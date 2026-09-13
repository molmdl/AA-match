# Phase 4 Research: Setup-Form Requirements → Existing API Seams

**Researched:** 2026-09-13
**Scope:** For each of SETUP-01..10, which existing Phase 1/2/3 function/object serves it, with exact signature and caveats. (File-format design for SETUP-08 and the upload→generator path for SETUP-03 are other researchers' briefs; this document maps the form-side seams only.)
**Confidence:** HIGH — every claim below was read directly from the named source file:line in this repo this session. No training-data claims.

---

## seam_map

Per-requirement table: requirement → API → signature → caveats. All citations verified this session.

| Req | Seam (module.function) | Exact signature / source | What the form must collect | Caveats |
|---|---|---|---|---|
| **SETUP-01** modeless window | `aamatch/__init__.py` menu wiring | `__init_plugin__(app=None)`; menu via `addmenuitemqt('AA-match', run_plugin_gui)` (`aamatch/__init__.py:25-26`) | — | Phase 4 re-points `run_plugin_gui` (`aamatch/__init__.py:29-39`, currently `from . import gamestart; return gamestart.start_game()`) at the setup window (spec.md:11-12; STATE 03-06 spec-gap note "Plugins → AA-match must ultimately open a SETUP POPUP"). **Breaking-test alert:** `tests/test_package_skeleton.py` pins `run_plugin_gui`'s body as an AST contract (lazy relative import + returned `start_game()` call — 03-05-SUMMARY) → that test MUST be deliberately updated in Phase 4 (contract change, not weakening). Gate A2 (`tests/test_purity.py:214-230`) still demands ZERO module-level imports in `__init__.py` — the Qt import stays lazy inside the handler. Metadata block (`aamatch/__init__.py:1-13`) must stay byte-identical first lines. |
| **SETUP-01** window mechanics | Qt tier pattern (new module) | Module-level singleton `dialog = None` + `dialog.show()` NEVER `.exec_()`; Qt via lazy `from pymol.Qt import QtWidgets` inside functions; `exec_()` allowed ONLY on child QFileDialog/QMessageBox | — | PITFALL 4 (`.planning/research/PITFALLS.md:104-114`): "first GUI architectural decision; retrofit is a rewrite". Prior art proves it: `tmp/bioCHEMeleon/biochemeleon/gui_setup.py:11` ("dialog stays modeless (QFileDialog/QMessageBox are modal children...)"). Recorded env: PyQt5 5.12.3 / Qt 5.12.9 (STATE 01-07, `windows-env-versions.md`). ROADMAP criterion "window survives minimize/re-open" → the singleton ref is load-bearing (GC prevention). |
| **SETUP-02** demo dropdown | `paths.package_data_path` + `persistence.read_json_file` + `manifest.parse_manifest_dict` | `read_json_file(path) -> container` (`aamatch/persistence.py:116-128`); `parse_manifest_dict(container) -> payload` (`aamatch/manifest.py:100-158`); canonical call shape `aamatch/engine.py:196-198` | Selected `set_id` (string) → `setup['demo_set_id']` | Manifest TODAY: exactly ONE set — `demo-dev-1` (tier `easy`, title "Phase-2 development set", license `''` / provenance `{}` = Phase-8 placeholders), 2 entries (benzamide, acetate) (`aamatch/data/MANIFEST.json:4-52`). Set display fields per payload shape (`aamatch/manifest.py:31-43`): `set_id`/`tier`/`title`. The dropdown lists `sets`; `enumerate_entries` (`manifest.py:298-314`) is the GENERATOR's candidate flattener — not dropdown data; `largest_entry` (`:317-329`) is the DETECT-05 smoke selector — not dropdown data. |
| **SETUP-02** dropdown → engine | `engine.new_game` demo_set_id filter | `new_game(setup, seed, candidates=None)` — non-empty `demo_set_id` filters rows and raises `EngineError("new_game: demo_set_id %r matches no manifest set -- check setup/MANIFEST.json")` when nothing matches (`aamatch/engine.py:200-207`); empty string enrolls ALL rows (`:200-201`) | — | `validate_state` does NOT check manifest membership — only non-empty string (`aamatch/setup_state.py:100-102,112-113`). Membership is the UI's job. Empty-manifest parses fine (STATE 02-03: "Empty sets list allowed; supply emptiness is the generator's concern") — dropdown shows a placeholder; generation-time refusal comes from `engine.py:215-218` ("zero ligand candidates enrolled"). |
| **SETUP-03** upload (form side only) | `setup_state` reserved fields | `setup['upload']` = `None` or `{'path': str, 'sha256': str}` (`aamatch/setup_state.py:57`; shape-checked `:137-142`); `setup['source_mode']` ∈ `('demo','upload')` (`:52`, validated `:108-110`) | File path (QFileDialog, SDF/MOL2 filter) + sha256 | sha256 is reserved so Load can warn when the file moved (`aamatch/setup_state.py:27-30`). **No engine path consumes `source_mode='upload'` today:** `new_game` reads only the bundled MANIFEST.json or the `candidates` override (`aamatch/engine.py:195-218`), and `placement.materialize` resolves ligand files ONLY as package-relative `package_data_path('data', ligand['file'])` (`aamatch/placement.py:304-306`) — a user file cannot flow through unchanged (needs staging into `data/` or a loader extension = the upload brief). Form contract: collect path+sha256, set `source_mode='upload'`, keep demo selection intact underneath (see `dropdown_and_upload_state`). |
| **SETUP-04** molecules per level | `setup_state` constants + `validate_state` clamp | `MOLECULES_DEFAULT, MOLECULES_MIN, MOLECULES_CAP = 2, 1, 10` (`aamatch/setup_state.py:46`) — FROZEN (STATE 01-09); clamp at `:119-122` | QSpinBox | Spec wording "default 2-5" (spec.md:15) = default **2** with a sensible range; frozen clamp is 1..10 — reconcile by mirroring the frozen constants exactly (see `form_field_specs` ruling). Generator re-checks `molecules_per_level >= 1` (`aamatch/generator.py:777-781`). |
| **SETUP-05** difficulty levels | same constants family | `DIFFICULTY_DEFAULT, DIFFICULTY_MIN, DIFFICULTY_CAP = 3, 1, 10` (`aamatch/setup_state.py:50`) — FROZEN (cap human-amended 9→10 at 01-09, commit aef7c5e); clamp at `:123-126` | QSpinBox | Generator re-checks int in 1..DIFFICULTY_CAP (`aamatch/generator.py:768-772`). Changing either cap = version-bump event (STATE 01-09). D=1 is legal (single easiest level; `aamatch/generator.py:162-166` guards the div-by-zero). |
| **SETUP-06** interaction mode | `setup_state` enum + list; `generator.derive_required` | `INTERACTION_MODES = ["exclusive","block_exclusive","unset"]` (`aamatch/setup_state.py:44`); `INTERACTION_TYPES = ["h_bond","salt_bridge","pi_stacking","cation_pi","hydrophobic","halogen","metal"]` (`:40-41` — THE canonical checkbox order); mode validated `:115-117`; `allowed_interactions` filtered/deduped/canonical-ordered `:128-135` | Mode radio (3-way) + 7 checkboxes | `allowed_interactions` is stored REGARDLESS of mode (mode governs USE; `aamatch/setup_state.py:24-26`) and always serialized canonically. `validate_state` never FAILS on these — it silently normalizes; the only UI-visible precondition failure is empty-allowed in exclusive/block_exclusive, raised later by `derive_required` (`aamatch/generator.py:386-389, 399-401`). Full semantics in `mode_widget_design`. |
| **SETUP-07** Reset | `setup_state.DEFAULTS` | Exactly 7 keys (`aamatch/setup_state.py:54-62`; key-set regression test `tests/test_setup_state.py:90-94`) | — | Apply `validate_state({})` or `copy.deepcopy(DEFAULTS)` — never alias the module dict into mutable widget state. Prior art: `gui_setup.py:315` (`reset_btn.clicked.connect(lambda: self.apply_state(DEFAULTS))`). |
| **SETUP-07** Randomize | `setup_state.randomize_state(seed=None)` | Returns a complete VALID state; deterministic under seed (`aamatch/setup_state.py:147-172`) | — | **Trap:** it synthesizes `demo_set_id = 'demo-%04x'` (`:165`) — matches NO manifest set → `engine.new_game` refuses (`engine.py:204-207`). The window must overwrite `demo_set_id` after randomizing (see `randomize_design`). `source_mode` stays `'demo'`, `upload` stays `None` (`:157-159`). |
| **SETUP-07** Save Setup | `persistence.save_setup_file(path, state)` | Validate-BEFORE-write; versioned container kind='setup'; atomic write (`aamatch/persistence.py:145-153`) | Path from QFileDialog | OSError (disk/permission) is NOT wrapped — propagates raw from `write_json_atomic` (`persistence.py:91-113`). Route the dialog path through `paths.to_windows_path` first (AGENTS path law, `aamatch/paths.py:8-11,20-51`). |
| **SETUP-07** Load Setup | `persistence.load_setup_file(path)` | Validate-AGAIN-on-load; returns a validated 7-field dict (`aamatch/persistence.py:156-165`) | Path from QFileDialog | FormatError (⊂ ValueError) refusal texts: foreign `"not an AA-match file (magic=%r, expected %r)"` (`:73-75`); newer `"unsupported AA-match format version %d (expected <= %d). Please update AA-match."` (`:80-83`); misfiled `"expected an AA-match setup file, found kind=%r"` (`:84-87`); unparseable `"could not parse AA-match JSON: %s"` (`:126-128`). Older containers ACCEPTED with `.get` forward-fill (`:69-71`). `FORMAT_VERSION = 1` refuse-newer/accept-older (`:34-35`). |
| **SETUP-08** Generate & export (button→generator seam) | `engine.new_game(setup, seed, candidates=None) -> (payload, rows)` | Full path: validates setup (`:193`), parses manifest or uses `candidates` (`:195-218`), builds per-candidate `ligand_data` via temp loads (`:220-223`), calls `generator.generate` (`:225-226`), asserts the scene UNCHANGED (`:232-235`) (`aamatch/engine.py:183-236`) | Setup + a seed decision | Payload shape: `aamatch/generator.py:714-730, 874-879` (stamps `detector_version`/`format_version`/`seed`). **Side effect:** new_game also sets module state `_payload`, `_game = GameState()`, `_registry = None` (`:228-231`) — an export replaces stale runtime state (benign; document it). Export must NOT materialize (spec.md:24 "Only generate ... WITHOUT starting play"; prior-art tooltip `gui_setup.py:280-284`). `KINDS` already includes `'game'` (`aamatch/persistence.py:37`) but NO save/load game wrapper exists (only setup wrappers, `:145-165`). Payload → shareable file = the other brief. |
| **SETUP-09** Cleanup | `placement.cleanup_game_objects() -> {'deleted': n}` | Deletes every object whose name starts with `geometry.GAME_PREFIX = '_aam_'` (`aamatch/placement.py:404-417`; `aamatch/geometry.py:81`) | — | PREFIX-ONLY rule — "user molecules must never match" (`aamatch/placement.py:408-410`). "Restore original scene" TODAY = prefix deletion + nothing else was ever mutated (full mutation inventory in `phase_4_5_boundary`). `placement.py:61-63` explicitly defers "full Cleanup-button semantics (pre-game atom counts, adopted-vs-materialized ligand bookkeeping)" to Phase 4 — but v1 adopts NO user objects, so that bookkeeping has zero workload; record that reading in the plan rather than inventing machinery. Live-game interaction: cleanup under an ACTIVE GameWizard deletes objects from a live registry — pop the wizard first (see `open_questions` Q4). |
| **SETUP-10** Start | `gamestart.start_game(setup=None, seed=42, candidates=None) -> live GameWizard` | Sequence (`aamatch/gamestart.py:221-254`): `cleanup_game_objects()` FIRST (`:239`) → `new_game(spec, seed, candidates)` (`:240-241`) → `materialize(payload, 0)` (`:242`) → `GameWizard(payload, registry, 0, 0).activate(replace)` conditional replace (`:243-245`) → zoom + roll + pitch (`:246-248`) → status print (`:250-253`) | Validated setup dict | `setup=None` → `dict(setup_state.DEFAULTS)` (`:240`); user dict validated fail-closed INSIDE new_game (`:226-229`; safe despite the shallow copy — `validate_state` deep-copies and never mutates input, `setup_state.py:104-106`). Fail-closed: GenerationError/EngineError/WizardError PROPAGATE (`:235-237`) — the Qt button must catch the ValueError family (see `error_surfacing`). **Order caveat:** cleanup runs BEFORE new_game can refuse — a refused start still deletes prior game objects; pre-check the form in the window (see `pure_layer_opportunities`). |
| (gate) setup files | `persistence.FORMAT_VERSION` | =1, refuse-newer/accept-older (`aamatch/persistence.py:34-35, 80-83`) | — | Never conflated with the detector gate. |
| (gate) exported specs | `level_spec.DETECTOR_VERSION` / `LEVEL_SPEC_VERSION` | `DETECTOR_VERSION = "det-1"` EXACT match — "stale or newer — regenerate" (`aamatch/level_spec.py:60, 117-121`); `LEVEL_SPEC_VERSION = 1` refuse-newer (`:61, 111-114`) | — | The generator stamps both verbatim (`aamatch/generator.py:874-877`); export preserves them. |

---

## form_field_specs

Field → widget → bounds → justification. **Bounds mirror the FROZEN `setup_state` clamp constants exactly, imported from the pure module** (dependency direction B8: cmd/Qt imports FROM pure — `aamatch/setup_state.py:32-33`). A WIDER spinbox range lets `validate_state` silently clamp (`aamatch/setup_state.py:119-126`) — "I typed 15, it used 10" and the number visibly changes after a Save/Load round-trip; a NARROWER range rejects values the pure layer accepts (loading a saved 7-difficulty file into a 3..5 spinbox misrenders) and creates a second bounds source to keep in sync.

| Setup field | Widget | min | max | default | Justification |
|---|---|---|---|---|---|
| `source_mode` + `demo_set_id` | 2-way source radio ("Bundled demo set" / "Upload my molecules..."); demo page = QComboBox of bundled sets (`currentData` = `set_id`, label = `title` else `set_id`, tier suffix optional) | — | — | `source_mode='demo'`, `demo_set_id=''` | `aamatch/setup_state.py:52-57`. Empty id = ALL sets (`aamatch/engine.py:200-201`); membership NOT validated by the pure layer (`aamatch/setup_state.py:100-102`). Prior-art stacked-pages pattern `gui_setup.py:89-96`. |
| `upload` | "Browse..." button → `QFileDialog.getOpenFileName` (filter `"Small molecules (*.sdf *.mol2)"`) + read-only path label | — | — | `None` | Reserved shape `{'path','sha256'}` (`aamatch/setup_state.py:57,137-142`); sha256 = glue-tier `hashlib` (whitelisted, `tests/test_purity.py:98`). |
| `molecules_per_level` | QSpinBox | `MOLECULES_MIN` = 1 | `MOLECULES_CAP` = 10 | `MOLECULES_DEFAULT` = 2 | Frozen (`aamatch/setup_state.py:46`). Spinbox range == clamp range ⇒ collect → `validate_state` is IDENTITY for this field. Spec's "default 2-5" (spec.md:15) satisfied: default 2, and 2–5 lies inside the reachable range; the frozen cap 10 wins over a literal 5 (changes = version-bump event, STATE 01-09). |
| `difficulty_levels` | QSpinBox | `DIFFICULTY_MIN` = 1 | `DIFFICULTY_CAP` = 10 | `DIFFICULTY_DEFAULT` = 3 | Frozen (`aamatch/setup_state.py:50`, human-amended 9→10). Same range-mirroring argument; spec "default 3-5" (spec.md:16): default 3, range superset. |
| `interaction_mode` | 3-way radio group: "Exclusive (any allowed)" / "Block-exclusive (checked set)" / "Unset (random)" | — | — | `'unset'` | Enum home `aamatch/setup_state.py:44`; default frozen `'unset'` (01-09). Labels carry the spec meanings (spec.md:18-20). |
| `allowed_interactions` | 7 QCheckBoxes in canonical `INTERACTION_TYPES` order | — | — | `[]` | Canonical order `aamatch/setup_state.py:40-41`; validator re-orders/dedupes canonically (`:128-135`) so widget order is cosmetic-but-do-it-anyway. Display labels ("hydrogen bond", "pi-stacking"...) are UI-only; stored values are the enum strings. |

**Reconciliation ruling (spec "2-5"/"3-5" vs frozen 1..10):** spinbox ranges = `[MOLECULES_MIN, MOLECULES_CAP]` (1..10) and `[DIFFICULTY_MIN, DIFFICULTY_CAP]` (1..10), defaults 2 and 3. The frozen bounds are a human-amended, version-gated decision (STATE 01-09); the spec wording reads naturally as "a sensible default in the 2–5 neighborhood", which defaults 2/3 satisfy. Matching ranges is the only way to make collect→validate lossless; the alternative (spinbox 2..5 / 3..5) is rejected above.

**Seed:** the spec's form list (spec.md:13-21) has NO seed field. `start_game(seed=42)` (`aamatch/gamestart.py:221`) and `generate(seed, ...)` both take one. Recommendation: no visible seed field in v1; Start uses the default 42 (matches SMOKE-08-verified behavior); Generate-and-export picks a fresh random seed per export — the exported payload already echoes it (`payload['seed']`, `aamatch/generator.py:877`). See `open_questions` Q2.

---

## mode_widget_design

**What setup_state stores** (`aamatch/setup_state.py:54-62`): `interaction_mode` (one of 3 strings) + `allowed_interactions` (list in canonical order, ALWAYS populated regardless of mode — `:24-26`; the mode governs how the list is USED).

**What the generator does with them** — `derive_required(setup, ligand_profile, rng, n_required_types)` (`aamatch/generator.py:337-439`), refusal texts verified verbatim:

| mode | generator behavior | refusals that can reach the UI |
|---|---|---|
| `exclusive` | returns `{'mode':'any','items':[]}` — "any interaction formed", SCOPED BY the allowed list (`aamatch/generator.py:384-396`) | empty allowed → `"exclusive mode requires the setup field 'allowed_interactions' to be non-empty -- check the interactions the game should teach in Setup"` (`:386-389`); ligand supports zero → `"molecule supports none of the allowed interactions (%s)"` (`:392-395`) |
| `block_exclusive` | required set = EXACTLY the checked types, count 1 each, canonical order (`:398-410`); hydrophobic reachable ONLY here (OQ-5, `:29-34`) | empty → `"block_exclusive mode requires 'allowed_interactions': no interactions checked"` (`:399-401`); checked-but-unsupported type → `"molecule cannot support required interaction(s): %s"` NAMING the type(s) (`:403-408`) — never silent degradation |
| `unset` | support-filtered sampling MINUS hydrophobic; vocabulary = allowed list if non-empty else all non-hydrophobic types; k = min(n_required_types, len(pool)) (`:412-430`) | only-hydrophobic supported → refusal NAMING the OQ-5 policy (`:418-426`); nothing sampleable → `"molecule supports none of the sampleable interactions (vocabulary: %s)"` (`:427-430`) |

**Widget recommendation:** 3-way radio group + 7 checkboxes, checkboxes ENABLED IN ALL THREE MODES. Rationale: in `unset` mode a non-empty allowed list NARROWS the sampling vocabulary (`aamatch/generator.py:413-414`) — disabling the checkboxes in unset mode would silently discard the user's restriction at collect time (and after Load the widgets would not reflect a non-empty stored list). A one-line context label under the group restates the current meaning:

- exclusive: "the game accepts ANY of the checked interactions"
- block_exclusive: "the player must form EXACTLY the checked interactions"
- unset: "the game randomizes the required set from the checked types (hydrophobic excluded from random picks)"

**Can the UI pre-validate the OQ-5 / unsupported-type refusals?** Partially — and it mostly should NOT:

- `capability.ligand_support(itype, ligand_profile)` (`aamatch/capability.py:679-701`) is the pure support predicate and `ligand_profile(atoms, bonds)` (`:616-676`) its constructor — but the profile must be computed FROM A LOADED MOLECULE (cmd tier; proven recipe `engine._ligand_data_for`, `aamatch/engine.py:144-180`). The manifest carries only `metal_present`/`halogen_present` flags per entry (`aamatch/manifest.py:70-71`), NOT the full profile — so "which of the 7 types does this demo set support" needs a cmd-tier temp load, i.e. generation-time work.
- Recommendation: do NOT duplicate support logic in the form (single-typing-home law, `aamatch/capability.py:30-32`; DETECT-04). Let generation refuse with its named-cause messages and surface them — they already point at Setup (`generator.py:388-389`).
- The PURE-layer pre-check that IS worth having: empty-allowed-list in exclusive/block_exclusive (see `pure_layer_opportunities`) — checkable from form data alone, and it prevents invoking a `start_game` that would clean the scene before refusing (`aamatch/gamestart.py:239`).
- Cheap honest hint the UI MAY show from manifest data only: annotate metal/halogen checkboxes "(no bundled molecule carries this)" when every bundled entry flags false — static `metal_present`/`halogen_present` aggregation, no typing duplication.

---

## randomize_design

**Existing API:** `randomize_state(seed=None)` (`aamatch/setup_state.py:147-172`) — pure, seed-deterministic (D4), already unit-tested (`tests/test_setup_state.py:11`). Output: random non-empty allowed subset in canonical order, random mode from the 3, random ints in the clamp ranges; `source_mode='demo'`, `upload=None` (`:157-159`).

**The trap (verified):** it synthesizes `demo_set_id = 'demo-%04x' % rng.randint(0, 0xFFFF)` (`:165`) — a string guaranteed to match NO manifest set, and `validate_state` does not check membership (`:100-102`). Start right after Randomize refuses with `"new_game: demo_set_id %r matches no manifest set -- check setup/MANIFEST.json"` (`aamatch/engine.py:204-207`). The ROADMAP criterion "Randomize produces a valid random configuration" is met by the pure call alone; USABLE requires the fix-up.

**Recommended shape:** a thin pure helper + a one-line GUI call:

```python
# pure (e.g. aamatch/setup_form.py, stdlib + .setup_state only)
def usable_randomized_state(seed=None, demo_set_id=''):
    state = randomize_state(seed)
    state['demo_set_id'] = demo_set_id      # a real manifest id, or '' = all sets
    return state
```

```python
# Qt handler (prior-art precedent gui_setup.py:620-642, which post-processes its own randomize)
self.apply_state(usable_randomized_state(demo_set_id=self._current_demo_set_id_or_empty()))
```

Do NOT change `randomize_state`'s output shape (pinned by tests); an additive optional kwarg is possible but buys nothing over this wrapper. The pure helper makes the fix-up WSL-testable (`randomize_state(0)` → fix-up → `validate_state` round-trip without Qt). After Randomize the window must also reflect `source_mode='demo'` / `upload=None` back into the widgets (`aamatch/setup_state.py:157-159`).

---

## persistence_seams

**Setup kind exists.** `KINDS = ('setup', 'level_spec', 'game', 'checkpoint', 'manifest')` (`aamatch/persistence.py:37`); Phase 1 froze the single container discipline for ALL AA-match files (`:1-26`). The setup wrappers exist and are tested (`tests/test_persistence.py:197-203` round-trip + header asserts):

- **Save:** `save_setup_file(path, state)` — validate-on-save; the file on disk is ALWAYS a normalized complete 7-field payload in the standard header (`aamatch/persistence.py:145-153`).
- **Load:** `load_setup_file(path)` — validate-on-load, idempotent (`validate_state(load) == load`), hand-edited files forward-fill from DEFAULTS (`:156-165`).
- Version gate: `FORMAT_VERSION` refuse-newer / accept-older (`:34-35, 80-83`).

**File dialog considerations** (prior art `gui_setup.py:644-677`, adapted):

- `QFileDialog.getSaveFileName(self, "Save AA-match Setup", "", "AA-match Setup (*.aam.setup.json);;All Files (*)")`; append the extension when missing (`:651-652` precedent). `exec_()` on these CHILD dialogs is explicitly allowed (PITFALL 4; the prior-art grep gate allows it on QFileDialog/QMessageBox only).
- Prior-art extension was `.bcm.setup.json` (`:648`); `.aam.setup.json` is the natural analog — a NEW convention, listed in `open_questions` Q1 for approval.
- **Path routing:** pass the dialog-returned path through `paths.to_windows_path` before any file API (`aamatch/paths.py:20-51`; the AGENTS law "every cmd.load/save/file-API call routes through it first", `paths.py:8-11`). Windows Qt dialogs return Windows paths, which the guard passes through unchanged — the guard is kept for idempotence and the WSL-path case.
- The JSON I/O itself stays PURE (`read_json_file`/`write_json_atomic` are stdlib-only, `aamatch/persistence.py:21-26`) — Save/Load need no cmd tier; the Qt handler calls the pure wrappers directly.

**Export (SETUP-08) persistence note for the planner:** the button's seam is `engine.new_game(...) -> payload`; wrapping the payload in a shareable container is the other brief. What already exists: level-spec container helpers + the exact-match DETECTOR_VERSION gate (`aamatch/level_spec.py:60-61, 111-121`); a `'game'` KIND with no wrapper yet (`aamatch/persistence.py:37`).

---

## dropdown_and_upload_state

**Dropdown data source (verified)** — read the manifest exactly the way `engine.new_game` does (`aamatch/engine.py:196-198`):

```python
from . import manifest, paths
from .persistence import read_json_file

payload = manifest.parse_manifest_dict(
    read_json_file(paths.package_data_path('data', 'MANIFEST.json')))
sets = payload.get('sets', [])    # set dicts: set_id/tier/title/license/provenance/entries
```

- Display label: `title` (fallback `set_id`); store `set_id` as userData (payload shape `aamatch/manifest.py:31-43`). Today: ONE set — `demo-dev-1` / "Phase-2 development set" / tier `easy` (`aamatch/data/MANIFEST.json:48-50`).
- **Empty-manifest behavior:** parse ACCEPTS an empty sets list (STATE 02-03) — render a "(no bundled sets)" placeholder item with `set_id=''` (empty = all-sets = none = the clear zero-candidates refusal at generation, `aamatch/engine.py:215-218`); never an exception at window-build time.
- **Window-build-time refusal risk:** a newer `manifest_version` raises FormatError (`aamatch/manifest.py:146-155`) — the window should catch FormatError here and degrade to an empty dropdown + visible message, not crash the menu action.
- `enumerate_entries` (`aamatch/manifest.py:298-314`) and `largest_entry` (`:317-329`) are generator/smoke surfaces — neither belongs in form code.

**Upload ↔ dropdown interaction (form-state model):** the state has THREE coexisting fields (`source_mode`, `demo_set_id`, `upload` — `aamatch/setup_state.py:55-57`), so mutual exclusion is a UI-layer policy, not a schema one. Recommendation: a 2-page source selector (prior-art stacked-pages pattern `gui_setup.py:89-96`), keeping the non-active page's values intact underneath:

- `source_mode='demo'` → generation uses `demo_set_id`; any leftover `upload` data is harmless (nothing reads it today).
- `source_mode='upload'` → `upload={'path','sha256'}` set; keep `demo_set_id` as-is (still serialized; format-stable).
- Randomize forces `source_mode='demo'` / `upload=None` (`aamatch/setup_state.py:157-159`) — the window must reflect that back into the widgets and fix up `demo_set_id` (see `randomize_design`).

**What the window passes through for an uploaded set:** form-side, nothing beyond the validated state fields. The `candidates` override (`engine.new_game(setup, seed, candidates)`, `aamatch/engine.py:183, 209-214`; `start_game(..., candidates=None)`, `aamatch/gamestart.py:221-233`) is the natural pipe, but building upload rows (staging vs package-relative paths — the `placement.py:304-306` constraint) is the upload researcher's problem. The window should NOT fabricate candidate rows itself.

---

## phase_4_5_boundary

**Phase 4's Start = the current `start_game` seam, unchanged** (`aamatch/gamestart.py:221-254`): cleanup FIRST → `new_game` (validates fail-closed inside) → `materialize(payload, 0)` (ONE level) → `GameWizard(...).activate(replace)` conditional → zoom/roll/pitch. Keep the Phase-4 button a THIN call (`start_game(validated_setup)` + error wrapper) so Phase 5 can extend the seam without re-touching the form.

**What Phase 4 does NOT build (SETUP-11 is Phase 5; ROADMAP Phase 5 criterion 1):**

- **Initial-state storage: NOTHING stores it today (verified).** Engine module state is `_payload/_registry/_game` only (`aamatch/engine.py:92-95`); `GameState` holds scores/formed types/timer anchor (STATE 02-10); `registry['pre_game_names']` is a NAME list for cleanup asserts (`aamatch/placement.py:279-284`), not a restorable state. Phase 5 adds the store (spec.md:22-25: store initial state, representations, Game tab, countdown).
- No Game status tab, no 3-2-1 countdown, no elapsed timer, no representations generation, no Hint (Phase 5, PLAY-05), no Import button (spec.md:27 puts Import in the Game status TAB — Phase 5+).
- No seed UI (see `form_field_specs`).

**Cleanup ("restore original scene") — the honest mutation inventory (all verified):**

- objects: only fresh `_aam_*` ones are ever born (never create-onto-existing, never load-into-existing — `aamatch/placement.py:33-39, 303-306`) → prefix deletion fully reverts (`:404-417`);
- user objects: never modified, recolored, or deleted (sentinel tagging applies to game objects only, `:149-156`; the wizard color store covers only slot objects);
- camera: zoom/roll/pitch (`aamatch/gamestart.py:246-248`) — not scene content;
- `mouse_selection_mode`: restored by wizard cleanup on Done (`aamatch/wizard.py:196-197`);
- representations: `cmd.hide/show` only on `_aam_aa` objects (`aamatch/placement.py:158-166`).

So Setup-window Cleanup = `cleanup_game_objects()` + surface `{'deleted': n}` is a COMPLETE "restore original scene" for v1. The adopted-ligand bookkeeping that `aamatch/placement.py:61-63` defers to Phase 4 has zero v1 workload (no user object is ever adopted); record that reading explicitly in the plan instead of inventing pre-game atom-count machinery.

---

## error_surfacing

**Inventory of every refusal/exception the 7 buttons can hit (all verified; all are ValueError subclasses unless noted):**

| Button | Error source | Type / message shape |
|---|---|---|
| Save Setup | `write_json_atomic` OSError (disk/permission) | raw OSError, NOT FormatError (`aamatch/persistence.py:91-113`) |
| Load Setup | 4 FormatError classes | foreign / newer ("...Please update AA-match.") / misfiled / unparseable (`aamatch/persistence.py:73-87, 126-128`) |
| Randomize | none (pure, total function) | — |
| Generate & export | `EngineError` (zero candidates `aamatch/engine.py:215-218`; demo_set_id no-match `:204-207`; candidate row shape `:210-214`; scene-changed assert `:232-235`); `GenerationError` (every named-cause refusal, `aamatch/generator.py:130-137` + mode table in `mode_widget_design`; degenerate ligand geometry `:226-279`; seed guards `:764-781`); OSError from the export write (other brief) |
| Cleanup | none from `cleanup_game_objects` itself (`aamatch/placement.py:404-417`) |
| Start | `GenerationError`/`EngineError`/`WizardError`/`PlacementError` propagate from the seam (`aamatch/gamestart.py:235-237`) |
| Window open / dropdown | FormatError from manifest parse (newer manifest, `aamatch/manifest.py:146-155`) |

**Two precedents:**

1. Wizard `_guard` (`aamatch/wizard.py:423-433`): the ValueError family → visible `self._error` + refresh; UNEXPECTED exceptions propagate ("bug surfacing, never a silent swallow"). Text renders `'ERROR:'`-prefixed LAST (`aamatch/wizard_text.py:228, 248, 264`).
2. bioCHEMeleon Qt (`gui_setup.py:657-659, 674-676, 362`): `QMessageBox.warning(self, title, msg)` on file/fetch failures; the main dialog stays modeless and QMessageBox is a modal CHILD — allowed (PITFALL 4).

**Recommendation (the Qt window has no wizard panel, so wizard-text conventions do not apply):** per-button handler mirroring `_guard`:

```python
try:
    <button work>
except ValueError as e:                    # FormatError / GenerationError / EngineError /
    QtWidgets.QMessageBox.warning(         # PlacementError / WizardError — all NAME the cause
        self, "AA-match", str(e))
# unexpected exceptions PROPAGATE (PyMOL console shows the traceback) — never silent
```

Show `str(e)` verbatim — every house refusal is already written user-facing (names the cause, points at Setup where relevant). Add `except OSError` on the Save/Load/Export handlers (OSError is not a ValueError). Do not catch-and-swallow anything else. An in-window status label is optional polish; the modal message box is the v1 contract.

---

## pure_layer_opportunities

What new validation/glue belongs in the PURE layer (WSL-testable under python3.6) vs the cmd/Qt tier. Gates are mechanical (`tests/test_purity.py`): new pure modules MUST be registered in `PURE_MODULES` (`:87-90`); `hashlib` IS whitelisted (`:98`); Gate D compiles every `aamatch/*.py` under 3.6.

**Recommended NEW pure module** (e.g. `aamatch/setup_form.py`, importing stdlib + `.setup_state` ONLY):

1. `build_state(form_values) -> (validated_state, warnings)` — plain-dict-in/plain-dict-out (spinbox ints, mode string, checkbox list, demo_set_id string, upload dict) → `validate_state` → plus human-readable warnings:
   - `interaction_mode in ('exclusive','block_exclusive')` and allowed empty → "N interactions must be checked in this mode" — exactly the condition `derive_required` refuses (`aamatch/generator.py:386-389, 399-401`); pre-checking in the window prevents a doomed `start_game` from cleaning the scene first (`aamatch/gamestart.py:239`);
   - `demo_set_id` non-empty and not in a supplied set-id list → "set no longer bundled" (manifest set-ids passed IN as plain data — the pure layer never reads files, matching `manifest.py`'s no-I/O discipline);
   - `source_mode='upload'` but `upload is None` → "choose a file".
2. `usable_randomized_state(seed=None, demo_set_id='')` — the Randomize fix-up as a pure function (see `randomize_design`), WSL-testable.
3. Optionally `manifest_sets(payload) -> [(set_id, title, tier)]` for dropdown label building (pure; input is the already-parsed payload) — additive to `manifest.py` or in the new module.

**What stays cmd/Qt tier (NOT pure):** everything touching `cmd.*` or Qt — QFileDialog/QMessageBox; the `start_game`/`cleanup_game_objects`/`new_game` calls; upload sha256 file reading (purity-legal via `hashlib` if desired, but it belongs to the upload brief); `to_windows_path` routing of dialog paths (the helper itself is pure; the routing DECISION is cmd-tier).

**Gates Phase 4 automatically inherits (planner checklist):**

- Gate A2: zero module-level imports in `aamatch/__init__.py` (`tests/test_purity.py:214-230`).
- Gate D: 3.6 syntax floor on every new `aamatch/*.py` (`:255-276`).
- `tests/test_wizard_source.py` SCANNED_MODULES must GROW by the new Qt UI module (one line; 03-05 precedent — "SCANNED_MODULES grows one line per new cmd-tier UI module").
- `tests/test_code_audit.py` PROSE_PIN demands a deliberate update if any docstring mentions banned tokens — in the Qt module simply never mention them ("the banned matrix calls" prose discipline, `aamatch/wizard.py:66-69`).
- `tests/test_package_skeleton.py`'s `run_plugin_gui` AST contract must be deliberately updated when the menu item re-points to the window (see `seam_map` SETUP-01).

---

## open_questions

1. **Setup file extension.** Prior art used `.bcm.setup.json` (`gui_setup.py:648`); recommend `.aam.setup.json`. Cosmetic but user-visible — needs explicit approval (nothing frozen pins it).
2. **Export seed policy.** Fixed 42 (deterministic, but every share of the same setup is the same game) vs fresh random seed per export (recommend; `payload['seed']` already echoes it, `aamatch/generator.py:877`) vs an optional seed field (not in spec's form list). Also: should a subsequent Start reuse the exported seed? Spec separates the flows (spec.md 3.5 vs 3.7) — recommend independent.
3. **Randomize fix-up semantics.** After `randomize_state`, should `demo_set_id` become (a) the currently selected dropdown value (recommend — preserves the user's chosen content), or (b) `''` (all sets)? Both defensible; pick one and pin it.
4. **Cleanup while a game wizard is active.** `cleanup_game_objects()` under a live GameWizard leaves dangling registry names. Options: pop the wizard first via canonical `cmd.set_wizard()` (runs its cleanup, `aamatch/wizard.py:179-206`) when `isinstance(cmd.get_wizard(), GameWizard)`; or disable the Cleanup button while a game is active. Recommend pop-first (matches `start_game`'s hygiene-first ordering, `aamatch/gamestart.py:15-17, 239`); either is safe — pick one and pin it in the plan.
5. **Window scope details not in SETUP-01..10:** tooltips on every widget + a short help text (spec UI standard "clear but sufficient in-game explanation"; prior art tooltips everywhere) — cheap; recommend in-scope, confirm.
6. **Upload flow dependency order.** The form can collect `source_mode='upload'` while generation still refuses ("no candidates") until the upload→generator brief lands. ROADMAP Phase-4 criterion 2 makes "upload an SDF/MOL2 molecule set" a Phase-4 [HUMAN] criterion, so the seam-owner plan must land WITHIN Phase 4 — the boundary is plan-level, not phase-level. The planner should sequence the two plans accordingly.

---

## Sources

All HIGH confidence — read directly this session (file:line citations throughout):

- `aamatch/setup_state.py` (full, 172 lines) — 7-field model, constants, validate/randomize
- `aamatch/persistence.py` (full, 165 lines) — kinds, gates, setup wrappers, refusal texts
- `aamatch/manifest.py` (full, 329 lines) — payload shape, parse gates, enumerate/largest
- `aamatch/generator.py` (full, 879 lines) — generate signature/payload, derive_required OQ-1/OQ-5 semantics + refusal texts
- `aamatch/gamestart.py` (full, 254 lines) — start_game exact seam
- `aamatch/placement.py` (full, 417 lines) — materialize, cleanup, sentinels, Phase-4 scope note
- `aamatch/engine.py` (full, 359 lines) — new_game/materialize, module state, candidates override
- `aamatch/wizard.py` (:1-270, :423-442) — GameWizard ctor, `_guard`, cleanup, activate
- `aamatch/capability.py` (full, 712 lines) — typing tables, `ligand_support`/`ligand_profile`
- `aamatch/__init__.py` (full) — menu entry, Gate A2, metadata block
- `aamatch/paths.py` (full) — `to_windows_path`, `package_data_path`
- `aamatch/geometry.py:81` — `GAME_PREFIX = '_aam_'`
- `aamatch/level_spec.py:41, 60-61, 89, 107-121` — version gates
- `aamatch/data/MANIFEST.json` (full) — demo-dev-1 / easy / benzamide + acetate
- `aamatch/wizard_text.py:200-264` — ERROR-line-last convention
- `tests/test_purity.py` (full), `tests/test_setup_state.py:1-100`, `tests/test_persistence.py` (test inventory)
- `.planning/STATE.md` (full), `.planning/ROADMAP.md:100-131`, `.planning/REQUIREMENTS.md:16-26`, `spec.md:1-60`
- `.planning/research/{FEATURES,PITFALLS,STACK,ARCHITECTURE,SUMMARY}.md` (targeted greps)
- `.planning/phases/02-headless-game-engine/02-08-SUMMARY.md`, `.planning/phases/03-wizard-gameplay-loop/03-05-SUMMARY.md`
- Prior art (borrowable, git-ignored): `tmp/bioCHEMeleon/biochemeleon/gui_setup.py:11, 47-96, 255-330, 619-686`

**Research date:** 2026-09-13. Own-repo, frozen-constants domain — no expiry concern beyond repo drift.
