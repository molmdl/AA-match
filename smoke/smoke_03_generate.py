"""Headless smoke 03 - count-asserted generate + materialize (plan 02-13).

Run (from WSL, repo root):  bash smoke/run_smoke.sh smoke/smoke_03_generate.py 180
Verdict is carried by the printed marker (exit codes cannot carry verdicts
through the cmd.exe wrapper): grep '=== SMOKE-03 PASS ==='.

Proof chain (materialization research §8.2 SMOKE-03 row + the 02-08
ligand_data contract):

1. MANIFEST.json parsed INSIDE PyMOL (pure gates survive there); the
   benzamide entry is selected programmatically (entry_id match on the
   enumerate_entries rows) -- the candidate list is restricted to
   exactly that row so the block_exclusive ['pi_stacking'] mode cannot
   refuse on a molecule without an aromatic ring (block semantics
   refuse a checked-but-unsupported type; a random acetate pick would
   make the smoke seed-fragile). Deterministic-by-construction.
2. LIGAND DATA (02-08 deviation-3 contract, binding): the fixture is
   loaded into a private _aam_tmp object; geometry.extract_game_atoms
   + geometry.bounding_sphere give {'centroid', 'radius'} and
   capability.ligand_profile over the EXTRACTED atom records + the
   remapped get_bonds block gives 'profile' -- geometry-only
   ligand_data would degrade fail-closed and this very setup would be
   refused by the generator.
3. generate(seed=42) -> level-spec payload; the full container gate
   chain (make_level_spec_container + parse_level_spec_dict) round-
   trips INSIDE PyMOL.
4. materialize(payload) -> registry; object growth asserted EXACTLY
   1 + n*n (n=3 -> 10 new objects); every game atom carries the
   sentinel (segi == 'AAM', b < 0); sentinel count == total game atom
   count; every AA centroid == its effective grid pose within 1e-6
   (float32 rule); detector features['unclassified_aa_atoms'] == 0 on
   the materialized fragments (field verifies capability atom naming).
5. Perturb (translate_to + transform_baked) -> reset_to_grid re-bakes
   the spec poses (never matrix_reset) -> cleanup_game_objects leaves
   the scene EXACTLY at the pre-game snapshot.

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv first /
cwd fallback (never __file__); import aamatch directly (module identity
'aamatch'); every print on ONE line and flushed; explicit space dict in
every iterate; no round() in expressions.

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_03_generate.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []


def check(name, cond, detail=''):
    print('SMOKE-03 %-38s %s %s' % (name, 'PASS' if cond else 'FAIL', detail),
          flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

from aamatch.persistence import read_json_file  # noqa: E402
from aamatch.manifest import parse_manifest_dict, enumerate_entries  # noqa: E402
from aamatch.paths import package_data_path, to_windows_path  # noqa: E402
from aamatch.setup_state import validate_state  # noqa: E402
from aamatch import capability, geometry, placement  # noqa: E402
from aamatch.generator import generate, GRID_SPACING  # noqa: E402
from aamatch.level_spec import (make_level_spec_container,  # noqa: E402
                                parse_level_spec_dict)
from aamatch.detector import extract_features  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

TOL = 1e-6  # float32 coordinate-storage rule (02-09; research §6.2)

# --- 1. Manifest + candidate selection (parsed INSIDE PyMOL) -----------------
entries = []
benz = None
try:
    container = read_json_file(os.path.join(
        _ROOT, 'aamatch', 'data', 'MANIFEST.json'))
    payload_manifest = parse_manifest_dict(container)
    entries = enumerate_entries(payload_manifest)
    check('manifest parse', len(entries) == 2,
          'entries=%d' % len(entries))
    benz_rows = [row for row in entries
                 if row['entry_id'] == 'benzamide']
    benz = benz_rows[0] if benz_rows else None
    check('benzamide entry', benz is not None,
          benz['file'] if benz else 'entry_id benzamide not in manifest')
except Exception:
    traceback.print_exc()
    check('manifest parse', False, 'raised (see traceback above)')


def _remap_ligand_bonds(records, bonds, index_to_id):
    """Remap get_bonds 0-based WALK positions into positions in the
    (object, id)-sorted ligand record list (02-09 pinned mapping:
    whole-object selection => walk position i -> index_to_id[i+1] ->
    atom id -> position in the sorted records; detector validates
    fail-closed)."""
    lig = sorted((r for r in records if r['side'] == 'lig'),
                 key=lambda r: r['id'])
    id_pos = dict((r['id'], i) for i, r in enumerate(lig))
    out = []
    for (i, j, order) in bonds:
        out.append((id_pos[index_to_id[i + 1]],
                    id_pos[index_to_id[j + 1]], int(order)))
    return lig, out


# --- 2. ligand_data with the chemistry profile (02-08 contract) ---------------
ligand_data = None
try:
    tmp_name = cmd.get_unused_name('_aam_tmp')
    try:
        winpath = to_windows_path(
            package_data_path('data', benz['file']))
        cmd.load(winpath, tmp_name)
        n_tmp = cmd.count_atoms(tmp_name)
        check('ligand load', n_tmp == benz['atom_count'],
              'atoms=%d want %d' % (n_tmp, benz['atom_count']))

        records = geometry.extract_game_atoms()
        check('extract side', [r['side'] for r in records].count('lig')
              == benz['atom_count'],
              '%d lig records' % len(records))
        center, radius = geometry.bounding_sphere(records)
        check('bounding sphere', radius > 0.0,
              'centroid=(%.3f, %.3f, %.3f) radius=%.3f'
              % (center + (radius,)))

        bonds, index_to_id = geometry.ligand_bonds(tmp_name)
        lig_records, lig_bonds = _remap_ligand_bonds(
            records, bonds, index_to_id)
        check('ligand bonds', len(lig_bonds) == benz['bond_count'],
              'bonds=%d want %d (0-based remap over %d records)'
              % (len(lig_bonds), benz['bond_count'], len(lig_records)))

        profile = capability.ligand_profile(lig_records, lig_bonds)
        check('profile present',
              isinstance(profile, dict)
              and 'ring_count' in profile
              and 'charge_signs' in profile,
              'keys=%s ring_count=%s'
              % (sorted(profile), profile.get('ring_count')))
        check('profile ring+donor',
              profile.get('ring_count', 0) >= 1
              and profile.get('has_acceptor'),
              'ring_count=%s donor=%s acceptor=%s'
              % (profile.get('ring_count'), profile.get('has_donor'),
                 profile.get('has_acceptor')))
        # THE CONTRACT: geometry + chemistry TOGETHER (02-08 dev 3).
        ligand_data = {'centroid': center, 'radius': radius,
                       'profile': profile}
    finally:
        cmd.delete(tmp_name)       # temps never leak
    leftover = [n for n in cmd.get_names('objects')
                if n.startswith('_aam_tmp')]
    check('no tmp leak (pre-generate)', not leftover,
          ', '.join(leftover))
except Exception:
    traceback.print_exc()
    check('ligand_data build', False, 'raised (see traceback above)')
    ligand_data = None

# --- 3. Generate + container gates inside PyMOL -------------------------------
payload = None
n = None
try:
    setup = validate_state({'interaction_mode': 'block_exclusive',
                            'allowed_interactions': ['pi_stacking'],
                            'molecules_per_level': 1,
                            'difficulty_levels': 3})
    check('setup validate',
          setup['interaction_mode'] == 'block_exclusive'
          and setup['allowed_interactions'] == ['pi_stacking']
          and setup['molecules_per_level'] == 1
          and setup['difficulty_levels'] == 3,
          str(setup))

    candidates = [benz]   # deterministic pick: block mode refuses a
                          # checked-but-unsupported type; acetate has no
                          # aromatic ring (see module docstring).
    payload = generate(42, setup, candidates, ligand_data,
                       setup['difficulty_levels'])
    level0 = payload['levels'][0]
    n = level0['difficulty']['grid_n']
    check('generate payload',
          payload['seed'] == 42
          and len(payload['levels']) == 3
          and n == 3
          and len(level0['molecules']) == 1
          and len(level0['molecules'][0]['grid']['slots']) == n * n
          and level0['molecules'][0]['grid']['n'] == n,
          'levels=%d n=%s slots=%d'
          % (len(payload['levels']), n,
             len(level0['molecules'][0]['grid']['slots'])))
    check('required mode',
          level0['molecules'][0]['required'] == {
              'mode': 'list',
              'items': [{'type': 'pi_stacking', 'count': 1}]},
          str(level0['molecules'][0]['required']))

    # Container gate chain survives inside PyMOL (parse returns the
    # payload UNCHANGED -- Level-1 passthrough).
    parsed = parse_level_spec_dict(make_level_spec_container(payload))
    check('spec gate round-trip', parsed == payload,
          'parse_level_spec_dict(make_level_spec_container(payload)) '
          'identity')
except Exception:
    traceback.print_exc()
    check('generate', False, 'raised (see traceback above)')
    payload = None

# --- 4. Materialize + count/pose/sentinel asserts -----------------------------
registry = None
pre_names = list(cmd.get_names('objects'))
try:
    check('clean pre-game scene',
          not [n0 for n0 in pre_names
               if n0.startswith(geometry.GAME_PREFIX)],
          'pre names: %s' % pre_names)

    registry = placement.materialize(payload, level_index=0)
    n_expected = 1 + n * n
    post_names = list(cmd.get_names('objects'))
    grew = sorted(set(post_names) - set(pre_names))
    check('object growth', len(grew) == n_expected,
          'grew=%d want %d (1 ligand + %d slots)'
          % (len(grew), n_expected, n * n))
    check('registry shape',
          registry['level_index'] == 0
          and registry['pre_game_names'] == pre_names
          and len(registry['molecules']) == 1
          and len(registry['molecules'][0]['slots']) == n * n,
          'molecules=%d slots=%d'
          % (len(registry['molecules']),
             len(registry['molecules'][0]['slots'])))

    molecule = registry['molecules'][0]
    lig_obj, lig_ids = molecule['ligand']
    check('ligand sentinel ids',
          cmd.count_atoms(lig_obj) == benz['atom_count']
          and len(lig_ids) == benz['atom_count']
          and lig_ids == sorted(lig_ids),
          'atoms=%d ids=%d' % (cmd.count_atoms(lig_obj),
                               len(lig_ids)))

    # Sentinel sweep: EVERY game atom in EVERY game object.
    total_atoms = 0
    sentinel_atoms = 0
    bad = []
    for name in sorted(geometry.game_object_names()):
        rows = []
        cmd.iterate(name, 'stored.append((segi, b))',
                    space={'stored': rows})
        n_here = len(rows)
        total_atoms += n_here
        ok_here = sum(1 for (segi, bf) in rows
                      if segi == 'AAM' and bf < 0.0)
        sentinel_atoms += ok_here
        if ok_here != n_here:
            bad.append('%s:%d/%d' % (name, ok_here, n_here))
    check('sentinel coverage',
          sentinel_atoms == total_atoms and not bad,
          '%d/%d atoms tagged%s'
          % (sentinel_atoms, total_atoms,
             ' BAD: ' + ', '.join(bad) if bad else ''))
    check('sentinel count == game atoms',
          sentinel_atoms == total_atoms > 0,
          'sentinels=%d atoms=%d' % (sentinel_atoms, total_atoms))
    check('sentinel b-factor selector',
          cmd.count_atoms('b < 0 and segi AAM') == total_atoms,
          '"b < 0 and segi AAM" selects %d/%d'
          % (cmd.count_atoms('b < 0 and segi AAM'), total_atoms))

    # Pose agreement with the SPEC (1e-6 float32 rule): per-slot
    # centroid == grid_pose.position + placement.offset.
    worst = 0.0
    pose_fail = []
    mol_payload = payload['levels'][0]['molecules'][0]
    offset = molecule['offset']
    for slot in mol_payload['grid']['slots']:
        target = placement.effective_position(
            slot['grid_pose']['position'], offset)
        aa_obj = molecule['slots'][slot['slot_id']][0]
        centroid = geometry.centroid_of(aa_obj)
        drift = max(abs(centroid[i] - target[i]) for i in range(3))
        worst = max(worst, drift)
        if drift > TOL:
            pose_fail.append('%s(%.2g)' % (slot['slot_id'], drift))
    check('spec pose agreement', not pose_fail,
          'worst=%.2g tol=%.0e%s'
          % (worst, TOL,
             ' FAIL: ' + ', '.join(pose_fail) if pose_fail else ''))

    # Phase-2 detector contract: materialized fragments classify 100%
    # against capability's atom naming (field verification; any miss
    # reconciles cap/backbone names in the detector's known set --
    # never thresholds).
    all_records = geometry.extract_game_atoms()
    lig_bonds_live, lig_index = geometry.ligand_bonds(lig_obj)
    lig_sorted, lig_remap = _remap_ligand_bonds(
        all_records, lig_bonds_live, lig_index)
    features = extract_features(all_records, lig_remap)
    unclassified = features['unclassified_aa_atoms']
    diag = ''
    if unclassified:
        names = []
        for rec in all_records:
            if rec['side'] == 'aa' and rec['elem'].upper() != 'H':
                names.append('%s:%s' % (rec['resn'], rec['name']))
        diag = 'unclassified=%d atoms=%s' % (
            unclassified, sorted(set(names))[:12])
    else:
        diag = 'aa_objects=%d atoms=%d' % (
            len(features['aa']),
            sum(1 for r in all_records if r['side'] == 'aa'))
    check('unclassified aa atoms == 0', unclassified == 0, diag)
except Exception:
    traceback.print_exc()
    check('materialize', False, 'raised (see traceback above)')
    registry = None

# --- 5. Perturb -> reset -> cleanup -------------------------------------------
try:
    molecule = registry['molecules'][0]
    mol_payload = payload['levels'][0]['molecules'][0]
    offset = molecule['offset']
    slot0 = mol_payload['grid']['slots'][0]
    aa0 = molecule['slots'][slot0['slot_id']][0]

    # Deliberate perturbations through the baked primitives.
    away = (placement.effective_position(
        slot0['grid_pose']['position'], offset))
    perturbed = (away[0] + 5.0, away[1] - 3.0, away[2] + 7.0)
    placement.translate_to(aa0, perturbed)
    c = geometry.centroid_of(aa0)
    check('translate_to perturb',
          max(abs(c[i] - perturbed[i]) for i in range(3)) < TOL,
          'landed (%.2f, %.2f, %.2f)' % c)

    # transform_baked: identity rotation + translation = pure shift,
    # per-atom asserted against coords_of snapshots.
    before = geometry.coords_of(aa0)
    M = [1.0, 0.0, 0.0, 0.5,
         0.0, 1.0, 0.0, -0.25,
         0.0, 0.0, 1.0, 1.5,
         0.0, 0.0, 0.0, 1.0]
    placement.transform_baked(aa0, M)
    after = geometry.coords_of(aa0)
    t = (0.5, -0.25, 1.5)
    ok_bake = len(before) == len(after) and all(
        abs(after[i][1 + a] - (before[i][1 + a] + t[a])) < TOL
        for i in range(len(before)) for a in range(3))
    check('transform_baked shift', ok_bake,
          'per-atom shift within %.0e over %d atoms' % (TOL,
                                                        len(after)))

    # SPEC REPLAY reset: every registered slot re-bakes to its grid
    # pose from the perturbed current pose.
    placement.reset_to_grid(payload, registry, level_index=0)
    worst = 0.0
    reset_fail = []
    for slot in mol_payload['grid']['slots']:
        target = placement.effective_position(
            slot['grid_pose']['position'], offset)
        centroid = geometry.centroid_of(
            molecule['slots'][slot['slot_id']][0])
        drift = max(abs(centroid[i] - target[i]) for i in range(3))
        worst = max(worst, drift)
        if drift > TOL:
            reset_fail.append('%s(%.2g)' % (slot['slot_id'], drift))
    check('reset_to_grid replay', not reset_fail,
          'worst=%.2g tol=%.0e%s'
          % (worst, TOL,
             ' FAIL: ' + ', '.join(reset_fail) if reset_fail else ''))

    # Clean teardown: prefix deletes -> scene EXACTLY pre-game.
    result = placement.cleanup_game_objects()
    post_names = list(cmd.get_names('objects'))
    check('cleanup count', result['deleted'] == 1 + n * n,
          'deleted=%d want %d' % (result['deleted'], 1 + n * n))
    check('teardown exact',
          post_names == pre_names and not any(
              n0.startswith(geometry.GAME_PREFIX) for n0 in post_names),
          'post=%s' % post_names)
except Exception:
    traceback.print_exc()
    check('perturb/reset/cleanup', False,
          'raised (see traceback above)')
    placement.cleanup_game_objects()   # never leave game objects behind

print('SMOKE-ENV grid_spacing=%.1f n=%s' % (GRID_SPACING, n), flush=True)

# --- Verdict marker (the SOLE verdict carrier) -------------------------------
print('=== SMOKE-03 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'), flush=True)
