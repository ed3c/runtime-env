from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture" / "dual-agent-runtime"
EXPECTED_ATOMS = {
    "DA-RC-C": (61, 69),
    "DA-TR-C": (70, 76),
    "DA-TR-L": (71, 77),
    "DA-TR-N": (72, 78),
    "DA-ID-C": (75, 79),
    "DA-ID-L": (80, 85),
    "DA-ID-CLOUD": (81, 86),
    "DA-ID-P": (82, 87),
}


class RuntimeDocsError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


def refuse(code: str, detail: str = "") -> None:
    raise RuntimeDocsError(code, detail)


def verify(index: dict, readme: str, agents: str) -> None:
    if index.get("schema") != "runtime-env.dual-agent-runtime-stack-index.v1":
        refuse("STACK_SCHEMA_DRIFT")
    if index.get("docs_issue") != 88 or index.get("live_handoff_issue") != 89:
        refuse("ISSUE_ROUTE_DRIFT")
    if index.get("docs_subject_state") != "CANDIDATE_SUBJECT_PENDING":
        refuse("DOCS_SELF_PROMOTION")

    nodes = index.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != len(EXPECTED_ATOMS):
        refuse("NODE_SET_DRIFT")
    by_atom = {item.get("atom"): item for item in nodes if isinstance(item, dict)}
    if set(by_atom) != set(EXPECTED_ATOMS):
        refuse("NODE_SET_DRIFT")
    for atom, (issue, pr) in EXPECTED_ATOMS.items():
        item = by_atom[atom]
        if item.get("issue") != issue or item.get("pr") != pr:
            refuse("NODE_ROUTE_DRIFT", atom)
        if item.get("state") != "MERGED_DETERMINISTIC":
            refuse("NODE_STATE_DRIFT", atom)
        for field, length in (("source_head", 40), ("source_tree", 40)):
            value = item.get(field)
            if not isinstance(value, str) or len(value) != length:
                refuse("EXACT_SUBJECT_MISSING", f"{atom}.{field}")
        if not isinstance(item.get("targeted_run"), int):
            refuse("RUN_RECEIPT_MISSING", atom)

    authority = index.get("authority", {})
    if authority.get("wire_contract_owner") != "ed3c/runtime-env:contracts/dual-agent":
        refuse("CONTRACT_AUTHORITY_DRIFT")
    if authority.get("workflow_task_effect_owner") != "ed3c/bettor-arena":
        refuse("WORKFLOW_EFFECT_AUTHORITY_DRIFT")
    if authority.get("independent_verification_owner") != "ed3c/truth-verify-loop":
        refuse("VERIFICATION_AUTHORITY_DRIFT")
    if authority.get("human_release_owner") != "EXTERNAL":
        refuse("HUMAN_RELEASE_AUTHORITY_DRIFT")

    parents = index.get("parents", {})
    if parents != {
        "57_runtime_contracts": "OPEN_DOWNSTREAM_PHYSICAL_CLOSURE",
        "58_transport": "OPEN_PHYSICAL_73",
        "59_identity": "OPEN_LIVE_83",
    }:
        refuse("PARENT_CLOSURE_LAUNDERING")

    live = index.get("live_frontier", {})
    expected_live = {
        "physical_nats_reconnect_issue": 73,
        "physical_nats_reconnect": "NOT_EXERCISED",
        "live_identity_issue": 83,
        "live_identity_enrollment_revocation_rotation": "NOT_EXERCISED",
        "secret_value_resolution": "NOT_EXERCISED",
        "workflow_effect_provider": "EXTERNAL_NOT_PROVEN_HERE",
        "physical_local_cloud_local": "NOT_EXERCISED",
        "human_admission": "NOT_PERFORMED",
        "release": "NOT_PERFORMED",
    }
    if live != expected_live:
        refuse("LIVE_STATE_PROMOTION")

    if index.get("evidence_ceiling") != "MERGED_DETERMINISTIC_RUNTIME_CONTRACT_TRANSPORT_IDENTITY_ONLY":
        refuse("EVIDENCE_CEILING_DRIFT")

    for token in (
        "Directory → State Machine → data ownership",
        "Process DAG",
        "Integrated molecular Stack",
        "Local Handoff Execution Queue",
        "TRANSPORT_ACKED` is not task success",
        "real NATS/JetStream               NOT_EXERCISED",
    ):
        if token not in readme:
            refuse("README_ROUTE_INCOMPLETE", token)

    for token in (
        "Exact-subject law",
        "Git DAG law",
        "Evidence non-substitution laws",
        "Shadow stop conditions",
        "Queue issue: #89",
        "transport ACK                  != task or user success",
    ):
        if token not in agents:
            refuse("AGENTS_ROUTE_INCOMPLETE", token)


class RuntimeDocsTest(unittest.TestCase):
    def load(self) -> tuple[dict, str, str]:
        return (
            json.loads((DOCS / "stack-index.json").read_text()),
            (DOCS / "README.md").read_text(),
            (DOCS / "AGENTS.md").read_text(),
        )

    def assert_code(self, code: str, fn) -> None:
        with self.assertRaises(RuntimeDocsError) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)

    def test_current_trace_is_exact_and_non_promoting(self) -> None:
        verify(*self.load())

    def test_live_state_cannot_promote(self) -> None:
        index, readme, agents = self.load()
        changed = deepcopy(index)
        changed["live_frontier"]["physical_nats_reconnect"] = "PASS"
        self.assert_code("LIVE_STATE_PROMOTION", lambda: verify(changed, readme, agents))

    def test_parent_cannot_close_from_deterministic_children(self) -> None:
        index, readme, agents = self.load()
        changed = deepcopy(index)
        changed["parents"]["58_transport"] = "CLOSED"
        self.assert_code("PARENT_CLOSURE_LAUNDERING", lambda: verify(changed, readme, agents))

    def test_runtime_cannot_take_workflow_effect_authority(self) -> None:
        index, readme, agents = self.load()
        changed = deepcopy(index)
        changed["authority"]["workflow_task_effect_owner"] = "ed3c/runtime-env"
        self.assert_code("WORKFLOW_EFFECT_AUTHORITY_DRIFT", lambda: verify(changed, readme, agents))

    def test_docs_cannot_self_promote(self) -> None:
        index, readme, agents = self.load()
        changed = deepcopy(index)
        changed["docs_subject_state"] = "RELEASED"
        self.assert_code("DOCS_SELF_PROMOTION", lambda: verify(changed, readme, agents))


if __name__ == "__main__":
    unittest.main()
