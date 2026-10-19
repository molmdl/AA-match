---
status: closed — superseded by the 2026-10-18 human design decision (movement input-model pivot: mouse-drag replaces directional keys/buttons; panel keeps Toward only)
trigger: "08.2-10 GUI mouse-rotation movement discrepancy — pickup of existing DEBUG HANDOFF (.planning/phases/08.2-direction-control-restoration/08.2-10-DEBUG-HANDOFF.md)"
created: 2026-10-12T00:00:00Z
updated: 2026-10-18T05:00:00Z
---

# nudge-direction-mouse-rotation (pickup of 08.2-10 DEBUG HANDOFF)

This session is a PICKUP. Bidirectional links:
- Handoff (source of truth for entry state): .planning/phases/08.2-direction-control-restoration/08.2-10-DEBUG-HANDOFF.md
- Prior lineage session: .planning/debug/nudge-direction-reopen.md (post-Phase-6 re-open; findings fed Phase 8.2; do NOT redo its work)
- Step-4 of plan 08.2-10 is UNRESOLVED; nothing may be approved over it.

## Current Focus

hypothesis: (user-approved purge applied 2026-10-18 — from the resumed round only the decode + d4 receipts + the USER RULING entry survive; the path/launch direction is ruled irrelevant and purged.) The repo law is exact monitor-LEFT and now PROVEN LIVE: d4 ran the current repo code in the REAL Windows GUI at the USER'S EXACT (c2) rotation block, through the user's own panel-Left button string AND the keyboard channel — screen=(-0.999996, ~0, ~0), dev_VIEWREL=2.13e-07, ALL rows PASS, no wizard errors (IDENT + Ry180 controls consistent; at Ry180, world-absolute would be exact RIGHT — refuted). Decode: the 10-12 "goes down" row (and the earlier 180-deg / "absolute coordinates" rows) uniquely fingerprints WORLD-ABSOLUTE movement — behavior d4 could NOT reproduce on current code at the exact printed orientation. Remaining explanations are session-side only, by prior: (i) an extra rotation between the final console paste and the Down press (the presses left NO view receipts — camera state at press time is UNAUDITED); (ii) board-frame wording (at c2, monitor-left = out of the grid plane toward the ligand — can read as "down [the board]" from that below-ish view); (iii) a zero-trace transient in that single session.
test: ASK-DON'T-GUESS (BINDING, see USER RULING entry): (A) two direct questions: (1) "did you rotate/drag the scene AT ALL between your last console paste and the panel-Left press that went down?" (2) "when you said it went down — toward the MONITOR's bottom edge, or down along/into the BOARD (grid) as you saw it on screen?" (B) optional final receipt play: user rotates however they like, prints get_view BEFORE and AFTER one panel-Left press, reports which monitor edge the AA slid toward. (C) accept receipts and adjudicate: the law is machine-proven AND live-GUI-proven (d4); step-4 verdict per the user's gate decision with the 10-12 row's disposition recorded.
expecting: (A1) "yes, rotated more" → the 10-12 row is explained (the press ran at a beyond-c2 state whose world-absolute fingerprint matches "down"); (A2) "down the board" → perceptual/wording, requirement already met, UX note only; (B) monitor-LEFT + equal pre/post prints → user-verified live confirmation on current code; any other (B) outcome → capture the numbers and STOP per Rule 4 → /gsd-plan-phase.
next_action: ORCHESTRATOR (fresh session — the user starts a new one): open with the receipt pack + options A/B/C and WAIT. Resolution section + handoff §9 routing once the user picks; nothing is approved over the 10-12 row until its disposition is recorded.

## Symptoms

expected: "anything the user need is, no matter how much it rotate, left go to left on monitor x, right go to right on monitor x" (human verbatim) — pressing Left must move the AA toward monitor-left in the CURRENT view, at ANY camera orientation.

actual: Human GUI session 2026-10-11, verbatim: "1-3 pass, 4 if i rotate 180 degree and press left, it goes right"; "8 pass, 9 chk above". Second GUI test, same session: "start: left is left, right is right" / "command type `rotate {x/y/z}, 90` (not mouse roate): correct left is left, right is right" / "rotate by mouse: left is the old direction, right is the old direction". Earlier: "THIS IS NOT WHAT U SHIPPED! OUR LAST TEST: START GAME LEFT=LEFT, AFTER ROTATING THE CAMERA ITS STILL THE SAME DIRECTION, NOT STRAIGHT LEFT!!!!!!!". Scene layout (their words): "ligand closer to the viewer, AA grid behind the ligand more away from viewer". Module identity CONFIRMED live repo copy (`print(type(cmd.get_wizard()).__module__)` → aamatch; "the exact one in this repo").

errors: NONE from AA-match. Step-9 console sweep: PASS (standard AA-match lines only; third-party plugin init noise is pre-existing Windows-env stock).

reproduction: GUI ONLY, user's Windows PyMOL 2.5.0 (Win conda env, OpenGL 4.6, Intel Iris): start a game, rotate scene by MOUSE DRAG (mouse-mode name UNKNOWN — missing receipt #1), then press a nudge input (panel vs keyboard per row unknown — missing receipt #3b). NOT reproducible headlessly via set_view — that is the core contradiction to machine counter-evidence.

started: First surfaced at 08.2-10 step-4 GUI playtest 2026-10-11 (movement model built Phase 3, frozen 03-07 "screen-relative BY DESIGN"; reopened 2026-09-21 → Phase 8.2 rebuild landed 2026-10-11, waves 1-3 green: WSL 960/960, smokes 01-23 pass).

timeline: 03-02/03-01 model → 03-07 freeze → 2026-09-21 reopen (nudge-direction-reopen.md) → Phase 8.2 waves 1-3 landed 2026-10-11 → first GUI playtest 2026-10-11 surfaced step-4 discrepancy → handoff written, this session is the pickup 2026-10-12.

## Machine counter-evidence that MUST be reconciled (from handoff §5)

- P1 probe (tmp/probe_082_p1_nudge_so3.py + tmp/probe_082_p1_output.log): 30/30 real-wizard presses across 5 views incl. full-SO(3); max screen-direction deviation 0.0000 deg; max convention deviation 2.51e-07 A. TO BE RE-READ FROM DISK.
- Step-4 diagnosis probe (tmp/probe_082_step4_diagnosis.py + tmp/probe_082_step4_output.log): real gamestart + scripted pick, views via set_view, Left via REAL panel-button code string AND wiz.do_special(100); world delta flipped per orientation while screen_dx = -1.000000 (monitor-LEFT) at EVERY orientation; dev ≤ 7.53e-08; verdict "STEP4-DIAGNOSIS H1-CONFIRMED". TO BE RE-READ FROM DISK.
- SMOKE-07 (wizard loop) + SMOKE-23 (direction battery) pin per-press live-tracking; green on merged tree.

## Eliminated

- hypothesis: H-A "console rotate proves tracking" — user's `rotate x, 90` row was a same-camera non-test.
  evidence: pymol-src/modules/pymol/editing.py:1716 `def rotate(...)` rotates ATOMIC COORDINATES of the selection (default all) — camera=1 merely means the AXIS is in camera coordinates; the view matrix is never touched. (Source receipt recorded in handoff §4.)
  timestamp: 2026-10-11 (pre-pickup; re-verified this session — see Evidence)

- hypothesis: H-C mechanism (narrow form) — "the view matrix read by the wizard at press time diverges from the renderer's live camera in the GUI-mouse context on stock PyMOL 2.5.0".
  evidence: SOURCE-REFUTED 2026-10-12. There is exactly ONE camera matrix in the process, G->Scene->m_view.m_rotMatrix: mouse orbit writes it synchronously in the motion event (SceneMouse.cpp:1886-1888 -> SceneRotate Scene.cpp:5240-5256), the render pipeline composes it (SceneGetModel2WorldMatrix Scene.cpp:4830-4839), and cmd.get_view reads it (viewing.py:660-661 -> PyMOL_CmdGetView PyMOL.cpp:743-761 -> SceneGetView Scene.cpp:898-920, explicitly reading m_rotMatrix at Scene.cpp:919-920). No defer/commit separation, no stereo rotation divergence, no wizard drag channel (Wizard.h:21-26,47-53), matrix_mode does not touch SceneRotate. A GUI-vs-headless divergence of get_view semantics is impossible on the same binaries (probes ran the same 2.5.0 build). RESIDUAL: non-stock interference (third-party plugin, custom cmd.button overrides, second instance) remains conceivable — receipts decide; if (c) != (a) AND panel-Left moves NOT-monitor-left, instrument per handoff §6 then STOP per Rule 4.
  timestamp: 2026-10-12

## Evidence

- timestamp: 2026-10-12 (session start)
  checked: git tree state + probe artifacts on disk
  found: main @ aae913c (handoff 1d0b000 + "chore: track oc stats"); only M opencode.json + this new debug file uncommitted; no worktrees; PATH symlink maps /home/lwng -> /mnt/c form. tmp/ contains probe_082_p1_nudge_so3.py + probe_082_p1_output.log + probe_082_step4_diagnosis.py + probe_082_step4_output.log (+ P2/P3 wave probes). pymol-src = full PyMOL checkout incl. C layers layer0..layer5 + modules/.
  implication: handoff entry state confirmed; probe artifacts available for re-reading (not just handoff claims).

- timestamp: 2026-10-12
  checked: tmp/probe_082_step4_output.log (full read)
  found: S4D-ENV pymol 2.5.0 python 3.9.13; real game start seed 42; script picked _aam_aa01 (r0c0); panel-Left verbatim code 'cmd.get_wizard().nudge_cam(-1, 0, 0)'. IDENT-fresh-start: world_delta=(-1,0,0) screen_dx=-1.000000. RY180-vertical-orbit: world_delta=(+1,0,0) screen_dx=-1.000000. RZ180-flipped: world_delta=(+1,0,0) screen_dx=-1.000000. SUMMARY presses=7 max screen_dir_angle=0.0000 deg max conv dev=7.53e-08 identity-clean=all errors=none; verdict line 59: "=== STEP4-DIAGNOSIS H1-CONFIRMED ... the viewer-relative law (P1/SMOKE-07/23) is INTACT ===".
  implication: via set_view-scripted orientations, the REAL panel-button code path + do_special(100) track the live view per press; screen_dx is monitor-LEFT at every orientation. Scripted-camera path is machine-perfect.

- timestamp: 2026-10-12
  checked: tmp/probe_082_p1_output.log (full read)
  found: 30/30 real-wizard presses across 5 views (S0 identity, S1 yaw Rz90, S2 ACTUAL post-start view, S3 full-SO3 Rx30Ry50Rz20, S4 rolled Rz200Rx25): max_press_screen_dir_angle=0.0000 deg, max_conv_dev=2.51e-07, identity clean. S2-ACTUAL-poststart start view rotation block: -0.447214 0.894427 0 -0.894427 -0.447214 -0 0 0 1 (a ~63.4-deg world-Z roll of the camera at game start — the start-composition roll). P1-VERDICT DISORIENTATION (screen axes vs world axes): worst 90.0 deg; per view S0:0.0 S1:90.0 S2:90.0 S3:46.9 S4:71.9.
  implication: headless machine evidence is perfect; ALSO quantifies the judging-frame hazard: after a large camera rotation, screen axes diverge from world/grid axes by up to 90 deg — a user judging "left" against the ROTATED BOARD would see the AA move "not board-left" even though it moved exactly monitor-left.

- timestamp: 2026-10-12
  checked: .planning/research/PITFALLS.md (Pitfalls 5, 6, 12) + 08.2-RESEARCH-code.md (full)
  found: Pitfall 5: default 3-Button Viewing left-click = cButModeSeleSet -> "sele" + WizardDoSelect; Picking modes = pk1 + WizardDoPick (C refs SceneMouse.cpp:337-356 vs 403-467 recorded from prior art). Pitfall 6: cmd.drag installs Dragging wizard (editing.py:1067-1074), dragging.py editor_scheme==3 self-destruct gate (wizard/dragging.py:49-54), matrix-vs-coordinate duality (dragging.py:33-35,98-101). 08.2-RESEARCH-code.md: full control-surface inventory — movement funnels through nudge_cam/rotate_axis/step_to_ligand -> _guard -> _require_playing -> _current_object -> wizard_core.view_camera_to_world(cmd.get_view(), step) (R^T; wizard.py:682-683 fresh read per press) -> cmd.translate(state=1, camera=0) bake -> _assert_identity. Keyboard do_special LEFT=100/RIGHT=102 only; Qt Game tab has ZERO movement buttons. Qt keyboard routing into tab is untested/unknown.
  implication: the repo-side movement path reads live get_view() per press and is machine-proven; remaining unknowns are entirely in the GUI/mouse/C-layer domain (Q1/Q2/Q3) and the user's exact input surface (missing receipts).

- timestamp: 2026-10-12 (source walk — Q1/Q2/Q3, all reads from pymol-src = full PyMOL 2.5.0 checkout: layer0..layer5 + modules; symlink ./pymol-src -> ../bioCHEMeleon/tmp/pymol-src)
  checked: Q1 — does a plain mouse orbit update the matrix cmd.get_view() returns, immediately, in the GUI?
  found: FULL COMMIT PATH (no defer): (1) mode profiles modules/pymol/controlling.py:320-321 ('three_button_viewing': ('l','none','rota')) and :349-350 ('three_button_editing': ('l','none','rota')) — plain left-drag = 'rota' in BOTH; but_act_code 'rota'->0 (controlling.py:58) = cButModeRotXYZ (ButMode.h:25). (2) SceneDrag dispatches via ButModeTranslate (SceneMouse.cpp:1320); case cButModeRotXYZ: SceneMouse.cpp:1886-1888 -> SceneRotate(G, theta, axis[0], axis[1], -axis[2]). (3) SceneRotate (Scene.cpp:5240-5256) writes DIRECTLY into I->m_view.m_rotMatrix (Scene.cpp:5249-5251: temp = rot(delta)*m_rotMatrix; copy back) + SceneUpdateInvMatrix. (4) cmd.get_view() (viewing.py:605,660-661: `_cmd.get_view` under lockcm) -> PyMOL_CmdGetView (PyMOL.cpp:743-761: SceneGetView + repack [0:3]+[4:7]+[8:11]+[16:25]) -> SceneGetView (Scene.cpp:898-920) reads THE SAME I->m_view.m_rotMatrix (Scene.cpp:919-920). Render side composes the same matrix via SceneGetModel2WorldMatrix (Scene.cpp:4830-4839, MatrixMultiplyC44f(I->m_view.m_rotMatrix, matrix)). ONE struct, ONE process, synchronous event-handler write — GUI and headless identical by construction.
  implication: Q1 = YES, immediate. There is no mechanism by which a real orbit could leave get_view stale inside the same process. The rotation block the wizard reads IS the camera the renderer draws with.

- timestamp: 2026-10-12 (source walk, cont.)
  checked: Q2 — which mouse modes / gestures rotate CONTENT (objects) instead of the camera on drag?
  found: MODE->GESTURE TABLE (stock 2.5.0, controlling.py mode_dict): every stock profile ('three_button_viewing' :320, 'three_button_editing' :349, 'three_button_motions' :378, 'three_button_maestro' :291 (L='box', M='rota'), 'three_button_lights' :235, 'two_button_viewing' :408, 'two_button_selecting' :436, 'two_button_editing' :464, 'one_button_viewing' :492, 'default' :535) assigns PLAIN left-drag ('l','none') = 'rota' = camera orbit (or 'box' in maestro). CONTENT-rotating gestures exist ONLY under modifiers/special gestures: 3-Button Editing: ('l','shft','roto')= RotObj (rotate the PICKED OBJECT), ('l','ctrl','torf')= torsion fragment (bakes coordinates), ('l','ctsh','mova')= move atom (bakes coordinates), ('double_middle','none','drgm')= drag molecule; 3-Button Motions: ('l','shft','rotv')= RotView (object TTT for movie views); 2-Button Editing: ('l','ctsh','rotf'). C-side gates: ALL editor-family drag gestures (case cButModeRotObj..cButModePkTorBnd, SceneMouse.cpp:1511-1523) fire ONLY when the drag started on a picked atom (obj = I->LastPicked.context.object, SceneMouse.cpp:1524) and transform ONE object at a time; EditorDrag (Editor.cpp:2136+) applies them as: matrix_mode==1 -> ObjectCombineTTT (Editor.cpp:2228), ==2 -> per-state matrix (:2232-2233), else -> ObjectMoleculeTransformSelection bakes coordinates into the fragment/selection (Editor.cpp:2237-2240). Single-clicks (no drag): viewing mode single_left='+/-' (sele toggle -> WizardDoSelect), editing mode single_left='pkat' (pk1 -> WizardDoPick) (controlling.py:343,372; SceneMouse.cpp:356,426). EditorConfigMouse (Editor.cpp:153-199) re-maps ONLY SHIFT-gestures per editor scheme (obj/frag/drag) in editing/motions modes — plain drag untouched.
  implication: a PLAIN unmodified left-drag NEVER rotates scene content in ANY stock mode. A whole-scene "rotation" via content is not reachable by plain drag; object gestures rotate one picked object and require modifier+drag-start-on-atom. If the user's (c) shows get_view UNCHANGED while the display rotated, their gesture was content-side (H-B-content) — e.g. shift-left 'roto' — OR a non-stock/custom mouse profile; either way monitor-left movement remained CORRECT for a camera that never moved.

- timestamp: 2026-10-12 (source walk, cont.)
  checked: Q3 — any state where get_view diverges from the displayed camera?
  found: NO in-process divergence state for the rotation block in stock 2.5.0: get_view reads the same m_rotMatrix the renderer composes (receipts above). Stereo modes only offset eye positions at render (get_stereo_x adjusts input x in SceneMouse; display still centered on the same view). The openvr build (_PYMOL_OPENVR, Scene.cpp:909-917) adds position-only offsets (dY/dZ) to the TAIL fields, not the rotation block — not the user's config (no OpenVR). matrix_mode setting (default <auto>) affects only how OBJECT/selection transforms are applied (editing.py:2014 edit-mode doc; editing.py:2143 matrix_reset mode -1 = "matrix_mode or 0"; Editor.cpp:2164-2171 reads it from the DRAG OBJECT's settings) — SceneRotate never consults it, so the plain 'rota' orbit always writes the camera matrix. Wizard channels: Wizard.h:21-26,47-53 — C delivers ONLY DoPick/DoSelect/DoKey/DoSpecial to wizards; there is NO drag/XY wizard channel, so the game wizard cannot intercept or divert drags. The only remaining divergence sources are NON-stock: third-party plugins (user's env loads findseq/cb_colors/wfmesh/bnitools/mtssl*/SuperSym — all error at init), custom `cmd.button` gesture overrides, or a second PyMOL instance (ruled out: module identity confirmed single repo copy).
  implication: H-C's mechanism (wizard's get_view diverging from the renderer's live camera in the GUI-mouse context) has NO realization path in stock 2.5.0 source. If receipts ever showed (c)!= (a) AND movement still not-monitor-left, that would be non-stock interference — the instrumentation-then-STOP branch.

- timestamp: 2026-10-12 (source walk, cont. — judging-frame math for the 180-degree case)
  checked: what the user's "goes right" could mean if the camera truly orbited 180 deg AND movement tracked monitor-left (P1/step-4-probe semantics).
  found: after a 180-deg camera orbit, the BOARD is mirrored on-screen: the board edge that was at monitor-right now appears at monitor-left. Pressing Left moves the AA monitor-left (machine-proven semantics; screen displacement = R * R^T * step = step) — i.e. toward the board edge that was previously the board's RIGHT side. A user judging "which side of the BOARD did it move toward" would report "it went [board-]right — the OLD direction". The P1 probe's DISORIENTATION metric quantifies this: screen-vs-world axis misalignment is up to 90 deg at yaw/rolled views (tmp/probe_082_p1_output.log:58), so board-relative judgments flip sign at 180-deg rotations while monitor-relative movement stays correct. Their two verbatim rows are BOTH consistent with this: "if i rotate 180 degree and press left, it goes right" (board-frame) and "left is the old direction" (world/board frame — after camera-180, Left = world +X = the old Right's world direction, exactly as the step-4 diagnosis probe logged for Ry180/Rz180: world_delta=(+1,0,0) while screen_dx=-1.000000, tmp/probe_082_step4_output.log:30,48).
  implication: if receipts land on the camera-orbit branch with panel-Left monitor-left, the verdict is H-B-perceptual — the movement law satisfies the user's own stated requirement ("left go to left on monitor x"); the fix is UX (help text / orientation cue in Phase-9 scope), not movement code. NOTE this converges EXACTLY with the prior-session analysis (.planning/debug/nudge-direction-reopen.md "Prime suspect": screen-relative movement FEELS wrong when judged against the grid/board after rotations — no code bug required).

- timestamp: 2026-10-12 (repo-side receipts, first-hand re-verified)
  checked: aamatch/wizard.py:668-688 (_nudge_cam_impl), :620 (_assert_identity), aamatch/wizard_text.py:41 (_MOVEMENT_BUTTONS), aamatch step-4 probe drives both panel-code and do_special paths (tmp/probe_082_step4_output.log)
  found: nudge order is _require_playing -> _current_object -> view_camera_to_world(cmd.get_view(), step) (wizard.py:682, LIVE per press) -> cmd.translate([step*w], obj, state=1, camera=0) (wizard.py:685-686) -> _assert_identity(obj) (wizard.py:687 — AFTER the move; under an object-matrix drag the AA still MOVES then the ERROR line appears on the panel, panel-only, NOT echoed to console).
  implication: (a) fresh get_view per press is real; (b) the console sweep (step 9) would NOT show panel ERROR lines — absence of console errors does not rule out object-matrix interference, but the receipt-3 panel-Left test + any ERROR line will; (c) the panel test after (c) is a complete discriminator in one press.

- timestamp: 2026-10-12 (CHECKPOINT RESPONSE RECEIPTS — orchestrator-held verbatim record; user PAUSED the session before continuation spawn: "pause after u summarize before u spawn, bak later")
  session_launch: interactive GUI (no -cq script) run from WSL: cmd.exe /c "set SRP_DEBUG=1&& C:\src\run-conda-pymol.bat". Banner: PyMOL 2.5.0, OpenGL 4.6 / GLSL 4.60, Intel(R) Iris(R) Plus Graphics, GL 4.6.0 Build 31.0.101.2130, 8 CPU cores. Third-party plugin init noise present = pre-existing stock (ignored per handoff §2).
  user_message_verbatim:
    "step 4, currently ligand behind grid, panel left goes to left, no error. rotated to have ligand on left and grid on right, panel left goes down"
    "previous failing case happens for both keyboard and panel"
    "for others, see the output in the above run, ask me if u cannot get which step for which log line"
  console_log_verbatim:
    PyMOL>print(cmd.get_setting_text("button_mode_name"))
    3-Button Viewing
    AA-match 0.1.0: game started -- 2 molecule(s), 18 amino-acid slot(s), seed 1769203439 (        cleaned 0 prior game object(s)).
     You clicked /_aam_aa07/AAM//HIS`2/CG
     Selector: selection "sele" defined with 1 atoms.
    PyMOL>print(cmd.get_view()[0:9])
    (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
     You clicked /_aam_aa08/AAM//SER`2/CA
     Selector: selection "sele" defined with 1 atoms.
    PyMOL>print(cmd.get_view()[0:9])
    (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    PyMOL>rotate x, 90
    PyMOL>print(cmd.get_view()[0:9])
    (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    PyMOL>print(cmd.get_view()[0:9])
    (0.9877981543540955, 0.14454860985279083, -0.05795199051499367, 0.06564578413963318, -0.049033861607313156, 0.9966374635696411, 0.14122097194194794, -0.98828125, -0.057924166321754456)
    PyMOL>echo above is after mouse rotation
      File "toplevel", line 1
        echo above is after mouse rotation
             ^
    SyntaxError: invalid syntax
    PyMOL>#above is after mouse rotation
     You clicked /_aam_aa04/AAM//ILE`2/CA
     Selector: selection "sele" defined with 1 atoms.
    PyMOL># the following is when ligand left, grid on right, after another mouse rotation
    PyMOL>print(cmd.get_view()[0:9])
    (0.04409969598054886, 0.11378264427185059, -0.9925242066383362, 0.9880138635635376, 0.14213986694812775, 0.060194872319698334, 0.1479278951883316, -0.9832831025123596, -0.10614964365959167)
    PyMOL>print(type(cmd.get_wizard()).__module__)
    pmg_tk.startup.aamatch.wizard
    PyMOL>print(cmd.get_view()[0:9])
    (0.04409969598054886, 0.11378264427185059, -0.9925242066383362, 0.9880138635635376, 0.14213986694812775, 0.060194872319698334, 0.1479278951883316, -0.9832831025123596, -0.10614964365959167)
  followup_verbatim: "i did install the one in this repo bia plugin path" (install ORIGIN = this repo; install DATE unknown — key open question).
  receipt_mapping: (a) = first two identity blocks (post-start; post-pick repeat);
    (b) = third identity block, directly after `rotate x, 90`;
    (c1) = fourth block, after first mouse rotation (user comment "#above is after mouse rotation");
    (c2) = fifth block, after another mouse rotation (user comment "# the following is when ligand left, grid on right, after another mouse rotation");
    press-1 ("goes to left", "no error", scene "ligand behind grid") = at the c1 view (or fresh view — both non-discriminating, see decode (4));
    press-2 ("goes down") = at c2 (user-labeled + geometry-verified below); press-2 panel-ERROR-line status NOT reported;
    module identity + drift re-print = after (c2); drift clean (identical block).
  decoded (orchestrator PRELIMINARY — continuation agent MUST independently recompute every number from the verbatim blocks before relying on it):
    (1) (b)==(a): identity blocks identical — the §4 / H-A source fact (cmd.rotate moves atoms, never the camera) now proven LIVE on the user's machine, in their own console.
    (2) (c1),(c2) != (a): plain left-drag in "3-Button Viewing" orbited the camera (exactly per Q1/Q2 source receipts: ('l','none','rota') -> SceneRotate -> m_rotMatrix) → H-B-content ELIMINATED for this session — the drag was a real camera rotation.
    (3) c2 self-label verified geometrically: at (c2), world +z (ligand side at start) -> screen x = R_c2 row0 col2 = -0.99252 -> screen LEFT; world -z (grid side) -> screen RIGHT. The matrix matches the user's own label "ligand left, grid on right".
    (4) THE DECISIVE PRESS ("goes down" at c2):
        repo view-relative law (current code, machine-proven): screen displacement = R * R^T * (-1,0,0) = (-1, 0, 0) EXACTLY → monitor-LEFT;
        world-absolute step (raw unconjugated translate of (-1,0,0) — old semantics): screen displacement = R_c2 * (-1,0,0) = -(column 0 of R_c2) = (-0.04410, -0.98801, -0.14793) → essentially straight DOWN (slight left);
        OBSERVED: "goes down" → matches world-absolute semantics, NOT the repo law.
        c1 press ("goes to left"): world-absolute → -(col 0 of R_c1) = (-0.988, -0.066, -0.141) → LEFT; repo law → LEFT; both agree → non-discriminating; observed LEFT consistent with both.
        historical coherence under world-absolute semantics: Ry(180) → screen (+1,0,0) = RIGHT = the 10-11 verbatim "if i rotate 180 degree and press left, it goes right"; the 2026-09-21 verbatim "not viewer-relative at all — like absolute coordinates" = same fingerprint; the original 03-06 "up/down feel inverted after scene rotation" = world-absolute steps under a rolled/tilted camera. ALL failing rows across the entire lineage are consistent with world-absolute movement under a rotated/rolled camera.
    (5) PIVOTAL: module identity = pmg_tk.startup.aamatch.wizard — the Plugin-Manager INSTALLED copy was active, NOT the repo module `aamatch`. AGENTS.md gates 5/6: an install is a POINT-IN-TIME snapshot; it never sees repo edits until REINSTALLED. The machine-proven view-relative law lives in the REPO tree; the installed snapshot is what executed the presses. TENSION with handoff §3 (10-11 identity print → `aamatch`, "the exact one in this repo", same session as the failing rows): today's receipt is in-session, numbered, timestamped; the 10-11 claim has no numbers. Either the sessions were launched with different staging (repo-path session then vs bare installed-copy session now), or the 10-11 attribution was wrong. Receipts-first: today's stands; the retest identity receipt will settle the 10-11 question.
    (6) H-D (input-surface mixup) ELIMINATED: "previous failing case happens for both keyboard and panel".
    (7) drift check clean at (c2): two identical blocks with the identity print between them.
    (8) press-1 "no error": absence of a panel ERROR line is not discriminating by itself (old installed code may lack the identity-assert; repo code asserts AFTER the move, and the step-9 console sweep never shows panel ERROR lines anyway — see repo-side receipts above).
  h_new (H-E, version skew / stale tested artifact — LEADING): ALL failing GUI rows ran an installed snapshot whose movement steps behave world-absolute (or at least lack the current conjugation); the repo's current view-relative law has never failed a test on current code (P1 30/30 @ 0.0000 deg; step-4 probe screen_dx=-1.000000 at every orientation; SMOKE-07/23 green). The 08.2-10 discrepancy is a TESTED-ARTIFACT / VERSION-SKEW artifact, not a defect in the shipped law. Install origin = this repo (user statement, verbatim above); install AGE unknown — if the snapshot predates the movement fixes (Phase 8.2 waves or the earlier conjugation era), it carries old semantics regardless of origin. If the diff unexpectedly shows current code, check secondary stale mechanisms: stale __pycache__ shadowing fresh .py files; a second (older) aamatch install location shadowing the plugin path.
  decisive_next_checks (autonomous on resume):
    d1: locate the installed aamatch on disk (Windows side, WSL-readable via /mnt/c): read /mnt/c/src/run-conda-pymol.bat → conda prefix → search the prefix (site-packages / pmg_tk startup dirs) for the aamatch install; fallback: user-home PyMOL plugin dirs; golden receipt ONLY if still unresolved: print(sys.modules[type(cmd.get_wizard()).__module__].__file__).
    d2: diff the installed copy's movement code vs repo main (wizard.py nudge/do_key/do_special paths; wizard_core.py — does view_camera_to_world exist there at all; step vectors; conjugation formula) + file mtimes vs the 8.2 commit dates + shadow-copy sweep (second install dir, stale __pycache__).
    d3 branch: installed != repo (expected) → ROOT CAUSE = H-E version skew; remedy = fresh Plugin-Manager reinstall from the CURRENT repo (the sanctioned human-checkpoint mechanism per AGENTS.md), exactly ONE copy active (gate 5 no-mix), then retest at exactly today's failing orientation (c2-style, "ligand left, grid on right") expecting monitor-LEFT; then step-4 adjudication + plain-language user answer + dated resolution section in the HANDOFF. installed == repo on movement code (unexpected) → H-C-live branch per handoff §6: TEMPORARY UNCOMMITTED instrumentation (debug print of cmd.get_view()[0:9] inside wizard._nudge_cam_impl around the view_camera_to_world call), one user press at a c2-style orientation, compare vs console get_view, capture to tmp/, REVERT, then STOP per Rule 4 → hand to /gsd-plan-phase.
  status: PAUSED (user instruction 2026-10-12) — continuation agent to be spawned with these receipts when the user returns.

- timestamp: 2026-10-18 (independent decode recompute — COMPLETE; tmp/verify_decode_082.py, all asserts)
  checked: every number in the orchestrator's preliminary decode (verbatim (a)/(b)/(c1)/(c2) blocks, row-major world->camera R convention per the P1/step-4 probes)
  found: ALL CHECKS PASS. (b)==(a) EXACT identity — the console `rotate x, 90` never moved the camera (H-A closed LIVE in the user's own console). (c1),(c2) are valid rotations (RRT dev 2.1e-6 / 4.4e-6; det +0.999998 / +0.999995) and differ from (a) — H-B-content dead for this session: the drags orbited the real camera. c2 self-label geometrically verified: world +z (ligand side) -> screen_x= -0.99252 = LEFT; world -z (grid) -> +0.99252 = RIGHT — matches "ligand left, grid on right". THE DECISIVE c2 press (step s=(-1,0,0)): repo law -> screen (-0.999996, +1e-6, +1e-6) = 0.000 deg off monitor-LEFT; world-absolute -> screen (-0.044100, -0.988014, -0.147928) = 8.880 deg off straight DOWN (the user's "goes down"); variant R.s -> 78.9 deg off down; variant R^T.R^T.s -> 83.5 deg off down — NEITHER variant matches "down": the observation uniquely fingerprints RAW WORLD-ABSOLUTE steps. c1 press non-discriminating (both laws ~ LEFT; observed LEFT consistent). Ry(180)/Rz(180) under world-absolute -> screen exactly (+1,0,0) RIGHT — the 10-11 "rotate 180 left->right" and 2026-09-21 "like absolute coordinates" rows fit the same fingerprint. Orchestrator's preliminary numbers reproduce to all printed digits.
  implication: every failing row in the entire lineage fingerprints world-absolute movement under a rotated/rolled camera while the repo's current law is exact monitor-LEFT. Whatever executed the failing presses was NOT the current conjugation law — or the current law somehow fails live in the real GUI (the scripted GUI repro decides).

- timestamp: 2026-10-18 (d4 — scripted real-GUI reproduction — RUN COMPLETE; the agent session was ABORTED by the user mid-round before analysis/write-up; orchestrator transcribed the results from the log on disk)
  authorization: the user's 2026-10-18 grant, verbatim: "I guess u can try to script-test gui as long as u give a timeout to the shell so i dont need to close it for you." / "resume."
  checked: does the current repo code, in the real Windows GUI, at the user's exact (c2) orientation, move the AA monitor-LEFT through the user's own input channels?
  found: EXECUTED 2026-10-18 03:34; full log = tmp/probe_082_gui_repro.log (scripts: tmp/probe_082_gui_repro_outer.py + tmp/probe_082_gui_repro_part2.py; watchdog-armed per the grant; self-terminated cleanly). Real GUI, real game (seed 42), scripted pick; the in-log identity receipts show the active plugin was the repo's aamatch code (lines verbatim in the log). Presses driven through the LOADED plugin's OWN verbatim button strings (Left: 'cmd.get_wizard().nudge_cam(-1, 0, 0)') AND wiz.do_special(100), at IDENT control, Ry180 fingerprint, and the USER'S VERBATIM (c2) rotation block (live-read exact, block dev=0 at all three orientations):
    IDENT-control     panel   world=(-1,0,0)   screen=(-1,0,0)   cls=VIEW-RELATIVE  dev 7.53e-08
    IDENT-control     special world=(-1,0,0)   screen=(-1,0,0)   cls=VIEW-RELATIVE  dev 0
    RY180-fingerprint panel   world=(+1,0,0)   screen=(-1,0,0)   cls=VIEW-RELATIVE  ang_WABS=180.0000deg (world-absolute would be exact RIGHT — refuted)
    RY180-fingerprint special world=(+1,0,0)   screen=(-1,0,0)   cls=VIEW-RELATIVE
    C2-USER-VERBATIM  panel   world=(-0.044100, -0.113783, 0.992524) screen=(-0.999996, 0.000001, 0.000001) dev_VIEWREL=2.13e-07 ang_VIEW=0.0001deg ang_WABS=87.4725deg cls=VIEW-RELATIVE identity=OK uniform=4.52e-07 err=None
    C2-USER-VERBATIM  special world=(-0.044100, -0.113783, 0.992524) screen=(-0.999996, 0.000001, 0.000001) dev_VIEWREL=2.38e-07 cls=VIEW-RELATIVE identity=OK err=None
    panel-vs-keyboard agreement at c2: dev=2.51e-08; every PASS row green; ALL GR-VERDICT lines = VIEW-RELATIVE. Verbatim verdict markers (log lines 104-105):
      "=== GR-C2-VERDICT: VIEW-RELATIVE — at the user's exact c2 orientation, the CURRENT repo code in the REAL GUI moved the AA EXACTLY MONITOR-LEFT via BOTH the panel-Left button path and the keyboard channel (screens printed above) — the shipped law holds live in the user's own environment ==="
      "=== GR-REPRO-COMPLETE: all checks pass ==="
  implication: at the user's exact failing orientation, the current repo code in the real GUI moved the AA EXACTLY monitor-LEFT via BOTH input channels — d4 could not reproduce the 10-12 "goes down" row on current code. The 10-12 row is NOT adjudicated by d4 alone; remaining explanations are session-side only (extra-rotation-before-press, board-frame wording, or a zero-trace transient — see Current Focus). Further steps are ASK-FIRST per the USER RULING entry below. The handoff §6 instrumentation branch is NOT warranted.

- timestamp: 2026-10-18 (USER RULING — session protocol + record purge directive; VERBATIM record)
  found:
    "the subagent gone far away from what its expected to, i stopped it to avoid further waste of time and tokens. quickly report whats done by the subagent if u have access to the history, then pause for now"
    "commit the changes first b4 u stop, if the change is meaningful / otherwise chkout head"
    "and ill start a new session to avoid any further pollusion"
    "or u update it to correct irrelevent stuff"
    "stop why ur also distracted by the subagnet that keep guessing but never just ask me?"
    "path-related stuff irrelevant, pymol is run directly via cmd. its wrong to assume its issue" / "this is why i stopped u"
    "seek my approval i worry u will polute the session" / "after u decie"
    approval given 2026-10-18: "Purge harder" — delete the environment/path sweep, pyc-audit, code-identity and launch-mechanics entries entirely; keep only the decode + d4 results + this ruling.
  action_taken: purge applied per approval; the raw artifacts of the purged entries remain only as git-ignored tmp/ files (not findings; not to be revived as candidate explanations).
  implication (BINDING on any continuation): (1) PATH/LAUNCH CONTENT RULED IRRELEVANT — PyMOL is run directly via cmd; do not build or record path/install/import/launch theories as candidate explanations. (2) ASK-DON'T-GUESS: when the remaining uncertainty is in the USER's session (chronology, wording, perception), put a short numbered question set to the user and WAIT — no autonomous forensic machinery. (3) No record changes beyond this commit without the ask-first flow; the user starts a fresh session next.

## Resolution

root_cause: NO CODE DEFECT. The shipped law was exonerated twice on final receipts — machine (P1 30/30 @ 0.0000 deg; step-4 probe screen_dx=-1.000000 at every orientation) and LIVE in the real GUI in the user's environment (d4, 2026-10-18 03:34: at the user's verbatim (c2) orientation, panel AND keyboard channels, exact monitor-LEFT, all rows PASS, tmp/probe_082_gui_repro.log). The 10-12 "goes down" row was never reproduced by current code; camera state at press time was never receipted; the session-side candidates (extra rotation before the press / board-frame wording / zero-trace transient) stay UNADJUDICATED — mooted by the user's 2026-10-18 design decision before the two closing questions were answered.
fix: none applied to movement code — the disputed input class is DELETED BY DECISION (2026-10-18, verbatim): "mouse to replace all keyboard direction buttons, and replace the directions in wizard panel, only keep the towards ligand in that list." Mouse-drag becomes THE movement input; all keyboard direction keys removed; panel movement list = Toward-ligand only. Recorded in STATE Phase 8.2 Decisions + PROJECT Key Decisions + ROADMAP 8.2 NOTE + the 08.2-10 handoff RESOLUTION section.
verification: exonerated-by-receipt (d4 all-pass, both channels, user's exact orientation); the pivot itself gets its own dedicated phase (fresh planning, NOT --gaps, no overrides) with RED-pinned tests + a [HUMAN] GUI checkpoint under the recorded Pitfall-6 hazards (Dragging-wizard replacement of the active game wizard; coordinate baking; rigid-body AA-object targeting only).
files_changed: none in aamatch/ (planning-doc records only; GUI-test scripts live uncommitted in git-ignored tmp/)
