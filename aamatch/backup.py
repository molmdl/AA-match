"""Backup pure core: snapshot/restore/discard/verify_intact over an INJECTED store.

PyMOL Open Source has NO undo — it ships a no-op `undocontext` stub
(editor.py:25-36, "not implemented in open-source"). Every destructive
mutation MUST therefore be preceded by a snapshot and followed by either a
discard (happy path) or a restore (failure path), with verify_intact as the
integrity proof. This module owns that POLICY; callers INJECT storage, so
the module is unit-testable in WSL with the stdlib alone (Phase-1 criterion 2).

Store protocol (duck-typed; both implementations live here, both pure stdlib):

    save_bytes(key, data: bytes)   store bytes under a simple-filename key
    load_bytes(key) -> bytes       bytes back; missing key -> BackupError
    delete(key)                    idempotent (absent key is fine)
    exists(key) -> bool

Stored format (self-describing; survives on-disk corruption detection):

    sha256(canonical_json).hexdigest().encode('ascii') + b'\\n' + canonical_json

`snapshot` returns a manifest dict {'key', 'sha256', 'timestamp'}; `restore`
splits the stored bytes, re-computes the sha256 and raises
``BackupError("backup corrupt ...")`` on any mismatch (corruption gate),
returning the decoded payload dict otherwise. `verify_intact` runs the SAME
gate and returns False on corruption instead of raising (after the
missing-key check, which raises).

Missing-key discipline (prior-art E3 / PITFALLS.md P7): a missing backup is
an ERROR, not a re-derivation trigger. ``restore``/``verify_intact`` raise
``BackupError("no backup stored under key %r")``; callers ASSERT the return
value / catch the error — never re-call on an already-discarded backup.

BACKUP_OBJECT_PREFIX ('_aam_backup') is reserved for the FUTURE cmd-tier
adapter (PyMOL object snapshotting via cmd.create) — deliberately NOT
implemented here; underscore = private-object convention.

Purity: module-level imports are stdlib only (hashlib, json, os, tempfile,
time). NO `pymol` import at module level OR inside any function body — this
module must import cleanly under bare python3.6 with zero stubs.
"""

import hashlib
import json
import os
import tempfile
import time

# Reserved for the future cmd-tier adapter's PyMOL backup objects
# (underscore => private/hidden per the prior-art convention).
BACKUP_OBJECT_PREFIX = '_aam_backup'

_SHA_HEX_LEN = 64        # length of a lowercase hex sha256 digest
_SEPARATOR = b'\n'       # splits the sha256 header from the canonical JSON
_TEMP_PREFIX = '.aam_'   # FileStore temp-file prefix (never left behind)


class BackupError(Exception):
    """Raised for missing backups, corrupt backups, or unsafe keys."""


# ---- Canonical form ----

def _canonical(payload):
    """Canonical JSON bytes for a payload: sorted keys, no NaN/Infinity.

    `allow_nan=False` makes non-finite floats fail loudly instead of
    emitting non-standard JSON tokens; `sort_keys=True` makes the bytes
    deterministic (key order irrelevant).
    """
    return json.dumps(payload, sort_keys=True, allow_nan=False).encode('utf-8')


# ---- Stored-bytes framing (sha256 header + canonical JSON) ----

def _pack(data):
    """Frame canonical bytes as stored bytes: sha256hex + b'\\n' + data."""
    return hashlib.sha256(data).hexdigest().encode('ascii') + _SEPARATOR + data


def _unpack(data, key):
    """Validate stored bytes and return the canonical payload region.

    Raises BackupError('backup corrupt ...') on any structural or sha256
    mismatch — the corruption gate exercised by the byte-flip test.
    """
    if (len(data) < _SHA_HEX_LEN + 1
            or data[_SHA_HEX_LEN:_SHA_HEX_LEN + 1] != _SEPARATOR):
        raise BackupError(
            "backup corrupt (missing sha256 header) for key %r" % (key,))
    try:
        stored_hex = data[:_SHA_HEX_LEN].decode('ascii')
    except UnicodeDecodeError:
        raise BackupError(
            "backup corrupt (sha256 header not ascii) for key %r" % (key,))
    payload = data[_SHA_HEX_LEN + 1:]
    if hashlib.sha256(payload).hexdigest() != stored_hex:
        raise BackupError(
            "backup corrupt (sha256 mismatch) for key %r" % (key,))
    return payload


def _decode_payload(key, payload_bytes):
    """Decode canonical JSON bytes back into a Python object."""
    try:
        return json.loads(payload_bytes.decode('utf-8'))
    except (UnicodeDecodeError, ValueError):
        raise BackupError(
            "backup corrupt (unparseable JSON) for key %r" % (key,))


# ---- Key safety: keys are simple filenames, never paths ----

def _check_key(key):
    """Reject keys that are not simple filenames (keeps store paths safe)."""
    if (not isinstance(key, str) or not key or os.sep in key
            or (os.altsep and os.altsep in key)
            or key in (os.curdir, os.pardir)):
        raise BackupError(
            "invalid backup key %r: keys must be simple filenames "
            "(no path separators)" % (key,))


# ---- Store implementations ----

class MemoryStore(object):
    """Dict-backed in-memory store (tests, and future cmd-tier adapters)."""

    def __init__(self):
        self._data = {}

    def save_bytes(self, key, data):
        _check_key(key)
        self._data[key] = bytes(data)

    def load_bytes(self, key):
        _check_key(key)
        if key not in self._data:
            raise BackupError("no backup stored under key %r" % (key,))
        return self._data[key]

    def delete(self, key):
        _check_key(key)
        self._data.pop(key, None)

    def exists(self, key):
        _check_key(key)
        return key in self._data


class FileStore(object):
    """Filesystem store: atomic saves (temp file + os.replace), idempotent delete."""

    def __init__(self, root_dir):
        self.root = root_dir
        os.makedirs(self.root, exist_ok=True)

    def _path(self, key):
        _check_key(key)
        return os.path.join(self.root, key)

    def save_bytes(self, key, data):
        path = self._path(key)
        fd, tmp = tempfile.mkstemp(dir=self.root, prefix=_TEMP_PREFIX,
                                   suffix='.tmp')
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)  # atomic overwrite
        except Exception:
            try:
                os.remove(tmp)  # best-effort litter cleanup on failure
            except OSError:
                pass
            raise

    def load_bytes(self, key):
        path = self._path(key)
        if not os.path.exists(path):
            raise BackupError("no backup stored under key %r" % (key,))
        with open(path, 'rb') as f:
            return f.read()

    def delete(self, key):
        path = self._path(key)
        try:
            os.remove(path)
        except OSError:
            pass  # idempotent: absent key is fine

    def exists(self, key):
        return os.path.exists(self._path(key))


# ---- The lifecycle (policy over any injected store) ----

def snapshot(store, key, payload):
    """Store a corruption-detected backup of a JSON-serializable payload.

    Replaces any stale backup under the same key. Returns a manifest dict:
    {'key': key, 'sha256': <64-char lowercase hex>, 'timestamp': <float>}.
    The manifest sha is read back from the stored header, so the manifest
    and the stored bytes describe the SAME digest by construction.
    """
    data = _canonical(payload)
    stored = _pack(data)
    store.save_bytes(key, stored)
    return {
        'key': key,
        'sha256': stored[:_SHA_HEX_LEN].decode('ascii'),
        'timestamp': time.time(),
    }


def verify_intact(store, key, current_payload):
    """Return True iff the stored backup is intact AND matches current_payload.

    Byte-level proof: the stored payload region (sha256-gated) must equal
    the canonical form of current_payload. A missing backup raises
    BackupError('no backup ...') — assert, don't re-derive (P7 discipline);
    a CORRUPT backup returns False instead of raising.
    """
    data = store.load_bytes(key)  # missing -> BackupError from the store
    try:
        payload_bytes = _unpack(data, key)
    except BackupError:
        return False  # corruption gate: report, don't raise
    return payload_bytes == _canonical(current_payload)


def restore(store, key):
    """Return the backed-up payload dict (failure-path recovery).

    Missing backup -> BackupError('no backup stored under key %r').
    Corrupt backup (sha256 gate) -> BackupError('backup corrupt ...').
    The CALLER asserts the result and routes failure to regenerate-from-spec
    (the seeded level spec is the source of truth); never re-call this on an
    already-discarded backup.
    """
    data = store.load_bytes(key)  # missing -> BackupError from the store
    payload_bytes = _unpack(data, key)  # corrupt -> BackupError
    return _decode_payload(key, payload_bytes)


def discard(store, key):
    """Delete the backup. Idempotent (absent key is not an error)."""
    store.delete(key)
