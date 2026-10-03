# Coding Conventions

**Analysis Date:** 2026-10-03

## Hard Constraints (never violate)

**Runtime is Python 3.6.9.** All code in `aamatch/` must compile under
`python3.6 -m py_compile aamatch/*.py` (Gate D, `tests/test_purity.py:270`).
Concretely:
- NO 3.7+ syntax (no `dataclasses` in pure modules, no postponed-evaluation
  annotations tricks requiring 3.7, no 3.7+-only stdlib).
- f-strings ARE 3.6-legal but the codebase uses `%`-formatting everywhere
  (`tests/test_purity.py:157`, `aamatch/persistence.py:53`). Use
  `%`-formatting for consistency.

**Layer purity is mechanically enforced.** There are two tiers:
- **PURE layer** — the 19 modules listed in `PURE_MODULES`
  (`tests/test_purity.py:99-103`): `setup_state`, `level_spec`,
  `persistence`, `backup`, `paths`, `vec3`, `spatial`, `manifest`,
  `capability`, `thresholds`, `detector`, `generator`, `game_state`,
  `wizard_core`, `wizard_text`, `setup_form`, `game_file`, `status_text`,
  `checkpoint`. These import stdlib + other pure modules ONLY — no `pymol`,
  no Qt, no numpy — at module level **OR inside any function body**
  (Gate A scans every AST node, `tests/test_purity.py:152`).
- **CMD/QT tier** — everything else (`engine.py`, `geometry.py`,
  `placement.py`, `wizard.py`, `gamestart.py`, `setup_window.py`,
  `game_window.py`, `upload.py`, `detector` helpers etc.). May import
  `from pymol import cmd` / Qt. Must NEVER be added to `PURE_MODULES`
  (`aamatch/engine.py:3-9` states this explicitly in its docstring).

**Adding a new pure module:** write it, then add its name to `PURE_MODULES` in
`tests/test_purity.py` AND add a `Test<Name>Registration` pinning test
following `TestGeneratorRegistration` (`tests/test_purity.py:294-304`) —
unregistered pure modules are silently ungated, so the registration is
itself pinned.

## Naming Patterns

**Files:** `snake_case.py`, one test file per module: `tests/test_<module>.py`
(`tests/test_vec3.py` ↔ `aamatch/vec3.py`). Smoke scripts:
`smoke/smoke_NN_name.py` (`smoke/smoke_01_bootstrap.py`).

**Functions/methods:** `snake_case` verbs — `validate_state`,
`randomize_state`, `write_json_atomic`, `extract_game_atoms`, `place_aa`.

**Private helpers:** leading underscore — `_to_int`, `_clamp`
(`aamatch/setup_state.py:65-87`), `_read_source` (`tests/test_purity.py:184`).

**Constants:** `UPPER_SNAKE_CASE`, often grouped in
`NAME_DEFAULT, NAME_MIN, NAME_CAP = ...` triples
(`aamatch/setup_state.py:46-50`). Public enums as module-level lists in
canonical order — `INTERACTION_TYPES` (`aamatch/setup_state.py:40`) is the
single home; never duplicate it elsewhere (modules re-export, e.g.
`thresholds.py` re-exports capability's `METAL_ELEMENTS`).

**Version constants:** each artifact pins its own gate —
`FORMAT_VERSION` (`aamatch/persistence.py:37`), `DETECTOR_VERSION` /
`LEVEL_SPEC_VERSION` (`aamatch/level_spec.py`), `CHECKPOINT_VERSION`
(`aamatch/checkpoint.py`).

**Errors:** `<Area>Error` subclassing the ValueError family —
`FormatError(ValueError)` (`aamatch/persistence.py:42`),
`BackupError`, `EngineError`, generator's own error subclassing ValueError
but **deliberately NOT** `persistence.FormatError`
(`aamatch/generator.py:133`) — keep refusal families per-module unless a
shared container parse is literally reused.

## Docstrings (a load-bearing convention)

Every module opens with a LONG docstring naming: **layer** (`Layer: PURE` /
`Layer: CMD TIER` — see `aamatch/engine.py:3`), the design contract, the
research/trace references (e.g. `(D1-D4, R4, P5)`, `(SETUP-06)`) and the
exact invariants/tests that guard it. Docstrings frequently cite upstream
PyMOL source locations (e.g. `plugins/__init__.py:193-210`) and plan IDs
(`(07-02)`). Write docstrings this way — they are the audit trail.

Trace tags used consistently: requirement IDs (`PERSIST-01`, `DETECT-03`,
`PLAY-04`, `SCORE-01`, `SETUP-06`, `GEN-04`), pitfall refs
(`PITFALLS.md:181`, `PITFALL 15`), research refs (`D2`, `B7`, `B8`, `R8.5`),
and phase-plan refs (`(07-02)`, `02-15`).

## Code Style

**Formatting:** no formatter config (no black/ruff/flake8 files). Hand
style: 4-space indent, ~79-char lines, hanging indents aligned, comments
placed in inline columns (`aamatch/setup_state.py:54-62`). String
formatting with `%`. Avoid semicolons/one-liners.

**Imports at module top:** one per line, stdlib-only in pure modules
(`import copy\nimport random`). Relative imports for intra-package pure:
`from .persistence import FormatError, check_container, make_container`
(`aamatch/level_spec.py:58`).

**`aamatch/__init__.py`:** ZERO module-level imports (Gate A2,
`tests/test_purity.py:229-245`). Entry points `__init_plugin__` /
`run_plugin_gui` lazy-import inside function bodies
(`aamatch/__init__.py:25,38`). The `# Key: value` metadata block MUST be
the first lines of the file — PyMOL's loader stops at the first non-`#`
line (`aamatch/__init__.py:1-11`, pinned by `tests/test_package_skeleton.py`).

**Multiple imports in tests:** parenthesized alphabetical lists
(`tests/test_setup_state.py:33-56`).

## State & Data Patterns

**Plain dicts over classes for domain state.** The 7-field setup model is a
module-level `DEFAULTS` dict (`aamatch/setup_state.py:54-62`); validators
return NEW dicts deep-copied from DEFAULTS and **never mutate input**
(contract D3/P6 — `aamatch/setup_state.py:90-106`). `GameState` is plain
data with a `to_dict()` read path, not shared mutable globals.

**Single source of truth per enum/table.** `INTERACTION_TYPES` lives only
in `setup_state.py`; thresholds live only in `aamatch/thresholds.py`;
typing tables only in `aamatch/capability.py`. Other modules import them —
never inline copies (`tests/test_detector_invariance.py:44` imports
`thresholds` and the boundary probes apply deltas to the constants, never
to inline numbers).

**Small pure helpers.** Private coercion helpers with explicit docstrings of
edge behavior (`_to_int` documents `int('x') -> ValueError,
int(None) -> TypeError`, `aamatch/setup_state.py:65-75`).

## Error Handling

**Fail-closed with the ValueError family.** All format/refusal flows raise
`<Area>Error` subclasses of ValueError with HUMAN-readable, prior-art-tested
messages (`aamatch/persistence.py:8-13` pins the exact phrasing patterns:
`"not an AA-match file (...)"`, `"unsupported AA-match format version ...
Please update AA-match."`). Refusal messages are **message-asserted** in
tests — pick stable wording before writing the test
(`tests/test_level_spec.py:176-224`).

**Multi-gate parsers.** Versioned-artifact parsers run a fixed gate chain
(magic → version → kind → payload gates), each raising `FormatError` naming
the failing gate (`aamatch/level_spec.py:81-121`).

**The two version gates (never conflate — `aamatch/thresholds.py:13-18`):**
- container `version` / payload `format_version`: **refuse-newer /
  accept-older** (additive-only evolution; readers use `.get()` defaults —
  `aamatch/persistence.py:71-73`),
- `detector_version`: **EXACT match** (stale AND newer both refused —
  `aamatch/level_spec.py:116-121`). Checkpoint adds its own refuse-newer
  `checkpoint_format_version` gate.

**Atomic writes.** `write_json_atomic`: temp file + fsync + `os.replace`,
`sort_keys`, `indent=2`, binary write, `allow_nan=False` (loud NaN/inf
refusal), best-effort temp cleanup on failure
(`aamatch/persistence.py:93-115`).

**Non-destructive cleanup discipline.** On refusal, original files stay
untouched; game objects are always cleaned in `finally`/explicit cleanup —
"never leave game objects" (`smoke/smoke_04_e2e.py` teardown). GUI slots
catch ValueError-family refusals per button via a guard (`_guard`);
unexpected exceptions propagate fail-closed
(`aamatch/__init__.py:35-37`).

## Banned calls (mechanically enforced)

`cmd.get_model` (OOM trap), `cmd.matrix_reset` (coordinate reverter),
`cmd.get_object_ttt` (segfault hazard) must never be CALLED anywhere in
`aamatch/` or `smoke/` (`tests/test_code_audit.py:56` `BANNED_CALLS`).
Prose mentions exist only at pinned exact counts in
`tests/test_code_audit.py:64-69` (`PROSE_PIN`); any count drift fails the
audit. In UI modules `wizard.py`/`gamestart.py`/`setup_window.py`/
`game_window.py` the helper-visual primitives `cmd.indicate`, `cmd.distance`,
`cmd.load_cgo` are likewise banned (PLAY-04; `tests/test_wizard_source.py:59`).

## WSL/Windows Path Discipline

Windows PyMOL/VMD cannot resolve `/mnt/c/...`. Path conversion goes through
`aamatch/paths.py` (`to_windows_path`); smoke scripts that bootstrap the
package itself carry a local `winpath()` mirror instead of importing the
package (`smoke/smoke_01_bootstrap.py:28-37`, deliberately not circular).

---

*Convention analysis: 2026-10-03*
