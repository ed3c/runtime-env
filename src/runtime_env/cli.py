"""Validate and consume the repository's environment contract catalog."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
import os
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
ALLOWED_FIELDS = {
    "variable": {"name", "secret", "description", "account_url"},
    "module": {"schema", "id", "summary", "requires", "optional", "defaults"},
    "profile": {"schema", "id", "summary", "modules"},
}


class ContractError(ValueError):
    """A catalog contract is invalid and cannot be consumed safely."""


@dataclass(frozen=True)
class Catalog:
    variables: dict[str, dict[str, Any]]
    modules: dict[str, dict[str, Any]]
    profiles: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class SelectedVariable:
    name: str
    required: bool
    default: str | None


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
        unexpected = sorted(set(document) - ALLOWED_FIELDS[kind])
        if unexpected:
            raise ContractError(f"{path}: unexpected fields: {', '.join(unexpected)}")
        if document.get("schema") != SCHEMAS[kind]:
            raise ContractError(f"{path}: expected schema {SCHEMAS[kind]}")
        identifier = document.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise ContractError(f"{path}: id must be a non-empty string")
        if identifier != path.stem:
            raise ContractError(f"{path}: id {identifier!r} must match filename")
        if identifier in documents:
            raise ContractError(f"duplicate {kind} id: {identifier}")
        if not isinstance(document.get("summary"), str) or not document["summary"].strip():
            raise ContractError(f"{path}: summary must be non-empty")
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
        unexpected = sorted(set(entry) - ALLOWED_FIELDS["variable"])
        if unexpected:
            raise ContractError(f"unexpected fields on {name}: {', '.join(unexpected)}")
        if not isinstance(entry.get("secret"), bool):
            raise ContractError(f"{name}: secret must be boolean")
        if not isinstance(entry.get("description"), str) or not entry["description"].strip():
            raise ContractError(f"{name}: description must be non-empty")
        account_url = entry.get("account_url")
        if account_url is not None and (
            not isinstance(account_url, str) or not account_url.startswith("https://")
        ):
            raise ContractError(f"{name}: account_url must be an HTTPS URL")
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


def select_variables(
    catalog: Catalog, *, profile_id: str | None, include_all: bool
) -> list[SelectedVariable]:
    if include_all:
        return [
            SelectedVariable(name=name, required=False, default=None)
            for name in sorted(catalog.variables)
        ]
    if profile_id not in catalog.profiles:
        raise ContractError(f"unknown profile: {profile_id}")

    selected: dict[str, SelectedVariable] = {}
    for module_id in catalog.profiles[profile_id]["modules"]:
        module = catalog.modules[module_id]
        required_names = set(module.get("requires", []))
        defaults = module.get("defaults", {})
        for name in module.get("requires", []) + module.get("optional", []):
            current = selected.get(name)
            default = defaults.get(name)
            if current and current.default is not None and default is not None and current.default != default:
                raise ContractError(
                    f"profile {profile_id}: conflicting defaults for {name}: "
                    f"{current.default!r} and {default!r}"
                )
            selected[name] = SelectedVariable(
                name=name,
                required=(current.required if current else False) or name in required_names,
                default=default if default is not None else (current.default if current else None),
            )
    return [selected[name] for name in sorted(selected)]


def render_dotenv(catalog: Catalog, variables: list[SelectedVariable]) -> str:
    lines = ["# Generated by runtime-env. Values are placeholders, never credentials."]
    for selected in variables:
        metadata = catalog.variables[selected.name]
        requirement = "required" if selected.required else "optional"
        sensitivity = "secret" if metadata["secret"] else "non-secret"
        lines.append(f"# {requirement}; {sensitivity}: {metadata['description']}")
        lines.append(f"{selected.name}={selected.default or ''}")
    return "\n".join(lines) + "\n"


def render_github_actions(catalog: Catalog, variables: list[SelectedVariable]) -> str:
    lines = ["# Generated by runtime-env. Add this mapping to a job or step.", "env:"]
    for selected in variables:
        metadata = catalog.variables[selected.name]
        if metadata["secret"]:
            value = "${{ secrets." + selected.name + " }}"
        elif selected.default is not None:
            value = json.dumps(selected.default)
        else:
            value = "${{ vars." + selected.name + " }}"
        lines.append(f"  {selected.name}: {value}")
    return "\n".join(lines) + "\n"


def load_dotenv(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ContractError(f"cannot read env file {path}: {exc.strerror}") from exc
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ContractError(f"{path}:{line_number}: expected NAME=VALUE")
        name, value = line.split("=", 1)
        name = name.strip()
        if not VARIABLE_NAME.fullmatch(name):
            raise ContractError(f"{path}:{line_number}: invalid variable name")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[name] = value
    return values


def check_environment(
    variables: list[SelectedVariable], *, env_file: Path | None
) -> tuple[list[str], list[str]]:
    configured = load_dotenv(env_file) if env_file else {}
    configured.update(os.environ)
    lines: list[str] = []
    missing_required: list[str] = []
    for selected in variables:
        present = bool(configured.get(selected.name) or selected.default)
        requirement = "required" if selected.required else "optional"
        state = "PRESENT" if present else "MISSING"
        lines.append(f"{state} {requirement}: {selected.name}")
        if selected.required and not present:
            missing_required.append(selected.name)
    return lines, missing_required


def _default_catalog_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="runtime-env")
    parser.add_argument("--catalog-root", type=Path, default=_default_catalog_root())
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate every catalog, module, and profile")
    render_parser = subparsers.add_parser("render", help="render a secret-free environment template")
    selection = render_parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--profile")
    selection.add_argument("--all", action="store_true", dest="include_all")
    render_parser.add_argument("--format", choices=("dotenv", "github-actions"), required=True)
    check_parser = subparsers.add_parser("check", help="check required names without printing values")
    check_parser.add_argument("--profile", required=True)
    check_parser.add_argument("--env-file", type=Path)
    list_parser = subparsers.add_parser("list", help="discover catalog entries or profile requirements")
    list_selection = list_parser.add_mutually_exclusive_group(required=True)
    list_selection.add_argument("--kind", choices=("variables", "modules", "profiles"))
    list_selection.add_argument("--profile")
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
    if args.command == "render":
        try:
            selected = select_variables(
                catalog,
                profile_id=args.profile,
                include_all=args.include_all,
            )
        except ContractError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        if args.format == "dotenv":
            sys.stdout.write(render_dotenv(catalog, selected))
        else:
            sys.stdout.write(render_github_actions(catalog, selected))
        return 0
    if args.command == "check":
        try:
            selected = select_variables(
                catalog,
                profile_id=args.profile,
                include_all=False,
            )
            lines, missing_required = check_environment(selected, env_file=args.env_file)
        except ContractError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        for line in lines:
            print(line)
        if missing_required:
            return 3
        print(f"OK profile {args.profile}: all required variables are present")
        return 0
    if args.command == "list":
        if args.kind == "variables":
            for name, metadata in sorted(catalog.variables.items()):
                sensitivity = "secret" if metadata["secret"] else "non-secret"
                print(f"{name}\t{sensitivity}\t{metadata['description']}")
            return 0
        if args.kind in {"modules", "profiles"}:
            documents = catalog.modules if args.kind == "modules" else catalog.profiles
            for identifier, document in sorted(documents.items()):
                print(f"{identifier}\t{document['summary']}")
            return 0
        try:
            selected = select_variables(
                catalog,
                profile_id=args.profile,
                include_all=False,
            )
        except ContractError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        for variable in selected:
            sensitivity = "secret" if catalog.variables[variable.name]["secret"] else "non-secret"
            requirement = "required" if variable.required else "optional"
            default = variable.default if variable.default is not None else "-"
            print(f"{requirement}\t{sensitivity}\t{variable.name}\t{default}")
        return 0
    raise AssertionError(f"unhandled command: {args.command}")
