"""Strict, non-executable workload isolation policy contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


SCHEMA = "runtime-env/workload-isolation-policy/v1"
ALLOWED_FIELDS = {
    "schema",
    "id",
    "summary",
    "allowed_classes",
    "forbidden_execution_surfaces",
    "non_equivalence",
    "absence_semantics",
    "owner",
    "reference",
}
REQUIRED_FIELDS = set(ALLOWED_FIELDS)
EVIDENCE_CLASSES = {
    "STATIC",
    "LOCAL",
    "EMULATOR",
    "PHYSICAL",
    "PRIVILEGED",
    "STORE_POLICY",
}
REQUIRED_FORBIDDEN_SURFACES = {
    "caller-supplied-shell",
    "generic-command-string",
    "generic-terminal",
    "root-fallback",
}
EXPECTED_ABSENCE_SEMANTICS = {
    "missing_runtime": "ABSENT",
    "missing_subject": "ABSENT",
    "unsupported_capability": "UNSUPPORTED",
    "not_exercised": "NOT_EXERCISED",
    "policy_denied": "DENIED",
}
POLICY_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REPOSITORY_ID = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
DEVICE_SERIAL = re.compile(r"(?:emulator-\d{4,}|(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}|R\d{10,})")
SECRET_MARKERS = (
    "sk-",
    "ghp_",
    "github_pat_",
    "akia",
    "begin private key",
    "password=",
    "token=",
    "secret=",
)
COMMAND_MARKERS = ("&&", "||", "`", "$(", ";")
ENDPOINT_MARKERS = ("://", "localhost", "127.0.0.1")
LOCAL_PATH_MARKERS = ("/users/", "/home/", "/var/", "c:\\")


class IsolationPolicyError(ValueError):
    """A workload-isolation policy cannot be admitted safely."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise IsolationPolicyError(f"missing isolation policy file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise IsolationPolicyError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise IsolationPolicyError(f"{path}: isolation policy must be an object")
    return value


def _bounded_string(value: Any, field: str, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise IsolationPolicyError(f"{field} must be a bounded non-empty string")
    if any(char.isprintable() is False for char in value):
        raise IsolationPolicyError(f"{field} contains control characters")
    return value


def _reject_sensitive_or_executable_text(value: str, field: str) -> None:
    lower = value.lower()
    if any(marker in lower for marker in SECRET_MARKERS):
        raise IsolationPolicyError(f"{field}: secret-bearing policy content is forbidden")
    if any(marker in lower for marker in ENDPOINT_MARKERS):
        raise IsolationPolicyError(f"{field}: endpoint-bearing policy content is forbidden")
    if any(marker in lower for marker in LOCAL_PATH_MARKERS):
        raise IsolationPolicyError(f"{field}: local-path policy content is forbidden")
    if DEVICE_SERIAL.search(value):
        raise IsolationPolicyError(f"{field}: device-serial policy content is forbidden")
    if any(marker in value for marker in COMMAND_MARKERS):
        raise IsolationPolicyError(f"{field}: command-bearing policy content is forbidden")


def _validate_reference(value: Any, field: str) -> None:
    if not isinstance(value, dict) or set(value) != {"repository", "issue"}:
        raise IsolationPolicyError(f"{field} must contain repository and issue only")
    repository = _bounded_string(value["repository"], f"{field}.repository", 200)
    if not REPOSITORY_ID.fullmatch(repository):
        raise IsolationPolicyError(f"{field}.repository must be owner/repository")
    issue = value["issue"]
    if not isinstance(issue, int) or isinstance(issue, bool) or issue <= 0:
        raise IsolationPolicyError(f"{field}.issue must be a positive integer")


def validate_isolation_policy_document(document: dict[str, Any], *, filename: str | None = None) -> dict[str, Any]:
    unexpected = sorted(set(document) - ALLOWED_FIELDS)
    if unexpected:
        raise IsolationPolicyError(f"unexpected isolation-policy fields: {', '.join(unexpected)}")
    missing = sorted(REQUIRED_FIELDS - set(document))
    if missing:
        raise IsolationPolicyError(f"missing isolation-policy fields: {', '.join(missing)}")
    if document.get("schema") != SCHEMA:
        raise IsolationPolicyError(f"expected schema {SCHEMA}")

    policy_id = _bounded_string(document.get("id"), "id", 128)
    if not POLICY_ID.fullmatch(policy_id):
        raise IsolationPolicyError("id must be a canonical kebab-case identifier")
    if filename is not None and Path(filename).stem != policy_id:
        raise IsolationPolicyError("isolation policy id must match filename")

    summary = _bounded_string(document.get("summary"), "summary")
    _reject_sensitive_or_executable_text(summary, "summary")

    allowed = document.get("allowed_classes")
    if (
        not isinstance(allowed, list)
        or not allowed
        or any(not isinstance(item, str) or item not in EVIDENCE_CLASSES for item in allowed)
        or len(allowed) != len(set(allowed))
    ):
        raise IsolationPolicyError("allowed_classes must be a non-empty unique evidence-class array")
    allowed_set = set(allowed)

    surfaces = document.get("forbidden_execution_surfaces")
    if (
        not isinstance(surfaces, list)
        or not surfaces
        or any(not isinstance(item, str) or not POLICY_ID.fullmatch(item) for item in surfaces)
        or len(surfaces) != len(set(surfaces))
    ):
        raise IsolationPolicyError("forbidden_execution_surfaces must contain canonical identifiers only")
    missing_hard_denials = sorted(REQUIRED_FORBIDDEN_SURFACES - set(surfaces))
    if missing_hard_denials:
        raise IsolationPolicyError(
            "isolation policy omitted hard execution denials: " + ", ".join(missing_hard_denials)
        )

    non_equivalence = document.get("non_equivalence")
    if not isinstance(non_equivalence, list) or not non_equivalence:
        raise IsolationPolicyError("non_equivalence must be a non-empty array")
    seen: dict[str, set[str]] = {}
    for rule in non_equivalence:
        if not isinstance(rule, dict) or set(rule) != {"observed", "cannot_satisfy"}:
            raise IsolationPolicyError("non_equivalence entries require observed and cannot_satisfy only")
        observed = rule.get("observed")
        cannot = rule.get("cannot_satisfy")
        if observed not in allowed_set or observed in seen:
            raise IsolationPolicyError("non_equivalence observed class must be unique and allowed")
        if (
            not isinstance(cannot, list)
            or not cannot
            or any(item not in allowed_set for item in cannot)
            or observed in cannot
            or len(cannot) != len(set(cannot))
        ):
            raise IsolationPolicyError("non_equivalence cannot_satisfy must name unique other allowed classes")
        seen[observed] = set(cannot)
    if set(seen) != allowed_set:
        raise IsolationPolicyError("every allowed evidence class requires a non-equivalence rule")
    for observed in sorted(allowed_set):
        expected = allowed_set - {observed}
        if seen[observed] != expected:
            raise IsolationPolicyError(
                f"evidence-lane promotion is forbidden: {observed} must remain non-equivalent to every other allowed class"
            )

    absence = document.get("absence_semantics")
    if absence != EXPECTED_ABSENCE_SEMANTICS:
        raise IsolationPolicyError("absence_semantics must preserve the stable fail-closed state mapping")

    _validate_reference(document.get("owner"), "owner")
    _validate_reference(document.get("reference"), "reference")
    return document


def load_isolation_policy_directory(directory: Path) -> dict[str, dict[str, Any]]:
    if not directory.is_dir():
        raise IsolationPolicyError(f"missing isolation-policies directory: {directory}")
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise IsolationPolicyError("isolation-policies directory is empty")
    documents: dict[str, dict[str, Any]] = {}
    for path in paths:
        document = validate_isolation_policy_document(_load_json(path), filename=path.name)
        policy_id = document["id"]
        if policy_id in documents:
            raise IsolationPolicyError(f"duplicate isolation policy id: {policy_id}")
        documents[policy_id] = document
    return documents


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate workload isolation policy contracts")
    parser.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    policies = load_isolation_policy_directory(args.directory.resolve())
    print(json.dumps({"state": "PASS", "schema": SCHEMA, "policies": sorted(policies)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
