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
python3 "${ROOT}/scripts/forgejo-host-service.py" preflight --binding "${TMP}/binding.json" > "${TMP}/preflight.json"
python3 - "${TMP}/plan.json" "${TMP}/preflight.json" <<'PY'
import json,sys
p,f=[json.load(open(x)) for x in sys.argv[1:]]
assert p['version']=='15.0.5' and p['service']=='NOT_EXERCISED' and p['health']=='NOT_EXERCISED'
assert p['restore']=='NOT_EXERCISED' and p['upgrade']=='HUMAN_ADMIT_REQUIRED' and p['rollback']=='NOT_EXERCISED'
assert f['state']=='PASS' and f['port_available'] is True and f['service']=='NOT_EXERCISED'
PY

# Interrupted staging is a hard blocker: never activate half-installed bytes.
staging="${TMP}/home/.local/lib/runtime-env/forgejo/.15.0.5.staging"
mkdir -p "${staging}"
if python3 "${ROOT}/scripts/forgejo-host-service.py" preflight --binding "${TMP}/binding.json" >/dev/null 2>&1; then
  echo 'FAIL: interrupted staging was accepted' >&2; exit 1
fi
rm -rf "${staging}"

RUNTIME_ENV_ALLOW_TEST_ROOT=1 python3 "${ROOT}/scripts/forgejo-host-service.py" install --binding "${TMP}/binding.json" --artifact "${fake}" --receipt "${TMP}/receipts/install.json" > "${TMP}/install.json"
test "$(stat -c '%a' "${TMP}/receipts/install.json")" = 600
test "$(stat -c '%a' "${TMP}/home/.local/state/runtime-env/forgejo/config/app.ini")" = 600
grep -F 'HTTP_ADDR = 127.0.0.1' "${TMP}/home/.local/state/runtime-env/forgejo/config/app.ini" >/dev/null
grep -F 'HTTP_PORT = 3000' "${TMP}/home/.local/state/runtime-env/forgejo/config/app.ini" >/dev/null
test ! -e "${staging}"

python3 "${ROOT}/scripts/forgejo-host-service.py" check --binding "${TMP}/binding.json" > "${TMP}/check.json"
python3 - "${TMP}/install.json" "${TMP}/check.json" <<'PY'
import json,sys
a,b=[json.load(open(x)) for x in sys.argv[1:]]
assert a['state']=='PASS' and a['service']=='NOT_EXERCISED' and a['health']=='NOT_EXERCISED'
assert a['credentials']=='NOT_EXERCISED' and a['migration']=='NOT_EXERCISED'
assert b['state']=='PASS' and b['restore']=='NOT_EXERCISED' and b['rollback']=='NOT_EXERCISED'
PY

# Backup refuses a potentially live SQLite copy without explicit stopped-service evidence.
if python3 "${ROOT}/scripts/forgejo-host-service.py" backup --binding "${TMP}/binding.json" --output "${TMP}/bad.zip" >/dev/null 2>&1; then
  echo 'FAIL: backup ran without stopped-service evidence' >&2; exit 1
fi
python3 "${ROOT}/scripts/forgejo-host-service.py" backup --binding "${TMP}/binding.json" --output "${TMP}/backup.zip" --service-stopped --receipt "${TMP}/receipts/backup.json" > "${TMP}/backup.json"
test -s "${TMP}/backup.zip"
python3 - "${TMP}/backup.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); assert p['state']=='PASS' and p['service_stopped'] is True
assert len(p['backup_sha256'])==64 and len(p['binary_sha256'])==64 and len(p['config_sha256'])==64
PY

# Restore preflight proves exact backup + binary + config identity but performs no destructive mutation.
python3 "${ROOT}/scripts/forgejo-host-service.py" restore-check --binding "${TMP}/binding.json" --backup-receipt "${TMP}/receipts/backup.json" --backup-file "${TMP}/backup.zip" > "${TMP}/restore.json"
python3 - "${TMP}/restore.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); assert p['state']=='PASS'; assert p['restore_execution']=='NOT_EXERCISED'; assert p['destructive_mutation'] is False
PY

# Tampered backup cannot become a restore or rollback subject.
printf 'tamper\n' >> "${TMP}/backup.zip"
if python3 "${ROOT}/scripts/forgejo-host-service.py" restore-check --binding "${TMP}/binding.json" --backup-receipt "${TMP}/receipts/backup.json" --backup-file "${TMP}/backup.zip" >/dev/null 2>&1; then
  echo 'FAIL: tampered backup was accepted' >&2; exit 1
fi
printf 'fake-consistent-forgejo-dump\n' > "${TMP}/backup.zip"

# Rollback remains Human-owned even after exact restore preflight passes.
set +e
python3 "${ROOT}/scripts/forgejo-host-service.py" rollback-plan --binding "${TMP}/binding.json" --backup-receipt "${TMP}/receipts/backup.json" --backup-file "${TMP}/backup.zip" > "${TMP}/rollback.json"
rollback_exit=$?
set -e
test "${rollback_exit}" = 4
python3 - "${TMP}/rollback.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); assert p['rollback']=='HUMAN_ADMIT_REQUIRED'; assert p['restore_preflight']=='PASS'; assert p['destructive_mutation'] is False
PY

# Upgrade cannot self-admit and must bind both backup and rollback subjects.
set +e
python3 "${ROOT}/scripts/forgejo-host-service.py" upgrade-plan --binding "${TMP}/binding.json" > "${TMP}/upgrade.json"
upgrade_exit=$?
set -e
test "${upgrade_exit}" = 4
python3 - "${TMP}/upgrade.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); assert p['upgrade']=='HUMAN_ADMIT_REQUIRED'; assert p['backup_required'] is True; assert p['rollback_subject_required'] is True
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

echo 'PASS: Forgejo atomic install, restore preflight, rollback gate, and interruption controls'
