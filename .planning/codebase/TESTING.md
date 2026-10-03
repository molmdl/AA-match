# Testing Patterns

**Analysis Date:** 2026-10-03

## Test Framework

**Runner:** Python 3.6 stdlib `unittest` ONLY. **No pytest**, no third-party
test deps (the dev shell is bare `python3.6` 3.6.9 on WSL Ubuntu; installing
is forbidden). Config: none — discovery conventions only.

**Run commands (from repo root):**

```bash
python3.6 -m py_compile aamatch/*.py            # syntax floor (3.6)
python3.6 -m unittest discover -s tests -v      # FULL WSL suite incl. purity gates
python3.6 -m unittest tests.test_setup_state -v # one module
bash smoke/run_smoke.sh smoke/smoke_01_bootstrap.py          # headless Windows PyMOL proof
```

## Test File Organization

**Location:** `tests/` at repo root (NOT co-located). One file per module
under test: `tests/test_vec3.py` ↔ `aamatch/vec3.py` (28 test files).
Cross-cutting mechanical audits get their own files: `tests/test_purity.py`,
`tests/test_code_audit.py`, `tests/test_wizard_source.py`,
`tests/test_package_skeleton.py`.

**Every test file opens with:**
1. A docstring stating WHAT is covered, the plan/trace references
   (`plan 02-02`, `RED-first suite for plan 01-05`), and the exact run
   commands (`tests/test_vec3.py:1-7`).
2. The path bootstrap so the file works both via discovery and direct
   execution (`tests/test_purity.py:55-61`):

```python
_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(_HERE, '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
```

(Some files use the shorter `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))` — `tests/test_setup_state.py:31`.)

3. Parenthesized imports of symbols under test
   (`tests/test_setup_state.py:33-56`).

**ZERO `sys.modules` stubs anywhere** — this is a standing rule
(purity gate prerequisite; `tests/test_purity.py:19-26`). Pure modules
import cleanly in a bare interpreter, so no MagicMock pymol stubs exist.
Do NOT add any.

## Test Structure

**Suite organization:** one `unittest.TestCase` subclass per behavior
cluster, each with a 1-line docstring of its cluster
(`tests/test_setup_state.py:87,114`). Test methods named
`test_<NN>_<what>` with sequence numbers in older suites
(`test_01_defaults_key_set_is_exactly_the_7_fields`,
`tests/test_setup_state.py:90) or plain `test_<what>` in newer ones
(`tests/test_vec3.py:18`). Trailing `if __name__ == '__main__': unittest.main()`.

**Setup/teardown:** `setUp` builds injected stores/temp dirs
(`tests/test_backup.py:60-63`); `tempfile` + `shutil.rmtree` in file-I/O
suites (`tests/test_setup_state.py` imports `tempfile`, `shutil`).

**Editable-case pattern:** `self.subTest()` for the per-iteration failures
that must name their case (`tests/test_purity.py:253,280`).

**Refusal assertion pattern:** context manager + message assert:

```python
with self.assertRaises(FormatError) as ctx:
    ...
self.assertIn('detector', str(ctx.exception))
```

(`tests/test_checkpoint.py:311-358`, `tests/test_level_spec.py:213-224`.
Refusal wording is pinned — gate phrasing is part of the contract.)

**Shared contract mixin pattern:** a plain mixin (NOT a TestCase subclass)
`BackupContractMixin(object)` paired with concrete `TestCase` subclasses per
store (`tests/test_backup.py:50-63`) — the contract runs exactly twice
(MemoryStore, FileStore), never as an abstract third suite.

**Fixtures:** module-level constants (`PAYLOAD` in
`tests/test_backup.py:36-47` includes unicode + nested shapes for
exact-equality round-trips) and private factory functions
(`_non_default_raw_state(interaction_mode)`,
`tests/test_setup_state.py:69-84` — an "every field non-default" dict with
boundary MIN/CAP values). Boundary values come from module constants
(`MOLECULES_MIN`, `DIFFICULTY_CAP`) — never inlined literals.

## Mechanical Audit Suites (the standing gates — do not weaken)

All live in the normal suite (`python3.6 -m unittest discover -s tests -v`).
They are **AST-based by design**, NOT grep-based: the AST is immune to the
"grep tripwire" — a docstring that SAYS `from PyQt5 import` is a string
constant, never an Import/Call node (prior art false-positived on prose;
the grep-form is a documented-only human-check "Gate C", never a blind-fail
mechanism). Every gate carries a **NEGATIVE CONTROL** proving the finder
can fire — "a gate that cannot fail proves nothing"
(`tests/test_purity.py:118-131,329-352`).

**`tests/test_purity.py` — the four purity gates:**
- **Gate A** (`TestGateAASTImportScan`, line 211): AST import scan over all
  `PURE_MODULES` (line 99). Every `ast.Import`/`ast.ImportFrom` node in
  EVERY scope (module level AND function bodies) is checked against
  `FORBIDDEN` roots `{pymol, numpy, dataclasses, PyQt5, PySide2, tkinter,
  Pmw, pmg_tk}` (line 107) and the `ALLOWED_STDLIB` whitelist (lines
  113-116). Relative imports must target pure modules.
- **Gate A2** (`TestGateA2LazyInit`, line 229): `aamatch/__init__.py` has
  ZERO module-level imports (lazy imports inside `__init_plugin__`/handlers
  are the design).
- **Gate B** (`TestGateBCleanSubprocessImport`, line 248): each pure module
  imported by a FRESH bare interpreter via `subprocess` with
  `cwd=REPO_ROOT` and no stubs — exit code must be 0. Catches dynamic
  `__import__` and transitive contamination. 30 s timeout per module.
- **Gate D** (`TestGateDPyCompileSyntax`, line 270): every `aamatch/*.py`
  compiles under `python3.6 -m py_compile` (the 3.6 syntax floor).
- **Registration pins** (`TestGeneratorRegistration`, line 294, and
  siblings): each newly-gated module gets a test asserting its name is in
  `PURE_MODULES` — unregistered pure modules are silently ungated.
- **Negative control** (`TestNegativeControl`, line 329): synthetic source
  with 2 real forbidden imports + a docstring repeating the tokens must
  produce EXACTLY 2 findings (prose must NOT count).

**`tests/test_code_audit.py` — detection-pipeline audits (plan 02-15):**
four permanent checks, all AST-over-source-text with negative controls:
1. Candidate routing: `detector.py` imports AND calls `cross_pairs`.
2. Oracle isolation: `brute_force_pairs` (O(N·M) test oracle,
   `aamatch/spatial.py`) is imported/called NOWHERE in `aamatch/ or smoke/`.
3. No naive pair loops: no nested record-namespace double loops in
   `detector.py` or `spatial.cross_pairs`.
4. Banned cmd calls: `BANNED_CALLS = ('get_model', 'matrix_reset',
   'get_object_ttt')` (line 56) never CALLED; prose mentions pinned by
   EXACT count in `PROSE_PIN` (lines 64-69) — count drift = human
   re-review, never blind-fail on prose alone.

**`tests/test_wizard_source.py`:** AST gate for PLAY-04 — zero `ast.Call`
sites of `indicate`/`distance`/`load_cgo` in `SCANNED_MODULES`
(`wizard.py`, `gamestart.py`, `setup_window.py`, `game_window.py`, line 51)
with a finder negative control; `game_window.py` 'grow the list' comments
show how new cmd-tier modules join the scan set.

**Version-gate tests:** refuse-newer / accept-older for container
`version` and payload `format_version`; EXACT-match (stale AND newer
refused) for `detector_version`; message-asserted
(`tests/test_level_spec.py:176-237`, `tests/test_setup_state.py:307`).
The two gates must never be conflated — format accepts older, detector
refuses any mismatch.

## Property/Invariant Test Pattern

`tests/test_detector_invariance.py` is the exemplar: seeded batteries over
hand-scripted plain-list geometry (NO numpy):

1. Rigid-transform invariance — 100 seeded random rotation+translation
   transforms; full-record **dict equality** (tolerance effectively 0.0,
   tighter than the plan's 1e-9 ceiling). Rotation via plain list math,
   `random.Random(seed)`.
2. Permutation invariance — seeded Fisher-Yates shuffles of the atom
   record list; canonical output identical.
3. Determinism — two consecutive calls return `==` lists.
4. Boundary sensitivity — per-type cases pushed `_DELTA_A = 0.2` Å /
   `_DELTA_DEG = 0.2`° inside and outside the `thresholds.py` constants
   (always against the imported constants, never inlined numbers).
5. Loose perf guard — **REGRESSION-only** assertion:
   `WSL_PERF_GUARD_SECONDS = 2.0` for a worst-case synthetic scene. The
   docstring (lines 24-31) says explicitly: WSL is slower/CI-noisy; a
   sub-100-ms assertion here would be a flaky false-alarm machine —
   the real <100 ms budget is asserted ONLY in the headless Windows
   smoke. **Never tighten this constant.**

Exact-equality discipline: exact match where the value is exactly
representable (`vec3.scale(..., 0.5)` uses `assertEqual`,
`tests/test_vec3.py:34-37`) and `assertAlmostEqual(..., places=12/15)`
only where genuinely irrational (`tests/test_vec3.py:72-74`).

## Mocking

**Framework: none.** No `unittest.mock` for the plugin layer, no
sys.modules stubs (forbidden by the purity contract). Isolation is by
architecture, not by mocking:
- Pure modules are tested directly in a bare interpreter.
- Store abstraction: `BackupContractMixin` injects `MemoryStore` /
  `FileStore` (`tests/test_backup.py`).
- Qt/PyMOL-dependent modules are NOT unit-tested in-process; they are
  covered by AST source gates (e.g. `tests/test_package_skeleton.py`
  asserts `run_plugin_gui`'s lazy-import seam via source analysis:
  "executing it needs pymol+Qt; SMOKE-11 covers that headlessly") and by
  the smoke layer below.

**What never to mock:** `pymol`, `cmd`, Qt — if you feel the need to mock
them, the code belongs in the pure layer instead.

## Smoke Testing (integration/e2e layer — headless Windows PyMOL)

**Runner:** `smoke/run_smoke.sh` (17 lines). From WSL repo root:

```bash
bash smoke/run_smoke.sh smoke/smoke_NN_name.py [timeout_sec]   # default timeout 120
```

Mechanics: `cmd.exe /c "C:\src\run-conda-pymol.bat -cq smoke\<script>"`
(launches Windows PyMOL 2.5.0 headless), output teed to
`/tmp/smoke_out.txt`, then **`grep -q "=== SMOKE-$NN PASS ==="`**
(`smoke/run_smoke.sh:15-17`). **The marker IS the verdict — exit codes
cannot carry verdicts through cmd.exe.** `NN` is parsed from the script
basename (`smoke_04_e2e.py` → `04`); scripts without an NN segment fall
back to `01`.

**21 smoke scripts** `smoke/smoke_01_bootstrap.py` …
`smoke/smoke_21_demo_cleanup.py` covering bootstrap → manifest →
generation → e2e → perf → wizard loop → upload → windows → lifecycle →
checkpoint round-trips → cleanup.

**In-script conventions** (`smoke/smoke_01_bootstrap.py` is the template):
- A `failures = []` list and a `check(name, cond, detail='')` helper that
  prints `SMOKE-NN <name>  PASS/FAIL <detail>` and appends failures
  (lines 63-69).
- Every print stays on ONE line — the runner tees + tails the output;
  multi-line prints complicate grepping (docstring, line 21).
- Final verdict marker, the SOLE verdict carrier:

```python
print('=== SMOKE-01 %s ===' % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'))
```

- Probe parts can be RECORD-ONLY: results print but never enter
  `failures` (`smoke_01_bootstrap.py` Part D).
- Teardown always cleans game objects — "never leave game objects"
  (placement cleanup in `smoke/smoke_04_e2e.py`).
- Repo-root anchoring does NOT trust `__file__` (inside a `-cq` script
  `__file__` points at the PyMOL launcher): anchor order is
  sys.argv-entry → `os.getcwd()` (`smoke_01_bootstrap.py:40-57`).
- `bash -ic` VMD-side analog is not used here; this project is PyMOL-only.

## Coverage

**None enforced** — no coverage config/plugin (stdlib-only constraint).
Coverage expectations are structural instead: one test file per module, the
mechanical audit suites above, refusal classes message-asserted, and the
smoke layer for the PyMOL/Qt tier.

## Adding New Tests — checklist

1. New pure module → `tests/test_<module>.py` with the standard docstring +
   bootstrap; register the module in `PURE_MODULES`
   (`tests/test_purity.py:99`) AND add a registration-pinning test class.
2. New refusal → subclass ValueError family, then message-assert with
   `assertIn(...)` in the test before writing the message.
3. New mechanical invariant → AST over source text (never grep), plus a
   negative control proving the finder fires; add the audit class to the
   relevant audit file.
4. New PyMOL/Qt behavior → cannot be unit-tested in WSL; write/extend a
   `smoke/smoke_NN_*.py` instead, with the `check()` helper, one-line
   prints, and the `=== SMOKE-NN PASS ===` marker.

---

*Testing analysis: 2026-10-03*
