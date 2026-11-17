"""Docs-audit battery: DOCS-02's audit as standing WSL checks (plan 09-10).

Methodology: .planning/phases/09-help-docs-release-audit/09-RESEARCH-docs-audit.md
section 4.c ("Automatable in the WSL suite"). This is a NEW file on purpose:
tests/test_demo_data.py forbids relaxation in its own header, so the docs
checks live here and never edit that battery. The file runs under bare
python3.6 with ZERO module-stub injections -- it reads repo files as text/data
only and never imports PyMOL, Qt, or numpy (the Qt-tier tooltips are pinned
via their SOURCE text, not by importing the modules).

Gate-C compliance (AGENTS.md gate 3): every assertion here is a
COVERAGE/PRESENCE check -- a required string must EXIST. There are no
prohibition-greps over English prose. The only "not in" asserts target (a)
the placeholder marker 'TBD' (a placeholder-completeness check, not prose
vocabulary) and (b) the three deleted private identifiers
(_INTERACTION_LABELS / _INTERACTION_TIPS / _MODE_CONTEXT), which are
identifier-scoped by construction and cannot false-fire on prose.

Tooltip pins read the Qt-tier sources as TEXT and first join implicitly
concatenated string literals, because the live tooltip sentences are written
across several source lines (e.g. '... it ' 'advances ...'). Joining lets a
plain source-text substring assert see the logical sentence; nothing here
imports the modules.

Repo root is anchored from __file__ (the tests/test_demo_data.py precedent:
unit tests may use __file__; only smokes may not).
"""

import json
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README_PATH = os.path.join(REPO_ROOT, 'README.md')
DOCS_PATH = os.path.join(REPO_ROOT, 'docs', 'DATA_SOURCES.md')
MANIFEST_PATH = os.path.join(REPO_ROOT, 'aamatch', 'data', 'MANIFEST.json')
LIGANDS_DIR = os.path.join(REPO_ROOT, 'aamatch', 'data', 'ligands')
INIT_PATH = os.path.join(REPO_ROOT, 'aamatch', '__init__.py')
GAME_WINDOW_PATH = os.path.join(REPO_ROOT, 'aamatch', 'game_window.py')
SETUP_WINDOW_PATH = os.path.join(REPO_ROOT, 'aamatch', 'setup_window.py')


def _read(path):
    """Read a repo file as UTF-8 text (text/data only -- never imported)."""
    with open(path, 'rb') as fh:
        return fh.read().decode('utf-8')


def _load_sets():
    """The manifest's set list, parsed as plain JSON (no runtime imports)."""
    return json.loads(_read(MANIFEST_PATH))['data']['sets']


def _section_span(text, heading):
    """Text after a top-level '## ' heading, up to the next '## ' heading/EOF."""
    start = text.find(heading)
    if start < 0:
        raise AssertionError('section not found: %r' % heading)
    start += len(heading)
    nxt = text.find('\n## ', start)
    return text[start:] if nxt < 0 else text[start:nxt]


def _set_section_span(text, set_id):
    """Text from a '### <set_id>' header line to the next '### ' header/EOF."""
    match = re.search(r'^### %s\b' % re.escape(set_id), text, re.MULTILINE)
    if not match:
        raise AssertionError('DATA_SOURCES section missing: %r' % set_id)
    after = text[match.end():]
    nxt = re.search(r'^### ', after, re.MULTILINE)
    end = len(text) if not nxt else match.end() + nxt.start()
    return text[match.start():end]


def _joined_string_source(path):
    """Source text with adjacent single-quoted literals joined together.

    The live tooltip sentences are split across implicitly concatenated
    literals, so a closing-quote / newline / whitespace / opening-quote
    sequence is collapsed. This is a TEXT transform over the source file --
    the Qt module is never imported.
    """
    return re.sub(r"'\s*\n\s*'", '', _read(path))


class TestReadmePlaceholders(unittest.TestCase):
    """README is placeholder-free and its required sections are filled."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(README_PATH)

    def test_no_tbd_placeholder_anywhere(self):
        # 'TBD' is a placeholder marker (not prose vocabulary): its absence
        # is the placeholder-completeness check, not a banned-token grep.
        self.assertNotIn('TBD', self.text)

    def test_usage_section_non_empty(self):
        span = _section_span(self.text, '## Usage')
        self.assertTrue(span.strip(), 'Usage section is empty')

    def test_project_structure_fenced_block_non_empty(self):
        span = _section_span(self.text, '## Project Structure')
        match = re.search(r'```(.*?)```', span, re.DOTALL)
        self.assertIsNotNone(match, 'Project Structure has no fenced block')
        block = match.group(1)
        self.assertTrue(block.strip(), 'Project Structure fenced block is empty')
        self.assertNotEqual(block.strip(), '#TBD')

    def test_acknowledgements_have_no_tbd(self):
        span = _section_span(self.text, '## Acknowledgements')
        self.assertNotIn('TBD', span)


class TestReadmeDemoTable(unittest.TestCase):
    """The README demo table covers every manifest set."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(README_PATH)
        cls.sets = _load_sets()

    def test_manifest_has_ten_sets(self):
        self.assertEqual(len(self.sets), 10)

    def test_every_manifest_set_appears(self):
        missing = [s['set_id'] for s in self.sets
                   if s['set_id'] not in self.text]
        self.assertEqual(missing, [], 'README is missing set ids: %r' % missing)

    def test_development_fixture_labelled(self):
        self.assertIn('development fixture', self.text)

    def test_data_sources_link_present(self):
        self.assertIn('docs/DATA_SOURCES.md', self.text)


class TestReadmeVibeWarning(unittest.TestCase):
    """README lines 1-2 retain the pinned vibe-coding warning byte-exactly."""

    @classmethod
    def setUpClass(cls):
        cls.lines = _read(README_PATH).splitlines()

    def test_line1_pinned_byte_exact(self):
        # The trailing space is deliberate (a Markdown hard-break).
        self.assertEqual(
            self.lines[0],
            '> This is a vibe-coding project. While the human attempt to '
            'verify the source of all ')
        self.assertTrue(self.lines[0].endswith(' '),
                        'line 1 lost its trailing hard-break space')

    def test_line2_pinned_byte_exact(self):
        self.assertEqual(
            self.lines[1],
            '> contents, if you find any issues please contact me.')


class TestDataSourcesCoverage(unittest.TestCase):
    """docs/DATA_SOURCES.md covers every bundled ligand and set."""

    @classmethod
    def setUpClass(cls):
        cls.doc = _read(DOCS_PATH)
        cls.sets = _load_sets()
        cls.ligands = sorted(
            name for name in os.listdir(LIGANDS_DIR) if name.endswith('.sdf'))

    def test_ligand_file_count(self):
        self.assertGreaterEqual(len(self.ligands), 1)
        self.assertEqual(len(self.ligands), 18)  # exact receipt

    def test_every_ligand_file_named(self):
        missing = [name for name in self.ligands
                   if ('ligands/%s' % name) not in self.doc]
        self.assertEqual(missing, [],
                         'DATA_SOURCES is missing ligand files: %r' % missing)

    def test_every_set_has_section(self):
        for entry in self.sets:
            set_id = entry['set_id']
            pattern = re.compile(r'^### %s\b' % re.escape(set_id),
                                 re.MULTILINE)
            self.assertIsNotNone(
                pattern.search(self.doc),
                'DATA_SOURCES is missing a %r section' % set_id)

    def test_curated_license_matches_verbatim_inside_section(self):
        # Expectations are derived FROM THE MANIFEST, never hardcoded lists.
        curated = [entry for entry in self.sets if entry['license']]
        self.assertEqual(len(curated), 9)  # 8 PubChem + the heme wwPDB set
        for entry in curated:
            span = _set_section_span(self.doc, entry['set_id'])
            self.assertIn(
                entry['license'], span,
                'license mismatch in the %r section' % entry['set_id'])


class TestVersionConsistency(unittest.TestCase):
    """aamatch/__init__.py metadata Version and __version__ agree."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(INIT_PATH)
        cls.first_lines = cls.text.splitlines()[:3]

    def test_metadata_block_stays_first(self):
        self.assertIn('# Version: 0.1.0', self.first_lines)

    def test_dunder_version_pinned(self):
        self.assertIn("__version__ = '0.1.0'", self.text)

    def test_parsed_versions_agree(self):
        meta = re.search(r'^#\s*Version:\s*(\S+)', self.text, re.MULTILINE)
        module = re.search(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]",
                           self.text, re.MULTILINE)
        self.assertIsNotNone(meta, 'metadata # Version: line not found')
        self.assertIsNotNone(module, '__version__ assignment not found')
        self.assertEqual(meta.group(1), module.group(1))


class TestTooltipPins(unittest.TestCase):
    """Load-bearing gameplay tooltips are pinned by source-text presence."""

    # Quoted verbatim from the LIVE sources at authoring time (09-10).
    GAME_WINDOW_PINS = (
        # Confirm -- the pass-gate button.
        'Attempt to finish this molecule: runs detection; it advances only '
        'when all required interactions are formed.',
        # Save -- the .aamz checkpoint.
        'Save the running game (PyMOL session + game state) to a checkpoint '
        'file.',
        # Import -- the one-button dispatch.
        'Load a saved checkpoint (.aamz) to resume playing, or an exported '
        'game file (.aamatch.json) to start it fresh.',
        # Hint.
        'Highlight the amino acids that could still form a required '
        'interaction (carbon recolor only).',
        # Skip / Give Up dropdown.
        'Skip the current molecule or give up the game (both ask for '
        'confirmation).',
    )
    SETUP_WINDOW_PINS = (
        # Browse -- the upload picker.
        'Pick an SDF or MOL2 molecule file (single file; a multi-record file '
        'provides several molecules).',
        # Cleanup tooltip fragment (true in both 09-05 branches).
        'game-generated object',
    )

    @classmethod
    def setUpClass(cls):
        cls.game_source = _joined_string_source(GAME_WINDOW_PATH)
        cls.setup_source = _joined_string_source(SETUP_WINDOW_PATH)

    def test_game_window_tooltips_present(self):
        for pin in self.GAME_WINDOW_PINS:
            self.assertIn(pin, self.game_source,
                          'missing game_window tooltip: %r' % pin)

    def test_setup_window_tooltips_present(self):
        for pin in self.SETUP_WINDOW_PINS:
            self.assertIn(pin, self.setup_source,
                          'missing setup_window tooltip: %r' % pin)


class TestSingleHomeWiring(unittest.TestCase):
    """The interaction strings read from help_text (09-07 single home)."""

    @classmethod
    def setUpClass(cls):
        cls.setup_text = _read(SETUP_WINDOW_PATH)

    def test_repoint_read_sites_present(self):
        for name in ('help_text.INTERACTION_LABELS',
                     'help_text.INTERACTION_TIPS',
                     'help_text.MODE_CONTEXT'):
            self.assertIn(name, self.setup_text,
                          'missing repoint read site: %s' % name)

    def test_old_private_dicts_gone(self):
        # Identifier-scoped prohibitions only (private names, not prose).
        self.assertNotIn('_INTERACTION_LABELS', self.setup_text)
        self.assertNotIn('_INTERACTION_TIPS', self.setup_text)
        self.assertNotIn('_MODE_CONTEXT', self.setup_text)


if __name__ == '__main__':
    unittest.main()
