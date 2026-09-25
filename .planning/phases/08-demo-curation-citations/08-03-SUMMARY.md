---
phase: 08-demo-curation-citations
plan: 03
subsystem: testing
tags: [smoke-suite, manifest, de-hardcoding, perf-budget, phase-8]

requires:
  - phase: 02-headless-game-engine
    provides: smoke_02 manifest-parse loop, smoke_03 generation smoke (02-13 benzamide restriction law), smoke_05 DETECT-05 perf battery on largest_entry
  - phase: 08-demo-curation-citations
    provides: 08-RESEARCH-mechanics Q6 table — the manifest-growth-sensitive literals map
provides:
  - Manifest-growth-proof smokes: smoke_02/03 use `len(entries) >= 2`; smoke_05 selects the perf target by max-heavy cross-check only (no name literal)
  - Proof that all three pass on the current dev-only manifest with zero behavior change
affects: [08-05 curated set 1, 08-06 curated set 2, 08-07 curated set 3, 08-08 regression battery, phase-8 verifier]

tech-stack:
  added: []
  patterns:
    - "Data-relative smoke assertions: entry counts are floors (>= 2), largest-entry selection is a max-heavy cross-check only — never name literals or absolute counts"

key-files:
  created: []
  modified:
    - smoke/smoke_02_manifest.py
    - smoke/smoke_03_generate.py
    - smoke/smoke_05_perf.py

key-decisions:
  - "Entry-count checks are floor assertions (>= 2): the manifest grows additively through Phase 8 curation; the anti-drift proof stays in smoke_02's per-entry loop and smoke_03's benzamide-row candidate restriction (02-13 seed-robustness law), not in any absolute count"
  - "smoke_05's perf target is the largest entry BY DATA (largest_entry + max-heavy cross-check): DETECT-05 targets the largest bundled molecule whatever its name; the Phase-8 expectation (medium aromatic ligand, NAD/heme class) is recorded as a comment with the feature-extraction fail-close note"

patterns-established:
  - "Pre-curation smoke hardening: before any curated set lands, re-audit smokes that touch MANIFEST.json for growth-sensitive literals (counts, names) and convert them to data-relative forms proven green on the dev-only tree"

duration: ~7 min
completed: 2026-09-25
---

# Phase 8 Plan 03: Smoke De-hardcoding Summary

**The three smokes that touch MANIFEST.json (02, 03, 05) are now manifest-growth-proof — entry counts are floor assertions and the perf target is selected by data (max-heavy cross-check), not by the literal name 'benzamide' — and all three still PASS headless on the current dev-only tree with zero behavior change.**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-09-25T17:43:27Z
- **Completed:** 2026-09-25T17:50Z
- **Tasks:** 3/3
- **Files modified:** 3 (smoke scripts only; zero production code touched)

## Accomplishments

- **smoke_02_manifest.py + smoke_03_generate.py:** `len(entries) == 2` → `len(entries) >= 2` (same check name + detail format). smoke_03's benzamide candidate restriction (row filter by entry_id) intentionally KEPT — it is already manifest-growth-proof per the research (block_exclusive refuses checked-but-unsupported types on aromatic-less molecules; 02-13 seed-robustness law).
- **smoke_05_perf.py:** the `biggest['entry_id'] == 'benzamide'` literal term removed; the check is now `biggest is not None and biggest['heavy_atom_count'] == max(row['heavy_atom_count'] for row in entries)` — largest_entry semantics proven purely by data. Comment records the Phase-8 expectation (largest entry = medium aromatic ligand, NAD/heme class) and the fail-close note (feature extraction at ~line 259 fails visibly if a future largest entry lacks a ligand ring).
- **Proof run (Task 3):** SMOKE-02 PASS (manifest parse entries=2, 18 checks), SMOKE-03 PASS (26 checks), SMOKE-05 PASS (21 checks, TIMEOUT 180; target=benzamide heavy=9 of 2 entries selected data-relatively; extract 20.7 ms + detect 20.2 ms vs budgets 100/1000 ms). Full WSL suite 890/890 green incl. purity gates.

## Task Commits

Each task was committed atomically on branch `exec/08-03` (worktree `tmp/exec-08-03`):

1. **Task 1: smoke_02 + smoke_03 entry-count literals → data-relative** — `38922bb` (fix)
2. **Task 2: smoke_05 largest-entry literal → data-relative** — `7359790` (fix)
3. **Task 3: prove all three smokes green on the current tree** — `1892e79` (test; explicitly-requested empty commit — zero fixes were needed, the commit records the proof verdicts)

**Plan metadata:** recorded below (docs: complete smoke de-hardcoding plan).

## Files Created/Modified

- `smoke/smoke_02_manifest.py` — manifest-parse check: entry count is now a floor (`>= 2`) with rationale comment.
- `smoke/smoke_03_generate.py` — same floor change; benzamide-row candidate restriction and all other lines untouched.
- `smoke/smoke_05_perf.py` — largest_entry check: name literal removed, max-heavy cross-check retained, Phase-8 expectation + fail-close comment added.

## Decisions Made

- Entry-count checks are **floor assertions** (`>= 2`), and the anti-drift weight stays in the per-entry loops and smoke_03's benzamide-row restriction — the absolute count was the drift trap, not the proof (plan rationale inline-commented in both files).
- smoke_05's perf target stays **largest-entry-by-data**: the max-heavy cross-check alone proves `largest_entry` semantics, which is exactly what DETECT-05 needs (the largest bundled molecule whatever its name). The Phase-8 manifest expectation (aromatic medium ligand so the pi_stacking block_exclusive game stays solvable) is recorded as a comment alongside the fail-close note.

## Deviations from Plan

None — plan executed exactly as written. All three smokes passed on first run post-edit; no Rule-1/2/3 fixes were triggered, no Rule-4 decision needed.

## Issues Encountered

None. (One note: the plan's Task-3 verify recipe `bash smoke/run_smoke.sh smoke/smoke_05_perf.py 180` passes the tier-9 grid battery TIMEOUT as the second argument per the 02-04 run_smoke.sh generalization — honored.)

## Authentication Gates

None — no external services involved.

## Next Phase Readiness

- **08-05..08-07 (curated sets 1-3):** SMOKE-02 per-set re-runs can no longer false-fail on entry-count growth; SMOKE-05's perf target follows the largest entry by data automatically.
- **Watch-item for curation:** if the future largest entry is NOT aromatic, smoke_05's pi_stacking block_exclusive game construction (~line 205) will fail visibly — the comment at the largest_entry check documents this expectation; revisit the perf scenario in that event rather than re-hardcoding a name.
- Zero blockers; no open concerns.

**Suggested next step:** proceed with the curation-content plans (08-05+) — the smoke machinery is now growth-proof.
