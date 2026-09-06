# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-05)

**Core value:** The player can place amino acids onto a small molecule in the PyMOL 3D viewer and the game correctly detects and scores the interactions they form — turning unguided 3D manipulation practice into a scored game.
**Current focus:** Phase 2 — Headless Game Engine

## Current Position

Phase: 2 of 9 (Headless Game Engine) — In progress
Plan: 13 of 16 complete on main — **wave 7 COMPLETE** (02-07b + 02-10 + 02-12 + 02-13 all merged; waves 1-6 before that)
Status: **Detector COMPLETE — all 7 types via detect()** (DETECT-01/02 done) + pure seeded generator + score/GameState + >=100-seed invariant suite (criterion 3 SATISFIED) + cmd-tier placement with SMOKE-03 PASS 28/28 (ligand_data profile contract PROVEN end-to-end); PURE_MODULES = 13
Last activity: 2026-09-06 — 02-13 (placement.py + SMOKE-03) merged; wave 8 = 02-11 / 02-14 next

Progress: [████████░░] 81% of Phase 2 (13/16) · [███████████░] 92% of project (phase 2 of 9; plans 26/25)

## Performance Metrics

**Velocity:**
- Total plans completed: 19 (Phase 1: 01-01…01-09; Phase 2: 02-01…02-09, 02-13)
- Average duration: ~11 min (02-03); 6 min (02-04); ~29 min (02-05); 23 min (02-06); 4 min (02-09); 11 min (02-07); 17 min (02-08); ~20 min (02-13)
- Total execution time: —

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 9/9 ✓ | — | — |
| 2 | 10/16 (02-12 pending merge) | ~8 min (02-02) + ~25 min (02-01 cont.) + 11 min (02-03) + 6 min (02-04) + 29 min (02-05) + 23 min (02-06) + 4 min (02-09) + 11 min (02-07) + 17 min (02-08) + 45 min (02-12) | — |

**Recent Trend:**
- Last 5 plans: —
- Trend: —

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table. Seeded from PROJECT.md at roadmap creation:

- v1 = PyMOL plugin only; VMD port deferred to v2
- Interaction detection implemented in-house from standard geometric criteria (zero-extra-deps)
- v1 interaction set: H-bond, salt bridge (ionic folded in), π-stacking, cation-π, hydrophobic, halogen, metal coordination (conditional on metal in ligand)
- Score = fraction of required interactions formed, binary per interaction; skip stores partial score
- Levels always solvable by grid generation
- Demo sets: agent proposes with citations → human approves → fetch/commit
- No helper visuals during gameplay (Hint = carbon recolor only)
- (Roadmap) Phases 1–3 isolate the risky unknowns pre-Qt: pure foundation → data + cmd-only headless engine → wizard interaction; Qt concentrated in Phases 4–7; demos late (8); docs last (9)
- (User, 2026-09-05) Some UI/mechanism code may be **borrowed from bioCHEMeleon** (`tmp/bioCHEMeleon/biochemeleon/` — git-ignored, main-repo path): Qt dialog patterns, wizard picking, persistence/backup, help/tooltip patterns. Adapt, don't vendor wholesale.
- (01-01) `aamatch/__init__.py` composition root has ZERO module-level imports (not even stdlib) — permanent zero-stubs proof; `addmenuitemqt` called FIRST inside `__init_plugin__`.
- (01-02) Atomic write via `os.fdopen(fd,'wb')` context manager + guarded cleanup; refuse-newer/accept-older container policy; canonical refusal message phrasing (`not an AA-match file` / `unsupported AA-match format version…` / `expected an AA-match <kind> file`) — 01-05/01-06 must reuse it.
- (01-03) Backup bytes self-describing: `sha256hex + b'\n' + canonical JSON`; `verify_intact` returns False on corruption, raises on missing key; simple-filename/path-traversal key guard applied to BOTH stores; cmd-tier adapter deferred (`BACKUP_OBJECT_PREFIX` documented).
- (01-04) `to_windows_path` ported verbatim incl. load-bearing `len(parts)==4` term; case-9 asymmetry pinned (`/mnt/c` unchanged, `/mnt/c/` → `C:\`); all cmd.load/save/file call sites must route through it.
- (01-05) Setup defaults in code: molecules 2/1/10, difficulty 3/1/9, `interaction_mode` "unset" — **pending human re-confirmation at 01-09 checkpoint**; container header is the only format tag; non-dict validate input → defaults; JSON `null` counts as missing for str fields.
- (01-06) `detector_version` gate = exact-match ("stale or newer — regenerate"); `seed` must be a real int (bools excluded); parse API = container in, payload out; `can_form` NOT validated against setup_state's enum (independent schemas).
- (01-07) Headless smoke repo-root anchor = `sys.argv` first, cwd fallback — `__file__` unusable in `-cq` scripts; loader-contract assertion headless = `info.load()` verdict, NOT the `loaded` property; Windows env recorded: Python 3.9.13 / PyQt5 5.12.3 / Qt 5.12.9 / PyMOL 2.5.0 / numpy 1.25.2; fwdslash + space-path cmd.load probes both OK.
- (01-08) Purity is ENFORCED by tests/test_purity.py (AST scan all scopes + clean-subprocess + negative control pinning exactly 2 findings); checker is pure fn `find_bad_imports(src)`; **new pure modules must be added to `PURE_MODULES` in tests/test_purity.py to be gated**.
- (01-09, HUMAN verdict 2026-09-06) INSTALL-01 PASS via **PLUGIN-PATH method** (repo root added to PyMOL plugin path — repo edits live, no reinstall; dialog copy-install branch not exercised). Module identity: exactly ONE module object; **never ALSO copy-install** (two module objects → duplicate singletons). Setup defaults FROZEN for Phases 2+ (changes = version-bump event): molecules_per_level 2/1/10 · difficulty_levels 3/1/**10** (human-amended from 9, commit aef7c5e) · interaction_mode 'unset'.
- (02-01, HUMAN gate 2026-09-06) **DETECT-03 [GATE] APPROVED** — docs/DETECTION_THRESHOLDS.md is the frozen transcription source for 02-05..02-08. Key adoptions: H-bond 4.0 Å/≥140° (BINANA), salt bridge 5.5 Å group-center, π-stacking 5.5 Å/30°/2.0 Å one-category, cation-π 6.0 Å + 2.0 Å offset w/ PLIP ligand-side anti-artifact rule (OQ-4), metal 3.0 Å distance-only list {MG, ZN, FE, CA, MN, CU, NI, CO, CD} [OQ-7], ring-ID 15° fallback, MIN_DIST 0.5 Å.
- (02-01) Resolved typing deviations from research: **Met thioether-S H-bond acceptor EXCLUDED in v1**; **Asp/Glu carboxylate acceptors + Asp/Gln/Glu/His/Cys(S) metal chelators INCLUDED** (BINANA rules); **C-F halogen donors EXCLUDED** (ProLIF precedent). His = neutral in v1 (OQ-3/D2); hydrophobic pedagogical set ALA VAL LEU ILE PRO PHE MET TRP; D1 side-chain-only; OQ-1 mode semantics (exclusive = "any" scoped by allowed_interactions); itertools NOT whitelisted; single typing home = aamatch/capability.py.
- (02-01, HUMAN caveat) Approval is **PROVISIONAL**: values may need adjustment depending on the final curated dataset (Phase 8) — any revisit is a **DETECTOR_VERSION bump event, never a silent edit** (bump policy §4.7 of the gate doc).
- (02-02) `vec3.py` floats-in/floats-out contract via float() coercion (int tuples never leak); `unit()`/`angle_at()` raise ValueError on zero-length arms (fail-closed); angle_at clamps cos to [-1,1] vs float rounding near 0/pi; `plane_project` requires a UNIT normal (documented, no re-normalization).
- (02-02) `spatial.py`: cell size == cutoff makes the 3×3×3 neighbourhood scan provably exhaustive (100-seed equivalence vs brute-force oracle proven); cell keys = int(x // cell) FLOOR division (negatives correct); `brute_force_pairs` is test-oracle-only — docstring carries the 02-15 audit-grep phrase, pinned by a unit test.
- (02-02) PURE_MODULES now 7 (`+ vec3, spatial`); ALLOWED_STDLIB untouched (math already whitelisted; spatial imports only `from .vec3 import dist`; itertools stays out per 02-01). Phase-2 pure-module pattern established: RED test commit → GREEN feat commit → PURE_MODULES registration as test commit.
- (02-03) Manifest schema FROZEN for 02-04/02-08: 14 required entry keys per 02-RESEARCH-materialization.md §3.2; `file` must be forward-slash package-relative (backslash/absolute/`X:` drive refused — PITFALL 2); counts are real ints (bools refused), bond_order_counts = digit-string → positive int, flags real bools; negative formal_charge_sum legal. manifest_version gate strict `_is_int` + refuse-newer/accept-older like FORMAT_VERSION.
- (02-03) set_id/entry_id must be non-empty strings (enumerate_entries sort keys — non-strings would TypeError in sorted(), so they are validated with clear refusals); enumerate_entries returns new dicts + set_id sorted by (set_id, entry_id); largest_entry = max heavy_atom_count, ties-first (DETECT-05 selector, no special-cased field). KINDS += 'manifest' (additive; refusal messages unchanged). PURE_MODULES = 8. Empty sets list allowed (supply emptiness is the generator's concern).
- (02-04) Fixtures are SCRIPT-BUILT (tmp/build_fixtures.py, git-ignored): SDF counts consistent by construction; manifest counts derived from the same lists; sha256 taken over written bytes in the same run — NEVER hand-edit an SDF after manifest creation, regenerate instead. Benzamide carries the script-derived counts (16 atoms/16 bonds {"1":12,"2":4}), not the plan sketch (11 bonds omitted the 5 ring C-H); acetate matches its sketch exactly. Both ligands flag-free (metal/halogen false) per DETECT-03 policy; license=''/provenance={} are Phase-8 placeholders; set_id 'demo-dev-1' tier 'easy' = development set (not curated demo data).
- (02-04) run_smoke.sh generalization CLOSED the 02-02 pending todo: SMOKE-NN derived from basename via sed (empty -> 01 legacy fallback); optional TIMEOUT arg (default 120); SMOKE-01 recipe unchanged in behavior. SMOKE-02 shape frozen for reuse: pure container parsed INSIDE PyMOL, per-entry private _aam_tmp* object with delete-in-finally, get_bonds order-MULTISET comparison (0-based index caveat irrelevant — orders only), iterate with explicit space dict and no round() in the expression, element-scan cross-check of metal/halogen flags, final get_names('objects') leak check.
- (02-05) capability.py = THE single typing home (gate §4.2), transcribed row-for-row from the gate doc with `source:` comments; per-type capable sets + counts (h_bond 12, salt 4, pi 4, cation_pi 6, hydrophobic 8, halogen 9, metal 9) test-pinned; '>= 2 capable AAs per type' is a permanent invariant test. API: aa_capable(resn, itype, ligand_profile) is polarity-aware (D3 salt-bridge sign; D4 cation-pi either direction; h_bond DIRECTION-REFINED — AA donor needs ligand acceptor and vice versa, Rule-2 addition closing a solvability hole). AA_TOKENS = the one generator-token → fragment/resn/charge_class vocabulary (20 tokens; protonation variants additive-later). PURE_MODULES = 9.
- (02-05) Ligand typing contract: §5.1 atom records + bond block [(i,j,order)] 0-based; optional `formal_charge` governs charge groups when present, kekulé structure-only when absent (recorded decision; acid-OH guard added Rule 2 — COOH never anion); aromatic = bond orders (6-ring 3 non-adjacent doubles = alternation; 5-ring 2; all-4 markers; unmarked = single per MDL) with 15° dihedral fallback ONLY when cycle orders absent; donors fail-closed (O/N/S needs bonded H); acceptors = any O/N/S; halogen donors Cl/Br/I (C-F excluded); `RING_PLANARITY_FALLBACK_DEG = 15.0` lives in capability.py — 02-06 should reference it, not duplicate.
- (02-05, recorded tension) Gate §3.3 Met-row halogen cell says Y(S) but §3.5's resolved halogen set (9) excludes Met; the plan's transcription rule + §3.5 were followed (Met excluded) — reconcile the doc row at the next versioned review (§4.7 bump event, never silent).
- (02-05, for 02-13) side_chain naming = heavy atoms beyond CB + polar Hs (plan examples pin it; ALA/GLY empty; carbon Hs omitted); chempy fragments digit-prefix HIS ring H ('2HE' per probe) vs standard-PDB names transcribed — SMOKE-03 field-verifies and reconciles atom names in capability.py (never thresholds).
- (02-06) thresholds.py = the approved table as 18 named constants, one `source:` comment per constant (row # + published source + 2026-09-06 approval date; provenance scan test makes the truthfulness rule mechanical); MAX_CUTOFF computed from distance rows (=6.0); AA_PREFILTER_MARGIN=7.5 (research §5.2.2 headroom, >= MAX_CUTOFF pinned); METAL_ELEMENTS + the 15-deg fallback are RE-EXPORTS of capability's objects (assertIs) — single homes, never duplicates; docstring carries the §4.7 bump policy + the spatial cell-cutoff note.
- (02-06) detector core: features precompute ONCE (donor-H pairs, acceptors, hydrophobes, aromatic rings with row-9 center/normal/radius, charge-group centers, halogen C-X donors, metals) — halogen-X + metal atoms already sit in the shared cross_pairs point set so 02-07 adds classification only; candidates ONLY via cross_pairs over (near-AA side-chain atoms incl. CB) x (ligand typed atoms) at cell==cutoff; charge/ring feature pairs enumerated directly; NO full atom-set double loop.
- (02-06, recorded) Ligand guanidino center = centroid of the 3 bonded Ns (gate §2.3's "midpoint of 2 Ns" is the protein-side Arg pattern; isolated guanidinium has 3 equivalent Ns) — docstring-documented; revisit = DETECTOR_VERSION event. Ligand phosphate/sulfonate NOT typed (capability doesn't type them — DETECT-04 parity; extension = versioned capability change).
- (02-06, recorded) One record per (donor heavy, acceptor) with the best-angle attached H (ties -> lowest H id); hydrophobic = one binary-presence record per (AA, ligand) with carbon-set atom_ids; AA donor-H pairing GEOMETRIC (AA_H_ATTACH_MAX=1.5, typing-internal, naming-agnostic for chempy '2HE'); unclassified_aa_atoms = non-H atoms outside side_chain ∪ {N,CA,C,O,OXT,CB} — SMOKE-03 asserts zero on materialized geometry (cap-atom names may extend the known set during 02-13 field verification).
- (02-06, Rule 2 additions) apply_altloc_policy implemented pure-side (research §7.2 assigned it, plans didn't name it) + fail-closed validation: bond indices out of range / unknown side ('aa'|'lig' only — waters can never silently join) raise ValueError.
- (02-09) geometry.py = THE cmd-tier geometry boundary (NEVER in PURE_MODULES; Gate D compiles it): extract_game_atoms = ONE iterate_state pass over the ' or '-joined '_aam_'-prefixed objects (explicit space dict, no round(), uppercase ID) → 12-key detector-contract records sorted by (object, id); record['resi'] comes from the resv INT accessor (expression-space resi is a str — blank for SDF, insertion-coded for PDB — contract requires int).
- (02-09) get_bonds mapping pinned empirically: bond endpoints are 0-based walk positions; whole-object selection ⇒ position i → index_to_id[i+1] (probe showed walk order == index property 1..N). 02-10 remaps bond positions into sorted ligand record order via that map; detector validates fail-closed. Fragment AA atom ids may start at 0 — identity stays (object, id), never assume 1-based ids.
- (02-09) bounding_sphere filters side=='lig' internally and raises ValueError on ligand-less records (fail-closed: empty bounds would silently size grids / hand NaN to the generator's save guard); world frame == ligand-file frame under Phase-2 baked coords.
- (02-09, probe rule) pose read-back asserts use tolerance 1e-6 — PyMOL stores coords as float32, translate/untranslate roundtrips accumulate ~1e-7 (research §6.2's stated tolerance).
- (02-08) generator.py = the pure seeded producer (PURE_MODULES = 12): difficulty via INTEGER HALF-UP `(L*6 + (D-1)//2)//(D-1)` with grid_n = 3+frac, types = 1+frac (plan's inline "3 + frac*6" was impossible — violated its own 3..9/1..7 invariants; formula wins, D=3 rows 3/1/small 6/4/medium 9/7/large verified; derived D=10 L4 = 6/4 vs the hand sketch's 5/4 — research pre-authorizes monotonicity, not hand literals). `round(` banned from the module by a source-scan test.
- (02-08) RNG contract: master Random(seed) draws D*MOLECULES_CAP unit sub-seeds ONCE (fixed stride, setup-independent) — adding a molecule never shifts existing molecules' streams (byte-isolation tested); each unit consumed in fixed order pick -> protonation -> derive -> allocate; ALL randomness via randint/choice/sample/shuffle over sorted/fixed-order lists, never sets/dicts.
- (02-08) **ligand_data CONTRACT (binds 02-13/02-14):** entries = {'centroid', 'radius', 'profile'} keyed by (set_id, entry_id) tuples, or ONE shared dict; 'profile' is the capability.ligand_profile shape and the cmd tier must compute it (ligand atoms + bonds) alongside bounding_sphere. Missing profile degrades FAIL-CLOSED to empty (modes refuse rather than promise unsolvable levels) — geometry-only ligand_data cannot ground polarity-aware derivation (D3/D4).
- (02-08) Mode semantics wired: exclusive = 'any' scoped by allowed (empty -> refuse naming the setup field); block_exclusive = exact checked set (unsupported type -> refuse NAMING it; hydrophobic reachable ONLY here per OQ-5); unset = support-filtered sampling minus hydrophobic (OQ-5; only-hydrophobic -> refusal naming the policy; empty allowed -> support-filtered all-types draw per OQ-1 harmonized with the "unset never draws unsupported" edge ruling).
- (02-08) Solvability by construction: one dedicated role='required' slot per required item, can_form truthful via aa_capable (per-slot proven), distractors from the sorted 20-AA list; grid-too-small / no-capable-AA / count!=1 / AA_TOKENS vocabulary drift all refuse naming the cause. DETECT-04 cross-check: synthetic SER/VAL scene proves aa_capable <-> detect_part1 agree BOTH directions.
- (02-08) Molecule selection: size-class bucket filter with NEAREST-BUCKET supply fallback (ties -> easier; difficulty dict keeps the TARGET class) — the 2-small dev manifest must drive D>=2 games until Phase-8 curation; distinct per-level picks via per-unit rng.sample(available, 1) + dedup; candidates re-sorted defensively by (set_id, entry_id); molecule_id numbered WITHIN each level (mol-001.., level_index + molecule_id identify globally; keeps isolation byte-exact).

- (02-07) pi_stacking offset = MIN over BOTH cross-projections (each ring center into the opposite ring's plane) — PLIP pistacking's verified form (detection.py re-checked 2026-09-06); a one-sided projection cannot form the T-shaped case the plan scripts. Subtype P/T is a metric only; metrics = {d_center, angle_deg, offset, subtype}.
- (02-07) OQ-4 veto semantics = KEEP when amine-normal-vs-ring-normal <= 30 deg, REJECT when > 30 (PLIP pication `if not a > 30: keep`; gate row 4/§4.4) — applies ONLY to ligand ammonium N with EXACTLY 3 non-H substituents (PLIP tertamine), never to AA cations (asymmetry proven by test), never to quaternary/primary/secondary/guanidino; collinear planes cannot veto. The veto's 30 deg reuses thresholds.PISTACK_ANGLE_TOL_DEG (same approved value as PLIP's hardcoded 30; thresholds.py outside the plan's file set) — separating it into its own row-4 constant would be a DETECTOR_VERSION event (§4.7), never silent.
- (02-07) cation_pi record contract final: roles cation/ring per direction, metrics {d_center, offset, direction} with direction ∈ {'aa_cation_over_lig_ring', 'aa_ring_under_lig_cation'} (D4 both directions; distance <= 6.0 inclusive, offset < 2.0 strict — transcribed from the thresholds row comments).
- (02-07) detect_part1 emits 5 of 7 types; ligand ammonium groups carry a 'substituents' feature annotation (non-H neighbor points) consumed only by the veto — feature extension, not a typing change; plan case-(e) prose inversion recorded as a Rule-1 deviation in 02-07-SUMMARY.md (gate doc is authoritative).
- (02-07) Ring-type tests always scope asserts with _of_type: scripted aromatic ligand ring carbons qualify as hydrophobes, so an unscoped 'no records' assert can be faked by a hydrophobic hit; veto proofs use the perpendicular/parallel CONTROL PAIR pattern.
- (02-07b) detect() = THE complete 7-type surface (DETECT-01/02 done): shared `_pipeline` preamble + `_part1_records`; detect_part1 kept byte-identical 5-of-7 for 02-06..02-08 consumers. Halogen row 6: structurally (AA capability-named acceptor) × (ligand typed C-X); C-F has NO candidate (typing), AA-side halogen unrepresentable; windows INCLUSIVE tuples from thresholds; donor upper bound 195 inert on acos∈[0,180].
- (02-07b) Row-6 Y anchor (acceptor bond partner) paired GEOMETRICALLY: nearest non-H same-object atom within `HALOGEN_Y_ATTACH_MAX=2.0` (typing-internal epsilon, Rule-2 like AA_H_ATTACH_MAX; no partner → no candidate, fail-closed) — AA fragments have no bond block, so Y cannot come from connectivity. Recorded as new typing policy in detector docstring.
- (02-07b) Metal row 7: distance-only ≤3.0, chelator = capability acceptors only; GATED on `capability.ligand_has_metal` before enumeration (spy-pinned: metal-free ligand → `_metal_records` call_count==0). MET exclusion per §3.5 falls out of `acceptors=()` — no special-case code anywhere.
- (02-07b) Record contract FINAL: halogen {d_ax, donor_angle_deg, acc_angle_deg} roles acceptor/donor lig ids [C,X sorted]; metal {d_metal} roles chelator/metal. detect() output closed-set: len(INTERACTION_TYPES)==7 + canonical sort (enum position, aa object, aa ids, lig ids) + AA-permutation determinism — 438→463 green.
- (02-10) SCORE-01 in game_state.py: score consumes ONLY r['type'] from canonical records ('any' binary 0.0/1.0; 'list' = formed items / items; binary per item — record counts NEVER inflate); fail-closed refusals: empty items in 'list' mode (empty is the exclusive 'any' representation only), record missing 'type'/type outside INTERACTION_TYPES/non-dict, unknown mode.
- (02-10) GameState = plain data only (purity-kept: PURE_MODULES = 13, imports time + setup_state): record_molecule_result stores score + canonical-order formed types in ONE call (score/debrief can never drift); molecule key 'L{level}M{molecule}'; skip-path guidance = record partial score via the same call + increment skip_count; start_timer(now=None) stores a float anchor, rendering is a later QTimer phase's job; to_dict/from_dict lossless NOW (Phase 7 wraps it, never reshapes).
- (02-12) The invariant suite tests IMPLEMENTED semantics, not plan sketches: exclusive mode is vacuously covered (no items -> no dedicated slots; 'any' scoring is 02-10); corpus type-coverage aggregates ALL modes because hydrophobic-required is block_exclusive-only per OQ-5 (the suite also pins hydrophobic == 0 across the unset corpus); cross-seed distinctness is measured with the 'seed' echo stripped (raw bytes would trivially pass); exhaustive pairwise-spacing proofs use an O(k log k) sorted-x sliding window -- 1800-payload O(k^2) would dominate runtime for no added rigor.
- (02-12) Corpus health observed (recorded for the 02-15 audit): 100/100 distinct payloads per config (floor 95); all 20 AAs appear as distractors; 7/7 types required; r0c0 required in 9.8% of 600 unset units (< 50%); suite adds ~51 s under python3.6 (456/456 total, ~67 s full suite).
- (02-13) placement.py = the cmd-tier materializer (NEVER in PURE_MODULES): materialize(payload, level_index=0) builds ONE level (fresh `_aam_lig`/`_aam_aa` names — never load-into-existing), sentinel-tags every atom (segi='AAM', b=-999.0), bakes AAs to effective poses (grid_pose + placement.offset, camera=0, world frame); registry = slot_id -> (object, sorted ids) + pre_game_names snapshot. reset_to_grid = spec REPLAY re-bake (never matrix_reset — probe-proven reverter); cleanup_game_objects = prefix-only deletion. Banned-call docstring list binds 02-15's audit.
- (02-13) SMOKE-03 field-verified capability atom naming: materialized chempy fragments classify with unclassified_aa_atoms == 0 against the live detector — NO reconciliation edits to detector.py/_KNOWN_NON_SIDE_CHAIN or capability.py were needed (the pre-authorized escape hatch stayed unused, a STRONGER outcome than planned).
- (02-13) SMOKE-03 candidates are restricted to the benzamide row by construction: block_exclusive (correctly) refuses checked-but-unsupported types on aromatic-less molecules, so passing both manifest entries would make the smoke seed-fragile; diversity proofs stay with SMOKE-02.

### Pending Todos

- Keep `aamatch/` pycache-free (live plugin-path loading runs from the repo; human cleans after local test runs).
- (Optional) Annotate 01-RESEARCH-plugin-install.md §1.3/§3.1: `load()` return ≠ `loaded` property; `__file__` unusable in `-cq` scripts.

### Blockers/Concerns Carried Forward

- **Phase 2 gate DETECT-03: RESOLVED (approved 2026-09-06, provisional pending Phase-8 dataset revisit)** — plans 02-05..02-08 transcribe constants from docs/DETECTION_THRESHOLDS.md row-by-row; the units/atom-typing check passed at approval.
- Phase 3 spike: movement model (`cmd.drag(wizard=0)` interplay, default `editor_scheme`) is UNVERIFIED — run headless spike before freezing
- Phase 7 gate: `.pse` matrix round-trip smoke before committing checkpoint design

## Session Continuity

Last session: 2026-09-06 (wave-7 executors on kimi-k3: 02-07b / 02-10 / 02-12 / 02-13 — all four COMPLETE, all merged by orchestrator)
Stopped at: Wave 7 COMPLETE (13/16) — wave 8 next = 02-11 / 02-14, then wave 9 = 02-15
Resume file: None

## Next Actions

- Orchestrator: wave 8 = 02-11 (detector invariance/sensitivity suite) + 02-14 (engine + SMOKE-04) in parallel worktrees, then wave 9 = 02-15 (perf smoke + AST audit + detector-version stamp)
- **02-14 (SMOKE-04) reuses SMOKE-03's ligand_data pattern verbatim:** temp _aam_tmp load -> extract_game_atoms -> bounding_sphere + ligand_profile over remapped get_bonds -> {'centroid','radius','profile'} (02-08 deviation 3 contract, PROVEN end-to-end by SMOKE-03); scripted placement consumes translate_to/transform_baked; rotation-invariance Part B bakes whole-scene rotates with camera=0
- **02-14 (engine) wires detect() = extract_game_atoms() + ligand_bonds()** with the probe-pinned remap — bond position i → index_to_id[i+1] → atom id → position in the (object, id)-sorted ligand records; bounding_sphere() + ligand_profile feed generate(..., ligand_data, ...) keyed by (set_id, entry_id); productionize the smoke-local ligand_data build + bond remap helpers; scoring binds to detector.detect() (NOT detect_part1 — the 7-type surface)
- **02-13 SMOKE-03 note for 02-11/02-14:** a materialized AA fragment whose acceptor atom sits > 2.0 A from every non-H same-object atom is malformed — `HALOGEN_Y_ATTACH_MAX` doubles as a fragment sanity bound alongside the unclassified-atoms assertion
- **Banned-call audit for 02-15:** `grep matrix_reset|get_object_ttt aamatch/` must hit only placement.py's docstring prohibition list
- SMOKE-03 reconciler result: materialized chempy fragments classify 100% against capability atom naming (unclassified_aa_atoms == 0) — _KNOWN_NON_SIDE_CHAIN untouched; the pre-authorized detector.py escape hatch stayed UNUSED
- SMOKE-03/04/05 need NO runner changes (marker-deriving run_smoke.sh handles any smoke_NN_name.py); geometry helpers are import-ready for all three
- Fixture geometry (benzamide xy-plane pose, acetate tetrahedral methyl) is stable for 02-14 E2E poses; pose asserts use 1e-6 tolerance (float32)
