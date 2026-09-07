# Phase 3: Wizard Gameplay Loop — Wizard/Viewer-Interaction Research

**Researched:** 2026-09-08
**Domain:** PyMOL 2.5.0 wizard event contract, panel mechanics, pick routing, environment save/restore
**Confidence:** HIGH (every claim below is cited `file:line` from the local PyMOL 2.5.0 source tree at `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/bioCHEMeleon/tmp/pymol-src/` — both Python modules AND C++ layers were read; prior-art claims cite `tmp/bioCHEMeleon/biochemeleon/*.py`. Explicit UNVERIFIED items listed in §10.)

---

## 1. Summary — the 10 planning-critical facts

1. **`cmd.set_wizard()` accepts ANY wizard *instance* — proven three ways.** The Python wrapper forwards the object verbatim to the C layer (`wizarding.py:110-118`); shipped `pmg_qt/builder.py:51-58` installs `self` (a Qt-builder wizard) with `cmd.set_wizard(self, replace=1)`; the C side (`Wizard.cpp:263-284`) pushes *any* PyObject and calls its methods dynamically via `PyObject_HasAttrString` (`Wizard.cpp:161-165`). The `pymol.wizard.<Name>` string lookup (`wizarding.py:30-60`) is ONLY for the `cmd.wizard("name")` launcher. **A custom wizard needs no registration anywhere.**

2. **NEW FINDING — the v1 saved-wizard pattern leaks the stack; the stack-native pattern is strictly better.** C `WizardSet` (`Wizard.cpp:263-284`) pops + calls `cleanup()` on the current wizard ONLY when the new wizard is None OR `replace=1`; otherwise it **pushes on top without cleanup**. v1's `deactivate()` does `cmd.set_wizard(self._saved_wizard)` with default `replace=0` (`tmp/bioCHEMeleon/biochemeleon/wizard.py:91`) — when a prior wizard W0 exists this pushes a *second* W0 reference while the game wizard stays buried on the stack (duplicate entries, double-cleanup later). **Recommended AA-match pattern:** activate = `cmd.set_wizard(self)` (push; prior wizard stays beneath, dormant); deactivate/Done = `cmd.set_wizard()` (None) which pops the game wizard, runs ITS `cleanup()` (restores `mouse_selection_mode` etc.), and the prior wizard **automatically resumes** as the new top (`WizardGet` = `Wiz.back()`, `Wizard.cpp:786`). One mechanism, no saved-wizard juggling, provably correct from the C source.

3. **Click routing (Pitfall 5, now verified in the C layer).** Default 3-Button Viewing left-click = `cButModeSeleSet` → the C layer builds the active selection (typically `"sele"`) and calls `WizardDoSelect(G, selName, state)` → Python `do_select(name)` (`SceneMouse.cpp:337-356`, call at `:356`; `Wizard.cpp:171-190`). Picking button modes (`Pk1`/`PkAt`) build `pk1` and call `WizardDoPick` → `do_pick(bondFlag)` (`SceneMouse.cpp:403-467`; `Wizard.cpp:302-325`). **`do_pick` never fires in stock Viewing mode** — the canonical do_select→do_pick map (`wizard/measurement.py:295-306`) is mandatory. Clicking **empty space fires NO wizard event at all** (`SceneClickPickNothing`, `SceneMouse.cpp:557-574` just empties the selection).

4. **Panel entries are ALWAYS 3-element lists `[kind, text, code]`.** The C parser requires `PyList_Size(i) > 2` per entry (`Wizard.cpp:239-246`) — a 2-element `[1, 'text']` renders as a **blank line** (falls through with `type=0`). Kinds: 0=blank, 1=text line, 2=button, 3=popup menu (`Wizard.cpp:43-46`). Button `code` strings are parsed via `PParse` on mouse release (`Wizard.cpp:569-576`) — deferred evaluation; popup `code` is a menu tag resolved via `get_menu(tag)` → `PopUpNew` (`Wizard.cpp:494-509`). Panel text is truncated at **255 chars** per line (`WordType[256]`, `Word.h:24,26`); `get_prompt()` returns a **list of strings** with no line-count/length cap (`PConv.cpp:1127-1156`, stored via `OrthoSetWizardPrompt`, `Ortho.cpp:305-310`).

5. **`cmd.get_wizard().method()` panel commands fully dodge the module-identity trap.** The command string is evaluated at CLICK time against the live top-of-stack instance — it references no module name at all. `aamatch/wizard.py` should import the engine RELATIVELY (`from . import engine` inside methods), so the module works identically as `aamatch` (smokes/plugin-path) and `pmg_tk.startup.aamatch` (installed). AGENTS.md gate 5 honored by construction.

6. **PLAY-01 visual feedback: recolor the picked AA object; it is detection-safe.** `extract_game_atoms` reads only `(model, ID, name, elem, resn, resv, alt, formal_charge, x, y, z)` (`aamatch/geometry.py:134-138`) — atom `color` is never read, so recoloring cannot corrupt detection. Snapshot per-atom colors with `cmd.iterate(obj, ... color ...)` (`color` is in the symbol table, `editing.py:1448`) and restore with `cmd.alter`; v1's shipped recolor precedent is `cmd.color('green', ...)` on found (`game.py:208-213`). Recolor = property change, NOT geometry → PLAY-04's no-helper-visuals gate is satisfied (no lines/dots/CGO).

7. **Object model for pick identity (pinned from placement.py): ONE `_aam_aa*` object PER SLOT.** `materialize` creates each slot via `cmd.get_unused_name('_aam_aa')` + `cmd.fragment` (`placement.py:328-329`) and registers `slot_id -> (object_name, sorted ids)` (`placement.py:348`). Therefore the click's **object name alone resolves the slot** (build a reverse `{object_name: slot_id}` map when the wizard activates). First object is literally `_aam_aa`, subsequent get numeric suffixes — prefix-match `'_aam_aa'` cleanly separates from `_aam_lig*`.

8. **Keyboard channel: `do_special` owns LEFT/RIGHT cleanly; UP/DOWN are NOT suppressible.** Dispatch order verified: `PyMOL_Special` tries `WizardDoSpecial` FIRST (`PyMOL.cpp:2318`), then UP/DOWN are **unconditionally** forwarded to `OrthoSpecial` (= command-line history navigation, NOT camera — `Ortho.cpp:323-340`), and LEFT/RIGHT only reach `OrthoSpecial` while the user is typing in the command line (`OrthoArrowsGrabbed`, `Ortho.cpp:396-401`; `PyMOL.cpp:2326-2332`); un-consumed keys fall to the `_special` set_key dispatcher (`PyMOL.cpp:2336-2341`, `internal.py:447-484`). Qt GUI forwards keys via `PyMOLQtGUI.keyPressEvent` → `pymol.button(...)` (`pymol_qt_gui.py:50-54`; arrows map to codes 100-103 in `pmg_qt/keymapping.py:19-41`). `do_key` (ASCII) is wizard-first too (`PyMOL.cpp:2302-2308`) and returning `1` consumes (`command.py:166-178`). **Arrow-key nudge is feasible via `do_special` for LEFT/RIGHT; avoid UP/DOWN as game keys.**

9. **`mouse_selection_mode` stock default is 1 (residue), NOT 0.** `SettingInfo.h:449: REC_i(354, mouse_selection_mode, global, 1)`. The wizard must save/restore whatever the user had (user can cycle it 0-6 via `cmd.mouse` select ring, `controlling.py:639-648`) and set atomic 0 defensively like every built-in wizard (`measurement.py:96-97` save+set, `:212` restore in `cleanup`; same pattern in `distance.py:69-70/104`, `pair_fit.py:24-25/40`, `appearance.py:68-69/225`). Since each slot IS one object = one residue, residue-mode clicks would also land, but atomic mode guarantees a single-atom selection → single-object read.

10. **PLAY-04 restore set is small and fully enumerable** (§7 table): prior wizard (stack-native), `mouse_selection_mode`, `pk1`/`sele` leftovers, recolored AA atoms, plus any setting the wizard itself flips. Panel state self-clears on wizard removal (`WizardSet` → `WizardRefresh` with no wizard → `OrthoReshapeWizard(G,0)`, `Wizard.cpp:253-258`).

**Primary recommendation:** Build `aamatch/wizard.py` as a thin input adapter (Pattern 2) — a `pymol.wizard.Wizard` subclass holding ONLY plain picklable data; `do_select`→`do_pick` canonical map reading `(model, ID, alt, resv)` from `pk1`; object-name→slot_id reverse-map lookup; explicit recolor with color snapshot/restore; stack-native activate/deactivate; panel with `[1,...]` status lines + `[2,...]` buttons (`Confirm`/`Reset`/`Done`) and the result rendered as prompt + text lines. All of it is headless-testable by calling `do_select`/`do_pick` directly; the live-mouse loop is the human checkpoint.

---

## 2. Wizard lifecycle contract (Q1)

### 2.1 Base class overridables — `pymol/wizard/__init__.py` (full file, 95 lines)

| Member | Line | Contract |
|---|---|---|
| `event_mask_pick/select/key/special/scene/state/frame/dirty/view/position` | 6-15 | Bits 1,2,4,8,16,32,64,128,256,512. C-side constants match exactly (`Wizard.cpp:48-57`). |
| `migrate_session(version)` | 17-20 | Session-restore hook; default no-op. |
| `__init__(_self=cmd)` | 22-27 | Sets `self.menu={}`, `self.prompt=None`, `self.panel=None`, `self.cmd=_self`; calls `_validate_instance()` (per-class session storage dict, `:38-47`). |
| `__getstate__` / `__reduce__` | 29-36 | `__getstate__` copies `__dict__` and **pops `'cmd'`** — the only automatic stripping. Everything else on `self` must be picklable (session save pickles the whole stack, `wizarding.py:176-180`). |
| `get_prompt()` | 49-50 | Returns `self.prompt` (None or list of strings). |
| `get_panel()` | 52-53 | Returns `self.panel` (list of 3-element entries) — or None for no panel. |
| `get_event_mask()` | 55-56 | **Default = pick + select** (bits 3). C fallback is the same (`Wizard.cpp:217,222`). |
| `do_scene/do_view/do_position/do_state/do_frame/do_dirty` | 58-74 | Optional event hooks, each gated by its mask bit (`Wizard.cpp:343-458`). |
| `do_pick(bondFlag)` | 76-77 | Picking-mode entry; `bondFlag` 0=atom, 1=bond (`SceneMouse.cpp:317-320` logs the call). |
| `do_select(name)` | 79-80 | Selection-mode entry; `name` = active selection name string (see §5.1). |
| `do_key(k,x,y,mod)` / `do_special(k,x,y,mod)` | 82-86 | Keyboard entries (see §6). |
| `cleanup()` | 88-89 | Called by the C layer when the wizard is popped/replaced (see 2.3). **This is where PLAY-04 restores happen.** |
| `get_menu(tag)` | 91-95 | Returns `self.menu[tag]` for popup kinds. |

### 2.2 Install / query / refresh

- `cmd.set_wizard(wizard=None, replace=0)` — `wizarding.py:110-118`: passes the object straight to `_cmd.set_wizard(_self._COb, wizard, replace)`. Any instance works.
- `cmd.get_wizard()` — `wizarding.py:156-164`: returns the top-of-stack instance (`WizardGet` = `Wiz.back()`, `Wizard.cpp:783-787`) or None.
- `cmd.refresh_wizard()` — `wizarding.py:130-144`: re-pulls `get_prompt` + `get_event_mask` + `get_panel` from the current wizard and re-renders (`WizardRefresh`, `Wizard.cpp:194-259`). Also called automatically after every `set_wizard` (`Wizard.cpp:282`) and when the C `Dirty` flag fires in `WizardUpdate` (`Wizard.cpp:100-131`). **Rule: call `cmd.refresh_wizard()` after any state change that should re-render the panel/prompt** (v1 `wizard.py:67`; measurement uses it throughout, e.g. `measurement.py:279,290`).
- String-based launcher `cmd.wizard("name")` → `pymol.wizard.<Name>` import + `name.capitalize()` class — `wizarding.py:30-60`. NOT needed for custom wizards.

### 2.3 Stack semantics — `Wizard.cpp:263-284` (THE critical mechanics)

```c
pymol::Result<> WizardSet(PyMOLGlobals * G, PyObject * wiz, bool replace)
{
  if ((!wiz) || (wiz == Py_None) || (!I->Wiz.empty() && replace)) {
    if (!I->Wiz.empty()) {                 // pop ONE wizard...
      auto old_wiz = std::move(I->Wiz.back());
      I->Wiz.pop_back();
      if (old_wiz) { WizardCallPython(G, old_wiz.get(), "cleanup", ...); }  // ...and run ITS cleanup
    }
  }
  if (wiz && (wiz != Py_None)) { I->Wiz.emplace_back(PIncRef(wiz)); }        // push new on top
  WizardRefresh(G);
}
```

Consequences (all load-bearing for the plan):

| Call | Stack before | Action | Stack after |
|---|---|---|---|
| `set_wizard(game)` (replace=0), empty stack | `[]` | push | `[game]` |
| `set_wizard(game)` (replace=0), prior W0 active | `[W0]` | push (W0 NOT cleaned, stays dormant beneath) | `[W0, game]` |
| `set_wizard()` (None) | `[W0, game]` | pop+`game.cleanup()`, no push | `[W0]` → **W0 auto-resumes** |
| `set_wizard(wiz, replace=1)` | `[...]` | pop+cleanup top, push wiz | e.g. `[wiz]` |
| Done buttons of all built-ins (`cmd.set_wizard()`) | any | pop+cleanup top | prior resumes |

- Event dispatch only ever touches the **top** of the stack (`WizardGet` at every `WizardDo*` entry, `Wizard.cpp:179,202,313,333,350,368,398,414,430,468,497,571`).
- **v1's `deactivate()` = `cmd.set_wizard(self._saved_wizard)` (replace=0) is defective when a prior wizard exists**: it pushes a duplicate W0 on top of `[W0, game]` → `[W0, game, W0]`; the game wizard leaks beneath and a later `set_wizard(None)` cleans W0 *twice*. With an empty prior stack (the common case) it degenerates to the correct stack-native behavior. **AA-match should use the stack-native pattern** (activate `cmd.set_wizard(self)`, exit `cmd.set_wizard()`); the prior wizard is then restored by the stack itself and PLAY-04's "prior wizard restored" holds structurally.
- Plugin **reload** while a wizard is active: the C stack keeps the OLD instance by reference; nothing automatic fires. The next `set_wizard(new, replace=1)` (new game start) pops + cleans the old instance — its `cleanup()` still works (bound methods use `self.cmd`). Module-identity caveat: old instance + new module coexist harmlessly because panel commands use `cmd.get_wizard()...` (instance-relative).
- **Session load**: `session_restore_wizard` (`wizarding.py:182-196`) unpickles the stack, rebinds `wiz.cmd`, calls `wiz.migrate_session(version)`, reinstalls. If the plugin module is not importable, PyMOL prints `Session-Warning: unable to restore wizard.` and continues (`:193-195`). Session save pickles the stack — "double-pickle so that session file is class-independent" (`wizarding.py:176-180`). **Phase-3 discipline (costs nothing, saves Phase 7): hold only plain data on the wizard; never store module references** (pickling a module raises TypeError).

### 2.4 What `cleanup()` MUST do for PLAY-04

`cleanup()` runs exactly when the game wizard is popped (Done button `cmd.set_wizard()`) or replaced (`replace=1`). Its mandatory restores (each evidenced in §7): `mouse_selection_mode` back to the snapshot; `pk1` deleted + unpicked; stale `sele` handled; recolored AA atoms restored from the color snapshot. It must be idempotent-safe (built-in wizards' cleanups are plain restores; `measurement.py:205-212` is the template).

---

## 3. Panel mechanics + detection-result display design (Q2)

### 3.1 Entry format (exact, C-verified)

Every entry = list of **≥3 elements** `[kind, text, code]` (`Wizard.cpp:239-246`: only entries with `PyList_Size(i) > 2` are parsed; shorter entries render blank):

| kind | C name | Behavior | Evidence |
|---|---|---|---|
| 0 | `cWizBlank` | blank line | `Wizard.cpp:43`; default `type=0` |
| 1 | `cWizTypeText` | static text line, overlay-colored | `Wizard.cpp:44`, drawn at `:751-754` |
| 2 | `cWizTypeButton` | button; `code` executed via `PParse` on release | `Wizard.cpp:45`, `:569-576` |
| 3 | `cWizTypePopUp` | menu button; `code` = tag → `get_menu(tag)` → `PopUpNew` | `Wizard.cpp:46`, `:494-509` |

Canonical examples: `measurement.py:195-203` (`[1,'Measurement','']`, `[3, label, 'mode']`, `[2,'Done','cmd.set_wizard()']`); menus = `[2,'header','']` + `[1,'item','cmd.get_wizard().set_mode("x")']` (`mutagenesis.py:180-209`, `measurement.py:77-94`).

- Text limit: 255 chars/panel line (`WordType[256]`, `Word.h:24,26`; `PConvPyObjectToStrMaxLen` at `Wizard.cpp:242-245`).
- Prompt: `get_prompt()` returns a **list of strings** — each element is one prompt line, unlimited count/length (`PConvPyListToStringVLA` joins them as a NUL-separated VLA, `PConv.cpp:1127-1156`; stored `Ortho.cpp:305-310`). Color escapes work inside prompt strings (`command.py:146-147` uses `\999` / `\990`).
- Every built-in "Done" button is exactly `'cmd.set_wizard()'` — the exit primitive.

### 3.2 Why `cmd.get_wizard().method()` commands dodge the module-identity trap

The `code` string is stored as text and **parsed only at click time** (`PParse`, `Wizard.cpp:569-576`). `cmd.get_wizard()` resolves the live top-of-stack instance then — regardless of whether the plugin module is `aamatch` (plugin-path/smoke) or `pmg_tk.startup.aamatch` (copy-installed). No module name ever appears in a panel command. Same discipline for menu items.

### 3.3 Detection-result rendering recommendation (Phase 3, no Qt)

v1's post-pick/confirm feedback was **text**: `on_log("Found one! %d remaining")` / `on_log("Miss!")` (`game.py:170-188`), rendered in its Qt log widget. AA-match Phase 3 (pre-Qt) renders the same shape in the wizard surface:

- **Prompt** (always-visible status, `get_prompt`): state machine line — "Click an amino acid to select it." → "Selected: SER slot-5 (object _aam_aa003). Move/rotate it, then Confirm." → after confirm: "Result: 2/3 required interactions formed." plus error lines appended (measurement appends `self.error`, `measurement.py:262-263`).
- **Panel text lines** `[1, ..., '']`: current molecule header, the formed/missing interaction list (7 types max — fits trivially under the 255-char/line cap), score fraction.
- **Buttons** `[2, ..., 'cmd.get_wizard().x()']`: `Confirm`, `Reset to Grid`, `Skip` (partial-score path, per project scoring decision), `Done`.
- **No result geometry**: formed interactions are NOT drawn (PLAY-04). The result exists as text + the detector's plain-data return. (Carbon recolor for Hint is PLAY-05, later phase.)

The result payload comes from `engine.confirm(level_index, molecule_index, required)` → `(records, score, formed_types)` (`engine.py:299-305`), where `required = payload['levels'][i]['molecules'][j]['required']` — a `{'mode': 'any'|'list', 'items': [{'type','count'}]}` dict (`level_spec.py:25-26`).

---

## 4. Selection visual feedback design (Q3, PLAY-01)

**What stock PyMOL natively does:** a SeleSet click creates/shows the active selection — `auto_show_selections` default **1** (`SettingInfo.h:162`) — so native pink selection indicators DO appear on click. But the canonical wizard pattern **deletes** that selection each pick (`measurement.py:299`; v1 `wizard.py:83`), which removes the native indication. v1's own visual answer was **recolor**: `cmd.color('green', ...)` on found (`game.py:208-213`), nothing on miss.

**Recommended mechanism (recolor + status text):**

1. On pick of a registered slot: `cmd.color(HIGHLIGHT, aa_object)` (whole object — it IS one residue/fragment).
2. Before the FIRST recolor, snapshot every game AA's atom colors: `cmd.iterate(obj, "stored.append((ID, color))", space={'stored': rows})` — `color` is a read/write atom property in the iterate/alter symbol table (`editing.py:1444-1449`).
3. On switching selection: restore previous slot's colors from the snapshot, recolor the new slot. On `cleanup()`: restore all recolored slots.
4. "Selected status" = the wizard prompt/panel text (§3.3) + optionally the unpicked-but-live selection. Keeping `sele`/`pk1` alive is NOT needed and is explicitly cleaned in the canonical pattern; rely on recolor + text (also the least ambiguous vs. the "no helper visuals" gate).

**Safety properties (all verified):**
- Recolor cannot corrupt detection — `extract_game_atoms` never reads `color` (`geometry.py:134-138`).
- Recolor introduces no lines/dots/CGO geometry (PLAY-04).
- Snapshot/restore is property-only; ids, coords, segi/b sentinels untouched.
- Anti-pattern to avoid: indicating selection with `cmd.indicate` or enabled selections left behind — they are display noise the next click/selection will fight with (`auto_hide_selections` default 1 hides others when a new selection is created, `SettingInfo.h:163`).

**Edge:** if the player manually recolors an AA mid-game, our restore overwrites their change — acceptable; note in plan.

---

## 5. Pick identity → slot_id mapping (Q4)

### 5.1 What each entry point hands the wizard (C-verified)

- `do_select(name)`: `name` = the **active selection name** the C layer just built — `ExecutiveGetActiveSeleName(G, selName, true, ...)` at `SceneMouse.cpp:258-261`, passed to `WizardDoSelect(G, selName.c_str(), state)` at `:356`. In practice `"sele"`; if the user has a *named* selection active, clicks modify that one instead (then the canonical `cmd.delete(name)` would delete the user's selection — the measurement wizard has shipped this behavior for ~20 years; AA-match may optionally guard by only deleting transient names, but matching the canonical pattern is defensible. Decision for the planner; note the caveat).
- `do_pick(bondFlag)`: fires only in Pk1/PkAt button modes after the C layer built `pk1` (`SceneMouse.cpp:403-467`); `bondFlag` 0=atom/1=bond. Our do_select map manufactures the same state: `cmd.unpick(); cmd.select("pk1", name); cmd.delete(name); self.do_pick(0)` (canonical: `measurement.py:295-306`; v1: `wizard.py:81-84`).
- Empty-space clicks: `SceneClickPickNothing` (`SceneMouse.cpp:557-574`) — **no wizard callback at all**.

### 5.2 Reading the pick (hygienic, Pitfall-8-conformant)

```python
props = []
cmd.iterate("pk1", "stored.append((model, ID, alt, resv))", space={'stored': props})
cmd.unpick()
```
(v1 `wizard.py:56-62`; `ID` uppercase — `editing.py:1444-1449`; explicit `space` dict — never None; `cmd.identify` alone rejected — no `alt`, `querying.py` per Pitfall 8.)

### 5.3 The actual Phase-2 object model the wizard will see (`aamatch/placement.py`)

- **ONE object PER SLOT**: `aa_name = cmd.get_unused_name('_aam_aa')` + `cmd.fragment(...)` per slot (`placement.py:328-329`). Names: `_aam_aa`, then `_aam_aa001`, `_aam_aa002`, … (get_unused_name suffixing). No grid-copy-vs-reference sharing — every slot is a distinct object; `(object, id)` identity is unambiguous *across slots*.
- Registry shape returned by `materialize` (`placement.py:241-249, 348`): `{'level_index', 'pre_game_names', 'molecules': [{'molecule_id', 'offset', 'ligand': (obj, ids), 'slots': {slot_id: (object_name, sorted ids)}}]}`.
- Engine holds it module-side (`engine.py:74-77, 221-231`); `engine.place_aa(slot_id, position)` translates the registered object (`engine.py:234-251`).

**Recommended mapping code (wizard-side):**

```python
# at wizard activation — reverse map, plain data, picklable
self._slot_by_object = {}
for mol in registry['molecules']:
    for slot_id, (obj_name, _ids) in mol['slots'].items():
        self._slot_by_object[obj_name] = slot_id

# in do_pick, after the hygienic read:
model, aid, alt, resv = props[0]
slot_id = self._slot_by_object.get(model)     # object name alone resolves the slot
if slot_id is None:
    return                                    # clicked ligand / user object: no-op (v1 game.py:169-171 precedent)
```

- Keep reading/carrying `(model, ID, alt, resv)` anyway: `alt` matters for LIGAND-side clicks (shipped ligands may carry altlocs; they resolve to no-op here) and the uniform tuple keeps Pitfall-8 discipline intact for later phases.
- The AA click does not need `alt`/`resv` for identity (fragments carry no altlocs), but the tuple costs nothing and future-proofs.
- Guard: `model.startswith('_aam_aa')` is implied by the reverse map (only registered names are in it) — no string-prefix logic needed at pick time; the registry IS the filter.

### 5.4 Multiple molecules per level

`materialize` builds one `slots` dict **per molecule** (`placement.py:275-361`); all molecules of the level materialize into the scene simultaneously. The reverse map therefore spans molecules; `slot_id` uniqueness is per-level global (generator numbers molecules `mol-001..`, slots within). The wizard tracks the CURRENT molecule index; clicks on other molecules' AAs are either refused or switch the current molecule (planner decision; per-level molecule advance is Phase 6's lifecycle — Phase 3 can scope to molecule 0 of each level or treat all slots as clickable with the current molecule's Confirm). Engine API takes `molecule_index` explicitly (`engine.py:281,299`).

---

## 6. Keyboard channel feasibility (Q5)

### 6.1 Dispatch order (C-verified)

- **ASCII keys**: `PyMOL_Key` → `WizardDoKey` first; if it returns false → `OrthoKey` (normal shortcut/command-line handling) (`PyMOL.cpp:2302-2308`).
- **Special keys**: `PyMOL_Special` → `WizardDoSpecial` first (`PyMOL.cpp:2318`); then:
  - UP/DOWN (`P_GLUT_KEY_UP/DOWN`): **unconditionally** forwarded to `OrthoSpecial` regardless of wizard consumption (`PyMOL.cpp:2321-2325`) — and `OrthoSpecial` UP/DOWN = **command-line history navigation**, not camera (`Ortho.cpp:323-340`). UP/DOWN are NOT cleanly ownable.
  - LEFT/RIGHT: forwarded only `if (OrthoArrowsGrabbed(G))` (`PyMOL.cpp:2326-2332`) — true only while the user is actively typing in the command line (`Ortho.cpp:396-401`: `CurChar > PromptChar && text visible`). If the wizard's `do_special` returned 1, un-grabbed LEFT/RIGHT are fully consumed — the `_special` set_key dispatcher never runs (`PyMOL.cpp:2336-2341`).
- Wizard must advertise the mask: `event_mask_key` (4) and/or `event_mask_special` (8) in `get_event_mask()` (`wizard/__init__.py:8-9`; `Wizard.cpp:330,465` gate on the bits; precedents `command.py:149-152`, `box.py:400-403`).
- Qt GUI delivers the events: `PyMOLQtGUI.keyPressEvent` → `keyPressEventToPyMOLButtonArgs` → `pymolwidget.pymol.button(...)` (`pymol_qt_gui.py:50-54`); arrows → special codes 100/101/102/103 (`pmg_qt/keymapping.py:19-41`; same codes `internal.py:414-417`).

### 6.2 Contracts

- `do_key(k, x, y, mod)`: `k` = ASCII code (printables 32-126; Backspace 8, Delete 127, Enter 13/10, Esc 27 — `command.py:166-178`). Return `1` to consume; return None/0 to fall through (`command.py:178`, `box.py:438` both end with `return 1`).
- `do_special(k, x, y, mod)`: `k` = GLUT special code (left=100, up=101, right=102, down=103, pgup=104, pgdn=105, home=106, end=107, insert=108, F1-F12=1-12 — `internal.py:398-423`). Return 1 consumes (LEFT/RIGHT only — see above).

### 6.3 Feasibility verdict for PLAY-02 "adjust"

- **Feasible**: `do_special` intercepting LEFT(100)/RIGHT(102) — clean, wizard-scoped (events arrive only while the wizard is top-of-stack), zero global state, no `set_key` pollution, auto-lifetime. Optionally specific ASCII keys via `do_key` (returns 1 only for owned keys so all other shortcuts/camera keys still work — `PyMOL.cpp:2305` falls through on falsy return).
- **Avoid**: UP/DOWN as exclusive game keys (history navigation co-fires); `cmd.set_key` rebinding (global, and there is no clean restore API for previous bindings in the visible surface).
- The transform primitive itself (nudge/rotate math) is the movement-model researcher's scope; this establishes only that the wizard CAN own LEFT/RIGHT + ASCII keys as input channels. **Note for the spike:** whether arrow keys reach `do_special` under the exact Windows Qt build is a 5-minute human/headless observation — the C path is verified, the Qt focus path (viewer widget vs main window focus) is the one soft spot (`pymol_gl_widget.py` implements mouse but delegates keys to the main-window handler).

---

## 7. Enter/exit environment save/restore table (Q6, PLAY-04)

| # | What the wizard touches | ON ENTER (activate / `__init__`) | ON EXIT (`cleanup()`) | Evidence |
|---|---|---|---|---|
| 1 | Wizard stack / prior wizard | `cmd.set_wizard(self)` — push; prior wizard (if any) stays dormant beneath | `cmd.set_wizard()` (None) — pops game wizard, runs this `cleanup()`, prior **auto-resumes** as top | `Wizard.cpp:263-284`; `WizardGet`=back `:786`; v1 flaw documented §2.3 |
| 2 | `mouse_selection_mode` | `self._saved_msm = cmd.get_setting_int("mouse_selection_mode")`; `cmd.set("mouse_selection_mode", 0)` | `self.cmd.set("mouse_selection_mode", self._saved_msm)` | save/set `measurement.py:96-97` (identical `distance.py:69-70`, `pair_fit.py:24-25`, `appearance.py:68-69`); restore `measurement.py:212`. Stock default = **1** (`SettingInfo.h:449`) |
| 3 | Active selection (`sele` / user's named selection) | `cmd.deselect()` (clear active selection so clicks start clean — `measurement.py:98`, v1 `wizard.py:45`) | `cmd.delete` stale transient selection if present (guarded); the canonical per-pick `cmd.delete(name)` already removes each click's sele | `measurement.py:98,299,219`; v1 `wizard.py:45,83` |
| 4 | `pk1` pick buffer | — (each pick: read then `cmd.unpick()`) | `self.cmd.unpick()` + `self.cmd.delete("pk1")` | `clear_input` pattern `measurement.py:214-221` (deletes `_mw*`, `_indicate_mw`, `pk1`); unpick per pick `measurement.py:341`, v1 `wizard.py:59` |
| 5 | Recolored AA atoms | Lazy: snapshot per-atom `color` of a slot BEFORE its first recolor (`cmd.iterate(obj, ... ID, color ...)`) | Restore every recolored slot's colors via `cmd.alter(obj, "color=...")` | symbol table `editing.py:1448`; recolor precedent v1 `game.py:208-213`; detection-immunity `geometry.py:134-138` |
| 6 | Any `cmd.set()` the wizard flips | Snapshot value before each `cmd.set` (today: only `mouse_selection_mode`; if the movement model adds settings, extend this row) | Restore each | measurement template above; PLAY-04 wording: "prior wizard and mouse_selection_mode restored" is the floor, not the ceiling |
| 7 | Wizard panel/prompt state | — | Self-clears: wizard removal → `WizardRefresh` with no wizard → `OrthoReshapeWizard(G, 0)` | `Wizard.cpp:253-258` |
| 8 | Game objects (`_aam_*`) | Created by `engine.materialize` BEFORE wizard activation | NOT deleted by `cleanup()` (game objects outlive the wizard; Cleanup-button semantics are Phase 4; `cleanup_game_objects` is prefix-only, `placement.py:392-405`) | state split `engine.py:11-20` |
| 9 | View/camera | Never touched (left-drag rotation must keep working — the canonical do_select map preserves it) | — | v1 rationale `wizard.py:17-20`; PITFALLS Pitfall 5 |

**Idempotency note:** cleanup runs on pop AND on replace; every restore above is naturally idempotent (set-back, delete-if-exists, color-write). Follow `measurement.py:205-212` shape. Also guard `self.cmd` being None (session-restore rebinding case) exactly like `dragging.py:72-74`.

**What cleanup must NOT do:** delete game objects, mutate engine state (engine ops own that), or touch user objects (prefix/slot-registry discipline only).

---

## 8. Recommended architecture for `aamatch/wizard.py` (Q8)

**Shape: thin input adapter (ARCHITECTURE.md Pattern 2), engine is the brain (engine.py composition root).**

```
aamatch/wizard.py            (CMD TIER — never PURE_MODULES; Gate D compiles it)
  class GameWizard(pymol.wizard.Wizard)
    owns:  plain-data state ONLY —
           _slot_by_object      {object_name: slot_id}     (reverse registry map, §5.3)
           _current_slot        slot_id | None
           _molecule_index      int
           _saved_msm           int                        (mouse_selection_mode snapshot)
           _color_snapshots     {object_name: [(ID, color), ...]}   (lazy, §4)
           _result_lines        [str, ...]                 (last confirm result, §3.3)
    delegates: ALL game state changes to engine.*
    imports: `from . import engine` INSIDE methods (module-identity-agnostic, §1.5);
             `from pymol.wizard import Wizard` + `from pymol import cmd` at module level (cmd tier — legal)

  activate(registry, payload, molecule_index=0):  builds reverse map, snapshots, set_wizard(self)
  do_select(name)      → canonical map → do_pick(0)          (measurement.py:295-306 shape)
  do_pick(bondFlag)    → hygienic read → slot lookup → highlight(slot_id) → refresh_wizard
  confirm()            → engine.confirm(level_index, molecule_index, required) → render §3.3
  reset_to_grid()      → engine.reset_to_grid() + restore colors + refresh
  cleanup()            → §7 table rows 2,3,4,5 (restore everything, touch nothing else)
  get_panel/get_prompt → pure functions of the plain-data state
```

Ownership split (what the wizard must NEVER do):
- No detection math, no scoring, no spec knowledge — `engine.confirm` returns ready `(records, score, formed_types)`.
- No object creation/deletion beyond the §7 restore set (`engine`/`placement` own materialize/cleanup).
- No Qt, no timers, no threads (Phase 4+ adds the Qt shell around the SAME engine calls — the v1 GUI-owns-wizard-lifecycle precedent `game.py:215-226` maps onto Phase 4).
- No module references stored on `self` (pickle discipline, §2.3).

Headless testability (planner-friendly): every wizard behavior except real-mouse delivery is callable headlessly — instantiate `GameWizard`, `cmd.select('sele', '<slot object> and name CA')`, call `do_select('sele')` directly, assert recolor + state + panel strings; call `confirm()` after scripted moves (SMOKE-04 pose-scripting pattern). Only the physical click routing (§2.2 C dispatch) is the human checkpoint. `cmd.refresh_wizard()` is safe headless (it merely re-pulls prompt/panel).

Start-Game wiring for Phase 3 (pre-Qt): the existing `run_plugin_gui` placeholder (`aamatch/__init__.py:28-31`) or a `cmd.extend`-registered command can invoke a cmd-tier starter: `engine.new_game(setup, seed)` → `engine.materialize(payload, 0)` → `GameWizard(...).activate(...)`. Zero new dependencies; menu path already proven at the 01-09 human checkpoint (plugin-path install, `01-09-SUMMARY.md` key-decisions).

---

## 9. Human-verify checkpoint design (Q7)

**"Fresh/stock PyMOL" defined concretely** (all defaults verified in the source):
- `button_mode` = 0 → Three Button Viewing (ring position 0 of `three_button_viewing` ring; `SettingInfo.h:147` default 0; `controlling.py:127-141,204`).
- `mouse_selection_mode` = **1** (residue; `SettingInfo.h:449`) — the checkpoint asserts restoration to the USER'S pre-game value, which on true stock = 1.
- No wizard active (`cmd.get_wizard()` is None); no `_aam_*` objects in the scene; `editor_scheme` at its default (movement-spike observation, not this phase's gate).
- Install: **plugin-path method** (repo root on PyMOL's plugin path; 01-09 verdict — repo edits live, exactly one module object; do NOT additionally copy-install).

**PLAY-01 steps (click-to-select):**
1. Fresh PyMOL; Plugins → AA-match → start a game (Phase-3 starter). A grid of `_aam_aa*` objects + `_aam_lig` appears; wizard panel visible at the viewer's edge; prompt says "Click an amino acid...".
2. In default 3-Button Viewing, LEFT-click an AA → its color visibly changes; prompt/panel shows the slot as selected. (No dev-box button-mode tweaks — verifies the do_select route on stock SeleSet mode.)
3. Left-drag rotates the camera (selection handling did not break viewing).
4. Click empty space → nothing breaks; current selection stays.

**PLAY-02 steps (move/rotate + detector scores the moved pose):** use the panel movement controls (per the frozen movement model — spike verdict governs) to move/rotate the selected AA near the ligand → Confirm → result text appears in panel; verify the score matches the visible geometry (place a clearly-interacting pose vs. a far pose; scores must differ accordingly). Reset to Grid returns every AA (verify one visually).

**PLAY-03 steps (switch selection + Confirm):** click a different AA → previous AA's color restored, new AA highlighted (per-click switch); Confirm on a complete molecule shows the final result in the wizard panel.

**PLAY-04 steps (restoration + no helper visuals):**
1. Before starting: launch a built-in wizard (e.g. `wizard measurement`) or note `cmd.get_wizard()`; note `mouse_selection_mode` value.
2. Play through; at NO point do helper lines/dots/CGO appear (only recolors + panel text).
3. Exit the game wizard (Done) → prior wizard is active again (or `get_wizard()` is None if none was prior); `mouse_selection_mode` equals the noted pre-game value; no leftover `pk1`/`sele`/`_aam_` strays beyond the deliberately-kept game objects; recolored AAs back to original colors.
4. Record the movement-model spike verdict in the phase summary (object-matrix default; `cmd.drag(wizard=0)` headless spike result + default `editor_scheme`) — the ROADMAP gate.

---

## 10. Open questions / UNVERIFIED items

1. **[UNVERIFIED — needs a 5-minute observation] Arrow-key delivery through the Windows Qt GUI focus path.** The C dispatch (`PyMOL.cpp:2310-2344`) and Qt translation (`keymapping.py`, `pymol_qt_gui.py:50-54`) are verified, but whether the viewer GL widget (mouse focus) reliably delivers `keyPressEvent` through `PyMOLQtGUI` on the conda Windows build is untested. Mitigation: the phase spike (already mandated for the movement model) should include one arrow-key probe; panel buttons remain the guaranteed input path regardless.
2. **[UNVERIFIED — planner decision] `do_select` on a user's named active selection.** If the player made a *named* selection active, `name` arrives as that selection and the canonical `cmd.delete(name)` would delete it (`SceneMouse.cpp:258-261`; canonical delete `measurement.py:299`). 20 years of measurement-wizard precedent says acceptable; AA-match can guard (delete only transient names) at the cost of a leftover enabled selection. Decide during planning.
3. **[LOW — observed behavior, no citation needed] Which representation stock PyMOL uses to visualize an enabled selection** (pink crosses/boxes vs spheres) was not pinned; irrelevant to the recommended recolor design, matters only if the plan opts into native selection display.
4. **[OPEN — movement researcher] The `cmd.drag(wizard=0)` interplay and default `editor_scheme`** — explicitly out of scope here per the brief; only the input channels (§6) are covered. Note `smoke/smoke_06_spike_movement.py` already exists untracked in the repo — the spike is in progress elsewhere.
5. **[OPEN — planner] Multi-molecule UX in Phase 3.** All molecules of a level materialize together (§5.4); Phase 3 can scope clicks to molecule 0 or allow free switching, with `engine.confirm` receiving the matching `molecule_index`. Phase 6 owns full lifecycle.
6. **[OPEN — Phase 7 liaison] Wizard pickling.** `session_save_wizard` pickles the stack (`wizarding.py:176-180`); the recommended plain-data wizard pickles cleanly, but the checkpoint design (Phase 7 gate) must verify the round-trip — `.pse` matrix/coords round-trip is already a STATE.md blocker note.
7. **[Verified-but-notable] `mouse_selection_mode` default is 1, not 0** — plans that assert "restore to 0" after the game would be wrong on stock PyMOL; restore to the *snapshot*.

## Sources

### Primary (HIGH confidence — read directly, PyMOL 2.5.0 tree `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/bioCHEMeleon/tmp/pymol-src/`)
- Python layer: `modules/pymol/wizarding.py` (full), `wizard/__init__.py` (full), `wizard/measurement.py:1-374`, `wizard/dragging.py` (full), `wizard/mutagenesis.py:1-120,180-320`, `wizard/command.py:120-178`, `wizard/box.py:384-445`, `wizard/pseudoatom.py` (full), `wizard/label.py` (grep), `wizard/distance.py`+`pair_fit.py`+`appearance.py` (grep: msm save/restore), `internal.py:390-484`, `keyboard.py` (full), `controlling.py:127-141,168-,620-660`, `editing.py:1425-1469`, `exporting.py:395-424`, `builder.py` via `modules/pmg_qt/builder.py:51-58,1208-1224`
- C layer: `layer1/Wizard.h` (full), `layer1/Wizard.cpp` (constants `:43-57`, `isEventType :139-142`, `WizardDoSelect :171-190`, `WizardRefresh :194-259`, `WizardSet :263-284`, `WizardDoPick :302-325`, `WizardDoKey :327-341`, `WizardDoSpecial :461-476`, `click/release/draw :480-582,700-779`, `WizardGet :783-787`, stack fns `:790-821`), `layer1/SceneMouse.cpp:232-372,403-479,557-600`, `layer5/PyMOL.cpp:2302-2344`, `layer1/Ortho.cpp:305-310,314-340,396-401`, `layer1/PConv.cpp:1127-1156`, `layer0/Word.h:24-26`, `layer1/SettingInfo.h:147,162-163,449`
- Qt GUI: `modules/pmg_qt/keymapping.py` (full), `modules/pmg_qt/pymol_qt_gui.py:30-69,440-460`

### Secondary (HIGH — shipped prior art, read directly)
- `tmp/bioCHEMeleon/biochemeleon/wizard.py` (full — PickWizard, canonical map, saved-wizard pattern incl. its flaw)
- `tmp/bioCHEMeleon/biochemeleon/game.py` (full — on_pick/confirm callbacks, recolor precedent, cleanup semantics)

### Tertiary (repo planning docs, consistent with findings)
- `.planning/research/PITFALLS.md` Pitfall 5 (line 118), Pitfall 8 (line 192); `.planning/research/ARCHITECTURE.md` Pattern 2 (line 140), Pattern 3 (line 164); `.planning/REQUIREMENTS.md` PLAY-01..05; `.planning/ROADMAP.md` Phase 3 (line 86); `.planning/phases/01-bootstrap-pure-foundation/01-09-SUMMARY.md` (plugin-path method); `aamatch/placement.py`, `aamatch/engine.py`, `aamatch/geometry.py`, `aamatch/level_spec.py`, `aamatch/__init__.py` (read directly)

## RESEARCH COMPLETE
