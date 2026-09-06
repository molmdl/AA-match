"""Purity gates for the aamatch pure layer (Phase 1, plan 01-08).

Enforces the purity contract MECHANICALLY (Phase-1 success criterion 2),
so "pure" never regresses silently. Four gates, all part of the normal
suite (`python3.6 -m unittest discover -s tests -v`):

- Gate A  -- AST import scan over the declared pure modules. EVERY
  ast.Import/ast.ImportFrom node is checked (module level AND inside
  function bodies -- research B7), so a lazy ``from pymol import cmd``
  buried in a helper fails the suite too. Absolute roots must be in the
  stdlib whitelist (A2) or the aamatch package; relative imports must
  target a pure module. AST parsing is immune to the grep tripwire (P2):
  a docstring that SAYS "from PyQt5 import" is a string constant in the
  AST, never an Import node (the prior art hit exactly that false
  positive -- G3/PITFALLS.md:83).
- Gate A2 -- ``aamatch/__init__.py`` must have ZERO module-level imports
  (lazy imports inside __init_plugin__/handlers are the design, R8.5).
  This is the prerequisite that lets every test in this repo import pure
  modules with zero sys.modules stubs (PITFALL 1: a greedy __init__ is
  how the prior art's MagicMock stubs crept back).
- Gate B  -- clean-subprocess import proof: each pure module is imported
  by a FRESH bare interpreter (cwd=repo-root, NO stubs anywhere). Catches
  what AST cannot: dynamic ``__import__('pymol')`` and transitive
  contamination through ``aamatch/__init__.py``. Subprocess exit codes
  are the only honest proof (P10) -- this process has already imported
  the package, so in-process sys.modules inspection would prove nothing.
- Gate D  -- 3.6 syntax floor: every ``aamatch/*.py`` compiles under
  ``python3.6 -m py_compile`` (A11; catches 3.7+ syntax, e.g.
  dataclasses or async-comprehension shortcuts).

Plus one NEGATIVE CONTROL proving the gate can actually FAIL: the
checker function is run against synthetic source containing real
``import pymol`` / ``from PyQt5 import QtWidgets`` statements AND a
docstring repeating the same tokens as prose. The gate must flag the
two REAL imports and NOT the docstring -- exactly 2 findings, one per
forbidden root. A naive token grep would find four hits and
false-positive on the docstring; this test pins that distinction.

This file itself is pure: it imports only ``ast, os, subprocess, sys,
unittest`` and treats the aamatch module names as STRINGS (Gate B runs
them in a subprocess; Gate A reads them as text). NO sys.modules
stubbing anywhere -- the whole point is zero stubs.

Run from repo root:
    python3.6 -m unittest tests.test_purity -v
    python3.6 -m unittest discover -s tests -v
"""

import ast
import os
import subprocess
import sys
import unittest

# Bootstrap so this suite works both via `unittest discover -s tests` and as
# a directly-executed module (prior-art pattern, PA-test-setup_state.py:17-19).
_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(_HERE, '..'))
PKG_DIR = os.path.join(REPO_ROOT, 'aamatch')
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# The declared pure modules (import targets: aamatch.<name>).
# Phase 1: setup_state, level_spec, persistence, backup, paths.
# Phase 2 (02-02): vec3 (tuple vector math), spatial (cell-list pruning).
# Phase 2 (02-03): manifest (bundled-data manifest parse/validate/enumerate).
# Phase 2 (02-05): capability (single typing home; imports math via vec3,
#                   .vec3 for the row-8 planarity fallback, and
#                   .setup_state INTERACTION_TYPES — the ONE enum home).
PURE_MODULES = ['setup_state', 'level_spec', 'persistence', 'backup',
                'paths', 'vec3', 'spatial', 'manifest', 'capability']

# Roots that must NEVER appear in any import of a pure module, in ANY
# scope (module level or function body -- B7). dataclasses is 3.7+.
FORBIDDEN = {'pymol', 'numpy', 'dataclasses', 'PyQt5', 'PySide2',
             'tkinter', 'Pmw', 'pmg_tk'}

# The ONLY stdlib roots a pure module may import (research A2 + sys).
ALLOWED_STDLIB = {'json', 'os', 'sys', 'tempfile', 'time', 'hashlib',
                  'random', 'copy', 'math', 'io', 're', 'collections',
                  'errno', 'ast', 'zipfile', 'shutil', 'unittest',
                  'datetime'}

# Synthetic source for the negative control: two REAL forbidden imports
# plus a docstring repeating the same tokens as PROSE. A token grep would
# count 4 hits (2 real + 2 prose) and false-positive on the docstring
# (P2 / prior-art G3); the AST gate must report exactly the 2 real ones.
NEGATIVE_CONTROL_SOURCE = '''"""Grep-trap bait: this module promises it will never do
"from PyQt5 import" anything at module level, and never says
import pymol outside of this docstring. All prose, no code.
"""

import os

import pymol
from PyQt5 import QtWidgets
'''


def find_bad_imports(src):
    """Return one problem string per impure import found in `src` (text).

    Pure function over source TEXT so the negative control can exercise
    it without touching real files. Walks EVERY node of the parsed tree,
    so imports inside function bodies are checked too (B7). Immune to
    docstrings/comments by construction (P2): prose becomes string
    constants in the AST, never Import nodes.

    Rules enforced:
    - any root in FORBIDDEN -> "forbidden import: ..."
    - any absolute root outside ALLOWED_STDLIB | {'aamatch'} -> whitelist
      failure (intra-package absolute imports of aamatch.* are allowed)
    - any relative import whose target is not one of PURE_MODULES (or
      '.') -> failure (relative imports must stay pure <- pure)
    """
    problems = []
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split('.')[0]
                if root in FORBIDDEN:
                    problems.append('forbidden import: import %s' % alias.name)
                elif root != 'aamatch' and root not in ALLOWED_STDLIB:
                    problems.append(
                        'import outside whitelist (stdlib + aamatch only): '
                        'import %s' % alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                # Relative: 'from . import x' -> node.module is None ('.',
                # the package itself); otherwise the target must be one of
                # the pure modules -- never a cmd/Qt module.
                target = node.module or ''
                if target and target.split('.')[0] not in PURE_MODULES:
                    problems.append(
                        'relative import must target a pure module: '
                        'from %s import ...' % target)
            else:
                root = (node.module or '').split('.')[0]
                if root in FORBIDDEN:
                    problems.append(
                        'forbidden import: from %s import ...' % node.module)
                elif root != 'aamatch' and root not in ALLOWED_STDLIB:
                    problems.append(
                        'import outside whitelist (stdlib + aamatch only): '
                        'from %s import ...' % node.module)
    return problems


def _read_source(path):
    """Read a .py file as text, encoding-independent of the locale."""
    with open(path, 'rb') as f:
        return f.read().decode('utf-8')


def _module_path(mod):
    """Absolute path of a pure module file inside the package dir."""
    return os.path.join(PKG_DIR, mod + '.py')


def _describe_import(node):
    """Human-readable form of an Import/ImportFrom node (for messages)."""
    if isinstance(node, ast.Import):
        return 'import %s' % ', '.join(a.name for a in node.names)
    return 'from %s%s import %s' % (
        '.' * node.level, node.module or '',
        ', '.join(a.name for a in node.names))


def _stderr_tail(stderr_bytes, lines=15):
    """Decode subprocess stderr (bytes) and keep the last `lines` lines."""
    text = stderr_bytes.decode('utf-8', errors='replace')
    tail = text.strip().splitlines()[-lines:]
    return '\n'.join(tail) if tail else '(no stderr)'


class TestGateAASTImportScan(unittest.TestCase):
    """Gate A: the declared pure modules import ONLY stdlib/pure, any scope."""

    def test_pure_modules_only_whitelisted_imports_anywhere(self):
        all_problems = []
        for mod in PURE_MODULES:
            path = _module_path(mod)
            for problem in find_bad_imports(_read_source(path)):
                all_problems.append('%s: %s' % (path, problem))
        self.assertEqual(
            all_problems, [],
            'Gate A failed: forbidden/non-whitelisted imports found in the '
            'pure modules (EVERY import node is checked, including inside '
            'function bodies; roots must be in ALLOWED_STDLIB or aamatch, '
            'relative imports must target pure modules):\n  '
            + '\n  '.join(all_problems))


class TestGateA2LazyInit(unittest.TestCase):
    """Gate A2: aamatch/__init__.py has ZERO module-level imports."""

    def test_init_has_no_module_level_imports(self):
        path = os.path.join(PKG_DIR, '__init__.py')
        tree = ast.parse(_read_source(path))
        offenders = [_describe_import(node) for node in tree.body
                     if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertEqual(
            offenders, [],
            'Gate A2 failed: aamatch/__init__.py has module-level import(s) '
            '%s. The lazy-import rule (R8.5) is what lets every pure-layer '
            'test run with zero sys.modules stubs (PITFALL 1): move imports '
            'inside __init_plugin__/handlers.' % (offenders,))
        # Function-level imports inside __init_plugin__ remain ALLOWED --
        # that IS the design. Gate A deliberately scans only PURE_MODULES
        # (not __init__.py) for exactly this reason.


class TestGateBCleanSubprocessImport(unittest.TestCase):
    """Gate B: each pure module imports in a fresh bare interpreter."""

    def test_pure_modules_import_in_clean_subprocess(self):
        for mod in PURE_MODULES:
            with self.subTest(module=mod):
                proc = subprocess.run(
                    [sys.executable, '-c', 'import aamatch.' + mod],
                    cwd=REPO_ROOT,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=30)
                self.assertEqual(
                    proc.returncode, 0,
                    'Gate B failed: clean-subprocess import of aamatch.%s '
                    'exited %d. NO stubs were used anywhere -- the package '
                    'itself pulls in something impure (check module-level '
                    'imports of aamatch/__init__.py and transitive '
                    'imports; dynamic __import__ escapes Gate A but not '
                    'this gate).\n%s'
                    % (mod, proc.returncode, _stderr_tail(proc.stderr)))


class TestGateDPyCompileSyntax(unittest.TestCase):
    """Gate D: every aamatch/*.py compiles under the 3.6 syntax floor."""

    def test_all_package_files_compile_under_36(self):
        py_files = sorted(name for name in os.listdir(PKG_DIR)
                          if name.endswith('.py'))
        self.assertTrue(
            py_files,
            'no .py files found in %s (wrong worktree/checkout?)' % PKG_DIR)
        for name in py_files:
            with self.subTest(file=name):
                proc = subprocess.run(
                    [sys.executable, '-m', 'py_compile',
                     os.path.join('aamatch', name)],
                    cwd=REPO_ROOT,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=30)
                self.assertEqual(
                    proc.returncode, 0,
                    'Gate D failed: %s does not compile under python3.6 '
                    '(3.7+ syntax? dataclasses?)\n%s'
                    % (name, _stderr_tail(proc.stderr)))


class TestNegativeControl(unittest.TestCase):
    """Proves Gate A can FAIL, and that docstring prose is immune (P2)."""

    def test_checker_flags_real_imports_but_not_docstring(self):
        problems = find_bad_imports(NEGATIVE_CONTROL_SOURCE)
        # Exactly two findings: the two REAL imports. The docstring
        # repeats both tokens as prose; a grep-based checker would raise
        # the count to 4 and false-positive -- the prior-art tripwire
        # this negative control pins down.
        self.assertEqual(
            len(problems), 2,
            'negative control broken: expected exactly 2 flagged imports '
            '(pymol + PyQt5; docstring ignored), got %d:\n  %s'
            % (len(problems), '\n  '.join(problems)))
        pymol_hits = [p for p in problems if 'pymol' in p]
        qt_hits = [p for p in problems if 'PyQt5' in p]
        self.assertEqual(
            len(pymol_hits), 1,
            'expected exactly one pymol finding, got %r' % (pymol_hits,))
        self.assertEqual(
            len(qt_hits), 1,
            'expected exactly one PyQt5 finding, got %r' % (qt_hits,))
        # And the whitelisted stdlib import passed silently.
        self.assertNotIn('import os', '\n'.join(problems))


if __name__ == '__main__':
    unittest.main()
