#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "${SCRATCH}"' EXIT

CATALOG="${SCRATCH}/catalog"
TARGET="${SCRATCH}/consumer"
RECEIPTS="${SCRATCH}/receipts"
LIVE_RUN_LOG="${SCRATCH}/live-canary.log"
mkdir -p "${CATALOG}"/{catalog,modules,profiles,workloads} \
  "${TARGET}/scripts" "${TARGET}/.githooks" "${RECEIPTS}" "${SCRATCH}/bin"
chmod 0700 "${RECEIPTS}"
printf '%s\n' '#!/bin/sh' "exec '${ROOT}/runtime-env' --catalog-root '${CATALOG}' \"\$@\"" \
  > "${SCRATCH}/bin/runtime-env"
chmod +x "${SCRATCH}/bin/runtime-env"
export PATH="${SCRATCH}/bin:${PATH}"

printf '%s\n' \
  '{"schema":"runtime-env/variables/v1","variables":[{"name":"FIXTURE_NAME","secret":false,"runtime_scope":"portable","description":"Fixture selector."}]}' \
  > "${CATALOG}/catalog/variables.json"
printf '%s\n' \
  '{"schema":"runtime-env/module/v1","id":"fixture","summary":"Fixture module.","requires":[],"optional":["FIXTURE_NAME"],"defaults":{"FIXTURE_NAME":"accepted"}}' \
  > "${CATALOG}/modules/fixture.json"
printf '%s\n' \
  '{"schema":"runtime-env/profile/v1","id":"fixture","summary":"Fixture profile.","modules":["fixture"]}' \
  > "${CATALOG}/profiles/fixture.json"
printf '%s\n' \
  '{"schema":"runtime-env/workload/v2","id":"fixture","summary":"Fixture consumer acceptance.","profile":"fixture","host":"local-macos","entrypoints":{"public-test":["sh","scripts/public-test.sh"],"live-canary":["sh","scripts/live-canary.sh"]},"acceptance_entrypoints":["public-test","live-canary"],"public_test_entrypoints":["public-test"],"entrypoint_environment":{"public-test":[],"live-canary":["FIXTURE_NAME"]},"secret_delivery":"none","agent_secret_access":"denied","mutation":"read-only","evidence":{"receipt":"private acceptance receipt","control":"scripts/public-test.sh"}}' \
  > "${CATALOG}/workloads/fixture.json"
printf '%s\n' '#!/bin/sh' 'test -f .runtime-env/bindings/fixture.json' \
  > "${TARGET}/scripts/public-test.sh"
printf '%s\n' '#!/bin/sh' "printf '%s\\n' run >> '${LIVE_RUN_LOG}'" \
  'test "${FIXTURE_NAME}" = accepted' \
  > "${TARGET}/scripts/live-canary.sh"
chmod +x "${TARGET}/scripts/public-test.sh" "${TARGET}/scripts/live-canary.sh"
printf '%s\n' '#!/bin/sh' 'set -eu' 'sh scripts/check-runtime-env-consumer.sh --staged' \
  > "${TARGET}/.githooks/pre-commit"
printf '%s\n' '#!/bin/sh' 'set -eu' 'runtime-env verify-consumer --target-root "$(git rev-parse --show-toplevel)" --binding fixture "$@"' \
  > "${TARGET}/scripts/check-runtime-env-consumer.sh"
chmod +x "${TARGET}/.githooks/pre-commit" "${TARGET}/scripts/check-runtime-env-consumer.sh"

git -C "${CATALOG}" init -q
git -C "${CATALOG}" config user.email runtime-env@test
git -C "${CATALOG}" config user.name runtime-env-test
git -C "${CATALOG}" add -A
git -C "${CATALOG}" commit -qm 'fixture catalog'
git -C "${CATALOG}" remote add origin git@github.com:ed3c/runtime-env.git
git -C "${TARGET}" init -q
git -C "${TARGET}" config user.email consumer@test
git -C "${TARGET}" config user.name consumer-test
git -C "${TARGET}" add -A
git -C "${TARGET}" commit -qm 'fixture consumer'

"${ROOT}/runtime-env" --catalog-root "${CATALOG}" sync \
  --profile fixture --binding fixture --workload fixture \
  --target-root "${TARGET}" --apply >/dev/null
git -C "${TARGET}" add .runtime-env
git -C "${TARGET}" commit -qm 'bind runtime contract'
git -C "${TARGET}" config core.hooksPath .githooks

output="$("${ROOT}/runtime-env" --catalog-root "${CATALOG}" accept-consumer \
  --target-root "${TARGET}" --binding fixture \
  --hook-verifier scripts/check-runtime-env-consumer.sh \
  --receipt "${RECEIPTS}/acceptance.json" --json)"

python3 -c '
import json, os, sys
d=json.load(sys.stdin)
assert d["schema"] == "runtime-env/consumer-acceptance-receipt/v1"
assert d["status"] == "passed"
assert d["maturity"] == "L5"
assert d["binding"] == "fixture"
assert d["projection_checks"] == {"staged": "passed", "worktree": "passed"}
assert d["hook_gate"]["status"] == "passed"
assert d["hook_gate"]["hooks_path"] == ".githooks"
assert d["hook_gate"]["verifier_execution"]["exit_code"] == 0
assert len(d["hook_gate"]["verifier_execution"]["stdout_sha256"]) == 64
assert d["target"]["dirty_before"] is False
assert d["target"]["dirty_after"] is False
assert d["target"]["head_before"] == d["target"]["head_after"]
assert [item["entrypoint"] for item in d["executions"]] == ["public-test", "live-canary"]
assert all(item["status"] == "passed" for item in d["executions"])
assert all(len(item["receipt_sha256"]) == 64 for item in d["executions"])
assert os.stat(d["receipt_path"]).st_mode & 0o777 == 0o600
' <<< "${output}"

[[ -f "${RECEIPTS}/acceptance.d/public-test.json" ]]
[[ -f "${RECEIPTS}/acceptance.d/live-canary.json" ]]
[[ -z "$(git -C "${TARGET}" status --porcelain=v1)" ]]
[[ "$(wc -l < "${LIVE_RUN_LOG}" | tr -d ' ')" == 1 ]]

"${ROOT}/runtime-env" --catalog-root "${CATALOG}" workload run \
  --id fixture --entrypoint live-canary --target-root "${TARGET}" \
  --receipt "${RECEIPTS}/standalone-live.json" --json >/dev/null
[[ "$(wc -l < "${LIVE_RUN_LOG}" | tr -d ' ')" == 2 ]]

reuse_output="$("${ROOT}/runtime-env" --catalog-root "${CATALOG}" accept-consumer \
  --target-root "${TARGET}" --binding fixture \
  --hook-verifier scripts/check-runtime-env-consumer.sh \
  --execution-receipt "live-canary=${RECEIPTS}/standalone-live.json" \
  --receipt "${RECEIPTS}/reuse.json" --json)"
python3 -c '
import json, sys
d=json.load(sys.stdin)
assert d["status"] == "passed" and d["maturity"] == "L5"
assert [item["evidence_source"] for item in d["executions"]] == ["executed", "reused"]
assert d["executions"][1]["entrypoint"] == "live-canary"
' <<< "${reuse_output}"
[[ -f "${RECEIPTS}/reuse.d/public-test.json" ]]
[[ ! -e "${RECEIPTS}/reuse.d/live-canary.json" ]]
[[ "$(wc -l < "${LIVE_RUN_LOG}" | tr -d ' ')" == 2 ]]

jq '.entrypoint = "public-test"' "${RECEIPTS}/standalone-live.json" \
  > "${RECEIPTS}/wrong-entrypoint.json"
chmod 0600 "${RECEIPTS}/wrong-entrypoint.json"
set +e
wrong_entrypoint_output="$("${ROOT}/runtime-env" --catalog-root "${CATALOG}" accept-consumer \
  --target-root "${TARGET}" --binding fixture \
  --hook-verifier scripts/check-runtime-env-consumer.sh \
  --execution-receipt "live-canary=${RECEIPTS}/wrong-entrypoint.json" \
  --receipt "${RECEIPTS}/wrong-entrypoint-acceptance.json" --json 2>&1)"
wrong_entrypoint_status=$?
set -e
[[ ${wrong_entrypoint_status} -eq 2 ]]
[[ "${wrong_entrypoint_output}" == *'execution receipt entrypoint mismatch'* ]]
[[ "$(wc -l < "${LIVE_RUN_LOG}" | tr -d ' ')" == 2 ]]

BAD_ENV="${SCRATCH}/bad.env"
printf '%s\n' 'FIXTURE_NAME=rejected' > "${BAD_ENV}"
chmod 0600 "${BAD_ENV}"
set +e
failed_output="$("${ROOT}/runtime-env" --catalog-root "${CATALOG}" accept-consumer \
  --target-root "${TARGET}" --binding fixture --env-file "${BAD_ENV}" \
  --hook-verifier scripts/check-runtime-env-consumer.sh \
  --receipt "${RECEIPTS}/failed.json" --json)"
failed_status=$?
set -e
[[ ${failed_status} -eq 2 ]]
python3 -c '
import json, sys
d=json.load(sys.stdin)
assert d["status"] == "failed" and d["maturity"] == "below-L5"
assert [item["status"] for item in d["executions"]] == ["passed", "failed"]
assert d["target"]["dirty_after"] is False
' <<< "${failed_output}"

printf '%s\n' dirty > "${TARGET}/untracked.txt"
set +e
dirty_output="$("${ROOT}/runtime-env" --catalog-root "${CATALOG}" accept-consumer \
  --target-root "${TARGET}" --binding fixture \
  --hook-verifier scripts/check-runtime-env-consumer.sh \
  --receipt "${RECEIPTS}/dirty.json" --json 2>&1)"
dirty_status=$?
set -e
[[ ${dirty_status} -eq 2 && "${dirty_output}" == *'requires a clean target checkout'* ]]
rm "${TARGET}/untracked.txt"

printf '%s\n' '#!/bin/sh' '# runtime-env verify-consumer --binding fixture' 'exit 0' \
  > "${TARGET}/scripts/check-runtime-env-consumer.sh"
chmod +x "${TARGET}/scripts/check-runtime-env-consumer.sh"
git -C "${TARGET}" add scripts/check-runtime-env-consumer.sh
git -C "${TARGET}" commit -qm 'plant comment-only verifier'
set +e
comment_gate_output="$("${ROOT}/runtime-env" --catalog-root "${CATALOG}" accept-consumer \
  --target-root "${TARGET}" --binding fixture \
  --hook-verifier scripts/check-runtime-env-consumer.sh \
  --receipt "${RECEIPTS}/comment-gate.json" --json 2>&1)"
comment_gate_status=$?
set -e
[[ ${comment_gate_status} -eq 2 && "${comment_gate_output}" == *'executable verifier line'* ]]

printf '%s\n' '#!/bin/sh' 'set -eu' 'runtime-env verify-consumer --target-root "$(git rev-parse --show-toplevel)" --binding fixture "$@"' \
  > "${TARGET}/scripts/check-runtime-env-consumer.sh"
printf '%s\n' 'ignored-state' > "${TARGET}/.gitignore"
printf '%s\n' 'stable' > "${TARGET}/ignored-state"
printf '%s\n' '#!/bin/sh' 'printf "%s\n" changed > ignored-state' 'test "${FIXTURE_NAME}" = accepted' \
  > "${TARGET}/scripts/live-canary.sh"
chmod +x "${TARGET}/scripts/check-runtime-env-consumer.sh" "${TARGET}/scripts/live-canary.sh"
git -C "${TARGET}" add .gitignore scripts/check-runtime-env-consumer.sh scripts/live-canary.sh
git -C "${TARGET}" commit -qm 'plant ignored mutation control'
set +e
ignored_output="$("${ROOT}/runtime-env" --catalog-root "${CATALOG}" accept-consumer \
  --target-root "${TARGET}" --binding fixture \
  --hook-verifier scripts/check-runtime-env-consumer.sh \
  --receipt "${RECEIPTS}/ignored-mutation.json" --json)"
ignored_status=$?
set -e
[[ ${ignored_status} -eq 2 ]]
python3 -c '
import json, sys
d=json.load(sys.stdin)
assert d["status"] == "failed" and d["maturity"] == "below-L5"
assert d["target"]["ignored_changed_after"] is True
' <<< "${ignored_output}"
printf '%s\n' 'stable' > "${TARGET}/ignored-state"

python3 -c '
import json, pathlib
path = pathlib.Path("'"${CATALOG}"'/workloads/fixture.json")
document = json.loads(path.read_text())
document["mutation"] = "workspace"
path.write_text(json.dumps(document, sort_keys=True) + "\n")
'
git -C "${CATALOG}" add workloads/fixture.json
git -C "${CATALOG}" commit -qm 'declare workspace mutation fixture'
"${ROOT}/runtime-env" --catalog-root "${CATALOG}" sync \
  --profile fixture --binding fixture --workload fixture \
  --target-root "${TARGET}" --apply >/dev/null
git -C "${TARGET}" add .runtime-env
git -C "${TARGET}" commit -qm 'project workspace mutation contract'

workspace_output="$("${ROOT}/runtime-env" --catalog-root "${CATALOG}" accept-consumer \
  --target-root "${TARGET}" --binding fixture \
  --hook-verifier scripts/check-runtime-env-consumer.sh \
  --receipt "${RECEIPTS}/workspace-mutation.json" --json)"
python3 -c '
import json, sys
d=json.load(sys.stdin)
assert d["status"] == "passed" and d["maturity"] == "L5"
assert d["target"]["ignored_changed_after"] is True
assert d["target"]["ignored_change_permitted"] is True
assert d["target"]["mutation"] == "workspace"
' <<< "${workspace_output}"

printf '%s\n' advance > "${CATALOG}/catalog-advance.txt"
git -C "${CATALOG}" add catalog-advance.txt
git -C "${CATALOG}" commit -qm 'advance catalog fixture'
set +e
stale_output="$("${ROOT}/runtime-env" --catalog-root "${CATALOG}" accept-consumer \
  --target-root "${TARGET}" --binding fixture \
  --hook-verifier scripts/check-runtime-env-consumer.sh \
  --receipt "${RECEIPTS}/stale.json" --json 2>&1)"
stale_status=$?
set -e
[[ ${stale_status} -eq 2 && "${stale_output}" == *'catalog source does not match the consumer pin'* ]]

echo 'PASS: consolidated acceptance binds every live entrypoint to one clean consumer revision'
