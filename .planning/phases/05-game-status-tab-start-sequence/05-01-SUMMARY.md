---
phase: 05-game-status-tab-start-sequence
plan: 01
subsystem: ui
tags: [pymol, qt, game-status-tab, pure-text-builders, tdd, poll-diff]

# Dependency graph
requires:
  - phase: 03-wizard-interaction
    provides: aamatch/wizard_text.py (required_summary — the single items renderer, reused verbatim)
  - phase: 04-qt-setup-window
    provides: per-surface pure-module precedent (setup_form.py, 04-02) + 688-test WSL baseline
provides:
  - aamatch/status_text.py (PURE): required_display, level_molecule_line, selected_line, error_line, status_events, EVENT_KINDS
  - tests/test_status_text.py (37-test battery pinning every Phase-5 tab string + diff rule)
  - PURE_MODULES = 18 (status_text AST-gated)
affects: [05-02/05-03 game_window GameTab (consumes these builders), 05-07 get_status accessors, phase-06-scoring-lifecycle, phase-07-persistence]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "poll-diff pure event builders: status_events(prev, curr) diffs plain-data get_status() dicts over an exact fingerprint-key set; Qt tier stays a dumb renderer"
    - "per-surface pure text modules: wizard_text (wizard overlay) vs status_text (Qt tab) — one wording home per surface"

key-files:
  created: [aamatch/status_text.py, tests/test_status_text.py]
  modified: [tests/test_purity.py]

key-decisions:
  - "Required-display count = len(required['items']) in list mode / 1 in 'any' mode; difficulty.n_required_types is NEVER the display source (research Q4, pitfall 5)"
  - "First poll observation is SILENT (prev=None -> []): the start sequence owns the first level line (pitfall 4)"
  - "'result' is NOT fingerprinted in Phase 5 — score lines reserved for Phase 6 via EVENT_KINDS (pitfall 7)"
  - "Fail-closed refusals in required_display are delegated to required_summary — zero duplicated refusal wording (single-home law)"

patterns-established:
  - "Fingerprint-key diff: molecule_id, molecule_pos, molecule_total, level_pos, selected['slot_id'], error — everything else ignored via .get (extra-key tolerance); emission order level -> selection -> error; one level line per tick even when several fingerprint keys move"
  - "EVENT_KINDS vocabulary constant: key set pinned by tests, reserved-kind notes carry phase markers only (final wording is the owning phase's research)"

# Metrics
duration: ~5 min
completed: 2026-09-18
---

# Phase 5 Plan 01: status_text Pure Text Surface Summary

**All 32 Game-status-tab strings and every poll-diff rule pinned in a new PURE module (status_text) as a 37-test WSL battery before any Qt wiring exists — 725/725 green with PURE_MODULES = 18.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-09-18T18:27:58Z
- **Completed:** 2026-09-18T18:32:59Z
- **Tasks:** 3
- **Files created/modified:** 3

## Accomplishments
- `aamatch/status_text.py` — 180-line PURE module (zero stdlib, sole import `from .wizard_text import required_summary`): the six-piece surface (required_display, status_events, level_molecule_line, selected_line, error_line, EVENT_KINDS) the Game status tab renders from.
- `tests/test_status_text.py` — 37-test RED-first battery pinning every wording string (both required-display modes, singular/plural count edge, the level/molecule/selection/error lines) and every diff rule (first-observation silence, one-line-per-tick, sticky-error dedupe, deselect/re-click/cleared-error silence, result-not-fingerprinted, extra-key tolerance).
- `EVENT_KINDS` documents the full Phase-5/6/7 event vocabulary (15 kinds: 7 emitted + 8 reserved) so later phases append without redesigning the format.
- PURE_MODULES 17 → 18; status_text now AST-gated in every scope. Full WSL suite 725/725 green (688 baseline + 37 new), py_compile floor clean.

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): the status_text battery** — `4d5d267` (test)
2. **Task 2 (GREEN): implement status_text.py** — `64babae` (feat)
3. **Task 3: register in PURE_MODULES** — `edd3f60` (test)

**Plan metadata:** see the `docs(05-01): complete status_text pure battery plan` commit on this branch.

_Note: TDD pattern — RED test commit → GREEN feat commit → PURE_MODULES registration test commit (the 02-02 protocol)._

## Files Created/Modified
- `aamatch/status_text.py` — PURE tab-side text builders: required_display (delegates items rendering to wizard_text.required_summary; count = len(items), never difficulty.n_required_types), level_molecule_line (fail-closed missing-key refusals), selected_line (None on deselect → silent), error_line, status_events (poll-diff over the exact fingerprint-key set, emission order level→selection→error), EVENT_KINDS (15-kind vocabulary).
- `tests/test_status_text.py` — the 37-test battery with registration-pin header (02-02 pattern).
- `tests/test_purity.py` — PURE_MODULES += 'status_text' with phase-comment line (established comment-block style); no ALLOWED_STDLIB change.

## Decisions Made
- All per the plan's pinned behavior — none beyond it:
  - Required-display count: len(items) list / 1 any (research Q4, pitfall 5 — difficulty.n_required_types stays generation metadata).
  - Diff fingerprint keys exactly: molecule_id, molecule_pos, molecule_total, level_pos, selected['slot_id'], error; 'result' deliberately excluded (Phase-6 reserve, pitfall 7).
  - First observation silent (pitfall 4); sticky error never re-logged, cleared error silent (pitfall 3); deselect is silent (only the pinned slot-selection string exists; the panel reflects deselects).
  - required_display unknown-mode/empty-list refusals delegated to required_summary wording (the delegation supplies the fail-closed wording — single-home law; zero duplicated refusal strings).

## Deviations from Plan

None — plan executed exactly as written. (The plan's verification grep for 'pymol'/'PyQt'/'numpy'/'import os' in status_text.py finds only the docstring's "NO pymol/Qt/numpy" purity declaration — the documented Gate-C prose case; the enforced AST gate in tests/test_purity.py reports zero findings on the module, and no real imports exist beyond the pinned `from .wizard_text import required_summary`.)

## Issues Encountered

None. RED failed for the right reason (ImportError: cannot import name 'status_text'); GREEN went 37/37 on the first implementation pass; the full suite stayed green after registration.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness
- The tab-side consumers (05-02/05-03 game_window.py GameTab) can now write their Qt glue as dumb renderers: `_log(status_text.status_events(prev, curr))` lines + `status_text.required_display(state['required'])` label updates — every string already regression-toothed.
- Phase 6/7 inherit the reserved EVENT_KINDS vocabulary (molecule_scored, molecule_skipped, gave_up, level_advanced, game_reset, game_restarted, game_saved, game_imported) with wording to be pinned by their own research.
- No blockers. No smoke was in scope for this plan (WSL-only pure battery).

---
*Phase: 05-game-status-tab-start-sequence*
*Completed: 2026-09-18*
