"""SMOKE-24: drag-movement battery (Phase 8.3 pivot) -- plan 08.3-02.

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
PERMANENTLY as smoke rows before any drag code lands. Later drag plans
extend this file WITHOUT re-deriving the battery design (the roster
number 24 is derived from this basename by run_smoke.sh's sed rule --
no runner edit was needed).

THE PLANNED ROW MAP -- transcribed from the drag research RQ6 table
(08.3-RESEARCH-drag.md sec.2 RQ6; this is the battery's FINAL shape --
NOT all rows are landed yet; row owners per the phase plan list):
  1. Arming contract: after a scripted pick + a wizard=0/edit=0 arm the
     GameWizard stays top-of-stack (identity predicate wizard.py:
     122-133), stack depth unchanged, get_editor_scheme() == 3,
     get_drag_object_name() == <picked obj>, '_drag' atom count ==
     object count, button_mode unchanged (probe C1-C9, 083B) — lands
     08.3-12.
  2. Re-arm law: any script pick clears the armed drag state; a re-arm
     retargets to the newly picked object; a double-arm is idempotent
     (probe 083B(1)(2)(4)) — lands 08.3-12.
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
     law (probe H1, 083B(3)) — lands 08.3-12.
  5. Gesture wiring: cmd.button(<slots>, 'dgmv'/'dgrt'/'dgmz') accepted
     without exception; profile-level restore via button_mode +
     cmd.mouse() works (probe D1/D2) — lands 08.3-12. DISPOSITION
     (2026-10-19, STATE Phase 8.3 Decisions): wired slots =
     cmd.button('left','shft','dgmv') translate +
     cmd.button('left','ctsh','dgmz') depth +
     cmd.button('right','shft','dgrt') drag-rotate (probe D receipted
     left-button slots; the right-slot delivery is an 08.3-04 pin).
  6. matrix_mode guard: object-scoped matrix_mode=0 set/read on the
     game objects at start (probe E1) — lands 08.3-12.
  7. Programmatic drag math (the wizard-side drag_move(dx_px, dy_px)
     helper): world delta == view_camera_to_world(live view,
     (dx*s, dy*s, 0)) with s = (-view[11]) * 2*tan(fov*pi/360) /
     viewport_h; identity clean after every step; per-axis 02-15
     float32 tolerances; view-invariance under the fixed S2/S3 blocks;
     all-atoms-identical displacement (rigidity) (probe 083C + the
     SMOKE-23 PART C/D pattern) — lands 08.3-14.
  8. Non-AA targets never drag: the arm guard refuses ligand/board/user
     objects — wizard-side _objects_by_slot membership before arming
     (design test) — lands 08.3-12.
  9. Game-over gate: drag refused when engine.is_over()
     (_require_playing first — the 06-06 law) — lands 08.3-12.
  10. Deletion battery: direction keys/buttons gone — dated
      EXPECTED-RED bridges (CONTEXT note 3) — lands with the wave-2/3
      deletion plans (08.3-03 roster + 08.3-05..08.3-09 reworks).

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

HONEST SCOPE: this shell pins STOCK PyMOL drag-installing behavior
ONLY — every PART P assertion is about PyMOL's own Dragging-wizard
machinery, NOT aamatch drag code (no aamatch drag implementation
exists at 08.3-02; the aamatch-facing rows are the enumerated future
rows above, landed by 08.3-12 / 08.3-14).

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv
first / cwd fallback (never __file__); import aamatch directly
(module identity 'aamatch' — NEVER the pmg_tk.startup path in the
same session); every print on ONE line and flushed; explicit space
dicts in every iterate (this shell needs NO iterate); no round() in
expressions; no calls to the placement.py banned cmd APIs —
cmd.get_object_matrix IS legal and required (the identity re-assert);
the Part-P selection names are deleted before the final teardown;
zero object leakage pinned; numbered PASS lines with a check-count
assert at the end (a skipped planned row fails the battery loudly).

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


pre_names = list(cmd.get_names('objects'))
pre_button_mode = int(cmd.get('button_mode'))
pre_msm = int(cmd.get('mouse_selection_mode'))
print('SMOKE-ENV pre button_mode=%d msm=%d pre_names=%s'
      % (pre_button_mode, pre_msm, pre_names), flush=True)

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
    for name in ('sele', '_drag', 'pk1'):
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
# (14 planned checks precede this one: P0 a-d, P1-P6, P5b, PT x2, TT;
# an exception path inserts the unplanned 'driver' row and the count
# fails loudly -- no planned row may be skipped silently.)
PLANNED_CHECKS = 14
check('planned check count (all battery rows ran)',
      len(CHECKS) == PLANNED_CHECKS,
      'ran=%d want=%d (+ this count row)' % (len(CHECKS), PLANNED_CHECKS))

# --- Verdict marker (the SOLE verdict carrier) --------------------------
print('=== SMOKE-24 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
