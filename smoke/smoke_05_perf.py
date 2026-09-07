"""Headless smoke 05 - DETECT-05 perf budget + version-stamp gate (plan 02-15).

Run (from WSL, repo root):  bash smoke/run_smoke.sh smoke/smoke_05_perf.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-05 PASS ==='.

What it proves (ROADMAP Phase-2 criterion 5, [HEADLESS]; research SS8
perf budgets + SS9.9 audit complements; materialization research SS9):

1. TARGET SELECTION -- MANIFEST.json is parsed (read_json_file ->
   parse_manifest_dict -> enumerate_entries) and the perf target is the
   LARGEST bundled molecule via manifest.largest_entry (max
   heavy_atom_count, ties-first; never a special-cased field).
2. MAX-GRID GAME -- setup D=10 with the candidates restricted to that
   row: the LAST level (level_index 9) carries the tier-9 max grid
   (grid_n 9 -> 81 capped AAs + 1 ligand = 82 objects; materialization
   object growth asserted EXACTLY).
3. TIMED PIPELINE -- after a scripted pi_stacking placement (SMOKE-04
   recipe: baked ring-normal alignment, ring center 4.5 A above the
   ligand ring center), ONE timed pass measures the engine pipeline's
   two stages with stdlib time.time: EXTRACT = geometry.extract_game_
   atoms() + the ligand-bonds wall (engine._remap_ligand_bonds over the
   registry's ligand objects); DETECT = detector.detect over the full
   7-type surface. ASSERTED budgets (the REAL headless DETECT-05 gate --
   the WSL 2.0 s loose guard in tests/test_detector_invariance.py is
   WSL-only and is deliberately NOT imported): detect < 100 ms and
   extract + detect < 1000 ms. Count asserts everywhere: >= 1
   pi_stacking record formed; every stage's object count exact.
4. DETECTOR-VERSION STAMP -- payload['detector_version'] ==
   level_spec.DETECTOR_VERSION; a deep-copied payload re-stamped 'det-0'
   (stale) is REFUSED by parse_level_spec_dict over
   make_level_spec_container (exact-match gate: stale OR newer --
   FormatError naming 'stale or newer'); the pristine payload passes
   (positive control). Stale games can never replay silently.
5. TEARDOWN -- cleanup_game_objects leaves the scene EXACTLY at the
   pre-game snapshot.

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv first
/ cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch'); every print on ONE line and flushed; per-check
'SMOKE-05 <label> PASS|FAIL <detail>' lines; SMOKE-ENV lines for the
record; explicit space dicts in every iterate; no round() in
expressions.

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import copy
import math
import os
import sys
import time
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_05_perf.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []


def check(name, cond, detail=''):
    print('SMOKE-05 %-38s %s %s' % (name, 'PASS' if cond else 'FAIL', detail),
          flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

from aamatch.persistence import FormatError, read_json_file  # noqa: E402
from aamatch.manifest import (enumerate_entries, largest_entry,  # noqa: E402
                              parse_manifest_dict)
from aamatch.setup_state import validate_state  # noqa: E402
from aamatch.level_spec import (DETECTOR_VERSION,  # noqa: E402
                                make_level_spec_container,
                                parse_level_spec_dict)
from aamatch import capability, detector, engine, geometry, placement  # noqa: E402
from aamatch.detector import extract_features  # noqa: E402
from aamatch.thresholds import PISTACK_ANGLE_TOL_DEG  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

# The REAL headless DETECT-05 budgets (research SS8.4; PITFALLS 15) --
# intentionally local literals; the WSL-only 2.0 s loose guard from
# tests/test_detector_invariance.py must never leak into this gate.
DETECT_BUDGET_MS = 100.0
TOTAL_BUDGET_MS = 1000.0


# --- tiny vec helpers (smoke-local, SMOKE-04 proven) ----------------
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
    ring-plane alignment step (SMOKE-04 proven)."""
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
    t = [pivot[i] - sum(R[i][j] * pivot[j] for j in range(3))
         for i in range(3)]
    return [R[0][0], R[0][1], R[0][2], t[0],
            R[1][0], R[1][1], R[1][2], t[1],
            R[2][0], R[2][1], R[2][2], t[2],
            0.0, 0.0, 0.0, 1.0]


# --- 0. Scene snapshot + manifest-driven target selection -------------
pre_names = list(cmd.get_names('objects'))
biggest = None
try:
    check('clean pre-game scene',
          not [n0 for n0 in pre_names
               if n0.startswith(geometry.GAME_PREFIX)],
          'pre names: %s' % pre_names)
    container = read_json_file(os.path.join(
        _ROOT, 'aamatch', 'data', 'MANIFEST.json'))
    entries = enumerate_entries(parse_manifest_dict(container))
    biggest = largest_entry(entries)
    check('largest_entry selects the target',
          biggest is not None
          and biggest['entry_id'] == 'benzamide'
          and biggest['heavy_atom_count'] == max(
              row['heavy_atom_count'] for row in entries),
          'target=%s heavy=%d of %d entries'
          % (biggest['entry_id'], biggest['heavy_atom_count'],
             len(entries)))
except Exception:
    traceback.print_exc()
    check('manifest parse', False, 'raised (see traceback above)')

# ============== 1. MAX-GRID GAME (D=10, last tier = 9x9 grid) ===========
payload = None
registry = None
molecule = None
mol_payload = None
required = None
records_perf = None
try:
    setup = validate_state({'interaction_mode': 'block_exclusive',
                            'allowed_interactions': ['pi_stacking'],
                            'molecules_per_level': 1,
                            'difficulty_levels': 10})
    payload, rows = engine.new_game(setup, 7, candidates=[biggest])
    check('new_game scene untouched',
          list(cmd.get_names('objects')) == pre_names,
          'new_game loads temps only and deletes them')
    check('generate built all 10 levels',
          payload['seed'] == 7 and len(payload['levels']) == 10,
          'seed=%r levels=%d' % (payload['seed'],
                                 len(payload['levels'])))

    level_index = 9
    level = payload['levels'][level_index]
    n = level['difficulty']['grid_n']
    mol_payload = level['molecules'][0]
    required = mol_payload['required']
    check('last level is the max 9x9 grid',
          level['difficulty']['tier'] == 9 and n == 9
          and len(mol_payload['grid']['slots']) == 81,
          'tier=%d grid_n=%d slots=%d'
          % (level['difficulty']['tier'], n,
             len(mol_payload['grid']['slots'])))
    check('required mode block_exclusive',
          required == {'mode': 'list',
                       'items': [{'type': 'pi_stacking', 'count': 1}]},
          str(required))

    registry = engine.materialize(payload, level_index=level_index)
    post_names = list(cmd.get_names('objects'))
    grew = sorted(set(post_names) - set(pre_names))
    check('materialize object growth == 82',
          len(grew) == 82,
          'grew=%d want 82 (1 ligand + 81 slots)' % (len(grew),))
    molecule = registry['molecules'][0]

    # Scripted pi_stacking placement (SMOKE-04 recipe): find the required
    # aromatic slot seed-agnostically, extract ring centers/normals from
    # the SAME feature layer detect() consumes, bake a normal alignment
    # when needed, land the AA ring 4.5 A above the ligand ring center.
    req_slots = [s for s in mol_payload['grid']['slots']
                 if s.get('role') == 'required'
                 and 'pi_stacking' in (s.get('can_form') or ())]
    check('one required pi_stacking slot', len(req_slots) == 1,
          '%d slot(s)' % (len(req_slots),))
    slot = req_slots[0]
    slot_id = slot['slot_id']
    resn = slot['aa']
    check('required slot aromatic',
          bool(capability.AA_RESIDUES[resn]['rings']),
          'slot=%s aa=%s' % (slot_id, resn))
    aa_obj = molecule['slots'][slot_id][0]
    lig_obj = molecule['ligand'][0]

    records_live = geometry.extract_game_atoms()
    _, lig_bonds = engine._remap_ligand_bonds(records_live, [lig_obj])
    features = extract_features(records_live, lig_bonds)
    lig_ring = features['lig']['rings'][0]
    aa_ring = features['aa'][aa_obj]['rings'][0]
    n_l = _tofloat(lig_ring['normal'])
    n_a = _tofloat(aa_ring['normal'])
    d_n = _dot(n_a, n_l)
    target_n = n_l if d_n >= 0.0 else _scale(-1.0, n_l)
    line_angle = math.degrees(math.acos(abs(max(-1.0, min(1.0, d_n)))))
    print('SMOKE-ENV placement aa=%s slot=%s line_angle=%.3f deg'
          % (resn, slot_id, line_angle), flush=True)
    if line_angle > PISTACK_ANGLE_TOL_DEG:
        M = _alignment_matrix(n_a, target_n, _tofloat(aa_ring['center']))
        placement.transform_baked(aa_obj, M)
        records_live = geometry.extract_game_atoms()
        features = extract_features(records_live, lig_bonds)
        aa_ring = features['aa'][aa_obj]['rings'][0]
        d_n = _dot(_tofloat(aa_ring['normal']), n_l)
        new_angle = math.degrees(math.acos(abs(
            max(-1.0, min(1.0, d_n)))))
        check('ring alignment baked', new_angle <= 1e-3,
              'was %.3f -> %.6f deg' % (line_angle, new_angle))
    else:
        check('ring alignment already fine', True,
              'natural line_angle %.3f <= %.1f deg'
              % (line_angle, float(PISTACK_ANGLE_TOL_DEG)))

    aa_center = _tofloat(aa_ring['center'])
    lig_center = _tofloat(lig_ring['center'])
    ring_target = _add(lig_center, _scale(4.5, n_l))
    delta = _sub(ring_target, aa_center)
    engine.place_aa(slot_id, _add(_tofloat(geometry.centroid_of(aa_obj)),
                                  delta))
    records_live = geometry.extract_game_atoms()
    features = extract_features(records_live, lig_bonds)
    placed_center = _tofloat(features['aa'][aa_obj]['rings'][0]['center'])
    drift = max(abs(placed_center[i] - ring_target[i]) for i in range(3))
    check('placement ring at target', drift < 1e-4,
          'drift=%.2g at (%.3f, %.3f, %.3f)'
          % ((drift,) + placed_center))
except Exception:
    traceback.print_exc()
    check('max-grid game setup', False, 'raised (see traceback above)')
    payload = registry = None

# ======== 2. TIMED PIPELINE (extract wall, then detect wall) ============
if registry is not None:
    try:
        lig_objects = [mol['ligand'][0] for mol in registry['molecules']]
        t0 = time.time()
        records_perf = geometry.extract_game_atoms()
        _, lig_bonds_perf = engine._remap_ligand_bonds(records_perf,
                                                       lig_objects)
        t1 = time.time()
        det_records = detector.detect(records_perf, lig_bonds_perf)
        t2 = time.time()
        extract_ms = (t1 - t0) * 1000.0
        detect_ms = (t2 - t1) * 1000.0
        n_atoms = len(records_perf)
        check('extract stage counted',
              n_atoms > 0 and lig_bonds_perf,
              'atoms=%d ligand_bonds=%d extract=%.3f ms'
              % (n_atoms, len(lig_bonds_perf), extract_ms))
        pi_records = [r for r in det_records
                      if r['type'] == 'pi_stacking']
        pi_here = [r for r in pi_records
                   if r['aa']['object'] ==
                   molecule['slots'][req_slots[0]['slot_id']][0]]
        check('placement formed >= 1 pi_stacking', len(pi_here) >= 1,
              'records=%d pi=%d on placed=%d'
              % (len(det_records), len(pi_records), len(pi_here)))
        print('SMOKE-ENV perf extract_ms=%d detect_ms=%d atoms=%d'
              % (int(extract_ms + 0.5), int(detect_ms + 0.5), n_atoms),
              flush=True)
        check('detect inside 100 ms budget',
              detect_ms < DETECT_BUDGET_MS,
              'detect=%.3f ms (< %.0f ms)' % (detect_ms,
                                              DETECT_BUDGET_MS))
        check('extract+detect inside 1000 ms budget',
              extract_ms + detect_ms < TOTAL_BUDGET_MS,
              'extract=%.3f ms + detect=%.3f ms = %.3f ms (< %.0f ms)'
              % (extract_ms, detect_ms, extract_ms + detect_ms,
                 TOTAL_BUDGET_MS))
    except Exception:
        traceback.print_exc()
        check('timed pipeline', False, 'raised (see traceback above)')
        records_perf = None
else:
    check('timed pipeline', False, 'skipped: game setup did not complete')

# ============ 3. DETECTOR-VERSION STAMP (exact-match gate) ==============
if payload is not None:
    try:
        check('fresh payload carries the stamp',
              payload['detector_version'] == DETECTOR_VERSION,
              'stamped %r == DETECTOR_VERSION %r'
              % (payload['detector_version'], DETECTOR_VERSION))
        fresh = parse_level_spec_dict(make_level_spec_container(payload))
        check('fresh payload parses (positive control)',
              fresh is not None
              and fresh['detector_version'] == DETECTOR_VERSION,
              'parse returned level_index tiers %s'
              % [lvl['difficulty']['tier'] for lvl in fresh['levels']])
        stale = copy.deepcopy(payload)
        stale['detector_version'] = 'det-0'   # bumped DOWN by 1 = stale
        refused = False
        message = ''
        try:
            parse_level_spec_dict(make_level_spec_container(stale))
        except FormatError as exc:
            refused = True
            message = str(exc)
        check('stale-stamped spec refused',
              refused and 'det-0' in message
              and 'stale or newer' in message,
              'FormatError: %s' % message)
    except Exception:
        traceback.print_exc()
        check('stamp gate', False, 'raised (see traceback above)')
else:
    check('stamp gate', False, 'skipped: no payload to stamp')

# ============================ 4. TEARDOWN ===============================
if registry is not None:
    try:
        result = placement.cleanup_game_objects()
        post_names = list(cmd.get_names('objects'))
        check('cleanup count',
              result['deleted'] == 82,
              'deleted=%d want 82' % (result['deleted'],))
        check('teardown leaves scene pre-game',
              post_names == pre_names and not any(
                  n0.startswith(geometry.GAME_PREFIX)
                  for n0 in post_names),
              'post=%s' % post_names)
    except Exception:
        traceback.print_exc()
        check('teardown', False, 'raised (see traceback above)')
        placement.cleanup_game_objects()   # never leave game objects
else:
    check('teardown', False, 'skipped: game setup did not complete')

# --- Verdict marker (the SOLE verdict carrier) -------------------------------
print('=== SMOKE-05 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'), flush=True)
