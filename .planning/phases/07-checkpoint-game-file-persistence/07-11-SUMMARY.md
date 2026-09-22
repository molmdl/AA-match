---
phase: 07-checkpoint-game-file-persistence
plan: 11
subsystem: testing
tags: [regression-battery, smoke-suite, wsl-suite, persistence, phase-7]

requires:
  - phase: 07-checkpoint-game-file-persistence
    provides: merged Phase-7 tree (07-01…07-10) — .pse round-trip, pure checkpoint module, save/load seams, Save/Import buttons, one-button kind-dispatch
provides:
  - Recorded full-battery verdicts on the merged Phase-7 tree (890/890 WSL, 20/20 smokes)
  - Matrix round-trip verdict (SMOKE-17: object matrices survive .pse bit-exactly; sidecar carries NO matrices)
  - ROADMAP Phase-7 criterion coverage map (criterion 1 HEADLESS half, criterion 2 refusals, criterion 3 mechanics)
affects: [07-12 human checkpoint, phase-7 verifier, phase-8, phase-9]

tech-stack:
  added: []
  patterns:
    - "Two-run smoke contract: fixture-existence toggles SAVE (run 1) -> VERIFY (run 2); battery runs each two-run smoke twice in sequence"

key-files:
  created: []
  modified: []

key-decisions:
  - "No production changes in 07-11 — the merged tree passed all 890 WSL tests and all 20 smokes with zero fixes"

patterns-established:
  - "Battery verdict recording: per-smoke PASS markers + check counts + criterion coverage map land in the plan SUMMARY for the phase verifier"

duration: ~7 min
completed: 2026-09-22
---

# Phase 7 Plan 11: Full Regression Battery — merged-tree verdicts + criterion coverage map

**890/890 WSL tests green and all 20 smokes PASS (SMOKE-17 & SMOKE-20 two-run contracts honored) on the merged Phase-7 tree — zero regressions across nine phases of accumulated behavior, zero fixes required.**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-09-22T03:41:03Z
- **Completed:** 2026-09-22T03:47:37Z
- **Tasks:** 2/2
- **Files modified:** 0 (verification/battery plan — no production code touched)

## Accomplishments

- Full WSL suite green on the merged tree: `py_compile aamatch/*.py` OK; **890/890 tests OK** (30.4 s, zero failures/errors, purity gates included; 02-11 perf guard: worst-case detect() 0.372 s / guard 2.0 s).
- All 20 smokes re-run green in number order; SMOKE-17 and SMOKE-20 run **twice each** under the fixture-existence two-run contract (run 1 SAVE -> run 2 VERIFY).
- Matrix round-trip verdict recorded: **object matrices survive `.pse` bit-exactly** (SMOKE-17 run 2 `matrix_max_delta=0.000e+00`, coords/view `max_delta=0.000e+00 exact=True`); the sidecar carries **NO matrices** (fallback documented, additive `.get(None)`-skip).
- Criterion coverage map recorded for the phase verifier and the 07-12 [HUMAN] checkpoint.

## Task Commits

This is a verification/battery plan (`files_modified: []`): no production or test files changed, so there are no per-task code commits — and none were needed (zero deviations).

1. **Task 1: Full WSL suite + py_compile** — PASS (890/890), no commit (no files changed)
2. **Task 2: Full smoke battery (01–20, two-run contracts)** — PASS (20/20), no commit (no files changed)

**Plan metadata:** see the `docs(07-11)` commit (SUMMARY + STATE).

## Battery Verdict Table

### WSL suite

| Gate | Command | Verdict |
|------|---------|---------|
| Syntax floor | `python3.6 -m py_compile aamatch/*.py` | **OK** |
| Full unit suite (incl. purity gates) | `python3.6 -m unittest discover -s tests -v` | **OK — Ran 890 tests in 30.433s, 0 failures/errors** |

### Smoke battery (all invoked via `bash smoke/run_smoke.sh smoke/smoke_NN_*.py <timeout>`)

| Smoke | Name | Timeout | Verdict | Checks |
|-------|------|---------|---------|--------|
| 01 | bootstrap | 120 | **=== SMOKE-01 PASS ===** | env probes OK (PyMOL 2.5.0 / PyQt5 5.12.3 / Qt 5.12.9 / numpy 1.25.2; fwdslash + spacepath loads OK) |
| 02 | manifest | 300 | **=== SMOKE-02 PASS ===** | all-manifest battery PASS (incl. benzamide charges/states/metal/halogen scans; no tmp leak) |
| 03 | generate | 180 | **=== SMOKE-03 PASS ===** | perturb/transform/reset replay/cleanup/teardown PASS (reset worst 2.9e-07) |
| 04 | e2e | 240 | **=== SMOKE-04 PASS ===** | 25/25 PASS lines (rotation metric drift 2.61e-09; score 1.0 survives rotation; reset restores grid) |
| 05 | perf | 300 | **=== SMOKE-05 PASS ===** | 21 PASS lines (perf + cleanup 82/82 + exact teardown) |
| 06 | spike_movement | 120 | **=== SMOKE-06 PASS ===** | 60 PASS lines (translate/undo dev = 0.0) |
| 07 | wizard_loop | 240 | **=== SMOKE-07 PASS ===** | 86 PASS lines (incl. the 07-08 books part; worst drifts all sub-1e-06) |
| 08 | starter | 240 | **=== SMOKE-08 PASS ===** | 52 PASS lines (incl. the 07-05 payload-direct part: registry parity/adopt identity/5-key `_last_start`/GO parity) |
| 09 | qt_probe | 120 | **=== SMOKE-09 PASS ===** | offscreen Qt platform probe PASS |
| 10 | upload_flow | 120 | **=== SMOKE-10 PASS ===** | 20 PASS lines (bundled bare start_game intact) |
| 11 | window | 240 | **=== SMOKE-11 PASS ===** | 95 PASS lines (incl. the evolved 5-key PART-H `_last_start` pin) |
| 12 | upload_e2e | 300 | **=== SMOKE-12 PASS ===** | 28 PASS lines (MOL2 probe refusal pinned; scene at baseline) |
| 13 | qt_timer_probe | 120 | **=== SMOKE-13 PASS ===** | offscreen timer/modal probe PASS |
| 14 | status_surface | 120 | **=== SMOKE-14 PASS ===** | 29 PASS lines (status tab surface incl. reserve) |
| 15 | lifecycle | 240 | **=== SMOKE-15 PASS ===** | **75/75** (A28+B23+C24, 0 failures) |
| 16 | tab | 240 | **=== SMOKE-16 PASS ===** | **95/95** (A30+B23+C14+D10+E18; incl. 07-06 Save part D and 07-10 resume/dispatch part E) |
| 17 | pse_roundtrip **run 1 (SAVE)** | 240 | **=== SMOKE-17 PASS ===** | wizard pickles: `pickle.dumps(wiz,1) ok=True`; fixtures minted (`tmp/smoke fixtures/aam_pse17/`) |
| 17 | pse_roundtrip **run 2 (VERIFY)** | 240 | **=== SMOKE-17 PASS ===** | `VERDICT coords: max_delta=0.000e+00 exact=True -> PROVEN`; `VERDICT view: max_delta=0.000e+00 exact=True`; `VERDICT matrix-probe: matrix_max_delta=0.000e+00 coord_vs_birth=8.340 A (bake confirmed), both sides survive .pse`; `VERDICT wizard: strict restore compare -> PROVEN` |
| 18 | save_checkpoint | 240 | **=== SMOKE-18 PASS ===** | **31/31** (A8+B10+C5+D3+E3+Z2): sidecar blocks round-trip EVERY block; restored top-of-stack is a GameWizard through the REAL `__reduce__` pickle path; restored books == captured sidecar books |
| 19 | import | 240 | **=== SMOKE-19 PASS ===** | **39/39** (A4+B14+C5+D16): import reconstructs + 16-check PART D eight-class exact-message refusal battery, scene byte-untouched |
| 20 | checkpoint_e2e **run 1 (SAVE)** | 240 | **=== SMOKE-20 PASS ===** | RUN1 saved game.aamz (detect=0, books_objects=7, elapsed=123.0) |
| 20 | checkpoint_e2e **run 2 (VERIFY)** | 240 | **=== SMOKE-20 PASS ===** | 32 checks: `VERDICT resume: adopt path books/status/pose/timer/detect/continue-play -> PROVEN`; `VERDICT resume: forced-rebuild branch (predicate patched False) -> PROVEN`; fixtures rmtree'd |

**Battery total: 20/20 smokes PASS; both two-run contracts (17, 20) passed BOTH runs; zero regressions.**

## Matrix Round-Trip Verdict (ROADMAP criterion 1 recording)

> **Object matrices survive `.pse` bit-exactly** — SMOKE-17 run 2 matrix-probe `matrix_max_delta=0.000e+00` (and `coord_vs_birth=8.340 A`, confirming the movement bake is live, with both sides surviving the `.pse`), plus coords and view at `max_delta=0.000e+00 exact=True`. **The checkpoint sidecar therefore needs NO matrices** — no sidecar transform keys exist; the pre-07-01 fallback remains documented and is skipped additively (`.get(None)`), so matrix persistence is entirely a `.pse` property.

## ROADMAP Phase-7 Criterion Coverage Map (mechanical halves)

- **Criterion 1 [HEADLESS + HUMAN] — HEADLESS half covered:** SMOKE-18 (save writes the zipped `.pse` + JSON-sidecar container; full sidecar round-trip through the real gates) + **SMOKE-20 two-run** (save -> quit -> relaunch-as-fresh-process -> load restores placed positions/orientations, scores, counters, and timer; adopt + forced-rebuild both PROVEN) + SMOKE-17 two-run (the matrix round-trip result recorded above). The HUMAN half is 07-12's to confirm.
- **Criterion 2 [HUMAN] — Import button loads an exported game and reconstructs it; stale/foreign refused — mechanical half covered:** SMOKE-19 (39/39: reconstruct proof incl. branch-taken object identity; PART D 16-check eight-class exact-message refusal battery: wrong magic / newer format version / detector stamp mismatch / foreign kind / corrupt JSON / etc., with the scene byte-untouched) + SMOKE-16 PART E (18/18: one-button dispatch drives both file kinds through the real `_import_by_kind`). The HUMAN UI confirmation is 07-12's.
- **Criterion 3 [GATE] — session-restore hygiene:** wizard pickles cleanly (SMOKE-17 run 1 `pickle.dumps ok=True` + run 2 **strict restore compare PROVEN**; SMOKE-18 REAL pickle-path GameWizard restore) · sentinel-first reconstruction reconciles sidecar vs loaded atoms (**SMOKE-20 run 2** reconcile/adopt asserts PROVEN; `load_checkpoint` = the 07-09 9-step sentinel-first order) · plugin-reload restore + console clean during save/load (SMOKE-17 run 2 zero Session-Warning under strict restore) · purity gates green (890-test WSL suite: pure checkpoint/persistence modules remain stub-free stdlib-only). **GATE half fully mechanical: PASS.**

## Decisions Made

None — verification plan executed exactly as written; no production or test edits were needed.

## Deviations from Plan

None — plan executed exactly as written. No regressions surfaced, so no Rule-1 fixes were required.

## Issues Encountered

None. The two-run fixture dirs (`tmp/smoke fixtures/aam_pse17/`, `aam_pse20/`) did not exist at battery start, so run 1 (SAVE) executed naturally on the first invocation of each two-run smoke; VERIFY smoke 17 rmtree'd its fixture after proving, and SMOKE-20 run 2 rmtree'd its own — the battery left only `tmp/smoke fixtures/min.pdb` behind.

## Authentication Gates

None.

## Next Phase Readiness

- **07-12 [HUMAN] checkpoint** consumes this SUMMARY: the mechanical halves of criteria 1–3 are recorded PASS above; the human halves (real-GUI save/load UX, Import button UX) are what 07-12 verifies.
- The phase verifier can rely on: 890/890 WSL, 20/20 smokes (17 & 20 two-run), matrix verdict, and the coverage map — all recorded here.
- No blockers or concerns carried forward.

---
*Phase: 07-checkpoint-game-file-persistence*
*Completed: 2026-09-22*
