"""Headless SMOKE-13 - Qt timer + tab mechanics probe (Phase-5 research Q6).

Settles the Phase-5 open question: does QTimer work under
QT_QPA_PLATFORM=offscreen in the Windows conda PyMOL 2.5.0 env
(PyQt5 5.12.3 / Qt 5.12.9)? Phase 5 needs, headlessly:
  1. a repeating QTimer member firing while a processEvents pumping
     loop runs (the 1 Hz elapsed-timer render pattern);
  2. QTimer.singleShot(0, fn) firing on the next processEvents
     (deferred GO-step delivery);
  3. a delayed singleShot firing only after real wall time has passed
     (the 3-2-1 countdown step cadence);
  4. QTabWidget addTab + setCurrentWidget round-trip (the Setup/Game
     tab restructure mechanic);
  5. QApplication.activeModalWidget() exists and returns None when no
     modal child is open (the timer-fairness pause predicate);
  6. QTimer.stop() cancels pending firings (the cancellable-countdown
     design: a member QTimer, unlike an uncancellable singleShot chain).

PROBE HYGIENE (PITFALL P5): ZERO modals anywhere - no .exec_(), no
QFileDialog, no QMessageBox. Everything is construct -> show/pump ->
processEvents -> plain asserts. No aamatch import, so the repo-root
anchor is intentionally omitted (smoke_09 precedent).

Run (from WSL, repo root):  bash smoke/run_smoke.sh smoke/smoke_13_qt_timer_probe.py 120
Verdict carrier: `=== PROBE PASS (platform=offscreen) ===` (or
`=== PROBE PASS (platform=default) ===` fallback); on any PASS,
`=== SMOKE-13 PASS ===` is printed as the FINAL line (run_smoke.sh
greps exactly that; exit codes cannot carry verdicts through cmd.exe).

Python-3.6 syntax floor (Gate D): %-formatting only, no f-strings.
"""
import os
import time
import traceback

# --- the platform env var MUST be set BEFORE any Qt import (QPA is
# chosen at QApplication construction; smoke_09 documented order).
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Qt comes via the pymol.Qt wrapper shim ONLY - `from PyQt5 import ...`
# is banned repo-wide.
from pymol.Qt import QtWidgets, QtCore  # noqa: E402


def _pump(app, seconds):
    """Pump the event loop for `seconds` REAL seconds (timers only fire
    while the event loop runs; processEvents dispatches DUE timer
    events)."""
    t0 = time.time()
    while time.time() - t0 < seconds:
        app.processEvents()
        time.sleep(0.01)


def _run_checks(platform):
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(['aamatch-timer-probe'])

    # --- check 1: repeating QTimer member fires while pumping ---
    hits = []
    timer = QtCore.QTimer()
    timer.setInterval(200)
    timer.timeout.connect(lambda: hits.append(time.time()))
    timer.start(200)
    _pump(app, 0.7)
    timer.stop()
    if len(hits) < 2:
        raise RuntimeError(
            'QTimer repeat: expected >=2 firings in 0.7 s at 200 ms, '
            'got %d' % len(hits))
    print('%s: check1 repeat-QTimer OK (%d firings in ~0.7 s)'
          % (platform, len(hits)))

    # --- check 6: stop() cancels pending firings ---
    before = len(hits)
    timer.start(200)
    timer.stop()          # stop immediately after start: nothing fires
    _pump(app, 0.5)
    if len(hits) != before:
        raise RuntimeError(
            'QTimer.stop() did not cancel pending firings (before=%d '
            'after=%d)' % (before, len(hits)))
    print('%s: check6 stop-cancels OK' % platform)

    # --- check 2: singleShot(0) fires on the next processEvents ---
    flag = []
    QtCore.QTimer.singleShot(0, lambda: flag.append(True))
    if flag:
        raise RuntimeError('singleShot(0) fired before processEvents')
    app.processEvents()
    if not flag:
        raise RuntimeError('singleShot(0) did not fire on processEvents')
    print('%s: check2 singleShot(0) OK' % platform)

    # --- check 3: delayed singleShot fires only after real time ---
    late = []
    QtCore.QTimer.singleShot(300, lambda: late.append(time.time()))
    _pump(app, 0.1)
    if late:
        raise RuntimeError('singleShot(300) fired after only ~0.1 s')
    _pump(app, 0.4)
    if not late:
        raise RuntimeError('singleShot(300) never fired within 0.5 s')
    print('%s: check3 delayed-singleShot OK' % platform)

    # --- check 4: QTabWidget addTab + setCurrentWidget round-trip ---
    tabs = QtWidgets.QTabWidget()
    setup_page = QtWidgets.QWidget()
    game_page = QtWidgets.QWidget()
    tabs.addTab(setup_page, 'Setup')
    tabs.addTab(game_page, 'Game status')
    if tabs.indexOf(game_page) != 1:
        raise RuntimeError('QTabWidget.addTab index mismatch')
    tabs.setCurrentWidget(game_page)
    if tabs.currentWidget() is not game_page:
        raise RuntimeError('setCurrentWidget round-trip failed')
    if not game_page.isVisible():
        # SOFT note: offscreen visibility semantics may differ; the
        # currentWidget identity is the binding assert.
        print('%s: note game_page isVisible() False (offscreen semantics)'
              % platform)
    app.processEvents()
    print('%s: check4 QTabWidget round-trip OK' % platform)

    # --- check 5: activeModalWidget predicate exists, None w/o modal ---
    if not callable(QtWidgets.QApplication.activeModalWidget):
        raise RuntimeError('QApplication.activeModalWidget missing')
    modal = QtWidgets.QApplication.activeModalWidget()
    if modal is not None:
        raise RuntimeError(
            'activeModalWidget() returned %r with no modal open'
            % (modal,))
    print('%s: check5 activeModalWidget predicate OK (None w/o modal)'
          % platform)


_verdict = None

print('PROBE attempt: QT_QPA_PLATFORM=offscreen')
try:
    _run_checks('offscreen')
    _verdict = 'offscreen'
except Exception as exc:
    _err_offscreen = '%s: %s' % (type(exc).__name__, exc)
    traceback.print_exc()
    print('offscreen: checks failed (%s)' % _err_offscreen)
    # Fallback: retry WITHOUT the env var (default platform) -- the
    # same smoke_09 degradation shape.
    os.environ.pop('QT_QPA_PLATFORM', None)
    print('PROBE attempt: QT_QPA_PLATFORM unset (default platform)')
    try:
        _run_checks('default')
        _verdict = 'default'
    except Exception as exc2:
        traceback.print_exc()
        print('=== PROBE FAIL ===')

if _verdict is not None:
    print('=== PROBE PASS (platform=%s) ===' % _verdict)
    # run_smoke.sh grep contract: FINAL line, exactly this marker.
    print('=== SMOKE-13 PASS ===')
