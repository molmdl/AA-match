---
phase: 04-qt-setup-window
verified: 2026-09-18T12:30:00Z
status: passed
score: 58/58 plan must-have truths verified (15/15 plans)
---

# Phase 4: Qt Setup Window — Verification Report

**Phase Goal:** From the Plugins menu the user gets a modeless setup window from which they can configure everything, save/load setups, export a shareable game, clean up the model, and start playing.
**Verified:** 2026-09-18 (initial verification — no previous VERIFICATION.md existed)
**Status:** PASSED
**Method:** Goal-backward, code-first. Every must-have from every 04-NN-PLAN.md frontmatter was checked against the ACTUAL codebase (existence → substantive → wired), all gates re-run live in this session, and the recorded human verdicts cross-referenced. SUMMARY claims were not trusted; code was read.

---

## 1. Live Gate Results (all run in this verification session)

| Gate | Command | Result |
|------|---------|--------|
| Gate D — syntax floor | `python3.6 -m py_compile aamatch/*.py` | **PASS** — all modules compile under the 3.6 floor |
| WSL suite | `python3.6 -m unittest discover -s tests` | **PASS — 688 tests, OK** (includes purity Gate A, Gate A2, code audit, AST seam contracts; perf guard 0.670 s < 2.0 s) |
| SMOKE-08 | `bash smoke/run_smoke.sh smoke/smoke_08_starter.py 240` | **PASS** — `=== SMOKE-08 PASS ===` (re-pointed to `gamestart.start_game()` directly; 31 checks intact; teardown restores scene exactly) |
| SMOKE-09 (probe) | `bash smoke/run_smoke.sh smoke/smoke_09_qt_probe.py 240` | **PASS** — `=== PROBE PASS (platform=offscreen) ===` + `=== SMOKE-09 PASS ===` |
| SMOKE-10 | `bash smoke/run_smoke.sh smoke/smoke_10_upload_flow.py 240` | **PASS** — synthetic upload row flows new_game→materialize→start_game; fail-closed EngineError proven; baseline restored |
| SMOKE-11 | `bash smoke/run_smoke.sh smoke/smoke_11_window.py 300` | **PASS — 46 checks, 0 FAIL** (parts A–H: import proof; construct/reuse/close-reopen same instance; reset/randomize/save/load; upload ingest; cleanup exact restore; export round-trip; real Start + seed replay + reuse guard; Gate A2 shape) |
| SMOKE-12 | `bash smoke/run_smoke.sh smoke/smoke_12_upload_e2e.py 300` | **PASS** — read_sdfstr parity proven live (atom/state/bond-order/charge identical); upload pipeline rows+content; multi-segment MOL2 fail-closed refusal pinned verbatim |

---

## 2. Must-Have-by-Must-Have Verification (per plan, 58 truths)

### 04-01 — offscreen-Qt probe (3/3 ✓)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| Probe verdict recorded, no TBD | ✓ VERIFIED | Live: `=== PROBE PASS (platform=offscreen) ===`; verdict recorded in 04-01-SUMMARY |
| Probe opens zero modals | ✓ VERIFIED | Headless run completes without hanging (a modal would trip the 240 s backstop) |
| Later plans reference a definite verdict | ✓ VERIFIED | 04-05..04-13 SUMMARYs cite the verdict; SMOKE-11/12 T1b parts construct widgets live |

Artifact `smoke/smoke_09_qt_probe.py`: EXISTS, SUBSTANTIVE (118 ≥ 40 lines), WIRED (drives `pymol.Qt` shim per the plan's key-link pattern; SMOKE-11/12 T1b tiers depend on its verdict).

### 04-02 — setup_form pure helpers (4/4 ✓)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| build_state refuses the 3 doomed configs pre-scene-touch | ✓ VERIFIED | setup_form.py:82–87 (upload w/o ready), :89–93 (unknown demo set), :98–108 (empty-allowed in exclusive/block_exclusive, on the NORMALIZED state) |
| Output is exactly a validate_state-normalized 7-field state | ✓ VERIFIED | :95–96 builds a fresh `_SCHEMA_KEYS` dict → validate_state (pure layer stays the sole validation authority); SMOKE-11 C2 live |
| usable_randomized_state kills the 'demo-%04x' trap | ✓ VERIFIED | :112–121 overwrites demo_set_id with a real id / ''; test_synthesized_id_never_survives pins it; SMOKE-11 C2 PASS live |
| manifest_sets = dropdown rows, no I/O | ✓ VERIFIED | :124–136 pure data-in/data-out; imported by setup_window.py:300 |

Artifacts: `aamatch/setup_form.py` EXISTS (136 ≥ 60), SUBSTANTIVE (all functions real, no stubs), WIRED (PURE_MODULES registered at tests/test_purity.py:95; imported by setup_window.py). `tests/test_setup_form.py` EXISTS (258 ≥ 60; 18 test methods covering every refusal + identity + fix-up determinism + manifest shape).

### 04-03 — game_file core (4/4 ✓)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| Round-trip: same setup, byte-identical embedded spec, sha256-matched ligand texts | ✓ VERIFIED | make_game_data (:90) embeds payload VERBATIM; parse_game_data (:120) re-runs parse_level_spec_dict(make_level_spec_container(...)) — ALL Phase-1 gates incl. exact-match detector_version (:77, :151–152); SMOKE-11 F live: "seed 4242 round-trip" |
| Every refusal class with clear FormatError | ✓ VERIFIED | check_container reuse (:78, :130); foreign/newer/misfiled/missing/stale-detector/sha256 branches all present (tests: 56 test methods, 823 lines ≥ 120) |
| Single meaning per source: upload ⇒ ligand_files, demo ⇒ none | ✓ VERIFIED | encode/decode_ligand_files (:167/:179); SMOKE-11 F live: "ligand_texts {} (demo)"; upload-only embedding enforced in export_game |
| detector_version NEVER mirrored in game header | ✓ VERIFIED | make_game_data returns EXACTLY game_format_version/created_at/generator/setup/seed/level_spec/ligand_files (:104–112, docstring "NO detector_version") |

Artifacts: `aamatch/game_file.py` EXISTS (487 ≥ 120), SUBSTANTIVE, WIRED (persistence check_container/FormatError; level_spec re-embed; PURE_MODULES + 'base64' whitelisted in tests/test_purity.py:95/:108).

### 04-04 — ligand_content pipe (3/3 ✓)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| All 4 seams accept ligand_content=None, byte-identical when None | ✓ VERIFIED | engine.py:144/:230/:294, placement.py:234, gamestart.py:285 — additive params, defaults None; SMOKE-10 "bundled bare start_game works (pre-04-04 default callers untouched)" live |
| Synthetic row + content flows through all three headlessly | ✓ VERIFIED | SMOKE-10 live ALL-PASS: synthetic 'uploads/mol-001.sdf' row → new_game → materialize (16/16 atoms) → start_game (wizard carries the payload) |
| Synthetic key WITHOUT content fails closed | ✓ VERIFIED | engine.py:170/:203; SMOKE-10 live: "missing content fails closed EngineError", "scene unchanged after refusal" |

Artifacts: 4 seam files EXISTS/SUBSTANTIVE/WIRED; `smoke/smoke_10_upload_flow.py` EXISTS (306 lines), run live PASS.

### 04-05 — Qt window shell + menu rewire (5/5 ✓)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| Modeless open_window; Gate A2 zero module-level imports | ✓ VERIFIED | setup_window.py:63–77 (show/raise_/activateWindow — NEVER exec_); `__init__.py` verified by reading: only lazy function-body imports; AST contract pinned by test_package_skeleton.py:114–149; Gate A2 smoke check live (SMOKE-11 part H: offenders=[]) |
| Double menu fire reuses the SAME dialog; _window singleton; NO closeEvent | ✓ VERIFIED | :60–77 module-scope `_window`; no closeEvent anywhere in aamatch/ (grep: docstring mentions only); SMOKE-11 part B live: "second open_window reuses the SAME dialog" + "close()+re-open is STILL the same instance" |
| run_plugin_gui AST contract REPLACED | ✓ VERIFIED | `from . import setup_window` + `return setup_window.open_window()` (__init__.py:38–39); pinned by test |
| SMOKE-08 re-pointed to start_game; all 31 checks preserved | ✓ VERIFIED | smoke_08 docstring + call sites use `aamatch.gamestart.start_game()`; live run: `=== SMOKE-08 PASS ===` (31 checks; 34 PASS-marked lines incl. markers) |
| Qt NEVER in PURE_MODULES; no WSL-test imports | ✓ VERIFIED | tests/test_purity.py PURE_MODULES lacks setup_window; no test imports it; T0 AST gates only (test_wizard_source.py:52 scans 'setup_window.py') |

Artifact `aamatch/setup_window.py`: EXISTS (944 ≥ 80), SUBSTANTIVE, WIRED (imported lazily by run_plugin_gui). `smoke/smoke_11_window.py` EXISTS (703 ≥ 40), live PASS.

### 04-06 — game_file upload helpers (4/4 ✓)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| SDF multi-record + MOL2 multi-segment splits, pure | ✓ VERIFIED | split_sdf_records (:268), split_mol2_segments (:301); SMOKE-12 live: "combined text splits into 2 records" + "mol2 probe splits into 2 segments (leading comment attaches to segment 1)" |
| Supply checks refuse zero/degenerate/over-cap | ✓ VERIFIED | check_upload_supply (:328) + UPLOAD_MAX_RECORDS=50 (:87); SMOKE-12 live supply checks |
| read_upload_source: (text, sha256, format); other extensions refused | ✓ VERIFIED | :359; SDF/MOL2 whitelist; PDB excluded; FormatError family |
| build_uploaded_row 14-key manifest-shaped row + validate_uploaded_rows | ✓ VERIFIED | :387/:446; validate reuses manifest._check_entry (:486 — single home); _candidate_class reused from generator (:76) |

### 04-07 — full 7-field form (4/4 ✓)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| Full form: 2-page selector, spinboxes from frozen constants, 3-way mode + context label, 7 canonical checkboxes, tooltips | ✓ VERIFIED | Read in full: _build_source_selector (:220, radios + QStackedWidget, demo dropdown + Browse/path label), _build_spinboxes (:356 — ranges from setup_state.MOLECULES_/DIFFICULTY_ constants, zero literals), _build_mode_group (:388, 3 radios + context label restating mode meaning), _build_interactions (:439, canonical INTERACTION_TYPES order), every widget tooltipped |
| collect/apply lossless round-trip; apply tolerates missing keys; _loading guard | ✓ VERIFIED | collect_state (:462–485), apply_state (:487–572, .get defaults + _loading guard); SMOKE-11 B live: apply(DEFAULTS)→collect round-trips |
| Dropdown from bundled MANIFEST.json (engine read shape); FormatError degrades to placeholder+warning | ✓ VERIFIED | _populate_demo_sets (:283–310): read_json_file + parse_manifest_dict + paths.package_data_path; except → placeholder item + visible source_note |
| No widget-side re-validation; spinbox ranges == clamp ranges | ✓ VERIFIED | collect emits raw values; ranges set from the same frozen constants validate_state clamps with (:369–371, :378–380) |

### 04-08 — upload.py + SMOKE-12 (4/4 ✓)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| prepare_uploaded_set: rows+content, temp-load per record, zero residue | ✓ VERIFIED | upload.py:72 with `cmd.get_unused_name('_aam_tmp')` (:125) + delete-in-finally; SMOKE-12 live: "prepare leaves scene at baseline" + "new_game incl. uploaded candidates leaves scene untouched" |
| read_sdfstr/read_mol2str parity proven in this build | ✓ VERIFIED | SMOKE-12 live parity block ALL-PASS: atom 7=7, states 1=1, bond-order multiset [1,1,1,1,1,2]=[1,1,1,1,1,2], charge −1=−1 |
| 2-segment MOL2 probed; fail-closed rule applies | ✓ VERIFIED | SMOKE-12 live: refusal pinned VERBATIM — "upload 'smoke12-2seg-probe.mol2' carries 2 MOL2 molecules -- this build accepts single-molecule MOL2 files only"; scene stays clean |
| Only the fail-closed minimum (no EXT-04) | ✓ VERIFIED | format whitelist + split + single-state + count + sha256 + manifest-shaped row; no extra machinery |

Artifact `aamatch/upload.py`: EXISTS (172 ≥ 60), SUBSTANTIVE, WIRED (game_file pure helpers; engine._remap_ligand_bonds; cmd string readers).

### 04-09 — SETUP-07 buttons (4/4 ✓)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| Reset restores DEEP-COPIED DEFAULTS | ✓ VERIFIED | _reset_impl (:612–622): `apply_state(copy.deepcopy(setup_state.DEFAULTS))`; SMOKE-11 C1 live |
| Randomize = usable_randomized_state, current dropdown preserved | ✓ VERIFIED | _randomize_impl (:628–641); Decision 5; SMOKE-11 C2 live (validate_state-stable, demo preserved) |
| Save/Load via persistence + extension auto-append | ✓ VERIFIED | _save_setup_to (:660–677) → save_setup_file + to_windows_path + '.aam.setup.json'; _load_setup_from (:694–713) → load_setup_file + apply_state; SMOKE-11 C3 live |
| _guard surfaces ValueError-family; unexpected propagates | ✓ VERIFIED | _guard (:596–606): except (ValueError, OSError) → QMessageBox.warning(self, ...); no bare except |

### 04-10 — upload button (4/4 ✓)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| Browse single-select; ingest fills session slot | ✓ VERIFIED | _on_browse_upload (:717–735, getOpenFileName — Decision 9); _ingest_upload (:737–780) full pipeline; `self._uploaded` slot |
| Form reflects upload mode after ingest | ✓ VERIFIED | :776 src_upload.setChecked(True); two-line path label ('%s\n(%d molecule record(s))' — the 27e8f34 fix, CONFIRMED IN CODE); collect_state returns upload={'path','sha256'} FILE hash (:470–473) |
| Start/Export refuse upload-without-content BEFORE scene-touching | ✓ VERIFIED | upload_ready_for (:574–592) → build_state pre-check; handlers pass upload_ready (SMOKE-11 D live: ready/stale/empty/demo verdicts) |
| Second Browse REPLACES the slot; idempotent; scene clean | ✓ VERIFIED | slot overwrite (:774); temps deleted in finally (SMOKE-12 temp-discipline checks) |

### 04-11 — cleanup button (3/3 ✓)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| Cleanup removes ONLY _aam_* objects | ✓ VERIFIED | _cleanup_now → placement.cleanup_game_objects (prefix-only, returns {'deleted': n}) |
| GameWizard popped FIRST iff top-of-stack; user wizard never popped | ✓ VERIFIED | :798–800: `isinstance(cmd.get_wizard(), wizard.GameWizard)` gate + `cmd.set_wizard()` None-pop |
| Deleted count surfaced; adopted-ligand bookkeeping = zero workload | ✓ VERIFIED | _on_cleanup (:804–816) shows count incl. zero; recorded reading, no machinery built (matches the recorded placement.py:61–63 deferral) |

SMOKE-11 part E live: "start → _cleanup_now → exact-scene-restore", deleted=20, after=[] baseline=[].

### 04-12 — generate-and-export (4/4 ✓)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| Export writes versioned kind-'game' container atomically to .aamatch.json | ✓ VERIFIED | export_game (:80–111): engine.new_game full payload → game_file.make_game_data → persistence.save_container(to_windows_path(path), 'game', data); extension auto-append (:104–105); modal-child file dialog in _on_generate_export |
| Fresh random seed shown; _last_export stored | ✓ VERIFIED | :865 `random.randint(0, 2**31-1)`; summary line carries seed; :872–874 stores _last_export; SMOKE-11 G2 live: seed 31337 replayed |
| Export never materializes and never cleans | ✓ VERIFIED | export_game body: no cleanup/materialize/wizard calls (docstring + code verified) |
| Demo flow zero extra state; upload flow embeds ONLY uploaded molecules | ✓ VERIFIED | ligand_files = encode_ligand_files(content) iff content (:101–102); SMOKE-11 F live: "ligand_texts {} (demo)" |

### 04-13 — start button (4/4 ✓)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| Start builds state through build_state FIRST | ✓ VERIFIED | _start_impl (:911–916): collect → upload_ready → known_ids → build_state BEFORE start_game (which cleans first) — the ordering law holds structurally |
| Seed policy exactly as decided | ✓ VERIFIED | :917–923: reuse iff `last['setup'] == state` (both normalized) else fresh random; SMOKE-11 G1/G2/G3 live: real start, seed 31337 replay, reuse skipped when setup changed |
| Upload mode requires matching session content; refusal never deletes prior objects | ✓ VERIFIED | build_state raises inside _guard → start_game never runs → scene untouched; SMOKE-11 D stale/empty verdicts |
| Start is a THIN call to gamestart.start_game; no SETUP-11 pieces | ✓ VERIFIED | :931–933 single call; no Game tab/countdown/timer/Import/Hint anywhere in setup_window.py (grep clean) |

### 04-14 — checkpoint A: APPROVED (3/3 ✓)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| Modeless + survive-minimize/re-open (SETUP-01, criterion 1) | ✓ VERIFIED | 04-14-SUMMARY verdict table: steps 1–3 PASS — viewer fully interactive; SAME window raised, never duplicated |
| All form fields by hand + Reset/Randomize/Save/Load round-trip (SETUP-02..07, criteria 2–3) | ✓ VERIFIED | Steps 4–10 PASS; step-7 human note ruled EXPECTED BEHAVIOR under the frozen-defaults contract (recorded ruling) |
| Tooltips helpful; no helper visuals; window never blocks | ✓ VERIFIED | Steps 11–12 PASS; no-helper-visuals additionally enforced by the test_wizard_source.py AST gate (live green) |

### 04-15 — checkpoint B: APPROVED-WITH-FIX (5/5 ✓)

| Must-have | Status | Evidence |
|-----------|--------|----------|
| Export writes shareable .aamatch.json, seed shown, scene untouched (SETUP-08) | ✓ VERIFIED | Step 1 PASS — on-disk JSON: kind 'game', header version 1, detector_version 'det-1'; viewer unchanged |
| Cleanup removes only game objects incl. mid-game with live wizard (SETUP-09) | ✓ VERIFIED | Steps 2+4 PASS — user objects survive; GameWizard popped; exact restore |
| Start → playable wizard gameplay while window stays open (SETUP-10) | ✓ VERIFIED | Step 3 PASS — clicks/moves/score live in the wizard panel; step 8: double-Start restarts cleanly |
| Upload E2E by hand (SETUP-03 full path) | ✓ VERIFIED | Step 5 PASS-AFTER-FIX — benzamide.sdf ingested → playable game (seed 888026772); the cramped one-line label was the ONLY failure, human-prescribed two-line fix applied (commit 27e8f34, verified in git + in code), re-greened |
| Two cosmetic extensions human-confirmed | ✓ VERIFIED | Step 7 PASS — '.aam.setup.json' + '.aamatch.json' (+ default name 'game.aamatch.json') both CLOSED |

---

## 3. Roadmap Success-Criteria Coverage

| # | Criterion (all tagged [HUMAN]) | Status | Coverage |
|---|-------------------------------|--------|----------|
| 1 | SETUP-01 modeless window survives minimize/re-open | ✓ MET | Human 04-14 steps 1–3 (12/12 APPROVED) + machine: SMOKE-11 A/B + singleton/no-exec_ code |
| 2 | SETUP-02..06: dropdown, upload, spinboxes, mode, checkboxes | ✓ MET | Human 04-14 steps 4–6, 10 + machine: SMOKE-11 B/D, SMOKE-12, form code |
| 3 | SETUP-07 Reset/Randomize/Save/Load round-trip | ✓ MET | Human 04-14 steps 7–9 + machine: SMOKE-11 C1–C3 + persistence round-trip tests |
| 4 | SETUP-08/09/10: export, cleanup, Start → gameplay | ✓ MET | Human 04-15 steps 1–4, 6, 8 + machine: SMOKE-11 E/F/G |

All four ROADMAP criteria have [HUMAN] verdict coverage (A: criteria 1–3; B: criterion 4 + upload E2E + extension confirms).

## 4. Requirements Coverage (SETUP-01..10)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| SETUP-01 | ✓ SATISFIED | open_window modeless trio + singleton + human 04-14 |
| SETUP-02 | ✓ SATISFIED | _populate_demo_sets + manifest_sets + human step 4 (curated sets land Phase 8 per ROADMAP) |
| SETUP-03 | ✓ SATISFIED (via SDF; see recorded-facts note) | read_upload_source whitelist + pipeline + human 04-15 step 5 |
| SETUP-04 | ✓ SATISFIED | molecules_spin (1..10, default 2 from frozen constants) + human step 5 |
| SETUP-05 | ✓ SATISFIED | difficulty_spin (3..5, default 3) + human step 5 |
| SETUP-06 | ✓ SATISFIED | 3-way mode + 7 checkboxes + human step 6 |
| SETUP-07 | ✓ SATISFIED | 4 handlers + versioned save/load + human steps 7–9 |
| SETUP-08 | ✓ SATISFIED | export_game + make_game_data + human 04-15 step 1 |
| SETUP-09 | ✓ SATISFIED | _cleanup_now prefix-only + human 04-15 steps 2/4 |
| SETUP-10 | ✓ SATISFIED | _start_impl thin seam + human 04-15 steps 3/6 |

## 5. Anti-Pattern Scan (phase-touched files)

| Scan | Result |
|------|--------|
| TODO/FIXME/XXX/HACK | **ZERO** across all 17 phase-touched files |
| Placeholder/coming-soon text | ZERO |
| Empty returns / `=> ()` handlers | Only documented-legitimate: setup_form.py:132 `return []` (empty-manifest contract, docstring + tests pin it) |
| console.log/print noise | ZERO in aamatch modules (print-free Qt tier per house rule) |
| `from PyQt5` (banned repo-wide) | ZERO (only test_purity.py gate docstrings mention the string) |
| `exec_()` on the main window | ZERO (docstring states the modeless contract; only child dialogs may be modal) |
| closeEvent overrides | ZERO (deliberate; the re-open mechanism IS the singleton reuse) |
| sys.modules stubs in tests | ZERO (enforced by test_purity.py, live green) |

## 6. Key Link Verification (the seams where stubs hide)

| From | To | Via | Status |
|------|----|-----|--------|
| `__init__.py` run_plugin_gui | setup_window.open_window | lazy relative import (Gate A2) | ✓ WIRED (AST-contract-tested + SMOKE-11 A) |
| SetupWindow | setup_state frozen constants | lazy import; spinbox ranges mirror clamps | ✓ WIRED (lossless round-trip proven) |
| SetupWindow | setup_form.manifest_sets / build_state / usable_randomized_state | lazy imports in _populate_demo_sets/_export_game_to/_start_impl/_randomize_impl | ✓ WIRED (SMOKE-11 B/C2/F/G) |
| SetupWindow _save/_load_setup_to | persistence save_setup_file/load_setup_file + paths.to_windows_path | validate-on-save/load containers | ✓ WIRED (SMOKE-11 C3) |
| SetupWindow _ingest_upload | game_file read/split/supply + upload.prepare_uploaded_set | pure + cmd-tier chain | ✓ WIRED (SMOKE-11 D + SMOKE-12) |
| SetupWindow _cleanup_now | placement.cleanup_game_objects + wizard.GameWizard isinstance gate | pop-first then prefix-only delete | ✓ WIRED (SMOKE-11 E) |
| SetupWindow export_game | engine.new_game → game_file.make_game_data/encode_ligand_files → persistence.save_container | full payload → atomic versioned write | ✓ WIRED (SMOKE-11 F) |
| SetupWindow _start_impl | setup_form.build_state → gamestart.start_game | pre-checks BEFORE the scene-touching seam | ✓ WIRED (SMOKE-11 G) |
| engine/placement/gamestart | cmd.read_sdfstr/read_mol2str string loads | ligand_content threading, fail-closed | ✓ WIRED (SMOKE-10 + SMOKE-12) |
| game_file | persistence check_container/FormatError + level_spec re-embed + manifest._check_entry + generator._candidate_class | refusal-class + rule reuse (single homes) | ✓ WIRED (imports verified; 688 tests green) |
| tests/test_purity.py | setup_form + game_file | PURE_MODULES + base64 whitelist | ✓ WIRED (live green) |

## 7. Recorded Facts Cross-Check (verified to hold, not re-litigated)

1. **MOL2 string-loading unavailable on this build (read_mol2str unexported)** — HOLDS. upload.py documents it (:49–63) and implements the hasattr fail-closed guard (:135–141); SMOKE-12 pins the multi-segment refusal VERBATIM live ("this build accepts single-molecule MOL2 files only"); Decision 14's mechanical fallback activated exactly as written. SETUP-03's deliverable was met via SDF at human checkpoint B (04-15 step 5).
2. **Two-line upload path label = fixed format (27e8f34)** — HOLDS. Commit exists in git history (fix(04-15), 8 insertions/4 deletions in aamatch/setup_window.py); the code carries `'%s\n(%d molecule record(s))'` at _ingest_upload; re-greening re-confirmed in this session (py_compile + 688/688 + SMOKE-11 PART D green).
3. **Both human checkpoints APPROVED with recorded verdict tables** — HOLDS. 04-14-SUMMARY: "APPROVED (human, 2026-09-18) — 12/12 PASS" (criteria 1–3); 04-15-SUMMARY: "APPROVED-WITH-FIX (human, 2026-09-18) — 8/8 PASS (step 5 PASS-AFTER-FIX)" (criterion 4 + upload E2E + extension confirms), fix resolved and re-greened.

## 8. Human-Verification Carry-Forward (informational, not a gap)

The 04-15 fix-batch explicitly recorded that the two-line upload label's VISUAL rendering ("rides any later GUI session") is deferred to the next natural GUI session — consistent with the recorded fact that the fix is cosmetic and headlessly re-greened. Phase 5's GUI work will naturally re-observe it. No other human-verify debt is open for Phase 4.

---

## Gaps Summary

**None.** All 58 must-have truths across all 15 plans verified against the actual codebase; all 7 live gates pass in this session; all four ROADMAP success criteria carry both machine proof and APPROVED human verdicts; zero anti-patterns; every key seam wired. The phase goal — "From the Plugins menu the user gets a modeless setup window from which they can configure everything, save/load setups, export a shareable game, clean up the model, and start playing" — is achieved.

---

_Verified: 2026-09-18T12:30:00Z_
_Verifier: OpenCode (gsd-verifier)_
