---
status: closed
trigger: "Phase-3 human GUI checkpoint (03-06) field failures: PLAY-02 PHE parallel pose no score change; nudge camera-relativity; AA line vs stick rendering; msm=0; CTSH-V key mapping; editor_scheme unknown"
created: 2026-09-10T00:00:00
updated: 2026-09-15T00:00:00
---

## Current Focus

hypothesis: H1 PLAY-02 = COMPOUND: (a) wizard scoped to molecule 0 while BOTH molecules materialize (user may have posed PHE over the wrong/aromatic-less ligand or expects wrong-molecule Confirm); (b) by-eye alignment with view-z-only rotation affordances likely outside the 30deg/2.0A/5.5A window; (c) panel shows ONLY required types so a formed-but-not-required pi_stacking moves no score. H2 PLAY-03 color = HIGHLIGHT_COLOR 'green' vs PyMOL default carbon lightgreen (visual ambiguity) OR real restore failure. H3 msm=0 = by-design during game (defensive set) + user env baseline unknown. H4 nudge = correct-by-construction (get_view re-read per nudge, R^T live-proven); field feel = expectation mismatch.
test: tmp/probe_gui_0306.py headless: default seed-42 game payload dump (which ligand is mol-0, required items), scripted picks + color RGB deltas, explicit-aligned PHE pose detect/sensitivity sweep, nudge invariant under set_view rotations, reps bitmask, msm lifecycle
expecting: numeric verdict per issue
next_action: write + run probe

## Symptoms

expected: (from 03-06 checkpoint) mouse_selection_mode stock 1; PHE posed parallel over aromatic ligand changes Confirm score; nudges camera-relative; AA recolor restore on switch; editor_scheme set/get restorable
actual:
- get mouse_selection_mode -> 0 (mid-game and after)
- button_mode 0 (OK); editor_scheme unknown setting in this build
- "No key mapping for 'CTSH-V'" right after game start
- PLAY-01 OK (click-select, camera drag, empty-space click)
- PLAY-02 CRITICAL: PHE parallel above/below ligand ring never changes Confirm score
- Nudge ~1 A OK but up/down feel inverted after scene rotation
- Working keys: LEFT/RIGHT + comma + period + q/w/e/d (UP/DOWN dead = by design)
- PLAY-03: switching AAs does NOT restore previous AA's original color (aa02..aa16 re-confirmed)
- Reset to Grid works; result clears after reset
- No helper geometry drawn (PLAY-04 half OK)
errors: "No key mapping for 'CTSH-V'"; "Error: unknown Setting: 'editor_scheme'"
reproduction: Plugins -> AA-match, default setup (2 molecules, D3, unset, seed 42)
started: first real-GUI playthrough (headless smokes all green — env difference from GUI path)

## Eliminated

- hypothesis: PLAY-02 = detector bug (pi_stacking fails to fire on good pose)
  evidence: probe run 1 aligned 4.5A pose -> pi=1, d_center=4.5000, angle=0.00deg, offset=0.0000, subtype P; tilt 27deg passes, 31 kills; lateral 1.9 passes, 2.5 kills; vert 5.4 passes, 5.6 kills. Detector + thresholds work exactly as approved.
  timestamp: 2026-09-10
- hypothesis: PLAY-03 = color ambiguity (green highlight vs greenish default carbon)
  evidence: probe B: PHE element colors C=index9 (1.00,0.60,0.60) salmon, H=29 (0.9,0.9,0.9), N=27 (0.2,0.2,1.0), O=28 (1.0,0.3,0.3) vs highlight green (0,1,0); rgb-dist 1.23-1.30 = plainly distinguishable.
  timestamp: 2026-09-10
- hypothesis: PLAY-03 = restore code broken (any build-level path)
  evidence: probe run 1 scripted GUI pick route (select sele + do_select): switch r0c1->r0c2 restored EXACTLY (color maps identical). Headless==same Python/build as GUI.
  timestamp: 2026-09-10
- hypothesis: nudge = stale view or R vs R^T inversion
  evidence: probe run 1: identity/Rz(90)/Rx(137)Rz(90) views -> camera-frame displacement exactly (0,1,0) each time; get_view re-read per press (wizard.py:436).
  timestamp: 2026-09-10

## Evidence

- timestamp: 2026-09-10 (probe run 1, tmp/probe_gui_0306.py)
  checked: default seed-42 payload (gamestart.start_game headless)
  found: mol-0 = benzamide at offset (0,0,0), required = {'mode':'list','items':[{'type':'h_bond','count':1}]}; mol-1 = acetate at offset +30.0 x, required salt_bridge x1. PHE = mol-0 slot r0c1, role=DISTRACTOR, can_form=[]. Panel header = "Required: h_bond x1".
  implication: pi_stacking is NOT a required type for the scored molecule; a fired pi_stacking cannot move the score (game_state._formed_types 'list' mode only counts REQUIRED types). Field observation reproduced exactly with a perfect pose: pi=1 fired, score=0.00.
- timestamp: 2026-09-10 (probe run 1)
  checked: natural ring tilts at grid vs benzamide ring normal
  found: _aam_aa02 (PHE, mol-0 only aromatic slot) = 31.18 deg; mol-1 aromatics 38.17/38.17/79.61 deg. PHE natural tilt is 1.18 deg OUTSIDE the <=30 deg approval threshold.
  implication: even if pi_stacking were required, a pure-translation by-eye pose silently fails; only rotation affordances are view-axis 90deg/10deg steps with zero tilt feedback.
- timestamp: 2026-09-10 (probe run 1 + B)
  checked: msm lifecycle + editor_scheme + CTSH-V source
  found: headless fresh msm=1 -> during game '0' (wizard.py:176 defensive atomic, by design) -> after Done '1'. cmd.get('editor_scheme') raises "Error: unknown Setting" (matches field); cmd.get_editor_scheme()=1 (API fn). "No key mapping" = pymol/internal.py:436 _invoke_key fallthrough; CTSH = ctrl+shift (modifier_keys[3]) -> a Ctrl+Shift+V press with no set_key mapping; zero hits in aamatch/.
  implication: msm=0 mid-game expected; after must equal pre-game baseline (if still 0 after Done, baseline was 0 -> user env). editor_scheme was never a setting; 03-06 plan wording wrong; nothing to restore in 03-07 (scheme law, no drags in game).
- timestamp: 2026-09-10 (probe run 1)
  checked: reps bitmask per game object + bit decode (probe B, empirical on this build)
  found: group A (ILE,PHE,LEU,ASN,THR,ALA,TRP,VAL,TYR) bits=49 = sticks(1)+nb_spheres(16)+cartoon(32); group B (GLU,ASP,ARG x2,LYS x3 = exactly the CHARGED fragments) bits=2176 = lines(128)+nonbonded(2048).
  implication: "some AA in line, some stick" = PyMOL new-object display heuristic splits charged vs neutral chempy fragments (charged -> ligand-like lines+nonbonded; neutral -> peptide-like sticks+cartoon). Cosmetic; detector never reads reps; homogenize at materialize.
- timestamp: 2026-09-10 (probe run 1)
  checked: mol-1 pick behavior (field: "clicking the AA near another ligand not changing anything")
  found: scripted pick on mol-1 slot object: _current_slot unchanged, no recolor, no restore -> exact field reproduction; by design (build_slot_map scopes to molecule 0).
  implication: field PLAY-03 "not restored" re-confirmations included mol-1 objects (aa14, aa16 = mol-1) -> no-op clicks leave the previous green selection in place; perceived as "switch doesn't restore".
- timestamp: 2026-09-10 (code read)
  checked: game_state.score / engine.confirm scoping
  found: score consumes ONLY r['type'] over ALL detected records across ALL ligands/objects; engine.confirm passes the full records list against molecule-0 required.
  implication: latent cross-molecule scoring leak (a required-type record formed over the WRONG ligand would count as formed). Benign in this field case but a real multi-molecule design gap.

## Resolution

root_cause: PLAY-02 = DESIGN compound: (1) seed-42 mol-0 requires h_bond x1, not pi_stacking — a fired pi_stacking legitimately never moves the score (proven with a perfect pose: pi=1, score=0.00); (2) natural PHE tilt 31.18deg > 30deg threshold makes pure by-eye poses fail even when required; (3) mol-1 (acetate, no aromatic ring, click no-op grid) confuses targeting. PLAY-03 = explained-by-design for mol-1 part + pending human re-test for strict mol-0 part (headless restore is exact). nudge = correct. msm = by-design during game; after must equal baseline. CTSH-V = harmless PyMOL keymap noise. editor_scheme = never a setting in this build (API fn exists).
fix: see prioritized fix list in final report (no code changes made — diagnose-only)
verification: headless probes tmp/probe_gui_0306.py + tmp/probe_gui_0306b.py (outputs in agent log)
files_changed: []

## Human confirmations (2026-09-10, checkpoint session 2)

- PHE was posed over **benzamide** (the ring ligand, correct target); panel showed `Required: h_bond` — CONFIRMS root cause (1): pi_stacking not required on this level, so the score could never move. The 03-06 plan's step-9 wording ("pose ring AA, expect change") was written generically and is invalid for an unset-random level that drew h_bond — checklist defect, replaced by the H-bond scoring test.
- `No key mapping for 'CTSH-V'`: human confirms an accidental Shift press while pasting — explained, ignorable, no action.
- Still pending from human: msm baseline pre-game + post-Done; H-bond scoring test (SER/ASN near benzamide -> 1.00, then away -> drop); strict mol-0 color re-test (aa02->aa03->aa04).
- msm baseline CONFIRMED (2026-09-10, fresh session): pre-game = 1 (stock), during game = 0 (by design), after Done = 1 (restored). Wizard msm save/restore field-verified; the earlier msm=0 readings were mid-game (design), not a .pymolrc baseline issue. Verdict 4 CLOSED.

## Human 03-07 verdicts (2026-09-15, checkpoint session; PLAY-04 [HUMAN+GATE] closure)

- **Start framing: APPROVED** after the gamestart saga (commits 1d48d71 -> 0c13184 -> d8e8f7d -> 0041e74 -> 2a182d7). Final form: ligand in front of the active grid (geometry-side offset), active-molecule-only start view, zoom-last framing. Laws recorded: zoom-last; camera-field-surgery-avoided (the scene re-frame after composition fixes the blank start-view regression without touching camera near/far planes by hand).
- **Step 1 / A (no helper visuals): PASS** — green recolors + panel/prompt text only, at no point any lines/dots/CGO/distance monitors/selection crosses.
- **Step 1 / B (restoration on Done): PASS** — full restoration table field-verified: prior `wizard measurement` auto-resumes after the game's Done (stack-native push/pop); msm baseline 1 (pre-game, by design 0 during, 1 post-Done); no pk1/sele/_drag leftovers; every recolored AA back to its original color; `_aam_*` game objects still present (Cleanup is Phase 4).
- **Step 2 (interactive drag path): COMPLETE — MATRIX PATH PROVEN.**
  - `drag _aam_aa06` echoed `Dragging whole object "_aam_aa06".` (the whole-object native drag = object-matrix path, NOT the coordinate path).
  - Real-mouse left-drag ROTATED the object (3-Button Viewing: left-drag = rotate; whether ctrl-left = standard translate unconfirmed by the human).
  - Checker snippet (`run tmp/check_drag.py`) RUN 2: `_aam_aa06 IDENTITY-OK False` with a GENUINE ROTATION matrix on `get_object_matrix` ([0.685537, -0.503814, -0.525557, 7.300527, ...]) — the native whole-object drag WRITES an object matrix (proven).
  - Run 1 earlier showed ALL IDENTITY (first drag session without an effective matrix write — noted, non-conclusive).
  - Extra console noise: `parser: no matching files.` before the drag = human typo, ignorable; clicks during drag sessions echoed normally.
- **Steps 3 & 4 (forced coordinate-path drag via populated `_drag`; transform_object render-doubling): SKIPPED by explicit human decision** — "does user need drag for gameplay? no" / movement already decided / "then dont need step 3 & 4". Rationale: low marginal value; the headless stack already covers the game-path movement model (SMOKE-07 78 checks, SMOKE-08 31 checks).
- **CTSH-V:** remains explained/ignorable (accidental Ctrl+Shift paste, no aamatch keymapping involvement).

## 03-07 probe result (2026-09-15, tmp/probe_0307_matrix_visibility.py, headless PyMOL 2.5.0)

Question: can the game's geometry/detector pipeline SEE a matrix-moved pose (native-drag-style object-matrix write via `cmd.transform_object(name, [R|t], homogenous=1)`)?

- Game built via the standard engine seam (`engine.new_game(dict(setup_state.DEFAULTS), 42)` + `materialize`, SMOKE-04 way); ligand `_aam_lig01`, control `_aam_aa01`, matrix object `_aam_aa02`.
- CONTROL (the game's own `cmd.translate([8,0,0], obj, state=1, camera=0)`): detector-view centroid shift EXACTLY (8.0000, 0.0000, 0.0000), dev 0.000000; distance-to-ligand 14.2975 -> 11.8499 A. Pipeline sanity PASS.
- MATRIX (`transform_object` with Rz(37deg) + translation (5,6,7), `homogenous=1`):
  - iterate_state x/y/z read-back: MATRIX-APPLIED (baked coordinates) — dev_vs_raw=11.117828 A, dev_vs_applied=0.000001 A (float32-level).
  - extract_game_atoms (the detector's actual input): pose matches the expected R.pose+t EXACTLY (det dev_vs_applied=0.000000; dev_vs_raw=14.546633 A); distance-to-ligand 11.8499 -> 18.5183 A.
  - Object-matrix history record non-identity (m[0..7]=[0.798635, -0.601815, 0.0, 5.0, 0.601815, 0.798635, 0.0, 6.0] = the Rz(37) block + translation, exactly as written).
  - `engine.detect()` over the matrix-moved scene: runs fine (0 records formed at the moved pose — none expected).
  - Scene restored with zero leaks.
- **VERDICT: MATRIX PATH VISIBLE** — native-drag-style object-matrix moves BAKE coordinates (`transform_object(homogenous=1)`), so the dragged pose lands in the detector pipeline input. Native drag is detector-compatible: SAFE, nothing to guard. The pre-planned Phase 5/6 guard candidates (pre-Confirm matrix sweep -> auto-bake / refuse-with-message) are NOT opened.

## 03-07 human decisions recorded (2026-09-15)

- Native drag NOT needed for gameplay (FROZEN): game movement = panel buttons + keyboard, baked world-frame coordinates (the 03-03 movement model). Native whole-object drag = matrix path (proven), detector-visible (probe) — acknowledged, deliberately not a gameplay input.
- Nudge left/right is SCREEN-RELATIVE BY DESIGN (keys move in the player's current view direction); help text for Phase 5/9 must SAY so explicitly ("keys move in your current view direction").
- Detector-visibility guard for native drag: NOT a gap (probe verdict VISIBLE); no Phase 5/6 guard candidate opened.
