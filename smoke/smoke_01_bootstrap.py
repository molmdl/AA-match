"""Headless smoke 01 - plugin skeleton loads under real Windows PyMOL.

Run (from WSL, repo root):  bash smoke/run_smoke.sh smoke/smoke_01_bootstrap.py
Verdict is carried by the printed marker (exit codes cannot carry verdicts
through the cmd.exe wrapper): grep '=== SMOKE-01 PASS ==='.

Parts:
  A - direct import of `aamatch` (module identity 'aamatch') + direct
      __init_plugin__ call (headless: EXPECTS QtNotAvailableError).
  B - real loader path: startup.__path__.append(repo_root) + plugin_load
      (module identity 'pmg_tk.startup.aamatch'; loaded=True even with the
      Qt warning, plugins/__init__.py:287-300).
  C - one-time Windows env record (transcribed into
      .planning/phases/01-bootstrap-pure-foundation/windows-env-versions.md).
  D - cmd.load path probes (forward-slash form; backslash form with a space
      in the dirname). RECORD-ONLY: results never enter `failures`
      (closes pure-foundation OQ4/OQ7 without gating Phase 1).

Python-3.6 floor: this file RUNS INSIDE PyMOL's Windows Python (3.6+).
Every print stays on ONE line (the runner tees + tails; multi-line prints
complicate grepping).
"""
import os
import sys
import traceback


def winpath(p):
    # Mirror of aamatch.paths.to_windows_path for SELF-bootstrap only.
    # Deliberately NOT importing aamatch.paths: this smoke bootstraps the
    # aamatch package itself, so going through it would be circular.
    if p.startswith('/mnt/') and len(p) > 6:
        drive = p[5]
        rest = p[6:]
        if drive.isalpha() and rest.startswith('/'):
            return drive.upper() + ':\\' + rest[1:].replace('/', '\\')
    return p


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__.

    DISCOVERY (2026-09-06, headless probe against Windows PyMOL 2.5.0,
    chemtools-win10 env): inside a -cq script __file__ EXISTS but points at
    pymol/__init__.py (the launcher), NOT at this script - so the v1-style
    `'__file__' in dir()` guard (PA phase11_gui_diag.py:33) is NOT sufficient.
    Anchor order instead:
      1. a sys.argv entry naming this script (absolute or cwd-relative);
      2. os.getcwd() - the frozen runner cds to the repo root before
         launching cmd.exe and PyMOL inherits that cwd (probe-proven).
    """
    mine = 'smoke_01_bootstrap.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            # <root>/smoke/<script> -> <root>  (repo root = package parent)
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT)

failures = []


def check(name, cond, detail=''):
    print('SMOKE-01 %-38s %s %s' % (name, 'PASS' if cond else 'FAIL', detail))
    if not cond:
        failures.append(name)


# --- Part A: direct import (module identity 'aamatch') ----------------------
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
try:
    import aamatch
    check('import aamatch', aamatch.__version__ == '0.1.0', aamatch.__version__)
    try:
        aamatch.__init_plugin__(None)              # headless: expect QtNotAvailableError
        check('init_plugin direct', False, 'expected QtNotAvailableError')
    except ImportError as e:
        check('init_plugin direct', False, repr(e))    # anything else is a real bug
    except Exception as e:
        from pymol.plugins import QtNotAvailableError
        check('init_plugin direct', isinstance(e, QtNotAvailableError), repr(e))
except Exception:
    traceback.print_exc()
    check('import aamatch', False, 'import raised')

# --- Part B: real loader path (module identity 'pmg_tk.startup.aamatch') ----
try:
    import pymol.plugins as P
    rootw = winpath(_ROOT)
    if rootw not in P.startup.__path__:
        # Same mechanism the loader itself uses for $PYMOL_DATA/startup
        # (plugins/__init__.py:38). Transient: this PyMOL process only.
        P.startup.__path__.append(rootw)
    P.plugin_load('aamatch')            # auto-initialize(-2) on empty registry
    info = P.plugins.get('aamatch')
    check('loader registered', info is not None)
    check('loader module', bool(info and info.module is not None))
    # Headless, legacyinit raises QtNotAvailableError; the loader catches it,
    # prints the 'only available with PyQt GUI' warning, and load() STILL
    # returns True (installed 2.5.0 plugins/__init__.py:287-302).
    # DISCOVERY (2026-09-06 headless probe): the `loaded` PROPERTY stays
    # False on that path - loadtime is only set on the fully-successful
    # branch - so assert the loader's own load() verdict, not the property.
    check('loader loaded', bool(info and info.load()))
    check('loader name', bool(info) and info.name == 'aamatch')
except Exception:
    traceback.print_exc()
    check('loader path', False, 'loader raised (see traceback above)')

# --- Part C: one-time env record (transcribed into windows-env-versions.md) --
print('SMOKE-ENV python:', sys.version.replace('\n', ' '))
print('SMOKE-ENV executable:', sys.executable)
try:
    import pymol.Qt
    print('SMOKE-ENV qt_binding:', pymol.Qt.PYQT_NAME)
    from pymol.Qt import QtCore
    print('SMOKE-ENV qt_version:', QtCore.QT_VERSION_STR)
    if hasattr(QtCore, 'PYQT_VERSION_STR'):
        print('SMOKE-ENV pyqt_version:', QtCore.PYQT_VERSION_STR)
except Exception as exc:    # headless Qt import must not kill the run (verify, don't assume)
    print('SMOKE-ENV qt: UNAVAILABLE headless (%r)' % (exc,))
from pymol import cmd
print('SMOKE-ENV pymol:', cmd.get_version()[0])
try:
    import numpy
    print('SMOKE-ENV numpy:', numpy.__version__)
except ImportError:
    print('SMOKE-ENV numpy: MISSING')

# --- Part D: cmd.load path probes (RECORD-ONLY: never added to failures) ----
# Closes pure-foundation OQ4 (forward-slash acceptance) / OQ7 (paths with
# spaces). Record-only rationale: to_windows_path already outputs the proven
# backslash form, so a probe failure is not a Phase-1 blocker - it is an
# answer, not a failure.
fixdir = os.path.join(_ROOT, 'tmp', 'smoke fixtures')   # space in dirname = probe 2
if not os.path.isdir(fixdir):
    os.makedirs(fixdir)
fixture = os.path.join(fixdir, 'min.pdb')
pdb_line = 'ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\n'
with open(fixture, 'w') as fh:
    fh.write(pdb_line + 'END\n')
bs = os.path.join(winpath(_ROOT), 'tmp', 'smoke fixtures', 'min.pdb')  # backslash + spaces

# Probe 1 - forward-slash form of the same Windows path.
try:
    cmd.load(bs.replace('\\', '/'))
    n = cmd.count_atoms('min')
    if n >= 1:
        print('SMOKE-ENV probe fwdslash-load: OK (n=%d)' % n)
    else:
        print('SMOKE-ENV probe fwdslash-load: FAILED (count_atoms=0)')
except Exception as exc:
    print('SMOKE-ENV probe fwdslash-load: FAILED (%r)' % (exc,))
cmd.delete('min')

# Probe 2 - backslash form WITH SPACES in the dirname.
try:
    cmd.load(bs)
    n = cmd.count_atoms('min')
    if n >= 1:
        print('SMOKE-ENV probe spacepath-load: OK (n=%d)' % n)
    else:
        print('SMOKE-ENV probe spacepath-load: FAILED (count_atoms=0)')
except Exception as exc:
    print('SMOKE-ENV probe spacepath-load: FAILED (%r)' % (exc,))
cmd.delete('min')

# --- Verdict marker (the SOLE verdict carrier) -------------------------------
print('=== SMOKE-01 %s ===' % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'))
