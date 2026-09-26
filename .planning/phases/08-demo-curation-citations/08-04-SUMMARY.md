---
phase: 08-demo-curation-citations
plan: 04
subsystem: content-curation / citations gate
tags: [pubchem, rcsb-pdb, sdf, citations, gate, human-approval, demo-content]

# Dependency graph
requires:
  - phase: 08-demo-curation-citations (08-01)
    provides: The bundling pipeline (scripts/build_demos.py) — the only sanctioned data write path the approved rows will flow through
  - phase: 08-demo-curation-citations (08-RESEARCH-sourcing / 08-RESEARCH-mechanics)
    provides: The candidate universe + URL patterns this proposal re-verified live
provides:
  - 08-PROPOSALS.md — the APPROVED [GATE] document: 9 set sections, 16 approved candidates + approved alternates, evidence corrections C1–C7, U1–U4 RESOLVED, 10 accepted decision defaults, approval-time atom-count re-verification table (16/16 MATCH), approval record with verbatim human verdicts
  - Dated STATE.md decision line: (08-04, HUMAN gate 2026-09-26) DEMO-CURATION [GATE] APPROVED
  - Formally ratified tier vocabulary (easy|hard|challenge|very_challenging)
  - Canonical PubChem citation wording (citation-guidelines page, 2026-09-26) for DATA_SOURCES.md (08-09)
affects: [08-05, 08-06, 08-07 (content plans transcribe approved rows only), 08-09 (DATA_SOURCES.md canonical citations), 08-10 (supply re-measurement), 08-11 (detector-coverage / DETECT-03 re-check + [HUMAN] checkpoint)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Approval-conditioned gate: human verdict 1 demanded an independent re-verification; approval recorded ONLY after the fresh source cross-check passed (16/16 MATCH)"
    - "Re-verification battery shape: per candidate — property JSON + 3D SDF fetched fresh; SDF counts-line==atom-block lines; heavy(SDF)==proposal==heavy(formula); exactly ONE $$$$ record"
    - "JS-walled doc pages: same server exposes a Markdown representation (/pcfe/docs/markdown/<slug>.md) — usable when the HTML shell is JS-gated"

key-files:
  created:
    - .planning/phases/08-demo-curation-citations/08-04-SUMMARY.md
  modified:
    - .planning/phases/08-demo-curation-citations/08-PROPOSALS.md
    - .planning/STATE.md

key-decisions:
  - "DEMO-CURATION [GATE] APPROVED 2026-09-26 (human): 9 sets / 16 curated ligands (18 total incl. dev set's 2); tier tokens easy|hard|challenge|very_challenging"
  - "C1 accepted ('1 ok'): benzoic acid = CID 243 (research's 3979 was a misidentification); aspirin CID 2244 human-spot-verified"
  - "C2 counts source-confirmed by independent re-verification: citric 13, acetate 4, glutamate 10, acetylcholine 10, folate 32, thyroxine 24 — distribution 12 small / 4 medium / 0 large"
  - "U1: docs/disclaimer is dead; canonical PubChem reference = https://pubchem.ncbi.nlm.nih.gov/docs/citation-guidelines — PubChem 2025 update, NAR 53(D1):D1516-D1525, doi:10.1093/nar/gkae1059 (+ PUG-REST doi:10.1093/nar/gky294 for fetch services)"
  - "U3: docs/DATA_SOURCES.md is a LATER deliverable (plan 08-09) — recorded in-proposal at the human's request"
  - "All 10 decision defaults ACCEPTED AS-IS with the human's re-check-later caveat ('4 accept first lets chk later') — re-check points 08-10 / 08-11; any D5/D9 revisit is a proposal-level event (02-01 GATE §4.7)"

patterns-established:
  - "Gate approval line protocol (DETECT-03 precedent): approval in BOTH the proposal header AND a dated STATE.md decision line, written only after every human condition passes, before any candidate data is fetched/committed"
  - "Verbatim verdict recording: human responses quoted, never paraphrased into agreement"
  - "expect_atom_count guards re-confirmed at approval time (16 rows) — the 08-01 builder will refuse any fetch disagreeing"

# Metrics
duration: ~13 min (continuation session: re-verification + amendments + approval recording; the drafting/checkpoint session was a separate earlier session)
completed: 2026-09-26
---

# Phase 8 Plan 04: Demo Curation [GATE] Proposals — Approval Summary

**Human-approved content gate for the ~9 curated demo sets: independent atom-count re-verification (human-demanded) passed 16/16 MATCH against fresh source fetches, all four deferred UNVERIFIED items resolved with verbatim human words, all ten decision defaults accepted with a re-check-later caveat, and approval recorded in both the proposal header and a dated STATE.md decision line — unblocking 08-05..08-07 content fetches through the 08-01 pipeline.**

## Performance

- **Duration:** ~13 min (continuation session; drafting + checkpoint session was earlier the same day, unrecorded)
- **Started:** 2026-09-26T13:17:45Z
- **Completed:** 2026-09-26T13:30Z
- **Tasks:** 4/4 (Task 3 = the [GATE] checkpoint, resolved by the human's verdicts; Task 4 = post-approval recording + this summary)
- **Files modified:** 2 (08-PROPOSALS.md, STATE.md) + 1 created (this summary)

## Accomplishments

- **Human-demanded atom-count re-verification: 16/16 MATCH.** Fresh, independent curl fetches of every primary candidate's PubChem property JSON + 3D SDF (15 CIDs) plus RCSB `HEM_ideal.sdf`; per candidate: SDF counts-line atom count == atom-block lines, heavy atoms (atom block, non-H) == the proposal's C2-corrected heavy count == heavy-atom total recomputed from the fetched MolecularFormula, and exactly ONE `$$$$` record per SDF. The approval condition ("do again yourself and re-verify against source") was satisfied BEFORE any approval line was written; any mismatch would have stopped the approval per the hard requirement.
- **U1–U4 all RESOLVED 2026-09-26 with the human's verbatim words.** U1: the old disclaimer URL is dead (human-verified); the canonical reference is the citation-guidelines page — the executor fetched it (via its Markdown representation; the HTML shell is JS-walled) and recorded verbatim: primary citation "PubChem 2025 update, NAR 53(D1):D1516-D1525, doi:10.1093/nar/gkae1059", per-record CID-URL citation format, original-source attribution guidance, and the PUG-REST service citation. U2: the previously-403 paper DOIs are human-verified "all verified from pdb website". U3: clarified in-proposal that `docs/DATA_SOURCES.md` is a LATER deliverable (plan 08-09) with the canonical citation wording coming from U1. U4: 1OXR PDBe entry page browser-tested pass ("tested 1xor pass").
- **Approval recorded in BOTH mandated places.** 08-PROPOSALS.md header: `APPROVED 2026-09-26, human` + amendment header + full Approval-record section quoting all 5 human verdicts VERBATIM; STATE.md: dated `(08-04, HUMAN gate 2026-09-26) DEMO-CURATION [GATE] APPROVED` decision line + Current Position / metrics / session continuity updated (84/92 plans, Phase 8 4/11).
- **All 10 decision defaults ACCEPTED AS-IS** with the re-check-later caveat recorded ("4 accept first lets chk later"); tier vocabulary formally ratified (easy|hard|challenge|very_challenging); 08-05..08-07 UNBLOCKED — approved rows transcribe into `scripts/demo_specs/*.json` and fetch/commit ONLY through the 08-01 pipeline.

## Task Commits

Each stage was committed atomically:

1. **Task 1: re-fetch candidate evidence + write 08-PROPOSALS.md** — `297e812` (docs, prior session)
2. **Task 2: record the open decisions with defaults** — `ddc5aeb` (docs, prior session)
3. **Checkpoint-reached STATE note** — `4e68b1c` (docs, prior session); checkpoint presented, approval PENDING
4. **Continuation: approval-time re-verification table** — `459e96f` (docs): fresh 16/16 MATCH cross-check appended
5. **Continuation: U1–U4 resolutions + decisions ACCEPTED + approval record** — `7b4d0f9` (docs)
6. **Continuation: GATE approval recorded in STATE.md** — `fc3d943` (docs)

**Plan metadata:** (this commit — `docs(08-04): complete demo-curation gate plan`)

## Files Created/Modified

- `.planning/phases/08-demo-curation-citations/08-PROPOSALS.md` — [GATE] proposal; amended with the re-verification table, U1–U4 resolutions, ACCEPTED-decisions status, approval header + verbatim approval record
- `.planning/STATE.md` — dated [GATE] APPROVED decision line; Current Position, metrics, session continuity
- `.planning/phases/08-demo-curation-citations/08-04-SUMMARY.md` — this file

ZERO candidate-data writes: no `aamatch/data/` change, no MANIFEST.json write, no SDF files — all verification GETs were read-only network calls to stdout/temp.

## Decisions Made

All recorded in 08-PROPOSALS.md (header + Decisions section status + Approval record) and STATE.md. Headlines: DEMO-CURATION [GATE] APPROVED 2026-09-26; C1 (benzoic acid 243) accepted; C2 counts source-confirmed by the re-verification; U1 canonical citation wording fixed (PubChem 2025 update NAR paper); data sources document ownership = 08-09 (U3); all 10 defaults accepted with re-check-later caveat; fetch boundary intact until 08-05..08-07 run their sanctioned fetches.

## Deviations from Plan

**1. [Rule 2 - Missing Critical] CLI-fix for the re-verification script's python3.6 incompatibility**
- **Found during:** Continuation execution (re-verification battery)
- **Issue:** The fresh re-verification script used `subprocess.run(..., capture_output=True)`, which is python3.7+; the env floor is python3.6.
- **Fix:** Switched to `stdout=subprocess.PIPE` + `universal_newlines=True` (3.6-compatible).
- **Files modified:** temp script only (`/tmp/opencode/08-04-reverify/reverify.py`) — never committed.
- **Verification:** Full battery re-ran cleanly → 16/16 MATCH.

**2. [Rule 3 - Blocking] JS-walled citation-guidelines page unblocked via its Markdown representation**
- **Found during:** U1 resolution (the human's resolution demanded executor-verified page content)
- **Issue:** `https://pubchem.ncbi.nlm.nih.gov/docs/citation-guidelines` returns a JS-gated HTML shell to non-browser fetches.
- **Fix:** The same server ships a full Markdown copy at `https://pubchem.ncbi.nlm.nih.gov/pcfe/docs/markdown/citation-guidelines.md` (advertised by a `<link rel="alternate" type="text/markdown">` in the shell); fetched and quoted verbatim into the proposal.
- **Files modified:** 08-PROPOSALS.md (U1 resolution records the route + wording).
- **Committed in:** `7b4d0f9`.

**3. [Plan-scope, documented] Re-verification covered HEM in addition to the 15 CIDs**
- The hard requirement named the 15 primary CIDs; HEM (16th candidate, RCSB source) was re-fetched in the same pass for completeness (`C34H32FeN4O4`, 43 heavy, `75 82`, ONE record — MATCH). No scope creep into content plans.
- **Committed in:** `459e96f`.

## Task Results (verbatim re-verification table)

| entry | CID | formula | heavy(SDF) | heavy(formula) | proposal | VERDICT |
|---|---|---|---|---|---|---|
| aspirin | 2244 | C9H8O4 | 13 | 13 | 13 | MATCH |
| benzoic_acid | 243 | C7H6O2 | 9 | 9 | 9 | MATCH |
| citric_acid | 311 | C6H8O7 | 13 | 13 | 13 | MATCH |
| acetate | 175 | C2H3O2− | 4 | 4 | 4 | MATCH |
| caffeine | 2519 | C8H10N4O2 | 14 | 14 | 14 | MATCH |
| benzamidine | 2332 | C7H8N2 | 9 | 9 | 9 | MATCH |
| guanidinium | 32838 | CH6N3+ | 4 | 4 | 4 | MATCH |
| glutamic_acid | 33032 | C5H9NO4 | 10 | 10 | 10 | MATCH |
| acetylcholine | 187 | C7H16NO2+ | 10 | 10 | 10 | MATCH |
| atp | 5957 | C10H16N5O13P3 | 31 | 31 | 31 | MATCH |
| nad | 5892 | C21H27N7O14P2 | 44 | 44 | 44 | MATCH |
| chloramphenicol | 5959 | C11H12Cl2N2O5 | 20 | 20 | 20 | MATCH |
| quinine | 3034034 | C20H24N2O2 | 24 | 24 | 24 | MATCH |
| folic_acid | 135398658 | C19H19N7O6 | 32 | 32 | 32 | MATCH |
| thyroxine | 5819 | C15H11I4NO4 | 24 | 24 | 24 | MATCH |
| heme | HEM (RCSB) | C34H32FeN4O4 | 43 | 43 | 43 | MATCH |

Full table (with MW, charge, SDF atoms/bonds, `$$$$` checks) lives in 08-PROPOSALS.md — *Approval-time re-verification (2026-09-26)*.

## Self-Check: PASSED

- [x] Re-verification table appended — 16/16 MATCH (zero mismatches; no STOP needed)
- [x] U1–U4 resolved in-proposal with verbatim human words; citation-guidelines page fetched + wording recorded
- [x] 10 defaults recorded ACCEPTED (2026-09-26, re-check-later caveat)
- [x] Approval recorded in PROPOSALS header + dated STATE.md decision line
- [x] GREPS: `APPROVED` in 08-PROPOSALS.md (4) + `GATE] APPROVED` in STATE.md (3)
- [x] Zero `aamatch/data/` or SDF writes; docs-only commits
- [x] 08-05..08-07 UNBLOCKED for the 08-01 pipeline

## Next Phase Readiness

- **08-05 / 08-06 / 08-07 (content plans): UNBLOCKED.** Transcribe APPROVED rows (set_ids, entry_ids, CIDs, URLs, expect_atom_count guards — aspirin 21, benzoic 15, citric 21, acetate 7, caffeine 24, benzamidine 17, guanidinium 10, glutamate 19, acetylcholine 26, ATP 47, NAD 71, chloramphenicol 32, quinine 48, folate 51, thyroxine 35, heme 75) into `scripts/demo_specs/*.json`; run the 08-01 pipeline per set (`--fetch` → SMOKE-02 → atomic commit). File naming per Decision 6 (`ligands/<set_id>-<entry_id>.sdf`); titles per Decision 10.
- **08-09 (DATA_SOURCES.md):** must quote the PubChem 2025 update canonical citation + per-record CID URLs + PUG-REST citation (all wordings recorded in U1), per-entry PDBe links as secondary provenance (U4), and cite 1OXR (Ca²⁺) as the cleanup-scene real-world analog (Decision 8).
- **08-10 / 08-11:** carry the re-check-later caveat — supply re-measurement (Decision 4/10) and detector-coverage / DETECT-03 revisit (Decision 9).
- **Outstanding concerns:** none blocking. The paper-DOI set in U2 is recorded as human-verified "from pdb website" — the human's response listed 6 DOIs against the proposal's 7-item 403 set; every DOI in both sets is independently VERIFIED in the RCSB Data API primary-citation record, so no follow-up needed, but 08-09 should include each DOI alongside its RCSB-record citation fields so the provenance chain never relies on doi.org resolution alone.
