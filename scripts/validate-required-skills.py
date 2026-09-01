#!/usr/bin/env python3
"""Strict schema validation for required-skills.yml."""

from __future__ import annotations

import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn

import yaml

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SOURCE_RE = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?/[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$"
)
STAGE_TOKEN_RE = re.compile(r"^(?:0[ab]|[0-8])$")
KINDS = {"local", "vendored", "claude-code"}
ENTRY_KEYS = {"name", "kind", "sourcePath", "source", "stage", "note", "fallback"}


def fail(message: str) -> NoReturn:
    raise SystemExit(message)


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def construct_unique_mapping(
    loader: UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as error:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "mapping keys must be hashable",
                key_node.start_mark,
            ) from error
        if duplicate:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"duplicate key: {key}",
                key_node.start_mark,
            )
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_unique_mapping,
)


def load_manifest(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as manifest_file:
            loader = UniqueKeyLoader(manifest_file)
            try:
                return loader.get_single_data()
            finally:
                loader.dispose()
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        fail(f"invalid skill manifest: {error}")


def require_nonempty_string(entry: dict[str, Any], field: str, name: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        fail(f"{name}: {field} must be a non-empty string")
    return value


def validate_source_path(entry: dict[str, Any], name: str, kind: str) -> None:
    source_path = require_nonempty_string(entry, "sourcePath", name)
    path = PurePosixPath(source_path)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        fail(f"{name}: sourcePath must be a safe repository-relative path")
    expected_root = "skills" if kind == "local" else "vendor/skills"
    if source_path != f"{expected_root}/{name}":
        fail(f"{name}: sourcePath must be {expected_root}/{name}")


def validate_stage(entry: dict[str, Any], name: str, kind: str) -> None:
    stage = entry.get("stage")
    if isinstance(stage, bool) or not isinstance(stage, (int, str)):
        fail(f"{name}: stage must be an integer or supported stage string")
    if isinstance(stage, int):
        if not 0 <= stage <= 8:
            fail(f"{name}: stage integer must be between 0 and 8")
        return

    value = stage.strip()
    if kind == "local" and value in {"conductor", "manual"}:
        return
    tokens = [token.strip() for token in value.split(",")]
    if not tokens or any(not token or not STAGE_TOKEN_RE.fullmatch(token) for token in tokens):
        fail(f"{name}: stage must use 0-8, 0a/0b, a comma-separated list, conductor, or manual")


def validate_entry(entry: Any, names: set[str]) -> None:
    if not isinstance(entry, dict):
        fail("every skills entry must be a mapping")
    non_string_keys = [repr(key) for key in entry if not isinstance(key, str)]
    if non_string_keys:
        fail(f"skill entry keys must be strings: {', '.join(non_string_keys)}")
    unknown = sorted(set(entry) - ENTRY_KEYS)
    if unknown:
        fail(f"skill entry has unknown fields: {', '.join(unknown)}")
    name = require_nonempty_string(entry, "name", "skill entry")
    if not NAME_RE.fullmatch(name):
        fail(f"invalid skill name: {name}")
    if name in names:
        fail(f"duplicate skill name: {name}")
    names.add(name)

    kind = require_nonempty_string(entry, "kind", name)
    if kind not in KINDS:
        fail(f"{name}: unsupported kind: {kind}")
    validate_stage(entry, name, kind)

    for field in ("note", "fallback"):
        if field in entry:
            require_nonempty_string(entry, field, name)

    if kind in {"local", "vendored"}:
        validate_source_path(entry, name, kind)
    elif "sourcePath" in entry:
        fail(f"{name}: {kind} entries must not define sourcePath")

    if kind == "vendored":
        source = require_nonempty_string(entry, "source", name)
        if not SOURCE_RE.fullmatch(source):
            fail(f"{name}: source must use owner/repository form")
    elif "source" in entry:
        fail(f"{name}: {kind} entries must not define source")

    if kind in {"vendored", "claude-code"}:
        require_nonempty_string(entry, "fallback", name)


def validate_manifest(data: Any) -> None:
    if not isinstance(data, dict):
        fail("skill manifest must be a mapping")
    if set(data) != {"version", "skills"}:
        fail("skill manifest must contain only version and skills")
    if type(data["version"]) is not int or data["version"] != 1:
        fail("skill manifest version must be the integer 1")
    skills = data["skills"]
    if not isinstance(skills, list) or not skills:
        fail("skill manifest skills must be a non-empty list")
    names: set[str] = set()
    for entry in skills:
        validate_entry(entry, names)


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: validate-required-skills.py REQUIRED_SKILLS_YML")
    path = Path(sys.argv[1])
    validate_manifest(load_manifest(path))


if __name__ == "__main__":
    main()
