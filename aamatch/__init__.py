# Version: 0.1.0
# Citation-Required: No
"""AA-match — educational small-molecule <-> amino-acid interaction matching game.

PyMOL 2.5.0 plugin. Phase 1: installable skeleton; game UI arrives in Phase 4.
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
    """Phase-1 placeholder. Deliberately Qt-free: proves the menu wiring at
    the [HUMAN] checkpoint and contains zero code Phase 4 must rewrite."""
    print('AA-match %s: plugin skeleton OK — game UI arrives in Phase 4.' % __version__)
