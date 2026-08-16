#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

consumer="${TMP}/consumer"
mkdir -p "${consumer}" "${TMP}/requirements"
git -C "${consumer}" init -q
git -C "${consumer}" config user.name runtime-env-test
git -C "${consumer}" config user.email runtime-env-test@example.invalid
printf 'fixture\n' > "${consumer}/README.md"
git -C "${consumer}" add README.md
git -C "${consumer}" commit -qm init

consumer_sha="$(git -C "${consumer}" rev-parse HEAD)"
runtime_sha="$(git -C "${ROOT}" rev-parse HEAD)"
runtime_tree="$(git -C "${ROOT}" rev-parse HEAD^{tree})"

python3 - "${TMP}" "${consumer_sha}" "${runtime_sha}" "${runtime_tree}" <<'PY'
import hashlib, json, pathlib, sys
base=pathlib.Path(sys.argv[1])
consumer_sha, runtime_sha, runtime_tree=sys.argv[2:]
req={
  "schema":"skills-shared/skill-runtime-requirements/v1",
  "skill":"control-plane-test",
  "capabilities":{"required":["forgejo-helper-contract"],"optional":[]},
  "modes":["connector","local"]
}
def digest(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
req_sha=digest(req)
(base/"requirements"/"control-plane-test.json").write_text(json.dumps(req,indent=2,sort_keys=True)+"\n")
resolution={
  "schema":"skills-shared/skill-resolution-receipt/v1",
  "skills_shared":{"repository":"ed3c/skills-shared","commit":"1"*40,"registry_sha256":"2"*64},
  "consumer":{"repository":"example/consumer","commit":consumer_sha},
  "skills":[{"name":"control-plane-test","content_sha256":"3"*64,"runtime_requirements_sha256":req_sha}]
}
binding={
  "schema":"runtime-env/repo-skill-runtime-binding/v1",
  "consumer":{"repository":"example/consumer","commit":consumer_sha},
  "runtime_env":{"repository":"ed3c/runtime-env","commit":runtime_sha,"tree":runtime_tree},
  "mode":"connector",
  "skills":{
    "control-plane-test":{
      "requirements_sha256":req_sha,
      "capability_map":{
        "forgejo-helper-contract":{
          "modules":["forgejo-local-keychain-helper"],
          "profile":"forgejo-delivery-keychain-local",
          "workload":"forgejo-delivery-loop",
          "policies":[],
          "setup_entrypoints":[],
          "probe_entrypoints":["broker-selftest"]
        }
      }
    }
  }
}
(base/"resolution.json").write_text(json.dumps(resolution,indent=2,sort_keys=True)+"\n")
(base/"binding.json").write_text(json.dumps(binding,indent=2,sort_keys=True)+"\n")
PY

"${ROOT}/runtime-env" skills resolve \
  --target-root "${consumer}" \
  --skill-resolution "${TMP}/resolution.json" \
  --requirements-dir "${TMP}/requirements" \
  --binding "${TMP}/binding.json" > "${TMP}/resolve.out"

"${ROOT}/runtime-env" skills plan \
  --target-root "${consumer}" \
  --skill-resolution "${TMP}/resolution.json" \
  --requirements-dir "${TMP}/requirements" \
  --binding "${TMP}/binding.json" \
  --output "${TMP}/plan.json"

"${ROOT}/runtime-env" skills check --plan "${TMP}/plan.json" --json > "${TMP}/check.json"

python3 - "${TMP}/plan.json" "${TMP}/check.json" <<'PY'
import json, sys
p=json.load(open(sys.argv[1])); c=json.load(open(sys.argv[2]))
assert p["mode"] == "connector"
assert p["resolved"]["modules"] == ["forgejo-local-keychain-helper"]
assert p["resolved"]["profile"] == "forgejo-delivery-keychain-local"
assert p["resolved"]["workload"] == "forgejo-delivery-loop"
assert p["resolved"]["probe_entrypoints"] == ["broker-selftest"]
assert p["capabilities"]["required"] == ["forgejo-helper-contract"]
assert set(p["claims"].values()) == {"NOT_EXERCISED"}
assert all(value is False for value in p["authority"].values())
assert p["secret_names"] == {"required": [], "optional": []}
assert c["execution_state"] == "NOT_EXERCISED"
assert c["missing_required_names"] == []
PY

# Connector is authorization/data access, not local compute.
if "${ROOT}/runtime-env" skills prepare \
  --plan "${TMP}/plan.json" \
  --target-root "${consumer}" \
  --receipt "${TMP}/receipt.json" >/dev/null 2>&1; then
  echo 'FAIL: connector mode executed prepare' >&2
  exit 1
fi

# Requirements bytes are exact-subject input; drift must fail closed.
python3 - "${TMP}/requirements/control-plane-test.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); p["capabilities"]["optional"].append("drift")
open(sys.argv[1],"w").write(json.dumps(p,indent=2,sort_keys=True)+"\n")
PY
if "${ROOT}/runtime-env" skills plan --target-root "${consumer}" --skill-resolution "${TMP}/resolution.json" --requirements-dir "${TMP}/requirements" --binding "${TMP}/binding.json" --output "${TMP}/bad-plan.json" >/dev/null 2>&1; then
  echo 'FAIL: requirements digest drift was accepted' >&2
  exit 1
fi

# Restore fixture then plant stale consumer subject.
git -C "${consumer}" commit --allow-empty -qm drift
python3 - "${TMP}/requirements/control-plane-test.json" <<'PY'
import json,sys
p={"schema":"skills-shared/skill-runtime-requirements/v1","skill":"control-plane-test","capabilities":{"required":["forgejo-helper-contract"],"optional":[]},"modes":["connector","local"]}
open(sys.argv[1],"w").write(json.dumps(p,indent=2,sort_keys=True)+"\n")
PY
if "${ROOT}/runtime-env" skills plan --target-root "${consumer}" --skill-resolution "${TMP}/resolution.json" --requirements-dir "${TMP}/requirements" --binding "${TMP}/binding.json" --output "${TMP}/stale-plan.json" >/dev/null 2>&1; then
  echo 'FAIL: stale consumer subject was accepted' >&2
  exit 1
fi

# Portable plans cannot be mutated into runtime PASS without an exact prepare receipt.
python3 - "${TMP}/plan.json" "${TMP}/mutated-plan.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); p["claims"]["environment_ready"]="PASS"
open(sys.argv[2],"w").write(json.dumps(p,indent=2,sort_keys=True)+"\n")
PY
if "${ROOT}/runtime-env" skills check --plan "${TMP}/mutated-plan.json" --json >/dev/null 2>&1; then
  echo 'FAIL: portable plan promoted itself to PASS' >&2
  exit 1
fi

for schema in \
  skill-resolution-receipt.schema.json \
  skill-runtime-requirements.schema.json \
  repo-skill-runtime-binding.schema.json \
  agent-environment-plan.schema.json \
  agent-environment-receipt.schema.json; do
  python3 -m json.tool "${ROOT}/contracts/${schema}" >/dev/null
done

echo 'PASS: exact Skill environment closure, connector boundary, and planted negatives'
