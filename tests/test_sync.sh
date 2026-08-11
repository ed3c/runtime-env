#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT
source_repo="${scratch}/source"
target_repo="${scratch}/target"
mkdir -p "${source_repo}/catalog" "${source_repo}/modules" \
  "${source_repo}/profiles" "${source_repo}/workloads" "${source_repo}/policies" "${target_repo}"

file_sha256() {
  python3 - "$1" <<'PY'
import hashlib
from pathlib import Path
import sys

print(hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())
PY
}

printf '%s\n' \
  '{"schema":"runtime-env/variables/v1","variables":[{"name":"FIXTURE_HOME","secret":false,"runtime_scope":"local-only","description":"Fixture config root."},{"name":"OLLAMA_URL","secret":false,"runtime_scope":"local-only","description":"Ollama service root."}]}' \
  > "${source_repo}/catalog/variables.json"
printf '%s\n' \
  '{"schema":"runtime-env/module/v1","id":"ollama-root","summary":"Fixture.","requires":[],"optional":["OLLAMA_URL"],"defaults":{"OLLAMA_URL":"http://localhost:11434"}}' \
  > "${source_repo}/modules/ollama-root.json"
printf '%s\n' \
  '{"schema":"runtime-env/profile/v1","id":"bettor-arena-local","summary":"Fixture.","modules":["ollama-root"]}' \
  > "${source_repo}/profiles/bettor-arena-local.json"
printf '%s\n' \
  '{"schema":"runtime-env/workload/v1","id":"local-proof","summary":"Fixture.","profile":"bettor-arena-local","host":"local-macos","entrypoints":{"prove":["sh","proof.sh"]},"entrypoint_environment":{"prove":["OLLAMA_URL"]},"secret_delivery":"none","agent_secret_access":"denied","mutation":"workspace","evidence":{"receipt":"receipt.json","control":"control.sh"}}' \
  > "${source_repo}/workloads/local-proof.json"
printf '%s\n' \
  '{"schema":"runtime-env/carrier-policy/v1","id":"fixture-native","summary":"Fixture.","carrier":"codex-cli","config_home_env":"FIXTURE_HOME","settings_file":"config.toml","required_settings":{"sandbox_mode":"workspace-write"},"forbidden_environment":["FOREIGN_HOME"],"external_requirements":["deny read"],"receipt_commands":["fixture status"]}' \
  > "${source_repo}/policies/fixture-native.json"

git -C "${source_repo}" init -q
git -C "${source_repo}" config user.name fixture
git -C "${source_repo}" config user.email fixture@example.invalid
git -C "${source_repo}" add .
git -C "${source_repo}" commit -qm 'fixture source'
git -C "${source_repo}" remote add origin git@github.com:ed3c/runtime-env.git
git -C "${target_repo}" init -q

dry_output="$(${ROOT}/runtime-env --catalog-root "${source_repo}" sync \
  --profile bettor-arena-local --binding bettor-arena-local \
  --workload local-proof --policy fixture-native --target-root "${target_repo}")"
[[ "${dry_output}" == *'WOULD-CREATE .runtime-env/bindings/bettor-arena-local.json'* ]]
[[ "${dry_output}" == *'WOULD-CREATE .runtime-env/examples/bettor-arena-local.env.example'* ]]
[[ "${dry_output}" == *'WOULD-CREATE .runtime-env/workloads/bettor-arena-local.json'* ]]
[[ "${dry_output}" == *'WOULD-CREATE .runtime-env/policies/fixture-native.json'* ]]
[[ ! -e "${target_repo}/.runtime-env" ]] || {
  echo "FAIL: dry-run wrote target files" >&2
  exit 1
}

${ROOT}/runtime-env --catalog-root "${source_repo}" sync \
  --profile bettor-arena-local --binding bettor-arena-local \
  --workload local-proof --policy fixture-native --target-root "${target_repo}" --apply >/dev/null

binding="${target_repo}/.runtime-env/bindings/bettor-arena-local.json"
example="${target_repo}/.runtime-env/examples/bettor-arena-local.env.example"
workload="${target_repo}/.runtime-env/workloads/bettor-arena-local.json"
policy="${target_repo}/.runtime-env/policies/fixture-native.json"
[[ -f "${binding}" && -f "${example}" && -f "${workload}" && -f "${policy}" ]]
python3 - "${binding}" \
  "$(git -C "${source_repo}" rev-parse HEAD)" \
  "$(git -C "${source_repo}" rev-parse 'HEAD^{tree}')" <<'PY'
import json
from pathlib import Path
import sys

document = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert document["source"]["repository"] == "https://github.com/ed3c/runtime-env"
assert document["profile"] == "bettor-arena-local"
assert document["schema"] == "runtime-env/consumer-binding/v2"
assert document["modules"][0]["id"] == "ollama-root"
assert document["modules"][0]["interface_version"] == "runtime-env/module/v1"
assert document["source"]["commit"] == sys.argv[2]
assert document["source"]["tree"] == sys.argv[3]
assert document["variables"][0]["runtime_scope"] == "local-only"
PY

# Desired-state sync pins the exact module closure. A profile expansion must be
# admitted by changing requirements rather than arriving as an invisible update.
requirements="${target_repo}/.runtime-env/requirements.json"
printf '%s\n' '{"schema":"runtime-env/consumer-requirements/v1","binding":"bettor-arena-local","profile":"bettor-arena-local","required_modules":["ollama-root"],"workload":"local-proof","policies":["fixture-native"]}' > "${requirements}"
${ROOT}/runtime-env --catalog-root "${source_repo}" sync \
  --requirements "${requirements}" --target-root "${target_repo}" --apply >/dev/null
python3 - "${binding}" "${requirements}" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

binding = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert binding["requirements_sha256"] == hashlib.sha256(Path(sys.argv[2]).read_bytes()).hexdigest()
assert [module["id"] for module in binding["modules"]] == ["ollama-root"]
PY
python3 - "${workload}" <<'PY'
import json
from pathlib import Path
import sys

document = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert document["schema"] == "runtime-env/consumer-workload/v1"
assert document["binding"] == "bettor-arena-local"
assert document["workload"]["id"] == "local-proof"
assert document["workload"]["secret_delivery"] == "none"
PY
python3 - "${policy}" <<'PY'
import json
from pathlib import Path
import sys

document = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert document["schema"] == "runtime-env/consumer-policy/v1"
assert document["policy"]["id"] == "fixture-native"
assert document["policy"]["forbidden_environment"] == ["FOREIGN_HOME"]
PY
git -C "${target_repo}" add .runtime-env
${ROOT}/runtime-env --catalog-root "${scratch}/absent-catalog" verify-consumer \
  --target-root "${target_repo}" --binding bettor-arena-local --staged >/dev/null

python3 - "${binding}" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
document = json.loads(path.read_text(encoding="utf-8"))
del document["variables"][0]["runtime_scope"]
unsigned = dict(document)
del unsigned["content_sha256"]
canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
document["content_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
git -C "${target_repo}" add "${binding}"
set +e
scope_output="$(${ROOT}/runtime-env --catalog-root "${scratch}/absent-catalog" verify-consumer \
  --target-root "${target_repo}" --binding bettor-arena-local --staged 2>&1)"
scope_status=$?
set -e
[[ ${scope_status} -eq 2 && "${scope_output}" == *'invalid variable runtime_scope'* ]]
${ROOT}/runtime-env --catalog-root "${source_repo}" sync \
  --profile bettor-arena-local --binding bettor-arena-local \
  --workload local-proof --policy fixture-native --target-root "${target_repo}" --apply >/dev/null
git -C "${target_repo}" add .runtime-env

python3 - "${workload}" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
document = json.loads(path.read_text(encoding="utf-8"))
document["schema"] = "runtime-env/consumer-policy/v1"
unsigned = dict(document)
del unsigned["content_sha256"]
canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
document["content_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
git -C "${target_repo}" add "${workload}"
set +e
schema_output="$(${ROOT}/runtime-env --catalog-root "${scratch}/absent-catalog" verify-consumer \
  --target-root "${target_repo}" --binding bettor-arena-local --staged 2>&1)"
schema_status=$?
set -e
[[ ${schema_status} -eq 2 ]]
[[ "${schema_output}" == *'unexpected schema'* ]]
${ROOT}/runtime-env --catalog-root "${source_repo}" sync \
  --profile bettor-arena-local --binding bettor-arena-local \
  --workload local-proof --policy fixture-native --target-root "${target_repo}" --apply >/dev/null
git -C "${target_repo}" add .runtime-env

python3 - "${workload}" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
content = path.read_text(encoding="utf-8")
old = '"secret_delivery": "none"'
new = '"secret_delivery": "broker-only"'
assert content.count(old) == 1
path.write_text(content.replace(old, new), encoding="utf-8")
PY
git -C "${target_repo}" add "${workload}"
set +e
staged_output="$(${ROOT}/runtime-env --catalog-root "${scratch}/absent-catalog" verify-consumer \
  --target-root "${target_repo}" --binding bettor-arena-local --staged 2>&1)"
staged_status=$?
set -e
[[ ${staged_status} -eq 2 ]]
[[ "${staged_output}" == *'content_sha256 mismatch'* ]]
${ROOT}/runtime-env --catalog-root "${source_repo}" sync \
  --profile bettor-arena-local --binding bettor-arena-local \
  --workload local-proof --policy fixture-native --target-root "${target_repo}" --apply >/dev/null
git -C "${target_repo}" add .runtime-env
${ROOT}/runtime-env --catalog-root "${scratch}/absent-catalog" verify-consumer \
  --target-root "${target_repo}" --binding bettor-arena-local --staged >/dev/null
[[ "$(cat "${example}")" == $'# Generated by runtime-env. Values are placeholders, never credentials.\n# optional; non-secret: Ollama service root.\nOLLAMA_URL=http://localhost:11434' ]]
if grep -Fq "${scratch}" "${binding}" "${example}"; then
  echo "FAIL: synchronized artifacts contain a local absolute path" >&2
  exit 1
fi

${ROOT}/runtime-env --catalog-root "${source_repo}" sync \
  --profile bettor-arena-local --binding bettor-arena-local \
  --workload local-proof --policy fixture-native --target-root "${target_repo}" --check >/dev/null

printf '\n# local drift\n' >> "${example}"
before_check="$(file_sha256 "${example}")"
set +e
check_output="$(${ROOT}/runtime-env --catalog-root "${source_repo}" sync \
  --profile bettor-arena-local --binding bettor-arena-local \
  --workload local-proof --policy fixture-native --target-root "${target_repo}" --check 2>&1)"
check_status=$?
set -e
[[ ${check_status} -eq 2 ]]
[[ "${check_output}" == *'DRIFT .runtime-env/examples/bettor-arena-local.env.example'* ]]
[[ "$(file_sha256 "${example}")" == "${before_check}" ]] || {
  echo "FAIL: sync --check mutated a drifted artifact" >&2
  exit 1
}

${ROOT}/runtime-env --catalog-root "${source_repo}" sync \
  --profile bettor-arena-local --binding bettor-arena-local \
  --workload local-proof --policy fixture-native --target-root "${target_repo}" --apply >/dev/null
${ROOT}/runtime-env --catalog-root "${source_repo}" sync \
  --profile bettor-arena-local --binding bettor-arena-local \
  --workload local-proof --policy fixture-native --target-root "${target_repo}" --check >/dev/null

printf '\n' >> "${source_repo}/profiles/bettor-arena-local.json"
set +e
dirty_output="$(${ROOT}/runtime-env --catalog-root "${source_repo}" sync \
  --profile bettor-arena-local --binding bettor-arena-local \
  --workload local-proof --policy fixture-native --target-root "${target_repo}" --apply 2>&1)"
dirty_status=$?
set -e
[[ ${dirty_status} -eq 2 ]]
[[ "${dirty_output}" == *'catalog repository must be clean'* ]]

echo "PASS: explicit runtime-env sync dry-run, apply, and read-only drift check"
