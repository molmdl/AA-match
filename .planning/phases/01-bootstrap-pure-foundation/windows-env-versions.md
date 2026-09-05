# Windows Conda Env Versions (one-time record)

**Recorded:** 2026-09-06
**Method:** headless smoke 01 (Plan 01-07) under the frozen WSL-to-Windows recipe — the SMOKE-ENV lines below are transcribed verbatim from the committed smoke's console output (`/tmp/smoke_out.txt`, full run ended with `=== SMOKE-01 PASS ===`, runner exit 0).
**Command:** `bash smoke/run_smoke.sh smoke/smoke_01_bootstrap.py` (run from the repo checkout; internally `cd <repo-root> && timeout 120 cmd.exe /c "C:\src\run-conda-pymol.bat -cq smoke\smoke_01_bootstrap.py"`).

## Recorded versions (verbatim SMOKE-ENV lines)

| What | Value (verbatim) |
|---|---|
| repo root anchor | `C:\Users\nglok\Desktop\WORKDIR\molmdl\AA-match\tmp\exec-01-07` |
| python | `3.9.13 (packaged by conda-forge, MSC v.1929 64 bit (AMD64)), main May 27 2022` |
| executable | `C:\Users\nglok\.conda\envs\chemtools-win10\python.exe` |
| qt_binding | `PyQt5` |
| qt_version | `5.12.9` |
| pyqt_version | `5.12.3` |
| pymol | `2.5.0` |
| numpy | `1.25.2` |
| probe fwdslash-load | `OK (n=1)` |
| probe spacepath-load | `OK (n=1)` |

Source line formats (for future re-runs): `SMOKE-ENV <key>: <value>` and `SMOKE-ENV probe <name>: OK (n=<count>)` / `... FAILED (<detail>)`.

## What this closes

- **STACK.md LOW-confidence flag "Windows env Python/Qt exact versions"** (STACK.md:22 "Verify the env's exact version once in the first headless smoke", :210, :227): **CLOSED** — Python 3.9.13 / PyQt5 5.12.9 / PyQt5 binding 5.12.3 / PyMOL 2.5.0 / numpy 1.25.2, all read at runtime inside the real Windows PyMOL process. The 3.6-compatible syntax floor (STACK.md:22) remains correct and necessary: 3.9.13 runs any 3.6-compatible code, and the WSL test shell is 3.6.9.
- **Pure-foundation OQ4 (forward-slash paths under `cmd.load`)**: **ANSWERED — accepted.** `cmd.load('C:/.../tmp/smoke fixtures/min.pdb')` loaded 1 atom.
- **Pure-foundation OQ7 (paths containing spaces under `cmd.load`)**: **ANSWERED — accepted.** `cmd.load('C:\...\tmp\smoke fixtures\min.pdb')` (backslash form, space in dirname) loaded 1 atom.
- **Research §1.6 U2 (headless `import pymol.Qt`)**: **VERIFIED OK** — reading `pymol.Qt.PYQT_NAME` / `QtCore.QT_VERSION_STR` / `QtCore.PYQT_VERSION_STR` headless works (module import is not widget instantiation).

## Headless-runtime discoveries (load-bearing for all future smokes)

1. **`__file__` inside a `-cq` script points at PyMOL's launcher, not the script.**
   A headless probe printed `__file__ = C:\Users\nglok\.conda\envs\chemtools-win10\Lib\site-packages\pymol\__init__.py` while running `tmp\probe_plugins.py` with cwd = repo root. The v1-era guard `if '__file__' in dir() else os.getcwd()` (PA `phase11_gui_diag.py:33`) is therefore **not sufficient** — `__file__` exists but is wrong. `smoke_01_bootstrap.py` anchors the repo root from `sys.argv` (the script path as passed) with `os.getcwd()` as fallback (the frozen runner `cd`s to the repo root before launching cmd.exe, and PyMOL inherits that cwd — probe-proven). Future smokes must use the same anchor, never `__file__`.
2. **`PluginInfo.loaded` stays `False` on the headless Qt-unavailable path even though `load()` returns `True`.**
   In the installed 2.5.0 `plugins/__init__.py`, `load()` catches `QtNotAvailableError`, prints `Plugin '<name>' only available with PyQt GUI.` and falls through to `return True` — but `self.loadtime` is only assigned on the fully-successful branch, and the `loaded` property is `loadtime is not None`. So after a clean headless `plugin_load`, assert `info.load()`'s return value (or `info.module is not None`), **not** `info.loaded`.
3. **Hygiene note:** the first (failing) smoke run wrote its Part-D fixture into the conda env's `site-packages\tmp\` (consequence of discovery 1); it was removed the same day and the fixture now lands in the checkout's git-ignored `tmp\smoke fixtures\`.

## Re-verification

To re-verify any of the above after an env change, re-run:
```bash
bash smoke/run_smoke.sh smoke/smoke_01_bootstrap.py
```
and diff the SMOKE-ENV lines against the table above.
