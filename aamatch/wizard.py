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

from pymol import cmd
from pymol.wizard import Wizard

from . import wizard_core, wizard_text


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
    - ``_result``         last confirm result dict or None
    - ``_error``          last visible error string or None
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
        """The plain-data state dict the pure text builders consume."""
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
            'required': self._required(),
            'selected': selected,
            'result': self._result,
            'error': self._error,
        }

    def get_prompt(self):
        """List-of-strings prompt, built by the pure builder (the
        wizard assembles plain data; wizard_text renders it)."""
        return wizard_text.prompt_lines(self._state_dict())

    def get_panel(self):
        """The [kind, text, code] panel entry list, built by the pure
        builder (button codes are cmd.get_wizard().method(...) strings
        -- instance-relative, module-identity-safe by construction)."""
        return wizard_text.panel_entries(self._state_dict())
