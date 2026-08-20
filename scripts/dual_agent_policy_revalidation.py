#!/usr/bin/env python3
"""Deterministic queued-job policy/revocation revalidation for #82."""
from __future__ import annotations

import argparse
import copy
import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts" / "dual_agent_identity.py"

spec = importlib.util.spec_from_file_location("dual_agent_identity_base", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("identity base unavailable")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


class PolicyRefusal(RuntimeError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise PolicyRefusal(code, detail)


def fixed_packet() -> dict[str, Any]:
    identity = base.fixed_binding("CLOUD")
    identity["enrollment"] = {"state": "ENROLLED", "evidence_kind": "ATTESTATION_RECEIPT", "evidence_digest": "8" * 64}
    identity["secret_handles"][0] = {"id": "secret://runtime/api-handle", "lease_state": "ACTIVE", "expires_at": "2026-08-20T00:00:00Z"}
    identity["credential_presentation"] = {"mode": "MTLS", "state": "ISSUED", "evidence_digest": "9" * 64}
    return {
        "schema": "runtime-env/dual-agent-identity/policy-revalidation/v1",
        "identity_binding": identity,
        "queued_policy": {"digest": identity["policy"]["digest"], "epoch": 1},
        "current_policy": {"digest": identity["policy"]["digest"], "epoch": 1, "decision": "ALLOW"},
        "capability_required": "workload.execute",
        "transport_auth_state": "AUTHENTICATED",
        "cleanup_state": "PASS",
        "external_states": {"task": "NOT_EXERCISED", "provider": "NOT_EXERCISED", "release": "NOT_EXERCISED"},
    }


def revalidate(packet: dict[str, Any]) -> dict[str, Any]:
    if packet.get("schema") != "runtime-env/dual-agent-identity/policy-revalidation/v1":
        refuse("POLICY_PACKET_SCHEMA_MISMATCH")
    identity = packet.get("identity_binding")
    if not isinstance(identity, dict):
        refuse("POLICY_PACKET_SCHEMA_MISMATCH")
    try:
        base.validate_binding(identity)
    except base.IdentityRefusal as exc:
        refuse(exc.code, str(exc))

    queued = packet.get("queued_policy", {})
    current = packet.get("current_policy", {})
    if queued.get("epoch") != current.get("epoch") or queued.get("digest") != current.get("digest"):
        refuse("POLICY_STALE")
    if current.get("decision") != "ALLOW":
        refuse("POLICY_REFUSED")
    required = packet.get("capability_required")
    capabilities = identity.get("capability", {}).get("capabilities", [])
    if not isinstance(required, str) or required not in capabilities or "*" in required:
        refuse("CAPABILITY_REFUSED")
    enrollment_state = identity.get("enrollment", {}).get("state")
    if enrollment_state == "REVOKED":
        refuse("REVOKED_IDENTITY")
    if enrollment_state == "EXPIRED":
        refuse("EXPIRED_IDENTITY_LEASE")
    for handle in identity.get("secret_handles", []):
        if handle.get("lease_state") == "REVOKED":
            refuse("REVOKED_IDENTITY")
        if handle.get("lease_state") == "EXPIRED":
            refuse("EXPIRED_IDENTITY_LEASE")
    if packet.get("cleanup_state") != "PASS":
        refuse("FAILED_CLEANUP")
    external = packet.get("external_states", {})
    if packet.get("transport_auth_state") == "AUTHENTICATED" and external.get("task") == "PASS":
        refuse("TRANSPORT_AUTH_AS_TASK_PASS")
    if any(v != "NOT_EXERCISED" for v in external.values()):
        refuse("POLICY_CHECK_AS_LIVE_PASS")
    return {
        "schema": "runtime-env/dual-agent-identity/policy-revalidation-receipt/v1",
        "admission_state": "ALLOW",
        "policy_epoch": current["epoch"],
        "policy_digest": current["digest"],
        "identity_state": "DETERMINISTIC_BINDING_ONLY",
        "task_state": "NOT_EXERCISED",
        "provider_state": "NOT_EXERCISED",
        "release_state": "NOT_EXERCISED",
        "evidence_ceiling": "DETERMINISTIC_POLICY_REVALIDATION_ONLY",
    }


def expect(code: str, fn: Any) -> None:
    try:
        fn()
    except PolicyRefusal as exc:
        if exc.code != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def selftest() -> int:
    p = fixed_packet()
    r = revalidate(p)
    assert r["admission_state"] == "ALLOW" and r["task_state"] == "NOT_EXERCISED"

    bad = copy.deepcopy(p); bad["current_policy"]["epoch"] = 2
    expect("POLICY_STALE", lambda: revalidate(bad))
    bad = copy.deepcopy(p); bad["current_policy"]["decision"] = "DENY"
    expect("POLICY_REFUSED", lambda: revalidate(bad))
    bad = copy.deepcopy(p); bad["capability_required"] = "admin.execute"
    expect("CAPABILITY_REFUSED", lambda: revalidate(bad))
    bad = copy.deepcopy(p); bad["identity_binding"]["enrollment"]["state"] = "REVOKED"
    expect("REVOKED_IDENTITY", lambda: revalidate(bad))
    bad = copy.deepcopy(p); bad["identity_binding"]["secret_handles"][0]["lease_state"] = "EXPIRED"
    expect("EXPIRED_IDENTITY_LEASE", lambda: revalidate(bad))
    bad = copy.deepcopy(p); bad["external_states"]["task"] = "PASS"
    expect("TRANSPORT_AUTH_AS_TASK_PASS", lambda: revalidate(bad))
    bad = copy.deepcopy(p); bad["cleanup_state"] = "UNKNOWN"
    expect("FAILED_CLEANUP", lambda: revalidate(bad))
    bad = copy.deepcopy(p); bad["external_states"]["provider"] = "PASS"; bad["transport_auth_state"] = "NOT_EXERCISED"
    expect("POLICY_CHECK_AS_LIVE_PASS", lambda: revalidate(bad))

    print("PASS: deterministic queued-job policy/revocation revalidation controls")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    parser.error("only --selftest is admitted; live policy/provider evidence remains external")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
