"""Headless smoke 25 - Phase-9 performance-budget battery (plan 09-02).

Run (from WSL, repo root):  bash smoke/run_smoke.sh smoke/smoke_25_perf_budgets.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-25 PASS ==='.

What it proves (ROADMAP Phase-9 criterion 4, [HEADLESS] half; budgets
quoted from ROADMAP.md:328/355 + PITFALLS.md:379/514 -- PROJECT.md:62
carries no numbers): "Perf budgets confirmed on the largest curated
demo: Generate < 30 s; pick/drag feedback < 200 ms."

Rows, in order (design = 09-RESEARCH-perf-budgets.md SS6):

G - GENERATE on the criterion's demo (cold + warm). The perf target is
    re-derived at runtime via manifest.largest_entry (never a special-
    cased field; smoke_05:180 precedent) and cross-checked to be
    (demo-hard-3, nad, heavy 44). One full gamestart.start_game(...) is
    timed COLD -- cleanup -> engine.new_game (manifest parse + per-
    candidate ligand profile loads + full-payload generation) ->
    engine.materialize(level 0) -> compose -> activate (gamestart.py:
    396-437; the superset of the export-only path). Object growth is
    asserted EXACTLY (1 ligand + 9 grid slots = 10 `_aam_` objects) so
    the row cannot pass vacuously. A SECOND (warm) start is echoed only;
    the COLD number is the asserted user experience.
W - GENERATE at the max LEGAL manifest workload. demo_set_id='' means
    NO candidate filter (all 18 rows, engine.py:317-320); molecules_per_
    level=4 is the ceiling the live 14/4/0 size census supports (the
    generator refuses mPL>=5 with its own GenerationError, generator.py:
    836-840). Level-0 growth asserted EXACTLY (4 x (1 + 9) = 40).
    A GenerationError here FAILS the row with the generator's message --
    never measure past a legality drift.
S - HEAVY SCENE for pick/drag. The row-G payload's LAST level (tier 9,
    grid_n 9) is materialized directly (smoke_05:236 precedent) and the
    82-object count asserted (81 capped AA slots + 1 ligand). A live
    GameWizard is attached via the checkpoint-rebuild pattern (GameWizard
    (payload, registry, 9, 0) + activate; gamestart.py:728-750,
    SMOKE-20-proven) so picks/drags run in the PLAYING state.
P - SCRIPTED PICK timing, N=20 reps, alternating between TWO slot
    objects so every rep exercises the restore+recolor switch path
    (wizard.py:515-517). Recipe = smoke_24:415-416. Reports min/avg/max;
    asserts BOTH avg and max < FEEDBACK_BUDGET_MS (max is the user-feel
    number).
D - SCRIPTED DRAG timing, N=20 reps of wiz.drag_move(dx, dy) alternating
    (+20, +12) / (-20, -12) so the AA stays near its slot. The C drag
    event loop CANNOT be pumped under -cq (wizard.py:921-923), so this
    is the programmatic twin; the bake is "IDENTICAL in form"
    (wizard.py:925-931). The real gesture's feel is the [HUMAN] half
    (plan 09-11). Reports min/avg/max; asserts avg and max < budget.
TEARDOWN - pop the wizard, cleanup_game_objects(), assert the scene is
    EXACTLY the pre-game name-set baseline (smoke_05:385-403 shape).

Every raw number is echoed as SMOKE-ENV lines (the receipt value is the
number, not the boolean). Timing uses stdlib time.time() per the
research harness law; on Windows its wall-clock tick is ~15.6 ms, so a
sub-tick op may read 0.000 ms (min shows the floor, max the observed
tick) -- that quantization is ~8% of the 200 ms budget, and the 30 s
generate rows are unaffected. Tier law: WSL tests assert NOTHING for these
budgets (tests/test_detector_invariance.py's 2.0 s loose guard is WSL-
only and must never leak into this gate -- smoke_05:97-101 precedent).

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv first
/ cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch'); every print on ONE line and flushed; per-check
'SMOKE-25 <label> PASS|FAIL <detail>' lines; explicit space dicts in
every iterate; no round() in expressions.

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import os
import sys
import time
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_25_perf_budgets.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []


def check(name, cond, detail=''):
    print('SMOKE-25 %-42s %s %s'
          % (name, 'PASS' if cond else 'FAIL', detail), flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

from aamatch.persistence import read_json_file  # noqa: E402
from aamatch.manifest import (enumerate_entries, largest_entry,  # noqa: E402
                              parse_manifest_dict)
from aamatch.setup_state import validate_state  # noqa: E402
from aamatch.generator import GenerationError  # noqa: E402
from aamatch.wizard import GameWizard  # noqa: E402
from aamatch import engine, gamestart, geometry, placement  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

# The recorded Phase-9 budgets (ROADMAP.md:328/355 + PITFALLS.md:379
# /514). Local literals asserted RAW -- the WSL-only 2.0 s loose guard
# in tests/test_detector_invariance.py is a different tier and must
# never leak into this gate (smoke_05_perf.py:97-101 precedent).
GENERATE_BUDGET_MS = 30000.0
FEEDBACK_BUDGET_MS = 200.0

PICK_REPS = 20
DRAG_REPS = 20


def _game_objects():
    """Every live object carrying the reserved game prefix."""
    return [n0 for n0 in cmd.get_names('objects')
            if n0.startswith(geometry.GAME_PREFIX)]


def _summarize(samples):
    """(min, avg, max) of a non-empty ms-sample list."""
    lo = min(samples)
    hi = max(samples)
    return lo, sum(samples) / len(samples), hi


pre_names = list(cmd.get_names('objects'))
check('clean pre-game scene', not _game_objects(),
      'pre names: %s' % (pre_names,))

# =============== Row G: Generate on the criterion demo =================
payload_g = None
gen_cold_ms = None
gen_warm_ms = None
try:
    container = read_json_file(os.path.join(
        _ROOT, 'aamatch', 'data', 'MANIFEST.json'))
    entries = enumerate_entries(parse_manifest_dict(container))
    biggest = largest_entry(entries)
    check('G largest_entry selects demo-hard-3/nad',
          biggest is not None
          and biggest['set_id'] == 'demo-hard-3'
          and biggest['entry_id'] == 'nad'
          and biggest['heavy_atom_count'] == 44,
          'target=%s/%s heavy=%d of %d entries'
          % (biggest['set_id'], biggest['entry_id'],
             biggest['heavy_atom_count'], len(entries)))
    # Default 'unset' interaction mode + mPL 1 / D 10 == the criterion
    # shape (smoke_05:207-211's workload, without the pi_stacking lock).
    setup = validate_state({'molecules_per_level': 1,
                            'difficulty_levels': 10})
    t0 = time.time()
    wiz_g = gamestart.start_game(setup, seed=42, candidates=[biggest])
    gen_cold_ms = (time.time() - t0) * 1000.0
    payload_g = wiz_g._payload
    n_objs = len(_game_objects())
    check('G level-0 growth == 10 objects', n_objs == 10,
          'live=%d want 10 (1 ligand + 9 slots)' % (n_objs,))
    check('G cold generate < 30 s', gen_cold_ms < GENERATE_BUDGET_MS,
          'cold=%.1f ms (< %.0f ms)' % (gen_cold_ms, GENERATE_BUDGET_MS))
    # Warm re-run (cleanup-first lives inside start_game, gamestart.py:
    # 396) -- ECHO ONLY; the cold number is asserted above.
    t0 = time.time()
    gamestart.start_game(setup, seed=42, candidates=[biggest])
    gen_warm_ms = (time.time() - t0) * 1000.0
    check('G warm generate echoed', gen_warm_ms is not None,
          'warm=%.1f ms (echo only)' % (gen_warm_ms,))
    print('SMOKE-ENV perf25 generate_cold_ms=%d generate_warm_ms=%d'
          % (int(gen_cold_ms + 0.5), int(gen_warm_ms + 0.5)), flush=True)
except Exception:
    traceback.print_exc()
    check('G generate on largest demo', False,
          'raised (see traceback above)')
    payload_g = None

# ======== Row W: Generate at the max LEGAL manifest workload ==========
workload_ms = None
try:
    setup_w = validate_state({'demo_set_id': '',
                              'molecules_per_level': 4,
                              'difficulty_levels': 10})
    t0 = time.time()
    gamestart.start_game(setup_w, seed=42)
    workload_ms = (time.time() - t0) * 1000.0
    n_objs = len(_game_objects())
    check('W level-0 growth == 40 objects', n_objs == 40,
          'live=%d want 40 (4 x (1 + 9))' % (n_objs,))
    check('W max-legal generate < 30 s', workload_ms < GENERATE_BUDGET_MS,
          'workload=%.1f ms (< %.0f ms)'
          % (workload_ms, GENERATE_BUDGET_MS))
    print('SMOKE-ENV perf25 workload_ms=%d'
          % (int(workload_ms + 0.5),), flush=True)
except GenerationError as exc:
    # A refusal means workload legality drifted (the 14/4/0 census is a
    # data fact) -- FAIL with the generator's own message, never
    # measure past it (research SS6/SS8).
    check('W max-legal workload generates', False,
          'GenerationError: %s' % (exc,))
except Exception:
    traceback.print_exc()
    check('W max-legal workload generates', False,
          'raised (see traceback above)')

# ============= Row S: heavy 82-object scene + live wizard =============
wiz_s = None
registry_s = None
if payload_g is not None:
    try:
        placement.cleanup_game_objects()
        registry_s = engine.materialize(payload_g, level_index=9)
        n_objs = len(_game_objects())
        check('S heavy scene == 82 objects', n_objs == 82,
              'live=%d want 82 (1 ligand + 81 capped slots)' % (n_objs,))
        wiz_s = GameWizard(payload_g, registry_s, 9, 0)
        # replace=1 pops+cleans the row-W GameWizard (activate's
        # documented replace contract; gamestart.activate_game:351).
        wiz_s.activate(replace=1)
        check('S GameWizard live on level 9',
              cmd.get_wizard() is wiz_s,
              'top=%r' % (cmd.get_wizard(),))
        print('SMOKE-ENV perf25 heavy_objects=%d' % (n_objs,), flush=True)
    except Exception:
        traceback.print_exc()
        check('S heavy scene assembly', False,
              'raised (see traceback above)')
        wiz_s = None
else:
    check('S heavy scene assembly', False,
          'skipped: row G produced no payload')

# =============== Row P: scripted pick timing (N=20) ===================
if wiz_s is not None:
    try:
        mol = registry_s['molecules'][0]
        slot_ids = sorted(mol['slots'])
        check('P two switchable slots exist', len(slot_ids) >= 2,
              'slots=%d' % (len(slot_ids),))
        slot_obj_a = mol['slots'][slot_ids[0]][0]
        slot_obj_b = mol['slots'][slot_ids[1]][0]
        picks = []
        seen_switch = False
        last_slot = None
        for rep in range(PICK_REPS):
            target = slot_obj_a if rep % 2 == 0 else slot_obj_b
            t0 = time.time()
            cmd.select('sele', '%s and name CA' % target)
            wiz_s.do_select('sele')
            picks.append((time.time() - t0) * 1000.0)
            now_slot = wiz_s._current_slot
            if last_slot is not None and now_slot != last_slot:
                seen_switch = True
            last_slot = now_slot
        check('P picks exercised the switch path', seen_switch,
              'alternated two slots across %d reps' % (PICK_REPS,))
        pick_min, pick_avg, pick_max = _summarize(picks)
        check('P pick avg < 200 ms', pick_avg < FEEDBACK_BUDGET_MS,
              'avg=%.3f ms (< %.0f ms)'
              % (pick_avg, FEEDBACK_BUDGET_MS))
        check('P pick max < 200 ms', pick_max < FEEDBACK_BUDGET_MS,
              'max=%.3f ms (< %.0f ms)'
              % (pick_max, FEEDBACK_BUDGET_MS))
        check('P pick left no wizard error', wiz_s._error is None,
              'error=%r' % (wiz_s._error,))
        print('SMOKE-ENV perf25 pick_min_ms=%d pick_avg_ms=%d '
              'pick_max_ms=%d'
              % (int(pick_min + 0.5), int(pick_avg + 0.5),
                 int(pick_max + 0.5)), flush=True)
    except Exception:
        traceback.print_exc()
        check('P scripted pick timing', False,
              'raised (see traceback above)')
else:
    check('P scripted pick timing', False,
          'skipped: heavy scene not assembled')

# =============== Row D: scripted drag timing (N=20) ===================
if wiz_s is not None:
    try:
        # Non-vacuity guard (this row must not pass if drag_move silently
        # no-ops): the AA picked in row P must actually displace on the
        # first rep. Without this, a zero-work drag records 0 ms and
        # would satisfy the budget for the wrong reason.
        obj_d = registry_s['molecules'][0]['slots'][wiz_s._current_slot][0]
        start_c = geometry.centroid_of(obj_d)
        drags = []
        first_move = None
        for rep in range(DRAG_REPS):
            if rep % 2 == 0:
                dx, dy = 20.0, 12.0
            else:
                dx, dy = -20.0, -12.0
            t0 = time.time()
            wiz_s.drag_move(dx, dy)
            drags.append((time.time() - t0) * 1000.0)
            if rep == 0:
                end_c = geometry.centroid_of(obj_d)
                first_move = max(abs(end_c[i] - start_c[i])
                                 for i in range(3))
        check('D drag moved the selected AA',
              first_move is not None and first_move > 1e-3,
              'first-rep centroid delta=%.4f A' % (first_move,))
        drag_min, drag_avg, drag_max = _summarize(drags)
        check('D drag avg < 200 ms', drag_avg < FEEDBACK_BUDGET_MS,
              'avg=%.3f ms (< %.0f ms)'
              % (drag_avg, FEEDBACK_BUDGET_MS))
        check('D drag max < 200 ms', drag_max < FEEDBACK_BUDGET_MS,
              'max=%.3f ms (< %.0f ms)'
              % (drag_max, FEEDBACK_BUDGET_MS))
        check('D drag left no wizard error', wiz_s._error is None,
              'error=%r' % (wiz_s._error,))
        print('SMOKE-ENV perf25 drag_min_ms=%d drag_avg_ms=%d '
              'drag_max_ms=%d'
              % (int(drag_min + 0.5), int(drag_avg + 0.5),
                 int(drag_max + 0.5)), flush=True)
    except Exception:
        traceback.print_exc()
        check('D scripted drag timing', False,
              'raised (see traceback above)')
else:
    check('D scripted drag timing', False,
          'skipped: heavy scene not assembled')

# ============================ Teardown ===============================
try:
    if wiz_s is not None or cmd.get_wizard() is not None:
        cmd.set_wizard()            # pop -> wizard cleanup (msm/buttons)
    result = placement.cleanup_game_objects()
    post_names = list(cmd.get_names('objects'))
    check('teardown leaves scene pre-game',
          post_names == pre_names and not _game_objects(),
          'deleted=%d post=%s' % (result['deleted'], post_names))
except Exception:
    traceback.print_exc()
    check('teardown', False, 'raised (see traceback above)')
    placement.cleanup_game_objects()   # never leave game objects

# --- Verdict marker (the SOLE verdict carrier) -----------------------
print('=== SMOKE-25 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'), flush=True)
