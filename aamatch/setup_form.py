"""aamatch.setup_form -- PURE form-glue for the Qt setup window.

Layer: PURE (Phase 4, plan 04-02) -- registered in
tests/test_purity.py PURE_MODULES (Gate A scans EVERY scope, module
level and function bodies). Stdlib plus ``.setup_state`` ONLY; NO
pymol/Qt/numpy; unit-testable under bare python3.6 with zero stubs.
The manifest payload arrives as plain DATA (matching manifest.py's
no-I/O discipline) -- this module never reads files, never touches the
scene.

Three functions serve every Phase-4 Qt button handler (04-09..04-13):

- build_state(form_values, known_set_ids=()) -- collect-then-check.
  Field schema is validate_state's job ALONE (the single validation
  authority; no widget-side re-validation -- setup_state.py:90-144).
  build_state adds the FATAL pre-checks validate_state deliberately
  never performs: each refusal fires BEFORE start_game runs, so a
  doomed Start never cleans the scene first (start_game cleans FIRST,
  gamestart.py:239 -- a refused start would otherwise delete the prior
  game objects before new_game can refuse):

  1. source_mode 'upload' without session-ready ingested content ->
     refuse (uploads are not stored in setup files, so a missing file
     can never silently revive);
  2. non-empty demo_set_id not among the known manifest ids -> refuse
     naming the id (validate_state checks string-shapes only, NEVER
     manifest membership -- setup_state.py:100-102; membership is the
     window's job);
  3. normalized exclusive / block_exclusive with an empty
     allowed_interactions -> refuse with the generator's own wording
     (generator.py:386-389 / :399-401). The check runs on the
     NORMALIZED state because widgets may carry values validate_state
     silently normalizes (setup_state.py:115-135) -- refusing on raw
     input would disagree with what the generator would have seen.

  The extra non-schema key 'upload_ready' (bool: True iff the window
  holds ingested content matching the form's upload path) is consumed
  here and NEVER passed through: the validate_state input is built as
  a NEW dict of the 7 schema keys, so the caller's dict stays
  untouched (D3/P6).

- usable_randomized_state(seed=None, demo_set_id='') -- the Randomize
  fix-up. Plain randomize_state synthesizes demo_set_id 'demo-%%04x'
  (setup_state.py:165) which matches NO manifest set: Start straight
  after Randomize refused inside new_game (engine.py:204-207). This
  helper overwrites the id with a REAL manifest id (or '' = all sets,
  engine.py:200-201) and leaves everything else untouched --
  source_mode stays 'demo' and upload stays None
  (setup_state.py:157-159), the random mode/allowed/int fields are
  randomize_state's own. randomize_state's output shape is pinned by
  tests/test_setup_state.py and is NOT changed.

- manifest_sets(payload) -- parsed manifest PAYLOAD (dict with 'sets')
  to dropdown rows: (set_id, title, tier) tuples sorted by set_id,
  with .get fallbacks (title -> set_id, tier -> ''; payload shape
  manifest.py:31-43). Empty or missing 'sets' -> [] (an empty
  manifest parses fine, per 02-03). Pure data-in/data-out, no I/O.

Dependency direction (B8): the cmd/Qt tier imports FROM this pure
module; this module imports stdlib + .setup_state only.
"""

from .setup_state import randomize_state, validate_state

_SCHEMA_KEYS = ('source_mode', 'demo_set_id', 'upload',
                'molecules_per_level', 'difficulty_levels',
                'interaction_mode', 'allowed_interactions')


def build_state(form_values, known_set_ids=()):
    """Validate the collected form into a setup state, or raise ValueError.

    `form_values` is a plain dict carrying the 7 setup fields as the
    widgets collect them PLUS one non-schema key 'upload_ready' (bool:
    True iff the window holds ingested content matching the form's
    upload path). `known_set_ids` is the manifest set-id inventory as
    plain data (pure layer never reads files). Raises ValueError with a
    user-facing message BEFORE touching anything on the three doomed
    configurations (module docstring); otherwise returns the
    validate_state-normalized 7-field dict, unmodified.
    """
    if form_values.get('source_mode') == 'upload' \
            and not form_values.get('upload_ready'):
        raise ValueError(
            "upload mode needs an ingested molecule file -- use Browse "
            "to pick an SDF or MOL2 file first (uploads are not stored "
            "in setup files)")
    demo_set_id = form_values.get('demo_set_id') or ''
    if form_values.get('source_mode') == 'demo' and demo_set_id \
            and demo_set_id not in known_set_ids:
        raise ValueError(
            "demo set %r is no longer bundled -- pick a set from the "
            "dropdown" % demo_set_id)

    schema_input = dict((k, form_values.get(k)) for k in _SCHEMA_KEYS)
    state = validate_state(schema_input)

    if state['interaction_mode'] == 'exclusive' \
            and not state['allowed_interactions']:
        raise ValueError(
            "exclusive mode requires the setup field "
            "'allowed_interactions' to be non-empty -- check the "
            "interactions the game should teach in Setup")
    if state['interaction_mode'] == 'block_exclusive' \
            and not state['allowed_interactions']:
        raise ValueError(
            "block_exclusive mode requires 'allowed_interactions': no "
            "interactions checked")
    return state


def usable_randomized_state(seed=None, demo_set_id=''):
    """Randomize a setup state whose demo_set_id is USABLE.

    randomize_state(seed) then overwrite demo_set_id with the passed
    value (a real manifest id, or '' = all sets); nothing else changes
    (module docstring). Deterministic under seed.
    """
    state = randomize_state(seed)
    state['demo_set_id'] = demo_set_id
    return state


def manifest_sets(payload):
    """Return dropdown rows [(set_id, title, tier)] for a manifest payload.

    Input: a parsed manifest PAYLOAD (dict with 'sets'). Rows are sorted
    by set_id; title falls back to set_id and tier to '' when missing
    (.get defaults). Empty or missing 'sets' -> []. No I/O.
    """
    if not isinstance(payload, dict):
        return []
    sets = payload.get('sets') or []
    rows = [(s.get('set_id'), s.get('title', s.get('set_id')),
             s.get('tier', '')) for s in sets]
    return sorted(rows, key=lambda row: row[0])


# Canonical tier vocabulary (08-RESEARCH-sourcing handoff #5; the manifest
# strings are exact tokens, display order is EASY first). Tiers outside
# this tuple land in the trailing 'Other' group of manifest_sets_grouped.
TIER_ORDER = ('easy', 'hard', 'challenge', 'very_challenging')
TIER_LABELS = {'easy': 'Easy', 'hard': 'Hard',
               'challenge': 'Challenge',
               'very_challenging': 'Very challenging'}


def manifest_sets_grouped(payload):
    """Return dropdown GROUPS [(display_label, rows)] for a manifest payload.

    rows are the manifest_sets tuples [(set_id, title, tier)] (already
    sorted by set_id); groups appear in TIER_ORDER sequence, empty groups
    omitted; tiers outside TIER_ORDER (incl. missing/'') land in a final
    'Other' group, omitted when empty. Non-dict payload -> []. No I/O.
    """
    rows = manifest_sets(payload)
    groups = []
    for tier in TIER_ORDER:
        group = [row for row in rows if row[2] == tier]
        if group:
            groups.append((TIER_LABELS[tier], group))
    other = [row for row in rows if row[2] not in TIER_ORDER]
    if other:
        groups.append(('Other', other))
    return groups
