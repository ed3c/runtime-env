#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "${ROOT}/scripts/dual_agent_identity_local.py" --selftest
python3 - "${ROOT}" <<'PY'
import json,sys
from pathlib import Path
r=Path(sys.argv[1])
m=json.loads((r/'modules/dual-agent-identity-local-broker.json').read_text())
p=json.loads((r/'profiles/dual-agent-identity-local-broker-hermetic.json').read_text())
w=json.loads((r/'workloads/dual-agent-identity-local-broker-selftest.json').read_text())
assert p['modules']==['dual-agent-identity-binding','dual-agent-identity-local-broker']
assert w['profile']==p['id'] and w['secret_delivery']=='none' and w['agent_secret_access']=='denied'
assert m['id']=='dual-agent-identity-local-broker'
print('PASS: Dual-Agent LOCAL identity/broker fixed-workload binding')
PY
