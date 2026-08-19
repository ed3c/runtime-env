#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "${ROOT}/scripts/dual_agent_nats_adapter.py" --selftest

python3 - "${ROOT}" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
module = json.loads((root/'modules/dual-agent-transport-nats.json').read_text())
profile = json.loads((root/'profiles/dual-agent-transport-nats-hermetic.json').read_text())
workload = json.loads((root/'workloads/dual-agent-transport-nats-selftest.json').read_text())
schema = json.loads((root/'contracts/dual-agent-transport/nats-jetstream-adapter.v1.schema.json').read_text())
assert module['id'] == 'dual-agent-transport-nats'
assert profile['modules'] == ['dual-agent-transport-local', 'dual-agent-transport-nats']
assert workload['profile'] == profile['id']
assert workload['entrypoints'] == {
    'nats-adapter-contract': ['python3', '@runtime-env/scripts/dual_agent_nats_adapter.py', '--selftest']
}
assert workload['acceptance_entrypoints'] == ['nats-adapter-contract']
assert workload['entrypoint_environment'] == {'nats-adapter-contract': []}
assert workload['secret_delivery'] == 'none'
assert workload['agent_secret_access'] == 'denied'
assert schema['$schema'] == 'https://json-schema.org/draft/2020-12/schema'
assert schema['additionalProperties'] is False
print('PASS: Dual-Agent NATS adapter module/profile/fixed-workload binding')
PY
