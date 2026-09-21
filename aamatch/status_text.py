"""Pure status-tab text builders (plan 05-01, Phase 5).

Layer: PURE -- registered in tests/test_purity.py PURE_MODULES (Gate A
scans EVERY scope, module level and function bodies). The ONLY import
here is ``required_summary`` from ``.wizard_text`` -- the single items
renderer, reused verbatim, never duplicated (single-home law). ZERO
stdlib imports; python3.6 floor (%-formatting only, no dataclasses).
NO pymol/Qt/numpy: these builders are dumb functions of the plain-data
get_status() dict the cmd-tier GameWizard (plan 05-07) exposes -- plain
data in, plain data out.

This module is the GAME STATUS TAB's pure text surface, distinct from
wizard_text (the wizard's overlay surface) -- the per-surface
pure-module precedent is setup_form.py (04-02: the setup window's pure
glue). The Qt tier (game_window.py, a sibling plan) stays a dumb
renderer: every string it can show is pinned here in WSL before any Qt
wiring exists (05-RESEARCH-status-surface.md dont_hand_roll).

Binding facts this module encodes (05-RESEARCH-status-surface.md):

- required_display: the required-interactions LABEL text. The
  authoritative count is len(required['items']) in list mode and 1 in
  'any' mode -- difficulty.n_required_types is the unset-draw CAP, never
  the display source (research Q4, pitfall 5).
- status_events(prev, curr): the 1 Hz poll-diff. First observation is
  SILENT (prev None -> []) because the start sequence owns the first
  level line (pitfall 4). Emits, in order: level/molecule line,
  selection line, error line. Fingerprint keys exactly: molecule_id,
  molecule_pos, molecule_total, level_pos, selected['slot_id'], error.
  Sticky dedupe: an UNCHANGED error string is never re-logged (pitfall
  3); same-slot re-click, deselect (to None), and cleared error are
  silent. 'result' is NEVER fingerprinted in Phase 5 -- score lines are
  reserved for Phase 6 (pitfall 7). Unknown/extra keys are tolerated
  via .get (the wizard_text consumer precedent).
- EVENT_KINDS: the documented event vocabulary -- the 7 Phase-5 emitted
  kinds + 6 reserved Phase-6 kinds + 2 reserved Phase-7 kinds. Reserved
  wording/format is NOT pinned in the dict (its value notes stay
  BYTE-UNCHANGED); the Phase-6 wording is pinned by the builders below.
- Phase 6 (plan 06-02): the SIX reserved kinds are now real builders
  with FINAL wording (D10). The poll-diff fingerprints ONE new key,
  'last_event' (whole-dict equality; the wizard's seq counter makes
  identical consecutive events distinct): when curr['last_event'] is
  not None and differs from prev's, the event's lines are dispatched
  through _EVENT_BUILDERS and prepended BEFORE the level/molecule,
  selection, and error lines. 'result' STAYS unfingerprinted (pitfall
  7). game_restarted is EXCLUDED from the poll table -- the tab handler
  logs it AFTER the countdown arms (the countdown clears the box; the
  marker would die with the popped wizard anyway). The scored debrief
  IS wizard_text.result_lines, imported and reused verbatim (the
  single-home law -- zero drift risk). SKIP_WARNING_*/GIVEUP_WARNING_*
  are the confirmation-box wording (endgame-ui sec 3.3); endgame_lines
    renders the SCORE-07 block (headline, per-level scores, total, time,
    sizes, counters) identically for the info box and the modal;
    format_mss is the pure M:SS timer formatter.
- Phase 7 (plan 07-03): the three handler-logged line builders
  (game_saved_line, game_imported_line, game_resumed_line) land in the
  game_restarted_line shape -- no event argument, EXCLUDED from
  _EVENT_BUILDERS (Save/Import/Resume are tab-side operations; the
  poll's fingerprint set has no key for them). EVENT_KINDS stays
  EXACTLY 15 and the game_saved/game_imported reserved notes stay
  BYTE-UNCHANGED (the Phase-6 precedent); there is no reserved resume
  kind -- the handler-logged pattern needs none.
"""

from .wizard_text import required_summary, result_lines

# Fingerprint keys for the molecule/level half of the poll-diff
# (fingerprint set pinned by tests/test_status_text.py).
_MOLECULE_KEYS = ('molecule_id', 'molecule_pos', 'molecule_total',
                  'level_pos')

# The documented event vocabulary (research's event inventory; the KEY
# SET is pinned by tests). kind name -> short role note.
EVENT_KINDS = {
    'game_start': "'Get ready...' start line, logged by the tab's "
                  "start sequence (Phase 5 emitted)",
    'countdown': "'3'/'2'/'1'/'GO!' ticks, logged by the tab's "
                 "countdown timer (Phase 5 emitted)",
    'level_molecule': "'Level %d, molecule %d of %d.' status line -- "
                      "logged at GO and by the poll diff on "
                      "molecule/level change (Phase 5 emitted)",
    'required_display': "the required-interactions reference label "
                        "(rendered by required_display; a label, not a "
                        "log line; Phase 5 emitted)",
    'selection': "'Selected: slot %s (%s).' line from the poll diff on "
                 "slot change (Phase 5 emitted)",
    'error': "'ERROR: %s' line from the poll diff on a NEW error "
             "string -- sticky dedupe applies (Phase 5 emitted)",
    'hint': "'Hint: %d eligible amino acid(s) highlighted.' line, "
            "logged by the tab's Hint handler (Phase 5 emitted)",
    'molecule_scored': "per-molecule result line -- reserved for "
                       "Phase 6",
    'molecule_skipped': "skip line -- reserved for Phase 6",
    'gave_up': "give-up line -- reserved for Phase 6",
    'level_advanced': "level-advance line -- reserved for Phase 6",
    'game_reset': "grid-reset line -- reserved for Phase 6",
    'game_restarted': "restart line -- reserved for Phase 6",
    'game_saved': "save line -- reserved for Phase 7",
    'game_imported': "import line -- reserved for Phase 7",
}


def required_display(required):
    """The required-interactions label text (research Q4 pinned strings).

    - ``{'mode': 'any', 'items': []}`` -> 'Required: any 1 interaction'
      (binary scoring: any single allowed-type record completes the
      molecule).
    - ``{'mode': 'list', 'items': [...]}`` -> 'Required: %d
      interaction%s: %s' where the count is len(items) -- NEVER
      difficulty.n_required_types (pitfall 5) -- the plural suffix is
      '' for 1 else 's', and the summary is wizard_text
      .required_summary reused verbatim (single-home law).

    Fail-closed identically to required_summary, by delegation: list
    mode with empty items (empty is the 'any'-mode representation only)
    and unknown modes / non-dict input raise ValueError naming the
    cause.
    """
    mode = required.get('mode') if isinstance(required, dict) else None
    if mode == 'any':
        return 'Required: any 1 interaction'
    if mode == 'list':
        summary = required_summary(required)
        count = len(required['items'])
        return ('Required: %d interaction%s: %s'
                % (count, '' if count == 1 else 's', summary))
    # Delegation supplies the fail-closed wording (it raises before
    # returning: unknown modes and non-dict input).
    return required_summary(required)


def level_molecule_line(state):
    """The level/molecule status line: 'Level %d, molecule %d of %d.'

    Fail-closed (house style): a missing level_pos, molecule_pos, or
    molecule_total key raises ValueError naming the missing key.
    """
    for key in ('level_pos', 'molecule_pos', 'molecule_total'):
        if state.get(key) is None:
            raise ValueError(
                'level_molecule_line: missing %r key' % key)
    return ('Level %s, molecule %s of %s.'
            % (state['level_pos'], state['molecule_pos'],
               state['molecule_total']))


def selected_line(selected):
    """The selection event line: 'Selected: slot %s (%s).'

    The panel's first prompt line minus its imperative tail
    (wizard_text prompt minus 'Move/rotate it, then Confirm.'). Returns
    None for a None/empty selected -- a DESELECT logs nothing: only the
    pinned slot-selection string exists; the panel reflects deselects
    (planner decision adopted from the research's silence).
    """
    if not selected:
        return None
    return ('Selected: slot %s (%s).'
            % (selected.get('slot_id'), selected.get('object')))


def error_line(msg):
    """The error event line: 'ERROR: %s' (same prefix as panel/prompt)."""
    return 'ERROR: %s' % msg


def format_mss(seconds):
    """The pure M:SS timer formatter: 75 -> '1:15', 3661 -> '61:01'.

    int() coercion of the input (a float truncates). Negative seconds
    are refused naming the cause -- the tick's max(0.0, ...) upstream
    keeps the live path from ever reaching here with a negative.
    """
    if seconds < 0:
        raise ValueError('format_mss: negative seconds %r' % (seconds,))
    total = int(seconds)
    return '%d:%02d' % (total // 60, total % 60)


# The confirmation-warning wording (endgame-ui sec 3.3, NO-number
# variant chosen so the wrapper never runs a pre-modal detection pass).
# The Qt tier shows ONLY these strings.
SKIP_WARNING_TITLE = 'Skip this molecule?'
SKIP_WARNING_TEXT = ('Skip this molecule and move to the next one? '
                     'The score formed so far is kept.')
GIVEUP_WARNING_TITLE = 'Give up?'
GIVEUP_WARNING_TEXT = ('Give up and end the game now? The game ends at '
                       'this stage and the endgame summary is shown.')


def _require_kind(event, kind, name):
    """Fail-closed kind validation for an event builder: the event must
    be a dict whose 'kind' equals this builder's own kind."""
    actual = event.get('kind') if isinstance(event, dict) else None
    if actual != kind:
        raise ValueError(
            '%s: expected an event of kind %r (got %r)'
            % (name, kind, actual))


def _require_keys(event, keys, name):
    """Fail-closed payload validation: each key must be present and not
    None; a missing/explicitly-None key raises ValueError naming it."""
    for key in keys:
        if not isinstance(event, dict) or event.get(key) is None:
            raise ValueError(
                '%s: missing %r key in the event payload' % (name, key))


def molecule_scored_lines(event):
    """The scored event block (SCORE-02): the header line plus the
    wizard_text.result_lines debrief appended VERBATIM -- one wording
    home, never duplicated.

    Requires payload keys score, total, molecule_pos, molecule_total,
    formed, required, extras (the marker payload 06-05 pins).
    """
    _require_kind(event, 'molecule_scored', 'molecule_scored_lines')
    _require_keys(event, ('score', 'total', 'molecule_pos',
                          'molecule_total', 'formed', 'required',
                          'extras'), 'molecule_scored_lines')
    header = ('Molecule %d of %d scored %.2f (total %.2f).'
              % (event['molecule_pos'], event['molecule_total'],
                 event['score'], event['total']))
    return ([header]
            + result_lines(event['score'], event['formed'],
                           event['required'], event['extras']))


def molecule_skipped_line(event):
    """The skip event line (SCORE-05): the partial score formed so far
    is stored, the molecule counts as done."""
    _require_kind(event, 'molecule_skipped', 'molecule_skipped_line')
    _require_keys(event, ('score', 'total', 'molecule_pos',
                          'molecule_total'), 'molecule_skipped_line')
    return ('Skipped molecule %d of %d (partial score %.2f, total %.2f).'
            % (event['molecule_pos'], event['molecule_total'],
               event['score'], event['total']))


def gave_up_line(event):
    """The give-up event line (all positions 1-based)."""
    _require_kind(event, 'gave_up', 'gave_up_line')
    _require_keys(event, ('total', 'molecule_pos', 'molecule_total',
                          'level_pos'), 'gave_up_line')
    return ('Game ended at level %d, molecule %d of %d (total %.2f).'
            % (event['level_pos'], event['molecule_pos'],
               event['molecule_total'], event['total']))


def level_advanced_line(event):
    """The level-advance line. PINNED for vocabulary completeness but
    the ops do NOT emit it -- the poll's position-change line already
    announces the new level (endgame-ui D8)."""
    _require_kind(event, 'level_advanced', 'level_advanced_line')
    _require_keys(event, ('level_pos',), 'level_advanced_line')
    return 'Level %d begins.' % event['level_pos']


def game_reset_line(event):
    """The reset event line (unifies restart-reset D4's orientation
    note with the last_event marker mechanism)."""
    _require_kind(event, 'game_reset', 'game_reset_line')
    return 'Amino acids reset to grid positions (orientations kept).'


def game_restarted_line():
    """The restart line. Handler-logged by the tab AFTER the countdown
    arms (the countdown clears the box; the marker would die with the
    popped wizard anyway), so it takes no event argument and is
    EXCLUDED from _EVENT_BUILDERS below."""
    return 'Game restarted.'


def game_saved_line(path):
    """The save line (Phase 7, SCORE-08). Handler-logged by the Game
    tab's Save wrapper AFTER a successful checkpoint write; takes no
    event argument and is EXCLUDED from _EVENT_BUILDERS (Save is a
    tab-side operation -- the wizard is not the actor; the poll's
    fingerprint set has no key for it). Sketch provenance:
    05-RESEARCH-status-surface.md:290."""
    return 'Game saved to %s.' % path


def game_imported_line(path):
    """The import line (Phase 7, PERSIST-02). Handler-logged by the
    Game tab's Import wrapper AFTER start_countdown arms (the
    countdown's _info_log.clear() would wipe a pre-arm line -- the
    restart D2/D7 law verbatim). Sketch provenance:
    05-RESEARCH-status-surface.md:291."""
    return 'Game imported: %s.' % path


def game_resumed_line(path):
    """The checkpoint-resume line (Phase 7, PERSIST-03). Handler-logged
    by the Game tab after a checkpoint load re-arms the tab (no
    countdown on resume -- the scene and books come back intact).
    Handler-logged like its siblings; EXCLUDED from _EVENT_BUILDERS
    (the reserved EVENT_KINDS set stays 15 -- no new kind)."""
    return 'Game resumed from %s.' % path


# The poll-emitted builder table (05-RESEARCH Q5/06-RESEARCH Q7
# ordering: event lines FIRST). EXACTLY the 5 poll-emitted kinds;
# game_restarted is tab-handler-logged (see game_restarted_line) --
# a marker with that kind, or any unknown kind, fails closed in
# status_events below.
_EVENT_BUILDERS = {
    'molecule_scored': molecule_scored_lines,
    'molecule_skipped': molecule_skipped_line,
    'gave_up': gave_up_line,
    'level_advanced': level_advanced_line,
    'game_reset': game_reset_line,
}


def endgame_lines(summary):
    """The SCORE-07 endgame block as a list of lines -- the info box
    and the modal render this SAME block (lines[0] is ALWAYS the
    headline).

    Consumes the plain summary dict game_state.endgame_summary
    produces (06-01): end_state ('completed'|'gave_up'), level_scores
    (list of float), total, final_time (seconds), levels, molecules,
    molecules_completed, skip_count, giveup_count, ended_level,
    ended_molecule (all positions 1-based).

    The gave-up headline's molecule denominator is the uniform
    per-level molecule count molecules // levels (every level has
    exactly m molecules by construction -- 06-RESEARCH.md Q5).

    Block shape (D1/D2/D3 adopted; scores 2 decimals; time M:SS):
    headline, then one 'Level %d: %.2f' per level, then 'Total score:
    %.2f.', 'Time: %s.', 'Molecules completed: %d of %d. Levels: %d.',
    'Skips: %d. Give-ups: %d.'

    Fail-closed: any missing key raises ValueError naming it; an
    end_state outside {'completed', 'gave_up'} is refused.
    """
    for key in ('end_state', 'level_scores', 'total', 'final_time',
                'levels', 'molecules', 'molecules_completed',
                'skip_count', 'giveup_count', 'ended_level',
                'ended_molecule'):
        if not isinstance(summary, dict) or key not in summary:
            raise ValueError(
                'endgame_lines: missing %r key in the summary'
                % (key,))
    end_state = summary['end_state']
    if end_state == 'completed':
        headline = ('You win! All %d level(s) finished in %s.'
                    % (summary['levels'],
                       format_mss(summary['final_time'])))
    elif end_state == 'gave_up':
        if summary['levels'] < 1:
            raise ValueError(
                'endgame_lines: levels must be >= 1 (got %r)'
                % (summary['levels'],))
        headline = ('Game over -- gave up at level %d, molecule %d of '
                    '%d.'
                    % (summary['ended_level'], summary['ended_molecule'],
                       summary['molecules'] // summary['levels']))
    else:
        raise ValueError(
            "endgame_lines: unknown end_state %r (expected one of "
            "completed, gave_up)" % (end_state,))
    lines = [headline]
    for i, score in enumerate(summary['level_scores']):
        lines.append('Level %d: %.2f' % (i + 1, score))
    lines.append('Total score: %.2f.' % summary['total'])
    lines.append('Time: %s.' % format_mss(summary['final_time']))
    lines.append('Molecules completed: %d of %d. Levels: %d.'
                 % (summary['molecules_completed'],
                    summary['molecules'], summary['levels']))
    lines.append('Skips: %d. Give-ups: %d.'
                 % (summary['skip_count'], summary['giveup_count']))
    return lines


def status_events(prev, curr):
    """Diff two get_status() plain-data dicts; return the log lines to
    append (list of str), IN ORDER event lines, then level/molecule,
    then selection, then error.

    - prev None -> [] (first observation SILENT; the start sequence
      already logged the level line -- pitfall 4).
    - Fingerprint keys exactly: last_event (whole-dict equality), and
      molecule_id, molecule_pos, molecule_total, level_pos,
      selected['slot_id'], error. Anything else is ignored (extra keys
      tolerated via .get). 'result' is deliberately NOT fingerprinted
      -- pitfall 7; the additive last_event marker (D2 event channel)
      is how score/lifecycle events reach the diff.
    - last_event: when curr's marker is not None and differs from
      prev's, the marker's kind is dispatched through _EVENT_BUILDERS
      and those lines are prepended BEFORE the position line (the
      score line describes the completed molecule; the position line
      announces the new one). The wizard's seq counter makes identical
      consecutive events (two Resets) distinct. Unknown kinds raise
      ValueError (fail-closed; closed set -- game_restarted is
      tab-handler-logged, never poll-emitted).
    - Exactly ONE level line per change tick even if several molecule
      fingerprint keys moved.
    - Sticky dedupe (pitfall 3): an UNCHANGED error string is never
      re-logged; a CLEARED error (X -> None) logs nothing; a different
      error string logs the new one.
    - Selection: same-slot re-click is silent; change TO None (deselect)
      is silent (selected_line(None) is None -- skipped).
    """
    if prev is None:
        return []
    lines = []
    prev_event = prev.get('last_event')
    curr_event = curr.get('last_event')
    if curr_event is not None and curr_event != prev_event:
        kind = curr_event.get('kind') if isinstance(curr_event,
                                                    dict) else None
        builder = _EVENT_BUILDERS.get(kind)
        if builder is None:
            raise ValueError(
                'status_events: unknown last_event kind %r (poll-'
                'emitted: molecule_scored, molecule_skipped, gave_up, '
                'level_advanced, game_reset -- game_restarted is '
                'tab-handler-logged, never poll-emitted)' % (kind,))
        event_lines = builder(curr_event)
        if isinstance(event_lines, str):
            event_lines = [event_lines]
        lines.extend(event_lines)
    prev_mol = tuple(prev.get(key) for key in _MOLECULE_KEYS)
    curr_mol = tuple(curr.get(key) for key in _MOLECULE_KEYS)
    if prev_mol != curr_mol:
        lines.append(level_molecule_line(curr))
    prev_selected = prev.get('selected') or {}
    curr_selected = curr.get('selected') or {}
    if prev_selected.get('slot_id') != curr_selected.get('slot_id'):
        line = selected_line(curr.get('selected'))
        if line is not None:
            lines.append(line)
    prev_error = prev.get('error')
    curr_error = curr.get('error')
    if prev_error != curr_error and curr_error is not None:
        lines.append(error_line(curr_error))
    return lines
