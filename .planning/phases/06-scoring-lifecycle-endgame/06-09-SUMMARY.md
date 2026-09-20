---
phase: 06-scoring-lifecycle-endgame
plan: 09
subsystem: ui
tags: [qt, endgame-modal, qmessagebox, singleShot, windowstaysontophint, timer-stop, natural-end, headless-smoke, regression-battery, python3.6]

# Dependency graph
requires:
  - phase: 06-scoring-lifecycle-endgame (06-07)
    provides: "_endgame_sequence order law (stop timer -> exact final label -> pop) + the stable _on_confirm/_on_skip/_on_giveup wrapper structures (shaped for this plan's modal tail) + the poll's ONE game_over-transition logging home"
  - phase: 06-scoring-lifecycle-endgame (06-08)
    provides: "_restart_now/_reset_grid_now impls + SMOKE-16 PART A+B state (53/53) PART C appends to"
  - phase: 06-scoring-lifecycle-endgame (06-02)
    provides: "status_text.endgame_lines (headline always lines[0]; the SAME pinned block both surfaces render) + format_mss"
  - phase: 06-scoring-lifecycle-endgame (06-01)
    provides: "the exact 11-key endgame_summary contract the modal consumes"
provides:
  - "_show_endgame_modal(summary): the SCORE-07 endgame MODAL -- child QMessageBox (parent self.window() + WindowStaysOnTopHint, Information icon, 'AA-match' title, headline setText + rich-text informative stats) rendering the SAME pinned endgame_lines block as the info box"
  - "The wrapper modal-scheduling tails (v1 _finish_win pattern): cmd.refresh() + QTimer.singleShot(100, ...) on _on_confirm/_on_skip/_on_giveup, wrapper-ONLY (smoke-99/P-6 law), AFTER the pop's color-restore burst"
  - "SMOKE-16 PART C (14 checks): the natural-end drive (confirm/skip through every molecule of every level), the stopped timer + EXACT final M:SS label, the win-headline-once + full-block info-box pins, post-endgame inertness, the Restart composition (restart-reset Q5)"
  - "The full Phase-6 mechanical regression battery record (all six smokes green + 826/826 WSL) -- the 06-10 human checkpoint's mechanical input"
affects: [06-10-human-endgame-checkpoint, phase-7-persistence]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Endgame modal scheduling = wrapper-owned v1 _finish_win mechanics: stop-the-timer FIRST (06-07's _endgame_sequence) -> pop -> cmd.refresh() -> QTimer.singleShot(100, show-modal) scheduled by the WRAPPER only, so the pop's color-restore burst paints BEFORE the modal's exec_() nested loop stops redraw servicing (v1 Bug A); parent self.window() + WindowStaysOnTopHint keeps the box ABOVE the OpenGL viewer (v1 Bug B)"
    - "Two-surface discipline for the SCORE-07 block: the modal is the MOMENT, the info box is the RECORD -- both render status_text.endgame_lines verbatim (setText = lines[0], setInformativeText = '<br>'.join(lines[1:])), one wording home, zero drift"
    - "Smoke structural pin for an undriveable member: hasattr + callable + docstring comment (never a source scan inside a smoke); the real exec_() drive stays [HUMAN]-only"

key-files:
  created: []
  modified:
    - aamatch/game_window.py
    - smoke/smoke_16_tab.py

key-decisions:
  - "The 100 ms modal delay is the v1-SHIPPED value kept verbatim -- no new constant (both v1 bug-fix rationales carried in the method docstring: Bug A clobbered redraw / Bug B hidden dialog)"
  - "The wrappers' tail keys on (truthy result AND result.get('game_over')) uniformly across all three wrappers -- a None guarded-refusal result schedules nothing (the _guard box already fired)"
  - "Modal content = EXACTLY the pure endgame_lines block (no hand-authored strings): headline on setText, '<br>'-joined rest on setInformativeText (Qt rich text, the v1 stats shape); human wording re-confirmation is 06-10's confirm-step, not a blocking gate"

patterns-established:
  - "Natural-end smoke proof shape: drive the tab IMPLS through every molecule of every level (zero-score records sufficient -- smoke_04 owns score correctness), assert the endgame tuple on the LAST op, then the four-part state pin (block lines / stopped timer / EXACT label / popped wizard), then post-endgame inertness AND the Restart composition (the endgame state is never a dead end)"

# Metrics
duration: 16 min
completed: 2026-09-20
---

# Phase 6 Plan 09: Endgame Screen Modal + Full Regression Battery Summary

**The SCORE-07 endgame modal lands with the v1-proven fairness mechanics — the wrappers schedule a `self.window()`-parented + stay-on-top QMessageBox via `cmd.refresh()` + `QTimer.singleShot(100, ...)` AFTER the pop's color-restore burst, rendering the exact `status_text.endgame_lines` block the info box also carries (modal = the moment, info box = the record) — SMOKE-16 PART C proves the natural end headlessly (stopped 1 Hz timer, EXACT final M:SS label, popped wizard, win headline logged once, Restart composition from the endgame state), and the complete six-smoke regression battery + 826/826 WSL suite close Phase 6's mechanical proof for the 06-10 human checkpoint.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-09-20T15:27:32Z
- **Completed:** 2026-09-20T15:43:03Z
- **Tasks:** 3
- **Files modified:** 2 (1 code + 1 smoke)

## Accomplishments

- **The endgame modal (SCORE-07, spec.md:57-58):** `_show_endgame_modal(summary)` is the v1 `_finish_win` shape transcribed to the tab — child `QMessageBox` with parent `self.window()` + `Qt.WindowStaysOnTopHint` (v1 Bug B: the box appears ABOVE the OpenGL viewer), Information icon, title 'AA-match', `setText(endgame_lines(summary)[0])` (the pinned headline: 'You win! ...' / 'Game over -- gave up ...'), `setInformativeText('<br>'.join(lines[1:]))` (Qt rich text stats — per-level scores, total, time, molecules/levels, skips/give-ups; the v1 stats shape), `exec_()` (the sanctioned child-modal class). Zero hand-authored strings — all wording from the pure `endgame_lines` home.
- **The wrapper scheduling tails (v1 `_on_win` mechanics):** `_on_confirm`/`_on_skip`/`_on_giveup` now capture the guarded result and, on truthy + `game_over`, run `cmd.refresh()` + `QtCore.QTimer.singleShot(100, lambda: self._show_endgame_modal(summary))` — the ~100 ms gap stays the v1-shipped constant (Bug A: a modal `exec_()` nested loop stops redraw servicing, so the pop's color-restore burst must paint FIRST). The tails live in the WRAPPERS ONLY (the smoke-99 law: impls and the tick never own boxes, so headless smokes drive the impls and never fire the modal); a None guarded-refusal result schedules nothing.
- **SMOKE-16 PART C (14 checks, first-run PASS):** the natural-end drive — countdown GO, then confirm/skip through EVERY molecule of EVERY level (5 confirms + 1 skip; zero-score records sufficient and documented — smoke_04 owns score correctness) until the LAST confirm returns `game_over True` + `end_state 'completed'`. Asserted: the final molecule's pinned scored line; the win headline 'You win! All 3 level(s) finished in' logged EXACTLY once (one transition home); the full `endgame_lines` block with literal pins ('Level N: 0.00' ×3, 'Total score: 0.00.', a 'Time:' line, 'Molecules completed: 6 of 6. Levels: 3.', 'Skips: 1. Give-ups: 0.'); the 1 Hz timer STOPPED (the tick cannot stop the clock); `_timer_label == format_mss(summary['final_time'])` EXACT; the wizard POPPED; post-endgame inertness (all three impls return None behind the isinstance gate); and the endgame state COMPOSES with Restart (`_restart_now` arms a fresh countdown, box == ['Get ready...', 'Game restarted.'], GO brings a fresh live game — restart-reset Q5). The phase regression record lines ('SMOKE-0N: PASS/NOT-RUN') print at the file's end for the orchestrator battery grep.
- **The full Phase-6 mechanical regression battery — ALL GREEN:**

  | Smoke | Verdict | Checks | Role |
  |---|---|---|---|
  | SMOKE-04 | PASS | 25/25 | engine byte-identity guard (E2E) |
  | SMOKE-08 | PASS | 41/41 | start seam + deferred-start compose |
  | SMOKE-11 | PASS | 51/51 | window/two-tab/countdown/cleanup/_last_start pins |
  | SMOKE-14 | PASS | 29/29 | status surface + 11-key game_status pin |
  | SMOKE-15 | PASS | 74/74 (A 28 + B 22 + C 24) | engine/wizard lifecycle |
  | SMOKE-16 | PASS | 67/67 (A 30 + B 23 + C 14) | tab lifecycle A+B+C |

  Plus `python3.6 -m py_compile aamatch/*.py` clean and the FULL WSL suite **826/826 OK** (incl. the test_purity gates; PROSE_PIN untouched; zero `engine._game`/`engine._payload` grep hits in game_window.py).

## Task Commits

Each task was committed atomically:

1. **Task 1: `_show_endgame_modal` + wrapper scheduling tails** — `71fc298` (feat)
2. **Task 2: SMOKE-16 PART C (natural end + final timer)** — `9845038` (test)
3. **Task 3: full regression battery** — no code changes needed (zero regressions surfaced); results recorded in this SUMMARY and the plan metadata commit

**Plan metadata:** recorded below (docs: complete plan)

## Files Created/Modified

- `aamatch/game_window.py` — `_show_endgame_modal(summary)` (both v1 bug-fix rationales + the WRAPPER-ONLY law in the docstring); the refresh+singleShot tails on `_on_confirm`/`_on_skip`/`_on_giveup` (impls untouched); module ROLE paragraph + handler docstrings updated (the 06-09 endgame-modal paragraph; the two-surface discipline)
- `smoke/smoke_16_tab.py` — PART C appended (14 checks, T1b impl-driven, ZERO modals); docstring grew the PART C descriptions; the phase regression record lines print at the file's end; the verdict line now reports the A/B/C breakdown (total 67)

## Decisions Made

- Recorded in frontmatter: the 100 ms v1 constant kept verbatim; the uniform truthy+`game_over` tail guard (None schedules nothing); the pure-block-only content rule (human wording re-confirmation at 06-10 is a confirm-step, not a blocking gate).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug / plan-internal contradiction] The plan's "`_last_status` None (post-pop poll cleared during the sync refresh)" assert reversed the committed 06-07 order**

- **Found during:** Task 2 (authoring the C9 assert)
- **Issue:** Plan Task-2 step 2 lists "`_last_status` None (post-pop poll cleared during the sync refresh)" as a natural-end assert. The committed 06-07 impl order is: wizard op -> `_refresh_status()` SYNCHRONOUSLY (wizard still live; the game_over transition block logs the endgame block and `_last_status` is set to the final game_over state) -> `_endgame_sequence` (timer stop -> label pin -> pop). The poll-clear branch (`_last_status = None` when no GameWizard is live) can only fire on a *later* refresh — but the timer is stopped at the pop, so no later poll ever runs. PART A's A6 already pins this exact "holds the last value" shape (the required label holding its last text post-pop).
- **Fix:** Asserted the actual committed behavior — `_last_status` is a dict with `game_over` True — with the plan-text mismatch documented in the smoke docstring (PART C C9) and the check name. Zero production-code divergence.
- **Files modified:** smoke/smoke_16_tab.py
- **Verification:** SMOKE-16 C9 PASS; full SMOKE-16 67/67 PASS
- **Committed in:** `9845038` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (plan-internal contradiction resolved toward the committed 06-07 order — the same reconciliation class as 06-08's D7 sketch contradiction)
**Impact on plan:** None — production code matches the plan's action list verbatim; only the smoke assert reconciled the plan text against the already-committed implementation order.

## Issues Encountered

None — SMOKE-16 PART C passed 14/14 on the FIRST run embedded in the full 67/67 verdict; every rerun in the regression battery was green on its first execution; py_compile, the full 826/826 WSL suite, the purity gates, and PROSE_PIN all held throughout.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **06-10 ([HUMAN] endgame checkpoint) input list:**
  1. The endgame MODAL itself (never headless-drivable, smoke-99): appears ~100 ms after the scene settles ON TOP of the OpenGL viewer (Bug-B fix), headline + rich-text stats legible, OK dismisses; both variants (natural-end 'You win!' via the last Confirm and give-up 'Game over' via the dropdown's Give Up...).
  2. The wrapper tails across all three triggers: Confirm button natural end; Skip of the last molecule of the last level; Give Up... (each shows the modal exactly once).
  3. The stopped timer: after the modal dismisses, the label holds the final M:SS and does not advance while the window stays open; the info box carries the full endgame block exactly once.
  4. The Skip/Give-Up warning boxes' look/feel + the timer freeze under them (P-5 class — a new dialog instance of the 05-11-confirmed mechanism).
  5. Post-endgame state: scene retained for inspection (Done semantics), wizard panel gone, Restart works from the endgame state (fresh countdown from 0:00 — SMOKE-16 C10/C11 mechanically pre-proven), Cleanup still available.
  6. Wording re-confirmation (D10 confirm-step): every endgame string is `status_text`-pinned; approval is the only pending item, not a blocking gate.
- Standing gates green at handoff: 826/826 WSL, SMOKE-04/08/11/14/15/16 ALL PASS (25+41+51+29+74+67 checks), py_compile clean, grep law zero-hit, PROSE_PIN untouched.
- Mechanical proof is complete pending only human GUI verification — the 06-10 checkpoint verifies exactly what is not headlessly provable.

---
*Phase: 06-scoring-lifecycle-endgame*
*Completed: 2026-09-20*
