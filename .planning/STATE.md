# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-05)

**Core value:** The player can place amino acids onto a small molecule in the PyMOL 3D viewer and the game correctly detects and scores the interactions they form — turning unguided 3D manipulation practice into a scored game.
**Current focus:** Phase 2 — Headless Game Engine

## Current Position

Phase: 2 of 9 (Headless Game Engine) — In progress
Plan: 4 of 15 complete (wave 3: 02-04 fixtures + MANIFEST.json + generalized runner + SMOKE-02 done; next: 02-05 detector constants transcription)
Status: In progress — data supply PROVEN (SMOKE-02 count-exact on both fixtures; manifest schema frozen and exercised)
Last activity: 2026-09-06 — Completed 02-04-PLAN.md (benzamide/acetate SDFs, sha256-pinned MANIFEST.json accepted by the 02-03 gate, run_smoke.sh NN-deriving, SMOKE-02 PASS first boot; 211/211 tests)

Progress: [███░░░░░░░] 27% of Phase 2 (4/15) · [█████░░░░░] 54% of project (phase 2 of 9; plans 13/24)

## Performance Metrics

**Velocity:**
- Total plans completed: 13 (Phase 1: 01-01…01-09; Phase 2: 02-01, 02-02, 02-03, 02-04)
- Average duration: ~11 min (02-03); 6 min (02-04)
- Total execution time: —

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 9/9 ✓ | — | — |
| 2 | 4/15 | ~8 min (02-02) + ~25 min (02-01 cont.) + 11 min (02-03) + 6 min (02-04) | — |

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

### Pending Todos

- Keep `aamatch/` pycache-free (live plugin-path loading runs from the repo; human cleans after local test runs).
- (Optional) Annotate 01-RESEARCH-plugin-install.md §1.3/§3.1: `load()` return ≠ `loaded` property; `__file__` unusable in `-cq` scripts.

### Blockers/Concerns Carried Forward

- **Phase 2 gate DETECT-03: RESOLVED (approved 2026-09-06, provisional pending Phase-8 dataset revisit)** — plans 02-05..02-08 transcribe constants from docs/DETECTION_THRESHOLDS.md row-by-row; the units/atom-typing check passed at approval.
- Phase 3 spike: movement model (`cmd.drag(wizard=0)` interplay, default `editor_scheme`) is UNVERIFIED — run headless spike before freezing
- Phase 7 gate: `.pse` matrix round-trip smoke before committing checkpoint design

## Session Continuity

Last session: 2026-09-06 (02-04 executed in worktree tmp/exec-02-04 on branch exec/02-04 — wave-3 parallel protocol; task commits 6a65dc8, fe7fb92, 4962551)
Stopped at: Completed 02-04-PLAN.md — 02-04-SUMMARY.md written, SMOKE-01+SMOKE-02 both PASS via generalized runner, full suite 211/211 green
Resume file: None

## Next Actions

- Orchestrator: merge exec/02-04 back in wave-3 dependency order, then proceed per plan frontmatter — 02-05..02-07 (detector/capability constants transcribed row-by-row from docs/DETECTION_THRESHOLDS.md), 02-08 (generator consumes enumerate_entries over aamatch/data/MANIFEST.json; DETECT-05 target via largest_entry -> benzamide)
- SMOKE-03/04/05 need NO runner changes (marker-deriving run_smoke.sh handles any smoke_NN_name.py)
- Fixture geometry (benzamide xy-plane pose, acetate tetrahedral methyl) is stable for 02-13 placement scripting and 02-14 E2E poses
