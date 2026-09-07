# Requirements: AA-match

**Defined:** 2026-09-05
**Core Value:** The player can place amino acids onto a small molecule in the PyMOL 3D viewer and the game correctly detects and scores the interactions they form — turning unguided 3D manipulation practice into a scored game.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Installation

- [x] **INSTALL-01**: User can install AA-match as a standard PyMOL plugin via Plugin Manager, registering an "AA-match" item under the Plugins menu

### Setup

- [ ] **SETUP-01**: Starting the plugin opens a setup window (modeless — the 3D viewer stays interactive)
- [ ] **SETUP-02**: User can choose a demo set from a dropdown of curated, pre-downloaded sets
- [ ] **SETUP-03**: User can upload a set of small molecules in SDF or MOL2 format (bond-order-carrying, so valence-correct rendering is preserved)
- [ ] **SETUP-04**: User can set number of small molecules per level (default 2–5, reasonable cap)
- [ ] **SETUP-05**: User can set number of difficulty levels per game (default 3–5, reasonable cap)
- [ ] **SETUP-06**: User can configure the required-interaction mode: exclusive (required target is `any` interaction formed), block-exclusive (required set is the specific checked interactions), or unset (random required set)
- [ ] **SETUP-07**: User can Reset (restore defaults), Randomize, Save Setup, and Load Setup from the setup window
- [ ] **SETUP-08**: User can Generate and export the initial game state to a shareable file
- [ ] **SETUP-09**: User can Cleanup model (remove game-generated objects, restore original objects)
- [ ] **SETUP-10**: User can Start the game from the setup window
- [ ] **SETUP-11**: Starting stores the initial state, generates representations per setup, switches to the Game status tab, and counts down 3-2-1 before play begins

### Game Generation

- [x] **GEN-0- [ ] **GEN-01**: Game generates multiple levels of increasing difficulty per the difficulty-count setting
- [x] **GEN-0- [ ] **GEN-02**: Each level contains small molecules of a specific protonation state rendered with correct valence
- [x] **GEN-0- [ ] **GEN-03**: For each molecule, an NxN grid (N by difficulty) of randomized, capped amino acids is laid out around the molecule beyond a gap
- [x] **GEN-0- [ ] **GEN-04**: Every generated level is solvable by construction (grid contains AAs able to form all required interactions, plus distractors)
- [x] **GEN-0- [ ] **GEN-05**: Difficulty is expressed through grid N, molecule size, and count of required interaction types
- [ ] **GEN-06**: Demo sets ship pre-downloaded (~9 tier slots: Easy ×3, Hard ×3, Challenge, Very challenging ×2) with protonation/interaction provenance from known binding databases; each entry records its selection rationale (educational coverage, tier fit) and chemical/interaction diversity across the set

### Viewer Gameplay

- [ ] **PLAY-01**: Player can click an amino acid in the OpenGL viewer to select it (color change + selected status)
- [ ] **PLAY-02**: Player can move/rotate/adjust the selected amino acid onto the small molecule
- [ ] **PLAY-03**: Player can switch to another amino acid by clicking it, or click Confirm to finish the molecule
- [ ] **PLAY-04**: No helper lines/dots are displayed during gameplay
- [ ] **PLAY-05**: Hint button recolors carbon atoms of amino acids that could form one of the required interactions (recolor only)

### Interaction Detection

- [x] **DETECT-01**: Game detects H-bond, salt bridge (ionic folded in), π-stacking (parallel + T-shaped in one category), cation-π, and hydrophobic contact from atom types and geometry
- [x] **DETECT-02**: Game detects halogen bond (ligand-side donors) and metal coordination (conditional on metal present in the ligand)
- [x] **DETECT-03**: Detection criteria adopt one internally consistent in-house threshold table, transcribed from published sources (PLIP/ProLIF/BINANA) and explicitly human-approved before shipping
- [x] **DETECT-04**: Detection is explicit about partner sides (amino acid vs small molecule) so capability checks (hint, solvability) and scoring agree
- [x] **DETECT-05**: Detection is vectorized, not loop-bound: numpy vectorized geometry (no naive per-atom-pair Python loops) with spatial pruning (e.g. cell lists); criteria/pairing logic stays WSL-unit-testable (pure layer), vector math verified by headless perf smoke on the largest demo

### Scoring & Game Lifecycle

- [ ] **SCORE-01**: Confirm runs detection and shows the molecule score (fraction of required interactions formed, binary per interaction) plus running total, then advances to the next molecule
- [ ] **SCORE-02**: After Confirm, a debrief shows which required interactions formed vs missed (numbers only — no geometry, respecting the no-helper rule)
- [ ] **SCORE-03**: Finishing a level advances to the next level with higher difficulty
- [ ] **SCORE-04**: Game status tab shows a rolling info box, elapsed timer (outside the info box), and the type + number of required interactions (`any` or from the allowed list)
- [ ] **SCORE-05**: Skip Molecule (with confirmation warning) stores the partial score and moves to the next molecule
- [ ] **SCORE-06**: Give Up (with confirmation warning) ends the game at the current stage and shows the endgame screen
- [ ] **SCORE-07**: After all levels: per-level scores + total score, stopped timer, and a winning message with time taken, total molecules and levels, and skip/give-up counts
- [ ] **SCORE-08**: Save button checkpoints the game (PyMOL session + game-state sidecar) so the user can load/resume any time
- [ ] **SCORE-09**: Restart button restarts the game from the stored initial state
- [ ] **SCORE-10**: Reset button places all amino acids back to their grid positions

### Persistence

- [x] **PERSIST-01**: Setup parameters save to / load from a file (versioned format)
- [ ] **PERSIST-02**: Generate-and-export writes a shareable game file that the Game status tab's Import button can load
- [ ] **PERSIST-03**: Checkpoint save/restore fully reconstructs the game (placed positions/orientations, scores, counters)

### Help & Attribution

- [ ] **HELP-01**: Setup window and game tab provide clear but sufficient in-game explanation (help panel + tooltips)
- [ ] **HELP-02**: All demo data citations live in a dedicated sources document, human-verified before shipping (propose → approve → fetch/commit protocol); each entry records download source and the verified license permitting bundling/redistribution

### Documentation

- [ ] **DOCS-01**: README placeholders (Usage, Project Structure, demo-set table) are filled to match shipped reality; the vibe-coding warning is retained
- [ ] **DOCS-02**: Final documentation audit: all user-facing docs (README, in-game help, tooltips, DATA_SOURCES.md) verified against actual code behavior before release

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### VMD Port

- **VMD-01**: VMD 1.9.3 (Tcl/Tk) port of the game on a viewer-agnostic core

### Extensions

- **EXT-01**: Water-bridge interaction type (needs explicit waters in generated scenes)
- **EXT-02**: π-stacking split into face-to-face (parallel) vs edge-to-face (T-shaped) as separate teachable types
- **EXT-03**: Protein–protein / DNA-RNA–ligand game modes
- **EXT-04**: User-set validation helper for uploaded molecule sets

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Helper lines/dots/geometry during gameplay | Defeats the core value (practicing 3D perception); spec-forbidden |
| Runtime network fetching | Offline constraint; reproducibility/citation problems — pre-downloaded demos + upload only |
| prolif/PLIP/BINANA as runtime dependencies | Zero-extra-deps constraint (proLIF needs RDKit+MDAnalysis; PLIP needs OpenBabel) — in-house detection instead |
| Auto-snap / auto-optimal-placement assist | Removes the skill being practiced |
| Multiplayer / leaderboards / online accounts | Offline plugin, no network at runtime |
| User scripting/recipes API | Scope creep; arbitrary code inside PyMOL is a safety risk |
| Covalent-bond interactions | Not a non-covalent placement exercise; even PLIP lists them as unsupported |
| PDB as upload format | No reliable bond orders → undermines valence-correct rendering (SDF/MOL2 only) |

## Traceability

Which phases cover which requirements. Updated during roadmap creation (2026-09-05).

| Requirement | Phase | Status |
|-------------|-------|--------|
| INSTALL-01 | Phase 1 | Complete |
| SETUP-01 | Phase 4 | Pending |
| SETUP-02 | Phase 4 | Pending |
| SETUP-03 | Phase 4 | Pending |
| SETUP-04 | Phase 4 | Pending |
| SETUP-05 | Phase 4 | Pending |
| SETUP-06 | Phase 4 | Pending |
| SETUP-07 | Phase 4 | Pending |
| SETUP-08 | Phase 4 | Pending |
| SETUP-09 | Phase 4 | Pending |
| SETUP-10 | Phase 4 | Pending |
| SETUP-11 | Phase 5 | Pending |
| GEN-01 | Phase 2 | Complete |
| GEN-02 | Phase 2 | Complete |
| GEN-03 | Phase 2 | Complete |
| GEN-04 | Phase 2 | Complete |
| GEN-05 | Phase 2 | Complete |
| GEN-06 | Phase 8 | Pending |
| PLAY-01 | Phase 3 | Pending |
| PLAY-02 | Phase 3 | Pending |
| PLAY-03 | Phase 3 | Pending |
| PLAY-04 | Phase 3 | Pending |
| PLAY-05 | Phase 5 | Pending |
| DETECT-01 | Phase 2 | Complete |
| DETECT-02 | Phase 2 | Complete |
| DETECT-03 | Phase 2 | Complete |
| DETECT-04 | Phase 2 | Complete |
| DETECT-05 | Phase 2 | Complete |
| SCORE-01 | Phase 6 | Pending |
| SCORE-02 | Phase 6 | Pending |
| SCORE-03 | Phase 6 | Pending |
| SCORE-04 | Phase 5 | Pending |
| SCORE-05 | Phase 6 | Pending |
| SCORE-06 | Phase 6 | Pending |
| SCORE-07 | Phase 6 | Pending |
| SCORE-08 | Phase 7 | Pending |
| SCORE-09 | Phase 6 | Pending |
| SCORE-10 | Phase 6 | Pending |
| PERSIST-01 | Phase 1 | Complete |
| PERSIST-02 | Phase 7 | Pending |
| PERSIST-03 | Phase 7 | Pending |
| HELP-01 | Phase 9 | Pending |
| HELP-02 | Phase 8 | Pending |
| DOCS-01 | Phase 9 | Pending |
| DOCS-02 | Phase 9 | Pending |

**Coverage:**
- v1 requirements: 45 total (corrected from 46 — exact ID audit on 2026-09-05 found 45: 1 INSTALL + 11 SETUP + 6 GEN + 5 PLAY + 5 DETECT + 10 SCORE + 3 PERSIST + 2 HELP + 2 DOCS)
- Mapped to phases: 45
- Unmapped: 0 ✓

**Phase map:** Phase 1 (Bootstrap & Pure Foundation) · Phase 2 (Headless Game Engine) · Phase 3 (Wizard Gameplay Loop) · Phase 4 (Qt Setup Window) · Phase 5 (Game Status Tab & Start Sequence) · Phase 6 (Scoring Lifecycle & Endgame) · Phase 7 (Checkpoint & Game-File Persistence) · Phase 8 (Demo Curation & Citations) · Phase 9 (Help, Docs & Release Audit). Each requirement maps to the first phase that could deliver its user-observable behavior; later phases may re-verify or extend earlier deliveries.

---
*Requirements defined: 2026-09-05*
*Last updated: 2026-09-05 after roadmap creation (traceability filled)*
