---
phase: 07-checkpoint-game-file-persistence
plan: 10
subsystem: persistence ui
tags: [aamz, checkpoint, import, dispatch, peek_kind, zip, qt-game-tab, smoke]

# Dependency graph
requires:
  - phase: 07-checkpoint-game-file-persistence (plans 07-02, 07-06, 07-07, 07-09)
    provides: pure checkpoint zip I/O + write_checkpoint_zip (07-02); the tab Save impl (07-06); refusal-first _import_game_from + gate-free Import wrapper (07-07); gamestart.load_checkpoint 9-step orchestration + summary dict + _canonical_registry (07-09)
provides:
  - ONE Import button loading BOTH file kinds via header-exact kind dispatch (no extension guessing)
  - persistence.peek_kind (pure, ZIP-AWARE: .aamz sidecar member OR JSON container)
  - game_window._resume_checkpoint_from (P-2 cancel -> load_checkpoint -> full tab re-arm; NO countdown on resume)
  - import dialog filter listing both extensions
  - molecule-aware engine.place_aa (Rule-1 fix for the per-molecule slot_id shadowing)
affects: [07-11 full battery + verification, 07-12 human checkpoint (both load paths now reachable through the ONE Import button)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - one-button kind dispatch: peek_kind BEFORE branch under a SINGLE _guard (no ambiguous None sentinel)
    - tab re-arm pattern: _last_status silent-poll seed + required label + timer-from-rebased-anchor + handler-logged line AFTER the re-arm (no countdown)
    - smoke dispatch teeth: patched-STATIC QFileDialog.getOpenFileName + QMessageBox.warning recorder, originals restored in finally

key-files:
  created: []
  modified:
    - aamatch/persistence.py (peek_kind, zip-aware; zipfile import added to the pure import block)
    - tests/test_persistence.py (TestPeekKind: 9 tests incl. the real-zip battery)
    - aamatch/game_window.py (filter both extensions; _import_by_kind dispatch; _resume_checkpoint_from + tab re-arm)
    - aamatch/engine.py (place_aa/_slot_object molecule_index-scoped resolution)
    - aamatch/wizard.py (move_to passes molecule_index; docstring record)
    - smoke/smoke_16_tab.py (PART E, 18 checks, total 95)

key-decisions (plan records, landed):
  - "ONE Import button dispatches on container kind ('game' -> fresh import, 'checkpoint' -> resume) -- header-exact, never extension guesswork (v1 one-button model)"
  - "NO countdown on resume -- the tab re-arms instantly (labels + resumed line + timer iff not game_over)"
  - "Filter lists both extensions: 'AA-match (*.aamatch.json *.aamz);;All Files (*)'"

patterns-established:
  - "peek-then-dispatch under ONE _guard: a two-_guard shape gives peek's None return an ambiguous refusal sentinel; the single _import_by_kind raise site boxes peek refusals and unknown kinds alike"
  - "resume re-arm = _begin_play minus activation: seed _last_status, render required from the STATE's 'required', label from _compute_elapsed() (rebased anchor reads the true resumed elapsed), timer start iff not game_over"

# Metrics
duration: 20 min
completed: 2026-09-22
---

# Phase 7 Plan 10: One-Button Import Kind-Dispatch + Checkpoint Tab Re-Arm Summary

**The Game-tab Import button is now the ONE load surface for both AA-match file kinds: an exported game file (.aamatch.json) starts fresh; a saved checkpoint (.aamz) resumes with scores, position, books, and the timer ticking from the saved elapsed -- the dispatch reads the container kind header-exact through a new pure, ZIP-aware persistence.peek_kind.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-09-22T03:15:18Z
- **Completed:** 2026-09-22T03:35:23Z
- **Tasks:** 3/3 (plus 1 Rule-1 production fix as its own commit)
- **Files modified:** 6

## Accomplishments

- `persistence.peek_kind` (pure; PURE_MODULES unchanged at 19, zipfile already whitelisted): reads ONLY the container kind -- .aamz archives peek through their single `*.json` sidecar member (single-json-member, unreadable-zip, and unparseable-sidecar refusals share the 07-02/read_json_file wordings verbatim); .aamatch.json keeps the read_json_file branch. No version gate on a peek (the kind's own consumer gates it). No extension guessing anywhere.
- The Import button dispatches on kind under ONE `_guard`: `_on_import` (filter now both extensions) -> box-free `_import_by_kind` -> kind 'game' routes the 07-07 fresh-import flow, kind 'checkpoint' routes `_resume_checkpoint_from`, and every other kind (including a missing-kind `None`) refuses with the pinned `expected an AA-match game or checkpoint file, found kind=...` message.
- `_resume_checkpoint_from`: P-2 `cancel_pending_start()` FIRST -> `gamestart.load_checkpoint` (07-09's 9-step orchestration: gates, any-identity pop, full-session load, sentinel reconcile, engine adopt + timer rebase, wizard adopt-or-rebuild) -> the full tab re-arm: `_last_status` silent-poll seed == the resumed wizard's get_status(), required label from the state's 'required' via the pure `status_text.required_display`, timer label set from `_compute_elapsed()` (the rebased anchor reads the true resumed elapsed, never a '0:00' placeholder) with the 1 Hz timer restarted iff not `game_over` (a completed checkpoint pins the EXACT frozen `final_time` and keeps the timer stopped), and the handler-logged `game_resumed_line` appended LAST. NO countdown anywhere on the resume path.
- **Rule 1 production fix landed in-flight (SMOKE-16 PART E2 surfaced it):** `engine.place_aa`/ `_slot_object` searched molecules in order with first-match while slot ids are PER-MOLECULE scoped by design (generator.py:524) -- the wizard's scripted `move_to` on any current molecule past the first silently translated the WRONG AA (first molecule's same-id object; the identity assert checked the untouched target so nothing ever raised). Fix: `place_aa(slot_id, position, molecule_index=None)` resolves within the named molecule's slots EXACTLY (None keeps the legacy Phase-2 first-match shape for the single-molecule call sites); `_move_to_impl` passes `self._molecule_index`. Nudge gameplay was never affected (nudges target `_current_object()` directly) -- only the scripted-pose seam was wrong-object.

## Task Commits

Each task was committed atomically:

1. **Task 1: persistence.peek_kind + tests** -- `38a2d87` (feat)
2. **Task 2: Import kind-dispatch + _resume_checkpoint_from + tab re-arm** -- `42278ba` (feat)
3. **Task 2-deviation: molecule-aware engine.place_aa slot resolution (Rule 1)** -- `14fccb5` (fix)
4. **Task 3: SMOKE-16 PART E -- one-button resume drive + dispatch teeth** -- `b90093c` (test)

**Plan metadata:** `<final commit>` (docs: complete plan)

## Files Created/Modified

- `aamatch/persistence.py` -- peek_kind (zip-aware); `zipfile` added to the pure import block
- `tests/test_persistence.py` -- TestPeekKind: 9 tests (JSON kinds game/checkpoint/setup, foreign/no-magic/non-dict/unparseable refusals, REAL .aamz via `checkpoint.write_checkpoint_zip` -> 'checkpoint', no-json-member zip -> sidecar-count refusal, unparseable sidecar -> shared parse wording, game-kind sidecar through the zip branch); 881 -> **890/890 WSL green**
- `aamatch/game_window.py` -- the one-button dispatch + resume impl; Import tooltip + class/module docstrings updated for both kinds
- `aamatch/engine.py` -- molecule-aware `place_aa`/`_slot_object` (Rule 1)
- `aamatch/wizard.py` -- `move_to` passes the live molecule index (Rule 1) + docstring record
- `smoke/smoke_16_tab.py` -- PART E (18 checks; file total 95: A 30 / B 23 / C 14 / D 10 / E 18)

## Decisions Made

- The three plan-recorded decisions landed as written: one-button header-exact dispatch; NO countdown on resume (instant re-arm); both-extension filter.
- **In-flight shape decision (Rule-2-adjacent):** the dispatch rides ONE `_guard` around `_import_by_kind` rather than the plan sketch's two `_guard` calls. The sketch's `kind is None -> return` treated peek's `None` return as the refusal sentinel, which would have SILENTLY swallowed a kind-less-but-valid container (no message, no branch). The single-raise-site shape boxes peek refusals and unknown kinds alike with the pinned wording; all must_haves satisfied.
- The game_over resume arm reads `final_time` via the sanctioned `engine.game_status()` call (the 7-key to_dict + extras), mirroring `_endgame_sequence`'s exact-final-label discipline.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] engine.place_aa resolved shadowed slot ids to the wrong molecule's object**

- **Found during:** Task 3 (SMOKE-16 PART E2 -- the scripted molecule-2 move reported dev=0)
- **Issue:** slot ids are per-molecule scoped by design (generator.py:524 -- 'r0c0' repeats across molecules of one level), but `engine._slot_object` searched `registry['molecules']` in order with FIRST MATCH: `move_to` on any current molecule past the first silently translated molecule-0's same-id AA (the identity assert checks the intended untouched object, so nothing raised). Nudge gameplay unaffected (it bakes `_current_object()` directly); only the scripted-pose seam was wrong-object. Zero prior smoke had scripted a move on molecule index > 0.
- **Fix:** `place_aa(slot_id, position, molecule_index=None)` + molecule-aware `_slot_object` (None keeps the Phase-2 first-match shape for legacy single-molecule call sites: smoke_04/05/06 unchanged and re-green); `wizard._move_to_impl` passes `self._molecule_index`.
- **Files modified:** aamatch/engine.py, aamatch/wizard.py
- **Verification:** SMOKE-16 E2 now proves dev=5 for the molecule-2 move pre-resume, E3 proves dev=0 after the resume replaces state; regressions SMOKE-04/06/07/15-adjacent all re-run green.
- **Committed in:** `14fccb5`

**2. [Rule 1 - Plan sketch ambiguity] single-_guard dispatch instead of the sketched two-_guard shape**

- **Found during:** Task 2 (reviewing the sketched `kind is None -> return` line)
- **Issue:** the plan sketch used peek's `None` return as the refusal sentinel, but peek_kind legitimately returns `raw.get('kind')` -- `None` for a structurally valid kind-less container. That path would have silently no-oped the Import (no message, no branch).
- **Fix:** one `_guard` around the whole `_import_by_kind` dispatch with a single `raise ValueError('expected an AA-match game or checkpoint file, found kind=%r' ...)` for every non-game/non-checkpoint kind INCLUDING None (the plan explicitly allowed "any clean shape" for the refusal path).
- **Files modified:** aamatch/game_window.py
- **Verification:** SMOKE-16 E5 drives the real dispatch with a patched-STATIC warning recorder and asserts the EXACT pinned message boxed plus the direct impl raise; scene/log/anchor/wizard untouched.
- **Committed in:** `42278ba`

---

**Total deviations:** 2 auto-fixed (both Rule 1; one production bug found by the new smoke, one plan-sketch ambiguity)
**Impact on plan:** Both fixes necessary for correctness; no scope creep. The production fix carries its own regression teeth inside PART E.

## Issues Encountered

None beyond the two recorded Rule-1 deviations. One debug detour inside Task 3 (the E2 dev=0 investigation) that RESOLVED as deviation 1 above.

## Verification Results

- `python3.6 -m py_compile aamatch/*.py` -- OK
- `python3.6 -m unittest discover -s tests` -- **890/890 OK** (was 881 at start; +9 TestPeekKind)
- `bash smoke/run_smoke.sh smoke/smoke_16_tab.py 240` -- **PASS** (95 checks: A 30 / B 23 / C 14 / D 10 / E 18)
- Regression battery (the plan's list + the hot place_aa/move_to seam):
  - SMOKE-19 (import regression anchor) -- **PASS** (39 checks)
  - SMOKE-18 (save checkpoint) -- **PASS** (31 checks)
  - SMOKE-20 two-process checkpoint E2E, BOTH runs -- **PASS** (run 1 save + run 2 verify: adopt + forced-rebuild + continue-play)
  - SMOKE-04 / SMOKE-06 / SMOKE-07 (place_aa + move_to seam) -- **PASS** (all three re-run after the Rule-1 fix)

## Authentication Gates

None.

## Next Phase Readiness

- Both load paths (fresh game file + checkpoint) are now reachable through the ONE Import button -- criterion 1's load affordance and criterion 2's single-button model are mechanically proven headlessly (SMOKE-19 fresh half + SMOKE-16 PART E resume half + dispatch teeth on a REAL .aamz).
- **For 07-11 (battery + verification):** re-run the full six/nine-smoke battery on this base; the 07-10 changes touched game_window.py, engine.py, wizard.py, persistence.py (all hot). WSL suite is 890/890.
- **For 07-12 (human checkpoint):** the GUI-visible halves needing eyes are the both-extension file dialog (default filter shows .aamz AND .aamatch.json) and a real-mouse Import of each kind (fresh game -> countdown; checkpoint -> instant re-arm with the resumed elapsed on the timer). The 'manifest'/foreign refusal boxes are _guard-backed [HUMAN]-verify candidates.
- **place_aa contract change for future smokes:** any scripted move on a non-first molecule MUST go through move_to (now molecule-scoped) or pass molecule_index explicitly; legacy cross-molecule first-match stays only for molecule-0 contexts.
- No blockers.

---
*Phase: 07-checkpoint-game-file-persistence*
*Completed: 2026-09-22*
