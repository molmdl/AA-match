---
phase: 09-help-docs-release-audit
plan: 06
type: execute
subsystem: docs
tags: [readme, docs, manifest, demo-sets, licenses, attribution, release-banner]

# Dependency graph
requires:
  - phase: 09-help-docs-release-audit
    plan: 01
    provides: "Decision B verdict = b-drop (drop the '> !! Under Development !!' banner; lines 1-3 byte-verbatim)"
  - phase: 09-help-docs-release-audit
    plan: 03
    provides: "README Install/Usage already filled (banner left byte-untouched for 09-06)"
  - phase: 08
    provides: "aamatch/data/MANIFEST.json (10 sets / 18 entries) + docs/DATA_SOURCES.md + tests/test_demo_supply.py thin-set pins"
provides:
  - "README '## Demo Molecules set' table: 10 filled rows (9 curated + demo-dev-1), every cell manifest-verified"
  - "Honest thin-set refusal footnote (demo-easy-3 / demo-veryhard-2 / demo-veryhard-1)"
  - "Repo-root-relative docs/DATA_SOURCES.md attribution link (09-RESEARCH §3 item 4 drift fixed)"
  - "Filled '## Acknowledgements' with the real license census"
  - "09-01 Decision B applied: banner dropped, vibe-coding prose retained byte-exactly"
affects: [09-09 (README Project Structure — last TBD), 09-10 (tests/test_docs_audit.py machine checks), 09-12 (audit artifact), 09-14 (DOCS-02 sign-off)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Docs values are re-derived from the live MANIFEST at write time and machine-diffed against the written table (no prose trust)"
    - "Line-targeted, byte-preserving README edits: only the banner line removed; lines 1-3 md5-pinned pre/post"

key-files:
  created: []
  modified:
    - README.md

key-decisions:
  - "Decision B taken as b-drop ONLY (the b-retain sub-branch is DEAD per 09-01-SUMMARY Consumers table)"
  - "Demo-set table rows carry set_id in the Category column so 09-10's machine check can key rows"
  - "All three tasks committed as ONE content commit (explicit plan Task 3 instruction), not three per-task commits"

patterns-established:
  - "Live-manifest table verification: a py3.6 loop parses the written README rows and asserts tier/title/set_id/entry-ids/source/network against MANIFEST.json (10/10 green)"

# Metrics
duration: 12 min
completed: 2026-11-18
---

# Phase 9 Plan 06: README Demo-Set Table, Acknowledgements, Banner Verdict Summary

**README's demo-set table now lists all 10 bundled sets machine-verified against MANIFEST.json, with the honest three-set refusal footnote, a working docs/DATA_SOURCES.md link, real license attribution, and the "Under Development" banner dropped per 09-01 Decision B.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-11-18 (session; UTC 2026-11-17T21:0xZ)
- **Completed:** 2026-11-18 (UTC 2026-11-17T21:20:51Z)
- **Tasks:** 3/3
- **Files modified:** 1 (README.md)

## Accomplishments

- **09-01 Decision B applied byte-exactly (b-drop):** exactly one line deleted
  (`> !! Under Development !!`). `head -6 | cat -A` confirms line 1 still ends
  with its trailing space and lines 1-3 are md5-identical pre/post
  (`e5569ad53ea0ce1533254ac61c7713e8`); the vibe-coding warning (DOCS-01
  mandated) is retained verbatim.
- **Demo-set table filled (DOCS-01):** 10 rows = 9 curated sets + the
  demo-dev-1 development fixture, using the original
  `| Tier | Category | Source | ID(s) | Needs network? |` header. Every cell
  (tier, title, set_id, entry_ids, source/license, network) was re-derived
  from the **live** `aamatch/data/MANIFEST.json` and then machine-diffed
  against the written rows: **10/10 OK, 10 unique set_ids, coverage == manifest**.
- **Honest thin-set footnote** transcribed from `tests/test_demo_supply.py`
  pins: demo-easy-3 and demo-veryhard-2 (single-entry sets) and
  demo-veryhard-1 (its level-0 small pool holds only thyroxine) refuse at the
  default 2-small-molecules-per-level setting with a clear message.
- **Link drift fixed** (09-RESEARCH-docs-audit §3 item 4): the bare
  ``Full attribution in `DATA_SOURCES.md`.`` became a repo-root-relative
  `[docs/DATA_SOURCES.md](docs/DATA_SOURCES.md)` link (file exists, 40,569 B).
- **Acknowledgements filled:** NCBI PubChem (public domain) for 8 of the 10
  bundled sets, wwPDB Chemical Component Dictionary (CC0 1.0) for the heme
  set, per-file attribution in docs/DATA_SOURCES.md, dev fixture generated
  in-repo. `grep -c 'TBD' README.md` is now exactly **1** — only the `#TBD`
  Project-Structure block that 09-09 owns.

## Task Commits

The plan's Task 3 explicitly mandates **one** commit for the three tasks
(all touch the same file); that structure was followed exactly.

1. **Tasks 1+2+3: banner verdict + demo table + link fix + Acknowledgements** —
   `3f05b3c` (docs)

`git diff --stat` for the content commit: `README.md | 30 +++++++++++++++++-------------`
(17 insertions, 13 deletions) — **README.md only**.

## Files Created/Modified

- `README.md` — banner line 4 removed; 10-row manifest-verified demo table +
  3 explanatory paragraphs; `docs/DATA_SOURCES.md` link; Acknowledgements
  filled. Lines 1-3 byte-identical to pre-9 (md5-pinned).

## The 10 rows as written (live-manifest verified)

| Tier | Category | Source | ID(s) | Needs network? |
|------|----------|--------|-------|----------------|
| Easy | Everyday organics (demo-easy-1) | NCBI PubChem (public domain) | aspirin, benzoic_acid | No |
| Easy | Metabolites & ions (demo-easy-2) | NCBI PubChem (public domain) | citric_acid, acetate | No |
| Easy | Caffeine (demo-easy-3) | NCBI PubChem (public domain) | caffeine | No |
| Hard | Trypsin classics (demo-hard-1) | NCBI PubChem (public domain) | benzamidine, guanidinium | No |
| Hard | Charged messengers (demo-hard-2) | NCBI PubChem (public domain) | glutamic_acid, acetylcholine | No |
| Hard | Cofactors (demo-hard-3) | NCBI PubChem (public domain) | atp, nad | No |
| Challenge | Halogen & alkaloids (demo-challenge-1) | NCBI PubChem (public domain) | chloramphenicol, quinine | No |
| Very challenging | Big & iodinated (demo-veryhard-1) | NCBI PubChem (public domain) | folic_acid, thyroxine | No |
| Very challenging | Metalloporphyrin (demo-veryhard-2) | wwPDB CCD (CC0 1.0) | heme | No |
| Easy | Phase-2 development set (demo-dev-1) - development fixture, script-built in-repo (no download) | (none - generated in this repo) | benzamide, acetate | No |

**Live-manifest match confirmation:** the executor's mandated
`python3.6 -c "import json; ..."` re-read of MANIFEST.json produced exactly
the plan's data pack — 10 sets, tier census {easy 4 (incl. dev), hard 3,
challenge 1, very_challenging 2}, entry lists identical, set-level licenses
8 × `Public domain (NCBI PubChem)` + 1 × `CC0 1.0 (wwPDB)` (demo-veryhard-2)
+ dev `''` placeholder-by-design. **Zero discrepancies — no STOP-and-report
item arose.**

## Decisions Made

- **b-drop only.** Per 09-01-SUMMARY's Consumers table, the b-retain
  sub-branch is DEAD; nothing was retained or verified as "kept".
- **set_id in the Category column** (`Title (set_id)`) so 09-10's planned
  machine checks and any future audit can key table rows without a second
  lookup.
- **Single content commit** exactly as plan Task 3 specifies (all three tasks
  edit one file); per-task commit granularity is deliberately traded for the
  plan's explicit one-commit instruction.

## Deviations from Plan

None — plan executed exactly as written. (One structural note, not a
deviation: the plan itself directed ONE commit across Tasks 1-3 rather than
per-task commits, and that was honored.)

## Issues Encountered

None. README line numbers had shifted since planning (09-03 rewrote Install/
Usage), so the table/attribution/Acknowledgements anchors were located by
content rather than raw line numbers — as the execution context anticipated.

## Verification Receipts

- `python3.6 -m py_compile aamatch/*.py` → **PYC-OK**
- `python3.6 -m unittest discover -s tests` → **Ran 1006 tests, OK**
  (unchanged from the 09-05 baseline; README is docs-only)
- `grep -c 'TBD' README.md` → **1** (only `#TBD`, line 116, 09-09 scope)
- `grep -n 'docs/DATA_SOURCES.md' README.md` → 2 hits (paragraph + Acknowledgements)
- `sed -n '1,3p' README.md | md5sum` → `e5569ad53ea0ce1533254ac61c7713e8` (pre == post)
- Machine table diff: **ALL ROWS MATCH: True**, `covered==manifest: True`
- `git diff --stat HEAD~1` → `README.md | 30 ...` only

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- 09-10's planned machine checks are satisfied by this state: 10 set_ids
  present, `development fixture` present, `docs/DATA_SOURCES.md` linked,
  `TBD` count 1.
- README is one plan away (09-09, same-file sequential) from fully TBD-free.
- 09-07 (help wiring) is the other wave-2/3 remaining implementation plan.

---
*Phase: 09-help-docs-release-audit*
*Completed: 2026-11-18*
