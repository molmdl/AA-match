---
phase: 01-bootstrap-pure-foundation
plan: 06
subsystem: persistence
tags: [level-spec, schema, versioning, validation, tdd, python-3.6, stdlib-only]

# Dependency graph
requires:
  - phase: 01-bootstrap-pure-foundation (01-01)
    provides: aamatch package skeleton with lazy-import __init__ (zero-stub test prerequisite)
  - phase: 01-bootstrap-pure-foundation (01-02)
    provides: persistence versioned-container core (check_container / make_container / FormatError / atomic JSON I/O)
provides:
  - "DETECTOR_VERSION = 'det-1' + LEVEL_SPEC_VERSION = 1 constants"
  - "parse_level_spec_dict: container gate -> format_version refuse-newer -> detector_version exact-match -> structural minimums"
  - "make_level_spec_container convenience re-export for Phase-2 generators/tests"
  - "RESERVED level-spec payload shape documented in module docstring (R5 verbatim)"
affects: [02-headless-game-engine (generator/detector stamp specs), 03-wizard-gameplay (reset/replay), 07-checkpoint-persistence (game files), detector-version gate policy users (DETECT-05)]

# Tech tracking
tech-stack:
  added: [none]
  patterns:
    - "Two-policy version gating: payload format_version refuse-newer/accept-older vs detector_version EXACT-match (both directions refused) with distinct refusal messages (P4)"
    - "Passthrough validation: unknown keys preserved, never stripped (P9); input never mutated (P6)"
    - "Malformed payloads -> FormatError with message naming the failing gate (never TypeError/AttributeError crashes)"

key-files:
  created:
    - aamatch/level_spec.py
    - tests/test_level_spec.py
  modified: []

key-decisions:
  - "detector_version gate is EXACT-match (stale AND newer refused) with a dedicated 'stale or newer' message -- deliberately distinct from the format gate's 'unsupported level spec version ... Please update' wording; a dedicated test asserts the two messages differ"
  - "seed must be present AND a real int; bools excluded (isinstance(int) minus bool) -- '42'/42.5/None/True all refused (H12 deterministic replay)"
  - "parse_level_spec_dict takes a FULL container dict (check_container gate) and returns the payload 'data' dict itself (passthrough), mirroring load_container's return-data convention"
  - "can_form members are NOT validated against setup_state's interaction enum -- independent schemas (R1); Phase-2 generator guarantees consistency"
  - "slot_id uniqueness enforced per MOLECULE (same id across different molecules accepted); unhashable slot_id refused with a clear message instead of a TypeError"

# Metrics
duration: 3 min
completed: 2026-09-05
---

# Phase 1 Plan 6: Level-Spec Schema + detector_version Exact-Match Gate Summary

**Reserved level-spec schema with a two-policy version gate pair: payload format_version refuse-newer/accept-older vs detector_version exact-match (stale AND newer both refused, distinct messages), plus structural minimums, required int seed, and unknown-key passthrough -- 20 TDD tests, 84/84 suite green, stdlib-only.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-09-05T16:29:55Z
- **Completed:** 2026-09-05T16:33:02Z
- **Tasks:** 1 feature (RED -> GREEN -> REFACTOR cycle)
- **Files modified:** 2 created

## Accomplishments
- Schema reserved once for Phases 2/3/7: constants, container wiring (kind='level_spec' via persistence.check_container), R5 payload shape documented verbatim in the module docstring
- The P4 regression trap is covered by tests: a newer detector stamp (det-2) is REFUSED -- refuse-newer-only would wrongly accept it; the two gates produce provably distinct refusal messages
- Structural minimums enforced with clear gate-naming messages: non-empty levels, difficulty.grid_n >= 1, grid.n >= 1, unique slot_id per molecule; seed required (present + int)
- Unknown keys preserved at every nesting level (payload, level, slot, grid_pose) -- Phase 3/7 additive extensions survive a Phase-1-era reader

## Task Commits

Each TDD phase was committed atomically:

1. **RED: failing tests** - `4a5c32c` (test) -- 20 tests across 6 classes, all failing with ModuleNotFoundError
2. **GREEN: implementation** - `5313497` (feat) -- aamatch/level_spec.py, all 20 tests pass on first run
3. **REFACTOR** - skipped: no changes warranted (code already minimal; gate chain linear, helpers single-purpose, conventions match persistence.py)

**Plan metadata:** (this commit)

_Note: TDD tasks may have multiple commits (test -> feat -> refactor)_

## Files Created/Modified
- `aamatch/level_spec.py` - RESERVED level-spec schema: DETECTOR_VERSION/LEVEL_SPEC_VERSION constants, parse_level_spec_dict gate chain, make_level_spec_container re-export (214 lines, pure stdlib+persistence)
- `tests/test_level_spec.py` - RED-first suite: 20 tests covering all 14 planned behavior cases + 3 robustness enrichments (310 lines)

## Decisions Made
- **Detector message wording:** "unsupported detector_version %r in level spec (expected %r): stale or newer game spec - regenerate it with a current AA-match generator" -- anchors PITFALLS.md:280's "regenerate" guidance; the test suite asserts 'stale or newer' appears in BOTH detector refusals and in NEITHER format refusal
- **Seed strictness:** presence AND int type enforced (cases 13-14); True refused despite being an int subclass (a boolean seed is never a valid RNG seed)
- **Parse API shape:** container in, payload out -- parse validates via check_container then returns `data` unchanged; round-trip test proves save_container(path, 'level_spec', spec) -> read_json_file -> parse == spec
- **Defensive type gates:** payload/difficulty/molecules/grid/slots type violations and unhashable slot_ids raise FormatError naming the failing field instead of crashing with TypeError/AttributeError

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Defensive type gates on structural traversal**

- **Found during:** Task GREEN (implementation)
- **Issue:** The plan enumerates structural minimums (levels non-empty, grid_n/n >= 1, unique slot ids) but iterating malformed payloads (molecules=None, grid missing, unhashable slot_id) would crash with TypeError/AttributeError instead of the module's clear-refusal contract
- **Fix:** Each traversal step type-checks its node and raises FormatError naming the failing field; unhashable slot_id caught via TypeError -> FormatError
- **Files modified:** aamatch/level_spec.py
- **Verification:** full discover 84/84 green; malformed-input paths exercised by tests 8-10
- **Committed in:** 5313497 (GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Defensive gates implement the module's stated contract ("Raises FormatError naming the failing gate") for inputs the plan's case list didn't enumerate. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Level-spec schema reserved and gated: Phase 2 (generator/detector) can stamp specs via make_level_spec_container + DETECTOR_VERSION; Phase 3 replay and Phase 7 game files extend additively (unknown keys survive)
- The detector gate is the enforcement half of DETECT-05's stale-game refusal -- Phase 2's detector only needs to keep the stamp in sync when thresholds change
- All 84 suite tests green under bare python3.6 stdlib (no stubs); py_compile clean

---
*Phase: 01-bootstrap-pure-foundation*
*Completed: 2026-09-05*
