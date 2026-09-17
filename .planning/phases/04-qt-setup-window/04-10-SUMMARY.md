---
phase: 04-qt-setup-window
plan: 10
subsystem: qt-window handlers
tags: [pymol, qt, qfiledialog, sdf, mol2, upload, gui, session-slot, sha256, smoke]

# Dependency graph
requires:
  - phase: 04-qt-setup-window (04-08)
    provides: upload.prepare_uploaded_set cmd-tier extraction bridge (rows + ligand_content)
  - phase: 04-qt-setup-window (04-06)
    provides: game_file pure upload surface (read_upload_source/split/check_upload_supply)
  - phase: 04-qt-setup-window (04-09)
    provides: _guard error-surfacing contract + _X_impl non-modal factoring rule
  - phase: 04-qt-setup-window (04-07)
    provides: 7-field form + collect/apply round-trip + session-only _uploaded slot
provides:
  - SetupWindow._on_browse_upload (single-select QFileDialog -> _guard wrapper)
  - SetupWindow._ingest_upload(path) -> int: pure read/split/cap -> cmd-tier prepare -> session _uploaded slot + widget reflection (replace-on-new-upload)
  - SetupWindow.upload_ready_for(form_values) -> bool: the build_state upload_ready pre-check input
  - apply_state upload tooltip carries the saved FILE sha256 (Load restores labels only)
  - SMOKE-11 PART D: headless ingest drive on bundled benzamide.sdf (11 checks)
affects: [04-12 export, 04-13 start, 04-15 checkpoint B]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Upload ingest pipeline in ONE non-modal impl: pure read_upload_source -> split by fmt -> check_upload_supply(cap 50) -> upload.prepare_uploaded_set -> session slot + widget reflection"
    - "upload_ready_for semantics: True iff source_mode != 'upload' OR session slot matches form upload path AND FILE sha256 (stale Load labels are NOT startable)"

key-files:
  created: []
  modified: [aamatch/setup_window.py, smoke/smoke_11_window.py]

key-decisions:
  - "Decision 9 enforced: single-select QFileDialog.getOpenFileName; the frozen upload field {'path','sha256'} wins; multi-file = schema change (version-bump event)"
  - "Ingested rows/content live ONLY in the session (self._uploaded); setup files persist path+sha256 labels; a new Browse REPLACES the slot (single slot v1)"
  - "No success QMessageBox after ingest: the widget reflection (upload page switch + path label with record count) IS the confirmation"

patterns-established:
  - "Upload-ready pre-check plumbing: handlers (04-12/04-13) call upload_ready_for(collect_state()) and pass it to pure build_state so un-ingested upload configs refuse BEFORE any scene-touching call"

# Metrics
duration: 7 min
completed: 2026-09-17
---

# Phase 4 Plan 10: Upload Button Handler + SMOKE-11 PART D Summary

**The Browse button is wired end-to-end (SETUP-03 form side): single-select QFileDialog -> _guard -> non-modal _ingest_upload that runs pure read/split/cap -> cmd-tier prepare_uploaded_set into the session-only _uploaded slot with widget reflection, plus the upload_ready_for pre-check that lets build_state refuse un-ingested upload configs before touching the scene — SMOKE-11 PASS with the 11-check PART D ingest drive on the bundled benzamide SDF.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-17T03:22:33Z
- **Completed:** 2026-09-17T03:29:22Z
- **Tasks:** 3
- **Files modified:** 2 (aamatch/setup_window.py, smoke/smoke_11_window.py)

## Accomplishments

- `_on_browse_upload` + `_ingest_upload(path) -> int` (setup_window.py, +68 lines): single-select `getOpenFileName` (Decision 9 — the frozen `upload = None | {'path','sha256'}` shape wins); the impl chains the proven helpers in order — `game_file.read_upload_source(to_windows_path(path))` (extension whitelist + utf-8 + FILE sha256, Decision 19) -> `split_sdf_records`/`split_mol2_segments` -> `check_upload_supply` (cap 50 + degenerate refusals naming the basename) -> `upload.prepare_uploaded_set(records, fmt)` (04-08 per-record temp discipline; scene residue asserted per record). The session slot `self._uploaded` carries rows + ligand_content + path/FILE-sha256/fmt; a new upload REPLACES it. Widget reflection: `src_upload.setChecked(True)` (switches the stack), path label `'%s (%d molecule record(s))'` + full-path tooltip. NON-MODAL by the smoke-99 receipt; _guard surfaces every (ValueError, OSError) refusal verbatim (incl. the pinned MOL2 refusal messages). EXT-04 depth NOT built (fail-closed minimum).
- `upload_ready_for(form_values) -> bool`: True iff `source_mode != 'upload'` OR the session slot matches the form's upload path AND FILE sha256 — Load-restored labels alone are never startable. Docstring hands 04-12/04-13 the exact call: `upload_ready=self.upload_ready_for(self.collect_state())` into pure `build_state`, whose fatal pre-check refuses BEFORE any scene-touching call. `apply_state` now carries the saved FILE sha256 in the upload label tooltip.
- SMOKE-11 PART D (T1b — the 04-01 probe verdict is PASS (platform=offscreen), `.planning/phases/04-qt-setup-window/04-01-SUMMARY.md`; success paths only, ZERO modals): repo-anchored `aamatch/data/ligands/benzamide.sdf` -> `_ingest_upload` returns 1; slot has 1 row (`entry_id 'mol-001'`, `file 'uploads/mol-001.sdf'`), content dict keyed by that file, sha256 == sha256 of the file bytes; form reflects upload mode (radio + stack page 1); `collect_state()['upload']` matches path + FILE sha256; re-ingest replaces the slot (still 1 row); `upload_ready_for` verdict matrix — own collect_state True, stale-sha256 config False, emptied slot False, demo page True. Cleanup restores `_uploaded=None` + demo page. The existing Gate A2 echo was renumbered PART D -> PART E.

## Task Commits

Each task was committed atomically:

1. **Task 1: _on_browse_upload + _ingest_upload** — `077e70d` (feat)
2. **Task 2: collect_state/upload_ready integration** — `fbd65eb` (feat)
3. **Task 3: SMOKE-11 PART D ingest drive** — `5db4ef1` (test)

**Plan metadata:** `<see final docs commit>` (docs: complete plan)

## Files Created/Modified

- `aamatch/setup_window.py` — upload ingestion handler (single-select picker + non-modal impl), `upload_ready_for`, apply_state sha256 tooltip, btn_browse connected in __init__. QT tier (never PURE_MODULES, never WSL-imported; AST source gates only).
- `smoke/smoke_11_window.py` — SMOKE-11 PART D: 11-check headless upload-ingest drive; Gate A2 echo renumbered to PART E.

## Decisions Made

- **(04-10, Decision 9 binding)** Single-select Browse: `QFileDialog.getOpenFileName` with filter `'Molecule files (*.sdf *.mol2);;All Files (*)'`. Multi-file upload would change the frozen `upload` field shape — a schema version-bump event, deliberately not taken. One multi-record SDF still yields several molecules (spec.md:14).
- **(04-10)** No success QMessageBox after a successful ingest: the form reflection (upload page switch + path label with record count) is the confirmation; impls never own boxes (04-09 smoke-99 receipt) and the wrapper adds no box either (unlike Save/Load whose confirmation is off-screen state the user cannot otherwise see).
- **(04-10)** `upload_ready_for` compares BOTH path and FILE sha256 of the session slot against the form block — a setup-file Load with matching labels but no session molecules returns False, which is exactly build_state's refusal trigger (plan-decision 3 verbatim).

## Deviations from Plan

None — plan executed exactly as written. (The smoke's Gate A2 part renumbering PART D -> PART E is the plan-mandated PART D name landing in a file that already had a PART D; behavior of the old part is unchanged.)

## Authentication Gates

None.

## Verification Evidence

- T0: `python3.6 -m py_compile aamatch/*` green; full WSL suite 688/688 green.
- T1b (probe-PASS): `bash smoke/run_smoke.sh smoke/smoke_11_window.py 120` prints `=== SMOKE-11 PASS ===` (PART D 11/11 checks green; parts A/B/C/E unchanged and green).
- Static: single getOpenFileName call site for Browse (+ docstring mention); to_windows_path routing on the ingest path; pure helpers + prepare_uploaded_set called in plan order; no candidate-row fabrication in the window; zero banned-token mentions in setup_window.py (get_model/matrix_reset/get_object_ttt absent); no `from PyQt5`.

## Next Phase Readiness

- **Sequencing check CLOSED (ROADMAP criterion 2):** the upload seam chain 04-04 -> 04-06 -> 04-08 -> 04-10 is complete before the checkpoints; uploads ingest INTO the engine's existing candidates/ligand_content pipe.
- **04-12 (export) / 04-13 (start):** consume `self._uploaded['rows']` + `self._uploaded['content']` as `candidates=`/`ligand_content=` and pass `upload_ready=self.upload_ready_for(self.collect_state())` into `setup_form.build_state` — the refusal for un-ingested upload configs is then mechanical.
- **04-15 checkpoint B:** the human-verify story now includes Browse -> ingest -> form reflection in the GUI.
