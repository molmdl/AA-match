# Phase 9: Help, Docs & Release Audit — Research (Aspect 3/3: Performance Budget Confirmation)

**Researched:** 2026-11-16
**Researcher scope:** Roadmap Phase-9 criterion 4 only — "[HEADLESS + HUMAN] Perf budgets confirmed on the largest curated demo: Generate < 30 s; pick/drag feedback < 200 ms (headless timing + human feel)". NOT in scope: HELP-01 help panel, DOCS-01/02 README + audit (covered by the sibling files `09-RESEARCH-help-ui.md` and `09-RESEARCH-docs-audit.md`, untouched).
**Method:** read-only. Every claim below cites a file:line I personally verified in this session. Nothing was executed (no PyMOL, no test suite); all numbers come from files. Do not commit.

---

## §1 Budget definitions — verbatim quotes + operational ruling

### Where the numbers actually live

**ROADMAP.md:328 (Phase 9, criterion 4 — the criterion verbatim):**
> `4. [HEADLESS + HUMAN] Perf budgets confirmed on the largest curated demo: Generate < 30 s; pick/drag feedback < 200 ms (headless timing + human feel). (PROJECT.md code standards)`

**ROADMAP.md:355 (Pitfall Coverage table, row 15 — verbatim):**
> `| 15 | Performance / event loop | Phase 2 (detect perf) · 3 (per-move cost) · 9 (final budgets) | Largest demo: Generate < 30 s, pick/drag < 200 ms |`

**.planning/research/PITFALLS.md:379 (Pitfall 15 "How to avoid", last bullet — verbatim):**
> `- Performance budget (adopt prior art's): Generate < 30 s on the largest demo; click/drag feedback < 200 ms.`

**PITFALLS.md:514 (pitfall-to-phase mapping, row 15 — verbatim):**
> `| 15. Performance/event loop | grid-generation + viewer-interaction + demos | Largest demo: Generate < 30 s, pick/drag < 200 ms (headless timing + HUMAN feel check) |`

**Correction to the brief:** the pitfall table is NOT in AGENTS.md. Root `AGENTS.md` has no pitfall table (grep for "Performance"/"budget"/pitfall rows: zero hits; only `.planning/` pointers at AGENTS.md:29). The pitfall-15 row lives in `ROADMAP.md:355` (lifted from `PITFALLS.md:514`). Cite ROADMAP/PITFALLS, not AGENTS.md.

**PROJECT.md itself carries NO numbers.** The criterion's "(PROJECT.md code standards)" reference resolves to the umbrella line — PROJECT.md:62 verbatim:
> `- **Code standards**: efficient, traceable, clean, safe; structured repo.`

So the ONLY quantitative statement of the budgets in the whole repo is ROADMAP.md:328/355 + PITFALLS.md:379/514. The plan should quote those, not PROJECT.md.

### What "Generate" covers — ambiguity + ruling

The word "Generate" is genuinely ambiguous in the shipped UI:

- The Setup window's button is **"Generate and export"** (setup_window.py:218-219, connected at :257 to `_on_generate_export` :928). Its engine work is `export_game` (setup_window.py:86-117): `engine.new_game` (:101-103) + `game_file.make_game_data` + save (:105-112) — **no materialize, no scene objects** (docstring :92-94: "The viewer scene is NEVER touched here").
- The **"Start"** button (setup_window.py:226, SETUP-10) drives `start_game` (setup_window.py:987-990: "pop -> prepare unactivated -> tab switch -> countdown"), which is cleanup → new_game → **materialize(level 0)** → compose → activate (gamestart.py:396-431).
- PITFALLS.md's own prose mixes both: the trap narrative says "Generate takes tens of seconds with the GUI frozen" (:368) and the warning sign says "'Start'/Generate freezes the GUI > 5 s" (:382). Phase-2's research recorded: "Budgets on record: Generate < 30 s on the largest demo (PROJECT code standards; ROADMAP Phase-9 …). Pick/drag < 200 ms is a Phase 3+/9 concern" (02-RESEARCH-materialization.md:524-526).

**Operational ruling proposed for the plan (planner may confirm):** "Generate" = one full `gamestart.start_game(...)` call at the defined workload — the superset: it contains everything `export_game` does (`engine.new_game`) PLUS materialize/compose/activate, so passing it implies the export path's engine half passes too. Optionally add one cheap extra row timing `export_game`-equivalent serialization (`game_file.make_game_data` + save) if the planner wants the literal button covered; the 30 s budget has orders-of-magnitude headroom for both (see §6). Rationale: the criterion pairs "Generate" with "pick/drag feedback" — i.e., the play experience — and PITFALLS.md:382 treats "Start"/Generate as the same freeze hazard.

### What "pick/drag feedback" means mechanically

- **Pick feedback** = the work behind one click on an AA: `do_select(name)` (wizard.py:428-453: `cmd.unpick` → `cmd.select('pk1', name)` → `cmd.deselect` → transient delete → `do_pick(0)`) → `do_pick` (wizard.py:455-497: `cmd.iterate('pk1', ...)`, slot-map lookup, game-over gate, `_select_slot`) → `_select_slot` (wizard.py:499-523: restore old slot colors `cmd.alter`+`cmd.rebuild` via `_restore_slot_colors` :397-426, snapshot new, `cmd.color(HIGHLIGHT_COLOR, obj)` :521, `cmd.refresh_wizard()` :523) → `_arm_drag` (wizard.py:776-816: `cmd.set('matrix_mode','0',obj)` :810, `cmd.select(_DRAG_SELE, obj)` :811, `cmd.drag(_DRAG_SELE, wizard=0, edit=0)` :812). **`detect()` is NOT called per pick** — detection runs only inside `_confirm_molecule_impl` (wizard.py:1058-1063: `engine.detect_molecule(...)`); ARCHITECTURE.md:266 records the law ("detection cost if run naively per-move. Fix: detect only on Confirm") and 02-RESEARCH-detection.md:276 repeats it. So pick cost = selection bookkeeping + recolor + panel refresh + drag arm — all O(selected object), not O(scene).
- **Drag feedback** = the work behind one drag event. **Reality check post-8.3:** the human gesture is the C-side drag on the `_DRAG_SELE` selection armed per pick (`cmd.drag(_DRAG_SELE, wizard=0, edit=0)`, wizard.py:812) — the C event loop drives those translates, and it **cannot be pumped under `-cq`** (wizard.py:921-923: "the C drag event loop cannot be pumped under -cq, so the programmatic path is the only SMOKE-provable form"). The measurable headless proxy is `wiz.drag_move(dx_px, dy_px)` → `_drag_move_impl` (wizard.py:939-960): `_require_playing` → `cmd.get_view()` + `cmd.get_viewport()` (:950-954) → pure `wizard_core.drag_world_step` (:955) → `cmd.translate(list(delta), obj, state=1, camera=0)` (:958) → `_assert_identity(obj)` (:959; `cmd.get_object_matrix`-style 12-element identity check, wizard.py:756-774) → `cmd.refresh_wizard()` (:960). Its docstring states it bakes "IDENTICAL in form to what the C drag applies (SceneMouse.cpp:1479-1507)" (wizard.py:925-931). **03-RESEARCH per-move-cost law status:** the law (ROADMAP.md:355 "Phase 3 (per-move cost)"; ARCHITECTURE.md:266) is still accurate post-8.3 — per-move work remains translate-bake + identity assert + refresh, detection still Confirm-only; 8.3 added `cmd.get_view`/`get_viewport` per drag step and the per-pick `_arm_drag`, all cheap, none O(scene).

**One definitional honesty item for the plan:** headless "drag" timing measures the *programmatic twin* (`drag_move`), not the real C gesture; the real gesture's feel is exactly what the [HUMAN] half of the criterion covers (§7). State this split in the receipt.

---

## §2 Largest curated demo — manifest facts

Parsed `aamatch/data/MANIFEST.json` (container magic `AAMATCH`, version 1, kind `manifest`; payload `manifest_version: 1`) with python3.6. Shipped reality: **10 sets, 18 entries**.

Per-set entry counts: demo-dev-1=2, demo-easy-1=2, demo-easy-2=2, demo-easy-3=1, demo-hard-1=2, demo-hard-2=2, demo-hard-3=2, demo-challenge-1=2, demo-veryhard-1=2, demo-veryhard-2=1. **No set has more than 2 entries** (max=2, shared by eight sets).

Top entries by the three size axes (all values read from MANIFEST.json this session):

| Rank | set_id | entry_id | heavy_atom_count | atom_count (all) | bond_count | metal | notes |
|---|---|---|---|---|---|---|---|
| 1 | demo-hard-3 | **nad** | **44** | 71 | 75 | no | **THE largest by the manifest's own law** |
| 2 | demo-veryhard-2 | heme | 43 | **73** | **80** | **yes** | largest by total atoms AND bonds; only metal entry |
| 3 | demo-veryhard-1 | folic_acid | 32 | 49 | 51 | no | |
| 4 | demo-hard-3 | atp | 31 | 47 | 49 | no | |
| 5 | demo-challenge-1 | quinine | 24 | 49 | 52 | no | |
| 6 | demo-veryhard-1 | thyroxine | 24 | 35 | 36 | halogen | |

- **THE largest single demo molecule (by the repo's own selector): (demo-hard-3, nad), heavy=44.** No tie (unique max), so `largest_entry`'s ties-first rule is not exercised by today's data.
- **largest_entry law verified:** `aamatch/manifest.py:317-329` — `largest_entry(entries)` returns "the entry with the max heavy_atom_count (ties: the first in the given order …)"; docstring :320-321: "This is the perf-smoke target selector (DETECT-05): derived from the entries, never a special-cased manifest field." The 02-03 de-hardcoding law holds; smoke_05 re-derives it at runtime (smoke_05_perf.py:180, cross-check assert :188-194) and its comment already anticipates the Phase-8 manifest: "With the Phase-8 manifest the largest entry is expected to be a medium ligand (NAD/heme class…)" (smoke_05_perf.py:183-187). Phase-2's recorded target was benzamide heavy=9 (STATE.md:123); today it is NAD heavy=44 — SMOKE-05 self-adapts, no renumber needed.
- **Planner decision input:** "largest curated demo" = **NAD** by the repo's own law. Note heme carries more total atoms (73) and bonds (80) and is the only metal entry — if the planner wants belt-and-braces, an OPTIONAL extra row can time the same budget on heme, but the criterion's selector is largest_entry → NAD. Do not silently swap the selector.

---

## §3 Generate-path anatomy + workload knobs

### Stage-by-stage trace of `start_game` (gamestart.py:356-437)

| # | Stage | Work | Cite |
|---|---|---|---|
| 1 | `placement.cleanup_game_objects()` | prefix-only deletion of prior `_aam_*` objects | gamestart.py:396; placement.py:495 |
| 2 | setup copy | `dict(setup_state.DEFAULTS if setup is None else setup)` | gamestart.py:397 |
| 3 | `engine.new_game(spec, seed, candidates, ligand_content)` | (a) `validate_state` (engine.py:310); (b) read+parse MANIFEST.json, `enumerate_entries`, filter by non-empty `demo_set_id` (engine.py:312-320); (c) **`_ligand_data_for` per candidate row** — temp `cmd.load` (or `read_sdfstr`) → atom_count cross-check → `geometry.extract_game_atoms` → bounding sphere → `remap_ligand_bonds` → `capability.ligand_profile` → temp deleted in `finally` (engine.py:337-340, 203-286); (d) `generator.generate(...)` builds the FULL payload (all D levels) (engine.py:342-343); (e) scene-unchanged assert (engine.py:350-353) | engine.py:289-354 |
| 4 | `engine.materialize(payload, 0)` → `placement.materialize` | **ONE level only (level 0)**: per molecule — unique-name `cmd.load` of the ligand (:344-388), count assert, sentinel tag (:389-391), `_normalize_ligand_reps` (:400), offset translate (:401); per slot — `cmd.fragment(AA_TOKENS[...]['fragment'])` + sentinel + sort + centroid-delta translate + pose assert (docstring placement.py:284-291) | engine.py:357-374; placement.py:262-401 |
| 5 | `GameWizard(payload, registry, 0, 0)` construction | books setup only, no scene ops | gamestart.py:402 |
| 6 | `compose_molecule_view(registry)` | `_move_ligand_in_front` (extract_game_atoms over the scene + cam_z projections + one `cmd.translate`, gamestart.py:233-303, called :332) then ONE `cmd.zoom` over the active molecule's objects (:333-334) | gamestart.py:306-334, called :419 |
| 7 | `_last_start` capture | deepcopy bookkeeping | gamestart.py:425-429 |
| 8 | `activate_game(wiz)` (default `activate=True`) | conditional replace read; `wiz.activate(replace=…)` — deselect, `cmd.set_wizard`, msm+button_mode snapshots, defensive msm 0, 3× `cmd.button` gesture map, `cmd.refresh_wizard` (wizard.py:293-338); then `engine.current_game().start_timer(time.time())` | gamestart.py:337-353, called :430-431 |
| 9 | status print | one line | gamestart.py:432-436 |

**Cost drivers, ranked:** (i) per-candidate ligand temp-loads + profile builds in `new_game` — scales with CANDIDATE COUNT (whole manifest = 18 rows when `demo_set_id` is empty; engine.py:317-320 — empty string means NO filter); (ii) `generator.generate` pure-Python over all D levels × molecules_per_level molecules, each with `allocate_slots` up to grid 9 (generator.py:797-854; grid law `grid_n = GRID_N_MIN + frac`, GRID_SPAN=6, GRID_N_MIN=3 → max 9, generator.py:110-127,172); (iii) level-0 materialize — mPL × (1 ligand load + grid 3×3 = 9 fragments); (iv) compose extract + zoom. Note each demo ligand is loaded TWICE per start when it is used (temp profile load in new_game + permanent load in materialize).

### Workload knobs + the clamp reality (verified)

- `molecules_per_level`: clamp [1, **10**] — setup_state.py:46 (`MOLECULES_DEFAULT, MOLECULES_MIN, MOLECULES_CAP = 2, 1, 10`), clamp applied :119-122.
- `difficulty_levels`: clamp [1, **10**] — setup_state.py:50 (`DIFFICULTY_DEFAULT, DIFFICULTY_MIN, DIFFICULTY_CAP = 3, 1, 10`, "human-amended at the 01-09 install checkpoint"), clamp :123-126.
- **BUT the raw clamps are not reachable on the bundled manifest.** Generator bucket law: `bucket_index = (L*3)//D` over `SIZE_CLASSES = ('small','medium','large')` (generator.py:167-174,124). Computed from today's MANIFEST.json: size_class distribution = **14 small, 4 medium, 0 large**. For D=10: levels 0-3 target small (pool 14), levels 4-6 target medium (pool **4**), levels 7-9 target large → `_select_pool` supply-side fallback to the nearest non-empty bucket = medium (generator.py:603-629, "SUPPLY-SIDE FALLBACK … recorded deviation, plan 02-08"). `taken` resets per level (generator.py:802), so the binding refusal is the medium pool: with `molecules_per_level = 5`, level 4's 5th pick finds `available` empty → GenerationError "Only 4 of the 18 molecules … fit the molecule size used in level 5. Set 'Small molecules per level' to 4 or less." (generator.py:836-840).
- **⇒ Heaviest LEGAL manifest workload = `demo_set_id: ''` (all 18 candidates), `molecules_per_level: 4`, `difficulty_levels: 10`** → new_game profiles 18 ligands; generate builds 10 levels × 4 molecules (40 allocations, grids up to 9); materialize builds level 0 = 4 × (1 ligand + 9 slots) = **40 objects**. Any `molecules_per_level ≥ 5` refuses; any single `demo_set_id` caps molecules at that set's entry count (≤ 2).

### Stopwatch boundaries (proposed)

- **Start:** immediately before `gamestart.start_game(setup=…, seed=…)` (includes cleanup — honest, matches the user's button press).
- **Stop:** immediately after the call returns (it includes compose + activate + timer anchor + print). Do NOT stop after materialize — the wizard activate is part of the user-visible freeze.
- Record a **cold** (first start in the process) and a **warm** (second start, same setup, after cleanup) number; assert the COLD one (that is the user's real experience; PyMOL first-call warm-up is inside it — §8).
- Workload rows: (A) criterion-letter row — `candidates=[largest_entry]` (NAD), `molecules_per_level: 1`, `difficulty_levels: 10`, any interaction mode (smoke_05's exact shape, smoke_05_perf.py:207-211); (B) max-legal-workload row — `demo_set_id: ''`, `molecules_per_level: 4`, `difficulty_levels: 10` (§3 knobs). Both < 30 s.

---

## §4 Pick/drag anatomy — event → work + mechanical latency definitions

Verified this session in wizard.py:

| Event | Work (order) | Cite |
|---|---|---|
| pick (Viewing mode) | `do_select(name)`: `cmd.unpick()` → `cmd.select('pk1', name)` → `cmd.deselect()` → transient-only delete → `self.do_pick(0)` | wizard.py:428-453 |
| pick (continued) | `do_pick`: `cmd.iterate('pk1', …, space={'stored': rows})` → `cmd.unpick()` → `_slot_by_object` lookup (non-slot = no-op) → game-over soft gate → `_select_slot(slot_id)` → `_arm_drag(object)` (LAST, because the arm's `cmd.drag` runs EditorInactivate which deletes pk1..pk4) | wizard.py:455-497 |
| pick → recolor | `_select_slot`: restore old slot colors (`cmd.alter` + `cmd.rebuild`, :397-426) → lazy snapshot → `cmd.color(HIGHLIGHT_COLOR, obj)` :521 → `cmd.refresh_wizard()` :523 | wizard.py:499-523 |
| pick → arm | `_arm_drag`: `cmd.set('matrix_mode','0',obj)` → `cmd.select(_DRAG_SELE, obj)` → `cmd.drag(_DRAG_SELE, wizard=0, edit=0)`; soft-fail into panel error | wizard.py:776-816 |
| drag event (headless proxy) | `drag_move(dx_px,dy_px)` → `_guard` → `_drag_move_impl`: `_require_playing()` → `cmd.get_view()` + `cmd.get_viewport()` → `wizard_core.drag_world_step(view, dx, dy, vh)` → `cmd.translate(delta, obj, state=1, camera=0)` → `_assert_identity(obj)` → `cmd.refresh_wizard()` | wizard.py:915-960 |
| detect | **Confirm-only** (`engine.detect_molecule` inside `_confirm_molecule_impl`); never per pick, never per drag | wizard.py:1058-1063 |

**Mechanical latency definitions (what a headless stopwatch can honestly measure):**

1. **pick_ms** — wall time of the full scripted-pick pair, per rep:
   ```python
   cmd.select('sele', '%s and name CA' % slot_obj)   # smoke_24:415 recipe
   wiz.do_select('sele')                              # smoke_24:416
   ```
   (the C-layer click equivalent; smoke_24:102-110 documents this as "the smoke_07/smoke_23 recipe"). Alternate between TWO slots per rep so the restore+recolor switch path (`_select_slot`'s old-slot branch, wizard.py:515-517) is inside every measurement, not just the cheap same-slot path.
2. **drag_ms** — wall time of one `wiz.drag_move(dx, dy)` call (e.g. alternating `(+20, +12)` / `(-20, -12)` to keep the AA near its slot). Honest-scope note (already shipped wording, wizard.py:921-923): this times the programmatic twin; the real C-side gesture loop is not pumpable under `-cq`. The two apply "IDENTICAL in form" bakes (wizard.py:925-931).
3. Both measured on the **heaviest live-game scene** available headlessly — see §6 row-2 workload options.

---

## §5 Timing-harness precedents (copy these recipes)

### smoke_05 (the repo's only budget-asserting smoke) — smoke/smoke_05_perf.py

- **Run line + verdict law:** `bash smoke/run_smoke.sh smoke/smoke_05_perf.py 240`; "Verdict is carried by the printed marker (exit codes cannot carry verdicts through the cmd.exe wrapper): grep '=== SMOKE-05 PASS ==='" (smoke_05_perf.py:3-5).
- **Budgets as local literals, with the tier comment:** `DETECT_BUDGET_MS = 100.0`, `TOTAL_BUDGET_MS = 1000.0` (:100-101) — "the WSL-only 2.0 s loose guard … must never leak into this gate" (:97-99).
- **Timing shape:** plain `t0 = time.time()` … `t1` … `t2` around the two pipeline stages (:312-318); ms math (:319-320).
- **Assert with observed numbers in the detail string:** `check('detect inside 100 ms budget', detect_ms < DETECT_BUDGET_MS, 'detect=%.3f ms (< %.0f ms)')` (:337-340); same for the 1000 ms total (:341-345). **No warm-up pass, no margin logic — raw budgets, headroom ~9x/46x** (02-VERIFICATION.md:27, :98: "detect 11.238 ms < 100 ms, extract+detect 21.805 ms < 1000 ms … 1285 atoms").
- **Raw numbers for the receipt:** `print('SMOKE-ENV perf extract_ms=%d detect_ms=%d atoms=%d' …)` (:334-336).
- **check() + verdict marker:** `check(name, cond, detail)` prints `'SMOKE-05 %-38s %s %s'` and accumulates failures (:71-75); sole verdict carrier `print('=== SMOKE-05 %s ===' % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'))` (:406-407).
- **Conventions (frozen Phase 1):** repo root via sys.argv first / cwd fallback, never `__file__` (:55-65); one-line flushed prints (:40-42); explicit space dicts; 3.6-safe source running on PyMOL's 3.9 (:45).

### run_smoke.sh — smoke/run_smoke.sh

- `TIMEOUT="${2:-120}"` (:14); NN derived from the basename via sed, fallback "01" (:15-17); per-run mktemp log (:18); runs `cmd.exe /c C:\src\run-conda-pymol.bat -cq smoke\<script>` from the repo root (:20-21); **verdict = `grep -q "=== SMOKE-$NN PASS ==="` in THIS run's log** (:24); timeout/dead-run diagnostics with "re-run with a larger TIMEOUT arg (some smokes need 180-240s)" (:30-37).

### Scripted interaction precedents

- **Scripted pick:** smoke_24 PART 0 — `cmd.select('sele', '%s and name CA' % slot_obj)` then `wiz.do_select('sele')` (smoke_24_drag_battery.py:415-416), recipe credit line :102-110.
- **Scripted drag:** `wiz3.drag_move(r7_dx, r7_dy)` (smoke_24:937, :990, :1044) on a live game; the honest-scope statement is wizard.py:919-923.
- **Heavy live scene precedents:** `engine.materialize(payload, level_index=9)` directly (smoke_05:236 — 82 objects, no wizard) and `engine.advance_level()` under a live wizard (smoke_15 docstring rows A5/B3: "advance_level: cleanup + materialize(L+1) + GameState atomically"; smoke_15_lifecycle.py:48, 94). For a live wizard ON the 9×9 scene, the assembly precedent is the checkpoint rebuild path: `GameWizard(payload, registry, level, molecule)` + `activate` (gamestart.py:728-750, exercised by SMOKE-20's forced-rebuild run, 08.3-15-SUMMARY:121).

### Where raw numbers get recorded (house pattern)

- In-log: `SMOKE-ENV` lines (smoke_05:334-336).
- In-record: the plan's SUMMARY quotes them — e.g. 02-VERIFICATION.md:27 (budget vs observed) and the smoke-sweep roster table with per-smoke runtime, 08.3-15-SUMMARY.md:100-127.

---

## §6 SMOKE-25 design (next free number)

**Next free number: SMOKE-25.** `ls smoke/` shows exactly smoke_01 … smoke_24 (verified this session); the 08.3-15 roster closes at 24 files / 26 invocations (08.3-15-SUMMARY.md:102-127). The roster-preservation convention (rename keeps the number: smoke_23 movement battery, 08.3-15-SUMMARY.md:124) means SMOKE-25 is a NEW additive file; smoke_05 is NOT touched (it already self-adapts to NAD via `largest_entry`, §2) — no renumbering, no dated bridge needed.

**File:** `smoke/smoke_25_perf_budgets.py` (basename → NN=25 via run_smoke.sh:15-17). Copy smoke_05's skeleton: `_find_repo_root` (:55-65), `check()` (:71-75), SMOKE-ENV env lines (:94-95), verdict marker (:406-407 shape with SMOKE-25).

**Proposed rows:**

1. **Row G — Generate (criterion letter):** manifest parse → `biggest = largest_entry(entries)`; `setup = validate_state({'molecules_per_level': 1, 'difficulty_levels': 10, …})`; `t0=time.time(); wiz = gamestart.start_game(setup, seed=42, candidates=[biggest]); gen_ms_cold=(time.time()-t0)*1000`. Assert `gen_ms_cold < 30000`. Echo `SMOKE-ENV generate_cold_ms=…`. Then a second start (warm) echoed only. Include a count assert (objects grew by the expected 1×(1+9)=10) so the row cannot pass vacuously.
2. **Row W — Generate at max legal workload (criterion spirit):** `demo_set_id: ''`, `molecules_per_level: 4`, `difficulty_levels: 10` (§3 legality); same stopwatch; assert < 30000; echo raw ms + object count (expected 4×10=40). **Pre-flight legality probe in the plan:** before writing the smoke, re-verify with a 5-line python3.6 pure check that bucket pools still support mPL=4 (the 14/4/0 distribution is a Phase-8 data fact; a future manifest edit could move it — the smoke should treat the generator's own GenerationError as a FAIL-with-message, never a crash).
3. **Row S — heavy scene assembly:** either (a) smoke_05-style `engine.materialize(payload, level_index=9)` + direct `GameWizard(payload, registry, 9, 0)` + `activate()` (precedents: smoke_05:236, gamestart.py:728-750) or (b) advance the row-1 game to level 9 via the smoke_15 `advance_level` route. Assert the 82-object count like smoke_05:239-241. This is the scene for rows P/D; if the planner wants to trim, rows P/D may run on the row-1 level-0 scene with the scene size echoed — but the 82-object scene is the honest worst case and is cheap to build.
4. **Row P — scripted pick timing:** N=20 reps alternating two slots (recipe §4.1); report **min/avg/max** in SMOKE-ENV; assert `avg < 200` ms AND `max < 200` ms (max is the user-feel number; with expected per-pick ~1-20 ms both have ≥10x headroom).
5. **Row D — scripted drag timing:** N=20 reps of `wiz.drag_move(20.0, 12.0)` / `(-20.0, -12.0)`; report min/avg/max; assert avg and max < 200 ms.
6. **Teardown:** `placement.cleanup_game_objects()` + scene-equals-pre-game assert (smoke_05:385-403 shape).

**PASS criteria greps:** `bash smoke/run_smoke.sh smoke/smoke_25_perf_budgets.py 240` must produce `=== SMOKE-25 PASS ===` (run_smoke.sh:24); the plan's SUMMARY quotes the marker + the SMOKE-ENV number lines (the 02-VERIFICATION.md:27 / 08.3-15-SUMMARY.md:100-127 pattern). **[HEADLESS] receipt = marker + raw numbers.**

**Margin policy:** assert the **raw budgets** (30 s / 200 ms) exactly as smoke_05 asserted raw 100/1000 ms with ~9x/46x headroom — no artificial margin inflation, because measured costs are expected ≥10x under budget and a margin-banded assert would be a second, invented budget. Procedural (not code) flake rule: any run landing within 2x of a budget (≥15 s or ≥100 ms) is treated as environment noise → re-run once and record both runs. Echo everything; the receipt's value is the raw number, not the boolean.

**Runtime cost of the smoke itself:** comparable to the heavy smokes — two start_games + an 82-object materialize + 40 scripted interactions ≈ the 1-8 s wall class of the roster (08.3-15-SUMMARY.md:102-125), plus PyMOL start; **timeout 240 s** (the roster's heavy-smoke value). **UNVERIFIED (settled by the first real run):** actual wall time of row W at mPL=4/D=10 in real PyMOL — expected seconds; the smoke's own receipt will pin it.

**Do NOT:** touch smoke_05 (byte-untouched control, 08.3-15-SUMMARY.md:138); renumber anything; weaken the standing gates; add WSL perf asserts (§8).

---

## §7 [HUMAN] feel checklist (smallest sufficient)

Criterion tag is [HEADLESS + HUMAN]; the human half = "pick/drag feedback … human feel". Model: 08.3-16's fresh-session ritual (08.3-16-PLAN.md:127-188 — fresh Windows PyMOL via setenv.bat, numbered steps, PASS/FAIL + verbatim quotes, verdicts transcribed into the SUMMARY + STATE). Smallest checklist that discharges the criterion:

1. **Session:** ONE fresh Windows PyMOL 2.5.0 session (setenv.bat recipe; live plugin-path method — 08.3-16-PLAN.md:127-128). Start the **demo-hard-3 (NAD)** game — the budget's demo — at default setup.
2. **Generate feel:** press Start and watch the countdown path: the gap between clicking Start and the live 3-2-1 game must feel immediate (no multi-second silent freeze; PITFALLS.md:377 "never a 30-second silent freeze", warning sign :382 "> 5 s"). Record "felt instant / ~N s".
3. **Pick feel:** click several AAs in sequence (including switching from a selected AA to a different one): highlight appears with the click, no perceptible lag.
4. **Drag feel:** shift+left-drag a selected AA (the shipped gesture map, wizard.py:335-337): the AA tracks the cursor rigidly with no stutter; release keeps position; drag a second AA right after a pick (re-arm law in the hands, 08.3-16-PLAN.md:148-150).
5. **Depth + rotate gestures** (ctrl+shift-left depth; shift+right-drag rotate) — same "instant" bar, one rep each.
6. **Confirm feel:** one Confirm — detection-on-confirm should be invisible (< 100 ms-class; PITFALLS.md:384) — and one deliberately-blind Confirm (Formed/Missing debrief renders promptly; pass-gate law untouched, PROJECT.md:76).
7. Verdict table (numbered PASS/FAIL + one sentence each, verbatim quotes for anything surprising) transcribed into the plan SUMMARY + STATE bullet (08.3-16-PLAN.md:199-218 pattern).

Steps 2-6 are the perf-criterion half; do not re-litigate 8.3's functional ritual (already approved, 08.3-16-SUMMARY.md:152) — this checklist only measures feel.

---

## §8 Environment honesty + flakiness traps

- **The tier law already exists — keep it exactly.** WSL: `WSL_PERF_GUARD_SECONDS = 2.0` loose guard on a synthetic crammed scene only, with the docstring law "The REAL DETECT-05 budget (< 100 ms) is asserted only headlessly" (tests/test_detector_invariance.py:52, 1123-1127; recorded in STATE.md:129 as the 02-11 receipt). No other WSL test asserts any timing (grep-verified this session). **Ruling: WSL unit tests assert NOTHING for the 30 s / 200 ms budgets (the existing 2.0 s detector loose guard stays as-is, untouched); the headless smoke asserts the budgets in real Windows PyMOL; the human records raw feel + the SUMMARY records the smoke's raw numbers.**
- **cmd.exe + PyMOL-start overhead lives OUTSIDE the stopwatch** (run_smoke.sh times nothing; the smoke's `time.time()` brackets only the op). But PyMOL-start and import cost bound the smoke's wall clock — budget the timeout, not the assertion.
- **First-call warm-up:** the FIRST `cmd.*` calls in a process (first `cmd.load`, first `cmd.fragment`) carry lazy-init cost. Mitigation per §6: assert the COLD start (< 30 s is generous), echo the WARM start; for pick/drag rows, discard nothing but report min/avg/max — min shows the warm floor, max is the honest feel bound.
- **Float32/1e-6 laws:** irrelevant to timing (they govern coordinate-drift asserts; SMOKE-24's DRAG_TOL/RIGID_TOL, smoke_24:263-270). SMOKE-25 does no pose asserts beyond object counts — do not import those tolerances.
- **cmd.exe verdict law:** exit codes cannot carry verdicts (run_smoke.sh:4-5) — SMOKE-25 must print the `=== SMOKE-25 PASS ===` marker and nothing else may be the verdict.
- **Timing-noise magnitude in this environment: UNVERIFIED.** No repo file records per-op Windows timing variance beyond smoke_05's single-run receipt (11.238 ms detect). The probe that settles it = running SMOKE-25 twice on the final build (the re-run rule in §6); expected headroom makes this a formality.
- **Workload legality is data-dependent:** the mPL=4 ceiling is a Phase-8 manifest fact (§3). If Phase 9's DOCS work adds entries, re-derive; the smoke fails loudly via the generator's own GenerationError rather than silently measuring less.

---

## §9 Planning inputs (facts a planner MUST respect)

1. **Quote the budgets from ROADMAP.md:328/355 + PITFALLS.md:379/514 — PROJECT.md:62 has no numbers** (only "efficient, traceable, clean, safe"). The pitfall table is in ROADMAP/PITFALLS, NOT AGENTS.md.
2. **The largest curated demo = (demo-hard-3, nad), heavy_atom_count=44**, via `manifest.largest_entry` (manifest.py:317-329, derived-never-hardcoded law intact; no tie today). Heme (73 atoms, metal) is larger only by total-atom/bond counts — do not swap the selector; optionally add an extra heme row.
3. **`start_game` is the operational "Generate"**: cleanup → `engine.new_game` (manifest parse + per-candidate ligand profile loads + full-payload generation) → `engine.materialize(payload, 0)` (level 0 ONLY) → compose → `activate_game` (gamestart.py:396-437). The export-only path (setup_window.py:86-117) never materializes; if the planner wants the literal "Generate and export" button timed, add one row — the budget headroom makes it trivial.
4. **Max workload is clamp-bounded by data, not clamps:** knobs clamp to 10/10 (setup_state.py:46,50) but the manifest's 14-small/4-medium/0-large distribution + the generator bucket law + supply fallback (generator.py:167-174, 603-629, refusal 836-840) make the heaviest LEGAL manifest game **molecules_per_level=4, difficulty_levels=10, demo_set_id='' (18 candidates)**. Any smoke that naively requests 10/10 FAILS with the generator's refusal.
5. **Detection is Confirm-only** (wizard.py:1058-1063); pick cost = bookkeeping + recolor + refresh + drag-arm; drag cost = view read + pure step math + `cmd.translate(state=1, camera=0)` + identity assert + refresh (wizard.py:939-960). The 03 per-move-cost law still holds post-8.3.
6. **Headless drag timing is the `drag_move` programmatic twin** — the C drag loop is not pumpable under `-cq` (wizard.py:921-923); the real gesture's feel is the [HUMAN] half. Scripted-pick recipe = smoke_24:415-416.
7. **Copy smoke_05's harness law** (smoke_05_perf.py:100-101, 312-345, 406-407): local budget literals, `time.time()` walls, observed numbers inside every check detail, SMOKE-ENV raw-number lines, single `=== SMOKE-NN PASS ===` verdict marker. Assert RAW budgets (30 s / 200 ms) — expected headroom ≥10x; re-run-once rule if within 2x.
8. **SMOKE-25 is the next free number** (smoke roster 01-24, 08.3-15-SUMMARY.md:102-127); additive file, run with `bash smoke/run_smoke.sh smoke/smoke_25_perf_budgets.py 240`; smoke_05 stays byte-untouched and already self-adapts to NAD.
9. **Tier ruling:** WSL tests assert nothing perf (existing 2.0 s loose guard untouched, test_detector_invariance.py:52,1123-1142); headless smoke asserts budgets; human checklist (§7) records feel verbatim; SUMMARY records raw numbers (02-VERIFICATION.md:27 + 08.3-15-SUMMARY.md:100-127 patterns).
10. **Level-9 (82-object / ~1285-atom) scene** is the honest pick/drag worst case; assembly precedents: smoke_05:236 (materialize 9), gamestart.py:728-750 (direct GameWizard+activate, SMOKE-20-proven), smoke_15 advance_level route (smoke_15_lifecycle.py:48,94).

**UNVERIFIED items (probes settle them):** (a) actual wall-time of `start_game` at the max-legal workload in real PyMOL (SMOKE-25 row W's own receipt); (b) per-pick/per-drag wall-time distributions in real PyMOL (SMOKE-25 rows P/D); (c) Windows timing variance across runs (the §6 re-run rule). All are settled by running the smoke once — no code probe needed beforehand beyond the §6 row-W legality re-check.

---

### Sources

- Code (read this session): aamatch/gamestart.py, engine.py, placement.py, wizard.py, setup_state.py, generator.py, manifest.py, setup_window.py; smoke/smoke_05_perf.py, smoke_24_drag_battery.py, smoke_15_lifecycle.py (docstring), smoke/run_smoke.sh; tests/test_detector_invariance.py.
- Data: aamatch/data/MANIFEST.json (parsed with python3.6).
- Planning records: .planning/PROJECT.md, ROADMAP.md, research/PITFALLS.md, research/ARCHITECTURE.md, research/SUMMARY.md, STATE.md, phases/02-*/02-RESEARCH-materialization.md + 02-RESEARCH-detection.md + 02-VERIFICATION.md, phases/08.3-*/08.3-15-SUMMARY.md + 08.3-16-PLAN.md + 08.3-16-SUMMARY.md, phases/04-qt-setup-window/04-RESEARCH-qt-window-architecture.md.
- Sibling Phase-9 research (not modified): 09-RESEARCH-docs-audit.md, 09-RESEARCH-help-ui.md.
