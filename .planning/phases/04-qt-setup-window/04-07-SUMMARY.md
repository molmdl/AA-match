---
phase: 04-qt-setup-window
plan: 07
subsystem: qt-window
tags: [pymol, pyqt5, qt, setup-window, form, qstackedwidget, collect-apply, round-trip, smoke-test]

# Dependency graph
requires:
  - phase: 04-qt-setup-window/04-05
    provides: the SetupWindow shell — form_area placeholder QVBoxLayout (stable layout slot), 7-button spec-order row, modeless singleton — extended, never reshaped
  - phase: 04-qt-setup-window/04-02
    provides: setup_form.manifest_sets pure dropdown-row helper (set_id/title/tier with .get fallbacks)
  - phase: 04-qt-setup-window/04-01
    provides: the offscreen probe verdict PASS — SMOKE-11's T1b form parts RUN (same rule as 04-05)
  - phase: 01-bootstrap-pure-foundation
    provides: setup_state frozen constants (MOLECULES_*/DIFFICULTY_*/INTERACTION_TYPES/DEFAULTS) + validate_state single authority
provides:
  - aamatch/setup_window.py — full 7-field form inside the shell: _build_source_selector (2-page QStackedWidget demo/upload), _build_spinboxes (ranges == frozen clamp constants), _build_mode_group (3-way radio + live context label), _build_interactions (7 canonical checkboxes, enabled in all modes), _populate_demo_sets (engine-shaped manifest read + FormatError degrade path), collect_state/apply_state lossless round-trip with _loading guard, session-only _uploaded slot
  - smoke/smoke_11_window.py — PART B extension: apply(DEFAULTS)->collect round-trip through validate_state + programmatic widget mutation drive + demo_combo userData 'demo-dev-1'
affects: [04-09..04-13 (handlers read the form via collect_state, write it via apply_state; 04-10 connects btn_browse and populates _uploaded), 05+ (window stays the form owner across gameplay)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Demo-set encoding: combo userData carries set_id; the empty target ('' = no restriction) is encoded as combo index -1 (empty selection) instead of a synthetic item, keeping apply(DEFAULTS)->collect losslessly equal through validate_state"
    - "Spinbox range == frozen clamp range (never numeric literals): the only arrangement that makes collect->validate_state lossless for int fields (form_field_specs ruling)"
    - "Stacked-pages source selector: inactive page's values stay intact underneath (three coexisting state fields); radio toggled(bool) reaches setCurrentIndex through a lambda because raw bool->int maps pages BACKWARDS"
    - "apply_state _loading guard shape (prior-art pattern): set True FIRST, try/finally False; future valueChanged hooks early-return"

key-files:
  created: []
  modified: [aamatch/setup_window.py, smoke/smoke_11_window.py]

key-decisions:
  - "Empty demo_set_id ('') is encoded as demo_combo.setCurrentIndex(-1) at apply time (no synthetic 'all sets' item invented) — required for the plan's own round-trip identity assert; documented below under deviations"
  - "Checkboxes stay ENABLED in every mode: in unset mode the allowed list is the sampling vocabulary (generator.py:413-414), so disabling would silently discard the user's restriction"
  - "Dropdown populated ONCE at construction; parse failure degrades to '(no bundled sets)' userData '' + visible note — never a crash of the menu action"
  - "The metal/halogen '(no bundled molecule carries this)' annotation is OMITTED (plan Decision 7 — Phase 8 changes the data anyway)"
  - "btn_browse created unconnected; _uploaded is a session-only slot — 04-10 connects/populates, apply_state shows the SAVED upload path in the label but never restores _uploaded"

patterns-established:
  - "collect_state emits EXACTLY the validate_state schema keys; the widget layer performs zero validation (pure layer is the single authority)"
  - "The form is driven headlessly: apply(DEFAULTS) -> mutation drive -> collect asserts, all inside SMOKE-11 PART B under the offscreen verdict"

# Metrics
duration: 16min
completed: 2026-09-15
---

# Phase 4 Plan 07: Setup-Window Form Summary

**The modeless setup window now carries the complete 7-field form (SETUP-02..06 widget side): a 2-page molecule-source selector (manifest-fed demo dropdown with a FormatError degrade path / unconnected upload Browse+path label), molecules and difficulty spinboxes whose ranges are imported from the frozen setup_state constants, a 3-way interaction-mode radio group with a live context label, and 7 canonical-order checkboxes that stay enabled in every mode — all tooltipped, and round-tripping losslessly through validate_state, proven headlessly by the extended SMOKE-11 (apply(DEFAULTS)->collect identity + a full widget mutation drive). 654/654 WSL tests green, === SMOKE-11 PASS === (15 checks).**

## Performance

- **Duration:** ~16 min
- **Started:** 2026-09-15T20:03:58Z
- **Completed:** 2026-09-15T20:19:55Z
- **Tasks:** 3/3
- **Files modified:** 2 (0 created)

## Accomplishments

- **The full form lives in SetupWindow (513 lines, up from the 141-line shell):** `_build_source_selector` — QGroupBox 'Molecule source' with `src_demo`/`src_upload` radios (exact plan tooltips) driving a 2-page `source_stack` (demo page: `demo_combo` + initially-empty `source_note`; upload page: unconnected `btn_browse` + read-only `upload_path_label`), values intact on the inactive page (three coexisting state fields); `_populate_demo_sets` reads MANIFEST.json exactly like the engine (`read_json_file(paths.package_data_path('data','MANIFEST.json'))` -> `parse_manifest_dict`) and fills rows via the pure `setup_form.manifest_sets` (userData=set_id, title-fallback label + optional tier suffix), degrading on any exception to a placeholder `'(no bundled sets)'` item + visible note — window construction can never crash the menu action. `_build_spinboxes` — 'Game size' group with ranges/defaults referenced ONLY as `setup_state.MOLECULES_*`/`DIFFICULTY_*` (grep proves zero numeric literals), spec-plan labels+tooltips. `_build_mode_group` — 3 radios (auto-exclusive in the group parent, no QButtonGroup) with plan-exact labels/tooltips, default `mode_unset` (frozen DEFAULTS), plus `mode_context_label` restating the current mode on every toggle (three exact research strings). `_build_interactions` — 7 QCheckBoxes built by iterating the frozen `INTERACTION_TYPES` (canonical order == collect order), UI-only display labels ('Hydrogen bond' ... 'Metal coordination') with per-type in-game-term tooltips.
- **collect_state/apply_state — the form as a lossless view of the 7-field model:** collect emits exactly the 7 schema keys (`source_mode` from the radios, `demo_set_id` via `currentData() or ''`, `upload` from the session-only `_uploaded` slot or None, int-coerced spinbox values, mode string, allowed list in canonical order); apply sets `_loading` first (try/finally), tolerates missing keys via `.get` + frozen defaults, selects the combo via `findData` with fallback index 0 + a `source_note` warning for non-empty unfound ids, shows the SAVED upload path in the label without restoring `_uploaded`, and encodes `demo_set_id == ''` as an empty combo selection (index -1) so apply(DEFAULTS)->collect is an identity through `validate_state`.
- **SMOKE-11 PART B extension (probe verdict PASS — cited 04-01-SUMMARY.md):** after the existing shell checks, `apply_state(dict(setup_state.DEFAULTS))` -> `collect_state()` asserted equal to `validate_state(dict(setup_state.DEFAULTS))` through the pure authority; the mutation drive (molecules 4, difficulty 2, block mode, h_bond + pi_stacking checked, upload toggle and back, combo re-select) asserted field-by-field; `demo_combo` carries userData `'demo-dev-1'`. **=== SMOKE-11 PASS ===, 15 checks, zero modals.**
- **Gates green:** `python3.6 -m py_compile aamatch/setup_window.py smoke/smoke_11_window.py` clean; 654/654 WSL tests (incl. purity gates, Gate A2, PROSE_PIN banned-token scan over setup_window.py — zero banned-token mentions, zero helper-visual call sites); source greps clean (no `from PyQt5`, no `.exec_(` calls, setRange/setValue reference setup_state attributes only).

## Task Commits

Each task was committed atomically:

1. **Task 1: source selector + demo dropdown + upload widgets** — `15cc00b` (feat)
2. **Task 2: spinboxes, mode radios + context label, 7 interaction checkboxes** — `115af6e` (feat)
3. **Task 3: collect/apply round-trip + SMOKE-11 form drive** — `6b8011e` (test)

**Plan metadata:** (see docs commit below)

## Files Created/Modified

- `aamatch/setup_window.py` (modified, 141 -> 513 lines) — the full 7-field form: 4 builders + `_populate_demo_sets` + `_current_mode`/`_on_mode_toggled` + `collect_state`/`apply_state` + `_INTERACTION_LABELS`/`_INTERACTION_TIPS`/`_MODE_CONTEXT` class constants + `_uploaded`/`_loading` instance slots; class docstring updated to describe the form.
- `smoke/smoke_11_window.py` (modified) — PART B extended with the round-trip and mutation-drive checks; header docstring updated; verdict marker logic unchanged (any part failing -> no PASS).

## Decisions Made

- **Empty demo_set_id encoded as combo index -1** (see Deviations): visible GUI state stays clean (empty selection = no restriction) and the plan's round-trip assert passes.
- **All checkboxes enabled in every mode** per the plan decision; per-type tooltips describe each interaction in game terms (spec UI standard).
- **The `toggled(bool)` -> stack-index edge:** a direct signal-to-slot wire would pass bool True as int 1, selecting the upload page when DEMO is checked; the lambda `0 if checked else 1` is required and commented.
- **`_population` runs once at construction** (plan Decision 16); the degrade path caught `Exception` (FormatError ⊂ ValueError plus any unexpected read failure) to satisfy "never crash the menu action".

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Empty demo_set_id could not round-trip with the plan's literal combo logic**
- **Found during:** Task 3 (collect/apply + SMOKE-11 extension)
- **Issue:** The plan's combo logic ("findData -> setCurrentIndex, fall back to index 0") leaves findData('') returning -1 -> index 0 ('demo-dev-1'), so `apply_state(DEFAULTS) -> collect_state()` yields demo_set_id 'demo-dev-1' and the plan's own smoke assert (`validate_state(collect) == validate_state(DEFAULTS)`) would FAIL.
- **Fix:** apply_state handles `set_id == ''` explicitly with `demo_combo.setCurrentIndex(-1)` (empty selection = no restriction; collect maps it back to '' via `currentData() or ''`). No synthetic combo item was invented (the plan's populate loop is verbatim); non-empty unfound ids keep the plan's fallback-index-0 + warning behavior.
- **Files modified:** `aamatch/setup_window.py`
- **Verification:** SMOKE-11 round-trip check PASS with `demo_set_id: ''` in the collected dump.
- **Committed in:** `6b8011e` (part of task commit)

**2. [Rule 1 - Bug] Accidental duplicate paste of the Task-1 builder methods during authoring**
- **Found during:** Task 1 (before commit)
- **Issue:** Two consecutive edits inserted `_build_source_selector`/`_populate_demo_sets` twice; the later definition would shadow the earlier, dead code.
- **Fix:** Removed the first copy, merged its demo_combo tooltip into the survivor.
- **Files modified:** `aamatch/setup_window.py`
- **Verification:** single definition (grep), py_compile + 654/654 WSL, SMOKE-11 PASS.
- **Committed in:** `15cc00b` (part of task commit — never reached the tree as a duplicate)

---

**Total deviations:** 2 auto-fixed (both Rule 1)
**Impact on plan:** Both necessary for correctness of the plan's own success assert and code hygiene; zero scope creep.

## Issues Encountered

None beyond the deviations above. The SMOKE-11 run printed the known benign offscreen Qt warnings (`QFontDatabase: Cannot find font directory`, `This plugin does not support propagateSizeHints()/raise()`) — the same cosmetic family recorded in 04-01/04-05.

## Authentication Gates

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **04-09..04-13 (handlers):** read the form via `dlg.collect_state()` and write it via `dlg.apply_state(...)` — both lossless and missing-key tolerant. The `_loading` flag exists for any valueChanged hooks a handler plan may add. Every button exists unconnected as `self.btn_reset`..`self.btn_start`.
- **04-10 (upload):** connect `self.btn_browse`, populate `self._uploaded = {'path': ..., 'sha256': ...}` and `self.upload_path_label` after ingest; collect already emits it.
- **04-09 (Reset/Randomize):** Reset = `self.apply_state(dict(setup_state.DEFAULTS))` (proven lossless in SMOKE-11); Randomize = apply of `setup_form.usable_randomized_state(...)` and reflects `source_mode='demo'`/`upload=None` back into the widgets for free.
- **Blockers:** none carried forward.

---
*Phase: 04-qt-setup-window*
*Completed: 2026-09-15*
