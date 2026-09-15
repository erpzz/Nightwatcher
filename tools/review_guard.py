#!/usr/bin/env python3
"""Bounded source-file comparison, not an approval/signature or malware detector.

Only reads source files. No networking, Git hooks, deployments, or subprocesses.
An expected manifest digest must be supplied from a separately retained reference.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any

MANIFEST_PATH = "audit/PROPOSED_MANIFEST.json"
EXCLUDED_DIRS = frozenset({".git", ".venv", "venv", "node_modules", "__pycache__",
                          ".pytest_cache", ".mypy_cache", ".ruff_cache", ".next", ".turbo"})
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_FILES = 5000
SHA256 = re.compile(r"[a-f0-9]{64}\Z")


class GuardError(ValueError):
    """Unsafe or unsupported input, not an attribution of malicious intent."""


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_relative(value: str) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return False
    parts = value.split("/")
    return (not PurePosixPath(value).is_absolute() and
            all(part not in {"", ".", ".."} for part in parts) and
            not any(ord(c) < 32 for c in value) and ":" not in value and
            not any(part in EXCLUDED_DIRS for part in parts) and value != MANIFEST_PATH)


def _file_record(path: Path) -> dict[str, Any]:
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise GuardError("Non-regular files and symlinks are outside the supported source scope")
    if before.st_size > MAX_FILE_BYTES:
        raise GuardError("File exceeds the source snapshot size limit")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise GuardError("File changed during opening; retry after stopping writers")
        data = stream.read(MAX_FILE_BYTES + 1)
        after = os.fstat(stream.fileno())
    final = path.lstat()
    fields = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_mode)
    if len(data) > MAX_FILE_BYTES or fields(before) != fields(after) or fields(after) != fields(final):
        raise GuardError("File changed while being read; no stable snapshot was established")
    return {"sha256": digest(data), "bytes": len(data), "executable": bool(before.st_mode & 0o111)}


def snapshot(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise GuardError("Root must be a source directory")
    files: dict[str, Any] = {}
    total = 0
    def walk_error(error: OSError) -> None:
        raise GuardError("A source directory could not be read") from error
    for directory, dirs, names in os.walk(root, topdown=True, followlinks=False, onerror=walk_error):
        directory = Path(directory)
        kept = []
        for name in sorted(dirs):
            path = directory / name
            if name in EXCLUDED_DIRS:
                continue
            if path.is_symlink():
                raise GuardError("Symlink directory is outside the supported source scope")
            kept.append(name)
        dirs[:] = kept
        for name in sorted(names):
            path = directory / name
            rel = path.relative_to(root).as_posix()
            if rel == MANIFEST_PATH or name == ".git":
                continue
            if not safe_relative(rel):
                raise GuardError("Unsupported source path")
            record = _file_record(path)
            files[rel] = record
            total += record["bytes"]
            if len(files) > MAX_FILES or total > MAX_TOTAL_BYTES:
                raise GuardError("Source snapshot exceeds the bounded collection limits")
    return {"schema_version": 1, "status": "PROPOSED_NOT_OWNER_APPROVED",
            "scope": "source_files_only", "excluded_directories": sorted(EXCLUDED_DIRS),
            "excluded_paths": [MANIFEST_PATH], "files": files}


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GuardError("Duplicate JSON key in manifest")
        result[key] = value
    return result


def verify(root: Path, manifest_bytes: bytes, expected_sha256: str) -> dict[str, Any]:
    if not SHA256.fullmatch(expected_sha256):
        raise GuardError("Expected digest must be a lowercase SHA-256 hex string")
    if not hmac.compare_digest(digest(manifest_bytes), expected_sha256):
        raise GuardError("Manifest does not match the separately supplied digest")
    if len(manifest_bytes) > MAX_FILE_BYTES:
        raise GuardError("Manifest is too large")
    try:
        baseline = json.loads(manifest_bytes, object_pairs_hook=_no_duplicates)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise GuardError("Manifest is not valid UTF-8 JSON") from exc
    keys = {"schema_version", "status", "scope", "excluded_directories", "excluded_paths", "files"}
    if not isinstance(baseline, dict) or set(baseline) != keys:
        raise GuardError("Invalid manifest schema")
    if (type(baseline["schema_version"]) is not int or baseline["schema_version"] != 1 or
        baseline["status"] != "PROPOSED_NOT_OWNER_APPROVED" or
        baseline["scope"] != "source_files_only" or
        baseline["excluded_directories"] != sorted(EXCLUDED_DIRS) or
        baseline["excluded_paths"] != [MANIFEST_PATH] or
        not isinstance(baseline["files"], dict)):
        raise GuardError("Unsupported manifest scope or version")
    if len(baseline["files"]) > MAX_FILES:
        raise GuardError("Too many manifest records")
    for path, record in baseline["files"].items():
        if (not safe_relative(path) or not isinstance(record, dict) or
            set(record) != {"sha256", "bytes", "executable"} or
            not isinstance(record["sha256"], str) or not SHA256.fullmatch(record["sha256"]) or
            type(record["bytes"]) is not int or not 0 <= record["bytes"] <= MAX_FILE_BYTES or
            type(record["executable"]) is not bool):
            raise GuardError("Invalid manifest path or file record")
    current = snapshot(root)["files"]
    old = baseline["files"]
    added, removed = sorted(current.keys() - old.keys()), sorted(old.keys() - current.keys())
    modified = sorted(key for key in current.keys() & old.keys() if current[key] != old[key])
    return {"status": "MISMATCH_PENDING_REVIEW" if added or removed or modified else "MATCHES_PROPOSED_SNAPSHOT",
            "release_authorized": False, "added": added, "removed": removed, "modified": modified,
            "files_checked": len(current), "limits": "Not a signature, owner approval, independent witness, or malware scan."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("snapshot", help="Create a new proposed manifest; refuses overwrite")
    create.add_argument("root", type=Path)
    create.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("verify", help="Read-only source comparison against a retained digest")
    check.add_argument("root", type=Path)
    check.add_argument("--manifest", type=Path, required=True)
    check.add_argument("--expected-sha256", required=True)
    args = parser.parse_args()
    try:
        if args.command == "snapshot":
            data = canonical(snapshot(args.root))
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("xb") as output:
                output.write(data)
            print(json.dumps({"manifest_sha256": digest(data), "release_authorized": False}))
            return 0
        if args.manifest.is_symlink() or args.manifest.stat().st_size > MAX_FILE_BYTES:
            raise GuardError("Unsupported manifest file")
        result = verify(args.root, args.manifest.read_bytes(), args.expected_sha256)
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "MATCHES_PROPOSED_SNAPSHOT" else 1
    except (GuardError, OSError, RecursionError) as exc:
        print(json.dumps({"status": "CHECK_FAILED", "release_authorized": False,
                          "error": str(exc) if isinstance(exc, GuardError) else type(exc).__name__}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
