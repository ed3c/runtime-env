#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT
mkdir -m 700 "${TMP}/home" "${TMP}/receipts"

fake="${TMP}/forgejo"
cat > "${fake}" <<'SH'
#!/usr/bin/env bash
if [[ "${1:-}" == "--version" ]]; then echo 'Forgejo version 15.0.5'; exit 0; fi
if [[ "${1:-}" == "dump" ]]; then
  out=''
  while [[ $# -gt 0 ]]; do
    if [[ "$1" == "--file" ]]; then out="$2"; shift 2; continue; fi
    shift
  done
  [[ -n "$out" ]] || exit 64
  printf 'fake-consistent-forgejo-dump\n' > "$out"
  exit 0
fi
exit 64
SH
chmod +x "${fake}"
artifact_sha="$(python3 - "${fake}" <<'PY'
import hashlib,sys
print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())
PY
)"
cat > "${TMP}/binding.json" <<JSON
{
  "schema":"runtime-env/forgejo-host-binding/v1",
  "version":"15.0.5",
  "platform":"linux-amd64",
  "artifact_sha256":"${artifact_sha}",
  "install_root":"${TMP}/home/.local/lib/runtime-env/forgejo",
  "state_root":"${TMP}/home/.local/state/runtime-env/forgejo",
  "port":3000
}
JSON

python3 "${ROOT}/scripts/forgejo-host-service.py" plan --binding "${TMP}/binding.json" > "${TMP}/plan.json"
python3 - "${TMP}/plan.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); assert p['version']=='15.0.5'; assert p['service']=='NOT_EXERCISED'; assert p['health']=='NOT_EXERCISED'; assert p['upgrade']=='HUMAN_ADMIT_REQUIRED'; assert p['rollback']=='NOT_EXERCISED'
PY

RUNTIME_ENV_ALLOW_TEST_ROOT=1 python3 "${ROOT}/scripts/forgejo-host-service.py" install --binding "${TMP}/binding.json" --artifact "${fake}" --receipt "${TMP}/receipts/install.json" > "${TMP}/install.json"
test "$(stat -c '%a' "${TMP}/receipts/install.json")" = 600
test "$(stat -c '%a' "${TMP}/home/.local/state/runtime-env/forgejo/config/app.ini")" = 600
grep -F 'HTTP_ADDR = 127.0.0.1' "${TMP}/home/.local/state/runtime-env/forgejo/config/app.ini" >/dev/null
grep -F 'HTTP_PORT = 3000' "${TMP}/home/.local/state/runtime-env/forgejo/config/app.ini" >/dev/null

python3 "${ROOT}/scripts/forgejo-host-service.py" check --binding "${TMP}/binding.json" > "${TMP}/check.json"
python3 - "${TMP}/install.json" "${TMP}/check.json" <<'PY'
import json,sys
a,b=[json.load(open(x)) for x in sys.argv[1:]]
assert a['state']=='PASS'; assert a['service']=='NOT_EXERCISED'; assert a['health']=='NOT_EXERCISED'; assert a['credentials']=='NOT_EXERCISED'; assert a['migration']=='NOT_EXERCISED'
assert b['state']=='PASS'; assert b['service']=='NOT_EXERCISED'; assert b['health']=='NOT_EXERCISED'
PY

# Backup refuses a potentially live SQLite copy without explicit stopped-service evidence.
if python3 "${ROOT}/scripts/forgejo-host-service.py" backup --binding "${TMP}/binding.json" --output "${TMP}/bad.zip" >/dev/null 2>&1; then
  echo 'FAIL: backup ran without stopped-service evidence' >&2; exit 1
fi
python3 "${ROOT}/scripts/forgejo-host-service.py" backup --binding "${TMP}/binding.json" --output "${TMP}/backup.zip" --service-stopped --receipt "${TMP}/receipts/backup.json" > "${TMP}/backup.json"
test -s "${TMP}/backup.zip"
python3 - "${TMP}/backup.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); assert p['state']=='PASS'; assert p['service_stopped'] is True; assert len(p['backup_sha256'])==64
PY

# Upgrade cannot self-admit; it produces a Human gate and a non-success exit.
set +e
python3 "${ROOT}/scripts/forgejo-host-service.py" upgrade-plan --binding "${TMP}/binding.json" > "${TMP}/upgrade.json"
upgrade_exit=$?
set -e
test "${upgrade_exit}" = 4
python3 - "${TMP}/upgrade.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); assert p['upgrade']=='HUMAN_ADMIT_REQUIRED'; assert p['backup_required'] is True
PY

# Wrong artifact digest is rejected before host mutation.
python3 - "${TMP}/binding.json" "${TMP}/wrong.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); p['artifact_sha256']='0'*64; json.dump(p,open(sys.argv[2],'w'))
PY
if RUNTIME_ENV_ALLOW_TEST_ROOT=1 python3 "${ROOT}/scripts/forgejo-host-service.py" install --binding "${TMP}/wrong.json" --artifact "${fake}" >/dev/null 2>&1; then
  echo 'FAIL: wrong Forgejo artifact digest was accepted' >&2; exit 1
fi

# Floating/mismatched version is rejected by central LTS manifest.
python3 - "${TMP}/binding.json" "${TMP}/version.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); p['version']='16.0.1'; json.dump(p,open(sys.argv[2],'w'))
PY
if python3 "${ROOT}/scripts/forgejo-host-service.py" plan --binding "${TMP}/version.json" >/dev/null 2>&1; then
  echo 'FAIL: non-admitted Forgejo version was accepted' >&2; exit 1
fi

# Consumer repository may not be used as host install/data root.
python3 - "${TMP}/binding.json" "${TMP}/repo-local.json" "${ROOT}" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); p['install_root']=sys.argv[3]+'/.forgejo-host'; json.dump(p,open(sys.argv[2],'w'))
PY
if python3 "${ROOT}/scripts/forgejo-host-service.py" plan --binding "${TMP}/repo-local.json" >/dev/null 2>&1; then
  echo 'FAIL: repository-local Forgejo service root was accepted' >&2; exit 1
fi

python3 -m json.tool "${ROOT}/catalog/forgejo-host-service.json" >/dev/null
python3 -m json.tool "${ROOT}/contracts/forgejo-host-binding.schema.json" >/dev/null

echo 'PASS: exact Forgejo host lifecycle, backup gate, and Human upgrade boundary'
