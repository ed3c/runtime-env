#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "${SCRATCH}"' EXIT

CATALOG="${SCRATCH}/catalog"
TARGET="${SCRATCH}/target"
mkdir -p "${CATALOG}"/{catalog,modules,profiles,workloads} "${TARGET}/scripts"

printf '%s\n' \
  '{"schema":"runtime-env/variables/v1","variables":[' \
  '{"name":"RUNTIME_SENTINEL","secret":false,"runtime_scope":"portable","description":"Non-secret runner test value."},' \
  '{"name":"UNRELATED_CONFIG","secret":false,"runtime_scope":"local-only","description":"A second carrier value that this entrypoint must not inherit."},' \
  '{"name":"BROKER_SECRET","secret":true,"runtime_scope":"cloud-runtime","description":"Secret that none-delivery must refuse."}' \
  ']}' > "${CATALOG}/catalog/variables.json"
printf '%s\n' \
  '{"schema":"runtime-env/module/v1","id":"runner","summary":"Runner fixture.","requires":[],"optional":["RUNTIME_SENTINEL","UNRELATED_CONFIG"],"defaults":{"RUNTIME_SENTINEL":"catalog-default"}}' \
  > "${CATALOG}/modules/runner.json"
printf '%s\n' \
  '{"schema":"runtime-env/module/v1","id":"secret","summary":"Secret fixture.","requires":["BROKER_SECRET"],"optional":[],"defaults":{}}' \
  > "${CATALOG}/modules/secret.json"
printf '%s\n' \
  '{"schema":"runtime-env/profile/v1","id":"runner","summary":"Runner fixture.","modules":["runner"]}' \
  > "${CATALOG}/profiles/runner.json"
printf '%s\n' \
  '{"schema":"runtime-env/profile/v1","id":"secret","summary":"Secret fixture.","modules":["secret"]}' \
  > "${CATALOG}/profiles/secret.json"
printf '%s\n' \
  '{"schema":"runtime-env/workload/v2","id":"runner","summary":"Runner fixture.","profile":"runner","host":"local-macos","entrypoints":{"fixed":["sh","scripts/fixed.sh"],"placeholder":["sh","<script>"],"trusted":["@runtime-env/trusted.sh"]},"acceptance_entrypoints":["fixed"],"entrypoint_environment":{"fixed":["RUNTIME_SENTINEL"],"placeholder":[],"trusted":[]},"clean_catalog_entrypoints":["trusted"],"secret_delivery":"none","agent_secret_access":"denied","mutation":"workspace","evidence":{"receipt":"artifact.txt","control":"scripts/fixed.sh"}}' \
  > "${CATALOG}/workloads/runner.json"
printf '%s\n' \
  '{"schema":"runtime-env/workload/v2","id":"secret","summary":"Secret fixture.","profile":"secret","host":"local-macos","entrypoints":{"fixed":["sh","scripts/fixed.sh"]},"acceptance_entrypoints":["fixed"],"entrypoint_environment":{"fixed":["BROKER_SECRET"]},"secret_delivery":"none","agent_secret_access":"denied","mutation":"workspace","evidence":{"receipt":"artifact.txt","control":"scripts/fixed.sh"}}' \
  > "${CATALOG}/workloads/secret.json"
printf '%s\n' \
  '{"schema":"runtime-env/workload/v2","id":"read-only","summary":"Read-only enforcement fixture.","profile":"runner","host":"local-macos","entrypoints":{"mutates":["sh","scripts/mutates.sh"]},"acceptance_entrypoints":["mutates"],"entrypoint_environment":{"mutates":[]},"secret_delivery":"none","agent_secret_access":"denied","mutation":"read-only","evidence":{"receipt":"must-not-write.txt","control":"scripts/mutates.sh"}}' \
  > "${CATALOG}/workloads/read-only.json"
printf '%s\n' \
  '{"schema":"runtime-env/workload/v2","id":"broker","summary":"Broker adapter fixture.","profile":"secret","host":"local-macos","entrypoints":{"adapter":["sh","scripts/broker.sh"],"untrusted":["sh","scripts/broker.sh"]},"acceptance_entrypoints":["adapter"],"entrypoint_environment":{"adapter":["BROKER_SECRET"],"untrusted":["BROKER_SECRET"]},"broker_adapters":{"adapter":{"implementation":"scripts/broker.sh","private_state":["test-only private dotenv"],"receipt":"hashed execution receipt"}},"secret_delivery":"broker-only","agent_secret_access":"denied","mutation":"read-only","evidence":{"receipt":"hashed execution receipt","control":"scripts/broker.sh"}}' \
  > "${CATALOG}/workloads/broker.json"

printf '%s\n' '#!/bin/sh' 'printf "%s\n" "${RUNTIME_SENTINEL:-missing}" > artifact.txt' '[ -z "${UNRELATED_CONFIG+x}" ]' 'printf "runner emitted ordinary output\n"' \
  > "${TARGET}/scripts/fixed.sh"
chmod +x "${TARGET}/scripts/fixed.sh"
printf '%s\n' '#!/bin/sh' 'printf "unexpected write\n" > must-not-write.txt' \
  > "${TARGET}/scripts/mutates.sh"
chmod +x "${TARGET}/scripts/mutates.sh"
printf '%s\n' '#!/bin/sh' 'test "${BROKER_SECRET}" = broker-value' 'printf "%s\n" "${BROKER_SECRET}"' \
  > "${TARGET}/scripts/broker.sh"
chmod +x "${TARGET}/scripts/broker.sh"
printf '%s\n' '#!/bin/sh' 'test "${PATH}" = "/usr/bin:/bin:/usr/sbin:/sbin"' \
  > "${CATALOG}/trusted.sh"
chmod +x "${CATALOG}/trusted.sh"
git -C "${CATALOG}" init -q
git -C "${CATALOG}" config user.email runtime-env@test
git -C "${CATALOG}" config user.name runtime-env-test
git -C "${CATALOG}" add -A
git -C "${CATALOG}" commit -qm fixture
git -C "${TARGET}" init -q
git -C "${TARGET}" config user.email runtime-env@test
git -C "${TARGET}" config user.name runtime-env-test
git -C "${TARGET}" add -A
git -C "${TARGET}" commit -qm fixture

ENV_FILE="${SCRATCH}/runtime.env"
printf '%s\n' 'RUNTIME_SENTINEL=broker-value' 'UNRELATED_CONFIG=must-not-cross-carriers' > "${ENV_FILE}"
chmod 0600 "${ENV_FILE}"

output="$(${ROOT}/runtime-env --catalog-root "${CATALOG}" workload run \
  --id runner --entrypoint fixed --target-root "${TARGET}" --env-file "${ENV_FILE}" \
  --receipt "${SCRATCH}/receipts/fixed.json" --json)"
[[ "${output}" != *'broker-value'* && "${output}" != *'runner emitted ordinary output'* ]] || {
  echo 'FAIL: workload runner leaked dotenv or child stdout' >&2
  exit 1
}
python3 -c '
import json, os, sys
d=json.load(sys.stdin)
assert d["schema"] == "runtime-env/execution-receipt/v1"
assert d["status"] == "passed" and d["child_exit"] == 0
assert d["workload"] == "runner" and d["entrypoint"] == "fixed"
assert d["stdout"]["bytes"] > 0 and len(d["stdout"]["sha256"]) == 64
assert d["stderr"]["bytes"] == 0 and len(d["stderr"]["sha256"]) == 64
assert os.stat(d["receipt_path"]).st_mode & 0o777 == 0o600
assert d["receipt_path"].endswith("/receipts/fixed.json")
' <<< "${output}"
[[ "$(cat "${TARGET}/artifact.txt")" == 'broker-value' ]]

PATH="${TARGET}:${PATH}" ${ROOT}/runtime-env --catalog-root "${CATALOG}" workload run \
  --id runner --entrypoint trusted --target-root "${TARGET}" --json >/dev/null

set +e
readonly_output="$(${ROOT}/runtime-env --catalog-root "${CATALOG}" workload run \
  --id read-only --entrypoint mutates --target-root "${TARGET}" \
  --receipt "${SCRATCH}/receipts/read-only.json" --json 2>&1)"
readonly_status=$?
set -e
[[ ${readonly_status} -eq 2 ]]
python3 - "${SCRATCH}/receipts/read-only.json" <<'PY'
import json
import sys

receipt = json.load(open(sys.argv[1], encoding="utf-8"))
assert receipt["status"] == "failed"
assert receipt["child_exit"] == 0
assert receipt["policy"]["read_only_unchanged"] is False
PY
rm -f "${TARGET}/must-not-write.txt"

set +e
collision_output="$(${ROOT}/runtime-env --catalog-root "${CATALOG}" workload run \
  --id runner --entrypoint fixed --target-root "${TARGET}" --env-file "${ENV_FILE}" \
  --receipt "${SCRATCH}/receipts/fixed.json" --json 2>&1)"
collision_status=$?
set -e
[[ ${collision_status} -eq 2 && "${collision_output}" == *'already exists'* ]] || {
  echo 'FAIL: explicit receipt path was overwritten' >&2
  exit 1
}

printf '%s\n' 'RUNTIME_SENTINEL=' 'UNRELATED_CONFIG=must-not-cross-carriers' > "${ENV_FILE}"
${ROOT}/runtime-env --catalog-root "${CATALOG}" workload run \
  --id runner --entrypoint fixed --target-root "${TARGET}" --env-file "${ENV_FILE}" --json >/dev/null
[[ "$(cat "${TARGET}/artifact.txt")" == 'catalog-default' ]]
printf '%s\n' 'RUNTIME_SENTINEL=broker-value' 'UNRELATED_CONFIG=must-not-cross-carriers' > "${ENV_FILE}"

set +e
placeholder_output="$(${ROOT}/runtime-env --catalog-root "${CATALOG}" workload run \
  --id runner --entrypoint placeholder --target-root "${TARGET}" --env-file "${ENV_FILE}" --json 2>&1)"
placeholder_status=$?
set -e
[[ ${placeholder_status} -eq 2 && "${placeholder_output}" == *'unresolved placeholder'* ]] || {
  echo 'FAIL: unresolved workload placeholder was not refused' >&2
  exit 1
}

SECRET_FILE="${SCRATCH}/secret.env"
printf '%s\n' 'BROKER_SECRET=must-not-reach-child' > "${SECRET_FILE}"
chmod 0600 "${SECRET_FILE}"
set +e
secret_output="$(${ROOT}/runtime-env --catalog-root "${CATALOG}" workload run \
  --id secret --entrypoint fixed --target-root "${TARGET}" --env-file "${SECRET_FILE}" --json 2>&1)"
secret_status=$?
set -e
[[ ${secret_status} -eq 2 && "${secret_output}" == *'secret_delivery=none'* && "${secret_output}" != *'must-not-reach-child'* ]] || {
  echo 'FAIL: none-delivery workload did not refuse configured secret' >&2
  exit 1
}

BROKER_FILE="${SCRATCH}/broker.env"
printf '%s\n' 'BROKER_SECRET=broker-value' > "${BROKER_FILE}"
chmod 0600 "${BROKER_FILE}"
rm -f "${TARGET}/artifact.txt"
broker_output="$(${ROOT}/runtime-env --catalog-root "${CATALOG}" workload run \
  --id broker --entrypoint adapter --target-root "${TARGET}" --env-file "${BROKER_FILE}" \
  --receipt "${SCRATCH}/receipts/broker.json" --json)"
[[ "${broker_output}" != *'broker-value'* ]]
python3 -c '
import json, sys
d=json.load(sys.stdin)
assert d["status"] == "passed"
assert d["environment"]["secret_names"] == ["BROKER_SECRET"]
assert d["broker_adapter"]["implementation"] == "scripts/broker.sh"
assert d["stdout"]["bytes"] > 0
' <<< "${broker_output}"

printf '%s\n' '# uncommitted broker mutation' >> "${TARGET}/scripts/broker.sh"
set +e
dirty_broker_output="$(${ROOT}/runtime-env --catalog-root "${CATALOG}" workload run \
  --id broker --entrypoint adapter --target-root "${TARGET}" \
  --env-file "${BROKER_FILE}" --json 2>&1)"
dirty_broker_status=$?
set -e
[[ ${dirty_broker_status} -eq 2 && "${dirty_broker_output}" == *'broker adapter requires a clean target repository'* ]]
git -C "${TARGET}" restore scripts/broker.sh

set +e
untrusted_output="$(${ROOT}/runtime-env --catalog-root "${CATALOG}" workload run \
  --id broker --entrypoint untrusted --target-root "${TARGET}" \
  --env-file "${BROKER_FILE}" --json 2>&1)"
untrusted_status=$?
set -e
[[ ${untrusted_status} -eq 2 && "${untrusted_output}" == *'has no dedicated broker adapter'* ]]

set +e
missing_output="$(${ROOT}/runtime-env --catalog-root "${CATALOG}" workload run \
  --id secret --entrypoint fixed --target-root "${TARGET}" --json 2>&1)"
missing_status=$?
set -e
[[ ${missing_status} -eq 3 && "${missing_output}" == *'missing required workload variables: BROKER_SECRET'* ]] || {
  echo 'FAIL: missing required workload configuration did not use exit 3' >&2
  exit 1
}

chmod 0644 "${ENV_FILE}"
set +e
mode_output="$(${ROOT}/runtime-env --catalog-root "${CATALOG}" workload run \
  --id runner --entrypoint fixed --target-root "${TARGET}" --env-file "${ENV_FILE}" --json 2>&1)"
mode_status=$?
set -e
[[ ${mode_status} -eq 2 && "${mode_output}" == *'mode 0600'* ]] || {
  echo 'FAIL: workload runner accepted an unsafe dotenv mode' >&2
  exit 1
}

echo 'PASS: fixed workload runner keeps dotenv and child streams behind metadata receipts'
