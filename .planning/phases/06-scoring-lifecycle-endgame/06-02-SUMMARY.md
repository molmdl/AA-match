---
phase: 06-scoring-lifecycle-endgame
plan: 02
subsystem: scoring
tags: [status_text, poll-diff, last_event, endgame, wording-home, pure, tdd]

# Dependency graph
requires:
  - phase: 05-game-status-tab-start-sequence
    provides: status_text pure battery (required_display/status_events/EVENT_KINDS),
      the poll-diff conventions (pitfalls 3/4/5/7), wizard_text.result_lines single home
  - phase: 06-scoring-lifecycle-endgame (06-01, same wave)
    provides: the endgame_summary plain-dict contract (keys pinned identically in both plans)
provides:
  - "Marker payload shapes the wizard emits (06-05 pins producers): molecule_scored ->"
    " {score, total, molecule_pos, molecule_total, formed, required, extras}; molecule_skipped"
    " -> {score, total, molecule_pos, molecule_total}; gave_up -> {total, molecule_pos,"
    " molecule_total, level_pos}; level_advanced -> {level_pos}; game_reset -> {} (all + kind/seq)"
  - "5 poll-emitted builders + game_restarted_line (handler-logged, NOT poll-emitted)"
    " with FINAL D10 wording; poll-diff renders last_event markers event-lines-first"
  - "SKIP_WARNING_TITLE/TEXT + GIVEUP_WARNING_TITLE/TEXT constants (06-07 wrappers show only these)"
  - "endgame_lines(summary) -> the identical info-box/modal SCORE-07 block (headline always lines[0])"
  - "format_mss(seconds) -> pure M:SS (reused by the timer label render at 06-07)"
affects: [06-05 (wizard marker producers), 06-07 (tab wiring + warning boxes + endgame block),
          06-09 (endgame modal), 06-08 (restart handler-logged line), 07 (game_saved/imported reserve)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Event marker channel: wizard sets _last_event = {kind, seq, ...payload}; the 1 Hz"
      " poll-diff fingerprints it whole-dict; builders render to lines (the 05-01 wording-home law)"
    - "Debrief-by-import: molecule_scored_lines returns header + wizard_text.result_lines(...)"
      " verbatim — one wording home, zero drift"

key-files:
  created: []
  modified:
    - aamatch/status_text.py
    - tests/test_status_text.py

key-decisions:
  - "Gave-up endgame headline denominator = molecules // levels (uniform per-level count;"
    " 06-RESEARCH.md Q5: every level has exactly m molecules)"
  - "game_restarted EXCLUDED from _EVENT_BUILDERS — tab-handler-logged after the countdown arms"
  - "EVENT_KINDS stays BYTE-UNCHANGED; the builders (not the dict notes) carry the final wording"

patterns-established:
  - "Event builder contract: validate own kind (ValueError naming mismatch) + fail-closed"
    " missing/None payload keys (ValueError naming the key), %-formatting, plain-data-in/out"
  - "Poll-diff ordering law: event lines, then level/molecule, then selection, then error"

# Metrics
duration: 6 min
completed: 2026-09-19
---

# Phase 6 Plan 2: status_text Phase-6 Event/Warning/Endgame Text Surface Summary

**status_text now pins every Phase-6 string headlessly in WSL: the six reserved-kind event builders (scored debrief IS wizard_text.result_lines verbatim), the last_event poll-diff fingerprint with event-lines-first ordering, the skip/give-up warning constants, the endgame_lines block, and the pure M:SS formatter — later wiring plans (06-05/06-07/06-09) can only show already-pinned strings.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-09-19T18:49:44Z
- **Completed:** 2026-09-19T18:55:58Z
- **Tasks:** 1 TDD feature (RED + GREEN commits)
- **Files modified:** 2

## Accomplishments

- Six reserved-kind wording pinned byte-for-byte in pure builders (`molecule_scored_lines`, `molecule_skipped_line`, `gave_up_line`, `level_advanced_line`, `game_reset_line`, `game_restarted_line`), each kind-validating and payload fail-closed
- `status_events` fingerprints ONE new key `last_event` (whole-dict equality; seq makes identical consecutive events distinct) and prepends dispatched event lines BEFORE the position line; unknown kinds and `game_restarted` markers fail closed; `'result'` stays unfingerprinted (pitfall-7 pin untouched)
- `endgame_lines(summary)` renders the SCORE-07 block (headline, per-level `Level %d: %.2f`, total, M:SS time, sizes, counters) from the 06-01 summary contract — identical for the info box and the modal
- Warning constants (`SKIP_WARNING_*`, `GIVEUP_WARNING_*`, endgame-ui §3.3 NO-number variant) + pure `format_mss` (75→'1:15', 3661→'61:01', negative refuses naming the cause)

## Task Commits

TDD cycle (2 atomic commits):

1. **RED: Phase-6 test battery** - `f0824bb` (test)
2. **GREEN: implement Phase-6 builders + poll-diff extension** - `2c07e46` (feat)

**Plan metadata:** recorded below (docs: complete plan)

## Files Created/Modified

- `aamatch/status_text.py` — grew from 180 to ~380 lines; additive only (existing `required_display`/`level_molecule_line`/`selected_line`/`error_line`/`EVENT_KINDS` untouched; `status_events` extended additively); import line grew to `from .wizard_text import required_summary, result_lines` (grep receipt: the ONLY import line)
- `tests/test_status_text.py` — +410 lines: 8 new TestCase classes (format_mss, warning constants, per-builder suites incl. kind-mismatch + missing-key refusals, last_event poll-diff suite incl. the plan's scenario pin and seq-distinctness, endgame_lines blocks + refusals); ALL Phase-5 pins byte-unchanged

## Decisions Made

- **Gave-up headline denominator** = `molecules // levels` (uniform per-level molecule count, 06-RESEARCH.md Q5: every level has exactly m molecules) — see Deviations for the plan-defect context; guarded fail-closed for `levels < 1`
- **`game_restarted` excluded from `_EVENT_BUILDERS`** (the 5-kind poll table) — the tab handler logs it AFTER the countdown arms (the countdown clears the box; the marker would die with the popped wizard); a poll marker with that kind raises ValueError naming it
- **`EVENT_KINDS` byte-unchanged** — the 15-key set and 'reserved for Phase 6' note pins pass untouched; the builders carry the real wording
- **`level_advanced_line` pinned but ops do NOT emit it** (endgame-ui D8) — the poll's position-change line already announces the new level; kind stays vocabulary-complete

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Gave-up endgame headline: plan's `%`-tuple had 3 placeholders, 2 arguments**

- **Found during:** GREEN (endgame_lines implementation)
- **Issue:** Plan line 69 specifies the gave-up headline
  `'Game over -- gave up at level %d, molecule %d of %d.' % (ended_level, ended_molecule).`
  — the format string has three `%d` placeholders but the shown tuple carries only two arguments, which would raise TypeError at every gave-up render
- **Fix:** Third argument resolves to the per-level molecule count `molecules // levels` (the summary's `molecules` is the SUM across all levels per the 06-01 key contract; counts are uniform by construction — 06-RESEARCH.md Q5). Matches the sibling pin in 06-07-PLAN line 120 (`'gave up at level 2, molecule 1 of 2.'` on a 2-per-level game: 6 // 3 = 2). A `levels < 1` guard raises ValueError naming the cause instead of dividing by zero
- **Files modified:** aamatch/status_text.py, tests/test_status_text.py (pin `test_gave_up_block` documents the derivation)
- **Verification:** gave-up pin green (`molecule 1 of 2` from molecules=6/levels=3); completed headline unaffected
- **Committed in:** 2c07e46 (GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** The fix was required for the pinned wording to be renderable at all; the derived denominator is the only reading consistent with the 06-01 key contract and the 06-07 sibling pin. No scope creep.

## Issues Encountered

None — RED failed exactly as specified (38 failures: AttributeError on the not-yet-implemented builders + ValueError-not-raised on refusals), GREEN passed on the first implementation; all 794 WSL tests green including the untouched Phase-5 pins and test_purity gates.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `format_mss`, the 5 poll builders, and the warning constants are ready for 06-07's tab wiring and confirmation boxes; `endgame_lines` is the shared info-box/modal block for 06-09
- Marker payload shapes for 06-05's wizard producers are pinned in tests (scored: `{score, total, molecule_pos, molecule_total, formed, required, extras}`; skipped: `{score, total, molecule_pos, molecule_total}`; gave_up: `{total, molecule_pos, molecule_total, level_pos}`; level_advanced: `{level_pos}`; game_reset: `{}`)
- Wording is a proposal (D10 adopted from research) — human re-confirms at the 06-10 checkpoint, NOT a blocking decision gate

---
*Phase: 06-scoring-lifecycle-endgame*
*Completed: 2026-09-19*
