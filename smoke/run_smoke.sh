#!/usr/bin/env bash
# Run a headless cmd-only smoke against Windows PyMOL.
# Usage: bash smoke/run_smoke.sh smoke/smoke_01_bootstrap.py
set -e
SCRIPT="$1"
cd "$(dirname "$0")/.."                # repo root = Windows-visible cwd (cmd.exe maps it to C:\...)
timeout 120 cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\$(basename "$SCRIPT")" 2>&1 \
  | tee /tmp/smoke_out.txt | tail -60
grep -q "=== SMOKE-01 PASS ===" /tmp/smoke_out.txt   # exit nonzero if the marker is missing
