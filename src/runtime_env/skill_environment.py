"""Resolve canonical Skill requirements into secret-free runtime-env plans.

This module deliberately owns only environment closure. Skill selection stays in
skills-shared; executable commands stay in checked-in runtime-env workloads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any

from .cli import ContractError, load_catalog, select_variables

SHA40 = __import__("re").compile(r"^[0-9a-f]{40}$")
SHA256 = __import__("re").compile(r"^[0-9a-f]{64}$")
MODES = {"local", "actions", "connector", "public-consumer"}
RECEIPT_SCHEMA = "skills-shared/skill-resolution-receipt/v1"
REQ_SCHEMA = "skills-shared/skill-runtime-requirements/v1"
BINDING_SCHEMA = "runtime-env/repo-skill-runtime-binding/v1"
PLAN_SCHEMA = "runtime-env/agent-environment-plan/v1"
ENV_RECEIPT_SCHEMA = "runtime-env/agent-environment-receipt/v1"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{path}: root must be an object")
    return value


def _strict(document: dict[str, Any], *, required: set[str], allowed: set[str], label: str) -> None:
    missing = sorted(required - set(document))
    extra = sorted(set(document) - allowed)
    if missing:
        raise ContractError(f"{label}: missing fields: {', '.join(missing)}")
    if extra:
        raise ContractError(f"{label}: unexpected fields: {', '.join(extra)}")


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=False)
    if proc.returncode:
        raise ContractError(f"git {' '.join(args)} failed for {root}")
    return proc.stdout.strip()


def _repo_subject(root: Path) -> tuple[str, str]:
    root = root.resolve()
    return _git(root, "rev-parse", "HEAD"), _git(root, "rev-parse", "HEAD^{tree}")


def _validate_identity(identity: dict[str, Any], label: str, *, tree: bool = False) -> None:
    required = {"repository", "commit"} | ({"tree"} if tree else set())
    _strict(identity, required=required, allowed=required, label=label)
    if not isinstance(identity["repository"], str) or not identity["repository"].strip():
        raise ContractError(f"{label}: repository must be non-empty")
    if not isinstance(identity["commit"], str) or not SHA40.fullmatch(identity["commit"]):
        raise ContractError(f"{label}: commit must be a full SHA")
    if tree and (not isinstance(identity["tree"], str) or not SHA40.fullmatch(identity["tree"])):
        raise ContractError(f"{label}: tree must be a full SHA")


def _validate_resolution(receipt: dict[str, Any]) -> None:
    _strict(
        receipt,
        required={"schema", "skills_shared", "consumer", "skills"},
        allowed={"schema", "skills_shared", "consumer", "skills"},
        label="skill resolution",
    )
    if receipt["schema"] != RECEIPT_SCHEMA:
        raise ContractError("unsupported skill-resolution receipt schema")
    _validate_identity(receipt["consumer"], "resolution consumer")
    ss = receipt["skills_shared"]
    _strict(ss, required={"repository", "commit", "registry_sha256"}, allowed={"repository", "commit", "registry_sha256"}, label="skills_shared")
    _validate_identity({"repository": ss["repository"], "commit": ss["commit"]}, "skills_shared")
    if not isinstance(ss["registry_sha256"], str) or not SHA256.fullmatch(ss["registry_sha256"]):
        raise ContractError("skills_shared.registry_sha256 must be sha256")
    skills = receipt["skills"]
    if not isinstance(skills, list) or not skills:
        raise ContractError("skill resolution must select at least one Skill")
    names: set[str] = set()
    for row in skills:
        if not isinstance(row, dict):
            raise ContractError("selected Skill must be an object")
        _strict(row, required={"name", "content_sha256", "runtime_requirements_sha256"}, allowed={"name", "content_sha256", "runtime_requirements_sha256"}, label="selected Skill")
        if not isinstance(row["name"], str) or not row["name"] or row["name"] in names:
            raise ContractError("selected Skill names must be unique non-empty strings")
        names.add(row["name"])
        for field in ("content_sha256", "runtime_requirements_sha256"):
            if not isinstance(row[field], str) or not SHA256.fullmatch(row[field]):
                raise ContractError(f"{row['name']}: {field} must be sha256")


def _validate_requirements(doc: dict[str, Any], skill: str) -> None:
    _strict(doc, required={"schema", "skill", "capabilities", "modes"}, allowed={"schema", "skill", "capabilities", "modes"}, label=f"requirements {skill}")
    if doc["schema"] != REQ_SCHEMA or doc["skill"] != skill:
        raise ContractError(f"{skill}: runtime requirements identity mismatch")
    caps = doc["capabilities"]
    if not isinstance(caps, dict) or set(caps) != {"required", "optional"}:
        raise ContractError(f"{skill}: capabilities must contain required and optional")
    required = caps["required"]
    optional = caps["optional"]
    if any(not isinstance(items, list) for items in (required, optional)):
        raise ContractError(f"{skill}: capability sets must be arrays")
    flat = required + optional
    if any(not isinstance(item, str) or not item for item in flat) or len(flat) != len(set(flat)):
        raise ContractError(f"{skill}: capability IDs must be unique strings")
    modes = doc["modes"]
    if not isinstance(modes, list) or not modes or any(mode not in MODES for mode in modes):
        raise ContractError(f"{skill}: invalid runtime modes")


def _validate_binding(binding: dict[str, Any]) -> None:
    _strict(binding, required={"schema", "consumer", "runtime_env", "mode", "skills"}, allowed={"schema", "consumer", "runtime_env", "mode", "skills"}, label="runtime binding")
    if binding["schema"] != BINDING_SCHEMA:
        raise ContractError("unsupported runtime binding schema")
    _validate_identity(binding["consumer"], "binding consumer")
    _validate_identity(binding["runtime_env"], "runtime_env", tree=True)
    if binding["mode"] not in MODES:
        raise ContractError("runtime binding mode is invalid")
    if not isinstance(binding["skills"], dict) or not binding["skills"]:
        raise ContractError("runtime binding needs explicit Skill mappings")


def _mapping_for(binding: dict[str, Any], skill: str, capability: str) -> dict[str, Any]:
    skill_binding = binding["skills"].get(skill)
    if not isinstance(skill_binding, dict):
        raise ContractError(f"no runtime binding for selected Skill {skill}")
    _strict(skill_binding, required={"requirements_sha256", "capability_map"}, allowed={"requirements_sha256", "capability_map"}, label=f"binding {skill}")
    if not isinstance(skill_binding["requirements_sha256"], str) or not SHA256.fullmatch(skill_binding["requirements_sha256"]):
        raise ContractError(f"{skill}: binding requirements_sha256 must be sha256")
    capability_map = skill_binding["capability_map"]
    if not isinstance(capability_map, dict):
        raise ContractError(f"{skill}: capability_map must be an object")
    mapping = capability_map.get(capability)
    if not isinstance(mapping, dict):
        raise ContractError(f"{skill}: required capability {capability} has no explicit mapping")
    allowed = {"modules", "profile", "workload", "policies", "setup_entrypoints", "probe_entrypoints"}
    _strict(mapping, required=allowed, allowed=allowed, label=f"mapping {skill}/{capability}")
    for key in ("modules", "policies", "setup_entrypoints", "probe_entrypoints"):
        if not isinstance(mapping[key], list) or any(not isinstance(x, str) or not x for x in mapping[key]):
            raise ContractError(f"{skill}/{capability}: {key} must be a string array")
    for key in ("profile", "workload"):
        if mapping[key] is not None and (not isinstance(mapping[key], str) or not mapping[key]):
            raise ContractError(f"{skill}/{capability}: {key} must be null or string")
    return mapping


def build_plan(*, catalog_root: Path, target_root: Path, resolution_path: Path, requirements_dir: Path, binding_path: Path) -> dict[str, Any]:
    catalog_root = catalog_root.resolve()
    target_root = target_root.resolve()
    receipt = _load(resolution_path)
    binding = _load(binding_path)
    _validate_resolution(receipt)
    _validate_binding(binding)

    consumer_head, _ = _repo_subject(target_root)
    if receipt["consumer"] != binding["consumer"]:
        raise ContractError("consumer identity differs between resolution and runtime binding")
    if consumer_head != receipt["consumer"]["commit"]:
        raise ContractError("consumer exact subject is stale")

    runtime_head, runtime_tree = _repo_subject(catalog_root)
    runtime_identity = binding["runtime_env"]
    if runtime_identity["commit"] != runtime_head or runtime_identity["tree"] != runtime_tree:
        raise ContractError("runtime-env exact subject is stale")

    catalog = load_catalog(catalog_root)
    selected_rows = {row["name"]: row for row in receipt["skills"]}
    if set(binding["skills"]) != set(selected_rows):
        raise ContractError("runtime binding Skill closure differs from resolution")

    modules: set[str] = set()
    policies: set[str] = set()
    profiles: set[str] = set()
    workloads: set[str] = set()
    setup: set[str] = set()
    probes: set[str] = set()
    required_caps: set[str] = set()
    optional_caps: set[str] = set()
    skill_subjects: list[dict[str, Any]] = []

    for skill in sorted(selected_rows):
        req_path = requirements_dir / f"{skill}.json"
        req = _load(req_path)
        _validate_requirements(req, skill)
        req_sha = _digest(req)
        selected = selected_rows[skill]
        skill_binding = binding["skills"][skill]
        if req_sha != selected["runtime_requirements_sha256"] or req_sha != skill_binding.get("requirements_sha256"):
            raise ContractError(f"{skill}: runtime requirements digest mismatch")
        if binding["mode"] not in req["modes"]:
            raise ContractError(f"{skill}: runtime mode {binding['mode']} is not admitted")
        required = req["capabilities"]["required"]
        optional = req["capabilities"]["optional"]
        required_caps.update(required)
        optional_caps.update(optional)
        for capability in required + optional:
            mapping = _mapping_for(binding, skill, capability)
            modules.update(mapping["modules"])
            policies.update(mapping["policies"])
            setup.update(mapping["setup_entrypoints"])
            probes.update(mapping["probe_entrypoints"])
            if mapping["profile"]:
                profiles.add(mapping["profile"])
            if mapping["workload"]:
                workloads.add(mapping["workload"])
        skill_subjects.append({
            "name": skill,
            "content_sha256": selected["content_sha256"],
            "runtime_requirements_sha256": req_sha,
        })

    optional_caps.difference_update(required_caps)
    if len(profiles) > 1:
        raise ContractError("PROFILE_CONFLICT: Skill mappings resolve to multiple profiles")
    if len(workloads) > 1:
        raise ContractError("WORKLOAD_CONFLICT: Skill mappings resolve to multiple workloads")
    profile = next(iter(profiles), None)
    workload = next(iter(workloads), None)

    for module in modules:
        if module not in catalog.modules:
            raise ContractError(f"unknown mapped module: {module}")
    for policy in policies:
        if policy not in catalog.policies:
            raise ContractError(f"unknown mapped policy: {policy}")
    if profile and profile not in catalog.profiles:
        raise ContractError(f"unknown mapped profile: {profile}")
    if workload and workload not in catalog.workloads:
        raise ContractError(f"unknown mapped workload: {workload}")
    if workload:
        if profile and catalog.workloads[workload]["profile"] != profile:
            raise ContractError("mapped workload/profile mismatch")
        known_entries = set(catalog.workloads[workload]["entrypoints"])
        unknown_entries = sorted((setup | probes) - known_entries)
        if unknown_entries:
            raise ContractError("unknown fixed entrypoints: " + ", ".join(unknown_entries))
    elif setup or probes:
        raise ContractError("fixed entrypoints require an explicit workload")

    required_secret_names: list[str] = []
    optional_secret_names: list[str] = []
    if profile:
        for selected in select_variables(catalog, profile_id=profile, include_all=False):
            if catalog.variables[selected.name]["secret"]:
                (required_secret_names if selected.required else optional_secret_names).append(selected.name)

    plan: dict[str, Any] = {
        "schema": PLAN_SCHEMA,
        "subject": {
            "consumer": receipt["consumer"],
            "skills_shared": receipt["skills_shared"],
            "runtime_env": runtime_identity,
        },
        "mode": binding["mode"],
        "skills": skill_subjects,
        "resolved": {
            "modules": sorted(modules),
            "profile": profile,
            "workload": workload,
            "policies": sorted(policies),
            "setup_entrypoints": sorted(setup),
            "probe_entrypoints": sorted(probes),
        },
        "capabilities": {"required": sorted(required_caps), "optional": sorted(optional_caps)},
        "secret_names": {"required": sorted(required_secret_names), "optional": sorted(optional_secret_names)},
        "authority": {
            "arbitrary_shell": False,
            "automatic_merge": False,
            "automatic_conflict_resolution": False,
            "visibility_change": False,
            "credential_values": False,
        },
        "claims": {
            "fixed_setup": "NOT_EXERCISED",
            "capability_probes": "NOT_EXERCISED",
            "environment_ready": "NOT_EXERCISED",
            "live_git_town": "NOT_EXERCISED",
            "live_forgejo": "NOT_EXERCISED",
        },
    }
    plan["plan_sha256"] = _digest(plan)
    return plan


def validate_plan(plan: dict[str, Any]) -> None:
    if plan.get("schema") != PLAN_SCHEMA:
        raise ContractError("unsupported environment plan schema")
    supplied = plan.get("plan_sha256")
    if not isinstance(supplied, str) or not SHA256.fullmatch(supplied):
        raise ContractError("environment plan digest missing")
    unsigned = dict(plan)
    unsigned.pop("plan_sha256", None)
    if _digest(unsigned) != supplied:
        raise ContractError("environment plan digest mismatch")
    authority = plan.get("authority")
    if not isinstance(authority, dict) or any(authority.values()):
        raise ContractError("environment plan attempted authority widening")
    claims = plan.get("claims")
    if not isinstance(claims, dict) or any(value != "NOT_EXERCISED" for value in claims.values()):
        raise ContractError("portable environment plan cannot claim runtime PASS")


def _dotenv_names(path: Path | None) -> set[str]:
    if path is None:
        return set(os.environ)
    path = path.expanduser()
    if not path.is_file():
        raise ContractError(f"env file not found: {path}")
    names: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _ = line.split("=", 1)
        if name:
            names.add(name)
    return names


def check_plan(plan: dict[str, Any], env_file: Path | None) -> tuple[dict[str, Any], int]:
    validate_plan(plan)
    names = _dotenv_names(env_file)
    required = plan.get("secret_names", {}).get("required", [])
    optional = plan.get("secret_names", {}).get("optional", [])
    missing = [name for name in required if name not in names]
    result = {
        "schema": "runtime-env/agent-environment-check/v1",
        "plan_sha256": plan["plan_sha256"],
        "required_secret_presence": {name: ("PRESENT" if name in names else "ABSENT") for name in required},
        "optional_secret_presence": {name: ("PRESENT" if name in names else "ABSENT") for name in optional},
        "execution_state": "BLOCKED" if missing else "NOT_EXERCISED",
        "missing_required_names": missing,
    }
    return result, (3 if missing else 0)


def prepare_plan(plan: dict[str, Any], *, catalog_root: Path, target_root: Path, env_file: Path | None, receipt_path: Path) -> int:
    validate_plan(plan)
    if plan.get("mode") in {"connector", "public-consumer"}:
        raise ContractError(f"{plan.get('mode')} mode cannot execute host workloads")
    check, check_exit = check_plan(plan, env_file)
    if check_exit:
        raise ContractError("required secret names are absent")
    resolved = plan["resolved"]
    workload = resolved.get("workload")
    all_entries = list(resolved.get("setup_entrypoints", [])) + list(resolved.get("probe_entrypoints", []))
    if not workload or not all_entries:
        raise ContractError("prepare requires an explicit workload and fixed setup/probe entrypoints")

    receipt_path = receipt_path.expanduser().absolute()
    if receipt_path.exists() or receipt_path.is_symlink():
        raise ContractError(f"environment receipt already exists: {receipt_path}")
    receipt_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    parent = receipt_path.parent.stat()
    if parent.st_uid != os.getuid() or stat.S_IMODE(parent.st_mode) != 0o700:
        raise ContractError("environment receipt directory must be user-owned mode 0700")
    detail_dir = receipt_path.parent / (receipt_path.stem + ".d")
    detail_dir.mkdir(mode=0o700)
    runtime_cli = catalog_root.resolve() / "runtime-env"
    executions: list[dict[str, Any]] = []
    ok = True
    for entrypoint in all_entries:
        child_receipt = detail_dir / f"{entrypoint}.json"
        command = [str(runtime_cli), "--catalog-root", str(catalog_root.resolve()), "workload", "run", "--id", workload, "--entrypoint", entrypoint, "--target-root", str(target_root.resolve()), "--receipt", str(child_receipt), "--json"]
        if env_file is not None:
            command += ["--env-file", str(env_file.expanduser().absolute())]
        proc = subprocess.run(command, text=True, capture_output=True, check=False)
        executions.append({
            "entrypoint": entrypoint,
            "exit": proc.returncode,
            "receipt_sha256": hashlib.sha256(child_receipt.read_bytes()).hexdigest() if child_receipt.is_file() else None,
        })
        if proc.returncode != 0:
            ok = False
            break
    probe_set = set(resolved.get("probe_entrypoints", []))
    executed_probes = {row["entrypoint"] for row in executions if row["exit"] == 0 and row["entrypoint"] in probe_set}
    probes_passed = executed_probes == probe_set
    receipt = {
        "schema": ENV_RECEIPT_SCHEMA,
        "plan_sha256": plan["plan_sha256"],
        "runtime_env": plan["subject"]["runtime_env"],
        "consumer": plan["subject"]["consumer"],
        "executions": executions,
        "required_secret_presence": check["required_secret_presence"],
        "fixed_setup": "PASS" if ok else "FAIL",
        "capability_probes": "PASS" if ok and probes_passed else "FAIL",
        "environment_ready": "PASS" if ok and probes_passed else "FAIL",
        "live_git_town": "NOT_EXERCISED",
        "live_forgejo": "NOT_EXERCISED",
    }
    encoded = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
    fd = os.open(receipt_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(encoded)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["environment_ready"] == "PASS" else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="runtime-env skills")
    parser.add_argument("--catalog-root", type=Path, default=Path(__file__).resolve().parents[2])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("resolve", "plan"):
        p = sub.add_parser(name)
        p.add_argument("--target-root", type=Path, required=True)
        p.add_argument("--skill-resolution", type=Path, required=True)
        p.add_argument("--requirements-dir", type=Path, required=True)
        p.add_argument("--binding", type=Path, required=True)
        if name == "plan":
            p.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("check")
    check.add_argument("--plan", type=Path, required=True)
    check.add_argument("--env-file", type=Path)
    check.add_argument("--json", action="store_true")
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--plan", type=Path, required=True)
    prepare.add_argument("--target-root", type=Path, required=True)
    prepare.add_argument("--env-file", type=Path)
    prepare.add_argument("--receipt", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command in {"resolve", "plan"}:
            plan = build_plan(catalog_root=args.catalog_root, target_root=args.target_root, resolution_path=args.skill_resolution, requirements_dir=args.requirements_dir, binding_path=args.binding)
            if args.command == "resolve":
                summary = {"schema": "runtime-env/skill-environment-resolution/v1", "plan_sha256": plan["plan_sha256"], "skills": [row["name"] for row in plan["skills"]], "resolved": plan["resolved"], "claims": plan["claims"]}
                print(json.dumps(summary, indent=2, sort_keys=True))
            else:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                print(f"OK environment plan {plan['plan_sha256']} -> {args.output}")
            return 0
        plan = _load(args.plan)
        if args.command == "check":
            result, code = check_plan(plan, args.env_file)
            print(json.dumps(result, sort_keys=True) if args.json else json.dumps(result, indent=2, sort_keys=True))
            return code
        return prepare_plan(plan, catalog_root=args.catalog_root, target_root=args.target_root, env_file=args.env_file, receipt_path=args.receipt)
    except ContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
