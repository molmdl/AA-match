> This is a vibe-coding project. While the human attempt to verify the source of all 
> contents, if you find any issues please contact me.
> 

# AA-match

A matching game of small molecule and biomolecular interactions based on common (bio-)molecular viewer.

For students and educators who want an engaging way to explore and study molecular interactions.

---

## Requirements

- **PyMOL 2.5.0** (anaconda build or equivalent)
- PyQt5 (bundled with PyMOL's Qt GUI — no extra install)
- numpy (PyMOL build dependency — no extra install)

> No external Python dependencies beyond what PyMOL already ships. If any are introduced later, they will be listed for explicit user approval and either user-installed or vendored into `./3rd_party_lib/` (git-ignored) with their license noted.

## Install

PyMOL's **Plugin Manager** can copy the package into a plugin directory:

1. In PyMOL: `Plugin → Plugin Manager`, then the install-new / install-from-local-file entry.
2. Point the file picker at the package's `__init__.py` file — for this repo,
   `AA-match/aamatch/__init__.py` — **not** at the `AA-match/` directory.
3. PyMOL registers a **AA-match** item under the Plugins menu.

> **Verified route (development):** the install exercised and approved for this
> project is the plugin-**path** method — add the repo root to PyMOL's plugin
> path. Code edits are then live in the running PyMOL with no reinstall.

> **Never install both ways at once.** One PyMOL session must see exactly one
> copy of the plugin; a plugin-path entry plus a Plugin-Manager copy import as
> two separate modules, and the plugin's shared state breaks.

## Usage

1. **Launch.** In PyMOL, open `Plugin → AA-match`. A modeless window titled
   **AA-match Setup** opens with two tabs: **Setup** and **Game status**.

2. **Choose molecules.** Pick a bundled demo set from the dropdown (grouped by
   difficulty tier), or choose **Upload my molecules...** and browse to one
   SDF or MOL2 file — a multi-record file gives several molecules. Uploads
   accept up to 50 records and are session-only (they are not saved into setup
   files). On this build MOL2 is refused with a clear message; use **SDF**.

3. **Set the game.** Choose the small molecules per level (1–10, default 2),
   the difficulty levels (1–10, default 3), the required-interactions mode
   (any allowed / exactly the checked set / random), and which of the 7
   interaction types are eligible.

4. **Start.** Press **Start**: any previous game is cleaned up, the levels are
   generated, a 3-2-1 countdown runs, then play begins with the ligand fixed
   and the amino acids arranged around it on a grid.

5. **Play in the 3D viewer.** Click an amino acid to select it (it highlights).
   Then drag it:
   - **shift + left-drag** — move it in the view plane
   - **ctrl + shift + left-drag** — change its depth
   - **shift + right-drag** — rotate it

   The panel's **Toward ligand** button nudges the selection 2.5 Å closer.
   The **Game status** tab tracks the time, the required interactions, and a
   rolling log.

6. **Score.** Press **Confirm** to check the required interactions. The
   molecule passes only when **all** of them are formed; a failed Confirm
   records nothing — adjust the pose and Confirm again. Each required
   interaction is scored independently (formed or not); extra interactions
   never inflate the score.

7. **Manage the game.** **Hint** highlights amino acids that could still form
   a required interaction. **Skip Molecule** keeps the partial score; it and
   **Give Up** both ask for confirmation. **Reset** puts the amino acids back
   on their grid positions (orientations kept); **Restart** replays the stored
   initial state. **Done** closes the board — the game is abandoned, with no
   record and no endgame screen.

8. **Finish.** Clear every level to reach the win screen, or **Give Up** for
   the summary at the current point. The endgame shows the per-level scores,
   total score, time, and skips.

9. **Save / share.** **Save** writes a checkpoint `.aamz` (PyMOL session +
   game state; resumes exactly where it stopped). **Generate and export** on
   the Setup tab writes a shareable `.aamatch.json` game file. **Save Setup**
   and **Load Setup** use `.aam.setup.json`. **Import** is the one button for
   both the `.aamz` checkpoint and the `.aamatch.json` game file — it
   dispatches on the file's container header, not its name.

## Demo Molecules set

| Tier | Category | Source | ID(s) | Needs network? |
|------|----------|--------|-------|----------------|
| Easy | Everyday organics (demo-easy-1) | NCBI PubChem (public domain) | aspirin, benzoic_acid | No |
| Easy | Metabolites & ions (demo-easy-2) | NCBI PubChem (public domain) | citric_acid, acetate | No |
| Easy | Caffeine (demo-easy-3) | NCBI PubChem (public domain) | caffeine | No |
| Hard | Trypsin classics (demo-hard-1) | NCBI PubChem (public domain) | benzamidine, guanidinium | No |
| Hard | Charged messengers (demo-hard-2) | NCBI PubChem (public domain) | glutamic_acid, acetylcholine | No |
| Hard | Cofactors (demo-hard-3) | NCBI PubChem (public domain) | atp, nad | No |
| Challenge | Halogen & alkaloids (demo-challenge-1) | NCBI PubChem (public domain) | chloramphenicol, quinine | No |
| Very challenging | Big & iodinated (demo-veryhard-1) | NCBI PubChem (public domain) | folic_acid, thyroxine | No |
| Very challenging | Metalloporphyrin (demo-veryhard-2) | wwPDB CCD (CC0 1.0) | heme | No |
| Easy | Phase-2 development set (demo-dev-1) - development fixture, script-built in-repo (no download) | (none - generated in this repo) | benzamide, acetate | No |

All bundled files ship with the plugin - no network is needed to play. Full per-file provenance (sources, licenses, DOIs, sha256) in [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).

At the default settings (2 small molecules per level), three sets cannot start and refuse with a clear message: demo-easy-3 and demo-veryhard-2 (single-entry sets) and demo-veryhard-1 (its small-molecule pool is too thin at level 0). Lower 'Small molecules per level' or choose another set.

demo-dev-1 is a development fixture kept for regression testing; it appears in the dropdown's Easy group.

## Project Structure

```
aamatch/                     # plugin package - 29 modules in 3 enforced tiers
  __init__.py                # entry point: AA-match menu item; zero module-level imports

  PURE tier (20 modules; no pymol / Qt / numpy - pinned by tests/test_purity.py)
    persistence.py           # versioned containers + atomic I/O
    detector.py              # 7-type geometry detection
    thresholds.py            # approved detection constants
    generator.py             # level generation + solvability
    game_state.py            # scoring + game state
    level_spec.py            # versioned level-spec container
    setup_state.py           # 7-field setup schema
    capability.py            # AA / ligand atom typing
    manifest.py              # MANIFEST parsing + entry enumeration
    game_file.py             # shareable game file + upload splitting
    checkpoint.py            # .aamz sidecar + zip I/O
    status_text.py           # status-log / endgame text
    wizard_text.py           # panel / prompt text
    wizard_core.py           # movement math + color constants
    spatial.py               # cell-list candidate pairs
    vec3.py                  # vector math
    backup.py                # snapshot / restore policy
    paths.py                 # path guard + package-data lookup
    setup_form.py            # setup-form helpers + tier-grouped rows
    help_text.py             # canonical in-game help content

  CMD tier (6 modules; the non-UI layer that drives PyMOL's cmd)
    engine.py                # game operations (generate / detect / record / advance)
    geometry.py              # atom extraction + bounding sphere
    placement.py             # amino-acid materialization + grid bake
    upload.py                # uploaded-molecule bridge
    gamestart.py             # start / import / checkpoint seams
    wizard.py                # play wizard (pick, drag, confirm)

  Qt tier (2 modules; the two-tab window shell)
    setup_window.py          # Setup tab + Help dialog
    game_window.py           # Game-status tab (timer, log, endgame)

  data/                      # bundled demo molecules
    MANIFEST.json            # 10 sets / 18 entries
    ligands/*.sdf            # 18 single-record SDF files

tests/                       # python3.6 WSL test battery
smoke/                       # headless Windows PyMOL smokes 01-25 + run_smoke.sh
scripts/build_demos.py       # reproducible demo pipeline
scripts/demo_specs/*.json    # 10 demo-set specs
```

The PURE tier imports only the standard library plus other pure modules -
never PyMOL, Qt, or numpy. The CMD tier is the non-UI layer that drives
PyMOL's `cmd`; the Qt tier is the two-tab window shell.

`tests/` holds the python3.6 WSL battery; the standing gates pin the
plugin's purity (`test_purity.py`), the cmd-tier source contracts
(`test_wizard_source.py`), AST audits (`test_code_audit.py`), and the demo
data (`test_demo_data.py`, `test_demo_supply.py`). `smoke/` runs the
headless Windows PyMOL battery: module identity, every demo set loading,
the end-to-end loops, and the performance budgets. `scripts/build_demos.py`
plus `scripts/demo_specs/*.json` are the reproducible demo pipeline
(`--report-only` re-derives every entry).

Development planning records live under `.planning/` (not shipped).

## License

BSD 3-Clause — see [LICENSE](LICENSE).

## Acknowledgements

Demo data courtesy of NCBI PubChem (public domain) for 8 of the 10 bundled sets and the wwPDB Chemical Component Dictionary (CC0 1.0) for the heme set, with full per-file attribution in [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md). The development fixture set is generated inside this repository.

---
