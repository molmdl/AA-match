"""Headless smoke 15 - the engine LIFECYCLE ops (plan 06-03).

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_15_lifecycle.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-15 PASS ==='.

Proves the 06-03 engine lifecycle ops headlessly in REAL PyMOL
(cmd-tier E2E -- the always tier; PART letters stay appendable so
06-05/06-06 can grow PART B/C for the wizard/tab halves):

PART A  the pure cmd drive over the DEFAULT game (seed 42; 2
        molecules/level x 3 levels, frozen Phase-1 DEFAULTS):
        A1   baseline snapshot; gamestart.start_game(activate=True)
             returns a GameWizard; the timer anchors (activate_game).
        A2   Zero-score Confirm mechanics: engine.record_scored(0, 0,
             required-from-payload) returns (0.0, []) at grid state --
             the score VALUE itself is smoke_04's proven domain, this
             smoke only needs deterministic zero-score mechanics to
             exercise the lifecycle. is_over() False / total_score()
             0.0 reads work.
        A3   GUARD (the D4/Q10 one-record site): a second
             record_scored on (0, 0) raises EngineError with the EXACT
             pinned refusal text, and the GameState is UNCHANGED
             (still exactly one record).
        A4   skip_molecule(0, 1, required): skip_count == 1, a second
             molecule_scores entry recorded via the SAME record path
             (02-10 sanctioned semantics); a skip-after-record retry
             is refused by the SAME message (Confirm and Skip share
             the one guard site).
        A5   advance_molecule: data-only (current_molecule_index 2,
             no range check by design -- the wizard owns range logic);
             advance_level: cleanup + materialize(L+1) + GameState
             advance atomically -> registry level_index 1, fresh
             _aam_* names with the derived count, game_status level 1
             molecule 0, and the TIMER ANCHOR UNCHANGED (the D6
             intent: the game clock runs across levels).
        A6   give_up mid-level-1: is_over True, end_state 'gave_up',
             giveup_count 1, final_time a float >= 0.0 (anchor STILL
             untouched), summary keys EXACTLY the 06-01 SCORE-07
             contract (sorted equality), level_scores length == levels.
        A7   fresh game (the restart seam): start_game(activate=True)
             again -> game_status zeroed INCLUDING the 06-01 fields
             (game_over False, end_state None, final_time None);
             a full completion drive (record_scored every molecule,
             advance_molecule/advance_level between, the last-level
             advance refused naming "no next level") -> complete_game()
             end_state 'completed', molecules_completed == molecules,
             total == sum(level_scores).
        A8   restore: Done pop + prefix cleanup -> baseline EXACTLY;
             gamestart._last_start reset (SMOKE-08 store hygiene).

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv
first / cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch'); every print on ONE line and flushed; check details
built from already-known data only (the 03-04 eager-detail lesson --
never call into the code under test to build an assert message).

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_15_lifecycle.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []
REC = {'checks': 0}


def check(name, cond, detail=''):
    REC['checks'] += 1
    print('SMOKE-15 %-46s %s %s' % (name, 'PASS' if cond else 'FAIL',
                                    detail), flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

from aamatch import engine, gamestart, placement  # noqa: E402
from aamatch.wizard import GameWizard  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

_REFUSAL = ('This molecule already has a recorded result (scored or '
            'skipped) -- use Restart to replay the game.')
_SUMMARY_KEYS = ('end_state', 'ended_level', 'ended_molecule',
                 'final_time', 'giveup_count', 'level_scores', 'levels',
                 'molecules', 'molecules_completed', 'skip_count',
                 'total')

pre_names = list(cmd.get_names('objects'))

# ============================================================
# PART A1: baseline + default start
# ============================================================
wiz = None
try:
    wiz = gamestart.start_game(activate=True)
    check('A1 start_game returns a GameWizard',
          isinstance(wiz, GameWizard), 'type=%r' % (type(wiz),))
    gs = engine.game_status()
    check('A1 fresh anchored timer (activate=True path)',
          isinstance(gs.get('timer_anchor'), float),
          'timer_anchor=%r' % (gs.get('timer_anchor'),))
    check('A1 zeroed lifecycle fields (06-01 shape)',
          gs.get('game_over') is False and gs.get('end_state') is None
          and gs.get('final_time') is None
          and gs.get('molecule_scores') == []
          and gs.get('skip_count') == 0 and gs.get('giveup_count') == 0,
          'game_over=%r end_state=%r final_time=%r scores=%r'
          % (gs.get('game_over'), gs.get('end_state'),
             gs.get('final_time'), gs.get('molecule_scores')))
except Exception:
    traceback.print_exc()
    check('A1 start', False, 'raised (see traceback above)')

# ============================================================
# PART A2: zero-score record mechanics + the reads
# ============================================================
try:
    payload = engine._payload
    n_levels = len(payload['levels'])
    molecules_per_level = [len(lev['molecules'])
                           for lev in payload['levels']]
    check('A2 default game shape (3 levels x 2 molecules)',
          n_levels == 3 and molecules_per_level == [2, 2, 2],
          'levels=%d molecules=%s' % (n_levels, molecules_per_level))
    required_00 = payload['levels'][0]['molecules'][0]['required']
    value, formed = engine.record_scored(0, 0, required_00)
    check('A2 record_scored(0,0) returns (0.0, []) at grid state',
          value == 0.0 and formed == [],
          'value=%r formed=%r' % (value, formed))
    check('A2 reads: is_over False, total_score 0.0',
          engine.is_over() is False and engine.total_score() == 0.0,
          'is_over=%r total=%r' % (engine.is_over(),
                                   engine.total_score()))
except Exception:
    traceback.print_exc()
    check('A2 record drives', False, 'raised (see traceback above)')

# ============================================================
# PART A3: the one-record GUARD (D4/Q10 pinned refusal)
# ============================================================
try:
    before = engine.game_status()
    raised = None
    try:
        engine.record_scored(0, 0, required_00)
    except engine.EngineError as exc:
        raised = str(exc)
    check('A3 second record refused with the EXACT pinned text',
          raised == _REFUSAL,
          'raised=%r' % (raised,))
    check('A3 EngineError is the house ValueError family',
          issubclass(engine.EngineError, ValueError), '')
    after = engine.game_status()
    check('A3 state UNCHANGED after refusal (one record stands)',
          len(after.get('molecule_scores') or []) == 1
          and after.get('skip_count') == before.get('skip_count')
          and len(after.get('score_per_molecule') or {}) == 1,
          'scores=%d keys=%s'
          % (len(after.get('molecule_scores') or []),
             sorted(after.get('score_per_molecule') or {})))
except Exception:
    traceback.print_exc()
    check('A3 guard drive', False, 'raised (see traceback above)')

# ============================================================
# PART A4: skip_molecule (02-10 sanctioned semantics)
# ============================================================
try:
    required_01 = payload['levels'][0]['molecules'][1]['required']
    s_val, s_formed = engine.skip_molecule(0, 1, required_01)
    gs = engine.game_status()
    check('A4 skip records via the same path + counts',
          gs.get('skip_count') == 1
          and len(gs.get('molecule_scores') or []) == 2
          and sorted(gs.get('score_per_molecule') or {})
          == ['L0M0', 'L0M1'],
          'skip=%d scores=%r value=%r formed=%r'
          % (gs.get('skip_count'), gs.get('molecule_scores'),
             s_val, s_formed))
    raised = None
    try:
        engine.skip_molecule(0, 1, required_01)
    except engine.EngineError as exc:
        raised = str(exc)
    check('A4 skip-after-record refused by the SAME guard text',
          raised == _REFUSAL,
          'raised=%r' % (raised,))
except Exception:
    traceback.print_exc()
    check('A4 skip drive', False, 'raised (see traceback above)')

# ============================================================
# PART A5: molecule/level advance -- anchor untouched (D6)
# ============================================================
try:
    # One advance per recorded molecule (the wizard drives exactly one
    # per Confirm/Skip): A2's record + A4's skip -> index 2, PAST the
    # last molecule of the level -- the data-only transition performs
    # NO range check by design (the wizard owns range logic).
    engine.advance_molecule()
    engine.advance_molecule()
    gs = engine.game_status()
    check('A5 advance_molecule is DATA-only (index 2, no range check)',
          gs.get('current_level_index') == 0
          and gs.get('current_molecule_index') == 2,
          'level=%r molecule=%r'
          % (gs.get('current_level_index'),
             gs.get('current_molecule_index')))
    anchor_before = engine.game_status().get('timer_anchor')
    registry = engine.advance_level()
    gs = engine.game_status()
    expected_objects = sum(
        1 + len(mol['slots']) for mol in registry['molecules'])
    aam_names = [n for n in cmd.get_names('objects')
                 if n.startswith('_aam_')]
    check('A5 advance_level registry: level 1, derived object count',
          registry.get('level_index') == 1
          and len(aam_names) == expected_objects,
          'level_index=%r objects=%d expected=%d'
          % (registry.get('level_index'), len(aam_names),
             expected_objects))
    check('A5 advance_level GameState: level 1 molecule 0',
          gs.get('current_level_index') == 1
          and gs.get('current_molecule_index') == 0,
          'level=%r molecule=%r'
          % (gs.get('current_level_index'),
             gs.get('current_molecule_index')))
    check('A5 timer anchor UNCHANGED across the level advance (D6)',
          gs.get('timer_anchor') == anchor_before,
          'before=%r after=%r' % (anchor_before,
                                  gs.get('timer_anchor')))
except Exception:
    traceback.print_exc()
    check('A5 advance drive', False, 'raised (see traceback above)')

# ============================================================
# PART A6: give_up mid-level-1 -- frozen game + summary contract
# ============================================================
try:
    anchor_before = engine.game_status().get('timer_anchor')
    summary = engine.give_up()
    gs = engine.game_status()
    check('A6 give_up freezes the game',
          engine.is_over() is True
          and gs.get('end_state') == 'gave_up'
          and gs.get('giveup_count') == 1,
          'is_over=%r end_state=%r giveup=%r'
          % (engine.is_over(), gs.get('end_state'),
             gs.get('giveup_count')))
    check('A6 final_time frozen float >= 0.0; anchor STILL untouched',
          isinstance(gs.get('final_time'), float)
          and gs.get('final_time') >= 0.0
          and gs.get('timer_anchor') == anchor_before,
          'final_time=%r anchor=%r (was %r)'
          % (gs.get('final_time'), gs.get('timer_anchor'),
             anchor_before))
    check('A6 summary keys EXACTLY the 06-01 SCORE-07 contract',
          isinstance(summary, dict)
          and sorted(summary) == sorted(_SUMMARY_KEYS),
          'keys=%s' % (sorted(summary) if isinstance(summary, dict)
                       else type(summary),))
    check('A6 summary shape: level-scores per level, ended position',
          summary.get('end_state') == 'gave_up'
          and len(summary.get('level_scores') or [])
          == summary.get('levels')
          and summary.get('ended_level') == 2
          and summary.get('molecules_completed') == 2,
          'end=%r level_scores=%r levels=%r ended_level=%r done=%r'
          % (summary.get('end_state'), summary.get('level_scores'),
             summary.get('levels'), summary.get('ended_level'),
             summary.get('molecules_completed')))
    raised = None
    try:
        engine.give_up()
    except engine.EngineError as exc:
        raised = str(exc)
    check('A6 double give-up refused (game already over)',
          raised is not None and 'already over' in raised,
          'raised=%r' % (raised,))
except Exception:
    traceback.print_exc()
    check('A6 give_up drive', False, 'raised (see traceback above)')

# ============================================================
# PART A7: fresh game + the natural-completion drive
# ============================================================
try:
    wiz2 = gamestart.start_game(activate=True)
    check('A7 restart seam returns a GameWizard',
          isinstance(wiz2, GameWizard), 'type=%r' % (type(wiz2),))
    gs = engine.game_status()
    check('A7 fresh GameState wipes the ended game (all-zero incl. '
          '06-01 fields)',
          gs.get('game_over') is False and gs.get('end_state') is None
          and gs.get('final_time') is None
          and gs.get('molecule_scores') == []
          and gs.get('skip_count') == 0 and gs.get('giveup_count') == 0
          and gs.get('current_level_index') == 0
          and gs.get('current_molecule_index') == 0,
          'game_over=%r end_state=%r final_time=%r scores=%r'
          % (gs.get('game_over'), gs.get('end_state'),
             gs.get('final_time'), gs.get('molecule_scores')))

    payload2 = engine._payload
    # Full completion drive: record every molecule of every level.
    for level_idx, level in enumerate(payload2['levels']):
        molecules = level['molecules']
        for mol_idx, molecule in enumerate(molecules):
            engine.record_scored(level_idx, mol_idx,
                                 molecule['required'])
            if mol_idx < len(molecules) - 1:
                engine.advance_molecule()
        if level_idx < len(payload2['levels']) - 1:
            engine.advance_molecule()
            engine.advance_level()
    gs = engine.game_status()
    check('A7 every molecule recorded across the drive',
          len(gs.get('molecule_scores') or []) == 6
          and gs.get('current_level_index') == 2
          and gs.get('current_molecule_index') == 1,
          'scores=%d level=%r molecule=%r'
          % (len(gs.get('molecule_scores') or []),
             gs.get('current_level_index'),
             gs.get('current_molecule_index')))
    raised = None
    try:
        engine.advance_level()
    except engine.EngineError as exc:
        raised = str(exc)
    check('A7 last-level advance refused naming "no next level"',
          raised is not None and 'no next level' in raised,
          'raised=%r' % (raised,))
    summary2 = engine.complete_game()
    gs = engine.game_status()
    check('A7 complete_game: completed state + summary laws',
          summary2.get('end_state') == 'completed'
          and summary2.get('molecules_completed')
          == summary2.get('molecules') == 6
          and gs.get('giveup_count') == 0
          and engine.is_over() is True,
          'end=%r completed=%r molecules=%r giveup=%r is_over=%r'
          % (summary2.get('end_state'),
             summary2.get('molecules_completed'),
             summary2.get('molecules'), gs.get('giveup_count'),
             engine.is_over()))
    check('A7 total == sum(level_scores) (06-01 aggregation)',
          abs(summary2.get('total', -1.0)
              - sum(summary2.get('level_scores') or ())) < 1e-12,
          'total=%r level_scores=%r'
          % (summary2.get('total'), summary2.get('level_scores')))
    check('A7 read op equals the returned summary (read-only)',
          engine.endgame_summary() == summary2, '')
except Exception:
    traceback.print_exc()
    check('A7 completion drive', False, 'raised (see traceback above)')

# ============================================================
# PART A8: restore -- scene back to the baseline EXACTLY
# ============================================================
try:
    if cmd.get_wizard() is not None:
        cmd.set_wizard()
    cleaned = placement.cleanup_game_objects()
    REC['teardown_deleted'] = cleaned['deleted']
    check('A8 teardown returns the scene to the baseline EXACTLY',
          list(cmd.get_names('objects')) == pre_names,
          'deleted=%d post=%s' % (cleaned['deleted'],
                                  cmd.get_names('objects')))
    gamestart._last_start = None
except Exception:
    traceback.print_exc()
    check('A8 teardown', False, 'raised (see traceback above)')
    placement.cleanup_game_objects()

# --- Verdict marker (the SOLE verdict carrier) -------------------------------
print('SMOKE-15 PART A: %d checks, %d failure(s)'
      % (REC['checks'], len(failures)), flush=True)
print('=== SMOKE-15 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
