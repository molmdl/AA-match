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
        the spec-order labels via text(); processEvents; finish
        dlg.close(). ZERO modals (PITFALL P5): no .exec_(), no
        QFileDialog, no QMessageBox anywhere in this script.
PART C  (ALWAYS, T0-in-smoke): Gate A2 shape sanity echoed inside
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
    app.processEvents()
    dlg.close()
    REC['dialog'] = '%r' % (type(dlg),)
except Exception:
    traceback.print_exc()
    check('part B widget-construction tier', False,
          'raised (see traceback)')

# ============================================================
# PART C: Gate A2 shape sanity inside PyMOL's interpreter (ALWAYS)
# ============================================================
try:
    init_path = os.path.join(_ROOT, 'aamatch', '__init__.py')
    with open(init_path, 'rb') as f:
        init_lines = f.read().decode('utf-8').splitlines()
    offenders = [ln for ln in init_lines
                 if ln and not ln[0].isspace() and not ln.startswith('#')
                 and (ln.startswith('import ') or ln.startswith('from '))]
    check('part C: Gate A2 shape -- zero column-0 import/from lines',
          not offenders, 'offenders=%r' % (offenders,))
except Exception:
    traceback.print_exc()
    check('part C Gate A2 echo', False, 'raised (see traceback)')

# --- evidence summary -------------------------------------------------
print('SMOKE-ENV record: %s'
      % dict((k, v) for k, v in sorted(REC.items())), flush=True)

# --- Verdict marker (the SOLE verdict carrier) ------------------------
print('=== SMOKE-11 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'),
      flush=True)
