#!/usr/bin/env python3
"""Deterministic CLOUD workload-identity adapter binding for #81.

No trust domain is created and no credential is issued. This contract keeps
provider presence, attestation, policy, task and release evidence independent.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts" / "dual_agent_identity.py"
H64 = re.compile(r"^[0-9a-f]{64}$")

spec = importlib.util.spec_from_file_location("dual_agent_identity_base", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("identity base unavailable")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


class CloudBindingRefusal(RuntimeError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise CloudBindingRefusal(code, detail)


def fixed_packet() -> dict[str, Any]:
    identity = base.fixed_binding("CLOUD")
    return {
        "schema": "runtime-env/dual-agent-identity/cloud-adapter-binding/v1",
        "identity_binding": identity,
        "adapter": {
            "provider_class": "WORKLOAD_IDENTITY_ADAPTER",
            "provider_ref": "runtime-ref://identity/provider/demo",
            "trust_domain_ref": "runtime-ref://identity/trust-domain/demo",
            "attestation_state": "NOT_EXERCISED",
            "attestation_digest": None,
            "credential_state": "NOT_EXERCISED",
            "credential_evidence_digest": None,
            "credential_lifetime_seconds": 900,
            "provider_health_state": "NOT_EXERCISED",
            "fallback_capabilities": [],
        },
        "external_states": {
            "trust_domain": "NOT_EXERCISED",
            "attestation": "NOT_EXERCISED",
            "credential_issuance": "NOT_EXERCISED",
            "policy": "NOT_EXERCISED",
            "task": "NOT_EXERCISED",
            "release": "NOT_EXERCISED",
        },
    }


def validate(packet: dict[str, Any]) -> None:
    if packet.get("schema") != "runtime-env/dual-agent-identity/cloud-adapter-binding/v1":
        refuse("CLOUD_BINDING_SCHEMA_MISMATCH")
    identity = packet.get("identity_binding")
    if not isinstance(identity, dict):
        refuse("CLOUD_BINDING_SCHEMA_MISMATCH")
    try:
        base.validate_binding(identity)
    except base.IdentityRefusal as exc:
        refuse(exc.code, str(exc))
    if identity.get("execution_lane") != "CLOUD":
        refuse("LOCAL_IDENTITY_REUSED_AS_CLOUD")

    adapter = packet.get("adapter")
    if not isinstance(adapter, dict):
        refuse("CLOUD_BINDING_SCHEMA_MISMATCH")
    for key in ("provider_ref", "trust_domain_ref"):
        value = adapter.get(key)
        if not isinstance(value, str) or not value.startswith("runtime-ref://identity/") or "*" in value:
            refuse("MUTABLE_PROVIDER_OR_TRUST_SUBJECT")
    lifetime = adapter.get("credential_lifetime_seconds")
    if not isinstance(lifetime, int) or lifetime < 60 or lifetime > 3600:
        refuse("UNBOUNDED_CREDENTIAL_LIFETIME")
    if adapter.get("attestation_state") == "ATTESTED":
        if not H64.fullmatch(str(adapter.get("attestation_digest", ""))):
            refuse("PACKAGE_PRESENCE_AS_ENROLLMENT_PASS")
    elif adapter.get("attestation_state") != "NOT_EXERCISED" or adapter.get("attestation_digest") is not None:
        refuse("PACKAGE_PRESENCE_AS_ENROLLMENT_PASS")
    if adapter.get("credential_state") == "ISSUED":
        if not H64.fullmatch(str(adapter.get("credential_evidence_digest", ""))):
            refuse("EXPIRED_OR_UNPROVEN_CREDENTIAL")
    elif adapter.get("credential_state") != "NOT_EXERCISED" or adapter.get("credential_evidence_digest") is not None:
        refuse("EXPIRED_OR_UNPROVEN_CREDENTIAL")
    fallback = adapter.get("fallback_capabilities", [])
    parent_caps = identity.get("capability", {}).get("capabilities", [])
    if any(item not in parent_caps for item in fallback):
        refuse("PROVIDER_FALLBACK_AUTHORITY_WIDENING")
    if adapter.get("provider_health_state") != "NOT_EXERCISED":
        refuse("PROVIDER_HEALTH_AS_PASS")
    external = packet.get("external_states", {})
    if not isinstance(external, dict) or any(v != "NOT_EXERCISED" for v in external.values()):
        refuse("ADAPTER_BINDING_AS_LIVE_PASS")


def receipt(packet: dict[str, Any]) -> dict[str, Any]:
    validate(packet)
    return {
        "schema": "runtime-env/dual-agent-identity/cloud-adapter-receipt/v1",
        "binding_state": "PASS",
        "provider_state": "NOT_EXERCISED",
        "attestation_state": "NOT_EXERCISED",
        "credential_state": "NOT_EXERCISED",
        "policy_state": "NOT_EXERCISED",
        "task_state": "NOT_EXERCISED",
        "evidence_ceiling": "DETERMINISTIC_CLOUD_IDENTITY_ADAPTER_ONLY",
    }


def expect(code: str, fn: Any) -> None:
    try:
        fn()
    except CloudBindingRefusal as exc:
        if exc.code != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def selftest() -> int:
    p = fixed_packet()
    assert receipt(p)["binding_state"] == "PASS"

    bad = copy.deepcopy(p); bad["identity_binding"]["execution_lane"] = "LOCAL"; bad["identity_binding"]["audience"] = "runtime-env/dual-agent/local"
    expect("LOCAL_IDENTITY_REUSED_AS_CLOUD", lambda: validate(bad))
    bad = copy.deepcopy(p); bad["identity_binding"]["audience"] = "runtime-env/dual-agent/local"
    expect("WRONG_AUDIENCE", lambda: validate(bad))
    bad = copy.deepcopy(p); bad["adapter"]["provider_ref"] = "latest"
    expect("MUTABLE_PROVIDER_OR_TRUST_SUBJECT", lambda: validate(bad))
    bad = copy.deepcopy(p); bad["adapter"]["credential_lifetime_seconds"] = 86400
    expect("UNBOUNDED_CREDENTIAL_LIFETIME", lambda: validate(bad))
    bad = copy.deepcopy(p); bad["adapter"]["attestation_state"] = "ATTESTTED"; bad["adapter"]["attestation_digest"] = None
    expect("PACKAGE_PRESENCE_AS_ENROLLMENT_PASS", lambda: validate(bad))
    bad = copy.deepcopy(p); bad["adapter"]["credential_state"] = "ISSUED"; bad["adapter"]["credential_evidence_digest"] = None
    expect("EXPIRED_OR_UNPROVEN_CREDENTIAL", lambda: validate(bad))
    bad = copy.deepcopy(p); bad["adapter"]["fallback_capabilities"] = ["admin.execute"]
    expect("PROVIDER_FALLBACK_AUTHORITY_WIDENING", lambda: validate(bad))
    bad = copy.deepcopy(p); bad["adapter"]["provider_health_state"] = "PASS"
    expect("PROVIDER_HEALTH_AS_PASS", lambda: validate(bad))
    bad = copy.deepcopy(p); bad["external_states"]["task"] = "PASS"
    expect("ADAPTER_BINDING_AS_LIVE_PASS", lambda: validate(bad))

    print("PASS: deterministic CLOUD workload-identity adapter controls")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    parser.error("only --selftest is admitted; live enrollment remains external")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
