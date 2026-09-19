"""aamatch.setup_window -- Qt-tier modeless setup window (Phase 4).

Layer: QT TIER. Module-level ``from pymol.Qt import ...`` is legal and
REQUIRED here (the class definition needs QtWidgets at class-creation
time); module-level ``from pymol import cmd`` is likewise legal in the
Qt tier (04-11, Decision 17 -- the cleanup handler needs raw cmd).
This module must NEVER be added to ``PURE_MODULES`` in
``tests/test_purity.py`` and is never imported by WSL tests -- it is
covered by the AST source gates only (Gate D still compiles it under
the 3.6 syntax floor).

THE BINDING CONTRACTS:

1. MODELESS WINDOW -- the main dialog is shown via
   show()/raise_()/activateWindow(), NEVER .exec_() (which would block
   PyMOL's event loop and freeze the viewer -- SETUP-01, PITFALL P1).

   TWO TABS (05-06, SETUP-11): the dialog is a QTabWidget -- 'Setup'
   wraps the existing 7-field form + stretch + 7-button row (every
   attribute preserved), and 'Game status' hosts the GameTab from
   game_window.py (info box, timer label + 1 Hz tick, required label,
   cancellable countdown, connected Hint button since 05-08).
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
from pymol import cmd   # 04-11 (Decision 17): the cleanup handler is the
                        # only handler that needs raw cmd; module-level is
                        # legal in the Qt tier.
import random           # 04-12 (Decision 4): the fresh-per-export seed
                        # policy; stdlib, harmless. Sibling imports stay
                        # lazy inside functions.

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


def export_game(state, seed, candidates, ligand_content, path):
    """Generate the full game for a validated setup and write the
    shareable versioned game file. Returns the success summary line.

    state must already be build_state/validate_state output.
    candidates/ligand_content: the uploaded-session pair, or
    None/None for the bundled-manifest flow. The viewer scene is
    NEVER touched here (no cleanup, no materialize, no wizard --
    spec.md:24, "Only generate ... WITHOUT starting play").
    Side effect (documented): engine.new_game replaces the engine's
    module-level runtime state (_payload/_game/_registry) -- benign.
    Module-level and construct-free so headless smokes drive it T1a
    (research P-hedge); the dialog wrapper is _export_game_to below.
    """
    from . import engine, game_file, paths, persistence
    payload, _rows = engine.new_game(state, seed,
                                     candidates=candidates,
                                     ligand_content=ligand_content)
    import time as _time
    data = game_file.make_game_data(
        state, payload,
        ligand_files=(game_file.encode_ligand_files(ligand_content)
                      if ligand_content else None),
        created_at=_time.strftime('%Y-%m-%dT%H:%M:%S'))
    if not path.endswith('.aamatch.json'):
        path = path + '.aamatch.json'
    persistence.save_container(paths.to_windows_path(path), 'game', data)
    levels = len(payload.get('levels', []))
    mols = sum(len(l.get('molecules', [])) for l in payload.get('levels', []))
    mode = state.get('source_mode')
    return ('Game exported to %s (seed %d, %d level(s), %d molecule '
            'placements, source: %s)' % (path, int(seed), levels, mols, mode))


class SetupWindow(QtWidgets.QDialog):
    """The modeless two-tab window (SETUP-01 + SETUP-11 shell, 05-06).

    'Setup' tab: window lifecycle (04-05) + the full form (04-07,
    SETUP-02..06 widget side): a 2-page molecule-source selector (demo
    dropdown / upload browse+path label), molecules + difficulty
    spinboxes whose ranges mirror the frozen setup_state clamp
    constants exactly (collect -> validate is lossless), a 3-way
    interaction-mode radio group with a context label, and 7
    checkboxes in canonical INTERACTION_TYPES order -- every widget
    tooltipped. The 7-button row sits below the form on the Setup page
    (spec.md:21), created IN SPEC ORDER and connected by the handler
    plans (04-09..04-13). collect_state/apply_state round-trip a
    validate_state-normalized dict losslessly.

    'Game status' tab: self.game_tab, the GameTab from game_window.py
    (05-06, SETUP-11 shell) -- the read-only rolling info box, the
    elapsed-timer label + 1 Hz live-anchor tick with modal-pause
    rebase, the required-interactions label, the cancellable 3-2-1
    countdown, and the Hint button (connected by 05-08, its handler
    plan). spec.md:33: the Game
    status tab of the SAME window -- never a second dialog.
    """

    def __init__(self):
        # NO parent -- a modeless top-level window must not be owned by
        # another widget (parenting would pin its lifecycle/geometry).
        super(SetupWindow, self).__init__()
        self.setWindowTitle('AA-match Setup')
        self.setMinimumWidth(420)   # the v1 dialog precedent

        # 05-06 (SETUP-11): lazy relative sibling import at the TOP of
        # __init__ (module-identity law, contract 4 -- never a
        # module-level sibling import in the Qt tier).
        from . import game_window

        top = QtWidgets.QVBoxLayout(self)

        # The window is a two-tab QTabWidget (spec.md:33 -- the Game
        # status tab of the SAME window): the 'Setup' page wraps the
        # EXISTING form area + stretch + 7-button row (every attribute
        # and label survives -- SMOKE-11 PART B is parentage-blind),
        # and the 'Game status' page hosts the GameTab
        # (game_window.py). The 7 setup buttons STAY on the Setup page
        # (spec.md:21 -- the button row at the bottom of the popup;
        # game-lifecycle buttons live on the Game tab).
        setup_page = QtWidgets.QWidget(self)
        setup_box = QtWidgets.QVBoxLayout(setup_page)

        # (a) form area -- the 7-field form packs vertically into this
        # stable layout slot (button row stays pinned below).
        self.form_area = QtWidgets.QWidget(setup_page)
        self.form_area.setLayout(QtWidgets.QVBoxLayout())
        setup_box.addWidget(self.form_area)

        # Session-only ingested-upload slot: the Browse handler (04-10)
        # populates it with {'path': ..., 'sha256': ...}; collect_state
        # reads it. Never restored from setup files (uploads are not
        # stored there -- the sha256 lets Load warn when it moved).
        self._uploaded = None

        # Start-after-Generate slot (04-12 / Decision 4): the dialog
        # remembers the exported {'setup', 'seed', 'candidates',
        # 'ligand_content'} tuple so 04-13's Start replays the SHARED
        # game when the form still matches; None until the first export.
        self._last_export = None

        # Bulk-populate guard (prior-art shape): True while apply_state
        # runs so future valueChanged hooks (none yet) can early-return
        # instead of cascading recompute.
        self._loading = False

        # SETUP-02..06 widget side: source selector, spinboxes, mode
        # group, interaction checkboxes -- in spec order.
        self._build_source_selector()
        self._build_spinboxes()
        self._build_mode_group()
        self._build_interactions()

        # (b) stretch -- keeps the button row pinned to the bottom.
        setup_box.addStretch(1)

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
        setup_box.addLayout(row)

        # The two tabs (SETUP-11, plan 05-06): 'Setup' holds everything
        # built above (the buttons stay here per spec.md:21); 'Game
        # status' hosts the GameTab shell -- info box, timer label,
        # required label, cancellable countdown, connected Hint --
        # from game_window.py (spec.md:33: the same window, not a
        # second dialog).
        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.addTab(setup_page, 'Setup')
        self.game_tab = game_window.GameTab(self)
        self.tabs.addTab(self.game_tab, 'Game status')
        top.addWidget(self.tabs)

        # 04-09 SETUP-07 connections: Reset, Randomize, Save Setup,
        # Load Setup; 04-10 connects the upload Browse button; 04-11
        # SETUP-09 connects Cleanup; 04-12 SETUP-08 connects Generate
        # and export; 04-13 SETUP-10 connects Start (all 7 wired).
        self.btn_reset.clicked.connect(self._on_reset)
        self.btn_randomize.clicked.connect(self._on_randomize)
        self.btn_save_setup.clicked.connect(self._on_save_setup)
        self.btn_load_setup.clicked.connect(self._on_load_setup)
        self.btn_browse.clicked.connect(self._on_browse_upload)
        self.btn_cleanup.clicked.connect(self._on_cleanup)
        self.btn_generate_export.clicked.connect(self._on_generate_export)
        self.btn_start.clicked.connect(self._on_start)

    # ---- the 7-field form (SETUP-02..06 widget side, 04-07) ----

    def _build_source_selector(self):
        """Molecule-source group: 2 radios + a 2-page QStackedWidget.

        Mirrors the prior-art stacked-pages pattern: the non-active
        page's values stay INTACT underneath (source_mode, demo_set_id
        and upload are three coexisting state fields).
        """
        group = QtWidgets.QGroupBox('Molecule source', self)
        vbox = QtWidgets.QVBoxLayout(group)

        radios = QtWidgets.QHBoxLayout()
        self.src_demo = QtWidgets.QRadioButton('Bundled demo set', group)
        self.src_demo.setToolTip(
            'Generate from a demo set bundled with AA-match.')
        self.src_upload = QtWidgets.QRadioButton(
            'Upload my molecules...', group)
        self.src_upload.setToolTip(
            'Generate from your own SDF or MOL2 file (one file; '
            'multi-record files give several molecules).')
        radios.addWidget(self.src_demo)
        radios.addWidget(self.src_upload)
        vbox.addLayout(radios)

        self.source_stack = QtWidgets.QStackedWidget(group)

        # Page 0 -- demo page: dropdown of bundled sets + a note label
        # for placeholder/warning text (initially empty).
        demo_page = QtWidgets.QWidget(self.source_stack)
        demo_layout = QtWidgets.QVBoxLayout(demo_page)
        self.demo_combo = QtWidgets.QComboBox(demo_page)
        self.demo_combo.setToolTip(
            'Which bundled demo set to generate from.')
        demo_layout.addWidget(self.demo_combo)
        self.source_note = QtWidgets.QLabel('', demo_page)
        self.source_note.setWordWrap(True)
        demo_layout.addWidget(self.source_note)
        self.source_stack.addWidget(demo_page)

        # Page 1 -- upload page: Browse button + read-only path label
        # (btn_browse connects to _on_browse_upload in __init__).
        upload_page = QtWidgets.QWidget(self.source_stack)
        upload_layout = QtWidgets.QHBoxLayout(upload_page)
        self.btn_browse = QtWidgets.QPushButton('Browse...', upload_page)
        self.btn_browse.setToolTip(
            'Pick an SDF or MOL2 molecule file (single file; a '
            'multi-record file provides several molecules).')
        upload_layout.addWidget(self.btn_browse)
        self.upload_path_label = QtWidgets.QLabel('', upload_page)
        upload_layout.addWidget(self.upload_path_label, 1)
        self.source_stack.addWidget(upload_page)
        vbox.addWidget(self.source_stack)

        # Radio toggles switch the stack page (demo checked -> page 0,
        # upload checked -> page 1). toggled(bool) would map True -> 1
        # directly, i.e. BACKWARDS -- hence the explicit lambda.
        self.src_demo.toggled.connect(
            lambda checked: self.source_stack.setCurrentIndex(
                0 if checked else 1))
        self.src_demo.setChecked(True)

        self._populate_demo_sets()
        self.form_area.layout().addWidget(group)

    def _populate_demo_sets(self):
        """Fill the demo dropdown from the bundled MANIFEST.json.

        Reads exactly the way the engine's manifest flow reads
        (read_json_file over paths.package_data_path, then
        parse_manifest_dict); dropdown rows come from the pure
        setup_form.manifest_sets helper (set_id as userData, title as
        label, tier suffix). A failure to parse (e.g. a newer manifest
        version) degrades to a placeholder item plus a visible note --
        the window must never crash the menu action.
        """
        try:
            from . import manifest, paths
            from .persistence import read_json_file
            from . import setup_form
            payload = manifest.parse_manifest_dict(read_json_file(
                paths.package_data_path('data', 'MANIFEST.json')))
            for (set_id, title, tier) in setup_form.manifest_sets(payload):
                label = title or set_id
                if tier:
                    label = '%s (%s)' % (label, tier)
                self.demo_combo.addItem(label, set_id)
            self.demo_combo.setCurrentIndex(0)
        except Exception as e:
            self.demo_combo.clear()
            self.demo_combo.addItem('(no bundled sets)', '')
            self.source_note.setText(
                'Could not read the bundled demo list: %s' % e)

    # UI-only display labels for the canonical interaction enum strings
    # (the stored values stay the enum strings from
    # setup_state.INTERACTION_TYPES; iteration order is frozen there).
    _INTERACTION_LABELS = {
        'h_bond': 'Hydrogen bond',
        'salt_bridge': 'Salt bridge',
        'pi_stacking': 'Pi-stacking',
        'cation_pi': 'Cation-pi',
        'hydrophobic': 'Hydrophobic',
        'halogen': 'Halogen bond',
        'metal': 'Metal coordination',
    }
    # Per-type tooltips in game terms (spec UI standard: clear but
    # sufficient in-game explanation).
    _INTERACTION_TIPS = {
        'h_bond': 'Hydrogen bond: a donor hydrogen (-OH or -NH) '
                  'facing an acceptor oxygen or nitrogen on the other '
                  'molecule.',
        'salt_bridge': 'Salt bridge: an opposite-charge pair held '
                       'together (a positive group on one molecule, a '
                       'negative group on the other).',
        'pi_stacking': 'Pi-stacking: two aromatic rings stacked '
                       'face-on or edge-on.',
        'cation_pi': 'Cation-pi: a positively charged group resting '
                     'on the face of an aromatic ring.',
        'hydrophobic': 'Hydrophobic: non-polar carbons of both '
                       'molecules clustered into the same greasy '
                       'patch.',
        'halogen': 'Halogen bond: a Cl/Br/I on the molecule accepting '
                   'from a donor on the amino acid.',
        'metal': 'Metal coordination: a metal ion bound by two or '
                 'more donor atoms.',
    }
    # Context-label strings restating the current interaction mode's
    # meaning under the radios (research mode_widget_design).
    _MODE_CONTEXT = {
        'exclusive': 'The game accepts ANY of the checked interactions',
        'block_exclusive': 'The player must form EXACTLY the checked '
                           'interactions',
        'unset': 'The game randomizes the required set from the '
                 'checked types (hydrophobic excluded from random '
                 'picks).',
    }

    def _build_spinboxes(self):
        """SETUP-04/05 spinboxes with ranges from the frozen constants.

        The ranges are imported from setup_state (never numeric
        literals): locking the spinbox range to the pure layer's clamp
        range is what makes collect -> validate_state lossless for
        these fields (form_field_specs ruling).
        """
        from . import setup_state
        group = QtWidgets.QGroupBox('Game size', self)
        form = QtWidgets.QFormLayout(group)

        self.molecules_spin = QtWidgets.QSpinBox(group)
        self.molecules_spin.setRange(setup_state.MOLECULES_MIN,
                                     setup_state.MOLECULES_CAP)
        self.molecules_spin.setValue(setup_state.MOLECULES_DEFAULT)
        self.molecules_spin.setToolTip(
            'How many small molecules each level contains (default 2; '
            'range mirrors the frozen 1..10 bounds).')
        form.addRow('Small molecules per level', self.molecules_spin)

        self.difficulty_spin = QtWidgets.QSpinBox(group)
        self.difficulty_spin.setRange(setup_state.DIFFICULTY_MIN,
                                      setup_state.DIFFICULTY_CAP)
        self.difficulty_spin.setValue(setup_state.DIFFICULTY_DEFAULT)
        self.difficulty_spin.setToolTip(
            'How many difficulty levels per game (each level is '
            'harder: bigger grid, more required interactions).')
        form.addRow('Difficulty levels', self.difficulty_spin)

        self.form_area.layout().addWidget(group)

    def _build_mode_group(self):
        """SETUP-06 mode group: 3 radios + a context label.

        Radio exclusivity is automatic within the group parent (no
        QButtonGroup needed). The context label restates the current
        mode's meaning and updates on every toggle. Default = the
        frozen DEFAULTS interaction_mode ('unset').
        """
        group = QtWidgets.QGroupBox('Required interactions', self)
        vbox = QtWidgets.QVBoxLayout(group)

        self.mode_exclusive = QtWidgets.QRadioButton(
            'Exclusive (any allowed)', group)
        self.mode_exclusive.setToolTip(
            'The game accepts ANY of the checked interactions.')
        self.mode_block = QtWidgets.QRadioButton(
            'Block-exclusive (checked set)', group)
        self.mode_block.setToolTip(
            'The player must form EXACTLY the checked interactions.')
        self.mode_unset = QtWidgets.QRadioButton(
            'Unset (random)', group)
        self.mode_unset.setToolTip(
            'The game randomizes the required set from the checked '
            'types (hydrophobic is excluded from random picks).')
        for radio in (self.mode_exclusive, self.mode_block,
                      self.mode_unset):
            radio.toggled.connect(self._on_mode_toggled)
            vbox.addWidget(radio)

        self.mode_context_label = QtWidgets.QLabel('', group)
        self.mode_context_label.setWordWrap(True)
        vbox.addWidget(self.mode_context_label)

        # Default: the frozen DEFAULTS interaction_mode 'unset'.
        self.mode_unset.setChecked(True)
        self._on_mode_toggled()   # set the initial context text
        self.form_area.layout().addWidget(group)

    def _current_mode(self):
        """The enum string of the checked mode radio."""
        if self.mode_exclusive.isChecked():
            return 'exclusive'
        if self.mode_block.isChecked():
            return 'block_exclusive'
        return 'unset'

    def _on_mode_toggled(self, *args):
        """Restate the current mode's meaning under the radios."""
        self.mode_context_label.setText(
            self._MODE_CONTEXT[self._current_mode()])

    def _build_interactions(self):
        """SETUP-06 checkboxes: 7 in canonical INTERACTION_TYPES order.

        Checkboxes are ENABLED in every mode on purpose: in unset
        mode a non-empty allowed list narrows the sampling vocabulary,
        so disabling them would silently discard the user's
        restriction at collect time. Iterating the frozen canonical
        list keeps collect order == validate_state order.
        """
        from .setup_state import INTERACTION_TYPES
        group = QtWidgets.QGroupBox('Allowed interactions', self)
        vbox = QtWidgets.QVBoxLayout(group)
        self.interaction_checks = []
        for itype in INTERACTION_TYPES:
            cb = QtWidgets.QCheckBox(
                self._INTERACTION_LABELS[itype], group)
            cb.setToolTip(self._INTERACTION_TIPS[itype])
            vbox.addWidget(cb)
            self.interaction_checks.append((itype, cb))
        self.form_area.layout().addWidget(group)

    # ---- collect/apply: the form as a view of the 7-field model ----

    def collect_state(self):
        """Snapshot the form into the plain 7-field setup dict.

        Returns EXACTLY the validate_state schema keys; validation and
        clamping stay with the pure layer (no widget-side
        re-validation). The upload entry is read from the session-only
        ingested slot populated by 04-10's Browse handler.
        """
        upload = None
        if self._uploaded:
            upload = {'path': self._uploaded['path'],
                      'sha256': self._uploaded['sha256']}
        return {
            'source_mode': 'upload' if self.src_upload.isChecked()
            else 'demo',
            'demo_set_id': str(self.demo_combo.currentData() or ''),
            'upload': upload,
            'molecules_per_level': int(self.molecules_spin.value()),
            'difficulty_levels': int(self.difficulty_spin.value()),
            'interaction_mode': self._current_mode(),
            'allowed_interactions': [
                t for (t, cb) in self.interaction_checks
                if cb.isChecked()],
        }

    def apply_state(self, state):
        """Repopulate every widget from a setup dict (Reset/Load/init).

        Missing-key tolerance on every field via .get with frozen
        defaults. The _loading guard is set for the whole populate so
        future valueChanged hooks (none yet) can early-return instead
        of cascading recompute. The upload label shows the SAVED path
        for context only -- the session-only _uploaded slot is NOT
        restored here (uploads are not stored in setup files).
        """
        if not isinstance(state, dict):
            state = {}
        from . import setup_state
        self._loading = True
        try:
            if state.get('source_mode', setup_state.DEFAULTS['source_mode']) \
                    == 'upload':
                self.src_upload.setChecked(True)
            else:
                self.src_demo.setChecked(True)

            set_id = str(state.get('demo_set_id') or '')
            if set_id:
                idx = self.demo_combo.findData(set_id)
                if idx >= 0:
                    self.demo_combo.setCurrentIndex(idx)
                else:
                    # Fallback to the first row, with a visible note --
                    # never a crash on a stale/named set id.
                    self.demo_combo.setCurrentIndex(0)
                    self.source_note.setText(
                        'set %r is not in the bundled list' % set_id)
            else:
                # Empty id = 'no restriction': no combo item selected
                # (the dropdown holds named sets only; -1 = empty
                # selection, which collect maps back to '').
                self.demo_combo.setCurrentIndex(-1)

            try:
                self.molecules_spin.setValue(int(state.get(
                    'molecules_per_level',
                    setup_state.DEFAULTS['molecules_per_level'])))
            except (TypeError, ValueError):
                self.molecules_spin.setValue(
                    setup_state.DEFAULTS['molecules_per_level'])
            try:
                self.difficulty_spin.setValue(int(state.get(
                    'difficulty_levels',
                    setup_state.DEFAULTS['difficulty_levels'])))
            except (TypeError, ValueError):
                self.difficulty_spin.setValue(
                    setup_state.DEFAULTS['difficulty_levels'])

            mode = state.get('interaction_mode',
                             setup_state.DEFAULTS['interaction_mode'])
            if mode == 'exclusive':
                self.mode_exclusive.setChecked(True)
            elif mode == 'block_exclusive':
                self.mode_block.setChecked(True)
            else:
                self.mode_unset.setChecked(True)

            allowed = state.get('allowed_interactions') or []
            for (t, cb) in self.interaction_checks:
                cb.setChecked(t in allowed)

            upload = state.get('upload')
            if isinstance(upload, dict) and upload.get('path'):
                # LABELS only -- the molecules are session-only and are
                # never re-ingested from a file (upload_ready_for then
                # reports False until Browse re-ingests). The tooltip
                # carries the FILE sha256 so a moved/changed file is
                # visible to the user (a file-moved warning at Start is
                # the pure build_state pre-check's job via
                # upload_ready).
                path = str(upload['path'])
                self.upload_path_label.setText(path)
                tip = str(path)
                if upload.get('sha256'):
                    tip = '%s\nsha256: %s' % (tip, str(upload['sha256']))
                self.upload_path_label.setToolTip(tip)
            else:
                self.upload_path_label.setText('')
                self.upload_path_label.setToolTip('')
        finally:
            self._loading = False

    def upload_ready_for(self, form_values):
        """True iff this window can actually start/export ``form_values``.

        False only when source_mode is 'upload' AND the form's upload
        block does NOT match this session's ingested slot
        (path AND FILE sha256 both compared): a setup-file Load
        restores path/sha256 LABELS only -- the molecules are
        session-only, so a not-re-ingested upload configuration is not
        startable. Handlers (04-12 export, 04-13 start) pass
        ``upload_ready=self.upload_ready_for(self.collect_state())``
        into the pure setup_form.build_state, whose fatal pre-check
        then refuses BEFORE any scene-touching call.
        """
        if form_values.get('source_mode') != 'upload':
            return True
        form_upload = form_values.get('upload') or {}
        return (self._uploaded is not None
                and self._uploaded['path'] == form_upload.get('path')
                and self._uploaded['sha256'] == form_upload.get('sha256'))

    # ---- SETUP-07 button handlers (04-09): the _guard contract ----

    def _guard(self, fn):
        """Run fn() mapping the ValueError family + OSError to a modal
        warning box (modal CHILD -- allowed, PITFALL 4). str(e) is shown
        verbatim: every house refusal already names its cause. Unexpected
        exceptions PROPAGATE (bug surfacing, never a silent swallow --
        wizard.py:423-433 precedent)."""
        try:
            return fn()
        except (ValueError, OSError) as e:
            QtWidgets.QMessageBox.warning(self, 'AA-match', str(e))
            return None

    def _on_reset(self):
        """Reset button: restore the frozen DEFAULTS (via _guard)."""
        self._guard(self._reset_impl)

    def _reset_impl(self):
        """Apply a DEEP COPY of setup_state.DEFAULTS to every widget.

        Never alias the module dict into mutable widget state (the
        allowed_interactions list is mutable; research SETUP-07 seam,
        prior-art gui_setup.py:315). Non-modal: headless smokes drive
        this method directly.
        """
        import copy
        from . import setup_state
        self.apply_state(copy.deepcopy(setup_state.DEFAULTS))

    def _on_randomize(self):
        """Randomize button: random USABLE configuration (via _guard)."""
        self._guard(self._randomize_impl)

    def _randomize_impl(self):
        """Randomize via setup_form.usable_randomized_state.

        randomize_state synthesizes demo_set_id 'demo-%04x' which matches
        NO manifest set (the 04-02 trap) -- usable_randomized_state
        overwrites it with the CURRENT dropdown selection (Decision 5:
        preserve the user's chosen set; '' when the placeholder/no
        selection = all sets). apply_state reflects source_mode 'demo' +
        upload None back into the widgets automatically. Non-modal.
        """
        from . import setup_form
        current = str(self.demo_combo.currentData() or '')
        state = setup_form.usable_randomized_state(demo_set_id=current)
        self.apply_state(state)

    def _on_save_setup(self):
        """Save Setup button: pick a path, save via _guard, confirm.

        The success box lives HERE (the dialog wrapper), not in the
        impl: _save_setup_to must stay modal-free so headless smokes
        can drive it (a modal QMessageBox BLOCKS under platform=
        offscreen -- the 04-09 smoke-99 probe receipt).
        """
        path, _selected_filter = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save AA-match Setup', '',
            'AA-match Setup (*.aam.setup.json);;All Files (*)')
        if path:
            saved = self._guard(lambda: self._save_setup_to(path))
            if saved is not None:
                QtWidgets.QMessageBox.information(
                    self, 'AA-match', 'Setup saved to %s' % saved)

    def _save_setup_to(self, path):
        """Write collect_state() as a versioned 'setup' container.

        Extension auto-append (Decision 2, prior-art gui_setup.py:651-
        652); the disk path routes through paths.to_windows_path (the
        AGENTS path law -- QFileDialog Windows paths pass through
        unchanged by design). persistence.save_setup_file validates
        BEFORE write; OSError (disk/permission) propagates to _guard,
        which catches it. NON-MODAL (no boxes) and returns the final
        path so the wrapper can confirm; headless smokes drive this
        method directly.
        """
        from . import persistence, paths
        if not path.endswith('.aam.setup.json'):
            path = path + '.aam.setup.json'
        persistence.save_setup_file(paths.to_windows_path(path),
                                    self.collect_state())
        return path

    def _on_load_setup(self):
        """Load Setup button: pick a path, load via _guard, confirm.

        Same modal-free-impl rule as _on_save_setup (the smoke-99
        receipt).
        """
        path, _selected_filter = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Load AA-match Setup', '',
            'AA-match Setup (*.aam.setup.json);;All Files (*)')
        if path:
            loaded = self._guard(lambda: self._load_setup_from(path))
            if loaded is not None:
                QtWidgets.QMessageBox.information(
                    self, 'AA-match', 'Setup loaded from %s' % loaded)

    def _load_setup_from(self, path):
        """Read a versioned setup container and apply it to the form.

        persistence.load_setup_file validates AGAIN on load; the 4
        FormatError refusal classes (foreign / newer / misfiled /
        unparseable -- all ValueError subclasses) arrive with clear
        user-facing messages that _guard shows verbatim. OSError
        (missing file) is likewise caught by _guard. NON-MODAL (no
        boxes); returns the path so the wrapper can confirm.

        CAVEAT: a loaded setup with source_mode 'upload' restores the
        path/sha256 LABELS only (apply_state's contract) -- the
        molecules themselves are session-only and are NOT re-ingested
        here; Start/Export refuse via build_state's upload_ready
        pre-check until re-ingested (04-10 wires that).
        """
        from . import persistence, paths
        state = persistence.load_setup_file(paths.to_windows_path(path))
        self.apply_state(state)
        return path

    # ---- SETUP-03 upload ingestion (04-10) ----

    def _on_browse_upload(self):
        """Browse button: pick ONE molecule file, ingest via _guard.

        Single-select ``getOpenFileName`` (Decision 9): the frozen
        setup upload field is ``None | {'path', 'sha256'}`` -- a
        multi-file pick would be a schema change (version-bump event).
        One multi-record SDF still delivers several molecules
        (spec.md:14). The picker is a modal CHILD (allowed, PITFALL
        4); the ingest runs through _guard so every pure/cmd-tier
        refusal (format whitelist, cap, reader guards -- the MOL2
        multi-segment refusal included) surfaces verbatim. No success
        box: the widget reflection (upload page + path label) IS the
        confirmation.
        """
        path, _selected_filter = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Upload molecule file', '',
            'Molecule files (*.sdf *.mol2);;All Files (*)')
        if path:
            self._guard(lambda: self._ingest_upload(path))

    def _ingest_upload(self, path):
        """Read/split/cap/extract an uploaded molecule file. NON-MODAL.

        Returns the ingested record count (int); headless smokes drive
        this method directly (the smoke-99 probe receipt: impls never
        own boxes). Pipeline, all proven helpers in order: pure
        read_upload_source (extension whitelist + utf-8 + FILE sha256,
        Decision 19) -> pure split_sdf_records / split_mol2_segments by
        fmt -> pure check_upload_supply (cap 50 + degenerate refusals
        naming the basename) -> cmd-tier prepare_uploaded_set (the
        04-08 per-record temp discipline; delete-in-finally, scene
        residue asserted per record, so the scene stays clean).

        The result lands in the session-only slot self._uploaded with
        the rows + ligand_content engine.new_game already accepts plus
        the path/FILE-sha256/fmt labels; a NEW upload REPLACES the
         slot (single slot v1). The form reflects upload mode: source
         radio switches to the upload page and the path label shows the
         file path with the record count on its OWN second line
         ('%s\n(%d molecule record(s))' -- a long path on one line
         clipped the count out of view, the 04-15 checkpoint-B fix;
         the tooltip still carries the full path) so collect_state
         then reports upload={'path','sha256'}.
        EXT-04 depth is NOT built -- the fail-closed minimum only
        (research upload_pipeline boundary); every refusal is a
        ValueError/OSError that _guard shows verbatim.
        """
        import os
        from . import game_file, paths, upload
        text, sha256_hex, fmt = game_file.read_upload_source(
            paths.to_windows_path(path))
        if fmt == 'sdf':
            records = game_file.split_sdf_records(text)
        else:
            records = game_file.split_mol2_segments(text)
        game_file.check_upload_supply(records, fmt, os.path.basename(path))
        rows, content = upload.prepare_uploaded_set(records, fmt)
        self._uploaded = {'rows': rows, 'content': content, 'path': path,
                          'sha256': sha256_hex, 'fmt': fmt}
        self.src_upload.setChecked(True)
        self.upload_path_label.setText(
            '%s\n(%d molecule record(s))' % (path, len(rows)))
        self.upload_path_label.setToolTip(path)
        return len(rows)

    # ---- SETUP-09 cleanup (04-11) ----

    def _pop_game_wizard(self):
        """Pop a GameWizard iff it is top-of-stack; returns popped-bool.

        The 04-11 isinstance-pop pattern, deletion excluded: canonical
        cmd.set_wizard() None-pop -- the popped wizard's own cleanup
        runs, the prior wizard (if any) auto-resumes, and a USER
        wizard is never popped. Shared by _cleanup_now (where the
        prefix-only deletion follows -- behavior byte-identical to the
        04-11 inline form) and by _start_impl, where the pop happens
        BEFORE the deferred prepare (pitfall P-3: the old wizard's slot
        map points at objects start_game's cleanup-first step deletes,
        so clicks during the countdown must never reach it) and
        start_game's own cleanup-first law still does the deletion.
        """
        from . import wizard
        prior = cmd.get_wizard()
        if isinstance(prior, wizard.GameWizard):
            cmd.set_wizard()
            return True
        return False

    def _cleanup_now(self):
        """Cleanup WITHOUT any dialog; returns the deleted-object count.

        Pops a GameWizard FIRST via _pop_game_wizard (canonical
        None-pop, user wizards untouched), then the prefix-only
        deletion (placement.cleanup_game_objects): user molecules can
        never match the reserved _aam_ prefix.

        Adopted-ligand bookkeeping (placement.py:61-63 defers it here):
        ZERO v1 workload -- v1 never adopts user objects (fresh _aam_*
        names only), so prefix deletion IS the complete original-scene
        restore. Recorded reading; no machinery."""
        from . import placement
        self._pop_game_wizard()
        result = placement.cleanup_game_objects()
        return result['deleted']

    def _on_cleanup(self):
        """Cleanup model button (SETUP-09): cancel-first + pop-cleanup.

        Cancels any pending countdown FIRST (pitfall P-2: a countdown
        surviving the cleanup would fire a stale GO whose wizard
        registry references the very objects this cleanup deletes).
        Then the pop-first cleanup via _guard. deleted == 0 is a LEGAL
        no-op (nothing on the scene) -- the plan brief: the count is
        always surfaced, zero included; only None (a _guard-caught
        refusal) means no box.
        """
        self.game_tab.cancel_pending_start()
        deleted = self._guard(self._cleanup_now)
        if deleted is not None:
            QtWidgets.QMessageBox.information(
                self, 'AA-match',
                'Removed %d game object(s). The scene is back to your '
                'original objects.' % deleted)

    # ---- SETUP-08 generate-and-export (04-12) ----

    def _on_generate_export(self):
        """Generate and export button: pick a path, export via _guard.

        Same modal-free-impl rule as _on_save_setup (the smoke-99
        receipt): _export_game_to is NON-MODAL and returns the summary
        line; the SUCCESS box lives HERE in the wrapper (a static/modal
        QMessageBox BLOCKS under platform=offscreen, so impls never own
        boxes). The export never touches the scene (spec.md:24: only
        generate, WITHOUT starting play -- no cleanup, no materialize,
        no wizard).
        """
        path, _selected_filter = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Export AA-match Game', 'game.aamatch.json',
            'AA-match Game (*.aamatch.json);;All Files (*)')
        if path:
            summary = self._guard(lambda: self._export_game_to(path))
            if summary is not None:
                QtWidgets.QMessageBox.information(
                    self, 'AA-match', summary)

    def _export_game_to(self, path):
        """Build the state, fresh-seed, export, store _last_export.
        NON-MODAL.

        Returns the success summary line (the wrapper shows it); every
        refusal is a ValueError/OSError that _guard surfaces verbatim.
        The seed is FRESH RANDOM per export (Decision 4:
        random.randint(0, 2**31-1), matching the generator's sub-seed
        domain). The upload flow reuses the session-ingested
        rows + ligand_content (bundled molecules are package-relative
        refs, never embedded); build_state's upload_ready pre-check
        already refused upload mode without an ingested file, so
        self._uploaded is non-None on the upload branch. After a
        successful export the exported tuple is stored as
        self._last_export for 04-13's Start-after-Generate.
        Side effect (documented): engine.new_game replaces the engine's
        module-level runtime state (_payload/_game/_registry) -- benign.
        Headless smokes drive this method directly.
        """
        from . import setup_form
        form = self.collect_state()
        form['upload_ready'] = self.upload_ready_for(form)
        known_ids = tuple(str(self.demo_combo.itemData(i))
                          for i in range(self.demo_combo.count()))
        state = setup_form.build_state(form, known_set_ids=known_ids)
        seed = random.randint(0, 2 ** 31 - 1)
        if state['source_mode'] == 'upload':
            up = self._uploaded
            candidates, content = up['rows'], up['content']
        else:
            candidates, content = None, None
        summary = export_game(state, seed, candidates, content, path)
        self._last_export = {'setup': state, 'seed': seed,
                             'candidates': candidates,
                             'ligand_content': content}
        return summary

    # ---- SETUP-10 start (04-13) ----

    def _on_start(self):
        """Start the configured game (SETUP-10). THIN: build_state
        pre-checks + seed policy, then _start_impl's deferred sequence
        (pop -> prepare unactivated -> tab switch -> countdown, SETUP-11,
        05-09). The countdown log + the wizard panel after GO are the
        success feedback (no dialog). Import and later game-lifecycle
        buttons land in later plans."""
        self._guard(self._start_impl)

    def _start_impl(self):
        """collect -> build_state -> seed policy -> the DEFERRED start
        sequence. NON-MODAL; returns the prepared (not yet activated)
        GameWizard -- the smoke's assertion handle.

        ORDERING LAW (unchanged from 04-13): setup_form.build_state
        raising is CAUGHT BY _guard and the scene is then UNTOUCHED --
        the pre-check's whole point (start_game cleans first, so a
        post-cleanup refusal would already have deleted the prior game
        objects; build_state's three fatal refusals fire BEFORE
        anything scene-touching runs). Upload mode without matching
        session content refuses inside build_state (upload_ready
        False); upload mode WITH it reuses the session rows +
        ligand_content (the synthetic upload keys cannot be
        materialized from the bundled manifest). Seed policy (Decision
        4): when self._last_export exists and its stored setup EQUALS
        the freshly built state (dict equality -- both sides are
        validate_state-normalized), the whole exported tuple (seed,
        candidates, ligand_content) is reused, so Start-after-Generate
        replays the SHARED game; otherwise a fresh random seed is drawn
        and candidates/content come from the CURRENT form's source
        mode. NO success dialog (04-13 decision): the materialized
        scene, the countdown log, the wizard panel after GO and the
        gamestart status print ARE the feedback -- a Start that opened
        a modal would be noise. Every refusal is a ValueError/
        OSError that _guard surfaces verbatim.

        DEFERRED SEQUENCE (05-09, SETUP-11; the WINDOW is the
        sequencer -- the cmd tier stays Qt-free and never learns about
        tabs, research Q2 answer (c)):
          1. _pop_game_wizard() -- the window pops the PRIOR GameWizard
             itself BEFORE prepare (pitfall P-3: its slot map points at
             objects start_game's cleanup-first step deletes, so clicks
             during the countdown must never reach it; the 04-11
             isinstance-pop pattern, deletion excluded -- start_game's
             own cleanup still does the deleting). start_game's
             internal conditional-replace stays untouched for direct
             callers (SMOKE-08's ORDER-LAW teeth).
          2. start_game(..., activate=False) -- prepare ONLY: the scene
             is built, the wizard constructed but NOT pushed (P-1: the
             countdown window is wizard-free).
          3. tabs.setCurrentWidget(game_tab) -- the spec.md:33 'same
             window' switch to the Game status tab.
          4. game_tab.start_countdown(wiz) -- hands off to the
             cancellable 3-2-1 countdown; only its GO step pushes and
             anchors (gamestart.activate_game, Pattern 2).
        """
        from . import setup_form, gamestart
        form = self.collect_state()
        form['upload_ready'] = self.upload_ready_for(form)
        known_ids = tuple(str(self.demo_combo.itemData(i))
                          for i in range(self.demo_combo.count()))
        state = setup_form.build_state(form, known_set_ids=known_ids)
        last = self._last_export
        if last is not None and last['setup'] == state:
            seed = last['seed']
            candidates = last['candidates']
            ligand_content = last['ligand_content']
        else:
            seed = random.randint(0, 2 ** 31 - 1)
            if state['source_mode'] == 'upload':
                up = self._uploaded
                candidates = up['rows']
                ligand_content = up['content']
            else:
                candidates = None
                ligand_content = None
        self._pop_game_wizard()
        wiz = gamestart.start_game(setup=state, seed=seed,
                                   candidates=candidates,
                                   ligand_content=ligand_content,
                                   activate=False)
        self.tabs.setCurrentWidget(self.game_tab)
        self.game_tab.start_countdown(wiz)
        return wiz

    # NO closeEvent OVERRIDE -- on purpose: default close hides the
    # dialog, and the module-level _window singleton keeps the object
    # alive, so re-open via open_window() is reuse-and-raise. That is
    # SETUP-01's survive-minimize/re-open mechanism (the v1 codebase
    # has ZERO closeEvent overrides -- repo-wide grep receipt).

    # NOTE: module-level ``from pymol import cmd`` was added by 04-11
    # (Decision 17) -- the cleanup handler is the only handler that
    # needs raw cmd. QtCore/QtGui are part of the wrapper shim's unit
    # import and are kept for the handler plans.
