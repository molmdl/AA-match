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

from .vec3 import sub, dot, cross, norm
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
        return bool(entry['rings']) and rings >= 1

    if itype == 'hydrophobic':
        return entry['hydrophobic'] and bool(prof.get('has_hydrophobe'))

    if itype == 'halogen':
        # AA side is the acceptor role only; donors are ligand-side
        # (row 6) and gated on the ligand's C-X (Cl/Br/I) profile.
        return bool(entry['acceptors']) \
            and bool(prof.get('has_halogen_donor'))

    if itype == 'metal':
        # Chelator atoms are the O/N/S acceptor atoms; runs only when
        # the ligand carries an approved-list metal (gate §5 item 5).
        return bool(entry['acceptors']) and bool(prof.get('has_metal'))

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
