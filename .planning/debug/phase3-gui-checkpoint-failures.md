---
status: investigating
trigger: "Phase-3 human GUI checkpoint (03-06) field failures: PLAY-02 PHE parallel pose no score change; nudge camera-relativity; AA line vs stick rendering; msm=0; CTSH-V key mapping; editor_scheme unknown"
created: 2026-09-10T00:00:00
updated: 2026-09-10T00:00:00
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
