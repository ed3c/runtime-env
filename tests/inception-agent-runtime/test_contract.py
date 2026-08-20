from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "contracts" / "inception-runtime-capability.schema.json").read_text()
)
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
CAPABILITY_STATES = {"UNKNOWN", "UNSUPPORTED", "NOT_EXERCISED", "SUPPORTED"}


class ContractError(ValueError):
    pass


def valid_contract() -> dict:
    return {
        "schema_version": "runtime-env/inception-runtime-capability/v1",
        "workload": {
            "name": "inception-agent-probe",
            "image_digest": "sha256:" + "1" * 64,
            "argv": ["python3", "-m", "runtime_probe"],
            "timeout_seconds": 60,
            "resources": {
                "cpu_millis": 1000,
                "memory_mb": 512,
                "pids": 64,
                "output_bytes": 1048576,
            },
        },
        "policy": {
            "policy_digest": "sha256:" + "2" * 64,
            "network": "NONE",
            "privileged": False,
            "host_mounts": [],
            "run_as_root": False,
        },
        "environment_names": ["TASK_ID", "WORKSPACE_LEASE_ID"],
        "workspace_lease": {
            "lease_id": "lease:inception-a2r:fixture",
            "workspace_name": "inception-a2r-fixture",
            "expires_at": "2026-08-20T00:00:00Z",
        },
        "capabilities": {
            "streaming_visibility": "NOT_EXERCISED",
            "safe_transaction_boundary": "NOT_EXERCISED",
            "cancellation": "UNKNOWN",
            "resume": "UNKNOWN",
            "assistant_prefill": "UNSUPPORTED",
            "tokenizer_identity": "NOT_EXERCISED",
            "context_limit": "NOT_EXERCISED",
            "tool_call_transactions": "NOT_EXERCISED",
            "hidden_reasoning_access": "ABSENT",
        },
        "cleanup": {
            "descendants_terminated": True,
            "workspace_removed": True,
            "residue_inventory_required": True,
        },
        "evidence": {
            "offline_contract": "PASS",
            "local_execution": "NOT_EXERCISED",
            "provider_observation": "NOT_EXERCISED",
        },
    }


def validate_contract(value: dict, *, now: datetime) -> None:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ContractError("evaluation clock must be timezone-aware")
    if value.get("schema_version") != "runtime-env/inception-runtime-capability/v1":
        raise ContractError("schema_version")
    allowed_top = {
        "schema_version", "workload", "policy", "environment_names",
        "workspace_lease", "capabilities", "cleanup", "evidence",
    }
    if set(value) != allowed_top:
        raise ContractError("unknown or missing top-level field")

    workload = value["workload"]
    if workload.get("name") != "inception-agent-probe":
        raise ContractError("workload name")
    if not DIGEST.fullmatch(str(workload.get("image_digest", ""))):
        raise ContractError("image must be immutable digest")
    argv = workload.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
        raise ContractError("argv")
    if any(token in {"sh", "bash", "zsh", "cmd.exe", "powershell"} for token in argv[:1]):
        raise ContractError("generic shell entrypoint")
    timeout = workload.get("timeout_seconds")
    if not isinstance(timeout, int) or not 1 <= timeout <= 900:
        raise ContractError("timeout")
    resources = workload.get("resources", {})
    for key in ("cpu_millis", "memory_mb", "pids", "output_bytes"):
        if not isinstance(resources.get(key), int) or resources[key] <= 0:
            raise ContractError(f"resource {key}")

    policy = value["policy"]
    if not DIGEST.fullmatch(str(policy.get("policy_digest", ""))):
        raise ContractError("policy digest")
    if policy.get("network") not in {"NONE", "ALLOWLIST_ONLY"}:
        raise ContractError("network")
    if policy.get("privileged") is not False or policy.get("run_as_root") is not False:
        raise ContractError("privilege")
    if policy.get("host_mounts") != []:
        raise ContractError("host mounts")

    env_names = value["environment_names"]
    if len(env_names) != len(set(env_names)):
        raise ContractError("duplicate environment name")
    if any(not re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", name) for name in env_names):
        raise ContractError("environment names only")
    if any("=" in name for name in env_names):
        raise ContractError("secret value")

    lease = value["workspace_lease"]
    if "/" in lease.get("workspace_name", "") or ".." in lease.get("workspace_name", ""):
        raise ContractError("workspace escape")
    try:
        expires_at = datetime.fromisoformat(lease["expires_at"].replace("Z", "+00:00"))
    except Exception as exc:
        raise ContractError("lease expiry") from exc
    if expires_at.tzinfo is None or expires_at.utcoffset() is None:
        raise ContractError("lease expiry must be timezone-aware")
    if expires_at <= now.astimezone(timezone.utc):
        raise ContractError("stale lease")

    capabilities = value["capabilities"]
    expected_capabilities = {
        "streaming_visibility", "safe_transaction_boundary", "cancellation",
        "resume", "assistant_prefill", "tokenizer_identity", "context_limit",
        "tool_call_transactions", "hidden_reasoning_access",
    }
    if set(capabilities) != expected_capabilities:
        raise ContractError("capability denominator")
    for name in expected_capabilities - {"hidden_reasoning_access"}:
        if capabilities[name] not in CAPABILITY_STATES:
            raise ContractError(f"capability state {name}")
    if capabilities["hidden_reasoning_access"] != "ABSENT":
        raise ContractError("hidden reasoning is not a runtime capability")

    cleanup = value["cleanup"]
    if cleanup != {
        "descendants_terminated": True,
        "workspace_removed": True,
        "residue_inventory_required": True,
    }:
        raise ContractError("cleanup")

    evidence = value["evidence"]
    if evidence.get("offline_contract") not in {"PASS", "FAIL"}:
        raise ContractError("offline evidence")
    for lane in ("local_execution", "provider_observation"):
        if evidence.get(lane) not in {"NOT_EXERCISED", "PASS", "FAIL", "BLOCKED"}:
            raise ContractError(lane)
    if evidence["offline_contract"] == "PASS" and (
        evidence["local_execution"] == "PASS" or evidence["provider_observation"] == "PASS"
    ):
        raise ContractError("offline PASS cannot proxy local/provider PASS")


class RuntimeCapabilityContractTests(unittest.TestCase):
    NOW = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)

    def test_schema_is_closed_and_publishes_required_hard_bounds(self) -> None:
        self.assertFalse(SCHEMA["additionalProperties"])
        self.assertEqual(
            set(SCHEMA["required"]),
            {
                "schema_version", "workload", "policy", "environment_names",
                "workspace_lease", "capabilities", "cleanup", "evidence",
            },
        )
        self.assertEqual(
            SCHEMA["properties"]["capabilities"]["properties"]["hidden_reasoning_access"],
            {"const": "ABSENT"},
        )
        self.assertEqual(
            SCHEMA["properties"]["policy"]["properties"]["privileged"],
            {"const": False},
        )

    def test_valid_secret_free_contract_passes(self) -> None:
        validate_contract(valid_contract(), now=self.NOW)

    def assert_refused(self, mutate, pattern: str) -> None:
        value = deepcopy(valid_contract())
        mutate(value)
        with self.assertRaisesRegex(ContractError, pattern):
            validate_contract(value, now=self.NOW)

    def test_mutable_image_shell_secret_privilege_mount_and_escape_are_refused(self) -> None:
        self.assert_refused(
            lambda v: v["workload"].update(image_digest="runtime:latest"), "immutable"
        )
        self.assert_refused(
            lambda v: v["workload"].update(argv=["bash", "-lc", "echo ok"]), "shell"
        )
        self.assert_refused(
            lambda v: v.update(environment_names=["API_KEY=secret"]), "environment"
        )
        self.assert_refused(
            lambda v: v["policy"].update(privileged=True), "privilege"
        )
        self.assert_refused(
            lambda v: v["policy"].update(host_mounts=["host-root"]), "mount"
        )
        self.assert_refused(
            lambda v: v["workspace_lease"].update(workspace_name="../escape"), "escape"
        )

    def test_stale_lease_missing_cleanup_and_hidden_reasoning_are_refused(self) -> None:
        self.assert_refused(
            lambda v: v["workspace_lease"].update(expires_at="2026-08-18T00:00:00Z"),
            "stale lease",
        )
        self.assert_refused(
            lambda v: v["cleanup"].update(workspace_removed=False), "cleanup"
        )
        self.assert_refused(
            lambda v: v["capabilities"].update(hidden_reasoning_access="SUPPORTED"),
            "hidden reasoning",
        )

    def test_offline_contract_pass_cannot_promote_local_or_provider_evidence(self) -> None:
        self.assert_refused(
            lambda v: v["evidence"].update(local_execution="PASS"), "cannot proxy"
        )
        self.assert_refused(
            lambda v: v["evidence"].update(provider_observation="PASS"), "cannot proxy"
        )

    def test_naive_evaluation_clock_is_refused(self) -> None:
        with self.assertRaisesRegex(ContractError, "timezone-aware"):
            validate_contract(valid_contract(), now=self.NOW.replace(tzinfo=None))


if __name__ == "__main__":
    unittest.main()
