---
phase: 07-checkpoint-game-file-persistence
plan: 07
subsystem: ui
tags: [pymol, qt, game-tab, import, game-file, payload-direct, restart, persistence]

# Dependency graph
requires:
  - phase: 04-qt-setup-window (04-03 game_file pure container, 04-12 export chain)
    provides: parse_game_data five-gate consumer contract + the EXACT export filter
  - phase: 05-game-status-tab-start-sequence (05-05/05-09)
    provides: deferred-start orchestration (P-2 cancel, P-3 pop, countdown, _last_start)
  - phase: 06-scoring-lifecycle-endgame (06-08)
    provides: _restart_now replay law, D7 line-placement law, _X_impl factoring
  - phase: 07-05 payload-direct seam
    provides: gamestart.start_game_from_payload + engine.adopt_game + 5-key _last_start
  - phase: 07-03 status surface
    provides: status_text.game_imported_line (handler-logged)
provides:
  - Game-tab Import button (PERSIST-02): btn_import + gate-free _on_import + refusal-first
    _import_game_from(path) -- parse gates BEFORE any scene touch, then P-2 cancel -> P-3
    pop -> start_game_from_payload -> countdown -> 'Game imported: <path>.' after the arm
  - Restart payload-direct replay branch (the c2 decision): _restart_now prefers
    start_game_from_payload whenever _last_start carries 'payload'
  - SMOKE-19: import E2E + branch-taken identity proof + the eight-class refusal battery
affects: [07-10 checkpoint kind-dispatch (the Import filter grows .aamz + dispatch), 07-09
  resume (start_game_from_payload is NOT the resume seam -- adopt_game w/ sidecar state),
  07-12 human checkpoint (Import dialog feel)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Refusal-first import impl: read_json_file + parse_game_data BEFORE any scene touch
      -- every refusal leaves the session byte-untouched"
    - "Branch-taken smoke proof by OBJECT IDENTITY: payload-direct replay keeps
      engine._payload identical; a legacy regeneration would mint a new object"

key-files:
  created: [smoke/smoke_19_import.py]
  modified: [aamatch/game_window.py]

key-decisions:
  - "Import filter = the EXACT 04-12 export filter (game-files-only; .aamz + kind dispatch
    land in 07-10 -- no dead branch now)"
  - "NO confirmation warning mid-game Import (house law: spec warnings exist ONLY for
    Skip/Give Up; Import discards the running game exactly like Start)"
  - "Restart routes payload-direct on 'payload' in _last_start; legacy start_game call kept
    as the defensive fallback for a payload-less direct-construction tuple"

patterns-established:
  - "Gate-free wrapper law: handlers that CREATE a game (Import) carry NO upfront
    isinstance gate -- the dialog is always reachable; refusals surface verbatim via _guard"

# Metrics
duration: 24 min
completed: 2026-09-21
---

# Phase 7 Plan 07: Game-tab Import button + Restart payload-direct routing Summary

**Wired spec.md:39 Import for game files: refusal-first parse-before-scene-touch, the 07-05
payload-direct seam (embedded payload = truth, fresh GameState, timer from zero at GO),
gate-free wrapper with the exact export filter, D7 'Game imported: <path>.' after the arm —
plus the c2-recommended restart payload branch, closing the uploaded-game manifest-fallback
hazard; SMOKE-19 39/39 PASS first run.**

## Performance

- **Duration:** 24 min
- **Started:** 2026-09-21T20:28:14Z
- **Completed:** 2026-09-21T20:52:04Z
- **Tasks:** 3
- **Files modified:** 1 (game_window.py) + 1 created (smoke_19_import.py)

## Accomplishments

- **Import button (PERSIST-02, spec.md:39)** — `btn_import` (bare name per the D7 logic
  that left `btn_restart` bare) inserted before the stretch after Save (stretch stays LAST;
  row Hint/Confirm/Skip-GiveUp/Restart/Reset/Save/Import). `_on_import` is a GATE-FREE
  thin wrapper: NO upfront isinstance gate (Import is legal with NO game live — it CREATES
  one), NO mid-game confirmation warning (house law: spec warnings exist ONLY for
  Skip/Give Up), the EXACT 04-12 export filter, silent cancel, NO success box (the
  countdown + armed wizard + after-arm line ARE the feedback), refusals verbatim through
  `_guard`.
- **Refusal-first import impl** — `_import_game_from(path)`: the 04-12-proven five-gate
  consumer chain runs BEFORE any scene touch (a foreign/corrupt file leaves scene, log,
  stack, countdown, and the running game EXACTLY untouched), then P-2
  `cancel_pending_start()` → P-3 `_pop_game_wizard()` → the 07-05
  `gamestart.start_game_from_payload(...)` seam (embedded payload materialized DIRECTLY,
  never regenerated; fresh GameState zeros; timer from zero at GO via the existing
  `_begin_play`) → `start_countdown` → `status_text.game_imported_line` logged AFTER the
  arm (the restart D7 law).
- **Restart payload-direct branch (the c2 decision)** — `_restart_now` branches on
  `'payload' in gamestart._last_start`: present → `start_game_from_payload(...)` replays
  the EMBEDDED payload directly, closing the hazard where the legacy `start_game(...)
  candidates=None` path silently fell back to the bundled manifest for imported uploaded
  games; the legacy call kept as the DEFENSIVE fallback for payload-less direct
  constructions. Refusal-FIRST ordering + D7 line placement byte-unchanged.
- **SMOKE-19 (39 checks, 0 failed, PASS first run)** — PART A: real game-file fixture
  built end-to-end through `engine._payload` + `make_game_data` + `save_container` plus
  the eight refusal fixtures. PART B: construction pins + gate-free import with NO wizard
  live + GO-from-zero + mid-game replacement over a marker-stamped generation. PART C: the
  restart payload branch TAKEN, proven by OBJECT IDENTITY (`engine._payload is` the
  pre-restart object — a legacy replay would have regenerated a new one) + names/ids
  fingerprint EQUAL. PART D: all eight refusal classes raise with their EXACT house
  messages (unparseable-JSON asserts the prefix, the detail text being
  implementation-versioned), each leaving the session byte-untouched.

## Task Commits

Each task was committed atomically:

1. **Task 1: btn_import + _on_import wrapper + _import_game_from impl** - `d43437d` (feat)
2. **Task 2: _restart_now payload branch** - `005cac5` (feat)
3. **Task 3: SMOKE-19 — import E2E + restart branch + refusal battery** - `880575f` (test)

## Files Created/Modified

- `aamatch/game_window.py` — module + class docstrings (07-07 import law + the c2 restart
  route); btn_import block + connect; the Import handler section (`_on_import` gate-free
  wrapper, `_import_game_from` refusal-first impl); `_restart_now` payload/fallback branch
  with docstring rationale.
- `smoke/smoke_19_import.py` — NEW (634 lines): T1b headless proof, 39 checks across
  PARTs A/B/C/D, count-asserted, restore per the SMOKE-08/16 hygiene shape.

## Decisions Made

(None beyond the plan's three RECORDED DECISIONS, all implemented as written: exact export
filter with `.aamz` deferred to 07-10; no mid-game import warning; the c2 restart branch
with a defensive legacy fallback.)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug in plan-literal call chain] Container read via `read_json_file`, not `load_container`**

- **Found during:** Task 1 (impl authoring)
- **Issue:** The plan's Task-1 action text (and the research's I3 pseudocode) states
  `parse_game_data(persistence.load_container(path, 'game'))` — but
  `persistence.load_container` returns the container's `data` payload, stripping the
  magic header, while `parse_game_data` takes the FULL container (its gate 1 IS
  `check_container`). Followed literally, every valid import would refuse with
  `not an AA-match file (magic=None, expected 'AAMATCH')`.
- **Fix:** `persistence.read_json_file(paths.to_windows_path(path))` →
  `game_file.parse_game_data(container)` — the exact 04-12 consumer-contract shape proven
  in SMOKE-11 PART F and replayed by 07-02's checkpoint module (`make_container` re-wrap
  for in-memory game blocks). ALL five gate classes still run (JSON-parse refusal inside
  the reader; foreign/newer/misfiled/game-version/detector/ligand gates inside
  parse_game_data). Documented in the impl docstring.
- **Files modified:** aamatch/game_window.py (impl + docstring note)
- **Verification:** SMOKE-19 PART B/D green — valid import succeeds; the eight refusal
  classes each raise their exact messages.
- **Committed in:** d43437d (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 plan-text/API mismatch bug)
**Impact on plan:** Required for correctness of the plan's own intent; zero behavior
change vs the planned consumer contract. No scope creep.

## Issues Encountered

None — SMOKE-19 passed on the first headless run; SMOKE-16 FULL (77/77 incl. the 07-06
save part) and SMOKE-11 regressions green on the first re-runs; 881/881 WSL green
throughout.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **07-10 (checkpoint kind-dispatch):** the Import filter currently pins game files ONLY
  by design. The dispatch must NOT touch `_import_game_from`'s parse-first ordering — the
  `.aamz` branch gets its own refusal-first impl; the refusal battery in SMOKE-19 PART D
  is the regression anchor for the game-file branch. Note a NEW refusal class lands with
  it: a misfiled `.aamz`-named game file vs a `.aamatch.json`-named checkpoint (extension
  is advisory; `check_container` kind gates decide).
- **07-09/07-06 consumers:** Restart-after-checkpoint-restore inherits the c2 payload
  branch for free (the sidecar `last_start` restores `_last_start` with a payload entry
  per the 07-04 schema). The resume seam must continue to use `materialize` +
  `adopt_game` with the sidecar GameState — NOT `start_game_from_payload` (it mints a
  FRESH GameState; 07-05 law).
- **07-12 human checkpoint:** [HUMAN] set: Import dialog (filter, cancel), refusing the
  eight classes through the `_guard` box, mid-game import feel, restart-after-import of an
  UPLOADED game on a machine without the uploader's bytes (the hazard the c2 branch
  closes).

---
*Phase: 07-checkpoint-game-file-persistence*
*Completed: 2026-09-21*
