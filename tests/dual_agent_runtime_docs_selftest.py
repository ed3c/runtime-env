from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture" / "dual-agent-runtime"
H40 = re.compile(r"^[0-9a-f]{40}$")
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
EXPECTED_READY_TO_CLOSE = {57, 61, 70, 71, 72, 74, 75, 80, 81, 82, 84}
EXPECTED_KEEP_OPEN = {58, 59, 73, 83}
EXPECTED_MERGED_PRS = {69, 76, 77, 78, 79, 85, 86, 87}


class RuntimeDocsError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


def refuse(code: str, detail: str = "") -> None:
    raise RuntimeDocsError(code, detail)


def require_h40(value: object, *, code: str, detail: str) -> str:
    if not isinstance(value, str) or not H40.fullmatch(value):
        refuse(code, detail)
    return value


def verify(index: dict, readme: str, agents: str) -> None:
    if index.get("schema") != "runtime-env.dual-agent-runtime-stack-index.v1":
        refuse("STACK_SCHEMA_DRIFT")
    if index.get("trace_owner_issue") != 50:
        refuse("TRACE_OWNER_DRIFT")
    if index.get("transport_docs_issue") != 74 or index.get("identity_docs_issue") != 84:
        refuse("DOCS_ROUTE_DRIFT")
    if index.get("trace_state") != "MAIN_IMPLEMENTATION_TRACE":
        refuse("DOCS_SELF_PROMOTION")

    implementation = index.get("implementation_main")
    if not isinstance(implementation, dict):
        refuse("MAIN_SUBJECT_MISSING")
    if implementation.get("repository") != "ed3c/runtime-env" or implementation.get("branch") != "main":
        refuse("MAIN_SUBJECT_DRIFT")
    main_commit = require_h40(
        implementation.get("commit"), code="MAIN_SUBJECT_MISSING", detail="commit"
    )
    main_tree = require_h40(
        implementation.get("tree"), code="MAIN_SUBJECT_MISSING", detail="tree"
    )
    if implementation.get("state") != "DETERMINISTIC_RUNTIME_STACK_MERGED":
        refuse("MAIN_STATE_DRIFT")

    method = index.get("method_subject")
    if not isinstance(method, dict):
        refuse("METHOD_SUBJECT_MISSING")
    require_h40(method.get("commit"), code="METHOD_SUBJECT_MISSING", detail="commit")
    require_h40(method.get("tree"), code="METHOD_SUBJECT_MISSING", detail="tree")
    if not isinstance(method.get("sha256"), str) or len(method["sha256"]) != 64:
        refuse("METHOD_SUBJECT_MISSING", "sha256")

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
        if item.get("state") != "MERGED_CONTRACT_CLOSED":
            refuse("NODE_STATE_DRIFT", atom)
        require_h40(item.get("head"), code="EXACT_SUBJECT_MISSING", detail=f"{atom}.head")
        require_h40(item.get("tree"), code="EXACT_SUBJECT_MISSING", detail=f"{atom}.tree")
        if not isinstance(item.get("targeted_run"), int):
            refuse("RUN_RECEIPT_MISSING", atom)

    merge_chain = index.get("merge_chain")
    if not isinstance(merge_chain, dict):
        refuse("MERGE_CHAIN_MISSING")
    main_merge = merge_chain.get("main")
    if not isinstance(main_merge, dict) or main_merge.get("pr") != 69:
        refuse("MERGE_CHAIN_DRIFT", "main")
    if main_merge.get("merge") != main_commit:
        refuse("MERGE_CHAIN_DRIFT", "main.merge")

    authority = index.get("authority", {})
    if authority.get("method_owner") != "ed3c/skills-shared":
        refuse("METHOD_AUTHORITY_DRIFT")
    if authority.get("wire_contract_owner") != "ed3c/runtime-env/contracts/dual-agent":
        refuse("CONTRACT_AUTHORITY_DRIFT")
    if authority.get("workflow_owner") != "ed3c/bettor-arena" or authority.get("effect_owner") != "ed3c/bettor-arena":
        refuse("WORKFLOW_EFFECT_AUTHORITY_DRIFT")
    if authority.get("provider_owner") != "ed3c/agent-shield-monorepo":
        refuse("PROVIDER_AUTHORITY_DRIFT")
    if authority.get("verification_owner") != "ed3c/truth-verify-loop":
        refuse("VERIFICATION_AUTHORITY_DRIFT")
    if authority.get("human_admission") != "EXTERNAL" or authority.get("release") != "EXTERNAL":
        refuse("HUMAN_RELEASE_AUTHORITY_DRIFT")

    actions = index.get("closure_actions")
    if not isinstance(actions, dict):
        refuse("CLOSURE_ACTIONS_MISSING")
    if set(actions.get("issues_ready_to_close_completed", [])) != EXPECTED_READY_TO_CLOSE:
        refuse("CLOSURE_ACTION_DRIFT", "ready_to_close")
    if set(actions.get("issues_keep_open", [])) != EXPECTED_KEEP_OPEN:
        refuse("PARENT_CLOSURE_LAUNDERING")
    if set(actions.get("prs_merged", [])) != EXPECTED_MERGED_PRS:
        refuse("MERGE_ACTION_DRIFT")
    if set(actions.get("prs_ready_to_close_superseded", [])) != {60}:
        refuse("SUPERSESSION_ACTION_DRIFT")

    live = index.get("live_frontier", {})
    expected_live = {
        "physical_cross_host_transport": "NOT_EXERCISED",
        "live_nats_jetstream_tls": "NOT_EXERCISED",
        "live_local_identity_and_secret_resolution": "NOT_EXERCISED",
        "live_cloud_identity_attestation_and_issuance": "NOT_EXERCISED",
        "live_policy_revocation_rotation": "NOT_EXERCISED",
        "workflow_execution": "NOT_EXERCISED_BY_RUNTIME_ENV",
        "provider_execution": "NOT_EXERCISED_BY_RUNTIME_ENV",
        "effect_execution": "NOT_EXERCISED_BY_RUNTIME_ENV",
        "user_outcome": "NOT_EXERCISED",
        "human": "NOT_EXERCISED",
        "release": "NOT_PERFORMED",
    }
    if live != expected_live:
        refuse("LIVE_STATE_PROMOTION")

    if index.get("evidence_ceiling") != "DETERMINISTIC_DUAL_AGENT_RUNTIME_STACK_ONLY":
        refuse("EVIDENCE_CEILING_DRIFT")

    handoffs = index.get("local_handoffs")
    if not isinstance(handoffs, list) or len(handoffs) != 2:
        refuse("HANDOFF_SET_DRIFT")
    by_id = {item.get("id"): item for item in handoffs if isinstance(item, dict)}
    expected_handoffs = {
        "LH-TR-001": ("ed3c/runtime-env#73", "ed3c/runtime-env#58"),
        "LH-ID-001": ("ed3c/runtime-env#83", "ed3c/runtime-env#59"),
    }
    if set(by_id) != set(expected_handoffs):
        refuse("HANDOFF_SET_DRIFT")
    for handoff_id, (owner, parent) in expected_handoffs.items():
        handoff = by_id[handoff_id]
        if handoff.get("owner") != owner or handoff.get("parent") != parent:
            refuse("HANDOFF_OWNER_DRIFT", handoff_id)
        if handoff.get("state") != "HANDOFF_READY_NOT_EXERCISED":
            refuse("HANDOFF_SELF_PROMOTION", handoff_id)
        exact_base = handoff.get("exact_base")
        if not isinstance(exact_base, dict):
            refuse("HANDOFF_BASE_DRIFT", handoff_id)
        if exact_base.get("repository") != "ed3c/runtime-env" or exact_base.get("commit") != main_commit or exact_base.get("tree") != main_tree:
            refuse("HANDOFF_BASE_DRIFT", handoff_id)
        for field in ("idempotency", "timeout", "receipt", "rollback", "verifier"):
            if not isinstance(handoff.get(field), str) or not handoff[field].strip():
                refuse("HANDOFF_PACKET_INCOMPLETE", f"{handoff_id}.{field}")

    readme_tokens = (
        "## Directory → State Machine → DAG owner",
        "## Process DAG",
        "## Git Stack and merge chain",
        "## Local Handoff Execution Queue",
        "Transport authentication never implies execution authorization or task success.",
        "`LIVE_NATS_CONNECTED`",
    )
    for token in readme_tokens:
        if token not in readme:
            refuse("README_ROUTE_INCOMPLETE", token)

    agents_tokens = (
        "## Git Stack law",
        "## Evidence non-substitution laws",
        "## Shadow stop conditions",
        "LH-TR-001 / #73",
        "LH-ID-001 / #83",
        "ACK                      != workflow/task/effect/user success",
    )
    for token in agents_tokens:
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
        changed["live_frontier"]["physical_cross_host_transport"] = "PASS"
        self.assert_code("LIVE_STATE_PROMOTION", lambda: verify(changed, readme, agents))

    def test_parent_cannot_close_from_deterministic_children(self) -> None:
        index, readme, agents = self.load()
        changed = deepcopy(index)
        changed["closure_actions"]["issues_keep_open"].remove(58)
        changed["closure_actions"]["issues_ready_to_close_completed"].append(58)
        self.assert_code("CLOSURE_ACTION_DRIFT", lambda: verify(changed, readme, agents))

    def test_runtime_cannot_take_workflow_effect_authority(self) -> None:
        index, readme, agents = self.load()
        changed = deepcopy(index)
        changed["authority"]["workflow_owner"] = "ed3c/runtime-env"
        self.assert_code("WORKFLOW_EFFECT_AUTHORITY_DRIFT", lambda: verify(changed, readme, agents))

    def test_docs_cannot_self_promote(self) -> None:
        index, readme, agents = self.load()
        changed = deepcopy(index)
        changed["trace_state"] = "RELEASED"
        self.assert_code("DOCS_SELF_PROMOTION", lambda: verify(changed, readme, agents))

    def test_handoff_cannot_self_promote(self) -> None:
        index, readme, agents = self.load()
        changed = deepcopy(index)
        changed["local_handoffs"][0]["state"] = "LIVE_PASS"
        self.assert_code("HANDOFF_SELF_PROMOTION", lambda: verify(changed, readme, agents))


if __name__ == "__main__":
    unittest.main()
