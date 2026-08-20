#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
H40 = re.compile(r"^[0-9a-f]{40}$")
H64 = re.compile(r"^[0-9a-f]{64}$")


class RuntimeStatusError(AssertionError):
    pass


def refuse(code: str, detail: str = "") -> None:
    raise RuntimeStatusError(f"{code}: {detail}" if detail else code)


def check(index: dict, readme: str, agents: str, queue: str) -> None:
    if index.get("schema") != "runtime-env.dual-agent-runtime-stack-index.v1":
        refuse("INDEX_SCHEMA_DRIFT")
    if index.get("owner_issues") != [74, 84] or index.get("parent_issues") != [57, 58, 59]:
        refuse("ISSUE_ROUTE_DRIFT")

    authority = index.get("authority", {})
    if authority.get("wire_contract_owner") != "ed3c/runtime-env":
        refuse("WIRE_AUTHORITY_DRIFT")
    if authority.get("workflow_effect_owner") != "ed3c/bettor-arena":
        refuse("WORKFLOW_EFFECT_AUTHORITY_DRIFT")
    if authority.get("provider_owner") != "ed3c/agent-shield-monorepo":
        refuse("PROVIDER_AUTHORITY_DRIFT")
    if authority.get("this_index_canonical_write") != "NONE":
        refuse("DOCS_AUTHORITY_WIDENING")

    method = index.get("method_subject", {})
    if not H40.fullmatch(str(method.get("commit", ""))) or not H40.fullmatch(str(method.get("tree", ""))):
        refuse("METHOD_SUBJECT_MUTABLE")
    if not H64.fullmatch(str(method.get("method_digest", ""))):
        refuse("METHOD_DIGEST_INVALID")
    if not H64.fullmatch(str(index.get("contract_set_digest", ""))):
        refuse("CONTRACT_SET_DIGEST_INVALID")

    expected_atoms = {
        "DA-RC-C",
        "DA-TR-C",
        "DA-TR-L",
        "DA-TR-N",
        "DA-ID-C",
        "DA-ID-L",
        "DA-ID-CLOUD",
        "DA-ID-P",
    }
    nodes = index.get("nodes")
    if not isinstance(nodes, list) or {item.get("atom") for item in nodes if isinstance(item, dict)} != expected_atoms:
        refuse("NODE_DENOMINATOR_DRIFT")
    for node in nodes:
        if node.get("state") != "MERGED_DETERMINISTIC":
            refuse("MERGED_STATE_DRIFT", str(node.get("atom")))
        if not H40.fullmatch(str(node.get("head", ""))) or not H40.fullmatch(str(node.get("tree", ""))):
            refuse("EXACT_SUBJECT_MISSING", str(node.get("atom")))
        run = node.get("targeted_run")
        if not isinstance(run, int) or isinstance(run, bool) or run <= 0:
            refuse("TARGETED_RUN_MISSING", str(node.get("atom")))
        ceiling = str(node.get("evidence_ceiling", ""))
        if not ceiling.endswith("ONLY"):
            refuse("EVIDENCE_CEILING_WIDENING", str(node.get("atom")))

    live = index.get("live_frontier")
    expected_live = {
        (73, "NOT_EXERCISED"),
        (83, "NOT_EXERCISED"),
        (186, "NOT_EXERCISED"),
    }
    if not isinstance(live, list) or {(item.get("issue"), item.get("state")) for item in live if isinstance(item, dict)} != expected_live:
        refuse("LIVE_FRONTIER_DRIFT")

    if index.get("program_state") != "RUNTIME_DETERMINISTIC_SUBTREE_MERGED_LIVE_FRONTIER_OPEN":
        refuse("PROGRAM_STATE_PROMOTION")

    required_docs = {
        "README": (
            readme,
            [
                "Directory → State Machine",
                "Admitted Git Stack",
                "Process DAG",
                "Runtime data flow",
                "Real problem denominator still open",
                "runtime merge                 != physical product closure",
            ],
        ),
        "AGENTS": (
            agents,
            [
                "canonical_write=NONE",
                "A true child consumes named unmerged parent bytes.",
                "Do not self-approve",
                "Shadow stop conditions",
                "SQLite replay PASS              != physical reconnect",
            ],
        ),
        "QUEUE": (
            queue,
            [
                "RH-01",
                "RH-02",
                "RH-03",
                "RH-04",
                "RH-05",
                "Completion packet",
                "HUMAN_TRUSTED_RUNTIME_REQUIRED",
            ],
        ),
    }
    for name, (document, tokens) in required_docs.items():
        for token in tokens:
            if token not in document:
                refuse(f"{name}_INCOMPLETE", token)


class RuntimeStatusTest(unittest.TestCase):
    def load(self) -> tuple[dict, str, str, str]:
        return (
            json.loads((ROOT / "stack-index.json").read_text()),
            (ROOT / "README.md").read_text(),
            (ROOT / "AGENTS.md").read_text(),
            (ROOT / "local-handoff-queue.md").read_text(),
        )

    def assert_code(self, code: str, fn) -> None:
        with self.assertRaises(RuntimeStatusError) as caught:
            fn()
        self.assertTrue(str(caught.exception).startswith(code))

    def test_current_snapshot_is_non_promoting(self) -> None:
        check(*self.load())

    def test_docs_cannot_become_runtime_writer(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["authority"]["this_index_canonical_write"] = "TRANSPORT_IDENTITY"
        self.assert_code("DOCS_AUTHORITY_WIDENING", lambda: check(changed, *docs))

    def test_merged_node_requires_exact_subject(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["nodes"][0]["head"] = "main"
        self.assert_code("EXACT_SUBJECT_MISSING", lambda: check(changed, *docs))

    def test_live_frontier_cannot_be_erased(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["live_frontier"] = changed["live_frontier"][:-1]
        self.assert_code("LIVE_FRONTIER_DRIFT", lambda: check(changed, *docs))

    def test_physical_state_cannot_be_promoted(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["live_frontier"][0]["state"] = "PASS"
        self.assert_code("LIVE_FRONTIER_DRIFT", lambda: check(changed, *docs))

    def test_contract_ceiling_cannot_widen(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["nodes"][0]["evidence_ceiling"] = "LIVE_RUNTIME_PASS"
        self.assert_code("EVIDENCE_CEILING_WIDENING", lambda: check(changed, *docs))


if __name__ == "__main__":
    unittest.main()
