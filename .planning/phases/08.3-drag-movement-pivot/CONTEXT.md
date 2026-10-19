# Phase 8.3 Context — Drag-Movement Pivot (seeded at insertion)

**Written:** 2026-10-18 (insertion step of /gsd-insert-phase; every claim below is copied from the already-committed decision records — nothing new invented here).
**Status:** Phase inserted AFTER Phase 8.2, BEFORE Phase 9. NOT PLANNED yet — run `/gsd-plan-phase 8.3` in a fresh session.

## The decision (LOCKED — human, 2026-10-18)

- Mouse-drag becomes THE movement input.
- ALL keyboard direction keys removed.
- Wizard-panel movement list: ONLY Toward-ligand survives (TOWARD_STEP 2.5 Å unchanged — world/goal-directed, view-invariant).
- The disputed direction-input class is DELETED rather than adjudicated (the 08.2-10 step-4 dispute closed as SUPERSEDED).

Human verbatim (full chain):
- "would it be easier if we simply jusr drop the arrow+direction support and switch to e.g. ctrl+mouse movement upon selection?"
- "good, could u record this and suggest if i should do gap-filling plans (and overide current if needed)? mouse to replace all keyboard direction buttons, and replace the directions in wizard panel, only keep the towards ligand in that list."

**Authoritative record homes (do not re-derive):** STATE.md §Phase 8.2 Decisions 2026-10-18 bullet (richest) · PROJECT.md Key Decisions dated row (2026-10-18) · ROADMAP.md Phase-8.2 NOTE (2026-10-18) · 08.2-10-DEBUG-HANDOFF.md RESOLUTION section · .planning/debug/nudge-direction-mouse-rotation.md (USER RULING + Resolution).

## Why SUPERSEDED, not adjudicated

The shipped movement law was exonerated twice on final receipts — machine (P1 30/30 @ 0.0000 deg; step-4 probe screen_dx=-1.000000 at every orientation) and LIVE in the real GUI in the user's own environment (d4 scripted real-GUI repro 2026-10-18 03:34, tmp/probe_082_gui_repro.log: at the user's verbatim c2 orientation, panel AND keyboard channels, exact monitor-LEFT, all rows PASS). The 10-12 "left goes down" row was never reproduced by current code; its session-side candidates stay unadjudicated — mooted by this pivot. The input class carrying the dispute is removed by decision.

## Planner standing notes (BINDING — carried from the decision records)

1. **Pitfall-6 drag hazards:** mouse drags install PyMOL's Dragging wizard, which REPLACES the active game wizard mid-session; transforms must BAKE world-frame coordinates (scoring reads them), never object matrices; drag targets the picked AA object as a rigid body ONLY (never ligand/board).
2. **No stock gesture fits:** ctrl-left in 3-Button Editing = torsion ('torf'); ctsh-left = move-ATOM (distorts the rigid body); whole-object drag-to-translate needs custom wiring → expect a [HUMAN] gesture-mapping decision checkpoint early in planning.
3. **Deletion battery:** direction keys/buttons, the camera-step law if Toward no longer needs it, SMOKE-07/08/16/23 direction portions, 08.2-03 AST movement pins — all via dated EXPECTED-RED bridges under the deliberate-evolution law; NEVER silent pin edits, NEVER weakened standing gates (purity: tests/test_purity.py stays enforced; no sys.modules stubs).
4. **Phase-9 help text must be re-worded to the drag model** (the nudge-direction-reopen "keys move in your current view direction" standing note is obsolete on landing).
5. **Protocol constraints inherited:** human verdicts transcribed verbatim; tmp/ git-ignored for one-off probes; never mix plugin import mechanisms (gate 5 — one active aamatch per session); GUI runs are [HUMAN] checkpoints (WSL cannot show Qt); python3.6-only WSL testing; commit style `feat(08.3-NN):` etc.
