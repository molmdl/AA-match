"""Headless smoke 21 - messy-scene cleanup field test (plan 08-08,
ROADMAP Phase-8 criterion 4 second clause: "on a ligand+ions+water
demo, Cleanup leaves exactly the original object set").

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_21_demo_cleanup.py 180
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-21 PASS ==='.

What it proves (PITFALL 13 in the field): on a NON-GAME messy user
scene (protein fragment + waters + Na+ ion), running a curated-set
game and then placement.cleanup_game_objects() restores the EXACT
original object set -- object NAMES and per-object ATOM COUNTS -- with
zero game-object ('_aam_' prefix) leakage and zero leftover 'AAM' segi
tags outside the game objects.

PART A: script-build the messy scene inline and write it to the
git-ignored tmp/messy_scene.pdb, then cmd.load it via to_windows_path
(01-04's probe-proven universal path). DEVIATION FROM THE RESEARCH
SKETCH (documented, 08-PLAN ratified): the research's
cmd.read_pdbstr sketch is replaced by a tmp-file cmd.load -- cmd.load
is the probe-proven universal path and read_pdbstr is an UNVERIFIED
surface in this build. The scene is local script-built atoms (no new
fetches of complex data); 1OXR (aspirin + Ca2+) is the approved
real-world analog cited in 08-PROPOSALS (D8).

PART B: parse the manifest via the pure chain, pick demo-easy-1's
first entry data-relative (the 1OXR-aspirin analog row), build a
single-molecule game (engine.new_game with candidates restricted to
that row, molecules_per_level == 1 per the 04-04 law) and materialize
it with placement.materialize. Assert every newly-created object is
'_aam_'-prefixed and at least one atom carries segi 'AAM'.

PART C: placement.cleanup_game_objects(); the scene must be EXACTLY
the pre-registered snapshot (03-05 law: pre-registered snapshot
asserts): name-set equality AND per-object atom-count equality
(PITFALL 13's own suggested proof); no '_aam_'-prefixed object may
remain and no atom anywhere may still carry segi 'AAM'.

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv
first / cwd fallback (never __file__); import aamatch directly
(module identity 'aamatch'); every print on ONE line and flushed;
explicit space dicts in every iterate; no round() in expressions;
every value computed into a variable BEFORE it appears in a check
detail string (never call cmd APIs inside an eager detail string,
03-04 authoring law).

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_21_demo_cleanup.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []


def check(name, cond, detail=''):
    print('SMOKE-21 %-38s %s %s' % (name, 'PASS' if cond else 'FAIL', detail),
          flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

from aamatch.persistence import read_json_file  # noqa: E402
from aamatch.manifest import parse_manifest_dict, enumerate_entries  # noqa: E402
from aamatch.setup_state import validate_state  # noqa: E402
from aamatch.paths import to_windows_path  # noqa: E402
from aamatch import engine, geometry, placement  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

GAME_PREFIX = geometry.GAME_PREFIX   # '_aam_'
SENTINEL_SEGI = placement.SENTINEL_SEGI   # 'AAM'
SEED = 20260808
MESSY_OBJECT = 'user_complex'
MESSY_PATH = os.path.join(_ROOT, 'tmp', 'messy_scene.pdb')


def _atom_line(record, serial, name, resn, chain, resi, x, y, z, elem):
    """Fixed-column PDB atom record (cols 1-6 record, 7-11 serial,
    13-16 name, 18-20 resn, 22 chain, 23-26 resseq, 31-54 xyz, 55-60
    occ, 61-66 b, 77-78 elem)."""
    return ('%-6s%5d %-4s %3s %c%4d    %8.3f%8.3f%8.3f'
            '%6.2f%6.2f          %2s'
            % (record, serial, name, resn, chain, resi,
               x, y, z, 1.00, 20.00, elem))


def _build_messy_pdb():
    """The messy user scene: a 5-residue protein fragment (backbone +
    CB), 3 HOH waters and 1 Na+ ion. Every atom's element is set so
    PyMOL types it on load."""
    lines = []
    serial = 0
    # Protein fragment (chain A): resn, resi, base offset
    fragment = (('ALA', 1, True), ('GLY', 2, False), ('LYS', 3, True),
                ('PHE', 4, True), ('SER', 5, True))
    for resn, resi, has_cb in fragment:
        base = 1.9 * (resi - 1)
        backbone = (('N', base + 0.0, 1.1, 0.0, 'N'),
                    ('CA', base + 1.2, 1.3, 0.4, 'C'),
                    ('C', base + 1.5, 0.1, 1.2, 'C'),
                    ('O', base + 1.3, -1.0, 0.8, 'O'))
        atoms = list(backbone)
        if has_cb:
            atoms.append(('CB', base + 1.8, 2.5, 1.2, 'C'))
        for name, x, y, z, elem in atoms:
            serial += 1
            lines.append(_atom_line('ATOM', serial, name, resn, 'A',
                                    resi, x, y, z, elem))
    # Waters (chain B)
    for i, resi in enumerate((101, 102, 103)):
        serial += 1
        lines.append(_atom_line('HETATM', serial, 'O', 'HOH', 'B',
                                resi, 6.0 + 3.0 * i, -4.0, 2.0, 'O'))
    # Na+ ion (chain C)
    serial += 1
    lines.append(_atom_line('HETATM', serial, 'NA', 'NA', 'C',
                            201, 12.0, 5.0, 8.0, 'NA'))
    lines.append('END')
    return '\n'.join(lines) + '\n', serial


def _segi_count(selection):
    """Number of atoms in `selection` carrying segi == 'AAM'."""
    segis = []
    cmd.iterate(selection, 'stored.append(segi)', space={'stored': segis})
    return sum(1 for segi in segis if segi == SENTINEL_SEGI)


# --- PART A: messy scene load + pre-game snapshot ---------------------
pre_ok = False
pre_names = []
pre_counts = {}
try:
    pdb_text, n_written = _build_messy_pdb()
    messy_dir = os.path.dirname(MESSY_PATH)
    if not os.path.isdir(messy_dir):
        os.makedirs(messy_dir)
    with open(MESSY_PATH, 'w') as fh:
        fh.write(pdb_text)
    check('a messy written', os.path.isfile(MESSY_PATH),
          '%s atoms=%d' % (os.path.basename(MESSY_PATH), n_written))

    cmd.load(to_windows_path(MESSY_PATH), MESSY_OBJECT)
    n_loaded = cmd.count_atoms(MESSY_OBJECT)
    check('a messy atom count', n_loaded == n_written,
          'loaded %d want %d' % (n_loaded, n_written))

    pre_names = list(cmd.get_names('objects'))
    pre_counts = {}
    for obj_name in pre_names:
        pre_counts[obj_name] = cmd.count_atoms(obj_name)
    prefixed = sorted(n for n in pre_names if n.startswith(GAME_PREFIX))
    check('a snapshot non-game scene',
          bool(pre_names) and not prefixed,
          'objects=%r prefixed=%r' % (pre_names, prefixed))
    pre_ok = True
except Exception:
    traceback.print_exc()
    check('a messy part', False, 'raised (see traceback above)')

# --- PARTS B + C: curated game on top, then full restoration ----------
game_ok = False
if pre_ok:
    try:
        payload = parse_manifest_dict(read_json_file(
            os.path.join(_ROOT, 'aamatch', 'data', 'MANIFEST.json')))
        demo_rows = [row for row in enumerate_entries(payload)
                     if row['set_id'] == 'demo-easy-1']
        row = demo_rows[0]   # data-relative: the 1OXR-aspirin analog row
        check('b candidate picked',
              row['set_id'] == 'demo-easy-1' and bool(row['entry_id']),
              '%s/%s' % (row['set_id'], row['entry_id']))

        setup = validate_state({
            'source_mode': 'demo',
            'demo_set_id': 'demo-easy-1',
            'molecules_per_level': 1,   # single-candidate law (04-04)
            'difficulty_levels': 1,
            'interaction_mode': 'unset',
        })
        game_payload, rows = engine.new_game(setup, SEED,
                                             candidates=[row])
        clean_names = list(cmd.get_names('objects'))
        check('b new_game scene untouched', clean_names == pre_names,
              'names=%r' % (clean_names,))

        registry = placement.materialize(game_payload, 0)
        mid_names = list(cmd.get_names('objects'))
        game_objs = sorted(n for n in mid_names if n not in pre_names)
        check('b game objects created', bool(game_objs),
              'new=%r' % (game_objs,))
        non_prefixed = sorted(
            n for n in game_objs if not n.startswith(GAME_PREFIX))
        check('b all game objects _aam_ prefix', not non_prefixed
              and len(game_objs) >= 2,
              'non_prefixed=%r total=%d' % (non_prefixed, len(game_objs)))
        aam_mid = _segi_count('all')
        check('b sentinel segi present', aam_mid >= 1,
              'segi AAM atoms=%d' % (aam_mid,))
        game_ok = True

        result = placement.cleanup_game_objects()
        n_deleted = result['deleted']
        check('c cleanup deleted game objects',
              n_deleted == len(game_objs),
              'deleted=%d want %d' % (n_deleted, len(game_objs)))

        post_names = list(cmd.get_names('objects'))
        check('c name set restored', post_names == pre_names,
              'post=%r pre=%r' % (post_names, pre_names))
        count_drifts = []
        for obj_name in pre_names:
            post_n = cmd.count_atoms(obj_name)
            if post_n != pre_counts[obj_name]:
                count_drifts.append(
                    '%s %d!=%d' % (obj_name, post_n, pre_counts[obj_name]))
        check('c per-object atom counts restored', not count_drifts,
              'drifts=%r' % (count_drifts,))
        leftover_prefix = sorted(
            n for n in post_names if n.startswith(GAME_PREFIX))
        check('c no _aam_ object remains', not leftover_prefix,
              'leftover=%r' % (leftover_prefix,))
        aam_post = _segi_count('all')
        check('c no AAM segi outside game objects', aam_post == 0,
              'segi AAM atoms=%d' % (aam_post,))
    except Exception:
        traceback.print_exc()
        check('c cleanup part', False, 'raised (see traceback above)')
        placement.cleanup_game_objects()   # never leave game objects
else:
    check('b/c skipped', False, 'part A did not complete')

# --- Verdict marker (the SOLE verdict carrier) ------------------------
print('=== SMOKE-21 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'), flush=True)
