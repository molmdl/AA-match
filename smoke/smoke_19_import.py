"""Headless SMOKE-19 - the Import button wiring and the restart
payload-direct branch (plan 07-07, PERSIST-02 / SCORE-09 c2), T1b.

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_19_import.py 240
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-19 PASS ==='.

Proves (aamatch/game_window.py) headlessly in REAL PyMOL under the T1b
house recipe (the 04-01 probe verdict is PASS, platform=offscreen;
QApplication reuse-or-create). ZERO modals: the smoke drives the
NON-MODAL impl _import_game_from(path) DIRECTLY -- the _on_import
wrapper owns the QFileDialog and its box path is [HUMAN]-only (the
smoke-99 receipt: a static QMessageBox BLOCKS indefinitely under
offscreen). The game under drive is built from a REAL exported game
file (PART A) -- never a synthetic payload hand-feed.

PART A  (fixtures, tmp/smoke fixtures/aam_pse19/):
        A1 the fixture dir is prepared clean.
        A2 a REAL game file is built end-to-end through the engine:
           gamestart.start_game(seed=4242, activate=False) -> the live
           engine._payload -> game_file.make_game_data(setup, payload,
           None, created_at) -> persistence.save_container(path,
           'game', data) (the SMOKE-11 PART F2 consumer-contract
           shape). Saved on disk.
        A3 the written file round-trips: parse_game_data(
           read_json_file) -> payload seed 4242, ligand_texts {} --
           the exact five-gate contract Import consumes (04-12).
        A4 the EIGHT refusal fixtures are written: a foreign-magic
           JSON, a container with version 99, a misfiled-kind
           ('setup') container, a JSON syntax error, a game container
           with game_format_version 99, a payload re-stamped
           'det-0' (the 02-15 stale-detector template), a tampered
           ligand_files row (sha256 mismatch over record text), and
           an upload-sourced payload with NO embedded content.

PART B  (import E2E via the tab impl, T1b):
        B1 construction - a FRESH standalone GameTab shows btn_import
           ('Import', non-empty tooltip) AFTER btn_save_game; the row
           is Hint/Confirm/Skip-GiveUp/Restart/Reset/Save/Import and
           the stretch stays LAST (the 05-06 OQ-1 no-reflow law).
        B2 import with NO wizard live (gate-free): the drive returns
           True, the pending wizard is armed and NOT on the stack
           (P-1), the info box is ['Get ready...', 'Game imported:
           <path>.'] in that order (D7: the line logs AFTER the arm),
           engine._payload IS the embedded payload object identity
           (the seam stores BY IDENTITY), the GameState is fresh
           zeros, _last_start carries the 5-key shape with 'payload'
           by identity (07-05).
        B3 GO: the counted-down import pushes THAT wizard, anchors the
           timer from ZERO (float near now), the derived generation
           count holds, detect() on-grid -> 0 records, the required
           label renders.
        B4 accrue state + stamp: one _confirm_now score record + the
           SMOKE-08/16 instance marker band over the generation.
        B5 mid-game import (replacement): a second import drive REPLACES
           the running game exactly like Start -- marker survivors 0
           (old generation dead), exactly one fresh generation, the
           running wizard POPPED before the arm (P-3), a NEW pending
           wizard armed, the imported line last again (D7), fresh
           zeros (the accrued score cannot survive).
        B6 GO on the second import: fresh game again (zeros, float
           anchor near zero).

PART C  (restart payload branch - the c2 decision):
        C1 the imported game is live; engine._payload identity P is
           captured WITH the names/ids structural fingerprint
           (extract_game_atoms (object, id) pairs) and the scene names.
        C2 _restart_now() returns True; box == ['Get ready...',
           'Game restarted.'] (D7); pending armed, not stacked.
        C3 BRANCH-TAKEN proof: after the replay, engine._payload IS P
           (the SAME object by identity -- a legacy start_game replay
           would have REGENERATED a new payload object) and
           _last_start['payload'] IS P.
        C4 GO: fresh zeros again; the names/ids fingerprint is EQUAL
           to the pre-restart fingerprint (regenerated-equivalent scene
           from the SAME payload); marker survivors 0 with one fresh
           generation.

PART D  (refusal battery - every gate surfaces verbatim, parse-first
        law): with the imported game LIVE, each fixture is driven
        through tab._import_game_from and must RAISE (the impl raises;
        _guard boxes are wrapper-side [HUMAN]) with the EXACT house
        message class: foreign ('not an AA-match file (...)' exact),
        newer container ('unsupported AA-match format version 99 ...'
        exact), misfiled kind ('expected an AA-match game file,
        found kind=' exact), unparseable JSON ('could not parse
        AA-match JSON: ' prefix -- the JSON detail text is
        implementation-versioned), wrong game_format_version (exact),
        stale detector stamp (exact, both directions named), sha256
        mismatch (exact with the computed digest), upload-without-
        content (exact, naming the molecule + key). After EVERY
        refusal the scene fingerprint is bit-UNTOUCHED, the log is
        unchanged, the live wizard is still on the stack, and
        engine._payload identity + game_status are unchanged (parse
        gates run BEFORE any scene touch).

Restore: cancel the pending countdown -> stop the 1 Hz timer -> done
pop -> prefix cleanup -> gamestart._last_start = None -> best-effort
fixture rmtree (the SMOKE-08/16 hygiene shape); every part tears down
after itself so a mid-part failure leaves a recoverable scene.

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv
first / cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch'); every print on ONE line and flushed; check
details built from already-known data only (the 03-04 eager-detail
lesson); NEVER pump processEvents between start_countdown and the
tick drive (the 05-RESEARCH anti-flakiness strategy).

Python floor: runs inside PyMOL's Windows Python (3.9); written
3.6-safe.
"""
import base64
import copy
import hashlib
import json
import os
import sys
import time
import traceback

# QT_QPA_PLATFORM MUST be set BEFORE any pymol.Qt import (the offscreen
# recipe the 04-01 probe proved; aamatch.game_window carries a
# module-level pymol.Qt import).
os.environ['QT_QPA_PLATFORM'] = 'offscreen'


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_19_import.py'
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
from aamatch import engine, gamestart, geometry, paths  # noqa: E402
from aamatch import persistence, placement  # noqa: E402
from aamatch import game_file, status_text  # noqa: E402
from aamatch.level_spec import DETECTOR_VERSION  # noqa: E402
from aamatch.wizard import GameWizard  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

FIXTURE_DIR = os.path.join(_ROOT, 'tmp', 'smoke fixtures', 'aam_pse19')
GAME_PATH = os.path.join(FIXTURE_DIR, 'import_seed4242.aamatch.json')
FX_FOREIGN = os.path.join(FIXTURE_DIR, 'fx_foreign.json')
FX_NEWER = os.path.join(FIXTURE_DIR, 'fx_newer_container.json')
FX_MISFILED = os.path.join(FIXTURE_DIR, 'fx_misfiled_kind.json')
FX_JSON = os.path.join(FIXTURE_DIR, 'fx_unparseable.json')
FX_GAMEVER = os.path.join(FIXTURE_DIR, 'fx_game_version_99.json')
FX_DET0 = os.path.join(FIXTURE_DIR, 'fx_detector_det0.json')
FX_SHA = os.path.join(FIXTURE_DIR, 'fx_sha_mismatch.json')
FX_NOCONTENT = os.path.join(FIXTURE_DIR, 'fx_upload_no_content.json')

failures = []
COUNTS = {}
_PART = ['?']


def check(name, cond, detail=''):
    COUNTS[_PART[0]] = COUNTS.get(_PART[0], 0) + 1
    print('SMOKE-19 %-46s %s %s' % (name, 'PASS' if cond else 'FAIL',
                                    detail), flush=True)
    if not cond:
        failures.append(name)


# The SMOKE-08 :146-162 instance marker band (03-05 law): same-payload
# restarts/imports REBUILD the same _aam_* names, so NAME-set equality
# can never prove the old generation is gone; stamp the live
# generation's b-factor instead (game sentinels sit at b=-999.0,
# outside the band).
MARK_LOW_B, MARK_HIGH_B = -2.0, -0.5


def _game_objects():
    """Sorted live scene objects carrying the reserved game prefix."""
    return sorted(n for n in cmd.get_names('objects')
                  if n.startswith(geometry.GAME_PREFIX))


def _stamp_band(objects):
    """Write the marker band onto every atom of ``objects``."""
    for name in objects:
        cmd.alter(name, 'b=-1.0', space={})


def _marked_atoms():
    """Atoms currently carrying the generation marker (0 post-clean)."""
    return cmd.count_atoms('b > %f and b < %f'
                           % (MARK_LOW_B, MARK_HIGH_B))


def _fingerprint():
    """The (object, atom-id) structural identity of the live game
    scene -- names AND ids equal proves a regenerated-equivalent scene
    from the SAME payload (extract_game_atoms is sorted (object, id)
    by the 02-09 detector contract)."""
    return [(str(r['object']), int(r['id']))
            for r in geometry.extract_game_atoms()]


def _expected_count(wiz):
    """Whole-scene game-object count derived from a wizard's registry
    + difficulty spec (1 + n*n per molecule) -- never hard-coded."""
    n = int(wiz._payload['levels'][0]['difficulty']['grid_n'])
    return len(wiz._registry['molecules']) * (1 + n * n)


def _write_json(path, obj):
    """Best-effort plain fixture write (fixtures only -- persistence's
    atomic writer is the production path's own contract)."""
    with open(path, 'w') as fh:
        fh.write(json.dumps(obj, indent=2, sort_keys=True))


def _write_text(path, text):
    with open(path, 'w') as fh:
        fh.write(text)


def _restore(tab=None):
    """Baseline restore: cancel -> stop tick -> done pop -> prefix
    cleanup -> _last_start reset -> best-effort fixture rmtree."""
    try:
        if tab is not None:
            tab.cancel_pending_start()
            tab._timer.stop()
    except Exception:
        pass
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


tab = None
try:
    # ==============================================================
    # PART A (fixtures): a REAL exported game file + the refusal set
    # ==============================================================
    _PART[0] = 'A'
    if os.path.isdir(FIXTURE_DIR):
        import shutil as _sh0
        _sh0.rmtree(FIXTURE_DIR)
    os.makedirs(FIXTURE_DIR)
    check('A1: fixture dir prepared clean', os.path.isdir(FIXTURE_DIR),
          'dir=%r' % (FIXTURE_DIR,))

    # A real payload through the engine (the SMOKE-11 PART F2 shape).
    gamestart.start_game(seed=4242, activate=False)
    fx_setup = copy.deepcopy(gamestart._last_start['setup'])
    fx_payload = engine._payload
    fx_data = game_file.make_game_data(
        fx_setup, fx_payload, None,
        created_at=time.strftime('%Y-%m-%dT%H:%M:%S'))
    persistence.save_container(GAME_PATH, 'game', fx_data)
    check('A2: real game file built through engine._payload and saved',
          os.path.exists(GAME_PATH), 'path=%r' % (GAME_PATH,))

    reparsed = game_file.parse_game_data(
        persistence.read_json_file(paths.to_windows_path(GAME_PATH)))
    check('A3: written file round-trips the five-gate consumer chain '
          '(payload seed 4242, demo embeds NOTHING)',
          reparsed['payload'] == json.loads(
              json.dumps(fx_data['level_spec']))
          and reparsed['payload']['seed'] == 4242
          and reparsed['ligand_texts'] == {},
          'seed=%r ligand_keys=%r'
          % (reparsed['payload']['seed'],
             sorted(reparsed['ligand_texts'])))
    placement.cleanup_game_objects()
    gamestart._last_start = None

    # -- the eight refusal fixtures --------------------------------
    ls_data = copy.deepcopy(fx_data['level_spec'])
    _write_json(FX_FOREIGN,
                {'magic': 'OTHER', 'version': 1, 'kind': 'game',
                 'data': {}})
    _write_json(FX_NEWER,
                {'magic': 'AAMATCH', 'version': 99, 'kind': 'game',
                 'data': {}})
    _write_json(FX_MISFILED,
                {'magic': 'AAMATCH', 'version': 1, 'kind': 'setup',
                 'data': {}})
    _write_text(FX_JSON, '{"magic": "AAMATCH", "version": 1, broken')
    gv = copy.deepcopy(fx_data)
    gv['game_format_version'] = 99
    _write_json(FX_GAMEVER,
                {'magic': 'AAMATCH', 'version': 1, 'kind': 'game',
                 'data': gv})
    det = copy.deepcopy(fx_data)
    det['level_spec']['detector_version'] = 'det-0'
    _write_json(FX_DET0,
                {'magic': 'AAMATCH', 'version': 1, 'kind': 'game',
                 'data': det})
    lig0 = ls_data['levels'][0]['molecules'][0]['ligand']
    sha = copy.deepcopy(fx_data)
    sha['level_spec']['levels'][0]['molecules'][0]['ligand'][
        'source'] = 'upload'
    tamper_text = ('tampered record text -- NOT the exported molecule')
    sha['ligand_files'] = {
        lig0['file']: base64.b64encode(
            tamper_text.encode('utf-8')).decode('ascii')}
    _write_json(FX_SHA,
                {'magic': 'AAMATCH', 'version': 1, 'kind': 'game',
                 'data': sha})
    nocont = copy.deepcopy(fx_data)
    for _m in nocont['level_spec']['levels'][0]['molecules']:
        _m['ligand']['source'] = 'upload'
    nocont['ligand_files'] = {}
    _write_json(FX_NOCONTENT,
                {'magic': 'AAMATCH', 'version': 1, 'kind': 'game',
                 'data': nocont})
    check('A4: the eight refusal fixtures written',
          all(os.path.exists(p) for p in
              (FX_FOREIGN, FX_NEWER, FX_MISFILED, FX_JSON, FX_GAMEVER,
               FX_DET0, FX_SHA, FX_NOCONTENT)), '')

    from pymol.Qt import QtWidgets
    from aamatch import game_window

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(['aamatch-smoke-19'])

    # ==============================================================
    # PART B: import E2E via the tab impl (T1b; ZERO modals)
    # ==============================================================
    _PART[0] = 'B'
    tab = game_window.GameTab(None)
    baseline_b = cmd.get_names('objects')

    # ---- B1: construction inventory --------------------------------
    btn_row_layout = None
    lay = tab.layout()
    for i in range(lay.count()):
        sub = lay.itemAt(i).layout()
        if sub is None:
            continue
        for j in range(sub.count()):
            if sub.itemAt(j).widget() is tab.btn_hint:
                btn_row_layout = sub
    row_ok = False
    if btn_row_layout is not None:
        ws = [btn_row_layout.itemAt(j).widget()
              for j in range(btn_row_layout.count())]
        last = btn_row_layout.itemAt(btn_row_layout.count() - 1)
        row_ok = (ws[:7] == [tab.btn_hint, tab.btn_confirm,
                             tab.btn_skip_menu, tab.btn_restart,
                             tab.btn_reset_grid, tab.btn_save_game,
                             tab.btn_import]
                  and ws[-1] is None
                  and last.spacerItem() is not None)
    check("B1: btn_import ('Import', non-empty tooltip) exists",
          tab.btn_import.text() == 'Import'
          and bool(tab.btn_import.toolTip()),
          'text=%r' % (tab.btn_import.text(),))
    check('B1: row order Hint/Confirm/Skip-GiveUp/Restart/Reset/Save/'
          'Import, stretch LAST', row_ok, '')

    # ---- B2: import with NO wizard live (gate-free) ------------------
    r_b2 = tab._import_game_from(GAME_PATH)
    wiz_b2 = tab._pending_wizard
    p_import_b2 = engine._payload
    ls_b2 = gamestart._last_start
    lines_b2 = tab._info_log.toPlainText().splitlines()
    check('B2: import with NO wizard live returns True; pending armed '
          'and NOT on the stack (gate-free + P-1)',
          r_b2 is True
          and isinstance(wiz_b2, GameWizard)
          and cmd.get_wizard() is None,
          'pending=%r top=%r' % (wiz_b2, cmd.get_wizard()))
    check("B2: info box == ['Get ready...', 'Game imported: <path>.'] "
          '(D7: the line logs AFTER the arm)',
          lines_b2 == ['Get ready...',
                       status_text.game_imported_line(GAME_PATH)],
          'lines=%r' % (lines_b2,))
    check('B2: engine._payload IS the embedded payload content (the '
          'seam stores BY IDENTITY into _last_start)',
          isinstance(ls_b2, dict)
          and ls_b2.get('payload') is p_import_b2
          and p_import_b2 == reparsed['payload'],
          'ls_keys=%r' % (sorted(ls_b2) if ls_b2 else ls_b2,))
    gs_b2 = engine.game_status()
    check('B2: fresh GameState zeros pre-GO (no scores/counters, '
          'timer unanchored)',
          len(gs_b2.get('molecule_scores') or []) == 0
          and gs_b2.get('skip_count') == 0
          and gs_b2.get('giveup_count') == 0
          and gs_b2.get('game_over') is False
          and engine._current_game().timer_anchor is None,
          'anchor=%r' % (engine._current_game().timer_anchor,))

    # ---- B3: GO on the import --------------------------------------
    for _ in range(4):
        tab._countdown_tick()
    anchor_b3 = engine._current_game().timer_anchor
    check('B3: GO pushed THAT import wizard; timer anchored from ZERO '
          '(float near now); 1 Hz running',
          cmd.get_wizard() is wiz_b2
          and isinstance(anchor_b3, float)
          and 0.0 <= (time.time() - anchor_b3) < 60.0
          and tab._timer.isActive(),
          'anchor=%r' % (anchor_b3,))
    check('B3: exactly one fresh generation (derived count); detect() '
          'on-grid -> 0 records',
          len(_game_objects()) == _expected_count(wiz_b2)
          and len(engine.detect()) == 0,
          'objects=%d expect=%d'
          % (len(_game_objects()), _expected_count(wiz_b2)))
    check('B3: required label rendered from the embedded payload',
          tab._required_label.text() != 'Required: -',
          'label=%r' % (tab._required_label.text(),))

    # ---- B4: accrue state + stamp the generation -------------------
    conf_b4 = tab._confirm_now()
    gen_b4 = _game_objects()
    _stamp_band(gen_b4)
    check('B4: a score recorded pre-import; marker band stamped on '
          'the whole generation',
          isinstance(conf_b4, dict)
          and len(engine.game_status().get('molecule_scores')
                  or []) == 1
          and _marked_atoms() > 0
          and len(gen_b4) == _expected_count(wiz_b2),
          'marked=%d' % (_marked_atoms(),))

    # ---- B5: mid-game import REPLACES the running game -------------
    r_b5 = tab._import_game_from(GAME_PATH)
    wiz_b5 = tab._pending_wizard
    lines_b5 = tab._info_log.toPlainText().splitlines()
    check('B5: mid-game import returns True; the running wizard is '
          'POPPED (P-3) and a NEW pending wizard armed',
          r_b5 is True
          and isinstance(wiz_b5, GameWizard)
          and wiz_b5 is not wiz_b2
          and cmd.get_wizard() is None,
          'top=%r' % (cmd.get_wizard(),))
    check('B5: marker-band survivors 0 (old generation dead) + exactly '
          'one fresh generation (derived count)',
          _marked_atoms() == 0
          and len(_game_objects()) == _expected_count(wiz_b5),
          'marked=%d objects=%d'
          % (_marked_atoms(), len(_game_objects())))
    gs_b5 = engine.game_status()
    check('B5: fresh zeros again (the accrued score cannot survive) + '
          'the imported line last (D7)',
          len(gs_b5.get('molecule_scores') or []) == 0
          and lines_b5 == ['Get ready...',
                           status_text.game_imported_line(GAME_PATH)],
          'scores=%r' % (gs_b5.get('molecule_scores'),))

    # ---- B6: GO on the second import -------------------------------
    for _ in range(4):
        tab._countdown_tick()
    gs_b6 = engine.game_status()
    anchor_b6 = engine._current_game().timer_anchor
    check('B6: GO on the second import: fresh game (zeros, float '
          'anchor near zero)',
          cmd.get_wizard() is wiz_b5
          and isinstance(anchor_b6, float)
          and 0.0 <= (time.time() - anchor_b6) < 60.0
          and len(gs_b6.get('molecule_scores') or []) == 0
          and gs_b6.get('game_over') is False,
          'anchor=%r' % (anchor_b6,))

    # ==============================================================
    # PART C: the Restart payload-direct branch (the c2 decision)
    # ==============================================================
    _PART[0] = 'C'
    # C1: live imported game; capture payload identity + fingerprint.
    gen_c = _game_objects()
    _stamp_band(gen_c)
    p_live_c = engine._payload
    fp_pre_c = _fingerprint()
    names_pre_c = list(cmd.get_names('objects'))
    check('C1: imported game live; payload identity + names/ids '
          'fingerprint captured over the stamped generation',
          cmd.get_wizard() is wiz_b5
          and _marked_atoms() > 0
          and len(fp_pre_c) > 0,
          'atoms=%d' % (len(fp_pre_c),))

    # C2: the restart drive (arm + D7 line placement).
    r_c = tab._restart_now()
    pending_c = tab._pending_wizard
    lines_c = tab._info_log.toPlainText().splitlines()
    check('C2: _restart_now returns True; replay wizard armed and NOT '
          'on the stack; box == Get-ready + restarted (D7)',
          r_c is True
          and isinstance(pending_c, GameWizard)
          and cmd.get_wizard() is None
          and lines_c == ['Get ready...',
                          status_text.game_restarted_line()],
          'lines=%r' % (lines_c,))

    # C3: BRANCH-TAKEN proof -- payload-direct replay keeps engine
    # ._payload IDENTICAL BY OBJECT (a legacy start_game replay would
    # have REGENERATED a new payload object).
    check("C3: the payload branch was TAKEN -- engine._payload IS the "
          "pre-restart object (identity) and _last_start['payload'] "
          'IS it too',
          engine._payload is p_live_c
          and gamestart._last_start.get('payload') is p_live_c,
          'same_obj=%r' % (engine._payload is p_live_c,))

    # C4: GO -- fresh zeros; regenerated-equivalent scene (names AND
    # ids EQUAL) from the SAME payload; one fresh generation.
    for _ in range(4):
        tab._countdown_tick()
    gs_c = engine.game_status()
    fp_post_c = _fingerprint()
    check('C4: GO on the replay: fresh zeros (scores [], counters 0, '
          'anchor float near zero)',
          cmd.get_wizard() is pending_c
          and len(gs_c.get('molecule_scores') or []) == 0
          and gs_c.get('skip_count') == 0
          and gs_c.get('giveup_count') == 0
          and gs_c.get('game_over') is False
          and 0.0 <= (time.time()
                      - engine._current_game().timer_anchor) < 60.0,
          'anchor=%r' % (engine._current_game().timer_anchor,))
    check('C4: names/ids fingerprint EQUAL to pre-restart + marker '
          'survivors 0 + one fresh generation',
          fp_post_c == fp_pre_c
          and list(cmd.get_names('objects')) == names_pre_c
          and _marked_atoms() == 0
          and len(_game_objects()) == _expected_count(pending_c),
          'fp=%d marked=%d' % (len(fp_post_c), _marked_atoms()))

    # ==============================================================
    # PART D: the refusal battery (parse gates BEFORE any scene touch)
    # ==============================================================
    _PART[0] = 'D'
    key0 = lig0['file']
    tamper_digest = hashlib.sha256(
        tamper_text.encode('utf-8')).hexdigest()
    battery = [
        ('foreign-magic', FX_FOREIGN, 'exact',
         "not an AA-match file (magic='OTHER', expected 'AAMATCH')"),
        ('newer-container', FX_NEWER, 'exact',
         'unsupported AA-match format version 99 (expected <= 1). '
         'Please update AA-match.'),
        ('misfiled-kind', FX_MISFILED, 'exact',
         "expected an AA-match game file, found kind='setup'"),
        ('unparseable', FX_JSON, 'prefix',
         'could not parse AA-match JSON: '),
        ('game-version-99', FX_GAMEVER, 'exact',
         'unsupported game file version 99 (expected <= 1). '
         'Please update AA-match.'),
        ('stale-detector', FX_DET0, 'exact',
         "unsupported detector_version 'det-0' in level spec "
         "(expected %r): stale or newer game spec - regenerate it "
         'with a current AA-match generator' % (DETECTOR_VERSION,)),
        ('sha256-mismatch', FX_SHA, 'exact',
         'game file ligand content %r sha256 mismatch (embedded '
         'content hashes %s, payload records %s)'
         % (key0, tamper_digest, lig0['sha256'])),
        ('upload-no-content', FX_NOCONTENT, 'exact',
         'game file is missing embedded content for uploaded '
         'molecule %r (key %r)' % (lig0['entry_id'], key0)),
    ]
    for name, fxpath, mode, expected in battery:
        names_pre = list(cmd.get_names('objects'))
        fp_pre = _fingerprint()
        log_pre = tab._info_log.toPlainText()
        gs_pre = engine.game_status()
        p_pre = engine._payload
        exc_d = None
        try:
            tab._import_game_from(fxpath)
        except ValueError as exc_caught:
            exc_d = exc_caught
        msg_ok = exc_d is not None and (
            str(exc_d) == expected if mode == 'exact'
            else str(exc_d).startswith(expected))
        check('D: %s refuses with the exact house message' % name,
              msg_ok, 'err=%r' % (exc_d,))
        intact = (list(cmd.get_names('objects')) == names_pre
                  and _fingerprint() == fp_pre
                  and tab._info_log.toPlainText() == log_pre
                  and cmd.get_wizard() is pending_c
                  and engine._payload is p_pre
                  and engine.game_status() == gs_pre)
        check('D: %s leaves scene/log/stack/game EXACTLY untouched '
              '(parse-first law)' % name, intact, '')
except Exception:
    traceback.print_exc()
    check('%s drive' % _PART[0], False, 'raised (see traceback above)')
finally:
    try:
        _restore(tab)
        from pymol.Qt import QtWidgets as _QTW
        app2 = _QTW.QApplication.instance()
        if app2 is not None:
            app2.processEvents()
        if tab is not None:
            tab.close()
    except Exception:
        traceback.print_exc()

total = sum(COUNTS.values())
print('SMOKE-19 parts: %s' % ', '.join(
    '%s=%d' % (k, COUNTS[k]) for k in sorted(COUNTS)), flush=True)
print('SMOKE-19 checks: %d total, %d failed' % (total, len(failures)),
      flush=True)
if failures:
    print('SMOKE-19 FAILURES: %r' % (failures,), flush=True)
else:
    print('=== SMOKE-19 PASS ===', flush=True)
