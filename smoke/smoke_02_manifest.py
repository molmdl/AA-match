"""Headless smoke 02 - every-manifest-id load proof (GEN-02 supply,
PITFALL 11.3 anti-drift; plan 02-04).

Run (from WSL, repo root):  bash smoke/run_smoke.sh smoke/smoke_02_manifest.py
Verdict is carried by the printed marker (exit codes cannot carry verdicts
through the cmd.exe wrapper): grep '=== SMOKE-02 PASS ==='.

For every manifest entry (pure container parsed INSIDE PyMOL -- the gate
chain must survive there): resolve the package-data file through the
(01-04) path helpers, cmd.load into a private _aam_tmp* object, then
count-assert atom_count / bond_order multiset / formal_charge_sum /
states_expected / sha256 / metal+halogen flags against the manifest
exactly. Objects are deleted in a finally so no entry can leak a temp
object into the next one; a final object-list check proves zero leakage.

Conventions (frozen Phase 1, kept): anchor repo root via sys.argv first /
cwd fallback (never __file__); import aamatch directly (module identity
'aamatch' -- never also plugin_load in the same session); every print on
ONE line and flushed; iterate uses an explicit space dict and no round()
in the expression (expression sandbox).

Python floor: runs inside PyMOL's Windows Python (3.9); written 3.6-safe.
"""
import hashlib
import os
import sys
import traceback


def _find_repo_root():
    """Anchor the repo root WITHOUT trusting __file__ (01-07 discovery:
    inside a -cq script __file__ points at pymol/__init__.py)."""
    mine = 'smoke_02_manifest.py'
    for arg in sys.argv:
        if arg.endswith(mine) and os.path.exists(arg):
            return os.path.dirname(os.path.dirname(os.path.abspath(arg)))
    return os.getcwd()


_ROOT = _find_repo_root()
print('SMOKE-ENV root:', _ROOT, flush=True)

failures = []


def check(name, cond, detail=''):
    print('SMOKE-02 %-38s %s %s' % (name, 'PASS' if cond else 'FAIL', detail),
          flush=True)
    if not cond:
        failures.append(name)


if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pymol import cmd  # noqa: E402

# Pure gates run inside PyMOL: read + parse the versioned container there.
from aamatch.persistence import read_json_file  # noqa: E402
from aamatch.manifest import parse_manifest_dict, enumerate_entries  # noqa: E402
from aamatch.paths import package_data_path, to_windows_path  # noqa: E402

print('SMOKE-ENV pymol: %s' % (cmd.get_version()[0],), flush=True)
print('SMOKE-ENV python: %s' % (sys.version.split()[0],), flush=True)

# DETECT-03 approved semantics (02-01): metal list {MG ZN FE CA MN CU NI CO
# CD} (distance-only); halogen donors {Cl Br I} -- C-F excluded.
_MANUAL_METALS = frozenset(
    ('MG', 'ZN', 'FE', 'CA', 'MN', 'CU', 'NI', 'CO', 'CD'))
_MANUAL_HALOGENS = frozenset(('CL', 'BR', 'I'))

entries = []
try:
    manifest_path = os.path.join(_ROOT, 'aamatch', 'data', 'MANIFEST.json')
    container = read_json_file(manifest_path)
    payload = parse_manifest_dict(container)
    entries = enumerate_entries(payload)
    check('manifest parse', len(entries) == 2,
          'entries=%d' % len(entries))
except Exception:
    traceback.print_exc()
    check('manifest parse', False, 'raised (see traceback above)')

print('SMOKE-ENV entries: %d' % len(entries), flush=True)

for entry in entries:
    label = str(entry.get('entry_id', '?'))
    try:
        # (01-04): every cmd.load call site routes through to_windows_path.
        winpath = to_windows_path(package_data_path('data', entry['file']))
        check(label + ' resolve', bool(winpath), winpath)

        # sha256 over the bytes read from the SAME Windows path PyMOL loads.
        with open(winpath, 'rb') as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        check(label + ' sha256', digest == entry['sha256'],
              digest[:12] + '...')

        # Fresh private object every time: re-loading into an existing
        # object APPENDS A STATE (research 1.1) -- never load into a
        # non-unique name.
        name = cmd.get_unused_name('_aam_tmp')
        try:
            cmd.load(winpath, name)

            n_at = cmd.count_atoms(name)
            check(label + ' atoms', n_at == entry['atom_count'],
                  'got %d want %d' % (n_at, entry['atom_count']))

            # get_bonds tuples are (atm1, atm2, order), atm indices 0-based
            # (only the orders matter here); compare sorted order multiset.
            bonds = cmd.get_bonds(name, 1)
            got_orders = sorted(int(b[2]) for b in bonds)
            want_orders = []
            for order_key in sorted(entry['bond_order_counts']):
                want_orders.extend(
                    [int(order_key)] * entry['bond_order_counts'][order_key])
            check(label + ' bonds',
                  len(got_orders) == entry['bond_count']
                  and got_orders == sorted(want_orders),
                  'got %s want %s (n=%d)'
                  % (got_orders, sorted(want_orders), len(got_orders)))

            # Explicit space dict, expression sandbox: no round(), no
            # Python-side names beyond `stored` (sum happens in Python).
            charges = []
            cmd.iterate(name, 'stored.append(formal_charge)',
                        space={'stored': charges})
            charge_sum = int(sum(charges))
            check(label + ' charge',
                  charge_sum == entry['formal_charge_sum'],
                  'got %d want %d'
                  % (charge_sum, entry['formal_charge_sum']))

            n_states = cmd.count_states(name)
            check(label + ' states', n_states == entry['states_expected'],
                  'got %d want %d' % (n_states, entry['states_expected']))

            # Element scan -> capability flags must match the manifest.
            elems = []
            cmd.iterate(name, 'stored.append(elem)',
                        space={'stored': elems})
            elem_set = set(e.strip().upper() for e in elems)
            metal_found = bool(elem_set & _MANUAL_METALS)
            halogen_found = bool(elem_set & _MANUAL_HALOGENS)
            check(label + ' metal flag',
                  metal_found == entry['metal_present'],
                  'scan=%s flag=%s' % (sorted(elem_set),
                                       entry['metal_present']))
            check(label + ' halogen flag',
                  halogen_found == entry['halogen_present'],
                  'scan=%s flag=%s' % (sorted(elem_set),
                                       entry['halogen_present']))
        finally:
            cmd.delete(name)      # even a failed check must not leak
    except Exception:
        traceback.print_exc()
        check(label + ' load', False, 'raised (see traceback above)')

leaks = [n for n in cmd.get_names('objects')
         if n.lower().startswith('_aam_tmp')]
check('no tmp leak', not leaks, ', '.join(leaks))

# --- Verdict marker (the SOLE verdict carrier) -------------------------------
print('=== SMOKE-02 %s ==='
      % ('FAIL: ' + ', '.join(failures) if failures else 'PASS'), flush=True)
