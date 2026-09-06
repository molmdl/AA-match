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

from aamatch.game_state import score, GameState
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


LIST_REQUIRED = {'mode': 'list',
                 'items': [{'type': 'h_bond', 'count': 1},
                           {'type': 'pi_stacking', 'count': 1}]}
ANY_REQUIRED = {'mode': 'any', 'items': []}


class TestGameStateContainer(unittest.TestCase):
    """GameState is PLAIN DATA ONLY: no PyMOL/Qt/file IO, just fields and
    the transitions the engine ops mutate (Task 2)."""

    def test_initial_state_fields(self):
        gs = GameState()
        self.assertEqual(gs.current_level_index, 0)
        self.assertEqual(gs.current_molecule_index, 0)
        self.assertEqual(gs.molecule_scores, [])
        self.assertEqual(gs.skip_count, 0)
        self.assertEqual(gs.giveup_count, 0)
        self.assertIsNone(gs.timer_anchor)
        self.assertEqual(gs.formed_types_per_molecule, {})

    def test_start_timer_stores_anchor(self):
        gs = GameState()
        gs.start_timer(123.5)
        self.assertEqual(gs.timer_anchor, 123.5)
        self.assertIsInstance(gs.timer_anchor, float)

    def test_total_score_sums_molecule_scores(self):
        gs = GameState()
        self.assertEqual(gs.total_score, 0.0)
        gs.molecule_scores = [0.5, 1.0]
        self.assertEqual(gs.total_score, 1.5)

    def test_skip_giveup_counters_are_plain_fields(self):
        gs = GameState()
        gs.skip_count += 1
        gs.giveup_count += 2
        self.assertEqual((gs.skip_count, gs.giveup_count), (1, 2))

    def test_advance_molecule_and_level(self):
        gs = GameState()
        gs.advance_molecule()
        gs.advance_molecule()
        self.assertEqual((gs.current_level_index,
                          gs.current_molecule_index), (0, 2))
        gs.advance_level()
        # A new level restarts the molecule index.
        self.assertEqual((gs.current_level_index,
                          gs.current_molecule_index), (1, 0))

    def test_molecule_key_format(self):
        self.assertEqual(GameState.molecule_key(0, 2), 'L0M2')
        self.assertEqual(GameState.molecule_key(1, 0), 'L1M0')

    def test_record_molecule_result_stores_score_and_formed_types(self):
        gs = GameState()
        s = gs.record_molecule_result(0, 0, LIST_REQUIRED,
                                      _recs('pi_stacking', 'h_bond',
                                            'h_bond'))
        self.assertEqual(s, 1.0)
        self.assertEqual(gs.molecule_scores, [1.0])
        # Formed types deduped and in canonical INTERACTION_TYPES order
        # (h_bond precedes pi_stacking) — record counts never inflate.
        self.assertEqual(gs.formed_types_per_molecule['L0M0'],
                         ['h_bond', 'pi_stacking'])

    def test_record_molecule_result_any_mode_formed_types(self):
        gs = GameState()
        # 'any' mode: formed types = the types the detector produced
        # (OQ-1 scoping lives in the detector's input).
        s = gs.record_molecule_result(1, 0, ANY_REQUIRED,
                                      _recs('salt_bridge', 'h_bond'))
        self.assertEqual(s, 1.0)
        self.assertEqual(gs.formed_types_per_molecule['L1M0'],
                         ['h_bond', 'salt_bridge'])

    def test_record_molecule_result_zero_score_still_recorded(self):
        gs = GameState()
        s = gs.record_molecule_result(0, 1, LIST_REQUIRED, [])
        self.assertEqual(s, 0.0)
        self.assertEqual(gs.molecule_scores, [0.0])
        self.assertEqual(gs.formed_types_per_molecule['L0M1'], [])


class TestGameStateRoundTrip(unittest.TestCase):
    """to_dict/from_dict must round-trip ALL fields losslessly (the dict
    is plain JSON-able; the formal sidecar container is Phase 7's, but
    this engine/debug surface must already lose nothing)."""

    def _loaded_state(self):
        gs = GameState()
        gs.current_level_index = 1
        gs.current_molecule_index = 2
        gs.record_molecule_result(0, 0, LIST_REQUIRED,
                                  _recs('h_bond', 'pi_stacking'))
        gs.record_molecule_result(1, 0, ANY_REQUIRED, _recs('h_bond'))
        gs.skip_count = 1
        gs.giveup_count = 2
        gs.start_timer(999.25)
        return gs

    def test_round_trip_lossless(self):
        d = self._loaded_state().to_dict()
        self.assertEqual(GameState.from_dict(d).to_dict(), d)

    def test_to_dict_is_json_able(self):
        import json
        d = self._loaded_state().to_dict()
        self.assertEqual(json.loads(json.dumps(d, sort_keys=True)), d)

    def test_from_dict_restores_fields_and_properties(self):
        gs = self._loaded_state()
        back = GameState.from_dict(gs.to_dict())
        self.assertEqual(back.current_level_index, 1)
        self.assertEqual(back.current_molecule_index, 2)
        self.assertEqual(back.molecule_scores, gs.molecule_scores)
        self.assertEqual(back.total_score, gs.total_score)
        self.assertEqual(back.skip_count, 1)
        self.assertEqual(back.giveup_count, 2)
        self.assertEqual(back.timer_anchor, 999.25)
        self.assertEqual(back.formed_types_per_molecule,
                         gs.formed_types_per_molecule)


if __name__ == '__main__':
    unittest.main()
