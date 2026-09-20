"""aamatch.wizard -- the GameWizard (plan 03-03, Phase 3).

Layer: CMD TIER. Module-level ``from pymol import cmd`` and
``from pymol.wizard import Wizard`` are LEGAL here; this module must
NEVER be added to ``PURE_MODULES`` in ``tests/test_purity.py`` (Gate D
still compiles it under the 3.6 syntax floor). NO Qt anywhere.

THE BINDING CONTRACTS:

1. THIN INPUT ADAPTER -- the engine is the brain
   (03-RESEARCH-wizard-interaction.md sec. 8, ARCHITECTURE Pattern 2).
   This class routes clicks/keys/panel buttons onto engine ops
   (confirm / reset_to_grid / place_aa) and renders the plain-data
   result as panel/prompt text. NO detection math, NO scoring, NO spec
   knowledge here; engine ops own game state.

2. PLAIN PICKLABLE DATA ONLY on self (RESEARCH sec. 2.3): session save
   pickles the whole wizard stack, so every GameWizard attribute is a
   plain dict/list/tuple/int/str/None -- NEVER a module reference,
   never a cmd clone (the base class holds self.cmd and its
   __getstate__ strips exactly that key; session restore rebinds it).
   The engine is imported RELATIVELY INSIDE the methods that need it
   (``from . import engine``) so this module behaves identically when
   imported as ``aamatch`` (smokes/plugin-path) and as
   ``pmg_tk.startup.aamatch`` (installed) -- AGENTS.md gate 5 holds by
   construction, and panel button codes are built by
   aamatch/wizard_text.py as ``cmd.get_wizard().method(...)`` strings
   (instance-relative, PParse'd at click time; no module name ever
   appears in a code string).

3. STACK-NATIVE LIFECYCLE (RESEARCH sec. 1.2/2.3, Wizard.cpp:263-284):
   activate() PUSHES via ``cmd.set_wizard(self)``; a prior wizard (if
   any) stays dormant beneath. Exit is the panel Done button's
   canonical ``cmd.set_wizard()`` (None): the C layer pops this wizard,
   runs THIS cleanup(), and the prior wizard AUTO-RESUMES as the new
   top of stack. NEVER the v1 saved-wizard pattern (deactivate
   re-installing a saved reference with replace=0): when a prior
   wizard exists that pattern pushes a DUPLICATE reference and leaks
   the game wizard buried beneath it (double-cleanup later).

4. msm SNAPSHOT ORDER LAW -- activate() runs cmd.set_wizard FIRST, the
   mouse_selection_mode snapshot SECOND, the defensive set-to-0 THIRD.
   Rationale (checker-traced): when replace=1 pops a prior GameWizard,
   that wizard's cleanup runs INSIDE set_wizard and restores the user's
   true msm value, so ONLY a post-push snapshot captures it. A
   snapshot-before-push records a stale defensive 0 on mid-game
   restart, the premature set-to-0 is then defeated by the popped
   cleanup's restore, and Done finally restores the stale 0 --
   clobbering the user's pre-game setting exactly in the scenario
   replace=1 exists for (PLAY-04). Stock msm default is 1
   (SettingInfo.h:449), NEVER assume 0: restore the SNAPSHOT.

5. MOVEMENT = BAKED WORLD-FRAME TRANSFORMS ONLY
   (03-RESEARCH-movement-spike.md verdict): cmd.translate(v, obj,
   state=1, camera=0) and cmd.rotate(axis, deg, selection=obj,
   camera=0, origin=C) bake STORED coordinates and leave the object
   matrix at identity. The detector reads stored coords; the screen
   renders the object matrix composed over stored coords. Maintaining
   the identity-matrix invariant after EVERY move (asserted, fail-
   closed) makes on-screen == stored == detected BY CONSTRUCTION (the
   PLAY-02 contract). NEVER the matrix-only object= keyword form of
   translate/rotate (detector-blind, spike-proven), NEVER
   placement.transform_baked / cmd.transform_object in game paths
   (they bake coords BUT record the applied matrix -- render semantics
   unverified), and NEVER the banned matrix calls (see placement.py's
   banned list). PROSE DISCIPLINE: do NOT write the tokens for the
   banned cmd calls anywhere in this file -- refer to them only as
   "the banned matrix calls", because tests/test_code_audit.py fails
   on ANY unwhitelisted mention of those tokens in aamatch/ sources.

6. NO HELPER VISUALS (PLAY-04): selection feedback is RECOLOR ONLY
   (an atom-property change, not geometry; extract_game_atoms never
   reads atom color -- geometry.py:134-138) plus panel/prompt TEXT via
   aamatch/wizard_text.py. No lines, dots, CGO, no cmd.indicate.
"""

import math

from pymol import cmd
from pymol.wizard import Wizard

from . import geometry, setup_state, wizard_core, wizard_text

_MATRIX_TOL = 1e-6    # identity-matrix invariant slack (SMOKE-06
                      # _is_identity pattern; float32-tight)
_IDENT_3X4 = (1.0, 0.0, 0.0, 0.0,
              0.0, 1.0, 0.0, 0.0,
              0.0, 0.0, 1.0, 0.0)

_KEY_NUDGES = {'w': (0.0, 1.0, 0.0), 's': (0.0, -1.0, 0.0),
               'q': (0.0, 0.0, -1.0), 'e': (0.0, 0.0, 1.0)}


class WizardError(ValueError):
    """A failed WIZARD op (house fail-closed style, peers with
    EngineError / PlacementError). The message NAMES the cause -- e.g.
    the object whose matrix failed the identity invariant."""


class GameWizard(Wizard):
    """The Phase-3 gameplay-loop wizard (PLAY-01..04).

    Holds ONLY plain picklable data (contract 2). __init__ performs NO
    cmd call -- instantiation must be side-effect-free headlessly;
    activate() does the live work. The attribute set:

    - ``_payload``        level-spec payload (plain data, spec truth)
    - ``_registry``       placement registry (object names + ids)
    - ``_level_index`` / ``_molecule_index``  ints
    - ``_slot_by_object`` {object_name: slot_id} reverse pick map
                          (RESEARCH sec. 5.3: ONE _aam_aa* object per
                          slot, so the click's object name alone
                          resolves slot identity)
    - ``_objects_by_slot`` the forward view of that map
    - ``_ligand_object``  the current molecule's ligand object name
    - ``_current_slot``   selected slot_id or None
    - ``_saved_msm``      mouse_selection_mode snapshot (None = not
                          taken yet; int once activate() ran)
    - ``_color_store``    {object_name: [(ID, color), ...]} PLAY-01
                          pre-recolor snapshots (lazy, wizard_core
                          bookkeeping)
    - ``_result``         last confirm result dict or None (06-05/D3:
                          Confirm NO LONGER stores a result -- the
                          debrief rides the ``_last_event`` marker; the
                          key stays for the text builders' .get path)
    - ``_error``          last visible error string or None
    - ``_event_seq``      int event sequence counter (06-05; makes
                          identical consecutive events distinct for the
                          status tab's poll diff)
    - ``_last_event``     last lifecycle event dict or None (06-05;
                          plain data -- every successful lifecycle op
                          stamps it via _set_event)
    - ``_game_over`` / ``_end_state``  op-time mirrors of the live
                          GameState's end fields (06-05; refreshed by
                          _sync_end_state after every advancing op --
                          the wizard ops are the ONLY mutation paths,
                          so the mirror drifts by construction never)
    """

    def __init__(self, payload, registry, level_index=0, molecule_index=0):
        Wizard.__init__(self)
        self._payload = payload
        self._registry = registry
        self._level_index = int(level_index)
        self._molecule_index = int(molecule_index)
        self._slot_by_object = wizard_core.build_slot_map(
            registry, self._molecule_index)
        self._objects_by_slot = dict(
            (slot_id, obj)
            for obj, slot_id in self._slot_by_object.items())
        self._ligand_object = \
            registry['molecules'][self._molecule_index]['ligand'][0]
        self._current_slot = None
        self._saved_msm = None
        self._color_store = {}
        self._result = None
        self._error = None
        # 06-05 lifecycle marker machinery (plain data, contract 2).
        self._event_seq = 0
        self._last_event = None
        self._game_over = False
        self._end_state = None

    def get_event_mask(self):
        """pick(1) | select(2) | key(4) | special(8) = 15.

        The base default is only pick+select (3); the keyboard channels
        (nudge keys, arrow specials) need the key/special bits
        (RESEARCH sec. 6 -- wizard-first dispatch).
        """
        return 15

    def activate(self, replace=0):
        """The enter sequence (RESEARCH sec. 7 rows 1-3). THE ORDER IS
        BINDING -- push BEFORE snapshot (contract 4):

        1. cmd.deselect() -- clear the active selection so clicks start
           clean (measurement.py:98 precedent).
        2. cmd.set_wizard(self, replace=replace) -- push; with
           replace=1 the top wizard is popped + cleaned first (gamestart
           computes replace conditionally: 1 only when the prior
           top-of-stack wizard is itself a GameWizard -- restart
           hygiene; else 0, a plain push over a user wizard or an empty
           stack that preserves stack-native auto-resume).
        3. Snapshot the user's mouse_selection_mode (post-push, so a
           popped GameWizard's cleanup has already restored the user's
           true value -- stock default is 1, NEVER assume 0).
        4. Defensive set to 0 (atomic single-atom mode like every
           built-in wizard -- single-atom picks read reliably).
        5. cmd.refresh_wizard().
        """
        cmd.deselect()
        cmd.set_wizard(self, replace=replace)
        self._saved_msm = int(cmd.get('mouse_selection_mode'))
        cmd.set('mouse_selection_mode', 0)
        cmd.refresh_wizard()

    def cleanup(self):
        """The PLAY-04 restore set (RESEARCH sec. 7). Idempotent:
        set-back, delete-if-exists, color-write are all naturally
        repeatable (cleanup runs on pop AND on replace).

        Order: guard a rebound/None self.cmd (session-restore case,
        dragging.py:72-74 pattern); restore msm to the SNAPSHOT (never
        a hard-coded 0); unpick + delete the pk1 pick buffer if
        present; deselect; restore EVERY recolored slot's colors, then
        clear the store.

        MUST NOT: delete game objects (_aam_* outlive the wizard --
        Cleanup-button semantics are Phase 4), touch user objects, or
        mutate engine state.
        """
        if self.cmd is None:
            return
        if self._saved_msm is not None:
            self.cmd.set('mouse_selection_mode', self._saved_msm)
        self.cmd.unpick()
        if 'pk1' in self.cmd.get_names('selections'):
            self.cmd.delete('pk1')
        self.cmd.deselect()
        for obj in wizard_core.snapshot_objects(self._color_store):
            self._restore_slot_colors(obj)
        self._color_store.clear()
        # self._current_slot and self._error stay -- harmless plain
        # data; _error remains for the record.

    def _atom_colors(self, obj):
        """[(int(ID), int(color)), ...] for ``obj`` -- the PLAY-01
        pre-recolor snapshot rows (color is a read/write atom property
        in the iterate/alter symbol table, editing.py:1448)."""
        rows = []
        cmd.iterate(obj, 'stored.append((ID, color))',
                    space={'stored': rows})
        return [(int(atom_id), int(color)) for (atom_id, color) in rows]

    def _restore_slot_colors(self, obj):
        """Write ``obj``'s snapshotted atom colors back (PLAY-01/04).

        Preferred: ONE cmd.alter over the {ID: color} map via the
        expression sandbox. Some builds may reject dict subscripting in
        the sandbox; fall back to a per-id loop (both house-legal;
        explicit space dict either way). Absent snapshot -> no-op.

        DISPLAY-STALENESS LAW (03-06 field bug, cumulative greening):
        cmd.alter updates the atom-color DATA without rebuilding the
        object's drawn lists, while cmd.color redraws immediately -- so
        in the GUI a restored object kept SHOWING the highlight color
        until some later op (e.g. Reset's per-object translate) forced
        a redraw, even though the data was exact (headless probes on
        the full multi-switch field sequence prove the data level).
        The restore therefore ALWAYS re-issues the object's display
        lists with the data-exact colors (scoped, never a global
        refresh).
        """
        m = wizard_core.color_map(self._color_store, obj)
        if m is None:
            return
        try:
            cmd.alter(obj, 'color=m[ID]', space={'m': m})
        except Exception:
            # expression-sandbox dict-subscripting fallback
            for atom_id, color in sorted(m.items()):
                cmd.alter('%s and id %d' % (obj, atom_id),
                          'color=%d' % (color,), space={})
        cmd.rebuild(obj)

    def do_select(self, name):
        """The ONLY pick entry in default 3-Button Viewing -- do_pick
        never fires in stock Viewing mode (RESEARCH sec. 1.3/5.1):
        SceneMouse builds the active selection and calls do_select
        with its NAME. Canonical do_select -> do_pick map
        (measurement.py:295-306 shape), PINNED sequence:

        1. cmd.unpick() -- drop the leftover pick marker.
        2. cmd.select('pk1', name) -- copy the pick into the pk1
           buffer while the user's selection still holds its atoms.
        3. cmd.deselect() -- clear the user's ACTIVE selection state
           (the named selection object itself survives untouched; the
           pick was already read from it via pk1).
        4. Delete ``name`` ONLY when transient (wizard_core guard:
           'sele', pk1..pk4, '_'-prefixed). RECORDED PLANNER DECISION:
           transient-only delete -- a user's NAMED selection is NEVER
           deleted (canonical always-delete was rejected as user-data
           loss, contrary to the project's restore discipline).
        5. self.do_pick(0).
        """
        cmd.unpick()
        cmd.select('pk1', name)
        cmd.deselect()
        if wizard_core.transient_selection(name):
            cmd.delete(name)
        self.do_pick(0)

    def do_pick(self, bondFlag):
        """Hygienic pk1 read -> slot identity (PLAY-01).

        Explicit space dict ALWAYS; uppercase ID; no round() in the
        expression (Pitfall-8 conformant). Reads (model, ID, alt,
        resv) as a uniform 4-tuple -- the AA click needs only the
        model (object name) for identity, but the full tuple keeps the
        discipline intact for ligand-side reads in later phases.

        The reverse map IS the filter: a click whose object is not a
        registered slot of the current molecule (ligand, user object,
        another molecule's AA) is a NO-OP (v1 game.py:169-171
        precedent; PLAY-03 first half).
        """
        rows = []
        cmd.iterate('pk1', 'stored.append((model, ID, alt, resv))',
                    space={'stored': rows})
        cmd.unpick()
        if not rows:
            return
        slot_id = self._slot_by_object.get(rows[0][0])
        if slot_id is None:
            return
        self._error = None
        self._select_slot(slot_id)

    def _select_slot(self, slot_id):
        """Switch selection to ``slot_id`` with recolor feedback
        (PLAY-01/03).

        Switch semantics: the OLD slot's colors are restored FIRST
        (via its snapshot -- the snapshot entry is KEPT so cleanup()
        re-restores harmlessly; idempotent), then the new slot is
        snapshotted (lazily, exactly once, BEFORE its first recolor)
        and recolored HIGHLIGHT_COLOR.

        Recolor is detection-safe (extract_game_atoms never reads atom
        color -- geometry.py:134-138) and is property-only -- NOT
        helper geometry (PLAY-04). Documented edge: if the player
        manually recolored an AA mid-game, our restore overwrites
        their change (acceptable; v1 precedent).
        """
        if self._current_slot is not None and self._current_slot != slot_id:
            old_obj = self._objects_by_slot[self._current_slot]
            self._restore_slot_colors(old_obj)
        obj = self._objects_by_slot[slot_id]
        wizard_core.ensure_snapshot(self._color_store, obj,
                                    self._atom_colors(obj))
        cmd.color(wizard_core.HIGHLIGHT_COLOR, obj)
        self._current_slot = slot_id
        cmd.refresh_wizard()

    def _required(self):
        """The current molecule's required dict
        ({'mode': 'any'|'list', 'items': [...]} -- level_spec shape)."""
        return self._payload['levels'][self._level_index]\
            ['molecules'][self._molecule_index]['required']

    def _state_dict(self):
        """The plain-data state dict the pure text builders consume.

        The level keys (05-07) are ADDITIVE: the existing pure builders
        (panel_entries / prompt_lines) read only their own keys and
        tolerate extras by construction."""
        selected = None
        if self._current_slot is not None:
            selected = {'slot_id': self._current_slot,
                        'object': self._objects_by_slot[
                            self._current_slot]}
        return {
            'molecule_id': self._registry['molecules'][
                self._molecule_index]['molecule_id'],
            'molecule_pos': self._molecule_index + 1,
            'molecule_total': len(self._registry['molecules']),
            # 05-07 additive extension (the status tab's READ path):
            'level_pos': self._level_index + 1,
            'level_total': len(self._payload['levels']),
            'required': self._required(),
            'selected': selected,
            'result': self._result,
            'error': self._error,
            # 06-05 additive extension (the status tab's EVENT channel,
            # status_text.status_events; consumers tolerate extras by
            # construction):
            'last_event': self._last_event,
            'game_over': self._game_over,
            'end_state': self._end_state,
        }

    def get_status(self):
        """Plain-data status snapshot for the Game status tab's 1 Hz
        poll (READ path; contract 2 -- plain data only, never Qt or
        callables). Returns _state_dict()."""
        return self._state_dict()

    # -- Lifecycle event machinery (06-05) --------------------------------

    def _set_event(self, kind, **payload):
        """Stamp the last-event marker (06-05/Q7): plain-data dict
        {'kind', 'seq', ...payload} carried on _state_dict['last_event']
        for the status tab's poll diff. The seq counter makes two
        identical consecutive events DISTINCT (whole-dict equality is
        the tab's fingerprint, so a repeat must still read as new)."""
        self._event_seq += 1
        self._last_event = dict(kind=kind, seq=self._event_seq)
        self._last_event.update(payload)

    def _sync_end_state(self):
        """Mirror the live GameState's end fields onto the wizard
        (06-05): op-time mirroring -- GameState.game_over/end_state
        change ONLY through wizard ops (the only callers of the engine
        lifecycle ops), so refreshing HERE keeps the mirror drift-free
        by construction; the tab poll reads plain wizard data, never
        the engine."""
        from . import engine
        gs = engine._current_game()
        self._game_over = bool(gs.game_over)
        self._end_state = gs.end_state

    def _rebind_maps(self, molecule_index):
        """Rebuild the molecule-scoped books (06-05): the pick maps
        (forward + reverse via wizard_core.build_slot_map over the
        LIVE registry), the ligand handle, and the index/selection/
        result books -- the full per-molecule view in ONE place so
        _rebind_molecule and _rebind_level can never half-swap."""
        self._slot_by_object = wizard_core.build_slot_map(
            self._registry, molecule_index)
        self._objects_by_slot = dict(
            (slot_id, obj)
            for obj, slot_id in self._slot_by_object.items())
        self._ligand_object = \
            self._registry['molecules'][molecule_index]['ligand'][0]
        self._molecule_index = molecule_index
        self._current_slot = None
        self._result = None

    def _rebind_molecule(self, molecule_index):
        """In-level advance rebind (06-05): same-level objects all
        still exist, so a live selection's colors are restored FIRST
        (the _select_slot restore-FIRST pattern; the snapshot entry is
        KEPT in the store -- cleanup still re-restores harmlessly),
        then the books rebuild for the NEW molecule."""
        if self._current_slot is not None:
            self._restore_slot_colors(
                self._objects_by_slot[self._current_slot])
        self._rebind_maps(molecule_index)

    def _rebind_level(self, new_registry, level_index):
        """Level advance rebind (06-05/D3): the dying level's objects
        were DELETED by engine.advance_level's scene rebuild, so the
        color store is cleared WITHOUT restoring (nothing to restore
        -- writing colors onto deleted objects would raise); the
        registry + level index swap to the NEW registry, then the
        molecule-0 books rebuild exactly like an in-level advance."""
        self._registry = new_registry
        self._level_index = level_index
        self._color_store.clear()
        self._rebind_maps(0)

    def _compose_active_molecule(self):
        """Camera re-frame onto the NEW molecule after a level advance
        (06-05): the 06-04 public compose seam -- ONE call, no compose
        logic duplicated here."""
        from . import gamestart
        gamestart.compose_molecule_view(self._registry,
                                        self._molecule_index)

    def get_prompt(self):
        """List-of-strings prompt, built by the pure builder (the
        wizard assembles plain data; wizard_text renders it)."""
        return wizard_text.prompt_lines(self._state_dict())

    def get_panel(self):
        """The [kind, text, code] panel entry list, built by the pure
        builder (button codes are cmd.get_wizard().method(...) strings
        -- instance-relative, module-identity-safe by construction)."""
        return wizard_text.panel_entries(self._state_dict())

    # -- Movement model (PLAY-02) ------------------------------------------
    # 03-RESEARCH-movement-spike.md verdict: baked world-frame
    # coordinate transforms on identity-matrix objects ONLY --
    # cmd.translate(v, obj, state=1, camera=0) and cmd.rotate(axis, deg,
    # selection=obj, camera=0, origin=C) bake stored coordinates and
    # provably leave the object matrix at identity. NEVER the object=
    # keyword form of translate/rotate (matrix-only -- the detector is
    # blind to it, spike Q2 confirmed), NEVER placement.transform_baked
    # or cmd.transform_object in game paths (they bake coords BUT record
    # the applied matrix -- render semantics unverified), and NEVER the
    # banned matrix calls (see module docstring contract 5).

    def _current_object(self):
        """The selected slot's object name, or None with a visible
        error line when nothing is selected (fail-closed with a
        VISIBLE message -- movement buttons are always pressable)."""
        if self._current_slot is None:
            self._error = 'Select an amino acid first.'
            cmd.refresh_wizard()
            return None
        return self._objects_by_slot[self._current_slot]

    def _matrix16(self, obj):
        """cmd.get_object_matrix as a 16-float row-major list; a build
        that hands back the 3x4 (12-value) block is normalized by
        appending the homogeneous row."""
        raw = cmd.get_object_matrix(obj)
        if raw is None:
            raise WizardError(
                'wizard: cmd.get_object_matrix(%r) returned None -- '
                'cannot verify the identity-matrix invariant' % (obj,))
        vals = [float(v) for v in raw]
        if len(vals) == 12:
            vals = vals + [0.0, 0.0, 0.0, 1.0]
        if len(vals) != 16:
            raise WizardError(
                'wizard: cmd.get_object_matrix(%r) returned %d values '
                '(expected 16 row-major, or 12 for the 3x4 block)'
                % (obj, len(vals)))
        return vals

    def _assert_identity(self, obj):
        """THE PLAY-02 invariant: the object matrix of every game
        object stays IDENTITY, so on-screen == stored == detected by
        construction (the detector reads stored coords; the screen
        renders the matrix composed over them). Rotation block
        (indices 0,1,2,4,5,6,8,9,10) must read the identity rotation
        and translation (3,7,11) ~ 0 within _MATRIX_TOL; anything else
        is a fail-closed game error NAMING the object (SMOKE-06's
        _is_identity pattern)."""
        m = self._matrix16(obj)
        for i in (0, 1, 2, 4, 5, 6, 8, 9, 10, 3, 7, 11):
            if abs(m[i] - _IDENT_3X4[i]) > _MATRIX_TOL:
                raise WizardError(
                    'wizard: object %r carries a NON-IDENTITY object '
                    'matrix (element %d = %g, expected %g) -- the '
                    'on-screen pose would diverge from the detected '
                    'pose; baked-transform moves keep this matrix at '
                    'identity by construction'
                    % (obj, i, m[i], _IDENT_3X4[i]))

    def _guard(self, op, *args, **kwargs):
        """Run one wizard handler body fail-closed with a VISIBLE
        message: house errors (the ValueError family -- EngineError,
        PlacementError, WizardError) land on self._error + refresh;
        UNEXPECTED exceptions propagate (bug surfacing, never a silent
        swallow). Returns op's return value on success (05-08: hint()
        returns its plain-data result through this seam; every prior
        caller ignores it), None on a guarded refusal."""
        try:
            return op(*args, **kwargs)
        except ValueError as e:
            self._error = str(e)
            cmd.refresh_wizard()
            return None

    def nudge_cam(self, dx, dy, dz):
        """Camera-frame nudge of the selected AA:
        (dx, dy, dz) in {-1, 0, 1} is converted to the WORLD frame via
        wizard_core.view_camera_to_world over cmd.get_view(), scaled by
        wizard_core.NUDGE_STEP, and BAKED via
        cmd.translate(..., state=1, camera=0) + identity assert."""
        self._guard(self._nudge_cam_impl, float(dx), float(dy),
                    float(dz))

    def _nudge_cam_impl(self, dx, dy, dz):
        obj = self._current_object()
        if obj is None:
            return
        w = wizard_core.view_camera_to_world(cmd.get_view(),
                                             (dx, dy, dz))
        step = wizard_core.NUDGE_STEP
        cmd.translate([step * w[0], step * w[1], step * w[2]], obj,
                      state=1, camera=0)
        self._assert_identity(obj)
        cmd.refresh_wizard()

    def rotate_axis(self, axis, deg, origin=None):
        """Generic WORLD-FRAME rotation of the selected AA about
        ``axis`` (3-vector) by ``deg`` degrees; origin defaults to the
        object's centroid (geometry.centroid_of -- baked world-frame
        coords). cmd.rotate(axis, deg, selection=obj, camera=0,
        origin=origin) -- the selection FORM, which bakes stored
        coords (SMOKE-06 Q1 CONFIRMED) -- + identity assert."""
        self._guard(self._rotate_axis_impl, axis, float(deg), origin)

    def _rotate_axis_impl(self, axis, deg, origin):
        obj = self._current_object()
        if obj is None:
            return
        if origin is None:
            origin = geometry.centroid_of(obj)
        cmd.rotate([float(axis[0]), float(axis[1]), float(axis[2])],
                   float(deg), selection=obj, camera=0, origin=origin)
        self._assert_identity(obj)
        cmd.refresh_wizard()

    def rotate_view(self, deg):
        """View-axis rotation: the camera +z axis converted to world
        frame (wizard_core.view_camera_to_world over cmd.get_view()),
        then rotate_axis."""
        axis = wizard_core.view_camera_to_world(cmd.get_view(),
                                                (0.0, 0.0, 1.0))
        self._guard(self._rotate_axis_impl, axis, float(deg), None)

    def step_to_ligand(self):
        """One NUDGE_STEP towards the ligand: unit vector from the
        selected AA's centroid towards the current molecule's ligand
        centroid, scaled by NUDGE_STEP, baked through the SAME path as
        nudge_cam (cmd.translate camera=0) + identity assert."""
        self._guard(self._step_to_ligand_impl)

    def _step_to_ligand_impl(self):
        obj = self._current_object()
        if obj is None:
            return
        aa = geometry.centroid_of(obj)
        lig = geometry.centroid_of(self._ligand_object)
        d = (lig[0] - aa[0], lig[1] - aa[1], lig[2] - aa[2])
        length = math.sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2])
        if length < 1e-9:
            self._error = 'Already at the ligand.'
            cmd.refresh_wizard()
            return
        step = wizard_core.NUDGE_STEP
        cmd.translate([step * d[0] / length,
                       step * d[1] / length,
                       step * d[2] / length], obj, state=1, camera=0)
        self._assert_identity(obj)
        cmd.refresh_wizard()

    def move_to(self, position):
        """DETERMINISTIC scripted placement: engine.place_aa (the
        Phase-2 op -- count- and pose-asserted, baked world-frame) +
        identity assert. This is the scripted-pose path (SMOKE-07 uses
        it for the exact 4.5 A pi-stacking pose, with the explicit
        baked ring-alignment step scripted there first -- the 02-14
        decision: fragments carry no guaranteed ring orientation)."""
        self._guard(self._move_to_impl, position)

    def _move_to_impl(self, position):
        obj = self._current_object()
        if obj is None:
            return
        from . import engine
        engine.place_aa(self._current_slot, position)
        self._assert_identity(obj)
        cmd.refresh_wizard()

    def confirm_molecule(self):
        """PLAY-03 Confirm, the 06-05 lifecycle form (SCORE-01/03):
        record -> event marker -> ADVANCE in ONE op. Renders through
        panel/prompt TEXT built from the plain-data state (wizard_text;
        no result geometry, PLAY-04).

        The Phase-3 re-Confirm caveat is CLOSED: the record routes
        through engine.record_scored, whose one-record guard refuses a
        second Confirm of an already-recorded molecule (the pinned
        'This molecule already has a recorded result ...' message lands
        on the panel error line via _guard). Unreachable after a real
        advance anyway -- Confirm always lands on the NEXT molecule.

        D3 (recorded 06-05): Confirm advances IMMEDIATELY -- the
        score/total debrief lives in the info box via the last-event
        marker, NOT in the prompt; the panel shows the NEXT molecule
        and self._result is CLEARED by every advance (shift from the
        04-15 clarification, rationale recorded in 06-05-SUMMARY).

        Returns the plain-data result through the _guard seam (score,
        total, advanced 'molecule'|'level'|None, game_over, summary,
        level_pos, molecule_pos of the COMPLETED molecule) -- the
        06-07 tab consumes game_over/summary; None on a guarded
        refusal."""
        return self._guard(self._confirm_molecule_impl)

    def _advance_after_record(self):
        """THE advancement decision site (06-05): called AFTER a
        successful record and BEFORE the event is set, so the marker
        is stamped LAST (on level advance the poll sees marker + new
        position in ONE diff). The two position books (GameState via
        the engine op, wizard indexes via the rebind) move atomically
        within this ONE method -- they can never drift.

        Returns ('molecule', None) on an in-level advance (data-only
        engine advance + wizard rebind), ('level', None) on a level
        advance (engine scene rebuild + SAME-INSTANCE rebind -- the D6
        timer anchor survives because activate_game is never called
        mid-game -- + camera re-frame through the 06-04 seam), or
        (None, summary) on natural completion (engine.complete_game;
        NO rebind -- the panel keeps its state, the game is over)."""
        from . import engine
        if self._molecule_index + 1 < len(self._registry['molecules']):
            engine.advance_molecule()
            self._rebind_molecule(self._molecule_index + 1)
            return ('molecule', None)
        if self._level_index + 1 < len(self._payload['levels']):
            new_registry = engine.advance_level()
            self._rebind_level(new_registry, self._level_index + 1)
            self._compose_active_molecule()
            return ('level', None)
        return (None, engine.complete_game())

    def _confirm_molecule_impl(self):
        from . import engine
        if engine.is_over():
            # Cheap plain-data gate (06-05; 06-06 hardens the rest of
            # the lifecycle ops with the same shape).
            raise WizardError('The game is over.')
        required = self._required()
        records = engine.detect_molecule(self._level_index,
                                         self._molecule_index)
        score, formed = engine.record_scored(self._level_index,
                                             self._molecule_index,
                                             required, records=records)
        total = engine.total_score()
        # 03-06 UX addition: records whose type is NOT required still
        # happened on screen -- surface them as 'Formed (not required)'
        # counts (plan's invisible-pi-stacking bug). 'any' mode has no
        # such concept (every record satisfies the requirement), so
        # extras stay empty there by construction.
        extras = []
        if required.get('mode') == 'list':
            required_types = set(item['type']
                                 for item in (required.get('items')
                                              or ()))
            order = dict((t, i) for i, t in
                         enumerate(setup_state.INTERACTION_TYPES))
            counts = {}
            for record in records:
                rtype = record['type']
                if rtype not in required_types:
                    counts[rtype] = counts.get(rtype, 0) + 1
            extras = [(t, counts[t])
                      for t in sorted(counts, key=order.get)]
        self._error = None
        # Capture the COMPLETED molecule's position BEFORE the advance
        # mutates both books -- the marker debriefs what was scored,
        # not where the player now stands.
        scored_level = self._level_index + 1
        scored_pos = self._molecule_index + 1
        scored_m_total = len(self._registry['molecules'])
        advanced, summary = self._advance_after_record()
        self._sync_end_state()
        self._set_event('molecule_scored',
                        score=float(score), total=float(total),
                        molecule_pos=scored_pos,
                        molecule_total=scored_m_total,
                        formed=list(formed), required=required,
                        extras=extras)
        cmd.refresh_wizard()
        return {'score': float(score), 'total': float(total),
                'advanced': advanced, 'game_over': self._game_over,
                'summary': summary, 'level_pos': scored_level,
                'molecule_pos': scored_pos}

    def skip_molecule(self):
        """SCORE-05 Skip (06-06): record the detection-AT-SKIP-TIME
        partial score via the SAME record path as Confirm
        (engine.skip_molecule: record_scored + skip_count + 1 --
        spec.md:44 'store only up to current score of the molecule',
        the 02-10 sanctioned partial-score reading), then advance
        EXACTLY like Confirm through the ONE shared advancement site
        (_advance_after_record) -- so a skip on the LAST molecule of
        the LAST level completes the game (end_state 'completed',
        every molecule has a record).

        WARNING OWNERSHIP: this op is the Yes-branch ONLY; the
        confirmation warning ('This will skip the molecule -- are you
        sure?') belongs to the 06-07 tab wrapper, never here.

        Returns the plain-data result through the _guard seam -- the
        SAME shape as confirm_molecule's ({score, total, advanced,
        game_over, summary, level_pos, molecule_pos of the SKIPPED
        molecule}) so the tab's code path stays uniform; None on a
        guarded refusal."""
        return self._guard(self._skip_molecule_impl)

    def _skip_molecule_impl(self):
        from . import engine
        self._require_playing()
        required = self._required()
        score, formed = engine.skip_molecule(self._level_index,
                                             self._molecule_index,
                                             required)
        total = engine.total_score()
        self._error = None
        # Capture the SKIPPED molecule's position BEFORE the advance
        # mutates both books -- exactly as confirm does.
        scored_level = self._level_index + 1
        scored_pos = self._molecule_index + 1
        scored_m_total = len(self._registry['molecules'])
        advanced, summary = self._advance_after_record()
        self._sync_end_state()
        self._set_event('molecule_skipped',
                        score=float(score), total=float(total),
                        molecule_pos=scored_pos,
                        molecule_total=scored_m_total)
        cmd.refresh_wizard()
        return {'score': float(score), 'total': float(total),
                'advanced': advanced, 'game_over': self._game_over,
                'summary': summary, 'level_pos': scored_level,
                'molecule_pos': scored_pos}

    def reset_grid(self):
        """PLAY-03 Reset: engine.reset_to_grid() -- POSITION replay
        (RECORDED PLANNER DECISION: option a) -- every AA's centroid
        re-bakes to its spec grid pose; ROTATIONS PERSIST (detection
        stays consistent -- SMOKE-06: detect returns 0 records on-grid
        even with the 4.64 A orientation residual; grid margins keep
        rotated side chains beyond cutoffs). The Phase-9 help text
        notes orientation is kept. Re-materialize (option b) was
        REJECTED: it rebuilds objects/registry mid-game, invalidating
        the pick map and color snapshots.

        After the replay: matrix identity asserted for every
        recolored-slot object (research sec. 5.3 -- a silent matrix
        failure can never hide); self._result cleared (poses changed,
        the old result is stale); the current SELECTION + its recolor
        PERSIST (only positions reset)."""
        self._guard(self._reset_grid_impl)

    def _reset_grid_impl(self):
        from . import engine
        engine.reset_to_grid()
        for obj in wizard_core.snapshot_objects(self._color_store):
            self._assert_identity(obj)
        self._result = None
        cmd.refresh_wizard()

    def hint(self):
        """PLAY-05 Hint: recolor the CARBONS of every amino-acid slot
        that could form at least one required interaction -- computed
        CAPABILITY-LIVE via the shared capability module (the same
        predicate the generator's solvability and the detector's
        typing consume; DETECT-04 by construction), NEVER reads the
        slot's can_form provenance (generation-time data,
        generator.py:453-456 -- the hint does not touch that field).

        Recolor ONLY (PLAY-04): no lines/dots/geometry; the atom-color
        property is invisible to detection (extract_game_atoms never
        reads atom color, geometry.py:134-138). The candidate set is
        STATIC within a molecule (payload resn x immutable ligand
        profile x immutable required), so repeated presses are
        idempotent -- NO new wizard attribute is needed (contract 2);
        candidates are recomputed per press.

        Returns plain data for the caller's info box through the
        _guard seam: {'count': n, 'slot_ids': [...] enveloping the
        payload-order candidate tuple}; None on a guarded refusal."""
        return self._guard(self._hint_impl)

    def _hint_impl(self):
        from . import capability, engine
        required = self._required()
        slots = self._payload['levels'][self._level_index] \
            ['molecules'][self._molecule_index]['grid']['slots']
        profile = engine.ligand_profile_molecule(self._level_index,
                                                 self._molecule_index)
        candidate_ids = capability.hint_candidate_slots(slots, profile,
                                                        required)
        if not candidate_ids:
            # Fail-CLOSED: solvability-by-construction makes an empty
            # candidate set unreachable for a real generated payload;
            # a silent no-op would hide a bug instead of surfacing it.
            raise WizardError(
                'hint: no amino acid in the grid could form a required '
                'interaction (%s) -- the solvability guarantee was '
                'violated' % (required.get('mode'),))
        for slot_id in candidate_ids:
            # Selection strings are built ONLY from _objects_by_slot
            # (molecule-scoped by construction via build_slot_map) --
            # the ligand and other molecules' objects are structurally
            # unreachable (H-5); the '<obj> and elem C' scope keeps
            # the recolor carbon-only.
            obj = self._objects_by_slot[slot_id]
            # THE CRITICAL LINE (the (a) trap, 05-RESEARCH-hint H-1):
            # register into the ONE _color_store BEFORE the object's
            # first recolor -- ensure_snapshot otherwise fires only in
            # _select_slot, so a hinted-never-selected object would not
            # be restored on Done. Idempotent: a slot hinted then
            # selected keeps its ORIGINAL pre-hint snapshot.
            wizard_core.ensure_snapshot(self._color_store, obj,
                                        self._atom_colors(obj))
            # cmd.color (NOT alter) -- redraw-safe apply per the 03-06
            # display-rebuild law (the color-rep cache invalidation is
            # C-cited in the research; alter+rebuild stays restore-only).
            cmd.color(wizard_core.HINT_COLOR, '%s and elem C' % obj)
        cmd.refresh_wizard()
        return {'count': len(candidate_ids),
                'slot_ids': list(candidate_ids)}

    # -- Keyboard channels (RESEARCH-wizard sec. 6) ------------------------

    def do_special(self, k, x, y, mod):
        """GLUT special keys: LEFT (100) / RIGHT (102) nudge the
        selected AA in camera x. LEFT/RIGHT are cleanly ownable
        (wizard-first dispatch consumes them when the command line has
        not grabbed arrows); UP/DOWN are NOT -- they co-fire
        command-line history unconditionally (OrthoSpecial), so they
        are NEVER used as game keys. Returning None falls through."""
        if k == 100:
            self.nudge_cam(-1, 0, 0)
            return 1
        if k == 102:
            self.nudge_cam(1, 0, 0)
            return 1
        return None

    def do_key(self, k, x, y, mod):
        """ASCII keys: w/s camera-y nudges, q/e camera-z nudges ('q' =
        In = INTO the screen; if the live build's camera z-sign proves
        inverted in SMOKE-07 / the human checkpoint, flip here --
        cosmetic, detector-neutral), ','/'.' view-axis rotation by
        wizard_core.ROTATE_STEP_DEG. Owned keys return 1 (consumed --
        wizard-first dispatch); everything else returns None so all
        other PyMOL shortcuts keep working."""
        ch = chr(k) if 0 <= k < 127 else ''
        step = _KEY_NUDGES.get(ch)
        if step is not None:
            self.nudge_cam(*step)
            return 1
        if ch == ',':
            self.rotate_view(-wizard_core.ROTATE_STEP_DEG)
            return 1
        if ch == '.':
            self.rotate_view(wizard_core.ROTATE_STEP_DEG)
            return 1
        return None
