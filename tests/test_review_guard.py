"""Offline tests: temporary directories only; not operational threat detections."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools import review_guard as g


class ReviewGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "example.py").write_bytes(b"print('hello')\n")
        self.manifest = g.canonical(g.snapshot(self.root))
        self.anchor = g.digest(self.manifest)

    def verify(self, data=None, anchor=None):
        return g.verify(self.root, data or self.manifest, anchor or self.anchor)

    def test_unchanged_is_not_approval(self):
        result = self.verify()
        self.assertEqual(result["status"], "MATCHES_PROPOSED_SNAPSHOT")
        self.assertFalse(result["release_authorized"])

    def test_content_change(self):
        (self.root / "example.py").write_text("changed\n")
        self.assertEqual(self.verify()["modified"], ["example.py"])

    def test_added_file(self):
        (self.root / "new.py").write_text("new")
        self.assertEqual(self.verify()["added"], ["new.py"])

    def test_deleted_file(self):
        (self.root / "example.py").unlink()
        self.assertEqual(self.verify()["removed"], ["example.py"])

    def test_untracked_sensitive_filename_is_not_silently_ignored(self):
        (self.root / ".env").write_text("EXAMPLE_ONLY=not-a-secret")
        self.assertEqual(self.verify()["added"], [".env"])

    @unittest.skipIf(os.name == "nt", "POSIX executable mode check")
    def test_executable_bit_change(self):
        (self.root / "example.py").chmod(0o755)
        self.assertEqual(self.verify()["modified"], ["example.py"])

    def test_manifest_tamper_fails_anchor(self):
        with self.assertRaises(g.GuardError):
            self.verify(self.manifest + b" ")

    def test_rewrite_files_and_adjacent_manifest_still_fails_original_anchor(self):
        (self.root / "example.py").write_text("different")
        replacement = g.canonical(g.snapshot(self.root))
        with self.assertRaises(g.GuardError):
            self.verify(replacement)

    def test_new_anchor_is_not_owner_approval(self):
        (self.root / "example.py").write_text("different")
        replacement = g.canonical(g.snapshot(self.root))
        self.assertFalse(self.verify(replacement, g.digest(replacement))["release_authorized"])

    def test_path_traversal_rejected(self):
        value = g.snapshot(self.root)
        value["files"]["../escape"] = copy.copy(value["files"]["example.py"])
        data = g.canonical(value)
        with self.assertRaises(g.GuardError):
            self.verify(data, g.digest(data))

    def test_absolute_path_rejected(self):
        self.assertFalse(g.safe_relative("/etc/passwd"))

    def test_windows_path_rejected(self):
        self.assertFalse(g.safe_relative("C:\\private\\key"))

    def test_boolean_size_rejected(self):
        value = g.snapshot(self.root)
        value["files"]["example.py"]["bytes"] = True
        data = g.canonical(value)
        with self.assertRaises(g.GuardError):
            self.verify(data, g.digest(data))

    def test_duplicate_json_keys_rejected(self):
        data = b'{"schema_version":1,"schema_version":1}'
        with self.assertRaises(g.GuardError):
            self.verify(data, g.digest(data))

    def test_invalid_json_rejected(self):
        data = b'not json'
        with self.assertRaises(g.GuardError):
            self.verify(data, g.digest(data))

    def test_malformed_digest_rejected(self):
        with self.assertRaises(g.GuardError):
            self.verify(anchor="not-a-digest")

    def test_nonhex_record_digest_rejected(self):
        value = g.snapshot(self.root)
        value["files"]["example.py"]["sha256"] = "z" * 64
        data = g.canonical(value)
        with self.assertRaises(g.GuardError):
            self.verify(data, g.digest(data))

    def test_changed_exclusions_rejected(self):
        value = g.snapshot(self.root)
        value["excluded_directories"].append("hidden-code")
        data = g.canonical(value)
        with self.assertRaises(g.GuardError):
            self.verify(data, g.digest(data))

    def test_manifest_itself_is_excluded(self):
        target = self.root / g.MANIFEST_PATH
        target.parent.mkdir()
        target.write_bytes(self.manifest)
        self.assertEqual(self.verify()["status"], "MATCHES_PROPOSED_SNAPSHOT")

    def test_cache_scope_is_explicit(self):
        path = self.root / "__pycache__"
        path.mkdir()
        (path / "cache.pyc").write_bytes(b"cache")
        self.assertIn("__pycache__", g.snapshot(self.root)["excluded_directories"])
        self.assertEqual(self.verify()["status"], "MATCHES_PROPOSED_SNAPSHOT")

    @unittest.skipIf(os.name == "nt", "Symlink permissions differ on Windows")
    def test_file_symlink_rejected(self):
        (self.root / "link").symlink_to(self.root / "example.py")
        with self.assertRaises(g.GuardError):
            g.snapshot(self.root)

    @unittest.skipIf(os.name == "nt", "Symlink permissions differ on Windows")
    def test_directory_symlink_rejected(self):
        (self.root / "link").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(g.GuardError):
            g.snapshot(self.root)

    def test_file_size_limit(self):
        with patch.object(g, "MAX_FILE_BYTES", 2):
            with self.assertRaises(g.GuardError):
                g.snapshot(self.root)

    def test_total_size_limit(self):
        with patch.object(g, "MAX_TOTAL_BYTES", 2):
            with self.assertRaises(g.GuardError):
                g.snapshot(self.root)

    def test_file_count_limit(self):
        with patch.object(g, "MAX_FILES", 0):
            with self.assertRaises(g.GuardError):
                g.snapshot(self.root)

    def test_repeat_snapshot_is_deterministic(self):
        self.assertEqual(self.manifest, g.canonical(g.snapshot(self.root)))

    def test_verify_does_not_write_files(self):
        before = list(self.root.rglob("*"))
        self.verify()
        self.assertEqual(before, list(self.root.rglob("*")))

    def test_safe_relative_empty_and_dot_rejected(self):
        for path in ("", ".", "./example.py", "a//b", "a/../b", "a\x00b"):
            with self.subTest(path=path):
                self.assertFalse(g.safe_relative(path))


if __name__ == "__main__":
    unittest.main()
