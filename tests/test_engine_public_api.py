"""Mechanical source pin for the engine's promoted public seam (quick-003).

CONTRACT STORY: the two former engine privates ``_current_game`` /
``_remap_ligand_bonds`` were promoted to the documented public API
``current_game`` / ``remap_ligand_bonds`` in quick-003. Every production
+ engine-internal caller now uses the PUBLIC names. The private names
survive ONLY as module-level alias assignments
(``_current_game = current_game`` etc.) -- the byte-frozen standing
smokes call through them (08.1-07 KEEP-smokes law), so this file pins
the shape that keeps smokes 01-22 green with zero smoke edits: public
FunctionDefs present, private names are ALIASES (never shadowing defs,
which would silently diverge), and zero ``engine.<private>`` attribute
call sites outside engine.py itself.

WHY AST, not an import: WSL has no PyMOL, so aamatch/engine.py can
never be imported here, and the 01-08 purity law forbids sys.modules
stubs. House precedent: test_wizard_source.py / test_package_skeleton.py
/ test_code_audit.py -- parse the source, walk the tree. ``ast`` makes
docstring prose structurally invisible to the call-site finder, so the
finder cannot blind-fail on a mention (Gate-C immunity), and the
NEGATIVE CONTROL below proves it still FIRES on a real
``engine._current_game()`` call -- test_purity.py's rule: a gate that
cannot fail proves nothing.

Run from repo root:
    python3.6 -m unittest tests.test_engine_public_api -v
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

# The promoted public names and their legacy private aliases (quick-003).
# '_current_registry' is deliberately NOT here -- it stays private,
# untouched, and no alias exists for it.
PUBLIC_NAMES = ('current_game', 'remap_ligand_bonds')
PRIVATE_ALIASES = ('_current_game', '_remap_ligand_bonds')


def _read_source(path):
    """Read a .py file as text, encoding-independent of the locale."""
    with open(path, 'rb') as f:
        return f.read().decode('utf-8')


def _chain_root_name(node):
    """Walk an Attribute value chain down to its root ast.Name id
    (``engine._x`` -> 'engine'; ``self.engine._x`` -> 'self'). Returns
    None when the chain bottoms out at a non-Name (call results,
    subscripts, ...)."""
    while isinstance(node, ast.Attribute):
        node = node.value
    if isinstance(node, ast.Name):
        return node.id
    return None


def find_private_engine_calls(src, privates=PRIVATE_ALIASES):
    """Every ast.Call in ``src`` of the form ``engine.<private>(...)``
    (the legacy seam no production code may use after quick-003).

    A call counts only when the attribute name is one of ``privates``
    AND the value chain roots at the bare name 'engine' -- a
    ``game._current_game()`` attribute call (different root) is
    ignored. Scans ALL scopes (module level + every function body --
    ast.walk). Returns one problem string per offender, source-line-
    annotated so a trip names its site. Docstring prose cannot appear
    here (string constants are not Call nodes).
    """
    problems = []
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        if func.attr in privates and _chain_root_name(func) == 'engine':
            problems.append(
                'line %d: CALLS engine.%s -- quick-003 promoted the '
                'public seam; production code must call '
                'engine.%s (the private name is an alias kept ONLY '
                "for the byte-frozen smokes' alias calls)"
                % (node.lineno, func.attr, func.attr.lstrip('_')))
    return problems


# Negative control: a synthetic source wired with exactly one
# engine._current_game() and one engine._remap_ligand_bonds(r, l) call,
# plus a game._current_game() line whose root name is NOT 'engine'
# (must be ignored -- the value-chain scoping proof).
PRIVATE_TRAP = (
    'def f(engine, game, r, l):\n'
    '    engine._current_game()\n'
    '    engine._remap_ligand_bonds(r, l)\n'
    '    game._current_game()\n'
)


class TestEnginePublicApi(unittest.TestCase):
    """quick-003: the promoted seam's source shape, pinned."""

    def test_public_functions_defined(self):
        tree = ast.parse(_read_source(os.path.join(PKG_DIR,
                                                   'engine.py')))
        defined = set(node.name for node in tree.body
                      if isinstance(node, ast.FunctionDef))
        for name in PUBLIC_NAMES:
            self.assertIn(
                name, defined,
                'engine.py must define a top-level public %s -- the '
                'quick-003 promoted seam is missing (or was renamed '
                'back)' % name)

    def test_privates_are_module_level_aliases(self):
        tree = ast.parse(_read_source(os.path.join(PKG_DIR,
                                                   'engine.py')))
        aliases = set()
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) \
                        and target.id in PRIVATE_ALIASES \
                        and isinstance(node.value, ast.Name) \
                        and node.value.id == target.id.lstrip('_'):
                    aliases.add(target.id)
        self.assertEqual(
            aliases, set(PRIVATE_ALIASES),
            'engine.py must carry module-level aliases '
            '_current_game = current_game and '
            '_remap_ligand_bonds = remap_ligand_bonds (the byte-frozen '
            "smokes' alias calls, 08.1-07 KEEP-smokes law); found %r"
            % (sorted(aliases),))
        defs = set(node.name for node in ast.walk(tree)
                   if isinstance(node, ast.FunctionDef))
        for name in PRIVATE_ALIASES:
            self.assertNotIn(
                name, defs,
                'engine.py must NOT define a FunctionDef named %s -- '
                'the private name is a module-level ALIAS only; a '
                'shadowing def would let the smoke-called name and '
                'the public name silently diverge' % name)

    def test_no_private_engine_calls_outside_engine(self):
        offenders = []
        for name in sorted(os.listdir(PKG_DIR)):
            if not name.endswith('.py') or name == 'engine.py':
                continue
            offenders.extend(
                '%s: %s' % (name, problem)
                for problem in find_private_engine_calls(
                    _read_source(os.path.join(PKG_DIR, name))))
        self.assertEqual(
            offenders, [],
            'every production caller uses the PUBLIC engine seam after '
            'quick-003:\n  ' + '\n  '.join(offenders))

    def test_finder_fires_on_negative_control(self):
        problems = find_private_engine_calls(PRIVATE_TRAP)
        self.assertEqual(
            len(problems), 2,
            'the finder must flag exactly the 2 synthetic '
            'engine.<private> calls (the game._current_game() line -- '
            'a non-engine value chain -- must NOT count), got %r'
            % (problems,))


if __name__ == '__main__':
    unittest.main()
