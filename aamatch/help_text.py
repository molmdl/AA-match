"""Canonical in-game help content (Phase 9, plan 09-04).

Layer: PURE -- registered in tests/test_purity.py PURE_MODULES (Gate A
scans EVERY scope, module level and function body). Imports stdlib and
the pure ``.setup_state`` enum only. NO pymol/Qt/numpy: the builders are
dumb functions of plain data, returning plain strings.

Single-home rationale (09-RESEARCH-help-ui.md SS4/SS5): the per-surface
pure-module precedent is ``setup_form.py`` (the setup window's pure
glue) and ``status_text.py`` ("every string it can show is pinned here
in WSL before any Qt wiring exists"). Help content follows the same law:
one home, WSL-pinnable, drift-auditable at criterion 3 (DOCS-02). The
Qt tier (setup_window.py, 09-07) and the wizard prompt (wizard_text.py,
09-08) will CONSUME these constants; they must never restate them.

Content provenance (no invented facts -- every line is sourced):

- INTERACTION_LABELS / INTERACTION_TIPS / MODE_CONTEXT are the
  byte-identical strings that live in setup_window.py today
  (:386-394, :397-415, :418-425). They become the single home when the
  09-07 widget repoint lands; moving them here first keeps that repoint
  behavior-preserving.
- SELECTED_GESTURE_HINT is NEW text worded to the shipped drag model
  (Phase 8.3 supersession: shift+left-drag = view-plane translate,
  ctrl+shift+left-drag = depth, shift+right-drag = rotate -- the
  cmd.button map in wizard.py:335-337; STATE.md 08.3-03/08.3-16). Mouse
  drag is the ONLY movement channel; every keyboard-legacy movement key
  was deleted, so the hint contains no arrow/wasd wording.
- The section lines cite their canonical sources in comments at the
  point of use below.

The gesture hint and any prompt-bound text are ASCII-only: they may
reach the 255-char-clipped PyMOL wizard overlay (wizard_text.py:64-74),
where the overlay font has no reliable non-ASCII coverage. 'A' (not a
degree or Angstrom sign), 'deg', '...' -- never a Unicode glyph.
"""

# Canonical key order for every per-type dict: setup_state.INTERACTION_TYPES
# is THE enum home (canonical order frozen there). A pure sibling import
# is legal (setup_state imports stdlib only).
from .setup_state import INTERACTION_TYPES


# ---------------------------------------------------------------------------
# Re-homed canonical dicts (byte-identical to setup_window.py today)
# ---------------------------------------------------------------------------

# UI-only display labels for the canonical interaction enum strings (the
# stored values stay the enum strings; iteration order is frozen in
# setup_state.INTERACTION_TYPES). Source: setup_window.py:386-394.
INTERACTION_LABELS = {
    'h_bond': 'Hydrogen bond',
    'salt_bridge': 'Salt bridge',
    'pi_stacking': 'Pi-stacking',
    'cation_pi': 'Cation-pi',
    'hydrophobic': 'Hydrophobic',
    'halogen': 'Halogen bond',
    'metal': 'Metal coordination',
}

# Per-type help in game terms (the UI standard: clear but sufficient
# in-game explanation). Source: setup_window.py:397-415, verbatim.
INTERACTION_TIPS = {
    'h_bond': 'Hydrogen bond: a donor hydrogen (-OH or -NH) '
              'facing an acceptor oxygen or nitrogen on the other '
              'molecule.',
    'salt_bridge': 'Salt bridge: an opposite-charge pair held '
                   'together (a positive group on one molecule, a '
                   'negative group on the other).',
    'pi_stacking': 'Pi-stacking: two aromatic rings stacked '
                   'face-on or edge-on.',
    'cation_pi': 'Cation-pi: a positively charged group resting '
                 'on the face of an aromatic ring.',
    'hydrophobic': 'Hydrophobic: non-polar carbons of both '
                   'molecules clustered into the same greasy '
                   'patch.',
    'halogen': 'Halogen bond: a Cl/Br/I on the molecule accepting '
               'from a donor on the amino acid.',
    'metal': 'Metal coordination: a metal ion bound by two or '
             'more donor atoms.',
}

# Context-label strings restating the current interaction mode's meaning
# under the radios. Source: setup_window.py:418-425, verbatim (verified
# against generator.derive_required, 09-RESEARCH-help-ui.md SS4).
MODE_CONTEXT = {
    'exclusive': 'The game accepts ANY of the checked interactions',
    'block_exclusive': 'The player must form EXACTLY the checked '
                       'interactions',
    'unset': 'The game randomizes the required set from the '
             'checked types (hydrophobic excluded from random '
             'picks).',
}


# ---------------------------------------------------------------------------
# New canonical gesture hint (consumed by wizard_text.py in 09-08)
# ---------------------------------------------------------------------------

# The three shipped gestures, exactly (wizard.py:335-337):
#   cmd.button('left', 'shft', 'dgmv')  -- move in the view plane
#   cmd.button('left', 'ctsh', 'dgmz')  -- change depth
#   cmd.button('right', 'shft', 'dgrt') -- rotate
# ASCII-only (overlay-bound).
SELECTED_GESTURE_HINT = ('Shift+left-drag moves it; shift+right-drag '
                         'rotates it; ctrl+shift+left-drag changes '
                         'its depth.')


# ---------------------------------------------------------------------------
# The 7-section builder
# ---------------------------------------------------------------------------

def _buttons_section():
    """The Setup-button bullets plus the destructive-consequence notes.

    Per-button wordings reuse the live tooltips (setup_window.py:208-
    227). The destructive bullets each cite the recorded decision / the
    status_text builder that is their source. The Cleanup line follows
    the 09-01 Decision A branch (a-add: a confirmation is asked).
    """
    return [
        # Per-button tooltip wordings (setup_window.py:208-227).
        'Reset: Restore the default settings.',
        'Randomize: Randomize the setup parameters.',
        'Save Setup: Save the game setup parameters to a file.',
        'Load Setup: Load the setup parameters from a file.',
        'Generate and export: Generate all levels and save the '
        'initial game state to a file for sharing or later loading.',
        'Cleanup model: Remove the game-generated objects from the '
        'scene.',
        'Start: Start the game with the current setup.',
        # Destructive / lifecycle consequences.
        # (09-01 Decision A = a-add; the a-accept branch is DEAD.)
        'Cleanup model removes every game-generated object from the '
        'scene, after asking for confirmation.',
        # Done semantics (quick-004, 2026-11-16 [HUMAN]-lite default):
        # abandon-stop, no record, no endgame screen (status_text.py:
        # 309-317; game_window.py:156-170). Never promise a summary.
        'Done closes the board: it stops the running game without a '
        'record and without the endgame screen. (Done is not Give '
        'Up.)',
        # Skip/Give Up carry Yes/No warnings (status_text.py:196-201).
        'Skip Molecule and Give Up both ask for confirmation before '
        'acting.',
        # Restart: no confirmation (06-08 D9; game_window.py:280-283).
        'Restart immediately replaces the running game with a fresh '
        'replay of its initial state; there is no confirmation.',
        # Import: no confirmation (07-07 RD2; game_window.py:1084-
        # 1087).
        'Import replaces a running game exactly like Start does; '
        'there is no confirmation.',
        # Reset to Grid: orientations kept (status_text.py:298).
        'Reset puts all amino acids back at their grid positions; '
        'orientations are kept.',
        # Hint: carbon recolor only (game_window.py:233-236).
        'Hint highlights (recolors) the amino acids that could still '
        'form a required interaction.',
    ]


def help_sections():
    """The canonical help content as ``[(title, [line, ...]), ...]``.

    Seven sections in fixed order. Every line is a plain-text (non-HTML)
    sentence whose source is cited at the point of use. Returns a NEW
    list on every call (callers may format it freely).
    """
    sections = []

    # 1. How to play -- selection, drag, Toward, Confirm, level flow.
    sections.append(('How to play', [
        # wizard_text.py:61 (selection) + the highlight feedback.
        'Click an amino acid to select it. The selected amino acid is '
        'highlighted.',
        # wizard.py:335-337 (the shipped drag map).
        'Drag the selected amino acid into place: shift+left-drag '
        'moves it in the view plane, ctrl+shift+left-drag changes its '
        'depth, and shift+right-drag rotates it.',
        # wizard_core.py:70 TOWARD_STEP=2.5; wizard_text.py:49-51.
        'The Toward ligand button nudges the selected amino acid 2.5 A '
        'toward the ligand.',
        # game_window.py:245-248 tooltip + CONFIRM_PASS_RULE.
        'Press Confirm to attempt the current molecule; the game '
        'advances only when all required interactions are formed.',
        # status_text.py:155-157, :398-423 (level/molecule flow).
        'Each level holds several small molecules; after each scored '
        'molecule the game moves to the next one, and finishing the '
        'last level wins the game.',
    ]))

    # 2. Interaction types -- one line per type, canonical enum order.
    sections.append(('Interaction types', [
        '%s: %s' % (INTERACTION_LABELS[t], INTERACTION_TIPS[t])
        for t in INTERACTION_TYPES
    ]))

    # 3. Scoring and Confirm -- binary scoring + retry semantics.
    sections.append(('Scoring and Confirm', [
        # game_state.py:13-15 (binary per interaction).
        'Each required interaction is either formed or not; extra '
        'copies of the same interaction never inflate the score.',
        # game_state.py:152 (CONFIRM_PASS_RULE = 'all').
        "Confirm passes only when ALL of the current molecule's "
        'required interactions are formed.',
        # status_text.py:254-261 (failed Confirm is not recorded).
        'A failed Confirm records nothing: pose the missing '
        'interactions and Confirm again as often as you like.',
    ]))

    # 4. Interaction modes -- the three mode strings, live-restated.
    sections.append(('Interaction modes', [
        MODE_CONTEXT['exclusive'],
        MODE_CONTEXT['block_exclusive'],
        MODE_CONTEXT['unset'],
        'The mode radios in the Setup tab restate these meanings live.',
    ]))

    # 5. Buttons -- Setup buttons + destructive consequences.
    sections.append(('Buttons', _buttons_section()))

    # 6. Saving and loading -- game, checkpoint, setup, uploads.
    sections.append(('Saving and loading', [
        # checkpoint.py:19-24; game_window.py:1123-1134.
        'Save (Game status tab) writes one .aamz checkpoint file '
        'holding the PyMOL session and the game state; Import resumes '
        'it exactly as saved, timer included.',
        # setup_window.py:940-941; game_file.py.
        'Generate and export writes a shareable .aamatch.json game '
        'file; Import starts it fresh.',
        # setup_window.py:738-772.
        'Save Setup / Load Setup move your form settings as '
        '.aam.setup.json files.',
        # setup_window.py:175-179, :835-842.
        'Uploads are session-only: they are never written into setup '
        'files, and a new upload replaces the previous one.',
    ]))

    # 7. Tips -- the recorded O1 lesson, Hint on misses, difficulty.
    sections.append(('Tips', [
        # The recorded phase_9_help_recommendation
        # (.planning/debug/saltbridge-hbond-interplay.md:238); numbers
        # = the approved H-bond thresholds (docs/
        # DETECTION_THRESHOLDS.md row 1: 4.0 A / >= 140 deg).
        'Salt bridge and hydrogen bond are scored independently. A '
        '5.5 A charge-group-center salt contact alone does not make a '
        'hydrogen bond: for both scores on one contact, place an '
        'actual polar donor hydrogen within 4.0 A of an acceptor '
        'heavy atom on the other molecule and align the '
        'donor-hydrogen...acceptor angle at the hydrogen to at least '
        '140 deg. Rotate the amino acid to aim a specific polar '
        'hydrogen.',
        # status_text.py:254-261 (Formed/Missing), game_window.py:233-
        # 236 (Hint).
        'A failed Confirm lists Formed and Missing interactions - use '
        'Hint to see which amino acids could still complete the '
        'missing ones.',
        # generator.py:70-86 (difficulty axes).
        'Levels grow harder as the game goes on: bigger grids and '
        'more required interactions per level.',
    ]))

    return sections


# ---------------------------------------------------------------------------
# HTML fragment builder (Qt-only consumer)
# ---------------------------------------------------------------------------

def _esc(text):
    """Minimal HTML-escape for authored help lines.

    '&' is replaced FIRST so the entity ampersands are never
    double-escaped. No authored line currently contains '&'; the helper
    exists so a future edit cannot break the QTextEdit render.
    """
    out = str(text)
    out = out.replace('&', '&amp;')
    out = out.replace('<', '&lt;')
    out = out.replace('>', '&gt;')
    return out


def help_html():
    """The help content as ONE rich-text fragment (no html/body wrapper).

    QTextEdit renders FRAGMENTS, not documents (the bioCHEMeleon v1
    law): emit ``<h2>`` + a ``<ul>`` of escaped ``<li>`` lines per
    section, joined with newlines, and never wrap in <html>/<body>.
    """
    parts = []
    for (title, lines) in help_sections():
        parts.append('<h2>%s</h2>' % _esc(title))
        parts.append('<ul>')
        for line in lines:
            parts.append('<li>%s</li>' % _esc(line))
        parts.append('</ul>')
    return '\n'.join(parts)
