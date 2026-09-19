---
phase: 05-game-status-tab-start-sequence
plan: 10
subsystem: ui
tags: [pymol, pyqt5, polling, status-surface, event-log, headless-smoke]

# Dependency graph
requires:
  - phase: 05-game-status-tab-start-sequence (plan 05-01)
    provides: pure status_text builders + EVENT_KINDS (status_events,
      required_display, level_molecule_line)
  - phase: 05-game-status-tab-start-sequence (plan 05-06)
    provides: GameTab skeleton with 1 Hz tick + modal-pause rebase
  - phase: 05-game-status-tab-start-sequence (plan 05-07)
    provides: GameWizard.get_status()/engine.game_status() public accessors
provides:
  - GameTab._refresh_status(): the 1 Hz poll-diff read path (public
    accessors only, lazy-import isinstance gate)
  - GameTab._begin_play owning the FIRST level line + FIRST required
    label (start-sequence-owned, no poll race) + _last_status baseline
  - SMOKE-14 T1b: standalone-GameTab live drive of the event log, both
    required modes, selection/error dedupe, no-score reserve
affects: [phase-06-scoring-lifecycle, phase-07-persistence-buttons]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "1 Hz poll-diff piggybacked on the elapsed-time tick (no second
      timer, no push callbacks -- wizard must stay picklable)"
    - "pure diff owns all event wording; the Qt tab is a dumb renderer"
    - "start sequence owns the first observation (pitfall 4); the poll
      only reports changes"

key-files:
  created: []
  modified:
    - aamatch/game_window.py
    - smoke/smoke_14_status_surface.py
    - smoke/smoke_11_window.py (deviation: I3 pin tolerance)

key-decisions:
  - "The poll reads ONLY cmd.get_wizard() + instanceof GameWizard +
    get_status() -- never engine._game/_payload/wizard privates, never
    callbacks on the wizard (session-save pickle contract)"
  - "Lazy relative import INSIDE _refresh_status for the isinstance
    gate (module-identity law, pitfall 2)"
  - "_last_status is a plain dict on the dialog (never pickled -- free
    per pitfall 1)"
  - "The required label refreshes on molecule change only; 'Required: -'
    is restored the moment no GameWizard is top of stack"

patterns-established:
  - "Poll-diff event log: tab-owned actions log directly (start
    sequence, hint); the poll appends only fingerprinted CHANGES
    (level/molecule line, Selected: line, ERROR: line with sticky
    dedupe) -- no mirroring, no movement lines, no timestamps, no
    score lines"
  - "Cross-wave smoke-pin evolution: when a must-have behavior change
    breaks another smoke's exact pin in a disjoint region, update the
    pin minimally and document (same drive-contract precedent as the
    PART G rework)"

# Metrics
duration: ~13 min
completed: 2026-09-19
---

# Phase 5 Plan 10: Status Poll-Diff Wiring (Info Box + Required Label) Summary

**The Game tab's info box is now a live event log: the 1 Hz tick polls
the GameWizard's public `get_status()`, a pure diff (`status_text.
status_events`) turns state changes into pinned log lines, and the
start sequence owns the first level line + first required label --
zero Qt/wizard coupling, pickle-safe, module-identity-safe.**

## Performance

- **Duration:** ~13 min
- **Started:** 2026-09-19T07:54:29Z
- **Completed:** 2026-09-19T08:07:46Z
- **Tasks:** 2/2 (+1 deviation fix commit)
- **Files modified:** 3

## Accomplishments

- `_refresh_status()` on `GameTab`: 1 Hz poll-diff reading ONLY
  public accessors (`cmd.get_wizard()` behind a lazy-import
  isinstance gate, then `get_status()`); the pure
  `status_text.status_events` owns every event line (first observation
  silent, one level line per molecule/level change, `Selected: slot
  %s (%s).` on selection change, `ERROR: %s` on a NEW error string
  with sticky dedupe); required label rendered by the pure
  `required_display` on molecule change and reset to `Required: -`
  when no GameWizard is live.
- `_on_tick` carries the poll AFTER the timer-label half; the modal-
  pause branch returns early so the poll is skipped while the clock is
  frozen (no second timer, no push callbacks).
- `_begin_play` owns the FIRST status content (pitfall 4): level line
  + required label from the PENDING wizard's `get_status()` right
  after `GO!` (instant, ordered), and seeds `_last_status` so the
  poll's first observation is silent.
- SMOKE-14 T1b (PARTs 3-4): standalone-`GameTab(None)` headless drive
  proves every diff rule against a LIVE game -- shell labels,
  no-wizard branch, deferred-countdown GO with the pinned level line,
  silent first poll, scripted-pick `Selected:` line + same-slot
  dedupe, `ERROR:` line + sticky dedupe, BOTH required modes
  (`Required: any 1 interaction` exclusive; list-mode prefix unset),
  the no-score reserve, and baseline-exact restore. PART 1 (T1a)
  byte-identical and green.

## Task Commits

1. **Task 1: _refresh_status + _on_tick hook + _begin_play status
   content** - `034b27b` (feat)
2. **Deviation fix: SMOKE-11 PART I3 pin tolerates the GO level
   line** - `2ee6954` (fix)
3. **Task 2: SMOKE-14 T1b status-surface extension** - `26c3cba` (test)

**Plan metadata:** `0f01275` (docs: complete plan)

## Files Created/Modified

- `aamatch/game_window.py` - `_refresh_status()` poll, `_last_status`
  baseline slot, `_on_tick` hook after the label half, `_begin_play`
  first-observation content; docstrings updated (poll landed, no
  banned tokens)
- `smoke/smoke_14_status_surface.py` - T1b header/docstring rewrite +
  QT_QPA_PLATFORM + PART 3 (import gate) + PART 4 (surface drive);
  PART 1 byte-identical
- `smoke/smoke_11_window.py` - PART I3 exact-lines pin evolved to
  tolerate the appended GO level line (deviation, Rule 3)

## Decisions Made

- The poll never reaches privates: `cmd.get_wizard()` + lazy relative
  `from . import status_text, wizard` inside `_refresh_status`
  (module-identity law; a module-level import would silently fail the
  isinstance gate under the installed identity), then the plain-data
  `get_status()`. No callbacks are ever registered on the wizard (the
  whole stack is pickled on session save).
- `_last_status` lives as a plain dict on the tab: the DIALOG is never
  pickled, so the baseline store is free (pitfall 1).
- The required label is reference info, never a log line: refreshed on
  molecule change (or on every read when the baseline is fresh),
  reset to `Required: -` the moment no GameWizard tops the stack.
- The no-selection movement drive in the smoke uses the real public
  handler `nudge_cam(1, 0, 0)` (the plan sketched a nonexistent
  `move_left()`; every movement handler funnels through
  `_current_object()`, which sets the pinned `Select an amino acid
  first.` error).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] SMOKE-11 PART I3 exact-lines pin broken by the
deliberate GO level line**

- **Found during:** Task 1 verification (`smoke_11_window.py`
  regression, required by the plan)
- **Issue:** The plan's own must-have (\_begin_play logs the first
  level line right after `GO!`) appends a 6th line to the countdown
  log, breaking PART I3's 05-06-era exact-equality pin
  (`lines_i == ['Get ready...', '3', '2', '1', 'GO!']`). SMOKE-11 is
  owned by the parallel wave-4 plan 05-09, whose plan reworks PART G
  only and never touches I3 -- the merged tree would stay red with no
  owner for the fix.
- **Fix:** Minimal evolution in the disjoint PART I region (lines
  ~915-925, far from PART G's 569-680 -- the wave merge is
  conflict-free): the five start lines stay exact-pinned, and a new
  check pins the 6th line's shape (`Level 1, molecule 1 of N.`
  prefix/suffix; the exact format is WSL-pinned in status_text and
  headlessly pinned in SMOKE-14 T1b). Same documented drive-contract
  precedent as 05-09's PART G rework.
- **Files modified:** `smoke/smoke_11_window.py`
- **Verification:** `=== SMOKE-11 PASS ===` (all parts, incl. I3's new
  level-line shape check)
- **Committed in:** `2ee6954`

**2. [Rule 3 - Blocking] Plan's scripted error drive named a
nonexistent `wiz.move_left()`**

- **Found during:** Task 2 (SMOKE-14 T1b step 6b)
- **Issue:** GameWizard has no `move_left`; the public movement
  handlers are `nudge_cam`/`rotate_axis`/`move_to`/`step_to_ligand`,
  all funnelling through `_current_object()` which sets the pinned
  `_error = 'Select an amino acid first.'` when nothing is selected.
- **Fix:** The smoke drives `wiz2.nudge_cam(1, 0, 0)` -- the same
  mechanism the plan described (public handler, no selection -> guard
  sets `_error`), so the `ERROR:` + sticky-dedupe assertions are
  unchanged.
- **Files modified:** `smoke/smoke_14_status_surface.py`
- **Verification:** `part 4.7: no-selection nudge -> exactly ONE
  'ERROR:' line` + `sticky dedupe` both PASS
- **Committed in:** `26c3cba`

**3. [Rule 3 - Blocking] smoke_14 did not set QT_QPA_PLATFORM despite
the plan saying "the smoke already sets it"**

- **Found during:** Task 2
- **Issue:** smoke_14 (05-07, T1a) had no offscreen env var; the T1b
  parts construct Qt widgets, so the 04-01 offscreen recipe must be
  set before any pymol.Qt import.
- **Fix:** Added `os.environ['QT_QPA_PLATFORM'] = 'offscreen'` right
  after the stdlib imports (SMOKE-11 PART A contract); PART 1 body
  untouched.
- **Files modified:** `smoke/smoke_14_status_surface.py`
- **Verification:** PART 3/4 all PASS under offscreen Qt
- **Committed in:** `26c3cba`

---

**Total deviations:** 3 auto-fixed (all Rule 3 -- blocking)
**Impact on plan:** Every deviation was mechanical/conflict-resolution
only; zero behavioral design drift. The one cross-file touch (smoke_11)
is in a region disjoint from the parallel 05-09 agent's PART G rework
-- note for the merge: if a conflict nonetheless appears, keep BOTH
05-09's PART G rework AND this I3 tolerance.

## Issues Encountered

None beyond the tracked deviations. The WSL suite (753 tests incl.
purity gates), the 3.6 syntax floor, the grep gate (zero
`engine._game`/`_payload` hits in `game_window.py`), SMOKE-11, and
SMOKE-14 are all green.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for 05-11 (wave-5 human checkpoint): the SCORE-04 verification
  step expects the info-box narrative (start lines, level line at GO,
  `Selected:`/`ERROR:` lines, timer outside the box, both-mode
  required label) -- all proven headlessly here.
- Merge note for the orchestrator: my branch also touches
  `smoke/smoke_11_window.py` (PART I3 region only); re-run SMOKE-11
  once after merging 05-09 + 05-10 to confirm both evolve cleanly.
- Phase 6 inherits the read path (`engine.game_status()`) and the
  `EVENT_KINDS` reserve for score/skip/give-up lines.
