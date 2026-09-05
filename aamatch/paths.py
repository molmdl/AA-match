"""Pure path helpers: WSL-to-Windows path guard + bundled-data resolution.

Layer: PURE (Phase-1 foundation). Module-level imports are stdlib-only
(``os``); no pymol, no Qt -- unit-testable under bare python3.6
(Phase-1 success criterion 2).

``to_windows_path`` ports the proven prior-art guard (bioCHEMeleon
demos.py:59-78; research F1-F2) verbatim: PyMOL runs as a Windows
process (launched via setenv.bat) and cannot resolve WSL ``/mnt/...``
paths, so every future ``cmd.load``/``cmd.save``/file-API call routes
through it first (PITFALLS.md Pitfall 2).

``package_data_path`` anchors bundled data to the installed package
directory (``__file__``), never ``os.getcwd()`` (PITFALLS.md:58).
"""

import os


def to_windows_path(path):
    """Convert a WSL mount path (/mnt/c/...) to a Windows path (C:\\...).

    PyMOL runs as a Windows process (launched via setenv.bat) and cannot
    resolve WSL paths. This is a GUARD, not an unconditional transform:
    only paths starting with /mnt/<single letter>/ are converted; all
    other paths (already-Windows C:\\... from an installed plugin, UNC
    shares, relative paths, and genuine Linux paths, plus '') are
    returned unchanged. Conversion is idempotent and preserves spaces.

    Known asymmetry (matrix case 9): the bare mount root '/mnt/c' (no
    trailing slash) is returned unchanged -- split('/', 3) yields only
    3 parts, so the guard rejects it -- while '/mnt/c/' (empty 4th
    part) converts to 'C:\\'. Real call sites always carry a filename
    below the mount root, so the asymmetry is harmless; it is pinned by
    test_09_mount_root_without_trailing_slash_unchanged.

    The ``len(parts) == 4`` term is LOAD-BEARING (matches prior art
    demos.py:73): without it, '/mnt/c' would pass the shortened guard
    and hit IndexError on parts[3] instead of returning unchanged.

    Source: prior art demos.py:59-78; research F1-F2, R7.
    """
    p = str(path)
    parts = p.replace('\\', '/').split('/', 3)
    # parts looks like ['', 'mnt', 'c', 'Users/...'] for a WSL mount path
    if len(parts) == 4 and parts[0] == '' and parts[1] == 'mnt' \
            and len(parts[2]) == 1 and parts[2].isalpha():
        drive = parts[2].upper()
        rest = parts[3]
        return '{}:\\{}'.format(drive, rest.replace('/', '\\'))
    return p


def package_data_path(*parts):
    """Resolve a bundled-data path relative to the INSTALLED plugin location.

    Anchors to this module's own directory (``__file__``), never
    ``os.getcwd()``: PyMOL's working directory is arbitrary at runtime,
    so bundled data must resolve from wherever aamatch is installed.

    Example: package_data_path('data', 'x.pdb') -> <package dir>/data/x.pdb
    """
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), *parts)
