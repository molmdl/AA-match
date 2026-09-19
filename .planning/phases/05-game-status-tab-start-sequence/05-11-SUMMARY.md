---
phase: 05-game-status-tab-start-sequence
plan: 11
type: execute-checkpoint-record
subsystem: human-checkpoint
tags: [pymol, qt, game-status-tab, start-sequence, hint, human-checkpoint, verdicts, fix-batch]

# Dependency graph
requires:
  - phase: 05-game-status-tab-start-sequence
    provides: plans 05-01..05-10 (tab shell, start seam, countdown, timer + modal-freeze, live status surface, hint, window-driven start wiring, status poll-diff — all headlessly proven via SMOKE-08/11/13/14 + WSL batteries)
provides:
  - ROADMAP Phase-5 criterion 1 (SETUP-11 start sequence) [HUMAN] verdict recorded: PASS
  - ROADMAP Phase-5 criterion 2 (SCORE-04 status surface) [HUMAN] verdict recorded: PASS (step 7 = EXPECTED two-surface vocabulary, resolved and documented)
  - ROADMAP Phase-5 criterion 3 (PLAY-05 hint) [HUMAN] verdict recorded: PASS
  - Fix-batch item 1 (block-exclusive refusal message clarity) applied as commit b749135 and re-green (753/753 WSL + SMOKE-08/-11/-14)
affects: [phase verifier, phase-6 (this plan's restart-feel verdict feeds it), phase-8 demo curation (block-exclusive needs a diverse eligible pool)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Checkpoint fix-batch pattern (fourth instance; 03-06/03-07/04-15 precedents): human FAIL on message clarity -> fix applied as its own fix() commit -> full WSL suite + affected smokes re-green -> visual re-confirm rides any later GUI session"
    - "Fail-closed generator refusals explain the mode's SEMANTICS, not just the local predicate: a refusal raised from a per-molecule check inside a every-molecule-mode must say so, name the offending type(s), and give an actionable remedy"

key-files:
  created:
    - ".planning/phases/05-game-status-tab-start-sequence/05-11-SUMMARY.md"
  modified:
    - "aamatch/generator.py"

key-decisions:
  - "05-11 checkpoint APPROVED (human, 2026-09-20) with 1 fix-batch item (block-exclusive unsupported-type refusal message), resolved in-session (commit b749135)"
  - "Step-7 resolution (documented, no defect): the wizard panel prints the 03-02-pinned vocabulary ('Required: any interaction' / 'Required: h_bond x1') while the Qt Game-status label prints the 05-01 vocabulary ('Required: any 1 interaction' / 'Required: N interaction(s): ...') — two surfaces, two pinned vocabularies, both working as designed"
  - "Block-exclusive dev-set refusal behavior recorded as the solvability-by-construction contract working fail-closed (benzamide+acetate = every level, m=2 defaults, non-universal checked sets must refuse); the designed cure is Phase-8 curated diverse demos"

patterns-established:
  - "Two-surface vocabulary discipline: when two UI surfaces display related requirement text with DIFFERENT pinned phrasings, record both exact strings side-by-side in the checkpoint SUMMARY so later phases never re-flag the divergence as a defect"

# Metrics
duration: ~20 min (fix + re-green + documentation; the human checkpoint session itself ran outside agent execution)
completed: 2026-09-20
---

# Phase 5 Plan 11: Consolidated GUI Checkpoint — Start Sequence + Status Surface + Hint Summary

**05-11 checkpoint APPROVED (human, 2026-09-20) with 1 fix-batch item: all 9 verification steps PASS on a real Windows PyMOL 2.5.0 session — SETUP-11 start sequence (countdown cadence, P-2 cancel paths, restart feel), SCORE-04 status surface (info box, M:SS timer with modal-freeze, both required-mode label forms), PLAY-05 hint (carbon-only orange recolor, legible, full restores). Step 7 was adjudicated EXPECTED behavior (documented two-surface vocabulary below, zero defect). The single fix-batch item — the block-exclusive refusal popup that confused the every-molecule semantics — was fixed in-session (commit b749135: the message itself now explains the requirement) with all gates re-green. All three ROADMAP Phase-5 criteria now carry [HUMAN] verdict coverage; Phase 5 is ready for the phase verifier.**

## Performance

- **Duration:** fix + re-green + verdict recording (~20 min); one refusal-message rewrite in `aamatch/generator.py`
- **Completed:** 2026-09-20
- **Tasks:** 1 blocking `checkpoint:human-verify` — resolved APPROVED with 1 fix-batch item, resolved in-session
- **Verification after fix:** `python3.6 -m py_compile aamatch/*.py` green; **753/753** WSL tests green; `=== SMOKE-08 PASS ===`, `=== SMOKE-11 PASS ===`, `=== SMOKE-14 PASS ===`

## Environment (recorded for the record)

- **PyMOL:** PyMOL(TM) 2.5.0 (Windows, via the recorded setenv.bat conda environment)
- **Install method:** 01-09 plugin-path method — repo root on the PyMOL plugin path, no copy-install (live repo copy)
- **Console triage baseline (04-14 recorded):** stock plugin-init warnings — findseq, aKMT_Lys_pred, cb_colors, wfmesh, bnitools, mtsslPlotter, mtsslTrilaterate, SuperSymPlugin, phase9_ssl_probe — pre-existing and UNRELATED to AA-match; only NEW AA-match tracebacks/prints are defects. Session log observed only this baseline + normal AA-match lines ('game started -- ...', 'You clicked ...', 'Selector: selection "sele" ...') across ~14 game starts.

## Checkpoint Verdict: APPROVED with 1 fix-batch item (human, 2026-09-20), resolved in-session — 9/9 PASS (step 7 = EXPECTED)

| Step | Requirement / ROADMAP criterion | Verdict | Notes |
|------|--------------------------------|---------|-------|
| 1-6 | SETUP-11 start sequence (1-2), SCORE-04 status surface (3-4), PLAY-05 hint (5-6) | PASS | Human quote: **"1-6 pass"** — countdown cadence + tab switch + timer-from-zero; P-2 double-Start cancel + Cleanup-mid-countdown; info-box narrative + deduped ERROR + timer label; timer FREEZES under the modal file dialog (P-5, the not-headlessly-provable behavior, human-confirmed); hint = carbon-only orange recolor, ligand/incapable untouched, idempotent, coexists with selection green, full Done restore, hint-before-selection trap clean. Hint color 'orange' CONFIRMED legible (no adjustment requested). |
| 7 | SCORE-04 (both required modes) | PASS (EXPECTED behavior — documented below) | Human quote: **"7 showing only 'any interaction' no 1, block_exclusive show required: hbond x 1 not required: N interactions if its expected"**. Investigation: the human's quotes match the WIZARD PANEL vocabulary character-for-character — 'Required: any interaction' = `wizard_text.py:90-91`; 'Required: h_bond x1' = `wizard_text.py:217-219` — the 03-02-pinned design wording. The Qt Game-status tab label carries the 05-01 vocabulary 'Required: any 1 interaction' / 'Required: N interaction(s): ...' (`status_text.py:97,101`), pinned live-green by `tests/test_status_text.py:75-105` and SMOKE-14 part 4.8. Two surfaces, two pinned vocabularies, both as-designed — NO defect. See the both-surface string table below. |
| 8 | Restart feel (feeds Phase 6) | PASS | Human quote: **"8 pass"** — fresh countdown + cleared info box, prior wizard popped, no residue, timer restarts from 0:00. |
| 9 | Console baseline | PASS | Human quote: **"9 see above"** (referring to the console session log) — the log showed ONLY the recorded stock-plugin baseline warnings (findseq, aKMT_Lys_pred, cb_colors, wfmesh, bnitools, mtsslPlotter, mtsslTrilaterate, SuperSymPlugin, phase9_ssl_probe) plus normal AA-match lines ('game started -- ...', 'You clicked ...', 'Selector: selection "sele" ...') across ~14 game starts. Zero AA-match tracebacks. |

### Step 7 — the two requirement-display surfaces, pinned strings (permanent record)

| Surface | Source of truth | `any` mode (exclusive) | list mode (block_exclusive/unset) |
|---------|-----------------|------------------------|-----------------------------------|
| Wizard panel (Phase-4 feedback surface) | `wizard_text.py:90-91` + `:217-219` (03-02-pinned) | `Required: any interaction` | `Required: h_bond x1` (per-item `<type> x<count>`) |
| Qt Game-status tab label (SCORE-04) | `status_text.py:97,101` (05-01-pinned; live-green via `tests/test_status_text.py:75-105` + SMOKE-14 part 4.8) | `Required: any 1 interaction` | `Required: N interaction(s): <type> x1, ...` |

The human's step-7 observation ('any interaction' with no count, 'hbond x 1' without the 'N interaction(s)' prefix) matches the WIZARD PANEL exactly — the expected, designed behavior on both surfaces. Recorded so no later phase re-flags the divergence.

### Step 7 — the "why can't block-exclusive support pi-stacking/cation-pi?" clarification (recorded answer)

Human quote: **"and why the set cannot support pi-stacking/cation-pi etc in block-exclusive? u already support e.g. cation-pi and salt bridge in unset, and tested to work, anyway"**

Recorded answer: the two modes have DIFFERENT sampling contracts — detector support is identical; the generator's per-molecule policy differs.

- **block_exclusive** DEMANDS the exact checked set from **EVERY molecule of the game**: `derive_required` runs per-molecule (`generator.py:823`, mode branch `:398-410`) and refuses if ANY checked type is unsupported by that molecule — solvability by construction requires every molecule to be able to score the full requirement.
- **unset** SAMPLES per-molecule from whatever each picked molecule supports (`generator.py:412-417`) — the draw pool is the ligand-supported intersection, so cation-pi/salt-bridge appear when and only when the molecule supports them (as observed and tested).
- **Why the dev set always refuses non-universal checks:** the dev set has 2 candidates — benzamide (h_bond/pi_stacking/cation_pi/hydrophobic; no charge => no salt_bridge) and acetate (h_bond/salt_bridge/hydrophobic; no ring => no pi_stacking/cation_pi). At default `molecules_per_level=2` with 2 candidates, the distinctness rule (`generator.py:800-817`) puts BOTH ligands in EVERY level => the checked set must be supported by both molecules => any non-universal checked set (pi-stacking, cation-pi, salt-bridge) refuses deterministically.
- The refusal is the **solvability-by-construction contract working fail-closed** — the generator never promises an unsolvable level. The recorded 04-12 seed-7 Randomize anecdote is the same mechanism.
- **Probe evidence** (tmp/, git-ignored): block_exclusive {salt_bridge} at m=1, seed 0 **did** generate — the mode works; the dev-set pool is the constraint.
- **Designed cure:** Phase 8 curates ~9 diverse demos (charged, aromatic, halogenated, metal-bearing) so block_exclusive gets a real eligible pool.

## Fix-Batch Record (1 item, resolved in-session — the 04-15 pattern)

**Human directive (verbatim):** *"if the interaction should be possible in all mol of the set, the popup warning should provide this, otherwise confusing."*

**The failure:** the generator's unsupported-checked-types refusal in block_exclusive mode read:

> `molecule cannot support required interaction(s): pi_stacking`

— factually correct, but it does not convey the block-exclusive SEMANTICS (the checked set must be supported by EVERY molecule of the game), so a user reading the popup at the dev set cannot tell why a type that works in unset is refused here.

**The fix (commit `b749135`, `aamatch/generator.py:398-410` — same raise site, same control flow, same `GenerationError` contract, no behavior change, no ligand chemistry hardcoded):** the refusal now reads:

> `block_exclusive mode requires EVERY molecule of the game to support ALL checked interaction(s); this molecule cannot support: pi_stacking -- uncheck the unsupported type(s) in Setup (or lower molecules_per_level / pick a molecule set whose every member supports all checked types)`

The message itself now: (a) states the every-molecule requirement; (b) names the offending type(s); (c) the refusing molecule's set_id/entry_id is NOT available in the refusal's scope (`derive_required` receives only setup + ligand profile — the identity lives one frame up at `generator.py:823`); (d) gives an actionable remedy. `setup_form.py` was checked for a mirror: only the empty-allowed wording is mirrored there (`setup_form.py:104-107`); the unsupported-type wording is generator-only (the popup originates from the generator), so `setup_form.py` was left untouched.

**Pin updates required: NONE.** No test or smoke ever pinned the old message verbatim — `tests/test_generator.py:401-406,989-998` pin substrings ('halogen', 'no interactions checked', 'supports none') which all survive; greps across `tests/` and `smoke/` found zero verbatim occurrences of the old text (the only matches were `.planning` research docs, historical records, left as-is).

**Re-green proof (post-fix, all green):**

- `python3.6 -m py_compile aamatch/*.py` — OK
- `python3.6 -m unittest discover -s tests -v` — **753/753 OK** (count unchanged; purity gates included)
- `bash smoke/run_smoke.sh smoke/smoke_11_window.py` — **=== SMOKE-11 PASS ===**
- `bash smoke/run_smoke.sh smoke/smoke_14_status_surface.py` — **=== SMOKE-14 PASS ===**
- `bash smoke/run_smoke.sh smoke/smoke_08_starter.py` — **=== SMOKE-08 PASS ===**

**Visual re-confirm:** the new popup wording rides any later GUI session (headless proof of the new string is the WSL suite above; the human sees it on the next block-exclusive refusal interaction) — per the 04-15 precedent.

## Deviations from Plan

None beyond the recorded fix-batch item — the plan prescribed exactly this flow (fix + re-green + record).

## Authentication Gates

None.

## Next Phase Readiness

- All three ROADMAP Phase-5 criteria (SETUP-11, SCORE-04, PLAY-05) carry [HUMAN] verdict coverage — Phase 5 is ready for `/gsd-verify-phase`.
- Restart-feel verdict (step 8 PASS) feeds Phase 6.
- Phase 8 inherits the curated-demos requirement: block_exclusive needs a diverse eligible pool (claimed in the roadmap, re-confirmed by the dev-set refusal investigations here).
