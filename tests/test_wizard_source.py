"""Mechanical source gate for the wizard gameplay loop (plan 03-04).

PLAY-04's no-lines/dots/geometry rule made mechanical: the GameWizard's
ONLY feedback channels are atom RECOLOR (a property change, not
geometry; extract_game_atoms never reads atom color) plus panel/prompt
TEXT via wizard_text. No scene geometry may ever be drawn -- no
measure distance objects, no indicate overlays, no CGO primitives.
``cmd.indicate`` / ``cmd.distance`` / ``cmd.load_cgo`` (the helper-visual
primitives) must have ZERO ast.Call sites in the scanned cmd-tier
sources.

The AST is immune to the Gate-C grep tripwire (test_code_audit.py
precedent): a docstring that SAYS ``cmd.indicate`` is a string
constant, never a Call node, so prose cannot blind-fail this gate --
which is why the docstring below may name the banned primitives
safely. ``find_visual_calls(src)`` is a small pure function so the
NEGATIVE CONTROL (a synthetic source string wired with cmd.indicate +
cmd.distance calls) can prove the finder FIRES -- test_purity.py's
negative-control rule: a gate that cannot fail proves nothing.

Scanned set: aamatch/wizard.py today; new cmd-tier UI modules get
added to ``SCANNED_MODULES`` as they land (03-05 adds gamestart.py).

Also asserted, belt-and-braces with test_code_audit.py's prose pin:
the wizard source carries ZERO mentions of the placement.py banned-
list tokens (get_model / matrix_reset / get_object_ttt) -- unlike
placement.py/engine.py/geometry.py, wizard.py's docstring contract 5
refers to those calls only as "the banned matrix calls" (03-03), so
the count here is zero, not a pinned prose allowance.

Run from repo root:
    python3.6 -m unittest tests.test_wizard_source -v
"""

import ast
import os
import sys
import unittest

# Bootstrap so this suite works both via `unittest discover -s tests` and
# as a directly-executed module (test_purity.py pattern).
_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(_HERE, '..'))
PKG_DIR = os.path.join(REPO_ROOT, 'aamatch')
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# The scanned set grows as cmd-tier UI modules land (03-05 added
# gamestart.py per the 03-03 spawn notes; both scans apply to every
# module in the set).
SCANNED_MODULES = ['wizard.py', 'gamestart.py',
                   'setup_window.py',   # 04-05: Qt setup window
                   'game_window.py',    # 05-06: GameTab shell (Qt tier,
                                        # growth protocol, 03-05/04-05
                                        # precedent)
                   'upload.py']  # quick-003 (2026-10-04): upload.py -- the
                                 # last cmd-tier module missing from any
                                 # registry (pre-verified clean for both
                                 # scans)

# --- quick-003 cmd-tier registration partition (TestCmdTierRegistration) --
# The cmd-tier roster is derived LIVE (listdir of aamatch/*.py minus
# PURE_MODULES minus the exempt composition root) and must be EXACTLY
# partitioned into SCANNED_MODULES u NON_UI_CMD_CORE -- a NEW cmd-tier
# module can never again silently escape both registries (quick-001's
# direction-2 coverage-gate pattern). Today: 28 *.py files = 19
# PURE_MODULES + '__init__' + exactly 8 cmd-tier modules
# [engine, game_window, gamestart, geometry, placement, setup_window,
# upload, wizard] (verified by ls in quick-003 planning).
NON_UI_CMD_CORE = ['engine', 'geometry',
                   'placement']  # deliberately non-UI core; the banned
                                 # matrix-token prose allowances for these
                                 # three are pinned in
                                 # tests/test_code_audit.py's PROSE_PIN
                                 # instead of this gate's zero-mention scan
CMD_TIER_EXEMPT = ['__init__']  # the 01-01 composition root -- the
                                # zero-module-level-imports law gates it
                                # via test_package_skeleton.py; it is
                                # neither a pure module nor a cmd-tier
                                # module to scan

from tests.test_purity import PURE_MODULES  # noqa: E402 -- the lines
# 42-46 bootstrap above inserts REPO_ROOT; tests/__init__.py exists, so
# the suite imports under `python3.6 -m unittest discover -s tests`.


def _derived_cmd_tier():
    """The cmd-tier roster, derived LIVE from the package contents:
    basename of every aamatch/*.py minus the pure modules (gated by
    tests/test_purity.py) minus the exempt composition root (gated by
    tests/test_package_skeleton.py). ANY new module automatically lands
    in this set -- no enrollment step can be forgotten (quick-001
    direction-2 pattern)."""
    return sorted(name[:-3]
                  for name in os.listdir(PKG_DIR)
                  if name.endswith('.py')
                  and name[:-3] not in set(PURE_MODULES)
                  and name[:-3] not in set(CMD_TIER_EXEMPT))


def _registered_cmd_tier():
    """The registered partition: the PLAY-04 scan set plus the
    deliberately non-UI cmd-tier core (whose banned-token prose
    allowances are pinned in tests/test_code_audit.py instead)."""
    return sorted(set(name[:-3] for name in SCANNED_MODULES)
                  | set(NON_UI_CMD_CORE))


# Helper-visual primitives banned by PLAY-04 (no scene geometry ever:
# measurement distance objects, measure-mode overlays, CGO primitives).
BANNED_VISUAL_CALLS = ('indicate', 'distance', 'load_cgo')

# placement.py's BANNED-list tokens -- wizard.py may mention NONE of
# them (contract 5's prose discipline refers to "the banned matrix
# calls" only).
BANNED_MATRIX_TOKENS = ('get_model', 'matrix_reset', 'get_object_ttt')


def _read_source(path):
    """Read a .py file as text, encoding-independent of the locale."""
    with open(path, 'rb') as f:
        return f.read().decode('utf-8')


def find_visual_calls(src, banned=BANNED_VISUAL_CALLS):
    """Every ast.Call in ``src`` whose function is named a banned
    helper-visual primitive (``cmd.indicate(...)`` reports 'indicate').

    Scans ALL call sites in every scope (module level + every function
    body -- ast.walk). Returns one problem string per offender,
    source-line-annotated so a trip names its site. Docstring prose
    cannot appear here (string constants are not Call nodes).
    """
    problems = []
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = None
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        if name in banned:
            problems.append('line %d: CALLS %r (PLAY-04: no helper '
                            'visuals -- recolor + text only)'
                            % (node.lineno, name))
    return problems


# Negative control: a synthetic source wired with exactly one cmd.
# indicate and one cmd.distance call (plus a distance-MENTION in a
# docstring, which must NOT count -- Gate C immunity proven too).
VISUAL_TRAP = '''"""Traps may mention cmd.distance in prose safely."""


def draw(cmd):
    cmd.indicate('sele')
    cmd.distance('sele', 'sele')
    _ = 'load_cgo is only a string here'
'''


def find_confirm_gate_calls(src):
    """Every ast.Call to ``game_state.confirm_passes(...)`` inside the
    GameWizard's confirm impl (the Phase-8.1 pass gate pin).

    Walks ONLY the ``_confirm_molecule_impl`` and ``_confirm_failed``
    function defs of wizard.py and returns one entry per call whose
    attribute name is 'confirm_passes' -- the gate cannot be silently
    removed without a visible test failure. AST again: docstring prose
    can never trip or satisfy this pin.
    """
    hits = []
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in (
                '_confirm_molecule_impl', '_confirm_failed'):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) \
                        and isinstance(sub.func, ast.Attribute) \
                        and sub.func.attr == 'confirm_passes':
                    hits.append('%s line %d' % (node.name, sub.lineno))
    return hits


def _function_def(tree, name):
    """The FunctionDef node named ``name`` anywhere in ``tree``
    (arbitrary nesting OK -- wizard.py's gameplay impls are methods
    of GameWizard), or None."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _const_int(node):
    """The python int of a LITERAL integer constant node: a plain
    ``ast.Num`` (``100``) or a negated one (``-1`` parses as
    UnaryOp(USub, Num) -- there is no negative-literal node type).
    Returns None for anything else (names, calls, float literals) so a
    computed argument can never slip past a literal-argument pin."""
    if isinstance(node, ast.Num) and isinstance(node.n, int) \
            and not isinstance(node.n, bool):
        return node.n
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) \
            and isinstance(node.operand, ast.Num) \
            and isinstance(node.operand.n, int):
        return -node.operand.n
    return None


# --- 08.3-05 keyboard direction channels pinned DELETED --------------------
# 2026-10-18 pivot (recorded disposition 2026-10-19; executed 08.3-03):
# the whole keyboard direction channel is removed from wizard.py --
# do_special (GLUT LEFT/RIGHT nudges), do_key (w/s/q/e camera nudges plus
# ','/'.' view-axis rotates) and the module-level _KEY_NUDGES map are all
# deleted. rotate_keys=delete was an explicit human OVERRIDE of the menu's
# keep default, so the ','/'.' rotate branches die together with do_key
# (the entire channel at once).
#
# The 08.2-03 pins (TestKeyboardChannelMap + its three finders + the frozen
# EXPECTED_SPECIAL_BRANCHES / EXPECTED_KEY_NUDGES maps + their three
# negative controls) existed precisely to make key-map changes loud. The
# pivot IS that loud, recorded change: their subject surfaces no longer
# exist, so the positive pins and controls are removed behind a dated
# bridge (08.3-03-SUMMARY.md roster; never a silent edit) and replaced by
# the DELETION pin below -- wizard.py must define NO do_special and NO
# do_key. K9 shape (08.3-03): outright deletion, no stubs -- the base
# Wizard defaults own the fall-through, so every PyMOL shortcut keeps
# working.

# The surfaces 08.3-03 deleted from wizard.py; re-introduction fails the
# deletion pin loudly.
DELETED_KEYBOARD_CHANNELS = ('do_special', 'do_key')


def find_reintroduced_keyboard_channels(src):
    """Every DELETED keyboard direction channel still defined in ``src``.

    Post-pivot law (2026-10-18 pivot; recorded disposition 2026-10-19;
    executed 08.3-03): do_special and do_key are deleted outright.
    Re-uses the shared ``_function_def`` AST finder, so docstring prose
    that cites the deletion can neither satisfy nor trip this pin (the
    Gate-C-safe idiom used throughout this file)."""
    tree = ast.parse(src)
    return [name for name in DELETED_KEYBOARD_CHANNELS
            if _function_def(tree, name) is not None]


# Negative control: a synthetic source redefining do_special must trip the
# deletion pin (test_purity.py's rule: a gate that cannot fail proves
# nothing).
KEY_CHANNEL_TRAP = '''\
def do_special(self, k, x, y, mod):
    return None
'''


# --- 08.2-03 frozen movement-MODEL discipline pins --------------------------
# ROADMAP 8.2 criterion 3 made mechanical: the Phase-3 movement MODEL
# is frozen, and the frozen discipline inside wizard.py gets WSL-runnable
# AST teeth. M1/M2 baked forms (translate state=1 camera=0; rotate
# selection-form camera=0, NEVER object=), M3 the fail-closed identity
# assert after every move, and the 06-06 law (STATE.md:212):
# _require_playing() is the FIRST line of every gameplay impl.

# The gameplay impls under the gate-order law (06-06). 2026-10-18 pivot
# (recorded disposition 2026-10-19; executed 08.3-03): the camera-frame
# nudge impl (_nudge_cam_impl) was deleted with the keyboard direction
# channel, so this pin shrinks to the four survivors -- the rotate chain
# follows its surviving public wrapper (M4/M5 both survive) and the
# Toward/move_to/reset impls are untouched. No gate weakened: the four
# survivors keep their full first-line + identity-assert teeth.
#
# 2026-10-18 pivot / 08.3-10 surface (2026-10-23, 08.3-13): the drag-move
# impl enumerated + gated per the loud-pin rule -- appended at the end so
# the post-08.3-05 tuple order survives byte-for-byte. Its subject landed
# in 08.3-10 (drag_move(dx_px, dy_px) via wizard_core.drag_world_step);
# the bridge RED that 08.3-10 captured verbatim is consumed by this plan.
GATED_IMPLS = ('_rotate_axis_impl', '_step_to_ligand_impl',
               '_move_to_impl', '_reset_grid_impl', '_drag_move_impl')


def _is_bake_call(node):
    """True for an ast.Call whose function is EXACTLY
    ``cmd.translate(...)`` or ``cmd.rotate(...)`` (the bake
    primitives)."""
    return isinstance(node, ast.Call) \
        and isinstance(node.func, ast.Attribute) \
        and node.func.attr in ('translate', 'rotate') \
        and isinstance(node.func.value, ast.Name) \
        and node.func.value.id == 'cmd'


def find_bake_call_sites(src):
    """Enumerate every cmd.translate / cmd.rotate ast.Call in ``src``
    as sorted (kind, owner) pairs, owner = the innermost enclosing
    FunctionDef name (or '<module>'). Docstring/comment mentions of
    the bake forms cannot appear here -- strings are not Call nodes.
    The self-audit list this returns is pinned against the RESEARCH-
    code map (post-pivot + 08.3-10: two translate sites -- the Toward
    step and the drag-move bake -- plus one rotate site)."""
    sites = []

    def visit(node, owner):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef):
                visit(child, child.name)
                continue
            if _is_bake_call(child):
                sites.append((child.func.attr, owner))
            visit(child, owner)

    visit(ast.parse(src), '<module>')
    return sorted(sites)


# The pinned enumeration (RESEARCH-code.md sec. 2; 2026-10-18 pivot --
# recorded disposition 2026-10-19, executed 08.3-03): the nudge translate
# site died with _nudge_cam_impl, so the survivors are the translate in
# _step_to_ligand_impl plus the rotate in _rotate_axis_impl (M4/M5
# survive). A NEW bake site (e.g. the drag-move impl landing later in
# this phase) fails this pin loudly -- it must be enumerated and gated,
# never sneaked in.
#
# 2026-10-18 pivot / 08.3-10 surface (2026-10-23, 08.3-13): the predicted
# "drag-move impl landing later" DID land -- 08.3-10 added the
# cmd.translate(state=1, camera=0) bake in _drag_move_impl and captured the
# loud enumeration RED verbatim in 08.3-10-SUMMARY.md (dated 2026-10-22).
# This plan consumes that bridge: the site is enumerated here (sorted(...)
# construction kept) and gated via GATED_IMPLS above.
EXPECTED_BAKE_SITES = sorted([('translate', '_step_to_ligand_impl'),
                              ('rotate', '_rotate_axis_impl'),
                              ('translate', '_drag_move_impl')])


def _keyword_const(node, name):
    """The literal int of keyword ``name`` on an ast.Call (None if
    absent or non-literal)."""
    for kw in node.keywords:
        if kw.arg == name:
            return _const_int(kw.value)
    return None


def find_bake_form_violations(src):
    """Every cmd.translate / cmd.rotate call in ``src`` that breaks
    the FROZEN bake forms (wizard.py module docstring contract 5,
    wizard.py:56-72; M1/M2 of the frozen movement MODEL):

    * every ``cmd.translate`` MUST carry ``state=1`` and ``camera=0``
      (Num constants -- baked world-frame coordinates);
    * every ``cmd.rotate`` MUST carry ``camera=0`` and MUST NOT carry
      a keyword named ``object`` (the matrix-only object= form is
      detector-blind -- spike Q2 refuted it);
    * a ``**kwargs`` or non-literal value on any forbidden keyword is
      reported, since the frozen form cannot be verified.

    Docstring prose about the baked forms is immune (strings are not
    Call nodes -- Gate-C-safe, the find_visual_calls idiom).
    """
    problems = []
    for node in ast.walk(ast.parse(src)):
        if not _is_bake_call(node):
            continue
        kind = node.func.attr
        if any(kw.arg is None for kw in node.keywords):
            problems.append(
                'line %d: cmd.%s carries **kwargs -- the frozen '
                'keywords cannot be verified; spell state=/camera= '
                'literally' % (node.lineno, kind))
        if kind == 'translate':
            if _keyword_const(node, 'state') != 1:
                problems.append(
                    'line %d: cmd.translate without state=1 -- M1 '
                    'bakes STORED coordinates only via state=1 '
                    '(contract 5, wizard.py:56-72)' % (node.lineno,))
            if _keyword_const(node, 'camera') != 0:
                problems.append(
                    'line %d: cmd.translate without camera=0 -- a '
                    'camera=1 bake is a RELATIVE move, not the frozen '
                    'world-frame form (contract 5)' % (node.lineno,))
        else:  # rotate
            if _keyword_const(node, 'camera') != 0:
                problems.append(
                    'line %d: cmd.rotate without camera=0 -- M2 is '
                    'the SELECTION form with camera=0 (spike Q1 '
                    'CONFIRMED bake; contract 5)' % (node.lineno,))
            for kw in node.keywords:
                if kw.arg == 'object':
                    problems.append(
                        'line %d: cmd.rotate carries object= -- the '
                        'matrix-only object= form is detector-blind '
                        '(spike Q2 REFUTED); selection= is the '
                        'frozen form' % (node.lineno,))
    return problems


def find_gate_discipline_violations(src):
    """Every gated gameplay impl that breaks the 06-06 gate order.

    Frozen law (STATE.md:212, the _require_playing docstring
    wizard.py:655-666): for each impl in GATED_IMPLS the FIRST
    gameplay statement must be ``self._require_playing()`` (leading
    relative lazy imports -- ``from . import engine`` -- are module-
    scope-hygiene boilerplate with zero gameplay effect and are
    skipped; every other statement kind must wait behind the gate),
    and the body must contain at least one ``self._assert_identity``
    call (M3, the fail-closed PLAY-02 identity invariant)."""
    problems = []
    tree = ast.parse(src)
    for name in GATED_IMPLS:
        fn = _function_def(tree, name)
        if fn is None:
            problems.append('%s: impl NOT FOUND -- a gated gameplay '
                            'op is missing from wizard.py' % (name,))
            continue
        body = list(fn.body)
        i = 0
        while i < len(body) and isinstance(body[i], ast.ImportFrom) \
                and body[i].level:
            i += 1
        gate_ok = i < len(body) and isinstance(body[i], ast.Expr) \
            and isinstance(body[i].value, ast.Call) \
            and isinstance(body[i].value.func, ast.Attribute) \
            and body[i].value.func.attr == '_require_playing' \
            and isinstance(body[i].value.func.value, ast.Name) \
            and body[i].value.func.value.id == 'self'
        if not gate_ok:
            problems.append(
                '%s (line %d): first gameplay statement is NOT '
                'self._require_playing() -- the 06-06 law: the '
                'game-over gate is the FIRST line of every gameplay '
                'impl (STATE.md:212); after give_up/complete_game '
                'the wizard must stay inert' % (name, fn.lineno))
        assert_ok = any(
            isinstance(sub, ast.Call)
            and isinstance(sub.func, ast.Attribute)
            and sub.func.attr == '_assert_identity'
            and isinstance(sub.func.value, ast.Name)
            and sub.func.value.id == 'self'
            for sub in ast.walk(fn))
        if not assert_ok:
            problems.append(
                '%s (line %d): no self._assert_identity(...) call '
                '-- M3: every move must re-prove the object matrix '
                'is identity, fail-closed (on-screen == stored == '
                'detected by construction, PLAY-02)'
                % (name, fn.lineno))
    return problems


# Negative-control traps for the discipline finders. 2026-10-18 pivot
# (executed 08.3-03): the trap owner names were re-pointed off the deleted
# nudge impl onto surviving impls -- the trap BODIES are otherwise
# unchanged, so the four controls keep their full mutation-proof teeth.
BAKE_TRAP_CAMERA = '''\
def _step_to_ligand_impl(self):
    cmd.translate([0.0, 0.0, 0.0], 'obj', state=1, camera=1)
'''

BAKE_TRAP_OBJECT = '''\
def _rotate_axis_impl(self, axis, deg, origin):
    cmd.rotate([1.0, 0.0, 0.0], 90.0, camera=0, object='aa1')
'''

# Only the gated impls matter to the gate finder; the trap wires ONE
# surviving impl with a non-gate first statement (a different call).
# 2026-10-23 (08.3-13): the traps gain a CONFORMANT _drag_move_impl stub
# so each control still isolates exactly the one violation it names (an
# absent impl would also report "impl NOT FOUND" noise); the traps'
# mutation-proof teeth are unchanged.
GATE_TRAP_FIRST = '''\
def _rotate_axis_impl(self, axis, deg, origin):
    self._current_object()
    self._assert_identity('obj')

def _step_to_ligand_impl(self):
    self._require_playing()
    self._assert_identity('obj')

def _move_to_impl(self, position):
    self._require_playing()
    self._assert_identity('obj')

def _reset_grid_impl(self):
    from . import engine
    self._require_playing()
    self._assert_identity('obj')

def _drag_move_impl(self, dx_px, dy_px):
    self._require_playing()
    self._assert_identity('obj')
'''

# Same shape but _reset_grid_impl drops the identity assert.
GATE_TRAP_ASSERT = '''\
def _rotate_axis_impl(self, axis, deg, origin):
    self._require_playing()
    self._assert_identity('obj')

def _step_to_ligand_impl(self):
    self._require_playing()
    self._assert_identity('obj')

def _move_to_impl(self, position):
    self._require_playing()
    self._assert_identity('obj')

def _reset_grid_impl(self):
    from . import engine
    self._require_playing()

def _drag_move_impl(self, dx_px, dy_px):
    self._require_playing()
    self._assert_identity('obj')
'''


# --- 08.3-13 drag-mechanism ORDERING pins -----------------------------------
# ROADMAP 8.3 criterion 2's "pinned changes are loud" rule, drag half. The
# ordering laws are probe-proven in 08.3-RESEARCH-drag.md RQ2 (items 1/5/7)
# and get AST teeth here equal to the 08.2-03 keyboard pins: the phase's own
# NEW surfaces can no longer be silently broken any more than the old ones
# could. The laws, and why each one is load-bearing:
#
#   (a) ARM SELECTION-FORM -- _arm_drag arms cmd.drag(_DRAG_SELE, wizard=0,
#       edit=0). wizard=0 avoids the Dragging-wizard install, edit=0 skips
#       the button-profile switch (editing.py:1061-1074; probes C2/C3/C8/C9
#       -- GameWizard stays top-of-stack and keeps receiving picks). The
#       target MUST be the private SELECTION name: an OBJECT-name arm takes
#       ExecutiveSetDrag's object branch -> ObjectCombineTTT (object MATRIX,
#       detector-blind, identity-breaking -- Executive.cpp:3208-3259,
#       Pitfall-6c). Recorded disposition (2026-10-19) is gesture=a, so the
#       wizard=0/edit=0 form is the pin; a future gesture=c disposition
#       evolves EXPECTED_ARM_KWARGS loudly (never a silent edit).
#   (b) ARM LAST IN do_pick -- ANY pick clears the armed drag state (probe
#       083B(1)(2)), so every successful pick re-arms as its LAST statement.
#       It MUST stay last: the arm's cmd.drag runs EditorInactivate, which
#       deletes pk1..pk4 (Editor.cpp:1701-1740) -- arming before the pk1
#       read swallows the pick (RQ2 item 5).
#   (c) SNAPSHOT AFTER PUSH -- activate() runs cmd.set_wizard FIRST, then
#       snapshots msm, then button_mode, then wires cmd.button. The push
#       can pop a prior GameWizard whose cleanup restores the user's TRUE
#       values inside set_wizard; snapshotting first would record a stale
#       value (the msm-order-law analog, wizard.py contract 4; the stock
#       Dragging wizard's own dragging.py:78-80 precedent, RQ2 item 7).
#   (d) CLEANUP RESTORES THE DRAG STATE -- cleanup deactivates the C drag,
#       deletes the private selection, then restores the recorded
#       button_mode profile via cmd.set + cmd.mouse() (probes H1/083B(3),
#       D2). Without the dearm the C-side drag stays armed past the wizard.

# The recorded 2026-10-19 disposition is gesture=a (Option A shift-left
# 'dgmv'): the arm is the custom-wiring form. wizard=1 is ONLY the
# gesture=c (stock sandwich) record -- evolving this map is a loud change.
EXPECTED_ARM_KWARGS = {'wizard': 0, 'edit': 0}

# The private drag-selection constant's NAME as it appears in wizard.py's
# AST (module-level ``_DRAG_SELE = '_aam_drag_sele'``).
DRAG_SELECTION_AST_NAME = '_DRAG_SELE'


def _const_str(node):
    """The python str of a LITERAL string constant node, else None."""
    if isinstance(node, ast.Str):
        return node.s
    return None


def _method_call(node, method):
    """True for an ast.Call spelled ``cmd.<method>(...)`` OR
    ``self.cmd.<method>(...)`` -- wizard.py uses both spellings
    (module-level cmd in the helpers, self.cmd in cleanup's
    rebound-session guard)."""
    if not isinstance(node, ast.Call) \
            or not isinstance(node.func, ast.Attribute) \
            or node.func.attr != method:
        return False
    base = node.func.value
    if isinstance(base, ast.Name) and base.id == 'cmd':
        return True
    return (isinstance(base, ast.Attribute) and base.attr == 'cmd'
            and isinstance(base.value, ast.Name)
            and base.value.id == 'self')


def _calls_of(fn, method):
    """Every ast.Call in ``fn`` matching ``_method_call(method)``,
    source order."""
    return sorted((n for n in ast.walk(fn)
                   if _method_call(n, method)),
                  key=lambda n: n.lineno)


def _self_attr_assignments(fn, attr):
    """Sorted linenos of every assignment to ``self.<attr> = ...``
    anywhere in ``fn`` (the snapshot writes)."""
    out = []
    for sub in ast.walk(fn):
        targets = []
        if isinstance(sub, ast.Assign):
            targets = sub.targets
        elif isinstance(sub, ast.AnnAssign) and sub.value is not None:
            targets = [sub.target]
        for tgt in targets:
            if isinstance(tgt, ast.Attribute) and tgt.attr == attr \
                    and isinstance(tgt.value, ast.Name) \
                    and tgt.value.id == 'self':
                out.append(sub.lineno)
    return sorted(out)


def find_arm_selection_form_violations(src):
    """Every _arm_drag arm call that breaks law (a).

    The cmd.drag call inside ``_arm_drag`` MUST carry the literal
    keywords wizard=0 and edit=0 (EXPECTED_ARM_KWARGS -- the recorded
    gesture=a disposition) and its FIRST positional MUST reference the
    private selection constant (``_DRAG_SELE``); the object-name arm is
    the FORBIDDEN object-MATRIX path. Prose cannot satisfy or trip this
    pin (strings are not Call nodes -- Gate-C-safe)."""
    problems = []
    fn = _function_def(ast.parse(src), '_arm_drag')
    if fn is None:
        return ['_arm_drag: NOT FOUND -- the drag arm helper is missing '
                'from wizard.py; nothing can carry the selection-form '
                'arm law']
    drags = _calls_of(fn, 'drag')
    if not drags:
        return ['_arm_drag: no cmd.drag(...) call -- the selection-form '
                'arm IS the mechanism this pin guards (RQ2 item 1)']
    for call in drags:
        for kwarg in sorted(EXPECTED_ARM_KWARGS):
            expected = EXPECTED_ARM_KWARGS[kwarg]
            if _keyword_const(call, kwarg) != expected:
                problems.append(
                    'line %d: cmd.drag without %s=%d -- the recorded '
                    'gesture=a disposition arms via the custom-wiring '
                    'form (RQ2 item 1, probes C2/C3/C8/C9); %s=1 '
                    'installs the Dragging wizard over GameWizard / '
                    'switches the button profile'
                    % (call.lineno, kwarg, expected, kwarg))
        if not call.args:
            problems.append(
                'line %d: cmd.drag has NO positional arm target -- the '
                'private selection %s is the only legal target'
                % (call.lineno, DRAG_SELECTION_AST_NAME))
            continue
        first = call.args[0]
        names = set(sub.id for sub in ast.walk(first)
                    if isinstance(sub, ast.Name))
        if DRAG_SELECTION_AST_NAME not in names:
            problems.append(
                'line %d: the arm target is not %s -- an OBJECT-name '
                'arm takes the FORBIDDEN object-MATRIX path '
                '(ExecutiveSetDrag -> ObjectCombineTTT, '
                'Executive.cpp:3208-3259, Pitfall-6c); only the '
                'SELECTION form bakes coordinates'
                % (call.lineno, DRAG_SELECTION_AST_NAME))
    return problems


def find_arm_last_violations(src):
    """Every do_pick re-arm that breaks law (b).

    do_pick's LAST top-level statement must be ``self._arm_drag(...)``,
    and NO earlier statement may arm: any pick clears the armed drag
    state (probe 083B(1)(2)), while the arm itself runs EditorInactivate
    -- which deletes pk1..pk4 (Editor.cpp:1701-1740) -- so arming before
    the pk1 read eats the pick (RQ2 item 5). Being last also places the
    arm after the ``_select_slot`` call."""
    problems = []
    fn = _function_def(ast.parse(src), 'do_pick')
    if fn is None:
        return ['do_pick: NOT FOUND -- the pick handler owning the re-arm '
                'tail is missing']
    body = list(fn.body)
    if not body:
        return ['do_pick: empty body -- the re-arm tail is missing']

    def _arm_calls(stmt):
        return [sub for sub in ast.walk(stmt)
                if isinstance(sub, ast.Call)
                and isinstance(sub.func, ast.Attribute)
                and sub.func.attr == '_arm_drag'
                and isinstance(sub.func.value, ast.Name)
                and sub.func.value.id == 'self']

    last = body[-1]
    last_is_arm = (isinstance(last, ast.Expr)
                   and isinstance(last.value, ast.Call)
                   and isinstance(last.value.func, ast.Attribute)
                   and last.value.func.attr == '_arm_drag'
                   and isinstance(last.value.func.value, ast.Name)
                   and last.value.func.value.id == 'self')
    if not last_is_arm:
        problems.append(
            'do_pick: self._arm_drag(...) is NOT the LAST statement -- '
            'ANY pick clears the armed drag state (probe 083B(1)(2)) '
            'and the arm runs EditorInactivate, which deletes '
            'pk1..pk4 (Editor.cpp:1701-1740): arming before the pk1 '
            'read swallows the pick (RQ2 item 5)')
    for stmt in body[:-1]:
        for call in _arm_calls(stmt):
            problems.append(
                'line %d: self._arm_drag is called BEFORE the tail -- '
                'the re-arm MUST stay last in do_pick (EditorInactivate '
                'deletes the pk1 pick buffer)' % (call.lineno,))
    return problems


def find_snapshot_order_violations(src):
    """Every activate() enter sequence that breaks law (c).

    Binding order: the ``cmd.set_wizard`` push FIRST, then the
    ``self._saved_msm`` snapshot, then the ``self._saved_button_mode``
    snapshot, then the ``cmd.button`` gesture wiring. The push can pop a
    prior GameWizard whose cleanup restores the user's TRUE values
    INSIDE set_wizard; snapshotting before the push records a stale
    value (the msm-order-law analog -- wizard.py contract 4; stock
    Dragging precedent dragging.py:78-80, RQ2 item 7)."""
    problems = []
    fn = _function_def(ast.parse(src), 'activate')
    if fn is None:
        return ['activate: NOT FOUND -- the enter sequence is missing']
    push = [call.lineno for call in _calls_of(fn, 'set_wizard')]
    msm = _self_attr_assignments(fn, '_saved_msm')
    bmode = _self_attr_assignments(fn, '_saved_button_mode')
    wires = [call.lineno for call in _calls_of(fn, 'button')]
    for label, rows in (
            ('cmd.set_wizard(...) push', push),
            ('self._saved_msm snapshot', msm),
            ('self._saved_button_mode snapshot', bmode),
            ('cmd.button(...) gesture wiring', wires)):
        if not rows:
            problems.append(
                'activate: missing %s -- the binding enter sequence is '
                'push -> msm snapshot -> button_mode snapshot -> gesture '
                'wiring' % (label,))
    if problems:
        return problems
    if not push[0] < msm[0] < bmode[0]:
        problems.append(
            'activate: snapshot order broken (push line %d, msm line %d, '
            'button_mode line %d) -- push BEFORE snapshot (wizard.py '
            'contract 4): a popped GameWizard restores the user\'s true '
            'button_mode INSIDE set_wizard, so snapshotting first records '
            'a stale value (the msm-order-law analog, dragging.py:78-80)'
            % (push[0], msm[0], bmode[0]))
    early_wiring = [ln for ln in wires if ln < bmode[0]]
    if early_wiring:
        problems.append(
            'activate line %d: cmd.button gesture wiring runs BEFORE the '
            'button_mode snapshot -- the pre-game profile would be '
            'overwritten before it is recorded' % (early_wiring[0],))
    return problems


def find_cleanup_restore_violations(src):
    """Every cleanup() restore set that breaks law (d).

    cleanup MUST contain, in order: a BARE ``cmd.drag()`` deactivation
    (no args -- that is what disarms the C-side drag, probe H1/083B(3)),
    the private selection's delete (``cmd.delete(_DRAG_SELE)``), and the
    profile-level button_mode restore (``cmd.set('button_mode', ...)``
    followed by ``cmd.mouse()``, probe D2)."""
    problems = []
    fn = _function_def(ast.parse(src), 'cleanup')
    if fn is None:
        return ['cleanup: NOT FOUND -- the PLAY-04 restore set is missing']
    dearm = [call.lineno for call in _calls_of(fn, 'drag')
             if not call.args and not call.keywords]
    drag_delete = [
        call.lineno for call in _calls_of(fn, 'delete')
        if call.args
        and DRAG_SELECTION_AST_NAME in set(
            sub.id for sub in ast.walk(call.args[0])
            if isinstance(sub, ast.Name))]
    mode_set = [
        call.lineno for call in _calls_of(fn, 'set')
        if call.args and _const_str(call.args[0]) == 'button_mode']
    mouse = [call.lineno for call in _calls_of(fn, 'mouse')]
    for label, rows in (
            ('bare cmd.drag() deactivation', dearm),
            ('cmd.delete(%s) private-selection cleanup'
             % DRAG_SELECTION_AST_NAME, drag_delete),
            ("cmd.set('button_mode', ...) restore", mode_set),
            ('cmd.mouse() profile re-apply', mouse)):
        if not rows:
            problems.append(
                'cleanup: missing %s -- the PLAY-04 restore set must '
                'deactivate the drag, delete the private selection, and '
                'restore button_mode (probes H1/083B(3), D2)' % (label,))
    if problems:
        return problems
    if not dearm[0] < drag_delete[0]:
        problems.append(
            'cleanup: the drag deactivation (line %d) must precede the '
            'selection delete (line %d) -- disarm first, then remove '
            'the target' % (dearm[0], drag_delete[0]))
    if not dearm[0] < mode_set[0] < mouse[0]:
        problems.append(
            'cleanup: button_mode restore order broken (dearm %d, set %d, '
            'mouse %d) -- deactivate the drag, then cmd.set('
            "'button_mode', saved) + cmd.mouse() (probe D2)"
            % (dearm[0], mode_set[0], mouse[0]))
    return problems


# Negative-control traps for the four ordering finders (08.2-03 house
# pattern: each trap is a module-level source string; each test asserts
# the finder FIRES and names its law -- a gate that cannot fail proves
# nothing).
ARM_TRAP_OBJECT_NAME = '''\
def _arm_drag(self, obj):
    cmd.select(_DRAG_SELE, obj)
    cmd.drag(obj, wizard=0, edit=0)
'''

ARM_TRAP_WIZARD_ONE = '''\
def _arm_drag(self, obj):
    cmd.select(_DRAG_SELE, obj)
    cmd.drag(_DRAG_SELE, wizard=1, edit=0)
'''

ARM_LAST_TRAP = '''\
def do_pick(self, bondFlag):
    self._arm_drag('aa1')
    rows = []
    cmd.iterate('pk1', 'stored.append((model, ID, alt, resv))',
                space={'stored': rows})
'''

SNAPSHOT_TRAP = '''\
def activate(self, replace=0):
    self._saved_button_mode = int(cmd.get('button_mode'))
    cmd.deselect()
    cmd.set_wizard(self, replace=replace)
    self._saved_msm = int(cmd.get('mouse_selection_mode'))
    cmd.set('mouse_selection_mode', 0)
    cmd.button('left', 'shft', 'dgmv')
'''

CLEANUP_TRAP = '''\
def cleanup(self):
    if self._saved_msm is not None:
        self.cmd.set('mouse_selection_mode', self._saved_msm)
    if _DRAG_SELE in self.cmd.get_names('selections'):
        self.cmd.delete(_DRAG_SELE)
    if self._saved_button_mode is not None:
        self.cmd.set('button_mode', str(self._saved_button_mode), quiet=1)
        self.cmd.mouse()
'''


class TestConfirmPassGatePresent(unittest.TestCase):
    """Phase 8.1: the pass gate sits in the ONE confirm impl."""

    def test_confirm_impl_calls_game_state_confirm_passes(self):
        hits = find_confirm_gate_calls(
            _read_source(os.path.join(PKG_DIR, 'wizard.py')))
        self.assertTrue(
            hits,
            'the Confirm pass gate (game_state.confirm_passes) MUST '
            'sit in wizard.py\'s confirm impl -- without it a blind '
            'Confirm records and advances again (the Phase-6 semantics '
            'defect Phase 8.1 restored)')

    def test_negative_control_finder_scoped(self):
        # The finder must NOT fire on unrelated scopes: a call to
        # confirm_passes outside the confirm impls is ignored.
        src = ('def other():\n'
               '    thing.confirm_passes(1, 2)\n')
        self.assertEqual(find_confirm_gate_calls(src), [])


class TestNoHelperVisualCalls(unittest.TestCase):
    """The scanned cmd-tier sources draw ZERO scene geometry."""

    def test_no_helper_visual_call_sites(self):
        offenders = []
        for name in SCANNED_MODULES:
            offenders.extend(
                '%s: %s' % (name, problem)
                for problem in find_visual_calls(
                    _read_source(os.path.join(PKG_DIR, name))))
        self.assertEqual(
            offenders, [],
            'PLAY-04 bans helper visuals (lines/dots/CGO): the wizard '
            'gives feedback by atom RECOLOR + panel/prompt TEXT only. '
            'Found call sites:\n  ' + '\n  '.join(offenders))

    def test_negative_control_finder_fires(self):
        problems = find_visual_calls(VISUAL_TRAP)
        self.assertEqual(
            len(problems), 2,
            'the finder must flag exactly the 2 synthetic cmd.indicate '
            '+ cmd.distance calls (the docstring/string-constant '
            'mentions must NOT count), got %r' % (problems,))

    def test_no_banned_matrix_token_mentions(self):
        problems = []
        for name in SCANNED_MODULES:
            src = _read_source(os.path.join(PKG_DIR, name))
            for token in BANNED_MATRIX_TOKENS:
                if token in src:
                    problems.append(
                        '%s: unwhitelisted %r mention -- wizard.py\'s '
                        'docstring contract 5 refers to the placement '
                        'banned list only as "the banned matrix calls" '
                        '(count pin: zero)' % (name, token))
        self.assertEqual(problems, [],
                         'banned-token drift:\n  ' + '\n  '.join(problems))


class TestCmdTierRegistration(unittest.TestCase):
    """quick-003: every cmd-tier module sits in EXACTLY ONE registry.

    The derived roster (aamatch/*.py - PURE_MODULES - __init__) is
    today exactly [engine, game_window, gamestart, geometry, placement,
    setup_window, upload, wizard] (8 = 28 files - 19 PURE_MODULES -
    the exempt composition root). The partition into SCANNED_MODULES u
    NON_UI_CMD_CORE must cover it with no remainder and no overlap, so
    a NEW cmd-tier module fails HERE -- loudly and by name -- instead
    of silently escaping every source gate (upload.py's quick-003
    discovery was exactly that silent escape).
    """

    def test_every_cmd_tier_module_is_registered(self):
        unregistered = sorted(set(_derived_cmd_tier())
                              - set(_registered_cmd_tier()))
        self.assertEqual(
            unregistered, [],
            'cmd-tier module(s) outside EVERY registry: %r -- a new '
            'cmd-tier module must register: a new UI module goes into '
            'SCANNED_MODULES (the PLAY-04 scans); a new deliberately '
            'non-UI core module goes into NON_UI_CMD_CORE; never both'
            % unregistered)

    def test_registered_modules_all_exist(self):
        missing = sorted(name for name in _registered_cmd_tier()
                         if not os.path.isfile(
                             os.path.join(PKG_DIR, name + '.py')))
        self.assertEqual(
            missing, [],
            'registry rot: registered module(s) missing from aamatch/: '
            '%r -- a rename/delete must update the registry WITH the '
            'file, not leave a phantom gate entry' % missing)

    def test_no_registry_overlap(self):
        overlap = sorted(set(name[:-3] for name in SCANNED_MODULES)
                         & set(NON_UI_CMD_CORE))
        self.assertEqual(
            overlap, [],
            'SCANNED_MODULES and NON_UI_CMD_CORE must be DISJOINT '
            '(a module is scanned for banned tokens via this gate XOR '
            'via test_code_audit.py\'s PROSE_PIN -- never both): %r'
            % overlap)


class TestKeyboardChannelDeleted(unittest.TestCase):
    """08.3-05: the deleted keyboard direction channels are AST-pinned
    ABSENT (the post-pivot evolution of the 08.2-03 TestKeyboardChannelMap
    pins; ROADMAP 8.2 criterion-3 teeth re-pointed, not dropped).

    2026-10-18 pivot (recorded disposition 2026-10-19; executed 08.3-03):
    do_special (GLUT LEFT/RIGHT nudges) and do_key (w/s/q/e camera nudges
    plus ','/'.' view-axis rotates) are DELETED outright from wizard.py
    (rotate_keys=delete was an explicit human override of the keep
    default, so the whole channel dies at once). The positive 08.2-03
    key-map pins, finders and controls were removed behind a dated bridge
    (their subject surfaces no longer exist); this negative pin takes
    their place -- the base Wizard defaults own the fall-through (K9
    shape: deletion, no stubs, 08.3-03), so every PyMOL shortcut keeps
    working and the direction channel cannot silently return. wizard.py
    is SCANNED, never imported -- a pure AST pin over the source text.
    """

    def test_deleted_keyboard_channels_absent(self):
        offenders = find_reintroduced_keyboard_channels(
            _read_source(os.path.join(PKG_DIR, 'wizard.py')))
        self.assertEqual(
            offenders, [],
            'the keyboard direction channels are DELETED (2026-10-18 '
            'pivot; rotate_keys=delete): wizard.py must define NO '
            'do_special and NO do_key -- the base Wizard defaults own '
            'the fall-through. Re-introduced: %r' % (offenders,))

    def test_negative_control_reintroduced_channel_fires(self):
        offenders = find_reintroduced_keyboard_channels(KEY_CHANNEL_TRAP)
        self.assertIn(
            'do_special', offenders,
            'a redefined do_special MUST trip the deletion pin -- the '
            'direction channel was removed outright, not stubbed. '
            'Got %r' % (offenders,))


class TestMovementDisciplineSource(unittest.TestCase):
    """08.2-03: the frozen Phase-3 movement MODEL inside wizard.py is
    AST-pinned (ROADMAP 8.2 criterion 3 made mechanical).

    RESEARCH-code.md sec. 2 is the claim map; wizard.py module
    docstring contract 5 (wizard.py:56-72) states the same laws:
    M1 -- every cmd.translate carries state=1 camera=0 (baked stored
    coords); M2 -- every cmd.rotate is the SELECTION form with
    camera=0 and NEVER object= (the matrix-only object= form is
    detector-blind, spike Q2 refuted); M3 -- every gameplay impl
    re-asserts identity fail-closed (on-screen == stored == detected
    by construction, PLAY-02); the 06-06 law (STATE.md:212) --
    self._require_playing() is the FIRST line of every gameplay impl
    (only leading relative lazy imports, ``from . import ...``, may
    precede it -- module-scope hygiene with zero gameplay effect;
    wizard.py:1039-1041 _reset_grid_impl is the living example).
    """

    def test_bake_call_site_enumeration_exact(self):
        # Self-audit of ALL cmd.translate / cmd.rotate call sites:
        # two translate sites + one rotate site (the nudge translate
        # died with _nudge_cam_impl, 08.3-03; the drag-move translate
        # landed 08.3-10 and is enumerated by 08.3-13 behind its
        # captured RED); a NEW bake site must be enumerated here and
        # gated, never sneaked in.
        sites = find_bake_call_sites(
            _read_source(os.path.join(PKG_DIR, 'wizard.py')))
        self.assertEqual(
            sites, EXPECTED_BAKE_SITES,
            'the bake-call enumeration drifted from the frozen map '
            '(translate: _step_to_ligand_impl + _drag_move_impl; '
            'rotate: _rotate_axis_impl), got %r' % (sites,))

    def test_bake_forms_exact(self):
        problems = find_bake_form_violations(
            _read_source(os.path.join(PKG_DIR, 'wizard.py')))
        self.assertEqual(
            problems, [],
            'every bake call must carry the frozen keywords '
            '(translate state=1 camera=0; rotate camera=0, no '
            'object=):\n  ' + '\n  '.join(problems))

    def test_gate_discipline_exact(self):
        problems = find_gate_discipline_violations(
            _read_source(os.path.join(PKG_DIR, 'wizard.py')))
        self.assertEqual(
            problems, [],
            'every gated impl must open with self._require_playing() '
            '(06-06) and contain self._assert_identity (M3):\n  '
            + '\n  '.join(problems))

    def test_negative_control_camera_one_translate(self):
        problems = find_bake_form_violations(BAKE_TRAP_CAMERA)
        self.assertTrue(
            problems,
            'a camera=1 translate MUST trip the pin -- the frozen '
            'bake form is camera=0 (world-frame stored coords)')
        self.assertTrue(any('camera=0' in p for p in problems),
                        'the trip must name the camera=0 law, got %r'
                        % (problems,))

    def test_negative_control_object_keyword_rotate(self):
        problems = find_bake_form_violations(BAKE_TRAP_OBJECT)
        self.assertTrue(
            problems,
            'an object=-keyword rotate MUST trip the pin -- the '
            'matrix-only form is detector-blind (spike Q2)')
        self.assertTrue(any('object=' in p for p in problems),
                        'the trip must name the object= ban, got %r'
                        % (problems,))

    def test_negative_control_first_statement_not_gate(self):
        problems = find_gate_discipline_violations(GATE_TRAP_FIRST)
        self.assertTrue(
            problems,
            'an impl whose first gameplay statement is not '
            '_require_playing() MUST trip the pin (the 06-06 '
            'first-line law, STATE.md:212)')
        self.assertTrue(
            any('_rotate_axis_impl' in p and '_require_playing' in p
                for p in problems),
            'the trip must name the offending impl, got %r'
            % (problems,))

    def test_negative_control_missing_identity_assert(self):
        problems = find_gate_discipline_violations(GATE_TRAP_ASSERT)
        self.assertTrue(
            problems,
            'an impl without self._assert_identity MUST trip the pin '
            '(M3 -- identity re-proven after every move)')
        self.assertTrue(
            any('_reset_grid_impl' in p and '_assert_identity' in p
                for p in problems),
            'the trip must name the impl missing M3, got %r'
            % (problems,))


class TestDragMechanismSource(unittest.TestCase):
    """08.3-13: the drag mechanism's ORDERING laws are AST-enforced.

    The 08.2-03 keyboard pins made the movement-MODEL changes loud; this
    class gives the phase's NEW drag surfaces the same teeth (ROADMAP 8.3
    criterion 2: the standing-gate clause is bidirectional -- the phase
    deleted pins AND grew new ones, both on the record). Four laws, each
    probe-proven in 08.3-RESEARCH-drag.md RQ2 and each with a trap source
    that MUST trip its finder (test_purity.py's negative-control rule):

    (a) arm selection-form -- ``_arm_drag`` arms
        ``cmd.drag(_DRAG_SELE, wizard=0, edit=0)``: no Dragging-wizard
        install, no profile switch, SELECTION form (never the
        object-MATRIX path); the recorded disposition is gesture=a.
    (b) arm LAST in do_pick -- the re-arm tail stays after all other
        do_pick work (any pick clears the arm; EditorInactivate deletes
        pk1..pk4, so arming before the read would eat the pick).
    (c) snapshot order in activate -- push, then msm snapshot, then
        button_mode snapshot, then the cmd.button wiring (the
        msm-order-law analog; dragging.py:78-80 precedent).
    (d) cleanup restores the drag state -- bare ``cmd.drag()`` dearm,
        private-selection delete, then the button_mode restore via
        ``cmd.set`` + ``cmd.mouse()``.
    """

    def _wizard_src(self):
        return _read_source(os.path.join(PKG_DIR, 'wizard.py'))

    def test_arm_selection_form_exact(self):
        problems = find_arm_selection_form_violations(self._wizard_src())
        self.assertEqual(
            problems, [],
            'the arm must stay the SELECTION form with wizard=0/edit=0 '
            '(gesture=a disposition; RQ2 item 1):\n  '
            + '\n  '.join(problems))

    def test_negative_control_arm_object_name_fires(self):
        problems = find_arm_selection_form_violations(
            ARM_TRAP_OBJECT_NAME)
        self.assertTrue(
            problems,
            'an OBJECT-name arm MUST trip the pin -- it takes the '
            'FORBIDDEN object-MATRIX path (Pitfall-6c)')
        self.assertTrue(
            any('object-MATRIX' in p for p in problems),
            'the trip must name the FORBIDDEN object-MATRIX path, got %r'
            % (problems,))

    def test_negative_control_arm_wizard_one_fires(self):
        problems = find_arm_selection_form_violations(
            ARM_TRAP_WIZARD_ONE)
        self.assertTrue(
            problems,
            'wizard=1 MUST trip the pin -- it installs the Dragging '
            'wizard over GameWizard (probe B1/B2)')
        self.assertTrue(
            any('wizard=0' in p for p in problems),
            'the trip must name the wizard=0 law, got %r' % (problems,))

    def test_arm_last_in_do_pick_exact(self):
        problems = find_arm_last_violations(self._wizard_src())
        self.assertEqual(
            problems, [],
            'every successful pick MUST re-arm as do_pick\'s LAST '
            'statement (RQ2 item 5):\n  ' + '\n  '.join(problems))

    def test_negative_control_arm_before_pk1_read_fires(self):
        problems = find_arm_last_violations(ARM_LAST_TRAP)
        self.assertTrue(
            problems,
            'an _arm_drag call BEFORE the pk1 iterate MUST trip the pin '
            '-- the arm deletes pk1..pk4 (Editor.cpp:1701-1740)')
        self.assertTrue(
            any('NOT the LAST statement' in p for p in problems),
            'the trip must name the arm-last law, got %r' % (problems,))

    def test_snapshot_after_push_exact(self):
        problems = find_snapshot_order_violations(self._wizard_src())
        self.assertEqual(
            problems, [],
            'activate must push BEFORE snapshotting button_mode and '
            'wire cmd.button LAST (wizard.py contract 4):\n  '
            + '\n  '.join(problems))

    def test_negative_control_snapshot_before_push_fires(self):
        problems = find_snapshot_order_violations(SNAPSHOT_TRAP)
        self.assertTrue(
            problems,
            'a button_mode snapshot BEFORE the set_wizard push MUST trip '
            'the pin -- it records a stale value (msm-order-law analog)')
        self.assertTrue(
            any('push BEFORE snapshot' in p for p in problems),
            'the trip must name the push-before-snapshot law, got %r'
            % (problems,))

    def test_cleanup_restores_drag_state_exact(self):
        problems = find_cleanup_restore_violations(self._wizard_src())
        self.assertEqual(
            problems, [],
            'cleanup must dearm the drag, delete the private selection, '
            'and restore button_mode via cmd.set + cmd.mouse() '
            '(probes H1/083B(3), D2):\n  ' + '\n  '.join(problems))

    def test_negative_control_cleanup_missing_dearm_fires(self):
        problems = find_cleanup_restore_violations(CLEANUP_TRAP)
        self.assertTrue(
            problems,
            'a cleanup missing the bare cmd.drag() deactivation MUST '
            'trip the pin -- the C-side drag would stay armed')
        self.assertTrue(
            any('cmd.drag() deactivation' in p for p in problems),
            'the trip must name the missing dearm, got %r' % (problems,))

    def test_live_wizard_passes_all_four_finders(self):
        # ONE aggregate positive: the LIVE wizard.py satisfies every
        # drag-mechanism law clean (the per-law tests above localize a
        # future failure; this one proves the envelope as a whole).
        src = self._wizard_src()
        problems = (find_arm_selection_form_violations(src)
                    + find_arm_last_violations(src)
                    + find_snapshot_order_violations(src)
                    + find_cleanup_restore_violations(src))
        self.assertEqual(
            problems, [],
            'the live wizard.py breaks one or more drag-mechanism '
            'ordering laws:\n  ' + '\n  '.join(problems))


if __name__ == '__main__':
    unittest.main()
