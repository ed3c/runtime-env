"""Validate and consume the repository's environment contract catalog."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Any


VARIABLE_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
SCHEMAS = {
    "variables": "runtime-env/variables/v1",
    "module": "runtime-env/module/v1",
    "profile": "runtime-env/profile/v1",
}


class ContractError(ValueError):
    """A catalog contract is invalid and cannot be consumed safely."""


@dataclass(frozen=True)
class Catalog:
    variables: dict[str, dict[str, Any]]
    modules: dict[str, dict[str, Any]]
    profiles: dict[str, dict[str, Any]]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"missing catalog file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{path} must contain a JSON object")
    return value


def _load_named_documents(directory: Path, kind: str) -> dict[str, dict[str, Any]]:
    if not directory.is_dir():
        raise ContractError(f"missing {kind} directory: {directory}")
    documents: dict[str, dict[str, Any]] = {}
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise ContractError(f"{kind} directory is empty: {directory}")
    for path in paths:
        document = _load_json(path)
        if document.get("schema") != SCHEMAS[kind]:
            raise ContractError(f"{path}: expected schema {SCHEMAS[kind]}")
        identifier = document.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise ContractError(f"{path}: id must be a non-empty string")
        if identifier != path.stem:
            raise ContractError(f"{path}: id {identifier!r} must match filename")
        if identifier in documents:
            raise ContractError(f"duplicate {kind} id: {identifier}")
        documents[identifier] = document
    return documents


def load_catalog(root: Path) -> Catalog:
    variables_document = _load_json(root / "catalog" / "variables.json")
    if variables_document.get("schema") != SCHEMAS["variables"]:
        raise ContractError(
            f"{root / 'catalog' / 'variables.json'}: expected schema {SCHEMAS['variables']}"
        )
    entries = variables_document.get("variables")
    if not isinstance(entries, list) or not entries:
        raise ContractError("variables must be a non-empty array")

    variables: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ContractError("each variable must be an object")
        name = entry.get("name")
        if not isinstance(name, str) or not VARIABLE_NAME.fullmatch(name):
            raise ContractError(f"invalid variable name: {name!r}")
        if name in variables:
            raise ContractError(f"duplicate variable: {name}")
        if not isinstance(entry.get("secret"), bool):
            raise ContractError(f"{name}: secret must be boolean")
        if not isinstance(entry.get("description"), str) or not entry["description"].strip():
            raise ContractError(f"{name}: description must be non-empty")
        variables[name] = entry

    modules = _load_named_documents(root / "modules", "module")
    for module_id, module in modules.items():
        required = module.get("requires", [])
        optional = module.get("optional", [])
        defaults = module.get("defaults", {})
        if not isinstance(required, list) or not isinstance(optional, list):
            raise ContractError(f"module {module_id}: requires and optional must be arrays")
        if not isinstance(defaults, dict):
            raise ContractError(f"module {module_id}: defaults must be an object")
        names = required + optional
        if len(names) != len(set(names)):
            raise ContractError(f"module {module_id}: duplicate variable reference")
        for name in names:
            if name not in variables:
                raise ContractError(f"module {module_id}: unknown variable {name}")
        for name, value in defaults.items():
            if name not in names:
                raise ContractError(f"module {module_id}: default for undeclared variable {name}")
            if variables[name]["secret"]:
                raise ContractError(f"module {module_id}: secret variable {name} cannot have a default")
            if not isinstance(value, str):
                raise ContractError(f"module {module_id}: default for {name} must be a string")

    profiles = _load_named_documents(root / "profiles", "profile")
    for profile_id, profile in profiles.items():
        module_ids = profile.get("modules")
        if not isinstance(module_ids, list) or not module_ids:
            raise ContractError(f"profile {profile_id}: modules must be a non-empty array")
        if len(module_ids) != len(set(module_ids)):
            raise ContractError(f"profile {profile_id}: duplicate module reference")
        for module_id in module_ids:
            if module_id not in modules:
                raise ContractError(f"profile {profile_id}: unknown module {module_id}")

    return Catalog(variables=variables, modules=modules, profiles=profiles)


def _default_catalog_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="runtime-env")
    parser.add_argument("--catalog-root", type=Path, default=_default_catalog_root())
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate every catalog, module, and profile")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        catalog = load_catalog(args.catalog_root.resolve())
    except ContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.command == "validate":
        print(
            f"OK catalog: {len(catalog.variables)} variables, "
            f"{len(catalog.modules)} modules, {len(catalog.profiles)} profiles"
        )
        return 0
    raise AssertionError(f"unhandled command: {args.command}")
