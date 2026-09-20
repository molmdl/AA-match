---
phase: 06-scoring-lifecycle-endgame
plan: 10
type: execute-checkpoint-record
subsystem: ui/verification
tags: [pymol, qt, scoring-lifecycle, endgame, skip-give-up, restart-reset, human-checkpoint, verdicts, fix-batch]

# Dependency graph
requires:
  - phase: 06-scoring-lifecycle-endgame
    provides: plans 06-01..06-09 (GameState lifecycle data layer, status_text Phase-6 surface, gamestart compose seam, engine lifecycle ops, wizard lifecycle core + skip/give-up half, tab lifecycle wiring — Confirm + Skip/Give-Up dropdown + _endgame_sequence, Restart _last_start replay + Reset wizard-public dispatch, endgame modal — all headlessly proven via SMOKE-15 A/B/C + SMOKE-16 A/B/C + the full six-smoke battery)
provides:
  - ROADMAP Phase-6 criterion 1 (SCORE-01/02 confirm + debrief + advance) [HUMAN] verdict recorded: defect-found-and-fixed (fix-batch item, step 1); step-1 re-verify RE-VERIFIED PASS (human, 2026-09-21)
  - ROADMAP Phase-6 criterion 2 (SCORE-03 level escalation, timer-continuous) [HUMAN] verdict recorded: PASS
  - ROADMAP Phase-6 criterion 3 (SCORE-05/06 skip/give-up + warning semantics) [HUMAN] verdict recorded: PASS
  - ROADMAP Phase-6 criterion 4 (SCORE-07 endgame screen, give-up + natural end) [HUMAN] verdict recorded: PASS
  - ROADMAP Phase-6 criterion 5 (SCORE-09/10 restart/reset) [HUMAN] verdict recorded: PASS
  - Wording verdicts for every pinned Phase-6 string (5 poll event lines, game_restarted, both warning boxes, endgame block/headline): CONFIRMED, no amendments
  - Fix-batch item 1 (molecule-advance camera re-frame) applied as commit ff4b519, all gates re-green
affects: [phase verifier (Phase 6 ready), phase-7 (saves carry the fixed camera behavior)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Checkpoint fix-batch pattern (fifth instance; 03-06/03-07/04-15/05-11 precedents): human defect on camera behavior -> RED-proven smoke assert -> one-line fix commit -> full WSL suite + lifecycle/regression smokes re-green -> step-1 visual re-verify routed back to the human"
    - "Advance-compose law: EVERY advance (molecule OR level) must re-frame the camera through _compose_active_molecule — the ONE 06-04 compose seam; _advance_after_record's two advance branches both compose, no duplicated logic"

key-files:
  created:
    - ".planning/phases/06-scoring-lifecycle-endgame/06-10-SUMMARY.md"
  modified:
    - "aamatch/wizard.py"
    - "smoke/smoke_15_lifecycle.py"

key-decisions:
  - "06-10 checkpoint APPROVED-after-fix (human, 2026-09-21) with 1 fix-batch item (in-level molecule advance did not re-frame the camera), resolved in-session (commit ff4b519); step-1 re-verify RE-VERIFIED PASS (human, 2026-09-21) — overall verdict APPROVED (human, 2026-09-21)"
  - "Advance-compose law (06-10 fix, commit ff4b519): the molecule branch of _advance_after_record runs the SAME _compose_active_molecule call as the level branch (wizard.py) — a newly advanced molecule is always camera-framed onto its own grid; regression teeth = SMOKE-15 PART B2 camera re-frame assert (75 checks)"
  - "All pinned Phase-6 wording CONFIRMED as-written (no amendments): 5 poll event lines, game_restarted, both warning boxes, endgame block/headline"

patterns-established:
    - "Smoke-assert vocabulary reuse for checkpoint fix teeth: new regression asserts derive/compare with the SAME primitives as the existing compose asserts (gamestart._active_molecule_selection + ' or '.join name-set comparison, view-before/after inequality) — no new assertion machinery for a fix-batch item"

# Metrics
duration: ~12 min (fix + re-green + documentation; the human checkpoint session itself ran outside agent execution)
completed: 2026-09-21
---

# Phase 6 Plan 10: Consolidated GUI Checkpoint — Full Scoring Lifecycle + Endgame Summary

**06-10 checkpoint APPROVED-after-fix (human, 2026-09-21) with 1 fix-batch item: 8/9 steps PASS outright on a real Windows PyMOL 2.5.0 session — Confirm/debrief/advance semantics + wording, level escalation (new grids materialized and camera-framed, timer CONTINUOUS at 8:28 across all 3 levels), Skip warning + mercy-path semantics (0.00 partial, timer froze under the box), Give Up + endgame screen (frozen label, per-level scores, counts, on-top modal, wizard popped with colors restored), natural end with the winning headline, Restart (D7 after-the-arm log order, counters zeroed, timer from zero), Reset (grid restore, orientations kept, selection green, timer running), wording CONFIRMED (no amendments), console clean. Step 1 (SCORE-01/02) carried the ONE defect: after an in-level molecule advance the camera was NOT re-framed onto the next molecule's grid. Root cause: the molecule branch of `wizard._advance_after_record` never called `_compose_active_molecule`. Fixed in-session (commit ff4b519 — the SAME 06-04 compose seam the level branch already runs), with a RED-proven SMOKE-15 PART B2 regression assert and all gates re-green (826/826 WSL, SMOKE-15 75/75, SMOKE-07 56/56, SMOKE-16 67/67). Step-1 re-verify is **RE-VERIFIED PASS (human, 2026-09-21)**: fresh games (molecules_per_level=1, then default 2) — after a level-1 molecule-1 Confirm the camera automatically re-framed/zoomed onto molecule 2's grid, fix ff4b519 confirmed working in the GUI. All five ROADMAP Phase-6 criteria now carry closed [HUMAN] verdicts; overall verdict is **APPROVED (human, 2026-09-21)**.**

## Performance

- **Duration:** fix + re-green + verdict recording (~12 min); one-line fix in `aamatch/wizard.py` + one new SMOKE-15 PART B2 assert
- **Completed:** 2026-09-21
- **Tasks:** 1 blocking `checkpoint:human-verify` — resolved APPROVED-after-fix with 1 fix-batch item, resolved in-session (step-1 re-verify pending)
- **Verification after fix:** `python3.6 -m py_compile aamatch/*.py` green; **826/826** WSL tests green (48.0 s, count unchanged; purity gates included); `=== SMOKE-15 PASS ===` (**75/75** — grew from 74 by the new B2 assert), `=== SMOKE-07 PASS ===` (**56/56** regression battery), `=== SMOKE-16 PASS ===` (**67/67** tab battery)

## Environment (recorded for the record)

- **PyMOL:** PyMOL(TM) 2.5.0 (Windows, via the recorded setenv.bat conda environment)
- **Install method:** 01-09 plugin-path method — repo root on the PyMOL plugin path, no copy-install (live repo copy)
- **Console triage baseline (04-14 recorded):** stock plugin-init warnings (findseq, aKMT_Lys_pred, cb_colors, wfmesh, bnitools, mtsslPlotter, mtsslTrilaterate, SuperSymPlugin, phase9_ssl_probe) — pre-existing and UNRELATED to AA-match; only NEW AA-match tracebacks/prints are defects.

## Checkpoint Verdict: APPROVED-after-fix with 1 fix-batch item (human, 2026-09-21), resolved in-session — 8/9 PASS + step 1 defect-fixed

| Step | Requirement / ROADMAP criterion | Verdict | Notes |
|------|--------------------------------|---------|-------|
| 1 | SCORE-01/02 Confirm + debrief + advance | DEFECT FOUND → FIXED (fix-batch) → **RE-VERIFIED PASS (human, 2026-09-21)** | Semantics + wording PASS (log evidence: `Molecule 1 of 2 scored 1.00 (total 1.00).` + Formed/Missing lines + next level line). The defect: after an in-level molecule advance the camera did NOT re-frame to the next molecule's grid, with no instruction how to get there. Human verdict verbatim: **"lv 1 after 1st mol not zooming to 2nd mol's grid and no instruction to do so"**. Fixed as commit ff4b519; human step-1 re-verify PASS — camera automatically re-framed/zoomed onto molecule 2's grid after Confirm on molecule 1 (molecules_per_level=1 then default 2). |
| 2 | SCORE-03 level escalation | PASS | `Level 2, molecule 1 of 2.` logged; new higher-difficulty grids materialized and camera-framed (the level-branch compose works); timer CONTINUOUS (final Time: 8:28 spanning all 3 levels, never reset). |
| 3 | SCORE-05 Skip warning + semantics | PASS | Warning box shown; the timer FROZE while the box was open (human gave up within a few seconds after skip; the frozen label evidenced the freeze). Log: `Skipped molecule 1 of 2 (partial score 0.00, total 0.00).` then `Level 1, molecule 2 of 2.` — mercy path (nothing formed stores 0.00, no refusal) exercised. |
| 4 | SCORE-06/07 Give Up + endgame | PASS | Warning; Yes → `Game ended at level 1, molecule 2 of 2 (total 0.00).` + full endgame block in the info box with the GIVE-UP headline `Game over -- gave up at level 1, molecule 2 of 2.`, per-level scores, Total, Time: 0:08 (label frozen), `Molecules completed: 1 of 6. Levels: 3.`, `Skips: 1. Give-ups: 1.`; wizard popped (colors restored); endgame modal appeared ABOVE the 3D viewer; `_aam_*` scene stayed for inspection. Note (human, verbatim): **"i do give up within few second after skip"** — the skip-then-immediate-give-up sequencing worked correctly. |
| 5 | SCORE-07 natural end + winning message | PASS (session 1) | Played all 3 levels (default): `You win! All 3 level(s) finished in 8:28.` + full endgame block (Level 1: 2.00 / Level 2: 0.00 / Level 3: 1.00, Total score: 3.00., Molecules completed: 6 of 6, Skips: 0. Give-ups: 0.). Also observed in-session: Hint worked (`Hint: 15 eligible amino acid(s) highlighted.`) and the `Formed (not required): hydrophobic x1` extras surface rendered. |
| 6 | SCORE-09 Restart | PASS | Log order `[Get ready... / Game restarted. / 3 2 1 GO!` — the pinned D7 after-the-arm order; rebuilt scene; timer from zero (Time: 0:08 on a fresh give-up); all counters zeroed (`Molecules completed: 0 of 6`, `Skips: 0`); required label fresh. |
| 7 | SCORE-10 Reset | PASS | `Amino acids reset to grid positions (orientations kept).` rendered; AAs back at grid; rotation kept; selection stayed green; timer kept running. |
| 8 | Wording approval | CONFIRMED | Every logged string matches the `aamatch/status_text.py` pins; no amendments requested. See the Wording Verdicts section. |
| 9 | Console | PASS | Only the recorded 04-14 stock-baseline plugin-init warnings; zero tracebacks; zero stray AA-match prints. |

**Overall verdict: APPROVED (human, 2026-09-21)** — approved-after-fix with the fix verified: the one fix-batch item (step 1 molecule-advance camera re-frame) was applied as commit `ff4b519` with all gates re-green, and the routed step-1 visual re-verify PASSED (human, 2026-09-21 — camera re-framed onto molecule 2's grid after the Confirm).

## Wording Verdicts (step 8 — permanent pins, human 2026-09-21)

**CONFIRMED for all pinned strings; no amendments requested.** Coverage map (all strings live-verified in-session against `aamatch/status_text.py`):

| String class | Evidence (verbatim from the session log / modal) | Verdict |
|--------------|---------------------------------------------------|---------|
| Poll event line: molecule scored | `Molecule 1 of 2 scored 1.00 (total 1.00).` | CONFIRMED |
| Poll event line: formed / missing debrief | (Formed/Missing lines shown after the scored line; `Formed (not required): hydrophobic x1` extras surface observed) | CONFIRMED |
| Poll event line: level advance | `Level 2, molecule 1 of 2.` | CONFIRMED |
| Poll event line: skip | `Skipped molecule 1 of 2 (partial score 0.00, total 0.00).` | CONFIRMED |
| Poll event line: game ended (give-up) | `Game ended at level 1, molecule 2 of 2 (total 0.00).` | CONFIRMED |
| Poll event line: game restarted | `Game restarted.` (inside the D7 tail `Get ready... / Game restarted. / 3 2 1 GO!`) | CONFIRMED |
| Poll event line: reset | `Amino acids reset to grid positions (orientations kept).` | CONFIRMED |
| Warning box: skip | 'Skip this molecule?' box with the pinned text | CONFIRMED |
| Warning box: give up | 'Give up?' box with the pinned text | CONFIRMED |
| Endgame block + headline (give-up) | `Game over -- gave up at level 1, molecule 2 of 2.` + per-level scores + Total + Time + `Molecules completed: 1 of 6. Levels: 3.` + `Skips: 1. Give-ups: 1.` | CONFIRMED |
| Endgame block + headline (natural end) | `You win! All 3 level(s) finished in 8:28.` + full block (`Total score: 3.00.`, `Molecules completed: 6 of 6`, `Skips: 0. Give-ups: 0.`) | CONFIRMED |
| Hint | `Hint: 15 eligible amino acid(s) highlighted.` | CONFIRMED |

## Fix-Batch Record (1 item, resolved in-session — the 05-11 pattern)

**Human defect (verbatim):** *"lv 1 after 1st mol not zooming to 2nd mol's grid and no instruction to do so"*

**Root cause (confirmed):** `aamatch/wizard.py` `_advance_after_record` — the molecule branch ran `engine.advance_molecule()` + `_rebind_molecule(self._molecule_index + 1)` and returned WITHOUT a compose call; only the level branch called `_compose_active_molecule()` (the re-frame). An in-level advance therefore left the camera framed on the JUST-COMPLETED molecule's grid while the panel already showed the NEXT molecule. The 06-04 public seam `gamestart.compose_molecule_view(registry, molecule_index)` already supports arbitrary indexes (SMOKE-08 PART 5 proved index-1 compose frames molecule 1 only, idempotent, default == explicit-0).

**The fix (commit `ff4b519`):**

- `aamatch/wizard.py` — in the molecule branch of `_advance_after_record`, call `self._compose_active_molecule()` AFTER `self._rebind_molecule(...)` and BEFORE the return. ONE added statement — the SAME seam the level branch already runs (no compose logic duplicated); the method docstring's molecule-branch description now records that the camera re-frames on in-level advance too (06-10 human-checkpoint fix).
- `smoke/smoke_15_lifecycle.py` — PART B2 gained one assert: `B2 camera re-framed by the molecule advance (06-10 fix)` (view-before/after comparison + `gamestart._active_molecule_selection` zoom-target derivation, assert style mirror of the existing B6 level-branch compose assert and the SMOKE-08 PART 5 compose asserts — no new assertion vocabulary). The PART B doc line now records the fix.

**Regime-teeth proof (RED before GREEN):** with ONLY the smoke assert applied (pre-fix `wizard.py`), SMOKE-15 ran 75 checks with EXACTLY ONE failure — the new B2 camera assert (`zoom target has 10 objects, 10 of them molecule-1` — the derivation was right; the view comparison failed, as the pre-fix molecule branch composed nothing). After the wizard fix: 75/75 PASS.

**Re-green proof (post-fix, all green):**

- `python3.6 -m py_compile aamatch/*.py` — OK
- `python3.6 -m unittest discover -s tests -v` — **826/826 OK** (count unchanged; purity gates included)
- `bash smoke/run_smoke.sh smoke/smoke_15_lifecycle.py` — **=== SMOKE-15 PASS ===** (75 checks; grew from 74 by the new assert)
- `bash smoke/run_smoke.sh smoke/smoke_07_wizard_loop.py` — **=== SMOKE-07 PASS ===** (56 `SMOKE-07 ... PASS` lines; regression battery)
- `bash smoke/run_smoke.sh smoke/smoke_16_tab.py` — **=== SMOKE-16 PASS ===** (67 checks)

**Step-1 re-verify obligation: RE-VERIFIED PASS (human, 2026-09-21).** The headless proof of the fix is the SMOKE-15 PART B2 assert above; the human's routed step-1 visual re-verify has now run: on real Windows PyMOL 2.5.0, fresh games were started (first with molecules_per_level=1 — 1 molecule, 9 slots — then default 2 molecules / 18 slots), AAs picked and molecule 1 Confirmed; the camera automatically re-framed/zoomed onto molecule 2's grid after the Confirm — fix `ff4b519` confirmed working in the GUI. Verdict: **RE-VERIFIED PASS**.

## Session Observations (human-volunteered; recorded, may matter later)

1. **Skip-then-immediate-give-up sequencing works** — the human exercised Give Up within a few seconds after Skip deliberately (step-4 note, verbatim: "i do give up within few second after skip"); the endgame books (`Skips: 1. Give-ups: 1.`, ended at level 1 molecule 2 of 2) reflect the full sequence correctly.
2. **Hint + extras surfaces exercised in-session** — step 5's session also exercised Hint (`Hint: 15 eligible amino acid(s) highlighted.`) and the `Formed (not required): hydrophobic x1` extras rendering (the 03-06 UX addition), both working in the real GUI.
3. **Timer freeze under the NEW warning modals human-confirmed** (P-5 class, new dialog instances) — the freeze label evidenced the clock stop while the Skip warning box was open; the must_haves truth is now human-covered.

## must_haves Check

- ✅ **"A human has played a full lifecycle on real PyMOL: confirm/debrief/advance, level escalation, skip/give-up warnings, endgame screen, restart/reset — all five ROADMAP criteria carry [HUMAN] verdicts"** — all five criteria carry verdicts in the step table above (criterion 1 = fixed-after-defect, **re-verify RE-VERIFIED PASS 2026-09-21**; criteria 2-5 PASS).
- ✅ **"The pinned Phase-6 wording (event lines, warnings, endgame block) is human-CONFIRMED or amended in-session"** — CONFIRMED for every pinned string; zero amendments (Wording Verdicts section).
- ✅ **"The timer freeze under the NEW warning modals is human-confirmed (P-5 class, new dialog instances)"** — CONFIRMED under the Skip warning box (step-3 frozen label evidence).
- ✅ **Artifact:** this SUMMARY contains "APPROVED" (APPROVED-after-fix).

## Deviations from Plan

None beyond the recorded fix-batch item — the plan prescribed exactly this flow (fix + re-green + record). The RED-proven smoke assert ordering (assert first, failure observed, then fix) is the house TDD-teeth discipline, not a plan deviation.

## Authentication Gates

None.

## Next Phase Readiness

- All five ROADMAP Phase-6 success criteria carry [HUMAN] verdict coverage — Phase 6 is ready for `/gsd-verify-phase`.
- **Outstanding obligation: CLOSED (2026-09-21).** The routed step-1 human re-verify (molecule-advance camera re-frame on the GUI) RE-VERIFIED PASS — camera re-framed onto molecule 2's grid after the level-1 molecule-1 Confirm (fix ff4b519 verified in the GUI; headless proof = SMOKE-15 PART B2, 75/75).
- Advance-compose law established for all later camera-touching work: ANY molecule/level advance re-frames through the ONE `_compose_active_molecule` seam (commit `ff4b519`).
