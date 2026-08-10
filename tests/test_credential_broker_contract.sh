#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOC="${ROOT}/docs/local-credential-broker.md"

for required in \
  'There is no absolute secrecy' \
  'Never add a generic `run -- <arbitrary command>`' \
  '`broker-only`' \
  'admitted receipt' \
  'gemini-3.6-flash-high' \
  'planted defect going red' \
  'Secure MCP Tunnel'; do
  grep -Fq "${required}" "${DOC}" || {
    echo "FAIL: credential broker contract omitted ${required}" >&2
    exit 1
  }
done

grep -Fq 'docs/local-credential-broker.md' "${ROOT}/README.md"

echo 'PASS: local credential broker has fail-closed boundaries'
