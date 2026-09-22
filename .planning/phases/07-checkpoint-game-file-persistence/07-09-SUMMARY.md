---
phase: 07-checkpoint-game-file-persistence
plan: 09
subsystem: persistence
tags: [checkpoint, pse, sidecar, reconstruction, sentinel-first, adopt_game, resume_from, e2e]

requires:
  - phase: 07-checkpoint-game-file-persistence
    provides: "07-02 checkpoint pure module (gates/reconcile/zip I/O); 07-05 engine.adopt_game + payload-direct seam; 07-08 is_game_wizard_any_identity + GameWizard.resume_from; 07-04 capture/save seams"
provides:
  - "gamestart.load_checkpoint(path): the 9-step sentinel-first reconstruction (gates-first -> pop -> cmd.load -> sweep -> reconcile -> adopt_game+rebase -> wizard adopt-or-rebuild -> _last_start -> summary)"
  - "_canonical_registry: the adopt-with-verify tuple/list normalizer (single fix site for registry-equality compares)"
  - "SMOKE-20: two-process checkpoint E2E (save -> quit -> relaunch -> load), adopt + forced-rebuild branches mechanically proven"
affects: [07-10 kind-dispatch/import + tab re-arm, 07-11 full battery, criterion-1/3 human checkpoint]

tech-stack:
  added: []
  patterns:
    - "exact-scene restore: loaded .pse atoms are the truth; sidecar repairs Python-side metadata only (no regeneration, no pose data)"
    - "adopt-with-verify with canonicalized registry equality (materialize ids = sorted LISTS; reconcile ids = TUPLES)"
    - "timer rebase on resume (rebase_timer(now, elapsed_at_save)); NO countdown/activate_game on resume (activate(replace=0) only)"
    - "msm repair lands in the rebuilt wizard's _saved_msm (live value stays the in-game defensive 0 ORDER LAW)"

key-files:
  created: [smoke/smoke_20_checkpoint_e2e.py]
  modified: [aamatch/gamestart.py]

key-decisions:
  - "Registry-equality verify MUST canonicalize tuple/list containers (never a bare plain-dict compare) — materialize and reconcile emit different container types for the SAME ids"
  - "msm repair is checked at its landing spot (rebuilt _saved_msm == sidecar saved_msm; post-pop cmd.get == saved_msm), not at live value (activate's defensive 0 ORDER LAW)"

patterns-established:
  - "Two-process E2E via expected-facts container + _norm deep tuple->list normalizer for pickle-vs-JSON cross-process compares"
  - "Forced-branch smoke pattern: module-attribute predicate patch + try/finally restore intercepts gamestart's call-time lookup"

duration: 69 min
completed: 2026-09-22
---

# Phase 7 Plan 9: Checkpoint Load (Sentinel-First Reconstruction) Summary

**`gamestart.load_checkpoint` reconstructs a saved game exactly — scene from the `.pse` (bit-exact), books from the sidecar, timer rebased — proven by SMOKE-20's two-process save → quit → relaunch → load E2E on both the adopt and forced-rebuild branches.**

## Performance

- **Duration:** 69 min (incl. one debug detour + regression battery)
- **Started:** 2026-09-22T01:58:05Z
- **Completed:** 2026-09-22T03:07:01Z
- **Tasks:** 2/2 (plan lists 2 tasks)
- **Files modified:** 2 (1 modified, 1 created)

## Accomplishments

- `gamestart.load_checkpoint(path)` — the 9-step sentinel-first load order (07-RESEARCH-state.md §4): ALL parse gates before any scene mutation; pop any-identity GameWizard (cleanup runs before `cmd.load` replaces the stack); full-session `cmd.load`; sentinel sweep with `segi AAM and b < 0` verification; `reconcile_registry` never-ghost + completeness gates; `engine.adopt_game` with sidecar game_state + timer rebase; wizard **adopt-with-verify** or **rebuild** (`resume_from` + msm repair + `activate(replace=0)`, never `activate_game`); 5-key payload-direct `_last_start` rebuild; plain summary dict for the 07-10 tab re-arm; temp dir rmtree on every exit path.
- SMOKE-20 (32 checks on run 2) — the two-process checkpoint E2E: run 1 saves mid-game (moved+rotated AA, hint recolors, skip recorded, `elapsed=123.0`); run 2 (fresh process = the relaunch) proves the dead-start state, then that the restored game is the saved game: books equal, `game_status()` equal except `timer_anchor` (rebase drift **0.004 s**), centroids float32-tight, detect count equal, identity invariant on recolored slots, `_last_start` rebuilt, and the game **continues to be playable** (molecule-2 pick + confirm advances the level).
- Forced-rebuild scenario (predicate patched False) mechanically exercises the repair branch: `resume_from` books restored, `_registry == sidecar registry`, msm repaired into `_saved_msm`, wizard pushed with `activate(replace=0)`.

## Task Commits

Each task was committed atomically:

1. **Task 1: gamestart.load_checkpoint(path)** - `c750fc1` (feat)
2. **(Rule-1 fix during Task 2 verify) canonicalize adopt-with-verify** - `ac99221` (fix)
3. **Task 2: SMOKE-20 two-process checkpoint E2E** - `3b751d3` (test)

## Files Created/Modified

- `aamatch/gamestart.py` — added `load_checkpoint` + `_canonical_registry` (modified)
- `smoke/smoke_20_checkpoint_e2e.py` — the SMOKE-20 two-run E2E (created)

## Verification Outputs

- `python3.6 -m py_compile aamatch/*.py` — clean
- `python3.6 -m unittest discover -s tests` — **881/881 OK** (32 s)
- SMOKE-20 run 1 (SAVE): 14 checks PASS — `=== SMOKE-20 PASS ===`
- SMOKE-20 run 2 (VERIFY): 32 checks PASS — `=== SMOKE-20 PASS ===`
- Regression: SMOKE-08 PASS; SMOKE-18 PASS (31 checks); SMOKE-17 ×2 PASS (`coords_exact: True`, `wizard_restore: GameWizard`)

## Decisions Made

- **Canonicalized registry verify:** the adopt-with-verify compares `_canonical_registry(...)` forms (values untouched, containers normalized) because `placement._sorted_ids` returns sorted LISTS while `checkpoint.reconcile_registry` emits TUPLES — a bare plain-dict compare was a false mismatch on every exact-identity restore.
- **msm repair observable contract:** after `activate(replace=0)` the LIVE `mouse_selection_mode` is the in-game defensive 0 (03-03 ORDER LAW: activate snapshots-then-zeroes); the repair's evidence is `rebuilt._saved_msm == sidecar saved_msm` plus a pop→cleanup proof (`cmd.get` == saved_msm after the pop).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Adopt-with-verify false mismatch (plan's "plain-dict equality" assumption)**

- **Found during:** Task 2 (SMOKE-20 run 2, adopt-path summary assert)
- **Issue:** The plan specifies the adopt verify as "its `_registry` equals the reconciled registry (plain-dict equality — both derive from the same materialize output)". The second clause is false: materialize's ids ride as sorted **lists** (`_sorted_ids` returns `sorted(...)`), while `reconcile_registry` normalizes to **tuples**. The literal compare can NEVER hold — every exact-identity restore silently fell into the rebuild branch (adoption defeated without failing anything else).
- **Fix:** `_canonical_registry` deep tuple→list normalizer in gamestart.py; the verify compares canonical forms (identity, not representation). Debug-probed empirically (one-off probe, removed after).
- **Files modified:** aamatch/gamestart.py
- **Verification:** SMOKE-20 run 2 `adopted: True` + adopted-books/registry/status asserts PASS
- **Committed in:** `ac99221`

**2. [Rule 1 - Bug] Plan's msm check mechanically impossible after `activate(replace=0)`**

- **Found during:** Task 2 (forced-rebuild scenario design)
- **Issue:** The plan's forced-rebuild step asks to assert `cmd.get('mouse_selection_mode') == data['wizard']['saved_msm']` while the rebuilt wizard is live. But `activate()` snapshots-then-zeroes msm (03-03 ORDER LAW), so the live value is the in-game defensive 0 — the literal assert would fail for every save where saved_msm != 0 (default is 1).
- **Fix:** The check is routed to the repair's actual landing spot: `rebuilt._saved_msm == sidecar saved_msm` (the repair owns the books value), `cmd.get(...) == 0` (defensive live value), and a pop→cleanup proof that the session recovers `saved_msm`. Smoke-only; production seam unchanged (the seam's repair ordering — repair BEFORE activate — is exactly what makes `activate`'s snapshot capture the repaired value).
- **Files modified:** smoke/smoke_20_checkpoint_e2e.py (checks + docstring note)
- **Verification:** SMOKE-20 C-block msm triplet PASS
- **Committed in:** `3b751d3`

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs)
**Impact on plan:** Both fixes necessary for the plan's OWN must-haves (truths 4: "adopted when the pickle restored it (with a registry-equality verify)" and the forced-rebuild msm mechanic). No scope creep.

## Issues Encountered

- One debug detour to identify deviation 1 (one-off probe script; not committed, moved out of the repo). No production-blocked state.

## Next Phase Readiness

- **07-10 (kind-dispatch Import + tab re-arm):** `load_checkpoint` returns `{'path','adopted','level_pos','molecule_pos','game_over','elapsed_at_save'}` for the re-arm. Note for the dispatch UX: a bare `.pse` at the Import button refuses at the zip OPEN (`FormatError: not an AA-match archive (unreadable zip: ...)`) — the plan decision-4 wording "could not parse AA-match JSON" is the JSON-member class; the actual first-touch message is the BadZipFile one, so 07-10's tests should pin the real message.
- **Registry equality law for downstream authors:** any future registry-identity compare must normalize containers (`gamestart._canonical_registry` is the single fix site) — materialize ids are lists, reconcile ids are tuples.
- **07-11 full battery:** SMOKE-20 joins the battery contract (run twice); baseline here: run 1 = 14 checks, run 2 = 32 checks.

---
*Phase: 07-checkpoint-game-file-persistence*
*Completed: 2026-09-22*
