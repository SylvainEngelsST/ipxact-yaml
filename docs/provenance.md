# Provenance and versioning

## Authority

The reference schema was initially constructed from the YAML accepted by
**mdbook-memmap**, at Git revision
`9619466e96c59d1cb48ce7d2c176d730e4b39990`.
The implementation surfaces used were:

- `src/source.rs`: scalar vocabulary, identifier rules, optional/nonempty lists,
  and YAML syntax restrictions.
- `src/loader.rs` and `src/model.rs`: properties, required values, defaults,
  conditionals, enumerations, and numeric capacities.
- `src/validation.rs`: local semantic requirements.
- `src/project.rs`: source resolution, hierarchy checks, and resolved alignment.
- `tests/engine.rs` and YAML fixtures: examples of accepted/rejected behavior.

The source checkout supplied for this work was
`/prj/rds/softwares/freeware/mdBook/0.5.4/rh80_64/git/mdbook-memmap`.
This path is provenance only, not a dependency of the reference repository.

## Earlier origin

rds-designspec contains the earlier memory-map authoring schema at
`tools/memory-map/python/src/rds_memmap/schemas/authoring-v1.schema.json`.
The inspected rds-designspec revision was
`735d075c093ad9dfc3908f34dc4dbdd6ca256dff`.

That implementation is historical context, not the authority for this schema.
In particular, the reference embeds mdbook-memmap's identifier rules instead of
depending on the earlier external naming-schema URN, and records the native
unsigned 64-bit width/index bounds.

## Contract versions

Both existing implementations identify authored documents as
`schema_version: 1`, `naming_profile: rds-v1`. The existence of two implementations
does **not** create a v2 authoring contract. mdbook-memmap's version-2 provenance
envelope is a different artifact and is outside this schema's scope.

- `schemas/v1/` now describes the revised target contract, not exact compatibility
  with the pinned implementation.
- VLNV `version` versions a user's definition, not this format.
- Documentation clarifications and corrections to match the pinned source
  belong in v1, with regression tests.
- At the repository owner's request, this pre-release v1 was revised in place
  instead of introducing v2. Consumer compatibility is deliberately not preserved.
- Neither rds-designspec nor mdbook-memmap is changed in this repository work.
  Consumers must migrate before accepting the revised examples.

The [validation guide](validation.md) records tool limitations separately from
the intentional contract changes below.

## Consumer migration

The intentional changes from the pinned source are:

1. Restrict register `width_bits` to exactly 8, 16, 32, or 64.
2. Restrict field widths to 1..64 and `lsb` to 0..63; additionally enforce
   `lsb + width_bits <= register.width_bits`.
3. Require reset `value` and `mask` as quoted hexadecimal strings with lowercase
   `0x` prefix and 1..16 hex digits. Convert existing integers without truncation;
   reject values that exceed the field width or the 64-bit limit.
4. Parse reset strings into unsigned 64-bit values and validate them against the
   field width. Handle width 64 without an overflowing `1 << 64` operation.
5. Preserve missing-reset, mask, permission, and priority semantics.
6. Update generated documentation, serializers, release-lock handling where
   applicable, fixtures, and diagnostics to match the new authored scalar types.

For example, `value: 0` becomes `value: "0x0"` and `mask: 1` becomes
`mask: "0x1"`. A 128-bit register cannot be migrated by truncating it; redesign
it as architecture-appropriate registers or reject it.

Address offsets/bases, address widths, byte extents, and map/system data widths
are unchanged. Removing arbitrary precision from reset handling does not yet
remove it from address/extent handling. Those limits need a separate decision.
