# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-05)

**Core value:** The player can place amino acids onto a small molecule in the PyMOL 3D viewer and the game correctly detects and scores the interactions they form — turning unguided 3D manipulation practice into a scored game.
**Current focus:** Phase 1 — Bootstrap & Pure Foundation

## Current Position

Phase: 1 of 9 (Bootstrap & Pure Foundation)
Plan: 4 of 9 complete (wave 1 of 3 merged: 01-01, 01-02, 01-03, 01-04)
Status: Executing — wave 2 next (01-05 setup_state, 01-06 level_spec, 01-07 headless smoke)
Last activity: 2026-09-05 — Wave 1 executed in parallel worktrees, merged clean to main (9df4ea0); combined suite 64 tests OK

Progress: [████░░░░░░] 44% (4/9 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 4 (01-01…01-04)
- Average duration: ~30 min/plan (only 01-03 self-reported: 30 min)
- Total execution time: —

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 4/9 | — | — |

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

### Pending Todos

- Sibling plans: do NOT re-create `tests/__init__.py` (exists since 01-01).
- 01-09 [HUMAN] Plugin-Manager install checkpoint pending (wave 3).

### Blockers/Concerns

Upcoming human gates/spikes from research (not blockers for Phase 1):

- Phase 2 gate: threshold table needs human transcription + approval before detector freeze (DETECT-03)
- Phase 3 spike: movement model (`cmd.drag(wizard=0)` interplay, default `editor_scheme`) is UNVERIFIED — run headless spike before freezing
- Phase 7 gate: `.pse` matrix round-trip smoke before committing checkpoint design

## Session Continuity

Last session: 2026-09-05
Stopped at: Wave 1 of Phase 1 complete (01-01…01-04 merged, 64 tests OK); paused per user before wave 2
Resume file: None

## Next Actions

- Continue `/gsd-execute-phase 1` — wave 2 (01-05, 01-06, 01-07), then wave 3 (01-08, 01-09 [HUMAN checkpoint])
