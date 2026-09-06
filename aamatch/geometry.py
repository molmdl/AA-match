"""Cmd-tier geometry bridge: PyMOL objects -> plain data for the pure
detector and generator.

Layer: CMD TIER. ``from pymol import cmd`` at module level is LEGAL here;
this module must NEVER be added to ``PURE_MODULES`` in
``tests/test_purity.py`` (Gates A/B scan only the pure registry; Gate D
still compiles this file under the 3.6 syntax floor).

This module IS the pure/cmd boundary for geometry: PyMOL objects are read
here and handed down as plain dicts/tuples/lists that the PURE detector
(``aamatch.detector.detect``) and the PURE generator
(``aamatch.generator.generate``) consume unchanged. Geometry crosses the
boundary at exactly two points (materialization research §7.2):

1. post-materialize bounds  -- ``bounding_sphere`` feeds the generator's
   ``ligand_data`` (grid sizing happens from the ligand's bounding sphere);
2. detect-on-demand         -- ``extract_game_atoms`` + ``ligand_bonds``
   produce the detector-contract records (detection research §5.1, the
   exact dict shape ``detector.detect`` consumes).

CONTRACTS (all probe- and research-pinned):

- WORLD FRAME ONLY. Phase 2 bakes coordinates (``cmd.translate``/``rotate``
  with ``camera=0`` write stored coords); ``iterate_state`` coords ARE the
  placed pose. No matrix composition, and pose assertions compare
  COORDINATES (``coords_of``) -- never ``cmd.get_object_matrix`` (it is the
  coordinate history and is non-identity after bakes; research §6.2).
- STATE 1 ONLY. The game keeps single-state objects (one state per loaded
  ligand file, one fragment per grid object); every read pins state 1.
- NEVER ``cmd.get_model`` for extraction (PITFALL 15: full-structure
  Python copy, the classic OOM trap). Only ``cmd.iterate_state`` with
  narrow selections over game objects.
- EXPLICIT ``space=`` dict ALWAYS (Pitfall 8: the default pollutes the
  global ``pymol`` module dict), and NO ``round()`` inside expressions
  (probe-proven NameError in the expression sandbox; rounding, if ever
  needed, happens in Python after extraction).
- IDENTITY = ``(object, id)``. ``id`` is read as uppercase ``ID`` in the
  iterate expression namespace (lowercase ``id`` is the Python builtin --
  NameError or a wrong value; Pitfall 8). Copies share ids, so the
  object name is half of every identity.
- RESIDUE NUMBER: the record key is ``resi`` (detector contract, int) but
  the expression reads ``resv`` -- the INTEGER residue value. ``resi`` in
  the expression namespace is a STRING (insertion-code capable, e.g.
  '12A', and blank for SDF loads), which would violate the detector
  contract's ``"resi": int`` and break ``int(rec['resi'])`` on the AA
  side. ``resv`` is the prior-art-proven int accessor (editing.py symbol
  table; prior art wizard.py carried ``resv``).
- BOND BLOCK: ``cmd.get_bonds(obj, 1)`` returns (atm1, atm2, order)
  tuples whose atm1/atm2 are 0-based positions enumerating the atoms of
  the SELECTION in walk order (querying.py:1078-1084 warning -- they do
  NOT necessarily equal the ``index`` atom property). For the only
  intended use -- a whole single-object selection -- walk position i
  addresses the atom whose per-object ``index`` property is i+1, so
  ``index_to_id[i + 1]`` is that atom's ID. The 1-based ``index``
  property values collected by the same ``iterate_state`` walk are in
  the same order, so the returned map is exhaustive over the bond
  indices. Callers translate bond positions into detector-side record
  positions via this map (the detector validates them fail-closed).
- NO FILE I/O HERE. Every file-path use routes through
  ``aamatch.paths.to_windows_path`` -- loads live in placement; this
  module only reads LIVE objects.
- RULE-FREE BRIDGE. No numpy (plain tuples/lists), no thresholds, no
  atom/residue typing logic -- typing is ``aamatch.capability``'s job and
  thresholds are ``aamatch.thresholds``' job. This module only moves
  bytes across the boundary.

Shared by SMOKE-03/04/05 and (later) the Phase-3 wizard confirm -- the
ONE extraction helper so both paths feed the detector identically
(detection research §5.1).

Python floor: PyMOL's Windows Python 3.9 at runtime, but written 3.6-safe
(Gate D compiles every aamatch/*.py under python3.6).
"""

from pymol import cmd

# Game-object namespace (research §4 sentinel + reserved-prefix
# conventions): every AA-match game object starts with this prefix.
# Filtering is PREFIX-ONLY -- never hetatm/polymer selectors (user
# molecules in the session must never leak into or out of the game set).
GAME_PREFIX = '_aam_'

# AA grid objects are the '_aam_aa*' subset; everything else game-side
# is the ligand side. This is the detector contract's side field
# ('aa' | 'lig' -- anything else fails closed inside the detector).
GAME_AA_PREFIX = '_aam_aa'

# The detector-contract record keys, in the order the single
# iterate_state pass collects them (model, ID, name, elem, resn, resv,
# alt, formal_charge, x, y, z). Pinned by a module-level tuple so the
# expression string and the record builder stay in lockstep.
_EXTRACT_FIELDS = ('model', 'ID', 'name', 'elem', 'resn', 'resv', 'alt',
                   'formal_charge', 'x', 'y', 'z')


def game_object_names():
    """Sorted names of game objects -- 'objects' starting with '_aam_'.

    Prefix filter ONLY (research §4): no hetatm/polymer/organic selectors,
    so a user-loaded protein can never be mistaken for game content and
    game content is never hidden by a selector change. Sorted for
    deterministic downstream selection/extraction order.
    """
    return sorted(n for n in cmd.get_names('objects')
                  if n.startswith(GAME_PREFIX))


def extract_game_atoms():
    """Extract detector-contract atom records over ALL game objects.

    One ``cmd.iterate_state(1, sel, ...)`` pass over the ' or '-joined
    game-object selection appends (model, ID, name, elem, resn, resv,
    alt, formal_charge, x, y, z) per atom -- properties AND coordinates
    in the SAME expression (iterate_state exposes x/y/z; plain iterate
    does not -- Pitfall 8). Records carry the exact dict shape
    ``aamatch.detector.detect`` consumes:

        {'side': 'aa'|'lig', 'object': str, 'id': int, 'name': str,
         'elem': str, 'resn': str, 'resi': int, 'alt': str,
         'formal_charge': int, 'x': float, 'y': float, 'z': float}

    'side' is 'aa' for objects under the '_aam_aa' prefix, 'lig'
    otherwise (sentinel objects never carry atoms, so no third case
    exists). Returns [] when no game objects exist. Records are sorted
    by (object, id) -- deterministic detector input regardless of
    PyMOL's object walk order.
    """
    names = game_object_names()
    if not names:
        return []
    rows = []
    # Explicit space dict ALWAYS; no round() in the expression (probe-
    # proven NameError); uppercase ID (lowercase id is the builtin).
    cmd.iterate_state(
        1, ' or '.join(names),
        'stored.append((model, ID, name, elem, resn, resv, alt, '
        'formal_charge, x, y, z))',
        space={'stored': rows})
    records = []
    for row in rows:
        (model, ID, name, elem, resn, resv, alt, formal_charge,
         x, y, z) = row
        records.append({
            'side': 'aa' if model.startswith(GAME_AA_PREFIX) else 'lig',
            'object': model,
            'id': int(ID),
            'name': name,
            'elem': elem,
            'resn': resn,
            'resi': int(resv),      # resv: int residue value (see module docstring)
            'alt': alt,
            'formal_charge': int(formal_charge),
            'x': float(x),
            'y': float(y),
            'z': float(z),
        })
    records.sort(key=lambda r: (r['object'], r['id']))
    return records


def ligand_bonds(lig_object):
    """Ligand bond block + the bond-index -> atom-ID map.

    Returns (bonds, index_to_id):

    - bonds: [(i, j, order), ...] from ``cmd.get_bonds(lig_object, 1)``
      -- one tuple per bond in the given state; i/j are 0-based
      positions enumerating the selection's atoms in walk order
      (querying.py:1078-1084). For a whole single-object selection,
      position i addresses the atom whose ``index`` property is i+1.
    - index_to_id: {index_property: atom ID} built in ONE
      ``iterate_state`` pass appending (index, ID). For a whole
      single-object selection the walk collects index == 1..N in bond
      order, so ``index_to_id[bond_pos + 1]`` resolves any bond endpoint.

    State 1 only (single-state game objects); explicit space dict; no
    file I/O (the ligand object is already live -- loads live in
    placement, behind ``to_windows_path``).
    """
    raw = cmd.get_bonds(lig_object, 1) or []
    bonds = [(int(i), int(j), int(order)) for (i, j, order) in raw]
    pairs = []
    cmd.iterate_state(1, lig_object, 'stored.append((index, ID))',
                      space={'stored': pairs})
    index_to_id = {}
    for index, ID in pairs:
        index_to_id[int(index)] = int(ID)
    return bonds, index_to_id


def bounding_sphere(records):
    """Ligand bounding sphere -> ((cx, cy, cz), radius).

    Centroid of ALL ligand-side records ('side' == 'lig') in the given
    record list, radius = max distance from the centroid (the same
    maximum-extent definition the detector applies internally). This is
    the generator's ``ligand_data`` -- {'centroid': ..., 'radius': ...}
    -- fed IN by the cmd tier after load/materialize (generation
    research §5); with Phase-2 baked coordinates the world frame IS the
    ligand-file frame.

    Fails closed (ValueError) when the records carry no ligand side:
    a ligand-less scene cannot size a grid, and NaN/empty bounds would
    only surface later inside the generator (or as allow_nan=False at
    save). Callers that hold separate ligand records may pass them
    directly -- the side filter is idempotent.
    """
    lig = [r for r in records if r.get('side') == 'lig']
    if not lig:
        raise ValueError(
            'geometry.bounding_sphere: no ligand-side records -- the '
            "generator's ligand_data needs the ligand's bounding sphere "
            "(side == 'lig')")
    n = len(lig)
    sx = sy = sz = 0.0
    for r in lig:
        sx += float(r['x'])
        sy += float(r['y'])
        sz += float(r['z'])
    center = (sx / n, sy / n, sz / n)
    radius = 0.0
    for r in lig:
        dx = float(r['x']) - center[0]
        dy = float(r['y']) - center[1]
        dz = float(r['z']) - center[2]
        d2 = dx * dx + dy * dy + dz * dz
        if d2 > radius:
            radius = d2
    return center, radius ** 0.5


def coords_of(object_name):
    """Per-atom world-frame coordinates -> [(id, x, y, z), ...].

    ONE ``iterate_state(1, ...)`` pass, sorted by atom id -- the
    pose-assertion helper (research §6.2): snapshot, transform, snapshot,
    compare per atom (after[i] == before[i] + delta for translation,
    after[i] == R.before[i] + t for rotation). Assert COORDINATES --
    never ``get_object_matrix`` (non-identity after bakes; it is the
    coordinate history).
    """
    rows = []
    cmd.iterate_state(1, object_name, 'stored.append((ID, x, y, z))',
                      space={'stored': rows})
    return sorted((int(ID), float(x), float(y), float(z))
                  for (ID, x, y, z) in rows)


def centroid_of(object_name):
    """Atom-count mean of the object's state-1 coordinates -> (cx, cy, cz).

    One ``coords_of`` pass reused (no second walk). Used to center
    placements (translate by slot - centroid) and in pose assertions.
    """
    coords = coords_of(object_name)
    if not coords:
        raise ValueError(
            'geometry.centroid_of: object %r has no atoms in state 1'
            % (object_name,))
    n = len(coords)
    cx = sum(c[1] for c in coords) / n
    cy = sum(c[2] for c in coords) / n
    cz = sum(c[3] for c in coords) / n
    return (cx, cy, cz)
