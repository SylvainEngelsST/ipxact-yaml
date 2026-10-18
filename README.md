# rds-ipxYAML

Reference schema and field-by-field documentation for **ipxYAML**, the
memory-map authoring format derived from **IP-XACT IEEE1685-2022** and can be found under [edaa-org](https://github.com/edaa-org/IPXACT-Schema/tree/main/ieee-1685-2022) git directory

The current contract is `schema_version: 1`, `naming_profile: yaml-ipxact2022`.
The authoritative schema is
[`schemas/v1/ipxyaml.schema.yaml`](schemas/v1/ipxyaml.schema.yaml), written
in [YAML Schema](https://yaml-schema.net/). 

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
- Examples: [IP](examples/ip.yaml), [subsystem](examples/subsystem.yaml),
  and [system](examples/system.yaml).

## Validate

An pre_installed version is available under `./bin` directory. If the version or the operating system need to be changed, you can install the reference implementation from yaml-schema.net:

```sh
cargo install yaml-schema --version 0.9.3 --locked
```

Validate the YAML versus the schema :

```sh
./bin/ys -f schemas/v1/ipxyaml.schema.yaml examples/ip.yaml
```

Validate the schema itself against the official meta-schema:

```sh
curl -fsSL https://yaml-schema.net/yaml-schema.yaml -o /tmp/yaml-schema.meta.yaml

./bin/ys -f /tmp/yaml-schema.meta.yaml schemas/v1/ipxyaml.schema.yaml

python3 tests/validate.py --meta-schema /tmp/yaml-schema.meta.yaml
```

Structural validation is necessary but **not sufficient**: an updated consumer
must enforce lexical restrictions, overlap/bounds checks, field-relative reset
limits, and hierarchy resolution. See [validation limitations](docs/validation.md).

IEEE 1685-2022 is the conceptual reference; this is a constrained authoring
profile, not the official IEEE schema or a complete YAML encoding of IP-XACT.
The repository is licensed under [MPL-2.0](LICENSE).
