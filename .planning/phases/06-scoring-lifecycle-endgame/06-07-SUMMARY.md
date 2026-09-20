---
phase: 06-scoring-lifecycle-endgame
plan: 07
subsystem: ui
tags: [qt, game-tab, lifecycle, confirm, skip, give-up, endgame, thin-wrapper-impl, headless-smoke, python3.6]

# Dependency graph
requires:
  - phase: 06-scoring-lifecycle-endgame (06-02)
    provides: "status_text Phase-6 surface: SKIP_WARNING_*/GIVEUP_WARNING_* pinned strings, endgame_lines (SCORE-07 block), molecule_scored/skipped + gave_up line builders, format_mss"
  - phase: 06-scoring-lifecycle-endgame (06-05)
    provides: "confirm_molecule() plain-dict return {score,total,advanced,game_over,summary,level_pos,molecule_pos} through the wizard _guard; the additive _state_dict keys (last_event/game_over/end_state)"
  - phase: 06-scoring-lifecycle-endgame (06-06)
    provides: "skip_molecule() (same confirm dict shape) and give_up() ({game_over:True,summary,level_pos,molecule_pos}; the wizard does NOT self-pop — the tab's endgame sequence owns the pop); the 'The game is over.' gate; marker kinds (molecule_skipped/gave_up)"
  - phase: 05-game-status-tab-start-sequence (05-06..05-11)
    provides: "GameTab shell + _guard + _hint_now wrapper/impl precedent + _refresh_status poll-diff + the button-row stretch + the 1 Hz tick's modal-pause branch (warnings freeze the clock with zero new code)"
provides:
  - "Game tab Confirm button (spec.md:41) + Skip/Give-Up QToolButton+QMenu dropdown (spec.md:42) whose wrappers gate isinstance-FIRST (silent no-op pre-GO) then show the pinned QMessageBox.question Yes|No warnings"
  - "_on_confirm/_on_skip/_on_giveup thin MODAL wrappers -> _confirm_now/_skip_now/_giveup_now NON-MODAL impls (the 04-09 _X_impl law; wrappers shaped for 06-09's modal-scheduling tail)"
  - "Zero-latency lifecycle logging: every impl runs _refresh_status() SYNCHRONOUSLY after the wizard op — scored/skipped/gave-up lines + position lines land without a 1 Hz poll wait"
  - "_endgame_sequence (stop the 1 Hz timer — v1 _on_win precedent — pin the EXACT final-elapsed label, pop the wizard) + the GameTab _pop_game_wizard helper (the setup_window.py:826 seam shape)"
  - "The required-label fix: refresh on molecule_id OR level_pos change (molecule_id repeats across levels); the poll's ONE game_over-transition logging home (endgame_lines, fires exactly once per game end)"
  - "SMOKE-16 PART A (30 checks): T1b impl-driven proof of the whole surface incl. the sync refresh, the give-up endgame tuple, and the label fix"
affects: [06-08-restart-reset-wiring, 06-09-endgame-screen-modal, 06-10-human-endgame-checkpoint]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Tab-triggered lifecycle op = isinstance gate -> wizard op -> SYNCHRONOUS _refresh_status() -> conditional shared _endgame_sequence: one uniform code path for confirm/skip/give-up (the 06-06 uniform-return contract pays off verbatim)"
    - "The poll-diff owns the game_over TRANSITION block (prev False -> curr True): single logging home for both tab-triggered ends (sync refresh) and panel-triggered ends (1 Hz tick), firing exactly once with no double-log"
    - "Insert-before-stretch row-order law: every new button lands via insertWidget(btn_row.count() - 1, w) so the stretch stays LAST and the timer row never reflows"

key-files:
  created:
    - smoke/smoke_16_tab.py
  modified:
    - aamatch/game_window.py

key-decisions:
  - "The required label refreshes on level_pos change too (not just molecule_id): molecule_id repeats across levels ('mol-001' again — generator numbers molecules within each level), so the 05-10 condition left level 1's requirement showing on level 2; the fix is level_pos-aware and SMOKE-16 A7 pins identity against required_display(get_status)"
  - "_endgame_sequence order is stop-first, label-pin, pop-last (v1 _on_win precedent): the engine's GameState stays LIVE after the game ends, so a running tick would advance the label forever over a finished game; the label is pinned to format_mss(summary['final_time']), not the <=1 s-stale tick value"
  - "GameTab gets its OWN _pop_game_wizard helper (lazy cmd+wizard imports, isinstance gate, canonical cmd.set_wizard() None-pop) instead of reaching for SetupWindow's — the tab must not cross the composition root; the _aam_* scene survives the pop (Done semantics, D6)"

patterns-established:
  - "Lifecycle impl return contract on the tab: wizard-op dict straight through, None on guarded refusal (panel already surfaced — the hint precedent), headless smokes assert the dict + the info-box lines"
  - "Warning wrappers hold ZERO timer code: the tick's activeModalWidget->rebase_timer branch freezes the clock over ANY real modal (caller-owns-modal-detection law), so wrappers never call rebase_timer"

# Metrics
duration: 25 min
completed: 2026-09-20
---

# Phase 6 Plan 07: Game Tab Lifecycle Controls (Part 1) Summary

**The Game tab's lifecycle controls land: Confirm button + Skip/Give-Up dropdown with the spec-pinned Yes|No warnings in thin wrappers, box-free impls whose synchronous poll-diff delivers zero-latency scored/skipped/gave-up logging, the shared _endgame_sequence (clock stop + exact final time + wizard pop), the game_over transition's single logging home, the cross-level required-label fix, and SMOKE-16 PART A proving all of it headlessly (30/30)**

## Performance

- **Duration:** 25 min
- **Started:** 2026-09-20T14:10:08Z
- **Completed:** 2026-09-20T14:35Z
- **Tasks:** 3
- **Files modified:** 2 (1 code + 1 smoke)

## Accomplishments

- **Confirm button (SCORE-01/03 UI, spec.md:41):** `btn_confirm` joined `btn_hint` on the row via insert-before-stretch (the timer-row no-reflow law); `_on_confirm` -> `_guard(_confirm_now)` with NO warning (Confirm is the routine action); `_confirm_now` dispatches to `GameWizard.confirm_molecule()` behind the isinstance gate, runs `_refresh_status()` SYNCHRONOUSLY (scored line + result_lines debrief + new position line land with zero 1 Hz loss), and hands a completed game to `_endgame_sequence`
- **Skip/Give-Up dropdown (SCORE-05/06 UI, spec.md:42):** `btn_skip_menu` QToolButton+QMenu (InstantPopup, spec-literal "dropdown button") with 'Skip Molecule' / 'Give Up...' actions; both wrappers GATE FIRST (no live GameWizard -> silent no-op BEFORE any box — a countdown-window press is inaudible), then `QMessageBox.question` Yes|No with the pinned 06-02 SKIP_WARNING_*/GIVEUP_* strings as modal children (Escape reads No); YES routes the impl through `_guard`; ZERO rebase_timer anywhere (the tick's modal-pause branch owns the freeze); wrapper structure left stable for 06-09's modal-scheduling tail
- **`_endgame_sequence` + `_pop_game_wizard`:** stop the 1 Hz timer FIRST (the engine GameState stays live post-end, v1 _on_win precedent), pin `_timer_label` to the EXACT `format_mss(summary['final_time'])`, then the isinstance-gated canonical None-pop (Done semantics — scene survives; the pop's color-restore burst is what 06-09's refresh+singleShot modal lands after)
- **Latent stale-label bug FIXED:** the 05-10 refresh keyed on `molecule_id` only, which repeats across levels ('mol-001' again) — level 1's requirement kept showing on level 2; the condition is now molecule_id-OR-level_pos and SMOKE-16 A7 pins identity against `required_display(level-2 required)` from a live `get_status()`
- **ONE game_over logging home:** the poll-diff gained a transition block (prev False -> curr True) logging `status_text.endgame_lines(engine.endgame_summary())` — serving tab-triggered ends (via the sync refresh) AND panel-triggered ends (via the 1 Hz tick) exactly once each; SMOKE-16 A6 asserts the headline count is 1
- **SMOKE-16 PART A (30/30 PASS, first run):** T1b construction inventory (controls, menu, tooltips, stretch-LAST, fresh placeholders), live countdown -> GO, impl-driven confirm/skip/give-up with the pinned lines, the zero-latency proof (asserts run pre-pump), the give-up endgame tuple (timer stopped, exact-time label, wizard popped, required label stable), the label fix, the no-wizard impl-gate None proof (wrappers stay [HUMAN]-only for 06-10), and an exact baseline restore
- **Regressions green:** SMOKE-11 PASS (two-tab structure + placeholder pins intact), SMOKE-14 PASS (status-surface wiring untouched), 826/826 WSL, `py_compile` clean, grep law holds (zero `engine._game`/`engine._payload` hits in game_window.py)

## Task Commits

Each task was committed atomically:

1. **Task 1: Confirm button + impl + required-label fix + poll game_over block** — `df94bbc` (feat)
2. **Task 2: Skip/Give-Up dropdown + warning wrappers + impls** — `2e6f6ba` (feat)
3. **Task 3: SMOKE-16 creation + PART A (tab drive)** — `d4600a8` (test)

## Files Created/Modified

- `aamatch/game_window.py` — `btn_confirm` + `_on_confirm`/`_confirm_now`; `btn_skip_menu`/`act_skip`/`act_giveup` + `_on_skip`/`_on_giveup`/`_skip_now`/`_giveup_now`; `_endgame_sequence` + `_pop_game_wizard`; the level_pos-aware required-label fix + the game_over transition block in `_refresh_status`; module/class/handler docstrings updated (ROLE paragraph, button inventory, smoke-99/06-09 notes)
- `smoke/smoke_16_tab.py` — NEW; SMOKE-16 PART A (30 checks, T1b house recipe: offscreen platform first, QApplication reuse-or-create, ZERO modals — impls driven as methods, never wrappers)

## Decisions Made

- Recorded in frontmatter: the level_pos-required-label fix rationale; the stop-first/label-pin/pop-last endgame order; the tab-side `_pop_game_wizard` (no composition-root crossing); wrappers carry zero timer code under the caller-owns-modal-detection law.

## Deviations from Plan

None - plan executed exactly as written. (Two in-flight self-corrections before the task commits — an insert-before-the-stretch-existed row ordering and a docstring prose mention of the `engine._game` grep token — were caught and fixed within their own task edit before any commit; the committed code matches the plan's action list verbatim.)

## Issues Encountered

None — SMOKE-16 PART A passed 30/30 on the FIRST run; SMOKE-11 and SMOKE-14 regressions PASS unchanged; 826/826 WSL green throughout; PROSE_PIN and test_wizard_source SCANNED_MODULES untouched (game_window.py was already scanned).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **06-08 (Restart/Reset wiring)** consumes: the same insert-before-stretch row slots (Restart/Reset buttons), the impl + sync-refresh pattern (the game_reset marker already flows through status_events), and `game_restarted_line()`'s tab-handler-logged channel (excluded from the poll table by design).
- **06-09 (endgame screen modal)** consumes: `_endgame_sequence` (its refresh+singleShot modal lands AFTER the pop's color-restore burst), the wrappers' stable structure (only the modal-scheduling tail is added), `status_text.endgame_lines` (the modal and the info box render the SAME block — lines[0] is the headline), and the give_up/completion summary shape.
- **06-10 ([HUMAN] endgame checkpoint)** owns the never-headless tails: the QMessageBox.question warnings' look/feel + timer freeze under them, and the modal endgame screen itself.
- Standing gates green at handoff: 826/826 WSL, SMOKE-16 30/30 PART A PASS, SMOKE-11 PASS, SMOKE-14 PASS, grep law zero-hit.

---
*Phase: 06-scoring-lifecycle-endgame*
*Completed: 2026-09-20*
