"""Pure wizard panel/prompt/result text builders (plan 03-02, Phase 3).

Layer: PURE -- registered in tests/test_purity.py PURE_MODULES (Gate A
scans EVERY scope, module level and function bodies). The ONLY import
here is the movement constants from ``.wizard_core`` -- the single home
for gameplay constants, never re-transcribed. NO pymol/Qt/numpy: these
builders are dumb functions of the plain-data state dict the cmd-tier
GameWizard (plan 03-03) assembles -- plain data in, plain data out.

Binding facts this module encodes
(03-RESEARCH-wizard-interaction.md section 3):

- Panel entries are ALWAYS 3-element lists ``[kind, text, code]``;
  kinds 0=blank / 1=text / 2=button. The C parser requires
  PyList_Size > 2 per entry -- a 2-element entry renders as a BLANK
  line (Wizard.cpp:239-246). Panel text is capped at 255 chars per
  line (WordType[256], Word.h:24,26): clip, never crash. Prompt text
  (``get_prompt``) is a list of strings with no cap -- clipped anyway
  so panel and prompt can share result lines.
- Button codes are PParse'd at CLICK time (Wizard.cpp:569-576):
  ``cmd.get_wizard().method(...)`` resolves the live top-of-stack
  instance, so commands dodge the module-identity trap (aamatch vs
  pmg_tk.startup.aamatch -- AGENTS.md gate 5). NO module name may ever
  appear in a panel/prompt code string. Done is the canonical
  ``cmd.set_wizard()``.
- ASCII-only panel/prompt text (PyMOL overlay font safety):
  'deg', never a degree sign.
- Result rendering is TEXT ONLY (PLAY-04 no-helper-visuals): the score
  fraction plus formed/missing interaction TYPE NAMES -- never
  geometry descriptors, coordinates, or atom names. SCORE-01 semantics
  mirror aamatch/game_state.py:score -- 'any' is binary (records of
  any type -> 1.0, else 0.0), 'list' is formed items / items.

Movement labels embed NUDGE_STEP from wizard_core (%g formatting): if
the constant changes, the 'A per press' text follows automatically.
"""

from .wizard_core import NUDGE_STEP, ROTATE_BUTTON_STEP_DEG

# Module-level constant, built from the single-home constants above.
_MOVEMENT_BUTTONS = (
    ('Left',  'cmd.get_wizard().nudge_cam(-1, 0, 0)'),
    ('Right', 'cmd.get_wizard().nudge_cam(1, 0, 0)'),
    ('Up',    'cmd.get_wizard().nudge_cam(0, 1, 0)'),
    ('Down',  'cmd.get_wizard().nudge_cam(0, -1, 0)'),
    ('In',    'cmd.get_wizard().nudge_cam(0, 0, -1)'),
    ('Out',   'cmd.get_wizard().nudge_cam(0, 0, 1)'),
    ('Toward ligand', 'cmd.get_wizard().step_to_ligand()'),
    ('Rotate %d deg' % int(ROTATE_BUTTON_STEP_DEG),
     'cmd.get_wizard().rotate_view(%d)' % int(ROTATE_BUTTON_STEP_DEG)),
)

_ACTION_BUTTONS = (
    ('Confirm',      'cmd.get_wizard().confirm_molecule()'),
    ('Reset to Grid', 'cmd.get_wizard().reset_grid()'),
)

_DONE_LABEL = 'Done'
_DONE_CODE = 'cmd.set_wizard()'

_CLICK_INSTRUCTION = 'Click an amino acid to select it.'


def _clip(text, limit=255):
    """Clip ``text`` to ``limit`` chars (the WordType[256] panel cap).

    Clipping is how overflow is handled everywhere in this module --
    never a crash on a long user-facing string (e.g. a pathological
    error message). Non-string input is coerced.
    """
    out = str(text)
    if len(out) > limit:
        out = out[:limit]
    return out


def required_summary(required):
    """One-line summary of the required interactions.

    - ``{'mode': 'list', 'items': [...]}`` ->
      'h_bond x1, pi_stacking x2' (items rendered in the order GIVEN --
      the level-spec payload already carries canonical order, so this
      builder never re-sorts).
    - ``{'mode': 'any', 'items': []}`` -> 'any interaction'.

    Fail-closed like game_state.score: unknown modes and a list mode
    with a missing/empty items list raise ValueError naming the cause.
    """
    mode = required.get('mode') if isinstance(required, dict) else None
    if mode == 'any':
        return 'any interaction'
    if mode == 'list':
        items = required.get('items')
        if not items:
            raise ValueError(
                "required_summary: 'list' mode requires a non-empty "
                "items list (empty items is the 'any'-mode "
                "representation)")
        return ', '.join('%s x%s' % (item.get('type'), item.get('count'))
                         for item in items)
    raise ValueError(
        'required_summary: unknown required mode %r (expected one of '
        'any, list)' % (mode,))


def result_lines(score, formed, required):
    """TEXT-ONLY detection-result lines (PLAY-04, PLAY-03).

    Consumes the plain data engine.confirm returns: the score float,
    the canonical-order formed type names, and the required payload.
    SCORE-01 semantics mirror game_state.score:

    - 'list' mode: first line 'N/M required interactions formed (score
      x.xx)' (N = required items whose type is formed; counts never
      inflate, one item per type presence), then 'Formed: ...' (or the
      PINNED 'Formed: (none)' shape), then 'Missing: ...' listing the
      required types NOT formed (item order, deduped) -- omitted when
      nothing is missing.
    - 'any' mode: binary. Formed types -> 'Interaction formed (score
      1.00)' + 'Formed: ...'; nothing -> the PINNED single line
      'Nothing formed (score 0.00)'. Never a 'Missing:' line (the 'any'
      required set is empty by representation).
    - Score renders with exactly 2 decimals.

    No geometry descriptors, no coordinates, no atom names beyond type
    names -- the debrief is text-only by decision (PLAY-04). Unknown
    modes and list mode with empty items raise ValueError naming the
    cause (same fail-closed contract as game_state.score).
    """
    value = float(score)
    mode = required.get('mode') if isinstance(required, dict) else None
    formed_list = [str(t) for t in formed]
    lines = []
    if mode == 'list':
        items = required['items']  # key_link: plain data engine returns
        if not items:
            raise ValueError(
                "result_lines: 'list' mode requires a non-empty items "
                "list (empty items is the 'any'-mode representation)")
        formed_set = set(formed_list)
        n_formed = sum(1 for item in items if item['type'] in formed_set)
        lines.append('%d/%d required interactions formed (score %.2f)'
                     % (n_formed, len(items), value))
        if formed_list:
            lines.append('Formed: ' + ', '.join(formed_list))
        else:
            lines.append('Formed: (none)')
        missing = []
        seen = set()
        for item in items:
            itype = item['type']
            if itype not in formed_set and itype not in seen:
                seen.add(itype)
                missing.append(itype)
        if missing:
            lines.append('Missing: ' + ', '.join(missing))
    elif mode == 'any':
        if formed_list:
            lines.append('Interaction formed (score %.2f)' % value)
            lines.append('Formed: ' + ', '.join(formed_list))
        else:
            lines.append('Nothing formed (score %.2f)' % value)
    else:
        raise ValueError(
            'result_lines: unknown required mode %r (expected one of '
            'any, list)' % (mode,))
    return [_clip(line) for line in lines]


def panel_entries(state):
    """The full wizard panel as a list of 3-element [kind, text, code]
    entries (Wizard.cpp contract -- see module docstring).

    Documented build order: header (molecule id + pos/total), required
    summary, [result lines when state['result'] is set, an 'ERROR:'
    text line when state['error'] is set], blank, movement header
    (embeds NUDGE_STEP), the six nudge buttons + 'Toward ligand' +
    'Rotate 90 deg', blank, 'Confirm', 'Reset to Grid', 'Done'
    (canonical cmd.set_wizard()).

    ``state`` is plain data; this builder never imports cmd and never
    touches PyMOL state (the GameWizard assembles the dict it will hand
    to this function).
    """
    entries = []
    entries.append([1, _clip('Molecule %s (%s/%s)'
                             % (state.get('molecule_id'),
                                state.get('molecule_pos'),
                                state.get('molecule_total'))), ''])
    entries.append([1, _clip('Required: '
                             + required_summary(state.get('required'))),
                    ''])
    result = state.get('result')
    if result:
        for line in result_lines(result['score'], result['formed'],
                                 result['required']):
            entries.append([1, line, ''])
    error = state.get('error')
    if error:
        entries.append([1, _clip('ERROR: %s' % error), ''])
    entries.append([0, '', ''])
    entries.append([1, _clip('Move (%g A per press):' % NUDGE_STEP), ''])
    for label, code in _MOVEMENT_BUTTONS:
        entries.append([2, label, code])
    entries.append([0, '', ''])
    for label, code in _ACTION_BUTTONS:
        entries.append([2, label, code])
    entries.append([2, _DONE_LABEL, _DONE_CODE])
    return entries


def prompt_lines(state):
    """The always-visible prompt as a LIST of plain strings (never
    None; get_prompt returns list-of-strings).

    Order: the state-machine line first (click instruction when nothing
    is selected, else the Move/rotate guidance naming slot id + object),
    then the result lines VERBATIM when a result is present, then an
    'ERROR'-prefixed line LAST (appended after status -- the
    measurement.py:262-263 shape). Result lines are produced by
    result_lines, so prompt and panel show identical text.
    """
    lines = []
    lines.append(_clip(_status_line(state.get('selected'))))
    result = state.get('result')
    if result:
        lines.extend(result_lines(result['score'], result['formed'],
                                  result['required']))
    error = state.get('error')
    if error:
        lines.append(_clip('ERROR: %s' % error))
    return lines


def _status_line(selected):
    """First prompt line: selection status or the click instruction."""
    if selected:
        return ('Selected: slot %s (%s). Move/rotate it, then Confirm.'
                % (selected.get('slot_id'), selected.get('object')))
    return _CLICK_INSTRUCTION
