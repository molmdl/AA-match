"""Verbatim content pins for aamatch/help_text.py (plan 09-04, DOCS-02).

``help_text`` is PURE and imports clean under bare python3.6 -- these
tests import it directly with ZERO sys.modules stubs (the standing
purity contract). Every load-bearing string a player can eventually see
in the Help panel or the wizard prompt is pinned BYTE-VERBATIM here in
WSL, BEFORE the Qt wiring (09-07) or the prompt reword (09-08) touches
any surface. The per-surface pure-module law (status_text.py:16-17):
pure = WSL-pinnable = drift-auditable at criterion 3.

Mechanical laws enforced here:

- The three re-homed dicts (INTERACTION_LABELS / INTERACTION_TIPS /
  MODE_CONTEXT) are byte-identical to setup_window.py's live strings, so
  the 09-07 widget repoint is behavior-preserving.
- SELECTED_GESTURE_HINT names the three shipped drag gestures EXACTLY and
  contains zero keyboard-legacy tokens (arrow/wasd) -- the Phase-8.3
  supersession (mouse drag is the only movement channel; STATE.md
  08.3-03/08.3-16).
- Done = closing the board, never an endgame summary (quick-004).
- The Cleanup bullet follows the 09-01 Decision A branch (a-add); the
  a-accept wording is DEAD.
- The help HTML is a FRAGMENT (no html/body wrapper; QTextEdit renders
  fragments) and every ampersand is escaped.
"""

import unittest

from aamatch import help_text
from aamatch.setup_state import INTERACTION_TYPES


class TestCanonicalDicts(unittest.TestCase):
    """The re-homed dicts cover the enum exactly and preserve wording."""

    def test_every_interaction_type_has_a_label_and_tip(self):
        for t in INTERACTION_TYPES:
            with self.subTest(interaction=t):
                self.assertIn(t, help_text.INTERACTION_LABELS)
                self.assertIn(t, help_text.INTERACTION_TIPS)

    def test_label_key_set_matches_the_canonical_enum(self):
        self.assertEqual(set(help_text.INTERACTION_LABELS),
                         set(INTERACTION_TYPES))

    def test_tip_key_set_matches_the_canonical_enum(self):
        self.assertEqual(set(help_text.INTERACTION_TIPS),
                         set(INTERACTION_TYPES))

    def test_each_tip_starts_with_its_label(self):
        for t in INTERACTION_TYPES:
            with self.subTest(interaction=t):
                self.assertTrue(
                    help_text.INTERACTION_TIPS[t].startswith(
                        help_text.INTERACTION_LABELS[t] + ': '),
                    'tip for %r must start %r: got %r'
                    % (t, help_text.INTERACTION_LABELS[t] + ': ',
                       help_text.INTERACTION_TIPS[t]))

    def test_h_bond_tip_byte_verbatim(self):
        # Pinned exactly as authored in help_text.py (re-homed verbatim
        # from setup_window.py:397-415).
        self.assertEqual(
            help_text.INTERACTION_TIPS['h_bond'],
            'Hydrogen bond: a donor hydrogen (-OH or -NH) facing an '
            'acceptor oxygen or nitrogen on the other molecule.')

    def test_metal_tip_byte_verbatim(self):
        self.assertEqual(
            help_text.INTERACTION_TIPS['metal'],
            'Metal coordination: a metal ion bound by two or more '
            'donor atoms.')

    def test_mode_context_byte_verbatim(self):
        self.assertEqual(
            help_text.MODE_CONTEXT,
            {
                'exclusive':
                    'The game accepts ANY of the checked interactions',
                'block_exclusive':
                    'The player must form EXACTLY the checked '
                    'interactions',
                'unset':
                    'The game randomizes the required set from the '
                    'checked types (hydrophobic excluded from random '
                    'picks).',
            })


class TestGestureHint(unittest.TestCase):
    """The drag-gesture wording + the no-keyboard-law + clip safety."""

    EXPECTED = ('Shift+left-drag moves it; shift+right-drag rotates it; '
                'ctrl+shift+left-drag changes its depth.')

    def test_hint_byte_verbatim(self):
        self.assertEqual(help_text.SELECTED_GESTURE_HINT, self.EXPECTED)

    def test_hint_is_ascii(self):
        # Overlay-bound strings must be ASCII (wizard_text.py:64-74).
        self.assertTrue(
            all(ord(c) < 128 for c in help_text.SELECTED_GESTURE_HINT),
            'gesture hint must be ASCII-only: %r'
            % (help_text.SELECTED_GESTURE_HINT,))

    def test_hint_names_the_three_shipped_gestures(self):
        hint = help_text.SELECTED_GESTURE_HINT
        self.assertIn('Shift+left-drag', hint)
        self.assertIn('shift+right-drag', hint)
        self.assertIn('ctrl+shift+left-drag', hint)

    def test_hint_has_no_keyboard_legacy_tokens(self):
        # Phase-8.3 supersession law: keyboard direction keys were all
        # deleted; mouse drag is the only movement channel.
        hint = help_text.SELECTED_GESTURE_HINT.lower()
        self.assertNotIn('arrow', hint)
        self.assertNotIn('wasd', hint)

    def test_prompt_plus_hint_fits_the_overlay_clip(self):
        # The 255-char WordType[256] panel cap: the longest realistic
        # selection line joined with the hint must still fit.
        prompt = ('Selected: slot r0c2 (_aam_aa999999). Move/rotate it, '
                  'then Confirm. ')
        self.assertLess(len(prompt + help_text.SELECTED_GESTURE_HINT),
                        255)


class TestHelpSections(unittest.TestCase):
    """The 7-section builder's structure and derived rows."""

    def test_section_titles_and_order(self):
        sections = help_text.help_sections()
        self.assertEqual(
            [title for title, _ in sections],
            ['How to play', 'Interaction types', 'Scoring and Confirm',
             'Interaction modes', 'Buttons', 'Saving and loading',
             'Tips'])

    def test_every_section_has_at_least_two_non_empty_lines(self):
        for title, lines in help_text.help_sections():
            with self.subTest(section=title):
                non_empty = [line for line in lines if line.strip()]
                self.assertGreaterEqual(
                    len(non_empty), 2,
                    'section %r must have >= 2 non-empty lines; got %r'
                    % (title, lines))

    def test_interaction_type_lines_are_canonical_order(self):
        sections = dict(help_text.help_sections())
        expected = [
            '%s: %s' % (help_text.INTERACTION_LABELS[t],
                        help_text.INTERACTION_TIPS[t])
            for t in INTERACTION_TYPES]
        self.assertEqual(sections['Interaction types'], expected)

    def test_interaction_mode_lines(self):
        sections = dict(help_text.help_sections())
        expected = [
            help_text.MODE_CONTEXT['exclusive'],
            help_text.MODE_CONTEXT['block_exclusive'],
            help_text.MODE_CONTEXT['unset'],
            'The mode radios in the Setup tab restate these meanings '
            'live.',
        ]
        self.assertEqual(sections['Interaction modes'], expected)

    def test_how_to_play_starts_with_click_instruction(self):
        sections = dict(help_text.help_sections())
        self.assertTrue(
            sections['How to play'][0].startswith(
                'Click an amino acid to select it.'))


class TestDoneAndDestructiveWordings(unittest.TestCase):
    """Done and destructive-action truth, per the recorded decisions."""

    def setUp(self):
        self.buttons_text = '\n'.join(
            dict(help_text.help_sections())['Buttons'])

    def test_done_closes_the_board(self):
        self.assertIn('Done closes the board', self.buttons_text)

    def test_done_never_promises_an_endgame_summary(self):
        # quick-004: abandon-stop, no record, no endgame screen.
        self.assertIn('without the endgame screen', self.buttons_text)

    def test_restart_and_import_have_no_confirmation(self):
        # 06-08 D9 / 07-07 RD2: recorded no-warning decisions.
        self.assertIn('no confirmation', self.buttons_text)

    def test_reset_keeps_orientations(self):
        self.assertIn('orientations are kept', self.buttons_text)

    def test_cleanup_follows_the_09_01_a_add_branch(self):
        # 09-01 Decision A = a-add; the a-accept wording is DEAD.
        self.assertIn('after asking for confirmation',
                      self.buttons_text)


class TestO1Tip(unittest.TestCase):
    """The recorded O1 salt-bridge/H-bond lesson (approved thresholds)."""

    def setUp(self):
        self.tips_text = '\n'.join(
            dict(help_text.help_sections())['Tips'])

    def test_scores_are_independent(self):
        self.assertIn('scored independently', self.tips_text)

    def test_salt_distance_present(self):
        self.assertIn('5.5 A', self.tips_text)

    def test_h_bond_distance_present(self):
        self.assertIn('4.0 A', self.tips_text)

    def test_h_bond_angle_present(self):
        self.assertIn('140 deg', self.tips_text)


class TestHtmlFragment(unittest.TestCase):
    """help_html() is a fragment, complete, and fully escaped."""

    TITLES = ['How to play', 'Interaction types', 'Scoring and Confirm',
              'Interaction modes', 'Buttons', 'Saving and loading',
              'Tips']

    def test_starts_with_a_heading(self):
        self.assertTrue(help_text.help_html().startswith('<h2>'))

    def test_is_a_fragment_not_a_document(self):
        # The bioCHEMeleon v1 law: QTextEdit renders fragments.
        html = help_text.help_html()
        self.assertNotIn('<html', html)
        self.assertNotIn('</html', html)
        self.assertNotIn('<body', html)

    def test_every_title_appears_as_a_heading(self):
        html = help_text.help_html()
        for title in self.TITLES:
            with self.subTest(title=title):
                self.assertIn('<h2>%s</h2>' % title, html)

    def test_every_interaction_label_appears(self):
        html = help_text.help_html()
        for label in help_text.INTERACTION_LABELS.values():
            with self.subTest(label=label):
                self.assertIn(label, html)

    def test_every_ampersand_is_an_entity_escape(self):
        html = help_text.help_html()
        for i, ch in enumerate(html):
            if ch == '&':
                self.assertEqual(
                    html[i:i + 5], '&amp;',
                    'unescaped "&" at index %d: %r'
                    % (i, html[i:i + 10]))


if __name__ == '__main__':
    unittest.main()
