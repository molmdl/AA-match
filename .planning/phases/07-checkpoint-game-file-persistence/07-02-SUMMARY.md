---
phase: 07-checkpoint-game-file-persistence
plan: 02
subsystem: persistence
tags: [checkpoint, sidecar, zip, aamz, version-gate, reconcile, zipfile, pure]

# Dependency graph
requires:
  - phase: 01-bootstrap-pure-foundation
    provides: versioned container core (persistence.check_container/make_container, kind 'checkpoint' reserved), refuse-newer/accept-older + exact-match version-gate laws, PURE_MODULES gating
  - phase: 04-qt-setup-window
    provides: game_file.make_game_data/parse_game_data five-gate chain (replayed VERBATIM by gate 3), embed-don't-regenerate law
  - phase: 02-pure-data-scoring
    provides: GameState.to_dict/from_dict lossless pair + rebase_timer (02-10 wrap-don't-reshape law), placement.materialize registry shape (tuple identity contract)
provides:
  - aamatch/checkpoint.py single pure home for the checkpoint schema (CHECKPOINT_VERSION gate)
  - four-gate parse chain (container -> checkpoint_format_version -> embedded parse_game_data VERBATIM -> GameState light validator) with every refusal pinned verbatim by tests
  - sentinel-first reconcile_registry (never-ghost-entry, tuple-shaped rebuild, current-level completeness gate)
  - write_checkpoint_zip/read_checkpoint_zip atomic .aamz I/O (refusal-before-extraction)
  - tests/test_checkpoint.py 46-test WSL battery; checkpoint registered in PURE_MODULES (19 modules)
affects: [07-04-save-seams, 07-09-resume, 07-10-dispatch, any-plane-consuming-checkpoint-data]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Third versioned artifact pattern: own refuse-newer constant (CHECKPOINT_VERSION), never conflated with FORMAT_VERSION/GAME_VERSION/DETECTOR_VERSION"
    - "Gate-replay pattern: nested artifact gates reused verbatim via make_container wrapping (checkpoint -> game five-gate chain); zero new version logic at the outer layer"
    - "Sentinel-first reconciliation: sidecar entries kept iff (object, sorted ids) verify against the scene sweep; dropped never registered (never-ghost-entry law); scene extras reported"
    - "JSON<->tuple registry round-trip law: sidecar carries lists, rebuild restores materialize tuples; pre_game_names dropped/rebuilt as []"

key-files:
  created: [aamatch/checkpoint.py, tests/test_checkpoint.py]
  modified: [tests/test_purity.py]

key-decisions:
  - "checkpoint_format_version is a THIRD distinct refuse-newer gate (own constant/message), never conflated with the container version or detector_version"
  - "Embedded game block replayed through game_file.parse_game_data VERBATIM (make_container wrap) -- the exact-match detector_version gate refuses a stale checkpoint with the level_spec wording, zero new code"
  - "Reconcile rebuilt registry restores TUPLE shapes matching placement.materialize exactly; pre_game_names dropped on save, rebuilt as [] (zero consumers)"
  - "Completeness gate walks payload-expected shape only for the current level; first-missing-piece message names object %r / molecule / slot (object None when even the sidecar row is gone)"
  - "Sidecar zip member is the FULL container JSON so check_container gate 1 applies on read; parse gates run BEFORE extraction hand-off (refusal-first order)"
  - "elapsed_at_save validated >= 0 or None at parse (rewind-the-clock refusal); caller clamps at capture"

patterns-established:
  - "Four-gate checkpoint parse chain with pinned-verbatim refusals (mirrors the 04-03 game_file pattern one layer up)"
  - "Registration-pin TestCase per new pure module (TestCheckpointRegistration; generator/game_state precedent)"

# Metrics
duration: ~11 min
completed: 2026-09-21
---

# Phase 7 Plan 2: Checkpoint Schema & Zip I/O Summary

**Pure checkpoint module (aamatch/checkpoint.py) owning the .aamz sidecar schema, the four-gate parse chain replaying parse_game_data verbatim, the sentinel-first never-ghost-entry registry reconciler, and atomic zip I/O -- 46-test WSL battery green, registered in PURE_MODULES (19 gated modules).**

## Performance

- **Duration:** ~11 min
- **Started:** 2026-09-21T03:18:54Z
- **Completed:** 2026-09-21T03:29:40Z
- **Tasks:** 3/3
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments

- `aamatch/checkpoint.py` (519 lines): CHECKPOINT_VERSION/PSE_MEMBER/SIDECAR_MEMBER constants; `build_checkpoint_data` (verbatim game + game_state embeds, JSON registry conversion dropping pre_game_names); `parse_checkpoint_data` four-gate chain; `reconcile_registry` sentinel-first keep/drop/report + completeness gate; `write_checkpoint_zip`/`read_checkpoint_zip` atomic .aamz I/O.
- `tests/test_checkpoint.py` (818 lines, 46 tests): round-trip, every refusal message pinned verbatim (gate 2 wordings, embedded game-gate replays incl. exact `det-0` detector message and `game_format_version=2` message, all gate-4 game_state validator messages, completeness-gate first-piece messages), reconcile semantics (never-ghost, id-mismatch, missing-from-sidecar, tuple rebuild, future-levels-need-nothing), zip I/O (full-container sidecar pin, missing-member + corrupt refusals, temp-cleanup), elapsed -> `GameState.rebase_timer` integration.
- `tests/test_purity.py`: `checkpoint` registered in PURE_MODULES with provenance comment + TestCheckpointRegistration pin; full suite 873/873 green, negative control unchanged at exactly 2 findings.

## Task Commits

1. **Task 1: RED -- tests/test_checkpoint.py (failing)** - `8c35523` (test)
2. **Task 2: GREEN -- aamatch/checkpoint.py implementation** - `31d7788` (feat)
3. **Task 3: PURE_MODULES registration + full-suite green** - `41bdc12` (test)

## Files Created/Modified

- `aamatch/checkpoint.py` -- the pure checkpoint sidecar module (schema constants, four-gate parse chain, sentinel-first reconcile, .aamz zip I/O)
- `tests/test_checkpoint.py` -- 46-test WSL unit battery pinning every refusal verbatim
- `tests/test_purity.py` -- 'checkpoint' registered in PURE_MODULES (19 modules) + registration pin

## Decisions Made

- **Completeness-gate wording:** pinned as `checkpoint scene is missing game object %r (molecule %r, slot %r) -- the saved session no longer matches this checkpoint`; ligand pieces carry slot `'ligand'`; object is `None` when the sidecar row itself is gone (the plan offered this exact shape as an example and authorized pinning).
- **Drop-report rows:** `{molecule, slot, object, reason}` plain dicts; reason `'object absent from scene'` or `'scene atom ids [...] do not match the sidecar ids [...]'` (v1 missing_from_pse semantics adapted to the slot registry).
- **parse returns game_state as the verbatim to_dict output** (never a GameState object -- the 02-10 wrap-don't-reshape law; `from_dict` lives with the restore seam, 07-09).
- **elapsed_at_save coerced int -> float**, bool refused (bools are not counts/anchors anywhere in the house).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Closed a name-shadowing bug in the RED commit's `_editor` helper**

- **Found during:** Task 2 (GREEN phase, first test run)
- **Issue:** the test helper `_editor(container)` shipped in the RED commit had `container = copy.deepcopy(container)` inside the closure -- an UnboundLocalError on every use (21 of 46 tests errored).
- **Fix:** rewrote the closure body to assign into a fresh local (`mutated = copy.deepcopy(container)`).
- **Files modified:** tests/test_checkpoint.py (committed inside the GREEN commit `31d7788`)
- **Verification:** 46/46 checkpoint tests green after the fix; full suite 872/872 green pre-registration.
- **Commit:** 31d7788

---

**Total deviations:** 1 auto-fixed (1 bug, in the plan's own RED test code)
**Impact on plan:** The deviation is confined to the test battery; no module behavior changed, no messages reworded. No scope creep.

## Issues Encountered

None beyond the Rule-1 test-helper fix above (implementation was green on the first run after the helper fix).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Every later Phase-7 consumer is unblocked on data: 07-04 (save seams) calls `build_checkpoint_data` + `write_checkpoint_zip`; 07-09 (resume) calls `read_checkpoint_zip` + `reconcile_registry` + feeds `elapsed_at_save` to `GameState.rebase_timer`; 07-10 (dispatch) sniffs kind via the full-container sidecar member (gate-1 wording proven).
- Signals for later plans: `reconcile_registry` is dependency-injected pure (observed sweep passed by the cmd tier); the sidecar wizard/candidates blocks are additive `.get` reads -- the wizard books-snapshot op (07-04+) fills them; `candidates=None` is the demo-game shape.
- No blockers or concerns. `zipfile` whitelist anticipation confirmed (ALLOWED_STDLIB already carried it).

---
*Phase: 07-checkpoint-game-file-persistence*
*Completed: 2026-09-21*
