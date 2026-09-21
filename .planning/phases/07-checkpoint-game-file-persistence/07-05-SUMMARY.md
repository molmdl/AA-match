---
phase: 07-checkpoint-game-file-persistence
plan: 05
subsystem: persistence
tags: [py mol, checkpoint, import, embed-dont-regenerate, payload-direct, adopt_game]

# Dependency graph
requires:
  - phase: 07-checkpoint-game-file-persistence (07-01)
    provides: GameWizard argless __reduce__ rebuilder (.pse restore law)
  - phase: 07-checkpoint-game-file-persistence (07-02)
    provides: pure checkpoint.py sidecar module (game_state validator, .aamz I/O)
  - phase: 07-checkpoint-game-file-persistence (07-04)
    provides: gamestart save seams + snapshot_books + SMOKE-18
  - phase: game-file foundation (04-03)
    provides: game_file.py embed-don't-regenerate contract (the payload is the truth)
provides:
  - engine.adopt_game(payload, registry, game_state_dict, ligand_content, elapsed_at_save=None)
    -- the ONE engine-adopt seam for Import AND checkpoint resume (4 globals + P-4 rebase)
  - gamestart.start_game_from_payload(payload, ligand_content, setup, candidates, activate)
    -- payload-direct start with ZERO generator involvement
  - _last_start additive 'payload' entry (5-key tuple) -- payload-direct Restart replay
  - placement.materialize package-load CmdException wrap (STATE.md:147(b) mirror-item CLOSED)
affects: [07-07 (Import button + Restart-after-import routing), 07-09 (checkpoint resume
  engine adopt + SMOKE-20 run 2 first exercise of the rebase), 08 (MANIFEST churn safety)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "One adopt seam for both consumers: import passes fresh GameState().to_dict() +
      elapsed None; resume passes the sidecar's game_state + elapsed_at_save (conditional
      rebase iff not game_over and elapsed is not None)"
    - "Payload-direct start: start_game_from_payload = start_game minus new_game --
      cleanup-first ordering law mirrored verbatim; payload stored BY IDENTITY in
      _last_start (never re-serialized)"
    - "Additive _last_start evolution: 4 -> 5 keys; all pre-existing readers look at the
      original keys (additive-only per the format-version law)"
    - "except-Exception CmdException wrap shape at cmd tiers that bind only
      'from pymol import cmd' (no new 'import pymol' needed)"

key-files:
  created: []
  modified:
    - aamatch/engine.py
    - aamatch/gamestart.py
    - aamatch/placement.py
    - smoke/smoke_08_starter.py
    - smoke/smoke_11_window.py

key-decisions:
  - "Restart-after-import/restart = payload-direct replay (plan Recorded Decision 1):
    _last_start gains additive 'payload'; start_game captures it TOO (uniform: every
    restart goes payload-direct -- byte-identical for demo games, CORRECT for uploaded
    games); deliberate SMOKE-11 PART-H key-pin evolution 4 -> 5 keys"
  - "One adopt seam for both consumers (plan Recorded Decision 2):
    engine.adopt_game(payload, registry, game_state_dict, ligand_content,
    elapsed_at_save=None) -- rebase iff not game_over and elapsed is not None"
  - "engine.py gained module-level 'import time' (stdlib-first): the rebase is first
    exercised by 07-09's SMOKE-20 run 2 -- a lazy import would hide a missing import
    until then"

patterns-established:
  - "embed-don't-regenerate start path: materialize(payload, 0) + adopt_game(fresh state)
    + GameWizard(payload, registry, 0, 0) + compose + _last_start 5-key capture"
  - "Interloper-generation instance-stamp proof: when deterministic names are reused
    across generations, replacement is proven by the b-factor marker band reading ZERO,
    never by name sets (03-05 restart-identity law reused for the seam)"

# Metrics
duration: ~40 min
completed: 2026-09-22
---

# Phase 7 Plan 05: Payload-Direct Start Seam (engine.adopt_game + start_game_from_payload) Summary

**Import can now start a game DIRECTLY from the embedded payload -- zero generator runs, zero seed re-derivation: `engine.adopt_game` rebinds all four module globals (with the P-4 conditional timer rebase for resume), `gamestart.start_game_from_payload` materializes the embedded payload and captures a payload-bearing 5-key `_last_start`, and placement's CmdException blind spot is closed (147(b) mirror-item).**

## Performance

- **Duration:** ~40 min
- **Completed:** 2026-09-22
- **Tasks:** 3/3
- **Files modified:** 5

## Accomplishments

- `engine.adopt_game(payload, registry, game_state_dict, ligand_content, elapsed_at_save=None)` -- the ONE engine-adopt seam for import AND checkpoint resume: binds `_payload/_registry/_game/_ligand_content` from explicit inputs, rebuilds GameState losslessly through `from_dict`, wraps malformed state as `EngineError` naming the cause, and rebases the timer via `rebase_timer(now, elapsed)` iff the game is not over and elapsed is not None. `materialize` byte-identical.
- `gamestart.start_game_from_payload(payload, ligand_content=None, setup=None, candidates=None, activate=False)` -- `start_game` minus `new_game`: cleanup-first -> `materialize(payload, 0)` -> `adopt_game` (fresh GameState, timer from zero at GO) -> `GameWizard(payload, registry, 0, 0)` -> `compose_molecule_view` -> 5-key `_last_start` capture -> optional `activate`. Returns the wizard. Serves the Import button (07-07), Restart-after-import routing (07-07), and the resume's engine adopt (07-09).
- `_last_start` now uniformly 5-key (`setup`, `seed`, `candidates`, `ligand_content`, `payload`); `start_game` captures `'payload'` too -- every Restart (demo or imported-uploaded) can replay payload-direct, byte-identical for demos and CORRECT for uploads whose regeneration is manifest-dependent or impossible.
- `placement.materialize`'s package-load `cmd.load` site wraps a missing/corrupt bundled fixture's `pymol.CmdException` into `PlacementError` naming the ligand ("could not load bundled ligand ... the AA-match data files may be missing or corrupt") -- the recorded STATE.md:147(b) mirror-item is CLOSED via the except-Exception shape (no new `import pymol`).
- SMOKE-08 gained a 12-check PART 7 proving the seam end-to-end in real headless PyMOL (registry parity modulo instance, payload identity, interloper-generation replacement via the marker band, fresh GameState zeros, 5-key pin, GO parity). SMOKE-11 PART-H key pin deliberately evolved 4 -> 5 keys with the payload-carries-'seed' check added.

## Task Commits

Each task was committed atomically (worktree branch `exec/07-05`):

1. **Task 1: engine.adopt_game op** - `112f3ea` (feat)
2. **Task 2: start_game_from_payload + _last_start 'payload' + placement wrap** - `3f601b5` (feat)
3. **Task 3: SMOKE-08 new part + SMOKE-11 PART-H pin evolution** - `f4503f7` (test)
4. **In-flight pin conformance (Task 2 polish)** - `8fd3cc8` (fix): the Task-2 wrap split the `bundled ligand` token across a string-literal line break, breaking the plan's must_haves source-content pin for placement.py; the concatenation was restructured so the pinned phrase is contiguous (raised message byte-identical; caught by self-review before hand-off)

**Plan metadata:** `c186c91` + follow-up (docs: complete plan + pin-fix record)

## Files Created/Modified

- `aamatch/engine.py` -- module-level `import time` (stdlib-first) + `adopt_game` op near materialize
- `aamatch/gamestart.py` -- `start_game_from_payload` seam; `_last_start` additive `'payload'` capture in BOTH start paths; module docstring tuple comment evolved to 5 keys
- `aamatch/placement.py` -- try/except-Exception wrap around the package-resolved `cmd.load` in `materialize` -> `PlacementError` naming the ligand
- `smoke/smoke_08_starter.py` -- new PART 7 (12 checks); teardown renumbered PART 8; docstring part list updated
- `smoke/smoke_11_window.py` -- PART-H pin 4 -> 5 keys + new payload-seed check; docstring wording updated (deliberate, plan-authorized evolution)

## Verification Results

- `python3.6 -m py_compile aamatch/*.py` -- clean
- `python3.6 -m unittest discover -s tests` -- **Ran 881 tests, OK** (baseline 881 -> 881; no new WSL tests per plan's smoke-forward design)
- `bash smoke/run_smoke.sh smoke/smoke_08_starter.py 240` -- **=== SMOKE-08 PASS ===** (all prior checks + new PART 7, first run)
- `bash smoke/run_smoke.sh smoke/smoke_11_window.py 240` -- **=== SMOKE-11 PASS ===** (evolved PART-H pin)
- Regression (engine.py + gamestart.py touched): **SMOKE-04 PASS, SMOKE-15 PASS, SMOKE-16 PASS**; additionally **SMOKE-18 PASS** (hot `_last_start`/gamestart consumer; full battery stays assigned to 07-11)

## Decisions Made

None beyond the plan's two Recorded Decisions (executed verbatim):

1. Restart-after-import/restart = payload-direct replay; `_last_start` additive `'payload'`; deliberate SMOKE-11 PART-H 4 -> 5 key-pin evolution.
2. One adopt seam for both consumers (`adopt_game` signature + conditional P-4 rebase).

## Deviations from Plan

None - plan executed exactly as written. (The plan's own recorded decisions cover the SMOKE-11 PART-H evolution and the except-Exception wrap shape; both were executed as specified. The smoke_08 new part is numbered PART 7 with the teardown renumbered to PART 8 -- smoke_08 uses numbered parts, not letters; equivalent structure.)

## Issues Encountered

One in-flight self-catch (no plan-change): the Task-2 placement wrap initially split the pinned phrase `could not load bundled ligand` across a string-literal line break, so the plan's must_haves `contains` source pin did not match the file even though the raised message was correct. Caught during the final must-have artifact sweep, fixed as `8fd3cc8` (contiguous literal, message byte-identical), and re-verified (881/881 WSL + SMOKE-08 PASS). All three tasks otherwise green on first run (py_compile, both updated smokes PASS first run, all named regression smokes PASS).

## Concerns for Later Plans (07-07, 07-09, 07-11)

- **07-07 (Import + Restart routing):** `_last_start['payload']` is stored BY IDENTITY (never re-serialized). Import should call `start_game_from_payload(payload, ligand_content, setup, candidates)` with the parsed sidecar fields; Restart routing should branch on `payload` presence (additive-only: pre-07-05 sessions in flight have no key -- `.get` defensive read). The countdown-window `activate=False` default means Import should mirror the 05-09 window-driven start orchestration (pop prior wizard -> prepare -> countdown -> `activate_game`).
- **07-09 (resume):** `adopt_game`'s `elapsed_at_save` rebase path has **no headless exercise yet** (adopted with elapsed=None everywhere in this plan) -- SMOKE-20 run 2 is its first live proof. Note the rebase happens INSIDE adopt_game at adopt time (single-anchor P-4: `timer_anchor = now - elapsed`); the resumed game must NOT also call `start_timer` afterwards or the rebase is lost.
- **07-09 / save→resume symmetry:** `start_game_from_payload` mints a FRESH GameState; the resume flow must NOT route through it for state restoration (use materialize + adopt_game with the sidecar's `game_state` dict directly so progress survives).
- **Placement wrap scope:** ONLY the package-resolved `cmd.load` branch is wrapped (per plan). The `ligand_content` string-load branches (read_sdfstr/read_mol2str-guard) keep their existing fail-closed behavior unwrapped.
- **Full battery:** SMOKE-07/13/14/17 not re-run here (out of the plan's named regression set); 07-11 owns the full re-verify.

## Next Phase Readiness

Ready for wave-4 plans 07-07 (Import button + restart routing) and 07-09 (checkpoint resume) -- both consumers of the payload-direct seam now have their engine/gamestart contract in place, smoke-proven for the fresh-import shape.

---
*Phase: 07-checkpoint-game-file-persistence*
*Completed: 2026-09-22*
