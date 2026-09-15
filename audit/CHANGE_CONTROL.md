# Change accountability for the local pilot

Baseline and current work are recorded, not retroactively approved. `CHANGE_REGISTER.jsonl` is an append-oriented development record in mutable Git history, not independent audit storage. Do not backdate or delete unexplained changes. Exact head approval remains pending.

For source comparison, use `tools/review_guard.py` from a trusted environment with a manifest digest retained outside the writable source. A proposed manifest cannot approve itself. Preserve the original handoff checksums as archive provenance, not as authority for current code.

The service's ledger links enrollment, event ingestion, analysis success/failure, candidates and owner review. Verification reconciles normalized event hashes, source policies, pending/completed jobs and cases with that ledger. A separately retained head detects a matching-chain truncation or rewrite relative to that checkpoint. A database administrator able to rewrite the records, code and reference remains able to defeat a same-host check; no tamper-proof claim is made.

No branch rule, external witness or independent approval is established by a text file. Branches were reported unprotected on the initial read. `CODEOWNERS` is only review routing. Source/config changes after an exact-version review invalidate that review. Do not merge or deploy automatically.

The prior PR-creation operation was blocked by a platform safety check. It is not retried, rephrased, or recreated through another tool. This milestone uses only independently authorized existing-branch commits.
