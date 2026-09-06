"""Tests for aamatch/game_state.py (plan 02-10, TDD).

SCORE-01 semantics over the CANONICAL detector record contract
(02-06/02-07): ``results`` is a list of dicts each carrying ``r['type']``
in ``setup_state.INTERACTION_TYPES``. ``required`` is the RESOLVED
level-spec shape (generator.py): ``{'mode': 'any'|'list', 'items':
[{'type': t, 'count': 1}, ...]}``.

Note on fixture records: score() is type-agnostic over records — it reads
only ``r['type']``, so the tests use minimal ``{'type': t}`` dicts rather
than the full 12-key / metrics-rich detector records. Any canonical record
satisfies the same contract.
"""

import unittest

from aamatch.game_state import score
from aamatch.setup_state import INTERACTION_TYPES


def _recs(*types):
    """Minimal canonical-record fixtures: one record per given type."""
    return [{'type': t} for t in types]


class TestScoreAnyMode(unittest.TestCase):
    """'any' mode is BINARY: >= 1 record of ANY type -> 1.0 (SCORE-01).

    Empty items is the exclusive-mode representation and is legal here;
    the formed-type check is scoped by the records the detector produced,
    which only enumerate allowed/cross-side interactions (OQ-1: scoping
    lives in the detector's input, never in score).
    """

    def test_zero_records_scores_zero(self):
        required = {'mode': 'any', 'items': []}
        self.assertEqual(score(required, []), 0.0)

    def test_one_record_scores_one(self):
        required = {'mode': 'any', 'items': []}
        self.assertEqual(score(required, _recs('h_bond')), 1.0)

    def test_duplicate_records_stay_binary_never_inflate(self):
        # Two h_bond records must still be exactly 1.0 — record COUNTS
        # never inflate the score (binary per interaction).
        required = {'mode': 'any', 'items': []}
        self.assertEqual(score(required, _recs('h_bond', 'h_bond')), 1.0)

    def test_any_type_counts(self):
        required = {'mode': 'any', 'items': []}
        for t in INTERACTION_TYPES:
            self.assertEqual(score(required, _recs(t)), 1.0)


class TestScoreListMode(unittest.TestCase):
    """'list' mode = len(formed items) / len(items), dedupe by type."""

    REQUIRED = {'mode': 'list',
                'items': [{'type': 'h_bond', 'count': 1},
                          {'type': 'pi_stacking', 'count': 1}]}

    def test_neither_formed_scores_zero(self):
        self.assertEqual(score(self.REQUIRED, []), 0.0)
        # A record of a type NOT in the required items forms nothing.
        self.assertEqual(score(self.REQUIRED, _recs('salt_bridge')), 0.0)

    def test_one_of_two_scores_half(self):
        self.assertEqual(score(self.REQUIRED, _recs('h_bond')), 0.5)

    def test_both_formed_scores_one(self):
        self.assertEqual(score(self.REQUIRED,
                               _recs('h_bond', 'pi_stacking')), 1.0)

    def test_duplicate_records_never_double_count(self):
        # Three h_bond records form ONE item exactly once: still 0.5.
        results = _recs('h_bond', 'h_bond', 'h_bond')
        self.assertEqual(score(self.REQUIRED, results), 0.5)

    def test_empty_items_list_raises(self):
        # A required set must be non-empty in list mode (empty items is
        # the exclusive 'any'-mode representation only).
        required = {'mode': 'list', 'items': []}
        with self.assertRaises(ValueError):
            score(required, [])


class TestScoreContractValidation(unittest.TestCase):
    """Defensive contract checks: malformed records and modes refuse."""

    def test_record_missing_type_raises(self):
        required = {'mode': 'any', 'items': []}
        with self.assertRaises(ValueError):
            score(required, [{'side': 'aa'}])

    def test_record_type_outside_enum_raises(self):
        required = {'mode': 'any', 'items': []}
        with self.assertRaises(ValueError):
            score(required, [{'type': 'anti_aromatic'}])

    def test_unknown_mode_raises(self):
        required = {'mode': 'sometimes', 'items': []}
        with self.assertRaises(ValueError):
            score(required, [])

    def test_record_not_dict_raises(self):
        required = {'mode': 'any', 'items': []}
        with self.assertRaises(ValueError):
            score(required, ['h_bond'])


if __name__ == '__main__':
    unittest.main()
