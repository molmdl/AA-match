---
phase: 02-headless-game-engine
plan: 01
subsystem: detection-chem
tags: [detect-03, gate, thresholds, plip, prolif, binana, hydrogen-bond, pi-stacking, halogen-bond, metal-coordination, capability-table, DETECTOR_VERSION]

# Dependency graph
requires:
  - phase: 01-bootstrap-pure-foundation
    provides: detector_version exact-match gate (aamatch/level_spec.py), FORMAT_VERSION container gate, purity enforcement (tests/test_purity.py), verified research corpus (02-RESEARCH-*.md)
provides:
  - Human-approved DETECT-03 gate document (docs/DETECTION_THRESHOLDS.md): 10 threshold rows, 20-AA capability table, policy decisions D1–D4 + OQ-1/4/5/7, approval record
  - Frozen transcription source for plans 02-05 (capability.py), 02-06 (thresholds.py/detector), 02-07 (detector), 02-08 (generator mode semantics), 02-10 (score 'any' semantics)
  - DETECTOR_VERSION bump policy for any threshold/typing change
affects: [02-02 capability module, 02-03..02-04 pure-layer plans, 02-05..02-08 detector/generator implementation, 02-10 scoring, phase 3 wizard, phase 8 dataset curation (provisional revisit), phase 9 docs]

# Tech tracking
tech-stack:
  added: [] # docs-only plan; zero libraries
  patterns:
    - "Gate-before-code: human approval recorded in-repo before any detector implementation freezes"
    - "Per-row approval provenance: each threshold row carries date + approver"
    - "Provisional approval pattern: revisit = DETECTOR_VERSION bump event, never a silent edit"

key-files:
  created:
    - docs/DETECTION_THRESHOLDS.md
  modified: []

key-decisions:
  - "DETECT-03 [GATE] APPROVED 2026-09-06 (human gate, phase-2 plan 02-01 checkpoint) — provisional: revisit if the Phase-8 curated dataset requires it (DETECTOR_VERSION bump event)"
  - "Units + atom-typing verified at approval: every distance in Å, every angle in degrees, element sets exact; NO adopted value changed"
  - "H-bond = BINANA pair 4.0 Å / ≥140°; salt bridge 5.5 Å group-center; π-stacking PLIP set 5.5 Å/30°/2.0 Å one-category; cation-π 6.0 Å + 2.0 Å offset with PLIP ligand-side anti-artifact rule (OQ-4)"
  - "Halogen donors ligand-side only, X ∈ {Cl, Br, I}, C-F EXCLUDED (ProLIF precedent supersedes research draft row 6)"
  - "Metal coordination 3.0 Å distance-only; metal list v1 = {MG, ZN, FE, CA, MN, CU, NI, CO, CD} [OQ-7]"
  - "His = neutral in v1 (not a salt-bridge cation) [OQ-3/D2]; hydrophobic pedagogical set = ALA VAL LEU ILE PRO PHE MET TRP (Kyte & Doolittle 1982); D1 side-chain-only; OQ-1 mode semantics frozen (exclusive = 'any' scoped by allowed_interactions)"
  - "itertools NOT added to ALLOWED_STDLIB (purity convention); single typing home = aamatch/capability.py (DETECT-04 by construction)"

patterns-established:
  - "Per-row Approval lines in gate documents (date + approver, grep-verifiable)"
  - "Deviation-from-research rows recorded verbatim in the gate doc (Met thioether-S acceptor, Asp/Glu metal chelator, C-F halogen donor)"

# Metrics
duration: ~35 min total (Task 1 prior segment; Task 2 continuation ~25 min: verification pass + approval recording)
completed: 2026-09-06
---

# Phase 2 Plan 01: Detection Threshold Gate Summary

**DETECT-03 [GATE] approved 2026-09-06: docs/DETECTION_THRESHOLDS.md frozen with 10 threshold rows + 20-AA capability table, units/atom-typing verified, provisional pending Phase-8 dataset revisit**

## Performance

- **Duration:** ~35 min across two segments (Task 1 in the checkpoint-blocking session; Task 2 in this continuation)
- **Started:** 2026-09-06 (Task 1 commit 15:59 +08:00)
- **Completed:** 2026-09-06T08:43Z
- **Tasks:** 2/2 (plus resolved checkpoint:human-verify)
- **Files modified:** 1 (docs/DETECTION_THRESHOLDS.md; zero .py files by design)

## Accomplishments

- Wrote the DETECT-03 gate document: verified sources (§1 with 4 DOIs), 10 threshold rows each with source + rationale + rejected alternatives (§2), BINANA charge-group table (§2.3), documented not-adopted deviations (§2.4), 20-AA × 7-type capability table with per-cell provenance marks [V-SRC]/[RESOLVE]/[HUMAN] (§3), 7 policy decisions (§4), chemistry policy summary (§5).
- Human checkpoint (DETECT-03 [GATE]) resolved: **approved with the condition that units and atom typing be verified** — the condition was satisfied before recording.
- Units + atom-typing verification pass executed: every distance criterion now explicitly in Ångström, every angle explicitly in degrees (12 additive unit clarifications across source/rationale lines: rows 1–3, 4, 5, 6, 7, 10 and §1.3's `DHA_angle = (130, 180)` — degrees); atom-typing element sets confirmed exact (H-bond O/N/S fail-closed, halogen donors {Cl, Br, I} w/ C-F excluded, metal list {MG, ZN, FE, CA, MN, CU, NI, CO, CD}, hydrophobe carbon rule, ring-atom rules). **No adopted value changed**; all values cross-checked against 02-RESEARCH-detection.md §3 — no contradiction.
- Approval recorded: all 11 `Approval:` lines filled (10 threshold rows + capability table as a whole) + §6 Approval record with date, approver, freeze statement, verification note, and the provisional-scope caveat.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write the threshold + capability + policy document** — `e25e428` (docs)
2. **Task 2: Record the approval** (units + atom-typing verified first) — `7214d66` (docs)

**Plan metadata:** (this commit) docs(02-01): complete threshold + capability gate plan

## Files Created/Modified

- `docs/DETECTION_THRESHOLDS.md` — the DETECT-03 [GATE] document (~505 lines): approved threshold table (10 rows), charge-group table, AA capability table, policy decisions D1–D4 + OQ-1/4/5/7 + purity convention + bump policy, chemistry policy summary, §6 Approval record

## Decisions Made

All decisions were transcriptions of the research + plan, approved by the human at the checkpoint. The recorded resolutions (approved):

- **Met thioether-S as H-bond acceptor: EXCLUDED in v1** — recorded DETECT-03 disagreement (BINANA "S atoms can act as acceptors" vs ProLIF SMARTS with no aliphatic S; research had recommended INCLUDE-marked-weak). Revisit only as a versioned capability-table change.
- **Asp/Glu carboxylate O as H-bond acceptor: INCLUDED** (BINANA's verified O/N/S rule supersedes the research draft's protonation-dependent "—"), and **Asp/Gln/Glu/His metal-chelator: INCLUDED** (BINANA N/O/S rule beats PLIP's list omissions); Cys(S) metal INCLUDED per PLIP+BINANA; Met thioether metal EXCLUDED.
- **C-F halogen-bond donors: EXCLUDED** (ProLIF's Auffinger-based donor pattern supersedes the research draft's X ∈ {F, Cl, Br, I}).
- **H-bond = 4.0 Å / ≥ 140°** (BINANA pair), salt bridge 5.5 Å group-center, π-stacking one-category PLIP set (5.5 Å / 30° / 2.0 Å), cation-π 6.0 Å + 2.0 Å offset (OQ-4 asymmetric rule), metal 3.0 Å distance-only with the 9-element list [OQ-7], ring-ID 15° fallback, MIN_DIST 0.5 Å.
- **Provisional approval recorded:** the human approved "for now" with the explicit caveat that values may need adjustment depending on the final curated dataset (Phase 8). Such a revisit is a **DETECTOR_VERSION bump event, never a silent edit** (recorded in §6).

## Deviations from Plan

**None from the plan itself** — executed exactly as written (Task 1 → checkpoint → Task 2). The units/atom-typing verification pass was a resume-instruction addition (the human's approval condition); it changed only explicit unit labels, zero values.

### Deviations from research (recorded in the gate document, per plan design)

These are the plan's own recorded resolutions, not execution deviations:

1. Met thioether-S H-bond acceptor → EXCLUDED in v1 (research draft cell "—", recommended INCLUDE-marked-weak)
2. Asp/Glu carboxylate acceptors → INCLUDED (research draft cells "—")
3. C-F halogen donors → EXCLUDED (research draft row 6 listed X ∈ {F, Cl, Br, I})

## Issues Encountered

None — verification suite stayed green throughout (114/114 tests, py_compile clean).

## Authentication Gates

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- **DETECT-03 [GATE] is CLOSED.** Plans 02-05 (capability.py), 02-06 (thresholds.py + detector), 02-07, 02-08 (generator mode semantics) may now freeze their constants against this document, row by row.
- Every transcription must cite the row it came from; any doc-vs-code divergence is a bug (§4.7).
- The capability-table resolutions bind 02-05's typing tables: h_bond acceptor set {ASN, ASP, CYS, GLN, GLU, HIS, SER, THR, TYR} (9), donor set (10), salt_bridge {LYS, ARG | ASP, GLU}, π {PHE, TYR, HIS, TRP}, cation-π 6 AAs either-direction, hydrophobic 8 (residue-name-based AA-side), halogen acceptors 9, metal chelators 9.
- Reminder for 02-06/07: metal coordination runs only when `ligand_has_metal` (ligand-side element ∈ the 9-element list).

---
*Phase: 02-headless-game-engine*
*Completed: 2026-09-06*
