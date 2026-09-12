# Phase 4: Qt Setup Window — Research (Window Architecture & Lifecycle)

**Researched:** 2026-09-13
**Domain:** Modeless Qt window inside PyMOL 2.5.0 — architecture, lifecycle, headless-vs-human verification
**Confidence:** HIGH for all borrowed-pattern and seam facts (every claim read from shipped v1 source, the local PyMOL 2.5.0 tree, or this repo's own code with file:line); LOW/UNVERIFIED only for headless **widget construction** (probe proposed, §verification_tiers Q1).

**Citation shorthand:**
- `PA-__init__` = `tmp/bioCHEMeleon/biochemeleon/__init__.py` (shipped v1, read 2026-09-13)
- `PA-setup` = `tmp/bioCHEMeleon/biochemeleon/gui_setup.py`
- `PA-game` = `tmp/bioCHEMeleon/biochemeleon/gui_game.py`
- `pymol-src/<f>` = `pymol-src/modules/pymol/<f>` (repo-root symlink; PyMOL 2.5.0 tree)
- Repo files cited as plain paths.

---

## Summary

The modeless-window problem is fully solved by shipped prior art: bioCHEMeleon opened a `QtWidgets.QDialog` via a **module-level singleton + `.show()`/`.raise_()`/`.activateWindow()`** trio, never `.exec_()`, never a `closeEvent` override (default close hides; the singleton reference prevents GC, so re-open is reuse-and-raise). Every piece of that pattern transfers — EXCEPT one: v1 put the Qt class *and module-level Qt imports* in `__init__.py`, which AA-match's Gate A2 forbids. The AA-match shape is therefore: a **new Qt-tier module** (proposed `aamatch/setup_window.py`) holding the class + the singleton + an `open_window()` entry, lazily imported inside `run_plugin_gui` (zero-module-level-imports contract preserved; `run_plugin_gui`'s current `gamestart.start_game()` AST contract in `tests/test_package_skeleton.py:110-154` is *deliberately replaced* in the same task — recorded 03-05 precedent).

The planning-critical discovery is the **verification split**: v1's headless smokes (`smoke/phase5_smoke.py:16-18`) imported the v1 package, executing v1's module-level `from pymol.Qt import ...` (`PA-__init__:156-157`) — proving **`import pymol.Qt` succeeds headless in this exact Windows conda env**. What is NOT proven is widget *construction* (needs a QApplication; PyMOL `-cq` builds none). One cheap probe (`QT_QPA_PLATFORM=offscreen` + minimal QApplication/QDialog) decides whether Phase 4 gets a full headless widget-test tier (construct dialog, `apply_state`/`collect_state` round-trip, `btn.click()` drive-through) or whether widget behavior stays [HUMAN]-only with cmd-tier handlers factored out for headless proof. Everything else (purity gates, seam reuse, 7-button delegation targets, threading rules) is already fixed by repo law.

**Primary recommendation:** New `aamatch/setup_window.py` (Qt tier, never `PURE_MODULES`): module-level `from pymol.Qt import ...` legal there; module-level `_window = None` singleton; `open_window()` = create-if-None → `show()` → `raise_()` → `activateWindow()` → return the dialog (assertion handle, 03-05 pattern); the dialog class holds the 7-field form (`collect_state`/`apply_state` round-trip with a `_loading` guard) and delegates all 7 buttons to existing pure/cmd APIs — Start through `gamestart.start_game()` imported *inside the handler*. Re-point `run_plugin_gui` to it; update the two source-gate tests deliberately; settle the offscreen probe FIRST because it dictates every plan's `<verify>` shape.

---

## standard_stack

Borrowed patterns + verified APIs. Nothing new is installed — Qt comes from `pymol.Qt` only.

### The verified Qt import surface

| Fact | Citation |
|---|---|
| Import form is ALWAYS `from pymol.Qt import QtWidgets[, QtCore, QtGui]` — the wrapper tries **PyQt5 first** (`QT_API` unset/'pyqt5'), then PySide2 → PyQt4 → PySide; raises `ImportError` if none | `pymol-src/Qt/__init__.py:24-64` (PyQt5 at :26-32) |
| The import pulls `QtGui, QtCore, QtOpenGL, QtWidgets` as a unit | `pymol-src/Qt/__init__.py:28` |
| Signal/Slot names are normalized on the wrapper (`QtCore.Signal = QtCore.pyqtSignal` for PyQt) — code against the shim, never the raw binding | `pymol-src/Qt/__init__.py:84-94` |
| `addmenuitemqt` raises `QtNotAvailableError` when `HAVE_QT` is False (default False, :29); the plugin loader catches it cleanly (:287-288) — the headless-safe menu registration design AA-match already uses | `pymol-src/plugins/__init__.py:100-108, 29, 33, 287-288` |
| `from PyQt5 import ...` is BANNED (bypasses the shim; violates the dep rule + v1 grep gate) | v1 AGENTS.md grep gate; PITFALLS.md:106 |

### Borrowed pattern 1 — the modeless open (THE core borrow)

Every line verified in shipped v1:

| Step | v1 code | Citation |
|---|---|---|
| Module-level singleton, GC prevention: `dialog = None` — comment: "MUST be module scope, not inside `__init_plugin__`, or the dialog flashes and vanishes" | `dialog = None` | `PA-__init__:3-5` |
| Menu handler reuses, never duplicates: `global dialog; if dialog is None: dialog = PluginDialog()` then `dialog.show(); dialog.raise_(); dialog.activateWindow()` | `run_plugin_gui` | `PA-__init__:141-153` |
| Main window class: `PluginDialog(QtWidgets.QDialog)`, no parent, `setMinimumWidth(420)`, QTabWidget | `PA-__init__:160-190` |
| Modeless by construction: `.show()`, NEVER `.exec_()` on the main dialog — "blocks the PyMOL event loop and the viewer" | `PA-__init__:144-146` |
| Modal children ARE allowed: `QFileDialog.getSaveFileName` (static, owns its own loop), `QMessageBox.warning`, `QInputDialog.getText`, and one child `QDialog.exec_()` (Help) — all on child dialogs only | `PA-__init__:691-696, 949-972`; `PA-setup:450-451, 646-668` |
| **No `closeEvent` override anywhere** (repo-wide grep: zero matches) — default close = hide; the singleton ref keeps the object alive; re-open = `show()+raise_()`. This IS the "window survives minimize/re-open" mechanism (SETUP-01) | grep `closeEvent` over repo incl. `tmp/bioCHEMeleon`: no matches |
| Double menu fire → same window raised, never two instances | `PA-__init__:148-153` |

### Borrowed pattern 2 — form/state separation (collect/apply round-trip)

v1's Setup tab is a dumb form; the DIALOG owns the action handlers:

- `SetupTab.collect_state()` → JSON-serializable dict of every widget (`PA-setup:539-557`); `apply_state(state)` repopulates with missing-key tolerance + a `self._loading` flag that suppresses cascading recompute (`PA-setup:559-617`, flag init `:77`).
- Reset = `apply_state(DEFAULTS)` (`PA-setup:315`); Randomize = pure `randomize_state(...)` → `apply_state(result)` (`PA-setup:620-642`).
- Action buttons live on the dialog: `self.setup_tab.start_btn.clicked.connect(self._on_start)` etc. (`PA-__init__:200-220`); handlers `_on_start`/`_on_cleanup`/`_on_export` are dialog methods (`PA-__init__:242-261, 915-946, 679-720`).

**AA-match adaptation (required):** v1's `__init__.py` has module-level `from pymol.Qt import ...` (`PA-__init__:156-157`) — **Gate A2 forbids this for AA-match** (`tests/test_purity.py:214-230` scans only module-level imports in `aamatch/__init__.py`). The class + singleton + handlers move into the new Qt-tier module; `__init__.py` keeps a pure lazy delegation (see architecture_patterns).

### The AA-match seams the buttons delegate to (all existing, all verified)

| Button | Delegate | Citation |
|---|---|---|
| Start | `gamestart.start_game(setup=validated_state, seed=?)` — cleanup FIRST → new_game → materialize → conditional-replace activate → camera framing; returns live wizard; setup validated fail-closed inside `new_game` | `aamatch/gamestart.py:221-254` (seam contract `:8-13`); `aamatch/engine.py:183` |
| Cleanup | `placement.cleanup_game_objects()` — prefix-only `_aam_` deletion, returns `{'deleted': n}`; docstring: "Full Cleanup-button semantics ... are Phase 4" | `aamatch/placement.py:404-417` |
| Generate & export | `engine.new_game(setup, seed)` → payload → versioned container write via `persistence.make_container/save_container` (KINDS already includes `'level_spec'` and `'game'`) | `aamatch/engine.py:183`; `aamatch/persistence.py:34-37, 44, 131` |
| Save Setup | `persistence.save_setup_file(path, state)` — versioned `'setup'` container, `validate_state` before write | `aamatch/persistence.py:145-153` |
| Load Setup | `persistence.load_setup_file(path)` — versioned container + `validate_state` on read | `aamatch/persistence.py:156-165` |
| Reset | `apply_state(setup_state.DEFAULTS)` | `aamatch/setup_state.py:54-63` (DEFAULTS); `PA-setup:315` pattern |
| Randomize | `setup_state.randomize_state(seed=None)` → `apply_state` | `aamatch/setup_state.py:147` |
| (field validation) | `setup_state.validate_state` — NEVER widget-side re-validation | `aamatch/setup_state.py:90` |

The 7-field setup model the form maps to — single source of truth `aamatch/setup_state.py:40-63`:

```python
INTERACTION_TYPES = ["h_bond", "salt_bridge", "pi_stacking", "cation_pi",
                     "hydrophobic", "halogen", "metal"]        # :40-41
INTERACTION_MODES = ["exclusive", "block_exclusive", "unset"]  # :43
MOLECULES_DEFAULT, MOLECULES_MIN, MOLECULES_CAP = 2, 1, 10     # :46
DIFFICULTY_DEFAULT, DIFFICULTY_MIN, DIFFICULTY_CAP = 3, 1, 10  # :50
DEFAULTS = {
    "source_mode": "demo",        # "demo" | "upload"          (:56)
    "demo_set_id": "",            # manifest id                (:57)
    "upload": None,               # None | {"path","sha256"}   (:58)
    "molecules_per_level": 2,     # clamp [1, 10]              (:59)
    "difficulty_levels": 3,       # clamp [1, 10]              (:60)
    "interaction_mode": "unset",  # SETUP-06                   (:61)
    "allowed_interactions": [],   # INTERACTION_TYPES members  (:62)
}
```

### Installation / commands (unchanged from repo law)

```bash
# WSL dev gates (nothing new needed):
python3.6 -m py_compile aamatch/*.py          # Gate D covers the new module
python3.6 -m unittest discover -s tests -v    # purity gates + source gates
# Headless Windows PyMOL (cmd-tier parts + the Q1 probe):
bash smoke/run_smoke.sh smoke/<script>.py     # greps === SMOKE-NN PASS ===
```

---

## architecture_patterns

### Recommended module layout

```
aamatch/
├── __init__.py          # UNCHANGED CONTRACT: zero module-level imports (Gate A2).
│                        # run_plugin_gui body becomes:
│                        #     from . import setup_window
│                        #     return setup_window.open_window()
├── setup_window.py      # NEW — Qt tier (never PURE_MODULES):
│                        #   module-level: from pymol.Qt import QtCore, QtGui, QtWidgets
│                        #   module-level: _window = None  (the GC-prevention singleton)
│                        #   def open_window():  create-if-None -> show -> raise_ -> activateWindow
│                        #   class SetupWindow(QtWidgets.QDialog):  form + 7-button handlers
├── gamestart.py         # unchanged — Start's seam (called from inside the handler)
├── placement.py         # unchanged — Cleanup's engine (cleanup_game_objects)
├── engine.py            # unchanged — Generate's engine (new_game)
├── persistence.py       # unchanged — Save/Load Setup + export container
└── setup_state.py       # unchanged — DEFAULTS / validate_state / randomize_state
```

Why the singleton lives in `setup_window.py`, not `__init__.py`: an assignment (`_window = None`) is Gate-A2-legal in `__init__.py` (only *imports* are banned), but keeping it beside the class that owns it keeps `__init__.py` a pure delegation shell AND makes the window reachable for later phases (`from . import setup_window; setup_window.get_window()`). Module-identity safety holds either way: under one session identity (`aamatch` OR `pmg_tk.startup.aamatch`) the lazy `from . import setup_window` always resolves the sibling from the SAME package object — the law (AGENTS.md gate 5, "never mix both mechanisms in one session") is satisfied by construction.

### Wiring pattern (menu → window → seam)

```python
# aamatch/__init__.py (rewired) — shape only, per Gate A2
def run_plugin_gui():
    from . import setup_window          # lazy; Gate A2 + module-identity law
    return setup_window.open_window()   # returns the dialog (assertion handle)

# aamatch/setup_window.py (shape only — research, not implementation)
from pymol.Qt import QtWidgets, QtCore, QtGui   # module level: LEGAL in Qt tier

_window = None                                   # module scope = GC prevention

def open_window():
    global _window
    if _window is None:
        _window = SetupWindow()
    _window.show()
    _window.raise_()                # idempotent re-open: same window, raised
    _window.activateWindow()
    return _window                  # assertion handle (03-05 pattern)

class SetupWindow(QtWidgets.QDialog):
    # ... 7-field form; collect_state()/apply_state() with _loading guard ...
    def _on_start(self):
        state = self.collect_state()
        from . import setup_state, gamestart      # lazy relative imports
        validated = setup_state.validate_state(state)   # fail-closed BEFORE the seam
        return gamestart.start_game(setup=validated, seed=42)
```

**Sibling-import discipline:** follow `aamatch/wizard.py`'s recorded contract (`wizard.py:22-29`, contract 2) — `from . import <sibling>` INSIDE handler methods, never at module level in the Qt module. `pymol.Qt` (and `pymol.cmd` if the window ever needs it directly) may be module-level here — that is what makes the module *Qt tier*.

### Pattern: synchronous handlers, no threads

- All button handlers run **synchronously on PyMOL's main/GUI thread**. `threading.Thread` + `cmd.*` = deadlock class (STACK.md:172; PITFALLS #15). AA-match forbids network at runtime, so v1's only async case (QProgressDialog + worker + QTimer drain for online fetches, `PA-__init__:545-677`) has **no AA-match counterpart** — do not borrow it.
- Generate & Export may take seconds (< 30 s budget, PITFALLS #15): accept the brief freeze, or set a `QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)` + disable buttons around the synchronous block (v1 used neither for its synchronous bundled-demo path — simplest acceptable). `processEvents`-chunking is overkill for Phase 4 sizes.
- No QTimer in Phase 4. Timer law for Phase 5 (recorded, not needed here): `QtCore.QTimer` on the Qt main thread only — `PA-game:108-111` (1 Hz pattern), STACK.md:172.

### Window/game interplay

- The window stays open while a game runs — the GameWizard stack and the Qt window are independent surfaces (v1 kept exactly this shape: dialog + active wizard simultaneously).
- Start mid-game is already hygienic: `start_game` runs `cleanup_game_objects()` FIRST and uses conditional-replace (`replace=1` iff prior top-of-stack is a GameWizard) — `aamatch/gamestart.py:239-245`, proven by SMOKE-08 both paths.
- **Cleanup mid-game is the one NEW hazard** (see pitfalls P7): `cleanup_game_objects()` deletes game objects but does NOT touch the wizard stack (`placement.py:404-417` — and its docstring defers "full Cleanup-button semantics" to Phase 4). A Cleanup handler must pop the game wizard if and only if `isinstance(cmd.get_wizard(), GameWizard)` via the canonical `cmd.set_wizard()` None-pop (`aamatch/wizard.py:31-39` — the C layer pops, runs cleanup, prior wizard auto-resumes). Never pop a user's wizard.

### Anti-patterns to avoid (all v1-gate-verified)

- **`.exec_()` on the main window** — freezes the viewer; modal forms only on child file/message dialogs (`PA-__init__:949-955` states the rule; PITFALLS #4).
- **Dialog as a local variable** — GC'd in a flash (`PA-__init__:3-5` comment; PITFALLS #4).
- **New instance per menu fire** — duplicates windows; reuse+raise instead (`PA-__init__:148-153`).
- **Qt imports in `aamatch/__init__.py` at module level** — Gate A2 violation; also what forced v1's MagicMock stubs (PITFALLS #1, #4).
- **Widget-side validation logic** — the pure layer owns validate/clamp (`setup_state.validate_state`); the form only collects/applies.
- **`logging`/`print` in the module** — house rule: no logging framework; handler errors propagate fail-closed (ValueError family) to PyMOL's menu handler, user-facing status via QMessageBox (repo CONVENTIONS.md "Logging: None in library code").

---

## verification_tiers

**THE planning-critical table.** What a Phase-4 plan's `<verify>` can run headlessly vs what must be a [HUMAN] checkpoint.

| Tier | Runs where | PROVEN today (with evidence) | Covers |
|---|---|---|---|
| **T0 — WSL static** | `python3.6`, repo root, zero stubs | Gate D py_compile of the new module (`tests/test_purity.py:255-276` scans ALL `aamatch/*.py`); Gate A2 untouched (`:214-230`); AST source gates modeled on `tests/test_wizard_source.py` (AST immune to docstring prose — `:12-19`); `SCANNED_MODULES` growth (`test_wizard_source.py:48-51`); updated `test_package_skeleton` AST contract (see P9) | import form (`pymol.Qt`, never `from PyQt5 import`), no `.exec_()` on the main window class, module not in `PURE_MODULES`, singleton-at-module-scope shape, lazy sibling imports in handlers, 3.6 syntax |
| **T1a — headless PyMOL, imports only** | `bash smoke/run_smoke.sh` → `cmd.exe /c ... -cq` | **`import pymol.Qt` works headless in this exact conda env** — v1's `smoke/phase5_smoke.py:1-2,16-18` ran `pymol -cq` with `from biochemeleon import ...`, executing v1's module-level `from pymol.Qt import QtCore, QtGui, QtWidgets` (`PA-__init__:156-157`) on every run | `import aamatch.setup_window` succeeds headless; module-level Qt binding loads (PyQt5 QtGui/QtCore/QtOpenGL/QtWidgets, `pymol-src/Qt/__init__.py:28`) |
| **T1b — headless PyMOL, widget construction** | same, via the **Q1 offscreen probe** (below) | **UNVERIFIED — probe required.** No `QApplication` exists in `-cq` mode; `QtWidgets.QDialog()` without one fails ("QWidget: Must construct a QApplication before a QWidget" — Qt semantics, env-behavior unproven). `QT_QPA_PLATFORM=offscreen` availability in the conda PyQt5 is unrecorded (repo-wide grep: zero prior use) | IF the probe passes: construct dialog + `apply_state`/`collect_state` round-trip + `btn.click()` drive-through + handler→seam calls (cmd works headless) — the entire window logic headlessly. IF it fails: widget tier stays T2-only and handlers must be factored as module-level functions (construct-free) for T1 coverage |
| **T2 — [HUMAN] real PyMOL GUI** | Windows conda PyMOL, real display | Never machine-provable (PITFALLS #1: "Qt/GUI behaviors are human-verify checkpoints by design") | SETUP-01 modeless interactivity (viewer rotates while window open), minimize/re-open, double-menu-fire raise, layout/UX readability, modal children (Save/Load/Upload file dialogs), Start→gameplay feel, Cleanup feel, tooltips |

**Q1 — the offscreen probe (run FIRST, cheapest plan task).** A `smoke/` script, run via `run_smoke.sh`, that: (1) `from pymol.Qt import QtWidgets, QtCore` (T1a baseline); (2) `app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(['pymol-probe'])` under `QT_QPA_PLATFORM=offscreen` (set via `os.environ` BEFORE the Qt import, or accepted as a `-cq` env passthrough — try both); (3) construct a throwaway `QDialog`, `show()`, `collect/apply` a dict round-trip on a stub widget set, `app.processEvents()`, print `=== PROBE PASS ===`. **Probe hygiene:** it must NOT open any modal (`QFileDialog`/`QMessageBox`/`.exec_()`) — a modal in a headless probe blocks forever (the `timeout` in `run_smoke.sh` is the backstop). If `offscreen` is unavailable, retry with the default windows platform (cmd.exe inherits the interactive desktop session); record whichever platform works. Verdict feeds every Phase-4 verify step.

**Tier-split rule for plans:** every verify step must name its tier. T0 for all source contracts; T1a for import-proof; T1b *only after* Q1 passes (else degrade to T1a+T2); T2 as explicit [HUMAN] checkpoints per ROADMAP success criteria (all four are [HUMAN]).

---

## dont_hand_roll

| Problem | Don't build | Use instead | Why |
|---|---|---|---|
| Setup validation/clamping | Widget-level range checks re-implemented in Qt slots | `setup_state.validate_state` (`setup_state.py:90`) — spinbox ranges mirror the constants (`MOLECULES_MIN/CAP` etc.), but validation authority stays pure | One home (CONVENTIONS.md single-home rule); WSL-tested |
| Setup file format | Raw `json.dump`/`json.load` (v1 did this, `PA-setup:644-659, 661-686`) | `persistence.save_setup_file`/`load_setup_file` (`persistence.py:145-165`) — versioned container, refuse-foreign/newer, validate both sides | AA-match already has the BETTER API v1 lacked |
| Game start | Re-implementing cleanup→generate→materialize→activate in the window | `gamestart.start_game` seam (`gamestart.py:221-254`) — the recorded Phase-4 contract (`gamestart.py:8-13`) | Restart hygiene + camera framing + conditional-replace already proven (SMOKE-08, 31 checks) |
| Cleanup | `cmd.get_names` + string filtering in the handler | `placement.cleanup_game_objects()` (`placement.py:404-417`) — prefix-only rule | Never chemical filters (PITFALL 13) |
| Window singleton/raise | Custom focus/z-order management | Copy the `PA-__init__:141-153` trio verbatim (show/raise_/activateWindow) | Proven on this exact PyMOL build |
| Upload file hashing | Custom hash loop | `hashlib.sha256` over chunks in the handler → `setup_state` `upload` field `{"path","sha256"}` (`setup_state.py:57-58`) | Field shape already frozen in DEFAULTS |
| Export container | Ad-hoc dict + bare json | `persistence.make_container`/`save_container` (`persistence.py:44, 131`) with a KINDS member | Version-gate discipline (two-version-gates law) |
| User-visible file paths | Raw `/mnt/c/...` passthrough | `paths.to_windows_path` before any `cmd.load`-adjacent use (`aamatch/paths.py`) | WSL→Windows guard (PITFALL 2) |

---

## common_pitfalls

**P1 — `.exec_()` on the main window.** Blocks PyMOL's event loop → viewer dead → SETUP-01 fails. Modal `.exec_()`/static file dialogs on CHILDREN only (`PA-__init__:949-972`). Gate: AST/grep — `.exec_()` hits allowed only on QFileDialog/QMessageBox/child dialogs, never `SetupWindow` (v1 gate, PITFALLS #4).

**P2 — GC'd dialog.** Window flashes and vanishes. Singleton MUST be module scope in `setup_window.py` (`PA-__init__:3-5` comment is the receipt).

**P3 — Second window on double menu fire.** `open_window()` must reuse-and-raise (`PA-__init__:148-153`), not construct unconditionally.

**P4 — Qt import in the wrong place.** `from PyQt5 import` banned everywhere; module-level Qt imports banned ONLY in `aamatch/__init__.py` (Gate A2, `tests/test_purity.py:214-230`) — legal and REQUIRED at module level in the Qt-tier module (class definition needs `QtWidgets` at class-creation time). A Qt-tier module must NEVER be added to `PURE_MODULES` and must NEVER be imported by WSL tests (no sys.modules stubs anywhere — repo purity law; T0 covers it by AST only).

**P5 — Headless probe blocks forever.** Any modal (`exec_`, static `getSaveFileName`, `QMessageBox`) inside a T1b probe hangs the smoke until `run_smoke.sh`'s timeout. Probe scripts construct widgets only; modal behavior is T2.

**P6 — Cleanup mid-game leaves a dangling GameWizard.** `cleanup_game_objects()` deletes `_aam_*` objects but never touches the wizard stack (`placement.py:404-417`). After a mid-game Cleanup the active GameWizard's registry points at deleted objects → subsequent picks operate on a dead registry (exact failure mode UNVERIFIED-in-this-build — cheap T1 probe: cleanup mid-game then scripted pick; expect a clean EngineError/ WizardError or a no-op, never a crash). Design: the Cleanup handler pops the wizard iff `isinstance(cmd.get_wizard(), GameWizard)` via `cmd.set_wizard()` (None-pop, `aamatch/wizard.py:31-39`), mirrors v1's `_on_cleanup` wizard teardown (`PA-__init__:925-928`).

**P7 — Threading any cmd work.** Handler code runs on the main thread; `threading.Thread` + `cmd.*` deadlocks (STACK.md:172). No async machinery in Phase 4 (network is forbidden by spec; v1's async fetch drain has no AA-match counterpart).

**P8 — 3.6 syntax floor + house style.** Gate D compiles the new module under python3.6 (`tests/test_purity.py:255-276`); no f-strings (house `%`-format convention, CONVENTIONS.md); module docstring opens with the layer declaration adapted verbatim ("Qt TIER ... never PURE_MODULES ... NO placement/engine imports at module level" style, per `aamatch/wizard.py:3-6` shape).

**P9 — The rewire breaks two recorded tests; update them deliberately, don't work around.**
- `tests/test_package_skeleton.py:110-154` asserts `run_plugin_gui` carries `from . import gamestart` + `return gamestart.start_game()` — after rewiring it must assert `from . import setup_window` + `return setup_window.open_window()` (exact 03-05 precedent of replacing a stale contract test: 03-05-SUMMARY.md:103-109).
- `tests/test_wizard_source.py:51` `SCANNED_MODULES` grows one line for the new cmd/Qt-tier UI module (`'setup_window.py'`) — the recorded growth protocol (:48-50).
- `tests/test_code_audit.py` PROSE_PIN: a new module whose docstring mentions banned tokens (`get_model`/`matrix_reset`/`get_object_ttt`) trips `test_prose_mentions_pinned_exactly` (`test_code_audit.py:64-67, 351-371`; heads-up recorded in STATE.md:175). Write docstrings without those tokens.

**P10 — SMOKE-08 re-point.** `smoke/smoke_08_starter.py` currently calls `aamatch.run_plugin_gui()` directly and asserts on the returned wizard (03-05-SUMMARY.md:66, :95). After the rewire that path opens a Qt window. Phase 4 must update SMOKE-08 to call the seam (`gamestart.start_game`) directly — or, if Q1's probe passes, optionally assert the window path too. Either way: a planned test evolution, not a regression.

**P11 — Timer-fairness law (recorded for later, cheap to respect now).** v1 pauses the timer around modal file dialogs (`PA-__init__:745-765` — pause-capture-dialog-save-resume). Phase 4 has no timer, but Save/Load/Upload handlers should be shaped so Phase 5 can adopt the pattern without rework (ROADMAP Phase-5 research notes repeat this rule).

**P12 — Display-rebuild law adjacency.** The window itself recolors nothing; if any Phase-4 handler path ever triggers a recolor (it shouldn't — Generate/Start materialize fresh objects), the 03-06 law applies: rebuild display lists; headless color-map equality ≠ on-screen color (03-06-SUMMARY.md:100, :142).

---

## State of the art (what changed vs v1)

| v1 (bioCHEMeleon) | AA-match Phase 4 | Why |
|---|---|---|
| Qt class + module-level Qt imports in `__init__.py` (`PA-__init__:156-190`) | Class in a dedicated Qt-tier module; `__init__.py` stays zero-import (Gate A2) | v1's shape forced MagicMock stubs in every WSL test (PITFALLS #1); AA-match's gates forbid both |
| Setup files = raw `json.dump` (`PA-setup:644-659`) | Versioned container via `persistence.save_setup_file` | Two-version-gates law (AGENTS.md gate 4) |
| Async network fetch machinery (QProgressDialog + worker + drain, `PA-__init__:545-677`) | **Drop entirely** — offline by spec | No AA-match counterpart exists |
| Wizard deactivate-on-cleanup via saved reference (`PA-__init__:925-928`) | Stack-native None-pop iff top is a GameWizard (`aamatch/wizard.py:31-39`) | AA-match's stack-native lifecycle law (03-03) supersedes the v1 saved-wizard pattern |
| Headless story: "anything touching pymol.Qt cannot run headless" (v1 AGENTS.md) | **Refined:** import-headless PROVEN (T1a); widget-headless UNVERIFIED (Q1 probe) | v1's own smokes imported the package with module-level Qt imports under `-cq` (`phase5_smoke.py:16-18`) |

---

## open_questions

1. **Q1 (UNVERIFIED — blocks verify-tier design): does widget construction work headless?**
   - What we know: Qt *import* headless is proven (T1a, v1 evidence). `-cq` builds no QApplication; offscreen platform availability in this conda PyQt5 is unrecorded anywhere in the repo.
   - Cheap probe: the T1b offscreen script (§verification_tiers). ~20 lines, one `run_smoke.sh` run, settles it.
   - Recommendation: make this Task 1 of plan 04-01; its verdict rewrites the verify columns of every later Phase-4 task.

2. **Q2 (planner decision): what seed does Start pass?** `start_game(setup, seed=42, candidates=None)` — seed is not a setup field. Options: always 42 (deterministic; matches SMOKE-08 asserts), or re-roll per Start. Defaults-compatible choice: keep 42 unless Randomize is meant to shuffle gameplay too (currently `randomize_state` shuffles config, not the generator seed). ROADMAP is silent; pick one and record.

3. **Q3 (planner decision): exported-game file shape (SETUP-08).** "Shareable, versioned game file" — KINDS already carries `'level_spec'` and `'game'` (`persistence.py:37`). Whether export = single versioned JSON (payload only) or v1-style zip of `.pse` + JSON is a Phase-4 plan decision constrained by Phase 7's import round-trip (ROADMAP:116 — "Import-side round-trip completes in Phase 7"). The container API supports either.

4. **Q4 (subsumed by Q1): does `dialog.show()` under the default windows platform headless create an invisible window or error?** Only matters if `offscreen` is unavailable; the probe tests both orders.

5. **Q5 (planner decision): upload validation depth (SETUP-03).** DEFAULTS freezes `upload = {"path","sha256"}` (`setup_state.py:57-58`). Open: extension check only (SDF/MOL2), or a load-probe at upload time (costly cmd call in a UI handler), or defer all validation to `engine.new_game` fail-closed (simplest, house-faithful). Recommend defer-to-engine + extension pre-check in the dialog.

6. **Q6 (planner confirms): module name.** `setup_window.py` proposed (avoids colliding with v1's `gui_setup.py` mental model; matches the "Qt tier" naming in repo docs). Alternative `gui_setup.py` matches the ARCHITECTURE.md research layout (`.planning/research/ARCHITECTURE.md:96`). Either is gate-compatible; pick one and keep `SCANNED_MODULES`/docs consistent.

---

## Sources

### Primary (HIGH — read directly, 2026-09-13)
- `tmp/bioCHEMeleon/biochemeleon/__init__.py` (`:3-5` singleton, `:129-138` entry, `:141-153` open trio, `:156-190` dialog class + module-level Qt imports, `:200-220` button wiring, `:242-261` start, `:545-677` async drain, `:679-720` export, `:915-946` cleanup, `:949-972` modal help child)
- `tmp/bioCHEMeleon/biochemeleon/gui_setup.py` (`:17` import form, `:67-77` form class + `_loading`, `:260-300` 7-button row, `:303-325` signal wiring, `:539-617` collect/apply, `:620-686` randomize/save/load)
- `tmp/bioCHEMeleon/biochemeleon/gui_game.py` (`:108-111` 1 Hz QTimer main-thread pattern)
- `tmp/bioCHEMeleon/smoke/phase5_smoke.py` (`:1-2` headless `-cq` header, `:16-18` package import executing v1's module-level Qt import)
- `pymol-src/modules/pymol/Qt/__init__.py` (`:24-64` binding order, `:84-94` shim)
- `pymol-src/modules/pymol/plugins/__init__.py` (`:29,33` HAVE_QT/QtNotAvailableError, `:100-108` addmenuitemqt)
- This repo: `aamatch/__init__.py:16-39`, `aamatch/gamestart.py:8-13,221-254`, `aamatch/placement.py:404-417`, `aamatch/engine.py:183`, `aamatch/setup_state.py:40-63,90,147`, `aamatch/persistence.py:34-37,44,131,145-165`, `aamatch/wizard.py:22-39`, `tests/test_purity.py:87-101,214-230,255-276`, `tests/test_wizard_source.py:48-51`, `tests/test_package_skeleton.py:110-154`, `tests/test_code_audit.py:64-67,351-371`, `smoke/run_smoke.sh`
- `.planning/ROADMAP.md:107-120` (Phase-4 criteria), `.planning/STATE.md:129-135,175`, `.planning/phases/03-wizard-gameplay-loop/03-05-SUMMARY.md`, `03-06-SUMMARY.md`, `.planning/research/{PITFALLS,STACK,ARCHITECTURE}.md`

### Derived evidence (HIGH — v1 execution records)
- Headless `pymol.Qt` import: v1 smoke battery ran the package-import path repeatedly under `-cq` (phase5_smoke header + v1 AGENTS.md recipe); repo-wide grep confirms no offscreen/closeEvent prior art.

### UNVERIFIED (flagged — probes proposed)
- Widget construction / QApplication headless (`offscreen` platform availability) — Q1.
- Exact failure mode of a mid-game dangling GameWizard after Cleanup — P6 cheap probe.

## Metadata

**Confidence breakdown:**
- Borrowed patterns & seams: HIGH — every line read from shipped v1 / PyMOL 2.5.0 tree / this repo today.
- Architecture recommendation: HIGH — pure recombination of verified patterns under existing repo gates.
- Verification tiers: HIGH for T0/T1a/T2 boundaries; T1b LOW→probe.
- Pitfalls: HIGH for P1-P5, P7-P12 (code-verified); P6 MEDIUM (hazard code-verified, failure mode inferred).

**Research date:** 2026-09-13
**Valid until:** stable (PyMOL 2.5.0 pinned; v1 frozen; repo laws frozen) — re-verify only if the conda env changes.
