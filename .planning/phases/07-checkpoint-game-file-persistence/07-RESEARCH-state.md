# Phase 7: Checkpoint & Game-File Persistence — Research: game-state inventory + sidecar design + sentinel-first reconstruction

**Researched:** 2026-09-21
**Domain:** What exactly must be persisted to fully reconstruct a running AA-match game; the checkpoint sidecar schema; sentinel-first reconciliation of sidecar vs loaded `.pse` atoms
**Confidence:** HIGH for every repo claim (read from source this session, file:line) and every `.pse` claim (SMOKE-17 probe + `07-RESEARCH-pse.md`, both committed). MEDIUM only where marked.

**Sibling research consumed (same phase, complementary scope):** `07-RESEARCH-pse.md` (`.pse` round-trip mechanics + wizard-pickle defect + SMOKE-17) and `07-RESEARCH-import.md` (Save/Import button flows, dialogs, timer-vs-modal, status lines). This doc answers the *what-state / what-format / how-reconcile* questions those two leave to it; conflicts between the three are called out explicitly (§7, §8).

---

## 1. State inventory — every piece of state, where it lives, what survives, what carries it

Legend: **Survives `.pse`?** = verified by SMOKE-17 (two-process round-trip, `smoke/smoke_17_pse_roundtrip.py`, committed + green per `07-RESEARCH-pse.md`) or [UNVERIFIED]. **Carrier** = the mechanism that restores it.

### 1.1 Engine module globals (die with the process — probe-proven)

SMOKE-17 B: `engine stays DEAD after load … engine._game=None` — "the `.pse` does NOT resurrect Python game state" (`07-RESEARCH-pse.md` verdict table; `aamatch/engine.py:129-132` declares the four globals).

| State | Lives | Survives `.pse`? | Sidecar? | Reconstruction |
|---|---|---|---|---|
| `_payload` — full level-spec payload (seed, levels, grids, required, detector stamp) | `engine.py:129` | **NO** | **YES** — embedded verbatim as the sidecar's game block `level_spec` | `parse_game_data` → payload → new engine adopt seam sets `_payload` (never regenerate — embed-don't-regenerate verdict, `game_file.py:17-20`) |
| `_registry` — materialize registry: `{'level_index', 'pre_game_names', 'molecules': [{molecule_id, offset, ligand: (name, ids), slots: {slot_id: (name, ids)}}]}` | `engine.py:130`; shape `placement.py:295-297` | **NO** | **YES** — identity ONLY (object names + sorted atom ids; **no poses** — coords ride the `.pse`) | sentinel-first rebuild from loaded atoms, reconciled against the sidecar rows (§4) |
| `_game` — the live `GameState` | `engine.py:131` | **NO** | **YES** — `GameState.to_dict()` verbatim | `GameState.from_dict` (lossless, SMOKE-17-proven: `GameState.from_dict lossless PASS`) |
| `_ligand_content` — `{file_key: record_text}` for uploaded games (advance_level's re-materialization input) | `engine.py:132`, consumed `engine.py:625` | **NO** | **YES** — `game_file.encode_ligand_files` base64 map | `game_file.decode_ligand_files` → sha256-verified by `parse_game_data` gate 5 (`game_file.py:202-250`) |

### 1.2 gamestart module state

| State | Lives | Survives `.pse`? | Sidecar? | Reconstruction |
|---|---|---|---|---|
| `_last_start` = `{'setup' (deep-copied), 'seed', 'candidates', 'ligand_content'}` — Restart's verbatim replay tuple (06-08) | `gamestart.py:184, 453-456` | **NO** (same module-state class as `engine._game`) | **YES** | rebuild the dict: `setup`/`seed` from the embedded game block; `candidates` from an additive sidecar key (see §2 — needed so uploaded-game Restart replays the right rows); `ligand_content` = decoded ligand texts. **Plus the payload-branch decision** (§2 note R; same conclusion as `07-RESEARCH-import.md` OQ-3) |

### 1.3 GameState fields — `to_dict` covers ALL of them (lossless, one call)

`aamatch/game_state.py:411-429` — `to_dict()` emits exactly 11 keys; `from_dict` (`:431-455`) is the inverse with accept-older `.get` defaults on the four 06-01 keys. None of these survive `.pse` (Python state).

| Field | Sidecar | Reconstruction note |
|---|---|---|
| `current_level_index`, `current_molecule_index` (`:184-185`) | YES | drives `GameWizard(payload, registry, level, molecule)` construction + which payload level the registry reconciles against |
| `molecule_scores` (list), `skip_count`, `giveup_count` (`:186-188`) | YES | direct |
| `timer_anchor` (float wall-clock) (`:189`) | **NOT authoritative** — meaningless across sessions (clock skew / app-closed time). Stored inside `to_dict` output as informational provenance only | re-anchor: sidecar carries `elapsed_at_save`; restore runs `GameState.rebase_timer(time.time(), elapsed_at_save)` (`game_state.py:212-243` — the P-4 single-anchor primitive; same recommendation as `07-RESEARCH-pse.md` §"What Phase 7 must do" item 5) |
| `formed_types_per_molecule`, `score_per_molecule` (`:190-191`) | YES | direct (`from_dict` coerces lists/floats) |
| `game_over`, `end_state`, `final_time` (`:192-194`) | YES | a game saved AFTER give-up/complete round-trips as over/inert (`final_time` frozen by `stop_timer`, `:245-267`) |
| `total_score` | derived (property `:201-204`) | nothing to store |

### 1.4 GameWizard attributes (all plain data — save-side pickle PROVEN clean)

SMOKE-17 A enumerated the live `__dict__`: `['_color_store', '_current_slot', '_end_state', '_error', '_event_seq', '_game_over', '_last_event', '_level_index', '_ligand_object', '_molecule_index', '_objects_by_slot', '_payload', '_registry', '_result', '_saved_msm', '_slot_by_object', 'cmd', 'menu', 'panel', 'prompt', 'session']` — zero Qt/locks/controller refs (contract 2 did its job; `07-RESEARCH-pse.md`). The **restore side is BROKEN as-shipped** (§6): base `__reduce__` calls `GameWizard()` argless → TypeError → Session-Warning → wizard dropped.

| Attribute | Lives | Survives `.pse`? (post-fix) | Sidecar wizard block? | Reconstruction |
|---|---|---|---|---|
| `_payload`, `_registry` | `wizard.py:142-143` | YES (pickle) | YES (game block + registry block) | adopt-or-rebuild; when both paths live, assert pickled `_registry` == reconciled registry (the `07-RESEARCH-pse.md` step-4 assert) |
| `_level_index`, `_molecule_index` | `:144-145` | YES | derivable from `GameState` | mirrors — `_sync_end_state`/construction keep them equal by construction |
| `_slot_by_object`, `_objects_by_slot`, `_ligand_object` | `:146-152` | YES | derivable | `wizard_core.build_slot_map(registry, molecule_index)` (pure, `wizard_core.py:64-120`) re-derives all three |
| `_current_slot` | `:153` | YES | YES | direct; on the rebuild path re-apply the highlight recolor (§4 step 7) |
| `_saved_msm` | `:154` | YES | YES | also the **msm repair** value for the rebuild path (§4 step 6: the session restores `mouse_selection_mode=0` — the value at save — not the user's pre-game value) |
| `_color_store` `{obj: [(ID, color), …]}` | `:155`; ops `wizard_core.py:166-200` | YES | YES | the snapshot of ORIGINAL colors is not derivable from the loaded scene (the scene carries the CURRENT — possibly highlighted — colors), so the sidecar copy is load-bearing on the rebuild path |
| `_result` | `:156` | YES | **skip** | always `None` in the advance flow (cleared by every advance/reset: `:438, :885`) |
| `_error` | `:157` | YES | YES (cheap) | direct |
| `_event_seq`, `_last_event` | `:159-160` | YES | YES | direct (keeps the tab poll's seq-distinct event semantics, `:401-409`) |
| `_game_over`, `_end_state` | `:161-162` | YES | derivable | mirrors of `GameState` — `_sync_end_state` (`:411-421`) refreshes them |
| base attrs `menu/prompt/panel/session` | `pymol/wizard/__init__.py:20-28,33-46` | YES (pickle) | skip | plain/harmless |

### 1.5 Scene/atom classes — ALL verified bit-exact by SMOKE-17 (no sidecar role)

From the committed SMOKE-17 verify-phase output (`07-RESEARCH-pse.md` verdict table): object names **exact**; baked coordinates **max_delta 0.0** (the matrix gate: baked coords ARE the movement model — `wizard.py:53-69` contract 5); sentinel `segi='AAM'`/`b=-999.0` **exact** (`placement.py:97-99`); atom `(object, id)` keys **360/360 identical**; per-atom colors **exact**; per-atom reps **exact**; camera view **bit-exact**; object matrices **exact** including a NON-IDENTITY probe (closes PITFALL 10's `[UNVERIFIED]` definitively — and makes the sidecar-matrix fallback moot for v1). Bonds: not separately diffed [UNVERIFIED-lite — atom-set identity implies them; optional `get_bonds` count assert in the gate smoke].

**Consequence for the sidecar:** it needs **NO per-AA poses, NO matrices, NO camera** — the `.pse` is the pose/display/camera store. This deliberately *refines* the `ARCHITECTURE.md:340-343` sketch (which listed "per-AA current pose + grid pose" in `state.json`): that listing was defensive pending the round-trip probe; the probe closed it. Grid poses already ride inside the embedded payload.

### 1.6 Session settings / tab / window

| State | Survives `.pse`? | Carrier |
|---|---|---|
| `mouse_selection_mode` — **0 at save** (the live wizard's defensive set, `wizard.py:195`) | YES (session settings) → restored as **0**, not the user's pre-game value | the pickled wizard's `_saved_msm` (adopt path: already correct; `cleanup()` on Done restores it) / sidecar `wizard.saved_msm` (rebuild path repair, §4 step 6) |
| GameTab `_timer` (1 Hz QTimer), `_last_status`, `_last_shown_elapsed`, `_timer_label`, `_required_label`, `_info_log` history | NO (the dialog is never pickled — `game_window.py:250-253`) | tab re-arm after load: reseed `_last_status = wiz.get_status()` (silent first poll observation — the `_begin_play` pattern, `game_window.py:321-328`), re-render labels, start/stop `_timer` iff not `game_over`; the log history is NOT reconstructed (it is a log, not game state) |
| `_countdown_timer`, `_pending_wizard` | NO | transient by design (P-1/P-2) |
| Setup window singleton `_window`, `setup_window._last_export` | NO | out of scope for game resume (Setup-tab concern, `setup_window.py:66, 942`) |
| Dormant user wizards beneath the GameWizard on the stack | YES (whole stack pickled, `wizarding.py:176-180`) | nothing to do — stock wizards unpickle natively |

---

## 2. Recommended sidecar design

**Container:** reuse the Phase-1 versioned container with the **already-reserved** kind — `persistence.py:37`: `KINDS = ('setup', 'level_spec', 'game', 'checkpoint', 'manifest')`. SMOKE-17 already wrote and re-read a snapshot through `persistence.save_container(path, 'checkpoint', …)` / `load_container(path, 'checkpoint')` (smoke lines 251, 364) — the container half is proven, zero new code.

**Schema home:** NEW pure module **`aamatch/checkpoint.py`**, registered in `PURE_MODULES` (`tests/test_purity.py:94-99`), owning: schema constants + `build_checkpoint_data` + `parse_checkpoint_data` (+ light validator) + `reconcile_registry` + zip I/O. Rationale: the repo's dominant pattern is ONE pure module per kind (`setup_state` → `level_spec` → `game_file`), each wrapping `persistence`'s container core; `zipfile` is ALREADY whitelisted in `ALLOWED_STDLIB` (`tests/test_purity.py:108-111` — anticipated for exactly this). *Alternative:* fold into `persistence.py` per the `ARCHITECTURE.md:70,89` sketch and v1's single-file precedent (v1 `persistence.py` held build/parse/apply + zip I/O, 279 lines) — viable, but it blurs the generic-container core with a kind-specific schema; the kind-specific module wins on consistency with `game_file.py`.

**Embed the FULL game-file data, not a diff.** The sidecar's `game` key carries the **complete `game_file.make_game_data` output** (`setup`, `seed`, `level_spec` = the payload verbatim, `ligand_files`, provenance; shape `game_file.py:22-34, 109-117`). Justification: (i) the payload is THE TRUTH and the only source of `required`/grids needed to resume scoring, hints and debriefs — it is NOT derivable from atoms; (ii) it makes the checkpoint self-contained (uploaded-game content travels inside — playable on a machine without the uploads); (iii) the entire `parse_game_data` five-gate chain is reused **verbatim** with zero new version logic (wrap: `game_file.parse_game_data(persistence.make_container('game', data['game']))` — the `make_level_spec_container` wrapping precedent, `level_spec.py:69-75`); (iv) size is a non-issue (base64 ligand inflation was already accepted for game files, `game_file.py:167-176`). A "minimal diff over the .pse" is impossible anyway: the spec (required/grids/seed) does not exist in the `.pse` at all, so there is nothing to diff against.

**Data dict (the container's `data`):**

```python
{
  'checkpoint_format_version': 1,     # refuse-newer gate (the GAME_VERSION pattern)
  'created_at': '2026-09-21T…',       # provenance, informational
  'generator': 'AA-match',            # provenance, informational
  'game': <make_game_data output>,    # setup, seed, level_spec(payload), ligand_files,
                                      # game_format_version — validated via parse_game_data
  'candidates': None | [rows],        # _last_start['candidates'] — uploads only (demo=None);
                                      # additive key so Restart-after-load replays the right rows
  'game_state': <GameState.to_dict()>,   # the 11 keys, verbatim (02-10 wrap-don't-reshape law)
  'elapsed_at_save': float | None,    # time.time()-anchor captured BEFORE the file dialog;
                                      # None = never anchored. The re-anchor authority.
  'registry': {                       # CURRENT LEVEL ONLY (only one level is ever materialized —
     'level_index': 0,                #   placement.py:64-66; advance_level collapses+rebuilds,
     'molecules': [                   #   engine.py:624-626 — future levels need no sidecar)
        {'molecule_id': 'mol-001',
         'offset': [x, y, z],
         'ligand':  ['_aam_lig1', [ids…]],          # tuple → list (JSON has no tuples)
         'slots':   {'r0c0': ['_aam_aa1', [ids…]], …}}]},
  'wizard': {                         # REPAIR block — used only when the pickled wizard did
     'current_slot': 'r0c2' | None,   #   not restore (identity mismatch / pre-fix sessions):
     'color_store': {'_aam_aa1': [[ID, color], …], …},
     'event_seq': 3,
     'last_event': {...} | None,
     'error': None,
     'saved_msm': 1},
}
```

Field-by-field provenance: `game` ← `engine._payload` + setup/seed from `gamestart._last_start` + `engine._ligand_content` (encoded) — exactly the `setup_window.export_game` assembly (`setup_window.py:105-112`) plus live-state extras; `candidates` ← `gamestart._last_start['candidates']`; `game_state` ← `engine.game_status()` (the sanctioned read op, `engine.py:690-697`) or `_current_game().to_dict()`; `elapsed_at_save` ← `max(0.0, time.time() - gs.timer_anchor)` captured in the wrapper before the dialog (the v1 doctrine, `PA-persistence.py:62-68`; human-verified that the tick's rebase freezes the clock under the dialog itself, `05-11-SUMMARY.md:66`); `registry` ← the live `engine._registry` minus `pre_game_names` (which has ZERO functional consumers today — grep: only docstrings/tests mention it — derive-or-empty on restore, resolving `07-RESEARCH-import.md` OQ-5); `wizard` ← a new additive public `GameWizard` books-snapshot op (plain-data dict; keeps the tab/engine from touching wizard privates, the 05-07/05-10 law).

**Explicitly OMITTED (with rationale):** per-AA poses / object matrices / camera view (`.pse` carries all bit-exactly — §1.5; the matrix fallback shape stays documented in `07-RESEARCH-pse.md` §Fallback for a future-format world, additive-`.get(None)`-skip); `pre_game_names` (no consumers); `_result` (always None).

**Note R (Restart-after-load, shared with `07-RESEARCH-import.md` OQ-3):** replaying `_last_start` through `start_game` regenerates — byte-identical for demo games at a fixed plugin build, **silently wrong for uploaded games** (`candidates=None` → bundled-manifest fallback, `engine.py:290-302`). Since the sidecar embeds the payload, the robust shape is the payload-branch restart (c2): `_last_start` gains an additive `'payload'` entry and Restart routes through the payload-direct seam when present. Both researchers independently land on this; the planner records it once.

---

## 3. Reconstruction model decision

| Model | Mechanism | Trade-offs |
|---|---|---|
| **(a) exact-scene restore** — the loaded `.pse` atoms are the truth; the sidecar repairs Python-side metadata | `cmd.load(.pse)` → sentinel sweep → reconcile sidecar registry ↔ atoms → rehydrate engine from sidecar | ✅ honors PITFALL 10's law ("source of truth = the atoms the player can click"); ✅ **zero pose data in the sidecar** (coords proven bit-exact); ✅ survives plugin reload (engine rehydrated from JSON, not module objects); ✅ load cost is I/O-only (no generation — the Generate < 30 s budget is not spent per load, PITFALL 15); ✅ gates the embedded spec on every load (stale detector refuses) |
| (b) full regeneration replay — `start_game(_last_start)` then re-apply saved poses | regenerate scene from setup+seed, then translate every AA to sidecar-stored poses | ❌ requires per-AA poses **and orientations** in the sidecar (orientation survives only as coordinates — storing them duplicates the `.pse`); ❌ regenerates at load (slow; manifest-dependent — Phase 8 will change MANIFEST.json and silently re-bucket the same seed, the exact regenerate_vs_embed refusal, `04-RESEARCH-export-upload.md`); ❌ a mid-play saved game with a changed detector would regenerate an unsolvable game instead of refusing |
| (c) hybrid | (a) for the scene, (b)'s inputs retained for Restart | ✅ this is really "(a) + embedded payload + payload-branch restart" — the recommended shape |

**Recommendation: (a)/(c) — exact-scene restore, with the full game payload embedded in the sidecar** (the embedded payload is what makes Restart and future Import reuse possible without regenerating the *restored* scene). The player-moved-AAs case is handled for free: moved/rotated coordinates ARE the saved atoms. The sentinel-first rule is satisfied literally: the registry is rebuilt FROM the loaded atoms and merely *checked* against the sidecar — a sidecar entry is never trusted over the scene.

---

## 4. Sentinel-first reconstruction plan

**What the reconstruction reads from the loaded `.pse`** (all selectors/mechanics probe-proven by SMOKE-17):

1. Game-object set: `geometry.game_object_names()` — prefix-only `_aam_` filter (`geometry.py:96-105`; the same rule `cleanup_game_objects` uses, `placement.py:451-453`).
2. Per object: sorted atom ids via one `cmd.iterate` pass (the `_sorted_ids` pattern, `placement.py:133-138` — uppercase `ID`, explicit `space=` dict) → `observed = {name: sorted_ids}`.
3. Sentinel verification per object: `cmd.count_atoms('%s and segi AAM and b < 0' % obj)` must equal `cmd.count_atoms(obj)` — the selector discipline is `b < 0`, never `b -999` (`placement.py:50`); SMOKE-17 ran exactly this per-object reconciliation post-load (`sentinel-first reconciliation … PASS`).

**Reconciliation (pure, dependency-injected — the v1 pattern simplified):** `checkpoint.reconcile_registry(sidecar_registry, observed)` takes plain dicts and returns the rebuilt registry + mismatch report. It is the v1 `reconcile_with_bcm` semantics (`PA registry.py:435-494`) adapted to AA-match's slot registry:

- **Match rule:** a sidecar registry entry `(molecule, role, slot_id) → (object, ids)` is KEPT iff `object` is in `observed` AND `sorted(observed[object]) == ids` (ids must match exactly — they are the identity contract, `placement.py:51-53`; SMOKE-17 proved ids stable 360/360).
- **THE NEVER-GHOST-ENTRY LAW:** an entry whose object/ids do not verify is **DROPPED, never registered** (v1 `missing_from_pse`: "NOT registered (ghost entry would corrupt counts…)" — a sidecar entry must never reference a non-existent atom). Reported, not fatal-by-itself.
- **Atoms without sidecar entries** (v1 `missing_from_bcm`): real, clickable atoms with no slot identity — reported; they cannot participate in play.
- **Completeness gate (AA-match-specific, stricter than v1):** the CURRENT level (`game_state.current_level_index`) must reconcile COMPLETELY — every molecule's ligand + all `n*n` slots verified — otherwise **refuse the resume** with a message naming the first missing piece. Rationale: unlike v1 (hiders on a pre-existing target; any survivor is playable), an AA-match scene without its slot map cannot route clicks and cannot score — "playable but without metadata" is not achievable for the current level without the spec. **Future levels need NOTHING**: only one level is ever materialized (`placement.py:64-66`) and `engine.advance_level` collapses + re-materializes the next from the payload (`engine.py:624-626`) — level-advance self-heals any damage.

**Degradation rules (sidecar missing — bare `.pse` loaded):**

- The shipped artifact is the zip (§7), so a sidecar-missing load only happens when a user deliberately extracts and opens the bare `.pse` (File→Open) or picks a stray `.pse` at the Load button.
- **File→Open path:** no plugin code runs; post-`__reduce__`-fix a same-identity session restores the wizard with full books, but the engine is dead — the first click lands `'engine: no live game -- call new_game(setup, seed) first'` on the panel via `_guard` (`engine.py:135-140`, `wizard.py:543-556`). Recovery = the Game tab's load affordance.
- **Load-button path with a bare `.pse`:** if a live same-identity `GameWizard` is on the stack → **degraded adopt** (prior-art "playable but without metadata" parity): rebind `engine._payload/_registry` from the wizard's own books, build a `GameState` carrying ONLY the positions (`current_level_index/current_molecule_index` from the wizard indexes), and print exactly what was lost (scores, counters, timer, `_last_start` → Restart refuses). Documented limits: one-record-per-molecule bookkeeping restarts empty (re-confirming a scored molecule becomes possible — accepted degraded semantics, matching v1's "all-hidden on sidecar-less reload"); `ligand_content=None` means an uploaded game fails closed at level advance (`placement.py:317-336` unknown synthetic key) — demo games advance fine. If NO wizard is on the stack → **refuse** with a clear message ("no AA-match metadata — open the `.aamatch` checkpoint file, not the bare `.pse`"). Never partially reconstruct in silence.
- **`.pse` game objects missing but sidecar present** (e.g. user deleted objects after saving, then loaded): the completeness gate above refuses with the named molecule/slot — never a ghost registry.

**End-to-end load order (cmd tier, refusal-first):**

1. Read zip + run ALL parse gates **before any scene mutation** (a foreign/corrupt file never touches the session) — `checkpoint.read_checkpoint_zip(path)` returns `(tmp_pse_path, data)` with `parse_checkpoint_data` already applied (v1 order: `read_bcmz` parses the sidecar before extraction hands off, `PA-persistence.py:216-248`).
2. Pop the live GameWizard if one is on the stack (its `cleanup()` restores msm/colors/pk1 — `wizard.py:198-223`) — `cmd.load` of a session replaces the stack without running the outgoing wizard's cleanup, so this must happen first.
3. `cmd.load(tmp_pse)` — full session replace (`load_pse` → `set_session(partial=0)`, `pymol-src/importing.py:823-832`; `partial=0` default). Restores objects + view (bit-exact) + the (fixed) pickled wizard stack.
4. Sentinel sweep + `reconcile_registry` → rebuilt registry (+ completeness gate).
5. Engine rehydrate via a new adopt seam (e.g. `engine.restore_game(payload, registry, game_state_dict, ligand_content)` — the seam name `07-RESEARCH-pse.md` proposes): set `_payload`, `_registry`, `_ligand_content`, `_game = GameState.from_dict(...)`, then `rebase_timer(time.time(), elapsed_at_save)` iff not `game_over` and elapsed is not None.
6. msm repair for the rebuild path: `cmd.set('mouse_selection_mode', wizard_block['saved_msm'])` when present (the session restored 0; the adopt path needs nothing — the restored wizard's `_saved_msm` is already the true value and its `cleanup()` will restore it).
7. Wizard: **adopt if same-identity GameWizard is on the stack** (post-fix pickle: books intact, highlight colors still on the atoms — verify `_current_slot` still resolves and `_registry` equals the reconciled registry); **else rebuild**: `GameWizard(payload, registry, level, molecule)` + apply the sidecar wizard block through a new additive public op (e.g. `resume_from(books)`) which re-applies the `_current_slot` highlight recolor, then `wiz.activate(replace=0)` — **NOT `activate_game`** (which anchors the timer from zero, `gamestart.py:365-381`; the resumed game re-anchors via rebase instead). Optionally re-run the hint recolor (candidate set is recomputable pure — `wizard.py:894-955` — cosmetic; planner's call).
8. `gamestart._last_start` rebuild (§1.2) — with the payload entry if Note R lands.
9. Tab re-arm: required label + level line + a `game_loaded`-style log line + `_last_status = get_status()` seed + `_timer` running iff not `game_over`.

---

## 5. Version-gate compliance (two-gates law applied to a THIRD artifact — never conflated)

The checkpoint runs a **gate chain of four distinct gates with distinct messages** (reuse, don't invent):

1. **Container header** — `check_container(raw, 'checkpoint')` (`persistence.py:61-88`): foreign magic → `not an AA-match file (magic=%r, expected %r)`; newer container → `unsupported AA-match format version %d (expected <= %d). Please update AA-match.`; misfiled kind → `expected an AA-match checkpoint file, found kind=%r`. Refuse-NEWER / accept-OLDER (additive-only).
2. **Data schema gate** — `checkpoint_format_version`, the `game_format_version` pattern (`game_file.py:135-143`): missing/invalid → `checkpoint data is missing or has an invalid 'checkpoint_format_version'`; newer → `unsupported checkpoint format version %d (expected <= %d). Please update AA-match.` Older accepted with `.get` defaults (additive evolution).
3. **Embedded game gates — replayed VERBATIM** by wrapping the `game` block: `parse_game_data(make_container('game', data['game']))` runs container check + `game_format_version` + `validate_state(setup)` + the full `parse_level_spec_dict` chain. **The `detector_version` EXACT-match gate applies to checkpoints**: a checkpoint saved by an AA-match whose detector stamp is not `DETECTOR_VERSION` refuses with the pinned message — `unsupported detector_version %r in level spec (expected %r): stale or newer game spec - regenerate it with a current AA-match generator` (`level_spec.py:116-121`). This is correct semantics (a stale detector makes the embedded spec unsolvable, not merely incomplete) and costs zero new code. Message-wording note: for a checkpoint the "regenerate" remedy reads as "re-save with a current AA-match" — acceptable v1 wording per the flows-research's own inventory analysis; do NOT build a catch-and-humanize layer (`_guard` shows `str(e)` verbatim).
4. **GameState block** — `from_dict`'s accept-older `.get` defaults (`game_state.py:439-454`) + a NEW light pure validator in `checkpoint.py` (fail-closed, FormatError naming the key): required base keys present (from_dict's seven direct `data['…']` indexes would raise bare KeyError otherwise — wrap them); `len(molecule_scores) == len(score_per_molecule)` (the one-record invariant, `game_state.py:284-302`); every `L{i}M{j}` key within the embedded payload's level/molecule bounds (the `endgame_summary` overflow-check pattern, `game_state.py:374-396`); `elapsed_at_save` ≥ 0 (a negative would rewind the clock — `rebase_timer` already refuses, `:238-243`; clamp at capture with `max(0.0, …)`).
5. **Registry/wizard blocks** — additive-only reads with `.get` defaults; unknown keys preserved (the P9 passthrough law, `level_spec.py:46-48`).

**Refusal behaviors:** every gate raises `FormatError` (ValueError family) BEFORE any scene mutation (step 1 of §4); the tab `_guard` boxes it verbatim; smokes assert exact messages (the flows-research refusal-inventory table covers the game-file gates verbatim; the two new wordings above are the only additions).

---

## 6. Plugin-reload & module-identity analysis (criterion 3's "restore works after a plugin reload")

**The identity mechanism:** the session pickles the wizard stack with the class recorded **by module path** — `Wizard.__reduce__` = `(self.__class__, (), self.__getstate__())` (`pymol/wizard/__init__.py:34-36`), and pickle stores `cls.__module__`. Installed plugins import as `pmg_tk.startup.<name>` (`pymol/plugins/__init__.py:423-428`: `mod_name = parent.__name__ + '.' + name`, auto-imported at GUI startup); the dev/smoke loop imports as `aamatch` (AGENTS.md gate 5: NEVER mix both identities in one session — two module objects make every `isinstance` gate fail across the boundary).

**The as-shipped defect (must-fix, criterion 3):** base `__reduce__` reconstructs via `GameWizard()` **with no args** → `GameWizard.__init__` requires `payload, registry` (`wizard.py:140`) → `TypeError` inside `session_restore_wizard` → caught → `"Session-Warning: unable to restore wizard."` printed → **the wizard is dropped from the restored session** (`pymol/wizarding.py:182-196`; SMOKE-17-observed live: `__init__() missing 2 required positional arguments: 'payload' and 'registry'` + the warning line). This double-violates criterion 3 (wizard lost + console noise). **Fix shapes:** (i) the SMOKE-17-PROVEN argless rebuilder — module-level `_rebuild_game_wizard(): return object.__new__(GameWizard)` + `__reduce__` override returning `(that, (), self.__getstate__())`; `__init__` never runs, state arrives via `__dict__.update`, `session_restore_wizard` rebinds `.cmd` — proven through the REAL task path (`session_save_wizard` → `pickle.loads` → rebind → `set_wizard_stack`) with `get_status()`/`_current_slot`/`_event_seq`/`_color_store`/`_payload`/`get_panel()` all equal (`07-RESEARCH-pse.md` phase-A part C); (ii) the flows-research's init-with-args `__reduce__` (real `__init__` runs with pickled plain-data args, then the state dict applies on top) — analyzed, not probed. **Recommend (i)** — probe-proven; (ii) is the documented fallback if (i) surprises (e.g. future `__init__` side effects).

**Consequence — the two restore paths (§4 step 7):** after the fix, a SAME-identity save/load restores a fully-armed wizard (adopt path: no rebuild, no cleanup churn, highlight/hint colors intact on the atoms). A CROSS-identity load (repo-identity save opened in an installed session, or vice versa; or a plugin reload creating a second module object) fails the unpickle → caught → warning → wizard dropped → **the sidecar `wizard` block is the repair path** (rebuild + `resume_from` + msm repair). This is precisely why the sidecar carries the wizard books even though the pickle usually does. Defense-in-depth note: the installed-identity round-trip itself is [UNVERIFIED] (SMOKE-17 ran repo-identity only; `07-RESEARCH-pse.md` UNVERIFIED-2) — the human checkpoint covers it, and the repair path makes even its failure survivable (console warning aside).

**Detecting a foreign-identity GameWizard on the stack** (for the pop step): `isinstance` against the current module's class fails across identities; use the identity-agnostic predicate `type(w).__name__ == 'GameWizard' and type(w).__module__.endswith('aamatch.wizard')` — matches both `aamatch.wizard` and `pmg_tk.startup.aamatch.wizard` (any pickle-resolved instance must live under one of those two paths). Pop it (cleanup runs, msm/colors restored), then push the rebuilt wizard.

**Why reconstruction must live where it lives:** the pure half (schema, gates, reconcile, zip) goes in `aamatch/checkpoint.py` — module-identity-immune plain data, WSL-testable. The cmd half (sweep, `cmd.load`, engine adopt, wizard adopt/rebuild, `_last_start`) goes in **`gamestart.py`** beside `start_game`/`activate_game`/`compose_molecule_view` (it already owns the lifecycle seams and the `_last_start` store; the flows-research independently places `start_game_from_payload` there). The Qt tier never writes engine globals (the 05-07/05-10 law). The wizard needs exactly two additive public ops: the books-snapshot (for the sidecar) and `resume_from` (rebuild path).

**Entry-point signatures (proposal):**
- `gamestart.capture_checkpoint_snapshot()` → plain dict (elapsed + game_status + wizard books) — called by the Save wrapper BEFORE the dialog.
- `gamestart.save_checkpoint(path, snapshot)` → summary str — cmd.save to a Windows temp path → `checkpoint.write_checkpoint_zip(final, data, tmp_pse)` (temp zip + `os.replace`, the `write_json_atomic` pattern, `persistence.py:91-113`) → unlink temp.
- `gamestart.load_checkpoint(path)` → summary str — raise ValueError family (wrapper boxes); the full §4 order.
- `gamestart.start_game_from_payload(payload, ligand_content, setup, seed, activate=False)` — the Import seam (`07-RESEARCH-import.md` I3) which also serves Restart's payload branch (Note R).

---

## 7. Zip vs sibling layout

**Recommendation: ONE zip archive, `.aamz`, containing `game.pse` + `state.json`** (the sidecar JSON, whose content is §2's schema).

Evidence for zip: (i) the ROADMAP criterion-1 wording itself — "Save writes the zipped `.pse` + JSON-sidecar container" (`.planning/ROADMAP.md:190`); (ii) the recorded architecture artifact — "`<name>.aamz` = zip containing `game.pse` + `state.json`" (`ARCHITECTURE.md:340-343`) and the research summary's "v1 `.bcmz` → `.aamz` pattern" (`research/SUMMARY.md:28`); (iii) the shipped v1 precedent — `write_bcmz`/`read_bcmz` with fixed member names `'game.pse'`/`'game.bcm'`, tempfile extraction, missing-member refusals (`PA-persistence.py:195-248`); (iv) single-artifact integrity: the pair cannot be separated by a file move/share, and there is no cross-file atomicity problem (the zip is written atomically via temp+replace; the `.pse` inside was already complete when zipped). The one sibling advantage — PyMOL-native File→Open on the `.pse` — is a **liability** for a checkpoint: opening the bare `.pse` yields exactly the degraded/broken half-state (engine dead, wizard-only), which the zip steers users away from. (Note: `07-RESEARCH-pse.md` §"Where checkpoint files live" sketches sibling files; this doc resolves that conflict in favor of the roadmap/architecture/v1-aligned zip. Also its `.pse`-compression note stands: "zipped" means OUR zip — `session_compression` is deprecated, `exporting.py:466-473`.)

Mechanics: Save = sidecar assembled pre-dialog → `cmd.save(to_windows_path(tmp.pse))` (temp minted inside the Windows process — no WSL conversion needed) → zip members `game.pse` (from temp) + `state.json` (from the assembled dict, `zf.writestr`) at the final path via temp+`os.replace` → unlink temp `.pse`. Load = read zip, parse gates, extract `game.pse` to a `tempfile.mkdtemp` dir, `cmd.load`, reconstruct, best-effort `rmtree`. Refusals mirror v1: `not an AA-match archive (missing state.json)` / `archive missing game.pse (cannot reconstruct)`. `paths.py` needs no new helpers (QFileDialog paths route through `to_windows_path` unchanged, `paths.py:20-51`).

**Load affordance (cross-reference):** `07-RESEARCH-import.md` OQ-1 recommends ONE Import button dispatching on file kind (`.aamatch.json` game vs `.aamz` checkpoint) — the v1 one-button model and the only affordance `spec.md:39-47`'s inventory supports. This doc has no conflict with that; the dispatch reads the container `kind` (`'game'` vs `'checkpoint'`), so kind-sniffing is header-exact, not extension-guesswork.

---

## 8. Open questions for the planner

1. **`__reduce__` fix shape** — argless rebuilder (SMOKE-17-proven, recommended) vs init-with-args (`07-RESEARCH-import.md`). Either way it is a MUST (gate 3), with a headless pickle probe + the phase smoke flipping SMOKE-17's documented-defect pin to the strict restore compare.
2. **Checkpoint-load affordance** — one Import button with kind dispatch (recommended by `07-RESEARCH-import.md` OQ-1; consistent with this doc) vs a separate Resume button.
3. **Save gating on a panel-ended game** (wizard live-but-inert, `game_over=True`): allow-and-roundtrip (lossless — `game_state` carries the end fields) vs refuse with the pinned `'The game is over.'` (`wizard.py:569`). `07-RESEARCH-import.md` S2-1 leaves this open; allowing is simpler.
4. **`cmd.save` scope** — whole session `'(all)'` (faithful resume incl. user objects; recommended here) vs game-only `'segi AAM'` (lean; `07-RESEARCH-import.md` OQ-4 leans scoped). Settings/wizard blobs ride either way (`exporting.py:442-455` runs all session-save tasks unconditionally). Decide with one smoke assert; note that with `partial=0` full-replace load, a scoped save means user objects vanish on resume.
5. **Hint re-color after a rebuild-path restore** (cosmetic; recomputable pure candidate set) — polish task or accepted loss.
6. **Bond round-trip belt-and-braces** — optional `get_bonds` count assert in the phase smoke ([UNVERIFIED-lite], §1.5).
7. **Naming details** — `elapsed_at_save` vs `timer_elapsed` key name; sidecar member name `state.json` (architecture-recorded) vs `checkpoint.json`; default Save filename + filter wording (04-RESEARCH OQ-5 precedent); the `game_loaded` log line wording (new — the two reserved lines `game_saved`/`game_imported` are pinned by `05-RESEARCH-status-surface.md:290-291`, a load line needs the same handler-logged, non-poll treatment).
8. **Restart payload-branch (Note R)** — one decision covering Import AND checkpoint (both researchers converge on c2; it touches `_last_start`'s pinned key set — SMOKE-11 PART-H evolution).
9. **Degraded sidecar-less adopt** (§4) — confirm the accept-with-console-message semantics (prior-art parity) vs hard refusal at the human checkpoint.

## Sources

### Primary (HIGH)
- `smoke/smoke_17_pse_roundtrip.py` + `07-RESEARCH-pse.md` (committed, gate PROVEN): all `.pse` round-trip rows, wizard pickle defect + fix proof, engine-stays-dead proof, sentinel selector post-load proof, `GameState.from_dict` lossless proof.
- `aamatch/`: `engine.py:129-132,267-332,624-626,690-697`; `game_state.py:184-194,201-204,206-267,284-302,374-396,411-455`; `gamestart.py:184,365-381,424-464`; `wizard.py:53-69,140-162,173-196,198-223,401-421,423-461,504-541,543-556,894-955`; `wizard_core.py:64-200`; `placement.py:50-53,64-66,84-99,133-138,190-231,234-412,415-455`; `persistence.py:34-58,61-88,91-142`; `game_file.py:17-34,81,109-164,167-250`; `level_spec.py:37-56,98-125`; `geometry.py:81-105,108-158,232-264`; `paths.py:20-63`; `game_window.py:130-133,245-253,302-328,344-394,658-716,765-786,836-855`; `setup_window.py:66,86-117,880-960`; `__init__.py:16-39`; `status_text.py:260-265`.
- `pymol-src` (2.5.0 line): `wizarding.py:176-196`; `wizard/__init__.py:15-46`; `importing.py:130-166,823-832`; `exporting.py:370-475,782-840`; `viewing.py:1141-1150`; `cmd.py:43-53`; `plugins/__init__.py:38-53,255-297,423-428`.
- Prior art (shipped v1): `biochemeleon/persistence.py:1-279` (sidecar schema, capture doctrine, `.bcmz` zip I/O, `resolve_target`); `biochemeleon/registry.py:418-494` (sentinel reconstruction + reconcile_with_bcm mismatch semantics); `biochemeleon/game.py:320-360` (`reconstruct_registry`/`import_state` order).
- Planning: `.planning/ROADMAP.md:185-197`; `.planning/REQUIREMENTS.md:62-70`; `.planning/research/PITFALLS.md:242-273` (PITFALL 10) + `:533` (prior-art pointer); `.planning/research/ARCHITECTURE.md:67-70,183-200,335-350`; `.planning/research/SUMMARY.md:28`; `tests/test_purity.py:94-111`; `smoke/run_smoke.sh:1-17`.

### Secondary (MEDIUM)
- `07-RESEARCH-import.md` (flows/dialogs/refusal inventory — consumed and cross-checked; conflicts resolved in §2/§7/§8).
- v1 `resolve_target` name-preservation inference (object names survive `.pse`) — superseded by SMOKE-17's direct name-equality proof.

### Metadata
**Confidence breakdown:** inventory HIGH (direct source + probe); sidecar design HIGH (container+gates proven, schema is composition); reconstruction HIGH (v1-proven semantics + SMOKE-17 mechanics); version gates HIGH (existing code reused); identity analysis HIGH for the defect/fix (probe), MEDIUM for installed-identity round-trip ([UNVERIFIED], human-checkpoint item).
**Research date:** 2026-09-21. **Valid until:** phase planning window (mechanics probe-frozen; revisit only if PyMOL build changes).
