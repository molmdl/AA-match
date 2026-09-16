"""Headless smoke 12 - upload extraction bridge E2E (plan 04-08).

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_12_upload_e2e.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-12 PASS ==='.

Proves aamatch/upload.py's prepare_uploaded_set -- the cmd-tier bridge
between the 04-06 pure split/row helpers and the 04-04 ligand_content
seams -- end-to-end in REAL headless PyMOL (cmd tier only, NO
QApplication):

PART 1  read_sdfstr/file-load parity (research OQ2, open_questions
        probe 2). acetate.sdf loads TWICE into fresh unused names --
        once via cmd.load(to_windows_path(...)), once via
        cmd.read_sdfstr(file_text) -- and the smoke asserts identical
        count_atoms, count_states, the engine._remap_ligand_bonds
        bond-order MULTISET (SMOKE-02 order-multiset convention), and
        formal-charge sums over the extracted records. Guarded by
        hasattr(cmd, 'read_sdfstr') (abort with a clear FAIL line).
        Both temp objects are deleted and the scene is asserted back
        at baseline.
PART 2  2-record SDF E2E. benzamide.sdf + acetate.sdf concatenated ->
        game_file.split_sdf_records -> check_upload_supply ->
        upload.prepare_uploaded_set: 2 rows (entry_ids 'mol-001' /
        'mol-002', content keys 'uploads/mol-001.sdf' /
        'uploads/mol-002.sdf', each row sha256 == the sha256 of its
        record text, scene byte-unchanged afterwards). Then the full
        generator flow: engine.new_game(validate_state(DEFAULTS),
        999, candidates=rows, ligand_content=content) +
        engine.materialize(payload, 0, ligand_content=content) -- the
        materialized ligand objects exist and their atom counts match
        the rows' atom_count -- cleanup + scene-baseline assert.
PART 3  timing datum (Decision 8 evidence for UPLOAD_MAX_RECORDS):
        prepare_uploaded_set is re-timed over the 2 records with
        time.time() deltas; the printed line
        'upload extraction: %d records in %.3f s (per-record %.4f s)'
        is the recorded datum copied verbatim into 04-08-SUMMARY.md.
PART 4  MOL2 2-segment probe (Decision 14, research open_questions
        probe 1). A minimal 2-segment MOL2 string (leading comment
        line, two @<TRIPOS>MOLECULE segments of 2 atoms / 1 bond
        each) splits via game_file.split_mol2_segments, then
        prepare_uploaded_set(segments, 'mol2') is probed. SUCCESS
        path: 2 rows with .mol2 keys, a level materializes from them,
        'MOL2-MULTI OK (2-segment split+load verified)'. FAILURE
        path: 'MOL2-MULTI UNVERIFIED (<reason>) -- activating
        fallback' -- the Decision-14 mechanical fallback then applies
        (see 04-08-PLAN.md Task 2 / PART 4).

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv
first / cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch'); every print on ONE line and flushed; explicit
space dicts in every iterate; no round() in expressions; no cmd API
that may throw inside an eager check-detail string (the 03-04 rule).

Python floor: runs inside PyMOL's Windows Python (3.9); written
3.6-safe.
"""
import hashlib
import os
import sys
import time
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_12_upload_e2e.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []


def check(name, cond, detail=''):
    print('SMOKE-12 %-44s %s %s' % (name, 'PASS' if cond else 'FAIL',
                                     detail), flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

from aamatch import engine, game_file, placement, setup_state  # noqa: E402
from aamatch import upload  # noqa: E402
from aamatch.paths import to_windows_path  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

# --- 0. Baseline scene snapshot + fixture texts -------------------------
pre_names = list(cmd.get_names('objects'))
check('clean pre-game scene',
      not [n0 for n0 in pre_names if n0.startswith('_aam_')],
      'pre names: %s' % pre_names)


def _read_ligand(filename):
    raw = None
    with open(os.path.join(_ROOT, 'aamatch', 'data', 'ligands',
                           filename), 'rb') as fh:
        raw = fh.read()
    return raw.decode('utf-8')


benz_text = None
acet_text = None
try:
    benz_text = _read_ligand('benzamide.sdf')
    acet_text = _read_ligand('acetate.sdf')
    check('fixture texts read', True,
          'benzamide=%dB acetate=%dB'
          % (len(benz_text), len(acet_text)))
except Exception:
    traceback.print_exc()
    check('fixture texts read', False, 'raised (see traceback above)')

# ============ PART 1: read_sdfstr / file-load PARITY (OQ2) =============
have_sdfstr = hasattr(cmd, 'read_sdfstr')
check('cmd.read_sdfstr available', have_sdfstr,
      'research open-questions probe-2 one-liner guard')

if have_sdfstr and acet_text is not None:
    # get_unused_name reservations are NOT atomic: two calls made BEFORE
    # any load return the same free name (this build suffixes '01'), and
    # a load/string-read into an EXISTING name APPENDS a state (the
    # placement.py:37-39 pitfall). Acquire the second name only after
    # the first load has materialized the first object.
    name_a = cmd.get_unused_name('_aam_tmp')
    try:
        cmd.load(to_windows_path(os.path.join(
            _ROOT, 'aamatch', 'data', 'ligands', 'acetate.sdf')), name_a)
        name_b = cmd.get_unused_name('_aam_tmp')
        check('parity probe names differ', name_a != name_b,
              'a=%r b=%r' % (name_a, name_b))
        cmd.read_sdfstr(acet_text, name_b)
        n_a = cmd.count_atoms(name_a)
        n_b = cmd.count_atoms(name_b)
        check('parity: atom counts identical', n_a == n_b,
              'load=%d str=%d' % (n_a, n_b))
        s_a = cmd.count_states(name_a)
        s_b = cmd.count_states(name_b)
        check('parity: state counts identical and 1',
              s_a == s_b == 1, 'load=%d str=%d' % (s_a, s_b))
        from aamatch import geometry
        rec_all = geometry.extract_game_atoms()
        lig_a, bonds_a = engine._remap_ligand_bonds(
            [r for r in rec_all if r['object'] == name_a], [name_a])
        lig_b, bonds_b = engine._remap_ligand_bonds(
            [r for r in rec_all if r['object'] == name_b], [name_b])
        orders_a = sorted(int(t[2]) for t in bonds_a)
        orders_b = sorted(int(t[2]) for t in bonds_b)
        check('parity: bond-order multiset identical',
              orders_a == orders_b,
              'load=%s str=%s' % (orders_a, orders_b))
        charge_a = sum(int(r['formal_charge']) for r in lig_a)
        charge_b = sum(int(r['formal_charge']) for r in lig_b)
        check('parity: formal-charge sums identical',
              charge_a == charge_b,
              'load=%d str=%d' % (charge_a, charge_b))
    except Exception:
        traceback.print_exc()
        check('parity probe run', False,
              'raised (see traceback above)')
    finally:
        for name in (name_a, name_b):
            if name in cmd.get_names('objects'):
                cmd.delete(name)
    check('parity probe temps deleted', cmd.get_names('objects')
          == pre_names, 'post names: %s' % cmd.get_names('objects'))
else:
    check('parity probe run', False,
          'skipped: read_sdfstr missing on this build')

# ================= PART 2: 2-record SDF end-to-end =====================
records = None
rows = None
content = None
try:
    # The bundled fixtures are terminator-less single records (they end
    # at 'M  END', no trailing '$$$$'): a raw concat would parse as ONE
    # record. Explicit terminators make the intended 2-record supply
    # (the plan's "benzamide+acetate text concatenated (2 records)").
    combined = benz_text + '$$$$\n' + acet_text + '$$$$\n'
    records = game_file.split_sdf_records(combined)
    check('combined text splits into 2 records', len(records) == 2,
          'records=%d' % len(records))
    game_file.check_upload_supply(records, 'sdf',
                                  'smoke12-combined.sdf')
    check('supply check accepts 2 sdf records', True, '')
except Exception:
    traceback.print_exc()
    check('combined text splits into 2 records', False,
          'raised (see traceback above)')
    records = None

if records is not None:
    try:
        rows, content = upload.prepare_uploaded_set(records, 'sdf')
        check('prepare_uploaded_set returns 2 rows', len(rows) == 2,
              'rows=%d' % len(rows))
        entry_ids = [row['entry_id'] for row in rows]
        check('synthetic entry ids mol-001/mol-002',
              entry_ids == ['mol-001', 'mol-002'],
              'entry_ids=%s' % entry_ids)
        keys = sorted(content)
        check('content keys are the synthetic file keys',
              keys == ['uploads/mol-001.sdf', 'uploads/mol-002.sdf'],
              'keys=%s' % keys)
        digests = [hashlib.sha256(rec.encode('utf-8')).hexdigest()
                   for rec in records]
        sha_ok = (len(rows) == 2 and len(digests) == 2
                  and rows[0]['sha256'] == digests[0]
                  and rows[1]['sha256'] == digests[1])
        check('row sha256 == record-text sha256', sha_ok,
              'decision-19 record-text hashes')
        verbatim_ok = (len(rows) == 2 and len(records) == 2
                       and content[rows[0]['file']] == records[0]
                       and content[rows[1]['file']] == records[1])
        check('content text is the record text verbatim', verbatim_ok,
              '')
        game_file.validate_uploaded_rows(rows)
        check('validate_uploaded_rows passes', True, '')
        check('prepare leaves scene at baseline',
              cmd.get_names('objects') == pre_names,
              'temp discipline: no leaks')
    except Exception:
        traceback.print_exc()
        check('prepare_uploaded_set 2-record run', False,
              'raised (see traceback above)')
        rows = None
        content = None

# --- 2b. full generator flow through the 04-04 seams --------------------
payload = None
registry = None
if rows is not None and content is not None:
    try:
        upload_setup = setup_state.validate_state(
            dict(setup_state.DEFAULTS, demo_set_id='uploaded'))
        payload, rows_out = engine.new_game(
            upload_setup, 999, candidates=rows,
            ligand_content=content)
        check('new_game incl. uploaded candidates leaves scene '
              'untouched', cmd.get_names('objects') == pre_names,
              'temp extraction loads from text, deleted in finally')
        lig_files = [m['ligand']['file']
                     for m in payload['levels'][0]['molecules']]
        check('level-0 payload drawn from uploaded rows',
              sorted(lig_files) == ['uploads/mol-001.sdf',
                                    'uploads/mol-002.sdf'],
              'files=%s' % sorted(lig_files))
    except Exception:
        traceback.print_exc()
        check('new_game with uploaded rows', False,
              'raised (see traceback above)')
        payload = None

if payload is not None:
    try:
        registry = engine.materialize(payload, 0,
                                      ligand_content=content)
        rows_by_file = dict((row['file'], row) for row in rows)
        counts_ok = True
        missing = []
        detail_bits = []
        names_now = list(cmd.get_names('objects'))
        for m0, mol in enumerate(registry['molecules']):
            lig_obj = mol['ligand'][0]
            file_key = payload['levels'][0]['molecules'][m0][
                'ligand']['file']
            if lig_obj not in names_now:
                counts_ok = False
                missing.append(lig_obj)
                continue
            n_atoms = cmd.count_atoms(lig_obj)
            want = int(rows_by_file[file_key]['atom_count'])
            detail_bits.append('%s=%d/%d' % (file_key, n_atoms, want))
            if n_atoms != want:
                counts_ok = False
        check('materialized ligands exist, counts match rows',
              counts_ok and not missing,
              ' '.join(detail_bits)
              + (' missing=%s' % missing if missing else ''))
    except Exception:
        traceback.print_exc()
        check('materialize uploaded payload', False,
              'raised (see traceback above)')
        registry = None

try:
    placement.cleanup_game_objects()
    check('cleanup restores baseline scene',
          cmd.get_names('objects') == pre_names,
          'post names: %s' % list(cmd.get_names('objects')))
except Exception:
    traceback.print_exc()
    check('cleanup restores baseline scene', False,
          'raised (see traceback above)')

# ================= PART 3: extraction timing datum =====================
if records is not None:
    try:
        t_start = time.time()
        rows_t, content_t = upload.prepare_uploaded_set(records, 'sdf')
        dt = time.time() - t_start
        print('upload extraction: %d records in %.3f s (per-record '
              '%.4f s)' % (len(records), dt, dt / len(records)),
              flush=True)
        check('timed run leaves scene at baseline',
              cmd.get_names('objects') == pre_names,
              'rows=%d (Decision 8 datum)' % len(rows_t))
    except Exception:
        traceback.print_exc()
        check('timed extraction run', False,
              'raised (see traceback above)')
else:
    check('timed extraction run', False, 'skipped: PART 2 split failed')

# ================= PART 4: MOL2 2-segment probe ========================
mol2_text = (
    '# SMOKE-12 MOL2 probe: leading comment before the first segment\n'
    '@<TRIPOS>MOLECULE\n'
    'SEG-ONE\n'
    ' 2 1 0 0 0\n'
    'SMALL\n'
    'NO_CHARGES\n'
    '\n'
    '@<TRIPOS>ATOM\n'
    '      1 C1          0.0000    0.0000    0.0000 C.3     1 UNK1    '
    '    0.0000\n'
    '      2 H1          1.0000    0.0000    0.0000 H       1 UNK1    '
    '    0.0000\n'
    '@<TRIPOS>BOND\n'
    '     1    1    2 1\n'
    '@<TRIPOS>MOLECULE\n'
    'SEG-TWO\n'
    ' 2 1 0 0 0\n'
    'SMALL\n'
    'NO_CHARGES\n'
    '\n'
    '@<TRIPOS>ATOM\n'
    '      1 C1          0.0000    0.0000    0.0000 C.3     1 UNK1    '
    '    0.0000\n'
    '      2 H1         -1.0000    0.0000    0.0000 H       1 UNK1    '
    '    0.0000\n'
    '@<TRIPOS>BOND\n'
    '     1    1    2 1\n')

segments = game_file.split_mol2_segments(mol2_text)
check('mol2 probe splits into 2 segments', len(segments) == 2,
      'segments=%d (leading comment attaches to segment 1)'
      % len(segments))

mol2_rows = None
mol2_content = None
try:
    mol2_rows, mol2_content = upload.prepare_uploaded_set(segments,
                                                          'mol2')
    check('mol2 2-segment prepare builds 2 rows',
          len(mol2_rows) == 2
          and sorted(mol2_content) == ['uploads/mol-001.mol2',
                                       'uploads/mol-002.mol2'],
          'rows=%d keys=%s' % (len(mol2_rows), sorted(mol2_content)))
except Exception as exc:
    print('MOL2-MULTI UNVERIFIED (%s: %s) -- activating fallback'
          % (type(exc).__name__, str(exc)), flush=True)
    check('MOL2-MULTI verdict definite', False,
          'unverified: %s: %s' % (type(exc).__name__, str(exc)[:60]))

if mol2_rows is not None:
    try:
        payload4, _ = engine.new_game(
            setup_state.validate_state(
                dict(setup_state.DEFAULTS, demo_set_id='uploaded')),
            555, candidates=mol2_rows, ligand_content=mol2_content)
        engine.materialize(payload4, 0, ligand_content=mol2_content)
        print('MOL2-MULTI OK (2-segment split+load verified)',
              flush=True)
        check('mol2 materialize leaves game objects', True,
              'registry level 0 materialized')
        placement.cleanup_game_objects()
        check('mol2 probe cleanup restores baseline',
              cmd.get_names('objects') == pre_names,
              'post names: %s' % list(cmd.get_names('objects')))
    except Exception:
        traceback.print_exc()
        check('mol2 materialize flow', False,
              'raised (see traceback above)')
        placement.cleanup_game_objects()

# --- Verdict marker (the SOLE verdict carrier) --------------------------
print('=== SMOKE-12 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
