# AA-match

## What This Is

A PyMOL plugin implementing an educational matching game of small-molecule ↔ amino-acid interactions, for students and educators who want an engaging way to explore and study molecular interactions. Each level presents small molecules (specific protonation state, correct valence rendering) with an NxN grid of randomized amino acids around them; the player drags, rotates, and adjusts amino acids onto the small molecule to form targeted interactions, which the game detects from standard geometric definitions of atom types and geometry. No helper lines/dots during gameplay so players practice working in 3D.

## Core Value

The player can place amino acids onto a small molecule in the PyMOL 3D viewer and the game correctly detects and scores the interactions they form — turning unguided 3D manipulation practice into a scored game.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Installable as a standard PyMOL plugin (Plugin Manager), for testing purposes
- [ ] Setup window on plugin start with configurable parameters (demo set dropdown or user upload, molecules per level, difficulty levels, allowed-interactions list with exclusive/block-exclusive/random modes)
- [ ] Setup window bottom buttons: Reset, Randomize, Save Setup, Load Setup, Generate and export, Cleanup model, Start
- [ ] Game generation: multiple levels of increasing difficulty; each level has small molecules of specific protonation state with correct valence; NxN AA grid per molecule sized by difficulty
- [ ] Levels are always solvable: grid generation guarantees AAs able to form every required interaction are present (plus distractors)
- [ ] Gameplay in the OpenGL viewer: click AA to select (color change + selected status), drag/rotate/adjust onto the small molecule, click another AA or Confirm
- [ ] No helper lines/dots displayed during gameplay
- [ ] Game status tab: rolling info box, timer, required interaction types/counts (`any` or from allowed list), import game, Hint (recolor carbon atoms of AAs that could form one of the interactions), Confirm, Skip Mol/Give up (with confirmation warnings), Save (PyMOL session + game state), Restart, Reset (AAs back to grid)
- [ ] Start sequence: store initial state, generate representations per setup, jump to Game status tab, 3-2-1 countdown, start
- [ ] On molecule finish: calculate and show molecule score + running total, move to next molecule; on level finish, advance to higher difficulty
- [ ] Interaction detection from standard geometric criteria (own implementation, thresholds verified against published sources and human-approved) covering: H-bond, salt bridge (ionic folded in), π-stacking, cation-π, hydrophobic contact, halogen bond, metal coordination (when metal present in ligand)
- [ ] Score = fraction of required interactions successfully formed (binary per interaction); skip stores partial score
- [ ] End of game: per-level scores + total, stopped timer, winning message with time, molecules/levels, skip/give-up counts
- [ ] Demo sets: several curated options pre-downloaded, citing source in a doc; protonation/interactions from known binding databases; difficulties grouped by interaction-type count, molecule size, grid N

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- VMD port (v2) — PyMOL first; keep core viewer-agnostic where cheap, but no VMD work in this roadmap
- proLIF/PLIP/binana as runtime dependencies — zero-extra-deps constraint; detection implemented in-house
- Helper visuals (lines/dots/hints of geometry) during gameplay — would defeat the 3D-practice purpose (Hint button only recolors carbons)
- Network access at gameplay time — demo data is pre-downloaded and committed with citations

## Context

- Spec of record is `spec.md`; README is placeholder-only except the vibe-coding warning which must be kept.
- Prior art: `tmp/bioCHEMeleon/` — our previous PyMOL 2.5.0 plugin game with similar UI and mechanisms (wizard-based interaction, PyQt5 GUI, pure data layer with unit tests, headless cmd-only smoke tests). Reference only, git-ignored.
- Reference repos (git-ignored): `Pymol-script-repo/` (open-source plugins), `pymol-src/` (PyMOL 2.5.0 source for API verification with file:line citations).
- Dev in WSL Ubuntu; PyMOL 2.5.0 (anaconda) runs in a Windows conda env reachable via `setenv.bat`; headless PyMOL via `cmd.exe /c C:\src\run-conda-pymol.bat -cq <script>`. GUI/Qt paths cannot run from WSL — human-verify checkpoints.
- Demo set curation protocol: agent proposes candidates (PDB/SDF IDs, protonation/interaction sources) with citations → human verifies and approves → only then fetch/commit. README has ~9 tier slots (Easy ×3, Hard ×3, Challenge, Very challenging ×2).
- README demo table, Usage, Project Structure sections are TBD placeholders to be filled as reality emerges.

## Constraints

- **Environment**: WSL Ubuntu dev shell; do NOT install anything, no conda envs, no pip installs. `python3.6` for syntax checks and pure-layer unit tests only.
- **Dependencies**: only what `pymol-open-source` ships (PyQt5 via `pymol.Qt`, numpy). Any additional lib must be listed and explicitly user-approved, then vendored into `3rd_party_lib/` (git-ignored) with license noted.
- **Viewer**: PyMOL 2.5.0 (Windows conda env). Qt GUI cannot run from WSL; interactive gameplay is human-verified.
- **Truthfulness**: do NOT make up anything; ALL claims and citations (DOIs, PDB IDs, sources) must be verified against a source and explicitly approved by a human.
- **Code standards**: efficient, traceable, clean, safe; structured repo.
- **UI standards**: simple, user-friendly, clear but sufficient in-game explanation.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| v1 = PyMOL plugin only; VMD is a later port (v2) | Root AGENTS.md anticipates both; sequence risk | — Pending |
| Interaction detection implemented in-house from standard geometric criteria | Zero-extra-deps constraint; thresholds verified against published sources and human-approved | — Pending |
| v1 interaction set: H-bond, salt bridge (ionic included), π-stacking, cation-π, hydrophobic, halogen bond, metal coordination (conditional on metal in ligand) | Core five + user-added two; ionic folded into salt bridge | — Pending |
| Score = fraction of required interactions formed, binary per interaction | Simple, explainable to students; skip stores partial score | — Pending |
| Levels always solvable by grid generation | Educational fairness; difficulty comes from grid size, molecule size, interaction-type count | — Pending |
| Demo sets: agent proposes with citations, human approves before fetch/commit | spec.md truthfulness constraint | — Pending |
| No helper visuals during gameplay (spec) | Preserves the 3D-practice core value | — Pending |

---
*Last updated: 2026-09-05 after initialization*
