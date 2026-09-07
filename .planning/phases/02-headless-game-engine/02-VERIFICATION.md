---
phase: 02-headless-game-engine
verified: 2026-09-07T00:00:00Z
status: passed
score: 5/5 must-haves verified
re_verification: null
human_verification: []
---

# Phase 2: Headless Game Engine — Verification Report

**Phase Goal:** The entire game works with no GUI at all: a human-approved threshold table drives a correct, vectorized detector; the seeded generator always produces solvable levels; bundled data materializes into real PyMOL objects; and generate → place → detect → score runs headlessly end-to-end on a scripted placement.
**Verified:** 2026-09-07
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP criterion) | Status | Evidence |
| --- | --- | --- | --- |
| 1 | [GATE] DETECT-03: threshold doc in-repo, every row cites published source, in-house resolutions recorded, human approval recorded BEFORE detector code | ✓ VERIFIED | `docs/DETECTION_THRESHOLDS.md` (511 lines): DOIs `10.1093/nar/gkaf361` (PLIP), `10.1186/s13321-021-00548-6` (ProLIF), `10.1016/j.jmgm.2011.01.004` (BINANA) each "verified from the project's own repository file" (§1.2); 82 PLIP/ProLIF/BINANA mentions; 10 rows each carry `Approval: date: 2026-09-06 approver: human gate, phase-2 plan 02-01 checkpoint`; §6 Approval record; `[RESOLVE]` markers document disagreements (e.g. C-F donor exclusion, Asp/Gln metal inclusion, His neutral-HIS v1 policy). **Git order:** approval commit `7214d66` (docs(02-01): record DETECT-03 human approval) precedes `735941d` (feat(02-06): approved threshold constants) and `b5fa47d` (feat(02-06): detector core). |
| 2 | [WSL] DETECT-01/02/04: detector classifies scripted geometries for all 7 types, explicit partner sides, single typing home, D1 side-chain-only | ✓ VERIFIED | `aamatch/detector.py` (1188 lines) has all 7 record functions (`_h_bond_records`, `_salt_bridge_records`, `_hydrophobic_records`, `_pi_stacking_records` with T-shaped subtype, `_cation_pi_records`, `_halogen_records`, `_metal_records`); canonical order from `INTERACTION_TYPES` (`_TYPE_ORDER`, records sorted by enum position). Single typing home: detector imports `from .capability import` (line 160); generator imports `aa_capable, ligand_support` from capability (line 95); `tests/test_detector.py:1081` proves records ordered by `INTERACTION_TYPES.index`. D1: `capability.py` §"D1 -- SIDE-CHAIN-ONLY capability" with per-AA `side_chain` atom-name sets. All covered in the green suite (test_detector.py 1712 lines, grep hits per type: h_bond 17, salt_bridge 9, pi_stacking 14, cation_pi 8, hydrophobic 23, halogen 34, metal 10). |
| 3 | [WSL] GEN-01/03/04/05: generator invariants over ≥100 seeds — solvable by construction, NxN grids, globally disjoint slots, difficulty via grid N / type count / size class, monotonic escalation, byte-determinism, version stamps | ✓ VERIFIED | `tests/test_generator_invariants.py` (750 lines): `SEEDS = list(range(100))`, documented corpus "18 configurations x 100 seeds = 1800 payloads"; tests A1 byte-determinism, A2 roundtrip through level-spec gates, A3 version stamps, B5 required-coverage dedicated slots, B6 can_form truthfulness vs `aa_capable/ligand_support`, C9 grid shape (NxN), C12 cross-molecule GLOBAL disjointness, D14 monotonic escalation. All green in the 531-test run. |
| 4 | [HEADLESS] GEN-02: count-asserted E2E smoke — generate → materialize (sentinels, protonation, bond orders) → scripted placement → detection → binary fraction score; rotation invariance; reset | ✓ VERIFIED | `bash smoke/run_smoke.sh smoke/smoke_04_e2e.py 240` → **`=== SMOKE-04 PASS ===`** with 25 count-asserted checks: materialize grew=10 (1 ligand + 9 slots), sentinels, scripted TYR ring placement (drift 2.4e-07), detect finds pi_stacking (records=1), score 1.0 after placement / 0.0 at grid, whole-scene rotation re-detects identically (dist drift 2.61e-09), score survives rotation, `reset_to_grid` restores poses (worst 2.9e-07). Sentinels in code: `placement.py` `SENTINEL_SEGI='AAM'`, `SENTINEL_B=-999.0`; bond orders via `geometry.py` bond-block extraction; protonation recorded in manifest/level_spec. |
| 5 | [HEADLESS] DETECT-05: perf smoke on largest bundled molecule inside budget, vectorized/spatially pruned (AST-audited), detector_version stamped + stale spec refused | ✓ VERIFIED | `bash smoke/run_smoke.sh smoke/smoke_05_perf.py 240` → **`=== SMOKE-05 PASS ===`**: largest manifest entry (benzamide, heavy=9) at max 9x9 grid (82 objects, 1285 atoms): **detect 11.238 ms < 100 ms**, **extract+detect 21.805 ms < 1000 ms**; fresh payload stamped `'det-1'` parses; stale `'det-0'` refused: `FormatError: unsupported detector_version 'det-0' ... regenerate it with a current AA-match generator`. Mechanical AST audit in the permanent suite: `tests/test_code_audit.py` (377 lines) — detector imports AND calls `cross_pairs`, no nested record/pair loops, `cross_pairs` itself has no O(N·M) double loop, banned calls (`get_model`, `matrix_reset`, `get_object_ttt`) absent (allowed prose pinned exactly), plus 3 negative controls proving the finders fire. Zero `get_model` hits in `aamatch/detector.py`. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `docs/DETECTION_THRESHOLDS.md` | Approved table (10 rows) + capability table (20 AAs) + decisions + approval record, ≥150 lines | ✓ VERIFIED | 511 lines, APPROVED status, per-row Approval lines, §6 record |
| `aamatch/thresholds.py` | Constants with citations, ≥80 lines | ✓ VERIFIED | 188 lines; every constant block cites gate § + source reasoning (PLIP/ProLIF/BINANA majority notes) |
| `aamatch/capability.py` | AA_RESIDUES, AA_TOKENS, ligand_profile, ligand_support, aa_capable, residue_capabilities, ligand_has_metal, ≥200 lines | ✓ VERIFIED | 712 lines; imports `from .vec3 import` (planarity fallback); D1 + no-itertools recorded |
| `aamatch/detector.py` | Full 7-type pipeline, ≥200 (part 1) / ≥1000 (final) lines | ✓ VERIFIED | 1188 lines; imports thresholds + capability + spatial.cross_pairs; no get_model |
| `aamatch/generator.py` | GRID_SPACING/GAP_MARGIN/INTER_GRID_MARGIN, difficulty_params, slot_position, derive_required, allocate_slots, generate, GenerationError, ≥250 lines | ✓ VERIFIED | 879 lines; stamps `DETECTOR_VERSION` + `LEVEL_SPEC_VERSION` into payload (lines 717, 875) |
| `aamatch/game_state.py` | score(required, results) + GameState, ≥80 lines | ✓ VERIFIED | 208 lines; binary-per-interaction (≥1 record ⇒ formed); validates `r['type']` against `INTERACTION_TYPES` |
| `aamatch/placement.py` | materialize, reset_to_grid, translate_to, transform_baked, cleanup_game_objects, ≥150 lines | ✓ VERIFIED | 405 lines; sentinels via `cmd.alter`+`cmd.sort`; uses `capability.AA_TOKENS` + `to_windows_path(package_data_path('data', ...))` |
| `aamatch/engine.py` | new_game, materialize, place_aa, reset_to_grid, detect, score_current, confirm, ≥120 lines | ✓ VERIFIED | 305 lines; `detector.detect` (7-type surface), `game_state` composition, no Qt |
| `tests/test_generator_invariants.py` | ≥100-seed suite | ✓ VERIFIED | 750 lines, 100 seeds × 18 configs = 1800 payloads |
| `tests/test_code_audit.py` | Mechanical AST audit | ✓ VERIFIED | 377 lines, permanent suite member, negative controls |
| `smoke/smoke_04_e2e.py` | Count-asserted E2E, ≥120 lines | ✓ VERIFIED | 498 lines, SMOKE-04 PASS (25 checks) |
| `smoke/smoke_05_perf.py` | Perf + stamp gate, budgets asserted | ✓ VERIFIED | 401 lines, `DETECT_BUDGET_MS=100.0` / `TOTAL_BUDGET_MS=1000.0`, SMOKE-05 PASS |

### Key Link Verification (sampled plans)

| From | To | Via | Status | Evidence |
| --- | --- | --- | --- | --- |
| `aamatch/detector.py` | `aamatch/thresholds.py` | `from .thresholds import` (02-06/02-07b) | ✓ WIRED | line 176 |
| `aamatch/detector.py` | `aamatch/capability.py` | single typing home (DETECT-04) | ✓ WIRED | line 160 |
| `aamatch/detector.py` | `aamatch/spatial.py` | `cross_pairs` ONLY candidate source | ✓ WIRED | lines 159, 633-637; audit-enforced |
| `tests/test_detector.py` | `setup_state.INTERACTION_TYPES` | canonical 7-type order (02-07b) | ✓ WIRED | lines 30, 1081 |
| `aamatch/generator.py` | `aamatch/capability.py` | pools + feasibility (02-08) | ✓ WIRED | line 95 |
| `aamatch/generator.py` | `aamatch/level_spec.py` | DETECTOR_VERSION stamped (02-08) | ✓ WIRED | lines 96, 717, 875 |
| generator `can_form` | detector typing | cross-check (02-08 claim) | ✓ WIRED (located in `tests/test_generator_invariants.py` B6, not test_generator.py — same proof, different file) | lines 44, 356-379: can_form validated against `aa_capable`/`ligand_support` enum + role accounting |
| `aamatch/game_state.py` | `setup_state.INTERACTION_TYPES` | formed-type bookkeeping (02-10) | ✓ WIRED | lines 40, 42, 55 |
| `aamatch/placement.py` | `capability.AA_TOKENS` | ONE vocabulary (02-13) | ✓ WIRED | lines 108-114 (reverse map built from AA_TOKENS) |
| `aamatch/placement.py` | `aamatch/paths.py` | `to_windows_path` before `cmd.load` (02-13) | ✓ WIRED | line 75 |
| `aamatch/engine.py` | `aamatch/detector.py` | extract → pure detect (02-14) | ✓ WIRED | lines 271-278 |
| `aamatch/engine.py` | `aamatch/game_state.py` | score_current → score(required, results) (02-14) | ✓ WIRED | lines 45-47, 281-287 |
| `smoke/smoke_04_e2e.py` | `aamatch/engine` | engine ops drive E2E (02-14) | ✓ WIRED | line 85 import; ops called at lines 222-265 |
| `aamatch/capability.py` | `aamatch/vec3.py` | dihedral/angle planarity fallback (02-05) | ✓ WIRED | line 57 |
| `aamatch/thresholds.py` | `docs/DETECTION_THRESHOLDS.md` | row-by-row transcription + approval date (02-01→02-06) | ✓ WIRED | constants cite gate § rows and 2026-09-06 approval |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
| --- | --- | --- |
| DETECT-01 | ✓ SATISFIED | — (5 types: h_bond, salt_bridge, pi_stacking incl. T-shaped, cation_pi, hydrophobic) |
| DETECT-02 | ✓ SATISFIED | — (halogen ligand-side Cl/Br/I only, C-F excluded; metal gated by `ligand_has_metal`) |
| DETECT-03 | ✓ SATISFIED | — (gate doc + approval commit order proven) |
| DETECT-04 | ✓ SATISFIED | — (records carry `aa{...}` / `lig{...}` partner sides; capability is the single home; tests prove agreement) |
| DETECT-05 | ✓ SATISFIED | — (SMOKE-05 budgets + AST audit + version-stamp refusal) |
| GEN-01 | ✓ SATISFIED | — (D14: exactly D levels for every legal D, monotonic escalation) |
| GEN-02 | ✓ SATISFIED | — (SMOKE-04/05: materialize with sentinels, bond orders from SDF, protonation in manifest/spec) |
| GEN-03 | ✓ SATISFIED | — (C9 NxN grid shape, C12 global disjointness, gap/spacing asserts C10-C13) |
| GEN-04 | ✓ SATISFIED | — (B5/B6: solvable-by-construction, dedicated required slots, truthful can_form, distractors) |
| GEN-05 | ✓ SATISFIED | — (difficulty via grid_n 3..9 / size class / required-type count; mode semantics B7) |

Note: `.planning/REQUIREMENTS.md` tracker rows for these IDs still read "Pending" — bookkeeping only, no code impact (orchestrator updates the tracker).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `aamatch/__init__.py` | 29 | "Phase-1 placeholder" prose | ℹ️ Info | Intentional: Qt-free bootstrap from Phase 1; engine composition lives in engine.py; GUI lands Phases 3-5. Not a phase-2 stub. |
| `aamatch/backup.py` | 4 | "not implemented in open-source" | ℹ️ Info | Quoted prior-art text explaining an API workaround, not a stub. |

No TODO/FIXME/blocking stub patterns in any phase-2 artifact. No sys.modules stubs (grep hits are prose in docstrings explaining why stubs are NOT used). No itertools/numpy/dataclasses in pure modules (prose notes only).

### Gate Evidence (standing gates, AGENTS.md)

- `python3.6 -m py_compile aamatch/*.py` → PASS
- `python3.6 -m unittest discover -s tests` → **Ran 531 tests in 30.707s — OK** (includes `tests/test_purity.py`: 13 PURE_MODULES AST scan + clean subprocess + negative control)
- SMOKE-02 → `=== SMOKE-02 PASS ===`; SMOKE-03 → `=== SMOKE-03 PASS ===`; SMOKE-04 → `=== SMOKE-04 PASS ===` (25 checks); SMOKE-05 → `=== SMOKE-05 PASS ===` (21 checks, budgets met with ~9x/46x headroom)

### Human Verification Required

None — Phase 2 is WSL/headless-verifiable by design. All five criteria carry programmatic or headless-smoke proof. (The GUI human gates belong to Phases 3-5.)

### Gaps Summary

None. All 5 ROADMAP success criteria are verified against the merged code: the approval gate precedes detector code in git history; the detector is substantively complete (1188 lines, 7 types, cross_pairs-only candidate routing, AST-audited); the generator proves solvability/determinism over 1800 payloads; the E2E smoke proves generate → materialize → place → detect → score → rotation-invariance → reset headlessly with count assertions; and the perf smoke proves vectorized detection 9x inside the detect budget on the largest bundled molecule with a working version-stamp refusal gate.

---

_Verified: 2026-09-07_
_Verifier: OpenCode (gsd-verifier)_
