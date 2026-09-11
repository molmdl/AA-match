# External Integrations

**Analysis Date:** 2026-09-12

> **Bottom line:** This plugin has **no live external integrations**. It is an
> offline, single-process PyMOL plugin: no network calls at runtime
> (enforced by scope — `.planning/PROJECT.md:45` "Network access at gameplay
> time — demo data is pre-downloaded and committed"), no databases, no auth,
> no webhooks, no CI. The only OS-level "integration" is the WSL→Windows
> process bridge used for development testing.

## APIs & External Services

**Runtime network calls:**
- None. Verified: no `requests`/`urllib`/`http` imports anywhere in `aamatch/`, `tests/`, or `smoke/` (pure layer imports stdlib only; `aamatch/paths.py:17`, `aamatch/persistence.py:28-30`, `aamatch/backup.py:42-46` etc.). Demo molecules are bundled and committed (`aamatch/data/ligands/*.sdf`).
- Interaction-detection libraries (proLIF/PLIP/binana) are explicitly excluded as runtime dependencies (`.planning/PROJECT.md:43`) — detection is implemented in-house in `aamatch/detector.py`.

**Authoring-time (human/agent curation, not runtime):**
- PDB / SDF molecular databases (RCSB PDB, PubChem class) — planned sources for curated demo sets. Protocol: agent proposes IDs with citations → human verifies/approves → only then fetch/commit (`.planning/PROJECT.md:53`). Citation log target: `docs/DETECTION_THRESHOLDS.md` (currently holds verified threshold citations) and the README demo table (`README.md:34+`, still TBD placeholders). None fetched yet in-repo.

## Data Storage

**Databases:**
- None. All persistence is local JSON files:
  - Setup/game-state JSON via `aamatch/persistence.py` (stdlib `json` + atomic tempfile writes, `aamatch/persistence.py:28-30`; container format with `FORMAT_VERSION`).
  - Level specs via `aamatch/level_spec.py` (payload gated by `DETECTOR_VERSION` exact-match).
  - Backup snapshots via `aamatch/backup.py` (hashlib-verified snapshots).

**File Storage:**
- Local filesystem only:
  - Bundled demo data inside the installed package — `aamatch/data/MANIFEST.json` + `aamatch/data/ligands/benzamide.sdf`, `aamatch/data/ligands/acetate.sdf` (resolved via `aamatch/paths.py:54 package_data_path()`, anchored to `__file__`, never cwd).
  - Save files go to user-chosen paths via Qt file dialogs.
  - PyMOL session saves use built-in `cmd.save` (`.pse`).

**Caching:**
- None.

**Molecular file formats (I/O vocabulary):**
- Read: SDF via `cmd.load` (bundled ligands; headless-probed OK for forward-slash and space-containing Windows paths — `.planning/phases/01-bootstrap-pure-foundation/windows-env-versions.md:27-28`).
- Write: JSON sidecars + PyMOL `.pse` sessions (`cmd.save`).

## Authentication & Identity

**Auth Provider:**
- None. Single-user desktop plugin; no accounts, no tokens, no API keys anywhere in the repo.

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry-style service).

**Logs:**
- PyMOL console output only (plugin prints / Python tracebacks surface through PyMOL's menu handler — see `aamatch/__init__.py:37` "PyMOL's menu handler surfaces the traceback").
- Smoke verdicts: `=== SMOKE-NN PASS ===` markers grepped by `smoke/run_smoke.sh:17` (exit codes cannot carry verdicts through cmd.exe).
- Smoke transcripts teed to `/tmp/smoke_out.txt` (`smoke/run_smoke.sh:16`).

## CI/CD & Deployment

**Hosting:**
- Not applicable — desktop plugin. Distribution = shared repo / zip installed via PyMOL Plugin Manager into `%APPDATA%\pymol\startup\aamatch\` (`README.md:22-28`).

**CI Pipeline:**
- None. Verification is manual/agent-driven via the standing gates (root `AGENTS.md`):
  - `python3.6 -m py_compile aamatch/*.py`
  - `python3.6 -m unittest discover -s tests -v`
  - `bash smoke/run_smoke.sh smoke/<script>.py`
- Git is local/undetermined-remote; commit style = Conventional Commits with phase scope (`feat(02-03):`).

**WSL↔Windows bridge (dev-only integration surface):**
- `smoke/run_smoke.sh` → `cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\<script>"` — launches Windows-conda PyMOL 2.5.0 headless from the WSL shell; repo root must be a Windows-visible `/mnt/c` path and the runner `cd`s to repo root first (`smoke/run_smoke.sh:14-16`).
- Windows PyMOL cannot resolve WSL `/mnt/...` paths embedded in script arguments, so all file-API paths route through `aamatch/paths.py:20 to_windows_path()` (converts `/mnt/c/...` → `C:\...`; idempotent guard).
- Windows GUI launch (human checkpoints) uses `setenv.bat` (user-side, not in repo; referenced by `.planning/PROJECT.md:52`).

## Environment Configuration

**Required env vars:**
- None. Zero environment-variable configuration in plugin code.

**Secrets location:**
- Not applicable — no secrets exist in this project (no keys, no tokens, no `.env`).

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None.

**In-process callback surfaces (not network webhooks, listed for completeness):**
- PyMOL plugin loader hooks: `__init_plugin__(app=None)` (`aamatch/__init__.py:16`) and menu callback `run_plugin_gui` (`aamatch/__init__.py:29`).
- PyMOL wizard event callbacks: `do_pick`/`do_select`/`do_key` on `GameWizard` (`aamatch/wizard.py`) — the gameplay input surface inside the viewer.
- PyMOL keyboard shortcuts can be registered via `cmd.set_key` (available, use per-phase need).

---

*Integration audit: 2026-09-12*
