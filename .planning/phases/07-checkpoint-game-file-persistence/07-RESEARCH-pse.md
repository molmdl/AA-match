# Phase 7: Checkpoint & Game-File Persistence — Research: `.pse` round-trip mechanics

**Researched:** 2026-09-21
**Domain:** PyMOL 2.5.0 session-save (`.pse`) round-trip + wizard pickling + checkpoint reconstruction
**Confidence:** **HIGH** — the standing gate was closed by an actual two-process headless probe run on the target build (`SMOKE-17`, exact commands + output below), cross-checked against the local PyMOL 2.5.0 source (`bioCHEMeleon/tmp/pymol-src/modules/pymol/`, same 2.5.0 line).

**Gate question answered:** *"Do object matrices survive `.pse`, or must transforms be persisted via the sidecar?"* → **Both baked coordinates AND object matrices survive `.pse` BIT-EXACTLY (max delta 0.000e+00 across all 360 atoms and all 20 game objects + a non-identity matrix probe). The sidecar does NOT need matrices.** The sidecar's job is Python game state only.

---

## Round-trip verdict (the gate result)

**PROVEN — geometry/display classes round-trip bit-exactly; Python game state does not survive (as expected); the GameWizard save-side pickles cleanly but restore is BROKEN as-is (defect root-caused and fix-shape PROVEN).**

**Evidence — real probe, two separate Windows PyMOL 2.5.0 processes (a true quit→relaunch):**

- Script: `smoke/smoke_17_pse_roundtrip.py` (committed; probe-only, no production changes)
- Commands (from repo root):
  - `bash smoke/run_smoke.sh smoke/smoke_17_pse_roundtrip.py 240` (run 1 = SAVE phase; run 2 = VERIFY phase; each run is a fresh `cmd.exe /c C:\src\run-conda-pymol.bat -cq smoke\smoke_17_pse_roundtrip.py` process)
- Fixture dir: `tmp/smoke fixtures/aam_pse17/` (git-ignored; `game.pse` + `game.snapshot.json`, snapshot written through the REAL pure container `persistence.save_container(kind='checkpoint')`)
- Scenario: `gamestart.start_game()` (seed 42 defaults, 2 molecules, 18 slots, wizard ACTIVE on the stack) → scripted pick (`do_select`) → `wiz.move_to(centroid + (2.5, 1.25, -0.75))` → `wiz.rotate_axis((0,0,1), 30°)` (baked world-frame moves; identity-matrix invariant asserted) → plus a `_aam_17probe` pseudoatom carrying a **non-identity** object matrix (`cmd.transform_object(..., homogenous=1)`, Rz 30° + t=(3,2,1)) → `cmd.save()` **with the wizard live on the stack**.

**Observed verify-phase output (verbatim key lines):**

```
SMOKE-17 B coordinates round-trip (float32-tight <= 1e-6) PASS max_delta=0.000e+00 exact=True props_bad=[]
SMOKE-17 VERDICT coords: max_delta=0.000e+00 exact=True -> PROVEN
SMOKE-17 B sentinel segi survives exactly             PASS bad=[]
SMOKE-17 B sentinel b-factor survives (max delta 0.000e+00) PASS
SMOKE-17 B per-atom colors round-trip exactly         PASS bad=[]
SMOKE-17 B per-atom representations (reps) round-trip exactly PASS
SMOKE-17 B camera view round-trips (<= 1e-6)          PASS max_delta=0.000e+00 exact=True
SMOKE-17 B game-object matrices round-trip (identity invariant) PASS max_delta=0.000e+00
SMOKE-17 B NON-IDENTITY object matrix round-trips (probe) PASS probe matrix max_delta=0.000e+00
__init__() missing 2 required positional arguments: 'payload' and 'registry'
Session-Warning: unable to restore wizard.
SMOKE-17 B wizard restore = DOCUMENTED defect signature (Phase 7 must fix) PASS get_wizard()=None, save-side pickle_ok=True
SMOKE-17 B sentinel-first reconciliation (segi AAM and b < 0) PASS per-object counts []
SMOKE-17 B GameState.from_dict lossless (checkpoint core) PASS
SMOKE-17 B engine stays DEAD after load (sidecar owns game state) PASS engine._game=None
=== SMOKE-17 PASS ===
```

Full console transcripts are reproduced in the probe output; both runs ended `=== SMOKE-17 PASS ===` (runner grep green, exit 0).

---

## What survives `.pse` (data class → survives? → evidence)

| Data class | Survives? | Evidence |
|---|---|---|
| Object names (`_aam_*`, 20 objects) | **YES exact** | SMOKE-17 B `object names round-trip EXACTLY loaded=20 want=20` |
| Baked coordinates (movement model, 360 atoms incl. the moved+rotated AA) | **YES bit-exact (max_delta = 0.0)** | SMOKE-17 B `VERDICT coords: max_delta=0.000e+00 exact=True -> PROVEN`. PyMOL stores coords as float32 in memory; save/load is a verbatim copy — no recomputation. The 02-09 float32 1e-6 tolerance law is satisfied with margin zero. |
| Sentinel `segi='AAM'` (per atom) | **YES exact (string equality)** | SMOKE-17 B `sentinel segi survives exactly bad=[]` |
| Sentinel `b=-999.0` (per atom) | **YES exact (delta 0.0)** | SMOKE-17 B `sentinel b-factor survives (max delta 0.000e+00)` |
| Atom `id` values (`(object, id)` identity keys) | **YES (all 360 keys identical)** | SMOKE-17 B `atom (object, id) keys round-trip loaded=360 want=360` |
| Per-atom colors (incl. the pick-highlight recolor) | **YES exact (color index ints)** | SMOKE-17 B `per-atom colors round-trip exactly bad=[]` (confirms PA-OBS exporting.py:424 / importing.py:130-175 on our real objects) |
| Per-atom representations (`reps`, sticks-bit) | **YES exact** | SMOKE-17 B `per-atom representations (reps) round-trip exactly` — placement._normalize_reps look survives; no sidecar needed for reps |
| Camera view (`cmd.get_view()`, 18 fields incl. roll + clip slab) | **YES bit-exact (delta 0.0)** | SMOKE-17 B `VERDICT view: max_delta=0.000e+00 exact=True` — **resume feel is free**; no compose replay needed on load |
| Object TTT matrices — identity (all game objects) | **YES exact** | SMOKE-17 B `game-object matrices round-trip (identity invariant) PASS max_delta=0.000e+00` |
| Object TTT matrices — **non-identity** (probe object) | **YES exact** | SMOKE-17 B `NON-IDENTITY object matrix round-trips (probe) PASS max_delta=0.000e+00` — closes Pitfall 10's `[UNVERIFIED]` definitively |
| Atom name/elem/resn/resi properties | **YES** | part of the `props_bad=[]` check in the coords line |
| `cmd.save` with Windows `C:\...` paths (via `paths.to_windows_path`) | **YES** | probe saved to `C:\...\tmp\smoke fixtures\aam_pse17\game.pse` and re-loaded it in a fresh process |
| Bonds/connectivity (implied by intact detection-ready geometry) | **YES** (not separately diffed) | atom set + coords + names identical; detector consumed the loaded geometry in the reconciliation counts [inferred — flag for the plan's smoke if paranoid] |

| Data class that does **NOT** survive | Evidence |
|---|---|
| `engine._payload` / `_registry` / `_game` / `_ligand_content` (module globals) | SMOKE-17 B `engine stays DEAD after load ... engine._game=None` — the `.pse` stores C-side object/session state, never plugin Python state (Pitfall 10 confirmed on this build) |
| `gamestart._last_start` (restart replay inputs) | same mechanism — Python module state [probe-observed via `engine._game=None`; `_last_start` is the same class of state] |
| Timer / scores / counters / level-molecule position | same — **carried by the sidecar**: `GameState.from_dict` proved lossless (`SMOKE-17 B GameState.from_dict lossless PASS`, `timer_anchor=1789931114.7336133` exact through JSON) |
| The GameWizard (as-is) | **NO — restore raises** (see next section; save side is clean) |

**`.pse` file format note:** a plain `.pse` is a pickled session dict written uncompressed — `session_compression` is **deprecated** with an explicit warning pointing at `.pze` / `.pse.gz` for compression (`exporting.py:466-473`). The roadmap phrase "zipped .pse" should be read as "`.pse` + JSON sidecar, optionally zipped together by the plugin" (the prior-art `.bcmz` pattern) — do not rely on `.pse` self-compression.

---

## Wizard pickling (what breaks, what must change, class-independence mechanism)

**The mechanism (PyMOL 2.5.0 source, verified on disk):**

- Save: `pymol/wizarding.py:176-180` `session_save_wizard` — `stack = _self.get_wizard_stack(); session['wizard'] = cPickle.dumps(stack, 1)` ("double-pickle so that session file is class-independent"). Registered as a `_session_save_tasks` entry (`pymol/cmd.py:52-53`).
- Restore: `wizarding.py:182-196` `session_restore_wizard` — `pkl.fromString(session['wizard'])`, then per wizard `wiz.cmd = _self` + `wiz.migrate_session(version)`, then `_self.set_wizard_stack(wizards)`. **The whole try block is wrapped in `except Exception` → prints the exception + `"Session-Warning: unable to restore wizard."`** — a failed restore is NON-FATAL but prints to the console (criterion 3 demands a clean console).
- Base class: `pymol/wizard/__init__.py:29-31` `__getstate__` = `self.__dict__.copy()` with `'cmd'` popped (the ONLY strip); `__init__.py:34-36` `__reduce__` = `(self.__class__, (), self.__getstate__())`.
- **The defect:** `__reduce__` reconstructs by **calling the class with NO args**. `GameWizard.__init__(self, payload, registry, ...)` requires both → unpickling raises `TypeError: __init__() missing 2 required positional arguments: 'payload' and 'registry'` → caught → Session-Warning → **the wizard is silently dropped from the restored session** (`cmd.get_wizard()` is `None`). Observed live in the probe's verify phase (console lines above).

**What does NOT break (probed):** save-side pickling of the live GameWizard is **clean** — direct `pickle.dumps(wiz, 1)` succeeded (`SMOKE-17 A VERDICT wizard-save: ok=True`). The full `GameWizard.__dict__` was enumerated by the probe: `['_color_store', '_current_slot', '_end_state', '_error', '_event_seq', '_game_over', '_last_event', '_level_index', '_ligand_object', '_molecule_index', '_objects_by_slot', '_payload', '_registry', '_result', '_saved_msm', '_slot_by_object', 'cmd', 'menu', 'panel', 'prompt', 'session']` — every attribute is plain data (dicts/lists/ints/strs/None), **no Qt, no locks, no controller refs, no module refs**. Contract 2 (03-03) did its job: there is NOTHING to strip beyond the base class's `cmd` pop. `self.session` (the per-class `wizard_storage` dict from `_validate_instance`) is a plain dict — picklable, harmless.

**The fix (probe-PROVEN through the REAL task path — SMOKE-17 phase-A part C):** give GameWizard an **argless reconstruction** path, e.g. a module-level rebuilder in `aamatch/wizard.py`:

```python
def _rebuild_game_wizard():
    return object.__new__(GameWizard)   # __init__ never runs

class GameWizard(Wizard):
    def __reduce__(self):
        return (_rebuild_game_wizard, (), self.__getstate__())
```

Probe evidence (phase A, part C, monkey-patched in-memory only — production files untouched):

```
SMOKE-17 NOTE base __reduce__ unpickle: TypeError: __init__() missing 2 required positional arguments: 'payload' and 'registry'
SMOKE-17 C REAL-path wizard restore via argless __reduce__ PASS get_wizard()=<...GameWizard object> panel=17 status-eq=True
```

The prototype drove the REAL sequence: `wizarding.session_save_wizard(session, cmd)` → `pickle.loads(session['wizard'])` → `w.cmd = cmd` rebind → `cmd.set_wizard_stack(wizards)` → the restored instance is fully functional (panel 17 entries, `get_status()` equal, `_current_slot`/`_event_seq`/`_color_store`/`_payload['seed']` all equal). No `__getstate__` changes are needed (the inherited one is exactly right); no `__setstate__` is needed (pickle applies the state dict via `__dict__.update` when `__setstate__` is absent). Alternative fix shape (also viable, more invasive): make `__init__` args optional with a registry-less early-exit — the rebuilder is preferred (one function, no `__init__` contract change, and `_validate_instance` bookkeeping is irrelevant because the restored `__dict__` carries `session` from the save-time instance).

**Class/module-identity caveat (gate 5):** pickle stores the class **by reference** (`module.qualname`). The smoke pickles `aamatch.wizard.GameWizard` (repo identity); an installed plugin pickles `pmg_tk.startup.aamatch.wizard.GameWizard`. Save and load must happen under the SAME module identity (AGENTS.md gate 5 — never mix). Cross-identity restore raises inside the unpickle → caught → Session-Warning (console not clean, wizard dropped, scene still fine). Startup plugins (`pmg_tk.startup.*`) are auto-imported at PyMOL launch, so the installed flow resolves before any session load. The rebuilder function reference obeys the same rule. `migrate_session(version)` (`wizard/__init__.py:17-19`) is the versioned hook if the pickled state shape ever evolves.

**Restore auto-arms the wizard:** after the fix, `cmd.load()` of the `.pse` re-installs the GameWizard **active on the stack** with its full plain-data state (`_current_slot`, `_event_seq`, `_last_event`, `_color_store`, `_saved_msm`, `_payload`, `_registry`). `activate()` is NOT re-run (only `cmd` rebind + `migrate_session`), which is correct: the session settings already carry `mouse_selection_mode=0` (saved while the wizard was in play), and `_saved_msm` (the user's pre-game snapshot, e.g. 1) comes back inside the state — the pair is self-consistent and `cleanup()` still restores the user's true value on Done. The status tab's 1 Hz poll reads `get_status()` — a restored wizard immediately renders the resumed game.

---

## Session-restore path (how a loaded `.pse` re-arms the game)

`cmd.load('game.pse')` → `load_pse` (`importing.py:823-830`): `file_read` → `io.pkl.fromString` → `set_session(session, steal=1)` (`importing.py:130-175`) → C-side `_cmd.set_session` restores objects/settings/**view** (get_session with `partial=0` stores view+settings+movie per its docstring), then `_pymol.session = session['session']` (deepcopy/steal of Python-side storage), then the `_session_restore_tasks` run **after** the C restore — errors never abort the load (each task's failure is collected; only `session_restore_views`-style falsy returns raise at the very end, and the wizard task swallows its own exceptions):

1. `viewing.session_restore_views` (`viewing.py:1146-1150`) — named-view dict (`_view_dict`); the CURRENT camera rides the C-side blob (probe: bit-exact).
2. `viewing.session_restore_scenes` — scenes.
3. `wizarding.session_restore_wizard` (`wizarding.py:182-196`) — the wizard stack (see above).

**What Phase 7 must do on top (sentinel-first reconstruction, Strategy A):** the `.pse` restores the SCENE; the sidecar restores the GAME:

1. Read sidecar (kind=`checkpoint`, same basename as the `.pse`) via `persistence.load_container` — refusal classes free (foreign/newer/misfiled/unparseable → FormatError with clear message).
2. Sentinel-first: rebuild the registry from the LOADED atoms (source of truth = the clickable atoms): per object, `cmd.count_atoms('<obj> and segi AAM and b < 0')` (probe-proven working post-load) and the sorted `(object, id)` id list; reconcile against the sidecar's registry rows by `(object, id)`; a sidecar ghost referencing a non-existent atom degrades gracefully (sidecar-missing → playable-but-metadata-less is the prior-art rule).
3. Rebuild the engine: `engine._payload/_registry/_game/_ligand_content` are all None after load (probe-proven) — a new engine seam (e.g. `engine.restore_game(payload, registry, game_state_dict, ligand_content)`) must set them; `GameState.from_dict` is proven lossless and is the checkpoint core. `gamestart._last_start` must be restored too (Restart replay) — it is derivable from the sidecar's setup/seed/candidates/ligand_content.
4. The pickled wizard (after the fix) auto-resumes; the reconstructed registry must EQUAL the wizard's pickled `_registry` (both derive from the same materialize output — assert-equal in the gate smoke).
5. **Timer semantics decision for the planner:** `timer_anchor` is an absolute wall-clock float. Restoring it verbatim means elapsed time KEEPS RUNNING across the closed period (now − anchor includes the app-closed time). To freeze at the save moment instead: store `elapsed_at_save = now − anchor` in the sidecar and call the existing `GameState.rebase_timer(now_at_load, elapsed_at_save)` on restore (the P-4 single-clock primitive, `game_state.py:212-243`). Recommend the rebase (a checkpoint should resume where the player left off); decide and record in the plan.
6. **Where checkpoint files live:** `paths.py` has only `to_windows_path` + `package_data_path` — no checkpoint-dir convention exists yet. The probe used `tmp/smoke fixtures/` (git-ignored, dev-only). Product shape: user-chosen via the Game status tab (modal `QFileDialog` — pause the timer around it per the UX pitfall; capture the GameState BEFORE opening the dialog per ROADMAP's research note), sidecar at `<pse-basename>.json` next to the `.pse`, both routed through `to_windows_path`. No absolute paths may be embedded in the sidecar except package-relative synthetic keys (`uploads/mol-001.sdf`-style — already path-safe by design in `game_file.py`).

**Console cleanliness:** save-half is clean TODAY (probe: no warnings during `cmd.save` with the wizard live). Load-half prints the Session-Warning until the `__reduce__` fix lands; after the fix, expect zero plugin-caused console output during save/load (PyMOL's own `Save: Please wait` line excepted).

---

## Gate-1 smoke design (the standing gate, now frozen)

**Script:** `smoke/smoke_17_pse_roundtrip.py` (committed; SMOKE-17 was the first unused number — smokes 01–16 existed).
**Runner contract:** `bash smoke/run_smoke.sh smoke/smoke_17_pse_roundtrip.py 240` — run TWICE (two independent Windows PyMOL processes = the quit→relaunch half). The runner greps `=== SMOKE-17 PASS ===` per run.

- **Run 1 (SAVE; runs when the fixture `.pse` is absent):** start_game(seed 42, wizard ACTIVE) → scripted pick → `move_to` + `rotate_axis` (baked moves, identity invariant asserted) → `_aam_17probe` non-identity-matrix object → snapshot EVERY data class into `game.snapshot.json` via `persistence.save_container(kind='checkpoint')` → `cmd.save()` with the wizard on the stack → assert save succeeded and the stack is undisturbed → in-memory fix prototype (part C) proving the argless-`__reduce__` restore through the real task functions → teardown.
- **Run 2 (VERIFY; runs when the fixture exists):** assert fresh-process state (`engine._game is None`, empty scene) → `cmd.load()` → re-extract and compare: object names, per-`(object,id)` coordinates (tolerance ≤ 1e-6, EXPECT exact), segi/b sentinels, colors, reps, view (≤ 1e-6, EXPECT exact), per-object matrices, probe matrix + probe stored coords → wizard restore observation → sentinel-first reconciliation counts → `GameState.from_dict` lossless → engine-stays-dead → delete fixtures → PASS.
- **Verdict format (recorded in the phase docs):** `SMOKE-17 VERDICT <class>: <metric> -> PROVEN|REFUTED` lines for coords / view / matrix-probe / wizard, plus the final `=== SMOKE-17 PASS ===` marker. Current recorded result: **coords PROVEN exact; view PROVEN exact; matrices PROVEN exact; wizard save-side clean + restore defect documented (fix prototype PROVEN)**.
- **Phase-7 plan note:** the phase's own gate smoke should keep this two-run shape and FLIP the phase-B wizard check from the "documented defect signature" pin to the strict restore compare (restored instance + state equality) once `aamatch/wizard.py` carries the rebuilder. The identity-invariant assert (`_assert_identity` on every recolored slot object) should also run post-load in the plan's smoke (the probe asserted it pre-save only).

---

## Fallback design (sidecar matrices) — NOT needed for v1, documented for completeness

The probe PROVED matrices round-trip, so per-object sidecar matrices are **not required** for the movement model. The fallback exists for one scenario only: a future PyMOL version changing `.pse` object-matrix serialization, or a corrupt/partial session. Shape (mirrors what the probe recorded):

```json
"object_matrices": {
  "<object_name>": [m00, m01, m02, m03,   // row-major 4x4, the EXACT
                    m10, ..., m13,        // cmd.get_object_matrix values
                    ... m33]
}
```

- Read side: `cmd.get_object_matrix(name)` → 16-float row-major (normalize 12-value blocks by appending `[0,0,0,1]` — the `wizard._matrix16` pattern).
- Apply side on reconstruction: `placement.transform_baked(name, m16)` → `cmd.transform_object(name, M, homogenous=1)` (the probe-verified bake; note transform_object BAKES coordinates AND records the matrix — probe-proven: the probe atom's stored coord moved by exactly the Rz30 bake, 8.34 Å, while the matrix also survived — so a fallback apply must run BEFORE sentinel reconciliation reads coordinates, or coordinates and matrix disagree).
- Verdict rule for the plan: if a future re-run of SMOKE-17 shows non-zero matrix deltas, the sidecar carries `object_matrices` and reconstruction applies them; until then the field is simply absent (`.get` default `None` → skip) — additive-only evolution per the container discipline.

---

## Sources & confidence

### Primary (HIGH — probe + source on disk)

- **SMOKE-17 probe (this repo, run 2026-09-21):** `smoke/smoke_17_pse_roundtrip.py`, commands and verbatim output above; two-process round-trip on PyMOL 2.5.0 / Python 3.9.13 (the frozen Windows env). All "survives" rows and the wizard defect are probe-observed, not inferred.
- **PyMOL 2.5.0 source** (`/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/bioCHEMeleon/tmp/pymol-src/modules/pymol/` — the same 2.5.0 source line, cited by file:line):
  - `wizarding.py:176-180` session_save_wizard (double-pickle, protocol 1); `wizarding.py:182-196` session_restore_wizard (cmd rebind, migrate_session, set_wizard_stack, swallow+warn).
  - `wizard/__init__.py:29-31` `__getstate__` (pops only `cmd`); `:34-36` `__reduce__` = `(self.__class__, (), self.__getstate__())` — the constructor-arg defect root; `:17-19` `migrate_session` hook.
  - `cmd.py:40-53` session task registration (views/scenes/wizard save+restore).
  - `importing.py:823-830` `load_pse` → `set_session(steal=1)`; `importing.py:130-175` `set_session` (C restore, `session['session']` storage, restore-task loop).
  - `exporting.py:370-424,455-475,424` `get_session` (partial=0 stores view/settings/movie; `session['session']` deepcopy; session_compression deprecated → `.pze`/`.pse.gz`); `exporting.py:782+` `cmd.save` (format guess, `session_file` setting, `.pse` branch).
  - `viewing.py:1141-1150` session_save/restore_views (named-view dict only).
- **Repo facts (read directly):** `aamatch/wizard.py` (contract 2 plain-data attrs; `_matrix16`/`_assert_identity`; movement contracts), `aamatch/game_state.py:206-266` (timer anchor/rebase/stop), `:411-454` (`to_dict`/`from_dict` lossless), `aamatch/placement.py:97-99,151-158` (sentinel constants + tagging), `:190-231` (`translate_to`, `transform_baked`), `aamatch/persistence.py` (container + atomic I/O), `aamatch/paths.py` (`to_windows_path` guard), `aamatch/engine.py:129-140` (module globals), `aamatch/gamestart.py:184` (`_last_start`), `aamatch/game_file.py` (game container + path-safe synthetic keys), `smoke/run_smoke.sh` (runner contract), `smoke/smoke_08_starter.py` (start_game recipe), `.planning/STATE.md:290,305` (standing gate), `.planning/ROADMAP.md:185-197` (Phase 7 criteria), `.planning/research/PITFALLS.md` Pitfall 2/10.

### Secondary (MEDIUM)

- Pickle class-by-reference semantics + state application via `__dict__.update` when `__setstate__` is absent: standard Python pickle behavior (docs knowledge), **indirectly verified** by the probe — the observed TypeError is exactly the by-reference-construction failure, and part C's rebuilder + state dict restore produced a working instance through the real task path.

### [UNVERIFIED — needs the plan's smoke or a human check]

1. **Bond/connectivity equality across `.pse`** — not separately diffed (atom set identical implies it, and the detector consumed the loaded geometry in the reconciliation counts); if the plan wants belt-and-braces, add a `get_bonds` count compare to the Phase-7 gate smoke (SMOKE-02 already has the bond-compare pattern).
2. **Installed-identity pickle round-trip** (`pmg_tk.startup.aamatch.wizard.GameWizard` saved by an installed plugin, restored after relaunch) — inferred safe because startup plugins auto-import at launch and the mechanism is identity-symmetric, but the probe ran under the repo identity only; the Phase-7 human checkpoint (install → save → relaunch → load) covers it.
3. **Timer-resume semantics choice** (keep-running vs rebase-freeze) — a planner/human decision, not a fact; both are mechanically supported (`timer_anchor` restore vs `rebase_timer(now, elapsed_at_save)`).
4. **Object visibility/enabled flag and object-level color** round-trip — not probed (per-atom color was); low risk (standard session state), add an assert to the plan's smoke if the restored look matters.

**Explicitly out of scope for this research (per the gate wording):** the Import button UX (Phase 7 plan), game-file container changes (none needed — `game_file.py` already carries the payload verbatim), and any production code change (the `__reduce__` fix is specified here, implemented by the plan).
