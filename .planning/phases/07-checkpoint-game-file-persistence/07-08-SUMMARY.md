---
phase: 07-checkpoint-game-file-persistence
plan: 08
subsystem: persistence
tags: [pymol, wizard, pickle, module-identity, checkpoint, sidecar, smoke]

requires:
  - phase: 07-checkpoint-game-file-persistence
    provides: "07-01 argless __reduce__ rebuilder (+module identity law); 07-02 checkpoint sidecar schema ('wizard' block additive .get reads); 07-04 snapshot_books public books read (the exact shape resume_from consumes)"
  - phase: 03-wizard-gameplay-loop
    provides: "03-02 endswith module-identity-dodge pattern; 03-04 SMOKE-07 wizard-loop smoke (the host of the new PART G)"
provides:
  - "is_game_wizard_any_identity(wiz) module predicate -- name + module-suffix form catches a GameWizard under EITHER import identity (aamatch.wizard / pmg_tk.startup.aamatch.wizard)"
  - "GameWizard.resume_from(books) additive public op -- adopts the sidecar 'wizard' repair block (current_slot, color_store, event_seq, last_event, error, saved_msm) with .get additive defaults, plain data only, zero cmd calls"
  - "SMOKE-07 PART G: books snapshot -> test-only corruption -> resume_from -> field-exact equality proof + predicate battery (11 new checks, 85 PASS lines total)"
affects: [07-09 load_checkpoint (the pop-before-load step consumes the predicate; the rebuild path consumes resume_from), 07-10 kind-dispatch, 07-12 human checkpoint (cross-identity repair path survivability)]

tech-stack:
  added: []
  patterns:
    - "Module-identity-agnostic detection by name + __module__ suffix (never isinstance across module objects)"
    - "Rebuild-path books adoption: additive .get defaults, unknown keys ignored by simply not reading them (P9 passthrough); re-derive, never adopt, the _sync_end_state mirrors"

key-files:
  created: []
  modified:
    - aamatch/wizard.py
    - smoke/smoke_07_wizard_loop.py

key-decisions:
  - "Predicate is a pure suffix match on type(wiz).__module__.endswith('aamatch.wizard') -- deliberately permissive: matches aamatch.wizard, pmg_tk.startup.aamatch.wizard, and any equally-suffixed path (07-RESEARCH-state.md sec. 6; the 03-02 endswith law)"
  - "resume_from performs NO recolor/rebuild -- the loaded .pse already shows the saved colors bit-exactly (SMOKE-17); the books restore only the ORIGINAL-color snapshot consumed by a later cleanup()"

patterns-established:
  - "Books round-trip smoke proof: snapshot -> deep-copy -> test-only direct corruption of every field -> resume_from -> equality (priors never merge; resume overwrites)"
  - "Foreign-identity stub construction in smokes: type(name, (object,), {'__module__': <foreign>}) -- the module string must genuinely fail the suffix"

duration: 9 min
completed: 2026-09-22
---

# Phase 7 Plan 08: Wizard Rebuild Primitives Summary

**Identity-agnostic GameWizard detection (`is_game_wizard_any_identity`) and the sidecar books repair op (`GameWizard.resume_from`) -- the two wizard-side primitives the 07-09 checkpoint rebuild path needs, smoke-proven end-to-end by SMOKE-07 PART G.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-09-21T23:34:45Z
- **Completed:** 2026-09-21T23:43:38Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments

- `is_game_wizard_any_identity(wiz)` module-level predicate beside `_rebuild_game_wizard` (aamatch/wizard.py): `wiz is not None and type(wiz).__name__ == 'GameWizard' and type(wiz).__module__.endswith('aamatch.wizard')` -- identity-agnostic by construction, because a pickle-resolved instance must live under one of the two import paths and `isinstance` cannot cross module objects.
- `GameWizard.resume_from(books)` additive public op beside `snapshot_books`: consumes EXACTLY the 07-04 snapshot shape with additive `.get` defaults; normalizes the sidecar's JSON `[[id, color], ...]` pairs back to `(int id, color)` tuples-of-pairs (the store is rebuilt, never the sidecar lists adopted by reference); zero cmd calls.
- SMOKE-07 PART G (11 new checks): `gamestart.start_game()` -> scripted pick (sets `_current_slot`) -> `hint()` (7-object color store) -> `snapshot_books` + deepcopy -> direct corruption of all six book fields -> `resume_from` -> every field reads back exactly; predicate battery covers live-True plus None / plain-object / foreign-stub False; scene-exact teardown.

## Task Commits

1. **Task 1: predicate + resume_from** - `793abd2` (feat)
2. **Task 2: SMOKE-07 PART G** - `4f61fd6` (test)

**Plan metadata:** see the docs commit that closes this plan.

## Files Created/Modified

- `aamatch/wizard.py` - +36 lines: `is_game_wizard_any_identity` after `_rebuild_game_wizard`; `GameWizard.resume_from` after `snapshot_books`
- `smoke/smoke_07_wizard_loop.py` - +119/-1 lines: `import copy`, `gamestart`/`wizard_mod` imports, PART G docstring entry, PART G block

## Decisions Made

- **Suffix-match predicate semantics:** `endswith('aamatch.wizard')` is deliberately permissive (any `*.*.aamatch.wizard` path matches, incl. `pmg_tk.startup.aamatch.wizard`); the pop-before-load step only needs to catch every pickle-resolvable GameWizard, never to discriminate subpaths.
- **No visual repair in resume_from:** the loaded .pse already carries the saved per-atom colors (SMOKE-17 bit-exact), so resume performs no recolor/rebuild -- the books exist solely for a later `cleanup()`'s original-color restore.
- **Mirrors re-derived, never adopted:** `_game_over`/`_end_state` stay constructor/fresh-state data on the rebuild path (the constructor's GameState-driven state owns them; the wizard ops are the only mutation path, so drift is impossible).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan's foreign-identity stub string actually MATCHES the suffix predicate**

- **Found during:** Task 2 (first SMOKE-07 run -- PART G's negative control FAILed)
- **Issue:** the plan directs a stub with `__module__ = 'not_aamatch.wizard'`, claiming "the module suffix does not [match]"; but `'not_aamatch.wizard'.endswith('aamatch.wizard')` is **True** (endswith is a pure suffix match; `'not_'` + `'aamatch.wizard'` still ends with the target), so the predicate correctly returned True and the negative control failed.
- **Fix:** the stub module changed to `'foreign.wizard'` (genuinely fails the suffix), with an in-file comment recording why. Production code (`aamatch/wizard.py`) was untouched -- the predicate's permissive suffix form is the RESEARCH-sec-6-pinned design, not a defect.
- **Files modified:** smoke/smoke_07_wizard_loop.py
- **Verification:** SMOKE-07 FULL PASS re-run after the fix; the True/None/plain/foreign battery all discriminate as intended.
- **Committed in:** `4f61fd6` (Rule-1 plan fix, documented in comment)

**2. [Plan-text note - no code impact] "Update the check-count print"**

- SMOKE-07 has no numeric check-count print (per-check PASS lines + the `=== SMOKE-07 PASS ===` marker only; the module docstring is the part documentation). Interpreted the plan as extending the docstring PART list + preserving the marker; both done (PART G entry added).

---

**Total deviations:** 1 auto-fixed (Rule 1, smoke-file only; production predicate unchanged) + 1 plan-text reading note. **Impact on plan:** the negative control now tests what the plan intended (a genuinely foreign identity); zero scope change.

## Issues Encountered

None beyond the deviation above -- first-run smoke surfaced exactly the stub-string flaw, no production debugging needed.

## User Setup Required

None -- no external service configuration required.

## Verification Evidence

| Gate | Result |
|------|--------|
| `python3.6 -m py_compile aamatch/*.py` | OK |
| `python3.6 -m unittest discover -s tests` | **881/881 OK** (test_wizard_source AST scan + PROSE_PIN green) |
| `smoke/run_smoke.sh smoke/smoke_07_wizard_loop.py 240` | **PASS** -- 85 PASS lines, incl. all 11 PART-G checks |
| `smoke/run_smoke.sh smoke/smoke_17_pse_roundtrip.py 240` (run 1) | **PASS** |
| `smoke/run_smoke.sh smoke/smoke_17_pse_roundtrip.py 240` (run 2) | **PASS** |
| `smoke/run_smoke.sh smoke/smoke_16_tab.py 240` | **PASS** -- 77/77 |

## Next Phase Readiness

- 07-09 can consume both primitives directly: `is_game_wizard_any_identity` guards the pop-before-load step (catches a foreign-identity restored wizard), and `GameWizard(payload, registry, L, M).resume_from(sidecar['wizard'])` applies the repair block after the constructor re-derives the pick maps -- remember the resume seam must be materialize + `engine.adopt_game` (07-05 note), NEVER `start_game_from_payload`, and activate via `wiz.activate(replace=0)`, NOT `activate_game` (research sec. 4 step 7; rebase owns the timer).
- The rebuild path's msm repair (research sec. 4 step 6: `cmd.set('mouse_selection_mode', books['saved_msm'])`) is 07-09's responsibility -- resume_from deliberately does not touch viewer state.
- Concern for 07-09: a same-identity adopt path must verify `_registry` equals the reconciled registry before adopting (research sec. 4 step 7) -- that comparison site is 07-09's, not covered here.

---
*Phase: 07-checkpoint-game-file-persistence*
*Completed: 2026-09-22*
