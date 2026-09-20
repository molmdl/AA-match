---
phase: 06-scoring-lifecycle-endgame
verified: 2026-09-21T02:19:57+08:00
status: passed
score: 39/39 must-haves verified (the step-1 human re-verify on the in-session fix closed 2026-09-21)
human_verification:
  - test: "Step-1 re-verify (the routed obligation): start a game, Confirm level-1 molecule-1, and watch the 3D viewer"
    expected: "The camera re-frames onto molecule 2's grid (the 06-04 compose seam runs on the molecule branch — commit ff4b519); no manual navigation needed."
    result: "RE-VERIFIED PASS (human, 2026-09-21) — fresh games (molecules_per_level=1, then default 2; AAs picked, molecule 1 Confirmed): camera automatically re-framed/zoomed onto molecule 2's grid after the Confirm; fix ff4b519 verified in the GUI."
---

# Phase 6: Scoring Lifecycle & Endgame Verification Report

**Phase Goal:** The full game semantics work end-to-end: confirm scores and advances, levels escalate, skip/give-up protect the player, restart/reset recover, and the endgame reports the complete result.
**Verified:** 2026-09-21T02:19:57+08:00
**Status:** passed (all mechanical checks PASS; the step-1 human re-verify routed from 06-10 closed 2026-09-21)
**Re-verification:** Yes — step-1 re-verify closed 2026-09-21 (human, real Windows PyMOL 2.5.0); initial verification 2026-09-21T02:19:57+08:00

## Goal Achievement

The ROADMAP Phase-6 success criteria 1–5 are [HUMAN]-tagged; their verdicts rest on the 06-10 consolidated GUI checkpoint (APPROVED-after-fix, 8/9 steps PASS first-pass, step-1 defect fixed in-session as commit ff4b519 with a RED-proven regression assert; the routed step-1 re-verify then RE-VERIFIED PASS on 2026-09-21, closing the overall verdict as APPROVED). This report verifies the artifacts/wiring mechanically and records the now-closed step-1 obligation.

### Observable Truths

Consolidated from the `must_haves` frontmatter of all 10 PLANs (06-01..06-10). Score: **39/39 truths verified** — truth 19 (post-advance camera consistency) verified mechanically post-fix AND by the human visual re-verify (closed 2026-09-21).

| # | Plan | Truth | Status | Evidence |
|---|------|-------|--------|----------|
| 1 | 06-01 | Ended game carries `game_over`, `end_state` ('completed'\|'gave_up'), frozen `final_time` surviving to_dict/from_dict | ✓ VERIFIED | `game_state.py:191-194,245-267`; SMOKE-14 exact 11-key pin includes all three |
| 2 | 06-01 | Every recorded molecule has exactly one keyed score entry | ✓ VERIFIED | `record_molecule_result` writes `score_per_molecule[key]` (game_state.py:299); SMOKE-15 A7 aggregation check |
| 3 | 06-01 | `has_record(level, molecule)` reports one-record status | ✓ VERIFIED | `game_state.py:278-282`; used by the engine guard |
| 4 | 06-01 | `endgame_summary` produces the complete SCORE-07 payload fail-closed | ✓ VERIFIED | `game_state.py:304+`; returned by `engine.give_up`/`complete_game`; SMOKE-15 A7 contract checks |
| 5 | 06-02 | Lifecycle wording pinned in pure `status_text` before Qt wiring | ✓ VERIFIED | 6 builders (`molecule_scored/skipped_lines`, `level_advanced_line`, `game_reset_line`, `game_restarted_line`, `game_ended` family) + `SKIP_/GIVEUP_WARNING_*` + `endgame_lines` + `format_mss` (status_text.py:160-380); tests/test_status_text.py 751 lines; human CONFIRMED all strings |
| 6 | 06-02 | Poll-diff renders lifecycle events via `last_event` marker, never fingerprinting 'result' | ✓ VERIFIED | `status_events` fingerprint (status_text.py:376-384); `_state_dict` carries `last_event` (wizard.py:388); SMOKE-15 C marker checks |
| 7 | 06-02 | Scored debrief reuses `wizard_text.result_lines` verbatim (single home) | ✓ VERIFIED | import at status_text.py:57, use at :219 |
| 8 | 06-02/09 | Endgame block identical for info box and modal (two surfaces, one wording home) | ✓ VERIFIED | `game_window.py:455` (info box) and `:826` (modal) both call `status_text.endgame_lines` |
| 9 | 06-03 | Second Confirm/Skip record on same molecule REFUSED, message names the cause | ✓ VERIFIED | `engine.record_scored` guard → `EngineError('This molecule already has a recorded result…')` (engine.py:504-536) |
| 10 | 06-03 | Skip stores detection-at-skip-time partial score via the same record path + increments skip_count | ✓ VERIFIED | `engine.skip_molecule` → `record_scored` + `skip_count += 1` (engine.py:538-555); human step-3 log `partial score 0.00` |
| 11 | 06-03 | Give Up ends game: counters, end_state, frozen time, summary returned | ✓ VERIFIED | `engine.give_up` (engine.py:630-651); human step-4 endgame block evidence |
| 12 | 06-03 | Level advance rebuilds scene (cleanup → materialize L+1) and advances atomically, timer anchor untouched | ✓ VERIFIED | `engine.advance_level` (engine.py:585-628): `placement.cleanup_game_objects()` BEFORE `materialize`, `game.advance_level()` last; human step-2 timer CONTINUOUS at 8:28 across 3 levels |
| 13 | 06-03 | Endgame summary read op returns the 06-01 contract dict from the live game | ✓ VERIFIED | `engine.endgame_summary` (engine.py:670); consumed by `game_window._refresh_status` (:455) |
| 14 | 06-04 | Start composition can frame ANY molecule index | ✓ VERIFIED | `compose_molecule_view(registry, molecule_index=0)` (gamestart.py:338) + `molecule_index` on all three helpers; SMOKE-08 part-5 index-1 compose PASS |
| 15 | 06-04 | start_game default path byte-identical (additive generalization) | ✓ VERIFIED | SMOKE-08 part-5: "default index == explicit 0 … centroid drift 0.00e+00 A, view drift 0.00e+00" |
| 16 | 06-05 | Confirm records (guarded), shows score+total, then ADVANCES — two position books atomic in ONE op | ✓ VERIFIED | `wizard._confirm_molecule_impl` (:726) → `_advance_after_record` (:694); human step-1 semantics PASS with log evidence |
| 17 | 06-05 | Scored debrief rides the last_event marker, rendered by pure builders | ✓ VERIFIED | `_set_event('molecule_scored', …)`; SMOKE-15 B2 marker check PASS |
| 18 | 06-05 | Level advance rebinds the SAME wizard instance, timer anchor untouched | ✓ VERIFIED | `_rebind_level` (:451); no `activate_game` mid-game; human timer-continuous evidence |
| 19 | 06-05 | After ANY advance, slot maps/ligand/selection/camera consistent for the NEW molecule | ✓ VERIFIED (mechanical + human re-look 2026-09-21) | Fixed by ff4b519: molecule branch of `_advance_after_record` now calls `_compose_active_molecule()` after `_rebind_molecule` (wizard.py:717); RED-proven SMOKE-15 B2 camera assert then 75/75. **Human visual re-verify PASS (2026-09-21)** — camera re-framed onto molecule 2's grid after the Confirm (molecules_per_level=1 then default 2). |
| 20 | 06-06 | Skip advances exactly like Confirm, incl. completing on LAST molecule of LAST level | ✓ VERIFIED | `_skip_molecule_impl` shares `_advance_after_record` (:800-812); human step-3 mercy path + sequencing evidence |
| 21 | 06-06 | Give Up ends the game at the current stage through the _guard seam | ✓ VERIFIED | `wizard.give_up` (:824) → `engine.give_up`; human step-4 PASS |
| 22 | 06-06 | After game over, EVERY gameplay handler refuses visibly ('The game is over.') | ✓ VERIFIED | `_require_playing` (:558-564) called first-line at 8 gameplay impls (movement :581/:603/:630/:659, confirm :728, skip :800, give-up :848, reset :881/:918) |
| 23 | 06-06 | Reset emits the game_reset marker | ✓ VERIFIED | `_set_event('game_reset')` (wizard.py:891); SMOKE-15 C5 marker PASS |
| 24 | 06-07 | Game tab has Confirm button + Skip/Give-Up dropdown with spec-required warnings | ✓ VERIFIED | `btn_confirm` (:177), `btn_skip_menu` QToolButton+QMenu (:190-206); `QMessageBox.question` with `SKIP_WARNING_*`/`GIVEUP_WARNING_*` in `_on_skip`/`_on_giveup`; human step-3/4 saw both boxes |
| 25 | 06-07 | Tab-triggered ops log ZERO-latency (synchronous poll after the op) | ✓ VERIFIED | `_confirm_now`/`_skip_now`/`_giveup_now` each call `self._refresh_status()` right after the op (:543, :634 area) |
| 26 | 06-07 | Required-interactions label refreshes on LEVEL change (stale-label fix) | ✓ VERIFIED | `game_window.py:440-443`: `prev.get('level_pos') != state.get('level_pos')` condition present |
| 27 | 06-07 | Impls non-modal/headless-driveable; ONLY wrappers own boxes | ✓ VERIFIED | `_confirm_now`/`_skip_now`/`_giveup_now`/`_restart_now`/`_reset_grid_now` are box-free; `_on_skip`/`_on_giveup` own the only modals; SMOKE-16 A/B/C drove impls headlessly (67/67) |
| 28 | 06-08 | Restart replays `_last_start` verbatim through the deferred sequence | ✓ VERIFIED | `_restart_now` (:691-701): `gamestart._last_start` → `start_game(setup/seed/candidates/ligand_content, activate=False)` → `start_countdown` → `game_restarted_line()` logged AFTER the arm (D7 order); human step-6 log-order PASS |
| 29 | 06-08 | Restart with nothing started refuses with a clear message | ✓ VERIFIED | `raise ValueError('Restart: no game has been started yet.')` (:695) |
| 30 | 06-08 | Reset routes through the wizard's PUBLIC `reset_grid()` behind the isinstance gate (never engine.reset_to_grid from the tab) | ✓ VERIFIED | `_reset_grid_now` (:735-760): isinstance gate → `prior.reset_grid()` → `_refresh_status()` |
| 31 | 06-08 | Reset keeps the timer running and touches NO GameState | ✓ VERIFIED | SMOKE-15 C5 "reset touches NO GameState (to_dict equality) PASS"; human step-7 timer running |
| 32 | 06-09 | Endgame modal ~100 ms after the pop burst, on-top, pure endgame_lines content | ✓ VERIFIED | `cmd.refresh()` + `QTimer.singleShot(100, …)` in `_on_skip`/`_on_giveup` (+ confirm tail); `_show_endgame_modal` (:790-837): parent `self.window()`, `WindowStaysOnTopHint`, `setText(lines[0])` + `setInformativeText('<br>'.join(lines[1:]))`; human step-4 modal ABOVE viewer |
| 33 | 06-09 | 1 Hz timer explicitly stopped at game end; label holds the EXACT final M:SS | ✓ VERIFIED | `_endgame_sequence` (:765-786): `self._timer.stop()` FIRST → `_timer_label.setText(format_mss(summary['final_time']))` → pop; human step-4/6 frozen labels |
| 34 | 06-09 | Full six-smoke regression battery green before the human checkpoint | ✓ VERIFIED (re-run today) | SMOKE-04 25 ✓, 08 ✓ (part-5 present), 11 51 ✓, 14 29 ✓, 15 **75/75** ✓, 16 **67/67** ✓ — all `=== SMOKE-0N PASS ===` |
| 35 | 06-10 | Human played a full lifecycle on real PyMOL; all five ROADMAP criteria carry [HUMAN] verdicts | ✓ VERIFIED (criterion 1 = fixed-after-defect, re-verify PASS 2026-09-21) | 06-10-SUMMARY verdict table: 8/9 PASS; step 1 DEFECT→FIXED (ff4b519) with human verbatim defect quote; re-verify **RE-VERIFIED PASS (human, 2026-09-21)** — camera auto re-framed onto molecule 2's grid |
| 36 | 06-10 | Pinned Phase-6 wording human-CONFIRMED or amended in-session | ✓ VERIFIED | Wording Verdicts section: every string class CONFIRMED, zero amendments (12-row coverage map) |
| 37 | 06-10 | Timer freeze under the NEW warning modals human-confirmed (P-5 class) | ✓ VERIFIED | Step-3 frozen-label evidence under the Skip warning box |
| 38 | 06-03/06-09 | `engine.give_up/complete_game` → `endgame_summary` returned as plain data through the op | ✓ VERIFIED | engine.py:651/669 `return endgame_summary()`; consumed by the tab's endgame tail |
| 39 | 06-01/06-02 | `engine.game_status()` grows the lifecycle keys additively (to_dict contract) | ✓ VERIFIED | SMOKE-14 exact-key pin: `['current_level_index', 'current_molecule_index', 'end_state', 'final_time', 'formed_types_per_molecule', 'game_over', 'giveup_count', 'molecule_scores', 'score_per_molecule', 'skip_count', 'timer_anchor']` |

**Score:** 39/39 truths verified (truth 19 verified mechanically post-fix AND by the human visual re-verify, closed 2026-09-21)

### Required Artifacts (three-level check)

| Artifact | Expected | Exists | Substantive | Wired | Status |
|----------|----------|--------|-------------|-------|--------|
| `aamatch/game_state.py` | lifecycle data layer (stop_timer/has_record/endgame_summary/keyed store) | ✓ (455 ln) | ✓ all defs present, no stubs | ✓ used by engine/wizard/status pin | ✓ VERIFIED |
| `tests/test_game_state.py` | WSL battery for the lifecycle layer | ✓ (735 ln) | ✓ (inside 826/826 green) | ✓ runs in the suite | ✓ VERIFIED |
| `aamatch/status_text.py` | 6 event builders + warning constants + endgame_lines + format_mss | ✓ (406 ln) | ✓ | ✓ imported by wizard + game_window | ✓ VERIFIED |
| `tests/test_status_text.py` | battery pinning every Phase-6 string | ✓ (751 ln) | ✓ | ✓ | ✓ VERIFIED |
| `aamatch/engine.py` | record_scored/skip/advance_level/give_up/complete_game/summary ops | ✓ (697 ln) | ✓ all 9 ops present | ✓ routed by wizard | ✓ VERIFIED |
| `aamatch/gamestart.py` | `compose_molecule_view` + molecule_index params + `_last_start` | ✓ (464 ln) | ✓ | ✓ used by wizard compose + tab restart | ✓ VERIFIED |
| `aamatch/wizard.py` | confirm rework, `_advance_after_record`, skip/give_up, `_require_playing`, reset + marker, ff4b519 fix | ✓ (993 ln) | ✓ | ✓ dispatched by tab, poll-integrated | ✓ VERIFIED |
| `aamatch/game_window.py` | Confirm/Skip dropdown/Restart/Reset buttons, warnings, endgame seq+modal, label fix | ✓ (855 ln) | ✓ all 14 handlers present | ✓ buttons connected (:229-233), wizard-dispatch gated | ✓ VERIFIED |
| `smoke/smoke_14_status_surface.py` | exact 11-key pin evolution | ✓ (455 ln) | ✓ 28 checks | ✓ PASS re-run | ✓ VERIFIED |
| `smoke/smoke_15_lifecycle.py` | PART A/B/C lifecycle E2E incl. B2 camera assert | ✓ (975 ln) | ✓ 75 checks | ✓ PASS re-run (75/75) | ✓ VERIFIED |
| `smoke/smoke_16_tab.py` | PART A/B/C tab battery + final-timer asserts | ✓ (939 ln) | ✓ 67 checks | ✓ PASS re-run | ✓ VERIFIED |
| `.planning/…/06-10-SUMMARY.md` | verdict table + fix-batch record | ✓ | ✓ contains APPROVED | ✓ n/a (record) | ✓ VERIFIED |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `game_state.record_molecule_result` | `score_per_molecule[molecule_key(level, molecule)]` | same-call keyed write | ✓ WIRED |
| `engine.record_scored` | `GameState.has_record` | the ONE guard site for Confirm AND Skip | ✓ WIRED (engine.py:524-527) |
| `engine.advance_level` | `placement.cleanup_game_objects` + `materialize` | cleanup BEFORE materialize; GameState LAST; timer anchor untouched | ✓ WIRED (engine.py:622-626) |
| `engine.give_up`/`complete_game` | `game_state.endgame_summary` | summary returned as plain data | ✓ WIRED |
| `status_text` | `wizard_text.result_lines` | import + verbatim reuse (single-home law) | ✓ WIRED (:57, :219) |
| `status_text.status_events` | `event['last_event']` marker | one fingerprint key, event lines before position line | ✓ WIRED (:376-384) |
| `wizard._confirm_molecule_impl` | `engine.record_scored` | guarded record (re-Confirm refusal inherited) | ✓ WIRED (:732) |
| `wizard._advance_after_record` | `engine.advance_molecule/advance_level/complete_game` | ONE advancement decision site | ✓ WIRED (:714-724) |
| `wizard._advance_after_record` (molecule branch) | `_compose_active_molecule` | **ff4b519 fix**: compose after rebind | ✓ WIRED (:717) + SMOKE-15 B2 assert |
| `wizard.skip_molecule` | `engine.skip_molecule` + `_advance_after_record` | same shared path as Confirm | ✓ WIRED (:802, :809) |
| `wizard.give_up` | `engine.give_up` | summary plain through _guard; no self-pop | ✓ WIRED (:852) |
| `wizard._require_playing` | `engine.is_over` | single gate home, 8 call sites | ✓ WIRED |
| `wizard._state_dict` | `status_text.status_events` | additive `last_event/game_over/end_state` keys | ✓ WIRED (:388) |
| `wizard._reset_grid_impl` | `game_reset` marker | `_set_event('game_reset')` | ✓ WIRED (:891) |
| `game_window._confirm_now` | `GameWizard.confirm_molecule()` | isinstance gate + sync `_refresh_status` + endgame seq | ✓ WIRED (:535-547) |
| `game_window._on_skip/_on_giveup` | `SKIP_WARNING_*/GIVEUP_WARNING_*` | `QMessageBox.question` Yes\|No, gate BEFORE box | ✓ WIRED |
| `_refresh_status` label condition | `level_pos` | molecule_id OR level_pos refresh | ✓ WIRED (:443) |
| `game_window._restart_now` | `gamestart._last_start` + `start_game(activate=False)` | spec replay (backup.py has NO role here — confirmed: no backup import in game_window restart path) | ✓ WIRED |
| `game_window._reset_grid_now` | `GameWizard.reset_grid()` | isinstance-gated public op | ✓ WIRED |
| `game_window._restart_now` | `status_text.game_restarted_line()` | logged AFTER the arm (D7) | ✓ WIRED (:701) |
| wrappers | `_show_endgame_modal(summary)` | `cmd.refresh()` + `singleShot(100, …)` AFTER the pop burst | ✓ WIRED |
| `_show_endgame_modal` | `status_text.endgame_lines` | setText(lines[0]) + `'<br>'.join(lines[1:])` | ✓ WIRED (:826-831) |
| `_endgame_sequence` | timer stop + exact final label | `self._timer.stop()` FIRST, `format_mss(final_time)` | ✓ WIRED (:776-780) |

### Standing Gates (re-run 2026-09-21)

| Gate | Result |
|------|--------|
| `python3.6 -m py_compile aamatch/*.py` | OK |
| `python3.6 -m unittest discover -s tests` | **Ran 826 tests — OK** (purity gates included) |
| SMOKE-04 | === SMOKE-04 PASS === (25 PASS lines) |
| SMOKE-08 | === SMOKE-08 PASS === (part-5 compose proof + default==explicit-0 present) |
| SMOKE-11 | === SMOKE-11 PASS === (51 PASS lines) |
| SMOKE-14 | === SMOKE-14 PASS === (29 PASS lines; 11-key exact pin confirmed) |
| SMOKE-15 | === SMOKE-15 PASS === (**"PART A: 28; PART B: 23; PART C: 24; TOTAL 75, 0 failure(s)"**; B2 camera assert PASS) |
| SMOKE-16 | === SMOKE-16 PASS === (**"PART A: 30; PART B: 23; PART C: 14; total 67, 0 failure(s)"**) |
| Fix commit ff4b519 | present in git log; `wizard.py` +13/−4 (compose call + docstring), `smoke_15_lifecycle.py` +24/−1 (B2 assert) — exactly as the 06-10 SUMMARY describes |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| SCORE-01 | ✓ SATISFIED | None — semantics + wording human-PASSed with log evidence; camera re-frame aspect of the post-confirm advance closed by the step-1 visual re-verify PASS (human, 2026-09-21; code fixed + headless-proven) |
| SCORE-02 | ✓ SATISFIED | None — debrief renders formed vs missed (numbers only) via `result_lines` reuse; human CONFIRMED |
| SCORE-03 | ✓ SATISFIED | None — level advance human-PASSed (new grids, camera-framed, timer continuous) |
| SCORE-05 | ✓ SATISFIED | None — skip warning + partial-score semantics human-PASSed |
| SCORE-06 | ✓ SATISFIED | None — give-up warning + game-end human-PASSed |
| SCORE-07 | ✓ SATISFIED | None — endgame screen (give-up + natural end) human-PASSed; modal + info box one wording home |
| SCORE-09 | ✓ SATISFIED | None — restart human-PASSed (D7 log order, counters zeroed, timer from zero) |
| SCORE-10 | ✓ SATISFIED | None — reset human-PASSed (grid restore, rotations kept, timer running) |

Note: the REQUIREMENTS.md status table listed these 8 as "Pending" at verify time — updated to "Complete" at phase close (2026-09-21) after the step-1 re-verify closure; never a code gap.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| aamatch/gamestart.py | 149 | docstring notes a scheme check is "explicitly NOT implemented" | ℹ️ Info | Documented design decision (scope note), not a stub |
| .planning/ROADMAP.md | Phase-6 plan list | 06-05..06-09 checkboxes still `[ ]` although all are complete with SUMMARYs | ℹ️ Info | ROADMAP checkbox staleness at verify time; resolved at phase close (2026-09-21 — all ten 06-01..06-10 boxes ticked) |

No TODO/FIXME/placeholder markers, no empty handlers, no orphaned artifacts in any Phase-6 file.

### Human Verification — Verified Items

### 1. Step-1 re-verify — molecule-advance camera re-frame (the routed obligation) — ✓ RE-VERIFIED PASS (human, 2026-09-21)

**Test (as prescribed):** Start a game; Confirm level-1 molecule-1 (with ≥1 interaction formed); observe the 3D viewer immediately after the confirm pop.
**Expected:** The camera re-frames onto molecule 2's grid (its objects centered/zoomed — the same framing a level advance gives), with no manual navigation needed.
**Result (2026-09-21, real Windows PyMOL 2.5.0):** PASS — fresh games started (first molecules_per_level=1: 1 molecule / 9 slots; then default 2 molecules / 18 slots), AAs picked, molecule 1 Confirmed; the camera automatically re-framed/zoomed onto molecule 2's grid after the Confirm. Fix `ff4b519` confirmed working in the GUI; the human typed "approved".
**Why human (original):** Visual camera behavior; the headless proof (SMOKE-15 PART B2 view-delta assert, RED-proven pre-fix, 75/75 post-fix) existed, and the ROADMAP criterion-1 [HUMAN] verdict is now closed (2026-09-21). Previously recorded as PENDING in 06-10-SUMMARY.md and STATE.md Pending Todos — now resolved in both.

Everything else the ROADMAP tags [HUMAN] (criteria 2–5, wording, timer-freeze-under-warnings, console cleanliness) was verified in the 06-10 session and needed no repeat.

### Gaps Summary

No code gaps. All 39 must-have truths are verified against the actual codebase at all three levels (exists / substantive / wired), all 23 key links are wired, the full standing-gate battery is green as re-run today (826/826 WSL incl. purity gates; six smokes PASS with 75/75 and 67/67 tallies confirmed), and the ff4b519 fix commit is present with the described content. The single open item — the step-1 human re-verify routed from the 06-10 checkpoint — is **CLOSED (2026-09-21)**: the in-level molecule-advance camera re-frame was defective, was fixed in-session with a RED-proven regression assert, and the short GUI confirmation ran the same day (camera re-framed onto molecule 2's grid after the Confirm; human "approved"). Status is therefore **passed** — the phase goal is achieved in code and in the human checkpoint (8/9 first-pass + the step-1 re-verify closure).

---

_Verified: 2026-09-21T02:19:57+08:00_
_Verifier: OpenCode (gsd-verifier)_
