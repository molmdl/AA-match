# Phase 1 Research — Pure-Foundation Modules + Python 3.6 stdlib-only Test Discipline

**Phase:** 1 — Bootstrap & Pure Foundation (scope: setup_state / persistence / level_spec / backup / paths + WSL test gates; NOT the plugin skeleton/install/headless toolchain — parallel research covers those)
**Researched:** 2026-09-05
**Confidence:** HIGH (every prior-art claim below is `file:line` from the readable prior-art tree `tmp/bioCHEMeleon/`; every environment claim was executed on the actual WSL `python3.6` shell today; UNVERIFIED items are flagged explicitly per the truthfulness constraint)

---

## Summary

The prior art (`tmp/bioCHEMeleon/biochemeleon/`) proves three of the four mechanisms directly: a versioned sidecar with magic+version refusal (`persistence.py`), a pure validated/randomizable setup-state model (`setup_state.py`), and a snapshot/restore/discard/verify backup contract (`backup.py`). But **AA-match Phase 1 requires MORE than the prior art shipped**, in three specific ways: (1) prior art's *setup* save/load had **no version/foreign-format refusal at all** (`gui_setup.py:661-686` — plain `json.load` + tolerant validate), while PERSIST-01 demands refusal — so the header discipline must be unified across ALL file kinds, not just sidecars; (2) prior art's `to_windows_path()` lived in the cmd tier (`demos.py:59-78`) and was **never WSL-unit-testable**, while Phase 1 requires it unit-tested — it must move to a pure module; (3) prior art's `backup.py` is **cmd-coupled and only py_compile-checkable in WSL** (`backup.py:24-27`), while Phase 1 requires the backup module unit-tested in WSL — it needs a pure core with an injected store. Each gap has a verified prior-art pattern to adapt (magic/version refusal from `persistence.py:130-145`; dependency injection precedent from `registry.py` per ARCHITECTURE.md:136).

**Primary recommendation:** Build one reusable versioned-container core (magic + version + kind + atomic JSON I/O) in `persistence.py`, pure data models with `validate_state`/`randomize_state` in `setup_state.py`, a reserved-for-Phase-2 schema with an exact-match `detector_version` gate in `level_spec.py`, a store-injected pure `backup.py`, a pure `paths.py` port of the proven path guard — and enforce purity with an **AST import-gate + clean-subprocess import test** (immune to the grep-gate docstring false positives that bit the prior art, PITFALLS.md:83), with `aamatch/__init__.py` kept lazy-import so tests need **zero stubs** (unlike prior art, which needed MagicMock stubs — `test_setup_state.py:13-15`).

Citation shorthand used below:
- `[PA-persist.py:N]` = `tmp/bioCHEMeleon/biochemeleon/persistence.py` (279 lines, read in full)
- `[PA-setup.py:N]` = `tmp/bioCHEMeleon/biochemeleon/setup_state.py` (544 lines, read in full)
- `[PA-backup.py:N]` = `tmp/bioCHEMeleon/biochemeleon/backup.py` (85 lines, read in full)
- `[PA-demos.py:N]` = `tmp/bioCHEMeleon/biochemeleon/demos.py`
- `[PA-gui.py:N]` = `tmp/bioCHEMeleon/biochemeleon/gui_setup.py`
- `[PA-test-*.py:N]` = `tmp/bioCHEMeleon/tests/*`
- `[ENV]` = verified by executing on this WSL machine today (python3.6.9)
- `[SPEC:N]` = `spec.md` · `[REQ:N]` = `.planning/REQUIREMENTS.md` · `[ROAD:N]` = `.planning/ROADMAP.md` · `[PIT:N]` = `.planning/research/PITFALLS.md` · `[ARCH:N]` = `.planning/research/ARCHITECTURE.md` · `[STACK:N]` = `.planning/research/STACK.md`

---

## Verified Facts

### A. Environment — WSL python3.6.9 stdlib (all executed on this machine, 2026-09-05)

| # | Fact | Evidence |
|---|------|----------|
| A1 | `python3.6` = 3.6.9 | `python3.6 --version` → `Python 3.6.9` |
| A2 | Available stdlib (all imported OK in one pass): `json, unittest, tempfile, shutil, zipfile, hashlib, os, random, copy, math, time, io, re, collections` (incl. `namedtuple`, `OrderedDict`), `errno`, `ast` | executed |
| A3 | `import dataclasses` → `ModuleNotFoundError` (3.7+ only) | executed; matches PITFALLS.md:74,77 |
| A4 | `import numpy` → `ModuleNotFoundError` | executed; matches PITFALLS.md:74,77 |
| A5 | `json.loads` accepts `bytes` directly (3.6 feature) | executed; prior art still hand-decodes bytes first (`PA-persist.py:130-131`) — defensive, fine to keep |
| A6 | `json.dumps`→`json.loads` is an **exact** round-trip for finite floats (repr-based shortest repr) | executed: `json.loads(json.dumps(0.1234567890123456789)) ==` original |
| A7 | `json.dumps(..., allow_nan=False)` raises `ValueError` on NaN/Infinity → use it so save fails loudly instead of emitting non-standard JSON | executed |
| A8 | `json.dumps(..., sort_keys=True)` gives byte-stable, diff-able, checksum-stable output | executed |
| A9 | `os.replace` exists on 3.6.9 (atomic-overwrite rename; POSIX rename atomicity is OS-standard; Windows maps to MoveFileEx-with-replace — the Windows-atomicity nuance is **MEDIUM**, from API knowledge, not repo-verifiable) | executed for availability; semantics flagged in OQ5 |
| A10 | `hashlib.sha256` available | executed |
| A11 | unittest invocation conventions proven by prior art: `python3.6 -m unittest tests.test_setup_state -v` and discover form `python3.6 -m unittest discover -s tests -v`; `python3.6 -m py_compile` checks SYNTAX only, not imports | `PA-test-setup_state.py:3`, STACK.md:141, `PA-backup.py:24-27` |

### B. Prior art `persistence.py` (279 lines, pure) — the versioned-format template

File: `tmp/bioCHEMeleon/biochemeleon/persistence.py` (all cites this file unless noted)

| # | Fact | Cite |
|---|------|------|
| B1 | Magic header constant: `BCM_MAGIC = 'BIOCHEMELEON-BCM'` written into every sidecar so parsing can "refuse non-bioCHEMeleon JSON with a clear error" | 33-35 |
| B2 | Numeric schema version: `BCM_VERSION = 1`; parse "refuses version > BCM_VERSION so a newer sidecar … surfaces a clear 'please update' error rather than silently mis-parsing" | 37-40 |
| B3 | Refusal semantics in `parse_bcm_dict`: bytes→utf-8 decode; `json.loads` failure → `ValueError("could not parse .bcm JSON: %s")`; magic mismatch → `ValueError("not a bioCHEMeleon sidecar (magic=%r, expected %r)")`; `version > BCM_VERSION` → `ValueError("unsupported .bcm version %d (expected %d). Please update bioCHEMeleon.")`. **Version < current is ACCEPTED** (no lower-bound check) — older files load via `.get()` defaults | 130-145 |
| B4 | `apply_bcm_dict` re-checks magic+version independently, then reads every field with `.get(field, default)` → forward-compatible reading of older files (defense in depth: parse AND apply both gate) | 177-188 |
| B5 | `build_bcm_dict` validates `kind ∈ {'checkpoint','puzzle'}` else `ValueError`; elapsed time is passed in **explicitly by the caller** to avoid the modal-dialog timer pitfall; transient fields (`_backup_name`, `_wizard`, callbacks, `_start_time`) are documented as NOT serialized — and a unit test enforces the non-leak | 56-77; leak test at `PA-test-persistence.py:137-146` |
| B6 | Archive I/O: `write_bcmz` = `zipfile.ZipFile(path,'w',ZIP_DEFLATED)` + `zf.write(pse)` + `zf.writestr('game.bcm', json.dumps(d, indent=2))` — **direct write, NO temp+rename atomicity** (a gap to fix in AA-match); `read_bcmz` validates member names (`game.bcm`/`game.pse` presence) with clear `ValueError`s before extracting, extracts `.pse` to `tempfile.mkdtemp` | 211-213, 236-247 |
| B7 | Purity contract, verbatim: "Purity: module-level imports are stdlib (json, os, tempfile, time, zipfile) + … ONLY. **NO `pymol` import at module level OR inside any function body.**" | 13-15 |
| B8 | Dependency direction, verbatim: `setup_state.py (PURE) <- registry.py (PURE) <- persistence.py (THIS) <- game.py (orchestrator) <- __init__.py (composition root)` — persistence imports the data models, never the reverse | 17-19 |
| B9 | The embedded `setup` dict is carried verbatim inside the sidecar (`'setup': setup_state`) so an exported file is self-describing | 108-109 |

### C. Prior art setup-file save/load — what actually happened (and what to NOT copy)

File: `tmp/bioCHEMeleon/biochemeleon/gui_setup.py`, `setup_state.py`

| # | Fact | Cite |
|---|------|------|
| C1 | Setup format tag is a **field inside the dict**: `SETUP_FORMAT = "biochemeleon-setup-v1"`, and `DEFAULTS["format"] = SETUP_FORMAT` | `PA-setup.py:115,119` |
| C2 | Save Setup = `QFileDialog` + `open(path,'w')` + `json.dump(self.collect_state(), f, indent=2)` — text mode, **no atomic write, no header, no checksum**; only a `.bcm.setup.json` extension convention | `PA-gui.py:644-659` |
| C3 | Load Setup = `json.load` → `validate_state(state, atom_count=…)` → `apply_state(validated)`. **There is NO magic/version/foreign-format check on setup files at all** — a foreign JSON file loads and silently becomes defaults via validate tolerance | `PA-gui.py:661-686` |
| C4 | `apply_state` tolerates missing keys ("forward-compat with future fields") — the GUI-side mirror of the `.get()` reader pattern | `PA-gui.py:559-564` |
| C5 | Setup files stored **session-local data** (`selected_object` = a live PyMOL object name) — acceptable there, but a lesson: AA-match's upload-path field needs deliberate portability semantics (OQ3) | `PA-gui.py:548`; `PA-setup.py:121` |
| C6 | **Consequence for AA-match:** PERSIST-01's "versioned header refuses newer/foreign formats with a clear message" (`ROAD:37`) is *new* behavior for setup files — the design must route setup save/load through the same container discipline as the sidecar, not replicate C2/C3 | `ROAD:32-38` |

### D. Prior art `setup_state.py` — the pure param-model template

File: `tmp/bioCHEMeleon/biochemeleon/setup_state.py`

| # | Fact | Cite |
|---|------|------|
| D1 | Module docstring: "single source of truth for the setup-configuration data schema … NO Qt and NO pymol.cmd dependencies so it can be unit-tested in WSL without PyMOL installed" | 1-12 |
| D2 | `DEFAULTS` is a complete dict with exactly one entry per field; a unit test asserts the exact key set so schema drift fails loudly | 118-130; key-set test `PA-test-setup_state.py:60-69` |
| D3 | `validate_state(state, …)` returns a **NEW dict** (deepcopy of DEFAULTS as base, never mutates input); fills missing keys from DEFAULTS; invalid enum → default (`mode if mode in _VALID_MODES else "loaded"`, `_VALID_MODES` at 133); int fields via `try: int(...)` except → default, then clamp `max(1, min(cap, hc))`; bool coercion; invalid list items dropped | 341-413 (esp. 355-411) |
| D4 | `randomize_state(seed=None, …)` uses a local `random.Random(seed)` → **deterministic when seeded**; returns a complete state with all DEFAULTS keys | 247-338 (rng at 279) |
| D5 | Pure constants/helpers live in the pure layer so cmd modules import FROM the pure module, never the reverse (`GAME_REPS`, `DEMO_MANIFEST`) | 8-11, 23-57 |

### E. Prior art `backup.py` (85 lines, cmd-coupled) — the contract template only

File: `tmp/bioCHEMeleon/biochemeleon/backup.py`

| # | Fact | Cite |
|---|------|------|
| E1 | Contract = `snapshot / restore / discard / verify_intact`; rationale: PyMOL Open Source ships a no-op `undocontext` stub (`editor.py:25-36`), so "every destructive mutation MUST be preceded by a snapshot and followed by either a discard (happy path) or a restore (failure path), with verify_intact as the structure-integrity proof" | 1-28; also PITFALLS.md:218-238 |
| E2 | `snapshot` discards stale backup first, then fresh independent copy; backup name is underscore-prefixed private (`BACKUP_PREFIX = '_bchm_backup'`) | 34, 39-44 |
| E3 | `restore` = **delete+create two-step, never single-call `cmd.create(existing, backup)`** ("merge-vs-replace ambiguity … UNVERIFIED C-dispatched"); returns True/False; caller asserts the return value — never re-derive by re-calling on a discarded backup (`CmdException` trap) | 52-64; prior-art AGENTS.md Phase-3 rules; PITFALLS.md:228-229 |
| E4 | `verify_intact` = cheap count gate + `(resn, resi, name, chain, segi)` **multiset** compare via `cmd.iterate(..., space={'stored': ...})`; coords omitted because iterate doesn't expose x/y/z | 69-85 |
| E5 | The module is **cmd-coupled**: `from pymol import cmd` at module level; WSL gets py_compile only; runtime verified by smoke | 29, 24-27 |
| E6 | **Consequence for AA-match:** Phase 1 success criterion 2 requires the backup module unit-tested in WSL stdlib-only (`ROAD:38`) → keep the contract (E1) but implement a **pure core over an injected store**, deferring the cmd-backed adapter to the cmd tier (injection precedent: ARCHITECTURE.md:136) | `ROAD:38` |

### F. Prior art `to_windows_path` — proven guard semantics, wrong layer

File: `tmp/bioCHEMeleon/biochemeleon/demos.py`

| # | Fact | Cite |
|---|------|------|
| F1 | It is a **GUARD, not an unconditional transform**: "only paths starting with /mnt/<letter>/ are converted; all other paths (already-Windows C:\... from an installed plugin, or genuine Linux paths) are returned unchanged" | 59-78 (docstring 60-66) |
| F2 | Implementation: `p.replace('\\','/').split('/',3)`; converts iff `parts[0]=='' and parts[1]=='mnt' and len(parts[2])==1 and isalpha` → returns `'{drive.upper()}:\{rest with backslashes}'` | 70-78 |
| F3 | Output form is **backslash Windows form** (`C:\...`), shipped and proven across all v1 phases (prior-art AGENTS.md:85: "converts /mnt/c/... → C:\... only for WSL mount paths"); every `cmd.load`/`cmd.save` call routes through it | 77; prior-art AGENTS.md:85; STACK.md:86; call sites demos.py:191, 489, 513, 547 |
| F4 | It lives in the **cmd tier** (`demos.py` imports `from pymol import cmd` at 49) → was NOT unit-testable in WSL; prior art has no test for it. AA-match Phase 1 explicitly requires it unit-tested (`ROAD:38`) → move to a pure module | 49 vs `ROAD:38` |
| F5 | Whether Windows PyMOL `cmd.load` also accepts forward-slash `C:/...` form is **UNVERIFIED** (Windows-runtime behavior, not visible in the Python source tree; prior art always produced backslashes) — moot if the helper keeps the proven backslash output; a one-line headless smoke can record it (OQ4) | UNVERIFIED |

### G. Prior art test discipline — what to keep, what to fix

| # | Fact | Cite |
|---|------|------|
| G1 | Tests stubbed `sys.modules['pymol']`/`['pymol.Qt']` with MagicMock **because `__init__.py` imported Qt at module level** — PITFALL 1 names this as the anti-pattern and prescribes lazy imports so "pure/cmd modules import cleanly without stubs" | `PA-test-setup_state.py:11-15`, `PA-test-persistence.py:22-26`; PITFALLS.md:36; prior-art AGENTS.md Tests section |
| G2 | sys.path bootstrap for direct-script mode: `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))` (discover mode from repo root also works — STACK.md:141) | `PA-test-setup_state.py:17-19` |
| G3 | Grep gates existed as documented shell commands with an explicit false-positive warning: "literal tokens in comments/docstrings trip this grep too (we hit a false positive on a docstring that said 'from PyQt5 import')"; PITFALL 3 prescribes inspecting matches, not blind-failing | prior-art AGENTS.md Commands; PITFALLS.md:83 |
| G4 | High-value test patterns to adopt: exact-key-set test for DEFAULTS (D2); transient-key non-leak test (B5); refusal-message tests for magic/version (B3 contract); file round-trip via tempfile/shutil in tests | `PA-test-persistence.py:12-19, 137-146`; `PA-test-setup_state.py:60-69` |

### H. Requirements anchoring the Phase-1 scope (what the modules must serve)

| # | Fact | Cite |
|---|------|------|
| H1 | PERSIST-01: "Setup parameters save to / load from a file (versioned format)" — mapped to Phase 1 | `REQ:68,156` |
| H2 | Phase-1 success criteria: (1) setup round-trip through a versioned save file, every field preserved, versioned header refuses newer/foreign formats with a clear message; (2) `setup_state`, `level_spec`, `persistence`, backup module (snapshot/restore/verify) unit-test stdlib-only (no pymol/Qt/numpy/dataclasses); `to_windows_path()` unit-tested | `ROAD:37-38` |
| H3 | Phase 4 depends on Phase 1 "(persistence formats, path helper)"; Phase 4 "Export format reuses the Phase-1 versioned-format discipline"; Phase 7 (`.aamz` zip of `.pse` + JSON sidecar, magic+`STATE_VERSION` refuse-newer) builds on the same core | `ROAD:80,87,123-131`; ARCH:338-345 |
| H4 | Setup params per spec: demo-set dropdown OR upload; molecules per level ("default 2-5, reasonable cap"); difficulty levels per game ("default 3-5, reasonable cap"); allowed-interactions list with three modes: exclusive (`any`), block-exclusive (specific selected), unset→random | `SPEC:13-20`; SETUP-04/05/06 `REQ:19-21` |
| H5 | Required interactions in-game display: "can be `any` or from the allowed list" | `SPEC:38`; SCORE-04 `REQ:58` |
| H6 | v1 interaction set (7 types): H-bond, salt bridge (ionic folded in), π-stacking, cation-π, hydrophobic, halogen, metal coordination (conditional on metal in ligand) | PROJECT.md:71; DETECT-01/02 `REQ:47-48` |
| H7 | Score = fraction of required interactions formed, binary per interaction; skip stores partial score | PROJECT.md:34; SCORE-01/05 `REQ:55,59` |
| H8 | Levels always solvable by grid generation; difficulty expressed via grid N, molecule size, required-interaction-type count; NxN grid depends on difficulty; per-molecule grids | PROJECT.md:73; GEN-03/04/05 `REQ:32-34`; `SPEC:7,61` |
| H9 | Detector-version stamp embedded in generated specs; stale games refused with clear message | prior decision; DETECT-05 `REQ:56`; PITFALLS.md:274-275,280 |
| H10 | Explicit partner sides (AA vs small molecule) recorded so hint/solvability/scoring agree → level_spec must carry per-AA capability data | DETECT-04 `REQ:50` |
| H11 | Reset-to-grid and crash recovery replay the spec ("the seeded level spec is the source of truth") → grid poses belong in the spec | ARCH:202,250-252; SCORE-10 `REQ:64` |
| H12 | Generation discipline the schema must support: one global RNG, deterministic seeds stored in the manifest, tests assert invariants not absolute placements | PITFALLS.md:276-279 |
| H13 | Protonation state is per-molecule source data (demo sets carry protonation from known binding databases; uploads are SDF/MOL2) — NOT a setup param | `SPEC:7,61`; SETUP-03 `REQ:18` |

---

## Design Recommendations

### R1. Module set for Phase 1 (pure layer) and dependency direction

```
aamatch/
├── __init__.py        # plugin skeleton: __init_plugin__ ONLY; ZERO module-level
│                      #   pymol/Qt imports (lazy imports inside functions) — the
│                      #   prerequisite that makes every pure test stub-free (G1, PITFALLS.md:36)
├── setup_state.py     # PURE: setup param model — DEFAULTS, INTERACTION_TYPES,
│                      #   validate_state, randomize_state, clamping constants
├── level_spec.py      # PURE: level-spec schema constants + DETECTOR_VERSION gate +
│                      #   dict-level parse/normalize (no file I/O)
├── persistence.py     # PURE: versioned-container core (magic/version/kind/refusals)
│                      #   + setup-file save/load + atomic JSON I/O
│                      #   imports setup_state (+ level_spec) — direction per B8
├── backup.py          # PURE: snapshot/restore/discard/verify_intact over an
│                      #   injected store (MemoryStore, FileStore included)
└── paths.py           # PURE: to_windows_path + package-relative path resolution
tests/                 # test_setup_state, test_level_spec, test_persistence,
                       #   test_backup, test_paths, test_purity (the gates)
```

Dependency direction (strictly downward, mirrors B8): `setup_state, level_spec, paths, backup` (leaf models) ← `persistence` ← later orchestrator/cmd/Qt tiers. `level_spec.py` must NOT import `setup_state.py` (independent schemas); `persistence.py` may import both. Keep file I/O out of `setup_state`/`level_spec` (pure dicts in/out; `persistence` owns files) — mirrors prior art (D1, B7) and keeps every schema function trivially unit-testable.

### R2. Versioned container core (in `persistence.py`) — one format, all file kinds

Unify what prior art split across two conventions (sidecar magic+version B1-B3 vs setup `format` field C1-C3) into ONE container used by setup files (Phase 1), level-spec/game files (Phase 4), checkpoint sidecars (Phase 7):

```python
AAM_MAGIC = "AAMATCH"          # single magic for every AA-match file
FORMAT_VERSION = 1             # container/schema version; refuse > this

def make_container(kind, data):    # kind: 'setup' | 'level_spec' | 'game' | 'checkpoint'
    return {"magic": AAM_MAGIC, "version": FORMAT_VERSION, "kind": kind, "data": data}

class FormatError(ValueError): pass    # one exception type; message distinguishes cause

def check_container(raw_dict, expected_kind):
    # 1. magic mismatch            -> FormatError("not an AA-match file (magic=%r, expected %r)")   [foreign]
    # 2. version > FORMAT_VERSION  -> FormatError("unsupported AA-match format version %d (expected <= %d). Please update AA-match.")  [newer]
    # 3. kind != expected_kind     -> FormatError("expected an AA-match %s file, found kind=%r")      [misfiled]
    # (version < current is ACCEPTED — additive-only evolution; readers use .get defaults, per B3/B4)
```

**Refusal semantics (answers RQ1's "what IS foreign"):** "foreign" = magic mismatch (not our file at all — includes any random JSON, which prior art's setup loader silently accepted, C3) or wrong `kind` (a setup file fed where a game file is expected). "Newer" = `version > FORMAT_VERSION`. Refusal messages follow the prior-art phrasing pattern with expected-vs-found values (B3). **No checksum in the header for v1** — corruption refusal comes from `json.loads` failure (wrapped with a clear message, B3) and from the backup module's checksums (R6); reserve the option to add an optional integrity field additively later. Rationale against header checksums now: hand-editable educator files are a feature, and the zip container (Phase 4/7) plus backup verify (R6) already cover integrity where it matters.

**Versioning policy (encode in tests):**
- Format version: refuse `>`, accept `<=` (prior-art semantics, B3/B4). Additive-field evolution only: new optional fields ignored by old readers; new readers fill old files from `.get()` defaults (B4, C4). Any *semantic* change to an existing field = version bump + migration note (no migration machinery exists in prior art; do not invent one in Phase 1).
- `detector_version`: **exact-match** refusal (accept only `== DETECTOR_VERSION`) — different from format version, because changed detection semantics make old specs unsolvable/unscorable, not merely incomplete (H9, PITFALLS.md:274-275). Both policies get explicit tests (see P4).

### R3. Atomic JSON file I/O (in `persistence.py`)

```python
def write_json_atomic(path, obj):
    # payload = json.dumps(obj, indent=2, sort_keys=True, allow_nan=False)  [A7, A8]
    # data = payload.encode('utf-8')
    # fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or '.', prefix='.aam_', suffix='.tmp')
    # write bytes; os.fsync(fd); os.close(fd); os.replace(tmp, path)        [A9]
    # on failure: best-effort os.remove(tmp); re-raise

def read_json_file(path):
    # open(path, 'rb') -> json.loads(bytes)   [A5; 'rb' avoids Windows CRLF translation]
    # json failure -> FormatError("could not parse AA-match JSON: %s")   [B3 phrasing]
```

Fixes three prior-art gaps at once: non-atomic direct write (B6, C2), Windows text-mode CRLF translation (binary `'wb'` → byte-stable files → stable checksums/diffs), and silent NaN/Infinity emission (A7). `sort_keys` + `indent=2` keeps files diff-able and checksum-stable (A8). *The Windows-atomicity nuance of `os.replace` is MEDIUM (A9, OQ5) — the pattern is still strictly safer than the prior art's direct write; the corruption-simulation test (R6) covers the WSL side where it is unit-testable.*

### R4. `setup_state.py` — complete field set (design the format NOW; GUI is Phase 4)

Per H4-H7, the complete serialized field set (header fields excluded — the container carries magic/version/kind, R2; do NOT duplicate a `format` field like prior art C1):

```python
INTERACTION_TYPES = ["h_bond", "salt_bridge", "pi_stacking", "cation_pi",
                     "hydrophobic", "halogen", "metal"]            # H6 (v1 decision)
INTERACTION_MODES = ["exclusive", "block_exclusive", "unset"]      # SETUP-06 wording (REQ:21)

MOLECULES_DEFAULT, MOLECULES_MIN, MOLECULES_CAP = 2, 1, 10         # FLAG OQ1 (spec "default 2-5")
DIFFICULTY_DEFAULT, DIFFICULTY_MIN, DIFFICULTY_CAP = 3, 1, 9       # FLAG OQ1 (spec "default 3-5")

DEFAULTS = {
    "source_mode": "demo",            # "demo" | "upload"                          (SPEC:14)
    "demo_set_id": "",                # manifest id; Phase 1 validates non-empty str only —
                                      #   manifest-membership check lands Phase 2/8 (additive)
    "upload": None,                   # None | {"path": str, "sha256": str}         (OQ3)
    "molecules_per_level": 2,         # int, clamp [MOLECULES_MIN, MOLECULES_CAP]
    "difficulty_levels": 3,           # int, clamp [DIFFICULTY_MIN, DIFFICULTY_CAP]
    "interaction_mode": "unset",      # "exclusive" | "block_exclusive" | "unset"   (FLAG OQ2)
    "allowed_interactions": [],       # members of INTERACTION_TYPES, deduped, stored in
                                      #   canonical INTERACTION_TYPES order; serialized ALWAYS
                                      #   (format stability even when mode != block_exclusive)
}
```

Functions (prior-art patterns, D3/D4):
- `validate_state(state)` → NEW dict, never mutates (D3): enums fallback to default on invalid; ints via try/int/except→default then clamp; `allowed_interactions` filtered to `INTERACTION_TYPES` + dedup + order-normalized (canonical order = `INTERACTION_TYPES` order, so equal sets serialize identically); `upload` shape-checked (`path`/`sha256` strings) else `None`.
- `randomize_state(seed=None)` → complete valid state, deterministic under seed (D4): random demo_set_id (Phase 1: any string; Phase 2 narrows to manifest), random molecules_per_level/difficulty_levels within clamp, random mode, random subset of interactions for block_exclusive.
- Derived data stays out: grid N per difficulty is a *generator* concern (Phase 2), derived from the difficulty tier — not a setup field (`SPEC:7` "NxN grid (depends on difficulty)"); the tier→N table lives with the generator and is stamped into each level spec (R5).
- Phase-1 scope = this data model + serialization; the GUI collect/apply equivalents (`PA-gui.py:539-617` pattern) are Phase 4.

### R5. `level_spec.py` — schema reserved now, filled by Phase 2+

Design goal (RQ3): Phases 2 (generator/detector), 3 (placement/reset replay), 7 (checkpoint reconstruction) extend without breaking. Per H8-H12:

```python
DETECTOR_VERSION = "det-1"        # EXACT-match gate (H9); bump when thresholds/typing change
LEVEL_SPEC_VERSION = 1            # additive evolution; format-version policy applies (R2)

# A level spec travels inside a container with kind='level_spec'. The 'data' payload:
{
  "detector_version": "det-1",    # EXACT match required on load, else refuse ("stale or newer
                                  #   game spec — regenerate", H9 / PITFALLS.md:280)
  "format_version": 1,            # additive-field policy (R2)
  "seed": <int>,                  # deterministic regeneration (H12)
  "levels": [
    {
      "level_index": 0,           # 0-based
      "difficulty": {             # GEN-05: difficulty = grid N + molecule size + type count
        "tier": 0,                # 0-based tier index (< difficulty_levels)
        "grid_n": 3,              # NxN grid for THIS level (SPEC:7)
        "n_required_types": 2,    # count of distinct required interaction types
        "molecule_size_class": "small"   # enum reserved; Phase 2/8 defines classes (additive)
      },
      "molecules": [              # a level = a SET of molecules (SPEC:7)
        {
          "molecule_id": "mol-001",
          "ligand": {
            "source": "demo",     # "demo" | "upload"
            "set_id": "demo-xxx", # demo manifest id (validated Phase 8)
            "entry_id": "",       # per-set entry id, reserved
            "file": "",           # package-relative path (never cwd, PITFALLS.md:58)
            "sha256": "",         # integrity of the referenced structure file
            "protonation": "",    # source-carried state tag (H13, SPEC:7,61)
            "provenance": ""      # database/provenance citation tag (Phase 8 fills; H13)
          },
          "required": {           # SCORE-01 fraction semantics; H5
            "mode": "any",        # "any" | "list"  ('any' <-> exclusive; 'list' <-> block_exclusive;
                                  #   'unset' is RESOLVED by the generator into a concrete per-molecule
                                  #   required set — the spec stores the RESOLVED requirement)
            "items": [{"type": "h_bond", "count": 1}]   # type + number required (SPEC:38)
          },
          "grid": {
            "n": 3,
            "slots": [
              {"slot_id": 0, "row": 0, "col": 0,
               "aa": "ALA",                            # amino-acid identity
               "role": "required",                     # "required" | "distractor" (GEN-04)
               "can_form": ["h_bond"],                 # interaction types THIS AA can form with THIS
                                                       #   ligand — AA-side capability (DETECT-04
                                                       #   partner sides, H10; powers hint + solvability)
               "grid_pose": {"position": [0.0, 0.0, 0.0]}   # minimal now; ADDITIVE keys (rotation
                                                       #   representation decided in Phase 3's
                                                       #   movement-model spike — PITFALL 6/12;
                                                       #   old readers ignore unknown pose keys)
              }
            ]
          }
        }
      ]
    }
  ]
}
```

API: `parse_level_spec_dict(d)` → validates container (via persistence's `check_container`, kind='level_spec') + `detector_version` exact-match + structural minimums (levels non-empty; grid n ≥ 1; slot ids unique per molecule — the invariant the generator must satisfy, PITFALLS.md:270-271). Normalizers are **passthrough**: unknown keys preserved, never stripped (P9), so Phase 3/7 extensions survive a Phase-2-era reader. Versioning policy documented in the module docstring.

### R6. `backup.py` — pure snapshot/restore/verify over an injected store

Keep the prior-art *contract* (E1: snapshot / restore / discard / verify_intact) but invert the coupling: the pure module owns policy, callers inject storage (injection precedent: ARCHITECTURE.md:136). This answers RQ4's "cmd coupling must stay OUT of the pure module":

```python
class BackupError(Exception): pass

# Store protocol (duck-typed; both implementations pure stdlib):
#   save_bytes(key, data: bytes); load_bytes(key) -> bytes; delete(key); exists(key) -> bool
class MemoryStore:  ...   # dict-backed (tests)
class FileStore:    ...   # root dir; save via temp file + os.replace (R3 pattern); idempotent delete

def snapshot(store, key, payload):      # payload = JSON-serializable dict
    data = _canonical(payload)          # json.dumps(sort_keys=True, allow_nan=False) UTF-8 [A7, A8]
    store.save_bytes(key, data)
    return {"key": key, "sha256": sha256(data), "timestamp": time.time()}   # manifest

def verify_intact(store, key, current_payload):
    # missing backup -> BackupError (caller ASSERTS the return/exception; E3 discipline)
    return _canonical(current_payload) == store.load_bytes(key)   # canonical-dict equality

def restore(store, key):                # returns payload dict
    data = store.load_bytes(key)        # missing -> BackupError
    if sha256(data) != stored_manifest_sha256: raise BackupError("backup corrupt")  # corruption gate
    return json.loads(data)

def discard(store, key): ...            # idempotent (E2)
```

- Verify semantics = canonical-dict equality + sha256 (A10) — the pure-layer analogue of prior art's multiset compare (E4). The cmd-tier adapter (Phase 2/3) will snapshot PyMOL objects via the proven `cmd.create('_aam_backup', …)` mechanics (E2/E3, PITFALLS.md:227-229) and feed atom-tuple payloads through the SAME verify contract — so "every destructive op routes through one backup module with the same contract" (PITFALLS.md:230) survives the layering.
- **Corruption-simulation recovery test** (PITFALLS.md:181, 508 — "corrupt-mutation simulation recovers"): FileStore → snapshot → flip a byte in the stored file on disk → `restore` raises `BackupError("backup corrupt")` and `verify_intact` returns False → documented recovery = regenerate from the seeded spec (H11; PITFALLS.md:486-488).
- Naming: the future cmd adapter's object prefix should be `_aam_backup` (AA-match namespace, mirroring E2's underscore-private convention; PITFALLS.md:328-329 reserved-prefix rule).

### R7. `paths.py` — port the proven guard, now pure and tested

Port `PA-demos.py:59-78` semantics verbatim (F1-F2); unit-test with this matrix (each a named test):

| Input | Expected | Why |
|-------|----------|-----|
| `/mnt/c/Users/x/lig.pdb` | `C:\Users\x\lig.pdb` | core conversion (F2) |
| `/mnt/d/data/x.mol2` | `D:\data\x.mol2` | any single-letter drive |
| `/mnt/C/Users/x` | `C:\Users\x` | drive letter uppercased |
| `/mnt/c/My Dir/a b.pdb` | `C:\My Dir\a b.pdb` | spaces preserved (spaces are safe through the Python-API string arg; runtime cmd.load-with-spaces smoke → OQ7) |
| `C:\Users\x` (backslashes) | unchanged | guard (F1) |
| `C:/Users/x` (forward slashes) | unchanged | guard |
| `\\srv\share\x` (UNC) | unchanged | parts[1] != 'mnt' |
| `data/x.pdb` (relative) | unchanged | guard |
| `/mnt/c` (no trailing) | unchanged | split yields 3 parts — document the asymmetry |
| `/mnt/c/` | `C:\` | 4th part empty |
| `/mnt/abc/x` | unchanged | multi-letter ≠ drive |
| `/mnt/wsl/x` | unchanged | 3-char 'wsl' ≠ single letter (real WSL mountpoint) |
| `/home/u/x`, `''` | unchanged | non-mount / empty |
| converted `C:\x` fed again | unchanged | idempotence |

Plus a second helper: `package_data_path(*parts)` resolving bundled data relative to `os.path.dirname(__file__)` — never `os.getcwd()` (PITFALLS.md:58) — with a test asserting the result is under the package dir.

### R8. Purity gates — enforce, don't aspire (RQ6)

Put the gates in `tests/test_purity.py`, run by the same `python3.6 -m unittest discover -s tests -v` invocation (A11, STACK.md:141):

1. **Gate A — AST import scan (primary):** for each declared pure module (`aamatch.setup_state`, `aamatch.level_spec`, `aamatch.persistence`, `aamatch.backup`, `aamatch.paths`), `ast.parse` the source and walk **every** `ast.Import`/`ast.ImportFrom` node — module level AND function bodies (prior-art purity rule: "no pymol import at module level OR inside any function body", B7). Assert: no root in `FORBIDDEN = {pymol, numpy, dataclasses, PyQt5, PySide2, tkinter, Pmw, pmg_tk}`; every absolute import is either in an explicit `ALLOWED_STDLIB` whitelist (the A2 list) or a pure-module name; relative imports resolve only to pure modules. **AST scanning is immune to the docstring false-positive trap that produced prior art's documented grep-gate false positive** (G3, PITFALLS.md:83) — a docstring saying "from PyQt5 import" is a string literal in the AST, not an Import node.
2. **Gate B — clean-subprocess import (the "zero stubs" proof):** for each pure module, spawn `[sys.executable, '-c', 'import aamatch.<mod>']` with cwd=repo-root and NO `sys.modules` stubbing in the parent; assert returncode 0. Catches what AST cannot: dynamic `__import__('pymol')` and transitive contamination through `aamatch/__init__.py`. This is the literal verification of success criterion 2's "stdlib-only imports (no pymol / Qt / numpy / dataclasses)" (H2).
3. **Gate C — grep recipe (documented, not a unittest):** keep the prior-art grep commands in AGENTS.md with the false-positive warning (G3); Grep-tool-plus-inspection stays a plan-check habit, not an automated gate.
4. **Gate D — 3.6 syntax:** `python3.6 -m py_compile aamatch/*.py` (A11; catches 3.7+ syntax).
5. **Design prerequisite to state in the plan:** `aamatch/__init__.py` must contain **zero module-level `pymol`/`pymol.Qt` imports** — lazy imports inside `__init_plugin__()`/handlers (PITFALLS.md:36). Without this, Gate B fails immediately and MagicMock stubs creep back (G1). This is a deliberate, research-endorsed deviation from the prior art's `__init__.py`.
6. **AGENTS.md hook:** Phase 1's plan should add the gate commands (py_compile + unittest discover + purity rationale + the lazy-`__init__` rule) to root `AGENTS.md` (or a new `aamatch/AGENTS.md`) so every later phase inherits them — this is how PITFALLS.md:502's "Import gate; 3.6 unit tests green with no stubs" becomes standing policy.

### R9. Round-trip test design (PERSIST-01, H2 criterion 1)

The criterion is "every field preserved, versioned header refuses newer/foreign formats with a clear message". Test set:

- **Exact round-trip:** build a state with EVERY field at a non-default value (including `allowed_interactions` with all 7 types, unicode strings, boundary ints at min/cap) → `validate_state` → `persistence.save_setup_file(tmp)` → `load_setup_file` → `assertEqual(loaded, original_validated)` — exact dict equality (A6 guarantees float exactness if any appear later; do NOT use assertAlmostEqual for round-trips — assert exact ==).
- **Refusals, message-asserted:** (a) random JSON file → FormatError mentioning "not an AA-match file"; (b) `{magic: AAM_MAGIC, version: 999}` → FormatError mentioning "unsupported … version" and "Please update"; (c) right magic, `kind: "level_spec"` loaded as setup → FormatError mentioning expected kind; (d) truncated/garbage bytes → "could not parse".
- **Older-version acceptance:** today `FORMAT_VERSION = 1`; write the test so that when it becomes 2, a v1 file still loads (inject a version-1 container through the parse path; assert `.get()` defaults fill new fields).
- **Field-completeness regression:** DEFAULTS key-set test (D2 pattern) so adding a field without updating validate/randomize/tests fails loudly.
- **Level-spec gates:** detector_version exact-match refusal (stale AND newer both refused); slot-id uniqueness; unknown-field passthrough (P9).
- **Atomicity:** `write_json_atomic` leaves no `.tmp` litter on success and the original file intact on a simulated write failure.
- **Backup corruption simulation:** as specified in R6.

---

## Pitfalls

### P1: Stubs creeping back through a greedy `__init__.py`
**What:** importing `aamatch.anything` executes `aamatch/__init__.py` first; if it imports `pymol.Qt` at module level (as prior art did, G1), every pure test needs a MagicMock stub and "stdlib-only imports" is violated in spirit even when the pure modules are clean.
**Avoid:** lazy imports inside `__init_plugin__`/handlers from day one (R8.5, PITFALLS.md:36); Gate B fails loudly the moment this regresses.

### P2: Grep-gate docstring false positives (the prior-art tripwire)
**What:** token greps fire on prose — prior art "hit a false positive on a docstring that said 'from PyQt5 import'" (G3, PITFALLS.md:83).
**Avoid:** the AST gate is the enforced mechanism (R8.1); greps stay documented-with-warning for human plan checks.

### P3: Non-atomic / non-deterministic file writes
**What:** prior art's `write_bcmz` and setup save wrote directly (B6, C2): a crash mid-write leaves a truncated file; text-mode writes get CRLF-mangled on Windows; default `allow_nan=True` can emit non-JSON `NaN` tokens (A7).
**Avoid:** R3's temp+`os.replace`+fsync, binary `'wb'`, `allow_nan=False`, `sort_keys=True`.

### P4: Confusing the two version gates
**What:** format `version` uses refuse-newer/accept-older (B3) but `detector_version` must refuse ANY mismatch — applying the format policy to the detector stamp would silently accept stale games (the exact scenario PITFALL 11 exists to prevent, H9).
**Avoid:** two distinct constants, two distinct refusal messages, a test for each policy (R2, R5, R9).

### P5: Setup files storing session-local / machine-local data without portability semantics
**What:** prior art stored a live PyMOL object name in setup files (C5); an AA-match upload path stored absolutely breaks on another machine or after a repo move (PITFALLS.md:417 "Saved games + repo moves").
**Avoid:** reserve `upload: {path, sha256}` now (R4/P5), record sha256 so Load can *warn* when the file is missing/moved; final semantics decided in Phase 4 (OQ3).

### P6: validate/normalize that mutates its input
**What:** aliasing bugs when callers keep the original dict (tests, GUI re-apply).
**Avoid:** `validate_state` returns a NEW dict from `deepcopy(DEFAULTS)` — the prior-art discipline (D3); assert non-mutation in tests.

### P7: Backup verify/restore misuse (double-verify trap)
**What:** prior art's `verify_intact` on an already-discarded backup raises `CmdException` (E3, PITFALLS.md:229) — orchestrators must assert return values, never re-derive.
**Avoid:** pure `BackupError` for missing/corrupt (R6); document "assert the return value, don't re-call" in the module docstring; the corruption test (R6) exercises the failure path deliberately.

### P8: Duplicating the format tag as a data field
**What:** prior art carried `format` both as a setup field (C1) and as sidecar magic (B1) — two places to drift.
**Avoid:** one container header (R2); the key-set test (R9) fails if anyone re-adds a `format` field.

### P9: Schemas that strip unknown fields
**What:** a strict re-serializer that drops unknown keys makes every future additive field destructive on re-save (Phase 3/7 extensions lost by a Phase-2-era writer).
**Avoid:** passthrough parsing — keep unknown keys in the parsed dict (R5); document "additive fields are preserved, not validated away".

### P10: Test-order coupling in the gates
**What:** Gate B spawns subprocesses per module — if a test imports `aamatch` with stubs BEFORE the purity test runs in the same process, the "clean" proof is undermined within that process (subprocesses stay clean regardless, but in-process assertions about `sys.modules` would lie).
**Avoid:** Gate B's proof lives in subprocess exit codes only; never assert `sys.modules` cleanliness in a process that has already imported the package.

---

## Open Questions / UNVERIFIED

1. **[Needs human/planner decision] Numeric defaults + caps** for `molecules_per_level` (spec: "default 2-5, reasonable cap" — SPEC:15) and `difficulty_levels` ("default 3-5" — SPEC:16). "Default 2-5" is ambiguous (a default *range*? a default *within* a range?). Proposed concrete constants in R4 (2/1/10 and 3/1/9) — planner should surface to the user or pick and record the reading.
2. **[Needs decision] Default `interaction_mode`:** proposed `"unset"` because SPEC:20 says "if not set, random" (unset is the natural no-touch state); alternative `"exclusive"`. SETUP-06's enum wording ("exclusive / block-exclusive / unset") is the canonical label set (REQ:21).
3. **[Phase 4 decision, fields reserved now] Upload-path portability semantics** — absolute path + sha256 + warn-on-missing (R4/P5) vs copy-into-file vs relative-to-setup-file. Reserved as `{"path", "sha256"}`; decide with the upload GUI.
4. **[UNVERIFIED, optional 1-line headless smoke] Does Windows PyMOL `cmd.load` accept forward-slash `C:/...` paths?** Not determinable from the Python source tree (C-side behavior); prior art always produced backslashes (F3), so this never mattered. Non-blocking: the helper outputs the proven backslash form; recording the answer in Phase 1's headless smoke (one extra `cmd.load` call) closes it cheaply and also feeds the parallel toolchain research.
5. **[MEDIUM] `os.replace` crash-atomicity nuance on Windows** (A9): POSIX rename atomicity is OS-standard; the Windows MoveFileEx mapping is API-knowledge, not repo-verifiable here. The pattern is adopted regardless (strictly better than prior art's direct write); WSL-side corruption tests are fully verifiable.
6. **[Phase 3 dependency, reserved additively] Final `grid_pose` shape** (rotation representation) waits on the movement-model decision (PITFALL 6/12 — matrix vs coordinates, PITFALLS.md:154-157, 298); Phase 1 ships position-only + the additive-key policy (R5).
7. **[LOW, recorded for the headless checklist] Runtime acceptance of space-containing paths by `cmd.load`** — conversion preserves spaces (R7) and the Python API passes strings through, but prior art never smoke-tested spaces; add one headless smoke line in Phase 1 (pairs with OQ4).
8. **[Planner choice] Whether a standalone level-spec file (vs the Phase-4 game container) is user-facing in Phase 1** — recommend Phase 1 tests exercise the container with `kind='level_spec'` and the schema module; whether users can save bare specs is a Phase 4 export question (H3).

---

## Recommended Reading for the Planner

**Prior art (the adapt-don't-vendor sources):**
1. `tmp/bioCHEMeleon/biochemeleon/persistence.py` — all 279 lines (container/refusal/archive patterns; B1-B9)
2. `tmp/bioCHEMeleon/biochemeleon/gui_setup.py:538-686` — collect/apply state round-trip + the save/load handlers AA-match must *improve on* (C1-C6)
3. `tmp/bioCHEMeleon/biochemeleon/setup_state.py:114-181, 231-413` — DEFAULTS/validate/randomize patterns (D1-D5)
4. `tmp/bioCHEMeleon/biochemeleon/backup.py` — all 85 lines (contract only; cmd-coupled by design, E1-E5)
5. `tmp/bioCHEMeleon/biochemeleon/demos.py:57-98` — `to_windows_path` port source (F1-F4)
6. `tmp/bioCHEMeleon/tests/test_persistence.py` (refusal + transient-leak + tempfile round-trip patterns) and `tests/test_setup_state.py:1-80` (stub pattern to AVOID + key-set test to keep)

**Planning docs:**
7. `.planning/ROADMAP.md:32-45` (Phase 1 detail), `:78-91` (Phase 4 reuse), `:123-135` (Phase 7 reuse)
8. `.planning/REQUIREMENTS.md` — PERSIST-01/02/03, SETUP-04/05/06, DETECT-01..05, SCORE-01/04/05/10
9. `.planning/research/PITFALLS.md` — Pitfalls 1, 2, 3, 9, 11 (+ Technical-Debt and Integration tables); phase mapping at PITFALLS.md:494-514
10. `.planning/research/ARCHITECTURE.md` — Pattern 1 (purity + injection, :128-138), Pattern 5 (sidecar, :183-193), project structure (:78-110), build order (:347-357)
11. `.planning/research/STACK.md` — persistence row (:28), pure-layer stdlib row (:71-72), test invocation (:140-150)

---
*Research for Phase 1 (pure-foundation scope): AA-match PyMOL 2.5.0 plugin game — setup_state / persistence / level_spec / backup / paths + Python 3.6.9 stdlib-only test gates.*
*Researched: 2026-09-05.*
