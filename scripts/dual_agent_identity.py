#!/usr/bin/env python3
"""Provider-neutral Dual-Agent workload identity binding contract.

This checker freezes deterministic metadata semantics only. It does not contact an
identity/policy/secret provider, issue credentials, or treat transport auth as
execution authorization.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "contracts" / "dual-agent-identity" / "workload-identity-binding.v1.schema.json"
EXPECTED_CONTRACT_SET_DIGEST = "e6671977dbf0a378474f924a142a82843bc0e3429f4546ffb0145af73f7827fe"
H40 = re.compile(r"^[0-9a-f]{40}$")
H64 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_AUDIENCE = {
    "LOCAL": "runtime-env/dual-agent/local",
    "CLOUD": "runtime-env/dual-agent/cloud",
}


class IdentityRefusal(RuntimeError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise IdentityRefusal(code, detail)


def fixed_binding(lane: str) -> dict[str, Any]:
    lower = lane.lower()
    return {
        "schema": "runtime-env/dual-agent-identity/workload-identity-binding/v1",
        "binding_id": f"dual-agent-{lower}-worker",
        "execution_lane": lane,
        "workload_subject": {
            "repository": "example/workload",
            "commit": "a" * 40,
            "tree": "b" * 40,
        },
        "identity_ref": f"identity-ref://{lower}/worker-demo",
        "tenant_scope": "tenant-demo",
        "audience": EXPECTED_AUDIENCE[lane],
        "enrollment": {
            "state": "NOT_EXERCISED",
            "evidence_kind": "NONE",
            "evidence_digest": None,
        },
        "capability": {
            "grant_ref": f"grant-{lower}-worker",
            "capabilities": ["workload.execute"],
            "fallback_capabilities": [],
        },
        "policy": {
            "digest": "3" * 64,
            "epoch": 1,
            "state": "CURRENT",
        },
        "secret_handles": [
            {
                "id": "secret://runtime/api-handle",
                "lease_state": "UNRESOLVED",
                "expires_at": None,
            }
        ],
        "credential_presentation": {
            "mode": "NONE",
            "state": "NOT_EXERCISED",
            "evidence_digest": None,
        },
        "transport_auth_state": "NOT_EXERCISED",
        "contract_set_digest": EXPECTED_CONTRACT_SET_DIGEST,
        "external_states": {
            "task": "NOT_EXERCISED",
            "provider": "NOT_EXERCISED",
            "user_outcome": "NOT_EXERCISED",
            "release": "NOT_EXERCISED",
        },
        "claims_not_proven": [
            "LIVE_IDENTITY_ENROLLMENT",
            "LIVE_POLICY_DECISION",
            "SECRET_RESOLUTION",
            "CREDENTIAL_ISSUANCE",
            "PROVIDER_EXECUTION",
            "TASK_SUCCESS",
            "USER_OUTCOME",
            "RELEASE",
        ],
    }


def validate_binding(binding: dict[str, Any]) -> None:
    if binding.get("schema") != "runtime-env/dual-agent-identity/workload-identity-binding/v1":
        refuse("IDENTITY_SCHEMA_MISMATCH")
    lane = binding.get("execution_lane")
    if lane not in EXPECTED_AUDIENCE:
        refuse("LANE_SUBSTITUTION")
    subject = binding.get("workload_subject")
    if not isinstance(subject, dict) or not H40.fullmatch(str(subject.get("commit", ""))) or not H40.fullmatch(str(subject.get("tree", ""))):
        refuse("MUTABLE_WORKLOAD_SUBJECT")
    repository = subject.get("repository")
    if not isinstance(repository, str) or "/" not in repository:
        refuse("MUTABLE_WORKLOAD_SUBJECT")

    identity_ref = binding.get("identity_ref")
    if not isinstance(identity_ref, str) or not identity_ref.startswith("identity-ref://"):
        refuse("SECRET_VALUE_LEAK")
    audience = binding.get("audience")
    if audience != EXPECTED_AUDIENCE[lane] or "*" in str(audience):
        refuse("WRONG_AUDIENCE")
    if binding.get("contract_set_digest") != EXPECTED_CONTRACT_SET_DIGEST:
        refuse("CONTRACT_SET_MISMATCH")

    enrollment = binding.get("enrollment")
    if not isinstance(enrollment, dict):
        refuse("IDENTITY_SCHEMA_MISMATCH", "enrollment")
    state = enrollment.get("state")
    if state == "REVOKED":
        refuse("REVOKED_IDENTITY")
    if state == "EXPIRED":
        refuse("EXPIRED_IDENTITY_LEASE")
    if state in ("ATTESTED", "ENROLLED"):
        if enrollment.get("evidence_kind") != "ATTESTATION_RECEIPT" or not H64.fullmatch(str(enrollment.get("evidence_digest", ""))):
            refuse("PACKAGE_PRESENCE_AS_ENROLLMENT_PASS")
    elif state == "NOT_EXERCISED":
        if enrollment.get("evidence_kind") != "NONE" or enrollment.get("evidence_digest") is not None:
            refuse("PACKAGE_PRESENCE_AS_ENROLLMENT_PASS")
    else:
        refuse("IDENTITY_SCHEMA_MISMATCH", "enrollment state")

    capability = binding.get("capability")
    if not isinstance(capability, dict):
        refuse("IDENTITY_SCHEMA_MISMATCH", "capability")
    capabilities = capability.get("capabilities", [])
    fallback = capability.get("fallback_capabilities", [])
    if not capabilities or any("*" in str(item) for item in capabilities):
        refuse("WILDCARD_CAPABILITY")
    if any(item not in capabilities for item in fallback):
        refuse("PROVIDER_FALLBACK_AUTHORITY_WIDENING")

    policy = binding.get("policy")
    if not isinstance(policy, dict) or not H64.fullmatch(str(policy.get("digest", ""))) or not isinstance(policy.get("epoch"), int) or policy["epoch"] < 1:
        refuse("IDENTITY_SCHEMA_MISMATCH", "policy")
    if policy.get("state") == "STALE":
        refuse("POLICY_STALE")
    if policy.get("state") == "REFUSED":
        refuse("POLICY_REFUSED")
    if policy.get("state") != "CURRENT":
        refuse("IDENTITY_SCHEMA_MISMATCH", "policy state")

    handles = binding.get("secret_handles")
    if not isinstance(handles, list):
        refuse("IDENTITY_SCHEMA_MISMATCH", "secret handles")
    for handle in handles:
        if not isinstance(handle, dict) or not isinstance(handle.get("id"), str) or not handle["id"].startswith("secret://"):
            refuse("SECRET_VALUE_LEAK")
        lease = handle.get("lease_state")
        if lease == "REVOKED":
            refuse("REVOKED_IDENTITY")
        if lease == "EXPIRED":
            refuse("EXPIRED_IDENTITY_LEASE")
        if lease not in ("UNRESOLVED", "ACTIVE", "RELEASED"):
            refuse("IDENTITY_SCHEMA_MISMATCH", "secret lease")

    credential = binding.get("credential_presentation")
    if not isinstance(credential, dict):
        refuse("IDENTITY_SCHEMA_MISMATCH", "credential presentation")
    if credential.get("state") == "REVOKED":
        refuse("REVOKED_IDENTITY")
    if credential.get("state") == "EXPIRED":
        refuse("EXPIRED_IDENTITY_LEASE")
    if credential.get("state") == "ISSUED" and not H64.fullmatch(str(credential.get("evidence_digest", ""))):
        refuse("PACKAGE_PRESENCE_AS_ENROLLMENT_PASS")
    if credential.get("state") == "NOT_EXERCISED" and credential.get("evidence_digest") is not None:
        refuse("PACKAGE_PRESENCE_AS_ENROLLMENT_PASS")

    external = binding.get("external_states")
    if not isinstance(external, dict) or any(value != "NOT_EXERCISED" for value in external.values()):
        if binding.get("transport_auth_state") == "AUTHENTICATED" and external.get("task") == "PASS":
            refuse("TRANSPORT_AUTH_AS_TASK_PASS")
        refuse("FIXTURE_AS_LIVE_PASS")


def validate_pair(local: dict[str, Any], cloud: dict[str, Any]) -> None:
    validate_binding(local)
    validate_binding(cloud)
    if local.get("execution_lane") != "LOCAL" or cloud.get("execution_lane") != "CLOUD":
        refuse("LANE_SUBSTITUTION")
    if local.get("tenant_scope") != cloud.get("tenant_scope"):
        refuse("WRONG_AUDIENCE", "tenant mismatch")
    if local.get("identity_ref") == cloud.get("identity_ref"):
        refuse("LOCAL_IDENTITY_REUSED_AS_CLOUD")
    if local.get("audience") == cloud.get("audience"):
        refuse("WRONG_AUDIENCE", "shared audience")


def receipt(local: dict[str, Any], cloud: dict[str, Any]) -> dict[str, Any]:
    validate_pair(local, cloud)
    return {
        "schema": "runtime-env/dual-agent-identity/contract-receipt/v1",
        "contract_state": "PASS",
        "local_binding": local["binding_id"],
        "cloud_binding": cloud["binding_id"],
        "local_identity_state": "NOT_EXERCISED",
        "cloud_identity_state": "NOT_EXERCISED",
        "policy_provider_state": "NOT_EXERCISED",
        "secret_provider_state": "NOT_EXERCISED",
        "credential_issuance_state": "NOT_EXERCISED",
        "task_state": "NOT_EXERCISED",
        "user_outcome_state": "NOT_EXERCISED",
        "release_state": "NOT_EXERCISED",
        "evidence_ceiling": "DETERMINISTIC_IDENTITY_CONTRACT_ONLY",
    }


def expect(code: str, fn: Any) -> None:
    try:
        fn()
    except IdentityRefusal as exc:
        if exc.code != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def selftest() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False

    local = fixed_binding("LOCAL")
    cloud = fixed_binding("CLOUD")
    result = receipt(local, cloud)
    assert result["contract_state"] == "PASS"
    assert result["local_identity_state"] == "NOT_EXERCISED"
    assert result["cloud_identity_state"] == "NOT_EXERCISED"

    bad = copy.deepcopy(cloud); bad["audience"] = "runtime-env/dual-agent/local"
    expect("WRONG_AUDIENCE", lambda: validate_binding(bad))
    bad = copy.deepcopy(cloud); bad["identity_ref"] = local["identity_ref"]
    expect("LOCAL_IDENTITY_REUSED_AS_CLOUD", lambda: validate_pair(local, bad))
    bad = copy.deepcopy(local); bad["policy"]["state"] = "STALE"
    expect("POLICY_STALE", lambda: validate_binding(bad))
    bad = copy.deepcopy(local); bad["enrollment"]["state"] = "REVOKED"
    expect("REVOKED_IDENTITY", lambda: validate_binding(bad))
    bad = copy.deepcopy(local); bad["secret_handles"][0]["lease_state"] = "EXPIRED"
    expect("EXPIRED_IDENTITY_LEASE", lambda: validate_binding(bad))
    bad = copy.deepcopy(local); bad["secret_handles"][0]["id"] = "plaintext-secret-value"
    expect("SECRET_VALUE_LEAK", lambda: validate_binding(bad))
    bad = copy.deepcopy(local); bad["capability"]["capabilities"] = ["*"]
    expect("WILDCARD_CAPABILITY", lambda: validate_binding(bad))
    bad = copy.deepcopy(local); bad["transport_auth_state"] = "AUTHENTICATED"; bad["external_states"]["task"] = "PASS"
    expect("TRANSPORT_AUTH_AS_TASK_PASS", lambda: validate_binding(bad))
    bad = copy.deepcopy(local); bad["enrollment"] = {"state": "ENROLLED", "evidence_kind": "PACKAGE_PRESENCE", "evidence_digest": "9" * 64}
    expect("PACKAGE_PRESENCE_AS_ENROLLMENT_PASS", lambda: validate_binding(bad))
    bad = copy.deepcopy(local); bad["capability"]["fallback_capabilities"] = ["admin.execute"]
    expect("PROVIDER_FALLBACK_AUTHORITY_WIDENING", lambda: validate_binding(bad))
    bad = copy.deepcopy(local); bad["workload_subject"]["commit"] = "main"
    expect("MUTABLE_WORKLOAD_SUBJECT", lambda: validate_binding(bad))
    bad_local = copy.deepcopy(local); bad_local["execution_lane"] = "CLOUD"; bad_local["audience"] = EXPECTED_AUDIENCE["CLOUD"]
    expect("LANE_SUBSTITUTION", lambda: validate_pair(bad_local, cloud))
    bad = copy.deepcopy(local); bad["contract_set_digest"] = "0" * 64
    expect("CONTRACT_SET_MISMATCH", lambda: validate_binding(bad))

    print("PASS: provider-neutral Dual-Agent identity/policy/secret-handle contract controls")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    parser.error("only the fixed --selftest contract surface is admitted; live enrollment remains #59 follow-on work")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
