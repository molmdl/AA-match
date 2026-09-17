---
phase: 04-qt-setup-window
plan: 15
type: execute-checkpoint-record
subsystem: human-checkpoint
tags: [pymol, qt, setup-window, human-checkpoint, export, cleanup, start, upload-e2e, verdicts, fix-batch]

# Dependency graph
requires:
  - phase: 04-qt-setup-window
    provides: plans 04-01..04-14 (all 7 spec-order buttons wired and headless-proven; checkpoint A APPROVED — ROADMAP criteria 1-3 human-verified)
provides:
  - ROADMAP Phase-4 criterion 4 [HUMAN] verdict recorded as APPROVED-WITH-FIX: SETUP-08 export (seed + counts in message, viewer untouched, kind 'game'/version 1/det-1 on disk), SETUP-09 cleanup (0-count + mid-game exact-restore + wizard pop), SETUP-10 start + gameplay through the window, Start-after-Generate seed replay (Decision 4), robustness (double-Start, no freeze)
  - SETUP-03 upload E2E [HUMAN] verdict PASS-AFTER-FIX: benzamide.sdf ingested, game built + playable (seed 888026772, 1 molecule/9 slots); the single fix-batch item (upload path label readability) applied and headlessly re-green
  - Decision 2 ('.aam.setup.json') and Decision 3 ('.aamatch.json', default name 'game.aamatch.json') human-confirmed — both extension decisions CLOSED
  - Score-surface clarification recorded for Phase-5 planning: the wizard panel is the Phase-4 feedback surface; the Qt Game status tab/timer/Hint are SETUP-11 = Phase 5 scope
affects: [phase verifier, phase-5 status tab (SETUP-11 scope owns the Qt feedback surface), phase-7 persistence]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Checkpoint fix-batch pattern: human FAIL on a cosmetic item -> prescribed fix applied as its own fix() commit -> full WSL suite + SMOKE-11 re-green -> verdict recorded PASS-AFTER-FIX (third fix-batch instance; 03-06 and 03-07 precedents)"
    - "Two-line QLabel: '%s\\n(%d ...)' embedded newline renders natively and grows the label vertically — long paths no longer clip the record count; tooltip keeps the full path"

key-files:
  created:
    - ".planning/phases/04-qt-setup-window/04-15-SUMMARY.md"
  modified:
    - "aamatch/setup_window.py"
    - ".planning/STATE.md"

key-decisions:
  - "04-15 checkpoint B APPROVED (human, 2026-09-18) with 1 cosmetic fix-batch item (upload path label), resolved: two-line label '%s\\n(%d molecule record(s))' is the new format; the tooltip keeps the full path"
  - "Score-surface clarification (human, 2026-09-18): score/moves feedback lives in the wizard panel for Phase 4 — by design; the Qt Game status tab + timer + Hint are SETUP-11 = Phase 5 scope (inherit into Phase-5 planning)"
  - "Extensions human-confirmed (Decisions 2/3 CLOSED): '.aam.setup.json' for setup files; '.aamatch.json' with default name 'game.aamatch.json' for game exports"

patterns-established:
  - "Grep-free label hygiene: no smoke assert was ever pinned to the upload label text (PART D treated it as cosmetic), so a label-format change touched exactly one production line + its docstring — zero smoke churn"

# Metrics
duration: ~15 min (fix + re-verify + documentation; the human checkpoint session itself ran outside agent execution)
completed: 2026-09-18
---

# Phase 4 Plan 15: Checkpoint B — Criterion 4 + Upload E2E + Extension Confirms Summary

**04-15 checkpoint B APPROVED (human, 2026-09-18) with 1 cosmetic fix-batch item: all 8 verification steps PASS on a real Windows PyMOL 2.5.0 session (SETUP-08 export, SETUP-09 cleanup ×2, SETUP-10 start + gameplay, Start-after-Generate seed replay, robustness) — the upload E2E flowed end-to-end and is recorded PASS-AFTER-FIX after the prescribed two-line upload-label fix (commit 27e8f34); both extension confirms (Decisions 2/3) are human-approved and CLOSED. ROADMAP Phase-4 criterion 4 has its verdict; Phase 4 ready for the phase verifier.**

## Performance

- **Duration:** fix + re-verify + verdict recording (~15 min); one production-code line + docstring
- **Completed:** 2026-09-18
- **Tasks:** 1 blocking `checkpoint:human-verify` — resolved APPROVED-WITH-FIX (fix-batch of one, resolved in-session)
- **Verification after fix:** `python3.6 -m py_compile` green; 688/688 WSL tests green; `=== SMOKE-11 PASS ===` (PART D green — no label-text assert existed to update)

## Environment (recorded for the record)

- **PyMOL:** PyMOL(TM) 2.5.0 (Windows, via the recorded setenv.bat conda environment)
- **Install method:** 01-09 plugin-path method — repo root on the PyMOL plugin path, no copy-install (live repo copy)
- **Session stdout seeds:** 1344424189 (2 molecules/18 slots, start), 888026772 (1 molecule/9 slots — the upload E2E game), 829433251 (restart)
- **Clicks registered:** `_aam_aa06/SER/CB`, `_aam_aa04/GLU/CD`, `_aam_lig01/UNK/C`, `_aam_aa03/ASN/CA` (picking live through the window)

## Checkpoint Verdict: APPROVED-WITH-FIX (human, 2026-09-18) — 8/8 PASS (step 5 PASS-AFTER-FIX)

| Step | Requirement / ROADMAP criterion | Verdict | Notes |
|------|--------------------------------|---------|-------|
| 1 | SETUP-08 / criterion 4 (generate + export demo) | PASS | `.aamatch.json` written; success message shows the seed + counts; viewer unchanged (no new objects, no wizard); on-disk JSON: kind 'game', header version 1, detector_version 'det-1' |
| 2 | SETUP-09 / criterion 4 (cleanup, no game) | PASS | 'Removed 0 game object(s)'; user objects untouched |
| 3 | SETUP-10 / criterion 4 (start + gameplay) | PASS | Game starts while the setup window STAYS OPEN; clicks/moves/score in the wizard panel confirmed live |
| 4 | SETUP-09 / criterion 4 (cleanup mid-game) | PASS | Game objects gone, GameWizard popped, count reported, user objects intact, console clean |
| 5 | SETUP-03 / criterion 4 (upload E2E) | **PASS-AFTER-FIX** | Flow WORKED: benzamide.sdf ingested and a playable game built (seed 888026772, 1 molecule/9 slots) — only the CRAMPED label failed: long path + ' (N molecule record(s))' on one line clipped the count to '(1 '. Human-prescribed fix applied (two-line label) + headlessly re-green; visual re-confirm rides any later GUI session |
| 6 | SETUP-10 + Decision 4 (start-after-generate) | PASS | Start-after-Generate replayed the EXPORTED seed — the shared game is the played game |
| 7 | Extension confirms (Decisions 2/3) | PASS | (a) '.aam.setup.json' approved; (b) '.aamatch.json' + default name 'game.aamatch.json' approved — BOTH CLOSED |
| 8 | Console + robustness | PASS | Zero tracebacks; double-Start restarts cleanly (mid-game replace path); viewer never frozen |

## Score-Surface Clarification (Phase-5 planning input)

Human question at step 3: *"so the score etc not in qt yet?"* — **Answer: YES, by design.** The wizard panel is the Phase-4 feedback surface (score/moves/prompt per the Phase-3 wizard contract); the Qt Game status tab + timer + Hint are SETUP-11 = Phase 5 scope. Recorded in STATE.md so Phase-5 planning inherits it and nobody re-flags the missing Qt score display as a Phase-4 defect.

## Stock-PyMOL Plugin Warnings (unrelated to AA-match)

Launch-session plugin-init warnings matched the 04-14 recorded baseline exactly (findseq, aKMT_Lys_pred, colorblindfriendly, wfmesh, bnitools, mtsslPlotter/mtsslTrilaterate, SuperSymPlugin, phase9_ssl_probe) — pre-existing, UNRELATED to AA-match; no AA-match traceback anywhere in the session.

## Fix-Batch Items

**1. [Rule 1 - Cosmetic readability] Upload path label clipped the record count — RESOLVED**

- **Found during:** checkpoint step 5 (SETUP-03 upload E2E)
- **Issue:** `upload_path_label` showed `'<path> (N molecule record(s))'` on ONE line; a long Windows path clipped everything after the '(' of the count ("only see `(1 ` label after upload")
- **Fix (human-prescribed):** record count on its OWN line: `'%s\n(%d molecule record(s))'` — QLabel renders embedded newlines natively and grows vertically; the tooltip still carries the FULL path (unchanged)
- **Files modified:** `aamatch/setup_window.py` (`_ingest_upload` label line + docstring mention)
- **Smoke check:** PART D carries NO assert pinned to the old single-line label text (the label was always treated as cosmetic — only blanked for a clean close), so zero smoke churn; path/sha256/upload_ready asserts untouched
- **Commit:** 27e8f34 `fix(04-15): upload path label readability -- record count on its own line (checkpoint B fix-batch)`
- **Re-verify:** py_compile green; 688/688 WSL green; SMOKE-11 PASS with PART D green

## Task Commits

1. **Fix:** 27e8f34 — `fix(04-15): upload path label readability -- record count on its own line (checkpoint B fix-batch)`
2. **Finalization (docs):** this summary + STATE.md updates — commit follows this file

**Plan metadata:** `docs(04-15): checkpoint B APPROVED -- criterion 4 + upload E2E + extension confirms (label fix applied)`

## Files Created/Modified

- `aamatch/setup_window.py` — two-line upload path label + docstring (fix-batch)
- `.planning/phases/04-qt-setup-window/04-15-SUMMARY.md` — this summary (records ROADMAP Phase-4 criterion 4 + upload E2E + extension-confirm [HUMAN] verdicts)
- `.planning/STATE.md` — position 15/15 Phase 4 ALL PLANS EXECUTED, verdict section, two decisions recorded, session continuity → next: phase verifier

## Decisions Made

- **04-15 checkpoint B APPROVED (with fix-batch of one, resolved):** ROADMAP Phase-4 criterion 4 (SETUP-08/09/10) human-verified; upload E2E PASS-AFTER-FIX; robustness green. Phase-4 verdict coverage is now complete (A: criteria 1-3; B: criterion 4).
- **Two-line upload label is the new format:** `'%s\n(%d molecule record(s))'` with the full path retained in the tooltip (human-prescribed; permanently recorded so no later plan re-flattens it).
- **Extensions confirmed (Decisions 2/3 CLOSED):** '.aam.setup.json' and '.aamatch.json' + default 'game.aamatch.json' both human-approved.
- **Score-surface clarification:** wizard panel = Phase-4 feedback; Qt Game tab/timer/Hint = Phase-5 SETUP-11 scope (Phase-5 planning inherits this).

## Deviations from Plan

None — checkpoint presented; human verdict recorded; the single fix-batch item carried the human's own prescribed fix and verified green on first re-run.

## Authentication Gates

None.

## Next-Phase Readiness

- **Phase verifier UNBLOCKED:** all four ROADMAP Phase-4 criteria have [HUMAN] verdict coverage (04-14: 1-3 APPROVED; 04-15: 4 APPROVED-WITH-FIX). 15/15 plans executed.
- **Phase-5 planning inherits:** the score-surface clarification (wizard panel is Phase-4 feedback; Qt Game status tab/timer/Hint = SETUP-11), the two-line upload-label format, and the recorded stock-plugin-warnings baseline for any future GUI checkpoint triage.
- **Watch item:** step 5's visual re-confirm (the two-line label on a real long path) rides any later GUI session — the fix is headless-proven only for correctness (flow), which is what step 5's substance was.
