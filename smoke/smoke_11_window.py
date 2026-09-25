"""Headless SMOKE-11 - the setup window shell (plan 04-05).

Run (from WSL, repo root):
    bash smoke/run_smoke.sh smoke/smoke_11_window.py 120
Verdict is carried by the printed marker (exit codes cannot carry
verdicts through the cmd.exe wrapper): grep '=== SMOKE-11 PASS ==='.

Proves the Phase-4 Qt-tier shell (aamatch/setup_window.py) in REAL
headless PyMOL to the extent the 04-01 probe allows. Probes the
menu-side wiring indirectly: run_plugin_gui now returns
setup_window.open_window()'s dialog, so the handles below are the
same objects the Plugins menu would surface.

PART A  (ALWAYS, T1a import tier): import aamatch.setup_window headless
        (the module-level pymol.Qt binding loads -- PyQt5
        QtCore/QtGui/QtWidgets imported as a unit via the wrapper shim,
        pymol-src/Qt/__init__.py:28); open_window is callable; the
        _window singleton starts None; source sanity: the module text
        contains 'from pymol.Qt import' and does NOT contain
        'from PyQt5' (the shim-only law), read via the repo-root anchor.
PART B  (T1b -- the 04-01 probe verdict is PASS (platform=offscreen),
        .planning/phases/04-qt-setup-window/04-01-SUMMARY.md, so the
        widget-construction parts RUN): QApplication reuse-or-create;
        dlg = open_window() is a QtWidgets.QDialog; open_window() is dlg
        again (reuse-and-raise, never a duplicate); dlg.close();
        open_window() is STILL dlg (default close hides; the module-level
        singleton keeps the object alive -- SETUP-01's
        survive-minimize/re-open mechanism); the 7 buttons exist with
        the spec-order labels via text(); then the 04-07 form parts:
        apply_state(validate-normalized DEFAULTS copy) -> collect_state
        round-trips losslessly through setup_state.validate_state,
        and a programmatic widget mutation drive (molecules 4,
        difficulty 2, block mode, h_bond + pi_stacking checked,
        upload toggle and back, demo set re-selected) lands in
        collect_state field-by-field with demo_combo carrying userData
        'demo-dev-1'; then the 08-02 tier-grouped-population asserts
        (data-relative: the expected shape re-derived through the same
        read_json_file + parse_manifest_dict + manifest_sets_grouped
        pure chain the window used -- data-row count == total group
        rows, separator count == (groups - 1), every None-data row is a
        flag-disabled separator, the known-ids helper excludes
        separators, findData/currentData round-trip); processEvents;
        finish dlg.close(). ZERO modals
        (PITFALL P5): no .exec_(), no QFileDialog, no QMessageBox
        anywhere in this script.
PART C  (T1b, 04-09 SETUP-07 setup-button drives -- success paths
        ONLY, driving the NON-MODAL _X_impl methods directly; the
        smoke-99 probe proved a modal QMessageBox BLOCKS under
        offscreen): C1 reset -- dlg._reset_impl() restores the
        defaults-normalized dict exactly; C2 randomize -- with the
        dropdown at 'demo-dev-1', dlg._randomize_impl() yields a
        validate_state-stable state with source_mode 'demo', upload
        None and demo_set_id PRESERVED as 'demo-dev-1' (Decision 5 --
        the 'demo-%04x' trap never reaches collect_state); C3
        save/load round-trip -- mutated widgets (4/2, block_exclusive,
        h_bond only) -> dlg._save_setup_to(tmp) writes a container
        with kind 'setup' version 1, _reset_impl wipes the form,
        dlg._load_setup_from(tmp) restores the mutated dict exactly.
PART D  (T1b, 04-10 SETUP-03 upload ingestion -- the 04-01 probe
        verdict is PASS (platform=offscreen), so this part RUNS;
        success paths ONLY, NO modals: _ingest_upload never owns a
        box): repo-anchored aamatch/data/ligands/benzamide.sdf ->
        dlg._ingest_upload(path) returns 1; the session slot carries 1
        row (entry_id 'mol-001', file 'uploads/mol-001.sdf') + the
        content dict keyed by that file + sha256 == the FILE bytes
        hash; the form reflects upload mode (src_upload checked, stack
        on page 1); collect_state()['upload'] matches path + FILE
        sha256; re-ingest replaces the slot; upload_ready_for is True
        for the window's own collect_state, False for a stale-sha256
        config and for a cleared slot, True again on the demo page.
        Cleanup: _uploaded = None, back to the demo page.
PART E  (ALWAYS -- the 04-11 SETUP-09 cleanup drive; the substance is
        cmd-tier/T1a-safe): baseline object list -> gamestart.start_game
        (defaults; scene grows, GameWizard pushed) -> the dialog's
        dlg._cleanup_now() when PART B's dialog was constructed, else
        the equivalent direct calls -> deleted > 0 asserted ->
        cmd.get_names('objects') == the baseline EXACTLY (original-
        scene restore, the prefix rule's proof) -> cmd.get_wizard()
        is None (the pop happened, nothing dangling -- research P6
        hazard closed). NO modals anywhere (impl only).
PART F  (ALWAYS, T1a -- the 04-12 SETUP-08 export drive via the
        module-level export_game, which needs no dialog and runs
        regardless of the probe; NO modals anywhere): tmp game file ->
        usable_randomized_state(7, demo_set_id='demo-dev-1') ->
        setup_window.export_game(state, 4242, None, None, tmp) -> the
        file exists with on-disk kind 'game' -> parse_game_data
        round-trips the validated setup, the embedded payload echoes
        seed 4242, ligand_texts == {} (bundled molecules are package-
        resolved, never embedded) and the summary names 'seed 4242'.
        os.remove(tmp).
PART F2 (T1b -- the 04-01 probe verdict is PASS (platform=offscreen),
        so this part RUNS; dlg._export_game_to is NON-MODAL by the
        smoke-99 receipt, no boxes): drive dlg._export_game_to(tmp2)
        with the form at defaults -> _last_export is stored (fresh int
        seed, candidates/ligand_content None on the demo flow); tmp2
        cleaned up.
PART G  (T1b -- the 04-01 probe verdict is PASS (platform=offscreen),
        so this part RUNS; the SETUP-10 start drive; NO modals
        anywhere: Start owns NO success box by design, 04-13 decision):
        form at defaults with the demo-dev-1 dropdown row ->
        dlg._start_impl() now runs the DEFERRED sequence (05-09): the
        window pops any prior GameWizard itself, prepares UNACTIVATED,
        switches to the Game status tab and arms the countdown, so the
        pending wizard (dlg.game_tab._pending_wizard) is a GameWizard
        NOT on the stack -> the GO step driven directly
        (dlg.game_tab._begin_play()) -> cmd.get_wizard() IS that wizard
        + engine._current_game().timer_anchor a float + the GO-time msm
        ORDER-LAW snapshot; then export-then-start -- dlg._last_export
        = {'setup': <the built defaults state>, 'seed': 31337, None,
        None} -> dlg._start_impl() again -> the PENDING wizard's
        payload['seed'] == 31337 read BEFORE its GO (Decision 4 proven),
        then GO; then molecules_spin.setValue(3) -> the reuse guard
        breaks (pure branch assert, unchanged). Restore:
        cancel_pending_start FIRST, then canonical done pop + the
        prefix-only cleanup -> get_names == baseline EXACTLY.
        DELIBERATE EVOLUTION (05-09; the 03-05 PART-letter precedent):
        the drive contract changed with the deferred design -- the
        CHECKS survive, the DRIVE sequence moves (pending-read before
        GO, GO driven directly).
PART G-alt (probe-FAIL degradation): skip the dialog drive; assert the
        pure chain directly -- build_state on DEFAULTS+upload_ready
        passes; print the skip line.
PART H  (ALWAYS, T1a -- the 05-05 SETUP-11 deferred-activation direct
        drive; cmd-substance only, NO dialog needed -- the activate=False
        seam + activate_game run against the plain cmd tier; the design
        is 05-RESEARCH-window-start-timer.md Pattern 2, GO-time
        activation living in the cmd tier): sentinel setup ->
        gamestart.start_game(setup=sentinel, seed=4242, activate=False)
        returns an UNACTIVATED GameWizard (cmd.get_wizard() is NOT it --
        the countdown window is wizard-free, pitfall P-1) while the
         scene grew (preparation complete); module-level _last_start
         holds EXACTLY the 5 input-tuple keys (07-05 deliberate
         evolution: the additive 'payload' entry, a dict carrying the
         seed) with the setup DEEP-COPIED
         (is not the sentinel, nested list not aliased) and the seed a
         real int; GO via gamestart.activate_game(wiz) pushes THAT wizard
        (conditional replace re-evaluated AT activation), anchors
        engine._current_game().timer_anchor to a float (timer from zero),
        and captures the wizard's msm snapshot post-push (the ORDER LAW
        fires at GO -- research Q4); restore: canonical done pop +
        prefix-only cleanup -> baseline scene EXACTLY + stack empty;
        _last_start reset so later parts start clean.
PART I  (T1b -- the 05-06 SETUP-11 two-tab restructure + GameTab
        shell drives; the 04-01 probe verdict is PASS
        (platform=offscreen), so this part RUNS; NO modals anywhere --
        pitfall P-6: the tick/countdown paths own no boxes; the
        countdown steps and _on_tick are driven AS METHODS per the
        05-RESEARCH anti-flakiness strategy, with NEVER a processEvents
        gap between start_countdown and the tick drive -- a real 1 s
        member QTimer tick firing through a pumped gap would shift
        _countdown_n and double-fire _begin_play): I1 the two tabs
        ('Setup'/'Game status'), game_tab is the tab-1 GameTab, and the
        7 button attributes + exact labels re-green after the re-wrap;
        I2 the shell state (_info_log a read-only QTextEdit, timer
        label '0:00', required label 'Required: -', btn_hint text
        'Hint'); I3 the countdown: start_game(activate=False) ->
        start_countdown (n == 3, 'Get ready...', timer active, pending
        wizard stored) -> 4 direct _countdown_tick drives land '3' '2'
        '1' 'GO!' each on its own line -> GO pushed THAT wizard
        (cmd.get_wizard() is it) with a float timer anchor and the 1 Hz
        _timer active (pitfall P-1 closed); I4 the timer label: anchor
        manipulated to time.time()-75 -> direct _on_tick -> '1:15'
        (pitfall P-4 live-anchor read); I5 the cancel: done pop +
        cleanup -> a second start_game(activate=False) ->
        start_countdown -> cancel_pending_start -> timer inactive +
        pending None -> one stray direct tick -> no 'GO!' and no stale
        activation (pitfall P-2 closed). Restore: cancel + done pop +
        prefix-only cleanup -> baseline scene EXACTLY.
PART J  (T1b -- the 04-01 probe verdict is PASS (platform=offscreen),
        so the dialog portions RUN; the 05-08 PLAY-05 hint drive;
        cmd-substance + dialog asserts only, NO modals anywhere: the
        hint handler is NON-MODAL by design -- impls never own boxes --
        and this part drives dlg.game_tab._hint_now directly; every
        color read uses the pinned cmd.iterate recipe, SMOKE-07's
        _color_map precedent): J1 pre-GO -- start_game(activate=False)
        + start_countdown -> dlg.game_tab._hint_now() returns None AND
        the whole scene's color maps are UNCHANGED (H-8 silent no-op);
        cancel + cleanup -> baseline. J2 main drive -- start_game()
        (default activates) -> expected candidates computed IN-SMOKE
        from the payload via capability.hint_candidate_slots over
        engine.ligand_profile_molecule(0, 0) -> wiz.hint() returns
        exactly that set (cmd path and pure path AGREE) -> every
        role=required slot is a candidate (GEN-04 parity live). J3 per
        candidate object: every elem C atom color ==
        cmd.get_color_index('orange') and every non-carbon unchanged
        from pre-hint; per NON-candidate (ligand, distractor slots,
        the OTHER molecule, the baseline scene): ZERO color change
        (H-5 closed). J4 re-press idempotence: color maps identical.
        J5 hint-over-green: cmd.color('green', <one candidate>) ->
        wiz.hint() -> carbons orange, non-carbons green (the coexist
        probe). J6 handler line: dlg.game_tab._hint_now() returns the
        dict AND _info_log carries 'Hint: %d eligible amino acid(s)
        highlighted.' with the right count. J7 restore: canonical Done
        -> the WHOLE scene's color maps == materialization colors (a
        hinted-never-selected object included -- the (a) trap closed,
        H-1) + _color_store cleared + stack empty + baseline scene
        EXACTLY after prefix-only cleanup.
PART K  (ALWAYS, T0-in-smoke): Gate A2 shape sanity echoed inside
        PyMOL's interpreter for the record -- aamatch/__init__.py
        carries ZERO column-0 import/from statements (the lazy-import
        discipline the menu rewire must preserve). (05-06 inserted PART
        I before the echo -- the established renumber pattern; the echo
        letter shifted H -> I (05-05) -> J (05-06) -> K (05-08).)

Conventions (frozen Phase 1, kept): anchor the repo root via sys.argv
first / cwd fallback (never __file__); import aamatch directly (module
identity 'aamatch' -- NEVER the pmg_tk.startup path in the same
session); every print on ONE line and flushed.

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import os
import sys
import traceback

# QT_QPA_PLATFORM MUST be set BEFORE any pymol.Qt import (the offscreen
# recipe the 04-01 probe proved on the FIRST attempt,
# 04-01-SUMMARY.md:33). aamatch.setup_window carries module-level Qt
# imports, so the env var goes up here, before the aamatch import below.
os.environ['QT_QPA_PLATFORM'] = 'offscreen'


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_11_window.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []
REC = {}


def check(name, cond, detail=''):
    print('SMOKE-11 %-44s %s %s' % (name, 'PASS' if cond else 'FAIL',
                                     detail), flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import aamatch  # noqa: E402

print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

setup_window = None

# ============================================================
# PART A: import-proof tier (ALWAYS)
# ============================================================
try:
    import aamatch.setup_window as setup_window
    check('part A: import aamatch.setup_window headless', True,
          'module-level pymol.Qt binding loaded')
    check('part A: open_window is callable',
          callable(setup_window.open_window),
          'open_window=%r' % (setup_window.open_window,))
    check('part A: _window singleton starts None',
          setup_window._window is None,
          '_window=%r' % (setup_window._window,))
    sw_path = os.path.join(_ROOT, 'aamatch', 'setup_window.py')
    with open(sw_path, 'rb') as f:
        sw_src = f.read().decode('utf-8')
    check("part A: source carries 'from pymol.Qt import' (shim only)",
          'from pymol.Qt import' in sw_src, sw_path)
    check("part A: source carries NO 'from PyQt5' (banned repo-wide)",
          'from PyQt5' not in sw_src, '')
except Exception:
    traceback.print_exc()
    check('part A import-proof tier', False, 'raised (see traceback)')

# ============================================================
# PART B: widget-construction tier (04-01 probe verdict: PASS
# (platform=offscreen) -- these parts RUN; a FAIL verdict would print
# 'PART B SKIPPED (probe verdict)' and continue instead)
# ============================================================
try:
    if setup_window is None:
        raise RuntimeError('part A failed')
    from pymol.Qt import QtWidgets
    # Reuse-or-create, the exact 04-01 probe recipe.
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(['aamatch-smoke-11'])
    dlg = setup_window.open_window()
    check('part B: open_window returns a QDialog',
          isinstance(dlg, QtWidgets.QDialog),
          'type=%r' % (type(dlg),))
    check('part B: second open_window reuses the SAME dialog',
          setup_window.open_window() is dlg,
          'singleton=%r' % (setup_window._window,))
    dlg.close()
    check('part B: close()+re-open is STILL the same instance',
          setup_window.open_window() is dlg,
          'default close hides; the singleton survives (SETUP-01)')
    expected = [('btn_reset', 'Reset'), ('btn_randomize', 'Randomize'),
                ('btn_save_setup', 'Save Setup'),
                ('btn_load_setup', 'Load Setup'),
                ('btn_generate_export', 'Generate and export'),
                ('btn_cleanup', 'Cleanup model'), ('btn_start', 'Start')]
    got = [(attr, getattr(dlg, attr).text()) if hasattr(dlg, attr)
           else (attr, None) for (attr, _label) in expected]
    check('part B: 7 buttons in spec order with exact labels',
          got == expected, 'got=%r' % (got,))

    # ---- 04-07 form parts: collect/apply round-trip + mutation ----
    # setup_state is pure and importable headlessly (no Qt, no pymol).
    from aamatch import setup_state
    dlg.apply_state(dict(setup_state.DEFAULTS))
    state = dlg.collect_state()
    check('part B: apply(DEFAULTS)->collect round-trips via '
          'validate_state',
          setup_state.validate_state(state)
          == setup_state.validate_state(dict(setup_state.DEFAULTS)),
          'got=%r' % (state,))
    # Widget mutation drive: every changed value must land in the next
    # collect_state snapshot.
    dlg.molecules_spin.setValue(4)
    dlg.difficulty_spin.setValue(2)
    dlg.mode_block.setChecked(True)
    for (itype, cb) in dlg.interaction_checks:
        cb.setChecked(itype in ('h_bond', 'pi_stacking'))
    dlg.src_upload.setChecked(True)
    dlg.src_demo.setChecked(True)
    sel = dlg.demo_combo.findData('demo-dev-1')
    if sel >= 0:
        dlg.demo_combo.setCurrentIndex(sel)
    got2 = dlg.collect_state()
    check('part B: widget mutation drive lands in collect_state',
          got2['molecules_per_level'] == 4
          and got2['difficulty_levels'] == 2
          and got2['interaction_mode'] == 'block_exclusive'
          and got2['allowed_interactions'] == ['h_bond', 'pi_stacking']
          and got2['source_mode'] == 'demo',
          'got=%r' % (got2,))
    check("part B: demo_combo carries userData 'demo-dev-1'",
          sel >= 0
          and dlg.demo_combo.currentData() == 'demo-dev-1',
          'currentData=%r' % (dlg.demo_combo.currentData(),))

    # ---- 08-02 grouped-population asserts (data-relative, T1b) ----
    # Re-derive the expected shape through the EXACT pure chain the
    # window used (read_json_file + parse_manifest_dict, the engine's
    # read path), so these stay green when the curated manifest lands.
    from aamatch import manifest, paths, persistence, setup_form
    payload_b = manifest.parse_manifest_dict(persistence.read_json_file(
        paths.package_data_path('data', 'MANIFEST.json')))
    groups_b = setup_form.manifest_sets_grouped(payload_b)
    total_rows_b = sum(len(rows) for (_lbl, rows) in groups_b)
    data_rows_b = sum(1 for i in range(dlg.demo_combo.count())
                      if dlg.demo_combo.itemData(i) is not None)
    sep_rows_b = dlg.demo_combo.count() - data_rows_b
    expected_seps_b = len(groups_b) - 1 if len(groups_b) > 1 else 0
    check('part B: combo data-row count == total rows across groups '
          '(08-02)',
          dlg.demo_combo.itemData(0) is not None
          and data_rows_b == total_rows_b,
          'data=%r groups=%r' % (data_rows_b, total_rows_b))
    check('part B: separator count == (groups - 1) -- BETWEEN groups '
          'only (08-02)',
          sep_rows_b == expected_seps_b,
          'seps=%r groups=%r' % (sep_rows_b, len(groups_b)))
    # Falsifiable amid any checklist defect: with today's dev-only
    # manifest (1 easy set) the dropdown is byte-identical to the old
    # flat list -- one data row, zero separators.
    try:
        from pymol.Qt import QtCore
        model_b = dlg.demo_combo.model()
        sep_flags_ok_b = True
        nonflagged_b = []
        for i in range(dlg.demo_combo.count()):
            if dlg.demo_combo.itemData(i) is None:
                item_b = model_b.item(i)
                if item_b is None \
                        or (item_b.flags() & QtCore.Qt.ItemIsEnabled):
                    sep_flags_ok_b = False
                    nonflagged_b.append(i)
    except Exception:
        traceback.print_exc()
        sep_flags_ok_b = False
        nonflagged_b = 'raised'
    check('part B: every None-data row IS a separator (enabled flag '
          'cleared -- 08-02)',
          sep_flags_ok_b, 'nonflagged rows=%r' % (nonflagged_b,))
    check('part B: known-ids helper yields NO None/str(None) (08-02)',
          dlg._known_demo_set_ids() == tuple(
              dlg.demo_combo.itemData(i)
              for i in range(dlg.demo_combo.count())
              if dlg.demo_combo.itemData(i) is not None),
          'known=%r' % (dlg._known_demo_set_ids(),))
    idx_dev_b = dlg.demo_combo.findData('demo-dev-1')
    if idx_dev_b >= 0:
        dlg.demo_combo.setCurrentIndex(idx_dev_b)
    check('part B: findData(demo-dev-1) resolves + currentData '
          'round-trips (08-02)',
          idx_dev_b >= 0
          and not dlg.demo_combo.itemData(idx_dev_b) is None
          and dlg.demo_combo.currentData() == 'demo-dev-1',
          'idx=%r data=%r' % (idx_dev_b, dlg.demo_combo.currentData()))

    app.processEvents()
    dlg.close()
    REC['dialog'] = '%r' % (type(dlg),)
except Exception:
    traceback.print_exc()
    check('part B widget-construction tier', False,
          'raised (see traceback)')

# ============================================================
# PART C: SETUP-07 setup-button drives (T1b -- the 04-01 probe
# verdict is PASS (platform=offscreen), so these parts RUN; success
# paths ONLY via the NON-MODAL _X_impl methods -- the smoke-99 probe
# proved a modal QMessageBox BLOCKS under offscreen)
# ============================================================
try:
    if setup_window is None:
        raise RuntimeError('part A failed')
    import tempfile
    from pymol.Qt import QtWidgets
    from aamatch import persistence, setup_state

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(['aamatch-smoke-11'])

    dlg = setup_window.open_window()   # singleton reuse (PART B closed it)

    # ---- C1: reset restores the defaults-normalized dict ----
    dlg._reset_impl()
    got_c1 = dlg.collect_state()
    check('part C1: _reset_impl restores DEFAULTS (deep-copied frozen)',
          got_c1 == setup_state.validate_state(dict(setup_state.DEFAULTS)),
          'got=%r' % (got_c1,))

    # ---- C2: randomize keeps the dropdown selection (Decision 5) ----
    sel2 = dlg.demo_combo.findData('demo-dev-1')
    if sel2 >= 0:
        dlg.demo_combo.setCurrentIndex(sel2)
    dlg._randomize_impl()
    got_c2 = dlg.collect_state()
    check('part C2: _randomize_impl yields a validate_state-stable state',
          setup_state.validate_state(got_c2) == got_c2,
          'got=%r' % (got_c2,))
    check('part C2: source demo, upload None, demo_set_id preserved',
          sel2 >= 0
          and got_c2['source_mode'] == 'demo'
          and got_c2['upload'] is None
          and got_c2['demo_set_id'] == 'demo-dev-1',
          "demo_set_id=%r (the 'demo-%%04x' trap must NOT appear)"
          % (got_c2['demo_set_id'],))

    # ---- C3: save -> reset -> load round-trip ----
    tmp = os.path.join(tempfile.gettempdir(),
                       'aamatch_smoke11_setup.aam.setup.json')
    dlg.molecules_spin.setValue(4)
    dlg.difficulty_spin.setValue(2)
    dlg.mode_block.setChecked(True)
    for (itype, cb) in dlg.interaction_checks:
        cb.setChecked(itype == 'h_bond')
    expected = dlg.collect_state()
    dlg._save_setup_to(tmp)
    check('part C3: _save_setup_to wrote the setup file',
          os.path.exists(tmp), 'tmp=%r' % (tmp,))
    payload = persistence.read_json_file(tmp)
    check('part C3: on-disk container kind=setup version=1',
          payload.get('kind') == 'setup' and payload.get('version') == 1,
          'kind=%r version=%r' % (payload.get('kind'),
                                  payload.get('version')))
    dlg._reset_impl()
    dlg._load_setup_from(tmp)
    got_c3 = dlg.collect_state()
    check('part C3: save->reset->load round-trips the mutated dict',
          got_c3 == expected, 'got=%r expected=%r' % (got_c3, expected))
    os.remove(tmp)

    app.processEvents()
    dlg.close()
    REC['setup_drives'] = 'C1 reset, C2 randomize, C3 save/load'
except Exception:
    traceback.print_exc()
    check('part C setup-button drives', False,
          'raised (see traceback)')

# ============================================================
# PART D: upload ingestion drive (T1b -- the 04-01 probe verdict is
# PASS (platform=offscreen), so this part RUNS; success paths ONLY,
# NO modals: _ingest_upload never owns a box -- the 04-09 smoke-99
# probe proved a modal QMessageBox BLOCKS under offscreen)
# ============================================================
try:
    if setup_window is None:
        raise RuntimeError('part A failed')
    import hashlib
    from pymol.Qt import QtWidgets

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(['aamatch-smoke-11'])
    dlg = setup_window.open_window()   # singleton reuse

    benz = os.path.join(_ROOT, 'aamatch', 'data', 'ligands',
                        'benzamide.sdf')
    with open(benz, 'rb') as f:
        benz_bytes = f.read()
    file_sha = hashlib.sha256(benz_bytes).hexdigest()

    n = dlg._ingest_upload(benz)
    check('part D: _ingest_upload returns the record count (1)',
          n == 1, 'n=%r' % (n,))
    up = dlg._uploaded or {}
    rows = up.get('rows') or []
    content = up.get('content') or {}
    row0 = rows[0] if len(rows) == 1 else {}
    check('part D: 1 row with synthetic entry/file ids',
          len(rows) == 1
          and row0.get('entry_id') == 'mol-001'
          and row0.get('file') == 'uploads/mol-001.sdf',
          'rows=%r' % (rows,))
    check('part D: ligand_content dict keyed by that file',
          list(content.keys()) == ['uploads/mol-001.sdf'],
          'keys=%r' % (sorted(content),))
    check('part D: slot path + sha256 == the FILE bytes hash',
          up.get('path') == benz and up.get('sha256') == file_sha,
          'sha256=%r' % (up.get('sha256'),))
    check('part D: form reflects upload mode (radio + stack page 1)',
          dlg.src_upload.isChecked()
          and dlg.source_stack.currentIndex() == 1,
          'checked=%r page=%r' % (dlg.src_upload.isChecked(),
                                  dlg.source_stack.currentIndex()))
    state_u = dlg.collect_state()
    upload_field = state_u.get('upload') or {}
    check("part D: collect_state upload={'path','sha256'} (FILE hash)",
          state_u.get('source_mode') == 'upload'
          and upload_field.get('path') == benz
          and upload_field.get('sha256') == file_sha,
          'upload=%r' % (state_u.get('upload'),))
    n2 = dlg._ingest_upload(benz)
    up2 = dlg._uploaded or {}
    check('part D: re-ingest REPLACES the slot (idempotent, 1 row)',
          n2 == 1 and len(up2.get('rows') or []) == 1
          and up2.get('path') == benz and up2.get('sha256') == file_sha,
          'n2=%r' % (n2,))
    check('part D: upload_ready_for its own collect_state is True',
          dlg.upload_ready_for(dlg.collect_state()) is True, '')
    stale = dict(state_u)
    stale['upload'] = {'path': benz, 'sha256': '0' * 64}
    check('part D: upload_ready_for a stale-sha256 config is False',
          dlg.upload_ready_for(stale) is False,
          'stale=%r' % (stale['upload'],))
    dlg._uploaded = None
    check('part D: upload_ready_for is False once the slot is empty',
          dlg.upload_ready_for(state_u) is False, '')
    dlg.src_demo.setChecked(True)
    check("part D: upload_ready_for a 'demo' config is True regardless",
          dlg.upload_ready_for(dlg.collect_state()) is True, '')
    # Cleanup: session slot cleared + demo page restored (above); the
    # path label is cosmetic -- blank it for a clean close.
    dlg.upload_path_label.setText('')
    dlg.upload_path_label.setToolTip('')
    app.processEvents()
    dlg.close()
    REC['upload_ingest'] = 'benzamide n=1; ready/stale/empty/demo verdicts'
except Exception:
    traceback.print_exc()
    check('part D upload-ingest drive', False, 'raised (see traceback)')

# ============================================================
# PART E: SETUP-09 cleanup drive (ALWAYS -- the substance is cmd-tier
# / T1a-safe; dlg._cleanup_now() when PART B's dialog was constructed,
# else the equivalent direct calls; NO modals anywhere -- impls never
# own boxes, the smoke-99 probe receipt)
# ============================================================
try:
    from pymol import cmd
    from aamatch import gamestart
    baseline = cmd.get_names('objects')
    wiz = gamestart.start_game()   # defaults: cleanup-first, materialize,
    scene = cmd.get_names('objects')  # activate -- the scene GREW
    new_names = [n for n in scene if n not in baseline]
    check('part E: start_game grows the scene, GameWizard on top',
          len(new_names) > 0
          and all(n.startswith('_aam_') for n in new_names)
          and cmd.get_wizard() is wiz,
          'grew=%d top=%r' % (len(new_names),
                              cmd.get_wizard(),))
    if (setup_window is not None
            and getattr(setup_window, '_window', None) is not None):
        deleted = setup_window._window._cleanup_now()
        drive = 'dlg._cleanup_now()'
    else:
        # Dialog unavailable (PART B probe-gated off): the equivalent
        # direct calls -- same isinstance gate, same None-pop, same
        # prefix-only deletion.
        from aamatch import wizard, placement
        prior = cmd.get_wizard()
        if isinstance(prior, wizard.GameWizard):
            cmd.set_wizard()
        deleted = placement.cleanup_game_objects()['deleted']
        drive = 'direct calls'
    check('part E: cleanup (%s) reports deleted > 0' % drive,
          deleted is not None and deleted > 0,
          'deleted=%r' % (deleted,))
    check('part E: exact scene restore -- get_names == baseline',
          cmd.get_names('objects') == baseline,
          'after=%r baseline=%r'
          % (cmd.get_names('objects'), baseline))
    check('part E: wizard popped iff GameWizard -- stack now empty',
          cmd.get_wizard() is None,
          'top=%r (P6 hazard closed)' % (cmd.get_wizard(),))
    REC['cleanup'] = '%s; deleted=%r' % (drive, deleted)
except Exception:
    traceback.print_exc()
    check('part E cleanup drive', False, 'raised (see traceback)')

# ============================================================
# PART F: SETUP-08 export_game drive (ALWAYS, T1a -- the module-level
# function needs no dialog and runs regardless of the probe; NO modals
# anywhere -- export_game itself owns no boxes)
# ============================================================
try:
    if setup_window is None:
        raise RuntimeError('part A failed')
    import tempfile
    from aamatch import game_file, persistence, setup_form, setup_state

    tmp = os.path.join(tempfile.gettempdir(),
                       'aamatch_smoke11_game.aamatch.json')
    state = setup_form.usable_randomized_state(7, demo_set_id='demo-dev-1')
    # usable_randomized_state guarantees a USABLE demo_set_id, not a
    # generation-feasible draw against the 2-molecule demo set: seed 7
    # draws molecules_per_level 9 (needs 9 distinct candidates;
    # generator.py correctly refuses) AND block_exclusive incl.
    # cation_pi (which the demo ligands cannot ALL support,
    # generator.py:403-410). The export smoke needs a FEASIBLE demo
    # state, so pin these fields the way a user correcting the
    # infeasible draw would before clicking Export: 2 molecules
    # (the frozen default; the demo set max) and 'exclusive' with
    # h_bond (every demo ligand forms at least one of the pair).
    state['molecules_per_level'] = 2
    state['interaction_mode'] = 'exclusive'
    state['allowed_interactions'] = ['h_bond', 'pi_stacking']
    summary = setup_window.export_game(state, 4242, None, None, tmp)
    check('part F: export_game returns the summary line',
          isinstance(summary, str), 'summary=%r' % (summary,))
    check('part F: the shareable game file exists',
          os.path.exists(tmp), 'tmp=%r' % (tmp,))
    container = persistence.read_json_file(tmp)
    check("part F: on-disk container kind is 'game'",
          container.get('kind') == 'game',
          'kind=%r' % (container.get('kind'),))
    data = game_file.parse_game_data(container)
    check('part F: parse_game_data round-trips the validated setup',
          data['setup'] == setup_state.validate_state(state),
          'setup=%r' % (data['setup'],))
    check('part F: embedded payload echoes the export seed (4242)',
          data['payload']['seed'] == 4242,
          'seed=%r' % (data['payload']['seed'],))
    check("part F: demo flow embeds NOTHING (ligand_texts == {})",
          data['ligand_texts'] == {},
          'keys=%r' % (sorted(data['ligand_texts']),))
    check("part F: the summary line names the seed ('seed 4242')",
          'seed 4242' in summary, 'summary=%r' % (summary,))
    os.remove(tmp)
    REC['export_game'] = 'seed 4242 round-trip; ligand_texts {} (demo)'
except Exception:
    traceback.print_exc()
    check('part F export_game drive', False, 'raised (see traceback)')

# ============================================================
# PART F2: dialog export drive (T1b -- the 04-01 probe verdict is PASS
# (platform=offscreen), so this part RUNS; dlg._export_game_to is
# NON-MODAL and returns the summary (the smoke-99 receipt: impls own no
# boxes), so driving it headless is safe)
# ============================================================
try:
    if setup_window is None:
        raise RuntimeError('part A failed')
    import tempfile
    from pymol.Qt import QtWidgets

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(['aamatch-smoke-11'])
    dlg = setup_window.open_window()   # singleton reuse
    dlg._reset_impl()                  # the form at defaults
    tmp2 = os.path.join(tempfile.gettempdir(),
                        'aamatch_smoke11_game2.aamatch.json')
    summary2 = dlg._export_game_to(tmp2)
    check('part F2: _export_game_to returns the summary, file written',
          isinstance(summary2, str) and os.path.exists(tmp2),
          'tmp2=%r' % (tmp2,))
    le = dlg._last_export or {}
    check('part F2: _last_export stored with a fresh int seed',
          dlg._last_export is not None
          and isinstance(le.get('seed'), int)
          and not isinstance(le.get('seed'), bool),
          'seed=%r' % (le.get('seed'),))
    check('part F2: demo flow -> candidates/ligand_content None',
          le.get('candidates') is None
          and le.get('ligand_content') is None
          and isinstance(le.get('setup'), dict)
          and le['setup'].get('source_mode') == 'demo',
          'mode=%r' % ((le.get('setup') or {}).get('source_mode'),))
    os.remove(tmp2)
    app.processEvents()
    dlg.close()
    REC['export_drive'] = 'dlg._export_game_to; _last_export tuple ok'
except Exception:
    traceback.print_exc()
    check('part F2 dialog export drive', False, 'raised (see traceback)')

# ============================================================
# PART G: SETUP-10 start drive + export-tuple reuse (T1b -- the 04-01
# probe verdict is PASS (platform=offscreen), so this part RUNS; NO
# modals anywhere: Start owns NO success box by design (04-13
# decision), and _start_impl is NON-MODAL by the smoke-99 receipt).
#
# DELIBERATE EVOLUTION (05-09; the 03-05 PART-letter precedent -- the
# CHECKS survive, the DRIVE sequence moves when the drive contract
# changes): _start_impl is now DEFERRED -- the window pops any prior
# GameWizard itself (P-3), prepares UNACTIVATED (activate=False),
# switches to the Game status tab and arms the cancellable countdown.
# After the drive the wizard is PENDING (game_tab._pending_wizard),
# NOT on the stack; the GO step is driven directly
# (game_tab._begin_play) per the anti-flakiness strategy, and only
# THEN do the wizard-active / anchor / msm ORDER-LAW asserts run.
# ============================================================
try:
    if setup_window is None:
        raise RuntimeError('part A failed')   # PART G-alt below
    from pymol import cmd
    from pymol.Qt import QtWidgets
    from aamatch import engine, placement, setup_form, setup_state, wizard

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(['aamatch-smoke-11'])
    dlg = setup_window.open_window()   # singleton reuse
    dlg._reset_impl()                  # the form at defaults
    sel_g = dlg.demo_combo.findData('demo-dev-1')
    if sel_g >= 0:
        dlg.demo_combo.setCurrentIndex(sel_g)
    baseline_g = cmd.get_names('objects')

    # ---- G1: _start_impl -> PENDING (not stacked) -> direct GO ----
    dlg._start_impl()                  # no modal on success by design
    wiz1 = dlg.game_tab._pending_wizard
    scene1 = cmd.get_names('objects')
    new1 = [n for n in scene1 if n not in baseline_g]
    check('part G1: _start_impl stores a PENDING GameWizard '
          '(deferred prepare)',
          isinstance(wiz1, wizard.GameWizard),
          'pending=%r' % (wiz1,))
    check('part G1: the pending wizard is NOT on the stack '
          '(the countdown window is wizard-free -- pitfalls P-1/P-3)',
          cmd.get_wizard() is not wiz1
          and not isinstance(cmd.get_wizard(), wizard.GameWizard),
          'top=%r' % (cmd.get_wizard(),))
    check('part G1: the scene grew (_aam_* objects materialized)',
          len(new1) > 0
          and all(n.startswith('_aam_') for n in new1),
          'grew=%d' % (len(new1),))
    seed1 = wiz1._payload.get('seed')
    check('part G1: the payload carries a real int seed',
          isinstance(seed1, int) and not isinstance(seed1, bool),
          'seed=%r' % (seed1,))

    # -- the GO step driven directly (the anti-flakiness strategy:
    # steps as methods, never a processEvents gap) --
    dlg.game_tab._begin_play()
    anchor1 = engine._current_game().timer_anchor
    check('part G1: GO (_begin_play) pushes THAT wizard + anchors '
          'the timer (float)',
          cmd.get_wizard() is wiz1 and isinstance(anchor1, float),
          'top=%r anchor=%r' % (cmd.get_wizard(), anchor1))
    check('part G1: msm snapshot captured POST-push at GO (ORDER LAW)',
          isinstance(wiz1._saved_msm, int),
          '_saved_msm=%r (the push happens at GO, so the snapshot does)'
          % (wiz1._saved_msm,))

    # ---- G2: export-then-start replays the exported tuple ----
    # (Decision 4): last_export.setup EQUALS the freshly built state,
    # so the exported (setup, seed, candidates, ligand_content) tuple
    # is replayed verbatim; the PENDING wizard's seed is read BEFORE
    # its GO -- the game prepared IS the game shared.
    form_g = dlg.collect_state()
    form_g['upload_ready'] = dlg.upload_ready_for(form_g)
    # 08-02: the mirror uses the SAME separator-aware helper the window
    # uses (a raw str(itemData) loop would yield 'None' for separators).
    known_g = dlg._known_demo_set_ids()
    state_g = setup_form.build_state(form_g, known_set_ids=known_g)
    dlg._last_export = {'setup': state_g, 'seed': 31337,
                        'candidates': None, 'ligand_content': None}
    dlg._start_impl()                  # mid-game restart (deferred)
    wiz2 = dlg.game_tab._pending_wizard
    seed2 = wiz2._payload.get('seed') if wiz2 is not None else None
    check('part G2: restart replays the exported seed 31337 in the '
          'PENDING wizard BEFORE its GO (Decision 4 proven)',
          wiz2 is not None and wiz2 is not wiz1
          and isinstance(wiz2, wizard.GameWizard)
          and seed2 == 31337,
          'seed=%r' % (seed2,))
    check('part G2: the window popped the prior wizard pre-prepare '
          '(P-3); the new one is pending, not stacked',
          not isinstance(cmd.get_wizard(), wizard.GameWizard),
          'top=%r' % (cmd.get_wizard(),))
    dlg.game_tab._begin_play()         # GO for the seed-31337 wizard
    check('part G2: GO pushes the seed-31337 wizard',
          cmd.get_wizard() is wiz2,
          'top=%r' % (cmd.get_wizard(),))

    # ---- G3: a form change breaks the reuse guard (pure assert,
    # tolerant of any random seed the next Start would draw;
    # UNCHANGED by the 05-09 evolution) ----
    dlg.molecules_spin.setValue(3)
    check('part G3: setup changed -> reuse branch is skipped',
          dlg._last_export['setup']
          != setup_state.validate_state(dlg.collect_state()),
          'last-setup=%r' % (dlg._last_export['setup'],))

    # ---- restore: cancel any pending countdown FIRST (P-2), then
    # the canonical done pop + prefix-only cleanup ----
    dlg.game_tab.cancel_pending_start()
    cmd.set_wizard()                   # GameWizard done pop
    result_g = placement.cleanup_game_objects()
    check('part G: cancel + done pop + cleanup restores the baseline '
          'scene EXACTLY',
          cmd.get_wizard() is None
          and result_g['deleted'] > 0
          and cmd.get_names('objects') == baseline_g,
          'deleted=%r after=%r baseline=%r'
          % (result_g['deleted'], cmd.get_names('objects'),
             baseline_g))
    app.processEvents()
    dlg.close()
    REC['start_drive'] = ('G1 deferred pending-then-GO (+anchor/ORDER '
                          'LAW), G2 seed 31337 pending-read-before-GO, '
                          'G3 reuse guard, cancel-first restore')
except Exception as e_g:
    if 'part A failed' not in str(e_g):
        traceback.print_exc()
        check('part G start drive', False, 'raised (see traceback)')
    else:
        # ---- PART G-alt (probe-FAIL): the pure pre-check chain only;
        # the start drive + reuse proof stay T2 [HUMAN] (04-14) ----
        print('SMOKE-11 PART G SKIPPED (probe verdict) -- dialog tier '
              'off; pure chain asserted instead [HUMAN]', flush=True)
        try:
            from aamatch import setup_form, setup_state
            form_alt = dict(setup_state.DEFAULTS)
            form_alt['upload_ready'] = True
            state_alt = setup_form.build_state(
                form_alt, known_set_ids=('demo-dev-1',))
            check('part G-alt: build_state(DEFAULTS, upload_ready='
                  'True) passes (pure chain)',
                  isinstance(state_alt, dict)
                  and state_alt.get('source_mode') == 'demo'
                  and state_alt == setup_state.validate_state(state_alt),
                  'state=%r' % (state_alt,))
            REC['start_drive'] = 'PART G SKIPPED (probe verdict) [HUMAN]'
        except Exception:
            traceback.print_exc()
            check('part G-alt pure chain', False,
                  'raised (see traceback)')

# ============================================================
# PART H: SETUP-11 deferred-activation direct drive (ALWAYS -- T1a
# cmd-substance only, NO dialog needed; the activate=False seam +
# activate_game run against the plain cmd tier; the design is
# 05-RESEARCH-window-start-timer.md Pattern 2, GO-time activation
# living in the cmd tier)
# ============================================================
try:
    from pymol import cmd
    from aamatch import engine, gamestart, placement, setup_state, wizard

    sentinel = dict(setup_state.DEFAULTS)
    baseline_h = cmd.get_names('objects')

    # ---- prepare WITHOUT activating (activate=False) ----
    wiz_h = gamestart.start_game(setup=sentinel, seed=4242,
                                 activate=False)
    check('part H: activate=False returns a GameWizard, NOT pushed',
          isinstance(wiz_h, wizard.GameWizard)
          and cmd.get_wizard() is not wiz_h,
          'top=%r (the countdown window is wizard-free -- pitfall P-1)'
          % (cmd.get_wizard(),))
    scene_h = cmd.get_names('objects')
    new_h = [n for n in scene_h if n not in baseline_h]
    check('part H: the scene grew though activation is deferred',
          len(new_h) > 0
          and all(n.startswith('_aam_') for n in new_h),
          'grew=%d (preparation complete)' % (len(new_h),))

    # ---- _last_start input tuple (SETUP-11; Phase-6 Restart) ----
    # 07-05 DELIBERATE evolution (plan-authorized): the pin moved from
    # the 4-key tuple to the 5-key tuple -- the ADDITIVE 'payload'
    # entry (07-05 Recorded Decision 1) makes every Restart replay
    # payload-direct (byte-identical for demos, CORRECT for uploads).
    ls = gamestart._last_start or {}
    check('part H: _last_start holds EXACTLY the 5 input-tuple keys',
          sorted(ls) == ['candidates', 'ligand_content', 'payload',
                         'seed', 'setup'],
          'keys=%r' % (sorted(ls),))
    check('part H: _last_start payload is a dict carrying the seed',
          isinstance(ls.get('payload'), dict)
          and 'seed' in ls['payload']
          and ls['payload']['seed'] == 4242,
          'the embed-don-t-regenerate replay input (07-05)')
    check('part H: _last_start setup DEEP-COPIED (aliasing proof)',
          isinstance(ls.get('setup'), dict)
          and ls.get('setup') is not sentinel
          and ls['setup'].get('allowed_interactions')
          is not sentinel['allowed_interactions'],
          'the 04-09 _reset_impl aliasing note, guarded')
    check('part H: _last_start seed is a real int',
          isinstance(ls.get('seed'), int)
          and not isinstance(ls.get('seed'), bool)
          and ls.get('seed') == 4242,
          'seed=%r' % (ls.get('seed'),))
    check('part H: _last_start tuple echoes the None overrides',
          ls.get('candidates') is None
          and ls.get('ligand_content') is None,
          'candidates=%r ligand_content=%r'
          % (ls.get('candidates'), ls.get('ligand_content')))

    # ---- GO: activate_game(wiz) pushes + anchors (Pattern 2) ----
    gamestart.activate_game(wiz_h)
    check('part H: activate_game pushes THAT wizard at GO',
          cmd.get_wizard() is wiz_h,
          'top=%r (conditional replace re-evaluated AT activation)'
          % (cmd.get_wizard(),))
    anchor = engine._current_game().timer_anchor
    check('part H: timer anchored from zero at GO (float)',
          isinstance(anchor, float),
          'timer_anchor=%r (GO-time anchor, start from zero)'
          % (anchor,))
    check('part H: msm snapshot captured POST-push at GO (ORDER LAW)',
          isinstance(wiz_h._saved_msm, int),
          '_saved_msm=%r (the push happens at GO, so the snapshot does)'
          % (wiz_h._saved_msm,))

    # ---- restore: done pop + prefix-only cleanup + store reset ----
    cmd.set_wizard()                   # canonical done pop
    result_h = placement.cleanup_game_objects()
    check('part H: restore -- baseline scene EXACTLY, stack empty',
          cmd.get_wizard() is None
          and result_h['deleted'] > 0
          and cmd.get_names('objects') == baseline_h,
          'deleted=%r after=%r baseline=%r'
          % (result_h['deleted'], cmd.get_names('objects'),
             baseline_h))
    gamestart._last_start = None       # later parts start clean
    REC['deferred_activation'] = ('unactivated prepare, GO push+anchor, '
                                  '_last_start round-trip, exact restore')
except Exception:
    traceback.print_exc()
    check('part H deferred-activation drive', False,
          'raised (see traceback)')

# ============================================================
# PART I: SETUP-11 two-tab + GameTab shell drives (T1b -- the 04-01
# probe verdict is PASS (platform=offscreen), so this part RUNS; NO
# modals anywhere -- pitfall P-6: the tick/countdown paths own no
# boxes. The countdown steps and _on_tick are driven AS METHODS per
# the 05-RESEARCH anti-flakiness strategy; NEVER pump processEvents
# between start_countdown and the tick drive -- a real 1 s member
# QTimer tick firing through a pumped gap would shift _countdown_n
# and double-fire _begin_play)
# ============================================================
try:
    if setup_window is None:
        raise RuntimeError('part A failed')
    import time as time_mod
    from pymol import cmd
    from pymol.Qt import QtWidgets
    from aamatch import engine, gamestart, game_window, placement

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(['aamatch-smoke-11'])
    dlg = setup_window.open_window()   # singleton reuse
    baseline_i = cmd.get_names('objects')

    # ---- I1: the two-tab structure; every Setup attribute intact ----
    check("part I1: two tabs -- 'Setup' first, 'Game status' second",
          dlg.tabs.count() == 2
          and dlg.tabs.tabText(0) == 'Setup'
          and dlg.tabs.tabText(1) == 'Game status',
          'titles=%r' % ([dlg.tabs.tabText(i)
                          for i in range(dlg.tabs.count())],))
    check('part I1: game_tab is the GameTab instance on tab 1',
          isinstance(dlg.game_tab, game_window.GameTab)
          and dlg.tabs.widget(1) is dlg.game_tab,
          'type=%r' % (type(dlg.game_tab),))
    expected_i = [('btn_reset', 'Reset'),
                  ('btn_randomize', 'Randomize'),
                  ('btn_save_setup', 'Save Setup'),
                  ('btn_load_setup', 'Load Setup'),
                  ('btn_generate_export', 'Generate and export'),
                  ('btn_cleanup', 'Cleanup model'), ('btn_start', 'Start')]
    got_i = [(attr, getattr(dlg, attr).text()) if hasattr(dlg, attr)
             else (attr, None) for (attr, _l) in expected_i]
    check('part I1: 7 buttons re-green after the tab re-wrap '
          '(minimal churn)',
          got_i == expected_i, 'got=%r' % (got_i,))

    # ---- I2: the GameTab shell state ----
    check('part I2: info box is a read-only QTextEdit',
          isinstance(dlg.game_tab._info_log, QtWidgets.QTextEdit)
          and dlg.game_tab._info_log.isReadOnly(),
          'type=%r' % (type(dlg.game_tab._info_log),))
    # I2 label pins run on a FRESH GameTab (the SMOKE-14 standalone
    # recipe): the singleton dlg is reused across PARTs, so after the
    # merged deferred-start drive a prior GO legitimately leaves live
    # status content on it. The placeholder contract belongs to fresh
    # construction, not to a mid-session tab.
    tab_fresh_i2 = game_window.GameTab(None)
    check("part I2: timer label '0:00' + required 'Required: -'",
          tab_fresh_i2._timer_label.text() == '0:00'
          and tab_fresh_i2._required_label.text() == 'Required: -',
          'timer=%r required=%r' % (tab_fresh_i2._timer_label.text(),
                                    tab_fresh_i2._required_label.text()))
    check("part I2: btn_hint exists with text 'Hint' (05-08 connected)",
          dlg.game_tab.btn_hint.text() == 'Hint',
          'text=%r' % (dlg.game_tab.btn_hint.text(),))

    # ---- I3: countdown drive -- steps AS METHODS; NO processEvents
    # gap (a real member-timer tick would shift _countdown_n) ----
    wiz_i = gamestart.start_game(activate=False)   # frozen DEFAULTS
    dlg.game_tab.start_countdown(wiz_i)
    check("part I3: start_countdown arms n=3 + 'Get ready...'",
          dlg.game_tab._countdown_n == 3
          and 'Get ready...' in dlg.game_tab._info_log.toPlainText(),
          'n=%r (a premature real tick would have shifted it)'
          % (dlg.game_tab._countdown_n,))
    check('part I3: countdown timer active, pending wizard stored',
          dlg.game_tab._countdown_timer.isActive()
          and dlg.game_tab._pending_wizard is wiz_i,
          'active=%r' % (dlg.game_tab._countdown_timer.isActive(),))
    for _ in range(4):
        dlg.game_tab._countdown_tick()
    lines_i = dlg.game_tab._info_log.toPlainText().splitlines()
    # 05-10 drive-contract evolution (the documented PART-letter
    # precedent -- the GO step's content contract changed the same way
    # PART G's did): _begin_play now OWNS the first level line, logged
    # right after 'GO!' (instant, ordered, no poll race). The five
    # start lines are still exact; the 6th must be the level line; the
    # format itself is WSL-pinned in status_text/smoke_14.
    check("part I3: log stepped 'Get ready...' '3' '2' '1' 'GO!'",
          lines_i[:5] == ['Get ready...', '3', '2', '1', 'GO!'],
          'lines=%r' % (lines_i,))
    check("part I3: 'GO!' is followed by the level line (05-10's "
          "_begin_play owns the first observation)",
          len(lines_i) == 6
          and lines_i[5].startswith('Level 1, molecule 1 of ')
          and lines_i[5].endswith('.'),
          'lines=%r' % (lines_i,))
    check('part I3: GO pushed THAT wizard, float anchor, 1 Hz on '
          '(P-1 closed)',
          cmd.get_wizard() is wiz_i
          and isinstance(engine._current_game().timer_anchor, float)
          and dlg.game_tab._timer.isActive(),
          'top=%r anchor=%r' % (cmd.get_wizard(),
                                engine._current_game().timer_anchor))

    # ---- I4: timer-label drive (deterministic anchor manipulation --
    # SMOKE-13 already proved the real cadence) ----
    engine._current_game().timer_anchor = time_mod.time() - 75
    dlg.game_tab._on_tick()
    check("part I4: _on_tick renders '1:15' from the LIVE anchor (P-4)",
          dlg.game_tab._timer_label.text() == '1:15',
          'label=%r' % (dlg.game_tab._timer_label.text(),))

    # ---- I5: cancel drive (P-2: a cancelled countdown NEVER fires GO)
    cmd.set_wizard()                   # done pop of wiz_i
    placement.cleanup_game_objects()
    wiz_i2 = gamestart.start_game(activate=False)
    dlg.game_tab.start_countdown(wiz_i2)
    dlg.game_tab.cancel_pending_start()
    check('part I5: cancel stops the timer + clears the pending wizard',
          not dlg.game_tab._countdown_timer.isActive()
          and dlg.game_tab._pending_wizard is None,
          'active=%r' % (dlg.game_tab._countdown_timer.isActive(),))
    dlg.game_tab._countdown_tick()     # one stray tick after the cancel
    text_i5 = dlg.game_tab._info_log.toPlainText()
    check("part I5: no 'GO!' after the cancel; NO stale activation "
          '(P-2 closed)',
          'GO!' not in text_i5
          and cmd.get_wizard() is not wiz_i2,
          'log=%r top=%r' % (text_i5, cmd.get_wizard()))

    # ---- restore: baseline scene EXACTLY + timers quiet ----
    dlg.game_tab.cancel_pending_start()
    dlg.game_tab._timer.stop()         # defensive: no 1 Hz tick over
    cmd.set_wizard()                   # the post-cleanup no-game state
    result_i = placement.cleanup_game_objects()
    check('part I: restore -- baseline scene EXACTLY, stack empty',
          cmd.get_wizard() is None
          and result_i['deleted'] > 0
          and cmd.get_names('objects') == baseline_i,
          'deleted=%r after=%r baseline=%r'
          % (result_i['deleted'], cmd.get_names('objects'),
             baseline_i))
    app.processEvents()
    dlg.close()
    REC['tab_shell'] = ('2 tabs, shell state, countdown 3-2-1-GO as '
                        "methods, '1:15' tick, cancel P-2, exact restore")
except Exception:
    traceback.print_exc()
    check('part I two-tab/GameTab shell drives', False,
          'raised (see traceback)')

# ============================================================
# PART J: PLAY-05 hint drive (05-08; T1b -- the 04-01 probe verdict is
# PASS (platform=offscreen), so the dialog portions RUN; cmd-substance
# + dialog asserts only, NO modals anywhere: the hint handler is
# NON-MODAL by design -- impls never own boxes -- and this part drives
# dlg.game_tab._hint_now directly. Every color read uses the pinned
# cmd.iterate recipe (SMOKE-07's _color_map precedent; wizard.py's
# _atom_colors mechanism)
# ============================================================
try:
    if setup_window is None:
        raise RuntimeError('part A failed')
    from pymol import cmd
    from pymol.Qt import QtWidgets
    from aamatch import capability, engine, gamestart, placement, wizard

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(['aamatch-smoke-11'])
    dlg = setup_window.open_window()   # singleton reuse
    baseline_j = cmd.get_names('objects')

    orange_idx = cmd.get_color_index('orange')
    green_idx = cmd.get_color_index('green')

    def _scene_color_maps():
        """{object: sorted [(ID, color, elem), ...]} for EVERY scene
        object -- the whole-scene color read-back (H-1's assert must
        cover hinted-never-selected objects, not just selected ones)."""
        maps = {}
        for obj in cmd.get_names('objects'):
            rows = []
            cmd.iterate(obj, 'stored.append((ID, color, elem))',
                        space={'stored': rows})
            maps[obj] = sorted((int(a), int(c), str(e))
                               for (a, c, e) in rows)
        return maps

    # ---- J1: pre-GO silent no-op via the dialog handler (H-8) ----
    wiz_j0 = gamestart.start_game(activate=False)
    dlg.game_tab.start_countdown(wiz_j0)   # P-1: wizard OFF the stack
    pre_j0 = _scene_color_maps()
    res_j0 = dlg.game_tab._hint_now()
    post_j0 = _scene_color_maps()
    check('part J1: pre-GO hint press is a SILENT no-op (H-8, P-1 held)',
          res_j0 is None and post_j0 == pre_j0
          and cmd.get_wizard() is None,
          'res=%r top=%r' % (res_j0, cmd.get_wizard()))
    dlg.game_tab.cancel_pending_start()
    dlg.game_tab._timer.stop()             # defensive: no 1 Hz ticking
    placement.cleanup_game_objects()
    check('part J1: the scratch game cleaned back to the baseline scene',
          cmd.get_names('objects') == baseline_j
          and cmd.get_wizard() is None,
          'names=%r' % (cmd.get_names('objects'),))

    # ---- J2: main drive -- cmd path and pure path AGREE ----
    wiz_j = gamestart.start_game()         # defaults: activate at once
    if not isinstance(wiz_j, wizard.GameWizard):
        raise RuntimeError('part J: start_game did not activate a '
                           'GameWizard (%r)' % (wiz_j,))
    mat_j = _scene_color_maps()            # materialization colors
    mol_j = wiz_j._payload['levels'][0]['molecules'][0]
    slots_j = mol_j['grid']['slots']
    required_j = mol_j['required']
    profile_j = engine.ligand_profile_molecule(0, 0)
    expected_j = capability.hint_candidate_slots(slots_j, profile_j,
                                                 required_j)
    res_j = wiz_j.hint()
    check('part J2: hint() returns the pure-computed candidate set '
          '(cmd path == pure path, DETECT-04 live)',
          res_j is not None
          and tuple(res_j['slot_ids']) == expected_j
          and res_j['count'] == len(expected_j)
          and len(expected_j) > 0,
          'count=%r expected=%s'
          % (res_j and res_j.get('count'), expected_j))
    req_j = tuple(sorted(s['slot_id'] for s in slots_j
                         if s.get('role') == 'required'))
    check('part J2: every role=required slot IS a candidate '
          '(GEN-04 parity, live recompute)',
          len(req_j) > 0
          and all(r in expected_j for r in req_j),
          'required=%s candidates=%s' % (req_j, expected_j))

    # ---- J3: carbon-only recolor on candidates; nothing else moved ----
    post_j = _scene_color_maps()
    cand_objs_j = tuple(sorted(wiz_j._objects_by_slot[s]
                               for s in expected_j))
    cand_set_j = set(cand_objs_j)
    carbons_ok = True
    for obj in cand_objs_j:
        pre_obj_j = dict((a, c) for (a, c, _e) in mat_j[obj])
        for (aid, col, elem) in post_j[obj]:
            if elem == 'C':
                if col != orange_idx:
                    carbons_ok = False
            elif col != pre_obj_j.get(aid):
                carbons_ok = False
    check('part J3: every candidate elem C atom reads HINT_COLOR '
          '(orange), non-carbons unchanged from pre-hint',
          carbons_ok, 'orange_index=%r' % (orange_idx,))
    others_ok = all(post_j[obj] == mat_j[obj] for obj in post_j
                    if obj not in cand_set_j)
    check('part J3: NON-candidates carry ZERO color change (ligand, '
          'distractor slots, the other molecule, the baseline scene '
          '-- H-5 closed)', others_ok, 'candidates=%r' % (cand_objs_j,))
    check('part J3: object NAMES unchanged (recolor only -- PLAY-04)',
          sorted(post_j) == sorted(mat_j), '')

    # ---- J4: repeated presses are idempotent (static candidate set) ----
    res_j4 = wiz_j.hint()
    post_j4 = _scene_color_maps()
    check('part J4: re-press is IDEMPOTENT (same set, same colors)',
          post_j4 == post_j and res_j4 is not None
          and tuple(res_j4['slot_ids']) == expected_j
          and res_j4['count'] == len(expected_j), '')

    # ---- J5: hint-over-green coexists per-atom (probe check 6) ----
    green_obj = cand_objs_j[0]
    cmd.color('green', green_obj)          # whole-object green first
    wiz_j.hint()                           # hint recolors carbons back
    gmap_j = _scene_color_maps()[green_obj]
    green_ok = True
    for (aid, col, elem) in gmap_j:
        if elem == 'C':
            if col != orange_idx:
                green_ok = False
        elif col != green_idx:
            green_ok = False
    check('part J5: hint-over-green coexists per-atom (orange carbons '
          '+ green non-carbons)', green_ok, 'obj=%r' % (green_obj,))

    # ---- J6: the tab handler returns the dict + logs the pinned line ----
    dlg.game_tab._info_log.clear()
    res_j6 = dlg.game_tab._hint_now()
    expect_line = ('Hint: %d eligible amino acid(s) highlighted.'
                   % len(expected_j))
    check('part J6: _hint_now returns the dict + logs the pinned hint '
          'line (wizard still active)',
          res_j6 is not None
          and res_j6['count'] == len(expected_j)
          and tuple(res_j6['slot_ids']) == expected_j
          and expect_line in dlg.game_tab._info_log.toPlainText(),
          'line=%r' % (expect_line,))

    # ---- J7: canonical Done restores the WHOLE scene (ONE store) ----
    cmd.set_wizard()                       # canonical Done pop
    done_j = _scene_color_maps()
    check('part J7: Done restores EVERY color map to materialization '
          'colors (hinted-never-selected objects too -- the (a) trap '
          'closed, H-1)',
          done_j == mat_j, '')
    check('part J7: the ONE store is cleared + the stack is empty',
          wiz_j._color_store == {} and cmd.get_wizard() is None,
          'store=%r top=%r' % (wiz_j._color_store, cmd.get_wizard()))
    result_j = placement.cleanup_game_objects()
    check('part J7: baseline scene EXACTLY after prefix-only cleanup',
          result_j['deleted'] > 0
          and cmd.get_names('objects') == baseline_j,
          'deleted=%r after=%r baseline=%r'
          % (result_j['deleted'], cmd.get_names('objects'), baseline_j))
    app.processEvents()
    dlg.close()
    REC['hint'] = ('pre-GO no-op, pure/cmd agreement (count %d), '
                   'carbon-only recolor, idempotence, hint-over-green, '
                   'pinned log line, whole-scene Done restore'
                   % len(expected_j))
except Exception:
    traceback.print_exc()
    check('part J PLAY-05 hint drive', False, 'raised (see traceback)')

# ============================================================
# PART K: Gate A2 shape sanity inside PyMOL's interpreter (ALWAYS)
# ============================================================
try:
    init_path = os.path.join(_ROOT, 'aamatch', '__init__.py')
    with open(init_path, 'rb') as f:
        init_lines = f.read().decode('utf-8').splitlines()
    offenders = [ln for ln in init_lines
                 if ln and not ln[0].isspace() and not ln.startswith('#')
                 and (ln.startswith('import ') or ln.startswith('from '))]
    check('part K: Gate A2 shape -- zero column-0 import/from lines',
          not offenders, 'offenders=%r' % (offenders,))
except Exception:
    traceback.print_exc()
    check('part K Gate A2 echo', False, 'raised (see traceback)')

# --- evidence summary -------------------------------------------------
print('SMOKE-ENV record: %s'
      % dict((k, v) for k, v in sorted(REC.items())), flush=True)

# --- Verdict marker (the SOLE verdict carrier) ------------------------
print('=== SMOKE-11 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
