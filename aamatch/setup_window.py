"""aamatch.setup_window -- Qt-tier modeless setup window (Phase 4).

Layer: QT TIER. Module-level ``from pymol.Qt import ...`` is legal and
REQUIRED here (the class definition needs QtWidgets at class-creation
time); this module must NEVER be added to ``PURE_MODULES`` in
``tests/test_purity.py`` and is never imported by WSL tests -- it is
covered by the AST source gates only (Gate D still compiles it under
the 3.6 syntax floor).

THE BINDING CONTRACTS:

1. MODELESS WINDOW -- the main dialog is shown via
   show()/raise_()/activateWindow(), NEVER .exec_() (which would block
   PyMOL's event loop and freeze the viewer -- SETUP-01, PITFALL P1).
   Modal .exec_()/static forms are allowed on CHILD dialogs only
   (QFileDialog/QMessageBox in later handler plans).

2. SINGLETON + REUSE-AND-RAISE -- ``_window`` lives at MODULE scope
   (a module-level reference prevents GC; a dialog held in a local
   variable flashes and vanishes -- the v1 module docstring receipt).
   open_window() constructs on first call only, so a second menu fire
   reuses and raises the SAME dialog, never duplicates it.

3. NO closeEvent OVERRIDE -- deliberately. The default close hides the
   dialog; the module-level singleton keeps the object alive, so
   re-open is reuse-and-raise. That IS SETUP-01's
   survive-minimize/re-open mechanism (the v1 codebase carries zero
   closeEvent overrides -- repo-wide grep receipt).

4. LAZY SIBLING IMPORTS -- sibling aamatch modules (setup_state,
   gamestart, persistence, ...) are imported RELATIVELY INSIDE the
   handler methods that need them (``from . import <sibling>``), so the
   module behaves identically when imported as ``aamatch``
   (smokes/plugin-path) and as ``pmg_tk.startup.aamatch`` (installed)
   -- the module-identity law, wizard.py's contract-2 shape.

Credits: the module-level singleton, the create-if-None open trio, and
the no-closeEvent rule are borrowed from the shipped v1 plugin
(bioCHEMeleon tmp/bioCHEMeleon/biochemeleon/__init__.py, verified
2026-09-13; 04-RESEARCH-qt-window-architecture.md borrowed pattern 1).

House rules: python-3.6 syntax floor, %-formatting only, no logging,
no print -- handler errors propagate fail-closed; user-facing status
via QMessageBox in the handler plans.
"""

from pymol.Qt import QtWidgets, QtCore, QtGui

# The GC-prevention singleton -- MUST be module scope, never a local
# (the v1 dialog=None receipt). Gate A2 scans aamatch/__init__.py only,
# so a module-level sentry here is legal in the Qt tier.
_window = None


def open_window():
    """Modeless open: create-if-None, then show/raise_/activateWindow.

    Returns the SetupWindow dialog so headless callers (SMOKE-11) have
    an assertion handle (03-05 pattern). A second call reuses and
    raises the SAME dialog instance -- reuse-and-raise, never a
    duplicate (the v1 menu-handler trio, adapted verbatim).
    """
    global _window
    if _window is None:
        _window = SetupWindow()
    _window.show()
    _window.raise_()
    _window.activateWindow()
    return _window


class SetupWindow(QtWidgets.QDialog):
    """The modeless setup window shell (SETUP-01).

    04-05 scope: window lifecycle + an empty form-area placeholder +
    the 7-button row created IN SPEC ORDER with tooltips and NOT
    connected (each handler plan connects its own button; no dead stub
    handlers). The form fields land in 04-07.
    """

    def __init__(self):
        # NO parent -- a modeless top-level window must not be owned by
        # another widget (parenting would pin its lifecycle/geometry).
        super(SetupWindow, self).__init__()
        self.setWindowTitle('AA-match Setup')
        self.setMinimumWidth(420)   # the v1 dialog precedent

        top = QtWidgets.QVBoxLayout(self)

        # (a) form-area placeholder -- the 7-field form lands here in
        # 04-07; the placeholder widget keeps the layout slot stable.
        self.form_area = QtWidgets.QWidget(self)
        self.form_area.setLayout(QtWidgets.QVBoxLayout())
        top.addWidget(self.form_area)

        # (b) stretch -- keeps the button row pinned to the bottom.
        top.addStretch(1)

        # (c) the 7-button row, created IN SPEC ORDER (spec.md: row 3:
        # Reset, Randomize, Save Setup, Load Setup, Generate and
        # export, Cleanup model, Start) with spec-meaning tooltips.
        # Created but NOT connected -- each handler plan (04-09..04-13)
        # connects its own button; no dead stub handlers here.
        row = QtWidgets.QHBoxLayout()
        self.btn_reset = QtWidgets.QPushButton('Reset', self)
        self.btn_reset.setToolTip('Restore the default settings.')
        self.btn_randomize = QtWidgets.QPushButton('Randomize', self)
        self.btn_randomize.setToolTip('Randomize the setup parameters.')
        self.btn_save_setup = QtWidgets.QPushButton('Save Setup', self)
        self.btn_save_setup.setToolTip(
            'Save the game setup parameters to a file.')
        self.btn_load_setup = QtWidgets.QPushButton('Load Setup', self)
        self.btn_load_setup.setToolTip(
            'Load the setup parameters from a file.')
        self.btn_generate_export = QtWidgets.QPushButton(
            'Generate and export', self)
        self.btn_generate_export.setToolTip(
            'Generate all levels and save the initial game state to a '
            'file for sharing or later loading.')
        self.btn_cleanup = QtWidgets.QPushButton('Cleanup model', self)
        self.btn_cleanup.setToolTip(
            'Remove the game-generated objects from the scene.')
        self.btn_start = QtWidgets.QPushButton('Start', self)
        self.btn_start.setToolTip('Start the game with the current setup.')
        for btn in (self.btn_reset, self.btn_randomize,
                    self.btn_save_setup, self.btn_load_setup,
                    self.btn_generate_export, self.btn_cleanup,
                    self.btn_start):
            row.addWidget(btn)
        top.addLayout(row)

    # NO closeEvent OVERRIDE -- on purpose: default close hides the
    # dialog, and the module-level _window singleton keeps the object
    # alive, so re-open via open_window() is reuse-and-raise. That is
    # SETUP-01's survive-minimize/re-open mechanism (the v1 codebase
    # has ZERO closeEvent overrides -- repo-wide grep receipt).

    # NOTE: module-level ``from pymol import cmd`` is deliberately NOT
    # added here -- only the 04-11 cleanup handler needs cmd, and it
    # lands there (04-05 plan decision). QtCore/QtGui are part of the
    # wrapper shim's unit import and are kept for the handler plans.
