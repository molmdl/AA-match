---
phase: 07-checkpoint-game-file-persistence
plan: 01
subsystem: persistence
tags: [pymol, pse, session, wizard, pickle, reduce, checkpoint]

# Dependency graph
requires:
  - phase: 03-wizard-interaction
    provides: GameWizard plain-data contract (picklable books, no Qt/locks)
  - phase: 06-scoring-lifecycle-endgame
    provides: wizard lifecycle event books (_last_event/_event_seq mirrors)
  - phase: 07-checkpoint-game-file-persistence (07-RESEARCH-pse.md)
    provides: probe-proven defect root cause + argless-rebuilder fix shape (phase-A part C)
provides:
  - GameWizard argless `__reduce__` rebuilder (_rebuild_game_wizard) — `.pse` sessions saved with a live game restore the wizard active on the stack
  - SMOKE-17 strict two-process wizard restore compare (defect-signature pin removed) + post-load identity invariant
  - ROADMAP Phase-7 criterion 3's wizard half: clean save/load of a wizard-carrying session, zero Session-Warning
affects: [07-* all later plans, sidecar/checkpoint smoke designs, human GUI checkpoint 07-12]

# Tech tracking
tech-stack:
  added: []
  patterns: [module-level argless unpickle rebuilder (`__reduce__` -> (rebuilder, (), __getstate__())), strict snapshot compare pattern for session round-trips (`color_store_full` JSON-safe full-store capture)]

key-files:
  created:
    - .planning/phases/07-checkpoint-game-file-persistence/07-01-SUMMARY.md
  modified:
    - aamatch/wizard.py
    - smoke/smoke_17_pse_roundtrip.py

key-decisions:
  - "Argless rebuilder (object.__new__ + inherited __getstate__ + default state dict application) over init-with-optional-args — one function, no __init__ contract change; probe-proven option (i) from 07-RESEARCH-pse.md"
  - "Console cleanliness in SMOKE-17 is asserted via positive restore (no stdout capture): the defect path prints Session-Warning AND drops the wizard, so a restored GameWizard implies a clean console; explicit NOTE line records the claim for the human checkpoint"

patterns-established:
  - "Session round-trip smoke: snapshot writes a JSON-safe full-store capture (tuples -> int lists) so the verify phase compares books EXACTLY, not key sets"
  - "Real-path flip discipline: remove the in-memory monkey-patch prototype from run 1 as soon as production carries the fix — run 2 then exercises the real class path only"

# Metrics
duration: 7 min
completed: 2026-09-21
---

# Phase 7 Plan 01: GameWizard Pickle-Restore Fix Summary

**Argless `_rebuild_game_wizard` rebuilder on `GameWizard.__reduce__` fixes the `.pse` wizard-drop defect; SMOKE-17 two-process round-trip now proves a saved-with-wizard session restores the wizard with byte-equal books and zero Session-Warning.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-21T03:17:44Z
- **Completed:** 2026-09-21T03:24:49Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `GameWizard.__reduce__` returns `(_rebuild_game_wizard, (), self.__getstate__())` — `object.__new__` skips `__init__`, so the required `payload`/`registry` args can no longer raise `TypeError` inside `session_restore_wizard` (the phase gate-3 landmine, ROADMAP criterion 3).
- Inherited `Wizard.__getstate__` (pops only `cmd`) and pickle's default state application via `__dict__.update` are used as-is — no `__setstate__`, no `__init__` contract change, no attribute stripping beyond `cmd`.
- SMOKE-17 phase B flipped from the documented-defect signature pin to the STRICT restore compare: restored top-of-stack IS a GameWizard through the REAL production reduce path; `_current_slot`, `_event_seq`, `_last_event`, `_saved_msm`, `_payload['seed']`, FULL `_color_store` (`color_store_full` JSON rows), and `get_status()` dict all equal the run-1 snapshot.
- Post-load identity invariant added: `_assert_identity` on every recolored slot object AFTER `cmd.load` (the probe asserted pre-save only).
- Run-1 part-C monkey-patch prototype deleted — the production module carries the real rebuilder, so run 2 exercises only the real class path.

## Task Commits

Each task was committed atomically:

1. **Task 1: GameWizard argless `__reduce__` rebuilder** — `11c6d89` (fix)
2. **Task 2: SMOKE-17 phase-B strict restore compare + post-load identity assert** — `43e168d` (test)

**Plan metadata:** recorded in the final docs commit (see orchestrator merge).

## Files Created/Modified

- `aamatch/wizard.py` — module-level `_rebuild_game_wizard()` + `GameWizard.__reduce__` override (32 insertions; docstrings carry no banned-token mentions — PROSE_PIN untouched).
- `smoke/smoke_17_pse_roundtrip.py` — phase-B strict compare block, post-load identity check, console NOTE, snapshot extended with `last_event` + `color_store_full`, part-C monkey-patch block removed.

## Decisions Made

- **Argless rebuilder over init-with-optional-args:** the research-recommended fix shape (i), probe-proven through the real task path (session_save_wizard -> pickle.loads -> cmd rebind -> set_wizard_stack). One module-level function; zero changes to `__init__`, `__getstate__`, or the attribute contract.
- **Console-cleanliness assertion style:** SMOKE-17 does not capture its own stdout, so cleanliness rides the positive restore result (defect path prints Session-Warning AND drops the wizard — a restored GameWizard proves zero plugin-caused warnings), with an explicit `SMOKE-17 NOTE console:` line preserved for the human checkpoint's criterion-3 record.

## Deviations from Plan

None — plan executed exactly as written. (The prescribed code/docstrings were applied verbatim; no banned-token prose added, so `tests/test_wizard_source.py` and `tests/test_code_audit.py` pins stayed green without edits.)

## Issues Encountered

None. Spot-check bonus: ran SMOKE-07 (wizard loop) after the wizard.py change — PASS (worst drifts unchanged), confirming `__reduce__` is purely additive. Full smoke battery re-verification remains assigned to plan 07-11 by design.

## User Setup Required

None — no external service configuration required.

## Verification Evidence

- `python3.6 -m py_compile aamatch/*.py smoke/smoke_17_pse_roundtrip.py` — green.
- `python3.6 -m unittest discover -s tests -v` — **826 tests OK** (incl. purity gates, test_wizard_source zero-mention pin, test_code_audit PROSE_PIN).
- `bash smoke/run_smoke.sh smoke/smoke_17_pse_roundtrip.py 240` **run 1 (SAVE):** `=== SMOKE-17 PASS ===` — snapshot written, `cmd.save` with the wizard live succeeded, `wizard-save: direct pickle.dumps(wiz,1) ok=True`.
- **run 2 (VERIFY, fresh process):** `=== SMOKE-17 PASS ===` — 19 more checks incl. coords/view/matrices bit-exact (max_delta=0.000e+00), `B restored top-of-stack is a GameWizard (REAL __reduce__ path) PASS`, `B restored GameWizard books == the run-1 snapshot PASS (seed=42/42 slot='r0c0'/'r0c0' seq=0/0 msm=1/1 store-eq=True status-eq=True)`, `SMOKE-17 VERDICT wizard: strict restore compare -> PROVEN`, `B post-load identity invariant on recolored slot objects PASS (objects=['_aam_aa01'])`. No `Session-Warning` line anywhere in the transcript.
- `bash smoke/run_smoke.sh smoke/smoke_07_wizard_loop.py 240` — `=== SMOKE-07 PASS ===` (regression spot-check).

## Next Phase Readiness

- `.pse` wizard half of ROADMAP criterion 3 is now PROVEN; plans 07-02+ can build the sidecar/checkpoint flow on a restored-wizard baseline (`engine._game` still correctly stays dead after load — sidecar owns game state).
- Must_haves for later plans: the restored wizard auto-arms active on the stack; `cmd.get_wizard()` is a GameWizard immediately after `cmd.load`; `_saved_msm` rides the state (cleanup still restores the user's true msm on Done).
- Concern for the human checkpoint (07-12): installed-identity round-trip (`pmg_tk.startup.aamatch`) is inferred-safe (startup plugins auto-import) but unprobed — per 07-RESEARCH [UNVERIFIED] item 2, the GUI checkpoint covers it.

---
*Phase: 07-checkpoint-game-file-persistence*
*Completed: 2026-09-21*
