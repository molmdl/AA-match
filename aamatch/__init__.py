# Version: 0.1.0
# Citation-Required: No
"""AA-match — educational small-molecule <-> amino-acid interaction matching game.

PyMOL 2.5.0 plugin. Phase 3: the Plugins-menu item starts the playable
wizard game loop; the Phase-4 Qt setup window reuses the same seam.
"""
# NOTE: the metadata block above MUST be the first lines of this file.
# pymol.plugins parses "# Key: value" comment lines at the very top and
# STOPS at the first non-# line (plugins/__init__.py:193-210). A '# Version:'
# line after the docstring parses to {} and breaks reinstall version compares.

__version__ = '0.1.0'   # keep in sync with the metadata block above


def __init_plugin__(app=None):
    """PyMOL plugin entry point — registers the Plugins-menu item.

    addmenuitemqt is imported locally and called FIRST: headless
    (HAVE_QT=False, plugins/__init__.py:29) it raises QtNotAvailableError,
    which the loader catches cleanly (plugins/__init__.py:287-288). Keeping
    it first also avoids the cmd.extend restore quirk
    (plugins/__init__.py:266-282).
    """
    from pymol.plugins import addmenuitemqt
    addmenuitemqt('AA-match', run_plugin_gui)


def run_plugin_gui():
    """Open the Phase-4 modeless Qt setup window (Plugins -> AA-match).

    Returns the SetupWindow dialog (assertion handle, 03-05 pattern).
    The import is lazy (Gate A2: zero module-level imports here). The
    window delegates Start to gamestart.start_game -- the SAME seam
    this function used in Phase 3. ValueError-family refusals are
    caught per button by the window's _guard; unexpected exceptions
    propagate fail-closed."""
    from . import setup_window
    return setup_window.open_window()
