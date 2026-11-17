---
phase: 09-help-docs-release-audit
plan: 03
subsystem: docs
tags: [readme, docs, truthfulness, install, usage, pymol, plugin-manager]

# Dependency graph
requires:
  - phase: 01-bootstrap-pure-foundation
    provides: 01-RESEARCH-plugin-install.md (directory-install contract, U3 label caveat) + 01-09 human install verdict (plugin-path route)
  - phase: 09-help-docs-release-audit
    provides: 09-RESEARCH-docs-audit.md §2.1/§3 shipped-reality data pack + 09-01 banner verdict (b-drop deferred to 09-06)
provides:
  - README.md "## Install" corrected (picker points at __init__.py; neutral GUI entry label; plugin-path named as the verified route; double-install warning)
  - README.md "## Usage" filled with a 9-step end-to-end flow matching shipped code, including the MOL2 fail-closed and 50-record/session-only upload realities
affects: [09-06 (banner verdict + demo table; do not touch lines 1-4 here), 09-10 (README placeholder/`## Usage` non-empty checks), 09-11 (README read-through), 09-12 (claim→code audit)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Docs-under-truthfulness-contract: every README sentence mapped to a 09-RESEARCH-docs-audit.md §2.1/§3 row and re-verified in code where the executor had any doubt"
    - "Relative links root-anchored; unverified GUI label kept neutral rather than asserted"

key-files:
  created:
    - .planning/phases/09-help-docs-release-audit/09-03-SUMMARY.md
  modified:
    - README.md

key-decisions:
  - "Dropped the existing 'universal across Windows/Linux/macOS' Plugin-Manager claim — not covered by the research citations; the rewritten Install body asserts only the five verified facts"
  - "Kept README.md lines 1-4 byte-identical (09-01 Verdict B banner drop belongs to 09-06, not this plan)"
  - "Included the shipped Done=abandon-stop behavior in Usage step 7 (QUICK-004 row of §2.1) so the panel's visible Done button is described honestly"

patterns-established:
  - "README facts consumed table (research row → README line) lives in this SUMMARY as the traceability receipt"

# Metrics
duration: ~15 min
completed: 2026-11-18
---

# Phase 9 Plan 03: README Install Correction + Usage Fill Summary

**README's Install section now points the Plugin-Manager picker at the package `__init__.py`, keeps the GUI label neutral, names plugin-path as the human-verified route, and warns against double installs; Usage is a 9-step end-to-end flow transcribed from the shipped-reality data pack, with the MOL2 fail-closed reality and 50-record session-only upload cap stated plainly — the vibe-coding/under-development blockquote (lines 1-4) is byte-untouched.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-11-18 (session; exact epoch not recorded)
- **Completed:** 2026-11-18T04:54:57+08:00 (`8d8bfc1`)
- **Tasks:** 3/3
- **Files modified:** 1 (`README.md`)

## Accomplishments

- Corrected all three Install drifts from 09-RESEARCH-docs-audit.md §3 (rows 1-3): wrong install target, unverified button label, and the incomplete "Plugin Manager is THE method" framing.
- Filled `## Usage` (was `> TBD`) with a numbered flow covering launch → molecule choice → setup → Start/countdown → drag-model play → Confirm pass gate → game management → endgame → save/import/share.
- Stated the honest edge cases: single-segment MOL2 refused on this build (SDF is the working format), uploads capped at 50 records and session-only.
- Preserved the vibe-coding / `!! Under Development !!` blockquote byte-for-byte; 09-06 still owns the banner application.

## Facts consumed (research row → README line, post-edit)

### Install (README.md:24-37)

| README:line | Claim written | Source row |
|---|---|---|
| 26 | `Plugin → Plugin Manager`, then the install-new / install-from-local-file entry (neutral label) | §3 row 2; 01-RESEARCH-plugin-install.md:337 (U3: label lives in a runtime `.ui` form) |
| 27-28 | Point the picker at the package's `__init__.py` (`AA-match/aamatch/__init__.py`), not the directory | §3 row 1; 01-RESEARCH-plugin-install.md:17-19 (installation.py:299-308, legacysupport.py:60-66) |
| 29 | Registers a **AA-match** item under the Plugins menu | §1.3 item 5 / §2.1; `aamatch/__init__.py:26` (`addmenuitemqt('AA-match', run_plugin_gui)`) |
| 31-33 | Plugin-**path** is the human-verified route; dev edits are live | §3 row 3; `01-09-SUMMARY.md:17,26-27,38,40,120-122` |
| 35-37 | Never install both ways at once (two module objects break shared state) | §3 row 3; AGENTS.md gates 5-6; `01-09-SUMMARY.md:27,40,122` |

### Usage (README.md:41-91)

| README:line | Step / claim | Source row (09-RESEARCH-docs-audit.md §2.1 unless noted) |
|---|---|---|
| 41-42 | Launch from Plugins → AA-match; modeless 'AA-match Setup' with Setup + Game status tabs | Install & launch; `setup_window.py:148, 241-244` |
| 44-45 | Demo dropdown grouped by difficulty tier | `setup_window.py:325-361`; `setup_form.py:142-162` |
| 45-48 | One SDF/MOL2 file; multi-record gives several molecules; 50-record cap; uploads session-only; MOL2 refused on this build | upload rows; `game_file.py:87`; `setup_window.py:175-179`; `upload.py:47-53, 114-141`; §3 row 9 |
| 50-53 | Molecules per level 1-10 default 2; difficulty 1-10 default 3; three interaction modes; 7 interaction types | `setup_state.py:40-50`; `setup_window.py:418-454` |
| 55-57 | Start cleans prior game, generates levels, 3-2-1 countdown, ligand fixed + AA grid | Game flow; `game_window.py:325-331`; `gamestart.py:356-381, 396` (cleanup FIRST) |
| 59-63 | Click to select; shift+left-drag view plane; ctrl+shift+left-drag depth; shift+right-drag rotate | `wizard.py:328-337` (`dgmv`/`dgmz`/`dgrt`); `wizard_text.py:61` |
| 65-67 | Toward ligand = 2.5 Å; Game-status tab tracks time/required/log | `wizard_core.py:70`; `wizard_text.py:37-51`; `game_window.py:179-323` |
| 69-73 | Confirm passes only when ALL required interactions formed; failed Confirm records nothing; independent binary-per-item scoring; extras never inflate | `game_state.py:152-168` (`CONFIRM_PASS_RULE='all'`); `wizard.py:1058-1069`; `game_state.py:9-26`; `status_text.py:380-424` |
| 75-80 | Hint highlights AAs for still-formable required interactions; Skip keeps partial score; Skip + Give Up confirm; Reset keeps orientations; Restart replays stored initial state; Done = abandon-stop, no record/endgame | `game_window.py:233-293`; `engine.py:607-625`; QUICK-004 `status_text.py:309` + STATE.md lines 14-15 |
| 82-84 | Win screen or Give Up summary; per-level scores, total, time, skips | Endgame; `status_text.py:365-424`; `game_window.py:42-86` |
| 86-91 | Save `.aamz` (session + state, resumes exactly); Generate and export `.aamatch.json`; Save/Load Setup `.aam.setup.json`; Import dispatches on container header, not filename | Checkpoints/share; `checkpoint.py:19-24,91`; `game_window.py:1042-1047, 1104-1134`; `setup_window.py:738, 940-941`; `persistence.py:133-182` |

## Task Commits

The plan's Task 1 and Task 2 are two edits of the same file, committed together by the plan's Task 3 (the plan explicitly specifies ONE commit):

1. **Task 1+2+3: Install corrected + Usage filled** — `8d8bfc1` (docs)

**Plan metadata:** created by the close-out docs commit (SUMMARY + STATE).

## Files Created/Modified

- `README.md` — Install body rewritten (lines 24-37) and Usage filled (lines 39-91); all other lines byte-identical.
- `.planning/phases/09-help-docs-release-audit/09-03-SUMMARY.md` — this receipt.

## Decisions Made

- Dropped the unverified "(universal across Windows/Linux/macOS)" claim from the Install intro; the rewritten text asserts only the five researched facts.
- Usage includes the shipped Done behavior ("closes the board — no record and no endgame screen") because the Done button is visible in the panel; it is directly traceable to the §2.1 Done row (QUICK-004).
- Left the 09-01 Verdict B banner decision untouched: lines 1-4 remain byte-identical; 09-06 applies the verdict.

## Deviations from Plan

None — plan executed as written. (The only discretionary content change was replacing the unverified "universal across…" clause, which follows the plan's "rewrite the body with exactly these verified facts" instruction.)

## Issues Encountered

None. Standing gates re-run after the edit: `python3.6 -m py_compile aamatch/*.py` PYC-OK; `python3.6 -m unittest discover -s tests` 973/973 OK (27.1 s, incl. purity gates).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- README Install and Usage are ready for 09-10's mechanical checks (`## Usage` non-empty, no `TBD`) — remaining `TBD`s are only in `## Project Structure` and `## Acknowledgements` (09-06/09-09 scope).
- Lines 1-4 remain byte-identical, so 09-06 can apply the 09-01 banner verdict cleanly.
- No blockers.

---
*Phase: 09-help-docs-release-audit*
*Completed: 2026-11-18*
