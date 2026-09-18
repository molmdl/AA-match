# Phase 5: PLAY-05 Hint — Research (capability predicates + carbon recolor + color bookkeeping)

**Researched:** 2026-09-18
**Domain:** the Hint feature: the "could form one of the required interactions" capability
predicate (pure), the carbon-only recolor mechanics on PyMOL 2.5.0 (cmd tier), and the
integration with the existing PLAY-01 color snapshot/restore bookkeeping
**Confidence:** HIGH for stack/patterns/pitfalls (every load-bearing claim read from this
repo's own code with file:line, the PyMOL 2.5.0 C/Python source tree, or field-verified
live on the conda build by the probe below); the only LOW items are flagged open questions
(human color preference, 'any'-mode pedagogy scope).

**Citation shorthand:**
- `PA-game` / `PA-gui_game` = `tmp/bioCHEMeleon/biochemeleon/{game.py, gui_game.py}`
  (shipped v1 game, read 2026-09-18) — [PA-OBS] when used as prior-art evidence.
- `pymol-src/<f>` = `/mnt/c/Users/nglok/Desktop/WORKDIR/molmdl/bioCHEMeleon/tmp/pymol-src/<f>`
  (the PyMOL 2.5.0 source tree, C layer included).
- `PROBE` = `tmp/probe_05_hint.py`, authored and RUN by this research on the live Windows
  conda build (2026-09-18): **14/14 checks PASS** — `elem C` completeness, named-color
  existence, carbon-only `cmd.color` read-back, alter+rebuild restore roundtrip,
  green+hint coexistence on one object, and a live-scene capability recomputation.
  It lives in `tmp/` (git-ignored); its verdicts are recorded here, its patterns go into
  the plan's smoke.
- `05-RESEARCH-window-start-timer.md` = the sibling Phase-5 research (committed
  976d508) — the Game-tab/deferred-activation contract this doc coordinates with.
- Repo files cited as plain `path:line`.

---

## Summary

The Hint is the *lowest-risk requirement in the project's riskiest-looking phase* because
its "could form" half **already exists**: `capability.aa_capable(resn, itype,
ligand_profile)` (`aamatch/capability.py:244-304`) is the polarity-aware, direction-refined
predicate the generator already uses for solvability-by-construction
(`aamatch/generator.py:492-496`), and `residue_capabilities(resn, ligand_profile)`
(`capability.py:307-314`) returns the full per-residue type set with a docstring that
**already names the Hint as an intended consumer**. The hint must NOT read the payload
slots' `can_form` field — `generator.py:453-456` pins that field as generation-time
provenance, "NOT the Hint's data source (Hint recomputes capability live via the shared
capability module, PLAY-05)". So the design question is not *what* to compute but *where
the ligand profile comes from* (the engine does not retain it — see below) and *how the
recolor integrates with the PLAY-01 snapshot/restore bookkeeping*.

**Primary recommendation:** one pure helper pair in `capability.py` (`hint_required_types`
resolving the required dict to a type tuple; `hint_candidate_slots` intersecting
`residue_capabilities` with it over the payload slots — TDD battery), one new cmd-tier
engine op `ligand_profile_molecule` (recompute the profile from the LIVE ligand object via
the existing `_remap_ligand_bonds` + `capability.ligand_profile` machinery — the profile is
byte-equal to generation-time because the ligand never changes), and one `GameWizard.hint()`
method (wizard.py, already under the PLAY-04 source gate) that snapshots each candidate
object via the EXISTING `wizard_core.ensure_snapshot` before recoloring its carbons with
`cmd.color(HINT_COLOR, '<obj> and elem C')`. **The single most important finding:** the
wizard's snapshot fires only in `_select_slot` (`wizard.py:321-322`) — a hint recolor that
did NOT `ensure_snapshot` first would leave hint colors stuck after Done (cleanup only
restores snapshotted objects, `wizard.py:202-204`). Registering hint recolors into the SAME
store closes the entire (a)-(f) integration matrix with zero parallel bookkeeping.

**The standard stack is already installed.** No new dependency, no new module, no new gate
entry: pure additions live in an already-registered module (`capability.py`), the recolor
lives in an already-scanned module (`wizard.py`), and the button wiring lives in the
sibling-planned `game_window.py`. `cmd.color` + `elem C` + named colors are verified against
the PyMOL 2.5.0 C source and the live build.

---

## standard_stack

### Core (nothing new to install — everything verified in place)

| Piece | Version/home | Purpose | Why standard (evidence) |
|---|---|---|---|
| `capability.aa_capable` / `residue_capabilities` | in repo, `capability.py:244-314` | THE "could form" predicate | the generator's solvability uses it (`generator.py:493`); DETECT-04 requires hint/scoring/detector to share the one typing home (`capability.py:1-8`, `FEATURES.md` dependency note "Hint must reuse detection in capability mode") |
| `capability.ligand_profile` + `engine._remap_ligand_bonds` | `capability.py:616-676`, `engine.py:114-141` | recompute the live ligand profile | proven at `engine.py:217` (new_game) and `upload.py:155`; SMOKE-03 field-verified the whole pipeline |
| `cmd.color(color, selection)` | PyMOL 2.5.0 (`viewing.py:1858`) | redraw-safe recolor | C source invalidates the color rep cache: `pymol-src/layer3/Executive.cpp:12440-12446` (`OMOP_COLR` + `OMOP_INVA`/`cRepInvColor` + `SceneInvalidate`) — matches the 03-06 display-rebuild law recorded at `wizard.py:225-234` |
| `elem C` selector | PyMOL 2.5.0 selector grammar | carbon-only selection | keyword table `pymol-src/layer3/Selector.cpp:512-516`; `SELE_ELEs` matcher `:7917-7937` matches the atom `elem` string; PROBE check 2: `elem C` count == iterate `elem=='C'` count on a materialized AA |
| `wizard_core.ensure_snapshot` / `color_map` / `snapshot_objects` | `wizard_core.py:158-192` | PLAY-01 color bookkeeping | the ONE store the wizard's cleanup restores (`wizard.py:202-204`) |
| Named color `'orange'` | PyMOL 2.5.0 registered color | hint color candidate | `pymol-src/layer1/Color.cpp:1039` `reg_named_color("orange", 1.F, 0.5F, 0.F)`; PROBE check 3: index 13 live; [PA-OBS] `PA-game:12` shipped `'orange'` for hints ("distinct from green=found") |
| `cmd.iterate(obj, 'stored.append((ID, color))', space=...)` | `wizard.py:208-215`, `smoke_07:206-211` | headless color read-back | the PROBE used it for every assertion; SMOKE-07's `_color_map` is the committed precedent |

### Existing repo seams consumed unchanged

| Seam | Where | Note |
|---|---|---|
| Game tab + Hint button shell | `game_window.py` (NEW per `05-RESEARCH-window-start-timer.md`) | the tab owns the button; the recolor op is this doc's plan |
| Live-wizard dispatch gate | `setup_window.py:797-802` (`isinstance(cmd.get_wizard(), GameWizard)`) | the exact gate the hint handler reuses |
| Required dict access | `wizard.py:327-331` (`_required()`) | hint reads the same `payload['levels'][L]['molecules'][M]` node |
| Payload slots carry the RESN | `generator.py:844` (`'aa': slot['aa']`), `placement.py:110-116` | `slot['aa']` IS the canonical uppercase resn — pure lookup key |
| Slot→object mapping | `wizard_core.build_slot_map` via `wizard.py:132-136` (`_objects_by_slot`) | hint recolors only registered slot objects — the ligand/grid are structurally unreachable |

### Alternatives considered

| Instead of | Could use | Tradeoff |
|---|---|---|
| Pure helpers in `capability.py` | NEW pure module `hint.py` | one more `PURE_MODULES` registration for no isolation gain; `capability.py`'s docstring already claims the Hint as a consumer (`capability.py:4, 309-310`) — single-home wins |
| Engine op recompute of the profile | embed the profile in the payload at generation (level-spec additive field) | a level-spec schema extension + game-file surface change for a trivially recomputable value; recompute is ~20 ms and byte-equal (ligand chemistry is immutable during play) |
| `cmd.color` per candidate | `cmd.alter` + `cmd.rebuild` | alter writes data without rebuilding the drawn lists — the exact 03-06 staleness bug; `cmd.color` is the law-conformant path (C-cited invalidate) |
| Recolor ALL eligible AAs | prior-art style: pick ONE random hider's vicinity (`PA-game:262-269`) | the AA-match spec says "the AA**s** that could form one of the required interactions" (ROADMAP criterion 3, plural) and `PITFALLS.md:452` says "keep it coarse" — deterministic all-candidates is both spec-faithful and idempotent (repeated presses re-apply the SAME set) |
| Hint colors carried in a second wizard store | reuse `_color_store` | a parallel store would double every restore path (cleanup, switch) for no benefit — the single-store rule (rule set below) is strictly simpler |

**Installation:** none — stdlib + `pymol.cmd` + `pymol.Qt` (existing). No new deps (AGENTS.md law).

---

## architecture_patterns

### Recommended module layout (delta; consistent with the sibling research)

```
aamatch/
├── capability.py        # EXTEND (PURE, already registered): + hint_required_types(required)
│                        #   -> tuple of required types ('any' -> all 7 canonical;
│                        #   'list' -> item types, fail-closed on unknown mode/empty items)
│                        #   + hint_candidate_slots(slots, profile, required)
│                        #   -> tuple of slot_ids whose resn is capable of >= 1 required type
├── engine.py            # EXTEND (CMD tier, already outside PURE_MODULES/SCANNED_MODULES):
│                        #   + ligand_profile_molecule(level_index, molecule_index) -> profile
│                        #   (extract restricted to the molecule's ligand object ->
│                        #   _remap_ligand_bonds -> capability.ligand_profile; mirrors
│                        #   detect_molecule's scoping pattern engine.py:361-392)
├── wizard.py            # EXTEND (CMD tier, already scanned by test_wizard_source):
│                        #   + GameWizard.hint() -> _guard(self._hint_impl) — compute
│                        #   candidates (pure helpers), ensure_snapshot per candidate,
│                        #   cmd.color(wizard_core.HINT_COLOR, '<obj> and elem C')
├── wizard_core.py       # EXTEND (PURE, zero-imports — a plain string constant needs none):
│                        #   + HINT_COLOR = 'orange' (next to HIGHLIGHT_COLOR 'green', :53)
└── game_window.py       # NEW (Qt tier, SIBLING'S module): Hint button + handler that
                         #   isinstance-gates cmd.get_wizard() and calls wizard.hint()
tests/
├── test_capability.py   # EXTEND: the pure hint battery (types resolution + candidates)
└── (or) test_generator_invariants.py  # the GEN-04 parity invariant fits either home
smoke/smoke_11_window.py # EXTEND: new hint PART (drive + color asserts + restore asserts)
```

### Pattern 1 — capability-first candidate computation (the DETECT-04 argument)

**What:** the hint NEVER re-derives typing and NEVER reads geometry. Per slot:
`residue_capabilities(slot['aa'], profile) ∩ required_types` non-empty ⇒ candidate.
**When to use:** always — this makes the hint's "could form" IDENTICAL to what
`allocate_slots` guaranteed solvable (same `aa_capable`, same profile) and to what
`score` credits (`game_state.py:74-82`), by construction rather than by convention.
**Example (the pure half, python3.6-safe, no new imports):**

```python
# Source: aamatch/capability.py (new functions; reuse aa_capable, :244 / :307)
def hint_required_types(required):
    """required dict -> tuple of required interaction types.

    - {'mode': 'any', 'items': []} -> ALL 7 canonical types (scoring in
      'any' mode credits ANY formed record, game_state.score:74-75, so
      the hint vocabulary is the full type set; ligand-unsupported types
      yield no candidates because aa_capable gates on the profile).
    - {'mode': 'list', ...} -> the item types, fail-closed: unknown
      mode / empty items / unknown item type raise ValueError (mirrors
      game_state.score:77-85 and wizard_text.required_summary:101-103).
    """
    if not isinstance(required, dict):
        raise ValueError('hint_required_types: required must be a dict '
                         "(found %s)" % type(required).__name__)
    mode = required.get('mode')
    if mode == 'any':
        return tuple(INTERACTION_TYPES)
    if mode == 'list':
        items = required.get('items')
        if not items:
            raise ValueError("hint_required_types: 'list' mode requires a "
                             "non-empty items list (empty items is the "
                             "'any'-mode representation)")
        unknown = [i.get('type') for i in items
                   if i.get('type') not in INTERACTION_TYPES]
        if unknown:
            raise ValueError('hint_required_types: unknown required type(s): '
                             '%s' % ', '.join(str(t) for t in unknown))
        return tuple(i['type'] for i in items)
    raise ValueError('hint_required_types: unknown required mode %r '
                     '(expected one of any, list)' % (mode,))


def hint_candidate_slots(slots, profile, required):
    """Slot ids whose AA could form >= 1 required type with this ligand.

    `slots` = the payload's grid.slots list (plain dicts with 'slot_id'
    and 'aa' resn, generator.py:840-850). Returns the tuple of matching
    slot_ids in PAYLOAD order (row-major, deterministic). Fail-closed:
    a non-list slots value or a slot without 'slot_id'/'aa' raises.
    Distractor slots ARE included when their resn is capable — the
    required slots are a SUBSET (GEN-04 parity, see solvability check).
    """
    if not isinstance(slots, list):
        raise ValueError('hint_candidate_slots: slots must be the '
                         "payload's grid.slots list (found %s)"
                         % type(slots).__name__)
    required_types = frozenset(hint_required_types(required))
    out = []
    for slot in slots:
        if not isinstance(slot, dict) or 'slot_id' not in slot \
                or 'aa' not in slot:
            raise ValueError('hint_candidate_slots: every slot must be a '
                             "dict with 'slot_id' and 'aa' (found %r)"
                             % (slot,))
        caps = residue_capabilities(slot['aa'], profile)
        if caps & required_types:
            out.append(slot['slot_id'])
    return tuple(out)
```

### Pattern 2 — the live profile recompute (engine op mirroring detect_molecule)

**What:** the engine does NOT retain the generation-time ligand profile (`ligand_data` is a
local in `new_game`, `engine.py:275-278`; the module-level state split is
`_payload/_registry/_game` only, `engine.py:92-95`, and the payload carries NO profile —
`level_spec.py:9-35`). The hint recomputes it from the LIVE ligand object.
**Why it is byte-equal:** `capability.ligand_profile(atoms, bonds)` reads only atom
elements/names/charges + bond orders — the ligand object is loaded once at materialize
(`placement.py:328-350`) and never modified (movement is AA-only, `wizard.py:53-72`).
**Example (the cmd half):**

```python
# Source: aamatch/engine.py (new op; mirrors detect_molecule:361-392)
def ligand_profile_molecule(level_index, molecule_index):
    """The CURRENT molecule's ligand chemistry profile, recomputed live
    (the 02-08 deviation-3 contract shape, engine.py:217). The hint's
    "could form" input — DETECT-04 by construction: the SAME
    capability.ligand_profile the generator consumed at generation time
    (generator._profile_of:655-676), over the SAME records."""
    registry = _current_registry()
    molecules = registry['molecules']
    index = int(molecule_index)
    if not 0 <= index < len(molecules):
        raise EngineError(
            'engine.ligand_profile_molecule: molecule_index %d out of '
            'range (registry has %d molecule(s))'
            % (index, len(molecules)))
    lig_object = molecules[index]['ligand'][0]
    records = [r for r in geometry.extract_game_atoms()
               if r['object'] == lig_object]
    lig_records, lig_bonds = _remap_ligand_bonds(records, [lig_object])
    return capability.ligand_profile(lig_records, lig_bonds)
```

### Pattern 3 — the wizard method (recolor + the ONE store)

**What:** `GameWizard.hint()` wraps `_hint_impl` in the established `_guard` pattern
(`wizard.py:423-433`): house errors land on the panel, unexpected ones propagate. The impl
computes candidates, snapshots, recolors. **No new wizard attributes** (the picklability
contract, `wizard.py:17-29`): candidates are recomputed per press and are STATIC within a
molecule (see rule set (c)).

```python
# Source: aamatch/wizard.py (new method, same tier as confirm_molecule:528)
def hint(self):
    """PLAY-05 Hint: recolor the CARBONS of every amino-acid slot that
    could form at least one required interaction (capability-live via
    the shared module; never reads the slot's can_form provenance,
    generator.py:453-456). Recolor only — no lines/dots/geometry
    (PLAY-04; the atom-color property is invisible to detection,
    geometry.py:134-138). Returns plain data for the caller's info box:
    {'count': n, 'slot_ids': [...]}."""
    self._guard(self._hint_impl)

def _hint_impl(self):
    from . import capability, engine
    required = self._required()
    slots = self._payload['levels'][self._level_index] \
        ['molecules'][self._molecule_index]['grid']['slots']
    profile = engine.ligand_profile_molecule(self._level_index,
                                             self._molecule_index)
    candidate_ids = capability.hint_candidate_slots(slots, profile,
                                                    required)
    if not candidate_ids:            # fail-closed (solvability makes
        raise WizardError(           # this unreachable; a silent no-op
            'hint: no amino acid in the grid could form a required '   # would hide a bug)
            'interaction (%s) -- the solvability guarantee was '
            'violated' % (required.get('mode'),))
    for slot_id in candidate_ids:
        obj = self._objects_by_slot[slot_id]
        # THE CRITICAL LINE: register into the ONE store BEFORE the
        # first recolor (cleanup restores exactly these objects,
        # wizard.py:202-204); idempotent when already snapshotted.
        wizard_core.ensure_snapshot(self._color_store, obj,
                                    self._atom_colors(obj))
        cmd.color(wizard_core.HINT_COLOR, '%s and elem C' % obj)
    cmd.refresh_wizard()
    return {'count': len(candidate_ids), 'slot_ids': list(candidate_ids)}
```

### Pattern 4 — the Qt handler (sibling's module, thin)

**What:** the Game tab's Hint button follows the established handler family: thin non-modal
impl, `_guard` for the ValueError family, NO boxes on success (the recolor IS the
feedback — the `_on_start` precedent, `setup_window.py:879-886`).

```python
# Source: aamatch/game_window.py (sibling's NEW module; the handler contract)
def _on_hint(self):
    """Hint button: recolor-capability hint via _guard. NON-MODAL: the
    recolor on-screen is the feedback; no success box (smoke-99 law:
    impls never own boxes; _on_start precedent, setup_window.py:879)."""
    from pymol import cmd
    from . import wizard as wizard_mod
    self._guard(self._hint_now)

def _hint_now(self):
    from pymol import cmd
    from . import wizard as wizard_mod
    prior = cmd.get_wizard()
    if not isinstance(prior, wizard_mod.GameWizard):
        return None          # pre-GO countdown / no game: silent no-op
                             # (PA-gui_game:142-145 precedent); the
                             # window orchestrates wizard activation.
    result = prior.hint()
    # optional: self._log('Hint: %d eligible amino acid(s) highlighted.'
    #                     % result['count'])  -- info-box policy is B's (coordination point)
    return result
```

### Anti-patterns to avoid

- **Reading `slot['can_form']` as the hint source:** it is generation-time provenance
  (`generator.py:453-456`); distractors carry `can_form: []` yet may be perfectly capable
  of a required type — reading it would make the hint MISS solvable paths.
- **Recoloring via `cmd.alter`** (data-only write): the 03-06 display-rebuild law — the
  restore path must `cmd.rebuild`, but the APPLY path should be `cmd.color` (invalidates
  the color rep cache itself, C-cited above).
- **A separate hint-color undo list:** any second store duplicates cleanup/switch/restore
  paths and WILL drift (the (a) bug class below). One store, one restore.
- **Hinting by geometry/proximity** (the prior-art `around 5.0` trick): wrong domain — the
  hint is capability-based; the ligand is always within reach of the grid by construction.
- **Adding the hint to the wizard PANEL buttons:** spec.md:40 puts the Hint button on the
  Game status tab; `wizard_text.panel_entries` button inventory is frozen by pinned tests
  (`tests/test_wizard_text.py`) — do not touch it.

---

## dont_hand_roll

| Problem | Don't build | Use instead | Why |
|---|---|---|---|
| "Could this AA form type X with this ligand?" | a new capability matrix/hand-rolled predicate | `capability.aa_capable` / `residue_capabilities` | already the generator's solvability predicate and the detector's typing source (`detector.py:160-161, 447`); a second matrix = DETECT-04 disagreement by construction |
| The required-type vocabulary for the hint | a mode-to-types switch in the wizard | one pure `hint_required_types` | the mode semantics are shared with scoring ('any' binary / 'list' fraction) and `required_summary`; one fail-closed resolver keeps all three in agreement |
| Ligand chemistry at hint time | re-parsing the file / caching at generation | `engine.ligand_profile_molecule` (extract + `_remap_ligand_bonds` + `ligand_profile`) | the machinery exists and is field-proven (`engine.py:212-217`, SMOKE-03); caching would add a 4th engine global, violating the recorded STATE SPLIT |
| Carbon-atom selection | `name C+CA+CB+...` hand lists | `elem C` (PyMOL selector keyword) | complete by element (PROBE check 2: matches iterate `elem=='C'` exactly on a materialized AA; chempy fragments carry uppercase element symbols); name lists would miss fragment-specific carbon names (aromatic CH, guanidino CZ...) |
| Recolor bookkeeping/restore | a hint-specific undo stack | the existing `ensure_snapshot`/`color_map`/`snapshot_objects` + `cleanup()` | the store is already restored by switch and Done; reuse = zero new restore paths |
| Color name validity | hardcoding RGB | a named color verified on this build (`cmd.get_color_index`) | named colors are registered in the C layer (`Color.cpp:1039` etc.); PROBE verified 7 candidate names live |

**Key insight:** the hint is 80% composition of already-proven primitives. The only NEW
logic is ~30 lines of pure set-intersection — which is exactly what makes it a clean TDD
battery.

---

## The type → predicate table (Q1, pinned from `capability.py:268-302` + detector side rules)

| Type | AA-side predicate (aa_capable) | Ligand-side gate (in the same fn) | Detector side rule (agreement evidence) | Capable-residue counts (test-pinned, STATE 02-05) |
|---|---|---|---|---|
| `h_bond` | (AA has `donors` AND ligand `has_acceptor`) OR (AA has `acceptors` AND ligand `has_donor`) — **direction-refined** (recorded Rule-2 addition, `capability.py:283-286`) | both halves via profile keys | BOTH directions detected with explicit roles: AA-donor→lig-acceptor AND lig-donor→AA-acceptor (`detector.py:722-744`) | 12 |
| `salt_bridge` | AA `charge` sign `'+'` → ligand signs contain `'-'`; AA `'-'` → ligand `'+'`; **neutral His → False** (OQ-3/D2, `capability.py:268-274`) | ligand `charge_signs` | opposite-sign charge-group centers only, either side either role (`detector.py:787-788`) | 4 (LYS/ARG vs ASP/GLU) |
| `pi_stacking` | AA `rings` non-empty AND `ligand_support('pi_stacking')` (ligand aromatic `ring_count >= 1`, `capability.py:288-289, 691-692`) | ligand aromatic rings | AA ring × ligand ring pairs, both aromatic by typing (`detector.py:860-865`) | 4 (HIS/PHE/TRP/TYR) |
| `cation_pi` | (AA charge `'+'` AND ligand `ring_count >= 1`) OR (AA `rings` AND `'+'` in ligand signs) — **D4 either direction** (`capability.py:276-281`) | ligand rings OR ligand cation | both directions detected (`detector.py:936-975`), OQ-4 veto ligand-side only | 6 (union LYS/ARG + aromatic) |
| `hydrophobic` | AA residue-name `hydrophobic` flag (gate §3.4) AND `ligand_support('hydrophobic')` = ligand `has_hydrophobe` (`capability.py:291-292`) | ligand qualifying carbons (all-bonded C/H) | AA side is residue-NAME-based + side-chain carbon names incl. CB; ligand side atom-rule (`detector.py:803-818`) | 8 (ALA VAL LEU ILE PRO PHE MET TRP) |
| `halogen` | AA `acceptors` (O/N/S side chains) AND `ligand_support('halogen')` = `has_halogen_donor` (C–X, X ∈ {Cl,Br,I}; **C-F excluded**) (`capability.py:294-297`) | ligand-side donors ONLY (row 6) | structurally one-directional: AA acceptor role × ligand C-X; "an AA-side halogen donor is unrepresentable" (`detector.py:996-1004`) | 9 (= h_bond acceptor set; Met thioether excluded) |
| `metal` | AA `acceptors` AND `ligand_support('metal')` = `has_metal` (`capability.py:299-302`) | approved metal list in ligand (`ligand_has_metal`, `capability.py:704-712`) | metal enumeration GATED on `capability.ligand_has_metal` before it runs (`detector.py:1044-1050`) | 9 (= h_bond acceptor set) |

**Exported surface to use (Q1 answer):** the hint needs ONLY
`capability.hint_required_types` (new, ~25 lines) + `capability.residue_capabilities`
(existing) + `capability.hint_candidate_slots` (new, ~25 lines). `ligand_support` /
`ligand_has_metal` are consumed *inside* `aa_capable` — the hint must not call them
separately (that would duplicate the gating and invite drift).

**Mode semantics (verified & pinned):**
- `exclusive` → `{'mode': 'any', 'items': []}` (`generator.py:396`) → hint types = **all 7**
  (scoring credits any formed record, `game_state.py:74-75`; `_formed_types` mirrors "every
  type the detector produced", `game_state.py:129-131`). The allowed list is generation-time
  sampling vocabulary only (`generator.py:337-361` docstring; `04-07` checkbox note:
  "unset mode treats the allowed list as sampling vocabulary").
- `block_exclusive` → `{'mode': 'list', 'items': checked types}` (`generator.py:409-410`)
  → hint types = the items (canonical order).
- `unset` → `{'mode': 'list', 'items': sampled subset}` (`generator.py:433-435`)
  → hint types = the items.

---

## The color-integration rule set (Q4 — the (a)-(f) matrix, resolved)

Design rule first, matrix second: **the hint registers every candidate object into the
EXISTING wizard color store (`_color_store`) via `ensure_snapshot` BEFORE recoloring, and
uses `cmd.color` (redraw-safe) restricted to `'<obj> and elem C'`. Restoration stays owned
by the existing machinery — the switch path (`wizard.py:317-319`), Done/cleanup
(`wizard.py:202-204`), and replace-on-restart (`gamestart.start_game` replace=1 pops the
prior wizard, whose cleanup restores) all already iterate that store.**

**(a) Hint BEFORE any selection — the trap and the fix.** Today `ensure_snapshot` fires
ONLY in `_select_slot` (`wizard.py:321-322`). A hint that recolored without snapshotting
would leave its colors after Done: cleanup restores only `snapshot_objects(store)`
(`wizard.py:202-204`), and the hinted-never-selected object is not in the store.
**Fix (mandatory):** `_hint_impl` calls `ensure_snapshot(...)` per candidate object before
its `cmd.color`. Idempotent (`wizard_core.py:172-175`: first call copies, later calls
return False), so a slot first hinted then selected keeps its ORIGINAL pre-hint snapshot.

**(b) Hint AFTER selection (slot already green).** `_select_slot` colors the WHOLE object
green (`cmd.color(wizard_core.HIGHLIGHT_COLOR, obj)`, `wizard.py:323`). If that slot is a
candidate, the hint's carbon-scope recolor lands OVER the green. PROBE check 6 (live):
carbons read the hint index (13), non-carbons stay green (3) — the two feedback layers
coexist per-atom, data-clean. On switch-away or Done, `_restore_slot_colors` writes back the
snapshot (pre-hint = materialization colors) and rebuilds (`wizard.py:239-246`) — full
restore, no residue. Minor UX note (open question 6): the selected slot shows orange
carbons + green everything else while both are active; acceptable, and the panel keeps the
selection state.

**(c) Repeated presses — idempotent by construction.** The candidate predicate is
resn (payload, immutable) × ligand profile (immutable during play) × required (immutable)
⇒ **the candidate set is STATIC within a molecule**; selection/movement never change it.
Each press recomputes the same set and re-applies the same colors → idempotent. No
restore-then-reapply bookkeeping is needed. Self-healing side effect: if a switch-restore
wiped a hinted slot's carbon color, the next hint press re-applies it. (Phase-6 note: if
molecule advancement re-scopes the wizard, a press on the new molecule highlights only that
molecule's slots — the wizard's slot map is already per-molecule, `wizard_core.build_slot_map`.)

**(d) Done/cleanup restore — ONE owner.** The wizard's `cleanup()` is the owner (it runs on
the canonical `cmd.set_wizard()` pop AND on replace-on-restart; `wizard.py:179-206`). The
hint adds no bookkeeping of its own; it only feeds the same store. Reset-to-grid also
leaves colors alone (position-only replay, `wizard.py:588-594`), so hint colors persist
across Reset — same rule as selection green (documented behavior, `wizard.py:584`).

**(e) Hint vs moved AAs.** Movement is `cmd.translate/rotate` with `camera=0` — baked
coordinates, color untouched (`wizard.py:451-452, 471-472`; `placement.translate_to` has no
color writes). Hint color persists across movement. Detection is geometry-only and never
reads color (`geometry.py:134-138` iterates model/ID/name/elem/resn/resv/alt/formal_charge/
x/y/z — no `color`; `grep color` over `aamatch/detector.py` returns ZERO hits).

**(f) PLAY-02 scoring-check interplay.** The standing human check (green-selected AA +
Confirm → 1.00 h_bond) is unaffected: `cmd.color` is a color-property write + color-cache
invalidate (`pymol-src/layer3/Executive.cpp:12440-12446` — `OMOP_COLR`, `OMOP_INVA`
`cRepInvColor`, `SceneInvalidate`); no coordinate field is touched, so
`extract_game_atoms`/`detect` output is byte-identical before/after any recolor. Also
verified in (e): zero color reads in the detector.

**Restart/Cleanup edges (for completeness):** Restart (Start mid-game) pops the prior
wizard via replace=1 — its cleanup restores hint+green colors before the fresh
materialization (`gamestart.py:127-141` conditional; the ORDER LAW already proven).
Cleanup (04-11) pops the wizard then prefix-deletes objects — colors restored, objects
gone. Both paths are covered by the shared store with zero hint-specific code.

---

## Module/tier placement table (Q5)

| Piece | Tier | Home | Notes |
|---|---|---|---|
| `hint_required_types(required)` | PURE | `aamatch/capability.py` (new fn) | single typing home; plain dict in/out; fail-closed ValueError |
| `hint_candidate_slots(slots, profile, required)` | PURE | `aamatch/capability.py` (new fn) | payload-order deterministic tuple; distractors included when capable |
| `ligand_profile_molecule(level, molecule)` | CMD | `aamatch/engine.py` (new op) | mirrors `detect_molecule` scoping; reuses `_remap_ligand_bonds` + `capability.ligand_profile` |
| `HINT_COLOR = 'orange'` | PURE constant | `aamatch/wizard_core.py` (next to `HIGHLIGHT_COLOR:53`) | zero-imports module: a string constant needs nothing; pin in `tests/test_wizard_core.py` alongside the existing exact-constants pin |
| `GameWizard.hint()` / `_hint_impl` | CMD | `aamatch/wizard.py` (new methods) | `_guard` pattern; returns plain data `{'count', 'slot_ids'}` |
| Hint button + `_on_hint` handler | Qt | `aamatch/game_window.py` (SIBLING's NEW module) | isinstance gate → `prior.hint()`; `_guard` for refusals; NO success box |
| Pure tests | WSL | extend `tests/test_capability.py` (or `tests/test_generator_invariants.py` for the parity invariant) | TDD battery — see Verification tiers |
| Smoke | headless PyMOL | extend `smoke/smoke_11_window.py` (new PART before the Gate-A2 echo) | the drive recipe below |

## Gate-impact list

| Gate file | Impact | Exact edit |
|---|---|---|
| `tests/test_purity.py` | **NONE** | `capability.py` and `wizard_core.py` are already registered (`:92-95`); no new pure module, no `ALLOWED_STDLIB` change (no new imports at all — capability needs no import, wizard_core needs no import) |
| `tests/test_wizard_source.py` | **NONE from this feature** | hint logic lives in `wizard.py` (ALREADY scanned, `:51-53`); the sibling adds `game_window.py` for the tab — coordinate so the hint handler there contains no banned calls either |
| `tests/test_code_audit.py` | **NONE** mechanically; discipline only | `PROSE_PIN` (`:64-69`) counts are untouched; new docstrings must not add `get_model`/`matrix_reset`/`get_object_ttt` mentions (wizard.py's zero-mention pin, `test_wizard_source.py:134-146`, applies); the hint does no atom-namespace double loops (P-ban N/A) |
| `tests/test_package_skeleton.py` | **NONE** | `__init__.py` untouched (Gate A2) |
| `smoke/smoke_11_window.py` | EXTEND | new hint PART (below); mind the sibling's PART G rework + echo-letter renumbering — insert before the echo and renumber as they did at 04-10/04-12/04-13 |
| `tests/test_wizard_core.py` | EXTEND (pin) | exact-constants battery gains `HINT_COLOR == 'orange'` |

**TDD verdict: YES** — the pure battery is the natural RED-first plan:
`hint_required_types` (any→7 canonical; list→items; unknown mode → ValueError with the
`game_state.score`-family wording; empty items in list → ValueError), `hint_candidate_slots`
(disjoint cases: required-slot capability, capable distractors INCLUDED, incapable slots
excluded, ligand-unsupported types yield nothing, missing slot keys → ValueError), plus the
**GEN-04 parity invariant**: for real generator payloads, every `role='required'` slot's
`aa` appears in `hint_candidate_slots(slots, profile, required)` (cross-module, cheap,
pins the single-home promise forever).

---

## Verification tiers (headless-provable vs human-checkpoint)

### Headless WSL (pure battery)
1. `hint_required_types`: any → all 7 in canonical order; list → given order; unknown mode /
   empty items / unknown item type → pinned ValueError wording.
2. `hint_candidate_slots`: hand-built profiles covering all 7 types (reuse
   `tests/test_capability.py` profile fixtures): required-slot capable; capable distractor
   included; incapable slot excluded; a type the ligand cannot support yields no candidates;
   deterministic payload order; malformed slots → ValueError.
3. GEN-04 parity invariant: generate a real payload (`generator.generate` with a real
   profile) → assert required slots ⊆ candidates, for several seeds/modes.
4. Agreement pin: for every resn in `AA_RESIDUES`, `residue_capabilities` == the
   per-type `aa_capable` union (already implied by implementation; cheap belt-and-braces).

### Headless PyMOL (SMOKE-11 new PART; cmd-substance, T1a/T1b-safe)
Drive (mirrors the PROBE; note the sibling's PART G rework — activate via the GO step if
the deferred design lands, else `start_game` already activates):
1. `start_game` (defaults or PART E's game) → `wiz = cmd.get_wizard()`.
2. Expected candidates computed in-smoke from the payload via the pure helpers (the cmd
   path and the pure path agree, asserted).
3. `wiz.hint()` → per candidate object: every `elem C` atom color == `cmd.get_color_index('orange')`
   AND every non-carbon color unchanged from its pre-hint read; per non-candidate object AND
   the ligand object: NO atom color changed.
4. Re-press idempotence: second `wiz.hint()` → color maps identical (static set).
5. Hint-over-green: `do_select`-style green on one candidate (or direct
   `cmd.color('green', obj)`) → hint → carbons orange, non-carbons green (PROBE check 6).
6. Restore: canonical Done (`cmd.set_wizard()`) → every snapshotted object's color map ==
   its materialization colors (pre-hint), store cleared; `cmd.get_wizard()` None.
7. (Optional) engine-op assert: `engine.ligand_profile_molecule(0, 0)` returns the profile
   the smoke recomputes from the live ligand (byte-equal keys).

### Human checkpoint (GUI session)
1. Hint visibility on uniform sticks (the 03-06 display-law class: data-level equality is
   proven headlessly; the on-screen redraw needs one human look — cmd.color's invalidate is
   C-cited, so this is expected-pass, not expected-risk).
2. Hint color legibility/distinctness vs the green selection and default element colors.
3. The Game-tab button placement/tooltip (sibling's tier).
4. (If 'any'-mode scope is changed to allowed-list — open question 2 — re-verify the pedagogy
   with the human.)

### Verification recipe for colors (pinned)
`cmd.iterate(obj, 'stored.append((ID, color))', space={'stored': rows})` then compare
against `cmd.get_color_index(HINT_COLOR)` — the `wizard._atom_colors` mechanism
(`wizard.py:208-215`) and SMOKE-07's `_color_map` (`smoke/smoke_07_wizard_loop.py:206-211`)
precedent; PROBE-verified this session.

---

## common_pitfalls

### Pitfall H-1: Hint colors stuck after Done (the (a) trap)
**What goes wrong:** hint recolors objects that were never selected; cleanup restores only
snapshotted objects → orange carbons survive Done.
**Why it happens:** `ensure_snapshot` currently fires only in `_select_slot`.
**How to avoid:** the hint impl snapshots every candidate BEFORE recoloring (Pattern 3).
**Warning signs:** a Done-restore test asserting only green objects restored; the smoke's
step 6 (restore) must cover a hinted-never-selected object — make it assert the WHOLE
scene's color maps, not just the selected slot.

### Pitfall H-2: Reading `can_form` as the hint source
**What goes wrong:** distractor slots carry `can_form: []`; the hint would miss capable
distractors (and mis-teach), while solvability promised them.
**How to avoid:** the generator's own note (`generator.py:453-456`) + the pure helpers
reading `slot['aa']` + `residue_capabilities` only.
**Warning signs:** any new code touching `slot['can_form']` in a hint context.

### Pitfall H-3: A second color store / parallel undo
**What goes wrong:** hint colors restored in one path, missed in another (cleanup vs switch
vs replace-on-restart); drift between stores.
**How to avoid:** one store (`_color_store`), one restore owner (`cleanup()`), one snapshot
entry per object.
**Warning signs:** any new dict/list attribute on GameWizard holding colors.

### Pitfall H-4: `cmd.alter` for the APPLY path
**What goes wrong:** the 03-06 staleness bug class — data changes, drawn lists don't
(`wizard.py:225-234`).
**How to avoid:** `cmd.color` applies (invalidate is C-cited); `cmd.alter`+`cmd.rebuild`
stays ONLY in the restore path (`_restore_slot_colors`).

### Pitfall H-5: Over-scoped selection (recoloring the ligand or cross-molecule slots)
**What goes wrong:** `cmd.color(HINT_COLOR, 'elem C')` (unscoped) would recolor every
carbon in the scene — ligand included, other molecules' AAs included.
**How to avoid:** per-object selection strings only, from `_objects_by_slot` (which is
built for ONE molecule, `wizard_core.build_slot_map:56-112` — the molecule-scoping guard
falls out of the map; mirrors the Confirm cross-molecule guard, `engine.py:361-392`).
**Warning signs:** any hint selection string not built from a registered slot object.

### Pitfall H-6: 'any'-mode semantic drift
**What goes wrong:** scoping the hint to `allowed_interactions` while scoring credits any
type (or vice versa) breaks the DETECT-04 promise and confuses players ("I formed what the
tab asked for; score 0").
**How to avoid:** `hint_required_types` resolves 'any' → all 7 (the scoring-honest
vocabulary); if the human later wants pedagogy-scoped hints, that is a deliberate
spec-level change (open question 2), never a silent asymmetry.
**Warning signs:** hint code referencing `setup` / `allowed_interactions` at all — the
hint consumes the RESOLVED required dict only.

### Pitfall H-7: PROSE_PIN / banned-token drift (P-7 of the sibling research)
New docstrings in `engine.py`/`wizard.py` must not add `get_model`/`matrix_reset`/
`get_object_ttt` mentions (count pins are exact). The hint code has no reason to mention
them — write "the banned matrix calls" style prose if ever needed.

### Pitfall H-8: Pre-GO hint press (deferred-activation interplay)
**What goes wrong:** under the sibling's deferred design, `cmd.get_wizard()` is None during
the countdown; a hint press then would either crash the handler or, under the immediate
fallback, recolor before play starts (spec: the game starts AT GO).
**How to avoid:** the handler isinstance-gates (Pattern 4) → silent no-op when no GameWizard
is active; the recolor op is only reachable through an ACTIVE wizard. Button disabling
during the countdown is the tab's concern (coordination point, open question 5).

---

## common pitfalls — detector/solvability cross-checks (Q7)

- **Solvability construction:** `allocate_slots` refuses a required type with zero capable
  AAs (`generator.py:494-496`) and draws required AAs from
  `[aa for aa in ALL_AA if aa_capable(aa, itype, ligand_profile)]` (`:492-493`).
- **Exclusive refuses a ligand supporting zero allowed types** (`generator.py:390-395`);
  unset draws only from the ligand-supported pool (`:416-417`); block_exclusive refuses
  unsupported checked types (`:403-408`).
- ⇒ For ANY generated payload, `hint_candidate_slots` is **non-empty** and **contains every
  required slot** (same `aa_capable`, same profile). The parity invariant test makes this
  permanent. If a future capability-table edit shrinks a capable set, the invariant
  (and allocate_slots' own refusal) fire together — a designed alarm, not silent drift.
- A hint predicate SMALLER than the solvability guarantee would be a design bug — flagged:
  never filter candidates by anything beyond `aa_capable` (no geometry, no selection state,
  no `can_form`).

---

## Answers to the numbered research questions (condensed)

1. **Capability predicates** — the table above; single home = `aa_capable`/`residue_capabilities`
   (`capability.py:244-314`); `can_form` is NOT the source (`generator.py:453-456`); mode
   resolution pinned; DETECT-04 agreement by construction (same tables the detector reads,
   `detector.py:160-161, 447`).
2. **Prior-art hint pattern** — [PA-OBS] `PA-game:10-12` (HINT_RADIUS 5.0, HINT_COLOR
   'orange' "distinct from green=found"); `PA-game:232-272` `hint()`: object-restricted
   selection (`... and %s` suffix — `around` crosses object boundaries), `cmd.color`
   (redraw-safe), increments a hint counter, no-op when no visible candidate; restore via
   the round BACKUP at cleanup (`PA-game:371-398`) — i.e., hint colors persist until round
   end. Button: `PA-gui_game:45-48` (QPushButton + tooltip), `:99` connect, `:142-147`
   handler (silent return when no game). **Transfers:** object-restricted recolor, distinct
   color, restore-at-teardown, silent no-op guard, non-modal impl. **Changes:** AA-match
   hints by CAPABILITY not proximity; recolors ALL eligible slots (coarse, ROADMAP plural)
   not one random pick; restricts to CARBONS (spec); restore via the shared snapshot store
   (AA-match's per-slot snapshot bookkeeping replaces the v1 whole-object backup);
   counters: prior-art `_hint_count` is display-only (DIFF-01, persisted in the sidecar
   `PA-persistence:50-56, 105, 187`) — spec.md is silent, so v1 AA-match ships NO counter
   (open question 4).
3. **Carbon-only mechanics** — `elem C` (Selector.cpp:512-516, :7917-7937; PROBE check 2:
   exact on materialized fragments; all elems uppercase). `cmd.color` invalidates the color
   rep cache (Executive.cpp:12440-12446) — redraw-safe per the 03-06 law. Sticks rendering
   shows atom colors — verified pattern from the green highlight (03-06 human-verified).
   Hint color: `'orange'` (Color.cpp:1039; PROBE index 13; PA-game:12 precedent; distinct
   from green=3 and from default element colors). Scope: per-candidate-object strings only.
4. **Color bookkeeping** — the (a)-(f) rule set above; single store, snapshot-before-color,
   static candidate set, cleanup owns restore.
5. **Tier placement + gates** — the placement table + gate-impact list above; TDD = YES
   (pure battery); SMOKE = SMOKE-11 new PART with the drive recipe.
6. **Hint button contract** — Game tab (spec.md:40), sibling's `game_window.py`; handler =
   non-modal impl + `_guard`; isinstance gate with silent no-op (PA-gui_game:142-145);
   errors: engine/WizardError refusals surface via `_guard` (panel: wizard `_guard`
   `wizard.py:423-433`; Qt box: `setup_window.py:596-606`); empty candidates → fail-closed
   WizardError (solvability makes it unreachable; a silent no-op would hide a bug);
   molecule-scoped by the wizard's per-molecule slot map (Confirm-guard precedent).
7. **Solvability parity** — verified; parity invariant test recommended (above).
8. **Open questions** — below.

---

## open_questions

1. **Hint color: human-visible preference.** Recommendation `'orange'` — prior-art hint
   color (`PA-game:12`, with the same green/hint pairing AA-match uses), registered on this
   build (`Color.cpp:1039`, PROBE index 13), distinct from `HIGHLIGHT_COLOR='green'`
   (`wizard_core.py:53`) and from default element coloring. Alternatives: `magenta` (8),
   `salmon` (9), `pink` (48) — all verified present (PROBE check 3). HUMAN call.
2. **'any'-mode hint scope: all 7 types (recommended) vs allowed-list subset.** All-7 is the
   DETECT-04/scoring-honest vocabulary (`game_state.py:74-75`); allowed-scoped would be a
   pedagogy preference (the user checked fewer boxes than the game scores). Recommend all-7;
   if the human prefers allowed-scoped, thread the setup's allowed list into the hint — a
   deliberate, testable change (never silent).
3. **Info-box hint line (researcher B's contract).** The impl returns plain data
   (`{'count', 'slot_ids'}`); whether the tab logs "N eligible amino acids highlighted" and
   whether the required-label content reuses `wizard_text.required_summary` wording are B's
   content-policy calls (`05-RESEARCH-window-start-timer.md` Q7). Coordination point: B's
   handler plan should consume the hint impl's return value; no new pure text function is
   forced.
4. **Hint counters/limits.** Spec silent; prior art counted hints (display-only, persisted,
   never score-affecting). Recommend NO counter in v1 (PLAY-05 is recolor-only; Phase 9
   help/stats can add it as additive UI). HUMAN optional.
5. **Hint button state during the countdown.** Under deferred activation the handler
   no-ops; whether the button should be visibly disabled until GO is the tab's UX call
   (sibling P-1). Coordination point only.
6. **Selected-slot visual under hint.** A selected (green) slot that is also a candidate
   shows orange carbons + green non-carbons until it is deselected. Recommend keep (static
   candidate set, data-clean coexistence — PROBE check 6); alternative: skip the current
   selection in the hint (inconsistent semantics for no gain). HUMAN optional.

---

## Sources

### Primary (HIGH confidence — probed or source-verified)
- `tmp/probe_05_hint.py` — authored + RUN on the live Windows conda build (2026-09-18),
  14/14 PASS (checks enumerated above; script in git-ignored `tmp/`).
- `aamatch/capability.py:1-8, 55-58, 92-175, 178-242, 244-314, 363-380, 616-712` — typing
  tables, predicates, ligand profile, single-home doctrine.
- `aamatch/generator.py:313, 337-435, 442-527 (esp. 453-456, 492-496), 750-879` — mode
  semantics, solvability-by-construction, the can_form provenance note, payload shape.
- `aamatch/wizard.py:41-52, 71-75, 100-146, 154-206, 208-246, 248-325, 327-331, 423-433,
  435-594` — contracts, snapshot/restore, `_select_slot`, cleanup, `_guard`, movement.
- `aamatch/wizard_core.py:47-53, 56-124, 158-192` — constants, slot map, store ops.
- `aamatch/engine.py:11-31, 92-111, 114-141, 144-227, 294-311, 361-421` — state split,
  bond remap, profile build, molecule-scoped ops.
- `aamatch/game_state.py:62-138` — score semantics ('any' binary; records_for_molecule).
- `aamatch/geometry.py:115-154` — extract fields (no color); `aamatch/placement.py:60-130,
  151-168, 234-449` — materialization, sentinel, reps, NO color assignment, reset_to_grid.
- `aamatch/detector.py` — zero `color` mentions (grep); per-type builders
  `:708-800, 803-894, 935-975, 996-1065`; capability-table reuse `:160-161, 447`.
- `aamatch/setup_state.py:40-42` — INTERACTION_TYPES canonical order.
- `aamatch/setup_window.py:596-606, 797-816` — `_guard` contract, isinstance pop gate.
- `pymol-src/modules/pymol/viewing.py:1858-1897` — `cmd.color` API; 
- `pymol-src/layer3/Executive.cpp:12392-12470` — ExecutiveColor: `OMOP_COLR` +
  `OMOP_INVA`/`cRepInvColor` + `SceneInvalidate` (redraw-safe apply).
- `pymol-src/layer3/Selector.cpp:512-516, 7917-7937` — `elem`/`element` keyword + matcher.
- `pymol-src/layer1/Color.cpp:45-49, 860, 914, 1039-1063, 1197` — named colors (orange
  1.0/0.5/0.0 et al.).
- `pymol-src/modules/pymol/wizard/__init__.py:17-91` — base Wizard method inventory (no
  `hint` collision).
- `smoke/smoke_07_wizard_loop.py:206-211, 16-25, 44-72` — color read-back + restore
  verification precedent.

### Secondary (MEDIUM/HIGH — shipped prior art, read line-by-line)
- `tmp/bioCHEMeleon/biochemeleon/game.py:10-12, 29-33, 60-63, 100-106, 225-272, 296-317,
  360-400, 410-414` — the hint/reveal implementation + counters + restore-from-backup.
- `tmp/bioCHEMeleon/biochemeleon/gui_game.py:27, 44-52, 62, 99, 139-152` — button wiring,
  silent-return handler, stats display.

### Planning docs (constraints)
- `.planning/STATE.md` (whole file) — inherited facts: 03-06 display-rebuild law, PLAY-01
  snapshot semantics, DETECT-04, 02-08/02-10 scoring, 04-09 handler contract, SCANNED_MODULES
  growth protocol.
- `.planning/research/FEATURES.md:35, 49, 138, 155-159` — hint = capability-mode reuse;
  no-helper-visuals rule; dependency note.
- `.planning/research/PITFALLS.md:452` — "keep it coarse".
- `.planning/research/ARCHITECTURE.md:71-73` — hint named as a controller-level op (AA-match
  realizes it as a GameWizard method + Qt handler).
- `.planning/phases/05-game-status-tab-start-sequence/05-RESEARCH-window-start-timer.md` —
  the sibling contract: `game_window.py`, deferred activation, `_pending_wizard`, SCANNED_MODULES
  gain, info-box ownership (Q7), P-7 prose discipline.
- `spec.md:40` — the Hint requirement verbatim; `.planning/ROADMAP.md:136-145` — criterion 3.
- `.planning/REQUIREMENTS.md:43` — PLAY-05 verbatim.

### Tertiary (LOW — flagged for validation)
- None load-bearing. (The only unverified-on-live claims are cosmetic: which exact orange
  shade reads best against sticks — a human-checkpoint item, not an API claim.)

## Metadata

**Confidence breakdown:**
- Capability predicates / stack: HIGH — read from the repo's own tested code + C source +
  live probe.
- Color-integration rule set: HIGH — every rule traces to a cited line; the (a) trap is the
  one novel finding.
- Pitfalls: HIGH for H-1..H-7 (all precedent-backed); H-8 depends on the sibling's deferred
  design (its recommendation, not yet decided).
- Tier placement / gates: HIGH — derived from the current gate files' literal content.

**Research date:** 2026-09-18
**Valid until:** ~2026-10-18 (stable: the only fast-moving dependency is the sibling's
game_window.py design, which is already written down).
