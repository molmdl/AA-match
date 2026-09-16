---
phase: 04-qt-setup-window
plan: 09
subsystem: qt-window handlers
tags: [pymol, pyqt5, qt, setup-window, handlers, guard-pattern, error-surfacing, persistence, smoke-test]

# Dependency graph
requires:
  - phase: 04-qt-setup-window/04-07
    provides: collect_state/apply_state lossless round-trip + _loading guard + the 7 unconnected spec-order buttons (btn_reset/btn_randomize/btn_save_setup/btn_load_setup)
  - phase: 04-qt-setup-window/04-02
    provides: setup_form.usable_randomized_state — the demo_set_id fix-up that kills the 'demo-%04x' trap
  - phase: 01-bootstrap-pure-foundation
    provides: persistence.save_setup_file/load_setup_file/read_json_file (versioned 'setup' container, FORMAT_VERSION=1), setup_state.DEFAULTS/validate_state, paths.to_windows_path
  - phase: 04-qt-setup-window/04-01
    provides: the offscreen probe verdict PASS — SMOKE-11 PART C parts RUN (T1b tier)
provides:
  - aamatch/setup_window.py — shared _guard (ValueError family + OSError -> modal-child QMessageBox.warning, unexpected exceptions propagate), Reset/Randomize/Save Setup/Load Setup handlers wired, _X_impl factoring (modal dialog wrappers + NON-MODAL impls)
  - smoke/smoke_11_window.py — PART C (T1b): C1 reset identity, C2 randomize usability + dropdown-id preservation, C3 save->reset->load round-trip of the versioned container
affects: [04-10..04-13 (every later handler reuses _guard and the _X_impl factoring), 04-14 checkpoint A (the four buttons are exercised interactively there — error surfacing verified by a human), 05+ (setup-file discipline is the window's persistence contract)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_guard(fn): catch ONLY (ValueError, OSError) -> QtWidgets.QMessageBox.warning(self, 'AA-match', str(e)) verbatim; every house refusal already names its cause; ANY other exception PROPAGATES (bug surfacing, never silent swallow — wizard.py:423-433 precedent)"
    - "_X_impl factoring: clicked signal -> thin dialog wrapper (_on_X: QFileDialog pick + _guard + success QMessageBox.information) -> NON-MODAL _X_impl that headless smokes drive directly (the smoke-99 probe receipt: a modal QMessageBox BLOCKS indefinitely under platform=offscreen)"
    - "Reset = apply_state(copy.deepcopy(setup_state.DEFAULTS)) — NEVER alias the module dict (the allowed list is mutable)"
    - "Randomize = apply_state(setup_form.usable_randomized_state(demo_set_id=<combo currentData or ''>)) — Decision 5 id preservation; apply_state reflects source_mode 'demo' + upload None automatically"

key-files:
  created: []
  modified: [aamatch/setup_window.py, smoke/smoke_11_window.py]

key-decisions:
  - "Extension auto-append on Save: any path not ending in '.aam.setup.json' gets it appended before to_windows_path routing (Decision 2, prior-art gui_setup.py:651-652)"
  - "Every disk path routes paths.to_windows_path — QFileDialog Windows paths pass through unchanged (the guard's documented behavior)"
  - "Success confirmation boxes live in the dialog WRAPPERS, gated on the impl's return value — impls stay modal-free (see Deviation 1)"
  - "Loaded 'upload' setups restore path/sha256 LABELS only; molecules are session-only and Start/Export refuse until re-ingested (documented caveat; 04-10 wires the refusal)"

patterns-established:
  - "_guard is THE error-surfacing contract for all 7 setup buttons (04-10..04-13 reuse it unchanged)"
  - "Headless drives call _X_impl methods only; smoke scripts remain P5-clean (no .exec_(), no QFileDialog, no QMessageBox)"

# Metrics
duration: 49min
completed: 2026-09-16
---

# Phase 4 Plan 09: Setup-Window Button Handlers Summary

**All four SETUP-07 buttons are wired with the phase-wide error-surfacing contract: a shared `_guard` maps the ValueError family (FormatError/GenerationError/EngineError/PlacementError/WizardError) plus OSError onto a modal-child `QMessageBox.warning` showing `str(e)` verbatim while unexpected exceptions propagate as bugs (wizard.py:423-433 precedent); Reset applies a deep-copied frozen DEFAULTS, Randomize produces a usable configuration via `setup_form.usable_randomized_state` preserving the current dropdown selection (Decision 5 — the 'demo-%04x' trap is structurally dead), and Save/Load round-trip the versioned 'setup' container through `persistence.save_setup_file`/`load_setup_file` with `.aam.setup.json` extension auto-append and `to_windows_path` routing on every disk path. Handlers follow the `_X_impl` factoring (modal wrapper + non-modal impl) proven headlessly by SMOKE-11 PART C: 688/688 WSL tests green, === SMOKE-11 PASS === (21 checks incl. C1 reset identity, C2 randomize usability + id preservation, C3 save->reset->load round-trip).**

## Performance

- **Duration:** ~49 min
- **Started:** 2026-09-16T18:03:51Z
- **Completed:** 2026-09-16T18:53:23Z
- **Tasks:** 3/3
- **Files modified:** 2 (0 created)

## Accomplishments

- **`_guard` — the shared error-surfacing helper (setup_window.py:510-521):** catches exactly `(ValueError, OSError)` and shows `QtWidgets.QMessageBox.warning(self, 'AA-match', str(e))` (modal CHILD — legal, PITFALL 4; every house refusal already names its cause per the research error_surfacing inventory). Anything else propagates: a bug is never silently swallowed. All later handler plans (04-10 through 04-13) reuse this verbatim.
- **Reset + Randomize (Task 1):** `_reset_impl` = `apply_state(copy.deepcopy(setup_state.DEFAULTS))` — a literal `import copy` deep copy, never an alias of the module dict (the `allowed_interactions` list is mutable; research SETUP-07 seam). `_randomize_impl` reads `str(self.demo_combo.currentData() or '')`, calls `usable_randomized_state(demo_set_id=current)` and applies the result — `source_mode 'demo'` and `upload None` reflect back into the widgets for free, and the randomizer's synthetic `'demo-%04x'` id can never reach Start.
- **Save/Load Setup (Task 2):** `_on_save_setup`/`_on_load_setup` are the modal dialog wrappers (QFileDialog save/open pickers with the `'AA-match Setup (*.aam.setup.json);;All Files (*)'` filter, then `_guard(lambda: _X_impl(path))`, then a success `QMessageBox.information` gated on the impl's return path). `_save_setup_to` auto-appends the extension (Decision 2, prior-art gui_setup.py:651-652), routes through `paths.to_windows_path`, and relies on `persistence.save_setup_file`'s validate-on-save; `_load_setup_from` relies on `load_setup_file`'s validate-on-load (the 4 FormatError refusal classes — foreign/newer/misfiled/unparseable — arrive with user-facing messages _guard shows verbatim) and applies the validated state. Both impls are NON-MODAL and return the final path so wrappers can confirm. The upload-labels-only caveat (session-only molecules; 04-10 wires the Start/Export refusal) is documented in `_load_setup_from`'s docstring.
- **SMOKE-11 PART C (Task 3, T1b under the 04-01 PASS verdict — cited 04-01-SUMMARY.md):** C1 — after the PART-B mutation drives left the form perturbed, `_reset_impl()` restores `collect_state() == validate_state(dict(setup_state.DEFAULTS))` exactly. C2 — with the dropdown at `'demo-dev-1'`, `_randomize_impl()` yields a `validate_state`-stable state with `source_mode 'demo'`, `upload None`, and `demo_set_id == 'demo-dev-1'` (Decision 5; the trap string never appears). C3 — widgets mutated to 4/2 + block_exclusive + h_bond only, `_save_setup_to(tmp)` writes a container asserted `kind == 'setup'`, `version == 1` via `persistence.read_json_file`; `_reset_impl()` wipes the form; `_load_setup_from(tmp)` restores the mutated dict exactly; temp file removed. Old Gate A2 echo relettered PART D. **=== SMOKE-11 PASS ===, 21 checks, zero modals.**
- **Gates green:** `python3.6 -m py_compile aamatch/*.py` clean; 688/688 WSL tests (incl. purity gates, Gate A2 untouched — setup_window.py stays Qt-tier, AST-gated only); static greps: one `except (ValueError, OSError)` clause, 3 `to_windows_path` call sites, extension auto-append present, zero PROSE_PIN banned tokens, zero `from PyQt5`.

## Task Commits

Each task was committed atomically:

1. **Task 1: _guard + Reset + Randomize handlers** — `a8ae554` (feat)
2. **Task 2: Save Setup + Load Setup handlers** — `392b750` (feat)
3. **Task 3: SMOKE-11 PART C setup-button drives** — `d1a00d3` (test)

**Plan metadata:** (see docs commit below)

## Files Created/Modified

- `aamatch/setup_window.py` (modified, 513 -> 641 lines) — `_guard`, `_on_reset`/`_reset_impl`, `_on_randomize`/`_randomize_impl`, `_on_save_setup`/`_save_setup_to`, `_on_load_setup`/`_load_setup_from`; all four SETUP-07 buttons connected at construction.
- `smoke/smoke_11_window.py` (modified, 219 -> 307 lines) — new PART C (T1b, 5 checks) with lazy imports; docstring updated; old PART C (Gate A2 echo) relettered PART D; verdict marker logic unchanged.

## Decisions Made

- **Extension auto-append (plan Decision 2)** implemented in `_save_setup_to` before path routing; the plan's filter string `'AA-match Setup (*.aam.setup.json);;All Files (*)'` used verbatim on both pickers.
- **Combo selection preserved on randomize (plan Decision 5)** via `str(self.demo_combo.currentData() or '')` — empty selection (placeholder/index -1) maps to `''` = all sets.
- **Impls stay modal-free; wrappers own ALL boxes.** The `_X_impl` factoring rule from the plan objective is the binding constraint (see Deviation 1): smokes drive impls directly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Success QMessageBox moved out of the impls into the dialog wrappers**
- **Found during:** Task 2 (before running Task 3; settled by an empirical probe)
- **Issue:** The plan's Task 2 places the success `QMessageBox.information` inside `_save_setup_to`/`_load_setup_from`, while Task 3 drives those same impls headlessly demanding "NO modals". A one-off offscreen probe (`smoke_99_qmsgbox.py`, run + removed) proved the contradiction is BLOCKING: under `platform=offscreen` a static QMessageBox opens a modal event loop nothing ever closes — PyMOL printed `before box` and hung until the 60s timeout killed it (`after box` never printed).
- **Fix:** `_save_setup_to`/`_load_setup_from` are NON-MODAL and return the final path; `_on_save_setup`/`_on_load_setup` show the identical success text (`'Setup saved to %s'` / `'Setup loaded from %s'`) gated on the impl returning non-None (a caught error means `_guard` already warned and returned None — no false "saved" box). Interactive behavior is unchanged; the rest of the plan (extension auto-append, to_windows_path routing, validate-on-save/load, _guard wrapping) is verbatim.
- **Files modified:** `aamatch/setup_window.py`
- **Verification:** SMOKE-11 PART C3 round-trip green with zero modals in 17s of PyMOL time; py_compile + 688/688 WSL.
- **Committed in:** `392b750` (part of task commit)

---

**Total deviations:** 1 auto-fixed (Rule 3)
**Impact on plan:** Resolves an internal contradiction between Task 2's literal success-box placement and Task 3's no-modals drive; strengthens the plan's own `_X_impl` factoring rule ("dialog wrapper + non-modal logic"). The smoke-99 receipt (modal boxes BLOCK under offscreen) is now load-bearing knowledge for 04-10..04-13 handler plans.

## Issues Encountered

None beyond the deviation above. SMOKE-11 printed the known benign offscreen Qt warnings (`QFontDatabase: Cannot find font directory`, `This plugin does not support propagateSizeHints()/raise()`) — the cosmetic family already recorded in 04-01/04-05/04-07. The warned sibling-worktree SMOKE-12 overlap never materialized as a failure (SMOKE-11 passed first attempt).

## Authentication Gates

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **04-14 checkpoint A** (the affects target): all four SETUP-07 buttons are interactively exercisable — Reset restores the frozen defaults visibly; Randomize always yields a usable config pinning the chosen demo set; Save/Load round-trip `.aam.setup.json` through real QFileDialogs; error surfacing (wrong-kind file, hand-corrupted JSON, unwritable directory) shows the verbatim refusal in a warning box — this is the human-verify tier the headless smoke deliberately never drove.
- **04-10 (upload Browse):** reuse `_guard` + the `_X_impl` factoring unchanged; the loaded-upload caveat in `_load_setup_from` documents that Start/Export must refuse via `build_state`'s `upload_ready` pre-check until re-ingested.
- **04-11..04-13:** `_guard` is the contract; every disk path routes `to_windows_path`; impls stay modal-free so the smoke tier can drive them.
- **Blockers:** none carried forward.

---
*Phase: 04-qt-setup-window*
*Completed: 2026-09-16*
