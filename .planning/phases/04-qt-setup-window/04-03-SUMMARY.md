---
phase: 04-qt-setup-window
plan: 03
subsystem: persistence
tags: [game-file, container, shareable-game, json, base64, sha256, purity-gates, tdd]

# Dependency graph
requires:
  - phase: 01-bootstrap-pure-foundation
    provides: versioned container core (persistence.check_container/FormatError, kind='game'), level_spec gates (refuse-newer + exact-match detector_version), setup_state.validate_state, purity-gate machinery (tests/test_purity.py)
  - phase: 02-headless-game-engine
    provides: generator.generate payload shape (detector_version/format_version/seed/levels), ligand block contract (source/set_id/entry_id/file/sha256), byte-identical determinism precedent, 02-15 stale-stamp refusal template
provides:
  - aamatch/game_file.py (PURE): GAME_VERSION=1 gate, UPLOAD_SET_ID, make_game_data, parse_game_data (5-gate import chain), encode/decode_ligand_files
  - SETUP-08 game-file format finalized in code (7-key data shape, embed-don't-regenerate, two-sha256 rule documented)
  - Phase 7 import gate chain: parse_game_data is invoked verbatim by PERSIST-02; decode_ligand_files feeds the 04-04 ligand_content seams
affects: [04-12 export handler, 04-06 upload helpers, Phase 7 (PERSIST-02 import)]

# Tech tracking
tech-stack:
  added: [stdlib base64 (ALLOWED_STDLIB whitelist +1)]
  patterns:
    - "Layered version gates: container header (persistence) -> game_format_version (game_file) -> format_version + exact-match detector_version (embedded level_spec) — each layer refuse-newer, detector exact-match, never mirrored upward"
    - "Embed-don't-regenerate: the full generator payload IS the shared truth; gates re-run on import with zero new import code"
    - "Registration-as-commit: PURE_MODULES append + ALLOWED_STDLIB whitelist line are their own test commit (02-02 pattern)"

key-files:
  created: [aamatch/game_file.py, tests/test_game_file.py]
  modified: [tests/test_purity.py]

key-decisions:
  - "detector_version NEVER mirrored at the game layer — single home inside the embedded spec (drift pitfall 11.3); absence is pinned by test"
  - "ligand_files holds ONLY uploaded molecules (source=='upload' requires an entry; source=='demo' forbids one — single meaning per source, fail-closed)"
  - "Two-sha256 rule: payload ligand.sha256 / ligand_files hashes are over the embedded RECORD TEXT; setup upload['sha256'] is over the uploaded FILE (04-06 territory)"
  - "seed duplicated at game layer as convenience only; level_spec['seed'] is authoritative"
  - "binascii.Error + UnicodeDecodeError both subclass ValueError — the bad-base64 refusal catches one family, no extra whitelist entries needed"

patterns-established:
  - "New pure module TDD cadence: RED tests (real generator payload via the test_generator fixture recipe) -> GREEN implementation -> REGISTER purity commit"

# Metrics
duration: 9min (execution; ~20min incl. mandatory context reading)
completed: 2026-09-16
---

# Phase 04 Plan 03: game_file core Summary

**PURE shareable-game container `aamatch/game_file.py`: GAME_VERSION refuse-newer gate + make/parse with the full 5-gate import chain (container -> game version -> setup -> embedded level-spec gates incl. exact-match detector_version -> ligand sha256/upload-demo cross-checks) + base64 ligand_files codec, purity-gated at 22 new tests.**

## Performance

- **Duration:** ~9 min execution (Started: 2026-09-15T18:26:18Z after mandatory reading; Completed: 2026-09-15T18:34:53Z)
- **Tasks:** 3 (RED / GREEN / REGISTER)
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments
- `make_game_data` returns the exact 7-key shape `{game_format_version, created_at, generator='AA-match', setup (re-validated), seed (convenience duplicate), level_spec (payload VERBATIM), ligand_files or {}}`; `detector_version` absence at the game layer is pinned by test.
- `parse_game_data` runs all five gates in order with the plan's refusal messages pinned verbatim by 14 refusal tests; the embedded spec re-runs ALL Phase-1 level-spec gates (incl. the exact-match "stale or newer game spec - regenerate it with a current AA-match generator") with zero new import-side code.
- Upload/demo single-meaning cross-check enforced fail-closed: uploaded molecules REQUIRE embedded content; demo molecules FORBID it; sha256 mismatches name the file + both hashes (64-char-lowercase-hex); unused entries refused ("no dead weight").
- Round-trips proven against REAL `generator.generate` payloads (fixture recipe copied from tests/test_generator.py): setup validated-equal, payload byte-identical (determinism precedent), decoded ligand texts sha256-verifying.
- Purity registration: `game_file` joins PURE_MODULES (17); `base64` joins ALLOWED_STDLIB with the research citation; full WSL suite 654/654 green.

## Task Commits

Each task was committed atomically (TDD RED -> GREEN -> REGISTER):

1. **Task 1: RED — failing tests for round-trip and every refusal class** - `96cea96` (test)
2. **Task 2: GREEN — implement aamatch/game_file.py core** - `8064648` (feat)
3. **Task 3: REGISTER — PURE_MODULES + ALLOWED_STDLIB 'base64'** - `e307a8e` (test)

**Plan metadata:** (docs commit follows) (docs: complete game_file-core plan)

## Files Created/Modified
- `aamatch/game_file.py` (created, 234 lines) — PURE module: GAME_VERSION=1, UPLOAD_SET_ID='uploaded', make_game_data, parse_game_data, encode/decode_ligand_files; docstring documents the layer, the two-sha256 rule, and the never-mirror-detector_version law
- `tests/test_game_file.py` (created, 441 lines) — 22 tests: 3 make-shape, 2 round-trips (demo + uploaded), 14 refusal classes (exact/substring message pins), encode/decode codec
- `tests/test_purity.py` (modified) — PURE_MODULES += 'game_file' (+ Phase-4 comment); ALLOWED_STDLIB += 'base64' (+ research citation comment)

## Decisions Made
- **detector_version NEVER mirrored at the game layer** (single source of truth inside the embedded spec; mirroring = drift pitfall 11.3). The absence test is a mechanical guard, not prose.
- **bad-base64 refusal catches `(ValueError, TypeError)` only** — verified in WSL: `binascii.Error` and `UnicodeDecodeError` subclass ValueError, so garbage base64, invalid UTF-8, and non-ASCII strings all refuse through one family naming the key; no whitelisting of binascii needed.
- **Refusal message placeholders:** the upload/demo cross-check messages use the molecule's `entry_id` as the molecule identifier (`%r (key %r)`), matching the "molecule"+"key" two-placeholder template.
- Fixture recipe COPIED (not imported) from tests/test_generator.py's Task-3 builders — keeps test modules independent; the recipe is small and the provenance is documented in the test docstring.

## Deviations from Plan

None - plan executed exactly as written. (All three commits match the pinned messages; no Rule 1-4 triggers fired.)

## Issues Encountered

None. First-attempt green on all three verify gates (`tests.test_game_file` 22/22, `tests.test_purity` 7/7, full discover 654/654, `py_compile aamatch/*.py` clean).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- **04-12 (export handler):** assemble via `make_game_data(setup, payload, encode_ligand_files(content), created_at)` → `persistence.save_container(path, 'game', data)`; the atomic writer and refusal chain are reused as-is.
- **04-06 (upload split/row helpers):** `UPLOAD_SET_ID='uploaded'` constant is live; rows restamped `source='upload'` + synthetic `uploads/mol-NNN` file keys already round-trip through this module (proven by TestRoundTripWithUploadedLigand). Note the carried-forward concern: this 2.5.0 build lacks the `cmd.read_mol2str` export — the mol2 upload route decision belongs to 04-06/04-08 (see 04-04-SUMMARY).
- **Phase 7 (PERSIST-02 import):** `persistence.load_container(path, 'game')` → `parse_game_data(container)` → `{'setup', 'payload', 'ligand_texts'}`; ligand_texts feed the 04-04 `ligand_content` seams of `engine.new_game`/`placement.materialize` directly.
- No smokes needed/added this plan (pure-layer TDD only); no PROSE_PIN disturbance (zero banned-token mentions added).

---
*Phase: 04-qt-setup-window*
*Completed: 2026-09-16*
