---
phase: 03-wizard-gameplay-loop
plan: 05
subsystem: core
tags: [pymol, wizard, game-entry, restart-hygiene, smoke-test, plugin-menu]

# Dependency graph
requires:
  - phase: 03-wizard-gameplay-loop/03-03
    provides: aamatch/wizard.py GameWizard with conditional-replace activate + the post-push msm snapshot ORDER LAW
  - phase: 03-wizard-gameplay-loop/03-04
    provides: SMOKE-07 wizard loop + scripted-pick recipe + tests/test_wizard_source.py SCANNED_MODULES extension point
  - phase: 02-data-and-headless-engine
    provides: engine new_game/materialize, placement cleanup_game_objects prefix-only deletion, DEFAULTS-frozen setup pipeline
  - phase: 01-bootstrap-pure-foundation/01-09
    provides: menu wiring (addmenuitemqt FIRST) + Gate A2 zero-module-level-import discipline in aamatch/__init__.py
provides:
  - aamatch/gamestart.py — start_game(setup=None, seed=42, candidates=None), the single cmd-tier game entry seam (cleanup FIRST → new_game → materialize → GameWizard.activate with CONDITIONAL replace: 1 only over a prior GameWizard, 0 over a user wizard or empty stack); the Phase-4 Qt setup window calls the same function
  - run_plugin_gui re-pointed at the seam via lazy import (Plugins → AA-match launches the game; metadata block byte-identical; Gate A2 green); returns the live GameWizard
  - smoke/smoke_08_starter.py — === SMOKE-08 PASS ===, 26 checks over the full entry path: starter state, restore-table spot check, BOTH restart paths (post-Done empty stack replace=0; mid-game without Done replace=1 with the ORDER-LAW msm regression-teeth assert), determinism, exact teardown
  - tests/test_wizard_source.py SCANNED_MODULES += gamestart.py (no-helper-visuals gate covers both cmd-tier UI modules)
  - tests/test_package_skeleton.py — the gamestart-seam AST source contract for run_plugin_gui
  - the instance-marker restart pattern (same-seed restarts reuse deterministic _aam_* names; identity proven by a b-factor stamp band, never by name-set equality)
affects: [03-06/03-07 human checkpoints (Plugins-menu start now exists and is headlessly proven), Phase 4 Qt setup window (calls start_game with the user's validated setup), Phase 6 cross-level staging (materialize(payload, 0) is the single-level start)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Game-start seam: cleanup_game_objects FIRST (restart hygiene) -> new_game -> materialize -> activate(conditional replace) in ONE function every caller shares"
    - "Restart-gone proof by INSTANCE marker (stamp b-band on the live generation; cleanup deletes marked instances; fresh objects are born sentinel) — object NAMES are not identity under deterministic same-seed materialization"
    - "WSL-side contract for a pymol-needing entry point: AST source assertions (lazy relative import + returned seam call), execution left to the headless smoke — zero sys.modules stubs preserved"

key-files:
  created: [aamatch/gamestart.py, smoke/smoke_08_starter.py]
  modified: [aamatch/__init__.py, tests/test_wizard_source.py, tests/test_package_skeleton.py]

key-decisions:
  - "start_game's conditional-replace rule RECORDED (checker-revised): replace=1 iff cmd.get_wizard() is a GameWizard (restart pop+clean — stale msm/colors/selection cannot leak); replace=0 over a user wizard or empty stack (stack-native auto-resume after Done; fresh PyMOL degenerates to a plain push)"
  - "No editor_scheme start-guard on 2.5.0 (03-RESEARCH-movement §5.6 contingency only — §3.3's scheme law makes the game's baked world-frame transforms scheme-independent)"
  - "Object names are NOT instance identity across restarts: same-seed same-shape restarts REBUILD the same _aam_* names after cleanup frees them; restart-gone asserts must stamp instances"
  - "__version__ stays 0.1.0 (no version bump: format/gate constants untouched)"

patterns-established:
  - "The Plugins-menu function is a plain callable headlessly: smokes call aamatch.run_plugin_gui() directly and assert on the RETURNED wizard's registry/payload (addmenuitemqt registration irrelevant headless)"

# Metrics
duration: 14min
completed: 2026-09-09
---

# Phase 3 Plan 05: Gamestart Entry Summary

**The one-call game entry seam is live and headlessly proven: `gamestart.start_game()` (cleanup FIRST → new_game → materialize → GameWizard.activate with conditional replace) is what Plugins → AA-match now calls via a lazy import — SMOKE-08 PASS proves starter state, the Done restore table, restart idempotence on BOTH paths (replace=0 over an empty stack; replace=1 mid-game with the ORDER-LAW msm assert), and same-seed determinism in real headless PyMOL, with gamestart.py requiring zero bug fixes.**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-09-09T02:45:17Z
- **Completed:** 2026-09-09T02:59:23Z
- **Tasks:** 3 completed
- **Files modified:** 5 (2 created, 3 modified)

## Accomplishments

- **=== SMOKE-08 PASS === (26 checks)** on the real entry path: `aamatch.run_plugin_gui()` called directly headless returns the live GameWizard; msm 0 in play with the post-push snapshot kept; 16-entry all-3-element panel; click-instruction prompt; scene growth exactly molecules × (1+n²), **derived from the returned registry** (never hard-coded).
- **BOTH restart paths proven idempotent:** post-Done empty-stack restart (replace=0) and mid-game restart WITHOUT Done (replace=1) each leave exactly one game generation; the new wizard instance is top; the replace=1 branch's post-push snapshot captures the TRUE pre-game msm (popped cleanup's restore) and Done restores 1 — the regression-teeth assert for 03-03's snapshot ORDER LAW now fires on the replace path (previously uncovered, per the 03-04 next-action note).
- **Old-generation-gone proven by INSTANCE, not name:** same-seed restarts reuse the exact same `_aam_*` names once cleanup frees them — the smoke stamps the live generation's b-factor (band −2.0..−0.5, sentinel b=−999.0 sits far outside) and asserts zero survivors.
- **Restore-table spot check:** scripted pick routes to slot identity + highlight recolor; Done restores msm (1, never hard-coded 0), restores recolored atom rows exactly, NEVER deletes game objects, pops the stack.
- **Gate A2 preserved:** `aamatch/__init__.py` still carries zero module-level imports; run_plugin_gui is `from . import gamestart` + `return gamestart.start_game()`; the `# Version: 0.1.0` metadata block + NOTE comment are byte-identical first lines (verified).
- **Source gates extended, not weakened:** tests/test_wizard_source.py's no-helper-visuals AST gate now scans gamestart.py too (one-line SCANNED_MODULES growth, per the 03-04 note); tests/test_package_skeleton.py swapped its stale Phase-1 placeholder-print assertion for the AST contract of the new seam (lazy relative import + returned `start_game` call + no leftover print).
- **Regression sweep green:** SMOKE-07 PASS, SMOKE-04 PASS, SMOKE-03 PASS, 593/593 WSL tests, `python3.6 -m py_compile aamatch/*.py` clean.

## Task Commits

Each task was committed atomically:

1. **Task 1: gamestart starter (gamestart.py + wizard-source gate growth)** — `dca4dec` (feat)
2. **Task 2: Plugins menu launches the game (run_plugin_gui + skeleton-test seam contract)** — `5043bda` (feat)
3. **Task 3: SMOKE-08 headless starter proof** — `68d284d` (feat)

**Plan metadata:** (this commit) `docs(03-05): complete gamestart-entry plan`

## Files Created/Modified

- `aamatch/gamestart.py` (created, 85 lines) — cmd tier (never PURE_MODULES): the single seam; conditional-replace rule + the editor_scheme contingency recorded in-docstring; one-line status print carries version/molecules/slots/seed/cleaned-count; returns the live wizard.
- `aamatch/__init__.py` (modified) — run_plugin_gui re-pointed at the seam (lazy import, returns the wizard); module docstring updated (Phase 1 skeleton → Phase 3 launcher); metadata block + NOTE untouched; `__version__` stays 0.1.0.
- `tests/test_wizard_source.py` (modified, 1-line gate growth) — SCANNED_MODULES = ['wizard.py', 'gamestart.py'].
- `tests/test_package_skeleton.py` (modified) — `test_run_plugin_gui_launches_gamestart_lazily` replaces the placeholder-print test (Rule-1 deviation below).
- `smoke/smoke_08_starter.py` (created, 377 lines) — the 26-check entry-path smoke; house conventions (sys.argv repo-root anchor, single-line flush prints, explicit space dicts, marker-based instance identity).

## Decisions Made

- **Conditional replace recorded as the binding rule** (plan's checker-revised wording, implemented verbatim): `replace=1 iff isinstance(cmd.get_wizard(), GameWizard)`. The smoke proves both branches and the msm contract on each.
- **run_plugin_gui returns the wizard** (plan-task wording: "SMOKE-08 checks 1/5 capture the returned wizard's registry/_payload") — smokes treat the menu function as an assertion handle; no wrapping around EngineError/WizardError (fail-closed with a surfaced traceback).
- **Instance-marker restart proof** promoted to a recorded pattern: deterministic materialization makes object names reusable across generations; identity asserts must stamp atoms (b-band), not compare name sets.
- **Contingency recorded, not implemented:** editor_scheme start-guard (03-RESEARCH-movement §5.6) stays out of gamestart — §3.3's scheme law holds for the baked world-frame movement model.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug, stale Phase-1 test] test_package_skeleton asserted the placeholder the plan replaces**
- **Found during:** Task 2 (run_plugin_gui re-point; full suite run)
- **Issue:** `test_run_plugin_gui_prints_version` EXECUTED the placeholder print and asserted its content; after the re-point it executed the gamestart import in WSL (no pymol) and errored. The plan's task-2 file set was `aamatch/__init__.py` only; tests/test_package_skeleton.py was not listed.
- **Fix:** Replaced the execution test with an AST source contract: the function body must carry `from . import gamestart` (lazy — Gate A2), `return gamestart.start_game()` (the smoke's assertion handle), and no leftover Phase-1 print. File-header contract item 5 updated; the now-unused `contextlib` import removed. Execution stays with SMOKE-08 headless; zero sys.modules stubs preserved.
- **Files modified:** tests/test_package_skeleton.py
- **Verification:** `python3.6 -m unittest discover -s tests` 593/593 green; Gate A2 (test_no_module_level_imports) still green.
- **Committed in:** `5043bda` (Task 2 commit)

**2. [Rule 1 - Bug in the smoke-check design, not in gamestart] name-based "old generation gone" is unimplementable**
- **Found during:** Task 3 (SMOKE-08 first run — 2 checks FAILed while the cleaned-20 status line and the count asserts all looked right)
- **Issue:** Same-seed same-shape restarts call `cleanup_game_objects()` (20 deleted), then `materialize` REBUILDS the same deterministic `_aam_aa01..18`/`_aam_lig01/02` names. A name-survivor check can never pass and proves nothing about instance identity.
- **Fix:** Instance-marker proof: stamp every live game atom's b-factor into a marker band (−2.0..−0.5; the materialization sentinel b=−999.0 sits far outside) before each restart; assert the marker reads ZERO afterwards, alongside the generation-count assert (a skipped cleanup would yield 40 objects, not 20).
- **Files modified:** smoke/smoke_08_starter.py
- **Verification:** `=== SMOKE-08 PASS ===` (26 checks; stamped 359 atoms → 0 survivors on both restart paths); SMOKE-07/04/03 regressions PASS.
- **Committed in:** `68d284d` (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1; one stale Phase-1 test, one plan-side smoke expectation — aamatch/gamestart.py itself needed zero fixes)
**Impact on plan:** None — the starter went headlessly field-verified unchanged on the first real run; the two fixes tighten the gates/tests that watch it.

## Issues Encountered

- The parallel smoke-regression commands initially referenced wrong filenames (`smoke_03_materialize.py`, `smoke_04_engine_e2e.py`); actual files are `smoke_03_generate.py` / `smoke_04_e2e.py` — re-ran, both PASS.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

**03-06/03-07 human-checkpoint notes:**
- The **Plugins → AA-match menu item now STARTS A REAL GAME** — the 03-06/03-07 flow is: fresh stock PyMOL (plugin-path install, repo edits live) → Plugins → AA-match → a defaulted (molecules 2, D 3, unset, seed 42) game materializes with the wizard active. No setup UI yet (Phase 4).
- Restart hygiene is human-verifiable the same way the smoke proves it: click Done, then menu again (replace=0 path); or menu again mid-game WITHOUT Done (replace=1, newest wizard on top, msms restored on Done).
- A user wizard beneath the game auto-resumes after Done (replace=0 push semantics) — the 03-07 B2/B3 checkpoint is true by construction (only replace=1 over a prior GameWizard pops).
- Everything headless now proven: 03-06/03-07 own ONLY the real-mouse/Qt-delivery questions (arrow-key Qt focus path, drag feel, q/e z-sign feel, visual recolor review).

**Phase 4 note:** the Qt setup window calls `gamestart.start_game(setup, seed, candidates=None)` with the user's validated setup — the seam and fail-closed behavior are already proven.

**Blockers:** none carried forward by this plan.

---
*Phase: 03-wizard-gameplay-loop*
*Completed: 2026-09-09*
