"""WSL-pure contract tests for the aamatch package skeleton (Phase 1, plan 01-01).

These tests replicate the PyMOL 2.5.0 plugin-loader contract against
``aamatch/__init__.py`` WITHOUT importing pymol or stubbing sys.modules:

1. Metadata block: ``# Key: value`` comment lines must be the first lines of
   the file; parsing stops at the first non-# line
   (pymol/plugins/__init__.py:193-210).
2. Docstring survival: the loader's get_docstring reads ``co_consts[0]`` of
   the compiled module (pymol/plugins/__init__.py:230-246) — the docstring
   must still be the first const despite the leading comment block.
3. Lazy-import discipline: ZERO module-level imports (the prerequisite that
   lets every pure-layer test run with no stubs — PITFALLS.md Pitfall 1,
   research R8.5).
4. Entry points: ``__init_plugin__``, ``run_plugin_gui``, ``__version__``.
5. Placeholder output: prints a version line using zero Qt code.

Run either way from the repo root:
    python3.6 -m unittest tests.test_package_skeleton -v
    python3.6 -m unittest discover -s tests -v
"""

import ast
import contextlib
import io
import os
import sys
import unittest

# Bootstrap so this suite works both via `unittest discover -s tests` and as
# a directly-executed module (prior-art pattern, PA-test-setup_state.py:17-19).
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

INIT_PATH = os.path.join(_REPO_ROOT, 'aamatch', '__init__.py')


def _read_init_source():
    """Read aamatch/__init__.py as text, encoding-independent of the locale."""
    with io.open(INIT_PATH, 'rb') as f:
        return f.read().decode('utf-8')


def _parse_metadata_block(src):
    """Replicate the loader's metadata parse (plugins/__init__.py:193-210).

    Consume leading lines while they start with '#'; split each on the first
    ':'; strip the leading '#' and whitespace from the key. Parsing stops at
    the first non-# line — which is why the metadata block must precede the
    module docstring.
    """
    metadata = {}
    for line in src.splitlines():
        if not line.startswith('#'):
            break
        if ':' not in line:
            continue
        raw_key, _, value = line.partition(':')
        metadata[raw_key.lstrip('#').strip()] = value.strip()
    return metadata


class TestPackageSkeleton(unittest.TestCase):
    """Loader-facing contract of the aamatch Phase-1 skeleton."""

    def setUp(self):
        self.assertTrue(
            os.path.isfile(INIT_PATH),
            'aamatch/__init__.py not found at %s' % INIT_PATH,
        )
        self.src = _read_init_source()

    def test_metadata_block_parses(self):
        """The two metadata lines are first and parse to the expected dict."""
        metadata = _parse_metadata_block(self.src)
        self.assertEqual(metadata.get('Version'), '0.1.0')
        self.assertEqual(metadata.get('Citation-Required'), 'No')

    def test_docstring_survives_metadata(self):
        """The docstring is still co_consts[0] despite the leading comments."""
        code = compile(self.src, 'aamatch/__init__.py', 'exec')
        first_const = code.co_consts[0]
        self.assertIsInstance(first_const, str)
        self.assertIn('AA-match', first_const)

    def test_no_module_level_imports(self):
        """Zero module-level import statements — even stdlib (lazy-import
        discipline; function-level imports inside __init_plugin__ are fine)."""
        tree = ast.parse(self.src)
        offenders = [
            node for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        self.assertEqual(
            offenders, [],
            'module-level imports found in aamatch/__init__.py: %r'
            % [ast.dump(node) for node in offenders],
        )

    def test_entry_points_exist(self):
        """Loader-contract entry points exist and version matches metadata."""
        import aamatch
        self.assertTrue(callable(aamatch.__init_plugin__))
        self.assertTrue(callable(aamatch.run_plugin_gui))
        self.assertEqual(aamatch.__version__, '0.1.0')

    def test_run_plugin_gui_prints_version(self):
        """Placeholder prints a version line containing version and label."""
        import aamatch
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            aamatch.run_plugin_gui()
        output = buf.getvalue()
        self.assertIn('0.1.0', output)
        self.assertIn('AA-match', output)


if __name__ == '__main__':
    unittest.main()
