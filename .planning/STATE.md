# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-05)

**Core value:** The player can place amino acids onto a small molecule in the PyMOL 3D viewer and the game correctly detects and scores the interactions they form — turning unguided 3D manipulation practice into a scored game.
**Current focus:** Phase 2 — Headless Game Engine

## Current Position

Phase: 2 of 9 (Headless Game Engine) — In progress
Plan: 8 of 16 complete (waves 1-5 + 02-08; 02-07 SPLIT 2026-09-06 into 02-07 [pi+cation-pi, wave 6] + 02-07b [halogen+metal+canonical, wave 7] after 6 silent spawn failures across models/prompt shapes; downstream re-waved: 02-11 -> wave 8 needs 02-07b, 02-14 adds 02-07b dep)
Status: PAUSED 2026-09-06 — split committed, awaiting opencode restart (model switch) before respawning 02-07; exec/02-08 branch holds the completed generator (unmerged: 7 commits, 423/423, 9 recorded deviations — deviation 3 binds the cmd tier: ligand_data must carry 'profile', engine (02-14) wires capability.ligand_profile over extracted records)
Last activity: 2026-09-06 — 02-08 (generator, exec/02-08) + 02-09 (geometry, merged) complete; split + re-wave committed

Progress: [█████░░░░░] 47% of Phase 2 (7/15) · [███████████░] 92% of project (phase 2 of 9; plans 22/24)

## Performance Metrics

**Velocity:**
- Total plans completed: 16 (Phase 1: 01-01…01-09; Phase 2: 02-01…02-06, 02-09)
- Average duration: ~11 min (02-03); 6 min (02-04); ~29 min (02-05); 23 min (02-06); 4 min (02-09)
- Total execution time: —

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 9/9 ✓ | — | — |
| 2 | 7/15 | ~8 min (02-02) + ~25 min (02-01 cont.) + 11 min (02-03) + 6 min (02-04) + 29 min (02-05) + 23 min (02-06) + 4 min (02-09) | — |

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

### Pending Todos

- Keep `aamatch/` pycache-free (live plugin-path loading runs from the repo; human cleans after local test runs).
- (Optional) Annotate 01-RESEARCH-plugin-install.md §1.3/§3.1: `load()` return ≠ `loaded` property; `__file__` unusable in `-cq` scripts.

### Blockers/Concerns Carried Forward

- **Phase 2 gate DETECT-03: RESOLVED (approved 2026-09-06, provisional pending Phase-8 dataset revisit)** — plans 02-05..02-08 transcribe constants from docs/DETECTION_THRESHOLDS.md row-by-row; the units/atom-typing check passed at approval.
- Phase 3 spike: movement model (`cmd.drag(wizard=0)` interplay, default `editor_scheme`) is UNVERIFIED — run headless spike before freezing
- Phase 7 gate: `.pse` matrix round-trip smoke before committing checkpoint design

## Session Continuity

Last session: 2026-09-06 (02-09 executor on worktree branch exec/02-09 — wave-5 parallel protocol; do NOT merge/push from the agent)
Stopped at: Completed 02-09-PLAN.md — aamatch/geometry.py cmd-tier bridge (probe-proven, 346/346 tests, purity untouched)
Resume file: None

## Next Actions

- Orchestrator (AFTER opencode restart / model switch): spawn 02-07 (pi+cation-pi only — small scope); merge exec/02-08 + exec/02-07 when both return (STATE.md conflict expected — combine); then wave 7 = 02-07b / 02-10 / 02-12 / 02-13, wave 8 = 02-11 / 02-14, wave 9 = 02-15
- 02-10 (engine): wire detect() = extract_game_atoms() + ligand_bonds() with the probe-pinned remap — bond position i → index_to_id[i+1] → atom id → position in the (object, id)-sorted ligand records; bounding_sphere() output feeds generate(..., ligand_data, ...) as {'centroid', 'radius'}
- SMOKE-03 (02-13): assert features['unclassified_aa_atoms'] == 0 per materialized AA; reconcile cap-atom naming by extending the detector's known non-side-chain set if needed (never thresholds)
- SMOKE-03/04/05 need NO runner changes (marker-deriving run_smoke.sh handles any smoke_NN_name.py); geometry helpers are import-ready for all three
- Fixture geometry (benzamide xy-plane pose, acetate tetrahedral methyl) is stable for 02-13 placement scripting and 02-14 E2E poses; pose asserts use 1e-6 tolerance (float32)
