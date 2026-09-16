"""aamatch.upload -- the cmd-tier upload extraction bridge (04-08).

Layer: CMD TIER (never PURE_MODULES); per-record uploaded-molecule
extraction. Module-level ``from pymol import cmd`` is legal here,
exactly like engine.py/placement.py; this module must NEVER be added
to ``PURE_MODULES`` in tests/test_purity.py (the purity gates scan
only the pure registry; Gate D's 3.6 syntax floor still compiles this
file).

This module is the bridge named by 04-RESEARCH-export-upload.md
upload_pipeline Step 2: the PURE split/row helpers (04-06,
aamatch/game_file.py) hand split record TEXT in, and this module
turns each record into exactly what ``engine.new_game`` /
``gamestart.start_game`` already accept -- manifest-shaped
``candidates`` rows plus the ``ligand_content`` dict (04-04 seams).
After this bridge, the window upload handler (04-10) is pure glue.

Per-record extraction copies the proven engine._ligand_data_for
discipline (engine.py:153-180), descriptor by descriptor:

1. a FRESH ``cmd.get_unused_name('_aam_tmp')`` name per record (never
   load into an existing name -- that appends a state);
2. the record loads FROM ITS STRING via ``cmd.read_sdfstr`` /
   ``cmd.read_mol2str`` -- the same C parsers as file loads
   (importing.py:931-959/1038-1069), so bond orders and ``M CHG``
   formal charges round-trip identically (SMOKE-12 PART 1 pins the
   parity empirically on this build);
3. ``cmd.count_states(tmp)`` must be EXACTLY 1 -- records are split
   one molecule per entry upstream; a multi-state decode means the
   record smuggled nested records (fail-closed);
4. extraction is SCOPED to the temp object
   (``r['object'] == tmp`` over geometry.extract_game_atoms()) and
   must produce atoms;
5. the bond block remaps through the 02-09-probed walk-position
   mapping (``engine._remap_ligand_bonds`` -- nothing in it is
   manifest-specific) and the capability profile comes from the ONE
   typing home (capability.ligand_profile);
6. the temp is DELETED in a finally and the object list is asserted
   identical to a pre-loop snapshot after EVERY iteration -- temps
   never leak, even on a mid-loop refusal.

NO bounding-sphere work here on purpose: rows need counts/flags, not
geometry; the engine recomputes geometry from ligand_content at
``new_game`` time via ``_ligand_data_for``. Calling it here would be
dead work.

Reader availability (04-04 build finding): both ``read_*str``
branches are hasattr-guarded and fail closed naming the missing
reader -- this 2.5.0 build defines ``read_mol2str`` in
importing.py:1038 but omits its api.py re-export, so mol2 string
loads are refused with a clear message instead of an AttributeError.
Single-molecule MOL2 upload availability is therefore a per-build
capability, never assumed.

Build note: multi-segment MOL2 policy is Decision 14 of the 04-08
plan (probe-gated; SMOKE-12 PART 4 records the verdict).

Python floor: runs inside PyMOL's Windows Python (3.9); written
3.6-safe (Gate D compiles every aamatch/*.py under python3.6).
"""

from pymol import cmd


def prepare_uploaded_set(records, fmt):
    """Split record strings -> (rows, ligand_content) for new_game.

    ``records`` is the per-record string list from
    game_file.split_sdf_records / split_mol2_segments (already
    supply-checked); ``fmt`` is 'sdf' or 'mol2' (anything else fails
    closed). Returns the pair the 04-04 ligand_content seams accept:

    - rows: manifest-shaped upload rows from
      game_file.build_uploaded_row (synthetic 'mol-%03d' entry ids,
      synthetic 'uploads/mol-%03d.<fmt>' file keys, record-text
      sha256), re-validated once at the end by
      game_file.validate_uploaded_rows (fail-closed before anything
      downstream consumes them);
    - ligand_content: {synthetic file key: record text} -- the key
      is a KEY, never a filesystem path (the absolute-path hazard is
      structurally impossible, 04 research upload_pipeline).

    Per record: fresh ``_aam_tmp`` name, string load, single-state +
    non-empty asserts, scoped extraction, bond remap, capability
    profile -- then the temp is deleted in a finally and the object
    list asserted unchanged (the engine.py:153-180 temp discipline;
    a leaked temp raises ValueError naming it). Every refusal names
    the 1-based record index.
    """
    # Lazy sibling imports INSIDE the function (wizard.py:22-29
    # discipline, uniform): module-identity-safe both as aamatch and
    # as pmg_tk.startup.aamatch.
    from . import geometry, capability, engine, game_file

    if fmt not in ('sdf', 'mol2'):
        raise ValueError(
            'upload: unsupported format %r (expected sdf or mol2)'
            % (fmt,))

    rows = []
    ligand_content = {}
    names_before = list(cmd.get_names('objects'))
    for i, record in enumerate(records):
        number = i + 1
        tmp = cmd.get_unused_name('_aam_tmp')
        try:
            if fmt == 'sdf':
                if not hasattr(cmd, 'read_sdfstr'):
                    raise ValueError(
                        'upload record %d needs cmd.read_sdfstr, which '
                        'THIS PyMOL build does not export -- sdf string '
                        'uploads are unavailable here' % (number,))
                cmd.read_sdfstr(record, tmp)
            else:
                if not hasattr(cmd, 'read_mol2str'):
                    raise ValueError(
                        'upload record %d needs cmd.read_mol2str, '
                        'which THIS PyMOL build does not export (2.5.0 '
                        'api.py omits it) -- mol2 uploads are '
                        'unavailable here' % (number,))
                cmd.read_mol2str(record, tmp)
            n_states = cmd.count_states(tmp)
            if n_states != 1:
                raise ValueError(
                    'upload record %d decoded to %d states (expected '
                    '1) -- the file may smuggle nested records'
                    % (number, n_states))
            records_i = [r for r in geometry.extract_game_atoms()
                         if r['object'] == tmp]
            if not records_i:
                raise ValueError(
                    'upload record %d produced 0 atoms' % (number,))
            lig_records, lig_bonds = engine._remap_ligand_bonds(
                records_i, [tmp])
            profile = capability.ligand_profile(lig_records, lig_bonds)
        finally:
            if tmp in cmd.get_names('objects'):
                cmd.delete(tmp)
            if cmd.get_names('objects') != names_before:
                raise ValueError(
                    'upload: temp object %r leaked (objects before: '
                    '%s, after: %s) -- prepare_uploaded_set must leave '
                    'the scene untouched' % (tmp, names_before,
                                             cmd.get_names('objects')))
        row = game_file.build_uploaded_row(records_i, lig_bonds,
                                           profile, record_text=record,
                                           fmt=fmt, index=i)
        rows.append(row)
        ligand_content[row['file']] = record

    game_file.validate_uploaded_rows(rows)
    return rows, ligand_content
