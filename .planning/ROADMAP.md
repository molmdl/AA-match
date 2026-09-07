# Roadmap: AA-match

## Overview

AA-match ships as a standard PyMOL 2.5.0 plugin implementing an educational small-molecule ↔ amino-acid matching game: players drag, rotate, and adjust amino acids onto a small molecule in the 3D viewer, and an in-house geometric detector scores the interactions they form — no helper visuals during play. The phase order is dependency-driven and honors the validated research skeleton (ARCHITECTURE.md build order + PITFALLS.md topic phases + SUMMARY.md suggested order): **Phases 1–3 isolate the risky unknowns before any Qt GUI work** (pure foundation → data + cmd-only headless game engine → wizard interaction), **Phases 4–7 concentrate the Qt/persistence work** as thin layers over a proven core, **Phase 8 curates demo content under the propose → human-approve → fetch/commit protocol**, and **Phase 9 closes with help, docs, and the release audit**. Every success criterion is tagged with the environment tier that can verify it, per PITFALLS.md test-tier discipline.

**Depth:** comprehensive (9 phases) · **v1 requirements:** 45/45 mapped (see Coverage)

> **Note for planning/execution agents — borrowable prior-art code:** Some UI and mechanism code can be **borrowed/adapted from bioCHEMeleon** (`tmp/bioCHEMeleon/biochemeleon/`, git-ignored, readable via the main-repo path): modeless Qt dialog pattern (`gui_setup.py`/`gui_game.py`), wizard picking (`wizard.py`), versioned persistence + checkpoint/export/import (`persistence.py`, `setup_state.py`), backup/restore (`backup.py`), help panel/tooltips, countdown, win-screen modal timing. Adapt naming/layout to AA-match — do not vendor wholesale; check the borrowing module against the research files' verified API citations.

### Success-criteria legend

- **[WSL]** — verifiable in the WSL dev shell: `python3.6 -m unittest` (pure layer: stdlib only — no numpy, no Qt)
- **[HEADLESS]** — verifiable headlessly: `cmd.exe /c C:\src\run-conda-pymol.bat -cq <script>` (exit 0 = pass)
- **[HUMAN]** — human-verified GUI checkpoint (Qt/interactive paths cannot run from WSL — by design, not a gap)
- **[GATE]** — recorded human decision/approval that unblocks later work (truthfulness protocol)

## Phases

- [x] **Phase 1: Bootstrap & Pure Foundation** — installable plugin skeleton, WSL→Windows toolchain proof, pure setup/persistence/level-spec layer with WSL tests
- [ ] **Phase 2: Headless Game Engine** — human-approved thresholds → detector → always-solvable generator → bundled data → cmd-only generate/place/detect/score, headless end-to-end
- [ ] **Phase 3: Wizard Gameplay Loop** — click-to-select, move/rotate onto the ligand, Confirm; movement-model decision; no helper visuals
- [ ] **Phase 4: Qt Setup Window** — modeless setup window: demo dropdown, upload, params, the seven bottom buttons
- [ ] **Phase 5: Game Status Tab & Start Sequence** — start sequence, live status tab (info box / timer / required interactions), Hint
- [ ] **Phase 6: Scoring Lifecycle & Endgame** — confirm/debrief/advance, skip/give-up, endgame screen, restart/reset
- [ ] **Phase 7: Checkpoint & Game-File Persistence** — save/restore round-trip, Import of exported games
- [ ] **Phase 8: Demo Curation & Citations** — ~9 curated tier slots under propose → approve → fetch/commit; DATA_SOURCES.md
- [ ] **Phase 9: Help, Docs & Release Audit** — in-game help, README, final docs audit, perf budgets

## Phase Details

### Phase 1: Bootstrap & Pure Foundation
**Goal**: An installable plugin skeleton whose pure foundation (setup params, versioned persistence, level-spec schema, backup safety net) is proven in WSL, and whose WSL→Windows headless pipeline is proven end-to-end — before any game code exists.
**Depends on**: Nothing (first phase)
**Requirements**: INSTALL-01, PERSIST-01
**Success Criteria** (what must be TRUE):
  1. [WSL] Setup parameters round-trip through a versioned save file — every field preserved, versioned header refuses newer/foreign formats with a clear message; `python3.6 -m unittest` green. (PERSIST-01)
  2. [WSL] Pure-layer gates green: `setup_state`, `level_spec`, `persistence`, and the backup module (snapshot/restore/verify) unit-test with stdlib-only imports (no pymol / Qt / numpy / dataclasses); `to_windows_path()` helper unit-tested. These gates protect every later phase.
  3. [HEADLESS] The staged plugin skeleton loads via the headless cmd.exe recipe with exit 0 (`__init_plugin__` runs clean); Windows conda env Python/Qt versions recorded once.
  4. [HUMAN] Installing via Plugin Manager and restarting PyMOL registers "AA-match" under the Plugins menu. (INSTALL-01)
**Research notes**: Modeless-Qt decision is made *here* as a rule (retrofit is a rewrite — PITFALLS 1/4). Installs the layer contract, path helper, and backup module every later phase depends on (PITFALLS 2, 3, 9).
**Plans**: 9 plans

Plans:
- [x] 01-01-PLAN.md — aamatch package skeleton: metadata-first `__init__.py`, Qt-free placeholder, skeleton contract test
- [x] 01-02-PLAN.md — persistence container core (magic/version/kind refusals) + atomic JSON I/O (TDD)
- [x] 01-03-PLAN.md — backup pure core over injected stores + corruption-recovery proof (TDD)
- [x] 01-04-PLAN.md — paths.to_windows_path 14-case matrix + package_data_path (TDD)
- [x] 01-05-PLAN.md — setup_state 7-field model + PERSIST-01 versioned round-trip and refusals (TDD)
- [x] 01-06-PLAN.md — level_spec schema reserve + detector_version exact-match gate (TDD)
- [x] 01-07-PLAN.md — headless smoke-01: loader proof, env-version record, cmd.load path probes
- [x] 01-08-PLAN.md — purity gate suite (AST + clean-subprocess) + AGENTS.md standing gates
- [x] 01-09-PLAN.md — [HUMAN] Plugin-Manager install checkpoint + setup-defaults confirmation

### Phase 2: Headless Game Engine
**Goal**: The entire game works with no GUI at all: a human-approved threshold table drives a correct, vectorized detector; the seeded generator always produces solvable levels; bundled data materializes into real PyMOL objects; and generate → place → detect → score runs headlessly end-to-end on a scripted placement.
**Depends on**: Phase 1
**Requirements**: DETECT-01, DETECT-02, DETECT-03, DETECT-04, DETECT-05, GEN-01, GEN-02, GEN-03, GEN-04, GEN-05
**Success Criteria** (what must be TRUE):
  1. [GATE] A threshold document exists in-repo: every criterion value for the seven interaction types cites its published source (PLIP / ProLIF / BINANA), in-house resolutions of disagreements are recorded, and explicit human approval is recorded before the detector freezes. (DETECT-03)
  2. [WSL] Detector unit tests classify scripted geometries for all seven types — H-bond, salt bridge (ionic folded in), π-stacking (parallel + T-shaped as one category), cation-π, hydrophobic, halogen (ligand-side donors only), metal coordination (only when the ligand carries a metal) — with explicit partner sides (AA vs small molecule) so hint/solvability checks and scoring agree. (DETECT-01, DETECT-02, DETECT-04)
  3. [WSL] Generator invariant tests over ≥100 seeds: every level solvable by construction (AAs capable of all required interactions present, plus distractors), NxN grid per difficulty, globally disjoint slots, difficulty expressed via grid N / molecule size / required-interaction-type count. (GEN-01, GEN-03, GEN-04, GEN-05)
  4. [HEADLESS] End-to-end smoke (exit 0, count-asserted): generate → materialize grid + ligand (specified protonation state; bond orders/valence preserved from SDF/MOL2; sentinel + reserved-prefix conventions) → scripted placement → detection → binary-per-interaction fraction score. (GEN-02)
  5. [HEADLESS] Detection perf smoke on the largest bundled molecule: full geometry-extract + detect pass inside the perf budget, vectorized/spatially pruned (no naive per-atom-pair loops — code-audited); a detector-version stamp is embedded in generated specs so stale games are refused. (DETECT-05)
**Research notes**: PITFALLS topics *detection-engine* + *grid-generation* live here. DETECT-05's "numpy vectorized" is reconciled with PITFALL 3: vectorization + spatial pruning (cell lists) implemented stdlib-pure (WSL-testable); numpy permitted only in cmd-tier helpers on the Windows side; perf verified headless. The threshold table is the critical-path human gate — sequence it as the phase's first plan. Chemistry policy (alt-conf, waters, frames, protonation) documented in the detector module.
**Plans**: 16 plans

Plans:
- [x] 02-01-PLAN.md — [GATE] threshold + capability decision document (D1, OQ-1 recorded) + human approval checkpoint (DETECT-03)
- [x] 02-02-PLAN.md — pure vec3 + spatial cell-list primitives with 100-seed equivalence proof (TDD)
- [x] 02-03-PLAN.md — pure manifest module + 'manifest' container kind (TDD)
- [x] 02-04-PLAN.md — fixture ligands + MANIFEST.json + generalized smoke runner + SMOKE-02 every-manifest-id proof
- [x] 02-05-PLAN.md — pure capability.py: single typing home (AA table + ligand typing + support predicates) (TDD)
- [x] 02-06-PLAN.md — thresholds.py constants + detector core (features, prefilter, candidates, h_bond/salt_bridge/hydrophobic) (TDD)
^- [x] 02-07-PLAN.md — detector part 2a: pi_stacking + cation_pi (TDD; split from original 02-07 after repeated silent spawn failures)
- [ ] 02-07b-PLAN.md — detector part 2b: halogen + metal + canonical 7-type surface (TDD; depends 02-07)
- [x] 02-08-PLAN.md — pure seeded generator: difficulty, grid geometry, mode semantics, solvable allocation, payload assembly (TDD)
- [x] 02-09-PLAN.md — cmd-tier geometry.py extraction bridge (records + bond block + bounds)
- [ ] 02-10-PLAN.md — pure game_state.py: score fraction semantics + runtime container (TDD)
- [ ] 02-11-PLAN.md — detector invariance/sensitivity property battery + WSL perf regression guard (wave 8; needs complete detector)
- [ ] 02-12-PLAN.md — generator >=100-seed invariant suite (ROADMAP criterion 3)
- [ ] 02-13-PLAN.md — cmd-tier placement.py (materialize/sentinels/reset/cleanup) + SMOKE-03
- [ ] 02-14-PLAN.md — engine.py composition root + SMOKE-04 count-asserted E2E (place/detect/score, rotation invariance, reset)
- [ ] 02-15-PLAN.md — SMOKE-05 perf smoke + AST code audit + detector-version stamp proof

### Phase 3: Wizard Gameplay Loop
**Goal**: In a fresh, stock PyMOL, a player can play the core loop by hand: click an amino acid to select it, move/rotate it onto the small molecule, confirm, and see the detection result — with no helper visuals and the user's environment restored afterwards.
**Depends on**: Phase 2 (materialized grids, detection, spec replay)
**Requirements**: PLAY-01, PLAY-02, PLAY-03, PLAY-04
**Success Criteria** (what must be TRUE):
  1. [HUMAN] On a fresh PyMOL in the default 3-Button Viewing mode, clicking an amino acid selects it — visible color change + selected status (canonical `do_select`→`do_pick` route; no dev-box button-mode tweaks required). (PLAY-01)
  2. [HUMAN] The selected AA can be moved/rotated/adjusted onto the small molecule, and the detector scores the moved pose (movement model composed into detection — result matches what is on screen). (PLAY-02)
  3. [HUMAN] Clicking another AA switches selection; Confirm finishes the molecule and runs detection, with the result visible in the wizard panel. (PLAY-03)
  4. [HUMAN + GATE] No helper lines/dots/geometry appear at any point during play; the movement-model spike verdict is recorded (object-matrix default; `cmd.drag(wizard=0)` headless spike result + default `editor_scheme` check); the prior wizard and `mouse_selection_mode` are restored when the game wizard exits. (PLAY-04)
**Research notes**: PITFALLS topics *viewer-interaction*. Mandatory human GUI check on a fresh PyMOL (PITFALL 5). Movement-model decision gates detector input + reset semantics (PITFALLS 6, 12) — run the spike headlessly before freezing. Reset-to-grid via spec replay established here.
**Plans**: TBD

Plans:
- [ ] 03-01: (TBD)

### Phase 4: Qt Setup Window
**Goal**: From the Plugins menu the user gets a modeless setup window from which they can configure everything, save/load setups, export a shareable game, clean up the model, and start playing.
**Depends on**: Phase 1 (persistence formats, path helper), Phase 2 (generation + bundled data for the dropdown), Phase 3 (Start launches playable wizard gameplay)
**Requirements**: SETUP-01, SETUP-02, SETUP-03, SETUP-04, SETUP-05, SETUP-06, SETUP-07, SETUP-08, SETUP-09, SETUP-10
**Success Criteria** (what must be TRUE):
  1. [HUMAN] Plugins → AA-match opens the setup window and the 3D viewer stays fully interactive while it is open (modeless; window survives minimize/re-open). (SETUP-01)
  2. [HUMAN] The user can pick a demo set from the dropdown of bundled sets, upload an SDF/MOL2 molecule set, and set molecules-per-level, difficulty-level count, and the required-interaction mode (exclusive / block-exclusive / unset-random). (SETUP-02, SETUP-03, SETUP-04, SETUP-05, SETUP-06)
  3. [HUMAN] Reset restores defaults; Randomize produces a valid random configuration; Save Setup / Load Setup round-trip the versioned setup file. (SETUP-07)
  4. [HUMAN] Generate and export writes a shareable, versioned game file; Cleanup removes only game-generated objects (sentinel/prefix rules) and restores the original scene; Start generates the configured game and drops the player into playable wizard gameplay. (SETUP-08, SETUP-09, SETUP-10)
**Research notes**: PITFALLS topic *setup-GUI* — first GUI architectural decision (PITFALL 4: modeless `show()`, module-level singleton, Qt imports via `pymol.Qt` only; grep gates). Export format reuses the Phase-1 versioned-format discipline; Import-side round-trip completes in Phase 7 (PERSIST-02). Cleanup button wired to Phase-2 sentinel conventions (PITFALL 13).
**Plans**: TBD

Plans:
- [ ] 04-01: (TBD)

### Phase 5: Game Status Tab & Start Sequence
**Goal**: Starting a game feels like a game: the start sequence stores state and builds representations, the Game status tab takes over with live status, a 3-2-1 countdown starts play, and Hint works.
**Depends on**: Phase 3 (gameplay loop), Phase 4 (Start from the setup window)
**Requirements**: SETUP-11, SCORE-04, PLAY-05
**Success Criteria** (what must be TRUE):
  1. [HUMAN] Start stores the initial state, generates representations per setup, switches to the Game status tab, plays a 3-2-1 countdown, and the timer starts from zero. (SETUP-11)
  2. [HUMAN] The Game status tab shows a rolling info box, the elapsed timer outside the info box, and the required interaction types + counts (`any` or from the allowed list). (SCORE-04)
  3. [HUMAN] Hint recolors carbon atoms of amino acids that could form one of the required interactions — recolor only, never lines/dots/geometry. (PLAY-05)
**Research notes**: QTimer-only timers on the main thread (PITFALL 1/15); pause the timer while any modal child is open (timer-fairness UX rule); win-screen modal timing pattern (~100 ms after last `cmd.color`) applies to later endgame work.
**Plans**: TBD

Plans:
- [ ] 05-01: (TBD)

### Phase 6: Scoring Lifecycle & Endgame
**Goal**: The full game semantics work end-to-end: confirm scores and advances, levels escalate, skip/give-up protect the player, restart/reset recover, and the endgame reports the complete result.
**Depends on**: Phase 5 (game tab exists), Phase 2 (scoring), Phase 3 (mechanics, spec replay)
**Requirements**: SCORE-01, SCORE-02, SCORE-03, SCORE-05, SCORE-06, SCORE-07, SCORE-09, SCORE-10
**Success Criteria** (what must be TRUE):
  1. [HUMAN] Confirm shows the molecule score (fraction of required interactions formed, binary per interaction) plus the running total, then advances to the next molecule; a post-confirm debrief lists formed vs missed interactions (numbers only — no geometry). (SCORE-01, SCORE-02)
  2. [HUMAN] Finishing all molecules of a level advances to the next level at higher difficulty. (SCORE-03)
  3. [HUMAN] Skip Molecule (with confirmation warning) stores the partial score and moves to the next molecule; Give Up (with confirmation warning) ends the game at the current stage. (SCORE-05, SCORE-06)
  4. [HUMAN] The endgame screen shows per-level scores + total, a stopped timer, and a winning message with time taken, total molecules and levels, and skip/give-up counts. (SCORE-07)
  5. [HUMAN] Restart replays the stored initial state into a fresh game; Reset returns all amino acids to their grid positions (spec replay — correct for the chosen movement model). (SCORE-09, SCORE-10)
**Research notes**: PITFALLS topics *scoring-lifecycle*. Reset must reset the same mechanism that moved the AA (PITFALL 6); Restart/Reset route through the Phase-1 backup module + spec replay, never "undo" (PITFALL 9). Confirmation warnings are spec-required — do not drop them.
**Plans**: TBD

Plans:
- [ ] 06-01: (TBD)

### Phase 7: Checkpoint & Game-File Persistence
**Goal**: Games survive closing PyMOL: checkpoints fully reconstruct a running game (positions, scores, counters, timer), and exported game files load through the Game status tab's Import button.
**Depends on**: Phase 5 (game tab / Import button), Phase 6 (full game state to persist)
**Requirements**: PERSIST-02, PERSIST-03, SCORE-08
**Success Criteria** (what must be TRUE):
  1. [HEADLESS + HUMAN] Save writes the zipped `.pse` + JSON-sidecar container; save → quit → relaunch → load restores placed positions/orientations, scores, counters, and timer; the matrix round-trip smoke result is recorded (object matrices survive `.pse`, or transforms are persisted via the sidecar). (SCORE-08, PERSIST-03)
  2. [HUMAN] The Game status tab's Import button loads a previously exported game file and reconstructs the initial game; stale or foreign files (wrong version / detector stamp) are refused with a clear message. (PERSIST-02)
  3. [GATE] Session-restore hygiene verified: the wizard pickles cleanly (no Qt/locks/controller on it), sentinel-first reconstruction reconciles sidecar vs loaded atoms, and restore works after a plugin reload — console clean during save/load. (PERSIST-03)
**Research notes**: PITFALLS topic *persistence* — gate 1 is the `.pse` matrix round-trip smoke (run before trusting the movement model's persistence); sentinel-first reconstruction; magic+version headers; capture timer before modal file dialogs.
**Plans**: TBD

Plans:
- [ ] 07-01: (TBD)

### Phase 8: Demo Curation & Citations
**Goal**: ~9 curated demo sets ship with full, human-verified provenance under the propose → human-approve → fetch/commit protocol — content is gated by truthfulness, not by code.
**Depends on**: Phase 2 (manifest + bundling machinery), Phase 4 (dropdown lists the sets)
**Requirements**: GEN-06, HELP-02
**Success Criteria** (what must be TRUE):
  1. [GATE] Every demo candidate is proposed with PDB/SDF IDs, protonation/interaction sources, and a recorded selection rationale (educational coverage, tier fit, chemical/interaction diversity) — and human approval is recorded **before** any fetch/commit. (GEN-06, HELP-02 protocol)
  2. [HUMAN] The ~9 tier slots ship (Easy ×3, Hard ×3, Challenge, Very challenging ×2), pre-downloaded and committed; the setup dropdown lists all curated sets grouped by tier. (GEN-06)
  3. [HUMAN] DATA_SOURCES.md covers every bundled file: download source, PDB ID + DOI, protonation/interaction provenance from known binding databases, and a verified license permitting bundling/redistribution. (HELP-02)
  4. [HEADLESS] Every-manifest-id smoke passes: each demo loads through the path helper with atom/bond counts matching the versioned manifest; on a ligand+ions+water demo, Cleanup leaves exactly the original object set. (verifies GEN-06 supply + PITFALL 13 in the field)
**Research notes**: PITFALLS topics *demos*. Multi-state ligand policy (state 1 vs collapse) decided here with the curated data; strip waters/solvent before bundling; SDF-first for ligand chemistry (bond orders + explicit H).
**Plans**: TBD

Plans:
- [ ] 08-01: (TBD)

### Phase 9: Help, Docs & Release Audit
**Goal**: A new user can learn the game from in-game help alone; every user-facing document matches shipped reality; performance budgets are confirmed on the final build.
**Depends on**: Phases 1–8 (docs must match shipped reality)
**Requirements**: HELP-01, DOCS-01, DOCS-02
**Success Criteria** (what must be TRUE):
  1. [HUMAN] The setup window and game tab provide a help panel + tooltips sufficient to play without external docs — each interaction type explained clearly but sufficiently; destructive actions carry warnings. (HELP-01)
  2. [HUMAN] README's Usage, Project Structure, and demo-set table sections are filled to match shipped reality; the vibe-coding warning is retained. (DOCS-01)
  3. [GATE] Final audit: every user-facing document (README, in-game help, tooltips, DATA_SOURCES.md) is verified against actual code behavior; discrepancies fixed before release. (DOCS-02)
  4. [HEADLESS + HUMAN] Perf budgets confirmed on the largest curated demo: Generate < 30 s; pick/drag feedback < 200 ms (headless timing + human feel). (PROJECT.md code standards)
**Research notes**: PITFALLS topic *polish*. Lands last so behavior is stable when docs are written — no doc churn.
**Plans**: TBD

Plans:
- [ ] 09-01: (TBD)

## Pitfall Coverage

Lifted from PITFALLS.md "Pitfall-to-Phase Mapping" (topic names → this roadmap's numbers):

| # | Pitfall | Addressed in | Verified by |
|---|---------|--------------|-------------|
| 1 | Qt tier discipline | Phase 1 (rules) + all phases (test tiers) | WSL tests green without pymol stubs; human-verify checkpoints written into plans |
| 2 | WSL→Windows paths | Phase 1 (helper) · 2 (bundled loads) · 7 (save/load) · 8 (every demo) | Headless smoke from WSL; every-manifest-id smoke |
| 3 | Pure layer stdlib-only | Phase 1 (contract) · 2 (detector math) | Import gate; 3.6 unit tests green with no stubs |
| 4 | Modeless Qt / GC / Tk | Phase 4 | Grep gates; viewer interactive with window open [HUMAN] |
| 5 | Wizard two-entry-point picking | Phase 3 | Default-Viewing-mode pick on fresh PyMOL [HUMAN]; prior wizard + selection mode restored |
| 6 | Movement model + editor_scheme | Phase 3 (spike/decision) · 6 (reset semantics) | Spike verdict recorded; Reset returns AAs to grid [HUMAN] |
| 7 | `cmd.create` merge/no-op semantics | Phase 2 | Count-asserted generate smokes |
| 8 | Atom identity & selectors | Phase 2 (conventions) · 3 (pick identity) · 7 (sentinel reconstruction) | Alt-conf pick/scoring correct; `b < 0` selectors; `ID`/`space=` discipline |
| 9 | No-undo backup discipline | Phase 1 (backup module) · 6 (Restart/Reset) | Snapshot at Start; corruption-simulation recovers |
| 10 | `.pse` round-trip gaps | Phase 7 | Save→quit→relaunch→load restores everything; matrix round-trip smoke recorded |
| 11 | Generation uniqueness / solvability contract | Phase 2 · 8 (manifest) | ≥100-seed invariant tests; detector-version stamp; every-manifest-id smoke |
| 12 | Detection chemistry/frames | Phase 2 (policy) · 3 (matrix composition) · 8 (SDF provenance) | SDF/PDB parity; rotation-invariance; approved threshold doc |
| 13 | Cleanup isolation | Phase 2 (sentinels) · 4 (button) — verified Phase 8 | Messy demo: Cleanup leaves the original object set exactly |
| 14 | Citation truthfulness | Phase 2 (thresholds) · 8 (demos) | Human approval recorded per threshold and per demo file |
| 15 | Performance / event loop | Phase 2 (detect perf) · 3 (per-move cost) · 9 (final budgets) | Largest demo: Generate < 30 s, pick/drag < 200 ms |

## Progress

**Execution order:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Bootstrap & Pure Foundation | 9/9 | Complete | 2026-09-06 |
| 2. Headless Game Engine | 15/16 | In progress (wave 8 complete; wave 9 = 02-15 last) | - |
| 3. Wizard Gameplay Loop | 0/TBD | Not started | - |
| 4. Qt Setup Window | 0/TBD | Not started | - |
| 5. Game Status Tab & Start Sequence | 0/TBD | Not started | - |
| 6. Scoring Lifecycle & Endgame | 0/TBD | Not started | - |
| 7. Checkpoint & Game-File Persistence | 0/TBD | Not started | - |
| 8. Demo Curation & Citations | 0/TBD | Not started | - |
| 9. Help, Docs & Release Audit | 0/TBD | Not started | - |

## Coverage

✓ **45/45 v1 requirements mapped** — no orphans, no duplicates. Each requirement maps to exactly one phase (the first that could deliver its user-observable behavior); later phases may re-verify or extend earlier deliveries (e.g., the demo dropdown ships in Phase 4 with bundled sets and is filled by curated sets in Phase 8).

Per-phase counts: P1 = 2 · P2 = 10 · P3 = 4 · P4 = 10 · P5 = 3 · P6 = 8 · P7 = 3 · P8 = 2 · P9 = 3

Full traceability table: `REQUIREMENTS.md` → Traceability.

> Note: REQUIREMENTS.md's coverage header previously claimed 46 v1 requirements; an exact ID audit on 2026-09-05 found 45 (INSTALL-01 … DOCS-02). Corrected there during roadmap creation.

### Environment-tier honesty

Phases 1–2 are verifiable in WSL + headless cmd.exe only (no Qt). Phases 4–7 concentrate the [HUMAN] GUI checkpoints — these are by-design verification steps, not gaps (Qt needs a real display). [GATE] items are recorded human approvals required by the project's truthfulness constraint.
