#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "${ROOT}/scripts/dual_agent_transport.py" --selftest
python3 "${ROOT}/scripts/dual_agent_transport.py" --replay-selftest

python3 - "${ROOT}" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
module = json.loads((root / "modules/dual-agent-transport-local.json").read_text(encoding="utf-8"))
profile = json.loads((root / "profiles/dual-agent-transport-local.json").read_text(encoding="utf-8"))
workload = json.loads((root / "workloads/dual-agent-transport-selftest.json").read_text(encoding="utf-8"))

assert module == {
    "schema": "runtime-env/module/v1",
    "id": "dual-agent-transport-local",
    "summary": module["summary"],
    "requires": [],
    "optional": [],
    "defaults": {},
}
assert profile["schema"] == "runtime-env/profile/v1"
assert profile["id"] == "dual-agent-transport-local"
assert profile["modules"] == ["dual-agent-transport-local"]
assert workload["schema"] == "runtime-env/workload/v2"
assert workload["profile"] == profile["id"]
assert workload["entrypoints"] == {
    "transport-contract": [
        "python3",
        "@runtime-env/scripts/dual_agent_transport.py",
        "--selftest",
    ],
    "transport-replay": [
        "python3",
        "@runtime-env/scripts/dual_agent_transport.py",
        "--replay-selftest",
    ],
}
assert workload["acceptance_entrypoints"] == ["transport-contract", "transport-replay"]
assert workload["entrypoint_environment"] == {
    "transport-contract": [],
    "transport-replay": [],
}
assert workload["secret_delivery"] == "none"
assert workload["agent_secret_access"] == "denied"
assert workload["mutation"] == "read-only"
print("PASS: Dual-Agent transport module/profile/fixed-workload replay binding")
PY
