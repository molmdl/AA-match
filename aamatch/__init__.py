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
    """Launch the Phase-3 playable wizard loop (Plugins -> AA-match).

    Returns the live GameWizard (headless callers assert on it). The
    import is lazy (Gate A2: zero module-level imports here). Phase 4
    replaces this with the Qt setup window calling the SAME gamestart
    seam (gamestart.start_game) with the user's validated setup.
    EngineError/WizardError propagate fail-closed -- PyMOL's menu
    handler surfaces the traceback."""
    from . import gamestart
    return gamestart.start_game()
