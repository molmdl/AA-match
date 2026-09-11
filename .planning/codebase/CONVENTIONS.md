# Coding Conventions

**Analysis Date:** 2026-09-12

## Scope Note

This repo is the PyMOL plugin subtree only: `aamatch/`, `tests/`, `smoke/`,
`docs/`, `.planning/`. There is **no `pymol/` or `vmd/` directory and no Tcl
code** in this repo, despite the parent `AGENTS.md` mentioning them — the
viewer layers referenced there live in sibling projects (`pymol-src` and
`Pymol-script-repo` are symlinks out of tree; do not treat them as code to
edit). All conventions below are Python conventions.

## Language & Toolchain Discipline

**Python 3.6 syntax floor, enforced.** Every `aamatch/*.py` must compile under
`python3.6 -m py_compile` (Gate D in `tests/test_purity.py`), even though the
runtime interpreter is Windows PyMOL's Python 3.9:
- **No `dataclasses`, no f-strings at all.** f-strings are 3.6-legal but are
  not used anywhere in the repo; string formatting is exclusively the `%`
  operator (with one `.format()` in `aamatch/paths.py:50`):

  ```python
  # aamatch/level_spec.py:112 — % formatting with %r for found values
  raise FormatError(
      "unsupported level spec version %d (expected <= %d). "
      "Please update AA-match." % (format_version, LEVEL_SPEC_VERSION))
  ```
- **Stdlib only in the pure layer.** No `numpy`, no `itertools` (recorded
  02-01 convention: "comprehensions and explicit tuple arithmetic only" —
  `aamatch/vec3.py:13-15`).

**No lint/format config exists.** There is no `.flake8`, `setup.cfg`,
`pyproject.toml`, `tox.ini`, `.editorconfig`, `.prettierrc`, or `.eslintrc`
in the repo. (One stray `# noqa: E402` comment appears at
`smoke/smoke_02_manifest.py:56-60` for post-`sys.path` imports — inherited
habit, not a configured rule.) Style is enforced by the mechanical AST gates
in `tests/` (see TESTING.md) and by matching the existing code. Derive style
from the code itself.

**Line width:** ~79 columns in source (a handful of overflow lines exist);
assertion messages and docstrings wrap early with hanging indents.

## Layer Architecture (the one structural rule)

Every module docstring declares its layer on the first lines:

- **PURE layer** — `aamatch/` modules registered in `PURE_MODULES`
  (`tests/test_purity.py:87-90`): `setup_state`, `level_spec`, `persistence`,
  `backup`, `paths`, `vec3`, `spatial`, `manifest`, `capability`,
  `thresholds`, `detector`, `generator`, `game_state`, `wizard_core`,
  `wizard_text`. These import whitelisted stdlib + pure siblings ONLY, at any
  scope (module level or function body — Gate A scans both).
- **CMD TIER** — `aamatch/` modules that import pymol: `engine.py`,
  `placement.py`, `geometry.py`, `wizard.py`, `gamestart.py`. Their docstrings
  open with the identical declaration (e.g. `aamatch/engine.py:3-8`):

  ```
  Layer: CMD TIER. ``from pymol import cmd`` at module level is LEGAL
  here; this module must NEVER be added to ``PURE_MODULES`` in
  ``tests/test_purity.py`` ... NO Qt anywhere.
  ```

  When adding a new cmd-tier module, copy this declaration verbatim (adapt the
  module name). When adding a new pure module, register it in `PURE_MODULES`
  AND add a registration-pin test (pattern: `TestGeneratorRegistration` in
  `tests/test_purity.py:279-289`).
- `aamatch/__init__.py` has **ZERO module-level imports** (Gate A2). Its
  `# Version: x.y.z` / `# Citation-Required: No` comment block MUST be the
  first lines of the file, before the docstring (PyMOL plugin-loader contract,
  pinned by `tests/test_package_skeleton.py`). All imports are lazy inside
  `__init_plugin__`/`run_plugin_gui`.

## Naming Patterns

**Files:** `snake_case.py`, one module per concern
(`aamatch/persistence.py`, `aamatch/level_spec.py`, `aamatch/game_state.py`).

**Functions:** snake_case, verb-first: `make_container`, `check_container`,
`write_json_atomic`, `read_json_file`, `save_container`, `load_container`
(`aamatch/persistence.py`); `to_windows_path`, `package_data_path`
(`aamatch/paths.py`); `parse_level_spec_dict` (`aamatch/level_spec.py`).
Verb pairs are consistent: make/check, save/load, write/read, parse/serialize.

**Private helpers:** single leading underscore, at module level when they
decompose a gate chain: `_is_int`, `_check_seed`, `_check_levels`,
`_check_level`, `_check_molecule_grid` (`aamatch/level_spec.py:64-214`);
`_to_int`, `_to_str`, `_clamp` (`aamatch/setup_state.py:65-87`). Tests call a
leading-underscore helper directly when it is the documented test seam
(`wizard_text._clip` in `tests/test_wizard_text.py:492`).

**Constants:** UPPER_SNAKE public constants at module top
(`AAM_MAGIC`, `FORMAT_VERSION`, `KINDS` in `aamatch/persistence.py:34-37`;
`DEFAULTS`, `INTERACTION_TYPES`, `MOLECULES_DEFAULT/MIN/CAP` in
`aamatch/setup_state.py:40-50`); leading-underscore for module-private
lookups (`_MATRIX_TOL`, `_IDENT_3X4`, `_KEY_NUDGES` in
`aamatch/wizard.py:84-91`; `_CANONICAL_POSITION` in
`aamatch/game_state.py:42`).

**Classes:** PascalCase, rare (function-oriented design). Only plugin shell
classes and exception types: `GameWizard(Wizard)` (`aamatch/wizard.py:100`),
plus exceptions below.

**Single-home rule for enums/constants:** e.g. `INTERACTION_TYPES` lives ONLY
in `aamatch/setup_state.py`; `thresholds` re-exports `capability`'s tables —
"single homes, never duplicates" (`tests/test_purity.py:70-76`). Add a value
to its home module; never re-declare.

## Code Style / Docstrings

**Module docstring is the design contract.** Pattern (every module):
1. First line: `aamatch.<name> -- <one-line purpose> (plan NN-MM)`.
2. Layer declaration (PURE or CMD TIER, see above).
3. Multi-paragraph design contract: data shapes, refusal semantics, versioning
   policy, non-mutation guarantees — with citations to plan IDs (`(plan
   02-13)`), requirement IDs (`DETECT-03`, `SCORE-01`, `PLAY-04`), research
   docs (`materialization research §1.5`), and pitfall lines
   (`PITFALLS.md:274-280`). Example: `aamatch/persistence.py:1-26`,
   `aamatch/wizard.py:1-75`. Use `--` for em-dashes in docstrings (mixed with
   `—`; both appear; `--` dominates).

**Function docstrings:** present on nearly every function, one-line summary
for trivial helpers, multi-line where behavior is contractual. No numpydoc/
Google-style sections; prose with inline ` ``code`` ` (double-backtick RST
style) for identifiers:

```python
# aamatch/persistence.py:91
def write_json_atomic(path, obj):
    """Serialize `obj` to `path` atomically: temp file + fsync + os.replace.

    Byte-stable, diff-able output (sort_keys, indent=2, binary write) and
    loud NaN/Infinity refusal (allow_nan=False). On any failure the temp
    file is removed (best-effort) and the original file is left untouched.
    """
```

**Comments:** explain WHY, cite provenance (`# Source: prior art
demos.py:59-78; research F1-F2, R7` — `aamatch/paths.py:41`), call out
load-bearing lines in CAPS (`# The ``len(parts) == 4`` term is LOAD-BEARING`
— `aamatch/paths.py:37`), and record discoveries with dates (`# DISCOVERY
(2026-09-06, headless probe ...)` — `aamatch/wizard.py`, smoke files).

## Import Organization

Order, always (example `aamatch/engine.py:75-82`):
1. stdlib (`import math`, `import time` — plain `import x` preferred over
   `from x import y` for stdlib),
2. `from pymol import cmd` and other pymol imports (cmd tier only),
3. pure siblings — `from . import capability, detector, ...` grouped on one
   line when several, and/or `from .persistence import read_json_file`
   explicit-name form.

Pure modules never import `pymol`/Qt/`numpy` at ANY scope; gate-checked.
Cmd-tier modules import pymol at module level (never lazily, except
`__init__.py` which imports EVERYTHING lazily). Relative imports
(`from . import engine`) inside cmd-tier bodies are used deliberately so the
module behaves identically under both module identities (`aamatch` vs
`pmg_tk.startup.aamatch` — `aamatch/wizard.py:19-29`).

## Error Handling

**Fail-closed with domain exceptions.** Each tier defines one exception type
subclassing `ValueError`, message naming the cause:

```python
# aamatch/persistence.py:40
class FormatError(ValueError):
    """An AA-match file is foreign, too new, misfiled, or unparseable."""

# aamatch/wizard.py:94 — peers pattern, documented in the class docstring
class WizardError(ValueError):
    """A failed WIZARD op (house fail-closed style, peers with
    EngineError / PlacementError). ..."""
```

Existing peers: `FormatError` (`persistence`), `EngineError` (`engine`),
`PlacementError` (`placement`), `WizardError` (`wizard`), `GenerationError`
(`generator`). New domain errors: subclass `ValueError`, name
`<Domain>Error`, message names the cause and includes the offending value via
`%r`.

**Message phrasing conventions** (`aamatch/persistence.py:8-12`): refusal
messages follow frozen patterns — `"not an AA-match file (...)"`,
`"unsupported ... Please update AA-match."`, `"expected an AA-match <kind>
file, found kind=..."`, `"could not parse AA-match JSON: ..."`. Tests
`assertIn` on these fragments, so **do not reword**.

**Never silent-catch.** Validation raises; no `except: pass`, no sentinel
returns. Degenerate inputs raise (`vec3.unit` raises `ValueError` for the
zero vector rather than producing NaN — `aamatch/vec3.py:64-69`). Fallback-to-
default coercions are allowed ONLY where documented (`_to_int`, `_to_str` in
`aamatch/setup_state.py`) — invalid enums fall back to defaults, that IS the
contract there.

**Cleanup discipline:** `try/finally` for PyMOL object lifetimes (temp
objects deleted in a `finally`, atomic-write temp removed on
`except BaseException` — `aamatch/persistence.py:102-113`).

**Non-mutation (P6):** validators/validators take input, return NEW objects
built from `deepcopy(DEFAULTS)`; inputs are never mutated
(`aamatch/setup_state.py:15-16`).

## Logging

**None in library code.** No `logging` import anywhere. The pure/cmd tiers
communicate by returning plain data and raising exceptions; PyMOL's menu
handler surfaces tracebacks (`aamatch/__init__.py:36-37`). Smokes print
single-line PASS/FAIL records (see TESTING.md). Do not introduce `logging`
or `print` into `aamatch/` modules.

## Function & Module Design

**Functions over classes; plain data in/out.** Engine ops take/return plain
dicts/lists/tuples ("each count-asserted; plain-data in/out" —
`aamatch/engine.py:33`). Wizard instance attributes are plain picklable data
ONLY (session-pickle contract — `aamatch/wizard.py:19-29`).

**Small gate-chain decomposition:** one public validator delegates to
`_check_*` helpers in declaration order (`aamatch/level_spec.py:98-214`).
Follow this for new validators; each helper's docstring names its gate.

**Constants over literals:** detection cutoffs live ONLY in
`aamatch/thresholds.py` — "the tests never inline a cutoff"
(`tests/test_detector.py:13-15`).

## Version Control

**Commit style: Conventional Commits with phase-plan scope**
(`git log`): `feat(03-06):`, `fix(03-06):`, `test(03-06):`, `docs(03-06):`,
`feat(03-05): ...`; repo-wide work uses bare type (`chore:`, `doc:`).
Messages are short imperative summaries, often with dashes for subtleties
(`test(03-06): SMOKE-07 PART F -- the field-bug batteries`). Planning docs
are committed with the code they describe.

---

*Convention analysis: 2026-09-12*
