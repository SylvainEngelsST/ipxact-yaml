# Validation with YAML Schema

Use the [YAML Schema](https://yaml-schema.net/) reference implementation, `ys`.
The authoritative artifact is YAML, not a JSON Schema file with a YAML filename.
It uses the site's `$defs`, `$ref`, object, numeric, and conditional vocabulary.

## Install and run

```sh
cargo install yaml-schema --version 0.9.3 --locked
ys version
ys -f schemas/v1/ipxyaml.schema.yaml examples/ip.yaml
ys -f schemas/v1/ipxyaml.schema.yaml examples/subsystem.yaml
ys -f schemas/v1/ipxyaml.schema.yaml examples/system.yaml
```

`ys` exits zero for success and nonzero for failure. Use `--json` for
machine-readable diagnostics with source locations and property paths.
Always pass `-f`: adding `$schema` to an authored IP/system document would violate
the native consumer's unknown-property rule. An editor's comment directive, such
as `# yaml-language-server: $schema=../schemas/v1/ipxyaml.schema.yaml`, does not
add a document property, but editor support for this YAML-native dialect varies.

## Validate the schema itself

Fetch the site's official meta-schema, then run it locally against our schema:

```sh
curl -fsSL https://yaml-schema.net/yaml-schema.yaml -o /tmp/yaml-schema.meta.yaml
ys -f /tmp/yaml-schema.meta.yaml schemas/v1/ipxyaml.schema.yaml
python3 tests/validate.py --meta-schema /tmp/yaml-schema.meta.yaml
```

Load your environment's proxy configuration before network commands if required.
The download retrieves only the public meta-schema: authored documents remain
local. The meta-schema is upstream-owned and may evolve; the validator version
is pinned for reproducibility. The test command accepts `--ys /path/to/ys` if
the executable is not on `PATH`.

The tests check meta-schema validity, valid examples, negative mutations across
all object types and conditional branches, required/unknown properties, names,
access/effects, and nonempty lists. They require Python 3.6+ and `ys`, with no
Python packages. They distinguish validation diagnostics from tool/setup failures,
so a missing schema or broken executable cannot masquerade as a passing negative test.

## Validation layers

The schema is the target authority. Native layers below describe requirements
for a migrated consumer; the pinned mdbook-memmap still expects integer resets
and is not compatible with the revised v1.

| Layer | Checks |
|---|---|
| Official meta-schema via `ys` | Schema vocabulary and shape, including unknown schema keywords. |
| Reference schema via `ys` | Required/unknown properties, scalar types, enums, naming patterns, positive/nonnegative values, register sizes 8/16/32/64, field width/index limits, hexadecimal reset syntax and 64-bit ceiling, nonempty lists, kind/usage branches, hardware-write volatility, effect/access compatibility. |
| Native YAML parser | Exactly one document, string keys, duplicate/merge key rejection, no anchors/aliases/explicit tags, supported directives, strict scalar spelling, nesting capacity. |
| Native local validator | Unique names, register alignment/bounds/overlaps, field bounds/overlaps, reset references/duplicates/widths, address capacity, allocation bounds/overlaps, duplicate mapping targets. |
| Native project loader/resolver | Readable referenced sources, unique VLNV per canonical file, no cycles, depth limit, existing child targets, allocation large enough for target, final register alignment, unambiguous flattened names. |

`ys` does not traverse `source` references: each file must be structurally
validated separately. The reference schema cannot express cross-property
arithmetic, name-key uniqueness in arrays, or filesystem/hierarchy relationships.
It does not require equal parent/child data widths or zero value bits outside
reset masks. Exact reset fit (`value, mask < 2 ** field.width_bits`) remains a
semantic check: the 16-hex-digit limit alone does not prove fit in a smaller field.

## Known `ys` 0.9.3 boundaries

Use an updated semantic validator in addition to `ys`:

- `ys` uses signed 64-bit integer storage and floating-point numeric paths,
  whereas addresses and extents retain unbounded schema ranges. Do not rely on `ys` for exact values or
  boundary comparisons outside signed 64-bit capacity. Large supported native
  values may be rejected or represented approximately by `ys`; this is a tool
  limitation, not a new schema restriction.
  Reset values and masks are different: their quoted hexadecimal representation
  is validated exactly as text, including `"0xFFFFFFFFFFFFFFFF"`. No big-integer
  storage is needed for resets. The upstream 80-bit reset
  `0x80000000000000000001` is intentionally invalid in the revised contract.
- YAML Schema's integer validation accepts integral floating-point values
  (for example `32.0`), while the native parser rejects floating-point syntax.
- General YAML parsing may resolve scalar spellings differently from the native
  authoring subset. Native integers are unquoted decimal or lowercase-prefix
  hexadecimal (`0x`), optionally signed; negative nonzero values are rejected.
  Leading decimal zeros do not mean octal. Native negative zero is accepted.
  Binary/octal/separator forms do not count as integers.
- Native booleans accept true/false in lowercase, title case, or uppercase.
  Numeric strings, nulls, and booleans cannot substitute for integers.
  Native `on`/`off`, dates, and binary/octal-looking prose remain strings.
- A general validator's YAML feature handling is not proof that native restrictions
  on aliases, tags, directives, duplicate keys, or multiple documents were met.

Prefer plain decimal/hex integers within signed 64-bit capacity for address and
byte-size properties when using `ys` as a first-line check. Do not quote those
properties to bypass a diagnostic. Only reset values/masks use hexadecimal strings.

## Native integration check

After migrating mdbook-memmap, load the files with its
`loader::load_definition` (one file) and `Project::load` / `Project::resolve`
(hierarchy and selected resolved space), or render them through the preprocessor.
There is no standalone `mdbook-memmap validate` command.

If a migrated native binary is available, the repository's test runner can additionally
render the example register/memory/reserved maps and resolve both hierarchy
levels, asserting exact final register addresses:

```sh
python3 tests/validate.py --meta-schema /tmp/yaml-schema.meta.yaml \
  --mdbook-memmap /path/to/mdbook-memmap
```

This optional check is not run against the current binary or in schema-only CI:
the current binary rejects quoted reset values. No native acceptance of the
revised contract is claimed until that consumer is updated.

For example, a book chapter may include:

````markdown
```memmap
source: /absolute/path/to/rds-ipxYAML/examples/system.yaml
address_space: cpu
view: summary
```
````

The example hierarchy should resolve `EVENT0.STATUS` under `CLUSTER0` to
`0x40001004`. Detailed register views require register maps; memory/reserved maps
are valid authoring inputs but cannot be selected as detailed register views.
