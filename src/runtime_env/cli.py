"""Validate and consume the repository's environment contract catalog."""

from __future__ import annotations

import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import hmac
import io
import json
from dataclasses import dataclass
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any
from urllib.parse import urlsplit, urlunsplit


VARIABLE_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
BINDING_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ENV_REFERENCE = re.compile(
    r"\$\{([A-Z][A-Z0-9_]*):[-+?=][^}]*\}|"
    r"process\.env\.([A-Z][A-Z0-9_]*)|"
    r"(?:getenv|environ\.get)\([\"']([A-Z][A-Z0-9_]*)[\"']|"
    r"environ\[[\"']([A-Z][A-Z0-9_]*)[\"']\]"
)
REPO_MODULE_REFERENCE = re.compile(
    r"(?<![A-Za-z0-9_.-])((?:kb-ingest|indexing)/[A-Za-z0-9_./-]+)"
)
SCHEMAS = {
    "variables": "runtime-env/variables/v1",
    "module": "runtime-env/module/v1",
    "profile": "runtime-env/profile/v1",
    "workload": "runtime-env/workload/v2",
    "policy": "runtime-env/carrier-policy/v1",
}
ALLOWED_FIELDS = {
    "variables": {"schema", "variables"},
    "variable": {"name", "secret", "runtime_scope", "description", "account_url"},
    "module": {"schema", "id", "summary", "requires", "optional", "defaults"},
    "profile": {"schema", "id", "summary", "modules"},
    "workload": {
        "schema",
        "id",
        "summary",
        "profile",
        "host",
        "entrypoints",
        "entrypoint_environment",
        "acceptance_entrypoints",
        "public_test_entrypoints",
        "broker_adapters",
        "clean_catalog_entrypoints",
        "secret_delivery",
        "agent_secret_access",
        "mutation",
        "evidence",
    },
    "policy": {
        "schema",
        "id",
        "summary",
        "carrier",
        "config_home_env",
        "settings_file",
        "required_settings",
        "forbidden_environment",
        "external_requirements",
        "receipt_commands",
    },
}
REQUIRED_FIELDS = {
    "variables": {"schema", "variables"},
    "variable": {"name", "secret", "runtime_scope", "description"},
    "module": {"schema", "id", "summary", "requires", "optional", "defaults"},
    "profile": {"schema", "id", "summary", "modules"},
    "workload": {
        "schema",
        "id",
        "summary",
        "profile",
        "host",
        "entrypoints",
        "entrypoint_environment",
        "acceptance_entrypoints",
        "secret_delivery",
        "agent_secret_access",
        "mutation",
        "evidence",
    },
    "policy": {
        "schema",
        "id",
        "summary",
        "carrier",
        "config_home_env",
        "settings_file",
        "required_settings",
        "forbidden_environment",
        "external_requirements",
        "receipt_commands",
    },
}


class ContractError(ValueError):
    """A catalog contract is invalid and cannot be consumed safely."""


class MissingConfiguration(ContractError):
    """A valid workload cannot start because required configuration is absent."""


@dataclass(frozen=True)
class Catalog:
    variables: dict[str, dict[str, Any]]
    modules: dict[str, dict[str, Any]]
    profiles: dict[str, dict[str, Any]]
    workloads: dict[str, dict[str, Any]]
    policies: dict[str, dict[str, Any]]
    root: Path | None = None


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
        missing = sorted(REQUIRED_FIELDS[kind] - set(document))
        if missing:
            raise ContractError(
                f"{path}: missing required fields: {', '.join(missing)}"
            )
        if document.get("schema") != SCHEMAS[kind]:
            raise ContractError(f"{path}: expected schema {SCHEMAS[kind]}")
        identifier = document.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise ContractError(f"{path}: id must be a non-empty string")
        if identifier != path.stem:
            raise ContractError(f"{path}: id {identifier!r} must match filename")
        if identifier in documents:
            raise ContractError(f"duplicate {kind} id: {identifier}")
        if (
            not isinstance(document.get("summary"), str)
            or not document["summary"].strip()
        ):
            raise ContractError(f"{path}: summary must be non-empty")
        documents[identifier] = document
    return documents


def load_catalog(root: Path) -> Catalog:
    variables_document = _load_json(root / "catalog" / "variables.json")
    unexpected = sorted(set(variables_document) - ALLOWED_FIELDS["variables"])
    if unexpected:
        raise ContractError(
            f"variables catalog: unexpected fields: {', '.join(unexpected)}"
        )
    missing = sorted(REQUIRED_FIELDS["variables"] - set(variables_document))
    if missing:
        raise ContractError(
            f"variables catalog: missing required fields: {', '.join(missing)}"
        )
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
        missing = sorted(REQUIRED_FIELDS["variable"] - set(entry))
        if missing:
            raise ContractError(
                f"{name}: missing required fields: {', '.join(missing)}"
            )
        if not isinstance(entry.get("secret"), bool):
            raise ContractError(f"{name}: secret must be boolean")
        if entry.get("runtime_scope") not in {
            "local-only",
            "cloud-runtime",
            "portable",
        }:
            raise ContractError(
                f"{name}: runtime_scope must be local-only, cloud-runtime, or portable"
            )
        if (
            not isinstance(entry.get("description"), str)
            or not entry["description"].strip()
        ):
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
            raise ContractError(
                f"module {module_id}: requires and optional must be arrays"
            )
        if any(not isinstance(name, str) for name in required + optional):
            raise ContractError(
                f"module {module_id}: variable references must be strings"
            )
        if not isinstance(defaults, dict):
            raise ContractError(f"module {module_id}: defaults must be an object")
        if any(not isinstance(name, str) for name in defaults):
            raise ContractError(f"module {module_id}: default names must be strings")
        names = required + optional
        if len(names) != len(set(names)):
            raise ContractError(f"module {module_id}: duplicate variable reference")
        for name in names:
            if name not in variables:
                raise ContractError(f"module {module_id}: unknown variable {name}")
        for name, value in defaults.items():
            if name not in names:
                raise ContractError(
                    f"module {module_id}: default for undeclared variable {name}"
                )
            if variables[name]["secret"]:
                raise ContractError(
                    f"module {module_id}: secret variable {name} cannot have a default"
                )
            if not isinstance(value, str):
                raise ContractError(
                    f"module {module_id}: default for {name} must be a string"
                )

    profiles = _load_named_documents(root / "profiles", "profile")
    for profile_id, profile in profiles.items():
        module_ids = profile.get("modules")
        if not isinstance(module_ids, list) or not module_ids:
            raise ContractError(
                f"profile {profile_id}: modules must be a non-empty array"
            )
        if any(not isinstance(module_id, str) for module_id in module_ids):
            raise ContractError(
                f"profile {profile_id}: module references must be strings"
            )
        if len(module_ids) != len(set(module_ids)):
            raise ContractError(f"profile {profile_id}: duplicate module reference")
        for module_id in module_ids:
            if module_id not in modules:
                raise ContractError(f"profile {profile_id}: unknown module {module_id}")

    workload_directory = root / "workloads"
    workloads = (
        _load_named_documents(workload_directory, "workload")
        if workload_directory.is_dir()
        else {}
    )
    for workload_id, workload in workloads.items():
        if workload.get("profile") not in profiles:
            raise ContractError(
                f"workload {workload_id}: unknown profile {workload.get('profile')}"
            )
        if workload.get("host") not in {"local-macos", "openshell"}:
            raise ContractError(f"workload {workload_id}: unsupported host")
        if workload.get("secret_delivery") not in {
            "none",
            "openshell-provider",
            "broker-only",
        }:
            raise ContractError(f"workload {workload_id}: unsupported secret delivery")
        if workload.get("agent_secret_access") != "denied":
            raise ContractError(
                f"workload {workload_id}: agent secret access must be denied"
            )
        if workload.get("mutation") not in {
            "read-only",
            "workspace",
            "external-release",
        }:
            raise ContractError(f"workload {workload_id}: unsupported mutation class")
        entrypoints = workload.get("entrypoints")
        if not isinstance(entrypoints, dict) or not entrypoints:
            raise ContractError(
                f"workload {workload_id}: entrypoints must be a non-empty object"
            )
        for entrypoint_id, command in entrypoints.items():
            if not isinstance(entrypoint_id, str) or not entrypoint_id:
                raise ContractError(f"workload {workload_id}: invalid entrypoint id")
            if (
                not isinstance(command, list)
                or not command
                or any(not isinstance(part, str) or not part for part in command)
            ):
                raise ContractError(
                    f"workload {workload_id}: entrypoint {entrypoint_id} must be a string array"
                )
        acceptance_entrypoints = workload.get("acceptance_entrypoints")
        if (
            not isinstance(acceptance_entrypoints, list)
            or not acceptance_entrypoints
            or any(
                not isinstance(entrypoint_id, str) or not entrypoint_id
                for entrypoint_id in acceptance_entrypoints
            )
            or len(acceptance_entrypoints) != len(set(acceptance_entrypoints))
        ):
            raise ContractError(
                f"workload {workload_id}: acceptance_entrypoints must be a "
                "non-empty unique string array"
            )
        unknown_acceptance = sorted(set(acceptance_entrypoints) - set(entrypoints))
        if unknown_acceptance:
            raise ContractError(
                f"workload {workload_id}: acceptance_entrypoints references "
                f"unknown entrypoints: {', '.join(unknown_acceptance)}"
            )
        unresolved_acceptance = sorted(
            entrypoint_id
            for entrypoint_id in acceptance_entrypoints
            if any(
                re.search(r"<[^>]+>", argument)
                for argument in entrypoints[entrypoint_id]
            )
        )
        if unresolved_acceptance:
            raise ContractError(
                f"workload {workload_id}: acceptance entrypoints contain unresolved "
                f"placeholders: {', '.join(unresolved_acceptance)}"
            )
        public_test_entrypoints = workload.get("public_test_entrypoints")
        if public_test_entrypoints is not None:
            if (
                not isinstance(public_test_entrypoints, list)
                or not public_test_entrypoints
                or any(
                    not isinstance(entrypoint_id, str) or not entrypoint_id
                    for entrypoint_id in public_test_entrypoints
                )
                or len(public_test_entrypoints)
                != len(set(public_test_entrypoints))
            ):
                raise ContractError(
                    f"workload {workload_id}: public_test_entrypoints must be a "
                    "non-empty unique string array"
                )
            unknown_public_tests = sorted(
                set(public_test_entrypoints) - set(acceptance_entrypoints)
            )
            if unknown_public_tests:
                raise ContractError(
                    f"workload {workload_id}: public_test_entrypoints must be "
                    "acceptance entrypoints: " + ", ".join(unknown_public_tests)
                )
        broker_adapters = workload.get("broker_adapters")
        if workload["secret_delivery"] == "broker-only":
            if not isinstance(broker_adapters, dict) or not broker_adapters:
                raise ContractError(
                    f"workload {workload_id}: broker-only delivery requires "
                    "dedicated broker_adapters"
                )
            unknown_adapters = sorted(set(broker_adapters) - set(entrypoints))
            if unknown_adapters:
                raise ContractError(
                    f"workload {workload_id}: broker_adapters references unknown "
                    f"entrypoints: {', '.join(unknown_adapters)}"
                )
            for entrypoint_id, adapter in broker_adapters.items():
                if not isinstance(adapter, dict) or set(adapter) != {
                    "implementation",
                    "private_state",
                    "receipt",
                }:
                    raise ContractError(
                        f"workload {workload_id}: broker_adapters.{entrypoint_id} "
                        "must contain implementation, private_state, and receipt"
                    )
                if (
                    not isinstance(adapter["implementation"], str)
                    or not adapter["implementation"]
                    or not isinstance(adapter["receipt"], str)
                    or not adapter["receipt"]
                    or not isinstance(adapter["private_state"], list)
                    or not adapter["private_state"]
                    or any(
                        not isinstance(item, str) or not item
                        for item in adapter["private_state"]
                    )
                ):
                    raise ContractError(
                        f"workload {workload_id}: broker_adapters.{entrypoint_id} "
                        "has invalid adapter metadata"
                    )
        elif broker_adapters is not None:
            raise ContractError(
                f"workload {workload_id}: broker_adapters is only valid for "
                "broker-only delivery"
            )
        entrypoint_environment = workload.get("entrypoint_environment")
        if not isinstance(entrypoint_environment, dict) or set(
            entrypoint_environment
        ) != set(entrypoints):
            raise ContractError(
                f"workload {workload_id}: entrypoint_environment must map every entrypoint exactly"
            )
        profile_variables = {
            selected.name
            for selected in select_variables(
                Catalog(variables, modules, profiles, {}, {}),
                profile_id=workload["profile"],
                include_all=False,
            )
        }
        for entrypoint_id, names in entrypoint_environment.items():
            if (
                not isinstance(names, list)
                or any(not isinstance(name, str) or not name for name in names)
                or len(names) != len(set(names))
            ):
                raise ContractError(
                    f"workload {workload_id}: entrypoint_environment.{entrypoint_id} "
                    "must be a unique string array"
                )
            unknown = sorted(set(names) - profile_variables)
            if unknown:
                raise ContractError(
                    f"workload {workload_id}: entrypoint_environment.{entrypoint_id} "
                    f"references variables outside profile: {', '.join(unknown)}"
                )
        clean_catalog_entrypoints = workload.get("clean_catalog_entrypoints", [])
        if (
            not isinstance(clean_catalog_entrypoints, list)
            or any(
                not isinstance(entrypoint_id, str) or not entrypoint_id
                for entrypoint_id in clean_catalog_entrypoints
            )
            or len(clean_catalog_entrypoints) != len(set(clean_catalog_entrypoints))
        ):
            raise ContractError(
                f"workload {workload_id}: clean_catalog_entrypoints must be a "
                "unique string array"
            )
        unknown_clean = sorted(set(clean_catalog_entrypoints) - set(entrypoints))
        if unknown_clean:
            raise ContractError(
                f"workload {workload_id}: clean_catalog_entrypoints references "
                f"unknown entrypoints: {', '.join(unknown_clean)}"
            )
        evidence = workload.get("evidence")
        if not isinstance(evidence, dict) or set(evidence) != {"receipt", "control"}:
            raise ContractError(
                f"workload {workload_id}: evidence must contain receipt and control"
            )
        if any(
            not isinstance(evidence[name], str) or not evidence[name]
            for name in evidence
        ):
            raise ContractError(
                f"workload {workload_id}: evidence paths must be non-empty"
            )

    policy_directory = root / "policies"
    policies = (
        _load_named_documents(policy_directory, "policy")
        if policy_directory.is_dir()
        else {}
    )
    for policy_id, policy in policies.items():
        if policy.get("carrier") not in {"claude-code", "codex-cli"}:
            raise ContractError(f"policy {policy_id}: unsupported carrier")
        config_home_env = policy.get("config_home_env")
        if config_home_env not in variables or variables[config_home_env]["secret"]:
            raise ContractError(f"policy {policy_id}: invalid config home variable")
        if (
            not isinstance(policy.get("settings_file"), str)
            or not policy["settings_file"]
        ):
            raise ContractError(f"policy {policy_id}: settings_file must be non-empty")
        if (
            not isinstance(policy.get("required_settings"), dict)
            or not policy["required_settings"]
        ):
            raise ContractError(
                f"policy {policy_id}: required_settings must be non-empty"
            )
        for field in (
            "forbidden_environment",
            "external_requirements",
            "receipt_commands",
        ):
            values = policy.get(field)
            if (
                not isinstance(values, list)
                or not values
                or any(not isinstance(value, str) or not value for value in values)
            ):
                raise ContractError(
                    f"policy {policy_id}: {field} must be a non-empty string array"
                )

    catalog = Catalog(
        variables=variables,
        modules=modules,
        profiles=profiles,
        workloads=workloads,
        policies=policies,
        root=root.resolve(),
    )
    for profile_id in profiles:
        select_variables(catalog, profile_id=profile_id, include_all=False)
    return catalog


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
            if (
                current
                and current.default is not None
                and default is not None
                and current.default != default
            ):
                raise ContractError(
                    f"profile {profile_id}: conflicting defaults for {name}: "
                    f"{current.default!r} and {default!r}"
                )
            selected[name] = SelectedVariable(
                name=name,
                required=(current.required if current else False)
                or name in required_names,
                default=default
                if default is not None
                else (current.default if current else None),
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


LOCAL_ENV_SECTIONS = (
    ("local-only", "LOCAL-ONLY HOST SETTINGS"),
    ("cloud-runtime", "CLOUD / REMOTE RUNTIME SETTINGS"),
    ("portable", "PORTABLE RUNTIME SETTINGS"),
)


def render_local_dotenv(catalog: Catalog, values: dict[str, str] | None = None) -> str:
    preserved = values or {}
    lines = [
        "# Managed by runtime-env. This host-only file must remain mode 0600 and untracked.",
        "# Agents may inspect names and presence states through the broker, never these values.",
    ]
    for scope, heading in LOCAL_ENV_SECTIONS:
        lines.extend(("", f"# === {heading} ==="))
        for name, metadata in sorted(catalog.variables.items()):
            if metadata["runtime_scope"] != scope:
                continue
            sensitivity = "secret" if metadata["secret"] else "non-secret"
            lines.append(f"# {sensitivity}: {metadata['description']}")
            lines.append(f"{name}={preserved.get(name, '')}")
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
        if name in values:
            raise ContractError(
                f"{path}:{line_number}: duplicate assignment for {name}"
            )
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


def _git(root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise ContractError(f"cannot run git: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise ContractError(detail)
    return result.stdout.strip()


def _ignored_files_fingerprint(root: Path) -> str:
    """Hash ignored consumer bytes so L5 cannot hide workspace mutations."""
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "--others",
                "--ignored",
                "--exclude-standard",
                "-z",
            ],
            check=False,
            capture_output=True,
        )
    except OSError as exc:
        raise ContractError(f"cannot inventory ignored consumer files: {exc}") from exc
    if result.returncode != 0:
        raise ContractError("cannot inventory ignored consumer files")

    digest = hashlib.sha256()
    for encoded_relative in sorted(part for part in result.stdout.split(b"\0") if part):
        relative = Path(os.fsdecode(encoded_relative))
        if relative.is_absolute() or ".." in relative.parts:
            raise ContractError("git returned an unsafe ignored consumer path")
        path = root / relative
        try:
            metadata = path.lstat()
        except OSError as exc:
            raise ContractError(
                "ignored consumer file changed during acceptance inventory"
            ) from exc
        digest.update(encoded_relative)
        digest.update(b"\0")
        digest.update(str(stat.S_IFMT(metadata.st_mode)).encode("ascii"))
        digest.update(b"\0")
        if path.is_symlink():
            digest.update(os.fsencode(os.readlink(path)))
        elif path.is_file():
            try:
                with path.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
            except OSError as exc:
                raise ContractError(
                    "cannot hash ignored consumer file during acceptance"
                ) from exc
        else:
            digest.update(b"directory")
        digest.update(b"\0")
    return digest.hexdigest()


def _repository_url(remote: str) -> str:
    if remote.startswith("git@") and ":" in remote:
        host, path = remote[4:].split(":", 1)
        remote = f"https://{host}/{path}"
    elif remote.startswith("ssh://git@"):
        parsed = urlsplit(remote)
        remote = urlunsplit(("https", parsed.hostname or "", parsed.path, "", ""))

    parsed = urlsplit(remote)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ContractError("origin must be a credential-free HTTPS or git@ SSH URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ContractError(
            "origin URL must not contain credentials, query, or fragment"
        )
    path = parsed.path.removesuffix(".git").rstrip("/")
    if not path or path == "/":
        raise ContractError("origin URL must identify a repository")
    return urlunsplit(("https", parsed.hostname, path, "", ""))


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _canonical_json(document: dict[str, Any]) -> str:
    return json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def _load_consumer_requirements(path: Path) -> dict[str, Any]:
    document = _load_json(path)
    expected = {
        "schema",
        "binding",
        "profile",
        "required_modules",
        "workload",
        "policies",
    }
    if set(document) != expected:
        raise ContractError(
            "consumer requirements must contain exactly schema, binding, profile, "
            "required_modules, workload, and policies"
        )
    if document.get("schema") != "runtime-env/consumer-requirements/v1":
        raise ContractError(
            "consumer requirements schema must be runtime-env/consumer-requirements/v1"
        )
    for field in ("binding", "profile"):
        value = document.get(field)
        if not isinstance(value, str) or not value:
            raise ContractError(f"consumer requirements {field} must be non-empty")
    if not BINDING_ID.fullmatch(document["binding"]):
        raise ContractError("consumer requirements binding has an invalid id")
    for field in ("required_modules", "policies"):
        value = document.get(field)
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item for item in value
        ):
            raise ContractError(f"consumer requirements {field} must be a name array")
        if len(value) != len(set(value)):
            raise ContractError(f"consumer requirements {field} must be unique")
    if document["workload"] is not None and not isinstance(document["workload"], str):
        raise ContractError("consumer requirements workload must be a name or null")
    return document


def _binding_artifacts(
    *,
    root: Path,
    catalog: Catalog,
    profile_id: str,
    binding_id: str,
    workload_id: str | None,
    policy_ids: list[str],
    requirements_sha256: str | None = None,
    required_modules: list[str] | None = None,
) -> dict[Path, str]:
    if not BINDING_ID.fullmatch(binding_id):
        raise ContractError(
            "binding must use lowercase letters, digits, and single hyphen separators"
        )
    if len(set(policy_ids)) != len(policy_ids):
        raise ContractError("policy ids must be unique")
    top_level = Path(_git(root, "rev-parse", "--show-toplevel")).resolve()
    if top_level != root.resolve():
        raise ContractError("catalog root must be the root of its git repository")
    if _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ContractError("catalog repository must be clean before synchronization")

    selected = select_variables(catalog, profile_id=profile_id, include_all=False)
    profile_modules = catalog.profiles[profile_id]["modules"]
    if required_modules is not None and profile_modules != required_modules:
        raise ContractError(
            f"profile {profile_id} module closure differs from consumer requirements: "
            f"wanted {required_modules}, resolved {profile_modules}"
        )
    modules = []
    for module_id in profile_modules:
        module = catalog.modules[module_id]
        modules.append(
            {
                "content_sha256": _sha256(_canonical_json(module)),
                "id": module_id,
                "interface_version": module["schema"],
            }
        )
    example = render_dotenv(catalog, selected)
    variables: list[dict[str, Any]] = []
    for item in selected:
        metadata = catalog.variables[item.name]
        variable: dict[str, Any] = {
            "description": metadata["description"],
            "name": item.name,
            "required": item.required,
            "runtime_scope": metadata["runtime_scope"],
            "secret": metadata["secret"],
        }
        if metadata.get("account_url") is not None:
            variable["account_url"] = metadata["account_url"]
        if item.default is not None:
            variable["default"] = item.default
        variables.append(variable)

    binding_path = Path(".runtime-env") / "bindings" / f"{binding_id}.json"
    example_path = Path(".runtime-env") / "examples" / f"{binding_id}.env.example"
    document: dict[str, Any] = {
        "binding": binding_id,
        "modules": modules,
        "profile": profile_id,
        "projections": {
            "policies": [
                (Path(".runtime-env") / "policies" / f"{policy_id}.json").as_posix()
                for policy_id in policy_ids
            ],
            "workload": (
                (Path(".runtime-env") / "workloads" / f"{binding_id}.json").as_posix()
                if workload_id is not None
                else None
            ),
        },
        "render": {
            "format": "dotenv",
            "path": example_path.as_posix(),
            "sha256": _sha256(example),
        },
        "requirements_sha256": requirements_sha256,
        "schema": "runtime-env/consumer-binding/v2",
        "source": {
            "commit": _git(root, "rev-parse", "HEAD"),
            "repository": _repository_url(_git(root, "remote", "get-url", "origin")),
            "tree": _git(root, "rev-parse", "HEAD^{tree}"),
        },
        "variables": variables,
    }
    document["content_sha256"] = _sha256(_canonical_json(document))
    binding = json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    artifacts = {binding_path: binding, example_path: example}
    if workload_id is not None:
        workload = catalog.workloads.get(workload_id)
        if workload is None:
            raise ContractError(f"unknown workload: {workload_id}")
        if workload["profile"] != profile_id:
            raise ContractError(
                f"workload {workload_id}: profile {workload['profile']} does not match {profile_id}"
            )
        workload_path = Path(".runtime-env") / "workloads" / f"{binding_id}.json"
        projection: dict[str, Any] = {
            "binding": binding_id,
            "schema": "runtime-env/consumer-workload/v1",
            "source": {
                "commit": _git(root, "rev-parse", "HEAD"),
                "repository": _repository_url(
                    _git(root, "remote", "get-url", "origin")
                ),
                "tree": _git(root, "rev-parse", "HEAD^{tree}"),
            },
            "workload": workload,
        }
        projection["content_sha256"] = _sha256(_canonical_json(projection))
        artifacts[workload_path] = (
            json.dumps(projection, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        )
    for policy_id in policy_ids:
        policy = catalog.policies.get(policy_id)
        if policy is None:
            raise ContractError(f"unknown policy: {policy_id}")
        policy_path = Path(".runtime-env") / "policies" / f"{policy_id}.json"
        projection = {
            "binding": binding_id,
            "schema": "runtime-env/consumer-policy/v1",
            "source": {
                "commit": _git(root, "rev-parse", "HEAD"),
                "repository": _repository_url(
                    _git(root, "remote", "get-url", "origin")
                ),
                "tree": _git(root, "rev-parse", "HEAD^{tree}"),
            },
            "policy": policy,
        }
        projection["content_sha256"] = _sha256(_canonical_json(projection))
        artifacts[policy_path] = (
            json.dumps(projection, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        )
    return artifacts


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temporary_name, path)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass


def sync_consumer(
    *,
    root: Path,
    catalog: Catalog,
    profile_id: str,
    binding_id: str,
    workload_id: str | None,
    policy_ids: list[str],
    target_root: Path,
    apply: bool,
    check: bool,
    requirements_sha256: str | None = None,
    required_modules: list[str] | None = None,
) -> int:
    target = target_root.resolve()
    target_top_level = Path(_git(target, "rev-parse", "--show-toplevel")).resolve()
    if target_top_level != target:
        raise ContractError("target root must be the root of its git repository")
    artifacts = _binding_artifacts(
        root=root,
        catalog=catalog,
        profile_id=profile_id,
        binding_id=binding_id,
        workload_id=workload_id,
        policy_ids=policy_ids,
        requirements_sha256=requirements_sha256,
        required_modules=required_modules,
    )
    drift = False
    for relative_path, expected in artifacts.items():
        destination = target / relative_path
        current = (
            destination.read_text(encoding="utf-8") if destination.is_file() else None
        )
        if current == expected:
            state = "UNCHANGED"
        elif current is None:
            state = "MISSING" if check else "WOULD-CREATE"
            drift = True
        else:
            state = "DRIFT" if check else "WOULD-UPDATE"
            drift = True
        if apply and current != expected:
            _atomic_write(destination, expected)
            state = "CREATED" if current is None else "UPDATED"
        print(f"{state} {relative_path.as_posix()}")
    if check and drift:
        return 2
    return 0


def _default_catalog_root() -> Path:
    return Path(__file__).resolve().parents[2]


def doctor_local_env(*, catalog: Catalog, env_file: Path, catalog_root: Path) -> int:
    path = env_file.expanduser().absolute()
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ContractError(f"cannot inspect env file {path}: {exc.strerror}") from exc
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise ContractError("local env must be a regular file, not a symlink")
    if metadata.st_uid != os.getuid():
        raise ContractError("local env must be owned by the current user")
    if stat.S_IMODE(metadata.st_mode) != 0o600:
        raise ContractError("local env must have mode 0600")

    values = load_dotenv(path)
    unknown = sorted(set(values) - set(catalog.variables))
    if unknown:
        raise ContractError(f"local env contains unknown names: {', '.join(unknown)}")

    root = catalog_root.resolve()
    resolved_path = path.resolve()
    try:
        relative = resolved_path.relative_to(root)
    except ValueError:
        relative = None
    if relative is not None:
        ignored = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "--quiet", "--", str(relative)],
            check=False,
        )
        if ignored.returncode != 0:
            raise ContractError("local env inside the catalog must be ignored by Git")

    for name in sorted(values):
        state = "PRESENT" if values[name] else "EMPTY"
        print(f"{state} {name} scope={catalog.variables[name]['runtime_scope']}")
    print(f"OK local env metadata: {len(values)} declared names, values redacted")
    return 0


def _load_private_dotenv(*, catalog: Catalog, env_file: Path) -> dict[str, str]:
    path = env_file.expanduser().absolute()
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ContractError(f"cannot inspect env file {path}: {exc.strerror}") from exc
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise ContractError("workload env file must be a regular file, not a symlink")
    if metadata.st_uid != os.getuid():
        raise ContractError("workload env file must be owned by the current user")
    if stat.S_IMODE(metadata.st_mode) != 0o600:
        raise ContractError("workload env file must have mode 0600")
    values = load_dotenv(path)
    unknown = sorted(set(values) - set(catalog.variables))
    if unknown:
        raise ContractError(
            f"workload env file contains unknown names: {', '.join(unknown)}"
        )
    return values


def reconcile_local_env(*, catalog: Catalog, env_file: Path) -> int:
    path = env_file.expanduser().absolute()
    values = _load_private_dotenv(catalog=catalog, env_file=path)
    missing = sorted(set(catalog.variables) - set(values))
    content = render_local_dotenv(catalog, values)
    if path.read_text(encoding="utf-8") == content:
        print(
            "UNCHANGED local env: sections and catalog names are current, values redacted"
        )
        return 0
    _atomic_write(path, content)
    path.chmod(0o600)
    print(
        f"RECONCILED local env: organized sections, added {len(missing)} empty names, "
        "values redacted"
    )
    return 0


def set_local_env_path(
    *, catalog: Catalog, env_file: Path, name: str, value: Path
) -> int:
    path = env_file.expanduser().absolute()
    _load_private_dotenv(catalog=catalog, env_file=path)
    metadata = catalog.variables.get(name)
    if metadata is None:
        raise ContractError(f"unknown variable: {name}")
    if metadata["secret"]:
        raise ContractError("set-path accepts only declared non-secret path variables")
    resolved = value.expanduser().absolute()
    if not resolved.exists():
        raise ContractError(f"set-path target does not exist for {name}")
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    assignment = re.compile(rf"^\s*(?:export\s+)?{re.escape(name)}\s*=")
    indexes = [index for index, line in enumerate(raw_lines) if assignment.match(line)]
    if len(indexes) > 1:
        raise ContractError(f"local env contains duplicate assignments for {name}")
    replacement = f"{name}={resolved}"
    if indexes:
        raw_lines[indexes[0]] = replacement
    else:
        raw_lines.append(replacement)
    _atomic_write(path, "\n".join(raw_lines) + "\n")
    path.chmod(0o600)
    print(f"UPDATED local env path: {name}")
    return 0


def set_local_env_value_from_stdin(
    *, catalog: Catalog, env_file: Path, name: str, payload: str
) -> int:
    path = env_file.expanduser().absolute()
    _load_private_dotenv(catalog=catalog, env_file=path)
    if name not in catalog.variables:
        raise ContractError(f"unknown variable: {name}")
    lines = payload.splitlines()
    if len(lines) != 1 or not lines[0] or "\x00" in lines[0]:
        raise ContractError("local-env set requires one non-empty line on stdin")
    value = lines[0]
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    assignment = re.compile(rf"^\s*(?:export\s+)?{re.escape(name)}\s*=")
    indexes = [index for index, line in enumerate(raw_lines) if assignment.match(line)]
    if len(indexes) > 1:
        raise ContractError(f"local env contains duplicate assignments for {name}")
    replacement = f"{name}={value}"
    if indexes:
        raw_lines[indexes[0]] = replacement
    else:
        raw_lines.append(replacement)
    _atomic_write(path, "\n".join(raw_lines) + "\n")
    path.chmod(0o600)
    print(f"UPDATED local env value: {name}")
    return 0


def _credential_payload(values: dict[str, str]) -> str:
    return "".join(f"{name}={value}\n" for name, value in values.items()) + "\n"


def _parse_credential_payload(payload: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in payload.splitlines():
        if not line:
            continue
        if "=" not in line:
            raise ContractError("credential helper returned an invalid response")
        name, value = line.split("=", 1)
        values[name] = value
    return values


def _run_credential_command(
    arguments: list[str], *, payload: str, stage: str
) -> str:
    environment = dict(os.environ)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    try:
        result = subprocess.run(
            ["git", *arguments],
            input=payload,
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
    except OSError as exc:
        raise ContractError(f"{stage} could not execute Git") from exc
    if result.returncode != 0:
        raise ContractError(f"{stage} failed with exit {result.returncode}")
    return result.stdout


def _clear_local_env_value(*, env_file: Path, name: str) -> None:
    raw_lines = env_file.read_text(encoding="utf-8").splitlines()
    assignment = re.compile(rf"^\s*(?:export\s+)?{re.escape(name)}\s*=")
    indexes = [index for index, line in enumerate(raw_lines) if assignment.match(line)]
    if len(indexes) != 1:
        raise ContractError(f"local env must contain exactly one assignment for {name}")
    raw_lines[indexes[0]] = f"{name}="
    _atomic_write(env_file, "\n".join(raw_lines) + "\n")
    env_file.chmod(0o600)


def migrate_forgejo_keychain(*, catalog: Catalog, env_file: Path) -> int:
    path = env_file.expanduser().absolute()
    values = _load_private_dotenv(catalog=catalog, env_file=path)
    url = values.get("FORGEJO_URL") or "http://localhost:3000"
    username = values.get("FORGEJO_USERNAME")
    password = values.get("FORGEJO_PASSWORD")
    if not username or not password:
        raise ContractError(
            "FORGEJO_USERNAME and FORGEJO_PASSWORD must both be present for migration"
        )

    parsed = urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ContractError("Forgejo URL has an invalid port") from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"localhost", "127.0.0.1"}
        or port != 3000
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ContractError(
            "migration accepts only http://localhost:3000 or http://127.0.0.1:3000"
        )

    host = f"{parsed.hostname}:3000"
    credential = {
        "protocol": "http",
        "host": host,
        "username": username,
        "password": password,
    }
    secret_payload = _credential_payload(credential)
    lookup_payload = _credential_payload(
        {"protocol": "http", "host": host, "username": username}
    )

    _run_credential_command(
        ["credential-osxkeychain", "store"],
        payload=secret_payload,
        stage="macOS Keychain store",
    )
    keychain = _parse_credential_payload(
        _run_credential_command(
            ["credential-osxkeychain", "get"],
            payload=lookup_payload,
            stage="macOS Keychain verification",
        )
    )
    returned_username = keychain.get("username")
    if not hmac.compare_digest(keychain.get("password", ""), password) or (
        returned_username is not None
        and not hmac.compare_digest(returned_username, username)
    ):
        raise ContractError("macOS Keychain verification returned different credentials")

    helper_key = f"credential.{url}.helper"
    _run_credential_command(
        ["config", "--global", "--replace-all", helper_key, ""],
        payload="",
        stage="Git credential helper reset",
    )
    _run_credential_command(
        ["config", "--global", "--add", helper_key, "osxkeychain"],
        payload="",
        stage="Git credential helper configuration",
    )

    legacy_store = Path.home() / ".git-credentials"
    _run_credential_command(
        ["credential-store", f"--file={legacy_store}", "erase"],
        payload=lookup_payload,
        stage="plaintext credential removal",
    )
    legacy_result = _parse_credential_payload(
        _run_credential_command(
            ["credential-store", f"--file={legacy_store}", "get"],
            payload=lookup_payload,
            stage="plaintext credential removal verification",
        )
    )
    if legacy_result.get("password"):
        raise ContractError("plaintext credential removal verification failed")

    resolved = _parse_credential_payload(
        _run_credential_command(
            ["credential", "fill"],
            payload=_credential_payload({"protocol": "http", "host": host}),
            stage="configured Git credential verification",
        )
    )
    if not (
        hmac.compare_digest(resolved.get("username", ""), username)
        and hmac.compare_digest(resolved.get("password", ""), password)
    ):
        raise ContractError(
            "configured Git credential verification returned different credentials"
        )

    _clear_local_env_value(env_file=path, name="FORGEJO_PASSWORD")
    print(
        "MIGRATED Forgejo localhost credential to macOS Keychain; "
        "plaintext store removed; FORGEJO_PASSWORD cleared; values suppressed"
    )
    return 0


def _execution_receipt_path(
    receipt: dict[str, Any], requested_path: Path | None = None
) -> Path:
    if requested_path is None:
        directory = Path(tempfile.gettempdir()) / f"runtime-env-receipts-{os.getuid()}"
        filename = None
    else:
        expanded = requested_path.expanduser()
        if not expanded.is_absolute():
            raise ContractError("explicit runtime receipt path must be absolute")
        path = expanded.absolute()
        if path.exists() or path.is_symlink():
            raise ContractError(f"runtime receipt already exists: {path}")
        directory = path.parent
        filename = path.name
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    metadata = directory.lstat()
    if (
        directory.is_symlink()
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        raise ContractError(
            "runtime receipt directory must be user-owned with mode 0700"
        )
    descriptor, raw_path = tempfile.mkstemp(
        prefix="receipt-", suffix=".json", dir=directory
    )
    temporary = Path(raw_path)
    path = temporary if filename is None else directory / filename
    receipt["receipt_path"] = str(path)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o600)
        if filename is not None:
            os.link(temporary, path)
            temporary.unlink()
    except FileExistsError as exc:
        raise ContractError(f"runtime receipt already exists: {path}") from exc
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return path


def _resolve_workload_command(catalog: Catalog, command: list[str]) -> list[str]:
    """Resolve versioned broker executables without using consumer-repo code."""
    resolved: list[str] = []
    for part in command:
        if not part.startswith("@runtime-env/"):
            resolved.append(part)
            continue
        if catalog.root is None:
            raise ContractError("runtime-env-owned entrypoint requires a catalog root")
        relative = Path(part.removeprefix("@runtime-env/"))
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            raise ContractError("runtime-env-owned entrypoint has an unsafe path")
        root = catalog.root.resolve()
        candidate = root.joinpath(relative)
        try:
            candidate.resolve().relative_to(root)
        except ValueError as exc:
            raise ContractError(
                "runtime-env-owned entrypoint escapes the catalog root"
            ) from exc
        if candidate.is_symlink() or not candidate.is_file():
            raise ContractError(
                f"runtime-env-owned entrypoint is not a regular file: {relative}"
            )
        resolved.append(str(candidate.resolve()))
    return resolved


def _catalog_source_metadata(catalog: Catalog) -> dict[str, Any]:
    if catalog.root is None:
        return {"root": None, "versioned": False, "head": None, "tree": None, "dirty": None}
    root = catalog.root.resolve()
    try:
        top_level = Path(_git(root, "rev-parse", "--show-toplevel")).resolve()
        head = _git(root, "rev-parse", "HEAD")
        tree = _git(root, "rev-parse", "HEAD^{tree}")
        dirty = bool(_git(root, "status", "--porcelain=v1"))
    except ContractError:
        return {
            "root": str(root),
            "versioned": False,
            "head": None,
            "tree": None,
            "dirty": None,
        }
    return {
        "root": str(root),
        "versioned": top_level == root,
        "head": head,
        "tree": tree,
        "dirty": dirty,
    }


def _require_clean_catalog(catalog: Catalog) -> dict[str, Any]:
    metadata = _catalog_source_metadata(catalog)
    if not metadata["versioned"] or metadata["dirty"] is not False:
        raise ContractError(
            "credential-bearing entrypoint requires a clean runtime-env catalog root"
        )
    return metadata


def run_workload(
    *,
    catalog: Catalog,
    workload_id: str,
    entrypoint_id: str,
    target_root: Path,
    env_file: Path | None,
    receipt_path: Path | None,
    json_output: bool,
) -> int:
    workload = catalog.workloads.get(workload_id)
    if workload is None:
        raise ContractError(f"unknown workload: {workload_id}")
    if workload["host"] != "local-macos":
        raise ContractError(
            f"workload {workload_id}: host {workload['host']} requires its dedicated adapter"
        )
    command = workload["entrypoints"].get(entrypoint_id)
    if command is None:
        raise ContractError(
            f"workload {workload_id}: unknown entrypoint {entrypoint_id}"
        )
    if any(re.search(r"<[^>]+>", part) for part in command):
        raise ContractError(
            f"workload {workload_id}: entrypoint {entrypoint_id} has an unresolved placeholder"
        )
    broker_adapter = workload.get("broker_adapters", {}).get(entrypoint_id)
    resolved_command = _resolve_workload_command(catalog, command)
    runtime_source = (
        _require_clean_catalog(catalog)
        if entrypoint_id in workload.get("clean_catalog_entrypoints", [])
        else _catalog_source_metadata(catalog)
    )

    target = target_root.expanduser().resolve()
    top_level = Path(_git(target, "rev-parse", "--show-toplevel")).resolve()
    if top_level != target:
        raise ContractError("target root must be the root of its git repository")
    before_head = _git(target, "rev-parse", "HEAD")
    before_status = _git(target, "status", "--porcelain=v1")
    if broker_adapter is not None and before_status:
        raise ContractError("broker adapter requires a clean target repository")

    profile_variables = select_variables(
        catalog,
        profile_id=workload["profile"],
        include_all=False,
    )
    allowed_names = set(workload["entrypoint_environment"][entrypoint_id])
    selected = [
        variable for variable in profile_variables if variable.name in allowed_names
    ]
    dotenv = (
        _load_private_dotenv(catalog=catalog, env_file=env_file) if env_file else {}
    )
    configured: dict[str, str] = {}
    for variable in selected:
        value = os.environ.get(variable.name)
        if not value:
            value = dotenv.get(variable.name)
        if not value:
            value = variable.default
        if value:
            configured[variable.name] = value

    missing = sorted(
        variable.name
        for variable in selected
        if variable.required and variable.name not in configured
    )
    if missing:
        raise MissingConfiguration(
            f"missing required workload variables: {', '.join(missing)}"
        )

    configured_secrets = sorted(
        name for name in configured if catalog.variables[name]["secret"]
    )
    delivery = workload["secret_delivery"]
    if configured_secrets and delivery == "none":
        raise ContractError(
            f"workload {workload_id}: secret_delivery=none refuses configured secret variables: "
            + ", ".join(configured_secrets)
        )
    if configured_secrets and delivery == "broker-only" and broker_adapter is None:
        raise ContractError(
            f"workload {workload_id}: entrypoint {entrypoint_id} has no dedicated "
            "broker adapter for configured secrets"
        )
    if configured_secrets and delivery == "openshell-provider":
        raise ContractError(
            f"workload {workload_id}: openshell-provider secrets require the "
            "dedicated provider bootstrap"
        )

    safe_inherited = {
        name: os.environ[name]
        for name in (
            "HOME",
            "LANG",
            "LC_ALL",
            "LOGNAME",
            "PATH",
            "SHELL",
            "SSH_AUTH_SOCK",
            "TERM",
            "TMPDIR",
            "USER",
        )
        if name in os.environ
    }
    child_environment = {**safe_inherited, **configured}
    child_environment.setdefault("PATH", os.defpath)
    if entrypoint_id in workload.get("clean_catalog_entrypoints", []):
        child_environment["PATH"] = "/usr/bin:/bin:/usr/sbin:/sbin"

    started_at = datetime.now(timezone.utc)
    try:
        result = subprocess.run(
            resolved_command,
            cwd=target,
            env=child_environment,
            check=False,
            capture_output=True,
        )
    except OSError as exc:
        raise ContractError(
            f"cannot execute workload entrypoint: {exc.strerror}"
        ) from exc
    finished_at = datetime.now(timezone.utc)
    after_head = _git(target, "rev-parse", "HEAD")
    after_status = _git(target, "status", "--porcelain=v1")
    read_only_unchanged = before_head == after_head and before_status == after_status
    policy_passed = workload["mutation"] != "read-only" or read_only_unchanged
    execution_exit = result.returncode if result.returncode != 0 else (0 if policy_passed else 2)

    def stream_metadata(value: bytes) -> dict[str, Any]:
        return {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}

    receipt: dict[str, Any] = {
        "schema": "runtime-env/execution-receipt/v1",
        "status": "passed" if execution_exit == 0 else "failed",
        "workload": workload_id,
        "entrypoint": entrypoint_id,
        "child_exit": result.returncode,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "command_sha256": hashlib.sha256(
            json.dumps(command, separators=(",", ":"), ensure_ascii=False).encode(
                "utf-8"
            )
        ).hexdigest(),
        "environment": {
            "configured_names": sorted(configured),
            "secret_names": configured_secrets,
            "delivery": delivery,
        },
        "broker_adapter": broker_adapter,
        "stdout": stream_metadata(result.stdout),
        "stderr": stream_metadata(result.stderr),
        "target": {
            "root": str(target),
            "head_before": before_head,
            "head_after": after_head,
            "dirty_before": bool(before_status),
            "dirty_after": bool(after_status),
        },
        "declared_evidence": workload["evidence"],
        "policy": {"read_only_unchanged": read_only_unchanged},
        "runtime_source": runtime_source,
    }
    _execution_receipt_path(receipt, receipt_path)
    if json_output:
        print(json.dumps(receipt, sort_keys=True, ensure_ascii=False))
    else:
        print(
            f"{receipt['status'].upper()} workload={workload_id} "
            f"entrypoint={entrypoint_id} exit={execution_exit} "
            f"receipt={receipt['receipt_path']}"
        )
    return execution_exit


def initialize_local_env(*, catalog: Catalog, env_file: Path) -> int:
    path = env_file.expanduser().absolute()
    if path.exists() or path.is_symlink():
        raise ContractError(f"local env already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, render_local_dotenv(catalog))
    path.chmod(0o600)
    print(f"CREATED local env template {path} mode=0600 values=empty")
    return 0


def inventory_skills(repo_root: Path) -> dict[str, Any]:
    repo = repo_root.resolve()
    skills_root = repo / ".agents" / "skills"
    if not skills_root.is_dir():
        raise ContractError(f"missing skills directory: {skills_root}")
    excluded_directories = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        "fixtures",
        "data",
        ".cache",
    }
    code_suffixes = {".py", ".sh", ".js", ".mjs", ".cjs", ".ts", ".tsx"}
    skills: list[dict[str, Any]] = []
    for skill_root in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        manifests = [
            path for path in skill_root.iterdir() if path.name.lower() == "skill.md"
        ]
        if len(manifests) != 1:
            if manifests:
                raise ContractError(
                    f"skill {skill_root.name}: multiple skill manifests"
                )
            continue
        manifest = manifests[0]
        runtime_modules: list[str] = []
        assertion_modules: list[str] = []
        searchable_text: list[str] = []
        for current_root, directory_names, file_names in os.walk(
            skill_root, followlinks=True
        ):
            directory_names[:] = sorted(
                name for name in directory_names if name not in excluded_directories
            )
            current = Path(current_root)
            for file_name in sorted(file_names):
                path = current / file_name
                try:
                    relative = path.relative_to(repo).as_posix()
                except ValueError:
                    relative = (
                        Path(".agents")
                        / "skills"
                        / skill_root.name
                        / path.relative_to(skill_root)
                    ).as_posix()
                if path.suffix.lower() in {
                    ".md",
                    ".py",
                    ".sh",
                    ".js",
                    ".mjs",
                    ".cjs",
                    ".ts",
                    ".tsx",
                }:
                    try:
                        searchable_text.append(path.read_text(encoding="utf-8"))
                    except (OSError, UnicodeDecodeError):
                        pass
                if path.suffix.lower() not in code_suffixes:
                    continue
                logical_parts = Path(relative).parts
                if any(
                    part in {"tests", "test", "assertions", "evals"}
                    for part in logical_parts
                ):
                    assertion_modules.append(relative)
                else:
                    runtime_modules.append(relative)
        combined = "\n".join(searchable_text)
        environment_names = sorted(
            {
                name
                for match in ENV_REFERENCE.finditer(combined)
                for name in match.groups()
                if name
            }
        )
        repo_modules: list[str] = []
        for match in REPO_MODULE_REFERENCE.finditer(combined):
            relative = match.group(1).rstrip(".,:;`)]}")
            if (repo / relative).is_file():
                repo_modules.append(relative)
        skills.append(
            {
                "id": skill_root.name,
                "manifest": manifest.relative_to(repo).as_posix(),
                "physical_source_root": str(skill_root.resolve()),
                "runtime_modules": sorted(set(runtime_modules)),
                "assertion_modules": sorted(set(assertion_modules)),
                "repo_modules": sorted(set(repo_modules)),
                "environment_names": environment_names,
            }
        )
    return {
        "schema": "runtime-env/skill-inventory/v1",
        "repo_root": str(repo),
        "skill_count": len(skills),
        "skills": skills,
    }


def _consumer_content(target: Path, relative: str, *, staged: bool) -> str:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ContractError(f"unsafe consumer projection path: {relative}")
    if staged:
        result = subprocess.run(
            ["git", "-C", str(target), "show", f":{path.as_posix()}"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise ContractError(
                f"missing staged consumer projection: {path.as_posix()}"
            )
        return result.stdout
    try:
        return (target / path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractError(
            f"cannot read consumer projection {path}: {exc.strerror}"
        ) from exc


def _verify_content_hash(document: dict[str, Any], relative: str) -> None:
    claimed = document.get("content_sha256")
    if not isinstance(claimed, str):
        raise ContractError(f"{relative}: missing content_sha256")
    unsigned = dict(document)
    del unsigned["content_sha256"]
    if _sha256(_canonical_json(unsigned)) != claimed:
        raise ContractError(f"{relative}: content_sha256 mismatch")


def verify_consumer(*, target_root: Path, binding_id: str, staged: bool) -> int:
    target = target_root.resolve()
    top_level = Path(_git(target, "rev-parse", "--show-toplevel")).resolve()
    if top_level != target:
        raise ContractError("target root must be the root of its git repository")
    binding_path = f".runtime-env/bindings/{binding_id}.json"
    try:
        binding = json.loads(_consumer_content(target, binding_path, staged=staged))
    except json.JSONDecodeError as exc:
        raise ContractError(f"{binding_path}: invalid JSON: {exc}") from exc
    if binding.get("schema") not in {
        "runtime-env/consumer-binding/v1",
        "runtime-env/consumer-binding/v2",
    }:
        raise ContractError(f"{binding_path}: unexpected schema")
    if binding.get("binding") != binding_id:
        raise ContractError(f"{binding_path}: binding id mismatch")
    _verify_content_hash(binding, binding_path)
    if binding.get("schema") == "runtime-env/consumer-binding/v2":
        modules = binding.get("modules")
        if not isinstance(modules, list) or not modules:
            raise ContractError(f"{binding_path}: invalid resolved module closure")
        seen_modules: set[str] = set()
        for module in modules:
            if not isinstance(module, dict) or set(module) != {
                "content_sha256",
                "id",
                "interface_version",
            }:
                raise ContractError(f"{binding_path}: invalid resolved module entry")
            if module["id"] in seen_modules:
                raise ContractError(f"{binding_path}: duplicate resolved module")
            seen_modules.add(module["id"])
            if not re.fullmatch(r"[0-9a-f]{64}", module["content_sha256"]):
                raise ContractError(f"{binding_path}: invalid resolved module digest")
            if module["interface_version"] != "runtime-env/module/v1":
                raise ContractError(f"{binding_path}: unsupported module interface")
        requirements_sha = binding.get("requirements_sha256")
        if requirements_sha is not None and not re.fullmatch(
            r"[0-9a-f]{64}", requirements_sha
        ):
            raise ContractError(f"{binding_path}: invalid requirements digest")
        if requirements_sha is not None:
            requirement_paths = (
                f".runtime-env/requirements/{binding_id}.json",
                ".runtime-env/requirements.json",
            )
            requirement_documents: list[tuple[str, str]] = []
            for requirement_path in requirement_paths:
                try:
                    content = _consumer_content(
                        target, requirement_path, staged=staged
                    )
                except ContractError as exc:
                    if "missing staged consumer projection" in str(exc) or (
                        not staged and "cannot read consumer projection" in str(exc)
                    ):
                        continue
                    raise
                requirement_documents.append((requirement_path, content))
            if len(requirement_documents) != 1:
                raise ContractError(
                    f"{binding_path}: expected exactly one consumer requirements file"
                )
            requirement_path, requirement_content = requirement_documents[0]
            if _sha256(requirement_content) != requirements_sha:
                raise ContractError(
                    f"{requirement_path}: requirements sha256 mismatch"
                )
            try:
                requirement_document = json.loads(requirement_content)
            except json.JSONDecodeError as exc:
                raise ContractError(
                    f"{requirement_path}: invalid JSON: {exc}"
                ) from exc
            if requirement_document.get("binding") != binding_id:
                raise ContractError(f"{requirement_path}: binding id mismatch")

        install_receipt_path = _default_catalog_root() / "INSTALL-RECEIPT.json"
        if install_receipt_path.is_file():
            try:
                install_receipt = json.loads(
                    install_receipt_path.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError) as exc:
                raise ContractError(f"invalid installed CLI receipt: {exc}") from exc
            source = binding.get("source", {})
            if (
                install_receipt.get("schema")
                != "runtime-env/consumer-cli-install/v1"
                or install_receipt.get("commit") != source.get("commit")
                or install_receipt.get("tree") != source.get("tree")
            ):
                raise ContractError(
                    f"{binding_path}: installed CLI source does not match binding source"
                )
    variables = binding.get("variables")
    if not isinstance(variables, list) or not variables:
        raise ContractError(f"{binding_path}: invalid variable projection")
    for variable in variables:
        if not isinstance(variable, dict) or variable.get("runtime_scope") not in {
            "local-only",
            "cloud-runtime",
            "portable",
        }:
            raise ContractError(f"{binding_path}: invalid variable runtime_scope")

    render = binding.get("render")
    if not isinstance(render, dict) or not isinstance(render.get("path"), str):
        raise ContractError(f"{binding_path}: invalid render projection")
    example = _consumer_content(target, render["path"], staged=staged)
    if _sha256(example) != render.get("sha256"):
        raise ContractError(f"{render['path']}: render sha256 mismatch")

    projections = binding.get("projections")
    if not isinstance(projections, dict) or set(projections) != {
        "policies",
        "workload",
    }:
        raise ContractError(f"{binding_path}: invalid projection manifest")
    paths: list[str] = []
    workload_path = projections["workload"]
    if workload_path is not None:
        if not isinstance(workload_path, str):
            raise ContractError(f"{binding_path}: invalid workload projection path")
        paths.append(workload_path)
    policy_paths = projections["policies"]
    if not isinstance(policy_paths, list) or any(
        not isinstance(path, str) for path in policy_paths
    ):
        raise ContractError(f"{binding_path}: invalid policy projection paths")
    if len(set(policy_paths)) != len(policy_paths):
        raise ContractError(f"{binding_path}: duplicate policy projection paths")
    paths.extend(policy_paths)

    for relative in paths:
        try:
            projection = json.loads(_consumer_content(target, relative, staged=staged))
        except json.JSONDecodeError as exc:
            raise ContractError(f"{relative}: invalid JSON: {exc}") from exc
        if projection.get("binding") != binding_id:
            raise ContractError(f"{relative}: binding id mismatch")
        expected_schema = (
            "runtime-env/consumer-workload/v1"
            if relative == workload_path
            else "runtime-env/consumer-policy/v1"
        )
        if projection.get("schema") != expected_schema:
            raise ContractError(f"{relative}: unexpected schema")
        if projection.get("source") != binding.get("source"):
            raise ContractError(f"{relative}: source receipt mismatch")
        _verify_content_hash(projection, relative)
    print(
        f"OK consumer {binding_id}: staged={str(staged).lower()} "
        f"projections={2 + len(paths)}"
    )
    return 0


def accept_consumer(
    *,
    catalog: Catalog,
    target_root: Path,
    binding_id: str,
    env_file: Path | None,
    hook_verifier: Path,
    receipt_path: Path,
    json_output: bool,
) -> int:
    """Run one consumer's complete, pinned acceptance set and bind the evidence."""
    target = target_root.expanduser().resolve()
    top_level = Path(_git(target, "rev-parse", "--show-toplevel")).resolve()
    if top_level != target:
        raise ContractError("target root must be the root of its git repository")
    before_head = _git(target, "rev-parse", "HEAD")
    before_tree = _git(target, "rev-parse", "HEAD^{tree}")
    before_status = _git(target, "status", "--porcelain=v1")
    if before_status:
        raise ContractError("consumer acceptance requires a clean target checkout")
    before_ignored = _ignored_files_fingerprint(target)

    hooks_path_text = _git(target, "config", "--get", "core.hooksPath")
    hooks_path = Path(hooks_path_text)
    if hooks_path.is_absolute() or ".." in hooks_path.parts:
        raise ContractError("L5 acceptance requires a repo-relative core.hooksPath")
    verifier_relative = hook_verifier
    if verifier_relative.is_absolute() or ".." in verifier_relative.parts:
        raise ContractError("hook verifier must be a safe target-relative path")
    hook_relative = hooks_path / "pre-commit"
    hook_path = target / hook_relative
    verifier_path = target / verifier_relative
    for label, path, relative in (
        ("pre-commit hook", hook_path, hook_relative),
        ("hook verifier", verifier_path, verifier_relative),
    ):
        if path.is_symlink() or not path.is_file():
            raise ContractError(f"L5 {label} must be a regular tracked file: {relative}")
        _git(target, "ls-files", "--error-unmatch", relative.as_posix())
        if not os.access(path, os.X_OK):
            raise ContractError(f"L5 {label} must be executable: {relative}")
    hook_bytes = hook_path.read_bytes()
    verifier_bytes = verifier_path.read_bytes()
    try:
        hook_text = hook_bytes.decode("utf-8")
        verifier_text = verifier_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError("L5 hook and verifier must be UTF-8 text") from exc
    hook_code = "\n".join(
        line for line in hook_text.splitlines() if not line.lstrip().startswith("#")
    )
    verifier_code = "\n".join(
        line for line in verifier_text.splitlines() if not line.lstrip().startswith("#")
    )
    if verifier_relative.as_posix() not in hook_code:
        raise ContractError("pre-commit hook does not invoke the declared verifier")
    if "verify-consumer" not in verifier_code or binding_id not in verifier_code:
        raise ContractError(
            "declared hook verifier requires an executable verifier line for this binding"
        )
    verifier_environment = {
        name: os.environ[name]
        for name in ("HOME", "LANG", "LC_ALL", "LOGNAME", "PATH", "SHELL", "TMPDIR", "USER")
        if name in os.environ
    }
    verifier_environment.setdefault("PATH", os.defpath)
    try:
        verifier_result = subprocess.run(
            [str(verifier_path), "--staged"],
            cwd=target,
            env=verifier_environment,
            check=False,
            capture_output=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ContractError("cannot execute the declared hook verifier") from exc
    if verifier_result.returncode != 0:
        raise ContractError(
            f"declared hook verifier --staged failed with exit {verifier_result.returncode}"
        )
    hook_gate = {
        "status": "passed",
        "hooks_path": hooks_path.as_posix(),
        "pre_commit": hook_relative.as_posix(),
        "pre_commit_sha256": hashlib.sha256(hook_bytes).hexdigest(),
        "verifier": verifier_relative.as_posix(),
        "verifier_sha256": hashlib.sha256(verifier_bytes).hexdigest(),
        "verifier_execution": {
            "exit_code": verifier_result.returncode,
            "stdout_sha256": hashlib.sha256(verifier_result.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(verifier_result.stderr).hexdigest(),
        },
    }

    with contextlib.redirect_stdout(io.StringIO()):
        verify_consumer(target_root=target, binding_id=binding_id, staged=False)
        verify_consumer(target_root=target, binding_id=binding_id, staged=True)

    binding_path = f".runtime-env/bindings/{binding_id}.json"
    binding = json.loads(_consumer_content(target, binding_path, staged=False))
    projections = binding["projections"]
    workload_path = projections.get("workload")
    if not isinstance(workload_path, str):
        raise ContractError(f"{binding_path}: L5 acceptance requires a workload")
    projection = json.loads(_consumer_content(target, workload_path, staged=False))
    workload = projection.get("workload")
    if not isinstance(workload, dict):
        raise ContractError(f"{workload_path}: invalid workload projection")
    workload_id = workload.get("id")
    catalog_workload = catalog.workloads.get(workload_id)
    if catalog_workload is None or workload != catalog_workload:
        raise ContractError(
            f"{workload_path}: projected workload does not match the pinned catalog"
        )
    public_tests = workload.get("public_test_entrypoints")
    if not isinstance(public_tests, list) or not public_tests:
        raise ContractError(
            f"workload {workload_id}: L5 acceptance requires public_test_entrypoints"
        )

    runtime_source = _require_clean_catalog(catalog)
    source = binding.get("source")
    if not isinstance(source, dict) or (
        source.get("commit") != runtime_source["head"]
        or source.get("tree") != runtime_source["tree"]
    ):
        raise ContractError(
            f"{binding_path}: catalog source does not match the consumer pin"
        )

    requested_receipt = receipt_path.expanduser()
    if not requested_receipt.is_absolute():
        raise ContractError("consumer acceptance receipt path must be absolute")
    if requested_receipt.exists() or requested_receipt.is_symlink():
        raise ContractError(
            f"consumer acceptance receipt already exists: {requested_receipt}"
        )
    requested_receipt.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    parent_stat = requested_receipt.parent.stat()
    if (
        parent_stat.st_uid != os.getuid()
        or stat.S_IMODE(parent_stat.st_mode) != 0o700
    ):
        raise ContractError(
            "consumer acceptance receipt directory must be user-owned with mode 0700"
        )
    execution_directory = requested_receipt.with_suffix("")
    execution_directory = execution_directory.parent / (
        execution_directory.name + ".d"
    )
    if execution_directory.exists() or execution_directory.is_symlink():
        raise ContractError(
            f"consumer acceptance execution directory already exists: {execution_directory}"
        )
    execution_directory.mkdir(mode=0o700)

    started_at = datetime.now(timezone.utc)
    executions: list[dict[str, Any]] = []
    all_passed = True
    for entrypoint_id in workload["acceptance_entrypoints"]:
        entry_receipt_path = execution_directory / f"{entrypoint_id}.json"
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                execution_exit = run_workload(
                    catalog=catalog,
                    workload_id=workload_id,
                    entrypoint_id=entrypoint_id,
                    target_root=target,
                    env_file=env_file,
                    receipt_path=entry_receipt_path,
                    json_output=False,
                )
        except MissingConfiguration as exc:
            executions.append(
                {
                    "entrypoint": entrypoint_id,
                    "status": "blocked",
                    "reason": str(exc),
                }
            )
            all_passed = False
            break
        except ContractError as exc:
            executions.append(
                {
                    "entrypoint": entrypoint_id,
                    "status": "failed",
                    "reason": str(exc),
                }
            )
            all_passed = False
            break
        execution_bytes = entry_receipt_path.read_bytes()
        execution = json.loads(execution_bytes)
        executions.append(
            {
                "child_exit": execution["child_exit"],
                "command_sha256": execution["command_sha256"],
                "entrypoint": entrypoint_id,
                "receipt_path": str(entry_receipt_path),
                "receipt_sha256": hashlib.sha256(execution_bytes).hexdigest(),
                "status": execution["status"],
            }
        )
        if execution_exit != 0 or execution["status"] != "passed":
            all_passed = False
            break

    after_head = _git(target, "rev-parse", "HEAD")
    after_tree = _git(target, "rev-parse", "HEAD^{tree}")
    after_status = _git(target, "status", "--porcelain=v1")
    after_ignored = _ignored_files_fingerprint(target)
    ignored_changed = before_ignored != after_ignored
    ignored_change_permitted = workload["mutation"] == "workspace"
    tracked_target_unchanged = (
        before_head == after_head
        and before_tree == after_tree
        and not after_status
    )
    target_unchanged = tracked_target_unchanged and (
        not ignored_changed or ignored_change_permitted
    )
    complete_set = [item["entrypoint"] for item in executions] == workload[
        "acceptance_entrypoints"
    ]
    passed = all_passed and complete_set and target_unchanged
    finished_at = datetime.now(timezone.utc)
    receipt: dict[str, Any] = {
        "schema": "runtime-env/consumer-acceptance-receipt/v1",
        "status": "passed" if passed else "failed",
        "maturity": "L5" if passed else "below-L5",
        "binding": binding_id,
        "workload": workload_id,
        "public_test_entrypoints": public_tests,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "runtime_source": runtime_source,
        "binding_content_sha256": binding["content_sha256"],
        "workload_content_sha256": projection["content_sha256"],
        "projection_checks": {"staged": "passed", "worktree": "passed"},
        "hook_gate": hook_gate,
        "target": {
            "root": str(target),
            "head_before": before_head,
            "head_after": after_head,
            "tree_before": before_tree,
            "tree_after": after_tree,
            "dirty_before": bool(before_status),
            "dirty_after": bool(after_status),
            "mutation": workload["mutation"],
            "ignored_changed_after": ignored_changed,
            "ignored_change_permitted": ignored_change_permitted,
        },
        "executions": executions,
    }
    _execution_receipt_path(receipt, requested_receipt)
    if json_output:
        print(json.dumps(receipt, sort_keys=True, ensure_ascii=False))
    else:
        print(
            f"{receipt['status'].upper()} consumer={binding_id} "
            f"maturity={receipt['maturity']} receipt={receipt['receipt_path']}"
        )
    return 0 if passed else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="runtime-env")
    parser.add_argument("--catalog-root", type=Path, default=_default_catalog_root())
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "validate", help="validate every catalog, module, and profile"
    )
    render_parser = subparsers.add_parser(
        "render", help="render a secret-free environment template"
    )
    selection = render_parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--profile")
    selection.add_argument("--all", action="store_true", dest="include_all")
    render_parser.add_argument(
        "--format", choices=("dotenv", "github-actions"), required=True
    )
    check_parser = subparsers.add_parser(
        "check", help="check required names without printing values"
    )
    check_parser.add_argument("--profile", required=True)
    check_parser.add_argument("--env-file", type=Path)
    list_parser = subparsers.add_parser(
        "list", help="discover catalog entries or profile requirements"
    )
    list_selection = list_parser.add_mutually_exclusive_group(required=True)
    list_selection.add_argument("--kind", choices=("variables", "modules", "profiles"))
    list_selection.add_argument("--profile")
    sync_parser = subparsers.add_parser(
        "sync", help="explicitly synchronize a pinned, secret-free consumer binding"
    )
    sync_parser.add_argument("--requirements", type=Path)
    sync_parser.add_argument("--profile")
    sync_parser.add_argument("--binding")
    sync_parser.add_argument("--workload")
    sync_parser.add_argument("--policy", action="append", default=[])
    sync_parser.add_argument("--target-root", type=Path, required=True)
    sync_mode = sync_parser.add_mutually_exclusive_group()
    sync_mode.add_argument("--apply", action="store_true")
    sync_mode.add_argument("--check", action="store_true")
    local_env_parser = subparsers.add_parser(
        "local-env", help="inspect host-only dotenv metadata without printing values"
    )
    local_env_subparsers = local_env_parser.add_subparsers(
        dest="local_env_command", required=True
    )
    local_env_init = local_env_subparsers.add_parser("init")
    local_env_init.add_argument("--env-file", type=Path)
    local_env_doctor = local_env_subparsers.add_parser("doctor")
    local_env_doctor.add_argument("--env-file", type=Path)
    local_env_reconcile = local_env_subparsers.add_parser(
        "reconcile",
        help="preserve values and organize all catalog names by runtime scope",
    )
    local_env_reconcile.add_argument("--env-file", type=Path)
    local_env_set_path = local_env_subparsers.add_parser(
        "set-path", help="set one declared non-secret path without printing it"
    )
    local_env_set_path.add_argument("--env-file", type=Path)
    local_env_set_path.add_argument("--name", required=True)
    local_env_set_path.add_argument("--path", type=Path, required=True)
    local_env_set = local_env_subparsers.add_parser(
        "set", help="set one declared value from stdin without printing it"
    )
    local_env_set.add_argument("--env-file", type=Path)
    local_env_set.add_argument("--name", required=True)
    local_env_set.add_argument("--stdin", action="store_true", required=True)
    local_env_migrate_forgejo = local_env_subparsers.add_parser(
        "migrate-forgejo-keychain",
        help="move one localhost Forgejo password from private dotenv/plaintext store to macOS Keychain",
    )
    local_env_migrate_forgejo.add_argument("--env-file", type=Path)
    workload_parser = subparsers.add_parser(
        "workload", help="inspect typed local workloads"
    )
    workload_subparsers = workload_parser.add_subparsers(
        dest="workload_command", required=True
    )
    workload_subparsers.add_parser("list")
    workload_show = workload_subparsers.add_parser("show")
    workload_show.add_argument("--id", required=True)
    workload_run = workload_subparsers.add_parser(
        "run", help="run one fixed local entrypoint and emit a redacted receipt"
    )
    workload_run.add_argument("--id", required=True)
    workload_run.add_argument("--entrypoint", required=True)
    workload_run.add_argument("--target-root", type=Path, required=True)
    workload_run.add_argument("--env-file", type=Path)
    workload_run.add_argument(
        "--receipt", type=Path, help="write one immutable metadata receipt to this path"
    )
    workload_run.add_argument("--json", action="store_true")
    policy_parser = subparsers.add_parser(
        "policy", help="inspect native carrier policies"
    )
    policy_subparsers = policy_parser.add_subparsers(
        dest="policy_command", required=True
    )
    policy_subparsers.add_parser("list")
    policy_show = policy_subparsers.add_parser("show")
    policy_show.add_argument("--id", required=True)
    inventory_parser = subparsers.add_parser(
        "inventory",
        help="enumerate physical runtime modules without reading secret values",
    )
    inventory_subparsers = inventory_parser.add_subparsers(
        dest="inventory_command", required=True
    )
    inventory_skills_parser = inventory_subparsers.add_parser("skills")
    inventory_skills_parser.add_argument("--repo-root", type=Path, required=True)
    verify_consumer_parser = subparsers.add_parser(
        "verify-consumer",
        help="verify consumer projections from the working tree or Git index",
    )
    verify_consumer_parser.add_argument("--target-root", type=Path, required=True)
    verify_consumer_parser.add_argument("--binding", required=True)
    verify_consumer_parser.add_argument("--staged", action="store_true")
    accept_consumer_parser = subparsers.add_parser(
        "accept-consumer",
        help="run every fixed acceptance entrypoint and emit one L5 receipt",
    )
    accept_consumer_parser.add_argument("--target-root", type=Path, required=True)
    accept_consumer_parser.add_argument("--binding", required=True)
    accept_consumer_parser.add_argument("--env-file", type=Path)
    accept_consumer_parser.add_argument("--hook-verifier", type=Path, required=True)
    accept_consumer_parser.add_argument("--receipt", type=Path, required=True)
    accept_consumer_parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "verify-consumer":
        try:
            return verify_consumer(
                target_root=args.target_root,
                binding_id=args.binding,
                staged=args.staged,
            )
        except ContractError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
    try:
        catalog = load_catalog(args.catalog_root.resolve())
    except ContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.command == "validate":
        print(
            f"OK catalog: {len(catalog.variables)} variables, "
            f"{len(catalog.modules)} modules, {len(catalog.profiles)} profiles, "
            f"{len(catalog.workloads)} workloads, {len(catalog.policies)} policies"
        )
        return 0
    if args.command == "accept-consumer":
        try:
            return accept_consumer(
                catalog=catalog,
                target_root=args.target_root,
                binding_id=args.binding,
                env_file=args.env_file,
                hook_verifier=args.hook_verifier,
                receipt_path=args.receipt,
                json_output=args.json,
            )
        except ContractError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
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
            lines, missing_required = check_environment(
                selected, env_file=args.env_file
            )
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
            sensitivity = (
                "secret" if catalog.variables[variable.name]["secret"] else "non-secret"
            )
            requirement = "required" if variable.required else "optional"
            default = variable.default if variable.default is not None else "-"
            print(f"{requirement}\t{sensitivity}\t{variable.name}\t{default}")
        return 0
    if args.command == "sync":
        try:
            requirements_sha256 = None
            required_modules = None
            if args.requirements is not None:
                if args.profile or args.binding or args.workload or args.policy:
                    raise ContractError(
                        "--requirements cannot be combined with --profile, --binding, --workload, or --policy"
                    )
                requirements = _load_consumer_requirements(args.requirements)
                requirements_sha256 = hashlib.sha256(
                    args.requirements.read_bytes()
                ).hexdigest()
                args.profile = requirements["profile"]
                args.binding = requirements["binding"]
                args.workload = requirements["workload"]
                args.policy = requirements["policies"]
                required_modules = requirements["required_modules"]
            elif not args.profile or not args.binding:
                raise ContractError(
                    "sync needs --requirements or both --profile and --binding"
                )
            return sync_consumer(
                root=args.catalog_root.resolve(),
                catalog=catalog,
                profile_id=args.profile,
                binding_id=args.binding,
                workload_id=args.workload,
                policy_ids=args.policy,
                target_root=args.target_root,
                apply=args.apply,
                check=args.check,
                requirements_sha256=requirements_sha256,
                required_modules=required_modules,
            )
        except ContractError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
    if args.command == "local-env":
        try:
            if args.local_env_command == "init":
                return initialize_local_env(
                    catalog=catalog,
                    env_file=args.env_file or (args.catalog_root / ".env"),
                )
            if args.local_env_command == "reconcile":
                return reconcile_local_env(
                    catalog=catalog,
                    env_file=args.env_file or (args.catalog_root / ".env"),
                )
            if args.local_env_command == "set-path":
                return set_local_env_path(
                    catalog=catalog,
                    env_file=args.env_file or (args.catalog_root / ".env"),
                    name=args.name,
                    value=args.path,
                )
            if args.local_env_command == "set":
                return set_local_env_value_from_stdin(
                    catalog=catalog,
                    env_file=args.env_file or (args.catalog_root / ".env"),
                    name=args.name,
                    payload=sys.stdin.read(),
                )
            if args.local_env_command == "migrate-forgejo-keychain":
                return migrate_forgejo_keychain(
                    catalog=catalog,
                    env_file=args.env_file or (args.catalog_root / ".env"),
                )
            return doctor_local_env(
                catalog=catalog,
                env_file=args.env_file or (args.catalog_root / ".env"),
                catalog_root=args.catalog_root,
            )
        except ContractError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
    if args.command == "workload":
        if args.workload_command == "list":
            for identifier, workload in sorted(catalog.workloads.items()):
                print(f"{identifier}\t{workload['summary']}")
            return 0
        if args.workload_command == "run":
            try:
                return run_workload(
                    catalog=catalog,
                    workload_id=args.id,
                    entrypoint_id=args.entrypoint,
                    target_root=args.target_root,
                    env_file=args.env_file,
                    receipt_path=args.receipt,
                    json_output=args.json,
                )
            except MissingConfiguration as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                return 3
            except ContractError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                return 2
        workload = catalog.workloads.get(args.id)
        if workload is None:
            print(f"ERROR: unknown workload: {args.id}", file=sys.stderr)
            return 2
        print(json.dumps(workload, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    if args.command == "inventory":
        try:
            document = inventory_skills(args.repo_root)
        except ContractError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    if args.command == "policy":
        if args.policy_command == "list":
            for identifier, policy in sorted(catalog.policies.items()):
                print(f"{identifier}\t{policy['summary']}")
            return 0
        policy = catalog.policies.get(args.id)
        if policy is None:
            print(f"ERROR: unknown policy: {args.id}", file=sys.stderr)
            return 2
        print(json.dumps(policy, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    raise AssertionError(f"unhandled command: {args.command}")
