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
        'demo-dev-1'; processEvents; finish dlg.close(). ZERO modals
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
PART D  (ALWAYS, T0-in-smoke): Gate A2 shape sanity echoed inside
        PyMOL's interpreter for the record -- aamatch/__init__.py
        carries ZERO column-0 import/from statements (the lazy-import
        discipline the menu rewire must preserve).

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
# PART D: Gate A2 shape sanity inside PyMOL's interpreter (ALWAYS)
# ============================================================
try:
    init_path = os.path.join(_ROOT, 'aamatch', '__init__.py')
    with open(init_path, 'rb') as f:
        init_lines = f.read().decode('utf-8').splitlines()
    offenders = [ln for ln in init_lines
                 if ln and not ln[0].isspace() and not ln.startswith('#')
                 and (ln.startswith('import ') or ln.startswith('from '))]
    check('part D: Gate A2 shape -- zero column-0 import/from lines',
          not offenders, 'offenders=%r' % (offenders,))
except Exception:
    traceback.print_exc()
    check('part D Gate A2 echo', False, 'raised (see traceback)')

# --- evidence summary -------------------------------------------------
print('SMOKE-ENV record: %s'
      % dict((k, v) for k, v in sorted(REC.items())), flush=True)

# --- Verdict marker (the SOLE verdict carrier) ------------------------
print('=== SMOKE-11 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
