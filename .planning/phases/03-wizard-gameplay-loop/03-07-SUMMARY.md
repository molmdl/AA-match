---
phase: 03-wizard-gameplay-loop
plan: 07
subsystem: ui
tags: [pymol, wizard, human-checkpoint, restoration, movement-model, native-drag, matrix, start-framing]

# Dependency graph
requires:
  - phase: 03-wizard-gameplay-loop
    provides: plans 03-01..03-06 (wizard stack + gamestart seam + SMOKE-07/08 headless proofs + 03-06 approved gameplay loop)
provides:
  - PLAY-04 [HUMAN+GATE] verdicts recorded: no helper visuals across all sessions; full restoration table on Done incl. prior-wizard auto-resume
  - Movement-model closure: native whole-object drag = object-MATRIX path PROVEN (panel echo + rotation-matrix evidence), baked-coordinate game movement FROZEN for gameplay
  - Headless matrix-visibility probe verdict: MATRIX PATH VISIBLE (transform_object bakes coordinates; detector sees the matrix-moved pose) — no drag guard needed
  - Start-framing laws: geometry-side ligand front-offset + active-molecule-only framing + zoom-last + camera-field-surgery-avoided
affects: [phase-3 verifier, phase-4 Qt setup window, phase-5 input/help text, phase-6 scoring/confirm UX, gap-closure planning]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Probe verdict: cmd.transform_object(name, [R|t] 16-vector, homogenous=1) BAKES coordinates (iterate_state reads matrix-applied coords; extract_game_atoms + detector.detect see the moved pose exactly) — object-matrix moves are detector-compatible"
    - "Start framing: ligand offset in WORLD space in front of its own grid + frame ONLY the active molecule's grid+ligand, zoom LAST (blank-start-view regression fixed by re-framing after composition, never by camera near/far surgery)"

key-files:
  created:
    - ".planning/phases/03-wizard-gameplay-loop/03-07-SUMMARY.md"
  modified:
    - ".planning/debug/phase3-gui-checkpoint-failures.md"
    - ".planning/STATE.md"
    - "aamatch/gamestart.py (earlier in-plan: framing chain 0c13184/d8e8f7d/0041e74/2a182d7)"
    - "smoke/smoke_08_starter.py (earlier in-plan: composition/frustum-aware asserts)"

key-decisions:
  - "PLAY-04 [HUMAN+GATE] CLOSED: no helper visuals in any session; Done restoration table fully field-verified (prior wizard auto-resume, msm 1->0->1 by design, no pk1/sele/_drag strays, recolors restored, _aam_* objects survive)"
  - "Native whole-object drag = MATRIX path PROVEN: 'Dragging whole object' echo + genuine rotation matrix on get_object_matrix (IDENTITY-OK False, run 2)"
  - "Movement model FROZEN (human, 2026-09-15): gameplay movement = panel buttons + keyboard, baked world-frame coordinates; native drag deliberately NOT a gameplay input"
  - "Probe verdict MATRIX PATH VISIBLE: transform_object(homogenous=1) bakes coordinates (dev_vs_applied=1e-6 A vs dev_vs_raw=11.12 A; detector-view centroid matches R.pose+t exactly) — native drag is detector-compatible, SAFE, no Phase 5/6 guard candidate opened"
  - "Nudge left/right is SCREEN-RELATIVE BY DESIGN: keys move in the player's current view direction; Phase 5/9 help text must say so explicitly"
  - "Start-framing laws: geometry-side ligand front-offset; active-molecule-only frame; zoom-last; camera-field-surgery avoided (re-frame after composition, never hand-edit clip planes)"
  - "Drag diagnostics steps 3/4 (populated-_drag session; transform_object render-doubling) SKIPPED by explicit human decision — low marginal value; headless stack coverage (SMOKE-07/08) already exists"

patterns-established:
  - "Human checkpoint -> recorded verdicts in phase artifacts + debug memory -> gate closure (PLAY-04 [HUMAN + GATE] both halves now observed)"
  - "tmp/ headless probes against the standard engine seam answer detector-visibility questions without production code changes"

# Metrics
duration: 4d (framing iterations 2026-09-12..15; human checkpoint session 2026-09-15; finalization 2026-09-15)
completed: 2026-09-15
---

# Phase 3 Plan 7: Restoration + No-Helper-Visuals + Drag Diagnostics Summary

**PLAY-04 [HUMAN+GATE] fully closed: no helper visuals in any session, the Done restoration table field-verified end-to-end (prior-wizard auto-resume included), the native-drag matrix path proven and — by headless probe — shown detector-VISIBLE (coordinates baked, detector sees the moved pose), with gameplay movement frozen on baked-coordinate buttons/keyboard and the start-framing saga resolved as geometry-side ligand front-offset + active-molecule-only + zoom-last framing.**

## Performance

- **Duration:** 2026-09-12 → 2026-09-15 (framing iterations inside the plan; human checkpoint session + probe + finalization 2026-09-15)
- **Completed:** 2026-09-15T12:30Z
- **Tasks:** 1 blocking human checkpoint (APPROVED with verdicts recorded) + headless matrix-visibility probe + finalization
- **Files modified:** 0 production files in finalization (probe lives in tmp/, git-ignored); framing chain touched `aamatch/gamestart.py` + `smoke/smoke_08_starter.py` earlier in-plan

## Checkpoint Verdict: APPROVED (human, 2026-09-15)

| Check | Verdict | Notes |
|-------|---------|-------|
| Start framing | PASS (after saga) | 5-commit chain: 1d48d71 (camera-only roll, 03-06 finalization) → 0c13184 (ligand-in-front depth framing) → d8e8f7d (blank start-view regression fix — re-frame after composition) → 0041e74 (geometry-side ligand front-offset) → 2a182d7 (active-molecule-only frame). Final = ligand in front of active grid + active-molecule-only view, zoom-last |
| A. No helper visuals (PLAY-04 core) | PASS | recolor + panel/prompt text ONLY across all sessions — never lines, dots, dashes, distance monitors, CGO blobs, or selection crosses |
| B. Restoration on Done | PASS | prior `wizard measurement` auto-resumes after the game's Done (stack-native push/pop); msm baseline 1 → 0 (during, by design) → 1 (post-Done); no pk1/sele/_drag strays; every recolored AA back to its original color; `_aam_*` objects still present (Cleanup is Phase 4). Plain run (no prior wizard): no wizard active after Done, msm unchanged, colors original |
| C. Interactive drag path | RECORDED — MATRIX PATH | `drag _aam_aa06` echoed `Dragging whole object "_aam_aa06".`; real left-drag ROTATED the object; checker run 2: `IDENTITY-OK False` with a genuine rotation matrix [0.685537, -0.503814, -0.525557, 7.300527, ...] — native whole-object drag WRITES object matrices (proven). Run 1 showed ALL IDENTITY (no effective matrix write that session — non-conclusive, noted) |
| D. Populated-_drag drag session | SKIPPED (human decision) | "does user need drag for gameplay? no … then dont need step 3 & 4" |
| E. transform_object render-doubling | SKIPPED (human decision) | Rationale: low marginal value; SMOKE-07/08 already cover the game-path movement model |
| 'parser: no matching files.' console line | Ignorable | human typo before the drag; unrelated to the game |
| CTSH-V key-mapping warning | Ignorable | accidental Ctrl+Shift paste (03-06 verdict, unchanged) |

## Matrix-Visibility Probe (the last open question)

`tmp/probe_0307_matrix_visibility.py` (git-ignored; no production code changes), headless PyMOL 2.5.0 against the standard engine seam (`engine.new_game` defaults + `materialize`, seed 42):

- **Control** (the game's own `cmd.translate([8,0,0], obj, state=1, camera=0)`): detector-view centroid shift EXACTLY (8.0000, 0.0000, 0.0000), dev 0.000000; distance-to-ligand 14.2975 → 11.8499 Å. Pipeline sanity PASS.
- **Matrix move** (`cmd.transform_object(name, Rz(37°)+(5,6,7) 16-vector, homogenous=1)`):
  - iterate_state read-back: **MATRIX-APPLIED (baked coordinates)** — dev_vs_raw = 11.117828 Å, dev_vs_applied = 0.000001 Å (float32-level).
  - Detector view (`geometry.extract_game_atoms`): pose matches R·pose + t EXACTLY (dev_vs_applied = 0.000000; dev_vs_raw = 14.546633 Å); distance-to-ligand 11.8499 → 18.5183 Å.
  - Object-matrix history non-identity, reading back exactly the written Rz(37) block + translation (m[0..7] = [0.798635, −0.601815, 0.0, 5.0, 0.601815, 0.798635, 0.0, 6.0]).
  - `engine.detect()` over the matrix-moved scene runs cleanly; scene restored with zero leaked objects.
- **VERDICT: MATRIX PATH VISIBLE** — `transform_object(homogenous=1)` bakes coordinates, so native-drag-style object-matrix moves land in the detector's pipeline input. Native drag is **detector-compatible: SAFE, nothing to guard**. The pre-planned Phase 5/6 guard candidates (pre-Confirm matrix sweep → auto-bake-to-coordinates / refuse-with-message) are **NOT opened**.

## Task Commits

The checkpoint itself produced no production-code commits; the in-plan framing work was already committed atomically:

1. **Framing chain (fix)**: `0c13184` ligand-in-front-of-grid depth framing → `d8e8f7d` re-frame scene after camera composition (blank start-view regression) → `0041e74` geometry-side ligand front-offset → `2a182d7` active-molecule-only framing
2. **Finalization (docs)**: this summary + STATE.md + debug report — commit follows this file

**Plan metadata:** `docs(03-07): finalize restoration checkpoint — matrix-path verdict + probe`

## Files Created/Modified

- `.planning/phases/03-wizard-gameplay-loop/03-07-SUMMARY.md` — this summary (closes the ROADMAP Phase-3 criterion 4 [HUMAN + GATE] half)
- `.planning/debug/phase3-gui-checkpoint-failures.md` — human 03-07 verdicts + probe result appended; file closed
- `.planning/STATE.md` — position 7/7, verdicts, decisions
- `tmp/probe_0307_matrix_visibility.py` — headless matrix-visibility probe (git-ignored, diagnostic only)

## Decisions Made

- **PLAY-04 [HUMAN+GATE] CLOSED.** Both halves observed: [HUMAN] no helper visuals at any point + full Done-restoration table including prior-wizard auto-resume; [GATE] the movement-spike verdict (RESEARCH-B, commit 3143555) joins this session's interactive-drag answer (matrix path, with populated-checker evidence) and the headless detector-visibility probe.
- **Movement model FROZEN for gameplay (human decision):** panel buttons + keyboard, baked world-frame coordinates (03-03 model). Native whole-object drag = the object-matrix path (panel echo + rotation-matrix run-2 evidence); it is detector-VISIBLE per the probe but is deliberately NOT a gameplay input.
- **Nudge screen-relativity is BY DESIGN:** left/right/up/down/in/out move in the player's *current view direction* (R^T re-read per press, live-proven in SMOKE-07). Phase 5/9 help text must state this explicitly ("keys move in your current view direction").
- **Start-framing laws (final):** (1) ligand offset in WORLD space in front of its own grid (geometry-side composition — user objects never moved); (2) frame ONLY the active molecule's grid + ligand (matches the panel's molecule-scope notice); (3) zoom LAST; (4) camera-field surgery avoided — the blank start-view regression was fixed by re-framing after composition, never by hand-editing near/far clip planes.
- **Steps D/E skipped by explicit human decision** — recorded with rationale (low marginal value; headless coverage (SMOKE-07 78 checks / SMOKE-08 31 checks) already bounds the game-path movement model). Not a gap: the ROADMAP's [GATE] half requires the drag-path verdict recorded, which the matrix echo + checker + probe provide.

## Deviations from Plan

### Auto-fixed Issues (earlier in-plan framing work)

**1. [Rule 1 - Bug] Blank start view after the first framing attempt**
- **Found during:** in-plan framing iteration
- **Issue:** camera composition left a blank start view (frustum regression)
- **Fix:** re-frame the scene after the composition step (`d8e8f7d`)
- **Files modified:** `aamatch/gamestart.py`
- **Verification:** SMOKE-08 composition asserts (frustum + clip-slab fit; inactive-molecule centroid outside the frame)

**2. [Rule 2 - Missing Critical] Ligand occludes/competes with the grid in the start view**
- **Fix:** geometry-side ligand front-offset (0041e74) + active-molecule-only framing (2a182d7); SMOKE-08 per-atom non-occlusion ≥ 5 Å viewer-relative lead + frustum/clip-slab fit asserts

**3. [Human checkpoint deviation] Steps D/E of the drag diagnostics skipped by explicit human decision** — recorded above with rationale; the [GATE] closure is unaffected (verdict recorded + probe result).

---

**Total deviations:** 3 auto-fixed/handled (framing bug batch inside the plan + human checkpoint skip decision); no production-code changes in finalization
**Impact on plan:** The blocking human checkpoint is APPROVED with every planned verdict either recorded or explicitly human-skipped on the record; the closure requirement is met.

## Issues Encountered

- **Drag-checker run 1 ambiguity:** the first interactive-drag session showed ALL IDENTITY matrices (no effective matrix write). Resolved by run 2 with an effective drag → genuine rotation matrix (`IDENTITY-OK False`), which is the decisive evidence for the matrix path; run 1 recorded as non-conclusive, not contradictory.
- **Farming the last open question headlessly:** the detector-visibility of matrix-moved poses was answered by a tmp/ probe against the standard engine seam — no production code touched, scene restored byte-exact.

## Test/Gate Counts

- WSL suite: **614 tests green** (python3.6; purity gates included) — unchanged by finalization (docs-only)
- `python3.6 -m py_compile aamatch/*.py` clean
- Headless probe: all checks PASS, verdict MATRIX PATH VISIBLE (no smoke re-run needed — no tracked-file changes beyond docs)

## User Setup Required

None.

## Next Phase Readiness

- **Phase 3 ALL PLANS EXECUTED (7/7)** — the phase verifier is next. 03-06-SUMMARY.md provides the ROADMAP [HUMAN] half of Phase-3 criteria 1–3; this summary provides criterion 4's [HUMAN + GATE] half (spike verdict RESEARCH-B commit 3143555 + interactive drag-matrix verdict + probe verdict here).
- **Phase 4 (Qt setup window) inputs staged already by 03-06:** the Plugins → AA-match start_game seam is the one-call entry; gap-closure candidate stands (spec.md 12-21 setup popup).
- **Phase 5/6 inputs from this plan:** movement model frozen (buttons/keyboard, baked coords); screen-relative nudge is by design → help text "keys move in your current view direction"; native-drag detector-visibility guard is NOT needed (probe VISIBLE) — no guard candidate carried into Phase 5/6 planning.
- **Phase 5 keyboard map unchanged:** LEFT/RIGHT + ',' '.' + q/w/e/d delivered; UP/DOWN dead by design (03-06).

---
*Phase: 03-wizard-gameplay-loop*
*Completed: 2026-09-15*
