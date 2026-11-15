# Phase 9 Research — DOCS AUDIT ASPECT (README fill-in + final documentation audit)

**Phase:** 9 — Help, Docs & Release Audit
**Aspect:** 2 of 3 — the docs audit (DOCS-01, DOCS-02; ROADMAP criteria 2 & 3)
**Researched:** 2026-11-16 (WSL; read-only session — no PyMOL, no test suite run)
**Researcher scope:** README current-state map, shipped-reality data pack (Usage / Project Structure / demo table), drift sweep, DOCS-02 audit methodology, existing data-integrity test coverage, README authoring constraints. NOT in scope: HELP-01 help-panel design, perf budgets (other aspects).
**Confidence:** HIGH for every claim below — each is cited to a file:line or JSON path I personally read this session. Items I could not verify are marked **UNVERIFIED** with the probe that would settle them.

---

## §1 README current-state map

File: `README.md` (repo **root**, 64 lines — users see it first; `docs/` contains only `DATA_SOURCES.md` and `DETECTION_THRESHOLDS.md`, verified by `ls docs/`).

### §1.1 Section inventory (every heading, in order)

| Lines | Heading | State |
|---|---|---|
| 1–4 | (blockquote warning — not a heading) | REAL — must be retained |
| 6 | `# AA-match` | REAL |
| 8 | (prose: "A matching game of small molecule and biomolecular interactions…") | REAL |
| 10 | (audience prose: "For students and educators…") | REAL |
| 14 | `## Requirements` | REAL (PyMOL 2.5.0 / PyQt5 bundled / numpy bundled + no-external-deps note, lines 16–20) |
| 22 | `## Install` | REAL CONTENT, but partially **unverified/stale** (see §3) |
| 30 | `## Usage` | **PLACEHOLDER** — body is exactly `> TBD` (line 32) |
| 34 | `## Demo Molecules set` | **PLACEHOLDER** — header row only (line 36: `\| Tier \| Category \| Source \| ID(s) \| Needs network? \|`) + 9 empty rows (lines 38–46: Easy ×3, Hard ×3, Challenge ×1, Very challenging ×2 — **no dev-set row**) + line 48: "Full attribution in `DATA_SOURCES.md`." |
| 50 | `## Project Structure` | **PLACEHOLDER** — body is a fenced code block containing exactly `#TBD` (lines 52–54) |
| 56 | `## License` | REAL — "BSD 3-Clause — see [LICENSE](LICENSE)." (LICENSE exists at repo root, verified by ls) |
| 60 | `## Acknowledgements` | **PLACEHOLDER** — "Demo data courtesy of `TBD`" (line 62) |

### §1.2 The vibe-coding warning — VERBATIM (DOCS-01 requires retention)

`README.md:1-4`, byte-for-byte (two-space line-continuations inside the blockquote):

```
> This is a vibe-coding project. While the human attempt to verify the source of all 
> contents, if you find any issues please contact me.
> 
> !! Under Development !!
```

Notes for the planner: (a) lines 1 and 3 end with a trailing space (markdown hard-break style) — retention should be byte-level, not retyped; (b) the `!! Under Development !!` line (line 4) is part of the same blockquote. DOCS-01 mandates "the vibe-coding warning is retained"; whether the under-development banner stays for the release is a **planner/human decision** — flag it, do not silently drop or keep it.

### §1.3 What README currently claims (right or wrong)

1. Requirements claim: "PyMOL 2.5.0 (anaconda build or equivalent)" (line 16) — matches the recorded env (`.planning/phases/01-bootstrap-pure-foundation/windows-env-versions.md` is the recorded build; PyMOL 2.5.0 is the standing target, AGENTS.md env section).
2. "PyQt5 (bundled with PyMOL's Qt GUI — no extra install)" / "numpy (PyMOL build dependency — no extra install)" (lines 17–18) — consistent with the dependency policy (AGENTS.md Dependencies section).
3. Install claims (lines 24–28):
   - "Install via PyMOL's **Plugin Manager** (universal across Windows/Linux/macOS)"
   - "1. In PyMOL: `Plugin → Plugin Manager → Install New Plugin`"
   - "2. Point the file picker at the `AA-match/` package directory"
   - "3. The plugin registers a **AA-match** item under the Plugins menu"
4. "Full attribution in `DATA_SOURCES.md`." (line 48) — the file actually lives at `docs/DATA_SOURCES.md`; as written the relative reference is wrong from the repo root.
5. Menu-name truth check: the **AA-match** menu label is REAL — `addmenuitemqt('AA-match', run_plugin_gui)` at `aamatch/__init__.py:26`; entry point `run_plugin_gui` → `setup_window.open_window()` (`aamatch/__init__.py:29-39`).

### §1.4 Audit scope-boundary ruling (proposal for DOCS-02)

DOCS-02 names four user-facing doc surfaces: README, in-game help, tooltips, DATA_SOURCES.md. Ruling I propose (planner may adopt):

| Document | Audience | In DOCS-02 scope? | Rationale |
|---|---|---|---|
| `README.md` | users | **YES** (explicitly named) | DOCS-02 + DOCS-01 |
| In-game help text (wizard panel + prompt lines) | users | **YES** (explicitly named) | built by `aamatch/wizard_text.py` (pure, lines 1–61) and logged via `aamatch/status_text.py` |
| Qt tooltips (32 `setToolTip` sites) | users | **YES** (explicitly named) | `aamatch/setup_window.py` + `aamatch/game_window.py` (grep-verified: 32 sites) |
| `docs/DATA_SOURCES.md` | users + gate record | **YES** (explicitly named) | HELP-02 doc; §2 rows machine-reproducible (its own header, lines 9–16) |
| `docs/DETECTION_THRESHOLDS.md` | developers (DETECT-03 [GATE] transcription source) | **NO — cited-only appendix** | It is the *upstream* approval record that `aamatch/thresholds.py` transcribes from (its header, lines 17–30); threshold transcription is already mechanically pinned by `tests/test_thresholds.py`. Recommend the 09-AUDIT add an optional consistency row (doc values == thresholds constants), not a full audit. |
| `spec.md` | original requirements contract (dev + human) | **NO** | It is the SOURCE the code is verified against, not a doc that must match code. (Its user-visible claims — 7 buttons spec.md:21, Game-status tab spec.md:33 — are already reflected in code; re-auditing spec would audit history.) |
| `AGENTS.md` | agents/developers | **NO** | Not user-facing. |

---

## §2 Shipped-reality data pack (for the three DOCS-01 sections)

### §2.1 USAGE — verified flow steps, each cited

**Install & launch**
- Plugin registers menu item **AA-match**: `aamatch/__init__.py:26` (`addmenuitemqt('AA-match', run_plugin_gui)`). Clicking it opens the **modeless** Qt window titled **'AA-match Setup'** (`aamatch/setup_window.py:148`), with two tabs: **'Setup'** and **'Game status'** (`setup_window.py:241-244`).
- Install methods (see §3 drift): plugin-path (repo root on PyMOL's plugin path) is the ONLY human-verified install (`01-09-SUMMARY.md:17,26,38`; "never ALSO copy-install — two module objects" at `:27,40,122`).

**Setup form (the 'Setup' tab)**
- Molecule source group, two radios: **'Bundled demo set'** / **'Upload my molecules...'** (`setup_window.py:273-277`); stacked pages keep both pages' values (`setup_window.py:262-322`).
- Demo dropdown: filled from the bundled `aamatch/data/MANIFEST.json` via `setup_form.manifest_sets_grouped` — groups by tier in `TIER_ORDER = ('easy','hard','challenge','very_challenging')` with a separator BETWEEN groups; row labels are `'title (tier)'` with `set_id` as userData (`setup_window.py:325-361`; `aamatch/setup_form.py:142-162`).
- Upload page: Browse opens `getOpenFileName(self, 'Upload molecule file', '', 'Molecule files (*.sdf *.mol2);;All Files (*)')` (`setup_window.py:816-818`). Ingestion pipeline (all fail-closed, `setup_window.py:822-833`): `game_file.read_upload_source` (extension whitelist `.sdf`/`.mol2` only — "unsupported upload format %r (expected .sdf or .mol2)", PDB included in the refusal, `game_file.py:359-385`) → split (`split_sdf_records` at `$$$$` / `split_mol2_segments` at `@<TRIPOS>MOLECULE`, `game_file.py:268-326`) → `check_upload_supply` cap **50** (`game_file.py:87 UPLOAD_MAX_RECORDS = 50`; refusal names the cap, `:350-355`) → `upload.prepare_uploaded_set` per-record temp discipline (`upload.py:72-172`).
- **MOL2 reality (fail-closed):** multi-segment MOL2 refused unconditionally (`upload.py:114-118`, Decision 14); single-molecule MOL2 is refused **on this build** because `read_mol2str` is unexported (`upload.py:47-53, 135-141`) — docs must present SDF as the format that works and MOL2 as refused-with-a-clear-message here.
- Uploads are **session-only**: the `self._uploaded` slot is "Never restored from setup files (uploads are not stored there -- the sha256 lets Load warn when it moved)" (`setup_window.py:175-179`); a new upload replaces the slot (single slot v1, `setup_window.py:835-842`).
- Game size spinboxes: 'Small molecules per level' (default 2, range 1..10) and difficulty (default 3, range 1..10), ranges imported from the frozen constants (`setup_window.py:439-454`; `aamatch/setup_state.py:46,50`).
- Required-interactions group: 3 radios — 'Exclusive (any allowed)' / 'Block-exclusive (checked set)' / 'Unset (random)' with context labels ("The game accepts ANY of the checked interactions" / "The player must form EXACTLY the checked interactions" / "The game randomizes the required set from the checked types (hydrophobic excluded from random picks).") (`setup_window.py:418-425, 460-485`); 7 interaction checkboxes in canonical `INTERACTION_TYPES` order, each with a game-terms tooltip (`setup_window.py:383-415`; `setup_state.py:40-41`).
- 7-button row in spec order: **Reset / Randomize / Save Setup / Load Setup / Generate and export / Cleanup model / Start** (`setup_window.py:202-233`; `spec.md:21`).

**Share flow**
- Save/Load Setup → files with extension **`.aam.setup.json`** (filter + auto-append, `setup_window.py:738, 758-759, 772`); versioned container kind `'setup'`, validate-on-save and validate-on-load (`aamatch/persistence.py:199-219`).
- Generate and export → **`.aamatch.json`** game file, default name `game.aamatch.json` (`setup_window.py:940-941`); the game file is ONE JSON container kind `'game'` embedding the FULL generator payload verbatim plus base64 `ligand_files` for uploaded molecules only (`aamatch/game_file.py:15-34, 81-117`; `GAME_VERSION = 1` at `game_file.py:81`).
- Import (Game tab) is the **ONE load surface for BOTH kinds**: header-exact `persistence.peek_kind` dispatch — `.aamatch.json` → fresh game; `.aamz` → resume (`persistence.py:133-182` "ZIP-AWARE... never extension guesswork"; `game_window.py:1104-1134`, dispatch at `:1123-1134`).

**Game flow (Start → play → endgame)**
- Start → switches to the Game status tab → **cancellable 3-2-1 countdown** → GO pushes the wizard (`game_window.py:325-331`; `aamatch/gamestart.py:356-381`; `spec.md:33-34`).
- Game status tab widgets: elapsed timer label, required-interactions label, read-only rolling info box, and the button row: **Hint, Confirm, Skip / Give Up (dropdown), Restart, Reset, Save, Import** (`game_window.py:179-323`).
- Play (3D viewer): ligand fixed; click an AA to select — prompt "Click an amino acid to select it." (`aamatch/wizard_text.py:61`); when selected: "Selected: slot %s (%s). Move/rotate it, then Confirm." (`wizard_text.py:273`).
- **Movement = mouse drag (2026-10-18 pivot)**: shift-left-drag = view-plane translate (`'dgmv'`), ctrl+shift-left = depth (`'dgmz'`), shift-right-drag = rotate (`'dgrt'`) — `aamatch/wizard.py:328-337` (`cmd.button('left','shft','dgmv')`, `('left','ctsh','dgmz')`, `('right','shft','dgrt')`); ALL keyboard direction keys are deleted (`wizard.py:19-21, 107`: "human decision -- ALL keyboard direction keys are gone; mouse-drag becomes THE movement"). Panel movement list = **'Toward ligand' only** under the constant `'Movement:'` header (2.5 Å step, `wizard_text.py:37-51`; `aamatch/wizard_core.py:70 TOWARD_STEP = 2.5`).
- Panel buttons: Toward ligand / Confirm / Reset to Grid / Done (`wizard_text.py:49-59`).
- **Confirm = pass gate (Phase 8.1)**: `CONFIRM_PASS_RULE = 'all'` — advances only when EVERY required interaction is formed (`aamatch/game_state.py:152-168`; enforcement between detect and record at `aamatch/wizard.py:1058-1069`; wrapper contract `wizard.py:986-998`; Game-tab tooltip "…advances only when all required interactions are formed." `game_window.py:246-248`). A failed Confirm records nothing and renders a Formed/Missing debrief (`wizard.py:999-1005` area; `status_text.confirm_failed_lines` `aamatch/status_text.py:243`).
- Score semantics: fraction of required interactions formed, binary per item; `'any'` mode is binary (`game_state.py:9-26`); scores render with 2 decimals (`status_text.py:380-424`; `wizard_text.py:31-35`).
- Skip Molecule / Give Up: both ask the spec-required confirmation warning (`game_window.py:250-274`; `spec.md:42-44`); skip stores the partial score and moves on (`aamatch/engine.py:607-625`).
- Advancement: molecule → molecule (`engine.advance_molecule` `engine.py:626`), level → level with re-materialization (`engine.advance_level` `:654`), last level's last molecule completes the game (`game_window.py:841-856`).
- **Endgame**: headline + per-level scores + total + time + molecules + skips/give-ups block rendered BOTH in the info box and a modal (`status_text.endgame_lines` `status_text.py:365-424`: "You win! All %d level(s) finished in %s." / "Game over -- gave up at level %d, molecule %d of %d."; modal `_show_endgame_modal` `game_window.py:42-86`).
- **Done button = abandon-stop** (QUICK-004, 2026-11-16): mid-game Done stops the clock, marks the game 'abandoned', logs ONE 'Game abandoned.', NO record/modal (`.planning/STATE.md` line 14, latest entry; `status_text.game_abandoned_line` `status_text.py:309`). Phase-9 carry: help wording **"Done = closing the board"**; 'Game abandoned.' re-word candidate (STATE.md line 15).
- Hint: "Highlight the amino acids that could still form a required interaction (carbon recolor only)." (`game_window.py:233-236`; dispatch `_hint_now` `:699-706`).
- Reset (Game tab): "Place all amino acids back to their grid positions; orientations are kept." (`game_window.py:290-293`); Restart: "Replay the stored initial state into a fresh game (countdown, timer from zero, scores cleared)." (`:280-283`).
- Cleanup model (Setup tab): cancels any pending countdown FIRST, then pop-cleanup; the deleted-object count is always surfaced (0 is a legal no-op) (`setup_window.py:907-922`); Cleanup never touches non-game objects (SMOKE-21 field-test proof, `smoke/smoke_21_demo_cleanup.py:1-7`).

**Checkpoints**
- Save → ONE zip **`.aamz`** with two fixed members: `game.pse` (session bytes) + `state.json` (sidecar container) (`aamatch/checkpoint.py:19-24`; default name 'game.aamz' with auto-append, `game_window.py:1042-1047`); checkpoint has its own refuse-newer gate `CHECKPOINT_VERSION = 1` (`checkpoint.py:91`).
- Resume: Import dispatches kind `'checkpoint'` → `_resume_checkpoint_from` (`game_window.py:1123-1125`; `aamatch/gamestart.py:590-610`), timer rebased from `elapsed_at_save` (`checkpoint.py:40-42`).

### §2.2 PROJECT STRUCTURE — module inventory with tiers

Tiers cross-checked against `tests/test_purity.py:99-116` (`PURE_MODULES`, `FORBIDDEN`, `ALLOWED_STDLIB`) and AGENTS.md purity contract. 28 modules total (verified by `ls aamatch/*.py`).

**PURE (19 — all in `PURE_MODULES`, no pymol/Qt/numpy anywhere):**

| Module | One-line role | Key proof of role |
|---|---|---|
| `setup_state` | single source of truth for the 7-field setup schema (enums, clamps, DEFAULTS, validate/randomize) | `setup_state.py:1-62` |
| `level_spec` | versioned level-spec container; `DETECTOR_VERSION = "det-1"` exact-match gate, `LEVEL_SPEC_VERSION = 1` | `level_spec.py:60-61` |
| `persistence` | THE versioned-container core (`{"magic":"AAMATCH","version":1,...}`) + atomic JSON I/O + zip-aware `peek_kind` | `persistence.py:36-39, 93-130, 133-182` |
| `backup` | snapshot/restore/discard/verify_intact policy (PyMOL open-source has NO undo) | `backup.py:1-16` |
| `paths` | WSL→Windows path guard + package-data resolution (never `os.getcwd()`) | `paths.py:1-25` |
| `vec3` | vector math | listed `test_purity.py:102` |
| `spatial` | cell-list candidate pairs (+ tests-only brute-force oracle) | listed `test_purity.py:100`; `tests/test_code_audit.py` audit 2 |
| `manifest` | parse/gate MANIFEST.json + enumerate entries | `manifest.py:1-34` |
| `capability` | THE AA/ligand atom-typing home (support predicates, profiles) | `setup_window.py` imports `capability.ligand_profile` (`upload.py:155`) |
| `thresholds` | DETECT-03 approved threshold constants | `docs/DETECTION_THRESHOLDS.md:17-20` binds it |
| `detector` | 7-type geometric interaction detection | `tests/test_code_audit.py` audit 1/3 |
| `generator` | level-spec generation (buckets, solvability) | `engine.new_game` → `generator.generate` (`engine.py:352-356`) |
| `game_state` | scoring + runtime state; ONE home of `CONFIRM_PASS_RULE` | `game_state.py:31, 152` |
| `wizard_core` | TOWARD_STEP 2.5, colors, view/drag math | `wizard_core.py:68-70` |
| `wizard_text` | pure panel/prompt/result text builders | `wizard_text.py:1-11` |
| `setup_form` | pure setup-form build/collect + tier-grouped dropdown rows | `setup_form.py:54-59, 124-162` |
| `game_file` | shareable-game container + upload split/supply/read | `game_file.py:1-13` |
| `status_text` | pure status-log + endgame text builders | `status_text.py:355-424` |
| `checkpoint` | `.aamz` sidecar schema + zip I/O | `checkpoint.py:1-24` |

**CMD TIER (5 — import `from pymol import cmd`; must NEVER join PURE_MODULES):** `engine` (game ops 1..18: new_game/materialize/detect/record/skip/advance/give_up/endgame_summary… `engine.py:135-781`), `geometry` (atom extraction, bounding sphere), `placement` (materialize/grid bake), `upload` (cmd-tier upload bridge; `upload.py:1-8` states the law), `gamestart` (start/import/checkpoint seams; `gamestart.py:356, 440, 590, 769`).

**QT TIER (2 — `from pymol.Qt import ...` at module level is legal):** `setup_window` (`setup_window.py:1-8`), `game_window` (`game_window.py:3`).

**Entry point:** `__init__.py` — ZERO module-level imports; metadata block FIRST (`__init__.py:1-13`); `__version__ = '0.1.0'` (`__init__.py:13`); menu registration (`:16-26`).

**Supporting trees:** `tests/` — 28 test files + `__init__.py` (verified by ls); `smoke/` — `run_smoke.sh` + `smoke_01..24` (roster below); `scripts/build_demos.py` + `scripts/demo_specs/*.json` (10 specs, verified by ls); data at `aamatch/data/MANIFEST.json` + `aamatch/data/ligands/*.sdf` (18 files, verified by ls).

**Smoke roster (one line each, from each file's docstring, first lines read this session):**
01 plugin skeleton loads under real Windows PyMOL (loader path + env record); 02 every-manifest-id load with count asserts; 03 count-asserted generate + materialize; 04 count-asserted E2E game loop (place/detect/score/reset/cleanup); 05 DETECT-05 perf budget + detector-version stamp gate; 06 movement-model spike; 07 E2E wizard gameplay loop; 08 starter path (countdown/start sequence); 09 offscreen-Qt widget-construction probe; 10 uploaded-flow ligand_content plumbing; 11 setup window shell; 12 upload extraction bridge E2E (incl. MOL2 fail-closed); 13 Qt timer + tab mechanics probe; 14 status-surface read path + wiring; 15 engine lifecycle ops; 16 Game-tab lifecycle controls + Save + one-button Import dispatch; 17 `.pse` round-trip gate probe; 18 checkpoint SAVE half E2E; 19 Import wiring + restart payload-direct branch; 20 checkpoint E2E save→quit→relaunch→load (two-run); 21 messy-scene cleanup field test; 22 detector-coverage oracle over curated molecules (Cl/I/Fe); 23 movement battery (8.2/8.3 rework); 24 drag-movement battery (8.3 pivot).

### §2.3 DEMO-SET TABLE — actual manifest data (parsed this session)

Source of truth: `aamatch/data/MANIFEST.json` — top shape `{"kind":"manifest","magic":"AAMATCH","version":1,"data":{"manifest_version":1,"sets":[...]}}`. **10 sets / 18 entries.** Tier census: easy ×4 (incl. the dev fixture), hard ×3, challenge ×1, very_challenging ×2. README's 9 empty rows have the right tier skeleton for the curated sets but **no dev-set row** and no data.

Rows the README needs (every value read from the manifest this session; `file` keys are package-relative under `aamatch/data/`):

| set_id | tier | title | entry_id | file | heavy | charge | size | halogen | metal |
|---|---|---|---|---|---|---|---|---|---|
| demo-easy-1 | easy | Everyday organics | aspirin | ligands/demo-easy-1-aspirin.sdf | 13 | −1 | small | no | no |
| demo-easy-1 | easy | | benzoic_acid | ligands/demo-easy-1-benzoic_acid.sdf | 9 | −1 | small | no | no |
| demo-easy-2 | easy | Metabolites & ions | citric_acid | ligands/demo-easy-2-citric_acid.sdf | 13 | −3 | small | no | no |
| demo-easy-2 | easy | | acetate | ligands/demo-easy-2-acetate.sdf | 4 | −1 | small | no | no |
| demo-easy-3 | easy | Caffeine | caffeine | ligands/demo-easy-3-caffeine.sdf | 14 | 0 | small | no | no |
| demo-hard-1 | hard | Trypsin classics | benzamidine | ligands/demo-hard-1-benzamidine.sdf | 9 | +1 | small | no | no |
| demo-hard-1 | hard | | guanidinium | ligands/demo-hard-1-guanidinium.sdf | 4 | +1 | small | no | no |
| demo-hard-2 | hard | Charged messengers | glutamic_acid | ligands/demo-hard-2-glutamic_acid.sdf | 10 | −1 | small | no | no |
| demo-hard-2 | hard | | acetylcholine | ligands/demo-hard-2-acetylcholine.sdf | 10 | +1 | small | no | no |
| demo-hard-3 | hard | Cofactors | atp | ligands/demo-hard-3-atp.sdf | 31 | 0 | medium | no | no |
| demo-hard-3 | hard | | nad | ligands/demo-hard-3-nad.sdf | 44 | 0 | medium | no | no |
| demo-challenge-1 | challenge | Halogen & alkaloids | chloramphenicol | ligands/demo-challenge-1-chloramphenicol.sdf | 20 | 0 | small | **yes (Cl)** | no |
| demo-challenge-1 | challenge | | quinine | ligands/demo-challenge-1-quinine.sdf | 24 | +1 | small | no | no |
| demo-veryhard-1 | very_challenging | Big & iodinated | folic_acid | ligands/demo-veryhard-1-folic_acid.sdf | 32 | −2 | medium | no | no |
| demo-veryhard-1 | very_challenging | | thyroxine | ligands/demo-veryhard-1-thyroxine.sdf | 24 | 0 | small | **yes (I)** | no |
| demo-veryhard-2 | very_challenging | Metalloporphyrin | heme | ligands/demo-veryhard-2-heme.sdf | 43 | −4 | medium | no | **yes (Fe)** |
| demo-dev-1 | easy | Phase-2 development set | benzamide | ligands/benzamide.sdf | 9 | 0 | small | no | no |
| demo-dev-1 | easy | | acetate | ligands/acetate.sdf | 4 | −1 | small | no | no |

Caveats for the README author:
- All entries are single-record SDF (`states_expected: 1` ∀, verified in the parse; single-record law `docs/DATA_SOURCES.md:228-233`).
- **Needs network? → No** for every set: curated files are bundled (fetched 2026-09-26, re-fetches 2026-10-04/05 per DATA_SOURCES); dev set is script-built (DATA_SOURCES.md:206-222).
- Set-level licenses (match MANIFEST verbatim, DATA_SOURCES §2 headers): every curated set `Public domain (NCBI PubChem)` EXCEPT demo-veryhard-2 `CC0 1.0 (wwPDB)`; dev set license `''` placeholder-by-design (DATA_SOURCES.md:211-214).
- Dropdown placement nuance: `manifest_sets_grouped` groups by TIER, so **demo-dev-1 lands INSIDE the Easy group** (sorted by set_id, i.e. first), not "last" — DATA_SOURCES.md:55 "development set last" describes the DOC's section order, while the dropdown reality is "under Easy per approved Decision 3" (DATA_SOURCES.md:206-210). The README table should mark demo-dev-1 as a development fixture to avoid implying curated content.

**DATA_SOURCES cross-check result (HELP-02 coverage):** I ran a loop over all 18 `aamatch/data/ligands/*.sdf` basenames grepping `docs/DATA_SOURCES.md` — **18/18 OK, zero MISS**. HELP-02's "every bundled file appears" claim is TRUE today. (File-level coverage only; per-row column-by-column truth is the 09 audit's job.)

---

## §3 Drift / discrepancy sweep

Method: grep + read. Searched README.md, docs/, spec.md for stale movement/score/extension/version claims.

| # | Claim | Location | Current truth | Code/record citation | Verdict |
|---|---|---|---|---|---|
| 1 | "Point the file picker at the `AA-match/` package directory" (install step 2) | README.md:27 | PyMOL's dialog accepts `*.py` + archives; a DIRECTORY install points at the package's **`__init__.py`** ("to install a directory, point to its __init__.py file") | `.planning/phases/01-bootstrap-pure-foundation/01-RESEARCH-plugin-install.md:17-19` (citing `installation.py:299-308`, `legacysupport.py:60-66`) | **STALE/WRONG** — rewrite step |
| 2 | "In PyMOL: `Plugin → Plugin Manager → Install New Plugin`" — button label | README.md:26 | The wiring is `b_local` → installplugin (`managergui_qt.py:45, 301-304`) but the visible label lives in a runtime-loaded `.ui` form NOT in the source tree | 01-RESEARCH-plugin-install.md:337 (U3) | **UNVERIFIED label** — needs the human checkpoint or neutral wording ("Install New Plugin / Install from local file") |
| 3 | (implicit) Plugin-Manager install as THE method | README.md:24-28 | The only HUMAN-VERIFIED install is **plugin-path** (repo root added to PyMOL's plugin path); Plugin-Manager copy installs are human-checkpoint-only; NEVER both at once (two module objects) | `01-09-SUMMARY.md:17,26-27,38,40,120-122`; AGENTS.md gate 5-6 | **INCOMPLETE** — README must present plugin-path as the verified route and warn against double-install |
| 4 | "Full attribution in `DATA_SOURCES.md`" | README.md:48 | The file is at `docs/DATA_SOURCES.md` — relative link from the root README should say so | verified by `ls docs/` | **FIX** (path) |
| 5 | "!! Under Development !!" | README.md:4 | Release-time decision: retain or drop. DOCS-01 mandates the *vibe-coding warning* only | — | **PLANNER/HUMAN DECISION** |
| 6 | Stale keyboard-control mentions in user-facing docs | docs/, spec.md, README | **NONE FOUND** (grep for keyboard/arrow/direction button/nudge over docs/ + spec.md returned zero hits) — the 8.3 deletion predates all shipped prose | grep run this session; deletion record `.planning/STATE.md` 8.3-03 bullet | **CLEAN** |
| 7 | Version claims | README (none beyond PyMOL 2.5.0) | Plugin version is `0.1.0` (metadata `# Version: 0.1.0` line 1 + `__version__` `aamatch/__init__.py:13`) | verified | **CONSISTENT** (README silent — fine) |
| 8 | Format gates (for Usage prose accuracy) | — | container `FORMAT_VERSION=1` (`persistence.py:37`); `LEVEL_SPEC_VERSION=1` + `DETECTOR_VERSION='det-1'` (`level_spec.py:60-61`); `GAME_VERSION=1` (`game_file.py:81`); `CHECKPOINT_VERSION=1` (`checkpoint.py:91`); manifest `manifest_version: 1` | verified | FACTS to transcribe, no drift |
| 9 | Tooltip "Generate from your own SDF or MOL2 file (one file; multi-record files give several molecules)" | setup_window.py:278-280 | Accurate as far as it goes; on THIS build single-segment MOL2 is refused at the reader guard (`read_mol2str` unexported) — the tooltip doesn't claim success, but the README/Usage should state the MOL2 fail-closed reality honestly | `upload.py:47-53, 114-118, 135-141` | **AUDIT ROW** (help-text sufficiency, HELP-01 adjacent) |
| 10 | Confirm tooltip | game_window.py:246-248 | Matches `CONFIRM_PASS_RULE='all'` pass gate exactly | `game_state.py:152-168` | **CLEAN** |
| 11 | Import tooltip ("Load a saved checkpoint (.aamz) … or an exported game file (.aamatch.json)") | game_window.py:311-313 | Matches the header-exact kind dispatch | `persistence.py:133-152`; `game_window.py:1107-1134` | **CLEAN** |
| 12 | Wizard panel: 'Movement:' header + Toward-only + Confirm/Reset to Grid/Done | wizard_text.py:49-59, 232-238 | Matches the 8.3 pivot | `wizard.py:107` | **CLEAN** |
| 13 | Prompt line "Selected: slot %s (%s). Move/rotate it, then Confirm." | wizard_text.py:273 | Wording predates the drag pivot; the recorded disposition **deferred the prompt tail to Phase 9** ("prompt_tail DEFERRED to Phase 9") and the pivot notes say "Phase-9 help text must be worded to the drag model" | `.planning/STATE.md` 8.3-01 disposition bullet + keys-note supersession bullet; 08.3-16-SUMMARY "affects" | **KNOWN CARRY** — this phase's help work must reword it (HELP-01/DOCS-02 intersection) |
| 14 | "Game abandoned." log line / Done semantics | status_text.py:309; STATE.md quick-004 | Shipped behavior: Done mid-game = abandon-stop (no record/modal); help wording carry "Done = closing the board"; re-word candidate recorded | STATE.md lines 14-15 | **KNOWN CARRY** |
| 15 | O1 help lesson (salt bridge vs H-bond) | — | Detector emits H-bond AND salt-bridge records together when the geometry qualifies; a 5.5 Å charge-center contact alone is NOT an H-bond. Help text must not imply mutually exclusive scoring | `.planning/STATE.md` O1-RESOLVED entry ("PHASE-9 HELP LESSON"); `.planning/debug/saltbridge-hbond-interplay.md` | **INPUT to help wording** |

Explicit non-findings (checked so the planner doesn't re-hunt): no `.mol2`-always-works claims anywhere in docs; no "keyboard arrows" in any shipped string (`wizard_text.py` was rewritten in 8.3 — its docstring and `_MOVEMENT_BUTTONS` are pivot-correct); no score-formula prose in README (it's a placeholder).

---

## §4 DOCS-02 audit methodology (design for the [GATE])

### 4.a Claims inventory (per document)

1. **README.md** — one claim-row per section (Requirements, Install steps 1-3, Usage steps, demo-table rows, Project-structure entries, License, Acknowledgements, warning-retained).
2. **In-game help strings** — two families:
   - Wizard panel/prompt: every string builder in `aamatch/wizard_text.py` (`_MOVEMENT_BUTTONS`, `_ACTION_BUTTONS`, `_DONE_LABEL`, `_CLICK_INSTRUCTION`, `panel_entries` order, `prompt_lines`, `required_summary`, `result_lines`) — ALREADY pinned by `tests/test_wizard_text.py` (button inventory `:173-177`, movement header `:207`, prompt shapes `:259-306`, result lines `:313-364`). The audit CITES these tests; do not duplicate them.
   - Status/log lines: `aamatch/status_text.py` builders (scored/failed/skip/give-up/level-advanced/reset/restarted/abandoned/saved/imported/resumed/endgame) — pinned by `tests/test_status_text.py`.
3. **Tooltips** — the 32 `setToolTip` sites (inventory grep-verified: 13 in setup_window.py, 17 in game_window.py + 2 upload-path-label dynamic ones). NO test currently pins these strings (Qt tier is AST-scanned only, per `setup_window.py:1-8` and the purity gates' scope).
4. **DATA_SOURCES.md** — rows already machine-reproducible via `python3.6 scripts/build_demos.py --report-only` (its own protocol, DATA_SOURCES.md:9-16); the audit re-runs that and diffs against the doc's tables + the file-coverage check from §2.3.

### 4.b Artifact format

`.planning/phases/09-help-docs-release-audit/09-AUDIT.md` — a claim→code table, one row per claim:

```
| # | Doc | Claim (verbatim or row ref) | Doc location | Verifying citation (file:line or test name) | Verdict (PASS / FIXED in <commit> / HUMAN) |
```

Rules mirroring the house gate-doc style (08-09-SUMMARY "patterns"): every row carries a citation; discrepancies get a FIXED row with the fixing commit; anything not machine-checkable gets an explicit HUMAN row feeding the [GATE]/[HUMAN] checkpoints. This artifact IS the criterion-3 evidence.

### 4.c Automatable in the WSL suite (proposed NEW test file, e.g. `tests/test_docs_audit.py`)

All of these are plain-text/data checks over repo files — they run under bare python3.6 with zero stubs, same as `test_demo_data.py`:

1. **DATA_SOURCES coverage:** every `aamatch/data/ligands/*.sdf` basename appears in `docs/DATA_SOURCES.md`; every manifest set_id has a `### <set_id>` section; every curated set's license string in the doc matches MANIFEST verbatim (the 08-09 claim, now pinned).
2. **README placeholders gone:** no `TBD` in README.md; `## Usage` section non-empty; `## Project Structure` code block non-empty; demo table contains all 10 set_ids (or at least all 9 curated ones + the dev set marked as fixture).
3. **Vibe warning retained:** README.md:1-2 exact-string check ("This is a vibe-coding project. While the human attempt to verify the source of all " + "contents, if you find any issues please contact me.") — presence check, not prohibition.
4. **Version consistency:** `__version__` == metadata `# Version:` line (parse `aamatch/__init__.py`'s first lines), and both == whatever version README eventually states (if any).
5. **Tooltip string pins (optional, judgement):** exact-string asserts for the load-bearing gameplay tooltips (Confirm / Import / Save / Hint / Toward-ligand / upload MOL2) so help regressions are caught mechanically. Keep it exact-string, not token-prohibition.

**Grep-gate pitfall compliance (AGENTS.md gate 3):** the enforced purity mechanism is the AST gate (`tests/test_purity.py`, negative-control pattern at `:118-129`); token greps are documented-only. The checks above are *coverage/presence* checks (require a string to EXIST), which cannot false-fire on prose the way a *prohibition* grep can. Do NOT add any banned-token grep to the suite, do not touch `test_purity.py`, no sys.modules stubs anywhere.

### 4.d What CANNOT be automated → [HUMAN]/[GATE]

- Whether README Usage **reads** as a correct end-to-end flow (an executor verifies row-by-row against code; the human plays it).
- Tooltip/help **sufficiency** = HELP-01 criterion 1 [HUMAN] (in-game help alone teaches the game) — the docs audit only checks *truth*, not *teaching quality*.
- DATA_SOURCES live re-verification (DOIs resolving) — the doc's own protocol owns this; the audit re-runs `--report-only` and checks structural coverage, not the network.
- The final [GATE] sign-off itself: a human reads 09-AUDIT.md.
- GUI-visible rendering of tooltips/panel text (real PyMOL session) — human checkpoint.

---

## §5 Existing data-integrity test coverage (what 08-01 already pins — extend, don't duplicate)

- `tests/test_demo_data.py` (08-01) — 10 checks over the REAL manifest: container parses; every entry file exists + sha256 matches disk; exactly the 14 `REQUIRED_ENTRY_KEYS`; `states_expected == 1`; `bond_order_counts` sums to `bond_count`; `size_class` reproduces `generator._candidate_class`; forward-slash package-relative files; curated-set semantics (non-empty license/provenance/title, tier in canonical vocabulary, spec provenance depth); spec coverage (spec ↔ manifest entry/file drift); builder py3.6 syntax. NOTE the file's own law: it is DATA-RELATIVE and "may NOT be relaxed" (`test_demo_data.py:8-10`) — add a NEW test file for docs checks, never edit this battery.
- `tests/test_demo_supply.py` (08-10) — curated bucket tally **small 12 / medium 4 / large 0** (14 incl. dev's 2 small); default-config generation over all sets EXCEPT three pinned thin refusals (demo-easy-3, demo-veryhard-2: 1 distinct entry; demo-veryhard-1: level-0 small pool thin). The README demo table and any "playable with defaults" claim must respect these three refusals (e.g., demo-easy-3 with molecules_per_level=2 refuses by design — a footnote candidate for Usage).
- `tests/test_manifest.py` — container/parse gate battery; `tests/test_purity.py` — PURE_MODULES registry (the module-tier source of truth for §2.2); `tests/test_code_audit.py` — AST-based banned-call/no-naive-loop audits (the grep-trap-immune precedent for any new mechanical check); `tests/test_wizard_text.py` + `tests/test_status_text.py` — the in-game help string pins.
- Headless: SMOKE-02 (every manifest id loads in real PyMOL with count asserts), SMOKE-22 (halogen/metal detector oracles on chloramphenicol/thyroxine/heme), SMOKE-21 (cleanup isolation field test).
- **Gap the phase fills:** nothing pins DATA_SOURCES.md coverage, README content, or tooltip strings — that's the §4.c test's job.

---

## §6 README authoring constraints + style precedents

- **Where README lives:** repo ROOT (`README.md`, verified) — GitHub-first surface; all relative links must be root-relative (`docs/DATA_SOURCES.md`, `LICENSE`).
- **Gate-doc format precedent to copy** (from `docs/DATA_SOURCES.md`, built by 08-09): header with last-verified date + verification protocol; every factual claim carries a source/URL+date; tables produced from the machine source (`--report-only` rows), never hand-maintained; honest absences marked with "— (none recorded…)"; per-set cross-ref law ("counts/sha256 pinned in MANIFEST.json; regenerate via scripts/build_demos.py …; never hand-edit an SDF or the manifest — 02-04 law", DATA_SOURCES.md:78-80).
- README-specific adaptations of that style: demo-set table columns (Tier | Category/Title | Source+license | ID(s) | Needs network?) can be filled verbatim from MANIFEST + DATA_SOURCES §2 (no new research needed — §2.3 of this document is the pre-digested dump); annotate that demo-dev-1 is a development fixture.
- **House truthfulness law binds README text** (spec.md:92 "Do NOT make up anything. ALL the claims and citations MUST BE VERIFIED…"; AGENTS.md Dependencies): the MOL2 fail-closed reality must be stated, not smoothed over; the install section must not present an unverified method as verified.
- UI-standards law (spec.md:87, AGENTS.md): "simple, user-friendly, clear but sufficient" — Usage should be a short numbered flow (§2.1 is the ready-made skeleton), not an exhaustive manual.
- Module-identity law constrains any install instructions: exactly ONE install mechanism; never plugin-path AND copy-install simultaneously (AGENTS.md gate 5; 01-09-SUMMARY.md:122).

---

## §7 Planning inputs — facts a planner MUST respect

1. **Manifest truth:** 10 sets / 18 entries — easy ×4 (incl. demo-dev-1 fixture), hard ×3, challenge ×1, very_challenging ×2 — `aamatch/data/MANIFEST.json` (`data.sets`); per-entry fields are `heavy_atom_count`, `formal_charge_sum`, `halogen_present`, `metal_present`, `size_class`, `states_expected`, `sha256` (all parsed this session, §2.3).
2. **README placeholders are exactly four:** `## Usage` (line 32 `> TBD`), `## Demo Molecules set` (lines 36-48, empty rows, missing dev row), `## Project Structure` (line 53 `#TBD`), `## Acknowledgements` (line 62 `TBD`). The vibe-coding warning (lines 1-4) is retained **byte-verbatim** (trailing spaces included); `## Requirements`, `## Install`, `## License` stay (Install needs the §3 fixes).
3. **Install section needs a human ruling** at the checkpoint: plugin-path is the only human-verified method (01-09-SUMMARY.md:17); the Plugin-Manager directory-install step as written points at the wrong thing (package directory vs `__init__.py`) and its button label is UNVERIFIED (runtime `.ui`).
4. **Movement prose = drag model:** shift-left translate / ctrl+shift-left depth / shift-right rotate (`wizard.py:335-337`), panel Toward-ligand only (2.5 Å, `wizard_core.py:70`), ZERO keyboard movement. Phase-9 carries: reword the selected-prompt tail to the drag model (08.3 disposition), "Done = closing the board" wording (QUICK-004), and the deferred movement hint.
5. **Pass gate wording:** Confirm advances ONLY when all required interactions are formed (`CONFIRM_PASS_RULE='all'`, `game_state.py:152`); failed Confirm = retry, records nothing. Score = fraction of required interactions formed (2-decimal display).
6. **File-format facts for Usage:** setup `.aam.setup.json`; game `.aamatch.json`; checkpoint `.aamz` = zip(game.pse + state.json); Import dispatches by container header (`peek_kind`), never by extension. Upload whitelist `.sdf`/`.mol2`, cap 50 records, MOL2 fail-closed on this build (multi-segment always; single-molecule via unexported `read_mol2str`), uploads session-only.
7. **DATA_SOURCES.md is 18/18 file-covered TODAY** (verified) and its set-license strings match MANIFEST verbatim — the audit extends it (README cross-links + coverage pin), it does not rebuild it.
8. **Existing pins to reuse, never weaken:** `test_demo_data.py` (10 checks, may NOT be relaxed), `test_demo_supply.py` (bucket tallies + 3 pinned thin-set refusals — constrain any "defaults work on every set" claim), `test_wizard_text.py`/`test_status_text.py` (help-string pins), `test_code_audit.py` (the AST precedent for mechanical checks). New docs tests go in a NEW file; no sys.modules stubs; no banned-token greps.
9. **Automation split:** README/`DATA_SOURCES` coverage + version consistency + placeholder-absence are WSL-testable (§4.c); tooltip exact-string pinning is optional; help sufficiency, install-method verification, GUI rendering, and the final gate are [HUMAN].
10. **Artifact = the gate:** `09-AUDIT.md` claim→code table (§4.b) with a verdict column and FIXED-commit references is the DOCS-02 criterion-3 evidence; plan it as a first-class deliverable, not a side note.

## Sources

All HIGH confidence — direct reads this session (2026-11-16):
- `README.md` (full), `docs/DATA_SOURCES.md` (full), `docs/DETECTION_THRESHOLDS.md` (header), `spec.md` (full), `AGENTS.md` (standing)
- `aamatch/`: `__init__.py`, `setup_state.py`, `setup_window.py` (form/bUTTON/upload/cleanup regions), `game_window.py` (tab/buttons/import/endgame regions), `wizard_text.py` (full), `wizard.py` (pivot/drag/confirm regions), `wizard_core.py` (constants), `game_state.py` (header + pass rule), `game_file.py` (header + cap/split/read), `upload.py` (full), `persistence.py` (full), `checkpoint.py` (header), `engine.py` (ops map + new_game), `gamestart.py` (seams), `setup_form.py` (grouping), `manifest.py` (tier refs), `paths.py`, `backup.py` (headers), `status_text.py` (builders), `level_spec.py` (version constants)
- `aamatch/data/MANIFEST.json` (full parse via python3.6) + `ls aamatch/data/ligands/`
- `tests/test_purity.py` (registry), `tests/test_demo_data.py` (full), `tests/test_demo_supply.py` (header), `tests/test_wizard_text.py` (test list), `tests/test_code_audit.py` (header)
- `smoke/smoke_01..24` docstring headers; `scripts/demo_specs/` ls
- `.planning/`: ROADMAP Phase-9 section, REQUIREMENTS.md (HELP/DOCS block), STATE.md lines 14-15 + Phase-8.2/8.3 decision bullets, research/PITFALLS.md pitfall-14 row, `phases/01-bootstrap-pure-foundation/01-09-SUMMARY.md` + `01-RESEARCH-plugin-install.md`, `phases/08-demo-curation-citations/08-09-SUMMARY.md`, `phases/08.3-drag-movement-pivot/08.3-16-SUMMARY.md`, `config.json`

**UNVERIFIED items (with settling probes):** (1) the Plugin-Manager "Install New Plugin" visible label — settle by one human GUI look or neutral wording; (2) whether `## Under Development !!` stays for release — human call; (3) LICENSE file content is assumed BSD-3-Clause per README:58 — settle by reading LICENSE (1 min) during execution if the audit needs the claim pinned.
