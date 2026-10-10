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


# --- 08.2-03 keyboard-channel pins (do_special / do_key) --------------------
# The frozen keyboard map (03-06 verdict, STATE.md:142): do_special owns
# GLUT LEFT (100) / RIGHT (102) ONLY -- UP (101) / DOWN (103) can never be
# wizard game keys because PyMOL's C-source OrthoSpecial co-fires
# command-line history unconditionally
# (03-RESEARCH-wizard-interaction.md:212-215). do_key owns w/s/q/e camera
# nudges via the module-level _KEY_NUDGES map plus ','/'.' view-axis
# rotates by wizard_core.ROTATE_STEP_DEG (the do_key contract,
# wizard.py:1134-1153). Zero automated coverage existed before 08.2-03.

# LEFT k==100 -> nudge camera -x; RIGHT k==102 -> nudge camera +x.
EXPECTED_SPECIAL_BRANCHES = {100: (-1, 0, 0), 102: (1, 0, 0)}

# The frozen w/s/y and q/e/z camera-step map (wizard.py:93-94 --
# 'w': camera +y, 's': camera -y, 'q': camera -z (In/into the screen),
# 'e': camera +z).
EXPECTED_KEY_NUDGES = {'w': (0.0, 1.0, 0.0), 's': (0.0, -1.0, 0.0),
                       'q': (0.0, 0.0, -1.0), 'e': (0.0, 0.0, 1.0)}


def find_special_key_violations(src):
    """Every problem with do_special's pinned GLUT special-key map.

    Frozen laws pinned here (03-06 keyboard verdict, STATE.md:142):
    * the set of int constants compared against anywhere in do_special
      is EXACTLY {100, 102} -- handling 101 (UP) or 103 (DOWN) is a
      violation by itself (the C-layer history co-fire makes those
      keys unusable, 03-RESEARCH-wizard-interaction.md:212-215);
    * each branch calls ``self.nudge_cam`` with LITERAL args
      (-1, 0, 0) for k==100 and (1, 0, 0) for k==102 (LEFT = camera
      -x, RIGHT = camera +x -- screen-relative by design);
    * each owned branch ``return 1`` (consumed -- wizard-first
      dispatch); a silent fall-through would hand the key back to
      PyMOL's built-in arrows.
    """
    problems = []
    tree = ast.parse(src)
    fn = _function_def(tree, 'do_special')
    if fn is None:
        return ['do_special: FunctionDef NOT FOUND -- the GLUT '
                'special-key channel (LEFT/RIGHT nudges) is missing '
                'entirely from wizard.py']
    seen = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Compare):
            for operand in [node.left] + list(node.comparators):
                v = _const_int(operand)
                if v is not None:
                    seen.add(v)
    if seen != set(EXPECTED_SPECIAL_BRANCHES):
        problems.append(
            'do_special: int constants in comparisons %s != the '
            'frozen {100, 102} (LEFT/RIGHT) -- UP=101/DOWN=103 can '
            'NEVER be game keys (PyMOL C-source co-fires command '
            'history unconditionally, 03-RESEARCH-wizard-interaction'
            '.md:212-215; 03-06 verdict STATE.md:142)'
            % (sorted(seen),))
    for node in ast.walk(fn):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not (isinstance(test, ast.Compare) and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Eq)
                and len(test.comparators) == 1):
            continue
        v = _const_int(test.left) if _const_int(test.left) is not None \
            else _const_int(test.comparators[0])
        if v is None or v not in EXPECTED_SPECIAL_BRANCHES:
            continue
        expected = EXPECTED_SPECIAL_BRANCHES[v]
        nudge_ok = False
        ret_ok = False
        for stmt in node.body:
            for sub in ast.walk(stmt):
                if isinstance(sub, ast.Call) \
                        and isinstance(sub.func, ast.Attribute) \
                        and sub.func.attr == 'nudge_cam' \
                        and isinstance(sub.func.value, ast.Name) \
                        and sub.func.value.id == 'self' \
                        and not sub.keywords \
                        and tuple(_const_int(a)
                                  for a in sub.args) == expected:
                    nudge_ok = True
                if isinstance(sub, ast.Return) and sub.value is not None \
                        and _const_int(sub.value) == 1:
                    ret_ok = True
        if not nudge_ok:
            problems.append(
                'do_special k==%d (line %d): no self.nudge_cam%s call '
                'in the branch -- LEFT/RIGHT must nudge camera x by '
                'exactly that LITERAL step (03-06 keyboard law, '
                'STATE.md:142)' % (v, node.lineno, expected))
        if not ret_ok:
            problems.append(
                'do_special k==%d (line %d): branch does not '
                '`return 1` -- an owned key must report CONSUMED in '
                'wizard-first dispatch, else it falls through to '
                'PyMOL shortcuts' % (v, node.lineno))
    return problems


def find_key_nudge_map_violations(src):
    """Every problem with the do_key nudge channel.

    Frozen laws pinned here (the do_key contract, wizard.py:1134-1153
    + _KEY_NUDGES wizard.py:93-94):
    * the module-level ``_KEY_NUDGES`` Dict literal must
      ast.literal_eval to EXACTLY EXPECTED_KEY_NUDGES -- w/s are
      camera-y +/-, q/e are camera-z -/+ ('q' = In = INTO the
      screen); no extra keys ('d' is NOT a nudge key);
    * do_key applies the map via ``_KEY_NUDGES.get(ch)`` and calls
      ``self.nudge_cam(*step)`` -- a raw indexing or a hand-unrolled
      per-char branch is a silent map-drift vector.
    """
    problems = []
    tree = ast.parse(src)
    value_node = None
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 \
                and isinstance(stmt.targets[0], ast.Name) \
                and stmt.targets[0].id == '_KEY_NUDGES':
            value_node = stmt.value
    if value_node is None:
        problems.append('_KEY_NUDGES: module-level assignment NOT '
                        'FOUND -- the w/s/q/e nudge map is missing')
    else:
        literal = None
        try:
            literal = ast.literal_eval(value_node)
        except (ValueError, SyntaxError):
            problems.append('_KEY_NUDGES: not a plain literal Dict -- '
                            'the map must stay literal_eval-able so '
                            'this pin can checksum it exactly')
        if isinstance(literal, dict):
            for ch, want in sorted(EXPECTED_KEY_NUDGES.items()):
                got = literal.get(ch)
                if got != want:
                    problems.append(
                        '_KEY_NUDGES[%r] = %r, must be %r (frozen '
                        'camera-step map, wizard.py:93-94 / the 03-06 '
                        'verdict STATE.md:142)' % (ch, got, want))
            for ch in sorted(set(literal) - set(EXPECTED_KEY_NUDGES)):
                problems.append(
                    '_KEY_NUDGES: EXTRA key %r -- the game OWNS only '
                    'w/s/q/e (everything else must fall through to '
                    'PyMOL shortcuts; the do_key contract)'
                    % (ch,))
        elif literal is not None:
            problems.append('_KEY_NUDGES: evaluates to %r, not a '
                            'dict' % (literal,))
    fn = _function_def(tree, 'do_key')
    if fn is None:
        problems.append('do_key: FunctionDef NOT FOUND -- the ASCII '
                        'key channel (w/s/q/e nudges, ,/. rotates) is '
                        'missing entirely from wizard.py')
        return problems
    get_ok = False
    nudge_ok = False
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call) \
                or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr == 'get' \
                and isinstance(node.func.value, ast.Name) \
                and node.func.value.id == '_KEY_NUDGES' \
                and len(node.args) == 1 \
                and isinstance(node.args[0], ast.Name) \
                and node.args[0].id == 'ch':
            get_ok = True
        if node.func.attr == 'nudge_cam' \
                and isinstance(node.func.value, ast.Name) \
                and node.func.value.id == 'self' \
                and len(node.args) == 1 \
                and isinstance(node.args[0], ast.Starred) \
                and isinstance(node.args[0].value, ast.Name) \
                and node.args[0].value.id == 'step' \
                and not node.keywords:
            nudge_ok = True
    if not get_ok:
        problems.append('do_key: no `_KEY_NUDGES.get(ch)` call -- '
                        'the map must be applied through the .get '
                        'lookup (the do_key contract)')
    if not nudge_ok:
        problems.append('do_key: no `self.nudge_cam(*step)` call -- '
                        'the looked-up camera step must be applied '
                        'verbatim through the nudge channel')
    return problems


def find_key_rotate_violations(src):
    """Every problem with do_key's ','/'.' view-axis rotate branches.

    Frozen law pinned here (the do_key contract, wizard.py:1147-1152):
    ',' rotates by ``-wizard_core.ROTATE_STEP_DEG`` (a UnaryOp USub
    over the Attribute -- a flipped sign is a caught bug, not a
    refactor), '.' by the positive Attribute; both branches
    ``return 1`` (consumed)."""
    problems = []
    tree = ast.parse(src)
    fn = _function_def(tree, 'do_key')
    if fn is None:
        return ['do_key: FunctionDef NOT FOUND -- the ,/. rotate '
                'branches are missing from wizard.py']

    for ch, neg in ((',', True), ('.', False)):
        branch = None
        for node in ast.walk(fn):
            if isinstance(node, ast.If) \
                    and isinstance(node.test, ast.Compare) \
                    and len(node.test.ops) == 1 \
                    and isinstance(node.test.ops[0], ast.Eq) \
                    and isinstance(node.test.left, ast.Name) \
                    and node.test.left.id == 'ch' \
                    and len(node.test.comparators) == 1:
                comp = node.test.comparators[0]
                if isinstance(comp, ast.Str) and comp.s == ch:
                    branch = node
        if branch is None:
            problems.append("do_key: no `ch == %r` branch -- the %s "
                            "rotate key is unhandled (it must be "
                            "owned, wizard-first dispatch)"
                            % (ch, 'negative' if neg else 'positive'))
            continue
        rot_ok = False
        ret_ok = False
        for stmt in branch.body:
            for sub in ast.walk(stmt):
                if isinstance(sub, ast.Call) \
                        and isinstance(sub.func, ast.Attribute) \
                        and sub.func.attr == 'rotate_view' \
                        and isinstance(sub.func.value, ast.Name) \
                        and sub.func.value.id == 'self' \
                        and len(sub.args) == 1 \
                        and not sub.keywords:
                    arg = sub.args[0]
                    if neg:
                        if isinstance(arg, ast.UnaryOp) \
                                and isinstance(arg.op, ast.USub) \
                                and isinstance(arg.operand, ast.Attribute) \
                                and arg.operand.attr == 'ROTATE_STEP_DEG' \
                                and isinstance(arg.operand.value,
                                               ast.Name) \
                                and arg.operand.value.id == 'wizard_core':
                            rot_ok = True
                    else:
                        if isinstance(arg, ast.Attribute) \
                                and arg.attr == 'ROTATE_STEP_DEG' \
                                and isinstance(arg.value, ast.Name) \
                                and arg.value.id == 'wizard_core':
                            rot_ok = True
                if isinstance(sub, ast.Return) and sub.value is not None \
                        and _const_int(sub.value) == 1:
                    ret_ok = True
        if not rot_ok:
            problems.append(
                'do_key ch == %r (line %d): no '
                'self.rotate_view(%swizard_core.ROTATE_STEP_DEG) call '
                '-- the view-axis rotate sign is FROZEN (a flip here '
                'is a bug, wizard.py:1147-1152)'
                % (ch, branch.lineno, '-' if neg else ''))
        if not ret_ok:
            problems.append(
                'do_key ch == %r (line %d): branch does not '
                '`return 1` -- an owned key must report CONSUMED '
                '(wizard-first dispatch)' % (ch, branch.lineno))
    return problems


# Negative-control traps for the keyboard finders (synthetic sources
# wired with exactly one violation each -- test_purity.py's rule: a
# gate that cannot fail proves nothing).
SPECIAL_TRAP = '''\
def do_special(self, k, x, y, mod):
    """Synthetic: 101 (UP) must NEVER be a game key."""
    if k == 100:
        self.nudge_cam(-1, 0, 0)
        return 1
    if k == 102:
        self.nudge_cam(1, 0, 0)
        return 1
    if k == 101:
        self.nudge_cam(0, 1, 0)
        return 1
    return None
'''

NUDGE_MAP_TRAP = '''\
_KEY_NUDGES = {'w': (1.0, 1.0, 0.0), 's': (0.0, -1.0, 0.0),
               'q': (0.0, 0.0, -1.0), 'e': (0.0, 0.0, 1.0)}


def do_key(self, k, x, y, mod):
    ch = chr(k) if 0 <= k < 127 else ''
    step = _KEY_NUDGES.get(ch)
    if step is not None:
        self.nudge_cam(*step)
        return 1
    return None
'''

ROTATE_TRAP = '''\
def do_key(self, k, x, y, mod):
    if ch == ',':
        self.rotate_view(wizard_core.ROTATE_STEP_DEG)
        return 1
    if ch == '.':
        self.rotate_view(wizard_core.ROTATE_STEP_DEG)
        return 1
    return None
'''


# --- 08.2-03 frozen movement-MODEL discipline pins --------------------------
# ROADMAP 8.2 criterion 3 made mechanical: the Phase-3 movement MODEL
# is frozen, and the frozen discipline inside wizard.py gets WSL-runnable
# AST teeth. M1/M2 baked forms (translate state=1 camera=0; rotate
# selection-form camera=0, NEVER object=), M3 the fail-closed identity
# assert after every move, and the 06-06 law (STATE.md:212):
# _require_playing() is the FIRST line of every gameplay impl.

# The five gameplay impls under the gate-order law (06-06).
GATED_IMPLS = ('_nudge_cam_impl', '_rotate_axis_impl',
               '_step_to_ligand_impl', '_move_to_impl',
               '_reset_grid_impl')


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
    code map (exactly two translate sites + one rotate site)."""
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


# The pinned enumeration (RESEARCH-code.md sec. 2, M1/M2: translate in
# _nudge_cam_impl wizard.py:685 + _step_to_ligand_impl wizard.py:740;
# rotate in _rotate_axis_impl wizard.py:706). A NEW bake site fails
# this pin loudly -- it must be enumerated and gated, never sneaked in.
EXPECTED_BAKE_SITES = sorted([('translate', '_nudge_cam_impl'),
                              ('translate', '_step_to_ligand_impl'),
                              ('rotate', '_rotate_axis_impl')])


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


# Negative-control traps for the discipline finders.
BAKE_TRAP_CAMERA = '''\
def _nudge_cam_impl(self):
    cmd.translate([0.0, 0.0, 0.0], 'obj', state=1, camera=1)
'''

BAKE_TRAP_OBJECT = '''\
def _rotate_axis_impl(self, axis, deg, origin):
    cmd.rotate([1.0, 0.0, 0.0], 90.0, camera=0, object='aa1')
'''

# Only the five gated impls matter to the gate finder; the trap wires
# ONE impl with a non-gate first statement (a different call).
GATE_TRAP_FIRST = '''\
def _nudge_cam_impl(self, dx, dy, dz):
    self._current_object()
    self._assert_identity('obj')

def _rotate_axis_impl(self, axis, deg, origin):
    from . import engine
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
    self._assert_identity('obj')
'''

# Same shape but _reset_grid_impl drops the identity assert.
GATE_TRAP_ASSERT = '''\
def _nudge_cam_impl(self, dx, dy, dz):
    self._require_playing()
    self._assert_identity('obj')

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


class TestKeyboardChannelMap(unittest.TestCase):
    """08.2-03: the wizard keyboard channels are AST-pinned (ROADMAP
    8.2 criterion-3 teeth).

    Until this class there was ZERO automated coverage of
    do_special/do_key -- any key-map change would have been invisible
    to the WSL battery (RESEARCH-code.md sec. 1.1). Pinned laws:
    do_special owns LEFT(100)/RIGHT(102) ONLY -- UP(101)/DOWN(103) can
    never be game keys because PyMOL's C-source co-fires command-line
    history unconditionally (03-RESEARCH-wizard-interaction.md:212-215;
    the 03-06 verdict STATE.md:142); do_key owns w/s/q/e via the frozen
    _KEY_NUDGES camera-step map plus ','/'.' view-axis rotates by
    wizard_core.ROTATE_STEP_DEG, every owned key returning 1 (the
    do_key contract, wizard.py:1134-1153). wizard.py is SCANNED, never
    imported -- these are pure AST pins over the source text.
    """

    def _problems(self, finder):
        return finder(_read_source(os.path.join(PKG_DIR, 'wizard.py')))

    def test_special_key_map_exact(self):
        problems = self._problems(find_special_key_violations)
        self.assertEqual(
            problems, [],
            'do_special must own LEFT/RIGHT only, nudging camera x '
            'with literal steps and consuming the keys:\n  '
            + '\n  '.join(problems))

    def test_key_nudge_map_and_apply_exact(self):
        problems = self._problems(find_key_nudge_map_violations)
        self.assertEqual(
            problems, [],
            '_KEY_NUDGES must be the frozen w/s/q/e camera-step map '
            'applied via .get(ch) + nudge_cam(*step):\n  '
            + '\n  '.join(problems))

    def test_key_rotate_branches_exact(self):
        problems = self._problems(find_key_rotate_violations)
        self.assertEqual(
            problems, [],
            "the ','/'.' branches must call rotate_view with the "
            "pinned-sign wizard_core.ROTATE_STEP_DEG and consume the "
            'keys:\n  ' + '\n  '.join(problems))

    def test_negative_control_do_special_handles_up(self):
        problems = find_special_key_violations(SPECIAL_TRAP)
        self.assertTrue(
            problems,
            'a do_special that owns 101 (UP) MUST trip the pin -- '
            'UP/DOWN are dead by design (C-layer history co-fire)')
        self.assertTrue(any('101' in p or '{100, 102}' in p
                            for p in problems),
                        'the trip must name the {100, 102} law, got %r'
                        % (problems,))

    def test_negative_control_wrong_w_vector(self):
        problems = find_key_nudge_map_violations(NUDGE_MAP_TRAP)
        self.assertTrue(
            problems,
            "a _KEY_NUDGES map with a wrong 'w' vector MUST trip the "
            'pin -- the camera-step map is frozen')
        self.assertTrue(any("'w'" in p for p in problems),
                        "the trip must name the 'w' entry, got %r"
                        % (problems,))

    def test_negative_control_flipped_rotate_sign(self):
        problems = find_key_rotate_violations(ROTATE_TRAP)
        self.assertTrue(
            problems,
            "a ',' branch without the NEGATIVE ROTATE_STEP_DEG MUST "
            'trip the pin -- a sign flip is a caught bug, not a '
            'refactor')
        self.assertTrue(any('-' in p for p in problems),
                        'the trip must name the negative-step law, '
                        'got %r' % (problems,))


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
        # exactly two translate sites + one rotate site today (the
        # RESEARCH-code.md sec. 2 map); a NEW bake site must be
        # enumerated here and gated, never sneaked in.
        sites = find_bake_call_sites(
            _read_source(os.path.join(PKG_DIR, 'wizard.py')))
        self.assertEqual(
            sites, EXPECTED_BAKE_SITES,
            'the bake-call enumeration drifted from the frozen map '
            '(translate: _nudge_cam_impl + _step_to_ligand_impl; '
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
            any('_nudge_cam_impl' in p and '_require_playing' in p
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


if __name__ == '__main__':
    unittest.main()
