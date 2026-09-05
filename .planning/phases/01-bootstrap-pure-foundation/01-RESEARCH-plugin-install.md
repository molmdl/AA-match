# Phase 1 Research — Plugin Skeleton, Installation & Headless Toolchain Proof

**Researched:** 2026-09-05 (all citations read from local sources the same day)
**Scope:** Plugin package contract, install path, headless smoke proof, version recording. (Pure-foundation modules — persistence / level-spec / backup — are covered by `01-RESEARCH-pure-foundation.md`.)
**Confidence:** HIGH for everything cited to the PyMOL 2.5.0 source tree (`pymol-src` → `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/bioCHEMeleon/tmp/pymol-src/modules/`). Windows-runtime specifics flagged explicitly.

> **Citation convention:** bare `file:line` = `<pymol-src>/modules/pymol/<file>`.
> `pmg_qt/...` = `<pymol-src>/modules/pmg_qt/<file>`. `PA` = prior art
> `tmp/bioCHEMeleon/` (= `../bioCHEMeleon/pymol/`). The repo itself is readable
> from Windows at `C:\Users\nglok\Desktop\WORKDIR\molmdl\AA-match\...` — this
> fact is load-bearing for the no-staging smoke design (§3.1).

---

## 1. Verified Facts

### 1.1 What the Plugin Manager accepts (installation contract)

| Fact | Citation |
|---|---|
| `installPluginFromFile(ofile, parent, plugdir)` is the single install entry point | `plugins/installation.py:186` |
| Accepted file types: `.py` files and `.zip` / `.tar.gz` archives (`zip_extensions = ['zip','tar.gz']`) | `installation.py:13-14` |
| **Directory install:** point the file dialog at the package's `__init__.py`; the whole dir is `shutil.copytree`'d to the destination | `installation.py:299-308`; dialog hint "to install a directory, point to its __init__.py file" at `plugins/legacysupport.py:60` |
| Zip must contain **exactly one package**: either `zip/<name>/__init__.py` (case 1) or `zip/<name>-<version>/<name>/__init__.py` (case 2); otherwise `BadInstallationFile('Missing __init__.py')` / `'Archive must contain a single package.'` | `installation.py:118-136` |
| Zip case-2 automatically filters out a top-level `tests` directory | `installation.py:132-133` |
| Zip absolute/escaping paths rejected | `installation.py:101-107` |
| Module name derived by regex `(\w+).*\.(py\|zip\|tar\.gz)$` → `aamatch-0.1.0.zip` installs as module `aamatch`; name must not contain dots | `installation.py:64-88` |
| Destination = the selected startup path; if **more than one** startup path exists the user gets a selection dialog (Qt `QInputDialog` when `pmg_qt.mimic_tk` loaded) | `installation.py:145-161, 203-208` |
| If the chosen dir is **not writable**, PyMOL offers to create the user dir `%APPDATA%\pymol\startup` (`get_default_user_plugin_path()`; `~/.pymol/startup` on Linux) and prepends it to the path list | `installation.py:22-29, 210-229` |
| New startup paths are **persisted** via `set_startup_path` → autosaved to `~/.pymolpluginsrc.py` (`pref_save` writes `set_startup_path([...], False)`) | `plugins/__init__.py:55-59, 70-97, 228-229 (installation.py)` |
| Reinstall flow: version compare from `# Version:` metadata using `distutils.version.StrictVersion` → "Reinstall?" prompt → old dir `rmtree`d → copy | `installation.py:44-62, 231-274` |
| After copying, plugin is loaded **immediately in-session**: `info.load(force=1)` → Success / "installed but initialization failed" dialogs | `installation.py:339-345` |
| Uninstall: per-plugin button in Plugin Manager → confirm → `shutil.rmtree` (packages) → "Please restart PyMOL" | `plugins/__init__.py:326-363`; button wired `plugins/managergui_qt.py:238` |
| Qt Plugin Manager: opened via Plugins → Plugin Manager (`addPluginManagerMenuItem`, `legacysupport.py:72-88`); the **"Install from local file"** button `b_local` → `installplugin()` → `installPlugin` (file dialog) → `installPluginFromFile` | `plugins/managergui_qt.py:45, 301-304`; `legacysupport.py:52-68` |
| The file dialog offers only `*.py` + archives — **there is no "pick a directory" mode**; directory installs go through selecting `__init__.py` | `legacysupport.py:61-66` |

### 1.2 How plugins are discovered / imported (loader)

| Fact | Citation |
|---|---|
| `findPlugins` scans each startup path for `.py` files **and directories containing `__init__.py`**; entries whose name starts with `.` or `_` are skipped; first-found wins per name ("warning: multiple plugins named") | `plugins/__init__.py:365-405` (skip rule `:384-385`, first-wins `:391-401`) |
| The plugin parent package is **`pmg_tk.startup`** (legacy name kept in the Qt build): plugins import as `pmg_tk.startup.aamatch` | `plugins/__init__.py:427` (`mod_name = parent.__name__ + '.' + name`); `plugins/legacysupport.py:17` (`from pmg_tk import startup`) |
| `startup.__path__` gets `$PYMOL_DATA/startup` appended when the plugins module is imported; user dirs are added via the saved prefs file or the install flow | `plugins/__init__.py:38-39` |
| Loading = `__import__(mod_name, level=0)`; a `force` reload uses `importlib.reload` | `plugins/__init__.py:273-277` |
| After import, `legacyinit(pmgapp)` calls **`mod.__init_plugin__(pmgapp)`** (a legacy module-level `__init__` *function* is the fallback) | `plugins/__init__.py:302-324` (`:320-321` for `__init_plugin__`) |
| During load, `cmd.extend` is wrapped so registered commands are recorded in `info.commands` | `plugins/__init__.py:266-270, 282` |
| **Quirk:** on the `QtNotAvailableError` path `cmd.extend` is NOT restored (the restore line `:282` is skipped) — the wrapper stays installed harmlessly. Keep `addmenuitemqt` as the *first* statement of `__init_plugin__` so it raises before any `cmd.extend` | `plugins/__init__.py:266-288` |
| `addmenuitemqt(label, command)` raises `QtNotAvailableError` when `HAVE_QT` is False; `HAVE_QT` starts False and is set True **only** by the Qt GUI | `plugins/__init__.py:29, 100-108`; set True at `pmg_qt/pymol_qt_gui.py:972` |
| A generic exception during load prints `Unable to initialize plugin '<name>'` and returns False — **a broken plugin never crashes PyMOL startup**, the menu item is simply missing | `plugins/__init__.py:289-298` |
| Metadata block: `# Key: value` comment lines at the **very top** of `__init__.py`; parsing stops at the first non-`#` line; recognized keys include `Version` (fallback: module `__version__`) and `Citation-Required: Yes` (install-time citation prompt) | `plugins/__init__.py:193-210, 212-228`; `installation.py:347-352` |
| `# Version:` must be StrictVersion-compatible (`X.Y.Z`) or `cmp_version` warns and returns 0 | `installation.py:44-62` |
| Local verification (2026-09-05, WSL python3.6): a file starting with `# Version: 0.1.0` / `# Citation-Required: No` comment lines **followed by** a docstring parses metadata correctly *and* still yields the docstring as `co_consts[0]` (so Plugin Manager "Info" shows it) | `plugins/__init__.py:193-210` + `plugins/__init__.py:230-246` (`get_docstring`), locally executed |
| `plugin_load <name>` cmd loads a plugin on demand; if the registry is empty it first runs `initialize(-2)` (scan, no autoload); an already-loaded plugin is a no-op ("plugin already loaded") | `plugins/__init__.py:130-145, 433` |

### 1.3 When `__init_plugin__` actually runs (startup-mode matrix) — the load-bearing discovery

| Mode | `options.plugins` | Plugin scan/autoload | `__init_plugin__` called? | `HAVE_QT` |
|---|---|---|---|---|
| GUI launch (normal) | 2 (default, `invocation.py:165`) | Yes — `window.initializePlugins()` after window show, then `app.exec_()` | **Yes** (autoload + legacyinit with real pmgapp) | True (`pymol_qt_gui.py:972-973`) |
| Headless `-cq` | 2 | **No** — nothing calls `initialize*`; `pymol.plugins` isn't even imported at startup (`pymol/__init__.py:365-371` imports it only when `external_gui in (1,3)`) | **No** | False |
| `-k` flag (any mode) | **0** (`invocation.py:481-483`) | **Never** | No | — |
| deferred `initialize(-1)` | only if `==1` (`invocation.py:523-525`) | no CLI path sets 1 (searched — only `=2` at `:165` and `=0` at `:483`) | import-only, no legacyinit | — |

Citations: `pymol_qt/pymol_qt_gui.py:1245-1249` (GUI: `if options.plugins: window.initializePlugins()`), `pymol_qt/pymol_qt_gui.py:956-973` (clears Plugin menu, adds Plugin Manager item, `HAVE_QT = True`, `plugins.initialize(app)`), `pymol/__init__.py:365-371`, `invocation.py:165, 477-488, 523-525`.

**Consequences for Phase 1:**

1. The headless smoke **cannot rely on startup autoload** — the smoke script must trigger the load itself (see §3).
2. `-cq` headless `plugin_load('aamatch')` → `info.load()` → `get_pmgapp()` lazily builds a **fake pmgapp whose `menuBar` methods are no-ops** (`pymol/gui.py:20-26, 38-40`; `legacysupport.py:113-127`). Even the non-Qt `addmenuitem` silently no-ops headless. **Menu registration is NOT assertable headlessly — by design. It is exactly what the [HUMAN] INSTALL-01 checkpoint proves.**
3. Headless, `addmenuitemqt` raises `QtNotAvailableError`, which `PluginInfo.load` catches and turns into the warning `Plugin 'aamatch' only available with PyQt GUI.` — and **still returns True** (`plugins/__init__.py:287-288, 300`). So a headless `plugin_load` of the skeleton is "clean" in the exit-code sense while visibly skipping menu wiring.

### 1.4 Menu structure in the Qt GUI (what the human will see)

- `initializePlugins` clears the Plugin menu, adds "Plugin Manager" + separator, then **aliases** `menudict['PluginQt'] = menudict['Plugin']` and demotes the legacy content to a "Legacy Plugins" submenu (`pmg_qt/pymol_qt_gui.py:960-970`).
- Therefore `addmenuitemqt('AA-match', cb)` places **AA-match directly in the top-level Plugins menu**, below Plugin Manager — exactly what INSTALL-01 requires. Sub-menu nesting is available via `'A|B'` labels if ever needed (`plugins/__init__.py:111-128`).
- Menu item label is independent of the package/module name: package `aamatch`, label `AA-match`.

### 1.5 Prior-art entry point (verified shape to adapt)

`PA biochemeleon/__init__.py:129-153`:

```python
def __init_plugin__(app=None):
    from pymol.plugins import addmenuitemqt          # local import, deliberate
    addmenuitemqt('bioCHEMeleon', run_plugin_gui)

def run_plugin_gui():
    global dialog
    if dialog is None:
        dialog = PluginDialog()
    dialog.show()                                    # modeless, NEVER .exec_()
```

(Qt import at `:156` is module-level in v1 — do **not** copy that; PITFALLS.md Pitfall 1 requires lazy Qt imports. Phase 1 needs no Qt at all — §2.2.)

### 1.6 Version-recording hooks (what to record, verified APIs)

| What | API | Citation |
|---|---|---|
| PyMOL version | `cmd.get_version()` → 6-tuple; `[0]` = version text | `querying.py:603-618` |
| Qt binding name | `import pymol.Qt; pymol.Qt.PYQT_NAME` (`'PyQt5'` expected) | `Qt/__init__.py:13, 26-32` |
| Qt version | `QtCore.QT_VERSION_STR` (native on PyQt5; the wrapper *maps* it for PySide — so it is safe cross-binding) | `Qt/__init__.py:84-94` |
| PyQt5 version | `QtCore.PYQT_VERSION_STR` (native PyQt5 attr, not in the wrapper — guard with `hasattr`) | PyQt5 API; wrapper only proves `QT_VERSION_STR` (`Qt/__init__.py:84-94`) |
| Python version | `sys.version`, `sys.executable` | stdlib |
| numpy | `import numpy; numpy.__version__` | numpy ships with PyMOL (STACK.md:24) |

**Headless caveat:** `pymol.Qt` *module import* executes `from PyQt5 import QtGui, QtCore, QtOpenGL, QtWidgets` (`Qt/__init__.py:28`) — importing QtWidgets does not create a `QApplication`, so it is *expected* to work under `-cq`; **runtime-verify in the recording script and mark the result** (Open Question U2). The conservative prior-art rule "nothing touching `pymol.Qt.*` runs headless" (PA AGENTS.md) applies to widget *instantiation*, not to reading version strings — but verify, don't assume.

### 1.7 Headless run semantics (recipe facts, from prior art — proven across 12 shipped v1 phases)

- Recipe: `cd <windows-visible dir> && timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq <script.py>" 2>&1 | tail -50` — PA AGENTS.md:13-24, distilled in STACK.md:119-150.
- PyMOL resolves the script path and all relative paths against the **cmd.exe cwd**, which is the WSL cwd mapped to its Windows path — so `cd` into the repo's `/mnt/c` path first (STACK.md:126-129).
- **Exit codes:** 0 = clean *or* script `sys.exit(1)` swallowed by the wrapper; nonzero = hard crash (STACK.md:132-133). ⇒ **Assertions must PRINT PASS/FAIL markers**; the harness greps output *and* checks the exit code (crash detection only).
- `__file__` availability inside `-cq` scripts was uncertain in v1 — prior art guarded it: `_HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()` (PA `smoke/phase11_gui_diag.py:33-36`). Copy this guard.
- **No staging needed (user-confirmed 2026-09-05):** the repo lives on `/mnt/c` (= `C:\Users\nglok\Desktop\WORKDIR\molmdl\AA-match`), so both the smoke script and the `aamatch/` package are directly Windows-visible. v1's `wsl2win_cp.sh` staging step is skippable — run from the repo root and use repo-relative paths.

---

## 2. Design Recommendations

### 2.1 AA-match package layout (grow-into-able, no renames later)

```
AA-match/
├── pymol/                          # PyMOL project root (mirrors root AGENTS.md refs to pymol/AGENTS.md)
│   ├── aamatch/                    # the plugin package = one dir, name = module name
│   │   ├── __init__.py             # metadata block + docstring + __init_plugin__ + run_plugin_gui placeholder
│   │   ├── _version.py             # single source of __version__ (imported by __init__, pure)
│   │   ├── path_utils.py           # PURE: to_windows_path() + package_data_path(__file__-relative)
│   │   ├── setup_state.py          # PURE (Phase 1, parallel plan)
│   │   ├── persistence.py          # PURE (Phase 1, parallel plan)
│   │   ├── level_spec.py           # PURE (Phase 1, parallel plan)
│   │   ├── backup.py               # cmd bridge (Phase 1, parallel plan)
│   │   ├── controller.py …         # later phases (ARCHITECTURE.md names stick)
│   │   └── data/                   # bundled data later (Phase 2/8) — __file__-relative access
│   ├── tests/                      # WSL: python3.6 -m unittest discover -s tests -v
│   │   ├── __init__.py             # empty
│   │   ├── test_path_utils.py
│   │   └── …                       # pure-layer tests (parallel plan); NO pymol stubs needed in Phase 1
│   ├── smoke/
│   │   ├── smoke_01_bootstrap.py   # the headless proof (§3)
│   │   └── run_smoke.sh            # 3-line wrapper: cd + timeout + cmd.exe + grep PASS/FAIL
│   └── AGENTS.md                   # created this phase (root AGENTS.md already points here)
├── spec.md, AGENTS.md, .planning/ …
```

Rationale + one flagged discrepancy:
- Root `AGENTS.md:9,21` already says "See `pymol/AGENTS.md`" — a `pymol/` top dir is the established convention of this repo family (v1 lived in `bioCHEMeleon/pymol/`), and it leaves room for `vmd/` in v2. **ARCHITECTURE.md:79-109** sketches `aamatch/` at repo root instead — the planner should pick one (recommendation: `pymol/`) and note it; only paths in docs change, no code impact.
- Package name `aamatch` (lowercase, no dots/underscores — `installation.py:83-88`, loader skip rule `plugins/__init__.py:384-385`), menu label `AA-match`.
- `tests/` needs `__init__.py` for `unittest discover`; it is NOT inside the package so it never ships in the install zip.
- Module identity note: after a real install the module is `pmg_tk.startup.aamatch`; in smokes/direct imports it is `aamatch`. Never mix both import mechanisms in one PyMOL session (two distinct module objects → two `dialog` singletons). Phase 1 has no singleton yet; the rule goes into `pymol/AGENTS.md` now.

### 2.2 Phase-1 `__init__.py` skeleton (Qt-free, proven-clean entry)

```python
# Version: 0.1.0
# Citation-Required: No
"""AA-match — educational small-molecule <-> amino-acid interaction matching game.

PyMOL 2.5.0 plugin. Phase 1: installable skeleton; game UI arrives in Phase 4.
"""
# NOTE: the metadata block above MUST be the first lines of this file
# (plugins/__init__.py:193-210 stops parsing at the first non-# line).

__version__ = '0.1.0'   # kept in sync with the metadata block; _version.py in later phases


def __init_plugin__(app=None):
    """PyMOL plugin entry point — registers the Plugins-menu item.

    addmenuitemqt is imported locally and called FIRST: headless (HAVE_QT=False,
    plugins/__init__.py:29) it raises QtNotAvailableError, which the loader
    catches cleanly (plugins/__init__.py:287-288); keeping it first also avoids
    the cmd.extend restore quirk (plugins/__init__.py:266-282).
    """
    from pymol.plugins import addmenuitemqt
    addmenuitemqt('AA-match', run_plugin_gui)


def run_plugin_gui():
    """Phase-1 placeholder. Deliberately Qt-free: proves the wiring, keeps the
    [HUMAN] checkpoint meaningful, and contains zero code Phase 4 must rewrite."""
    print('AA-match %s: plugin skeleton OK — game UI arrives in Phase 4.' % __version__)
```

Why a `print` placeholder and not a stub dialog:
- Criterion 4 only requires the menu item to **register** and be **clickable**; a console line proves the callback fired without introducing any Qt code into Phase 1 (Phase 4 introduces Qt per PITFALLS.md Pitfall 4's grep gates from day one of GUI work).
- Zero Qt in the package ⇒ Phase-1 WSL tests import `aamatch` with **no `sys.modules` stubs at all** (v1 needed stubs only because its `__init__.py` imported Qt at module level — PA AGENTS.md "Tests" section). This is a hard, testable purity win for the bootstrap phase.
- Module-level imports stay stdlib-only in Phase 1 — the entire package imports cleanly under bare `python3.6`.

### 2.3 One-time Windows env version recording

A tiny script run **once** through the headless recipe, writing nothing itself — its console output is transcribed into a committed doc:

`pymol/smoke/record_env.py` (sketch):
```python
import sys
print('SMOKE-ENV python:', sys.version.replace('\n', ' '))
print('SMOKE-ENV executable:', sys.executable)
try:
    import pymol.Qt
    print('SMOKE-ENV qt_binding:', pymol.Qt.PYQT_NAME)
    from pymol.Qt import QtCore
    print('SMOKE-ENV qt_version:', QtCore.QT_VERSION_STR)
    if hasattr(QtCore, 'PYQT_VERSION_STR'):
        print('SMOKE-ENV pyqt_version:', QtCore.PYQT_VERSION_STR)
except Exception as exc:            # headless Qt import must not kill the run
    print('SMOKE-ENV qt: UNAVAILABLE headless (%r)' % (exc,))
from pymol import cmd
print('SMOKE-ENV pymol:', cmd.get_version()[0])
try:
    import numpy
    print('SMOKE-ENV numpy:', numpy.__version__)
except ImportError:
    print('SMOKE-ENV numpy: MISSING')
```

Record home: **`.planning/phases/01-bootstrap-pure-foundation/windows-env-versions.md`** (committed; `commit_docs: true` per config.json) + echoed into the new `pymol/AGENTS.md`. STACK.md:210 marks the Windows env versions LOW-confidence until exactly this run — this closes that gap.

### 2.4 INSTALL-01 human checkpoint — exact steps (code-verified wiring; button labels cosmetic)

One-time build of the install artifact (WSL, verified locally 2026-09-05):
```bash
cd <repo>/pymol
python3.6 -m zipfile -c aamatch-0.1.0.zip aamatch
python3.6 -m zipfile -l aamatch-0.1.0.zip   # MUST show 'aamatch/' dir at zip root
```
The zip root must contain the **package directory** (`aamatch/__init__.py`), never a flat `__init__.py` — flat zips fail with `BadInstallationFile('Missing __init__.py')` (`installation.py:118-130`).

Human steps:
1. Launch PyMOL 2.5.0 (GUI).
2. **Plugins → Plugin Manager** (`legacysupport.py:87` adds the item; Qt window opens `managergui_qt.PluginManager`, `legacysupport.py:74-85`).
3. Click **"Install from local file"** (`b_local` → `installplugin` → file dialog, `managergui_qt.py:45, 301-304`, `legacysupport.py:52-68`) and pick `aamatch-0.1.0.zip`. *(Alternative: pick `pymol/aamatch/__init__.py` — directory install, `installation.py:299-308`.)*
4. If a **"Select plugin directory"** dialog appears (only when >1 startup path — `installation.py:145-161`): pick `%APPDATA%\pymol\startup` if offered, else accept the default. If the chosen dir is unwritable, PyMOL itself offers to create `%APPDATA%\pymol\startup` (`installation.py:210-226`).
5. Expect **"Success: Plugin 'aamatch' has been installed."** (`installation.py:342-343`) — the menu item is already live in this session (immediate `load(force=1)`).
6. **Restart PyMOL** (the roadmap criterion's restart leg): GUI startup re-runs `initializePlugins` → autoload → `__init_plugin__` → menu item present again (`pymol_qt_gui.py:1245-1249, 972-973`).
7. Verify: **Plugins menu shows "AA-match"** below Plugin Manager (`pmg_qt/pymol_qt_gui.py:960-970` aliasing). Click it → the placeholder line appears in the PyMOL console/log window.
8. If the item is missing: check the console for `Unable to initialize plugin 'aamatch'` — load errors never crash PyMOL, they only print (`plugins/__init__.py:289-298`).

What the human records: menu present Y/N; click feedback Y/N; console clean Y/N. That is the entirety of INSTALL-01 for Phase 1.

---

## 3. Headless Smoke Proof (design)

### 3.1 `smoke_01_bootstrap.py` — what it proves and how

**Proves:** the repo's `aamatch/` package imports clean under real Windows PyMOL; `__init_plugin__` runs with exit 0 through (a) direct call and (b) the real loader path (`findPlugins`/`plugin_load`); the `path_utils` helpers behave under Windows paths. Menu registration is *not* assertable headless (§1.3) — that's INSTALL-01's job.

```python
# smoke/smoke_01_bootstrap.py (sketch; full version in the plan)
import os, sys, traceback

def winpath(p):                       # mirror of path_utils.to_windows_path for self-bootstrap
    return p.replace('/mnt/c/', 'C:\\').replace('/', '\\') if p.startswith('/mnt/c/') else p

_HERE = (os.path.dirname(os.path.abspath(__file__))
         if '__file__' in dir() else os.getcwd())          # guard proven in PA phase11_gui_diag.py:33
_ROOT = os.path.dirname(_HERE)                             # pymol/ (package parent)

failures = []
def check(name, cond, detail=''):
    print('SMOKE-01 %-38s %s %s' % (name, 'PASS' if cond else 'FAIL', detail))
    if not cond: failures.append(name)

# --- Part A: direct import (module identity 'aamatch') ---
if _ROOT not in sys.path: sys.path.insert(0, _ROOT)
import aamatch
check('import aamatch', aamatch.__version__ == '0.1.0')
try:
    aamatch.__init_plugin__(None)              # headless: expect QtNotAvailableError
    check('init_plugin direct', False, 'expected QtNotAvailableError')
except ImportError as e:
    check('init_plugin direct', False, repr(e))   # anything else is a real bug
except Exception as e:                          # 3.6: no `except QtNotAvailableError` w/o import chain worries
    from pymol.plugins import QtNotAvailableError
    check('init_plugin direct', isinstance(e, QtNotAvailableError), repr(e))

# --- Part B: loader path (module identity 'pmg_tk.startup.aamatch') ---
import pymol.plugins as P
rootw = winpath(_ROOT)
if rootw not in P.startup.__path__:
    P.startup.__path__.append(rootw)           # same mechanism as plugins/__init__.py:38
P.plugin_load('aamatch')                       # auto-initialize(-2) on empty registry (:136-137)
info = P.plugins.get('aamatch')
check('loader registered', info is not None)
check('loader loaded', bool(info and info.loaded))          # True even w/ Qt warning (:287-300)
check('loader module', bool(info and info.module is not None))
check('loader name', bool(info) and info.name == 'aamatch')

# --- Part C: env record (same prints as record_env.py; §2.3) ---

print('=== SMOKE-01 %s ===' % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'))
```

Runner (`smoke/run_smoke.sh`, the entire "toolchain recipe" as a repo script — PITFALLS.md Pitfall 2 asks for exactly this):
```bash
#!/usr/bin/env bash
# Run a headless cmd-only smoke. Usage: bash smoke/run_smoke.sh smoke/smoke_01_bootstrap.py
set -e
SCRIPT="$1"
cd "$(dirname "$0")/.."   # repo pymol/ dir = Windows-visible cwd
timeout 120 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\$(basename "$SCRIPT")" 2>&1 | tee /tmp/smoke_out.txt | tail -50
grep -q "=== SMOKE-01 PASS ===" /tmp/smoke_out.txt   # exit nonzero if marker missing
```
Key properties (all verified facts): `cd` into the `/mnt/c` repo path so cmd.exe cwd maps to `C:\...` (§1.7); `timeout` guards hangs; output markers carry the verdict because exit codes can't (§1.7); **no staging step** — script and package are used from the repo directly (§1.7, user-confirmed).

### 3.2 Why `startup.__path__.append(repo_root)` is legitimate

It is the exact mechanism the loader itself uses for `$PYMOL_DATA/startup` (`plugins/__init__.py:38`), it is transient (this PyMOL process only), and `findPlugins` will pick up `aamatch/` from the repo root like any startup dir (`:365-405`). It also proves the *real* discovery path the installed plugin will use — a stronger claim than a bare `sys.path` import, which is why the smoke does both (Part A isolates the entry point; Part B exercises the loader contract).

---

## 4. Pitfalls (this slice only)

| # | Pitfall | Verified basis | Avoidance |
|---|---|---|---|
| A | **`-k` disables plugin loading entirely** (`options.plugins = 0`); `-cq` contains no `k` but someone adding flags to the recipe later could silently break every smoke | `invocation.py:481-483`, `:59` | Recipe string frozen in `run_smoke.sh`; `-cq` only |
| B | **Exit codes lie for script assertions** — `sys.exit(1)` is swallowed by the wrapper (exit 0) | STACK.md:132-133 (prior-art proven) | Print `=== SMOKE-01 PASS/FAIL ===` markers; grep them |
| C | **Installed copy ≠ repo copy** — install imports `pmg_tk.startup.aamatch`; repo edits never reach the installed PyMOL until reinstall | `plugins/__init__.py:427`; `installation.py:295-296` | Dev loop = headless smoke on repo copy; install only for checkpoints. Document in `pymol/AGENTS.md` |
| D | **`cmd.extend` not restored** when `__init_plugin__` raises `QtNotAvailableError` mid-load | `plugins/__init__.py:266-288` | `addmenuitemqt` first statement in `__init_plugin__` (§2.2) |
| E | **Install may target the conda env's own startup dir** (it's writable) instead of `%APPDATA%\pymol\startup` — env-local, lost on env changes | `installation.py:145-161, 203-208` (user dir only offered when unwritable) | Human picks `%APPDATA%` in the dir dialog (step 4, §2.4); or pre-add the path via Plugin Manager path list (`managergui_qt.py:384-390`, `:52`) |
| F | **Flat zip fails** — `__init__.py` at zip root = `BadInstallationFile('Missing __init__.py')` | `installation.py:118-130` | Zip contains `aamatch/` as top-level entry; verify with `zipfile -l` (§2.4) |
| G | **Metadata placement** — `# Version:` after the docstring parses to `{}`; non-StrictVersion strings warn | `plugins/__init__.py:193-210`; `installation.py:44-62` | Metadata block first, `X.Y.Z` format; locally verified combo (§1.2) |
| H | **Duplicate menu items on in-session reinstall** — `load(force=1)` appends the item again; the menu is only cleared in `initializePlugins` | `installation.py:342`; `pmg_qt/pymol_qt_gui.py:960` | Cosmetic; restart clears. Note in checkpoint steps |
| I | **Broken plugins fail silently for humans** — error only in console, PyMOL runs on | `plugins/__init__.py:289-298` | Checkpoint step 8 (§2.4) |
| J | **Loader registers any `__init__.py` dir in scanned paths** — e.g. a transient repo-root scan would register `tests/` if it had `__init__.py` and didn't start with `_`/`.` | `plugins/__init__.py:383-401` | Harmless (transient, no autoload); don't leave the repo root permanently in startup paths; `tests/__init__.py` may exist for unittest — fine |
| K | **Fresh-install path prefs** — `%APPDATA%\pymol\startup` is *not* auto-scanned on a virgin install; it enters via the install flow or Plugin Manager path settings and persists in `~/.pymolpluginsrc.py` | `plugins/__init__.py:38-39, 415-420`; `installation.py:22-29, 228-229` | The install flow handles it (step 4); just don't assume the dir is scanned before any install happened |
| L | **3.6 syntax floor in ALL shipped files** — including smoke scripts (they run inside PyMOL's 3.6+) | STACK.md:22, 164 | `python3.6 -m py_compile pymol/aamatch/*.py pymol/smoke/*.py` gate |

---

## 5. Open Questions / UNVERIFIED

1. **U1 — Windows env exact versions** (Python/Qt binding/Qt/PyMOL/numpy). *The recording script in §2.3 is the verification task; closes STACK.md:210's LOW flag.* Expected: Python 3.6–3.10, PyQt5.
2. **U2 — headless `import pymol.Qt`** (expected OK: module import ≠ widget instantiation; `Qt/__init__.py:28` only imports modules). Verify in the same run; script is written to fail-soft (§2.3).
3. **U3 — Plugin Manager button labels** (`b_local` wiring verified at `managergui_qt.py:45`; the visible label lives in a runtime-loaded `.ui` form not present in this tree — `managergui_qt.py:42`). Steps in §2.4 describe *function*, not pixel labels; the human checkpoint confirms the actual label.
4. **U4 — `run-conda-pymol.bat` internals** — not read (user directed to treat as given); recipe semantics carried at HIGH confidence from prior-art usage (12 shipped phases, PA AGENTS.md:13-26).
5. **U5 — layout decision** `pymol/` (recommended, §2.1) vs ARCHITECTURE.md's repo-root `aamatch/` (ARCHITECTURE.md:79-109). Planner decision; doc-only impact.

---

## 6. Recommended Reading for the Planner

1. `.planning/research/STACK.md` — §Installation (lines 90-150) is the distilled contract; this file supersedes it on *when* `__init_plugin__` runs (§1.3 here) and on the no-staging smoke.
2. `.planning/research/PITFALLS.md` — Pitfalls 1 (Qt tiers — drives the Qt-free Phase-1 entry), 2 (paths — drives `path_utils` + `run_smoke.sh`), 3 (stdlib purity — WSL test import with zero stubs).
3. `.planning/phases/01-bootstrap-pure-foundation/01-RESEARCH-pure-foundation.md` — the parallel researcher's file; merge its module list into §2.1's tree before planning.
4. `tmp/bioCHEMeleon/biochemeleon/__init__.py:129-153` + `AGENTS.md` (Commands + Environment sections) — the entry-point and recipe prior art.
5. `pymol-src/modules/pymol/plugins/__init__.py` + `installation.py` — read the loader once before finalizing the plan; every claim above cites it.
6. `ARCHITECTURE.md:76-124` — package/module naming to preserve (flat `aamatch/`, module names fixed for Phases 2-9).

**Planner-facing summary:** Phase 1's install/headless slice = (1) Qt-free skeleton package with metadata-first `__init__.py` + print placeholder; (2) `smoke_01_bootstrap.py` proving direct-import + loader-path load with printed PASS markers (no staging; run from repo); (3) one-time env-record smoke → committed doc; (4) built zip + 8-step human checkpoint. The two success criteria map 1:1: criterion 3 → §3, criterion 4 → §2.4.

---
*Researched 2026-09-05 against `pymol-src` (PyMOL 2.5.0), prior-art v1 tree, and local WSL python3.6.9 runtime checks. Valid ~30 days (host app is pinned at 2.5.0).*
