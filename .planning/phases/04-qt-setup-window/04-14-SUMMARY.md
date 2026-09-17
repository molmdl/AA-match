---
phase: 04-qt-setup-window
plan: 14
type: execute-checkpoint-record
subsystem: human-checkpoint
tags: [pymol, qt, setup-window, human-checkpoint, modeless, setup-form, setup-file-round-trip, verdicts]

# Dependency graph
requires:
  - phase: 04-qt-setup-window
    provides: plans 04-01..04-13 (offscreen-Qt probe verdict, setup_form pure layer, upload pipe, Qt window shell + full 7-field form + all 7 spec-order buttons wired, SMOKE-11/12 headless proofs)
provides:
  - ROADMAP Phase-4 criteria 1-3 [HUMAN] verdicts recorded as APPROVED: SETUP-01 modelessness + window lifecycle, SETUP-02..06 form configuration, SETUP-07 Reset/Randomize/Save/Load round-trip (12/12 steps PASS)
  - Step-7 expected-behavior ruling recorded: Reset restores the demo dropdown selection while the source radio stays on the demo page = apply_state(deep-copied DEFAULTS) — the frozen-defaults contract, not a defect
  - Stock-PyMOL plugin-init warnings baseline recorded as unrelated to AA-match (pre-existing, no AA-match traceback)
affects: [04-15 checkpoint B (ROADMAP criterion 4), phase-4 verifier, phase-5 status tab, phase-7 persistence]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Human checkpoint -> per-step verdict table in the plan's SUMMARY + verdict section in STATE.md -> gate closure (third instance: 03-06, 03-07, now 04-14)"
    - "Plugin-path install method (01-09) keeps repo edits live for the human checkpoint session — no copy-install drift"

key-files:
  created:
    - ".planning/phases/04-qt-setup-window/04-14-SUMMARY.md"
  modified:
    - ".planning/STATE.md"

key-decisions:
  - "04-14 checkpoint A APPROVED (human, 2026-09-18): ROADMAP Phase-4 criteria 1-3 (SETUP-01..07) all PASS, 12/12 steps, zero fix-batch items"
  - "Step-7 verdict ruled EXPECTED BEHAVIOR: Reset restores the demo dropdown selection while the source radio stays on the demo page — setup_state.DEFAULTS carry source_mode='demo' + demo_set_id='demo-dev-1', so apply_state(deep-copied DEFAULTS) reproducing both IS the frozen-defaults contract"

patterns-established:
  - "Stock-plugin warnings triage: any console noise at launch is attributed against a recorded stock-PyMOL plugin-init failure list; AA-match cleanliness is judged only by the presence/absence of AA-match tracebacks or stray prints"

# Metrics
duration: ~5 min (documentation only; the human checkpoint session itself ran outside agent execution)
completed: 2026-09-18
---

# Phase 4 Plan 14: Checkpoint A — SETUP-01..07 Human Verdicts Summary

**04-14 checkpoint A APPROVED (human, 2026-09-18): all 12 verification steps PASS on a real Windows PyMOL 2.5.0 session — ROADMAP Phase-4 criteria 1-3 (modeless window lifecycle, form configuration, setup-file round-trip) are human-green with zero fix-batch items; the one flagged observation (step 7) was ruled expected behavior under the frozen-defaults contract.**

## Performance

- **Duration:** documentation-only continuation (verdict recording + STATE.md update); no code written (`files_modified: []` in the plan)
- **Completed:** 2026-09-18
- **Tasks:** 1 blocking `checkpoint:human-verify` — resolved APPROVED

## Environment (recorded for the record)

- **PyMOL:** PyMOL(TM) 2.5.0 (Windows, via the recorded setenv.bat conda environment)
- **OpenGL:** 4.6 (Intel Iris Plus Graphics, GLSL 4.60); 8 CPU cores multithreaded rendering
- **Install method:** 01-09 plugin-path method — repo root on the PyMOL plugin path, no copy-install (repo edits live for the checkpoint session)
- **GUI platform:** the only tier that can prove modeless interactivity (per the plan's key_links); everything machine-provable was already proven at T0/T1a/T1b (688 WSL tests green, SMOKE-01..12 PASS)

## Checkpoint Verdict: APPROVED (human, 2026-09-18) — 12/12 PASS

| Step | Requirement / ROADMAP criterion | Verdict | Notes |
|------|--------------------------------|---------|-------|
| 1 | SETUP-01 / criterion 1 (modeless open) | PASS | Window opens; the 3D viewer stays fully interactive (rotate/zoom) while the window is open; nothing blocked |
| 2 | SETUP-01 / criterion 1 (minimize/re-open) | PASS | The SAME window returns raised to front — not duplicated (singleton reuse-and-raise, SMOKE-11's mechanical teeth hold live) |
| 3 | SETUP-01 / criterion 1 (double menu fire) | PASS | One window, raised — never two instances |
| 4 | SETUP-02 / criterion 2 (demo dropdown) | PASS | Lists the Phase-2 development set; no crash, no console error |
| 5 | SETUP-04/05 / criterion 2 (spinboxes) | PASS | Typed 10 then spun down; values clamp at the 1..10 edges, never silently change after the fact |
| 6 | SETUP-06 / criterion 2 (mode + context label) | PASS | Block-exclusive label wording EXACT; checkboxes stay ENABLED in unset mode with the random wording (checked set = sampling vocabulary) |
| 7 | SETUP-07 / criterion 3 (Reset) | PASS | Human note (verbatim): "demo dropdown reset but source remains demo, if its what u mean" — ruled EXPECTED BEHAVIOR (see below) |
| 8 | SETUP-07 / criterion 3 (Randomize) | PASS | 3 presses changed mode/allowed/numbers; demo dropdown selection preserved (Decision 5); configuration always valid |
| 9 | SETUP-07 / criterion 3 (Save/Load) | PASS | `.aam.setup.json` extension auto-appended when omitted (Decision 2); reset-then-load returned the form exactly to the saved values; console clean |
| 10 | SETUP-03 form side / criterion 2 (upload widget) | PASS | Native file dialog filtered to SDF/MOL2; cancelled cleanly (full ingestion is checkpoint B step 5) |
| 11 | Tooltips (spec UI standard) | PASS | Clear one-line explanations on 5+ widgets (mode radios, spinboxes, checkboxes) |
| 12 | Console cleanliness | PASS | No tracebacks, no stray prints from AA-match throughout the session |

## Step-7 Expected-Behavior Ruling

The human flagged: *"demo dropdown reset but source remains demo, if its what u mean"*.

**Ruling: EXPECTED BEHAVIOR, not a defect — no fix needed.** `setup_state.DEFAULTS` carry `source_mode='demo'` + `demo_set_id='demo-dev-1'`. Reset is `apply_state(copy.deepcopy(setup_state.DEFAULTS))` (04-09, never aliasing the module dict), so the dropdown returning to the `demo-dev-1` selection **while the source radio stays on the demo page** is exactly the frozen-defaults contract. The plan's step-7 expectation ("demo page active") is what was observed; the radio could only leave the demo page if DEFAULTS said otherwise, which they do not.

## Stock-PyMOL Plugin Warnings (unrelated to AA-match)

Launch-session plugin-init warnings appeared from STOCK PyMOL plugins and are pre-existing on this build — **no AA-match traceback involved anywhere**:

- `findseq`, `aKMT_Lys_pred`, `colorblindfriendly`, `wfmesh` (No module 'OpenGL')
- `bnitools` ("module 'base64' has no attribute 'encodestring'")
- `mtsslPlotter` (use() warn kwarg), `mtsslTrilaterate` (No module 'wx')
- `SuperSymPlugin` (No module 'cctbx'), `phase9_ssl_probe` (No module 'biochemeleon')

Console-cleanliness step 12 was judged only on AA-match output: none observed.

## Task Commits

The checkpoint produced no production-code commits (plan `files_modified: []`):

1. **Finalization (docs):** this summary + STATE.md updates — commit follows this file

**Plan metadata:** `docs(04-14): checkpoint A APPROVED — SETUP-01..07 human verdicts (12/12 PASS)`

## Files Created/Modified

- `.planning/phases/04-qt-setup-window/04-14-SUMMARY.md` — this summary (records ROADMAP Phase-4 criteria 1-3 [HUMAN] verdicts)
- `.planning/STATE.md` — position 14/15, 04-14 verdict section, session continuity → next: 04-15 checkpoint B

## Decisions Made

- **04-14 checkpoint A APPROVED:** ROADMAP Phase-4 criteria 1-3 (SETUP-01..07) human-verified PASS, 12/12 steps. Criteria 1-3 are now satisfied; criterion 4 (SETUP-08/09/10 + upload E2E + extension confirms) stays pending for checkpoint B (04-15).
- **Step-7 observation ruled expected behavior:** Reset restoring the demo dropdown selection with the source radio on the demo page IS `apply_state(deep-copied DEFAULTS)` — the frozen-defaults contract from 01-09/04-09. Recorded as a ruling so 04-15 and any future UAT do not re-flag it.

## Deviations from Plan

None — plan executed exactly as written (checkpoint presented; verdict recorded; no fix-batch triggered).

## Authentication Gates

None.

## Fix-Batch Items

**None.** 12/12 PASS on first presentation; no re-test needed.

## Next-Phase Readiness

- **04-15 checkpoint B (wave 9, blocking [HUMAN]) is UNBLOCKED**: ROADMAP Phase-4 criterion 4 — Generate-and-export writes a shareable versioned game file; Cleanup removes only game objects and restores the scene; Start drops the player into playable wizard gameplay — plus upload E2E (full ingestion, this checkpoint's step-10 cancel deferred it) and extension confirms.
- Everything checkpoint B verifies is already wired and headless-proven (SMOKE-11 PART F/F2 round-trip, PART E exact-scene restore, PART G real-start drive + seeded-replay; SMOKE-12 upload E2E).
