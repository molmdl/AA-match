"""Headless smoke 04 - count-asserted E2E game loop (plan 02-14).

Run (from WSL, repo root):  bash smoke/run_smoke.sh smoke/smoke_04_e2e.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-04 PASS ==='.

What it proves (ROADMAP Phase-2 criterion 4, [HEADLESS] E2E; research
SS8.2 SMOKE-04 row):

PART A (happy path) -- engine.new_game(block_exclusive ['pi_stacking'],
molecules 1, D 3, seed 42, candidates restricted to the benzamide row)
-> materialize (object growth EXACTLY 1 + n*n) -> grid poses score 0.0
-> scripted placement of the required aromatic AA so its ring sits 4.5
A directly above the ligand benzene ring (a baked normal-alignment step
first when the fragment's natural ring plane is not within the 30-deg
parallel window -- transform_baked; then translate via place_aa) ->
detect returns >= 1 pi_stacking record on the placed object (subtype P,
offset ~ 0) -> score_current == 1.0.

PART B (rotation invariance) -- cmd.rotate('z', 37.0, <all game
objects>, camera=0, origin=ligand ring center) BAKES the whole scene
equally (probe SS6.3 pattern); re-detect: the record set is byte-equal
structurally (types/objects/ids/roles) and metrics drift only by the
float32-storage budget pinned below; score still 1.0.

PART C (reset replay) -- engine.reset_to_grid() re-bakes every AA to
its spec grid pose (worst drift within the 1e-6 float32 tolerance),
re-detect gives ZERO pi_stacking records and score_current == 0.0;
cleanup_game_objects leaves the scene EXACTLY at the pre-game snapshot.

FLOAT32 METRIC BUDGET (why Part B is not asserted at 1e-6 uniformly):
PyMOL stores coordinates as float32 (02-09). A baked 90-deg-class
rotation re-stores every atom: each coordinate picks up up to ~0.5 ulp
(~1e-6 at the ~15 A magnitudes of this scene), so DISTANCE metrics can
drift a few e-6 and ANGLE metrics (unit-normal recomputation from the
re-stored coords, then acos) can drift ~1e-6 rad ~ 6e-5 deg. Part B
asserts structural equality EXACTLY and metric drift within the
documented budgets: distances/offsets <= 5e-6, angles <= 3e-4 deg (each
budget printed with the worst observed drift).

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv first
/ cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch'); every print on ONE line and flushed; explicit
space dicts in every iterate; no round() in expressions.

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import math
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_04_e2e.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []


def check(name, cond, detail=''):
    print('SMOKE-04 %-38s %s %s' % (name, 'PASS' if cond else 'FAIL', detail),
          flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

from aamatch.persistence import read_json_file  # noqa: E402
from aamatch.manifest import parse_manifest_dict, enumerate_entries  # noqa: E402
from aamatch.setup_state import validate_state  # noqa: E402
from aamatch import capability, engine, geometry, placement  # noqa: E402
from aamatch.detector import extract_features  # noqa: E402
from aamatch.thresholds import PISTACK_ANGLE_TOL_DEG  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

TOL = 1e-6          # float32 pose tolerance (02-09; research SS6.2)
METRIC_D_TOL = 5e-6     # float32-storage distance-metric drift budget
METRIC_ANGLE_TOL = 3e-4  # float32-storage angle-metric drift budget (deg)


def _remap_ligand_bonds(records, bonds, index_to_id):
    """Remap get_bonds 0-based WALK positions into positions in the
    (object, id)-sorted single-ligand record list (02-09 pinned mapping;
    engine.engine._remap_ligand_bonds is the productionized multi-ligand
    home -- the smoke keeps the pinned single-object form for clarity)."""
    lig = sorted((r for r in records if r['side'] == 'lig'),
                 key=lambda r: r['id'])
    id_pos = dict((r['id'], i) for i, r in enumerate(lig))
    out = []
    for (i, j, order) in bonds:
        out.append((id_pos[index_to_id[i + 1]],
                    id_pos[index_to_id[j + 1]], int(order)))
    return lig, out


# --- tiny vec helpers (smoke-local) --------------------------------
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(s, a):
    return (s * a[0], s * a[1], s * a[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(a):
    return math.sqrt(_dot(a, a))


def _unit(a):
    n = _norm(a)
    return (a[0] / n, a[1] / n, a[2] / n)


def _tofloat(pt):
    return (float(pt[0]), float(pt[1]), float(pt[2]))


def _alignment_matrix(n_from, n_to, pivot):
    """Row-major homogeneous 4x4 rotating unit vector n_from onto
    unit vector n_to (Rodrigues) about ``pivot`` -- for the baked
    ring-plane alignment step."""
    k_raw = _cross(n_from, n_to)
    klen = _norm(k_raw)
    if klen < 1e-12:
        return None                      # already parallel/antiparallel
    k = _unit(k_raw)
    c = max(-1.0, min(1.0, _dot(n_from, n_to)))
    s = math.sqrt(max(0.0, 1.0 - c * c))
    kx, ky, kz = k
    one_c = 1.0 - c
    R = (
        (c + kx * kx * one_c, kx * ky * one_c - kz * s,
         kx * kz * one_c + ky * s),
        (ky * kx * one_c + kz * s, c + ky * ky * one_c,
         ky * kz * one_c - kx * s),
        (kz * kx * one_c - ky * s, kz * ky * one_c + kx * s,
         c + kz * kz * one_c),
    )
    # t = pivot - R . pivot  (rotation about the pivot point)
    t = [pivot[i] - sum(R[i][j] * pivot[j] for j in range(3))
         for i in range(3)]
    return [R[0][0], R[0][1], R[0][2], t[0],
            R[1][0], R[1][1], R[1][2], t[1],
            R[2][0], R[2][1], R[2][2], t[2],
            0.0, 0.0, 0.0, 1.0]


def _record_key(r):
    """Structural record identity: everything except the metrics."""
    return (r['type'], r['aa']['object'], tuple(r['aa']['atom_ids']),
            r['aa']['resn'], r['aa']['resi'], r['aa']['role'],
            r['lig']['object'], tuple(r['lig']['atom_ids']),
            r['lig']['role'], r.get('formed'))


# --- 0. Scene snapshot + candidate selection (parsed INSIDE PyMOL) ----
pre_names = list(cmd.get_names('objects'))
benz = None
try:
    check('clean pre-game scene',
          not [n0 for n0 in pre_names
               if n0.startswith(geometry.GAME_PREFIX)],
          'pre names: %s' % pre_names)
    container = read_json_file(os.path.join(
        _ROOT, 'aamatch', 'data', 'MANIFEST.json'))
    entries = enumerate_entries(parse_manifest_dict(container))
    benz_rows = [row for row in entries
                 if row['entry_id'] == 'benzamide']
    benz = benz_rows[0] if benz_rows else None
    check('benzamide candidate', benz is not None,
          benz['file'] if benz else 'entry_id benzamide not in manifest')
except Exception:
    traceback.print_exc()
    check('manifest parse', False, 'raised (see traceback above)')

# ============================ PART A: HAPPY PATH ========================
payload = None
registry = None
n = None
mol_payload = None
required = None
records_a = None
records_b = None
lig_ring = None
aa_obj = None
slot_id = None
try:
    setup = validate_state({'interaction_mode': 'block_exclusive',
                            'allowed_interactions': ['pi_stacking'],
                            'molecules_per_level': 1,
                            'difficulty_levels': 3})
    payload, rows = engine.new_game(setup, 42, candidates=[benz])
    check('new_game scene untouched',
          list(cmd.get_names('objects')) == pre_names,
          'new_game loads temps only and deletes them')

    level0 = payload['levels'][0]
    n = level0['difficulty']['grid_n']
    mol_payload = level0['molecules'][0]
    required = mol_payload['required']
    check('generate payload',
          payload['seed'] == 42
          and len(payload['levels']) == 3
          and n == 3
          and len(level0['molecules']) == 1
          and len(mol_payload['grid']['slots']) == n * n,
          'levels=%d n=%s slots=%d'
          % (len(payload['levels']), n,
             len(mol_payload['grid']['slots'])))
    check('required mode block_exclusive',
          required == {'mode': 'list',
                       'items': [{'type': 'pi_stacking', 'count': 1}]},
          str(required))

    registry = engine.materialize(payload, level_index=0)
    post_names = list(cmd.get_names('objects'))
    grew = sorted(set(post_names) - set(pre_names))
    n_expected = 1 + n * n
    check('materialize object growth',
          len(grew) == n_expected,
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

    # Grid pose: nothing formed yet.
    records0 = engine.detect()
    pi0 = [r for r in records0 if r['type'] == 'pi_stacking']
    score0, formed0 = engine.score_current(0, 0, required,
                                           records=records0)
    check('grid yields zero pi_stacking', not pi0,
          'records=%d pi=%d' % (len(records0), len(pi0)))
    check('grid scores zero',
          score0 == 0.0 and formed0 == [],
          'score=%r formed=%r' % (score0, formed0))

    # The required aromatic slot (seed-agnostic: resn read FROM the slot;
    # works for HIS/PHE/TRP/TYR alike).
    req_slots = [s for s in mol_payload['grid']['slots']
                 if s.get('role') == 'required'
                 and 'pi_stacking' in (s.get('can_form') or ())]
    check('one required pi_stacking slot', len(req_slots) == 1,
          '%d slot(s); roles=%s'
          % (len(req_slots),
             sorted(set(s.get('role')
                        for s in mol_payload['grid']['slots']))))
    slot = req_slots[0]
    slot_id = slot['slot_id']
    resn = slot['aa']
    ring_walks = capability.AA_RESIDUES[resn]['rings']
    check('required slot aromatic',
          bool(ring_walks),
          'slot=%s aa=%s rings=%d' % (slot_id, resn, len(ring_walks)))
    aa_obj = registry['molecules'][0]['slots'][slot_id][0]

    # Ring centers + normals from the SAME feature layer detect() uses
    # (capability ring typing over extracted records + bonds, row-9
    # geometry: center = mean, unit normal of the p0/p2/p4 plane).
    molecule = registry['molecules'][0]
    lig_obj = molecule['ligand'][0]
    records_live = geometry.extract_game_atoms()
    bonds, index_to_id = geometry.ligand_bonds(lig_obj)
    _, lig_remap = _remap_ligand_bonds(records_live, bonds, index_to_id)
    features = extract_features(records_live, lig_remap)
    lig_ring = features['lig']['rings'][0]
    aa_ring = features['aa'][aa_obj]['rings'][0]
    n_l = _tofloat(lig_ring['normal'])
    n_a = _tofloat(aa_ring['normal'])
    d_n = _dot(n_a, n_l)
    line_cos = max(-1.0, min(1.0, d_n))
    target_n = n_l if d_n >= 0.0 else _scale(-1.0, n_l)
    line_angle = math.degrees(math.acos(abs(line_cos)))
    print('SMOKE-ENV placement aa=%s slot=%s line_angle=%.3f deg'
          % (resn, slot_id, line_angle), flush=True)

    # Baked normal alignment when the fragment's natural ring plane is
    # outside the parallel window (rotate the object about its ring
    # center so the normals coincide; pure translate keeps orientation
    # fixed, which cannot fix a tilted plane).
    if line_angle > PISTACK_ANGLE_TOL_DEG:
        M = _alignment_matrix(n_a, target_n, _tofloat(aa_ring['center']))
        placement.transform_baked(aa_obj, M)
        records_live = geometry.extract_game_atoms()
        features = extract_features(records_live, lig_remap)
        aa_ring = features['aa'][aa_obj]['rings'][0]
        lig_ring = features['lig']['rings'][0]
        n_a = _tofloat(aa_ring['normal'])
        d_n = _dot(n_a, n_l)
        new_angle = math.degrees(math.acos(abs(
            max(-1.0, min(1.0, d_n)))))
        check('ring alignment baked', new_angle <= 1e-3,
              'was %.3f -> %.6f deg' % (line_angle, new_angle))
    else:
        check('ring alignment already fine', True,
              'natural line_angle %.3f <= %.1f deg'
              % (line_angle, float(PISTACK_ANGLE_TOL_DEG)))

    # Place: ring center lands 4.5 A directly above the ligand ring
    # center (offset ~ 0 -> P-subtype construction).
    aa_center = _tofloat(aa_ring['center'])
    lig_center = _tofloat(lig_ring['center'])
    ring_target = _add(lig_center, _scale(4.5, n_l))
    delta = _sub(ring_target, aa_center)
    position = _add(_tofloat(geometry.centroid_of(aa_obj)), delta)
    engine.place_aa(slot_id, position)
    placed_center = None
    records_live = geometry.extract_game_atoms()
    features = extract_features(records_live, lig_remap)
    placed_center = _tofloat(features['aa'][aa_obj]['rings'][0]['center'])
    drift = max(abs(placed_center[i] - ring_target[i]) for i in range(3))
    check('placement ring at target', drift < 1e-4,
          'ring placed at (%.3f, %.3f, %.3f), target (%.3f, %.3f, %.3f),'
          ' drift=%.2g'
          % (placed_center + ring_target + (drift,)))

    records_a = engine.detect()
    pi_records = [r for r in records_a if r['type'] == 'pi_stacking']
    pi_here = [r for r in pi_records
               if r['aa']['object'] == aa_obj]
    check('detect finds the placement',
          len(pi_here) >= 1,
          'pi_stacking total=%d on placed object=%d'
          % (len(pi_records), len(pi_here)))
    if pi_here:
        rec = pi_here[0]
        m = rec['metrics']
        geom_ok = (4.0 < m['d_center'] < 5.5
                   and m['offset'] < 2.0
                   and m['angle_deg'] <= float(PISTACK_ANGLE_TOL_DEG)
                   and m['subtype'] == 'P')
        check('formed record geometry', geom_ok,
              'd=%.4f offset=%.4g angle=%.4f subtype=%s roles=%s/%s'
              % (m['d_center'], m['offset'], m['angle_deg'], m['subtype'],
                 rec['aa']['role'], rec['lig']['role']))

    score_a, formed_a = engine.score_current(0, 0, required,
                                             records=records_a)
    check('score after placement == 1.0',
          score_a == 1.0 and formed_a == ['pi_stacking'],
          'score=%r formed=%r' % (score_a, formed_a))
except Exception:
    traceback.print_exc()
    check('part A happy path', False, 'raised (see traceback above)')
    payload = registry = None

# ============================ PART B: ROTATION INVARIANCE ================
if payload is not None and records_a is not None:
    try:
        names = geometry.game_object_names()
        sel = ' or '.join(names)
        org = _tofloat(lig_ring['center'])
        # Note: lig_ring recorded pre-placement (the ligand did not
        # move during placement -- only the AA object moved).
        cmd.rotate('z', 37.0, sel, camera=0, origin=list(org))
        print('SMOKE-ENV rotated objects=%d axis=z angle=37.0 '
              'origin=(%.3f, %.3f, %.3f)' % ((len(names),) + org),
              flush=True)

        records_b = engine.detect()
        check('rotation preserves record set',
              [ _record_key(r) for r in records_b ]
              == [ _record_key(r) for r in records_a ],
              'before=%d after=%d records'
              % (len(records_a), len(records_b)))

        worst_d = 0.0
        worst_a = 0.0
        metric_fail = []
        for ra, rb in zip(records_a, records_b):
            if set(ra['metrics']) != set(rb['metrics']):
                metric_fail.append('metric keys: %s vs %s'
                                   % (set(ra['metrics']),
                                      set(rb['metrics'])))
                continue
            for key, va in ra['metrics'].items():
                vb = rb['metrics'][key]
                if isinstance(va, (int, float)) and \
                        isinstance(vb, (int, float)):
                    drift = abs(float(va) - float(vb))
                    if key.endswith('deg'):
                        worst_a = max(worst_a, drift)
                        if drift > METRIC_ANGLE_TOL:
                            metric_fail.append('%s %s %.3g'
                                               % (key, ra['type'], drift))
                    else:
                        worst_d = max(worst_d, drift)
                        if drift > METRIC_D_TOL:
                            metric_fail.append('%s %s %.3g'
                                               % (key, ra['type'], drift))
                elif va != vb:
                    metric_fail.append('%s: %r vs %r' % (key, va, vb))
        check('rotation metric drift in budget', not metric_fail,
              'worst dist=%.3g (<= %.0g) worst angle=%.3g deg '
              '(<= %.0g)%s'
              % (worst_d, METRIC_D_TOL, worst_a, METRIC_ANGLE_TOL,
                 ' BAD: ' + '; '.join(metric_fail) if metric_fail else ''))

        score_b, formed_b = engine.score_current(0, 0, required,
                                                 records=records_b)
        check('score survives rotation', score_b == 1.0,
              'score=%r formed=%r' % (score_b, formed_b))
    except Exception:
        traceback.print_exc()
        check('part B rotation', False, 'raised (see traceback above)')
else:
    check('part B rotation', False, 'skipped: part A did not complete')

# (Part C appended by Task 3.)

# --- Verdict marker (the SOLE verdict carrier) -------------------------------
print('=== SMOKE-04 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'), flush=True)
