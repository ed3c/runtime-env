#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "$ROOT" <<'PY'
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
manifest = json.loads((root / "contracts/dual-agent/contract-set-manifest.json").read_text())
index = json.loads((root / "docs/architecture/dual-agent-runtime/stack-index.json").read_text())
readme = (root / "docs/architecture/dual-agent-runtime/README.md").read_text()
agents = (root / "docs/architecture/dual-agent-runtime/AGENTS.md").read_text()
contract_readme = (root / "contracts/dual-agent/README.md").read_text()
docs_index = (root / "docs/INDEX.md").read_text()

IMPLEMENTATION_COMMIT = "92feed7c4e671dc63238155da9d4f394aac80d90"
IMPLEMENTATION_TREE = "406895a4b0ac0df301d146aa89940c6adda402cd"
CONTRACT_SET = "e6671977dbf0a378474f924a142a82843bc0e3429f4546ffb0145af73f7827fe"
CEILING = "DETERMINISTIC_DUAL_AGENT_RUNTIME_STACK_ONLY"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


require(manifest["manifest_state"] == "BOUND", "manifest must be BOUND")
require(
    manifest["runtime_subject"]
    == {
        "repository": "ed3c/runtime-env",
        "commit": IMPLEMENTATION_COMMIT,
        "tree": IMPLEMENTATION_TREE,
    },
    "runtime subject drift",
)
require(manifest["contract_set_digest"] == CONTRACT_SET, "contract-set digest drift")
required_unproven = {
    "PHYSICAL_CROSS_HOST_TRANSPORT_EXECUTION",
    "LIVE_NATS_JETSTREAM_SERVER_CONSUMER_TLS",
    "LIVE_WORKLOAD_IDENTITY_ENROLLMENT_ATTESTATION",
    "LIVE_SECRET_RESOLUTION",
    "LIVE_POLICY_PROVIDER_REVOCATION_ROTATION",
    "WORKFLOW_EXECUTION",
    "PROVIDER_SANDBOX_EXECUTION",
    "EXTERNAL_EFFECT_EXECUTION",
    "USER_OUTCOME",
    "HUMAN_ADMISSION",
    "RELEASE",
}
require(set(manifest["claims_not_proven"]) == required_unproven, "unproven-claim denominator drift")

require(index["schema"] == "runtime-env.dual-agent-runtime-stack-index.v1", "Stack schema drift")
require(index["trace_state"] == "MAIN_IMPLEMENTATION_TRACE", "trace state drift")
require(
    index["implementation_main"]
    == {
        "repository": "ed3c/runtime-env",
        "branch": "main",
        "commit": IMPLEMENTATION_COMMIT,
        "tree": IMPLEMENTATION_TREE,
        "merge_pr": 69,
        "state": "DETERMINISTIC_RUNTIME_STACK_MERGED",
    },
    "main implementation subject drift",
)
require(index["contract_set"] == {"manifest_state": "BOUND", "digest": CONTRACT_SET}, "Stack contract binding drift")

expected_nodes = {
    "DA-RC-C": (61, 69, "1fd6a65a2e628ba1b31e89800297e7202dadf126", "cc287010c96391e0a718141c2f4afb92bac3db06", 32251505194),
    "DA-TR-C": (70, 76, "08fd712572ebe63b3c4286b361909a11ded9d172", "a0971d7b4bb0f70548989582f54f522ce655c91b", 32252919999),
    "DA-TR-L": (71, 77, "f910536b5a8ace7610eb8957cd3eb37f16c08065", "a1aa879cbd9b0d8ddf9845183c4d1a3e3a6dc4e3", 32253473378),
    "DA-TR-N": (72, 78, "ebf7e36387d4ffff8f8b428eb062525098013f5c", "c706be102cb4466ffed041d7985e3713579528be", 32254465413),
    "DA-ID-C": (75, 79, "5c9a960ed9883e294d6cdb5c949256cf937972ed", "b8c7efc2a653a008cf12aa4f7120ed526eb80b3d", 32254852893),
    "DA-ID-L": (80, 85, "8ea2667265b553059b2879f800c7bb1afc788d40", "48a5744fd4ca6d6d7b6a4921dba81c02c7c3ddaf", 32258804609),
    "DA-ID-CLOUD": (81, 86, "940f9c74be8b8f7b2c427e79725786059696cd45", "61a7e346c6e0e0a1346d8363188db5128615fd35", 32259034357),
    "DA-ID-P": (82, 87, "22bff7e329209491ee47e29c4cdd8c74b4725d81", "8ddb3c88e80f76ef74210d9fba9b0c9a540404ce", 32259277414),
}
by_atom = {node["atom"]: node for node in index["nodes"]}
require(set(by_atom) == set(expected_nodes), "molecular node set drift")
for atom, (issue, pr, head, tree, run) in expected_nodes.items():
    node = by_atom[atom]
    require(node["issue"] == issue, f"{atom} issue drift")
    require(node["pr"] == pr, f"{atom} PR drift")
    require(node["head"] == head, f"{atom} head drift")
    require(node["tree"] == tree, f"{atom} tree drift")
    require(node["targeted_run"] == run, f"{atom} run drift")
    require("MERGED" in node["state"], f"{atom} must remain merged deterministic state")

require(index["evidence_ceiling"] == CEILING, "evidence ceiling drift")
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
require(index["live_frontier"] == expected_live, "live frontier promotion or drift")

closure = index["closure_actions"]
require(closure["issues_keep_open"] == [58, 59, 73, 83], "open live issue set drift")
require(set(closure["issues_ready_to_close_completed"]) == {57, 61, 70, 71, 72, 74, 75, 80, 81, 82, 84}, "closure action drift")
require(closure["prs_ready_to_close_superseded"] == [60], "superseded PR drift")

handoffs = {item["id"]: item for item in index["local_handoffs"]}
require(set(handoffs) == {"LH-TR-001", "LH-ID-001"}, "handoff set drift")
for handoff_id, owner in (("LH-TR-001", "ed3c/runtime-env#73"), ("LH-ID-001", "ed3c/runtime-env#83")):
    handoff = handoffs[handoff_id]
    require(handoff["owner"] == owner, f"{handoff_id} owner drift")
    require(handoff["state"] == "HANDOFF_READY_NOT_EXERCISED", f"{handoff_id} self-promotion")
    require(handoff["exact_base"]["commit"] == IMPLEMENTATION_COMMIT, f"{handoff_id} base commit drift")
    require(handoff["exact_base"]["tree"] == IMPLEMENTATION_TREE, f"{handoff_id} base tree drift")
    for field in ("idempotency", "timeout", "receipt", "rollback", "verifier"):
        require(bool(handoff.get(field)), f"{handoff_id} missing {field}")

readme_tokens = [
    IMPLEMENTATION_COMMIT,
    IMPLEMENTATION_TREE,
    CONTRACT_SET,
    CEILING,
    "Directory → State Machine → DAG owner",
    "Process DAG",
    "Git Stack and merge chain",
    "Data flow",
    "LH-TR-001",
    "LH-ID-001",
    "physical local→cloud→local",
    "ACK                      != workflow/task/effect/user success",
]
for token in readme_tokens:
    require(token in readme, f"README missing {token}")

agents_tokens = [
    IMPLEMENTATION_COMMIT,
    IMPLEMENTATION_TREE,
    "State Machine",
    "Path and writer leases",
    "Git Stack law",
    "Evidence non-substitution laws",
    "LH-TR-001",
    "LH-ID-001",
    "Shadow stop conditions",
    "Use `NOT_EXERCISED` or `NOT_PERFORMED`, never fake PASS.",
]
for token in agents_tokens:
    require(token in agents, f"AGENTS missing {token}")

for token in (IMPLEMENTATION_COMMIT, CONTRACT_SET, "manifest state      BOUND", CEILING):
    require(token in contract_readme, f"contract README missing {token}")

for token in (
    "architecture/dual-agent-runtime/README.md",
    "architecture/dual-agent-runtime/AGENTS.md",
    "architecture/dual-agent-runtime/stack-index.json",
):
    require(token in docs_index, f"docs index missing {token}")

# Planted controls: a docs/trace mutation cannot promote live evidence or move a handoff owner.
mutated = copy.deepcopy(index)
mutated["live_frontier"]["physical_cross_host_transport"] = "PASS"
require(mutated["live_frontier"] != expected_live, "live promotion mutation must be observable")
mutated = copy.deepcopy(index)
mutated["local_handoffs"][0]["owner"] = "ed3c/runtime-env"
require(mutated["local_handoffs"][0]["owner"] != "ed3c/runtime-env#73", "handoff owner mutation must be observable")

print("PASS: Dual-Agent merged runtime trace + LH-TR-001 + LH-ID-001")
PY
