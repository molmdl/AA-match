---
phase: 07-checkpoint-game-file-persistence
plan: 12
type: execute-checkpoint-record
subsystem: persistence/verification
tags: [pymol, checkpoint, persistence, pse, aamz, import, human-checkpoint, verdicts, session-restore]

# Dependency graph
requires:
  - phase: 07-checkpoint-game-file-persistence
    provides: plans 07-01..07-11 (wizard argless __reduce__ rebuilder, checkpoint.py pure schema/parse/reconcile/zip-I/O, handler-logged status lines, snapshot_books/capture_checkpoint_snapshot/save_checkpoint save seams, engine.adopt_game + start_game_from_payload, Game-tab Save + Import buttons with kind-dispatch, wizard identity predicate + resume_from, load_checkpoint 9-step sentinel-first orchestration, full regression battery with matrix verdict + criterion coverage map)
provides:
  - ROADMAP Phase-7 criterion 1 (SCORE-08/PERSIST-03 save -> quit -> relaunch -> load round-trip) [HUMAN] verdict recorded: PASS
  - ROADMAP Phase-7 criterion 2 (PERSIST-02 Import button loads exported game; stale/foreign refused) [HUMAN] verdict recorded: PASS
  - ROADMAP Phase-7 criterion 3 (PERSIST-03 [GATE] session-restore hygiene: wizard pickles cleanly, sentinel-first reconciliation, restore after plugin reload, console clean) [GATE] verdict recorded: PASS — CLOSED
  - Installed-identity (pmg_tk.startup.aamatch) pickle round-trip exercised in-session — the [UNVERIFIED] item carried since 07-01 is CLOSED
affects: [phase verifier (Phase 7 ready), phase-9 (help/docs inherit the recorded refusal wordings; optional bare-.pse polish note)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Checkpoint record-only pattern (04-14 precedent): a docs-only plan whose single artifact is the human verdict table — code tree untouched, py_compile sanity check only, full battery NOT re-run because the tree is byte-identical to the 07-11-verified tree"
    - "Conditional fix-batch candidate protocol: pre-authorized wording refinements fire ONLY if a fix-batch is open anyway; an approved-as-is checkpoint demotes the candidate to an optional later-phase polish note (recorded, NOT a defect)"

key-files:
  created:
    - ".planning/phases/07-checkpoint-game-file-persistence/07-12-SUMMARY.md"
  modified: []

key-decisions:
  - "07-12 checkpoint APPROVED (human, 2026-09-22) — ALL 6 steps PASS, zero fix-batch items; ROADMAP Phase-7 criteria 1 ([HUMAN] half), 2, and 3 ([GATE]) all carry recorded human verdicts"
  - "Criterion 3 [GATE] CLOSED: wizard pickles cleanly + sentinel-first reconciliation + restore-after-reload + installed-identity (pmg_tk.startup.aamatch) pickle round-trip all exercised — zero 'Session-Warning: unable to restore wizard.' lines anywhere"
  - "Bare-.pse-at-Import refusal wording: human approved as-is; the pre-authorized archive-expectation wording refinement is demoted to an optional Phase-9 polish note (NOT a defect, no fix-batch)"

patterns-established:
  - "Console-evidence recording: verbatim status echoes from the human session are stored in the SUMMARY so the phase verifier can audit console cleanliness without re-running the GUI (session-2 'from embedded payload' + 'cleaned 20 prior game object(s)' lines double as the clean-scene-replacement and payload-direct-law proofs)"

# Metrics
duration: ~5 min (docs-only verdict record; the human checkpoint sessions themselves ran outside agent execution)
completed: 2026-09-22
---

# Phase 7 Plan 12: Consolidated GUI Checkpoint — Save/Resume/Import Human Verdicts Summary

**07-12 checkpoint APPROVED (human, 2026-09-22) — ALL 6 STEPS PASS, zero fix-batch items.** On real Windows PyMOL 2.5.0 (setenv.bat, 01-09 plugin-path install): the Game-tab Save dialog opened with the `game.aamz` default and checkpoint filter, wrote a real `.aamz`, logged `Game saved to <path>.`, and the game kept running; save → quit → relaunch → load restored placed positions AND orientations, scores, counters, and a timer continuing from approximately the saved elapsed — with **zero `Session-Warning: unable to restore wizard.` lines anywhere**; Import loaded an exported game through the countdown with a fresh timer and the after-the-arm `Game imported:` line; foreign files were refused with a clear message box (no traceback); double-import mid-session replaced cleanly (`cleaned 20 prior game object(s)`); both consoles carried ONLY the recorded 04-14 stock-baseline warnings. The relaunch+load half exercised the installed-identity (`pmg_tk.startup.aamatch`) pickle round-trip, closing the [UNVERIFIED] item carried since 07-01 — criterion 3 [GATE] is **CLOSED**, and PERSIST-02/03 + SCORE-08 are human-verified end to end.

## Performance

- **Duration:** verdict recording (~5 min, docs-only); the human checkpoint sessions ran outside agent execution
- **Completed:** 2026-09-22
- **Tasks:** 1 blocking `checkpoint:human-verify` (APPROVED — all 6 steps PASS) + Task 2 (this record)
- **Sanity:** `python3.6 -m py_compile aamatch/*.py` green; full battery NOT re-run — the tree is byte-identical to the 07-11-verified tree (be8009b), zero code changes since

## Environment (recorded for the record)

- **PyMOL:** PyMOL(TM) 2.5.0 (Windows, via the recorded setenv.bat conda environment); two real GUI sessions
- **Install method:** 01-09 plugin-path method — repo root on the PyMOL plugin path, running as the installed identity `pmg_tk.startup.aamatch` (no copy-install)
- **Console triage baseline (04-14 recorded):** stock plugin-init warnings (findseq, aKMT_Lys_pred, cb_colors/colorblindfriendly, wfmesh, bnitools, mtsslPlotter, mtsslTrilaterate, SuperSymPlugin, phase9_ssl_probe) plus OpenGL/CPU init lines — pre-existing and UNRELATED to AA-match; only NEW AA-match tracebacks/prints would be defects.

## Checkpoint Verdict: APPROVED (human, 2026-09-22) — 6/6 steps PASS, zero fix-batch items

| Step | Requirement / ROADMAP criterion | Verdict | Notes |
| ---- | ------------------------------- | ------- | ----- |
| 1 | SCORE-08 save flow (criterion 1, part 1) | PASS | Game tab → Save opened the dialog with default name `game.aamz` + filter 'AA-match Checkpoint (*.aamz)'; the `.aamz` was written to the user's folder; the info box logged `Game saved to <path>.`; NO success popup (per the 07-06 law); the game kept running (timer still ticking, wizard still active); console clean. |
| 2 | PERSIST-03 restore: save → quit → relaunch → load (criterion 1, part 2) | PASS | Full PyMOL quit, relaunch via setenv.bat, Import of the saved `.aamz`: the scene reappeared exactly (placed positions AND orientations — session 2's real-mouse pick echo `You clicked /_aam_aa14/AAM//TRP`2/CZ2` after resume proves the restored slot objects are live and pickable); the info box re-armed (resumed line + level/required lines); the timer CONTINUED from approximately the saved elapsed (not zero, not the wall-clock gap — the 07-05 `rebase_timer` single-anchor doctrine); scores/counters matched via the wizard panel; play-on worked (moved an AA and Confirmed — scoring continued); **zero `Session-Warning: unable to restore wizard.` lines**; console clean throughout the load. |
| 3 | PERSIST-02 Import of an exported game (criterion 2, part 1) | PASS | Setup tab generated + exported a game (`.aamatch.json`); Game tab → Import picked it: countdown 3-2-1 → GO, fresh timer from zero, fresh scores, `Game imported: <path>.` logged AFTER the countdown armed (the 07-03 D7 after-the-arm law). The start echo `...game started from embedded payload -- 2 molecule(s), 18 amino-acid slot(s), seed 1291141194 (cleaned 20 prior game object(s)).` is the EXPECTED 07-07 c2 law (payload-direct; a mid-session Import/restart discards the running game exactly like Start) — the `cleaned 20 prior game object(s)` count is the clean-scene-replacement evidence, NOT noise. |
| 4 | PERSIST-02 refusals: stale/foreign files (criterion 2, part 2) | PASS | A random non-AA-match file (incl. a bare `.pse`) was refused with a clear message box — NO traceback (fail-closed per 07-09 Decision 4 + the 07-10 pinned peek/import messages). The plan's conditional wording refinement (bare-`.pse` JSON-parse wording could name the archive expectation, e.g. 'expected an AA-match archive (.aamz) or AA-match JSON container') was a pre-authorized fix-batch CANDIDATE ONLY if a batch opened anyway — the human approved as-is, so NO fix-batch opened and the candidate is demoted to an OPTIONAL Phase-9 polish note (recorded below, NOT a defect). |
| 5 | Criterion 3 [GATE]: plugin reload + installed identity | PASS | The entire session ran under the 01-09 plugin-path INSTALLED identity (`pmg_tk.startup.aamatch`) — so the step-2 save → quit → relaunch → load flow exercised the installed-identity pickle round-trip end to end: the wizard restored with byte-equal books and zero Session-Warning anywhere. **The [UNVERIFIED] item carried since 07-01 (installed-identity round-trip inferred-safe) is CLOSED.** |
| 6 | Console + robustness sweep | PASS | Both sessions' consoles carry ONLY the recorded 04-14 stock-baseline plugin-init warnings plus OpenGL/CPU init lines; zero AA-match tracebacks; zero stray AA-match prints beyond the recorded status echoes. Double-import / mid-session replacement is clean (old game discarded like Start — `cleaned 20 prior game object(s)`). |

**Overall verdict: APPROVED (human, 2026-09-22, verbatim intent "approve all, see log above") — ALL 6 STEPS PASS; zero fix-batch items; criterion 3 [GATE] CLOSED.**

## Console Evidence (verbatim, as supplied by the human)

**Session 1 (fresh game):**

```
AA-match 0.1.0: game started -- 2 molecule(s), 18 amino-acid slot(s), seed 1384048103 (        cleaned 0 prior game object(s)).
You clicked /_aam_aa01/AAM//PHE`2/CE1
Selector: selection "sele" defined with 1 atoms.
```

Clean start (0 prior game objects on a fresh session); real-mouse pick routed to a game AA — no tracebacks.

**Session 2 (after save → quit → relaunch → load):**

```
AA-match 0.1.0: game started from embedded payload -- 2 molecule(s), 18 amino-acid slot(s), seed 1291141194 (cleaned 20 prior game object(s)).
You clicked /_aam_aa14/AAM//TRP`2/CZ2
```

The `from embedded payload` line is the EXPECTED 07-07 c2 law (payload-direct start — the embedded level_spec is THE TRUTH, never regenerated), the `cleaned 20 prior game object(s)` count is the clean-scene-replacement evidence, the pick echo proves the restored/resumed slot objects are live under the wizard, and there are **zero `Session-Warning: unable to restore wizard.` lines anywhere** in either session.

## [GATE] Closure — ROADMAP Phase-7 criterion 3

The [GATE] criterion 3 is **CLOSED** with BOTH halves carried:

- **Wizard pickles cleanly (no Qt/locks/controller on it):** mechanical half = SMOKE-17 run 1 `pickle.dumps ok=True` + run 2 strict restore compare PROVEN (07-11); human half = this session's save → quit → relaunch → load with zero Session-Warning.
- **Sentinel-first reconstruction reconciles sidecar vs loaded atoms:** mechanical half = SMOKE-20 run 2 reconcile/adopt asserts PROVEN (07-11, the 07-09 9-step order with the `gamestart._canonical_registry` fix); human half = the step-2 restore showing exact positions/orientations with live pickable slots.
- **Restore works after a plugin reload:** mechanical half = SMOKE-17 two-process strict compare; human half = this session itself, which ran under the fresh relaunch's plugin load.
- **Installed identity:** the whole session ran as `pmg_tk.startup.aamatch` (01-09 plugin-path install) — the pickle round-trip under the installed identity is now EXERCISED, closing the [UNVERIFIED] item carried since 07-01 (`inferred-safe` → **verified**).
- **Console clean during save/load:** step 6 PASS (04-14 baseline only).

## Optional Phase-9 Polish Note (NOT a defect — recorded for the docs-audit phase)

- **Bare-.pse-at-Import refusal wording:** a bare `.pse` at Import currently fails at the JSON parse with 'could not parse AA-match JSON' (fail-closed per 07-09 Decision 4 — correct behavior, human-approved wording). If Phase 9 ever touches the refusal strings for docs alignment, consider naming the archive expectation explicitly, e.g. 'expected an AA-match archive (.aamz) or AA-match JSON container'. Deferred as OPTIONAL; no fix-batch opened.

## Requirement Coverage (final — mechanical + human halves)

- **SCORE-08 (Save button checkpoints the game):** mechanical = SMOKE-16 save part + SMOKE-18 (07-04/07-06); human = step 1 PASS + step 2 PASS — **COMPLETE.**
- **PERSIST-03 (checkpoint save/restore fully reconstructs: positions/orientations, scores, counters):** mechanical = SMOKE-20 two-process E2E (07-09/07-11); human = step 2 PASS + step 5 PASS (plus criterion 3 [GATE] closed) — **COMPLETE.**
- **PERSIST-02 (Import loads an exported game; stale/foreign refused):** mechanical = SMOKE-19 eight-class refusal battery + SMOKE-16 kind-dispatch (07-07/07-10); human = step 3 PASS + step 4 PASS — **COMPLETE.**

All three ROADMAP Phase-7 criteria now carry BOTH mechanical (07-11 battery: 890/890 WSL, 20/20 smokes) and [HUMAN] verdict coverage.

## Task Commits

- **Task 1 (checkpoint:human-verify):** human GUI sessions — no code commit (checkpoint artifact is this SUMMARY)
- **Task 2 (record verdicts):** this SUMMARY + STATE.md + ROADMAP.md tick — land in the plan metadata commit (see git log)

## Files Created/Modified

- `.planning/phases/07-checkpoint-game-file-persistence/07-12-SUMMARY.md` — this verdict record (created)
- No code files touched (record-only plan)

## Decisions Made

- **Checkpoint APPROVED as-is (human, 2026-09-22):** the bare-.pse refusal wording candidate was pre-authorized only inside an open fix-batch; with an approved-all verdict NO batch opened, and the candidate is demoted to an optional Phase-9 polish note (see above).
- **Installed-identity installed-round-trip is CLOSED:** the 01-09 plugin-path session IS the installed identity `pmg_tk.startup.aamatch`; the relaunch+load flow exercised the pickle round-trip end to end with zero Session-Warning — the 07-01 gate blocker candidate (`[UNVERIFIED]: installed-identity round-trip — inferred-safe`) is removed from Blockers/Concerns Carried Forward.
- **Session-2 embedded-payload echo recorded as EXPECTED:** `game started from embedded payload` + `(cleaned 20 prior game object(s))` constitute the 07-07 c2 law in action (payload-direct mid-session replacement) and double as the clean-scene-replacement proof — future checkpoint readers must not flag these lines as findings.

## Deviations from Plan

None — plan executed exactly as written: the human approved all six steps, so Task 2 recorded verdicts only (no fix-batch branch was entered).

## Issues Encountered

None.

## Authentication Gates

None.

## Next Phase Readiness

- **Phase 7 execution is COMPLETE (12/12 plans):** all three ROADMAP criteria carry mechanical + human verdict coverage; **ready for `/gsd-verify-phase` on Phase 7.** The phase verifier can rely on: 890/890 WSL + 20/20 smokes (07-11), the matrix verdict (07-11), this APPROVED verdict table, the [GATE] closure section, and the verbatim console evidence.
- REQUIREMENTS.md traceability flips (PERSIST-02, PERSIST-03, SCORE-08 → Complete) belong to the phase close-out/verification step, per the Phase-5/6 precedent.
- Phase 8 continues independently (08-04 [GATE] approval pending); the optional bare-.pse wording polish note rides Phase 9.

---
*Phase: 07-checkpoint-game-file-persistence*
*Completed: 2026-09-22*
