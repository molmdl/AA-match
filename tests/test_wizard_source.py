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

# The scanned set grows as cmd-tier UI modules land (03-05 adds
# gamestart.py per the 03-03 spawn notes).
SCANNED_MODULES = ['wizard.py']

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


if __name__ == '__main__':
    unittest.main()
