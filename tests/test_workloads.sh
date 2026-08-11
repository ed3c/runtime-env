#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

workloads="$(${ROOT}/runtime-env workload list)"
for workload in bettor-arena-proof repo-wiki-converge ios-testflight-verify ios-testflight-beta \
  gemini-conversation-research agy-gemini36-flash-high-replay dr-research-loop stealth-browser-mcp; do
  [[ "${workloads}" == *"${workload}"* ]] || {
    echo "FAIL: missing workload ${workload}" >&2
    exit 1
  }
done

python3 - "${ROOT}" <<'PY'
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
consumer_workloads = {
    "agy-gemini36-flash-high-replay",
    "bettor-arena-proof",
    "dr-research-loop",
    "gemini-conversation-research",
    "ios-testflight-beta",
    "ios-testflight-verify",
    "repo-wiki-converge",
    "stealth-browser-mcp",
}
for path in sorted((root / "workloads").glob("*.json")):
    workload = json.loads(path.read_text(encoding="utf-8"))
    acceptance = workload.get("acceptance_entrypoints")
    assert isinstance(acceptance, list) and acceptance, (
        f"{workload['id']} has no required live acceptance entrypoints"
    )
    for entrypoint in acceptance:
        assert entrypoint in workload["entrypoints"]
        assert not any(
            re.search(r"<[^>]+>", argument)
            for argument in workload["entrypoints"][entrypoint]
        ), f"{workload['id']} acceptance entrypoint {entrypoint} is unresolved"
    if workload["secret_delivery"] == "broker-only":
        adapters = workload.get("broker_adapters")
        assert isinstance(adapters, dict) and adapters, (
            f"{workload['id']} has no dedicated broker adapter mapping"
        )
    if workload["id"] in consumer_workloads:
        public_tests = workload.get("public_test_entrypoints")
        assert isinstance(public_tests, list) and public_tests, (
            f"{workload['id']} cannot reach L5 without public test entrypoints"
        )
        assert set(public_tests) <= set(acceptance)
PY

testflight="$(${ROOT}/runtime-env workload show --id ios-testflight-beta)"
python3 -c '
import json, sys
value = json.load(sys.stdin)
assert value["profile"] == "ios-testflight-ship-local"
assert value["secret_delivery"] == "broker-only"
assert value["agent_secret_access"] == "denied"
assert value["mutation"] == "external-release"
assert value["entrypoints"]["preflight"] == ["bash", "scripts/runtime-env/run-ios-acceptance.sh", "preflight"]
assert "IOS_TARGET_ROOT" in value["entrypoint_environment"]["preflight"]
assert value["evidence"]["control"]
' <<< "${testflight}"

repo_wiki="$(${ROOT}/runtime-env workload show --id repo-wiki-converge)"
python3 -c '
import json, sys
value = json.load(sys.stdin)
assert value["entrypoints"]["author"] == ["bash", "scripts/runtime-env/run-repo-wiki-acceptance.sh", "author"]
assert "REPO_WIKI_RUN_ROOT" in value["entrypoint_environment"]["author"]
assert "ANTIGRAVITY_KB_PYTHON" in value["entrypoint_environment"]["consumer-test"]
assert "adapter-test" in value["public_test_entrypoints"]
' <<< "${repo_wiki}"

gemini="$(${ROOT}/runtime-env workload show --id gemini-conversation-research)"
python3 -c '
import json, sys
value = json.load(sys.stdin)
assert value["entrypoints"]["extract"] == ["node", "scripts/runtime-env/run-gemini-acceptance.mjs", "extract"]
assert value["entrypoints"]["guided-edge"] == ["node", "scripts/runtime-env/run-gemini-acceptance.mjs", "guided"]
assert set(value["public_test_entrypoints"]) == {"carrier-gate", "guided-contract", "adapter-test"}
assert "GEMINI_RESEARCH_RUN_ROOT" in value["entrypoint_environment"]["extract"]
' <<< "${gemini}"

proof="$(${ROOT}/runtime-env workload show --id bettor-arena-proof)"
python3 -c '
import json, sys
value = json.load(sys.stdin)
assert value["secret_delivery"] == "broker-only"
assert value["entrypoint_environment"]["claude-auth-status"] == []
assert value["entrypoint_environment"]["codex-login-status"] == ["CODEX_HOME"]
assert "CODEX_HOME" not in value["entrypoint_environment"]["claude-auth-status"]
assert "CLAUDE_CONFIG_DIR" not in value["entrypoint_environment"]["codex-login-status"]
assert value["entrypoints"]["claude-auth-status"][-1] == "claude"
assert value["entrypoints"]["codex-login-status"][-1] == "codex"
assert value["entrypoints"]["agy-model-inventory"][-1] == "agy"
assert value["entrypoint_environment"]["research-browser-health"] == ["DR_CDP_URL"]
assert value["evidence"]["receipt"]
assert value["evidence"]["control"]
' <<< "${proof}"

echo 'PASS: typed workloads preserve secret and evidence boundaries'
