---
phase: 08-demo-curation-citations
verified: 2026-10-10T23:59:00Z
status: passed
score: 4/4 phase criteria verified (11/11 plan must_have groups verified)
re_verification: null
gaps: []
---

# Phase 8: Demo Curation & Citations — Verification Report

**Phase Goal:** ~9 curated demo sets ship with full, human-verified provenance under the propose → human-approve → fetch/commit protocol — content is gated by truthfulness, not by code.
**Verified:** 2026-10-10 (live WSL + headless Windows PyMOL runs on the final tree)
**Status:** **passed**
**Re-verification:** No — initial verification (no prior VERIFICATION.md existed)
**Sequencing:** Per ROADMAP CONTEXT constraint 8, this verification ran AFTER Phase 8.1 landed, on the corrected final tree (R1–R8 protonation-swap state) — as required.

---

## Goal Achievement

### Per-Criterion Verdict Table

| # | Criterion (ROADMAP) | Tier | Verdict | Receipts (file:line / command) |
|---|---------------------|------|---------|-------------------------------|
| 1 | Every demo candidate proposed with PDB/SDF IDs, protonation/interaction sources, recorded rationale — human approval recorded BEFORE fetch/commit | [GATE] | ✓ VERIFIED | Evidence blocks below (C1-a…C1-d) |
| 2 | ~9 tier slots ship (Easy ×3, Hard ×3, Challenge, Very-challenging ×2), pre-downloaded + committed; dropdown lists curated sets grouped by tier | [HUMAN] | ✓ VERIFIED | C2-a…C2-f |
| 3 | DATA_SOURCES.md covers every bundled file: download source, PDB ID + DOI, protonation/interaction provenance, verified license; dated amendments | [HUMAN] | ✓ VERIFIED | C3-a…C3-e |
| 4 | Every-manifest-id smoke + messy-scene Cleanup smoke PASS; WSL suite green | [HEADLESS] | ✓ VERIFIED (live runs this session) | C4-a…C4-e |

**Score:** 4/4 criteria verified.

---

### Criterion 1 [GATE] — propose → human-approve → fetch/commit

- **C1-a — Proposal artifact exists and is substantive.** `.planning/phases/08-demo-curation-citations/08-PROPOSALS.md` (50,263 bytes; 9 set sections + per-candidate field tables). Rows carry every required field — seen verbatim in the Set-1 rows: set_id/tier/entry_id; molecule + formula + heavy atoms; source + exact fetch URL + evidence (HTTP 200 + counts line); interaction types + why (capability.py rules); halogen/metal flags; PDB complex provenance (ID + entry DOI + paper DOI + PLIP ref); protonation record with why; license + policy URL; selection rationale; alternates.
- **C1-b — Approval recorded in the proposal header, BEFORE any fetch/commit.** Header line: `Status: APPROVED 2026-09-26, human — approval recorded here and as a dated [GATE] APPROVED line in .planning/STATE.md, before any candidate data is fetched into the repo or committed`. The approval was conditioned on the human-demanded independent re-verification ("for the atom count, do again yourself and re-verify against source") — the **Approval-time re-verification table shows 16/16 MATCH** (three-way cross-check: counts-line==atom-block, heavy(SDF)==proposal, heavy(formula)==proposal, exactly ONE `$$$$` per SDF; fresh curl fetches 2026-09-26).
- **C1-c — Git-ordering proof (approval precedes data commits).**
  - `459e96f 2026-09-26 21:22 docs(08-04): append approval-time atom-count re-verification (16/16 MATCH)`
  - `7b4d0f9 2026-09-26 21:24 docs(08-04): resolve U1-U4 with human verdicts verbatim + decisions ACCEPTED`
  - **first** data commit: `d0cef87 2026-09-26 22:18 feat(08-05): bundle demo-easy-1` — 54+ minutes after the approval record. All later data commits (9b64323, 0875c74, aca6b8f…b55e773) follow.
- **C1-d — STATE.md dated gate record + U1-U4 resolutions.** `STATE.md:285` "(08-04, HUMAN gate 2026-09-26) **DEMO-CURATION [GATE] APPROVED** — … re-verification 16/16 MATCH … U1–U4 RESOLVED verbatim … 08-05..08-07 UNBLOCKED". U1 resolved to the citation-guidelines canonical reference (PubChem gkae1059); U2 "all verified from pdb website"; U3 DATA_SOURCES is 08-09's deliverable; U4 "tested 1xor pass". The 2026-10-05 R1–R8 swap record (`STATE.md:316`) carries the human directive verbatim ("per our spec we want to assume physiological pH normally" → "2 go R1-R8, 3 +1") — the propose→approve→commit protocol was re-honored for the LATER data surgery too (six atomic set commits 862fdc7…b55e773, each through the 08-01 pipeline).

**C1 VERDICT: ✓ VERIFIED** — the gate is real, dated, ordered, and re-honored under amendment.

### Criterion 2 [HUMAN] — ~9 tier slots + grouped dropdown

- **C2-a — Live manifest census (derived from the data this session, NOT from SUMMARYs).** `python3.6` parse of `aamatch/data/MANIFEST.json` (container `AAMATCH/manifest` v1): **10 sets / 18 entries (16 curated + 2 dev)**; tiers: easy 4 / hard 3 / challenge 1 / very_challenging 2. The dev set carries `tier: easy` per the recorded Decision 3 (08-PROPOSALS.md:343: "demo-dev-1 REMAINS in the manifest and the dropdown under Easy") — so the curated census is exactly **Easy ×3, Hard ×3, Challenge ×1, Very-challenging ×2 = 9 curated sets** (GEN-06 slot inventory met) + the dev regression oracle. SMOKE-02 pins this exact census (`smoke/smoke_02_manifest.py:103-105 EXPECTED_TIER_CENSUS = {easy:4, hard:3, challenge:1, very_challenging:2}`) and PASSED.
- **C2-b — All ligand files pre-downloaded and committed.** `git ls-files aamatch/data/ligands/` = **18**; `ls aamatch/data/ligands/` = 18 files; `git status --porcelain` clean. All 18 manifest `file` paths exist on disk (live check: 0 missing).
- **C2-c — Dropdown grouping code + data path.** `aamatch/setup_form.py:142-162` (TIER_ORDER/TIER_LABELS/`manifest_sets_grouped`, pure, groups outside TIER_ORDER land in the trailing Other group); `aamatch/setup_window.py:331-371` (grouped population loop, `insertSeparator` BETWEEN groups only, `_known_demo_set_ids` None-guard so a separator can never yield set-id `'None'`; stale-id fallback to first selectable data row at :549-591, :970, :1045).
- **C2-d — The smoke proving it.** `bash smoke/run_smoke.sh smoke/smoke_11_window.py 180` → `=== SMOKE-11 PASS ===` (part-B T1b data-relative asserts: separator count == groups−1, every None-data row is a flag-disabled separator, known-ids helper excludes separators).
- **C2-e — [HUMAN] half CLOSED by recorded verdicts.** `08-11-SUMMARY.md` criterion map c2 **CLOSED (2026-09-27, re-confirmed 2026-10-05)**: recorded '**1 pass**' grouped-dropdown verdict (2026-09-27) + re-confirmed in the combined session step 1 ('**1-8 pass**'); the post-R1–R8 curated-set retest across all six swapped sets recorded '**6 all**' (2026-10-05). Records EXIST and are internally consistent: the swap commits 862fdc7…b55e773 match the manifest state, and this session's independent charge re-derivation (C4-e) confirms the swapped charges (acetylsalicylate −1, benzoate −1, citrate −3, benzamidinium +1, L-glutamate −1, quinuclidinium +1, folate −2, thyroxine 0) — the data state the human retested is the data state on disk. Not re-demanded per verifier discipline.

**C2 VERDICT: ✓ VERIFIED** (mechanical + recorded-human halves both closed).

### Criterion 3 [HUMAN] — DATA_SOURCES.md

- **C3-a — Coverage of every bundled file.** `docs/DATA_SOURCES.md` (274 lines): §2 has one section per set in dropdown tier order (lines 70-206: demo-easy-1…demo-dev-1, dev last, marked "DEVELOPMENT FIXTURE, NOT curated demo data"). **Live cross-check: all 18 manifest entry files are named in the doc (18/18, 0 uncovered).**
- **C3-b — Per-row provenance.** Every curated row carries: download source + exact fetch URL, CID/CCD, PDB complex + entry DOI + paper DOI, PLIP reference (doi:10.1093/nar/gkaf361), protonation record with why (pKa values + sources), license matching MANIFEST.json verbatim, sha256, fetch date. Honest-absence discipline present and later superseded by dated amendments (8FUY/1S0R/9NDX/1MBN paper-DOI absences resolved by the 1CTS/1V2L/4WNV swaps — prior records explicitly "stay in git history", never deleted).
- **C3-c — License quotes.** §1 (lines 24-30): verbatim **PubChem/NCBI public domain** quote + Fair-Use disclaimer with submitter-rights caveat, and **wwPDB CC0 1.0** verbatim quote ("Data files contained in the PDB archive are available under the CC0 1.0 Universal…"), each with policy URL + fetch/re-verify dates (2026-09-24, re-verified 2026-09-26 at the 08-04 GATE).
- **C3-d — DATED AMENDMENTS (history not rewritten).** All present with dates and human directive quotes: 1CTS swap (line 99, "Amended 2026-10-04 by human directive… 8FUY → 1CTS"), 1V2L swap (line 128, 1S0R → 1V2L), 4WNV swap for quinine (line 174, 9NDX → 4WNV) AND heme (line 204, 1MBN → 4WNV, verbatim human reasoning "1mbn has a old ref w/o doi, but the xtal quality is low so better use 4wnv to be simple"); heme **modified-from note** (line 204: "MODIFIED from the RCSB HEM_ideal.sdf: 2 artifact hydrogens + their O–H bonds removed… recorded 2026-10-04 per human approval… verbatim 'yes drop the 2 H since its supposed to be deprotonated'"); **R1–R8 physiological-protonation swaps 2026-10-05** on 8 rows (lines 84, 85, 99, 128, 143, 174, 187, 188) each with pKa evidence (PubChem AIDs, IUPAC Digitized pKa Dataset records, Merck, HSDB) + the human directive verbatim "per our spec we want to assume physiological pH normally" / "2 go R1-R8, 3 +1"; the **444655 bare-cation mislabel fix** (line 128: "MISLABEL FIX… it is the BARE benzamidinium cation C7H9N2⁺… the CID was right, the prose was wrong"). §3 policy section amended 2026-10-05 (line 237). Dated amendments are honest records, not violations.
- **C3-e — [HUMAN] sign-off CLOSED by record.** `08-11-SUMMARY.md` step 9: human verbatim '**5 pass**' (2026-10-05; URL/DOI lists delivered pre- and post-swap and spot-checked). Criterion map c3 **CLOSED (2026-10-05)**. Not re-demanded per verifier discipline.

**C3 VERDICT: ✓ VERIFIED.**

### Criterion 4 [HEADLESS] — live-run evidence (this session)

- **C4-a — py_compile gate:** `python3.6 -m py_compile aamatch/*.py` → OK.
- **C4-b — WSL suite:** `python3.6 -m unittest discover -s tests` → **Ran 940 tests … OK** (51.6 s) — exactly the expected 940, including the demo-data battery (`tests/test_demo_data.py`), the supply battery (`tests/test_demo_supply.py`), and the purity gates.
- **C4-c — Every-manifest-id smoke:** `bash smoke/run_smoke.sh smoke/smoke_02_manifest.py 180` → `=== SMOKE-02 PASS ===` (exit 0; tail shows per-set loads with counts == manifest incl. `SMOKE-02 heme charge PASS got -4 want -4`, `heme metal flag PASS scan=['C','FE','H','N','O'] flag=True`, `no tmp leak PASS`).
- **C4-d — Messy-scene cleanup smoke:** `bash smoke/run_smoke.sh smoke/smoke_21_demo_cleanup.py 180` → `=== SMOKE-21 PASS ===` (exit 0; tail: `name set restored PASS post=['user_complex'] pre=['user_complex']`, `per-object atom counts restored PASS drifts=[]`, `no _aam_ object remains PASS leftover=[]`, `no AAM segi outside game objects PASS segi AAM atoms=0`) — PITFALL 13 proven in the field; Cleanup leaves exactly the original object set.
- **C4-e — Independent formal-charge/counts re-derivation (verifier's own receipt, disk bytes → manifest):** parsed all 18 SDFs (counts line + M CHG block) and compared to the manifest pins — **atom_count/bond_count/formal_charge_sum: 0 mismatches across 18/18 entries**. This live-confirms the post-2026-10-05 swap state without trusting any SUMMARY.

**C4 VERDICT: ✓ VERIFIED.**

---

### Requirements Coverage

| Requirement | Status | Evidence |
|-------------|--------|----------|
| GEN-06 (demo sets ship pre-downloaded ~9 tier slots with provenance + rationale) | ✓ SATISFIED | REQUIREMENTS.md:35 `[x]`, :135 Phase 8 Complete; criteria 1+2 verified above |
| HELP-02 (dedicated sources doc, human-verified, propose→approve→fetch/commit; verified licenses) | ✓ SATISFIED | REQUIREMENTS.md:75 `[x]`, :160 Phase 8 Complete; criteria 1+3 verified above |

### Key Link Verification

| From | To | Via | Status |
|------|----|----|--------|
| setup_window.py `_populate_demo_sets` | setup_form.manifest_sets_grouped | grouped loop + insertSeparator + _known_demo_set_ids | WIRED (setup_window.py:331-371; SMOKE-11 PASS) |
| MANIFEST.json entries | aamatch/data/ligands/*.sdf | `file` paths + sha256/counts pins | WIRED (18/18 exist; 18/18 committed; live counts/charges 0 mismatches; SMOKE-02 PASS) |
| docs/DATA_SOURCES.md rows | MANIFEST.json + 08-PROPOSALS.md | license fields verbatim + GATE-approval pointer in header | WIRED (18/18 files covered; license strings match manifest) |
| 08-PROPOSALS.md approved rows | scripts/demo_specs/*.json → build_demos.py | transcription of approved rows only (protocol) | WIRED (10 specs committed; --report-only contract; swaps re-ran the same pipeline) |
| smoke_21 | aamatch.placement.cleanup_game_objects | prefix-only deletion vs messy scene | WIRED (SMOKE-21 PASS, exact restoration incl. per-object atom counts) |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| aamatch/setup_window.py | 288/340/716 | "placeholder" in comments (combo initial-state / degradation path docs) | ℹ️ Info | None — design commentary, not stubs |
| docs/DATA_SOURCES.md | 211-212 | dev-set license `''` "placeholder by design" | ℹ️ Info | None — documents the recorded 02-04 dev-fixture law |

Zero TODO/FIXME/HACK across all phase-touched code, docs, smokes, and tests. No blocker or warning anti-patterns.

### Human Verification Required

None outstanding. All [HUMAN] halves are CLOSED by recorded verdicts (08-11-SUMMARY.md criterion coverage map: c2 '1 pass' 2026-09-27 + '1-8 pass' re-confirm; c3 '5 pass' 2026-10-05; curated-set retests '6 all' 2026-10-05), and this session independently re-verified the underlying data state those verdicts covered (C4-e: 0 mismatches). Per the verifier discipline for this phase, no human testing is re-demanded.

### Gaps Summary

None. All four ROADMAP Phase-8 criteria verified against live code/data/smoke evidence. Two census notations for the record, neither a gap:
1. The dev set carries `tier: easy`, so the raw tier census is easy 4 / hard 3 / challenge 1 / very_challenging 2 — this is the recorded Decision 3 (08-PROPOSALS.md:343) and is pinned exactly by SMOKE-02's `EXPECTED_TIER_CENSUS`; the curated census is 3+3+1+2 = 9 sets, meeting GEN-06's "~9 tier slots".
2. The prompt's referenced smoke filename `smoke_02_every_manifest.py` is actually `smoke/smoke_02_manifest.py` (verified via `ls smoke/`; run + PASS this session).

---

_Verified: 2026-10-10T23:59:00Z_
_Verifier: OpenCode (gsd-verifier)_
