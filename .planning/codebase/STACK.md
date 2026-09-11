# Technology Stack

**Analysis Date:** 2026-09-12

> **Scope note:** This repo is currently PyMOL-plugin only (v1). The VMD Tcl
> port is explicitly out of scope (`.planning/PROJECT.md:42`). There are no
> `pymol/` or `vmd/` subtrees — the cmd-coupled viewer layer lives inside the
> `aamatch/` package alongside the pure layer. Verified research with
> file:line citations for the PyMOL host API: `.planning/research/STACK.md`.

## Languages

**Primary:**
- Python 3.6-compatible (3.6 syntax floor, no walrus / no positional-only params) — the entire plugin `aamatch/`, tests `tests/`, smokes `smoke/smoke_*.py`. Written 3.6-safe so it runs under both runtimes below.

**Secondary:**
- Bash (POSIX-ish) — smoke harness `smoke/run_smoke.sh` only. Runs under WSL Ubuntu bash.
- Tcl — NOT YET PRESENT (reserved for the deferred VMD v2 port).

## Runtime

**Environment (dev shell):**
- WSL Ubuntu on Windows 11; `python3.6` 3.6.9 used ONLY for syntax checks and pure-layer unit tests (no installs allowed — `opencode.json:60-64` denies/asks `pip*`, `apt*`, `conda*`).
- `python3.6 -m py_compile aamatch/*.py` is the syntax floor gate.
- `python3.6 -m unittest discover -s tests -v` is the WSL test suite (includes purity gates from `tests/test_purity.py`).

**Environment (product runtime, Windows-hosted):**
- PyMOL 2.5.0 (open-source build) inside Windows conda env `chemtools-win10`, launched from WSL via `cmd.exe /c C:\src\run-conda-pymol.bat -cq <script>` (headless) or GUI for human checkpoints.
- Recorded env versions (verbatim, one-time record): Python 3.9.13 conda-forge → `C:\Users\nglok\.conda\envs\chemtools-win10\python.exe`, PyQt5 binding 5.12.3 / Qt 5.12.9, PyMOL 2.5.0, numpy 1.25.2 — `.planning/phases/01-bootstrap-pure-foundation/windows-env-versions.md:9-20`.

**Package Manager:**
- None. The plugin ships as source; installation is via PyMOL's Plugin Manager (package dir or zip with one package + `__init__.py`). No `setup.py`, `pyproject.toml`, `requirements.txt`, or `package.json` exists — verified.
- Lockfile: not applicable.

## Frameworks

**Core (all ship inside PyMOL 2.5.0 — zero extra deps by hard constraint):**
- PyMOL `cmd` API (2.5.0) — 3D viewer/object manipulation; entry point `aamatch/__init__.py` (`__init_plugin__` → `pymol.plugins.addmenuitemqt('AA-match', run_plugin_gui)`).
- PyQt5 — imported ONLY via `from pymol.Qt import QtWidgets, QtGui, QtCore` (never `from PyQt5 import ...`); used by the Phase-4 setup window. Current headless modules import `from pymol import cmd` only (`aamatch/engine.py:75`, `aamatch/geometry.py:75`, `aamatch/placement.py:72`, `aamatch/wizard.py:79`).
- `pymol.wizard.Wizard` — built-in wizard framework; gameplay loop `aamatch/wizard.py` (`GameWizard` subclass, `from pymol.wizard import Wizard` at `aamatch/wizard.py:80`).
- numpy 1.25.2 — ships with PyMOL; geometry math.

**Testing:**
- `unittest` (stdlib, 3.6) — all WSL tests in `tests/` (e.g. `tests/test_purity.py`, `tests/test_detector.py`, ...). No pytest.
- Headless smoke harness — bash + cmd.exe bridge, `smoke/run_smoke.sh` + `smoke/smoke_0N_*.py`; verdict via PASS-marker grep (exit codes cannot cross cmd.exe).

**Build/Dev:**
- `opencode.json` — OpenCode/GSD workflow config (agent models, permission gates; `rm *` and `rg *` denied).
- `.planning/config.json` — GSD workflow config (`mode: yolo`, `depth: comprehensive`, `parallelization: true`, `commit_docs: true`).
- Git — conventional commits with phase-plan scope (`feat(02-03):` etc.).

## Key Dependencies

**Critical:**
- `pymol` (2.5.0, host-provided) — cmd API + plugin loader; imported in cmd-coupled modules only (`aamatch/engine.py`, `aamatch/geometry.py`, `aamatch/placement.py`, `aamatch/wizard.py`, `aamatch/gamestart.py`). Pure modules (`aamatch/setup_state.py`, `level_spec.py`, `persistence.py`, `backup.py`, `paths.py`) must NOT import it — enforced by AST purity gates in `tests/test_purity.py`.
- Python stdlib only in pure layer: `json`, `os`, `tempfile` (`aamatch/persistence.py:28-30`), `hashlib`/`json`/`os`/`tempfile`/`time` (`aamatch/backup.py:42-46`), `copy`/`random` (`aamatch/setup_state.py:36-37`), `math` (`aamatch/vec3.py:18`, `aamatch/detector.py:155`), `os` (`aamatch/paths.py:17`).
- `numpy` — host-provided 1.25.2; detection-geometry math (no scipy/RDKit/pandas allowed).

**Infrastructure:**
- None — no servers, no databases, no external runtime services. Everything runs inside the PyMOL process.

## Configuration

**Environment:**
- No `.env` files. No env-var-driven configuration in plugin code.
- WSL↔Windows bridge: `C:\src\run-conda-pymol.bat` (Windows-side, outside repo) activates conda env and forwards args to PyMOL; WSL entry point is `smoke/run_smoke.sh` ( `timeout $TIMEOUT cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\<script>"` at `smoke/run_smoke.sh:15`).
- No `setenv.bat` in repo (referenced in AGENTS/PROJECT as the Windows GUI launch script; lives outside the repo).

**Build:**
- No build step. Python source is interpreted in-place.
- Version metadata: `# Version: 0.1.0` comment block at the top of `aamatch/__init__.py:1` (parsed by `pymol.plugins` — must stay first lines) kept in sync with `__version__ = '0.1.0'` at `aamatch/__init__.py:13`.
- Data-format versions (two separate gates, never conflate): `FORMAT_VERSION` in `aamatch/persistence.py` (container format — refuses newer, accepts older) and `DETECTOR_VERSION`/`LEVEL_SPEC_VERSION` in `aamatch/level_spec.py` (exact-match required).

**Bundled data (committed, offline):**
- `aamatch/data/MANIFEST.json` — demo-set manifest (`manifest_version: 1`, magic `AAMATCH`, entries with SDF file, atom/bond counts, sha256, protonation).
- `aamatch/data/ligands/benzamide.sdf`, `aamatch/data/ligands/acetate.sdf` — development demo set.

## Platform Requirements

**Development:**
- Windows 10/11 + WSL (Ubuntu) with the repo under `/mnt/c/...` (must be Windows-visible — headless smokes run from the repo copy, no staging step).
- `python3.6` (3.6.9) available in WSL; NO installs ever (opencode permission rules).
- Windows conda env `chemtools-win10` with PyMOL 2.5.0 + `C:\src\run-conda-pymol.bat` launcher.
- `tclsh` (Tcl 8.5/8.6) available but currently unused (for future VMD port).

**Production (user side):**
- PyMOL 2.5.0 (anaconda build or equivalent) with Qt GUI; install `aamatch/` via Plugin Manager (`README.md:22-28`). Plugin installs to `%APPDATA%\pymol\startup\aamatch\`.
- No network access at gameplay time (demo data bundled; `.planning/PROJECT.md:45`).

## Dev/Test Command Surface (canonical)

```bash
# WSL, from repo root:
python3.6 -m py_compile aamatch/*.py            # syntax floor (3.6)
python3.6 -m unittest discover -s tests -v      # WSL suite incl. purity gates
bash smoke/run_smoke.sh smoke/smoke_01_bootstrap.py   # headless Windows PyMOL proof
```

---

*Stack analysis: 2026-09-12*
