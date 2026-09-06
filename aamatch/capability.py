"""aamatch.capability -- the SINGLE atom/residue typing home (plan 02-05).

Layer: PURE. Shared by the generator (solvability, GEN-04), the detector
(typing agreement, DETECT-04) and the Hint (PLAY-05). The detection
research's proposed ``chem_types.py`` is merged here per the recorded
gate decision (docs/DETECTION_THRESHOLDS.md §4.2): DETECT-04 "capability
checks and scoring agree" holds BY CONSTRUCTION only if both sides read
the same tables -- this module is that table.

Every table row is transcribed from the APPROVED DETECT-03 gate document
(docs/DETECTION_THRESHOLDS.md, approved 2026-09-06, human gate at the
02-01 checkpoint). The project truthfulness rule forbids inventing
chemistry; ``source:`` comments tie each row group to the approving
section. Any change to capability typing is a DETECTOR_VERSION bump
event (gate §4.7) -- never a silent edit.

Recorded policies carried by this module (each binds the generator, the
detector and the Hint simultaneously):

- D1 -- SIDE-CHAIN-ONLY capability (gate §4.1): backbone and cap atoms
  are NEVER typed as interacting for grid AAs. Donor/acceptor matching
  is restricted to the ``side_chain`` atom-name set of AA_RESIDUES; the
  AA-side hydrophobic rule is residue-NAME-based (gate §3.4) -- the
  atom-level carbon rule applies to the ligand side only. CB is
  deliberately absent from every side_chain set (it anchors no typed
  role; the plan's SER/LYS/ARG examples pin this convention), so ALA and
  GLY carry empty side_chain sets. Carbon-bonded side-chain hydrogens
  are likewise omitted -- they participate in no typed interaction (all
  typed roles are heteroatom-based).
- SINGLE TYPING HOME (gate §4.2): this module is the only place that
  knows "LYS side chain = cationic amine; PHE = one six-ring; SER =
  donor+acceptor OG". No parallel hand-written matrix anywhere.
- FAIL-CLOSED DONOR TYPING (gate §5 item 3): an O/N/S without an
  attached H is not a donor. On the ligand side this is computed from
  the bond block (Task 2, ``ligand_profile``); on the AA side the
  residue table lists donor heavy atoms whose polar Hs are materialized
  (plan 02-13 / SMOKE-03 field-verifies every atom name against the
  materialized fragments -- do not ship detector code that guesses
  protonation).
- NEUTRAL-HIS POLICY (gate OQ-3 / D2): HIS is bundled neutral
  (HIE-like tautomer -- donor NE2 + acceptor ND1), therefore NOT a
  salt-bridge cation in v1 and a cation-pi RING role only. A HIP entry
  would be an additive residue-table row (versioned change).
- Polarity/direction (gate D3/D4): salt-bridge capability depends on
  the LIGAND's charge sign; cation-pi counts EITHER direction
  (AA-cation over ligand ring, or AA-ring under ligand cation) --
  encoded in ``aa_capable``.

Dependency direction: stdlib ``math`` + pure ``vec3`` (planarity
fallback only) + ``setup_state`` (INTERACTION_TYPES -- the ONE enum
home, generation research §3.1). No itertools (recorded 02-01
convention), no numpy, no pymol.
"""

import math

from .vec3 import sub, dot, cross, norm, scale
from .setup_state import INTERACTION_TYPES


def _entry(side_chain, donors=(), acceptors=(), charge=None,
           charge_atoms=(), rings=(), hydrophobic=False):
    """Build one AA_RESIDUES record (uniform shape, immutably held).

    Keys: 'side_chain' frozenset of atom names (heavy side-chain atoms
    beyond CB + polar Hs attached to N/O/S), 'donors'/'acceptors' lists
    of heavy-atom names (fail-closed: a donor H must be materialized),
    'charge' = (sign|None, [representative atom names]), 'rings' = list
    of cyclic atom-name walks, 'hydrophobic' = bool (residue-name rule,
    gate §3.4).
    """
    return {
        'side_chain': frozenset(side_chain),
        'donors': list(donors),
        'acceptors': list(acceptors),
        'charge': (charge, list(charge_atoms)),
        'rings': [list(r) for r in rings],
        'hydrophobic': bool(hydrophobic),
    }


# The 20 standard AAs. Atom names are standard PDB naming; ring lists
# are stored as valid cyclic walks (row-9 ring geometry may take the
# first/third/fifth-atom plane). SMOKE-03 (plan 02-13) field-verifies
# every name against the materialized chempy fragments (known variant:
# chempy digit-prefixes the HIS ring H -- '2HE' on hie per the
# materialization probe -- reconcile there, never here silently).
#
# source: docs/DETECTION_THRESHOLDS.md §3.3 (table rows) + §3.5
# (resolved sets) + §2.3 (charge-group representatives), approved
# 2026-09-06.
AA_RESIDUES = {
    'ALA': _entry(() , hydrophobic=True),
    'ARG': _entry(
        # guanidinium chain + terminal Ns; donors per the approved cell
        # name NH1/NH2 (the fragment's NE/HE is a side-chain atom but is
        # not a table-listed donor -- widening = §4.7 version event).
        ('CG', 'CD', 'NE', 'CZ', 'NH1', 'NH2',
         'HE', 'HH11', 'HH12', 'HH21', 'HH22'),
        donors=('NH1', 'NH2'),
        # charge rep: guanidino center = midpoint of the two terminal N
        # (gate §2.3, BINANA verified table).
        charge='+', charge_atoms=('NH1', 'NH2')),
    'ASN': _entry(
        ('CG', 'OD1', 'ND2', 'HD21', 'HD22'),
        donors=('ND2',), acceptors=('OD1',)),
    'ASP': _entry(
        # carboxylate O acceptors: RESOLVE->ADOPTED INCLUDE (BINANA
        # O/N/S rule; gate §3.3 Asp row). No polar H under D2 (fixed -).
        ('CG', 'OD1', 'OD2'),
        acceptors=('OD1', 'OD2'),
        charge='-', charge_atoms=('OD1', 'OD2')),
    'CYS': _entry(
        # thiol donor; SG also an accepted acceptor per the §3.5 set.
        ('SG', 'HG'),
        donors=('SG',), acceptors=('SG',)),
    'GLN': _entry(
        ('CG', 'CD', 'OE1', 'NE2', 'HE21', 'HE22'),
        donors=('NE2',), acceptors=('OE1',)),
    'GLU': _entry(
        ('CG', 'CD', 'OE1', 'OE2'),
        acceptors=('OE1', 'OE2'),
        charge='-', charge_atoms=('OE1', 'OE2')),
    'GLY': _entry(()),  # no side chain (gate §3.3 Gly row)
    'HIS': _entry(
        # Neutral HIE-like tautomer (OQ-3/D2): NE2 carries the ring H
        # (donor), ND1 is the acceptor; NO charge (not a salt-bridge
        # cation in v1); one 5-ring. HID/HIP variants = additive rows
        # later (versioned).
        ('CG', 'ND1', 'CD2', 'CE1', 'NE2', 'HE2'),
        donors=('NE2',), acceptors=('ND1',),
        rings=(('CG', 'ND1', 'CE1', 'NE2', 'CD2'),)),
    'ILE': _entry(('CG1', 'CG2', 'CD1'), hydrophobic=True),
    'LEU': _entry(('CG', 'CD1', 'CD2'), hydrophobic=True),
    'LYS': _entry(
        ('CG', 'CD', 'CE', 'NZ', 'HZ1', 'HZ2', 'HZ3'),
        donors=('NZ',),
        # charge rep: amine N (gate §2.3, BINANA "Lys -- amine N").
        charge='+', charge_atoms=('NZ',)),
    'MET': _entry(
        # thioether-S acceptor EXCLUDED in v1 (recorded DETECT-03
        # disagreement, gate §3.3 Met row); hydrophobic [HUMAN] set.
        ('CG', 'SD', 'CE'),
        hydrophobic=True),
    'PHE': _entry(
        ('CG', 'CD1', 'CD2', 'CE1', 'CE2', 'CZ'),
        rings=(('CG', 'CD1', 'CE1', 'CZ', 'CE2', 'CD2'),),
        hydrophobic=True),
    'PRO': _entry(
        # no side-chain N-H (ring N is the backbone N) -- not a donor.
        ('CG', 'CD'),
        hydrophobic=True),
    'SER': _entry(
        ('OG', 'HG'),
        donors=('OG',), acceptors=('OG',)),
    'THR': _entry(
        ('OG1', 'CG2', 'HG1'),
        donors=('OG1',), acceptors=('OG1',)),
    'TRP': _entry(
        # two rings (BINANA assignment, gate §2.2 row 8): indole 5-ring
        # + benzene 6-ring sharing the CD2-CE2 bond.
        ('CG', 'CD1', 'CD2', 'NE1', 'CE2', 'CE3', 'CZ2', 'CZ3', 'CH2',
         'HE1'),
        donors=('NE1',),
        rings=(('CG', 'CD1', 'NE1', 'CE2', 'CD2'),
               ('CD2', 'CE2', 'CE3', 'CZ2', 'CZ3', 'CH2')),
        hydrophobic=True),
    'TYR': _entry(
        # hydrophobic EXCLUDED from the pedagogical set (OH dominates
        # pedagogy; gate §3.3 Tyr row / §3.4).
        ('CG', 'CD1', 'CD2', 'CE1', 'CE2', 'CZ', 'OH', 'HH'),
        donors=('OH',), acceptors=('OH',),
        rings=(('CG', 'CD1', 'CE1', 'CZ', 'CE2', 'CD2'),)),
    'VAL': _entry(('CG1', 'CG2'), hydrophobic=True),
}


def _residues_where(predicate):
    """Residue names matching `predicate(entry)`, canonical sorted order."""
    return tuple(resn for resn in sorted(AA_RESIDUES)
                 if predicate(AA_RESIDUES[resn]))


def hbond_donor_residues():
    """Side chains listed as donors. source: gate §3.5 donors row (10)."""
    return _residues_where(lambda e: bool(e['donors']))


def hbond_acceptor_residues():
    """Side chains with acceptor atoms (O/N/S). source: gate §3.5
    acceptors row (9; Met thioether EXCLUDED in v1)."""
    return _residues_where(lambda e: bool(e['acceptors']))


def salt_cation_residues():
    """Cationic side chains (LYS/ARG; NOT His -- OQ-3/D2).
    source: gate §3.5 salt_bridge row."""
    return _residues_where(lambda e: e['charge'][0] == '+')


def salt_anion_residues():
    """Anionic side chains (ASP/GLU). source: gate §3.5 salt_bridge."""
    return _residues_where(lambda e: e['charge'][0] == '-')


def pi_ring_residues():
    """Aromatic-ring side chains. source: gate §3.5 pi_stacking row."""
    return _residues_where(lambda e: bool(e['rings']))


def cation_pi_cation_residues():
    """Cation role of cation-pi. source: gate §3.5 cation_pi row."""
    return salt_cation_residues()


def cation_pi_ring_residues():
    """Ring role of cation-pi (either direction counts, D4).
    source: gate §3.5 cation_pi row."""
    return pi_ring_residues()


def hydrophobic_residues():
    """Pedagogical hydrophobic set, residue-name-based on the AA side.
    source: gate §3.4 ([HUMAN] approved; Kyte & Doolittle 1982 cited)."""
    return _residues_where(lambda e: e['hydrophobic'])


def halogen_acceptor_residues():
    """AA-side halogen-bond acceptor role = the h_bond-acceptor set
    (O/N/S side chains; donors are ligand-side only, row 6).
    source: gate §3.5 halogen row (9). NOTE: the §3.3 Met-row cell
    marks Y(S); the resolved §3.5 set and this plan's transcription
    rule both exclude Met -- tension recorded, not silently dropped."""
    return hbond_acceptor_residues()


def metal_chelator_residues():
    """AA-side metal-chelator role (chelating atoms = the O/N/S
    acceptor atoms). source: gate §3.5 metal row (9; Asp/Gln INCLUDED
    per the approved resolutions, Met thioether EXCLUDED)."""
    return hbond_acceptor_residues()


def aa_capable(resn, itype, ligand_profile):
    """True iff residue `resn` could form interaction `itype` with a
    ligand whose chemistry profile is `ligand_profile`.

    This is the polarity-aware capability API (gate D3): salt-bridge
    capability depends on the LIGAND's charge sign, and cation-pi
    counts either direction (gate D4). Simple types gate on the table
    set AND the ligand-side support predicate (generation research
    §2.4). Unknown residues/types and missing profile keys fail closed
    (False).

    h_bond is direction-refined like D3 (Recorded addition, plan
    deviation Rule 2): an AA DONOR needs a ligand ACCEPTOR and an AA
    ACCEPTOR needs a ligand DONOR -- the coarse "has either" rule could
    mark a donor-only AA capable against a donor-only ligand, a level
    the detector can never solve (GEN-04 must not starve).
    """
    entry = AA_RESIDUES.get(resn)
    if entry is None or itype not in INTERACTION_TYPES:
        return False
    prof = ligand_profile or {}
    signs = prof.get('charge_signs') or ()
    rings = prof.get('ring_count') or 0

    if itype == 'salt_bridge':
        sign = entry['charge'][0]
        if sign == '+':
            return '-' in signs     # AA cation vs ligand anion
        if sign == '-':
            return '+' in signs     # AA anion vs ligand cation
        return False                # neutral His under OQ-3/D2

    if itype == 'cation_pi':
        if entry['charge'][0] == '+' and rings >= 1:
            return True             # AA cation over a ligand ring
        if entry['rings'] and '+' in signs:
            return True             # AA ring under a ligand cation
        return False

    if itype == 'h_bond':
        aa_donates = bool(entry['donors']) and bool(prof.get('has_acceptor'))
        aa_accepts = bool(entry['acceptors']) and bool(prof.get('has_donor'))
        return aa_donates or aa_accepts

    if itype == 'pi_stacking':
        return bool(entry['rings']) and ligand_support('pi_stacking', prof)

    if itype == 'hydrophobic':
        return entry['hydrophobic'] and ligand_support('hydrophobic', prof)

    if itype == 'halogen':
        # AA side is the acceptor role only; donors are ligand-side
        # (row 6) and gated on the ligand's C-X (Cl/Br/I) profile.
        return bool(entry['acceptors']) and ligand_support('halogen', prof)

    if itype == 'metal':
        # Chelator atoms are the O/N/S acceptor atoms; runs only when
        # the ligand carries an approved-list metal (gate §5 item 5).
        return bool(entry['acceptors']) and ligand_support('metal', prof)

    return False


def residue_capabilities(resn, ligand_profile):
    """Set of interaction types `resn` could form with a ligand of the
    given profile (generation research §5.3: the generator, the Hint
    and the detector's typing all consume this ONE function)."""
    if resn not in AA_RESIDUES:
        return set()
    return set(t for t in INTERACTION_TYPES
               if aa_capable(resn, t, ligand_profile))


# Generator aa-tokens -> materialization vocabulary. ONE mapping for the
# whole pipeline: the generator emits the token, the materializer calls
# cmd.fragment(entry['fragment']) and the level spec carries
# entry['resn']. Fragment names verified against the chempy fragment
# library probe (materialization research §1.4: all 20 standard AAs
# present; 'his' fragment carries resn HIS).
#
# Charge classes follow D2 (capped AAs, standard ionization): Asp-,
# Glu-, Lys+, Arg+; His NEUTRAL (HIE-like; NOT 'cation' under OQ-3).
#
# Protonation-variant tokens (hip, asph, gluh, lysn, argn, hid, hie)
# are RESERVED-ADDITIVE-LATER (schema extension slot.protonation /
# extra AA_TOKENS entries) -- NOT in v1.
AA_TOKENS = {
    'ala': {'fragment': 'ala', 'resn': 'ALA', 'charge_class': 'neutral'},
    'arg': {'fragment': 'arg', 'resn': 'ARG', 'charge_class': 'cation'},
    'asn': {'fragment': 'asn', 'resn': 'ASN', 'charge_class': 'neutral'},
    'asp': {'fragment': 'asp', 'resn': 'ASP', 'charge_class': 'anion'},
    'cys': {'fragment': 'cys', 'resn': 'CYS', 'charge_class': 'neutral'},
    'gln': {'fragment': 'gln', 'resn': 'GLN', 'charge_class': 'neutral'},
    'glu': {'fragment': 'glu', 'resn': 'GLU', 'charge_class': 'anion'},
    'gly': {'fragment': 'gly', 'resn': 'GLY', 'charge_class': 'neutral'},
    'his': {'fragment': 'his', 'resn': 'HIS', 'charge_class': 'neutral'},
    'ile': {'fragment': 'ile', 'resn': 'ILE', 'charge_class': 'neutral'},
    'leu': {'fragment': 'leu', 'resn': 'LEU', 'charge_class': 'neutral'},
    'lys': {'fragment': 'lys', 'resn': 'LYS', 'charge_class': 'cation'},
    'met': {'fragment': 'met', 'resn': 'MET', 'charge_class': 'neutral'},
    'phe': {'fragment': 'phe', 'resn': 'PHE', 'charge_class': 'neutral'},
    'pro': {'fragment': 'pro', 'resn': 'PRO', 'charge_class': 'neutral'},
    'ser': {'fragment': 'ser', 'resn': 'SER', 'charge_class': 'neutral'},
    'thr': {'fragment': 'thr', 'resn': 'THR', 'charge_class': 'neutral'},
    'trp': {'fragment': 'trp', 'resn': 'TRP', 'charge_class': 'neutral'},
    'tyr': {'fragment': 'tyr', 'resn': 'TYR', 'charge_class': 'neutral'},
    'val': {'fragment': 'val', 'resn': 'VAL', 'charge_class': 'neutral'},
}


# ---------------------------------------------------------------------------
# Ligand-side typing (plan 02-05 Task 2). Input: plain atom records
# (detection research §5.1: side/object/id/name/elem/resn/resi/alt/x/y/z,
# optional 'formal_charge' — SDF M CHG round-trips into it, materialization
# research §1.1) + the bond block [(i, j, order)] with 0-based atom
# indices. Geometry stays OUT except the row-8 planarity fallback — no
# thresholds live here (typing only, detection research §5.1).
# ---------------------------------------------------------------------------

# source: gate §3.5 metal list (row 7, OQ-7 approved 2026-09-06).
METAL_ELEMENTS = frozenset(('MG', 'ZN', 'FE', 'CA', 'MN', 'CU', 'NI',
                            'CO', 'CD'))
# source: gate row 6 — halogen-bond donors are ligand-side C-X with
# X in {Cl, Br, I}; C-F EXCLUDED (recorded ProLIF-precedent resolution).
_HALOGEN_DONOR_ELEMS = frozenset(('CL', 'BR', 'I'))
# source: gate §5 item 3 / row 6 — donor/acceptor elements are O/N/S.
_POLAR_ELEMS = frozenset(('O', 'N', 'S'))
# source: gate row 5 — qualifying carbon: element C whose bonded
# neighbors are all C or H (ligand side only; the AA side is
# residue-name-based per §3.4).
_HYDROPHOBE_NEIGHBOR_ELEMS = frozenset(('C', 'H'))
# source: gate row 8 fallback — 5/6-member ring with adjacent-dihedral
# deviation <= 15 deg (BINANA [V]); consumed in RADIANS via conversion
# below (02-02: vec3 angle math is radians — converted explicitly).
RING_PLANARITY_FALLBACK_DEG = 15.0
# MDL/SDF aromatic bond-order marker ("all aromatic-order markers").
_AROMATIC_MARKER = 4


def _elem(atom):
    """Normalized element symbol (uppercase, stripped)."""
    return str(atom.get('elem', '')).strip().upper()


def _formal_charge(atom):
    """Optional formal_charge as int, or None when absent/invalid."""
    value = atom.get('formal_charge')
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bond_order_int(order):
    """Coerce a bond order to 1/2/3/4; None when absent/unrecognizable.

    Aromatic markers (SDF order 4; MOL2 'ar'/'aromatic' spellings)
    coerce to 4. Unknown values fail closed (never guessed).
    """
    if order is None:
        return None
    try:
        value = int(order)
    except (TypeError, ValueError):
        text = str(order).strip().lower()
        if text in ('ar', 'aromatic', 'resonance'):
            return _AROMATIC_MARKER
        return None
    return value if value in (1, 2, 3, 4) else None


def _adjacency(atoms, bonds):
    """idx -> sorted neighbor-index lists from the bond block."""
    adjacency = {}
    for bond in bonds:
        i, j = int(bond[0]), int(bond[1])
        if i == j:
            continue                       # defensive: self-loop
        adjacency.setdefault(i, [])
        adjacency.setdefault(j, [])
        if j not in adjacency[i]:
            adjacency[i].append(j)
        if i not in adjacency[j]:
            adjacency[j].append(i)
    for key in adjacency:
        adjacency[key].sort()
    return adjacency


def _order_lookup(bonds):
    """{(min(i,j), max(i,j)): raw order} from the bond block."""
    lookup = {}
    for bond in bonds:
        i, j = int(bond[0]), int(bond[1])
        lookup[(min(i, j), max(i, j))] = bond[2] if len(bond) > 2 else None
    return lookup


def _canonical_ring(path):
    """Cyclic walk canonicalized (min atom first, lexicographically
    smaller of the two directions) so each cycle dedupes to one tuple."""
    start = min(path)
    idx = path.index(start)
    rotated = tuple(path[idx:] + path[:idx])
    backwards = (rotated[0],) + tuple(reversed(rotated[1:]))
    return rotated if rotated <= backwards else backwards


def _find_rings(adjacency):
    """All simple 5/6-member cycles as canonical atom-index tuples.

    Explicit-stack DFS over the bond-block adjacency — NO itertools
    (recorded 02-01 convention: explicit stack + nested loops only).
    Each cycle is walked from its MINIMUM atom (neighbors with index
    > start), so the two traversal directions are the only duplicates
    and the canonical form dedupes them. Paths are capped at 6 atoms;
    a cycle closes when the walk re-reaches `start` at length 5 or 6.
    """
    found = {}
    for start in sorted(adjacency):
        stack = [(start, (start,))]
        while stack:
            node, path = stack.pop()
            for nxt in adjacency.get(node, ()):
                if nxt == start:
                    if len(path) in (5, 6):
                        ring = _canonical_ring(path)
                        found[ring] = ring
                elif nxt > start and nxt not in path and len(path) < 6:
                    stack.append((nxt, path + (nxt,)))
    return sorted(found)


def _no_adjacent(positions, n):
    """True iff no two ring-bond positions are consecutive mod n."""
    ordered = sorted(positions)
    for k in range(len(ordered)):
        if (ordered[k] + 1) % n == ordered[(k + 1) % len(ordered)]:
            return False
    return True


def _ring_aromatic(ring, order_lookup, atoms):
    """Row-8 aromaticity for one 5/6-member cycle.

    Primary: bond-order-derived — all orders aromatic markers, OR the
    Kekule alternation pattern (6-ring: 3 non-adjacent doubles =
    perfect alternation; 5-ring: 2 non-adjacent doubles = the
    pyrrole/imidazole/furan pattern; unmarked bonds count as single
    per MDL semantics; any triple/unknown order fails the ring).
    Fallback: ONLY when every bond order in the cycle is absent —
    adjacent-dihedral deviation <= RING_PLANARITY_FALLBACK_DEG.
    """
    n = len(ring)
    orders = []
    for k in range(n):
        i, j = ring[k], ring[(k + 1) % n]
        orders.append(order_lookup.get((min(i, j), max(i, j))))
    coerced = [_bond_order_int(o) for o in orders]

    if all(o is None for o in coerced):
        return _ring_planar(ring, atoms)          # fallback ONLY here

    known = [1 if o is None else o for o in coerced]
    if all(o == _AROMATIC_MARKER for o in known):
        return True
    if any(o not in (1, 2) for o in known):
        return False                              # e.g. a triple bond
    doubles = [k for k, o in enumerate(known) if o == 2]
    return len(doubles) == n // 2 and _no_adjacent(doubles, n)


def _dihedral_deviation_deg(p0, p1, p2, p3):
    """Deviation of the p0-p1-p2-p3 dihedral from planarity (the nearest
    of 0/180 deg), in [0, 90]; None when the central bond is degenerate.

    Built on vec3 primitives (floats in/out); atan2 yields RADIANS and
    is converted here — the 02-02 vec3 contract is radians-only.
    """
    b0 = sub(p0, p1)
    b1 = sub(p2, p1)
    b2 = sub(p3, p2)
    length = norm(b1)
    if length == 0.0:
        return None
    axis = scale(b1, 1.0 / length)
    v = sub(b0, scale(axis, dot(b0, axis)))
    w = sub(b2, scale(axis, dot(b2, axis)))
    x = dot(v, w)
    y = dot(cross(axis, v), w)
    angle = abs(math.degrees(math.atan2(y, x)))   # radians -> degrees
    if angle > 180.0:                             # atan2 range guard
        angle = 360.0 - angle
    return min(angle, 180.0 - angle)


def _ring_planar(ring, atoms):
    """Row-8 fallback: every adjacent-dihedral deviation <= 15 deg.
    A degenerate window fails closed (not planar)."""
    n = len(ring)
    coords = [(float(atoms[i]['x']), float(atoms[i]['y']),
               float(atoms[i]['z'])) for i in ring]
    for k in range(n):
        deviation = _dihedral_deviation_deg(
            coords[k], coords[(k + 1) % n], coords[(k + 2) % n],
            coords[(k + 3) % n])
        if deviation is None or deviation > RING_PLANARITY_FALLBACK_DEG:
            return False
    return True


def _has_h_neighbor(idx, elements, adjacency):
    """True iff atom `idx` has a bonded H (fail-closed donor test)."""
    return any(elements[j] == 'H' for j in adjacency.get(idx, ()))


def _all_single_bonds(idx, neighbors, order_lookup):
    """True iff every bond from `idx` to `neighbors` has order 1."""
    for j in neighbors:
        order = _bond_order_int(
            order_lookup.get((min(idx, j), max(idx, j))))
        if order != 1:
            return False
    return True


def _charge_signs(elements, adjacency, order_lookup, atoms):
    """Ligand charge-group typing (gate §2.3 ligand side + the recorded
    formal_charge decision). Returns a set of '+'/'-'.

    '-' carboxylate: C bonded to exactly 2 O with NO O bearing an H.
      When formal_charge is present on the Os it governs (any O < 0);
      when absent, the kekule C=O/O-C structure alone types '-' (the
      recorded plan decision — esters written without charge flags are
      the accepted false-positive of that decision, recorded here).
      Recorded Rule-2 guard: a carboxyl OH (neutral acid) is never an
      anion — fail-closed, consistent with donor typing.
    '+' ammonium: N with formal_charge > 0, OR N with 4 single bonds
      including >= 1 H.
    '+' guanidino: C bonded to 3 N.
    """
    signs = set()
    for idx, elem in enumerate(elements):
        neighbors = adjacency.get(idx, ())
        if elem == 'C':
            o_neighbors = [j for j in neighbors if elements[j] == 'O']
            if len(o_neighbors) == 2 \
                    and not any(_has_h_neighbor(j, elements, adjacency)
                                for j in o_neighbors):
                charges = [_formal_charge(atoms[j]) for j in o_neighbors]
                known = [c for c in charges if c is not None]
                if known:
                    if any(c < 0 for c in known):
                        signs.add('-')     # formal charge governs
                else:
                    signs.add('-')         # structure alone (recorded)
            n_neighbors = [j for j in neighbors if elements[j] == 'N']
            if len(n_neighbors) == 3:
                signs.add('+')             # guanidino
        elif elem == 'N':
            fc = _formal_charge(atoms[idx])
            if fc is not None and fc > 0:
                signs.add('+')             # formal charge governs
            if len(neighbors) == 4 \
                    and _all_single_bonds(idx, neighbors, order_lookup) \
                    and _has_h_neighbor(idx, elements, adjacency):
                signs.add('+')             # ammonium structure
    return signs


def ligand_profile(atoms, bonds):
    """Ligand chemistry profile from atom records + bond block.

    Returns a plain dict (generation research §2.4 support predicates
    consume it; the generator may carry it via the manifest):
    {'has_donor', 'has_acceptor', 'charge_signs' (set of '+'/'-'),
     'ring_count', 'aromatic_rings' (list of atom-index lists),
     'has_hydrophobe', 'has_halogen_donor', 'has_metal',
     'metal_elements' (sorted)}.

    Typing rules (each unit-tested): aromatic rings from bond orders
    (5/6-member cycles, alternating 1/2 or all aromatic markers; the
    15-deg dihedral fallback fires ONLY when bond orders are absent
    for the cycle); donors FAIL-CLOSED (O/N/S needs a bonded H);
    acceptors = any O/N/S (an -OH oxygen is both donor and
    acceptor-eligible — the geometric test decides later); charge
    groups per ``_charge_signs``; hydrophobe = row-5 qualifying
    carbon; halogen donor = C-X with X in {Cl, Br, I} (C-F excluded);
    metal = row-7 approved element list. ring_count counts AROMATIC
    rings (pi_stacking/cation_pi support is about aromatic rings,
    row 8). Unknown elements/values fail closed.
    """
    adjacency = _adjacency(atoms, bonds)
    order_lookup = _order_lookup(bonds)
    elements = [_elem(a) for a in atoms]

    has_donor = False
    has_acceptor = False
    has_hydrophobe = False
    has_halogen_donor = False
    metals = set()
    for idx, elem in enumerate(elements):
        neighbor_elems = set(elements[j] for j in adjacency.get(idx, ()))
        if elem in _POLAR_ELEMS:
            has_acceptor = True
            if 'H' in neighbor_elems:
                has_donor = True           # fail-closed: needs attached H
        if elem == 'C' and neighbor_elems <= _HYDROPHOBE_NEIGHBOR_ELEMS:
            has_hydrophobe = True          # vacuous OK for a lone C
        if elem in _HALOGEN_DONOR_ELEMS and 'C' in neighbor_elems:
            has_halogen_donor = True       # C-F excluded by the elem set
        if elem in METAL_ELEMENTS:
            metals.add(elem)

    aromatic = []
    for ring in _find_rings(adjacency):
        if _ring_aromatic(ring, order_lookup, atoms):
            aromatic.append(list(ring))

    return {
        'has_donor': has_donor,
        'has_acceptor': has_acceptor,
        'charge_signs': _charge_signs(elements, adjacency, order_lookup,
                                      atoms),
        'ring_count': len(aromatic),
        'aromatic_rings': aromatic,
        'has_hydrophobe': has_hydrophobe,
        'has_halogen_donor': has_halogen_donor,
        'has_metal': bool(metals),
        'metal_elements': sorted(metals),
    }


def ligand_support(itype, ligand_profile):
    """Ligand-side support predicate per generation research §2.4 —
    the generator's required-set feasibility half (the AA half is
    ``aa_capable``; the SAME tables feed both, DETECT-04 by
    construction). Unknown types and missing keys fail closed."""
    prof = ligand_profile or {}
    signs = prof.get('charge_signs') or ()
    rings = prof.get('ring_count') or 0
    if itype == 'h_bond':
        return bool(prof.get('has_donor')) or bool(prof.get('has_acceptor'))
    if itype == 'salt_bridge':
        return bool(signs)
    if itype == 'pi_stacking':
        return rings >= 1
    if itype == 'cation_pi':
        return rings >= 1 or '+' in signs
    if itype == 'hydrophobic':
        return bool(prof.get('has_hydrophobe'))
    if itype == 'halogen':
        return bool(prof.get('has_halogen_donor'))
    if itype == 'metal':
        return bool(prof.get('has_metal'))
    return False


def ligand_has_metal(atoms):
    """True iff any ligand-side atom's element is in the approved metal
    list — the shared gating helper so the generator's required-type
    selection mirrors the detector's metal gate (gate §5 item 5;
    detection research §7.6)."""
    for atom in atoms:
        if _elem(atom) in METAL_ELEMENTS:
            return True
    return False
