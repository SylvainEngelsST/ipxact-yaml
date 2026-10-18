# rds-ipxYAML

Reference schema and field-by-field documentation for **ipxYAML**, the
memory-map authoring format derived from `mdbook-memmap`.

The current contract is `schema_version: 1`, `naming_profile: rds-v1`.
The authoritative schema is
[`schemas/v1/ipxyaml.schema.yaml`](schemas/v1/ipxyaml.schema.yaml), written
in [YAML Schema](https://yaml-schema.net/). This is the target contract for a
future mdbook-memmap update, not its Rust internal model, mdBook configuration,
or release locks.

**Compatibility notice:** v1 has been revised before release. Register sizes
are now exactly 8, 16, 32, or 64 bits; reset `value` and `mask` are quoted
hexadecimal strings, such as `"0xFFFFFFFFFFFFFFFF"`. The existing mdbook-memmap
does not accept these reset strings and must be updated separately. See
[migration requirements](docs/provenance.md#consumer-migration).

## Start here

- [Field reference](docs/reference.md): every property, requirement, unit,
  default, and access/reset effect.
- [IEEE 1685-2022 relationship](docs/ieee-1685-2022.md): scope, conceptual
  mapping, and project-specific conventions.
- [Validation](docs/validation.md): `ys` commands, validation boundaries, and tests.
- [Provenance and versioning](docs/provenance.md): rds-designspec origins and
  the mdbook-memmap implementation used to construct this schema.
- Examples: [IP](examples/ip.yaml), [subsystem](examples/subsystem.yaml),
  and [system](examples/system.yaml).

## Validate

Install the reference implementation from yaml-schema.net:

```sh
cargo install yaml-schema --version 0.9.3 --locked
ys -f schemas/v1/ipxyaml.schema.yaml examples/ip.yaml
```

Validate the schema itself against the official meta-schema:

```sh
curl -fsSL https://yaml-schema.net/yaml-schema.yaml -o /tmp/yaml-schema.meta.yaml
ys -f /tmp/yaml-schema.meta.yaml schemas/v1/ipxyaml.schema.yaml
python3 tests/validate.py --meta-schema /tmp/yaml-schema.meta.yaml
```

In proxy-controlled environments, load the local proxy configuration before
network commands. No authored documents need to be sent to a website.

Structural validation is necessary but **not sufficient**: an updated consumer
must enforce lexical restrictions, overlap/bounds checks, field-relative reset
limits, and hierarchy resolution. See [validation limitations](docs/validation.md).

IEEE 1685-2022 is the conceptual reference; this is a constrained authoring
profile, not the official IEEE schema or a complete YAML encoding of IP-XACT.
The repository is licensed under [MPL-2.0](LICENSE).
