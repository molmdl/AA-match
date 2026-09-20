"""Headless smoke 15 - the engine LIFECYCLE ops (plan 06-03).

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_15_lifecycle.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-15 PASS ==='.

Proves the 06-03 engine lifecycle ops (PART A), the 06-05 wizard
lifecycle core (PART B), and the 06-06 wizard skip/give-up half
(PART C) headlessly in REAL PyMOL (cmd-tier E2E -- the always tier;
PART letters stay appendable so 06-07's tab side can grow further
letters):

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

PART B  the WIZARD-tier lifecycle E2E (06-05; drives the wizard's
        PUBLIC methods only -- no modals anywhere):
        B1   fresh default start: cmd.get_wizard() IS the returned
             GameWizard; the timer anchor is captured; the initial
             status shows level 1 mol 1 with a None marker.
        B2   MOLECULE advance: confirm_molecule() returns the plain
             dict; advanced 'molecule', mol 2 of the level, marker
             molecule_scored seq 1 molecule_pos 1, result cleared (D3),
             selection cleared, required reflects molecule 2, and the
             camera RE-FRAMED onto the NEW molecule (06-10 human
             checkpoint fix: the molecule branch runs the SAME 06-04
             compose seam as the level branch -- the zoom target names
             only the new molecule's objects).
        B3   LEVEL advance (the second confirm closes level 1):
             advanced 'level', level 2 mol 1, the SAME wizard instance
             still on the stack, the timer anchor UNCHANGED (the D6
             intent assert), a fresh scene at the derived object count,
             selection/result cleared, marker seq 2 molecule_pos 2, and
             the camera view CHANGED (the 06-04 compose running).
        B4   rebind proof: the SMOKE-07 scripted-pick recipe on a slot
             of the NEW molecule resolves slot identity through the
             rebuilt maps.
        B5   completion drive: four more confirms walk molecule ->
             level -> molecule -> None; the last returns game_over True
             + the 06-01 summary keys, status shows game_over/
             'completed', engine.is_over() True.
        B6   restore: Done pop + prefix cleanup -> baseline EXACTLY;
             gamestart._last_start reset.
        NOTE: the re-Confirm REFUSAL is proven at the engine level in
        PART A only -- after a real advance a second Confirm always
        lands on the NEXT molecule, so a wizard-level double-Confirm
        refusal is unreachable by design.

PART C  the 06-06 wizard skip/give-up half (SCORE-05/06 wizard ops,
        game-over gating, reset marker; public wizard methods only):
        C1   fresh start; confirm molecule 1 -> skip molecule 2 ->
             advanced 'level', skip_count 1, two molecule_scores, the
             molecule_skipped marker (pos 2 of 2, seq 2), status at
             level 2 molecule 1 -- skip advances EXACTLY like Confirm
             through the shared _advance_after_record.
        C2   skip-COMPLETES-the-game: confirm/skip through to the
             LAST molecule of the LAST level, then skip_molecule ->
             advanced None, game_over True, summary end_state
             'completed' (a skipped final molecule still finishes the
             game -- every molecule has a record).
        C3   full game-over LOCKDOWN: fresh game, select a slot, then
             give_up -> nudge_cam / rotate_view refused with the
             pinned 'The game is over.' AND the pose unchanged; hint /
             reset_grid / skip_molecule / confirm_molecule all refuse
             (None through _guard); a scripted pick on a DIFFERENT
             slot is a SOFT no-op (selection unchanged -- never raise
             into the C-layer pick dispatch).
        C4   give_up data: the return carries game_over True + the
             exact 06-01 summary keys; the wizard marker is gave_up
             (level/molecule position of the end); game_status shows
             giveup_count 1, end_state 'gave_up', a frozen float
             final_time; get_status()['end_state'] 'gave_up'.
        C5   reset marker: fresh game, select + move_to one AA far
             off-grid, then reset_grid -> the last_event marker kind
             is 'game_reset'; the AA's centroid is back at the
             effective_position target (1e-6 tolerance + float32 ulp
             slack); game_status to_dict UNCHANGED (reset touches NO
             GameState data -- the marker is the ONLY channel the
             poll sees the reset through).
        C6   restore: Done pop + prefix cleanup -> baseline EXACTLY;
             gamestart._last_start reset.

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

from aamatch import engine, gamestart, geometry, placement  # noqa: E402,E501
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

# ============================================================
# PART B (06-05): the WIZARD lifecycle core -- confirm -> event
# marker -> atomic advance, through the wizard's PUBLIC methods.
# ============================================================
part_a_checks = REC['checks']

# ============================================================
# PART B1: default start + anchor capture
# ============================================================
wiz_b = None
anchor0 = None
try:
    wiz_b = gamestart.start_game(activate=True)
    check('B1 start_game returns the stacked GameWizard',
          isinstance(wiz_b, GameWizard) and cmd.get_wizard() is wiz_b,
          'type=%r' % (type(wiz_b),))
    anchor0 = engine.game_status().get('timer_anchor')
    check('B1 timer anchor captured (float)',
          isinstance(anchor0, float), 'anchor0=%r' % (anchor0,))
    st = wiz_b.get_status()
    check('B1 initial status: level 1 mol 1, no marker, not over',
          st.get('level_pos') == 1 and st.get('molecule_pos') == 1
          and st.get('molecule_total') == 2
          and st.get('level_total') == 3
          and st.get('last_event') is None
          and st.get('game_over') is False
          and st.get('end_state') is None,
          'level_pos=%r molecule_pos=%r last_event=%r game_over=%r'
          % (st.get('level_pos'), st.get('molecule_pos'),
             st.get('last_event'), st.get('game_over')))
except Exception:
    traceback.print_exc()
    check('B1 start', False, 'raised (see traceback above)')

# ============================================================
# PART B2: MOLECULE advance via Confirm (zero-score mechanics)
# ============================================================
try:
    view_pre2 = [float(v) for v in cmd.get_view()]
    ret1 = wiz_b.confirm_molecule()
    st = wiz_b.get_status()
    ev = st.get('last_event') or {}
    check('B2 molecule advance return contract',
          isinstance(ret1, dict)
          and ret1.get('advanced') == 'molecule'
          and isinstance(ret1.get('score'), float)
          and isinstance(ret1.get('total'), float)
          and ret1.get('game_over') is False,
          'advanced=%r score=%r total=%r'
          % (ret1.get('advanced') if isinstance(ret1, dict) else ret1,
             ret1.get('score') if isinstance(ret1, dict) else None,
             ret1.get('total') if isinstance(ret1, dict) else None))
    check('B2 status moved to molecule 2 of level 1',
          st.get('molecule_pos') == 2 and st.get('level_pos') == 1,
          'molecule_pos=%r level_pos=%r'
          % (st.get('molecule_pos'), st.get('level_pos')))
    check('B2 marker: molecule_scored seq 1, completed pos 1 of 2',
          ev.get('kind') == 'molecule_scored' and ev.get('seq') == 1
          and ev.get('molecule_pos') == 1
          and ev.get('molecule_total') == 2
          and isinstance(ev.get('formed'), list)
          and isinstance(ev.get('extras'), list),
          'kind=%r seq=%r pos=%r total=%r'
          % (ev.get('kind'), ev.get('seq'), ev.get('molecule_pos'),
             ev.get('molecule_total')))
    check('B2 D3: result + selection cleared on advance',
          st.get('result') is None and st.get('selected') is None,
          'result=%r selected=%r'
          % (st.get('result'), st.get('selected')))
    required_m1 = engine._payload['levels'][0]['molecules'][1] \
        ['required']
    check('B2 required label data reflects molecule 2',
          st.get('required') == required_m1,
          'required=%r want=%r' % (st.get('required'), required_m1))
    view_b2 = [float(v) for v in cmd.get_view()]
    mol_b0 = wiz_b._registry['molecules'][0]
    mol_b1 = wiz_b._registry['molecules'][wiz_b._molecule_index]
    names_b0 = [mol_b0['ligand'][0]]
    names_b0.extend(entry[0] for entry in mol_b0['slots'].values())
    names_b1 = [mol_b1['ligand'][0]]
    names_b1.extend(entry[0] for entry in mol_b1['slots'].values())
    sel_b2 = gamestart._active_molecule_selection(
        wiz_b._registry, wiz_b._molecule_index)
    target_b2 = set(sel_b2.split(' or '))
    check('B2 camera re-framed by the molecule advance (06-10 fix)',
          view_pre2 != view_b2
          and sel_b2 == ' or '.join(names_b1)
          and not any(n in target_b2 for n in names_b0),
          'zoom target has %d objects, %d of them molecule-1'
          % (len(target_b2),
             len([n for n in names_b1 if n in target_b2])))
except Exception:
    traceback.print_exc()
    check('B2 molecule advance', False, 'raised (see traceback above)')

# ============================================================
# PART B3+B6: LEVEL advance -- same instance, anchor untouched,
# scene rebuilt, camera re-framed
# ============================================================
try:
    view_pre = [float(v) for v in cmd.get_view()]
    ret2 = wiz_b.confirm_molecule()
    st = wiz_b.get_status()
    ev = st.get('last_event') or {}
    check('B3 level advance return contract',
          isinstance(ret2, dict) and ret2.get('advanced') == 'level',
          'advanced=%r'
          % (ret2.get('advanced') if isinstance(ret2, dict) else ret2,))
    check('B3 status: level 2 molecule 1',
          st.get('level_pos') == 2 and st.get('molecule_pos') == 1,
          'level_pos=%r molecule_pos=%r'
          % (st.get('level_pos'), st.get('molecule_pos')))
    check('B3 SAME wizard instance still stacked (D6 rebind)',
          cmd.get_wizard() is wiz_b, '')
    check('B3 timer anchor UNCHANGED by the level advance (D6)',
          engine.game_status().get('timer_anchor') == anchor0,
          'before=%r after=%r'
          % (anchor0, engine.game_status().get('timer_anchor')))
    registry_b = engine._registry
    expected_b = sum(1 + len(mol['slots'])
                     for mol in registry_b['molecules'])
    aam_b = [n for n in cmd.get_names('objects')
             if n.startswith('_aam_')]
    check('B3 fresh level-2 scene at the derived object count',
          registry_b.get('level_index') == 1
          and len(aam_b) == expected_b,
          'level_index=%r objects=%d expected=%d'
          % (registry_b.get('level_index'), len(aam_b), expected_b))
    check('B3 selection + result cleared through the rebind',
          st.get('selected') is None and st.get('result') is None,
          'selected=%r result=%r'
          % (st.get('selected'), st.get('result')))
    check('B3 marker: seq 2, completed level-1 final molecule (pos 2)',
          ev.get('kind') == 'molecule_scored' and ev.get('seq') == 2
          and ev.get('molecule_pos') == 2
          and ev.get('molecule_total') == 2,
          'kind=%r seq=%r pos=%r'
          % (ev.get('kind'), ev.get('seq'), ev.get('molecule_pos')))
    view_post = [float(v) for v in cmd.get_view()]
    check('B6 camera re-framed by the level advance (compose ran)',
          view_pre != view_post,
          'pre=%s...' % (['%.3f' % v for v in view_pre[:3]],))
except Exception:
    traceback.print_exc()
    check('B3 level advance', False, 'raised (see traceback above)')

# ============================================================
# PART B4: rebind proof -- a pick on the NEW molecule resolves
# ============================================================
try:
    mol_b = engine._registry['molecules'][0]
    slot_b = sorted(mol_b['slots'])
    slot0 = slot_b[0] if slot_b else None
    obj0 = mol_b['slots'][slot0][0] if slot0 is not None else None
    cmd.select('sele', '%s and name CA' % obj0)
    wiz_b.do_select('sele')
    st = wiz_b.get_status()
    check('B4 scripted pick resolves a slot via the rebuilt maps',
          isinstance(st.get('selected'), dict)
          and st['selected'].get('slot_id') == slot0,
          'slot_id=%r (object %r)' % (slot0, obj0))
except Exception:
    traceback.print_exc()
    check('B4 pick drive', False, 'raised (see traceback above)')

# ============================================================
# PART B5: completion drive -- four confirms close the game
# ============================================================
try:
    got = []
    for _ in range(3):
        r_mid = wiz_b.confirm_molecule()
        got.append(r_mid.get('advanced')
                   if isinstance(r_mid, dict) else r_mid)
    final = wiz_b.confirm_molecule()
    check('B5 intermediate advances walk molecule -> level -> molecule',
          got == ['molecule', 'level', 'molecule'],
          'advanced=%r' % (got,))
    check('B5 final confirm: advanced None, game_over, summary keys',
          isinstance(final, dict) and final.get('advanced') is None
          and final.get('game_over') is True
          and isinstance(final.get('summary'), dict)
          and sorted(final['summary']) == sorted(_SUMMARY_KEYS),
          'advanced=%r game_over=%r keys=%s'
          % (final.get('advanced') if isinstance(final, dict)
             else final,
             final.get('game_over') if isinstance(final, dict)
             else None,
             sorted(final.get('summary') or {})
             if isinstance(final, dict) else type(final)))
    st = wiz_b.get_status()
    check('B5 status mirrors the completed end state',
          st.get('game_over') is True
          and st.get('end_state') == 'completed',
          'game_over=%r end_state=%r'
          % (st.get('game_over'), st.get('end_state')))
    check('B5 engine agrees: is_over True, summary completed',
          engine.is_over() is True
          and isinstance(final, dict)
          and (final.get('summary') or {}).get('end_state')
          == 'completed'
          and (final.get('summary') or {})
          .get('molecules_completed') == 6
          and (final.get('summary') or {}).get('molecules') == 6,
          'is_over=%r completed=%r of %r'
          % (engine.is_over(),
             (final.get('summary') or {}).get('molecules_completed')
             if isinstance(final, dict) else None,
             (final.get('summary') or {}).get('molecules')
             if isinstance(final, dict) else None))
except Exception:
    traceback.print_exc()
    check('B5 completion drive', False, 'raised (see traceback above)')

# ============================================================
# PART B6: restore -- scene back to the baseline EXACTLY
# ============================================================
try:
    if cmd.get_wizard() is not None:
        cmd.set_wizard()
    cleaned = placement.cleanup_game_objects()
    check('B6 teardown returns the scene to the baseline EXACTLY',
          list(cmd.get_names('objects')) == pre_names,
          'deleted=%d post=%s' % (cleaned['deleted'],
                                  cmd.get_names('objects')))
    gamestart._last_start = None
except Exception:
    traceback.print_exc()
    check('B6 teardown', False, 'raised (see traceback above)')
    placement.cleanup_game_objects()

# ============================================================
# PART C (06-06): wizard skip / give-up / game-over gating /
# game_reset marker -- through the wizard's PUBLIC methods.
# ============================================================
part_b_checks = REC['checks']

# ============================================================
# PART C1: skip advances EXACTLY like Confirm (shared site)
# ============================================================
wiz_c = None
try:
    wiz_c = gamestart.start_game(activate=True)
    check('C1 fresh start returns the stacked GameWizard',
          isinstance(wiz_c, GameWizard) and cmd.get_wizard() is wiz_c,
          'type=%r' % (type(wiz_c),))
    r_conf = wiz_c.confirm_molecule()
    check('C1 confirm on molecule 1 advances molecule',
          isinstance(r_conf, dict) and r_conf.get('advanced')
          == 'molecule',
          'advanced=%r'
          % (r_conf.get('advanced') if isinstance(r_conf, dict)
             else r_conf,))
    r_skip = wiz_c.skip_molecule()
    gs = engine.game_status()
    st = wiz_c.get_status()
    ev = st.get('last_event') or {}
    check('C1 skip return contract (same shape as confirm)',
          isinstance(r_skip, dict) and r_skip.get('advanced') == 'level'
          and isinstance(r_skip.get('score'), float)
          and isinstance(r_skip.get('total'), float)
          and r_skip.get('game_over') is False
          and r_skip.get('summary') is None,
          'advanced=%r score=%r total=%r'
          % (r_skip.get('advanced') if isinstance(r_skip, dict)
             else r_skip,
             r_skip.get('score') if isinstance(r_skip, dict) else None,
             r_skip.get('total') if isinstance(r_skip, dict) else None))
    check('C1 skip recorded via the same path + counted',
          gs.get('skip_count') == 1
          and len(gs.get('molecule_scores') or []) == 2,
          'skip=%d scores=%r'
          % (gs.get('skip_count'), gs.get('molecule_scores')))
    check('C1 marker molecule_skipped pos 2 of 2 (seq 2)',
          ev.get('kind') == 'molecule_skipped' and ev.get('seq') == 2
          and ev.get('molecule_pos') == 2
          and ev.get('molecule_total') == 2
          and isinstance(ev.get('score'), float)
          and isinstance(ev.get('total'), float),
          'kind=%r seq=%r pos=%r total=%r'
          % (ev.get('kind'), ev.get('seq'), ev.get('molecule_pos'),
             ev.get('molecule_total')))
    check('C1 skip advanced the level (status at level 2 mol 1)',
          st.get('level_pos') == 2 and st.get('molecule_pos') == 1,
          'level_pos=%r molecule_pos=%r'
          % (st.get('level_pos'), st.get('molecule_pos')))
except Exception:
    traceback.print_exc()
    check('C1 skip drive', False, 'raised (see traceback above)')

# ============================================================
# PART C2: skip-COMPLETES-the-game (last molecule, last level)
# ============================================================
try:
    got = []
    for _ in range(3):
        r_mid = wiz_c.confirm_molecule()
        got.append(r_mid.get('advanced')
                   if isinstance(r_mid, dict) else r_mid)
    r_final = wiz_c.skip_molecule()
    check('C2 confirms walk molecule -> level -> molecule',
          got == ['molecule', 'level', 'molecule'],
          'advanced=%r' % (got,))
    check('C2 skip on the LAST molecule completes the game',
          isinstance(r_final, dict) and r_final.get('advanced') is None
          and r_final.get('game_over') is True
          and (r_final.get('summary') or {}).get('end_state')
          == 'completed',
          'advanced=%r game_over=%r end_state=%r'
          % (r_final.get('advanced') if isinstance(r_final, dict)
             else r_final,
             r_final.get('game_over') if isinstance(r_final, dict)
             else None,
             (r_final.get('summary') or {}).get('end_state')
             if isinstance(r_final, dict) else None))
    st = wiz_c.get_status()
    check('C2 status/engine mirror the completion (skip_count 2)',
          st.get('game_over') is True
          and st.get('end_state') == 'completed'
          and engine.is_over() is True
          and engine.game_status().get('skip_count') == 2,
          'game_over=%r end_state=%r is_over=%r skip=%r'
          % (st.get('game_over'), st.get('end_state'),
             engine.is_over(), engine.game_status().get('skip_count')))
except Exception:
    traceback.print_exc()
    check('C2 completion drive', False, 'raised (see traceback above)')

# ============================================================
# PART C4 (data) + C3 (lockdown): give_up, then EVERY gate refuses
# ============================================================
wiz_c2 = None
try:
    wiz_c2 = gamestart.start_game(activate=True)
    mol_c = engine._registry['molecules'][0]
    slots_c = sorted(mol_c['slots'])
    obj_c0 = mol_c['slots'][slots_c[0]][0]
    cmd.select('sele', '%s and name CA' % obj_c0)
    wiz_c2.do_select('sele')
    centroid_pre = geometry.centroid_of(obj_c0)
    ret_g = wiz_c2.give_up()
    st = wiz_c2.get_status()
    gs = engine.game_status()
    ev = st.get('last_event') or {}
    check('C4 give_up return contract (endgame summary consumed)',
          isinstance(ret_g, dict) and ret_g.get('game_over') is True
          and isinstance(ret_g.get('summary'), dict)
          and sorted(ret_g['summary']) == sorted(_SUMMARY_KEYS)
          and ret_g.get('level_pos') == 1
          and ret_g.get('molecule_pos') == 1,
          'game_over=%r keys=%s'
          % (ret_g.get('game_over') if isinstance(ret_g, dict)
             else ret_g,
             sorted(ret_g.get('summary') or {})
             if isinstance(ret_g, dict) else type(ret_g)))
    check('C4 gave_up marker at the end position + status mirrors',
          ev.get('kind') == 'gave_up' and ev.get('level_pos') == 1
          and ev.get('molecule_pos') == 1
          and ev.get('molecule_total') == 2
          and isinstance(ev.get('total'), float)
          and st.get('game_over') is True
          and st.get('end_state') == 'gave_up',
          'kind=%r level=%r pos=%r end_state=%r'
          % (ev.get('kind'), ev.get('level_pos'),
             ev.get('molecule_pos'), st.get('end_state')))
    check('C4 engine books: giveup 1, gave_up, frozen final_time',
          gs.get('giveup_count') == 1
          and gs.get('end_state') == 'gave_up'
          and isinstance(gs.get('final_time'), float)
          and gs.get('final_time') >= 0.0,
          'giveup=%r end_state=%r final_time=%r'
          % (gs.get('giveup_count'), gs.get('end_state'),
             gs.get('final_time')))

    wiz_c2.nudge_cam(1, 0, 0)
    st = wiz_c2.get_status()
    centroid_post = geometry.centroid_of(obj_c0)
    dev_nudge = max(abs(centroid_post[i] - centroid_pre[i])
                    for i in range(3))
    check('C3 nudge refused with the pinned wording, pose UNCHANGED',
          st.get('error') == 'The game is over.' and dev_nudge < 1e-9,
          'error=%r dev=%g' % (st.get('error'), dev_nudge))
    wiz_c2.rotate_view(10.0)
    st = wiz_c2.get_status()
    centroid_post2 = geometry.centroid_of(obj_c0)
    dev_rot = max(abs(centroid_post2[i] - centroid_pre[i])
                  for i in range(3))
    check('C3 rotate refused with the pinned wording, pose UNCHANGED',
          st.get('error') == 'The game is over.' and dev_rot < 1e-9,
          'error=%r dev=%g' % (st.get('error'), dev_rot))
    r_hint = wiz_c2.hint()
    st = wiz_c2.get_status()
    check('C3 hint returns None with the pinned wording',
          r_hint is None and st.get('error') == 'The game is over.',
          'hint=%r error=%r' % (r_hint, st.get('error')))
    wiz_c2.reset_grid()
    st = wiz_c2.get_status()
    check('C3 reset refused with the pinned wording',
          st.get('error') == 'The game is over.',
          'error=%r' % (st.get('error'),))
    obj_c1 = mol_c['slots'][slots_c[1]][0]
    cmd.select('sele', '%s and name CA' % obj_c1)
    wiz_c2.do_select('sele')
    st = wiz_c2.get_status()
    sel = st.get('selected') or {}
    check('C3 scripted pick is a SOFT no-op (selection unchanged)',
          sel.get('slot_id') == slots_c[0]
          and st.get('error') == 'The game is over.',
          'selected=%r error=%r' % (sel.get('slot_id'),
                                    st.get('error')))
    r_skip_g = wiz_c2.skip_molecule()
    st = wiz_c2.get_status()
    check('C3 skip refused post-game-over (None through _guard)',
          r_skip_g is None and st.get('error') == 'The game is over.',
          'skip=%r error=%r' % (r_skip_g, st.get('error')))
    r_conf_g = wiz_c2.confirm_molecule()
    st = wiz_c2.get_status()
    check('C3 confirm refused post-game-over (None through _guard)',
          r_conf_g is None and st.get('error') == 'The game is over.',
          'confirm=%r error=%r' % (r_conf_g, st.get('error')))
except Exception:
    traceback.print_exc()
    check('C3/C4 give-up + lockdown drive', False,
          'raised (see traceback above)')

# ============================================================
# PART C5: reset marker + pose replay + NO GameState touch
# ============================================================
wiz_c3 = None
try:
    wiz_c3 = gamestart.start_game(activate=True)
    gs_before = engine.game_status()
    mol_d = engine._registry['molecules'][0]
    slots_d = sorted(mol_d['slots'])
    slot_d0 = slots_d[0]
    obj_d0 = mol_d['slots'][slot_d0][0]
    cmd.select('sele', '%s and name CA' % obj_d0)
    wiz_c3.do_select('sele')
    mol_payload = engine._payload['levels'][0]['molecules'][0]
    slot_payload = None
    for sp in mol_payload['grid']['slots']:
        if sp['slot_id'] == slot_d0:
            slot_payload = sp
            break
    offset = (mol_payload.get('placement') or {}).get(
        'offset', (0.0, 0.0, 0.0))
    target = placement.effective_position(
        slot_payload['grid_pose']['position'], offset)
    moved = (target[0] + 3.0, target[1] + 5.0, target[2] - 2.0)
    wiz_c3.move_to(moved)
    after_move = geometry.centroid_of(obj_d0)
    dev_move = max(abs(after_move[i] - target[i]) for i in range(3))
    check('C5 move_to genuinely displaced the AA (> 1 A off target)',
          dev_move > 1.0, 'dev=%g target=%r after=%r'
          % (dev_move, target, after_move))
    wiz_c3.reset_grid()
    st = wiz_c3.get_status()
    ev = st.get('last_event') or {}
    check('C5 reset stamps the game_reset marker',
          ev.get('kind') == 'game_reset'
          and isinstance(ev.get('seq'), int),
          'kind=%r seq=%r' % (ev.get('kind'), ev.get('seq')))
    after_reset = geometry.centroid_of(obj_d0)
    dev_reset = 0.0
    tol_reset = 0.0
    for i in range(3):
        dev_reset = max(dev_reset, abs(after_reset[i] - target[i]))
        tol_reset = max(tol_reset,
                        placement.POSE_TOLERANCE
                        + placement.FLOAT32_ULP_REL
                        * max(abs(after_reset[i]), abs(target[i])))
    check('C5 pose back at the effective_position target (float32 ulp)',
          dev_reset <= tol_reset,
          'dev=%g tol=%g target=%r after=%r'
          % (dev_reset, tol_reset, target, after_reset))
    gs_after = engine.game_status()
    check('C5 reset touches NO GameState (to_dict equality)',
          gs_after == gs_before,
          'changed=%s' % (sorted(k for k in gs_after
                                 if gs_after.get(k)
                                 != gs_before.get(k)),))
except Exception:
    traceback.print_exc()
    check('C5 reset-marker drive', False, 'raised (see traceback above)')

# ============================================================
# PART C6: restore -- scene back to the baseline EXACTLY
# ============================================================
try:
    if cmd.get_wizard() is not None:
        cmd.set_wizard()
    cleaned = placement.cleanup_game_objects()
    check('C6 teardown returns the scene to the baseline EXACTLY',
          list(cmd.get_names('objects')) == pre_names,
          'deleted=%d post=%s' % (cleaned['deleted'],
                                  cmd.get_names('objects')))
    gamestart._last_start = None
except Exception:
    traceback.print_exc()
    check('C6 teardown', False, 'raised (see traceback above)')
    placement.cleanup_game_objects()

# --- Verdict marker (the SOLE verdict carrier) -------------------------------
print('SMOKE-15 PART A: %d checks; PART B: %d checks; PART C: %d '
      'checks; TOTAL %d, %d failure(s)'
      % (part_a_checks, part_b_checks - part_a_checks,
         REC['checks'] - part_b_checks, REC['checks'], len(failures)),
      flush=True)
print('=== SMOKE-15 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
