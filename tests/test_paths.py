"""Unit tests for aamatch.paths — the WSL-to-Windows path guard (plan 01-04).

Covers the exact 14-case conversion matrix from phase research R7
(.planning/phases/01-bootstrap-pure-foundation/01-RESEARCH-pure-foundation.md)
plus package_data_path resolution (package-dir-anchored, never cwd-relative).

Pure stdlib: runs under bare python3.6, no pymol/Qt.
"""

import os
import unittest

from aamatch import paths


class TestToWindowsPathMatrix(unittest.TestCase):
    """The exact 14-case matrix from research R7, one named test per row."""

    def test_01_core_conversion(self):
        # /mnt/c/Users/x/lig.pdb -> C:\Users\x\lig.pdb
        self.assertEqual(
            paths.to_windows_path('/mnt/c/Users/x/lig.pdb'),
            'C:\\Users\\x\\lig.pdb')

    def test_02_any_single_letter_drive(self):
        # /mnt/d/data/x.mol2 -> D:\data\x.mol2
        self.assertEqual(
            paths.to_windows_path('/mnt/d/data/x.mol2'),
            'D:\\data\\x.mol2')

    def test_03_drive_letter_uppercased(self):
        # /mnt/C/Users/x -> C:\Users\x
        self.assertEqual(
            paths.to_windows_path('/mnt/C/Users/x'),
            'C:\\Users\\x')

    def test_04_spaces_preserved(self):
        # /mnt/c/My Dir/a b.pdb -> C:\My Dir\a b.pdb
        self.assertEqual(
            paths.to_windows_path('/mnt/c/My Dir/a b.pdb'),
            'C:\\My Dir\\a b.pdb')

    def test_05_already_windows_backslashes_unchanged(self):
        # C:\Users\x is already Windows form -> guard passes it through
        self.assertEqual(
            paths.to_windows_path('C:\\Users\\x'),
            'C:\\Users\\x')

    def test_06_already_windows_forward_slashes_unchanged(self):
        # C:/Users/x is already a drive path -> guard passes it through
        self.assertEqual(
            paths.to_windows_path('C:/Users/x'),
            'C:/Users/x')

    def test_07_unc_path_unchanged(self):
        # \\srv\share\x -> parts[1] == '' != 'mnt' -> unchanged
        self.assertEqual(
            paths.to_windows_path('\\\\srv\\share\\x'),
            '\\\\srv\\share\\x')

    def test_08_relative_path_unchanged(self):
        # data/x.pdb -> relative, no leading '' part -> unchanged
        self.assertEqual(
            paths.to_windows_path('data/x.pdb'),
            'data/x.pdb')

    def test_09_mount_root_without_trailing_slash_unchanged(self):
        # /mnt/c -> split('/', 3) yields only 3 parts -> guard rejects.
        # Documented asymmetry vs case 10: bare mount root passes through.
        self.assertEqual(
            paths.to_windows_path('/mnt/c'),
            '/mnt/c')

    def test_10_mount_root_with_trailing_slash_converts(self):
        # /mnt/c/ -> 4th part is '' -> C:\
        self.assertEqual(
            paths.to_windows_path('/mnt/c/'),
            'C:\\')

    def test_11_multi_letter_second_component_not_a_drive(self):
        # /mnt/abc/x -> 'abc' is not a single letter -> unchanged
        self.assertEqual(
            paths.to_windows_path('/mnt/abc/x'),
            '/mnt/abc/x')

    def test_12_wsl_mountpoint_not_a_drive(self):
        # /mnt/wsl/x -> 'wsl' is not a single letter (real WSL mountpoint) -> unchanged
        self.assertEqual(
            paths.to_windows_path('/mnt/wsl/x'),
            '/mnt/wsl/x')

    def test_13_non_mount_and_empty_unchanged(self):
        # /home/u/x -> genuine Linux path; '' -> empty; both unchanged
        self.assertEqual(
            paths.to_windows_path('/home/u/x'),
            '/home/u/x')
        self.assertEqual(
            paths.to_windows_path(''),
            '')

    def test_14_idempotent(self):
        # Feeding the converted output back must return it unchanged.
        once = paths.to_windows_path('/mnt/c/Users/x/lig.pdb')
        self.assertEqual(once, 'C:\\Users\\x\\lig.pdb')
        self.assertEqual(paths.to_windows_path(once), once)


class TestPackageDataPath(unittest.TestCase):
    """package_data_path must anchor to the installed package directory,
    never os.getcwd() (PITFALLS.md Pitfall 2 / ':58 never cwd-relative')."""

    def test_resolves_under_package_dir(self):
        pkg_dir = os.path.dirname(os.path.abspath(paths.__file__))
        result = paths.package_data_path('data', 'x.pdb')
        self.assertTrue(result.startswith(pkg_dir + os.sep),
                        '%r is not under package dir %r' % (result, pkg_dir))
        self.assertEqual(result, os.path.join(pkg_dir, 'data', 'x.pdb'))

    def test_result_is_absolute_not_cwd_relative(self):
        result = paths.package_data_path('data', 'x.pdb')
        self.assertTrue(os.path.isabs(result))
        # Independent of cwd: anchored to the module location itself.
        self.assertEqual(
            os.path.dirname(os.path.dirname(result)),
            os.path.dirname(os.path.abspath(paths.__file__)))

    def test_accepts_single_part(self):
        pkg_dir = os.path.dirname(os.path.abspath(paths.__file__))
        self.assertEqual(
            paths.package_data_path('levels.json'),
            os.path.join(pkg_dir, 'levels.json'))


if __name__ == '__main__':
    unittest.main()
