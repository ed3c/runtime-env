#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

policies="$(${ROOT}/runtime-env policy list)"
[[ "${policies}" == *'claude-code-native-isolation'* ]]
[[ "${policies}" == *'codex-cli-native-isolation'* ]]

claude="$(${ROOT}/runtime-env policy show --id claude-code-native-isolation)"
python3 -c '
import json, sys
p = json.load(sys.stdin)
assert p["config_home_env"] == "CLAUDE_CONFIG_DIR"
assert p["required_settings"]["sandbox.enabled"] is True
assert p["required_settings"]["sandbox.failIfUnavailable"] is True
assert p["required_settings"]["sandbox.allowUnsandboxedCommands"] is False
assert p["required_settings"]["permissions.disableBypassPermissionsMode"] == "disable"
assert "CODEX_HOME" in p["forbidden_environment"]
assert "Read(<stealth-profile-root>/**)" in p["required_settings"]["permissions.deny"]
assert "Edit(<stealth-profile-root>/**)" in p["required_settings"]["permissions.deny"]
assert "<stealth-profile-root>" in p["required_settings"]["sandbox.filesystem.denyRead"]
assert "<stealth-profile-root>" in p["required_settings"]["sandbox.filesystem.denyWrite"]
assert not any("<stealth-browser-root>/profiles" in value for value in p["required_settings"]["permissions.deny"])
' <<< "${claude}"

codex="$(${ROOT}/runtime-env policy show --id codex-cli-native-isolation)"
python3 -c '
import json, sys
p = json.load(sys.stdin)
assert p["config_home_env"] == "CODEX_HOME"
assert p["required_settings"]["sandbox_mode"] == "workspace-write"
assert p["required_settings"]["approval_policy"] == "on-request"
assert p["required_settings"]["shell_environment_policy.inherit"] == "none"
assert p["required_settings"]["shell_environment_policy.ignore_default_excludes"] is False
assert "CLAUDE_CONFIG_DIR" in p["forbidden_environment"]
assert any("deny" in item.lower() for item in p["external_requirements"])
assert any("<stealth-profile-root>" in item for item in p["external_requirements"])
' <<< "${codex}"

echo 'PASS: Claude and Codex native settings remain isolated and fail closed'
