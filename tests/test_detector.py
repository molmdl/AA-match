"""Unit tests for aamatch.detector — pipeline core + the full 7-type
surface (DETECT-01 / DETECT-02 complete).

Plan 02-06 scope: extract_features (typed features, computed ONCE), the
AA bounding-sphere prefilter, spatial.cross_pairs candidate enumeration,
and the h_bond / salt_bridge / hydrophobic tests with explicit partner
sides. Plans 02-07 (pi_stacking, cation_pi — the ring-geometry types)
and 02-07b (halogen, metal, canonical 7-type detect(); 02-07 split
2026-09-06) extend this file on the SAME pipeline — every geometry here
is hand-placed and runs under bare python3.6 with ZERO PyMOL (pure-layer
contract).

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
from unittest import mock

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


# --- ring-geometry helpers (plan 02-07) -----------------------------------

_HEX_R = 1.39                                       # benzene-like radius
_HEX_Y = _HEX_R * math.sin(math.pi / 3.0)           # exact hexagon


def _benzene_ligand():
    """Plain benzene ring (6 C + 6 H, kekule bonds), center at origin,
    normal +z, radius 1.39. Ring carbons qualify as hydrophobes
    (neighbors C/C/H), so the ring-type tests below scope all asserts
    with _of_type — a stray hydrophobic record never fakes a miss."""
    atoms = [_lig_atom(0, 'C1', 'C', 1.39, 0.0, 0.0),
             _lig_atom(1, 'C2', 'C', 0.695, _HEX_Y, 0.0),
             _lig_atom(2, 'C3', 'C', -0.695, _HEX_Y, 0.0),
             _lig_atom(3, 'C4', 'C', -1.39, 0.0, 0.0),
             _lig_atom(4, 'C5', 'C', -0.695, -_HEX_Y, 0.0),
             _lig_atom(5, 'C6', 'C', 0.695, -_HEX_Y, 0.0)]
    h_scale = (_HEX_R + 1.09) / _HEX_R              # C-H ~1.09 A, radial
    for k in range(6):
        carbon = atoms[k]
        atoms.append(_lig_atom(len(atoms), 'H%d' % (k + 7), 'H',
                               carbon['x'] * h_scale,
                               carbon['y'] * h_scale, 0.0))
    bonds = [(0, 1, 2), (1, 2, 1), (2, 3, 2), (3, 4, 1), (4, 5, 2),
             (5, 0, 1)]
    bonds.extend((k, k + 6, 1) for k in range(6))
    return atoms, bonds


def _hex_ring(obj, next_id, resn, resi, center, normal_u, inplane_u,
              names):
    """Six ring atoms (regular hexagon, radius 1.39) in the plane through
    ``center`` with unit normal ``normal_u``; ``inplane_u`` is a unit
    in-plane axis. The walk order ``names`` (atoms at 0, 60, ..., 300
    deg) puts atoms 0/2/4 at 120 deg so the row-9 plane is
    non-degenerate; (u, v, n) is right-handed so the computed normal
    equals ``normal_u``."""
    n = normal_u
    u = inplane_u
    v = (n[1] * u[2] - n[2] * u[1],
         n[2] * u[0] - n[0] * u[2],
         n[0] * u[1] - n[1] * u[0])
    atoms = []
    for k, name in enumerate(names):
        theta = 2.0 * math.pi * k / 6.0
        c = math.cos(theta)
        s = math.sin(theta)
        atoms.append(_aa_atom(
            obj, next_id + k, name, 'C', resn, resi,
            center[0] + _HEX_R * (c * u[0] + s * v[0]),
            center[1] + _HEX_R * (c * u[1] + s * v[1]),
            center[2] + _HEX_R * (c * u[2] + s * v[2])))
    return atoms


# The capability AA_RESIDUES['PHE']['rings'][0] walk — asserted here so
# the scripted atoms always match the production ring table.
_PHE_WALK = ('CG', 'CD1', 'CE1', 'CZ', 'CE2', 'CD2')


def _phenylalanine(obj, center, normal_u, inplane_u, resi=5):
    """PHE fragment: backbone + CB + the capability ring walk as a
    regular hexagon with the scripted center/normal/in-plane axis."""
    assert tuple(capability.AA_RESIDUES['PHE']['rings'][0]) == _PHE_WALK
    atoms, next_id = _aa_backbone(obj, 600, 'PHE', resi,
                                  (center[0] - 2.0, center[1] - 4.0,
                                   center[2]))
    atoms.append(_aa_atom(obj, next_id, 'CB', 'C', 'PHE', resi,
                          center[0] - 1.5, center[1] - 1.0, center[2]))
    next_id += 1
    atoms.extend(_hex_ring(obj, next_id, 'PHE', resi, center, normal_u,
                           inplane_u, _PHE_WALK))
    return atoms


def _lysine(obj, nz_pos, ce_pos, cd_pos, cg_pos, resi=6):
    """LYS fragment with the charged ammonium NZ at ``nz_pos`` (charge
    center = NZ per gate 2.3, charge_atoms=('NZ',)) and the chain atoms
    at scripted positions; polar HZ1..3 ride on NZ at ~1.0 A."""
    atoms, next_id = _aa_backbone(obj, 700, 'LYS', resi,
                                  (cg_pos[0] - 2.0, cg_pos[1] - 2.0,
                                   cg_pos[2]))
    atoms.append(_aa_atom(obj, next_id, 'CB', 'C', 'LYS', resi,
                          cg_pos[0] - 1.5, cg_pos[1] + 1.0, cg_pos[2]))
    next_id += 1
    for name, pos in (('CG', cg_pos), ('CD', cd_pos), ('CE', ce_pos),
                      ('NZ', nz_pos)):
        elem = 'N' if name == 'NZ' else 'C'
        atoms.append(_aa_atom(obj, next_id, name, elem, 'LYS', resi,
                              pos[0], pos[1], pos[2]))
        next_id += 1
    for name, off in (('HZ1', (0.59, 0.59, 0.59)),
                      ('HZ2', (-0.82, 0.0, 0.58)),
                      ('HZ3', (0.0, -0.82, 0.58))):
        atoms.append(_aa_atom(obj, next_id, name, 'H', 'LYS', resi,
                              nz_pos[0] + off[0], nz_pos[1] + off[1],
                              nz_pos[2] + off[2]))
        next_id += 1
    return atoms


def _tert_ammonium_ligand(n_pos, sub_positions):
    """Protonated tertiary amine: N with exactly THREE non-H substituents
    at ``sub_positions`` (all single bonds) + one H — a ligand '+'
    charge group of kind ammonium whose substituent plane is DEFINED
    (the OQ-4 veto subject). The H position is irrelevant to the veto
    (only the three non-H substituent points define the plane)."""
    atoms = [_lig_atom(0, 'N1', 'N', n_pos[0], n_pos[1], n_pos[2])]
    bonds = []
    for k, pos in enumerate(sub_positions):
        atoms.append(_lig_atom(len(atoms), 'C%d' % (k + 2), 'C',
                               pos[0], pos[1], pos[2]))
        bonds.append((0, len(atoms) - 1, 1))
    atoms.append(_lig_atom(len(atoms), 'H9', 'H',
                           n_pos[0], n_pos[1], n_pos[2] - 1.01))
    bonds.append((0, len(atoms) - 1, 1))
    return atoms, bonds


# --- halogen/metal geometry helpers (plan 02-07b) ------------------------

_C_X_BOND = 1.77        # scripted C-X covalent length
_C_CB_BOND = 1.43       # scripted O...C bond length (acceptor's Y partner)


def _c_x_ligand(c_pos, x_pos, x_elem='CL'):
    """Minimal halogen donor: C0 bonded to X1 (default Cl) + three H on
    the C. The C is NOT a qualifying hydrophobe (neighbor X not in
    {C, H}); X alone is typed by row-6 donor typing (C-X, X in
    Cl/Br/I — C-F is excluded at TYPING, gate row 6)."""
    atoms = [_lig_atom(0, 'C1', 'C', c_pos[0], c_pos[1], c_pos[2]),
             _lig_atom(1, 'X2', x_elem, x_pos[0], x_pos[1], x_pos[2])]
    bonds = [(0, 1, 1)]
    for k, off in enumerate(((-0.66, 0.77, 0.0), (-0.66, -0.77, 0.0),
                             (0.0, 0.0, -1.09))):
        atoms.append(_lig_atom(len(atoms), 'H%d' % (k + 3), 'H',
                               c_pos[0] + off[0], c_pos[1] + off[1],
                               c_pos[2] + off[2]))
        bonds.append((0, len(atoms) - 1, 1))
    return atoms, bonds


def _halogen_positions(d_ax, donor_deg, acc_deg):
    """Scripted row-6 geometry: acceptor A at the ORIGIN, halogen X at
    (d_ax, 0, 0); the donor C is placed so the angle A-X-C at X equals
    ``donor_deg``, and the acceptor's Y partner at 1.43 A so the angle
    Y-A-X at A equals ``acc_deg``. All points in the xy-plane.
    Returns (c_pos, y_pos)."""
    donor_rad = math.radians(donor_deg)
    acc_rad = math.radians(acc_deg)
    # X->A is (-1, 0, 0); X->C is (-cos(donor), sin(donor), 0) so the
    # angle at X is exactly donor_deg.
    c_pos = (d_ax - _C_X_BOND * math.cos(donor_rad),
             _C_X_BOND * math.sin(donor_rad), 0.0)
    y_pos = (_C_CB_BOND * math.cos(acc_rad),
             _C_CB_BOND * math.sin(acc_rad), 0.0)
    return c_pos, y_pos


def _serine_og_cb(obj, og, cb):
    """SER fragment with OG at ``og`` and its bonded partner CB at
    ``cb`` (the row-6 acceptor angle needs Y); NO HG (acceptor-only
    side). CB is 1.43 A from OG; the backbone is scripted ~2.5/3.2 A
    from OG along +y so NOTHING heavy except CB sits within the
    detector's 2.0 A internal Y-pairing epsilon."""
    atoms, next_id = _aa_backbone(obj, 100, 'SER', 1,
                                  (og[0], og[1] + 4.6, og[2]))
    atoms.append(_aa_atom(obj, next_id, 'CB', 'C', 'SER', 1,
                          cb[0], cb[1], cb[2]))
    next_id += 1
    atoms.append(_aa_atom(obj, next_id, 'HB1', 'H', 'SER', 1,
                          cb[0] + 0.9, cb[1] + 0.5, cb[2]))
    next_id += 1
    atoms.append(_aa_atom(obj, next_id, 'HB2', 'H', 'SER', 1,
                          cb[0] - 0.7, cb[1] + 0.6, cb[2]))
    next_id += 1
    atoms.append(_aa_atom(obj, next_id, 'OG', 'O', 'SER', 1,
                          og[0], og[1], og[2]))
    return atoms


def _methionine_sd(obj, sd, cg):
    """MET fragment: backbone + CB + CG + SD at scripted positions.
    MET carries NO acceptors (thioether-S excluded from the halogen
    acceptor set, gate §3.5 — do not revisit), so SD at perfect C-X
    geometry must still form nothing."""
    atoms, next_id = _aa_backbone(obj, 400, 'MET', 4,
                                  (sd[0], sd[1] + 4.6, sd[2]))
    for name, pos in (('CB', (cg[0] - 1.35, cg[1], cg[2])),
                      ('CG', cg), ('SD', sd)):
        atoms.append(_aa_atom(obj, next_id, name,
                              'S' if name == 'SD' else 'C', 'MET', 4,
                              pos[0], pos[1], pos[2]))
        next_id += 1
    return atoms


def _aa_c_x_fragment(obj, c_pos, x_pos):
    """Bogus 'SER'-labeled fragment carrying a C..CL pair (CB + an atom
    named 'CL'): no capability table can EVER type an AA-side halogen
    donor — plan case (e) asserts nothing forms even at textbook
    flipped geometry. The 'CL' atom counts as unclassified."""
    atoms, next_id = _aa_backbone(obj, 300, 'SER', 3,
                                  (c_pos[0] + 10.0, c_pos[1] + 10.0,
                                   c_pos[2]))
    atoms.append(_aa_atom(obj, next_id, 'CB', 'C', 'SER', 3,
                          c_pos[0], c_pos[1], c_pos[2]))
    next_id += 1
    atoms.append(_aa_atom(obj, next_id, 'CL', 'CL', 'SER', 3,
                          x_pos[0], x_pos[1], x_pos[2]))
    return atoms


def _histidine(obj, nd1_pos, start_id=500):
    """HIS fragment (neutral HIE-like, OQ-3/D2): backbone + CB + CG +
    ND1 at ``nd1_pos`` — ND1 is the ring-N acceptor the metal type
    chelates (capability HIS acceptors = ('ND1',); the metal row is
    DISTANCE-ONLY, no polar H needed anywhere)."""
    atoms, next_id = _aa_backbone(obj, start_id, 'HIS', 5,
                                  (nd1_pos[0] - 5.0, nd1_pos[1] - 5.0,
                                   nd1_pos[2]))
    atoms.append(_aa_atom(obj, next_id, 'CB', 'C', 'HIS', 5,
                          nd1_pos[0] - 2.5, nd1_pos[1] + 2.0,
                          nd1_pos[2]))
    next_id += 1
    atoms.append(_aa_atom(obj, next_id, 'CG', 'C', 'HIS', 5,
                          nd1_pos[0] - 1.38, nd1_pos[1], nd1_pos[2]))
    next_id += 1
    atoms.append(_aa_atom(obj, next_id, 'ND1', 'N', 'HIS', 5,
                          nd1_pos[0], nd1_pos[1], nd1_pos[2]))
    return atoms


def _metal_ligand(elem, m_pos):
    """Single-atom ligand carrying element ``elem`` at ``m_pos``
    (ZN = approved row-7 metal; NA = NOT in METAL_ELEMENTS)."""
    return [_lig_atom(0, elem, elem, m_pos[0], m_pos[1], m_pos[2])], []


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


# ---------------------------------------------------------------------------
# 02-07 RED spec 1 — pi_stacking (row 3: one uniform test for parallel
# AND T-shaped; sub-type recorded as a metric only)
# ---------------------------------------------------------------------------

class TestPiStacking(unittest.TestCase):
    """Row 3 (gate §2.2): ring-center dist < 5.5 A AND normals within
    30 deg of parallel OR of perpendicular AND projected-center offset
    < 2.0 A — the sub-type P/T is a METRIC; the type is always
    'pi_stacking'. Ligand benzene ring at origin, normal +z; the AA
    ring is PHE scripted from the capability walk."""

    def _pi(self, center, normal, u):
        lig_atoms, lig_bonds = _benzene_ligand()
        phe = _phenylalanine('aa_phe', center, normal, u)
        atoms, bonds = _scene(lig_atoms, lig_bonds, [phe])
        return _of_type(detector.detect_part1(atoms, bonds),
                        'pi_stacking')

    def test_parallel_formed_subtype_p(self):
        # Ring center (1.0, 0, 4.5): d = sqrt(21.25) < 5.5, normals
        # parallel, both cross-projections give offset 1.0 < 2.0.
        records = self._pi((1.0, 0.0, 4.5), (0.0, 0.0, 1.0),
                           (1.0, 0.0, 0.0))
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record['aa']['resn'], 'PHE')
        self.assertEqual(record['aa']['role'], 'ring')
        self.assertEqual(record['lig']['role'], 'ring')
        self.assertAlmostEqual(record['metrics']['d_center'],
                               math.sqrt(21.25), places=6)
        self.assertAlmostEqual(record['metrics']['angle_deg'], 0.0,
                               places=6)
        self.assertAlmostEqual(record['metrics']['offset'], 1.0,
                               places=6)
        self.assertEqual(record['metrics']['subtype'], 'P')
        self.assertEqual(set(record['metrics']),
                         {'d_center', 'angle_deg', 'offset', 'subtype'})
        self.assertEqual(record['aa']['atom_ids'],
                         [607, 608, 609, 610, 611, 612])
        self.assertEqual(record['lig']['atom_ids'], [0, 1, 2, 3, 4, 5])
        self.assertTrue(record['formed'])

    def test_parallel_5p6_not_formed(self):
        # Center distance 5.6 A exceeds the strict 5.5 A row-3 cutoff.
        self.assertEqual(self._pi((0.0, 0.0, 5.6), (0.0, 0.0, 1.0),
                                  (1.0, 0.0, 0.0)), [])

    def test_t_shaped_formed_subtype_t(self):
        # Ring plane perpendicular (normal +x), center 5.0 A away with
        # projected offset 1.0: the min cross-projection (AA center into
        # the ligand plane) keeps the hit; subtype 'T'.
        records = self._pi((1.0, 0.0, 4.898979485566356),
                           (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertAlmostEqual(record['metrics']['d_center'], 5.0,
                               places=6)
        self.assertAlmostEqual(record['metrics']['angle_deg'], 90.0,
                               places=6)
        self.assertAlmostEqual(record['metrics']['offset'], 1.0,
                               places=6)
        self.assertEqual(record['metrics']['subtype'], 'T')

    def test_offset_2p5_not_formed(self):
        # Parallel stack at offset 2.5 (distance sqrt(26.5) < 5.5 and
        # angle fine) — the offset test alone must kill the hit.
        self.assertEqual(self._pi((2.5, 0.0, 4.5), (0.0, 0.0, 1.0),
                                  (1.0, 0.0, 0.0)), [])

    def test_normals_45deg_neither_nor_formed(self):
        # Normals 45 deg off parallel: within NEITHER 30 deg of parallel
        # NOR 30 deg of perpendicular — the angle test alone kills it
        # (distance 4.5 and offset 0.0 both pass).
        s = math.sqrt(0.5)
        self.assertEqual(self._pi((0.0, 0.0, 4.5), (s, 0.0, s),
                                  (s, 0.0, -s)), [])

    def test_backbone_atoms_never_join_ring_test_d1(self):
        # D1: backbone + CB only — a PHE object WITHOUT its side-chain
        # ring atoms carries no ring feature; nothing can stack.
        lig_atoms, lig_bonds = _benzene_ligand()
        atoms_phe, _ = _aa_backbone('aa_phe', 800, 'PHE', 5,
                                    (0.0, 0.0, 3.0))
        atoms_phe.append(_aa_atom('aa_phe', 806, 'CB', 'C', 'PHE', 5,
                                  0.5, 1.0, 3.5))
        atoms, bonds = _scene(lig_atoms, lig_bonds, [atoms_phe])
        self.assertEqual(_of_type(detector.detect_part1(atoms, bonds),
                                  'pi_stacking'), [])
        self.assertEqual(_of_type(detector.detect_part1(atoms, bonds),
                                  'cation_pi'), [])

    def test_records_agree_with_capability_tables(self):
        # DETECT-04: PHE is pi_stacking-capable against a ring ligand.
        lig_atoms, lig_bonds = _benzene_ligand()
        profile = capability.ligand_profile(lig_atoms, lig_bonds)
        self.assertTrue(capability.aa_capable('PHE', 'pi_stacking',
                                              profile))
        self.assertFalse(capability.aa_capable('ALA', 'pi_stacking',
                                               profile))


# ---------------------------------------------------------------------------
# 02-07 RED spec 2 — cation_pi (row 4: <= 6.0 A + 2.0 A offset, BOTH
# directions per D4; OQ-4 ligand-side anti-artifact veto, AA-side none)
# ---------------------------------------------------------------------------

# sqrt(5.5^2 - 1.0^2) — z for a 5.5 A charge-center distance with a 1.0 A
# projected offset (case a/b geometry).
_CATION_Z = 5.408326913195984


class TestCationPi(unittest.TestCase):
    """Row 4 (gate §2.2 + D4 + §4.4): charge center <-> ring center
    <= 6.0 A AND projected charge offset < 2.0 A, direction recorded.
    The tertiary-amine anti-artifact veto applies ONLY when the ligand
    carries the cation (documented asymmetry)."""

    def _run(self, lig_atoms, lig_bonds, aa_lists, type_='cation_pi'):
        atoms, bonds = _scene(lig_atoms, lig_bonds, aa_lists)
        return _of_type(detector.detect_part1(atoms, bonds), type_)

    def test_ligand_ring_over_aa_cation_formed(self):
        # (a) LYS NZ 5.5 A from the benzene center, projected offset 1.0.
        lig_atoms, lig_bonds = _benzene_ligand()
        nz = (1.0, 0.0, _CATION_Z)
        lys = _lysine('aa_lys', nz, (2.2, 0.5, _CATION_Z + 1.4),
                      (3.4, 1.0, _CATION_Z + 2.8),
                      (4.2, 0.5, _CATION_Z + 4.2))
        records = self._run(lig_atoms, lig_bonds, [lys])
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record['aa']['resn'], 'LYS')
        self.assertEqual(record['aa']['role'], 'cation')
        self.assertEqual(record['lig']['role'], 'ring')
        self.assertEqual(record['aa']['atom_ids'], [710])
        self.assertEqual(record['lig']['atom_ids'], [0, 1, 2, 3, 4, 5])
        self.assertEqual(record['metrics']['direction'],
                         'aa_cation_over_lig_ring')
        self.assertAlmostEqual(record['metrics']['d_center'], 5.5,
                               places=6)
        self.assertAlmostEqual(record['metrics']['offset'], 1.0,
                               places=6)
        self.assertEqual(set(record['metrics']),
                         {'d_center', 'offset', 'direction'})
        self.assertTrue(record['formed'])

    def test_ligand_cation_over_aa_ring_formed(self):
        # (b) primary ammonium ligand (one C neighbor — NOT a veto
        # subject) N at origin; AA PHE ring 5.5 A away, offset 1.0.
        lig_atoms, lig_bonds = _ammonium_ligand(
            (0.0, 0.0, 0.0), ((0.59, 0.59, 0.59), (-0.82, 0.0, 0.58),
                              (0.0, -0.82, 0.58)))
        phe = _phenylalanine('aa_phe', (1.0, 0.0, _CATION_Z),
                             (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
        records = self._run(lig_atoms, lig_bonds, [phe])
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record['aa']['role'], 'ring')
        self.assertEqual(record['lig']['role'], 'cation')
        self.assertEqual(record['lig']['atom_ids'], [0])
        self.assertEqual(record['metrics']['direction'],
                         'aa_ring_under_lig_cation')
        self.assertAlmostEqual(record['metrics']['d_center'], 5.5,
                               places=6)
        self.assertAlmostEqual(record['metrics']['offset'], 1.0,
                               places=6)

    def test_distance_6p5_not_formed(self):
        # (c) charge center 6.5 A from the ring center > 6.0 A cutoff.
        lig_atoms, lig_bonds = _ammonium_ligand(
            (0.0, 0.0, 0.0), ((0.59, 0.59, 0.59), (-0.82, 0.0, 0.58),
                              (0.0, -0.82, 0.58)))
        phe = _phenylalanine('aa_phe', (0.0, 0.0, 6.5),
                             (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
        self.assertEqual(self._run(lig_atoms, lig_bonds, [phe]), [])

    def test_offset_2p5_not_formed(self):
        # (d) distance 5.5 A passes; projected offset 2.5 >= 2.0 kills.
        lig_atoms, lig_bonds = _ammonium_ligand(
            (0.0, 0.0, 0.0), ((0.59, 0.59, 0.59), (-0.82, 0.0, 0.58),
                              (0.0, -0.82, 0.58)))
        phe = _phenylalanine('aa_phe', (2.5, 0.0, 4.898979485566356),
                             (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
        self.assertEqual(self._run(lig_atoms, lig_bonds, [phe]), [])

    def test_ligand_tertiary_amine_veto_fires(self):
        # (e) OQ-4 veto: protonated tertiary amine in the SAME would-be
        # formed geometry as case (b), but its substituent plane normal
        # is ~perpendicular to the ring normal (amine stacked 'through'
        # the ligand side) — the veto must reject the hit.
        subs = [(1.47, 0.0, 0.0), (-0.735, 0.0, 1.2727481),
                (-0.735, 0.0, -1.2727481)]          # plane normal ~ +y
        lig_atoms, lig_bonds = _tert_ammonium_ligand((0.0, 0.0, 0.0),
                                                     subs)
        phe = _phenylalanine('aa_phe', (1.0, 0.0, _CATION_Z),
                             (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
        self.assertEqual(self._run(lig_atoms, lig_bonds, [phe]), [])

    def test_tertiary_amine_plane_parallel_formed(self):
        # Control for the veto: identical tertiary-amine geometry but
        # with the substituent plane normal ~parallel to the ring normal
        # (pole-on) — the veto passes and the hit forms. This proves the
        # miss above is the VETO, not a distance/offset accident.
        subs = [(1.47, 0.0, 0.0), (-0.735, 1.2727481, 0.0),
                (-0.735, -1.2727481, 0.0)]          # plane normal ~ +z
        lig_atoms, lig_bonds = _tert_ammonium_ligand((0.0, 0.0, 0.0),
                                                     subs)
        phe = _phenylalanine('aa_phe', (1.0, 0.0, _CATION_Z),
                             (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
        records = self._run(lig_atoms, lig_bonds, [phe])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['metrics']['direction'],
                         'aa_ring_under_lig_cation')

    def test_aa_cation_side_has_no_veto_asymmetry(self):
        # Documented OQ-4 asymmetry: arrange the LYS chain in the exact
        # through-plane shape the ligand veto rejects (CG/CD/CE in a
        # plane whose normal is ~perpendicular to the ring normal) —
        # the AA side has no such veto and the hit STILL forms.
        lig_atoms, lig_bonds = _benzene_ligand()
        nz = (1.0, 0.0, _CATION_Z)
        lys = _lysine('aa_lys', nz,
                      (nz[0] + 1.47, 0.0, nz[2]),
                      (nz[0] - 0.735, 0.0, nz[2] + 1.2727481),
                      (nz[0] - 0.735, 0.0, nz[2] - 1.2727481))
        records = self._run(lig_atoms, lig_bonds, [lys])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['metrics']['direction'],
                         'aa_cation_over_lig_ring')
        self.assertAlmostEqual(records[0]['metrics']['d_center'], 5.5,
                               places=6)

    def test_records_agree_with_capability_tables(self):
        # DETECT-04, both directions (D4): LYS cation against a ring
        # ligand; PHE ring against a cationic ligand.
        lig_atoms, lig_bonds = _benzene_ligand()
        ring_profile = capability.ligand_profile(lig_atoms, lig_bonds)
        self.assertTrue(capability.aa_capable('LYS', 'cation_pi',
                                              ring_profile))
        self.assertFalse(capability.aa_capable('ASP', 'cation_pi',
                                               ring_profile))
        cat_atoms, cat_bonds = _ammonium_ligand(
            (0.0, 0.0, 0.0), ((0.59, 0.59, 0.59), (-0.82, 0.0, 0.58),
                              (0.0, -0.82, 0.58)))
        cat_profile = capability.ligand_profile(cat_atoms, cat_bonds)
        self.assertTrue(capability.aa_capable('PHE', 'cation_pi',
                                              cat_profile))
        self.assertFalse(capability.aa_capable('ALA', 'cation_pi',
                                               cat_profile))


# ---------------------------------------------------------------------------
# 02-07b RED spec 1 — halogen (row 6: A...X <= 4.0 AND two angle windows;
# enumeration STRUCTURALLY (AA acceptor O/N/S) x (ligand C-X, X in
# Cl/Br/I); C-F excluded at typing; Met excluded per §3.5; AA-side
# halogen donors unrepresentable)
# ---------------------------------------------------------------------------

class TestHalogen(unittest.TestCase):
    """Row 6 (gate §2.2): SER OG acceptor vs a ligand C-Cl donor, both
    angle windows scripted exactly via _halogen_positions (A at origin,
    X on +x, everything in the xy-plane)."""

    def _detect(self, d_ax, donor_deg, acc_deg, x_elem='CL'):
        c_pos, y_pos = _halogen_positions(d_ax, donor_deg, acc_deg)
        lig_atoms, lig_bonds = _c_x_ligand(c_pos, (d_ax, 0.0, 0.0),
                                           x_elem)
        ser = _serine_og_cb('aa_ser', (0.0, 0.0, 0.0), y_pos)
        atoms, bonds = _scene(lig_atoms, lig_bonds, [ser])
        return detector.detect(atoms, bonds)

    def test_formed_3p5_both_windows(self):
        # (a) d = 3.5, donor angle 165 (165 +- 30), acceptor 120
        # (120 +- 30) -> FORMED.
        records = self._detect(3.5, 165.0, 120.0)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record['type'], 'halogen')
        self.assertEqual(record['aa']['role'], 'acceptor')
        self.assertEqual(record['lig']['role'], 'donor')
        self.assertEqual(record['aa']['resn'], 'SER')
        # scripted ids: OG = 109; ligand C1 = 0, X2 = 1
        self.assertEqual(record['aa']['atom_ids'], [109])
        self.assertEqual(record['lig']['atom_ids'], [0, 1])
        self.assertAlmostEqual(record['metrics']['d_ax'], 3.5, places=6)
        self.assertAlmostEqual(record['metrics']['donor_angle_deg'],
                               165.0, places=6)
        self.assertAlmostEqual(record['metrics']['acc_angle_deg'],
                               120.0, places=6)
        self.assertEqual(set(record['metrics']),
                         {'d_ax', 'donor_angle_deg', 'acc_angle_deg'})
        self.assertTrue(record['formed'])

    def test_donor_angle_100_not_formed(self):
        # (b) donor angle 100 out of the (135, 195) window; acceptor
        # angle still passes.
        self.assertEqual(self._detect(3.5, 100.0, 120.0), [])

    def test_acceptor_angle_60_not_formed(self):
        # (c) acceptor angle 60 out of the (90, 150) window; donor
        # angle still passes.
        self.assertEqual(self._detect(3.5, 165.0, 60.0), [])

    def test_c_f_excluded_at_typing_no_candidates(self):
        # (d) IDENTical geometry to (a) but X = F: C-F donors are
        # excluded at TYPING (row 6) — no candidates exist at all.
        c_pos, y_pos = _halogen_positions(3.5, 165.0, 120.0)
        lig_atoms, lig_bonds = _c_x_ligand(c_pos, (3.5, 0.0, 0.0), 'F')
        ser = _serine_og_cb('aa_ser', (0.0, 0.0, 0.0), y_pos)
        atoms, bonds = _scene(lig_atoms, lig_bonds, [ser])
        features = detector.extract_features(atoms, bonds)
        self.assertEqual(features['lig']['halogen_donors'], [])
        self.assertEqual(detector.detect(atoms, bonds), [])

    def test_aa_side_halogen_donor_never_enumerated(self):
        # (e) flipped sides: ligand carbonyl O at the ACCEPTOR position,
        # an AA-side C...CL at textbook donor positions/angles.
        # Enumeration is strictly (AA acceptor) x (ligand C-X), and no
        # capability table types an AA halogen donor — nothing can form.
        x_pos = (1.77, 0.0, 0.0)
        rad = math.radians(165.0)
        a_pos = ((x_pos[0] - 3.5 * math.cos(rad)),
                 3.5 * math.sin(rad), 0.0)
        lig_atoms, lig_bonds = _carbonyl_ligand(a_pos)
        aa = _aa_c_x_fragment('aa_ser', (0.0, 0.0, 0.0), x_pos)
        atoms, bonds = _scene(lig_atoms, lig_bonds, [aa])
        self.assertEqual(detector.detect(atoms, bonds), [])
        # feature-level structural proof: nothing typed on either side
        features = detector.extract_features(atoms, bonds)
        self.assertEqual(features['lig']['halogen_donors'], [])
        self.assertEqual(features['aa']['aa_ser']['acceptors'], [])
        self.assertEqual(features['unclassified_aa_atoms'], 1)  # the CL

    def test_met_thioether_s_excluded_per_3p5_ruling(self):
        # §3.5 ruling (do not revisit): MET SD at PERFECT row-6 geometry
        # forms nothing — MET carries no acceptor names at all, so the
        # candidate is rejected at classification (not geometry).
        c_pos, y_pos = _halogen_positions(3.5, 165.0, 120.0)
        lig_atoms, lig_bonds = _c_x_ligand(c_pos, (3.5, 0.0, 0.0))
        met = _methionine_sd('aa_met', (0.0, 0.0, 0.0), y_pos)
        atoms, bonds = _scene(lig_atoms, lig_bonds, [met])
        features = detector.extract_features(atoms, bonds)
        self.assertEqual(features['aa']['aa_met']['acceptors'], [])
        self.assertEqual(detector.detect(atoms, bonds), [])

    def test_distance_boundary_4p0_yes_4p1_no(self):
        # Row 6 distance is (<=) like row 1: exactly 4.0 forms, 4.1 not.
        self.assertEqual(
            len(_of_type(self._detect(4.0, 165.0, 120.0), 'halogen')), 1)
        self.assertEqual(_of_type(self._detect(4.1, 165.0, 120.0),
                                  'halogen'), [])

    def test_donor_window_boundary_134_not_formed(self):
        self.assertEqual(self._detect(3.5, 134.0, 120.0), [])

    def test_min_dist_guard_rejects_coincident_geometry(self):
        self.assertEqual(self._detect(0.4, 165.0, 120.0), [])


# ---------------------------------------------------------------------------
# 02-07b RED spec 2 — metal (row 7: metal...chelator <= 3.0 A,
# DISTANCE-ONLY; gated by ligand_has_metal; chelators = AA side-chain
# N/O/S acceptor atoms)
# ---------------------------------------------------------------------------

class TestMetal(unittest.TestCase):

    def _detect(self, lig_atoms, lig_bonds, aa_lists):
        atoms, bonds = _scene(lig_atoms, lig_bonds, aa_lists)
        return detector.detect(atoms, bonds)

    def test_formed_zn_his_nd1_2p5(self):
        # (a) approved ZN + HIS ring N at 2.5 A -> FORMED, aa role
        # 'chelator' (distance-only: no angles exist in row 7).
        lig_atoms, lig_bonds = _metal_ligand('ZN', (0.0, 0.0, 0.0))
        his = _histidine('aa_his', (2.5, 0.0, 0.0))
        records = self._detect(lig_atoms, lig_bonds, [his])
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record['type'], 'metal')
        self.assertEqual(record['aa']['role'], 'chelator')
        self.assertEqual(record['lig']['role'], 'metal')
        self.assertEqual(record['aa']['resn'], 'HIS')
        # scripted ids: ND1 = 514 (500 start + 14), ligand metal = 0
        self.assertEqual(record['aa']['atom_ids'], [514])
        self.assertEqual(record['lig']['atom_ids'], [0])
        self.assertEqual(set(record['metrics']), {'d_metal'})
        self.assertAlmostEqual(record['metrics']['d_metal'], 2.5,
                               places=6)
        self.assertTrue(record['formed'])

    def test_boundary_3p0_formed(self):
        lig_atoms, lig_bonds = _metal_ligand('ZN', (0.0, 0.0, 0.0))
        his = _histidine('aa_his', (3.0, 0.0, 0.0))
        records = _of_type(self._detect(lig_atoms, lig_bonds, [his]),
                           'metal')
        self.assertEqual(len(records), 1)
        self.assertAlmostEqual(records[0]['metrics']['d_metal'], 3.0,
                               places=6)

    def test_3p2_not_formed(self):
        # (b) 3.2 A exceeds METAL_D_MAX (3.0).
        lig_atoms, lig_bonds = _metal_ligand('ZN', (0.0, 0.0, 0.0))
        his = _histidine('aa_his', (3.2, 0.0, 0.0))
        self.assertEqual(self._detect(lig_atoms, lig_bonds, [his]), [])

    def test_no_metal_in_ligand_gate_not_even_enumerated(self):
        # (c) SAME geometry but the ligand carries NO metal: no record,
        # and the metal branch is not even enumerated — the gate is
        # capability.ligand_has_metal (detection research §7.6).
        lig_atoms, lig_bonds = _carbonyl_ligand((2.5, 0.0, 0.0))
        his = _histidine('aa_his', (2.5, 0.0, 0.0))
        atoms, bonds = _scene(lig_atoms, lig_bonds, [his])
        with mock.patch.object(detector, '_metal_records',
                               wraps=detector._metal_records) as spy:
            records = detector.detect(atoms, bonds)
        self.assertEqual(spy.call_count, 0)
        self.assertEqual(records, [])

    def test_element_not_in_metal_elements_no_record(self):
        # (d) 'NA' is not in the approved METAL_ELEMENTS list (OQ-7) —
        # not typed as a metal AT ALL, so nothing can coordinate.
        lig_atoms, lig_bonds = _metal_ligand('NA', (0.0, 0.0, 0.0))
        his = _histidine('aa_his', (2.5, 0.0, 0.0))
        atoms, bonds = _scene(lig_atoms, lig_bonds, [his])
        features = detector.extract_features(atoms, bonds)
        self.assertEqual(features['lig']['metals'], [])
        self.assertEqual(detector.detect(atoms, bonds), [])

    def test_non_chelator_aa_no_record(self):
        # ALA carries no side-chain N/O/S acceptor atoms: CB at 2.5 A
        # from ZN forms nothing (chelators = acceptor atoms only).
        lig_atoms, lig_bonds = _metal_ligand('ZN', (0.0, 0.0, 0.0))
        ala = _alanine('aa_ala', (2.5, 0.0, 0.0))
        self.assertEqual(self._detect(lig_atoms, lig_bonds, [ala]), [])

    def test_min_dist_guard_rejects_coincident_metal(self):
        lig_atoms, lig_bonds = _metal_ligand('ZN', (0.0, 0.0, 0.0))
        his = _histidine('aa_his', (0.3, 0.0, 0.0))
        self.assertEqual(self._detect(lig_atoms, lig_bonds, [his]), [])


class TestHalogenMetalCapabilityParity(unittest.TestCase):
    """DETECT-04 for rows 6/7: every formed record's (resn, type) must
    be capable under capability.aa_capable with the same profile, and
    the scripted exclusions (Met, metal-free ligand) stay incapable."""

    def test_halogen_capability_parity(self):
        c_pos, y_pos = _halogen_positions(3.5, 165.0, 120.0)
        lig_atoms, lig_bonds = _c_x_ligand(c_pos, (3.5, 0.0, 0.0))
        ser = _serine_og_cb('aa_ser', (0.0, 0.0, 0.0), y_pos)
        atoms, bonds = _scene(lig_atoms, lig_bonds, [ser])
        profile = capability.ligand_profile(atoms[:5], bonds)
        self.assertTrue(profile['has_halogen_donor'])
        self.assertFalse(profile['has_metal'])
        records = detector.detect(atoms, bonds)
        self.assertEqual(len(records), 1)
        self.assertTrue(capability.aa_capable(
            records[0]['aa']['resn'], 'halogen', profile))
        # the recorded exclusions:
        self.assertTrue(capability.aa_capable('SER', 'halogen', profile))
        self.assertFalse(capability.aa_capable('MET', 'halogen',
                                               profile))   # §3.5
        self.assertFalse(capability.aa_capable('ALA', 'halogen',
                                               profile))

    def test_metal_capability_parity(self):
        lig_atoms, lig_bonds = _metal_ligand('ZN', (0.0, 0.0, 0.0))
        his = _histidine('aa_his', (2.5, 0.0, 0.0))
        atoms, bonds = _scene(lig_atoms, lig_bonds, [his])
        profile = capability.ligand_profile(atoms[:1], bonds)
        self.assertTrue(profile['has_metal'])
        self.assertEqual(profile['metal_elements'], ['ZN'])
        records = detector.detect(atoms, bonds)
        self.assertEqual(len(records), 1)
        self.assertTrue(capability.aa_capable(
            records[0]['aa']['resn'], 'metal', profile))
        self.assertTrue(capability.aa_capable('HIS', 'metal', profile))
        self.assertFalse(capability.aa_capable('MET', 'metal', profile))
        self.assertFalse(capability.aa_capable('ALA', 'metal', profile))
        # metal-free ligand mirrors the detection gate in capability:
        cf_atoms = [_lig_atom(0, 'C1', 'C', 0.0, 0.0, 0.0)]
        self.assertFalse(capability.aa_capable(
            'HIS', 'metal', capability.ligand_profile(cf_atoms, [])))


if __name__ == '__main__':
    unittest.main()
