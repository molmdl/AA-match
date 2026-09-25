#!/usr/bin/env python3.6
"""scripts/build_demos.py -- AA-match bundled demo-data builder (Phase 8).

Durable replacement for the 02-04 throwaway tmp/build_fixtures.py: one
committed, reproducible pipeline that takes a per-set JSON spec
(scripts/demo_specs/<set_id>.json) and fetches/verifies/derives the SDF
bytes + the matching MANIFEST.json set payload.

Contract (the 02-04 fixture laws generalized to multi-set curated data):
- Counts are DERIVED from the ligand bytes via a stdlib-only V2000
  parser (counts line + atom/bond blocks + M CHG lines), never
  hand-entered; sha256 is taken over the target-file bytes IN THE SAME
  RUN; regenerated rather than hand-edited (STATE.md 02-04 law: NEVER
  hand-edit an SDF or MANIFEST.json).
- Single-record guarantee: a source with more than one '$$$$'-delimited
  record is REFUSED naming the entry -- split or pick one state at
  curation time, never collapse (08-RESEARCH-sourcing RQ7).
- All manifest machinery comes from its single homes: persistence
  (read_json_file / write_json_atomic / make_container), manifest
  (parse_manifest_dict / REQUIRED_ENTRY_KEYS), generator._candidate_class
  (the size-bucket rule is NEVER re-implemented here).
- Manifest entries are EXACTLY the 14 REQUIRED_ENTRY_KEYS. Entry-level
  provenance lives in the SPECS (and flows to DATA_SOURCES.md via
  --report-only); it is deliberately NOT written into MANIFEST.json, so
  the dry-run reproduces the committed dev set byte-for-byte on parsed
  content and 08-RESEARCH Q5's payload-provenance-'' verdict holds.

CLI:
  python3.6 scripts/build_demos.py --spec scripts/demo_specs/<set_id>.json
                                   [--fetch] [--dry-run] [--report-only]

Modes:
  (default)      resolve ligand bytes (url fetch, local_path copy, or
                 existing committed file), derive the set payload,
                 replace-or-insert ONLY that set in
                 aamatch/data/MANIFEST.json (all other set dicts
                 untouched), re-parse the rebuilt container for validity,
                 write atomically (write_json_atomic).
  --dry-run      same derivation, but prints the derived set payload plus
                 a per-key derived-vs-committed comparison and exits
                 WITHOUT writing anything (exit 2 on mismatch; the dev
                 set is the committed-parser oracle: derived must equal
                 committed demo-dev-1 on every key exactly).
  --report-only  no network, no writes: reads the committed manifest +
                 every spec under scripts/demo_specs/, verifies each
                 spec's entry files/sha256 against the manifest (exit 1,
                 every gap named) and prints per-set markdown provenance
                 rows (the exact columns 08-09's DATA_SOURCES.md needs).
  --fetch        resolve ligand bytes via urllib.request GET of the
                 entry 'url' (User-Agent 'AA-match-build/1.0',
                 timeout 60 s) written to the target file; without
                 --fetch the existing target file is used (or copied
                 from 'local_path').

Authoritative cross-check: every content plan runs SMOKE-02 (real PyMOL
loads, per-entry count/charge/state/flag asserts) BEFORE its atomic
commit, so a parser/PyMOL disagreement can never land in git. If SMOKE-02
ever disagrees with this parser: repair the parser, regenerate, re-run --
never hand-edit.

python3.6-safe, stdlib-only (json/os/sys/hashlib/urllib/argparse), NO
pymol/Qt/numpy imports anywhere, no dataclasses. Lives outside the
purity gates by design (Gate A scans PURE_MODULES, Gate D compiles
aamatch/*.py); kept clean anyway.
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aamatch.persistence import (  # noqa: E402
    read_json_file,
    write_json_atomic,
    make_container,
)
from aamatch.manifest import (  # noqa: E402
    parse_manifest_dict,
    REQUIRED_ENTRY_KEYS,
)
from aamatch.generator import _candidate_class  # noqa: E402

MANIFEST_RELPATH = os.path.join('aamatch', 'data', 'MANIFEST.json')
MANIFEST_PATH = os.path.join(REPO_ROOT, MANIFEST_RELPATH)
DATA_DIR = os.path.join(REPO_ROOT, 'aamatch', 'data')
SPECS_RELPATH = os.path.join('scripts', 'demo_specs')
SPECS_DIR = os.path.join(REPO_ROOT, SPECS_RELPATH)

FETCH_USER_AGENT = 'AA-match-build/1.0'
FETCH_TIMEOUT = 60

TIERS = ('easy', 'hard', 'challenge', 'very_challenging')

ENTRY_PROVENANCE_KEYS = (
    'source_url', 'pdb_id', 'entry_doi', 'paper_doi', 'plip', 'notes')

# DETECT-03 element vocabularies (approved 2026-09-06): metals gate the
# metal-coordination type; halogen donors are Cl/Br/I (C-F excluded).
METAL_ELEMENTS = frozenset(
    ('MG', 'ZN', 'FE', 'CA', 'MN', 'CU', 'NI', 'CO', 'CD'))
HALOGEN_ELEMENTS = frozenset(('CL', 'BR', 'I'))


class BuildError(ValueError):
    """Spec invalid / source refused / derivation failed -- names the field."""


def _fail(message):
    raise BuildError(message)


# ---------------------------------------------------------------------------
# Spec loading + validation (structure only; semantic depth is the test
# battery's job -- tests/test_demo_data.py)
# ---------------------------------------------------------------------------

def load_spec(spec_ref):
    """Read + structurally validate a spec; return the spec dict.

    Accepts a repo-relative path, an absolute path, or a bare set_id
    (resolved to scripts/demo_specs/<set_id>.json).
    """
    spec_path = spec_ref
    if not spec_path.endswith('.json'):
        spec_path = os.path.join(SPECS_RELPATH, '%s.json' % spec_ref)
    abs_path = spec_path if os.path.isabs(spec_path) \
        else os.path.join(REPO_ROOT, spec_path)
    if not os.path.isfile(abs_path):
        _fail("spec file not found: %r" % spec_ref)
    try:
        with open(abs_path, 'rb') as fh:
            spec = json.loads(fh.read().decode('utf-8'))
    except (ValueError, UnicodeDecodeError) as exc:
        _fail("spec %r is not valid JSON: %s" % (spec_ref, exc))
    return validate_spec(spec, spec_ref)


def validate_spec(spec, spec_ref):
    """Structural spec validation; every refusal names the bad field."""
    where = "spec %r" % spec_ref
    if not isinstance(spec, dict):
        _fail("%s must be a JSON object (found %s)"
              % (where, type(spec).__name__))
    set_id = spec.get('set_id')
    if not isinstance(set_id, str) or not set_id:
        _fail("%s: 'set_id' must be a non-empty string (found %r)"
              % (where, set_id))
    where = "spec %r (set %r)" % (spec_ref, set_id)
    tier = spec.get('tier')
    if tier not in TIERS:
        _fail("%s: 'tier' must be one of %s (found %r)"
              % (where, ' | '.join(TIERS), tier))
    title = spec.get('title')
    if not isinstance(title, str) or not title:
        _fail("%s: 'title' must be a non-empty string (found %r)"
              % (where, title))
    if not isinstance(spec.get('license'), str):
        _fail("%s: 'license' must be a string, '' allowed ONLY for the "
              "dev set (found %r)" % (where, spec.get('license')))
    if not isinstance(spec.get('provenance'), dict):
        _fail("%s: 'provenance' must be a dict, {} allowed ONLY for the "
              "dev set (found %s)"
              % (where, type(spec.get('provenance')).__name__))
    entries = spec.get('entries')
    if not isinstance(entries, list) or not entries:
        _fail("%s: 'entries' must be a non-empty list (found %s)"
              % (where, type(entries).__name__))
    seen_ids = set()
    for index, entry in enumerate(entries):
        _validate_entry(entry, where, index)
        if entry['entry_id'] in seen_ids:
            _fail("%s: duplicate 'entry_id' %r" % (where, entry['entry_id']))
        seen_ids.add(entry['entry_id'])
    return spec


def _validate_entry(entry, where, index):
    if not isinstance(entry, dict):
        _fail("%s entry %d must be a dict (found %s)"
              % (where, index, type(entry).__name__))
    entry_id = entry.get('entry_id')
    if not isinstance(entry_id, str) or not entry_id:
        _fail("%s entry %d: 'entry_id' must be a non-empty string "
              "(found %r)" % (where, index, entry_id))
    where = "%s entry %r" % (where, entry_id)
    has_url = bool(entry.get('url'))
    has_local = bool(entry.get('local_path'))
    if has_url == has_local:
        _fail("%s: exactly one of 'url' / 'local_path' is required "
              "(found url=%r local_path=%r)"
              % (where, entry.get('url'), entry.get('local_path')))
    file_rel = entry.get('file')
    if file_rel is not None:
        if not isinstance(file_rel, str) or not file_rel \
                or '\\' in file_rel or file_rel.startswith('/') \
                or (len(file_rel) >= 2 and file_rel[1] == ':'
                    and file_rel[0].isalpha()):
            _fail("%s: 'file' must be a non-empty package-relative "
                  "forward-slash path (found %r)" % (where, file_rel))
    protonation = entry.get('protonation', 'as-recorded')
    if not isinstance(protonation, str) or not protonation:
        _fail("%s: 'protonation' must be a non-empty string (found %r)"
              % (where, protonation))
    expect = entry.get('expect_atom_count')
    if expect is not None \
            and (not isinstance(expect, int) or isinstance(expect, bool)):
        _fail("%s: 'expect_atom_count' must be an int (found %r)"
              % (where, expect))
    provenance = entry.get('provenance')
    if not isinstance(provenance, dict):
        _fail("%s: 'provenance' must be a dict with keys %s (found %s)"
              % (where, '/'.join(ENTRY_PROVENANCE_KEYS),
                 type(provenance).__name__))
    for key in ENTRY_PROVENANCE_KEYS:
        if key not in provenance:
            _fail("%s: 'provenance' missing required key %r"
                  % (where, key))


def entry_file_rel(set_id, entry):
    """The entry's package-relative target file: explicit 'file' override
    or the collision-free default ligands/<set_id>-<entry_id>.sdf."""
    if entry.get('file'):
        return entry['file']
    return 'ligands/%s-%s.sdf' % (set_id, entry['entry_id'])


def _entry_target_path(file_rel):
    return os.path.join(DATA_DIR, file_rel.replace('/', os.sep))


# ---------------------------------------------------------------------------
# Ligand byte resolution (fetch / local_path / existing target)
# ---------------------------------------------------------------------------

def _fetch_bytes(entry, where):
    request = urllib.request.Request(
        entry['url'], headers={'User-Agent': FETCH_USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=FETCH_TIMEOUT) as fh:
            return fh.read()
    except Exception as exc:
        _fail("%s: fetch failed for %r (%s)" % (where, entry['url'], exc))


def _read_bytes(path, where):
    try:
        with open(path, 'rb') as fh:
            return fh.read()
    except OSError as exc:
        _fail("%s: cannot read %r (%s)" % (where, path, exc))


def _write_bytes(path, data, where):
    parent = os.path.dirname(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    try:
        with open(path, 'wb') as fh:
            fh.write(data)
    except OSError as exc:
        _fail("%s: cannot write %r (%s)" % (where, path, exc))


def resolve_ligand_bytes(spec, entry, fetch, dry_run):
    """Return (file_rel, bytes) of the entry's target ligand file.

    Byte source:
    - fetch mode (entry has 'url'): GET the url and, unless dry-run,
      write the bytes to the target file; sha256 then covers the written
      bytes in the same run.
    - 'local_path': copy to the target file (unless dry-run; no-op when
      the local path IS the target, the dev-set legacy shape), then read
      the target bytes back so sha256/coverage truly match the file.
    - otherwise: the existing committed target file.
    Empty sources refuse naming the entry.
    """
    file_rel = entry_file_rel(spec['set_id'], entry)
    target = _entry_target_path(file_rel)
    where = "spec set %r entry %r" % (spec['set_id'], entry['entry_id'])
    if fetch and entry.get('url'):
        data = _fetch_bytes(entry, where)
        if not dry_run:
            _write_bytes(target, data, where)
        return file_rel, data
    if entry.get('local_path'):
        local_abs = os.path.join(REPO_ROOT,
                                 entry['local_path'].replace('/', os.sep))
        if not os.path.isfile(local_abs):
            _fail("%s: 'local_path' %r does not exist"
                  % (where, entry['local_path']))
        if os.path.abspath(local_abs) != os.path.abspath(target) \
                and not dry_run:
            _write_bytes(target, _read_bytes(local_abs, where), where)
            return file_rel, _read_bytes(target, where)
        return file_rel, _read_bytes(local_abs, where)
    if not os.path.isfile(target):
        _fail("%s: target file %r not found (need --fetch or a "
              "'local_path')" % (where, file_rel))
    return file_rel, _read_bytes(target, where)


# ---------------------------------------------------------------------------
# Pure V2000 derivation (route A -- stdlib-only, WSL python3.6 floor)
# ---------------------------------------------------------------------------

def split_sdf_records(data):
    """Split SDF bytes on '$$$$' lines (terminator ignored). Returns the
    list of non-empty record byte strings, terminators normalized."""
    records = []
    current = []
    for line in data.splitlines(True):
        if line.rstrip(b'\r\n') == b'$$$$':
            if current:
                records.append(b''.join(current))
            current = []
        else:
            current.append(line)
    if current:
        records.append(b''.join(current))
    return [record for record in records if record.strip()]


def _counts_line_parse(lines, where):
    """The V2000 counts line: line index 3, cols 0-3 atoms / 3-6 bonds,
    trailing ' V2000'. Refusals name the entry."""
    if len(lines) < 4:
        _fail("%s: V2000 counts-line parse failure (record has %d lines; "
              "counts line needs index 3)" % (where, len(lines)))
    counts = lines[3]
    if 'V2000' not in counts:
        _fail("%s: V2000 counts-line parse failure (line 3 lacks the "
              "V2000 tag: %r) -- V3000 or non-MDL source"
              % (where, counts.rstrip('\r\n')))
    try:
        atom_count = int(counts[0:3])
        bond_count = int(counts[3:6])
    except (ValueError, TypeError):
        _fail("%s: V2000 counts-line parse failure (count columns not "
              "ints: %r)" % (where, counts[:9]))
    if atom_count < 1 or bond_count < 0:
        _fail("%s: V2000 counts-line parse failure (atom_count=%d "
              "bond_count=%d)" % (where, atom_count, bond_count))
    return atom_count, bond_count


def derive_v2000_fields(record_bytes, where):
    """Parse ONE V2000 record into the derived-counts dict; refuses any
    structural failure (counts line, block truncation, element symbols,
    bond-order columns, M CHG lines)."""
    try:
        text = record_bytes.decode('utf-8')
    except UnicodeDecodeError as exc:
        _fail("%s: V2000 record is not valid UTF-8 (%s)" % (where, exc))
    lines = text.splitlines()
    atom_count, bond_count = _counts_line_parse(lines, where)
    atom_block = lines[4:4 + atom_count]
    bond_block = lines[4 + atom_count:4 + atom_count + bond_count]
    if len(atom_block) != atom_count or len(bond_block) != bond_count:
        _fail("%s: V2000 counts-line parse failure (record truncated: "
              "declare %d atoms/%d bonds, record holds %d/%d block lines)"
              % (where, atom_count, bond_count,
                 len(atom_block), len(bond_block)))
    elements = [line[31:34].strip().upper() for line in atom_block]
    if any(not element for element in elements):
        _fail("%s: V2000 atom-block parse failure (missing element "
              "symbol)" % where)
    heavy_atom_count = sum(1 for element in elements if element != 'H')
    bond_order_counts = {}
    for line in bond_block:
        order = line[6:9].strip()
        if not order.isdigit() or order == '0':
            _fail("%s: V2000 bond-block parse failure (order column not "
                  "a positive int: %r)" % (where, line.rstrip('\r\n')))
        bond_order_counts[order] = bond_order_counts.get(order, 0) + 1
    formal_charge_sum = 0
    for line in lines:
        if not line.startswith('M  CHG'):
            continue
        tokens = line.split()  # 'M' 'CHG' <n> then n (idx, chg) pairs
        try:
            n_pairs = int(tokens[2])
            pairs = tokens[3:]
            if len(pairs) != 2 * n_pairs:
                raise ValueError
            for pair in range(n_pairs):
                formal_charge_sum += int(pairs[2 * pair + 1])
        except (ValueError, IndexError):
            _fail("%s: M CHG line parse failure (%r)"
                  % (where, line.strip()))
    element_set = frozenset(elements)
    return {
        'atom_count': atom_count,
        'bond_count': bond_count,
        'bond_order_counts': bond_order_counts,
        'formal_charge_sum': formal_charge_sum,
        'heavy_atom_count': heavy_atom_count,
        'metal_present': bool(element_set & METAL_ELEMENTS),
        'halogen_present': bool(element_set & HALOGEN_ELEMENTS),
    }


def build_entry(spec, entry, file_rel, data):
    """Assemble the manifest-shaped entry: EXACTLY the 14
    REQUIRED_ENTRY_KEYS (derived counts + sha256 over the target bytes +
    size_class from the generator's single bucket home + provenance-free
    pass-through keys). Works even in fetch mode for the dev set."""
    where = "spec set %r entry %r" % (spec['set_id'], entry['entry_id'])
    records = split_sdf_records(data)
    if len(records) > 1:
        _fail("%s: multi-record SDF source REFUSED (%d records) -- split "
              "the file or pick one state at curation time; never "
              "collapse" % (where, len(records)))
    if not records:
        _fail("%s: empty SDF source (no molecule record)" % where)
    derived = derive_v2000_fields(records[0], where)
    expect = entry.get('expect_atom_count')
    if expect is not None and derived['atom_count'] != expect:
        _fail("%s: expect_atom_count %d != derived %d (fetch corruption "
              "guard)" % (where, expect, derived['atom_count']))
    return {
        'entry_id': entry['entry_id'],
        'file': file_rel,
        'format': 'sdf',
        'sha256': hashlib.sha256(data).hexdigest(),
        'protonation': entry.get('protonation', 'as-recorded'),
        'atom_count': derived['atom_count'],
        'heavy_atom_count': derived['heavy_atom_count'],
        'bond_count': derived['bond_count'],
        'bond_order_counts': derived['bond_order_counts'],
        'formal_charge_sum': derived['formal_charge_sum'],
        'states_expected': 1,
        'metal_present': derived['metal_present'],
        'halogen_present': derived['halogen_present'],
        'size_class': _candidate_class(
            {'heavy_atom_count': derived['heavy_atom_count']}),
    }


# ---------------------------------------------------------------------------
# Manifest set assembly (replace-or-insert ONLY the target set)
# ---------------------------------------------------------------------------

def build_set_payload(spec, entry_datas):
    """The set payload dict: {set_id, tier, title, license, provenance,
    entries} -- nothing else."""
    entries = [
        build_entry(spec, entry, file_rel, data)
        for entry, (file_rel, data) in zip(spec['entries'], entry_datas)
    ]
    return {
        'set_id': spec['set_id'],
        'tier': spec['tier'],
        'title': spec['title'],
        'license': spec['license'],
        'provenance': spec['provenance'],
        'entries': entries,
    }


def assemble_manifest(committed_payload, set_payload):
    """Replace-or-insert the target set; all other set dicts untouched,
    in original order. Returns the new (not-yet-validated) payload."""
    new_sets = []
    replaced = False
    for set_dict in committed_payload.get('sets', []):
        if not replaced and set_dict.get('set_id') == set_payload['set_id']:
            new_sets.append(set_payload)
            replaced = True
        else:
            new_sets.append(set_dict)
    if not replaced:
        new_sets.append(set_payload)
    new_payload = dict(committed_payload)
    new_payload['sets'] = new_sets
    return new_payload


def committed_set(committed_payload, set_id):
    """The committed set dict for set_id, or None."""
    for set_dict in committed_payload.get('sets', []):
        if set_dict.get('set_id') == set_id:
            return set_dict
    return None


def compare_set_payloads(derived, committed):
    """Per-key derived-vs-committed comparison. Returns a list of
    mismatch lines (empty == exact match on parsed content)."""
    if committed is None:
        return ["no committed set %r to compare against" % derived['set_id']]
    mismatches = []
    for key in ('set_id', 'tier', 'title', 'license', 'provenance'):
        if derived.get(key) != committed.get(key):
            mismatches.append("set key %r differs: derived=%r "
                              "committed=%r"
                              % (key, derived.get(key), committed.get(key)))
    derived_by_id = {e['entry_id']: e for e in derived.get('entries', [])}
    committed_by_id = {e['entry_id']: e for e in committed.get('entries', [])}
    if set(derived_by_id) != set(committed_by_id):
        return mismatches + [
            "entry_id sets differ: derived=%s committed=%s"
            % (sorted(derived_by_id), sorted(committed_by_id))]
    for entry_id in sorted(derived_by_id):
        derived_entry = derived_by_id[entry_id]
        committed_entry = committed_by_id[entry_id]
        for key in sorted(set(derived_entry) | set(committed_entry)):
            if derived_entry.get(key) != committed_entry.get(key):
                mismatches.append("entry %r key %r differs: derived=%r "
                                  "committed=%r"
                                  % (entry_id, key, derived_entry.get(key),
                                     committed_entry.get(key)))
    return mismatches


# ---------------------------------------------------------------------------
# Report rows (the exact columns 08-09's DATA_SOURCES.md consumes)
# ---------------------------------------------------------------------------

def provenance_rows(spec, manifest_entries):
    """Per-entry markdown provenance row dicts for --report-only:
    entry_id, file, molecule, source URL, ID, PDB complex + DOIs, PLIP
    ref, protonation, halogen/metal, sha256, fetched."""
    rows = []
    fetched = ''
    if isinstance(spec.get('provenance'), dict):
        fetched = spec['provenance'].get('fetched', '')
    committed_by_id = {e['entry_id']: e for e in manifest_entries}
    for entry in spec['entries']:
        manifest_entry = committed_by_id[entry['entry_id']]
        prov = entry['provenance']
        rows.append({
            'entry_id': manifest_entry['entry_id'],
            'file': manifest_entry['file'],
            'molecule': manifest_entry['entry_id'],
            'source_url': prov['source_url'],
            'id': prov['pdb_id'],
            'pdb_complex_dois': '; '.join(
                doi for doi in (prov['entry_doi'], prov['paper_doi'])
                if doi),
            'plip_ref': prov['plip'],
            'protonation': manifest_entry['protonation'],
            'halogen': 'yes' if manifest_entry['halogen_present'] else 'no',
            'metal': 'yes' if manifest_entry['metal_present'] else 'no',
            'sha256': manifest_entry['sha256'][:12],
            'fetched': fetched,
        })
    return rows


def format_report_rows(all_rows):
    lines = [
        '| entry_id | file | molecule | source URL | ID | '
        'PDB complex + DOIs | PLIP ref | protonation | halogen | metal | '
        'sha256 | fetched |',
        '|---|---|---|---|---|---|---|---|---|---|---|---|',
    ]
    for row in all_rows:
        lines.append(
            '| {entry_id} | {file} | {molecule} | {source_url} | {id} | '
            '{pdb_complex_dois} | {plip_ref} | {protonation} | {halogen} | '
            '{metal} | {sha256} | {fetched} |'.format(**row))
    return lines


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def run_build(spec, fetch=False, dry_run=False):
    """Default / --dry-run mode. Returns (exit_code, output lines)."""
    entry_datas = []
    for entry in spec['entries']:
        file_rel, data = resolve_ligand_bytes(spec, entry, fetch, dry_run)
        entry_datas.append((file_rel, data))
    set_payload = build_set_payload(spec, entry_datas)
    committed_payload = parse_manifest_dict(read_json_file(MANIFEST_PATH))
    new_payload = assemble_manifest(committed_payload, set_payload)
    container = make_container('manifest', new_payload)
    if parse_manifest_dict(container) != new_payload:
        _fail("rebuilt manifest failed the re-parse round-trip -- "
              "builder bug")
    if dry_run:
        lines = ["DRY-RUN set %r" % spec['set_id']]
        for key in ('set_id', 'tier', 'title', 'license', 'provenance'):
            lines.append('  %-12s = %r' % (key, set_payload[key]))
        for manifest_entry in set_payload['entries']:
            lines.append('  entry %r:' % manifest_entry['entry_id'])
            for key in sorted(REQUIRED_ENTRY_KEYS):
                lines.append('    %-18s = %r' % (key, manifest_entry[key]))
        mismatches = compare_set_payloads(
            set_payload, committed_set(committed_payload, spec['set_id']))
        if mismatches:
            lines.append('  MISMATCH (%d):' % len(mismatches))
            lines.extend('  - %s' % line for line in mismatches)
            return 2, lines
        lines.append('  derived == committed for set %r (every key, '
                     '%d entries)' % (spec['set_id'], len(entry_datas)))
        return 0, lines
    write_json_atomic(MANIFEST_PATH, container)
    return 0, ["REGENERATED MANIFEST.json for set %r (%d entries, derived "
               "from the resolved ligand bytes; sha256 over the written "
               "files in the same run)" % (spec['set_id'], len(entry_datas))]


def run_report_only():
    """--report-only: no network, no writes. Verify every committed spec
    against MANIFEST.json and print the provenance rows. Returns the
    exit code (1 with every gap named on any mismatch)."""
    committed_payload = parse_manifest_dict(read_json_file(MANIFEST_PATH))
    committed_sets = {s['set_id']: s
                      for s in committed_payload.get('sets', [])}
    problems = []
    all_rows = []
    spec_names = [name for name in sorted(os.listdir(SPECS_DIR))
                  if name.endswith('.json')]
    for name in spec_names:
        spec = load_spec(name[:-len('.json')])
        set_dict = committed_sets.get(spec['set_id'])
        if set_dict is None:
            problems.append("spec %r: set_id %r has no matching set in "
                            "MANIFEST.json" % (name, spec['set_id']))
            continue
        committed_entries = {e['entry_id']: e
                             for e in set_dict.get('entries', [])}
        matched = []
        for entry in spec['entries']:
            committed_entry = committed_entries.get(entry['entry_id'])
            if committed_entry is None:
                problems.append("spec %r entry %r: not present in "
                                "MANIFEST.json" % (name, entry['entry_id']))
                continue
            file_rel = entry_file_rel(spec['set_id'], entry)
            if committed_entry['file'] != file_rel:
                problems.append("spec %r entry %r: spec file %r != "
                                "manifest file %r"
                                % (name, entry['entry_id'], file_rel,
                                   committed_entry['file']))
            target = _entry_target_path(committed_entry['file'])
            if not os.path.isfile(target):
                problems.append("spec %r entry %r: file %r missing under "
                                "aamatch/data/" % (name, entry['entry_id'],
                                                   committed_entry['file']))
            else:
                with open(target, 'rb') as fh:
                    disk_sha = hashlib.sha256(fh.read()).hexdigest()
                if disk_sha != committed_entry['sha256']:
                    problems.append("spec %r entry %r: sha256 mismatch for "
                                    "%r (manifest %s, disk %s)"
                                    % (name, entry['entry_id'],
                                       committed_entry['file'],
                                       committed_entry['sha256'], disk_sha))
            matched.append(committed_entry)
        if len(matched) == len(spec['entries']):
            all_rows.extend(provenance_rows(spec, matched))
    lines = []
    for problem in problems:
        lines.append('GAP: %s' % problem)
    lines.extend(format_report_rows(all_rows))
    if problems:
        lines.append('REPORT: %d gap(s) -- every gap named above'
                     % len(problems))
        for line in lines:
            print(line)
        return 1
    lines.append('REPORT: all specs match the committed manifest '
                 '(%d spec(s), %d entrie(s))'
                 % (len(spec_names), len(all_rows)))
    for line in lines:
        print(line)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description='AA-match demo-data bundling pipeline')
    parser.add_argument('--spec',
                        help='spec path (or bare set_id under '
                             'scripts/demo_specs/)')
    parser.add_argument('--fetch', action='store_true',
                        help='resolve entry bytes via url fetch')
    parser.add_argument('--dry-run', action='store_true',
                        help='derive + per-key compare; write nothing')
    parser.add_argument('--report-only', action='store_true',
                        help='verify all committed specs against '
                             'MANIFEST.json + print provenance rows')
    args = parser.parse_args(argv)
    if args.report_only:
        if not os.path.isdir(SPECS_DIR):
            print('GAP: specs directory %r missing' % SPECS_RELPATH)
            return 1
        try:
            return run_report_only()
        except BuildError as exc:
            print('BUILD ERROR: %s' % exc, file=sys.stderr)
            return 1
    if not args.spec:
        parser.error('--spec is required unless --report-only')
    try:
        spec = load_spec(args.spec)
        code, lines = run_build(spec, fetch=args.fetch,
                                dry_run=args.dry_run)
    except BuildError as exc:
        print('BUILD ERROR: %s' % exc, file=sys.stderr)
        return 1
    except ValueError as exc:  # parse_manifest_dict FormatError family
        print('ERROR: %s' % exc, file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return code


if __name__ == '__main__':
    sys.exit(main())
