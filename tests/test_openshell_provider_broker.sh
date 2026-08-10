#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "${SCRATCH}"' EXIT

python3 - "${ROOT}" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
variables = {
    item["name"]: item
    for item in json.loads((root / "catalog/variables.json").read_text())["variables"]
}
module = json.loads((root / "modules/openshell-agent-providers.json").read_text())
transport = json.loads(
    (root / "policies/codex-openshell-chatgpt-placeholder.json").read_text()
)
for name in (
    "OPENSHELL_CLAUDE_PROVIDER",
    "OPENSHELL_CODEX_PROVIDER",
    "CODEX_SANDBOX_MODEL",
    "OPENSHELL_GATEWAY",
    "OPENSHELL_GATEWAY_ENDPOINT",
):
    assert name in variables and variables[name]["secret"] is False
    assert name in module["optional"]
assert module["defaults"]["CODEX_SANDBOX_MODEL"] == "gpt-5.6-sol"
for profile_name in (
    "bettor-arena-runtime-local",
    "dr-research-loop-local",
    "logged-in-agent-carriers-local",
):
    profile = json.loads((root / f"profiles/{profile_name}.json").read_text())
    assert "openshell-agent-providers" in profile["modules"]

settings = transport["required_settings"]
assert transport["carrier"] == "codex-cli"
assert settings == {
    "model_provider": "openshell_chatgpt",
    "model_providers.openshell_chatgpt.base_url": "https://chatgpt.com/backend-api/codex",
    "model_providers.openshell_chatgpt.env_http_headers.ChatGPT-Account-ID": "CODEX_AUTH_ACCOUNT_ID",
    "model_providers.openshell_chatgpt.env_key": "CODEX_AUTH_ACCESS_TOKEN",
    "model_providers.openshell_chatgpt.requires_openai_auth": False,
    "model_providers.openshell_chatgpt.supports_websockets": False,
    "model_providers.openshell_chatgpt.wire_api": "responses",
}
assert "CODEX_AUTH_JSON" in transport["forbidden_environment"]
assert "~/.codex/auth.json" in "\n".join(transport["external_requirements"])
PY

FAKE_BIN="${SCRATCH}/bin"
mkdir -p "${FAKE_BIN}"
cat > "${FAKE_BIN}/openshell" <<'SH'
#!/bin/sh
set -eu
printf '%s\n' "$@" > "${TMPDIR}/argv"
env | LC_ALL=C sort > "${TMPDIR}/environment"
printf 'provider created; access=%s\n' "${CODEX_AUTH_ACCESS_TOKEN}" >&2
SH
chmod +x "${FAKE_BIN}/openshell"

AUTH="${SCRATCH}/auth.json"
cat > "${AUTH}" <<'JSON'
{
  "auth_mode": "chatgpt",
  "tokens": {
    "access_token": "fixture-access-value",
    "refresh_token": "fixture-refresh-value",
    "account_id": "fixture-account-value",
    "id_token": "fixture-id-value"
  }
}
JSON
chmod 0600 "${AUTH}"

CAPTURE="${SCRATCH}/capture"
RECEIPT="${SCRATCH}/receipt.json"
mkdir -p "${CAPTURE}"
output="$(
  PATH="${FAKE_BIN}:/usr/bin:/bin" \
  TMPDIR="${CAPTURE}" \
  CLAUDE_CONFIG_DIR="/must/not/cross" \
  ANTHROPIC_API_KEY="must-not-cross" \
  python3 "${ROOT}/scripts/bootstrap-openshell-provider.py" codex-chatgpt \
    --name codex-runtime-env --auth-file "${AUTH}" \
    --openshell-bin "${FAKE_BIN}/openshell" --receipt "${RECEIPT}"
)"

for value in fixture-access-value fixture-refresh-value fixture-account-value fixture-id-value must-not-cross; do
  ! grep -Fq "${value}" <<< "${output}"
  ! grep -Fq "${value}" "${CAPTURE}/argv"
  ! grep -Fq "${value}" "${RECEIPT}"
done

grep -Fxq -- '--credential' "${CAPTURE}/argv"
grep -Fxq 'CODEX_AUTH_ACCESS_TOKEN' "${CAPTURE}/argv"
grep -Fxq 'CODEX_AUTH_REFRESH_TOKEN' "${CAPTURE}/argv"
grep -Fxq 'CODEX_AUTH_ACCOUNT_ID' "${CAPTURE}/argv"
grep -Fxq 'CODEX_AUTH_ID_TOKEN' "${CAPTURE}/argv"
grep -Fq 'CODEX_AUTH_ACCESS_TOKEN=fixture-access-value' "${CAPTURE}/environment"
! grep -Fq 'CLAUDE_CONFIG_DIR=' "${CAPTURE}/environment"
! grep -Fq 'ANTHROPIC_API_KEY=' "${CAPTURE}/environment"

python3 - "${RECEIPT}" <<'PY'
import json
import os
import sys

path = sys.argv[1]
document = json.load(open(path, encoding="utf-8"))
assert document["schema"] == "runtime-env/openshell-provider-receipt/v1"
assert document["carrier"] == "codex-chatgpt"
assert document["provider"] == "codex-runtime-env"
assert document["status"] == "created"
assert document["credential_components"] == 4
assert os.stat(path).st_mode & 0o777 == 0o600
PY

chmod 0644 "${AUTH}"
set +e
unsafe_output="$(python3 "${ROOT}/scripts/bootstrap-openshell-provider.py" codex-chatgpt \
  --name refused --auth-file "${AUTH}" --openshell-bin "${FAKE_BIN}/openshell" \
  --receipt "${SCRATCH}/unsafe.json" 2>&1)"
unsafe_status=$?
set -e
[[ ${unsafe_status} -eq 2 && "${unsafe_output}" == *'mode 0600'* ]]

chmod 0600 "${AUTH}"
ln -s "${AUTH}" "${SCRATCH}/auth-link.json"
set +e
link_output="$(python3 "${ROOT}/scripts/bootstrap-openshell-provider.py" codex-chatgpt \
  --name refused --auth-file "${SCRATCH}/auth-link.json" \
  --openshell-bin "${FAKE_BIN}/openshell" --receipt "${SCRATCH}/link.json" 2>&1)"
link_status=$?
set -e
[[ ${link_status} -eq 2 && "${link_output}" == *'symlink'* ]]

echo 'PASS: OpenShell Codex bootstrap keeps OAuth components out of argv and cross-carrier state'
