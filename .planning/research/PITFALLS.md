# Pitfalls Research — AA-match (PyMOL 2.5.0 plugin game)

**Domain:** PyMOL 2.5.0 plugin educational game — NxN amino-acid grids around small molecules; player clicks + drags/rotates AAs in the OpenGL viewer; in-house geometric interaction detection (H-bond, salt bridge, π-stacking, cation-π, hydrophobic, halogen, metal coordination); scoring/timer/checkpoint save; WSL-dev → Windows-PyMOL split environment.

**Researched:** 2026-09-05
**Confidence:** **HIGH** for all PyMOL API-behavior claims (each is either `prior-art-observed` — a bug that actually happened in our previous PyMOL game, verified by its smoke/diag artifacts — or `verified-source` — cited to the local PyMOL 2.5.0 source with file:line). **MEDIUM** for geometric-detection domain edge cases (protonation, metal coordination geometry — the *engineering* risks are concrete; the *threshold values* are deliberately NOT asserted here because PROJECT.md requires every numeric claim to be verified against published sources and human-approved). **LOW / flagged** items are explicitly marked Open Questions.

## How to read this file

Evidence tiers used throughout:

- **[PA-OBS]** = prior-art-observed. This exact bug occurred in our previous PyMOL 2.5.0 game (`tmp/bioCHEMeleon/`, shipped 2026-08-18, 12 phases / 77 plans). Evidence: its AGENTS.md domain rules, `smoke/diag_*.py` scripts, or shipped code comments. Highest practical confidence — it bit a real project on the exact PyMOL build we target.
- **[SRC file:line]** = verified against the local PyMOL 2.5.0 open-source Python modules at `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/bioCHEMeleon/tmp/pymol-src/modules/pymol/`.
- **[PA-V1DOC]** = distilled in the previous project's research (recovered from git: `bioCHEMeleon` commit `123b115` `.planning/research/PITFALLS.md`, v1 PyMOL edition) and/or verified by its runtime smoke tests.
- **[UNVERIFIED]** = plausible but not yet verified; carries an explicit verification task.

Phase names used below are **roadmap-topic names, not numbers** (roadmap not yet created): *bootstrap / setup-GUI / grid-generation / viewer-interaction / detection-engine / scoring-lifecycle / persistence / demos / polish*. The Pitfall-to-Phase Mapping table at the end is designed to be lifted directly into ROADMAP.md.

---

## Critical Pitfalls

### Pitfall 1: Qt code is untestable from the dev shell — any code path that touches `pymol.Qt` is human-verify-only

**What goes wrong:**
The game's Qt dialog (setup window, game-status tab, confirm dialogs) is written and "tested" via syntax checks only, then GUI bugs (layout, signal wiring, focus, timer interplay) are discovered late by a human in a real PyMOL session — or worse, Qt code is imported at module level in a module the headless smoke needs, so *headless testing of cmd-tier code dies too*.

**Why it happens:**
PyMOL runs in a Windows conda env; the WSL dev shell has Python 3.6 with no Qt and no display. `pymol.Qt.*` needs a real display — it cannot run headlessly. `[PA-OBS]` prior art AGENTS.md: "any code path that executes `pymol.Qt.*` at runtime STILL cannot be run from WSL (GUI/Qt needs a real display)". The prior art's `phase11_keyerror_repro.py` exists precisely because `_prepare_and_start` was Qt-coupled and had to be re-mirrored at the cmd tier to be testable — a direct cost of Qt bleeding downward.

**How to avoid:**
- Adopt the prior art's three-tier test discipline from Phase 1 and encode it in `pymol/AGENTS.md`:
  1. **Pure layer** (grid math, interaction detection, scoring, RNG, setup state): stdlib-only, unit-tested in WSL `python3.6 -m unittest`.
  2. **cmd tier** (object creation, transforms, detection plumbing): pure `pymol.cmd.*`, headless-testable from WSL via `cmd.exe /c C:\src\run-conda-pymol.bat -cq <script>` (stage package + script to the Windows-visible path first; wrap in `timeout`; check exit code).
  3. **Qt tier**: `dialog.show()` GUI behaviors are **human-verify checkpoints by design** — write the checkpoint into the phase plan, don't discover it at review.
- Keep `from pymol.Qt import ...` **inside functions** in the entry module only (prior art imported at module level in `__init__.py`, which then forced every WSL test to stub `sys.modules['pymol']` with MagicMock `[PA-OBS]`). Prefer lazy imports so pure/cmd modules import cleanly without stubs.
- Structure the game controller so the Qt layer is a thin shell over a cmd/pure controller (prior art's `game.py` composition-root pattern) — then most game logic is testable tiers 1–2.

**Warning signs:**
- A `diag_*`/smoke script that has to re-implement a GUI method at the cmd tier to test it (prior art literally did this twice).
- Unit tests that begin with `sys.modules['pymol'] = MagicMock()` — a symptom of module-level Qt/pymol imports.
- GUI bugs first seen by a human after "everything passed".

**Phase to address:** *bootstrap* (architecture decision) + every phase (test-tier discipline).

---

### Pitfall 2: WSL→Windows path and cwd resolution — Windows PyMOL cannot see `/mnt/c/...`, and relative paths resolve against the cmd.exe cwd

**What goes wrong:**
`cmd.load('/mnt/c/Users/.../lig.pdb')` fails ("unable to open file") in Windows PyMOL; a script run via `cmd.exe /c` resolves relative paths against the WSL cwd mapped into Windows (`\\wsl$` or `/mnt/c`), so a staged script loads data from the wrong place or nowhere; saved sessions/games embed absolute Windows paths that break when the repo moves.

**Why it happens:**
Windows PyMOL is a Windows process: POSIX mount paths and `~` are meaningless to it. The `cmd.exe /c C:\src\run-conda-pymol.bat -cq script.py` bridge runs with cwd = whatever `cd` the WSL shell did before invoking cmd.exe — PyMOL resolves relative script/data paths against *that*. `[PA-OBS]` prior art AGENTS.md: "Always `cd` into the staged Windows path first (PyMOL resolves relative paths against the cmd.exe cwd ... use the /mnt/c path so Windows PyMOL can read it)."

**How to avoid:**
- A single `to_windows_path()` helper (prior art shipped `demos.to_windows_path()`: `/mnt/c/...` → `C:\...`, other paths returned unchanged) applied before **every** `cmd.load` / `cmd.save` / file open.
- Resolve bundled demo/level data relative to the package's own `__file__`, never `os.getcwd()` — the cwd differs between WSL tests, headless cmd.exe runs, and GUI installs.
- Standardize the headless recipe (stage package + script → `cd` into the staged dir → `timeout N cmd.exe /c ... -cq script` → check exit code) as a repo script, not tribal knowledge.
- Any saved game (`.pse` + sidecar) that stores data paths must store them relative to the package or re-resolve on load; `[PA-V1DOC]` PyMOL sessions store absolute paths (v2's VMD research verified `save_state` stores absolute file paths; PyMOL `.pse` path handling for external references must be verified in the *persistence* phase).

**Warning signs:**
- A load works in one invocation mode (WSL test) and fails in another (headless/GUI).
- `os.path.exists` returns True in WSL but `cmd.load` fails — classic sign the path never got converted.
- A repo move breaks loading saved games.

**Phase to address:** *bootstrap* (helper + first end-to-end headless load) + *demos* (every bundled file loads via the helper).

---

### Pitfall 3: The "pure layer" must be stdlib-only — numpy is NOT in WSL python3.6, and 3.6 language/library limits bite

**What goes wrong:**
Interaction-detection geometry is written with numpy (natural choice; numpy ships with PyMOL on the *Windows* side), then the pure layer can't be unit-tested in WSL (`ModuleNotFoundError: No module named 'numpy'` — verified on this machine, 2026-09-05). Similarly `dataclasses` (3.7+) doesn't exist on 3.6.9, and accidentally importing `pymol` anywhere in the pure layer breaks every WSL test.

**Why it happens:**
The constraint "only what pymol-open-source ships (PyQt5, numpy)" describes the **Windows PyMOL runtime**, not the WSL dev shell. The two Pythons have different stdlib/library universes. `[VERIFIED]` on this machine: `python3.6 -c "import numpy"` → ModuleNotFoundError; `import dataclasses` → ModuleNotFoundError; typing + f-strings OK.

**How to avoid:**
- Rule for the pure layer: **stdlib + math only**. Vector geometry (dot/cross products, angles, plane normals, ring centroids) is entirely doable with `math.sqrt/acos` on 3-tuples/lists for the data sizes involved (one small molecule + ≤ N² amino acids). Keep a tiny pure `vec3.py`-style helper instead of reaching for numpy.
- numpy usage (if any) lives in the cmd tier and is validated by headless Windows smoke runs, not WSL unit tests.
- Pure-layer style guide: no `dataclasses` (use `collections.namedtuple` or plain classes — the prior art's registry used exactly this), no 3.7+ syntax, `python3.6 -m py_compile` gate in CI-like checks.
- The prior art's purity grep gate MUST be part of the checks, with the documented tripwire: literal tokens in comments/docstrings cause false positives (`[PA-OBS]` "we hit a false positive on a docstring that said 'from PyQt5 import'"). Prefer the Grep tool and inspect matches rather than blind-failing.

**Warning signs:**
- A pure module's imports include `numpy`, `pymol`, or `dataclasses`.
- WSL unit tests skipped or xfailed "until numpy available" — that's the pitfall wearing a green hat.
- Tests requiring `sys.modules` stubs of pymol in a module that claims to be pure.

**Phase to address:** *bootstrap* (layer contract) + *detection-engine* (geometry in stdlib) — verify at every phase's test gate.

---

### Pitfall 4: Modal dialogs freeze the viewer, Tkinter is a deprecated trap, and the dialog gets garbage-collected

**What goes wrong:**
The setup/game window is built with `.exec_()` (modal) → the OpenGL viewer stops accepting mouse input → the entire click-and-drag game is dead. Or the GUI is copied from legacy `Pymol-script-repo` plugins using Tkinter/Pmw → deprecated layer, z-order issues (windows appear behind PyMOL), and removal by PyMOL 4. Or the dialog is created as a local variable → Python GCs it → the window flashes and vanishes.

**Why it happens:**
PyMOL 2.x is Qt-based; Tkinter support is deprecated ("full expectation of removal by PyMOL 4.0" — PyMOL wiki, per `[PA-V1DOC]`). `exec_()` runs a nested event loop that blocks PyMOL's. Qt objects with no Python reference are GC'd. `[PA-OBS]` prior art encoded all three as hard rules after inheriting the ecosystem's habits from legacy plugins.

**How to avoid:**
- Entry point `__init_plugin__(app=None)`; menu item via `from pymol.plugins import addmenuitemqt` (imported locally).
- **Module-level** `dialog = None` singleton; reuse on re-open (`if dialog is None: build; dialog.show()`).
- Main game window is **modeless**: `dialog.show()`, never `.exec_()`. `exec_()` allowed ONLY on brief child dialogs (`QFileDialog`, `QMessageBox`) — and any modal child must pause the game timer (see scoring-lifecycle pitfall).
- All Qt imports via `from pymol.Qt import QtWidgets` (auto-selects PyQt5/PySide2), never `from PyQt5 import`.
- Keep the prior art's two grep gates in the phase checks: the Tk/PyQt5-import gate (expect zero matches) and the `.exec_()` gate (expect matches only on QFileDialog/QMessageBox, never the main dialog) `[PA-OBS]`.

**Warning signs:**
- Viewer unclickable while the game window is open.
- A window that appears for a split second then disappears (GC).
- Any `import tkinter` / `from Pmw import` / `grab_set` / `mainloop` in the package.

**Phase to address:** *setup-GUI* (first GUI architectural decision; retrofit is a rewrite).

---

### Pitfall 5: Wizard-based picking — `do_pick` NEVER fires in the default mouse mode; there are two event entry points; only one wizard exists at a time

**What goes wrong:**
The game registers a custom `pymol.wizard.Wizard` and implements `do_pick(bondFlag)` only. On a stock PyMOL (3-Button Viewing preset) left-clicks create the `sele` selection and call `do_select(name)` — `do_pick` is never called. The game appears completely broken for the player while working on the developer's machine (who happens to be in a Picking button mode).

**Why it happens:**
The C layer routes clicks differently per button mode: Picking modes (`PkAt`/`Pk1`) create `pk1` + `WizardDoPick`; the default Viewing mode's left-click (`cButModeSeleSet`) creates `sele` + `WizardDoSelect`. `[PA-OBS]` the prior art's *shipped* `wizard.py` documents exactly this with C-layer references (`SceneMouse.cpp:337-356` vs `403-467`) after hitting it in its click-to-find loop, and implements the canonical `do_select` → build `pk1` → dispatch-through-`do_pick` map (modeled on `pymol/wizard/measurement.py`).

**How to avoid (all verified in shipped prior-art code `tmp/bioCHEMeleon/biochemeleon/wizard.py`):**
- Implement **both** `do_pick` and `do_select` in the game wizard; `do_select` normalizes to the pick path: `cmd.unpick(); cmd.select("pk1", name); cmd.delete(name); self.do_pick(0)`.
- On activation set `mouse_selection_mode` to atomic (0) — otherwise the "sele" contains a whole residue/chain, not the clicked atom — and **save + restore the previous value** on deactivate `[PA-OBS]`.
- Save the prior wizard on activate (`self._saved_wizard = cmd.get_wizard()`) and restore it on deactivate `[PA-OBS]`.
- Read the pick via ONE `cmd.iterate("pk1", "stored.append((model, ID, alt, resv))", space={'stored': props})` and immediately `cmd.unpick()` — never read picks through `index` (officially fragile: querying.py:1313-1317 "Atom indices are fragile and will change as atoms are added or deleted"), never rely on `cmd.identify` alone (returns `(model, id)` with **no alt** — mode documented at querying.py:1282-1283), and never let the same click be processed twice.
- `cmd.refresh_wizard()` after handling a pick so the wizard panel redraws `[PA-OBS]`.

**Why this matters MORE for AA-match than the prior art:** the player must click a *whole amino acid* (an object-or-residue pick), not one atom — the `mouse_selection_mode` choice (atom vs residue) is a real gameplay decision, and the click target (grid AA) vs click target (ligand atom for measurement-style interactions) may want different granularities. Decide explicitly per interaction, not by accident.

**Warning signs:**
- Clicks do nothing on a fresh PyMOL but work on the dev box.
- A click selects 8 atoms (residue) when the code expects 1.
- After closing the game, the user's previous wizard (e.g. measurement) is gone — the save/restore was skipped.

**Phase to address:** *viewer-interaction* (the first gameplay milestone; human-verify checkpoint mandatory here).

---

### Pitfall 6: `cmd.drag` — the built-in drag mechanic clobbers the game's wizard, requires a specific mouse scheme, and has a matrix-vs-coordinates duality

**What goes wrong:**
AA-match's core verb is drag/rotate an AA. The obvious implementation — `cmd.drag(selection)` — (a) **replaces whatever wizard is active**: if the game's pick wizard is running, `cmd.drag` tears it down and installs its own `Dragging` wizard (editing.py:1067-1074: if the current wizard is not a `Dragging` instance, it calls `_self.wizard("dragging", ...)`), so click-to-select dies while dragging; (b) **self-destructs unless the editor scheme is 3** (`wizard/dragging.py:49-54`: `check_valid()` returns 0 and executes `cmd.set_wizard()` — killing the drag — if `get_editor_scheme() != 3`), so on a user's machine with a different mouse scheme dragging silently does nothing; (c) mixes two mutation models: with an empty selection it drags the **whole object via its matrix** ("Dragging matrix for object", dragging.py:33-35,98-101), with atom selections it modifies **coordinates** — and these have different reset (`matrix_reset` modes 0/1/2, editing.py:2143-2146) and different save/round-trip semantics.

**Why it happens:**
`cmd.drag` is designed for interactive editing sessions, not for a game that also owns a wizard. The interplay (one-wizard-at-a-time, editor-scheme gate, matrix-vs-coordinate duality) is invisible until runtime.

**How to avoid:**
- Decide the movement model **deliberately** in *viewer-interaction* design, and document it:
  - **Option A (recommended starting point): game-driven transforms.** Selection via the game wizard (Pitfall 5); movement via explicit `cmd.transform_object`/`cmd.transform_selection` calls driven by Qt controls or by polling the picked atom drag. This keeps ONE wizard (the game's) in charge and makes every move reproducible + restorable.
  - **Option B: native `cmd.drag`** for the "adjust" feel, but then: re-install the game wizard after drag Done (listen for wizard teardown or provide a Done button that re-activates), accept the editor-scheme gate (verify `get_editor_scheme()` at Start and show a setup hint if ≠3), and handle both the matrix path (empty selection) and coordinates path (atom selection) in save/restore/reset.
- Whatever the model, **reset must reset the same mechanism that moved the atom** (spec 6 "reset: place all AA back to grid"): `matrix_reset(name, state, mode)` mode 0 (coordinates) vs 1 (TTT) vs 2 (state matrix) — resetting the wrong mode silently does nothing `[SRC editing.py:2126-2151]`.
- Matrix math is PyMOL-specific, NOT a standard homogeneous 4×4: pre-translation lives in the bottom row (m12..m14) and post-translation in the last column (m3,m7,m11) `[SRC editing.py:1962-1987]`; `set_object_ttt`'s `homogenous` flag is documented by PyMOL itself as "NAME IS MISLEADING AND IMPLEMENTATION POSSIBLY WRONG!" `[SRC editing.py:1904-1906]`. Build one well-tested matrix helper (pure layer, stdlib math) instead of scattering matrix literals.

**Warning signs:**
- Selecting an AA works until the first drag; afterwards clicks do nothing (game wizard was replaced).
- Drag works for the developer but "does nothing" for a user on a different mouse scheme.
- Reset button appears to do nothing for some AAs (wrong reset mode).
- Rotation of an AA via object matrix looks fine but its detection geometry is computed from stale stored coordinates (matrix ≠ coordinates — see Pitfall 12).

**Phase to address:** *viewer-interaction* (movement model decision) + *scoring-lifecycle* (reset semantics).

---

### Pitfall 7: `cmd.create` merge-vs-replace is C-dispatched and undocumented; single-call create on an existing object REPLACES state contents, and copies share atom ids

**What goes wrong:**
Building grid AAs / game copies with `cmd.create(existing_obj, fragment)` **replaces** the object's state contents (prior art observed: after `cmd.create(obj, tmp, target_state=0)`, state-1 atom count collapsed to the fragment's count — `diag_create_target_state.py`, `diag_stepwise_states.py`, `diag_fix_approaches.py`). Conversely `cmd.create(obj, seg, 1, 1)` was observed to be a **silent no-op** in a phase-5 spike despite a plausible citation `[PA-OBS]`. And a created copy **preserves source atom ids** (`diag_new_resi.py`: "cmd.create preserves source ids (backup=snapshot → copy shares id with the real CA), so id-keyed scoring can't disambiguate a real-trace click") — a game that keys on ids can confuse the copy with the original.

**Why it happens:**
The Python wrapper is thin over `_cmd.create` (C-dispatched); the docstring says only "can also be used to create states in an existing object" and "target_state = -1 appends after last state" `[SRC creating.py:960-997]` — merge-vs-replace for target_state=0 on an existing object is nowhere documented. The id-preservation is also undocumented; prior art only discovered it when scoring broke.

**How to avoid:**
- Treat every `cmd.create` onto an existing object as suspect: **assert before/after counts** (total, per-state, per-sentinel) in every smoke run.
- Adopt the prior art's proven mutations pattern for appending into a live object: build the fragment in a temp object (single-state, new chain), then merge via `pseudoatom`-style in-place insertion or a verified create form — and re-verify atom counts and sentinel counts after each step `[PA-OBS]` (their final cartoon design: "single-state new-chain copy" after **4 failed alt-conf GUI bug cycles**, per its MILESTONES.md).
- If a copy must coexist with its source in one object, disambiguate on a **different axis than id**: prior art reassigned the copy's `resi` to a disjoint offset range (real +10000) so (id, resv) is unique `[PA-OBS: diag_new_resi.py]`. AA-match: grid AAs and ligand copies should get disjoint `resi`/`chain`/`segi` namespaces by design.
- Never assume; when an API behaves differently than its docstring, read the local source (that's what `pymol-src` is for) and record the finding in AGENTS.md.

**Warning signs:**
- Atom counts shrink or explode after a create.
- "Found"/scoring fires on the wrong atom (id collision between copy and original).
- A create call that changes nothing (silent no-op).

**Phase to address:** *grid-generation* (build mechanics) — with count-assert smoke gates from the first plan.

---

### Pitfall 8: Atom identity — `index` is officially fragile; alt-conf atoms share ids; `iterate` exposes `ID` (uppercase), not coords; sentinel selectors use comparisons

**What goes wrong:**
A registry keyed on `index` breaks when atoms are added/removed; a registry keyed on `id` cannot distinguish an alt-conf copy from the original (they share the id — prior art's `wizard.py` header: "alt-conf atoms SHARE ids with originals (cmd.identify returns (model, id) with NO alt)"); code reading `id` (lowercase) inside `cmd.iterate` expressions gets the Python builtin → `NameError` or a wrong value; code that needs coordinates uses `cmd.iterate` and silently gets nothing (iterate doesn't expose x/y/z); a sentinel cleanup uses `b -999` as a selector and matches nothing.

**Why it happens:**
- `index` fragility is **officially documented**: querying.py:1313-1317 — "Atom indices are fragile and will change as atoms are added or deleted. Whenever possible, use integral atom identifiers instead of indices." `[SRC]`
- `iterate`'s expression namespace exposes the atom id as uppercase `ID` (symbol table editing.py:1444-1449) and does NOT expose coordinates at all — coords need `cmd.iterate_state` `[SRC editing.py:1578-1608]` `[PA-OBS: prior art AGENTS.md, lowercase-id transcription bug caught by smoke test]`.
- PyMOL has **no exact-match b-factor selector**: `b -999` is a malformed selector ("Selector-Error: Malformed selection") that silently matches nothing; the comparison `b < 0` is the working form `[PA-OBS]`.

**How to avoid (all `[PA-OBS]` unless cited):**
- Identity = `(object_name, atom_id)` from `cmd.identify(sel, mode=0)`/`mode=1` or iterate `ID`; `(resi, chain)` only as a human-readable debug aid.
- When alt-conf or copy-vs-original ambiguity is possible (it IS possible in AA-match: ligand structures ship altlocs; grid copies vs reference), carry `(id, alt, resv)` in pick handling — exactly the prior art's final design (`wizard.py` do_pick reads `(model, ID, alt, resv)`).
- Coordinates for detection: `cmd.iterate_state(1, sele, "...x,y,z...", space={'stored': out})` — with an explicit `space` dict, NEVER `space=None`/default (pollutes global `pymol.__dict__` — `editing.py`'s `_iterate_prepare_args` defaults; `[PA-OBS]`).
- Sentinel design: `segi='GAME'` (or AA-match's own unique segid) + `b=-999`; select with `b < 0`, never `b -999`; cleanup by sentinel ONLY, never by `resi`/`chain`/`index`.
- `cmd.sort(obj)` after `cmd.alter` of `segi`/`chain` — stale canonical order confounds later `create`/`byres` `[PA-OBS, SRC editing.py:1457]`.

**Warning signs:**
- After any removal, "found" tracking points at the wrong atom.
- An alt-conf ligand (very common) breaks pick disambiguation.
- A cleanup that removes 0 atoms with no error (malformed selector).

**Phase to address:** *grid-generation* (identity design) + *viewer-interaction* (pick identity) + *persistence* (sentinel reconstruction).

---

### Pitfall 9: PyMOL Open Source has NO undo — snapshot/restore is the only safety net, and restore itself has traps

**What goes wrong:**
A generator bug, a bad drag, or an over-broad cleanup corrupts the molecule mid-game; Ctrl-Z does nothing (`editor.py`'s `undocontext` is a stub, `editor.py:25-36` `[PA-OBS]`, quoted "not implemented in open-source"). Worse: the restore path itself has known traps — single-call `cmd.create(existing, backup)` semantics are C-dispatched (prior art keeps a delete+create two-step for an unambiguous failure path), `cmd.sort` after restore-alterations, and re-calling `verify_intact` on an already-discarded backup raises `CmdException`.

**Why it happens:**
Muscle memory from interactive PyMOL plus the existence of undo-sounding APIs (`undocontext`) that are no-ops in the open-source build.

**How to avoid (the prior art's proven discipline — all `[PA-OBS]`):**
- **Snapshot before every mutation** (`cmd.create('_aam_backup', target)` or a full `cmd.save` of the pre-game state — spec 5 requires "store the initial state" at Start anyway).
- Restore = `cmd.delete(target)` + `cmd.create(target, backup)` two-step; verify counts after.
- Orchestrator asserts the *return value* of verify/restore helpers; never re-derives by re-calling on a discarded backup.
- Every destructive op (generate, cleanup, restart, reset) routes through one backup module with the same contract — prior art's `backup.py` (snapshot/restore/discard/verify_intact) is the template.
- Document for users that Ctrl-Z does not undo plugin actions; the game's own Restart/Reset/Cleanup are the safety nets (spec already provides those buttons — keep them wired to the backup, not to "undo").

**Warning signs:**
- A "Restart" that doesn't restore the original rep/state (no snapshot was taken at Start).
- After a generator exception, a half-mutated object.
- `CmdException` mentioning a deleted backup object (double-verify/discard).

**Phase to address:** *bootstrap* (backup module early) — every destructive feature thereafter depends on it.

---

### Pitfall 10: `.pse` round-trip saves atoms/reps/colors but NOT Python game state — and object matrices may or may not survive (unverified)

**What goes wrong:**
"Save game" (spec 6: save as a pymol session + game state) writes only `cmd.save('game.pse')`. On reload: atoms are back (sentinel fields survive — `[PA-OBS]` prior art smoke: segi/b/id stable across `.pse` reload; per-atom color round-trips, verified via `exporting.py:424` → `_cmd.get_session` and `importing.py:130-175` `[PA-OBS: phase-8 research]`), but the timer, found/placed status, level/score, setup params, and per-AA movement records are gone. If AAs were moved via **object matrix** (drag whole-object path, Pitfall 6), whether the matrix round-trips through `.pse` is **[UNVERIFIED]** in this repo — flag it for a dedicated persistence smoke test before committing to the matrix movement model.

**Why it happens:**
`.pse` stores PyMOL's C-side object/session state, not plugin Python objects. The prior art's canonical pattern: `.pse` = geometry save + **JSON sidecar** = game state, zipped together for shareable games (`[PA-OBS]` v1 shipped `.pse` + `.bcm` → `.bcmz`). Note also that **wizards are pickled into the session** (`wizarding.py:176-180`, "double-pickle so that session file is class-independent") — a custom game wizard holding a Qt dialog or controller reference will break session save with a pickle error unless `__getstate__` strips non-picklables (the base class already pops `cmd`; `wizard/__init__.py:29-36`).

**How to avoid:**
- Two-file save from day one (sidecar JSON + `.pse`), assembled/disassembled in a **pure** persistence module (prior art's `persistence.py` imported registry + setup_state only).
- **Sentinel-first reconstruction** on load (prior art's proven Strategy A): rebuild the game registry from sentinel atoms in the loaded `.pse` (source of truth = the atoms the player can click), then reconcile with the sidecar by `(object, id)`; degrade gracefully when the sidecar is missing (playable but without metadata) — never let a sidecar ghost entry reference a non-existent atom.
- The sentinel cannot carry everything (prior art: `rep` not recoverable from `segi`+`b` sentinels → carried in the sidecar). Decide AA-match's sentinel payload early: what must survive in-atom (position class? grid slot?) vs what lives only in the sidecar (timer, score, which interaction each AA is meant to form).
- Custom wizard: implement `__getstate__`/`__setstate__` (pop Qt/controller) or don't keep it active during Save.
- **Verification task (persistence phase):** smoke-test whether object TTT matrices and per-object state matrices survive `.pse` save/load on PyMOL 2.5.0; if not, the AA movement model must persist transforms as explicit coordinates or sidecar matrices (see Pitfall 6's decision dependency).

**Warning signs:**
- Save → quit → relaunch → Load: timer/score/level zeroed.
- Pickle errors in the console during Save (wizard or callback holding Qt).
- An AA that was dragged onto the ligand appears back at the grid after Load (matrix didn't round-trip — or was never persisted because it lived only as TTT).

**Phase to address:** *persistence* (whole phase) — with the matrix round-trip smoke as its gate 1.

---

### Pitfall 11: Grid generation — global uniqueness, the always-solvable contract, and determinism coupling

**What goes wrong:**
Three real prior-art failures generalize directly to grid generation:
1. **Independent per-item placement collides**: prior art picked cartoon and ribbon hider segments *independently per rep*; with count=1 both picked the same deterministic window → same anchor id → `registry.register` KeyError ("hider already registered"). Fix was global disjoint allocation `[PA-OBS: phase11_keyerror_repro.py]`. AA-match: each AA must claim a unique grid slot **globally per molecule** (and each "can form interaction X" AA assignment must be globally planned), not independently randomized.
2. **Data-quirk coupling**: deduplicating alt-conf entries changed which chain was "longest", which silently shifted all generated placements to a different chain — a deterministic test flipped for a reason that had nothing to do with the fix `[PA-OBS: diag_4wb3_altconf_fix.py §4]`. AA-match: generation decisions must not depend on incidental data properties (chain lengths, atom order); pin with seeds AND assert structural invariants (slot disjointness, solvability) rather than exact placements.
3. **Schema drift**: a manifest key rename (`'file'` → `'cache_name'`) in one plan broke the loader written by another plan → KeyError on every demo load `[PA-OBS: diag_demo_keyerror.py]`. AA-match: level/demo manifests are shared contracts — version them, and iterate **every** manifest id through load in a smoke test (the prior art's post-fix smoke does exactly this).

Also: **the always-solvable guarantee is a contract between the generator and the detector.** If detection thresholds/atom-typing change after levels were generated (or after "Generate and export" produced a static file, spec 3.5), previously-generated levels may no longer be solvable. Regeneration must be forced when the detector changes (bump a detector-version stamp into generated files and refuse stale ones).

**How to avoid:**
- One global RNG + one global allocation pass per molecule (slots, then assignments), with pure-layer unit tests for disjointness and solvability (the detector is pure — it can validate the generated grid headlessly).
- Deterministic seeds stored in the level manifest; tests assert invariants, not absolute placements.
- Manifest = versioned dict with an explicit schema doc; a smoke that loads every id.
- Detector version stamp in exported games; loader refuses stale games with a clear message.

**Warning signs:**
- Two AAs occupy one slot; a required interaction is impossible on some seeds.
- A test that passed yesterday fails today with no code change (data-quirk coupling).
- Old exported games silently misbehave after threshold tuning.

**Phase to address:** *grid-generation* + *detection-engine* (contract) + *demos* (manifest).

---

### Pitfall 12: Interaction detection edge cases — protonation/valence, alt-conf, camera-vs-world coordinates, object-matrix blindness, metals, waters

**What goes wrong:**
The detector is geometrically correct but chemically wrong, or right in tests and wrong in gameplay:
- **Protonation/valence:** H-bond and salt-bridge detection need donor/acceptor typing and often H positions. PDB files typically lack hydrogens AND ligand bond orders — PyMOL's own `h_add` docstring warns: "Because PDB files do not normally contain bond valences for ligands and other nonstandard components, it may be necessary to manually correct ligand conformations before adding hydrogens" `[SRC editing.py:1216-1241]`. Auto-added H's and guessed valences can flip protonation states (HIS δ/ε, COO⁻ vs COOH, Lys⁺). The spec *requires* "small molecules of a specific protonation state and correct rendering of valence" — so demo ligands should be **SDF** (carries bond orders; `[SRC importing.py:683]` lists sdf as supported, `read_sdfstr` at importing.py:931) or pre-processed with verified protonation, NOT raw PDB ligands + `h_add`. Bond-order *display* additionally needs PyMOL's valence rendering enabled (the `cmd.valence` order command exists `[SRC editing.py:596]`; the display setting name should be verified at runtime in the first detection phase — `[UNVERIFIED]` here).
- **Alt-conf:** both conformers of a side chain can produce different interactions; iterate-and-filter on `alt` (blank vs non-blank matching in the `alt` selector is finicky — use iterate filtering `[PA-OBS: diag_4wb3_altconf_fix.py §2]`) and decide policy: detect on altloc A only, or best-scoring conformer. Dedup `(chain, resv, name)` before any `alt=''` retag merges duplicates `[PA-OBS]`.
- **Coordinate frames:** `cmd.translate` defaults to **camera coordinates** (`camera=1` — `[SRC editing.py:1636]`). Grid placement math computed in world coordinates but applied via camera-frame commands silently misplaces everything. Pick one frame (world/object) for all generation/detection math; convert explicitly at the boundary.
- **Matrix blindness:** if AAs are moved via object TTT matrices (Pitfall 6 Option B), the stored atom coordinates do NOT change — a detector reading `iterate_state` coordinates sees the *unmoved* AA while the viewer shows it placed (or vice versa). Either read the object matrix and compose it in the detector, or use a movement model that bakes transforms into coordinates. This is a **correctness-critical** decision, not a nuance.
- **Metals & waters:** metal coordination detection needs generous distance criteria and explicit handling of bridging waters (spec's interaction list includes metal coordination "when metal present"); waters/nearby solvent must be excluded from contact counting unless intended. Metal-ligand bonds often exist in PDB CONECT records but geometry varies — thresholds must come from the approved sources (per PROJECT.md), not memory. *(No numeric thresholds asserted here by design.)*
- **`cmd.find_pairs` if used for candidate generation:** officially "Only checks atom orientation, not atom type (so would hydrogen bond between carbons for example), so make sure to provide appropriate atom selections" `[SRC querying.py:1332-1369]` — and it returns `(model, index)` tuples (fragile — convert to ids immediately).

**How to avoid:**
- Detector = pure module (stdlib) consuming typed atom records `(elem, name, resn, resi, chain, alt, x, y, z, charge?)` collected via `iterate_state`; all chemistry policy (protonation assumptions, alt-conf policy, water exclusion, typing tables) explicit and unit-tested.
- Fix the ligand provenance pipeline: SDF-first for demo ligands (bond orders + explicit H), or a human-approved preparation step documented in `DATA_SOURCES.md`.
- One coordinate-frame convention documented at the top of the detection module; conversion helpers tested.
- Decide the movement-model dependency (matrix vs coordinates) BEFORE writing the detector (see Pitfall 6/10 dependency chain).
- Thresholds: sourced from the specified published references (proLIF/PLIP/binana-style definitions per spec) and human-approved — record each threshold + source + approval in a doc; never invent values.

**Warning signs:**
- Detection result changes when the view is rotated (camera-frame leak) or between runs (matrix blindness).
- H-bonds detected to carbons / missing N-H donors (typing or H-adding mistake).
- Different results on the same ligand loaded from PDB vs SDF (valence/protonation divergence).
- An alt-conf ligand scores differently depending on which conformer is "current".

**Phase to address:** *detection-engine* (whole phase) — with ligand provenance decided in *demos* and the matrix question closed in *viewer-interaction*.

---

### Pitfall 13: Cleanup must remove ONLY game-generated content — generic filters destroy the user's scene

**What goes wrong:**
"Cleanup model" (spec 3.6: "clear generated by the game that is not in the original object") implemented as `cmd.remove('hetatm')` / `resn X` / `not polymer` deletes the user's ligands, ions, waters, or membrane. There is no undo (Pitfall 9) — the user's prepared scene is gone.

**Why it happens:**
Game objects and real chemistry share chemical categories (hetatm, non-polymer). The operative phrase in the spec is "**not in the original object**" — that requires knowing the original, not filtering by chemistry. `[PA-V1DOC]` prior art hit exactly this class of bug in design review (membrane demos) and enshrined the sentinel rule.

**How to avoid:**
- Every game-created atom carries the sentinel (`segi='AAM'` — pick a unique segid — plus `b=-999`); cleanup = `cmd.remove("obj and segi AAM")` only.
- Every game-created **object** (grid AA objects, if separate) gets a reserved name prefix (`_aam_*`) via `cmd.get_unused_name('_aam_')` `[PA-V1DOC]`; cleanup deletes `cmd.get_names("objects")` filtered by the prefix only. **Note the trade-off from prior art:** prior art inserted hiders INTO the target object specifically so the player couldn't toggle one object to win. AA-match has the OPPOSITE requirement — the player must click/select/move whole AAs, which strongly favors separate AA objects. That's fine for cleanup (prefix-deletes), but then the game must ensure the ligand object itself is never game-generated (never prefixed) and never deleted by cleanup.
- Snapshot at Start (Pitfall 9) makes cleanup verifiable: after cleanup, `cmd.count_atoms(target)` == pre-Start count, and the object-name list minus `_aam_*` equals the original list.
- Never cleanup by: `hetatm`, `water`, `solvent`, `not polymer`, residue-name lists.

**Warning signs:**
- After Cleanup, anything the user loaded is missing.
- Cleanup misses some game content (unnamed/prefixed inconsistently).
- `cmd.get_names("objects")` grows during Generate (leaked temp objects).

**Phase to address:** *grid-generation* (naming + sentinel conventions) + *scoring-lifecycle* (Cleanup button) — verified in *demos*.

---

### Pitfall 14: Citation truthfulness and demo-set provenance — the one rule that can void the whole project

**What goes wrong:**
A demo set ships with a PDB/SDF ID, DOI, protonation source, or interaction definition that nobody verified — or the manifest schema drifts and loaders break (Pitfall 11.3). The project constraint is absolute: "Do NOT make up anything. ALL claims and citations (DOIs, PDB IDs, sources) MUST BE VERIFIED against a source and explicitly approved by a human" (AGENTS.md / spec.md).

**Why it happens:**
Agent-generated citations look plausible; fabrication is easy and detection is hard after the fact. Also, multi-phase development drifts manifest schemas (the prior art's `'file'`→`'cache_name'` KeyError `[PA-OBS]`).

**How to avoid:**
- Keep the PROJECT.md protocol exactly: agent proposes candidates (IDs + sources + why) → **human verifies and approves** → only then fetch/commit. The approval is a visible checkpoint in the plan (UAT), not a formality.
- Every demo/level data file ships with `DATA_SOURCES.md` entries: PDB ID + DOI + publication + protonation/interaction source + license. Prior art maintained exactly this (`DATA_SOURCES.md` in v1; its own docs committed "fix wrong DOI" fixes — proof that even careful projects catch DOI errors late `[PA-OBS: bioCHEMeleon commit a360e34]`).
- Version the data manifest; smoke-test loading every entry (Pitfall 11.3).
- Thresholds for interaction definitions: same protocol — each numeric criterion (distance/angle cutoffs) recorded with its published source and human approval in a detection doc.

**Warning signs:**
- A demo PDB ID or DOI appears in code/docs without a `DATA_SOURCES.md` entry.
- A threshold number appears in a test with no source comment.
- Loader KeyError on a demo id (schema drift).

**Phase to address:** *demos* (entire phase is this) + *detection-engine* (threshold provenance).

---

### Pitfall 15: Performance and event-loop hygiene with many generated objects and per-frame game code

**What goes wrong:**
An NxN grid (up to ~81 AAs) × several molecules × several levels can mean hundreds of objects and thousands of game atoms. Symptoms: Generate takes tens of seconds with the GUI frozen (all `cmd.*` runs on the main/GUI thread — a long synchronous loop blocks Qt + PyMOL rendering), `.pse` saves balloon, per-drag refresh lags, and detection-on-confirm walks every atom pair in Python.

**Why it happens:**
PyMOL commands take an internal lock; all `cmd.*` calls should happen on the GUI main thread (`[PA-V1DOC]` v1 Pitfall: threading + cmd = deadlocks/segfaults; the prior art used `QTimer` on the main thread only). Python-loop pair enumeration over all atoms is O(N²) where N is avoidable.

**How to avoid:**
- **Data-size discipline:** the detection workload is small by design (one ligand + ≤ 81 AAs). Enumerate only game-relevant atoms via `iterate_state` with narrow selections (`segi AAM`, ligand selection) — never `cmd.get_model` on a whole large object (full-structure Python copy; the classic OOM trap `[PA-V1DOC]`).
- If any candidate-pair pre-filtering is wanted, use C-side selection (`within 5 of ...`) or `cmd.find_pairs` (mind its orientation-only caveat, Pitfall 12) — but at AA-match's data sizes, plain Python over the collected coordinates is fine and keeps the detector pure/testable.
- Keep per-frame/per-pick work O(1): cache last-seen pick; refresh only the moved object; don't rebuild all reps after each change (`[PA-V1DOC]` prior art's rep-refresh trap).
- Chunk any long generation loop and yield to the event loop between chunks (modeless progress), or accept a brief modal "Generating…" — but never a 30-second silent freeze.
- Object-count hygiene: one object per AA is the natural model (click/drag/move whole AA), but prefer **one object per AA built as a single-state object with the AA's own atoms** — avoid exploding each AA into many objects or states; strip waters/solvent from demo structures before bundling (prior art did this for its membrane demos `[PA-OBS]`).
- Performance budget (adopt prior art's): Generate < 30 s on the largest demo; click/drag feedback < 200 ms.

**Warning signs:**
- "Start"/Generate freezes the GUI > 5 s even on small molecules.
- `.pse` files tens of MB; Load takes seconds.
- Detection-on-Confirm takes visible time (it should be < 100 ms at this scale).

**Phase to address:** *grid-generation* (allocation + object model) + *viewer-interaction* (per-drag cost) — with a large-demo perf check in *demos*.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Qt imports at module level (like v1's `__init__.py`) | One less import line | Every WSL test must stub `sys.modules['pymol']`; Qt tier bleeds into pure/cmd tiers | **Never** — lazy-import Qt inside functions |
| numpy in the detection module | Familiar vector math | Pure layer untestable in WSL (no numpy on 3.6.9) | Only in cmd-tier helpers; keep detector stdlib |
| Keying game state on `(resi, chain)` or `index` | Human-readable | Ambiguous across altlocs/copies; index shifts on any removal | Debug aid only; identity = `(object, id)` + sentinels |
| One-shot `cmd.create(existing, fragment)` to append atoms | Feels natural | Undocumented C-side replace semantics eat the object (Pitfall 7) | **Never** without count assertions |
| Object-matrix movement with coordinate-based detection | Drag feels native | Detector reads stale coordinates → wrong scoring (Pitfall 12) | Only if the detector composes the matrix — decide explicitly |
| Storing game state only in `.pse` | One file | Timer/score/placement metadata lost on reload | **Never** — sidecar JSON + sentinel reconstruction |
| Cleanup by chemical filters (`hetatm`, `not polymer`) | One-liner | Destroys user's ligands/membrane; no undo | **Never** — sentinel + prefix only |
| Per-item independent randomization in generation | Simple code | Slot collisions, unsolvable grids (Pitfall 11.1) | **Never** — global allocation pass |
| Inventing interaction thresholds from memory | Fast | Violates truthfulness constraint; wrong chemistry | **Never** — sourced + human-approved |
| Hardcoding paths or assuming WSL cwd | Quick demo | Breaks in Windows PyMOL / after repo move | **Never** — `to_windows_path()` + `__file__`-relative |
| `space=None` in iterate/alter | Less typing | Pollutes global `pymol.__dict__`; cross-call state leaks | **Never** — explicit `space={'stored': ...}` |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `pymol.Qt` event loop | Spinning a new `QApplication`/`exec_()` for the game window | Use PyMOL's existing QApplication; `dialog.show()` only (modeless); `exec_()` only on child file/message dialogs |
| Game wizard + `cmd.drag` | Calling `cmd.drag` while the game wizard is active | Re-install the game wizard after drag Done, or drive movement explicitly (Pitfall 6) |
| Game wizard + user's wizards | Blowing away the user's active wizard | Save on activate, restore on deactivate (`_saved_wizard` pattern) |
| `mouse_selection_mode` | Assuming clicks yield one atom | Set atomic mode at Start; save/restore; implement BOTH `do_pick` and `do_select` (Pitfall 5) |
| `cmd.load` of demo data | Passing `/mnt/c/...` or cwd-relative paths | `to_windows_path()` + package-`__file__`-relative paths (Pitfall 2) |
| SDF vs PDB ligands | Loading PDB ligands and expecting valence/H chemistry | SDF-first for ligand chemistry (bond orders, explicit H); `h_add` only with documented caveats (Pitfall 12) |
| Level/demo manifests | Two plans editing the schema independently | Versioned schema doc + smoke loading every id (Pitfall 11.3) |
| Saved games + repo moves | Absolute paths inside saved files | Store data relative to package; re-resolve on load; document the limitation |
| `cmd.get_unused_name` | Hardcoding `_tmp1`-style names | Prefix + `cmd.get_unused_name('_aam_')` for every transient |
| Parallel GSD waves | Shared git index commit races | Worktree-per-plan protocol (root AGENTS.md) — keep it; it happened for real in prior art's Phase 4 |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `cmd.get_model(large_obj)` | RAM spike; multi-second freeze | `iterate_state` with narrow selections; `count_atoms` for counts | Any large demo; fatal on membrane-scale structures |
| Python O(N²) pair loops over all atoms | Confirm/hint lags | Detect over game-atoms only (ligand + AAs); pure-layer math on collected coords | Grid ≥ 6×6 with big ligands |
| Rebuilding all reps/objects after each move | Drag lag | Refresh only the moved object | >20 AAs placed |
| Synchronous generation loop | GUI frozen during Generate | Chunk + yield (or brief modal progress) | >200 ms of work |
| Per-frame polling without caching | Constant CPU; duplicate pick processing | Cache last-seen pick; `cmd.unpick()` after read | Long idle sessions |
| Unstripped demo structures (waters/solvent) | Bloated saves; slow load | Strip before bundling (prior art did this for membrane demos) | All demos |
| Hundreds of objects with verbose reps | Slow scene, big `.pse` | Minimal reps on grid AAs; single-state objects; no per-AA surface/cartoon extras | N ≥ 7 grids, multi-level saves |

## Security / Truthfulness Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Fabricated or unverified DOIs/PDB IDs/protonation sources | Violates the project's absolute truthfulness rule; educationally wrong content | Human-approval protocol; `DATA_SOURCES.md` for every file; never generate citations from memory |
| Interaction thresholds without published sources | Chemically wrong game teaches wrong science | Every cutoff sourced (approved refs) + approval recorded |
| Vendoring an unapproved lib into `3rd_party_lib/` | License violation; constraint breach | List → user approval → vendor with license note (spec.md) |
| Loading user-supplied files (`cmd.load(user_path)`) without error handling | Crash loops; confusing errors | Catch `CmdException`, validate extension, clean message (local risk is low but UX matters) |
| Network access at gameplay time | Spec forbids it; flaky offline behavior | All demo data pre-downloaded + committed with citations; no fetch-on-play |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Modal setup/game window | Viewer unclickable; game unplayable | Modeless `dialog.show()`; reserve modals for confirmations |
| Timer runs during modal file dialogs | Unfair times | Pause timer while any modal child is open (v1 UX rule) |
| No feedback on selecting/moving an AA | Player unsure anything happened | Distinct selected color + status; flash on pick (spec 7.2 already requires color change) |
| No feedback when a placement forms nothing | Player thinks the game is broken | On Confirm, show per-interaction result summary (spec 6 requires counts; keep it honest — no helper lines *during* play, but post-confirm results are allowed) |
| Drag impossible on user's mouse scheme | Game unplayable for some users | Verify editor scheme at Start; provide keyboard/button-based movement fallback (Pitfall 6) |
| Hint reveals too much | Game trivial | Spec's hint = recolor carbons of *eligible* AAs only — keep it coarse |
| Explanations too sparse | Students don't learn | In-game explanation of each interaction type (spec UI standard); prior art shipped a post-game debrief — a strong pattern to reuse |
| Accidental Skip/Give-up | Progress lost | Confirmation warnings (spec 6 already requires them — don't skip) |

## "Looks Done But Isn't" Checklist

- [ ] **Bootstrap:** Often missing the path helper + headless smoke recipe — verify one tiny demo loads end-to-end via `cmd.exe` from WSL in phase 1.
- [ ] **Purity:** Often numpy/pymol sneaks into the "pure" layer — verify `python3.6 -m unittest` passes with NO stubs for pure modules.
- [ ] **Setup GUI:** Often `.exec_()` on the main window or a GC'd dialog — verify the viewer stays interactive with the window open (HUMAN GUI CHECK) and the window survives minimize/re-open.
- [ ] **Wizard:** Often `do_pick` only — verify clicking in DEFAULT 3-Button Viewing mode reaches the game (HUMAN GUI CHECK), and the user's prior wizard + selection mode are restored after quit.
- [ ] **Drag:** Often works only on dev's mouse scheme — verify `get_editor_scheme()` handling and the post-drag wizard re-install (HUMAN GUI CHECK).
- [ ] **Grid generation:** Often slot collisions or unsolvable grids on some seeds — verify pure-layer invariants (disjoint slots, solvability) across ≥ 100 seeds.
- [ ] **Generation into live session:** Often `cmd.create` replace/no-op surprises — verify before/after atom + sentinel counts on every Generate smoke.
- [ ] **Detection:** Often right on SDF, wrong on PDB (valence/H) — verify one ligand through both paths with the same expected interactions.
- [ ] **Detection:** Often camera/world frame leak — verify results are rotation-invariant (rotate view, re-check).
- [ ] **Matrix movement:** Often detector reads stale coords — verify a moved AA's detection result matches its on-screen position (HUMAN GUI CHECK).
- [ ] **Persistence:** Often saves `.pse` without sidecar, or wizard pickle crash — verify Save → quit → relaunch → Load restores timer/score/placements and console is clean.
- [ ] **Persistence:** Often assumes object matrices round-trip — verify TTT/state-matrix survival in a dedicated smoke BEFORE committing to the movement model.
- [ ] **Reset:** Often resets the wrong transform mode — verify Reset returns AAs to grid slots when moved by the chosen movement model.
- [ ] **Cleanup:** Often over-matches — verify on a demo with ligand+ions+water: Cleanup leaves exactly the original object set.
- [ ] **Demos:** Often missing citations or schema drift — verify `DATA_SOURCES.md` covers every file and the every-manifest-id smoke passes.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Qt code contaminates lower tiers (1) | MEDIUM | Extract pure/cmd cores; make Qt lazy; re-layer tests |
| Path bugs (2) | LOW | Add `to_windows_path()`; re-run demo-load smoke |
| numpy/dataclasses in pure layer (3) | LOW-MEDIUM | Rewrite with stdlib math; add import gate |
| Modal/GC'd dialog (4) | MEDIUM | `show()` + module-level singleton; re-test viewer interactivity |
| Missing `do_select` route (5) | LOW | Add canonical select→pick map; re-run human pick check |
| `cmd.drag` clobbers wizard (6) | MEDIUM | Adopt explicit-transform model or re-install wizard post-drag |
| `cmd.create` data loss (7) | MEDIUM (backup!) | Restore from snapshot; rebuild with count-asserted steps |
| Identity/alt-conf mixups (8) | MEDIUM | Switch to `(id, alt, resv)` identity; rebuild registry from sentinels |
| No-backup corruption (9) | HIGH (no undo) | Reload from disk; then add snapshot-first discipline |
| Lost game state on reload (10) | MEDIUM | Add sidecar + sentinel-first reconstruction |
| Collision/unsolvable grids (11) | MEDIUM | Global allocation pass + invariant tests + regenerate levels |
| Chemistry-frame errors (12) | HIGH (wrong science) | Fix provenance (SDF-first), frames, matrix handling; re-validate against approved sources |
| Cleanup data loss (13) | HIGH if no backup | Restore from snapshot; sentinel/prefix-only cleanup |
| Citation fabrication (14) | HIGH (trust) | Remove offending content; re-run human approval for replacements |
| Perf freezes (15) | MEDIUM | Narrow selections; chunk; cap object reps |

## Pitfall-to-Phase Mapping

(Phase topics are proposed names — the roadmap should map these to numbered phases; ordering follows dependency: bootstrap → setup-GUI → grid-generation → viewer-interaction → detection-engine → scoring-lifecycle → persistence → demos → polish.)

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1. Qt tier discipline | bootstrap (+ all) | Pure/cmd tiers pass WSL tests with no pymol stubs; Qt checks marked human-verify in plans |
| 2. WSL→Windows paths | bootstrap + demos | One demo loads headlessly from WSL; all bundled files load via helper |
| 3. Pure-layer stdlib-only | bootstrap | Import gate (no numpy/pymol/dataclasses in pure modules); 3.6 unit tests green |
| 4. Modeless Qt GUI | setup-GUI | Grep gates (no Tk, no `.exec_()` on main dialog); viewer interactive with window open (HUMAN) |
| 5. Wizard two-entry-point picking | viewer-interaction | Pick works in default Viewing mode on fresh PyMOL (HUMAN); prior wizard/selection-mode restored |
| 6. Drag model + editor-scheme gate | viewer-interaction | Movement model documented; drag works (or fallback) on non-3-button scheme (HUMAN); reset returns AAs to grid |
| 7. `cmd.create` semantics | grid-generation | Count-asserted generate smoke green; no silent no-ops/replaces |
| 8. Atom identity & selectors | grid-generation + viewer-interaction + persistence | Alt-conf demo pick/scoring correct; `b < 0` selectors; iterate uses `ID`/`space=` |
| 9. No-undo backup discipline | bootstrap | Snapshot at Start; corrupt-mutation simulation recovers |
| 10. Save/load round-trip | persistence | Save→quit→load restores timer/score/placements; matrix round-trip smoke result recorded |
| 11. Generation uniqueness/contract | grid-generation + detection-engine + demos | ≥100-seed invariant tests; detector-version stamp rejects stale games; every-manifest-id smoke |
| 12. Detection chemistry/frames | detection-engine (+ demos provenance) | SDF/PDB parity test; rotation-invariance test; thresholds documented with approved sources |
| 13. Cleanup isolation | grid-generation + scoring-lifecycle | Demo with ligand/ions/water: Cleanup leaves original object set exactly |
| 14. Citation truthfulness | demos (+ detection-engine) | `DATA_SOURCES.md` complete; human approval recorded per file & threshold |
| 15. Performance/event loop | grid-generation + viewer-interaction + demos | Largest demo: Generate < 30 s, pick/drag < 200 ms (headless timing + HUMAN feel check) |

## Open Questions (need phase-specific or human verification)

1. **[UNVERIFIED] Do object TTT / state matrices survive `.pse` save/load on PyMOL 2.5.0?** Decides whether the whole-object drag path (Pitfall 6 Option B) can checkpoint via sessions alone. One persistence-phase smoke: move an object via matrix, save, reload, compare `cmd.get_object_matrix` before/after. (`get_object_matrix` is documented as "unsupported" but functional — querying.py:89-100.)
2. **[UNVERIFIED] Default `editor_scheme` on stock installs and exact behavior when ≠3** for `cmd.drag` (dragging.py:49-54 self-destructs). Needs one human GUI check on the default Windows install; drives the fallback UX.
3. **[UNVERIFIED] Valence display setting name/behavior** (`set valence, on`-style) for "correct rendering of valence" (spec requirement); `cmd.valence` order-setting command verified at editing.py:596, the display setting should be confirmed at runtime.
4. **[MEDIUM] Detection threshold values for all seven interaction types** — deliberately not asserted here; must be sourced from the specified published references (proLIF/PLIP/binana-style definitions) and human-approved per PROJECT.md. The *engineering* pitfalls (frames, alt-conf, protonation, matrix blindness) are independent of the numbers and can be built/tested meanwhile.
5. **[MEDIUM] Multi-state ligand handling policy** — demo ligands with biological-assembly states or NMR models: detect on state 1? Collapse first (prior art's `collapse_to_single_state` pattern `[PA-OBS]`)? Decide in demos with the curated data.
6. **[LOW] Exact mouse-mode constants** (`button_mode` values for pick modes) — prior art deliberately avoided hardcoding (fragile across versions); prefer the wizard + `mouse_selection_mode` route which sidesteps button-mode coupling entirely `[PA-OBS]`.

## Sources

**Prior art (primary evidence — real bugs from our previous PyMOL 2.5.0 game, `tmp/bioCHEMeleon/`, git-ignored):**
- `tmp/bioCHEMeleon/AGENTS.md` — distilled domain rules from 12 shipped phases (headless recipe, cmd.create no-op, path/cwd resolution, grep-gate false positives, sentinel rules, no-undo, pseudoatom returns None, ID uppercase, b<0 selector, space= discipline).
- `tmp/bioCHEMeleon/biochemeleon/wizard.py` — shipped PickWizard: do_pick/do_select duality, mouse_selection_mode save/restore, alt-conf id sharing, saved-wizard pattern. HIGH.
- `tmp/bioCHEMeleon/biochemeleon/__init__.py` (lines ~520-930) — wizard deactivate/prior-wizard-reference loss fixes across three call sites. HIGH.
- `tmp/bioCHEMeleon/smoke/diag_*.py` (17 files) — real bug forensics: alt-conf anchor duplicates (`diag_4wb3_altconf_fix.py`, `diag_4wb3_anchor.py`), `cmd.create` target_state replace semantics (`diag_create_target_state.py`, `diag_fix_approaches.py`, `diag_stepwise_states.py`), id aliasing of copies (`diag_new_resi.py`), per-rep pick collision KeyError (`phase11_keyerror_repro.py`), nucleic-acid empty CA selectors (`diag_nucleic_hiders.py`), manifest schema drift (`diag_demo_keyerror.py`), rep-applied-but-invisible rendering (`diag_altconf_visibility.py`, `diag_render_question.py`). HIGH.
- Previous project's v1 research (recovered from git `bioCHEMeleon` @ `123b115`): `.planning/research/PITFALLS.md` (PyMOL edition) — Qt-vs-Tk, modeless rule, dialog GC, thread/lock rules, `.pse` round-trip gaps, cleanup over-match, no-undo, WSL path, perf traps, RCSB/SASBDB citation policies. HIGH (runtime-verified in that project).
- Previous project's Phase 8 persistence research (`.planning/phases/08-persistence-and-shareable-puzzles/08-state-reconstruction-RESEARCH.md`) — sentinel-first reconstruction, sidecar reconciliation, per-atom color round-trip via `exporting.py:424`/`importing.py:130-175`. HIGH.
- Previous project's `MILESTONES.md` — "4 failed alt-conf GUI bug cycles" before the single-state new-chain design; 6 runtime library-bug discoveries in Phase 3. HIGH.

**PyMOL 2.5.0 source (local, verified 2026-09-05) — `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/bioCHEMeleon/tmp/pymol-src/modules/pymol/`:**
- `editing.py:1018-1076` — `cmd.drag` replaces non-Dragging wizards; edit-mode interplay.
- `wizard/dragging.py:26-56,72-80,97-101` — editor_scheme==3 gate + self-destruct; whole-object matrix drag; button-mode restore.
- `wizard/__init__.py:29-47` — wizard pickling (`__getstate__` pops `cmd`; session `wizard_storage`).
- `wizarding.py:62-119,176-184` — one-wizard stack; wizards pickled into session ("double-pickle").
- `editing.py:1216-1253` — `h_add` valence caveat (ligand bond orders).
- `editing.py:1578-1608` — `iterate_state` + `space=` handling.
- `editing.py:1610-1652` — `translate` camera-coordinate default; state semantics (-1/0/all).
- `editing.py:1881-1944` — `set_object_ttt` (state UNUSED; misleading `homogenous` flag per PyMOL's own docstring).
- `editing.py:1946-2005` — PyMOL-specific matrix layout (pre/post-translation positions).
- `editing.py:2006-2055` — `transform_object` matrix_mode semantic switch.
- `editing.py:2126-2166` — `matrix_reset` modes 0/1/2.
- `editing.py:596` — `cmd.valence` order command.
- `editing.py:1444-1449,1457` — iterate symbol table (`ID` uppercase); `sort` after alter.
- `querying.py:89-100` — `get_object_matrix` ("unsupported" but functional).
- `querying.py:1269-1300` — `identify` modes (no alt in either mode).
- `querying.py:1302-1330` — official `index` fragility note.
- `querying.py:1332-1369` — `find_pairs` orientation-only warning; (model, index) return.
- `querying.py:1371-1392` — `get_extent` (grid placement).
- `creating.py:960-1036` — `create` signature/docstring gaps (merge-vs-replace undocumented); properties unsupported note.
- `creating.py:1082+` — `pseudoatom` defaults (elem='PS', resn='PSD', etc. — prior-art-verified).
- `importing.py:683,931-959` — SDF supported; `read_sdfstr`.

**Environment (verified on this machine, 2026-09-05):**
- WSL `python3.6.9`: no numpy, no dataclasses; typing + f-strings OK.
- Root `AGENTS.md` + `spec.md` + `.planning/PROJECT.md` (this repo) — environment split rules, dependency constraints, truthfulness protocol, key decisions.

**Unverified / flagged:** Open Questions 1–6 above. No numeric interaction thresholds asserted anywhere in this file by design.

---
*Pitfalls research for: AA-match — PyMOL 2.5.0 plugin educational interaction-matching game*
*Researched: 2026-09-05*
