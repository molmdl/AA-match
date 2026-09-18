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


if __name__ == '__main__':
    unittest.main()
