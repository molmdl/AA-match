"""Mechanical code audit for the detection pipeline (plan 02-15).

ROADMAP Phase-2 criterion 5's machine half: the pruning discipline is
enforced in the suite, not just re-read by reviewers. All checks run on
SOURCE TEXT via python3.6's stdlib ``ast`` -- the AST is immune to the
grep tripwire (Gate C / PITFALLS G3): a docstring that SAYS
``cmd.get_model`` is a string constant in the AST, never an Attribute or
Call node, so prose cannot blind-fail this gate. The prose-pin counts
(below) are asserted separately and exactly, so a NEW mention anywhere
(not just a call) is flagged for human review.

Four audits, all permanent suite members
(`python3.6 -m unittest discover -s tests -v`):

1. CANDIDATE ROUTING -- detector.py imports AND calls ``cross_pairs``
   (from spatial.py): candidate generation routes through the cell list.
2. ORACLE ISOLATION -- ``brute_force_pairs`` exists in spatial.py with a
   'test oracle' docstring, and NO file in aamatch/ or smoke/ imports or
   CALLS it (the O(N*M) oracle is tests-only; the detector must never
   fall back to it).
3. NO NAIVE PAIR LOOPS -- detector.py contains no nested for-loop pair
   in which BOTH loops iterate atom/record namespaces (the token-pair
   rule that matches the true per-atom-pair shape; the linear
   objects-x-one-object-atoms packing pass that FEEDS cross_pairs is
   documented and pinned as not-flagged); and
   spatial.cross_pairs itself contains no full O(N*M) double loop over
   points_a x points_b (the only nesting allowed is the 3x3x3 neighbour
   scan over the dx/dy/dz constants). Both finders carry NEGATIVE
   CONTROLS proving they can fire (test_purity.py's pattern).
4. BANNED CMD CALLS -- ``get_model`` (PITFALL 15 OOM trap),
   ``get_object_ttt`` (probe-proven SEGFAULT hazard) and
   ``matrix_reset`` (probe-proven coordinate reverter, placement.py) are
   called nowhere in aamatch/ or smoke/. Prose prohibition mentions are
   whitelisted by exact count per (file, token) -- inspect, never
   blind-fail; a count drift means a human re-reviews that file.

Run from repo root:
    python3.6 -m unittest tests.test_code_audit -v
"""

import ast
import os
import sys
import unittest

# Bootstrap so this suite works both via `unittest discover -s tests` and
# as a directly-executed module (test_purity.py pattern).
_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(_HERE, '..'))
PKG_DIR = os.path.join(REPO_ROOT, 'aamatch')
SMOKE_DIR = os.path.join(REPO_ROOT, 'smoke')
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Banned cmd APIs with their prohibition reason (PITFALLS + probes).
BANNED_CALLS = ('get_model', 'matrix_reset', 'get_object_ttt')

# Whitelisted PROSE mentions of the banned tokens: (relative file, token)
# -> exact occurrence count. These are docstring prohibition prose (the
# placement.py banned-call list + engine.py's two '(never matrix_reset)'
# mentions + geometry.py's PITFALL-15 note) -- Gate C: inspect, never
# blind-fail. Any count drift (a new mention, a removed one, a real call
# sneaked in) fails this audit and demands human re-review.
PROSE_PIN = {
    ('placement.py', 'matrix_reset'): 3,     # banned list (x2) + reset fn
    ('engine.py', 'matrix_reset'): 2,        # '(never matrix_reset)' x2
    ('placement.py', 'get_object_ttt'): 1,   # banned list
    ('geometry.py', 'get_model'): 1,         # PITFALL-15 extraction note
}


def _read_source(path):
    """Read a .py file as text, encoding-independent of the locale."""
    with open(path, 'rb') as f:
        return f.read().decode('utf-8')


def _py_files(root):
    return sorted(name for name in os.listdir(root)
                  if name.endswith('.py'))


def _iter_names(expr):
    """Every name mentioned in an AST expression (Name ids + Attribute
    attrs), e.g. ``range(len(points_a))`` -> {'range', 'len', 'points_a'}.
    """
    names = set()
    for node in ast.walk(expr):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def _called_names(tree):
    """Every function name CALLED in an AST (Name ids + Attribute attrs).
    ``cmd.get_model(...)`` reports 'get_model'; ``cross_pairs(...)``
    reports 'cross_pairs'. Docstring prose cannot appear here."""
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.append(func.id)
            elif isinstance(func, ast.Attribute):
                names.append(func.attr)
    return names


def _imported_names(tree):
    """Names bound by 'from <mod> import <name>' statements."""
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names.extend(alias.name for alias in node.names)
    return names


def _function_defs(tree):
    """{(name): FunctionDef node} for every def, any scope."""
    return dict((node.name, node)
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef))


def _record_token_mentions(expr):
    """Identifiers in the iter expression carrying an atom/record TOKEN
    (`'_'.join` split): 'atoms', 'aa_recs', 'lig_records_live', ...
    'near_objs'/'pairs'/'b_entries' do NOT qualify -- the naive pair-loop
    ban is about both FULL sets, not any identifier substring."""
    names = set()
    tokens = set(('atom', 'atoms', 'rec', 'recs', 'record', 'records'))
    for node in ast.walk(expr):
        text = None
        if isinstance(node, ast.Name):
            text = node.id
        elif isinstance(node, ast.Attribute):
            text = node.attr
        if text and set(text.lower().split('_')) & tokens:
            names.add(text)
    return names


def find_nested_record_loops(src):
    """Flag the naive per-atom-pair double-loop shape DETECT-05 bans
    from detector.py: an ast.For whose iter iterates a record NAMESPACE
    (token rule above) whose body contains ANOTHER ast.For whose iter
    iterates a record namespace too -- two loops, both over atom/record
    sets, means one full set is being walked per element of the other.

    Not flagged (by design): a packing pass like
    ``for obj in near_objs: for rec in _pair_atoms(features, obj)`` --
    the outer loop is over OBJECTS, the inner over one object's atoms,
    which is the O(near atoms) input assembly that FEEDS
    spatial.cross_pairs, never a pairwise walk (02-15: the plan's
    substring-shaped rule would flag this legitimate pattern; the
    token-pair rule keeps the gate strict where it matters). Returns one
    problem string per offender."""
    problems = []
    for fname, fnode in _function_defs(ast.parse(src)).items():
        for outer in ast.walk(fnode):
            if not isinstance(outer, ast.For):
                continue
            outer_hits = _record_token_mentions(outer.iter)
            if not outer_hits:
                continue
            for sub in ast.walk(outer):
                if sub is outer:
                    continue
                if not isinstance(sub, ast.For):
                    continue
                inner_hits = _record_token_mentions(sub.iter)
                if inner_hits:
                    problems.append(
                        '%s (line %d): %s walked inside %s'
                        % (fname, sub.lineno,
                           '/'.join(sorted(inner_hits)),
                           '/'.join(sorted(outer_hits))))
    return problems


def find_full_pair_loops(src, funcname):
    """Flag nesting of the O(N*M) shape inside ONE named function: an
    ast.For whose iter mentions 'points_a'/'points_b' sitting inside
    another ast.For whose iter mentions 'points_a'/'points_b'. The 3x3x3
    neighbour scan nests loops over the dx/dy/dz CONSTANTS and a cell
    'bucket' -- never over the point lists -- so it cannot trip this."""
    problems = []
    target = _function_defs(ast.parse(src)).get(funcname)
    if target is None:
        return ['%s: function not found' % funcname]
    for outer in ast.walk(target):
        if not isinstance(outer, ast.For):
            continue
        if not _iter_names(outer.iter) & set(('points_a', 'points_b')):
            continue
        for sub in ast.walk(outer):
            if sub is outer:
                continue
            if isinstance(sub, ast.For) and \
                    _iter_names(sub.iter) & set(('points_a', 'points_b')):
                problems.append(
                    '%s (line %d): full double loop over %s'
                    % (funcname, sub.lineno,
                       '/'.join(sorted(
                           _iter_names(sub.iter)
                           & set(('points_a', 'points_b'))))))
    return problems


# Negative-control sources: prove audit 3's finders can FIRE (a gate that
# cannot fail proves nothing -- test_purity.py's negative-control rule).
NESTED_LOOP_TRAP = '''def look(atoms, records):
    for a in atoms:
        for b in records:
            hold(a, b)
'''

# The legal packing shape: outer over OBJECTS, inner over one object's
# atoms (02-15 token-pair rule) -- must NOT trip the finder.
PACKING_SHAPE_OK = '''def pack(features, near_objs):
    for obj in near_objs:
        for rec in _pair_atoms(features, obj):
            a_pts.append(rec)
'''

FULL_PAIR_TRAP = '''def pairs(points_a, points_b, cutoff):
    for i in range(len(points_a)):
        for j in range(len(points_b)):
            near(i, j)
'''


class TestCrossPairsRouting(unittest.TestCase):
    """Audit 1: detector candidate generation routes through the cell
    list -- detector.py imports AND calls cross_pairs."""

    def test_detector_imports_and_calls_cross_pairs(self):
        tree = ast.parse(
            _read_source(os.path.join(PKG_DIR, 'detector.py')))
        self.assertIn(
            'cross_pairs', _imported_names(tree),
            'detector.py must import cross_pairs from spatial '
            '(candidate generation routes through the cell list)')
        self.assertIn(
            'cross_pairs', _called_names(tree),
            'detector.py must CALL cross_pairs -- import alone proves '
            'nothing (candidates come from the cell list, not loops)')


class TestBruteForceOracle(unittest.TestCase):
    """Audit 2: the O(N*M) oracle exists for tests and ONLY tests."""

    def test_oracle_exists_with_test_oracle_docstring(self):
        defs = _function_defs(ast.parse(
            _read_source(os.path.join(PKG_DIR, 'spatial.py'))))
        oracle = defs.get('brute_force_pairs')
        self.assertIsNotNone(
            oracle,
            'spatial.py must define brute_force_pairs (test_spatial.py '
            'proves cross_pairs equivalence against it)')
        docstring = ast.get_docstring(oracle) or ''
        self.assertIn(
            'test oracle', docstring.lower(),
            'brute_force_pairs must carry the test-oracle docstring '
            '(02-02 pinned the audit-grep phrase)')

    def test_no_non_test_call_or_import_sites(self):
        offenders = []
        for root, tag in ((PKG_DIR, 'aamatch'), (SMOKE_DIR, 'smoke')):
            for name in _py_files(root):
                if tag == 'aamatch' and name == 'spatial.py':
                    continue                  # the definition home
                tree = ast.parse(_read_source(os.path.join(root, name)))
                if 'brute_force_pairs' in _called_names(tree):
                    offenders.append('%s/%s: CALLS brute_force_pairs'
                                     % (tag, name))
                if 'brute_force_pairs' in _imported_names(tree):
                    offenders.append('%s/%s: IMPORTS brute_force_pairs'
                                     % (tag, name))
        self.assertEqual(
            offenders, [],
            'brute_force_pairs is tests-only (02-02/02-15): found '
            'non-test use:\n  ' + '\n  '.join(offenders))


class TestNoNaivePairLoops(unittest.TestCase):
    """Audit 3: no per-atom-pair double loops in the detector; the cell
    list itself prunes instead of looping both full sets."""

    def test_detector_has_no_nested_record_loops(self):
        problems = find_nested_record_loops(
            _read_source(os.path.join(PKG_DIR, 'detector.py')))
        self.assertEqual(
            problems, [],
            'detector.py contains a nested loop iterating atom/record '
            'names -- the naive per-atom-pair shape DETECT-05 bans; '
            'route candidates through spatial.cross_pairs:\n  '
            + '\n  '.join(problems))

    def test_cross_pairs_has_no_full_double_loop(self):
        problems = find_full_pair_loops(
            _read_source(os.path.join(PKG_DIR, 'spatial.py')),
            'cross_pairs')
        self.assertEqual(problems, [],
                         'cross_pairs must prune via the cell list (only '
                         'the 3x3x3 dx/dy/dz scan may nest), found:\n  '
                         + '\n  '.join(problems))

    def test_negative_control_nested_loop_finder_fires(self):
        problems = find_nested_record_loops(NESTED_LOOP_TRAP)
        self.assertEqual(len(problems), 1,
                         'nested-loop finder must flag the synthetic '
                         'per-atom-pair trap, got %r' % (problems,))

    def test_negative_control_packing_shape_not_flagged(self):
        problems = find_nested_record_loops(PACKING_SHAPE_OK)
        self.assertEqual(problems, [],
                         'the linear packing pass (objects x one-'
                         'object-atoms) must NOT trip the pair-loop gate'
                         ' -- got %r' % (problems,))

    def test_negative_control_full_pair_finder_fires(self):
        problems = find_full_pair_loops(FULL_PAIR_TRAP, 'pairs')
        self.assertEqual(len(problems), 1,
                         'full-pair finder must flag the synthetic '
                         'points_a x points_b trap, got %r' % (problems,))


class TestBannedCmdCalls(unittest.TestCase):
    """Audit 4: get_model / matrix_reset / get_object_ttt are called
    nowhere; prose mentions are whitelisted by exact count."""

    def test_no_banned_call_sites(self):
        offenders = []
        for root, tag in ((PKG_DIR, 'aamatch'), (SMOKE_DIR, 'smoke')):
            for name in _py_files(root):
                tree = ast.parse(_read_source(os.path.join(root, name)))
                called = set(_called_names(tree))
                for token in BANNED_CALLS:
                    if token in called:
                        offenders.append('%s/%s: CALLS %s'
                                         % (tag, name, token))
        self.assertEqual(
            offenders, [],
            'banned cmd APIs (PITFALL 15 OOM / TTT SEGFAULT / baked-'
            'coordinate reverter) must have ZERO call sites:\n  '
            + '\n  '.join(offenders))

    def test_prose_mentions_pinned_exactly(self):
        problems = []
        for (fname, token), want in sorted(PROSE_PIN.items()):
            src = _read_source(os.path.join(PKG_DIR, fname))
            got = src.count(token)
            if got != want:
                problems.append(
                    '%s: %r appears %d time(s), pin says %d -- a NEW '
                    'mention (or a removed prohibition line) demands '
                    'human re-review (Gate C: inspect, never blind-fail)'
                    % (fname, token, got, want))
        # And the tokens appear in NO other aamatch module at all.
        for name in _py_files(PKG_DIR):
            for token in BANNED_CALLS:
                if (name, token) in PROSE_PIN:
                    continue
                if token in _read_source(os.path.join(PKG_DIR, name)):
                    problems.append(
                        '%s: unwhitelisted %r mention -- only %s may '
                        'carry it (docstring prohibition prose)'
                        % (name, token, sorted(PROSE_PIN)))
        self.assertEqual(problems, [],
                         'prose-pin drift:\n  ' + '\n  '.join(problems))


if __name__ == '__main__':
    unittest.main()
