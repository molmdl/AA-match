---
phase: 01-bootstrap-pure-foundation
plan: 05
subsystem: persistence
tags: [setup-schema, json-persistence, validation, tdd, python36-stdlib, deterministic-random, persist-01]

# Dependency graph
requires:
  - phase: 01-bootstrap-pure-foundation (01-01, 01-02)
    provides: aamatch package skeleton (zero-stub composition root); versioned container core (magic/version/kind, FormatError refusals, atomic JSON I/O)
provides:
  - aamatch/setup_state.py: 7-field setup model (INTERACTION_TYPES 7-value enum, INTERACTION_MODES 3-value enum, clamp constants 2/1/10 and 3/1/9, DEFAULTS, validate_state non-mutating, randomize_state seed-deterministic)
  - persistence.save_setup_file / load_setup_file: validate-before-write + validate-on-load wrappers over the versioned container
  - PERSIST-01 proven end-to-end in WSL: every-field-non-default round-trip with exact dict equality; all four refusal classes message-asserted; older versions accepted with DEFAULTS forward-fill
affects: [01-06-level-spec, phase-2-generator, phase-4-gui, phase-8-demos, 01-08-purity-gates]

# Tech tracking
tech-stack:
  added: [] # stdlib only (copy, random)
  patterns:
    - "validate-on-save AND validate-on-load via a single validate_state (idempotent fixpoint)"
    - "deepcopy(DEFAULTS) base + never-mutate-input validation (D3/P6)"
    - "canonical list ordering (allowed_interactions stored in INTERACTION_TYPES order so equal sets serialize identically)"
    - "local random.Random(seed) for seed-deterministic state generation (D4)"
    - "container header is the ONLY format tag -- no 'format' data field (P8)"

key-files:
  created:
    - aamatch/setup_state.py
    - tests/test_setup_state.py
  modified:
    - aamatch/persistence.py

key-decisions:
  - "Adopted research R4 numeric defaults: MOLECULES 2/1/10, DIFFICULTY 3/1/9, interaction_mode default 'unset' (spec 'default 2-5'/'default 3-5' read as default-value + clamp range) -- human re-confirms at the 01-09 checkpoint"
  - "No 'format' field in setup data: container header (magic/version/kind) is the only format tag (P8; prior art carried both, C1)"
  - "randomize_state keeps source_mode='demo' and upload=None: a randomized state must be usable without a real file"
  - "Non-dict validate_state input treated as {} (fills from DEFAULTS): hand-edited data payloads degrade to defaults instead of AttributeError, consistent with the hand-editable-files design"
  - "JSON null (None) counts as missing for str-coerced fields (demo_set_id null -> '')"

patterns-established:
  - "Pure model module docstring = single source of truth phrasing + NO Qt/NO pymol purity statement (D1)"
  - "Refusal-message reuse from 01-02 canonical phrasing (not an AA-match file / unsupported ... Please update AA-match / expected an AA-match <kind> file / could not parse AA-match JSON)"
  - "RED-first 13-case suite with message-asserted refusals and subTest-per-mode round-trip"

# Metrics
duration: 4min
completed: 2026-09-05
---

# Phase 1 Plan 05: Setup Model + Versioned Setup-File I/O Summary

**7-field setup model (validate non-mutating, randomize seed-deterministic) wired through the versioned container with validate-on-save+load -- PERSIST-01 proven: every-field-non-default round-trip is exact-dict-equal, all four refusal classes message-asserted**

## Performance

- **Duration:** 4 min
- **Started:** 2026-09-05T16:27:21Z
- **Completed:** 2026-09-05T16:30:50Z
- **Tasks:** 3/3 (RED, GREEN, REFACTOR-assessed)
- **Files modified:** 3 (1 created module, 1 created test suite, 1 extended module)

## Accomplishments
- `aamatch/setup_state.py` (pure, stdlib-only): INTERACTION_TYPES (7 types), INTERACTION_MODES (exclusive/block_exclusive/unset), clamp constants (molecules 2/1/10, difficulty 3/1/9), DEFAULTS (exactly 7 fields, no `format` field per P8), `validate_state` (NEW dict from deepcopy(DEFAULTS); enum fallback; int coerce+clamp; allowed_interactions filtered/deduped/canonical-ordered; upload shape-checked to {path, sha256}; input never mutated), `randomize_state` (local `random.Random(seed)`, deterministic, demo_set_id `'demo-####'`, non-empty canonical interaction subset, source_mode stays demo / upload stays None)
- `persistence.py` extended minimally: module-level `from .setup_state import validate_state` (pure<-pure, B8), `save_setup_file` (validate-before-write), `load_setup_file` (validate-on-load, idempotent); 01-02 container core untouched
- PERSIST-01 proven in WSL: state with every field non-default (unicode demo_set_id `démo-β`, molecules at MIN, difficulty at CAP, all 7 interaction types, upload dict, subTest per each of the 3 modes) round-trips through a versioned setup file with EXACT dict equality; refusal classes (a)-(d) message-asserted; `version: FORMAT_VERSION - 1` accepted; v0-style data dict forward-filled from DEFAULTS
- Phase-1 prior art retired: the headerless raw `json.dump` setup save (gui_setup.py:644-686, C2/C3) is replaced by container-discipline I/O

## Task Commits

Each TDD stage committed atomically:

1. **RED: failing 13-case suite** - `2683b52` (test)
2. **GREEN: model + wrappers** - `6994a41` (feat)
3. **REFACTOR:** no changes needed -- implementation was already minimal; no commit (per plan: "Commit if changed")

## Files Created/Modified
- `aamatch/setup_state.py` - created: the pure 7-field setup schema model (enums, clamps, DEFAULTS, validate_state, randomize_state)
- `aamatch/persistence.py` - modified: purity docstring now lists the pure sibling import; + module-level validate_state import; + save_setup_file/load_setup_file wrappers appended after load_container
- `tests/test_setup_state.py` - created: 370-line RED-first suite, 25 tests (key-set regression, validation/clamping matrix, non-mutation incl. deep-aliasing, deterministic randomize, round-trip per mode, idempotence, refusals, older-version acceptance, forward-fill)

## Decisions Made
- Adopted the plan's `<decisions>` block verbatim: molecules 2/1/10, difficulty 3/1/9, interaction_mode default "unset"; these are flagged for human re-confirmation at the 01-09 checkpoint (not re-litigated here)
- Header-only format tagging: no `format` field anywhere in setup data (P8; the DEFAULTS key-set test fails loudly if one is re-added)
- `randomize_state` guarantees a USABLE state: source_mode stays "demo", upload stays None, allowed_interactions non-empty regardless of mode (mode governs USE, decided Phase 2/4)
- Non-dict input to `validate_state` is treated as `{}` (defaults-filled) rather than crashing -- hand-edited `data` payloads degrade gracefully, consistent with the no-checksum hand-editable-files design
- JSON `null` counts as missing for str-coerced fields (`demo_set_id: null` -> `""`) instead of the string "None"

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical, minor] Non-dict input guard in validate_state**
- **Found during:** GREEN (writing validate_state)
- **Issue:** plan's `<behavior>` specifies dict inputs only; a hand-edited container with a non-dict `data` payload (e.g. `"data": "oops"`) would reach validate_state via load_setup_file and crash with AttributeError instead of a usable state
- **Fix:** `if not isinstance(state, dict): state = {}` at the top of validate_state (fills from DEFAULTS), documented in the docstring
- **Files modified:** aamatch/setup_state.py
- **Verification:** covered by the design; no dedicated test added (no refusal semantics specified for this case -- it is tolerance, not a refusal)
- **Committed in:** 6994a41

---

**Total deviations:** 1 auto-fixed (1 missing-critical, minor defensive guard)
**Impact on plan:** One-line defensive guard; no scope creep. All 13 planned test cases implemented as specified (plus test-elaboration sub-assertions within the planned behaviors).

## Issues Encountered
None - RED failed exactly as predicted (ImportError on the not-yet-existing wrappers), GREEN passed on the first run.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 01-06 (level_spec, same wave) can proceed: persistence.py container core is untouched and its setup wrappers are additive; `tests/__init__.py` untouched
- Phase 2 generator can consume `demo_set_id` / `molecules_per_level` / `difficulty_levels` from validated setup states; Phase 4 GUI implements collect/apply over this same model
- Open for later phases: manifest membership of demo_set_id (Phase 2/8), upload portability semantics (Phase 4, OQ3), interaction-mode semantics (Phase 2/4)
- Numeric defaults (2/1/10, 3/1/9, mode "unset") await human confirmation at the 01-09 checkpoint

---
*Phase: 01-bootstrap-pure-foundation*
*Completed: 2026-09-05*
