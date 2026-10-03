---
phase: quick-001
plan: 001
type: execute
wave: 1
depends_on: []
files_modified: [tests/test_purity.py, smoke/run_smoke.sh]
autonomous: true

must_haves:
  truths:
    - "Removing any ONE of the 19 names from PURE_MODULES makes the WSL purity suite FAIL (per-name registration pin, mutation-proven)"
    - "Every aamatch/*.py file is either in PURE_MODULES or on a documented non-pure list — a new module can never silently escape all purity gates"
    - "Two concurrent smoke invocations each grep their OWN log — zero occurrences of the shared /tmp/smoke_out.txt remain in run_smoke.sh"
    - "A timeout kill (status 124) is explicitly named in the FAIL block, distinct from a missing PASS marker"
    - "PASS verdict byte-compatible: exit 0 iff '=== SMOKE-$NN PASS ===' appears in that run's output; NN from basename with legacy fallback 01"
  artifacts:
    - path: "tests/test_purity.py"
      provides: "Registration pins for all 19 PURE_MODULES names + package-coverage direction check"
      contains: "TestPureModuleRegistrationPins"
    - path: "smoke/run_smoke.sh"
      provides: "Per-run mktemp log + timeout-vs-missing-marker FAIL diagnostics"
      contains: "PIPESTATUS"
  key_links:
    - from: "tests/test_purity.py pin loop"
      to: "PURE_MODULES list"
      via: "assertIn per name over a 19-name literal, subTest per module"
      pattern: "assertIn"
    - from: "smoke/run_smoke.sh verdict grep"
      to: "per-run log file ($OUT)"
      via: "grep against the mktemp log, never a shared fixed path"
      pattern: 'grep -q "=== SMOKE-\$NN PASS ===" "\$OUT"'
---

<objective>
Close the two verified must-fix concerns from the 2026-10-03 codebase map (.planning/codebase/CONCERNS.md):

1. **Purity registration pins (HIGH):** only 3 of 19 PURE_MODULES entries (generator, game_state, checkpoint) are pinned by tests — deleting any of the other 16 names fails nothing, so Gates A/A2/B/D silently skip unregistered modules and the AGENTS.md law "do not weaken the purity gates" is not mechanically enforced at the list level.
2. **run_smoke.sh hardening (MEDIUM-HIGH):** all smokes tee into ONE shared /tmp/smoke_out.txt (config.json sets parallelization: true, so parallel GSD waves cross-report verdicts) and a timeout kill is indistinguishable from a FAIL-loop except by marker absence.

Purpose: These are the enforcement and measurement infrastructure every later phase inherits — unregistered pure modules are ungated, and flaky/parallel smoke verdicts poison every regression battery.
Output: Hardened tests/test_purity.py + smoke/run_smoke.sh, two atomic commits, mutation-proof recorded in the summary.
</objective>

<execution_context>
@~/.config/opencode/get-shit-done/workflows/execute-plan.md
@~/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@AGENTS.md
@.planning/STATE.md
@.planning/codebase/CONCERNS.md
@tests/test_purity.py
@smoke/run_smoke.sh

**Established facts (spot-checked 2026-10-03, no re-research):**
- `tests/test_purity.py:99-103` — PURE_MODULES has 19 names. Pin classes exist ONLY for generator (294-305), game_state (307-315), checkpoint (318-326).
- `aamatch/` holds exactly 28 .py files: `__init__` + the 19 pure + 8 non-pure (engine, geometry, placement, wizard, gamestart, upload, setup_window, game_window).
- `smoke/run_smoke.sh` is 17 lines: TIMEOUT default 120 (line 10), one shared tee target /tmp/smoke_out.txt (lines 15-16), grep-only verdict (line 17). STATE.md battery notes: several smokes need 180-240 s.
- Baseline WSL suite: 931 tests green (912 + 19 from 8.1). Adding 2 test methods → expect 933.

**Repo laws (binding):** python3.6 for tests ONLY; NEVER pip/apt/conda; `rm` is denied (use the edit tool to mutate/restore, /tmp scratch is fine, no repo junk). Commands from repo root: `python3.6 -m py_compile aamatch/*.py` then `python3.6 -m unittest discover -s tests -v`. Zero sys.modules stubs, ever. Solo main-line commits (single plan, no worktree protocol). Do NOT touch: .planning/codebase/ (TESTING.md line 206 still describes the old shared log — out of scope), ROADMAP.md, historical phase docs that mention /tmp/smoke_out.txt (they are records, not live docs).
</context>

<tasks>

<task type="auto">
  <name>Task 1: Pin all 19 PURE_MODULES registrations + package-coverage gate</name>
  <files>tests/test_purity.py</files>
  <action>
    In tests/test_purity.py, add ONE new TestCase class `TestPureModuleRegistrationPins`, inserted AFTER `TestCheckpointRegistration` (line ~326) and BEFORE `TestNegativeControl`. Keep the 3 existing pin classes (TestGeneratorRegistration / TestGameStateRegistration / TestCheckpointRegistration) BYTE-IDENTICAL — do not fold or delete them; their message wording is the house pattern.

    Method 1 — `test_every_pure_module_name_is_pinned`: a 19-name list literal defined INSIDE the method (not a module-level twin of PURE_MODULES — inline literals are how the 3 existing pins work, and editing the test is the only way to silence it). Docstring must state the law: Gates A/A2/B/D silently SKIP unregistered modules (01-08), so until now removing e.g. 'persistence' failed nothing. Loop with `self.subTest(module=name)` and per-name `assertIn(name, PURE_MODULES, 'aamatch/%s.py must be registered in PURE_MODULES (unregistered pure modules are silently ungated)' % name)` — same message wording style as the existing 3 classes. The 19 names in PURE_MODULES order: setup_state, level_spec, persistence, backup, paths, vec3, spatial, manifest, capability, thresholds, detector, generator, game_state, wizard_core, wizard_text, setup_form, game_file, status_text, checkpoint. NO set-equality and NO length pin — assertIn per name only (additions stay governed by the house per-module pin-class pattern).

    Method 2 (option B, keep it small) — `test_every_package_module_is_registered_or_documented_non_pure`: direction-2 coverage so a brand-new module file can never silently escape all gates. Define a local list `non_pure = ['engine', 'geometry', 'placement', 'wizard', 'gamestart', 'upload', 'setup_window', 'game_window']` (comment: the cmd/Qt-tier modules deliberately outside the purity gates; Gate D still compiles them). Reuse the EXISTING Gate-D directory-scan pattern (`os.listdir(PKG_DIR)` + `.py` filter — os and PKG_DIR already exist at lines 49-59; do NOT add imports). Skip `__init__` explicitly with a comment "Gate A2 covers __init__.py separately". For every other module name (strip `.py`), subTest + `assertTrue(mod in PURE_MODULES or mod in non_pure, ...)` with a message naming the file and instructing: register it (and gate it) or add it to the non-pure list with a reason. This is a REGISTRATION check ONLY — do NOT re-implement import scanning (find_bad_imports/Gate A already does that).

    Then run the mutation proof (verification only — NEVER commit the mutated state):
    a. With the edit tool, temporarily delete `'persistence', ` from the PURE_MODULES literal (line ~99-103).
    b. Run `python3.6 -m unittest tests.test_purity -v` — `test_every_pure_module_name_is_pinned` MUST fail (subTest module=persistence, the assertIn message). Gate A/B simply shrink scope (they iterate PURE_MODULES), so this pin should be the only failure.
    c. Restore `'persistence', ` with the edit tool; re-run — all green.
    d. Record the observed FAIL/PASS output in the summary.

    Commit ONLY the restored file: `test(quick-001): pin all 19 PURE_MODULES registrations + package coverage gate`.
  </action>
  <verify>
    From repo root:
    1. Mutation proof (step above): removing 'persistence' from PURE_MODULES makes `python3.6 -m unittest tests.test_purity -v` FAIL on test_every_pure_module_name_is_pinned; after restore it PASSES. Both observations recorded in the summary; `git diff` clean of the mutation before commit.
    2. `python3.6 -m py_compile aamatch/*.py` → exit 0, silent.
    3. `python3.6 -m unittest discover -s tests -v` → 933 tests (931 prior + 2 new), OK, zero failures/errors; the 3 legacy pin classes still present (`grep -c "Registration(unittest.TestCase)" tests/test_purity.py` → 3).
    4. `grep -c "sys.modules" tests/test_purity.py` → unchanged from baseline (docstring mentions only; NO new stubbing code).
  </verify>
  <done>
    All 19 names fail the suite individually if removed from PURE_MODULES (proven via the persistence mutation); every aamatch/*.py file must be registered-or-documented-non-pure (both directions enforced); full WSL suite 933/933 green; zero stubs; 3 legacy pin classes untouched; single atomic `test(quick-001)` commit.
  </done>
</task>

<task type="auto">
  <name>Task 2: run_smoke.sh — per-run logs + timeout-vs-missing-marker FAIL block</name>
  <files>smoke/run_smoke.sh</files>
  <action>
    Rewrite smoke/run_smoke.sh (17 lines) to the exact shape below. Verdict semantics stay byte-compatible: the PASS marker `=== SMOKE-$NN PASS ===` grep is the single verdict; NN derivation (sed over basename, empty → 01 legacy fallback), the `cd`-to-repo-root line, the cmd.exe invocation string (backslash escaping is load-bearing), `set -e`, and `tail -60` console streaming are ALL unchanged.

    ```bash
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
    ```

    WHY each property holds (do not break them):
    - `TMO_STATUS="${PIPESTATUS[0]}"` must be the IMMEDIATE next command after the pipeline (bash resets PIPESTATUS on any intervening command). The pipeline's own exit status is tail's (0), so `set -e` still never fires on a timeout — today's property preserved.
    - The `grep -q` moves INSIDE an `if` condition (set -e exempts condition-position commands), so the script can print diagnostics; explicit `exit 0` / `exit 1` preserves today's contract: script exit == grep verdict (0 pass / 1 fail).
    - mktemp gives a unique log per invocation (parallel GSD waves can no longer cross-report). Logs persist in /tmp for inspection — do NOT clean up (`rm` is denied; the OS owns /tmp).
    - The start-echo (timeout value + log path) is deliberate: several smokes need 180-240 s per STATE.md battery notes, so a 120 s default kill must be self-explaining.
    - ZERO occurrences of the fixed shared path `/tmp/smoke_out.txt` may remain in the script.

    Do NOT edit .planning/codebase/TESTING.md (describes the old shared log — out of scope per repo laws) or any historical phase doc referencing /tmp/smoke_out.txt.

    Commit: `fix(quick-001): per-run smoke logs + timeout-vs-missing-marker FAIL block in run_smoke.sh`.
  </action>
  <verify>
    From repo root:
    1. `bash -n smoke/run_smoke.sh` → exit 0, silent (syntax).
    2. `grep -c "/tmp/smoke_out.txt" smoke/run_smoke.sh` → 0 matches (shared log eliminated); `grep -n "PIPESTATUS" smoke/run_smoke.sh` → present; `grep -n 'sed -n' smoke/run_smoke.sh` → NN derivation line unchanged.
    3. FAIL-path proof (fast, no long wait): `bash smoke/run_smoke.sh smoke/no_such_smoke_zz.py 30; echo "exit=$?"` → expect the `=== SMOKE-01 FAIL ===` block (NN legacy fallback → 01), a `reason:` line (either "marker missing" or "cmd.exe wrapper exited N" — PyMOL errors on the nonexistent script; either branch is acceptable), the `full log:` path, the last-40 tail, and exit=1.
    4. Real PASS run (load-bearing): `bash smoke/run_smoke.sh smoke/smoke_01_bootstrap.py; echo "exit=$?"` → allow ~120 s → console shows the `=== run_smoke: smoke_01_bootstrap (timeout 120s, log /tmp/smoke_out.XXXXXX.txt) ===` header and `=== SMOKE-01 PASS ===` in the tail; exit=0. The header's log path contains the PASS marker when grepped.
  </verify>
  <done>
    Syntax-clean script with zero shared-log references; FAIL path proven end-to-end on a bogus script (exit 1 + named reason + log path + tail); real SMOKE-01 PASS run exits 0 with byte-compatible verdict semantics (same marker grep, same NN derivation, exit == grep verdict); parallel-safe per-run logs; single atomic `fix(quick-001)` commit.
  </done>
</task>

</tasks>

<verification>
Full gates, in order, from repo root (both tasks landed):
1. `python3.6 -m py_compile aamatch/*.py` → exit 0.
2. `python3.6 -m unittest discover -s tests -v` → 933 tests, OK, zero failures (includes purity gates with the new pins).
3. `bash -n smoke/run_smoke.sh` → exit 0.
4. `bash smoke/run_smoke.sh smoke/smoke_01_bootstrap.py` → `=== SMOKE-01 PASS ===`, exit 0 (the one real headless smoke proof; allow ~120 s).
5. `git log --oneline -2` → exactly the two quick-001 commits (test then fix), no mutated intermediates.
</verification>

<success_criteria>
- CONCERNS.md issue 1 CLOSED: all 19 PURE_MODULES entries pinned (mutation-proven on 'persistence'); new modules cannot silently escape gates (coverage direction enforced).
- CONCERNS.md issue 2 CLOSED: per-invocation smoke logs (parallel-wave cross-report impossible); timeout (124) explicitly distinguished from missing-marker in a printed FAIL block with log path + last-40 tail.
- Verdict semantics byte-compatible: PASS marker grep unchanged, NN derivation + legacy fallback unchanged, exit status still equals the grep verdict, `set -e` pipeline behavior preserved.
- Full WSL suite green (933), one real headless smoke green (SMOKE-01), two atomic conventional commits (`test(quick-001)`, `fix(quick-001)`), mutation check recorded in the summary and never committed.
</success_criteria>

<output>
After completion, create `.planning/quick/001-purity-pins-smoke-hardening/001-SUMMARY.md` recording: the mutation-proof observations (FAIL on removal / PASS after restore, verbatim test lines), the SMOKE-01 run verdict + exit code, the FAIL-path proof output, and any deviations. The orchestrator performs the final `docs(quick-001)` STATE.md commit.
</output>
