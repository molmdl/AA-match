# Nudge-direction re-open (human report 2026-09-21, post-Phase-6)

## Why this file

The Phase-6 06-10 consolidated GUI checkpoint surfaced a report too large for
the post-phase record trail: after full Phase-6 play (confirm/skip/give-up/
restart/reset all exercised across 3 levels), the human re-raised the Phase-3
nudge-direction concern with a STRONGER claim than the original:

- 03-06 original report: "up/down feel inverted after scene rotation" —
  adjudicated correct-by-construction, then FROZEN at 03-07
  ("Nudge left/right SCREEN-RELATIVE BY DESIGN").
- 2026-09-21 report: nudges feel "not viewer-relative at all — like absolute
  coordinates". The human also recalls having raised the issue before (the
  03-06 note).

STATE.md carries the standing pointer to this file; ROADMAP phase contracts
stay untouched.

## Claim under test

Keyboard/panel nudges (LEFT/RIGHT + ',' '.' + q/w/e/d + panel Up/Down
buttons) move the selected AA in the player's CURRENT VIEW direction
(camera-frame steps converted to world frame), per the 03-02/03-01 design.

The human's claim is that the observed on-screen movement contradicts this —
movement appears world-absolute rather than view-relative.

## Evidence status (as of 2026-09-21)

### Code-level facts (re-verified 2026-09-21)

- `aamatch/wizard.py:585` — the nudge handler re-reads `cmd.get_view()` PER
  PRESS. No stale-view cache exists; a rotated view after the press is
  picked up on the next press.
- `aamatch/wizard_core.py:135` `view_camera_to_world` — converts the
  camera-frame step to world via `R^T . step`, where R is get_view's
  row-major 3x3 world->camera block. Unit-pinned in tests; the camera-frame
  step vectors ((−1..1,0,0)/(0,±1,0)/(0,0,∓1)) are pinned in wizard_text.
- Movement itself is a BAKED world-frame transform (`cmd.translate(state=1,
  camera=0)` / `cmd.rotate(camera=0)`), so once the world step vector is
  computed, application is frame-faithful.

### Live-proof coverage gap (the one real hole)

- The 03-04 live verification covered ONLY a yaw case: scripted Rz(90) view,
  nudge deviation 2.51e-08. **Pitch and roll were never live-tested.**
- Mathematical argument on record: a fixed convention error (e.g. transposed
  R vs R^T) CANNOT pass the yaw test and fail pitch/roll — the matrix
  identity is orientation-independent for pure axis permutations. So a
  wrong-convention bug is ruled out by the existing yaw proof.
- NOT ruled out: (a) roll-dependent human perception (screen direction vs
  world direction genuinely diverge after a camera roll — that is what
  screen-relative MEANS, but it FEELS wrong when judging against the grid),
  (b) an unknown transform application subtlety in the translate/rotate
  composition for non-yaw rotations (untested path).

### Prime suspect (hypothesis to kill first)

The 03-06 start-composition LAW applies a CAMERA-ONLY ROLL after zoom-to-frame
so the active ligand composes above the grid. After that roll:

- Screen-up ≈ NOT world-up; screen-x ≈ NOT world-x.
- A viewer-relative nudge therefore moves the AA along a direction that
  disagrees with the grid axes / the player's mental world model — reading as
  "diagonal" or "absolute" even though the transform is correct
  viewer-relative.

This is consistent with BOTH reports (03-06 "after scene rotation", 2026-09-21
"not viewer-relative at all") and requires NO code bug to exist.

## Decisive next steps (cheap, before any code change)

1. **Headless probe (tmp/, ~5 min):** script a ROLLED + TILTED view
   (e.g. start view then `cmd.turn/rotate` a known roll + pitch), apply each
   camera-frame nudge unit, and PRINT the exact world displacement per
   camera-frame nudge for each of the 6 directions. Assert displacement ==
   R^T . step. This proves/disproves the math end-to-end for pitch/roll —
   the gap the 03-04 proof left.
2. **30-second GUI check (human):** in a visibly ROLLED game view (fresh
   game start — the roll happens automatically), pick an AA, press LEFT and
   UP, and watch whether the AA tracks the screen direction or the world
   axis. Report which it appears to follow.

## Outcomes and their remedies

- **(a) Confirmed viewer-relative (expected)** — it is a UX problem, not a
  math problem. Candidate remedies (human's call; 03-07 freeze must be
  deliberately re-opened, not silently edited):
  - Reduce or drop the start-composition roll so world-up ≈ screen-up more
    often (framing-law change, needs 03-06 law amendment record).
  - Keep behavior + document it in Phase-9 help text ("keys move in your
    current view direction") — the existing standing note.
  - Add an on-screen orientation hint (axis guide) — scope risk, evaluate
    only if the first two feel insufficient.
- **(b) Disproven** — genuine bug: single fix site is
  `wizard_core.view_camera_to_world` (+ regression pin with a rolled+tilted
  scripted view in the invariance battery). Still not urgent, but then it is
  a fix, not a preference.

## Constraints on any change

- The 03-07 human decision "screen-relative BY DESIGN" is FROZEN — changing
  movement semantics is a deliberate re-opening with a recorded decision, not
  a drive-by edit.
- wizard_core is a PURE_MODULES member: any change must keep the purity gate
  (tests/test_purity.py) green and update the unit pins.
- If the remedy touches the start-composition roll, the 03-06 framing chain
  laws (zoom-to-frame THEN camera-only roll) must be amended in the same
  record — they are load-bearing for the start view.
- Phase-9 help text (HELP-01/DOCS-01) must match whatever is finally decided
  — the current standing note says "keys move in your current view
  direction"; do not let docs drift from the final behavior.

## Related candidates

- Representation tuning (ligand ball-and-stick, AA thinner sticks/wires) is
  recorded as the Phase-9 09-01 candidate in STATE.md — if a Phase-9
  "gameplay feel" plan batch forms, nudge-UX and representations pair
  naturally under one [HUMAN] look/feel checkpoint.
