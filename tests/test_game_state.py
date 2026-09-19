"""Tests for aamatch/game_state.py (plan 02-10, TDD; 06-01 lifecycle battery).

SCORE-01 semantics over the CANONICAL detector record contract
(02-06/02-07): ``results`` is a list of dicts each carrying ``r['type']``
in ``setup_state.INTERACTION_TYPES``. ``required`` is the RESOLVED
level-spec shape (generator.py): ``{'mode': 'any'|'list', 'items':
[{'type': t, 'count': 1}, ...]}``.

Note on fixture records: score() is type-agnostic over records — it reads
only ``r['type']``, so the tests use minimal ``{'type': t}`` dicts rather
than the full 12-key / metrics-rich detector records. Any canonical record
satisfies the same contract.

06-01 additions (the SCORE-06/07 lifecycle data layer): end-state fields,
``stop_timer``, ``has_record``, the keyed ``score_per_molecule`` store,
and the fail-closed ``endgame_summary`` builder.
"""

import unittest

from aamatch.game_state import score, GameState, records_for_molecule
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
        gs.stop_timer(1064.25)              # 06-01: final_time 65.0 + over
        gs.end_state = 'completed'
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

    def test_to_dict_has_exact_11_keys(self):
        # 06-01: the additive growth is exactly these 4 keys on top of the
        # original 7 (SMOKE-14 pins the same 11-key set engine-side).
        d = self._loaded_state().to_dict()
        self.assertEqual(set(d), {
            'current_level_index', 'current_molecule_index',
            'molecule_scores', 'skip_count', 'giveup_count',
            'timer_anchor', 'formed_types_per_molecule',
            'game_over', 'end_state', 'final_time',
            'score_per_molecule'})

    def test_round_trip_carries_end_state_fields(self):
        d = self._loaded_state().to_dict()
        self.assertEqual(d['game_over'], True)
        self.assertEqual(d['end_state'], 'completed')
        self.assertEqual(d['final_time'], 65.0)
        self.assertEqual(d['score_per_molecule'],
                         {'L0M0': 1.0, 'L1M0': 1.0})
        back = GameState.from_dict(d)
        self.assertEqual(back.game_over, True)
        self.assertEqual(back.end_state, 'completed')
        self.assertEqual(back.final_time, 65.0)
        self.assertEqual(back.score_per_molecule, d['score_per_molecule'])

    def test_from_dict_accepts_older_7_key_dict(self):
        # Accept-older law (.get defaults): a pre-06-01 7-key dict loads
        # WITHOUT KeyError and yields the zero-init defaults for the 4
        # new fields (additive-only evolution).
        old = {'current_level_index': 0, 'current_molecule_index': 1,
               'molecule_scores': [0.5], 'skip_count': 0,
               'giveup_count': 0, 'timer_anchor': None,
               'formed_types_per_molecule': {'L0M0': ['h_bond']}}
        gs = GameState.from_dict(old)
        self.assertFalse(gs.game_over)
        self.assertIsNone(gs.end_state)
        self.assertIsNone(gs.final_time)
        self.assertEqual(gs.score_per_molecule, {})

    def test_to_dict_copies_score_per_molecule(self):
        gs = self._loaded_state()
        d = gs.to_dict()
        d['score_per_molecule']['L9M9'] = 9.9
        self.assertNotIn('L9M9', gs.score_per_molecule)
        self.assertEqual(gs.score_per_molecule['L0M0'], 1.0)


def _mol_rec(rtype, aa_object, lig_object):
    """A record-shaped-enough fixture for the molecule-scope filter:
    canonical records carry 'aa'/'lig' dicts with an 'object' name."""

    # NOTE: score() itself reads only 'type' -- this fixture serves the
    # records_for_molecule scoping layer (03-06 guard).
    return {'type': rtype,
            'aa': {'object': aa_object},
            'lig': {'object': lig_object}}


class TestRecordsForMolecule(unittest.TestCase):
    """The 03-06 cross-molecule scoring guard: a required-type record
    formed over the WRONG molecule's ligand or over another molecule's
    AA must never count for the scored molecule."""

    SLOTS0 = ['_aam_aa01', '_aam_aa02']
    SLOTS1 = ['_aam_aa10', '_aam_aa11']

    def _filter(self, records):
        return records_for_molecule(records, self.SLOTS0, '_aam_lig01')

    def test_keeps_records_over_the_molecule(self):
        recs = [_mol_rec('h_bond', '_aam_aa01', '_aam_lig01'),
                _mol_rec('pi_stacking', '_aam_aa02', '_aam_lig01')]
        self.assertEqual(self._filter(recs), recs)

    def test_drops_records_over_the_wrong_ligand(self):
        wrong = _mol_rec('h_bond', '_aam_aa01', '_aam_lig02')
        right = _mol_rec('h_bond', '_aam_aa02', '_aam_lig01')
        self.assertEqual(self._filter([wrong, right]), [right])

    def test_drops_records_over_the_wrong_aa(self):
        wrong = _mol_rec('h_bond', '_aam_aa10', '_aam_lig01')
        right = _mol_rec('h_bond', '_aam_aa01', '_aam_lig01')
        self.assertEqual(self._filter([wrong, right]), [right])

    def test_returns_new_list_preserving_order(self):
        recs = [_mol_rec('h_bond', '_aam_aa02', '_aam_lig01'),
                _mol_rec('salt_bridge', '_aam_aa10', '_aam_lig02'),
                _mol_rec('hydrophobic', '_aam_aa01', '_aam_lig01')]
        out = self._filter(recs)
        self.assertEqual(out, [recs[0], recs[2]])
        self.assertIsNot(out, recs)

    def test_scoping_flips_a_leaked_score(self):
        # THE GUARD'S TEETH at the pure level: unscoped, the wrong-ligand
        # h_bond record scores 1.00 against mol-0's required list;
        # scoped, the score is 0.00.
        required = {'mode': 'list',
                    'items': [{'type': 'h_bond', 'count': 1}]}
        leaked = [_mol_rec('h_bond', '_aam_aa01', '_aam_lig02')]
        self.assertEqual(score(required, leaked), 1.0)
        self.assertEqual(score(required, self._filter(leaked)), 0.0)

    def test_fail_closed_on_missing_partner_side(self):
        with self.assertRaises(ValueError):
            self._filter([{'type': 'h_bond',
                           'aa': {'object': '_aam_aa01'}}])
        with self.assertRaises(ValueError):
            self._filter([{'type': 'h_bond',
                           'lig': {'object': '_aam_lig01'}}])

    def test_fail_closed_on_object_less_side(self):
        with self.assertRaises(ValueError):
            self._filter([{'type': 'h_bond',
                           'aa': {'object': '_aam_aa01'},
                           'lig': {'role': 'donor'}}])

    def test_fail_closed_on_non_dict_record(self):
        with self.assertRaises(ValueError):
            self._filter(['not-a-record'])

    def test_empty_input_scores_nothing(self):
        self.assertEqual(self._filter([]), [])


class TestRebaseTimer(unittest.TestCase):
    """The pause-freeze op (plan 05-04): rebase_timer(now, elapsed) re-anchors
    the ONE timer so the shown elapsed FREEZES at `elapsed` — the 1 Hz tick's
    modal-open pause mechanism mutates the single anchor in place, never a
    GUI-side clock copy (P-4: two clocks drift, the v1 bug class).
    """

    def test_anchor_math_freezes_elapsed(self):
        gs = GameState()
        gs.start_timer(1000.0)
        gs.rebase_timer(1100.0, 42.0)
        # anchor = float(now) - float(elapsed)
        self.assertEqual(gs.timer_anchor, 1058.0)
        # the re-derived elapsed at the rebase instant is exactly 42.0
        self.assertEqual(1100.0 - gs.timer_anchor, 42.0)

    def test_float_coercion_on_both_args(self):
        gs = GameState()
        gs.start_timer(1000.0)
        # String/int inputs coerce, matching start_timer's float() contract;
        # the STORED anchor is a real float.
        gs.rebase_timer('1100', 42)
        self.assertIsInstance(gs.timer_anchor, float)
        self.assertEqual(gs.timer_anchor, 1058.0)

    def test_total_over_never_started_game(self):
        # The tick only calls it after GO, but the op itself is total over
        # valid inputs — no start_timer precondition.
        gs = GameState()
        gs.rebase_timer(500.0, 0.0)
        self.assertEqual(gs.timer_anchor, 500.0)
        self.assertIsInstance(gs.timer_anchor, float)

    def test_negative_elapsed_refuses(self):
        # A negative elapsed would push the anchor into the future and
        # REWIND the clock — fail-closed, never silent.
        gs = GameState()
        gs.start_timer(1000.0)
        try:
            gs.rebase_timer(1100.0, -5.0)
        except ValueError as e:
            self.assertIn('non-negative', str(e))
        else:
            self.fail('negative elapsed must raise ValueError')
        # The anchor is untouched by the refused call.
        self.assertEqual(gs.timer_anchor, 1000.0)

    def test_to_dict_carries_rebased_anchor(self):
        gs = GameState()
        gs.start_timer(1000.0)
        gs.rebase_timer(1100.0, 42.0)
        self.assertEqual(gs.to_dict()['timer_anchor'], 1058.0)
        self.assertEqual(GameState.from_dict(gs.to_dict()).timer_anchor,
                         1058.0)


class TestEndStateFields(unittest.TestCase):
    """06-01 SCORE-06/07 groundwork: a game that ends (give-up or natural
    completion) carries game_over=True, an end_state reason, a frozen
    final_time, and a keyed per-molecule score store — all zero-init on
    a fresh GameState."""

    def test_new_fields_zero_init(self):
        gs = GameState()
        self.assertFalse(gs.game_over)
        self.assertIsNone(gs.end_state)
        self.assertIsNone(gs.final_time)
        self.assertEqual(gs.score_per_molecule, {})

    def test_zero_init_survives_to_dict(self):
        d = GameState().to_dict()
        self.assertFalse(d['game_over'])
        self.assertIsNone(d['end_state'])
        self.assertIsNone(d['final_time'])
        self.assertEqual(d['score_per_molecule'], {})


class TestStopTimer(unittest.TestCase):
    """stop_timer(now) = capture the final elapsed ONCE + freeze (Q8).
    The timer anchor itself stays untouched — it is the pause mechanism's
    home. The caller (the lifecycle op) owns WHEN the game stops; the op
    only snapshots the clock and marks game_over."""

    def test_captures_elapsed_and_marks_game_over(self):
        gs = GameState()
        gs.start_timer(1000.0)
        gs.stop_timer(1065.0)
        self.assertEqual(gs.final_time, 65.0)
        self.assertIsInstance(gs.final_time, float)
        self.assertTrue(gs.game_over)

    def test_anchor_stays_untouched(self):
        # The anchor is the pause mechanism's home (rebase_timer's live
        # derivation); stop_timer must NEVER disturb it.
        gs = GameState()
        gs.start_timer(1000.0)
        gs.stop_timer(1065.0)
        self.assertEqual(gs.timer_anchor, 1000.0)

    def test_stop_does_not_own_the_reason(self):
        # end_state ('completed'|'gave_up') is set by the lifecycle op that
        # owns the end cause — stop_timer only freezes the clock.
        gs = GameState()
        gs.start_timer(1000.0)
        gs.stop_timer(1065.0)
        self.assertIsNone(gs.end_state)

    def test_now_default_reads_wall_clock(self):
        gs = GameState()
        gs.start_timer()
        gs.stop_timer()
        self.assertIsInstance(gs.final_time, float)
        self.assertGreaterEqual(gs.final_time, 0.0)
        self.assertTrue(gs.game_over)

    def test_never_started_game_is_zero_tolerant(self):
        # Total over valid inputs, matching rebase_timer's contract: a
        # never-started game stops at 0.0, never crashes.
        gs = GameState()
        gs.stop_timer(1065.0)
        self.assertEqual(gs.final_time, 0.0)
        self.assertIsInstance(gs.final_time, float)
        self.assertTrue(gs.game_over)

    def test_now_before_anchor_clamps_to_zero(self):
        gs = GameState()
        gs.start_timer(1000.0)
        gs.stop_timer(900.0)
        self.assertEqual(gs.final_time, 0.0)

    def test_float_coercion_like_start_timer(self):
        gs = GameState()
        gs.start_timer(1000.0)
        gs.stop_timer('1065')
        self.assertEqual(gs.final_time, 65.0)
        self.assertIsInstance(gs.final_time, float)

    def test_final_time_round_trips(self):
        gs = GameState()
        gs.start_timer(1000.0)
        gs.stop_timer(1065.0)
        back = GameState.from_dict(gs.to_dict())
        self.assertEqual(back.final_time, 65.0)
        self.assertTrue(back.game_over)


class TestHasRecord(unittest.TestCase):
    """The Q10 one-record guard, derivable from the keyed store:
    has_record(level, molecule) reports whether a molecule already
    produced a Confirm/Skip record (06-03's refusal primitive)."""

    def test_false_before_any_record(self):
        gs = GameState()
        self.assertFalse(gs.has_record(0, 0))
        self.assertFalse(gs.has_record(1, 2))

    def test_true_after_record(self):
        gs = GameState()
        gs.record_molecule_result(0, 2, LIST_REQUIRED,
                                  _recs('h_bond', 'pi_stacking'))
        self.assertTrue(gs.has_record(0, 2))
        # Other positions stay unrecorded.
        self.assertFalse(gs.has_record(0, 1))

    def test_true_after_zero_score_record(self):
        # The zero-score case writes the key too
        # (record_molecule_result stores unconditionally).
        gs = GameState()
        s = gs.record_molecule_result(0, 1, LIST_REQUIRED, [])
        self.assertEqual(s, 0.0)
        self.assertTrue(gs.has_record(0, 1))


class TestKeyedScoreStore(unittest.TestCase):
    """06-01 D11: score_per_molecule is written by record_molecule_result
    in the SAME call as the flat molecule_scores append — the two views
    can never drift; per-level aggregation no longer needs flat slicing
    under a one-record invariant."""

    def test_same_call_write_keeps_views_in_sync(self):
        gs = GameState()
        s = gs.record_molecule_result(0, 0, LIST_REQUIRED,
                                      _recs('h_bond'))
        self.assertEqual(s, 0.5)
        self.assertEqual(gs.molecule_scores, [0.5])
        self.assertEqual(gs.score_per_molecule, {'L0M0': 0.5})
        gs.record_molecule_result(1, 0, ANY_REQUIRED,
                                  _recs('salt_bridge'))
        self.assertEqual(gs.score_per_molecule,
                         {'L0M0': 0.5, 'L1M0': 1.0})
        self.assertEqual(gs.molecule_scores, [0.5, 1.0])

    def test_zero_score_record_still_writes_key(self):
        gs = GameState()
        gs.record_molecule_result(0, 1, LIST_REQUIRED, [])
        self.assertEqual(gs.score_per_molecule, {'L0M1': 0.0})

    def test_keyed_scores_sum_to_total_score(self):
        gs = GameState()
        gs.record_molecule_result(0, 0, LIST_REQUIRED, _recs('h_bond'))
        gs.record_molecule_result(0, 1, LIST_REQUIRED, _recs('h_bond',
                                                             'pi_stacking'))
        self.assertAlmostEqual(sum(gs.score_per_molecule.values()),
                               gs.total_score)


class TestEndgameSummary(unittest.TestCase):
    """06-01 SCORE-07 data payload (the plain dict 06-03's engine read op
    and 06-09's endgame screen consume): per-level scores, total, frozen
    time, sizes, counters, end position — fail-closed on any inconsistency
    between the end_state and the recorded results."""

    def _completed_game(self):
        # 2 levels x 2 molecules, scores 0.5/1.0/0.0/1.0 -> [1.5, 1.0].
        gs = GameState()
        gs.record_molecule_result(0, 0, LIST_REQUIRED, _recs('h_bond'))
        gs.record_molecule_result(0, 1, LIST_REQUIRED,
                                  _recs('h_bond', 'pi_stacking'))
        gs.advance_level()
        gs.record_molecule_result(1, 0, LIST_REQUIRED, [])
        gs.record_molecule_result(1, 1, LIST_REQUIRED,
                                  _recs('h_bond', 'pi_stacking'))
        gs.advance_molecule()   # position rests at the last molecule
        gs.start_timer(1000.0)
        gs.end_state = 'completed'
        gs.stop_timer(1065.0)
        return gs

    def test_payload_key_set_exact(self):
        summary = self._completed_game().endgame_summary([2, 2])
        self.assertEqual(set(summary), {
            'end_state', 'level_scores', 'total', 'final_time',
            'levels', 'molecules', 'molecules_completed',
            'skip_count', 'giveup_count',
            'ended_level', 'ended_molecule'})

    def test_happy_path_numeric(self):
        gs = self._completed_game()
        out = gs.endgame_summary([2, 2])
        self.assertEqual(out['end_state'], 'completed')
        self.assertEqual(out['level_scores'], [1.5, 1.0])
        self.assertEqual(out['total'], 2.5)
        self.assertEqual(out['total'], gs.total_score)
        self.assertEqual(out['final_time'], 65.0)
        self.assertIsInstance(out['final_time'], float)
        self.assertEqual(out['levels'], 2)
        self.assertEqual(out['molecules'], 4)
        self.assertEqual(out['molecules_completed'], 4)
        self.assertEqual(out['skip_count'], 0)
        self.assertEqual(out['giveup_count'], 0)
        self.assertEqual(out['ended_level'], 2)
        self.assertEqual(out['ended_molecule'], 2)

    def test_gave_up_current_molecule_intentionally_unrecorded(self):
        # Q5: the current molecule at give-up is NOT recorded — a complete
        # level 0, then give-up at L1M0 with 2 records.
        gs = GameState()
        gs.record_molecule_result(0, 0, LIST_REQUIRED, _recs('h_bond'))
        gs.record_molecule_result(0, 1, LIST_REQUIRED,
                                  _recs('h_bond', 'pi_stacking'))
        gs.advance_level()
        gs.skip_count = 1
        gs.giveup_count = 1
        gs.start_timer(1000.0)
        gs.end_state = 'gave_up'
        gs.stop_timer(1040.0)
        out = gs.endgame_summary([2, 2])
        self.assertEqual(out['end_state'], 'gave_up')
        self.assertEqual(out['level_scores'], [1.5, 0.0])
        self.assertEqual(out['total'], 1.5)
        self.assertEqual(out['final_time'], 40.0)
        self.assertEqual(out['molecules'], 4)
        self.assertEqual(out['molecules_completed'], 2)
        self.assertEqual(out['skip_count'], 1)
        self.assertEqual(out['giveup_count'], 1)
        self.assertEqual(out['ended_level'], 2)
        self.assertEqual(out['ended_molecule'], 1)

    def test_gave_up_mid_level_count_law(self):
        # 1 record (L0M0), gave up at L0M1: expected records = 0 full
        # levels + current_molecule_index.
        gs = GameState()
        gs.record_molecule_result(0, 0, LIST_REQUIRED, _recs('h_bond'))
        gs.advance_molecule()
        gs.end_state = 'gave_up'
        gs.stop_timer(10.0)
        out = gs.endgame_summary([2])
        self.assertEqual(out['molecules_completed'], 1)
        self.assertEqual(out['level_scores'], [0.5])
        self.assertEqual(out['ended_level'], 1)
        self.assertEqual(out['ended_molecule'], 2)

    def test_fail_closed_empty_molecule_counts(self):
        try:
            self._completed_game().endgame_summary([])
        except ValueError as e:
            self.assertIn('molecule_counts', str(e))
        else:
            self.fail('empty molecule_counts must raise ValueError')

    def test_fail_closed_non_int_entries(self):
        gs = self._completed_game()
        for bad in (['2', 2], [1.5, 2], [(2, 2)], [True, 2]):
            try:
                gs.endgame_summary(bad)
            except ValueError:
                pass
            else:
                self.fail('non-int molecule_counts entry %r must raise '
                          'ValueError' % (bad,))

    def test_fail_closed_end_state_none(self):
        gs = self._completed_game()
        gs.end_state = None
        try:
            gs.endgame_summary([2, 2])
        except ValueError as e:
            self.assertIn('end_state', str(e))
        else:
            self.fail('end_state None must raise ValueError')

    def test_fail_closed_unknown_end_state(self):
        gs = self._completed_game()
        gs.end_state = 'won'
        try:
            gs.endgame_summary([2, 2])
        except ValueError as e:
            self.assertIn('end_state', str(e))
        else:
            self.fail('unknown end_state must raise ValueError')

    def test_fail_closed_completed_requires_every_molecule_recorded(self):
        gs = self._completed_game()
        # A 'completed' game missing ANY molecule record is inconsistent —
        # refuse, never ship a partial summary as believable.
        del gs.score_per_molecule['L1M1']
        try:
            gs.endgame_summary([2, 2])
        except ValueError as e:
            self.assertIn('completed', str(e))
        else:
            self.fail('completed with a missing record must raise '
                      'ValueError')

    def test_fail_closed_gave_up_record_count_mismatch(self):
        # gave_up at L1M0 expects exactly 2 records; only 1 exists.
        gs = GameState()
        gs.record_molecule_result(0, 0, LIST_REQUIRED, _recs('h_bond'))
        gs.advance_level()
        gs.end_state = 'gave_up'
        gs.stop_timer(10.0)
        with self.assertRaises(ValueError):
            gs.endgame_summary([2, 2])

    def test_fail_closed_per_level_overflow(self):
        # counts [1, 3]: level 0 carries 2 records for a declared size of
        # 1 — more records than the level has molecules. (The completed
        # total-count law alone passes here: 4 records == 1 + 3.)
        try:
            self._completed_game().endgame_summary([1, 3])
        except ValueError as e:
            self.assertIn('level', str(e))
        else:
            self.fail('per-level record overflow must raise ValueError')

    def test_fail_closed_record_for_level_outside_counts(self):
        # totals [4] alone satisfy the completed law (4 records), but L1*
        # records name a level the payload never had.
        with self.assertRaises(ValueError):
            self._completed_game().endgame_summary([4])


if __name__ == '__main__':
    unittest.main()
