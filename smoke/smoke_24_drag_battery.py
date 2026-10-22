"""SMOKE-24: drag-movement battery (Phase 8.3 pivot) -- plans 08.3-02/-12.

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_24_drag_battery.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-24 PASS ==='.
Timeout: 240 s initial recipe (baseline 120 s class; real game start +
composition, as SMOKE-07/23).

LANDED BY 08.3-02 BEFORE ANY DRAG IMPLEMENTATION EXISTS -- and that is
the point (drag research sec.5 note 1): the Pitfall-6 positive control
passes on current PyMOL TODAY because it pins STOCK PyMOL 2.5.0
drag-installing behavior, not aamatch behavior -- "it is a
PyMOL-behavior pin, not an aamatch-code pin". Pitfall-6 (drags REPLACE
the active game wizard mid-session) is the single most dangerous hazard
of the drag pivot; the probe-B receipts proved the displacement +
restore behaviors stable on this exact build, so this file pins them
PERMANENTLY as smoke rows before any drag code lands. 08.3-12
(2026-10-23) then appended the aamatch-facing rows 1-2 / 4-6 / 8-9
against the landed drag core (08.3-04) WITHOUT touching PART 0 / PART P
(dated evolution: PART 0b + PART 0c added, PRE-READ block extended with
the editor-scheme baseline, teardown sweep extended with the private
_aam_drag_sele name). Later drag plans extend this file WITHOUT
re-deriving the battery design (the roster number 24 is derived from
this basename by run_smoke.sh's sed rule -- no runner edit was needed).

THE PLANNED ROW MAP -- transcribed from the drag research RQ6 table
(08.3-RESEARCH-drag.md sec.2 RQ6; this is the battery's FINAL shape --
every row now has its owner; rows 1-2 / 4-6 / 8-9 landed 08.3-12
against the landed drag core (08.3-04)):
  1. Arming contract: after a scripted pick + a wizard=0/edit=0 arm the
     GameWizard stays top-of-stack (identity predicate wizard.py:
     122-133), stack depth unchanged, get_editor_scheme() == 3,
     get_drag_object_name() == <picked obj>, '_drag' atom count ==
     object count, button_mode unchanged (probe C1-C9, 083B) — LANDED
     08.3-12 (2026-10-23; rows 1a-1d).
  2. Re-arm law: any script pick clears the armed drag state; a re-arm
     retargets to the newly picked object; a double-arm is idempotent
     (probe 083B(1)(2)(4)) — LANDED 08.3-12 (rows 2a-2c).
  3. Pitfall-6 positive control, PERMANENT regression pin (THIS SHELL,
     landed 08.3-02): a stock cmd.drag(<selection>) installs the
     Dragging wizard OVER the active GameWizard (stack depth +1,
     GameWizard dormant beneath); the stock panel Done path
     cmd.set_wizard() pops it and the GameWizard AUTO-RESUMES
     top-of-stack and still receives picks; the Dragging wizard's
     cleanup restores the saved button_mode (probe B1-B6).
  4. Deactivation: cmd.drag() clears the drag state and the editor
     scheme returns to baseline, GameWizard untouched; the Done path
     leaves no '_drag'/pk1/'sele' strays — the 03-07 restoration-table
     law (probe H1, 083B(3)) — LANDED 08.3-12 (rows 4a-4b; the
     PyMOL-internal '_drag' shell receipted there, see the residual
     note below).
  5. Gesture wiring: cmd.button(<slots>, 'dgmv'/'dgrt'/'dgmz') accepted
     without exception; profile-level restore via button_mode +
     cmd.mouse() works (probe D1/D2) — LANDED 08.3-12. DISPOSITION
     (2026-10-19, STATE Phase 8.3 Decisions): wired slots =
     cmd.button('left','shft','dgmv') translate +
     cmd.button('left','ctsh','dgmz') depth +
     cmd.button('right','shft','dgrt') drag-rotate (probe D receipted
     left-button slots; the right-slot delivery is an 08.3-04 pin:
     stock ('right','shft') = 'clip', overridden by 'dgrt').
  6. matrix_mode guard: object-scoped matrix_mode=0 set/read on the
     game objects at arm time (probe E1) — LANDED 08.3-12 (row 6).
  7. Programmatic drag math (the wizard-side drag_move(dx_px, dy_px)
     helper): world delta == view_camera_to_world(live view,
     (dx*s, dy*s, 0)) with s = (-view[11]) * 2*tan(fov*pi/360) /
     viewport_h; identity clean after every step; per-axis 02-15
     float32 tolerances; view-invariance under the fixed S2/S3 blocks;
     all-atoms-identical displacement (rigidity) (probe 083C + the
     SMOKE-23 PART C/D pattern) — lands 08.3-14 (needs 08.3-10's
     drag_move surface; NOT authored here).
  8. Non-AA targets never drag: the arm guard refuses ligand/board/user
     objects — wizard-side _objects_by_slot membership before arming
     (design test) — LANDED 08.3-12 (row 8).
  9. Game-over gate: drag refused when engine.is_over()
     (_require_playing first — the 06-06 law) — LANDED 08.3-12 (row 9).
 10. Deletion battery: direction keys/buttons gone — dated
     EXPECTED-RED bridges (CONTEXT note 3) — landed with the wave-2/3
     deletion plans (08.3-03 roster + 08.3-05..08.3-09 reworks; the
     deletion proofs live in their own smokes/unit pins).


[HUMAN]-ONLY CAVEATS — NOT smoke-provable, GUI checkpoints (drag
research sec.3 table): real-mouse drag feel (cursor tracking,
parallax, modifier ergonomics, box-select loss — the C SceneDrag path
has no event pump headless); do_dirty/do_view/do_position hook firing
in the GUI render loop (probe F1/F2 count=0 headless); Alt-key
delivery (the Option B risk — MOOT on the 2026-10-19 Option-A
disposition, kept on the list for any later re-map); drag-rotate
pivot feel at the 'dgrt' bbox-center pivot (recorded minor divergence
from the atom-centroid rotate laws).

PART 0  REAL GAME + SCRIPTED PICK (the smoke_07/smoke_23 recipe): the
        one-call REAL start path gamestart.start_game() (DEFAULTS,
        seed 42, bundled manifest: cleanup -> engine.new_game ->
        engine.materialize -> compose_molecule_view -> GameWizard + the
        cmd.set_wizard activate push, wizard.py:222-245); the wizard
        is cmd.get_wizard(); molecule-0 slot objects resolve from the
        placement registry; a scripted pick runs through the REAL
        do_select (cmd.select('sele', '<slot obj> and name CA') ->
        do_select('sele') — the C-layer click equivalent).
PART 0b ROWS 1-2 + ROW 4 (landed 08.3-12): the SAME live game (the
        PART P hygiene tail left it as-found) drives the aamatch drag
        core's arm/re-arm/deactivation laws. Every row is a
        transcription of the drag research RQ6 table with its probe
        receipt in the block comment; the live tmp/ reconnaissance
        for this plan is receipted in 08.3-12-SUMMARY.md.
PART 0c ROWS 5-9 (landed 08.3-12): row 4's Done-path pop ENDS game #1
        by design, so a second real gamestart.start_game() supplies
        the live session for gesture wiring (row 5), the matrix_mode
        guard (row 6), the non-AA refusal (row 8), and the game-over
        refusal (row 9).
PART P  THE PITFALL-6 POSITIVE CONTROL — every row is a TRANSCRIPTION
        of a probe_083 B receipt (the verbatim probe lines below are
        the authority; tmp/ is git-ignored — 08.3-RESEARCH-drag.md
        sec.2 RQ1b is the durable record):
          PROBE-083 B1 stock cmd.drag installs Dragging wizard   PASS type=Dragging
          PROBE-083 B stack after stock drag: depth=2 types=['GameWizard', 'Dragging']
          PROBE-083 B2 GameWizard dormant beneath                PASS types=['GameWizard', 'Dragging']
          PROBE-083 B3 editor scheme now 3                       PASS scheme=3
          PROBE-083 B4 button_mode switched by edit_mode         PASS button_mode=1 (pre 0)
          PROBE-083 B5 pop Dragging -> GameWizard auto-resumes   PASS type=GameWizard
          PROBE-083 B6 button_mode restored by Dragging cleanup  PASS button_mode=0 (want 0)
        P1  stock install: cmd.drag('<slot-0 object>') — the probe's
            whole-object form, DEFAULT wizard=1/edit=1 implied ->
            cmd.get_wizard() is a 'Dragging' (B1).
        P2  stack introspection: depth == 2 and types ==
            ['GameWizard', 'Dragging'] — the GameWizard DORMANT
            beneath (B1/B2).
        P3  get_editor_scheme() == 3 after the stock install (B3;
            the pre-install baseline scheme is captured first).
        P4  button_mode switched by the stock drag: record the
            pre-install value FIRST, assert it CHANGED (B4). The
            detail also prints pre-install == the pre-game baseline
            (a pre-implementation fact: the game start path never
            touches button_mode; if a later plan makes the game own
            the profile this row must be evolved with a dated
            EXPECTED-RED bridge, never silently edited).
        P5  dismiss via the stock panel Done path = cmd.set_wizard()
            -> the GameWizard AUTO-RESUMES top-of-stack as the SAME
            instance (B5); the ACTIVE wizard still receives picks:
            one more scripted pick per the smoke_07 recipe post-pop
            and the slot selection CHANGES (r0c0 -> r0c1).
        P6  button_mode RESTORED to the P4 pre-install value by the
            Dragging cleanup (B6) — assert post == pre, NEVER a
            hard-coded 0.
        PT  hygiene tail (the 03-07 restoration-table law preview):
            pop anything Part P pushed (P5 did), deactivate the drag
            state (cmd.drag() -> get_drag_object_name() '', the
            probe H receipt), delete the Part-P selection names
            ('sele' consumed by the real do_select; '_drag' from the
            stock install deleted), stack as-found (depth 1,
            ['GameWizard']), and the slot-0 object matrix still
            IDENTITY — the stock object-name arm is the Pitfall-6c
            MATRIX-path branch (research RQ5), and this pin proves
            the arm alone (no motion events headless) writes nothing.
            The finally then tears the game down (smoke_23 shape) and
            the teardown check re-asserts the pre-game object names.

HONEST SCOPE: PART P pins STOCK PyMOL drag-installing behavior ONLY --
every PART P assertion is about PyMOL's own Dragging-wizard machinery.
PART 0b / PART 0c (landed 08.3-12) pin the AAMATCH drag core (the
08.3-04 surface): the selection-form arm, the per-pick re-arm, the
Done-path deactivation/hygiene, the disposition gesture wiring, the
matrix_mode=0 guard, and the non-AA + game-over refusals. What remains
unproven is exactly the [HUMAN]-only list above (real-mouse feel, GUI
hook cadence, Alt delivery, dgrt pivot feel) plus row 7's drag-move
MATH battery (08.3-14, needs 08.3-10's drag_move surface).

RECORDED RESIDUAL (2026-10-23, row 4b receipt): PyMOL's own INTERNAL
'_drag' selection (created by the C-side EditorActivate when our arm
calls cmd.drag; it mirrors the drag target's atom set) SURVIVES both
cmd.drag() deactivation and GameWizard.cleanup() (which deletes only
our private _aam_drag_sele). Probed live: names ['_drag'] with 19
atoms after the Done path, hide_underscore_names='on' (panel-hidden).
The 03-07 "no _drag strays" element therefore holds only for the
names aamatch OWNS after the landed core; the smoke sweeps the
PyMOL-internal shell exactly as the PART P tail always has. A
cleanup-side delete of '_drag' is recorded as a candidate micro-fix
for the wizard file's owner (NOT edited here -- parallel wave).

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv
first / cwd fallback (never __file__); import aamatch directly
(module identity 'aamatch' — NEVER the pmg_tk.startup path in the
same session); every print on ONE line and flushed; explicit space
dicts in every iterate (the aamatch rows added 08.3-12 iterate atom
IDs with an explicit space dict + no round()); no round() in
expressions; no calls to the placement.py banned cmd APIs —
cmd.get_object_matrix IS legal and required (the identity re-assert);
the Part-P / aamatch-row selection names are deleted before the final
teardown; zero object leakage pinned; numbered PASS lines with a
check-count assert at the end (a skipped planned row fails the battery
loudly).

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_24_drag_battery.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []
CHECKS = []               # ordered registry of every check run


def check(name, cond, detail=''):
    """Numbered receipt line: the verdict carrier is the marker, but
    every planned row prints its own [NN] PASS/FAIL line (the count
    assert at the end fails the battery if any planned row was
    skipped silently)."""
    num = len(CHECKS) + 1
    CHECKS.append(name)
    print('SMOKE-24 [%02d] %-54s %s %s'
          % (num, name, 'PASS' if cond else 'FAIL', detail), flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

from aamatch import engine  # noqa: E402
from aamatch import gamestart, placement  # noqa: E402
from aamatch import wizard as wizard_mod  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

IDENT_F32 = 1e-6          # identity after float32-touching matrix ops


def _obj_matrix(name):
    """cmd.get_object_matrix as a 16-list (or None)."""
    m = cmd.get_object_matrix(name)
    if m is None:
        return None
    return [float(v) for v in m]


def _is_identity(m16, tol=IDENT_F32):
    if m16 is None or len(m16) != 16:
        return False
    want = (1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0)
    return all(abs(m16[i] - want[i]) <= tol for i in range(16))


def _identity_dev(m16):
    """Max |m16 - identity| per element (inf when None/mis-shaped) --
    the P13 receipt detail (receipts carry real data, never %s)."""
    if m16 is None or len(m16) != 16:
        return float('inf')
    want = (1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0)
    return max(abs(m16[i] - want[i]) for i in range(16))


def _atom_ids(sel):
    """[(model, ID), ...] for a selection OR object name (explicit
    space dict, uppercase ID, no round()) -- the rigid-body receipt
    method for the 08.3-12 rows (probe_083 style: content comparison,
    never a bare count). Missing names return [] instead of raising so
    a failed arm surfaces as a FAIL row, not a driver crash."""
    known = (list(cmd.get_names('selections'))
             + list(cmd.get_names('objects')))
    if sel not in known:
        return []
    rows = []
    cmd.iterate(sel, 'stored.append((model, ID))', space={'stored': rows})
    return sorted(rows)


pre_names = list(cmd.get_names('objects'))
pre_button_mode = int(cmd.get('button_mode'))
pre_msm = int(cmd.get('mouse_selection_mode'))
pre_scheme = int(cmd.get_editor_scheme())
print('SMOKE-ENV pre button_mode=%d msm=%d editor_scheme=%d '
      'pre_names=%s' % (pre_button_mode, pre_msm, pre_scheme, pre_names),
      flush=True)

try:
    # ============================================================
    # PART 0: the REAL game + scripted pick (the smoke_07/23 recipe)
    # ============================================================
    wiz = gamestart.start_game()          # DEFAULTS, seed 42, compose
    top0 = cmd.get_wizard()
    check('P0 real game started; GameWizard active (start_game '
          'instance)', wiz is not None and top0 is wiz
          and wizard_mod.is_game_wizard_any_identity(top0),
          'cmd.get_wizard()=%r type=%s (module %s)'
          % (top0, type(top0).__name__, type(top0).__module__))
    mol0 = wiz._registry['molecules'][0]
    slot_ids = sorted(mol0['slots'])
    slot_obj = mol0['slots'][slot_ids[0]][0]
    check('P0 registry resolves molecule-0 slots (>= 2 for the P5 '
          're-pick)', len(slot_ids) >= 2,
          'slots=%d first=%s picked=%s' % (len(slot_ids), slot_ids[0],
                                           slot_obj))
    stack0 = cmd.get_wizard_stack()
    types0 = [type(w).__name__ for w in stack0]
    check('P0 baseline stack: depth 1, types [GameWizard]',
          len(stack0) == 1 and types0 == ['GameWizard'],
          'depth=%d types=%s' % (len(stack0), types0))
    cmd.select('sele', '%s and name CA' % slot_obj)
    wiz.do_select('sele')
    check('P0 scripted pick routes to molecule-0 slot %s' % slot_ids[0],
          wiz._current_slot == slot_ids[0] and wiz._error is None,
          'slot=%r want %r error=%r'
          % (wiz._current_slot, slot_ids[0], wiz._error))
    print('SMOKE-ENV game seed=42 defaults slots=%d picked=%s '
          '(slot %s)' % (len(slot_ids), slot_obj, slot_ids[0]),
          flush=True)

    # ============================================================
    # PART P: the Pitfall-6 positive control (probe B1-B6 receipts)
    # ============================================================
    # DATED EVOLUTION RECEIPT (2026-10-23, 08.3-12): rows P1-P6 are
    # byte-stable since 08.3-02, but their INPUTS changed when 08.3-04
    # landed the per-pick arm: the P0 scripted pick is a REAL do_select
    # -> do_pick -> _arm_drag, so an aamatch drag is ALREADY armed (and
    # the editor scheme is already 3) before the stock install. The
    # 08.3-02 receipt read 'editor_scheme before stock drag: 1'; today
    # it reads 3. P3 still asserts the stock install's required end
    # state (scheme == 3 -- the Dragging wizard's check_valid condition)
    # and P4 still proves the button_mode switch, so the stock pin
    # holds; only the pre-read baseline moved. Never silent -- this is
    # the receipt (see 08.3-12-SUMMARY).
    # Baselines captured BEFORE the stock install (probe PART A shape).
    scheme_pre = int(cmd.get_editor_scheme())
    p4_pre = int(cmd.get('button_mode'))
    print('SMOKE-ENV editor_scheme before stock drag: %d '
          'button_mode pre-install: %d' % (scheme_pre, p4_pre),
          flush=True)

    # P1 -- stock install: the probe's whole-object form, DEFAULT
    # wizard=1/edit=1 implied (probe line 'Dragging whole object').
    cmd.drag(slot_obj)
    wz_b = cmd.get_wizard()
    check('P1 stock cmd.drag installs the Dragging wizard',
          wz_b is not None and type(wz_b).__name__ == 'Dragging',
          'type=%s (probe B1)' % (type(wz_b).__name__,))
    # P2 -- stack introspection (probe B1/B2 receipt line verbatim:
    # 'depth=2 types=['GameWizard', 'Dragging']').
    stack_b = cmd.get_wizard_stack()
    types_b = [type(w).__name__ for w in stack_b]
    check('P2 stack depth 2: [GameWizard, Dragging] -- GameWizard '
          'DORMANT beneath', len(stack_b) == 2
          and types_b == ['GameWizard', 'Dragging']
          and wizard_mod.is_game_wizard_any_identity(stack_b[0]),
          'depth=%d types=%s beneath-is-start-wizard=%s (probe B1/B2)'
          % (len(stack_b), types_b, stack_b[0] is wiz))
    # P3 -- editor scheme gate (probe B3).
    check('P3 editor scheme == 3 after the stock install',
          int(cmd.get_editor_scheme()) == 3,
          'before=%d after=%d (probe B3)' % (scheme_pre,
                                             int(cmd.get_editor_scheme())))
    # P4 -- button_mode switched by edit_mode(1) (probe B4: pre
    # recorded FIRST; the install must CHANGE it).
    p4_post = int(cmd.get('button_mode'))
    check('P4 button_mode switched by the stock drag (post != pre)',
          p4_post != p4_pre,
          'button_mode=%d (pre %d; pre-game baseline %d%s, probe B4 '
          'receipt 1 (pre 0))'
          % (p4_post, p4_pre, pre_button_mode,
             '' if p4_pre == pre_button_mode else ' MISMATCH'))
    # P5 -- dismiss via the stock panel Done path (the canonical
    # cmd.set_wizard() pop): GameWizard AUTO-RESUMES top-of-stack as
    # the SAME instance (probe B5 + the stack-native auto-resume law).
    cmd.set_wizard()
    wz_res = cmd.get_wizard()
    check('P5 cmd.set_wizard() pop -> GameWizard auto-resumes (same '
          'instance)', wizard_mod.is_game_wizard_any_identity(wz_res)
          and wz_res is wiz,
          'type=%s same_instance=%s (probe B5)'
          % (type(wz_res).__name__, wz_res is wiz))
    # P5b -- the resumed wizard still RECEIVES picks: one scripted
    # pick post-pop per the smoke_07 recipe; the slot selection CHANGES
    # (r0c0 -> r0c1). Drives cmd.get_wizard() -- the ACTIVE-stack top,
    # the object the C layer would dispatch to.
    slot2_obj = mol0['slots'][slot_ids[1]][0]
    ok5b = False
    detail5b = 'top wizard is not the resumed GameWizard: %r' % (
        type(cmd.get_wizard()).__name__,)
    if cmd.get_wizard() is wiz:
        cmd.select('sele', '%s and name CA' % slot2_obj)
        cmd.get_wizard().do_select('sele')
        moved = (wiz._current_slot == slot_ids[1]
                 and slot_ids[1] != slot_ids[0])
        ok5b = moved and wiz._error is None
        detail5b = ('slot=%r want %r (was %r -> CHANGED) error=%r'
                    % (wiz._current_slot, slot_ids[1], slot_ids[0],
                       wiz._error))
    check('P5b resumed wizard receives picks (slot selection '
          'changes)', ok5b, detail5b)
    # P6 -- button_mode RESTORED to the P4 pre-install value by the
    # Dragging cleanup (probe B6: 'button_mode=0 (want 0)'; assert
    # post == pre, never a hard-coded 0).
    p6_now = int(cmd.get('button_mode'))
    check('P6 button_mode restored to the pre-install value '
          '(post == pre)', p6_now == p4_pre,
          'button_mode=%d (want %d) (probe B6)' % (p6_now, p4_pre))

    # ============================================================
    # PART P hygiene tail: leave the game session EXACTLY as-found
    # (pop anything it pushed -- P5 did; delete its sele names;
    # deactivate the drag state per the probe H receipt).
    # ============================================================
    cmd.drag()                     # defensive deactivate (probe H1)
    for name in ('sele', '_drag', 'pk1'):
        if name in cmd.get_names('selections'):
            cmd.delete(name)
    stack_t = cmd.get_wizard_stack()
    types_t = [type(w).__name__ for w in stack_t]
    strays = [name for name in ('sele', '_drag', 'pk1')
              if name in cmd.get_names('selections')]
    check('PT cleanup: drag deactivated, no strays, stack as-found',
          cmd.get_drag_object_name() == ''
          and not strays
          and len(stack_t) == 1 and types_t == ['GameWizard']
          and stack_t[0] is wiz,
          'drag_obj=%r strays=%s depth=%d types=%s (probe H + the '
          '03-07 restoration-table law)'
          % (cmd.get_drag_object_name(), strays, len(stack_t), types_t))
    # The as-found identity pin: the stock object-name arm is the
    # Pitfall-6c MATRIX-path branch; with no motion events headless
    # the arm alone writes nothing (a stock-behavior drift that ever
    # writes an object matrix at arm time fails the battery loudly).
    m_slot = _obj_matrix(slot_obj)
    check('PT as-found: slot-0 object matrix still identity '
          '(Pitfall-6c pin)', _is_identity(m_slot),
          'max_dev=%.3g tol=%.1g (get_object_matrix is smoke-legal; '
          'the ObjectCombineTTT path only writes on fired drags)'
          % (_identity_dev(m_slot), IDENT_F32))
    print('SMOKE-ENV part-P complete: game session as-found '
          '(drag deactivated, stack depth 1)', flush=True)

    # ============================================================
    # PART 0b: ROWS 1-2 + ROW 4 -- the aamatch drag core (08.3-04)
    # ============================================================
    # The PART P hygiene tail left game #1 as-found (drag dearmed,
    # stack depth 1), so the SAME live wizard drives the aamatch-facing
    # laws. Row 4's Done path then ENDS game #1 by design; PART 0c
    # starts a second game for rows 5-9.

    # ------------------------------------------------------------
    # Row 1 -- ARMING CONTRACT (RQ6 row 1; probe C1-C9 + 083B).
    # Receipts (08.3-RESEARCH-drag.md sec.2 RQ1b/RQ2): the arm is the
    # SELECTION-form cmd.drag(_aam_drag_sele, wizard=0, edit=0) issued
    # by the LANDED core's do_pick tail (wizard.py:_arm_drag); no
    # stock wizard is installed, so the GameWizard stays top-of-stack
    # and keeps receiving picks. Live tmp/ reconnaissance 2026-10-23
    # (tmp/probe_08312.py): after the scripted pick -- drag_obj
    # '_aam_aa01', scheme 3 (pre 1), button_mode 0 (pre 0), stack
    # ['GameWizard'], _aam_drag_sele 19 atoms == object 19 atoms,
    # '_drag' 19 atoms (PyMOL's internal mirror), matrix identity.
    # ------------------------------------------------------------
    r1_obj = mol0['slots'][slot_ids[0]][0]
    r1_stack_pre = cmd.get_wizard_stack()
    r1_depth_pre = len(r1_stack_pre)
    r1_bm_pre = int(cmd.get('button_mode'))
    r1_scheme_pre = int(cmd.get_editor_scheme())
    cmd.select('sele', '%s and name CA' % r1_obj)
    wiz.do_select('sele')          # REAL pick route -> do_pick -> _arm_drag
    r1_stack = cmd.get_wizard_stack()
    r1_types = [type(w).__name__ for w in r1_stack]
    r1_top = cmd.get_wizard()
    check('Row 1a arm contract: GameWizard top-of-stack, depth unchanged',
          len(r1_stack) == r1_depth_pre and r1_types == ['GameWizard']
          and r1_top is wiz
          and wizard_mod.is_game_wizard_any_identity(r1_top)
          and wiz._error is None,
          'depth=%d (pre %d) types=%s same-instance=%s slot=%r error=%r '
          '(probe C2/C3/C9)' % (len(r1_stack), r1_depth_pre, r1_types,
                                r1_top is wiz, wiz._current_slot,
                                wiz._error))
    r1_drag = cmd.get_drag_object_name()
    r1_ids_obj = _atom_ids(r1_obj)
    r1_ids_sel = _atom_ids(wizard_mod._DRAG_SELE)
    r1_ids_int = _atom_ids('_drag')
    check('Row 1b arm contract: drag target == picked object; selection '
          'covers ALL its atoms', r1_drag == r1_obj
          and r1_ids_sel == r1_ids_obj and len(r1_ids_sel) == len(r1_ids_obj)
          and r1_ids_int == r1_ids_obj,
          'drag_obj=%r want %r private_atoms=%d obj_atoms=%d '
          'internal_drag_atoms=%d identical_ids=%s (probe C-sel/083B)'
          % (r1_drag, r1_obj, len(r1_ids_sel), len(r1_ids_obj),
             len(r1_ids_int), r1_ids_sel == r1_ids_obj))
    r1_bm_post = int(cmd.get('button_mode'))
    r1_scheme_post = int(cmd.get_editor_scheme())
    check('Row 1c arm contract: button_mode unchanged; editor scheme == 3',
          r1_bm_post == r1_bm_pre and r1_scheme_post == 3,
          'button_mode=%d (pre %d, probe C8) editor_scheme=%d (pre %d, '
          'probe C3)' % (r1_bm_post, r1_bm_pre, r1_scheme_post,
                         r1_scheme_pre))
    r1_m = _obj_matrix(r1_obj)
    check('Row 1d arm contract: object matrix still identity '
          '(baked-coords law)', _is_identity(r1_m),
          'max_dev=%.3g tol=%.1g (the selection-form arm never takes the '
          'matrix path -- RQ5/Pitfall-6c)'
          % (_identity_dev(r1_m), IDENT_F32))

    # ------------------------------------------------------------
    # Row 2 -- RE-ARM LAW (RQ6 row 2; probe 083B(1)(2)(4)).
    # Receipts: 'PROBE-083B(1)(2) any pick clears the armed state then
    # the wizard re-arms' + '083B(4) a second arm call is idempotent'.
    # The core arms as do_pick's LAST statement, so a second pick
    # retargets; a deactivate-then-pick re-arms from scratch.
    # ------------------------------------------------------------
    r2a_obj = mol0['slots'][slot_ids[1]][0]
    r2a_n = len(_atom_ids(r2a_obj))
    cmd.select('sele', '%s and name CA' % r2a_obj)
    wiz.do_select('sele')
    r2a_drag = cmd.get_drag_object_name()
    r2a_sel_n = len(_atom_ids(wizard_mod._DRAG_SELE))
    check('Row 2a re-arm law: second pick retargets the armed drag',
          r2a_drag == r2a_obj and wiz._current_slot == slot_ids[1]
          and wiz._error is None and r2a_sel_n == r2a_n
          and r2a_drag != r1_obj,
          'drag=%r want %r (was %r -> RETARGETED) slot=%r error=%r '
          'selection_atoms=%d obj_atoms=%d (probe 083B(1)(2))'
          % (r2a_drag, r2a_obj, r1_obj, wiz._current_slot, wiz._error,
             r2a_sel_n, r2a_n))
    cmd.drag()                     # deactivate (probe H1)
    r2b_drag_pre = cmd.get_drag_object_name()
    r2b_obj = mol0['slots'][slot_ids[2]][0]
    cmd.select('sele', '%s and name CA' % r2b_obj)
    wiz.do_select('sele')
    r2b_drag = cmd.get_drag_object_name()
    check('Row 2b re-arm law: a pick re-arms after external deactivation',
          r2b_drag_pre == '' and r2b_drag == r2b_obj
          and wiz._current_slot == slot_ids[2] and wiz._error is None,
          'deactivated=%r then pick -> drag=%r want %r slot=%r '
          'error=%r (probe 083B(2))'
          % (r2b_drag_pre, r2b_drag, r2b_obj, wiz._current_slot,
             wiz._error))
    r2c_before = (cmd.get_drag_object_name(),
                  len(_atom_ids(wizard_mod._DRAG_SELE)),
                  len(cmd.get_wizard_stack()),
                  int(cmd.get('button_mode')),
                  int(cmd.get_editor_scheme()))
    wiz._arm_drag(r2b_obj)         # the extra arm call (probe 083B(4))
    r2c_after = (cmd.get_drag_object_name(),
                 len(_atom_ids(wizard_mod._DRAG_SELE)),
                 len(cmd.get_wizard_stack()),
                 int(cmd.get('button_mode')),
                 int(cmd.get_editor_scheme()))
    check('Row 2c re-arm law: double-arm is idempotent',
          r2c_after == r2c_before,
          'before=%r after=%r (drag_obj, sele_atoms, depth, button_mode, '
          'scheme) (probe 083B(4))' % (r2c_before, r2c_after))

    # ------------------------------------------------------------
    # Row 4 -- DEACTIVATION + HYGIENE (RQ6 row 4; probe H1/083B(3)/D2).
    # Receipts: 'PROBE-083 H1 cmd.drag() deactivates' +
    # '083B(3) dearm returns the editor scheme to baseline' +
    # 'probe D2 button_mode restored'. The Done path = GameWizard
    # cleanup() + the canonical cmd.set_wizard() pop (idempotent
    # cleanup, the 03-07 restoration-table smoke style).
    # ------------------------------------------------------------
    wiz.cleanup()                  # Done path's cleanup half
    cmd.set_wizard()               # canonical pop (runs cleanup again)
    r4_drag = cmd.get_drag_object_name()
    r4_scheme = int(cmd.get_editor_scheme())
    r4_bm = int(cmd.get('button_mode'))
    r4_msm = int(cmd.get('mouse_selection_mode'))
    r4_stack = cmd.get_wizard_stack()
    check('Row 4a Done path: drag deactivated; scheme/button_mode/msm '
          'restored', r4_drag == '' and r4_scheme == pre_scheme
          and r4_bm == pre_button_mode and r4_msm == pre_msm
          and len(r4_stack) == 0,
          'drag=%r scheme=%d (pre %d) button_mode=%d (pre %d) msm=%d '
          '(pre %d) stack_depth=%d (probe H1/083B(3)/D2)'
          % (r4_drag, r4_scheme, pre_scheme, r4_bm, pre_button_mode,
             r4_msm, pre_msm, len(r4_stack)))
    # The 03-07 scan: names aamatch OWNS must be gone. PyMOL's own
    # INTERNAL '_drag' selection (created by EditorActivate on arm)
    # SURVIVES deactivation + cleanup -- receipted here, swept below
    # (probe 2026-10-23: 19 atoms, hide_underscore_names='on'; see the
    # header residual note + 08.3-12-SUMMARY).
    r4_names = list(cmd.get_names('selections'))
    r4_owned = [n for n in ('pk1', 'sele', wizard_mod._DRAG_SELE)
                if n in r4_names]
    r4_internal = [n for n in ('_drag',) if n in r4_names]
    r4_internal_atoms = cmd.count_atoms('_drag') if r4_internal else 0
    r4_hide = str(cmd.get('hide_underscore_names'))
    check('Row 4b Done-path hygiene: zero aamatch-owned strays (03-07 law)',
          not r4_owned,
          'aamatch_strays=%s selections=%s | PyMOL-internal _drag '
          'residual=%s atoms=%d hide_underscore_names=%r (receipted, '
          'not re-pinned; header note)' % (r4_owned, r4_names,
                                           r4_internal,
                                           r4_internal_atoms, r4_hide))
    # Sweep the private names before game #2 (the PART P tail pattern).
    for name in ('sele', 'pk1', '_drag', wizard_mod._DRAG_SELE):
        if name in cmd.get_names('selections'):
            cmd.delete(name)
    print('SMOKE-ENV rows 1-2 + 4 complete: game #1 Done path leaves the '
          'aamatch-owned scene clean', flush=True)

    # ============================================================
    # PART 0c: game #2 -- the live session for rows 5-9
    # ============================================================
    wiz2 = gamestart.start_game()
    r0c_top = cmd.get_wizard()
    r0c_stack = cmd.get_wizard_stack()
    r0c_types = [type(w).__name__ for w in r0c_stack]
    r0c_saved = wiz2._saved_button_mode
    check('P0c second real game started; GameWizard active (rows 5-9 '
          'harness)', wiz2 is not None and r0c_top is wiz2
          and wiz2 is not wiz
          and wizard_mod.is_game_wizard_any_identity(r0c_top)
          and len(r0c_stack) == 1 and r0c_types == ['GameWizard']
          and r0c_saved == pre_button_mode,
          'type=%s depth=%d fresh_instance=%s saved_button_mode=%r '
          '(pre-game %d)' % (type(r0c_top).__name__, len(r0c_stack),
                             wiz2 is not wiz, r0c_saved, pre_button_mode))

    # ------------------------------------------------------------
    # Row 5 -- GESTURE WIRING + PROFILE RESTORE (RQ6 row 5; D1/D2).
    # Disposition (2026-10-19): gesture=a -> ('left','shft','dgmv');
    # depth_drag=yes -> ('left','ctsh','dgmz'); drag_rotate_gesture=yes
    # -> ('right','shft','dgrt') (the 08.3-04 pin: stock ('right',
    # 'shft') = 'clip', overridden by 'dgrt').
    # NO per-slot READ-BACK API exists for cmd.button (the button map
    # is Python-level pymol.controlling state, not a settable value);
    # acceptance-without-exception is the probe-D1 receipt shape. The
    # PROFILE RESTORE half was receipted in Row 4a (button_mode back to
    # the pre-game snapshot after the Done path); the snapshot-fidelity
    # half is in P0c above.
    # ------------------------------------------------------------
    r5_slots = (('left', 'shft', 'dgmv'),
                ('left', 'ctsh', 'dgmz'),
                ('right', 'shft', 'dgrt'))
    r5_rejected = []
    for r5_args in r5_slots:
        try:
            cmd.button(*r5_args)
        except Exception:
            r5_rejected.append((r5_args, sys.exc_info()[0].__name__))
    r5_bm = int(cmd.get('button_mode'))
    r5_saved = wiz2._saved_button_mode
    check('Row 5 gesture wiring: the 3 disposition slots accepted; '
          'profile untouched', not r5_rejected
          and r5_bm == pre_button_mode and r5_saved == pre_button_mode,
          'slots=%s rejected=%s button_mode=%d saved_snapshot=%r '
          '(pre-game %d; restore receipted Row 4a; probe D1/D2)'
          % (list(r5_slots), r5_rejected, r5_bm, r5_saved,
             pre_button_mode))

    # ------------------------------------------------------------
    # Row 6 -- matrix_mode GUARD (RQ6 row 6; probe E1). The guard is
    # set by the LANDED _arm_drag at arm time (object-scoped), so the
    # receipt is on the FRESHLY picked object. Live recon 2026-10-23:
    # an unarmed slot reads '-1'; after its pick it reads '0'; a
    # sibling slot stays '-1' (object-scoped, never global).
    # ------------------------------------------------------------
    mol0b = wiz2._registry['molecules'][0]
    slot_ids_b = sorted(mol0b['slots'])
    r6_obj = mol0b['slots'][slot_ids_b[0]][0]
    r6_pre = cmd.get('matrix_mode', r6_obj)
    cmd.select('sele', '%s and name CA' % r6_obj)
    wiz2.do_select('sele')         # REAL pick -> _arm_drag sets the guard
    r6_post = cmd.get('matrix_mode', r6_obj)
    r6_sibling = cmd.get('matrix_mode',
                         mol0b['slots'][slot_ids_b[1]][0])
    r6_global = cmd.get('matrix_mode')
    check('Row 6 matrix_mode guard: object-scoped 0 on the freshly '
          'armed object', r6_post == '0' and r6_pre != '0'
          and r6_sibling != '0' and wiz2._current_slot == slot_ids_b[0],
          'matrix_mode(%s)=%r (pre-arm %r) sibling=%r global=%r '
          'slot=%r (probe E1)'
          % (r6_obj, r6_post, r6_pre, r6_sibling, r6_global,
             wiz2._current_slot))

    # ------------------------------------------------------------
    # Row 8 -- NON-AA REFUSAL (RQ6 row 8; design test). The arm guard
    # is wizard-side _objects_by_slot membership BEFORE any arming; the
    # unit-style negative control calls _arm_drag on the ligand object
    # (a name the wizard path never produces).
    # ------------------------------------------------------------
    r8_lig = wiz2._ligand_object
    r8_lig_slot = wiz2._slot_by_object.get(r8_lig)
    r8_drag_pre = cmd.get_drag_object_name()
    r8_err_pre = wiz2._error
    r8_raised = None
    try:
        wiz2._arm_drag(r8_lig)
    except Exception:
        r8_raised = sys.exc_info()[0].__name__
    r8_drag_post = cmd.get_drag_object_name()
    r8_err_post = wiz2._error
    check('Row 8 non-AA refusal: ligand arm attempt is a silent no-op',
          r8_lig_slot is None and r8_raised is None
          and r8_drag_post == r8_drag_pre and r8_drag_post == r6_obj
          and r8_err_post == r8_err_pre,
          'ligand=%r slot_of_ligand=%r drag=%r (want unchanged %r) '
          'error=%r->%r raised=%r (design test)'
          % (r8_lig, r8_lig_slot, r8_drag_post, r8_drag_pre,
             r8_err_pre, r8_err_post, r8_raised))

    # ------------------------------------------------------------
    # Row 9 -- GAME-OVER REFUSAL (RQ6 row 9; the 06-06 soft gate).
    # End the game through the engine path (give_up -- the smoke_15
    # recipe), then script a REAL pick: do_pick's soft gate lands the
    # pinned wording on the panel and returns BEFORE _select_slot /
    # _arm_drag, so no drag is armed and the selection stays unchanged.
    # Deactivate first so "stays ''" is a meaningful read.
    # ------------------------------------------------------------
    cmd.drag()
    r9_drag_before = cmd.get_drag_object_name()
    r9_ret = wiz2.give_up()        # engine path (smoke_15 recipe)
    r9_over = engine.is_over()
    r9_slot_pre = wiz2._current_slot
    r9_obj = mol0b['slots'][slot_ids_b[0]][0]
    cmd.select('sele', '%s and name CA' % r9_obj)
    wiz2.do_select('sele')
    r9_drag = cmd.get_drag_object_name()
    r9_err = wiz2._error
    r9_slot_post = wiz2._current_slot
    check('Row 9 game-over refusal: soft gate fires; no drag armed',
          r9_drag_before == '' and r9_ret is not None and r9_over is True
          and r9_err == 'The game is over.' and r9_drag == ''
          and r9_slot_post == r9_slot_pre,
          'is_over=%r error=%r drag=%r slot=%r->%r ret_keys=%s '
          '(08.3-04 soft short-circuit + 06-06 gate)'
          % (r9_over, r9_err, r9_drag, r9_slot_pre, r9_slot_post,
             None if r9_ret is None else sorted(r9_ret)))

    # ============================================================
    # aamatch-row hygiene tail: delete every selection this battery
    # created (aamatch-private + PyMOL-internal '_drag' shell); the
    # finally pops the wizard and tears game #2 down.
    # ============================================================
    cmd.drag()
    for name in ('sele', 'pk1', '_drag', wizard_mod._DRAG_SELE):
        if name in cmd.get_names('selections'):
            cmd.delete(name)
    rT_strays = [n for n in ('sele', 'pk1', '_drag', wizard_mod._DRAG_SELE)
                 if n in cmd.get_names('selections')]
    rT_stack = cmd.get_wizard_stack()
    rT_types = [type(w).__name__ for w in rT_stack]
    check('RT aamatch-row hygiene: no _drag/_aam_drag_sele/pk1/sele '
          'strays', not rT_strays and cmd.get_drag_object_name() == ''
          and len(rT_stack) == 1 and rT_types == ['GameWizard'],
          'strays=%s drag=%r depth=%d types=%s (as-found for the '
          'finally pop)' % (rT_strays, cmd.get_drag_object_name(),
                            len(rT_stack), rT_types))

except Exception:
    traceback.print_exc()
    check('PART 0/P driver', False, 'raised (see traceback above)')
finally:
    # Teardown (the smoke_23 finally + the probe's cleanup hygiene):
    # pop the game wizard so its cleanup runs, remove every game
    # object and named selection, defensively restore the mouse
    # modes -- the session must end at the pre-game state.
    try:
        cmd.drag()
    except Exception:
        pass
    try:
        cmd.set_wizard()
    except Exception:
        pass
    try:
        placement.cleanup_game_objects()
    except Exception:
        pass
    for name in ('sele', '_drag', 'pk1', wizard_mod._DRAG_SELE):
        try:
            cmd.delete(name)
        except Exception:
            pass
    try:
        cmd.set('button_mode', pre_button_mode, quiet=1)
        cmd.set('mouse_selection_mode', pre_msm, quiet=1)
        cmd.mouse()
    except Exception:
        pass

# --- Teardown verification: zero object leakage ------------------------
leftover = sorted(set(cmd.get_names('objects')) - set(pre_names))
check('TT teardown: zero object leakage (scene == pre-game names)',
      not leftover, 'leftover=%s' % (leftover,))

# --- Check-count assert: every planned row must have run ----------------
# (29 planned checks precede this one: P0 a-d, P1-P6, P5b, PT x2 (=14,
# the 08.3-02 shell) + Rows 1a-1d, 2a-2c, 4a-4b (=9), P0c + Rows 5/6/8/9
# (=5), RT (=1) -- 15 appended by 08.3-12. An exception path inserts the
# unplanned 'driver' row and the count fails loudly -- no planned row
# may be skipped silently.)
PLANNED_CHECKS = 29
check('planned check count (all battery rows ran)',
      len(CHECKS) == PLANNED_CHECKS,
      'ran=%d want=%d (+ this count row)' % (len(CHECKS), PLANNED_CHECKS))

# --- Verdict marker (the SOLE verdict carrier) --------------------------
print('=== SMOKE-24 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
