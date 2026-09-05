---
phase: 01-bootstrap-pure-foundation
plan: 03
subsystem: persistence
tags: [backup, sha256, integrity, dependency-injection, canonical-json, python36, stdlib, tdd]

# Dependency graph
requires: []
provides:
  - "aamatch.backup pure core: BackupError, MemoryStore, FileStore, snapshot, restore, discard, verify_intact, BACKUP_OBJECT_PREFIX"
  - "Store protocol (save_bytes/load_bytes/delete/exists) — the injection seam for the future cmd-tier adapter"
  - "Self-describing corruption-detecting backup format: sha256hex + b'\\n' + canonical JSON"
  - "23-test green suite incl. on-disk byte-flip corruption simulation (PITFALLS.md:181 recovery proof)"
affects: [grid-generation, viewer-interaction, scoring-lifecycle, checkpoint-persistence, cmd-tier-backup-adapter]

# Tech tracking
tech-stack:
  added: []   # stdlib only (hashlib, json, os, tempfile, time) — zero new deps
  patterns:
    - "Store injection: pure policy functions take an injected store; storage is never imported (ARCHITECTURE.md Pattern 1)"
    - "Self-describing stored bytes (sha256 header + canonical JSON) so restore/verify gate corruption byte-level"
    - "Missing-key discipline (prior-art E3 / PITFALLS P7): BackupError('no backup ...'); callers assert, never re-derive"
    - "Mixin-based contract suite: one test body, executed once per store implementation"

key-files:
  created:
    - aamatch/backup.py
    - tests/test_backup.py
  modified: []

key-decisions:
  - "Stored bytes are self-describing (sha256hex + b'\\n' + canonical JSON) per the plan's final implementation sketch — restore splits, re-hashes, and refuses on mismatch; no separate manifest object needed"
  - "verify_intact raises on missing key (P7/E3 discipline) but returns False on corruption — corrupt backups are a reportable state, missing backups are a caller error"
  - "Canonical payload comparison (byte-level) for verify_intact, not parsed-dict equality — 'byte-level integrity via canonical-JSON + sha256'"
  - "Key validation (simple filenames only, path-traversal guard) shared by BOTH stores via _check_key, not FileStore-only — keeps the store protocol uniformly safe"
  - "allow_nan=False + sort_keys=True canonical JSON (A7/A8): non-finite floats fail loudly; byte-stable output"

patterns-established:
  - "Pattern: every destructive op routes through snapshot → mutate → discard|restore with verify_intact as the integrity proof (no-undo discipline, PITFALL 9)"
  - "Pattern: contract tests via plain mixin + per-store TestCase subclasses (runs once per store, no abstract third suite)"

# Metrics
duration: 30 min
completed: 2026-09-05
---

# Phase 1 Plan 03: Backup Pure Core Summary

**Pure snapshot/restore/discard/verify_intact lifecycle over injected stores (MemoryStore + FileStore) with sha256 corruption detection — 23 stdlib-only tests green, proven by an on-disk byte-flip simulation.**

## Performance

- **Duration:** 30 min
- **Started:** 2026-09-05T09:13:19Z
- **Completed:** 2026-09-05T09:43:43Z
- **Tasks:** 3 (RED → GREEN → REFACTOR)
- **Files modified:** 2 created

## Accomplishments
- Full backup lifecycle (snapshot/restore/discard/verify_intact) works identically over MemoryStore and FileStore with exact dict round-trips (nested dicts + unicode) — zero pymol imports, stub-free under bare python3.6
- Corruption is DETECTED: stored bytes are self-describing (`sha256hex + b'\n' + canonical_json`); a single flipped byte on disk makes `restore` raise `BackupError('backup corrupt ...')` and `verify_intact` return False — the PITFALLS.md:181 recovery proof
- Missing-key discipline encoded (prior-art E3 / P7): `BackupError('no backup stored under key %r')`; docstrings instruct callers to assert, never re-derive
- FileStore writes are atomic (mkstemp + fsync + os.replace, no `.aam_` temp litter) and persist across instances; keys are validated simple filenames (path-traversal guard)
- `BACKUP_OBJECT_PREFIX = '_aam_backup'` reserved and documented for the future cmd-tier adapter (deliberately not implemented here)

## Task Commits

Each TDD phase was committed atomically:

1. **RED: failing tests for pure backup core over injected stores** - `0c5361e` (test)
2. **GREEN: implement backup snapshot/restore/verify over injected stores** - `ec33da7` (feat)
3. **REFACTOR: clean up backup core** - `64d9344` (refactor)

**Plan metadata:** _see final docs commit_

## Files Created/Modified
- `aamatch/backup.py` — pure backup policy + MemoryStore/FileStore (244→246 lines): canonical JSON, sha256 framing, store protocol, lifecycle functions
- `tests/test_backup.py` — 23 tests: 8-case contract × 2 stores, on-disk byte-flip (payload region AND sha-header region), MemoryStore tamper, temp-litter check, cross-instance durability, unsafe-key guard, prefix pin

## Decisions Made
- **Self-describing stored format** (per plan's final implementation sketch, superseding its earlier `save_bytes(key, data)`-only sketch): the sha256 rides in the stored bytes, so any store implementation gets corruption detection for free and restore needs no side-channel manifest
- **verify_intact asymmetric error policy:** missing key → raise (missing backup is caller error, P7); corrupt → False (corruption is a reportable state the orchestrator routes to regenerate-from-spec)
- **Shared `_check_key` in both stores** (plan placed validation under FileStore; uniform enforcement keeps the duck-typed protocol safe for every caller)
- **Manifest sha read back from the stored header** (REFACTOR): one sha256 computation per snapshot; manifest and stored digest consistent by construction

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test-suite design: abstract contract base was collected as a third suite**
- **Found during:** GREEN (first full run after implementing `aamatch/backup.py`)
- **Issue:** `BackupContractTestCase(unittest.TestCase)` with an abstract `make_store` was itself collected by unittest — its 8 contract tests ran with no store and errored (`NotImplementedError` in setUp), masking the real 23-test result
- **Fix:** Converted the shared contract to a plain mixin (`BackupContractMixin`) with concrete suites `MemoryStoreBackupTests(BackupContractMixin, unittest.TestCase)` and `FileStoreBackupTests(BackupContractMixin, unittest.TestCase)`; contract now runs exactly twice, once per store
- **Files modified:** tests/test_backup.py
- **Verification:** 23/23 green in both `-m unittest tests.test_backup` and `discover -s tests` modes
- **Committed in:** ec33da7 (folded into the GREEN commit — the fix was required to go green)

---

**Total deviations:** 1 auto-fixed (1 bug in test infrastructure, not in planned behavior)
**Impact on plan:** No scope change; all 12 planned behaviors covered as written plus the plan's own key-safety clause.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- The backup contract is ready for every later destructive feature: placement/reset/cleanup phases (2/3/6) and checkpoint persistence (7) must route through snapshot → mutate → discard|restore with verify_intact as the proof
- The cmd-tier adapter (PyMOL object snapshotting via `cmd.create('_aam_backup', ...)`) is deliberately NOT built here — later phase injects a cmd-backed store / feeds atom-tuple payloads through this same contract
- Note for orchestrator: `aamatch/__init__.py` and `tests/__init__.py` are owned by parallel plan 01-01; this plan verified its suite works both with and without them (PEP 420 namespace imports under python3.6.9, both `tests.test_backup` and `discover -s tests` modes)

---
*Phase: 01-bootstrap-pure-foundation*
*Completed: 2026-09-05*
