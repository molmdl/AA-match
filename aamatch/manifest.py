"""aamatch.manifest -- bundled-data manifest: parse, validate, enumerate.

PURE module (Phase 2, plan 02-03). Imports .persistence ONLY; file
loading and path resolution stay cmd-tier: the caller (headless smoke,
cmd-tier materializer) reads aamatch/data/MANIFEST.json from disk
(persistence.read_json_file) and hands the DICT to parse_manifest_dict.
This module never touches the filesystem and does not import paths --
resolution is documented only: cmd tier does
paths.package_data_path('data', entry['file']) -> paths.to_windows_path
-> cmd.load.

The manifest is the contract between bundled data files and the engine
(PITFALL 11.3 anti-drift; GEN-02 supply proof):

- COUNTS ARE THE CONTRACT: atom_count / bond_count / bond_order_counts /
  formal_charge_sum / states_expected are exactly what the
  every-manifest-id smoke (SMOKE-02, plan 02-04) asserts after cmd.load;
  each field is load-bearing, none decorative.
- sha256 pins file content (silent data swaps are detected).
- metal_present / halogen_present gate conditional interaction types
  (approved DETECT-03 semantics: metal list {MG, ZN, FE, CA, MN, CU, NI,
  CO, CD}; halogen donors {Cl, Br, I}, C-F excluded -- see
  02-01-SUMMARY.md).
- The largest bundled molecule (perf-smoke target, DETECT-05) is derived
  as max(entries, key=heavy_atom_count) -- largest_entry; no
  special-cased field to drift.

Payload shape (the container's 'data'; full field reference:
02-RESEARCH-materialization.md §3.2):

    {
      "manifest_version": 1,
      "sets": [
        {"set_id": "demo-easy-1", "tier": ..., "title": ...,
         "license": ..., "provenance": {...},
         "entries": [
           {"entry_id", "file", "format", "sha256", "protonation",
            "atom_count", "heavy_atom_count", "bond_count",
            "bond_order_counts", "formal_charge_sum", "states_expected",
            "metal_present", "halogen_present", "size_class"}
         ]}
      ]
    }

Versioning: manifest_version follows refuse-newer / accept-older like
FORMAT_VERSION -- a newer manifest is refused ("Please update
AA-match"); older ones accepted (additive-only evolution: unknown extra
fields are PRESERVED, never stripped -- P9). Entry 'file' values are
package-relative FORWARD-SLASH paths: Windows or absolute paths are
refused at parse time (PITFALL 2 -- the manifest never stores them).

Validation helpers mirror level_spec.py's style: plain functions,
FormatError with entry context naming set, entry index, entry_id, and
the offending field.

Purity: module-level import is `.persistence` ONLY (FormatError,
check_container). NO file I/O, NO pymol/Qt/numpy. Unit-tests under bare
python3.6 with zero stubs.
"""

from .persistence import FormatError, check_container

MANIFEST_VERSION = 1

FORMATS = ('sdf', 'mol2')
SIZE_CLASSES = ('small', 'medium', 'large')

REQUIRED_ENTRY_KEYS = (
    'entry_id', 'file', 'format', 'sha256', 'protonation',
    'atom_count', 'heavy_atom_count', 'bond_count', 'bond_order_counts',
    'formal_charge_sum', 'states_expected', 'metal_present',
    'halogen_present', 'size_class',
)

_COUNT_KEYS = ('atom_count', 'heavy_atom_count', 'bond_count',
               'states_expected')
_FLAG_KEYS = ('metal_present', 'halogen_present')

_HEX_DIGITS = frozenset('0123456789abcdef')
_DECIMAL_DIGITS = frozenset('0123456789')


def _is_int(value):
    """True for real ints only -- bool is an int subclass, never a count."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_digit_str(value):
    """True for non-empty ASCII digit strings ('1', '12'); '²' is not."""
    return (isinstance(value, str) and value != ''
            and all(char in _DECIMAL_DIGITS for char in value))


def _is_lower_hex64(value):
    """True for exactly-64-char lowercase hex strings (sha256 pins)."""
    return (isinstance(value, str) and len(value) == 64
            and all(char in _HEX_DIGITS for char in value))


def parse_manifest_dict(container):
    """Validate a manifest container; return its payload UNCHANGED.

    `container` is a full AA-match container dict (magic/version/kind/
    data) as produced by persistence.make_container('manifest', ...) or
    read from aamatch/data/MANIFEST.json. Gate chain, in order:

    1. container gate -- persistence.check_container(kind='manifest'):
       foreign magic / newer container version / misfiled kind refused
       with the canonical persistence messages (reused, not duplicated).
    2. manifest_version: must be a real int; refuse-newer / accept-older
       like FORMAT_VERSION (missing or > MANIFEST_VERSION -> "unsupported
       manifest version ... (expected <= 1)").
    3. structure: sets a list; each set a dict with a non-empty string
       set_id and an entries list; every entry validated against the
       REQUIRED_ENTRY_KEYS schema.

    Entry rules (every refusal names the set, the entry, and the field):
    - all 14 required keys present (entry_id/file/format/sha256/
      protonation/atom_count/heavy_atom_count/bond_count/
      bond_order_counts/formal_charge_sum/states_expected/
      metal_present/halogen_present/size_class)
    - entry_id: non-empty string (the enumeration sort key)
    - file: non-empty forward-slash package-relative path -- backslashes,
      absolute ('/...') and Windows-drive ('X:...') paths refused
      (PITFALL 2)
    - format: 'sdf' | 'mol2'
    - sha256: 64-char lowercase hex string
    - atom_count / heavy_atom_count / bond_count / states_expected: real
      ints (bool refused -- the _is_int pattern from level_spec.py)
    - bond_order_counts: dict of digit-string order -> positive int
    - formal_charge_sum: int (may be negative -- acetate et al.)
    - size_class: 'small' | 'medium' | 'large'
    - metal_present / halogen_present: real bools

    Returns the payload dict itself (passthrough, P9); the input is
    never mutated (P6); unknown extra fields are preserved. Raises
    FormatError naming the failing gate.
    """
    container = check_container(container, 'manifest')
    data = container.get('data')
    if not isinstance(data, dict):
        raise FormatError(
            "manifest payload must be a dict (found %s)"
            % type(data).__name__)

    manifest_version = data.get('manifest_version')
    if not _is_int(manifest_version):
        raise FormatError(
            "unsupported manifest version %r (expected <= %d)"
            % (manifest_version, MANIFEST_VERSION))
    if manifest_version > MANIFEST_VERSION:
        raise FormatError(
            "unsupported manifest version %d (expected <= %d). "
            "Please update AA-match."
            % (manifest_version, MANIFEST_VERSION))

    _check_sets(data.get('sets'))
    return data


def _check_sets(sets):
    """sets must be a list of set dicts (each with set_id + entries)."""
    if not isinstance(sets, list):
        raise FormatError(
            "manifest 'sets' must be a list (found %s)"
            % type(sets).__name__)
    for set_index, set_dict in enumerate(sets):
        _check_set(set_dict, set_index)


def _check_set(set_dict, set_index):
    """One set: set_id (enumeration sort key) + entries list to walk."""
    if not isinstance(set_dict, dict):
        raise FormatError(
            "manifest sets[%d] must be a dict (found %s)"
            % (set_index, type(set_dict).__name__))
    set_id = set_dict.get('set_id')
    if not isinstance(set_id, str) or not set_id:
        raise FormatError(
            "manifest sets[%d] 'set_id' must be a non-empty string "
            "(found %r)" % (set_index, set_id))
    entries = set_dict.get('entries')
    if not isinstance(entries, list):
        raise FormatError(
            "manifest set %r 'entries' must be a list (found %s)"
            % (set_id, type(entries).__name__))
    for entry_index, entry in enumerate(entries):
        _check_entry(set_id, entry_index, entry)


def _check_entry(set_id, entry_index, entry):
    """One entry against the REQUIRED_ENTRY_KEYS schema (module
    docstring). Refusals always carry set/entry/field context."""
    if not isinstance(entry, dict):
        raise FormatError(
            "manifest set %r entries[%d] must be a dict (found %s)"
            % (set_id, entry_index, type(entry).__name__))
    where = "manifest set %r entry %d" % (set_id, entry_index)
    if 'entry_id' in entry:
        where += " (entry_id=%r)" % (entry.get('entry_id'),)

    for key in REQUIRED_ENTRY_KEYS:
        if key not in entry:
            raise FormatError("%s: missing required key %r" % (where, key))

    entry_id = entry.get('entry_id')
    if not isinstance(entry_id, str) or not entry_id:
        raise FormatError(
            "%s: 'entry_id' must be a non-empty string (found %r)"
            % (where, entry_id))

    _check_entry_file(where, entry.get('file'))

    fmt = entry.get('format')
    if fmt not in FORMATS:
        raise FormatError(
            "%s: 'format' must be one of 'sdf', 'mol2' (found %r)"
            % (where, fmt))

    sha256 = entry.get('sha256')
    if not _is_lower_hex64(sha256):
        raise FormatError(
            "%s: 'sha256' must be a 64-char lowercase hex string "
            "(found %r)" % (where, str(sha256)[:24]))

    for key in _COUNT_KEYS:
        value = entry.get(key)
        if not _is_int(value):
            raise FormatError(
                "%s: %r must be an int (found %r)" % (where, key, value))

    _check_bond_order_counts(where, entry.get('bond_order_counts'))

    formal_charge_sum = entry.get('formal_charge_sum')
    if not _is_int(formal_charge_sum):
        raise FormatError(
            "%s: 'formal_charge_sum' must be an int (found %r)"
            % (where, formal_charge_sum))

    size_class = entry.get('size_class')
    if size_class not in SIZE_CLASSES:
        raise FormatError(
            "%s: 'size_class' must be one of 'small', 'medium', 'large' "
            "(found %r)" % (where, size_class))

    for key in _FLAG_KEYS:
        value = entry.get(key)
        if not isinstance(value, bool):
            raise FormatError(
                "%s: %r must be a bool (found %r)" % (where, key, value))


def _check_entry_file(where, file_path):
    """'file' is a package-relative FORWARD-SLASH path (PITFALL 2):
    backslashes (Windows), absolute POSIX and Windows-drive paths are
    refused at parse time -- the manifest never stores them; the cmd
    tier resolves entry['file'] via paths.package_data_path('data', ...)."""
    if not isinstance(file_path, str) or not file_path:
        raise FormatError(
            "%s: 'file' must be a non-empty package-relative path "
            "(found %r)" % (where, file_path))
    if '\\' in file_path:
        raise FormatError(
            "%s: 'file' must use forward slashes -- backslash (Windows) "
            "paths are never stored in the manifest (found %r)"
            % (where, file_path))
    if file_path.startswith('/'):
        raise FormatError(
            "%s: 'file' must be package-relative, not an absolute path "
            "(found %r)" % (where, file_path))
    if len(file_path) >= 2 and file_path[1] == ':' \
            and file_path[0].isalpha():
        raise FormatError(
            "%s: 'file' must be package-relative, not a Windows drive "
            "path (found %r)" % (where, file_path))


def _check_bond_order_counts(where, bond_order_counts):
    """bond_order_counts: dict of digit-string bond order -> positive
    int (the multiset the every-manifest-id smoke expands + compares)."""
    if not isinstance(bond_order_counts, dict):
        raise FormatError(
            "%s: 'bond_order_counts' must be a dict of digit-string -> "
            "positive int (found %s)"
            % (where, type(bond_order_counts).__name__))
    for order_key, order_count in bond_order_counts.items():
        if not _is_digit_str(order_key):
            raise FormatError(
                "%s: 'bond_order_counts' keys must be digit strings "
                "(found %r)" % (where, order_key))
        if not _is_int(order_count) or order_count < 1:
            raise FormatError(
                "%s: 'bond_order_counts' values must be positive ints "
                "(found %r for order %r)"
                % (where, order_count, order_key))


def enumerate_entries(payload):
    """Flatten a VALIDATED manifest payload into a deterministic list.

    Returns a NEW list of NEW dicts (the input is never mutated): each
    row is one entry's fields plus 'set_id'. Rows are sorted by
    (set_id, entry_id), so repeated calls return identical order --
    the generator (02-08) consumes this list as its candidate input.
    """
    rows = []
    for set_dict in payload.get('sets', []):
        set_id = set_dict.get('set_id')
        for entry in set_dict.get('entries', []):
            row = dict(entry)
            row['set_id'] = set_id
            rows.append(row)
    rows.sort(key=lambda row: (row['set_id'], row['entry_id']))
    return rows


def largest_entry(entries):
    """Return the entry with the max heavy_atom_count (ties: the first
    in the given order -- i.e. the first in enumerate_entries' sorted
    order). This is the perf-smoke target selector (DETECT-05): derived
    from the entries, never a special-cased manifest field.
    Empty `entries` -> None.
    """
    best = None
    for entry in entries:
        if best is None \
                or entry['heavy_atom_count'] > best['heavy_atom_count']:
            best = entry
    return best
