---
phase: 02-headless-game-engine
plan: 03
subsystem: pure-layer-data
tags: [manifest, persistence, container-kind, sha256, schema-validation, refuse-newer, purity, TDD, GEN-02, PITFALL-11.3]

# Dependency graph
requires:
  - phase: 01-bootstrap-pure-foundation
    provides: versioned-container discipline (persistence.check_container canonical refusals, refuse-newer/accept-older policy), FormatError, the _is_int bool-refusing pattern (level_spec.py), enforced purity gates (tests/test_purity.py PURE_MODULES)
  - phase: 02-headless-game-engine (02-01)
    provides: approved flag semantics — metal list {MG,ZN,FE,CA,MN,CU,NI,CO,CD}, halogen donors {Cl,Br,I} C-F excluded (documented context for metal_present/halogen_present)
  - phase: 02-headless-game-engine (02-RESEARCH-materialization §3.2)
    provides: the verbatim manifest entry schema this module validates
provides:
  - aamatch/manifest.py (PURE): MANIFEST_VERSION, parse_manifest_dict (passthrough P9 / no-mutation P6), enumerate_entries (deterministic flat rows sorted by set_id, entry_id), largest_entry (max heavy_atom_count, ties first — DETECT-05 perf-smoke selector)
  - 'manifest' as a first-class persistence container kind (KINDS additive; refusal messages still built dynamically from KINDS)
  - Full entry-schema validation: 14 required keys, format/sha256/count/bond_order_counts/formal_charge_sum/size_class/flag rules, forward-slash package-relative 'file' enforcement (PITFALL 2)
  - Contract surface for 02-04 (aamatch/data/MANIFEST.json must satisfy THIS schema; SMOKE-02 asserts its counts) and 02-08 (generator consumes enumerate_entries as candidate list)
affects: [02-04 MANIFEST.json + SMOKE-02, 02-08 generator candidates, 02-09 geometry bridge, DETECT-05 perf smoke (largest_entry), phase 8 dataset curation]

# Tech tracking
tech-stack:
  added: [] # stdlib-only; no new libraries
  patterns:
    - "Pure payload-validator module: container in (dict), payload out unchanged — file I/O stays caller/cmd-tier (manifest.py never touches disk, never imports paths)"
    - "Refusal messages name set + entry index + entry_id + offending field"
    - "Kind extension is additive: KINDS tuple grows, check_container messages need no edits"
    - "Phase-2 TDD module pattern (from 02-02): RED test commit → GREEN feat commit → PURE_MODULES registration test commit"

key-files:
  created:
    - aamatch/manifest.py
    - tests/test_manifest.py
  modified:
    - aamatch/persistence.py
    - tests/test_persistence.py
    - tests/test_purity.py

key-decisions:
  - "manifest_version gate uses the strict _is_int pattern (bool refused), not the container-gate's int() coercion — missing/bool/non-int all refused as 'unsupported manifest version None/True/... (expected <= 1)'; refuse-newer/accept-older preserved (older accepted, newer refused with 'Please update AA-match')"
  - "Set-level structure validation added (sets must be a list; set must be a dict; set_id non-empty string; entries a list) and entry_id/set_id must be non-empty strings — both are the enumerate_entries sort keys, so non-strings would break deterministic sorting (TypeError) rather than merely look odd"
  - "Empty sets list allowed (no refusal): an empty manifest is valid data-side; candidate-supply emptiness is the generator's concern, not a structural fault"
  - "'file' path validation is char-based, no re import: backslash refused, leading '/' refused, 'X:'-style drive prefix refused (PITFALL 2 — manifest never stores Windows or absolute paths; cmd tier resolves via paths.package_data_path)"
  - "largest_entry returns None for an empty list and preserves identity (returns the actual entry object) for ties-first in given order — enumerate output order makes this deterministic"
  - "bond_order_counts keys validated as ASCII digit strings via char-set check (str.isdigit() accepts Unicode digits like '²'; isascii() is 3.7+)"

patterns-established:
  - "Manifest entry schema = the contract: counts recorded in MANIFEST.json are exactly what SMOKE-02 asserts (PITFALL 11.3 anti-drift)"
  - "Validation helpers mirror level_spec.py style: plain functions, FormatError with positional context"

# Metrics
duration: 11 min
completed: 2026-09-06
---

# Phase 2 Plan 03: Pure Manifest Module Summary

**Pure manifest module (MANIFEST_VERSION=1, parse/validate/enumerate + largest-entry selector) with 'manifest' added as a first-class container kind — 211/211 tests green, PURE_MODULES=8**

## Performance

- **Duration:** 11 min (08:54:37Z → 09:05:10Z)
- **Started:** 2026-09-06T08:54:37Z
- **Completed:** 2026-09-06T09:05:10Z
- **Tasks:** 3/3
- **Files modified:** 5 (2 created, 3 modified)

## Accomplishments

- `aamatch/manifest.py` (329 lines, PURE): `parse_manifest_dict` reuses `persistence.check_container(container, 'manifest')` for the header gate (canonical foreign/newer/misfiled refusals — zero duplication), then validates `manifest_version` (refuse-newer/accept-older like FORMAT_VERSION) and walks sets → entries against the verbatim §3.2 schema. Payload passthrough (P9), input never mutated (P6), unknown fields preserved.
- Every entry refusal names the set, the entry index, the entry_id, and the offending field — e.g. `manifest set 'demo-easy-1' entry 0 (entry_id='mol-001'): missing required key 'sha256'`.
- `enumerate_entries` produces deterministic flat rows (entry fields + `set_id`, sorted by `(set_id, entry_id)`, new dicts each call); `largest_entry` derives the DETECT-05 perf-smoke target as max `heavy_atom_count` (ties → first in sorted order) with no special-cased manifest field.
- `KINDS` gains `'manifest'` additively; unknown-kind/misfiled canonical messages pinned unchanged; all Phase-1 persistence tests still green.
- Purity gates extended: Gates A/B now scan `manifest` (imports `.persistence` only; dict-level parsing, no file I/O — reading MANIFEST.json stays with the caller/cmd tier). PURE_MODULES = 8.

## Task Commits

Each task was committed atomically (TDD: RED → GREEN per task):

1. **Task 1 RED: failing manifest-kind tests** — `0e6c059` (test)
2. **Task 1 GREEN: add manifest container kind** — `0636d08` (feat)
3. **Task 2 RED: failing parse/validate/enumerate tests** — `8ab01f7` (test)
4. **Task 2 GREEN: manifest parse/validate/enumerate** — `771b71b` (feat; the small REFACTOR — hoisting the `_make_remover` test helper — was folded into this commit as the test-file edit preceded staging)
5. **Task 3: register manifest in purity gate (PURE_MODULES=8)** — `c9629cb` (test)

**Plan metadata:** (this commit) docs(02-03): complete pure manifest module plan

## Files Created/Modified

- `aamatch/manifest.py` — PURE manifest module: MANIFEST_VERSION, parse_manifest_dict, enumerate_entries, largest_entry
- `tests/test_manifest.py` — 48 tests: kind acceptance, container-gate canonical messages, version gate, full entry-schema refusals, set-structure refusals, enumeration determinism, largest-entry selector
- `aamatch/persistence.py` — KINDS += 'manifest' (+ one docstring line; nothing else changed)
- `tests/test_persistence.py` — KINDS pin updated minimally (plan-anticipated)
- `tests/test_purity.py` — PURE_MODULES = 8 (+ manifest)

## Decisions Made

- **manifest_version gate is strict (_is_int, bool refused)** rather than the container header's `int()` coercion — consistent with level_spec's count validation; missing/True/non-int all surface as `unsupported manifest version ... (expected <= 1)`.
- **Set-structure + entry_id/set_id string validation added** (beyond the plan's enumerated list): they are the enumeration sort keys — non-strings would crash `sorted()` with TypeError instead of producing a clear refusal (Rule 2: required for the deterministic-enrollment guarantee).
- **Empty `sets` list accepted** — structural validity only; candidate supply is the generator's concern.
- **'file' validated by char checks, no `re` import**: backslash / leading-`/` / `X:` drive prefix refused at parse time (PITFALL 2).
- **`str.isdigit()` avoided** for bond_order_counts keys (accepts Unicode digits like `'²'`; `isascii()` is 3.7+) — ASCII char-set check instead.
- **Negative `formal_charge_sum` accepted** (acetate −1 is legitimate); only type is enforced, pinned by test.

## Deviations from Plan

### Plan-anticipated updates

**1. Phase-1 KINDS pin updated (explicitly anticipated by Task 1)**
- **Found during:** Task 1 GREEN
- **Issue:** `tests/test_persistence.py::test_constants` pinned the exact KINDS tuple `('setup', 'level_spec', 'game', 'checkpoint')`
- **Fix:** Assertion updated to include `'manifest'` — minimal one-line change, noted here per the plan's instruction
- **Files modified:** tests/test_persistence.py
- **Verification:** tests.test_persistence fully green (all other Phase-1 container behavior untouched)
- **Committed in:** 0636d08

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added set-structure and sort-key validation**
- **Found during:** Task 2 GREEN
- **Issue:** The plan's refusal list covers entry fields, but `enumerate_entries` sorts by `(set_id, entry_id)` — non-string or missing `set_id`/`entry_id` values would raise bare TypeError from `sorted()`, and non-list `sets`/`entries` would break iteration
- **Fix:** `_check_sets`/`_check_set` validate structure; `set_id`/`entry_id` must be non-empty strings; refusal messages carry set/entry context
- **Files modified:** aamatch/manifest.py, tests/test_manifest.py (TestSetStructure + entry_id/set_id tests)
- **Verification:** all 48 manifest tests green
- **Committed in:** 771b71b

---

**Total deviations:** 1 plan-anticipated pin update + 1 Rule 2 auto-add
**Impact on plan:** Both necessary for the plan's own "deterministic enumeration" truth; no scope creep. Schema fidelity preserved verbatim from 02-RESEARCH-materialization.md §3.2.

## Issues Encountered

- One test-assertion fragment corrected during GREEN iteration: the Windows-drive `'file'` refusal message reads "not a Windows drive path" (more precise than the test's initial `'absolute'` fragment); behavior was correct, assertion updated before the GREEN commit. No code change needed.

## Authentication Gates

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **Schema is frozen for 02-04:** `aamatch/data/MANIFEST.json` must satisfy exactly this validation (14 required keys, `'file'` forward-slash package-relative, counts as ints, flags as bools, `manifest_version: 1`). SMOKE-02's assertions (atom_count / bond_count / expanded bond_order_counts / formal_charge_sum / states_expected / sha256 / flags) validate against the SAME numbers recorded in these fields.
- **02-08 generator** consumes `enumerate_entries(payload)` output as its candidate list (rows carry `set_id`).
- **DETECT-05 perf smoke** target = `largest_entry(enumerate_entries(payload))`.
- Watch-item for 02-04: `bond_order_counts` keys must be digit STRINGS (`"1"`, `"2"`) — JSON object keys are strings anyway, but hand-edits must not use e.g. `"1.0"`.
- No blockers carried forward.

---
*Phase: 02-headless-game-engine*
*Completed: 2026-09-06*
