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

testflight="$(${ROOT}/runtime-env workload show --id ios-testflight-beta)"
python3 -c '
import json, sys
value = json.load(sys.stdin)
assert value["profile"] == "ios-testflight-ship-local"
assert value["secret_delivery"] == "broker-only"
assert value["agent_secret_access"] == "denied"
assert value["mutation"] == "external-release"
assert value["evidence"]["control"]
' <<< "${testflight}"

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
assert value["evidence"]["receipt"]
assert value["evidence"]["control"]
' <<< "${proof}"

echo 'PASS: typed workloads preserve secret and evidence boundaries'
