#!/usr/bin/env bash
# Run a headless cmd-only smoke against Windows PyMOL.
# Usage: bash smoke/run_smoke.sh smoke/smoke_NN_name.py [timeout_sec]
# Verdict: greps "=== SMOKE-$NN PASS ===" in the teed output (exit codes
# cannot carry verdicts through cmd.exe). NN is derived from the script
# basename; a basename without an NN segment falls back to 01 so legacy
# smoke_01_bootstrap keeps working unchanged.
set -e
SCRIPT="$1"
TIMEOUT="${2:-120}"
BASE="$(basename "$SCRIPT" .py)"                       # e.g. smoke_02_manifest
NN="$(printf '%s' "$BASE" | sed -n 's/^smoke_\([0-9][0-9]*\)_.*/\1/p')"
[ -n "$NN" ] || NN="01"                                # legacy scripts
cd "$(dirname "$0")/.."                # repo root = Windows-visible cwd (cmd.exe maps it to C:\...)
timeout "$TIMEOUT" cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\$(basename "$SCRIPT")" 2>&1 \
  | tee /tmp/smoke_out.txt | tail -60
grep -q "=== SMOKE-$NN PASS ===" /tmp/smoke_out.txt   # exit nonzero if the marker is missing
