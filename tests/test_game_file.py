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
import unittest

from aamatch import generator
from aamatch.game_file import (
    GAME_VERSION,
    UPLOAD_SET_ID,
    decode_ligand_files,
    encode_ligand_files,
    make_game_data,
    parse_game_data,
)
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


if __name__ == '__main__':
    unittest.main()
