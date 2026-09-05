# Feature Research

**Domain:** Educational molecular-interaction matching game (PyMOL 2.5.0 plugin) — small-molecule ↔ amino-acid interaction placement, detection, and scoring
**Researched:** 2026-09-05
**Confidence:** HIGH for interaction-tool feature sets (official docs fetched today) and prior-art game features (source read directly); MEDIUM for speculative extensions (flagged inline)

> **Numeric-threshold policy (project constraint):** This file contains **no numeric interaction thresholds**. PLIP and BINANA both publish full threshold tables at their official URLs (existence verified 2026-09-05 — see Sources). The later human-verification phase must transcribe the adopted values from those URLs / primary literature and record explicit human approval. Where this file says "thresholds exist and are published," that claim is HIGH confidence; the *values* are deliberately not transcribed here.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features without which the game feels broken. All are spec.md-mandated unless noted; prior art (bioCHEMeleon) proves the implementation pattern for most.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Install as a standard PyMOL plugin (Plugin Manager + menu entry) | Spec req 0; users expect zero-friction install | LOW | Proven pattern in prior art: `__init_plugin__(app=None)` + `addmenuitemqt`, module-level dialog singleton (GC prevention). |
| Setup window on plugin start (modeless) | Spec req 1; player must configure before play | MEDIUM | Modeless dialog (`show()`, never `exec_()`) so the 3D viewer stays interactive — proven pattern; modal only for child dialogs (file/message). |
| Demo-set dropdown (curated, pre-downloaded) | Spec req 2 + Note 1; offline constraint | MEDIUM (UI) / process-heavy (curation) | ~9 tier slots (Easy×3, Hard×3, Challenge, Very challenging×2). Prior art's `DEMO_MANIFEST` with tier labels is a direct template. |
| Upload of user small molecules (right format) | Spec req 2 ("or to upload a set of small molecules of right format") | MEDIUM | `QFileDialog` pattern proven. **Format choice matters:** SDF/MOL2 carry bond orders (valence-correct rendering); PDB needs CONECT records — pin accepted formats in requirements phase. |
| Molecules-per-level + difficulty-count parameters (with sane caps) | Spec req 2; defaults 2–5 and 3–5 | LOW | Prior art's dynamic cap (`hider_count_cap(atom_count)`) proves the "cap by molecule size" UX. |
| Allowed-interactions list: exclusive / block-exclusive / random | Spec req 2; core difficulty control | MEDIUM | Three modes are spec'd. ⚠ **Semantics need requirements-phase clarification:** "exclusive = any supporting interactions" vs "block-exclusive = specific interaction selected" is ambiguous in spec.md lines 18–20 — recommended reading: exclusive = only listed interactions count; block-exclusive = listed ones excluded; unset = random. Confirm with human. |
| 7 setup buttons: Reset / Randomize / Save Setup / Load Setup / Generate & export / Cleanup / Start | Spec req 3; all seven named explicitly | MEDIUM | All seven have proven analogs in prior art (`setup_state.DEFAULTS`/`randomize_state`/`validate_state`, JSON setup round-trip, export button, backup/restore cleanup, bold Start button). |
| Setup persistence (Save/Load Setup to file) | Spec req 3.3/3.4; educators reuse configs | LOW | Proven: versioned JSON with format tag + magic + `validate_state` round-trip (prior art `SETUP_FORMAT`, `.bcm.setup.json`). |
| Generate & export + Import game (shareable file) | Spec req 3.5, 6 (import button) | MEDIUM | Proven pattern: zip archive bundling `.pse` session + JSON sidecar with magic + version, checkpoint-vs-puzzle kinds, reconcile-on-import (`persistence.py`). |
| Game generation: levels of increasing difficulty; per molecule an NxN grid of randomized (capped) AAs | Spec req 5/7; the core new surface | HIGH | No prior-art equivalent — this is the main new engineering. Grid placement, per-difficulty N, molecule size, interaction-type count. Levels always solvable (see Differentiators). |
| Click-to-select AA + move/rotate gameplay in the 3D viewer | Spec req 7.1–7.2; the core loop | HIGH | Wizard-based click loop is proven (prior art `PickWizard`; pick while drag still rotates). *Moving/rotating a selected AA* is new — PyMOL editing APIs must be verified in `pymol-src` during design. |
| 3-2-1 countdown, then game start; auto-switch to game tab | Spec req 5; game-feel | LOW | Proven `QTimer.singleShot` chain; timer starts after GO. |
| Rolling info box + elapsed timer (outside the info box) | Spec req 6; spec UI standard | LOW | Proven: read-only QTextEdit log + 1 Hz QTimer on the Qt main thread (never a `threading.Thread` touching `cmd.*`). |
| Required-interactions display (type + number; `any` or explicit list) | Spec req 6 | LOW | Pure formatting; prior art's `format_remaining` proves the pure-helper pattern. |
| Confirm → detection → score (fraction of required interactions, binary each) | Spec req 6/7.3; the core value ("player places, game detects") | HIGH | The 7-interaction detection engine is the single riskiest component. Criteria concepts verified against PLIP/ProLIF/BINANA (see Competitor Feature Analysis); numeric thresholds require human verification (flagged above). |
| Per-molecule score + running total; advance to next molecule/level | Spec req 7.3–7.4 | LOW–MEDIUM | Straightforward once scoring exists. |
| Hint button (recolor carbons of AAs that could form an interaction) | Spec req 6; differentiation from a "reveal" | MEDIUM | Reuses the detection engine in *capability* mode ("could this AA form any required interaction?"). Must recolor only — no lines/dots (see Anti-Features). Prior art hint pattern (vicinity recolor, restricted to the target object so backup copies aren't touched) transfers. |
| Skip molecule / Give up, each with a confirmation warning | Spec req 6; fairness | LOW | Proven `QMessageBox.question` pattern; skip stores partial score per PROJECT.md. |
| Save checkpoint (PyMOL session + game-state sidecar) / Restart / Reset AAs to grid | Spec req 6 | MEDIUM | Checkpoint = `.pse` + sidecar zip (proven). Restart and Reset need the stored initial state — requires snapshot-at-start (see Dependencies). |
| Win screen: per-level scores, total, stopped timer/time, molecules & levels, skip/give-up counts | Spec req 8 | LOW | Proven stats-modal pattern. Gotcha from prior art: delay the modal ~100 ms after the last `cmd.color` + `cmd.refresh()` so the redraw lands before Qt blocks the event loop. |
| Cleanup model (remove game-generated objects, restore original state) | Spec req 3.6 | MEDIUM | PyMOL open-source has **no undo** — prior art's snapshot→restore→discard pattern (backup object + sentinel tagging) is the proven mechanism. |
| In-game help & tooltips (simple, clear, sufficient explanation) | Spec UI standard | LOW | Proven: `HELP_HTML` panel + tooltip on every widget (prior art even documents the scroll-wheel-vs-clipping-plane PyMOL gotcha). |
| Demo-data citation document (human-verified) | Spec Note 1 + truthfulness constraint | LOW (file) / process-heavy | Proven: `DATA_SOURCES.md` with PDB ID + DOI + license per entry (RCSB CC0 etc.), consolidated repo-root doc + per-demo pointer file. |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Always-solvable-by-construction generation** | Educational fairness: every level is winnable; difficulty comes from grid size, molecule size, and interaction-type count — not from luck | HIGH | Needs an AA-capability matrix (which standard AAs can form each interaction type) + a constraint-satisfying grid fill: per required interaction, guarantee ≥1 capable AA in the grid, rest = distractors. Capability matrix itself must be human-reviewed with the interaction definitions. |
| **Difficulty tiers as first-class data** (grid N × molecule size × interaction-type count; ~9 demo tier slots) | Progression/curriculum structure; educators can pick a tier | MEDIUM | Prior art proved 4 tier labels + 9 demos in a tier-ordered manifest — same shape carries over. |
| **No-helper-visuals practice mode** | The pedagogical identity: players learn to *see* 3D geometry without dashes; PLIP-style interaction overlays exist only post-hoc | LOW (cost) | Enforced negatively: hint = recolor only; scoring UI = numbers; geometry display only after Confirm/game end. Must be stated in help so players don't think it's missing. |
| **Protonation-state-correct, valence-correct small molecules with provenance** | BINANA explicitly warns accuracy degrades without correct polar hydrogens/charges (official doc, verified) — our H-bond/salt-bridge detection inherits that requirement; demos sourced "from known binding database and structure also from a database" | MEDIUM–HIGH | Curation + rendering. Decide: explicit hydrogens in data vs PyMOL valence inference — flag for the detection-definitions phase. Valence-correct display favors bond-order-carrying formats (SDF/MOL2). |
| **Checkpoint save & resume mid-game** | Long games (multiple levels) survive session close; educators can hand out half-finished states | MEDIUM | Proven sidecar mechanics, but state here is richer (positions/orientations of placed AAs, per-molecule scores, counters). |
| **Randomize + three allowed-interaction modes** | Replayability; one setup → many distinct games | MEDIUM | Proven `randomize_state` + lock-source concept transfers; interaction-mode sampling is new logic over the v1 interaction set. |
| **Post-confirm interaction debrief (which required interactions formed, which missed)** | The teaching moment: after Confirm, show per-interaction results — PLIP's own product is exactly this (post-analysis overlays in a PyMOL session), so it's the professional analog, deliberately gated to post-confirm | MEDIUM | Extension beyond spec's "show the molecule's score" (**SPECULATIVE** — spec only requires the score; the per-interaction breakdown is recommended). Strictly after Confirm or game end to respect the no-helper rule. |
| **Metal coordination conditional on ligand composition** | Honest chemistry: feature only activates when the level's ligand actually carries a metal | LOW–MEDIUM | Verified precedent: PLIP's tutorial example (1XDN) is an ATP+Mg composite ligand; BINANA detects metal bonds distance-only and documents why angle checks are omitted. Demo curation must include ≥1 metal-containing ligand for this to ever trigger. |
| **Human-approved citation workflow as a trust feature** | Every demo set's PDB/SDF IDs, protonation source, and DOIs are human-verified before shipping — rare rigor for educational plugins | process cost | Proven: DATA_SOURCES.md protocol (agent proposes → human verifies → fetch/commit). |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Helper lines/dots/ghost geometry during gameplay | "PLIP draws dashes; it's clearer" | Spec-forbidden — it defeats the core value (practicing 3D perception); turns the game into a coloring exercise | Recolor-only hint during play; per-interaction debrief strictly after Confirm; post-game reveal |
| Runtime network fetching (fetch PDB by code, download demos on demand) | Prior art had it; feels convenient | Spec + PROJECT.md forbid network at runtime; reproducibility/citation problems | Pre-downloaded demo sets committed with citations; user upload path |
| prolif / PLIP / BINANA as runtime dependencies | "The criteria come from them, just import them" | ProLIF requires RDKit + MDAnalysis; PLIP requires OpenBabel; violates the only-pymol-shipped-libs constraint | In-house numpy-only detection; thresholds transcribed from their published tables and human-verified |
| Water bridges (v1) | PLIP and ProLIF both detect them; chemically real | Requires explicit water molecules placed in generated scenes — conflicts with the grid/solvability model; the most complex parameter shape (six parameters in PLIP); no water in the v1 demo model | Defer to v1.x/v2; keep the detection API extensible so a water-bridge checker can slot in |
| Protein–protein / DNA-RNA–ligand modes (PLIP advanced modes) | Broader audience | Grid game is defined on small-molecule ↔ AA; protein partners can't be dragged by a player | Keep v1 scoped to small molecule ↔ amino acid |
| Covalent-bond interactions | "Complete the chemistry" | Even PLIP lists covalent bonds as unsupported (verified); not a non-covalent placement exercise | Stay with the v1 seven |
| Auto-snap / auto-optimal-placement assist | "Dragging in 3D is fiddly" | Removes the skill being practiced; silently solves the level | Confirm + rescore loop; skip button for stuck players; difficulty cap on grid N keeps fiddliness bounded |
| Multiplayer / leaderboards / online accounts (Foldit-style) | Social motivation | Offline plugin, no network at runtime; server infrastructure out of scope | Local win-screen stats; shareable exported games |
| Scripting/recipes API (Foldit-style user scripts) | Power users | Scope creep; arbitrary user code inside PyMOL (safety) | Export/import file formats as the extension surface |
| VMD port in v1 | Root AGENTS anticipates v2 | Splits focus; viewer-specific APIs differ | Keep core (detection, generation, scoring) viewer-agnostic where cheap; VMD is v2 |

## Interaction-Detection Landscape (what the reference tools detect)

This grounds the v1 interaction set and the criteria-table design. All statements below are about the *reference tools' documented behavior*, not AA-match's adopted criteria.

### PLIP (Protein-Ligand Interaction Profiler) — official help page, fetched 2026-09-05

- **Detects:** hydrogen bonds, water bridges, salt bridges, halogen bonds, hydrophobic interactions, π-stacking, π-cation interactions, metal complexes. Modes: protein–ligand (default), protein–protein, DNA/RNA–ligand.
- **Algorithm shape (two stages):** (1) classify potential interacting groups — hydrophobic atoms (carbon with only C/H neighbors), aromatic rings (ring perception + planarity fallback), H-bond donors/acceptors, charged groups, halogen donors/acceptors, water; (2) apply per-interaction geometric rules.
- **Parameter shapes per interaction (variable names verified on the help page; values published there, to be transcribed by the human):**
  - H-bond: donor–acceptor distance max + donor angle (D-H···A) min.
  - π-stacking: ring-center distance max + angular deviation from ideal (90° T-shape / 180° parallel) + center-projection offset max.
  - Cation-π: charge-center → ring-center distance max (+ extra angle criterion for ligand tertiary amines).
  - Salt bridge: opposite charge-center ↔ charge-center distance max (no extra geometry).
  - Hydrophobic: hydrophobic-atom pair distance max, **plus mandatory reduction/clustering steps** — PLIP explicitly documents that hydrophobic hits "can easily surpass all other interaction types combined" without dedup (per-residue closest-only, then per-atom closest-only).
  - Halogen bond: distance max + donor angle + acceptor angle + angular deviation.
  - Water bridge: two distances + two angles — **not in AA-match v1**.
  - Metal complex: distance max **plus** coordination-geometry fitting against known geometries (linear, trigonal planar/pyramidal, tetrahedral, square planar, trigonal bipyramidal, square pyramidal, octahedral), removing superfluous targets.
- **Dedup/precedence rules (documented behavior — directly relevant to AA-match's binary scoring):** a donor takes part in only one H-bond (keep the one closest to 180°); acceptors may be multi-partner (bifurcated); H-bonds between groups already forming a salt bridge are suppressed; hydrophobic contacts between π-stacked rings are removed.
- **Where the human verification phase gets PLIP's numbers:** the threshold table is published at the help page URL (variables `HBOND_DIST_MAX`, `HBOND_DON_ANGLE_MIN`, `PISTACK_DIST_MAX`, `PISTACK_ANG_DEV`, `PISTACK_OFFSET_MAX`, `PICATION_DIST_MAX`, `SALTBRIDGE_DIST_MAX`, `HALOGEN_DIST_MAX`, `HALOGEN_ACC_ANGLE`, `HALOGEN_DON_ANGLE`, `HALOGEN_ANGLE_DEV`, `HYDROPH_DIST_MAX`, `AROMATIC_PLANARITY`, `METAL_DIST_MAX`, water-bridge set). PLIP 2025 citation shown on the site: Schake, Bolz et al., doi:10.1093/nar/gkaf361 — must be human-verified before appearing in any shipped doc.

### ProLIF — official docs, fetched 2026-09-05 (latest release 2.2.1, 2026-07-27; Apache-2.0)

- **Detects (interaction classes):** Anionic, Cationic (charged pairs — salt-bridge territory), HBAcceptor / HBDonor (+ Implicit variants), Hydrophobic, VdWContact, PiStacking — split into **FaceToFace** and **EdgeToFace**, CationPi and **PiCation** (directionality: which side of the pair holds the cation), MetalDonor / MetalAcceptor, XBDonor / XBAcceptor (halogen), WaterBridge.
- **Base-class shapes (from the docs class list):** `Distance`, `SingleAngle`, `DoubleAngle`, `BasePiStacking`, `BridgedInteraction` — i.e., every interaction reduces to distance + one/two angle predicates, with π-stacking as its own family. Matches PLIP's shape and validates an AA-match criteria table built from (distance, angle[s]) rows per interaction type.
- **Relevant concepts for AA-match:** the ligand-side vs protein-side naming (CationPi vs PiCation) shows detection must be explicit about *which partner* is which — for the game, the AA is always one partner and the small molecule the other; the criteria table should encode direction so the generator's feasibility check is symmetric with the detector. `get_residues_near_ligand()` is the binding-site-pool concept — AA-match's NxN grid is the game-ified analog.
- **Runtime role:** none. ProLIF depends on RDKit + MDAnalysis — unusable under the zero-extra-deps constraint; reference only. Paper: doi:10.1186/s13321-021-00548-6 (verify before citing in shipped docs).

### BINANA — official repo INTERACTIONS.md, fetched 2026-09-05 (BINANA 2.1, Apache-2.0; original paper Durrant & McCammon, J Mol Graph Model 2011, doi:10.1016/j.jmgm.2011.01.004)

- **Detects:** close contacts (two distance tiers, atom-type pair tallies), electrostatics, binding-pocket flexibility (secondary-structure characterization), hydrophobic contacts (carbon–carbon), hydrogen bonds, halogen bonds, salt bridges, π interactions (**parallel π-π stacking + T-stacking** + cation-π), metal coordination bonds, ligand atom types / rotatable bonds.
- **Concepts worth adopting (documented design, verification still required):**
  - **Charge representative points:** each charged group gets one representative coordinate (carboxylate: midpoint of the two oxygens; guanidino: midpoint of the terminal nitrogens; Lys: the amine N; His: midpoint of the ring Ns — BINANA treats His as always charged; ligand side: quaternary/sp³ ammonium, guanidino, carboxylate, phosphate, sulfonate, plus a metal-cation name list). Salt bridge = opposite-charge representative points within cutoff. Gives a simple, implementable charged-group table for both AA side chains and small molecules.
  - **Ring-disk projection for π interactions:** rings get a center, plane, radius + padding; partners are *projected onto the plane* and must land inside the padded disk — BINANA explicitly notes projecting only the center is insufficient because stacking is often off-center. Relevant to how the game scores a placed AA (any-atom-in-disk vs center-based — a criteria-table decision for the human).
  - **Metal coordination is distance-only, with published rationale:** many geometries are possible, real L-M-L angles deviate substantially, and coordination sites may be vacant; "detecting metal-coordination bonds by distance is sufficient in almost all cases." → Direct prior-art support for AA-match using a **simple distance-only metal criterion in v1** (decision still needs human approval, but the precedent is documented).
  - **Protonation note:** BINANA recommends polar hydrogens + partial charges (PDBQT) and warns that without hydrogens it must *guess* protonation from geometry with worse accuracy → independent support for the spec's "specific protonation state, correct valence" requirement.
  - Aromatic rings: ligand rings found by a planarity (dihedral-deviation) criterion; protein aromatic residues fixed by residue name — Phe/Tyr/His one ring, **Trp two rings**.
- **Where the human verification phase gets BINANA's numbers:** the complete parameter-value table is in `INTERACTIONS.md` at the repo URL (human transcribes + approves).

### Coverage matrix vs AA-match v1 set

| Interaction | PLIP | ProLIF | BINANA | AA-match v1 | Notes |
|---|---|---|---|---|---|
| H-bond | Yes | Yes (Donor/Acceptor + Implicit) | Yes | Yes | Shape agreed by all three: distance + D-H···A angle |
| Salt bridge | Yes | Yes (Anionic+Cationic) | Yes | Yes (ionic folded in) | Charge-center distance; PLIP suppresses overlapping H-bonds |
| π-stacking | Yes (one type; T + parallel via angle deviation) | Yes (FaceToFace + EdgeToFace) | Yes (parallel + T-stacking) | Yes (single category) | **Decision needed:** does v1 π-stacking include T-shaped/edge-to-face? Phase research + human approval |
| Cation-π | Yes | Yes (directional pair) | Yes | Yes | Charge-point → ring projection |
| Hydrophobic contact | Yes (with clustering) | Yes (+ VdWContact variant) | Yes (C–C tally) | Yes | Must define "at least one qualifying contact" semantics for binary scoring |
| Halogen bond | Yes | Yes (XBDonor/XBAcceptor) | Yes | Yes | Distance + donor/acceptor angles |
| Metal coordination | Yes (distance + geometry fitting) | Yes (MetalDonor/MetalAcceptor) | Yes (**distance-only**, with rationale) | Yes (conditional on metal in ligand) | v1 recommendation: distance-only; human approves |
| Water bridge | Yes | Yes | — | **— (future)** | Most geometry-heavy type; defer |
| Electrostatics scoring / flexibility stats | — | — | Yes | — | Analysis outputs, not gameplay |
| Covalent / weak C-H H-bonds / higher-degree water bridges | Documented unsupported | — | — | — | Keep out; matches the tools' own limits |

**Cross-tool finding (HIGH confidence, design-relevant):** PLIP and BINANA publish *different* numeric values for the same interaction (e.g., their halogen-bond and metal-coordination distance cutoffs differ), even though the parameter *shapes* agree. AA-match therefore cannot "copy a threshold" — it must adopt **one internally consistent, human-approved in-house table**, cited per-row. This confirms the existing project Key Decision.

## Feature Dependencies

```
[Interaction definitions + human-verified thresholds]
    └──requires──> [AA-capability matrix (AA ↔ interaction types)]
                       └──requires──> [Always-solvable grid generation]
                                          └──requires──> [Game generation (levels, molecules, NxN grids)]
                                                             └──requires──> [Confirm + detection + scoring]
                                                                                └──requires──> [Running total + level advance]
                                                                                                     └──requires──> [Win screen stats]

[Detection engine] ──enables──> [Hint recolor]         (capability-mode reuse)
[Detection engine] ──enables──> [Post-confirm debrief] (results-mode reuse)

[Game generation] ──enables──> [Initial-state snapshot] ──enables──> [Restart / Reset / Checkpoint save / Cleanup]
[Persistence formats (setup JSON, game archive)] ──enables──> [Save/Load Setup, Generate & export, Import, Checkpoint]
[Demo curation workflow (human approval)] ──enables──> [Demo-set dropdown + citations doc]
[Plugin install] ──enables──> everything (menu entry)

[No-helper-visuals rule] ──conflicts──> [any live interaction-geometry display, snap assists]
[Offline constraint] ──conflicts──> [runtime fetch, leaderboards, online anything]
[Zero-extra-deps constraint] ──conflicts──> [prolif/PLIP/BINANA as libraries]
[Metal coordination] ──conditional──> [demo sets containing a metal-bearing ligand]
[Halogen bond] ──conditional──> [halogen-bearing demo ligands]  (donors live on the ligand side per PLIP/BINANA)
```

### Dependency Notes

- **Scoring requires detection; detection requires definitions; definitions require human approval.** The critical path for the whole roadmap runs through the human-verified threshold table. Everything downstream (hint, debrief, solvability) consumes the same engine.
- **Checkpoint/Restart/Cleanup require the initial-state snapshot**, which generation must persist before play starts (prior art: snapshot *before* any mutation — PyMOL open-source has no undo).
- **Hint must reuse detection in capability mode** ("could this AA form a required interaction?"), not a separate heuristic — otherwise hint and scoring can disagree.
- **Metal coordination is conditional** on ligand composition; demo curation and the level generator must agree on when the metal type is offered.
- **Halogen bonds need halogenated ligands**: both PLIP and BINANA treat halogen-bond *donors* as ligand-side (proteins assumed halogen-free), so demo curation determines whether the type is ever exercisable.
- **Upload format and valence rendering are coupled**: PDB without bond-order/CONECT info undermines the "correct valence" requirement; SDF/MOL2 carry bond orders.
- **Exclusive/block-exclusive semantics are ambiguous in spec.md** — resolve before requirements freeze.

## MVP Definition

### Launch With (v1)

v1 *is* the specced game; these are the must-haves within it:

- [ ] Plugin install + modeless setup window with the 7 buttons — the product's front door
- [ ] Demo-set dropdown (curated, pre-downloaded, cited) + user upload — content supply
- [ ] Game generation: multi-level, NxN grids, capped AA randomization — the game itself
- [ ] Always-solvable generation — educational fairness (differentiator on the critical path)
- [ ] Detection engine for the v1 seven (H-bond, salt bridge, π-stacking, cation-π, hydrophobic, halogen bond, metal-conditional) with human-verified thresholds — the core value
- [ ] Select/move/rotate gameplay + Confirm + binary scoring — the loop
- [ ] Countdown, info box, timer, required-interactions display — game feel
- [ ] Hint (recolor-only), Skip/Give-up with warnings — pacing & mercy
- [ ] Setup save/load, Generate & export, Import, Checkpoint save, Restart, Reset, Cleanup — persistence set
- [ ] Win screen with per-level scores, time, skip/give-up counts — closure
- [ ] Help panel + tooltips + citations doc — spec UI & truthfulness standards

### Add After Validation (v1.x)

- [ ] Post-confirm per-interaction debrief breakdown — trigger: core loop validated; spec's score display already ships, this enriches it
- [ ] Water-bridge interaction — trigger: educator demand + demo data gains explicit waters
- [ ] π-stacking split into face-to-face (parallel) vs edge-to-face (T-shaped) as separate teachable types — trigger: all three reference tools distinguish them internally
- [ ] More demo sets / user-set validation helper — trigger: adoption beyond the initial ~9 slots

### Future Consideration (v2+)

- [ ] VMD port — PROJECT.md: PyMOL first; keep core viewer-agnostic where cheap
- [ ] Protein–protein or DNA/RNA-ligand game modes — different grid/physics model entirely
- [ ] Localized UI (Foldit ships translations; meaningful only with a user base)

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Detection engine (7 interactions, verified criteria) | HIGH | HIGH | P1 |
| Game generation + always-solvable grids | HIGH | HIGH | P1 |
| Select/move/rotate + Confirm + scoring loop | HIGH | HIGH | P1 |
| Setup window (params + 7 buttons) | HIGH | MEDIUM | P1 |
| Demo sets + citations workflow | HIGH | MEDIUM (process) | P1 |
| Setup save/load + export/import + checkpoint | MEDIUM–HIGH | MEDIUM | P1 |
| Hint / Skip / Give up | MEDIUM–HIGH | MEDIUM / LOW | P1 |
| Countdown, timer, info box, win screen | MEDIUM | LOW | P1 |
| Help + tooltips | MEDIUM | LOW | P1 |
| Post-confirm interaction debrief | HIGH | MEDIUM | P2 |
| Water bridges | MEDIUM | HIGH | P3 |
| π-stacking subtype split | MEDIUM | MEDIUM | P3 |
| VMD port | MEDIUM (new audience) | HIGH | P3 |

**Priority key:** P1 = must have for launch; P2 = should have, add when possible; P3 = nice to have, future.

## Competitor Feature Analysis

Reference tools verified against official documentation on 2026-09-05. **All numeric threshold values are deliberately omitted** (see policy at top).

| Feature | PLIP | ProLIF | BINANA | bioCHEMeleon (prior art) | AA-match plan |
|---------|------|--------|--------|--------------------------|---------------|
| Purpose | Protein-ligand interaction profiler (web + CLI) | Interaction fingerprints for MD/docking/structures | Ligand-pose binding analyzer (CLI, Python/JS libs, web app) | Hide-and-seek PyMOL game | Matching/placement game |
| H-bond | Yes (D-H···A distance + donor-angle) | Yes (HBDonor/HBAcceptor, + implicit-H variants) | Yes (donor/acceptor + D-H···A angle; deliberately liberal cutoffs for low-res structures) | — | Yes (v1) |
| Salt bridge / ionic | Yes (charge-center distance; suppresses overlapping H-bonds) | Yes (Anionic+Cationic pair) | Yes (representative charge points; His always considered charged) | — | Yes (v1, ionic folded into salt bridge) |
| π-stacking | Yes (center distance + angular deviation + projected offset) | Yes (PiStacking, split FaceToFace / EdgeToFace) | Yes (parallel + T-stacking; padded ring-disk projection) | — | Yes (v1, single category; subtype split deferred) |
| Cation-π | Yes (charge-center ↔ ring-center distance; extra angle for tertiary amines) | Yes (directional pair: CationPi / PiCation) | Yes (charge point projected onto ring disk) | — | Yes (v1) |
| Hydrophobic contact | Yes (hydrophobic atom = carbon with only C/H neighbors; heavy dedup because counts explode) | Yes (Hydrophobic + separate VdWContact) | Yes (C–C distance tally) | — | Yes (v1; binary per-required-interaction avoids count explosion) |
| Halogen bond | Yes (donor ligand-side only — proteins assumed halogen-free; O/N/S acceptors; distance + 2 angles ± deviation) | Yes (XBDonor/XBAcceptor) | Yes (O/N/S/C–X donors; O/N/S acceptors; donor-halogen-acceptor angle) | — | Yes (v1); needs halogenated demo ligands |
| Metal coordination | Yes (>50 metal species; distance + best-fit against ideal coordination geometries) | Yes (MetalDonor/MetalAcceptor) | Yes (distance-only, explicitly no angle check, with documented rationale) | — | Yes (v1, conditional on metal in ligand); distance-based precedent exists |
| Water bridge | Yes (six-parameter geometry) | Yes (BridgedInteraction base class) | — | — | No (v1) — deferred |
| Aromaticity detection | Ring perception + planarity criterion (OpenBabel) | RDKit-based | Planarity via dihedral-deviation criterion; Phe/Tyr/His one ring, Trp two | — | In-house (numpy); definitions phase fixes ring identification |
| Atom/charge typing source | OpenBabel + curated charged-group lists (protein: Arg/His/Lys +, Asp/Glu −; ligand: quaternary ammonium, sulfonium, guanidine; phosphate, sulfonate, carboxylate −) | RDKit smart patterns | AutoDock atom types + Gasteiger charges + name-based protein rules | — | In-house residue/atom tables — part of the human-verified definitions |
| Protonation stance | Adds polar hydrogens, strips alt-confs | Standardizer pipeline (bond orders from template) | Recommends PDBQT (polar H + charges); warns results degrade without H | — | Spec requires specific protonation state + correct valence — validated by all three tools' practice |
| Thresholds published? | Yes — full table on official help page | Yes — docs (per-class params) | Yes — full parameter table in INTERACTIONS.md | — | Adopt one consistent in-house table; the tools' published defaults **disagree** for several types, so per-type adoption must be human-approved |
| Solvability guarantee | N/A | N/A | N/A | N/A | Yes — by construction (differentiator) |
| Game features (score/timer/hints/persistence) | N/A | N/A | N/A | Timer, hint/reveal counters, import/export, checkpoint, win stats, debrief | Superset of prior art's proven set, adapted to placement gameplay |
| Network | Web service (online) | Offline lib | Offline lib (+ web app) | Fetch mode (online) + bundled demos | **Offline only** — pre-downloaded demos + upload |
| Runtime deps | OpenBabel stack | RDKit + MDAnalysis | Self-contained (Python/JS), Apache-2.0 | pymol.Qt + numpy only | pymol-shipped only (PyQt5, numpy) |
| Output | Tables, XML, PyMOL session with interactions grouped by type | IFP tables, plots | Reports + counts | PyMOL session mutations + sidecar JSON | Score feedback in-UI; PyMOL session changes ARE the game board |

Educational-game context (Foldit, verified against its live homepage 2026-09-05): puzzles with progression, leaderboards (soloist/group), recipes (user scripting), community forums/groups, "For Educators" resources, translations. Leaderboards/community/scripting are anti-features here (offline plugin, scope). Transferable, verified Foldit lessons for the genre: puzzle progression tiers and educator-facing resources matter — both already in the plan (difficulty tiers; citations doc; help panel). Deeper Foldit mechanics (tutorial levels, in-game score broadcasts) come from general knowledge — **SPECULATIVE, unverified here**, but consistent with the prior art's proven tooltip/help patterns.

## Sources

Official documentation fetched 2026-09-05 (HIGH confidence for interaction lists, concepts, and parameter *shapes*):

- PLIP web tool Help ("Detectable interactions" + threshold table): https://plip-tool.biotec.tu-dresden.de/plip-web/plip/help#section-interactions — interaction list, two-step rule-based algorithm, group definitions, dedup rules, metal coordination-geometry fitting, published threshold table (values not transcribed per project policy). PLIP 2025 citation shown on site: Schake, Bolz et al., Nucleic Acids Research, https://doi.org/10.1093/nar/gkaf361
- ProLIF official docs: https://prolif.readthedocs.io/en/latest/ — interaction class list (HBDonor/HBAcceptor, Hydrophobic, VdWContact, PiStacking/FaceToFace/EdgeToFace, CationPi/PiCation, Anionic/Cationic, XBDonor/XBAcceptor, MetalDonor/MetalAcceptor, WaterBridge), base parameter shapes (Distance, SingleAngle, DoubleAngle), v2.2.1 (2026-07-27), Apache-2.0; paper https://doi.org/10.1186/s13321-021-00548-6
- BINANA: https://github.com/durrantlab/binana (Apache-2.0, BINANA 2.1) and https://raw.githubusercontent.com/durrantlab/binana/main/INTERACTIONS.md — full interaction descriptions, distance-only metal coordination with rationale, protonation note, published parameter table (values not transcribed per project policy). Citation from README: Durrant JD, McCammon JA. J Mol Graph Model. 2011;29(6):888-893. https://doi.org/10.1016/j.jmgm.2011.01.004
- Foldit: https://fold.it/ — live feature surface (puzzles, leaderboards, recipes, community, educators, translations). Deeper mechanics from training data: flagged SPECULATIVE.

Local prior art read directly (HIGH confidence):

- bioCHEMeleon source: `tmp/bioCHEMeleon/biochemeleon/{game,gui_game,gui_setup,generators,persistence,setup_state,demos,registry,backup,mutation,wizard,__init__}.py` — proven feature implementations (setup form + 7 buttons, persistence formats, checkpoint/import/export, hint/reveal, win/debrief dialogs, countdown, help panel, demo manifest with tiers).
- bioCHEMeleon `DATA_SOURCES.md` + `data/demos/SOURCES.md` — proven demo-citation pattern (PDB ID + DOI + license per source; RCSB CC0, MemProtMD CC-BY 4.0, SASBDB attribution; bundled-vs-fetched sourcing).
- bioCHEMeleon `AGENTS.md` — proven gotchas that shape feature feasibility (no undo in PyMOL open-source → snapshot/restore; modeless main dialog; QTimer on main thread; delayed modal after redraw).

Not consulted / not available: `vmd-ref/` (not present in this repo checkout). Numeric threshold **values** from PLIP/BINANA/ProLIF: intentionally excluded; the human-verification phase must transcribe and approve them from the URLs above.

---
*Feature research for: AA-match — educational molecular-interaction matching game (PyMOL plugin)*
*Researched: 2026-09-05*
