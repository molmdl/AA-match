"""Tests for aamatch.setup_form -- the PURE form-glue module (plan 04-02).

RED-first suite covering the three functions every Phase-4 Qt button
handler (04-09..04-13) calls:

- build_state(form_values, known_set_ids=()): the FATAL pre-checks that
  refuse doomed configurations BEFORE the scene is touched (start_game
  cleans FIRST, gamestart.py:239 -- a refused start must not delete prior
  game objects), delegating the field schema itself to validate_state
  (the single validation authority; no widget-side re-validation):

  1. source_mode 'upload' without ingested content (upload_ready False)
     -> refuse naming Browse
  2. demo_set_id not among the known manifest set ids -> refuse naming
     the id
  3. exclusive / block_exclusive with an empty allowed_interactions ->
     refuse with the generator's own wording (generator.py:386-389 /
     :399-401)

- usable_randomized_state(seed, demo_set_id): the Randomize fix-up.
  Plain randomize_state synthesizes demo_set_id 'demo-%04x' which matches
  NO manifest set (setup_state.py:165) -- starting right after Randomize
  refused inside new_game (engine.py:204-207). The helper overwrites the
  id with a REAL one (or '' = all sets) and leaves everything else
  untouched.
- manifest_sets(payload): parsed manifest payload -> sorted dropdown
  rows (set_id, title, tier) with .get fallbacks; pure data-in/data-out,
  no I/O.

Runs under bare python3.6 in WSL with stdlib only -- zero stubs (the
module under test is pure and imports only stdlib + .setup_state).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aamatch.setup_form import (
    build_state,
    manifest_sets,
    usable_randomized_state,
)
from aamatch.setup_state import (
    INTERACTION_TYPES,
    randomize_state,
    validate_state,
)

# The pinned refusal messages (regression teeth: wording is user-facing
# and must never drift silently).
MSG_UPLOAD = ("upload mode needs an ingested molecule file -- use Browse "
              "to pick an SDF or MOL2 file first (uploads are not stored "
              "in setup files)")
MSG_EXCLUSIVE = ("exclusive mode requires the setup field "
                 "'allowed_interactions' to be non-empty -- check the "
                 "interactions the game should teach in Setup")
MSG_BLOCK_EXCLUSIVE = ("block_exclusive mode requires "
                       "'allowed_interactions': no interactions checked")
MSG_DEMO = "demo set %r is no longer bundled -- pick a set from the dropdown"

KNOWN_SET_IDS = ('demo-dev-1',)
SCHEMA_KEYS = ('source_mode', 'demo_set_id', 'upload', 'molecules_per_level',
               'difficulty_levels', 'interaction_mode',
               'allowed_interactions')


def _valid_form(**overrides):
    """A complete valid form dict: the 7 schema fields + upload_ready."""
    form = {
        'source_mode': 'demo',
        'demo_set_id': 'demo-dev-1',
        'upload': None,
        'molecules_per_level': 4,
        'difficulty_levels': 5,
        'interaction_mode': 'unset',
        'allowed_interactions': ['h_bond', 'metal'],
        'upload_ready': False,
    }
    form.update(overrides)
    return form


class TestBuildStateIdentity(unittest.TestCase):
    """A valid form passes through validate_state EXACTLY (the pure layer
    stays the ONLY validation authority -- build_state adds refusals, not
    re-validation)."""

    def test_build_state_identity(self):
        form = _valid_form()
        result = build_state(form, known_set_ids=KNOWN_SET_IDS)
        schema_only = dict((k, form[k]) for k in SCHEMA_KEYS)
        self.assertEqual(result, validate_state(schema_only))
        # The non-schema key never leaks into the output.
        self.assertNotIn('upload_ready', result)
        self.assertEqual(set(result), set(SCHEMA_KEYS))
        # The caller's dict is never mutated (upload_ready still there).
        self.assertIn('upload_ready', form)


class TestBuildStateRefusesEmptyAllowed(unittest.TestCase):
    """Refusal 3: exclusive / block_exclusive with an empty allowed list.
    Wording aligned with the generator's own refusals (generator.py
    :386-389 / :399-401) so the user sees ONE consistent message family."""

    def test_build_state_refuses_empty_allowed_exclusive(self):
        form = _valid_form(interaction_mode='exclusive',
                           allowed_interactions=[])
        with self.assertRaises(ValueError) as ctx:
            build_state(form, known_set_ids=KNOWN_SET_IDS)
        self.assertEqual(str(ctx.exception), MSG_EXCLUSIVE)

    def test_build_state_refuses_empty_allowed_block_exclusive(self):
        form = _valid_form(interaction_mode='block_exclusive',
                           allowed_interactions=[])
        with self.assertRaises(ValueError) as ctx:
            build_state(form, known_set_ids=KNOWN_SET_IDS)
        self.assertEqual(str(ctx.exception), MSG_BLOCK_EXCLUSIVE)


class TestBuildStateRefusesUploadWithoutContent(unittest.TestCase):
    """Refusal 1: upload mode requires session-ready ingested content."""

    UPLOAD = {'path': 'C:\\sets\\mine.sdf', 'sha256': 'ab' * 32}

    def test_upload_mode_without_upload_ready_refuses(self):
        form = _valid_form(source_mode='upload', upload=self.UPLOAD,
                           upload_ready=False)
        with self.assertRaises(ValueError) as ctx:
            build_state(form, known_set_ids=KNOWN_SET_IDS)
        self.assertEqual(str(ctx.exception), MSG_UPLOAD)

    def test_upload_mode_with_upload_ready_passes(self):
        form = _valid_form(source_mode='upload', upload=self.UPLOAD,
                           upload_ready=True)
        result = build_state(form, known_set_ids=KNOWN_SET_IDS)
        self.assertEqual(result['source_mode'], 'upload')
        self.assertEqual(result['upload'], self.UPLOAD)


class TestBuildStateRefusesUnknownDemoSet(unittest.TestCase):
    """Refusal 2: a non-empty demo_set_id must be among the known ids."""

    def test_unknown_demo_set_refuses_naming_the_id(self):
        form = _valid_form(demo_set_id='demo-gone')
        with self.assertRaises(ValueError) as ctx:
            build_state(form, known_set_ids=KNOWN_SET_IDS)
        self.assertEqual(str(ctx.exception), MSG_DEMO % 'demo-gone')

    def test_no_known_sets_still_refuses_nonempty_id(self):
        # Empty manifest case: no bundled sets at all -> a non-empty id
        # still refuses (membership can never hold).
        form = _valid_form(demo_set_id='demo-gone')
        with self.assertRaises(ValueError) as ctx:
            build_state(form, known_set_ids=())
        self.assertEqual(str(ctx.exception), MSG_DEMO % 'demo-gone')

    def test_empty_demo_set_id_passes(self):
        # '' = all sets (engine.py:200-201); never a membership refusal.
        form = _valid_form(demo_set_id='')
        result = build_state(form, known_set_ids=())
        self.assertEqual(result['demo_set_id'], '')


class TestBuildStateNonemptyAllowedPasses(unittest.TestCase):
    """Exclusive with at least one checked type normalizes cleanly."""

    def test_build_state_nonempty_allowed_passes(self):
        form = _valid_form(interaction_mode='exclusive',
                           allowed_interactions=['metal', 'h_bond'])
        result = build_state(form, known_set_ids=KNOWN_SET_IDS)
        # Canonical INTERACTION_TYPES order, deduped (validate_state's
        # job -- build_state returns it unmodified).
        self.assertEqual(result['allowed_interactions'],
                         ['h_bond', 'metal'])
        canonical = [t for t in INTERACTION_TYPES
                     if t in result['allowed_interactions']]
        self.assertEqual(result['allowed_interactions'], canonical)
        self.assertEqual(result['interaction_mode'], 'exclusive')


class TestUsableRandomizedStateDeterministicAndUsable(unittest.TestCase):
    """The Randomize fix-up: deterministic under seed, validate-clean,
    source demo/upload None preserved (setup_state.py:157-159)."""

    def test_seeded_calls_are_identical(self):
        first = usable_randomized_state(0, demo_set_id='demo-dev-1')
        second = usable_randomized_state(0, demo_set_id='demo-dev-1')
        self.assertEqual(first, second)

    def test_output_round_trips_validate_state(self):
        result = usable_randomized_state(0, demo_set_id='demo-dev-1')
        self.assertEqual(validate_state(result), result)
        self.assertEqual(set(result), set(SCHEMA_KEYS))

    def test_demo_set_id_override(self):
        result = usable_randomized_state(0, demo_set_id='demo-dev-1')
        self.assertEqual(result['demo_set_id'], 'demo-dev-1')
        result = usable_randomized_state(0, demo_set_id='')
        self.assertEqual(result['demo_set_id'], '')

    def test_source_and_upload_preserved(self):
        result = usable_randomized_state(0, demo_set_id='demo-dev-1')
        self.assertEqual(result['source_mode'], 'demo')
        self.assertIsNone(result['upload'])

    def test_default_arguments(self):
        result = usable_randomized_state()
        self.assertEqual(result['demo_set_id'], '')
        self.assertEqual(result['source_mode'], 'demo')


class TestUsableRandomizedStateKillTheTrap(unittest.TestCase):
    """The 'demo-%04x' trap is dead: plain randomize_state synthesizes an
    id matching NO manifest set (setup_state.py:165 -> engine.py:204-207
    refusal); the fix-up NEVER lets it survive."""

    def test_synthesized_id_never_survives(self):
        for seed in range(20):
            with self.subTest(seed=seed):
                synthesized = randomize_state(seed)['demo_set_id']
                self.assertTrue(synthesized.startswith('demo-'),
                                'trap premise broken: %r' % synthesized)
                usable = usable_randomized_state(
                    seed, demo_set_id='demo-dev-1')
                self.assertNotEqual(usable['demo_set_id'], synthesized)
                self.assertEqual(usable['demo_set_id'], 'demo-dev-1')


class TestManifestSets(unittest.TestCase):
    """Dropdown rows from a parsed manifest PAYLOAD: sorted tuples with
    .get fallbacks, pure data-in/data-out (no I/O)."""

    def test_sorted_tuples_with_fallbacks(self):
        payload = {
            'manifest_version': 1,
            'sets': [
                {'set_id': 'demo-b', 'tier': 'hard'},          # no title
                {'set_id': 'demo-a', 'title': 'A set', 'tier': 'easy'},
                {'set_id': 'demo-c', 'title': 'C set'},        # no tier
            ],
        }
        self.assertEqual(
            manifest_sets(payload),
            [('demo-a', 'A set', 'easy'),
             ('demo-b', 'demo-b', 'hard'),    # title falls back to set_id
             ('demo-c', 'C set', '')])        # tier falls back to ''

    def test_empty_sets_gives_empty_list(self):
        self.assertEqual(manifest_sets({'sets': []}), [])

    def test_missing_sets_key_gives_empty_list(self):
        self.assertEqual(manifest_sets({}), [])


class TestManifestSetsGrouped(unittest.TestCase):
    """Tier-grouped dropdown rows (08-02): groups follow TIER_ORDER with
    display labels, rows stay the manifest_sets tuples (sorted by set_id
    within a group), tiers outside the vocabulary (incl. missing/'')
    collapse into ONE final 'Other' group, and empty groups are omitted
    entirely (a single-group manifest yields zero separators at runtime).
    manifest_sets itself stays byte-identical -- the grouping is ONE call
    plus list-comprehension partitioning, no re-sort."""

    def test_multi_tier_groups_follow_tier_order(self):
        from aamatch import setup_form
        payload = {
            'manifest_version': 1,
            'sets': [
                {'set_id': 's-vc', 'title': 'VC', 'tier': 'very_challenging'},
                {'set_id': 's-easy', 'title': 'E', 'tier': 'easy'},
                {'set_id': 's-chal', 'title': 'C', 'tier': 'challenge'},
                {'set_id': 's-hard', 'title': 'H', 'tier': 'hard'},
            ],
        }
        groups = setup_form.manifest_sets_grouped(payload)
        self.assertEqual([label for (label, _rows) in groups],
                         ['Easy', 'Hard', 'Challenge', 'Very challenging'])

    def test_within_group_rows_sorted_by_set_id(self):
        from aamatch import setup_form
        payload = {
            'sets': [
                {'set_id': 'z-easy', 'title': 'Z', 'tier': 'easy'},
                {'set_id': 'a-easy', 'title': 'A', 'tier': 'easy'},
                {'set_id': 'm-easy', 'tier': 'easy'},   # title -> set_id
            ],
        }
        groups = setup_form.manifest_sets_grouped(payload)
        self.assertEqual(groups, [('Easy', [('a-easy', 'A', 'easy'),
                                            ('m-easy', 'm-easy', 'easy'),
                                            ('z-easy', 'Z', 'easy')])])

    def test_unknown_missing_tiers_collapse_into_one_other_group(self):
        from aamatch import setup_form
        payload = {
            'sets': [
                {'set_id': 's-z', 'tier': 'weird'},
                {'set_id': 's-easy', 'title': 'E', 'tier': 'easy'},
                {'set_id': 's-y'},                       # tier -> ''
                {'set_id': 's-x', 'tier': ''},
            ],
        }
        groups = setup_form.manifest_sets_grouped(payload)
        # 'Other' lands LAST, after every known-tier group, and the rows
        # of ALL three collateral tiers live in ONE group (set_id order).
        self.assertEqual([label for (label, _rows) in groups],
                         ['Easy', 'Other'])
        other_rows = groups[1][1]
        self.assertEqual(other_rows, [('s-x', 's-x', ''),
                                      ('s-y', 's-y', ''),
                                      ('s-z', 's-z', 'weird')])

    def test_empty_groups_omitted(self):
        from aamatch import setup_form
        payload = {
            'sets': [
                {'set_id': 'only-easy', 'title': 'OE', 'tier': 'easy'},
            ],
        }
        # EXACTLY one group -> zero separators at runtime today.
        self.assertEqual(setup_form.manifest_sets_grouped(payload),
                         [('Easy', [('only-easy', 'OE', 'easy')])])
        # No unknown tiers -> no 'Other' group either.
        hard_only = {'sets': [{'set_id': 'h', 'tier': 'hard'}]}
        self.assertEqual(setup_form.manifest_sets_grouped(hard_only),
                         [('Hard', [('h', 'h', 'hard')])])

    def test_empty_or_missing_sets_gives_empty_groups(self):
        from aamatch import setup_form
        self.assertEqual(setup_form.manifest_sets_grouped({'sets': []}), [])
        self.assertEqual(setup_form.manifest_sets_grouped({}), [])

    def test_non_dict_payload_gives_empty_groups(self):
        from aamatch import setup_form
        for bad in (None, [], 'x', 42, ['sets']):
            with self.subTest(bad=bad):
                self.assertEqual(setup_form.manifest_sets_grouped(bad), [])


if __name__ == '__main__':
    unittest.main()
