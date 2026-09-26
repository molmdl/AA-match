---
phase: 08-demo-curation-citations
plan: 09
subsystem: demo-data
tags: [demo-curation, data-sources, citations, licenses, pubchem, wwpdb,
  cc0, doi, plip, provenance, gate-doc, python3.6]

# Dependency graph
requires:
  - phase: 08-demo-curation-citations
    provides: 08-01 bundling pipeline (scripts/build_demos.py --report-only
      row printer), 08-04 [GATE] APPROVED 2026-09-26 proposal + U1-U4
      resolutions (incl. canonical PubChem citation doi:10.1093/nar/gkae1059
      from the human-verified citation-guidelines page), 08-05..08-07
      committed specs + MANIFEST.json (10 sets / 18 entries), 08-RESEARCH-
      sourcing (RQ5 verbatim policy quotes, RQ7 ratified policy, RQ9 skeleton)
provides:
  - docs/DATA_SOURCES.md — the HELP-02 dedicated sources document in
    gate-doc format (258 lines): header with last-verified date +
    verification protocol; §1 sources & licenses with verbatim wwPDB CC0
    1.0 / NCBI public-domain / PubChem FTP Fair Use quotes + URLs/fetch
    dates + database citations (Berman 2000, wwPDB 2018, PubChem 2025
    gkae1059, PUG-REST gky294, PLIP 2025, ChEBI Malik 2025 recorded as
    consulted-not-used); §2 ten set sections in dropdown tier order
    (3 easy, 3 hard, 1 challenge, 2 very_challenging, dev set last marked
    as development fixture with license '' placeholder-by-design) with
    per-entry rows (fetch URL, CID/CCD, PDB complex + entry DOI + paper
    DOI incl. honest absences 8FUY/1S0R/9NDX/1MBN, PLIP ref, protonation
    why, halogen/metal, sha256, fetched date); §3 ratified RQ7 multi-state
    & ions policy; §4 not-bundled acknowledgements (DrugBank CC BY-NC
    informational-only, PDBsum unavailable verbatim quote, context
    complexes not shipped with 1OXR as the real-world analog)
  - Zero-MISSING coverage: all 18 bundled SDF filenames appear in the doc;
    set-level license strings match MANIFEST.json verbatim
affects: [08-11 [HUMAN] checkpoint (DATA_SOURCES.md sign-off is ROADMAP
  phase-8 criterion 3), Phase 9 (DOCS-02 audit consumes this document
  alongside README/help)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gate-doc register: every factual claim carries a fetched URL + date;
      rows are machine-reproducible from specs via build_demos.py
      --report-only, never a hand-maintained orphan"
    - "Honest-absence convention: '— (none recorded in the RCSB data —
      honest absence)' instead of invented paper DOIs"

key-files:
  created: [docs/DATA_SOURCES.md]
  modified: []

key-decisions:
  - "PubChem canonical citation included (gkae1059) — plan's condition met:
    08-04 U1/U3 recorded it VERIFIED from the human-verified
    citation-guidelines page; PUG-REST citation (gky294) recorded for the
    fetch-dates columns"
  - "ChEBI citation recorded as consulted-NOT-used (deprotonated-citrate
    sourcing rejected per approved Decision 5) — truthful rather than
    silently omitted"

patterns-established:
  - "Per-set cross-ref law restated in doc: counts/sha256 pinned in
    MANIFEST.json; regenerate via build_demos.py --spec ... --fetch, never
    hand-edit an SDF or the manifest (02-04 law)"

# Metrics
duration: ~16min
completed: 2026-09-26
---

# Phase 8 Plan 09: DATA_SOURCES.md (HELP-02) Summary

**HELP-02's dedicated sources document written from the approved proposal + committed
specs (`--report-only` rows): every one of the 18 bundled ligand files covered with fetch
URL, CID/CCD, PDB complex + entry DOI + paper DOI (honest absences marked), PLIP
provenance, protonation why, license permitting redistribution, sha256 and fetch date —
plus verbatim wwPDB CC0 / NCBI public-domain policy quotes and the GATE-verified PubChem
canonical citation.**

## Performance

- **Duration:** ~16 min
- **Started:** 2026-09-26T15:07:11Z
- **Completed:** 2026-09-26T15:23:34Z
- **Tasks:** 2/2 completed
- **Files created:** 1 (`docs/DATA_SOURCES.md`, 258 lines)

## Accomplishments

- `docs/DATA_SOURCES.md` exists in the DETECTION_THRESHOLDS.md gate-doc register:
  verification-protocol header, verbatim policy quotes with URLs + fetch dates, and every
  factual claim carrying its verification provenance (ROADMAP phase-8 criterion 3's
  [HUMAN] sign-off is deferred to 08-11 by design).
- Coverage audit: all 18 bundled SDF filenames (16 curated + 2 dev) appear in the doc —
  zero MISSING in the mechanical loop; set-level license strings (`Public domain (NCBI
  PubChem)` ×8, `CC0 1.0 (wwPDB)` ×1, `''` dev) match MANIFEST.json verbatim.
- Paper-DOI honesty preserved: 8FUY (citric acid), 1S0R (benzamidine), 9NDX (quinine),
  1MBN (heme) carry explicit "none recorded in the RCSB data — honest absence" markers
  (U2 6-vs-7 note from 08-04 honored — the recorded 403-blocked set is transcribed, not
  "resolved" silently).
- DOI spot-checks 2026-09-26: 3 samples across 3 sets all HTTP 200 at doi.org — entry DOI
  `10.2210/pdb1oxr/pdb`, paper DOIs `10.1016/j.chembiol.2017.08.021` (5NWQ/hard-1) and
  `10.1016/j.str.2016.08.010` (5IT5/hard-3); the sampling date is recorded in the doc
  header.
- WSL suite green: 906/906 tests OK (docs-only change; standing gate runs anyway).

## Task Commits

Each task was committed atomically (worktree branch `exec/08-09`):

1. **Task 1: generate docs/DATA_SOURCES.md per the RQ9 skeleton** - `3d4f861` (docs)
2. **Task 2: coverage audit + DOI spot-checks** - `88007d2` (docs) — commit message per
   plan: `docs(08-09): add DATA_SOURCES.md (per-file provenance, licenses, policy quotes)`

**Plan metadata:** (this SUMMARY + STATE.md update committed below)

## Files Created/Modified

- `docs/DATA_SOURCES.md` — the HELP-02 sources document (header + §1 sources & licenses +
  §2 ten tier-ordered set sections + §3 multi-state & ions policy + §4 not-bundled
  acknowledgements); source rows reproduce via `python3.6 scripts/build_demos.py
  --report-only`.

## Doc section inventory

- Header: last-verified/provenance protocol + GATE approval pointer + DOI spot-check record
- §1 Sources & licenses: PubChem (NCBI policies + FTP Fair Use, 2 verbatim quotes),
  wwPDB/RCSB CC0 1.0 (verbatim); database citations incl. PubChem 2025 gkae1059 (U1/U3
  canonical) + PUG-REST gky294; per-record CID URL citation format; PDBe secondary
  provenance (U4)
- §2 Demo sets: demo-easy-1/2/3, demo-hard-1/2/3, demo-challenge-1, demo-veryhard-1/2,
  demo-dev-1 (last, development fixture, license '' placeholder-by-design) — one row per
  bundled file (18)
- §3 Multi-state & ions policy (ratified RQ7 / Decision 1)
- §4 Not-bundled acknowledgements: DrugBank CC BY-NC (informational only), PDBsum
  unavailable (verbatim quote), context complexes not shipped (1OXR analog)

## Decisions Made

- PubChem canonical citation **included** (plan's conditional): 08-04 recorded it VERIFIED
  via the U1 resolution — quoted exactly as fetched from the citation-guidelines page
  (doi:10.1093/nar/gkae1059), plus the PUG-REST service citation.
- ChEBI citation listed as **consulted, not a bundled source** (truthful completeness; the
  only ChEBI-derivative route was rejected by approved Decision 5).
- Heme's charge delta narrative (derived −4 vs proposal's 'charge field 0' parenthetical)
  carried into the row's protonation/why cell, per the 08-07 honesty law.

## Deviations from Plan

None — plan executed exactly as written (deviation rules 1-3: zero fired; no Rule-4
architectural question).

## Next Phase Readiness

- 08-11 [HUMAN] checkpoint: DATA_SOURCES.md sign-off is on its checklist (ROADMAP
  criterion 3); the doc is ready for review.
- No blockers, no concerns; document is regenerable (specs + `--report-only`), so any
  post-08-10/08-11 supply or provenance change regenerates rows rather than hand-editing.
