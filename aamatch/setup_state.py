"""aamatch.setup_state -- single source of truth for the setup schema.

Layer: PURE (Phase-1 foundation). The complete 7-field setup model lives
here: enums, clamp constants, DEFAULTS, validate_state (non-mutating)
and randomize_state (seed-deterministic). NO Qt, NO pymol -- unit-tested
in WSL with bare python3.6 (Phase-1 success criterion 1; the GUI
collect/apply equivalents are Phase 4).

Design contract (research D1-D4, R4, P5/P6/P8):

- DEFAULTS is complete: exactly one entry per field. The key-set test
  fails loudly on schema drift (D2). Do NOT add a 'format' field: the
  persistence container header (magic/version/kind) is the ONLY format
  tag (P8 -- prior art carried both and drifted, C1).
- validate_state returns a NEW dict built from a deepcopy of DEFAULTS;
  the input is never mutated (D3/P6). Missing keys fill from DEFAULTS;
  invalid enums fall back to their default; ints coerce via int() then
  clamp to [MIN, CAP]; allowed_interactions is filtered to
  INTERACTION_TYPES, deduped and stored in canonical INTERACTION_TYPES
  order, so equal sets serialize identically; upload is shape-checked.
- randomize_state uses a local random.Random(seed): deterministic under
  a fixed seed (D4). source_mode stays 'demo' and upload stays None --
  a randomized state must be usable without a real upload file.
- allowed_interactions is populated regardless of interaction_mode: the
  mode governs USE (decided in Phase 2/4), and the list is always
  serialized for format stability (R4).
- upload reserves {path, sha256} for portability semantics decided in
  Phase 4 (OQ3/P5: sha256 lets Load warn when the file moved). Manifest
  membership of demo_set_id lands in Phase 2/8 -- Phase 1 validates
  non-empty string only.

Dependency direction (B8): cmd/GUI modules import FROM this pure module;
this module imports stdlib only (copy, random).
"""

import copy
import random

# v1 decision: 7 interaction types, salt bridge includes ionic (H6).
INTERACTION_TYPES = ["h_bond", "salt_bridge", "pi_stacking", "cation_pi",
                     "hydrophobic", "halogen", "metal"]

# SETUP-06 wording: mode governs how allowed_interactions is USED.
INTERACTION_MODES = ["exclusive", "block_exclusive", "unset"]

MOLECULES_DEFAULT, MOLECULES_MIN, MOLECULES_CAP = 2, 1, 10
# difficulty cap 10: human-amended at the 01-09 install checkpoint
# (proposed 9, human approved 10). Frozen for Phases 2+; changing it
# later is a version-bump event.
DIFFICULTY_DEFAULT, DIFFICULTY_MIN, DIFFICULTY_CAP = 3, 1, 10

_VALID_SOURCE_MODES = ('demo', 'upload')

DEFAULTS = {
    "source_mode": "demo",        # "demo" | "upload"                (SPEC:14)
    "demo_set_id": "",            # manifest id; membership lands Phase 2/8
    "upload": None,               # None | {"path": str, "sha256": str} (OQ3)
    "molecules_per_level": 2,     # int, clamp [MOLECULES_MIN, MOLECULES_CAP]
    "difficulty_levels": 3,       # int, clamp [DIFFICULTY_MIN, DIFFICULTY_CAP]
    "interaction_mode": "unset",  # "unset" = random (spec.md:20), SETUP-06
    "allowed_interactions": [],   # INTERACTION_TYPES members, canonical order
}


def _to_int(value, default):
    """Coerce to int via int(), falling back to `default` on failure.

    int('x') -> ValueError, int(None) -> TypeError; both fall back.
    Numeric strings ('5') and floats (truncation) coerce; bools coerce
    to 0/1 and are then clamped like any other int.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_str(value, default):
    """Coerce to str; JSON null (None) counts as missing -> `default`."""
    if value is None:
        return default
    return str(value)


def _clamp(value, minimum, cap):
    """Clamp `value` into the closed interval [minimum, cap]."""
    return max(minimum, min(cap, value))


def validate_state(state):
    """Return a NEW validated setup dict; `state` is never mutated (D3/P6).

    Fill/normalize rules (R4/D3):
    - missing keys (or a non-dict input) fill from DEFAULTS
    - enums fall back to default on invalid values
    - int fields coerce via int() then clamp to [MIN, CAP]
    - allowed_interactions keeps only INTERACTION_TYPES members, deduped,
      stored in canonical INTERACTION_TYPES order
    - upload is kept only as {'path': str, 'sha256': str} (extra keys
      dropped), else None
    - demo_set_id/source_mode get str coercion only; manifest membership
      is a Phase 2/8 concern
    """
    if not isinstance(state, dict):
        state = {}
    clean = copy.deepcopy(DEFAULTS)

    source_mode = _to_str(state.get('source_mode'), DEFAULTS['source_mode'])
    clean['source_mode'] = source_mode if source_mode in _VALID_SOURCE_MODES \
        else DEFAULTS['source_mode']

    clean['demo_set_id'] = _to_str(state.get('demo_set_id'),
                                   DEFAULTS['demo_set_id'])

    mode = state.get('interaction_mode')
    clean['interaction_mode'] = mode if mode in INTERACTION_MODES \
        else DEFAULTS['interaction_mode']

    clean['molecules_per_level'] = _clamp(
        _to_int(state.get('molecules_per_level'),
                DEFAULTS['molecules_per_level']),
        MOLECULES_MIN, MOLECULES_CAP)
    clean['difficulty_levels'] = _clamp(
        _to_int(state.get('difficulty_levels'),
                DEFAULTS['difficulty_levels']),
        DIFFICULTY_MIN, DIFFICULTY_CAP)

    chosen = set()
    items = state.get('allowed_interactions')
    if isinstance(items, (list, tuple, set, frozenset)):
        for item in items:
            if item in INTERACTION_TYPES:
                chosen.add(item)
    clean['allowed_interactions'] = [t for t in INTERACTION_TYPES
                                     if t in chosen]

    upload = state.get('upload')
    if isinstance(upload, dict):
        path = upload.get('path')
        sha256 = upload.get('sha256')
        if isinstance(path, str) and isinstance(sha256, str):
            clean['upload'] = {'path': path, 'sha256': sha256}

    return clean


def randomize_state(seed=None):
    """Return a complete, valid setup state; deterministic under seed (D4).

    Uses a local random.Random(seed) so repeated calls with the same
    seed return equal states. Fields:
    - demo_set_id: random non-empty string ('demo-' + 4 hex digits)
    - molecules_per_level / difficulty_levels: random within clamp
    - interaction_mode: random choice from INTERACTION_MODES
    - allowed_interactions: random NON-EMPTY subset in canonical order,
      regardless of mode (mode governs USE, decided Phase 2/4)
    - source_mode stays 'demo' and upload stays None: a randomized
      state must be usable without a real file
    """
    rng = random.Random(seed)
    count = rng.randint(1, len(INTERACTION_TYPES))
    picked = set(rng.sample(INTERACTION_TYPES, count))
    candidate = {
        'source_mode': DEFAULTS['source_mode'],
        'demo_set_id': 'demo-%04x' % rng.randint(0, 0xFFFF),
        'upload': None,
        'molecules_per_level': rng.randint(MOLECULES_MIN, MOLECULES_CAP),
        'difficulty_levels': rng.randint(DIFFICULTY_MIN, DIFFICULTY_CAP),
        'interaction_mode': rng.choice(INTERACTION_MODES),
        'allowed_interactions': [t for t in INTERACTION_TYPES if t in picked],
    }
    return validate_state(candidate)
