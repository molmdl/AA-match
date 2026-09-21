"""TDD RED battery for aamatch/status_text.py (plan 05-01).

Phase 5's Game status tab is a DUMB RENDERER (05-RESEARCH-status-surface.md
dont_hand_roll): every string it can show is built by the PURE status_text
builders pinned here, BEFORE any Qt wiring exists (game_window.py lands in a
sibling plan and consumes exactly these functions). Written FIRST (RED):
``aamatch.status_text`` does not exist yet, so collecting this module raises
ImportError -- that failure IS the RED proof. Task-2 GREEN then implements
the builders; Task 3 registers the module: status_text registered in
tests/test_purity.py PURE_MODULES in this phase.

Mechanical properties pinned here (05-RESEARCH-status-surface.md Q4, the
event inventory, pitfalls 3/4/5/7):

- required_display: the required-interactions LABEL text. mode 'any' ->
  'Required: any 1 interaction'; mode 'list' -> 'Required: %d
  interaction(s): <wizard_text.required_summary output>' where the count
  is len(required['items']) -- difficulty.n_required_types is NOT the
  display source (generator.py cap, pitfall 5). Fail-closed identically
  to required_summary (delegated): list mode with empty items and unknown
  modes raise ValueError naming the cause.
- level_molecule_line / selected_line / error_line: one-line builders.
  selected_line(None) is None (a deselect logs nothing).
- status_events(prev, curr): the poll-diff over two get_status() plain-data
  dicts. prev None -> [] (first observation SILENT -- pitfall 4): the start
  sequence owns the first level line. Emits, IN ORDER: level/molecule line,
  selection line, error line. Fingerprint keys: molecule_id, molecule_pos,
  molecule_total, level_pos, selected['slot_id'], error. Sticky dedupe:
  an unchanged error string is never re-logged (pitfall 3); same-slot
  re-click and cleared error and deselect are silent. 'result' is NOT
  fingerprinted in Phase 5 (score lines reserved for Phase 6, pitfall 7).
  Unknown/extra keys are tolerated (.get -- the wizard_text consumer
  precedent).
- EVENT_KINDS: the documented event vocabulary, exactly 15 keys: the 7
  Phase-5 emitted kinds (game_start, countdown, level_molecule,
  required_display, selection, error, hint) + 6 reserved for Phase 6
  (molecule_scored, molecule_skipped, gave_up, level_advanced, game_reset,
  game_restarted) + 2 reserved for Phase 7 (game_saved, game_imported).

State dicts are PLAIN DATA shaped exactly like what GameWizard.get_status()
(plan 05-07) returns:
    {'molecule_id': 'mol-001', 'molecule_pos': 1, 'molecule_total': 2,
     'level_pos': 1, 'level_total': 2,
     'required': {'mode': ..., 'items': [...]},
     'selected': {'slot_id': 'r0c0', 'object': '_aam_aa01'} | None,
     'result': {...} | None,
     'error': None | str}
"""

import inspect
import unittest

from aamatch import status_text


def _state(**overrides):
    """A minimal get_status()-shaped dict; keyword overrides applied."""
    state = {
        'molecule_id': 'mol-001',
        'molecule_pos': 1,
        'molecule_total': 2,
        'level_pos': 1,
        'level_total': 2,
        'required': {'mode': 'any', 'items': []},
        'selected': None,
        'result': None,
        'error': None,
    }
    state.update(overrides)
    return state


class TestRequiredDisplay(unittest.TestCase):
    """The required-interactions label text (Q4 pinned strings)."""

    def test_any_mode(self):
        self.assertEqual(
            status_text.required_display({'mode': 'any', 'items': []}),
            'Required: any 1 interaction')

    def test_list_mode_singular(self):
        self.assertEqual(
            status_text.required_display(
                {'mode': 'list',
                 'items': [{'type': 'h_bond', 'count': 1}]}),
            'Required: 1 interaction: h_bond x1')

    def test_list_mode_plural(self):
        self.assertEqual(
            status_text.required_display(
                {'mode': 'list',
                 'items': [{'type': 'h_bond', 'count': 1},
                           {'type': 'pi_stacking', 'count': 2}]}),
            'Required: 2 interactions: h_bond x1, pi_stacking x2')

    def test_list_mode_count_is_len_items(self):
        # The count is len(items) -- NEVER difficulty.n_required_types
        # (pitfall 5). Three items renders '3 interactions' regardless
        # of any generation cap.
        state = {'mode': 'list',
                 'items': [{'type': 'h_bond', 'count': 1},
                           {'type': 'h_bond', 'count': 1},
                           {'type': 'pi_stacking', 'count': 2}]}
        self.assertEqual(status_text.required_display(state),
                         'Required: 3 interactions: '
                         'h_bond x1, h_bond x1, pi_stacking x2')

    def test_list_mode_empty_items_refused(self):
        # Empty items is the 'any'-mode representation only; the refusal
        # wording is delegated to required_summary (single-home law).
        with self.assertRaises(ValueError) as cm:
            status_text.required_display({'mode': 'list', 'items': []})
        self.assertIn('list', str(cm.exception))
        self.assertIn('empty', str(cm.exception))

    def test_unknown_mode_refused(self):
        with self.assertRaises(ValueError) as cm:
            status_text.required_display({'mode': 'bogus', 'items': []})
        self.assertIn('bogus', str(cm.exception))

    def test_non_dict_refused(self):
        with self.assertRaises(ValueError):
            status_text.required_display('any')


class TestLevelMoleculeLine(unittest.TestCase):
    """The level/molecule status line."""

    def test_basic(self):
        self.assertEqual(
            status_text.level_molecule_line(
                {'level_pos': 1, 'molecule_pos': 1, 'molecule_total': 2}),
            'Level 1, molecule 1 of 2.')

    def test_missing_level_pos_refused(self):
        with self.assertRaises(ValueError) as cm:
            status_text.level_molecule_line(
                {'molecule_pos': 1, 'molecule_total': 2})
        self.assertIn('level_pos', str(cm.exception))

    def test_missing_molecule_pos_refused(self):
        with self.assertRaises(ValueError) as cm:
            status_text.level_molecule_line(
                {'level_pos': 1, 'molecule_total': 2})
        self.assertIn('molecule_pos', str(cm.exception))

    def test_missing_molecule_total_refused(self):
        with self.assertRaises(ValueError) as cm:
            status_text.level_molecule_line(
                {'level_pos': 1, 'molecule_pos': 1})
        self.assertIn('molecule_total', str(cm.exception))


class TestSelectedLine(unittest.TestCase):
    """The selection event line (panel's first prompt line minus its
    imperative tail -- wizard_text.py:271)."""

    def test_basic(self):
        self.assertEqual(
            status_text.selected_line(
                {'slot_id': 'r0c0', 'object': '_aam_aa01'}),
            'Selected: slot r0c0 (_aam_aa01).')

    def test_none_returns_none(self):
        # A deselect logs nothing -- only the slot-selection string exists;
        # the panel reflects deselects (planner decision from the research).
        self.assertIsNone(status_text.selected_line(None))


class TestErrorLine(unittest.TestCase):
    """The error event line (same 'ERROR: ' prefix as panel/prompt)."""

    def test_basic(self):
        self.assertEqual(status_text.error_line('Select an amino acid first.'),
                         'ERROR: Select an amino acid first.')


class TestStatusEvents(unittest.TestCase):
    """The poll-diff (Pattern 2): prev/curr get_status() dicts -> the log
    lines to append, IN ORDER level/molecule, then selection, then error."""

    def test_first_observation_silent(self):
        # prev=None -> [] (pitfall 4): the start sequence already logged
        # the level line; the poll only reports CHANGES.
        self.assertEqual(status_text.status_events(None, _state()), [])

    def test_identical_states_silent(self):
        state = _state()
        self.assertEqual(status_text.status_events(state, dict(state)), [])

    def test_molecule_id_change_logs_level_line(self):
        prev = _state()
        curr = _state(molecule_id='mol-002', molecule_pos=2)
        self.assertEqual(status_text.status_events(prev, curr),
                         ['Level 1, molecule 2 of 2.'])

    def test_level_change_logs_level_line(self):
        prev = _state()
        curr = _state(level_pos=2, molecule_id='mol-001',
                      molecule_pos=1, molecule_total=3)
        self.assertEqual(status_text.status_events(prev, curr),
                         ['Level 2, molecule 1 of 3.'])

    def test_molecule_total_change_logs_level_line(self):
        prev = _state()
        curr = _state(molecule_total=3)
        self.assertEqual(status_text.status_events(prev, curr),
                         ['Level 1, molecule 1 of 3.'])

    def test_several_fingerprint_keys_moved_emit_one_level_line(self):
        # Exactly ONE line per change tick even if several fingerprint
        # keys moved.
        prev = _state()
        curr = _state(molecule_id='mol-002', molecule_pos=2,
                      molecule_total=3, level_pos=2)
        self.assertEqual(status_text.status_events(prev, curr),
                         ['Level 2, molecule 2 of 3.'])

    def test_selection_change_logs_selected_line(self):
        prev = _state()
        curr = _state(selected={'slot_id': 'r0c0', 'object': '_aam_aa01'})
        self.assertEqual(status_text.status_events(prev, curr),
                         ['Selected: slot r0c0 (_aam_aa01).'])

    def test_selection_slot_change_logs_selected_line(self):
        prev = _state(selected={'slot_id': 'r0c0', 'object': '_aam_aa01'})
        curr = _state(selected={'slot_id': 'r0c1', 'object': '_aam_aa02'})
        self.assertEqual(status_text.status_events(prev, curr),
                         ['Selected: slot r0c1 (_aam_aa02).'])

    def test_same_slot_reclick_silent(self):
        prev = _state(selected={'slot_id': 'r0c0', 'object': '_aam_aa01'})
        curr = _state(selected={'slot_id': 'r0c0', 'object': '_aam_aa01'})
        self.assertEqual(status_text.status_events(prev, curr), [])

    def test_deselect_silent(self):
        # Change TO None: selected_line(None) is None -- skipped.
        prev = _state(selected={'slot_id': 'r0c0', 'object': '_aam_aa01'})
        curr = _state(selected=None)
        self.assertEqual(status_text.status_events(prev, curr), [])

    def test_new_error_logged(self):
        prev = _state()
        curr = _state(error='Select an amino acid first.')
        self.assertEqual(status_text.status_events(prev, curr),
                         ['ERROR: Select an amino acid first.'])

    def test_sticky_error_not_relogged(self):
        # pitfall 3: wizard._error persists; an UNCHANGED error string is
        # never re-logged.
        prev = _state(error='Select an amino acid first.')
        curr = _state(error='Select an amino acid first.')
        self.assertEqual(status_text.status_events(prev, curr), [])

    def test_different_error_logged(self):
        prev = _state(error='Select an amino acid first.')
        curr = _state(error='Nothing detected for this molecule.')
        self.assertEqual(status_text.status_events(prev, curr),
                         ['ERROR: Nothing detected for this molecule.'])

    def test_cleared_error_silent(self):
        prev = _state(error='Select an amino acid first.')
        curr = _state()
        self.assertEqual(status_text.status_events(prev, curr), [])

    def test_result_never_fingerprinted(self):
        # pitfall 7: score lines are a Phase-6 reserve; a result change
        # alone logs NOTHING in Phase 5.
        prev = _state()
        curr = _state(result={'score': 1.0,
                              'formed': ['h_bond'],
                              'required': {'mode': 'any', 'items': []}})
        self.assertEqual(status_text.status_events(prev, curr), [])

    def test_order_level_then_selection_then_error(self):
        prev = _state()
        curr = _state(molecule_id='mol-002', molecule_pos=2,
                      selected={'slot_id': 'r2c1', 'object': '_aam_aa05'},
                      error='Select an amino acid first.')
        self.assertEqual(status_text.status_events(prev, curr),
                         ['Level 1, molecule 2 of 2.',
                          'Selected: slot r2c1 (_aam_aa05).',
                          'ERROR: Select an amino acid first.'])

    def test_extra_keys_tolerated(self):
        # .get-based: unknown/extra keys are ignored (the wizard_text
        # consumer precedent) -- a future additive key must not break the
        # diff.
        prev = _state()
        curr = _state(result=None, some_future_key=42,
                      another_future={'nested': True})
        self.assertEqual(status_text.status_events(prev, curr), [])

    def test_selected_present_but_identical_silent(self):
        # selected dict equal in both; combined with a molecule change the
        # selection half contributes nothing.
        prev = _state(selected={'slot_id': 'r0c0', 'object': '_aam_aa01'})
        curr = _state(molecule_id='mol-002', molecule_pos=2,
                      selected={'slot_id': 'r0c0', 'object': '_aam_aa01'})
        self.assertEqual(status_text.status_events(prev, curr),
                         ['Level 1, molecule 2 of 2.'])


class TestEventKinds(unittest.TestCase):
    """EVENT_KINDS -- the documented event vocabulary constant. The KEY
    SET is what is pinned; reserved-kind notes only carry phase markers
    (final wording is Phase 6/7 research's job)."""

    def test_exact_15_keys(self):
        self.assertEqual(
            sorted(status_text.EVENT_KINDS),
            sorted(['game_start', 'countdown', 'level_molecule',
                    'required_display', 'selection', 'error', 'hint',
                    'molecule_scored', 'molecule_skipped', 'gave_up',
                    'level_advanced', 'game_reset', 'game_restarted',
                    'game_saved', 'game_imported']))

    def test_values_are_notes(self):
        for kind, note in status_text.EVENT_KINDS.items():
            self.assertIsInstance(note, str)
            self.assertTrue(note, 'empty note for %r' % kind)

    def test_phase6_reserved_kinds_marked(self):
        for kind in ('molecule_scored', 'molecule_skipped', 'gave_up',
                     'level_advanced', 'game_reset', 'game_restarted'):
            self.assertIn('reserved for Phase 6',
                          status_text.EVENT_KINDS[kind])

    def test_phase7_reserved_kinds_marked(self):
        for kind in ('game_saved', 'game_imported'):
            self.assertIn('reserved for Phase 7',
                          status_text.EVENT_KINDS[kind])

    def test_emitted_kinds_not_marked_reserved(self):
        for kind in ('game_start', 'countdown', 'level_molecule',
                     'required_display', 'selection', 'error', 'hint'):
            self.assertNotIn('reserved for Phase',
                             status_text.EVENT_KINDS[kind])


# ---------------------------------------------------------------------------
# Phase 6 (plan 06-02) -- additive battery. RED first: the Phase-6 builders
# (format_mss, warning constants, the six reserved-kind event builders, the
# last_event poll-diff extension, endgame_lines) do not exist yet, so these
# tests fail on AttributeError; the GREEN commit implements them. The Phase-5
# pins above stay BYTE-UNCHANGED: EVENT_KINDS keeps its 15-key set and its
# 'reserved for Phase 6' note text (the builders, not the dict, carry the
# final wording), and 'result' is STILL never fingerprinted (pitfall 7).
# ---------------------------------------------------------------------------


def _event(kind, **payload):
    """A last_event marker as the wizard will surface it: kind + seq +
    payload (pure data, the contract-2 picklable shape)."""
    marker = {'kind': kind, 'seq': 1}
    marker.update(payload)
    return marker


class TestFormatMss(unittest.TestCase):
    """The pure M:SS time formatter (score/timer display, SCORE-07)."""

    def test_basic(self):
        self.assertEqual(status_text.format_mss(75), '1:15')

    def test_over_an_hour(self):
        self.assertEqual(status_text.format_mss(3661), '61:01')

    def test_zero(self):
        self.assertEqual(status_text.format_mss(0), '0:00')

    def test_int_coercion(self):
        # int() coercion of the input: a float truncates.
        self.assertEqual(status_text.format_mss(75.9), '1:15')

    def test_negative_refused(self):
        # Negative seconds refuse naming the cause -- the tick's
        # max(0.0, ...) upstream keeps the live path safe.
        with self.assertRaises(ValueError) as cm:
            status_text.format_mss(-0.5)
        self.assertIn('negative', str(cm.exception))


class TestWarningConstants(unittest.TestCase):
    """The confirmation-warning text constants (endgame-ui section 3.3,
    NO-number variant). Byte-for-byte pins: the Qt wrappers can show ONLY
    these strings."""

    def test_skip_warning_title(self):
        self.assertEqual(status_text.SKIP_WARNING_TITLE,
                         'Skip this molecule?')

    def test_skip_warning_text(self):
        self.assertEqual(
            status_text.SKIP_WARNING_TEXT,
            'Skip this molecule and move to the next one? The score '
            'formed so far is kept.')

    def test_giveup_warning_title(self):
        self.assertEqual(status_text.GIVEUP_WARNING_TITLE, 'Give up?')

    def test_giveup_warning_text(self):
        self.assertEqual(
            status_text.GIVEUP_WARNING_TEXT,
            'Give up and end the game now? The game ends at this stage '
            'and the endgame summary is shown.')


class TestMoleculeScoredLines(unittest.TestCase):
    """The scored event (SCORE-02): header line + the wizard_text
    result_lines debrief appended VERBATIM (single-home law -- imported,
    never copied)."""

    def test_list_mode_full_block(self):
        event = _event('molecule_scored', score=1.0, total=2.5,
                       molecule_pos=1, molecule_total=2,
                       formed=['h_bond'],
                       required={'mode': 'list',
                                 'items': [{'type': 'h_bond', 'count': 1}]},
                       extras=[('pi_stacking', 1)])
        self.assertEqual(
            status_text.molecule_scored_lines(event),
            ['Molecule 1 of 2 scored 1.00 (total 2.50).',
             '1/1 required interactions formed (score 1.00)',
             'Formed: h_bond',
             'Formed (not required): pi_stacking x1'])

    def test_any_mode_nothing_formed(self):
        event = _event('molecule_scored', score=0.0, total=0.5,
                       molecule_pos=2, molecule_total=3,
                       formed=[],
                       required={'mode': 'any', 'items': []},
                       extras=[])
        self.assertEqual(
            status_text.molecule_scored_lines(event),
            ['Molecule 2 of 3 scored 0.00 (total 0.50).',
             'Nothing formed (score 0.00)'])

    def test_wrong_kind_refused(self):
        with self.assertRaises(ValueError) as cm:
            status_text.molecule_scored_lines(_event('molecule_skipped'))
        self.assertIn('molecule_scored', str(cm.exception))
        self.assertIn('molecule_skipped', str(cm.exception))

    def test_missing_payload_keys_refused(self):
        for key in ('score', 'total', 'molecule_pos', 'molecule_total',
                    'formed', 'required', 'extras'):
            payload = {'score': 1.0, 'total': 2.5,
                       'molecule_pos': 1, 'molecule_total': 2,
                       'formed': ['h_bond'],
                       'required': {'mode': 'any', 'items': []},
                       'extras': []}
            del payload[key]
            with self.assertRaises(ValueError) as cm:
                status_text.molecule_scored_lines(
                    _event('molecule_scored', **payload))
            self.assertIn(key, str(cm.exception))


class TestMoleculeSkippedLine(unittest.TestCase):
    """The skip event line (SCORE-05)."""

    def test_basic(self):
        event = _event('molecule_skipped', score=0.5, total=2.5,
                       molecule_pos=1, molecule_total=2)
        self.assertEqual(
            status_text.molecule_skipped_line(event),
            'Skipped molecule 1 of 2 (partial score 0.50, total 2.50).')

    def test_wrong_kind_refused(self):
        with self.assertRaises(ValueError) as cm:
            status_text.molecule_skipped_line(_event('gave_up'))
        self.assertIn('molecule_skipped', str(cm.exception))

    def test_missing_key_refused(self):
        for key in ('score', 'total', 'molecule_pos', 'molecule_total'):
            payload = {'score': 0.5, 'total': 2.5,
                       'molecule_pos': 1, 'molecule_total': 2}
            del payload[key]
            with self.assertRaises(ValueError) as cm:
                status_text.molecule_skipped_line(
                    _event('molecule_skipped', **payload))
            self.assertIn(key, str(cm.exception))


class TestGaveUpLine(unittest.TestCase):
    """The give-up event line (positions 1-based)."""

    def test_basic(self):
        event = _event('gave_up', total=2.5, molecule_pos=1,
                       molecule_total=2, level_pos=2)
        self.assertEqual(
            status_text.gave_up_line(event),
            'Game ended at level 2, molecule 1 of 2 (total 2.50).')

    def test_wrong_kind_refused(self):
        with self.assertRaises(ValueError) as cm:
            status_text.gave_up_line(_event('level_advanced'))
        self.assertIn('gave_up', str(cm.exception))

    def test_missing_key_refused(self):
        for key in ('total', 'molecule_pos', 'molecule_total',
                    'level_pos'):
            payload = {'total': 2.5, 'molecule_pos': 1,
                       'molecule_total': 2, 'level_pos': 2}
            del payload[key]
            with self.assertRaises(ValueError) as cm:
                status_text.gave_up_line(_event('gave_up', **payload))
            self.assertIn(key, str(cm.exception))


class TestLevelAdvancedLine(unittest.TestCase):
    """The level-advance line. The builder is PINNED but ops do NOT emit
    it -- the poll's position-change line already announces the new
    level (endgame-ui D8). The kind stays vocabulary-complete."""

    def test_basic(self):
        event = _event('level_advanced', level_pos=2)
        self.assertEqual(status_text.level_advanced_line(event),
                         'Level 2 begins.')

    def test_wrong_kind_refused(self):
        with self.assertRaises(ValueError) as cm:
            status_text.level_advanced_line(_event('game_reset'))
        self.assertIn('level_advanced', str(cm.exception))

    def test_missing_key_refused(self):
        with self.assertRaises(ValueError) as cm:
            status_text.level_advanced_line(_event('level_advanced'))
        self.assertIn('level_pos', str(cm.exception))


class TestGameResetLine(unittest.TestCase):
    """The reset event line (restart-reset D4's orientation note)."""

    def test_basic(self):
        self.assertEqual(
            status_text.game_reset_line(_event('game_reset')),
            'Amino acids reset to grid positions (orientations kept).')

    def test_wrong_kind_refused(self):
        with self.assertRaises(ValueError) as cm:
            status_text.game_reset_line(
                _event('molecule_scored', score=1.0, total=1.0,
                       molecule_pos=1, molecule_total=2, formed=[],
                       required={'mode': 'any', 'items': []}, extras=[]))
        self.assertIn('game_reset', str(cm.exception))


class TestGameRestartedLine(unittest.TestCase):
    """The restart line -- handler-logged by the tab AFTER the countdown
    arms (the countdown clears the box; the marker would die with the
    popped wizard), so it NEVER poll-emits: it is EXCLUDED from the
    builder table and takes no event argument."""

    def test_basic(self):
        self.assertEqual(status_text.game_restarted_line(),
                         'Game restarted.')

    def test_not_in_poll_builder_table(self):
        self.assertNotIn('game_restarted', status_text._EVENT_BUILDERS)


class TestStatusEventsLastEvent(unittest.TestCase):
    """The poll-diff's last_event fingerprint (D2 event channel): one new
    whole-dict fingerprint key; event lines prepend BEFORE the position
    line; the seq counter makes identical consecutive events distinct;
    'result' stays unfingerprinted (pitfall 7)."""

    def _scored_marker(self, seq=1):
        return _event('molecule_scored', seq=seq, score=1.0, total=1.0,
                      molecule_pos=1, molecule_total=2,
                      formed=['h_bond'],
                      required={'mode': 'list',
                                'items': [{'type': 'h_bond', 'count': 1}]},
                      extras=[])

    def test_new_marker_emits_event_lines(self):
        prev = _state()
        curr = _state(last_event=self._scored_marker())
        self.assertEqual(
            status_text.status_events(prev, curr),
            ['Molecule 1 of 2 scored 1.00 (total 1.00).',
             '1/1 required interactions formed (score 1.00)',
             'Formed: h_bond'])

    def test_unchanged_marker_silent(self):
        marker = self._scored_marker()
        prev = _state(last_event=marker)
        curr = _state(last_event=dict(marker))
        self.assertEqual(status_text.status_events(prev, curr), [])

    def test_new_marker_replaces_old(self):
        prev = _state(last_event=self._scored_marker(seq=1))
        curr = _state(last_event=_event('game_reset', seq=2))
        self.assertEqual(
            status_text.status_events(prev, curr),
            ['Amino acids reset to grid positions (orientations kept).'])

    def test_same_payload_new_seq_fires(self):
        # The seq counter makes identical consecutive events (two Resets
        # in a row) distinct -- no sticky-dedupe ambiguity.
        prev = _state(last_event=_event('game_reset', seq=2))
        curr = _state(last_event=_event('game_reset', seq=3))
        self.assertEqual(
            status_text.status_events(prev, curr),
            ['Amino acids reset to grid positions (orientations kept).'])

    def test_cleared_marker_silent(self):
        prev = _state(last_event=self._scored_marker())
        curr = _state(last_event=None)
        self.assertEqual(status_text.status_events(prev, curr), [])

    def test_event_lines_before_position_line(self):
        # Behavior 7 (the scenario pin): prev without marker, curr with a
        # molecule_scored marker + a level change -> exactly the scored
        # header, the debrief lines, then the position line, IN ORDER.
        prev = _state()
        curr = _state(level_pos=2, molecule_id='mol-001', molecule_pos=1,
                      molecule_total=2,
                      last_event=_event(
                          'molecule_scored', seq=3, score=1.0, total=2.5,
                          molecule_pos=2, molecule_total=2,
                          formed=['h_bond'],
                          required={'mode': 'list',
                                    'items': [{'type': 'h_bond',
                                               'count': 1}]},
                          extras=[]))
        self.assertEqual(
            status_text.status_events(prev, curr),
            ['Molecule 2 of 2 scored 1.00 (total 2.50).',
             '1/1 required interactions formed (score 1.00)',
             'Formed: h_bond',
             'Level 2, molecule 1 of 2.'])

    def test_event_lines_before_selection_and_error(self):
        prev = _state()
        curr = _state(selected={'slot_id': 'r2c1', 'object': '_aam_aa05'},
                      error='Select an amino acid first.',
                      last_event=_event('game_reset', seq=1))
        self.assertEqual(
            status_text.status_events(prev, curr),
            ['Amino acids reset to grid positions (orientations kept).',
             'Selected: slot r2c1 (_aam_aa05).',
             'ERROR: Select an amino acid first.'])

    def test_unknown_kind_refused(self):
        prev = _state()
        curr = _state(last_event=_event('wizard_boop', seq=1))
        with self.assertRaises(ValueError) as cm:
            status_text.status_events(prev, curr)
        self.assertIn('wizard_boop', str(cm.exception))

    def test_game_restarted_marker_refused(self):
        # game_restarted is EXCLUDED from the poll table -- it is
        # handler-logged by the tab (the countdown clears the box).
        prev = _state()
        curr = _state(last_event=_event('game_restarted', seq=1))
        with self.assertRaises(ValueError) as cm:
            status_text.status_events(prev, curr)
        self.assertIn('game_restarted', str(cm.exception))

    def test_first_observation_with_marker_still_silent(self):
        # prev None -> [] unchanged, even with a marker present (pitfall
        # 4: the start sequence owns the first event).
        self.assertEqual(
            status_text.status_events(
                None, _state(last_event=self._scored_marker())),
            [])


class TestEndgameLines(unittest.TestCase):
    """The endgame block (SCORE-07; the info box AND the modal render the
    SAME block -- lines[0] is always the headline)."""

    def _summary(self, **overrides):
        summary = {'end_state': 'completed',
                   'level_scores': [1.0, 0.5],
                   'total': 1.5,
                   'final_time': 75.0,
                   'levels': 2,
                   'molecules': 4,
                   'molecules_completed': 4,
                   'skip_count': 0,
                   'giveup_count': 0,
                   'ended_level': 2,
                   'ended_molecule': 2}
        summary.update(overrides)
        return summary

    def test_completed_block(self):
        self.assertEqual(
            status_text.endgame_lines(self._summary()),
            ['You win! All 2 level(s) finished in 1:15.',
             'Level 1: 1.00',
             'Level 2: 0.50',
             'Total score: 1.50.',
             'Time: 1:15.',
             'Molecules completed: 4 of 4. Levels: 2.',
             'Skips: 0. Give-ups: 0.'])

    def test_gave_up_block(self):
        # The gave-up headline's molecule denominator is the uniform
        # per-level molecule count: molecules // levels (every level has
        # exactly m molecules by construction -- 06-RESEARCH.md Q5).
        self.assertEqual(
            status_text.endgame_lines(
                self._summary(end_state='gave_up',
                              level_scores=[1.0, 0.5, 0.0],
                              final_time=3661.0,
                              levels=3, molecules=6,
                              molecules_completed=3,
                              skip_count=1, giveup_count=1,
                              ended_level=2, ended_molecule=1)),
            ['Game over -- gave up at level 2, molecule 1 of 2.',
             'Level 1: 1.00',
             'Level 2: 0.50',
             'Level 3: 0.00',
             'Total score: 1.50.',
             'Time: 61:01.',
             'Molecules completed: 3 of 6. Levels: 3.',
             'Skips: 1. Give-ups: 1.'])

    def test_headline_always_first(self):
        for state in ('completed', 'gave_up'):
            lines = status_text.endgame_lines(self._summary(
                end_state=state,
                level_scores=[0.0] * 3, levels=3, molecules=6))
            if state == 'completed':
                self.assertTrue(lines[0].startswith('You win!'))
            else:
                self.assertTrue(lines[0].startswith('Game over'))

    def test_missing_key_refused(self):
        for key in ('end_state', 'level_scores', 'total', 'final_time',
                    'levels', 'molecules', 'molecules_completed',
                    'skip_count', 'giveup_count', 'ended_level',
                    'ended_molecule'):
            summary = self._summary()
            del summary[key]
            with self.assertRaises(ValueError) as cm:
                status_text.endgame_lines(summary)
            self.assertIn(key, str(cm.exception))

    def test_unknown_end_state_refused(self):
        with self.assertRaises(ValueError) as cm:
            status_text.endgame_lines(self._summary(end_state='exploded'))
        self.assertIn('exploded', str(cm.exception))


# ---------------------------------------------------------------------------
# Phase 7 (plan 07-03) -- additive battery. RED first: the three
# handler-logged line builders (game_saved_line, game_imported_line,
# game_resumed_line) do not exist yet, so these tests fail on
# AttributeError; the GREEN commit implements them. The Phase-5/6 pins above
# stay BYTE-UNCHANGED: EVENT_KINDS keeps its EXACTLY-15-key set and the
# game_saved/game_imported reserved notes keep their 'reserved for Phase 7'
# wording byte-unchanged (the Phase-6 precedent -- the builders, not the
# dict, carry the final wording; reserved-note pins at :315-316 and
# TestEventKinds keep passing untouched).
#
# Pattern provenance (05-RESEARCH-status-surface.md:290-291): 'Game saved
# to %s.' / 'Game imported: %s.' are DIRECT-_log lines emitted by tab-side
# handlers, NOT the poll-diff -- Save/Import are tab operations (the wizard
# is not the actor; for Import the wizard does not exist yet), and the
# poll's fingerprint set has no key for them. The same handler-logged
# law as game_restarted_line applies: no event argument, EXCLUDED from
# _EVENT_BUILDERS. game_resumed_line (07-RESEARCH-state.md section 4 step 9
# -- the checkpoint-resume tab re-arm) shares the pattern; the EVENT_KINDS
# set has no resume kind and the handler-logged pattern needs none.
# ---------------------------------------------------------------------------


class TestGameSavedLine(unittest.TestCase):
    """The save line (SCORE-08): 'Game saved to %s.' -- handler-logged by
    the Game tab's Save wrapper AFTER a successful checkpoint write."""

    def test_basic(self):
        self.assertEqual(
            status_text.game_saved_line('C:\\x\\game.aamz'),
            'Game saved to C:\\x\\game.aamz.')

    def test_trailing_period(self):
        # The trailing period is part of the pinned wording.
        self.assertEqual(
            status_text.game_saved_line('out/game.aamz'),
            'Game saved to out/game.aamz.')


class TestGameImportedLine(unittest.TestCase):
    """The import line (PERSIST-02): 'Game imported: %s.' --
    handler-logged by the Game tab's Import wrapper AFTER
    start_countdown arms (the countdown's _info_log.clear() would wipe
    a pre-arm line -- the restart D2/D7 law verbatim)."""

    def test_basic(self):
        path = 'C:\\save\\level3.aamz'
        self.assertEqual(status_text.game_imported_line(path),
                         'Game imported: %s.' % path)


class TestGameResumedLine(unittest.TestCase):
    """The checkpoint-resume line (PERSIST-03): 'Game resumed from %s.'
    -- handler-logged by the Game tab after a checkpoint load re-arms
    the tab (no countdown on resume)."""

    def test_basic(self):
        path = 'C:\\auto\\checkpoint.aamz'
        self.assertEqual(status_text.game_resumed_line(path),
                         'Game resumed from %s.' % path)


class TestPhase7BuildersHandlerLogged(unittest.TestCase):
    """The three Phase-7 builders share the game_restarted_line
    handler-logged pattern: they take no event argument (their single
    parameter is 'path') and are EXCLUDED from _EVENT_BUILDERS -- the
    poll-diff can never see them (tab-side operations; the reserved
    EVENT_KINDS set stays 15, no new kind)."""

    def test_kinds_not_in_poll_builder_table(self):
        table = status_text._EVENT_BUILDERS
        self.assertNotIn('game_saved', table)
        self.assertNotIn('game_imported', table)
        self.assertNotIn('game_resumed', table)

    def test_builder_functions_not_in_poll_builder_table(self):
        values = set(status_text._EVENT_BUILDERS.values())
        for name in ('game_saved_line', 'game_imported_line',
                     'game_resumed_line'):
            self.assertNotIn(getattr(status_text, name), values)

    def test_take_no_event_argument(self):
        # Signature pin: exactly one parameter, named 'path' -- these
        # builders never consume a last_event marker payload.
        for name in ('game_saved_line', 'game_imported_line',
                     'game_resumed_line'):
            params = list(inspect.signature(
                getattr(status_text, name)).parameters.values())
            self.assertEqual(len(params), 1, name)
            self.assertEqual(params[0].name, 'path', name)

    def test_vocabulary_pins_unchanged(self):
        # The pre-existing vocabulary pins must keep passing
        # byte-unchanged: exactly 15 kinds, and the game_saved /
        # game_imported notes still carry 'reserved for Phase 7'.
        self.assertEqual(len(status_text.EVENT_KINDS), 15)
        self.assertIn('reserved for Phase 7',
                      status_text.EVENT_KINDS['game_saved'])
        self.assertIn('reserved for Phase 7',
                      status_text.EVENT_KINDS['game_imported'])


if __name__ == '__main__':
    unittest.main()
