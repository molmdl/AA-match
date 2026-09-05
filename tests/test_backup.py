"""Unit tests for aamatch.backup — pure backup core over injected stores.

Plan 01-03 (TDD, RED-first). Covers the planned behaviors over BOTH stores
(MemoryStore, FileStore) via a shared contract base class, plus the
FileStore on-disk corruption simulation (PITFALLS.md:181 — a corrupt-mutation
must be DETECTED; documented recovery = regenerate from the seeded spec),
MemoryStore tampering, atomic-save litter check, and cross-instance
FileStore durability.

Run:
    python3.6 -m unittest tests.test_backup -v
    python3.6 -m unittest discover -s tests -v
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from aamatch.backup import (
    BACKUP_OBJECT_PREFIX,
    BackupError,
    FileStore,
    MemoryStore,
    _canonical,
    discard,
    restore,
    snapshot,
    verify_intact,
)

# A JSON-serializable payload exercising nested dicts, lists, ints, floats
# and non-ASCII unicode. The round-trip contract is EXACT dict equality.
PAYLOAD = {
    'object': 'ligand_01',
    'label': 'Amino-Acid Match – Ünïcødé ✓',
    'counts': {'atoms': 9, 'residues': 1},
    'atoms': [
        {'name': 'N', 'resi': 1, 'chain': 'A'},
        {'name': 'CA', 'resi': 1, 'chain': 'A'},
        {'name': 'C', 'resi': 1, 'chain': 'A'},
    ],
    'ratio': 0.5,
    'level': 2,
}


class BackupContractTestCase(unittest.TestCase):
    """Shared snapshot/restore/discard/verify contract, one run per store."""

    def make_store(self):
        raise NotImplementedError('subclass must provide a store factory')

    def setUp(self):
        self.store = self.make_store()
        self.key = 'game_backup'

    # ---- case 1: exact round-trip (nested dicts + unicode) ----
    def test_snapshot_restore_roundtrip_exact(self):
        snapshot(self.store, self.key, PAYLOAD)
        self.assertEqual(restore(self.store, self.key), PAYLOAD)

    # ---- case 2: manifest shape ----
    def test_snapshot_returns_manifest(self):
        manifest = snapshot(self.store, self.key, PAYLOAD)
        self.assertEqual(manifest['key'], self.key)
        sha = manifest['sha256']
        self.assertEqual(len(sha), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in sha),
                        'sha256 must be lowercase hex, got %r' % (sha,))
        self.assertIsInstance(manifest['timestamp'], float)

    # ---- case 3: verify_intact True / False on any nested change ----
    def test_verify_intact_true_and_false_on_nested_change(self):
        snapshot(self.store, self.key, PAYLOAD)
        self.assertTrue(verify_intact(self.store, self.key, PAYLOAD))

        mutated_counts = dict(PAYLOAD)
        mutated_counts['counts'] = {'atoms': 10, 'residues': 1}  # 9 -> 10
        self.assertFalse(verify_intact(self.store, self.key, mutated_counts))

        swapped = [PAYLOAD['atoms'][0], PAYLOAD['atoms'][2], PAYLOAD['atoms'][1]]
        mutated_order = dict(PAYLOAD)
        mutated_order['atoms'] = swapped
        self.assertFalse(verify_intact(self.store, self.key, mutated_order))

    # ---- case 4: restore on a missing key ----
    def test_restore_missing_key_raises_no_backup(self):
        with self.assertRaises(BackupError) as cm:
            restore(self.store, 'never_snapshotted')
        self.assertIn('no backup', str(cm.exception))

    # ---- case 5: verify_intact on a missing key raises (P7/E3 discipline) ----
    def test_verify_intact_missing_key_raises(self):
        with self.assertRaises(BackupError) as cm:
            verify_intact(self.store, self.key, PAYLOAD)
        self.assertIn('no backup', str(cm.exception))

    # ---- case 6: discard idempotent; restore after discard raises ----
    def test_discard_idempotent_then_restore_raises(self):
        snapshot(self.store, self.key, PAYLOAD)
        discard(self.store, self.key)
        discard(self.store, self.key)  # second discard must NOT raise
        with self.assertRaises(BackupError) as cm:
            restore(self.store, self.key)
        self.assertIn('no backup', str(cm.exception))

    # ---- case 7: snapshot over an existing key REPLACES (stale discard) ----
    def test_snapshot_replaces_stale_backup(self):
        snapshot(self.store, self.key, PAYLOAD)
        second = dict(PAYLOAD)
        second['level'] = 99
        snapshot(self.store, self.key, second)
        self.assertEqual(restore(self.store, self.key), second)

    # ---- case 10: canonical determinism (key order irrelevant) ----
    def test_canonical_is_order_insensitive(self):
        self.assertEqual(_canonical({'b': 1, 'a': 2}),
                         _canonical({'a': 2, 'b': 1}))
        nested_a = {'outer': {'z': 1, 'a': 2}, 'm': [3, 1]}
        nested_b = {'m': [3, 1], 'outer': {'a': 2, 'z': 1}}
        self.assertEqual(_canonical(nested_a), _canonical(nested_b))


class MemoryStoreBackupTests(BackupContractTestCase):
    """Contract over the dict-backed in-memory store."""

    def make_store(self):
        return MemoryStore()

    # ---- case 9: corruption detected against MemoryStore ----
    def test_tampered_memory_backup_detected(self):
        snapshot(self.store, self.key, PAYLOAD)
        # Tamper the stored bytes directly via the store's internal mapping
        # (same effect as a hostile write): garbage is not a valid backup.
        self.store.save_bytes(self.key, b'this is not a backup at all')
        with self.assertRaises(BackupError) as cm:
            restore(self.store, self.key)
        self.assertIn('backup corrupt', str(cm.exception))
        self.assertFalse(verify_intact(self.store, self.key, PAYLOAD))


class FileStoreBackupTests(BackupContractTestCase):
    """Contract over the filesystem store (temp file + os.replace)."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='aam_backup_test_')
        BackupContractTestCase.setUp(self)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def make_store(self):
        return FileStore(self.root)

    # ---- case 8: THE load-bearing corruption simulation (PITFALLS.md:181) ----
    def test_ondisk_byte_flip_in_payload_detected(self):
        snapshot(self.store, self.key, PAYLOAD)
        path = os.path.join(self.root, self.key)
        with open(path, 'rb') as f:
            raw = bytearray(f.read())
        # Flip ONE byte inside the payload region (after 64-hex sha + newline).
        raw[64 + 1 + 2] ^= 0xFF
        with open(path, 'wb') as f:
            f.write(bytes(raw))
        with self.assertRaises(BackupError) as cm:
            restore(self.store, self.key)
        self.assertIn('backup corrupt', str(cm.exception))
        self.assertFalse(verify_intact(self.store, self.key, PAYLOAD))

    def test_ondisk_byte_flip_in_sha_header_detected(self):
        snapshot(self.store, self.key, PAYLOAD)
        path = os.path.join(self.root, self.key)
        with open(path, 'rb') as f:
            raw = bytearray(f.read())
        # Flip one byte inside the stored sha256 hex header itself.
        raw[10] ^= 0xFF
        with open(path, 'wb') as f:
            f.write(bytes(raw))
        with self.assertRaises(BackupError) as cm:
            restore(self.store, self.key)
        self.assertIn('backup corrupt', str(cm.exception))

    # ---- case 11: atomic save leaves no temp litter ----
    def test_atomic_save_leaves_no_temp_litter(self):
        snapshot(self.store, self.key, PAYLOAD)
        leftovers = [n for n in os.listdir(self.root) if n.startswith('.aam_')]
        self.assertEqual(leftovers, [])

    # ---- case 12: FileStore round-trip across instances (disk persistence) ----
    def test_filestore_persists_across_instances(self):
        snapshot(self.store, self.key, PAYLOAD)
        fresh = FileStore(self.root)
        self.assertEqual(restore(fresh, self.key), PAYLOAD)

    # ---- key safety: keys are simple filenames (path-traversal guard) ----
    def test_unsafe_keys_rejected(self):
        for bad in ['sub/dir', '../evil', os.sep + 'abs', '..', '']:
            with self.assertRaises(BackupError):
                snapshot(self.store, bad, PAYLOAD)


class ModuleContractTests(unittest.TestCase):
    """Module-level contract pins."""

    def test_backup_object_prefix_reserved_for_cmd_adapter(self):
        # Documented for the future cmd-tier adapter (not implemented here).
        # Underscore = private-object convention (prior-art E2).
        self.assertEqual(BACKUP_OBJECT_PREFIX, '_aam_backup')
        self.assertTrue(BACKUP_OBJECT_PREFIX.startswith('_'))


if __name__ == '__main__':
    unittest.main()
