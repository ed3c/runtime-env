#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
H40 = re.compile(r"^[0-9a-f]{40}$")


class RuntimeStatusError(AssertionError):
    pass


def refuse(code: str, detail: str = "") -> None:
    raise RuntimeStatusError(f"{code}: {detail}" if detail else code)


def verify(index: dict, readme: str, agents: str, review: str, queue: str) -> None:
    if index.get("schema") != "runtime-env.dual-agent-runtime-stack-index.v1":
        refuse("INDEX_SCHEMA_DRIFT")
    if index.get("owner_issue") != 88 or index.get("parent_issues") != [57, 58, 59]:
        refuse("OWNER_ROUTE_DRIFT")

    authority = index.get("authority", {})
    if authority.get("this_index_canonical_write") != "NONE":
        refuse("DOCS_AUTHORITY_WIDENING")
    if authority.get("human_release_owner") != "external-trusted-authority":
        refuse("HUMAN_RELEASE_OWNER_DRIFT")
    for key in ("workflow_owner", "effect_owner", "provider_owner", "independent_verification_owner"):
        if not str(authority.get(key, "")).startswith("external:"):
            refuse("EXTERNAL_AUTHORITY_DRIFT", key)

    expected = {
        ("DA-RC-C", 61, 69),
        ("DA-TR-C", 70, 76),
        ("DA-TR-L", 71, 77),
        ("DA-TR-N", 72, 78),
        ("DA-ID-C", 75, 79),
        ("DA-ID-L", 80, 85),
        ("DA-ID-CLOUD", 81, 86),
        ("DA-ID-P", 82, 87),
    }
    nodes = index.get("merged_nodes")
    if not isinstance(nodes, list):
        refuse("MERGED_NODE_SET_MISSING")
    observed = {(item.get("atom"), item.get("issue"), item.get("pr")) for item in nodes if isinstance(item, dict)}
    if observed != expected:
        refuse("MERGED_NODE_SET_DRIFT")
    for node in nodes:
        if node.get("state") != "MERGED_DETERMINISTIC":
            refuse("MERGE_STATE_DRIFT", str(node.get("atom")))
        if not H40.fullmatch(str(node.get("candidate_head", ""))):
            refuse("EXACT_HEAD_MISSING", str(node.get("atom")))
        if not H40.fullmatch(str(node.get("candidate_tree", ""))):
            refuse("EXACT_TREE_MISSING", str(node.get("atom")))
        run = node.get("prior_exact_head_ci")
        if not isinstance(run, int) or isinstance(run, bool) or run <= 0:
            refuse("CI_RECEIPT_MISSING", str(node.get("atom")))

    if index.get("closed_completed_issues") != [61, 70, 71, 72, 75, 80, 81, 82]:
        refuse("ISSUE_CLOSURE_DRIFT")
    if index.get("open_parent_issues") != [57, 58, 59]:
        refuse("PARENT_CLOSURE_LAUNDERING")

    docs = index.get("documentation_convergence", {})
    if docs.get("current_issue") != 88 or docs.get("stale_pr") != 60 or docs.get("absorbed_issues") != [74, 84]:
        refuse("DOCS_CONVERGENCE_DRIFT")
    if docs.get("state") != "CURRENT_MAIN_DOCS_CANDIDATE":
        refuse("DOCS_SELF_PROMOTION")

    live = index.get("live_frontier")
    expected_live = {
        (73, "PHYSICAL_NATS_JETSTREAM_DISCONNECT_RECONNECT_REDELIVERY_RESTART", "NOT_EXERCISED"),
        (83, "LIVE_LOCAL_CLOUD_IDENTITY_POLICY_SECRET_REVOCATION_ROTATION", "NOT_EXERCISED"),
    }
    observed_live = {(item.get("issue"), item.get("capability"), item.get("state")) for item in live if isinstance(item, dict)} if isinstance(live, list) else set()
    if observed_live != expected_live:
        refuse("LIVE_FRONTIER_DRIFT")

    if index.get("physical_product_state") != "NOT_CLOSED":
        refuse("FALSE_PHYSICAL_CLOSURE")
    if index.get("human_state") != "NOT_PERFORMED" or index.get("release_state") != "NOT_PERFORMED":
        refuse("HUMAN_RELEASE_PROMOTION")
    if index.get("evidence_ceiling") != "MERGED_DETERMINISTIC_RUNTIME_CONTRACT_TRANSPORT_IDENTITY_ONLY":
        refuse("EVIDENCE_CEILING_DRIFT")

    required_docs = {
        "README": (readme, [
            "MERGED_DETERMINISTIC_RUNTIME_PLANE / LIVE_RUNTIME_OPEN",
            "Directory → State Machine ownership",
            "Git DAG admitted to main",
            "#73  physical NATS/JetStream",
            "#83  distinct local/cloud identity",
            "transport ACK                != workflow/task/user success",
        ]),
        "AGENTS": (agents, [
            "canonical_write=NONE",
            "A true child consumes named unmerged parent bytes.",
            "Do not self-approve.",
            "Shadow stop conditions",
            "NATS adapter PASS            != live NATS server/stream/consumer",
        ]),
        "MERGE_REVIEW": (review, [
            "Issues closed as completed",
            "Must remain open",
            "PR #60",
            "#74 and #84",
        ]),
        "QUEUE": (queue, [
            "LH-R01", "LH-R02", "LH-R03", "LH-R04", "LH-R05",
            "LH-I01", "LH-I02", "LH-RI01", "Completion packet",
        ]),
    }
    for name, (document, tokens) in required_docs.items():
        for token in tokens:
            if token not in document:
                refuse(f"{name}_INCOMPLETE", token)


class RuntimeStatusTest(unittest.TestCase):
    def load(self) -> tuple[dict, str, str, str, str]:
        return (
            json.loads((ROOT / "stack-index.json").read_text()),
            (ROOT / "README.md").read_text(),
            (ROOT / "AGENTS.md").read_text(),
            (ROOT / "merge-review.md").read_text(),
            (ROOT / "local-handoff-queue.md").read_text(),
        )

    def assert_code(self, code: str, fn) -> None:
        with self.assertRaises(RuntimeStatusError) as caught:
            fn()
        self.assertTrue(str(caught.exception).startswith(code))

    def test_current_snapshot(self) -> None:
        verify(*self.load())

    def test_docs_cannot_become_writer(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["authority"]["this_index_canonical_write"] = "TASK_EFFECT_RELEASE"
        self.assert_code("DOCS_AUTHORITY_WIDENING", lambda: verify(changed, *docs))

    def test_parent_issues_cannot_be_laundered_closed(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["open_parent_issues"] = []
        self.assert_code("PARENT_CLOSURE_LAUNDERING", lambda: verify(changed, *docs))

    def test_live_frontier_cannot_be_erased(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["live_frontier"] = changed["live_frontier"][:1]
        self.assert_code("LIVE_FRONTIER_DRIFT", lambda: verify(changed, *docs))

    def test_deterministic_merge_cannot_close_physical_product(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["physical_product_state"] = "CLOSED"
        self.assert_code("FALSE_PHYSICAL_CLOSURE", lambda: verify(changed, *docs))

    def test_candidate_head_must_remain_exact(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["merged_nodes"][0]["candidate_head"] = "main"
        self.assert_code("EXACT_HEAD_MISSING", lambda: verify(changed, *docs))


if __name__ == "__main__":
    unittest.main()
