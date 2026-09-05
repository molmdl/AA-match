# Stack Research

**Domain:** PyMOL 2.5.0 open-source plugin — educational matching game of small-molecule ↔ amino-acid interactions (PyQt5 GUI + interactive 3D gameplay)
**Researched:** 2026-09-05
**Confidence:** HIGH (all API claims verified against the local PyMOL 2.5.0 source tree at `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/bioCHEMeleon/tmp/pymol-src/modules/pymol/` and the shipped v1 prior art at `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/AA-match/tmp/bioCHEMeleon/biochemeleon/`; exceptions marked LOW with a check-later note)

> **Citation convention:** `file:line` references without a path prefix mean
> `<pymol-src>/modules/pymol/<file>`. Prior-art references mean
> `tmp/bioCHEMeleon/biochemeleon/<file>` unless stated otherwise. Every claim
> below was read from these local trees on 2026-09-05 — nothing cited from
> memory.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| PyMOL open-source (host app) | 2.5.0 | Runtime host; owns the OpenGL viewer, event loop, cmd API | The game runs *inside* PyMOL as a plugin. Version verified from `pymol-src/ChangeLog` ("2021-05-10 … * 2.5.0", lines 3–6). Pin all development to this tree. |
| Python (inside PyMOL) | 3.6+ compatible | Plugin language | `pymol-src/INSTALL` REQUIREMENTS: "Python 3.6+". Writing 3.6-compatible syntax (no walrus, no positional-only params, no f-string `=` debug) guarantees it runs in the WSL 3.6.9 test shell *and* whatever 3.6–3.10 the Windows conda env ships. Verify the env's exact version once in the first headless smoke (`import sys; print(sys.version)`) — LOW confidence until that run. |
| PyQt5 (via `pymol.Qt`) | ships with PyMOL | All GUI: setup window, game-status tab, dialogs | `pymol/Qt/__init__.py:26–32` imports PyQt5 **first** (then PySide2, PyQt4, PySide). Access it only as `from pymol.Qt import QtWidgets, QtGui, QtCore` — the wrapper normalizes Signal/Slot naming (Qt/__init__.py:84–94) and is what the plugin loader itself uses (`plugins/installation.py:157`). |
| numpy | ships with PyMOL (hard dependency) | Interaction-detection geometry: distances, ring centroids, normals, rotation matrices | numpy is required to *build* PyMOL (`pymol-src/setup.py:459–461`) and imported at runtime by `chempy/brick.py:15` and `chempy/mmtf/io.py:12`. All six interaction criteria (H-bond, salt bridge, π-stacking, cation-π, hydrophobic, halogen, metal coordination) reduce to numpy vector math — no scipy/RDKit needed. |
| Wizard framework (`pymol.wizard.Wizard`) | built-in | Interactive gameplay loop: click AA → drag → detect | The only sanctioned hook into viewer mouse events in Python. Base class at `pymol/wizard/__init__.py:4–95`; event masks `event_mask_pick/select/key/…` (lines 6–15); callbacks `do_pick(bondFlag)` (:76), `do_select(name)` (:79), `do_key(k,x,y,mod)` (:82), panel via `get_panel()` (:52). Same mechanism all stock wizards use (17 stock wizards implement `do_pick`, e.g. `wizard/label.py:79`, `wizard/mutagenesis.py:715`). |
| `cmd.drag()` | built-in (2.5.0) | Object drag/rotate by mouse during gameplay | `editing.py:1018–1076`: "enables the user to manipulate the atom coordinates … using mouse controls similar to those for controlling the camera". Hard constraint documented in the docstring: "the selection of atom to drag must all reside in a **single molecular object**" (editing.py:1037–1038) → each grid AA must be its own object (or the drag selection must be one object's atoms). Internally installs the `Dragging` wizard (editing.py:1067–1074) and requires editor scheme 3 (wizard/dragging.py:49). |
| ChemPy model (`cmd.get_model` / `cmd.get_bonds`) | built-in | Coordinate + bond-graph snapshots for the detection engine | `cmd.get_model` returns a ChemPy "Indexed" model (`querying.py:1053–1070`); Atom class with `symbol/name/resn/vdw/alt/…` fields at `chempy/__init__.py:24+`. `cmd.get_bonds` returns `(atm1, atm2, order)` with an explicit warning that indices are 0-based and unrelated to atom `id` (`querying.py:1072–1096`) — needed for valence rendering and ring detection (π-stacking needs ring membership). |
| JSON (stdlib) + `cmd.save`/`cmd.load` | built-in | Setup save/load, game-state persistence, session save | Pure-layer persistence uses stdlib `json` (unit-testable in WSL). Scene/game-state snapshots use `cmd.save` (`exporting.py:782`) and `cmd.load` (`importing.py:635`). Prior art proves the pattern: `persistence.py` (279 lines, pure) + `.bcm` sidecar files. |

### The verified cmd API toolbox (what the game is built from)

Every call below verified at the cited location; this is the allowed vocabulary
for cmd-coupled layers.

| API | Citation | Game use |
|-----|----------|----------|
| `cmd.drag(selection, wizard, edit, quiet, mode)` | `editing.py:1018` | Player drags/rotates an AA onto the small molecule |
| `cmd.translate(vector, selection, state, camera)` | `editing.py:1610` | Programmatic placement: move AA from grid slot toward molecule |
| `cmd.rotate(axis, angle, selection, state, camera)` | `editing.py:1716` | Programmatic AA orientation (e.g. Reset-to-grid re-layout) |
| `cmd.transform_selection / transform_object / matrix_reset` | `editing.py:1946 / 2006 / 2126` | Whole-object 4×4 matrix moves (compose rotate+translate in one op; cheaper than consecutive translate/rotate) |
| `cmd.get_object_matrix(object, state, incl_ttt)` | `querying.py:89` | Read an AA's current pose after a player drag |
| `cmd.iterate(selection, expression, space=…)` | `editing.py:1490` | Read atom properties (name, elem, resn, **uppercase `ID`** — editing.py symbol table; prior-art AGENTS.md:91) |
| `cmd.iterate_state(state, selection, expression, space=…)` | `editing.py:1578` | Read **coordinates** (`x,y,z`) — `cmd.iterate` does NOT expose coords (prior-art AGENTS.md:98) |
| `cmd.get_model(selection, state)` | `querying.py:1053` | Bulk coordinate+bond snapshot for the detection engine |
| `cmd.get_bonds(selection, state)` | `querying.py:1072` | Bond graph for rings/valence (0-based indices — see warning above) |
| `cmd.get_distance(atom1, atom2, state)` | `querying.py:951` | Debug/QA distance checks (engine itself uses numpy on iterated coords) |
| `cmd.identify(selection, mode)` | `querying.py:1269` | Stable `(object, id)` atom keys for game-state bookkeeping (mode semantics verified by prior-art AGENTS.md:92 — id stable across .pse reload) |
| `cmd.count_atoms(selection)` | `querying.py:1412` | Guard clauses, grid occupancy checks |
| `cmd.get_object_list(selection)` | `querying.py:131` | Enumerate AA objects in the grid |
| `cmd.get_names / get_type / get_object_state` | `querying.py:1148 / 1199 / 1496` | Object inventory & type dispatch |
| `cmd.copy(target, source, zoom)` | `creating.py:867` | Clone AA templates into grid slots |
| `cmd.pseudoatom(object, name, resn, resi, chain, …)` | `creating.py:1082` | Sentinel/marker atoms. Prior-art caveat: return value is `None` — always re-read ids via `cmd.identify` (prior-art AGENTS.md:90) |
| `cmd.fuse(selection1, selection2, …)` | `editing.py:937` | Bond editing if a level needs covalent adjustment (2.5.0 ChangeLog: fuse now "disallows hypervalent bonds") |
| `cmd.load(filename, object, state, format)` | `importing.py:635` | Load curated demo molecules (small-molecule `.mol2/.sdf/.pdb` sets). Use `async_=0` for synchronous load (prior-art AGENTS.md:84) |
| `cmd.save(filename, selection, state, format)` | `exporting.py:782` | Save game session/level state |
| `cmd.zoom / center / orient / origin` | `viewing.py:65 / 133 / 281 / 227` | Camera framing per level |
| `cmd.mask / unmask(selection)` | `controlling.py:870 / 897` | Protect the small molecule from accidental drag (mask its atoms so drags only move AAs) |
| `cmd.set_key(key, fn)` | `controlling.py:719` | Optional keyboard shortcuts (e.g. R = reset AA to grid) |
| `cmd.set / get / get_setting` | `setting.py:348` (`get_setting`), `controlling.py` (`set`) | Settings: `mouse_selection_mode`, `button_mode`, `auto_zoom`, etc. |
| `cmd.set_wizard(instance)` / `get_wizard()` / `refresh_wizard()` | `wizarding.py:110 / 156 / 130` | Activate custom game wizard instance; `set_wizard` accepts a Wizard **instance** (wizarding.py:54 constructs by name then delegates to the same call) |
| `cmd.select(name, selection)` | `selecting.py` (thin C dispatch; command verified in stock wizards, e.g. prior-art `wizard.py:79`) | `cmd.select("pk1", name)` canonical select→pick map |
| `cmd.undo / redo` | **NOT AVAILABLE** — `editor.py:25–36` `undocontext`: "not implemented in open-source" (no-op stub) | Do not use. All destructive ops need the backup-snapshot pattern (see What NOT to Use) |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pymol.Qt` wrapper | built-in | Import shim selecting PyQt5 → PySide2 → PyQt4 → PySide | Always. `Qt/__init__.py:26–40` order is verified; in this PyMOL build PyQt5 resolves. |
| ChemPy (`chempy.*`) | built-in | Atom/Model container classes returned by `cmd.get_model` | Indirectly, via get_model/get_bonds. Do not import chempy directly unless a phase proves a need. |
| `pmg_qt` | built-in | PyMOL's own Qt GUI (`pmg_qt/pymol_gl_widget.py`, `pymol_qt_gui.py`) | Read-only reference for dialog/form patterns (`pmg_qt/forms/`). Do not import pmg_qt internals from the plugin. |
| stdlib: `json`, `random`, `math`, `time`, `os`, `copy`, `pickle` | 3.6 stdlib | Pure game layer: level generation logic, scoring, persistence | Entire pure layer. Zero non-stdlib imports there (see Architecture rule). |
| `unittest` + `unittest.mock.MagicMock` | 3.6 stdlib | WSL unit tests with `pymol`/`pymol.Qt` stubbed via `sys.modules` | All pure-layer tests. Pattern proven in prior art `tests/test_setup_state.py` (prior-art AGENTS.md:74). |

**No third-party additions.** The constraint "only what pymol-open-source
ships (PyQt5 via pymol.Qt, numpy)" is honored by this stack — every runtime
dependency above is inside the PyMOL 2.5.0 tree.

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| WSL `python3.6` (3.6.9) | Syntax check + pure-layer unit tests | `python3.6 -m py_compile <pkg>/*.py` then `python3.6 -m unittest tests.<mod> -v`. Never import PyMOL for real in WSL — stub it (prior-art AGENTS.md:74). Nothing may be installed (opencode.json denies `pip*`/`apt*`/`conda*`). |
| Headless Windows PyMOL via cmd.exe | cmd-only integration smoke tests (no Qt, no GUI) | Verified recipe from prior-art AGENTS.md:13–24: stage package + script to a `/mnt/c` path, then `cd tmp/<stage> && timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq <script.py>" 2>&1 | tail -50`; exit 0 = clean. Pure-cmd scripts run; anything touching `pymol.Qt.*` at runtime cannot run this way (GUI needs a real display) — those stay human-verify checkpoints. |
| Windows Plugin Manager (human step) | Install the packaged plugin into a real PyMOL session | `pymol/plugins/installation.py:186–352`: accepts single `.py`, package dir with `__init__.py`, or zip/tar.gz; installs to `%APPDATA%\pymol\startup` (installation.py:22–29). |
| Grep gates | Prevent forbidden-API regressions | Prior-art AGENTS.md:36–43 pattern: zero matches for `import tkinter\|import Pmw\|from PyQt5 import\|mainloop\|grab_set\|Toplevel\|menuBar.addmenuitem`; `.exec_()` hits allowed only on QFileDialog/QMessageBox, never the main dialog. |
| `wsl2win` staging copy | Make WSL-side package visible to Windows PyMOL | Prior-art `wsl2win_cp.sh` pattern (prior-art AGENTS.md:24). WSL→Windows path guard applies to any path embedded in scripts (Windows PyMOL cannot resolve `/mnt/c/...`). |

---

## Installation

There is **no pip/npm installation** — the plugin is distributed as source and
installed through PyMOL's Plugin Manager. The contract, verified from
`pymol/plugins/installation.py` + `pymol/plugins/__init__.py`:

1. **Package layout:** a single directory named after the plugin (e.g.
   `aamatch/`) containing `__init__.py`. `findPlugins` scans startup dirs for
   `.py` files *and* directories with `__init__.py`
   (`plugins/__init__.py:365–405`); zip/tar.gz installs require exactly one
   package with `__init__.py` (`installation.py:118–136`).
2. **Metadata block:** optional `# Key: value` comment lines at the very top
   of `__init__.py` are parsed as metadata — `Version`, `Citation-Required`
   (`plugins/__init__.py:193–228`). Put a version here so re-install
   version checks work (`installation.py:254–274`). Note: metadata must be
   the *first* thing in the file (parser stops at the first non-`#` line,
   plugins/__init__.py:199–204).
3. **Entry point:** module-level `__init_plugin__(app=None)` — called by the
   loader after import (`plugins/__init__.py:320–324`). Register menu entry
   with `from pymol.plugins import addmenuitemqt;
   addmenuitemqt('AA-match', open_gui)` (requires `HAVE_QT`;
   `plugins/__init__.py:100–108`). Prior-art reference:
   `__init__.py:129–138`. Register cmd-visible game commands with
   `cmd.extend` inside the module — the loader wraps `cmd.extend` during
   plugin load to track registered commands (`plugins/__init__.py:266–270`).
4. **Windows dev install:** copy the package to `%APPDATA%\pymol\startup\aamatch\`
   (`installation.py:22–29`) or use Plugin Manager → Install from file.
   Restart PyMOL or run `plugin_load aamatch` (`plugins/__init__.py:130–145,
   433`).
5. **Headless smoke path** — the full verified recipe, distilled from
   prior-art `tmp/bioCHEMeleon/AGENTS.md:13–26` (proven across all 12 shipped
   v1 phases). Facts behind it:
   - `C:\src\run-conda-pymol.bat` is a Windows cmd.exe batch that activates
     the conda env and passes all args through to
     `python .../pymol/__init__.py %*` — so `-cq` = command-line mode + quiet
     (no GUI, no OpenGL window).
   - PyMOL resolves relative script/data paths against the **cmd.exe cwd**,
     which is the WSL cwd mapped into Windows — always `cd` into the staged
     `/mnt/c` path first so Windows PyMOL can read it (a `\\wsl$` cwd also
     works but `/mnt/c` is the convention).
   - Wrap in `timeout` + `tail` — a stray dialog or blocking call hangs the
     run forever otherwise; expect ~30 s for a typical smoke.
   - Exit-code semantics: 0 = clean (a script's `sys.exit(1)` is caught by
     the wrapper); nonzero = crash.
   - Ceiling: anything touching `pymol.Qt.*` at runtime CANNOT run this way
     (Qt needs a real display) — Qt/GUI/picking behavior stays a
     human-verify checkpoint.

```bash
# --- Development checks (WSL, nothing installed) ---
python3.6 -m py_compile aamatch/*.py          # syntax gate
python3.6 -m unittest discover -s tests -v    # pure-layer tests (pymol stubbed)

# --- Headless cmd-only smoke (WSL → Windows conda PyMOL) ---
# 1. Stage the package + script to the Windows-visible path first:
bash wsl2win_cp.sh                            # stage aamatch/ to tmp/<stage>/aamatch/
mkdir -p tmp/<stage>/smoke && cp smoke/smoke_01.py tmp/<stage>/smoke/
# 2. Run headlessly (timeout + tail to avoid hangs):
cd tmp/<stage> && timeout 90 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\smoke_01.py" 2>&1 | tail -50
# 3. Check exit code: 0 = clean (or sys.exit(1) caught by wrapper); nonzero = crash.
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| **Wizard framework** for gameplay input (`do_pick`/`do_select`/`do_key`) | Raw `cmd.set("button_mode", …)` + polling `pk1`/`sele` selections | Never for this game. Button-mode swapping is fragile (Dragging wizard itself must save/restore `button_mode`, wizard/dragging.py:78–80, and requires editor scheme 3, :49). The prior art proved the wizard receives clicks in *both* picking and selection button modes via the `do_select`→`do_pick` map (prior-art `wizard.py:78–82`). |
| **`cmd.drag()`** for player drag/rotate | numpy-only rotate/translate on drag deltas from `do_key`/timer | Only if `cmd.drag`'s single-object constraint (editing.py:1037–1038) fights the grid design. Keep each AA as its own object and `cmd.drag` works per-AA. Fallback: implement drag via `do_key` motion events + `cmd.transform_selection` (editing.py:1946) — more code, full control. |
| **`cmd.get_model` + numpy** for detection geometry | PyMOL selection language (`within 5 of …`) for proximity | For quick debug/prototype proximity checks only. The `within` operator is C-layer (not visible in `selecting.py` — LOW confidence from local source alone); the six interaction criteria need angles/centroids/normals that selectors cannot express. numpy on `iterate_state` coords is fully unit-testable. |
| **`fitting.pair_fit`** (`fitting.py:710`) if template-superposition placement is wanted | numpy Kabsch/rotation math | pair_fit is a ready alignment tool but its 2.5.0 Python surface (kabsch algorithm details, quiet semantics) is unverified locally — numpy implementation is ~30 lines, deterministic, unit-testable. Prefer numpy; revisit pair_fit only if a phase needs PyMOL-internal alignment quality. (Note: there is **no** `pymol.pairwise` module in this tree — the ls of `modules/pymol/` contains no pairwise*.py.) |
| **JSON sidecar files** for game state | Pickling wizard state into the .pse session | Both. Wizards pickle their `__dict__` into sessions (`wizard/__init__.py:29–36 __getstate__/__reduce__`; session_save_wizard at `wizarding.py:176–179`) — keep wizard state small and picklable. But scores/levels/setup belong in JSON sidecars (pure-layer, testable, prior-art `persistence.py` pattern). |
| **Modeless Qt dialog (`dialog.show()`)** | Modal (`dialog.exec_()`) main window | Never for the main window — a modal dialog freezes the 3D viewer, killing gameplay. Prior art enforces modeless with a grep gate (AGENTS.md:41–43); module-level singleton ref prevents GC (prior-art `__init__.py:10–12`, citing `Pymol-script-repo/plugins/outline.py:46` pattern). `exec_()` is fine on QFileDialog/QMessageBox children. |
| **Single `python3.6`-compatible codebase** | Dropping to 3.7+ syntax | Never. 3.6 is the verified floor (INSTALL) and the WSL test shell is 3.6.9; 3.6-safe syntax runs unchanged on newer Pythons. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Tkinter / Pmw / `pmg_tk` | Legacy Tk GUI stack. `pymol.Qt` + `pmg_qt` replaced it (2.5.0 tree ships both; Qt wrapper is the sanctioned shim, Qt/__init__.py:1–9). Pmw is optional in INSTALL and absent from this conda env per prior art. Mixing Tk with the Qt main window breaks event loops. | PyQt5 via `from pymol.Qt import QtWidgets` |
| `from PyQt5 import …` (direct) | Bypasses PyMOL's binding shim; breaks if the host build uses PySide2, and violates the AGENTS dependency rule (prior-art AGENTS.md:70 + grep gate). | `from pymol.Qt import QtWidgets, QtGui, QtCore` |
| `threading.Thread` calling `cmd.*` | The cmd API must be called from the PyMOL/Qt main thread; prior art codified this as PITFALLS #6 ("NEVER threading.Thread with cmd.*", prior-art gui_game.py:6,108). Background threads are allowed only for pure-stdlib work (e.g. the prior art's fetch worker in `__init__.py:570–676`, drained back to the main thread via `QTimer.singleShot`). | `QtCore.QTimer` (1 Hz game timer, gui_game.py:108–109) + `QTimer.singleShot` for deferred steps |
| `cmd.undo` / `undocontext` | Explicit no-op in open-source: "not implemented in open-source" (`editor.py:25–36`). Any reliance silently loses state. | Snapshot-before-mutation: `cmd.copy('_backup', target)` (creating.py:867) + restore via `cmd.delete` + `cmd.create` (prior-art AGENTS.md:89 verified replace semantics in smoke tests) |
| Reading picked atoms via `index` | `index` shifts on any insert/delete; `cmd.identify` warns to use integral identifiers (`querying.py:1313–1317`, prior-art AGENTS.md:92). `cmd.iterate` exposes id as UPPERCASE `ID` (editing.py symbol table; prior-art AGENTS.md:91). | `cmd.identify(..., mode=0)` / `cmd.iterate(..., "stored.append((model, ID, alt, resv))", space={'stored': …})` |
| `space=None` on iterate/alter | Pollutes global `pymol.__dict__` (prior-art AGENTS.md:97, editing.py:59–60). | Always `space={'stored': mylist}` (or a dedicated dict) |
| New third-party Python libs (scipy, RDKit, pandas…) | Hard constraint: only pymol-open-source ships. numpy + stdlib cover every geometric need (distance, angle, dihedral, centroid, rotation via 3×3 matrices). | numpy + stdlib; if ever truly blocked, seek explicit user approval + vendor under `3rd_party_lib/` with license (repo AGENTS.md rule) |
| Network calls at runtime | Gameplay must work offline; demo sets are pre-downloaded (PROJECT.md). Prior art isolated fetch code from cmd entirely (prior-art demos.py:40,362). | Bundled demo data loaded with `cmd.load`; downloads happen at authoring time only |
| `cmd.iterate` for coordinates | Coordinates are state-dependent and NOT exposed by `cmd.iterate` (prior-art AGENTS.md:98). | `cmd.iterate_state(state, sele, "stored.append((x,y,z))", space=…)` (editing.py:1578) or `cmd.get_model` |
| `pymol.pairwise` (mentioned in some docs) | No such module exists in this 2.5.0 tree. | `fitting.pair_fit` (fitting.py:710) if needed; else numpy |

## Stack Patterns by Variant

**If gameplay stays click+drag only (MVP):**
- One custom Wizard (`GameWizard`) handling `do_pick`/`do_select` + `cmd.drag`
  for placement. Mirror prior-art `PickWizard.activate()/deactivate()` save &
  restore of the prior wizard + `mouse_selection_mode` (prior-art
  `wizard.py:84–91`).

**If per-atom fine adjustment is added (rotate single AA torsion):**
- Stay in the wizard: `do_key` (event_mask_key, wizard/__init__.py:8,82) for
  arrow-key nudges + `cmd.rotate(axis, angle, selection)` (editing.py:1716).
  Avoid entering PyMOL's 3-button *editing* mode (`get_editor_scheme()==3`,
  editing.py:1123) during gameplay — it changes global mouse semantics.

**If level molecules must be regenerated at runtime (not just loaded):**
- Prefer curated data files + `cmd.load` (PROJECT.md demo-set direction).
  Programmatic construction (`cmd.pseudoatom` + `cmd.bond`/`fuse`) cannot
  guarantee protonation/valence correctness without heavy own chemistry
  logic — treat as a research-flagged phase, not a stack feature.

**If a future milestone adds VMD parity:**
- None of this stack transfers (VMD is Tcl/Tk). The pure layer
  (setup_state/generators/persistence/scoring) is deliberately stdlib-only so
  it can be ported; every cmd/Qt module is PyMOL-only by design.

## Version Compatibility

| Component | Compatible With | Notes |
|-----------|-----------------|-------|
| Plugin code (3.6-safe) | Python 3.6 → 3.10+ | 3.6 floor verified (INSTALL "Python 3.6+"). Windows conda env exact version unverified locally — one-time check `import sys; print(sys.version)` in first headless smoke (LOW until run). |
| `pymol.Qt` | PyQt5 (primary), PySide2, PyQt4, PySide | Import order verified Qt/__init__.py:26–61. Code against the shim's normalized API (Signal/Slot aliases :84–94); never the raw binding. |
| PyMOL 2.5.0 cmd API | PyMOL 2.x | Signatures cited from the 2.5.0 tree; 2.5.0-specific ChangeLog entries (e.g. hypervalent-guard on fuse) confirm 2.5.0 behavior, not 2.4. |
| Qt version (5.12/5.15 class) | whatever conda env ships | `QtCore.QT_VERSION_STR` readable at runtime (Qt/__init__.py:90–94 maps PySide→QT_VERSION_STR). Only relevant if using version-gated Qt APIs — avoid needing them. |
| Plugin package | Plugin Manager install contract | Single package + `__init__.py`; metadata first lines; `__init_plugin__(app=None)` entry (verified above). |

## Confidence Assessment

| Recommendation | Level | Basis |
|----------------|-------|-------|
| PyMOL 2.5.0 host + Python 3.6+ floor | HIGH | ChangeLog:3–6; INSTALL REQUIREMENTS |
| PyQt5 via `pymol.Qt` only | HIGH | Qt/__init__.py:26–40; plugins/installation.py:157; prior-art grep gate |
| Wizard framework as the input layer | HIGH | wizard/__init__.py:4–95; 17 stock wizards; prior-art PickWizard in production v1 |
| `cmd.drag` for player drag | HIGH | editing.py:1018–1076 incl. single-object constraint docstring |
| numpy for the detection engine | HIGH | setup.py:459–461; chempy imports; geometry needs exceed selector language |
| Backup-snapshot instead of undo | HIGH | editor.py:25–36 no-op stub + prior-art smoke-verified restore pattern |
| Headless cmd.exe smoke recipe | HIGH | prior-art AGENTS.md:13–24, proven across v1 phases |
| Windows env Python/Qt exact versions | LOW | Not in local sources — one-time runtime check in first headless smoke |
| `within/near_to` selector ops availability | LOW | C-layer, not in Python sources; avoid depending on it (numpy engine) |
| `chempy/fragments` as molecule source | LOW | Directory exists but contains only `__init__.py` — do not plan around it |

## Sources

- **Local PyMOL 2.5.0 source** `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/bioCHEMeleon/tmp/pymol-src/` — ChangeLog, INSTALL, setup.py, `modules/pymol/*` (all file:line citations above) — HIGH
- **Prior art (shipped v1 plugin, same constraints)** `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/AA-match/tmp/bioCHEMeleon/` — AGENTS.md (headless recipe, grep gates, pitfall ledger), `biochemeleon/__init__.py` (entry point, GC-singleton, fetch worker), `wizard.py` (PickWizard pattern), `gui_game.py` (QTimer pattern), `game.py` (controller composition root) — HIGH (runtime-verified in v1)
- **Reference plugins** `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/AA-match/Pymol-script-repo/plugins/` — menu/dialog idioms (outline.py module-singleton pattern) — MEDIUM (read-only reference, not runtime-verified here)

---
*Stack research for: AA-match — PyMOL 2.5.0 interaction-matching game plugin*
*Researched: 2026-09-05*
