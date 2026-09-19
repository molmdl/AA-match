# Phase 6: Scoring Lifecycle & Endgame — Research (Lifecycle-Core scope)

**Researched:** 2026-09-20
**Domain:** AA-match scoring lifecycle core — Confirm→advance, score accumulation, molecule/level progression, Skip/Give-Up termination, status-event emission (SCORE-01/02/03/05/06/07-data/09-state/10-wiring)
**Confidence:** HIGH (every claim below is verified against the current repo source with file:line; this is a codebase research, not a library research — no external APIs are involved)

**Scope note:** The endgame SCREEN (Qt widget) is another researcher's scope. This document owns: the lifecycle ops' semantics, the state/data shapes, the event-emission mechanism, the timer-stop data, and the Restart/Reset state contracts.

---

## 1. Current-state map — every seam the lifecycle touches

| # | Seam | File:line | Today's behavior | Phase-6 relevance |
|---|------|-----------|------------------|-------------------|
| 1 | `GameState` fields | aamatch/game_state.py:168-175 | `current_level_index`, `current_molecule_index`, `molecule_scores` (flat list), `skip_count`, `giveup_count`, `timer_anchor`, `formed_types_per_molecule` | The data container the lifecycle mutates; needs additive end-state fields |
| 2 | `GameState.advance_molecule/advance_level` | game_state.py:226-233 | Defined, **ZERO callers in aamatch/** (verified by grep; only tests/test_game_state.py:149-158 exercises them) | Dead transitions awaiting a lifecycle owner |
| 3 | `record_molecule_result` | game_state.py:235-248 | Appends score to `molecule_scores` + writes `formed_types_per_molecule['L{n}M{n}']` in ONE call; **no duplicate-record guard** (re-Confirm appends again) | Confirm/Skip wire around it; the written key IS the "already scored" marker |
| 4 | `total_score` property | game_state.py:182-185 | `sum(molecule_scores)`; consumed by NO runtime code yet | SCORE-01 running total |
| 5 | `start_timer` / `rebase_timer` | game_state.py:187-191 / 193-224 | Anchor set at GO (gamestart.py:339); rebase = modal-pause freeze (1 Hz tick) | SCORE-07 stopped timer needs a freeze/capture op beside these |
| 6 | `engine.confirm` | engine.py:462-469 | `detect_molecule` + `score_current` → `(records, score, formed)`; **no advance** | The op Phase 6 wraps with lifecycle semantics |
| 7 | `engine.score_current` | engine.py:443-459 | `record_molecule_result` via `_current_game()`; returns `(score, formed)` | Skip reuses the same record path |
| 8 | `engine.detect_molecule` | engine.py:370-401 | Molecule-scoped detection (03-06 cross-molecule guard) | Skip's partial-score detection pass |
| 9 | `engine.new_game` | engine.py:239-300 (GameState reset at :295) | Creates a **fresh GameState** — wipes scores | Restart is safe through start_game; level-advance must NOT route through new_game |
| 10 | `engine.materialize(payload, level_index)` | engine.py:303-320 → placement.py:234-412 | Materializes ONE level (all its molecules); **does not delete prior objects** | Level-advance build path (after `cleanup_game_objects`) |
| 11 | `engine.reset_to_grid` | engine.py:343-352 → placement.py:415-439 | Spec REPLAY of ALL AAs of the current level (both molecules); rotations persist | SCORE-10's mechanism — exists; only the tab button is missing |
| 12 | `engine.game_status()` | engine.py:472-478 | READ-only 7-key `GameState.to_dict()` snapshot | The lifecycle's read path; key set is pinned by SMOKE-14 (smoke/smoke_14_status_surface.py:206-208) → additive growth = deliberate test evolution |
| 13 | `GameWizard.__init__` position attrs | wizard.py:126-143 | `_level_index`/`_molecule_index` set at construction, **never mutated anywhere in Phases 3–5** | The wizard-side position book; must be advanced + re-synced with GameState |
| 14 | `GameWizard._slot_by_object/_objects_by_slot/_ligand_object` | wizard.py:132-138 (built via `wizard_core.build_slot_map`, wizard_core.py:64-120) | Scoped to ONE molecule index | Molecule advance = rebuild these maps for the new index (no re-materialization) |
| 15 | `confirm_molecule` / `_confirm_molecule_impl` | wizard.py:544-584 | engine.confirm + extras computation + `_result` set; docstring CAVEAT (:550-553): "repeated Confirm appends … score-history semantics are Phase 6's lifecycle" | The op to rework into record→show→advance |
| 16 | `reset_grid` / `_reset_grid_impl` | wizard.py:586-610 | engine.reset_to_grid + identity asserts + `_result=None`; selection + recolor persist | Already SCORE-10-correct; needs the tab button + event emission |
| 17 | `_guard` | wizard.py:436-449 | Catches ValueError family → `_error` + refresh; **returns the op result** (None on refusal) | The data-delivery seam for new lifecycle ops (05-08 law) |
| 18 | `_state_dict` / `get_status` | wizard.py:333-356 / 358-362 | 9 plain keys (+ level keys); `'result'` at :354 | The poll-diff source; needs additive event/game-over keys |
| 19 | `gamestart.start_game` | gamestart.py:342-424 | cleanup-first (:382) → new_game (:384) → materialize (:386) → compose (:405-407) → `_last_start` capture (:413-416) → activate | Restart replays `_last_start` verbatim through this seam |
| 20 | `gamestart._last_start` | gamestart.py:178, capture contract :167-177, :413-416 | Deep-copied `{'setup','seed','candidates','ligand_content'}` after every successful start | SCORE-09's replay source (binding decision a) |
| 21 | `gamestart.activate_game(wiz)` | gamestart.py:323-339 | Conditional replace re-eval + **`start_timer(time.time())` — ALWAYS re-anchors the clock to zero** | Level advance must push a wizard WITHOUT re-anchoring → needs an additive param or a separate push path |
| 22 | gamestart compose helpers | gamestart.py:181-196 (`_active_molecule_selection`), :199-254 (`_frame_ligand_above_grid`), :257-320 (`_move_ligand_in_front`) | All hardcoded to `registry['molecules'][0]` | Docstring :105-108 explicitly assigns molecule-advance re-framing to Phase 6 |
| 23 | `status_text.status_events` | status_text.py:143-180 (fingerprint keys :44-45) | Diffs `molecule_id, molecule_pos, molecule_total, level_pos, selected.slot_id, error`; **`'result'` NEVER fingerprinted** (:152-154) | The emission channel for the reserved kinds |
| 24 | `status_text.EVENT_KINDS` | status_text.py:49-75 | 15 kinds; 6 reserved Phase-6: `molecule_scored` :66, `molecule_skipped` :68, `gave_up` :69, `level_advanced` :70, `game_reset` :71, `game_restarted` :72 (wording deliberately NOT pinned — test_status_text.py:322-326 only pins the "reserved for Phase 6" marker) | Phase 6 research pins the final text (this doc, §5) |
| 25 | `wizard_text.result_lines` | wizard_text.py:106-175 | TEXT-ONLY debrief: `N/M required interactions formed (score x.xx)` / `Formed: …` / `Missing: …` / `Formed (not required): …` | SCORE-02's renderer already exists — reuse verbatim (single-home law) |
| 26 | Panel button inventory pin | wizard_text.py:53-59 + tests/test_wizard_text.py:169-189 | Exactly {movement…, Confirm, Reset to Grid, Done} with pinned codes | Adding panel buttons = deliberate test evolution; NOT required by spec (buttons live on the tab) |
| 27 | `GameTab` shell | game_window.py:78-371 | Info box `_log` (:150-157), 1 Hz tick (:257-287), `_refresh_status` poll-diff (:291-328), `_guard` (:332-343, ValueError+OSError → `QMessageBox.warning`), `_on_hint`/`_hint_now` (:345-371), button row with **stretch reserved for lifecycle buttons** (:118-125) | The tab is the spec-mandated control surface (spec.md:36-46); hint is the handler-logs-via-result precedent |
| 28 | `GameTab._refresh_status` label condition | game_window.py:323-327 | Refreshes the required label only when `prev is None or molecule_id changed` | **BUG on level advance**: `molecule_id` repeats across levels ('mol-001' again — generator.py:739-741) → stale required label. Must also compare `level_pos` (or `required`) |
| 29 | `GameTab.start_countdown` | game_window.py:161-177 | **CLEARs the info box** (:174) then 'Get ready…' | Any restart line logged before it is wiped — ordering constraint for `game_restarted` |
| 30 | `GameTab._begin_play` | game_window.py:195-221 | `activate_game` + first level line + seeds `_last_status` (first poll silent) | Restart re-enters this path; the timer re-anchors here (correct for restart) |
| 31 | `SetupWindow._pop_game_wizard` / `_start_impl` | setup_window.py:826-838 / :953+ | isinstance pop; pop→prepare(activate=False)→tab→countdown | The restart handler clones this sequence with `_last_start` instead of `collect_state` |
| 32 | Purity registry | tests/test_purity.py:94 (`PURE_MODULES`), AST scan all scopes | status_text + wizard_text + game_state are gated pure | New pure code must be registered; game_state stays stdlib-only (time + setup_state) |
| 33 | SCANNED_MODULES | tests/test_wizard_source.py:51-54 | wizard.py, gamestart.py, setup_window.py, game_window.py | New cmd/Qt-tier files (if any) must be appended |
| 34 | Smoke pins | smoke/smoke_14_status_surface.py:206-208 (exact 7-key game_status), SMOKE-08 (start seam), SMOKE-07 (wizard loop) | Regression teeth | Lifecycle changes re-run these; SMOKE-14 grows additive PARTs |

---

## 2. Answers to the ten questions

### Q1 — What does Confirm do today; where is advance bookkeeping; who must own it?

**Confirm today = detect + record only.** `engine.confirm(level, molecule, required)` (engine.py:462-469) composes `detect_molecule` (engine.py:370-401, the 03-06 molecule-scoped pass) + `score_current` (engine.py:443-459), which calls `GameState.record_molecule_result` (game_state.py:235-248) — that appends the score to the flat `molecule_scores` list and writes `formed_types_per_molecule['L{n}M{n}']`. **Nothing anywhere advances.** The wizard's `_confirm_molecule_impl` (wizard.py:556-584) renders the result into `_result` and stops.

**There are TWO position books, both stale-prone:**
- Wizard: `self._level_index` / `self._molecule_index` (wizard.py:130-131) — fixed at construction, never mutated in Phases 3–5. All engine ops receive these as arguments (wizard.py:559-561).
- Engine: `GameState.current_level_index` / `current_molecule_index` (game_state.py:169-170) — with ready-made `advance_molecule()`/`advance_level()` transitions (game_state.py:226-233) that have **zero callers in aamatch/** (verified by grep).

**What a new lifecycle op must call to advance:**
- *Molecule advance (same level):* NO scene rebuild. The registry already holds ALL molecules of the level (placement.materialize builds every molecule, placement.py:299-411). Advance = (i) `GameState.advance_molecule()` (or equivalent engine data-op), (ii) wizard rebinds `_molecule_index`, `_slot_by_object`/`_objects_by_slot` (via `wizard_core.build_slot_map(registry, new_index)`), `_ligand_object` (registry.py:137-138 shape), clears `_current_slot` (restoring the selected slot's colors first — the `_select_slot` restore-first pattern, wizard.py:317-319), clears `_result`, (iii) camera re-frame onto the new molecule (Q6).
- *Level advance:* (i) `placement.cleanup_game_objects()` (placement.py:442-455, prefix-only deletion) — otherwise stale objects accumulate and `get_unused_name` names drift, (ii) `engine.materialize(payload, L+1)` → NEW registry (new `_aam_*` names), (iii) `GameState.advance_level()` (resets molecule index, game_state.py:230-233), (iv) a NEW `GameWizard(payload, new_registry, L+1, 0)` pushed with the conditional-replace rule (a GameWizard is top-of-stack → replace=1, mirroring gamestart.py:337-338), (v) camera compose for molecule 0 of the new level, (vi) **DO NOT re-anchor the timer** (Q8).

**Ownership recommendation:** the ENGINE owns data transitions + the level re-materialization (new ops, e.g. `engine.advance_level() -> registry`, `engine.skip_molecule(...)`, `engine.give_up()`); the WIZARD owns scene-side rebinds + camera + a single atomic wizard-level op per transition that calls the engine op and then rebinds itself — this keeps the two books in sync by construction (one code path mutates both) and honors ARCHITECTURE Pattern 2 ("the engine is the brain", wizard.py:10-15).

### Q2 — How is the molecule score computed; what is the running-total shape?

- The SCORE-01 fraction is exactly `game_state.score(required, results)` (game_state.py:62-85): `'any'` binary (≥1 record of any type → 1.0), `'list'` = formed items / items, binary per item, counts never inflate. `engine.confirm` already returns it.
- **Running total** = `GameState.total_score` (game_state.py:182-185) = `sum(molecule_scores)`. It is a property over the flat append-only list; no runtime code consumes it yet.
- **Shape caveat:** `molecule_scores` is a FLAT list with no level/molecule keying. Per-level scores (SCORE-07) are derivable only as `sum(molecule_scores[L*m : (L+1)*m])` — valid **only under a strict one-record-per-molecule invariant** (every molecule recorded exactly once, in play order). That invariant does not exist yet (re-Confirm appends — Q10). Two remedies: (a) the lifecycle enforces one-record-per-molecule (refusals) and the arithmetic is documented + tested, or (b) add an additive keyed store (e.g. `score_per_molecule: {'L0M0': 0.5}`) written by `record_molecule_result` alongside the flat list — robust for Phase-7 persistence too. Recommended: (b), flagged as a decision candidate (§5).
- Spec 7.3 ordering: "calculate and show the molecule's score and total score til the stage, **then** move to the next molecule" — the total shown must INCLUDE the just-recorded molecule (record → total → advance).

### Q3 — What does the debrief need; where does rendering live?

- **The debrief renderer already exists**: `wizard_text.result_lines(score, formed, required, extras)` (wizard_text.py:106-175) renders 'N/M required interactions formed (score x.xx)', 'Formed: …'/'Formed: (none)', 'Missing: …' (omitted when none), 'Formed (not required): …' — text-only, PLAY-04-conformant, WSL-pinned by tests/test_wizard_text.py.
- **Missing/formed derivation** is internal to `result_lines` (from `required` + `formed`); the 05-status-surface event inventory (05-RESEARCH-status-surface.md:284) already sketches the info-box line as "`Molecule %s scored %.2f (total %.2f).` + `result_lines(...)` verbatim".
- **Home:** `result_lines` STAYS in wizard_text (the panel's pure surface); `status_text` reuses it cross-module — exactly the `required_summary` precedent (status_text.py:40 imports `required_summary` from wizard_text; single-home law, 05-01). New per-kind event line builders live in **status_text** (the tab's wording home per the 05-01 law); the wizard panel keeps its existing result rendering unchanged.
- Data the event must carry: score (float), total (float, post-record), formed types, required dict, extras — all plain data the op already has or can compute (extras logic is in `_confirm_molecule_impl`, wizard.py:567-580; it should move/be shared so both surfaces emit identical debriefs — do not duplicate the extras computation).

### Q4 — What does Skip's "partial score" mean numerically?

**Sanctioned answer (from the Phase-2 record):** run the molecule-scoped detection AT SKIP TIME and record the CURRENT live fraction via the same `record_molecule_result`, then `skip_count += 1`, then advance. Evidence:
- 02-10-SUMMARY.md:93: "Skip semantics note for the engine: SCORE-01 says 'skip stores partial score' — a skip path should **record the current partial fraction via the same `record_molecule_result`** (score is append-only per molecule) and increment `skip_count`."
- STATE.md:106 (02-10 decision): "skip-path guidance = record partial score via the same call + increment skip_count."
- PROJECT.md frozen decision: "Score = fraction of required interactions formed, binary per interaction; **skip stores partial score**."
- spec.md:44: "skip mol give a warning for confirmation then store only up to current score of the molecule, move to the next molecule."

So Skip ≈ Confirm's detection+record, plus the counter, plus the skip event line. The alternative reading ("skipped molecule contributes 0") contradicts the recorded engine guidance. Residual ambiguity is low but the wording is human-visible → flagged as a decision candidate (§5 D1) for a one-line human confirmation, not a redesign.

### Q5 — Give Up: what marks "game over"; what must the endgame data aggregate; what happens to the wizard/scene?

- **Nothing marks game over today** (grep for `game_over`/`give_up`/`final_time` in aamatch/ → only the `giveup_count` counter, game_state.py:173). Gap.
- **Needed GameState additions (additive):** an end-state flag + reason + frozen time, e.g. `game_over` (bool), `end_state` (`None | 'completed' | 'gave_up'`), `final_time` (float | None). `giveup_count += 1` on Give Up. The current molecule is **NOT scored** by Give Up (spec.md:44-45 gives partial-store to Skip only; Give Up just "end[s] the game at the stage").
- Two end paths set the flag: Give Up (SCORE-06) and natural completion (the Confirm that records the last molecule of the last level — no advance target exists). Both freeze the timer (Q8) and feed the same endgame data.
- **Endgame data aggregate (SCORE-07):** per-level scores (Q2), total score, final time, total levels (D = `len(payload['levels'])`), total molecules (D × molecules_per_level — every level has exactly m molecules, generator.py:798-806), skip_count, giveup_count, end_state (drives "winning message" vs gave-up message). Recommend a PURE builder (e.g. `game_state.endgame_summary(...) -> plain dict`) wrapped by a thin READ-only engine op — ARCHITECTURE.md:88's aspirational "scoring.py — score computation, level totals, endgame summary" maps here (module-home decision candidate, §5 D8).
- **Wizard/scene after Give Up:** recommend the wizard STAYS on the stack (scene intact, colors restorable via Done) and every gameplay handler gates on `game_over` with a visible refusal ('The game is over.' — lands on the panel error line via `_guard`, or the tab warning box via its `_guard`). The player exits via Done (canonical) or Restart. Alternatives (self-pop; frozen-but-silent wizard) in §5 D5. The Game tab's lifecycle buttons must equally gate on game_over (no double give-up, no confirm-after-end).

### Q6 — What does "higher difficulty" mean mechanically; what is re-materialized; which existing call?

- **Difficulty is baked at generation time.** `generator.difficulty_params(D, L)` (generator.py:144-178) computes per level: `grid_n = 3+frac` (3..9), `n_required_types = 1+frac` (1..7), size class by level thirds — monotonic in L. `generate()` bakes ALL D levels into the payload up front (generator.py:798-806); each level carries exactly `molecules_per_level` molecules.
- **Therefore level advance needs NO regeneration:** `engine.materialize(payload, L+1)` (engine.py:303-320) after `placement.cleanup_game_objects()` is the whole build path. The payload is already on the engine (`_payload`, engine.py:102, 293, 318).
- **Per-molecule:** nothing is re-materialized (Q1) — the level registry already holds all m molecules.
- **Camera re-frame:** gamestart's compose helpers are hardcoded to molecule 0 (`_active_molecule_selection` gamestart.py:193, `_frame_ligand_above_grid` :216, `_move_ligand_in_front` :296) and the gamestart docstring (:105-108) **explicitly assigns molecule-advance re-framing to Phase 6**: "re-framing when the active molecule advances is a start-sequence / scoring-lifecycle concern (Phases 5/6), NOT gamestart's". Recommended: generalize the three helpers with a `molecule_index=0` default parameter (byte-identical for existing callers/SMOKE-08) and call them with the new index from the lifecycle ops. Note `_move_ligand_in_front` translates the ligand ~5 Å toward the camera — chemistry-profile reads stay byte-equal (translation-invariant; the ligand_profile_molecule byte-equality argument, engine.py:417-426, is about chemistry, not position), and detection reads live geometry, so a re-fronted ligand is consistent with the start-molecule feel (spec.md:47 "the small molecule is fixed in the middle of the UI" per molecule).

### Q7 — Reserved EVENT_KINDS: exact state-dict deltas so the EXISTING poll-diff emits them WITHOUT fingerprinting 'result'

**Current diff machinery** (status_text.py:143-180): fingerprints `molecule_id, molecule_pos, molecule_total, level_pos` (:44-45) + `selected['slot_id']` + `error`; `'result'` is deliberately NOT fingerprinted (:152-154; pinned by tests/test_status_text.py:265-272). Position changes ALREADY emit the `level_molecule` line — so molecule/level advance lines come free once the wizard's indexes move.

**Recommended design — an event marker in the wizard state dict (NOT 'result'):**
- `GameWizard` gains two plain attributes: `_event_seq` (int, monotonic per wizard instance) and `_last_event` (None or a plain dict). Every lifecycle op that succeeds sets `_last_event = {'kind': <reserved kind>, 'seq': _event_seq, ...payload}` and increments the seq. Payload fields per kind:
  - `molecule_scored`: `{'score': float, 'total': float, 'molecule_pos': int, 'formed': [...], 'required': {...}, 'extras': [...]}` (status_text renders the header line + `result_lines` verbatim — the debrief rides the event).
  - `molecule_skipped`: `{'score': float, 'total': float, 'molecule_pos': int}`.
  - `gave_up`: `{'total': float, 'molecule_pos': int, 'level_pos': int}`.
  - `level_advanced`: `{'level_pos': int}`.
  - `game_reset`: `{}` (Reset changes no fingerprint key — the marker is the ONLY way the diff can see it).
  - `game_restarted`: emitted by the restart flow (see the ordering caveat below).
- `_state_dict()` (wizard.py:333-356) gains ADDITIVE keys: `'last_event': self._last_event`, `'game_over': <bool>`, `'end_state': <str|None>` (read from the engine's GameState or mirrored at op time — one home is GameState; the wizard surfaces it). All plain data → contract-2 picklable.
- `status_text.status_events` learns ONE new fingerprint key (`last_event`) and emits, per kind, via NEW pure line builders (e.g. `molecule_scored_line(event)`, `molecule_skipped_line(event)`, `gave_up_line(event)`, `level_advanced_line(event)`, `game_reset_line(event)`). The `seq` counter makes identical consecutive events (e.g. two Resets) distinct — no sticky-dedupe ambiguity. Emission ORDER: event line(s) FIRST, then the level/molecule line, then selection, then error (the score line describes the completed molecule; the position line announces the new one) — planner to pin.
- **Why NOT fingerprint `'result'`:** `_result` is set by Phase-3 confirm on every press (including refused/repeat paths), its identity churn is not event-shaped, and the pitfall-7 reserve (05-RESEARCH-status-surface.md:192-193, tests/test_status_text.py:265-272) pins it out. The marker is event-shaped by construction and never violates the reserve.
- **Latency + loss property and the fix:** the poll runs at 1 Hz; two ops within one tick would lose the first event (only the last marker survives the prev/curr diff). Fix: the tab handlers call `self._refresh_status()` SYNCHRONOUSLY right after a successful op — the same poll-diff runs immediately (emitting event + level lines in order) and refreshes `_last_status`, so the next tick is silent. This gives tab-triggered ops zero-latency logging, no duplicates, and the 1 Hz tick remains the safety net for PANEL-triggered ops (the panel's Confirm/Reset buttons call the same wizard ops without a handler — their events surface at the next tick, ≤1 s). The tab stays a dumb renderer; ALL wording stays in status_text.
- **GameState-dict deltas** (engine.game_status(), additive): `game_over`, `end_state`, `final_time` (+ optionally the keyed per-molecule score store, Q2). SMOKE-14's exact-7-key pin (smoke/smoke_14_status_surface.py:206-208) is a deliberate test evolution.
- **`game_restarted` ordering caveat:** `start_countdown` CLEARS the info box (game_window.py:174), so a restart line logged before it is wiped. Options in §5 D7.

### Q8 — Timer stop: what mechanism; what does "stop" mean for the anchor; who is the caller?

- There is ONE clock home: `GameState.timer_anchor` (game_state.py:174, 187-191); the 1 Hz tick computes `time.time() - anchor` live (game_window.py:237-248, P-4 law) and REBASES the anchor while a modal child is open (game_window.py:276-283, 05-04 op).
- **"Stop" should mean: capture the final elapsed once at game-over and freeze the render.** Recommended pure op beside `rebase_timer`: e.g. `GameState.stop_timer(now=None)` → stores `final_time = max(0.0, now - anchor)` (0.0-tolerant for a never-started game, matching rebase's totality) and sets `game_over`. The anchor itself can stay untouched (it is the pause mechanism's home; a second "frozen anchor" field avoids disturbing P-4 semantics). The 1 Hz tick then renders `final_time` when `game_over` (Qt integration — the UI researcher's plan consumes the flag; the modal-pause rebase branch should early-return when game_over).
- **Who is the caller:** the lifecycle ops (Give Up / last-molecule Confirm) run inside Qt button handlers — the handler's confirmation `QMessageBox.question` is a modal CHILD, so the existing rebase branch freezes the clock during the warning automatically (game_window.py:276-283). The op captures `final_time` AFTER the modal closes (i.e., at op execution time). The `rebase_timer` docstring's law ("the CALLER owns modal detection", game_state.py:207-209) is unchanged: the 1 Hz tick remains the only modal detector; lifecycle ops never touch Qt.
- **Restart** re-anchors from zero via `activate_game` → `start_timer(time.time())` (gamestart.py:339) — correct for a fresh game. **Level advance must NOT** re-anchor (the game clock runs across levels) — hence the `activate_game` additive param (§5 D6).

### Q9 — Purity / test-tier constraints binding the new code

- **Pure tier (WSL-testable, stdlib-only, 3.6 syntax, %-formatting, no dataclasses):**
  - `game_state.py` additions: stop/final-time op, optional keyed score store, per-level/endgame summary builders. It already imports only `time` + `setup_state` (game_state.py:38-40) — keep it that way. MUST be registered in `PURE_MODULES`-adjacent fashion (it already is; new pure MODULES would need registration at tests/test_purity.py:94).
  - `status_text.py`: the 6 new event-line builders + the extended `status_events` diff. Imports stay `wizard_text`-only (status_text.py:40).
  - Existing pins that GROW deliberately: `EVENT_KINDS` 15-key set (test_status_text.py:308-315 — the key set is pinned; values only carry phase markers), `status_events` rules (new tests additive; existing ones unchanged), `GameState.to_dict` round-trip (new fields must round-trip — test_game_state.py:194-231 pattern).
- **Cmd tier** (`pymol` allowed at module level; NEVER in PURE_MODULES): `engine.py` (lifecycle ops), `wizard.py` (lifecycle methods + state-dict extension), `gamestart.py` (helper generalization + `activate_game` param). Lazy relative imports inside methods where module identity matters (wizard.py:22-29 law).
- **Qt tier** (`from pymol.Qt import ...` at module level legal there; never WSL-imported): `game_window.py` (buttons, modal wrappers, sync-refresh calls; the endgame screen is the other researcher's plan). `SCANNED_MODULES` already covers game_window.py (tests/test_wizard_source.py:51-54); append any new cmd/Qt module per the growth protocol.
- **Standing gates (AGENTS.md):** `python3.6 -m py_compile aamatch/*.py`; `python3.6 -m unittest discover -s tests -v` (INCLUDES tests/test_purity.py — no sys.modules stubs anywhere); `bash smoke/run_smoke.sh smoke/<script>.py` with the `=== SMOKE-0N PASS ===` grep verdict.
- **T1b offscreen-Qt recipe is AVAILABLE** (04-01 probe verdict, STATE.md:142, 268) but **ZERO modals headless** (smoke-99 law, STATE.md:163): a static QMessageBox blocks indefinitely under offscreen. Therefore the 04-09 `_X_impl` factoring rule is BINDING for the confirmation warnings: thin modal wrapper (`_on_skip`: `QMessageBox.question(...)` → Yes → `self._guard(self._skip_impl)`) around a NON-MODAL impl the smoke drives directly. The warning text itself can be pinned as a pure string (status_text or a module constant) so WSL tests pin the wording even though the box is human-only.
- **PROSE_PIN heads-up** (STATE.md:271): any docstring adding/removing a banned-token mention requires a deliberate tests/test_code_audit.py update.
- **Module-identity law:** new panel-button codes (if any) must remain `cmd.get_wizard().method(...)` strings (wizard_text.py:20-29); new tab handlers use the lazy `from . import wizard` + isinstance gate (game_window.py:313-316 pattern).

### Q10 — Confirm-advance + the Phase-3 re-Confirm caveat: the new contract

**Recommended contract: refuse, do not re-record.**
- **Guard condition (already derivable, zero new state):** `GameState.molecule_key(level, molecule) in formed_types_per_molecule` — `record_molecule_result` writes that key UNCONDITIONALLY on every record, including a 0.0 score with an empty formed list (game_state.py:246-247; pinned by tests/test_game_state.py:186-191). Key presence == "this molecule already produced a record (Confirm or Skip)".
- **Behavior:** a second Confirm (or a Skip) on an already-recorded molecule raises `ValueError` (WizardError/EngineError family) with a message naming the cause, e.g. `'This molecule already has a recorded result (scored or skipped) -- use Restart to replay the game.'` It lands on the wizard panel error line via `_guard` (wizard.py:444-449) or the tab's warning box via the GameTab `_guard` (game_window.py:338-343). No state changes on refusal.
- **Why refuse (not no-op, not re-score-and-replace):** (i) the flat `molecule_scores` list maps onto (level, molecule) positions only under one-record-per-molecule — a replace would need keyed surgery; (ii) the house style is fail-closed refusals that name the cause (every module docstring); (iii) a silent no-op hides the lifecycle bug the Phase-3 caveat documented.
- **Consistency:** this guard is shared by Confirm and Skip (one check site, e.g. inside the engine record op — `engine.score_current` or a new `engine.record_result_checked`), so both surfaces behave identically. This ALSO fixes the Phase-3 caveat verbatim (wizard.py:550-553 says Phase 6 owns it).

---

## 3. Gaps / missing machinery (what must be built)

1. **No advance machinery is wired**: `GameState.advance_molecule/advance_level` have zero callers; wizard indexes never move; nothing rebinds slot maps or re-frames the camera on advance. (Q1)
2. **No lifecycle engine ops**: skip (detect+record+counter), give-up (counter+end state), advance-level (cleanup+materialize+state advance), and an event-producing confirm wrapper do not exist. (Q1/Q4/Q5)
3. **No end-state fields**: `game_over` / `end_state` / `final_time` absent from GameState (and therefore from `to_dict`, `game_status()`, and any endgame surface). (Q5/Q8)
4. **No per-level score aggregation**: flat `molecule_scores` + no keying; the endgame summary cannot be built robustly today. (Q2)
5. **No event marker in the poll-diff**: `_state_dict` carries no event key; `status_events` knows only 3 diff halves; the 6 reserved kinds have no builders and no pinned wording. (Q7)
6. **No stopped-timer op**: only start/rebase exist. (Q8)
7. **No camera re-frame for molecule/level advance**: gamestart compose helpers are molecule-0-hardcoded; the gamestart docstring defers this to Phase 6. (Q6)
8. **`activate_game` always re-anchors the timer** (gamestart.py:339) — unusable as-is for level advance. (Q8)
9. **No tab lifecycle buttons**: the Game tab has only Hint; the spec requires confirm / skip+give-up / restart / reset (+ Phase-7's save/import) on the tab (spec.md:39-46); the button row's stretch (game_window.py:118-125) reserved the space. SCORE-10's reset MECHANISM exists (wizard.reset_grid) but no tab button calls it.
10. **No restart handler**: `_last_start` exists (gamestart.py:178, :413-416) with zero Phase-6 consumers; the restart flow (pop → replay tuple through start_game → tab → countdown) is unwired.
11. **Stale-required-label bug on level advance**: the label refresh condition (game_window.py:323-327) keys on `molecule_id` only; `molecule_id` repeats across levels (generator.py:739-741) → the label would keep the previous level's requirement. Must extend the condition (e.g. also compare `level_pos`, or compare the `required` dict).
12. **One-record-per-molecule invariant** unenforced (re-Confirm appends — wizard.py:550-553 caveat). (Q10)
13. **Debrief/total not surfaced anywhere yet**: `result_lines` exists but nothing emits it post-advance; `total_score` has no consumer. (Q2/Q3)
14. **Endgame summary builder** (per-level + total + time + counts + message kind) absent. (Q5)

## 4. Pitfall register (PITFALLS.md items that bind here)

| Pitfall | Binding here | Evidence |
|---|---|---|
| **P6 — reset must reset the same mechanism that moved the AA** | Reset = `engine.reset_to_grid` spec REPLAY (position-only, rotations persist) — exists and is correct; the tab button MUST route through it; `cmd.matrix_reset` stays banned (placement.py:26-29 probe-proven reverter). Never "re-materialize" on Reset (rejected in Phase 3 — invalidates the pick map + color snapshots, wizard.py:592-595). | PITFALLS.md:144-165; ROADMAP:170 |
| **P9 — no undo; snapshot/replay only** | Restart = replay the `_last_start` INPUT tuple through `start_game` (full regeneration), never a state-undo; Reset = spec replay. The Phase-1 backup module stays the standing safety net for destructive ops. | PITFALLS.md:218-238; gamestart.py:136-140 |
| **P1/P4 — Qt tier discipline; modeless window; modals only as children** | All lifecycle confirmation dialogs are modal CHILDREN (legal) → the 1 Hz tick freezes the clock during them automatically (game_window.py:276-283). The main window stays modeless; ZERO modals in T1b smokes (smoke-99 law) → `_X_impl` factoring. | PITFALLS.md:23-44, 94-114; STATE.md:163 |
| **Status-surface pitfall 7 — `'result'` never fingerprinted** | The event marker design (Q7) satisfies the reserve; 'result' stays unfingerprinted. Also mind the **'score'-token collision** class in new pure text: test_wizard_text pins result-line substrings; `_molecule_scope_line` deliberately says 'counts' not 'score' (wizard_text.py:184-185) — new status_text wording must be probe-checked against the existing substring pins. | 05-RESEARCH-status-surface.md:192-193, 496-504 |
| **Contract 2 — picklable wizard** | New wizard attributes (`_event_seq`, `_last_event`) must be plain data (int/dict/None); never Qt/callables (session save pickles the whole stack). | wizard.py:17-29; 05-RESEARCH-status-surface.md anti-patterns |
| **Module identity (gate 5)** | Lazy relative imports inside methods; isinstance gates for wizard access from the tab; panel codes stay `cmd.get_wizard().method(...)`. | wizard.py:22-29; game_window.py:313-316 |
| **One-record-per-molecule** | The flat-list→(level,molecule) mapping (and the re-Confirm refusal) depend on it; enforce + test it. | Q2/Q10 |
| **Poll-diff 1 Hz latency/loss** | Two lifecycle ops within one tick lose the first event unless handlers refresh synchronously (Q7 design). | status_text.py:143-180 mechanics |
| **Stale required label on level advance** | molecule_id repeats across levels; extend the refresh condition (gap 11). | game_window.py:323-327; generator.py:739-741 |
| **Cleanup-order hazard on level advance** | cleanup_game_objects deletes the objects the LIVE wizard's maps reference; a mid-op failure leaves a cleaned scene with a live wizard (clicks no-op via the empty-pk1 path, wizard.py:289-297). Same accepted-residue class as 04-13's clean-then-refuse; document, and Restart is the recovery. | placement.py:442-455; STATE.md:171 |
| **msm ORDER LAW on any new wizard push** | Level advance pushes a NEW GameWizard → use the `activate_game` conditional-replace path (or replicate its re-evaluation), never a raw push that skips the popped-wizard cleanup interplay. | wizard.py:41-51; gamestart.py:323-339 |
| **Pins that must evolve deliberately** | SMOKE-14 exact-7-key game_status pin; EVENT_KINDS 15-key pin; panel button inventory pin (only if panel buttons change); test_wizard_text substring probes if wording overlaps. | smoke_14:206-208; test_status_text.py:308-315; test_wizard_text.py:169-189 |
| **P15 — perf/event-loop** | detect at Confirm/Skip is already molecule-scoped and inside budget (DETECT-05); no new per-frame work; the 1 Hz poll pattern is unchanged. | PITFALLS.md:365-386 |

## 5. Decision candidates (human should rule)

- **D1 — Skip partial-score semantics.** Recommend: detection-at-skip-time fraction recorded via `record_molecule_result` (02-10 sanctioned, §Q4). Confirm the reading (one line); it makes Skip and Confirm differ only by counter + event wording.
- **D2 — Event channel.** Recommend: event-marker in `_state_dict` + new status_text builders + synchronous `_refresh_status()` after tab-triggered ops (Q7). Alternative: handler-direct `_log` (the hint precedent, game_window.py:364-370) — simpler but panel-triggered ops stay silent and wording risks splitting. The marker design also satisfies "lifecycle ops MUST emit" literally.
- **D3 — Confirm advance immediacy + `_result` fate.** Spec 7.3 reads as immediate advance (score+total in the INFO BOX, then move). Consequence: the wizard panel's `_result` rendering becomes practically vestigial (the panel shows the NEXT molecule immediately) — a visible shift from the 04-15 clarification ("the wizard panel IS the Phase-4 feedback surface", STATE.md:174). Options: (a) clear `_result` on advance (recommended — debrief lives in the info box per spec), (b) keep `_result` set on the new molecule (confusing: old result under new header). Human tick needed because it changes a recorded clarification's practical effect.
- **D4 — Re-Confirm/Skip-after-record refusal wording** (Q10): proposed `'This molecule already has a recorded result (scored or skipped) -- use Restart to replay the game.'` (or shorter). Wording is pinned forever once tested — approve now.
- **D5 — Post-Give-Up wizard behavior.** Recommend: wizard stays, all gameplay handlers refuse with a visible 'The game is over.'-class error; Restart/Restart-countdown and Done remain the exits; tab lifecycle buttons gate on `game_over`. Alternatives: self-pop the wizard (Done-equivalent), or leave it fully interactive (player could keep moving AAs pointlessly).
- **D6 — Level-advance timer continuation.** Recommend: additive `activate_game(wiz, anchor_timer=True)` (default byte-identical); the lifecycle's level-advance push passes `anchor_timer=False`. Alternative: a separate push helper (duplicates the conditional-replace logic — drift risk).
- **D7 — `game_restarted` line placement vs the countdown's box clear.** Options: (a) drop the line (the countdown IS the feedback; the kind stays reserved-for-Phase-7-style unused — weak), (b) a small GameTab flag so `_begin_play` logs 'Game restarted.' right after GO and before the level line (recommended), (c) `start_countdown` gains an optional first-line parameter.
- **D8 — Endgame-summary + keyed-score home.** Recommend: additive fields + pure builders in `game_state.py` (the established scoring home; no new PURE_MODULES churn). Alternative: a new pure module (ARCHITECTURE.md:88's aspirational `scoring.py`) — more surface, same content.
- **D9 — Restart confirmation warning.** Spec requires warnings for Skip/Give Up only (spec.md:43-45). Restart discards progress silently. Recommend: follow spec (no warning) unless the human wants symmetry; note the PITFALLS UX table lists only skip/give-up (PITFALLS.md:454).
- **D10 — Final wording of the 6 reserved kinds** (status_text is the ONE wording home; EVENT_KINDS values are unpinned placeholders). Sketches from 05-RESEARCH-status-surface.md:284-289: `Molecule %s scored %.2f (total %.2f).` / `Molecule %s skipped (score %.2f).` / `Game over: gave up. Total %.2f.` / `Level %d begins.` / `Grid reset.` / `Game restarted.` Approve/adapt now — they become permanent pins.
- **D11 — Per-level aggregation mechanism** (Q2): additive keyed `score_per_molecule` dict (recommended) vs documented flat-list arithmetic under the one-record invariant.

## 6. Recommended decomposition hints for planning

Concerns cluster cleanly along the tier boundaries; each cluster is one plan-sized unit (TDD where pure):

1. **06-01 (PURE core, TDD):** GameState additions — end-state fields (`game_over`, `end_state`, `final_time`), `stop_timer(now=None)`, one-record guard support (the key-presence check is already derivable; expose a helper), optional keyed score store (D11), per-level + endgame summary pure builders (D8). Lossless to_dict/from_dict growth. WSL battery + purity registry unchanged (game_state already registered).
2. **06-02 (PURE text, TDD):** status_text event builders for the 6 kinds (final wording per D10) + `status_events` extension (fingerprint `last_event`; ordering rule event-lines-then-level-line) + confirmation-warning TEXT constants (pinnable headlessly even though the boxes are human-only). Reuses `wizard_text.result_lines` verbatim for the scored debrief (single-home law). Deliberate additive evolution of tests/test_status_text.py.
3. **06-03 (engine lifecycle ops, cmd tier):** `engine` ops — confirm-with-lifecycle (record-checked + total + advance decision), `skip_molecule`, `give_up`, `advance_level` (cleanup + materialize + GameState advance, returns the new registry), `endgame_summary()` read op. Enforces the one-record-per-molecule refusal (Q10) at the record site. Headless SMOKE: full lifecycle drive (scripted placements → confirm×m → level advance → … → endgame; skip + give-up + re-Confirm refusal paths) — the phase's mechanical E2E proof, grep-verdict style.
4. **06-04 (wizard lifecycle + gamestart generalization, cmd tier):** rework `confirm_molecule` (record → event marker → advance → rebind maps → clear selection/result), new `skip_molecule`/`give_up` wizard ops returning plain data through `_guard`, `_state_dict` additive keys (`last_event`, `game_over`, `end_state`), gamestart compose helpers generalized by `molecule_index=0` default + `activate_game(..., anchor_timer=True)` param (D6). SMOKE-07/08/14 regression + new parts.
5. **06-05 (Game tab wiring, Qt tier):** lifecycle buttons in the reserved row (Confirm, Skip/Give-Up dropdown, Restart, Reset), 04-09-style modal wrappers (`_on_skip` question → `_guard(_skip_impl)`), synchronous `_refresh_status()` after ops, the stale-required-label fix (gap 11), restart handler replaying `_last_start` through the `_start_impl`-shaped sequence (pop → start_game(activate=False) → tab → countdown) + D7 mechanics, Reset → `reset_grid` + game_reset marker, game_over gating. SMOKE-14 T1b parts (drive impls directly; ZERO modals).
6. **06-06 ([HUMAN] checkpoint):** the ROADMAP criteria 1–5 GUI verification (confirm/debrief/advance, level escalation, skip/give-up warnings + behaviors, endgame data on screen, restart/reset) + per-phase VERIFICATION.

**Wave/dependency shape:** 06-01 ∥ 06-02 (both pure, disjoint files) → 06-03 → 06-04 → 06-05 → 06-06. 06-03/06-04 touch adjacent seams (engine ops consumed by wizard ops) — sequential, or one merged plan if the planner prefers a single lifecycle plan. The endgame SCREEN plan (other researcher) consumes 06-01's summary shape + 06-05's game_over gating; coordinate the plain-data contract (`endgame_summary()` dict keys) in 06-01 so the UI plan can proceed in parallel after 06-01.

**Phase-7 inheritance notes:** GameState.to_dict growth IS the future sidecar payload (keep lossless); `_last_start` is module-level and does NOT survive a session restore — after Save/Load (Phase 7) Restart must source the tuple from the loaded sidecar, not `gamestart._last_start` (flag for the Phase-7 researcher).

## RESEARCH COMPLETE
