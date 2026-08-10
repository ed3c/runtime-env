#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "${SCRATCH}"' EXIT

"${ROOT}/runtime-env" validate >/dev/null

python3 - "${ROOT}" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
sys.path.insert(0, str(root / "src"))
from runtime_env.cli import ContractError, _resolve_workload_command, load_catalog

module = json.loads((root / "modules/forgejo-local-keychain-helper.json").read_text())
assert module["requires"] == []
assert module["optional"] == []
assert module["defaults"] == {}

profile = json.loads((root / "profiles/forgejo-delivery-keychain-local.json").read_text())
assert profile["modules"] == ["forgejo-local-keychain-helper"]

workload = json.loads((root / "workloads/forgejo-delivery-loop.json").read_text())
assert workload["profile"] == "forgejo-delivery-keychain-local"
assert workload["secret_delivery"] == "none"
assert workload["agent_secret_access"] == "denied"
assert workload["mutation"] == "read-only"
assert workload["entrypoints"] == {
    "broker-selftest": ["@runtime-env/runtime-env", "validate"],
    "credential-canary": [
        "/bin/bash",
        "@runtime-env/scripts/verify-local-runtime.sh",
        "--credential-helper-only",
    ],
}
assert workload["entrypoint_environment"] == {
    "broker-selftest": [],
    "credential-canary": [],
}
assert workload["clean_catalog_entrypoints"] == ["credential-canary"]

bettor_profile = json.loads((root / "profiles/bettor-arena-runtime-local.json").read_text())
assert "forgejo-local-keychain-helper" in bettor_profile["modules"]
bettor_workload = json.loads((root / "workloads/bettor-arena-proof.json").read_text())
assert bettor_workload["entrypoints"]["forgejo-credential-canary"] == [
    "/bin/bash",
    "@runtime-env/scripts/verify-local-runtime.sh",
    "--credential-helper-only",
]
assert bettor_workload["entrypoint_environment"]["forgejo-credential-canary"] == []
assert "forgejo-credential-canary" in bettor_workload["clean_catalog_entrypoints"]

try:
    _resolve_workload_command(load_catalog(root), ["@runtime-env/../outside"])
except ContractError as error:
    assert "unsafe path" in str(error)
else:
    raise AssertionError("runtime-env-owned command accepted path traversal")
PY

target="${SCRATCH}/target"
mkdir -p "${target}"
printf 'fixture\n' > "${target}/README.md"
git -C "${target}" init -q
git -C "${target}" config user.email runtime-env@test
git -C "${target}" config user.name runtime-env-test
git -C "${target}" add -A
git -C "${target}" commit -qm fixture

catalog_fixture="${SCRATCH}/catalog-fixture"
mkdir -p "${catalog_fixture}"
printf 'trusted\n' > "${catalog_fixture}/broker"
git -C "${catalog_fixture}" init -q
git -C "${catalog_fixture}" config user.email runtime-env@test
git -C "${catalog_fixture}" config user.name runtime-env-test
git -C "${catalog_fixture}" add -A
git -C "${catalog_fixture}" commit -qm fixture
printf 'dirty\n' >> "${catalog_fixture}/broker"

PYTHONPATH="${ROOT}/src" python3 - "${catalog_fixture}" <<'PY'
import sys
from pathlib import Path

from runtime_env.cli import Catalog, ContractError, _require_clean_catalog

catalog = Catalog({}, {}, {}, {}, {}, root=Path(sys.argv[1]))
try:
    _require_clean_catalog(catalog)
except ContractError as error:
    assert "requires a clean runtime-env catalog" in str(error)
else:
    raise AssertionError("credential broker accepted a dirty catalog root")
PY

receipt="${SCRATCH}/receipts/forgejo-selftest.json"
output="$("${ROOT}/runtime-env" workload run \
  --id forgejo-delivery-loop \
  --entrypoint broker-selftest \
  --target-root "${target}" \
  --receipt "${receipt}" \
  --json)"

[[ "${output}" != *'OK catalog:'* ]]
python3 - "${receipt}" <<'PY'
import json
import os
import sys

receipt = json.load(open(sys.argv[1], encoding="utf-8"))
assert receipt["status"] == "passed"
assert receipt["environment"] == {
    "configured_names": [],
    "delivery": "none",
    "secret_names": [],
}
assert receipt["stdout"]["bytes"] > 0
assert receipt["runtime_source"]["head"]
assert isinstance(receipt["runtime_source"]["dirty"], bool)
assert os.stat(sys.argv[1]).st_mode & 0o777 == 0o600
PY

echo 'PASS: Forgejo delivery uses the Keychain-backed Git helper without dotenv injection'
