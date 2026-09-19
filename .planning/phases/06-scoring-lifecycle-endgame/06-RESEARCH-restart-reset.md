# Phase 6: Scoring Lifecycle & Endgame — RESEARCH (Restart/Reset slice: SCORE-09, SCORE-10)

**Researched:** 2026-09-20
**Domain:** Restart/Reset semantics of the AA-match PyMOL plugin (gamestart seam, wizard reset mechanics, Game status tab button wiring, endgame-recovery interplay)
**Confidence:** HIGH (all claims cite file:line in this repo's sources; no training-data claims used)

**Sources:** every claim below is verified against the repo copy at the cited file:line — `aamatch/gamestart.py` (424 lines), `aamatch/wizard.py` (710), `aamatch/engine.py` (478), `aamatch/game_state.py` (277), `aamatch/game_window.py` (371), `aamatch/setup_window.py` (1038), `aamatch/placement.py` (455), `aamatch/backup.py` (248), `aamatch/status_text.py` (180), `aamatch/wizard_text.py`, `aamatch/setup_state.py:90-144`, `smoke/smoke_08_starter.py`, `smoke/smoke_11_window.py`, plus `.planning/STATE.md` decision entries (line-cited), `03-03/03-06/05-05/05-06/05-08/05-09-SUMMARY.md`, `.planning/research/PITFALLS.md` (PITFALL 6 §156, PITFALL 9 §218-238), `spec.md:33-58`, `ROADMAP.md:160-171`.

---

## (1) Current-State Map

### The Restart source: `gamestart._last_start`

| Item | Evidence |
|---|---|
| Declared module-level, initialized `None` | `aamatch/gamestart.py:178` (`_last_start = None`) |
| **Capture point** | `aamatch/gamestart.py:413-416` — inside `start_game`, AFTER `cleanup_game_objects()` (:382), `engine.new_game` (:384-385), `engine.materialize` (:386-387), the fresh `GameWizard(payload, registry, 0, 0)` construction (:388), and the full compose (`_move_ligand_in_front` :405, `_frame_ligand_above_grid` :406, `cmd.zoom` :407) — and BEFORE the `if activate:` branch (:417-418). So BOTH the default (activate=True) AND the deferred (activate=False) paths capture. On the deferred (window/Start) path the capture lands at PREPARE time, before the countdown, while the wizard is still OFF the stack — "BEFORE any wizard mutation" (gamestart.py:409-412) holds because P-1 (wizard-free countdown, game_window.py:37-41) guarantees nothing mutates it pre-GO. |
| Exact keys | `gamestart.py:415-416`: `{'setup': copy.deepcopy(spec), 'seed': seed, 'candidates': candidates, 'ligand_content': ligand_content}` — exactly 4 keys (pinned by SMOKE-11 PART H: smoke_11_window.py:835-838 `sorted(ls) == ['candidates','ligand_content','seed','setup']`). |
| Deep-copy proof | `gamestart.py:414-415` (`import copy; _last_start = {'setup': copy.deepcopy(spec), ...}`) + aliasing proof pinned in smoke_11_window.py:839-844 (`ls['setup'].get('allowed_interactions') is not sentinel['allowed_interactions']`). The `spec` captured is `dict(setup or DEFAULTS)` (gamestart.py:383) — for a Start with `setup=None` the captured setup is `dict(DEFAULTS)`, never None. |
| **Lifetime** | Module-level → survives EVERYTHING within one PyMOL session: Done/pops, `cleanup_game_objects`, Give Up, mid-game cleanups, count-down cancels. **NEVER cleared by production code** — the only production write is the re-capture on every successful start (gamestart.py:413-416); a FAILED start leaves the store holding the last successfully BUILT game's tuple (gamestart.py:373-376 docstring "a failed start leaves the store holding the last successfully BUILT game's tuple"). Cleared only manually in smoke restore (smoke_11_window.py:882 `gamestart._last_start = None`). |
| Replay safety (repeated Restarts) | `setup_state.validate_state` returns `clean = copy.deepcopy(DEFAULTS)` — a completely fresh dict rebuilt field-by-field (setup_state.py:106-144; its own list rebuilt :134-135, upload dict fresh :142). So the deep-copied `_last_start['setup']` is only ever READ through the validation path — the source cannot be corrupted by repeated replay. `engine.new_game` also `dict(row)`-copies candidate rows (engine.py:273). |
| Not a v1 backup object | `gamestart.py:137-140` ("NOT a v1-style backup object -- the materialization inputs fully regenerate the scene, so no backup machinery is ported"); `05-05-SUMMARY.md` key-decisions ("_last_start lives in gamestart, never in the window's _last_export"). |
| Recorded decision | `STATE.md:183` (05-05): "Phase-6 Restart replays it verbatim through start_game (NOT a v1-style backup object; the input tuple fully regenerates the scene)". |

### Reset mechanism: `placement.reset_to_grid` / `engine.reset_to_grid` / `wizard.reset_grid`

| Layer | Evidence | What it does |
|---|---|---|
| `placement.reset_to_grid(payload, registry, level_index=0)` | placement.py:415-439 | For each (reg_mol, mol) pair of the level's registry × payload (the zip covers **ALL molecules of the current level** — placement.py:425-426), for each slot: current centroid = `geometry.centroid_of(aa_name)` (baked world-frame coords), target = `effective_position(slot['grid_pose']['position'], offset)` (placement.py:119-130 — spec pose + the per-molecule placement offset), then ONE `cmd.translate(delta, aa_name, state=1, camera=0)` (placement.py:437) and `_assert_pose` within `POSE_TOLERANCE=1e-6` + per-axis float32-ulp slack (placement.py:84-95, :171-188). **Never matrix_reset** (probe-proven reverter; placement.py:418-420). |
| `engine.reset_to_grid()` | engine.py:343-352 | Reads `_current_registry()` (EngineError when `_registry is None` — engine.py:115-120) + fails closed when `_payload is None` (:347-350); delegates with `level_index=registry['level_index']` (:351-352). **Touches NOTHING module-side**: `_payload`/`_registry`/`_game` are read-only here; only PyMOL coordinates move. |
| `wizard.reset_grid()` / `_reset_grid_impl` | wizard.py:586-610 | `public reset_grid -> _guard(_reset_grid_impl)` (:602). Impl: `engine.reset_to_grid()` (:606), then **identity-matrix assert for every recolored-slot object** (`wizard_core.snapshot_objects(self._color_store)` loop :607-608 — `wizard_core.snapshot_objects` is SORTED per STATE.md:121), then `self._result = None` (:609), then `cmd.refresh_wizard()` (:610). **Selection (`_current_slot`) + its recolor PERSIST** (wizard.py:601 docstring "the current SELECTION + its recolor PERSIST (only positions reset)"); `_color_store` is NOT touched (only `_result` cleared). |
| Position-only decision (option a) | wizard.py:587-595 docstring; `03-03-SUMMARY.md:36`; `STATE.md:128` | ROTATIONS PERSIST (detection stays consistent — SMOKE-06: detect returns 0 records on-grid even with the 4.64 Å orientation residual). Re-materialize (option b) REJECTED: rebuilds objects/registry mid-game, invalidating the pick map + color snapshots. |
| PITFALL 6 conformance | PITFALLS.md §156 ("reset must reset the same mechanism that moved the atom") | The same mechanism = baked world-frame `cmd.translate(..., state=1, camera=0)` — movement (`wizard.py:451-542`) and reset (`placement.py:437`) both translate baked stored coords on identity-matrix objects. Reset re-bakes via the identical primitive, and the identity assert after replay proves the matrix invariant held. |

### GameTab current button inventory (pre-Phase 6)

| Item | Evidence |
|---|---|
| GameTab ships **ONE connected button: Hint** | `aamatch/game_window.py:119-126` (`self.btn_hint` + `clicked.connect(self._on_hint)`). No Confirm/Skip/GiveUp/Save/Restart/Reset/Import buttons exist on the tab yet. |
| The reserved button-row slot | game_window.py:84-87 (class docstring): "the later phases' game-lifecycle button rows (Confirm/Skip/Save/Restart/Reset/Import arrive with Phases 6/7, research OQ-1 later-add recommendation) never reflow the timer row" — the row was built with `btn_row.addStretch(1)` (:124) so additions don't reflow. |
| Import button | Reserved for Phase 7 (ROADMAP.md:177-178 Phase 7 depends on Phase 5 "game tab / Import button"; spec.md:39). |
| Confirm button | Lives on the **wizard PANEL** today (`wizard_text.py:54-55`: panel buttons 'Confirm' → `cmd.get_wizard().confirm_molecule()` and 'Reset to Grid' → `cmd.get_wizard().reset_grid()`). The spec ALSO wants a Confirm on the Game tab (spec.md:41) — SCORE-01's plan scope. |
| Skip/Give-up dropdown | spec.md:42-44 — another Phase-6 plan's scope; not wired today. |
| Setup tab's OWN "Reset" button | `aamatch/setup_window.py:208-209` (`btn_reset`, spec.md:21-22 "Reset: restore the default settings") — a DIFFERENT Reset (game-setup defaults) on the Setup page. Name-collision note for smokes/asserts below (§7). |

### The 05-09 start-sequence shape Restart mirrors

| Item | Evidence |
|---|---|
| `_start_impl` deferred sequence | setup_window.py:953-1027: collect → build_state pre-checks → Decision-4 seed policy (:1006-1019) → `_pop_game_wizard()` (:1020, P-3) → `gamestart.start_game(setup=state, seed=..., candidates=..., ligand_content=..., activate=False)` (:1021-1024) → `tabs.setCurrentWidget(game_tab)` (:1025) → `game_tab.start_countdown(wiz)` (:1026) → return wiz (:1027). |
| `_pop_game_wizard` | setup_window.py:826-845: `isinstance(cmd.get_wizard(), GameWizard)` gate → canonical `cmd.set_wizard()` None-pop (popped wizard's own cleanup runs; prior wizard auto-resumes; a USER wizard is never popped) → returns popped-bool. Deletion excluded — start_game's own cleanup-first law does the deleting (:836-839). |
| `_on_cleanup` cancel-first (P-2) | setup_window.py:864-881: `game_tab.cancel_pending_start()` FIRST (:875), then `_guard(self._cleanup_now)`. |
| Restart expectation recorded | `05-09-SUMMARY.md` frontmatter affects: "phase-06 game lifecycle (restart replays start through this same sequence)" — the deferred sequence IS the sanctioned Restart shape. |
| Double-Start hazard solved | `STATE.md:245` (04-15 step 8): "double-Start restarts cleanly"; mechanism = every `start_countdown` cancels any pending countdown FIRST (self-healing, game_window.py:172 `self.cancel_pending_start()` at the top of `start_countdown`). |
| Give Up / endgame | NOT implemented — SCORE-06/SCORE-07 are Phase-6 requirements with zero existing code (grep: no "give" in aamatch/). The wizard panel has Confirm/Reset-to-Grid/Done only (wizard_text.py:53-59); `status_text.EVENT_KINDS` reserves `gave_up` (:68-69) + `game_reset` (:71-72) + `game_restarted` (:72) + `molecule_scored`/`molecule_skipped`/`level_advanced` as Phase-6 kinds (status_text.py:66-72; 'result' is NEVER fingerprinted — status_text.py:151-155). |

---

## (2) Answers to the 8 Questions

### Q1. `gamestart._last_start` — capture, keys, deep-copy, lifetime; the Restart call; mid-game `start_game` behavior

**Capture point / keys / deep-copy / lifetime:** see the map table §1. Verbatim call shape: `_last_start` keys are EXACTLY the first four kwargs of `start_game(setup=None, seed=42, candidates=None, ligand_content=None, activate=True)` (gamestart.py:342-343) — so a Restart replay is literally `start_game(**_last_start, activate=False)` for the deferred path, or with explicit kwargs `start_game(setup=ls['setup'], seed=ls['seed'], candidates=ls['candidates'], ligand_content=ls['ligand_content'], activate=False)`. `ls['setup']` is always a real dict (never None — the capture holds `dict(setup or DEFAULTS)`, gamestart.py:383).

**Mid-game `start_game` (deferred/window path — the 05-09 shape), step by step:**

1. The window's Restart impl calls `_pop_game_wizard()` FIRST (P-3, setup_window.py:836-839): the LIVE GameWizard is popped via canonical `cmd.set_wizard()`; its `cleanup()` runs inside the C-layer pop — msm restored to snapshot (wizard.py:196-197), unpick + pk1 delete-if-present (:198-200), deselect (:201), **every recolored slot's colors restored then `_color_store.clear()`** (:202-204). The stale wizard's `_slot_by_object` registry now points at objects that step 2 is about to delete — the pop puts it OFF the stack so countdown-window clicks can never reach it (P-3 rationale, setup_window.py:836-839).
2. `start_game(..., activate=False)`: `placement.cleanup_game_objects()` deletes ALL `_aam_*` objects prefix-only (gamestart.py:382 → placement.py:442-455) — "a restart must never leave two generations of `_aam_*` objects" (gamestart.py:31-33). Then `engine.new_game(spec, seed, candidates, ligand_content)` (:384-385 → engine.py:239-300): re-validates setup, re-parses the manifest (or uses the override rows), re-loads ligand fixtures, runs the generator, THEN replaces the module state — `_payload = payload; _registry = None; _game = game_state.GameState()` (engine.py:292-295) — and asserts the scene unchanged across the op (:296-299). Then `engine.materialize(payload, 0, ligand_content=...)` (:386-387 → engine.py:303-320) rebuilds fresh `_aam_*` objects and the registry. Then the fresh `GameWizard(payload, registry, 0, 0)` (:388) with `__init__` zero cmd calls (wizard.py:126-143), the full compose (:405-407), and the `_last_start` re-capture (:413-416 — same values, deep-copied again; the source stays pristine per Q1's replay-safety note).
3. Window returns: `tabs.setCurrentWidget(game_tab)` + `game_tab.start_countdown(wiz)` — `start_countdown` cancels any pending countdown FIRST (self-healing, game_window.py:172), stores `_pending_wizard`, clears the info box, logs 'Get ready...', starts the member timer (game_window.py:161-177).
4. At GO: `game_tab._begin_play` (game_window.py:195-221) calls `gamestart.activate_game(self._pending_wizard)` (:213) — `activate_game` (gamestart.py:323-339) re-evaluates the conditional replace AT GO: `cmd.get_wizard()` is None (popped at step 1; the countdown is wizard-free per P-1) → replace=0 plain push → `wiz.activate(replace=0)` (:338) runs the msm ORDER LAW (wizard.py:154-177: deselect → push → POST-push msm snapshot — the popped old wizard's cleanup already restored the user's TRUE msm value at step 1, so the GO-time snapshot captures the true pre-game value; SMOKE-08 PART 4's regression teeth) → defensive 0 → refresh. Then `engine._current_game().start_timer(time.time())` (:339) anchors the NEW GameState from zero. `_begin_play` then owns the first level line, seeds `_last_status` (first poll silent), stops+starts the 1 Hz timer (:214-221).

**Mid-game `start_game` (DEFAULT activate=True path — SMOKE-08 PART 4's proven branch, gamestart.py:44-53):** cleanup-first deletes the old generation; the wizard is NOT pre-popped by anyone; at `activate_game` the conditional replace reads the LIVE old GameWizard as top-of-stack → replace=1 → `cmd.set_wizard(self, replace=1)` pops the old wizard INSIDE the push call (its cleanup runs, restoring true msm) — and ONLY a post-push snapshot captures the restored value (the 03-03 ORDER LAW rationale verbatim, wizard.py:41-51; SMOKE-08 PART 4 checks at smoke_08_starter.py:531-556). The window path deliberately stays on the deferred variant so the pop precedes the prepare (P-3) — start_game's internal conditional-replace remains untouched for direct callers (setup_window.py:989-991).

### Q2. Reset mechanics, preconditions, failure modes, and the correct tab-side OWNER

**Exact mechanism:** position replay — per slot, ONE `cmd.translate(delta, aa_name, state=1, camera=0)` from the current baked centroid to `effective_position(spec grid_pose, offset)` + `_assert_pose` fail-closed (placement.py:415-439). Covers ALL molecules of the current level (zip over `registry['molecules']` × `payload['levels'][level_index]['molecules']`, placement.py:425-426). Registry module-side state is read-only; only stored coordinates move.

**Preconditions:** `engine._registry` live (else `EngineError` from `_current_registry`, engine.py:115-120) and `engine._payload` live (else EngineError, engine.py:347-350). Post `new_game`+`materialize` both hold. Reset is a no-op-equivalent on a freshly materialized game (centroids already AT the spec poses — `_assert_pose` passes with delta≈0).

**Failure modes (all ValueError family → `_guard` catchable):**
- `EngineError`: nothing materialized (engine.py:115-120, :347-350).
- `PlacementError` (engine reset path): a `_assert_pose` miss — "any miss raises PlacementError naming the slot" (placement.py:438-439). Per-slot message names object/slot/target.
- `WizardError` from `wizard._assert_identity` (wizard.py:416-434): a recolored object whose matrix stopped being identity — fail-closed naming the object.

**What `wizard.reset_grid` adds on top of `engine.reset_to_grid`:** the identity-matrix asserts for every snapshot object (:607-608 — "a silent matrix failure can never hide", wizard.py:599-600), `_result = None` (:609 — "poses changed, the old result is stale", wizard.py:600), and `cmd.refresh_wizard()` (:610 — the panel redraws). Skipping these by calling `engine.reset_to_grid()` from the tab would leave a stale Confirm result displayed and a silent matrix-failure class — that's PITFALL 6 applied at the widget layer.

**Correct OWNER for the SCORE-10 tab button: the wizard's PUBLIC `reset_grid()` behind the isinstance gate — NOT `engine.reset_to_grid()` directly.**

The 05-07/05-10 laws bind exactly this: "The tab NEVER reaches engine._game/_payload or wizard privates and NEVER pushes callbacks onto the wizard" (STATE.md:185; 05-07-SUMMARY.md:61-63) and "the tab stays a dumb renderer (grep law: game_window.py has zero engine._game/_payload hits)" (STATE.md:188; verified today — zero hits, while `engine._current_game()` IS the sanctioned accessor for the tick, game_window.py:245, :279). `engine.reset_to_grid` is a public engine op, so a literal grep wouldn't fire — but calling it from the tab bypasses the wizard-instance bookkeeping (asserts/`_result`/refresh) and would be the dumb-renderer law violated in spirit. The established GameTab handler family (05-08) is "non-modal impl + _guard + isinstance-gated dispatch to the live GameWizard's public method, SILENT no-op before GO" (05-08-SUMMARY.md:18, :29): `_on_hint` → `_guard(_hint_now)`; `_hint_now` gates `cmd.get_wizard()` isinstance GameWizard → `prior.hint()`. Reset should be the identical shape: `_on_reset_grid` → `_guard(_reset_grid_now)`; `_reset_grid_now` gates → `prior.reset_grid()`. `reset_grid()` returns None always (its `_guard` returns the impl's None — wizard.py:602 returns `_guard(...)` whose impl returns None), so the tab handler cannot log a data line from the return — the 'game_reset' info-box line is handler-logged directly, exactly as the 'Hint:' line is (game_window.py:369-370), never by the poll-diff (see Q3b nuance).

**Pre-GO no-op is CORRECT semantics:** during the countdown (P-1) there is no wizard on the stack → the gate returns None → nothing happens — and nothing NEEDS to happen: the freshly prepared game's AAs are already AT their grid poses (materialize bakes them there, STATE.md:109). Same for no-game-ever.

**Shared limitation (documented, mirrors Hint):** the gate reads `cmd.get_wizard()` = top-of-stack ONLY. If a user wizard sits on top (game wizard dormant beneath, stack-native auto-resume, wizard.py:31-39), the tab's Reset (like Hint) cannot reach the game wizard. The wizard panel's own 'Reset to Grid' button is reachable only when the game wizard is top. This is today's Hint behavior verbatim (05-08 H-8) — acceptable, documented-only.

### Q3. GameState on Restart — fresh construction proof + what persists

**Fresh GameState is PROVEN by construction:** `start_game` → `engine.new_game` → `global _payload, _game, _registry; _payload = payload; _registry = None; _game = game_state.GameState()` (engine.py:292-295). `GameState.__init__` zeros everything: level/molecule 0/0, `molecule_scores = []`, `skip_count = 0`, `giveup_count = 0`, `timer_anchor = None`, `formed_types_per_molecule = {}` (game_state.py:168-175). So scores/timer/skip-counts RESET to fresh on every Restart — nothing to clear manually, and there is no "clear scores" op anywhere in the engine (grep: no reset-op touches `_game`).

**The full cross-game state ledger is section (5).** Highlights of what PERSISTS (by design) vs what must NOT persist:
- `gamestart._last_start` — persists BY DESIGN (the replay source; re-captured on the restart with identical values, deep-copied again). Who resets it: nobody in production; only a later successful start re-captures.
- `setup_window._last_export` — persists (Decision-4 store); Restart neither reads nor writes it (different home — 05-05 key-decision "a later export must never corrupt the restart source").
- `setup_window._uploaded` — persists (session-only upload ingest). Correct: `_last_start` holds `candidates`/`ligand_content` so an uploaded game restarts WITHOUT re-ingesting.
- `game_tab` countdown/`_pending_wizard` — cancelled by the new `start_countdown` (self-healing P-2, game_window.py:172).
- Tab `1 Hz _timer` / `_last_status` / labels / info log — self-managed (§5).
- msm / colors / pk1 / selection — old wizard's cleanup restores at pop; fresh wizard re-snapshots at GO (ORDER LAW).
- Camera/scene composition — recomputed fresh per start (front-offset is "idempotent by construction ... every start runs it on FRESH materialize output, so restarts reproduce the same composed scene", gamestart.py:281-285).

**No engine-level "clear scores" op exists or is needed.** The ONLY thing the Restart impl must handle itself: `_last_start is None` refusal (Q1's edge — decision candidate in §8).

### Q3b. GameState on Reset (SCORE-10) — separation proof

**`reset_to_grid` touches NO GameState.** The chain `wizard._reset_grid_impl` → `engine.reset_to_grid` → `placement.reset_to_grid` (wizard.py:604-610 → engine.py:343-352 → placement.py:415-439) contains zero `_current_game`/GameState references — only coordinate translate + pose assert + wizard instance bookkeeping (`_result = None`, wizard.py:609). The timer anchor is untouched (Q7), scores/counters untouched, level/molecule position untouched. `engine.game_status()` (the 7-key to_dict read, engine.py:472-478) returns byte-identical before/after a Reset. Spec wording conforms: "reset button to place all AA back to the grid" (spec.md:47) — positions only. **Nothing must change.**

**One Phase-6 design nuance (score-lifecycle, owned by the SCORE-01 plan):** Reset does NOT retract a recorded score. After Confirm (which appended to `molecule_scores` via `record_molecule_result`, game_state.py:235-248), a Reset then a re-Confirm appends AGAIN — the documented repeated-Confirm caveat (wizard.py:550-553 "repeated Confirm appends to the engine GameState's molecule_scores -- score-history semantics are Phase 6's lifecycle"). Reset's `_result = None` clears the DISPLAY of the last result but not the recorded history. The SCORE-01 plan must define confirm-history semantics; the Reset plan should simply not claim "undo of a score".

### Q4. (merged into Q3b — separation confirmed)

### Q5. Give Up leaves an "ended" game — what exists today, what Restart must do differently, Cleanup as the post-endgame exit

**Today NOTHING marks game-over — SCORE-06/SCORE-07 have zero existing code.** The wizard's lifecycle is: Done = canonical `cmd.set_wizard()` pop (wizard_text.py:58-59, wizard.py:31-39). "End of game" today can only be approximated by Done + Cleanup (04-11).

**What an ended game will inherit (the Give Up plan's raw material):** a LIVE GameWizard on the stack, live `_aam_*` objects, live `engine._game` (partial scores — Confirm history + skip count if Skip landed), a RUNNING 1 Hz tab timer with a live `timer_anchor`. SCORE-07 wants "a stopped timer" (spec.md:57; ROADMAP.md:168) — the sanctioned pure mechanism to FREEZE the clock is `GameState.rebase_timer(now, elapsed)` (game_state.py:193-224 — "the shown elapsed FREEZES at `elapsed`"; the 1 Hz tick already uses it for the modal pause, game_window.py:276-283). The Give Up plan's likely minimal shape: confirmation warning → rebase_timer to freeze → render the endgame count/message in the info box (+ reserve `gave_up` event kind, status_text.py:68-69) → game-over marker decision (§8 — nothing exists to mark it with: GameState has no ended flag; wizard has none).

**Does Restart do anything different after a Give Up vs mid-game? Probably NOTHING extra — verified reasoning:**
- Restart's chain pops the still-live wizard (identical to mid-game), replays `_last_start` (identical — the tuple survived the endgame, never cleared in production, §1 lifetime), rebuilds everything fresh (fresh GameState zeros, fresh objects, GO re-anchors the timer from zero). A frozen `rebase_timer` state dies with the old GameState at `new_game`'s replacement (engine.py:295).
- If the Give Up plan renders the endgame via a MODAL box: Restart from behind a modal is impossible (modality blocks the tab) — no interplay. If the endgame is info-box-rendered (spec.md:55-58 "show" in the game status context): Restart is a normal click; the restart chain's `start_countdown` clears the info box (game_window.py:174) — the endgame message disappears, the countdown logs, the fresh game's level line lands at GO. Clean.
- **If the Give Up plan POPS the wizard at endgame** (a "torn-down" endgame design): then Restart's `_pop_game_wizard()` returns False harmlessly (isinstance gate on None) and the chain proceeds identically. Either Give Up design composes with Restart with no special case — as long as Restart never assumes a wizard is on the stack (it must not; `_pop_game_wizard` is gate-guarded, setup_window.py:841-845).
- The one interplay Restart MUST respect: if Give Up leaves a game-over marker that SCORE-07's plan or a later plan keys on, that marker must be game-scoped (inside the GameState or the wizard instance that `new_game`/restart replaces), NOT module-level — otherwise Restart would leave a stale "ended" flag over the fresh game. Flag this to the SCORE-06/07 plans (§8 decision candidate).

**Cleanup on an ended game = the sanctioned post-endgame exit TODAY:** `_on_cleanup` → `cancel_pending_start()` first (P-2) → `_guard(_cleanup_now)` → `_pop_game_wizard()` (canonical pop; user wizard untouched) → `placement.cleanup_game_objects()` prefix-only → count surfaced via `QMessageBox.information` (setup_window.py:864-881, :847-862). Proven headlessly (SMOKE-11 PART E: baseline → start_game +20 `_aam_*` → `dlg._cleanup_now()` → deleted=20 → baseline EXACTLY + stack empty; smoke_11_window.py:167 recount in STATE.md:167) and human-verified mid-game (04-15 step 4, STATE.md:241). Whether the Give Up plan adopts Cleanup as its designed exit or adds its own post-endgame "OK/exit" affordance is that plan's call; Cleanup composes regardless.

### Q6. Button wiring precedents — the GameTab handler family

**Current inventory:** ONE connected button — Hint (game_window.py:119-126), connected by 05-08 ("the 04-05 shell law: the handler plan connects its own button", game_window.py:22-24). The tab docstring reserves the row for Confirm/Skip/Save/Restart/Reset/Import (game_window.py:84-87).

**The GameTab DOES have `_guard`-like behavior natively — added by 05-08:** `GameTab._guard` (game_window.py:332-343) is "the 04-09 _guard contract, VERBATIM (setup_window.py:637) — the FIRST _guard on this class": catch ONLY `(ValueError, OSError)` → `QtWidgets.QMessageBox.warning(self, 'AA-match', str(e))`; unexpected exceptions PROPAGATE. So GameTab handlers get the same contract as the QDialog's — no structural difference. GameTab is `QtWidgets.QWidget` (not QDialog); `QMessageBox.warning(self, ...)` with a QWidget parent is the running 05-08 precedent (game_window.py:342).

**The factoring to follow (05-08, binding):** thin non-modal `_on_X` wrapper → `_guard(_X_now)` → non-modal `_X_now` impl with an isinstance-gated dispatch and NO boxes in the impl ("NON-MODAL: the recolor on-screen IS the feedback; NO success box (the _on_start precedent, setup_window.py:920)", game_window.py:345-349). For Restart/Reset:
- `_on_restart` → `_guard(self._restart_now)` — impl chain per §3 (no file pickers, no success box; the countdown log + scene rebuild + gamestart status print ARE the feedback — same as `_on_start`, STATE.md:171 "a Start that opened a modal would be noise").
- `_on_reset_grid` → `_guard(self._reset_grid_now)` — impl chain per §4; the info-box 'game_reset' line is the pinned log line (mirroring the pinned 'Hint: %d eligible...' line, game_window.py:369-370).
- The impls must be **driveable headlessly as methods** (the smoke-99 law: "impls never own boxes" — a modal under platform=offscreen BLOCKS, STATE.md:163).
- Button creation: created in `GameTab.__init__` with a spec-meaning tooltip, connected in `__init__` per the 04-05 shell law (`btn_hint.clicked.connect(self._on_hint)` at game_window.py:126); spec labels "Restart" / "Reset" (spec.md:46-47); the stretch keeps the row from reflowing (game_window.py:124).
- SCANNED_MODULES: `game_window.py` is already scanned by `tests/test_wizard_source.py` (05-06 grew it, STATE.md:184) — no registry change needed; `aamatch/` grep-law state verified: game_window.py has 1 `QMessageBox` hit (the `_guard`) and zero `engine._game`/`engine._payload` hits today (05-10 grep law holds).

### Q7. Timer semantics — verified

**Restart: timer re-anchors from zero.** `activate_game` runs `engine._current_game().start_timer(time.time())` on the NEW GameState (gamestart.py:339) — `start_timer` stores a fresh float anchor (game_state.py:187-191). Pre-GO the new GameState's anchor is `None` and `_compute_elapsed` returns 0.0 ("Returns 0.0 before the anchor exists (a never-started game)", game_window.py:244-248) — so the label legitimately shows '0:00' during the restart countdown and starts advancing at GO. `_begin_play` re-drives the 1 Hz timer with a defensive stop+start (game_window.py:220-221).

**Reset: the timer MUST keep running — verified nothing touches the anchor.** `placement.reset_to_grid` = translate + pose assert only (placement.py:415-439); `engine.reset_to_grid` = registry/payload reads only (engine.py:343-352); `wizard._reset_grid_impl` = engine call + asserts + `_result = None` + refresh (wizard.py:604-610). No `start_timer`, no `rebase_timer` anywhere in the chain (grep over the three functions: none). The 1 Hz tick keeps rendering live elapsed from the untouched anchor. `game_tab._last_shown_elapsed` continues updating. No rebase call is needed or wanted for SCORE-10.

### Q8. Smoke/assert strategy (summary here; full sketch in §7)

T1a cmd-tier proofs are possible for everything mechanical: restart replay identity via the SMOKE-08 b-factor instance-marker band (smoke_08_starter.py:146-162 — names are reused, instances are proven new), fresh-GameState via `engine.game_status()`/`to_dict()` zeros, position equality for Reset within `POSE_TOLERANCE` + per-axis ulp slack (placement.py:84-95), rotation-persist via on-grid detect count (SMOKE-06 evidence), timer anchor untouched-checks, `_last_start` aliasing checks (SMOKE-11 PART H's pinned pattern, smoke_11_window.py:833-854). T1b dialog-tier proofs: button existence/connect, method-driven `_restart_now`/`_reset_grid_now`, countdown sequence, `_guard` refusal path. `[HUMAN]`: restart feel (countdown visible, scene rebuild, timer 0:00), reset feel (selection stays green mid-rotation), Give-Up→Restart interplay once the endgame design exists, restart with a dormant user wizard.

---

## (3) Restart Design Recommendation (SCORE-09)

**Recommended shape: the window-driven deferred sequence with `_last_start` inputs — `_start_impl` (05-09) with the collect/build_state/Decision-4 prefix replaced by the verbatim `_last_start` tuple. Recorded evidence for this direction: `05-09-SUMMARY.md` frontmatter "affects: phase-06 game lifecycle (restart replays start through this same sequence)".**

Exact call chain (owner: `SetupWindow`/GameTab-side handler in the same window — the spec places the button on the Game status tab, spec.md:46, so the handler lives on GameTab with the window seam available):

1. `_on_restart` (thin `_guard` wrapper on GameTab, §6 family; NO success dialog — the countdown log is the feedback, mirroring `_on_start`).
2. `self._restart_now()` (non-modal impl, driveable headlessly):
   a. **Refuse when nothing to restart**: if `gamestart._last_start is None` → raise ValueError ('Restart: no game has been started yet.') so `_guard` surfaces it verbatim (house fail-closed + spec UI standard "clear but sufficient explanation"; alternative = silent no-op per Hint's H-8 — decision candidate D1).
   b. `game_tab.cancel_pending_start()` FIRST (P-2 defensive, mirroring `_on_cleanup`'s handler-top cancel, setup_window.py:875) — belt-and-braces; the new `start_countdown` also self-heals.
   c. Log the 'game_restarted' pinned line in the info box (decision candidate D2 — recommended BEFORE the chain, mirroring the handler-logged 'Hint:' line; note the countdown's `start_countdown` then CLEARS the info box, so a pre-chain line would be wiped — if the line is wanted, log it as the LAST pre-countdown act or rework `start_countdown`'s clear; simplest: rely on the countdown 'Get ready...' sequence itself as the restart surface and log 'game_restarted' via `_log` in `_restart_now` AFTER `start_countdown` armed — i.e. after step (f), appending to the cleared box).
   d. `_pop_game_wizard()` (P-3 — setup_window.py:826-845; pops the LIVE GameWizard, cleanup restores msm/colors/pk1; a user wizard on top is never popped — gate returns False).
   e. `gamestart.start_game(setup=ls['setup'], seed=ls['seed'], candidates=ls['candidates'], ligand_content=ls['ligand_content'], activate=False)` with `ls = gamestart._last_start` (§2 Q1 call shape). NO build_state pre-checks: the tuple was validated when the game first started (validate fail-closed inside new_game, engine.py:257) and the same inputs provably generate (deterministic generator, seed+inputs — the double-Start proof class, STATE.md:245). The `_guard` still wraps OSError/ValueError (e.g. a package fixture deleted between start and restart — accepted residue per the 04-13 clean-then-refuse law, STATE.md:171).
   f. Switch tab + arm the countdown: `tabs.setCurrentWidget(game_tab)` (if driving from the window) — note: the Restart handler may live ON GameTab itself, in which case the tab is already current and this step degenerates to the window-side `tabs.setCurrentWidget` only when the handler is window-owned (recommendation: the button handler lives on GameTab next to `_on_hint`; the impl reaches the window seam only if needed. Decision candidate D3 — GameTab-owned vs SetupWindow-owned handler).
   g. `game_tab.start_countdown(wiz)` (self-healing cancel + clear + 'Get ready...' + member timer).
3. At GO: `_begin_play` → `activate_game` (replace=0 plain push — stack is empty since (d); ORDER LAW post-push snapshot = the user's TRUE msm restored at (d)) → `start_timer(time.time())` fresh anchor (gamestart.py:339) → first level line + `_last_status` seed + 1 Hz stop/start (game_window.py:213-221).

**NOT touched by Restart (explicit no-ops):** `setup_window._last_export` (Decision-4 guard untouched — Restart reads ONLY `gamestart._last_start`); `setup_window._uploaded`; `backup.py` (verdict in §4 note below); `status_text.EVENT_KINDS` wording stays reserved until a plan pins it.

**`backup.py` verdict — NO Phase-6 role (explicit, so planning does not invent work):** `aamatch/backup.py` provides snapshot/restore/discard/verify_intact over an INJECTED store (MemoryStore/FileStore; sha256-gated canonical-JSON framing; BackupError family; BACKUP_OBJECT_PREFIX reserved for a future cmd-tier adapter, backup.py:1-54, :198-247). Its only consumers today are `tests/test_backup.py` (15 tests pinning the contract, tests/test_backup.py:65-212) and nothing else (grep: zero aamatch/ imports). PITFALL 9's "Restart/Reset route through the backup module + spec replay, never undo" (ROADMAP.md:170; PITFALLS.md §218-238) is SATISFIED DIFFERENTLY than the literal wording: the spec-replay half is what Phase 6 uses (Restart = input-tuple replay through start_game per 05-05/STATE.md:183 — "NOT a v1-style backup object -- the materialization inputs fully regenerate the scene"; Reset = spec re-bake per PITFALL 6), and the no-undo law is closed by ABSENCE of undo (PyMOL open-source undocontext is a stub — backup.py:2-4 docstring; game movement is fail-closed assert-protected per the 03-03 identity invariant, wizard.py:416-434). **The plan should NOT wire backup.py into Restart/Reset** — doing so would port the v1 machinery the 05-05 decision explicitly rejected and double-protect a path that is already deterministic-replay-safe. If PITFALL 9's literal "route through one backup module" is still demanded as a provenance note, record the reading in the plan docstring (spec replay IS the PITFALL-9 mechanism; backup.py remains the Phase-1 pure policy module for the Phase-7 sidecar), never in code.

**Alternative (recorded, not recommended): cmd-tier default-path restart** — `gamestart.start_game(**_last_start)` with activate=True (SMOKE-08 PART 4's replace=1 branch, proven at smoke_08_starter.py:516-556). One call, GO immediate, no countdown. Rejected for the UX path because the 05-09 sequence is the recorded Restart shape and spec.md:33-34's countdown-then-start is the house start convention; keep the default-path knowledge for the SMOKE's regression view only.

**Restart ordering hazard note (pre-existing, NOT new):** `_pop_game_wizard` pops only a GameWizard TOP. The sequence user-wizard-mid-game → Restart → (old game wizard dormant BENEATH the user wizard, never popped) → play the restarted game → Done → auto-resume user wizard → user Done → auto-resume the STALE old game wizard (registry → deleted objects). This hole is IDENTICAL in today's `_start_impl` (05-09 P-3 pops a GameWizard top only) — pre-existing, edge-class, no stack-walking API exists to fix it cheaply. Record as documented-only (§8 D6); never a Restart blocker.

## (4) Reset Wiring Recommendation (SCORE-10)

**Owner: GameTab handler → `GameTab._guard` → isinstance-gated dispatch to the LIVE GameWizard's PUBLIC `reset_grid()`. Never `engine.reset_to_grid()` directly from the tab (Q2's law).**

Exact call chain:

1. Button: created in `GameTab.__init__` on the reserved row (`btn_row` stretch slot, game_window.py:118-125) with label 'Reset' + spec tooltip ("Place all amino acids back to their grid positions; orientations are kept." — the orientation note is the Phase-9 help-text reserve, wizard.py:592-593), connected in `__init__` (04-05 shell law).
2. `_on_reset_grid` → `_guard(self._reset_grid_now)` — non-modal; no boxes in the impl.
3. `_reset_grid_now` impl:
   a. `from pymol import cmd; from . import wizard as wizard_mod` (lazy, module-identity law, game_window.py:359-360 precedent).
   b. Gate: `prior = cmd.get_wizard()`; `if not isinstance(prior, wizard_mod.GameWizard): return None` — silent no-op pre-GO/no-game (H-8/PA-gui precedent, game_window.py:361-363). Correct semantics: AAs are already at grid poses in a fresh game; nothing to place back.
   c. `prior.reset_grid()` — the wizard's PUBLIC method (wizard.py:586-610). Its own `_guard` maps the ValueError family to the wizard panel's visible `_error` + refresh (wizard.py:436-449); the tab's `_guard` catches any REMAINING ValueError/OSError (unexpected — the wizard _guard already guarded house refusals) into the QMessageBox. Layering note: a house refusal lands on the PANEL error line (never a box) — same as Confirm/Reset today.
   d. Handler-logged pinned line on success: `'AA reset to grid positions (orientations kept).'` or the reserved kind's final wording — via `self._log(...)` (decision candidate D4 pins the text; the poll-diff CANNOT emit it: positions are not in `_state_dict` (wizard.py:333-356 — no pose keys) and 'result' is never fingerprinted (status_text.py:151-155), so the 'game_reset' kind must be handler-logged exactly as 'game_start'/'countdown'/'hint' are tab-handler-logged Phase-5 kinds, status_text.py:49-65). Also note `_result = None` produced by Reset produces NO poll event by design — the wizard panel loses its result display silently, which is the intended "stale result cleared" UX.
4. What the handler must NOT do: touch `engine._game`/`_payload` (05-10 grep law), reach wizard privates (`_color_store`/`_result` are instance-internal — the wizard method owns them), or add any pose data to the poll (would grow `_state_dict` contract 2 for no benefit).

**Timer/score invariants to assert in the smoke (Q3b/Q7):** after the tab Reset — `engine.game_status()` unchanged (7-key to_dict equality), timer anchor unchanged, elapsed derivation still advances, `wiz._result is None`, selection persists (`get_status()['selected']` unchanged), detect() on-grid returns 0 records (SMOKE-06 class evidence).

## (5) Cross-Game State Ledger

Every piece of state, who resets it, and when — across a RESTART (R), a RESET (X), an endgame/Give-Up (G — Phase-6 decision pending), and a CLEANUP (C):

| # | State | Home | R (Restart) | X (Reset) | C (Cleanup) | Notes/evidence |
|---|---|---|---|---|---|---|
| 1 | `gamestart._last_start` | module (gamestart.py:178) | re-captured (same values, deep-copied again :415-416) | untouched | untouched | never cleared in production; survives endgame (Q5) |
| 2 | `engine._payload` | module (engine.py:102) | replaced by new_game (:293) | untouched | untouched | |
| 3 | `engine._registry` | module (engine.py:103) | new_game sets None (:294) → materialize replaces (:317-319) | untouched | untouched (objects die; registry state stays until next materialize/new_game — stale names harmless: next new_game :294 sets None first) | |
| 4 | `engine._game` (GameState) | module (engine.py:104) | fresh `GameState()` (:295) — ALL fields zeroed (game_state.py:168-175) | untouched | untouched (stale `_game` survives cleanup; `_current_game` still returns it — the 05-06 tick hazard class: smokes must stop the 1 Hz timer post-cleanup, 05-06-SUMMARY.md:112-118) | |
| 5 | GameState fields (scores/skips/giveups/formed/anchor) | instance | zeroed via #4 | untouched (Q3b) | untouched | giveup_count increments are SCORE-06's |
| 6 | `GameState.timer_anchor` | instance | None until GO; fresh float at GO (gamestart.py:339) | UNTOUCHED (Q7 — keeps running) | untouched | freeze = rebase_timer (SCORE-07's G half) |
| 7 | PyMOL `_aam_*` objects | scene | cleanup deletes ALL (gamestart.py:382) → materialize rebuilds | moved only (translate per slot, placement.py:437) | prefix-deleted (placement.py:442-455) | names REUSED — identity via instance markers (Q8; 03-05 law STATE.md:136) |
| 8 | Sentinels (segi AAM, b=-999) | per-atom | rebuilt fresh | untouched (translate keeps tags — "the AAM/Z sentinels (segi, b=-999) are untouched", gamestart.py:277-279) | die with objects | |
| 9 | GameWizard instance (payload/registry/maps/slot state) | stack (pushed at activate) | fresh instance (gamestart.py:388; init zeroes `_current_slot/_saved_msm/_color_store/_result/_error`, wizard.py:139-143) | same instance: `_result→None` (wizard.py:609); `_current_slot`/recolor PERSIST (wizard.py:601) | popped (cleanup runs) | |
| 10 | `_color_store` | wizard instance | restored + cleared at old pop (wizard.py:202-204); fresh {} on new | KEPT (only positions reset; Done still restores) | dies with instance | |
| 11 | msm | setting | old cleanup restores at pop; new push re-snapshots + defensive 0 (ORDER LAW, wizard.py:154-177) | untouched (stays 0 during play) | cleanup restores (wizard.py:196-197) | stock default 1 (SettingInfo.h:449, wizard.py:50-51) |
| 12 | Selection + pk1 + user's ACTIVE selection | cmd state | cleared at old cleanup (unpick :198-200, deselect :201) + new activate deselects (:173) | PERSIST (wizard.py:601) | cleared at pop | |
| 13 | `game_tab._countdown_timer` + `_pending_wizard` | tab instance | cancelled self-healing at new start_countdown (game_window.py:172) + handler-top defensive cancel (§3) | untouched | cancelled handler-first (P-2, setup_window.py:875) | |
| 14 | `game_tab._timer` (1 Hz) | tab instance | keeps running; tick renders 0:00 from anchor-None during countdown; `_begin_play` stop+start at GO (:220-221) | keeps running (Q7) | NOT stopped by production — smokes must stop it (05-06 Rule-2, 05-06-SUMMARY.md:112-118) | the non-modal tick branch has NO EngineError guard over a no-game window (game_window.py:284 `_compute_elapsed` raises — the modal branch alone guards, :277-282) |
| 15 | `game_tab._last_status` / labels / `_last_shown_elapsed` | tab instance | cleared when wizard-free (poll :317-319), re-seeded at GO (:218) | `required`/selection unchanged → poll silent; result never fingerprinted (status_text.py:151-155) | cleared when wizard-free | |
| 16 | `game_tab._info_log` | tab instance | cleared by start_countdown (:174) | NOT cleared (rolling log; handler appends its line) | NOT cleared | |
| 17 | `setup_window._last_export` | window instance | NO-OP (different home — §3) | NO-OP | NO-OP | Decision-4 store (setup_window.py:937-939) |
| 18 | `setup_window._uploaded` | window instance | NO-OP (game restarts replay `ligand_content`/`candidates` from `_last_start`) | NO-OP | NO-OP | session-only ingest slot (:179, :816-817) |
| 19 | `setup_window._window` singleton | module (setup_window.py:66) | survives (reuse-and-raise) | survives | survives | 04-05 SETUP-01 |
| 20 | Camera/scene composition | cmd view | recomputed fresh per start (front-offset idempotent on fresh materialize — gamestart.py:281-285) | untouched | n/a | |
| 21 | backup.py stores | module (pure) | NO-OP — no Phase-6 role (§3 verdict) | NO-OP | NO-OP | zero aamatch/ consumers (grep receipt) |
| 22 | Game-over marker (G's future) | TBD | must be game-scoped (die with #4/#9) — never module-level | n/a | n/a | decision candidate D5 |

## (6) Pitfall Register

**PITFALL 6 (movement-model reset duality) — application to Phase 6:** full text at PITFALLS.md §144-165. Binding reading: "Whatever the model, **reset must reset the same mechanism that moved the atom**" (§156) — movement is baked world-frame `cmd.translate(state=1, camera=0)` / `cmd.rotate(selection-form, camera=0)` on identity-matrix objects (wizard.py:53-69 contract 5, :451-542); Reset re-bakes through the IDENTICAL primitive (`placement.py:437`) and asserts the identity matrix afterwards (wizard.py:607-608). The Phase-3 recorded decision already locked position-only replay with rotation persist (03-03-SUMMARY.md:36; SMOKE-06's on-grid-with-orientation-residual evidence, wizard.py:587-592). **Phase 6's job is WIRING the tab button through `wizard.reset_grid()` — never re-inventing the mechanism** (per 05-09's affects note + the 03-06 RECORDED PLANNER DECISION). Concretely: the plan must NOT add any new translate/rotate/matrix code for SCORE-10, must NOT use the banned matrix calls anywhere new (placement matrix_reset ×3 / get_object_ttt ×1 / engine matrix_reset ×2 / geometry get_model ×1 prose pins stay exact — STATE.md:118), and must keep the identity-assert-after-move pattern untouched.

**PITFALL 9 (no undo — snapshot/restore is the only safety net) — application to Phase 6:** full text at PITFALLS.md §218-238. Binding reading reconciled with the recorded decisions (Q5's ROADMAP wording "Restart/Reset route through the Phase-1 backup module + spec replay, never 'undo'"): the spec-replay half IS the sanctioned mechanism — Restart replays the captured input tuple (05-05, STATE.md:183: "NOT a v1-style backup object -- the input tuple fully regenerates the scene"), Reset replays the spec poses (PITFALL 6's mechanism), and "never undo" is closed by PyMOL open-source having no undo at all (backup.py:2-4; PITFALLS.md §220-221). **`backup.py` itself provides NOTHING on the Phase-6 Restart/Reset path** (evidence §3/§5 ledger row 21: zero aamatch/ consumers; the module is the Phase-1 pure policy home whose Phase-7 sidecar future is documented in its docstring :34-35 and test :212-214). The plan should state this reconciliation explicitly in a docstring ("spec replay IS the PITFALL-9 mechanism for Restart/Reset; the backup module remains the Phase-7 persistence policy home") so planning neither wires backup.py in nor claims it's forgotten. The PITFALL-9 disciplines that DO bind Phase 6: orchestrator asserts return values / never re-derives from a discarded source (§229) maps to "never mutate `_last_start`'s contents — always re-capture through start_game"; and "the game's own Restart/Reset/Cleanup are the safety nets — keep them wired to the mechanism, not to undo" (§231) maps to the §3/§4 chains verbatim.

**03-05 instance-identity law (03-05, STATE.md:136) — application to any Restart smoke/assert:** "Object NAMES are not instance identity across restarts: same-seed same-shape restarts REBUILD the same `_aam_*` names after cleanup frees them — generation-gone asserts must stamp INSTANCES (b-factor marker band; sentinel b=-999.0 sits outside), never compare name sets." The working pattern is SMOKE-08's: `_stamp(gen_names)` writes a marker band into a b-factor range far outside the sentinel; after the restart `_marked_atoms() == 0` proves the old generation's instances died while `len(_game_objects()) == expected_count` proves exactly one fresh generation (smoke_08_starter.py:146-162, :489-494, :537-543). Any Phase-6 Restart smoke copying a "restart identity" proof MUST use this pattern — a name-set comparison would false-pass the double-generation class.

**03-06 msm/display laws in force (03-06, STATE.md:202-213):** msm pre-game 1 / during 0 / post-Done 1 (defensive restore) — Restart re-runs the ORDER LAW at GO (post-push snapshot; the popped old wizard's cleanup restored the TRUE value at pop time — the 03-05 restart-variant teeth, SMOKE-08 PART 4). Display-rebuild law: any recolor/restore must rebuild display lists (wizard.py:224-246) — Reset's chain does NOT recolor (only the persisting selection's existing recolor stays), so no new display-rebuild code is needed; the smoke's pose asserts are data-level only.

**The 03-05 pose/metric tolerance laws (STATE.md:136 relevant half):** pose asserts use float32-realizable tolerance — `POSE_TOLERANCE=1e-6` floor + `FLOAT32_ULP_REL` per-axis slack (placement.py:84-95); metric drift budgets 5e-6 Å / 3e-4 deg where rigid-transform invariance is compared (02-14, STATE.md:114). Reset position-equality asserts must read the target via `effective_position` and compare with the same slack class — never a fixed 1e-6-only assert at tier-9 |coord| ~32.9 Å magnitudes (the 02-15 raise-fire receipt, placement.py:86-91).

**05-06 Rule-2 standing law (STATE.md:184):** "Smoke restore must STOP the 1 Hz timer — a real pumped tick post-cleanup raises EngineError inside a timer callback." Any Phase-6 Restart/Reset smoke's restore block = cancel_pending_start + `dlg.game_tab._timer.stop()` + canonical done pop + prefix cleanup + `gamestart._last_start = None` (the PART H restore shape, smoke_11_window.py:872-882, plus the timer stop from 05-06).

## (7) T1a/T1b Smoke Strategy + [HUMAN] Items

**Naming/disambiguation (binding for smoke authoring):** the Setup tab's `dlg.btn_reset` (game-setup defaults, spec.md:21-22) vs the Game tab's SCORE-10 `dlg.game_tab.btn_reset` (AA-to-grid) — smokes/asserts must never abbreviate to "the reset button"; the plan should name the GameTab attribute distinctly (e.g. `btn_reset_grid` or `btn_restart`/`btn_reset_grid` pair — decision candidate D7) and its smoke check strings should carry "grid"/"game" wording. The spec-order stub docstring (game_window.py:84-87) already lists "Restart/Reset" — keep the labels 'Restart'/'Reset' (spec.md:46-47) with distinct tooltips.

**RESTART smoke sketch (T1a cmd-tier core + T1b dialog drive; PART-lettered, count-asserted, SMOKE-08/11 precedents):**

- PART A (ALWAYS, T1a — the SMOKE-08 PART 3/4 + SMOKE-11 PART H hybrid):
  1. Baseline scene snapshot; `start_game(setup=sentinel, seed=4242, activate=False)` (the 05-05 deferred prepare; assert returned GameWizard NOT pushed + scene grew `_aam_`-prefixed — smoke_11_window.py:819-831 shape).
  2. Fabricate a dirty game: push the wizard via `activate_game(wiz)` (assert push + float anchor + `_saved_msm` int — :857-870 shape), then `engine.place_aa(slot_id, scripted_position)` (or a wizard `move_to`) on ONE slot + a Confirm to append a score + `skip_count += 1` via the engine GameState ( SCORE-05's record path, STATE.md:106 — fabricate with `game.record_molecule_result` + direct field writes; WSL-testable shape).
  3. Stamp the instance marker band on gen1 `_aam_*` (smoke_08_starter.py:156-162); read `stamped > 0`.
  4. Record pre-restart invariants: `pre_msm = cmd.get('mouse_selection_mode')` (== 0 in play), `ls = gamestart._last_start`, aliasing sentinel (`ls['setup'].get('allowed_interactions') is not sentinel[...]`).
  5. The Restart drive as the window would (method-driven): `gamestart._last_start` read → canonical pop `cmd.set_wizard()` — NO; the T1a core proves the cmd-tier replay itself: `wiz2 = gamestart.start_game(setup=ls['setup'], seed=ls['seed'], candidates=ls['candidates'], ligand_content=ls['ligand_content'], activate=False)` (NO pre-pop — proving the DEFAULT mid-game replace path would need the live-wizard variant; see PART A' below) → assert: marked survivors == 0 (instance law, smoke_08_starter.py:489-494), one generation (count), `cmd.get_names('objects')` grew only `_aam_`-prefixed, `gamestart._last_start` setup object is the SAME dict (is — deep-copied source pristine across replay) with equal 4-key shape.
  6. Dirty-state cleared: `engine.game_status()` == fresh zeros (molecule_scores [], skip_count 0, giveup_count 0, formed_types {}, level/molecule 0/0) — the to_dict 7-key shape (engine.py:472-478); anchor None pre-GO.
  7. `activate_game(wiz2)` → anchor float; `_saved_msm` int; pose equality for the previously-moved slot: `geometry.centroid_of(obj)` vs `effective_position(payload pose, registry offset)` within POSE_TOLERANCE + ulp slack (1e-6 floor + per-axis slack — the 02-15 law); detect() on the fresh scene — count-asserted (0 records on-grid, SMOKE-06 class).
  8. Done pop (`cmd.set_wizard()`) → msm restored to the pre-game TRUE value (== stock 1 for a defaults session) + stack empty.
  9. Restore: prefix cleanup → baseline EXACTLY; `gamestart._last_start = None`.
- PART A' (ALWAYS, T1a — the replace=1 mid-game variant, SMOKE-08 PART 4 re-shape with the _last_start replay inputs): NO pre-pop; `start_game(...same explicit kwargs...)` over the LIVE wizard → assert replace path: old popped inside push (ORDER LAW: msm 0 in play, snapshot == TRUE pre-game value, Done restores), instance marker survivors 0, one generation. (This proves start_game's internal conditional-replace stays intact for direct callers even when the window path pre-pops — setup_window.py:989-991's preserved law.)
- PART B (T1b, offscreen — the SMOKE-11 PART B/I shape): buttons exist ('Restart'/'Reset' labels + tooltips), connected (`_on_restart`/`_on_reset_grid` reachable via `btn.click()` or method drive), GameTab button-row inventory re-green (btn_hint + additions; I1-style attribute/text asserts, smoke_11_window.py:925-955).
- PART C (T1b — the restart drive through the tab impl, method-driven per I3's NO-processEvents-gap rule, smoke_11_window.py:957-984): build a live game via the existing `_start_impl`/`_begin_play` drive; drive `_restart_now` as a METHOD (impl owns no boxes — smoke-99 law); assert: pending wizard armed + NOT on stack; countdown sequence 'Get ready...' '3' '2' '1' 'GO!' + level line; timer label '0:00' during countdown (anchor-None read); drive the 4 ticks → GO; assert float anchor + fresh game_status; restore = cancel_pending_start + `_timer.stop()` + done pop + cleanup + `_last_start = None` (05-06 Rule-2 + PART H shape).
- PART D (T1a — `_last_start is None` refusal): with `_last_start = None` (fresh module state), drive the restart impl → ValueError family refusal ('no game has been started yet') — assert the message + scene untouched + no wizard; restore `_last_start = None` again.
- PART E (T1b — the Reset drive through the tab impl): live game; script a moved AA (`engine.place_aa`) + Confirm (score appended) + record the anchor; drive `_reset_grid_now` as a METHOD; assert: the moved AA centroid == `effective_position` target (float32 slack class), OTHER AAs unchanged (count/pose), `wiz._result is None` via `get_status()['result']` (public read — not a private reach), selection key unchanged in `get_status()`, `engine.game_status()` to_dict UNCHANGED (scores/skip/anchor untouched — Q3b), anchor UNCHANGED float (Q7), detect() on-grid → 0 records (rotation-persist evidence), info box carries the pinned reset line (D4 wording). Restore per PART C.
- PART F (T1b — `_guard` refusal path): no wizard (post-cleanup state) → `_on_reset_grid` click → silent no-op (no box, no crash — the H-8 contract); unexpected-exception propagation is already covered by the 04-09 contract tests — no re-proof needed.

**RESET smoke sketch (T1a core, the SMOKE-06/07 hybrid):**

1. `start_game()` live; script a moved pose + an explicit `cmd.rotate`-baked orientation change on one AA (the SMOKE-06 movement-spike recipe — smoke_06_spike_movement.py's drive; rotate about the object centroid with the identity-assert read-back).
2. Record pre-Reset: centroid, anchor float, game_status to_dict, `get_status()` selection.
3. Drive `wiz.reset_grid()` (the wizard's own public path — the same seam the tab will call) via method drive; assert: centroid == `effective_position(pose, offset)` within tolerance for EVERY slot of the level (all molecules — placement.py:425-426), orientation PERSISTED (compare the baked coords against the scripted rotate+translate replay within the 5e-6 Å / 3e-4 deg metric class — or the SMOKE-06 count-evidence: detect() == 0 records on-grid with the orientation residual), identity matrix reads identity for every snapshot object, `_result` None, selection persisted, anchor unchanged, to_dict unchanged.
4. Engine-precondition refusals: fresh module state (nothing materialized) → `engine.reset_to_grid()` raises EngineError naming no-registry/no-payload (engine.py:115-120, :347-350) — WSL-testable shape for the message pins? No — cmd tier; assert in the smoke.

**[HUMAN] checkpoint items (per ROADMAP criterion 5's [HUMAN] half):**
- Restart feel: countdown 3-2-1 visible after pressing Restart; scene rebuilds; timer resets to 0:00 during countdown; required label resets; wizard panel fresh; status poll re-observes the fresh game silently.
- Restart from a game with a DORMANT user wizard beneath (auto-resume after the restarted game's Done — the deferred variant of SMOKE-08 PART 4's GUI confirmation).
- Reset mid-rotation feel: a rotated AA keeps its orientation (Phase-9 help-text reserve note "orientation is kept" — wizard.py:592-593), selection stays green/recolored, the panel result line clears.
- Reset while the 1 Hz clock runs: label keeps advancing (not frozen) — not headlessly provable beyond the data-level anchor check.
- Give-Up→Restart/Reset interplay once SCORE-06/07's design exists (modal vs info-box endgame — §2 Q5).
- Restart with `_last_start` from an UPLOADED game (restart replays the uploaded molecules without re-ingesting — verify the feel; headlessly the candidates/ligand_content replay is covered by the PART A variants with an uploaded sentinel if smoke budget allows).

## (8) Decision Candidates

- **D1 — Restart with nothing started (`_last_start is None`):** fail-closed ValueError refusal surfaced by `_guard` ("Restart: no game has been started yet.") vs Hint-style silent no-op. Recommendation: refusal (house fail-closed + spec UI standard; the op is not gated behind an active wizard the way Hint's dispatch is). Low risk either way.
- **D2 — the 'game_restarted' info-box line:** handler-logged (tab) vs relying on the countdown sequence alone. Constraint: `start_countdown` CLEARS the info box (game_window.py:174), so a pre-chain line is wiped — log AFTER `start_countdown` arms, or don't log at all. The poll CANNOT emit lifecycle lines (positions/`_last_start` are not in `_state_dict`; 'result' never fingerprinted — status_text.py:151-155). Recommendation: log the pinned line right after the countdown arms (matches the reserved kind, status_text.py:72; wording pinned by the plan).
- **D3 — handler home:** Restart/Reset handlers on GameTab (next to `_on_hint`, using GameTab._guard; the Reset impl dispatches via cmd tier and needs no window state; the Restart impl reads `gamestart._last_start` — also no window state) vs SetupWindow-side (mirroring `_start_impl`). Recommendation: GameTab-owned (the spec places both buttons on the Game status tab, spec.md:46-47; GameTab._guard exists; no window seam needed). The tab-switch step degenerates (tab already current); if the planner wants absolute symmetry with `_start_impl`, SetupWindow-side also works — recorded either way.
- **D4 — the 'game_reset' pinned line wording:** e.g. 'AA reset to grid positions (orientations kept).' — plan pins verbatim; the EVENT_KINDS role note stays "grid-reset line" (status_text.py:71-72).
- **D5 — game-over marker for Give Up (inter-phase contract with the SCORE-06/07 plans):** whatever marks "ended" must die with the GameState or the wizard instance (both replaced on Restart), never module-level, or Restart would inherit a stale ended flag. Also: the endgame render half (info box vs modal) decides the Give-Up→Restart UX. Recommendation: pass this constraint to the SCORE-06/07 planning; the Restart plan only asserts "Restart works identically on an ended game" in a [HUMAN] item (§7).
- **D6 — the dormant-user-wizard stack-hole (pre-existing, document-only):** user wizard mid-game → Start/Restart → old game wizard buried beneath → Done ×2 surfaces a STALE wizard (registry → deleted objects). Identical in today's `_start_impl` (05-09 P-3 pops a GameWizard TOP only; no stack-walking API exists). Recommendation: record in the plan docstring + open question; no Phase-6 fix (out of scope, edge-class, pre-existing). SMOKE-08 PART 4's proven replace=1 branch and the window path's pre-pop cover the two non-buried cases.
- **D7 — GameTab attribute naming for the new buttons:** e.g. `btn_restart` + `btn_reset_grid` (distinct from SetupWindow's `btn_reset`) — avoids the smoke assert ambiguity (§7). Labels stay spec wording 'Restart'/'Reset' (spec.md:46-47).
- **D8 — Reset reachable during the countdown?** The isinstance gate makes it a silent no-op pre-GO (Q2) — correct because AAs are already at grid poses. No change needed; recorded so the planner doesn't add a countdown-state check.

## Open Questions

1. **Give Up / SCORE-07 endgame design (owned by the sibling Phase-6 plans):** the endgame render surface (info box vs modal), the game-over marker home (D5), and whether the endgame pops the wizard. This research proves Restart composes with EITHER design (§2 Q5) but the sibling plans should decide first if the Restart plan's smoke wants a Give-Up-then-Restart drive.
2. **Confirm-history semantics after Reset (SCORE-01 plan's scope):** Reset does not retract a recorded score (§2 Q3b) — the SCORE-01 plan owns whether re-Confirm appends or replaces. The Reset plan should not claim score-undo behavior.
3. **Import replay (Phase 7) interplay:** a Phase-7 Import presumably calls `start_game` with the imported setup/seed, re-capturing `_last_start` — making Restart replay the IMPORTED game. Not constrained yet; recorded so Phase-7 planning inherits the note.

## Sources

### Primary (HIGH confidence)
- `aamatch/gamestart.py` — whole file read (start_game/activate_game/_last_start/compose/cleanup ordering; lines 1-424)
- `aamatch/wizard.py` — whole file read (reset_grid/_reset_grid_impl/_guard/activate/cleanup/ORDER LAW; lines 1-710)
- `aamatch/engine.py` — whole file read (new_game/materialize/reset_to_grid/game_status; lines 1-478)
- `aamatch/game_state.py` — whole file read (GameState construction/anchor/rebase/record; lines 1-277)
- `aamatch/game_window.py` — whole file read (GameTab/tick/countdown/_guard/hint family; lines 1-371)
- `aamatch/setup_window.py` — whole file read (_pop_game_wizard/_start_impl/_on_cleanup/_guard; lines 1-1038)
- `aamatch/placement.py` — reset_to_grid/cleanup_game_objects/pose tolerance (lines 84-188, 400-455)
- `aamatch/backup.py` — whole file read (module surface; lines 1-248)
- `aamatch/status_text.py` — whole file read (EVENT_KINDS/diff rules; lines 1-180)
- `aamatch/wizard_text.py` — panel button inventory (lines 30-74, 193-202)
- `aamatch/setup_state.py` — validate_state non-aliasing proof (lines 90-144)
- `smoke/smoke_08_starter.py` — restart-identity + replace paths (lines 41-73, 146-162, 479-568)
- `smoke/smoke_11_window.py` — PART H deferred drive + _last_start pins (lines 805-990)
- `spec.md:33-58` — SCORE-09/10/06/07 spec wording
- `.planning/STATE.md:105-136, 139-141, 161-193, 202-213` — decisions 02-10/03-03/03-05/03-06/05-05/05-06/05-07/05-08/05-09/05-10
- `.planning/research/PITFALLS.md` §144-165 (PITFALL 6), §218-238 (PITFALL 9)
- `.planning/ROADMAP.md:160-171` — Phase 6 requirements + research notes
- `.planning/phases/03-wizard-gameplay-loop/03-03-SUMMARY.md` — reset decision (key-decisions :35-39)
- `.planning/phases/05-game-status-tab-start-sequence/05-05-SUMMARY.md` — _last_start capture decisions
- `.planning/phases/05-game-status-tab-start-sequence/05-06-SUMMARY.md` — Rule-2 timer-stop deviation (:110-118)
- `.planning/phases/05-game-status-tab-start-sequence/05-08-SUMMARY.md` — GameTab handler family contract
- `.planning/phases/05-game-status-tab-start-sequence/05-09-SUMMARY.md` — deferred start sequence + Restart affects note
- `tests/test_backup.py` — backup module contract (15 tests)

### Secondary (MEDIUM confidence)
- `.planning/phases/03-wizard-gameplay-loop/03-06-SUMMARY.md` — msm field-verified law (§41, §75, §139)

### Tertiary (LOW confidence)
- The dormant-user-wizard stack-hole analysis (§3 D6): reasoned from the recorded design (wizard.py:31-39, setup_window.py:826-845) — no runtime probe of the Done×2 stale-surfacing was run; document-only, pre-existing class.

## Metadata

**Confidence breakdown:**
- Restart seam (_last_start replay): HIGH — every step cited in gamestart.py/engine.py/setup_window.py; SMOKE-08/11 pins.
- Reset mechanism + owner: HIGH — placement/wizard/engine read whole-file; the 05-07/05-10 laws verified against today's grep state.
- Cross-game ledger: HIGH — each row cites the resetting call site.
- Smoke shapes: HIGH — copied from pinned PART patterns (smoke_08/11) with the 03-05 instance-marker law applied.
- Give-Up interplay: MEDIUM — no SCORE-06/07 code exists; composition argued from the pop-gate + replay determinism (design-independent).
- backup.py no-role verdict: HIGH — grep receipt (zero aamatch/ consumers) + recorded 05-05 decision.

**Research date:** 2026-09-20
**Valid until:** stable (repo-internal research; re-verify only if gamestart/wizard/game_window change materially)

## RESEARCH COMPLETE
