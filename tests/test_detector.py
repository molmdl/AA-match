"""Unit tests for aamatch.detector — pipeline core + 3 of 7 types (02-06).

Plan 02-06 scope: extract_features (typed features, computed ONCE), the
AA bounding-sphere prefilter, spatial.cross_pairs candidate enumeration,
and the h_bond / salt_bridge / hydrophobic tests with explicit partner
sides. Plan 02-07 extends this file with pi_stacking, cation_pi, halogen
and metal on the SAME pipeline — every geometry here is hand-placed and
runs under bare python3.6 with ZERO PyMOL (pure-layer contract).

All criteria asserted at scripted boundaries come from the APPROVED
DETECT-03 gate document (docs/DETECTION_THRESHOLDS.md, 2026-09-06) via
aamatch.thresholds — the tests never inline a cutoff.

Record contract (detection research §4): every record is
  {"type", "aa": {"object","atom_ids","resn","resi","role"},
   "lig": {"object","atom_ids","role"}, "metrics": {...}, "formed": True}
sorted canonically by (INTERACTION_TYPES position, aa object, aa atom_ids,
lig atom_ids); same input twice -> identical list.
"""

import math
import unittest

from aamatch import capability
from aamatch import detector
from aamatch.setup_state import INTERACTION_TYPES


# ---------------------------------------------------------------------------
# Scripted-geometry helpers (no PyMOL — plain atom records per detection
# research §5.1: side/object/id/name/elem/resn/resi/alt/x/y/z).
# ---------------------------------------------------------------------------

def _lig_atom(idx, name, elem, x, y, z, fc=None):
    """Ligand-side atom record; id == ligand-sublist index for clarity."""
    record = {'side': 'lig', 'object': 'ligand', 'id': idx, 'name': name,
              'elem': elem, 'resn': 'LIG', 'resi': 1, 'alt': '',
              'x': float(x), 'y': float(y), 'z': float(z)}
    if fc is not None:
        record['formal_charge'] = fc
    return record


def _aa_atom(obj, idx, name, elem, resn, resi, x, y, z):
    """AA-side atom record (grid amino acid object, one residue per object)."""
    return {'side': 'aa', 'object': obj, 'id': idx, 'name': name,
            'elem': elem, 'resn': resn, 'resi': resi, 'alt': '',
            'x': float(x), 'y': float(y), 'z': float(z)}


def _h_pos(donor, acceptor, r, angle_deg):
    """Position for an H at distance ``r`` from ``donor`` such that the
    angle AT the H between donor and acceptor is ``angle_deg`` (law of
    sines in the D-H-A triangle; H lies in the plane spanned by the
    D->A axis and a fixed perpendicular)."""
    dx = acceptor[0] - donor[0]
    dy = acceptor[1] - donor[1]
    dz = acceptor[2] - donor[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    ux, uy, uz = dx / length, dy / length, dz / length
    axis = (0.0, 0.0, 1.0)
    if abs(uz) > 0.9:
        axis = (0.0, 1.0, 0.0)
    wx = uy * axis[2] - uz * axis[1]
    wy = uz * axis[0] - ux * axis[2]
    wz = ux * axis[1] - uy * axis[0]
    wlen = math.sqrt(wx * wx + wy * wy + wz * wz)
    wx, wy, wz = wx / wlen, wy / wlen, wz / wlen
    theta = math.radians(angle_deg)
    s = r * math.sin(theta) / length
    if s > 1.0:
        raise ValueError('degenerate D-H-A triangle for the requested angle')
    ang_a = math.asin(s)
    psi = math.pi - theta - ang_a
    return (donor[0] + r * (math.cos(psi) * ux + math.sin(psi) * wx),
            donor[1] + r * (math.cos(psi) * uy + math.sin(psi) * wy),
            donor[2] + r * (math.cos(psi) * uz + math.sin(psi) * wz))


# --- scripted ligands ------------------------------------------------------

def _carbonyl_ligand(o_pos):
    """Minimal acceptor-only ligand: C1(=O2) with one C-H. The carbonyl O
    sits at ``o_pos``; no donors, no charge groups, no hydrophobes
    (C1 neighbors are O + H)."""
    c_pos = (o_pos[0] + 1.22, o_pos[1], o_pos[2])
    atoms = [_lig_atom(0, 'C1', 'C', c_pos[0], c_pos[1], c_pos[2]),
             _lig_atom(1, 'O2', 'O', o_pos[0], o_pos[1], o_pos[2]),
             _lig_atom(2, 'H3', 'H', c_pos[0] + 0.5, c_pos[1] + 0.85, 0.0)]
    bonds = [(0, 1, 2), (0, 2, 1)]
    return atoms, bonds


def _ammonium_ligand(n_pos, h_offsets):
    """sp3 ammonium N+ (4 single bonds incl. >= 1 H) + one methyl C —
    the structural '+' charge group of gate §2.3 (no formal_charge key)."""
    c_pos = (n_pos[0] + 1.35, n_pos[1] + 0.9, n_pos[2])
    atoms = [_lig_atom(0, 'N1', 'N', n_pos[0], n_pos[1], n_pos[2]),
             _lig_atom(1, 'C2', 'C', c_pos[0], c_pos[1], c_pos[2])]
    bonds = [(0, 1, 1)]
    for k, off in enumerate(h_offsets):
        atoms.append(_lig_atom(len(atoms), 'H%d' % (k + 3), 'H',
                               n_pos[0] + off[0], n_pos[1] + off[1],
                               n_pos[2] + off[2]))
        bonds.append((0, len(atoms) - 1, 1))
    return atoms, bonds


def _cation_no_h_ligand(n_pos):
    """Formal-charge cation with NO hydrogens (N fc=+1 + methyl C) —
    isolates salt-bridge geometry from any h-bond side effects."""
    atoms = [_lig_atom(0, 'N1', 'N', n_pos[0], n_pos[1], n_pos[2], fc=1),
             _lig_atom(1, 'C2', 'C', n_pos[0] + 1.5, n_pos[1], n_pos[2])]
    bonds = [(0, 1, 1)]
    return atoms, bonds


def _carboxylate_ligand(center):
    """Ligand carboxylate C(=O)(-O) — the structural '-' group of gate
    §2.3 (2 Os on one C, no O-H, no formal charges: kekule structure
    alone types '-', the recorded 02-05 decision)."""
    atoms = [_lig_atom(0, 'C1', 'C', center[0], center[1], center[2]),
             _lig_atom(1, 'O2', 'O', center[0] + 1.0, center[1] + 0.75,
                       center[2]),
             _lig_atom(2, 'O3', 'O', center[0] - 1.0, center[1] + 0.75,
                       center[2])]
    bonds = [(0, 1, 1), (0, 2, 1)]
    return atoms, bonds


def _methane_ligand(c_pos):
    """Qualifying hydrophobe: C with all bonded neighbors in {C, H}."""
    atoms = [_lig_atom(0, 'C0', 'C', c_pos[0], c_pos[1], c_pos[2])]
    bonds = []
    for k, off in enumerate(((0.63, 0.63, 0.0), (-0.63, 0.63, 0.0),
                             (0.0, -0.63, 0.9), (0.0, -0.63, -0.9))):
        atoms.append(_lig_atom(len(atoms), 'H%d' % (k + 1), 'H',
                               c_pos[0] + off[0], c_pos[1] + off[1],
                               c_pos[2] + off[2]))
        bonds.append((0, len(atoms) - 1, 1))
    return atoms, bonds


def _n_methyl_ligand(c_pos):
    """C bonded to N (an amine) — NOT a qualifying hydrophobe (row 5)."""
    atoms = [_lig_atom(0, 'C0', 'C', c_pos[0], c_pos[1], c_pos[2]),
             _lig_atom(1, 'N1', 'N', c_pos[0] + 1.47, c_pos[1], c_pos[2])]
    bonds = [(0, 1, 1)]
    for off in ((0.0, 0.63, 0.9), (0.0, 0.63, -0.9), (-0.63, -0.63, 0.0)):
        atoms.append(_lig_atom(len(atoms), 'H%d' % len(atoms), 'H',
                               c_pos[0] + off[0], c_pos[1] + off[1],
                               c_pos[2] + off[2]))
        bonds.append((0, len(atoms) - 1, 1))
    for off in ((0.9, 0.35, 0.0), (0.35, -0.9, 0.0)):
        atoms.append(_lig_atom(len(atoms), 'H%d' % len(atoms), 'H',
                               c_pos[0] + 1.47 + off[0],
                               c_pos[1] + off[1], c_pos[2]))
        bonds.append((1, len(atoms) - 1, 1))
    return atoms, bonds


def _benzamide_ligand():
    """Benzamide: kekule 6-ring in the xy-plane (center origin, radius
    1.39, normal +z) + C7(=O8)N9(H10,H11). Ring C1 carries the C7
    substituent; C2..C6 carry H12..H16. Ring coordinates use exact
    trig so the row-9 radius is exactly 1.39."""
    ring_y = 1.39 * math.sin(math.pi / 3.0)   # 1.203775... (exact hexagon)
    coords = [
        ('C1', 'C', (1.39, 0.0, 0.0)), ('C2', 'C', (0.695, ring_y, 0.0)),
        ('C3', 'C', (-0.695, ring_y, 0.0)), ('C4', 'C', (-1.39, 0.0, 0.0)),
        ('C5', 'C', (-0.695, -ring_y, 0.0)), ('C6', 'C', (0.695, -ring_y,
                                                          0.0)),
        ('C7', 'C', (2.89, 0.0, 0.0)), ('O8', 'O', (2.89, 1.22, 0.0)),
        ('N9', 'N', (2.89, -1.35, 0.0)), ('H10', 'H', (3.79, -1.85, 0.0)),
        ('H11', 'H', (3.5, -0.6, 0.0)), ('H12', 'H', (1.09, 2.09, 0.0)),
        ('H13', 'H', (-1.09, 2.09, 0.0)), ('H14', 'H', (-2.39, 0.0, 0.0)),
        ('H15', 'H', (-1.09, -2.09, 0.0)), ('H16', 'H', (1.09, -2.09, 0.0)),
    ]
    atoms = [_lig_atom(i, name, elem, xyz[0], xyz[1], xyz[2])
             for i, (name, elem, xyz) in enumerate(coords)]
    bonds = [(0, 1, 2), (1, 2, 1), (2, 3, 2), (3, 4, 1), (4, 5, 2),
             (5, 0, 1), (0, 6, 1), (6, 7, 2), (6, 8, 1), (8, 9, 1),
             (8, 10, 1), (1, 11, 1), (2, 12, 1), (3, 13, 1), (4, 14, 1),
             (5, 15, 1)]
    return atoms, bonds


def _acetammonium_ligand():
    """Combined-scene ligand: C0(methyl hydrophobe)-C1(=O2)-C3(H2)-
    N4(H3)+ (ammonium). C3 is NOT a hydrophobe (bonded to N)."""
    coords = [
        ('C0', 'C', (0.0, 0.0, 0.0)), ('C1', 'C', (1.5, 0.0, 0.0)),
        ('O2', 'O', (1.5, 1.22, 0.0)), ('C3', 'C', (3.0, 0.0, 0.0)),
        ('N4', 'N', (4.45, 0.0, 0.0)), ('H6', 'H', (5.4, 0.5, 0.0)),
        ('H7', 'H', (5.4, -0.5, 0.0)), ('H12', 'H', (4.45, 0.0, 0.95)),
        ('H8', 'H', (-0.5, 0.87, 0.0)), ('H9', 'H', (-0.5, -0.87, 0.0)),
        ('H10', 'H', (0.0, 0.0, 1.09)), ('H5', 'H', (2.5, -0.87, 0.0)),
        ('H11', 'H', (3.5, -0.87, 0.0)),
    ]
    atoms = [_lig_atom(i, name, elem, xyz[0], xyz[1], xyz[2])
             for i, (name, elem, xyz) in enumerate(coords)]
    bonds = [(0, 1, 1), (1, 2, 2), (1, 3, 1), (3, 4, 1), (4, 5, 1),
             (4, 6, 1), (4, 7, 1), (0, 8, 1), (0, 9, 1), (0, 10, 1),
             (3, 11, 1), (3, 12, 1)]
    return atoms, bonds


# --- scripted amino acids --------------------------------------------------

_BACKBONE = (('N', 'N'), ('CA', 'C'), ('C', 'C'), ('O', 'O'))


def _aa_backbone(obj, start_id, resn, resi, origin):
    """Backbone atoms (N, CA, C, O) + H, HA — NEVER typed (D1)."""
    atoms = []
    offsets = {'N': (-1.2, 0.7, 0.0), 'CA': (0.0, 0.0, 0.0),
               'C': (0.4, -1.4, 0.0), 'O': (-0.6, -2.2, 0.0)}
    next_id = start_id
    for name, elem in _BACKBONE:
        off = offsets[name]
        atoms.append(_aa_atom(obj, next_id, name, elem, resn, resi,
                              origin[0] + off[0], origin[1] + off[1],
                              origin[2] + off[2]))
        next_id += 1
    atoms.append(_aa_atom(obj, next_id, 'H', 'H', resn, resi,
                          origin[0] - 2.0, origin[1] + 1.4, 0.0))
    next_id += 1
    atoms.append(_aa_atom(obj, next_id, 'HA', 'H', resn, resi,
                          origin[0] + 0.3, origin[1] + 1.0, 0.2))
    return atoms, next_id + 1


def _serine(obj, og, hg):
    """SER: backbone + CB/OG/HG + carbon Hs. OG-HG distance ~0.97 A so the
    fail-closed donor pairing finds HG (detector AA_H_ATTACH_MAX = 1.5)."""
    atoms, next_id = _aa_backbone(obj, 100, 'SER', 1, (0.0, 4.6, 0.0))
    atoms.append(_aa_atom(obj, next_id, 'CB', 'C', 'SER', 1,
                          0.2, 5.4, 0.0))
    next_id += 1
    atoms.append(_aa_atom(obj, next_id, 'HB1', 'H', 'SER', 1,
                          0.9, 6.2, 0.0))
    next_id += 1
    atoms.append(_aa_atom(obj, next_id, 'HB2', 'H', 'SER', 1,
                          -0.6, 6.0, 0.0))
    next_id += 1
    atoms.append(_aa_atom(obj, next_id, 'OG', 'O', 'SER', 1,
                          og[0], og[1], og[2]))
    next_id += 1
    if hg is not None:
        atoms.append(_aa_atom(obj, next_id, 'HG', 'H', 'SER', 1,
                              hg[0], hg[1], hg[2]))
    return atoms


def _alanine(obj, cb):
    """ALA: backbone + CB only (capability side_chain is empty for ALA —
    CB is the universal side-chain anchor the hydrophobic rule uses)."""
    atoms, next_id = _aa_backbone(obj, 200, 'ALA', 2, (-3.6, -1.4, 0.0))
    atoms.append(_aa_atom(obj, next_id, 'CB', 'C', 'ALA', 2,
                          cb[0], cb[1], cb[2]))
    next_id += 1
    for name, off in (('HB1', (0.63, 0.63, 0.0)), ('HB2', (0.63, -0.63, 0.0)),
                      ('HB3', (-0.4, 0.0, 0.9))):
        atoms.append(_aa_atom(obj, next_id, name, 'H', 'ALA', 2,
                              cb[0] + off[0], cb[1] + off[1],
                              cb[2] + off[2]))
        next_id += 1
    return atoms


def _aspartate(od1, od2, cg):
    """ASP: backbone + CB/CG/OD1/OD2 — the carboxylate anion group
    (capability charge_atoms = OD1/OD2, center = their midpoint)."""
    atoms, next_id = _aa_backbone('aa_asp', 300, 'ASP', 3, (2.6, -1.9, 0.0))
    for name, pos in (('CB', (4.45, -2.4, 0.0)), ('CG', cg),
                      ('OD1', od1), ('OD2', od2)):
        elem = 'O' if name.startswith('OD') else 'C'
        atoms.append(_aa_atom('aa_asp', next_id, name, elem, 'ASP', 3,
                              pos[0], pos[1], pos[2]))
        next_id += 1
    return atoms


def _tyrosine():
    """TYR: backbone + CB + a planar 6-ring (CG..CD2) + OH/HH — NOT in the
    pedagogical hydrophobic set (residue-name rule, coordination #2)."""
    atoms, next_id = _aa_backbone('aa_tyr', 400, 'TYR', 4, (4.6, 0.0, 0.0))
    ring = [('CG', (1.89, 0.5, 0.0)), ('CD1', (1.195, 1.704, 0.0)),
            ('CE1', (-0.195, 1.704, 0.0)), ('CZ', (-0.89, 0.5, 0.0)),
            ('CE2', (-0.195, -0.704, 0.0)), ('CD2', (1.195, -0.704, 0.0))]
    for name, pos in ring:
        atoms.append(_aa_atom('aa_tyr', next_id, name, 'C', 'TYR', 4,
                              pos[0], pos[1], pos[2]))
        next_id += 1
    atoms.append(_aa_atom('aa_tyr', next_id, 'CB', 'C', 'TYR', 4,
                          3.5, 1.3, 0.0))
    next_id += 1
    atoms.append(_aa_atom('aa_tyr', next_id, 'OH', 'O', 'TYR', 4,
                          -2.2, 0.5, 0.0))
    next_id += 1
    atoms.append(_aa_atom('aa_tyr', next_id, 'HH', 'H', 'TYR', 4,
                          -2.9, 0.9, 0.0))
    return atoms


def _far_alanine():
    """An AA whose bounding sphere cannot intersect the ligand sphere
    (placed ~170 A away) — the prefilter must drop it entirely."""
    atoms, next_id = _aa_backbone('aa_far', 900, 'ALA', 9,
                                  (100.0, 100.0, 100.0))
    atoms.append(_aa_atom('aa_far', next_id, 'CB', 'C', 'ALA', 9,
                          101.5, 100.6, 100.0))
    return atoms


def _scene(lig_atoms, lig_bonds, aa_atom_lists):
    """Concatenate: ligand FIRST (the bond block indexes the ligand
    subsequence in its given order), then the AA records in order."""
    atoms = list(lig_atoms)
    for aa_list in aa_atom_lists:
        atoms.extend(aa_list)
    return atoms, list(lig_bonds)


def _of_type(records, type_):
    return [r for r in records if r['type'] == type_]


# ---------------------------------------------------------------------------
# Task 2 RED spec 1 — extract_features (typed features, computed once)
# ---------------------------------------------------------------------------

class TestExtractFeatures(unittest.TestCase):
    """Feature precomputation on a benzamide-like ligand + SER + ALA."""

    @classmethod
    def setUpClass(cls):
        lig_atoms, lig_bonds = _benzamide_ligand()
        ser = _serine('aa_ser', (1.5, 4.22, 0.0), (2.2, 4.9, 0.0))
        ala = _alanine('aa_ala', (-3.0, -1.0, 0.0))
        cls.atoms, cls.bonds = _scene(lig_atoms, lig_bonds, [ser, ala])
        cls.features = detector.extract_features(cls.atoms, cls.bonds)

    def test_ligand_donor_h_pairs_from_bond_block(self):
        pairs = self.features['lig']['donor_pairs']
        heavy_names = [p[0][1]['name'] for p in pairs]
        h_names = [p[1][1]['name'] for p in pairs]
        # N9 is the only polar ligand atom with a bonded H (fail-closed).
        self.assertEqual(heavy_names, ['N9', 'N9'])
        self.assertEqual(h_names, ['H10', 'H11'])

    def test_ligand_acceptors(self):
        names = [rec['name'] for idx, rec
                 in self.features['lig']['acceptors']]
        # acceptors = any O/N/S (recorded 02-05 rule; geometry decides later)
        self.assertEqual(names, ['O8', 'N9'])

    def test_ligand_hydrophobes(self):
        names = [rec['name'] for idx, rec
                 in self.features['lig']['hydrophobes']]
        # ring C1..C6 qualify (all neighbors C/H; C1's substituent C7 is C);
        # carbonyl C7 does not (bonded to O and N).
        self.assertEqual(sorted(names),
                         ['C1', 'C2', 'C3', 'C4', 'C5', 'C6'])

    def test_ligand_aromatic_ring_geometry_row9(self):
        rings = self.features['lig']['rings']
        self.assertEqual(len(rings), 1)
        ring = rings[0]
        center = ring['center']
        self.assertAlmostEqual(center[0], 0.0, places=6)
        self.assertAlmostEqual(center[1], 0.0, places=6)
        self.assertAlmostEqual(center[2], 0.0, places=6)
        normal = ring['normal']
        self.assertAlmostEqual(normal[0], 0.0, places=6)
        self.assertAlmostEqual(normal[1], 0.0, places=6)
        self.assertAlmostEqual(abs(normal[2]), 1.0, places=6)
        self.assertAlmostEqual(ring['radius'], 1.39, places=6)
        self.assertEqual(ring['atom_ids'], [0, 1, 2, 3, 4, 5])

    def test_ligand_charge_groups_match_capability(self):
        # DETECT-04 by construction: the detector's ligand charge-group
        # signs MUST equal capability.ligand_profile's charge_signs.
        signs = set(g['sign'] for g in self.features['lig']['charge_groups'])
        profile = capability.ligand_profile(self.atoms[:16], self.bonds)
        self.assertEqual(signs, set())
        self.assertEqual(signs, profile['charge_signs'])

    def test_aa_features_side_chain_only_d1(self):
        ser = self.features['aa']['aa_ser']
        self.assertEqual(ser['resn'], 'SER')
        # ONLY side-chain atoms are typed (D1): the backbone O is a
        # chemical acceptor but must never appear here.
        self.assertEqual([r['name'] for r in ser['acceptors']], ['OG'])
        self.assertEqual(len(ser['donor_pairs']), 1)
        self.assertEqual(ser['donor_pairs'][0][0]['name'], 'OG')
        self.assertEqual(ser['donor_pairs'][0][1]['name'], 'HG')
        self.assertEqual([r['name'] for r in ser['side_chain']],
                         ['HG', 'OG'])          # name-sorted
        self.assertIsNone(ser['charge']['sign'])
        self.assertEqual(ser['rings'], [])
        self.assertFalse(ser['hydrophobic'])

    def test_aa_alanine_cb_anchor_and_empty_side_chain(self):
        ala = self.features['aa']['aa_ala']
        self.assertEqual([r['name'] for r in ala['side_chain']], [])
        self.assertTrue(ala['hydrophobic'])
        # CB is the side-chain anchor the residue-name hydrophobic rule
        # enumerates (capability omits CB from side_chain by convention).
        self.assertEqual([r['name'] for r in ala['hydrophobic_carbons']],
                         ['CB'])
        self.assertEqual(ala['donor_pairs'], [])
        self.assertEqual(ala['acceptors'], [])

    def test_unclassified_aa_atoms_zero_for_fragments(self):
        # Every heavy atom of both fragments is side_chain or a known
        # backbone/anchor name — SMOKE-03 (02-13) asserts this stays zero
        # on the materialized geometry.
        self.assertEqual(self.features['unclassified_aa_atoms'], 0)

    def test_unclassified_counts_unknown_residue_atoms(self):
        bogus = [_aa_atom('aa_bogus', 500, 'XX1', 'C', 'XYZ', 7,
                          50.0, 50.0, 50.0),
                 _aa_atom('aa_bogus', 501, 'XX2', 'O', 'XYZ', 7,
                          51.0, 50.0, 50.0)]
        features = detector.extract_features(self.atoms + bogus, self.bonds)
        self.assertEqual(features['unclassified_aa_atoms'], 2)
        # and the unknown residue contributes no typed features
        bogus_feats = features['aa']['aa_bogus']
        self.assertEqual(bogus_feats['acceptors'], [])
        self.assertEqual(bogus_feats['donor_pairs'], [])

    def test_ligand_feature_families_all_precomputed(self):
        lig = self.features['lig']
        center, radius = lig['sphere']
        self.assertIsInstance(radius, float)
        self.assertGreater(radius, 2.0)
        # feature families the 7-type version (02-07) consumes — all
        # computed ONCE here, never per-pair:
        for key in ('atoms', 'donor_pairs', 'acceptors', 'hydrophobes',
                    'charge_groups', 'rings', 'halogen_donors', 'metals',
                    'sphere'):
            self.assertIn(key, lig)

    def test_bond_indices_out_of_range_fail_closed(self):
        lig_atoms = self.atoms[:16]          # the ligand subsequence alone
        with self.assertRaises(ValueError):
            detector.extract_features(lig_atoms, [(0, 99, 1)])

    def test_unknown_side_fails_closed(self):
        bad = {'side': 'water', 'object': 'x', 'id': 0, 'name': 'O',
               'elem': 'O', 'resn': 'HOH', 'resi': 1, 'alt': '',
               'x': 0.0, 'y': 0.0, 'z': 0.0}
        with self.assertRaises(ValueError):
            detector.extract_features([bad], [])


class TestAltlocPolicy(unittest.TestCase):
    """Chemistry policy item 2 (detection research §7.2): keep alt ''/'A',
    drop the rest — defensive pure-layer filter applied before typing;
    never best-scoring-conformer (nondeterministic)."""

    def test_keeps_blank_and_A_drops_others(self):
        atoms = [
            _aa_atom('a', 1, 'CA', 'C', 'ALA', 1, 0.0, 0.0, 0.0),
            _aa_atom('a', 2, 'CB', 'C', 'ALA', 1, 1.0, 0.0, 0.0),
            _aa_atom('a', 3, 'CB', 'C', 'ALA', 1, 1.1, 0.0, 0.0),
        ]
        atoms[1]['alt'] = 'A'
        atoms[2]['alt'] = 'B'
        kept = detector.apply_altloc_policy(atoms)
        self.assertEqual([a['id'] for a in kept], [1, 2])


# ---------------------------------------------------------------------------
# Task 2 RED spec 2 — AA bounding-sphere prefilter
# ---------------------------------------------------------------------------

class TestAAPrefilter(unittest.TestCase):
    """Two-level pruning: AA bounding sphere first, cell list second."""

    def test_far_aa_produces_no_records(self):
        lig_atoms, lig_bonds = _carbonyl_ligand((3.0, 0.0, 0.0))
        ser = _serine('aa_ser', (0.0, 0.0, 0.0),
                      _h_pos((0.0, 0.0, 0.0), (3.0, 0.0, 0.0), 1.0, 160.0))
        atoms, bonds = _scene(lig_atoms, lig_bonds, [ser, _far_alanine()])
        records = detector.detect_part1(atoms, bonds)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['aa']['object'], 'aa_ser')

    def test_only_far_aa_yields_nothing(self):
        lig_atoms, lig_bonds = _carbonyl_ligand((3.0, 0.0, 0.0))
        atoms, bonds = _scene(lig_atoms, lig_bonds, [_far_alanine()])
        self.assertEqual(detector.detect_part1(atoms, bonds), [])

    def test_bounding_spheres_are_centroid_max_dist(self):
        lig_atoms, lig_bonds = _carbonyl_ligand((3.0, 0.0, 0.0))
        ser = _serine('aa_ser', (0.0, 0.0, 0.0), (0.97, 0.23, 0.0))
        atoms, bonds = _scene(lig_atoms, lig_bonds, [ser])
        features = detector.extract_features(atoms, bonds)
        spheres = detector._aa_bounding_spheres(features['aa'])
        center, radius = spheres['aa_ser']
        atoms_ser = features['aa']['aa_ser']['atoms']
        xs = [a['x'] for a in atoms_ser]
        ys = [a['y'] for a in atoms_ser]
        zs = [a['z'] for a in atoms_ser]
        self.assertAlmostEqual(center[0], sum(xs) / len(xs), places=9)
        self.assertAlmostEqual(center[1], sum(ys) / len(ys), places=9)
        self.assertAlmostEqual(center[2], sum(zs) / len(zs), places=9)
        farthest = max(math.sqrt((a['x'] - center[0]) ** 2
                                 + (a['y'] - center[1]) ** 2
                                 + (a['z'] - center[2]) ** 2)
                       for a in atoms_ser)
        self.assertAlmostEqual(radius, farthest, places=9)


# ---------------------------------------------------------------------------
# Task 2 RED spec 3 — h_bond (row 1: D...A <= 4.0 A, angle at H >= 140 deg)
# ---------------------------------------------------------------------------

class TestHBond(unittest.TestCase):
    """SER OG+HG (aa role 'donor') vs a ligand carbonyl O; boundaries."""

    def _detect(self, og, hg, o_pos):
        lig_atoms, lig_bonds = _carbonyl_ligand(o_pos)
        ser = _serine('aa_ser', og, hg)
        atoms, bonds = _scene(lig_atoms, lig_bonds, [ser])
        return detector.detect_part1(atoms, bonds)

    def test_formed_160_deg_3p0_angstrom(self):
        og = (0.0, 0.0, 0.0)
        o_pos = (3.0, 0.0, 0.0)
        records = self._detect(og, _h_pos(og, o_pos, 1.0, 160.0), o_pos)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record['type'], 'h_bond')
        self.assertEqual(record['aa']['role'], 'donor')
        self.assertEqual(record['lig']['role'], 'acceptor')
        self.assertEqual(record['aa']['object'], 'aa_ser')
        self.assertEqual(record['aa']['resn'], 'SER')
        # OG id 109 + HG id 110 (scripted builder), ligand O2 id 1
        self.assertEqual(sorted(record['aa']['atom_ids']), [109, 110])
        self.assertEqual(record['lig']['atom_ids'], [1])
        self.assertAlmostEqual(record['metrics']['d_da'], 3.0, places=6)
        self.assertAlmostEqual(record['metrics']['angle_deg'], 160.0,
                               places=6)
        self.assertTrue(record['formed'])

    def test_angle_100_deg_not_formed(self):
        og = (0.0, 0.0, 0.0)
        o_pos = (3.0, 0.0, 0.0)
        hg = _h_pos(og, o_pos, 1.0, 100.0)   # distance still fine
        self.assertEqual(self._detect(og, hg, o_pos), [])

    def test_angle_boundary_141_vs_139(self):
        og = (0.0, 0.0, 0.0)
        o_pos = (3.0, 0.0, 0.0)
        formed = self._detect(og, _h_pos(og, o_pos, 1.0, 141.0), o_pos)
        self.assertEqual(len(formed), 1)
        self.assertAlmostEqual(formed[0]['metrics']['angle_deg'], 141.0,
                               places=6)
        not_formed = self._detect(og, _h_pos(og, o_pos, 1.0, 139.0), o_pos)
        self.assertEqual(not_formed, [])

    def test_distance_boundary_3p9_yes_4p1_no(self):
        og = (0.0, 0.0, 0.0)
        inside = self._detect(og, _h_pos(og, (3.9, 0.0, 0.0), 1.0, 180.0),
                              (3.9, 0.0, 0.0))
        self.assertEqual(len(inside), 1)
        self.assertAlmostEqual(inside[0]['metrics']['d_da'], 3.9, places=6)
        outside = self._detect(og, _h_pos(og, (4.1, 0.0, 0.0), 1.0, 180.0),
                               (4.1, 0.0, 0.0))
        self.assertEqual(outside, [])

    def test_fail_closed_donor_without_h(self):
        # SER OG present but NO HG anywhere -> no donor-H pair -> nothing
        # (gate §5.3: an O/N/S without an attached H is not a donor).
        lig_atoms, lig_bonds = _carbonyl_ligand((3.0, 0.0, 0.0))
        ser = _serine('aa_ser', (0.0, 0.0, 0.0), None)
        atoms, bonds = _scene(lig_atoms, lig_bonds, [ser])
        self.assertEqual(detector.detect_part1(atoms, bonds), [])

    def test_aa_acceptor_direction(self):
        # Ligand ammonium donates TO SER OG (no HG on the SER): aa role
        # 'acceptor', lig role 'donor' — the direction-refined enumeration
        # mirroring capability.aa_capable's h_bond refinement (02-05).
        og = (0.0, 0.0, 0.0)
        n_pos = (3.0, 0.0, 0.0)
        lig_atoms, lig_bonds = _ammonium_ligand(
            n_pos, [(0.5, 0.85, 0.0), (-0.5, 0.85, 0.0), (0.0, -1.0, 0.0)])
        h2 = _h_pos(n_pos, og, 1.0, 160.0)
        lig_atoms[2] = _lig_atom(2, 'H3', 'H', h2[0], h2[1], h2[2])
        ser = _serine('aa_ser', og, None)
        atoms, bonds = _scene(lig_atoms, lig_bonds, [ser])
        records = _of_type(detector.detect_part1(atoms, bonds), 'h_bond')
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record['aa']['role'], 'acceptor')
        self.assertEqual(record['lig']['role'], 'donor')
        self.assertEqual(len(record['aa']['atom_ids']), 1)   # OG alone
        self.assertAlmostEqual(record['metrics']['angle_deg'], 160.0,
                               places=6)

    def test_one_record_per_donor_acceptor_pair_best_h(self):
        # Two Hs on one donor produce the single best-angle record, not
        # two records (one physical contact = one record; presence
        # semantics unaffected — recorded gate §2.4 deviation stands).
        og = (0.0, 0.0, 0.0)
        o_pos = (3.0, 0.0, 0.0)
        hg1 = _h_pos(og, o_pos, 1.0, 160.0)
        hg2 = _h_pos(og, o_pos, 1.0, 145.0)
        lig_atoms, lig_bonds = _carbonyl_ligand(o_pos)
        ser = _serine('aa_ser', og, hg1)
        ser.append(_aa_atom('aa_ser', 999, 'HG2', 'H', 'SER', 1,
                            hg2[0], hg2[1], hg2[2]))
        atoms, bonds = _scene(lig_atoms, lig_bonds, [ser])
        records = _of_type(detector.detect_part1(atoms, bonds), 'h_bond')
        self.assertEqual(len(records), 1)
        self.assertAlmostEqual(records[0]['metrics']['angle_deg'], 160.0,
                               places=6)


# ---------------------------------------------------------------------------
# Task 2 RED spec 4 — salt_bridge (row 2: opposite charge-group centers
# <= 5.5 A; polarity from the ligand charge sign, D3)
# ---------------------------------------------------------------------------

class TestSaltBridge(unittest.TestCase):

    def test_formed_4p5_group_centers(self):
        od1, od2, cg = (3.2, -4.5, 0.0), (5.7, -4.5, 0.0), (4.45, -3.3, 0.0)
        # ammonium Hs all point to +y/+z, away from the ASP below -y
        lig_atoms, lig_bonds = _ammonium_ligand(
            (4.45, 0.0, 0.0),
            [(0.9, 0.5, 0.3), (0.2, 0.9, 0.5), (-0.4, 0.6, 0.8)])
        atoms, bonds = _scene(lig_atoms, lig_bonds,
                              [_aspartate(od1, od2, cg)])
        records = _of_type(detector.detect_part1(atoms, bonds),
                           'salt_bridge')
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record['aa']['role'], 'anion')
        self.assertEqual(record['lig']['role'], 'cation')
        self.assertEqual(record['aa']['resn'], 'ASP')
        # aa atom_ids = the GROUP representatives OD1/OD2 (ids 308, 309)
        self.assertEqual(sorted(record['aa']['atom_ids']), [308, 309])
        self.assertEqual(record['lig']['atom_ids'], [0])   # the N center
        self.assertAlmostEqual(record['metrics']['d_center'], 4.5, places=6)

    def test_same_charge_pair_no_record(self):
        od1, od2, cg = (3.2, -4.5, 0.0), (5.7, -4.5, 0.0), (4.45, -3.3, 0.0)
        lig_atoms, lig_bonds = _carboxylate_ligand((4.45, 5.0, 0.0))
        atoms, bonds = _scene(lig_atoms, lig_bonds,
                              [_aspartate(od1, od2, cg)])
        records = detector.detect_part1(atoms, bonds)
        self.assertEqual(_of_type(records, 'salt_bridge'), [])
        self.assertEqual(records, [])   # no other type fires either

    def test_group_center_used_not_first_atom(self):
        # detection research §9.12: a carboxylate whose FIRST O is far
        # from the midpoint still uses the GROUP center.
        # OD1 at 7.0 A from the cation, OD2 at 2.0 -> midpoint at 4.5.
        od1, od2, cg = (0.0, -7.0, 0.0), (0.0, -2.0, 0.0), (0.0, -4.5, 0.0)
        lig_atoms, lig_bonds = _cation_no_h_ligand((0.0, 0.0, 0.0))
        atoms, bonds = _scene(lig_atoms, lig_bonds,
                              [_aspartate(od1, od2, cg)])
        records = _of_type(detector.detect_part1(atoms, bonds),
                           'salt_bridge')
        self.assertEqual(len(records), 1)
        self.assertAlmostEqual(records[0]['metrics']['d_center'], 4.5,
                               places=6)

    def test_no_record_when_center_exceeds_cutoff_despite_close_atom(self):
        # OD1 at 4.0 (inside 5.5) but the GROUP center at 6.0 -> nothing.
        od1, od2, cg = (0.0, -4.0, 0.0), (0.0, -8.0, 0.0), (0.0, -6.0, 0.0)
        lig_atoms, lig_bonds = _cation_no_h_ligand((0.0, 0.0, 0.0))
        atoms, bonds = _scene(lig_atoms, lig_bonds,
                              [_aspartate(od1, od2, cg)])
        records = detector.detect_part1(atoms, bonds)
        self.assertEqual(_of_type(records, 'salt_bridge'), [])
        self.assertEqual(records, [])

    def test_ligand_guanidino_group_center_and_salt(self):
        # Ligand guanidinium (C bonded to 3 N) types '+' in capability
        # (_charge_signs); the detector must enumerate the group (DETECT-04
        # parity) with the symmetric N-centroid center (gate §2.3 ligand
        # row says "midpoint of 2 Ns" — an isolated guanidinium has three
        # equivalent Ns; see the detector docstring note) and form the
        # salt bridge with ASP.
        c_pos = (0.0, 4.8, 0.0)
        lig_atoms = [_lig_atom(0, 'C1', 'C', c_pos[0], c_pos[1], c_pos[2])]
        lig_bonds = []
        for k, off in enumerate(((0.0, 1.25, 0.0), (-1.08, -0.62, 0.0),
                                 (1.08, -0.62, 0.0))):
            lig_atoms.append(_lig_atom(len(lig_atoms), 'N%d' % (k + 2), 'N',
                                       c_pos[0] + off[0], c_pos[1] + off[1],
                                       c_pos[2]))
            lig_bonds.append((0, len(lig_atoms) - 1, 1))
        od1, od2, cg = (0.0, -1.5, 0.0), (0.0, 2.5, 0.0), (0.0, -2.2, 0.0)
        atoms, bonds = _scene(lig_atoms, lig_bonds,
                              [_aspartate(od1, od2, cg)])
        features = detector.extract_features(atoms, bonds)
        groups = features['lig']['charge_groups']
        self.assertEqual([g['kind'] for g in groups], ['guanidino'])
        self.assertEqual(groups[0]['sign'], '+')
        profile = capability.ligand_profile(atoms[:4], bonds)
        self.assertEqual(set(g['sign'] for g in groups),
                         profile['charge_signs'])
        records = _of_type(detector.detect_part1(atoms, bonds),
                           'salt_bridge')
        self.assertEqual(len(records), 1)
        expected_center_y = 4.8 + (1.25 - 0.62 - 0.62) / 3.0
        self.assertAlmostEqual(records[0]['metrics']['d_center'],
                               expected_center_y - 0.5, places=6)

    def test_charge_sign_parity_with_capability_on_more_ligands(self):
        # DETECT-04: the group signs the detector enumerates must equal
        # capability.ligand_profile's charge_signs for every ligand shape.
        cases = [_benzamide_ligand(), _acetammonium_ligand(),
                 _carboxylate_ligand((0.0, 0.0, 0.0))]
        # ester: C-C(=O)-O-C — capability's structure-alone decision types
        # '-' (the recorded accepted false-positive); parity must hold.
        ester_atoms = [_lig_atom(0, 'C0', 'C', 0.0, 0.0, 0.0),
                       _lig_atom(1, 'C1', 'C', 1.5, 0.0, 0.0),
                       _lig_atom(2, 'O2', 'O', 1.5, 1.22, 0.0),
                       _lig_atom(3, 'O3', 'O', 3.0, 0.0, 0.0),
                       _lig_atom(4, 'C4', 'C', 4.4, 0.6, 0.0)]
        cases.append((ester_atoms,
                      [(0, 1, 1), (1, 2, 2), (1, 3, 1), (3, 4, 1)]))
        for lig_atoms, lig_bonds in cases:
            features = detector.extract_features(lig_atoms, lig_bonds)
            signs = set(g['sign'] for g in features['lig']['charge_groups'])
            profile = capability.ligand_profile(lig_atoms, lig_bonds)
            self.assertEqual(signs, profile['charge_signs'],
                             'charge-group parity broken for %s'
                             % [a['name'] for a in lig_atoms])


# ---------------------------------------------------------------------------
# Task 2 RED spec 5 — hydrophobic (row 5: qualifying carbons <= 4.0 A;
# AA side by residue NAME, ligand side by the atom rule)
# ---------------------------------------------------------------------------

class TestHydrophobic(unittest.TestCase):

    def _detect(self, lig_atoms, lig_bonds, aa_lists):
        atoms, bonds = _scene(lig_atoms, lig_bonds, aa_lists)
        return detector.detect_part1(atoms, bonds)

    def test_formed_ala_cb_vs_qualifying_ligand_carbon(self):
        lig_atoms, lig_bonds = _methane_ligand((3.0, 0.0, 0.0))
        records = _of_type(self._detect(lig_atoms, lig_bonds,
                                        [_alanine('aa_ala',
                                                  (0.0, 0.0, 0.0))]),
                           'hydrophobic')
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record['aa']['role'], 'carbon')
        self.assertEqual(record['lig']['role'], 'carbon')
        self.assertEqual(record['aa']['resn'], 'ALA')
        self.assertAlmostEqual(record['metrics']['d_cc'], 3.0, places=6)
        self.assertEqual(record['aa']['atom_ids'], [206])   # the CB
        self.assertEqual(record['lig']['atom_ids'], [0])    # the C0

    def test_tyr_not_in_pedagogical_set_no_record(self):
        # A TYR ring carbon 3.0 A from a qualifying ligand carbon still
        # yields NO hydrophobic record (residue-name-based AA side).
        lig_atoms, lig_bonds = _methane_ligand((3.0, 0.0, 0.0))
        records = self._detect(lig_atoms, lig_bonds, [_tyrosine()])
        self.assertEqual(_of_type(records, 'hydrophobic'), [])
        self.assertEqual(records, [])

    def test_ligand_c_bonded_to_n_not_qualifying(self):
        lig_atoms, lig_bonds = _n_methyl_ligand((3.0, 0.0, 0.0))
        records = self._detect(lig_atoms, lig_bonds,
                               [_alanine('aa_ala', (0.0, 0.0, 0.0))])
        self.assertEqual(_of_type(records, 'hydrophobic'), [])
        self.assertEqual(records, [])

    def test_min_dist_guard_rejects_coincident_atoms(self):
        # row 10: all pair distances must be > 0.5 A.
        lig_atoms, lig_bonds = _methane_ligand((0.3, 0.0, 0.0))
        records = self._detect(lig_atoms, lig_bonds,
                               [_alanine('aa_ala', (0.0, 0.0, 0.0))])
        self.assertEqual(records, [])


# ---------------------------------------------------------------------------
# Task 2 RED spec 6 — record shape, canonical order, determinism
# ---------------------------------------------------------------------------

def _combined_scene(aa_order='ser_first'):
    """One scene firing all three 02-06 types: SER h_bond donor,
    ASP salt anion, ALA hydrophobic — against _acetammonium_ligand."""
    lig_atoms, lig_bonds = _acetammonium_ligand()
    og = (1.5, 4.22, 0.0)
    hg = _h_pos(og, (1.5, 1.22, 0.0), 1.0, 160.0)
    ser = _serine('aa_ser', og, hg)
    asp = _aspartate((3.2, -4.5, 0.0), (5.7, -4.5, 0.0), (4.45, -3.3, 0.0))
    ala = _alanine('aa_ala', (-3.0, 0.0, 0.0))
    aa_lists = [ser, asp, ala]
    if aa_order == 'reversed':
        aa_lists = [ala, asp, ser]
    return _scene(lig_atoms, lig_bonds, aa_lists)


class TestRecordContract(unittest.TestCase):
    """Canonical record shape/order + determinism on the combined scene."""

    @classmethod
    def setUpClass(cls):
        cls.atoms, cls.bonds = _combined_scene()
        cls.records = detector.detect_part1(cls.atoms, cls.bonds)

    def test_three_types_fire(self):
        self.assertEqual([r['type'] for r in self.records],
                         ['h_bond', 'salt_bridge', 'hydrophobic'])

    def test_record_shape_exact(self):
        for record in self.records:
            self.assertEqual(set(record),
                             {'type', 'aa', 'lig', 'metrics', 'formed'})
            self.assertEqual(set(record['aa']),
                             {'object', 'atom_ids', 'resn', 'resi', 'role'})
            self.assertEqual(set(record['lig']),
                             {'object', 'atom_ids', 'role'})
            self.assertTrue(record['formed'])
            self.assertEqual(record['lig']['object'], 'ligand')
            self.assertIsInstance(record['aa']['resi'], int)

    def test_metrics_carry_the_type_criterion(self):
        self.assertEqual(set(self.records[0]['metrics']),
                         {'d_da', 'angle_deg'})
        self.assertEqual(set(self.records[1]['metrics']), {'d_center'})
        self.assertEqual(set(self.records[2]['metrics']), {'d_cc'})

    def test_canonical_order_matches_enum_positions(self):
        positions = [INTERACTION_TYPES.index(r['type'])
                     for r in self.records]
        self.assertEqual(positions, sorted(positions))
        keys = [(INTERACTION_TYPES.index(r['type']), r['aa']['object'],
                 tuple(r['aa']['atom_ids']), tuple(r['lig']['atom_ids']))
                for r in self.records]
        self.assertEqual(keys, sorted(keys))

    def test_determinism_same_input_twice(self):
        again = detector.detect_part1(self.atoms, self.bonds)
        self.assertEqual(self.records, again)

    def test_aa_record_order_permutation_invariant(self):
        # Shuffled AA record order must give identical canonical records
        # (name-sorted internal iteration fixes float summation order; the
        # coarse prefilter sphere is metric-free so 1e-15 wobble is inert).
        atoms, bonds = _combined_scene(aa_order='reversed')
        self.assertEqual(detector.detect_part1(atoms, bonds), self.records)

    def test_records_agree_with_capability_tables(self):
        # DETECT-04 end-to-end: every record's (resn, type) must be
        # capable under capability.aa_capable with the SAME ligand
        # profile — and the scripted negatives must stay incapable.
        lig_atoms = self.atoms[:13]
        profile = capability.ligand_profile(lig_atoms, self.bonds)
        for record in self.records:
            self.assertTrue(
                capability.aa_capable(record['aa']['resn'], record['type'],
                                      profile),
                '%s/%s record contradicts capability' % (record['aa']['resn'],
                                                         record['type']))
        self.assertFalse(capability.aa_capable('TYR', 'hydrophobic',
                                               profile))
        self.assertFalse(capability.aa_capable('ALA', 'h_bond', profile))
        self.assertTrue(capability.aa_capable('ASP', 'salt_bridge', profile))
        self.assertTrue(capability.aa_capable('SER', 'h_bond', profile))


if __name__ == '__main__':
    unittest.main()
