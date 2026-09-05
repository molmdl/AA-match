"""aamatch.persistence -- versioned-container core + atomic JSON file I/O.

The single format discipline for ALL AA-match files (setup, level_spec,
game, checkpoint): every file is a versioned container

    {"magic": "AAMATCH", "version": 1, "kind": <KINDS entry>, "data": {...}}

Refusal semantics (clear FormatError messages, prior-art phrasing):
- foreign file (wrong magic)  -> "not an AA-match file (...)"
- newer file (version > ours) -> "unsupported AA-match format version ... Please update AA-match."
- misfiled kind               -> "expected an AA-match <kind> file, found kind=..."
- unparseable JSON            -> "could not parse AA-match JSON: ..."

Versioning policy: refuse-newer / accept-older. Older container versions
(version < FORMAT_VERSION) are ACCEPTED -- additive-only evolution: new
optional fields are ignored by old readers; new readers fill older files
from .get() defaults. Any semantic change to an existing field requires a
version bump. No header checksum by design: hand-editable educator files
are a feature (corruption surfaces as a parse error with a clear message).

Purity: module-level imports are stdlib (json, os, tempfile) ONLY.
NO `pymol` / Qt / numpy import at module level OR inside any function
body, so this module unit-tests in WSL with bare python3.6 and zero stubs.
"""

import json
import os
import tempfile

AAM_MAGIC = "AAMATCH"
FORMAT_VERSION = 1
KINDS = ('setup', 'level_spec', 'game', 'checkpoint')


class FormatError(ValueError):
    """An AA-match file is foreign, too new, misfiled, or unparseable."""


def make_container(kind, data):
    """Build a versioned container dict around `data`.

    Raises FormatError for a kind outside KINDS.
    """
    if kind not in KINDS:
        raise FormatError(
            "unknown AA-match file kind %r (expected one of: %s)"
            % (kind, ', '.join(KINDS)))
    return {
        "magic": AAM_MAGIC,
        "version": FORMAT_VERSION,
        "kind": kind,
        "data": data,
    }


def check_container(raw_dict, expected_kind):
    """Validate a loaded dict as an AA-match container of `expected_kind`.

    Returns the container dict unchanged on success. Refusals:
    1. magic mismatch -> foreign file ("not an AA-match file")
    2. version > FORMAT_VERSION -> newer file ("unsupported ... Please update")
    3. kind != expected_kind -> misfiled ("expected an AA-match <kind> file")

    Older versions (version < FORMAT_VERSION) are accepted: additive-only
    evolution, readers use .get() defaults for fields older files lack.
    """
    magic = raw_dict.get('magic')
    if magic != AAM_MAGIC:
        raise FormatError(
            "not an AA-match file (magic=%r, expected %r)" % (magic, AAM_MAGIC))
    try:
        version = int(raw_dict.get('version'))
    except (TypeError, ValueError):
        raise FormatError("missing or invalid version field in AA-match file")
    if version > FORMAT_VERSION:
        raise FormatError(
            "unsupported AA-match format version %d (expected <= %d). "
            "Please update AA-match." % (version, FORMAT_VERSION))
    kind = raw_dict.get('kind')
    if kind != expected_kind:
        raise FormatError(
            "expected an AA-match %s file, found kind=%r" % (expected_kind, kind))
    return raw_dict


def write_json_atomic(path, obj):
    """Serialize `obj` to `path` atomically: temp file + fsync + os.replace.

    Byte-stable, diff-able output (sort_keys, indent=2, binary write) and
    loud NaN/Infinity refusal (allow_nan=False). On any failure the temp
    file is removed (best-effort) and the original file is left untouched.
    """
    payload = json.dumps(obj, indent=2, sort_keys=True, allow_nan=False)
    data = payload.encode('utf-8')
    dir_name = os.path.dirname(os.path.abspath(path)) or '.'
    fd, tmp = tempfile.mkstemp(dir=dir_name, prefix='.aam_', suffix='.tmp')
    try:
        with os.fdopen(fd, 'wb') as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def read_json_file(path):
    """Read a JSON file in binary mode and return the parsed object.

    Binary mode avoids Windows CRLF translation, keeping files byte-stable.
    A parse failure raises FormatError with a clear message (never a bare
    json.JSONDecodeError).
    """
    with open(path, 'rb') as fh:
        raw = fh.read()
    try:
        return json.loads(raw)
    except ValueError as exc:
        raise FormatError("could not parse AA-match JSON: %s" % exc)


def save_container(path, kind, data):
    """Write `data` as a versioned container of `kind` to `path` atomically."""
    write_json_atomic(path, make_container(kind, data))


def load_container(path, expected_kind):
    """Read and validate a container file; return its `data` payload.

    Transparent to callers: header refusal classes are handled by
    check_container (foreign / newer / misfiled).
    """
    return check_container(read_json_file(path), expected_kind)['data']
