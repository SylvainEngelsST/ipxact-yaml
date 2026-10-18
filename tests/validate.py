#!/usr/bin/env python3
"""Exercise the reference schema using the yaml-schema.net ys implementation."""

import argparse
import copy
import json
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/v1/ipxyaml.schema.yaml"
FIELD = {
    "name": "FLAG", "lsb": 0, "width_bits": 1,
    "access": "read-write", "hwAccess": "read-only", "volatile": False,
}
REGISTER = {"name": "CTRL", "offset": 0, "width_bits": 32, "fields": [FIELD]}
MAP = {
    "name": "csr", "size_bytes": 4096, "data_width_bits": 32,
    "registers": [REGISTER],
}
IP = {
    "schema_version": 1, "naming_profile": "rds-v1", "kind": "ip",
    "vlnv": {"vendor": "example.org", "library": "test", "name": "unit", "version": "1"},
    "reset_types": [{"name": "HARD"}], "maps": [MAP],
}
MAPPING = {"target": "csr", "base": 0, "size_bytes": 4096}
INSTANCE = {"name": "UNIT0", "source": "ip.yaml", "mappings": [MAPPING]}
SPACE = {
    "name": "cpu", "address_width_bits": 32, "data_width_bits": 32,
    "size_bytes": 65536, "instances": [INSTANCE],
}
SYSTEM = {
    "schema_version": 1, "naming_profile": "rds-v1", "kind": "system",
    "vlnv": {"vendor": "example.org", "library": "test", "name": "system", "version": "1"},
    "address_spaces": [SPACE],
}
RESET = {"resetType": "HARD", "value": "0x0", "mask": "0x1"}


def at(document, path):
    for part in path:
        document = document[part]
    return document


def cases():
    yield "minimal-ip", IP, True
    yield "minimal-system", SYSTEM, True
    objects = [
        (IP, (), ["schema_version", "naming_profile", "kind", "vlnv", "maps"]),
        (IP, ("vlnv",), list(IP["vlnv"])),
        (IP, ("reset_types", 0), ["name"]),
        (IP, ("maps", 0), ["name", "size_bytes", "data_width_bits", "registers"]),
        (IP, ("maps", 0, "registers", 0), list(REGISTER)),
        (IP, ("maps", 0, "registers", 0, "fields", 0), list(FIELD)),
        (SYSTEM, (), ["address_spaces"]),
        (SYSTEM, ("address_spaces", 0), list(SPACE)),
        (SYSTEM, ("address_spaces", 0, "instances", 0), list(INSTANCE)),
        (SYSTEM, ("address_spaces", 0, "instances", 0, "mappings", 0), list(MAPPING)),
    ]
    reset_ip = copy.deepcopy(IP)
    reset_ip["maps"][0]["registers"][0]["fields"][0]["resets"] = [RESET]
    objects.append((reset_ip, ("maps", 0, "registers", 0, "fields", 0, "resets", 0),
                    list(RESET)))
    for base, path, required in objects:
        for key in required:
            value = copy.deepcopy(base)
            del at(value, path)[key]
            yield "missing-{}-{}".format(path, key), value, False
        value = copy.deepcopy(base)
        at(value, path)["unexpected"] = True
        yield "unknown-{}".format(path), value, False

    field_path = ("maps", 0, "registers", 0, "fields", 0)
    mutations = [
        ((), "schema_version", 2, False),
        ((), "schema_version", "1", False),
        ((), "naming_profile", "other", False),
        ((), "kind", "component", False),
        ((), "address_spaces", [SPACE], False),
        ((), "maps", [], False),
        ((), "reset_types", [], False),
        (("vlnv",), "version", 1, False),
        (("vlnv",), "vendor", " \t", False),
        (("maps", 0), "size_bytes", 0, False),
        (("maps", 0), "size_bytes", -1, False),
        (("maps", 0), "size_bytes", True, False),
        (("maps", 0), "size_bytes", "4096", False),
        (("maps", 0), "data_width_bits", 7, False),
        (("maps", 0), "data_width_bits", 0, False),
        (("maps", 0), "registers", [], False),
        (("maps", 0), "access", "read-write", False),
        (("maps", 0), "usage", "other", False),
        (("maps", 0), "usage", "memory", False),
        (("maps", 0), "usage", "reserved", False),
        (("maps", 0), "usage", "register", True),
        (("maps", 0), "name", "CSR", False),
        (("maps", 0), "name", "csr_", False),
        (("maps", 0), "name", "c__sr", False),
        (("maps", 0), "name", "_csr", False),
        (("maps", 0), "name", "c_0", True),
        (("maps", 0, "registers", 0), "name", "ctrl", False),
        (("maps", 0, "registers", 0), "offset", -1, False),
        (("maps", 0, "registers", 0), "width_bits", 9, False),
        (("maps", 0, "registers", 0), "fields", [], False),
        (field_path, "width_bits", 0, False),
        (field_path, "width_bits", 3, True),
        (field_path, "lsb", -1, False),
        (field_path, "hwAccess", "writeOnce", False),
        (field_path, "hwAccess", "write-only", False),
        (field_path, "hwAccess", "read-write", False),
        (field_path, "volatile", "true", False),
        (field_path, "volatile", True, True),
        (field_path, "access", "rw", False),
        (field_path, "modified_write_value", "invalid", False),
        (field_path, "read_action", "modify", False),
        (field_path, "resets", [], False),
        (field_path, "description", None, False),
        (field_path, "description", "", True),
        (field_path, "resets", [RESET], True),
    ]
    for path, key, replacement, valid in mutations:
        value = copy.deepcopy(IP)
        at(value, path)[key] = replacement
        yield "set-{}-{}-{}".format(path, key, replacement), value, valid

    for key, replacement in [
        ("maps", [MAP]), ("reset_types", [{"name": "HARD"}]),
        ("address_spaces", []),
    ]:
        value = copy.deepcopy(SYSTEM)
        value[key] = replacement
        yield "system-{}".format(key), value, False
    for path, key, replacement in [
        (("address_spaces", 0), "address_width_bits", 0),
        (("address_spaces", 0), "data_width_bits", 3),
        (("address_spaces", 0), "instances", []),
        (("address_spaces", 0, "instances", 0), "source", "  "),
        (("address_spaces", 0, "instances", 0), "mappings", []),
        (("address_spaces", 0, "instances", 0, "mappings", 0), "target", "CSR"),
        (("address_spaces", 0, "instances", 0, "mappings", 0), "base", -1),
        (("address_spaces", 0, "instances", 0, "mappings", 0), "size_bytes", 0),
    ]:
        value = copy.deepcopy(SYSTEM)
        at(value, path)[key] = replacement
        yield "system-{}-{}".format(path, key), value, False

    for usage in ["memory", "reserved"]:
        value = copy.deepcopy(IP)
        memory_map = value["maps"][0]
        del memory_map["registers"]
        memory_map["usage"] = usage
        if usage == "memory":
            memory_map["access"] = "read-write"
        yield usage, copy.deepcopy(value), True
        if usage == "memory":
            del memory_map["access"]
        else:
            memory_map["access"] = "no-access"
        yield "{}-wrong-access".format(usage), value, False

    for access in ["read-only", "write-only", "read-write", "writeOnce",
                   "read-writeOnce", "no-access"]:
        value = copy.deepcopy(IP)
        at(value, field_path)["access"] = access
        yield "access-{}".format(access), value, True
        for effect in ["oneToClear", "oneToSet", "oneToToggle", "zeroToClear",
                       "zeroToSet", "zeroToToggle", "clear", "set"]:
            value = copy.deepcopy(IP)
            field = at(value, field_path)
            field.update(access=access, modified_write_value=effect)
            yield "write-{}-{}".format(access, effect), value, access in [
                "write-only", "read-write", "writeOnce", "read-writeOnce"]
        for effect in ["clear", "set"]:
            value = copy.deepcopy(IP)
            at(value, field_path).update(access=access, read_action=effect)
            yield "read-{}-{}".format(access, effect), value, access in [
                "read-only", "read-write", "read-writeOnce"]
    for access in ["read-only", "write-only", "read-write", "no-access"]:
        for volatile in [False, True]:
            value = copy.deepcopy(IP)
            at(value, field_path).update(hwAccess=access, volatile=volatile)
            yield "hardware-{}-{}".format(access, volatile), value, (
                volatile or access in ["read-only", "no-access"])
    for width in [8, 16, 32, 64, 0, 7, 24, 48, 128]:
        value = copy.deepcopy(IP)
        value["maps"][0]["registers"][0]["width_bits"] = width
        yield "register-width-{}".format(width), value, width in [8, 16, 32, 64]
    for key, values in [
        ("width_bits", [(64, True), (65, False)]),
        ("lsb", [(63, True), (64, False)]),
    ]:
        for number, valid in values:
            value = copy.deepcopy(IP)
            at(value, field_path)[key] = number
            if key == "width_bits":
                value["maps"][0]["registers"][0]["width_bits"] = 64
            elif valid:
                value["maps"][0]["registers"][0]["width_bits"] = 64
            yield "field-{}-{}".format(key, number), value, valid
    for width in [8, 16, 32, 64]:
        value = copy.deepcopy(IP)
        register = value["maps"][0]["registers"][0]
        register["width_bits"] = width
        field = register["fields"][0]
        field["width_bits"] = width
        pattern = "0x" + "F" * (width // 4)
        field["resets"] = [dict(RESET, value=pattern, mask=pattern)]
        yield "full-width-reset-{}".format(width), value, True
    for key in ["value", "mask"]:
        for pattern, valid in [
            ("0x0", True), ("0x1", True), ("0x0001", True),
            ("0xFFFFFFFFFFFFFFFF", True), ("0xffffffffffffffff", True),
            (0, False), (1, False), ("1", False), ("0X1", False),
            ("0x", False), ("0xG", False), ("-0x1", False),
            ("0x1_0", False), ("0x10000000000000000", False),
        ]:
            value = copy.deepcopy(IP)
            value["maps"][0]["registers"][0]["width_bits"] = 64
            field = at(value, field_path)
            field["width_bits"] = 64
            field["resets"] = [dict(RESET, **{key: pattern})]
            yield "reset-{}-{}".format(key, pattern), value, valid


def validate(ys, schema, document, expected):
    result = subprocess.run(
        [ys, "--json", "-f", str(schema), str(document)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
        timeout=30,
    )
    if expected:
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
    else:
        if result.returncode != 1:
            raise AssertionError("Expected validation rejection: " + result.stdout + result.stderr)
        errors = json.loads(result.stdout)
        if not isinstance(errors, list) or not errors or result.stderr.strip():
            raise AssertionError("Expected schema diagnostics, not a tool error: " +
                                 result.stdout + result.stderr)


def validate_native(executable):
    selections = [
        ("ip.yaml", "map: csr", "registers", ["STATUS", "oneToClear"]),
        ("ip.yaml", "map: scratch", "summary", ["memory"]),
        ("ip.yaml", "map: hole", "summary", ["reserved"]),
        ("subsystem.yaml", "address_space: apb", "summary",
         ["EVENT0.csr", "`0x00001004`", "EVENT1.csr", "`0x00003004`"]),
        ("system.yaml", "address_space: cpu", "summary",
         ["CLUSTER0.EVENT0.csr", "`0x40001004`", "`0x40003004`"]),
    ]
    with tempfile.TemporaryDirectory(prefix="ipxyaml-native-") as directory:
        for filename, selector, view, expected in selections:
            content = "```memmap\nsource: {}\n{}\nview: {}\n```\n".format(
                ROOT / "examples" / filename, selector, view)
            Path(directory, "page.md").write_text(content)
            request = [
                {"root": directory, "config": {"book": {"title": "Reference", "src": "."}},
                 "renderer": "html", "mdbook_version": "0.5.4"},
                {"items": [{"Chapter": {
                    "name": "Reference", "content": content, "number": [1],
                    "sub_items": [], "path": "page.md", "source_path": "page.md",
                    "parent_names": [],
                }}]},
            ]
            result = subprocess.run(
                [executable], input=json.dumps(request),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True, timeout=30,
            )
            if result.returncode != 0:
                raise AssertionError(result.stdout + result.stderr)
            rendered = json.loads(result.stdout)["items"][0]["Chapter"]["content"]
            for text in expected:
                if text not in rendered:
                    raise AssertionError("{}: missing {!r} in native output".format(filename, text))
    return len(selections)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ys", default="./bin/ys", help="Path to yaml-schema.net ys executable")
    parser.add_argument("--meta-schema", type=Path,
                        help="Downloaded official https://yaml-schema.net/yaml-schema.yaml")
    parser.add_argument("--mdbook-memmap",
                        help="Optional migrated native executable supporting hexadecimal string resets")
    args = parser.parse_args()
    if args.meta_schema:
        validate(args.ys, args.meta_schema, SCHEMA, True)
    count = 1
    for example in sorted((ROOT / "examples").glob("*.yaml")):
        validate(args.ys, SCHEMA, example, True)
        count += 1
    with tempfile.TemporaryDirectory(prefix="ipxyaml-") as directory:
        document = Path(directory) / "document.yaml"
        for name, value, valid in cases():
            document.write_text(json.dumps(value))
            try:
                validate(args.ys, SCHEMA, document, valid)
            except AssertionError as error:
                raise AssertionError("{}: {}".format(name, error))
            count += 1
        if args.meta_schema:
            document.write_text(SCHEMA.read_text() + "\nunknownKeyword: true\n")
            validate(args.ys, args.meta_schema, document, False)
            count += 1
    print("Passed {} checks using {}".format(count, args.ys))
    if args.mdbook_memmap:
        count = validate_native(args.mdbook_memmap)
        print("Passed {} native example rendering/resolution checks".format(count))


if __name__ == "__main__":
    main()
