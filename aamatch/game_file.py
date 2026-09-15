"""aamatch.game_file -- the shareable-game container (pure, 04-03).

Layer: PURE (builds on the Phase-1 persistence/level_spec/setup_state
pure foundation; stdlib base64/hashlib + pure siblings ONLY). No viewer
calls, no file I/O (persistence owns files; this module owns dicts), no
Qt -- unit-tested in WSL with bare python3.6, zero stubs.

ONE JSON file, kind='game' (reserved in persistence.KINDS): SETUP-08's
export output, Phase-7's import input. The FULL generator payload is
embedded VERBATIM as 'level_spec' -- THE TRUTH (embed-don't-regenerate
verdict, 04-RESEARCH-export-upload.md regenerate_vs_embed: manifest-
content dependence makes regeneration unstable, and uploaded molecule
bytes never exist on importer machines).

The data dict shape:

    {
      'game_format_version': GAME_VERSION,   # refuse-newer gate
      'created_at': <str>,                   # provenance, informational
      'generator': 'AA-match',               # provenance, informational
      'setup': {...},                        # validate_state output
      'seed': <int>,                         # DUPLICATE convenience of
                                             # level_spec['seed'] -- the
                                             # spec's is authoritative
      'level_spec': {...},                   # FULL payload, verbatim
      'ligand_files': {file_key: base64},    # UPLOADED molecules ONLY
    }

The TWO-sha256 rule (do not conflate): the payload molecule's
ligand.sha256 (and any manifest/upload-row hash, and this module's
integrity check below) is over the embedded RECORD TEXT -- what an
importer decodes and verifies. The SETUP field upload['sha256'] is over
the uploaded FILE as picked (04-06's split/row territory; noted here
for contrast only).

Versioning: game_format_version is a REFUSE-NEWER / accept-older gate
(additive-only evolution, .get defaults on read -- the
level_spec.py:106-114 pattern mirrored one layer up). detector_version
is NEVER mirrored at this layer: its single home is inside the embedded
spec, where parse_level_spec_dict enforces EXACT match (any mismatch --
stale or newer -- refuses; mirroring would invite drift, pitfall 11.3).

Parse gate chain (parse_game_data; Phase 7's import reuses it VERIFYBATIM):
1. persistence.check_container(container, 'game') -- foreign magic /
   newer container header / misfiled kind refused for free.
2. game_format_version gate (above).
3. setup re-validated via validate_state (idempotent, fail-closed).
4. level_spec re-parsed via
   parse_level_spec_dict(make_level_spec_container(...)) -- ALL Phase-1
   spec gates re-run with ZERO new code (refuse-newer format_version,
   exact-match detector_version, seed + structural minimums).
5. ligand integrity + source cross-checks: every ligand_files entry is
   base64-decoded; every source=='upload' molecule REQUIRES its
   ligand.file key in ligand_files (an uploaded game without its
   molecules is unsolvable); every source=='demo' molecule must NOT
   have an entry (bundled molecules are package-resolved, never
   embedded -- single meaning per source); sha256 of each decoded text
   must equal the matching payload molecule's ligand.sha256
   (64-char-lowercase-hex discipline, manifest.py:94-97); entries
   matching NO payload molecule key are refused (no dead weight).
"""

import base64
import hashlib

from .level_spec import make_level_spec_container, parse_level_spec_dict
from .persistence import FormatError, check_container
from .setup_state import validate_state

GAME_VERSION = 1          # payload gate: refuse-newer / accept-older
UPLOAD_SET_ID = 'uploaded'  # synthetic set_id for uploaded rows (04-06)


def make_game_data(setup, payload, ligand_files=None, created_at=''):
    """Build the `data` dict of a shareable-game container.

    `setup` is RE-VALIDATED via validate_state (idempotent, fail-closed,
    non-mutating). `payload` is the FULL generator payload (stamps,
    seed, levels) embedded VERBATIM -- never regenerated, never reduced.
    `ligand_files` is the ENCODED map ({file_key: base64 text}) returned
    by encode_ligand_files; bundled-demo-only games pass nothing.

    Returned key set is exactly: game_format_version, created_at,
    generator, setup, seed, level_spec, ligand_files. NO detector_version
    (single home inside the embedded spec); NO capability profiles
    (charge_signs is a set -- unserializable, and recomputable).
    """
    if not isinstance(payload, dict) or 'seed' not in payload:
        raise FormatError(
            "game data needs the full generator payload "
            "(a dict with at least 'seed'; found %s)"
            % type(payload).__name__)
    return {
        'game_format_version': GAME_VERSION,
        'created_at': created_at,
        'generator': 'AA-match',
        'setup': validate_state(setup),
        'seed': payload['seed'],
        'level_spec': payload,
        'ligand_files': dict(ligand_files) if ligand_files else {},
    }


def parse_game_data(container):
    """Validate a game-file container; return its three components.

    Runs the five-gate chain in the module docstring IN ORDER; every
    refusal is a FormatError naming the cause. Returns::

        {'setup': <validate_state output>,
         'payload': <the embedded level-spec payload, passthrough>,
         'ligand_texts': {file_key: decoded record text}}
    """
    container = check_container(container, 'game')
    data = container.get('data')
    if not isinstance(data, dict):
        data = {}

    version = data.get('game_format_version')
    if not isinstance(version, int) or isinstance(version, bool):
        raise FormatError(
            "game file data is missing or has an invalid "
            "'game_format_version'")
    if version > GAME_VERSION:
        raise FormatError(
            "unsupported game file version %d (expected <= %d). "
            "Please update AA-match." % (version, GAME_VERSION))

    if 'setup' not in data:
        raise FormatError("game file data is missing 'setup'")
    setup = validate_state(data['setup'])

    if 'level_spec' not in data:
        raise FormatError("game file data is missing 'level_spec'")
    payload = parse_level_spec_dict(
        make_level_spec_container(data['level_spec']))

    encoded = data.get('ligand_files', {})
    if not isinstance(encoded, dict):
        raise FormatError(
            "game file data has an invalid 'ligand_files' "
            "(expected a dict of file keys to base64 text, found %s)"
            % type(encoded).__name__)
    ligand_texts = decode_ligand_files(encoded)
    _check_ligand_integrity(payload, ligand_texts)

    return {'setup': setup, 'payload': payload,
            'ligand_texts': ligand_texts}


def encode_ligand_files(mapping):
    """Encode `{file_key: record_text}` as `{file_key: base64 str}`.

    Base64 of the UTF-8 record text keeps the container a single JSON
    file (laws of hand-editability + atomic writer; the ~33% inflation
    is immaterial at small-molecule record sizes).
    """
    return dict(
        (key, base64.b64encode(text.encode('utf-8')).decode('ascii'))
        for key, text in mapping.items())


def decode_ligand_files(mapping):
    """Inverse of encode_ligand_files: base64 str -> record text.

    A non-decodable entry raises FormatError naming the key (never a
    bare binascii/Unicode exception). Exported for Phase 7's import,
    which feeds the decoded map to the ligand_content seams (04-04).
    """
    texts = {}
    for key in sorted(mapping):
        try:
            raw = base64.b64decode(str(mapping[key]).encode('ascii'),
                                   validate=True)
            texts[key] = raw.decode('utf-8')
        except (ValueError, TypeError) as exc:
            # binascii.Error and UnicodeDecodeError both subclass
            # ValueError, so this one family covers garbage base64,
            # invalid UTF-8, and non-ascii-encodable strings.
            raise FormatError(
                "game file ligand_files entry %r is not valid base64 "
                "text (%s)" % (key, exc))
    return texts


def _check_ligand_integrity(payload, ligand_texts):
    """Gate 5: integrity + source cross-checks over the payload.

    Fail-closed .get traversal (never KeyError): every molecule's
    ligand.source is cross-checked against ligand_texts -- 'upload'
    requires content, 'demo' forbids it, and any present entry's
    sha256(decoded text) must equal the payload's ligand.sha256.
    Entries matching NO payload molecule key are refused last.
    """
    payload_keys = {}
    for level_index, level in enumerate(payload.get('levels') or []):
        molecules = level.get('molecules')
        if not isinstance(molecules, list):
            raise FormatError(
                "game file level %d is missing a 'molecules' list"
                % level_index)
        for mol_index, molecule in enumerate(molecules):
            ligand = molecule.get('ligand')
            if not isinstance(ligand, dict):
                raise FormatError(
                    "game file level %d molecule %d is missing a "
                    "'ligand' block" % (level_index, mol_index))
            source = ligand.get('source')
            file_key = ligand.get('file')
            molecule_id = ligand.get('entry_id')
            if source == 'upload' and file_key not in ligand_texts:
                raise FormatError(
                    "game file is missing embedded content for "
                    "uploaded molecule %r (key %r)"
                    % (molecule_id, file_key))
            if source == 'demo' and file_key in ligand_texts:
                raise FormatError(
                    "game file embeds content for bundled molecule %r "
                    "(key %r) -- bundled molecules are package-resolved, "
                    "never embedded" % (molecule_id, file_key))
            if file_key in ligand_texts:
                digest = hashlib.sha256(
                    ligand_texts[file_key].encode('utf-8')).hexdigest()
                expected = ligand.get('sha256')
                if digest != expected:
                    raise FormatError(
                        "game file ligand content %r sha256 mismatch "
                        "(embedded content hashes %s, payload records %s)"
                        % (file_key, digest, expected))
            payload_keys[file_key] = source
    for key in sorted(ligand_texts):
        if key not in payload_keys:
            raise FormatError(
                "game file embeds unused ligand content %r" % (key,))
