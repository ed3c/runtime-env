#!/usr/bin/env python3
"""Bounded, hermetic NATS/JetStream adapter contract for Dual-Agent transport.

This module proves adapter semantics only. It opens no socket, imports no NATS
client, enrolls no TLS identity, and cannot promote transport evidence to
workflow/task/effect/user/release success.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "contracts" / "dual-agent-transport" / "nats-jetstream-adapter.v1.schema.json"
EXPECTED_CONTRACT_SET_DIGEST = "e6671977dbf0a378474f924a142a82843bc0e3429f4546ffb0145af73f7827fe"
NON_TRANSPORT_LANES = ("workflow_state", "task_state", "effect_state", "user_outcome_state", "release_state")


class AdapterRefusal(RuntimeError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise AdapterRefusal(code, detail)


def fixed_config() -> dict[str, Any]:
    return {
        "schema": "runtime-env/dual-agent-transport/nats-jetstream-adapter/v1",
        "adapter_id": "dual-agent-edge-hub",
        "provider_class": "NATS_JETSTREAM_ADAPTER",
        "server_ref": "runtime-ref://nats/edge-hub-demo",
        "tenant_subjects": [
            {"tenant_scope": "tenant-demo", "subject": "dual-agent.tenant-demo.jobs"},
            {"tenant_scope": "tenant-other", "subject": "dual-agent.tenant-other.jobs"},
        ],
        "stream": {
            "name": "DUAL_AGENT_JOBS",
            "subjects": ["dual-agent.tenant-demo.jobs", "dual-agent.tenant-other.jobs"],
            "max_age_seconds": 3600,
            "max_bytes": 1048576,
        },
        "consumer": {
            "durable_name": "dual-agent-edge-demo",
            "ack_wait_ms": 1000,
            "max_deliver": 3,
        },
        "tls": {
            "mode": "REQUIRED",
            "credential_handles": ["secret://nats/client-cert", "secret://nats/client-key"],
        },
        "contract_set_digest": EXPECTED_CONTRACT_SET_DIGEST,
        "evidence_state": "NOT_EXERCISED",
        "claims_not_proven": [
            "LIVE_NATS_CONNECTIVITY",
            "TLS_ENROLLMENT",
            "CROSS_HOST_DELIVERY",
            "WORKFLOW_EXECUTION",
            "EXTERNAL_EFFECT",
            "USER_OUTCOME",
            "RELEASE",
        ],
    }


def validate_config(config: dict[str, Any]) -> dict[str, str]:
    if config.get("schema") != "runtime-env/dual-agent-transport/nats-jetstream-adapter/v1":
        refuse("ADAPTER_SCHEMA_MISMATCH")
    if config.get("provider_class") != "NATS_JETSTREAM_ADAPTER":
        refuse("ADAPTER_SCHEMA_MISMATCH", "provider_class")
    server_ref = config.get("server_ref")
    if not isinstance(server_ref, str) or not server_ref.startswith("runtime-ref://nats/"):
        refuse("MUTABLE_SERVER_ID")
    if config.get("contract_set_digest") != EXPECTED_CONTRACT_SET_DIGEST:
        refuse("CONTRACT_SET_MISMATCH")
    if config.get("evidence_state") != "NOT_EXERCISED":
        refuse("PROVIDER_ABSENCE_AS_PASS")

    consumer = config.get("consumer")
    if not isinstance(consumer, dict):
        refuse("ADAPTER_SCHEMA_MISMATCH", "consumer")
    max_deliver = consumer.get("max_deliver")
    ack_wait_ms = consumer.get("ack_wait_ms")
    if not isinstance(max_deliver, int) or not 1 <= max_deliver <= 100:
        refuse("UNBOUNDED_REDELIVERY")
    if not isinstance(ack_wait_ms, int) or not 100 <= ack_wait_ms <= 600000:
        refuse("UNBOUNDED_REDELIVERY", "ack_wait_ms")

    tenant_subjects = config.get("tenant_subjects")
    if not isinstance(tenant_subjects, list) or not tenant_subjects:
        refuse("ADAPTER_SCHEMA_MISMATCH", "tenant_subjects")
    mapping: dict[str, str] = {}
    seen_subjects: set[str] = set()
    for item in tenant_subjects:
        if not isinstance(item, dict):
            refuse("ADAPTER_SCHEMA_MISMATCH", "tenant subject")
        tenant = item.get("tenant_scope")
        subject = item.get("subject")
        if not isinstance(tenant, str) or not tenant or not isinstance(subject, str) or not subject:
            refuse("ADAPTER_SCHEMA_MISMATCH", "tenant subject")
        if any(token in subject for token in ("*", ">")):
            refuse("WILDCARD_SUBJECT")
        if tenant in mapping or subject in seen_subjects:
            refuse("CROSS_TENANT_SUBJECT", "duplicate mapping")
        mapping[tenant] = subject
        seen_subjects.add(subject)

    stream = config.get("stream")
    if not isinstance(stream, dict) or set(stream.get("subjects", [])) != seen_subjects:
        refuse("SUBJECT_INJECTION", "stream subject set")
    if not isinstance(stream.get("max_age_seconds"), int) or stream["max_age_seconds"] <= 0:
        refuse("UNBOUNDED_REDELIVERY", "retention")
    if not isinstance(stream.get("max_bytes"), int) or not 1024 <= stream["max_bytes"] <= 1073741824:
        refuse("UNBOUNDED_REDELIVERY", "max_bytes")

    tls = config.get("tls")
    if not isinstance(tls, dict) or tls.get("mode") != "REQUIRED":
        refuse("RAW_CREDENTIAL", "TLS must be required")
    handles = tls.get("credential_handles")
    if not isinstance(handles, list) or not handles or any(not isinstance(h, str) or not h.startswith("secret://") for h in handles):
        refuse("RAW_CREDENTIAL")
    return mapping


class HermeticJetStream:
    """In-memory redelivery model. It is deliberately not a NATS client."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = copy.deepcopy(config)
        self.subjects = validate_config(self.config)
        self.max_deliver = int(self.config["consumer"]["max_deliver"])
        self.messages: dict[int, dict[str, Any]] = {}
        self.message_ids: dict[str, int] = {}
        self.next_sequence = 1

    def publish(self, tenant_scope: str, subject: str, packet_id: str, packet_digest: str) -> dict[str, Any]:
        expected = self.subjects.get(tenant_scope)
        if expected is None:
            refuse("CROSS_TENANT_SUBJECT", tenant_scope)
        if subject != expected:
            if subject in set(self.subjects.values()):
                refuse("CROSS_TENANT_SUBJECT")
            refuse("SUBJECT_INJECTION")
        if not isinstance(packet_digest, str) or len(packet_digest) != 64 or any(ch not in "0123456789abcdef" for ch in packet_digest):
            refuse("PACKET_DIGEST_MISMATCH")
        message_id = f"{packet_id}:{packet_digest}"
        existing = self.message_ids.get(message_id)
        if existing is not None:
            return {"sequence": existing, "state": "DUPLICATE_SUPPRESSED"}
        for message in self.messages.values():
            if message["packet_id"] == packet_id and message["packet_digest"] != packet_digest:
                refuse("MESSAGE_ID_COLLISION")
        sequence = self.next_sequence
        self.next_sequence += 1
        self.messages[sequence] = {
            "tenant_scope": tenant_scope,
            "subject": subject,
            "packet_id": packet_id,
            "packet_digest": packet_digest,
            "delivery_attempts": 0,
            "acked": False,
        }
        self.message_ids[message_id] = sequence
        return {"sequence": sequence, "state": "PUBLISHED_HERMETIC"}

    def deliver(self, sequence: int, tenant_scope: str) -> dict[str, Any]:
        message = self.messages.get(sequence)
        if message is None:
            refuse("SUBJECT_INJECTION", "unknown sequence")
        if message["tenant_scope"] != tenant_scope:
            refuse("CROSS_TENANT_SUBJECT")
        if message["acked"]:
            return {"sequence": sequence, "state": "ALREADY_ACKED", "attempt": message["delivery_attempts"]}
        if message["delivery_attempts"] >= self.max_deliver:
            refuse("REDELIVERY_BUDGET_EXCEEDED")
        message["delivery_attempts"] += 1
        return {"sequence": sequence, "state": "DELIVERED_HERMETIC", "attempt": message["delivery_attempts"]}

    def ack(self, sequence: int) -> str:
        message = self.messages.get(sequence)
        if message is None or message["delivery_attempts"] == 0:
            refuse("ACK_WITHOUT_DELIVERY")
        message["acked"] = True
        return "ACKED_HERMETIC"

    def receipt(self, sequence: int) -> dict[str, Any]:
        message = self.messages.get(sequence)
        if message is None:
            refuse("SUBJECT_INJECTION", "unknown sequence")
        receipt = {
            "schema": "runtime-env/dual-agent-transport/nats-adapter-receipt/v1",
            "adapter_id": self.config["adapter_id"],
            "server_ref": self.config["server_ref"],
            "sequence": sequence,
            "packet_id": message["packet_id"],
            "packet_digest": message["packet_digest"],
            "tenant_scope": message["tenant_scope"],
            "subject": message["subject"],
            "delivery_attempts": message["delivery_attempts"],
            "ack_state": "ACKED_HERMETIC" if message["acked"] else "UNACKED_HERMETIC",
            "adapter_contract_state": "PASS",
            "provider_state": "NOT_EXERCISED",
            "network_state": "NOT_EXERCISED",
            "workflow_state": "NOT_EXERCISED",
            "task_state": "NOT_EXERCISED",
            "effect_state": "NOT_EXERCISED",
            "user_outcome_state": "NOT_EXERCISED",
            "release_state": "NOT_EXERCISED",
            "evidence_ceiling": "HERMETIC_NATS_ADAPTER_CONTRACT_ONLY",
            "claims_not_proven": list(self.config["claims_not_proven"]),
        }
        validate_receipt(receipt)
        return receipt


def validate_receipt(receipt: dict[str, Any]) -> None:
    if receipt.get("provider_state") != "NOT_EXERCISED" or receipt.get("network_state") != "NOT_EXERCISED":
        refuse("PROVIDER_ABSENCE_AS_PASS")
    for lane in NON_TRANSPORT_LANES:
        if receipt.get(lane) != "NOT_EXERCISED":
            refuse("ACK_AS_TASK_PASS", lane)


def expect(code: str, fn: Any) -> None:
    try:
        fn()
    except AdapterRefusal as exc:
        if exc.code != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def selftest() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False

    config = fixed_config()
    validate_config(config)
    bus = HermeticJetStream(config)
    packet_digest = "a" * 64
    published = bus.publish("tenant-demo", "dual-agent.tenant-demo.jobs", "packet-1", packet_digest)
    sequence = int(published["sequence"])
    duplicate = bus.publish("tenant-demo", "dual-agent.tenant-demo.jobs", "packet-1", packet_digest)
    assert duplicate == {"sequence": sequence, "state": "DUPLICATE_SUPPRESSED"}
    assert bus.deliver(sequence, "tenant-demo")["attempt"] == 1
    assert bus.deliver(sequence, "tenant-demo")["attempt"] == 2
    assert bus.ack(sequence) == "ACKED_HERMETIC"
    receipt = bus.receipt(sequence)
    assert receipt["delivery_attempts"] == 2
    assert receipt["provider_state"] == "NOT_EXERCISED"
    assert all(receipt[lane] == "NOT_EXERCISED" for lane in NON_TRANSPORT_LANES)

    bad = fixed_config(); bad["tenant_subjects"][0]["subject"] = "dual-agent.>"
    expect("WILDCARD_SUBJECT", lambda: validate_config(bad))
    bad = fixed_config(); bad["consumer"]["max_deliver"] = 1000
    expect("UNBOUNDED_REDELIVERY", lambda: validate_config(bad))
    bad = fixed_config(); bad["tls"]["credential_handles"] = ["plaintext-nats-token"]
    expect("RAW_CREDENTIAL", lambda: validate_config(bad))
    expect("SUBJECT_INJECTION", lambda: bus.publish("tenant-demo", "dual-agent.tenant-demo.other", "packet-2", "b" * 64))
    pending = bus.publish("tenant-demo", "dual-agent.tenant-demo.jobs", "packet-3", "c" * 64)
    expect("ACK_WITHOUT_DELIVERY", lambda: bus.ack(int(pending["sequence"])))
    promoted = copy.deepcopy(receipt); promoted["task_state"] = "PASS"
    expect("ACK_AS_TASK_PASS", lambda: validate_receipt(promoted))
    promoted = copy.deepcopy(receipt); promoted["provider_state"] = "PASS"
    expect("PROVIDER_ABSENCE_AS_PASS", lambda: validate_receipt(promoted))
    expect("CROSS_TENANT_SUBJECT", lambda: bus.publish("tenant-demo", "dual-agent.tenant-other.jobs", "packet-4", "d" * 64))
    bad = fixed_config(); bad["server_ref"] = "nats://edge.example.invalid:4222"
    expect("MUTABLE_SERVER_ID", lambda: validate_config(bad))

    limited = fixed_config(); limited["consumer"]["max_deliver"] = 2
    limited_bus = HermeticJetStream(limited)
    seq = int(limited_bus.publish("tenant-demo", "dual-agent.tenant-demo.jobs", "packet-limit", "e" * 64)["sequence"])
    limited_bus.deliver(seq, "tenant-demo")
    limited_bus.deliver(seq, "tenant-demo")
    expect("REDELIVERY_BUDGET_EXCEEDED", lambda: limited_bus.deliver(seq, "tenant-demo"))

    print("PASS: bounded hermetic NATS/JetStream adapter contract and redelivery controls")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    parser.error("only the fixed --selftest surface is admitted; live NATS belongs to #73")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
