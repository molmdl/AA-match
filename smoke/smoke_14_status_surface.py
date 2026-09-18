"""Headless smoke 14 - the status-surface READ path (plan 05-07, T1a).

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_14_status_surface.py 120
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-14 PASS ==='.

Proves the two additive status accessors of the Phase-5 status access
path (05-RESEARCH-status-surface.md, researcher B's Q6) headlessly in
REAL PyMOL. The Game status tab must NEVER reach engine/wizard privates
and must NEVER push callbacks onto the wizard (session save pickles the
whole wizard stack -- wizarding.py:175-180; wizard.py contract 2), so
everything the tab polls is plain data behind these public accessors:

T1a (THIS smoke, always runs, no dialog):
PART 1  accessors -- engine.game_status() raises EngineError BEFORE
        any game (the _current_game guard, engine.py:98-103); after
        gamestart.start_game() (defaults -- the default path activates,
        fine for the accessor drive), GameWizard.get_status() returns
        the _state_dict shape PLUS the 05-07 additive level keys
        (level_pos/level_total), is plain data (json.dumps succeeds --
        no Qt objects/callables can reach the tab), carries the right
        molecule counting (molecule_pos == 1, molecule_total ==
        len(registry['molecules'])), and is mutation-free across calls
        (s2 == status); engine.game_status() then returns the EXACT
        7-key GameState.to_dict() shape with molecule_scores == [].
        timer_anchor tolerance is UNCONDITIONAL (None or float): same-
        wave plan 05-05 makes the DEFAULT start_game path anchor the
        timer at activation, so a merged-tree regression run may
        legitimately read a float here.
PART 2  restore -- Done (canonical cmd.set_wizard()) +
        placement.cleanup_game_objects() returns the scene to the
        pre-start snapshot EXACTLY.

T1b (extension slot): the status-SURFACE parts (populated tab fields)
are added by the status-wiring plan (05-10) as additional PARTs; the
amount of PARTs in this file grows additively, and the verdict marker
stays the sole carrier.

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv
first / cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch'); every print on ONE line and flushed; check details
built from already-known data only (the 03-04 eager-detail lesson --
never call into the code under test to build an assert message).

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import json
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_14_status_surface.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []
REC = {}


def check(name, cond, detail=''):
    print('SMOKE-14 %-44s %s %s' % (name, 'PASS' if cond else 'FAIL',
                                     detail), flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

import aamatch  # noqa: E402
from aamatch import engine, gamestart, placement  # noqa: E402
from aamatch.wizard import GameWizard  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

_STATE_KEYS = ('molecule_id', 'molecule_pos', 'molecule_total',
               'required', 'selected', 'result', 'error',
               'level_pos', 'level_total')
_GAME_KEYS = ('current_level_index', 'current_molecule_index',
              'molecule_scores', 'skip_count', 'giveup_count',
              'timer_anchor', 'formed_types_per_molecule')

# ============================================================
# PART 0: pre-start snapshot
# ============================================================
pre_names = list(cmd.get_names('objects'))

# ============================================================
# PART 1 (T1a): the accessor drive
# ============================================================
wiz = None
try:
    # -- 1: EngineError BEFORE any game ---
    raised = None
    try:
        engine.game_status()
    except engine.EngineError as e:
        raised = str(e)
    check('game_status raises EngineError before new_game',
          raised is not None,
          'raised=%r' % (raised,))

    # -- 2: start the default game ---
    wiz = gamestart.start_game()
    check('start_game returns a GameWizard',
          isinstance(wiz, GameWizard), 'type=%r' % (type(wiz),))

    # -- 3: get_status shape + plain-data + level/molecule counting ---
    status = wiz.get_status()
    missing = [k for k in _STATE_KEYS if k not in status]
    check('get_status carries the full state shape + level keys',
          isinstance(status, dict) and not missing,
          'missing=%s' % (missing,))
    check('level counting (level_pos 1, level_total int >= 1)',
          status.get('level_pos') == 1
          and isinstance(status.get('level_total'), int)
          and status.get('level_total', 0) >= 1,
          'level_pos=%r level_total=%r'
          % (status.get('level_pos'), status.get('level_total')))
    jsonable = None
    try:
        json.dumps(status)
        jsonable = True
    except (TypeError, ValueError):
        jsonable = False
    check('status is plain data (json round-trip; contract 2)',
          jsonable is True,
          'json.dumps(status) succeeded' if jsonable else
          'json.dumps raised -- Qt/callable leaked into the snapshot')
    mtotal = len(wiz._registry['molecules'])
    check('molecule counting matches the live registry',
          status.get('molecule_pos') == 1
          and status.get('molecule_total') == mtotal,
          'molecule_pos=%r molecule_total=%r registry=%d'
          % (status.get('molecule_pos'), status.get('molecule_total'),
             mtotal))
    REC['level_total'] = status.get('level_total')
    REC['molecule_total'] = mtotal

    # -- 4: no mutation across calls ---
    s2 = wiz.get_status()
    check('repeated get_status is mutation-free (s2 == status)',
          s2 == status, '')

    # -- 5: engine.game_status exact 7-key shape ---
    gs = engine.game_status()
    check('game_status key set is EXACTLY the 7 to_dict keys',
          isinstance(gs, dict) and set(gs) == set(_GAME_KEYS),
          'keys=%s' % (sorted(gs) if isinstance(gs, dict) else type(gs),))
    anchor = gs.get('timer_anchor')
    check('timer_anchor None or float (UNCONDITIONAL 05-05 tolerance)',
          anchor is None or isinstance(anchor, float),
          'timer_anchor=%r' % (anchor,))
    check('fresh game: molecule_scores empty',
          gs.get('molecule_scores') == [],
          'molecule_scores=%r' % (gs.get('molecule_scores'),))
except Exception:
    traceback.print_exc()
    check('part 1 accessor drive', False, 'raised (see traceback above)')

# ============================================================
# PART 2: restore -- scene back to the pre-start snapshot EXACTLY
# ============================================================
try:
    if cmd.get_wizard() is not None:
        cmd.set_wizard()
    cleaned = placement.cleanup_game_objects()
    REC['teardown_deleted'] = cleaned['deleted']
    check('teardown returns the scene to pre-start EXACTLY',
          list(cmd.get_names('objects')) == pre_names,
          'deleted=%d post=%s' % (cleaned['deleted'],
                                  cmd.get_names('objects')))
except Exception:
    traceback.print_exc()
    check('part 2 teardown', False, 'raised (see traceback above)')
    placement.cleanup_game_objects()

# --- evidence summary -------------------------------------------------
print('SMOKE-ENV record: %s'
      % dict((k, v) for k, v in sorted(REC.items())), flush=True)

# --- Verdict marker (the SOLE verdict carrier) --------------------------
print('=== SMOKE-14 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
