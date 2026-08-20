#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for json_file in \
  "${ROOT}"/contracts/dual-agent/*.json \
  "${ROOT}"/examples/dual-agent/*.json \
  "${ROOT}"/tests/fixtures/dual-agent/*.json
do
  python3 -m json.tool "${json_file}" >/dev/null
done

python3 "${ROOT}/tests/dual_agent_contract_selftest.py"
echo "PASS: test_dual_agent_contract.sh"
