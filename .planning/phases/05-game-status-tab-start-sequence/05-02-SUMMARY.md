---
phase: 05-game-status-tab-start-sequence
plan: 02
subsystem: testing
tags: [hint, capability-truth, detect-04, gen-04, tdd, pure-layer]

requires:
  - phase: 02-pure-foundation-data-engine
    provides: capability.py single typing home (aa_capable / residue_capabilities),
      generator solvability-by-construction, game_state.score refusal wording family
  - phase: 05-game-status-tab-start-sequence
    provides: 05-RESEARCH-hint.md Pattern 1 sketches + mode-semantics pins

provides:
  - capability.hint_required_types(required) — resolved required dict -> type tuple
    ('any' -> all 7 canonical; 'list' -> items in given order; 4 fail-closed refusals)
  - capability.hint_candidate_slots(slots, profile, required) — live capability
    intersection, payload-order deterministic, capable distractors included,
    generation-time provenance never read (pitfall H-2)
  - GEN-04 parity invariant (TestGen04HintParity) — required slots always appear
    in the live-computed hint candidates over real generated payloads
  - Residue-capabilities agreement pin (aa_capable union == residue_capabilities)

affects: [game-status-tab, hint-recolor, wizard, game_window, scoring]

tech-stack:
  added: []
  patterns:
    - "Hint = capability-live recomputation through the ONE typing home; never
       reads payload provenance fields (DETECT-04 by construction)"
    - "Refusal-wording family reuse: new pure validators mirror game_state.score
       phrasing so score/hint/wizard_text can never disagree in shape or tone"

key-files:
  created: []
  modified:
    - aamatch/capability.py
    - tests/test_capability.py
    - tests/test_generator_invariants.py

key-decisions:
  - "Hint refuses with the game_state.score refusal-family wording (one
     vocabulary for mode/shape refusals across scoring, hint, and wizard text)"
  - "Hint vocabulary for 'any' mode = all 7 canonical INTERACTION_TYPES
     (scoring-honest), never the setup's allowed list (sampling vocabulary only)"

patterns-established:
  - "GEN-04 parity invariant: cross-module alarm pinning 'solvability promise ==
     live hint candidates' on real generator payloads; fires together with
     allocate_slots' own refusal on any future capability-table edit"

duration: 7 min
completed: 2026-09-18
---

# Phase 05 Plan 02: Hint Predicates Battery Summary

**Pure PLAY-05 "could form" half landed RED-first: capability.hint_required_types + hint_candidate_slots composing the existing single typing home, with the GEN-04 parity invariant pinning "solvability == hint candidates" forever — 710 WSL tests green, zero new imports, zero gate edits.**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-09-18T18:28:35Z
- **Completed:** 2026-09-18T18:36:04Z
- **Tasks:** 3/3
- **Files modified:** 3

## Accomplishments

- `hint_required_types(required)`: mode 'any' → all 7 canonical INTERACTION_TYPES (scoring-honest vocabulary); mode 'list' → item types in GIVEN order; fail-closed ValueErrors in the game_state.score / required_summary refusal-family wording for non-dict / unknown mode / empty items / unknown item type
- `hint_candidate_slots(slots, profile, required)`: `residue_capabilities(slot['aa'], profile) ∩ required_types` non-empty ⇒ candidate, returned as a payload-order-deterministic tuple; capable DISTRACTORS included (generation-time provenance NEVER read — pitfall H-2); incapable slots and ligand-unsupported types excluded
- GEN-04 parity invariant green: over 12 fresh (4 seeds × 3 modes) generated payloads, every role='required' slot's slot_id appears in the live-computed candidates; a companion test proves capable distractors enter the candidate set despite their empty provenance (can_form never dereferenced)
- Belt-and-braces agreement pin: for every AA_RESIDUES member across 5 representative profiles, `residue_capabilities == {aa_capable per type}` union

## Task Commits

1. **Task 1 (RED): hint predicate battery + GEN-04 parity invariant** — `084aa45` (test)
2. **Task 2 (GREEN): implement hint_required_types + hint_candidate_slots** — `f594fa3` (feat)
3. **Task 3: full regression sweep** — no commit required (no docstring polish beyond the GREEN commit; `<files>[]`)

**Plan metadata:** see the closing `docs(05-02)` commit.

## Files Created/Modified

- `aamatch/capability.py` — +88 lines: the two hint helpers after `residue_capabilities`; docstrings carry the DETECT-04 single-home argument, the provenance-read prohibition, and the GEN-04 parity note; ZERO new imports
- `tests/test_capability.py` — +hint battery: TestHintRequiredTypes (10 tests), TestHintCandidateSlots (11 tests), TestResidueCapabilitiesAgreement (1 swept test)
- `tests/test_generator_invariants.py` — +TestGen04HintParity: G20 required-slots ⊆ candidates + G21 capable-distractor anti-provenance pin over fresh generator payloads

## Decisions Made

- Refusal wording mirrors the game_state.score family verbatim in structure (`unknown required mode %r (expected one of any, list)`, the empty-items 'any'-mode note, found-type naming) — one refusal vocabulary across scoring, hint, and wizard text surfaces (plan-pinned; the research C sketch was transcribed).
- 'any'-mode hint vocabulary = all 7 canonical types, scoped by the resolved required dict ONLY — the setup's allowed_interactions list is generation-time sampling vocabulary (research H-6; no hint code references setup).
- Unknown resn in a slot is incapable, not an error (inherits residue_capabilities' fail-closed empty set); malformed slot SHAPES are the error.

## Deviations from Plan

None — plan executed exactly as written. (One item-level test was extended with a duplicated-type items case pinned by the plan's own behavior example "h_bond x1, pi_stacking x2 → given order"; implementation unchanged.)

## Issues Encountered

None. RED failed for exactly the right reason (21 errors, all `AttributeError: module 'aamatch.capability' has no attribute 'hint_...'`); GREEN passed on the first implementation (the research Pattern 1 sketches transcribed verbatim).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- The pure half of PLAY-05 is complete; the parallel/cmd-tier hint work (engine `ligand_profile_molecule`, `GameWizard.hint()`, the Game-tab button in the sibling's `game_window.py`, HINT_COLOR pin, SMOKE-11 hint PART) consumes these two helpers directly per 05-RESEARCH-hint.md Patterns 2–4.
- Purity gates untouched: capability.py remains registered with no new imports; no PURE_MODULES/PROSE_PIN/SCANNED_MODULES edits were needed by this plan (confirmed by the full 710-test sweep).
- No blockers or concerns carried forward.

---
*Phase: 05-game-status-tab-start-sequence*
*Completed: 2026-09-18*
