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


if __name__ == '__main__':
    unittest.main()
