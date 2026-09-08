# Phase 3: Wizard Gameplay Loop — MOVEMENT-MODEL SPIKE (research record)

**Researched:** 2026-09-08 (headless spike executed + verdict recorded)
**Domain:** PyMOL 2.5.0 transform primitives vs the Phase-2 stored-coordinate detector; `cmd.drag(wizard=0)` headless behavior; reset-to-grid semantics
**Confidence:** HIGH for every claim below that cites a `SMOKE-06` number — all were **empirically executed headlessly** on the real Windows PyMOL 2.5.0 conda build (`run_smoke.sh smoke/smoke_06_spike_movement.py 180` → `=== SMOKE-06 PASS ===`, all ~50 asserts green; full log retained in the run output). Source citations are `file:line` from the local PyMOL 2.5.0 tree and were **re-verified against the INSTALLED build's source printed by the spike itself** (identical for `wizard/dragging.py`).
**Spike artifact:** `smoke/smoke_06_spike_movement.py` (commit `09570e0`, `test(03): add movement-model spike probe`)

---

## 1. SPIKE VERDICT

**The movement model for Phase 3 is Option A, made precise: baked world-frame coordinate transforms on identity-matrix objects — `cmd.translate(v, obj, state=1, camera=0)` (what `engine.place_aa` wraps) and `cmd.rotate(axis, angle, selection=obj, camera=0, origin=C)` — and the object-matrix path is REFUTED, not merely disfavored.** The coordinate path provably satisfies all three gameplay requirements: (a) the moved pose lands in STORED coordinates, which is exactly what `geometry.extract_game_atoms`/`engine.detect()` read — SMOKE-06 scripted a qualifying TYR pose through a selection-form rotate + `place_aa` and `detect()` reported the `pi_stacking` record (`d_center=4.5000002`, `angle=2.6e-05 deg`, score 1.0); (b) `engine.reset_to_grid()` restores grid positions exactly (translation-only moves: worst per-atom dev 4.8e-07 Å vs tolerance 1.9e-06); and (c) the object matrix stays IDENTITY throughout (asserted after every bake), so **on-screen == stored == detected** by construction. The object-matrix path (`cmd.rotate(..., object=obj)`) fails all three: it writes only the TTT *display* matrix (state slot stays identity, coordinates untouched → the detector scores the OLD pose while the screen shows the new one: stored ring angle 0.000 deg vs on-screen 37.000 deg), and worse, any live TTT residue **conjugates every subsequent bake into the local matrix frame** (proven law: stored shift = R⁻¹·s, dev 2e-07) — under residue, `engine.place_aa` raises `PlacementError` and `engine.reset_to_grid` either silently ignores a matrix-only move (screen stays wrong) or fails closed when the stored pose is off-grid. `cmd.drag(wizard=0)` headless is benign at the API level (no exception, custom wizard kept, drag armed, nothing moves without a mouse) — but interactive whole-object dragging feeds the *matrix* path (the Dragging wizard reports "Dragging whole object" when `_drag` is empty), so native drag is admissible only as an interactive gesture layer behind a human checkpoint, with a matrix-identity assert after every drag session. **Recommended default for plans: game-driven baked transforms (panel buttons / keyboard nudges / scripted gestures through `cmd.rotate(selection)`+`cmd.translate`), reset = `engine.reset_to_grid()` spec replay (position replay), matrix identity asserted after every move.**

---

## 2. Probe results table (Q1–Q6)

Every "observed" cell is a printed number from the passing SMOKE-06 run.

| Q | Probe | Expected (hypothesis) | Observed (printed) | Verdict |
|---|-------|----------------------|--------------------|---------|
| **Q1** | `cmd.rotate(axis_vec, angle, SELECTION, camera=0, origin=ring_center)` — stored coords change? | Yes — selection form bakes coords (editing.py:1814-1819 builds a TTT and calls `transform_selection`) | max atom displacement **6.046 Å**; ring normal 79.606° → **0.000023°**; `get_object_matrix` **identity** throughout | **CONFIRMED** — pure world-frame bake, matrix untouched |
| Q1 | detect()/score see the moved pose? | Yes — detector reads stored coords | `pi_stacking` on placed object = **1**; `d_center=4.5000002`, `angle=2.6e-05 deg`, subtype P; `score_current == 1.0` | **CONFIRMED** |
| **Q2** | `cmd.rotate('axis', angle, object=obj, origin=C, camera=0)` — stored coords change? | No — object form writes only the display matrix (editing.py:1820-1832, `combine_object_ttt`) | coord disp **0.0** (exact); TTT display matrix = R_y(37°)-about-C (cos37=0.7986/sin37=0.6018 rows); **state slot (`incl_ttt=0`) stays identity** | **CONFIRMED** — matrix-only; two matrix slots exist |
| Q2 | Does detect() see the matrix move? | No — detector reads stored coords | pi records at grid+matrix = **0**; stored ring angle **0.000 deg** vs on-screen (M∘stored) **37.000 deg** | **CONFIRMED — detector blind to matrix moves** |
| Q2 | Read-back convention: does composing `get_object_matrix` with stored coords predict the on-screen pose? | TTT convention (editing.py:1985-1987): y = R·(p + m12..m14) + (m3,m7,m11) | dev **1.88e-07** (TTT layout; homogeneous layout identical here because the bottom row was (0,0,0)) | **PINNED** — `_apply_ttt` composition is the read-back rule |
| **Q3** | `cmd.transform_selection` semantics | Documented TTT layout bakes coords (editing.py:1946-2004) | coords baked; model fit **m1_documented** (y = R·(p−origin)+origin) with dev **1.39e-07** (m2 pre-ignored 0.94, m3 post-ignored 0.94, m4 transposed 1.32); matrix stays **identity** | **PINNED** — documented TTT semantics exact; pure coordinate bake |
| Q3 | `cmd.transform_object(name, M, homogenous=1)` (matrix_mode=−1 default) | Bakes coords (placement.transform_baked's proven form) | coords baked by +t (dev **2.38e-07**); **BUT leaves the applied matrix in `get_object_matrix` — BOTH incl_ttt=0 and incl_ttt=1 read exactly [I \| t]** | **REFINED** — bakes coords AND records the matrix (render semantics unverified → §6) |
| Q3 | `cmd.transform_object(...)` with `matrix_mode=1` | Matrix-only (docstring: "operates on the TTT (movie) matrix") | coord disp **0**; matrix **non-identity** | **CONFIRMED** — the duality hazard is real |
| **Q4** | `engine.reset_to_grid()` after a COORDINATE-path move — exact restore? | Yes for positions; orientation unknown | centroid restored (dev **1.8e-07** ≤ tol 2.1e-06); **per-atom residual 4.64 Å remains after a rotational move** (orientation NOT replayed); after a pure-translation move: per-atom exact (**4.8e-07 ≤ 1.9e-06**); matrix identity | **REFINED** — reset = POSITION replay (translate-only re-bake); rotations survive reset |
| Q4 | Matrix residue after a matrix-path move + re-bake — overwrite or compose? | Residue survives (translate never touches the matrix) | **SURVIVES**: after reset, M2 == M exactly (recorded 16 values); on-screen angle **37.000 deg** unchanged; detect sees clean grid | **CONFIRMED — matrix path is dangerous for reset** (two failure modes, §4) |
| **Q5** | `cmd.drag(sel, wizard=0)` headless | No exception; custom wizard kept; nothing moves | exception **None**; wizard kept (**ProbeWizard**); drag armed: `get_drag_object_name` **'' → '_aam_aa03'** (deactivate → ''); centroid drift **0**; button_mode **0→1** (edit=1 default) and deactivation does NOT restore | **CONFIRMED** (+ button_mode side effect, §3) |
| Q5 | `cmd.drag(sel, wizard=1)` — wizard replaced? | Per prior art: replaced/destroyed | **PUSHED on top of a stack**: `get_wizard_stack()` = **['ProbeWizard', 'Dragging']**; `Dragging.valid=1`; one `cmd.set_wizard()` pops back to ProbeWizard; **2 pops** to empty; the game wizard is NOT destroyed | **REFINED** — stack push/pop, not clobber (matches the C-source finding in 03-RESEARCH-wizard-interaction.md §1.2) |
| Q5 | Default `get_editor_scheme()` on stock PyMOL 2.5.0 | Unknown (roadmap demanded the record) | **1** (idle, fresh headless session; button_mode=0, matrix_mode=−1) | **RECORDED** |
| Q6 | When does the scheme gate (`!=3` → self-destruct, wizard/dragging.py:49-56) actually fire? | Prior art: "silently does nothing on scheme≠3" | **scheme tracks the ARMED-DRAG state, not the mouse ring**: idle scheme=1 → `Dragging().valid=0` (gate fires); **drag armed → scheme=3 → valid=1**; deactivated → 1; `edit_mode(1)` ring-flip alone → scheme stays **1** | **REFUTED the prior-art fear for this build** — `cmd.drag` arms the C-side drag BEFORE installing Dragging, so its own gate is self-satisfied (§3, §5.6) |

---

## 3. `cmd.drag(wizard=0)` headless behavior record + default editor_scheme

Environment recorded by the spike: PyMOL **2.5.0**, Python **3.9.13** (Windows conda, `C:\Users\nglok\.conda\envs\chemtools-win10\...`), installed `pymol/wizard/dragging.py` **identical** to the pymol-src snapshot the research cited (its `check_valid` source was printed verbatim by the spike).

### 3.1 `cmd.drag(sel, wizard=0)` (the API-level record; no mouse exists headless)

- **No exception.** No scheme gate is ever consulted (the gate lives in the Dragging *wizard*, which is not installed).
- **The game wizard survives** — `cmd.get_wizard()` still returns the custom instance after the call.
- **The drag IS armed**: `cmd.get_drag_object_name()` returns the object (`''` → `'_aam_aa03'`); `cmd.drag()` (no args) deactivates (`→ ''`). The `_drag` **selection lingers** after deactivation (`get_names('selections') == ['_drag']`).
- **Nothing moves** (centroid drift 0.0) — dragging requires real mouse events (HUMAN checkpoint, §6).
- **Side effect:** with the `edit=1` default, `cmd.drag` calls `edit_mode(1)` → `mouse('three_button_editing')` → the global `button_mode` flips **0→1**. Deactivation does **not** restore it. With `edit=0` there is no flip (observed 1→1 in the probe). (`edit_mode` at controlling.py:688-717; `mouse` re-programs the button map at controlling.py:609-686.)

### 3.2 `cmd.drag(sel, wizard=1)`

- The built-in `Dragging` wizard is **pushed on top of the wizard stack** (`['ProbeWizard', 'Dragging']`); the game wizard is dormant beneath, not destroyed. `cmd.set_wizard()` (the panel's "Done") pops **one** level — the game wizard **automatically resurfaces**. (Consistent with the C-source stack finding in the companion research doc §1.2; the v1 "re-install after drag" dance is unnecessary on 2.5.0.)
- The installed `Dragging` was **valid** (`valid=1`, `atom_count=0` → panel would read "Dragging whole object"). This matters: with `_drag` empty/whole-object, an interactive drag would mutate the **object matrix** — the refuted path (§4).
- The queued self-destruct (`cmd.do("_ cmd.set_wizard()")` in `check_valid`) never had to fire: see 3.3.

### 3.3 The editor_scheme law (Q6 evidence)

| State | `get_editor_scheme()` | direct `Dragging().valid` |
|---|---|---|
| fresh idle session (button_mode=0) | **1** | **0** (gate fires; self-destruct armed) |
| drag ARMED (`cmd.drag(sel, wizard=0)`) | **3** | **1** |
| drag deactivated | 1 | 0 |
| `edit_mode(1)` ring-flip alone (no drag) | **1** | **0** |

The scheme follows the **armed-drag C-side state**, not the mouse ring. Since `cmd.drag` executes `_cmd.drag(...)` (arming) *before* the wizard-install branch (editing.py:1059-1074), `Dragging.check_valid()` always sees scheme 3 on this build — **the gate is self-satisfied by cmd.drag's own arming and never fires during a real drag session**. Default idle value = **1** (this is "the default editor_scheme check" the roadmap demanded).

---

## 4. Reset semantics under each path (the matrix-residue question, answered)

**Coordinate path (recommended):** `engine.reset_to_grid()` is a **position replay** — per slot it re-bakes the centroid to `grid_pose.position + offset` via `cmd.translate(delta, camera=0)`.
- After a rotational move (align-rotate + place): centroid restored to **1.8e-07 Å** (tol 2.1e-06), detect back to 0 records, score 0.0, matrix identity — but the **per-atom orientation residual (4.64 Å) remains**: reset does NOT undo player rotations (SMOKE-04's Part C asserted centroids only; this spike extends the record).
- After a pure-translation move: **per-atom exact restore** (worst 4.8e-07 ≤ 1.9e-06).
- Matrix stays identity through everything (Phase-2 bakes never touch it — asserted at materialize and after every move).

**Matrix path (refuted) — two distinct failure modes, both proven:**
1. **Matrix-only move (stored coords still at grid):** `reset_to_grid()` **completes silently** (deltas ≈ 0; its internal centroid assert passes) while the TTT residue survives **exactly** (M2 == M, 16 values recorded) and the screen keeps showing the moved pose (ring angle 37.000 deg). Reset cannot see or fix the matrix — the engine's success is a false negative.
2. **Off-grid stored pose under residue** (what a failed `place_aa` leaves behind): the world-frame re-bake delta lands **conjugated** (local frame) → the centroid assert fails → `reset_to_grid` raises `PlacementError` ("baked centroid ... differs on axis 0 by 0.902003"). Fail-closed, but the game's Reset button would hard-fail.

**The conjugation law that explains both** (proven to 2e-07): with a live TTT display matrix M, every "bake" primitive (`cmd.translate`, `cmd.rotate` selection-form, `transform_selection`) applies the requested world transform T in the LOCAL frame: `stored_new = M⁻¹∘T∘M(stored_old)`; for pure translations, `stored_shift = R⁻¹·s` (observed (0.6018, 0, −0.7986) == R_y(−37°)·(0,0,−1) exactly). On identity-matrix objects (the Phase-2 invariant) local == world and everything behaves as Phase 2 proved.

**Fold-clear escape hatch (legal, no banned calls):** `cmd.matrix_copy(identity_matrix_donor, target)` — the spike used the game's own ligand object, whose matrix is identity-asserted — restores the matrix to identity (exact in the game probe; float32-tight ≈7.5e-08 noise on scratch), after which **translate is world-frame again (shift exactly (0,0,−1)) and reset fully recovers translation-only excursions** (worst 1.9e-06 ≤ tol 2.15e-06, detect 0). Caveat recorded: conjugated ROTATIONS leave orientation damage in stored coords that only re-materialization undoes.

---

## 5. Implications for plans

1. **Transform primitive standard.** All game movement goes through `cmd.translate(v, obj, state=1, camera=0)` and `cmd.rotate(axis, angle, selection=obj, camera=0, origin=C)` — the pair that bakes stored coordinates and provably leaves `get_object_matrix` at identity. NEVER `cmd.rotate(..., object=)`/`cmd.translate(..., object=)` (matrix-only), and avoid `placement.transform_baked`/`cmd.transform_object` in game paths: it bakes coords **but also records the applied matrix into `get_object_matrix` (both incl_ttt views)** — its render semantics are unverified (§6.2) and a matrix-bearing object breaks the engine (§4). If `transform_object` is ever used, follow with a `matrix_copy` fold-clear or at minimum an identity assert.
2. **Detection-composition rule (the PLAY-02 contract).** The detector reads STORED coordinates; the screen renders M∘stored. The game must therefore maintain **M == identity as a permanent invariant** — assert `get_object_matrix(obj)` is identity after every move (and treat any non-identity as a fail-closed game error). Under that invariant, on-screen == stored == detected *by construction*, and the PLAY-02 "result matches what is on screen" requirement holds without any matrix composition in the detector. (Read-back rule if ever needed: `_apply_ttt` — y = R·(p + m12..m14) + (m3, m7, m11); proven to 1.9e-07.)
3. **Reset rule.** Reset = `engine.reset_to_grid()` (position replay, exact for translations, silent no-op for orientation). Phase 3 must decide explicitly: (a) accept position-only reset — rotations persist (detection stays consistent; only the pose aesthetics carry over), or (b) full pose reset = re-materialize the level (`engine.materialize` rebuilds fresh objects — already proven headless). Recommend (a) for the Reset button plus an orientation-replay note in the help text, or (b) if "back to grid" must be visually exact. Either way: **assert matrix identity after reset** so failure mode §4.1 can never hide.
4. **Audit-gate interaction (correction to the phase premise).** The objective claimed the spike "may probe [banned calls] freely" from smoke/ — **that is wrong for CALLS**: `tests/test_code_audit.py::TestBannedCmdCalls.test_no_banned_call_sites` scans **both aamatch/ and smoke/** for `ast.Call` sites of `get_model`/`matrix_reset`/`get_object_ttt` (prose mentions are pinned only inside aamatch/). The spike complied — it used `cmd.get_object_matrix` (legal, and now fully characterized: the two-slot incl_ttt decomposition) and `cmd.matrix_copy` (legal) as the matrix-clearing primitive instead of the banned `matrix_reset`. **The winning movement path is clean of all banned calls** — `translate`/`rotate(selection)`/`place_aa`/`reset_to_grid` touch none of them. Future probe scripts must observe the same smoke/-level call ban.
5. **Wizard-stack integration for the wizard plan.** `cmd.set_wizard(wiz)` pushes; `cmd.drag(wizard=1)` pushes Dragging over the game wizard; panel "Done" pops and the game wizard resumes automatically (no re-install listener needed — better than the prior-art dance). The game should still verify stack depth after drag sessions (`pops_to_empty=2` in the spike when a game wizard sat beneath Dragging) and clean the lingering `_drag` selection.
6. **editor_scheme guard design (Q6 answer).** On PyMOL 2.5.0 **no Start-time editor_scheme guard is needed**: the gate cannot fire during a real drag session because cmd.drag's own arming sets scheme 3 (§3.3), and `cmd.drag(wizard=1)` restores the user's `button_mode` in the Dragging wizard's `cleanup()` (old_button_mode is captured at drag start). The hygiene the game DOES need: prefer `wizard=1` (restores button_mode) or pass `edit=0` (never flips it); never rely on `get_editor_scheme()` for game logic (it is drag-state-coupled, not a user setting); if a future PyMOL build tightens check_valid, a cheap Start-time read of `cmd.get_editor_scheme()` with a hint dialog is the fallback — record it as a contingency, not a requirement.
7. **Rotate-gesture semantics are safe.** `cmd.rotate(selection, origin=C)` follows the documented TTT semantics exactly (dev 1.4e-07) — a Phase-3 rotate gesture about the AA's ring center does what it says ON IDENTITY-MATRIX OBJECTS. (PART A's alignment step exercised exactly this primitive end-to-end: 79.606° → 0.000023°.)

---

## 6. HUMAN-CHECK-PENDING (headless cannot verify these; exact GUI steps)

1. **Interactive drag path + feel (the spike's declared boundary).** In a real PyMOL 2.5.0 GUI: start/materialize a game, select an AA, drag it with the mouse, then run a checker snippet asserting (a) `cmd.get_object_matrix(aa_obj)` is still identity (i.e., the drag took the COORDINATE path, not the matrix path), (b) `engine.detect()` reports the moved pose on Confirm, (c) Reset restores. **Watch the Dragging panel text**: "Dragging N atoms in object X" (coordinate path) vs "Dragging matrix for object X" (the refuted path — the headless probe saw the latter because `_drag` was empty). If whole-object drags take the matrix path interactively, the game must populate the drag selection (e.g. `cmd.select('_drag', aa_obj)`) before `cmd.drag`, or route all movement through panel/keyboard baked transforms.
2. **`transform_object` render-doubling question.** `cmd.transform_object(obj, [I|t], homogenous=1)` bakes coords by +t AND records [I|t] into `get_object_matrix` (both views). Does the RENDERER apply that recorded matrix (object visually displaced by **2t** — stored says t) or is it inert history? Steps: fragment an object, apply a +5 Å x-translation via `transform_object`, compare its on-screen position against an untranslated twin. (The game avoids `transform_object`, so this is diagnostic, not blocking — but it decides whether `placement.transform_baked` leaves a *visible* artifact and whether SMOKE-04's alignment step ever double-rendered.)
3. **Drag-session end-to-end with a populated `_drag`** (combine 1 with `cmd.select('_drag', aa_obj)` + `cmd.drag(sel, wizard=1)`): verify the panel shows the atoms path, the mouse gesture moves the WHOLE AA coherently, the game wizard resumes after Done, and `button_mode` is restored by the Dragging cleanup.
4. **Confirm the scheme law interactively once** (idle scheme should read 1 in the GUI; drag should work out of the box on the stock 3-Button Viewing ring) — a 2-minute sanity pass alongside check 1.

---

## 7. Open questions

1. **Renderer semantics of the transform_object-recorded matrix** (§6.2) — the one remaining unknown in the matrix model; the game's identity-matrix invariant makes it non-blocking.
2. **Why `get_editor_scheme()` tracks the armed drag** — empirically pinned (4-state table) but the C-side mechanism is unread (C source not in the local tree; only Python modules available). No gameplay impact on 2.5.0.
3. **Queued self-destruct flush timing** — the `cmd.do("_ cmd.set_wizard()")` queued by an invalid Dragging never flushed during headless scripts (corpse lingers); interactively the event loop presumably flushes it. No impact on 2.5.0 (the gate self-satisfies during drags); noted for completeness.
4. **`.pse` round-trip of a TTT display matrix** — remains the Phase-7 gate (STATE.md blocker, unchanged). This spike *shrinks* its importance: if the game never creates matrix residue, checkpoints only need baked coords (known-safe: atoms + sentinels round-trip, 02-13).
5. **Whether interactive whole-object dragging can be forced onto the coordinate path** via a populated `_drag` selection — §6.1/§6.3 human checkpoints; if it cannot, native drag is limited to per-atom "adjust" gestures and the panel/keyboard baked transforms carry the game.

---

## Sources

### Primary (HIGH — executed headlessly this session)
- `smoke/smoke_06_spike_movement.py` run log (all numbers in §2-§4; `=== SMOKE-06 PASS ===`, ~50 asserts; commit `09570e0`)
- Installed PyMOL 2.5.0 `pymol/wizard/dragging.py` source printed by the spike (identical to the snapshot below)

### Verified source (MEDIUM-HIGH — cited file:line, re-checked this session)
- `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/bioCHEMeleon/tmp/pymol-src/modules/pymol/editing.py` — `drag` (1018-1076), `get_editor_scheme` (1123-1131), `translate` (1610-1714), `rotate` (1716-1853), `transform_selection` (1946-2004), `transform_object` (2006-2056), `matrix_copy` (2058-2124), `matrix_reset` docstring (2126-2166)
- `.../pymol/querying.py` — `get_drag_object_name` (84-87), `get_object_matrix` (89-100)
- `.../pymol/wizarding.py` — set/get/pop wizard stack (110-174)
- `.../pymol/wizard/dragging.py` — check_valid (46-56), recount (26-40), cleanup (72-81)
- `.../pymol/controlling.py` — `mouse` (609-686), `edit_mode` (688-717), rings (185-229)
- Repo: `aamatch/engine.py`, `aamatch/placement.py` (POSE_TOLERANCE/FLOAT32_ULP_REL, translate_to, reset_to_grid), `aamatch/geometry.py` (stored-coords contract), `tests/test_code_audit.py` (smoke/-level call ban)

### Companion research
- `.planning/phases/03-wizard-gameplay-loop/03-RESEARCH-wizard-interaction.md` (same day; stack-native wizard lifecycle, pick routing, panel contract — consistent with §3.2's push/pop observation)
- `.planning/research/PITFALLS.md` Pitfall 6/12 (superseded in part: the "wizard clobber" is a stack push; the editor_scheme gate is self-satisfied on 2.5.0; the matrix-vs-coords duality is now quantified)

## Metadata

**Confidence breakdown:**
- Movement verdict: HIGH — every claim is an executed, printed headless result on the real target build
- cmd.drag record: HIGH for API-level state (executed); interactive feel explicitly deferred (HUMAN-CHECK-PENDING)
- Reset semantics: HIGH — both failure modes + the escape hatch executed end-to-end
- Renderer semantics of transform_object's recorded matrix: LOW/UNVERIFIED (headless cannot see pixels) — explicitly deferred, non-blocking

**Research date:** 2026-09-08
**Valid until:** stable — pinned to PyMOL 2.5.0 conda build; re-run SMOKE-06 if the PyMOL env changes

## RESEARCH COMPLETE
