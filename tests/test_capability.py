"""Unit tests for aamatch.capability — the single typing home (plan 02-05).

Every table assertion here is transcribed from the APPROVED DETECT-03 gate
document (docs/DETECTION_THRESHOLDS.md, approved 2026-09-06, human gate at
the 02-01 checkpoint): the AA capability table §3.3, the resolved sets
§3.5, the per-type counts, and the polarity decisions D3/D4. The module
is the ONLY atom/residue typing home (gate §4.2) shared by the generator
(GEN-04 solvability), the detector (DETECT-04 typing agreement), and the
Hint (PLAY-05) — these tests pin "agrees by construction".

Task 1 scope: AA residue table + capability matrix + AA_TOKENS + polarity.
Task 2 scope (appended below): ligand-side typing + support predicates.

Runs under bare python3.6, stdlib only, zero stubs. capability must
import only `math`, `.vec3` and `.setup_state` (purity Gate A).
"""

import math
import unittest

from aamatch import capability
from aamatch.setup_state import INTERACTION_TYPES


def profile(has_donor=False, has_acceptor=False, charge_signs=(),
            ring_count=0, has_hydrophobe=False, has_halogen_donor=False,
            has_metal=False):
    """Hand-built ligand profile for polarity tests (Task 1, D3/D4).

    Shape mirrors what capability.ligand_profile() produces in Task 2.
    """
    return {
        'has_donor': has_donor,
        'has_acceptor': has_acceptor,
        'charge_signs': set(charge_signs),
        'ring_count': ring_count,
        'has_hydrophobe': has_hydrophobe,
        'has_halogen_donor': has_halogen_donor,
        'has_metal': has_metal,
    }


# A ligand carrying every feature — used by the "never starves" scan so
# each type's capable-AA count is the table's full row membership.
RICH = profile(has_donor=True, has_acceptor=True,
               charge_signs=('+', '-'), ring_count=1,
               has_hydrophobe=True, has_halogen_donor=True,
               has_metal=True)

APOLAR = profile(has_hydrophobe=True)


class TestAATableTruthfulness(unittest.TestCase):
    """The permanent invariant: the approved table, row for row (gate §3).

    These sets are transcribed from docs/DETECTION_THRESHOLDS.md §3.3/§3.5
    (approved 2026-09-06). Any change here is a DETECTOR_VERSION bump
    event (gate §4.7) — never a silent edit.
    """

    def test_hbond_donor_set_exact(self):
        # source: gate §3.5 "h_bond donors (side chain)" (10)
        self.assertEqual(
            set(capability.hbond_donor_residues()),
            {'ARG', 'ASN', 'CYS', 'GLN', 'HIS', 'LYS', 'SER', 'THR',
             'TRP', 'TYR'})

    def test_hbond_acceptor_set_exact(self):
        # source: gate §3.5 "h_bond acceptors" (9) — Met thioether-S
        # EXCLUDED in v1 (recorded DETECT-03 disagreement, §3.3 Met row).
        self.assertEqual(
            set(capability.hbond_acceptor_residues()),
            {'ASN', 'ASP', 'CYS', 'GLN', 'GLU', 'HIS', 'SER', 'THR',
             'TYR'})

    def test_salt_bridge_cations_and_anions_exact(self):
        # source: gate §3.5 salt_bridge row — cationic LYS/ARG, anionic
        # ASP/GLU; HIS is NOT a cation under the neutral-His policy
        # (OQ-3 / D2).
        self.assertEqual(set(capability.salt_cation_residues()),
                         {'LYS', 'ARG'})
        self.assertEqual(set(capability.salt_anion_residues()),
                         {'ASP', 'GLU'})

    def test_pi_stacking_set_exact(self):
        # source: gate §3.5 pi_stacking row (4; Trp = two rings)
        self.assertEqual(set(capability.pi_ring_residues()),
                         {'PHE', 'TYR', 'HIS', 'TRP'})

    def test_cation_pi_roles(self):
        # source: gate §3.5 cation_pi row — cation role LYS/ARG; ring
        # role PHE/TYR/HIS/TRP; either direction counts (D4).
        self.assertEqual(set(capability.cation_pi_cation_residues()),
                         {'LYS', 'ARG'})
        self.assertEqual(set(capability.cation_pi_ring_residues()),
                         {'PHE', 'TYR', 'HIS', 'TRP'})

    def test_hydrophobic_set_exact(self):
        # source: gate §3.4 pedagogical set (approved [HUMAN]); Gly has
        # no side chain; Cys/Tyr excluded per the §3.3 row resolutions.
        self.assertEqual(set(capability.hydrophobic_residues()),
                         {'ALA', 'VAL', 'LEU', 'ILE', 'PRO', 'PHE',
                          'MET', 'TRP'})

    def test_halogen_acceptor_set_equals_hbond_acceptor_set(self):
        # source: gate §3.5 "halogen acceptor (AA-side O/N/S)" (9) — the
        # plan's transcription rule: the halogen-acceptor role IS the
        # h_bond-acceptor set. (The §3.3 Met-row cell Y(S) is superseded
        # by the resolved §3.5 set — Met excluded; recorded.)
        self.assertEqual(set(capability.halogen_acceptor_residues()),
                         set(capability.hbond_acceptor_residues()))

    def test_metal_chelator_set_exact(self):
        # source: gate §3.5 "metal chelator (AA-side N/O/S)" (9) —
        # Asp/Gln/Glu/His/Cys(S) INCLUDED per the approved resolutions;
        # Met thioether EXCLUDED.
        self.assertEqual(set(capability.metal_chelator_residues()),
                         {'ASN', 'ASP', 'CYS', 'GLN', 'GLU', 'HIS',
                          'SER', 'THR', 'TYR'})

    def test_recorded_exclusions_hold(self):
        # The recorded v1 resolutions, pinned so they cannot regress:
        acceptors = set(capability.hbond_acceptor_residues())
        self.assertNotIn('MET', acceptors)      # weak thioether, v1 EXCLUDE
        self.assertNotIn('MET', set(capability.metal_chelator_residues()))
        self.assertNotIn('MET', set(capability.halogen_acceptor_residues()))
        self.assertNotIn('HIS', set(capability.salt_cation_residues()))
        self.assertNotIn('CYS', set(capability.hydrophobic_residues()))
        self.assertNotIn('TYR', set(capability.hydrophobic_residues()))
        self.assertNotIn('GLY', set(capability.hydrophobic_residues()))

    def test_all_20_standard_residues_present(self):
        self.assertEqual(len(capability.AA_RESIDUES), 20)
        standard = set('ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS '
                       'MET PHE PRO SER THR TRP TYR VAL'.split())
        self.assertEqual(set(capability.AA_RESIDUES), standard)

    def test_gly_side_chain_empty(self):
        # Gly has no side chain (gate §3.3 Gly row).
        self.assertEqual(len(capability.AA_RESIDUES['GLY']['side_chain']),
                         0)

    def test_his_neutral_hie_like(self):
        # source: gate §3.3 His row + OQ-3/D2 — neutral (HIE-like):
        # donor NE2 (N-H), acceptor ND1, NO charge (not a salt-bridge
        # cation in v1), one 5-ring.
        entry = capability.AA_RESIDUES['HIS']
        self.assertIsNone(entry['charge'][0])
        self.assertEqual(entry['donors'], ['NE2'])
        self.assertEqual(entry['acceptors'], ['ND1'])
        # Ring list is a valid CYCLIC WALK (row-9 geometry consumes it):
        # imidazole connectivity CG-ND1-CE1-NE2-CD2-CG.
        self.assertEqual(entry['rings'],
                         [['CG', 'ND1', 'CE1', 'NE2', 'CD2']])

    def test_trp_two_rings_binana_assignment(self):
        # source: gate §2.2 row 8 — Trp = two rings (BINANA assignment).
        rings = capability.AA_RESIDUES['TRP']['rings']
        self.assertEqual(len(rings), 2)
        lengths = sorted(len(r) for r in rings)
        self.assertEqual(lengths, [5, 6])

    def test_phe_tyr_one_six_ring(self):
        for resn in ('PHE', 'TYR'):
            rings = capability.AA_RESIDUES[resn]['rings']
            self.assertEqual(len(rings), 1, resn)
            self.assertEqual(len(rings[0]), 6, resn)

    def test_typed_atom_names_inside_side_chain(self):
        # D1 boundary integrity: every typed atom (donor, acceptor,
        # charge representative, ring atom) must be inside the
        # side_chain frozenset, so a side-chain membership test implies
        # every typed role.
        for resn, entry in capability.AA_RESIDUES.items():
            side = entry['side_chain']
            for name in entry['donors']:
                self.assertIn(name, side, (resn, name))
            for name in entry['acceptors']:
                self.assertIn(name, side, (resn, name))
            for name in entry['charge'][1]:
                self.assertIn(name, side, (resn, name))
            for ring in entry['rings']:
                for name in ring:
                    self.assertIn(name, side, (resn, name))

    def test_side_chain_excludes_backbone_and_cap_atoms(self):
        # D1: backbone + cap atoms are NEVER typed as interacting. The
        # standard backbone names must not appear in any side_chain set.
        forbidden = {'N', 'CA', 'C', 'O', 'OXT', 'H', 'H1', 'H2', 'H3',
                     'HA'}
        for resn, entry in capability.AA_RESIDUES.items():
            overlap = entry['side_chain'] & forbidden
            self.assertEqual(overlap, set(), resn)


class TestAACapablePolarity(unittest.TestCase):
    """aa_capable() polarity/direction decisions (gate D3/D4)."""

    def test_salt_bridge_cation_side_polarity(self):
        # D3: ligand anionic -> AA must be cationic (LYS/ARG).
        anionic = profile(charge_signs=('-',))
        self.assertTrue(capability.aa_capable('LYS', 'salt_bridge',
                                              anionic))
        self.assertTrue(capability.aa_capable('ARG', 'salt_bridge',
                                              anionic))
        self.assertFalse(capability.aa_capable('ASP', 'salt_bridge',
                                               anionic))
        self.assertFalse(capability.aa_capable('GLU', 'salt_bridge',
                                               anionic))

    def test_salt_bridge_anion_side_polarity(self):
        # D3: ligand cationic -> AA must be anionic (ASP/GLU).
        cationic = profile(charge_signs=('+',))
        self.assertTrue(capability.aa_capable('ASP', 'salt_bridge',
                                              cationic))
        self.assertTrue(capability.aa_capable('GLU', 'salt_bridge',
                                              cationic))
        self.assertFalse(capability.aa_capable('LYS', 'salt_bridge',
                                               cationic))
        self.assertFalse(capability.aa_capable('ARG', 'salt_bridge',
                                               cationic))

    def test_salt_bridge_not_capable_for_apolar_ligand(self):
        self.assertFalse(capability.aa_capable('LYS', 'salt_bridge',
                                               APOLAR))
        self.assertFalse(capability.aa_capable('ASP', 'salt_bridge',
                                               APOLAR))

    def test_salt_bridge_his_never_a_cation(self):
        # Neutral-His policy (OQ-3/D2): HIS is not a salt-bridge partner
        # even against an anionic ligand.
        anionic = profile(charge_signs=('-',))
        self.assertFalse(capability.aa_capable('HIS', 'salt_bridge',
                                               anionic))

    def test_cation_pi_aa_cation_direction(self):
        # D4 direction 1: AA cation (LYS/ARG) over a LIGAND ring.
        ringed = profile(ring_count=1)
        self.assertTrue(capability.aa_capable('LYS', 'cation_pi', ringed))
        self.assertTrue(capability.aa_capable('ARG', 'cation_pi', ringed))
        self.assertFalse(capability.aa_capable('PHE', 'cation_pi', ringed))

    def test_cation_pi_aa_ring_direction(self):
        # D4 direction 2: AA ring (PHE/TYR/HIS/TRP) under a LIGAND
        # cation.
        cationic = profile(charge_signs=('+',))
        self.assertTrue(capability.aa_capable('PHE', 'cation_pi', cationic))
        self.assertTrue(capability.aa_capable('TYR', 'cation_pi', cationic))
        self.assertTrue(capability.aa_capable('HIS', 'cation_pi', cationic))
        self.assertTrue(capability.aa_capable('TRP', 'cation_pi', cationic))
        self.assertFalse(capability.aa_capable('LYS', 'cation_pi', cationic))

    def test_cation_pi_either_direction_counts(self):
        # D4: a ligand with BOTH a ring and a cation enables both roles.
        both = profile(ring_count=1, charge_signs=('+',))
        self.assertTrue(capability.aa_capable('LYS', 'cation_pi', both))
        self.assertTrue(capability.aa_capable('PHE', 'cation_pi', both))

    def test_pi_stacking_gated_on_ligand_ring(self):
        self.assertTrue(capability.aa_capable('PHE', 'pi_stacking',
                                              profile(ring_count=1)))
        self.assertFalse(capability.aa_capable('PHE', 'pi_stacking',
                                               APOLAR))

    def test_hbond_polarity(self):
        # AA donor needs a ligand acceptor; AA acceptor needs a ligand
        # donor; nothing without either.
        donor_lig = profile(has_donor=True)
        acceptor_lig = profile(has_acceptor=True)
        self.assertTrue(capability.aa_capable('SER', 'h_bond', donor_lig))
        self.assertTrue(capability.aa_capable('ASP', 'h_bond', donor_lig))
        self.assertTrue(capability.aa_capable('SER', 'h_bond',
                                              acceptor_lig))
        self.assertTrue(capability.aa_capable('LYS', 'h_bond',
                                              acceptor_lig))
        self.assertFalse(capability.aa_capable('SER', 'h_bond', APOLAR))
        self.assertFalse(capability.aa_capable('PHE', 'h_bond',
                                               donor_lig))

    def test_metal_gated_on_ligand_metal(self):
        # gate §5 item 5: metal coordination only when the ligand
        # carries an approved-list metal.
        with_metal = profile(has_metal=True)
        self.assertTrue(capability.aa_capable('SER', 'metal', with_metal))
        self.assertTrue(capability.aa_capable('ASP', 'metal', with_metal))
        self.assertFalse(capability.aa_capable('SER', 'metal', APOLAR))
        self.assertFalse(capability.aa_capable('MET', 'metal', with_metal))

    def test_halogen_aa_side_is_acceptor_role_only(self):
        # Row 6: donors are LIGAND-side only; AA side contributes the
        # O/N/S acceptor role. Met is excluded per §3.5.
        hal = profile(has_halogen_donor=True)
        self.assertTrue(capability.aa_capable('TYR', 'halogen', hal))
        self.assertTrue(capability.aa_capable('CYS', 'halogen', hal))
        self.assertFalse(capability.aa_capable('MET', 'halogen', hal))
        self.assertFalse(capability.aa_capable('TYR', 'halogen', APOLAR))

    def test_hydrophobic_gated_on_ligand_hydrophobe(self):
        self.assertTrue(capability.aa_capable('ALA', 'hydrophobic',
                                              profile(has_hydrophobe=True)))
        self.assertFalse(capability.aa_capable('ALA', 'hydrophobic',
                                               profile()))

    def test_hbond_donor_only_aa_vs_donor_only_ligand_fails_closed(self):
        # h_bond is direction-refined like D3 (recorded Rule-2
        # addition): an AA DONOR needs a ligand ACCEPTOR. LYS/ARG
        # (donor-only side chains) against a donor-only ligand can
        # never form an H-bond — the detector would find none — so the
        # capability must say no (GEN-04 must not allocate a doomed
        # slot).
        donor_only = profile(has_donor=True)
        self.assertFalse(capability.aa_capable('LYS', 'h_bond',
                                               donor_only))
        self.assertFalse(capability.aa_capable('ARG', 'h_bond',
                                               donor_only))

    def test_unknown_residue_and_type_fail_closed(self):
        self.assertFalse(capability.aa_capable('XYZ', 'h_bond', RICH))
        self.assertFalse(capability.aa_capable('SER', 'nope', RICH))


class TestResidueCapabilities(unittest.TestCase):
    """residue_capabilities(): the type set per residue + the permanent
    '>= 2 capable AAs per type' solvability invariant (generation
    research §2.3 / gate §3.5 counts)."""

    def test_returns_subset_of_interaction_types(self):
        result = capability.residue_capabilities('SER', RICH)
        self.assertIsInstance(result, set)
        self.assertTrue(result.issubset(set(INTERACTION_TYPES)))

    def test_serine_rich_profile_exact_set(self):
        # SER: donor+acceptor OG -> h_bond, halogen, metal.
        self.assertEqual(capability.residue_capabilities('SER', RICH),
                         {'h_bond', 'halogen', 'metal'})

    def test_lysine_rich_profile_exact_set(self):
        # LYS: donor NZ, cation; cation-PI needs the ligand ring
        # (RICH has one).
        self.assertEqual(capability.residue_capabilities('LYS', RICH),
                         {'h_bond', 'salt_bridge', 'cation_pi'})

    def test_aspartate_rich_profile_exact_set(self):
        # ASP: acceptor carboxylate, anion -> h_bond (acceptor side vs
        # RICH donor), salt_bridge (vs RICH '+'), halogen, metal.
        self.assertEqual(capability.residue_capabilities('ASP', RICH),
                         {'h_bond', 'salt_bridge', 'halogen', 'metal'})

    def test_phenylalanine_rich_profile_exact_set(self):
        self.assertEqual(capability.residue_capabilities('PHE', RICH),
                         {'pi_stacking', 'cation_pi', 'hydrophobic'})

    def test_arginine_rich_profile_exact_set(self):
        self.assertEqual(capability.residue_capabilities('ARG', RICH),
                         {'h_bond', 'salt_bridge', 'cation_pi'})

    def test_empty_profile_empty_capabilities_for_polar(self):
        self.assertEqual(capability.residue_capabilities('SER',
                                                         profile()),
                         set())
        self.assertEqual(capability.residue_capabilities('ARG',
                                                         profile()),
                         set())

    def test_every_type_has_at_least_two_capable_aas(self):
        # Permanent invariant (generation research §2.3): with a rich
        # ligand, no interaction type ever starves the solver — the
        # generator can always sample a required type.
        for itype in INTERACTION_TYPES:
            n = sum(1 for resn in capability.AA_RESIDUES
                    if capability.aa_capable(resn, itype, RICH))
            self.assertGreaterEqual(
                n, 2,
                '%s has only %d capable AAs — solvability would starve'
                % (itype, n))

    def test_counts_match_approved_document(self):
        # source: gate §3.5 "Counts per type" — h_bond 12, salt_bridge
        # 4, pi_stacking 4, cation_pi 6, hydrophobic 8, halogen 9,
        # metal 9.
        expected = {'h_bond': 12, 'salt_bridge': 4, 'pi_stacking': 4,
                    'cation_pi': 6, 'hydrophobic': 8, 'halogen': 9,
                    'metal': 9}
        for itype, count in expected.items():
            n = sum(1 for resn in capability.AA_RESIDUES
                    if capability.aa_capable(resn, itype, RICH))
            self.assertEqual(n, count, itype)


class TestAATokens(unittest.TestCase):
    """AA_TOKENS: the ONE vocabulary mapping generator aa-tokens to
    fragment names + resn (plan 02-05; consumed by the materializer
    and the level-spec payload)."""

    def test_exactly_20_standard_tokens(self):
        self.assertEqual(len(capability.AA_TOKENS), 20)
        expected = set('ala arg asn asp cys gln glu gly his ile leu lys '
                       'met phe pro ser thr trp tyr val'.split())
        self.assertEqual(set(capability.AA_TOKENS), expected)

    def test_token_shape_fragment_and_resn(self):
        for token, entry in capability.AA_TOKENS.items():
            self.assertEqual(set(entry),
                             {'fragment', 'resn', 'charge_class'},
                             token)
            self.assertEqual(entry['fragment'], token, token)
            self.assertEqual(entry['resn'], token.upper(), token)

    def test_charge_classes(self):
        for token in ('asp', 'glu'):
            self.assertEqual(
                capability.AA_TOKENS[token]['charge_class'], 'anion',
                token)
        for token in ('lys', 'arg'):
            self.assertEqual(
                capability.AA_TOKENS[token]['charge_class'], 'cation',
                token)
        for token in ('ala', 'asn', 'cys', 'gln', 'gly', 'his', 'ile',
                      'leu', 'met', 'phe', 'pro', 'ser', 'thr', 'trp',
                      'tyr', 'val'):
            self.assertEqual(
                capability.AA_TOKENS[token]['charge_class'], 'neutral',
                token)

    def test_his_is_neutral_with_resn_HIS(self):
        entry = capability.AA_TOKENS['his']
        self.assertEqual(entry, {'fragment': 'his', 'resn': 'HIS',
                                 'charge_class': 'neutral'})

    def test_no_protonation_variants_in_v1(self):
        # Protonation-variant tokens (hip, asph, gluh, lysn, argn, hid,
        # hie) are reserved-additive-later, NOT in v1.
        for variant in ('hip', 'asph', 'gluh', 'lysn', 'argn', 'hid',
                        'hie'):
            self.assertNotIn(variant, capability.AA_TOKENS)


# ---------------------------------------------------------------------------
# Task 2: ligand-side typing + support predicates (detection research §5.1
# atom-record shape + bond block; typing rules per plan 02-05 Task 2).
# ---------------------------------------------------------------------------

PROFILE_KEYS = {'has_donor', 'has_acceptor', 'charge_signs', 'ring_count',
                'aromatic_rings', 'has_hydrophobe', 'has_halogen_donor',
                'has_metal', 'metal_elements'}


def _atom(idx, name, elem, x=0.0, y=0.0, z=0.0, fc=None):
    """Synthetic atom record, detection research §5.1 shape. The optional
    'formal_charge' key round-trips SDF M CHG (materialization research
    §1.1) and is carried by the plan 02-09 extraction."""
    record = {'side': 'lig', 'object': 'LIG', 'id': idx, 'name': name,
              'elem': elem, 'resn': 'LIG', 'resi': 1, 'alt': '',
              'x': float(x), 'y': float(y), 'z': float(z)}
    if fc is not None:
        record['formal_charge'] = fc
    return record


def _ring_atoms(prefix, n, radius=1.4, elem='C', puck=0.0, lift_idx=None,
                lift=0.8):
    """n ring atoms on a circle (z=0). `puck` alternates +/-z (chair);
    `lift_idx` pushes one atom out of plane (envelope)."""
    atoms = []
    for k in range(n):
        ang = 2.0 * math.pi * k / n
        z = 0.0
        if puck and k % 2 == 0:
            z = puck
        elif puck:
            z = -puck
        if lift_idx is not None and k == lift_idx:
            z = lift
        atoms.append(_atom(k, '%s%d' % (prefix, k), elem,
                           radius * math.cos(ang),
                           radius * math.sin(ang), z))
    return atoms


def _ring_bonds(n, orders=None, default_order=1):
    """Consecutive ring bonds (i, (i+1) % n, order); `orders` cycles."""
    bonds = []
    for k in range(n):
        order = default_order
        if orders:
            order = orders[k % len(orders)]
        bonds.append((k, (k + 1) % n, order))
    return bonds


def _hydrogens(atoms, start_idx, hosts, prefix='h'):
    """Append one H per host atom index; returns (atoms, bonds)."""
    bonds = []
    for offset, host in enumerate(hosts):
        idx = start_idx + offset
        atoms.append(_atom(idx, '%s%d' % (prefix, offset), 'H',
                           atoms[host]['x'], atoms[host]['y'],
                           atoms[host]['z']))
        bonds.append((host, idx, 1))
    return atoms, bonds


def _benzamide():
    """Ring + amide N-H donor + carbonyl O acceptor (plan fixture).

    idx 0-5 ring C, 6-11 ring H, 12 carbonyl C, 13 O, 14 amide N,
    15-16 amide H.
    """
    atoms = _ring_atoms('c', 6)
    atoms, hbonds = _hydrogens(atoms, 6, list(range(6)))
    atoms.append(_atom(12, 'cx', 'C', 1.4 + 1.5, 0.0, 0.0))
    atoms.append(_atom(13, 'o', 'O', 1.4 + 2.4, 0.9, 0.0))
    atoms.append(_atom(14, 'n', 'N', 1.4 + 2.4, -0.9, 0.0))
    atoms.append(_atom(15, 'hn1', 'H', 1.4 + 3.1, -1.5, 0.0))
    atoms.append(_atom(16, 'hn2', 'H', 1.4 + 3.1, -0.2, 0.3))
    bonds = _ring_bonds(6, orders=(2, 1, 2, 1, 2, 1))
    bonds.extend(hbonds)
    bonds.extend([(0, 12, 1), (12, 13, 2), (12, 14, 1), (14, 15, 1),
                  (14, 16, 1)])
    return atoms, bonds


def _acetate(formal_charges=True):
    """CH3-C(=O)-O(-): idx 0 methyl C, 1 carboxyl C, 2 O (double),
    3 O (single), 4-6 methyl H, 7 optional hydroxyl H (acid variant
    via `hydroxyl`)."""
    o1_fc = -1 if formal_charges else None
    atoms = [_atom(0, 'C1', 'C'), _atom(1, 'C2', 'C'),
             _atom(2, 'O1', 'O', fc=o1_fc), _atom(3, 'O2', 'O',
                                                  fc=0 if formal_charges
                                                  else None),
             _atom(4, 'H1', 'H'), _atom(5, 'H2', 'H'), _atom(6, 'H3', 'H')]
    bonds = [(0, 1, 1), (1, 2, 2), (1, 3, 1), (0, 4, 1), (0, 5, 1),
             (0, 6, 1)]
    return atoms, bonds


def _acetic_acid():
    """Acetate + an H on the single-bonded O (neutral COOH)."""
    atoms, bonds = _acetate(formal_charges=False)
    atoms.append(_atom(7, 'ho', 'H', atoms[3]['x'] + 0.9,
                       atoms[3]['y'] + 0.5, 0.0))
    bonds.append((3, 7, 1))
    return atoms, bonds


class TestLigandProfile(unittest.TestCase):
    """ligand_profile(atoms, bonds): the plain-dict chemistry summary."""

    def test_profile_shape(self):
        prof = capability.ligand_profile(*_benzamide())
        self.assertEqual(set(prof), PROFILE_KEYS)
        self.assertIsInstance(prof['charge_signs'], set)
        self.assertIsInstance(prof['aromatic_rings'], list)
        self.assertIsInstance(prof['metal_elements'], list)
        self.assertEqual(prof['ring_count'], len(prof['aromatic_rings']))

    def test_benzamide_donor_acceptor_ring(self):
        atoms, bonds = _benzamide()
        prof = capability.ligand_profile(atoms, bonds)
        self.assertTrue(prof['has_donor'])       # amide N-H
        self.assertTrue(prof['has_acceptor'])    # carbonyl O (+ amide N)
        self.assertEqual(prof['charge_signs'], set())
        self.assertEqual(prof['ring_count'], 1)
        self.assertEqual(len(prof['aromatic_rings'][0]), 6)
        self.assertEqual(sorted(prof['aromatic_rings'][0]),
                         [0, 1, 2, 3, 4, 5])
        self.assertTrue(prof['has_hydrophobe'])  # qualifying ring carbons
        self.assertFalse(prof['has_halogen_donor'])
        self.assertFalse(prof['has_metal'])
        self.assertEqual(prof['metal_elements'], [])

    def test_determinism_same_input_same_profile(self):
        atoms, bonds = _benzamide()
        self.assertEqual(capability.ligand_profile(atoms, bonds),
                         capability.ligand_profile(atoms, bonds))

    def test_empty_inputs(self):
        prof = capability.ligand_profile([], [])
        self.assertFalse(prof['has_donor'])
        self.assertFalse(prof['has_acceptor'])
        self.assertEqual(prof['charge_signs'], set())
        self.assertEqual(prof['ring_count'], 0)
        self.assertFalse(prof['has_hydrophobe'])
        self.assertFalse(prof['has_halogen_donor'])
        self.assertFalse(prof['has_metal'])
        self.assertEqual(prof['metal_elements'], [])


class TestChargeGroupTyping(unittest.TestCase):
    """Charge groups (gate §2.3 + the recorded formal_charge decision)."""

    def test_carboxylate_with_formal_charge(self):
        # acetate-like: C with two O, one formally -1 -> {'-'}
        atoms, bonds = _acetate(formal_charges=True)
        prof = capability.ligand_profile(atoms, bonds)
        self.assertEqual(prof['charge_signs'], {'-'})

    def test_carboxylate_structure_only_when_charges_absent(self):
        # recorded decision: with formal_charge ABSENT, the kekule
        # C=O/O-C carboxylate structure alone types '-'.
        atoms, bonds = _acetate(formal_charges=False)
        prof = capability.ligand_profile(atoms, bonds)
        self.assertEqual(prof['charge_signs'], {'-'})

    def test_formal_charge_zero_overrides_structure(self):
        # "when present use it": explicit 0 charges -> NOT an anion.
        atoms = [_atom(0, 'C1', 'C'), _atom(1, 'C2', 'C'),
                 _atom(2, 'O1', 'O', fc=0), _atom(3, 'O2', 'O', fc=0),
                 _atom(4, 'H1', 'H'), _atom(5, 'H2', 'H'),
                 _atom(6, 'H3', 'H')]
        bonds = [(0, 1, 1), (1, 2, 2), (1, 3, 1), (0, 4, 1), (0, 5, 1),
                 (0, 6, 1)]
        prof = capability.ligand_profile(atoms, bonds)
        self.assertEqual(prof['charge_signs'], set())

    def test_carboxylic_acid_oh_is_not_an_anion(self):
        # Recorded Rule-2 guard: a carboxyl OH (neutral acid) is never
        # a carboxylate anion — fail-closed like donor typing.
        atoms, bonds = _acetic_acid()
        prof = capability.ligand_profile(atoms, bonds)
        self.assertEqual(prof['charge_signs'], set())
        self.assertTrue(prof['has_donor'])

    def test_ammonium_four_single_bonds_with_h(self):
        # methylammonium: N with 4 single bonds incl >= 1 H -> '+'
        atoms = [_atom(0, 'C', 'C'), _atom(1, 'N', 'N'),
                 _atom(2, 'H1', 'H'), _atom(3, 'H2', 'H'),
                 _atom(4, 'H3', 'H'), _atom(5, 'H4', 'H'),
                 _atom(6, 'H5', 'H'), _atom(7, 'H6', 'H')]
        bonds = [(0, 1, 1), (0, 2, 1), (0, 3, 1), (0, 4, 1), (1, 5, 1),
                 (1, 6, 1), (1, 7, 1)]
        prof = capability.ligand_profile(atoms, bonds)
        self.assertEqual(prof['charge_signs'], {'+'})

    def test_ammonium_by_formal_charge(self):
        # N with formal_charge > 0 -> '+' even at ring connectivity of
        # 2 ring bonds + 1 substituent (pyridinium-like; the fc branch
        # of the ammonium rule).
        atoms = [_atom(k, 'c%d' % k, 'C',
                       1.4 * math.cos(2 * math.pi * k / 6),
                       1.4 * math.sin(2 * math.pi * k / 6), 0.0)
                 for k in range(6)]
        atoms[0] = _atom(0, 'n0', 'N', 1.4, 0.0, 0.0, fc=1)
        atoms.append(_atom(6, 'csub', 'C', 3.9, 0.0, 0.0))
        bonds = [(k, (k + 1) % 6, (2, 1, 2, 1, 2, 1)[k]) for k in range(6)]
        bonds.append((0, 6, 1))
        prof = capability.ligand_profile(atoms, bonds)
        self.assertEqual(prof['charge_signs'], {'+'})

    def test_amine_n_not_ammonium(self):
        # trimethylamine: N with 3 C neighbors, no H, no charge -> no '+'
        atoms = [_atom(0, 'N', 'N'), _atom(1, 'C1', 'C'),
                 _atom(2, 'C2', 'C'), _atom(3, 'C3', 'C')]
        bonds = [(0, 1, 1), (0, 2, 1), (0, 3, 1)]
        prof = capability.ligand_profile(atoms, bonds)
        self.assertEqual(prof['charge_signs'], set())

    def test_guanidino_c_with_three_n(self):
        # C bonded to 3 N -> '+' (gate §2.3 guanidino)
        atoms = [_atom(0, 'C', 'C'), _atom(1, 'N1', 'N'),
                 _atom(2, 'N2', 'N'), _atom(3, 'N3', 'N'),
                 _atom(4, 'H1', 'H'), _atom(5, 'H2', 'H'),
                 _atom(6, 'H3', 'H'), _atom(7, 'H4', 'H')]
        bonds = [(0, 1, 2), (0, 2, 1), (0, 3, 1), (2, 4, 1), (2, 5, 1),
                 (3, 6, 1), (3, 7, 1)]
        prof = capability.ligand_profile(atoms, bonds)
        self.assertEqual(prof['charge_signs'], {'+'})

    def test_mixed_signs(self):
        # acetate anion + ammonium cation in one molecule -> both signs
        anion_atoms, anion_bonds = _acetate(formal_charges=True)
        base = len(anion_atoms)
        extra_atoms = [_atom(base, 'N', 'N'), _atom(base + 1, 'H1', 'H'),
                       _atom(base + 2, 'H2', 'H'),
                       _atom(base + 3, 'H3', 'H'),
                       _atom(base + 4, 'H4', 'H')]
        extra_bonds = [(base, base + 1, 1), (base, base + 2, 1),
                       (base, base + 3, 1), (base, base + 4, 1)]
        prof = capability.ligand_profile(anion_atoms + extra_atoms,
                                         anion_bonds + extra_bonds)
        self.assertEqual(prof['charge_signs'], {'-', '+'})


class TestAromaticRingTyping(unittest.TestCase):
    """Row 8: bond-order-derived aromaticity + 15-deg planarity
    fallback (ONLY when bond orders are absent for the cycle)."""

    def test_benzene_alternating_orders_aromatic(self):
        atoms = _ring_atoms('c', 6)
        prof = capability.ligand_profile(atoms,
                                         _ring_bonds(6, (2, 1, 2, 1, 2, 1)))
        self.assertEqual(prof['ring_count'], 1)
        self.assertEqual(sorted(prof['aromatic_rings'][0]),
                         [0, 1, 2, 3, 4, 5])

    def test_pyrrole_like_five_ring_aromatic(self):
        # 5-ring, 2 non-adjacent doubles (kekule N-H pattern)
        atoms = _ring_atoms('c', 5)
        atoms.append(_atom(5, 'n', 'N', 1.2, 0.0, 0.0))
        atoms.append(_atom(6, 'hn', 'H', 2.2, 0.0, 0.0))
        bonds = [(0, 5, 1), (5, 6, 1)]
        bonds.extend(_ring_bonds(5, (1, 2, 1, 2, 1)))
        prof = capability.ligand_profile(atoms, bonds)
        self.assertEqual(prof['ring_count'], 1)

    def test_cyclohexene_not_aromatic(self):
        atoms = _ring_atoms('c', 6)
        prof = capability.ligand_profile(atoms,
                                         _ring_bonds(6, (2, 1, 1, 1, 1, 1)))
        self.assertEqual(prof['ring_count'], 0)

    def test_cyclohexadiene_not_aromatic(self):
        # 1,4-cyclohexadiene: 2 non-adjacent doubles in a 6-ring — the
        # 6-ring rule needs 3 (perfect alternation).
        atoms = _ring_atoms('c', 6)
        prof = capability.ligand_profile(atoms,
                                         _ring_bonds(6, (2, 1, 1, 2, 1, 1)))
        self.assertEqual(prof['ring_count'], 0)

    def test_adjacent_doubles_not_aromatic(self):
        atoms = _ring_atoms('c', 6)
        prof = capability.ligand_profile(atoms,
                                         _ring_bonds(6, (2, 2, 1, 1, 1, 1)))
        self.assertEqual(prof['ring_count'], 0)

    def test_all_aromatic_markers_aromatic(self):
        # SDF bond order 4 = aromatic marker for the whole cycle
        atoms = _ring_atoms('c', 6)
        prof = capability.ligand_profile(atoms, _ring_bonds(6, (4,)))
        self.assertEqual(prof['ring_count'], 1)

    def test_partial_orders_missing_treated_single(self):
        # MDL semantics: an unmarked bond is single; [2,1,2,1,2,None]
        # is still perfect alternation.
        atoms = _ring_atoms('c', 6)
        bonds = _ring_bonds(6, (2, 1, 2, 1, 2, 1))
        bonds[5] = (5, 0, None)
        prof = capability.ligand_profile(atoms, bonds)
        self.assertEqual(prof['ring_count'], 1)

    def test_planarity_fallback_planar_no_orders(self):
        # fallback fires ONLY when bond orders are absent for the
        # cycle: planar hexagon, order None everywhere -> aromatic.
        atoms = _ring_atoms('c', 6)
        prof = capability.ligand_profile(atoms, _ring_bonds(6, (None,)))
        self.assertEqual(prof['ring_count'], 1)

    def test_planarity_fallback_puckered_no_orders(self):
        # chair-puckered ring -> adjacent-dihedral deviation far above
        # the 15-deg row-8 value -> not aromatic.
        atoms = _ring_atoms('c', 6, puck=0.8)
        prof = capability.ligand_profile(atoms, _ring_bonds(6, (None,)))
        self.assertEqual(prof['ring_count'], 0)

    def test_planarity_fallback_planar_five_ring(self):
        atoms = _ring_atoms('c', 5, radius=1.2)
        prof = capability.ligand_profile(atoms, _ring_bonds(5, (None,)))
        self.assertEqual(prof['ring_count'], 1)

    def test_planarity_fallback_envelope_five_ring(self):
        atoms = _ring_atoms('c', 5, radius=1.2, lift_idx=4)
        prof = capability.ligand_profile(atoms, _ring_bonds(5, (None,)))
        self.assertEqual(prof['ring_count'], 0)

    def test_orders_present_govern_over_geometry(self):
        # bond orders present -> the fallback does NOT fire; alternating
        # orders decide even though the fixture is planar.
        atoms = _ring_atoms('c', 6)
        prof = capability.ligand_profile(atoms,
                                         _ring_bonds(6, (2, 1, 2, 1, 2, 1)))
        self.assertEqual(prof['ring_count'], 1)


class TestDonorAcceptorTyping(unittest.TestCase):
    """Fail-closed donors; acceptors = any O/N/S."""

    def test_donor_needs_bonded_h(self):
        # N with bonded H -> donor; N without H -> not a donor (both
        # branches of the fail-closed rule).
        with_h = [_atom(0, 'N', 'N'), _atom(1, 'C', 'C'),
                  _atom(2, 'H', 'H')]
        bonds_with = [(0, 1, 1), (0, 2, 1)]
        prof = capability.ligand_profile(with_h, bonds_with)
        self.assertTrue(prof['has_donor'])

        without_h = [_atom(0, 'N', 'N'), _atom(1, 'C', 'C')]
        prof = capability.ligand_profile(without_h, [(0, 1, 1)])
        self.assertFalse(prof['has_donor'])
        self.assertTrue(prof['has_acceptor'])   # N is still an acceptor

    def test_pyridine_ring_n_donor_fail_closed(self):
        atoms = _ring_atoms('c', 6)
        atoms[0] = _atom(0, 'n0', 'N', 1.4, 0.0, 0.0)
        prof = capability.ligand_profile(atoms,
                                         _ring_bonds(6, (2, 1, 2, 1, 2, 1)))
        self.assertFalse(prof['has_donor'])
        self.assertTrue(prof['has_acceptor'])

    def test_hydroxyl_o_is_donor_and_acceptor(self):
        # methanol: the -OH oxygen is BOTH donor and acceptor-eligible
        # (the geometric test decides later).
        atoms = [_atom(0, 'C', 'C'), _atom(1, 'O', 'O'),
                 _atom(2, 'H', 'H'), _atom(3, 'HO', 'H')]
        bonds = [(0, 1, 1), (0, 2, 1), (1, 3, 1)]
        prof = capability.ligand_profile(atoms, bonds)
        self.assertTrue(prof['has_donor'])
        self.assertTrue(prof['has_acceptor'])

    def test_thiol_donor_vs_thioether(self):
        # S with H -> donor; C-S-C thioether -> acceptor only.
        thiol = [_atom(0, 'C', 'C'), _atom(1, 'S', 'S'),
                 _atom(2, 'H', 'H'), _atom(3, 'HS', 'H')]
        prof = capability.ligand_profile(
            thiol, [(0, 1, 1), (0, 2, 1), (1, 3, 1)])
        self.assertTrue(prof['has_donor'])

        thioether = [_atom(0, 'C1', 'C'), _atom(1, 'S', 'S'),
                     _atom(2, 'C2', 'C')]
        prof = capability.ligand_profile(thioether,
                                         [(0, 1, 1), (1, 2, 1)])
        self.assertFalse(prof['has_donor'])
        self.assertTrue(prof['has_acceptor'])


class TestHydrophobeHalogenMetalTyping(unittest.TestCase):
    """Row 5 qualifying carbon; row 6 halogen donors (C-F EXCLUDED);
    row 7 metal list."""

    def test_qualifying_carbon_rule(self):
        # C with all bonded neighbors in {C, H} qualifies (methane);
        # a C bonded to N does not (methylamine's C neighbors N).
        methane = capability.ligand_profile(
            [_atom(0, 'C', 'C'), _atom(1, 'H1', 'H'), _atom(2, 'H2', 'H'),
             _atom(3, 'H3', 'H'), _atom(4, 'H4', 'H')],
            [(0, 1, 1), (0, 2, 1), (0, 3, 1), (0, 4, 1)])
        self.assertTrue(methane['has_hydrophobe'])

        methylamine = capability.ligand_profile(
            [_atom(0, 'C', 'C'), _atom(1, 'N', 'N'), _atom(2, 'H1', 'H'),
             _atom(3, 'H2', 'H'), _atom(4, 'H3', 'H')],
            [(0, 1, 1), (1, 2, 1), (1, 3, 1), (1, 4, 1)])
        self.assertFalse(methylamine['has_hydrophobe'])

    def test_halogen_donor_c_cl(self):
        atoms = [_atom(0, 'C', 'C'), _atom(1, 'Cl', 'CL'),
                 _atom(2, 'H1', 'H'), _atom(3, 'H2', 'H'),
                 _atom(4, 'H3', 'H')]
        bonds = [(0, 1, 1), (0, 2, 1), (0, 3, 1), (0, 4, 1)]
        prof = capability.ligand_profile(atoms, bonds)
        self.assertTrue(prof['has_halogen_donor'])

    def test_c_f_only_excluded(self):
        # C-F EXCLUDED per the recorded gate resolution (row 6).
        atoms = [_atom(0, 'C', 'C'), _atom(1, 'F', 'F'),
                 _atom(2, 'H1', 'H'), _atom(3, 'H2', 'H'),
                 _atom(4, 'H3', 'H')]
        bonds = [(0, 1, 1), (0, 2, 1), (0, 3, 1), (0, 4, 1)]
        prof = capability.ligand_profile(atoms, bonds)
        self.assertFalse(prof['has_halogen_donor'])

    def test_bromine_and_iodine_are_donors(self):
        for elem in ('BR', 'I'):
            atoms = [_atom(0, 'C', 'C'), _atom(1, 'X', elem)]
            prof = capability.ligand_profile(atoms, [(0, 1, 1)])
            self.assertTrue(prof['has_halogen_donor'], elem)

    def test_metal_elements_list(self):
        atoms = [_atom(0, 'zn', 'zn')]
        prof = capability.ligand_profile(atoms, [])
        self.assertTrue(prof['has_metal'])
        self.assertEqual(prof['metal_elements'], ['ZN'])  # uppercased

    def test_non_list_element_not_metal(self):
        atoms = [_atom(0, 'na', 'NA')]
        prof = capability.ligand_profile(atoms, [])
        self.assertFalse(prof['has_metal'])
        self.assertEqual(prof['metal_elements'], [])


class TestLigandSupport(unittest.TestCase):
    """ligand_support(itype, profile) — generation research §2.4."""

    def test_support_table(self):
        empt = capability.ligand_profile([], [])
        donor_only = dict(empt, has_donor=True)
        acceptor_only = dict(empt, has_acceptor=True)
        ringed = dict(empt, ring_count=1)
        cationic = dict(empt, charge_signs={'+',})
        anionic = dict(empt, charge_signs={'-',})
        anionic_ringed = dict(empt, charge_signs={'-',}, ring_count=1)
        hydrophobic = dict(empt, has_hydrophobe=True)
        halogen = dict(empt, has_halogen_donor=True)
        metallic = dict(empt, has_metal=True)

        # h_bond: donor OR acceptor
        self.assertTrue(capability.ligand_support('h_bond', donor_only))
        self.assertTrue(capability.ligand_support('h_bond', acceptor_only))
        self.assertFalse(capability.ligand_support('h_bond', empt))
        # salt_bridge: charges non-empty
        self.assertTrue(capability.ligand_support('salt_bridge', anionic))
        self.assertTrue(capability.ligand_support('salt_bridge', cationic))
        self.assertFalse(capability.ligand_support('salt_bridge', empt))
        # pi_stacking: ring_count >= 1
        self.assertTrue(capability.ligand_support('pi_stacking', ringed))
        self.assertFalse(capability.ligand_support('pi_stacking', empt))
        # cation_pi: ring >= 1 OR '+' in charge_signs (either direction;
        # a ring-bearing anion still supports the AA-cation direction)
        self.assertTrue(capability.ligand_support('cation_pi', ringed))
        self.assertTrue(capability.ligand_support('cation_pi', cationic))
        self.assertTrue(capability.ligand_support('cation_pi', anionic_ringed))
        self.assertFalse(capability.ligand_support('cation_pi', empt))
        # hydrophobic / halogen / metal
        self.assertTrue(
            capability.ligand_support('hydrophobic', hydrophobic))
        self.assertFalse(capability.ligand_support('hydrophobic', empt))
        self.assertTrue(capability.ligand_support('halogen', halogen))
        self.assertFalse(capability.ligand_support('halogen', empt))
        self.assertTrue(capability.ligand_support('metal', metallic))
        self.assertFalse(capability.ligand_support('metal', empt))

    def test_unknown_type_fails_closed(self):
        self.assertFalse(capability.ligand_support('nope',
                                                   dict(
                                                       capability.ligand_profile(
                                                           [], []),
                                                       has_metal=True)))


class TestLigandHasMetal(unittest.TestCase):
    """ligand_has_metal(atoms) — the generator/detector gating helper
    (detection research §7.6, gate §5 item 5)."""

    def test_zinc_ligand(self):
        atoms = [_atom(0, 'C', 'C'), _atom(1, 'ZN', 'ZN')]
        self.assertTrue(capability.ligand_has_metal(atoms))

    def test_no_metal(self):
        atoms = [_atom(0, 'C', 'C'), _atom(1, 'O', 'O')]
        self.assertFalse(capability.ligand_has_metal(atoms))

    def test_empty(self):
        self.assertFalse(capability.ligand_has_metal([]))


if __name__ == '__main__':
    unittest.main()
