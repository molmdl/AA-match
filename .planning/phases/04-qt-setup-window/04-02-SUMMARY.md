---
phase: 04-qt-setup-window
plan: 02
subsystem: pure-layer
tags: [setup-form, pure-glue, validation, tdd, python3.6, py-qt-seams]

# Dependency graph
requires:
  - phase: 01-bootstrap-pure-foundation
    provides: setup_state.validate_state / randomize_state (single validation authority), the PURE_MODULES gate machinery
  - phase: 02-headless-game-engine
    provides: manifest payload shape (sets -> set_id/title/tier), engine demo_set_id 'demo-...' refusal wording, generator mode-refusal wording
  - phase: 03-wizard-gameplay-loop
    provides: gamestart.start_game cleans-the-scene-FIRST ordering (the ordering hazard the pre-checks defend against)
provides:
  - aamatch/setup_form.build_state (three fatal user-facing refusals BEFORE the scene is touched + validate_state delegation)
  - aamatch/setup_form.usable_randomized_state (Randomize fix-up — the 'demo-%04x' trap is dead)
  - aamatch/setup_form.manifest_sets (dropdown rows from a parsed manifest payload, no I/O)
affects: [setup_window plans]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fatal pre-checks BEFORE start_game's cleanup-first ordering: refuse doomed configurations in the pure layer so a refused Start never deletes prior game objects"
    - "Collect-then-check: validate_state stays the single validation authority; the form layer adds ONLY refusals, never re-validation"
    - "Non-schema form flags (upload_ready) consumed and never passed through — validate_state input built as a NEW 7-key dict (input non-mutation preserved)"

key-files:
  created:
    - aamatch/setup_form.py
    - tests/test_setup_form.py
  modified:
    - tests/test_purity.py

key-decisions:
  - "Refusal messages copied VERBATIM from the plan (upload / demo / exclusive / block_exclusive) and pinned by test-message equality — wording is user-facing regression teeth"
  - "Empty-allowed check runs on the NORMALIZED state, not raw input (widgets may carry values validate_state silently normalizes, setup_state.py:115-135)"
  - "manifest_sets takes the parsed PAYLOAD as plain data (no manifest import) — matches manifest.py's no-I/O discipline for callers"

patterns-established:
  - "Phase-4 pure-module TDD triplet: RED test commit → GREEN feat commit → PURE_MODULES registration as its own test commit (02-02 pattern continued)"
  - "Layer declaration docstring in the wizard_text.py style naming the PURE_MODULES registration and the no-I/O discipline"

# Metrics
duration: 8min
completed: 2026-09-15
---

# Phase 4 Plan 02: setup_form Pure Helpers Summary

**PURE form-glue module (`aamatch/setup_form.py`) with three fatal pre-start refusals, the Randomize `demo_set_id` fix-up, and manifest dropdown rows — purity-gated, WSL-proven (632/632 green, +18 new tests), probe-independent.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-09-15T04:26:49Z
- **Completed:** 2026-09-15T04:34:17Z
- **Tasks:** 3
- **Files modified:** 3 (2 created, 1 edited)

## Accomplishments
- `build_state(form_values, known_set_ids=())` refuses the three doomed configurations with user-facing messages BEFORE anything scene-adjacent runs: upload mode without ingested content (names Browse), non-empty `demo_set_id` not among known manifest ids (names the id), normalized exclusive/block_exclusive with empty `allowed_interactions` (wording aligned with the generator's own refusals). Fires before `start_game`'s cleanup-first ordering, so a doomed Start never deletes prior game objects.
- `usable_randomized_state(seed, demo_set_id)` kills the `demo-%04x` trap: `randomize_state` output with the synthesized id overwritten by a real manifest id (or `''` = all sets); trap-kill proven across seeds 0..19.
- `manifest_sets(payload)` turns a parsed manifest payload into sorted `(set_id, title, tier)` dropdown rows with `.get` fallbacks — pure data-in/data-out, no I/O.
- `setup_form` registered in `PURE_MODULES`; the purity gate now AST-scans and clean-subprocess-imports the new module.

## Task Commits

Each task was committed atomically (TDD RED → GREEN → REGISTER):

1. **Task 1: RED — failing tests for the three refusals, randomize fix-up, manifest_sets** — `f72836b` (test)
2. **Task 2: GREEN — implement aamatch/setup_form.py** — `78560d5` (feat)
3. **Task 3: REGISTER — PURE_MODULES registration as its own step** — `0286962` (test)

**Plan metadata:** see final `docs(04-02)` commit (SUMMARY.md + STATE.md).

## Files Created/Modified
- `aamatch/setup_form.py` — PURE module: `build_state`, `usable_randomized_state`, `manifest_sets`; imports `from .setup_state import randomize_state, validate_state` only.
- `tests/test_setup_form.py` — 18 tests / 8 test classes pinning the refusal messages VERBATIM, identity-through-validate_state, input non-mutation, fix-up determinism + trap-kill over seeds 0..19, and manifest_sets shape/fallbacks.
- `tests/test_purity.py` — `'setup_form'` appended to `PURE_MODULES` with a Phase-4 comment line; nothing else touched (ALLOWED_STDLIB unchanged).

## Decisions Made
- Refusal messages copied verbatim from the plan/behavior contract and pinned by exact string equality in tests — the wording is user-facing and must never drift silently.
- The empty-allowed refusal runs on the NORMALIZED state (post-validate_state) because widgets may carry values validate_state silently normalizes; refusing on raw input could disagree with what the generator would have seen.
- The `upload_ready` non-schema flag is consumed and never passed through: the validate_state input is built as a NEW dict of the 7 schema keys, preserving input non-mutation (D3/P6).
- `manifest_sets` takes the parsed payload as plain data instead of importing `manifest` — matches manifest.py's own no-I/O discipline for callers.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None. RED state came up clean (`ModuleNotFoundError: No module named 'aamatch.setup_form'`); GREEN needed no iteration.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness
- The pure-half contract for all Phase-4 Qt button handlers (04-09..04-13) now exists and is WSL-proven: handlers pass widget-collected form dicts into `build_state`, catch the ValueError family, and show `str(e)` verbatim.
- The `upload_ready` flag semantics (True iff the window holds ingested content matching the form's upload path) is pinned for the upload-brief plans.
- Verification suite: `python3.6 -m unittest tests.test_setup_form -v` (18/18) and the full WSL suite `python3.6 -m unittest discover -s tests` (632/632) green; `python3.6 -m py_compile aamatch/setup_form.py` green.

---
*Phase: 04-qt-setup-window*
*Completed: 2026-09-15*
