# Codebase Concerns

**Analysis Date:** 2026-09-12

**Scope:** Dual-viewer interaction-matching game plugin (PyMOL 2.5.0 side active,
VMD v2 deferred). Audited: `aamatch/` (pure + cmd tiers), `smoke/`, `tests/`,
`.planning/` (STATE/ROADMAP/research/phase summaries). No TODO/FIXME/HACK
tokens exist anywhere in `aamatch/`, `smoke/`, or `tests/` — debt is
documented in planning docs and docstrings, not inline.

---

## Tech Debt

**Placeholder demo metadata and data set:**
- Issue: The only shipped molecule set is a 2-entry development set; its
  `license` and `provenance` fields are explicitly "Phase-8 placeholders".
- Files: `aamatch/data/MANIFEST.json` (set `demo-dev-1`: `license: ""`,
  `provenance: {}`), `aamatch/data/ligands/` (benzamide, acetate only)
- Impact: README's demo table and `DATA_SOURCES.md` cannot be populated;
  higher-difficulty games reuse tiny ligands via the generator's
  nearest-bucket supply fallback.
- Fix approach: Phase 8 curation under the propose → human-approve →
  fetch/commit protocol (PROJECT.md); write `DATA_SOURCES.md` with PDB/DOI
  + license per entry; drop script-built fixtures in favor of curated data.

**Backup module is pure-store only; cmd-tier adapter deferred:**
- Issue: `aamatch/backup.py` implements the byte-store (sha256 + JSON) but
  the PyMOL-object snapshot/restore adapter is explicitly deferred —
  `BACKUP_OBJECT_PREFIX` (`_aam_backup`) is reserved and unused.
- Files: `aamatch/backup.py:33,50`
- Impact: No in-session snapshot of live PyMOL objects exists yet; Phase 7
  persistence (`.pse` + sidecar) has no backup substrate to build on.
- Fix approach: Phase 7 adds the cmd-tier snapshots using the prefix;
  Pitfall 9's restore two-step (delete + create, assert counts) applies.

**Detection thresholds are PROVISIONAL pending Phase 8:**
- Issue: All 18 threshold constants in `aamatch/thresholds.py` are
  transcribed from `docs/DETECTION_THRESHOLDS.md`, whose approval is
  provisional — any value change is a `DETECTOR_VERSION` bump event and
  refuses ALL previously generated level specs (exact-match gate in
  `aamatch/level_spec.py`).
- Files: `docs/DETECTION_THRESHOLDS.md` (line 4 provisional note),
  `aamatch/thresholds.py`, `aamatch/level_spec.py` (`DETECTOR_VERSION`)
- Impact: Saved/exported games become unplayable after a threshold revisit;
  this is intentional (stale-specs-must-regenerate) but operationally sharp
  once Phase 7 save/restore ships.
- Fix approach: Freeze thresholds at Phase 8 dataset curation; communicate
  regeneration requirement in user-facing docs (Phase 9).

**Recorded gate-doc inconsistency (Met halogen cell):**
- Issue: `docs/DETECTION_THRESHOLDS.md` §3.3 Met-row says Y(S) for halogen
  while §3.5's resolved 9-AA set excludes Met; code followed §3.5. Not yet
  reconciled in the doc.
- Files: `docs/DETECTION_THRESHOLDS.md`, `aamatch/capability.py`
- Impact: Doc/code divergence on a frozen artifact; next reviewer may
  follow the wrong cell.
- Fix approach: Reconcile at the next versioned review (§4.7 bump event,
  never a silent edit).

**Untyped ligand groups:**
- Issue: Ligand phosphate/sulfonate are not typed (accepted in 02-06 for
  DETECT-04 parity); ligand water-bridge H-bonds deferred (EXT-01 note in
  `aamatch/detector.py:16`).
- Files: `aamatch/capability.py`, `aamatch/detector.py:16`
- Impact: Some real interactions in future demo molecules will never be
  detectable → unsolvable-by-design risk for curated sets.
- Fix approach: Extension is a versioned `capability` change
  (`DETECTOR_VERSION` bump) when Phase 8 curation requires it.

**Dormant color-restore fallback never exercised:**
- Issue: AA color restore tries the `alter` expression-sandbox dict
  subscript first, with a per-id `cmd.alter` fallback. SMOKE-07 proved the
  sandbox branch fires on this build; the per-id fallback has never run.
- Files: `aamatch/wizard.py:221-242`
- Impact: An unexercised code path guards against cross-build sandbox
  differences; if it ever fires in the field, it is untested.
- Fix approach: Add a headless smoke that forces the fallback (monkeypatch
  or alternate-build run) before Phase 4 ships; or delete and re-spec if
  sandbox rejection is never observed.

**README and docs stubs:**
- Issue: Usage, Project Structure, Demo Molecules table, and
  Acknowledgements are all `TBD`; `DATA_SOURCES.md` referenced but absent;
  `biochemeleon.zip` referenced in AGENTS.md is not present in the repo.
- Files: `README.md`, `AGENTS.md`
- Impact: Users cannot install/start guided gameplay beyond the 03-07
  menu path; new dev machines lack the staged fallback install artifact.
- Fix approach: Phase 9 docs pass (ROADMAP already schedules it); remove
  stale AGENTS.md references or restore the artifact.

**Probe-script accumulation:**
- Issue: Ad-hoc probe scripts accumulate under git-ignored `tmp/`
  (`probe_0306_*.py`, `probe_crashhunt.py`, etc.) — useful field data but
  undocumented and rot-prone.
- Files: `tmp/`
- Impact: Findings live only in working memory/summaries; scripts may no
  longer run as APIs change.
- Fix approach: Either promote durable probes into `smoke/` or prune `tmp/`
  per phase; this is dev-only clutter, not shipped code.

---

## Known Bugs

**03-06 checkpoint fix batch committed but UNVERIFIED (pending human re-test):**
- Symptoms: The 2026-09-11 fix batch addressed (a) cumulative greening of
  recolored AAs (display-list staleness after color restore), (b) AA
  representation split (charged 2176 / neutral 49 atoms → uniform sticks),
  (c) game opening zoomed-in (zoom-to-frame), (d) formed-but-not-required
  types invisible (new result line), (e) multi-molecule scope notice, (f)
  cross-molecule scoring guard (records on the wrong ligand could count).
- Files: `aamatch/placement.py`, `aamatch/wizard.py`, `aamatch/engine.py`
  (`detect_molecule` at ~line 299), `aamatch/wizard_text.py`; verdicts in
  `.planning/STATE.md` (lines 142-152)
- Trigger: All surfaced during the 03-06 human checkpoint; fixes are
  headlessly smoke-covered (SMOKE-07 +26, SMOKE-08 +3) but the GUI re-test
  has not yet confirmed them against a real mouse/display.
- Workaround: None needed — pending verification is the state, not a bug.
  Do not write 03-06-SUMMARY.md until re-test records verdicts.

**UP/DOWN arrow keys dead by design:**
- Symptoms: Arrow UP/DOWN do nothing during gameplay; LEFT/RIGHT and
  w/s/q/e/comma/period work.
- Files: `aamatch/wizard.py` (`do_special` owns LEFT=100/RIGHT=102 only;
  UP/DOWN co-fire command history on PyMOL 2.5.0)
- Trigger: User presses UP/DOWN in the wizard.
- Workaround: By design (prevents the game stealing console history keys);
  consider documenting in the Phase 9 help so users are not surprised.

**Whole-scene `engine.detect()` retained alongside scoped guard:**
- Symptoms: Cross-molecule scoring is guarded in the Confirm path via
  `detect_molecule`, but the unrestricted whole-scene `detect()` still
  exists for grid/hygiene asserts; calling the wrong one in a future
  scoring path silently reintroduces the cross-molecule credit bug.
- Files: `aamatch/engine.py:22-29` (docstring warning), ~line 299
- Trigger: Future code (Phases 4-7) wiring scoring to `detect()` instead
  of `detect_molecule()`.
- Workaround: None mechanical; reviewer discipline + existing docstring
  warning. Consider a source-gate test that bans `engine.detect(` outside
  grid/hygiene call sites.

---

## Security Considerations

**Wizard panel button codes are deferred-evaluation command strings:**
- Risk: Panel entries' third element is parsed by PyMOL's C layer
  (`Wizard.cpp:569-576`, PParse on mouse release) — any user-controlled
  string that reaches a button `code` becomes executed Python. Dev ligand
  names/IDs and setup fields do NOT currently flow into codes (codes are
  internal constants constrained by a regex source gate).
- Files: `aamatch/wizard_text.py` (panel entry builders; code regex
  `^cmd\.get_wizard\(\)\.[a-z_]+\(` pinned by `tests/test_wizard_source.py`)
- Current mitigation: Mechanical AST/regex source gate limits codes to
  fixed getter calls with no module name or arguments.
- Recommendations: When Phase 4 adds UI where any user-typed value (file
  name, setup text) could reach a panel entry, extend the gate to ban
  interpolation of such values into `code` strings.

**WSL test interpreter is EOL Python 3.6.9:**
- Risk: `python3.6` (3.6.9, EOL 2021-12) runs the entire 600+ test suite
  and `py_compile` floor; it receives no security fixes.
- Files: `tests/` (all run under 3.6 per AGENTS.md), root `AGENTS.md`
- Current mitigation: Interpreter runs local code only, no network; the
  runtime target is PyMOL's Python 3.9.13 (Windows conda env), not 3.6.
- Recommendations: Accept local-only risk now; if the project grants any
  network or user-input surface to the WSL suite, move to a maintained
  interpreter and keep the 3.6-syntax floor via `ast.parse(feature_version)`
  or `vermin` instead of the 3.6 binary itself.

**Persistence integrity and key safety (already mitigated, keep):**
- Risk: Backup byte-store keys could smuggle path traversal.
- Files: `aamatch/backup.py:111-119` (simple-filename key guard applied to
  both stores), `aamatch/persistence.py` (sha256 self-describing bytes)
- Current mitigation: Guards present and unit-tested
  (`tests/test_backup.py`, `tests/test_persistence.py`).
- Recommendations: When the cmd-tier adapter lands (Phase 7), apply the
  same key guard to object names; do not relax on a "local plugin" theory.

---

## Performance Bottlenecks

**WSL unit-test suite time is on an upward trend:**
- Problem: The exhaustive generator-invariant corpus (+ ~51 s) and
  detector-property battery brought the full suite to ~67 s under
  python3.6 (02-12/02-11 records); Phase 4-7 additions will extend it.
- Files: `tests/test_generator_invariants.py`,
  `tests/test_detector_invariance.py`
- Cause: Deliberate thoroughness (100-seed invariance, exhaustive pairwise
  spacing proofs); python3.6 is not the bottleneck, the design is.
- Improvement path: Split a "quick" gate (`py_compile` + purity + audit) for
  edit-loop use and keep the full sweep for pre-commit/phase gates; if
  needed, prune redundant seeds (no signal loss observed below 25 seeds in
  02-11 discussion).

**Headless detection budgets are proven only at Phase-2 data sizes:**
- Problem: SMOKE-05 asserts extract ~16-21 ms / detect 0.0 ms on a 1285-atom
  scene (largest bundled molecule, 82 objects), but the larger Phase-8
  curated molecules and 9×9 grids with heavier ligands are unmeasured;
  PITFALL 15's budgets (Generate < 30 s, detect < 100 ms, click feedback
  < 200 ms) remain gates, not measured facts.
- Files: `smoke/smoke_05_perf.py`, `.planning/research/PITFALLS.md` (Pitfall 15)
- Cause: Dev set is two small SDFs only.
- Improvement path: Phase 8/9 adds a large-demo perf gate; keep spatial
  `cross_pairs` (cell == cutoff) as the only candidate path (already
  audit-pinned by `tests/test_code_audit.py`) so scaling stays near-linear.

---

## Fragile Areas

**`aamatch/detector.py` — largest, most policy-dense module (1188 lines):**
- Files: `aamatch/detector.py`, `aamatch/capability.py` (712),
  `aamatch/generator.py` (879)
- Why fragile: Thresholds are provisional; typing tables are transcribed
  from a gate doc with one recorded internal inconsistency; every
  substantive edit is a `DETECTOR_VERSION` bump that orphans stored specs.
- Safe modification: Never edit constants in place; new thresholds go
  through the §4.7 versioned-review path; keep `source:` comments
  truthful (provenance scan test enforces).
- Test coverage: Strong — 7-type unit suite, 100-seed rigid-transform
  invariance, thresholds kill/restore sensitivity controls
  (`tests/test_detector*.py`); coverage is not the gap, change-cost is.

**Module-level singleton game state in `aamatch/engine.py`:**
- Files: `aamatch/engine.py:93-103` (`_payload/_registry/_game` module
  globals)
- Why fragile: One game per PyMOL session by construction; the DUPLICATE
  hazard is import identity — loading the plugin once as `aamatch` (plugin
  path) and once as `pmg_tk.startup.aamatch` (Plugin-Manager install)
  creates two module objects → two singleton sets (AGENTS.md rule 5).
- Safe modification: Exactly one install mechanism per session (plugin-path
  by default; 01-09 checkpoint); never copy-install alongside plugin-path.
- Test coverage: Smokes use direct imports; the dual-import case is
  deliberately unexercised.

**Purity gate requires manual registration:**
- Files: `tests/test_purity.py` (`PURE_MODULES` list, line ~87)
- Why fragile: A new pure module that is NOT added to `PURE_MODULES` is
  silently ungated — the gate only scans listed modules.
- Safe modification: Add the module name in the same commit as the new
  module (Phase-2 pattern: RED test → GREEN feat → registration as test
  commit).
- Test coverage: The gate itself is solid (AST scan + clean-subprocess +
  2-finding negative control); the gap is process, not code.

**Prose false positives in grep gates (documented-only):**
- Files: `tests/test_code_audit.py` (PROSE_PIN exact-count prose pins),
  `tests/test_purity.py`
- Why fragile: Token greps fire on docstring prose ("from PyQt5 import" in
  a comment hit a false positive in prior art); `test_code_audit.py`'s
  prose pins demand deliberate updates whenever docstrings change
  banned-token mention counts.
- Safe modification: AST gates are the enforced mechanism — update prose
  pins deliberately (Gate C = human re-review by design); never blind-fail
  on grep output.

**Plugin metadata block position is load-bearing:**
- Files: `aamatch/__init__.py:1-12` (`# Version:` / `# Citation-Required:`
  must be the file's first lines)
- Why fragile: `pymol.plugins` parses `# Key: value` lines at the top and
  stops at the first non-# line; moving anything breaks reinstall version
  compares.
- Safe modification: Header edits only per the NOTE comment;
  `tests/test_package_skeleton.py` pins the seam.

**`to_windows_path` case-9 asymmetry (path conversion):**
- Files: `aamatch/paths.py` (verbatim port incl. the `len(parts)==4`
  term; `/mnt/c` unchanged vs `/mnt/c/` → `C:\`)
- Why fragile: The whole WSL/Windows split (AGENTS.md "single most common
  way to break things"); every `cmd.load/save` must route through the
  converter; repo must sit on a Windows-visible `/mnt/c` path.
- Safe modification: Never "simplify" the asymmetry — it is unit-pinned
  (`tests/test_paths.py`); new file-touching call sites must use the
  helper (02-15 audit banners cover existing sites).

**Smoke verdict channel is stdout-grep, not exit code:**
- Files: `smoke/run_smoke.sh` (greps `=== SMOKE-NN PASS ===` from teed
  output; cmd.exe cannot propagate exit codes), hard-codes
  `C:\src\run-conda-pymol.bat`
- Why fragile: A smoke that prints the marker then crashes afterwards
  still "passes" (marker is printed last by convention, so this is a
  convention-only hazard); the bat-bridge path and WSL cwd assumption make
  the suite non-portable to any machine without `C:\src\run-conda-pymol.bat`.
- Safe modification: Keep the PASS marker as the final statement of every
  smoke; guard with a trailing `=== SMOKE-NN DONE ===` marker if a crash
  after PASS becomes plausible.

**Git-ignored reference material the dev workflow depends on:**
- Files: `Pymol-script-repo` (symlink → `../bioCHEMeleon/Pymol-script-repo`),
  `pymol-src` (symlink → `../bioCHEMeleon/tmp/pymol-src`),
  `tmp/bioCHEMeleon/` (prior-art code), `.gitignore`
- Why fragile: Research docs and AGENTS.md cite PyMOL source file:line
  from `pymol-src`; a machine without the sibling `bioCHEMeleon` checkout
  loses the "read the source" verification path and the symlink's target.
- Safe modification: Document the sibling-repo prerequisite in onboarding
  docs; keep symlinks relative so the layout travels together.

---

## Scaling Limits

**Molecule supply:**
- Current capacity: 2 small-ligand entries (`benzamide`, `acetate`) in one
  dev set; generator bucket-filter with nearest-bucket fallback ties to
  easier.
- Limit: Difficulty ≥ 2 games on arbitrary difficulty/diversity targets
  degrade to reusing the same two ligands; levels look repetitive.
- Scaling path: Phase 8 curates ~9 tier slots (ROADMAP); generator
  complexity formula already supports grid_n 3..9 + types 1..7.

**Gameplay scoping (Phase 3):**
- Current capacity: Interactively playable/scorable molecule is index 0
  only (`wizard_core.build_slot_map`, `aamatch/gamestart.py` start);
  other molecules render as context with a UI notice.
- Limit: Real multi-molecule play (score advance across molecules of one
  level) is Phase 5/6 work; the cross-molecule guard is in place but the
  progression UX is not.
- Scaling path: `detect_molecule(level_index, molecule_index)` already
  parameterizes the scope; Phases 5-6 swap the hard 0 for progression
  state in `GameState`.

**Largest proven scene:**
- Current capacity: 82 objects / 1285 atoms headless (SMOKE-05).
- Limit: Above that, `.pse` bloat and per-frame Python work per PITFALL
  15's warnings are unmeasured; GUI-thread `cmd.*` loops freeze Qt if
  generation runs > 200 ms synchronously (relevant to Phase 4 setup).
- Scaling path: Phase 8 large-demo perf gate; chunk generation with event
  yields if needed; budgets stay the Phase 9 audit criteria.

---

## Dependencies at Risk

**python3.6 (3.6.9) WSL interpreter:**
- Risk: EOL since 2021-12; no `numpy`, no `dataclasses`, no 3.7+ syntax;
  the purity contract is BECAUSE of this floor. Any dependency bump the
  pure layer wants (e.g. `itertools`-heavy designs) is blocked.
- Impact: Security-unmaintained test interpreter; permanent stdlib-only
  pure layer.
- Migration plan: Deliberate choice, not drift — see Security section;
  if ever revisited, replace the 3.6 binary with a 3.6-syntax checker and
  modern interpreter in one motion.

**PyMOL 2.5.0 (pin):**
- Risk: Fixed-version runtime (2021-era) via a machine-specific batch
  bridge; API behaviors (msm restore, unpick deletes pk1, get_bonds walk
  order, sandbox dict subscript) are empirically pinned to THIS build —
  several probe findings contradict or extend docs.
- Impact: Behavior-dependent code (camera math R^T, msm order law, color
  restore sandbox branch) may differ on other PyMOL/OS builds; the
  single-fix-site convention (`wizard_core.view_camera_to_world`) exists
  but users on other builds are untested.
- Migration plan: Stay pinned for v1; record per-build probes as smokes so
  a future 3.x compatibility pass re-runs them.

**Reference material external to the repo (see Fragile Areas):**
- Risk: `pymol-src`, `Pymol-script-repo`, `tmp/bioCHEMeleon`,
  `biochemeleon.zip` all git-ignored/symlinked/absent.
- Impact: Fresh setups cannot audit cited PyMOL behavior or borrow prior
  art.
- Migration plan: Onboarding doc enumerates required sibling checkout
  (Phase 9 docs). Not code-fixable.

---

## Missing Critical Features

All below are roadmap-scheduled, not forgotten — listed because they are
gaps any contributor will hit:

**No Qt setup window (Phase 4):**
- Problem: `gamestart.start_game()` runs on hard defaults (molecules 2,
  difficulty 3, interaction_mode unset, seed 42); players cannot configure
  anything.
- Files: `aamatch/gamestart.py`, `aamatch/setup_state.py` (defaults frozen)
- Blocks: Demo-set selection, level difficulty choice, seed choice.

**No game status tab / timer / hint (Phase 5):**
- Problem: `GameState.start_timer` stores a float anchor only
  (`aamatch/game_state.py`); no live timer UI, no hint path
  (carbon-recolor-only per spec).
- Blocks: Spec'd time-tracking and hint features.

**No scoring lifecycle (Phase 6):**
- Problem: Repeated Confirm appends `molecule_scores` with a note that
  "Phase 6 owns score-history lifecycle" (`aamatch/wizard.py:535` and
  surrounding notes); no debrief, skip-with-partial-score UX, advance, or
  endgame screen.
- Blocks: Multi-molecule progression, endgame.

**No save/restore / import-export (Phase 7):**
- Problem: `.pse` round-trip of object matrices is still UNVERIFIED
  (STATE.md blocker carried forward; PITFALL 10 verification task); no
  sidecar persistence wiring exists.
- Files: `aamatch/persistence.py` (pure container ready), `aamatch/backup.py`
  (adapter deferred)
- Blocks: Saved games, shareable exported games (spec 3.5).

**VMD v2 target entirely absent:**
- Problem: No `vmd/` directory exists; README/commit history show v2 is
  explicitly deferred.
- Blocks: VMD port (PROJECT.md decision: v1 = PyMOL only).

---

## Test Coverage Gaps

**Qt tier: zero automation possible:**
- What's not tested: Everything in the upcoming Phases 4-7 Qt layer —
  dialogs, signal wiring, focus, timer interplay.
- Files: (future `aamatch/` Qt modules; today the only Qt touchpoint is
  `addmenuitemqt` in `aamatch/__init__.py`)
- Risk: GUI bugs will surface at human checkpoints only (PITFALL 1 is the
  documented reason; accepted by design).
- Priority: High when Phase 4 starts — enforce the thin-shell-over-controller
  rule so cmd-tier unit tests absorb as much logic as possible.

**Real-mouse/keyboard delivery paths:**
- What's not tested: Actual LEFT/RIGHT/other key delivery through Qt's
  focus path, q/e camera-z-sign feel, drag feel, and single-green recolor
  review — headless SMOKE-07 scripts the C-layer pick route, not the
  mouse.
- Files: `aamatch/wizard.py`, `smoke/smoke_07_wizard_loop.py`
- Risk: Focus/co-fire behavior differs between scripted `do_select` and
  real input (03-06 checkpoint already caught several GUI-only bugs —
  proof the gap is real).
- Priority: High — resolve with the pending 03-06 re-test + 03-07
  checkpoint; keep the checkpoint template for every Qt-touching phase.

**Dormant fallback branches:**
- What's not tested: wizard.py per-id `cmd.alter` fallback
  (`aamatch/wizard.py:221-242`); the "editor_scheme" start-guard
  contingency is recorded as NOT implemented (`aamatch/gamestart.py:46`)
- Risk: Unexercised guards may be broken when they are actually needed.
- Priority: Medium — force-path smoke before Phase 4.

**`.pse` object-matrix round-trip (Phase 7 gate):**
- What's not tested: Whether TTT/state matrices survive session save/load
  (PITFALL 10, flagged UNVERIFIED).
- Files: future persistence smoke; gate is recorded in `.planning/STATE.md`
- Risk: If matrices do not round-trip, the persistence design (currently a
  frozen decision) must switch to coordinate/sidecar persistence.
- Priority: High at Phase 7 start (explicit gate before committing the
  design).

**Persistence cmd-tier backup adapter:**
- What's not tested: `BACKUP_OBJECT_PREFIX` snapshot/restore of live
  objects — no code exists yet.
- Files: `aamatch/backup.py:33,50`
- Risk: None now (feature absent); design risk if the pure-byte contract
  shaped for files does not fit object snapshots.
- Priority: Medium — lands with Phase 7; keep `verify_intact` failure
  semantics identical across both stores.

**Cross-build PyMOL behavior:**
- What's not tested: Anything outside the recorded dev build (Python
  3.9.13/PyQt5 5.12.3/Qt 5.12.9/PyMOL 2.5.0/numpy 1.25.2 — recorded in
  `.planning/phases/01-bootstrap-pure-foundation/windows-env-versions.md`).
- Risk: Empirics (unpick-deletes-pk1, get_bonds walk order, sandbox
  dict-subscript) are single-build facts.
- Priority: Medium — document as "tested on dev build only" in Phase 9
  release notes; smokes are the regression channel if a target build
  changes.

---

*Concerns audit: 2026-09-12*
