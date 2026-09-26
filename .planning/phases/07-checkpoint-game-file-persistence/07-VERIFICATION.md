---
phase: 07-checkpoint-game-file-persistence
verified: 2026-09-26T21:05:00Z
status: passed
score: 51/51 must-have truths verified (12/12 plans)
re_verification: false
---

# Phase 7: Checkpoint & Game-File Persistence — Verification Report

**Phase Goal:** Games survive closing PyMOL: checkpoints fully reconstruct a running game (positions, scores, counters, timer), and exported game files load through the Game status tab's Import button.
**Verified:** 2026-09-26
**Status:** PASSED — zero gaps
**Re-verification:** No — initial verification

## Method

Goal-backward: every plan's `must_haves` frontmatter (07-01…07-12) was checked against the actual code at three levels (exists → substantive → wired), then against the ROADMAP success criteria. Recorded verdicts (07-11 battery, 07-12 human checkpoint) were treated as primary evidence; the WSL suite was independently re-run as teeth. SUMMARY claims were not trusted without code or recorded-verdict backing.

## Fresh Mechanical Teeth (this verification, 2026-09-26)

| Check | Result |
| --- | --- |
| `python3.6 -m py_compile aamatch/*.py` | OK (3.6 syntax floor) |
| `python3.6 -m unittest discover -s tests` | **OK — Ran 906 tests, 0 failures** (890 at the Phase-7 tree per 07-11; +16 from the already-merged Phase-8 wave 1). Purity gates included; checkpoint + persistence remain stub-free stdlib-only pure modules. |
| Purity registration | `tests/test_purity.py` lists `'checkpoint'` in PURE_MODULES (:103) and asserts the full set (:324) |
| Anti-pattern scan (grep TODO/FIXME/placeholder/stub across all 8 Phase-7 production files) | Clean — single hit is prose in a comment (game_window.py:1065, "never a placeholder '0:00'") |

## Per-Plan Must-Have Verification

Evidence format: code inspection (file:line) + recorded mechanical verdicts (07-11-SUMMARY) + recorded human verdicts (07-12-SUMMARY).

### 07-01 — Wizard pickle restore (4/4 truths)

| Must-have | Verdict | Evidence |
| --- | --- | --- |
| `.pse` with live GameWizard restores it; books intact | ✓ | `aamatch/wizard.py:197-208` `__reduce__` returns `(_rebuild_game_wizard, (), self.__getstate__())`; `_rebuild_game_wizard` at :100 (argless `object.__new__` path). SMOKE-17 two-run strict compare → `VERDICT wizard: strict restore compare -> PROVEN` (07-11). |
| Zero plugin console output on save/load | ✓ | 07-12 steps 2/6: **zero `Session-Warning` lines anywhere** (installed identity); SMOKE-17 run 2 same. |
| Restored state equals pre-save state | ✓ | SMOKE-17 strict compare (recorded PROVEN); books field-equality re-proven through the real pickle path in SMOKE-18 PART E. |
| Identity-matrix invariant holds after load | ✓ | SMOKE-17 recorded (movement bake + load both sides); 07-12 step 2 real-mouse pick echo on a restored slot object (`/_aam_aa14/.../CZ2`). |

### 07-02 — checkpoint.py pure module (4/4 truths)

| Must-have | Verdict | Evidence |
| --- | --- | --- |
| Four version gates incl. verbatim five-gate replay of the embedded game block | ✓ | `checkpoint.py:125 parse_checkpoint_data`, :163 replays `game_file.parse_game_data(make_container('game', ...))` — detector EXACT-match gate inherited at zero new code; `CHECKPOINT_VERSION = 1` refuse-newer at :89. tests/test_checkpoint.py (818 lines) pins every refusal verbatim. |
| reconcile never-ghost-entry | ✓ | `checkpoint.py:199 reconcile_registry` (keep iff object + sorted ids match; non-verifying dropped + reported). Unit-pinned; SMOKE-20 run 2 reconcile asserts PROVEN. |
| Current-level completeness gate | ✓ | Unit-pinned in test_checkpoint.py; SMOKE-20 forced-incomplete scenario covered. |
| Atomic zip write; read refuses before extraction | ✓ | `checkpoint.py:304 write_checkpoint_zip` (temp + os.replace), :336 `read_checkpoint_zip` refusal-first. |

### 07-03 — handler-logged status lines (4/4 truths)

| Must-have | Verdict | Evidence |
| --- | --- | --- |
| `Game saved to <path>.` builder | ✓ | `status_text.py:276` |
| `Game imported: <path>.` builder (after arm) | ✓ | `status_text.py:286`; logged after `start_countdown` at `game_window.py:1031` (D7 law) |
| `Game resumed from <path>.` builder | ✓ | `status_text.py:295`; logged last at `game_window.py:~1069` |
| EVENT_KINDS stays exactly 15; reserved notes byte-unchanged; builders EXCLUDED from `_EVENT_BUILDERS` | ✓ | `status_text.py:74 EVENT_KINDS` (15 keys, test-pinned at test_status_text.py:311); `_EVENT_BUILDERS` at :309 contains only the 5 Phase-6 poll builders — the three Phase-7 builders are absent, as required |

### 07-04 — Save-side seams (4/4 truths)

| Must-have | Verdict | Evidence |
| --- | --- | --- |
| `capture_checkpoint_snapshot` = complete sidecar, scene-read-only | ✓ | `gamestart.py:542`; assembles via pure `checkpoint.build_checkpoint_data` (call at :595). Reads engine module state (sanctioned cmd-tier home). |
| `save_checkpoint` = atomic .aamz, full session, no temp leaks | ✓ | `gamestart.py:784`; FULL-session `cmd.save` to in-process temp, `checkpoint.write_checkpoint_zip` call at :815, unlink in finally. SMOKE-18 recorded PASS. |
| `snapshot_books` plain-data, zero cmd calls | ✓ | `wizard.py:445` |
| Saved zip re-reads through gates; .pse restores wizard in-process | ✓ | SMOKE-18 (recorded): snapshot → atomic zip → member/sidecar/pse verification incl. REAL pickle-path wizard restore. |

### 07-05 — payload-direct + adopt seams (4/4 truths)

| Must-have | Verdict | Evidence |
| --- | --- | --- |
| `start_game_from_payload` materializes the embedded payload, no regeneration | ✓ | `gamestart.py:474`; cleanup → `engine.materialize(payload, 0)` → `engine.adopt_game` (call at :518). SMOKE-08 parity part recorded PASS. |
| `engine.adopt_game` sets all four globals + timer rebase | ✓ | `engine.py:364` (rebase via `rebase_timer` single anchor; live-proven by SMOKE-20 run 2 timer continuation). |
| `_last_start` carries additive `'payload'` (5 keys) | ✓ | `gamestart.py:489` docstring + SMOKE-11 PART-H 5-key pin (recorded); Restart branch consumes it (game_window.py:785). |
| Bundled-fixture load failure raises ValueError family | ✓ | `placement.py:357` `'could not load bundled ligand %r (%s: %s)'` — CmdException wrapped into PlacementError. |

### 07-06 — Game-tab Save (5/5 truths)

| Must-have | Verdict | Evidence |
| --- | --- | --- |
| `btn_save_game` before the stretch; stretch LAST | ✓ | `game_window.py:273-277` (`btn_row.insertWidget(btn_row.count() - 1, ...)`); SMOKE-16 pins row order + stretch-last. |
| Silent no-op gate BEFORE any dialog | ✓ | Wrapper isinstance-gate (07-06 law); SMOKE-16 gate no-op checks recorded. |
| Elapsed captured BEFORE the dialog | ✓ | `_on_save_game` → `_compute_elapsed()` → `_save_game_to(path, elapsed)`; sidecar `elapsed_at_save == N` asserted via SMOKE-16 PART D (recorded). |
| Success feedback = logged line, no box | ✓ | `game_window.py:889` `self._log(status_text.game_saved_line(final))` |
| `.aamz` auto-append + both members on disk | ✓ | SMOKE-18 member assertions + 07-12 step 1 human PASS (`game.aamz` default written). |

### 07-07 — Game-tab Import (game files) (6/6 truths)

| Must-have | Verdict | Evidence |
| --- | --- | --- |
| `btn_import` before the stretch, after Save | ✓ | `game_window.py:283-287` |
| Gate-free import; P-2 cancel → P-3 pop → seam cleanup | ✓ | `game_window.py` `_on_import` (no isinstance gate) → `_import_game_from`; 07-12 step 3 double-import replaced cleanly (`cleaned 20 prior game object(s)`). |
| Materialized from embedded payload, fresh zeros, timer from zero at GO | ✓ | `game_window.py:1025` `gamestart.start_game_from_payload(...)`; countdown then GO (SMOKE-19 E2E + 07-12 step 3). |
| Import line AFTER the arm | ✓ | `game_window.py:1031` (after countdown arm) |
| Restart routes payload-direct | ✓ | `_restart_now` branches on `_last_start['payload']` → `start_game_from_payload` (game_window.py:730/785); SMOKE-19 PART C identity assert (recorded). |
| Eight refusal classes surface verbatim through `_guard` | ✓ | SMOKE-19 refusal battery (recorded 8/8 exact messages); 07-12 step 4 human PASS (clear box, no traceback). |

### 07-08 — Wizard reconstruction ops (3/3 truths)

| Must-have | Verdict | Evidence |
| --- | --- | --- |
| Identity-agnostic predicate (either module identity) | ✓ | `wizard.py:119 is_game_wizard_any_identity` (suffix match on `aamatch.wizard`); used by load_checkpoint pop step (`gamestart.py:722`). |
| `resume_from(books)` applies the sidecar repair block, plain data | ✓ | `wizard.py:471` (normalizes JSON `[[id,color],...]` pairs; zero cmd calls) |
| Books round-trip equality after resume_from | ✓ | SMOKE-07 PART G (recorded 11 checks): snapshot → corrupt-all-six → resume_from → exact equality. |

### 07-09 — load_checkpoint orchestration (5/5 truths)

| Must-have | Verdict | Evidence |
| --- | --- | --- |
| All parse gates BEFORE any scene mutation | ✓ | `gamestart.py:624 load_checkpoint` — refusal-first ordering (docstring §1-4; SMOKE-19/20 refusal classes re-run against it). |
| 9-step sentinel-first order | ✓ | Call sites verified in-body: `checkpoint.reconcile_registry` (:~735 relative), `engine.adopt_game`, `resume_from` + msm repair + `activate(replace=0)`, 5-key `_last_start` rebuild (docstring steps 5-8 match the code). |
| Resumed game equals saved game (poses bit-exact, sidecar state, timer rebased) | ✓ | SMOKE-20 two-run: `VERDICT resume: adopt path books/status/pose/timer/detect/continue-play -> PROVEN`; 07-12 step 2 human PASS (positions AND orientations, scores, counters, timer continuing from saved elapsed). |
| Adopt when pickled, rebuild otherwise | ✓ | SMOKE-20 run 2: `VERDICT resume: forced-rebuild branch (predicate patched False) -> PROVEN` (both branches proven headlessly); registry equality canonicalized via `_canonical_registry` (07-09 Rule-1 fix, in code). |
| Restored engine stays playable | ✓ | SMOKE-20 detect/confirm asserts + 07-12 step 2 (moved an AA and Confirmed). |

### 07-10 — kind-dispatch Import (4/4 truths)

| Must-have | Verdict | Evidence |
| --- | --- | --- |
| Header-exact kind dispatch under one button | ✓ | `game_window.py:962` `kind = persistence.peek_kind(...)` → `'checkpoint'` → `_resume_checkpoint_from` (:964/:1034); else pinned unknown-kind refusal. |
| Filter lists both extensions | ✓ | 07-10 Recorded Decision 3 (filter `'AA-match (*.aamatch.json *.aamz);;All Files (*)'`); SMOKE-16 dispatch drive recorded. |
| Tab re-arm on resume (no countdown, timer from rebased anchor) | ✓ | `_resume_checkpoint_from` → `load_checkpoint` → `_last_status` seed, required label, timer from `_compute_elapsed()`, `game_resumed_line` LAST (:~1069); 07-12 step 2 (info box re-armed). |
| Non-kind/unreadable refuse with clear message | ✓ | `persistence.py:133 peek_kind` — zip-aware (single `*.json` sidecar member; BadZipFile → `'not an AA-match archive (unreadable zip: %s)'`); pinned messages shared with load path; tests/test_persistence.py covers game/checkpoint/foreign/unparseable/REAL .aamz/missing-member. |

### 07-11 — regression battery (4/4 truths)

| Must-have | Verdict | Evidence |
| --- | --- | --- |
| Full WSL suite green on merged tree | ✓ | Recorded 890/890 (07-11-SUMMARY task table); re-run today: 906/906 OK on the current tree (Phase-8 additions only). |
| Every smoke 01-20 PASS (17 & 20 two-run) | ✓ | 07-11-SUMMARY verdict table: 20/20, both two-run contracts passed both runs. |
| Matrix round-trip verdict recorded | ✓ | 07-11-SUMMARY: `matrix_max_delta=0.000e+00`, coords/view `exact=True` — matrices survive `.pse` bit-exactly; sidecar needs none. |
| Criterion coverage identified and passing | ✓ | 07-11-SUMMARY coverage map: criteria 1 (HEADLESS half), 2 (refusal battery), 3 (GATE mechanics) — all PASS. |

### 07-12 — [HUMAN] consolidated checkpoint (4/4 truths)

| Must-have | Verdict | Evidence |
| --- | --- | --- |
| Save via Game tab writes a real `.aamz`; game keeps running | ✓ | 07-12-SUMMARY step 1 PASS (human, 2026-09-22) |
| save → quit → relaunch → load restores positions/orientations, scores, counters, timer continues | ✓ | 07-12-SUMMARY step 2 PASS (installed identity, zero Session-Warning, pick echo proves live slot objects) |
| Import loads exported game; stale/foreign refused with clear boxes | ✓ | 07-12-SUMMARY steps 3/4 PASS |
| [GATE] console clean, plugin reload, installed-identity pickle round-trip | ✓ | 07-12-SUMMARY steps 5/6 PASS — criterion 3 CLOSED, the [UNVERIFIED] item carried since 07-01 is CLOSED |

## ROADMAP Success-Criteria Coverage

| # | Criterion | Mechanical half | Human half | Verdict |
| --- | --- | --- | --- | --- |
| 1 | Save writes zipped `.pse` + sidecar; save→quit→relaunch→load restores positions/orientations, scores, counters, timer; matrix verdict recorded | SMOKE-18 + SMOKE-20 two-run + SMOKE-17 two-run (matrix verdict `0.000e+00` recorded) | 07-12 steps 1+2 PASS | **MET** |
| 2 | Game-tab Import loads exported games; stale/foreign refused clearly | SMOKE-19 eight-class refusal battery + SMOKE-16 kind-dispatch | 07-12 steps 3+4 PASS | **MET** |
| 3 | [GATE] Session-restore hygiene: wizard pickles cleanly, sentinel-first reconcile, restore after plugin reload, console clean | SMOKE-17 strict restore + SMOKE-20 reconcile/adopt + purity gates | 07-12 steps 5+6 PASS — **GATE CLOSED** (installed-identity round-trip exercised) | **MET** |

## Requirements Coverage

| Requirement | Status | Evidence |
| --- | --- | --- |
| SCORE-08 (Save button checkpoints the game) | ✓ SATISFIED | SMOKE-16 save part + SMOKE-18; 07-12 steps 1-2 |
| PERSIST-02 (Import exported games; refusals) | ✓ SATISFIED | SMOKE-19 + SMOKE-16; 07-12 steps 3-4 |
| PERSIST-03 (checkpoint save/restore full reconstruction) | ✓ SATISFIED | SMOKE-20 two-process E2E; 07-12 steps 2+5; [GATE] closed |

## Key Link Verification (wiring summary)

| From | To | Via | Status |
| --- | --- | --- | --- |
| `game_window._save_game_to` | `gamestart.capture_checkpoint_snapshot` / `save_checkpoint` | direct calls (game_window.py:907-908) | WIRED |
| `gamestart.save_checkpoint` | `checkpoint.write_checkpoint_zip` | call at gamestart.py:815 | WIRED |
| `gamestart.capture_checkpoint_snapshot` | `checkpoint.build_checkpoint_data` | call at gamestart.py:595 | WIRED |
| `checkpoint.parse_checkpoint_data` | `game_file.parse_game_data` | embedded-block replay at checkpoint.py:163 | WIRED |
| `game_window._on_import` | `persistence.peek_kind` | dispatch at game_window.py:962 | WIRED |
| `game_window._import_game_from` | `gamestart.start_game_from_payload` | call at game_window.py:1025 | WIRED |
| `game_window._restart_now` | payload-direct branch | `_last_start['payload']` at game_window.py:785 | WIRED |
| `game_window._resume_checkpoint_from` | `gamestart.load_checkpoint` | call in impl (:1034+) | WIRED |
| `gamestart.load_checkpoint` | `checkpoint.reconcile_registry` + `engine.adopt_game` + `wizard.resume_from` | in-body call sites (gamestart.py:722+, :660-780) | WIRED |
| `wizard.__reduce__` | `_rebuild_game_wizard` (pickle path) | wizard.py:208 | WIRED |
| Save/Import/Resume wrappers | `status_text.*_line` builders | game_window.py:889, :1031, :~1069 | WIRED |
| Qt tier | engine/wizard privates | grep law: 0 hits for `engine._game`/`engine._payload` in game_window.py | HELD |

## Anti-Patterns Found

None blocking. No TODO/FIXME/placeholder/stub patterns in any Phase-7 production file. The single grep hit (game_window.py:1065) is prose stating the timer must NOT show a placeholder.

## Human Verification Required

None outstanding. All [HUMAN] halves were verified by a real GUI checkpoint (07-12, human verdict 2026-09-22, APPROVED 6/6) on Windows PyMOL 2.5.0 under the installed plugin identity — dialog feel, relaunch restore, timer continuation, refusal message boxes, console cleanliness, plugin reload. Standing note (recorded, NOT a defect): the bare-`.pse`-at-Import refusal wording names the JSON parse failure rather than the archive expectation; human approved as-is, deferred as an OPTIONAL Phase-9 polish note.

## Gaps Summary

None. All 51 must-have truths across the 12 plans verify against the code and recorded verdicts; all key links are wired; the full test suite re-runs green today (906/906); all three ROADMAP criteria carry both mechanical and human coverage.

---

_Verified: 2026-09-26_
_Verifier: OpenCode (gsd-verifier)_
