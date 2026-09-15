"""Unit tests for aamatch.game_file -- the shareable-game container (04-03).

The game file is SETUP-08's output and Phase-7's import input: ONE JSON
container (kind='game', already reserved in persistence.KINDS) whose data
embeds the FULL generator payload VERBATIM as truth (embed-don't-
regenerate verdict, 04-RESEARCH-export-upload.md regenerate_vs_embed), a
validated setup snapshot, and base64 ligand_files for uploaded molecules
only.

Gate chain under test (all refusals FormatError with pinned messages):
1. persistence.check_container(container, 'game') -- foreign magic /
   newer container header / misfiled kind come for free.
2. game_format_version: refuse-newer / accept-older (missing or non-int
   refused; 0 accepted as the positive control for accept-older).
3. setup re-validated via validate_state.
4. embedded level spec re-runs ALL Phase-1 gates via
   parse_level_spec_dict(make_level_spec_container(...)) -- incl. the
   exact-match detector_version stamp ("stale or newer game spec ...").
5. ligand integrity + source cross-checks: every source=='upload'
   molecule REQUIRES its ligand.file key in ligand_files; every
   source=='demo' molecule must NOT have one (single meaning per
   source); sha256 of the decoded text must equal the payload molecule's
   ligand.sha256; entries matching no payload molecule are refused.

TDD: this file lands BEFORE aamatch/game_file.py (RED); the fixture
recipe (candidate rows + ligand_data with a hand-built capability
profile) is copied from tests/test_generator.py's payload builders.

Runs under bare python3.6, stdlib only, zero stubs.
"""

import base64
import copy
import hashlib
import json
import os
import tempfile
import unittest

from aamatch import game_file
from aamatch import generator
from aamatch.game_file import (
    GAME_VERSION,
    UPLOAD_SET_ID,
    decode_ligand_files,
    encode_ligand_files,
    make_game_data,
    parse_game_data,
)
from aamatch.manifest import REQUIRED_ENTRY_KEYS
from aamatch.persistence import FormatError, make_container
from aamatch.setup_state import INTERACTION_TYPES, validate_state


# ---------------------------------------------------------------------------
# Fixtures -- copied from tests/test_generator.py's Task-3 payload builders.
# ---------------------------------------------------------------------------

SET_ID = 'demo-dev-1'


def _rich_profile():
    """Hand-built capability.ligand_profile shape: every feature on, so
    all 7 interaction types are supportable (test_generator.py RICH)."""
    return {
        'has_donor': True,
        'has_acceptor': True,
        'charge_signs': {'+', '-'},      # a SET (input-side only)
        'ring_count': 2,
        'has_hydrophobe': True,
        'has_halogen_donor': True,
        'has_metal': True,
    }


def _candidate(entry_id, size_class='small', protonation='as-recorded',
               **over):
    """One manifest-shaped candidate row (enumerate_entries shape)."""
    heavy = {'small': 9, 'medium': 40, 'large': 80}[size_class]
    row = {
        'set_id': SET_ID,
        'entry_id': entry_id,
        'file': 'ligands/%s.sdf' % entry_id,
        'format': 'sdf',
        'sha256': 'a' * 64,
        'protonation': protonation,
        'atom_count': heavy + 7,
        'heavy_atom_count': heavy,
        'bond_count': heavy + 7,
        'bond_order_counts': {'1': 12, '2': 4},
        'formal_charge_sum': 0,
        'states_expected': 1,
        'metal_present': False,
        'halogen_present': False,
        'size_class': size_class,
    }
    row.update(over)
    return row


RICH = _rich_profile()

CANDIDATES = sorted([
    _candidate('acetate'),
    _candidate('benzamide'),
    _candidate('toluene'),
    _candidate('naphthalene', 'medium'),
    _candidate('anthracene', 'medium'),
    _candidate('coronene', 'large'),
], key=lambda c: (c['set_id'], c['entry_id']))

LIGAND_DATA = dict(
    ((c['set_id'], c['entry_id']),
     {'centroid': (0.0, 0.0, 0.0), 'radius': 4.0, 'profile': RICH})
    for c in CANDIDATES)

# A fake uploaded SDF record: the importer never parses it here (sha256
# over the RECORD TEXT is the only integrity arrow), so plain text is a
# faithful stand-in.
UPLOAD_FILE_KEY = 'uploads/mol-001.sdf'
UPLOAD_RECORD_TEXT = ('mol-001\n  AA-match upload fixture\n\n'
                      'fake sdf record body\n$$$$\n')


def make_setup(molecules=1, difficulty=2):
    """A validated setup_state dict (the generator's real input shape)."""
    return validate_state({
        'interaction_mode': 'unset',
        'allowed_interactions': list(INTERACTION_TYPES),
        'molecules_per_level': molecules,
        'difficulty_levels': difficulty,
    })


def make_payload(seed=42, molecules=1, difficulty=2):
    """(setup, payload): a REAL generator.generate payload for tests."""
    setup = make_setup(molecules, difficulty)
    payload = generator.generate(
        seed, setup, CANDIDATES, LIGAND_DATA, difficulty)
    return setup, payload


def make_valid_container(setup=None, payload=None, ligand_files=None,
                         created_at=''):
    """(container, data, setup, payload) for a well-formed game file."""
    if setup is None or payload is None:
        setup, payload = make_payload()
    data = make_game_data(setup, payload, ligand_files=ligand_files,
                          created_at=created_at)
    return make_container('game', data), data, setup, payload


def restamp_first_molecule_uploaded(payload, file_key=UPLOAD_FILE_KEY,
                                    record_text=UPLOAD_RECORD_TEXT):
    """Deep-copy `payload` with molecule 0 re-stamped as an uploaded
    molecule: source='upload', set_id=UPLOAD_SET_ID, synthetic file key,
    sha256 over the embedded RECORD TEXT (the two-sha256 rule)."""
    payload = copy.deepcopy(payload)
    ligand = payload['levels'][0]['molecules'][0]['ligand']
    ligand['source'] = 'upload'
    ligand['set_id'] = UPLOAD_SET_ID
    ligand['file'] = file_key
    ligand['sha256'] = hashlib.sha256(
        record_text.encode('utf-8')).hexdigest()
    return payload


class TestMakeShape(unittest.TestCase):
    """make_game_data: exact key set, stamps, embed-don't-regenerate."""

    def test_make_shape(self):
        setup, payload = make_payload()
        data = make_game_data(setup, payload, created_at='2026-09-16')
        self.assertEqual(
            sorted(data),
            ['created_at', 'game_format_version', 'generator',
             'level_spec', 'ligand_files', 'seed', 'setup'])
        self.assertEqual(data['game_format_version'], GAME_VERSION)
        self.assertEqual(GAME_VERSION, 1)
        self.assertEqual(UPLOAD_SET_ID, 'uploaded')
        self.assertEqual(data['created_at'], '2026-09-16')
        self.assertEqual(data['generator'], 'AA-match')
        self.assertEqual(data['seed'], payload['seed'])
        self.assertIs(data['level_spec'], payload)  # verbatim embed
        self.assertEqual(data['ligand_files'], {})
        self.assertEqual(data['setup'], setup)      # already validated
        # THE mirroring ban: detector_version lives ONLY inside the
        # embedded spec -- never at the game layer (drift pitfall 11.3).
        self.assertNotIn('detector_version', data)

    def test_setup_is_re_validated_and_input_never_mutated(self):
        setup, payload = make_payload()
        raw = dict(setup)
        raw['molecules_per_level'] = 999   # clamps to the frozen cap
        raw['nonschema'] = 'dropped'
        raw_snapshot = copy.deepcopy(raw)
        data = make_game_data(raw, payload)
        self.assertEqual(data['setup'], validate_state(raw))
        self.assertNotIn('nonschema', data['setup'])
        self.assertEqual(raw, raw_snapshot)  # P6: input never mutated

    def test_default_created_at_and_ligand_files(self):
        setup, payload = make_payload()
        data = make_game_data(setup, payload)
        self.assertEqual(data['created_at'], '')
        self.assertEqual(data['ligand_files'], {})


class TestRoundTrip(unittest.TestCase):
    """make -> container -> (JSON bytes) -> parse: setup + payload +
    ligand texts all round-trip. Demo-only games embed NO ligand files."""

    def test_round_trip(self):
        container, data, setup, payload = make_valid_container()
        # The real save path is byte-stable JSON (persistence writer);
        # an in-memory json round-trip proves serializability + equality.
        reloaded = json.loads(json.dumps(container, sort_keys=True))
        parsed = parse_game_data(reloaded)
        self.assertEqual(sorted(parsed),
                         ['ligand_texts', 'payload', 'setup'])
        self.assertEqual(parsed['setup'], validate_state(setup))
        # Byte-identical determinism precedent
        # (tests/test_generator.py:791-810): the embedded payload comes
        # back EXACTLY -- parse is passthrough, gates re-run.
        self.assertEqual(parsed['payload'], payload)
        self.assertEqual(
            json.dumps(parsed['payload'], sort_keys=True),
            json.dumps(payload, sort_keys=True))
        self.assertEqual(parsed['ligand_texts'], {})


class TestRoundTripWithUploadedLigand(unittest.TestCase):
    """An uploaded molecule carries its RECORD TEXT in ligand_files;
    parse decodes it and sha256-verifies it against the payload."""

    def test_round_trip_uploaded(self):
        setup, payload = make_payload()
        payload = restamp_first_molecule_uploaded(payload)
        ligand_files = encode_ligand_files(
            {UPLOAD_FILE_KEY: UPLOAD_RECORD_TEXT})
        data = make_game_data(setup, payload, ligand_files=ligand_files)
        # The stored map is base64, the record text itself is NOT stored.
        self.assertEqual(data['ligand_files'][UPLOAD_FILE_KEY],
                         base64.b64encode(
                             UPLOAD_RECORD_TEXT.encode('utf-8')
                         ).decode('ascii'))
        reloaded = json.loads(json.dumps(make_container('game', data),
                                         sort_keys=True))
        parsed = parse_game_data(reloaded)
        self.assertEqual(parsed['ligand_texts'],
                         {UPLOAD_FILE_KEY: UPLOAD_RECORD_TEXT})
        self.assertEqual(parsed['payload'], payload)
        self.assertEqual(parsed['setup'], setup)


class TestRefusals(unittest.TestCase):
    """Every refusal class: FormatError with a message naming the cause."""

    def test_foreign_magic_refused(self):
        container, data, _, _ = make_valid_container()
        bad = dict(container)
        bad['magic'] = 'NOTAAM'
        with self.assertRaises(FormatError) as ctx:
            parse_game_data(bad)
        self.assertIn('not an AA-match file', str(ctx.exception))

    def test_newer_container_header_refused(self):
        container, data, _, _ = make_valid_container()
        bad = dict(container)
        bad['version'] = 99
        with self.assertRaises(FormatError) as ctx:
            parse_game_data(bad)
        self.assertIn('unsupported AA-match format version',
                      str(ctx.exception))
        self.assertIn('Please update AA-match.', str(ctx.exception))

    def test_misfiled_kind_refused(self):
        _, data, _, _ = make_valid_container()
        bad = make_container('setup', data)   # game data in a setup box
        with self.assertRaises(FormatError) as ctx:
            parse_game_data(bad)
        self.assertIn('expected an AA-match game file',
                      str(ctx.exception))

    def _container_with_data_edit(self, edit):
        """Valid container with `edit(data)` applied in place."""
        container, data, setup, payload = make_valid_container()
        edit(data)
        return container

    def test_game_format_version_missing_refused(self):
        container = self._container_with_data_edit(
            lambda d: d.pop('game_format_version'))
        with self.assertRaises(FormatError) as ctx:
            parse_game_data(container)
        self.assertEqual(
            "game file data is missing or has an invalid "
            "'game_format_version'", str(ctx.exception))

    def test_game_format_version_non_int_refused(self):
        container = self._container_with_data_edit(
            lambda d: d.update(game_format_version='two'))
        with self.assertRaises(FormatError) as ctx:
            parse_game_data(container)
        self.assertEqual(
            "game file data is missing or has an invalid "
            "'game_format_version'", str(ctx.exception))

    def test_newer_game_format_version_refused_with_exact_message(self):
        container = self._container_with_data_edit(
            lambda d: d.update(game_format_version=2))
        with self.assertRaises(FormatError) as ctx:
            parse_game_data(container)
        self.assertEqual(
            'unsupported game file version 2 (expected <= 1). '
            'Please update AA-match.', str(ctx.exception))

    def test_older_game_format_version_accepted(self):
        # Positive control for accept-older (additive-only evolution).
        container = self._container_with_data_edit(
            lambda d: d.update(game_format_version=0))
        parsed = parse_game_data(container)
        self.assertIn('payload', parsed)

    def test_missing_setup_refused(self):
        container = self._container_with_data_edit(
            lambda d: d.pop('setup'))
        with self.assertRaises(FormatError) as ctx:
            parse_game_data(container)
        self.assertEqual("game file data is missing 'setup'",
                         str(ctx.exception))

    def test_missing_level_spec_refused(self):
        container = self._container_with_data_edit(
            lambda d: d.pop('level_spec'))
        with self.assertRaises(FormatError) as ctx:
            parse_game_data(container)
        self.assertEqual("game file data is missing 'level_spec'",
                         str(ctx.exception))

    def test_stale_detector_version_in_embedded_spec_refused(self):
        setup, payload = make_payload()
        payload = copy.deepcopy(payload)
        payload['detector_version'] = 'det-0'   # re-stamp (02-15:82)
        container = make_container(
            'game', make_game_data(setup, payload))
        with self.assertRaises(FormatError) as ctx:
            parse_game_data(container)
        self.assertIn(
            'stale or newer game spec - regenerate it with a current '
            'AA-match generator', str(ctx.exception))

    def test_uploaded_molecule_without_embedded_content_refused(self):
        setup, payload = make_payload()
        payload = restamp_first_molecule_uploaded(payload)
        container = make_container('game', make_game_data(setup, payload))
        with self.assertRaises(FormatError) as ctx:
            parse_game_data(container)
        self.assertIn('game file is missing embedded content for '
                      'uploaded molecule', str(ctx.exception))
        self.assertIn(repr(UPLOAD_FILE_KEY), str(ctx.exception))

    def test_demo_molecule_with_embedded_content_refused(self):
        setup, payload = make_payload()
        file_key = payload['levels'][0]['molecules'][0]['ligand']['file']
        ligand_files = encode_ligand_files({file_key: 'some text\n'})
        container = make_container(
            'game', make_game_data(setup, payload,
                                   ligand_files=ligand_files))
        with self.assertRaises(FormatError) as ctx:
            parse_game_data(container)
        self.assertIn('game file embeds content for bundled molecule',
                      str(ctx.exception))
        self.assertIn('-- bundled molecules are package-resolved, '
                      'never embedded', str(ctx.exception))
        self.assertIn(repr(file_key), str(ctx.exception))

    def test_sha256_mismatch_refused_naming_file_and_hashes(self):
        setup, payload = make_payload()
        payload = restamp_first_molecule_uploaded(payload)
        ligand = payload['levels'][0]['molecules'][0]['ligand']
        wrong = 'b' * 64
        ligand['sha256'] = wrong
        real = hashlib.sha256(
            UPLOAD_RECORD_TEXT.encode('utf-8')).hexdigest()
        ligand_files = encode_ligand_files(
            {UPLOAD_FILE_KEY: UPLOAD_RECORD_TEXT})
        container = make_container(
            'game', make_game_data(setup, payload,
                                   ligand_files=ligand_files))
        with self.assertRaises(FormatError) as ctx:
            parse_game_data(container)
        message = str(ctx.exception)
        self.assertIn(repr(UPLOAD_FILE_KEY), message)
        self.assertIn(wrong, message)
        self.assertIn(real, message)

    def test_unused_ligand_files_entry_refused(self):
        setup, payload = make_payload()
        ligand_files = encode_ligand_files({'uploads/ghost.sdf': 'x\n'})
        container = make_container(
            'game', make_game_data(setup, payload,
                                   ligand_files=ligand_files))
        with self.assertRaises(FormatError) as ctx:
            parse_game_data(container)
        self.assertEqual("game file embeds unused ligand content "
                         "'uploads/ghost.sdf'", str(ctx.exception))

    def test_bad_base64_refused_naming_the_key(self):
        setup, payload = make_payload()
        container = make_container(
            'game', make_game_data(
                setup, payload,
                ligand_files={UPLOAD_FILE_KEY: '!!!not-base64!!!'}))
        with self.assertRaises(FormatError) as ctx:
            parse_game_data(container)
        self.assertIn(UPLOAD_FILE_KEY, str(ctx.exception))
        self.assertIn('base64', str(ctx.exception))


class TestEncodeDecodeLigandFiles(unittest.TestCase):
    """base64 codec: round-trip and garbage refusal (Phase-7 reuses
    decode_ligand_files for import; exported for exactly that seam)."""

    def test_round_trip(self):
        mapping = {
            'uploads/mol-001.sdf': UPLOAD_RECORD_TEXT,
            'uploads/mol-002.mol2': '@<TRIPOS>MOLECULE\nfake segment\n',
        }
        encoded = encode_ligand_files(mapping)
        for key, value in encoded.items():
            self.assertIsInstance(value, str)
            raw = base64.b64decode(value.encode('ascii'), validate=True)
            self.assertEqual(raw.decode('utf-8'), mapping[key])
        self.assertEqual(decode_ligand_files(encoded), mapping)

    def test_decode_garbage_refused_naming_the_key(self):
        with self.assertRaises(FormatError) as ctx:
            decode_ligand_files({'uploads/ghost.sdf': '@@@broken@@@'})
        self.assertIn("'uploads/ghost.sdf'", str(ctx.exception))
        self.assertIn('base64', str(ctx.exception))


# ---------------------------------------------------------------------------
# 04-06 fixtures: hand-built minimal SDF / MOL2 upload strings. The pure
# split/supply/row helpers work on STRINGS ONLY (record parsing is the cmd
# tier's, 04-08), so these fixtures are shape-plausible text, not chemistry.
# ---------------------------------------------------------------------------

SDF_RECORD_1 = (
    'rec-001\n'
    '  AA-match upload fixture\n'
    '\n'
    '  3  2  0  0  0  0            999 V2000\n'
    '    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0\n'
    '    1.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0\n'
    '    0.0000    1.0000    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0\n'
    '  1  2  2  0  0  0  0\n'
    '  1  3  1  0  0  0  0\n'
    'M  END\n'
    '$$$$\n')

SDF_RECORD_2 = (
    'rec-002\n'
    '  AA-match upload fixture\n'
    '\n'
    '  1  1  0  0  0  0            999 V2000\n'
    '    0.0000    0.0000    0.0000 N   0  0  0  0  0  0  0  0  0  0  0  0\n'
    '  1  1  1  0  0  0  0\n'
    'M  END\n'
    '$$$$\n')

SDF_TWO_RECORDS = SDF_RECORD_1 + SDF_RECORD_2

MOL2_TWO_SEGMENTS = (
    '# comment before the first block\n'
    '@<TRIPOS>MOLECULE\n'
    'SEG-001\n'
    '@<TRIPOS>ATOM\n'
    '      1 C1    0.0000    0.0000    0.0000 C.2    1 RES1    0.0000\n'
    '@<TRIPOS>BOND\n'
    '@<TRIPOS>MOLECULE\n'
    'SEG-002\n'
    '@<TRIPOS>ATOM\n'
    '      1 N1    0.0000    0.0000    0.0000 N.3    1 RES1    0.0000\n')

ROW_ATOMS = [
    {'elem': 'C', 'formal_charge': 1},
    {'elem': 'O', 'formal_charge': -1},
    {'elem': 'H'},                       # missing key counts 0
]
ROW_BONDS = [(0, 1, 2.0), (1, 2, 1.0)]
ROW_PROFILE = {
    'has_donor': False,
    'has_acceptor': True,
    'charge_signs': set(),               # a SET (input-side only)
    'ring_count': 0,
    'has_hydrophobe': True,
    'has_halogen_donor': False,
    'has_metal': True,
}


class TestSplitSdfRecords(unittest.TestCase):
    """split_sdf_records: '$$$$'-line splitting, CRLF byte-stability."""

    def test_two_records_split_each_carrying_its_terminator(self):
        records = game_file.split_sdf_records(SDF_TWO_RECORDS)
        self.assertEqual(records, [SDF_RECORD_1, SDF_RECORD_2])
        for record in records:
            self.assertTrue(record.endswith('$$$$\n'))

    def test_single_record_without_terminator(self):
        text = 'lone record\nno ' + '$$$$' + ' terminator here\n'
        self.assertEqual(game_file.split_sdf_records(text), [text])

    def test_whitespace_only_returns_empty(self):
        self.assertEqual(game_file.split_sdf_records('  \n\t \n'), [])

    def test_trailing_blank_tail_dropped(self):
        records = game_file.split_sdf_records(SDF_TWO_RECORDS + '\n  \t\n\n')
        self.assertEqual(records, [SDF_RECORD_1, SDF_RECORD_2])

    def test_crlf_splits_byte_stably(self):
        def crlf(text):
            return text.replace('\n', '\r\n')
        records = game_file.split_sdf_records(crlf(SDF_TWO_RECORDS))
        self.assertEqual(records, [crlf(SDF_RECORD_1), crlf(SDF_RECORD_2)])
        for record in records:
            self.assertTrue(record.endswith('$$$$\r\n'))
            self.assertIn('\r\n', record)


class TestSplitMol2Segments(unittest.TestCase):
    """split_mol2_segments: column-0 @<TRIPOS>MOLECULE boundaries."""

    def test_two_segments_leading_comment_attaches_to_first(self):
        segments = game_file.split_mol2_segments(MOL2_TWO_SEGMENTS)
        self.assertEqual(len(segments), 2)
        self.assertIn('# comment before the first block\n', segments[0])
        self.assertIn('@<TRIPOS>MOLECULE\n', segments[0])
        self.assertTrue(segments[1].startswith('@<TRIPOS>MOLECULE'))

    def test_single_segment(self):
        text = '@<TRIPOS>MOLECULE\nSEG-001\n@<TRIPOS>ATOM\n'
        self.assertEqual(game_file.split_mol2_segments(text), [text])

    def test_no_keyword_returns_text_or_empty(self):
        text = 'no keyword here\njust text\n'
        self.assertEqual(game_file.split_mol2_segments(text), [text])
        self.assertEqual(game_file.split_mol2_segments(' \n\t \n'), [])


class TestCheckUploadSupply(unittest.TestCase):
    """check_upload_supply: zero/empty/over-cap refusals (silent None
    when usable). Messages name the file and the record index."""

    def test_zero_records_refused(self):
        with self.assertRaises(FormatError) as ctx:
            game_file.check_upload_supply([], 'sdf', 'set.sdf')
        self.assertEqual(
            "upload 'set.sdf' contains 0 sdf records -- nothing to "
            "play with", str(ctx.exception))

    def test_blank_record_refused_naming_index(self):
        with self.assertRaises(FormatError) as ctx:
            game_file.check_upload_supply(['ok\n', '  \n'], 'sdf',
                                          'set.sdf')
        self.assertEqual(
            "upload 'set.sdf' record 2 is empty -- remove it and retry",
            str(ctx.exception))

    def test_over_cap_refused_with_perf_rationale(self):
        records = ['rec\n'] * (game_file.UPLOAD_MAX_RECORDS + 1)
        with self.assertRaises(FormatError) as ctx:
            game_file.check_upload_supply(records, 'sdf', 'set.sdf')
        self.assertEqual(
            "upload 'set.sdf' carries 51 records -- the v1 cap is 50 "
            "(generation temp-loads every molecule per generate); "
            "split the set or reduce it", str(ctx.exception))

    def test_exactly_cap_passes(self):
        records = ['rec\n'] * game_file.UPLOAD_MAX_RECORDS
        self.assertIsNone(
            game_file.check_upload_supply(records, 'sdf', 'set.sdf'))

    def test_single_record_passes(self):
        self.assertIsNone(
            game_file.check_upload_supply(['rec\n'], 'mol2', 'set.mol2'))

    def test_cap_value_is_50(self):
        self.assertEqual(game_file.UPLOAD_MAX_RECORDS, 50)


class TestReadUploadSource(unittest.TestCase):
    """read_upload_source: (text, FILE sha256, format) with fail-closed
    format + decode refusals. The two-sha256 rule is under test: this is
    the FILE hash (Decision 19); row hashes are over record text."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix='aamatch_upload_')
        self.paths = {}

        def plant(name, payload):
            path = os.path.join(self.tmpdir, name)
            with open(path, 'wb') as handle:
                handle.write(payload)
            self.paths[name] = path

        plant('fixture.sdf', SDF_RECORD_1.encode('utf-8'))
        plant('fixture.MOL2', MOL2_TWO_SEGMENTS.encode('utf-8'))
        plant('fixture.pdb', b'ATOM      1  C   LIG     1\n')
        plant('broken.sdf',
              b'\xff\xfe binary garbage that is not utf-8 \x80\x81')

    def tearDown(self):
        for path in self.paths.values():
            os.remove(path)
        os.rmdir(self.tmpdir)

    def test_sdf_returns_text_file_sha_and_format(self):
        text, sha, fmt = game_file.read_upload_source(
            self.paths['fixture.sdf'])
        self.assertEqual(text, SDF_RECORD_1)
        self.assertEqual(fmt, 'sdf')
        self.assertEqual(sha, hashlib.sha256(
            SDF_RECORD_1.encode('utf-8')).hexdigest())

    def test_uppercase_extension_lowercased(self):
        text, sha, fmt = game_file.read_upload_source(
            self.paths['fixture.MOL2'])
        self.assertEqual(fmt, 'mol2')
        self.assertEqual(text, MOL2_TWO_SEGMENTS)
        self.assertEqual(sha, hashlib.sha256(
            MOL2_TWO_SEGMENTS.encode('utf-8')).hexdigest())

    def test_pdb_refused_with_pinned_message(self):
        with self.assertRaises(FormatError) as ctx:
            game_file.read_upload_source(self.paths['fixture.pdb'])
        self.assertEqual(
            "unsupported upload format '.pdb' (expected .sdf or .mol2) "
            "-- PDB is not supported (no reliable bond orders)",
            str(ctx.exception))

    def test_non_utf8_refused_with_pinned_message(self):
        with self.assertRaises(FormatError) as ctx:
            game_file.read_upload_source(self.paths['broken.sdf'])
        self.assertEqual(
            "could not decode %r as UTF-8" % self.paths['broken.sdf'],
            str(ctx.exception))


class TestBuildUploadedRowShape(unittest.TestCase):
    """build_uploaded_row: manifest-shaped row + 'set_id' + 'title',
    synthetic identity keys, record-text sha256, profile projection."""

    def _row(self, index=0, fmt='sdf', record_text=SDF_RECORD_1):
        return game_file.build_uploaded_row(
            ROW_ATOMS, ROW_BONDS, ROW_PROFILE, record_text, fmt, index)

    def test_key_set_is_manifest_keys_plus_set_id_and_title(self):
        row = self._row()
        self.assertEqual(
            sorted(row),
            sorted(list(REQUIRED_ENTRY_KEYS) + ['set_id', 'title']))
        self.assertEqual(row['set_id'], UPLOAD_SET_ID)
        self.assertEqual(UPLOAD_SET_ID, 'uploaded')

    def test_synthetic_identity_keys(self):
        row = self._row(index=0)
        self.assertEqual(row['entry_id'], 'mol-001')
        self.assertEqual(row['file'], 'uploads/mol-001.sdf')
        self.assertEqual(row['format'], 'sdf')
        row2 = self._row(index=1, fmt='mol2')
        self.assertEqual(row2['entry_id'], 'mol-002')
        self.assertEqual(row2['file'], 'uploads/mol-002.mol2')
        self.assertEqual(row2['format'], 'mol2')

    def test_sha256_over_record_text(self):
        row = self._row()
        self.assertEqual(
            row['sha256'],
            hashlib.sha256(SDF_RECORD_1.encode('utf-8')).hexdigest())

    def test_counts_and_profile_projection(self):
        row = self._row()
        self.assertEqual(row['atom_count'], 3)
        self.assertEqual(row['heavy_atom_count'], 2)
        self.assertEqual(row['bond_count'], 2)
        self.assertEqual(row['bond_order_counts'], {'2': 1, '1': 1})
        self.assertEqual(row['formal_charge_sum'], 0)
        self.assertEqual(row['states_expected'], 1)
        self.assertEqual(row['protonation'], 'as-recorded')
        self.assertIs(row['metal_present'], True)
        self.assertIs(row['halogen_present'], False)
        self.assertEqual(
            row['size_class'],
            generator._candidate_class({'heavy_atom_count': 2}))
        self.assertEqual(row['title'], 'rec-001')

    def test_blank_title_line_yields_empty_title(self):
        row = self._row(record_text='\nblank title line\nM  END\n$$$$\n')
        self.assertEqual(row['title'], '')


class TestValidateUploadedRows(unittest.TestCase):
    """validate_uploaded_rows: fail-closed set_id/entry_id guards, then
    the manifest's OWN dict-level entry rules (single home), including
    the absolute / backslash / drive-letter path refusals."""

    def _rows(self):
        return [
            game_file.build_uploaded_row(
                ROW_ATOMS, ROW_BONDS, ROW_PROFILE, SDF_RECORD_1, 'sdf', 0),
            game_file.build_uploaded_row(
                ROW_ATOMS, ROW_BONDS, ROW_PROFILE, SDF_RECORD_2, 'sdf', 1),
        ]

    def test_built_rows_pass(self):
        self.assertIsNone(game_file.validate_uploaded_rows(self._rows()))

    def test_missing_set_id_refused(self):
        rows = self._rows()
        del rows[0]['set_id']
        with self.assertRaises(FormatError) as ctx:
            game_file.validate_uploaded_rows(rows)
        self.assertEqual(
            "uploaded row 1 must carry 'set_id' 'uploaded' "
            "(which construction guarantees -- found None)",
            str(ctx.exception))

    def test_wrong_set_id_refused(self):
        rows = self._rows()
        rows[1]['set_id'] = 'demo-easy-1'
        with self.assertRaises(FormatError) as ctx:
            game_file.validate_uploaded_rows(rows)
        self.assertEqual(
            "uploaded row 2 must carry 'set_id' 'uploaded' "
            "(which construction guarantees -- found 'demo-easy-1')",
            str(ctx.exception))

    def test_empty_entry_id_refused(self):
        rows = self._rows()
        rows[0]['entry_id'] = ''
        with self.assertRaises(FormatError) as ctx:
            game_file.validate_uploaded_rows(rows)
        self.assertEqual(
            "uploaded row 1 must carry a non-empty 'entry_id' string "
            "(which construction guarantees -- found '')",
            str(ctx.exception))

    def test_absolute_file_refused(self):
        rows = self._rows()
        rows[0]['file'] = '/abs/x.sdf'
        with self.assertRaises(FormatError) as ctx:
            game_file.validate_uploaded_rows(rows)
        self.assertIn('absolute', str(ctx.exception))
        self.assertIn(repr('/abs/x.sdf'), str(ctx.exception))

    def test_backslash_file_refused(self):
        rows = self._rows()
        rows[0]['file'] = 'x\\y.sdf'
        with self.assertRaises(FormatError) as ctx:
            game_file.validate_uploaded_rows(rows)
        self.assertIn('forward slashes', str(ctx.exception))

    def test_windows_drive_file_refused(self):
        rows = self._rows()
        rows[0]['file'] = 'C:/x.sdf'          # forward slash + drive
        with self.assertRaises(FormatError) as ctx:
            game_file.validate_uploaded_rows(rows)
        self.assertIn('drive', str(ctx.exception))
        # The backslash drive form is refused too (backslash branch).
        rows[0]['file'] = 'C:\\x.sdf'
        with self.assertRaises(FormatError):
            game_file.validate_uploaded_rows(rows)

    def test_not_a_dict_row_refused(self):
        with self.assertRaises(FormatError) as ctx:
            game_file.validate_uploaded_rows(['not-a-dict'])
        self.assertIn('set_id', str(ctx.exception))


class TestValidateDelegationAdapter(unittest.TestCase):
    """Task 3 pin: validate_uploaded_rows is a thin adapter over the
    manifest's OWN entry rules -- a valid row passes through unchanged
    and a broken row surfaces the manifest's own message text (never a
    re-implemented rule)."""

    def _row(self):
        return game_file.build_uploaded_row(
            ROW_ATOMS, ROW_BONDS, ROW_PROFILE, SDF_RECORD_1, 'sdf', 0)

    def test_valid_row_passes_through_unchanged(self):
        row = self._row()
        before = copy.deepcopy(row)
        self.assertIsNone(game_file.validate_uploaded_rows([row]))
        self.assertEqual(row, before)          # never mutated (P6)

    def test_broken_bond_order_counts_surfaces_manifest_message(self):
        row = self._row()
        row['bond_order_counts'] = {'1': 0}    # value must be > 0
        with self.assertRaises(FormatError) as ctx:
            game_file.validate_uploaded_rows([row])
        message = str(ctx.exception)
        # The manifest's OWN message shape, with its set/entry context:
        self.assertIn(
            "'bond_order_counts' values must be positive ints", message)
        self.assertIn("manifest set 'uploaded' entry 0", message)
        self.assertIn("entry_id='mol-001'", message)

    def test_non_digit_bond_order_key_surfaces_manifest_message(self):
        row = self._row()
        row['bond_order_counts'] = {'None': 1}  # unrecognized order
        with self.assertRaises(FormatError) as ctx:
            game_file.validate_uploaded_rows([row])
        self.assertIn(
            "'bond_order_counts' keys must be digit strings",
            str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
