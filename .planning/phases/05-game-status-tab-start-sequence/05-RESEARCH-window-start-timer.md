# Phase 5: Game Status Tab & Start Sequence — Research (window + start + timer)

**Researched:** 2026-09-18
**Domain:** Qt tab restructure inside the existing modeless SetupWindow, the Start
sequence (initial-state store + deferred wizard activation), the 3-2-1 countdown,
and the 1 Hz elapsed timer
**Confidence:** HIGH for stack/architecture (every claim read from shipped prior
art, the PyMOL 2.5.0 source tree, this repo's own code with file:line, or probed
live); MEDIUM only where flagged below (modal-timer interplay is not headlessly
provable per PITFALL P5).

**Citation shorthand:**
- `PA-__init__` = `tmp/bioCHEMeleon/biochemeleon/__init__.py` (shipped v1 plugin,
  read 2026-09-18) — [PA-OBS] when used as prior-art evidence
- `PA-game` = `tmp/bioCHEMeleon/biochemeleon/game.py`
- `PA-gui_game` = `tmp/bioCHEMeleon/biochemeleon/gui_game.py`
- `PA-gui_setup` = `tmp/bioCHEMeleon/biochemeleon/gui_setup.py`
- `pymol-src/<f>` = `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/bioCHEMeleon/tmp/pymol-src/modules/pymol/<f>` (PyMOL 2.5.0 tree)
- Repo files cited as plain paths.

---

## Summary

The entire Phase-5 window/start/timer surface is **proven prior-art territory**: v1
shipped exactly this shape (a `QTabWidget` with Setup + "Game status" tabs in one
modeless dialog; a Start handler that switches the tab and runs a 3-2-1 countdown;
a 1 Hz `QTimer` render loop; manual timer pause around modals). The AA-match
adaptation is mostly mechanical, with **three genuinely new design points**:

1. **The wizard must NOT be active during the countdown.** v1 activates its
   PickWizard only at GO (`PA-gui_game:266-269`), and the spec reads "countdown
   3, 2, 1, then start the game" (spec.md:34). AA-match's one-call seam
   `gamestart.start_game` currently activates the GameWizard as its last step, so
   the minimal-churn spec-faithful shape is an optional `activate=True` kwarg
   (default preserves every existing caller byte-for-byte) plus a new
   `gamestart.activate_game(wiz)` that re-evaluates the conditional replace AT GO
   time and sets the `GameState.timer_anchor`. The Qt window orchestrates: pop any
   prior GameWizard → `start_game(activate=False)` → switch tab → countdown → GO →
   `activate_game` → timer starts from zero. (Fallback: keep activation immediate
   and make the countdown purely presentational — zero churn but ≤3 s of pre-GO
   play; flagged as open question with a recommendation to defer.)
2. **The countdown must be CANCELLABLE.** v1's `QTimer.singleShot` lambda chain is
   uncancellable and v1 has a latent bug (Cleanup during a countdown leaves a stale
   wizard activation at GO — `PA-__init__` `_on_cleanup` never cancels). AA-match's
   Cleanup and double-Start are both reachable mid-countdown, so the recommended
   mechanism is a **reusable member `QTimer`** stepping 3→2→1→GO; `.stop()`
   cancels it (probe-verified, check 6 below). Every new start cancels any pending
   countdown first.
3. **One timer anchor, live-read.** `GameState.timer_anchor` (game_state.py:187)
   is the single source; the Game tab's tick reads it LIVE each tick. v1 kept two
   clocks (controller + GUI) and hit a real drift bug that needed a patch
   (`PA-gui_game:279-284`). Pause-on-modal = the 1 Hz tick checks
   `QApplication.activeModalWidget()` (probe-verified to exist and return None
   with no modal) and rebases the anchor to freeze at the last shown second —
   this generalizes v1's manual stop/rebase pattern (v1 only paused at the
   checkpoint save) and automatically covers Setup-tab file dialogs opened while
   a game runs.

The probe (SMOKE-13, authored and RUN by this research) proves all timer mechanics
headlessly: repeating QTimer, `stop()` cancellation, `singleShot(0)`, delayed
`singleShot`, QTabWidget round-trip, and the `activeModalWidget()` predicate all
work under `QT_QPA_PLATFORM=offscreen` in the real conda env.

**Primary recommendation:** New Qt-tier module `aamatch/game_window.py` holding the
GameTab (info box, timer, countdown, Hint shell); extend `aamatch/gamestart.py` with
`activate=` kwarg + `activate_game()` + the `_last_start` initial-state store; wrap
the existing SetupWindow content in a `QTabWidget` Setup page; drive the whole
sequence from the window (prior-art pattern). SMOKE-11 gains parts and reworks
PART G's drive sequence; SMOKE-08 is untouched.

---

## standard_stack

Nothing new is installed. Qt comes via `from pymol.Qt import QtWidgets, QtCore`
only (the shim imports `QtGui, QtCore, QtOpenGL, QtWidgets` as a unit —
`pymol-src/Qt/__init__.py:28`; `from PyQt5 import ...` stays banned repo-wide).

### Core (Phase-5 additions to the proven stack)

| API | Where | Purpose | Evidence |
|---|---|---|---|
| `QtCore.QTimer` (member, interval 1000 ms) | GameTab | 1 Hz elapsed-timer render | [PA-OBS] `PA-gui_game:108-115` ("1 Hz QTimer (main thread…)"), probed SMOKE-13 check 1 |
| `QtCore.QTimer` (member, interval 1000 ms, reused) | GameTab | the 3-2-1 countdown steps (3→2→1→GO), cancellable via `.stop()` | probe SMOKE-13 checks 1+6; v1 used an uncancellable `singleShot` chain (`PA-gui_game:258-264`) — same cadence, better cancellation |
| `QTimer.singleShot(0/delay, fn)` | optional deferred steps | fires on next processEvents / after real delay | probe SMOKE-13 checks 2+3; [PA-OBS] `PA-gui_game:261` |
| `QTabWidget` (+`addTab`, `setCurrentWidget`) | SetupWindow | Setup + Game status pages in ONE modeless dialog | [PA-OBS] `PA-__init__:172-184` ("pattern from optimize.py:72-79 — QTabWidget replaces the legacy notebook widget"); probed SMOKE-13 check 4 |
| `QApplication.activeModalWidget()` | GameTab tick | the timer-fairness pause predicate (is any modal child open?) | probe SMOKE-13 check 5 (exists, None without modal); ROADMAP Phase-5 research note |
| `QTextEdit` (read-only) | GameTab | the generic rolling info box | [PA-OBS] `PA-gui_game:24-27` (setReadOnly(True), append via `_log`) |
| `QLabel` | GameTab | elapsed timer OUTSIDE the info box; required-interactions label | [PA-OBS] `PA-gui_game:28,39-42`; spec.md:37 "timing after the game started (out of info box)" |
| `time.time()` anchors | GameState (pure) | the elapsed source of truth | repo: `aamatch/game_state.py:187-191` |

### Existing repo seams consumed unchanged

| Seam | Citation | Role in Phase 5 |
|---|---|---|
| `gamestart.start_game(setup, seed, candidates, ligand_content)` | `aamatch/gamestart.py:285-339` | gains `activate=True` kwarg + the `_last_start` store; default path byte-identical (SMOKE-08 preserved) |
| `engine.new_game` / `engine.materialize` | `aamatch/engine.py:230, 294` | already ARE "generate the representations per setup" (research Q3b: nothing missing) |
| `GameState.start_timer(now)` | `aamatch/game_state.py:187-191` | the anchor setter — never called in production yet (grep-verified); Phase 5 wires it |
| `GameState.timer_anchor` field + `to_dict/from_dict` | `aamatch/game_state.py:174, 217-243` | single anchor home; lossless round-trip already built (Phase 7 inherits) |
| `GameWizard.activate(replace)` / `cleanup()` | `aamatch/wizard.py:154-177, 179-206` | called only at GO in the deferred design; msm ORDER LAW untouched |
| `setup_window._cleanup_now` pop-first gate | `aamatch/setup_window.py:784-802` | the window's start sequence reuses the same isinstance-pop (without deletion) |

### Alternatives considered

| Instead of | Could use | Tradeoff |
|---|---|---|
| Reusable member QTimer for countdown | `QTimer.singleShot` lambda chain (v1) | The chain is the shipped-v1 proven pattern but CANNOT be cancelled; the member timer is equally simple (probe-verified) and cancels cleanly — required for the Cleanup/double-Start mid-countdown edges |
| Tick-level `activeModalWidget()` pause | `QEvent.WindowBlocked/Unblocked` application event filter | Exact pause timing, but unverified on this build (LOW); the 1 Hz rebase is ≤1 s coarse, which is acceptable for a game clock |
| Separate `game_window.py` module | inline GameTab class in `setup_window.py` | Inline keeps one Qt module (one SCANNED_MODULES entry) but couples the tab restructure and the game-tab plans to the same file; the separate module mirrors v1's `gui_setup.py`/`gui_game.py` split and keeps parallel-plan `files_modified` disjoint |

**Installation:** none — stdlib `time` + `pymol.Qt` (PyQt5 5.12.3 / Qt 5.12.9,
recorded baseline 01-07) + the existing pure layer.

---

## architecture_patterns

### Recommended module layout (delta)

```
aamatch/
├── gamestart.py         # EXTEND (cmd tier): + activate kwarg on start_game,
│                        #   + activate_game(wiz) (GO-time activation + timer anchor),
│                        #   + module-level _last_start initial-state store
├── game_window.py       # NEW (Qt tier): class GameTab(QtWidgets.QWidget) --
│                        #   info box + _log, timer label + 1 Hz QTimer + _on_tick,
│                        #   required-interactions label, Hint button,
│                        #   countdown (member QTimer: _countdown_step/GO),
│                        #   cancel_pending_start(); start_countdown(wiz) entry
├── setup_window.py      # EXTEND (Qt tier): QTabWidget restructure (Setup page
│                        #   wraps form_area + stretch + 7-button row; Game page
│                        #   = self.game_tab = GameTab()); _start_impl reworked to
│                        #   the deferred sequence; _pop_game_wizard() helper split
│                        #   out of _cleanup_now's first half; _on_cleanup cancels
│                        #   a pending countdown
├── game_state.py        # EXTEND (pure, optional): rebase_timer(now, elapsed)
│                        #   pure method if the planner wants the pause rebase
│                        #   routed through a named op (see pitfalls P-5)
└── wizard_text.py       # (optional pure home for format_elapsed — see Q7)
```

`aamatch/__init__.py` stays untouched (Gate A2: `run_plugin_gui` still returns
`open_window()`; `tests/test_package_skeleton.py:147-162` pins that AST shape).

### Pattern 1 — the window drives the start sequence (tab switch + countdown)

**What:** the cmd-tier seam never learns about tabs; the Qt window owns the
sequence and switches the tab itself.
**When to use:** always for this phase — it is the prior-art-proven pattern
([PA-OBS] `PA-__init__:242-261`: `_on_start` = prepare/start →
`self.tabs.setCurrentWidget(self.game_tab)` → `self.game_tab.start_countdown(...)`).

```python
# aamatch/setup_window.py (shape only — the deferred sequence)
def _start_impl(self):
    # ... build_state pre-checks + seed policy UNCHANGED (ordering law) ...
    self._pop_game_wizard()          # isinstance-pop, no deletion (04-11 pattern)
    wiz = gamestart.start_game(setup=state, seed=seed, candidates=...,
                               ligand_content=..., activate=False)
    self.tabs.setCurrentWidget(self.game_tab)          # "same window" (spec.md:33)
    self.game_tab.start_countdown(wiz)                 # 3-2-1 -> GO
    return wiz   # assertion handle for smokes

# aamatch/game_window.py (shape only)
def start_countdown(self, wizard):
    self._pending_wizard = wizard
    self._log('Get ready...')
    self._countdown_n = 3
    self._countdown_timer.start(1000)   # member QTimer; .stop() cancels

def _countdown_tick(self):
    n = self._countdown_n
    if n > 0:
        self._log('%d' % n)
        self._countdown_n -= 1
    else:
        self._countdown_timer.stop()
        self._log('GO!')
        self._begin_play()

def _begin_play(self):
    from . import gamestart
    gamestart.activate_game(self._pending_wizard)   # cmd-tier activation + anchor
    self._pending_wizard = None
    self._timer.stop()          # defensive (prior-art shape)
    self._timer.start(1000)     # 1 Hz render loop
```

### Pattern 2 — GO-time activation lives in the cmd tier

**What:** `gamestart.activate_game(wiz)` is the ONLY place that pushes the
GameWizard on the deferred path, sets the timer anchor, and re-evaluates the
conditional replace AT ACTIVATION TIME (the stack can change during the 3-second
countdown, so the 03-05 conditional-replace decision is re-checked, not cached).
**Why:** keeps all cmd-tier game semantics in the cmd tier; the Qt tier stays a
sequencer. `start_game`'s `activate=True` branch calls the same function (one
activation home; SMOKE-08's msm ORDER-LAW asserts fire on the unchanged default
path).

```python
# aamatch/gamestart.py (shape only)
def start_game(setup=None, seed=42, candidates=None, ligand_content=None,
               activate=True):
    # ... cleanup -> new_game -> materialize -> compose (UNCHANGED) ...
    # ... _last_start store set here (after materialize SUCCEEDED) ...
    if activate:
        activate_game(wiz)
    return wiz

def activate_game(wiz):
    """Push the prepared GameWizard + anchor the timer (Phase 5 GO step)."""
    from . import engine
    replace = 1 if isinstance(cmd.get_wizard(), GameWizard) else 0
    wiz.activate(replace=replace)
    engine._current_game().start_timer(time.time())   # timer starts from zero
```

### Pattern 3 — the 1 Hz tick renders from the LIVE anchor; pause = rebase

**What:** the tick computes `elapsed = time.time() - anchor` from
`GameState.timer_anchor` each tick (never a GUI-side copy — see pitfall P-4),
formats `M:SS` like v1, and freezes under any open modal child by rebasing the
anchor to the last shown elapsed.
**When:** every tick after GO.

```python
# aamatch/game_window.py (shape only)
def _on_tick(self):
    if QtWidgets.QApplication.activeModalWidget() is not None:
        # timer-fairness rule (ROADMAP Phase-5 note): freeze at the last
        # shown second -- rebase the anchor so elapsed stops advancing.
        # (Granularity: <=1 s over-count at modal-open edge; document.)
        from . import engine
        try:
            gs = engine._current_game()
        except engine.EngineError:
            return
        gs.rebase_timer(time.time(), self._last_shown_elapsed)  # pure op
        return
    self._last_shown_elapsed = self._compute_elapsed()
    self._timer_label.setText(self._format(self._last_shown_elapsed))
```

### Pattern 4 — the initial-state store near the seam

**What:** `gamestart._last_start = {'setup', 'seed', 'candidates',
'ligand_content'}` (deep-copied setup) is set once per successful start; Phase 6
Restart replays it verbatim through `start_game` (ROADMAP:159 "Restart replays
the stored initial state into a fresh game").
**Why here:** the one-call seam already owns every input; the window's
`_last_export` (Decision 4) is the WRONG home — a later export overwrites it and
a restart would replay the wrong game.

### Anti-patterns to avoid

- **`gamestart` importing `setup_window`** (option a of research Q2): violates
  the strict downward dependency direction (`.planning/research/ARCHITECTURE.md:20,
  66-73`; `SUMMARY.md:61`) and is unnecessary — no player-facing start path exists
  outside the window (verified: `aamatch/__init__.py:39`).
- **GUI-side clock copy** (v1's `gui_game._start_time` alongside
  `controller._start_time`): produced a real bug (`PA-gui_game:279-284`).
  One anchor in GameState; the tick reads it live.
- **Uncancellable singleShot countdown chain** (v1's exact mechanism): cannot be
  stopped, so Cleanup/double-Start mid-countdown leak a stale GO activation.
- **Dead stub handlers on the Game tab** if the full spec button inventory is
  created now: Phase 4's convention was "created but NOT connected" for a fixed
  7-button set; game-lifecycle buttons arrive across Phases 5-7 — see open
  question OQ-1 before deciding.
- **Storing Qt objects on the GameWizard**: unchanged repo law (wizard.py:17-21
  contract 2); the Game tab holds Qt widgets, the wizard stays picklable.

---

## dont_hand_roll

| Problem | Don't build | Use instead | Why |
|---|---|---|---|
| 1 Hz elapsed render | threading.Thread clock / busy-wait | `QtCore.QTimer` member + `processEvents` pumping (probe-proven) | PITFALL 1/15: `cmd.*` from foreign threads deadlocks; the main-thread timer is the shipped pattern |
| Countdown cadence | modal overlay / sleep loops / singleShot chain | reusable member QTimer stepping 3→2→1→GO | cadence == proven 1 s steps; `.stop()` cancellation is a probe-proven property the chain lacks |
| Tabbed window | a second top-level dialog for game status | `QTabWidget` inside the existing modeless dialog | spec.md:33 "the Game status tab of the SAME window"; v1 precedent |
| Modal-open detection | hand-rolled child scan / parent walk | `QApplication.activeModalWidget()` | one call, probe-verified to exist on this build; catches EVERY modal child incl. future file dialogs |
| Elapsed formatting math | custom wall-clock parsing | `int(elapsed)//60` + `%d:%02d` | v1's exact shipped format (`PA-gui_game:228-232`); optionally hoist into a pure helper for WSL pinning |
| Initial-state replay | object-level snapshot/restore machinery (v1 backup pattern) | the materialization INPUT tuple + re-run `start_game` | AA-match owns its objects (fresh `_aam_*` names, never load-into-existing — placement.py 02-13 docstring), so the inputs fully regenerate the scene; v1 needed a backup only because hiders were inserted into the USER's object |

**Key insight:** v1's backup-object initial-state pattern exists because v1
mutated the user's molecule in place. AA-match's materializer builds its own
objects from plain-data inputs every time — the input tuple IS the initial state.
Do not port the backup machinery.

---

## common_pitfalls

### P-1: Wizard active during the countdown (spec violation + pre-GO play)
**What goes wrong:** if `start_game` activates immediately (today's behavior) and
the window only then switches tabs and runs the countdown, the player can pick,
move, and even confirm during "3, 2, 1" — the game began before GO.
**Why it happens:** the one-call seam bundles activation with preparation.
**How to avoid:** the `activate=False` deferral + `activate_game()` at GO
(Pattern 2), with the window popping any prior GameWizard BEFORE
`start_game(activate=False)` so the countdown window is wizard-free.
**Warning signs:** the wizard panel is visible during the countdown; SMOKE-11
PART G's wizard-active assert fires right after `_start_impl()`.

### P-2: Stale GO activation after Cleanup / double-Start mid-countdown
**What goes wrong:** Cleanup (Setup tab) during a countdown deletes the freshly
materialized objects; the pending countdown then fires GO and pushes a wizard
whose registry references deleted objects. Double-Start leaves TWO pending
countdowns; the first GO activates the ORPHANED first wizard over the second
game.
**Why it happens:** an uncancellable pending callback outlives the game it was
created for (v1 has this latent bug — `PA-__init__:_on_cleanup` never cancels).
**How to avoid:** member-QTimer countdown + `cancel_pending_start()` called from
`_on_cleanup` AND from every new `start_countdown` (self-healing: a new countdown
cancels the previous one). Probed: `QTimer.stop()` cancels pending firings
(SMOKE-13 check 6).
**Warning signs:** a GO that activates a wizard after a Cleanup count > 0.

### P-3: The restart edge during the deferred window (old GameWizard active)
**What goes wrong:** on a mid-game restart, the OLD GameWizard stays on the stack
until GO (3 s) — its slot map points at objects `start_game`'s cleanup already
deleted; clicks during the countdown hit the stale wizard.
**Why it happens:** `start_game`'s conditional replace pops the prior GameWizard
only AT ACTIVATION (03-05 recorded decision — do NOT redesign it for direct
callers; SMOKE-08's ORDER-LAW teeth depend on it).
**How to avoid:** the window's start sequence pops the prior GameWizard itself
BEFORE `start_game(activate=False)` (the 04-11 `_cleanup_now` isinstance-pop
pattern, deletion excluded — start_game's `cleanup_game_objects` deletes).
**Warning signs:** `cmd.get_wizard()` is a GameWizard during the countdown.

### P-4: Two clocks drift (the v1 bug class)
**What goes wrong:** a GUI-side `_start_time` copy and `GameState.timer_anchor`
disagree after any rebase (pause) — the display and the persisted state diverge.
**Why it happens:** v1 kept both and needed a patch (`PA-gui_game:279-284`:
"if the controller already has a `_start_time`, do NOT clobber it").
**How to avoid:** single anchor in GameState; the tick reads it LIVE every tick;
rebase mutates the one anchor.
**Warning signs:** the displayed elapsed disagrees with the sidecar after a
pause (Phase 7).

### P-5: Timer keeps running under modal children
**What goes wrong:** modal children (QMessageBox, QFileDialog, future
confirmations) run a nested event loop that STILL processes timers — the 1 Hz
tick keeps firing and elapsed keeps advancing while the player is stuck in a
dialog (unfair time; ROADMAP's timer-fairness UX rule).
**Why it happens:** Qt modal dialogs spin a local event loop; timers fire inside
it. [MEDIUM confidence — standard Qt behavior, not headlessly provable (PITFALL
P5 forbids modals offscreen); the Phase-5 [HUMAN] checkpoint should watch the
timer during a real file dialog.]
**How to avoid:** the tick's `activeModalWidget()` check + anchor rebase
(Pattern 3). This also catches Setup-tab file dialogs opened mid-game (a v1 gap).
**Warning signs:** the timer label advances while a warning box is open.

### P-6: `_guard` boxes are modal — never inside the tick or countdown
**What goes wrong:** a `QMessageBox` inside a tick handler re-enters a modal
loop inside a timer callback (and blocks offscreen smokes indefinitely — the
04-09 smoke-99 receipt).
**How to avoid:** the tick/countdown own NO boxes; failures surface via the
normal handler `_guard` wrappers only.
**Warning signs:** any `QMessageBox` reference inside `_on_tick`/countdown code.

### P-7: PROSE_PIN / banned-token drift in new docstrings
**What goes wrong:** new `gamestart.py`/`game_window.py` docstrings mentioning
the banned cmd tokens (get_model/matrix_reset/get_object_ttt) would fail
`tests/test_code_audit.py`'s prose pin (gamestart.py currently carries ZERO
pinned mentions — verified).
**How to avoid:** refer to them only as "the banned matrix calls" (the
`wizard.py:66-69` convention). No naive atom/record double loops are planned
(timer/tab code touches no atom namespaces), so the TOKEN-PAIR rule stays
dormant.

### P-8: `QTimer.singleShot` chains fire THROUGH nested event loops
**What goes wrong:** a pending singleShot (or the 1 Hz timer) fires while a modal
child runs its loop — any "wait for the modal to close" assumption in countdown
or tick code is wrong by construction (same root cause as P-5).
**How to avoid:** design for the timer firing under modals (the rebase freeze);
never assume a modal suspends timers.
**Warning signs:** countdown steps observed while a dialog is open (harmless
today — nothing opens modals during the 3-s countdown; document it).

---

## Verification tiers (headless-provable vs human-checkpoint)

| Tier | What is provable | How |
|---|---|---|
| T0/T1 (WSL, python3.6) | pure additions (`rebase_timer`, optional `format_elapsed`): elapsed math, rebase semantics, format strings | unit tests, zero stubs |
| T1a (headless PyMOL, cmd tier) | `start_game(activate=False)` returns an UN-activated wizard; `activate_game(wiz)` pushes it + sets the anchor; `_last_start` round-trips; scene growth asserts | SMOKE-08 extension (or PART E-style in SMOKE-11) |
| T1b (headless offscreen Qt) | Game tab construction (info box read-only, timer label "0:00", required label present, tabs.count()==2, Setup page holds the 7 buttons); countdown steps driven AS METHODS (direct `_countdown_tick` calls → "3"/"2"/"1"/"GO!" in the log); GO driven directly → wizard active + anchor set; timer label via direct `_on_tick` with a manipulated anchor (set `timer_anchor = time.time()-75` → "1:15") and via a real 1.1 s pumped wait; `cancel_pending_start()` stops the pending countdown; singleton reuse unchanged | SMOKE-11 new PART(s) + SMOKE-13 (already PASSED) |
| T2 [HUMAN] | countdown look/feel in the real viewer; the timer freeze under a REAL modal (file dialog / warning box); the Game tab's visual layout; msm/pick feel at GO; the deferred-activation game feel end-to-end | Phase-5 GUI checkpoint (04-14/04-15 checkpoint style) |

**SMOKE-13 verdict (recorded 2026-09-18, run by this research):**

```
PROBE attempt: QT_QPA_PLATFORM=offscreen
offscreen: check1 repeat-QTimer OK (3 firings in ~0.7 s)
offscreen: check6 stop-cancels OK
offscreen: check2 singleShot(0) OK
offscreen: check3 delayed-singleShot OK
offscreen: note game_page isVisible() False (offscreen semantics)
offscreen: check4 QTabWidget round-trip OK
offscreen: check5 activeModalWidget predicate OK (None w/o modal)
=== PROBE PASS (platform=offscreen) ===
=== SMOKE-13 PASS ===
```

(`smoke/smoke_13_qt_timer_probe.py` is committed for the executor to re-run;
`run_smoke.sh` derives NN=13 and greps the final marker.)

**Recommended assertion strategy (anti-flakiness):** drive countdown steps and GO
as ORDINARY METHODS (deterministic); treat real-timer firing as asserted once by
SMOKE-13 (already green) and let cadence/feel stay with the [HUMAN] checkpoint.
For the label, prefer the deterministic anchor-manipulation drive
(`timer_anchor = time.time() - 75` → `_on_tick` → "1:15") over real sleeps where
possible; a single real-time pumped check (1.1 s) is acceptable as SMOKE-13
already proves the mechanism.

---

## Module/tier placement table

| Piece | Tier | Home | Notes |
|---|---|---|---|
| GameTab class (info box, timer label, required label, countdown, Hint button) | Qt | NEW `aamatch/game_window.py` | module-level `from pymol.Qt import QtWidgets, QtCore` (legal+required, setup_window precedent); NEVER in PURE_MODULES; joins `SCANNED_MODULES` |
| `_log` info-box append + content policy | Qt | `game_window.py` (`_log`) / content owned by researcher B | the countdown appends via the same `_log` — shared interface |
| 1 Hz elapsed timer + `_on_tick` + modal-freeze pause | Qt | `game_window.py` | reads the LIVE GameState anchor |
| Countdown member QTimer + `cancel_pending_start` | Qt | `game_window.py` | cancellable (probe check 6) |
| Tab restructure (QTabWidget Setup/Game pages) | Qt | `setup_window.py` | existing attributes preserved; SMOKE-11 PART B stays green |
| Start sequence orchestration (pop → prepare → switch → countdown) | Qt | `setup_window.py` (`_start_impl` + `_pop_game_wizard`) | ordering law preserved (build_state refusals before ANY scene touch) |
| `start_game(activate=...)` + `activate_game(wiz)` | cmd | `gamestart.py` | default path byte-identical; NO Qt |
| `_last_start` initial-state store | cmd | `gamestart.py` module state | deep-copied setup; set on materialize success |
| Timer anchor set (GO) | cmd | `gamestart.activate_game` → `engine._current_game().start_timer(time.time())` | one anchor home (pure GameState) |
| `rebase_timer(now, elapsed)` (pause freeze op) | pure | `game_state.py` (optional; if the planner wants a named op) | no PURE_MODULES change; `time` already whitelisted |
| `format_elapsed(seconds)` (optional WSL pin) | pure | `game_state.py` or `wizard_text.py` — or inline in `game_window.py` exactly like v1 (`PA-gui_game:228-232`) | inline is the v1 precedent; a pure helper only buys a format unit test |
| Required-interactions CONTENT | — | researcher B (SCORE-04) | data source: `wiz._payload['levels'][L]['molecules'][M]['required']` = `{'mode': 'any'\|'list', 'items': [{'type','count'}]}` (`aamatch/generator.py:727, 862`), reachable from the GO-activated wizard |
| Hint handler (recolor-only) | cmd/Qt | researcher C (PLAY-05) | Game tab owns the button; the recolor op is C's plan |

**Purity cost:** ZERO new pure modules recommended → `PURE_MODULES` (currently 17,
`tests/test_purity.py:92-95`) unchanged; `ALLOWED_STDLIB` unchanged. If the
planner invents a pure module anyway (e.g. a `start_state.py`), it must be
registered in `PURE_MODULES` (the 01-08 gate demands registration to be gated)
and its imports reviewed against `ALLOWED_STDLIB`.

---

## Gate-impact list (every touched gate file + the exact edit)

| File | Change | Exact edit |
|---|---|---|
| `smoke/smoke_11_window.py` | EXTEND + rework PART G | Insert new PART(s) BEFORE the PART-H echo (established renumber pattern — the echo has shifted letters at 04-10/04-12/04-13, so expect the echo letter to move again): (i) tab asserts: `dlg.tabs.count() == 2`, the 7 button attributes still resolve with exact labels (PART B unchanged), game tab has info box + timer label "0:00"; (ii) PART G rework: after `dlg._start_impl()`, assert `dlg.game_tab._pending_wizard` is a `GameWizard` NOT on the stack (`cmd.get_wizard()` is not it), drive the GO step (the tab's begin method) directly, THEN assert `cmd.get_wizard()` is that wizard + msm law; G2 reads the pending wizard's `_payload['seed'] == 31337` BEFORE its GO; G3 unchanged; the restore block must call the tab's cancel before `cmd.set_wizard()`; (iii) countdown step drive: direct step calls land "3"/"2"/"1"/"GO!" lines; (iv) timer label: set `timer_anchor = time.time()-75` → direct `_on_tick` → label "1:15" (+ optionally one real pumped 1.1 s check) |
| `smoke/smoke_13_qt_timer_probe.py` | NEW (authored+PASSED by this research) | re-run as-is: `bash smoke/run_smoke.sh smoke/smoke_13_qt_timer_probe.py 120` |
| `tests/test_wizard_source.py` | GROW | `SCANNED_MODULES` gains `'game_window.py'` (the growth protocol; 03-05/04-05 precedents) — the banned-visual-call scan and the banned-matrix-token zero-mention scan then cover the new module |
| `tests/test_purity.py` | UNCHANGED | no new pure module; pure additions live in registered modules (`game_state.py`) |
| `tests/test_code_audit.py` | UNCHANGED mechanics | discipline only: new docstrings must not add banned-token mentions (P-7); no atom-namespace double loops planned |
| `tests/test_package_skeleton.py` | UNCHANGED | `run_plugin_gui` still `return setup_window.open_window()` (AST contract :147-162) |
| `smoke/smoke_08_starter.py` | UNCHANGED | `start_game()` default path byte-identical (activate=True default); its 3 direct calls (:192/:485/:530) and ORDER-LAW asserts stay green |
| `smoke/smoke_10_upload_flow.py` | UNCHANGED | direct `start_game` calls (:225/:285) unaffected by the kwarg (default) |
| `aamatch/__init__.py` | UNCHANGED | Gate A2 (zero module-level imports) untouched |

---

## Answers to the numbered research questions

**Q1 — Tab restructure.** QTabWidget wrapper inside the existing SetupWindow
(v1-proven: `PA-__init__:172-184`). Today's structure (`aamatch/setup_window.py:
137-216`): top `QVBoxLayout` → (a) `self.form_area` (QWidget + QVBoxLayout; four
groups appended via `self.form_area.layout().addWidget`) → (b) `addStretch(1)` →
(c) the 7-button `QHBoxLayout`. Minimal churn: create a `setup_page` QWidget with
its own VBox, move (a)+(b)+(c) into it, `tabs.addTab(setup_page, 'Setup')`,
`tabs.addTab(self.game_tab, 'Game status')`, `top.addWidget(tabs)`. Every
attribute (`form_area`, `btn_*`) survives — PART B asserts button attributes +
labels, collect/apply round-trips, and singleton reuse, none of which depend on
parentage (verified against `smoke/smoke_11_window.py:189-260`). The 7-button row
STAYS on the Setup tab (spec.md:21 "the bottom of the popup"; v1 put setup actions
on the Setup tab — `PA-__init__:200-208` — and game buttons on the Game tab).
Game-lifecycle buttons per spec.md:39-47: Import (P7), Hint (P5 — build now,
researcher C), Confirm (P6), Skip/give-up dropdown (P6), Save (P7), Restart (P6),
Reset (P6); Cleanup stays on the Setup tab (spec.md:27; v1 precedent
`PA-__init__:203`). Placeholder-vs-later-add: open question OQ-1.

**Q2 — Tab-switch mechanism.** RECOMMEND (c): the Qt window drives the switch
after the cmd-tier prepare returns. (a) is rejected: cmd-tier importing the Qt
tier inverts the strict downward dependency (ARCHITECTURE.md:20; SUMMARY.md:61)
and is unnecessary. (b) a pure callback registry is over-engineered for one
window and has no prior-art precedent for tab switching. Evidence the window path
is the ONLY player path: `aamatch/__init__.py:39` (`run_plugin_gui` →
`open_window()`; the 04-05 rewire) — direct `start_game` callers are all test
smokes (SMOKE-08 :192/:485/:530, SMOKE-10 :225/:285, SMOKE-11 :433). v1 does
exactly (c) (`PA-__init__:260-261`).

**Q3 — Initial-state store + "representations".** Store = the materialization
INPUT tuple `{'setup' (validated, deep-copied), 'seed', 'candidates',
'ligand_content'}` — the same shape as Decision-4's `_last_export`
(`setup_window.py:872-874`), but in `gamestart` (a later export must never
corrupt the game's restart source). This satisfies Phase 6 Restart
(ROADMAP:159) and is compatible with Phase 7 (whose checkpoint store is the
RUNTIME state: `.pse` + sidecar with the payload VERBATIM — a DIFFERENT store;
do not conflate). NOT an object-level snapshot: AA-match materializes fresh
`_aam_*` objects from plain inputs (placement.py 02-13 docstring), so the
inputs fully regenerate the scene — v1 needed a backup object only because it
mutated the user's molecule in place (`PA-game.py:60` snapshot-before-insert;
restart restores from it, `PA-__init__:886-913`). Capture order: set
`_last_start` AFTER `new_game`+`materialize` succeed (a failed start leaves the
store holding the last successfully BUILT game's tuple). Deep-copy the setup
(allowed_interactions list aliasing — the 04-09 `_reset_impl` note,
`setup_window.py:612-622`). "Generate the additional representation based on the
setup parameters": ALREADY SATISFIED — `start_game`'s `new_game` (payload from
setup+seed+candidates) + `materialize` (grid+ligand objects) IS that
representation; verified end-to-end (`gamestart.py:309-314`). Nothing to build.

**Q4 — Countdown mechanics.** v1 verbatim: `start_countdown` clears the log,
logs "Get ready...", then `_countdown_step(3)`: `if n > 0: self._log("%d" % n);
QTimer.singleShot(1000, lambda: self._countdown_step(n - 1))` else `"GO!"` +
`_begin_play()` (`PA-gui_game:234-264`). The board is NOT frozen — the scene is
already built (controller.start ran before the countdown) and the viewer is fully
interactive, but NO wizard is active, so clicks don't pick anything. Nothing
blocks input (no modal, no overlay) — the countdown is log text only. The
PickWizard is created+activated ONLY in `_begin_play` (GO), which also sets
`_start_time` and starts the 1 Hz timer (`PA-gui_game:266-287`). AA-match maps
this to: no GameWizard during the 3-s window (prior GameWizard popped first —
P-3), GO → `gamestart.activate_game(wiz)` + anchor set + timer start. msm/wizard
state during the window: msm untouched (user's value; activate's ORDER-LAW
snapshot still captures it correctly at GO because the push happens then).
Closing the window mid-countdown is harmless (the dialog object survives; the
member QTimer keeps firing; GO activates — re-open shows the Game tab).
User wizard activation during the window: at GO, replace=0 pushes ON TOP of the
user wizard (stack-native dormancy — consistent with 03-05). `QTimer`/`singleShot`
verified live on this build (SMOKE-13). CANCELLABILITY is the one divergence from
v1's chain — see P-2.

**Q5 — Elapsed timer.** 1 Hz member QTimer: `setInterval(1000)` at construction +
`timeout.connect(self._on_tick)`, started at GO with a defensive `.stop()` then
`.start(1000)` (`PA-gui_game:108-115, 285-286`). `_on_tick` formats
`"%d:%02d"` (M:SS, minutes unbounded — 90 min renders "90:12"; v1 shipped this
exact format; no hours). The anchor: `GameState.timer_anchor` (game_state.py:174,
187-191) — currently NEVER set by production code (grep-verified; only
`tests/test_game_state.py` uses it). Set at GO inside `activate_game`. Pause-on-
modal: v1 does NOT auto-detect — it manually stops + rebases around known modals
(`PA-__init__:745-788` `_on_save`: `timer.stop()` → elapsed capture → file
dialog → rebase `self._controller._start_time = _time.time() - elapsed` →
`timer.start(1000)` on cancel/fail/success paths alike; also `_timer.stop()` in
`_on_cleanup` :929 and `_on_restart` :879; and `PA-persistence:64-67` documents
"capture BEFORE the file dialog"). The ROADMAP rule generalizes it. Recommend the
tick-level `activeModalWidget()` freeze (Pattern 3) as the Phase-5 mechanism
(probe-verified predicate; catches ALL modal children including Setup-tab file
dialogs during a running game), with v1's exact manual bracket documented for the
Phase-7 checkpoint save. The countdown does NOT need pause logic (nothing can
open a modal during it in Phase-5 scope; and timers fire through nested loops
anyway — P-8). `_guard` boxes and file dialogs are caught uniformly by the same
predicate.

**Q6 — Headless timer verification.** PROBED AND GREEN (SMOKE-13, first
attempt, offscreen): a repeating QTimer fires while a processEvents pumping loop
runs; `.stop()` cancels; `singleShot(0)` fires on the next processEvents; a
delayed singleShot fires only after real wall time; QTabWidget round-trips;
`activeModalWidget()` exists and is None without a modal. WHAT REMAINS
UNVERIFIED HEADLESSLY: timer firing UNDER a modal child's nested loop (cannot
open modals offscreen — P5/PITFALL) → [HUMAN]; visual cadence → [HUMAN]. The
exact probe script is committed (`smoke/smoke_13_qt_timer_probe.py`) with the
verdict lines above.

**Q7 — Module/purity placement.** See the placement table above. Summary: one
new Qt-tier module (`game_window.py`, joins `SCANNED_MODULES`), two extended
cmd-tier files (`gamestart.py` — no Qt; `setup_window.py` restructure), pure
additions confined to already-registered modules. `__init__.py` untouched.

**Q8 — Smoke/gate plan.** See the gate-impact table above. The one substantial
churn item is SMOKE-11 PART G's drive sequence (G1/G2 gain a GO step; the
wizard-active asserts move after GO) — an extension of the established
PART-letter pattern, not a rewrite of the checks.

**Q9 — Prior-art inventory.** Tab structure: `PA-__init__:160-224` (QTabWidget,
two tabs, per-tab button rows, lazy tab-class imports inside `__init__`). Tab
switch: `PA-__init__:260-261` (+ the async drain's duplicate at :641-642 and the
import path :866-868). Countdown: `PA-gui_game:234-264` (singleShot chain;
"Get ready..." → 3/2/1 → "GO!"; elapsed>0 resume support at :252-255 for the
checkpoint import path). GO/begin-play: `PA-gui_game:266-287` (wizard activate,
callbacks registered, `timer.stop()` defensive + `start(1000)`). Timer:
`PA-gui_game:108-115` (1 Hz QTimer), `:228-232` (`_on_tick`, M:SS format),
`:289-304` (`_on_win` — the ~100 ms after last `cmd.color` + `cmd.refresh()`
modal-timing pattern, a Phase-6 note, NOT built now). Pause-on-modal:
`PA-__init__:745-788` (save: stop/capture/dialog/rebase/start on all three
paths), `:879` (restart), `:929` (cleanup); `PA-persistence:64-67`
(capture-before-dialog doctrine). Initial-state storage: `PA-game.py:60`
(backup.snapshot BEFORE any insert — the v1 pattern AA-match does NOT need),
restart routing `PA-__init__:870-913` (imported: restore-from-backup +
re-snapshot + fresh `start_countdown`; fresh: re-run `_on_start` = regenerate
from the Setup tab — the same "replay the inputs" semantics AA-match adopts).
Reset-on-cleanup UI hygiene: `PA-__init__:942-945` (clear log, timer label
"0:00", remaining label reset).

**Q10 — Open questions.** See below.

---

## open_questions

1. **Game-tab button inventory: placeholder vs later-add.** spec.md:39-47 lists
   Import/Hint/Confirm/Skip-give-up/Save/Restart/Reset for the Game tab; Phase 5
   builds only Hint (PLAY-05) + the shell (info box, timer, required label).
   Options: (i) create the FULL inventory now, unconnected (AA-match Phase-4
   precedent — the 7 setup buttons were created unconnected in 04-05 and
   connected by 04-09..04-13); (ii) add rows per owning phase (v1 precedent —
   `PA-gui_game:44-98` comments show Phase 6/7/8 rows added incrementally).
   **Recommendation: (ii) later-add** — avoids long-lived unconnected stubs,
   keeps each plan's `files_modified` disjoint for parallel waves, and the
   layout reserves the slots with a stretch so later rows don't reflow the
   timer row. HUMAN/PLANNER decision (the phase brief asks this be decided, not
   assumed).
2. **Wizard activation timing (deferred vs immediate).** Recommend DEFERRED
   (activate at GO) — spec-faithful ("countdown … then start the game",
   spec.md:34), prior-art-proven, prevents pre-GO picks. Cost: SMOKE-11 PART G
   drive rework + `activate_game`. Fallback: immediate activation (zero churn in
   gamestart/SMOKE-08; PART G untouched; countdown purely presentational) with a
   ≤3 s pre-GO play window. If the human/planner prefers zero churn, the fallback
   is honest — but the research recommendation is defer.
3. **Timer format.** M:SS (v1) vs hh:mm:ss. Recommend M:SS (prior-art
   consistency; a game session beyond 60 min renders "75:23", acceptable; can
   revisit at Phase 9 polish).
4. **Countdown visuals.** Info-box log lines only (v1) vs an on-viewer overlay.
   Recommend log lines only — the spec demands no overlay, v1 shipped none, and
   an overlay adds a second surface to verify.
5. **Window title.** Keep 'AA-match Setup' (the 04-14 human checkpoint cited the
   title; a rename is cosmetic churn) vs rename to 'AA-match'. Recommend KEEP
   for Phase 5; flag as a Phase-9 polish candidate.
6. **Pause mechanism.** (A) 1 Hz `activeModalWidget()` rebase (recommended,
   probe-verified predicate, ≤1 s granularity) vs (B) `QEvent.WindowBlocked/
   Unblocked` application event filter (exact, UNVERIFIED on this build — would
   need its own probe) vs (C) manual per-site stop/rebase (v1-proven, incomplete
   coverage). Recommend (A) now; Phase 7's checkpoint save adds the exact manual
   bracket (PA-persistence:64-67 doctrine).
7. **Info-box content ownership boundary.** The countdown appends via the tab's
   `_log`; researcher B (SCORE-04) owns what ELSE the box shows and whether it
   mirrors wizard-panel text. The 04-15 clarification stands: the wizard panel
   remains the Phase-3 pick/move feedback surface; the info box is the tab-side
   narrative — recommend NO verbatim mirroring (two surfaces, two roles), with
   B deciding the content policy.

---

## Sources

### Primary (HIGH confidence — probed or source-verified)
- `smoke/smoke_13_qt_timer_probe.py` — authored and RUN by this research
  (2026-09-18): all 6 checks PASS under `QT_QPA_PLATFORM=offscreen`
  (PyQt5 5.12.3 / Qt 5.12.9 conda env). Verdict lines recorded above.
- `pymol-src/modules/pymol/Qt/__init__.py:24-64` — the shim: PyQt5 first,
  `QtCore` imported as a unit (QTimer available through the shim).
- `aamatch/setup_window.py:114-216, 462-592, 784-816, 879-933` — current
  dialog structure, collect/apply, `_cleanup_now` pop-first, `_start_impl`.
- `aamatch/gamestart.py:127-141, 143-282, 285-339` — the one-call seam,
  composition helpers, full start sequence.
- `aamatch/game_state.py:141-243` — GameState fields, `start_timer`,
  lossless round-trip.
- `aamatch/engine.py:11-31, 92-111, 230-293` — STATE SPLIT law, module runtime
  (`_payload/_registry/_game`; `new_game` creates a FRESH GameState per game).
- `aamatch/wizard.py:8-91, 154-246` — contracts (picklable data, stack-native
  lifecycle, msm ORDER LAW, display-staleness law), `activate`/`cleanup`.
- `aamatch/generator.py:727, 862` — payload `required` = `{'mode', 'items'}`.
- `aamatch/__init__.py:39` — run_plugin_gui → `open_window()` (the only
  player-facing start path).
- `smoke/smoke_11_window.py:1-131, 165-266, 424-470, 569-700` — PART structure,
  PART B asserts, PART E/G drives, PART H echo.
- `smoke/run_smoke.sh:1-17` — the NN-derivation + marker grep contract.
- `tests/test_purity.py:92-108` — `PURE_MODULES` (17) + `ALLOWED_STDLIB`.
- `tests/test_wizard_source.py:48-52` — `SCANNED_MODULES` growth protocol.
- `tests/test_code_audit.py:57-66` — `PROSE_PIN` table (gamestart.py carries
  zero pinned tokens).
- `tests/test_package_skeleton.py:147-162` — the run_plugin_gui AST contract.

### Secondary (MEDIUM/HIGH — shipped prior art, read line-by-line)
- [PA-OBS] `tmp/bioCHEMeleon/biochemeleon/__init__.py:160-224, 242-261,
  528-534, 641-642, 745-788, 866-868, 870-913, 915-946` — tabs, start flow,
  wizard teardown, save-pause/rebase, restart/cleanup.
- [PA-OBS] `tmp/bioCHEMeleon/biochemeleon/gui_game.py:1-115, 228-304, 234-287`
  — GameTab layout, QTimer, countdown chain, begin-play, win timing note.
- [PA-OBS] `tmp/bioCHEMeleon/biochemeleon/game.py:48-90` — snapshot-before-
  insert (the pattern AA-match deliberately does NOT port).
- [PA-OBS] `tmp/bioCHEMeleon/biochemeleon/persistence.py:60-70` —
  capture-before-dialog doctrine.

### Planning docs (constraints)
- `.planning/ROADMAP.md:136-148` — Phase 5 goal/criteria/research notes.
- `.planning/REQUIREMENTS.md:26, 43, 58` — SETUP-11 / PLAY-05 / SCORE-04 wording.
- `spec.md:29-47` — the start sequence + Game-tab inventory verbatim.
- `.planning/research/PITFALLS.md:97-108, 371, 428, 447-448` — modeless law,
  main-thread-only cmd, timer-fairness rule.
- `.planning/research/FEATURES.md:30-31, 38` — countdown/timer proven patterns,
  win-screen timing note (Phase 6).
- `.planning/research/ARCHITECTURE.md:20, 66-73, 179-192, 220, 252` — layering,
  timer discipline, callbacks, the wizard-after-countdown flow sketch.
- `.planning/STATE.md:141, 151, 173, 245, 247` — inherited decisions (04-15
  score-surface clarification, T1b tier, screen-relative help note).

### Tertiary (LOW — flagged for validation)
- QEvent.WindowBlocked/Unblocked event-filter pause alternative — UNVERIFIED on
  this build (would need its own probe if chosen; not the recommendation).
- "Timers fire inside a modal child's nested event loop" — standard Qt behavior,
  MEDIUM confidence, not headlessly testable (PITFALL P5); the Phase-5 [HUMAN]
  checkpoint verifies it incidentally.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every Qt API probed live (SMOKE-13) or read from the
  PyMOL source tree / shipped v1.
- Architecture: HIGH — the prior-art pattern is read line-by-line and every repo
  seam verified; the one divergence (cancellable countdown) is probe-backed.
- Pitfalls: HIGH for P-1..P-4, P-6..P-8 (source-verified); MEDIUM for P-5's
  modal-loop claim (not headlessly provable; [HUMAN] verifies).

**Research date:** 2026-09-18
**Valid until:** ~2026-10-18 (stable domain; the conda env and repo seams are
frozen baselines)
