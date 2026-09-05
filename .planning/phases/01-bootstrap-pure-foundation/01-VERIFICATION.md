---
phase: 01-bootstrap-pure-foundation
verified: 2026-09-06T00:00:00Z
status: passed
score: 4/4 phase success criteria (9/9 plan must-have groups)
re_verification: null
gaps: null
human_verification: []
---

# Phase 1: Bootstrap & Pure Foundation — Verification Report

**Phase Goal:** An installable plugin skeleton whose pure foundation (setup params, versioned persistence, level-spec schema, backup safety net) is proven in WSL, and whose WSL→Windows headless pipeline is proven end-to-end — before any game code exists.
**Verified:** 2026-09-06 (WSL, repo root `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/AA-match`)
**Status:** **passed**
**Re-verification:** No — initial verification

---

## Verification Method

Every SUMMARY claim was checked against the actual code, tests, and committed records on disk — not trusted. Live runs performed in WSL: `python3.6 -m py_compile aamatch/*.py` (clean) and `python3.6 -m unittest discover -s tests` (**Ran 114 tests — OK**). The Windows PyMOL smoke was NOT re-run (per instruction); its PASS record was verified on disk instead. Working tree is clean — all phase work is committed (53 commits; HEAD `650a158`).

## Goal Achievement

### Phase Success Criteria (ROADMAP.md:36-40)

| #  | Criterion | Status | Evidence |
| -- | --------- | ------ | -------- |
| 1 | [WSL] PERSIST-01 versioned round-trip + refusals, unittest green | ✓ VERIFIED | `tests/test_setup_state.py::test_09_round_trip_every_field_non_default` (line 269): every-field-non-default state → `save_setup_file`/`load_setup_file` → **exact dict equality**, container header asserted on disk (`magic`/`version`/`kind`), subTest per interaction mode. Refusal classes message-asserted: `test_11a` foreign JSON, `test_11b` newer version ("Please update"), `test_11c` misfiled kind, `test_11d` garbage bytes. Suite 114/114 OK. |
| 2 | [WSL] Pure-layer gates green — 5 pure modules stdlib-only; `to_windows_path` unit-tested | ✓ VERIFIED | `tests/test_purity.py` (280 lines) enforces: **Gate A** AST import scan over all 5 pure modules (all scopes — module level AND function bodies), **Gate A2** lazy-`__init__` rule (zero module-level imports), **Gate B** clean-subprocess import with ZERO sys.modules stubs, **Gate D** 3.6 py_compile floor, plus a **negative control** proving the gate flags real imports but ignores docstring prose (exactly 2 findings pinned). `tests/test_paths.py`: 17 tests incl. the 14-case conversion matrix. All green. |
| 3 | [HEADLESS] Skeleton loads via headless cmd.exe recipe exit 0; env versions recorded once | ✓ VERIFIED (record on disk) | `windows-env-versions.md` (committed) records verbatim: full run **ended with `=== SMOKE-01 PASS ===`, runner exit 0**; env table Python 3.9.13 / PyQt5 5.12.9 (binding 5.12.3) / PyMOL 2.5.0 / numpy 1.25.2; closes STACK.md LOW-confidence flag; cmd.load probe answers (forward-slash + space paths OK, n=1 atom each). Smoke script itself verified substantive: `smoke/smoke_01_bootstrap.py` (173 lines, Parts A-D, `plugin_load` at line 98, SMOKE-ENV prints) + `smoke/run_smoke.sh` (frozen recipe: `timeout 120 cmd.exe /c "C:\src\run-conda-pymol.bat -cq …"` + marker grep). `bash -n smoke/run_smoke.sh` — clean. |
| 4 | [HUMAN] INSTALL-01: plugin registered under Plugins menu | ✓ VERIFIED (human-approved, method deviation noted) | Recorded human verdict in `01-09-SUMMARY.md`: Plugins menu shows **AA-match = Y**; click prints placeholder **= Y** (verbatim: `AA-match 0.1.0: plugin skeleton OK — game UI arrives in Phase 4.` — matches `aamatch/__init__.py:31` exactly); console clean **= Y**. Orchestrator-accepted as human-approved evidence. **Method deviation, honestly recorded:** the human installed via PLUGIN-PATH (repo root added to PyMOL's plugin path) instead of the Plugin-Manager dialog copy install; the dialog-install branch was never exercised — recorded as *not-exercised, not-failed*. The core INSTALL-01 outcome (menu wiring + click feedback + clean console, proven by a human in a real GUI session) is satisfied. |

**Score: 4/4 phase success criteria verified.**

---

## Plan-Level Must-Have Verification (9/9)

| Plan | Must-have group | Status | Key evidence (actual code, not SUMMARY claims) |
| ---- | --------------- | ------ | --------------------------------------------- |
| 01-01 | Plugin skeleton: metadata-first, zero module-level imports, loader contract | ✓ | `aamatch/__init__.py` (31 lines): metadata block is the literal first 2 lines (`# Version: 0.1.0` / `# Citation-Required: No`); **zero module-level imports anywhere**; `__init_plugin__` imports `addmenuitemqt` locally and calls it FIRST (lines 24-25); Qt-free `run_plugin_gui` prints the version line. 5 contract tests (`test_package_skeleton.py`, 121 lines ≥ 50 min). |
| 01-02 | Versioned container core + atomic JSON I/O | ✓ | `aamatch/persistence.py` (164 lines): `AAM_MAGIC = "AAMATCH"` (line 34), `FORMAT_VERSION = 1`, `KINDS`, `FormatError`; three refusal classes with the canonical phrasing ("not an AA-match file" / "unsupported AA-match format version … Please update AA-match." / "expected an AA-match <kind> file"); older versions accepted (line 79: refuse only `> FORMAT_VERSION`); `write_json_atomic`: mkstemp → write → fsync → `os.replace`, binary, `sort_keys=True`, `allow_nan=False`, tmp cleanup on `BaseException`. 19 tests. |
| 01-03 | Backup pure core over injected stores | ✓ | `aamatch/backup.py` (248 lines): `BackupError`, `MemoryStore` (125), `FileStore` (150), `snapshot` (198), `verify_intact` (216), `restore` (232), `discard` (246), `BACKUP_OBJECT_PREFIX` (50); sha256 corruption gate with "backup corrupt" refusals (mismatch/missing-header/unparseable); shared `_check_key` path-traversal guard. 23 tests incl. on-disk byte-flip simulation. |
| 01-04 | Path guard + package data resolution | ✓ | `aamatch/paths.py` (63 lines): `to_windows_path` — guard semantics, only `/mnt/<single-alpha>/` converts, load-bearing `len(parts) == 4` term documented; `package_data_path` anchored to `__file__`, never cwd. 17 tests (14 matrix rows + 3 resolution). |
| 01-05 | 7-field setup model + PERSIST-01 | ✓ | `aamatch/setup_state.py` (172 lines): exactly 7 DEFAULTS keys, no `format` field; 7-value `INTERACTION_TYPES`, 3-value `INTERACTION_MODES`; `validate_state` non-mutating (deepcopy, fill/clamp/enum-fallback/canonical ordering); `randomize_state` local `random.Random(seed)`. `save_setup_file`/`load_setup_file` wrappers validate on save AND load (persistence.py:152,164 + module-level pure←pure import line 32). 25 tests. |
| 01-06 | level_spec schema + detector_version exact-match gate | ✓ | `aamatch/level_spec.py` (214 lines): `DETECTOR_VERSION = "det-1"` (line 60), `LEVEL_SPEC_VERSION = 1`; **exact-match** detector gate refusing stale AND newer with distinct "stale or newer … regenerate" message (lines 116-121) vs format gate's refuse-newer-only (line 111); structural minimums (non-empty levels, grid_n ≥ 1, grid.n ≥ 1, unique slot_id per molecule, int seed excluding bool); unknown keys preserved (passthrough parse). 20 tests. |
| 01-07 | Headless toolchain proof + env record | ✓ | See criterion 3 above. `windows-env-versions.md` exists, committed, contains SMOKE-ENV verbatim table + PASS record + probe answers + the two runtime discoveries (`__file__` unusable in `-cq`; `loaded` property False on Qt-warning path). |
| 01-08 | Purity gates ENFORCED + standing rules | ✓ | `tests/test_purity.py` (280 lines ≥ 100 min): Gates A/A2/B/D + negative control as live suite members (the 114-test run above includes them). `AGENTS.md` line 33: `## AA-match standing gates (Phase 1 — inherit into every phase)` — commands, purity contract (zero-stubs, ARCHITECTURE stub pattern superseded), grep-gate warning, two-version-gates rule, module identity, dev loop, env pointer. |
| 01-09 | [HUMAN] install checkpoint + defaults decision | ✓ | `01-09-SUMMARY.md`: human verdict table (Y/Y/Y) + verbatim placeholder line + PLUGIN-PATH decision + defaults approval. **Cap-10 amendment verified at all three levels:** code (`aamatch/setup_state.py:50` — `DIFFICULTY_CAP = 10` with the human-amendment comment, default 3 / min 1 untouched), tests (`tests/test_setup_state.py:106` pin `(3, 1, 10)`; literal boundary `{'difficulty_levels': 10} → 10`, `{'difficulty_levels': 11} → 10` at lines 153-154, independent of the constant), commit (`aef7c5e` "fix(01-09): adopt human-amended difficulty_levels cap 10 (was 9)" — touches exactly the 2 files). |

---

## Key Link Verification

| From | To | Via | Status | Evidence |
| ---- | -- | --- | ------ | -------- |
| `__init_plugin__` (aamatch/\_\_init\_\_.py) | `pymol.plugins.addmenuitemqt` | function-level local import, FIRST statement | ✓ WIRED | line 24-25: `from pymol.plugins import addmenuitemqt; addmenuitemqt('AA-match', run_plugin_gui)` |
| `persistence.save_setup_file` | `setup_state.validate_state` | validate-before-write AND validate-on-load | ✓ WIRED | persistence.py:32 (import), :152 (save), :164 (load); idempotence pinned by `test_10` |
| `level_spec.parse_level_spec_dict` | `persistence.check_container` | container gate `kind='level_spec'` | ✓ WIRED | level_spec.py:58 (import), detector gate at :116-121 |
| `backup.snapshot/restore` | injected store protocol (`save_bytes`/`load_bytes`) | store injection — no storage import | ✓ WIRED | backup.py:198-208; both `MemoryStore` and `FileStore` implement it; contract tests run per store |
| smoke Part B | `pymol.plugins` real loader | `startup.__path__.append(repo_root)` + `plugin_load('aamatch')` | ✓ WIRED (record) | smoke_01_bootstrap.py:98; PASS recorded in windows-env-versions.md |
| `tests/test_setup_state.py` round-trip | `persistence.save_container/load_container` | versioned-container discipline | ✓ WIRED | test_09 asserts header fields on disk (`AAM_MAGIC`, `FORMAT_VERSION`, `kind='setup'`) |

---

## Requirements Coverage (REQUIREMENTS.md mapped to Phase 1)

| Requirement | Status | Blocking Issue |
| ----------- | ------ | -------------- |
| INSTALL-01 | ✓ SATISFIED (human-approved, method deviation honestly recorded) | None — dialog-install branch not exercised (recorded as not-exercised, not-failed) |
| PERSIST-01 | ✓ SATISFIED | None — versioned round-trip + refusals proven in WSL with exact-dict-equality tests |

(Note: the REQUIREMENTS.md status table still lists both as "Pending" — that bookkeeping is the orchestrator's to update, outside this verifier's write scope.)

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `aamatch/__init__.py` | 29 | "Phase-1 placeholder" in docstring | ℹ️ Info | Not a stub — this placeholder **is** the Phase-1 deliverable and it has a real implementation (prints the version line; proven by human click + headless run). Game UI arrives Phase 4 by design. |
| `aamatch/backup.py` | 4 | "not implemented in open-source" | ℹ️ Info | Docstring prose quoting prior-art context (editor.py) — not a stub marker. |

No TODO/FIXME/HACK, no empty returns, no console-only handlers in any shipped module. Zero stub patterns across `aamatch/*.py` and `smoke/*.py`.

---

## Watch Items (info-level, non-blocking)

1. **`aamatch/__pycache__` is present** — regenerated by this verification's test run (any WSL suite run recreates it). Standing practice from 01-09: clean it after suite runs, since the human loads the plugin live from the repo via plugin-path. (`rm` is denied to this verifier; the human/orchestrator clears it.)
2. **`smoke/run_smoke.sh` marker grep is smoke-01-specific** (`grep -q "=== SMOKE-01 PASS ==="`). The Phase-1 plan only required the recipe as proven for smoke-01 — later-phase smokes will need the marker generalized (forward note for Phase 2 planning, not a Phase-1 gap).
3. **Module-identity discipline is a standing human practice** — plugin-path only; never additionally copy-install (would create two module objects). Already documented in AGENTS.md gate 5 and 01-09-SUMMARY.md.

---

## Human Verification Required

None blocking. INSTALL-01's outcome evidence (menu present / click feedback / console clean) is already recorded from a human GUI session and accepted by the orchestrator. For completeness only: if the Project ever requires the Plugin-Manager **dialog copy-install** path itself to be proven (e.g., for Phase 9 release instructions to end users), that remains an unexercised branch to be checked by a human at that time.

---

## Gaps Summary

**No gaps.** All 4 phase success criteria verified, all 9 plan must-have groups verified against actual code (not SUMMARY claims), all key links wired, purity gates live in the green 114-test suite, cap-10 amendment confirmed in code + tests + commit, and the headless/env/install records exist on disk as committed artifacts. The single recorded deviation (PLUGIN-PATH install instead of Plugin-Manager dialog) is human-directed, honestly documented, and satisfies INSTALL-01's intent — noted, not scored as a gap.

---

_Verified: 2026-09-06_
_Verifier: OpenCode (gsd-verifier)_
