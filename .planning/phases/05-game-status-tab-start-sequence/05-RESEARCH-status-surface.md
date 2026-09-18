# Phase 5: Game Status Tab & Start Sequence — Status-Surface Research (Researcher B)

**Researched:** 2026-09-18
**Domain:** SCORE-04 status surface — the rolling info box, the required-interactions
display, and the live game-state access path between the Qt Game status tab and the
running GameWizard/engine.
**Confidence:** HIGH — every load-bearing claim is verified against this repo's sources
(file:line), the PyMOL 2.5.0 source tree, or the shipped prior art. Two NEW accessors are
proposals (clearly marked), not existing APIs.

**Scope boundary (sibling alignment):**
- Researcher A (`05-RESEARCH-window-start-timer.md`) owns the TAB STRUCTURE
  (QTabWidget restructure), the NEW `aamatch/game_window.py` module (`GameTab`), the
  start sequence (deferred activation: `start_game(activate=False)` +
  `gamestart.activate_game(wiz)` at GO), the countdown (cancellable member QTimer), and
  the 1 Hz elapsed timer. A's countdown ALREADY appends `Get ready...` / `3` / `2` / `1` /
  `GO!` through a shared `_log`; A's OQ-7 hands the info-box CONTENT POLICY to me.
- Researcher C (`05-RESEARCH-hint.md`) owns the Hint button: `GameWizard.hint()` in
  `aamatch/wizard.py` returning plain data `{'count': n, 'slot_ids': [...]}`, a
  non-modal handler with an isinstance gate and silent no-op pre-GO. C's OQ-3 hands the
  info-box hint LINE to me.
- I own: what the info box shows and when, the required-interactions label, and the
  read path the tab uses to see live game state.

---

## Summary

Phase 5's status surface is three widgets plus one read path: a read-only rolling
QTextEdit (the info box), a QLabel for the required interactions, and a per-tick
state poll. The prior art proves the widget shapes verbatim (read-only `QTextEdit`
+ `.append()` log, `QLabel` reference row, 1 Hz `QTimer`), but its *sync mechanism*
(callbacks registered onto a controller object) does NOT transfer: AA-match's
GameWizard must stay pickle-safe (contract 2 — PyMOL session save pickles the whole
wizard stack, [SRC wizarding.py:175-180]), so the wizard can never hold Qt-bound
callables. The correct AA-match mechanism is **1 Hz polling piggybacked on A's timer**:
the tick reads the live wizard's plain-data status dict, a NEW pure module
(`aamatch/status_text.py`) diffs the previous snapshot against the current one and
returns the log lines, and tab-owned actions (start/countdown/hint) log directly
with no wizard round-trip. I verified PyMOL exposes NO observable wizard-refresh
hook ([SRC wizarding.py:130-142] — `refresh_wizard` is an internal C dispatch with no
callback registration; the Wizard base `do_*` methods are C→wizard callbacks, not
observer slots), so polling is the realistic option, matching how the prior art
pulled label state at render time.

The required-interactions display is a per-molecule QLabel fed by a new pure builder
that REUSES `wizard_text.required_summary` as the single items renderer. The
authoritative "number" is `len(required['items'])` in list mode (the divisor
`game_state.score` and `result_lines` both use) and **1** in 'any' mode (binary
scoring: any single allowed-type record completes the molecule);
`difficulty.n_required_types` is the unset-draw CAP, never the display source
([SRC generator.py:396, 409-410, 431-435]).

The read path needs exactly two tiny additive accessors: `GameWizard.get_status()`
(public plain-data snapshot; `_state_dict()` extended with `level_pos`/`level_total`)
and `engine.game_status()` (read-only `GameState.to_dict()` snapshot for the running
scores/counters the wizard does not hold). Phase 5 exposes the READ path only; the
info box reserves the Phase-6/7 event kinds (score lines, skip/give-up, save/import)
so later phases append without redesigning the format.

**Primary recommendation:** poll-diff architecture — `_refresh_status()` on A's 1 Hz
tick → `cmd.get_wizard()` + lazy relative isinstance gate → `wizard.get_status()` →
pure `status_text.status_events(prev, curr)` → `_log()` appends; tab-owned events log
directly; required label re-rendered from `status_text.required_display()` whenever
the molecule changes. No wizard→Qt coupling, no new cmd-tier module, zero picklability
risk.

---

## standard_stack

No new dependencies (pymol.Qt/PyQt5 + numpy + stdlib only, per AGENTS.md). The stack
is the existing Phase-4 Qt tier plus one new pure module.

### Core (what Phase 5 uses)

| Item | Version/home | Purpose | Why standard |
|---|---|---|---|
| `QtWidgets.QTextEdit` (read-only) | pymol.Qt (PyQt5 5.12.3 / Qt 5.12.9, baseline 01-07) | the generic rolling info box | [PA-OBS] prior art `PA-gui_game:24-27` — `QTextEdit()` + `setReadOnly(True)` + tooltip; append via `_log` |
| `QTextEdit.append(str)` | Qt | log-line append (auto-scrolls) | [PA-OBS] `PA-gui_game:119-120` — `self._info_log.append(str(msg))`; no timestamps, no pruning |
| `QtWidgets.QLabel` | pymol.Qt | required-interactions reference label (outside the info box) | [PA-OBS] `PA-gui_game:31` `Remaining: -` label row — reference info lives in a label, not the log |
| `QtCore.QTimer` (1 Hz) | pymol.Qt | the tick that renders elapsed (A) AND the status diff (mine) | [PA-OBS] `PA-gui_game:108-111` + [PA-OBS] A's Pattern 3; PITFALL 1/15 (never `threading.Thread` + cmd) |
| `cmd.get_wizard()` | pymol.cmd | the live wizard instance read | [SRC wizarding.py:156-160]; None-safe isinstance gate precedent `aamatch/setup_window.py:797-799` |
| `wizard_text.required_summary(required)` | aamatch/wizard_text.py (PURE) | THE single items renderer, reused by the tab's required display | single-home law; pinned shapes [SRC wizard_text.py:77-103, tests/test_wizard_text.py:85-102] |

### New (proposed, this phase)

| Item | Tier | Purpose |
|---|---|---|
| `aamatch/status_text.py` (NEW PURE) | PURE (stdlib-free text builders) | `required_display(required)`, `status_events(prev, curr)`, `level_molecule_line(...)`, `selected_line(selected)`, `error_line(msg)`, `EVENT_KINDS` vocabulary |
| `GameWizard.get_status()` + `_state_dict()` level keys | cmd (aamatch/wizard.py) | public plain-data snapshot the Qt tab reads |
| `engine.game_status()` | cmd (aamatch/engine.py) | read-only `GameState.to_dict()` snapshot (scores/counters/anchor) — Phase 6 inherits it |

### Alternatives considered

| Instead of | Could use | Tradeoff |
|---|---|---|
| 1 Hz poll-diff | push callbacks onto the wizard (prior-art `set_callbacks`, [PA-OBS] `PA-game:94-111`) | REJECTED: every GameWizard attribute must be plain picklable data (contract 2, `aamatch/wizard.py:17-29`); a Qt-bound callable on self breaks session save ([SRC wizard/__init__.py:23-26] `__getstate__` pops only `cmd`; [SRC wizarding.py:175-180] the WHOLE stack is pickled). v1 got away with it only because it saved the target OBJECT, never a full session ([PA-OBS] `PA-__init__:776` `cmd.save(pse_path, self._controller.target_obj)`) |
| 1 Hz poll-diff | new cmd-tier event-bus module called from wizard methods | REJECTED for Phase 5: a new cmd-tier module (SCANNED_MODULES growth) + a coupling surface for zero Phase-5 benefit — every Phase-5 event is either tab-owned or state-visible. Keep as the documented fallback if the human later wants sub-second event fidelity |
| New pure `status_text.py` | extend `wizard_text.py` | wizard_text's module contract is "panel/prompt/result text builders" (the wizard's overlay); tab text is a different surface. A per-surface pure module is the established pattern (`setup_form.py` = the setup-window's pure glue, 04-02). Also keeps wizard_text's pinned docstring surface untouched (PROSE_PIN hygiene) |
| `QPlainTextEdit` | prior-art `QTextEdit` | QPlainTextEdit is lighter for huge logs, but prior art shipped `QTextEdit` + append with no pruning and a game session generates only dozens of lines — borrow the proven shape verbatim |

---

## architecture_patterns

### Data-flow diagram (the recommended access path)

```
[GO!] gamestart.activate_game(wiz)            (cmd tier — A's; pushes wizard + sets
        |                                      GameState.timer_anchor)
        v
GameWizard live at cmd.get_wizard(); GameState holds scores/counters/anchor
        |
        | every 1 Hz tick (game_window.GameTab._on_tick — A's timer)
        v
GameTab._refresh_status()                      (Qt tier — MINE)
        |
        |-- from . import wizard               (lazy relative import INSIDE the
        |                                       method — module-identity law,
        |                                       wizard.py:23-29 contract 2;
        |                                       setup_window.py:797-799 precedent)
        |-- w = cmd.get_wizard()
        |-- isinstance(w, wizard.GameWizard)?
        |      no  -> required label -> 'Required: -'; self._last_status = None; return
        |      yes -> state = w.get_status()           (plain-data dict, level keys incl.)
        |             lines = status_text.status_events(self._last_status, state)
        |             for line in lines: self._log(line)
        |             if molecule changed: self._required_label.setText(
        |                    status_text.required_display(state['required']))
        |             self._last_status = state
        v
self._info_log.append(line)                    (prior-art _log, PA-gui_game:119-120)

Tab-owned events (NO wizard round-trip — direct _log):
  start sequence (A): _info_log.clear() + 'Get ready...'/'3'/'2'/'1'/'GO!'
  begin_play:         'Level %d, molecule %d of %d.' from the PENDING wizard's
                      get_status() + set the required label   (instant, ordered)
  hint handler (C):   prior.hint() -> 'Hint: %d eligible amino acid(s) highlighted.'
```

### Pattern 1 — the info box is an event log; the tab logs its own actions directly

**What:** `_log(line)` is a thin `self._info_log.append(str(line))` wrapper. Anything
the TAB does (Start sequence, Hint press) logs synchronously at the handler — no state
polling, no wizard coupling.
**When to use:** every user-initiated, tab-visible action.
**Evidence:** [PA-OBS] `PA-gui_game:119-120` (`_log`), `PA-gui_game:250-263` (clear +
`Get ready...` + 3/2/1/`GO!` logged in the box), `PA-__init__:942-945` (cleanup resets
log + labels). C's handler sketch already contains the log call
(`05-RESEARCH-hint.md` `_hint_now`).

```python
# aamatch/game_window.py (shape only — A owns the module)
def _log(self, line):
    self._info_log.append(str(line))     # [PA-OBS] PA-gui_game:119-120 verbatim

def _begin_play(self):
    from . import gamestart
    gamestart.activate_game(self._pending_wizard)   # cmd tier (A's)
    state = self._pending_wizard.get_status()        # plain data; safe pre/post-activate
    self._log(status_text.level_molecule_line(state))
    self._required_label.setText(
        status_text.required_display(state['required']))
    self._last_status = state
    self._pending_wizard = None
    self._timer.stop()          # defensive (prior-art shape, PA-gui_game:285)
    self._timer.start(1000)
```

### Pattern 2 — the poll-diff: pure `status_events(prev, curr)` returns the lines

**What:** the tick's status half calls ONE pure function with the previous and current
plain-data state dicts; it returns the list of lines to append (empty = silent). The
Qt tier never interprets state; the pure tier owns all wording and event semantics.
**When to use:** every tick after GO. **TDD: this is the phase's highest-value pure
battery** (all wording becomes pinned regression teeth).
**First observation is SILENT** (`prev=None` → `[]`): the start sequence already logged
the level line; the poll only reports CHANGES.

```python
# aamatch/status_text.py (NEW PURE — full signature contract)
def status_events(prev, curr):
    """Diff two get_status() plain-data dicts; return log lines (list of str).

    prev None -> [] (initialization is silent; the start sequence logs first).
    Emits, in order:
      - molecule/level change: level_molecule_line(curr)
      - selection change:      selected_line(curr['selected'])
      - new error:             error_line(curr['error'])
    Fingerprint keys: molecule_id, molecule_pos, molecule_total, level_pos,
    selected['slot_id'], error. 'result' is deliberately NOT fingerprinted in
    Phase 5 (score lines are reserved for Phase 6 — see the event inventory).
    Sticky-state dedupe: an UNCHANGED error string is never re-logged; a
    cleared error (X -> None) logs nothing.
    """
```

```python
# aamatch/game_window.py (shape only — the tick's status half; A owns _on_tick)
def _refresh_status(self):
    from . import status_text, wizard
    w = cmd.get_wizard()
    if not isinstance(w, wizard.GameWizard):
        self._required_label.setText('Required: -')
        self._last_status = None
        return
    state = w.get_status()
    for line in status_text.status_events(self._last_status, state):
        self._log(line)
    prev = self._last_status
    if prev is None or prev.get('molecule_id') != state.get('molecule_id'):
        self._required_label.setText(
            status_text.required_display(state['required']))
    self._last_status = state
```

The isinstance gate with a lazy relative import INSIDE the method is the established
module-identity pattern verbatim (`aamatch/setup_window.py:797-799`: `from . import
placement, wizard` → `isinstance(prior, wizard.GameWizard)`) — safe under both
`aamatch` and `pmg_tk.startup.aamatch` identities (AGENTS.md gate 5).

### Pattern 3 — required display = a reference LABEL, refreshed on molecule change

**What:** the required interactions are persistent reference info, NOT an event —
a QLabel next to the timer row (prior-art row shape, `PA-gui_game:39-43`), re-rendered
whenever the molecule changes (and reset to `Required: -` when no game wizard is live).
**Why a label, not a log line:** spec.md:40 lists it as tab content alongside the info
box and the timer, not inside the rolling log; a stale molecule's requirement must
never scroll away mid-molecule.

### Pattern 4 — read-only engine snapshot for the score/counter state

**What:** `engine.game_status()` returns the live GameState's `to_dict()` (already
lossless and plain, `aamatch/game_state.py:217-229`) — the READ path for running
scores, skip/give-up counters, and the timer anchor. Raises `EngineError` before
`new_game` (the `_current_game()` guard, `aamatch/engine.py:98-103`).
**Phase 5 uses it minimally** (the info box shows no scores until Phase 6); landing it
now gives Phase 6 a green read path. The write side (timer anchor at GO) is already
A's `activate_game` (`engine._current_game().start_timer(...)`).

```python
# aamatch/engine.py (NEW, additive — 4 lines)
def game_status():
    """Read-only plain-data snapshot of the live GameState (no mutation).

    Returns GameState.to_dict(): current_level_index, current_molecule_index,
    molecule_scores, skip_count, giveup_count, timer_anchor,
    formed_types_per_molecule. Raises EngineError when no game is live."""
    return _current_game().to_dict()
```

### Anti-patterns to avoid

- **Storing Qt objects/callables on the GameWizard** — contract 2 (`wizard.py:17-29`):
  session save pickles the whole stack ([SRC wizarding.py:175-180]); a bound method of
  the dialog breaks `cmd.save()` (TypeError) and restore would silently print
  "Session-Warning: unable to restore wizard." ([SRC wizarding.py:187-191]). The tab
  polls; it never registers itself on the wizard.
- **Mirroring wizard-panel text into the info box** (A's OQ-7 + mine): the panel is the
  Phase-3/4 imperative feedback surface (04-15 clarification); the info box is the
  event narrative. Duplication is noise and doubles the pinned-string maintenance.
- **Logging movement/nudge presses** — they are not in `_state_dict()` (would need a
  new publish channel = tier change) and would flood the log; the panel already echoes
  every press. The info box logs milestones.
- **Timestamping each log line** — prior art ships none ([PA-OBS]
  `PA-gui_game:119-120`); the timer label carries time. Keep lines short (see OQ-1).
- **Polling `engine._game` / reaching `engine._payload` directly from the Qt tier** —
  private module state; use the new public accessors (`get_status`,
  `engine.game_status`).

### The event inventory (Q2 — the planner's primary table)

| Event | Text format (pinned) | Source (who emits) | Channel |
|---|---|---|---|
| game_start | `Get ready...` | A's `start_countdown` | direct `_log` |
| countdown | `3`, `2`, `1`, `GO!` (one per second) | A's countdown tick | direct `_log` |
| level/molecule status | `Level %d, molecule %d of %d.` (e.g. `Level 1, molecule 1 of 2.`) | tab `_begin_play` at GO (from the pending wizard's `get_status()`); poll re-emits on molecule/level change | direct `_log` / poll diff |
| required display | QLabel, NOT a log line: `Required: any 1 interaction` (any mode) or `Required: %d interaction(s): <required_summary>` (list mode) — see Q4 | tab `_begin_play` + poll on molecule change | `setText` from pure builder |
| selection | `Selected: slot %s (%s).` (the panel's first prompt line minus its imperative tail, [SRC wizard_text.py:268-273]) | poll diff on `selected.slot_id` change | poll diff → `_log` |
| error | `ERROR: %s` (same prefix as panel/prompt, [SRC wizard_text.py:228,264]) | poll diff on `error` change (new string only) | poll diff → `_log` |
| hint used | `Hint: %d eligible amino acid(s) highlighted.` (%d = `hint()`'s `count`; text = C's sketch, adopted verbatim) | C's `_hint_now` handler after a successful `prior.hint()` | direct `_log` (handler-owned) |
| game over (informal) | RESERVED — not emitted in Phase 5 (Done is the panel's exit; a restart also transits `start_countdown` which clears the log — a `Game closed.` line would double-fire on restarts) | — | — |
| **RESERVED molecule_scored (P6, SCORE-01/02)** | sketch: `Molecule %s scored %.2f (total %.2f).` + `result_lines(...)` verbatim (spec.md:52 7.3: molecule score + total in the info box) | Phase 6 confirm/advance flow | direct `_log` or poll (planner decides) |
| **RESERVED molecule_skipped (P6, SCORE-05)** | sketch: `Molecule %s skipped (score %.2f).` | Phase 6 skip handler | direct `_log` |
| **RESERVED gave_up (P6, SCORE-06)** | sketch: `Game over: gave up. Total %.2f.` | Phase 6 give-up handler | direct `_log` |
| **RESERVED level_advanced (P6, SCORE-03)** | sketch: `Level %d begins.` | Phase 6 advance flow | poll or direct |
| **RESERVED game_reset (P6, SCORE-10)** | sketch: `Grid reset.` | Phase 6 Reset button handler | direct `_log` |
| **RESERVED game_restarted (P6, SCORE-09)** | sketch: `Game restarted.` (then the normal start lines) | Phase 6 Restart handler | direct `_log` |
| **RESERVED game_saved (P7, SCORE-08)** | sketch: `Game saved to %s.` | Phase 7 save handler | direct `_log` |
| **RESERVED game_imported (P7, PERSIST-02)** | sketch: `Game imported: %s.` | Phase 7 import handler | direct `_log` |

Reserved kinds live in `status_text.EVENT_KINDS` (a documented vocabulary constant) so
Phase 6/7 append lines without redesigning the format; only the Phase-5 rows are
emitted by `status_events`. The `_guard` split is explicit: **setup-window errors**
(SETUP form refusals) surface ONLY in the QMessageBox ([SRC
`aamatch/setup_window.py:594-607`], 04-09 contract — they are pre-game, a different
surface); **wizard errors** (movement/refusal WizardErrors) land in `wizard._error`
([SRC `aamatch/wizard.py:423-433`]) and are LOGGED by the poll as history while the
panel still shows the live one.

### Q4 — the required-interactions display contract (pinned strings)

**What exists today:** `wizard_text.required_summary(required)` renders
`'any interaction'` for mode 'any' and `'<type> x<count>'` comma-joined in GIVEN order
for mode 'list' ([SRC wizard_text.py:77-103]; pinned in tests/test_wizard_text.py:85-102).
The wizard panel prefixes it: `Required: h_bond x1, pi_stacking x2`
([SRC wizard_text.py:217-219]).

**Which number is authoritative (verified):**
- mode 'list': **`len(required['items'])`** — `game_state.score` divides formed by
  `len(items)` ([SRC game_state.py:81-82]) and `result_lines` renders `N/M` with
  `M = len(items)` ([SRC wizard_text.py:146-148]).
- mode 'any': **1** — scoring is binary (≥1 record of any type → 1.0,
  [SRC game_state.py:74-75]); one interaction completes the molecule.
- `difficulty.n_required_types` is NOT the display source: it caps the unset draw
  (`k = min(n_required_types, len(pool))`, [SRC generator.py:431]); block_exclusive
  ignores it entirely (items = the whole allowed list, [SRC generator.py:409-410]);
  exclusive returns `items: []` ([SRC generator.py:396]). The payload's `required`
  dict ([SRC level_spec.py:25-26]) is the single truth the display reads.

**Pinned display strings (new pure builder `status_text.required_display`):**
- mode 'any' → `Required: any 1 interaction`
- mode 'list' → `Required: %d interaction%s: %s` where %d = `len(items)`, the plural
  suffix is `''` for 1 else `'s'`, and `%s` = `wizard_text.required_summary(required)`
  reused verbatim (single items renderer; e.g. `Required: 2 interactions: h_bond x1,
  pi_stacking x2`)
- fail-closed identical to `required_summary`: list mode with empty items and unknown
  modes raise ValueError naming the cause (delegated by the reuse).
- no-game state → `Required: -` (prior-art `Remaining: -` shape, [PA-OBS]
  `PA-gui_game:31`).

Type names are the canonical INTERACTION_TYPES tokens ([SRC setup_state.py:40-42]) —
the same tokens the panel, the result lines, and the setup checkboxes' values use,
so one vocabulary spans all game surfaces. The pretty-label map
(`_INTERACTION_LABELS`, [SRC setup_window.py:315-323]) stays a FORM-only teaching
surface: a pure builder cannot import the Qt tier, and moving the map to a pure home
is churn in a human-verified module (see OQ-2 for the alternative).

**Where the helper lives (Q7 overlap):** NEW pure module `aamatch/status_text.py`
(not wizard_text — different surface, clean TDD home, `setup_form.py` per-surface
precedent), importing `.wizard_text` for the reuse. TDD candidate: YES (WSL battery).

### Q5 — update triggers (verified)

- **Is there an observable `cmd.refresh_wizard()` hook? NO.** `refresh_wizard` is an
  internal command dispatching straight into C (`_cmd.refresh_wizard`,
  [SRC wizarding.py:130-142]); the C layer re-calls `wizard->get_panel()/get_prompt()`
  directly. The Wizard base's `do_scene/do_view/do_dirty/...` methods are C→wizard
  callbacks on the wizard ITSELF ([SRC wizard/__init__.py:44-64]) — an external Qt
  widget cannot subscribe. No hook API exists anywhere in the Python modules.
- **Explicit handler/wizard→Qt calls? NO** — `wizard.py` is cmd-tier, Qt-free by law
  (`aamatch/wizard.py:1-7`); prior art's wizard never touched Qt either ([PA-OBS]
  `PA-wizard.py` — zero Qt imports; its coupling was DI callables on the controller,
  a pattern AA-match cannot copy onto the wizard because of the pickle contract).
- **1 Hz poll piggybacked on A's timer: RECOMMENDED.** It covers every Phase-5 event
  (selection, errors, molecule/level changes are all in `get_status()`), costs a
  dict-diff per second, is robust to missed refreshes, and matches the prior art's
  pull-at-render precedent for labels ([PA-OBS] `PA-gui_game:122-130`
  `_update_remaining` reads the controller at render time). Latency ≤1 s is
  appropriate for an event log; the panel remains the instant surface.

### Q6 — score/total state (verified flow)

- The authoritative running score lives in `engine._game` (the module-level
  `GameState`, [SRC engine.py:92-95]): `record_molecule_result` appends the score and
  stores the formed types together ([SRC game_state.py:202-215]);
  `total_score` is the sum property ([SRC game_state.py:182-185]).
- Flow today: `wizard.confirm_molecule` → `_guard(_confirm_molecule_impl)` →
  `engine.confirm(level, molecule, required)` → `detect_molecule` + `score_current` →
  `game.record_molecule_result` ([SRC engine.py:395-421], [SRC wizard.py:528-568]).
  The wizard holds only the LAST result in `_result` — it does NOT hold history.
- The wizard's `_state_dict()` ([SRC wizard.py:333-349]) carries molecule_id/pos/total,
  required, selected, result, error — but NOT the level and NOT scores. Consistent
  snapshot for the tab therefore needs:
  1. `_state_dict()` extended additively with `level_pos` (`_level_index + 1`) and
     `level_total` (`len(_payload['levels'])`) — plain data; the pure builders use
     `.get` and ignore unknown keys (verified: `panel_entries`/`prompt_lines` read
     only their keys, [SRC wizard_text.py:209-265]); no test pins the dict's exact
     key set (grep: zero `_state_dict` references in tests/). NEW public
     `GameWizard.get_status()` returns it (the tab never reaches `_state_dict`
     across modules).
  2. `engine.game_status()` (Pattern 4) for scores/counters/anchor.
- Phase-5 posture: READ path only — no advance/skip/give-up writes; Phase 6 owns the
  scoring lifecycle (SCORE-01..03) and will consume the same accessors.

### Q9 — no-helper-visuals + the complement split (verified)

- **No-helper-visuals: trivially safe.** The design adds zero scene geometry: the
  info box is a Qt text widget, the required display a QLabel; `status_events` and
  `required_display` are pure string functions; the poll's only cmd call is the read
  `cmd.get_wizard()`. No lines/dots/CGO/`cmd.indicate` anywhere — the
  `tests/test_wizard_source.py` visual gate is unaffected (and if the tab is a NEW
  module it JOINS the scanned set — see Gate impact).
- **Complement split (recommendation, human-adjustable):**
  - **Wizard panel = imperative instruction** (what to do NOW): click instruction /
    `Selected: slot ... Move/rotate it, then Confirm.` + result lines + `ERROR:` line
    ([SRC wizard_text.py:240-273]) — UNCHANGED Phase-3 contract.
  - **Info box = event log** (what HAPPENED, in order): start/countdown/level/
    selection/error/hint lines — no instruction text, no live state restated.
  - **Required label = reference info** (persistent): the molecule's requirement,
    always visible, never scrolled away.
  - A's OQ-7 recommends the same NO-mirroring stance; the 04-15 clarification (wizard
    panel is the Phase-4 feedback surface; the Qt tab is ADDITIONAL) is honored by
    construction — the info box does not replace or restate the panel.

---

## dont_hand_roll

| Problem | Don't build | Use instead | Why |
|---|---|---|---|
| Rolling log widget | custom scroll/append machinery, pruning logic, rich-text handling | `QTextEdit.setReadOnly(True)` + `.append()` | [PA-OBS] `PA-gui_game:24-27,119-120` — shipped, auto-scrolls, no pruning needed at game-session scale |
| Event wording/formatting | ad-hoc strings at call sites in the Qt tier | pure `status_text` builders + `EVENT_KINDS` | wording becomes WSL-pinned regression teeth; the Qt tier stays a dumb renderer |
| State diffing | Qt-side nested ifs per widget | `status_text.status_events(prev, curr)` | one pure function owns the event semantics; unit-testable without PyMOL/Qt |
| Required-set rendering | a second items renderer in the tab | reuse `wizard_text.required_summary` | single-home law — two renderers WILL drift |
| Live-state reads | reaching `engine._game`/`_payload`/wizard privates from Qt | `GameWizard.get_status()` + `engine.game_status()` | public, additive, pickle-safe, module-identity-safe |
| Score totals | recomputing from payload + records | `GameState.total_score` via `engine.game_status()` | Phase-2-verified accumulation ([SRC game_state.py:182-185]) |
| Timer anchor/pause | a second GUI-side clock copy | `GameState.timer_anchor` (A's design; prior art's dual-anchor produced a real bug, [PA-OBS] `PA-gui_game:279-284`) | one anchor home, Phase-7-persistable |

**Key insight:** everything user-visible in the status surface is either (a) already
plain data on the wizard/GameState, or (b) an action the tab itself performed. Both
are readable WITHOUT new coupling — resist any design that threads callables, Qt
references, or new publish channels through the cmd tier.

---

## common_pitfalls

### Pitfall 1: Qt-bound callbacks on the GameWizard break session save
**What goes wrong:** registering the tab (or any bound method) as a wizard callback
(TotalCmd the prior-art `set_callbacks` shape) puts an unpicklable object on the
wizard stack; `cmd.save()` of a full session raises TypeError, and restore prints
"Session-Warning: unable to restore wizard."
**Why it happens:** PyMOL pickles the ENTIRE wizard stack on session save
([SRC wizarding.py:175-180]); `Wizard.__getstate__` strips only `self.cmd`
([SRC wizard/__init__.py:23-26]). Prior art avoided this by saving a single OBJECT
([PA-OBS] `PA-__init__:776`), not the session.
**How to avoid:** poll from the tab; the tab holds NO reference the wizard holds back.
The tab may keep `self._last_status` (a plain dict) freely — the DIALOG is never
pickled.
**Warning signs:** any `def` on GameWizard taking a widget/callback parameter; any
`self._something = <callable>` in wizard.py.

### Pitfall 2: module-identity in the isinstance gate
**What goes wrong:** a module-level `from .wizard import GameWizard` in the Qt tier
(or an absolute `aamatch.wizard` import) creates a SECOND module object under the
installed identity (`pmg_tk.startup.aamatch`) and `isinstance` silently fails → the
tab thinks no game is running.
**How to avoid:** lazy relative import INSIDE the method (`from . import wizard`) —
the established pattern ([SRC `aamatch/setup_window.py:797-799`], wizard.py:23-29
contract 2). Never mix `aamatch` and `pmg_tk.startup.aamatch` in one session
(AGENTS.md gate 5).
**Warning signs:** `isinstance` returning False right after a successful start;
duplicate-singleton symptoms.

### Pitfall 3: sticky error/result re-logging (poll dedupe)
**What goes wrong:** `wizard._error` persists until a later successful pick/confirm
clears it ([SRC wizard.py:298, 423-433, 567]) — a naive per-tick "if error: log"
re-logs the same error every second.
**How to avoid:** fingerprint the error STRING in `status_events`; log only on
CHANGE (None→X or X→Y where Y≠X); cleared (→None) logs nothing. Same rule guards the
selection (re-clicking the same slot must not re-log).
**Warning signs:** a log filling with repeated `ERROR: Select an amino acid first.`
lines.

### Pitfall 4: first-observation double-logging after GO
**What goes wrong:** if the poll logs on `prev=None`, the level/molecule line appears
twice (once from `_begin_play`, once from the first tick) — or the start sequence and
the poll race on the required label.
**How to avoid:** the START SEQUENCE owns the first level line + the first required
label (direct, instant, ordered right after `GO!`); `status_events(None, curr)`
returns `[]`; the poll only reports changes.
**Warning signs:** duplicated first lines after every Start/Restart.

### Pitfall 5: n_required_types mistaken for the display count
**What goes wrong:** showing `n_required_types` as "number of interactions required"
is WRONG for block_exclusive (items = the whole allowed list, generator.py:409-410)
and for unset when the pool is smaller than the cap (k = min(...), generator.py:431).
**How to avoid:** `len(required['items'])` (list) / 1 (any) — the payload's required
dict is the only display source; `difficulty` is generation metadata.
**Warning signs:** a tab count disagreeing with the panel's `N/M` line after a
block_exclusive or small-pool unset game.

### Pitfall 6: reading pre-GO state as game state
**What goes wrong:** between Start and GO the wizard exists but is NOT activated (A's
deferred design); a poll/hint reading `cmd.get_wizard()` in that window sees None
(untouched stack), while the tab's pending-wizard reference is live. Conflating the
two produces phantom "no game" states.
**How to avoid:** follow A's split — the pending wizard is accessed via the tab's
`self._pending_wizard` reference only for start-sequence reads; the POLL starts after
GO (`_begin_play` starts the timer). C's handler already silent-no-ops pre-GO on the
same reasoning.
**Warning signs:** log lines appearing during the countdown.

### Pitfall 7: 'score'-token collisions in new pure text (PROSE_PIN hygiene)
**What goes wrong:** tests/test_wizard_text.py pins result-line probes by substring;
new panel-adjacent text carrying the word 'score' in the WRONG builder could collide
with probe expectations (the `_molecule_scope_line` precedent deliberately avoided
the token, [SRC wizard_text.py:178-185]).
**How to avoid:** Phase-5 `status_text` contains no score lines at all (reserved for
Phase 6); when Phase 6 lands them, they live in their own builder functions with
their own tests.
**Warning signs:** a new test asserting substring overlap across builders.

---

## Verification tiers

| Tier | What it proves | How |
|---|---|---|
| WSL TDD (pure, python3.6) | `required_display` both modes + fail-closed refusals; `status_events` every diff rule (init silent, molecule/level change, selection change, error change, sticky dedupe, cleared-error silence); `level_molecule_line`; `selected_line`; `error_line`; `EVENT_KINDS` documents the reserved Phase-6/7 vocabulary | NEW `tests/test_status_text.py` (RED→GREEN per the 02-02 pattern) + `PURE_MODULES` registration |
| T1a (headless cmd tier) | `wizard.get_status()` shape (level_pos/level_total present, plain data); `engine.game_status()` snapshot keys + EngineError before new_game | SMOKE-14 (or SMOKE-11 PART per the planner's ordering) |
| T1b (headless offscreen Qt — `QT_QPA_PLATFORM='offscreen'` before the pymol.Qt import, ZERO modals per the 04-01/04-05 recipe) | info box read-only + `_log` appends; required label renders both modes from a LIVE game; direct `_refresh_status` calls land diff lines ('Selected:' after the SMOKE-07 scripted-pick recipe `cmd.select('sele', '<slot> and name CA')` + `do_select('sele')`; 'ERROR:' after a no-selection nudge); the box gains NO score lines (Phase-5 reserve) | SMOKE-14 |
| [HUMAN] GUI checkpoint | log readability/placement, label layout, both-mode required display across different games, restart clears the log | rides the Phase-5 checkpoint steps |

Smoke numbering: **SMOKE-13 is TAKEN** (A's timer probe, already PASSED per A's
research). I claim **SMOKE-14** = status-surface probe. If the planner prefers fewer
scripts, my T1a/T1b checks can fold into SMOKE-11's ordered PART list instead — hand
the planner the ordered PART-list request (C's protocol); do not self-assign letters
into the already-reworked SMOKE-11 (A reworks PART G; C adds a hint PART).

---

## Module/tier placement table (Q7)

| Piece | Tier | File | TDD? |
|---|---|---|---|
| `status_text.py` (NEW): `required_display`, `status_events`, `level_molecule_line`, `selected_line`, `error_line`, `EVENT_KINDS` | PURE (imports `.wizard_text` only; zero stdlib needed) | `aamatch/status_text.py` | YES — WSL battery |
| `GameWizard._state_dict()` += `level_pos`/`level_total`; NEW public `get_status()` (returns `_state_dict()`) | cmd | `aamatch/wizard.py` | smoke-tier (no WSL import) |
| NEW `engine.game_status()` → `_current_game().to_dict()` | cmd | `aamatch/engine.py` | smoke-tier |
| Info box `QTextEdit`(read-only) + `_log()` | Qt | `aamatch/game_window.py` (A's NEW module) | T1b |
| Required `QLabel` + molecule-change update + no-game reset | Qt | `aamatch/game_window.py` | T1b |
| `_refresh_status()` poll + `_last_status` plain-dict store | Qt | `aamatch/game_window.py` | T1b |
| `_on_tick` gains the `_refresh_status()` call (after A's timer-label half; skipped during A's modal-pause branch) | Qt | `aamatch/game_window.py` (A owns `_on_tick`) | T1b |
| Hint info-box line (consumes C's `hint()` → `{'count','slot_ids'}`) | Qt | `aamatch/game_window.py` (C's handler calls `self._log(...)`) | T1b |
| Start-sequence log clear + first level line + first label | Qt | `aamatch/game_window.py` (`start_countdown`/`_begin_play` — A's methods, my content) | T1b |
| `PURE_MODULES += 'status_text'` | test | `tests/test_purity.py:92-95` | YES |
| `SCANNED_MODULES += 'game_window.py'` | test | `tests/test_wizard_source.py:51-53` | YES (A's module landing) |

Single-home laws respected: `required_summary` stays in `wizard_text` (reused, not
duplicated); `INTERACTION_TYPES` stays in `setup_state`; no new cmd-tier module (the
fallback event-bus is deliberately NOT built — see standard_stack alternatives).

---

## Gate impact (Q8)

1. **tests/test_purity.py** — `PURE_MODULES` grows by exactly one: `'status_text'`
   (unregistered pure modules are silently ungated, test_purity.py:288-296). No
   whitelist changes (status_text imports only `.wizard_text`; no stdlib needed).
2. **tests/test_wizard_source.py** — `SCANNED_MODULES += 'game_window.py'` when A's
   module lands (growth protocol, test_wizard_source.py:21-22,51-53). I introduce NO
   new cmd-tier module. The visual-primitive gate is unaffected (no scene calls).
3. **tests/test_code_audit.py PROSE_PIN** — NO deliberate update needed: the pins
   cover placement/engine/geometry docstrings only (test_code_audit.py:64-68); new
   modules must simply not mention the banned tokens (`get_model`/`matrix_reset`/
   `get_object_ttt`) — pure text builders never do.
4. **tests/test_package_skeleton.py** — untouched (the `run_plugin_gui` seam is A's
   surface; my scope changes no entry-point shape).
5. **NEW** `tests/test_status_text.py` — the phase's TDD battery (see Verification
   tiers). Registration-pin comment per the 02-02 pattern.
6. **Smokes** — SMOKE-13 taken (A, PASSED). NEW **SMOKE-14** (mine): T1a accessors +
   T1b status-surface drive (recipe in Verification tiers; reuses the SMOKE-07
   scripted-pick recipe). Alternative: fold into SMOKE-11's ordered PART list per the
   planner's call. python3.6 floor: `status_text.py` uses %-formatting only (no
   f-strings/dataclasses).
7. **PART-letter protocol** — if my checks ride SMOKE-11, hand the planner an ordered
   PART-list request; A's PART G rework + C's hint PART are already in flight.

---

## open_questions (Q10)

1. **Info-box verbosity / timestamp prefixes.** Recommend NO timestamps (prior-art
   parity — `PA-gui_game:119-120` appends bare lines; the timer label carries time)
   and the minimal Phase-5 line set in the event inventory (no movement/nudge lines,
   no panel mirroring per A's OQ-7). HUMAN may want richer narration later — the
   EVENT_KINDS vocabulary makes additions additive.
2. **Required-display vocabulary: tokens vs pretty names.** Recommended: canonical
   tokens (`h_bond`) everywhere in game surfaces — one vocabulary across panel, tab,
   and result lines; the setup form's pretty labels ([SRC setup_window.py:315-323])
   remain the teaching surface. Alternative (HUMAN-adjustable): move
   `_INTERACTION_LABELS` to a pure home and render `Hydrogen bond`-style names in the
   tab — costs a refactor of a human-verified module for a cosmetic gain.
3. **'any'-mode allowed-list context.** The payload does NOT carry the setup's
   `allowed_interactions` (verified: molecule keys are molecule_id/ligand/required/
   placement/grid, [SRC generator.py:862-874]), so `Required: any 1 interaction` shows
   no type context. Spec-literal reading (spec.md:40: "can be `any` or from the
   allowed list") supports 'any' alone. Threading the allowed list into the wizard
   (additive ctor param, picklable list) is POSSIBLE but not recommended for Phase 5.
4. **Formed-so-far counts in the required display.** NOT Phase 5: spec.md:52 (7.3)
   puts score/total display AFTER the molecule is finished — SCORE-01/02 territory
   (Phase 6). Phase 5 shows the requirement only; the panel's result lines are the
   per-Confirm feedback. Reserved via `molecule_scored`.
5. **Placeholder buttons policy (shared with A's OQ-1).** ADOPT A's recommendation:
   **later-add per owning phase** — Phase 5's Game tab carries Hint (C) + the status
   surface (info box/timer/required label) only; Confirm/Skip-give-up/Save/Restart/
   Reset/Import arrive with their owning phases (P6/P7), keeping each plan's
   `files_modified` disjoint. My earlier alternative (full inventory created disabled)
   is rejected for Phase 5: long-lived unconnected stubs + the wizard panel remains
   the live feedback surface per the 04-15 clarification. HUMAN/PLANNER decision.
6. **SMOKE-14 vs folding into SMOKE-11.** Recommend a separate SMOKE-14 (independent
   of A's PART G rework and C's hint PART); the planner may merge. Coordination only.
7. **Game-closed line on Done.** Skipped in Phase 5 (restart transitions would
   double-fire through `start_countdown`'s clear; the player sees the wizard vanish).
   Possible Phase-9 polish (a generation counter would disambiguate restart vs Done).
8. **Hint line text.** Pinned as C's sketch (`Hint: %d eligible amino acid(s)
   highlighted.`, consuming `result['count']`); HUMAN may prefer mentioning the
   carbon recolor explicitly — one-string change in C's handler, text pinned in
   `status_text` or at the call site per the planner's task split.

---

## Sources

### Primary (HIGH confidence — repo sources, read this session)
- `aamatch/wizard.py:17-29` (contract 2 pickle law), `126-143` (`__init__` attrs),
  `154-177` (activate), `248-273` (do_select/do_pick; `_error=None` at 298),
  `327-331` (`_required`), `333-349` (`_state_dict` — current keys), `423-433`
  (`_guard`), `528-568` (confirm flow), `570-594` (reset_grid)
- `aamatch/wizard_text.py:38-59` (buttons/codes), `64-74` (`_clip`), `77-103`
  (`required_summary`), `106-175` (`result_lines`; `N/M` at 146-148), `178-190`
  (`_molecule_scope_line` 'score'-token avoidance), `193-237` (`panel_entries`;
  `Required:` line at 217-219), `240-273` (`prompt_lines`; `_status_line`)
- `aamatch/engine.py:92-103` (module runtime + `_current_game`), `230-291`
  (new_game), `361-392` (detect_molecule), `395-421` (score_current/confirm)
- `aamatch/game_state.py:40-42` (INTERACTION_TYPES import), `62-85` (`score` binary/
  len-divisor), `141-175` (GameState fields), `182-185` (`total_score`), `187-191`
  (`start_timer`), `202-215` (`record_molecule_result`), `217-243` (`to_dict`)
- `aamatch/generator.py:337-439` (`derive_required`: 396 any/items[], 409-410
  block_exclusive items=allowed, 431-435 unset k=min + items), `862-874`
  (molecule payload keys — NO allowed_interactions echo)
- `aamatch/level_spec.py:9-35` (payload shape; difficulty.n_required_types),
  `116-121` (detector gate)
- `aamatch/setup_state.py:40-42` (INTERACTION_TYPES canonical list)
- `aamatch/setup_window.py:59-77` (singleton), `315-323` (`_INTERACTION_LABELS`),
  `594-607` (`_guard`), `784-802` (`_cleanup_now` isinstance gate — the
  module-identity precedent), `879-933` (`_on_start`/`_start_impl`)
- `aamatch/gamestart.py:285-339` (`start_game` — the seam A extends)
- `tests/test_purity.py:92-108` (PURE_MODULES + FORBIDDEN/ALLOWED_STDLIB),
  `288-296` (registration-pin warning)
- `tests/test_wizard_source.py:21-22,51-62` (SCANNED_MODULES growth protocol)
- `tests/test_code_audit.py:56-68` (banned calls + PROSE_PIN)
- `tests/test_wizard_text.py:85-114` (required_summary pins)

### PyMOL 2.5.0 source (HIGH)
- [SRC] `modules/pymol/wizarding.py:130-142` (`refresh_wizard` internal, no hook),
  `156-160` (`get_wizard`), `175-194` (`session_save_wizard` pickles the WHOLE stack;
  restore prints a warning on failure)
- [SRC] `modules/pymol/wizard/__init__.py:18-42` (`__init__`, `__getstate__` pops
  only `cmd`, `get_panel/get_prompt`, event-mask/do_* callbacks)

### Prior art (HIGH — shipped v1, read this session)
- [PA-OBS] `tmp/bioCHEMeleon/biochemeleon/gui_game.py:24-43` (QTextEdit read-only +
  tooltip, timer/remaining labels, layout row), `108-115` (1 Hz QTimer + state),
  `119-120` (`_log` = bare `append`), `122-130` (`_update_remaining` pull model),
  `234-264` (`start_countdown`: clear + `Get ready...` + 3/2/1/`GO!`),
  `266-287` (`_begin_play`: lazy wizard import, `set_callbacks`, timer start),
  `279-284` (the dual-anchor bug comment)
- [PA-OBS] `tmp/bioCHEMeleon/biochemeleon/game.py:15-46` (GameController: no Qt
  import; callbacks as plain attributes), `94-111` (`set_callbacks` — the DI shape
  AA-match cannot copy onto its wizard)
- [PA-OBS] `tmp/bioCHEMeleon/biochemeleon/wizard.py` (96 lines, zero Qt imports —
  the cmd-tier wizard stayed Qt-free in v1 too)
- [PA-OBS] `tmp/bioCHEMeleon/biochemeleon/setup_state.py:418-443`
  (`format_remaining` — the pure label-formatter precedent)
- [PA-OBS] `tmp/bioCHEMeleon/biochemeleon/__init__.py:160-261` (tab construction,
  `_on_start` = prepare → `setCurrentWidget(game_tab)` → `start_countdown`),
  `776` (save = single OBJECT, not session), `920-945` (cleanup resets log/labels)

### Sibling research (aligned, committed)
- `.planning/phases/05-game-status-tab-start-sequence/05-RESEARCH-window-start-timer.md`
  (A: game_window.py GameTab, deferred activation + `activate_game`, member-QTimer
  countdown, 1 Hz tick + modal pause, OQ-1 buttons, OQ-7 info-box ownership handoff)
- `.planning/phases/05-game-status-tab-start-sequence/05-RESEARCH-hint.md`
  (C: `GameWizard.hint()` → `{'count','slot_ids'}`, handler isinstance gate +
  silent no-op pre-GO, OQ-3 info-box line handoff)

## Metadata

**Confidence breakdown:**
- Widget/pattern choices: HIGH — prior art read line-by-line; AA-match equivalents are
  direct adaptations.
- Access path / polling recommendation: HIGH — the no-hook claim is verified in the
  PyMOL source; the pickle constraint is verified in two independent places
  (wizard.py contract + wizarding.py session code).
- Required-display semantics: HIGH — generator/level_spec/game_state/wizard_text all
  read and cross-consistent.
- Event inventory wording: HIGH as RECOMMENDATION (pinnable strings); the human may
  adjust any line before plans pin them in tests.
- Reserved Phase-6/7 sketches: MEDIUM — formats are proposals; Phase 6/7 research
  will pin their final wording.

**Research date:** 2026-09-18
**Valid until:** Phase-5 planning complete (~30 days; the verified API facts are
build-pinned and stable).
