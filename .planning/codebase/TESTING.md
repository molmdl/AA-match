# Testing Patterns

**Analysis Date:** 2026-09-12

## Test Framework

**Runner:**
- stdlib `unittest` ONLY (no pytest, no nose). Python 3.6.9 in WSL.
- No config file (no `pytest.ini`, `tox.ini`, `setup.cfg`) — discovery is
  driven entirely by `unittest discover`.

**Assertion library:** `unittest.TestCase` methods (`assertEqual`,
`assertIn`, `assertRaises`, `assertAlmostEqual`, `subTest`, ...).
**Mocking:** `unittest.mock` only (used sparingly — 2 files).

**Run Commands:**
```bash
python3.6 -m unittest discover -s tests -v     # the full WSL suite (incl. purity gates)
python3.6 -m unittest tests.test_purity -v     # one module
python3.6 -m py_compile aamatch/*.py           # 3.6 syntax floor (also Gate D)
bash smoke/run_smoke.sh smoke/smoke_01_bootstrap.py   # headless Windows PyMOL smoke
```
All run from the repo root.

**Three test tiers** (each with a distinct verdict carrier):
1. **WSL unit tests** — `tests/test_*.py`, pure-Python, zero PyMOL.
2. **Mechanical AST gates** — also in `tests/`, scan source text
   (`test_purity.py`, `test_code_audit.py`, `test_wizard_source.py`).
3. **Headless smoke proofs** — `smoke/smoke_NN_*.py` run inside real Windows
   PyMOL via `cmd.exe`; verdict is a grepped marker, not an exit code.

## Test File Organization

**Location:** flat `tests/` directory, one file per source module
(`aamatch/level_spec.py` → `tests/test_level_spec.py`). `tests/__init__.py`
is a single comment line. Cross-cutting suites are named for their purpose,
not a module: `tests/test_purity.py`, `tests/test_code_audit.py`,
`tests/test_package_skeleton.py`, `tests/test_generator_invariants.py`,
`tests/test_detector_invariance.py`.

**Naming:** files `test_<module>.py`; classes `Test<Concept>` (`TestGateA2LazyInit`, `TestCheckContainer`, `TestBuildSlotMap`); methods long descriptive snake_case (`test_newer_version_refused_with_update_message`, `test_garbage_file_refused_with_parse_message`).

**Module docstring is mandatory** on every test file and must state: scope,
the plan ID it serves, and the zero-stub run conditions. Pattern
(`tests/test_persistence.py:1-14`):

```python
"""Tests for aamatch.persistence -- versioned container core + atomic JSON I/O.

RED-first suite for plan 01-02 (PERSIST-01 format discipline). Covers:
- container construction (magic/version/kind/data, exact shape)
- all three refusal classes with message assertions ...
Runs under bare python3.6 in WSL with stdlib only (no pymol/Qt/numpy
stubs needed -- the module under test is pure).
"""
```

**Bootstrap block** — every test file inserts the repo root on `sys.path`
before importing `aamatch`, so suites run both via `discover -s tests` and as
direct modules (`tests/test_purity.py:55-61`):

```python
_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(_HERE, '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
```

## The Zero-Stub Contract (critical)

Tests import pure modules directly — `from aamatch.persistence import ...` —
with **ZERO `sys.modules` stubs anywhere** (`AGENTS.md` gate 2). This works
because `aamatch/__init__.py` has no module-level imports (Gate A2) and pure
modules never import pymol/Qt/numpy at any scope. **Do NOT add stub patterns
from the old research docs; they are explicitly superseded and enforced
against by `tests/test_purity.py`.**

## Test Structure & Assertions

**TDD, RED-first:** suites are written before implementation; the docstring
records it (`tests/test_wizard_core.py:1-10`: "simply collecting this module
raises ImportError -- that failure IS the RED proof").

**Exact-equality discipline:**
- Round-trip tests use `assertEqual` on parsed structures — `"Exact equality
  after load (NEVER assertAlmostEqual)"` (`tests/test_persistence.py:128`).
- Float geometry: `assertAlmostEqual(..., places=N)` with pinned precision —
  `places=12` for vec3 unit tests, `places=6..9` for detector metrics
  (`tests/test_detector.py` throughout).

**Error assertions always check the message:**
```python
with self.assertRaises(FormatError) as ctx:
    check_container(newer, 'setup')
message = str(ctx.exception)
self.assertIn('unsupported', message)
self.assertIn('Please update AA-match', message)   # frozen phrasing
```
(`tests/test_persistence.py:88-94`). Error message fragments are part of the
public contract — see CONVENTIONS.md.

**Parametrization via `subTest`** (used in 6+ files):
```python
for mod in PURE_MODULES:
    with self.subTest(module=mod):
        ...
```
(`tests/test_purity.py:237-238`; heavier batteries in
`tests/test_generator_invariants.py` nest two levels).

**Temp files:**
```python
def setUp(self):
    self.tmp = tempfile.mkdtemp(prefix='aamatch-test-')
    self.addCleanup(shutil.rmtree, self.tmp)
```
(`tests/test_persistence.py:123-125`) — `addCleanup`, never `tearDown`.

**Expensive fixture builds** use `setUpClass` (`tests/test_detector.py:580,1054,1637`).

## Mocking

**Framework:** `from unittest import mock` — but only TWO test files use it.
The canonical use is **failure injection on OS calls**, never for the domain
(`tests/test_persistence.py:164`):

```python
with mock.patch('os.replace', side_effect=OSError('boom')):
    with self.assertRaises(OSError):
        write_json_atomic(path, {'marker': 'new'})
```

**What to mock:** OS-level failure points (`os.replace`) to prove cleanup
invariants (no `.tmp` litter, original file intact).
**What NOT to mock:** pymol (impossible — cmd tier is proven by smokes, not
unit tests; stubbing pymol is exactly the forbidden stub pattern), and never
the module under test's pure logic.

## Fixtures and Factories

**Hand-scripted, module-level builder functions** with leading underscore —
no factory libraries, no fixtures directories:

```python
# tests/test_detector.py:38 — plain-dict atom records, hand-placed geometry
def _lig_atom(idx, name, elem, x, y, z, fc=None):
    """Ligand-side atom record; id == ligand-sublist index for clarity."""
    record = {'side': 'lig', 'object': 'ligand', 'id': idx, 'name': name,
              'elem': elem, 'resn': 'LIG', 'resi': 1, 'alt': '',
              'x': float(x), 'y': float(y), 'z': float(z)}
    ...
```

Other examples: `_registry_two_molecules()` (`tests/test_wizard_core.py:35`),
`_non_default_raw_state()` (`tests/test_setup_state.py:69`), scripted ligand
geometries `_carbonyl_ligand`/`_ammonium_ligand` (`tests/test_detector.py:86-110`).
Simple constants dicts (`EXPECTED_KEYS` at `tests/test_setup_state.py:58`) at
module level. Real bundled data lives under `aamatch/data/` (consumed via
`paths.package_data_path`), not under `tests/`.

## The AST Gate Pattern (repo-specific, reuse it)

Mechanical audits are unit tests over **source text**, not behavior. Every
gate pair follows one shape (`tests/test_purity.py`, `tests/test_code_audit.py`,
`tests/test_wizard_source.py`):

1. **A pure finder function over source text** — e.g. `find_bad_imports(src)`
   (`tests/test_purity.py:119`) walks the `ast` tree; immune to the
   "docstring-says-the-token" grep tripwire by construction.
2. **A NEGATIVE CONTROL** proving the finder can fail — synthetic source with
   real `import pymol` + prose repeating the tokens; the gate must flag
   exactly the real imports (`TestNegativeControl`,
   `tests/test_purity.py:303-326`). "A gate that cannot fail proves nothing."
3. **PROSE_PIN allowances with exact counts** (`tests/test_code_audit.py:64-69`)
   when prose mentions are legitimate — any count drift fails and demands
   human re-review: "inspect, never blind-fail" (Gate C discipline).
4. **Registration-pin tests** when a registry grows — `PURE_MODULES` scans
   skip unregistered modules silently, so `TestGeneratorRegistration`
   (`tests/test_purity.py:279-289`) pins that each new pure module is
   actually gated. Add one per new pure module.

New cross-module source rules (banned calls, banned visuals, import
whitelists): implement them THIS way, in a new `tests/test_*` file or by
extending the existing gate files.

## Smoke Tests (headless Windows PyMOL)

**Runner:** `bash smoke/run_smoke.sh smoke/smoke_NN_name.py [timeout_sec]`
(`smoke/run_smoke.sh`) — cds to repo root, launches
`cmd.exe /c C:\src\run-conda-pymol.bat -cq smoke\<script>`, tees output, and
`grep -q "=== SMOKE-$NN PASS ==="`. **Exit codes cannot cross cmd.exe; the
printed marker is the sole verdict carrier.**

**File conventions** (every smoke script; see `smoke/smoke_01_bootstrap.py`,
`smoke/smoke_02_manifest.py`):

- Leading docstring: purpose, run command, and the marker line to grep.
- `_find_repo_root()` helper — anchor via `sys.argv` entry first, `os.getcwd()`
  fallback, **NEVER `__file__`** (inside a `-cq` script `__file__` points at
  `pymol/__init__.py`, probe-proven; `smoke/smoke_01_bootstrap.py:40-57`).
- Module-level `failures = []` plus a `check` helper printing ONE line,
  flushed:

  ```python
  def check(name, cond, detail=''):
      print('SMOKE-02 %-38s %s %s' % (name, 'PASS' if cond else 'FAIL', detail),
            flush=True)
      if not cond:
          failures.append(name)
  ```
- Try/except blocks around each part with `traceback.print_exc()` then
  `check(..., False, ...)` — the smoke must reach its marker even when broken.
- Post-`sys.path` imports may carry `# noqa: E402`
  (`smoke/smoke_02_manifest.py:56-60`).
- Final line: `print('=== SMOKE-NN %s ===' % ('FAIL: ' + ', '.join(failures)
  if failures else 'PASS'))` — NN matches the filename number.
- Import `aamatch` directly (identity `aamatch`) OR use the real
  `plugin_load` loader (identity `pmg_tk.startup.aamatch`) — **never both in
  one session** (`AGENTS.md` gate 5; `smoke_01` demonstrates each in separate
  labelled parts).
- RECORD-ONLY probes (`SMOKE-ENV` lines, `smoke_01` Part D) may gather facts
  but never append to `failures`.
- Written 3.6-safe even though it runs under PyMOL's Python 3.9.

## Coverage

**None.** No coverage tool, no config, no target. Protection comes from the
AST gates + RED-first hand-computed batteries + smokes. (Coverage gaps are a
documented concern class, not a metric — see CONCERNS.md when written.)

## Test Types

**Unit tests:** `tests/test_*.py` over the PURE layer only — pure functions,
dict contracts, refusal message classes, seeded determinism
(`random.Random(seed)`), invariant batteries
(`tests/test_generator_invariants.py`, `tests/test_detector_invariance.py`).

**Mechanical/architecture tests:** the AST gates above — these ARE the
architectural enforcement; treat them as load-bearing.

**Integration/E2E:** the smokes — real PyMOL, real `cmd`, GUI-adjacent flows
proven headlessly (`smoke_07_wizard_loop.py` drives the whole wizard loop;
`smoke_04_e2e.py` the engine op chain). There is no GUI automation tier;
GUI real-mouse verification is a human checkpoint per `AGENTS.md`.

---

*Testing analysis: 2026-09-12*
