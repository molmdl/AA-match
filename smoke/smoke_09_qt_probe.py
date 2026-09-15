"""Headless SMOKE-09 - offscreen-Qt widget-construction probe (research Q1).

Settles open question Q1 of
.planning/phases/04-qt-setup-window/04-RESEARCH-qt-window-architecture.md
(§verification_tiers): whether widget CONSTRUCTION (QApplication + QDialog)
works in the Windows conda PyMOL 2.5.0 env (PyQt5 5.12.3 / Qt 5.12.9) under
QT_QPA_PLATFORM=offscreen, falling back to the default platform.
`import pymol.Qt` headless is already PROVEN (T1a, v1 smokes executed
module-level Qt imports under `-cq`), but `-cq` builds no QApplication, so
construction is the open question. The verdict rewrites the verify tiers
of plans 04-05..04-13 (T1b available vs degrade to T1a + [HUMAN]).

Run (from WSL, repo root):  bash smoke/run_smoke.sh smoke/smoke_09_qt_probe.py 120
Verdict carrier: `=== PROBE PASS (platform=offscreen) ===` or
`=== PROBE PASS (platform=default) ===` or `=== PROBE FAIL ===`; on any
PASS, `=== SMOKE-09 PASS ===` is printed as the FINAL line (run_smoke.sh
derives NN=09 from the basename and greps exactly that - exit codes
cannot carry verdicts through cmd.exe).

PROBE HYGIENE (PITFALL P5): ZERO modals anywhere - no .exec_(), no
QFileDialog, no QMessageBox. Construct -> show -> processEvents -> soft
visibility assert only. The probe needs no aamatch import, so the
smoke_01-style repo-root anchor (sys.argv/cwd fallback; __file__ is
unusable in -cq scripts per 01-07) is intentionally omitted.

Python-3.6 syntax floor (Gate D): %-formatting only, no f-strings.
Every print stays on ONE line except failure tracebacks (smoke_01
precedent).
"""
import os
import traceback

# --- PART A preamble: the platform env var MUST be set BEFORE any Qt import
# (the QPA platform is chosen when the QApplication is constructed; setting
# the env var at the top of the script before the import is the documented
# probe order, 04-RESEARCH §verification_tiers Q1). Offscreen is tried
# FIRST; the default platform is the PART B fallback.
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Qt comes via the pymol.Qt wrapper shim ONLY - `from PyQt5 import ...` is
# banned repo-wide (binding order pymol-src/Qt/__init__.py:24-64).
# QtCore is imported with QtWidgets as the unit per the plan's probe shape.
from pymol.Qt import QtWidgets, QtCore  # noqa: E402


def _construct_and_check(platform):
    """The identical construct sequence run by both probe parts.

    Construction success is the verdict - not pixel visibility (offscreen
    visibility semantics may differ; a failed visibility assert is noted
    and the round-trip check still runs).
    """
    # Reuse-or-create, exactly the shape 04-RESEARCH §verification_tiers
    # Q1 specifies.
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(['aamatch-qt-probe'])
    dlg = QtWidgets.QDialog()
    dlg.setMinimumWidth(420)
    layout = QtWidgets.QVBoxLayout(dlg)
    layout.addWidget(QtWidgets.QLabel('probe'))
    layout.addWidget(QtWidgets.QPushButton('probe'))
    dlg.show()
    app.processEvents()
    if not dlg.isVisible():
        # SOFT assert: construction succeeded, so the probe continues to
        # the round-trip check; only the visibility note is printed.
        print('%s: visible-assert failed (isVisible() False after show())' % platform)
    # Mini round-trip: proves the widgets are live signal/slot objects,
    # not mere shells (QSpinBox set/read-back + QCheckBox toggle).
    spin = QtWidgets.QSpinBox()
    spin.setRange(1, 10)
    spin.setValue(7)
    if spin.value() != 7:
        raise RuntimeError('%s: QSpinBox round-trip failed (value()=%r)' % (platform, spin.value()))
    check = QtWidgets.QCheckBox('probe')
    check.toggle()
    if not check.isChecked():
        raise RuntimeError('%s: QCheckBox round-trip failed (isChecked() False after toggle)' % platform)
    app.processEvents()


_verdict = None

print('PROBE attempt: QT_QPA_PLATFORM=offscreen')
try:
    _construct_and_check('offscreen')
    _verdict = 'offscreen'
except Exception as exc:     # any failure routes to the PART B fallback
    _err_offscreen = '%s: %s' % (type(exc).__name__, exc)
    print('offscreen: construction failed (%s)' % _err_offscreen)
    traceback.print_exc()
    # PART B - default platform fallback. Retried WITHOUT the env var so
    # the default windows platform is used (cmd.exe inherits the
    # interactive desktop session).
    os.environ.pop('QT_QPA_PLATFORM', None)
    # LIMITATION (recorded): if PART A already created a QApplication,
    # QApplication.instance() still returns it (a process singleton), so
    # PART B then re-uses that app rather than constructing a fresh
    # default-platform one. In practice an offscreen failure happens
    # AT app construction, leaving no instance behind.
    print('PROBE attempt: QT_QPA_PLATFORM unset (default platform)')
    try:
        _construct_and_check('default')
        _verdict = 'default'
    except Exception as exc2:    # both platforms failed - the FAIL verdict
        _err_default = '%s: %s' % (type(exc2).__name__, exc2)
        traceback.print_exc()
        print('PROBE offscreen error: %s' % _err_offscreen)
        print('PROBE default error: %s' % _err_default)
        # NO SMOKE-09 marker on FAIL - run_smoke.sh's grep fails, which
        # is the correct verdict carrier.
        print('=== PROBE FAIL ===')

if _verdict is not None:
    print('=== PROBE PASS (platform=%s) ===' % _verdict)
    # run_smoke.sh grep contract: FINAL line, exactly this marker.
    print('=== SMOKE-09 PASS ===')
