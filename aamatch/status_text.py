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
  wording/format is NOT pinned; Phase 6/7 research pins the final text.
"""

from .wizard_text import required_summary

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


def status_events(prev, curr):
    """Diff two get_status() plain-data dicts; return the log lines to
    append (list of str), IN ORDER level/molecule, then selection, then
    error.

    - prev None -> [] (first observation SILENT; the start sequence
      already logged the level line -- pitfall 4).
    - Fingerprint keys exactly: molecule_id, molecule_pos,
      molecule_total, level_pos, selected['slot_id'], error. Anything
      else is ignored (extra keys tolerated via .get). 'result' is
      deliberately NOT fingerprinted in Phase 5 -- score lines are a
      Phase-6 reserve (pitfall 7).
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
