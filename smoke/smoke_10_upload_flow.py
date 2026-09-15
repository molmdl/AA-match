"""Headless smoke 10 - uploaded-flow ligand_content plumbing (plan 04-04).

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_10_upload_flow.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-10 PASS ==='.

Proves the 04-04 additive ``ligand_content=None`` pipe end-to-end in
REAL headless PyMOL (cmd tier only, NO QApplication; T1a tier):

PART 1  synthetic uploaded flow. A manifest-shaped row built by COPYING
        the bundled benzamide row and rewriting it to synthetic keys
        (set_id 'uploaded', entry_id 'mol-001', file
        'uploads/mol-001.sdf', sha256 = hashlib.sha256 of the DECODED
        RECORD TEXT -- the 04-DECISIONS #19 record-text hash) flows
        through engine.new_game (seed 12345, candidates=[row],
        ligand_content={'uploads/mol-001.sdf': <benzamide.sdf text>}):
        the temp-load extraction reads the STRING via cmd.read_sdfstr
        (the same C parser as file loads, NEVER a package path), the
        payload's level-0 ligand block names the synthetic file, then
        engine.materialize(payload, 0, ligand_content=...) recreates
        the ligand from the SAME embedded text (atom count == the
        row's atom_count, every atom sentinel-tagged segi 'AAM'). The
        FULL one-call seam then runs: gamestart.start_game(setup,
        seed=777, candidates=[row], ligand_content=...) returns the
        LIVE GameWizard carrying the uploaded payload/registry; Done
        (canonical cmd.set_wizard()) + cleanup restore the baseline
        scene EXACTLY.
PART 2  negative control. The SAME synthetic row WITHOUT ligand_content
        makes engine.new_game fail CLOSED with EngineError: the
        synthetic key resolves into the package data dir, the load
        fails (THIS build file-reads sdf text first --
        internal.py:359-360's _load2str path -- so a missing fixture
        raises pymol.CmdException from file_read), and the engine's
        package-load wrapper converts the load failure into an
        EngineError naming the ligand (04-04 deviation: the must-have
        demands a clear EngineError, and gamestart's guard contract
        maps the ValueError family only). Never a silent wrong
        molecule; the scene is byte-unchanged afterwards.
PART 3  regression. Bare gamestart.start_game() (no args -- the
        bundled-manifest seed-42 path every pre-04-04 caller uses)
        still starts, and Done + cleanup restore the baseline.

FOUR SKETCH RECONCILIATIONS (recorded; the two code deviations also
live in 04-04-SUMMARY.md):

1. Plan Task 3's setup snippet is used except for
   ``molecules_per_level=1``: ONE synthetic candidate row cannot fill
   the generator's two-DISTINCT-molecules-per-level DEFAULTS contract
   (GenerationError "has 1 distinct candidate(s)"), so a
   single-candidate game must declare one molecule per level --
   SMOKE-04's own setup does exactly this for the same reason.
2. The plan text says the level-0 ligand block "reads source
   'uploaded'"; ligand['source'] is generator.py:854's verbatim echo
   of setup source_mode ('demo' here -- 'uploaded' is not a legal
   source_mode value). The smoke pins what the generation contract
   actually carries: set_id 'uploaded' + the synthetic file key, with
   the source echo PRINTED for the record.
3. cmd.load of a MISSING package fixture raises CmdException on this
   build (it file-reads sdf first; the plan sketched a silent 0-atom
   temp), so engine._ligand_data_for wraps the package-load failure
   into EngineError naming the ligand.
4. THIS 2.5.0 build defines read_mol2str in importing.py:1038 but
   NEVER exports it in api.py -- hasattr(cmd, 'read_mol2str') is
   False. The mol2 branches fail closed with the house error naming
   the missing reader; the availability probe below is RECORD-ONLY.

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv
first / cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch'); every print on ONE line and flushed; explicit
space dicts in every iterate; no round() in expressions; no cmd API
that may throw inside an eager check-detail string (the 03-04 rule).

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import hashlib
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_10_upload_flow.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []


def check(name, cond, detail=''):
    print('SMOKE-10 %-44s %s %s' % (name, 'PASS' if cond else 'FAIL',
                                     detail), flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

from aamatch.persistence import read_json_file  # noqa: E402
from aamatch.manifest import parse_manifest_dict, enumerate_entries  # noqa: E402
from aamatch import engine, gamestart, placement, setup_state  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

# --- 0. Capability guards + scene snapshot + synthetic uploaded row ----
check('cmd.read_sdfstr available', hasattr(cmd, 'read_sdfstr'),
      '(research open-questions probe-2 one-liner guard)')
print('SMOKE-ENV cmd.read_mol2str available: %s (RECORD-ONLY -- this '
      '2.5.0 build omits the api.py export; the mol2 branches fail '
      'closed, reconciliation 4)' % (hasattr(cmd, 'read_mol2str'),),
      flush=True)

pre_names = list(cmd.get_names('objects'))
check('clean pre-game scene',
      not [n0 for n0 in pre_names
           if n0.startswith('_aam_')],
      'pre names: %s' % pre_names)

row = None
text = None
ligand_content = None
try:
    raw = None
    with open(os.path.join(_ROOT, 'aamatch', 'data', 'ligands',
                           'benzamide.sdf'), 'rb') as fh:
        raw = fh.read()
    text = raw.decode('utf-8')
    container = read_json_file(os.path.join(_ROOT, 'aamatch', 'data',
                                            'MANIFEST.json'))
    entries = enumerate_entries(parse_manifest_dict(container))
    benz = [r for r in entries if r['entry_id'] == 'benzamide'][0]
    row = dict(benz)
    row['set_id'] = 'uploaded'
    row['entry_id'] = 'mol-001'
    row['file'] = 'uploads/mol-001.sdf'
    row['sha256'] = hashlib.sha256(text.encode('utf-8')).hexdigest()
    ligand_content = {'uploads/mol-001.sdf': text}
    check('synthetic uploaded row built', True,
          'atom_count=%s file=%s sha256=%s...'
          % (row.get('atom_count'), row['file'], row['sha256'][:12]))
except Exception:
    traceback.print_exc()
    check('synthetic uploaded row built', False,
          'raised (see traceback above)')

upload_setup = setup_state.validate_state(
    dict(setup_state.DEFAULTS, demo_set_id='uploaded',
         molecules_per_level=1))

# ============================ PART 1: UPLOADED FLOW =====================
# --- 1a. new_game with ligand_content ----------------------------------
payload = None
registry = None
lig_obj = None
try:
    payload, rows_out = engine.new_game(
        upload_setup, 12345, candidates=[row],
        ligand_content=ligand_content)
    check('new_game uploaded leaves scene untouched',
          list(cmd.get_names('objects')) == pre_names,
          'temp extraction loads from text, deleted in finally')
    check('payload seed carried', payload['seed'] == 12345,
          'seed=%s' % payload['seed'])
    lig = payload['levels'][0]['molecules'][0]['ligand']
    check('ligand block names synthetic key',
          lig['set_id'] == 'uploaded'
          and lig['file'] == 'uploads/mol-001.sdf',
          'source=%s set_id=%s file=%s'
          % (lig.get('source'), lig['set_id'], lig['file']))
except Exception:
    traceback.print_exc()
    check('new_game uploaded flow', False,
          'raised (see traceback above)')
    payload = None

# --- 1b. materialize from embedded text --------------------------------
if payload is not None:
    try:
        registry = engine.materialize(payload, 0,
                                      ligand_content=ligand_content)
        mol0 = registry['molecules'][0]
        lig_obj = mol0['ligand'][0]
        names_now = list(cmd.get_names('objects'))
        check('materialized ligand object exists',
              lig_obj in names_now,
              'ligand=%s grew=%d'
              % (lig_obj, len(set(names_now) - set(pre_names))))
        n_atoms = cmd.count_atoms(lig_obj)
        check('ligand atom count matches row',
              n_atoms == int(row['atom_count']),
              'loaded=%d row=%d' % (n_atoms, int(row['atom_count'])))
        segis = set()
        cmd.iterate(lig_obj, 'stored.add(segi)',
                    space={'stored': segis})
        check('ligand sentinel segi AAM on every atom',
              segis == set([placement.SENTINEL_SEGI]),
              'segis=%s' % sorted(segis))
    except Exception:
        traceback.print_exc()
        check('materialize uploaded flow', False,
              'raised (see traceback above)')
        registry = None
else:
    check('materialize uploaded flow', False,
          'skipped: 1a did not complete')

# --- 1c. FULL one-call seam on a clean scene ---------------------------
try:
    placement.cleanup_game_objects()
    check('back to baseline before full start',
          list(cmd.get_names('objects')) == pre_names,
          'bare materialize generation cleaned')
    wiz = gamestart.start_game(setup=upload_setup, seed=777,
                               candidates=[row],
                               ligand_content=ligand_content)
    check('start_game returns the live wizard',
          cmd.get_wizard() is wiz,
          'SMOKE-08 return-value pattern')
    wp = wiz._payload
    wr = wiz._registry
    lig2 = wp['levels'][0]['molecules'][0]['ligand']
    check('wizard carries uploaded payload+registry',
          wp['seed'] == 777
          and lig2['set_id'] == 'uploaded'
          and lig2['file'] == 'uploads/mol-001.sdf'
          and wr['molecules'][0]['ligand'][0]
          in list(cmd.get_names('objects')),
          'seed=%s set_id=%s file=%s ligand=%s'
          % (wp['seed'], lig2['set_id'], lig2['file'],
             wr['molecules'][0]['ligand'][0]))
    n_grid = wp['levels'][0]['difficulty']['grid_n']
    grew = sorted(set(cmd.get_names('objects')) - set(pre_names))
    n_expected = len(wr['molecules']) * (1 + n_grid * n_grid)
    check('start growth derived and exact',
          len(grew) == n_expected,
          'grew=%d want %d (%d molecule(s) x (1 + %d*%d))'
          % (len(grew), n_expected, len(wr['molecules']),
             n_grid, n_grid))
    cmd.set_wizard()        # canonical Done
    check('Done returns empty stack', cmd.get_wizard() is None, '')
    placement.cleanup_game_objects()
    check('full-start teardown restores baseline',
          list(cmd.get_names('objects')) == pre_names,
          'post names: %s' % list(cmd.get_names('objects')))
except Exception:
    traceback.print_exc()
    check('full start uploaded flow', False,
          'raised (see traceback above)')
    if cmd.get_wizard() is not None:
        cmd.set_wizard()
    placement.cleanup_game_objects()   # never leave game objects

# ============================ PART 2: NEGATIVE CONTROL ==================
neg = None
try:
    engine.new_game(upload_setup, 99, candidates=[row])
except engine.EngineError as exc:
    neg = exc
except Exception as exc:                # unexpected error class
    traceback.print_exc()
    neg = exc
check('missing content fails closed EngineError',
      isinstance(neg, engine.EngineError),
      'raised: %s: %s'
      % (type(neg).__name__ if neg is not None else '<none raised>',
         str(neg)[:90] if neg is not None else ''))
check('scene unchanged after refusal',
      list(cmd.get_names('objects')) == pre_names,
      'post-refusal names: %s' % list(cmd.get_names('objects')))

# ============================ PART 3: REGRESSION ========================
try:
    wiz3 = gamestart.start_game()
    check('bundled bare start_game works',
          cmd.get_wizard() is wiz3 and wiz3._payload['seed'] == 42,
          'seed=%s molecules=%d (pre-04-04 default callers untouched)'
          % (wiz3._payload['seed'], len(wiz3._registry['molecules'])))
    cmd.set_wizard()
    placement.cleanup_game_objects()
    check('bundled teardown restores baseline',
          list(cmd.get_names('objects')) == pre_names,
          'post names: %s' % list(cmd.get_names('objects')))
except Exception:
    traceback.print_exc()
    check('bundled bare start_game works', False,
          'raised (see traceback above)')
    if cmd.get_wizard() is not None:
        cmd.set_wizard()
    placement.cleanup_game_objects()   # never leave game objects

# --- Verdict marker (the SOLE verdict carrier) -------------------------
print('=== SMOKE-10 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
