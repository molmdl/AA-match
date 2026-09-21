"""Headless smoke 18 - THE checkpoint SAVE half E2E (plan 07-04).

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_18_save_checkpoint.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-18 PASS ==='.

SINGLE-RUN design (unlike SMOKE-17's two-run contract): capture ->
atomic zip -> member/sidecar/.pse verification all in one process, in
the plan's prescribed order (A, B, D/E-before-C-load -- the plan's PART
C is split into C (zip side, pre-load) and E (load side, post-D) per
its own ordering note "run PART D BEFORE PART C's cmd.load"):

  PART A (baseline + scenario): start_game() defaults (seed 42) ->
    scripted pick (SMOKE-07 recipe) -> baked move_to + rotate_axis ->
    hint() (non-trivial _color_store) -> skip_molecule() (real
    lifecycle state: 0.00 partial + skip_count 1 + advance to molecule
    2). NOTE (implemented semantics, 02-12 precedent): the skip's
    advance clears _current_slot via _rebind_maps, so the books'
    current_slot at capture is None -- the smoke asserts the books
    VERBATIM (data['wizard'] == wiz.snapshot_books()) plus the PART-A
    pick having selected the scripted slot.
  PART B (capture): capture_checkpoint_snapshot(elapsed=75.0) -> the
    COMPLETE sidecar dict, asserted field-by-field (game_state VERBATIM,
    level_spec IDENTITY embed, seed, candidates None, registry modulo
    tuple->list, wizard books VERBATIM).
  PART C (save + zip): save_checkpoint into
    tmp/smoke fixtures/aam_pse18/game.aamz -> file exists -> exact
    member set {game.pse, state.json} -> no temp leftovers ->
    read_checkpoint_zip round-trips EVERY parsed component through the
    REAL gates (read_checkpoint_zip returns PARSED components
    {'setup','payload',...}, not the raw sidecar dict -- field-wise
    equality is the full round-trip).
  PART D (post-save integrity): engine.game_status() unchanged,
    wizard still the live top-of-stack one, _payload untouched --
    Save never ends the game (07-RESEARCH-import.md S3-6).
  PART E (load + restore): the extracted .pse loads IN-PROCESS ->
    the restored top-of-stack is a GameWizard (07-01 __reduce__ through
    the REAL pickle path) with books == the captured sidecar block, and
    the game objects returned under their saved names.

Restore block: wizard pop -> prefix cleanup -> gamestart._last_start =
None (SMOKE-08 store hygiene) -> best-effort fixture/temp rmtree.

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_18_save_checkpoint.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

import aamatch  # noqa: E402
from aamatch import checkpoint, engine, gamestart, geometry, placement  # noqa: E402
from aamatch.wizard import GameWizard  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

FIXTURE_DIR = os.path.join(_ROOT, 'tmp', 'smoke fixtures', 'aam_pse18')
ZIP_PATH = os.path.join(FIXTURE_DIR, 'game.aamz')

failures = []
REC = {}
COUNTS = {}
_PART = ['?']


def check(name, cond, detail=''):
    print('SMOKE-18 %-46s %s %s' % (name, 'PASS' if cond else 'FAIL',
                                    detail), flush=True)
    COUNTS[_PART[0]] = COUNTS.get(_PART[0], 0) + 1
    if not cond:
        failures.append(name)


def _restore():
    """Baseline restore: wizard pop -> prefix cleanup -> _last_start
    reset -> best-effort fixture rmtree (SMOKE-08 hygiene shape)."""
    try:
        if cmd.get_wizard() is not None:
            cmd.set_wizard()
    except Exception:
        pass
    try:
        placement.cleanup_game_objects()
    except Exception:
        pass
    gamestart._last_start = None
    try:
        import shutil as _sh
        _sh.rmtree(FIXTURE_DIR)
    except Exception:
        pass


try:
    # ==============================================================
    # PART A (baseline + scenario)
    # ==============================================================
    _PART[0] = 'A'
    for stale in (ZIP_PATH,):
        if os.path.exists(stale):
            os.remove(stale)
    pre_names = list(cmd.get_names('objects'))
    check('A clean pre-start scene',
          not geometry.game_object_names(),
          'pre game objects=%s' % (geometry.game_object_names(),))

    wiz = gamestart.start_game()              # seed 42 defaults, ACTIVE
    check('A start_game returns a GameWizard',
          isinstance(wiz, GameWizard), 'type=%r' % (type(wiz),))
    check('A wizard is top-of-stack', cmd.get_wizard() is wiz,
          'get_wizard()=%r' % (cmd.get_wizard(),))

    slots = sorted(wiz._registry['molecules'][0]['slots'])
    slot_id = slots[0]
    obj = wiz._registry['molecules'][0]['slots'][slot_id][0]
    cmd.select('sele', '%s and name CA' % obj)
    wiz.do_select('sele')
    cmd.deselect()
    check('A scripted pick selected slot %s' % (slot_id,),
          wiz._current_slot == slot_id,
          'current=%r want %r' % (wiz._current_slot, slot_id))

    cen = geometry.centroid_of(obj)
    wiz.move_to((cen[0] + 2.5, cen[1] + 1.25, cen[2] - 0.75))
    wiz.rotate_axis((0.0, 0.0, 1.0), 30.0)
    try:
        wiz._assert_identity(obj)
        ident_ok = True
    except Exception as exc:
        ident_ok = False
        print('SMOKE-18 identity-assert detail: %s' % (exc,), flush=True)
    check('A moved AA keeps the identity object matrix', ident_ok,
          'baked-transform invariant (post move_to + rotate)')

    hint_result = wiz.hint()
    check('A hint() recolored candidates (non-trivial books)',
          bool(hint_result) and hint_result['count'] > 0
          and bool(wiz._color_store),
          'hint=%r store_objects=%d'
          % (hint_result, len(wiz._color_store)))

    skip_result = wiz.skip_molecule()
    gs_after_skip = engine.game_status()
    check('A skip_molecule recorded a partial + advanced',
          bool(skip_result)
          and bool(gs_after_skip['score_per_molecule'])
          and gs_after_skip['skip_count'] == 1
          and gs_after_skip['current_molecule_index'] == 1,
          'scores=%s skip_count=%r mol_index=%r'
          % (sorted(gs_after_skip['score_per_molecule']),
             gs_after_skip['skip_count'],
             gs_after_skip['current_molecule_index']))
    check('A skip advance cleared the selection (rebind semantics)',
          wiz._current_slot is None,
          'current_slot=%r -- the advance rebind resets it; the books '
          'at capture carry None' % (wiz._current_slot,))

    # ==============================================================
    # PART B (capture)
    # ==============================================================
    _PART[0] = 'B'
    data = gamestart.capture_checkpoint_snapshot(elapsed=75.0)
    check('B capture returned the full checkpoint data dict',
          isinstance(data, dict)
          and sorted(data.keys()) == [
              'candidates', 'checkpoint_format_version', 'created_at',
              'elapsed_at_save', 'game', 'game_state', 'generator',
              'registry', 'wizard'],
          'keys=%s' % (sorted(data.keys()),))
    check('B game_state block == engine.game_status() (VERBATIM)',
          data['game_state'] == engine.game_status(), '')
    check("B elapsed_at_save == the caller-passed 75.0 (VERBATIM)",
          data['elapsed_at_save'] == 75.0, '%r' % (data['elapsed_at_save'],))
    check("B embedded level_spec IS engine._payload (identity embed)",
          data['game']['level_spec'] is engine._payload,
          'embed-don\'t-regenerate law')
    check("B embedded game seed == 42",
          data['game']['seed'] == 42, '%r' % (data['game']['seed'],))
    check("B candidates is None (demo game)",
          data['candidates'] is None, '')
    check("B registry level_index == 0",
          data['registry']['level_index'] == 0,
          '%r' % (data['registry']['level_index'],))
    want_reg = {'level_index': int(engine._registry['level_index']),
                'molecules': []}
    for row in engine._registry['molecules']:
        want_reg['molecules'].append({
            'molecule_id': row['molecule_id'],
            'offset': [float(x) for x in row['offset']],
            'ligand': [row['ligand'][0],
                       [int(i) for i in row['ligand'][1]]],
            'slots': dict(
                (sid, [entry[0], [int(i) for i in entry[1]]])
                for sid, entry in row['slots'].items()),
        })
    check('B registry rows == engine._registry modulo tuple->list',
          data['registry'] == want_reg,
          'molecules=%d (identity-only: no pre_game_names)'
          % (len(want_reg['molecules']),))
    books = wiz.snapshot_books()
    check('B wizard block == wiz.snapshot_books() (VERBATIM)',
          data['wizard'] == books,
          'keys=%s' % (sorted(data['wizard']),))
    check('B wizard color_store non-trivial (hint + pick landed)',
          bool(data['wizard']['color_store']),
          'store_objects=%d' % (len(data['wizard']['color_store']),))

    # ==============================================================
    # PART C (save + zip side; NO load yet)
    # ==============================================================
    _PART[0] = 'C'
    if not os.path.exists(FIXTURE_DIR):
        os.makedirs(FIXTURE_DIR)
    final = gamestart.save_checkpoint(ZIP_PATH, data)
    check('C save_checkpoint returned the final path',
          isinstance(final, str) and os.path.exists(final),
          'final=%s' % (final,))
    import zipfile as _zipfile
    with _zipfile.ZipFile(final, 'r') as zf:
        member_names = sorted(zf.namelist())
    check('C archive members exactly {game.pse, state.json}',
          member_names == [checkpoint.PSE_MEMBER,
                           checkpoint.SIDECAR_MEMBER],
          'members=%s' % (member_names,))
    leftovers = sorted(n for n in os.listdir(FIXTURE_DIR)
                       if n != 'game.aamz')
    check('C no temp leftovers beside the archive', not leftovers,
          'atomic write + temp .pse unlink; dir=%s' % (leftovers,))
    pse_path, data2 = checkpoint.read_checkpoint_zip(final)
    check('C sidecar re-reads through ALL REAL parse gates',
          isinstance(data2, dict), '')
    roundtrip_ok = (
        data2['setup'] == data['game']['setup']
        and data2['payload'] == data['game']['level_spec']
        and data2['game_state'] == data['game_state']
        and data2['elapsed_at_save'] == data['elapsed_at_save']
        and data2['registry'] == data['registry']
        and data2['wizard'] == data['wizard']
        and data2['candidates'] == data['candidates']
        and data2['ligand_texts'] == {})
    check('C parsed components round-trip EVERY sidecar block',
          roundtrip_ok,
          'mismatch=%s'
          % ([k for k in ('setup', 'payload', 'game_state',
                          'elapsed_at_save', 'registry', 'wizard',
                          'candidates')
              if (data2[k] != data['game']['setup'] if k == 'setup'
                  else data2[k] != data['game']['level_spec']
                  if k == 'payload' else data2[k] != data[k])]
             if not roundtrip_ok else [],))

    # ==============================================================
    # PART D (post-save integrity -- Save never ends the game)
    # ==============================================================
    _PART[0] = 'D'
    check('D engine.game_status() UNCHANGED by the save',
          engine.game_status() == data['game_state'],
          '07-RESEARCH-import.md S3-6')
    check('D wizard still the live top-of-stack one',
          cmd.get_wizard() is wiz,
          'get_wizard()=%r' % (cmd.get_wizard(),))
    check('D engine._payload still the embedded spec object',
          engine._payload is not None
          and engine._payload['seed'] == 42, '')

    # ==============================================================
    # PART E (load + restore through the REAL pickle path)
    # ==============================================================
    _PART[0] = 'E'
    expect_names = set()
    for row in data['registry']['molecules']:
        expect_names.add(row['ligand'][0])
        for entry in row['slots'].values():
            expect_names.add(entry[0])
    cmd.load(pse_path)          # temp path minted in-process (S3-3)
    restored = cmd.get_wizard()
    check('E restored top-of-stack is a GameWizard (REAL __reduce__)',
          isinstance(restored, GameWizard),
          'get_wizard()=%r -- the old defect dropped it (None)'
          % (restored,))
    if isinstance(restored, GameWizard):
        check('E restored wizard books == the captured sidecar block',
              restored.snapshot_books() == data['wizard'],
              'slot=%r seq=%r msm=%r store=%d'
              % (restored._current_slot, int(restored._event_seq),
                 restored._saved_msm, len(restored._color_store)))
    else:
        check('E restored wizard books == the captured sidecar block',
              False, 'no restored wizard to compare')
    loaded_game_names = set(geometry.game_object_names())
    check('E game objects returned under their saved names',
          loaded_game_names == expect_names,
          'loaded=%d want=%d missing=%s extra=%s'
          % (len(loaded_game_names), len(expect_names),
             sorted(expect_names - loaded_game_names),
             sorted(loaded_game_names - expect_names)))
    try:
        import shutil as _sh
        _sh.rmtree(os.path.dirname(pse_path))   # caller owns the temp
    except Exception:
        pass

    # ---- restore block + pre/post scene equality -------------------
    _PART[0] = 'Z'
    _restore()
    check('Z teardown restores the pre-start scene',
          list(cmd.get_names('objects')) == pre_names,
          'post=%s' % (cmd.get_names('objects'),))
    check('Z _last_start reset (SMOKE-08 store hygiene)',
          gamestart._last_start is None, '')
except Exception:
    traceback.print_exc()
    check('SMOKE-18 run', False, 'raised (see traceback above)')
    _restore()

# ======================================================================
# Verdict marker (the SOLE verdict carrier)
# ======================================================================
print('SMOKE-ENV record: %s'
      % dict((k, v) for k, v in sorted(REC.items())), flush=True)
print('SMOKE-18 check counts per part: %s'
      % dict((k, COUNTS[k]) for k in sorted(COUNTS)), flush=True)
print('=== SMOKE-18 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
