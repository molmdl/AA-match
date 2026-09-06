"""Tests for aamatch.manifest -- bundled-data manifest container.

RED-first suite for plan 02-03. Covers:

- 'manifest' as a first-class container kind (additive KINDS change in
  aamatch/persistence.py; refusal messages stay built from KINDS)
- parse/validate/enumerate of the manifest payload (Task 2, added below)

Runs under bare python3.6 in WSL with stdlib only (no pymol/Qt/numpy
stubs needed -- the module under test is pure).
"""

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aamatch.persistence import (
    KINDS,
    FormatError,
    check_container,
    make_container,
)


class TestManifestContainerKind(unittest.TestCase):
    """'manifest' is a legal container kind (Task 1)."""

    def test_make_container_manifest_succeeds(self):
        container = make_container('manifest', {'manifest_version': 1,
                                                'sets': []})
        self.assertEqual(container['kind'], 'manifest')
        self.assertEqual(container['magic'], 'AAMATCH')

    def test_check_container_accepts_manifest_kind(self):
        container = make_container('manifest', {'manifest_version': 1,
                                                'sets': []})
        result = check_container(container, 'manifest')
        self.assertIs(result, container)

    def test_manifest_in_kinds_tuple(self):
        self.assertIn('manifest', KINDS)

    def test_unknown_kind_still_refused_with_canonical_message(self):
        with self.assertRaises(FormatError) as ctx:
            make_container('bogus', {})
        message = str(ctx.exception)
        self.assertIn('unknown AA-match file kind', message)
        self.assertIn('bogus', message)

    def test_misfiled_kind_still_refused_with_canonical_message(self):
        manifest = make_container('manifest', {})
        with self.assertRaises(FormatError) as ctx:
            check_container(manifest, 'setup')
        self.assertIn('expected an AA-match setup file', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
