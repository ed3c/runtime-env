#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

profile="$(<"${ROOT}/profiles/bettor-arena-runtime-local.json")"
python3 -c '
import json, sys
value = json.load(sys.stdin)
modules = set(value["modules"])
required = {
  "agent-actor-claude-code",
  "agent-actor-codex-cli",
  "model-replay-actor-agy",
  "browser-transport-playwright-cdp",
  "browser-transport-stealth-playwright",
  "browser-transport-antigravity-puppeteer-cdp",
  "browser-transport-chatgpt-chrome-extension",
  "browser-transport-claude-in-chrome",
}
assert required <= modules, required - modules
' <<< "${profile}"

workload="$(${ROOT}/runtime-env workload show --id bettor-arena-proof)"
python3 -c '
import json, sys
value = json.load(sys.stdin)
assert value["entrypoints"]["carrier-contract"] == [
  "python3", "scripts/runtime-env/check-carrier-contract.py",
  "--matrix", "loop_wiki/evolve-technical-equivalence-research/carrier-capabilities.json",
]
assert value["entrypoint_environment"]["carrier-contract"] == []
assert value["entrypoints"]["stealth-profile-hygiene"] == [
  "sh", "scripts/runtime-env/check-stealth-profile-hygiene.sh",
]
assert value["entrypoint_environment"]["stealth-profile-hygiene"] == [
  "STEALTH_BROWSER_ROOT", "STEALTH_PROFILE_ROOT",
]
assert value["entrypoint_environment"]["stealth-browser-control"] == [
  "STEALTH_BROWSER_ROOT", "STEALTH_PROFILE_ROOT",
]
' <<< "${workload}"

codex="$(<"${ROOT}/modules/agent-actor-codex-cli.json")"
python3 -c '
import json, sys
value = json.load(sys.stdin)
assert "no native browser" in value["summary"].lower()
' <<< "${codex}"

stealth="$(<"${ROOT}/modules/browser-transport-stealth-playwright.json")"
python3 -c '
import json, sys
value = json.load(sys.stdin)
assert value["requires"] == ["STEALTH_BROWSER_ROOT", "STEALTH_PROFILE_ROOT"]
' <<< "${stealth}"

echo "PASS: runtime-env models actors and browser transports as separate modules"
