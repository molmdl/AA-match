---
phase: 08-demo-curation-citations
plan: 02
subsystem: ui
tags: [pyqt5, qcombobox, tier-grouping, demo-curation, pure-layer, tdd]

# Dependency graph
requires:
  - phase: 04-qt-setup-window
    provides: setup_form.manifest_sets (pinned flat rows), setup_window
      Qt shell + _populate_demo_sets, smoke_11 offscreen T1b tier
  - phase: 01-bootstrap-pure-foundation
    provides: purity gates (tests/test_purity.py), pure-layer contract
provides:
  - setup_form.TIER_ORDER / TIER_LABELS / manifest_sets_grouped (pure,
    PURE_MODULES member, no new imports)
  - Tier-grouped demo dropdown with QComboBox separators BETWEEN groups
  - _known_demo_set_ids separator-safe helper closing the 'None'-id hazard
  - First-selectable-row fallback for stale saved demo_set_ids
  - Data-relative T1b offscreen proof in smoke_11 (5 new asserts)
affects: [08-04 gate, 08-05..08-13 per-set bundling (multi-group dropdown
  activates automatically), 08-11 human GUI checkpoint, 08-17 regression
  battery]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Tier vocabulary canonicalized east-to-west: TIER_ORDER exact manifest
      tokens ('easy','hard','challenge','very_challenging'); display labels
      'Easy'/'Hard'/'Challenge'/'Very challenging'; unknown/missing tiers
      collapse into ONE trailing 'Other' group"
    - "QComboBox separator discipline: separators inserted BETWEEN groups
      only; separator rows carry NO itemData -- every itemData loop must
      route through a None-skipping helper (_known_demo_set_ids)"
    - "Current-index-never-separator law: popup non-selectability +
      apply_state first-selectable-row fallback keep collect_state/
      _randomize_impl's currentData() reads on data rows"

key-files:
  created: []
  modified:
    - aamatch/setup_form.py
    - aamatch/setup_window.py
    - tests/test_setup_form.py
    - smoke/smoke_11_window.py

key-decisions:
  - "manifest_sets stays byte-identical; grouping lives in a NEW function
    (one manifest_sets call + tier-partition comprehensions) so the pinned
    TestManifestSets battery stays untouched"
  - "setCurrentIndex(0) kept on the populate success path (safe: separators
    only ever appear after >= 1 data rows) but apply_state's stale-id
    fallback now scans for the first SELECTABLE data row"
  - "Single-group manifests (today's dev-only bundle) render byte-identical
    to the old flat list: zero separators by construction"

patterns-established:
  - "08-02 grouping pattern: pure grouping function returns
    [(display_label, rows)]; Qt tier inserts separators at group boundaries
    and keeps set_id in userData; visuals stay in the label text"
  - "Separator hazard closure pattern: None-skipping helper shared by
    production call sites AND the smoke mirror loop (no independent
    str(itemData) loops anywhere)"

# Metrics
duration: 14min
completed: 2026-09-25
---

# Phase 8 Plan 02: Dropdown Tier Grouping Summary

**Demo dropdown groups curated sets by tier via pure `manifest_sets_grouped` + QComboBox separators between groups, with all three separator hazards ('None'-id pollution, stale-id-on-separator fallback, smoke mirror loops) closed and proven offscreen in real headless PyMOL.**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-09-25T17:45:08Z
- **Completed:** 2026-09-25T17:59:28Z
- **Tasks:** 3 (task 3 = verification; its artifact changes rode in tasks 1-2)
- **Files modified:** 4

## Accomplishments

- Pure tier grouping shipped: `TIER_ORDER`/`TIER_LABELS`/`manifest_sets_grouped` in `setup_form.py` (PURE, zero new imports), pinned by a new 6-test `TestManifestSetsGrouped` battery (TIER_ORDER sequence, within-group set_id sort, Other-group collapse, empty-group omission, empty/{} payload, non-dict payload) -- `manifest_sets` byte-identical, its pinned tests untouched.
- Qt side: `_populate_demo_sets` now populates groups with `insertSeparator` BETWEEN groups only; today's dev-only manifest (1 easy set) renders byte-identical to the old flat list (proven headlessly: 1 data row, 0 separators).
- All three separator hazards closed: `_known_demo_set_ids()` (None-skipping) replaced BOTH known_ids sites (~export ~927, ~start ~1003) AND smoke_11's part-G mirror loop; `apply_state`'s stale-id fallback now lands on the first SELECTABLE data row; `collect_state`/`_randomize_impl` carry the current-index-never-separator comment law.
- Verification: SMOKE-11 PASS offscreen (5 new data-relative PART B asserts: data-row count == total group rows, separator count == (groups-1), every None-data row is a flag-disabled separator, known-ids helper purity, findData/currentData round-trip) -- full WSL suite 896/896 green incl. purity gates.

## Task Commits

Each task was committed atomically (TDD task 1 = RED then GREEN):

1. **Task 1 RED: failing TestManifestSetsGrouped** - `7c23e4e` (test)
2. **Task 1 GREEN: pure tier grouping (TIER_ORDER/manifest_sets_grouped)** - `bcc918c` (feat)
3. **Task 2: Qt separators + the three hazard fixes + smoke extension** - `c3b3c58` (feat)
4. **Task 3: offscreen T1b proof** - no new commit (verification-only task; SMOKE-11 PASS on `c3b3c58`)

**Plan metadata:** separate `docs(08-02): complete dropdown tier grouping plan` commit carrying this SUMMARY + STATE.md update.

## Files Created/Modified

- `aamatch/setup_form.py` - `TIER_ORDER`/`TIER_LABELS`/`manifest_sets_grouped` (additive only; `manifest_sets` byte-identical)
- `aamatch/setup_window.py` - grouped `_populate_demo_sets` with `insertSeparator`; new `_known_demo_set_ids`; both known_ids sites rewired; `apply_state` first-selectable-row fallback; two comment laws
- `tests/test_setup_form.py` - `TestManifestSetsGrouped` (6 tests, RED-first)
- `smoke/smoke_11_window.py` - PART B data-relative grouped-population asserts (5 checks); part-G mirror loop uses `_known_demo_set_ids`; docstring updated

## Decisions Made

- Grouping is a NEW pure function consuming `manifest_sets` output; the flat-rows function and its pinned tests stay byte-identical (additive-only evolution of the pure surface).
- Separators are inserted only at group boundaries; index 0 is therefore always a data row, so the populate-time `setCurrentIndex(0)` success path is kept, while the stale-id fallback explicitly scans for the first row whose `itemData` is not None.
- Tier vocabulary fixed as the plan's tokens (`easy|hard|challenge|very_challenging`, display order Easy -> Hard -> Challenge -> Very challenging); out-of-vocabulary tiers land in a trailing 'Other' group -- ratification of the vocabulary itself stays with the 08-04 GATE.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- WSL-side note only: `run_smoke.sh` pipes stdout through `tail -60`, so the new PART B check lines sit above the visible tail; grepping the tee'd `/tmp/smoke_out.txt` showed all 5 new 08-02 asserts PASS with the final `=== SMOKE-11 PASS ===` marker. No code impact.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Grouped dropdown is LIVE for any multi-tier manifest: when 08-05..08-13 land curated sets, separators activate automatically (PART B asserts are data-relative and turn from degenerate-case (1 group, 0 separators) into real multi-group teeth with zero code edits).
- The real-viewer grouped-dropdown visual check remains for the 08-11 [HUMAN] GUI checkpoint (by design; offscreen cannot verify look/feel).
- Tier vocabulary is still pending formal ratification at the 08-04 GATE; the code accepts the recommended tokens plus an 'Other' escape group, so a GATE vocabulary change would be a data-only edit.

---
*Phase: 08-demo-curation-citations*
*Completed: 2026-09-25*
