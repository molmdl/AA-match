---
phase: 05-game-status-tab-start-sequence
verified: 2026-09-19T17:33:49Z
status: passed
score: 88/88 must-haves verified (39 truths + 28 artifacts + 21 key links)
gaps: []
human_verification: []
human_verification_covered_by: ".planning/phases/05-game-status-tab-start-sequence/05-11-SUMMARY.md (checkpoint APPROVED, human, 2026-09-20, 9/9 steps PASS)"
requirements_covered: [SETUP-11, SCORE-04, PLAY-05]
---

# Phase 5: Game Status Tab & Start Sequence — Verification Report

**Phase Goal:** Starting a game feels like a game: the start sequence stores state and builds representations, the Game status tab takes over with live status, a 3-2-1 countdown starts play, and Hint works.
**Verified:** 2026-09-19T17:33:49Z
**Status:** PASSED
**Re-verification:** No — initial verification
**Method:** Goal-backward. All 11 plan frontmatter `must_haves` extracted, then verified against the ACTUAL code/tests/smokes (SUMMARY claims used only as pointers, never as evidence).

## Goal Achievement — Gates Re-Run Independently (all green)

| Gate | Command | Result |
|------|---------|--------|
| Syntax floor | `python3.6 -m py_compile aamatch/*.py` | OK |
| WSL suite incl. purity gates | `python3.6 -m unittest discover -s tests` | **Ran 753 tests … OK** (753/753, `tests/test_purity.py` included — purity contract NOT weakened; zero sys.modules stubs verified) |
| Deferred-activation + tab + countdown + hint | `bash smoke/run_smoke.sh smoke/smoke_11_window.py 180` | **=== SMOKE-11 PASS ===** (parts G1/G2/G3, H, I1–I5, J1–J7, K all emitted) |
| Status-surface poll-diff | `bash smoke/run_smoke.sh smoke/smoke_14_status_surface.py 180` | **=== SMOKE-14 PASS ===** (T1a accessors + parts 4.1–4.9 all emitted) |
| Default-path byte-identity (msm ORDER-LAW teeth) | `bash smoke/run_smoke.sh smoke/smoke_08_starter.py 180` | **=== SMOKE-08 PASS ===** |

## Observable Truths (goal level — ROADMAP criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Start stores the initial state, generates representations per setup, switches to the Game status tab, plays a 3-2-1 countdown, timer starts from zero (SETUP-11) | ✓ VERIFIED | [HUMAN] recorded PASS (05-11-SUMMARY.md steps 1-2, 8; human quote "1-6 pass", "8 pass", 2026-09-20) + mechanical underpinnings: deferred seam `aamatch/gamestart.py:342-345` (`activate=True` default kwarg; `:418 if activate: activate_game(wiz)`), `_last_start` 4-key deep-copied input tuple (`:178,413-415`), window-driven sequence `aamatch/setup_window.py:1020-1026` (pop → `start_game(..., activate=False)` → `tabs.setCurrentWidget(game_tab)` → `game_tab.start_countdown(wiz)`), cancellable countdown `aamatch/game_window.py:161-193` (member `QTimer` 1000 ms, n=3→2→1→GO; `cancel_pending_start` `:223-230`), timer-from-zero at GO `aamatch/gamestart.py:339` (`start_timer(time.time())`). SMOKE-11: G1 (pending NOT on stack, `top=None`), G2 (seed 31337 read BEFORE GO), H (`top=None` unactivated → scene grew=20 → GO push + float anchor), I3 (stepped `'Get ready...','3','2','1','GO!'`), I5 (cancel → no GO, `top=None`). |
| 2 | Game status tab shows a rolling info box, elapsed timer OUTSIDE the info box, required interaction types + counts (`any` or from the allowed list) (SCORE-04) | ✓ VERIFIED | [HUMAN] recorded PASS (05-11-SUMMARY.md steps 3-4, 7 adjudicated EXPECTED with the permanent two-surface string table) + mechanical: info box read-only `QTextEdit` + `_log` (`game_window.py:150`, smoke I2 `readOnly=True`), timer label rendered by `_on_tick` from the LIVE `GameState.timer_anchor` (`_compute_elapsed` `game_window.py:253-261` — `time.time() - gs.timer_anchor`, never a GUI copy), separate `_timer_label` widget outside the info box, both label modes pinned: `status_text.py:97` (`'Required: any 1 interaction'`) / `:101-102` (`'Required: %d interaction%s: %s'`, count = `len(required['items'])`, summary delegated to `wizard_text.required_summary`), pinned live by `tests/test_status_text.py:75-118` and SMOKE-14 parts 4.8 (EXCLUSIVE → `'Required: any 1 interaction'`; UNSET → `'Required: 1 interaction: h_bond x1'`), 4.2 (`'0:00'` + `'Required: -'` initial), I4 (`'1:15'` from anchor manipulation). |
| 3 | Hint recolors carbon atoms of amino acids that could form one of the required interactions — recolor only, never lines/dots/geometry (PLAY-05) | ✓ VERIFIED | [HUMAN] recorded PASS (05-11-SUMMARY.md steps 5-6: "carbon-only orange recolor, ligand/incapable untouched, idempotent, coexists with selection green, full Done restore, hint-before-selection trap clean"; hint color 'orange' CONFIRMED legible) + mechanical: capability-live candidates `aamatch/wizard.py:634-643` (`capability.hint_candidate_slots(slots, engine.ligand_profile_molecule(...), required)` — `can_form` grep in capability.py = **0**), snapshot-before-recolor into the ONE store `:664` (`wizard_core.ensure_snapshot(self._color_store, obj, ...)` before `:669 cmd.color(wizard_core.HINT_COLOR, '%s and elem C' % obj)` — object-scoped, the ligand can never recolor), restore owned by the existing cleanup store (SMOKE-11 J7: EVERY color map restored incl. hinted-never-selected objects, store cleared `store={}`), idempotent (J4), hint-over-green per-atom coexistence (J5), names unchanged (J3 `object NAMES unchanged`), GEN-04 parity live (J2 `required=('r2c1',)` ⊂ candidates). |

**Score:** 3/3 ROADMAP truths verified ([HUMAN] verdict coverage + mechanical underpinnings)

## Plan-Level Must-Haves (39 truths / 28 artifacts / 21 key links — all 11 plans)

### 05-01 — status_text pure text surface — ALL VERIFIED

| Must-have | Status | Evidence |
|-----------|--------|----------|
| required_display both modes, count = len(items), never difficulty.n_required_types | ✓ | `aamatch/status_text.py:78-105` (any `:97`, list `:101-102`, count `:100`); `tests/test_status_text.py:75-118` (any/singular/plural/count-is-len-items/empty-refused/unknown-refused/non-dict-refused) |
| status_events diff rules (first observation silent, level/selection/error-sticky lines) | ✓ | `status_text.py:143+`; tests `:181-230` (first-observation-silent, identical-silent, molecule/level/total change → ONE level line, several-fingerprints → one line, selection lines); sticky dedupe proven headless (SMOKE-14 4.7 `lines=1` after unchanged error) |
| EVENT_KINDS = 15 kinds (7 Phase-5 emitted + 8 reserved Phase-6/7) | ✓ | `status_text.py:49-75`; counted 15 — emitted: game_start, countdown, level_molecule, required_display, selection, error, hint; reserved: molecule_scored, molecule_skipped, gave_up, level_advanced, game_reset, game_restarted, game_saved, game_imported |
| Artifact `aamatch/status_text.py` (≥60 lines, imports ONLY .wizard_text) | ✓ | 180 lines; sole import `:40 from .wizard_text import required_summary`; PURE_MODULES-registered |
| Artifact `tests/test_status_text.py` (wording + diff battery) | ✓ | 341 lines; registration-pin comment `:10` ("tests/test_purity.py PURE_MODULES in this phase") |
| Artifact `tests/test_purity.py` PURE_MODULES += status_text | ✓ | `tests/test_purity.py:92-98` (`'status_text'` in the Phase-5 registration block); suite 753/753 green |
| Key link status_text → wizard_text.required_summary (single-home law) | ✓ | imported `:40`, delegated `:99,105` — never duplicated |

### 05-02 — capability hint predicates + GEN-04 — ALL VERIFIED

| Must-have | Status | Evidence |
|-----------|--------|----------|
| hint_required_types: 'any' → ALL 7 canonical types; 'list' → given order; fail-closed ValueError | ✓ | `aamatch/capability.py:317-360` (docstring pins the scoring-honest semantics; INTERACTION_TYPES from `.setup_state` `:58`); battery `tests/test_capability.py:956-995` ( resolutions + bogus-mode/empty ValueError) |
| hint_candidate_slots: capability-live (residue_capabilities ∩ required), distractors included, NEVER reads slot['can_form'] | ✓ | `capability.py:362+` built on `residue_capabilities` `:307`; `grep can_form capability.py` = **0 matches**; live distractor inclusion proven by SMOKE-11 J2 (count=6 candidates incl. role=capable slots beyond the required one) |
| GEN-04 parity invariant over real generated payloads (several seeds × modes) | ✓ | `tests/test_generator_invariants.py:750-800` (Group G; iterates MODE_CONFIGS × fresh payloads × every molecule; every role='required' slot_id asserted IN candidates); SMOKE-11 J2 live recompute agrees |
| Artifact `aamatch/capability.py` | ✓ | 800 lines; `hint_required_types` `:317`, `hint_candidate_slots` `:362` |
| Artifact `tests/test_capability.py` | ✓ | 1180 lines |
| Artifact `tests/test_generator_invariants.py` (GEN-04) | ✓ | 834 lines, Group G `:750+` |
| Key link hint_candidate_slots → residue_capabilities (ONE typing home) | ✓ | same-module call `:307` — the same predicate the generator solvability and detector consume |

### 05-03 — HINT_COLOR — ALL VERIFIED

| Must-have | Status | Evidence |
|-----------|--------|----------|
| HINT_COLOR == 'orange' in the PURE zero-imports module beside HIGHLIGHT_COLOR | ✓ | `aamatch/wizard_core.py:61` (`HINT_COLOR = 'orange'`) beside `:53` (`HIGHLIGHT_COLOR = 'green'`) |
| 'orange' is a registered named color on this PyMOL 2.5.0 build, distinct from green/element defaults | ✓ | SMOKE-11 J3 live `orange_index=13` (real Windows PyMOL color read); human CONFIRMED legible (05-11 step 5-6, "no adjustment requested"); pinned distinct `tests/test_wizard_core.py:239` (`assertNotEqual(HINT_COLOR, ...)`) |
| Artifact `aamatch/wizard_core.py` | ✓ | 200 lines, `HINT_COLOR` `:61` |
| Artifact `tests/test_wizard_core.py` exact-constants pin | ✓ | `:232-239` (== 'orange', str-typed, != HIGHLIGHT_COLOR) |
| Key link test → HINT_COLOR | ✓ | pin `:232` in the same battery style that pins NUDGE_STEP |

### 05-04 — rebase_timer pause-freeze op — ALL VERIFIED

| Must-have | Status | Evidence |
|-----------|--------|----------|
| rebase_timer(now, elapsed) re-anchors the ONE timer to float(now) - float(elapsed); no GUI-side clock copy | ✓ | `aamatch/game_state.py:193-210` (docstring pins ONE clock home, ≤1 s documented granularity); tests `tests/test_game_state.py:312-342` (anchor math 1100-42→1058 `:321`, str coercion `:332`, round-trip neutrality `:340-342`, to_dict `:358-362`) |
| Fail-closed: negative elapsed raises ValueError; float coercion both args | ✓ | `tests/test_game_state.py:344-356` (`ValueError` with 'non-negative', anchor UNTOUCHED after refusal) |
| Artifact `aamatch/game_state.py` rebase_timer beside start_timer | ✓ | `:193`; game_state stays PURE (753/753 incl. purity gates) |
| Artifact `tests/test_game_state.py` rebase battery | ✓ | 368 lines, `:312-362` |
| Key link game_window._on_tick → rebase_timer | ✓ | `aamatch/game_window.py:277-283` (modal branch calls `engine._current_game().rebase_timer(time.time(), self._last_shown_elapsed)` with EngineError guard; returns early — the poll is skipped while frozen) |

### 05-05 — deferred-activation seam — ALL VERIFIED

| Must-have | Status | Evidence |
|-----------|--------|----------|
| start_game(activate=False) prepares the FULL game and returns the GameWizard WITHOUT pushing it | ✓ | `aamatch/gamestart.py:342-345` (signature) + `:418` (`if activate: activate_game(wiz)` — activation is conditional); SMOKE-11 H: `top=None` unactivated while scene grew=20 |
| activate_game(wiz) is the ONLY GO-time activation: conditional replace re-evaluated AT activation, push, start_timer from zero | ✓ | `:323-340` (`replace = 1 if isinstance(cmd.get_wizard(), GameWizard) else 0` at `:336` — re-checked, not cached; `wiz.activate(replace=replace)`; `engine._current_game().start_timer(time.time())` `:339`); SMOKE-11 H: GO push + "timer anchored from zero" + msm ORDER-LAW "snapshot captured POST-push" |
| _last_start holds the 4-input-tuple {'setup' deep-copied, 'seed', 'candidates', 'ligand_content'} captured before mutation; NOT a v1 backup object | ✓ | `:178` module-level; `:413-415` (`copy.deepcopy(spec)`); SMOKE-11 H: EXACTLY 4 keys, deep-copied aliasing proof, real int seed, None overrides echoed |
| DEFAULT path (activate=True) byte-identical: SMOKE-08's 26 checks incl. msm ORDER-LAW teeth green unchanged | ✓ | **=== SMOKE-08 PASS ===** re-run independently (replace=1 msm ordering asserts all PASS) |
| Artifact `aamatch/gamestart.py` (activate kwarg + activate_game + _last_start) | ✓ | 424 lines; `_last_start` `:178`, `activate_game` `:323`, `start_game` `:342` |
| Artifact `smoke/smoke_11_window.py` T1a ALWAYS-tier part | ✓ | 1238 lines; part H emitted in the re-run |
| Key link activate_game → GameState.start_timer | ✓ | `:339` — ONE anchor home, set at GO |
| Key link setup_window._start_impl → start_game(activate=False) | ✓ | `aamatch/setup_window.py:1021-1025` (literal `gamestart.start_game(..., activate=False)`) |

### 05-06 — GameTab shell + two-tab window — ALL VERIFIED

| Must-have | Status | Evidence |
|-----------|--------|----------|
| Two-tab QTabWidget: 'Setup' wraps the existing form + stretch + 7-button row; 'Game status' hosts the GameTab | ✓ | `aamatch/setup_window.py:154-163` (lazy `from . import game_window` in `__init__`), `:235-239`; SMOKE-11 I1: `titles=['Setup','Game status']`, `game_tab` is the `GameTab` instance on tab 1, 7 buttons re-green (`[btn_reset, btn_randomize, btn_save_setup, btn_load_setup, btn_generate_export, btn_cleanup, btn_start]`) |
| GameTab shell: read-only rolling info box with _log, elapsed label OUTSIDE the info box ('0:00', M:SS), required label ('Required: -'), btn_hint (connected per 05-08 — the initial "not connected" state was superseded by the hint plan, smoke I2/J6 assert the connected state) | ✓ | `aamatch/game_window.py:78+` (class GameTab), `:119-126` (btn_hint), `:150` (_log); SMOKE-11 I2: `QTextEdit` read-only, `timer='0:00' required='Required: -'`; M:SS formatter `:267-270` |
| CANCELLABLE reusable member QTimer 3→2→1→GO (never a singleShot chain); every new start_countdown cancels pending first; _on_cleanup also cancels | ✓ | `game_window.py:161-176` (start_countdown: `cancel_pending_start()` FIRST, `_countdown_n=3`, `_countdown_timer.start(1000)` — a member QTimer, not a chain), `:179-193` (_countdown_tick steps → GO), `:223-230` (cancel_pending_start); SMOKE-11 I3 (armed n=3, stepped Get ready/3/2/1/GO!) + I5 (cancel → `active=False`, no GO, `top=None`) |
| 1 Hz tick reads the LIVE GameState.timer_anchor each tick (never a GUI copy); modal-open → REBASE via rebase_timer, clock freezes ≤1 s | ✓ | `game_window.py:253-261` (_compute_elapsed reads `gs.timer_anchor` live, clamps ≥0), `:285-290` (_format_mss), `:277-283` (modal branch rebases, returns early); SMOKE-11 I4: `'1:15'` rendered from anchor manipulation |
| Countdown runs with NO wizard on the stack: start_countdown stores _pending_wizard; only _begin_play calls gamestart.activate_game, then restarts the 1 Hz timer (defensive stop + start) | ✓ | `game_window.py:161-176` (_pending_wizard stored), `:195-220` (_begin_play: activate_game at `:213`, `self._timer.stop(); self._timer.start(1000)` defensive restart); SMOKE-11 G1: pending NOT on stack (`top=None`), GO pushes THAT wizard |
| Artifact `aamatch/game_window.py` (≥120 lines, module-level pymol.Qt, lazy sibling imports) | ✓ | 371 lines; `class GameTab` `:78`; lazy `from . import engine/status_text/gamestart` inside methods |
| Artifact `aamatch/setup_window.py` QTabWidget restructure | ✓ | 1038 lines; lazy game_window import `:154`, `game_tab` hosted `:162-163` |
| Artifact `tests/test_wizard_source.py` SCANNED_MODULES += 'game_window.py' | ✓ | `tests/test_wizard_source.py:53` |
| Artifact `smoke/smoke_11_window.py` T1b parts | ✓ | parts I1-I5 emitted in the re-run |
| Key link setup_window.__init__ → game_window.GameTab | ✓ | `:154` lazy import; smoke I1 asserts the instance + type |
| Key link game_window._on_tick → rebase_timer | ✓ | `:279` |
| Key link game_window._begin_play → gamestart.activate_game | ✓ | `:213` |

### 05-07 — status read accessors — ALL VERIFIED

| Must-have | Status | Evidence |
|-----------|--------|----------|
| GameWizard.get_status() public plain-data snapshot, _state_dict extended ADDITIVELY with level_pos (index+1) / level_total; no test pins the exact key set | ✓ | `aamatch/wizard.py:350-351` (`'level_pos': self._level_index + 1`, `'level_total': len(self._payload['levels'])`), `:358 def get_status`; `grep -rn _state_dict tests/` = **0**; SMOKE-14: full shape + level keys (`level_pos=1 level_total=3`), json round-trip (pickle/plain-data contract), repeated-call mutation-free |
| engine.game_status() read-only to_dict() snapshot; raises EngineError before new_game | ✓ | `aamatch/engine.py:472-478` (returns `_current_game().to_dict()` — READ only); SMOKE-14: `EngineError` raised before game, EXACT 7 to_dict keys, teardown scene EXACT |
| READ path only: no advance/skip/give-up writes; no new cmd-tier module | ✓ | `game_status()` body is 1 line (`:478`); no mutation asserted by SMOKE-14 no-mutation check; no new SCANNED_MODULES entry beyond the 05-06 game_window.py growth |
| Artifact `aamatch/wizard.py` def get_status | ✓ | `:358` |
| Artifact `aamatch/engine.py` def game_status (~4 lines additive) | ✓ | `:472-478` |
| Artifact `smoke/smoke_14_status_surface.py` (T1a accessors) | ✓ | 449 lines; T1a parts emitted in the re-run |
| Key link game_window._refresh_status → GameWizard.get_status | ✓ | `game_window.py:320` (`state = w.get_status()` behind the isinstance gate) |
| Key link wizard._state_dict → wizard_text builders unchanged (additive keys) | ✓ | 753/753 green including all pre-existing wizard_text batteries; panel still renders (SMOKE-11 J6 wizard active) |

### 05-08 — Hint vertical slice — ALL VERIFIED

| Must-have | Status | Evidence |
|-----------|--------|----------|
| CAPABILITY-LIVE hint (never slot['can_form']); DETECT-04 by construction | ✓ | `wizard.py:634-643` (_hint_impl via `capability.hint_candidate_slots` + live `engine.ligand_profile_molecule`); capability.py can_form grep = 0; SMOKE-11 J2: "cmd path == pure path (DETECT-04 live)" |
| TRAP CLOSED: EVERY candidate registered via ensure_snapshot into the ONE _color_store BEFORE its first recolor | ✓ | `wizard.py:660-666` (ensure_snapshot per candidate inside the loop, BEFORE `:669 cmd.color`); SMOKE-11 J7: "Done restores EVERY color map to materialization colors (hinted-never-selected objects too — the (a) trap closed, H-1)", store cleared `store={}` |
| Recolor = cmd.color(HINT_COLOR, '<obj> and elem C') per candidate ONLY (never alter on apply path; never unscoped elem C) | ✓ | `wizard.py:669` (literal `'%s and elem C' % obj` — object-scoped); SMOKE-11 J3: every candidate elem C reads orange index 13, "NON-candidates carry ZERO color change (ligand, distractor slots, the other molecule, the baseline scene)", "object NAMES unchanged" |
| Repeated presses IDEMPOTENT; hint-over-green per-atom coexistence | ✓ | SMOKE-11 J4 (re-press same set/colors) + J5 ("orange carbons + green non-carbons" on `_aam_aa04`) |
| Handler contract: non-modal impl + _guard + isinstance gate + lazy import; SILENT no-op pre-GO; empty-candidate case → WizardError | ✓ | `game_window.py:332-371` (_guard verbatim 04-09 contract `:332-343`; _on_hint non-modal, NO success box; _hint_now isinstance gate `:358-360`, returns None pre-GO); `wizard.py:647` (empty candidates → WizardError, fail-closed); SMOKE-11 J1 (pre-GO silent no-op, `res=None top=None`) + J6 (dict + pinned line `'Hint: 6 eligible amino acid(s) highlighted.'`) |
| Artifact `aamatch/engine.py` ligand_profile_molecule | ✓ | `:404-407` (recompute LIVE from the materialized ligand; mirrors detect_molecule scoping) |
| Artifact `aamatch/wizard.py` def hint → plain data {'count','slot_ids'} | ✓ | `:612` (returns `self._guard(self._hint_impl)`), `:671-673` (literal `{'count': len(candidate_ids), 'slot_ids': list(candidate_ids)}`) |
| Artifact `aamatch/game_window.py` _hint_now + connected btn_hint | ✓ | `:126` (btn_hint.clicked.connect(self._on_hint)), `:351` |
| Artifact `smoke/smoke_11_window.py` hint parts | ✓ | J1-J7 emitted in the re-run |
| Key link _hint_impl → capability.hint_candidate_slots | ✓ | `wizard.py:641-642` |
| Key link _hint_impl → wizard_core.ensure_snapshot + _color_store | ✓ | `wizard.py:664` |
| Key link game_window._hint_now → prior.hint() | ✓ | `game_window.py:362` (`result = prior.hint()`) |

### 05-09 — window-driven start sequence — ALL VERIFIED

| Must-have | Status | Evidence |
|-----------|--------|----------|
| Window orchestrates the deferred sequence: collect/build_state/seed-policy UNCHANGED → _pop_game_wizard() → start_game(activate=False) → tabs.setCurrentWidget(game_tab) → game_tab.start_countdown(wiz) → return wiz | ✓ | `aamatch/setup_window.py:953-1026` (docstring enumerates the 4 steps; body `:1020` pop, `:1021-1025` literal `start_game(..., activate=False)`, `:1025` `setCurrentWidget(self.game_tab)`, `:1026` `start_countdown(wiz)`, `:1027 return wiz`); seed-policy/reuse branch unchanged `:1003-1019` |
| Prior GameWizard popped by the WINDOW BEFORE start_game (isinstance-pop, NO deletion); start_game's internal conditional-replace untouched for direct callers | ✓ | `_pop_game_wizard` `:826`; pop at `:1020` BEFORE the prepare call `:1021`; SMOKE-11 G2: "the window popped the prior wizard pre-prepare (P-3); the new one is pending, not stacked"; SMOKE-08's conditional-replace teeth green (replace=1 asserts PASS) |
| _on_cleanup cancels any pending countdown FIRST | ✓ | `setup_window.py:875` (`self.game_tab.cancel_pending_start()`) BEFORE `:876 self._guard(self._cleanup_now)`; SMOKE-11 G restore: "cancel + done pop + cleanup restores the baseline scene EXACTLY" |
| SMOKE-11 PART G reworked as documented deliberate evolution (G2 pending-seed BEFORE GO, direct GO drive, cancel-before-restore) | ✓ | G1/G2/G3 all emitted in the re-run: "restart replays the exported seed 31337 in the PENDING wizard BEFORE its GO", "GO pushes the seed-31337 wizard", "setup changed → reuse branch is skipped" |
| Artifact `aamatch/setup_window.py` (_pop_game_wizard, _start_impl, _on_cleanup cancel-first) | ✓ | `:826, :953, :864-876` |
| Artifact `smoke/smoke_11_window.py` reworked PART G | ✓ | G1/G2/G3 emitted |
| Key link _start_impl → start_game(activate=False) | ✓ | `:1021-1025` literal |
| Key link _start_impl → GameTab.start_countdown | ✓ | `:1026` |
| Key link _on_cleanup → GameTab.cancel_pending_start | ✓ | `:875` |

### 05-10 — status poll-diff wiring — ALL VERIFIED

| Must-have | Status | Evidence |
|-----------|--------|----------|
| Info box = EVENT LOG, not a state mirror: tab-owned actions log directly; 1 Hz poll appends only CHANGES via pure status_text.status_events (first observation silent, level line, selection line, ERROR sticky dedupe); NO panel mirroring, no movement lines, no timestamps | ✓ | `game_window.py:291-328` (_refresh_status: pure diff owns all lines `:321-322`, baseline cleared no-wizard `:316-319`); SMOKE-14: 4.5 first poll SILENT (`lines 6 -> 6`), 4.6 scripted pick → exactly ONE 'Selected:' line + same-slot re-poll NO line, 4.7 no-selection nudge → exactly ONE 'ERROR:' + unchanged error NOT re-logged, 4.9 NO 'score' substring in ANY driven info box (Phase-6 reserve) |
| Required LABEL = reference info refreshed on molecule change, reset 'Required: -' when no wizard; never a log line; rendered by status_text.required_display | ✓ | `game_window.py:316-319` (reset branch), `:323-326` (refresh when `prev is None or molecule_id` changed); SMOKE-14 4.3 (no-wizard reset) + 4.8 (both modes live) |
| _begin_play logs the FIRST level line + sets the first required label from the PENDING wizard's get_status() right after 'GO!', seeds _last_status so the poll's first observation is silent | ✓ | `game_window.py:206-218` (literal: level line `:215`, required label `:216-217`, `self._last_status = state` `:218`); SMOKE-14 4.4 (GO logged level + rendered label + seeded baseline, `last-dict=True`) + 4.5 (first poll silent); ordering 'GO!' → level line proven by SMOKE-11 I3 ("'GO!' is followed by the level line") |
| Poll reads ONLY public accessors: cmd.get_wizard() + isinstance gate + LAZY relative import inside the method + w.get_status() — never engine privates, never callbacks on the wizard | ✓ | `game_window.py:310-313` (`from pymol import cmd; from . import status_text, wizard` INSIDE the method — module-identity law), `:314-315` (`isinstance(w, wizard.GameWizard)`), `:320 w.get_status()` |
| Artifact `aamatch/game_window.py` _refresh_status + _last_status + _begin_play content | ✓ | `:146` (_last_status init), `:291`, `:206-218` |
| Artifact `smoke/smoke_14_status_surface.py` T1b extension | ✓ | parts 4.1-4.9 emitted in the re-run |
| Key link _on_tick → _refresh_status (piggyback, no second timer; skipped while frozen) | ✓ | `game_window.py:290` (poll after the label render; modal branch returns EARLY `:283` — poll skipped while frozen, per the docstring) |
| Key link _refresh_status → status_text.status_events | ✓ | `:321` |
| Key link _refresh_status → wizard.GameWizard.get_status | ✓ | `:320` behind the gate |

### 05-11 — [HUMAN] consolidated checkpoint — ALL VERIFIED (recorded verdicts + underpinnings)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| [HUMAN] SETUP-11 start sequence (ROADMAP criterion 1) | ✓ | Recorded verdict: step 1-2 PASS + step 8 (restart feel) PASS (05-11-SUMMARY.md verdict table, human, 2026-09-20, "1-6 pass"/"8 pass"); mechanical: SMOKE-11 parts G/H/I re-run PASS |
| [HUMAN] SCORE-04 status surface (ROADMAP criterion 2) | ✓ | Recorded verdict: steps 3-4 PASS; step 7 adjudicated EXPECTED (two-surface vocabulary) — underpinnings verified: wizard panel strings at `wizard_text.py:90-92` + `:215-219` ('any interaction' / 'Required: ' + required_summary) and Qt label strings at `status_text.py:97,101`, both pinned live by SMOKE-14 4.8; timer FREEZE under modal file dialog (P-5, the not-headlessly-provable behavior) human-confirmed (step 4 note) + rebase op mechanically pinned (05-04) |
| [HUMAN] PLAY-05 hint (ROADMAP criterion 3) | ✓ | Recorded verdict: steps 5-6 PASS ("carbon-only orange recolor, legible, full restores"; 'orange' CONFIRMED legible, no adjustment); mechanical: SMOKE-11 parts J1-J7 re-run PASS |
| [HUMAN] timer pauses while any modal child is open; hint color human-confirmed | ✓ | Same recorded verdicts (step 4: "timer FREEZES under the modal file dialog"; step 5-6: color confirmed) |
| Artifact 05-11-SUMMARY.md recorded verdict table for all three criteria | ✓ | Read in full: checkpoint APPROVED (human, 2026-09-20) with 1 fix-batch item resolved in-session — verdict table rows 1-6/7/8/9, permanent two-surface string table, console-baseline record (step 9: zero AA-match tracebacks across ~14 starts) |
| Key link human operator → window-driven start sequence → Game status tab → Hint (real GUI session) | ✓ | Recorded: real Windows PyMOL 2.5.0 session, plugin-path install method, ~14 game starts driven through the window |

## Requirements Coverage

| Requirement | Status | Blocking Issue |
| ----------- | ------ | -------------- |
| SETUP-11 (start sequence: stores state, builds representations, tab switch, 3-2-1 countdown, timer from zero) | ✓ SATISFIED | None — [HUMAN] recorded PASS + SMOKE-11 G/H/I mechanically re-run PASS |
| SCORE-04 (rolling info box, elapsed timer outside the info box, required types + counts) | ✓ SATISFIED | None — [HUMAN] recorded PASS + SMOKE-14 4.1-4.9 + pinned label strings |
| PLAY-05 (Hint recolors carbon atoms of capable amino acids — recolor only) | ✓ SATISFIED | None — [HUMAN] recorded PASS + SMOKE-11 J1-J7 + GEN-04 invariant |

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| aamatch/setup_window.py | 288, 333, 676 | 'placeholder' substring | ℹ️ Info | NOT a stub — Phase-4 prose about the upload list's placeholder item behavior (pre-existing Phase-4 domain vocabulary); no Phase-5 artifact affected |
| (all 10 key aamatch files scanned) | — | TODO/FIXME/XXX/HACK | — | **0 hits** — zero markers across status_text, capability, game_window, setup_window, wizard, engine, game_state, gamestart, wizard_core, generator |
| (all key aamatch files) | — | console.log / empty returns / stub handlers | — | **0 hits** — no stub handlers (`_on_hint` drives the full dispatch; no `() => {}` shapes) |

## Human Verification Required

**None outstanding.** All [HUMAN] criteria were human-verified 2026-09-20 in the consolidated 05-11 GUI checkpoint (real Windows PyMOL 2.5.0 session, 9/9 steps PASS, APPROVED; verdicts recorded in 05-11-SUMMARY.md and treated as satisfied evidence per the phase protocol — no re-verification demanded). The one in-session fix-batch item (block-exclusive refusal message clarity) was verified: commit `b749135 fix(05-11): clarify block-exclusive refusal message` confirmed in git history and its literal message confirmed in `aamatch/generator.py:398-410` (states the every-molecule requirement, names the offending types, gives the remedy), with the full re-green (753/753 + 3 smokes) independently re-run by this verifier.

Behaviors covered by recorded human verdicts (and NOT re-demandable headlessly): countdown cadence feel, modal timer-freeze legibility (P-5), hint recolor legibility, restart feel, console baseline cleanliness (step 9).

## Gaps Summary

**No gaps.** All 39 truths, 28 artifacts, and 21 key links verified at all three levels (existence, substance, wiring). Notable verification depth:

- **Level 3 (wired) — the 80% stub-hiding zone — was verified literally, not by smoke inference:** every named cross-module call site was located (e.g. `setup_window.py:1021-1025` literal `start_game(..., activate=False)`; `game_window.py:213` `activate_game` in `_begin_play`; `:279` `rebase_timer` in the modal branch; `:321` `status_events` in the poll; `wizard.py:641,664,669` the hint pipeline; `:875` cancel-first in `_on_cleanup`).
- **Purity contract intact:** `status_text` registered in PURE_MODULES (`tests/test_purity.py:92-98`), imports only `.wizard_text` (`status_text.py:40`); zero sys.modules stubs; suite 753/753 green.
- **The 05-11 step-7 adjudication is mechanically sound:** the human's quoted strings match `wizard_text.py` (wizard panel vocabulary) character-for-character while the Qt tab label strings live at `status_text.py:97,101` — both surfaces pinned live-green (tests + SMOKE-14 4.8), matching the recorded two-surface table.
- **The fix-batch item (b749135) verified in code and history** with zero stale verbatim pins (`tests/` pins substrings that all survive).

---

_Verified: 2026-09-19T17:33:49Z_
_Verifier: OpenCode (gsd-verifier)_
