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
score, skip/give-up counters, a timer anchor, and (06-01 lifecycle data
layer) the end-state fields, the frozen final time, and the keyed
per-molecule score store. PLAIN DATA ONLY — the QTimer/rendering side
of timing is a later Qt phase; this module merely stores the anchor
float (``start_timer(now)``, caller supplies ``time.time()`` or accepts
the default wall-clock read) and the frozen ``final_time`` float via
``stop_timer(now)``.
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
    - ``score_per_molecule`` — dict keyed the same way -> that
      molecule's recorded score (float), written by
      ``record_molecule_result`` in the SAME call as the flat
      ``molecule_scores`` append (06-01 D11: per-level aggregation
      never needs flat-list slicing under a one-record invariant; the
      key presence is the "already recorded" marker — see
      ``has_record``).
    - ``game_over`` / ``end_state`` / ``final_time`` — the lifecycle
      end state (06-01): ``game_over`` set by ``stop_timer``; the
      reason ``end_state`` (``None | 'completed' | 'gave_up'``) is set
      by the caller (the lifecycle op owns the cause); ``final_time``
      is the frozen final elapsed float from ``stop_timer``.

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
        self.score_per_molecule = {}
        self.game_over = False
        self.end_state = None
        self.final_time = None

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

    def rebase_timer(self, now, elapsed):
        """Re-anchor the ONE timer so the shown elapsed FREEZES at `elapsed`
        (the 1 Hz tick's modal-open pause mechanism — 05-RESEARCH Pattern 3).

        ``timer_anchor`` becomes ``float(now) - float(elapsed)``, so the
        live ``time.time() - timer_anchor`` derivation the tick renders
        stops advancing while a modal child is open. Mutating the single
        anchor in place kills the v1 bug class (P-4: two clocks drifted
        because v1 kept a GUI-side copy) — there is ONE clock home, here.

        Granularity: the freeze is pinned to the last shown second, so the
        modal-open edge can over-count by <= 1 s (documented in the tick
        that calls this).

        The CALLER (the 1 Hz tick) owns modal detection via the Qt
        application object's ``activeModalWidget()`` query — this op is a
        dumb pure function of (now, elapsed) and never touches Qt itself.

        ``elapsed`` must be non-negative: a negative value would push the
        anchor into the future and REWIND the clock — fail-closed, never
        silent. Both args are float-coerced (start_timer's contract), so
        the stored anchor is a real float. Total over valid inputs: works
        from a never-started game too (no start_timer precondition).
        """
        now_f = float(now)
        elapsed_f = float(elapsed)
        if elapsed_f < 0.0:
            raise ValueError(
                "rebase_timer: elapsed must be non-negative, got %r "
                "(a negative elapsed would push the anchor into the "
                "future and rewind the clock)" % (elapsed,))
        self.timer_anchor = now_f - elapsed_f

    def stop_timer(self, now=None):
        """Capture the final elapsed ONCE and freeze it (`final_time`);
        mark ``game_over`` (Q8: stop = capture once + freeze; the caller
        — the lifecycle op — owns WHEN the game stops).

        The timer ANCHOR itself is NEVER touched: it is the pause
        mechanism's home (rebase_timer's live derivation). The end
        REASON (``end_state``, 'completed' | 'gave_up') is likewise NOT
        set here — the caller owns the cause.

        ``now`` defaults to the wall clock (start_timer's contract) and
        is float-coerced, so ``final_time`` is always a real float.
        Total over valid inputs: a never-started game (anchor None)
        freezes at 0.0 (matching rebase_timer's totality); a ``now``
        earlier than the anchor clamps at 0.0 (max(0.0, ...)), never a
        negative elapsed.
        """
        now_f = float(time.time() if now is None else now)
        if self.timer_anchor is None:
            self.final_time = 0.0
        else:
            self.final_time = max(0.0, now_f - self.timer_anchor)
        self.game_over = True

    def advance_molecule(self):
        """Move to the next molecule within the current level."""
        self.current_molecule_index += 1

    def advance_level(self):
        """Move to the next level; the molecule position restarts at 0."""
        self.current_level_index += 1
        self.current_molecule_index = 0

    def has_record(self, level, molecule):
        """Whether molecule (level, molecule) already produced a
        Confirm/Skip record (the Q10 one-record-per-molecule guard
        primitive — key presence, including a 0.0-score record)."""
        return self.molecule_key(level, molecule) in self.score_per_molecule

    def record_molecule_result(self, level, molecule, required, results):
        """Score `results` against `required` and store BOTH the score and
        the formed types for molecule (level, molecule) in one call — in
        BOTH views (the flat ``molecule_scores`` list and the keyed
        ``score_per_molecule`` / ``formed_types_per_molecule`` dicts, so
        the views can never drift apart).

        Returns the SCORE-01 fraction. Raises ValueError on the same
        contract violations as `score` (fail-closed — a malformed record
        set must never be persisted as a believable result).
        """
        value = score(required, results)
        record_types = _validate_records(results)
        key = self.molecule_key(level, molecule)
        self.molecule_scores.append(value)
        self.score_per_molecule[key] = value
        self.formed_types_per_molecule[key] \
            = _formed_types(required, record_types)
        return value

    def endgame_summary(self, molecule_counts):
        """SCORE-07 endgame data payload as a plain dict (the contract
        06-03's engine read op and 06-09's endgame screen consume).

        ``molecule_counts`` = list of per-level molecule counts in
        payload order. ``end_state`` must already be set by the caller
        (the lifecycle op that owns the end cause).

        Returns a dict with EXACTLY these keys:

        - ``end_state`` (str) — 'completed' | 'gave_up'
        - ``level_scores`` (list of float, one per level) — the SUM of
          that level's recorded scores via ``score_per_molecule``
        - ``total`` (float) — the running ``total_score``
        - ``final_time`` (float) — the frozen stop_time
        - ``levels`` / ``molecules`` (int) — len / sum of the counts
        - ``molecules_completed`` (int) — len(``score_per_molecule``)
        - ``skip_count`` / ``giveup_count`` (int) — the plain counters
        - ``ended_level`` / ``ended_molecule`` (int) — the 1-based
          position the game ended at

        FAIL-CLOSED (ValueError naming the cause, never a believable
        partial summary): empty ``molecule_counts``; non-int entries;
        ``end_state`` None or unknown; for 'completed', unless EVERY
        molecule is recorded (len(store) == sum(counts)); for
        'gave_up', unless the record count == full levels up to the
        current one + the current molecule index (the current molecule
        at give-up is intentionally unrecorded — research Q5); and any
        per-level record-count overflow (more records for a level than
        its molecule count — with keys the payload never had counting
        as overflow records for level 0). Per-level aggregation walks
        the keyed store, never flat-list slicing.
        """
        counts = list(molecule_counts)
        if not counts:
            raise ValueError(
                "endgame_summary: molecule_counts must be a non-empty "
                "list of per-level molecule counts (payload order)")
        for c in counts:
            if isinstance(c, bool) or not isinstance(c, int):
                raise ValueError(
                    "endgame_summary: every molecule_counts entry must "
                    "be a plain int count, got %r" % (c,))
        end = self.end_state
        if end is None or end not in ('completed', 'gave_up'):
            raise ValueError(
                "endgame_summary: end_state %r is None or unknown — the "
                "lifecycle op must set 'completed' or 'gave_up' before "
                "the summary is built" % (end,))
        total_molecules = sum(counts)
        n_records = len(self.score_per_molecule)
        if end == 'completed':
            if n_records != total_molecules:
                raise ValueError(
                    "endgame_summary: a 'completed' game must have EVERY "
                    "molecule recorded — %d records for %d molecules"
                    % (n_records, total_molecules))
        else:
            expected = (sum(counts[:self.current_level_index])
                        + self.current_molecule_index)
            if n_records != expected:
                raise ValueError(
                    "endgame_summary: a 'gave_up' game must have exactly "
                    "the completed molecules recorded (%d) — %d records"
                    % (expected, n_records))
        # Per-level aggregation over the keyed store. The container key
        # is 'L{level}M{molecule}' (molecule_key) — parse it the way we
        # built it; anything malformed or outside the declared level
        # range is an overflow/corruption the laws above did not catch,
        # and refuses with its key named.
        level_scores = [0.0] * len(counts)
        seen_per_level = [0] * len(counts)
        for key, value in self.score_per_molecule.items():
            try:
                level = int(key[1:].split('M', 1)[0])
            except (TypeError, IndexError, ValueError):
                raise ValueError(
                    "endgame_summary: score_per_molecule key %r is not a "
                    "'L{level}M{molecule}' container key (corrupt store)"
                    % (key,))
            if level < 0 or level >= len(counts):
                raise ValueError(
                    "endgame_summary: level %d (key %r) is outside the "
                    "declared molecule_counts (%d levels)"
                    % (level, key, len(counts)))
            seen_per_level[level] += 1
            if seen_per_level[level] > counts[level]:
                raise ValueError(
                    "endgame_summary: level %d has more recorded results "
                    "than its molecule count %d (one-record-per-molecule "
                    "broken, key %r)"
                    % (level, counts[level], key))
            level_scores[level] += value
        return {
            'end_state': end,
            'level_scores': level_scores,
            'total': float(self.total_score),
            'final_time': self.final_time,
            'levels': len(counts),
            'molecules': total_molecules,
            'molecules_completed': n_records,
            'skip_count': self.skip_count,
            'giveup_count': self.giveup_count,
            'ended_level': self.current_level_index + 1,
            'ended_molecule': self.current_molecule_index + 1,
        }

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
            'score_per_molecule':
                dict((k, float(v))
                     for k, v in self.score_per_molecule.items()),
            'game_over': self.game_over,
            'end_state': self.end_state,
            'final_time': self.final_time,
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild a GameState from to_dict output (lossless inverse).

        Accept-OLDER law (additive-only evolution): the four 06-01 keys
        use ``.get`` defaults, so a pre-06-01 7-key dict loads without
        KeyError and yields the zero-init defaults for the new fields.
        """
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
        gs.score_per_molecule = dict(
            (k, float(v))
            for k, v in data.get('score_per_molecule', {}).items())
        gs.game_over = data.get('game_over', False)
        gs.end_state = data.get('end_state')
        gs.final_time = data.get('final_time')
        return gs
