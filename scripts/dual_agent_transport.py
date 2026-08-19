#!/usr/bin/env python3
"""Deterministic, provider-neutral Dual-Agent transport core for issue #70.

This module owns only local durable transport mechanics. It does not connect to
NATS, execute a workflow, perform an external effect, or promote task/user/release
state.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SET_PATH = ROOT / "contracts" / "dual-agent" / "contract-set-manifest.json"
EXPECTED_CONTRACT_SET_DIGEST = "e6671977dbf0a378474f924a142a82843bc0e3429f4546ffb0145af73f7827fe"
STORE_SCHEMA_VERSION = 1

NON_TRANSPORT_LANES = (
    "workflow_state",
    "task_state",
    "effect_state",
    "artifact_state",
    "user_outcome_state",
    "release_state",
)

TRANSITIONS = {
    "OUTBOX_COMMITTED": {"DELIVERY_PENDING", "DISCONNECTED"},
    "DELIVERY_PENDING": {"CONNECTED", "DISCONNECTED"},
    "DISCONNECTED": {"CONNECTED"},
    "CONNECTED": {"PUBLISHED"},
    "PUBLISHED": {"CONSUMER_ACKED"},
    "CONSUMER_ACKED": {"RESULT_PENDING"},
    "RESULT_PENDING": set(),
}

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS metadata (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS packets (
  packet_id TEXT PRIMARY KEY,
  tenant_scope TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  packet_digest TEXT NOT NULL,
  job_json TEXT NOT NULL,
  state TEXT NOT NULL,
  policy_digest TEXT NOT NULL,
  runtime_digest TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transport_events (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  packet_id TEXT NOT NULL REFERENCES packets(packet_id),
  kind TEXT NOT NULL,
  event_digest TEXT NOT NULL,
  UNIQUE(packet_id, kind, event_digest)
);
"""


class TransportRefusal(RuntimeError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise TransportRefusal(code, detail)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require_job(job: dict[str, Any]) -> None:
    if job.get("schema") != "runtime-env/dual-agent/offload-job/v1":
        refuse("PACKET_SCHEMA_MISMATCH")
    for key in ("job_id", "idempotency_key", "tenant_scope", "execution_lane", "data_classification"):
        if not isinstance(job.get(key), str) or not job[key]:
            refuse("PACKET_SCHEMA_MISMATCH", key)
    ref = job.get("contract_set_ref")
    if not isinstance(ref, dict) or ref.get("manifest_digest") != EXPECTED_CONTRACT_SET_DIGEST:
        refuse("CONTRACT_SET_MISMATCH")

    allowlists = job.get("allowlists")
    if not isinstance(allowlists, dict):
        refuse("PACKET_SCHEMA_MISMATCH", "allowlists")
    network = allowlists.get("network_origins", [])
    filesystem = allowlists.get("filesystem_paths", [])
    if job["data_classification"] == "LOCAL_ONLY" and (
        job["execution_lane"] != "LOCAL" or network
    ):
        refuse("LOCAL_ONLY_REMOTE_EGRESS")

    for path in filesystem:
        if not isinstance(path, str) or Path(path).is_absolute() or ".." in Path(path).parts:
            refuse("SECRET_OR_HOST_PATH")
    for handle in job.get("secret_handles", []):
        if not isinstance(handle, str) or not handle.startswith("secret://"):
            refuse("SECRET_OR_HOST_PATH")

    bindings = job.get("bindings")
    if not isinstance(bindings, dict):
        refuse("PACKET_SCHEMA_MISMATCH", "bindings")
    for key in ("policy_digest", "runtime_digest"):
        value = bindings.get(key)
        if not isinstance(value, str) or len(value) != 64:
            refuse("PACKET_SCHEMA_MISMATCH", key)


def _event_digest(packet_id: str, kind: str, payload: Any) -> str:
    return digest_json({"packet_id": packet_id, "kind": kind, "payload": payload})


class SQLiteTransportStore:
    """One local durable transport authority backed by SQLite."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=FULL")
        self.conn.executescript(SCHEMA_SQL)
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO metadata(key,value) VALUES('schema_version',?)",
                (str(STORE_SCHEMA_VERSION),),
            )

    def _packet(self, packet_id: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM packets WHERE packet_id=?", (packet_id,)
        ).fetchone()

    def _packet_by_idempotency(self, idempotency_key: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM packets WHERE idempotency_key=?", (idempotency_key,)
        ).fetchone()

    def _append_event(self, packet_id: str, kind: str, payload: Any) -> None:
        event_digest = _event_digest(packet_id, kind, payload)
        self.conn.execute(
            "INSERT OR IGNORE INTO transport_events(packet_id,kind,event_digest) VALUES(?,?,?)",
            (packet_id, kind, event_digest),
        )

    def enqueue(self, job: dict[str, Any]) -> dict[str, str]:
        _require_job(job)
        packet_id = job["job_id"]
        packet_digest = digest_json(job)
        existing = self._packet(packet_id) or self._packet_by_idempotency(job["idempotency_key"])
        if existing is not None:
            if (
                existing["packet_id"] == packet_id
                and existing["tenant_scope"] == job["tenant_scope"]
                and existing["packet_digest"] == packet_digest
                and existing["idempotency_key"] == job["idempotency_key"]
            ):
                return {
                    "packet_id": packet_id,
                    "packet_digest": packet_digest,
                    "state": "DUPLICATE_DELIVERY",
                }
            refuse("PACKET_DIGEST_COLLISION")

        with self.conn:
            self.conn.execute(
                """INSERT INTO packets(
                     packet_id,tenant_scope,idempotency_key,packet_digest,job_json,
                     state,policy_digest,runtime_digest
                   ) VALUES(?,?,?,?,?,?,?,?)""",
                (
                    packet_id,
                    job["tenant_scope"],
                    job["idempotency_key"],
                    packet_digest,
                    canonical_json(job),
                    "OUTBOX_COMMITTED",
                    job["bindings"]["policy_digest"],
                    job["bindings"]["runtime_digest"],
                ),
            )
            self._append_event(packet_id, "OUTBOX_COMMITTED", {"packet_digest": packet_digest})
        return {
            "packet_id": packet_id,
            "packet_digest": packet_digest,
            "state": "OUTBOX_COMMITTED",
        }

    def advance(self, packet_id: str, next_state: str, tenant_scope: str) -> str:
        row = self._packet(packet_id)
        if row is None:
            refuse("ACK_BEFORE_DURABLE_COMMIT")
        if row["tenant_scope"] != tenant_scope:
            refuse("CROSS_TENANT_DELIVERY")
        allowed = TRANSITIONS.get(row["state"], set())
        if next_state not in allowed:
            refuse("ILLEGAL_TRANSPORT_TRANSITION", f"{row['state']}->{next_state}")
        with self.conn:
            self.conn.execute(
                "UPDATE packets SET state=? WHERE packet_id=?", (next_state, packet_id)
            )
            self._append_event(packet_id, next_state, {"tenant_scope": tenant_scope})
        return next_state

    def receipt(self, packet_id: str) -> dict[str, Any]:
        row = self._packet(packet_id)
        if row is None:
            refuse("ACK_BEFORE_DURABLE_COMMIT")
        receipt = {
            "schema": "runtime-env/dual-agent/transport-receipt/v1",
            "packet_id": row["packet_id"],
            "tenant_scope": row["tenant_scope"],
            "packet_digest": row["packet_digest"],
            "transport_state": row["state"],
            "contract_set_digest": EXPECTED_CONTRACT_SET_DIGEST,
            "workflow_state": "NOT_EXERCISED",
            "task_state": "NOT_EXERCISED",
            "effect_state": "NOT_EXERCISED",
            "artifact_state": "NOT_EXERCISED",
            "user_outcome_state": "NOT_EXERCISED",
            "release_state": "NOT_EXERCISED",
            "evidence_ceiling": "LOCAL_DETERMINISTIC_TRANSPORT_ONLY",
            "claims_not_proven": [
                "NATS_CONNECTIVITY",
                "CROSS_HOST_DELIVERY",
                "WORKFLOW_EXECUTION",
                "EXTERNAL_EFFECT",
                "USER_OUTCOME",
                "RELEASE",
            ],
        }
        validate_transport_receipt(receipt)
        return receipt

    def counts(self) -> dict[str, int]:
        return {
            "packets": int(self.conn.execute("SELECT COUNT(*) FROM packets").fetchone()[0]),
            "events": int(self.conn.execute("SELECT COUNT(*) FROM transport_events").fetchone()[0]),
        }

    def close(self) -> None:
        try:
            self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            self.conn.close()


def validate_transport_receipt(receipt: dict[str, Any]) -> None:
    for lane in NON_TRANSPORT_LANES:
        if receipt.get(lane) != "NOT_EXERCISED":
            refuse("TRANSPORT_ACK_AS_TASK_PASS", lane)


def assert_cleanup(path: Path) -> None:
    residue = [Path(str(path) + suffix) for suffix in ("-wal", "-shm")]
    present = [str(item.name) for item in residue if item.exists()]
    if present:
        refuse("CLEANUP_WITH_RESIDUE", ",".join(present))


def _fixture_job() -> dict[str, Any]:
    return {
        "schema": "runtime-env/dual-agent/offload-job/v1",
        "job_id": "transport-job-1",
        "idempotency_key": "transport-idem-1",
        "tenant_scope": "tenant-demo",
        "requester_identity_ref": "identity://fixture/requester",
        "source_subject": {
            "repository": "example/workload",
            "commit": "a" * 40,
            "tree": "b" * 40,
        },
        "goal": "Exercise deterministic transport mechanics only.",
        "non_goals": ["No provider execution"],
        "deadline": "2026-08-20T00:00:00Z",
        "budget": {
            "max_cpu_seconds": 10,
            "max_output_bytes": 4096,
            "max_attempts": 1,
            "max_cost_microunits": 0,
        },
        "retry_policy": {"max_attempts": 1, "backoff_class": "NONE"},
        "data_classification": "PUBLIC",
        "side_effect_class": "READ_ONLY",
        "execution_lane": "CLOUD",
        "capability_grant_ref": "grant-transport-1",
        "bindings": {
            "runtime_digest": "1" * 64,
            "profile_digest": "2" * 64,
            "policy_digest": "3" * 64,
            "skill_digest": "4" * 64,
            "tool_digests": ["5" * 64],
            "image_digest": "6" * 64,
        },
        "allowlists": {
            "filesystem_paths": ["workspace/input.json", "workspace/output.json"],
            "network_origins": ["https://api.example.test"],
            "environment_names": ["LANG", "TZ"],
        },
        "secret_handles": [],
        "approval_requirement": "NONE",
        "artifact_requirements": [
            {
                "logical_name": "result",
                "media_type": "application/json",
                "required": True,
                "max_bytes": 4096,
            }
        ],
        "trace_id": "1" * 32,
        "method_contract": {"id": "fixture-method", "sha256": "7" * 64},
        "contract_set_ref": {
            "schema": "runtime-env/dual-agent/contract-set-manifest/v1",
            "manifest_digest": EXPECTED_CONTRACT_SET_DIGEST,
        },
    }


def _expect(code: str, fn: Any) -> None:
    try:
        fn()
    except TransportRefusal as exc:
        if exc.code != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def selftest() -> int:
    manifest = json.loads(CONTRACT_SET_PATH.read_text(encoding="utf-8"))
    assert manifest["contract_set_digest"] == EXPECTED_CONTRACT_SET_DIGEST, manifest

    with tempfile.TemporaryDirectory(prefix="dual-agent-transport-") as td:
        db = Path(td) / "transport.sqlite3"
        store = SQLiteTransportStore(db)
        job = _fixture_job()

        first = store.enqueue(job)
        assert first["state"] == "OUTBOX_COMMITTED", first
        duplicate = store.enqueue(copy.deepcopy(job))
        assert duplicate["state"] == "DUPLICATE_DELIVERY", duplicate
        assert store.counts()["packets"] == 1

        _expect(
            "ACK_BEFORE_DURABLE_COMMIT",
            lambda: store.advance("missing-packet", "CONSUMER_ACKED", "tenant-demo"),
        )

        collision = copy.deepcopy(job)
        collision["goal"] = "Different bytes under the same idempotency identity."
        _expect("PACKET_DIGEST_COLLISION", lambda: store.enqueue(collision))

        _expect(
            "CROSS_TENANT_DELIVERY",
            lambda: store.advance(job["job_id"], "DELIVERY_PENDING", "tenant-other"),
        )

        local_only = copy.deepcopy(job)
        local_only["job_id"] = "transport-job-local-only"
        local_only["idempotency_key"] = "transport-idem-local-only"
        local_only["data_classification"] = "LOCAL_ONLY"
        _expect("LOCAL_ONLY_REMOTE_EGRESS", lambda: store.enqueue(local_only))

        bad_path = copy.deepcopy(job)
        bad_path["job_id"] = "transport-job-bad-path"
        bad_path["idempotency_key"] = "transport-idem-bad-path"
        bad_path["allowlists"]["filesystem_paths"].append("/var/runtime/forbidden-key")
        _expect("SECRET_OR_HOST_PATH", lambda: store.enqueue(bad_path))

        store.advance(job["job_id"], "DELIVERY_PENDING", "tenant-demo")
        store.advance(job["job_id"], "CONNECTED", "tenant-demo")
        store.advance(job["job_id"], "PUBLISHED", "tenant-demo")
        store.advance(job["job_id"], "CONSUMER_ACKED", "tenant-demo")
        receipt = store.receipt(job["job_id"])
        assert receipt["transport_state"] == "CONSUMER_ACKED"
        assert all(receipt[lane] == "NOT_EXERCISED" for lane in NON_TRANSPORT_LANES)

        promoted = copy.deepcopy(receipt)
        promoted["task_state"] = "PASS"
        _expect("TRANSPORT_ACK_AS_TASK_PASS", lambda: validate_transport_receipt(promoted))

        store.close()
        assert_cleanup(db)

        planted = Path(str(db) + "-wal")
        planted.write_text("planted-residue", encoding="utf-8")
        _expect("CLEANUP_WITH_RESIDUE", lambda: assert_cleanup(db))
        planted.unlink()
        assert_cleanup(db)

    print("PASS: Dual-Agent deterministic SQLite transport core controls")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    parser.error("only the fixed --selftest surface is admitted in DA-TR-C")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
