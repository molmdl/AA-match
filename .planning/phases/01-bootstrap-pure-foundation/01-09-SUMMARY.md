---
phase: 01-bootstrap-pure-foundation
plan: 09
subsystem: plugin-install
tags: [pymol, plugin-manager, plugin-path, install, human-checkpoint, setup-defaults, module-identity, gui-menu]

# Dependency graph
requires:
  - phase: 01-bootstrap-pure-foundation (01-01)
    provides: "repo-root aamatch/ plugin skeleton (metadata-first __init__.py, __init_plugin__ registering the AA-match menu item, Qt-free placeholder) — the subject this checkpoint installs and verifies"
  - phase: 01-bootstrap-pure-foundation (01-05)
    provides: "the adopted setup defaults (molecules_per_level / difficulty_levels / interaction_mode) whose human confirmation this checkpoint records"
  - phase: 01-bootstrap-pure-foundation (01-07)
    provides: "headless SMOKE-01 PASS proving the package loads clean under real Windows PyMOL — the GUI-only legs (menu + click) are what remained for a human"
provides:
  - "INSTALL-01 human verdict RECORDED: Plugins menu shows AA-match (Y), click feedback prints the placeholder (Y), console clean apart from pre-existing unrelated plugin warnings (Y); placeholder verbatim: 'AA-match 0.1.0: plugin skeleton OK — game UI arrives in Phase 4.'"
  - "Install method decision: PLUGIN-PATH (repo root C:\\Users\\nglok\\Desktop\\WORKDIR\\molmdl\\AA-match added to PyMOL's plugin path), not the Plugin-Manager dialog copy install — repo edits are live with zero reinstall, the better dev loop"
  - "Setup defaults HUMAN-APPROVED and FROZEN as schema constants for Phases 2+ (changes = version-bump event): molecules_per_level 2/min 1/cap 10, difficulty_levels 3/min 1/cap 10 (amended from 9), interaction_mode 'unset'"
  - "Code amendment applied: DIFFICULTY_CAP 9 -> 10 in aamatch/setup_state.py with literal boundary tests (10 accepted, 11 clamps to 10) — full suite green"
affects: [phase-2-headless-engine, phase-4-game-ui, phase-8-demos, setup-schema-consumers]

# Tech tracking
tech-stack:
  added: []   # no new libraries; plugin-path install uses PyMOL's built-in plugin-path mechanism
  patterns:
    - "Plugin-path dev install: repo root on PyMOL's plugin path loads aamatch live from the repo — no copy install, no reinstall step, one module object"
    - "Module-identity discipline: exactly ONE module object under plugin-path loading; NEVER additionally copy-install the same plugin (two module objects -> duplicate singletons later)"
    - "Human-verdict-as-artifact: GUI-only claims (menu presence, click feedback) are recorded verbatim in the plan SUMMARY, not asserted headless"

key-files:
  created:
    - .planning/phases/01-bootstrap-pure-foundation/01-09-SUMMARY.md
  modified:
    - aamatch/setup_state.py
    - tests/test_setup_state.py

key-decisions:
  - "Install via PLUGIN-PATH (human added repo root to PyMOL's plugin path), NOT the Plugin-Manager dialog copy install — dev-efficient: repo edits live, no reinstall; orchestrator-verified from GUI console output"
  - "difficulty_levels cap amended 9 -> 10 by the human at the checkpoint; all other defaults approved as-is and now FROZEN as schema constants for Phases 2+ (changes = version-bump event)"
  - "Plugin-path module identity: one module object loads, so no duplicate-singleton risk — but the human must NOT ALSO copy-install the plugin (that WOULD create two module objects)"
  - "Step-7 clarification recorded: no popup exists in Phase 1 (Qt-free skeleton); the confirmation was the human's explicit reply, which IS the verdict"

patterns-established:
  - "Dev-loop install contract for all later phases: plugin-path loading from the repo copy (per AGENTS.md gate 6) is the PROVEN method; Plugin-Manager installs remain human-checkpoint-only"
  - "Keep aamatch/ pycache-free after every WSL test run (the human loads the plugin live from this repo)"

# Metrics
duration: 6 min (continuation session; checkpoint plan spanned multiple sessions)
completed: 2026-09-06
---

# Phase 1 Plan 9: [HUMAN] Install Checkpoint Summary

**INSTALL-01 human-verified via plugin-path install (menu + click + clean console, placeholder verbatim), setup defaults approved with ONE amendment — difficulty_levels cap 9 -> 10 applied and tested — defaults now frozen as schema constants for Phases 2+**

## Performance

- **Duration:** 2 min (continuation session applying the resolved checkpoint verdict; the human-install checkpoint itself spanned prior sessions)
- **Started:** 2026-09-05T18:15:35Z
- **Completed:** 2026-09-05T18:17:33Z (local 2026-09-06)
- **Tasks:** 2 (Task A: cap amendment; Task B: this summary)
- **Files modified:** 3 (2 code/test + 1 planning doc)

## Human Verdict (INSTALL-01) — RECORDED

| Check | Result |
| ----- | ------ |
| Plugins menu shows **AA-match** after restart | **Y** |
| Click AA-match → console prints placeholder | **Y** |
| Console clean (only pre-existing unrelated plugin warnings) | **Y** |

Placeholder line, verbatim:

```
AA-match 0.1.0: plugin skeleton OK — game UI arrives in Phase 4.
```

## Install Method — PLUGIN-PATH (not the dialog copy install)

The human installed by **adding the repo root `C:\Users\nglok\Desktop\WORKDIR\molmdl\AA-match` to PyMOL's plugin path** (their words: "not only the specific file, i just add the repo root to plugin path") — NOT by the Plugin-Manager "Install from local file" dialog copy install the plan's steps 2–5 described.

- **Why this is better for dev:** repo edits are live in PyMOL with zero reinstall — matches the AGENTS.md dev-loop gate (headless smokes already run against the repo copy; now the GUI session does too).
- **Module-identity note:** with plugin-path loading there is exactly **ONE** module object (no copy in `%APPDATA%\pymol\startup`), so no duplicate-singleton risk. **The human must NOT additionally copy-install the plugin** — that WOULD create two module objects → duplicate singletons later.
- **Consequence for the repo:** `aamatch/__pycache__` must be cleaned after WSL test runs (done after this plan's suite runs) so nothing stale loads live from the repo.

## Defaults Decision — APPROVED WITH ONE AMENDMENT (now ADOPTED + FROZEN)

Verbatim checkpoint question answers, adopted:

| Field | Approved value | Status |
| ----- | -------------- | ------ |
| `molecules_per_level` | default **2**, min **1**, cap **10** | approved as-is |
| `difficulty_levels` | default **3**, min **1**, cap **10** | **AMENDED from cap 9** (human: "cap 10 levels") |
| `interaction_mode` (no user choice) | **"unset"** → generator picks a random required set | approved as-is |

These are now **FROZEN as schema constants for Phases 2+; changing them later is a version-bump event.** The amendment was applied in code in this plan:

- `aamatch/setup_state.py`: `DIFFICULTY_CAP = 10` (was 9); default 3 and min 1 untouched; `molecules_per_level` / `interaction_mode` untouched.
- `tests/test_setup_state.py`: constants pin updated to `(3, 1, 10)`; added literal boundary pins — **10 accepted, 11 clamps to 10** — proving the boundary independent of the constant. Full suite green (114 tests).

## Step-7 Clarification

The human reported "i dont get step 7, nothing popup after seeing the line in step 6." **No popup exists in Phase 1** — the skeleton is deliberately Qt-free (the game UI arrives in Phase 4); the only click feedback IS the console placeholder line. The confirmation of the defaults was therefore the human's explicit reply in the checkpoint ("cap 10 levels ... approve others for 7"), which is the verdict recorded above.

## Task Commits

Each task was committed atomically:

1. **Task A: Apply the human-amended difficulty_levels cap (9 → 10)** - `aef7c5e` (fix)
2. **Task B: Write 01-09-SUMMARY.md recording the human verdict** - this docs commit

## Files Created/Modified

- `aamatch/setup_state.py` - `DIFFICULTY_CAP` 9 → 10 (human-amended default now a frozen schema constant)
- `tests/test_setup_state.py` - cap pin `(3, 1, 10)`, literal boundary cases 10/11, CAP comment updated
- `.planning/phases/01-bootstrap-pure-foundation/01-09-SUMMARY.md` - this record

## Decisions Made

- Plugin-path install adopted as the standing dev-loop install method (rationale above); Plugin-Manager dialog installs remain for human checkpoints only.
- `difficulty_levels` cap amended 9 → 10 by the human; all other defaults approved as-is; defaults frozen as schema constants for Phases 2+ (version-bump event to change).
- No duplicate module objects: plugin-path only; never also copy-install.

## Deviations from Plan

### Checkpoint-Outcome Change (human-directed, orchestrator-verified)

**1. Install method: plugin-path instead of Plugin-Manager dialog directory install**

- **Found during:** checkpoint resolution (human reply to the 01-09 checkpoint)
- **Issue:** the plan's how-to-verify steps 2–5 described the Plugin-Manager "Install from local file" dialog copy install; the human instead added the repo root to PyMOL's plugin path (their explicit choice: "more efficient for dev")
- **Resolution:** verdict accepted — the INSTALL-01 evidence (menu present, click prints placeholder, console clean) was captured from the human's GUI session with the plugin-path load; the dialog-install branch was never exercised and is NOT proven (documented here for honesty)
- **Files modified:** none (decision only; code amendment tracked as the plan's Task A)
- **Committed in:** `aef7c5e` (cap amendment) + this docs commit

---

**Total deviations:** 1 (human-directed install-method change; 0 auto-fixed code issues)
**Impact on plan:** INSTALL-01's intent (GUI menu wiring + placeholder proven by a human) is fully satisfied; the dev loop is strictly better (live repo loading). The unexercised Plugin-Manager dialog path is recorded as not-proven, not as failed.

## Issues Encountered

- None beyond the install-method change above (the "step 7 nothing popup" confusion was a plan-wording gap, clarified in the Step-7 Clarification section).

## User Setup Required

None - no external service configuration required. (Standing user practice: load AA-match via the plugin path from the repo root; do NOT also copy-install.)

## Next Phase Readiness

- **Phase 1 is complete: 9/9 plans done.** All four Phase-1 success criteria now have proof: pure modules + suite (01-01..01-06), headless load (01-07), purity gates (01-08), GUI install + defaults (01-09).
- Setup defaults are frozen schema constants — Phase 2 (setup persistence/level spec) and Phase 4 (game UI) can build against `molecules_per_level 2/min 1/cap 10`, `difficulty_levels 3/min 1/cap 10`, `interaction_mode 'unset'` without re-litigating.
- Watch item carried forward: keep `aamatch/` pycache-free (live plugin-path loading) and keep module identity single (never also copy-install).

---
*Phase: 01-bootstrap-pure-foundation*
*Completed: 2026-09-06*
