> This is a vibe-coding project. While the human attempt to verify the source of all 
> contents, if you find any issues please contact me.
> 
> !! Under Development !!

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
| Easy | 
| Easy | 
| Easy | 
| Hard | 
| Hard | 
| Hard | 
| Challenge | 
| Very challenging | 
| Very challenging | 

Full attribution in `DATA_SOURCES.md`.

## Project Structure

```
#TBD
```

## License

BSD 3-Clause — see [LICENSE](LICENSE).

## Acknowledgements

Demo data courtesy of `TBD`

---
