#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOC="${ROOT}/docs/runtime-topology.md"

[[ -f "${DOC}" ]] || {
  echo "FAIL: runtime execution topology is absent" >&2
  exit 1
}

for required in \
  'GitHub app is a repository context plane, not a compute plane' \
  'Codex cloud creates a container' \
  'Secure MCP Tunnel' \
  'never expose a generic shell tool' \
  'self-hosted runners should almost never execute public pull-request code' \
  'https://learn.chatgpt.com/docs/environments/cloud-environment' \
  'https://developers.openai.com/api/docs/guides/secure-mcp-tunnels' \
  'https://docs.github.com/en/actions/reference/security/secure-use'; do
  grep -Fq "${required}" "${DOC}" || {
    echo "FAIL: runtime topology omitted ${required}" >&2
    exit 1
  }
done

grep -Fq 'docs/runtime-topology.md' "${ROOT}/README.md" || {
  echo "FAIL: README does not route readers to runtime topology" >&2
  exit 1
}

echo "PASS: runtime execution topology contract"
