#!/usr/bin/env python3
"""Deterministic LOCAL identity-to-broker binding for #80.

This module validates only metadata and the existing public broker contract. It
never opens Keychain, resolves a secret value, or promotes broker presence to
identity/task success.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts" / "dual_agent_identity.py"
BROKER_DOC = ROOT / "docs" / "local-credential-broker.md"
H64 = re.compile(r"^[0-9a-f]{64}$")
ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")

spec = importlib.util.spec_from_file_location("dual_agent_identity_base", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("identity base unavailable")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


class LocalBindingRefusal(RuntimeError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise LocalBindingRefusal(code, detail)


def fixed_packet() -> dict[str, Any]:
    identity = base.fixed_binding("LOCAL")
    return {
        "schema": "runtime-env/dual-agent-identity/local-broker-binding/v1",
        "identity_binding": identity,
        "broker": {
            "contract_path": "docs/local-credential-broker.md",
            "delivery_class": "broker-only",
            "secret_handle_ids": [item["id"] for item in identity["secret_handles"]],
            "admitted_tree_digest": "8" * 64,
            "environment_names": ["LANG", "TZ"],
            "operator_environment_inherited": False,
            "generic_shell_surface": False,
            "provider_presence_state": "NOT_EXERCISED",
        },
        "external_states": {
            "secret_resolution": "NOT_EXERCISED",
            "credential_access": "NOT_EXERCISED",
            "task": "NOT_EXERCISED",
            "user_outcome": "NOT_EXERCISED",
            "release": "NOT_EXERCISED",
        },
    }


def validate(packet: dict[str, Any]) -> None:
    if packet.get("schema") != "runtime-env/dual-agent-identity/local-broker-binding/v1":
        refuse("LOCAL_BINDING_SCHEMA_MISMATCH")
    identity = packet.get("identity_binding")
    if not isinstance(identity, dict):
        refuse("LOCAL_BINDING_SCHEMA_MISMATCH")
    try:
        base.validate_binding(identity)
    except base.IdentityRefusal as exc:
        refuse(exc.code, str(exc))
    if identity.get("execution_lane") != "LOCAL":
        refuse("LOCAL_LANE_REQUIRED")

    broker = packet.get("broker")
    if not isinstance(broker, dict):
        refuse("BROKER_CONTRACT_MISMATCH")
    if broker.get("contract_path") != "docs/local-credential-broker.md" or not BROKER_DOC.is_file():
        refuse("BROKER_CONTRACT_MISMATCH")
    doc = BROKER_DOC.read_text(encoding="utf-8")
    for required in ("`broker-only`", "Never add a generic `run -- <arbitrary command>`"):
        if required not in doc:
            refuse("BROKER_CONTRACT_MISMATCH")
    if broker.get("delivery_class") != "broker-only":
        refuse("BROKER_DELIVERY_WIDENING")
    expected_handles = [item["id"] for item in identity.get("secret_handles", [])]
    if broker.get("secret_handle_ids") != expected_handles or any(not x.startswith("secret://") for x in expected_handles):
        refuse("RAW_SECRET_VALUE")
    if not H64.fullmatch(str(broker.get("admitted_tree_digest", ""))):
        refuse("MUTABLE_ADMISSION_SUBJECT")
    if broker.get("operator_environment_inherited") is not False:
        refuse("OPERATOR_ENVIRONMENT_INHERITANCE")
    if broker.get("generic_shell_surface") is not False:
        refuse("GENERIC_SHELL_CREDENTIAL_READ")
    names = broker.get("environment_names", [])
    if not isinstance(names, list) or any(not ENV_NAME.fullmatch(str(x)) for x in names):
        refuse("OPERATOR_ENVIRONMENT_INHERITANCE")
    if broker.get("provider_presence_state") != "NOT_EXERCISED":
        refuse("PROVIDER_PRESENCE_AS_PASS")
    external = packet.get("external_states", {})
    if not isinstance(external, dict) or any(v != "NOT_EXERCISED" for v in external.values()):
        refuse("BROKER_BINDING_AS_LIVE_PASS")


def receipt(packet: dict[str, Any]) -> dict[str, Any]:
    validate(packet)
    return {
        "schema": "runtime-env/dual-agent-identity/local-broker-receipt/v1",
        "binding_state": "PASS",
        "identity_state": "NOT_EXERCISED",
        "secret_resolution_state": "NOT_EXERCISED",
        "credential_access_state": "NOT_EXERCISED",
        "task_state": "NOT_EXERCISED",
        "evidence_ceiling": "DETERMINISTIC_LOCAL_BROKER_BINDING_ONLY",
    }


def expect(code: str, fn: Any) -> None:
    try:
        fn()
    except LocalBindingRefusal as exc:
        if exc.code != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def selftest() -> int:
    import copy
    p = fixed_packet()
    r = receipt(p)
    assert r["binding_state"] == "PASS"
    assert r["secret_resolution_state"] == "NOT_EXERCISED"

    bad = copy.deepcopy(p); bad["identity_binding"]["audience"] = "runtime-env/dual-agent/cloud"
    expect("WRONG_AUDIENCE", lambda: validate(bad))
    bad = copy.deepcopy(p); bad["broker"]["secret_handle_ids"] = ["plaintext-value"]
    expect("RAW_SECRET_VALUE", lambda: validate(bad))
    bad = copy.deepcopy(p); bad["broker"]["admitted_tree_digest"] = "main"
    expect("MUTABLE_ADMISSION_SUBJECT", lambda: validate(bad))
    bad = copy.deepcopy(p); bad["broker"]["operator_environment_inherited"] = True
    expect("OPERATOR_ENVIRONMENT_INHERITANCE", lambda: validate(bad))
    bad = copy.deepcopy(p); bad["broker"]["generic_shell_surface"] = True
    expect("GENERIC_SHELL_CREDENTIAL_READ", lambda: validate(bad))
    bad = copy.deepcopy(p); bad["broker"]["provider_presence_state"] = "PASS"
    expect("PROVIDER_PRESENCE_AS_PASS", lambda: validate(bad))
    bad = copy.deepcopy(p); bad["external_states"]["secret_resolution"] = "PASS"
    expect("BROKER_BINDING_AS_LIVE_PASS", lambda: validate(bad))
    bad = copy.deepcopy(p); bad["broker"]["delivery_class"] = "environment"
    expect("BROKER_DELIVERY_WIDENING", lambda: validate(bad))

    print("PASS: deterministic LOCAL identity-to-broker binding controls")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    parser.error("only --selftest is admitted; live secret resolution remains external")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
