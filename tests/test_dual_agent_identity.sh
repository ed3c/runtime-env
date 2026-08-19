#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "${ROOT}/scripts/dual_agent_identity.py" --selftest

python3 - "${ROOT}" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
module = json.loads((root/'modules/dual-agent-identity-binding.json').read_text())
profile = json.loads((root/'profiles/dual-agent-identity-hermetic.json').read_text())
workload = json.loads((root/'workloads/dual-agent-identity-selftest.json').read_text())
schema = json.loads((root/'contracts/dual-agent-identity/workload-identity-binding.v1.schema.json').read_text())
assert module['id'] == 'dual-agent-identity-binding'
assert profile['modules'] == ['dual-agent-identity-binding']
assert workload['profile'] == profile['id']
assert workload['entrypoints'] == {
    'identity-contract': ['python3', '@runtime-env/scripts/dual_agent_identity.py', '--selftest']
}
assert workload['entrypoint_environment'] == {'identity-contract': []}
assert workload['secret_delivery'] == 'none'
assert workload['agent_secret_access'] == 'denied'
assert schema['$schema'] == 'https://json-schema.org/draft/2020-12/schema'
assert schema['additionalProperties'] is False
print('PASS: Dual-Agent identity module/profile/fixed-workload binding')
PY
