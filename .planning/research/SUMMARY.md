# Project Research Summary

**Project:** AA-match — PyMOL 2.5.0 plugin educational matching game (small-molecule ↔ amino-acid interactions)
**Domain:** Desktop-plugin game inside a scientific viewer (PyQt5 GUI + wizard-driven 3D gameplay + geometric detection engine)
**Researched:** 2026-09-05
**Confidence:** HIGH (stack/architecture/pitfalls verified against the local PyMOL 2.5.0 source tree and the shipped v1 prior art; features verified against official PLIP/ProLIF/BINANA docs fetched today; explicit UNVERIFIED items listed under Gaps)

## Executive Summary

AA-match is a game that lives *inside* PyMOL: a Qt setup/game window, a custom Wizard that receives 3D-viewer clicks, and an in-house geometric detector that decides whether a placed amino acid forms each required interaction with the ligand. Experts build exactly this kind of thing with a strict layered plugin: a **pure stdlib game brain** (generation, detection, scoring, persistence) that is unit-testable in the WSL 3.6.9 shell, thin **cmd bridges** that convert PyMOL objects ↔ plain data, a **thin wizard input adapter**, and a **modeless Qt shell** — the architecture our own shipped v1 plugin (bioCHEMeleon) proved across 12 phases. Nearly the entire UI/persistence feature set (setup window with 7 buttons, sidecar checkpoint/export/import, hint, win screen, demo manifest with tiers, citation protocol) has a *working, battle-tested prior-art implementation* to copy.

The recommended approach: build the pure game core first and verify it entirely in WSL (`python3.6 -m unittest`), then prove a headless cmd-only path (generate → place → detect → score, no GUI) through the verified `cmd.exe /c C:\src\run-conda-pymol.bat -cq` smoke recipe (**full recipe in STACK.md — Development Tools + Installation §5**), and only then add wizard interaction and Qt windows, which need human GUI verification. Two mechanisms are genuinely new and carry the project risk: **always-solvable grid generation** (AA-capability matrix + global slot allocation) and the **select → move/rotate → Confirm placement loop** (movement-model decision). Both decompose into verifiable spikes if sequenced early.

Key risks, in order: (1) **the human-approved threshold table is the critical path** — PLIP, ProLIF, and BINANA publish *different* numeric values for the same interaction types, so no value can be copied on authority; one internally consistent in-house table must be transcribed from published sources and human-approved before the detector/generator freeze. (2) **Movement model** — `cmd.drag` clobbers the game wizard and self-destructs unless `editor_scheme==3`; object-matrix commands are the verified default, but matrix movement has two open questions (detector must compose the matrix; does the matrix survive `.pse` round-trip?). (3) **No undo exists** in open-source PyMOL — snapshot-before-mutation plus seeded-spec replay are the only safety nets. (4) **Truthfulness is structural** — every threshold, DOI, and PDB ID needs a recorded human approval (`DATA_SOURCES.md` pattern), enforced by versioned manifests and every-id smoke tests.

## Key Findings

### Recommended Stack

Zero-install, zero-new-dependency: everything ships inside PyMOL 2.5.0. Code must be **Python 3.6-compatible** (WSL test shell is 3.6.9 — no numpy, no `dataclasses`; the Windows conda env's exact version is unverified — check once in the first headless smoke).

**Core technologies:**
- **PyMOL 2.5.0 host + cmd API** — runtime and vocabulary; every call cited `file:line` in STACK.md's verified toolbox.
- **PyQt5 via `from pymol.Qt import …`** — all GUI; never `from PyQt5 import` directly (bypasses the binding shim; grep-gated).
- **Wizard framework (`pymol.wizard.Wizard`)** — the *only* sanctioned hook for viewer clicks; custom wizards are passed as instances, no `pymol.wizard` package residency needed.
- **Object-matrix commands (`cmd.rotate/translate/transform_object`, `cmd.get_object_matrix`)** — recommended movement model; `cmd.drag` is constrained (single-object selection), replaces the active wizard, and self-destructs unless `editor_scheme==3`.
- **stdlib + math for the pure layer; numpy only in the cmd tier (Windows side)** — ⚠ cross-file reconciliation: STACK.md lists numpy for detection geometry, but PITFALLS verified WSL 3.6.9 has **no numpy**. The detector is a pure module, so it must be stdlib-only vec3 math; numpy stays in cmd-tier helpers validated by headless smoke.
- **JSON sidecar + `cmd.save`/`cmd.load`** — checkpoint = `.pse` (geometry, wizard stack auto-pickled) + pure JSON game state, zipped (v1 `.bcmz` → `.aamz` pattern).
- **No `cmd.undo`** — it is a no-op stub in open-source (`editor.py:25-36`); backup-snapshot + seeded-spec replay instead.

**Plugin install contract (fully mapped):** package dir + `__init__.py`; metadata comment block must be the *first* lines; module-level `__init_plugin__(app=None)`; `addmenuitemqt` for the menu; installs to `%APPDATA%\pymol\startup\`. Restart or `plugin_load aamatch`.

**Headless testing recipe — location: STACK.md, "Development Tools" table + "Installation" section step 5.** Distilled: stage package + script via the `wsl2win` copy script to a `/mnt/c` path → `cd` into the staged dir → `timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\smoke_01.py" 2>&1 | tail -50` → exit 0 = clean. Anything touching `pymol.Qt` at runtime **cannot** run this way — Qt is human-verify-only by design.

### Expected Features

**Must have (table stakes — all spec-mandated, nearly all proven by prior art):**
- Standard plugin install + **modeless** setup window with the 7 named buttons (Reset/Randomize/Save Setup/Load Setup/Generate & export/Cleanup/Start)
- Demo-set dropdown (curated, pre-downloaded, cited; ~9 tier slots) + user upload of small molecules
- Game generation: multi-level, NxN AA grids per molecule, capped randomization, **always solvable by construction**
- Core loop: click AA to select → move/rotate onto molecule → Confirm → detection → score (fraction of required interactions, **binary per interaction**); countdown, rolling info box, timer, required-interactions display
- Hint (recolor carbons only — no lines/dots, ever, during play), Skip/Give-up with confirmations
- Setup save/load, Generate & export, Import, Checkpoint save, Restart, Reset-to-grid, Cleanup
- Win screen stats; help panel + tooltips; `DATA_SOURCES.md` citation doc per demo set

**Should have (differentiators):**
- Always-solvable generation as an educational-fairness guarantee (AA-capability matrix + constraint-satisfying grid fill)
- Difficulty tiers as first-class data (grid N × molecule size × interaction-type count)
- Post-confirm per-interaction debrief (recommended extension beyond spec; strictly post-Confirm)
- Human-approved citation workflow as a trust feature; metal coordination conditional on ligand composition

**Defer (v1.x / v2+):**
- Water bridges (most geometry-heavy type; needs explicit waters in scenes)
- π-stacking split into parallel vs T-shaped subtypes (all three reference tools distinguish internally)
- Post-validate debrief enrichment, more demo sets → v1.x; VMD port → v2

**Landscape facts that shape design:** halogen-bond **donors are ligand-side only** (PLIP/BINANA) — demo curation gates whether the type is ever exercisable; PLIP documents hydrophobic hit "count explosion" without dedup — our **binary per-required-interaction scoring sidesteps this entirely**; BINANA documents distance-only metal coordination with rationale (v1 precedent, still needs human approval); ProLIF's CationPi/PiCation split shows the criteria table must encode *which partner* holds the cation.

### Architecture Approach

A proven 4-layer pattern from shipped v1: **Layer 1 pure game logic** (stdlib(+math) only: `level_spec`, `generator`, `detector`, `game_state`/`scoring`, `persistence`) → **Layer 2 cmd bridges** (`placement`, `geometry`, `session`, `controller` as orchestrator) → **Layer 3 viewer adapter** (thin `GameWizard`, no game logic — it gets *pickled into sessions*) and **Layer 4 Qt GUI** (modeless dialog singleton, callbacks, QTimer-only timers) → **Layer 0 PyMOL host**. Dependency direction is strictly downward; the composition root (`__init__.py`) is the only cross-layer wirer.

**Major components:**
1. **Pure detector + interactions module** — geometric criteria on collected atom records; thresholds as citable constants; direction-aware typing.
2. **Seeded generator + level spec** — single source of truth; Reset/crash-recovery/export all *replay the spec* rather than reverse PyMOL mutations.
3. **Wizard input adapter** — implements BOTH `do_pick` and `do_select`; canonical map for the default Viewing mode where `do_pick` never fires: `do_select` → `cmd.unpick()` → `cmd.select("pk1", name)` → `cmd.delete(name)` → `self.do_pick(0)`. Saves/restores prior wizard and `mouse_selection_mode`.
4. **Session/persistence bridge** — `.aamz` zip (`.pse` + `state.json`), magic+version headers, sentinel-first reconstruction on load, wizard `__getstate__` hygiene (no Qt/locks/controller on the pickled wizard).
5. **Identity & sentinel conventions** — identity = `(object, atom_id)` (+`alt`, `resv` where ambiguity possible); never `index`; game objects named `_aam_*`; sentinel `segi` + `b<-9`-style selectors (`b -999` is a malformed selector that matches nothing); cleanup deletes by prefix/sentinel only.

**Key data flow rule:** geometry crosses the bridge at exactly two points (grid-pose snapshot after materialize; detection on Confirm). During play only transforms flow; detection never runs per-frame. UI updates are callbacks, never PyMOL polling.

### Critical Pitfalls (top 5 of 15 — full ledger in PITFALLS.md)

1. **Qt tier contamination** — any code path touching `pymol.Qt` at runtime is human-verify-only; module-level Qt imports force MagicMock stubs onto every WSL test (bit v1 twice). Prevent: lazy Qt imports inside functions, entry module only; three-tier test discipline from Phase 1; Qt checkpoints written into plans, not discovered at review.
2. **Default-mode wizard trap** — `do_pick` never fires in the default 3-Button Viewing mode; the game looks broken for players while working on the dev box. Prevent: implement both entry points + the canonical select→pick map; save/restore prior wizard and `mouse_selection_mode`; mandatory human GUI check on a fresh PyMOL.
3. **`cmd.drag` vs the game's wizard** — `cmd.drag` replaces the active wizard and self-destructs unless `editor_scheme==3`; it also has a matrix-vs-coordinates duality with different reset semantics. Prevent: movement-model decision made explicitly (object-matrix commands recommended as verified default; `cmd.drag(wizard=0)` is an UNVERIFIED spike); reset = replay grid poses from the pure spec, sidestepping `matrix_reset` modes entirely.
4. **`cmd.create` merge-vs-replace + id-sharing** — creating onto an existing object can *replace* its state contents or silently no-op; copies share source atom ids (ate v1 state; 4 failed GUI-bug cycles before the final design). Prevent: count-asserted steps in every smoke; disjoint `resi`/`chain`/`segi` namespaces between grid AAs, ligand copies, and originals; build-in-temp-object then verified merge.
5. **No undo → corruption is permanent** — snapshot before every mutation; restore = delete+create two-step with count verification; better: regenerate from the seeded spec (the spec is the source of truth).

Also load-bearing: **WSL python3.6.9 has no numpy/dataclasses** (pure layer = stdlib math only), **alt-conf atoms share ids** (carry `(id, alt, resv)` in pick handling), **WSL→Windows path guard** (`to_windows_path()` before every `cmd.load/save`; resolve bundled data via `__file__`), **camera-vs-world frames** (`cmd.translate` defaults to camera coords), and **cleanup over-match** (sentinel/prefix only — never `hetatm`/`not polymer` filters).

## Implications for Roadmap

Based on combined research, suggested 7-phase structure. It merges ARCHITECTURE.md's dependency-driven 5-stage build order with PITFALLS.md's 9 topic names; the roadmapper may renumber/split, but the dependency logic should hold.

### Phase 1: Bootstrap — plugin skeleton + pure setup/persistence layer
**Rationale:** Prove the WSL→Windows toolchain end-to-end before any game code; install the layer contract, path helper, and backup module that every later phase depends on. The modeless-Qt decision is made *here* as a rule even though Qt UI comes later (retrofit is a rewrite).
**Delivers:** Installable plugin shell with menu entry; one green headless smoke (a tiny load via the STACK.md recipe); `to_windows_path()`; backup module; pure `setup_state` + `persistence` + `level_spec` with WSL tests; grep gates + import gates encoded in AGENTS.md.
**Addresses:** Plugin install, setup persistence (Save/Load Setup formats).
**Avoids:** Pitfalls 1, 2, 3, 4 (rules), 9.

### Phase 2: Interaction definitions + detector + always-solvable generator (pure core)
**Rationale:** The critical path from FEATURES.md's dependency graph runs through the human-approved threshold table → capability matrix → solvable generation → detection → scoring. Pure modules are fully WSL-testable; failures here are the cheapest. **Human gate:** threshold table approval happens in/before this phase.
**Delivers:** `interactions.py` + `detector.py` (stdlib math), AA-capability matrix, seeded always-solvable generator (global allocation pass), scoring; ≥100-seed invariant tests (disjoint slots, solvability); threshold-provenance doc.
**Addresses:** P1 detection engine, solvability guarantee, generation logic, scoring.
**Avoids:** Pitfalls 3, 11, 12 (typing/frame policy explicit), 14 (threshold provenance).

### Phase 3: Bundled data + cmd-only placement/detection path (headless-verifiable)
**Rationale:** Materialize specs into real PyMOL objects and prove generate → place → detect → score *headlessly, with no GUI and no wizard* — isolating `cmd.create`, path, identity, and perf risks while they are cheap.
**Delivers:** Bundled AA/ligand structures + versioned MANIFEST; `placement.py`/`geometry.py`; count-asserted create smokes; end-to-end headless smoke that detects a scripted interaction.
**Addresses:** Demo supply skeleton, generation materialization, geometry extraction.
**Avoids:** Pitfalls 7, 8, 2, 15.

### Phase 4: Viewer interaction — wizard + movement model
**Rationale:** The highest-leverage early decision per PITFALLS (movement model → detector input → reset semantics → checkpoint persistence). Isolated before GUI work; needs human GUI verification.
**Delivers:** `GameWizard` with the canonical pick map and mode save/restore; movement model decided + implemented (object-matrix default; `cmd.drag(wizard=0)` spike with recorded verdict); reset-to-grid via spec replay; wizard panel (Confirm/Reset/Done); selected-state color feedback.
**Addresses:** Core gameplay loop (spec 7.1–7.2).
**Avoids:** Pitfalls 5, 6, 8, 12 (matrix-blindness decision).
**Research flag:** movement-model spike — `cmd.drag(wizard=0)` under a custom wizard is UNVERIFIED; default `editor_scheme` on stock installs is UNVERIFIED (drives fallback UX).

### Phase 5: Qt GUI — setup window + game tab
**Rationale:** GUI is a thin shell over a now-proven controller; v1's Qt patterns (modeless singleton, callbacks, QTimer) transfer directly, so this is assembly rather than invention — but it concentrates human-verify checkpoints.
**Delivers:** Modeless setup window with the 7 buttons and params; game-status tab (info box, timer, required interactions, Hint, Confirm, Skip/Give-up); 3-2-1 countdown; win screen (delay modal ~100 ms after last `cmd.color` + refresh); timer pause during modal children.
**Addresses:** The table-stakes UI set.
**Avoids:** Pitfalls 4, 1; UX timer-fairness pitfall.

### Phase 6: Scoring lifecycle + checkpoint/export/import + cleanup
**Rationale:** Depends on gameplay working end-to-end; persistence gates are verified here with the whole loop live.
**Delivers:** `.aamz` zip round-trip (save → quit → relaunch → load restores timer/score/placements); import-with-reconcile; Restart/Reset/Cleanup wired to snapshot + spec replay; running totals, level advance, skip partial scores.
**Addresses:** The persistence set, scoring lifecycle.
**Avoids:** Pitfalls 10 (sidecar + sentinel-first reconstruction; **matrix round-trip smoke = gate 1**), 13 (cleanup isolation), 9.
**Research flag:** `.pse` matrix round-trip smoke; wizard-restore-with-plugin-reload edge case; valence display setting name.

### Phase 7: Demo curation + citations + polish + performance
**Rationale:** Content is gated by the human approval protocol (agent proposes → human verifies → fetch/commit); polish lands last when behavior is stable.
**Delivers:** ~9 tier slots curated with `DATA_SOURCES.md` entries (PDB/SDF ID + DOI + protonation source + license); versioned manifest + every-manifest-id smoke; perf budget check (Generate < 30 s, pick/drag < 200 ms); help panel + tooltips; README sections filled.
**Addresses:** Demo sets + citation doc, in-game help, perf.
**Avoids:** Pitfalls 14, 11.3, 15.

### Phase Ordering Rationale

- **Dependency-driven:** thresholds → capability matrix → solvable generation → detection → scoring → UI presentation → persistence → content. Every phase depends only on earlier ones; the riskiest unknowns (detector criteria, movement model) get isolated spikes in phases 2–4 where failure is cheap.
- **Testability-driven:** everything verifiable in WSL or headless Windows PyMOL is front-loaded (phases 1–3); Qt/human-verify work is back-loaded (5) and concentrated (4–5 checkpoints).
- **Pitfall-driven:** bootstrap installs the gates (paths, purity, backup, modeless rule) that structurally prevent the highest-frequency failure classes; count-asserted smokes and identity conventions land *with* the first object creation, not after.

### Research Flags

Phases likely needing deeper research / spikes during planning:
- **Phase 4 (viewer interaction):** movement-model spike (`cmd.drag(wizard=0)` interplay — UNVERIFIED; default `editor_scheme` — UNVERIFIED); pick granularity decision (atom vs residue `mouse_selection_mode`); human GUI checks mandatory.
- **Phase 6 (persistence):** matrix round-trip smoke before committing the movement model; wizard `__getstate__` hygiene; restore with plugin reload.
- **Phase 2 (detection):** threshold values are a *human transcription/approval gate*, not a research gap (published tables exist at PLIP help page + BINANA INTERACTIONS.md; the tools disagree → one in-house table). Geometric edge cases (alt-conf policy, frames, protonation, ring identification) need phase-level research.
- **Phase 7 (demos):** process-heavy human approval protocol; multi-state ligand policy (state 1 vs collapse).

Phases with standard patterns (skip research-phase):
- **Phase 1 (bootstrap):** install contract, stub tests, backup module, path helper — all proven in shipped v1.
- **Phase 3 (cmd placement):** v1 placement/sentinel/persistence patterns proven; only the AA-grid specifics are new.
- **Phase 5 (Qt GUI):** v1 Qt patterns proven end-to-end (modeless singleton, QTimer, callbacks, win-screen modal timing).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Every API claim cited `file:line` from the local PyMOL 2.5.0 tree; headless recipe runtime-proven across v1's 12 phases. LOW spots: Windows env exact Python/Qt versions (one-time runtime check), `within` selector availability (avoid — numpy/stdlib engine), chempy fragments inventory. |
| Features | HIGH | Interaction sets + parameter *shapes* verified against official PLIP/ProLIF/BINANA docs fetched 2026-09-05; prior-art feature set read directly from shipped source. Numeric *values* deliberately not asserted (policy). MEDIUM for speculative extensions (debrief). |
| Architecture | HIGH | 4-layer pattern is the shipped v1 architecture; all wizard/cmd mechanics cited. UNVERIFIED: `cmd.drag(wizard=0)` under a custom wizard; chempy fragment inventory. |
| Pitfalls | HIGH | 15 pitfalls are either prior-art-observed real bugs (with diag artifacts) or source-verified. MEDIUM for detection chemistry edge cases; threshold values intentionally open (human gate). |

**Overall confidence:** HIGH — unusually strong, because both the host's source code and a shipped prior-art plugin built under identical constraints are locally available and were read directly.

### Gaps to Address

Open questions requiring **human decisions** (gate the phases noted):

- **Threshold table approval (gates Phase 2):** transcribe per-type values from the published PLIP help-page table and BINANA `INTERACTIONS.md` (ProLIF docs as cross-check); the tools **disagree** on several cutoffs → adopt one internally consistent in-house table, each row recorded with source + human approval. Related per-type decisions: π-stacking — include T-shaped/edge-to-face in v1's single category? metal coordination — approve distance-only criterion (BINANA precedent)? hydrophobic — "≥1 qualifying contact" semantics? ring-disk projection — any-atom-in-disk vs center-based?
- **Exclusive vs block-exclusive semantics (gates Phase 1/2 setup + generator):** spec.md lines 18–20 are ambiguous. Recommended reading: *exclusive* = only listed interactions count; *block-exclusive* = listed ones excluded; unset = random. Confirm with human before requirements freeze.
- **Movement-model spike (gates Phase 4):** object-matrix commands are the verified recommended default; `cmd.drag(wizard=0)` under a custom wizard is UNVERIFIED — run the spike headlessly; if native drag is wanted, verify `editor_scheme` default on a stock install and design the post-drag wizard re-install + fallback UX.
- **`.pse` matrix round-trip smoke (gates Phase 6, informs Phase 4):** move an object via matrix → save → reload → compare `cmd.get_object_matrix`. If matrices don't survive, persist transforms as sidecar matrices/coordinates. Run *before* freezing the movement model.
- **Detector input under matrix movement:** if object-matrix movement is chosen, the detector must compose the object matrix over stored coordinates (matrix blindness) — decide together with the spike above.
- **Upload format pinning:** SDF/MOL2 carry bond orders (valence-correct rendering + chemistry); PDB needs CONECT records — pin accepted formats in requirements.
- **Windows conda env versions:** one-time `import sys; print(sys.version)` + `QT_VERSION_STR` in the first headless smoke.
- **Valence display setting name:** `cmd.valence` verified; the display setting (`set valence, on`-style) needs runtime confirmation.
- **Multi-state ligand policy:** detect on state 1 vs collapse-to-single-state — decide in demos with curated data.
- **Waters/alt-conf policy:** explicit exclusion rules from contact counting; altloc A-only vs best-conformer — fix in the detection module's documented chemistry policy.

## Sources

### Primary (HIGH confidence)
- **Local PyMOL 2.5.0 open-source source tree** `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/bioCHEMeleon/tmp/pymol-src/modules/pymol/` — wizard/, wizarding.py, editing.py, creating.py, querying.py, exporting.py, importing.py, plugins/, Qt/ (all `file:line` citations across the four files)
- **Shipped prior art** `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/AA-match/tmp/bioCHEMeleon/` — AGENTS.md (headless recipe, grep gates, pitfall ledger), wizard.py, game.py, persistence.py, generators.py, registry.py, backup.py, gui_*.py, tests/, smoke/diag_*.py (17 forensics files), DATA_SOURCES.md, MILESTONES.md
- **PLIP official help page** https://plip-tool.biotec.tu-dresden.de/plip-web/plip/help — interaction list, two-stage algorithm, dedup rules, published threshold table (values not transcribed per policy)
- **ProLIF official docs** https://prolif.readthedocs.io/en/latest/ — class list, parameter shapes, v2.2.1, Apache-2.0
- **BINANA** https://github.com/durrantlab/binana + INTERACTIONS.md — distance-only metal rationale, charge representative points, ring-disk projection, protonation note

### Secondary (MEDIUM confidence)
- `Pymol-script-repo/plugins/` (outline.py, show_contacts.py, apbsplugin.py, mtsslWizard.py) — menu/dialog/wizard idioms; read-only reference
- Foldit live homepage https://fold.it/ — genre feature surface (tiers, educator resources); deeper mechanics flagged SPECULATIVE
- Previous project's v1 research recovered from git (`bioCHEMeleon` @ `123b115`), incl. Phase 8 persistence research — sentinel-first reconstruction

### Tertiary (LOW confidence — validate during implementation)
- Windows conda env exact Python/Qt versions — one-time runtime check
- `cmd.drag(wizard=0)` coexistence with a custom wizard; default `editor_scheme` on stock installs — Phase 4 spike
- Object TTT/state-matrix `.pse` round-trip on 2.5.0 — Phase 6 gate-1 smoke
- `within/near_to` selector ops, chempy fragments inventory, valence display setting name — avoid or verify at first use

---
*Research completed: 2026-09-05*
*Ready for roadmap: yes*
