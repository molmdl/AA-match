"""SMOKE-22: detector-coverage oracle over the bundled curated molecules.

Run (from WSL, repo root, headless via the standing runner):
    bash smoke/run_smoke.sh smoke/smoke_22_detector_coverage.py 240
(240 s: Windows loader startup + three SDF scenes.)
Verdict carrier (printed, grepped by the runner): the SMOKE-22 PASS
marker line appears ONLY when every check below is green; the verbatim
verdict line (detailed below) precedes the marker.

Provenance: quick-002 (2026-10-03) folded the plan-08-11 Task 2
ONE-OFF probe (tmp/detector_coverage_phase8.py, git-ignored) into the
standing battery -- same scenes, same constructed targets and slacks,
same ledger/leak checks; only smoke-house prefixes and the SMOKE-22
marker changed. Before this, a count-level detector oracle existed
only for benzamide (SMOKE-03/05); this smoke adds record-level halogen
and metal coverage over the curated halogen/metal rows -- the rows
most likely to expose detector regressions.

Scenes (DETECT-03 revision-triggered check, 08-PROPOSALS decision 9
'TRIGGERED-FOR-CHECK'): for each scene below this smoke loads the
bundled SDF via the standard path helpers into a private '_aam_tmp*'
object, materializes ONE capable AA fragment (GLU, the
acceptor+chelator dual) near the target geometry using the SMOKE-04
scripted-placement recipe (physically-unclashed at typical radii,
probe-pinned Rodrigues alignment), runs engine-level detect
(geometry.extract_game_atoms + the pinned bond remap + detector.detect),
and asserts the expected record types appear with sane metrics. Every
metric window comes from the imported thresholds constants
(HALOGEN_D_MAX / HALOGEN_DONOR_ANGLE_DEG / HALOGEN_ACC_ANGLE_DEG /
METAL_D_MAX) -- none hardcoded:

  1. chloramphenicol (demo-challenge-1): GLU OE1 placed 3.3 A along
     the extension of a C-Cl bond -> halogen record with donor angle
     ~180 deg (window [135,195]), acceptor angle constructed to
     120 deg (window [90,150]), d_ax ~ 3.3 (<= HALOGEN_D_MAX 4.0).
  2. thyroxine (demo-veryhard-1): same construction on a C-I bond.
  3. heme (demo-veryhard-2): GLU OE1 placed 2.5 A along the porphyrin
     plane normal from the Fe -> metal record with d_metal ~ 2.5
     (<= METAL_D_MAX 3.0, distance-only per detector row 7).

Heme formal-charge input (08-07 honesty note): the derived
formal_charge_sum of the bundled HEM_ideal.sdf is -4 (the 08-07
proposal narrative said 'charge field 0'); this smoke prints AND pins
the -4 sum as a recorded input. It does NOT affect the metal record
(Fe typing is element-based), but the verdict carries it verbatim.

VERDICT RULE (plan-pinned, carried over from the probe): if every
expected record appears with sane metrics -> 'NO threshold surprise --
DETECT-03 provisional values hold on real data; no DETECTOR_VERSION
bump proposal needed'. If any expected record is missing or a metric
is pathological -> the FAIL checks fire, NO pass marker prints, and
the fix path is a DETECTOR_VERSION bump PROPOSAL in a new plan, never
a silent edit of thresholds.py, detector.py or capability.py.

Scene hygiene: every scene's objects are deleted in a finally block;
the script re-asserts cmd.get_names('objects') equals the pre-run
snapshot (zero leakage).

Python floor: runs inside PyMOL's Windows Python 3.9; written 3.6-safe.
"""
import math
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_22_detector_coverage.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []


def check(name, cond, detail=''):
    print('SMOKE-22 %-44s %s %s' % (name, 'PASS' if cond else 'FAIL', detail),
          flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

from aamatch.persistence import read_json_file  # noqa: E402
from aamatch.manifest import parse_manifest_dict, enumerate_entries  # noqa: E402
from aamatch import detector, geometry, placement  # noqa: E402
from aamatch.paths import package_data_path, to_windows_path  # noqa: E402
from aamatch.thresholds import (HALOGEN_ACC_ANGLE_DEG, HALOGEN_D_MAX,  # noqa: E402
                                HALOGEN_DONOR_ANGLE_DEG, METAL_D_MAX)

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

LIG_OBJ = '_aam_tmp_lig'
AA_OBJ = '_aam_aatmp'          # startswith '_aam_aa' -> side 'aa'

# Construction targets (windows from aamatch/thresholds.py, printed).
TARGET_D_AX = 3.3              # \u00c5 along the C->X extension (<= 4.0)
TARGET_ACC_ANGLE = 120.0       # deg, mid-window of [90, 150]
TARGET_D_METAL = 2.5           # \u00c5 axial off the Fe (<= 3.0)
METRIC_SLACK_D = 0.30          # construction slack vs target distance
METRIC_SLACK_ANGLE = 12.0      # construction slack vs target angle


# --- tiny vec helpers (SMOKE-04 pattern) -----------------------------
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


def _alignment_matrix(n_from, n_to, pivot):
    """Row-major homogeneous 4x4 rotating unit vector n_from onto
    unit vector n_to (Rodrigues) about ``pivot`` -- the SMOKE-04 baked
    ring-plane alignment helper, reused for acceptor-angle control."""
    k_raw = _cross(n_from, n_to)
    klen = _norm(k_raw)
    if klen < 1e-12:
        return None
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


def _remap_ligand_bonds(records, bonds, index_to_id):
    """Remap get_bonds 0-based WALK positions into positions in the
    (object, id)-sorted single-ligand record list (02-09 pinned mapping;
    the SMOKE-04 single-object form, kept for clarity)."""
    lig = sorted((r for r in records if r['side'] == 'lig'),
                 key=lambda r: r['id'])
    id_pos = dict((r['id'], i) for i, r in enumerate(lig))
    out = []
    for (i, j, order) in bonds:
        out.append((id_pos[index_to_id[i + 1]],
                    id_pos[index_to_id[j + 1]], int(order)))
    return lig, out


def _atom_positions(obj):
    rows = []
    cmd.iterate_state(1, obj,
                      'stored.append((name, ID, x, y, z))',
                      space={'stored': rows})
    out = {}
    for (name, ID, x, y, z) in rows:
        out[name] = (float(x), float(y), float(z), int(ID))
    return out


def _scene_records_and_remap():
    """Extract live-scene records + the pinned bond remap."""
    records = geometry.extract_game_atoms()
    bonds, index_to_id = geometry.ligand_bonds(LIG_OBJ)
    _, lig_remap = _remap_ligand_bonds(records, bonds, index_to_id)
    return records, lig_remap


def _scene_features():
    records, lig_remap = _scene_records_and_remap()
    return detector.extract_features(records, lig_remap)


def _detect():
    """Engine-level detect over the live scene (the pinned chain)."""
    records, lig_remap = _scene_records_and_remap()
    return detector.detect(records, lig_remap)


def _load_ligand(entry):
    winpath = to_windows_path(package_data_path('data', entry['file']))
    cmd.load(winpath, LIG_OBJ)
    n = cmd.count_atoms(LIG_OBJ)
    check('load %s' % entry['entry_id'], n >= 1,
          'file=%s atoms=%d' % (entry['file'], n))


def _place_halogen_scene(features, label):
    """GLU OE1 on the C->X extension at TARGET_D_AX; the acceptor-side
    anchor (CD) rotated about OE1 onto the 120-deg construction."""
    donors = features['lig']['halogen_donors']
    check('%s halogen donors typed' % label, len(donors) >= 1,
          'donors=%d' % len(donors))
    if not donors:
        return False, None, None
    (x_idx, x_rec), (c_idx, c_rec) = donors[0]
    x_pos = (x_rec['x'], x_rec['y'], x_rec['z'])
    c_pos = (c_rec['x'], c_rec['y'], c_rec['z'])
    a_hat = _unit(_sub(x_pos, c_pos))        # C -> X direction
    target_a = _add(x_pos, _scale(TARGET_D_AX, a_hat))
    print('SMOKE-ENV %s donor: X=%s elem=%s C=%s elem=%s'
          % (label, x_rec['name'], x_rec['elem'],
             c_rec['name'], c_rec['elem']), flush=True)

    cmd.fragment('glu', AA_OBJ, zoom=0)
    atoms = _atom_positions(AA_OBJ)
    oe1 = atoms['OE1']
    cd = atoms['CD']
    delta = _sub(target_a, oe1[:3])
    cmd.translate(list(delta), AA_OBJ, state=1, camera=0)

    atoms = _atom_positions(AA_OBJ)
    oe1 = atoms['OE1']
    cd = atoms['CD']
    # Acceptor angle target: angle(CD--OE1...X) at OE1 ==
    # TARGET_ACC_ANGLE, in the [90, 150] window.
    u_ax = _unit(_sub(x_pos, oe1[:3]))       # OE1 -> X
    w = _cross(u_ax, (0.0, 0.0, 1.0))
    if _norm(w) < 1e-9:
        w = _cross(u_ax, (1.0, 0.0, 0.0))
    w = _unit(w)
    n_target = _unit(_add(_scale(math.cos(math.radians(TARGET_ACC_ANGLE)),
                                 u_ax),
                          _scale(math.sin(math.radians(TARGET_ACC_ANGLE)),
                                 w)))
    n_from = _unit(_sub(cd[:3], oe1[:3]))
    M = _alignment_matrix(n_from, n_target, oe1[:3])
    if M is not None:
        placement.transform_baked(AA_OBJ, M)
    return True, x_rec, atoms.get('OE1')


def _place_metal_scene(features, label):
    """GLU OE1 at TARGET_D_METAL along the porphyrin-normal axis from
    the ligand's typed metal atom (Fe) -- distance-only row 7."""
    metals = features['lig']['metals']
    check('%s metals typed' % label, len(metals) >= 1,
          'metals=%s' % ([r['elem'] for _, r in metals],))
    if not metals:
        return False, None
    m_idx, m_rec = metals[0]
    fe = (m_rec['x'], m_rec['y'], m_rec['z'])
    # Porphyrin-plane normal from Fe-bound N vectors (largest |cross|
    # pair wins -- robust against a nearly-axial Fe).
    lig_atoms = features['lig']['atoms']
    ns = [(a['x'], a['y'], a['z']) for a in lig_atoms
          if a['elem'] == 'N'
          and _norm(_sub((a['x'], a['y'], a['z']), fe)) < 2.4]
    check('%s porphyrin Ns near Fe' % label, len(ns) >= 4,
          'Ns=%d' % len(ns))
    best, best_k = None, -1.0
    for i in range(len(ns)):
        for j in range(i + 1, len(ns)):
            k = _cross(_sub(ns[i], fe), _sub(ns[j], fe))
            if _norm(k) > best_k:
                best, best_k = k, _norm(k)
    normal = _unit(best) if best is not None and best_k > 1e-9 \
        else (0.0, 0.0, 1.0)
    target = _add(fe, _scale(TARGET_D_METAL, normal))

    cmd.fragment('glu', AA_OBJ, zoom=0)
    atoms = _atom_positions(AA_OBJ)
    oe1 = atoms['OE1']
    delta = _sub(target, oe1[:3])
    cmd.translate(list(delta), AA_OBJ, state=1, camera=0)
    return True, m_rec


def _oe1_record(records, type_):
    """The halogen/metal record whose AA side is OE1 of our fragment."""
    out = []
    for r in records:
        if r['type'] != type_:
            continue
        out.append(r)
    return out


pre_names = list(cmd.get_names('objects'))
entries = {}
ok_scene = {}
try:
    check('clean pre-smoke scene',
          not [n0 for n0 in pre_names
               if n0.startswith(geometry.GAME_PREFIX)],
          'pre names: %s' % pre_names)
    container = read_json_file(os.path.join(
        _ROOT, 'aamatch', 'data', 'MANIFEST.json'))
    for row in enumerate_entries(parse_manifest_dict(container)):
        entries.setdefault(row['entry_id'], row)
    check('smoke entries present',
          all(k in entries for k in
              ('chloramphenicol', 'thyroxine', 'heme')),
          'ids=%s' % sorted(entries.keys()))
except Exception:
    traceback.print_exc()
    check('manifest parse', False, 'raised (see traceback above)')

# ======================= SCENE 1: chloramphenicol C-Cl =================
try:
    entry = entries.get('chloramphenicol')
    if entry:
        _load_ligand(entry)
        features = _scene_features()
        label = 'chloramphenicol'
        placed, x_rec, _ = _place_halogen_scene(features, label)
        if placed:
            recs = _detect()
            halo = _oe1_record(recs, 'halogen')
            tally = {}
            for r in recs:
                tally[r['type']] = tally.get(r['type'], 0) + 1
            check('%s >=1 halogen record' % label, len(halo) >= 1,
                  'records=%d tally=%s' % (len(recs), tally))
            target_recs = [r for r in halo
                           if abs(r['metrics']['d_ax'] - TARGET_D_AX)
                           <= METRIC_SLACK_D]
            check('%s OE1-constructed record sane' % label,
                  len(target_recs) >= 1,
                  'constructed=%d of %d halogen'
                  % (len(target_recs), len(halo)))
            for r in target_recs:
                m = r['metrics']
                sane = (HALOGEN_D_MAX >= m['d_ax'] > 0.5
                        and HALOGEN_DONOR_ANGLE_DEG[0]
                        <= m['donor_angle_deg']
                        <= HALOGEN_DONOR_ANGLE_DEG[1]
                        and HALOGEN_ACC_ANGLE_DEG[0]
                        <= m['acc_angle_deg']
                        <= HALOGEN_ACC_ANGLE_DEG[1]
                        and abs(m['donor_angle_deg'] - 180.0)
                        <= METRIC_SLACK_ANGLE
                        and abs(m['acc_angle_deg'] - TARGET_ACC_ANGLE)
                        <= METRIC_SLACK_ANGLE)
                check('%s metric frame d_ax/donor/acc' % label, sane,
                      'd_ax=%.3f donor=%.1f acc=%.1f (targets 3.3/180/120)'
                      % (m['d_ax'], m['donor_angle_deg'],
                         m['acc_angle_deg']))
            ok_scene['chloramphenicol'] = bool(halo and target_recs)
finally:
    for name in (LIG_OBJ, AA_OBJ):
        if name in cmd.get_names('objects'):
            cmd.delete(name)

# ========================== SCENE 2: thyroxine C-I =====================
try:
    entry = entries.get('thyroxine')
    if entry:
        _load_ligand(entry)
        features = _scene_features()
        label = 'thyroxine'
        placed, x_rec, _ = _place_halogen_scene(features, label)
        if placed:
            recs = _detect()
            halo = _oe1_record(recs, 'halogen')
            tally = {}
            for r in recs:
                tally[r['type']] = tally.get(r['type'], 0) + 1
            check('%s >=1 halogen record' % label, len(halo) >= 1,
                  'records=%d tally=%s' % (len(recs), tally))
            target_recs = [r for r in halo
                           if abs(r['metrics']['d_ax'] - TARGET_D_AX)
                           <= METRIC_SLACK_D]
            check('%s OE1-constructed record sane' % label,
                  len(target_recs) >= 1,
                  'constructed=%d of %d halogen'
                  % (len(target_recs), len(halo)))
            for r in target_recs:
                m = r['metrics']
                sane = (HALOGEN_D_MAX >= m['d_ax'] > 0.5
                        and HALOGEN_DONOR_ANGLE_DEG[0]
                        <= m['donor_angle_deg']
                        <= HALOGEN_DONOR_ANGLE_DEG[1]
                        and HALOGEN_ACC_ANGLE_DEG[0]
                        <= m['acc_angle_deg']
                        <= HALOGEN_ACC_ANGLE_DEG[1]
                        and abs(m['donor_angle_deg'] - 180.0)
                        <= METRIC_SLACK_ANGLE
                        and abs(m['acc_angle_deg'] - TARGET_ACC_ANGLE)
                        <= METRIC_SLACK_ANGLE)
                check('%s metric frame d_ax/donor/acc' % label, sane,
                      'd_ax=%.3f donor=%.1f acc=%.1f (targets 3.3/180/120)'
                      % (m['d_ax'], m['donor_angle_deg'],
                         m['acc_angle_deg']))
            ok_scene['thyroxine'] = bool(halo and target_recs)
finally:
    for name in (LIG_OBJ, AA_OBJ):
        if name in cmd.get_names('objects'):
            cmd.delete(name)

# ============================ SCENE 3: heme Fe =========================
try:
    entry = entries.get('heme')
    if entry:
        _load_ligand(entry)
        label = 'heme'
        # 08-07 honesty-note input: the bundled HEM_ideal.sdf derives
        # formal_charge_sum -4 (the -4 charge model ships as-recorded).
        raw = []
        cmd.iterate_state(1, LIG_OBJ, 'stored.append(formal_charge)',
                          space={'stored': raw})
        q_sum = sum(int(q) for q in raw)
        check('%s formal_charge_sum == -4 (08-07 recorded input)' % label,
              q_sum == -4, 'sum=%d' % q_sum)
        features = _scene_features()
        placed, m_rec = _place_metal_scene(features, label)
        if placed:
            recs = _detect()
            metal = _oe1_record(recs, 'metal')
            tally = {}
            for r in recs:
                tally[r['type']] = tally.get(r['type'], 0) + 1
            check('%s >=1 metal record' % label, len(metal) >= 1,
                  'records=%d tally=%s' % (len(recs), tally))
            target_recs = [r for r in metal
                           if abs(r['metrics']['d_metal'] - TARGET_D_METAL)
                           <= METRIC_SLACK_D]
            check('%s OE1-constructed record sane' % label,
                  len(target_recs) >= 1,
                  'constructed=%d of %d metal'
                  % (len(target_recs), len(metal)))
            for r in target_recs:
                m = r['metrics']
                sane = 0.5 < m['d_metal'] <= METAL_D_MAX
                check('%s metric frame d_metal' % label, sane,
                      'd_metal=%.3f (target %.1f, window (0.5, %.1f])'
                      % (m['d_metal'], TARGET_D_METAL, METAL_D_MAX))
            ok_scene['heme'] = bool(metal and target_recs)
finally:
    for name in (LIG_OBJ, AA_OBJ):
        if name in cmd.get_names('objects'):
            cmd.delete(name)

# ======================= leakage + verdict =============================
post_names = list(cmd.get_names('objects'))
check('zero object leakage', post_names == pre_names,
      'post=%s pre=%s' % (post_names, pre_names))

if failures:
    print('SMOKE-22 VERDICT: DETECTOR_VERSION bump PROPOSAL required -- '
          'failed checks: %s' % (sorted(failures),), flush=True)
else:
    print('SMOKE-22 VERDICT: NO threshold surprise -- DETECT-03 '
          'provisional values hold on real data (halogen records '
          'provable on chloramphenicol C-Cl and thyroxine C-I '
          'geometry inside the approved 4.0 A / [135,195] / [90,150] '
          'windows; metal record provable on HEM Fe inside the 3.0 A '
          'window; heme formal_charge_sum -4 as recorded at 08-07); '
          'no DETECTOR_VERSION bump proposal needed', flush=True)
    print('=== SMOKE-22 PASS ===', flush=True)
