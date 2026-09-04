#!/usr/bin/env python3
"""Conservative backwards-compatibility gate for the public OpenAPI v1 contract."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def load_schema(path: str) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} does not contain an OpenAPI document")
    return data


def parameter_key(parameter: dict[str, Any]) -> tuple[str, str]:
    return str(parameter.get("in", "")), str(parameter.get("name", ""))


def compare_schema(old: Any, new: Any, location: str, errors: list[str]) -> None:
    if not isinstance(old, dict) or not isinstance(new, dict):
        return

    for key in ("type", "format"):
        if key in old and old.get(key) != new.get(key):
            errors.append(f"{location}: {key} changed from {old.get(key)!r} to {new.get(key)!r}")

    old_enum = old.get("enum")
    new_enum = new.get("enum")
    if isinstance(old_enum, list):
        if not isinstance(new_enum, list):
            errors.append(f"{location}: enum constraint was removed")
        else:
            removed = [value for value in old_enum if value not in new_enum]
            if removed:
                errors.append(f"{location}: enum values removed: {removed!r}")

    old_properties = old.get("properties")
    new_properties = new.get("properties")
    if isinstance(old_properties, dict):
        if not isinstance(new_properties, dict):
            errors.append(f"{location}: object properties were removed")
        else:
            for name, old_property in old_properties.items():
                if name not in new_properties:
                    errors.append(f"{location}: property {name!r} was removed")
                    continue
                compare_schema(
                    old_property,
                    new_properties[name],
                    f"{location}.properties.{name}",
                    errors,
                )

    old_required = set(old.get("required") or [])
    new_required = set(new.get("required") or [])
    added_required = sorted(new_required - old_required)
    if added_required:
        errors.append(f"{location}: new required fields added: {added_required!r}")

    for composition_key in ("allOf", "oneOf", "anyOf"):
        old_items = old.get(composition_key)
        new_items = new.get(composition_key)
        if isinstance(old_items, list):
            if not isinstance(new_items, list) or len(new_items) < len(old_items):
                errors.append(f"{location}: {composition_key} alternatives were removed")
                continue
            for index, old_item in enumerate(old_items):
                compare_schema(
                    old_item,
                    new_items[index],
                    f"{location}.{composition_key}[{index}]",
                    errors,
                )

    if "items" in old:
        if "items" not in new:
            errors.append(f"{location}: array items schema was removed")
        else:
            compare_schema(old["items"], new["items"], f"{location}.items", errors)


def compare_operation(path: str, method: str, old: dict[str, Any], new: dict[str, Any], errors: list[str]) -> None:
    old_responses = old.get("responses") or {}
    new_responses = new.get("responses") or {}
    for status_code in old_responses:
        if status_code not in new_responses:
            errors.append(f"{method.upper()} {path}: response {status_code} was removed")

    old_parameters = {
        parameter_key(item): item
        for item in old.get("parameters") or []
        if isinstance(item, dict) and "$ref" not in item
    }
    new_parameters = {
        parameter_key(item): item
        for item in new.get("parameters") or []
        if isinstance(item, dict) and "$ref" not in item
    }
    for key in old_parameters:
        if key not in new_parameters:
            errors.append(f"{method.upper()} {path}: parameter {key!r} was removed")
    for key, parameter in new_parameters.items():
        if key not in old_parameters and parameter.get("required"):
            errors.append(f"{method.upper()} {path}: new required parameter {key!r} was added")

    old_body = old.get("requestBody")
    new_body = new.get("requestBody")
    if old_body is not None and new_body is None:
        errors.append(f"{method.upper()} {path}: request body was removed")
    if isinstance(old_body, dict) and isinstance(new_body, dict):
        if not old_body.get("required") and new_body.get("required"):
            errors.append(f"{method.upper()} {path}: request body became required")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: check_openapi_compat.py BASELINE.yml CURRENT.yml")

    baseline = load_schema(sys.argv[1])
    current = load_schema(sys.argv[2])
    errors: list[str] = []

    old_paths = baseline.get("paths") or {}
    new_paths = current.get("paths") or {}
    for path, old_path_item in old_paths.items():
        new_path_item = new_paths.get(path)
        if not isinstance(new_path_item, dict):
            errors.append(f"path removed: {path}")
            continue
        for method, old_operation in old_path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(old_operation, dict):
                continue
            new_operation = new_path_item.get(method)
            if not isinstance(new_operation, dict):
                errors.append(f"operation removed: {method.upper()} {path}")
                continue
            compare_operation(path, method, old_operation, new_operation, errors)

    old_schemas = ((baseline.get("components") or {}).get("schemas") or {})
    new_schemas = ((current.get("components") or {}).get("schemas") or {})
    for name, old_schema in old_schemas.items():
        new_schema = new_schemas.get(name)
        if not isinstance(new_schema, dict):
            errors.append(f"component schema removed: {name}")
            continue
        compare_schema(old_schema, new_schema, f"components.schemas.{name}", errors)

    if errors:
        print("OpenAPI v1 backwards-compatibility check FAILED:", file=sys.stderr)
        for error in errors:
            print(f" - {error}", file=sys.stderr)
        raise SystemExit(1)

    print(
        "OpenAPI v1 backwards-compatibility check passed: "
        f"{len(old_paths)} baseline paths and {len(old_schemas)} schemas preserved."
    )


if __name__ == "__main__":
    main()
