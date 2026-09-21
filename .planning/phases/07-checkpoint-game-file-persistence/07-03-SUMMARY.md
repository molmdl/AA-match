---
phase: 07-checkpoint-game-file-persistence
plan: 03
subsystem: ui
tags: [status-text, pure-layer, handoff-lines, game-save, game-import, checkpoint-resume]

requires:
  - phase: 05-game-status-tab-start-sequence
    provides: status_text pure surface + EVENT_KINDS vocabulary + 290-291 sketch pins
  - phase: 06-scoring-lifecycle-endgame
    provides: game_restarted_line handler-logged precedent + reserved-notes-byte-unchanged law
provides:
  - "game_saved_line(path) -> 'Game saved to %s.' (SCORE-08)"
  - "game_imported_line(path) -> 'Game imported: %s.' (PERSIST-02, post-countdown-arm)"
  - "game_resumed_line(path) -> 'Game resumed from %s.' (PERSIST-03, resume re-arm)"
affects: [07-04 Game-tab Save/Import wrappers, 07-0x checkpoint-resume flow, 07-VERIFICATION]

tech-stack:
  added: []
  patterns:
    - "Handler-logged status lines: tab-side operations bypass the poll-diff — no event argument, EXCLUDED from _EVENT_BUILDERS (game_restarted_line shape)"

key-files:
  created: []
  modified:
    - aamatch/status_text.py
    - tests/test_status_text.py

key-decisions:
  - "Three Phase-7 lines are handler-logged direct _log lines, never poll-emitted — the EVENT_KINDS set stays EXACTLY 15; there is no reserved resume kind (the handler-logged pattern needs none)"
  - "game_saved/game_imported reserved-note texts stay BYTE-UNCHANGED even after the builders land (Phase-6 precedent: builders carry the final wording, not the dict)"

patterns-established:
  - "Phase-7 tab-side line builders: pinned wording builders + signature/exclusion test pins (single 'path' param, not-in-table by kind AND by function)"

duration: 3 min
completed: 2026-09-21
---

# Phase 7 Plan 3: Phase-7 handler-logged status-line builders Summary

**Three pure status-text builders — `game_saved_line`/`game_imported_line`/`game_resumed_line` — land in the game_restarted_line handler-logged shape (no event argument, excluded from the poll table), with exact-wording and exclusion test pins; EVENT_KINDS stays exactly 15 and the reserved notes byte-unchanged.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-09-21T03:16:53Z
- **Completed:** 2026-09-21T03:19:46Z
- **Tasks:** 2 (executed as TDD: Task 2's pins RED first, then Task 1's builders GREEN)
- **Files modified:** 2

## Accomplishments

- `game_saved_line(path)` pinned to `'Game saved to %s.'` (05-RESEARCH-status-surface.md:290; SCORE-08) — logged by the Game tab's Save wrapper AFTER a successful checkpoint write.
- `game_imported_line(path)` pinned to `'Game imported: %s.'` (:291; PERSIST-02) — logged AFTER `start_countdown` arms so the countdown's `_info_log.clear()` cannot wipe it (restart D2/D7 law verbatim).
- `game_resumed_line(path)` pinned to `'Game resumed from %s.'` (PERSIST-03) — serves the checkpoint-resume tab re-arm (07-RESEARCH-state.md §4 step 9); no countdown on resume.
- All three follow the handler-logged law: single `path` parameter (never an event payload), excluded from `_EVENT_BUILDERS` by kind name AND by builder function; `EVENT_KINDS` stays exactly 15, `game_saved`/`game_imported` reserved notes byte-unchanged (Phase-6 precedent), `status_events` untouched, `'result'` stays unfingerprinted.

## Task Commits

Executed RED-first per the wave TDD discipline (pins prove AttributeError before builders land):

1. **Task 2's pins (RED): failing pins for the three builders** - `5b5feca` (test)
2. **Task 1's builders (GREEN): implement the three handler-logged builders** - `548b82b` (feat)

_Note: RED run proved 6 AttributeErrors on `status_text.game_saved_line` etc.; GREEN run: 86/86 status_text tests, 834/834 full WSL suite (up from 826 — 8 new pins) including the purity gates._

## Files Created/Modified

- `aamatch/status_text.py` — +39/−3: three builders immediately after `game_restarted_line()` (plan-verbatim code incl. docstrings); module docstring gains the Phase-7 running-history bullet (06-02 precedent). `EVENT_KINDS`, `_EVENT_BUILDERS`, `status_events`, and the reserved notes at :90-91 untouched.
- `tests/test_status_text.py` — +103: `TestGameSavedLine`, `TestGameImportedLine`, `TestGameResumedLine` (exact wording incl. trailing period / Windows backslash path) and `TestPhase7BuildersHandlerLogged` (kinds not in table, functions not in table, signature = exactly one `path` param, vocabulary pins unchanged).

## Decisions Made

- Handler-logged, not poll-emitted: Save/Import/Resume are tab-side operations — the wizard is not the actor (for Import it does not exist yet), and the poll's fingerprint set has no key for them. Hence no new `EVENT_KINDS` entry for resume; the reserved-set stays exactly 15.
- Reserved-note texts stay byte-unchanged now that the builders exist (the Phase-6 precedent): the builders, not the dict, carry the final wording.

## Deviations from Plan

None — plan executed exactly as written (Task order re-arranged into the wave-prescribed TDD sequence: Task 2's pins committed RED before Task 1's GREEN; both tasks' content verbatim).

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- The Game tab's Save/Import wrappers (07-04) can log both pinned lines from pure builders; Import's line MUST be logged after the countdown arms.
- The checkpoint-resume flow (07-RESEARCH-state.md §4 step 9) can log `game_resumed_line` after the tab re-arms.
- No blockers or concerns.

---
*Phase: 07-checkpoint-game-file-persistence*
*Completed: 2026-09-21*
