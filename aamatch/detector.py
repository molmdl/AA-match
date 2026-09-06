"""aamatch.detector -- pure-layer detection pipeline (plans 02-06/02-07).

Layer: PURE. Consumes plain atom records + the ligand bond block, returns
plain canonical result records. The detector NEVER reads PyMOL state:
coordinates are the final composed world-frame values the caller passes
(matrix composition is the caller's job -- PITFALLS 12); state semantics
are "state 1 only, the state the caller gave me" (game objects are
single-state by design); the camera frame never enters.

CHEMISTRY POLICY (detection research §7, human-approved with the DETECT-03
gate document on 2026-09-06; the docstring is the policy carrier):

1. WATERS EXCLUDED ENTIRELY. The cmd-tier extraction collects only game
   objects (grid AAs + ligand); demo structures are stripped of waters
   before bundling; no water-bridge type in v1 (EXT-01 deferred). Here the
   policy is structural: records carry side 'aa' or 'lig' and anything
   else fails closed (ValueError) -- a water can never silently join a
   detection. PLIP precedent: all-water metal complexes are skipped even
   there.
2. ALT-CONF: keep alt ''/'A' only (``apply_altloc_policy``, applied
   before typing, unit-tested). Ligands come from SDF/MOL2 (no altlocs)
   and grid AAs from bundled fragments (no altlocs), so this is defensive;
   NEVER "best-scoring conformer" (nondeterministic). Precedent: PLIP
   ships ALTLOC = False.
3. FAIL-CLOSED DONOR TYPING. An O/N/S without an attached H is NOT a
   donor -- ligand side via the bond block, AA side via proximity to a
   materialized polar H (AA_H_ATTACH_MAX below). Rationale: BINANA
   documents that guessing protonation degrades accuracy; a guessed-H
   detector that fires wrong H-bonds is worse for a teaching game than
   one that misses marginal ones. The shared capability tables keep
   generator capability and detector typing consistent, so fail-closed
   cannot create unsolvable levels.
4. STATE 1 ONLY / caller-owned frames: see the header above.
5. METAL GATING PREVIEW (02-07b finishes the type): metal coordination
    will run only when a ligand-side element is in the approved list
   (capability.METAL_ELEMENTS / capability.ligand_has_metal, gate §5
   item 5) so the generator can never require metal on a metal-free
   ligand. Ligand metal atoms are precomputed here as features.
6. COVALENT EXCLUSIONS. Enumeration is strictly CROSS-SIDE (aa x lig), so
   an intra-side covalent pair is unrepresentable by construction; the
   AA side carries no bond block, and identical atom ids are excluded.
   Cross-side pairs at or below MIN_DIST are rejected (row 10). Covalent
   ligand interactions are out of scope per REQUIREMENTS.md.
7. MIN_DIST 0.5 A GLOBAL (thresholds.MIN_DIST): every pair distance must
   exceed it -- cheap guard against coincident/duplicate atoms.

TYPING POLICY (all consumed from aamatch.capability -- THE single typing
home, gate §4.2; no parallel matrix lives here):

- D1 SIDE-CHAIN-ONLY (gate §4.1): AA-side donor/acceptor atoms are only
  the capability table's donors/acceptors (side-chain-scoped names);
  backbone and cap atoms are never typed. The AA-side hydrophobic rule is
  residue-NAME-based (gate §3.4 pedagogical set); its enumerated atoms
  are the side-chain carbons INCLUDING CB -- CB is the universal
  side-chain anchor that capability's side_chain sets deliberately omit
  (they list atoms "beyond CB"; ALA/GLY carry empty sets), while the
  backbone set N/CA/C/O/OXT stays untyped.
- Donor-H pairing on the AA side is GEOMETRIC (H within
  AA_H_ATTACH_MAX = 1.5 A of the donor heavy; X-H covalent lengths are
  <= ~1.36 A for S-H, so 1.5 carries margin). This is a typing-internal
  pairing epsilon, NOT a detection threshold from the gate table, chosen
  so naming variants (e.g. chempy's digit-prefixed '2HE' ring H on HIS)
  still pair -- SMOKE-03 (02-13) field-verifies the names themselves.
- Ligand charge-group centers follow gate §2.3: ammonium N (center = N),
  carboxylate (center = midpoint of the two Os), guanidino. The signs
  are the SAME predicates capability._charge_signs uses, and
  tests/test_detector.py pins sign parity with capability.ligand_profile
  for every ligand shape (DETECT-04 by construction). Ligand-side
  phosphate/sulfonate groups (gate §2.3 rows) are NOT typed in v1 --
  capability does not type them either; adding them is a versioned
  capability change so generator and detector never disagree.
- Guanidino center note: gate §2.3's ligand row says "midpoint of 2 Ns"
  (written for the protein-side Arg pattern, where the chain anchors NE).
  An isolated ligand guanidinium has three equivalent Ns and no chain
  anchor, so no terminal pair is definable from the bond block; the
  symmetric centroid of the bonded Ns is used. Revisiting this is a
  DETECTOR_VERSION event (gate §4.7), never a silent edit.
- ONE RECORD PER CONTACT: h_bond emits one record per (donor heavy,
   acceptor) pair, represented by the attached H with the largest
   D-H...A angle (ties -> lowest H id) -- two Hs on one donor (LYS NZ)
   are one physical contact, not two. Donor-uniqueness ACROSS different
   donors is intentionally NOT deduped (recorded gate §2.4 deviation:
   those rules change counts, not presence; fraction scoring is
   presence-based). Hydrophobic emits one binary-presence record per
   (AA object, ligand) whose atom_ids are the contacted carbon sets
   (row 5 ">= 1 pair of qualifying carbons"). The ring-geometry types
   (plan 02-07) emit one record per qualifying (AA ring, ligand ring)
   pair (pi_stacking) or per qualifying (charge group, ring) pair in
   each direction (cation_pi) -- both are feature-level contacts, and
   the cation_pi direction/sub-role is recorded in metrics per D4.
- Ligand rings precomputed here are AROMATIC rings only (rows 3-4 are
  aromatic-ring interactions; capability.ligand_profile counts the same
  set). Row-9 geometry: center = mean of ring atoms, normal = plane
  normal of the first/third/fifth atoms of the canonical ring walk,
  radius = max(center->atom); a degenerate (non-planar-samplable) ring
  is skipped, never guessed.
- 'unclassified_aa_atoms': count of NON-HYDROGEN AA atoms whose names
  are neither in the capability side_chain set nor in the known
  backbone/anchor set {N, CA, C, O, OXT, CB}. Game fragments score zero
  (pinned by test); SMOKE-03 (02-13) asserts zero on the MATERIALIZED
  geometry and reconciles any cap-atom naming there -- in capability.py,
  never silently here.

PIPELINE (detection research §5.2; the DETECT-05 two-level pruning):

1. extract_features -- typed features computed ONCE per detect (donor-H
   pairs, acceptors, charge-group centers, rings with center/normal/
   radius, hydrophobes, halogen donors, metals; per-AA side-chain
   features). No per-pair recomputation of centroids/normals.
2. AA bounding-sphere prefilter (_aa_bounding_spheres + the ligand
   sphere inflated by thresholds.AA_PREFILTER_MARGIN) -- far AAs are
   pruned before any pair math.
3. spatial.cross_pairs over (near-AA side-chain atoms) x (ligand typed
   atoms) is the ONLY atom-level candidate source -- cell size == the
   shared cutoff keeps the 3x3x3 neighbourhood scan provably exhaustive
   (tests/test_spatial.py). Charge/ring FEATURE pairs are enumerated
   directly (tiny counts).
4. Per-candidate constant-time tests run the approved rows from
   aamatch.thresholds -- never an inlined number.
5. Records are sorted canonically by (INTERACTION_TYPES position,
   aa object, aa atom_ids, lig atom_ids); identical input gives an
   identical list (determinism pinned by test, including AA record
   order permutation).

detect_part1 runs five of the seven types (h_bond, salt_bridge,
pi_stacking, cation_pi, hydrophobic) through the shared pipeline; the
02-07 split (2026-09-06) put the two ring-geometry types here, and
plan 02-07b adds halogen + metal on the same features/candidates and
wraps the full 7-type detect().

Dependency direction: math + pure vec3/spatial/capability/thresholds +
setup_state.INTERACTION_TYPES (the ONE enum home, canonical type order).
NO numpy, NO itertools (recorded 02-01 convention: explicit loops and
comprehensions only), no pymol.
"""

import math

from .vec3 import (add, angle_at, cross, dist, norm_squared,
                   plane_project, scale, sub, unit)
from .spatial import cross_pairs
from .capability import (
    AA_RESIDUES,
    METAL_ELEMENTS,
    _adjacency,
    _all_single_bonds,
    _elem,
    _find_rings,
    _formal_charge,
    _HALOGEN_DONOR_ELEMS,
    _has_h_neighbor,
    _HYDROPHOBE_NEIGHBOR_ELEMS,
    _order_lookup,
    _POLAR_ELEMS,
    _ring_aromatic,
)
from .thresholds import (
    AA_PREFILTER_MARGIN,
    CATIONPI_D_MAX,
    CATIONPI_OFFSET_MAX,
    HALOGEN_D_MAX,
    HBOND_ANGLE_MIN_DEG,
    HBOND_D_MAX,
    HYDRO_D_MAX,
    METAL_D_MAX,
    MIN_DIST,
    PISTACK_ANGLE_TOL_DEG,
    PISTACK_CENTER_D_MAX,
    PISTACK_OFFSET_MAX,
    SALT_CENTER_D_MAX,
)
from .setup_state import INTERACTION_TYPES

# Canonical type order = the ONE enum home's order (plan 02-06 Task 3).
_TYPE_ORDER = dict((t, i) for i, t in enumerate(INTERACTION_TYPES))

# AA-side donor-H pairing epsilon (typing-internal, see docstring item on
# geometric pairing; X-H covalent <= ~1.36 A S-H, so 1.5 carries margin).
AA_H_ATTACH_MAX = 1.5

# Origin vertex for angle_at()-based vector angles (normal-vs-normal).
_ORIGIN = (0.0, 0.0, 0.0)

# Known NON-side-chain heavy atom names: the standard backbone plus OXT
# plus CB (the universal side-chain anchor). Anything else heavy is
# counted by features['unclassified_aa_atoms'] for SMOKE-03.
_KNOWN_NON_SIDE_CHAIN = frozenset(('N', 'CA', 'C', 'O', 'OXT', 'CB'))

# Shared atom-level candidate cutoff: the max distance criterion that
# applies to ATOM pairs (rows 1/5/6/7; pi/cation-pi are feature-level).
# cross_pairs derives its cell size FROM this cutoff (cell == cutoff).
_PAIR_CUTOFF = max(HBOND_D_MAX, HYDRO_D_MAX, HALOGEN_D_MAX, METAL_D_MAX)


def apply_altloc_policy(atoms):
    """Chemistry policy item 2: keep alt ''/'A' (or missing), drop other
    altlocs, order-preserving. Never best-scoring-conformer."""
    kept = []
    for atom in atoms:
        alt = atom.get('alt') or ''
        if alt in ('', 'A'):
            kept.append(atom)
    return kept


def _pos(record):
    """(x, y, z) as plain floats (vec3 floats-in/floats-out contract)."""
    return (float(record['x']), float(record['y']), float(record['z']))


def _split_sides(atoms):
    """Partition records into (aa_records, lig_records); anything that is
    not side 'aa' or 'lig' fails closed (policy item 1)."""
    aa_recs = []
    lig_recs = []
    for atom in atoms:
        side = atom.get('side')
        if side == 'aa':
            aa_recs.append(atom)
        elif side == 'lig':
            lig_recs.append(atom)
        else:
            raise ValueError(
                'detector: atom record %r carries side %r -- only '
                "'aa' and 'lig' game objects are detected (waters/"
                'cofactors never reach the detector)' % (atom.get('id'),
                                                         side))
    return aa_recs, lig_recs


def _validate_ligand_bonds(lig_recs, ligand_bonds):
    """Every bond index must address the ligand subsequence (fail-closed
    input validation; silent index drift would corrupt every feature)."""
    n = len(lig_recs)
    for bond in ligand_bonds:
        i, j = int(bond[0]), int(bond[1])
        if not (0 <= i < n) or not (0 <= j < n):
            raise ValueError(
                'detector: ligand bond (%r, %r) out of range for %d '
                'ligand atoms -- ligand_bonds must index the ligand-side '
                'atoms in their given order' % (i, j, n))


def _mean_point(records):
    """Mean of the records' positions (row-9 centers, group centers)."""
    n = len(records)
    sx = sy = sz = 0.0
    for record in records:
        sx += float(record['x'])
        sy += float(record['y'])
        sz += float(record['z'])
    return (sx / n, sy / n, sz / n)


def _bounding_sphere(records):
    """(center, radius) with radius = max(center -> atom); None if empty."""
    if not records:
        return None
    center = _mean_point(records)
    radius = 0.0
    for record in records:
        d = dist(center, _pos(record))
        if d > radius:
            radius = d
    return (center, radius)


def _ring_geometry(recs):
    """Row-9 geometry for one ring (records in canonical walk order):
    center = mean; normal = unit normal of the first/third/fifth-atom
    plane; radius = max(center -> atom). Returns None when the three
    plane atoms are collinear (degenerate -- skipped, never guessed)."""
    center = _mean_point(recs)
    p0 = _pos(recs[0])
    p2 = _pos(recs[2])
    p4 = _pos(recs[4])
    normal = cross(sub(p2, p0), sub(p4, p0))
    if norm_squared(normal) == 0.0:
        return None
    normal = unit(normal)
    radius = 0.0
    for record in recs:
        d = dist(center, _pos(record))
        if d > radius:
            radius = d
    return {'center': center, 'normal': normal, 'radius': radius,
            'atom_ids': [int(r['id']) for r in recs]}


def _ligand_features(lig_recs, ligand_bonds):
    """Ligand-side typed features, computed ONCE (research §5.2.1).

    Atom-level entries are (index, record) tuples; indices address the
    ligand subsequence in its given order (the SDF bond block maps
    directly). The typing predicates are capability's -- consumed, never
    re-written (single typing home, DETECT-04)."""
    adjacency = _adjacency(lig_recs, ligand_bonds)
    order_lookup = _order_lookup(ligand_bonds)
    elements = [_elem(a) for a in lig_recs]

    donor_pairs = []
    donor_hs = {}
    acceptors = []
    hydrophobes = []
    halogen_donors = []
    metals = []
    for idx, elem in enumerate(elements):
        neighbors = adjacency.get(idx, ())
        if elem in _POLAR_ELEMS:
            acceptors.append((idx, lig_recs[idx]))
            if _has_h_neighbor(idx, elements, adjacency):
                for j in neighbors:
                    if elements[j] == 'H':
                        donor_pairs.append(
                            ((idx, lig_recs[idx]), (j, lig_recs[j])))
                        donor_hs.setdefault(idx, []).append(
                            (j, lig_recs[j]))
        if elem == 'C' \
                and set(elements[j] for j in neighbors) \
                <= _HYDROPHOBE_NEIGHBOR_ELEMS:
            hydrophobes.append((idx, lig_recs[idx]))
        if elem in _HALOGEN_DONOR_ELEMS:
            for j in neighbors:
                if elements[j] == 'C':
                    halogen_donors.append(
                        ((idx, lig_recs[idx]), (j, lig_recs[j])))
        if elem in METAL_ELEMENTS:
            metals.append((idx, lig_recs[idx]))

    rings = []
    for ring in _find_rings(adjacency):
        if _ring_aromatic(ring, order_lookup, lig_recs):
            geometry = _ring_geometry([lig_recs[i] for i in ring])
            if geometry is not None:
                rings.append(geometry)

    return {
        'atoms': list(lig_recs),
        'donor_pairs': donor_pairs,
        'donor_hs': donor_hs,
        'acceptors': acceptors,
        'hydrophobes': hydrophobes,
        'charge_groups': _ligand_charge_groups(lig_recs, elements,
                                               adjacency, order_lookup),
        'rings': rings,
        'halogen_donors': halogen_donors,
        'metals': metals,
        'sphere': _bounding_sphere(lig_recs),
    }


def _ligand_charge_groups(lig_recs, elements, adjacency, order_lookup):
    """Ligand charge groups (gate §2.3 ligand side) with centers, using
    the SAME predicates as capability._charge_signs (parity pinned by
    test): ammonium N+ (center = N), carboxylate - (midpoint of the two
    Os), guanidino + (centroid of the bonded Ns -- see module docstring).
    Phosphate/sulfonate are NOT typed in v1 (capability parity).

    Ammonium groups also carry 'substituents' -- the N's non-H neighbor
    positions, consumed ONLY by the OQ-4 cation-pi anti-artifact veto
    (a substituent-plane normal exists iff there are exactly three:
    PLIP's tertamine; quaternary ammonium and primary/secondary amines
    are never veto subjects)."""
    groups = []
    for idx, elem in enumerate(elements):
        neighbors = adjacency.get(idx, ())
        if elem == 'N':
            fc = _formal_charge(lig_recs[idx])
            ammonium = len(neighbors) == 4 \
                and _all_single_bonds(idx, neighbors, order_lookup) \
                and _has_h_neighbor(idx, elements, adjacency)
            if (fc is not None and fc > 0) or ammonium:
                groups.append({'sign': '+', 'kind': 'ammonium',
                               'center': _pos(lig_recs[idx]),
                               'atom_ids': [int(lig_recs[idx]['id'])],
                               'substituents': tuple(
                                   _pos(lig_recs[j]) for j in neighbors
                                   if elements[j] != 'H')})
        elif elem == 'C':
            o_neighbors = [j for j in neighbors if elements[j] == 'O']
            n_neighbors = [j for j in neighbors if elements[j] == 'N']
            if len(o_neighbors) == 2 \
                    and not any(_has_h_neighbor(j, elements, adjacency)
                                for j in o_neighbors):
                charges = [_formal_charge(lig_recs[j]) for j in o_neighbors]
                known = [c for c in charges if c is not None]
                if not known or any(c < 0 for c in known):
                    o_recs = [lig_recs[j] for j in o_neighbors]
                    center = scale(add(_pos(o_recs[0]), _pos(o_recs[1])),
                                   0.5)
                    groups.append({'sign': '-', 'kind': 'carboxylate',
                                   'center': center,
                                   'atom_ids': sorted(
                                       int(r['id']) for r in o_recs)})
            if len(n_neighbors) == 3:
                n_recs = [lig_recs[j] for j in n_neighbors]
                groups.append({'sign': '+', 'kind': 'guanidino',
                               'center': _mean_point(n_recs),
                               'atom_ids': sorted(
                                   int(r['id']) for r in n_recs)})
    return groups


def _aa_features(aa_recs):
    """Per-AA-object side-chain features (D1). One residue per object is
    the game contract (one fragment per grid object); resn/resi come from
    the object's first record. Internal iteration is NAME-SORTED so float
    summation order is independent of the caller's record order."""
    grouped = {}
    for record in aa_recs:
        grouped.setdefault(record['object'], []).append(record)

    features = {}
    unclassified = 0
    for obj in sorted(grouped):
        recs = grouped[obj]
        by_name = dict((r['name'], r) for r in recs)
        resn = recs[0]['resn']
        resi = int(recs[0]['resi'])
        entry = AA_RESIDUES.get(resn)
        feat = {'resn': resn, 'resi': resi, 'atoms': list(recs),
                'side_chain': [], 'donor_pairs': [], 'donor_map': {},
                'acceptors': [], 'charge': {'sign': None, 'center': None,
                                            'atom_ids': []},
                'rings': [], 'hydrophobic': False,
                'hydrophobic_carbons': []}
        if entry is None:
            # Unknown residue: no typing at all; every heavy atom counts
            # as unclassified (fail-closed, SMOKE-03 visible).
            for record in recs:
                if _elem(record) != 'H':
                    unclassified += 1
            features[obj] = feat
            continue

        side_names = sorted(entry['side_chain'])
        side_recs = [by_name[n] for n in side_names if n in by_name]
        feat['side_chain'] = side_recs

        # Donor-H pairs: fail-closed -- only listed donor names, and only
        # when a materialized polar H sits within AA_H_ATTACH_MAX.
        heavy_h = [r for r in recs if _elem(r) == 'H']
        for donor_name in entry['donors']:
            if donor_name not in by_name:
                continue
            heavy = by_name[donor_name]
            attached = []
            for h_rec in sorted(heavy_h, key=lambda r: r['name']):
                if dist(_pos(heavy), _pos(h_rec)) <= AA_H_ATTACH_MAX:
                    attached.append(h_rec)
            for h_rec in attached:
                feat['donor_pairs'].append((heavy, h_rec))
            if attached:
                feat['donor_map'][donor_name] = attached

        feat['acceptors'] = [by_name[n] for n in sorted(entry['acceptors'])
                             if n in by_name]

        # Charge group: midpoint/center of the table's representative
        # atoms (gate §2.3 protein side). Partial atoms -> no center
        # (fail-closed; no salt candidates from a broken fragment).
        sign, charge_names = entry['charge']
        if sign is not None:
            charge_recs = [by_name[n] for n in charge_names
                           if n in by_name]
            if len(charge_recs) == len(charge_names):
                feat['charge'] = {'sign': sign,
                                  'center': _mean_point(charge_recs),
                                  'atom_ids': sorted(
                                      int(r['id']) for r in charge_recs)}

        # Rings: capability's atom-name walks, row-9 geometry.
        for walk in entry['rings']:
            if all(name in by_name for name in walk):
                geometry = _ring_geometry([by_name[n] for n in walk])
                if geometry is not None:
                    feat['rings'].append(geometry)

        feat['hydrophobic'] = bool(entry['hydrophobic'])
        # Side-chain carbons INCLUDING CB (the universal anchor) -- used
        # only when the residue is in the pedagogical hydrophobic set.
        carbon_names = sorted(set(entry['side_chain']) | set(('CB',)))
        feat['hydrophobic_carbons'] = [by_name[n] for n in carbon_names
                                       if n in by_name
                                       and _elem(by_name[n]) == 'C']

        for record in recs:
            if _elem(record) == 'H':
                continue
            if record['name'] in entry['side_chain']:
                continue
            if record['name'] in _KNOWN_NON_SIDE_CHAIN:
                continue
            unclassified += 1
        features[obj] = feat

    return features, unclassified


def extract_features(atom_records, ligand_bonds):
    """Typed features for one detection pass, computed ONCE.

    Input: atom records (detection research §5.1 shape: side/object/id/
    name/elem/resn/resi/alt/x/y/z, optional formal_charge) + the ligand
    bond block [(i, j, order)] with 0-based indices into the LIGAND-side
    atoms in their given order (the SDF/MOL2 bond block maps directly).
    The altloc policy is applied first; bond indices are validated
    fail-closed.

    Returns:
    {
      'aa':   {object: {'resn','resi','atoms','side_chain','donor_pairs',
                        'donor_map','acceptors','charge','rings',
                        'hydrophobic','hydrophobic_carbons'}},
      'lig':  {'atoms','donor_pairs','donor_hs','acceptors','hydrophobes',
               'charge_groups','rings','halogen_donors','metals','sphere'},
      'unclassified_aa_atoms': int,
    }
    """
    atoms = apply_altloc_policy(atom_records)
    aa_recs, lig_recs = _split_sides(atoms)
    _validate_ligand_bonds(lig_recs, ligand_bonds)
    aa_features, unclassified = _aa_features(aa_recs)
    return {
        'aa': aa_features,
        'lig': _ligand_features(lig_recs, ligand_bonds),
        'unclassified_aa_atoms': unclassified,
    }


def _aa_bounding_spheres(aa_features):
    """Coarse AA-level prefilter spheres: per object, center = centroid of
    its atoms, radius = max(center -> atom) (research §5.2.2). Returns
    {object: (center, radius)} in sorted object order."""
    spheres = {}
    for obj in sorted(aa_features):
        sphere = _bounding_sphere(aa_features[obj]['atoms'])
        if sphere is not None:
            spheres[obj] = sphere
    return spheres


def _prefilter_pass(features):
    """Objects whose bounding sphere intersects the ligand sphere inflated
    by thresholds.AA_PREFILTER_MARGIN (research §5.2.2). Sufficiency: all
    feature centers lie inside their side's sphere, so an interacting
    feature pair at d <= MAX_CUTOFF implies center distance <=
    r_aa + r_lig + MAX_CUTOFF <= r_aa + r_lig + AA_PREFILTER_MARGIN."""
    lig_sphere = features['lig']['sphere']
    if lig_sphere is None:
        return []
    lig_center, lig_radius = lig_sphere
    near = []
    for obj, (center, radius) in sorted(
            _aa_bounding_spheres(features['aa']).items()):
        if dist(center, lig_center) <= radius + lig_radius \
                + AA_PREFILTER_MARGIN:
            near.append(obj)
    return near


def _flat_donor_pairs(donor_pairs):
    """((d_idx, d_rec), (h_idx, h_rec)) -> (d_idx, d_rec, h_idx, h_rec)."""
    return [(d_idx, d_rec, h_idx, h_rec)
            for (d_idx, d_rec), (h_idx, h_rec) in donor_pairs]


def _ligand_context(features):
    """Index sets the classifiers need, built once: acceptor / donor-heavy
    / hydrophobe / halogen-X / metal index sets + per-donor H lists."""
    lig = features['lig']
    acceptor_idx = set(idx for idx, rec in lig['acceptors'])
    donor_heavy_idx = set(idx for idx, rec, h_idx, h_rec
                          in _flat_donor_pairs(lig['donor_pairs']))
    donor_hs = {}
    for (d_idx, d_rec), (h_idx, h_rec) in lig['donor_pairs']:
        donor_hs.setdefault(d_idx, []).append((h_idx, h_rec))
    hydrophobe_idx = set(idx for idx, rec in lig['hydrophobes'])
    halogen_idx = set(x_idx for (x_idx, x_rec), (c_idx, c_rec)
                      in lig['halogen_donors'])
    metal_idx = set(idx for idx, rec in lig['metals'])
    return {'acceptor_idx': acceptor_idx,
            'donor_heavy_idx': donor_heavy_idx,
            'donor_hs': donor_hs,
            'hydrophobe_idx': hydrophobe_idx,
            'halogen_idx': halogen_idx,
            'metal_idx': metal_idx}


def _pair_atoms(features, obj):
    """The AA-side atoms that join the cell-list candidate enumeration:
    side-chain heavy atoms plus CB (the hydrophobic anchor). Side-chain
    polar Hs are excluded -- their positions ride along via donor_map."""
    feat = features['aa'][obj]
    names = set(r['name'] for r in feat['side_chain'])
    for rec in feat['hydrophobic_carbons']:
        names.add(rec['name'])
    recs = []
    for rec in sorted(feat['atoms'], key=lambda r: r['name']):
        if rec['name'] in names and _elem(rec) != 'H':
            recs.append(rec)
    return recs


def _atom_candidate_pairs(features, near_objs):
    """THE candidate source (research §5.2.3): spatial.cross_pairs over
    (near-AA side-chain atoms) x (ligand typed atoms) at the shared
    atom-level cutoff. No full atom-set double loop exists anywhere.

    Returns [(aa_rec, lig_idx, lig_rec, dist)] sorted by cross_pairs'
    canonical pair order."""
    a_pts = []
    a_refs = []
    for obj in near_objs:
        for rec in _pair_atoms(features, obj):
            a_pts.append(_pos(rec))
            a_refs.append(rec)

    lig = features['lig']
    typed_idx = set()
    typed_idx.update(idx for idx, rec in lig['acceptors'])
    typed_idx.update(idx for idx, rec in lig['hydrophobes'])
    typed_idx.update(idx for idx, rec in lig['metals'])
    for (x_idx, x_rec), (c_idx, c_rec) in lig['halogen_donors']:
        typed_idx.add(x_idx)
    for d_idx, d_rec, h_idx, h_rec in _flat_donor_pairs(lig['donor_pairs']):
        typed_idx.add(d_idx)
    lig_atoms = lig['atoms']
    b_pts = []
    b_entries = []
    for idx in sorted(typed_idx):
        b_pts.append(_pos(lig_atoms[idx]))
        b_entries.append((idx, lig_atoms[idx]))

    pairs = cross_pairs(a_pts, b_pts, _PAIR_CUTOFF)
    candidates = []
    for i, j in pairs:
        aa_rec = a_refs[i]
        lig_idx, lig_rec = b_entries[j]
        candidates.append((aa_rec, lig_idx, lig_rec,
                           dist(_pos(aa_rec), _pos(lig_rec))))
    return candidates


def _aa_contexts(features, near_objs):
    """Per-object classifier context, built once for the near AAs."""
    contexts = {}
    for obj in near_objs:
        feat = features['aa'][obj]
        contexts[obj] = {
            'feat': feat,
            'donor_map': feat['donor_map'],
            'acceptor_names': set(r['name'] for r in feat['acceptors']),
            'hydrophobic': feat['hydrophobic'],
            'hydro_carbon_names': set(r['name'] for r
                                      in feat['hydrophobic_carbons']),
        }
    return contexts


def _record(type_, aa_obj, aa_resn, aa_resi, aa_role, aa_ids,
            lig_obj, lig_role, lig_ids, metrics):
    """Canonical record shape (detection research §4)."""
    return {
        'type': type_,
        'aa': {'object': aa_obj, 'atom_ids': sorted(int(i) for i in aa_ids),
               'resn': aa_resn, 'resi': int(aa_resi), 'role': aa_role},
        'lig': {'object': lig_obj, 'atom_ids': sorted(int(i) for i in lig_ids),
                'role': lig_role},
        'metrics': metrics,
        'formed': True,
    }


def _lig_object_name(features):
    """The ligand object name (game contract: exactly one ligand object)."""
    atoms = features['lig']['atoms']
    return atoms[0]['object'] if atoms else 'ligand'


def _h_bond_records(features, near_objs, lig_ctx, atom_pairs):
    """Row 1: D...A <= HBOND_D_MAX AND angle at H >= HBOND_ANGLE_MIN_DEG,
    both directions (AA donor / AA acceptor) with explicit roles; one
    record per (donor heavy, acceptor) with the best-angle H."""
    contexts = _aa_contexts(features, near_objs)
    # best[(side, donor_id, acceptor_id)] = (angle, h_id, record pieces)
    best = {}
    for aa_rec, lig_idx, lig_rec, d in atom_pairs:
        if d <= MIN_DIST or d > HBOND_D_MAX:
            continue
        ctx = contexts.get(aa_rec['object'])
        if ctx is None:
            continue
        aa_name = aa_rec['name']
        # AA side DONATES: aa donor heavy (+ its attached H) -> lig acceptor
        if aa_name in ctx['donor_map'] and lig_idx in lig_ctx['acceptor_idx']:
            for h_rec in ctx['donor_map'][aa_name]:
                angle = math.degrees(
                    angle_at(_pos(aa_rec), _pos(h_rec), _pos(lig_rec)))
                if angle < HBOND_ANGLE_MIN_DEG:
                    continue
                key = ('aa_d', aa_rec['id'], lig_rec['id'])
                cand = (angle, h_rec['id'])
                if key not in best or _better_h(cand, best[key]):
                    best[key] = (cand, aa_rec, lig_rec, h_rec, d, 'aa_d')
        # AA side ACCEPTS: lig donor heavy (+ H) -> aa acceptor
        if aa_name in ctx['acceptor_names'] \
                and lig_idx in lig_ctx['donor_heavy_idx']:
            for h_idx, h_rec in lig_ctx['donor_hs'].get(lig_idx, ()):
                angle = math.degrees(
                    angle_at(_pos(lig_rec), _pos(h_rec), _pos(aa_rec)))
                if angle < HBOND_ANGLE_MIN_DEG:
                    continue
                key = ('lig_d', aa_rec['id'], lig_rec['id'])
                cand = (angle, h_idx)
                if key not in best or _better_h(cand, best[key]):
                    best[key] = (cand, aa_rec, lig_rec, h_rec, d, 'lig_d')

    records = []
    for key in sorted(best):
        cand, aa_rec, lig_rec, h_rec, d, side = best[key]
        angle = cand[0]
        if side == 'aa_d':
            records.append(_record(
                'h_bond', aa_rec['object'], aa_rec['resn'], aa_rec['resi'],
                'donor', [aa_rec['id'], h_rec['id']],
                lig_rec['object'], 'acceptor', [lig_rec['id']],
                {'d_da': d, 'angle_deg': angle}))
        else:
            records.append(_record(
                'h_bond', aa_rec['object'], aa_rec['resn'], aa_rec['resi'],
                'acceptor', [aa_rec['id']],
                lig_rec['object'], 'donor', [lig_rec['id'], h_rec['id']],
                {'d_da': d, 'angle_deg': angle}))
    return records


def _better_h(candidate, incumbent):
    """Largest angle wins; ties -> lowest H id (deterministic)."""
    cand_angle, cand_h = candidate
    inc_angle, inc_h = incumbent[0]
    if cand_angle != inc_angle:
        return cand_angle > inc_angle
    return cand_h < inc_h


def _salt_bridge_records(features, near_objs):
    """Row 2: opposite charge-GROUP centers <= SALT_CENTER_D_MAX (gate
    §2.3 center definitions; polarity per D3 -- same sign never pairs).
    Feature pairs enumerated directly (tiny counts, no cell list)."""
    records = []
    lig_groups = features['lig']['charge_groups']
    for obj in near_objs:
        aa_charge = features['aa'][obj]['charge']
        aa_sign = aa_charge['sign']
        if aa_sign is None or aa_charge['center'] is None:
            continue
        aa_feat = features['aa'][obj]
        for group in lig_groups:
            if group['sign'] == aa_sign:
                continue                       # D3: opposite charges only
            d = dist(aa_charge['center'], group['center'])
            if d <= MIN_DIST or d > SALT_CENTER_D_MAX:
                continue
            records.append(_record(
                'salt_bridge', obj, aa_feat['resn'], aa_feat['resi'],
                'cation' if aa_sign == '+' else 'anion',
                aa_charge['atom_ids'],
                _lig_object_name(features),
                'cation' if group['sign'] == '+' else 'anion',
                group['atom_ids'],
                {'d_center': d}))
    return records


def _hydrophobic_records(features, near_objs, lig_ctx, atom_pairs):
    """Row 5: >= 1 pair of qualifying carbons within HYDRO_D_MAX -- binary
    presence per (AA object, ligand). The AA side is residue-NAME-based
    (gate §3.4): its atoms are the side-chain carbons incl. CB; the
    ligand side applies the atom rule (features['lig']['hydrophobes'])."""
    contexts = _aa_contexts(features, near_objs)
    contacts = {}
    for aa_rec, lig_idx, lig_rec, d in atom_pairs:
        if d <= MIN_DIST or d > HYDRO_D_MAX:
            continue
        ctx = contexts.get(aa_rec['object'])
        if ctx is None or not ctx['hydrophobic']:
            continue
        if aa_rec['name'] not in ctx['hydro_carbon_names']:
            continue
        if lig_idx not in lig_ctx['hydrophobe_idx']:
            continue
        contact = contacts.get(aa_rec['object'])
        if contact is None:
            contact = {'aa_ids': set(), 'lig_ids': set(), 'min_d': d}
            contacts[aa_rec['object']] = contact
        contact['aa_ids'].add(aa_rec['id'])
        contact['lig_ids'].add(lig_rec['id'])
        if d < contact['min_d']:
            contact['min_d'] = d

    records = []
    for obj in sorted(contacts):
        contact = contacts[obj]
        feat = features['aa'][obj]
        records.append(_record(
            'hydrophobic', obj, feat['resn'], feat['resi'], 'carbon',
            contact['aa_ids'], _lig_object_name(features), 'carbon',
            contact['lig_ids'], {'d_cc': contact['min_d']}))
    return records


def _normals_angle_deg(n1, n2):
    """Unsigned LINE angle between two unit normals in degrees, folded to
    [0, 90] via min(theta, 180 - theta) -- ring planes have no direction
    (PLIP detection.py pistacking/pication)."""
    theta = math.degrees(angle_at(n1, _ORIGIN, n2))
    if theta > 90.0:
        return 180.0 - theta
    return theta


def _pi_stacking_records(features, near_objs):
    """Row 3: ring-center dist < PISTACK_CENTER_D_MAX (strict) AND
    normals within PISTACK_ANGLE_TOL_DEG of parallel OR of perpendicular
    AND projected-center offset < PISTACK_OFFSET_MAX -- one uniform test
    covering both sub-geometries (gate §2.2 row 3); the sub-type P/T is
    recorded as a METRIC only (the reported type is always pi_stacking).
    Offset = min over the two cross-projections (each ring center into
    the opposite ring's plane), the PLIP pistacking form. Ring pairs are
    enumerated directly (tiny counts, no cell list)."""
    records = []
    lig_rings = features['lig']['rings']
    lig_obj = _lig_object_name(features)
    for obj in near_objs:
        feat = features['aa'][obj]
        for aa_ring in feat['rings']:
            for lig_ring in lig_rings:
                d = dist(aa_ring['center'], lig_ring['center'])
                if d <= MIN_DIST or d >= PISTACK_CENTER_D_MAX:
                    continue
                angle = _normals_angle_deg(aa_ring['normal'],
                                           lig_ring['normal'])
                if angle <= PISTACK_ANGLE_TOL_DEG:
                    subtype = 'P'
                elif angle >= 90.0 - PISTACK_ANGLE_TOL_DEG:
                    subtype = 'T'
                else:
                    continue
                offset = min(
                    dist(plane_project(aa_ring['center'],
                                       lig_ring['center'],
                                       lig_ring['normal']),
                         lig_ring['center']),
                    dist(plane_project(lig_ring['center'],
                                       aa_ring['center'],
                                       aa_ring['normal']),
                         aa_ring['center']))
                if offset >= PISTACK_OFFSET_MAX:
                    continue
                records.append(_record(
                    'pi_stacking', obj, feat['resn'], feat['resi'],
                    'ring', aa_ring['atom_ids'], lig_obj, 'ring',
                    lig_ring['atom_ids'],
                    {'d_center': d, 'angle_deg': angle, 'offset': offset,
                     'subtype': subtype}))
    return records


def _cation_pi_test(charge_center, ring):
    """Row 4 shared geometry: (d, offset) when the charge center lies
    within CATIONPI_D_MAX of the ring center (inclusive <=, per the
    thresholds row transcription) AND projects within CATIONPI_OFFSET_MAX
    of the ring center in the ring plane (strict <); None otherwise."""
    d = dist(charge_center, ring['center'])
    if d <= MIN_DIST or d > CATIONPI_D_MAX:
        return None
    projected = plane_project(charge_center, ring['center'],
                              ring['normal'])
    offset = dist(projected, ring['center'])
    if offset >= CATIONPI_OFFSET_MAX:
        return None
    return d, offset


def _substituent_plane_veto(group, ring):
    """OQ-4 (gate §4.4, PLIP ligand-side-only anti-artifact rule): when
    the LIGAND cation is a tertiary ammonium (exactly three non-H
    substituents on the single N), its substituent-plane normal must lie
    within PISTACK_ANGLE_TOL_DEG of the ring normal -- a larger angle is
    a 'pi-cation interaction through the ligand' and the hit is rejected
    (return True). The AA side has NO such veto (documented asymmetry);
    primary/secondary ammonium, quaternary ammonium, and guanidino
    ligand cations are not tertamines and never veto. A degenerate
    (collinear) substituent plane carries no normal and cannot veto."""
    if group['kind'] != 'ammonium':
        return False
    subs = group.get('substituents', ())
    if len(subs) != 3:
        return False
    normal = cross(sub(subs[1], subs[0]), sub(subs[2], subs[0]))
    if norm_squared(normal) == 0.0:
        return False
    return _normals_angle_deg(unit(normal), ring['normal']) \
        > PISTACK_ANGLE_TOL_DEG


def _cation_pi_records(features, near_objs):
    """Row 4: cation-pi in BOTH directions per D4 -- AA '+' charge-group
    center over a ligand ring, or ligand '+' group over an AA ring --
    with the direction recorded and the OQ-4 veto applied ONLY when the
    ligand carries the cation (documented asymmetry, gate §4.4)."""
    records = []
    lig_groups = features['lig']['charge_groups']
    lig_rings = features['lig']['rings']
    lig_obj = _lig_object_name(features)
    for obj in near_objs:
        feat = features['aa'][obj]
        aa_charge = feat['charge']
        if aa_charge['sign'] == '+' and aa_charge['center'] is not None:
            for lig_ring in lig_rings:
                test = _cation_pi_test(aa_charge['center'], lig_ring)
                if test is None:
                    continue
                d, offset = test
                records.append(_record(
                    'cation_pi', obj, feat['resn'], feat['resi'],
                    'cation', aa_charge['atom_ids'], lig_obj, 'ring',
                    lig_ring['atom_ids'],
                    {'d_center': d, 'offset': offset,
                     'direction': 'aa_cation_over_lig_ring'}))
        for group in lig_groups:
            if group['sign'] != '+':
                continue
            for aa_ring in feat['rings']:
                test = _cation_pi_test(group['center'], aa_ring)
                if test is None:
                    continue
                if _substituent_plane_veto(group, aa_ring):
                    continue
                d, offset = test
                records.append(_record(
                    'cation_pi', obj, feat['resn'], feat['resi'],
                    'ring', aa_ring['atom_ids'], lig_obj, 'cation',
                    group['atom_ids'],
                    {'d_center': d, 'offset': offset,
                     'direction': 'aa_ring_under_lig_cation'}))
    return records


def _canonical_sort(records):
    """Deterministic canonical order: (INTERACTION_TYPES position,
    aa object, aa atom_ids, lig atom_ids)."""
    return sorted(records, key=lambda r: (
        _TYPE_ORDER[r['type']],
        r['aa']['object'],
        tuple(r['aa']['atom_ids']),
        tuple(r['lig']['atom_ids'])))


def detect_part1(atom_records, ligand_bonds):
    """Detect five of the seven types (h_bond, salt_bridge, pi_stacking,
    cation_pi, hydrophobic) through the shared pipeline: features once
    -> AA bounding-sphere prefilter -> spatial.cross_pairs atom-level
    candidates (contact types) and direct feature-pair enumeration
    (charge-group and ring pairs) -> per-candidate row tests ->
    canonical records.

    Input/output contract: see extract_features and the module docstring
    (records carry explicit partner sides; identical input yields an
    identical list). The 02-07 split (2026-09-06) put the two ring-
    geometry types here; plan 02-07b adds halogen + metal on the same
    features/candidates and wraps the full 7-type detect().
    """
    features = extract_features(atom_records, ligand_bonds)
    if not features['lig']['atoms'] or not features['aa']:
        return []
    near_objs = _prefilter_pass(features)
    if not near_objs:
        return []
    lig_ctx = _ligand_context(features)
    atom_pairs = _atom_candidate_pairs(features, near_objs)
    records = []
    records.extend(_h_bond_records(features, near_objs, lig_ctx,
                                   atom_pairs))
    records.extend(_salt_bridge_records(features, near_objs))
    records.extend(_pi_stacking_records(features, near_objs))
    records.extend(_cation_pi_records(features, near_objs))
    records.extend(_hydrophobic_records(features, near_objs, lig_ctx,
                                        atom_pairs))
    return _canonical_sort(records)
