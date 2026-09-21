---
phase: 07-checkpoint-game-file-persistence
plan: 04
subsystem: persistence
tags: [checkpoint, aamz, pse, save, sidecar, gamestart, wizard, smoke, pymol]

# Dependency graph
requires:
  - phase: 07-checkpoint-game-file-persistence (07-01)
    provides: GameWizard argless __reduce__ rebuilder (the pickled-wizard restore path the .pse half rides)
  - phase: 07-checkpoint-game-file-persistence (07-02)
    provides: checkpoint.py pure home — build_checkpoint_data / parse_checkpoint_data / write_checkpoint_zip / read_checkpoint_zip
provides:
  - gamestart.capture_checkpoint_snapshot(elapsed=None) — the cmd-tier capture seam (complete sidecar data dict, scene-read-only)
  - gamestart.save_checkpoint(path, data) — the atomic .aamz write seam (FULL-session cmd.save + zip + temp cleanup)
  - GameWizard.snapshot_books() — the sanctioned public plain-data read of the wizard repair block
  - SMOKE-18 — headless save E2E (capture -> atomic zip -> gate round-trip -> in-process .pse restore)
affects: [07-05 (load/reconstruct side), 07-06 (Qt Save button wrapper on these seams), 07-08 (resume consumes the wizard block)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Capture-before-dialog timer doctrine (elapsed captured pre-dialog, stored verbatim; game_over -> None)"
    - "Full-session save scope paired with full-replace load (game-scoped save would destroy user objects on resume)"
    - "cmd-tier lifecycle home = the ONLY sanctioned direct reader of engine._payload/_registry/_ligand_content (Qt tier goes through this seam)"

key-files:
  created: [smoke/smoke_18_save_checkpoint.py]
  modified: [aamatch/wizard.py, aamatch/gamestart.py]

key-decisions:
  - "cmd.save scope = FULL session (no selection argument), paired with full-replace load (07-04 Recorded Decision 1)"
  - "Timer doctrine: caller-passed elapsed stored VERBATIM; None -> max(0.0, now - timer_anchor) live; game_over -> None (final_time authoritative)"
  - "Save on game_over = ALLOW (no extra gate; to_dict carries game_over/end_state/final_time losslessly)"
  - "snapshot_books omits _result by design (always None in the advance flow)"

patterns-established:
  - "Save-seam discipline: capture is scene-read-only (no I/O), write is atomic (temp+os.replace) with finally temp unlink, and neither disturbs game state (S3-6)"
  - "Smoke BOOKS-round-trip proof: restored.snapshot_books() == captured sidecar 'wizard' block through the REAL pickle path"

# Metrics
duration: 13 min
completed: 2026-09-21
---

# Phase 7 Plan 04: Checkpoint Save Seams (cmd-tier capture + atomic .aamz + wizard books) Summary

**SCORE-08's save half landed: `capture_checkpoint_snapshot`/`save_checkpoint` cmd seams in gamestart, the wizard's public books snapshot, and SMOKE-18 proving capture -> atomic zip -> REAL-gate round-trip -> REAL `__reduce__` wizard restore headlessly (31/31 checks).**

## Performance

- **Duration:** 13 min
- **Started:** 2026-09-21T19:30:40Z
- **Completed:** 2026-09-21T19:43:17Z
- **Tasks:** 3/3
- **Files modified:** 2 modified, 1 created

## Accomplishments

- `GameWizard.snapshot_books()` — additive plain-data public read (current_slot/color_store/event_seq/last_event/error/saved_msm; `_result` deliberately omitted; zero viewer calls, lazy `copy` import).
- `gamestart.capture_checkpoint_snapshot(elapsed=None)` — the complete 07-RESEARCH-state.md §2 sidecar dict via `checkpoint.build_checkpoint_data`: game block = full `make_game_data` output verbatim (setup from `_last_start`, `engine._payload` embedded by identity, upload ligand_files re-encoded), game_state verbatim via `engine.game_status()`, identity-only registry, wizard books, candidates. Scene-read-only.
- `gamestart.save_checkpoint(path, data)` — `to_windows_path` -> in-process temp `.pse` (no path conversion, S3-3) -> FULL-session `cmd.save` -> `checkpoint.write_checkpoint_zip` (atomic temp+os.replace; members game.pse + state.json exactly) -> temp unlink in `finally`. Returns the final path; failures propagate to the caller's `_guard` with scene/game untouched.
- SMOKE-18 (single-run, A/B/C/D/E/Z parts): scripted pick `r0c0` + baked move/rotate + hint (7-object color store) + skip (partial 0.00, skip_count 1, advance to molecule 2) -> capture asserts -> save + zip-member/temp-leak asserts -> full-gate component round-trip -> post-save engine-integrity asserts -> in-process `cmd.load` of the extracted .pse restoring an ACTIVE GameWizard with books == the sidecar block and all 20 saved object names returning.

## Task Commits

Each task was committed atomically:

1. **Task 1: GameWizard.snapshot_books() additive public op** — `45d11a5` (feat; estate green at 881/881 after the edit)
2. **Task 2: gamestart.capture_checkpoint_snapshot + save_checkpoint** — `54f13e9` (feat; 881/881)
3. **Task 3: SMOKE-18 — headless save E2E** — `ba7758a` (test; first full run 1 scripted-assert fix, then 31/31 PASS)

**Plan metadata:** committed below (docs: complete 07-04 plan)

## Files Created/Modified

- `aamatch/wizard.py` — `snapshot_books()` added after `get_status` (~line 431); module-level imports unchanged.
- `aamatch/gamestart.py` — two module-level seams appended after `start_game`; lazy `os`/`tempfile`/`paths`/`checkpoint`/`game_file` imports inside the functions per the file's established pattern.
- `smoke/smoke_18_save_checkpoint.py` — SMOKE-18, 31 checks across parts A(8)/B(10)/C(5)/D(3)/E(3)/Z(2).

## Verification Results

- `python3.6 -m py_compile aamatch/*.py` — OK (Gate D).
- `python3.6 -m unittest discover -s tests` — **881/881 green** after every task (final run 881 tests OK; purity gates untouched — no PURE_MODULES changes, no stubs).
- `bash smoke/run_smoke.sh smoke/smoke_18_save_checkpoint.py 240` — `=== SMOKE-18 PASS ===` (31/31).
- SMOKE-17 regression (wizard.py touched — plan-mandated re-run, two runs): run 1 (phase A save) PASS, run 2 (phase B verify) PASS — strict wizard restore compare still PROVEN, coords/view bit-exact.
- SMOKE-08 regression (gamestart.py touched — standing regression discipline): PASS (restart idempotence + zoom/composition asserts all green).

## Decisions Made

None new beyond the plan's three RECORDED DECISIONS, which were implemented verbatim (full-session save scope; capture-before-dialog timer doctrine with game_over -> None; save on game_over allowed). Implemented-semantics reconciliations for the smoke's scripted asserts are documented below as Rule-1 deviations (02-12 precedent: smokes pin implemented semantics, not plan sketches).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan-script semantics] PART B scripted-slot assert reversed on purpose**

- **Found during:** Task 3 (SMOKE-18 authoring)
- **Issue:** The plan's PART B scripts `skip_molecule()` into the scenario and then asserts `data['wizard']['current_slot'] == the scripted slot`. The skip's advance routes through the ONE shared `_advance_after_record` site -> `_rebind_molecule` -> `_rebind_maps`, which sets `_current_slot = None` (06-05 rebind law, wizard.py:495). The scripted assert would fail against the true, frozen lifecycle semantics.
- **Fix (smoke-only, zero production divergence):** PART A asserts the pick selected the scripted slot (`r0c0`); PART A additionally asserts the skip advance cleared the selection (rebind semantics pinned explicitly); PART B asserts `data['wizard'] == wiz.snapshot_books()` VERBATIM — strictly stronger than the single-key assert.
- **Files modified:** smoke/smoke_18_save_checkpoint.py
- **Verification:** `A skip advance cleared the selection (rebind semantics)` + `B wizard block == wiz.snapshot_books() (VERBATIM)` PASS; PART E's restored-books equality (slot=None) confirms the captured None round-trips.

**2. [Rule 1 - Plan-shorthand vs API shape] `data2 == data` realized as field-wise component equality**

- **Found during:** Task 3 (SMOKE-18 authoring)
- **Issue:** The plan's PART C says "assert data2 == data (full round-trip through the REAL gates)", but `checkpoint.read_checkpoint_zip` returns PARSED COMPONENTS (`{'setup','payload','ligand_texts','game_state','elapsed_at_save','registry','wizard','candidates'}`), not the raw sidecar dict (07-02's established parse API).
- **Fix (smoke-only):** PART C asserts every parsed component field-wise against the captured blocks (`setup` vs `data['game']['setup']`, `payload` vs the embedded level_spec, `game_state`/`elapsed_at_save`/`registry`/`wizard`/`candidates` verbatim, `ligand_texts == {}`) — the full round-trip at equal-or-greater strength through the REAL four-gate chain.
- **Files modified:** smoke/smoke_18_save_checkpoint.py
- **Verification:** `C sidecar re-reads through ALL REAL parse gates` + `C parsed components round-trip EVERY sidecar block` PASS.

---

**Total deviations:** 2 auto-fixed (both Rule 1, both smoke-script reconciliations of plan shorthand; ZERO production-code divergence from the plan's pinned contracts).
**Impact on plan:** None on shipped semantics — capture/save/wizard ops match the plan and research verbatim.

## Issues Encountered

- First SMOKE-18 run failed exactly one check (`B capture returned the full checkpoint data dict`): my expected sorted key list was alphabetically wrong (`candidates` sorts before `checkpoint_format_version`). One-line smoke fix, re-run 31/31 PASS. Not a deviation (authoring slip), recorded for honesty.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **07-05 (load/reconstruct) inherits:** the complete sidecar data producer; the exact capture-time books shape (`snapshot_books`); proof the in-process `cmd.load` of an extracted `.pse` restores an ACTIVE GameWizard with byte-equal books (so its reconcile/adopt branches have a real, green baseline).
- **07-06 inherits:** the two seams' exact call contract — the Qt wrapper owns the `elapsed` pre-dialog capture (captured value stored VERBATIM by the capture seam), the gate-first silent no-op when no live GameWizard, the `_guard` error surfacing (OSError/ValueError propagate), and the `game_saved_line` log AFTER the scheduling. `save_checkpoint` returns the final path for the log line.
- No blockers. Concern for 07-08: the captured sidecar 'wizard' block (consumed by resume_from on the repair path) has a PROVEN content identity — restored pickle books == captured block (SMOKE-18 PART E) — so the books-block semantics are field-verified, not just schema-verified.

---
*Phase: 07-checkpoint-game-file-persistence*
*Completed: 2026-09-21*
