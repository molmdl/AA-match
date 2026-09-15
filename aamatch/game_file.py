"""aamatch.game_file -- the shareable-game container (pure, 04-03/04-06).

Layer: PURE (builds on the Phase-1 persistence/level_spec/setup_state
pure foundation; stdlib base64/hashlib/os + pure siblings ONLY). No
viewer calls, no Qt -- unit-tested in WSL with bare python3.6, zero
stubs. 04-03's half owns the container dicts; 04-06's half adds the
UPLOAD-SIDE pure surface (SETUP-03, research 04-RESEARCH-export-upload
upload_pipeline + multi_record_rules): format-aware splitting, supply
checks, file reading with sha256 + format detection, the manifest-shaped
uploaded-row builder, and row validation. Everything below the 04-06,
part-2 marker is pure string/dict work except read_upload_source's
deliberate small stdlib-open file read (the same I/O persistence
performs -- pure layer, no viewer calls).

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
import os

from . import manifest
from .capability import _bond_order_int
from .generator import _candidate_class
from .level_spec import make_level_spec_container, parse_level_spec_dict
from .persistence import FormatError, check_container
from .setup_state import validate_state

GAME_VERSION = 1          # payload gate: refuse-newer / accept-older
UPLOAD_SET_ID = 'uploaded'  # synthetic set_id for uploaded rows (04-06)
# Decision 8 (04-DECISIONS): one temp-load extraction per candidate row
# per Generate (engine.py:220-223) -- an uncapped upload would run that
# many extractions on every Generate click. The refusal message carries
# this rationale verbatim (check_upload_supply).
UPLOAD_MAX_RECORDS = 50


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


# ---------------------------------------------------------------------------
# 04-06, part 2: UPLOAD-SIDE pure surface (SETUP-03). The cmd-tier upload
# pipeline (04-08) and window upload handler (04-10) assemble on exactly
# these helpers: read -> split -> supply-check -> per-record extraction ->
# row build -> row validate. Research: 04-RESEARCH-export-upload.md
# upload_pipeline + multi_record_rules.
#
# The TWO-sha256 rule (Decision 19):
# - read_upload_source returns the FILE hash (sha256 of the raw picked
#   bytes -> setup upload['sha256'], the load-moved-file guard).
# - build_uploaded_row's sha256 is over the embedded RECORD TEXT (what an
#   importer decodes and verifies, gate 5 above).
# ---------------------------------------------------------------------------


def split_sdf_records(text):
    """Split multi-record SDF text at the '$$$$' terminator lines.

    The SDF terminator is a line exactly '$$$$' (reader/writer:
    pymol-src/modules/chempy/sdf.py:145-155). Lines are split with
    splitlines(True) and re-joined per record, never str.split('\\n')
    -- CRLF uploads must preserve their original bytes (binary-mode
    byte-stability, persistence.py rationale). Each returned record
    INCLUDES its trailing '$$$$' line. A whitespace-only tail after the
    last terminator is dropped. A text with no terminator is one record
    if it has non-whitespace content (single-record SDF is legal), else
    [].
    """
    records = []
    current = []
    found_terminator = False
    for line in text.splitlines(True):
        if line.rstrip('\r\n') == '$$$$':
            found_terminator = True
            current.append(line)
            records.append(''.join(current))
            current = []
        else:
            current.append(line)
    tail = ''.join(current)
    if tail.strip():
        if found_terminator:
            records.append(tail)      # content after the last $$$$
        else:
            records.append(text)      # single record, no terminator
    return records


def split_mol2_segments(text):
    """Split multi-molecule MOL2 text at column-0 @<TRIPOS>MOLECULE.

    The writer emits the keyword at column 0 (pymol-src/modules/chempy/
    mol2.py:34); the C reader consumes restart-based segments
    (ObjectMolecule.cpp:8537-8540). Each returned segment INCLUDES its
    keyword line; any leading comment/pre-block lines before the FIRST
    keyword attach to the first segment (the reader's restart mechanism
    consumes segment 1 -- research multi_record_rules). No keyword ->
    [text] if non-whitespace, else [].
    """
    segments = []
    current = []
    found_keyword = False
    for line in text.splitlines(True):
        if line.startswith('@<TRIPOS>MOLECULE'):
            if found_keyword:
                segments.append(''.join(current))
                current = []
            found_keyword = True
        current.append(line)
    if found_keyword:
        segments.append(''.join(current))     # last segment (or only 1)
        return segments
    return [text] if text.strip() else []


def check_upload_supply(records, fmt, source_name):
    """Refuse unusable upload supplies (FormatError naming file + index).

    Refusals (fail-closed minimum; full validation is EXT-04 v2):
    - zero records -> nothing to play with.
    - any record whose stripped text is empty -> degnerate record,
      remove it and retry (record index is 1-based, user-facing).
    - more than UPLOAD_MAX_RECORDS records -> the v1 cap, with the
      perf rationale in the message (Decision 8: new_game temp-loads
      EVERY candidate row upfront per Generate, engine.py:220-223 --
      one extraction per record per Generate).
    Returns None silently when the supply is usable.
    """
    if not records:
        raise FormatError(
            "upload %r contains 0 %s records -- nothing to play with"
            % (source_name, fmt))
    for index, record in enumerate(records):
        if not str(record).strip():
            raise FormatError(
                "upload %r record %d is empty -- remove it and retry"
                % (source_name, index + 1))
    if len(records) > UPLOAD_MAX_RECORDS:
        raise FormatError(
            "upload %r carries %d records -- the v1 cap is %d "
            "(generation temp-loads every molecule per generate); "
            "split the set or reduce it"
            % (source_name, len(records), UPLOAD_MAX_RECORDS))
    return None


def read_upload_source(path):
    """Read an uploaded molecule file -> (text, FILE sha256, fmt).

    fmt comes from the LOWERCASED extension (os.path.splitext); anything
    outside manifest.FORMATS ('sdf','mol2') is refused -- PDB included
    (REQUIREMENTS Out of Scope: no reliable bond orders). The file is
    read in binary; sha256 is over the RAW BYTES (the FILE hash --
    Decision 19: row hashes are over record text, never conflate).
    Bytes decode utf-8-strict; a decode failure is a FormatError, never
    a bare UnicodeDecodeError. Pure I/O exactly like
    persistence.read_json_file (stdlib open only).
    """
    ext = os.path.splitext(str(path))[1].lower()
    fmt = ext[1:] if ext.startswith('.') else ext
    if fmt not in manifest.FORMATS:
        raise FormatError(
            "unsupported upload format %r (expected .sdf or .mol2) "
            "-- PDB is not supported (no reliable bond orders)" % (ext,))
    with open(path, 'rb') as handle:
        raw = handle.read()
    sha256_hex = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        raise FormatError("could not decode %r as UTF-8" % (path,))
    return text, sha256_hex, fmt


def build_uploaded_row(atom_records, lig_bonds, profile, record_text,
                       fmt, index):
    """Build one manifest-shaped upload row (14 keys + 'set_id' +
    'title') for record `index` (0-based) of an uploaded file.

    Synthetic identity (research upload_pipeline Step 3): entry_id is
    'mol-%03d' (index + 1) -- the generator's own convention
    (generator.py:852), so distinct-pick dedup can never collide; file
    is the package-relative-style key 'uploads/mol-%03d.<fmt>' (a KEY
    into ligand_files / ligand_content, NEVER a real path -- the
    absolute-path hazard is structurally impossible). sha256 is over the
    RECORD TEXT (the two-sha256 rule, Decision 19). protonation is
    'as-recorded' (never invent chemistry claims, PITFALL 14).
    size_class derives via generator._candidate_class (the single home
    for the SIZE_S1/S2 buckets); bond_order_counts via
    capability._bond_order_int (digit-string keys -> positive ints,
    manifest shape); states_expected is 1 per split record.
    """
    number = index + 1
    heavy = sum(1 for record in atom_records
                if str(record.get('elem', '')).strip().upper() != 'H')
    bond_order_counts = {}
    for bond in lig_bonds:
        order = _bond_order_int(bond[2] if len(bond) > 2 else None)
        # An unrecognized order yields None -> key 'None' -> refused by
        # the manifest's digit-string rule in validate_uploaded_rows
        # (fail-closed, never guessed).
        key = str(order)
        bond_order_counts[key] = bond_order_counts.get(key, 0) + 1
    formal_charge_sum = 0
    for record in atom_records:
        charge = record.get('formal_charge')
        if charge is not None:
            try:
                formal_charge_sum += int(charge)
            except (TypeError, ValueError):
                pass                        # fail-closed: counts 0
    first_line = record_text.split('\n', 1)[0].strip()
    profile = profile or {}
    return {
        'set_id': UPLOAD_SET_ID,
        'entry_id': 'mol-%03d' % number,
        'file': 'uploads/mol-%03d.%s' % (number, fmt),
        'format': fmt,
        'sha256': hashlib.sha256(record_text.encode('utf-8')).hexdigest(),
        'protonation': 'as-recorded',
        'atom_count': len(atom_records),
        'heavy_atom_count': heavy,
        'bond_count': len(lig_bonds),
        'bond_order_counts': bond_order_counts,
        'formal_charge_sum': formal_charge_sum,
        'states_expected': 1,
        'metal_present': bool(profile.get('has_metal')),
        'halogen_present': bool(profile.get('has_halogen_donor')),
        'size_class': _candidate_class({'heavy_atom_count': heavy}),
        'title': first_line,
    }


def validate_uploaded_rows(rows):
    """Validate upload rows: construction guards, then the manifest's
    OWN dict-level entry rules.

    Rows are built by build_uploaded_row, so set_id and entry_id are
    correct BY CONSTRUCTION -- they are CHECKED anyway (fail-closed):
    set_id must be UPLOAD_SET_ID and entry_id a non-empty string. Then
    every row is checked by manifest._check_entry itself (the single
    home for the 14-key rules, manifest.py:191-295) via this thin
    same-package adapter -- never re-implemented here. The 'file'
    refusals (backslash / absolute / Windows-drive, manifest.py:
    253-275) therefore apply verbatim: upload file values are KEYS, and
    the os.path.join hazard (an absolute third component silently drops
    the package prefix) is structurally impossible. Raises FormatError
    (ValueError family) with the manifest's own message shapes;
    returns None on success.
    """
    for index, row in enumerate(rows):
        number = index + 1
        if not isinstance(row, dict):
            raise FormatError(
                "uploaded row %d must be a dict with 'set_id' %r "
                "(found %s)"
                % (number, UPLOAD_SET_ID, type(row).__name__))
        set_id = row.get('set_id')
        if set_id != UPLOAD_SET_ID:
            raise FormatError(
                "uploaded row %d must carry 'set_id' %r "
                "(which construction guarantees -- found %r)"
                % (number, UPLOAD_SET_ID, set_id))
        entry_id = row.get('entry_id')
        if not isinstance(entry_id, str) or not entry_id:
            raise FormatError(
                "uploaded row %d must carry a non-empty 'entry_id' "
                "string (which construction guarantees -- found %r)"
                % (number, entry_id))
        # The single-home delegation: manifest's per-entry rules (via
        # _check_set's own caller shape) verify all 14 REQUIRED keys,
        # the path-family file refusals, counts, flag bools, and the
        # digit-string bond_order_counts shape.
        manifest._check_entry(UPLOAD_SET_ID, index, row)
    return None
