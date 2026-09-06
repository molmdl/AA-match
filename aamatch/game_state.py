"""Pure scoring + runtime game state (SCORE-01, plan 02-10).

Layer: PURE (stdlib + pure aamatch modules only; gated by
tests/test_purity.py). No PyMOL/Qt/numpy/file IO anywhere in this module.

SCORE-01 semantics (frozen decision: "Score = fraction of required
interactions formed, binary per interaction; skip stores partial score"):

- ``results`` is the list of CANONICAL detector records (02-06/02-07):
  score consumes ONLY ``r['type']`` and is type-agnostic over the rest of
  the record shape. Scoring must read the SAME records the debrief will
  show (SCORE-02) — one source, no drift.
- Binary per interaction: a required item counts as formed IFF >= 1
  detector record of that type exists. Record COUNTS never inflate the
  score — three h_bond records form the h_bond item exactly once.
- ``mode == 'any'`` (exclusive levels): binary. >= 1 record of ANY type
  -> 1.0, zero records -> 0.0. Empty items is the exclusive-mode
  representation and is legal ONLY here. OQ-1 scoping note: the
  formed-type check is over the records the detector PRODUCED, which the
  detector only enumerates for allowed/cross-side interactions — the
  allowed_interactions scoping lives in the detector's INPUT, never in
  score.
- ``mode == 'list'``: len(formed items) / len(items). An items list MUST
  be non-empty in list mode (refusal below).

Records missing 'type', records whose 'type' is outside
``setup_state.INTERACTION_TYPES`` (the ONE enum home), non-dict records,
and unknown modes raise ValueError — never silently mis-score.

GameState is the minimal in-memory runtime container the engine ops
mutate: level/molecule position, per-molecule formed types, running
score, skip/give-up counters, and a timer anchor. PLAIN DATA ONLY — the
QTimer/rendering side of timing is a later Qt phase; this module merely
stores the anchor float (``start_timer(now)``, caller supplies
``time.time()`` or accepts the default wall-clock read).
"""

import time

from .setup_state import INTERACTION_TYPES

_CANONICAL_POSITION = dict((t, i) for i, t in enumerate(INTERACTION_TYPES))


def _validate_records(results):
    """Fail-closed contract check; returns the set of record types."""
    types = set()
    for r in results:
        if not isinstance(r, dict) or 'type' not in r:
            raise ValueError(
                "score: every detector record must be a dict carrying "
                "'type' (canonical 02-06/02-07 record contract)")
        if r['type'] not in _CANONICAL_POSITION:
            raise ValueError(
                "score: record 'type' %r is not in INTERACTION_TYPES "
                "(the detector never records unclassified interactions)"
                % (r['type'],))
        types.add(r['type'])
    return types


def score(required, results):
    """SCORE-01 fraction of the required interactions formed.

    ``required`` = resolved level-spec dict ``{'mode': 'any'|'list',
    'items': [{'type': ..., 'count': ...}]}`` (generator.py shape).
    ``results`` = list of canonical detector records. Returns a float in
    [0.0, 1.0] — module docstring carries the full semantics and the
    OQ-1 'any'-mode scoping note.
    """
    record_types = _validate_records(results)
    mode = required.get('mode')
    items = required.get('items') or ()
    if mode == 'any':
        return 1.0 if record_types else 0.0
    if mode == 'list':
        if not items:
            raise ValueError(
                "score: 'list' mode requires a non-empty items list "
                "(empty items is the exclusive 'any'-mode representation)")
        formed = sum(1 for item in items if item['type'] in record_types)
        return formed / float(len(items))
    raise ValueError(
        "score: unknown required mode %r (expected one of any, list)"
        % (mode,))
