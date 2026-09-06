# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-05)

**Core value:** The player can place amino acids onto a small molecule in the PyMOL 3D viewer and the game correctly detects and scores the interactions they form — turning unguided 3D manipulation practice into a scored game.
**Current focus:** Phase 2 — Headless Game Engine

## Current Position

Phase: 2 of 9 (Headless Game Engine)
Plan: 2 of 15 (02-02 complete — executed in PARALLEL with 02-01 on branch exec/02-02; merge order handled by orchestrator)
Status: In progress
Last activity: 2026-09-06 — Completed 02-02-PLAN.md (vec3 + spatial pure geometry primitives, TDD, 163/163 tests)

Progress: [████░░░░░░] 42% of project plans (10/24: Phase 1 9/9 + Phase 2 1/15)

## Performance Metrics

**Velocity:**
- Total plans completed: 10 (Phase 1: 01-01…01-09; Phase 2: 02-02)
- Average duration: —
- Total execution time: —

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 9/9 ✓ | — | — |
| 2 | 1/15 | ~8 min (02-02) | 8 min |

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
- (02-02) `vec3.py` floats-in/floats-out contract via float() coercion (int tuples never leak); `unit()`/`angle_at()` raise ValueError on zero-length arms (fail-closed); angle_at clamps cos to [-1,1] vs float rounding near 0/pi; `plane_project` requires a UNIT normal (documented, no re-normalization).
- (02-02) `spatial.py`: cell size == cutoff makes the 3×3×3 neighbourhood scan provably exhaustive (100-seed equivalence vs brute-force oracle proven); cell keys = int(x // cell) FLOOR division (negatives correct); `brute_force_pairs` is test-oracle-only — docstring carries the 02-15 audit-grep phrase, pinned by a unit test.
- (02-02) PURE_MODULES now 7 (`+ vec3, spatial`); ALLOWED_STDLIB untouched (math already whitelisted; spatial imports only `from .vec3 import dist`; itertools stays out per 02-01). Phase-2 pure-module pattern established: RED test commit → GREEN feat commit → PURE_MODULES registration as test commit.

### Pending Todos

- Keep `aamatch/` pycache-free (live plugin-path loading runs from the repo; human cleans after local test runs).
- Generalize `smoke/run_smoke.sh` marker grep beyond SMOKE-01 when Phase 2 smokes arrive.
- (Optional) Annotate 01-RESEARCH-plugin-install.md §1.3/§3.1: `load()` return ≠ `loaded` property; `__file__` unusable in `-cq` scripts.

### Blockers/Concerns

Upcoming human gates/spikes from research (not blockers for Phase 1):

- **Phase 2 gate (NOW THE NEXT CONCERN): threshold table needs human transcription + approval before detector freeze (DETECT-03)** — sequence as Phase 2's first plan
- Phase 3 spike: movement model (`cmd.drag(wizard=0)` interplay, default `editor_scheme`) is UNVERIFIED — run headless spike before freezing
- Phase 7 gate: `.pse` matrix round-trip smoke before committing checkpoint design

## Session Continuity

Last session: 2026-09-06 (02-02 executor, worktree tmp/exec-02-02, branch exec/02-02)
Stopped at: Completed 02-02-PLAN.md (5 commits: d26d219, f31e474, 221f99e, 9f9ec65, 4b85861; SUMMARY at .planning/phases/02-headless-game-engine/02-02-SUMMARY.md)
Resume file: None

## Next Actions

- Orchestrator: merge exec/02-02 (and exec/02-01) back in dependency order, then continue Phase-2 wave 2 (02-03+)
- Detector plans 02-06/07 consume `spatial.cross_pairs` + `vec3` per-candidate math
