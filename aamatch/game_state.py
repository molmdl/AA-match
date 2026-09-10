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


def records_for_molecule(records, slot_objects, ligand_object):
    """Keep only the records formed OVER one molecule (03-06
    cross-molecule scoring guard).

    The detector runs on a COMBINED ligand feature layer (all ligand
    objects in the scene join one 'lig' feature set); without scoping,
    a required-type record formed over the WRONG molecule's ligand
    would count as formed for the scored molecule. A record belongs to
    the molecule iff its AA partner is one of the molecule's slot
    objects AND its ligand partner is that molecule's ligand object.

    ``records``     canonical detector records (each must carry 'aa' /
                    'lig' dicts with an 'object' name -- fail-closed on
                    any other shape, never silently mis-scope).
    ``slot_objects``    iterable of the molecule's AA object names.
    ``ligand_object``   the molecule's ONE ligand object name.

    Returns a NEW list (input order preserved); the caller's list is
    untouched. Pure: plain data in, plain data out.
    """
    allowed = set(slot_objects)
    out = []
    for r in records:
        aa = r.get('aa') if isinstance(r, dict) else None
        lig = r.get('lig') if isinstance(r, dict) else None
        if not isinstance(aa, dict) or not isinstance(lig, dict) \
                or 'object' not in aa or 'object' not in lig:
            raise ValueError(
                "records_for_molecule: every record must carry 'aa' and "
                "'lig' dicts with an 'object' name (canonical detector "
                "record contract)")
        if aa['object'] in allowed and lig['object'] == ligand_object:
            out.append(r)
    return out


def _formed_types(required, record_types):
    """The set of formed type names, deduped by type (counts never
    inflate, same rule as score).

     - 'list' mode: the required ITEM types that have >= 1 record.
     - 'any' mode: every type the detector produced — its input already
       scopes to allowed/cross-side interactions (OQ-1), so mirroring
       the record types is the formed set the debrief will show.
    """
    if required.get('mode') == 'list':
        formed = set(item['type'] for item in required.get('items') or ()
                     if item['type'] in record_types)
    else:
        formed = set(record_types)
    return sorted(formed, key=_CANONICAL_POSITION.get)


class GameState:
    """Minimal in-memory runtime state the engine ops mutate.

    PLAIN DATA ONLY — ints, floats, strings, lists, dicts; no PyMOL/Qt,
    no file IO. Fields:

    - ``current_level_index`` / ``current_molecule_index`` — position in
      the baked level structure (advance_* transitions below).
    - ``molecule_scores`` — running per-molecule scores (list of floats);
      ``total_score`` is their sum. Skip stores the partial score as a
      regular entry (SCORE-01: "skip stores partial score").
    - ``skip_count`` / ``giveup_count`` — plain counters the engine
      increments.
    - ``timer_anchor`` — float wall-clock anchor set via
      ``start_timer(now)`` (``None`` until first set). Rendering/timeout
      is a later phase's QTimer; this module only stores the anchor.
    - ``formed_types_per_molecule`` — dict keyed
      ``'L{level}M{molecule}'`` -> formed type names in canonical
      INTERACTION_TYPES order, written by ``record_molecule_result``
      which stores the score and the formed types TOGETHER (one record
      call per molecule — the two views can never drift apart).

    ``to_dict``/``from_dict`` round-trip ALL fields losslessly as a plain
    JSON-able dict (engine/debug surface; the formal sidecar container
    format is Phase 7's — but this surface must already be lossless).
    """

    def __init__(self):
        self.current_level_index = 0
        self.current_molecule_index = 0
        self.molecule_scores = []
        self.skip_count = 0
        self.giveup_count = 0
        self.timer_anchor = None
        self.formed_types_per_molecule = {}

    @staticmethod
    def molecule_key(level, molecule):
        """Container key for ONE molecule's bookkeeping: 'L0M2' etc."""
        return 'L%dM%d' % (level, molecule)

    @property
    def total_score(self):
        """Running total: sum of the per-molecule scores recorded so far."""
        return sum(self.molecule_scores)

    def start_timer(self, now=None):
        """Anchor the per-molecule timer at `now` (defaults to the wall
        clock). Stores a float; the countdown/rendering half is a later
        phase's QTimer, never this module's concern."""
        self.timer_anchor = float(time.time() if now is None else now)

    def advance_molecule(self):
        """Move to the next molecule within the current level."""
        self.current_molecule_index += 1

    def advance_level(self):
        """Move to the next level; the molecule position restarts at 0."""
        self.current_level_index += 1
        self.current_molecule_index = 0

    def record_molecule_result(self, level, molecule, required, results):
        """Score `results` against `required` and store BOTH the score and
        the formed types for molecule (level, molecule) in one call.

        Returns the SCORE-01 fraction. Raises ValueError on the same
        contract violations as `score` (fail-closed — a malformed record
        set must never be persisted as a believable result).
        """
        value = score(required, results)
        record_types = _validate_records(results)
        self.molecule_scores.append(value)
        self.formed_types_per_molecule[self.molecule_key(level, molecule)] \
            = _formed_types(required, record_types)
        return value

    def to_dict(self):
        """Plain JSON-able snapshot of ALL fields (lossless)."""
        return {
            'current_level_index': self.current_level_index,
            'current_molecule_index': self.current_molecule_index,
            'molecule_scores': list(self.molecule_scores),
            'skip_count': self.skip_count,
            'giveup_count': self.giveup_count,
            'timer_anchor': self.timer_anchor,
            'formed_types_per_molecule':
                dict((k, list(v))
                     for k, v in self.formed_types_per_molecule.items()),
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild a GameState from to_dict output (lossless inverse)."""
        gs = cls()
        gs.current_level_index = data['current_level_index']
        gs.current_molecule_index = data['current_molecule_index']
        gs.molecule_scores = list(data['molecule_scores'])
        gs.skip_count = data['skip_count']
        gs.giveup_count = data['giveup_count']
        gs.timer_anchor = data['timer_anchor']
        gs.formed_types_per_molecule = dict(
            (k, list(v))
            for k, v in data['formed_types_per_molecule'].items())
        return gs
