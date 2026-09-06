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
        self.assertEqual(entry['rings'],
                         [['CG', 'ND1', 'CD2', 'CE1', 'NE2']])

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


if __name__ == '__main__':
    unittest.main()
