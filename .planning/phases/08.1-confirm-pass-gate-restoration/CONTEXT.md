# Phase 8.1 Planning Context — Confirm Pass-Gate Restoration

Inserted 2026-09-27 by /gsd-insert-phase after human GUI sessions exposed a core-loop semantics
defect. Read this BEFORE planning; it contains the full provenance and the constraints agreed
with the human. Related: STATE.md (Roadmap Evolution + Phase 8 Decisions, 2026-09-27 entries).

## Goal (outcome-shaped)

The game's core loop matches the spec and the human's originally-tested semantics:
Confirm is a detection attempt that passes ONLY when the required interactions are formed;
blind confirm can never pass, score, or win. The requirement/decision records that encoded
the wrong behavior are repaired. The deferred 08-11 [HUMAN] checkpoint closes in this phase.

## Provenance (receipts in-repo — do not re-derive)

- spec.md:40 — Game tab shows "type and number of interactions **required to finish this
  molecule**"; spec.md:52 — "click the confirm button to **finish this molecule**" ⇒
  pass-gate reading. spec.md 7.3 "Once the molecule is finished … then move to the next
  molecule" is the AMBIGUOUS line that was misread.
- Phase-3 code (commit `1c3737c`, human-validated at 03-06/03-07 checkpoints):
  `_confirm_molecule_impl` detected + rendered Formed/Missing and STAYED — no record,
  no advance. THIS is the semantics to restore.
- Phase 6 defect chain: REQUIREMENTS.md SCORE-01 over-specified "…then advances to the
  next molecule" (no pass condition) → 06-05-PLAN D3 "Confirm advances IMMEDIATELY" →
  pinned by SMOKE-15 B2/B5 + SMOKE-16 C5/F → 06-10 checkpoint approved following the
  plan's checklist. Skip (spec 43, partial score) is only meaningful if Confirm is the
  pass gate — the redundancy smell test that would have caught the misreading.
- Phases 7/8 are innocent (diff audit 06-10→HEAD: zero gameplay hunks).
- Already landed: `9870561` (panel-end timer/pop fix, game_window.py + SMOKE-16 PART F —
  human retest confirmed in-GUI 2026-09-27) and `0fb3d7d` (float32 front-offset noise
  floor). These stay.

## Human directive (2026-09-27, verbatim intent)

"IN THE PAST THE CONFIRM DETECT INTERACTION, ONLY PASS IF ITS CORRECT, OTHERWISE NOT
PASSING!" + "in previous phases… if confirm w/o right interaction its not advancing".
This OVERRIDES the 06-10-approved advance-on-confirm semantics. Record as a dated human
amendment, never a silent edit. spec.md itself is ambiguous-not-wrong: annotate only if
the human asks (ask at the 8.1-03 checkpoint; default leave untouched).

## Constraints for planning

1. **One gate site** for the pass rule so wizard-panel Confirm AND Game-tab Confirm
   inherit it (engine confirm op is the likely choke point — verify with greps that no
   other advance path exists).
2. **Single-homed constant** `CONFIRM_PASS_RULE = 'all'` (all required formed);
   'any' (≥1 formed) documented as the alternative — one-line flip.
3. **Failed confirm:** NO record (no molecule_scores entry, no skip_count change), NO
   advance, debrief (Formed/Missing — SCORE-02 feedback) + clear not-passing/retry line,
   timer keeps running, retry freely. Purity gates apply to any pure-layer logic.
4. **Skip/Give Up unchanged** (spec warnings stay); they become the non-passing advance
   paths by construction.
5. **Pinned tests must be REWORKED, not deleted:** SMOKE-15 B2/B5, SMOKE-16 C5 + PART F
   (PART F's 9870561 timer pins must survive), engine/wizard WSL pins; verify
   SMOKE-17/18/19/20 persistence (molecule_scores only from passes/skips); check
   smoke_04 E2E placement flow still holds. Full battery green is the exit bar
   (912+ WSL, smokes 01–21).
6. **Records repair is part of this phase** (records-first plan recommended):
   REQUIREMENTS.md SCORE-01 rewritten (pass-gate wording; check SCORE-03 too),
   ROADMAP Phase-6 criterion-1 addendum, PROJECT.md Key Decisions + STATE.md dated
   amendment with the provenance chain.
7. **The final plan MUST fold in the deferred 08-11 Task 3** (human decision 2026-09-27):
   one combined [HUMAN] GUI session covering (a) 8.1 retest — failed confirm does not
   advance/score, retry works, correct placement passes and advances, Skip escape,
   win only after all molecules pass, tab+panel parity; (b) 08-11's open items —
   grouped-dropdown (already human-passed 2026-09-27 "1 pass"), curated-set play +
   Cleanup check, DATA_SOURCES.md sign-off, detector-verdict acceptance (probe verdict:
   NO threshold surprise, no DETECTOR_VERSION bump — recorded in STATE.md). On approval
   one continuation records 08-11-SUMMARY.md (criterion coverage map already drafted in
   STATE.md) + the 8.1 plan summary.
8. Phase 8's verifier runs AFTER 8.1 lands (on the corrected tree).

## Known carry-forward items (not 8.1 scope — do not absorb)

- Arrow-key direction re-open probe + representation tuning → Phase 9 (planned 09-01).
- Human decision candidates (confirm 0-formed warning is now MOOT — superseded by the
  pass gate; live formed-count in info box; endgame modal for panel-ended games;
  Toward-ligand in the Game tab) → Phase 9 planning inputs, listed in the 2026-09-27
  report to the human.
