# Phase 9 — Aspect 1 of 3: In-Game Help Surface (HELP-01) — Research

**Phase:** 9 — Help, Docs & Release Audit
**Aspect:** 1/3 — the IN-GAME HELP SURFACE (roadmap criterion 1, requirement HELP-01)
**Researched:** 2026-11-16 (WSL, repo at HEAD `b860c10`; quick-004 tree)
**Researcher scope:** read-only code/records audit + feasibility analysis. No code changed, no GUI run, no commit. Sibling output `09-RESEARCH-docs-audit.md` (same dir) covers the DOCS aspect — not duplicated here.
**Criterion under research:** `[HUMAN] The setup window and game tab provide a help panel + tooltips sufficient to play without external docs — each interaction type explained clearly but sufficiently; destructive actions carry warnings. (HELP-01)` (ROADMAP.md:325)

---

## §1 Verified inventory — every existing user-facing string surface

Legend: **pinned-by** = test/smoke that asserts the string verbatim (WSL tests cannot import Qt-tier modules — `tests/test_purity.py:107-108` FORBIDDEN includes `PyQt5`; Qt-tier strings are only mirrored by headless smokes).

### §1.1 `aamatch/setup_window.py` (Qt tier — Setup tab)

| # | Surface | Exact string | file:line | pinned-by |
|---|---------|--------------|-----------|-----------|
| 1 | Window title | `'AA-match Setup'` | setup_window.py:148 | **none** (verified: no smoke or test asserts `windowTitle` — grep over smoke/*.py returned zero hits) |
| 2 | Tab labels | `'Setup'`, `'Game status'` | setup_window.py:242, 244 | smoke_11_window.py:994-997 (`tabText(0)=='Setup'`, `tabText(1)=='Game status'`) |
| 3 | Btn + tooltip | `'Reset'` / `'Restore the default settings.'` | setup_window.py:208-209 | label only: smoke_11_window.py:304-309, 1004-1010. **Tooltip text NOT pinned anywhere** |
| 4 | Btn + tooltip | `'Randomize'` / `'Randomize the setup parameters.'` | setup_window.py:210-211 | label only (same smoke rows) |
| 5 | Btn + tooltip | `'Save Setup'` / `'Save the game setup parameters to a file.'` | setup_window.py:212-214 | label only |
| 6 | Btn + tooltip | `'Load Setup'` / `'Load the setup parameters from a file.'` | setup_window.py:215-217 | label only |
| 7 | Btn + tooltip | `'Generate and export'` / `'Generate all levels and save the initial game state to a file for sharing or later loading.'` | setup_window.py:218-222 | label only |
| 8 | Btn + tooltip | `'Cleanup model'` / `'Remove the game-generated objects from the scene.'` | setup_window.py:223-225 | label only |
| 9 | Btn + tooltip | `'Start'` / `'Start the game with the current setup.'` | setup_window.py:226-227 | label only |
| 10 | Radio + tooltip | `'Bundled demo set'` / `'Generate from a demo set bundled with AA-match.'` | setup_window.py:273-275 | none (Qt tier) |
| 11 | Radio + tooltip | `'Upload my molecules...'` / `'Generate from your own SDF or MOL2 file (one file; multi-record files give several molecules).'` | setup_window.py:276-280 | none |
| 12 | Combo tooltip | `'Which bundled demo set to generate from.'` | setup_window.py:292-293 | none |
| 13 | Degrade note | `'(no bundled sets)'` item + `'Could not read the bundled demo list: %s'` | setup_window.py:364-366 | none |
| 14 | Browse + tooltip | `'Browse...'` / `'Pick an SDF or MOL2 molecule file (single file; a multi-record file provides several molecules).'` | setup_window.py:304-307 | none |
| 15 | Spinbox label + tooltip | `'Small molecules per level'` / `'How many small molecules each level contains (default 2; range mirrors the frozen 1..10 bounds).'` | setup_window.py:443-446 | none |
| 16 | Spinbox label + tooltip | `'Difficulty levels'` / `'How many difficulty levels per game (each level is harder: bigger grid, more required interactions).'` | setup_window.py:452-455 | none |
| 17 | Group box | `'Molecule source'` (269), `'Game size'` (436), `'Required interactions'` (467), `'Allowed interactions'` (520) | setup_window.py:269/436/467/520 | none |
| 18 | Mode radios + tooltips | `'Exclusive (any allowed)'` / `'The game accepts ANY of the checked interactions.'`; `'Block-exclusive (checked set)'` / `'The player must form EXACTLY the checked interactions.'`; `'Unset (random)'` / `'The game randomizes the required set from the checked types (hydrophobic is excluded from random picks).'` | setup_window.py:470-482 | none |
| 19 | Mode context label (`_MODE_CONTEXT`) | `'The game accepts ANY of the checked interactions'` / `'The player must form EXACTLY the checked interactions'` / `'The game randomizes the required set from the checked types (hydrophobic excluded from random picks).'` | setup_window.py:418-425 (rendered at 507-508) | none |
| 20 | 7 interaction labels (`_INTERACTION_LABELS`) | `'Hydrogen bond'`, `'Salt bridge'`, `'Pi-stacking'`, `'Cation-pi'`, `'Hydrophobic'`, `'Halogen bond'`, `'Metal coordination'` | setup_window.py:386-394 | none (Qt tier; canonical enum order from setup_state.INTERACTION_TYPES, setup_state.py:40-41) |
| 21 | 7 per-type tooltips (`_INTERACTION_TIPS`) | `'Hydrogen bond: a donor hydrogen (-OH or -NH) facing an acceptor oxygen or nitrogen on the other molecule.'`; `'Salt bridge: an opposite-charge pair held together (a positive group on one molecule, a negative group on the other).'`; `'Pi-stacking: two aromatic rings stacked face-on or edge-on.'`; `'Cation-pi: a positively charged group resting on the face of an aromatic ring.'`; `'Hydrophobic: non-polar carbons of both molecules clustered into the same greasy patch.'`; `'Halogen bond: a Cl/Br/I on the molecule accepting from a donor on the amino acid.'`; `'Metal coordination: a metal ion bound by two or more donor atoms.'` | setup_window.py:397-415 (applied at 526) | none |
| 22 | Upload path label + sha256 tooltip | `'%s\n(%d molecule record(s))'` label; tooltip = full path (`+ '\nsha256: %s'` after Load) | setup_window.py:862-864, 644-652 | none |
| 23 | `_guard` warning box | `QMessageBox.warning(self, 'AA-match', str(e))` — str(e) verbatim | setup_window.py:687 | refusal WORDINGS pinned at the pure layer (e.g. test_setup_form.py:112-157 MSG_EXCLUSIVE/MSG_BLOCK_EXCLUSIVE/MSG_UPLOAD/MSG_DEMO; generator.py:832-840 thin-set wording pinned in test_demo_supply.py) |
| 24 | Save/Load/Export confirmations | `'Setup saved to %s'` (743), `'Setup loaded from %s'` (777), export summary `'Game exported to %s (seed %d, %d level(s), %d molecule placements, source: %s)'` (116-117, shown at 945-946) | setup_window.py:742-743, 776-777, 945-946 | none |
| 25 | Cleanup info box | `'Removed %d game object(s). The scene is back to your original objects.'` | setup_window.py:921-924 | none |
| 26 | File dialogs | `'Save AA-match Setup'` (737-738), `'Load AA-match Setup'` (770-772), `'Upload molecule file'` (816-818), `'Export AA-match Game'` (939-941) | setup_window.py | none |

**Negative finding (verified):** grep for `Help|help` across setup_window.py and game_window.py returns ZERO UI surfaces (only docstring prose). **There is no help button, no help panel, no help dialog anywhere in the plugin today.**

### §1.2 `aamatch/game_window.py` (Qt tier — Game status tab, `GameTab`)

| # | Surface | Exact string | file:line | pinned-by |
|---|---------|--------------|-----------|-----------|
| 27 | Timer label + tooltip | `'0:00'` initial / `'Time since the game started.'` | game_window.py:213-214 | `'0:00'`: smoke_11_window.py:1028, smoke_16_tab.py:618-621. Tooltip: none |
| 28 | Required label + tooltip | `'Required: -'` initial / `'The interactions the current molecule requires.'` | game_window.py:216-218; reset to `'Required: -'` at 529 | label: smoke_11_window.py:1028-1029, smoke_16_tab.py:618-621, 793, 1975-1976. Tooltip: none |
| 29 | Info log tooltip | `'What happened, in order.'` | game_window.py:226 | none |
| 30 | Hint btn + tooltip | `'Hint'` / `'Highlight the amino acids that could still form a required interaction (carbon recolor only).'` | game_window.py:233-236 | `'Hint'`: smoke_11_window.py:1032-1034. Tooltip: none |
| 31 | Confirm btn + tooltip | `'Confirm'` / `'Attempt to finish this molecule: runs detection; it advances only when all required interactions are formed.'` | game_window.py:245-248 | none |
| 32 | Skip/Give-Up dropdown + tooltip | `'Skip / Give Up'` / `'Skip the current molecule or give up the game (both ask for confirmation).'` | game_window.py:258-262 | none |
| 33 | Menu actions + tooltips | `'Skip Molecule'` / `'Store the partial score and move to the next molecule (asks for confirmation).'`; `'Give Up...'` / `'Ends the game at the current stage -- asks for confirmation.'` | game_window.py:265-272 | none |
| 34 | Restart btn + tooltip | `'Restart'` / `'Replay the stored initial state into a fresh game (countdown, timer from zero, scores cleared).'` | game_window.py:280-283 | none |
| 35 | Reset btn + tooltip (`btn_reset_grid`) | `'Reset'` / `'Place all amino acids back to their grid positions; orientations are kept.'` | game_window.py:290-293 | none |
| 36 | Save btn + tooltip | `'Save'` / `'Save the running game (PyMOL session + game state) to a checkpoint file.'` | game_window.py:300-303 | none |
| 37 | Import btn + tooltip | `'Import'` / `'Load a saved checkpoint (.aamz) to resume playing, or an exported game file (.aamatch.json) to start it fresh.'` | game_window.py:310-313 | none |
| 38 | Countdown log lines | `'Get ready...'`, `'3'`, `'2'`, `'1'`, `'GO!'` | game_window.py:380, 393, 397 | smoke_11/13/16 exercise them; wording pinned via status_text.EVENT_KINDS notes (status_text.py:85-88) |
| 39 | Hint log line | `'Hint: %d eligible amino acid(s) highlighted.'` | game_window.py:723-724 | test_status_text.py EVENT_KINDS note (status_text.py:99-100); SMOKE-16 |
| 40 | Skip/Give-Up confirmations | `QMessageBox.question(self.window(), status_text.SKIP_WARNING_TITLE, status_text.SKIP_WARNING_TEXT, Yes|No)`; same for GIVEUP | game_window.py:797-801, 821-825 | strings pinned: test_status_text.py:396-412 |
| 41 | Import unknown-kind refusal | `'expected an AA-match game or checkpoint file, found kind=%r'` | game_window.py:1128-1130 | none (Qt tier) |
| 42 | Save/Import dialogs | `'Save AA-match Game'`, `'game.aamz'`, `'AA-match Checkpoint (*.aamz);;All Files (*)'` (1041-1043); `'Import AA-match Game'`, `'AA-match (*.aamatch.json *.aamz);;All Files (*)'` (1096-1098) | game_window.py | none |
| 43 | Endgame modal | title `'AA-match'`; setText = `status_text.endgame_lines(summary)[0]`; setInformativeText = `'<br>'.join(lines[1:])` | game_window.py:1353-1361 | block pinned: test_status_text.py:721-722 |
| 44 | `_guard` warning box | `QMessageBox.warning(self, 'AA-match', str(e))` | game_window.py:696 | pure refusal wordings as in row 23 |
| 45 | Abandon line (quick-004) | `'Game abandoned.'` via `status_text.game_abandoned_line()` | game_window.py:680; status_text.py:317 | test_status_text.py (3 new TestGameAbandonedLine tests, STATE.md quick-004 row) |

### §1.3 `aamatch/wizard_text.py` (PURE — wizard panel + prompt overlay)

| # | Surface | Exact string | file:line | pinned-by |
|---|---------|--------------|-----------|-----------|
| 46 | Movement buttons | `('Toward ligand', 'cmd.get_wizard().step_to_ligand()')` — the ONLY movement entry under header `'Movement:'` | wizard_text.py:49-51, 232-234 | test_wizard_text.py:55-56, 184, 212-213 |
| 47 | Action buttons | `('Confirm', 'cmd.get_wizard().confirm_molecule()')`, `('Reset to Grid', 'cmd.get_wizard().reset_grid()')`, `('Done', 'cmd.set_wizard()')` | wizard_text.py:53-59 | test_wizard_text.py:55-56, 154, 160, 184-186 |
| 48 | Click instruction | `'Click an amino acid to select it.'` | wizard_text.py:61 | test_wizard_text.py:265 |
| 49 | Panel header | `'Molecule %s (%s/%s)'`; `'Required: ' + required_summary(...)`; `'ERROR: %s'` | wizard_text.py:212-221, 230 | test_wizard_text.py (panel contract tests) |
| 50 | Multi-molecule notice | `'Only molecule %s of %s counts and is clickable; the rest are context.'` | wizard_text.py:189-190 | test_wizard_text.py:461 |
| 51 | Result lines (list mode) | `'%d/%d required interactions formed (score %.2f)'`, `'Formed: '`, `'Formed: (none)'`, `'Missing: '`, `'Formed (not required): %s x%s'` | wizard_text.py:147-164 | test_wizard_text.py (result battery) |
| 52 | Result lines (any mode) | `'Interaction formed (score %.2f)'` / `'Nothing formed (score %.2f)'` | wizard_text.py:167, 170 | test_wizard_text.py |
| 53 | Selected prompt line | `'Selected: slot %s (%s). Move/rotate it, then Confirm.'` | wizard_text.py:273-274 | test_wizard_text.py:277 (`'Move/rotate'`) |
| 54 | Panel clip | 255-char `_clip` cap on every panel/prompt line | wizard_text.py:64-74 | Word.h:24,26 receipt in module docstring (wizard_text.py:16-22) |

### §1.4 `aamatch/status_text.py` (PURE — Game tab text builders)

| # | Surface | Exact string | file:line | pinned-by |
|---|---------|--------------|-----------|-----------|
| 55 | required_display | `'Required: any 1 interaction'` / `'Required: %d interaction%s: %s'` | status_text.py:134, 138-139 | test_status_text.py:81, 88, 96, 107 |
| 56 | Level line | `'Level %s, molecule %s of %s.'` | status_text.py:155-157 | test_status_text.py |
| 57 | Selected event line | `'Selected: slot %s (%s).'` | status_text.py:171-172 | test_status_text.py:164, 225, 231 |
| 58 | Skip warning | `SKIP_WARNING_TITLE='Skip this molecule?'`; `SKIP_WARNING_TEXT='Skip this molecule and move to the next one? The score formed so far is kept.'` | status_text.py:196-198 | test_status_text.py:396-401 |
| 59 | Give-up warning | `GIVEUP_WARNING_TITLE='Give up?'`; `GIVEUP_WARNING_TEXT='Give up and end the game now? The game ends at this stage and the endgame summary is shown.'` | status_text.py:199-201 | test_status_text.py:406-412 |
| 60 | Scored header | `'Molecule %d of %d scored %.2f (total %.2f).'` | status_text.py:235-237 | test_status_text.py |
| 61 | Failed-confirm header + retry | `'Molecule %d of %d not passing yet (score so far %.2f, total %.2f; not recorded).'` + `'Form the missing interactions and Confirm again.'` | status_text.py:254-261 | test_status_text.py (8.1 battery) |
| 62 | Skipped line | `'Skipped molecule %d of %d (partial score %.2f, total %.2f).'` | status_text.py:270-272 | test_status_text.py |
| 63 | Gave-up line | `'Game ended at level %d, molecule %d of %d (total %.2f).'` | status_text.py:280-282 | test_status_text.py |
| 64 | Reset line | `'Amino acids reset to grid positions (orientations kept).'` | status_text.py:298 | test_status_text.py |
| 65 | Restart / abandoned / saved / imported / resumed lines | `'Game restarted.'` (306), `'Game abandoned.'` (317), `'Game saved to %s.'` (327), `'Game imported: %s.'` (336), `'Game resumed from %s.'` (345) | status_text.py | test_status_text.py:564, 809, 827, 838 |
| 66 | Endgame block | `'You win! All %d level(s) finished in %s.'` / `'Game over -- gave up at level %d, molecule %d of %d.'` / `'Level %d: %.2f'` / `'Total score: %.2f.'` / `'Time: %s.'` / `'Molecules completed: %d of %d. Levels: %d.'` / `'Skips: %d. Give-ups: %d.'` | status_text.py:398-423 | test_status_text.py:721-722 |

### §1.5 `aamatch/wizard.py` (cmd tier) — panel/prompt error strings

| # | Surface | Exact string | file:line | pinned-by |
|---|---------|--------------|-----------|-----------|
| 67 | Game-over gate | `'The game is over.'` | wizard.py:485 (do_pick soft gate), 844 (`_require_playing`) | SMOKE-15/16 drive the refusal |
| 68 | No-selection movement error | `'Select an amino acid first.'` | wizard.py:732 | none (cmd tier, smoke-driven) |
| 69 | Drag arm failure | `'Drag could not be armed. (%s)'` | wizard.py:814-815 | none |
| 70 | At-ligand guard | `'Already at the ligand.'` | wizard.py:905 | none |
| 71 | One-record guard (engine) | `'This molecule already has a recorded result (scored or skipped) -- use Restart to replay the game.'` | engine.py:599-600 | none (docstring receipt wizard.py:1002) |

### §1.6 `aamatch/gamestart.py` console prints (cmd tier)

| # | Surface | Exact string | file:line |
|---|---------|--------------|-----------|
| 72 | Start print | `'AA-match %s: game started -- %d molecule(s), %d amino-acid slot(s), seed %d (        cleaned %d prior game object(s)).'` (note: 8 stray spaces before `cleaned`, byte-verified) | gamestart.py:433-436 |
| 73 | Payload-start print | `'AA-match %s: game started from embedded payload -- %d molecule(s), %d amino-acid slot(s), seed %d (cleaned %d prior game object(s)).'` | gamestart.py:500-504 |

### §1.7 `aamatch/checkpoint.py` — clarification

checkpoint.py is a PURE zip/schema module (checkpoint.py:1-8); it has **no Qt surface and no user-facing prose** — the checkpoint UI is the GameTab's Save/Import buttons + tooltips (rows 36-37) and the status_text saved/resumed lines (row 65). There is no separate "checkpoint panel".

### §1.8 Pinning summary (what the phase can rely on)

- **WSL-pinned verbatim:** all of wizard_text + status_text (rows 46-66) — these are pure modules imported by `tests/test_wizard_text.py` / `tests/test_status_text.py`.
- **Headless-smoke-pinned (labels/placeholders only):** button/tab/label texts in setup_window + game_window (SMOKE-11/14/16). **Tooltip texts are pinned NOWHERE** (SMOKE-11 only clears one tooltip — smoke_11_window.py:567).
- **Pure refusal wordings** surfaced through `_guard` boxes are pinned at the pure layer (test_setup_form.py, test_demo_supply.py, test_generator.py).
- Gate law for new scanned-module strings: `tests/test_wizard_source.py:902-914` greps SCANNED_MODULES sources for raw substrings `get_model` / `matrix_reset` / `get_object_ttt` — **even prose/help-HTML constants inside setup_window.py or game_window.py must avoid these tokens**. `find_visual_calls` (:878-892) is AST-based (Call nodes only), so prose naming `cmd.distance` etc. is safe there.

---

## §2 Gap analysis vs HELP-01 (criterion 1)

### (a) Is there ANY help panel today? — **NO.**
Zero help surfaces in both Qt modules (§1 negative finding). The only prior-art pattern is bioCHEMeleon's (§3). Criterion 1 demands "a help panel + tooltips" — the **panel half is entirely missing**.

### (b) Per-widget tooltip coverage — **good on controls, absent on concepts.**
Every Setup-tab form widget and all 7 buttons carry tooltips (rows 3-21); every Game-tab button + 3 labels carry tooltips (rows 27-37). Gaps: no tooltip anywhere explains **the drag gestures**, **scoring semantics**, or **the overall game flow**; tooltips on the Game tab describe the buttons but not the game.

### (c) Explanations audit (criterion's "sufficient to play" list)

| Topic | Exists today? | Evidence | Verdict |
|---|---|---|---|
| The 7 interaction types | Partial | Per-checkbox tooltips with 1-sentence game-term definitions (setup_window.py:397-415) | Discoverable only by hovering each checkbox; **no consolidated explanation anywhere**; no numbers, no salt-bridge/H-bond independence note |
| Scoring (binary per required item, pass gate) | Partial | Result-line vocabulary (rows 51-52), failed-confirm header says "not recorded" + retry line (row 61); Confirm tooltip says "advances only when all required interactions are formed" (row 31) | The *mechanics* (binary per type; counts never inflate — game_state.py:13-15; pass rule 'all' — game_state.py:152) are **never explained in player terms** |
| Difficulty | Yes (thin) | Tooltip row 16: "each level is harder: bigger grid, more required interactions" — accurate per generator.py:70-86 (grid_n 3..9, n_required_types 1..7, size class by thirds) | Accurate; could name the concrete axes |
| Interaction modes | Yes | Mode radio tooltips + live context label (rows 18-19) — verified accurate against generator.derive_required (generator.py:337-443): exclusive→`{'mode':'any'}` scoped by allowed (396); block_exclusive→exact checked list, count 1 each (413-414); unset→random draw from supported pool minus hydrophobic (416-439) | The strongest existing explanation; help panel should reuse, not restate |
| Demo vs upload | Yes | Rows 10-14; sha256/moved-file story only in tooltip (setup_window.py:644-652) | Sufficient; a help section could consolidate |
| **Drag controls (gestures)** | **NO — total gap** | Verified: zero shipped strings mention shift/ctrl/drag gestures (grep over setup_window.py, game_window.py, wizard_text.py — only hit is an internal docstring, game_window.py:618). Gestures ARE shipped: `cmd.button('left','shft','dgmv')`, `('left','ctsh','dgmz')`, `('right','shft','dgrt')` (wizard.py:335-337) | **The single largest HELP-01 gap.** A new user cannot discover shift+left-drag = move, ctrl+shift+left-drag = depth, shift+right-drag = rotate from any UI surface. The prompt's generic "Move/rotate it, then Confirm." (wizard_text.py:273) names the goal, not the input. STATE.md carries the standing note: *"Phase-9 help text must be worded to the drag model (CONTEXT note 4)"* (08.3-16 record-repairs bullet) |
| Molecule/level flow | Partial | `'Only molecule %s of %s counts and is clickable; the rest are context.'` (wizard_text.py:189-190) + `'Level %s, molecule %s of %s.'` (status_text.py:155-157) + advance re-frames (wizard.py:1046-1054) | In-game lines exist; **no overview** of "levels × molecules, score each, win screen at the end" |
| Skip | Yes | Tooltip (row 33) + warning (row 58) + scored-partial semantics in the tooltip | Good |
| Reset to Grid semantics | Yes | Tooltip "orientations are kept" (row 35) + pinned line (row 64); semantics verified: positions replay, rotations persist (wizard.py:1237-1252) | Good and truthful |
| Checkpoint restore | Partial | Import tooltip explains both file kinds (row 37); resume has no countdown (game_window.py:1241-1261); **no warning when Import replaces a running game** (07-07 Recorded Decision 2, game_window.py:1084-1087) | Documented decision — help should STATE the replacement semantics rather than promise a warning |
| Done (panel) | NEW semantics | quick-004 (2026-11-16): Done mid-game = abandon-stop; timer frozen, `'Game abandoned.'`, no record/modal; Done ≠ Give-Up (game_window.py:156-170, 606-682; status_text.py:309-317) | **Help must say "Done = closing the board (no record)"** — STATE.md quick-004 carry: "help wording 'Done = closing the board'; 'Game abandoned.' re-word candidate" |

### (d) Destructive actions WITHOUT warnings today (verified in code)

| Action | What it destroys | Warning today? | Evidence |
|---|---|---|---|
| Skip Molecule | forfeits remaining score potential (partial kept) | **YES** — Yes/No box | game_window.py:797-801 + status_text.py:196-198 |
| Give Up | ends game | **YES** — Yes/No box | game_window.py:821-825 + status_text.py:199-201 |
| Cleanup model | deletes ALL `_aam_*` objects (game scene) | **NO confirm** — only an AFTER info box | setup_window.py:907-924 (cancel-countdown → `_cleanup_now` → info box); deletion = `placement.cleanup_game_objects()` (setup_window.py:902-905) |
| Start | cleanup-first → replaces any running game | **NO** | gamestart.py:396 `placement.cleanup_game_objects()` runs unconditionally at start; no dialog (04-13 decision, setup_window.py:1016-1019) |
| Restart | replaces running game with replay | **NO** — recorded D9 | game_window.py:275-283 + docstring "NO confirmation warning (spec.md:43-45 requires warnings for Skip/Give Up only -- restart-reset D9)" |
| Reset to Grid | discards pose (rotations persist) | **NO** — by design non-destructive | game_window.py:961-966 |
| Panel Done | abandons live game (no record) | **NO** | wizard_text.py:58-59 (`Done` → `cmd.set_wizard()`); quick-004 abandon semantics |
| Import (either kind) | replaces running game/session | **NO** — recorded 07-07 Decision 2 | game_window.py:1084-1087 ("NO confirmation warning mid-game ... a mid-game Import discards the running game exactly like Start does") |
| Setup Load | overwrites the whole form | **NO** | setup_window.py:764-777 |
| Upload re-ingest | replaces the single session upload slot | **NO** — documented | setup_window.py:838-844 ("a NEW upload REPLACES the slot (single slot v1)") |

**Tension to surface at planning:** spec.md's own warning requirement is Skip/Give-Up only (spec.md:43-45), and three no-warning behaviors are RECORDED DECISIONS (06-08 D9; 07-07 RD2; 04-13 Start-no-dialog). Criterion 1's "destructive actions carry warnings" can be satisfied either by (i) **new confirmation modals** (a behavior change overriding recorded decisions — needs human sign-off) or (ii) **making the destructive consequences explicit in help/tooltip text** plus new warnings only where recorded decisions don't cover (Cleanup is the strongest candidate: it deletes the scene and is NOT covered by any recorded no-warning decision — its current after-the-fact box, setup_window.py:921-924, is informational, not a guard). This is a planner/human call; this research only records the verified state.

---

## §3 Where should help live, mechanically?

### §3.1 The proven prior-art pattern (bioCHEMeleon, borrowed-pattern sanctioned)

ROADMAP.md:9 explicitly sanctions borrowing "help panel/tooltips" from `tmp/bioCHEMeleon/biochemeleon/` ("Adapt, don't vendor wholesale"; user decision 2026-09-05). The shipped v1 pattern, verified in its code:

- **Content:** one module-level rich-text constant `HELP_HTML` (tmp/bioCHEMeleon/biochemeleon/__init__.py:8-14 header + :14 onward) — 6 sections as `<h2>` blocks with `<ul><li><b>` items; QTextEdit renders the fragment without `<html>/<body>` wrapper (:10-13 comment); `&` escaped as `&amp;`.
- **Entry point:** a `Help` QPushButton in a right-aligned row BELOW the QTabWidget, reachable from both tabs, with its own tooltip ("Open the help panel: what each control does, ...") (:225-239).
- **Dialog:** `_show_help` builds a modal child `QDialog(self)`, `setMinimumSize(520, 600)`, a read-only `QTextEdit.setHtml(HELP_HTML)`, an OK button wired to `accept()`, then `help_dlg.exec_()` (:948-975). The v1 AGENTS/gate record: modal CHILD dialogs are allowed; only the main dialog must stay modeless.
- **AA-match equivalent law already in writing:** setup_window.py:23-24 — "Modal .exec_()/static forms are allowed on CHILD dialogs only (QFileDialog/QMessageBox in later handler plans)."

### §3.2 Placement options for AA-match (feasibility, verified against the code)

| Option | Mechanism | Feasibility | T1b (offscreen) testability | Assessment |
|---|---|---|---|---|
| **A. Help button row below the tabs in SetupWindow (recommended)** | In `SetupWindow.__init__`, after `top.addWidget(self.tabs)` (setup_window.py:245), add a small HBox with `addStretch(1)` + `btn_help` + tooltip, connected to `_show_help` — the exact v1 shape. Both tabs inherit the affordance (the window owns the row). | Direct; no new module; SetupWindow already holds both tabs (241-245) | Button existence + dialog-class construction provable offscreen (SMOKE-09/11 pattern, QT_QPA_PLATFORM=offscreen — smoke_09_qt_probe.py:38). **`exec_()` itself is NOT smoke-driveable** — smoke-99 law (see §7); the drive is [HUMAN] | **Recommended.** Mirrors prior art; smallest surface; one button, one dialog |
| B. Per-tab help buttons | One button inside each tab page | Works, but duplicates affordance and reflows the Game tab button row (insert-before-stretch law, game_window.py:241-244) | same | More surface for no gain |
| C. Expanding section / dock | QToolBox or collapsible widget inside a tab | Feasible Qt-wise but no prior-art precedent in either codebase; changes tab layout | constructible offscreen | Reject: deviates from "simple UI" and prior art |
| D. QMessageBox.about-style | `QMessageBox.about(self, 'AA-match Help', text)` | One call, but rich-text control is weaker and **a static QMessageBox BLOCKS indefinitely under platform=offscreen** (the smoke-99 receipt, game_window.py:1344-1349 quote) | NOT even constructible in a smoke without the entry-gate dance | Reject: worse than the child QDialog |
| E. Wizard-panel Help button | A 4th panel button `[2, 'Help', 'cmd.get_wizard().<method>()']` | The PParse'd code resolves the live wizard instance (wizard_text.py:23-29); the method is cmd-tier and **wizard.py is NO-Qt by contract** (wizard.py:6) — it could only print console text or set a state field the 1 Hz tab poll reads (a new `get_status()` key = a status_events fingerprint change, status_text.py:427-455 contract) | Panel entries pure-testable in WSL | **Not recommended for criterion 1.** Adds cross-tier machinery; the 255-char clip (wizard_text.py:64-74) makes the panel a bad home for help prose; the help panel belongs in the window that hosts both tabs. Optionally a short panel pointer line could be added later |
| F. Help on the game tab only | New button in GameTab row | Feasible (insert before the stretch, game_window.py:241-244) but Setup-tab users have no affordance; criterion names BOTH surfaces | same as A | Subsumed by A |

### §3.3 Offscreen-testability split (T1b vs [HUMAN])

- **T1b-testable (headless, offscreen):** Help button exists with label/tooltip; the help-content builder (pure) returns non-empty sections containing pinned key phrases; the dialog class constructs (not opens) with parent wiring; endgame-modal-style offscreen ENTRY GATE pattern if the dialog is shown via a deferred arm (precedent: `_show_endgame_modal`'s `platformName()=='offscreen'` gate, game_window.py:1343-1349).
- **[HUMAN]-only:** actually opening the modal over the live viewer (exec_ blocks offscreen — smoke-99 law), scroll/copy behavior, tooltip hover feel, and the "learn to play without docs" verdict itself.

---

## §4 Content sourcing map (canonical wordings to REUSE, not restate)

**Single-home law risk (explicit):** every duplication of chemistry/scoring prose creates a drift surface against the DETECT-03 gate doc. Recommendation below.

| Help topic | Canonical existing wording | Home (file:line) | How help should use it |
|---|---|---|---|
| The 7 interaction types (short forms) | `_INTERACTION_TIPS` 1-sentence definitions | setup_window.py:397-415 | **Reuse verbatim** as the help panel's per-type bullets; ideally re-home the dict into the new pure module and have `_build_interactions` read it from there (one home, two consumers) — a Qt-tier lazy sibling import (setup_window.py:151-154 precedent) |
| Interaction-type numbers (cutoffs/angles) | docs/DETECTION_THRESHOLDS.md §2.2 rows (verified: Row 1 H-bond 4.0 Å/≥140° at :92-102; Row 2 salt bridge 5.5 Å group-center :104-112; Row 3 π-stacking 5.5 Å/30°/2.0 Å :114-126; Row 4 cation-π 6.0 Å + 2.0 Å :128-140; Row 5 hydrophobic 4.0 Å :142-154; Row 6 halogen 4.0 Å/165±30°/120±30° :156-174; Row 7 metal 3.0 Å :176-189) | docs/DETECTION_THRESHOLDS.md | Help MAY quote the numbers ONLY as approved (truthfulness rule, AGENTS.md). Safer: qualitative wording + "exact detection rules are documented in the plugin's Detection Thresholds doc" pointer. Any re-statement must be copy-checked against the doc in the DOCS-02 audit |
| **Salt-bridge vs H-bond independence (O1 lesson)** | The debug doc's `phase_9_help_recommendation` verbatim: "Salt bridge and H-bond are scored independently. For both on one contact, put an actual polar donor-H and acceptor heavy atom within 4.0 A and align D-H...A at H to at least 140 deg; a 5.5 A charge-group-center salt contact alone is not enough. Rotate the AA to aim a specific polar H, and where relevant choose a pair with a donor/acceptor role in the required direction." | .planning/debug/saltbridge-hbond-interplay.md:238 (O1 RESOLVED works-as-designed, STATE.md 2026-11-15 entry) | Adapt into a help "tips" item — this is the human-directed Phase-9 help content, recorded |
| Required set (what the label means) | `required_display` / `required_summary` vocabulary ('Required: 2 interactions: h_bond x1, pi_stacking x2'; 'any 1 interaction') | status_text.py:115-142; wizard_text.py:77-103 | Help explains the label USING this vocabulary (types named as `h_bond` etc. exactly as displayed) |
| Scoring semantics | "Binary per interaction: a required item counts as formed IFF >= 1 detector record of that type exists. Record COUNTS never inflate the score" (game_state.py:13-15); pass rule `CONFIRM_PASS_RULE='all'` (game_state.py:152); failed confirm "not recorded" + retry line (status_text.py:254-261) | game_state.py, status_text.py | Help paraphrase in player terms: each required interaction type is either formed or not; Confirm passes only when ALL required types are formed; a failed Confirm records nothing — retry freely |
| Difficulty axes | Tooltip row 16 + generator axes (grid_n 3..9, n_required_types 1..7, size class thirds — generator.py:70-86, 144-173) | generator.py | One help sentence per axis; keep the widget tooltip as-is |
| Mode semantics | `_MODE_CONTEXT` strings (setup_window.py:418-425) — verified against generator.derive_required (generator.py:337-443) | setup_window.py (context label) | Reuse verbatim; add the hydrophobic-unset-exclusion note already in the string |
| Drag gestures | NO existing prose. Mechanism: `cmd.button('left','shft','dgmv')`, `('left','ctsh','dgmz')` (depth_drag), `('right','shft','dgrt')` (drag_rotate_gesture); dgrt pivots at selection bbox center | wizard.py:327-338; disposition STATE.md Phase-8.3 Decisions (2026-10-19: shift-left translate + ctrl+shift-left depth + shift-right rotate) | **New text, worded to the drag model** (CONTEXT note 4). Must be written fresh; recommend human wording review at the checkpoint |
| Movement button | `'Toward ligand'` — one 2.5 Å step toward the ligand (TOWARD_STEP=2.5, wizard_core; acceleration off) | wizard_text.py:49-51; wizard.py:876-913; STATE.md 08.2-01 (2.5 Å, accel off) | Help: "Toward ligand nudges the selected amino acid 2.5 Å toward the ligand" |
| Selecting/clicking | `'Click an amino acid to select it.'` + `'Selected: slot %s (%s). Move/rotate it, then Confirm.'` | wizard_text.py:61, 273-274 | Reuse verbatim in the help "how to play" steps |
| Reset to Grid | Tooltip row 35 + `'Amino acids reset to grid positions (orientations kept).'` (status_text.py:298) | game_window.py:290-293; status_text.py:298 | Reuse; the "orientations kept" clause is load-bearing truth (wizard.py:1237-1244) |
| Done semantics | `'Game abandoned.'` + quick-004 applied default "Done = closing the board (no record); Done != Give-Up" | status_text.py:309-317; game_window.py:156-170; STATE.md quick-004 | Help must NOT promise an endgame summary on Done |
| Skip/Give Up | Row 58-59 strings | status_text.py:196-201 | Reuse verbatim in help |
| Setup refusals (player-register) | Thin-set strings: `"This %s only has %d molecule%s. Set 'Small molecules per level' to %d or less to play it."` / `"Only %d of the %d molecules in this %s fit the molecule size used in level %d. ..."` | generator.py:830-840 | Already player-worded; help need not restate |
| Win/endgame | Row 66 block | status_text.py:398-423 | Help can describe the endgame screen generically |

**Where canonical help text should live (recommendation):** a NEW pure module, e.g. `aamatch/help_text.py`, holding (i) the per-type help paragraphs (seeding from `_INTERACTION_TIPS`), (ii) the drag-gesture wording, (iii) a `help_lines()`/`help_html()` builder returning the panel content as plain data. Rationale: the per-surface pure-module precedent is exactly `setup_form.py` (04-02, "the setup window's pure glue" — status_text.py:13-15 documents the pattern) and `status_text.py` ("every string it can show is pinned here in WSL before any Qt wiring exists" — status_text.py:16-17). Pure = WSL-pinnable = drift-auditable at criterion 3 (DOCS-02).

---

## §5 Tier placement + test-tier plan (concrete)

### §5.1 Module placement

| Artifact | Tier | Registry action | Evidence |
|---|---|---|---|
| NEW `aamatch/help_text.py` (help content builder + per-type/gesture/flow strings) | PURE | **Add to `PURE_MODULES`** in tests/test_purity.py:99-103 (currently 19 entries) — the 01-08 law: "new pure modules must be added to PURE_MODULES ... to be gated" (STATE.md 01-08 bullet). Imports allowed: stdlib whitelist (test_purity.py:113-116) + pure siblings (may reuse nothing at first; could import nothing) | test_purity.py:99-116 |
| Help button + `_show_help` wrapper + dialog | QT (inside `setup_window.py`) | **No registry change** — setup_window.py is already in `SCANNED_MODULES` (test_wizard_source.py:51-59) and in the cmd-tier partition via that list | test_wizard_source.py:51-59, 917-959 |
| NEW standalone Qt help-dialog module (e.g. `help_dialog.py`) — ONLY if the planner splits it out | QT | **Must be added to `SCANNED_MODULES`** (one line) — the 03-04 growth protocol; the `TestCmdTierRegistration` partition test fails loudly for any unregistered new cmd-tier module (test_wizard_source.py:930-939) | test_wizard_source.py:21-22, 51-59, 917-959 |
| Tooltip edits in game_window.py / setup_window.py | QT | No registry change (already scanned) | as above |
| No new cmd-tier NON-UI module expected | — | If one appears, it goes in `NON_UI_CMD_CORE`, never both lists (disjointness test :951-959) | test_wizard_source.py:70-80 |

### §5.2 Test tiers

1. **WSL unit (python3.6, pure):** new `tests/test_help_text.py` pinning the help builder output — section headers present, per-type entries cover all 7 `INTERACTION_TYPES`, gesture wording mentions the three gestures, no banned-token substrings (`get_model`/`matrix_reset`/`get_object_ttt`), ASCII-safety for any line that could ever reach the wizard overlay (the panel law; help HTML is Qt-only so rich text is fine there).
2. **T1b offscreen smoke** (extend SMOKE-11 or new SMOKE-25): offscreen window construction → `btn_help` exists + tooltip non-empty; help dialog class constructs with the pure builder's content; **never call `exec_()`** (smoke-99). Optionally an offscreen ENTRY-GATE assert mirroring `_show_endgame_modal`'s `platformName()` check (game_window.py:1343-1349).
3. **[HUMAN] checkpoint:** §6.

### §5.3 What must NOT change

- No `sys.modules` stubs anywhere (standing purity contract).
- `aamatch/__init__.py` keeps zero module-level imports (help is reached via the window, not the menu).
- Pure modules never import Qt even inside function bodies (Gate A scans all scopes — test_purity.py:147-149).
- The two version gates and DETECTOR_VERSION are untouched (help is display-only).

---

## §6 [HUMAN] checkpoint proposal — "can learn/play without external docs"

Smallest fresh-session ritual (single Windows PyMOL 2.5.0 session, plugin-path install — one module identity, AGENTS.md gate 5; no external docs open):

1. **Discovery (Setup tab):** Plugins → AA-match. Without prompting: is a help affordance visible? Open it. Verify sections exist and read clearly: how to play (click → drag gestures → Confirm), the 7 interaction types, scoring, modes, buttons, files (save/import), tips (salt-bridge/H-bond independence). Close the panel.
2. **Tooltip sweep (Setup):** hover source radios, both spinboxes, the three mode radios, two interaction checkboxes (H-bond + salt bridge), and the 7 buttons — each shows a tooltip that matches behavior.
3. **Start blind:** press Start with defaults. From countdown + required label + panel + help alone, state what to do (self-report, no coaching).
4. **Gestures:** click an AA (recolor = selected per help). Perform shift+left-drag (move), ctrl+shift+left-drag (depth), shift+right-drag (rotate); press Toward ligand. Each does what the help said.
5. **Scoring:** pose a required interaction and Confirm → debrief lines match help's scoring description. Then blind-Confirm (no requirement formed) → "not passing yet ... not recorded" + retry line; retry works.
6. **Warnings:** Skip → Yes/No warning appears; Give Up → warning appears; endgame block + modal render. Reset to Grid → positions reset, orientation kept (visually verify a rotated AA stays rotated).
7. **Destructive/no-warning set (observe current reality):** Restart replaces the game silently; Import over a live game replaces silently; Cleanup (if no new confirm added) deletes the scene with only the after-info box. **Verdict required:** does the human accept the current warning coverage per criterion 1, or does Cleanup (minimum) need a confirm?
8. **Done semantics:** mid-game panel Done → timer freezes, 'Game abandoned.' line, no endgame modal — matches help's "Done = closing the board".
9. **Verdict:** record per-step PASS/FAIL + any wording amendments (the checkpoint may amend `Game abandoned.` per the STATE carry note).

Rationale for ordering: discovery → comprehension (help) → action (play) → guard rails (warnings) → exit paths. Steps 1-5 alone prove "learn the game from in-game help alone"; steps 6-8 prove the destructive-action clause.

---

## §7 Known traps (planner must respect)

1. **smoke-99 law:** a static/modal box under `QT_QPA_PLATFORM=offscreen` blocks a headless smoke indefinitely (receipt quoted at game_window.py:1344-1349; original 04-09 probe). A modal help dialog (`exec_()`, the v1 shape) is **[HUMAN]-only to open** — smokes verify construction + content only. If the planner wants a smoke to *arm* an open, it must copy the endgame-modal ENTRY GATE + deferred-singleShot pattern (game_window.py:602-603, 1343-1352).
2. **255-char wizard-panel clip:** panel/prompt lines clip at 255 chars, never crash (wizard_text.py:64-74; Word.h:24,26). Help prose cannot live in the wizard panel; also any *short* pointer line added there must stay ASCII (no degree signs — wizard_text.py:29-30) and pass the panel-contract tests.
3. **Superseded keyboard text:** ALL keyboard direction channels are deleted (wizard.py:105-108, 1333-1341; STATE 08.3-16 record-repairs: "no shipped string ever carried this note; the movement input is mouse-drag"). Help must NEVER mention arrows/wasd/rotate-keys; it must word the drag model (CONTEXT note 4). Note the prompt line "Move/rotate it, then Confirm." (wizard_text.py:273) is generic and predates the pivot — if help restates it, pair it with the gesture sentence.
4. **D1 is CLOSED — don't re-describe the old bug:** quick-004 (2026-11-16) shipped the abandon-stop Done path (STATE.md:14 quick-004 row; game_window.py:606-682). Help says "Done = closing the board (no record)"; it must NOT promise an endgame summary on Done (Done ≠ Give-Up). A `'Game abandoned.'` re-word is a pending candidate (STATE carry) — the checkpoint can amend it.
5. **O1 is RESOLVED (works as designed) — teach it, don't "fix" it:** salt bridge and H-bond score independently; a 5.5 Å charge-group-center contact alone is NOT an H-bond (debug doc :238). Help should carry the recorded recommendation; NO detector change, NO DETECTOR_VERSION event.
6. **Drift / single-home:** help prose that restates threshold numbers or chemistry duplicates the DETECT-03 gate doc and `_INTERACTION_TIPS` — prefer re-homing `_INTERACTION_TIPS` into the pure help module and referencing (not re-deriving) numbers; DOCS-02 (criterion 3) will audit every user-facing string against behavior.
7. **Raw-token grep gate:** `test_wizard_source.py:902-914` substring-scans SCANNED_MODULES files for `get_model` / `matrix_reset` / `get_object_ttt` — a help-HTML string constant living in setup_window.py/game_window.py must avoid these tokens **even as prose**. (The helper-visual scan `find_visual_calls` is AST/Call-based, so prose naming `cmd.distance` is safe there — test_wizard_source.py:12-19.)
8. **Modal-child law:** modal `.exec_()` is legal only on CHILD dialogs (setup_window.py:23-24); the main SetupWindow stays show()/raise_() modeless (setup_window.py:14-16, 69-83). A help dialog must parent to the window (`QDialog(self)` / `self.window()` from the tab) and use WindowStaysOnTopHint if it must float above the OpenGL viewer (the v1 Bug-B pattern, game_window.py:1327-1329).
9. **Recorded no-warning decisions:** Restart (06-08 D9), mid-game Import (07-07 RD2), Start-no-dialog (04-13) are RECORDED — changing them is a human decision, not a Phase-9 unilateral fix (see §2d table). Cleanup is the un-covered destructive action.
10. **D7 line-placement analog:** any new handler-logged line on the Game tab must log AFTER `start_countdown` arms (the arm clears the info box — game_window.py:379-380; restart D7 law). Relevant if help adds a one-time "first-run tip" line to the log.
11. **Module identity:** any new sibling import inside Qt handlers stays lazy + relative (setup_window.py:38-43 contract 4); panel button codes never carry a module name (wizard_text.py:23-29) — irrelevant unless option E is taken.
12. **Naming collision law:** Game-tab button attributes are distinct on purpose (`btn_reset` Setup vs `btn_reset_grid` Game, game_window.py:187-189); a new `btn_help` collides with nothing (verified: no `btn_help` in either module).

---

## §8 Planning inputs — facts a planner MUST respect

1. **No help surface exists today** — zero Help UI in setup_window.py/game_window.py (grep-verified); the panel half of criterion 1 is greenfield, while the tooltip half is ~90% covered (§1, §2a/b).
2. **The biggest content gap is the drag gestures** — the three shipped gestures (wizard.py:335-337) have zero player-facing documentation anywhere; STATE carries a standing Phase-9 note that help must be worded to the drag model (§2c, §7.3).
3. **The borrowable pattern is v1's Help button + modal child QDialog + HELP_HTML** (tmp/bioCHEMeleon/biochemeleon/__init__.py:225-239, 948-975), sanctioned by ROADMAP.md:9; AA-match's own modal-child law is setup_window.py:23-24. Recommended placement: one Help row below the QTabWidget in SetupWindow (§3.2 option A).
4. **Content should live in a NEW pure module** (e.g. `help_text.py`) registered in `PURE_MODULES` (test_purity.py:99-103) following the setup_form/status_text per-surface precedent; WSL tests pin the content; Qt shells stay dumb renderers (§4, §5.1).
5. **Registry deltas are one-line each:** new pure module → PURE_MODULES; a new Qt UI module (if split out) → SCANNED_MODULES; keeping the dialog inside setup_window.py needs NO registry change (§5.1).
6. **Modal help is [HUMAN]-only to open** (smoke-99); smokes prove construction + pinned content; the endgame-modal entry-gate pattern is the precedent if arming is ever needed (§3.3, §7.1).
7. **Warning coverage today:** Skip/Give-Up have Yes/No confirmations (status_text.py:196-201); Cleanup/Start/Restart/Import-over-live-game/Done/Setup-Load/upload-re-ingest do NOT, and three of those no-warning states are recorded decisions (06-08 D9, 07-07 RD2, 04-13). Cleanup is the one destructive action with NO recorded decision and no guard — the likely minimum warning addition, but it is a behavior change needing human approval (§2d).
8. **D1 closed / O1 resolved:** help text must describe Done = abandon ("closing the board", no record — quick-004) and must teach salt-bridge/H-bond independence per the recorded O1 recommendation (debug doc :238); neither implies any detector/engine work in Phase 9 (§7.4-5).
9. **Existing accurate explainers to reuse verbatim:** `_INTERACTION_TIPS`, `_MODE_CONTEXT`, the Skip/Give-Up warnings, required_display vocabulary, Reset-orientations-kept wording, player-register thin-set refusals (§4 table) — reuse over restatement to control drift.
10. **Criterion 1 is [HUMAN]; its proof shape is §6's ritual** — discovery → tooltip sweep → blind start → gestures → scoring → warnings → Done; the checkpoint doubles as the DOCS-02 wording-amendment pass for the help surface.

---

## Sources

### Primary (file-verified, HIGH confidence)
- `aamatch/setup_window.py`, `aamatch/game_window.py`, `aamatch/wizard_text.py`, `aamatch/status_text.py`, `aamatch/wizard.py`, `aamatch/gamestart.py`, `aamatch/engine.py`, `aamatch/generator.py`, `aamatch/game_state.py`, `aamatch/setup_state.py`, `aamatch/capability.py`, `aamatch/checkpoint.py` — read in full or in relevant sections this session; all file:line citations above are from these reads.
- `tests/test_purity.py`, `tests/test_wizard_source.py`, `tests/test_wizard_text.py`, `tests/test_status_text.py`, `tests/test_setup_form.py` — registry + pin verification.
- `smoke/smoke_09_qt_probe.py`, `smoke/smoke_11_window.py`, `smoke/smoke_16_tab.py` — T1b pattern + label pins.
- `tmp/bioCHEMeleon/biochemeleon/__init__.py` (git-ignored prior art) — help pattern, read this session.
- `spec.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/FEATURES.md`, `.planning/research/PITFALLS.md` — requirement/criterion text.
- `.planning/STATE.md` (quick-004 + 08.3-16 entries), `.planning/phases/08.3-drag-movement-pivot/08.3-16-SUMMARY.md`, `.planning/debug/saltbridge-hbond-interplay.md` — D1/O1 provenance.

### Confidence
- Inventory (§1): **HIGH** — every string quoted from a direct read; pinning claims grep-verified.
- Gap analysis (§2): **HIGH** on existence/absence claims (negative greps), **MEDIUM** on the "sufficient to play" judgment (human criterion).
- Placement feasibility (§3): **HIGH** for option A (prior-art code + AA-match modal-child law both read); **MEDIUM** for option E (cross-tier signal mechanism not prototyped).
- Content sourcing (§4): **HIGH** (all wordings quoted).
- Tier plan (§5): **HIGH** (registry law quoted).
- Checkpoint design (§6): **MEDIUM** (proposal; human ritual shape precedent from 06-10/07-12/08.3-16 records).

### UNVERIFIED items (with the probe that would settle each)
1. Exact behavior of a modeless (`show()`, non-`exec_()`) help dialog under offscreen for T1b (likely constructible, but unproven in this repo). Probe: a one-off smoke constructing + `show()` + `processEvents()` + `close()` the dialog under offscreen. *(Resolved during verification: the window-title pinning question was settled — no smoke asserts `windowTitle`; row 1 updated.)*
