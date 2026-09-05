# Phase 2: Headless Game Engine — Materialization & cmd-Tier Pipeline Research

**Researched:** 2026-09-06
**Domain:** cmd-tier materialization (SDF/MOL2 + amino acids), scripted placement, sentinel/identity conventions, manifest format, headless engine pipeline, smoke harness
**Confidence:** HIGH for all PyMOL API-behavior claims below — every probe claim was **executed today inside the real Windows PyMOL 2.5.0 headless process** (probe scripts + verbatim outputs in §12); everything else is cited to the already-verified research files (`.planning/research/*.md`) or the local PyMOL 2.5.0 source tree.

> **Scope boundary:** detection criteria math → `02-RESEARCH-detection.md`; generator algorithms →
> `02-RESEARCH-generation.md`. This file covers what the cmd tier materializes, how the pipeline
> wires pure → cmd → objects → pure, and how it is all proven headlessly.

---

## Summary

Phase 2 must materialize two kinds of chemistry into real PyMOL objects — ligands from
bond-order-carrying SDF/MOL2 files (GEN-02) and standard amino acids with controlled protonation —
then move them by scripted transforms and prove generate → materialize → place → detect → score
end-to-end with no GUI. Three probe sessions against the actual target runtime (Windows PyMOL
2.5.0, `chemtools-win10` env) settled the critical unknowns:

1. **The built-in fragment library EXISTS and is rich.** `cmd.fragment('ala')` works in the target
   env: 114 `.pkl` fragments covering **all 20 standard AAs plus explicit protonation variants**
   (`hid`/`hie`/`hip` for His, `asph`/`gluh` neutral, `lysn`/`argn` neutral) and N/C-capped forms
   (`nt_*`/`ct_*`). The generation researcher's OQ-4 ("fragment inventory LOW — bundle files
   instead") is **resolved**: fragments load, carry hydrogens, set `formal_charge`, and use
   **distinct resn per protonation variant** (HIS/HID/HIE/HIP/ASPH/LYSN/ARGN) — exactly the hook a
   typing table needs. STACK.md's LOW flag ("fragments dir only `__init__.py`") was looking at
   `modules/chempy/fragments/` (code only); the data lives under
   `pymol_path/data/chempy/fragments/`.
2. **SDF/MOL2 loads preserve bond orders** (`cmd.get_bonds` returns the loaded orders — probe:
   acetic acid loaded from `.sdf` and `.mol2` both report `orders=[1,2]`), multi-record SDF files
   become one state per record, and SDF `M CHG` charges round-trip into `formal_charge`. The
   headless "valence preserved" assertion is therefore a **count assertion on `get_bonds` +
   `count_atoms` + `formal_charge`** against manifest-recorded values.
3. **Scripted placement must BAKE coordinates** — `cmd.translate/rotate(..., camera=0)` and
   `cmd.transform_object(name, M, homogenous=1)` all write world-frame coordinates (probe-verified),
   which is what the pure detector reads via `iterate_state`. The object-matrix path
   (`cmd.rotate(object=...)`) moves the *display matrix only* — coordinates unchanged (re-confirming
   PITFALL 12 matrix-blindness). Two NEW hard findings: **`cmd.get_object_ttt` SEGFAULTS the
   process when the object carries a TTT matrix** (crash reproduced; use `cmd.get_object_matrix`),
   and **`matrix_reset(mode=0)` reverts baked coordinates** — so placement code must never call it,
   and Phase 6's Reset must replay the spec, not `matrix_reset` (PITFALL 6 alignment).

**Primary recommendation:** materialize AAs via `cmd.fragment` (fragment name chosen per
protonation) and ligands via `cmd.load` of manifest-referenced SDF/MOL2 through
`paths.to_windows_path`; place with baked world-frame transforms; tag every game atom
`segi='AAM'` + `b=-999.0` and every game object with the reserved `_aam_` prefix; assert counts at
every step; prove it all through a generalized `run_smoke.sh` that derives the SMOKE-NN marker from
the script filename.

---

## 1. Verified API behavior (probes + source citations)

Every `PROBE` line below is verbatim from today's headless runs (§12). Command recipe for all
probes (from repo root):

```bash
timeout 150 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq tmp\\probe_materialize.py" 2>&1 | tail -60
```

### 1.1 SDF loading (GEN-02)

| Claim | Evidence |
|---|---|
| `cmd.load('<file>.sdf', name)` works via extension dispatch, no `format=` needed | probe `sdf.load OK atoms=8 states=1`; `.sdf` falls through `filename_to_format` to `getattr(_loadable, 'sdf')` (`importing.py:41-90`, `constants.py:40-42`) |
| **Bond orders survive the load** | probe `nbonds=7 orders=[1, 2]` — the C=O double bond read back through `cmd.get_bonds(obj, 1)` (returns `(atm1, atm2, order)`; 0-based index warning at `querying.py:1072-1090`) |
| Multi-record SDF → one state per record | probe `sdf.multistate OK states=2 atoms=16` (2 identical records) |
| Re-loading into an existing object **appends a state** | probe `sdf.reload_append OK states_after=2` — matches `cmd.load` docstring "content is appended after the last existing state" (`importing.py:680-681`). **Hazard:** never `cmd.load` into a non-unique name |
| `M CHG` charges round-trip | probe `sdf.formal_charge [('C',0,0.0), ..., ('O',-1,0.0), ...]` — acetate `M CHG` lands in `formal_charge` (readable via `cmd.iterate`); `partial_charge` stays 0.0 (SDF has none) |
| String loaders exist for tests/fixtures | `cmd.read_sdfstr` (`importing.py:931-960`, `discrete` default 1), `cmd.read_mol2str` (`importing.py:1038+`), `loadable.sdf2str=38`, `mol2str=34` (`constants.py:36-42`) |

**Multi-state policy is deliberately NOT decided here** (Phase 8 decides with curated data —
ROADMAP). Phase 2 must only: record `states_expected` per manifest entry, assert
`cmd.count_states(obj) == states_expected` after load, and keep the materializer's state handling
parameterized (default: use state 1 for detection; never mutate state semantics in a way that
forecloses collapse-to-single-state later). The verified mechanics above are what Phase 8 will
choose between.

### 1.2 MOL2 loading

| Claim | Evidence |
|---|---|
| `cmd.load('<file>.mol2', name)` works | probe `mol2.load OK atoms=8 states=1 nbonds=7 orders=[1, 2]` |
| Bond orders preserved (SYBYL bond block) | same probe |
| Partial charges available when present in file | fixture used `NO_CHARGES`; mol2 `partial_charge` readback untested — **LOW, verify if upload validation ever needs it** |

### 1.3 Valence display (the rendering half of GEN-02)

| Claim | Evidence |
|---|---|
| The display setting is `valence` (numeric on/off + gap width) | `_gui.py:483` ("Show Valences" check box → setting `valence`); `wizard/demo.py:448` uses `cmd.set("valence","0.05")` |
| **Default in the target build is ON** | probe `setting.valence default='on' set1='on' unset0='off'` — `cmd.get('valence')` returns `'on'`/`'off'` strings |
| `cmd.valence(order, sel1, sel2)` *edits* bond orders (not display) | `editing.py:596-648` |

Consequence: **do not touch the setting by default** — valence-correct display (double-bond
rendering) is on for users out of the box; a Phase-2 [HUMAN] checkpoint can confirm visually. If
any code toggles it, it must save/restore the prior value like every other global setting.

### 1.4 Amino-acid fragments (the AA materialization source)

| Claim | Evidence |
|---|---|
| Fragment library present in target env at `<env>/Lib/site-packages/pymol/pymol_path/data/chempy/fragments/` — **114 `.pkl` files** | probe `chempy.path`, `fragments.dir`, `fragments.pkl_count 114` |
| All 20 standard AAs present: `ala arg asn asp cys gln glu gly his ile leu lys met phe pro ser thr trp tyr val` | probe `fragments.names` (verbatim list in §12.1) |
| **Protonation variants present**: `hid hie hip` (His δ/ε/double), `asph` (neutral Asp), `gluh` (neutral Glu), `lysn` (neutral Lys), `argn` (neutral Arg) | probe `fragments.names` |
| Capped terminal forms: `nt_*` (N-term, +1 charge), `ct_*` (C-term, −1), plus caps `ace nhh nme` | probe `resn.nt_ala ['ALA'] charge=[0,1]`, `resn.ct_ala ['ALA'] charge=[-1,0]` |
| `cmd.fragment(aa, object_name)` creates the object directly (no temp-copy needed) | `creating.py:929-958` (`fragment(name, object=None, ...)` → `load_model`); probe `fragment.ala OK atoms=10 states=1` |
| Fragments carry hydrogens (e.g. ala = 10 atoms incl. H) | probe atom counts: `ala=10, gly=7, arg=24, trp=24, his=17, hip=18, pro=14` |
| `formal_charge` is set on charged fragments | probe: `asp charge=[-1,0]` (carboxylate O = −1), `hip [0,1]`, `lys [0,1]`, `nt_ala [0,1]`, `ct_ala [-1,0]` |
| **Distinct resn per protonation variant** | probe: `his→HIS hid→HID hie→HIE hip→HIP asph→ASPH lysn→LYSN argn→ARGN` (Amber-style names) |
| His ring-N protonation readable by atom name | probe `frag.hid.ringH H_on_N=['1HD']`, `hie → ['2HE']`, `hip → ['1HD','2HE']` |
| Fragment default placement is a fixed template pose near origin (bbox ±~2 Å) | probe `frag.ala.bbox x[-1.6,2.0] y[-2.2,1.9] z[-1.4,1.7]` — materializer always translates to slot |
| `cmd.get_fastastr` works on polymer objects | probe `get_fastastr '>probe_pep_A\nAG\n'` on a 2-residue PDB fixture (`exporting.py:169`) |

**Closes generation-research OQ-4** (02-RESEARCH-generation.md:553): no bundled AA files are
required for standard AAs. Keep the manifest/AA-source layer abstract (fragment name OR bundled
file) so Phase 8 can bundle special cases without re-planning.

Why STACK.md's LOW flag existed: it checked `modules/chempy/fragments/` (a code package containing
only the 8-line loader, `chempy/fragments/__init__.py:5-8` — `get(name)` = `io.pkl.fromFile`).
The `.pkl` data ships separately under `pymol_path/data/chempy/`. Lesson recorded: **data
directories are not module directories** — probe the runtime, don't infer from the source tree.

### 1.5 Transform / placement mechanics (scripted placement)

| Claim | Evidence |
|---|---|
| `cmd.transform_object(name, M16, homogenous=1)` **bakes a standard row-major homogeneous 4×4 into coordinates** | probe P3.1 `coords_baked (0,0,0) -> (1,2,3)`; matrix layout doc at `editing.py:1962-1987`, `homogenous` arg at `editing.py:2031-2033` |
| After the bake, **display TTT stays None** (renderer applies coords once — no double transform) | probe P3.1 `ttt_identity ttt=None` |
| `cmd.get_object_matrix` returns **non-identity** after a baked transform (it is the coordinate-*history* record) | probe P3.1 `objmatrix_ident is_ident=False`; **do not use it to assert placement — assert coordinates** |
| `cmd.matrix_reset(name, mode=0)` **reverts baked coordinates to pre-transform** | probe P3.2 `reset0_reverts ... reverted=True` (`editing.py:2126-2151`: mode 0 = "transformation was applied to coordinates") |
| `cmd.translate([dx,dy,dz], obj, camera=0)` and `cmd.rotate(axis, angle, obj, camera=0)` bake world-frame coords | probe: `translate.camera0 ok=True`; `rotate.camera0 rotz_ok=True` (90° about z: (1,2,3)→(−2,1,3)) (`editing.py:1610-1714`, `:1716+`; camera default is 1 = camera frame — PITFALL 12) |
| `cmd.rotate(axis, angle, object=NAME, origin=...)` sets the **TTT display matrix; stored coords UNCHANGED** | probe P3.3/`rotate.object_matrix`: `coords_changed=False`, matrix non-identity — the matrix-movement model (Phase 3 decision); detector reading `iterate_state` coords would be **blind** to it |
| **`cmd.get_object_ttt` SEGFAULTS on a TTT-bearing object** (fresh object: returns None, fine) | crash-hunt probes §12.3–12.4: `rotate(object=...)` OK → `get_object_ttt` kills the process (exit 0 via wrapper, zero output). Use `cmd.get_object_matrix(object, state, incl_ttt=1)` instead (`querying.py:89-100`) |

### 1.6 Naming, grouping, identity

| Claim | Evidence |
|---|---|
| `cmd.get_unused_name('_aam_')` → `_aam_01` (zero-padded counter) | probe `get_unused_name _aam_01` — collisions impossible if every game object is born through this call |
| `cmd.group(name, '_aam_*')` / `cmd.ungroup` work | probe `group OK names=[...]` |
| `cmd.copy` and `cmd.create` to a NEW name both full-copy (8 atoms) | probe `copy.new_name OK atoms=8`, `create.new_name OK atoms=8` |
| **`cmd.copy` preserves source atom ids** (so do `create` copies — PITFALL 7) | probe `copy.id_preserved True` — identity is `(object, id)`, never bare `id` |
| `cmd.iterate` expression namespace has **no `round()`** | probe-1 `transform_object.homog1 ERR NameError("name 'round' is not defined")` — only symbol-table names + `space` dict entries; round in Python after extraction |
| `cmd.iterate` exposes uppercase `ID`; coords only via `cmd.iterate_state` | PITFALL 8 (`editing.py:1444-1449`, `:1578-1608`) — re-confirmed by both probes' working `space={'stored': ...}` reads |
| Phase-1 runtime facts still govern smokes: `__file__` unusable in `-cq` scripts (anchor via `sys.argv`/cwd); assert `info.load()` not `.loaded`; forward-slash and space paths load fine | `01-07-SUMMARY.md`, `windows-env-versions.md` |

---

## 2. Amino-acid materialization — recommendation

### Options considered

| Option | Verdict | Why |
|---|---|---|
| **`cmd.fragment(name)` from the built-in library** | **RECOMMENDED (primary)** | Verified present in the target env with all 20 AAs + protonation variants + caps; explicit H and `formal_charge`; distinct resn per protonation; zero data to bundle; deterministic template geometry |
| Bundled AA structure files in `aamatch/data/` | Fallback / special cases | Extra curation burden for zero benefit while fragments cover the need; keep as the escape hatch for anything fragments lack (e.g. a special residue or an alternative protonation PyMOL names differently) |
| `editor.attach_amino_acid` | Rejected | Builds ONTO an existing terminus (mutagenesis-style growth, `editor.py:85-268`); needs a picked N/C connection point; depends on the same fragment library internally; wrong shape for "independent movable AA objects" |
| `cmd.get_fastastr` | Rejected for materialization | It *reads* sequence (`exporting.py:169`); it does not create objects. Useful only as a diagnostic |

### Recommended design

1. **AA template registry (pure data):** map each generator-emitted `aa` token to a materialization
   source. Default table: `ala→ala ... val→val` plus the protonation variants the generator may
   emit: `his→his|hie|hid|hip`, `asp→asp|asph`, `glu→glu|gluh`, `lys→lys|lysn`, `arg→arg|argn`
   (plain names = default ionization: Asp⁻/Glu⁻/Lys⁺/Arg⁺/His-neutral — probe-verified charges).
   The capability table (generation research §2) must use the SAME tokens — one shared vocabulary.
2. **Materializer per slot:** `cmd.get_unused_name('_aam_aa')` → `cmd.fragment(frag, name, zoom=0)`
   → translate to `grid_pose.position` (§6) → sentinel-tag all atoms (§4). One object per AA —
   PITFALL 13's note that whole-AA objects favor cleanup by prefix, and `cmd.drag`'s single-object
   constraint (STACK.md) keeps this the right model for Phase 3 picking too.
3. **No `cmd.create`-onto-existing anywhere in materialization** — fragments create fresh objects
   and ligands load fresh objects, so PITFALL 7's replace/merge trap is avoided *by construction*
   rather than by count assertions alone. Count assertions still guard every step (§8).
4. **Protonation is explicit at the manifest/generator level** (GEN-02): the level spec's
   `ligand.protonation` covers the small molecule (SDF payload is the state); grid AAs carry
   protonation implicitly via the fragment token in `slot['aa']` (e.g. emit `hip` when the required
   interaction needs double-protonated His). The AA registry should record `resn` per token
   (HIS vs HID vs HIE vs HIP) so detector `chem_types` keys on resn exactly.

---

## 3. Bundled-data manifest (proposal)

### 3.1 Format: versioned JSON container, read by a PURE module

Precedent splits: prior art kept `DEMO_MANIFEST` as a Python dict in `setup_state.py` (works, but
no version header — PITFALL 11.3's schema-drift risk); Phase 1 built the versioned-container
discipline (`aamatch/persistence.py`). stdlib `json` file I/O is purity-legal (persistence.py
already does it), so:

```
aamatch/data/MANIFEST.json          # versioned container, kind='manifest' (add to KINDS)
aamatch/manifest.py                 # PURE: load/validate/enumerate manifest entries
                                    #   (imports persistence + paths only; add to PURE_MODULES)
```

- `KINDS` in `persistence.py` gains `'manifest'` (additive; refuse-newer semantics already handled).
- The generator receives **already-resolved candidate dicts** (generation research §3.2) — the cmd
  tier (or headless smoke) calls `manifest.py` to resolve `set_id → entries`.

### 3.2 Per-entry schema (what every-manifest-id loading must verify)

```json
{
  "manifest_version": 1,
  "sets": [
    {
      "set_id": "demo-easy-1",
      "tier": "easy",                      // Phase-8 tier slot placeholder (easy|hard|challenge|very_challenging)
      "title": "Phase-2 development set",
      "license": "",                       // Phase-8 placeholder — MUST be filled before curated bundling (HELP-02)
      "provenance": {},                    // Phase-8 placeholder: {source_db, id, doi, protonation_source}
      "entries": [
        {
          "entry_id": "mol-001",
          "file": "demos/mol-001.sdf",     // relative to aamatch/data/ (resolved via paths.package_data_path)
          "format": "sdf",                 // "sdf" | "mol2"
          "sha256": "<hex>",               // content pin (truthfulness: detect silent data swaps)
          "protonation": "as-recorded",    // descriptive; Phase 8 fills the real provenance string
          "atom_count": 8,                 // cmd.count_atoms after load
          "heavy_atom_count": 4,           // non-H subset (grid/size-class input for the generator)
          "bond_count": 7,                 // len(cmd.get_bonds)
          "bond_order_counts": {"1": 6, "2": 1},   // multiset of orders — the valence-preservation assertion
          "formal_charge_sum": 0,          // sum of iterate formal_charge (charge sanity)
          "states_expected": 1,            // count_states after load (multi-state policy stays open for Phase 8)
          "metal_present": false,          // detector capability flags (metal coordination / halogen conditional)
          "halogen_present": false,
          "size_class": "small"            // generator input (GEN-05 molecule-size axis)
        }
      ]
    }
  ]
}
```

Design rules:
- **Counts are the contract.** `atom_count`/`bond_count`/`bond_order_counts`/`formal_charge_sum`/
  `states_expected` are exactly what the every-manifest-id smoke asserts (below) — each field is
  load-bearing, none decorative. Adding a field is additive evolution (`.get` defaults).
- `file` paths are **package-relative and forward-slash**; resolution goes
  `paths.package_data_path('data', relfile)` → `paths.to_windows_path` → `cmd.load`. Never
  cwd-relative (PITFALL 2), never `/mnt/` literals inside the manifest.
- The **largest-bundled-molecule** target for the perf smoke (DETECT-05) is derived as
  `max(entries, key=heavy_atom_count)` — no special-cased field to drift.

### 3.3 Every-manifest-id smoke (GEN-06 supply proof, PITFALL 11.3 anti-drift)

```
for each set → for each entry:
    path = to_windows_path(package_data_path('data', entry.file))
    cmd.load(path, tmp_name)                      # tmp_name via get_unused_name('_aam_tmp')
    assert cmd.count_atoms == entry.atom_count
    assert sorted(get_bonds orders) == expand(entry.bond_order_counts)
    assert sum(formal_charge) == entry.formal_charge_sum
    assert cmd.count_states == entry.states_expected
    assert sha256(open(path,'rb').read()) == entry.sha256
    assert entry.metal/halogen flags match element scan
    cmd.delete(tmp_name)
print marker
```

This is SMOKE-02 (§8). It reuses the prior art's proven shape (its post-fix smoke iterates every
demo id; PITFALLS.md:272 "a smoke that loads every id").

---

## 4. Sentinel + reserved-prefix conventions (Phase 2 establishes → Phase 4 Cleanup consumes)

Adapting PITFALL 8/13 and the prior art's battle-tested scheme to AA-match's object-per-AA model:

| Convention | Rule | Rationale |
|---|---|---|
| **Object prefix** | every game-created object is born `cmd.get_unused_name('_aam_<role>')` with role ∈ `aa`, `lig`, `tmp` (e.g. `_aam_aa01`, `_aam_lig01`) | Cleanup (Phase 4) deletes `cmd.get_names('objects')` entries starting with `_aam_` ONLY; `get_unused_name` makes collisions impossible (probe: `_aam_01`) |
| **Atom sentinel** | every atom of every game object: `segi='AAM'` + `b=-999.0` (set via `cmd.alter(..., "segi='AAM'; b=-999.0", space={})` + `cmd.sort(obj)`) | Cleanup can also atom-scan `segi AAM` inside any object (defense in depth); Phase 7 sentinel-first reconstruction finds game atoms in a loaded `.pse` by the same tag. Prior art used `segi='GAME'`; AA-match uses its own `AAM` |
| **Selector forms** | `segi AAM`, `b < 0` — **never `b -999`** (malformed selector, silently matches nothing — PITFALL 8) | probe-adjacent prior-art rule; value stays −999, only the selector compares |
| **Ligand naming** | game-materialized ligand → `_aam_lig*` (Cleanup removes it); user-adopted ligand (Phase 4 upload/user-scene flow) → recorded by name, NEVER prefixed, NEVER deleted | PITFALL 13: "the game must ensure the ligand object itself is never game-generated and never deleted by cleanup" — the adopt path is how Phase 2's conventions serve both flows |
| **Temp objects** | everything transient (probe objects, build temps) uses `_aam_tmp*` and is deleted before the operation returns; a generate smoke asserts `cmd.get_names('objects')` grew by exactly the intended count | PITFALL 13 warning sign: "object list grows during Generate (leaked temp objects)" |
| **Group (optional)** | `cmd.group('_aam_game', '_aam_*')` — group name itself carries the prefix so prefix-deletion removes it too | visual organization for Phases 4+; defer creation to Phase 4, fix the *name* now |
| **Record at generate-time** (reversibility payload, held in runtime state) | 1) pre-game object-name snapshot; 2) pre-game atom counts of user objects; 3) the list of created game objects; 4) `ligand_origin` ∈ {materialized, adopted} | Cleanup contract: delete `_aam_*` names → assert remaining names == pre-game snapshot → assert user atom counts unchanged. The Phase-1 backup module covers the (not expected) mutated-user-object failure path |

What Cleanup will do with this (Phase 4, documented now so Phase 2 doesn't under-build):
`cmd.delete(name)` over every `_aam_`-prefixed name → assert scene equals the pre-game snapshot →
report counts. No `hetatm`/`not polymer`/resn filters ever (PITFALL 13).

---

## 5. Atom identity & selectors (conventions materialization must establish)

For Phase 3 picking and Phase 7 sentinel-first reconstruction to reconcile, materialization pins:

1. **Identity = `(object_name, atom_id, alt)`** — never `index` (officially fragile,
   `querying.py:1313-1317`), never bare `id` (copies share ids — probe `copy.id_preserved=True`).
   `alt` is carried even though SDF/MOL2 loads produce `alt=''` — the convention must survive
   PDB-derived Phase-8 data where altlocs exist (prior-art `wizard.py` carries `(model, ID, alt, resv)`).
2. **Materialize-time registry:** the engine records `slot_id → (object_name, sorted atom ids)`
   (and ligand `(object, ids)`) when objects are created. Atom ids are stable from creation
   through `.pse` save (prior-art smoke: id stable across reload; `cmd.sort` preserves id) — this
   map is what the sidecar reconciles against in Phase 7.
3. **`resi` policy:** leave fragment defaults (one AA per object makes resi collisions harmless);
   never select game content by `resi`/`chain` (sentinel-only rule). The ligand keeps its
   file-authored resi (usually blank/1 for SDF) — detection keys on atom records, not resi.
4. **Read discipline (all cmd-tier extraction):** `cmd.iterate` for properties with **uppercase
   `ID`**; `cmd.iterate_state(1, sel, "...", space={'stored': out})` for coordinates; explicit
   `space=` dict **always**; **no `round()` inside expressions** (probe NameError — round in
   Python after extraction).
5. **Extraction record shape** (hands off to the detector — contract from 02-RESEARCH-detection.md §5.1):
   `{"side": "aa"|"lig", "object": str, "id": int, "name": str, "elem": str, "resn": str,
     "resi": int, "alt": str, "x": float, "y": float, "z": float}` + ligand bond block
   `[(i, j, order)]` from `cmd.get_bonds` (0-based indices + an `index`→`id` mapping built via one
   `iterate_state ... "stored.append((index, ID))"` pass, per the `get_bonds` warning at
   `querying.py:1078-1084`). Coordinates are **final composed world-frame coordinates** — with the
   §6 baking rule, `iterate_state` coords ARE the placed pose; no matrix composition needed in
   Phase 2.
6. **Never `cmd.get_model` on large objects** for extraction (PITFALL 15 OOM trap) — narrow
   `iterate_state` over `segi AAM` + the ligand object only.

---

## 6. Scripted placement mechanics (headless E2E "scripted placement")

### 6.1 The Phase-2 rule: bake coordinates, never matrices

The detector reads `iterate_state` coordinates (detection research §5.1: "final composed
world-frame coordinates"). Two mechanical families exist (PITFALL 6's duality, probe-settled):

| Mechanism | What changes | Use in Phase 2 |
|---|---|---|
| `cmd.translate(v, sel, camera=0)`, `cmd.rotate(axis, ang, sel, camera=0)`, `cmd.transform_object(name, M, homogenous=1)`, `cmd.transform_selection(sel, M, homogenous=1)` | **stored coordinates** (probe-verified); TTT stays None/identity → renderer shows exactly the coords the detector reads | **ALL scripted placement** |
| `cmd.rotate(..., object=NAME)`, `cmd.translate(..., object=NAME)`, TTT/matrix_mode paths | display matrix only; stored coords unchanged (probe P3.3) | **never in Phase 2**; it is Phase 3's movement-model decision (with detector-side matrix composition) |

Placement recipe for a grid slot (generation research §5 gives `grid_pose.position`):

```python
# cmd tier — bake an AA from its template pose to the slot pose
name = cmd.get_unused_name('_aam_aa')
cmd.fragment(frag_token, name, zoom=0)              # template pose near origin
cmd.alter(name, "segi='AAM'; b=-999.0", space={})   # sentinel (all atoms)
cmd.sort(name)
centroid = geometry.centroid_of(name)               # iterate_state mean
delta = [slot_x - centroid[0], slot_y - centroid[1], slot_z - centroid[2]]
cmd.translate(delta, name, state=1, camera=0)       # BAKE world-frame coords
```

Rigid pose from a full 4×4 (rotation about the AA centroid + translation) in one call:

```python
M = [R00, R01, R02, tx,
     R10, R11, R12, ty,
     R20, R21, R22, tz,
     0.0, 0.0, 0.0, 1.0]
cmd.transform_object(name, M, homogenous=1)         # standard row-major homogeneous (probe-verified)
```

### 6.2 Pose assertion (how the smoke proves the placed pose)

Snapshot → transform → snapshot → compare per-atom:

```python
before = geometry.coords_of(name)                    # iterate_state x,y,z
cmd.translate(delta, name, state=1, camera=0)
after = geometry.coords_of(name)
# rigid assert: after[i] == before[i] + delta for every atom (tolerance 1e-6)
```

For rotation: `after[i] == R·before[i] + t` per atom (probe pattern — `rotate.camera0 rotz_ok=True`
checked exactly this against a hand-computed rotation). **Assert coordinates, never
`get_object_matrix`** (non-identity after bakes — it is the coordinate history, probe P3.1).

### 6.3 Rotation-invariance probe (coordinating with the detector research)

The detector researcher's WSL suite proves criteria are rotation-invariant on synthetic data. The
cmd-tier E2E adds the *pipeline-level* version (no camera-frame leak, baking correct):

```
place AA(s) → detect → results_A
rotate the WHOLE scene (ligand object + every placed AA object) by R about the ligand centroid
    (cmd.rotate(axis, ang, '_aam_* or ligand', camera=0) — bakes both sides equally)
re-detect → results_B; assert results_A == results_B (same formed/missed set)
```

Folded into SMOKE-04 Part B (§8) — one extra detect pass, no separate smoke.

### 6.4 Hazards verified today

- **`matrix_reset(name, mode=0)` reverts baked coordinates** (probe P3.2 `reverted=True`).
  Consequences: (a) placement code must never call it; (b) Phase 6 Reset must **replay the spec's
  grid poses** (re-bake), not `matrix_reset` — which is exactly PITFALL 6's "reset must reset the
  same mechanism that moved the atom" resolved in favor of spec-replay (ARCHITECTURE Pattern 6).
- **`get_object_ttt` segfaults on TTT-bearing objects** (§12.3-12.4) — banned from the codebase;
  use `get_object_matrix(incl_ttt=1)` where a matrix read is genuinely needed (Phase 3+).
- `cmd.load` into an existing object name **appends a state** (probe) — always load into
  `get_unused_name`-issued names, or delete-then-load.

---

## 7. Pipeline architecture (pure core ⇄ cmd tier)

### 7.1 Module split (Phase-2 additions; aligns with both sibling research files)

```
aamatch/
├── (PURE, existing)   level_spec.py        # spec schema + gates (Phase 1) — payload produced by generator
├── (PURE, gen-rsch)   capability.py        # AA/ligand typing + capability table (shared vocabulary with §2)
├── (PURE, gen-rsch)   generator.py         # generate(seed, setup, candidates, ligand_data, D) → payload
├── (PURE, det-rsch)   vec3/spatial/chem_types/thresholds/detector.py
├── (PURE, NEW)        manifest.py          # load/validate/enumerate bundled-data manifest (§3)
├── (PURE, NEW)        game_state.py        # runtime game state: placements, scores, counters (sidecar payload)
├── (CMD, NEW)         geometry.py          # objects → atom records + bond block + centroids (detector contract)
├── (CMD, NEW)         placement.py         # materialize(spec) + place/reset (baked transforms) + sentinels
├── (CMD, NEW)         engine.py            # the headless operation set (§7.2) — composition root for Phase 2;
│                                             controller.py (wizard/GUI callbacks) arrives in Phase 3 over the same ops
└── data/MANIFEST.json                      # versioned manifest container (§3)
```

Purity gates: add `manifest` (+ sibling pure modules) to `PURE_MODULES` in `tests/test_purity.py`
(01-08 contract — new pure modules escape the AST gate otherwise).

### 7.2 Engine operation set (what Phases 3–7 call)

```python
# engine.py — cmd tier; each op is count-asserted and returns plain data
new_game(setup, seed)          → level_spec payload   # calls PURE generator (candidates from manifest.py,
                                                      #   ligand_data from geometry.bounding_sphere after load)
materialize(spec)              → RuntimeView          # ligand load + per-slot fragment creation + sentinels
                                                      #   + registry {slot_id → (object, ids)}, counts asserted
place_aa(slot_id, pose)        → None                 # baked transform (§6); updates game_state
reset_to_grid()                → None                 # replay spec grid poses (re-bake; NEVER matrix_reset)
detect()                       → results              # geometry extraction → PURE detector
score(results, required)       → float                # PURE scoring: fraction of required, binary each
save_state(path)/load_state(p) → game_state           # Phase-1 persistence containers (sidecar JSON)
cleanup()                      → counts               # prefix+sentinel deletion (§4) — full UI wiring in Phase 4
```

- **State split:** serialized (level_spec container): seed, grids, required, ligand refs
  (`sha256`, `protonation`, detector_version stamp). Runtime-only (game_state → sidecar JSON in
  Phase 7): current placements, object-name registry, scores, counters, timer anchor. PyMOL holds:
  atoms + sentinels only. **The spec is the single source of truth** — reset/recover/export replay
  it (ARCHITECTURE key data-flow rule).
- **Geometry crosses at exactly two points:** post-materialize snapshot (bounds for the generator;
  registry ids) and detect-on-demand. No per-frame geometry (ARCHITECTURE).
- GUI/wizard (Phases 3–5) consume the SAME engine ops through a controller wrapper with callbacks
  — Phase 2 proves them headless with no Qt import anywhere (purity + headless gates).

### 7.3 E2E data flow (one molecule, one level — what SMOKE-04 exercises)

```
manifest.py resolves set/entries (pure)
  → cmd.load ligand via path helpers (placement)
  → geometry.bounding_sphere → generate(seed, ...) → payload (pure)
  → make_level_spec_container + persistence save (pure file I/O)
  → placement.materialize(payload): ligand + grid objects + sentinels + registry
  → engine.place_aa(slot, pose): baked transforms for the scripted placement
  → geometry.extract(ligand + AAs) → detector.detect (pure) → scoring (pure)
  → assertions: counts before/after at every step; score == expected fraction
```

---

## 8. Smoke harness design (SMOKE-02+ conventions)

### 8.1 `run_smoke.sh` generalization (closes the pending TODO)

The current runner hardcodes `SMOKE-01` (`smoke/run_smoke.sh:7-9`). Generalize by **deriving NN
from the script filename** — the existing `smoke_01_bootstrap.py` already matches the pattern, so
the change is backward-compatible:

```bash
#!/usr/bin/env bash
# Usage: bash smoke/run_smoke.sh smoke/smoke_03_e2e.py [timeout_sec]
set -e
SCRIPT="$1"
TIMEOUT="${2:-120}"
BASE="$(basename "$SCRIPT" .py)"                       # smoke_03_e2e
NN="$(printf '%s' "$BASE" | sed -n 's/^smoke_\([0-9][0-9]*\)_.*/\1/p')"
[ -n "$NN" ] || NN="01"                                # legacy scripts without _NN_
cd "$(dirname "$0")/.."
timeout "$TIMEOUT" cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\$(basename "$SCRIPT")" 2>&1 \
  | tee /tmp/smoke_out.txt | tail -60
grep -q "=== SMOKE-$NN PASS ===" /tmp/smoke_out.txt
```

Script-side conventions (frozen from Phase 1, kept):
- filename `smoke_<NN>_<name>.py`; final marker `=== SMOKE-<NN> PASS ===` (the SOLE verdict
  carrier — exit codes can't cross cmd.exe); per-check lines `SMOKE-<NN> <label> PASS|FAIL <detail>`;
  env records `SMOKE-ENV <key>: <value>`; **every print stays on one line**.
- **NEW (from today's crash):** flush after each print (`sys.stdout.flush()` or
  `print(..., flush=True)`). A mid-script segfault otherwise discards ALL buffered output (§12.3:
  probe-3's first run produced zero bytes) — flushing preserves the progress trail up to the crash
  and the missing marker still fails the run correctly.
- Anchor repo root via `sys.argv` (never `__file__`) — `01-07` discovery; import `aamatch`
  directly (module identity `aamatch`; never also `plugin_load` in the same session — standing
  gate 5).
- `python3.6 -m py_compile` before every Windows launch (a syntax error wastes a ~60 s boot).

### 8.2 Phase-2 smoke suite (what each proves)

| Smoke | Name | Asserts | Ties to |
|---|---|---|---|
| **SMOKE-02** | `smoke_02_manifest.py` | every manifest entry: load via path helpers, `count_atoms`/`get_bonds` orders/`formal_charge` sum/`count_states`/sha256 match the manifest; objects deleted after each; object list clean at end | GEN-02 supply; PITFALL 11.3; ROADMAP Phase-8 criterion 4 rehearses this shape |
| **SMOKE-03** | `smoke_03_generate.py` | generate on real fixture ligand: `get_names('objects')` grows by exactly ligand+slots; every `_aam_aa*` object's atom count matches its fragment template's expected count; every atom `segi AAM` + sentinel count == total atoms; no `_aam_tmp*` leaks | PITFALL 7 count-asserted generate smoke; PITFALL 13 |
| **SMOKE-04** | `smoke_04_e2e.py` | **Part A (happy path):** new_game → materialize → scripted placement that forms ≥1 required interaction (poses computed from known fixture geometry) → detect → score == expected binary fraction; **Part B (rotation invariance):** rotate whole game scene, re-detect, identical results; **Part C (reset):** reset_to_grid re-bakes, coords match the spec's grid poses again | GEN-02; ROADMAP Phase-2 criterion 4 (count-asserted E2E); PITFALL 12 frames |
| **SMOKE-05** | `smoke_05_perf.py` | largest manifest entry by `heavy_atom_count`: timed `geometry.extract + detector.detect` inside the perf budget (§9); prints `SMOKE-ENV perf extract_ms=… detect_ms=… atoms=…` | DETECT-05 headless verification; ROADMAP criterion 5 |

(Perf budget + measurement detail in §9. A dedicated fragment-inventory smoke is unnecessary —
SMOKE-03 exercises every fragment token the generator can emit, and SMOKE-02 covers file data.)

### 8.3 Headless recipe (unchanged, frozen)

```bash
python3.6 -m py_compile aamatch/*.py smoke/smoke_04_e2e.py
python3.6 -m unittest discover -s tests -v          # purity gates run here
bash smoke/run_smoke.sh smoke/smoke_04_e2e.py 180   # marker-gated verdict
```

Smokes run against the REPO copy (no staging — `01-07` decision). Fixtures written by smokes go to
git-ignored `tmp/smoke fixtures/` (Phase-1 precedent; never inside `aamatch/`).

---

## 9. Perf smoke design (DETECT-05's headless verification)

**Budgets on record:** Generate < 30 s on the largest demo (PROJECT code standards; ROADMAP Phase-9
criterion 4; PITFALLS 15). Detection-on-Confirm "should be < 100 ms at this scale" (PITFALLS 15
warning sign). Pick/drag < 200 ms is a Phase 3+/9 concern, not Phase 2.

**Phase-2 gate (recommended, stated explicitly for the planner):** on the largest *Phase-2
bundled* molecule, `geometry.extract` + `detector.detect` complete in **< 1000 ms headless wall
time** (10× slack over the PITFALLS expectation because Phase-2 fixtures are small and the curated
Phase-8 demos will be re-measured; the *trend* — extraction O(atoms), detect O(candidates) — is
what SMOKE-05 pins). Measure with stdlib `time.time()` around each stage; print one line
`SMOKE-ENV perf extract_ms=<int> detect_ms=<int> atoms=<int>`; the marker gates on
`extract_ms + detect_ms < 1000`. Phase 9 re-runs the same smoke against curated data.

**What the cmd tier supplies the pure detector (spatial-pruning hooks):** the detector's cell-list
needs only plain data (detection research §5.2) — the cmd tier is a *supplier*, not a pruner:

- world-frame atom records (§5) — the bounding-sphere AA prefilter and cell list run pure-side;
- ligand bond block `(i, j, order)` + index→id map (§5, `get_bonds` caveat);
- ligand bounding sphere `(centroid, radius)` from the same extraction (generator input too);
- counts via `count_atoms`/`count_states` (guards, not extraction).

**Code-audit hook (ROADMAP criterion 5):** "no naive per-atom-pair loops" is audited in
`detector.py`/`spatial.py` (detection research §5.2 defines the check); the cmd tier stays out of
pair math entirely, which makes the audit trivial for `geometry.py`.

---

## 10. Pitfalls for the planner (new probe findings + inherited)

### NEW from today's probes

1. **`cmd.get_object_ttt` SEGFAULTS on TTT-bearing objects** (crash reproduced twice, §12.3–12.4;
   silent — exit 0 through the cmd.exe wrapper with zero output when stdout is buffered). Ban it;
   use `cmd.get_object_matrix(object, state, incl_ttt=1)`. Add a grep gate when Phase 3 lands.
2. **`matrix_reset(mode=0)` reverts baked coordinates** — never call it after scripted placement;
   Phase 6 Reset replays the spec instead (PITFALL 6 alignment). Also: after a bake,
   `get_object_matrix` is non-identity (history) — assert poses via coordinates only.
3. **`round()` (and other builtins) are absent from iterate/alter_state expression namespaces** —
   NameError at runtime. Round in Python after extraction.
4. **Buffered stdout + hard crash = zero output** — smokes must flush after every print (§8.1).
5. **`cmd.load` into an existing object appends a state** — unique names via
   `cmd.get_unused_name` always, or delete-then-load.
6. **`cmd.copy`/`create` preserve source atom ids** even for fresh-name copies (probe) — identity
   maps must always be keyed `(object, id)`; never merge maps across objects.
7. **Valence display defaults ON in this build** (`cmd.get('valence') == 'on'`) — do not toggle
   globally; if ever toggled, save/restore. Note `cmd.get` returns `'on'`/`'off'` strings for it.

### Inherited (already verified — restated because Phase 2 touches them all)

| # | Pitfall | Phase-2 application |
|---|---|---|
| 2 | WSL→Windows paths | every `cmd.load`/`cmd.save`/open routes through `paths.to_windows_path`; manifest paths package-relative (`package_data_path`) |
| 3 | pure layer stdlib-only | `manifest.py`/`game_state.py` join `PURE_MODULES`; no numpy anywhere pure (numpy only in cmd-tier helpers, Windows side) |
| 7 | `cmd.create` merge/no-op | avoided by construction (fragments/load create fresh objects); count assertions still guard every step |
| 8 | atom identity | §5 conventions (uppercase `ID`, `space=`, `b < 0`, no resi/index keying) |
| 11.3 | manifest schema drift | versioned manifest + every-id smoke (§3) |
| 12 | camera frame / matrix blindness | bake with `camera=0` (§6); object-matrix path is Phase 3's decision |
| 13 | cleanup isolation | §4 sentinel + prefix conventions; ligand adopt-vs-materialize split |
| 15 | perf / event loop | narrow `iterate_state` extraction (never `get_model` on big objects); perf smoke §9 |

---

## 11. Open questions (for the planner)

1. **MOL2 partial-charge readback** — fixture had `NO_CHARGES`; if upload validation (SETUP-03) or
   the detector wants mol2 charges, verify `partial_charge` round-trip in a one-off probe before
   relying on it. LOW risk: SDF-first is already the policy (PITFALL 12).
2. **`states_expected` semantics for multi-record SDF uploads** — mechanics verified (states;
   append-on-reload), policy intentionally deferred to Phase 8. The materializer should assert the
   manifest count and expose a `state_policy` parameter (default: detect on state 1) without
   implementing collapse yet.
3. **`matrix_copy`-based flows** — `cmd.matrix_copy(source_mode=4, target_mode=4)` was not
   characterized (its probe crashed for unrelated reasons before reaching it; the crash itself was
   `get_object_ttt`). If Phase 3's movement model needs matrix copying, spike it then — with
   `get_object_matrix`, not `get_object_ttt`.
4. **Fragment token vocabulary freeze** — the generator's `slot['aa']` tokens must be a fixed
   subset of the verified fragment names (§1.4). The capability table (generation research §2) and
   `manifest.py`'s AA registry should be written from ONE table (recommend: `capability.py` owns
   `AA_TOKENS = {token: {fragment, resn, charge_class}}`), otherwise naming drift recreates
   PITFALL 11.3 for AAs.
5. **Exact grid-pose → translate decomposition** — generation research §5.2 fixes positions;
   whether placement uses per-slot `cmd.translate` (delta from fragment centroid) or one
   `transform_object` per AA with a composed matrix is an implementation choice with identical
   baked results; recommend per-slot translate for simpler assertion math (§6.2).

---

## 12. Probe record (exact commands + verbatim outputs)

All probes run 2026-09-06 from the repo root; scripts live in git-ignored `tmp/` (uncommitted,
Phase-1 precedent `tmp/probe_plugins.py`); fixtures in `tmp/probe_fixtures/`. Invocation:
`timeout 150 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq tmp\\<script>.py" 2>&1 | tail -N`.

### 12.1 `tmp/probe_materialize.py` (fragment inventory, SDF/MOL2, valence, naming, fasta, copy/create)

```
PROBE chempy.path                    C:\Users\nglok\.conda\envs\chemtools-win10\Lib\site-packages\pymol\pymol_path\data/chempy/
PROBE fragments.dir                  C:\Users\nglok\.conda\envs\chemtools-win10\Lib\site-packages\pymol\pymol_path\data/chempy/fragments/
PROBE fragments.pkl_count            114
PROBE fragments.names                ace,acetylene,ala,arg,argn,asn,asp,asph,atp,benzene,...,ct_ala,...,ct_hip,...,cys,ethylene,formaldehyde,formamide,formic,gln,glu,gluh,gly,gtp,hid,hie,hip,his,ile,...,leu,lys,lysn,met,...,nt_ala,...,nt_hip,...,peptide,phe,...,pro,...,ser,thr,...,trp,...,tyr,...,val
PROBE fragment.ala                   OK atoms=10 states=1
PROBE fragment.gly                   OK atoms=7 states=1
PROBE fragment.arg                   OK atoms=24 states=1
PROBE fragment.trp                   OK atoms=24 states=1
PROBE fragment.his                   OK atoms=17 states=1
PROBE fragment.pro                   OK atoms=14 states=1
PROBE sdf.load                       OK atoms=8 states=1 nbonds=7 orders=[1, 2]
PROBE sdf.multistate                 OK states=2 atoms=16
PROBE sdf.reload_append              OK states_after=2
PROBE sdf.formal_charge              OK [('C', 0, 0.0), ('C', 0, 0.0), ('O', 0, 0.0), ('O', -1, 0.0), ('H', 0, 0.0), ('H', 0, 0.0), ('H', 0, 0.0)]
PROBE mol2.load                      OK atoms=8 states=1 nbonds=7 orders=[1, 2]
PROBE setting.valence                default='on' set1='on' unset0='off'
PROBE transform_object.homog1        ERR NameError("name 'round' is not defined")     [probe bug → finding §10.3]
PROBE rotate.camera0                 ERR NameError("name 'round' is not defined")     [ditto]
PROBE get_object_matrix.after_bake   [1.0, 0.0, ... identity]
PROBE transform_selection            ERR NameError("name 'round' is not defined")     [ditto]
PROBE get_unused_name                _aam_01
PROBE group                          OK names=[... 'probe_grp']
PROBE pdb.load                       OK atoms=8
PROBE get_fastastr                   '>probe_pep_A\nAG\n'
PROBE copy.new_name                  OK atoms=8
PROBE create.new_name                OK atoms=8
PROBE copy.id_preserved              True
=== PROBE-01 DONE ===
```

### 12.2 `tmp/probe_materialize2.py` (transforms fixed, protonation variants, bbox)

```
PROBE transform_object.bake          c0 (0.0, 0.0, 0.0) -> (1.0, 2.0, 3.0) coords_ok=True
PROBE transform_object.matrix_after  identity=False                                  [history record — §10.2]
PROBE rotate.camera0                 c0 (1.0, 2.0, 3.0) -> (-2.0, 1.0, 3.0) rotz_ok=True
PROBE translate.camera0              c0 (-2.0, 1.0, 3.0) -> (3.0, 1.0, 3.0) ok=True
PROBE rotate.object_matrix           coords_changed=False matrix_identity=False      [TTT path — §6.1]
PROBE frag.his atoms=17   frag.hid atoms=17   frag.hie atoms=17   frag.hip atoms=18
PROBE frag.asp atoms=12   frag.asph atoms=13  frag.glu atoms=15   frag.gluh atoms=16
PROBE frag.lys atoms=22   frag.lysn atoms=21  frag.arg atoms=24   frag.argn atoms=23
PROBE frag.nt_ala atoms=12  frag.ct_ala atoms=11  frag.ala atoms=10
PROBE frag.his.ringH  H_on_N=['2HE']
PROBE frag.hid.ringH  H_on_N=['1HD']
PROBE frag.hie.ringH  H_on_N=['2HE']
PROBE frag.hip.ringH  H_on_N=['1HD', '2HE']
PROBE frag.ala.bbox   x[-1.6,2.0] y[-2.2,1.9] z[-1.4,1.7]
=== PROBE-02 DONE ===
```

### 12.3 `tmp/probe_materialize3.py` (TTT/bake semantics; flushed prints after first crash)

```
PROBE P3.1 coords_baked              (0.0, 0.0, 0.0) -> (1.0, 2.0, 3.0)
PROBE P3.1 ttt_identity              ttt=None is_ident=True
PROBE P3.1 objmatrix_ident           is_ident=False
PROBE P3.2 reset0_reverts            coords (1.0, 2.0, 3.0) -> (0.0, 0.0, 0.0) reverted=True
PROBE P3.2 objmatrix_after_reset     is_ident=True
<process died at P3.3 — see 12.4>
```

### 12.4 `tmp/probe_hunt2.py` (crash isolation — `get_object_ttt` on a TTT-bearing object)

```
PROBE rotate.object                ok
<process died at cmd.get_object_ttt('pb1') — zero further output, wrapper exit 0>
```

Companion `tmp/probe_crashhunt.py` on a fresh (TTT-less) fragment object:
`get_object_ttt ok type=NoneType`, `get_object_matrix ok len=16` — the crash requires a TTT-bearing
object. (First probe-3/hunt runs lost ALL output because prints were buffered — §10.4.)

### 12.5 `tmp/probe_resn.py` (fragment resn + formal charges)

```
PROBE resn.his    ['HIS']   charge=[0]
PROBE resn.hid    ['HID']   charge=[0]
PROBE resn.hie    ['HIE']   charge=[0]
PROBE resn.hip    ['HIP']   charge=[0, 1]
PROBE resn.asp    ['ASP']   charge=[-1, 0]
PROBE resn.asph   ['ASPH']  charge=[0]
PROBE resn.lys    ['LYS']   charge=[0, 1]
PROBE resn.lysn   ['LYSN']  charge=[0]
PROBE resn.arg    ['ARG']   charge=[0, 1]
PROBE resn.argn   ['ARGN']  charge=[0]
PROBE resn.ala    ['ALA']   charge=[0]
PROBE resn.nt_ala ['ALA']   charge=[0, 1]
PROBE resn.ct_ala ['ALA']   charge=[-1, 0]
=== RESN DONE ===
```

---

## Sources

### Primary (HIGH — executed today in the target runtime)
- Headless probes §12.1–12.5 (scripts + fixtures in git-ignored `tmp/`) — Windows PyMOL 2.5.0,
  Python 3.9.13, `chemtools-win10` env, via the frozen `cmd.exe /c C:\src\run-conda-pymol.bat -cq`
  recipe.
- Local PyMOL 2.5.0 source `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/bioCHEMeleon/tmp/pymol-src/modules/pymol/`:
  `importing.py:41-90, 660-734, 931-960, 1038+`; `creating.py:929-997`; `editing.py:596-648,
  1610-1714, 1716+, 1946-2056, 2100-2166`; `querying.py:89-100, 102-119, 1072-1090`;
  `exporting.py:169`; `editor.py:85-268`; `completing.py:30-36`; `chempy/fragments/__init__.py`;
  `constants.py:36-42`; `_gui.py:483`.

### Secondary (HIGH — previously verified project research)
- `.planning/research/STACK.md`, `ARCHITECTURE.md`, `PITFALLS.md`, `SUMMARY.md` — prior-art-verified
  behavior (PITFALLS 7/8/12/13/15, headless recipe, toolbox citations).
- `.planning/phases/01-bootstrap-pure-foundation/01-04-SUMMARY.md` (path helpers),
  `01-07-SUMMARY.md` + `windows-env-versions.md` (headless runtime facts),
  `01-08-SUMMARY.md` (purity-gate mechanics).
- Prior art `tmp/bioCHEMeleon/biochemeleon/` — `demos.py` (manifest + load + format= rationale),
  `mutation.py` (sentinel/alter/sort/id discipline, collapse_to_single_state), `setup_state.py`
  (DEMO_MANIFEST shape).
- Sibling phase-2 research: `02-RESEARCH-detection.md` §5.1 (atom-record + bond-block contract),
  `02-RESEARCH-generation.md` §3 (candidates/ligand_data contract), §5.2-5.3 (grid geometry,
  materializer contract), :553 (OQ-4 — closed by §1.4 here).

### Metadata

**Confidence breakdown:** SDF/MOL2/fragment/transform/valence behavior — HIGH (probes + source);
manifest/sentinel/identity/pipeline designs — HIGH (built on verified mechanics + proven prior-art
patterns); perf budget derivation — MEDIUM (documented budgets exist; the 1000 ms Phase-2 gate is
a recommendation pending a real measurement). **Research date:** 2026-09-06. **Valid until:**
~2026-10-06 (stable domain; re-probe only if the conda env changes).
