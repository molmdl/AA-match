---
phase: 04-qt-setup-window
plan: 13
subsystem: qt-window handlers
tags: [pymol, qt, offscreen, headless-smoke, setup-window, gamestart, seed-policy, SETUP-10]

# Dependency graph
requires:
  - phase: 04-qt-setup-window (04-02, 04-07, 04-09, 04-10, 04-12)
    provides: setup_form.build_state fatal pre-checks; collect_state/apply_state contract; _guard error-surfacing + _X_impl factoring; upload_ready_for + _uploaded session slot; _last_export exported tuple + module-level random
  - phase: 03-wizard-gameplay-loop (03-05)
    provides: gamestart.start_game -- THE one-call seam (cleanup-first -> new_game -> materialize -> GameWizard activate + framing)
provides:
  - _on_start/_start_impl -- SETUP-10 Start handler (configure game in, playable wizard gameplay out)
  - Decision 4 seed policy IMPLEMENTED + headless-proven (Start-after-Generate replays the exported tuple)
  - All 7 spec-order buttons wired -- the Phase-4 setup window is functionally complete
  - SMOKE-11 PART G/G-alt (T1b start drive + probe-FAIL degradation); Gate A2 echo renumbered PART H
affects: [04-14, 04-15 checkpoints, phase-05-game-play-ui]

# Tech tracking
tech-stack:
  added: []
  patterns: [pre-check-before-scene-touch ordering (build_state refuses BEFORE start_game cleans), dict-equality reuse guard on validate_state-normalized states, thin-seam handler (no re-implementation of the start sequence)]

key-files:
  created: []
  modified: [aamatch/setup_window.py, smoke/smoke_11_window.py]

key-decisions:
  - "Seed policy (Decision 4) implemented: last_export setup == freshly built state -> reuse the exported (seed, candidates, ligand_content) tuple; else fresh random + form-mode content (upload: session rows+content; demo: None/None)"
  - "No success dialog for Start -- the materialized scene + wizard panel + gamestart status print ARE the feedback"
  - "Error surfacing via _guard only; build_state refusals fire BEFORE cleanup; later generation refusals (checked-but-unsupported types) clean-then-refuse inside start_game -- accepted residue"

patterns-established:
  - "Ordering law: pure build_state pre-checks run BEFORE the cleanup-first seam, so a doomed Start can never delete prior game objects"
  - "Smoke PART G proves the seam contract end-to-end by driving _start_impl twice and reading the wizard's payload seed (no return value needed -- cmd.get_wizard() is the handle)"

# Metrics
duration: 6min
completed: 2026-09-17
---

# Phase 4 Plan 13: Start Handler (SETUP-10) Summary

**Start button wired as a pre-checked thin seam call: build_state refusals fire before any scene touch, Decision 4 seed policy replays exported games on setup equality, and all 7 spec-order buttons are now live -- SMOKE-11 PART G proves the full drive headlessly.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-09-17T04:29:49Z
- **Completed:** 2026-09-17T04:35:14Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `_on_start`/`_start_impl` landed EXACTLY per the plan's prescriptive snippet: collect -> `upload_ready_for` -> `setup_form.build_state` (fatal pre-checks BEFORE any scene-touching call) -> seed policy -> `gamestart.start_game(setup, seed, candidates, ligand_content)`; `btn_start` connected (all 7 buttons wired)
- Decision 4 seed policy implemented and headless-proven: `_last_export['setup'] == state` (validate_state-normalized dict equality) reuses the exported tuple so Start-after-Generate replays the shared game; otherwise a fresh random seed (generator sub-seed domain) with candidates/content from the form's source mode
- SMOKE-11 PART G green: G1 real game started from the dialog impl (scene +20 `_aam_*`, GameWizard on top, int payload seed); G2 restart replayed exported seed **31337** through the mid-game replace path; G3 reuse guard proven to break on a spinbox change; exact-scene restore via done pop + prefix-only cleanup; PART G-alt probe-FAIL degradation added; Gate A2 echo renumbered PART H
- Verification: `python3.6 -m py_compile aamatch/*.py` green; full WSL suite 688/688 green; `bash smoke/run_smoke.sh smoke/smoke_11_window.py 120` prints `=== SMOKE-11 PASS ===`; static checks (build_state before start_game, thin seam, no QTimer/countdown/Import/Hint code) clean

## Task Commits

Each task was committed atomically:

1. **Task 1: _on_start + _start_impl** - `6d31af8` (feat)
2. **Task 2: SMOKE-11 PART G start drive + export reuse** - `93c6207` (test)

**Plan metadata:** (see docs(04-13) commit)

## Files Created/Modified

- `aamatch/setup_window.py` - SETUP-10 Start handler: `_on_start` (_guard wrapper) + `_start_impl` (collect -> build_state -> seed policy -> start_game; NON-MODAL; docstring carries the ordering law, upload-content rule, Decision 4, no-success-dialog + SETUP-11-absence decisions); `btn_start` connected in `__init__`
- `smoke/smoke_11_window.py` - PART G/G-alt added (start drive + reused-seed proof + reuse-guard break + exact-scene restore, probe-FAIL pure-chain fallback); module docstring updated; Gate A2 echo renumbered PART H

## Decisions Made

None new -- executed the plan's binding decisions verbatim:
- Seed policy (Decision 4): exported tuple reused iff `_last_export['setup'] == build_state(collect())`; dict equality is sound because both sides are validate_state-normalized
- No success dialog for Start (wizard panel + status print are the feedback)
- Post-cleanup generation refusals (e.g. checked-but-unsupported type at generation time) remain accepted residue -- they cannot be pre-checked without cmd-tier typing (single-typing-home law)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The T1b tier (04-01 probe verdict PASS, platform=offscreen) ran the full PART G drive on the first smoke execution; G1/G2/G3 + restore all PASS.

## Authentication Gates

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The setup window is **functionally complete for Phase 4** -- all 7 spec-order buttons wired: Reset, Randomize, Save Setup, Load Setup, Generate and export, Cleanup model, Start
- ROADMAP criterion 4 satisfied to the headless limit: Start turns the configured form into playable wizard gameplay with the decided seed semantics, refusing doomed configurations before any scene change
- Only the [HUMAN] checkpoints remain: 04-14 (visual/UAT) and 04-15 (phase close-out): Start-after-Generate shared-game replay, upload-mode Start with real molecules, modal refusal surfaces (browse/upload/build_state refusals), and the modeless-window lifecycle
- Phase 5 owns all SETUP-11 pieces (Game tab, countdown, timer, initial-state store, Import, Hint) -- deliberately absent here per the phase-4/5 boundary

---
*Phase: 04-qt-setup-window*
*Completed: 2026-09-17*
