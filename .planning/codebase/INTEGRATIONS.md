# External Integrations

**Analysis Date:** 2026-10-03

**Headline: AA-match has ZERO external service integrations.** No network calls in the
shipped plugin (`grep` of `http|urllib|requests|socket` across `aamatch/*.py` returns
no code hits), no databases, no auth providers, no SaaS SDKs, no webhooks. The
"integration surfaces" are the **host-application APIs** (PyMOL `cmd.*`, the
`pymol.Qt` PyQt5 shim, the `pymol.wizard` input stack), the **PyMOL plugin loader
contract**, and the **file formats** the plugin reads/writes. Those are mapped below.

## APIs & External Services

**External network services:** None in `aamatch/`.

- The ONLY network-touching code in the repo is the maintainer-only data-curation
  script `scripts/build_demos.py` (`import urllib.request`, line 72) whose `--fetch`
  mode does a stdlib GET of ligand SDF records from upstream archives to build the
  bundled demo set offline. It runs at **data-curation time** (human-gated, results
  committed to `aamatch/data/`), never at plugin runtime. Upstream provenance/
  licenses are documented in `docs/DATA_SOURCES.md` (PDB/PDBe-derived records with
  verified DOIs; every claim human-approved before commit).
- The shipped plugin runs fully offline. Demo molecules are bundled under
  `aamatch/data/ligands/*.sdf` (18 files) with a checksummed index
  `aamatch/data/MANIFEST.json` (per-entry `sha256`, atom/bond counts, format).

### Host-application API surface #1: `pymol.cmd` (the real "external API")

Verified inventory of `cmd.*` calls across `aamatch/*.py` (`grep -o "cmd\.\w*"`):

| Category | Calls (hot files) |
|---|---|
| Loading / parsing | `cmd.load` (`aamatch/engine.py:243`, `aamatch/gamestart.py:747`, package loads in `aamatch/manifest.py` flow), `cmd.read_sdfstr` / `cmd.read_mol2str` — uploaded molecule strings via PyMOL's C parsers, guarded by `hasattr(cmd, ...)` because `read_mol2str` is unexported on some 2.5.0 builds (`aamatch/upload.py:128-141`). PDB upload is explicitly REFUSED (`aamatch/game_file.py:376`, "no reliable bond orders") |
| Session save/restore | `cmd.save` (full-session `.pse` capture, `aamatch/gamestart.py:836`), `cmd.load` of extracted `game.pse` for full session replace (`aamatch/gamestart.py:672-747`) |
| Coordinate/contact queries | `cmd.iterate`, `cmd.iterate_state`, `cmd.get_model`, `cmd.get_bonds`, `cmd.count_atoms`, `cmd.count_states` (detector/geometry reads) |
| Object manipulation | `cmd.create`, `cmd.fragment`, `cmd.delete`, `cmd.alter`, `cmd.sort`, `cmd.get_names`, `cmd.get_unused_name`, `cmd.color`, `cmd.show`/`hide`, `cmd.select`, `cmd.deselect`, `cmd.rebuild` |
| Movement (gameplay) | `cmd.translate` (18 call sites) and `cmd.rotate` — **world-frame baked transforms only** (`camera=0`), leaving the object matrix at identity; `cmd.get_object_matrix`, `cmd.transform_object`, `cmd.get_object_ttt`, `cmd.matrix_reset` (contract 5, `aamatch/wizard.py` header) |
| Wizard stack | `cmd.set_wizard` / `cmd.get_wizard` / `cmd.refresh_wizard` — push/pop/lifecycle of `GameWizard` (`aamatch/wizard.py` header contract 3; C-layer pops run `cleanup()`) |
| View / settings / misc | `cmd.get_view`, `cmd.set_view`, `cmd.zoom`, `cmd.set` (e.g. mouse_selection_mode snapshot/restore), `cmd.get`, `cmd.refresh`, `cmd.indicate`, `cmd.unpick`, `cmd.extend` |

**Auth:** none. **Keys/tokens:** none.

### Host-application API surface #2: Qt via the `pymol.Qt` shim

- Qt is reached **only** through `from pymol.Qt import QtWidgets, QtCore[, QtGui]`
  (`aamatch/setup_window.py:55`, `aamatch/game_window.py:148`). `from PyQt5 import ...`
  is banned repo-wide (comment-pinned in both QT TIER headers; negative-control
  tested in `tests/test_purity.py`).
- Widgets used: `QDialog` (`SetupWindow`, `aamatch/setup_window.py:120`),
  `QTabWidget` (Setup/Game tabs, `aamatch/setup_window.py:241`),
  `QWidget` (`GameTab`, `aamatch/game_window.py:151`), `QPushButton`, `QCheckBox`,
  `QMessageBox`, `QFileDialog` (import/export/save pickers), `QtCore.QTimer`
  (3-2-1 countdown + 1 Hz game clock, `aamatch/game_window.py`; proven headless by
  `smoke/smoke_13_qt_timer_probe.py`). Headless `import pymol.Qt` (no widget
  instantiation) is verified OK.
- Recorded binding versions: PyQt5 5.12.3 / Qt 5.12.9
  (`.planning/phases/01-bootstrap-pure-foundation/windows-env-versions.md`).

### Host-application API surface #3: PyMOL plugin loader + wizard stack

- **Entry point:** `__init_plugin__(app=None)` (`aamatch/__init__.py:16`) calling
  `pymol.plugins.addmenuitemqt('AA-match', run_plugin_gui)` — imported lazily and
  called FIRST so headless raises `QtNotAvailableError`, which PyMOL's loader catches
  (installed `plugins/__init__.py:287-288`). Metadata: the `# Version: 0.1.0` comment
  block must stay the first lines (`pymol.plugins` parses `# Key: value` only at the
  top, `aamatch/__init__.py:8-11`).
- **Module identity:** after install, imports as `pmg_tk.startup.aamatch`; in
  smokes/direct import as `aamatch`. Never mix both in one PyMOL session (double
  module objects; `AGENTS.md` gate 5). `aamatch/wizard.py` imports the engine
  relatively INSIDE methods (`from . import engine`) so both identities work.
- **Wizard lifecycle:** `GameWizard(Wizard)` (`aamatch/wizard.py:136`) uses
  stack-native `cmd.set_wizard` push/pop; session save **pickles the wizard stack**,
  so every `GameWizard` attribute must be plain picklable data (the base class's
  `__getstate__` strips `self.cmd`; contract 2, `aamatch/wizard.py`).
- **Dragging internals:** smokes probe `import pymol.wizard.dragging` /
  `import pymol.wizard as _wizard_mod` (movement-spike smoke,
  `smoke/smoke_06_spike_movement.py`) — research-only, not product imports.

## Data Storage

**Databases:** None.

**File storage — local filesystem only.** All persistence is versioned files:

| Artifact | Format | Writer/Reader | File(s) |
|---|---|---|---|
| Container envelope | JSON `{"magic": "AAMATCH", "version": 1, "kind": ..., "data": {...}}` | `make_container` / `check_container` (`aamatch/persistence.py:39` KINDS = `setup, level_spec, game, checkpoint, manifest`) | `aamatch/persistence.py` |
| Setup save/load | JSON, kind `setup` | setup window buttons (spec 3.3/3.4) | `aamatch/persistence.py`, `aamatch/setup_state.py` |
| Shareable game export/import | ONE JSON file, kind `game`, extension `.aamatch.json`; embedded uploaded ligands as base64 + sha256 of record text (`aamatch/game_file.py:33`), refuse-newer `game_format_version` gate | `aamatch/game_file.py` (487 lines) | `aamatch/game_file.py` |
| Checkpoint save/resume | `**.aamz**` — zip with exactly two members `game.pse` (PyMOL session bytes) + `state.json` (sidecar), atomic write via temp + `os.replace` | `aamatch/checkpoint.py:305-364` (`zipfile.ZIP_DEFLATED`, `PSE_MEMBER`/`SIDECAR_MEMBER` `:90-91`) | `aamatch/checkpoint.py`, `aamatch/game_window.py:76,96` |
| Bundled demo set | `*.sdf` ligand records + `MANIFEST.json` (sha256-indexed) | built by `scripts/build_demos.py`; consumed through `aamatch/manifest.py` → `package_data_path` → `cmd.load` | `aamatch/data/`, `aamatch/manifest.py` |
| Uploaded molecules (runtime) | SDF / MOL2 **only**, single- or multi-record; strings parsed via `cmd.read_sdfstr`/`cmd.read_mol2str`; PDB refused | `aamatch/upload.py`, `aamatch/game_file.py:363-376` | — |
| PyMOL session snapshot | `.pse` via `tempfile.mkstemp(suffix='.pse')` + `cmd.save` (full session) inside the Windows process | `aamatch/gamestart.py:833-836` | — |

**Caching:** None. **Cloud storage:** None.

## Authentication & Identity

**Auth Provider:** None. No users, no accounts, no sessions beyond PyMOL's own.

## Monitoring & Observability

**Error tracking:** None.

**Logging / surfacing:** Python `print` to the PyMOL console for smoke verdicts
(`=== SMOKE-NN PASS ===` markers, grepped by `smoke/run_smoke.sh:17` because exit
codes can't cross `cmd.exe`), plus Qt `QMessageBox` refusals and the in-game
rolling info box (`aamatch/game_window.py`, text built by pure
`aamatch/status_text.py`). Failure philosophy is **fail-closed**: versioned-format
refusals raise `persistence.FormatError` / `ValueError` before touching the PyMOL
session (e.g. "an incomplete checkpoint NEVER touches the session",
`aamatch/gamestart.py:662`).

## CI/CD & Deployment

**Hosting:** Git repo only; no CI service configured (no `.github/`, no CI YAML).

**"Pipeline" = the three standing gates** (run manually / by agents, `AGENTS.md`):
1. `python3.6 -m py_compile aamatch/*.py` — 3.6 syntax floor.
2. `python3.6 -m unittest discover -s tests -v` — WSL suite incl.
   `tests/test_purity.py` (AST import-purity gates A/A2/B/D + negative control).
3. `bash smoke/run_smoke.sh smoke/<NN>.py` — headless Windows-PyMOL proof via
   `cmd.exe /c "C:\src\run-conda-pymol.bat -cq smoke\<NN>.py"` (21 smokes,
   `smoke/smoke_01_*` … `smoke/smoke_21_*`).

**Deployment:** PyMOL Plugin Manager install of the `aamatch/` directory
(`README.md:22-28`). Dev loop edits the repo copy directly (repo is Windows-visible
via `/mnt/c`); installed copies never see repo edits until reinstalled.

## Environment Configuration

**Required env vars:** None. No `.env*` files (git-ignored anyway, `.gitignore:10`),
no secrets, `**/secrets.toml` and `**/auth.json` explicitly git-ignored
(`.gitignore:15-16`).

**External environment dependencies (machine-level, not plugin config):**
- `C:\src\run-conda-pymol.bat` — the Windows conda-env PyMOL launcher, hard-coded in
  `smoke/run_smoke.sh:15`.
- Conda env `chemtools-win10` (recorded in
  `.planning/phases/01-bootstrap-pure-foundation/windows-env-versions.md`).

## Webhooks & Callbacks

**Incoming:** None (no HTTP surface).

**Outgoing (host-application callbacks):**
- PyMOL menu callback: Plugins → AA-match → `run_plugin_gui()` →
  `setup_window.open_window()` (`aamatch/__init__.py:29-39`).
- Wizard input callbacks: `GameWizard` click/key/panel-button handlers route to
  engine ops; panel button codes are `cmd.get_wizard().method(...)` strings built by
  `aamatch/wizard_text.py` and PParse'd at click time (instance-relative, never
  naming a module — dual-identity safe).
- `QtCore.QTimer` timeouts (countdown, 1 Hz game clock) and Qt signal/slot
  connections in the two QT TIER modules.

## Planned-but-absent (do not reference in code)

- **VMD/Tcl port (v2):** the `vmd/` directory does NOT exist in this repo. VMD 1.9.3
  (Windows, Tcl/Tk 8.5 + ttk) is reachable from WSL per root `AGENTS.md`, and
  `vmd-ref/` reference material is git-ignored (`.gitignore:6-8`) — but no v2 code,
  no `vmd/3rd_party_lib/`, nothing to map.
- **`.planning/research/`** contains verified domain research (`STACK.md`,
  `ARCHITECTURE.md`, `PITFALLS.md`, `FEATURES.md`, `SUMMARY.md`) used by the GSD
  workflow — planning docs, not runtime integrations.

---

*Integration audit: 2026-10-03*
