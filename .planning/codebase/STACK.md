# Technology Stack

**Analysis Date:** 2026-10-03

AA-match is a **PyMOL 2.5.0 plugin** (a molecular-matching educational mini-game), not a
standalone application. There is no `package.json` / `requirements.txt` / `pyproject.toml`
— dependency truth is in the imports plus `AGENTS.md` (repo law) and `README.md`
("No external Python dependencies beyond what PyMOL already ships", `README.md:20`).
`opencode.json` in the repo root is AI-tooling config, NOT product dependencies.

## Languages

**Primary:**
- Python — 100% of product code. Package: `aamatch/` (28 modules), tests `tests/`,
  headless PyMOL proofs `smoke/`, demo-data builder `scripts/build_demos.py`.

**Secondary:**
- Bash — exactly one script, the headless-smoke runner `smoke/run_smoke.sh`.
- Tcl/Tk — NONE in product code. The VMD/Tcl port ("v2") is PLANNED but the `vmd/`
  directory **does not exist in this repo** — do not reference it. (`vmd-ref/` and
  `vmd/3rd_party_lib/` appear only in `.gitignore:7-8` and `AGENTS.md` as
  git-ignored reference material for the future port.)

## Runtime

**Development shell (WSL Ubuntu):**
- `python3.6` = Python **3.6.9** (verified: `python3.6 --version`). This is the
  **3.6 syntax floor**: unit tests and syntax checks run here only. `tclsh` is NOT
  installed in this WSL shell (`command not found`), despite `AGENTS.md` mentioning it
  for the future v2 port.
- Per `opencode.json` permissions: `pip*`, `apt*`, `conda*`, `rm*` are denied/ask —
  **never install anything in WSL**.

**Production runtime (Windows):**
- PyMOL runs as a **Windows** process inside a conda env, invoked from WSL via
  `cmd.exe /c "C:\src\run-conda-pymol.bat -cq <script>"` (see `smoke/run_smoke.sh:15`).
- Recorded Windows env versions (verbatim, `.planning/phases/01-bootstrap-pure-foundation/windows-env-versions.md`):

| Component | Version |
|---|---|
| Python (conda env) | 3.9.13 (conda-forge, `C:\Users\nglok\.conda\envs\chemtools-win10\python.exe`) |
| PyMOL | 2.5.0 |
| Qt binding | PyQt5 (Qt 5.12.9, PyQt 5.12.3) |
| numpy | 1.25.2 |

**The dual-runtime rule (load-bearing):** all code must be 3.6-compatible syntax
(enforced by `tests/test_purity.py` Gate D: `python3.6 -m py_compile aamatch/*.py`)
yet runs under 3.9.13 in PyMOL. No `dataclasses`, no walrus, no positional-only
params, no f-string `=`.

**Package Manager:** None for the product. The plugin is installed via PyMOL's
**Plugin → Plugin Manager → Install New Plugin** pointing at the `aamatch/` package
directory (`README.md:22-28`). Any future extra lib requires explicit user approval
and vendoring under `3rd_party_lib/` (git-ignored, `.gitignore:19`).

## Frameworks

**Core / host application:**
- **PyMOL 2.5.0** (open-source build) — THE host. The plugin imports:
  - `from pymol import cmd` — module-level legal in CMD TIER modules
    (`aamatch/engine.py:120`, `aamatch/gamestart.py:160`, `aamatch/placement.py:74`,
    `aamatch/geometry.py:75`, `aamatch/upload.py:69`, `aamatch/setup_window.py:56`,
    `aamatch/wizard.py`), lazy (`from pymol import cmd` inside functions) in
    `aamatch/game_window.py`.
  - `from pymol.Qt import QtWidgets, QtCore[, QtGui]` — Qt ONLY via this shim;
    `from PyQt5 import ...` is banned repo-wide (test-pinned in
    `aamatch/setup_window.py` header comment and checked by smokes). Used in the two
    QT TIER modules `aamatch/setup_window.py:55` and `aamatch/game_window.py:148`.
  - `from pymol.wizard import Wizard` — the game input adapter
    `aamatch/wizard.py:83` (`class GameWizard(Wizard)`, `aamatch/wizard.py:136`).
  - `from pymol.plugins import addmenuitemqt` — menu registration, lazy inside
    `__init_plugin__` (`aamatch/__init__.py:25-26`).
- **numpy** — available in the PyMOL env (1.25.2) but **deliberately UNUSED** in
  product code. The pure-layer gate forbids `numpy` imports
  (`tests/test_purity.py` `FORBIDDEN` set); vector math is plain-tuple stdlib in
  `aamatch/vec3.py` ("No classes, no numpy", `aamatch/vec3.py:13`).

**Testing:**
- Python stdlib `unittest` only (run: `python3.6 -m unittest discover -s tests -v`
  from repo root). 28 test modules in `tests/`. No pytest, no plugins, no mock
  framework — the purity contract (`tests/test_purity.py`) exists precisely so pure
  modules import under bare 3.6 with **zero sys.modules stubs**.

**Build/Dev:**
- None (no bundler/compiler). `scripts/build_demos.py` is a stdlib-only
  (`json/os/sys/hashlib/urllib/argparse`) offline data-curation tool that fetches
  ligand SDFs and writes `aamatch/data/` — a maintainer script, not part of the
  shipped plugin pipeline.

## Key Dependencies

**Critical (ship with PyMOL open-source — never added):**
- `pymol.cmd` — the viewer API (`aamatch` touches ~55 distinct `cmd.*` calls;
  see INTEGRATIONS.md for the inventory).
- `pymol.Qt` (PyQt5 5.12.3 / Qt 5.12.9 in the recorded env) — UI widgets:
  `aamatch/setup_window.py` (`class SetupWindow(QtWidgets.QDialog)`,
  `aamatch/setup_window.py:120`, two-tab `QTabWidget`), `aamatch/game_window.py`
  (`class GameTab(QtWidgets.QWidget)`, `aamatch/game_window.py:151`, `QMessageBox`,
  `QFileDialog`, `QCheckBox`, `QtCore.QTimer` for countdown/1-Hz game clock).
- `pymol.wizard.Wizard` — panel/pick interaction for gameplay.

**Infrastructure (stdlib only — this is the complete pure-layer whitelist,
`tests/test_purity.py` ALLOWED_STDLIB):**
- `json`, `os`, `sys`, `tempfile`, `time`, `hashlib`, `random`, `copy`, `math`,
  `io`, `re`, `collections`, `errno`, `ast`, `zipfile`, `shutil`, `unittest`,
  `datetime`, `base64`.
- Notable stdlib uses: `zipfile` for the `.aamz` checkpoint archive
  (`aamatch/checkpoint.py:84`), `base64` + `hashlib` for embedded uploaded-ligand
  records in the shareable game file (`aamatch/game_file.py:70-72`),
  `tempfile.mkstemp(suffix='.pse')` for atomic session capture
  (`aamatch/gamestart.py:833`).

**Forbidden (AST-enforced in pure modules, `tests/test_purity.py` FORBIDDEN):**
`pymol`, `numpy`, `dataclasses`, `PyQt5`, `PySide2`, `tkinter`, `Pmw`, `pmg_tk`.

## Configuration

**Environment:** No `.env`, no config files, no settings files for the product.
PyMOL-side runtime state is manipulated via `cmd.set(...)` (e.g. mouse_selection_mode
snapshot/restore in `aamatch/wizard.py` header contract 4). Version constants live
in code:
- `aamatch/__init__.py:13` — `__version__ = '0.1.0'` (plus the `# Version:` metadata
  block that `pymol.plugins` parses, `aamatch/__init__.py:1`).
- `aamatch/persistence.py:37` — `FORMAT_VERSION = 1` (container gate,
  refuse-newer/accept-older).
- `aamatch/level_spec.py:60-61` — `DETECTOR_VERSION = "det-1"` (EXACT match gate),
  `LEVEL_SPEC_VERSION = 1`.
- `aamatch/checkpoint.py:89` — `CHECKPOINT_VERSION = 1`.

**Build:** None. Installation = PyMOL Plugin Manager install of the `aamatch/`
directory (imports then as `pmg_tk.startup.aamatch`; in smokes/direct imports it is
`aamatch` — never mix both in one PyMOL session, `AGENTS.md` gate 5).

**WSL→Windows path guard:** every `cmd.load`/`cmd.save`/file-API path routes through
`to_windows_path()` (`aamatch/paths.py:20`) — Windows PyMOL cannot resolve
`/mnt/c/...`. Anchor bundled data via `package_data_path()` (`aamatch/paths.py:54`,
`__file__`-anchored, never `os.getcwd()`).

## Platform Requirements

**Development:**
- WSL Ubuntu with `python3.6` (3.6.9). Repo checkout on `/mnt/c/...` (Windows-visible —
  smokes run against the repo copy directly; no staging step).
- Test commands (from repo root):
  - `python3.6 -m py_compile aamatch/*.py` — syntax floor
  - `python3.6 -m unittest discover -s tests -v` — full suite incl. purity gates
  - `bash smoke/run_smoke.sh smoke/<script>.py` — headless Windows PyMOL proof;
    verdict greps `=== SMOKE-NN PASS ===` because exit codes cannot carry through
    `cmd.exe` (`smoke/run_smoke.sh:4-17`). 21 smokes exist (`smoke/smoke_01_bootstrap.py`
    … `smoke/smoke_21_demo_cleanup.py`).

**Production:**
- Windows PyMOL 2.5.0 (anaconda build or equivalent, `README.md:16`) with its bundled
  PyQt5 + numpy. The PyMOL GUI (Qt) is required for the setup/game windows; headless
  (-cq) works for cmd-only smokes — `addmenuitemqt` headless raises
  `QtNotAvailableError` which PyMOL's loader catches cleanly
  (`aamatch/__init__.py:19-24`).

**Headless runtime gotchas (recorded in
`.planning/phases/01-bootstrap-pure-foundation/windows-env-versions.md`):**
1. `__file__` inside a `-cq` script points at PyMOL's launcher, not the script —
   anchor repo root from `sys.argv`/`os.getcwd()`, never `__file__`.
2. `PluginInfo.loaded` stays `False` on the headless Qt-unavailable path even when
   `load()` returns `True` — assert the return value, not `.loaded`.

---

*Stack analysis: 2026-10-03*
