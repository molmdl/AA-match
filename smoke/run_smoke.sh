#!/usr/bin/env bash
# Run a headless cmd-only smoke against Windows PyMOL.
# Usage: bash smoke/run_smoke.sh smoke/smoke_NN_name.py [timeout_sec]
# Verdict: greps "=== SMOKE-$NN PASS ===" in THIS run's log (exit codes
# cannot carry verdicts through cmd.exe). NN is derived from the script
# basename; a basename without an NN segment falls back to 01 so legacy
# smoke_01_bootstrap keeps working unchanged.
# quick-001 hardening: each invocation tees into its OWN mktemp log so
# parallel smoke runs can never cross-report verdicts; on a missing
# marker the FAIL block prints the script, whether `timeout` killed the
# run (status 124), the log path and the last 40 lines.
set -e
SCRIPT="$1"
TIMEOUT="${2:-120}"
BASE="$(basename "$SCRIPT" .py)"                       # e.g. smoke_02_manifest
NN="$(printf '%s' "$BASE" | sed -n 's/^smoke_\([0-9][0-9]*\)_.*/\1/p')"
[ -n "$NN" ] || NN="01"                                # legacy scripts
OUT="$(mktemp /tmp/smoke_out.XXXXXX.txt)"              # per-run log — no shared file
echo "=== run_smoke: $BASE (timeout ${TIMEOUT}s, log $OUT) ==="
cd "$(dirname "$0")/.."                # repo root = Windows-visible cwd (cmd.exe maps it to C:\...)
timeout "$TIMEOUT" cmd.exe /c "C:\\src\\run-conda-pymol.bat -cq smoke\\$(basename "$SCRIPT")" 2>&1 \
  | tee "$OUT" | tail -60
TMO_STATUS="${PIPESTATUS[0]}"          # FIRST command after the pipeline — anything else resets PIPESTATUS
if grep -q "=== SMOKE-$NN PASS ===" "$OUT"; then
  exit 0
fi
echo ""
echo "=== SMOKE-$NN FAIL ==="
echo "script: $SCRIPT"
if [ "$TMO_STATUS" -eq 124 ]; then
  echo "reason: timeout killed the run after ${TIMEOUT}s (status 124) -- re-run with a larger TIMEOUT arg (some smokes need 180-240s)"
elif [ "$TMO_STATUS" -ne 0 ]; then
  echo "reason: cmd.exe wrapper exited $TMO_STATUS (no PASS marker)"
else
  echo "reason: PASS marker '=== SMOKE-$NN PASS ===' missing from output"
fi
echo "full log: $OUT"
echo "--- last 40 lines of this run ---"
tail -40 "$OUT"
exit 1
