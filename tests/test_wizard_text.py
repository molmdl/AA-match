"""TDD RED battery for aamatch/wizard_text.py (plan 03-02).

Phase 3's wizard panel is the game's entire pre-Qt UI (PLAY-03: "result
visible in the wizard panel"). This module pins the PURE text half --
panel entry lists, prompt lines, and detection-result rendering as pure
functions of plain-data wizard state -- BEFORE plan 03-03's GameWizard
wires them to the live pymol.wizard.Wizard hooks. Written FIRST (RED):
``aamatch.wizard_text`` does not exist yet, so collecting this module
raises ImportError -- that failure IS the RED proof. Task-2 GREEN then
implements the builders and registers the module in PURE_MODULES.

Mechanical properties pinned here (03-RESEARCH-wizard-interaction.md
section 3, Wizard.cpp:239-246 / WordType[256] / PParse-at-click):
- Panel entries are ALWAYS 3-element lists [kind, text, code]; kinds
  0=blank/1=text/2=button (2-element entries render BLANK in the C
  parser). Panel text is capped at 255 chars per line and must be ASCII
  (PyMOL overlay font safety; 'deg', never a degree sign).
- Button codes reference ONLY cmd.set_wizard() (canonical Done) or
  cmd.get_wizard().method(...) -- PParse'd at CLICK time against the
  live top-of-stack instance, so NO module name may ever appear
  (module-identity trap: aamatch vs pmg_tk.startup.aamatch, AGENTS.md
  gate 5).
- Result rendering is TEXT ONLY (PLAY-04 no-helper-visuals): score
  fraction + formed/missing type names -- never geometry, coordinates,
  or atom names. SCORE-01 semantics mirror game_state.score: 'any' is
  binary, 'list' is formed items / items.

State dicts are PLAIN DATA shaped exactly like what 03-03's GameWizard
will hold:
    {'molecule_id': 'mol-001', 'molecule_pos': 1, 'molecule_total': 2,
     'selected': {'slot_id': 'r0c2', 'object': '_aam_aa003'} | None,
     'result': {'score': 1.0, 'formed': ['pi_stacking'],
                'required': {...}} | None,
     'error': None | str,
     'required': {'mode': ..., 'items': [...]}}
"""

import re
import unittest

from aamatch import wizard_text

# Lore only -- assertion uses a REGEX, not this token object call shape.
_BUTTON_CODE_RE = re.compile(r'^cmd\.get_wizard\(\)\.[a-z_]+\(')

_REQUIRED_LIST_2 = {'mode': 'list',
                    'items': [{'type': 'h_bond', 'count': 1},
                              {'type': 'pi_stacking', 'count': 2}]}

_ALL_BUTTON_LABELS = {'Left', 'Right', 'Up', 'Down', 'In', 'Out',
                      'Toward ligand', 'Rotate 90 deg', 'Confirm',
                      'Reset to Grid', 'Done'}


def _state(**overrides):
    """Plain-data wizard state shaped like 03-03's GameWizard holds."""
    state = {'molecule_id': 'mol-001',
             'molecule_pos': 1,
             'molecule_total': 2,
             'selected': None,
             'result': None,
             'error': None,
             'required': _REQUIRED_LIST_2}
    state.update(overrides)
    return state


def _result(score=1.0, formed=('pi_stacking',), required=None):
    """engine.confirm's plain-data triple as the wizard carries it."""
    return {'score': score, 'formed': list(formed),
            'required': (required if required is not None
                         else {'mode': 'list',
                               'items': [{'type': 'pi_stacking',
                                          'count': 1}]})}


class TestRequiredSummary(unittest.TestCase):
    """required_summary: 'pi_stacking x1' style list summaries /
    'any interaction' for exclusive mode; fail-closed like
    game_state.score."""

    def test_single_list_item(self):
        required = {'mode': 'list',
                    'items': [{'type': 'pi_stacking', 'count': 1}]}
        self.assertEqual(wizard_text.required_summary(required),
                         'pi_stacking x1')

    def test_two_items_rendered_in_given_order(self):
        self.assertEqual(wizard_text.required_summary(_REQUIRED_LIST_2),
                         'h_bond x1, pi_stacking x2')

    def test_order_as_given_not_resorted(self):
        reversed_items = {'mode': 'list',
                          'items': [{'type': 'pi_stacking', 'count': 2},
                                    {'type': 'h_bond', 'count': 1}]}
        self.assertEqual(wizard_text.required_summary(reversed_items),
                         'pi_stacking x2, h_bond x1')

    def test_any_mode(self):
        self.assertEqual(
            wizard_text.required_summary({'mode': 'any', 'items': []}),
            'any interaction')

    def test_unknown_mode_refused(self):
        with self.assertRaises(ValueError):
            wizard_text.required_summary({'mode': 'weird', 'items': []})

    def test_list_mode_empty_items_refused(self):
        with self.assertRaises(ValueError):
            wizard_text.required_summary({'mode': 'list', 'items': []})

    def test_list_mode_missing_items_refused(self):
        with self.assertRaises(ValueError):
            wizard_text.required_summary({'mode': 'list'})


class TestPanelContract(unittest.TestCase):
    """THE panel contract battery: 3-element entries, kinds {0,1,2},
    255-char cap, ASCII-only, module-identity-safe button codes."""

    def setUp(self):
        self.entries = wizard_text.panel_entries(_state())

    def _buttons(self):
        return [e for e in self.entries if e[0] == 2]

    def test_every_entry_is_exactly_3_element_list_with_str_text(self):
        self.assertTrue(self.entries)
        for entry in self.entries:
            self.assertIsInstance(entry, list)
            self.assertEqual(len(entry), 3,
                             'every panel entry must be [kind, text, code] '
                             '(-- 2-element entries render BLANK): %r'
                             % (entry,))
            self.assertIn(entry[0], (0, 1, 2),
                          'unknown panel kind: %r' % (entry,))
            self.assertIsInstance(entry[1], str)

    def test_text_is_ascii_only(self):
        for entry in self.entries:
            entry[1].encode('ascii')  # raises UnicodeEncodeError on failure

    def test_no_text_exceeds_255_chars(self):
        for entry in self.entries:
            self.assertLessEqual(len(entry[1]), 255,
                                 'panel line cap is WordType[256]: %r'
                                 % (entry[1],))

    def test_exactly_one_done_button_with_canonical_exit_code(self):
        done = [e for e in self._buttons() if e[1] == 'Done']
        self.assertEqual(len(done), 1)
        self.assertEqual(done[0][2], 'cmd.set_wizard()')

    def test_other_button_codes_are_module_identity_safe(self):
        for entry in self._buttons():
            if entry[1] == 'Done':
                continue
            self.assertRegex(entry[2], _BUTTON_CODE_RE,
                             'panel code must be PParse-safe against the '
                             'live top-of-stack wizard: %r' % (entry[2],))

    def test_no_module_name_appears_in_any_button_code(self):
        for entry in self.entries:
            code = entry[2]
            self.assertIsInstance(code, str)
            self.assertNotIn('aamatch', code)
            self.assertNotIn('pmg_tk', code)

    def test_button_inventory_exact(self):
        labels = set(e[1] for e in self._buttons())
        self.assertEqual(labels, _ALL_BUTTON_LABELS)

    def test_movement_button_codes(self):
        expected = {
            'Left': 'cmd.get_wizard().nudge_cam(-1, 0, 0)',
            'Right': 'cmd.get_wizard().nudge_cam(1, 0, 0)',
            'Up': 'cmd.get_wizard().nudge_cam(0, 1, 0)',
            'Down': 'cmd.get_wizard().nudge_cam(0, -1, 0)',
            'In': 'cmd.get_wizard().nudge_cam(0, 0, -1)',
            'Out': 'cmd.get_wizard().nudge_cam(0, 0, 1)',
            'Toward ligand': 'cmd.get_wizard().step_to_ligand()',
            'Rotate 90 deg': 'cmd.get_wizard().rotate_view(90)',
            'Confirm': 'cmd.get_wizard().confirm_molecule()',
            'Reset to Grid': 'cmd.get_wizard().reset_grid()',
        }
        codes = dict((e[1], e[2]) for e in self._buttons())
        for label, code in expected.items():
            self.assertEqual(codes.get(label), code,
                             'button %r code mismatch' % (label,))

    def test_header_line_names_molecule_and_position(self):
        texts = [e[1] for e in self.entries]
        header = [t for t in texts if 'mol-001' in t and '(1/2)' in t]
        self.assertTrue(header,
                        'no header line naming the molecule id and the '
                        '(pos/total) position: %r' % (texts,))

    def test_required_line_contains_summary(self):
        texts = [e[1] for e in self.entries]
        summary = 'h_bond x1, pi_stacking x2'
        self.assertTrue(any(summary in t for t in texts),
                        'no panel line carries required_summary: %r'
                        % (texts,))

    def test_movement_header_mentions_step_size(self):
        self.assertTrue(any('1 A per press' in e[1] for e in self.entries),
                        'movement header must embed NUDGE_STEP as text')

    def test_buttons_and_labels_appear_exactly_once_each(self):
        counts = {}
        for entry in self.entries:
            if entry[0] in (1, 2) and entry[1] in _ALL_BUTTON_LABELS:
                counts[entry[1]] = counts.get(entry[1], 0) + 1
        self.assertEqual(counts.get('Confirm', 0), 1,
                         'no duplicated Confirm button')
        for entry in self._buttons():
            self.assertIn(entry[1], _ALL_BUTTON_LABELS)
        self.assertEqual(len(self._buttons()), len(_ALL_BUTTON_LABELS))

    def test_long_error_string_is_clipped_not_crashed(self):
        state = _state(error='x' * 400)
        entries = wizard_text.panel_entries(state)
        for entry in entries:
            self.assertLessEqual(len(entry[1]), 255)
        shown = [e[1] for e in entries if 'xxx' in e[1]]
        self.assertTrue(shown, 'clipped error must still surface, not vanish')


class TestPanelResultRendering(unittest.TestCase):
    """Result lines appear in the panel exactly when state['result'] is
    set (PLAY-03: result visible in the wizard panel)."""

    def test_result_lines_present_when_result_set(self):
        result = _result(score=1.0, formed=('pi_stacking',))
        entries = wizard_text.panel_entries(_state(result=result))
        texts = [e[1] for e in entries]
        for line in wizard_text.result_lines(result['score'],
                                             result['formed'],
                                             result['required']):
            self.assertIn(line, texts)

    def test_no_result_lines_when_result_none(self):
        # Panel over the plain default state (no result, no selection).
        texts = [e[1] for e in wizard_text.panel_entries(_state())]
        self.assertFalse(any('Formed:' in t or 'score' in t
                             for t in texts),
                         'result-less panel must carry no result lines: '
                         '%r' % (texts,))


class TestPromptLines(unittest.TestCase):
    """prompt_lines: the always-visible status line list."""

    def test_no_selection_starts_with_click_instruction(self):
        lines = wizard_text.prompt_lines(_state())
        self.assertTrue(lines)
        self.assertIn('Click an amino acid', lines[0])

    def test_plain_list_of_str_never_none(self):
        lines = wizard_text.prompt_lines(_state())
        self.assertIsInstance(lines, list)
        for line in lines:
            self.assertIsInstance(line, str)

    def test_selected_shows_move_guidance_and_slot_identity(self):
        state = _state(selected={'slot_id': 'r0c2',
                                 'object': '_aam_aa003'})
        text = '\n'.join(wizard_text.prompt_lines(state))
        self.assertIn('Move/rotate', text)
        self.assertIn('r0c2', text)
        self.assertIn('_aam_aa003', text)

    def test_result_lines_included_verbatim(self):
        result = _result(score=0.5, formed=('h_bond',),
                         required=_REQUIRED_LIST_2)
        prompt = wizard_text.prompt_lines(_state(result=result))
        expected = wizard_text.result_lines(result['score'],
                                            result['formed'],
                                            result['required'])
        for start in range(len(prompt) - len(expected) + 1):
            if prompt[start:start + len(expected)] == expected:
                break
        else:
            self.fail('result lines not included verbatim in prompt: %r'
                      % (prompt,))

    def test_error_line_appears_last_prefixed_error(self):
        result = _result(score=1.0)
        state = _state(selected={'slot_id': 'r0c2',
                                 'object': '_aam_aa003'},
                       result=result, error='detector blew up')
        lines = wizard_text.prompt_lines(state)
        self.assertTrue(lines[-1].startswith('ERROR'),
                        'error line must be appended LAST (measurement.py '
                        'shape): %r' % (lines,))
        self.assertIn('detector blew up', lines[-1])

    def test_long_error_clipped_to_255(self):
        lines = wizard_text.prompt_lines(_state(error='y' * 400))
        for line in lines:
            self.assertLessEqual(len(line), 255)
        self.assertTrue(lines[-1].startswith('ERROR'))


class TestResultLines(unittest.TestCase):
    """result_lines: TEXT-ONLY detection-result rendering with SCORE-01
    semantics (score fraction + formed/missing type names only)."""

    def test_list_mode_one_of_two_formed(self):
        lines = wizard_text.result_lines(0.5, ['pi_stacking'],
                                         _REQUIRED_LIST_2)
        joined = '\n'.join(lines)
        self.assertIn('1/2', joined)
        self.assertIn('0.50', joined)
        self.assertIn('pi_stacking',
                      [l for l in lines if l.startswith('Formed:')][0])
        self.assertIn('h_bond',
                      [l for l in lines if l.startswith('Missing:')][0])

    def test_all_formed_no_missing_line(self):
        lines = wizard_text.result_lines(
            1.0, ['h_bond', 'pi_stacking'], _REQUIRED_LIST_2)
        joined = '\n'.join(lines)
        self.assertIn('1.00', joined)
        self.assertIn('2/2', joined)
        self.assertFalse(any(l.startswith('Missing:') for l in lines))

    def test_none_formed_pinned_shape(self):
        # PINNED SHAPE: the 'Formed:' line stays with '(none)'.
        lines = wizard_text.result_lines(0.0, [], _REQUIRED_LIST_2)
        formed = [l for l in lines if l.startswith('Formed:')]
        self.assertEqual(formed, ['Formed: (none)'])
        missing = [l for l in lines if l.startswith('Missing:')]
        self.assertTrue(missing and 'h_bond' in missing[0]
                        and 'pi_stacking' in missing[0])

    def test_any_mode_formed(self):
        any_required = {'mode': 'any', 'items': []}
        lines = wizard_text.result_lines(1.0, ['h_bond'], any_required)
        formed = [l for l in lines if l.startswith('Formed:')]
        self.assertTrue(formed and 'h_bond' in formed[0])
        self.assertFalse(any(l.startswith('Missing:') for l in lines))
        self.assertIn('1.00', '\n'.join(lines))

    def test_any_mode_nothing_formed_pinned_shape(self):
        # PINNED SHAPE: exactly 'Nothing formed (score 0.00)'.
        any_required = {'mode': 'any', 'items': []}
        lines = wizard_text.result_lines(0.0, [], any_required)
        self.assertEqual(lines, ['Nothing formed (score 0.00)'])

    def test_score_renders_with_exactly_two_decimals(self):
        lines = wizard_text.result_lines(0.5, ['h_bond'],
                                         _REQUIRED_LIST_2)
        self.assertRegex(lines[0], r'score \d+\.\d\d\)$')

    def test_text_only_no_geometry_descriptors(self):
        # PLAY-04: no coordinates, no 'Angstrom', no geometry words.
        forbidden = ('x:', 'y:', 'z:', 'Angstrom', 'A ')
        for lines in (
                wizard_text.result_lines(0.5, ['pi_stacking'],
                                         _REQUIRED_LIST_2),
                wizard_text.result_lines(1.0, ['h_bond'],
                                         {'mode': 'any', 'items': []}),
                wizard_text.result_lines(0.0, [], _REQUIRED_LIST_2)):
            for line in lines:
                for token in forbidden:
                    self.assertNotIn(token, line)

    def test_unknown_mode_refused(self):
        with self.assertRaises(ValueError):
            wizard_text.result_lines(0.0, [], {'mode': 'weird',
                                               'items': []})

    def test_list_mode_empty_items_refused(self):
        with self.assertRaises(ValueError):
            wizard_text.result_lines(0.0, [], {'mode': 'list',
                                               'items': []})


class TestClip(unittest.TestCase):
    """The 255-char cap helper: clip, never crash (WordType[256])."""

    def test_short_text_unchanged(self):
        self.assertEqual(wizard_text._clip('short'), 'short')

    def test_long_text_clipped_to_limit(self):
        out = wizard_text._clip('z' * 400)
        self.assertEqual(len(out), 255)
        self.assertTrue(out.startswith('zzz'))

    def test_explicit_limit(self):
        self.assertEqual(wizard_text._clip('abcdef', limit=3), 'abc')

    def test_non_string_coerced(self):
        self.assertEqual(wizard_text._clip(None), 'None')


if __name__ == '__main__':
    unittest.main()
