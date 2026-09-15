---
phase: 03-wizard-gameplay-loop
verified: 2026-09-15T14:00:00Z
status: passed
score: 27/27 must-haves verified
gaps: []
notes_for_later_phases:
  - "spec.md 12-21 setup popup from Plugins menu — recorded Phase-4 seam item (Plugins -> AA-match currently auto-starts a default game); Phase-3 roadmap criteria do not include the setup window"
  - "Nudge keys are screen-relative BY DESIGN — Phase 5/9 help text must say 'keys move in your current view direction'"
  - "Native whole-object drag = object-MATRIX path, probe-verified detector-VISIBLE (transform_object bakes coordinates) — no Phase 5/6 guard needed"
  - "REQUIREMENTS.md traceability table still shows PLAY-01..04 as 'Pending' — stale doc-tracking; update at phase close"
  - "Repeated Confirm appends to engine GameState molecule_scores — Phase 6 owns score-history lifecycle"
  - "Reset to Grid is position-only (rotations persist) — documented behavior, help-text candidate for Phase 5/9"
---

# Phase 3: Wizard Gameplay Loop — Verification Report

**Phase Goal:** In a fresh, stock PyMOL, a player can play the core loop by hand: click an amino acid to select it, move/rotate it onto the small molecule, confirm, and see the detection result — with no helper visuals and the user's environment restored afterwards.
**Verified:** 2026-09-15T14:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification (no previous VERIFICATION.md existed)

**Method:** goal-backward against the ACTUAL code (not SUMMARY claims). All artifacts checked for existence, substance (line floors + export surfaces), and wiring (grep of call sites). All four standing gates re-run live from the repo root during this verification. The two [HUMAN] checkpoints (03-06, 03-07) are treated as APPROVED per the recorded verdicts in their SUMMARYs + STATE.md; this report verified the recorded evidence exists and is internally consistent, not re-run the GUI sessions.

---

## Gate Results (re-run live during this verification)

| Gate | Command | Result |
| ---- | ------- | ------ |
| Syntax floor (3.6) | `python3.6 -m py_compile aamatch/*.py` | CLEAN |
| WSL suite (incl. purity gates + no-helper-visuals AST gate) | `python3.6 -m unittest discover -s tests` | **614/614 OK** (47.8 s) |
| SMOKE-07 headless E2E wizard loop | `bash smoke/run_smoke.sh smoke/smoke_07_wizard_loop.py` | `=== SMOKE-07 PASS ===` (78 checks incl. PART F; worst drifts: nudge3 7.84e-09, R^T live 2.51e-08, reset 2.94e-07) |
| SMOKE-08 headless starter proof | `bash smoke/run_smoke.sh smoke/smoke_08_starter.py` | `=== SMOKE-08 PASS ===` (31 checks; both restart paths, ORDER-LAW msm assert, instance-marker restart proof, exact teardown) |

---

## Per-Plan Must-Have Verification

### 03-01 — Pure wizard_core

| Must-have | Evidence | Verdict |
| --------- | -------- | ------- |
| Reverse slot map from ONE molecule, fail-closed refusals | `build_slot_map` (wizard_core.py:56) consumes `registry['molecules'][molecule_index]['slots']` (lines 78–90), ValueError naming the cause on bad shapes | ✓ VERIFIED |
| Camera→world Rᵀ conversion from get_view rotation block; identity pass-through | `view_camera_to_world` (wizard_core.py:127); convention **live-verified** in SMOKE-07 run today (`rt_live_dev: 2.51e-08` vs scripted `cmd.set_view`) — the single fix site never fired | ✓ VERIFIED |
| Snapshot exactly-once per slot, idempotent; restore = plain {ID: color} | `ensure_snapshot`/`color_map`/`snapshot_objects` (wizard_core.py:158/178/189); 18-test battery + SMOKE-07 row-exact restore asserts | ✓ VERIFIED |
| Artifact `aamatch/wizard_core.py` (≥100 lines, named exports) | 192 lines; build_slot_map, transient_selection, view_camera_to_world, ensure_snapshot, color_map, snapshot_objects + NUDGE_STEP 1.0 / ROTATE_STEP_DEG 10.0 / ROTATE_BUTTON_STEP_DEG 90.0 / HIGHLIGHT_COLOR 'green' all present | ✓ VERIFIED |
| Artifact `tests/test_wizard_core.py` (≥100 lines) | 239 lines, 18 tests | ✓ VERIFIED |
| Key link: registry shape consumption | `registry.get('molecules')` at wizard_core.py:78 | ✓ WIRED |
| Key link: PURE_MODULES registration | test_purity.py:90 — `'wizard_core', 'wizard_text'` in PURE_MODULES | ✓ WIRED |

### 03-02 — Pure wizard_text

| Must-have | Evidence | Verdict |
| --------- | -------- | ------- |
| Panel entries always 3-element [kind, text, code], kinds {0,1,2}, ≤255 ASCII | `panel_entries` (wizard_text.py:193) + `_clip` (:64); 41-test contract battery; SMOKE-08 live panel = "16-entry all-3-element" | ✓ VERIFIED |
| Button codes only `cmd.get_wizard().method()` / `cmd.set_wizard()` | Codes built at :49–50 etc.; no module name anywhere (module-identity trap dodged by construction, pinned by tests) | ✓ VERIFIED |
| Results render as text lines only — never geometry descriptors | `result_lines` (wizard_text.py:106); 'Formed (not required)' line (7cf28f5); no-geometry-words assert in test battery | ✓ VERIFIED |
| Required summaries: 'pi_stacking x1' list mode / 'any interaction' | `required_summary` (:77), order-preserving, fail-closed | ✓ VERIFIED |
| Artifact `aamatch/wizard_text.py` (≥100 lines, named exports) | 273 lines; required_summary, panel_entries, prompt_lines, result_lines, _clip all present | ✓ VERIFIED |
| Artifact `tests/test_wizard_text.py` (≥120 lines) | 499 lines, 41 tests | ✓ VERIFIED |
| Key link: movement constants from wizard_core (single home) | wizard_text.py:38 `from .wizard_core import NUDGE_STEP, ROTATE_BUTTON_STEP_DEG`; labels derive via %g (:230) | ✓ WIRED |
| Key link: result_lines consumes engine.confirm payload (required['items']/mode) | result_lines signature `(score, formed, required, extras=None)`; consumed by wizard.get_prompt/get_panel via `_state_dict()`; SMOKE-07 asserts live panel/prompt result text | ✓ WIRED |

### 03-03 — GameWizard cmd tier (aamatch/wizard.py)

| Must-have | Evidence | Verdict |
| --------- | -------- | ------- |
| Stack-native lifecycle: push via cmd.set_wizard(self), exit via cmd.set_wizard() (None) | wizard.py:174 `cmd.set_wizard(self, replace=replace)`; canonical None-pop documented and used; v1 saved-wizard pattern absent | ✓ VERIFIED |
| do_select→do_pick canonical routing; reverse-map slot resolution; green recolor after snapshot | `do_select` (:248), `do_pick` (:275), `_select_slot` (:301) → `wizard_core.build_slot_map` (:132) + `ensure_snapshot` (:321); SMOKE-07 routes r0c0/r0c1/r0c2 exactly | ✓ VERIFIED |
| Switch restores old colors, recolors new; non-slot clicks no-ops | SMOKE-07 switch/restore + ligand/scratch/empty-space no-op checks PASS today; plus 03-06 display-rebuild fix (0409216) for on-screen staleness | ✓ VERIFIED |
| Movement ONLY via baked world-frame transforms + identity-matrix assert after every move | `cmd.translate(..., state=1, camera=0)` (:451, :504), `cmd.rotate(..., camera=0)` (:471); `_assert_identity` (:403) fail-closes into `_error`; SMOKE-07 re-asserts matrix identity after every press | ✓ VERIFIED |
| confirm_molecule wraps engine.confirm verbatim; reset_grid wraps engine.reset_to_grid | wizard.py:541–543 `from . import engine; engine.confirm(...)`, :589–590 `engine.reset_to_grid()`; result rendered via wizard_text; engine molecule-scoped scoring guard (5962bb2) | ✓ VERIFIED |
| cleanup(): msm SNAPSHOT restore (never '0'), unpick + pk1 delete, per-slot color restore, idempotent, cmd-None guard, never deletes game objects | `cleanup` (:179–247) iterates `wizard_core.snapshot_objects`; SMOKE-07/08 Done restore tables PASS (msm 1→0→1, no pk1/sele strays, colors restored, `_aam_*` kept, idempotent) | ✓ VERIFIED |
| Artifact `aamatch/wizard.py` (≥300 lines, full named surface) | 632 lines; all 16 named methods present (activate, cleanup, do_select, do_pick, _select_slot, nudge_cam, rotate_view, rotate_axis, step_to_ligand, move_to, confirm_molecule, reset_grid, get_prompt, get_panel, get_event_mask, do_special, do_key + WizardError) | ✓ VERIFIED |
| Key link: wizard → engine (lazy relative import inside methods) | `from . import engine` at :523, :541, :589 (inside impls) | ✓ WIRED |
| Key link: wizard → wizard_text | :354 `wizard_text.prompt_lines(self._state_dict())`, :360 `wizard_text.panel_entries(...)` | ✓ WIRED |
| Key link: wizard → wizard_core | :132/:202/:236/:271/:321/:448/:450/:480/:503/:591/:627/:630 | ✓ WIRED |
| Key link: wizard → geometry.centroid_of | :470, :495–496 (rotate origins + step directions) | ✓ WIRED |

### 03-04 — SMOKE-07 + no-helper-visuals source gate

| Must-have | Evidence | Verdict |
| --------- | -------- | ------- |
| Full loop headless: new_game+materialize → activate → scripted select/recolor/switch/no-ops → baked movement + identity → confirm 1.0 → reset replay → Done restore | Re-ran live this session: `=== SMOKE-07 PASS ===` (78 checks); worst drifts recorded (nudge 7.84e-09, Rᵀ live 2.51e-08, step_to_ligand 1.91e-07, reset 2.94e-07) | ✓ VERIFIED |
| No helper visuals: no indicate/distance/load_cgo in wizard source (mechanical gate); smoke creates no lines/dots/CGO | tests/test_wizard_source.py: SCANNED_MODULES=['wizard.py','gamestart.py'] (:51), BANNED_VISUAL_CALLS=('indicate','distance','load_cgo') (:55), ast.Call finder (:80) + firing negative control (VISUAL_TRAP :98–102); gate green inside the 614 | ✓ VERIFIED |
| Camera→world convention live-verified against scripted cmd.set_view | `rt_live_dev: 2.51e-08` in today's SMOKE-07 SMOKE-ENV record | ✓ VERIFIED |
| Artifact `smoke/smoke_07_wizard_loop.py` (≥300 lines, marker) | 924 lines; real print `=== SMOKE-07 %s ===` at :922 (not a docstring mention); imports `from aamatch.wizard import GameWizard` (:131, repo identity) + `from aamatch import engine, ...` (:130) | ✓ VERIFIED |
| Artifact `tests/test_wizard_source.py` (≥40 lines) | 148 lines | ✓ VERIFIED |
| Key link: smoke → GameWizard (repo module identity) | :131 | ✓ WIRED |
| Key link: smoke → engine.new_game/materialize | :283/:292 (+ :720/:722, :757 for parts E/F) | ✓ WIRED |
| Key link: AST scan mirrors ast.Call finder | ast.Call walk at :80 | ✓ WIRED |

### 03-05 — gamestart seam + Plugins menu wiring

| Must-have | Evidence | Verdict |
| --------- | -------- | ------- |
| One-call start_game: cleanup FIRST → new_game → materialize → activate with conditional replace (1 only over prior GameWizard) | gamestart.py:303 `placement.cleanup_game_objects()`, :305–306 `engine.new_game`/`engine.materialize(payload, 0)`, :308 `GameWizard(payload, registry, 0, 0)`, :325 `wiz.activate(replace=(1 if isinstance(prior, GameWizard) else 0))` | ✓ VERIFIED |
| run_plugin_gui lazily imports gamestart; __init__ keeps ZERO module-level imports (Gate A2) | `from . import gamestart` + `return gamestart.start_game()` INSIDE run_plugin_gui; metadata block byte-first; Gate A2 green in the 614 | ✓ VERIFIED |
| SMOKE-08 proves starter headlessly incl. BOTH restart paths + ORDER-LAW msm teeth | Re-ran live this session: `=== SMOKE-08 PASS ===`; replace=1 branch showed "msm 0 in play, snapshot == TRUE pre-game value (saved=1, pre=1)" + "Done after replace=1 restores TRUE pre-game msm"; instance-marker restart proof (359 atoms stamped, 0 survivors) | ✓ VERIFIED |
| Artifact `aamatch/gamestart.py` (≥50 lines, start_game export) | 331 lines; `start_game(setup=None, seed=42, candidates=None)` (:285) | ✓ VERIFIED |
| Artifact `aamatch/__init__.py` (run_plugin_gui lazy seam) | 39 lines; verified above | ✓ VERIFIED |
| Artifact `smoke/smoke_08_starter.py` (≥120 lines, marker) | 608 lines; real print at :606; drives `aamatch.run_plugin_gui()` directly (:192 — the menu-path function) | ✓ VERIFIED |
| Key link: gamestart → engine.new_game + materialize | :305–306 | ✓ WIRED |
| Key link: gamestart → GameWizard + activate(conditional replace) | :132 (import), :308 (instantiate), :325 (activate) | ✓ WIRED |
| Key link: __init__ → gamestart (lazy, inside function) | run_plugin_gui body | ✓ WIRED |

### 03-06 — [HUMAN] gameplay-loop checkpoint (APPROVED via recorded evidence)

| Must-have | Evidence | Verdict |
| --------- | -------- | ------- |
| [HUMAN] PLAY-01 click-select on fresh stock PyMOL, no dev tweaks | 03-06-SUMMARY verdict table: "stock 3-Button Viewing, no dev tweaks — PASS"; strict mol-0 re-test aa02→aa03→aa04 | ✓ VERIFIED (recorded) |
| [HUMAN] PLAY-02 move/rotate + Confirm, result matches screen | Verdict "PASS (after fix batch)": H-bond test SER near benzamide → 1.00 h_bond formed (replaces the invalid generic pi_stacking step-9 — checklist defect recorded) | ✓ VERIFIED (recorded) |
| [HUMAN] PLAY-03 switch selection + Confirm result in panel | Verdict "PASS (after 0409216 switch-restore display-rebuild fix)"; 9/9 fix-batch re-test items APPROVED incl. item 9 Done restore | ✓ VERIFIED (recorded) |
| [HUMAN] Arrow-key Qt-focus probe recorded; editor_scheme sanity | Recorded: LEFT/RIGHT + ',' '.' + q/w/e/d delivered; UP/DOWN dead BY DESIGN; editor_scheme NOT a setting in this build (get_editor_scheme()=1 API) — nothing to restore | ✓ VERIFIED (recorded) |
| Artifact 03-06-SUMMARY.md with recorded verdicts | Present; verdict table + fix-batch commit list (10 commits) + debug memory reference (.planning/debug/phase3-gui-checkpoint-failures.md) | ✓ VERIFIED |
| Key link: checkpoint exercised gamestart.start_game via Plugins menu | Recorded flow: fresh PyMOL → Plugins → AA-match → defaulted game materializes with wizard active | ✓ VERIFIED (recorded) |

### 03-07 — [HUMAN+GATE] restoration + no-helper-visuals + drag diagnostics (APPROVED via recorded evidence)

| Must-have | Evidence | Verdict |
| --------- | -------- | ------- |
| [HUMAN] No helper lines/dots/CGO at any point during play | 03-07-SUMMARY check A: "recolor + panel/prompt text ONLY across all sessions — PASS" | ✓ VERIFIED (recorded) |
| [HUMAN] Done restores prior wizard (stack-native), msm SNAPSHOT, no pk1/sele/_drag strays, colors restored | Check B PASS: prior `wizard measurement` auto-resumes; msm 1→0→1; no strays; recolors restored; `_aam_*` objects survive; plain-run variant also recorded | ✓ VERIFIED (recorded) |
| [HUMAN-GATE] Interactive-drag verdict recorded (coordinate vs matrix path) | Check C RECORDED — MATRIX PATH: `drag _aam_aa06` echo + run-2 checker `IDENTITY-OK False` with genuine rotation matrix; run 1 (all-identity) recorded as non-conclusive. Headless probe verdict MATRIX PATH VISIBLE (transform_object bakes coordinates; detector-view centroid matches R·pose+t exactly, dev 0.0–1e-6). Steps D/E (populated-_drag session, transform_object doubling) SKIPPED by explicit human decision with recorded rationale — per the [GATE] contract, the required verdict IS recorded; the skip is a decision, not a gap | ✓ VERIFIED (recorded) |
| [HUMAN] transform_object render-doubling verdict recorded | Explicitly human-skipped with rationale (low marginal value; SMOKE-07 78 / SMOKE-08 31 already bound the game-path movement model); recorded as a decision in the SUMMARY and STATE.md | ✓ VERIFIED (recorded decision) |
| Artifact 03-07-SUMMARY.md closing the [HUMAN+GATE] half | Present; verdict table + probe verdict + movement-model-frozen decision + STATE.md updated | ✓ VERIFIED |
| Key link: checker snippet asserts identity via get_object_matrix (legal call) | Run-2 evidence recorded (`IDENTITY-OK False` + matrix values); get_object_matrix is not in the banned trio | ✓ VERIFIED (recorded) |

---

## Goal-Backward Observable Truths (phase-level)

| # | Truth (what must be TRUE for the goal) | Status | Evidence |
| - | -------------------------------------- | ------ | -------- |
| 1 | A player clicking an AA selects it (recolor + status), on stock PyMOL in 3-Button Viewing | ✓ VERIFIED | do_select→do_pick→_select_slot wired to the slot map; SMOKE-07 scripted-pick routing PASS; human 03-06 PLAY-01 APPROVED |
| 2 | The selected AA can be moved/rotated onto the small molecule | ✓ VERIFIED | 6 panel movement handlers + keyboard channels, baked camera=0 transforms, identity invariant; SMOKE-07 movement battery PASS; human 03-06 PLAY-02 APPROVED (1.00 h_bond matches screen) |
| 3 | Clicking another AA switches selection; Confirm runs detection with the result visible in the wizard panel | ✓ VERIFIED | switch-restore + display-rebuild fix; confirm_molecule → engine.confirm (molecule-scoped) → wizard_text result lines into live panel AND prompt (SMOKE-07 assert); human 03-06 PLAY-03 APPROVED |
| 4 | No helper visuals at any point during play | ✓ VERIFIED | Mechanical AST gate (test_wizard_source.py, in the 614 green) + human-confirmed across all 03-06/03-07 sessions |
| 5 | The user's environment is restored after the game wizard exits | ✓ VERIFIED | cleanup() msm-snapshot restore / unpick+pk1 delete / per-slot color restore / idempotent; SMOKE-07+08 Done restore tables PASS live today; human 03-07 check B APPROVED incl. prior-wizard auto-resume |
| 6 | A fresh PyMOL reaches the playable loop from the Plugins menu in one step | ✓ VERIFIED | run_plugin_gui → gamestart.start_game lazy seam; SMOKE-08 drives the menu function directly, PASS live today |

**Phase truth score: 6/6** · **Plan must-have score: 27/27**

---

## ROADMAP Phase-3 Success Criteria Mapping

| # | Criterion (ROADMAP) | Requirement | Verdict | Evidence |
| - | ------------------- | ----------- | ------- | -------- |
| 1 | [HUMAN] Click selects AA on fresh PyMOL, canonical do_select→do_pick, no dev-box tweaks | PLAY-01 | ✓ SATISFIED | 03-06 human APPROVED (stock 3-Button Viewing, no tweaks) + SMOKE-07 scripted-pick routing/recolor PASS (re-run live) |
| 2 | [HUMAN] Selected AA moved/rotated onto the small molecule; detector scores the moved pose (movement model composed into detection, result matches screen) | PLAY-02 | ✓ SATISFIED | 03-06 human APPROVED after fix batch (H-bond 1.00 matches screen); movement model = baked camera=0 transforms + identity invariant, headless-proven; spike verdict + drag-matrix verdict recorded (03-07) |
| 3 | [HUMAN] Clicking another AA switches selection; Confirm finishes + detection result visible in wizard panel | PLAY-03 | ✓ SATISFIED | 03-06 human APPROVED (strict mol-0 re-test) + switch-restore + live panel/prompt result asserts in SMOKE-07 |
| 4 | [HUMAN + GATE] No helper visuals; movement-spike verdict recorded; prior wizard + mouse_selection_mode restored on exit | PLAY-04 | ✓ SATISFIED | [HUMAN] 03-07 checks A+B APPROVED (no visuals any session; full restoration incl. prior-wizard resume); [GATE] movement-spike verdict (RESEARCH-B, commit 3143555) + interactive drag = matrix path (run-2 checker evidence) + headless probe MATRIX PATH VISIBLE; msm 1→0→1 field-verified; AST source gate permanent in the suite |

**Requirements coverage: PLAY-01..04 all SATISFIED.** (PLAY-05 is Phase-5 scope, untouched here.)

---

## Anti-Pattern Scan

| File | Finding | Severity |
| ---- | ------- | -------- |
| All 4 phase production files (wizard_core, wizard_text, wizard, gamestart) | Zero TODO/FIXME/placeholder/empty-return patterns | Clean |
| aamatch/gamestart.py:119 | Prose noting the editor_scheme start-guard contingency is "explicitly NOT implemented" | ℹ️ Info — documented decision (scheme law makes baked world-frame movement scheme-independent), not a stub |
| smoke/smoke_07_wizard_loop.py / smoke_08_starter.py | No helper-visual cmd calls; verdict markers are real prints | Clean |

Blockers: none.

---

## Human Verification Required

None outstanding. The ROADMAP's two [HUMAN] checkpoints are APPROVED with recorded verdicts (03-06: PLAY-01..03 + 9/9 fix-batch re-test + arrow-key map; 03-07: PLAY-04 restoration + no-helper-visuals + drag-matrix verdict), and the underlying evidence was confirmed present and consistent across the SUMMARYs, STATE.md, and the debug memory. The two skipped drag-diagnostics steps (populated-_drag session; transform_object render-doubling) are explicit recorded human decisions — per the [GATE] contract the required verdict (drag = matrix path) is recorded with checker + probe evidence; these are not gaps.

---

## Gaps Summary

**No gaps.** Every plan must-have is verified in the actual code; all four gates re-run green during this verification (614/614 WSL, py_compile clean, SMOKE-07 + SMOKE-08 PASS live).

**Notes for later phases (not gaps):**
1. **Phase 4 seam item:** spec.md 12–21 expects Plugins → AA-match to open a setup popup; today it auto-starts a default game. Recorded human decision — Phase-3 roadmap criteria do not include the setup window; the full Qt setup window is Phase 4 and calls the same `start_game` seam.
2. **Phase 5/9 help text:** nudge keys are screen-relative by design — help text must say "keys move in your current view direction." Also: Reset to Grid is position-only (rotations persist) — a help-text candidate.
3. **No Phase 5/6 guard needed:** native drag = object-matrix path, probe-verified detector-VISIBLE (transform_object bakes coordinates).
4. **Doc housekeeping:** `.planning/REQUIREMENTS.md` traceability table still lists PLAY-01..04 as "Pending" — stale; should be flipped at phase close by the orchestrator.
5. **Phase 6:** repeated Confirm appends to engine GameState `molecule_scores` (documented caveat; score-history lifecycle is Phase 6 scope).

---

_Verified: 2026-09-15T14:00:00Z_
_Verifier: OpenCode (gsd-verifier)_
