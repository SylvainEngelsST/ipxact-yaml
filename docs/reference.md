# ipxYAML v1 field reference

The [schema](../schemas/v1/ipxyaml.schema.yaml) defines structural constraints.
This reference also describes the native semantic requirements.
See [validation](validation.md) before treating a document as valid.

## Common conventions

- A document contains exactly one IP or system definition.
- Unknown properties are rejected at every object level. Property names and
  enumeration values are case-sensitive, including `hwAccess` and `resetType`.
- Every list is nonempty when present. Omit optional lists instead of writing
  `[]` or `null`. Optional properties do not accept `null`.
- `description`, wherever allowed, is optional string Markdown prose, including
  multiline text (`|`). It may be empty. Descriptions do not configure behavior.
- Byte addresses are zero-based. Ranges are half-open: `[base, base + size)`.
  Widths and bit positions are in bits; offsets, bases, and extents are in bytes.
- Uppercase names start with `A`-`Z`, then contain uppercase ASCII
  letters, digits, or single internal underscores. Lowercase names follow the
  equivalent `a`-`z` convention. Leading/trailing/doubled underscores are invalid.
  Examples: `EVENT0`, `SOFT_RESET`, `csr`, `cpu_0`.
- VLNV strings and `source` need a non-whitespace character; they are not
  identifiers and are not trimmed or restricted to those naming patterns.
- Registers are exactly 8, 16, 32, or 64 bits. Field widths are 1 to 64 bits,
  `lsb` is 0 to 63, and `lsb + width_bits` must fit the containing register.
  Reset values and masks are quoted hexadecimal strings fitting the field width,
  so reset processing needs at most unsigned 64-bit storage, not big integers.
- Address/offset integers and byte extents are independent of register size and
  retain their previous unbounded schema ranges. Map/system data widths remain
  positive multiples of eight; no automatic equality with register width is
  imposed. See [validation](validation.md) for `ys` numeric limitations.

There are no implicit access permissions, field widths, reset records, or
volatility values. The only authored property default is map `usage: register`.

## Document root

| Property | Requirement / type | Usage |
|---|---|---|
| `schema_version` | Required integer `1` | Authoring format version, independent of VLNV and tool versions. |
| `naming_profile` | Required string `rds-v1` | Selects the identifier conventions above. |
| `kind` | Required `ip` or `system` | Determines which root collections are legal. |
| `vlnv` | Required object | Identity of this definition; see below. |
| `description` | Optional string | Documentation for the definition. |
| `reset_types` | Optional list, IP only | Reset declarations for this IP's field reset records. |
| `maps` | Required list for IP; forbidden for system | Local register, memory, or reserved maps. |
| `address_spaces` | Required list for system; forbidden for IP | Address spaces populated by referenced instances. |

Systems cannot declare `reset_types`; reset declarations belong to their
referenced IPs. An IP has no placement address. A system supplies placement
through instances and mappings.

## VLNV object

| Property | Requirement / type | Usage |
|---|---|---|
| `vendor` | Required nonblank string | Vendor identity, e.g. `example.org`. |
| `library` | Required nonblank string | Logical library, e.g. `peripherals`. |
| `name` | Required nonblank string | Definition name, distinct from an instance name. |
| `version` | Required nonblank string | Revision text, e.g. `"1.0"`; quote numeric-looking text. |

The native project loader rejects distinct canonical files with identical VLNV
identities in a loaded hierarchy. Multiple instances may reuse the same file.
VLNV `version` is neither `schema_version` nor a mandated semantic-version format.

## Reset type (`reset_types[]`)

| Property | Requirement / type | Usage |
|---|---|---|
| `name` | Required uppercase name | Unique within the IP, e.g. `HARD` or `SOFT`. |
| `description` | Optional string | Explain reset trigger, scope, polarity, or priority. |

Declaring a reset type does not automatically assign it to every field. Names
do not imply polarity or priority; describe those explicitly.

## Local map (`maps[]`)

| Property | Requirement / type | Usage |
|---|---|---|
| `name` | Required lowercase name | Unique within the IP; selected by a parent's `target`. |
| `description` | Optional string | Explain the local region. |
| `usage` | Optional `register`, `memory`, or `reserved` | Omission means `register`. |
| `size_bytes` | Required positive integer | Full local extent, starting at byte zero, including gaps. |
| `data_width_bits` | Required positive multiple of 8 | Data width metadata, not the map extent or an address unit. |
| `access` | Required for memory; forbidden otherwise | Software permission for the whole memory region. |
| `registers` | Required nonempty list for register; forbidden otherwise | Implemented register definitions. |

Different maps are separate local coordinate systems, not automatically adjacent
regions. Reserved maps have effective `no-access` in the native model, but must
not author `access`. Memory maps do not contain register/field descriptions.

The loader does not require register width to equal map data width, nor child
data width to equal parent data width. Those properties do not declare a bus
width converter.

## Register (`maps[].registers[]`)

| Property | Requirement / type | Usage |
|---|---|---|
| `name` | Required uppercase name | Unique within the containing map. |
| `description` | Optional string | Explain the register's purpose. |
| `offset` | Required nonnegative integer | Byte offset from local map origin. |
| `width_bits` | Required integer: `8`, `16`, `32`, or `64` | Register size selected for the architecture; byte size is `width_bits / 8`. |
| `fields` | Required nonempty list | Implemented bit fields. |

The register must fit the map and its offset must align to its own byte size.
Registers must not overlap. Other sizes, including 24, 48, and 128 bits, are invalid.
For example, a 32-bit register at offset 4 occupies bytes `[4, 8)`.
Registers have no authored `access`, `hwAccess`, or reset property:
those belong to fields.

## Field (`registers[].fields[]`)

| Property | Requirement / type | Usage |
|---|---|---|
| `name` | Required uppercase name | Unique within its register. |
| `description` | Optional string | Explain function, update priority, and hardware/software interactions. |
| `lsb` | Required integer, 0 to 63 | Least significant bit in the register. |
| `width_bits` | Required integer, 1 to 64 | Number of bits; must fit the register, but need not be byte-aligned. |
| `access` | Required access enum | Software-side access. |
| `hwAccess` | Required hardware access enum | Hardware-side access, independently specified. |
| `modified_write_value` | Optional write-effect enum | Software write behavior; omit for ordinary writes. |
| `read_action` | Optional `clear` or `set` | Software read side effect; omit for no declared effect. |
| `resets` | Optional nonempty list | Field-relative reset records; see below. |

The occupied bit interval is `[lsb, lsb + width_bits)`. Fields must fit their
register and must not overlap. Gaps are reserved; they are not implicitly
read-write fields with zero resets.

### Software access (`access`)

These values apply to fields and memory maps:

| Value | Meaning |
|---|---|
| `read-only` | Software can read, not write. |
| `write-only` | Software can write, not read. |
| `read-write` | Software can read and write. |
| `writeOnce` | Software write-once permission; no read permission. |
| `read-writeOnce` | Software can read with write-once permission. |
| `no-access` | Neither software reads nor writes are permitted. |

Write-once permissions are descriptive. The schema does not implement a latch,
select a reset that rearms writes, or define illegal-access bus responses.
Explain implementation-specific behavior in descriptions.

### Hardware access (`hwAccess`)

| Value | Meaning |
|---|---|
| `read-only` | Hardware observes the field but does not update it. |
| `write-only` | Hardware updates the field; no hardware read permission is declared. |
| `read-write` | Hardware observes and updates the field. |
| `no-access` | No hardware-side access is declared. |

Permissions are from the named actor's perspective. A software-writable control
field consumed by logic may use `access: read-write`, `hwAccess: read-only`.
A hardware-updated status flag may use `access: read-only`,
`hwAccess: write-only`. The translator derives IP-XACT volatility from
hardware-access analysis; volatility is not authored in ipxYAML. Hardware access
has no write-once values. No permission combination supplies arbitration,
clock-domain behavior, or reset/update priorities; document those separately.

### Software write effects (`modified_write_value`)

| Value | Effect |
|---|---|
| `oneToClear` | Each written 1 clears the corresponding field bit; 0 leaves it unchanged. |
| `oneToSet` | Each written 1 sets the corresponding bit; 0 leaves it unchanged. |
| `oneToToggle` | Each written 1 toggles the corresponding bit; 0 leaves it unchanged. |
| `zeroToClear` | Each written 0 clears the corresponding bit; 1 leaves it unchanged. |
| `zeroToSet` | Each written 0 sets the corresponding bit; 1 leaves it unchanged. |
| `zeroToToggle` | Each written 0 toggles the corresponding bit; 1 leaves it unchanged. |
| `clear` | A software write clears the field, independently of written data. |
| `set` | A software write sets the field, independently of written data. |

Requires software-write access: `write-only`, `read-write`, `writeOnce`, or
`read-writeOnce`. Absence declares ordinary write behavior, not a default effect.

### Software read effects (`read_action`)

`clear` clears the field on a software read; `set` sets it. Requires
`read-only`, `read-write`, or `read-writeOnce`. This property does not itself
define returned read data or simultaneous hardware-update priority.

Read and write effects may coexist when access permits both. Neither effect
changes hardware access permissions.

## Reset record (`fields[].resets[]`)

| Property | Requirement / type | Usage |
|---|---|---|
| `resetType` | Required uppercase name | Exact reference to a declaration in this IP's `reset_types`. |
| `value` | Required hexadecimal string | Reset bits relative to the field, not shifted by `lsb`. |
| `mask` | Required hexadecimal string | One means the bit's reset value is specified; zero means unspecified. |

Both strings require a lowercase `0x` prefix and 1 to 16 hexadecimal digits
(`0`-`9`, `a`-`f`, or `A`-`F`), with no signs, spaces, or separators. Always quote
them, even `"0x0"`; an unquoted YAML hexadecimal number is not a string.
Leading zeros are allowed within the 16-digit limit.

Both numeric patterns must fit `width_bits`: each is at most
`2 ** width_bits - 1`. A full 64-bit field can use `"0xFFFFFFFFFFFFFFFF"` without
arbitrary-precision arithmetic. A 3-bit field can use `"0x7"` but not `"0x8"`.
The schema checks syntax and the 64-bit ceiling; an updated semantic validator
must enforce the exact field-relative ceiling.

There may be at most one record per reset
type per field. A 4-bit field at register bit 8 with `value: "0x5"`, `mask: "0xF"`
specifies all four reset bits; do not shift these patterns by 8. `mask: "0x3"` specifies
only its lowest two bits. The native validator does not require value bits
outside the mask to be zero; those bits do not specify reset behavior.

Missing records are unspecified, not implicit zero resets. Zero masks are legal.
Multiple records specify different reset types, not a priority order.

## Address space (`address_spaces[]`)

| Property | Requirement / type | Usage |
|---|---|---|
| `name` | Required lowercase name | Unique within the system; usable as a parent mapping target. |
| `description` | Optional string | Explain the address space. |
| `address_width_bits` | Required positive integer | Address capacity; `size_bytes <= 2 ** address_width_bits`. |
| `data_width_bits` | Required positive multiple of 8 | Data width metadata in bits. |
| `size_bytes` | Required positive integer | Space extent `[0, size_bytes)` in bytes. |
| `instances` | Required nonempty list | Referenced IPs or nested systems placed in this space. |

Allocations from all instances in one address space must be disjoint and fit
within its extent. Separate address spaces have independent coordinates.

## Instance (`address_spaces[].instances[]`)

| Property | Requirement / type | Usage |
|---|---|---|
| `name` | Required uppercase name | Unique within the containing address space. |
| `description` | Optional string | Describe this occurrence, not the reusable definition. |
| `source` | Required nonblank string | Child YAML path relative to the referencing YAML file, or an absolute path. |
| `mappings` | Required nonempty list | Allocations of selected maps or address spaces in the child. |

`source` refers to a file, not a VLNV string, URL, directory, or mdBook chapter.
Referenced definitions may be IPs or systems. Portable repositories should use
relative paths. Cycles are invalid; the native loader permits at most 128 source
levels. Only trusted sources should be loaded: native resolution has no directory
allowlist.

## Mapping (`instances[].mappings[]`)

| Property | Requirement / type | Usage |
|---|---|---|
| `target` | Required lowercase name | Child IP map name or child system address-space name. |
| `base` | Required nonnegative integer | Byte origin of the child target in the parent space. |
| `size_bytes` | Required positive integer | Allocated window; must be at least the child's full extent. |

Each target can occur only once per instance (no aliases). Not every child
target must be mapped. A larger allocation is allowed, but extra allocated bytes
are not implemented child registers or memory. `base + size_bytes` must fit the
parent; the entire allocated window participates in overlap checks.

Resolution sums mapping bases through the hierarchy, then adds register offsets.
Final register addresses must align to register byte sizes. The native resolver
also rejects ambiguous underscore-flattened map/reset names.

In the [system example](../examples/system.yaml), `CLUSTER0` maps `apb` at
`0x40000000`. That subsystem places `EVENT0.csr` at `0x1000`; register `STATUS`
has offset `0x4`. Its final byte address is `0x40001004`.
