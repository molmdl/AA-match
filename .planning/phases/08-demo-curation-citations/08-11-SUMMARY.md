---
phase: 08-demo-curation-citations
plan: 11
type: execute-checkpoint-record
subsystem: ui/verification
tags: [pymol, demo-curation, data-sources, grouped-dropdown, detector-coverage, human-checkpoint, verdicts, fix-batch, protonation-swap]

# Dependency graph
requires:
  - phase: 08-demo-curation-citations
    provides: plans 08-01..08-10 (bundling pipeline + dry-run oracle, dropdown tier grouping, smoke de-hardcoding, 08-PROPOSALS [GATE] APPROVED 2026-09-26, Easy/Hard/Challenge/Very-challenging bundling through the sanctioned pipeline, SMOKE-02 curated coverage + SMOKE-21 messy-scene cleanup, DATA_SOURCES.md, curated-manifest supply measurement)
  - phase: 08.1-confirm-pass-gate-restoration
    provides: the combined [HUMAN] session that closed this plan's deferred Task 3 (human decision 2026-09-27) — pass-gate retest on the corrected tree folded the dropdown/curated-play/cleanup/DATA_SOURCES/detector-verdict items into one sitting
provides:
  - ROADMAP Phase-8 criterion 1 (GEN-06 [GATE] propose→approve protocol) — verdict recorded: c1 CLOSED via 08-04 approval record (08-PROPOSALS.md APPROVED 2026-09-26, human; 16/16 count re-verification satisfied)
  - ROADMAP Phase-8 criterion 2 (GEN-06 [HUMAN] ~9 tier slots + grouped dropdown) — verdict recorded: CLOSED (mechanical/headless halves 08-05/06/07 + 08-08 + 08-10 + SMOKE-11; real-viewer half human-passed 2026-09-27 '1 pass' + re-confirmed in the combined session step 1)
  - ROADMAP Phase-8 criterion 3 (HELP-02 [HUMAN] DATA_SOURCES.md sign-off) — verdict recorded: CLOSED (human '5 pass' 2026-10-05; URL/DOI lists delivered pre- and post-swap and spot-checked)
  - ROADMAP Phase-8 criterion 4 ([HEADLESS] every-manifest-id + messy-scene cleanup) — CLOSED (SMOKE-02 + SMOKE-21 PASS across the session trees; standing battery)
  - DETECT-03 dataset-revisit verdict — accepted as recorded: NO threshold surprise, no DETECTOR_VERSION bump (Task-2 probe 2026-09-27; now standing SMOKE-22, 24 checks)
affects: [phase verifier (Phase 8 ready), Phase 8.2, Phase 9 (docs-match-reality audit inherits the swap-tree data)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Combined-checkpoint pattern (second instance; 04-14/04-15 precedent relaxed): ONE [HUMAN] GUI session closes a phase's deferred checkpoint inside the follow-on inserted phase's final plan — declared by dated deferral NOTEs in ROADMAP + STATE, never implicit"
    - "Propose → human-approve → fetch/commit data protocol survives later data surgery: provenance swaps, artifact data fixes, and the R1-R8 protonation swaps all re-ran the SAME 08-01 pipeline (spec → fetch → drift-restore → derive in-run → SMOKE-02 → battery → atomic commit)"

key-files:
  created:
    - ".planning/phases/08-demo-curation-citations/08-11-SUMMARY.md"
  modified: []

key-decisions:
  - "08-11 Task 3 DEFERRED to Phase 8.1's final [HUMAN] plan by human decision 2026-09-27 (ROADMAP.md Phase-8 NOTE) — one combined GUI session closes both; closed by the 8.1 combined session 2026-09-27 → 2026-10-05"
  - "DETECT-03 revisit verdict (accepted 2026-10-04): 'NO threshold surprise — DETECT-03 provisional values hold on real data (halogen records provable on chloramphenicol C-Cl and thyroxine C-I geometry inside the approved 4.0 A / [135,195] / [90,150] windows; metal record provable on HEM Fe inside the 3.0 A window; heme formal_charge_sum -4 as recorded at 08-07); no DETECTOR_VERSION bump proposal needed'"
  - "All four Phase-8 criteria + the DETECT-03 revisit now carry closed verdicts — Phase 8 execution records COMPLETE 11/11"
  - "Physiological-protonation data state (R1-R8 swaps, human '2 go R1-R8, 3 +1' 2026-10-05) is the FINAL curated data state the dropdown/DATA_SOURCES verdicts cover"

patterns-established:
  - "Criterion coverage map: each ROADMAP criterion split into [GATE]/[HUMAN]/[HEADLESS] halves with the concrete artifact per half (document + date / GUI step + verdict quote / smoke + count) — reusable by every later phase close-out"

# Metrics
duration: Task 1 + Task 2 executed 2026-09-27 (battery + probe); the [HUMAN] Task 3 session ran 2026-09-27 → 2026-10-05 inside Phase 8.1; this record assembled at close-out
completed: 2026-10-05
---

# Phase 8 Plan 11: Full Regression Battery + Detector-Coverage Verdict + [HUMAN] Consolidated Demo Checkpoint — Summary

**The Phase-8 close-out plan, closed in the combined 8.1 [HUMAN] session per the recorded deferral: full regression battery GREEN (912/912 WSL + smokes 01–21 at the 2026-09-27 tree, re-greened 931/931 by 08.1-07 and 940/940 on the final tree), the DETECT-03 dataset-revisit verdict accepted as recorded (NO threshold surprise, no DETECTOR_VERSION bump), and every [HUMAN] item — grouped dropdown, curated-set play, Cleanup field check, DATA_SOURCES.md sign-off — human-PASSED ('1 pass', '5 pass') with trial/skip logs recorded.**

## Performance

- **Task 1 (auto, 2026-09-27):** full regression battery on the final Phase-8 tree `0fb3d7d` — py_compile OK; **912/912 WSL** (purity gates + demo-data + supply included); **smokes 01–21 ALL PASS** headless (23 runs; SMOKE-17 two-phase + SMOKE-20 two-run at 240 s; 180 s for 02/05/08/11/21; 03–07 re-verified post-fix). ONE Rule-1 fix `0fb3d7d` (`gamestart._FRONT_NOISE_FLOOR = 5e-5` — SMOKE-08 part-5 idempotent-compose float32-noise floor; owning-file fix, smoke untouched).
- **Task 2 (auto, 2026-09-27):** detector-coverage probe `tmp/detector_coverage_phase8.py` (one-off, git-ignored) — halogen records provable on chloramphenicol C–Cl and thyroxine C–I (constructed d_ax 3.300 / donor 180.0 / acc 120.0, inside the approved windows), metal records provable on heme Fe (2 records ≤ 3.0 Å), heme formal_charge_sum −4 re-verified, zero leakage. Verdict below.
- **Task 3 ([HUMAN], 2026-09-27 → 2026-10-05):** DEFERRED into Phase 8.1's final checkpoint plan (08.1-08 Task 1) and CLOSED there — full per-step record in `.planning/phases/08.1-confirm-pass-gate-restoration/08.1-08-SUMMARY.md`; the criterion map below carries the verdicts. Multiple GUI sessions, human-driven retests; Windows PyMOL 2.5.0 via `setenv.bat` (01-09 plugin-path install, live repo copy).

## Deferral record (verbatim from the plan's originating decision)

> Task 3 closed by Phase 8.1's combined [HUMAN] session per human decision 2026-09-27 (ROADMAP.md:234)

ROADMAP Phase-8 NOTEs (2026-09-27): "08-11 auto tasks 1-2 COMPLETE (battery GREEN + detector verdict recorded); Task 3 ([HUMAN] checkpoint + SUMMARY) DEFERRED to Phase 8.1's final human-checkpoint plan per human decision — one combined GUI session will close both" + "(CONTEXT constraint 8): Phase 8's /gsd-verify-phase runs AFTER Phase 8.1 lands (on the corrected tree)".

## Criterion coverage map (ROADMAP Phase-8 criteria → evidence → VERDICT)

(This is the plan's required "criterion coverage" record — promoted from the STATE draft with verdicts filled.)

| Criterion | Tier | Evidence | Verdict |
|-----------|------|----------|---------|
| c1 — every demo candidate proposed with IDs/protonation/interaction sources + recorded rationale; human approval recorded BEFORE any fetch/commit | [GATE] | The 08-04 propose→approve record: `08-PROPOSALS.md` header "**APPROVED 2026-09-26, human**" (approval conditioned on the executor's independent atom-count re-verification — PASSED 16/16 MATCH; C1 accepted; U1–U4 resolved verbatim; all 10 defaults accepted) + the dated `[GATE] APPROVED` line in STATE.md; content fetch/commit afterwards ONLY through the sanctioned 08-01 pipeline (spec → `--fetch` → SMOKE-02 → atomic commit) | **CLOSED (2026-09-26)** |
| c2 — ~9 tier slots ship (Easy ×3, Hard ×3, Challenge, Very challenging ×2), pre-downloaded and committed; the setup dropdown lists all curated sets grouped by tier | [HUMAN] | Mechanical/headless halves: 08-05/06/07 bundling commits (10 sets / 18 entries final incl. dev: 3 easy + 3 hard + 1 challenge + 2 very_challenging) + SMOKE-02 10-set census & exact tier census (08-08) + supply instrument (08-10) + SMOKE-11 PART B grouped-dropdown asserts. **[HUMAN] real-viewer half:** the recorded 2026-09-27 '**1 pass**' verdict (dropdown shows the tier groups Easy/Hard/Challenge/Very challenging with separators) + re-confirmed in the combined session step 1 ('**1-8 pass**', trial log 1) | **CLOSED (2026-09-27, re-confirmed 2026-10-05)** |
| c3 — DATA_SOURCES.md covers every bundled file (download source, PDB ID + DOI, protonation/interaction provenance, verified license), human-signed | [HUMAN] | Mechanical half: 08-09 (18/18 files covered, zero-MISSING audit, `--report-only` reproduction, verbatim policy quotes, DOI/other spot-checks). **[HUMAN] sign-off half:** URL/DOI lists delivered TWICE (pre-swap and post-swap states); the human spot-checked entries against live sources → human verbatim '**5 pass**' (2026-10-05). c3 now also covers the post-sign-off data state: the 8 DATA_SOURCES rows carry the dated 2026-10-05 protonation-swap amendments and the heme modified-from note. | **CLOSED (2026-10-05)** |
| c4 — every-manifest-id smoke passes; messy-scene Cleanup leaves exactly the original object set | [HEADLESS] | SMOKE-02 (every-manifest-id: loads via path helper, atom/bond counts == manifest, element-scan flag cross-check) + SMOKE-21 (messy-scene cleanup) — BOTH PASS in the 08-11 Task-1 battery and re-proven headless across every later session tree (SMOKE-02/21/22 on the final tree `b13f6bb`); plus the combined session step 8 curated Cleanup field check in the real viewer ('1-8 pass'). | **CLOSED** |
| DETECT-03 revisit (02-01 provisional caveat + 08-PROPOSALS decision 9 TRIGGERED-FOR-CHECK) | [GATE]-class verdict | Task-2 probe verdict (2026-09-27, recorded in STATE Phase-8 Decisions): "**NO threshold surprise — DETECT-03 provisional values hold on real data (halogen records provable on chloramphenicol C-Cl and thyroxine C-I geometry inside the approved 4.0 A / [135,195] / [90,150] windows; metal record provable on HEM Fe inside the 3.0 A window; heme formal_charge_sum -4 as recorded at 08-07); no DETECTOR_VERSION bump proposal needed**". thresholds.py / detector.py / level_spec.py UNTOUCHED (§4.7 honored). **Human acceptance:** presented verbatim 2026-10-04 (combined-session step 10, delegated to the orchestrator '10-11 check yourself' — checked + presented PASS); the probe is now standing **SMOKE-22** (24 checks, quick task 002) and PASSES on the final tree. | **CLOSED (accepted 2026-10-04)** |

## Battery tally (all three trees of the session arc)

| Tree / date | WSL | Smokes | Notes |
|-------------|-----|--------|-------|
| `0fb3d7d` (08-11 Task 1, 2026-09-27) | **912/912** (incl. purity gates + demo-data + supply) | 01–21 ALL PASS (23 runs) | ONE Rule-1 fix `0fb3d7d` `_FRONT_NOISE_FLOOR = 5e-5` (SMOKE-08 part-5 idempotent compose under float32 storage noise; owning-file fix) |
| Post-rework tree (08.1-07, 2026-10-01) | **931/931** (912 + 19 new 8.1 tests; purity 8/8) | 01–21 ALL PASS (23 runs; SMOKE-15 87, SMOKE-16 113 F=12, smoke_19 39, smoke_20 verify 32) | full re-green on the pass-gate tree — the combined session's verification basis |
| `b13f6bb` (final, 2026-10-05) | **940/940** (incl. purity + data battery; zero pin evolutions across the session's data work) | smokes 01–22 ALL PASS across the session; 02/08/15/16/21/22 re-proven on the final tree (15=87 checks, 16=113 F=12, 22=24) | the verifier-ready corrected tree |

## Combined-session per-step verdict table (the 08.1-08 Task-1 session that closed Task 3)

Session span: 2026-09-27 → 2026-10-05, multiple GUI sessions, human-driven retests. Full verbatim logs (trial log 1 + skip log) live in `08.1-08-SUMMARY.md`.

| Step (08.1-08 Task 1) | Covers (08-11 mapping) | Verdict (human, verbatim quotes) |
|-----------------------|------------------------|-----------------------------------|
| 1 — environment + optional dropdown re-confirm | c2 [HUMAN] half | **PASS** — '1-8 pass' (window opens, viewer interactive; tier-grouped dropdown — the 2026-09-27 '1 pass' already on record) |
| 2 — curated-set start (demo-easy-1) | c2 / c4 curated-set start | **PASS** — '1-8 pass' (countdown 3-2-1 → GO, timer from 0:00, required label, aspirin/benzoic playable — trial log 1) |
| 3 — blind confirm FAILS (+ wording sub-verdict) | 8.1 core; wording approval | **PASS** — '1-8 pass' (Formed/Missing debrief + retry line + tooltip wording approved in the same verdict) |
| 4 — retry works (panel Confirm) | 8.1 core | **PASS** — '1-8 pass' ('Molecule 1 of 2 scored 1.00 (total 1.00)', camera re-frame; "the fix working according to spec now") |
| 5 — blind confirm on molecule 2 also fails | 8.1 core | **PASS** — '1-8 pass' (no 0.00 record, no advance — the defect scenario now negative) |
| 6 — Skip escape | 8.1 + SCORE-05 regression | **PASS** — '1-8 pass' (skip log) |
| 7 — win gate + ENDGAME POPUP PARITY (panel end) | 8.1 + fix-batch parity item | **PASS** — '1-8 pass' (popup parity proven on the panel end; `c2cbb24` modal-parity fix human-passed) |
| 8 — Cleanup field check | c4 messy-scene half (real viewer) | **PASS** — '1-8 pass' (only game objects removed; stray/user objects remain; count reported; the human's deliberate ATP load was the session's only extra console line) |
| 9 — DATA_SOURCES.md sign-off | c3 [HUMAN] half | **PASS** — human '**5 pass**' (2026-10-05; URL/DOI lists delivered pre- and post-swap, spot-checked) |
| 10 — detector-verdict acceptance | DETECT-03 revisit acceptance | **PASS** — delegated to the orchestrator ('10-11 check yourself'), checked + presented PASS 2026-10-04 (verdict accepted as recorded: NO threshold surprise, no DETECTOR_VERSION bump) |
| 11 — console sweep | session hygiene | **PASS** — checked + presented 2026-10-04 (04-14 stock baseline only; zero AA-match tracebacks; the human's deliberate ATP load line excepted) |
| Protonation-swapped sets retest (all six swapped sets in GUI) | post-swap data-state coverage | **PASS** — human '**6 all**' (2026-10-05) |
| Fix-batch retest (heme lines; popup wording; ball-and-stick vs sticks) | folded fix batches | **PASS** — 'item 1 still see lines in heme, need fix' → resolved by `ef3c1e5` + `e903eea`, retested PASS in the '1 pass' verdict of 2026-10-05; 'item 2 popup wording pass / item 3 pass' |

## Fix-batch history folded into this session (one line each, with commits)

- **Panel-end endgame modal parity + offscreen entry-gate discovery** — `c2cbb24` (the first "no popup" diagnosis→fix cycle; the smoke pumps DO deliver armed shots).
- **Sticks normalization on the ligand too** — `3241616` (mixed line/stick scene, demo-veryhard-2).
- **Student-friendly thin-set start warning** — `74ce2c1` (generator refusal verbatim → runtime-derived student wording).
- **Provenance swaps** — `951245f` (citric_acid 8FUY→1CTS, benzamidine 1S0R→1V2L, quinine 9NDX→4WNV; all rows gained paper DOIs).
- **Heme artifact-H data fix** — `ef3c1e5` (pipeline transform `drop_artifact_OH_bonds`; 73 atoms / 80 bonds {1:65,2:15} / −4; DATA_SOURCES modified-from note per the human 'explicitly state what we have done').
- **Heme reference upgrade** — `557b2f4` (1MBN→4WNV per '1mbn has a old ref w/o doi, but the xtal quality is low so better use 4wnv to be simple'; honest-absence set now empty).
- **Q1 visual distinction (ball-and-stick ligand vs stick AAs)** — `e903eea` (recording-miss repaired; 'same group same rep'; retested PASS).
- **R1–R8 physiological-protonation swaps** — `862fdc7` easy-1 / `2a7cf63` easy-2 / `6126165` hard-1 / `332f5a6` hard-2 / `c91d824` challenge-1 / `b55e773` veryhard-1 (human '**2 go R1-R8, 3 +1**'; 8 audit-verified PubChem 3D physiological records; audit at `08.1-08-protonation-audit.md`, header APPLIED 2026-10-05).

## Issues Encountered

- ONE Rule-1 auto-fix in Task 1 (`0fb3d7d` front-offset noise floor) — recorded at the time in the checkpoint return + STATE Phase-8 Decisions.
- Task-2 probe-side transcription bugs (`_cross` typo + `_alignment_matrix` diagonal corruption) root-caused via an isolation rig BEFORE any verdict — never a product defect; shipped smokes byte-correct throughout (full record in STATE Phase-8 Decisions, 2026-09-27).

## Next Phase Readiness

- **All four ROADMAP Phase-8 criteria + the DETECT-03 revisit carry closed verdicts**; Phase 8 execution records are COMPLETE (11/11 SUMMARYs present).
- **Verifier sequencing honored (CONTEXT constraint 8):** Phase 8's `/gsd-verify-phase` now runs on the FINAL corrected tree (`b13f6bb` + this record — 940/940 WSL, smokes 01–22) AFTER Phase 8.1 landed; Phase 8 and 8.1 are ready for their verifiers together.
- Phase 8.2 (Direction-Control Restoration, inserted 2026-10-05) and Phase 9 inherit the final curated data state and the modal-parity / representation laws this phase's fix batches established.

---
*Phase: 08-demo-curation-citations*
*Completed: 2026-10-05*
