---
phase: quick-004
plan: 004
subsystem: game lifecycle / Qt status tab / checkpoint persistence
tags: [pymol, qt, wizard, lifecycle, abandon, checkpoint, books, smoke, purity]

# Dependency graph
requires:
  - phase: 08.3-drag-movement-pivot
    provides: drag core + get_wizard_stack receipts; D1 routed out-of-phase by 08.3-VERIFICATION
  - phase: 07-checkpoint-persistence
    provides: snapshot_books/resume_from + load_checkpoint rebuild branch (the (b) seam)
  - phase: 08.1-confirm-pass-gate-restoration
    provides: the endgame modal parity tail (_show_endgame_modal offscreen gate + once latch)
provides:
  - "engine op 18 abandon_game: end_state 'abandoned' + stop_timer freeze, NO summary (Done != Give-Up)"
  - "GameTab poll abandon-stop: Done mid-game stops the 1 Hz clock within one tick, freezes the label, logs ONE 'Game abandoned.'"
  - "pure status_text.game_abandoned_line() in the handler-logged shape (zero EVENT_KINDS drift)"
  - "checkpoint books carry _saved_button_mode + rebuild-path button_mode repair (deferred (b) closed)"
  - "SMOKE-16 PART G (Done-path lifecycle battery), SMOKE-07/SMOKE-20 dated additive rows"
affects: [Phase 9 help wording, any future Done/abandon GUI work]

tech-stack:
  added: []
  patterns:
    - "Poll-side lifecycle observation with a wizard-stack membership guard (no wizard.py changes)"
    - "No-record end state ('abandoned') fail-closed by existing endgame_summary refusal"
    - "Additive-only persistence carry (.get -> None) mirroring saved_msm"

key-files:
  created: []
  modified:
    - aamatch/engine.py
    - aamatch/game_state.py
    - aamatch/status_text.py
    - aamatch/game_window.py
    - aamatch/wizard.py
    - aamatch/gamestart.py
    - tests/test_status_text.py
    - tests/test_game_state.py
    - smoke/smoke_16_tab.py
    - smoke/smoke_07_wizard_loop.py
    - smoke/smoke_20_checkpoint_e2e.py

key-decisions:
  - "DATED [HUMAN]-lite applied default (2026-11-16): panel Done mid-game = abandon-stop (no record), amendable at the next GUI touch"
  - "Done-that-raced-the-poll converges on the legitimate endgame tail, never re-branded abandoned"
  - "Deferred (b) closed additive-only (books .get -> None legacy default)"
  - "Still deferred (a): PyMOL-internal '_drag' residual"

# Metrics
duration: unrecorded (single continuous session, 2026-11-16)
completed: 2026-11-16
---

# Quick Task 004: Fix D1 — Done-path lifecycle defect (+ deferred (b) fold) Summary

**Panel Done mid-game now stops the Qt clock within one tick and honestly abandons the game ('abandoned', no record, one 'Game abandoned.'), while Give-Up/panel-Confirm ends stay byte-unchanged; checkpoint books now carry `_saved_button_mode` and a rebuilt wizard restores the true pre-arm button profile.**

## Performance

- **Duration:** unrecorded (single continuous session, 2026-11-16)
- **Completed:** 2026-11-16
- **Tasks:** 3/3
- **Files modified:** 11 (all within the plan's `files_modified`)

## Accomplishments

- **D1 CLOSED at the UI level**: `_abandon_check` at the head of `_refresh_status`'s no-live-GameWizard branch stops the 1 Hz timer FIRST, freezes the label at the abandon instant, marks the engine `game_over`/`'abandoned'` via the new engine op 18 `abandon_game`, and logs exactly one `'Game abandoned.'` — no endgame block, no modal, no summary record.
- The Done-raced-the-poll case (panel Confirm completes; Done pops before the tick observed it) converges on the 08.1-08 endgame tail: win headline once, exact final M:SS, once-latched modal arm — never re-branded as an abandon.
- A user wizard stacked over the live GameWizard (`cmd.drag` stock recipe) never triggers a false abandon (the `cmd.get_wizard_stack()` membership guard); after it pops, the GameWizard auto-resumes and the tab keeps working.
- **Deferred (b) CLOSED**: `snapshot_books` carries `saved_button_mode` (7-key roster), `resume_from` reads it with the `saved_msm` `.get`->None legacy default, and the `load_checkpoint` rebuild branch repairs `button_mode` before `activate()` (probe-D2 `cmd.set(..., quiet=1)` + `cmd.mouse()`), so a rebuilt wizard's eventual cleanup restores the user's pre-arm profile. Old 6-key checkpoints load exactly as before.
- Give-Up, panel-Confirm endgame, `game_over` transition block, `_endgame_sequence`, `_show_endgame_modal`, EVENT_KINDS, and `endgame_summary` remain byte-identical (git diff: engine/game_window/status_text pure additions; the only production edits elsewhere are docstrings + the additive (b) rows).

## Task Commits

Each task was committed atomically:

1. **Task 1: Engine op 18 + pure game_abandoned_line + WSL pins** — `782c272` (feat)
2. **Task 2: GameTab poll Done-pop detection + SMOKE-16 PART G** — `acf9e9a` (feat)
3. **Task 3a: Fold deferred (b) production** — `a60a33c` (feat)
4. **Task 3b: dated SMOKE-07 / SMOKE-20 rows** — `a30fdea` (test)
5. **Plan metadata (SUMMARY + STATE)** — docs commit (below)

## DATED [HUMAN]-lite Applied Default (2026-11-16) — amendable at the next GUI touch

**Decision:** a mid-game panel **Done** = **abandon-stop**, not an end. On detecting the Done pop, the Game tab stops the clock, freezes the elapsed display, marks the engine `game_over` with `end_state='abandoned'`, and logs one `'Game abandoned.'` line. NO endgame modal, NO summary record, no giveup counter — **Done != Give-Up** (Give-Up stays the scored, confirmation-guarded exit; Done = closing the board).

**Rejected alternatives:**
- *Endgame-on-Done* (treat Done like Give-Up/completion): would erase the Done != Give-Up distinction — closing the board would fabricate a scored record the player never asked for.
- *Tab-only stop* (stop the clock but leave the engine live): would leave `game_status()` lying about a live game; every engine/gameplay op would keep operating on an abandoned board.

This default was applied in yolo mode under the human imperative "fix D1" (the 08.3-01 convention); the applied-default note is recorded in the touched production docstrings (`engine.abandon_game`, `status_text.game_abandoned_line`, `game_window` module docstring) with the same 2026-11-16 date. **The human can amend at the next GUI touch** (wording and/or semantics).

## Phase-9 Carry-Forward

- **Help wording:** panel **Done = closing the board** — no summary/record by design (it is not Give-Up).
- A `'Game abandoned.'` re-word candidate is open for the Phase-9 discuss plan (e.g. "Board closed." family), gated by the same dated applied-default amendment.
- Still resident help lesson from O1 (unchanged): salt bridges and H-bonds score independently (`116d13d`).

## Still Deferred

- **(a) `_drag` residual — UN-MET.** The PyMOL-internal `'_drag'` mirror object (19 atoms) survives the Done path; SMOKE-24 row 4b continues to receipt the aamatch-owned empty set + the residual. No code touched here (out of this plan's scope).

## Exact Count Arithmetic

- **WSL:** 969 baseline + 3 `TestGameAbandonedLine` + 1 `test_abandoned_end_state_refused_by_summary` = **973/973 OK** (0 failures).
- Gate trio individually receipted: `test_purity` 10/10, `test_wizard_source` 27/27, `test_code_audit` 10/10; `test_engine_public_api` 4/4; `TestConfirmPassGatePresent` 2/2.
- **SMOKE-16:** 113 baseline (A36/B23/C14/D10/E18/F12) + **PART G 24 = 137 checks, 0 failures**.
- **SMOKE-07:** 83 baseline + 2 dated rows = **85 PASS / 0 FAIL**.
- **SMOKE-18:** **32 PASS / 0 FAIL**, script byte-untouched (its B row auto-adapts to the 7-key books).
- **SMOKE-20:** two-run recipe — RUN 1 SAVE **13 PASS / 0 FAIL**, RUN 2 VERIFY **35 PASS / 0 FAIL** (baseline + 2 dated rows).

## Receipts (grep-verified marker lines)

- `SMOKE-16 PART A: 36 checks; PART B: 23 checks; PART C: 14 checks; PART D: 10 checks; PART E: 18 checks; PART F: 12 checks; PART G: 24 checks; total 137, 0 failure(s)`
- `=== SMOKE-16 PASS ===`
- `=== SMOKE-07 PASS ===` (85 PASS lines, 0 FAIL)
- `=== SMOKE-18 PASS ===` (32 PASS lines, 0 FAIL)
- `=== SMOKE-20 PASS ===` (RUN 1 SAVE, 13 PASS) and `=== SMOKE-20 PASS ===` (RUN 2 VERIFY, 35 PASS)
  - `C forced-rebuild: _saved_button_mode == sidecar saved_button_mode (the quick-004 repair landed) PASS got=0 want=0`
  - `C pop->cleanup restores the repaired button_mode profile PASS post-pop button_mode=0 want 0`
- `python3.6 -m py_compile aamatch/*.py` -> PYC-OK
- `python3.6 -m unittest discover -s tests` -> `Ran 973 tests ... OK`

## SMOKE-20 Invocation Ledger

1. Pre-check: `tmp/smoke fixtures/aam_pse20/` ABSENT -> no stale-fixture contingency.
2. Invocation 1 — `bash smoke/run_smoke.sh smoke/smoke_20_checkpoint_e2e.py 240` -> `SMOKE-ENV phase: save`; `=== SMOKE-20 PASS ===` (13 checks).
3. Invocation 2 — same command (fresh process) -> `SMOKE-ENV phase: verify`; `=== SMOKE-20 PASS ===` (35 checks), including both new (b) rows.
No stale-fixture re-run was needed.

## Files Created/Modified

- `aamatch/engine.py` — op 18 `abandon_game` + OPS docstring row (pure additions; give_up/complete_game/endgame_summary untouched).
- `aamatch/game_state.py` — docstring-only: `end_state` domain names `'abandoned'` with the fail-closed no-summary note (zero executable change).
- `aamatch/status_text.py` — `game_abandoned_line()` (handler-logged shape; EVENT_KINDS / `_EVENT_BUILDERS` untouched).
- `aamatch/game_window.py` — `_abandon_check` + the branch-head call + dated module-docstring paragraph.
- `aamatch/wizard.py` — books carry `saved_button_mode`; `resume_from` `.get`/int/None read; docstrings.
- `aamatch/gamestart.py` — rebuild-path `button_mode` repair + step-7 docstring sentence.
- `tests/test_status_text.py` — `TestGameAbandonedLine` (3 tests).
- `tests/test_game_state.py` — abandoned-summary refusal pin (1 test).
- `smoke/smoke_16_tab.py` — PART G (G1-G6) + docstring note + count-line field (A-F rows byte-untouched).
- `smoke/smoke_07_wizard_loop.py` — 7-key roster + saved_button_mode round-trip rows (additive).
- `smoke/smoke_20_checkpoint_e2e.py` — repair-landed + one-pop restore rows (additive).

## Decisions Made

- D1's Done semantics landed as the dated applied default above (abandon-stop).
- Fix seam chosen: pure tab-side poll observation (`_abandon_check`) — zero `wizard.py` activate/cleanup changes, zero 08.3-13 AST-pin wakes.
- The missed-transition convergence reuses the 08.1-08 endgame parity tail verbatim-in-shape (one moment per end).
- (b) fold kept additive-only; the ADOPT path needs nothing (the pickled wizard already carries `_saved_button_mode`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] SMOKE-16 PART G needed a `pymol.wizard` namespace repair before the stock `cmd.drag`**
- **Found during:** Task 2 (SMOKE-16 PART G, G6 buried-wizard negative control).
- **Issue:** PyMOL `-cq` scripts exec with `globals() == pymol.__dict__` (probe-verified this session). PART A's module-level `from aamatch import wizard` therefore SHADOWS `pymol.wizard`; `cmd.drag` resolves `pymol.wizard.dragging` internally and raised `AttributeError: module 'aamatch.wizard' has no attribute 'dragging'`. (Pre-existing smoke-namespace quirk; harmless until this plan's first `cmd.drag` call in SMOKE-16.)
- **Fix:** In G6, immediately before `cmd.drag(obj9)`, restore the real package (`import pymol.wizard.dragging`; `pymol.wizard = sys.modules['pymol.wizard']`) with a dated inline comment. Production code untouched; no later `wizard.` global use in the smoke.
- **Files modified:** `smoke/smoke_16_tab.py`.
- **Verification:** SMOKE-16 PASS with all G6 rows green (`top=Dragging stack=['GameWizard', 'Dragging']`, no false abandon, auto-resume + reseeded label).
- **Committed in:** `acf9e9a` (Task 2 commit).

### Ordering note (not a behavior deviation)

- The Task-3 smoke rows were authored before the two Task-3 commits, so the SMOKE-07/18/16/20 receipt runs cover BOTH the production fold and the new test rows. The commits were still split atomically into `feat` (production) and `test` (smoke rows): `a60a33c` then `a30fdea`. No file content changed between the receipt runs and HEAD.

### Count notes

- `test_wizard_source` reports **27/27** (the plan's verification prose said "29/29"; the actual suite count is 27 — a plan-numbering slip, not a regression; all pins green).
- SMOKE-18 prints no total line; 32 PASS/0 FAIL counted from its check lines.

## Silent-Pin-Edit Accounting

**ZERO silent pin edits.** All smoke/test changes are additive (new rows/methods). The only in-place edit to a standing smoke artifact is SMOKE-16's verdict count-summary line, which the plan explicitly authorizes (additive PART G field; `=== SMOKE-16 PASS ===` marker byte-identical). SMOKE-16 rows A-F, SMOKE-07 existing rows, and SMOKE-20 existing rows are byte-untouched (git diff: additions only). Smokes 01-15, 17-19, 21-24 are untouched entirely.

## Issues Encountered

- The `pymol.wizard` shadowing described above (resolved in-smoke; no production impact).
- No other blockers; authentication gates: none.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 9 (help wording) inherits a correct lifecycle: Done = closing the board (no summary by design); the 'Game abandoned.' re-word candidate is open; (a) `_drag` residual remains documented/deferred.
- Tree clean at completion; quick tasks do not modify ROADMAP.md.

---
*Task: quick-004*
*Completed: 2026-11-16*
