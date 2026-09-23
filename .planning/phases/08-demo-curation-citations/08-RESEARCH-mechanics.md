# Phase 8: Demo Curation & Citations — RESEARCH (mechanics & code integration)

**Researched:** 2026-09-24
**Scope:** Bundling mechanics + code integration ONLY (sourcing/candidate selection is the sibling research track)
**Method:** Every claim below is either **VERIFIED-BY-READING** (repo file + line read today) or **UNVERIFIED-RUNTIME** (needs a headless Windows-PyMOL smoke; exact script sketch included). No code was modified.

---

## Q1 — Current bundling pipeline & where the Phase-8 build script lives

### What 02-04 actually did (VERIFIED-BY-READING)

- The dev fixtures were built by a **throwaway git-ignored script** `tmp/build_fixtures.py` (now deleted; contract recorded in `.planning/phases/02-headless-game-engine/02-04-PLAN.md:69` and `02-04-SUMMARY.md:26,46,107-110`):
  1. PROGRAMMATICALLY emit SDF V2000 files (counts consistent **by construction**),
  2. derive manifest counts from the *same lists* that wrote the SDF,
  3. take `sha256` over the **written bytes in the same run** (`hashlib`),
  4. assemble the manifest via the pure stack (`make_container('manifest', payload)` + `write_json_atomic` → `aamatch/data/MANIFEST.json`),
  5. run under `python3.6` from repo root (WSL; no PyMOL involved in the build).
- Rule frozen in STATE.md:76 — **NEVER hand-edit an SDF after manifest creation; regenerate instead.**
- Current bundled data (VERIFIED): `aamatch/data/MANIFEST.json` (57 lines) = one container `{magic AAMATCH, version 1, kind 'manifest', data.manifest_version 1}` with ONE set `demo-dev-1` (tier `easy`, `license: ""`, `provenance: {}`) and 2 entries (`benzamide.sdf` 16 atoms/16 bonds, `acetate.sdf` 7 atoms/6 bonds, both `size_class: small`, `states_expected: 1`). Ligand files live flat in `aamatch/data/ligands/`; entry `file` values are package-relative forward-slash (`ligands/benzamide.sdf`).

### What must GENERALIZE for Phase 8

1. **Multi-set:** the builder must emit N sets (not one) into one MANIFEST.json `sets` list.
2. **Set-level fields become real:** `license` and `provenance` (currently `''`/`{}` placeholders) must be filled per set; `title` becomes user-facing (dropdown label).
3. **Counts are DERIVED, not constructed:** 02-04's "counts consistent by construction" is impossible for curated downloads — the molecule bytes come from outside. The anti-drift proof shifts to: sha256 pins the committed bytes; the derived counts (atom/bond/charge/states/flags/size_class) are cross-checked by the every-manifest-id smoke's REAL loads (SMOKE-02 shape). The builder should derive counts from the **same parser the engine trusts** — two viable routes:
   - **(A) WSL pure-python3.6 V2000 parser** (stdlib-only): read the SDF counts line + atom/bond blocks, derive `atom_count`, `heavy_atom_count` (non-H), `bond_count`, `bond_order_counts` (digit-string tally), `formal_charge_sum` (M CHG lines), `states_expected` (count `$$$$` records), element set for metal/halogen flags, `size_class` (bucket rule below). Fits the 02-04 precedent (python3.6, no PyMOL) and the opencode permission reality (no pip/conda; `AGENTS.md`, `opencode.json` bash rules).
   - **(B) In-PyMOL builder** (headless Windows PyMOL script, `run_smoke.sh`-style invocation): `cmd.load` each candidate file → `cmd.count_atoms` / `cmd.get_bonds` / `cmd.iterate(formal_charge)` / `cmd.count_states` / element scan → write the manifest using the pure stack (proven to import inside PyMOL — SMOKE-02 already does exactly that, `smoke/smoke_02_manifest.py:59-61`). **Most authoritative** (manifest counts can never disagree with what the engine will count) at the cost of a Windows boot per build run.
   - Recommendation: **(B) for count derivation, assembled + written by the same script** — it eliminates the "my parser disagrees with PyMOL's" failure class entirely; sha256 over file bytes in the same run; the pure `make_container`/`write_json_atomic` calls run inside PyMOL exactly as SMOKE-02 proves. Route (A) remains a fallback if a Windows boot per regeneration is too slow.
4. **Metadata per entry:** `protonation` (VERIFIED: `generator.py:683-700` accepts a string used verbatim OR a non-empty list of states → `rng.choice(sorted(...))`; manifest validator presence-checks only, `manifest.py:202-204`), `size_class`, `metal_present`/`halogen_present` (element-scan vs DETECT-03 lists `MG ZN FE CA MN CU NI CO CD` / `Cl Br I`, C-F excluded — `smoke_02_manifest.py:66-70`).

### Where the build script should live (VERIFIED facts)

- `tmp/` is entirely git-ignored (`.gitignore` line `tmp`) — fine for a throwaway, **wrong for a permanent, reproducible curation pipeline** (9 sets will be regenerated on any data fix).
- There is **no `scripts/` or `tools/` directory today** (checked; repo root listing).
- Purity gates do NOT reach outside the package: Gate A scans only `PURE_MODULES` (`tests/test_purity.py:211-226`), Gate D compiles only `aamatch/*.py` (`tests/test_purity.py:270-291`). A top-level `scripts/build_demos.py` is outside every gate by design.
- **Recommendation:** create a new top-level `scripts/` (committed) holding the Phase-8 bundler; keep it python3.6-safe stdlib-only so the WSL suite can py_compile it (add a small test or include it in a compile loop if desired); document its use in the plan. This replaces the 02-04 throwaway precedent with a durable capability — the curation pipeline IS a deliverable of this phase.

---

## Q2 — PDB → SDF conversion mechanics

### What the repo already decided (VERIFIED-BY-READING)

- `PITFALL 12` (`.planning/research/PITFALLS.md:295-304`): PDB files typically lack hydrogens AND ligand bond orders; PyMOL's own `h_add` docstring warns ligand valences may need manual correction (`[SRC editing.py:1216-1241]`). The policy decided there: **demo ligands should be SDF** (carries bond orders + explicit H) "or pre-processed with verified protonation, NOT raw PDB ligands + h_add". The ROADMAP phase-8 research note repeats it: "SDF-first for ligand chemistry".
- `FEATURES.md:22,160` / `SUMMARY.md:169`: "PDB without bond-order/CONECT info undermines the correct-valence requirement; SDF/MOL2 carry bond orders."

### In-PyMOL conversion tooling (VERIFIED from the local 2.5.0 source tree)

- **`cmd.get_sdfstr(selection, state=-1)` EXISTS in this build**: `pymol-src/modules/pymol/exporting.py:950-951` (`get_sdfstr` → `get_str('sdf', ...)` → `get_bytes` → the C layer). `cmd.save('x.sdf', ...)` is also supported (`exporting.py:808` supported-forms docstring; `savefunctions['sdf']` at `exporting.py:991`). So a headless PyMOL bundler can normalize/re-export any loaded selection to SDF text.
- **CAVEAT (chemistry, not API):** conversion does not *create* bond orders that the source lacked. A PDB-loaded ligand's bonds come from CONECT records (order-less) or distance heuristics; exported SDF would carry order-1 bonds everywhere — fatal for ring/π and amide detection. **PDB→SDF conversion inside PyMOL is therefore NOT a sourcing path for chemistry-correct ligands**; it is usable only for normalization of already-ordered input (e.g. re-export after cleanup) with human-approved preparation documented in DATA_SOURCES.md.
- **Open Babel is NOT in the allowed universe** (not shipped with pymol-open-source; would need user approval per AGENTS.md dependencies rule). Recommendation: skip it — prefer ready-made SDF sources (PubChem 3D / RCSB ligand pages serve ideal-gamma SDFs — sourcing researcher's domain to verify).

### Multi-state handling (the 04-04 question)

- **Probe-verified mechanics** (02-RESEARCH-materialization.md:68,630): a multi-record SDF loads as **one state per record** (`PROBE sdf.multistate OK states=2 atoms=16` — note `count_atoms` returned **16**, i.e. atoms are counted **across all states**), and re-loading into an existing name **appends a state** (`PROBE sdf.reload_append OK states_after=2`).
- **Engine behavior:** the package `cmd.load` path in `engine._ligand_data_for` (`engine.py:239-257`) does **NOT** assert `count_states` — only the `ligand_content` string path does (`engine.py:234-238`). So a multi-state bundled file would NOT be refused by the engine at game time; it would silently produce a multi-state `_aam_lig` object (and `count_atoms`/bounding-sphere math would see the union). The safety net that catches this is **SMOKE-02's `count_states == states_expected` assert** (`smoke_02_manifest.py:135-137`).
- **Resolution of the ROADMAP's "state 1 vs collapse" note:** the bundler must guarantee **exactly one molecule record per SDF file** (split multi-record sources into per-record files or refuse), `states_expected: 1` for every curated entry. "State 1 vs collapse" then becomes moot at runtime — the decision happens at curation time (pick ONE conformer/protonation state per entry) and is recorded in the GATE proposal. **No engine change needed.**
- Altloc policy: N/A for SDF (no altloc concept in the format; SDF/MOL2 loads produce `alt=''` per 02-RESEARCH-materialization.md:295).

### UNVERIFIED-RUNTIME items for Q2

1. `hasattr(cmd, 'get_sdfstr')` in the actual Windows build (source says yes; the `read_mol2str` precedent shows API surface can differ — `engine.py:220-227` guards it). Smoke sketch: one-liner probe script printing `hasattr(cmd,'get_sdfstr')`, `hasattr(cmd,'read_pdbstr')`, then `get_sdfstr` round-trip of benzamide (load → export → re-load → compare atom/bond counts).
2. Whether `cmd.get_sdfstr` writes a proper V2000 counts line + `M CHG` (probe: export acetate, re-load, assert formal_charge_sum == -1 via `cmd.iterate`).

---

## Q3 — Water/solvent stripping & what "committed scene" means for criterion 4

### How the game consumes demo data today (VERIFIED-BY-READING)

- `engine.new_game` (`engine.py:299-341`): parses MANIFEST.json, filters rows by `demo_set_id` ('' = all sets), builds `ligand_data` per row (`_ligand_data_for`), calls the pure generator. **Only ligand rows are consumed.**
- `placement.materialize` (`placement.py:234-428`): loads ONLY each molecule's ligand file (`_aam_lig*`) + AA fragments (`_aam_aa*`). Nothing else is ever materialized.
- There is **no code path that loads a bundled "scene"** (protein/ions/water). `game_file.py` is a separate container for saved games (04-03 decision; `game_file.py:254` upload-side note). Curated demos do NOT go through game_file.

### What criterion 4 can therefore mean

"on a ligand+ions+water demo, Cleanup leaves exactly the original object set" — given the data model, the **shipped artifact is still just the ligand SDF** (a demo *derived from* a ligand+ions+water complex; the complex is the provenance, cited in DATA_SOURCES.md). The **field test is a smoke-shaped rehearsal of PITFALL 13**: a messy user scene coexists with the game, and Cleanup restores it exactly.

### Where stripping happens (VERIFIED reasoning)

- Waters/ions never enter a bundled SDF in the first place if sources are ready-made SDFs (they don't carry solvent). The "strip waters/solvent before bundling" note (PITFALLS.md:378) applies to any PDB-derived route: strip at **bundling time** — committed files must be ligand-only. Add a bundler assertion: refuse files whose element set suggests solvent/metal contamination unless the entry's flags declare it (e.g. a metal-bearing ligand is legitimate — the flag system exists for it; waters are not).
- **No load-time stripping exists or is needed** — the engine loads exactly one ligand object per molecule; there is nothing to strip at load.

### What must be BUILT for the field test (VERIFIED gaps)

- **Nothing in engine/placement**: `cleanup_game_objects` is prefix-only (`placement.py:458-471`, `GAME_PREFIX = '_aam_'` at `geometry.py:81`) and the materializer only ever creates `_aam_*` names. Cleanup already cannot touch user objects.
- **Build = a new smoke part** (see Q6/Q7): construct a messy scene in the smoke (protein fragment + waters + ion — inline PDB string via `cmd.read_pdbstr`, the same string-family as the probe-proven `cmd.read_sdfstr` (`pymol-src/modules/pymol/importing.py:931-959` family; **UNVERIFIED-RUNTIME**: `hasattr(cmd,'read_pdbstr')`), or `cmd.load` of a tiny committed PDB), snapshot `cmd.get_names('objects')` + per-object atom counts, run the curated-set game flow, `cleanup_game_objects()`, assert restoration (exact shape below in Q7).
- **Design decision for the GATE/human:** ship context complexes as bundled files or not? Shipping them (a) adds citation burden ×9, (b) is OUTSIDE the manifest schema (`format: sdf|mol2` only), (c) serves no runtime consumer. **Recommendation: do NOT ship context complexes**; document them in DATA_SOURCES.md as provenance. If the human wants a visual "original scene" for the demo, that is a new bundled-file class requiring its own policy — flag it as an explicit GATE decision, default no.

---

## Q4 — Setup dropdown tier grouping

### Today (VERIFIED-BY-READING)

- Pure: `setup_form.manifest_sets(payload)` (`setup_form.py:124-136`) → `[(set_id, title, tier)]` **sorted by set_id**, `.get` fallbacks (title→set_id, tier→''). Pinned by `tests/test_setup_form.py:231-254` (`TestManifestSets`).
- Qt: `setup_window._populate_demo_sets` (`setup_window.py:325-352`) → flat `QComboBox.addItem(label, set_id)` with tier suffix in the label; failure path = placeholder `'(no bundled sets)', ''` + note. Selection is read back via `currentData()` (`setup_window.py:519`), restore via `findData` (`552-558`), Randomize preserves `currentData` (`681`), and **two `known_ids` builders iterate ALL items' `itemData`** (`927-928`, `1003-1004`).

### Qt mechanism (VERIFIED against Qt 5.12.12 docs; runtime check still advised)

- `QComboBox.insertSeparator(int index)` — in Qt since 4.4, present in the 5.12.12 docs (fetched 2026-09-24). Separator rows are non-selectable in the popup. The separator item carries **no UserRole data** (`itemData` returns invalid QVariant → `None` in PyQt5).
- Alternative: QComboBox's **default model IS a QStandardItemModel** (stated in the QComboBox ctor docs), so disabled "header rows" are possible: `combo.model().item(row).setFlags(flags & ~Qt.ItemIsEnabled)`. Richer (grey header text) but more surface area; **UNVERIFIED-RUNTIME under offscreen**.
- **Recommendation: `insertSeparator` between tier groups** — minimal diff, no model juggling; tier identity stays in the label text (e.g. `title (tier)` as today) so the grouping is also readable in the closed box's selected item.

### Integration hazards found (VERIFIED-BY-READING — these are the real code changes)

1. **`known_ids` pollution:** `str(self.demo_combo.itemData(i))` over all items turns a separator's `None` into the **string `'None'`** in `known_set_ids` → `build_state`'s membership check (`setup_form.py:88-93`) would then accept `demo_set_id == 'None'`. Both sites (`setup_window.py:927-928`, `1003-1004`) must skip separator/None-data rows. Cleanest: introduce one window helper (e.g. `_known_demo_set_ids()`) used by both call sites AND by smoke_11's mirror loops (`smoke/smoke_11_window.py:729-730`).
2. **`setCurrentIndex(0)` fallback can land on a separator** (`setup_window.py:558` when a saved set_id is stale): `currentData()` → `''` = "all sets" **silently**. Must fall back to the first *selectable* row instead of index 0.
3. **`collect_state`/`_on_randomize`** (`519`, `681`): safe only as long as the current index is never a separator — guaranteed by popup selectability + fix #2. Worth an assertion comment, not new code.
4. **smoke_11 expectations shift:** findData-based selections keep working; any count/position assumptions and the itemData loops need updating.

### Dependency direction & tests (VERIFIED)

- Grouping must live in the **pure tier**: add e.g. `manifest_sets_grouped(payload)` (+ a `TIER_ORDER` constant) to `setup_form.py` (already PURE, `tests/test_purity.py:99-103`); the Qt tier consumes grouped rows and inserts separators at group boundaries. Keep `manifest_sets` **byte-identical** (pinned tests) unless the plan explicitly revisits them.
- Tier vocabulary needs a canonical decision (open decision below): ROADMAP GEN-06 slots are Easy ×3 / Hard ×3 / Challenge / Very challenging ×2 — canonical manifest strings are likely `'easy' | 'hard' | 'challenge' | 'very challenging'`, but today `tier` is a **freeform unvalidated string** (`manifest.py:_check_set` checks only `set_id` + `entries`).

---

## Q5 — Manifest validation of license/provenance

### Today (VERIFIED-BY-READING)

- `manifest._check_set` (`manifest.py:171-188`) validates ONLY: `set_id` (non-empty string) and `entries` (list). **`tier`, `title`, `license`, `provenance` have ZERO validation** — not even presence. The dev set carries `license: ""`, `provenance: {}` (`MANIFEST.json:46-47`), and `tests/test_manifest.py:88-101` documents them as "Phase-8 placeholder fields — preserved, not validated" (P9 passthrough preserves unknown/extra fields, `manifest.py:135-138`).
- Entry-level `provenance` does not exist in the 14-key schema (frozen 02-03; `manifest.py:68-73`), but P9 means an entry could carry one and it would be **preserved and enumerated** (`enumerate_entries` copies the whole entry dict, `manifest.py:298-314`).

### Does filling require schema changes? — NO (VERIFIED)

Filling license/provenance/tier/title is purely a DATA change; the container stays version 1; refuse-newer/accept-older is untouched. **Adding new REQUIRED runtime validation would violate accept-older** (the current dev set's `license=''` would suddenly fail) unless gated behind a `manifest_version: 2` bump — not worth it.

### Recommendation

- **Do not touch the runtime validator.** Truthfulness is the human GATE's job (GEN-06/HELP-02 protocol) + DATA_SOURCES.md; a machine check that `license != ''` proves nothing about truthfulness and risks the additive-only contract.
- **Add repo-side data tests instead** (no purity impact — they read a bundled data file): every curated set has non-empty `license`/`provenance`/`tier` in the approved vocabulary; every bundled ligand file referenced by the manifest exists and sha256-matches (the WSL-side half of what SMOKE-02 proves at runtime). This can live in a new `tests/test_demo_data.py` (plain unittest, reads MANIFEST.json via the pure stack).
- **Provenance shape (convention, not schema):** recommend a documented dict per set, e.g. `{source_url, pdb_id, doi, license, license_url, fetched, notes}` — recorded as the DATA_SOURCES.md cross-reference. If per-entry provenance is desired in saved-game payloads, entries could carry an extra string key — see the open decision below about `generator.py:864`.
- **Payload provenance hook (VERIFIED, currently vestigial):** `generator.py:864` writes `'provenance': picked.get('provenance', '')` into every payload ligand block (frozen ligand-block key, `level_spec.py:23-24`; pinned `''` for synthetic rows, `tests/test_generator.py:746-751`; `generator.py:742-743` says "or '' until Phase 8 curates it"). Phase 8 must DECIDE: leave payloads with `''` (citations live in the manifest + DATA_SOURCES.md only) **or** put a per-entry provenance string in curated manifest entries so it flows into payloads/game files/checkpoints (additive; `level_spec` parse never type-checks the field — `level_spec.py:173-214` only checks grid structure). Default recommendation: keep `''` in payloads for Phase 8 (smallest blast radius); the manifest + DATA_SOURCES.md carry the citations.

---

## Q6 — Every-manifest-id smoke extension (SMOKE-02 and friends)

### Hardcoded drift points to fix (VERIFIED-BY-READING)

| Site | Today | Phase-8 change |
|---|---|---|
| `smoke/smoke_02_manifest.py:78-79` | `check('manifest parse', len(entries) == 2, ...)` | data-relative (e.g. `>= 2`) + set/tier coverage asserts |
| `smoke/smoke_03_generate.py:100-101` | `len(entries) == 2` | same |
| `smoke/smoke_05_perf.py:181-189` | pins `biggest['entry_id'] == 'benzamide'` | make data-relative (it already cross-checks `max(heavy)`; restrict candidates like smoke_03/04 do, or drop the literal) |
| `smoke/smoke_03_generate.py:198`, `smoke/smoke_04_e2e.py:222` | candidates explicitly restricted to the benzamide row | already manifest-growth-proof — no change needed |

The generic per-entry loop in smoke_02 (resolve → sha256 → load → atoms/bonds multiset/charge/states/flags → delete-in-finally → leak check, `smoke_02_manifest.py:86-162`) is **already exactly the criterion-4 "every demo loads through the path helper with counts matching the manifest" machine** — extension is mostly coverage assertions, not new mechanics:
- per-set: every curated set has ≥ 1 entry; the ~9 sets across the canonical tiers exist;
- optionally: `metal_present`/`halogen_present` TRUE appears at least once across the bundle (curation goal: interaction diversity — GEN-06), so the flag cross-check exercises both branches.

### Runtime budget (VERIFIED reasoning)

- Smoke cost is dominated by the PyMOL boot (~30–60 s recorded for prior smokes); per-entry loads are ms-scale. ~9 sets × 2–4 entries ≈ 20–40 entries is well inside the default `TIMEOUT=120` (`run_smoke.sh:10`); pass 180 like 02-04 did (`02-04-PLAN.md:99`). A new smoke file works with **zero runner changes** — the runner derives SMOKE-NN from the basename (`run_smoke.sh:11-13`).

### The messy-scene cleanup field test — new smoke part or new smoke

Recommend a **new smoke (e.g. `smoke_21_demo_cleanup.py`)** rather than growing smoke_02, keeping each smoke's verdict surface small (house pattern: one concern per smoke). Sketch (UNVERIFIED-RUNTIME as a whole; every primitive it uses is individually probe/source-verified):

```python
# smoke_21_demo_cleanup.py — criterion 4 field test (PITFALL 13 in the field)
# PART A: messy scene (inline PDB string — read_pdbstr, same family as the
#         probe-proven read_sdfstr; guard hasattr(cmd,'read_pdbstr') and
#         fall back to cmd.load of a tiny committed fixture if missing)
#   cmd.read_pdbstr(MESSY_PDB, 'user_complex')   # protein piece + 3 HOH + 1 Na+
#   pre_names = cmd.get_names('objects'); pre_counts = {n: cmd.count_atoms(n)}
# PART B: pick the curated ligand+ions+water-derived set's SDF row from the
#   manifest; engine.new_game(setup, seed) -> placement.materialize(payload,0)
#   assert game objects exist and are ALL '_aam_*'
# PART C: placement.cleanup_game_objects()
#   post = cmd.get_names('objects')
#   assert post == pre_names                     # exact name set
#   assert all(cmd.count_atoms(n) == pre_counts[n] for n in pre_names)
#   assert no atom anywhere carries segi 'AAM' outside game objects (cheap extra)
# final marker: === SMOKE-21 PASS ===
```

---

## Q7 — Cleanup field test details (what Cleanup deletes / preserves)

- **Deletes:** every object whose name starts with `_aam_` (`placement.py:458-471`). That's the whole rule — no hetatm/water/chemical selectors ever.
- **Preserves:** everything else, by construction. `_cleanup_now` (`setup_window.py:847-862`) additionally pops any GameWizard first.
- Cleanup is also invoked mid-flow by `engine.advance_level` (`engine.py:648-680`, cleanup BEFORE re-materializing the next level) and by `gamestart` (`gamestart.py:430,514`, cleanup-first restart law).
- **Field-assertion shape (VERIFIED precedent):** `smoke_04_e2e.py:477-486` already asserts `post_names == pre_names and not any(n.startswith(GAME_PREFIX))` after cleanup. The Phase-8 field test adds (a) a *messy* pre-game scene (waters/ions present — the exact prior-art hazard class), and (b) **per-object atom counts** before/after (Pitfall 13's own suggested proof: "after cleanup, `cmd.count_atoms(target)` == pre-Start count, and the object-name list minus `_aam_*` equals the original list", PITFALLS.md:339).
- Follow the smoke-authoring discipline: never call cmd APIs that may throw inside an eager check-detail string; tolerance 1e-6 for any coordinate compares (03-04/02-15); assert INSTANCES not name sets where identity matters (03-05) — for cleanup the name-set comparison IS the assertion (pre-registered snapshot), which is the sanctioned pattern.

---

## Q8 — Size-class supply analysis (what the sourcing researcher must target)

### The bucket machine (VERIFIED-BY-READING)

- Difficulty buckets: `bucket_index = (L * 3) // D` (`generator.py:167`); targeted classes per D: D=1→{small}; D=2→{small, medium}; **D≥3 targets all three classes** across levels (D=3: one level each; D=10: 4 small / 3 medium / 3 large levels).
- `_select_pool` (`generator.py:603-629`): fallback to the NEAREST non-empty bucket **only when the target pool is EMPTY** (ties → smaller/easier rank). A pool that is non-empty but smaller than `molecules_per_level` does **NOT** fall back → `GenerationError` naming the shortage (`generator.py:809-818`).
- Distinctness is **per level** (`taken` resets each level, `generator.py:802`), so the binding constraint is `len(pool) >= molecules_per_level` for every bucket targeted by the game's D (after fallback).
- Clamps: `molecules_per_level ∈ [1, 10]` (`setup_state.py:46`), `difficulty_levels ∈ [1, 10]` (`setup_state.py:50`).
- Buckets by heavy atoms: small < 25 ≤ medium < 60 ≤ large (`generator.py:121-122`), explicitly "tuned when the Phase-8 manifest exists" (`generator.py:118-120`) — **re-tuning SIZE_S1/S2 is a legitimate Phase-8 task** (invariant tests pin monotonicity, not values).
- The pool is GLOBAL across sets when `demo_set_id = ''` (all sets); a single-set game pools only that set's entries — so size-class balance matters **manifest-wide**, and each individual set should still span enough classes for standalone use.

### Consequences for curation targets

- Full no-refusal coverage at m=10, D=10 needs **≥ 10 distinct entries per size class**. With ~9 sets that means ~3–4 entries per set (~27–36 total ligands) balanced ~⅓ per class — a real curation-cost decision.
- Minimum viable floor: ≥ 3 entries per class (supports the default m=2 plus headroom at D=3+); below that, m≥3 games at the thin class refuse fail-closed (message already names the shortage).
- **Recommendation to the sourcing researcher:** ~9 sets × 3 entries = 27 ligands, distributed roughly 9 small / 9 medium / 9 large manifest-wide, with Easy sets biased small, Hard biased medium, Challenge/Very-challenging biased large (tier fit); at least one metal-bearing and one halogen-bearing ligand somewhere in the bundle (GEN-06 interaction diversity + exercises the flag branches in SMOKE-02). Record the final SIZE_S1/S2 re-tune decision (if any) as an explicit plan task with invariant tests re-run.

---

## Q9 — Phase-8 plan structure recommendation

Constraint: the GATE (propose → human-approve → fetch/commit) blocks all *content* work but not *machinery* work. Two workstreams run in parallel; content lands only after approval.

**Recommended plan sequence (waves):**

1. **Wave 1 (machinery, parallel):**
   - `08-01` Bundling pipeline: committed `scripts/` builder (generalizes the 02-04 contract to multi-set + real license/provenance), dry-run proven on the existing dev set (no fetching), plus `tests/test_demo_data.py` data-integrity tests. Files: `scripts/build_demos.py` (new), `tests/test_demo_data.py` (new).
   - `08-02` Dropdown tier grouping: pure `manifest_sets_grouped` + `TIER_ORDER` in `setup_form.py`; `_populate_demo_sets` separators + separator-guard fixes at `setup_window.py:558, 927-928, 1003-1004`; test updates (`test_setup_form.py`); T1b offscreen verify (extend smoke_11 or new smoke). Files: `aamatch/setup_form.py`, `aamatch/setup_window.py`, `tests/test_setup_form.py`, `smoke/smoke_11_window.py`.
   - `08-03` Smoke de-hardcoding: smoke_02/03/05 data-relative fixes (independent of curated data landing). Files: `smoke/smoke_02_manifest.py`, `smoke/smoke_03_generate.py`, `smoke/smoke_05_perf.py`.
2. **Wave 2 (GATE):**
   - `08-04` [GATE] Proposal document: all ~9 candidates with IDs/sources/rationale/tier/size-class/protonation/multi-state policy per the frozen schema; **human approval recorded before ANY fetch** (UAT checkpoint; DETECT-03 revisit decision recorded here too). Files: `.planning/phases/08-demo-curation-citations/08-PROPOSAL.md` (or `docs/` staging) — a planning artifact, not shipped code.
3. **Wave 3 (per-set bundling, after approval — one small plan per set or per tier batch):**
   - `08-05..08-13` fetch → bundle → regenerate MANIFEST.json → run SMOKE-02 per set; each plan tiny and independently revertible. Files: `aamatch/data/ligands/*.sdf`, `aamatch/data/MANIFEST.json`, `scripts/build_demos.py` (invocations), per-set DATA_SOURCES.md sections.
4. **Wave 4 (consolidation):**
   - `08-14` SMOKE-02 extension (tier/coverage/flag-branch asserts) + `smoke_21_demo_cleanup.py` messy-scene field test. Files: `smoke/smoke_02_manifest.py`, `smoke/smoke_21_demo_cleanup.py` (new).
   - `08-15` DATA_SOURCES.md consolidation (`docs/DATA_SOURCES.md`, DETECTION_THRESHOLDS.md-style gate doc with per-file provenance/license + approval record).
   - `08-16` (conditional) SIZE_S1/S2 re-tune + size-distribution invariant updates if the real ligand sizes demand it. Files: `aamatch/generator.py`, `tests/test_generator*.py`.
5. **Wave 5:** `08-17` [HUMAN] GUI checkpoint — dropdown grouped by tier in the real viewer; full regression battery (WSL suite + all smokes).

Rationale: the GATE plan sits at the earliest point where the proposal can be *validated* by the pipeline dry-run; per-set plans keep every fetch/commit human-reviewable; consolidation waits for all content.

---

## Open questions / decisions for the GATE & planner

1. **Multi-state policy (resolve the ROADMAP note):** research recommendation = one molecule record per file, `states_expected: 1`, conformer/protonation chosen at curation time. Confirm or override.
2. **Tier vocabulary:** canonical manifest strings for the 4 tiers (`easy`, `hard`, `challenge`, `very challenging`?) and what to do with the legacy dev set's `easy` tier (keep it listed under Easy, or exclude `demo-dev-1` from the curated list?). Note `_populate_demo_sets` lists ALL sets — decide whether the dev set remains user-visible post-Phase-8.
3. **Ship context complexes?** Default no (see Q3); the messy scene lives in the smoke only.
4. **Payload provenance (`generator.py:864`):** keep `''` in saved-game payloads (recommended) or add entry-level provenance strings.
5. **SIZE_S1/S2 re-tune:** in scope or not (Q8).
6. **DETECT-03 provisional thresholds:** STATE.md:70 marks them PROVISIONAL pending the Phase-8 dataset revisit — any threshold change is a DETECTOR_VERSION bump event (never a silent edit). The GATE must record whether the curated dataset triggers the revisit (e.g. first real metal/halogen ligands).
7. **Entry counts per set:** ~3 per set (27 total) vs the ≥10/class ideal (Q8) — a curation-cost tradeoff the human should size.
8. **`read_pdbstr` availability** (UNVERIFIED-RUNTIME): if missing in the build, the messy-scene smoke falls back to `cmd.load` of a tiny committed fixture file (which then needs its own DATA_SOURCES.md line or must be synthetic — prefer inline string if available).

## Sources

### Primary (VERIFIED-BY-READING, repo)
- `aamatch/manifest.py` (whole file), `aamatch/data/MANIFEST.json`, `aamatch/setup_form.py:124-136`, `aamatch/setup_window.py:289-352, 510-570, 672-683, 920-940, 995-1019`, `aamatch/engine.py:130-341, 640-680`, `aamatch/placement.py:1-471`, `aamatch/geometry.py:81,105,191-206`, `aamatch/generator.py:110-175, 540-649, 683-700, 742-743, 750-883`, `aamatch/level_spec.py:20-31, 128-214`, `aamatch/setup_state.py:46-50`, `aamatch/paths.py`, `aamatch/__init__.py`
- `smoke/smoke_02_manifest.py`, `smoke/run_smoke.sh`, `smoke/smoke_03_generate.py:99-101,198`, `smoke/smoke_04_e2e.py:196-222, 477-486`, `smoke/smoke_05_perf.py:180-189`, `smoke/smoke_11_window.py`
- `tests/test_purity.py:99-116, 211-291`, `tests/test_manifest.py:49-120`, `tests/test_setup_form.py:231-254`, `tests/test_generator.py:746-751`
- `.planning/ROADMAP.md:210-223, 242-260`, `.planning/REQUIREMENTS.md:35,75`, `.planning/STATE.md:70,76-77,91-96,146-147,194,239,336`
- `.planning/phases/02-headless-game-engine/02-04-PLAN.md`, `02-04-SUMMARY.md`, `02-RESEARCH-materialization.md` (probe receipts §12.1)
- `.planning/research/PITFALLS.md` (Pitfalls 11-14, §demos), `STACK.md`, `FEATURES.md`, `SUMMARY.md`
- `pymol-src/modules/pymol/exporting.py:664-676, 795-815, 950-994` (SDF writer); `.planning/phases/01-bootstrap-pure-foundation/01-RESEARCH-plugin-install.md` (copytree/zip shipping of `data/`); `docs/DETECTION_THRESHOLDS.md` (gate-doc precedent)
- Qt 5.12.12 QComboBox docs (webfetch 2026-09-24): `insertSeparator` (since 4.4), default model = QStandardItemModel, `itemData` invalid-QVariant contract.

### UNVERIFIED-RUNTIME (needs headless Windows PyMOL)
1. `hasattr(cmd, 'get_sdfstr')` + SDF round-trip (orders + M CHG) — probe sketch in Q2.
2. `hasattr(cmd, 'read_pdbstr')` + inline messy-scene load — probe sketch in Q6.
3. QComboBox separator behavior under `QT_QPA_PLATFORM=offscreen` (itemData None-ness, popup non-selectability) — T1b extension of the smoke_11 pattern (04-01-SUMMARY verdict: PASS platform=offscreen).

## Handoff to planner

**Candidate plans (files_modified):**

| Plan | Scope | files_modified |
|---|---|---|
| 08-01 | Bundling pipeline + data-integrity tests (dry-run on dev set) | `scripts/build_demos.py` (new), `tests/test_demo_data.py` (new) |
| 08-02 | Dropdown tier grouping (pure grouping + Qt separators + hazard fixes) | `aamatch/setup_form.py`, `aamatch/setup_window.py`, `tests/test_setup_form.py`, `smoke/smoke_11_window.py` |
| 08-03 | Smoke de-hardcoding (data-relative entry counts / largest-entry) | `smoke/smoke_02_manifest.py`, `smoke/smoke_03_generate.py`, `smoke/smoke_05_perf.py` |
| 08-04 | [GATE] Proposal + human approval checkpoint | `.planning/phases/08-demo-curation-citations/08-PROPOSAL.md` (planning artifact) |
| 08-05..08-13 | Per-set fetch/bundle (after approval; ~9 small plans or per-tier batches) | `aamatch/data/ligands/*.sdf`, `aamatch/data/MANIFEST.json`, `scripts/build_demos.py` usage, DATA_SOURCES sections |
| 08-14 | SMOKE-02 extension + messy-scene cleanup field smoke | `smoke/smoke_02_manifest.py`, `smoke/smoke_21_demo_cleanup.py` (new) |
| 08-15 | DATA_SOURCES.md consolidation (gate-doc format) | `docs/DATA_SOURCES.md` (new) |
| 08-16 | (conditional) SIZE_S1/S2 re-tune + invariants | `aamatch/generator.py`, `tests/test_generator*.py` |
| 08-17 | [HUMAN] GUI checkpoint + full regression battery | none (verification-only) |

**Open design decisions the GATE/human must resolve:** multi-state policy (recommended: single-record files, states_expected=1); canonical tier strings + dev-set visibility; context-complex shipping (recommended: no); payload provenance `''` vs entry-level (recommended: keep `''`); size-class distribution & per-set entry counts; SIZE_S1/S2 re-tune scope; DETECT-03 provisional-threshold revisit trigger.
