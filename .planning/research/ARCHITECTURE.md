# Architecture Research

**Domain:** PyMOL 2.5.0 plugin game (educational interaction-matching; Qt GUI + wizard-driven viewer interaction)
**Researched:** 2026-09-05
**Confidence:** HIGH (every PyMOL API claim below is cited `file:line` from the local PyMOL 2.5.0 open-source source tree at `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/bioCHEMeleon/tmp/pymol-src/modules/pymol/`, or is drawn from the shipped v1 plugin `bioCHEMeleon` which uses the *same* architecture pattern; the few unverified spots are explicitly marked)

---

## Standard Architecture

### System Overview

Proven pattern (v1 `bioCHEMeleon` shipped with exactly this shape): **strict one-directional dependency layering** with a pure, WSL-unit-testable core, cmd-coupled bridges, a thin wizard input adapter, and a Qt GUI that only ever talks downward to the controller.

```
┌──────────────────────────────────────────────────────────────────────┐
│  LAYER 4 — Qt GUI (pymol.Qt / PyQt5; Windows-display only)           │
│  ┌────────────────┐        ┌────────────────────┐                    │
│  │ SetupWindow    │        │ GameStatusTab      │  modeless dialog   │
│  │ (params+7 btns)│        │ (log,timer,score…) │  dialog.show()     │
│  └───────┬────────┘        └─────────┬──────────┘  NEVER .exec_()   │
│          │  calls controller methods │  receives Qt signals/callbacks│
├──────────┴───────────────────────────┴──────────────────────────────┤
│  LAYER 3 — Viewer interaction adapter (pymol.wizard.Wizard subclass) │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ GameWizard: do_pick/do_select → controller.on_pick(aid)  │       │
│  │  do_key/do_special → nudge/rotate events                 │       │
│  │  get_panel() → wizard-panel buttons (Confirm/Reset/Done) │       │
│  └───────┬──────────────────────────────────────────────────┘       │
│          │ duck-typed controller reference (thin adapter)           │
├──────────┴──────────────────────────────────────────────────────────┤
│  LAYER 2 — cmd bridge / orchestrator (imports pymol.cmd)             │
│  ┌──────────────┐ ┌──────────────┐ ┌───────────────┐ ┌────────────┐ │
│  │ placement.py │ │ geometry.py  │ │ session.py    │ │ controller │ │
│  │ (objects:    │ │ (coords →    │ │ (pse+sidecar  │ │ (game.py:  │ │
│  │  fragment/   │ │  numpy arrays│ │  save/load/   │ │ composition│ │
│  │  create/     │ │  out, data   │ │  import/      │ │ root, wires│ │
│  │  translate/  │ │  in)         │ │  cleanup)     │ │ everything)│ │
│  │  rotate/drag)│ │              │ │               │ │            │ │
│  └──────┬───────┘ └──────┬───────┘ └──────┬────────┘ └─────┬──────┘ │
├─────────┴────────────────┴────────────────┴────────────────┴────────┤
│  LAYER 1 — PURE game logic (stdlib + numpy ONLY; no pymol, no Qt)   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────────────┐   │
│  │ level_spec │ │ generator  │ │ detector   │ │ game_state +    │   │
│  │ (dataclasses│ │ (seeded,   │ │ (pure      │ │ scoring.py      │ │
│  │  + serialize)│ │ always-    │ │ geometry   │ │ (score, win,    │   │
│  │            │ │  solvable) │ │  criteria) │ │  level progress)│   │
│  └────────────┘ └────────────┘ └────────────┘ └─────────────────┘   │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ data/: bundled AA + ligand structure files (+ MANIFEST)       │  │
│  └───────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  LAYER 0 — PyMOL host (cmd API, wizard stack, .pse session, Qt loop)│
└─────────────────────────────────────────────────────────────────────┘
```

Dependency direction is **strictly downward** (identical to the v1 rule, `bioCHEMeleon/AGENTS.md:48-64`): Layer 1 imports stdlib/numpy only; Layer 2 imports Layer 1 + `pymol.cmd`; Layer 3 imports Layer 2's controller via constructor injection; Layer 4 imports Layer 2 (and instantiates Layer 3). **Never reverse.** The composition root (`__init__.py`) is the only module allowed to wire across all layers.

### Component Responsibilities

| Component | Responsibility | Typical Implementation (proven v1 pattern) |
|-----------|----------------|---------------------------------------------|
| `level_spec.py` (pure) | Immutable description of one molecule/level: ligand data ref, AA grid contents, required interactions, difficulty. Serialize/deserialize. | Dataclasses + `to_dict`/`from_dict` (v1: `registry.py` record pattern) |
| `generator.py` (pure) | Seeded, always-solvable level generation: pick ligand + protonation, choose required interactions, choose AA set that guarantees solvability + distractors, lay out NxN grid poses. Data in → spec out. | v1 `generators.py` docstring: "The cmd-coupled caller feeds data (bounding box, neighbor pool) IN and gets pure geometry/selection decisions OUT" — no pymol import |
| `detector.py` (pure) | Given ligand coords/types + placed AA coords/types (numpy arrays), classify each required interaction (H-bond, salt bridge, π-stacking, cation-π, hydrophobic, halogen, metal) as formed/not. Returns interaction results for scoring. | Pure functions on coordinate arrays; thresholds as module constants (per PROJECT.md: thresholds verified against published sources, human-approved) |
| `game_state.py` + `scoring.py` (pure) | Current molecule/level index, per-AA placement transforms, scores, skip counts, timer anchor. Score = fraction of required interactions formed (binary per interaction). | Pure state container + reducers; mirrors v1 `registry.HiderRegistry` CRUD/status pattern |
| `persistence.py` (pure) | Build/parse/apply the game-state sidecar dict (magic header + schema version). Archive I/O (zip of `.pse` + JSON). | v1 `persistence.py:1-40`: BCM_MAGIC + BCM_VERSION refuse-foreign-file pattern; "All functions in this module are PURE; the cmd-coupled steps live in the GUI handler + game.py" |
| `placement.py` (cmd bridge) | Materialize a spec into PyMOL objects: load AA/ligand structures, `cmd.create` AA copies, `cmd.translate`/`cmd.rotate(object=…, origin=…)` to grid poses; cleanup `cmd.delete`. | `creating.py:960-997` (create), `editing.py:1610` (translate), `editing.py:1716-1760` (rotate with `object=`/`origin=`) |
| `geometry.py` (cmd bridge) | Extract per-atom numpy arrays (coords via `cmd.iterate_state`, ids/types via `cmd.iterate`) from named objects; feed detector; report formed interactions back to view layer (coloring on finish only). | `editing.py:1578-1608` (iterate_state exposes `x/y/z`), `querying.py:1269` (identify), `editing.py:1445-1450` (iterate symbol table: uppercase `ID`) |
| `session.py` (cmd bridge) | Checkpoint save/restore, generate-and-export, import, cleanup-generated-objects. Uses `cmd.save`/`cmd.load` + pure persistence module. | `exporting.py:782-824` (save supports `.pse`), v1 `.bcmz` zip pattern |
| `controller.py` (orchestrator) | Composition root of gameplay: owns pure game state; calls placement/geometry/session; exposes methods the GUI and wizard call (`on_pick`, `confirm`, `reset_to_grid`, `hint`, `skip`, …); emits GUI callbacks. | v1 `game.py:15-46`: `GameController` with `set_callbacks(on_log=…, on_win=…)` — every callback defaults to a no-op lambda |
| `wizard.py` (viewer adapter) | Intercept clicks (select AA) and optional keyboard nudges; route to `controller.on_pick(aid)`; expose Confirm/Reset/Done in the wizard panel. Keep mouse-rotate working. | v1 `wizard.py:34-96` `PickWizard` (verified against `wizard/mutagenesis.py`, `wizard/measurement.py`, `wizard/dragging.py`) |
| `gui_setup.py`, `gui_game.py` (Qt) | Setup window (params + 7 buttons), Game status tab (log/timer/required interactions/Hint/Confirm/Skip/Save/Restart/Reset). Qt only reads controller state + connects callbacks; QTimer for the timer. | v1 `gui_game.py:108-113`: "1 Hz QTimer (main thread; … NEVER threading.Thread)" |
| `__init__.py` (composition root) | `__init_plugin__(app=None)` entry, menu registration, module-level dialog singleton, wiring. | `plugins/__init__.py:320-321` calls `mod.__init_plugin__(pmgapp)`; v1 `__init__.py:5,129-138` |

## Recommended Project Structure

```
AA-match/
├── aamatch/                    # plugin package (installable via Plugin Manager)
│   ├── __init__.py             # __init_plugin__ + dialog singleton + wiring (composition root)
│   ├── setup_state.py          # PURE: setup params model, defaults, validate/randomize, SETUP_FORMAT
│   ├── level_spec.py           # PURE: level/molecule spec dataclasses + serialization
│   ├── generator.py            # PURE: seeded solvable level generation (grid layout, AA selection)
│   ├── interactions.py         # PURE: interaction definitions & thresholds (constants, citable)
│   ├── detector.py             # PURE: geometric detection on numpy arrays
│   ├── game_state.py           # PURE: gameplay state container + transitions
│   ├── scoring.py              # PURE: score computation, level totals, endgame summary
│   ├── persistence.py          # PURE: sidecar dict build/parse/apply + zip archive I/O
│   ├── controller.py           # cmd bridge: gameplay orchestrator (composition root of a round)
│   ├── placement.py            # cmd bridge: spec → PyMOL objects; reset-to-grid
│   ├── geometry.py             # cmd bridge: PyMOL objects → numpy arrays
│   ├── session.py              # cmd bridge: save/export/import/cleanup
│   ├── wizard.py               # Wizard subclass: pick routing + panel (thin)
│   ├── gui_setup.py            # Qt: setup window (params + 7 buttons)
│   ├── gui_game.py             # Qt: game-status tab
│   ├── gui_dialog.py           # Qt: main modeless tabbed dialog (or in __init__.py, as v1)
│   └── data/                   # bundled AA + ligand structure files + MANIFEST/SOURCES.md
├── tests/                      # WSL-runnable: python3.6 -m unittest discover tests -v
│   ├── __init__.py
│   ├── test_setup_state.py
│   ├── test_generator.py
│   ├── test_detector.py
│   ├── test_game_state.py
│   ├── test_scoring.py
│   ├── test_persistence.py
│   └── stubs.py                # shared sys.modules stub for pymol/pymol.Qt
├── smoke/                      # headless cmd-only scripts (Windows PyMOL via cmd.exe)
└── wsl2win_cp.sh               # stage package to a Windows-visible path (v1 recipe)
```

### Structure Rationale

- **aamatch/ flat module layout:** v1 shipped a flat package and it worked; PyMOL's plugin loader imports the package by name (`plugins/__init__.py:277` `__import__(self.mod_name, level=0)`), and a flat layout keeps `from . import x` imports simple and grep-gate friendly.
- **tests/ mirrors the pure layer:** every PURE module gets a unittest file runnable under WSL `python3.6`. The stub pattern is mandatory (v1 `tests/test_setup_state.py:13-15`):

  ```python
  if 'pymol' not in sys.modules:
      sys.modules['pymol'] = MagicMock()
      sys.modules['pymol.Qt'] = MagicMock()
  ```

- **smoke/ separate from tests:** cmd-coupled code cannot be unit-tested in WSL; it is verified by headless Windows PyMOL runs (`cmd.exe /c C:\src\run-conda-pymol.bat -cq smoke\…`, v1 AGENTS.md recipe). Keep those scripts in their own folder so the WSL test-suite gate stays clean.
- **data/ inside the package:** bundled structures must be reachable at runtime from the installed plugin location — `os.path.dirname(__file__)` relative paths (same as v1 `biochemeleon/data/demos/`).

## Architectural Patterns

### Pattern 1: Purity layering with dependency injection (the testability backbone)

**What:** The entire game brain — setup params, level generation, interaction detection, scoring, persistence dict assembly — lives in modules that import **stdlib + numpy only**. A thin cmd bridge converts PyMOL world → plain data, calls pure functions, and converts results back.

**When to use:** Always in this project. It is the *only* way to satisfy the hard constraint "pure-layer unit tests in WSL python3.6 while PyMOL itself runs on Windows."

**Evidence (v1, shipped):** v1 `persistence.py:5-19` — "All functions in this module are PURE (stdlib only…); the cmd-coupled steps (cmd.save …, cmd.load …) live in the GUI handler + game.py… Dependency direction (strict, no cycle): setup_state.py (PURE) <- registry.py (PURE) <- persistence.py (THIS) <- game.py (orchestrator) <- __init__.py (composition root)."

**Key trick — inject the impure callable, don't import it:** v1 `registry.py:14-17` — "`reconstruct_from_sentinels` uses dependency injection — the iterate fn is passed as a parameter so `registry.py` stays pure (no `from pymol import cmd`); `game.py` injects `lambda: mutation.fetch_all_hider_ids(obj)`."

**Trade-offs:** Slightly more argument plumbing (coords dicts, data refs). Worth it: the detector/generator/scorer become fully deterministic and testable, and the same pure code runs headlessly.

### Pattern 2: Wizard as a thin input adapter (picking through the wizard stack)

**What:** A `pymol.wizard.Wizard` subclass is the *only* sanctioned way to receive 3D-viewer click events while keeping normal camera control. The wizard intercepts picks, translates them into stable atom identities, and hands them to the controller. It owns **no game logic**.

**Verified mechanics (PyMOL 2.5.0 source):**

- Base class and event hooks: `wizard/__init__.py:4-15` defines `event_mask_pick/select/key/special/scene/state/frame/dirty/view/position`; `:76-88` defines the `do_pick(bondFlag)`, `do_select(name)`, `do_key(k,x,y,mod)`, `do_special(...)`, `cleanup()` overridables; `:49-56` `get_prompt()`/`get_panel()`/`get_event_mask()` (default mask = pick + select).
- Install/replace: `wizarding.py:110-118` `cmd.set_wizard(wizard, replace)` puts an arbitrary Wizard **instance** on the C wizard stack; `wizarding.py:156-164` `cmd.get_wizard()`. Custom wizards do **not** need to live in `pymol/wizard/` — that package lookup (`wizarding.py:30-60`, `full_name = 'pymol.wizard.'+name`) is only for the string-based `cmd.wizard("name")` launcher; plugins pass instances directly (v1 `wizard.py:88`).
- **Click routing — the canonical two-path problem** (v1 `wizard.py:7-28` documents it with C-layer references): in Picking button modes the C layer creates `pk1` and calls `do_pick`; in the default 3-Button Viewing **selection** mode the C layer creates the `sele` selection and calls `do_select` — `do_pick` never fires. The canonical fix (from `wizard/measurement.py:295-305`) is to re-route in `do_select`: `cmd.unpick()` → `cmd.select("pk1", name + …)` → `cmd.delete(name)` → `self.do_pick(0)`. This keeps **left-drag = camera rotate** working (essential for AA-match, where players must spin the scene to aim placements).
- Reading *what* was picked: iterate `pk1` with a hygienic space dict — v1 `wizard.py:56-62`:

  ```python
  props = []
  cmd.iterate("pk1", "stored.append((model, ID, alt, resv))", space={'stored': props})
  cmd.unpick()
  ```

  `ID` must be **uppercase** (iterate symbol table, `editing.py:1445-1450`; lowercase `id` collides with the Python builtin). `space={'stored': props}` must never be `None` (pollutes `pymol.__dict__`; v1 AGENTS.md Phase-3 rules).
- Mode save/restore: the Mutagenesis wizard saves and overrides `mouse_selection_mode` (`wizard/mutagenesis.py:90-91`); restore in `cleanup()` (v1 `wizard.py:90-92` does exactly this).
- Panel buttons are command strings evaluated later, e.g. `[2, 'Confirm', 'cmd.get_wizard().confirm()']` — format `wizard/dragging.py:82-105`; nested lists make dropdown menus (`wizard/mutagenesis.py:93-135`). Call `cmd.refresh_wizard()` after any state change that should re-render the panel (`wizarding.py:130-144`; used throughout `wizard/dragging.py`).
- Keyboard events: `do_key` returns `1` to consume the key (`wizard/command.py:166-178`). Available if discrete nudge/rotate UX is chosen.

**Trade-offs:** One active wizard at a time — a game wizard must save/restore any prior wizard (v1 `wizard.py:86-91`), and must not fight the built-in ones. Panel real estate is modest (a text + button list); the Qt tab carries the rich UI.

### Pattern 3: Drag/rotate of AA objects — object-matrix commands, wizard-stays-on-top

**What:** Moving a selected AA "onto" the ligand has two viable mechanisms; both keep the game wizard installed:

- **(a) Object-matrix commands (recommended default):** `cmd.translate(vector, selection, …)` (`editing.py:1610`) and `cmd.rotate(axis, angle, selection, state=-1, camera=1, object=None, origin=None, …)` (`editing.py:1716-1760`). With `object=` given, rotate "modifies the matrix associated with a particular object" (docstring, `editing.py:1722-1724`), and `origin=` sets the rotation center (`:1747-1749`) — i.e. `cmd.rotate('y', 15, object=aa_name, origin=centroid, camera=0)` turns an AA about its own centroid without touching coordinates of anything else. Panel buttons / keys drive incremental moves; the wizard's `get_panel()` exposes Rotate-X/Y/Z, Nudge-toward-ligand, Confirm.
- **(b) Built-in drag machinery:** `cmd.drag(selection, wizard=1, edit=1, …)` (`editing.py:1018-1076`) enables mouse-gesture coordinate manipulation, "the selection … must all reside in a single molecular object" (`:1037-1039`). **Hazards, verified:** default `wizard=1` installs the built-in `Dragging` wizard, *replacing the current one* (`:1067-1074` — `if wiz is None: _self.wizard("dragging", old_button_mode)`); the Dragging wizard self-disables unless `cmd.get_editor_scheme()==3` (`wizard/dragging.py:49-56`) and restores `button_mode` only in its own `cleanup()` (`dragging.py:72-80`). Using `cmd.drag(sele, wizard=0, edit=0)` avoids the wizard replacement, but drag-under-custom-wizard behavior is **UNVERIFIED** → requires a phase spike if this route is chosen.

**Recommendation:** Build gameplay v1 on (a) — fully verified, deterministic, wizard-compatible, and it composes with "Reset to grid" (replay grid poses from the pure level spec — no reverse-transformation math needed). Treat (b) as an enhancement spike. Either way the *controller API is identical* (`apply_move(aa_id, transform)`), so the UX choice is swappable.

**Reading back placements:** `cmd.get_object_matrix(object, state=1, incl_ttt=1)` returns the object's 4×4 transform (`querying.py:89-100`); `cmd.get_coordset(name, state)` returns the coordinate array (`querying.py:914`); per-atom coords for detection come from `cmd.iterate_state` (`editing.py:1578-1608`, example at `:1592-1593` sums `x`).

### Pattern 4: Callback-decoupled controller + modeless Qt (GUI never blocks the viewer)

**What:** The controller exposes explicit callback registration with no-op defaults; the Qt layer connects to them. The main dialog is **modeless** so the 3D viewer stays interactive during gameplay.

**Evidence:** v1 `game.py:94-111` — `set_callbacks(on_log=None, on_remaining_changed=None, on_win=None, on_counts_changed=None)`, "Each defaults to a no-op lambda when None". v1 `__init__.py:5` module-level `dialog = None` singleton (GC prevention), `__init__.py:158-166` `dialog.show()` modeless, "NEVER use the modal form (blocks the PyMOL event loop and the viewer)". Qt imports exclusively via `from pymol.Qt import QtWidgets` (`Qt/__init__.py:26-40` auto-selects PyQt5 → PySide2; a bare `from PyQt5 import` bypasses this and is banned by the v1 grep gate).

**Timer discipline:** the only legal timer is `QtCore.QTimer` on the Qt main thread (v1 `gui_game.py:108-113`, "NEVER threading.Thread" — PyMOL cmd calls from foreign threads deadlock). Anything timer-like in game logic stores `time.time()` anchors in the pure state and lets the QTimer *render* them.

### Pattern 5: Sidecar persistence — session file + JSON game state (checkpoint/export/import)

**What:** A checkpoint is **two artifacts, one archive**: the PyMOL session (objects, views, wizard stack) plus a JSON game-state sidecar (pure state), zipped together.

**Verified mechanics:**

- `cmd.save(filename, selection='(all)', state=-1, format='', …)` writes `.pse` sessions; format auto-guessed from extension, zipped-output supported (`exporting.py:782-824`, zipped detection at `:834`).
- The wizard stack round-trips inside the session automatically: `wizarding.py:176-180` `session_save_wizard` pickles `get_wizard_stack()` into `session['wizard']`; `wizarding.py:182-196` `session_restore_wizard` unpickles, **rebinds `wiz.cmd`**, calls `wiz.migrate_session(version)`, and re-installs the stack. Consequences: (i) the wizard object is *pickled* — hold **no Qt widgets, no locks, no open files** on it; keep it to plain data + a controller reference that is rebuilt on load (see `migrate_session`, `wizard/__init__.py:17-20`); (ii) the plugin module must be importable at session-load time for restore to succeed (else PyMOL prints "unable to restore wizard" and continues, `wizarding.py:193-195`).
- Sidecar discipline (v1 `persistence.py:31-40`): magic header (`BCM_MAGIC`) + schema version (`BCM_VERSION`), refuse newer versions with a clear error; `build_bcm_dict`/`parse_bcm_dict`/`apply_bcm_dict` are pure; **cmd-coupled steps (cmd.save of the .pse, cmd.load, re-coloring) live in the orchestrator/GUI handler, NOT in the pure module**. v1 shipped `.bcmz` = zip of `.pse` + `.bcm` JSON — AA-match's "Generate and export" and "Save (PyMOL session + game state)" map 1:1 onto this (`kind='checkpoint'` vs `kind='puzzle'`, v1 `persistence.py:60-63`).
- Capture timing pitfall (v1 `persistence.py:64-67`): capture elapsed time **before** opening a modal file dialog.

### Pattern 6: Object identity & sentinel conventions (survives cleanup, save/reload)

**What:** Every game-placed object/atom carries a sentinel; identity keys are stable ids, never indices.

**Evidence (v1, battle-tested):**

- Objects the game creates get a reserved namespace (`_aam_*` naming, analogous to v1's `_bchm_backup`) so `Cleanup` = `cmd.delete` over the reserved prefix + wizard teardown — deterministic and never touches user objects.
- Atom-level sentinels: `segi='GAME'` + `b=-999`; the *selector* is `segi GAME` or `b < 0` (PyMOL has no exact-match b-factor selector — `b -999` is a malformed selector; v1 AGENTS.md Phase-3 rules). Identity keyed on atom `id` via `cmd.identify(sel, mode=0)` (`querying.py:1269`; `querying.py:1313-1317` warns to "use integral atom identifiers instead of indices"), never `index` (shifts on insert/remove).
- **PyMOL Open Source has no undo** (v1 AGENTS.md; the built-in Dragging wizard offers `cmd.undo()` in its panel, `wizard/dragging.py:88-89`, but the no-op stub reality in open source is documented in v1 `editor.py:25-36` note). Any destructive step needs an explicit snapshot first (`cmd.create('_backup', …)`, `creating.py:960-997`) or, better in AA-match, **regeneration from the pure spec** — the seeded level spec is the source of truth, so "Reset to grid" and crash recovery both replay the spec instead of undoing history.

## Data Flow

### Main flow: setup → generate → gameplay → detection → score → endgame

```
SetupWindow (Qt)                    controller                     pure layer
────────────────                    ──────────                     ──────────
params + button click ──collect_state()──▶ controller.setup(spec dict)
                                              │ validate/randomize   ▶ setup_state (pure)
Start ──────────────────────────────────────▶ controller.start()
                                              │ generator.feed(ligand data, AA pool, seed)
                                              │                      ▶ generator → LevelSpec (pure)
                                              │ placement.materialize(spec)
                                              ▼
                                     PyMOL: fragment/load + create + translate/rotate(object=)
                                              │ geometry.snapshot_grid_poses()
3-2-1 countdown (QTimer) ──▶ GameWizard.activate()  (wizard stack + panel)
────────────────────────────
player Left-click AA ──▶ do_select ──▶ re-route pk1 ──▶ do_pick
                              │ iterate pk1 → (model, ID, …) ──▶ controller.on_pick(aid)
                              │                                    game_state.select_aa(aid)
panel/key: rotate/nudge ──▶ cmd.rotate(object=…, origin=…) / cmd.translate
                              │ controller.apply_move(aid, transform) → game_state
Confirm (panel or tab) ──▶ controller.confirm()
                              │ geometry.extract(ligand + placed AAs)   (iterate_state → numpy)
                              │ detector.detect(coords, types, spec.required)
                              │                      ▶ interaction results (pure)
                              │ scoring.update(state, results)         ▶ score (pure)
                              ├── callbacks: on_score, on_molecule_done …
                              ▼
                     next molecule / next level / win screen (Qt tab switches)
```

### Checkpoint / export / import flow

```
Save (Game tab) ──▶ t0 = time.time() captured BEFORE QFileDialog
                    controller.checkpoint(path):
                      persistence.build_checkpoint_dict(state, spec, elapsed)   (pure)
                      cmd.save(tmp .pse)  →  zip{game.pse, state.json}          (session.py)
Import ──▶ unzip → cmd.load(.pse) → persistence.parse/apply → rebuild wizard+UI
Cleanup ──▶ cmd.delete('_aam_*') + wizard deactivate + Qt tab reset      (session.py)
```

### Key data flows

1. **Spec is the single source of truth.** Generation is seeded and pure; placement materializes it. Reset-to-grid, crash recovery, and exported games all *replay the spec* rather than reverse PyMOL mutations.
2. **Geometry flows outward only at two points:** grid-pose snapshot (after materialize) and detection (on Confirm). During play, only transforms (which AA, which move) flow — detection is never run per-frame.
3. **UI updates are callbacks, never polling of PyMOL:** the wizard pushes picks; the controller pushes score/log events; the QTimer only re-renders the timer label from a stored anchor.

## Scaling Considerations

*(Adapted from the template's scaling table — here "scale" = level size / grid N, the axis that actually stresses this design.)*

| Scale | Architecture Adjustments |
|-------|--------------------------|
| N=2–3 grid (4–9 AAs), ≤7 interaction types | Straightforward: one PyMOL object per AA (object-matrix rotation is per-object and cheap); detector is O(AAs × ligand atoms) per Confirm — trivially fast |
| N=4–5 (16–25 AAs), metal/halogen types added | Still one-object-per-AA; keep detector numpy-vectorized (distance matrix, not per-pair Python loops); precompute ligand ring centroids/normals once per molecule |
| Many levels / long sessions | Checkpoint zip already bounds state; keep `game_state.to_dict()` O(placements), not O(history) — store current pose per AA, not move history |

### Scaling Priorities

1. **First bottleneck:** detection cost if run naively per-move. Fix: detect only on Confirm (per PROJECT.md flow), vectorize pair screening with numpy (pure layer owns this; geometry bridge just supplies arrays).
2. **Second bottleneck:** PyMOL object count clutter with 25 AAs + ligand + backups. Fix: reserved-prefix naming + group objects (`cmd.group`) in the placement bridge; Cleanup deletes by prefix only.

## Anti-Patterns

### Anti-Pattern 1: Game logic inside the wizard or Qt slots

**What people do:** Put solvability checks, scoring, or level data inside `do_pick` or a button handler.
**Why it's wrong:** Both are untestable in WSL (need live PyMOL/Qt), and the wizard gets *pickled into the session* (`wizarding.py:176-180`) — logic there bloats and can break session restore.
**Do this instead:** Wizard = adapter only (v1 `wizard.py` is 96 lines); all logic in the pure layer behind `controller`.

### Anti-Pattern 2: Modal dialogs during gameplay

**What people do:** `dialog.exec_()` on the main plugin window.
**Why it's wrong:** Blocks the PyMOL event loop — the 3D viewer freezes, no picking possible (v1 AGENTS.md exec_ gate).
**Do this instead:** `dialog.show()` modeless; reserve `exec_()` for child QFileDialog/QMessageBox only (v1 gate allows exactly those).

### Anti-Pattern 3: Identifying atoms/objects by index or by name-derived position

**What people do:** Store `index` from iterate, or parse object names for meaning.
**Why it's wrong:** `index` shifts on every insert/delete (`querying.py:1313-1317` warns against indices); game objects get deleted/recreated by reset.
**Do this instead:** Key on stable atom `id` (`cmd.identify(mode=0)`) and on reserved-prefix object names recorded in the pure state.

### Anti-Pattern 4: Qt state or callbacks on the pickled wizard / threading

**What people do:** Hold widget refs in the wizard; spawn `threading.Thread` for timers or detection.
**Why it's wrong:** Wizard is pickled into `.pse` (widgets aren't picklable; restore breaks); PyMOL cmd from foreign threads deadlocks (v1 Pitfall 6).
**Do this instead:** Wizard holds plain data + a controller reference; all GUI timers are `QtCore.QTimer`; heavy detection stays synchronous-on-confirm (it is fast by design).

### Anti-Pattern 5: Reverse dependencies / UI importing up

**What people do:** Pure module does `from pymol import cmd` "just for one call", or placement module imports the GUI.
**Why it's wrong:** Kills WSL testability and creates import cycles at plugin load.
**Do this instead:** Enforce the v1 rule — pure modules have zero pymol/Qt imports (grep-gate it), bridges import pure only, GUI imports bridges.

### Anti-Pattern 6: Undo/restore-by-mutation

**What people do:** Try to "undo" player moves by tracking deltas, or rely on PyMOL undo.
**Why it's wrong:** Open-source PyMOL has no working undo (v1 AGENTS.md); delta-tracking across object-matrix edits is error-prone.
**Do this instead:** Regenerate from the seeded spec (reset/restore), and snapshot before any destructive batch op if regeneration is too coarse.

## Integration Points

### PyMOL API surface (verified signatures — the cmd bridge's full contract)

| Need | API | Citation |
|------|-----|----------|
| Install/remove input wizard | `cmd.set_wizard(wizard, replace)` / `cmd.get_wizard()` / `cmd.refresh_wizard()` | `wizarding.py:110-118`, `:156-164`, `:130-144` |
| Receive clicks | Override `do_pick(bondFlag)` / `do_select(name)`; event masks | `wizard/__init__.py:6-15, 76-88`; re-route pattern `wizard/measurement.py:295-305` |
| Read picked atom | `cmd.iterate("pk1", "stored.append((model, ID, …))", space={'stored': …})` + `cmd.unpick()` | `editing.py:1445-1450` (symbol table; `ID` uppercase); v1 `wizard.py:56-62` |
| Keyboard nudges (optional) | `do_key/do_special`, return 1 to consume | `wizard/__init__.py:82-86`; `wizard/command.py:166-178` |
| Panel buttons/menus | `get_panel()` → `[[2, 'Label', 'cmd.get_wizard().x()'], …]`; `self.menu[tag]` | `wizard/dragging.py:82-105`; `wizard/mutagenesis.py:93-135` |
| Mouse selection granularity | `cmd.get_setting_int`/`cmd.set("mouse_selection_mode", n)` (0=atom, 1=residue) | `wizard/mutagenesis.py:90-91`; v1 `wizard.py:43-45` |
| Load AA / ligand structures | `cmd.fragment(name)` (fragment library = amino acids) / `cmd.load` of bundled data files | `creating.py:929-935`; `completing.py:30-35` (fragments from `chempy.path + 'fragments'`) |
| Place an AA copy | `cmd.create(name, selection, source_state=0, target_state=0, discrete=0, …)` | `creating.py:960-997` |
| Move/turn objects | `cmd.translate(vector, selection, …)`; `cmd.rotate(axis, angle, selection, state, camera, object=None, origin=None, …)` | `editing.py:1610`; `editing.py:1716-1760` |
| Read transforms/coords | `cmd.get_object_matrix(object, state=1, incl_ttt=1)`; `cmd.get_coordset(name, state)`; `cmd.iterate_state(state, selection, expr, space=…)` (exposes x/y/z) | `querying.py:89-100`; `querying.py:914`; `editing.py:1578-1608` |
| Identity/count queries | `cmd.identify(sel, mode=0)`; `cmd.count_atoms(sel)`; `cmd.get_distance(a1, a2, state)`; `around`/`within` selectors | `querying.py:1269`, `:1412`, `:951`; `selecting.py:75` |
| Session save/load | `cmd.save(file, …)` (`.pse`, zipped ok); wizard stack auto-saved/restored | `exporting.py:782-824`; `wizarding.py:176-196` |
| Plugin menu + load contract | `__init_plugin__(app=None)`; `from pymol.plugins import addmenuitemqt; addmenuitemqt(label, cb)`; package import via `__import__(mod_name)`; `QtNotAvailableError` gracefully skips plugin without Qt | `plugins/__init__.py:320-321`, `:100-108`, `:277`, `:287-288` |
| Qt import surface | `from pymol.Qt import QtWidgets, QtCore, QtGui` (auto PyQt5→PySide2) | `Qt/__init__.py:26-40, 63-64` |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Qt ↔ controller | direct method calls (down) + registered callbacks (up) | callbacks default no-op; QTimer renders only |
| Wizard ↔ controller | duck-typed `controller.on_pick(aid)` (v1 `wizard.py:39`) | wizard holds the only cross-cut reference; rebuilt on session restore |
| Controller ↔ pure layer | plain dicts/dataclasses/numpy | the *same* pure API the unit tests exercise |
| cmd bridges ↔ pure layer | bridges serialize PyMOL→data, call pure, apply results | bridges never contain rules/thresholds |
| persistence ↔ session | pure build/parse vs cmd save/load split | v1 `persistence.py:5-12` wording is the contract |

## Session + State Checkpoint Design (explicit, per roadmap need)

**Artifact:** `<name>.aamz` = zip containing `game.pse` + `state.json` (+ `spec.json` when exporting an unstarted game).

- `game.pse`: written by `cmd.save` (`exporting.py:782-824`) — carries all objects, views, and the wizard stack (auto-pickled, `wizarding.py:176-180`).
- `state.json`: produced by pure `persistence.build_state_dict(game_state, level_spec, setup_state, kind)` — magic header + `STATE_VERSION`, refuse-newer-version on load (v1 `persistence.py:31-40` pattern). Contents: molecule/level index, per-AA current pose + grid pose, scores, skip counts, timer anchor, RNG seed.
- **Load:** `cmd.load(.pse)` restores objects and re-instantiates the wizard via `session_restore_wizard` (`wizarding.py:182-196`); the wizard's `migrate_session` (base-class hook, `wizard/__init__.py:17-20`) + a lightweight "controller reattach" step (GUI notices active wizard and re-binds callbacks, or the load handler re-activates the wizard explicitly) reconnects logic. The wizard carries **only ids** — the controller rebuilds all heavy state from `state.json`.
- **Guard rails:** capture timer before file dialogs (v1 `persistence.py:64-67`); never store Qt/lock/file objects on the wizard; if plugin module isn't importable at load, PyMOL degrades gracefully (wizard restore warning, `wizarding.py:193-195`) — acceptable, the sidecar is the recovery path.

## Build Order Implications (dependency-driven phase suggestions)

Dependencies between components dictate this ordering (each stage is verifiable in WSL or headless Windows PyMOL before the next):

1. **Pure foundation** — `setup_state`, `level_spec`, `generator` (seeded solvable levels), `interactions`+`detector`, `game_state`, `scoring`, `persistence` + full WSL unittest suite. No PyMOL needed; validates the entire game brain.
2. **Data + cmd-only placement/detection path** — bundled AA/ligand structures, `placement.py`, `geometry.py`, `session.py` (save/export/import/cleanup); verified by **headless** Windows PyMOL smoke scripts (`-cq`). Ends with: a script that generates a level and detects a scripted interaction — no GUI, no wizard.
3. **Wizard interaction** — pick routing (canonical `do_select`→`do_pick`), panel (Confirm/Reset/Done), object-matrix move application, mouse-mode save/restore. Headless-verifiable for logic; pick/UX needs human verify.
4. **Qt windows** — setup window, game-status tab, dialog singleton, QTimer, callbacks wiring, countdown/win screens. Human-verify checkpoints (GUI needs real display).
5. **Checkpoint/export/import end-to-end + cleanup + polish** — full `.aamz` round-trip across a real session, edge cases (restore with plugin reload), help text, scoring presentation.

Rationale: every phase depends only on earlier ones; the riskiest unknowns (detector criteria, wizard pick UX, drag vs. discrete moves) get isolated spikes in phases 1–3 where failures are cheap, and the phase-3 drag spike (`cmd.drag(wizard=0)` behavior under a custom wizard — the one flagged **UNVERIFIED** item above) can be run headlessly before any GUI work.

## Sources

**Local PyMOL 2.5.0 open-source source tree** (`/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/bioCHEMeleon/tmp/pymol-src/modules/pymol/`) — HIGH confidence, all `file:line` above:
- `wizard/__init__.py`, `wizarding.py`, `wizard/dragging.py`, `wizard/mutagenesis.py`, `wizard/measurement.py`, `wizard/command.py`
- `editing.py`, `creating.py`, `querying.py`, `selecting.py`, `exporting.py`, `completing.py`
- `plugins/__init__.py`, `Qt/__init__.py`

**Prior art, same architecture pattern (v1 shipped plugin)** — HIGH confidence for behavioral claims (smoke-tested in this environment):
- `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/AA-match/tmp/bioCHEMeleon/biochemeleon/` — `wizard.py`, `game.py`, `persistence.py`, `generators.py`, `registry.py`, `__init__.py`, `gui_game.py`
- `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/AA-match/tmp/bioCHEMeleon/AGENTS.md` (headless recipe, domain rules, grep gates)
- `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/AA-match/tmp/bioCHEMeleon/tests/` (stub pattern)

**Third-party plugin examples** — MEDIUM confidence (reference material, not verified in this PyMOL build):
- `Pymol-script-repo/plugins/show_contacts.py:330-332` (modern `__init_plugin__` + `addmenuitemqt`), `apbsplugin.py:330-338` (legacy Tk pattern), `mtsslWizard.py:65` (Wizard subclass in a plugin)

**Marked LOW/UNVERIFIED (needs phase-level spike):**
- `cmd.drag(selection, wizard=0, edit=0)` coexisting with a custom active wizard (built-in wizard replacement verified at `editing.py:1067-1074`, but not the wizard=0 interplay)
- Exact contents of the shipped chempy fragment library (which amino acids / protonation states available as fragments) — `creating.py:929-935` confirms amino-acid fragments exist; inventory must be checked in the phase-2 spike. Bundled curated data files (v1 `data/` pattern) are the safe default regardless.

---
*Architecture research for: AA-match (PyMOL 2.5.0 educational interaction-matching plugin game)*
*Researched: 2026-09-05*
