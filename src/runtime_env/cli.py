"""Validate and consume the repository's environment contract catalog."""

from __future__ import annotations

import argparse
import hashlib
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
REPO_MODULE_REFERENCE = re.compile(r"(?<![A-Za-z0-9_.-])((?:kb-ingest|indexing)/[A-Za-z0-9_./-]+)")
SCHEMAS = {
    "variables": "runtime-env/variables/v1",
    "module": "runtime-env/module/v1",
    "profile": "runtime-env/profile/v1",
    "workload": "runtime-env/workload/v1",
    "policy": "runtime-env/carrier-policy/v1",
}
ALLOWED_FIELDS = {
    "variables": {"schema", "variables"},
    "variable": {"name", "secret", "description", "account_url"},
    "module": {"schema", "id", "summary", "requires", "optional", "defaults"},
    "profile": {"schema", "id", "summary", "modules"},
    "workload": {
        "schema",
        "id",
        "summary",
        "profile",
        "host",
        "entrypoints",
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
    "variable": {"name", "secret", "description"},
    "module": {"schema", "id", "summary", "requires", "optional", "defaults"},
    "profile": {"schema", "id", "summary", "modules"},
    "workload": {
        "schema",
        "id",
        "summary",
        "profile",
        "host",
        "entrypoints",
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


@dataclass(frozen=True)
class Catalog:
    variables: dict[str, dict[str, Any]]
    modules: dict[str, dict[str, Any]]
    profiles: dict[str, dict[str, Any]]
    workloads: dict[str, dict[str, Any]]
    policies: dict[str, dict[str, Any]]


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
            raise ContractError(f"{path}: missing required fields: {', '.join(missing)}")
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
    unexpected = sorted(set(variables_document) - ALLOWED_FIELDS["variables"])
    if unexpected:
        raise ContractError(f"variables catalog: unexpected fields: {', '.join(unexpected)}")
    missing = sorted(REQUIRED_FIELDS["variables"] - set(variables_document))
    if missing:
        raise ContractError(f"variables catalog: missing required fields: {', '.join(missing)}")
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
            raise ContractError(f"{name}: missing required fields: {', '.join(missing)}")
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
        if any(not isinstance(name, str) for name in required + optional):
            raise ContractError(f"module {module_id}: variable references must be strings")
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
        if any(not isinstance(module_id, str) for module_id in module_ids):
            raise ContractError(f"profile {profile_id}: module references must be strings")
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
            raise ContractError(f"workload {workload_id}: agent secret access must be denied")
        if workload.get("mutation") not in {"read-only", "workspace", "external-release"}:
            raise ContractError(f"workload {workload_id}: unsupported mutation class")
        entrypoints = workload.get("entrypoints")
        if not isinstance(entrypoints, dict) or not entrypoints:
            raise ContractError(f"workload {workload_id}: entrypoints must be a non-empty object")
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
        evidence = workload.get("evidence")
        if not isinstance(evidence, dict) or set(evidence) != {"receipt", "control"}:
            raise ContractError(
                f"workload {workload_id}: evidence must contain receipt and control"
            )
        if any(not isinstance(evidence[name], str) or not evidence[name] for name in evidence):
            raise ContractError(f"workload {workload_id}: evidence paths must be non-empty")

    policy_directory = root / "policies"
    policies = (
        _load_named_documents(policy_directory, "policy") if policy_directory.is_dir() else {}
    )
    for policy_id, policy in policies.items():
        if policy.get("carrier") not in {"claude-code", "codex-cli"}:
            raise ContractError(f"policy {policy_id}: unsupported carrier")
        config_home_env = policy.get("config_home_env")
        if config_home_env not in variables or variables[config_home_env]["secret"]:
            raise ContractError(f"policy {policy_id}: invalid config home variable")
        if not isinstance(policy.get("settings_file"), str) or not policy["settings_file"]:
            raise ContractError(f"policy {policy_id}: settings_file must be non-empty")
        if not isinstance(policy.get("required_settings"), dict) or not policy["required_settings"]:
            raise ContractError(f"policy {policy_id}: required_settings must be non-empty")
        for field in ("forbidden_environment", "external_requirements", "receipt_commands"):
            values = policy.get(field)
            if not isinstance(values, list) or not values or any(
                not isinstance(value, str) or not value for value in values
            ):
                raise ContractError(f"policy {policy_id}: {field} must be a non-empty string array")

    catalog = Catalog(
        variables=variables,
        modules=modules,
        profiles=profiles,
        workloads=workloads,
        policies=policies,
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
        raise ContractError("origin URL must not contain credentials, query, or fragment")
    path = parsed.path.removesuffix(".git").rstrip("/")
    if not path or path == "/":
        raise ContractError("origin URL must identify a repository")
    return urlunsplit(("https", parsed.hostname, path, "", ""))


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _canonical_json(document: dict[str, Any]) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _binding_artifacts(
    *,
    root: Path,
    catalog: Catalog,
    profile_id: str,
    binding_id: str,
    workload_id: str | None,
    policy_ids: list[str],
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
    example = render_dotenv(catalog, selected)
    variables: list[dict[str, Any]] = []
    for item in selected:
        metadata = catalog.variables[item.name]
        variable: dict[str, Any] = {
            "description": metadata["description"],
            "name": item.name,
            "required": item.required,
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
        "schema": "runtime-env/consumer-binding/v1",
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
                "repository": _repository_url(_git(root, "remote", "get-url", "origin")),
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
                "repository": _repository_url(_git(root, "remote", "get-url", "origin")),
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
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
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
    )
    drift = False
    for relative_path, expected in artifacts.items():
        destination = target / relative_path
        current = destination.read_text(encoding="utf-8") if destination.is_file() else None
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
        print(f"{state} {name}")
    print(f"OK local env metadata: {len(values)} declared names, values redacted")
    return 0


def initialize_local_env(*, catalog: Catalog, env_file: Path) -> int:
    path = env_file.expanduser().absolute()
    if path.exists() or path.is_symlink():
        raise ContractError(f"local env already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    variables = select_variables(catalog, profile_id=None, include_all=True)
    _atomic_write(path, render_dotenv(catalog, variables))
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
        manifests = [path for path in skill_root.iterdir() if path.name.lower() == "skill.md"]
        if len(manifests) != 1:
            if manifests:
                raise ContractError(f"skill {skill_root.name}: multiple skill manifests")
            continue
        manifest = manifests[0]
        runtime_modules: list[str] = []
        assertion_modules: list[str] = []
        searchable_text: list[str] = []
        for current_root, directory_names, file_names in os.walk(skill_root, followlinks=True):
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
                        Path(".agents") / "skills" / skill_root.name / path.relative_to(skill_root)
                    ).as_posix()
                if path.suffix.lower() in {".md", ".py", ".sh", ".js", ".mjs", ".cjs", ".ts", ".tsx"}:
                    try:
                        searchable_text.append(path.read_text(encoding="utf-8"))
                    except (OSError, UnicodeDecodeError):
                        pass
                if path.suffix.lower() not in code_suffixes:
                    continue
                logical_parts = Path(relative).parts
                if any(part in {"tests", "test", "assertions", "evals"} for part in logical_parts):
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
            raise ContractError(f"missing staged consumer projection: {path.as_posix()}")
        return result.stdout
    try:
        return (target / path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractError(f"cannot read consumer projection {path}: {exc.strerror}") from exc


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
    if binding.get("schema") != "runtime-env/consumer-binding/v1":
        raise ContractError(f"{binding_path}: unexpected schema")
    if binding.get("binding") != binding_id:
        raise ContractError(f"{binding_path}: binding id mismatch")
    _verify_content_hash(binding, binding_path)

    render = binding.get("render")
    if not isinstance(render, dict) or not isinstance(render.get("path"), str):
        raise ContractError(f"{binding_path}: invalid render projection")
    example = _consumer_content(target, render["path"], staged=staged)
    if _sha256(example) != render.get("sha256"):
        raise ContractError(f"{render['path']}: render sha256 mismatch")

    projections = binding.get("projections")
    if not isinstance(projections, dict) or set(projections) != {"policies", "workload"}:
        raise ContractError(f"{binding_path}: invalid projection manifest")
    paths: list[str] = []
    workload_path = projections["workload"]
    if workload_path is not None:
        if not isinstance(workload_path, str):
            raise ContractError(f"{binding_path}: invalid workload projection path")
        paths.append(workload_path)
    policy_paths = projections["policies"]
    if not isinstance(policy_paths, list) or any(not isinstance(path, str) for path in policy_paths):
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
    sync_parser = subparsers.add_parser(
        "sync", help="explicitly synchronize a pinned, secret-free consumer binding"
    )
    sync_parser.add_argument("--profile", required=True)
    sync_parser.add_argument("--binding", required=True)
    sync_parser.add_argument("--workload")
    sync_parser.add_argument("--policy", action="append", default=[])
    sync_parser.add_argument("--target-root", type=Path, required=True)
    sync_mode = sync_parser.add_mutually_exclusive_group()
    sync_mode.add_argument("--apply", action="store_true")
    sync_mode.add_argument("--check", action="store_true")
    local_env_parser = subparsers.add_parser(
        "local-env", help="inspect host-only dotenv metadata without printing values"
    )
    local_env_subparsers = local_env_parser.add_subparsers(dest="local_env_command", required=True)
    local_env_init = local_env_subparsers.add_parser("init")
    local_env_init.add_argument("--env-file", type=Path)
    local_env_doctor = local_env_subparsers.add_parser("doctor")
    local_env_doctor.add_argument("--env-file", type=Path)
    workload_parser = subparsers.add_parser("workload", help="inspect typed local workloads")
    workload_subparsers = workload_parser.add_subparsers(dest="workload_command", required=True)
    workload_subparsers.add_parser("list")
    workload_show = workload_subparsers.add_parser("show")
    workload_show.add_argument("--id", required=True)
    policy_parser = subparsers.add_parser("policy", help="inspect native carrier policies")
    policy_subparsers = policy_parser.add_subparsers(dest="policy_command", required=True)
    policy_subparsers.add_parser("list")
    policy_show = policy_subparsers.add_parser("show")
    policy_show.add_argument("--id", required=True)
    inventory_parser = subparsers.add_parser(
        "inventory", help="enumerate physical runtime modules without reading secret values"
    )
    inventory_subparsers = inventory_parser.add_subparsers(
        dest="inventory_command", required=True
    )
    inventory_skills_parser = inventory_subparsers.add_parser("skills")
    inventory_skills_parser.add_argument("--repo-root", type=Path, required=True)
    verify_consumer_parser = subparsers.add_parser(
        "verify-consumer", help="verify consumer projections from the working tree or Git index"
    )
    verify_consumer_parser.add_argument("--target-root", type=Path, required=True)
    verify_consumer_parser.add_argument("--binding", required=True)
    verify_consumer_parser.add_argument("--staged", action="store_true")
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
    if args.command == "sync":
        try:
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
