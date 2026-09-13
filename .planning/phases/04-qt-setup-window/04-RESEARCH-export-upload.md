# Phase 4 Research: Generate-and-Export Game File + SDF/MOL2 Upload Path

**Researched:** 2026-09-13
**Domain:** versioned-container serialization (game file) + uploaded-molecule ingestion (cmd→pure pipeline)
**Confidence:** HIGH for all file:line-cited claims (all verified against actual source this session); MEDIUM/LOW where explicitly marked (UNVERIFIED items + probes listed in `open_questions`).

**Scope note:** This file covers the two genuinely new Phase-4 design problems: (1) the shareable game file (SETUP-08, consumed by Phase 7 PERSIST-02) and (2) the SDF/MOL2 upload path (SETUP-03). It deliberately does NOT cover the Qt window architecture itself — see sibling `04-RESEARCH-setup-form-seams.md`.

---

## game_file_design

### Recommendation: ONE JSON file, `AAMATCH` container, `kind='game'` (already reserved), full payload embedded

The `game` kind **already exists** in `KINDS = ('setup', 'level_spec', 'game', 'checkpoint', 'manifest')` — aamatch/persistence.py:37 (pin test: tests/test_persistence.py:67-70 `test_every_known_kind_accepted`). No KINDS change needed.

**Recommended `data` payload (new pure module, e.g. `aamatch/game_file.py`):**

```python
{
  "game_format_version": 1,      # NEW gate: refuse-newer / accept-older (GAME_VERSION const)
  "created_at": "2026-09-13T12:00:00",  # provenance, informational only (readers .get it)
  "generator": "AA-match",       # provenance, informational only
  "setup": {...},                # validated 7-field setup snapshot (validate_state output verbatim)
  "seed": 12345,                 # DUPLICATE of level_spec['seed'] for convenience; level_spec's is authoritative
  "level_spec": {...},           # the FULL generator payload verbatim (generator.py:874-879) -- THE TRUTH
  "ligand_files": {              # ONLY uploaded sets; bundled demo sets are NEVER embedded
     "uploads/mol-001.sdf": "<base64 of one SDF record>",
     "uploads/mol-002.mol2": "<base64 of one MOL2 segment>"
  }
}
```

**Load-side gate chain (Phase 7 reuses exactly this):**

1. `persistence.check_container(raw, 'game')` — canonical foreign/newer/misfiled refusals for free (persistence.py:61-88: `not an AA-match file` / `unsupported AA-match format version…Please update AA-match.` / `expected an AA-match game file, found kind=...`).
2. `game_format_version` refuse-newer / accept-older — mirror level_spec.py:106-114's exact pattern (missing/invalid → FormatError naming it; `> GAME_VERSION` → "unsupported game file version %d (expected <= %d). Please update AA-match.").
3. `parse_level_spec_dict(make_level_spec_container(data['level_spec']))` — the embedded spec re-runs **ALL** existing gates: container check, refuse-newer `format_version`, **exact-match `detector_version`** ("stale or newer game spec - regenerate it with a current AA-match generator", level_spec.py:116-121), int seed, structural minimums (level_spec.py:98-125). Nothing new to write.
4. `validate_state(data['setup'])` — re-validates the setup snapshot (setup_state.py:90-144; idempotent on already-valid dicts).
5. Embedded-ligand integrity: for each `ligand_files` entry, sha256(decoded bytes) must equal the matching payload molecule's `ligand.sha256` → mismatch = FormatError naming the file (reuses the manifest's 64-char-lowercase-hex discipline, manifest.py:94-97, 220-224).
6. Cross-check: every `level_spec` molecule whose `ligand.source == 'upload'` must have its `ligand.file` key present in `ligand_files` (fail-closed — an uploaded game without its molecules is unsolvable); every bundled (`source == 'demo'`) molecule must NOT have an entry (single meaning per source).

**Why one JSON file (not zip / not .pse+sidecar):**

| Option | Verdict | Reason |
|---|---|---|
| **Single JSON `game` container** | **RECOMMEND** | Atomic writer already exists and is purity-tested (`write_json_atomic`, persistence.py:91-113; temp+fsync+os.replace+guarded cleanup, the 01-02 atomic discipline); hand-editable educator files are a recorded feature (persistence.py:18-19 docstring); molecule files are small (small molecules → KBs), so base64's ~33% inflation is immaterial; zero new machinery; the whole payload round-trips byte-stably (`sort_keys=True, indent=2`; determinism pinned in tests/test_generator.py:791-797). |
| Zip container (game.json + ligands/) | Record only | Needs `zipfile` (pure, fine) but adds a second reader/writer path, loses hand-editability, and buys nothing at v1 molecule sizes. Revisit only if Phase 8 curated sets ever embed binaries. |
| Folder (game.json + ligand files beside it) | Reject | Breaks "shareable **file**" (spec.md:26); multi-asset sharing invites missing-file breakage. |
| `.pse` + sidecar | Reject for THIS file | That is Phase 7's **checkpoint** pattern (PyMOL session state is inherently `.pse`; PITFALLS.md:60 notes `.pse` stores absolute paths and must be re-resolved/verified in the persistence phase). The game file must be viewer-independent truth, and it must be writable from a pure path. |

**Version gates — the two-gate law maps cleanly:**

- Container `version` (header): refuse-newer only — persistence.py:80-83. Already handled.
- `game_format_version` (payload): refuse-newer only — NEW constant `GAME_VERSION = 1`, additive evolution, `.get()` defaults on read.
- `detector_version` (inside embedded level_spec): **exact-match**, both directions refused — level_spec.py:116-121, inherited by step 3 above. Never re-implement it at the game layer; never mirror it in the game header (single source of truth; mirroring invites the drift PITFALL 11.3 describes).

**Do NOT add a format tag anywhere else** — "the container header is the only format tag" is a recorded 01-05 decision (STATE.md Decisions; setup_state.py:12-14 docstring, P8 law).

---

## serialization_shapes

### The generator payload is ALREADY fully JSON-serializable — tuple keys are INPUT-SIDE ONLY

**Finding (HIGH, source-verified):** the tuple-key problem exists only in the `ligand_data` **input** contract, not in anything the generator emits.

- Input: `ligand_data` is keyed by `(set_id, entry_id)` **tuples** — `engine.new_game` builds it at engine.py:220-223 (`ligand_data[(row['set_id'], row['entry_id'])] = _ligand_data_for(row, names_before)`), and `generator._geometry_for` looks it up by tuple identity (generator.py:628-652: "EITHER a dict keyed by ``(set_id, entry_id)`` tuples … OR ONE shared … dict"). The alternative shared-dict form exists for single-ligand smokes (02-13 pattern).
- Output: each molecule records ligand identity **flat** — `'ligand': {'source', 'set_id', 'entry_id', 'file', 'sha256', 'protonation', 'provenance'}` (generator.py:851-861). No tuples anywhere in the emitted dict.
- Proof: the emitted payload survives `json.dumps(payload, sort_keys=True)` byte-stably for the same seed (tests/test_generator.py:791-797 `test_determinism_same_seed_byte_identical`) and round-trips `parse_level_spec_dict(make_level_spec_container(payload)) == payload` unchanged (tests/test_generator.py:807-810 `test_round_trip_through_phase1_gates`; the parse is passthrough P9 — level_spec.py:46-48, 95-97).

Full emitted shape with every key (generator.py:714-730, 793-879 — the authoritative enumeration):

```
payload = {
  'detector_version': 'det-1',          # DETECTOR_VERSION, level_spec.py:60
  'format_version': 1,                  # LEVEL_SPEC_VERSION, level_spec.py:61
  'seed': <int>,
  'levels': [
    { 'level_index': L,
      'difficulty': {'tier', 'grid_n', 'n_required_types', 'molecule_size_class'},
      'molecules': [
        { 'molecule_id': 'mol-001',
          'ligand': {'source', 'set_id', 'entry_id', 'file',
                     'sha256', 'protonation', 'provenance'},
          'required': {'mode': 'any'|'list', 'items': [{'type', 'count'}]},
          'placement': {'offset': [x, y, z]},        # JSON list (generator.py:863-865)
          'grid': {'n', 'slots': [{'slot_id', 'row', 'col', 'aa',
                                    'role', 'can_form': [..],
                                    'grid_pose': {'position': [x,y,z]}}]}  # JSON lists (generator.py:847-849)
        } ] } ] }
```

Every value is dict/list/str/int/float — `float(position[0])` coercions at generator.py:847-849 and 863-865 guarantee plain floats. **No serialization mapper is needed for the payload. No new pure-layer key-encoding contract is needed.** The only serialization work in Phase 4 is the `ligand_files` base64 map (stdlib `base64`, pure-compatible) and refusing non-JSON values loudly (`write_json_atomic` already does: `allow_nan=False` — persistence.py:98; NaN would die at save with a clear error, and the generator refuses non-finite inputs earlier anyway, generator.py:226-279, 834-839).

### One nearby trap: `charge_signs` is a Python SET

`capability.ligand_profile()` returns `'charge_signs'` as a **set** of `'+'`/`'-'` (capability.py:572-586 builds `signs = set()`, returned at capability.py:668). Sets are **not JSON-serializable**. This matters only if a profile is ever written into a file.

**Recommendation: do NOT embed profiles in the game file.** They are (a) recomputable from the embedded molecule bytes at import time, (b) recomputed live by the detector/Hint through the shared capability module at play time (DETECT-04 single-typing-home — capability.py:4-8), and (c) already consumed at generation time; the *decisions* they produced are durably recorded in the payload (`required`, `can_form`). Embedding them would create a second copy that can drift. If a future phase must serialize a profile, the canonical mapping is `sorted(charge_signs)` → list — record it there, not now.

---

## regenerate_vs_embed

### Recommendation: EMBED the full payload as truth; seed recorded for provenance only. Regeneration is NOT the mechanism.

**Why regeneration is rejected as the primary mechanism:**

1. **The engine's own law says so.** engine.py:13-15: "The LEVEL-SPEC PAYLOAD is the single source of truth: seed, grids, required, ligand refs, detector_version stamp. **Nothing re-derives from the seed at replay**; save/load is a Phase-7 persistence concern." The generator deliberately serializes slot assignments AND grid positions (generator.py:5-8, §7.2) precisely so replay never re-runs the RNG.
2. **Molecule selection depends on manifest CONTENTS, which change.** Selection draws from size-class buckets over the candidate rows sorted by `(set_id, entry_id)` (generator.py:597-625 `_select_pool`, 575 sort, 803-815 per-unit picks). The 02-08 fallback policy ("nearest non-empty bucket") makes the picked set sensitive to the *composition* of the manifest: Phase 8 curation (GEN-06, ~9 tier slots) or any manifest edit re-buckets the same `demo_set_id` → the **same seed silently produces a different game**. For bundled sets this is not hypothetical — Phase 8 is scheduled and will change MANIFEST.json contents.
3. **Uploaded sets make regeneration impossible.** The uploaded SDF/MOL2 bytes exist only on the exporting machine. An import-side regenerate needs the molecules to (a) load, (b) yield the same geometry, (c) yield the same profile — none guaranteed even with bytes present, and there are no bytes at all on a shared machine.
4. **PITFALL 11's solvability contract** (PITFALLS.md:278-280): "If detection thresholds/atom-typing change after levels were generated …, previously-generated levels may no longer be solvable. Regeneration must be forced when the detector changes (bump a detector-version stamp into generated files and refuse stale ones)." The exact-match `detector_version` gate is that stamp — it protects an *embedded* spec by refusing to import stale ones; it cannot protect a regenerate-from-seed scheme (regeneration would happily re-derive under NEW semantics and produce a *different but self-consistent* game — not the game that was shared).
5. **02-15 already proved the stale-refusal path for embedded specs** (02-15-SUMMARY.md:82: fresh `'det-1'` payload parses; `'det-0'` re-stamp refused with the exact "stale or newer" message). Import = replay of that proven gate chain.

**What the seed in the file is for:** provenance/debugging (a user report can be reproduced with `generate(seed, setup, candidates, …)` on the exporting machine) — it is already inside the embedded payload (`'seed'`, generator.py:877); the top-level duplicate is optional convenience. It must never be *required* by import.

**Hybrid explicitly rejected:** "payload for bundled sets, regenerate for uploads" — inverts the logic (uploads are exactly the case where regeneration is impossible).

---

## upload_pipeline

### SETUP-03 end-to-end, mapped onto existing functions (gaps marked ⚠)

**Step 0 — Qt file pick.** `pymol.Qt` → `QtWidgets.QFileDialog.getOpenFileNames(...)` (multi-select) — pattern proven in the reference plugins (Pymol-script-repo/plugins/vina.py:746 `QFileDialog.getOpenFileName`, plugins/outline.py:170 `getSaveFileName`; PyQt5 5.12.9 binding per windows-env-versions.md:26). Filter: `"Molecule files (*.sdf *.mol2)"`. Qt-tier only (Pitfall 1 discipline); everything below is cmd/pure.

**Step 1 — read + split (cmd tier → pure helper).** Read file text (UTF-8, binary-read + decode; also keep raw bytes for sha256). Detect format by extension ∈ `FORMATS = ('sdf', 'mol2')` (manifest.py:65) — refuse others fail-closed (SETUP-03 names SDF/MOL2 only; PDB is out of scope per REQUIREMENTS.md Out-of-Scope: no reliable bond orders).

- **SDF multi-record:** records are delimited by the `$$$$` terminator line — verified in the PyMOL source reader, pymol-src/modules/chempy/sdf.py:145-155 (`SDF.read` returns a record at `s[0:4]==r'$$$$'`; `SDF.write` appends `'$$$$\n'`). Python-side split at `$$$$` lines; each record (with its `$$$$`) = one molecule.
- **MOL2 multi-record:** split at `@<TRIPOS>MOLECULE` boundaries — the writer emits exactly this keyword (pymol-src/modules/chempy/mol2.py:34), and the C reader consumes restart-based segments (pymol-src/layer2/ObjectMolecule.cpp:8537-8540 `ObjectMoleculeMOL2Str2CoordSet(G, start, &atInfo, &restart)`). **Edge-case parsing (comment lines before the first keyword, casing) is UNVERIFIED** — see `open_questions` probe 1; fail-closed fallback is to accept single-molecule MOL2 only in v1.

**Step 2 — per-record extraction (cmd tier, the proven `engine._ligand_data_for` pattern).** For each record i:

1. `tmp = cmd.get_unused_name('_aam_tmp')`; load **from string** — `cmd.read_sdfstr(record, tmp)` / `cmd.read_mol2str(record, tmp)` — pymol-src/modules/pymol/importing.py:931-959 and 1038-1069 ("reads an MDL MOL format file as a string … PYMOL API ONLY"; mol2 variant: "load … without involving any temporary files"). Both route through `_cmd.load` with the `sdf2str`/`mol2str` loadables (importing.py:957-959, 1064-1068) → same C parser as file loads, so bond orders and `M CHG` formal charges round-trip identically. **No temp files needed at all.** (One-line probe recommended — probe 2.)
2. `records = [r for r in geometry.extract_game_atoms() if r['object'] == tmp]` — geometry.py:108-158, exactly engine.py:165-166.
3. `center, radius = geometry.bounding_sphere(records)` — geometry.py:191-229 (works for any loaded molecule; it only reads `'side' == 'lig'` records, and a bare molecule object loaded under an `_aam_`-prefixed name is side-lig by the prefix rule, geometry.py:144).
4. `lig_records, lig_bonds = engine._remap_ligand_bonds(records, [tmp])` — engine.py:114-141 (the 02-09-probed `cmd.get_bonds` walk-position→`index`→ID remap; geometry.py:48-58, 161-188). **Works for uploaded molecules unchanged** — nothing in it is manifest-specific.
5. `profile = capability.ligand_profile(lig_records, lig_bonds)` — capability.py:616-676. **Uploaded molecules get typed by the identical single typing home** (bond-order-derived aromatics incl. SDF order-4 markers / MOL2 `ar` spellings, capability.py:399-414; fail-closed donors; metal list; halogen donors). No new typing code.
6. `cmd.delete(tmp)` in a `finally`; assert scene unchanged (engine.py:173-180 pattern).
7. `assert cmd.count_states(tmp) == 1` fail-closed — because we split records ourselves (see multi_record_rules for why default `cmd.load` of a multi-record file would instead create N states in ONE object).

**Step 3 — manifest-entry-equivalent metadata (NEW PURE helper — the one genuinely new pure-side piece).** Build the 14-key row (schema: manifest.py:68-73) from the extracted data:

| Key | Source | Notes |
|---|---|---|
| `entry_id` | synthetic `'mol-001'`-style per set (generator's own convention, generator.py:852) | avoids title collisions/sanitization; keep the record's original title line as an extra `'title'` field (unknown keys are preserved everywhere — P9) |
| `file` | synthetic package-relative-style key `'uploads/mol-001.sdf'` | matches the manifest's forward-slash relative convention (manifest.py:253-275); it is a KEY into `ligand_files`, never a real path |
| `format` | `'sdf'\|'mol2'` from extension | manifest.py:214-218 rule |
| `sha256` | hashlib.sha256 of the **record text** (what gets embedded) | import verifies what it decodes, not the original file |
| `protonation` | `'as-recorded'` | same as both bundled fixtures (MANIFEST.json:21,41); never invent protonation claims (Pitfall 14) |
| `atom_count` | `cmd.count_atoms(tmp)` | engine.py:158 pattern |
| `heavy_atom_count` | count records with `elem != 'H'` | from the extracted records |
| `bond_count` | `len(lig_bonds)` | from the remapped bond block |
| `bond_order_counts` | tally `_bond_order_int(order)` over lig_bonds (digit-string keys) | capability.py:399-414 coercion; manifest.py:278-295 shape |
| `formal_charge_sum` | sum of `formal_charge` over records | SDF `M CHG` round-trips into records (capability.py:357-359 comment); MOL2 reader applies formal charges (`set_formal_charges = true`, ObjectMolecule.cpp:8539-8541). Accuracy is NOT load-bearing — `_charge_signs` has structure-based fallbacks (capability.py:572-613) |
| `states_expected` | 1 (per split record) | |
| `metal_present` / `halogen_present` | `profile['has_metal']` / `profile['has_halogen_donor']` | capability.py:673-674 |
| `size_class` | derive from `heavy_atom_count` via the generator's own buckets | `generator._candidate_class` (generator.py:578-596) already falls back to `heavy_atom_count` with SIZE_S1=25/SIZE_S2=60 — computing the field explicitly keeps rows manifest-shaped and future-parseable |

`set_id = 'uploaded'` (module constant). Validate each finished row with a pure function (reuse the manifest entry rules by calling `manifest._check_entry`-equivalent logic or a thin wrapper — the checks are dict-level and pure, manifest.py:191-295).

**Step 4 — feed the generator via the EXISTING seam.** `engine.new_game(setup, seed, candidates=<uploaded rows>)` — the candidates override already exists (engine.py:183, 208-214: builds rows locally, checks only non-empty `set_id`/`entry_id`, never calls `parse_manifest_dict`). `generate()` re-sorts rows defensively by `(set_id, entry_id)` (generator.py:540-575) and consumes them unchanged. Size-class bucketing/fallback applies to uploads identically (generator.py:597-625). **No generator changes.**

**Step 5 — ligand_data for uploads.** ⚠ **GAP:** `engine._ligand_data_for` hardcodes `package_data_path('data', row['file'])` (engine.py:155-157) — an uploaded record's synthetic `'uploads/mol-001.sdf'` would resolve into the package dir and fail. **Fix (additive):** optional `ligand_content=None` parameter on `new_game` (dict: synthetic file key → molecule text). In `_ligand_data_for`: if the row's `file` is in `ligand_content` → `read_sdfstr/read_mol2str` from the string (no package path, no disk); else the existing `cmd.load` path, byte-identical for demo sets. Default `None` keeps every existing call site and test unchanged.

**Step 6 — materialization for uploaded payloads.** ⚠ **GAP:** `placement.materialize` hardcodes `to_windows_path(package_data_path('data', ligand['file']))` (placement.py:304-306). **Same additive fix:** optional `ligand_content=None` param; when `ligand['file']` is a key → `read_sdfstr/read_mol2str` into the fresh `get_unused_name('_aam_lig')` name; else current path. **This is not deferrable to Phase 7** — Phase 4's own Start-after-upload needs it (a payload whose ligands are synthetic keys cannot materialize from the package dir).

> ⚠ **Hazard to record:** `os.path.join` silently discards the package prefix for an absolute third component (`os.path.join('/pkg','data','/abs/x.sdf') → '/abs/x.sdf'` — verified this session under python3.6). If uploads ever stored absolute paths in `ligand.file`, materialize would "work" on the exporting machine and break on every other machine — the worst kind of portable-looking bug. The synthetic-key + embedded-content design makes absolute paths structurally impossible; also keep rejecting absolute values in the uploaded-row validator (reuse manifest.py:267-275's checks).

**Extensibility seam for Phase 7:** the same `ligand_content` dict, populated by base64-decoding `ligand_files`, is the entire import-side mechanism. Phase 4 should land the pure-side encode/decode helpers (`base64` is stdlib; purity-gate compatible) + unit tests so Phase 7 only wires the decode → materialize call.

**EXT-04 boundary:** the fail-closed minimum only — format whitelist, non-empty split, per-record single state, count>=1, sha256 integrity, manifest-shaped row. A full user-set validator (valence checking, protonation inference, chemistry warnings) is **EXT-04, deferred to v2** — do not build it now.

---

## multi_record_rules

### Verified behavior of the underlying readers (C source)

- **Default `cmd.load` of a multi-record SDF (or multi-`@<MOLECULE>` MOL2) creates N STATES in ONE object**, not N objects: the loader loop takes `restart` from the parser and does `repeatFlag = true; start = restart; frame = frame + 1` (pymol-src/layer2/ObjectMolecule.cpp:8649-8653), appending each record as a new CoordSet ("read through molecule N" at :8627-8637). With `multiplex > 0` records become separate objects instead (:8654-8658) — `cmd.load(..., multiplex)` default is `multiplex=-2` (importing.py:724-725).
- N-states-in-one-object **violates the game's STATE-1-ONLY convention** (geometry.py:27-29: "The game keeps single-state objects …; every read pins state 1") and would silently play molecule 1 while showing the file's other records as hidden states.

### Recommended v1 rules

1. **One uploaded FILE = one set contribution; records within the file = molecules.** Both natural readings of "a set of small molecules" (spec.md:14) are supported: multi-select several single-molecule files, or one multi-record SDF.
2. **Split in Python, not via multiplex.** Python-side SDF splitting at `$$$$` (format verified, sdf.py:145-155) yields per-record strings — which is exactly what embedding and per-record `read_sdfstr` need; `multiplex=1` would give objects named by record title but no per-record strings and uncontrolled naming. Each split record loads via `read_sdfstr` into its own `get_unused_name('_aam_tmp')` object → 1 object / 1 state, convention-compliant.
3. **SDF multi-record: supported.** MOL2 multi-record: **probe first** (open_questions 1); fail-closed fallback = v1 accepts single-molecule MOL2 per file and refuses multi-`@<TRIPOS>MOLECULE` files with a message naming the file and record count.
4. **`states_expected = 1` per split record**, and `cmd.count_states(tmp) == 1` asserted fail-closed after each `read_*str` (guards a malformed record that smuggles an inner record).
5. **Empty/degenerate record → refuse** naming file + record index (fail-closed minimum; full validation is EXT-04 v2). Zero records total → refuse before generation ("zero ligand candidates" message class already exists, engine.py:216-218).
6. **Uniqueness by construction:** synthetic `entry_id`s (`mol-001`…) per uploaded set; original record titles kept as extra fields. The generator's distinct-pick dedup keys on `(set_id, entry_id)` (generator.py:803-807) — synthetic ids cannot collide.
7. **Upload count cap:** `new_game` builds `ligand_data` for **every** candidate row upfront (one temp load each, engine.py:220-223) — a 500-record upload would run 500 extractions per Generate. Add a fail-closed cap constant (pure-side, e.g. `UPLOAD_MAX_RECORDS = 50`, tune at plan time) refusing larger sets with a clear message; record the perf rationale.

---

## export_flow

### SETUP-08 button flow (recommendation)

1. **Collect** the window's fields → `validate_state` (pure; setup_state.py:90-144) → refuse with the specific field error on failure (same normalization the Save Setup button uses).
2. **Resolve supply:** `source_mode == 'demo'` → read MANIFEST.json via `read_json_file` + `parse_manifest_dict` + `enumerate_entries`, filter to non-empty `demo_set_id` (the exact engine.new_game path, engine.py:196-207 — or simply call `new_game` and let it do this); `'upload'` → the uploaded rows + contents from Step 3 above (refuse if none were uploaded this session).
3. **Seed:** auto-random — `random.randint(0, 2**31 - 1)` (matches the generator's `_SUB_SEED_MAX` domain, generator.py:286) — and **display it in the success message**. Rationale: spec.md:26 says "the specific game" — a visible seed makes the share provenance concrete; a user seed field is extra UI for zero v1 value (recorded alternative). Note: today's menu Start is `start_game()` with **seed=42 every time** (gamestart.py:221 default; `aamatch/__init__.py:39` passes nothing) — Phase 4's Start handler must pass a fresh seed (or the export seed, next point) or every exported/started game is identical.
4. **Generate:** `engine.new_game(setup, seed, candidates, ligand_content)` — full fail-closed generation; `GenerationError`/`EngineError` text goes straight into an error dialog (every refusal names the cause by contract, generator.py:130-137).
5. **Assemble + write:** build the game payload (game_file_design shape; embed `ligand_files` = base64 of uploaded record texts only) → `save_container(to_windows_path(chosen_path), 'game', data)` — atomic writer, persistence.py:131-133. Path comes from `QFileDialog.getSaveFileName` (Windows-native path; `to_windows_path` passes `C:/...` and `C:\...` through unchanged by design, paths.py:20-51).
6. **Feedback:** success message = file path + seed + `D` levels × `molecules_per_level` molecules; the demo/upload mode + set identity. Errors non-mutating (atomic writer leaves the original file untouched on failure, persistence.py:108-113).
7. **Current game in the viewer: untouched.** Generate is not Start (spec 3.5 vs 3.7); Cleanup remains its own button (spec 3.6, SETUP-09, prefix-only rules placement.py:404-417). No cleanup, no materialize, no wizard change on export.
8. **Start-after-Generate (recommendation):** keep the last exported `(setup, seed, candidates, ligand_content)` module-side in the setup window; Start passes **that same tuple** to `start_game` (requires threading the `ligand_content` param through `start_game` → `new_game`, the 3rd additive param — same shape as the other two). Effect: the game the user then plays IS the game they shared — the least-surprising reading of "for sharing or later loading of the specific game". **Recorded alternative (simpler):** Start always fresh-seeds independent of Generate; the exported file is then only consumable via Phase 7's Import. Choose at plan time; both are wired through the same seam (gamestart.py:8-13 — "everything that wants to start a game calls start_game").

---

## detector_stamp_placement

**Stamps are written at exactly one place: `generator.generate()` payload assembly** — generator.py:874-877:

```python
return {
    'detector_version': DETECTOR_VERSION,   # 'det-1', level_spec.py:60
    'format_version': LEVEL_SPEC_VERSION,   # 1,       level_spec.py:61
    'seed': seed,
    'levels': levels,
}
```

**The exported file inherits both stamps automatically** — it embeds this payload verbatim, and Phase 7's import re-runs `parse_level_spec_dict`, which enforces: refuse-newer `format_version` (level_spec.py:111-114) and **exact-match `detector_version`** (level_spec.py:116-121). No explicit game-layer stamp is needed; **do not mirror `detector_version` into the game payload header** (duplication = drift risk; PITFALL 11.3).

The 02-15 stamp-gate round-trip is the proven import-side test template (02-15-SUMMARY.md:82): fresh payload parses (positive control), `'det-0'` re-stamped deep copy refused with the verbatim "stale or newer game spec - regenerate it with a current AA-match generator" message. Phase 7's import test should replay exactly this against the embedded `level_spec`.

Detector changes remain a deliberate `DETECTOR_VERSION` bump event (capability.py:14-15 "Any change to capability typing is a DETECTOR_VERSION bump event — never a silent edit"); a bump instantly makes all previously exported games refuse at import with the "regenerate" message — which is the intended contract (PITFALLS.md:278-280).

---

## phase_7_contract

Everything Phase 7's Import button needs from THIS phase's format — the sufficiency list:

1. **Header refusals:** `load_container(path, 'game')` gives foreign/newer/misfiled/unparseable with the canonical messages (persistence.py:61-88, 116-128) — nothing new.
2. **`game_format_version` gate:** constant + refuse-newer parse (new pure `game_file` module) — Phase 4 lands it; Phase 7 calls it.
3. **Spec re-validation:** `parse_level_spec_dict(make_level_spec_container(data['level_spec']))` — inherits detector exact-match, spec refuse-newer, seed/structure minimums. Phase 4 documents this call; Phase 7 invokes it.
4. **Setup re-validation:** `validate_state(data['setup'])` → a ready input for `engine.new_game`/reconstruction.
5. **Molecule reconstruction:** decode `ligand_files` (pure base64 helper, Phase 4) → sha256-verify against each payload molecule's `ligand.sha256` → pass the `{file: text}` dict as `ligand_content` to `engine.new_game` (regenerate path) and/or `placement.materialize` (replay path). **Phase 4 must land the `ligand_content` params + helpers so Phase 7 adds zero cmd-tier loading code.**
6. **Bundled sets on import:** molecules with `ligand.source == 'demo'` resolve via the existing `package_data_path` route — the importing machine needs the same AA-match version's data (a missing bundled file fails loudly at `cmd.load`; the detector_version gate already refuses cross-version specs).
7. **Reconstruction target:** `engine.materialize(payload, level_index=0)` + `game_state.GameState()` — the same two calls `start_game` makes (gamestart.py:241-242); the payload fully determines the initial game (generator.py:758-760 "The payload fully determines the level (nothing re-derives from the seed at replay)").
8. **Refusal UX contract:** every failure is a `FormatError`/`EngineError` naming the cause (persistence gate chain + level_spec gate chain + sha256 check) — Phase 7 renders message text only.
9. **Checkpoint independence:** this format is deliberately NOT the `.pse`+sidecar checkpoint format (Phase 7's other half, PITFALLS.md:60) — game file = viewer-independent truth; checkpoint = live session state.

---

## pure_layer_opportunities

New pure-side surface (all stdlib + persistence/manifest imports, registered in `tests/test_purity.py` PURE_MODULES, WSL-testable):

| Piece | Home suggestion | Contents |
|---|---|---|
| Game-file schema | `aamatch/game_file.py` (new PURE module) | `GAME_VERSION = 1`, `UPLOAD_SET_ID = 'uploaded'`, `make_game_data(setup, payload, ligand_files=None, created_at='')`, `parse_game_data(container)` (gate chain above), `encode_ligand_files({file: text})` / `decode_ligand_files(dict) -> (texts, integrity errors)` (stdlib `base64`, `hashlib`) |
| Uploaded-row builder | `aamatch/game_file.py` or `aamatch/uploaded.py` | pure fn: `(atom_records, lig_bonds, profile, record_text, fmt, index) -> 14-key manifest-shaped row` (+ `'title'` extra); reuses manifest's validation rules for self-check |
| Split helpers | same pure module | `split_sdf_records(text) -> [records]` ($$$$-delimited), `split_mol2_segments(text) -> [segments]` (probe-gated); pure string work, fully unit-testable in WSL |
| Upload cap | constant `UPLOAD_MAX_RECORDS` | enforced by a pure validate function so the refusal is testable headlessly |

cmd-tier additions (thin, existing patterns): `ligand_content` params on `engine.new_game` + `engine._ligand_data_for` + `placement.materialize` (+ optionally `gamestart.start_game`); the per-record extraction loop reusing `_ligand_data_for`'s temp-object discipline. Qt tier: file dialogs + message boxes only.

Standing laws respected: purity (new modules import stdlib + pure siblings only); atomic writes (reuse `save_container`/`write_json_atomic` — no new writer); to_windows_path on every disk path.

---

## common_pitfalls

- **Tuple-key trap (averted):** the (set_id, entry_id) tuple keys live only in `ligand_data` INPUT (engine.py:220-223, generator.py:646); the emitted payload is flat (generator.py:851-861) and JSON-proven (tests/test_generator.py:791-810). Don't "fix" a problem that doesn't exist on the output side.
- **`charge_signs` is a set** (capability.py:668) — never serialize a profile; if ever needed, `sorted()` it (documented, not built).
- **Absolute paths in payloads look like they work** — `os.path.join` drops the package prefix for an absolute third component (verified: `/abs/x.sdf` this session); on other machines it breaks. Synthetic keys + embedded content make it structurally impossible; keep the absolute-path refusal in the uploaded-row validator (manifest.py:267-275 rules).
- **Multi-record files → states, not objects** by default (ObjectMolecule.cpp:8649-8653) — silently violating the STATE-1-ONLY convention (geometry.py:27-29). Split in Python; assert `count_states == 1`.
- **`cmd.load`/`read_*str` into an EXISTING name appends a state** (placement.py:37-39, probe-proven) — always `cmd.get_unused_name('_aam_tmp')` first (engine.py:153 pattern); never `cmd.create` onto existing objects (Pitfall 7, PITFALLS.md:169-200).
- **WSL→Windows paths:** every disk path routes `to_windows_path` (Pitfall 2, PITFALLS.md:48-67; paths.py:20-51). QFileDialog returns Windows-native paths — the guard passes them through unchanged (paths.py:27-30), which is correct for a Windows PyMOL process.
- **Seed 42 default** — `start_game(setup=None, seed=42, ...)` (gamestart.py:221) is called with no seed by the menu item (`aamatch/__init__.py:39`): Phase 4's Start/Generate handlers must pass real seeds or every game is the same game.
- **Never store profile/derived chemistry in the file** — single-source-of-truth drift (Pitfall 11.3); recompute from embedded bytes.
- **Uploaded-set provenance:** record only what is true (format, sha256, `'protonation': 'as-recorded'`, user file name as `'title'`). Never invent DOIs/sources for user molecules (Pitfall 14, PITFALLS.md:342-353; the project's truthfulness rule).
- **`allow_nan=False` is the last-line guard** (persistence.py:98) — the generator's fail-early finite checks (generator.py:246-272, 834-839) fire first; don't strip them when wiring uploads (user files can produce degenerate geometry).
- **Cleanup semantics untouched:** Generate must not clean; Cleanup stays prefix-only (placement.py:404-417; Pitfall 13, PITFALLS.md:319+).

---

## open_questions

UNVERIFIED items, each with a cheap probe (all runnable headless via `cmd.exe /c C:\src\run-conda-pymol.bat -cq <script>` against the repo copy — pymol/AGENTS.md staging recipe):

1. **MOL2 multi-segment Python split edge cases** (LOW — writer keyword verified, reader restart mechanism verified, parser leniency not): does every real-world multi-molecule MOL2 place `@<TRIPOS>MOLECULE` at column 0 with optional preceding comment/molecule blocks? **Probe:** one 2-segment mol2 string (with a leading comment line) → split → two `read_mol2str` loads → `count_atoms` + `count_states` per object. **Fallback:** v1 refuses multi-molecule MOL2 files with a clear message (fail-closed, SETUP-03 still met via SDF).
2. **`read_sdfstr`/`read_mol2str` parity with file loads** (MEDIUM-HIGH — both funnel into the same `_cmd.load` C parsers per importing.py:957-959/1064-1068, but the installed build should be probed once): **Probe:** load `aamatch/data/ligands/acetate.sdf` both ways; assert identical atom/bond/formal-charge counts and `get_bonds` output. Include a `hasattr(cmd, 'read_sdfstr')` guard (one line) in the first upload smoke.
3. **MOL2 formal-charge mapping** (LOW — informational only): which `@<TRIPOS>ATOM` charge categories become `formal_charge` (C source applies `set_formal_charges` for MOL2, ObjectMolecule.cpp:8539-8541, exact category mapping unverified). **Probe:** one known-charged mol2 → check `formal_charge` in extracted records. Not load-bearing (structure fallbacks exist, capability.py:572-613); document whatever the probe shows.
4. **QFileDialog returned path style on Windows** (forward vs backslashes; cosmetic — both pass `to_windows_path` unchanged): human-verify checkpoint in the first GUI pass.
5. **Default export filename/extension** (cosmetic, e.g. `game.aamatch.json`): human preference at plan/checkpoint time; no functional weight.
6. **`UPLOAD_MAX_RECORDS` value** (50 proposed): tune at plan time against a timing probe — Generate's per-candidate temp-load cost is linear (engine.py:220-223); one headless timing run with ~20 records sizes it.

**What might I have missed (reviewed):** Phase 5's Start-sequence interplay with exported games (Start uses the seam either way — contract holds); Phase 6 checkpoint format interaction (deliberately independent, phase_7_contract item 9); concurrent uploads across two setup windows (single module-side uploaded-set state — acceptable v1; Qt singleton makes the scenario moot).

---

## Sources

### Primary (HIGH — all read this session, file:line cited inline)
- `aamatch/persistence.py` (container/kinds/atomic I/O), `aamatch/level_spec.py` (gates), `aamatch/generator.py` (payload + stamps + ligand_data contract), `aamatch/manifest.py` (14-key schema), `aamatch/geometry.py`, `aamatch/capability.py` (profile + set-typed charge_signs), `aamatch/engine.py` (new_game seams), `aamatch/gamestart.py`, `aamatch/placement.py` (materialize/package paths), `aamatch/setup_state.py` (upload reserve), `aamatch/paths.py`
- `aamatch/data/MANIFEST.json`, `tests/test_generator.py` (determinism/round-trip), `tests/test_persistence.py`, `tests/test_manifest.py`, `tests/test_level_spec.py` (test list)
- `pymol-src/modules/pymol/importing.py` (cmd.load multiplex default :724-725; `read_sdfstr` :931-959; `read_mol2str` :1038-1069), `pymol-src/layer2/ObjectMolecule.cpp` (multi-record state loop :8500-8655; MOL2 formal charges :8539-8541), `pymol-src/modules/chempy/sdf.py` ($$$$ records :145-155), `pymol-src/modules/chempy/mol2.py` (@<TRIPOS>MOLECULE writer :34)
- `Pymol-script-repo/plugins/vina.py:746`, `plugins/outline.py:170` (QFileDialog precedent)

### Secondary (MEDIUM-HIGH)
- `.planning/phases/01-bootstrap-pure-foundation/01-06-SUMMARY.md`, `02-headless-game-engine/02-03-SUMMARY.md`, `02-08-SUMMARY.md`, `02-15-SUMMARY.md`, `.planning/research/PITFALLS.md` (2/7/8/11/12/13/14), `.planning/STATE.md` (recorded decisions), `.planning/REQUIREMENTS.md` (SETUP-03/08, PERSIST-02), `.planning/ROADMAP.md` (Phase 4/7 details), `windows-env-versions.md` (PyQt5 5.12.9), `spec.md` (3.5 at :26, Import at :39)

### Tertiary (LOW — flagged above)
- MOL2 parser leniency, QFileDialog path style (probes 1/4)
