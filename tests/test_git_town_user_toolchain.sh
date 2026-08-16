#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT
mkdir -m 700 "${TMP}/home" "${TMP}/receipts"

fake="${TMP}/fake"
mkdir -p "${fake}/payload"
cat > "${fake}/payload/git-town" <<'SH'
#!/usr/bin/env bash
if [[ "${1:-}" == "--version" ]]; then
  echo 'Git Town 24.0.0'
  exit 0
fi
echo 'fake git-town: tests must not execute Stack operations' >&2
exit 64
SH
chmod +x "${fake}/payload/git-town"
tar -C "${fake}/payload" -czf "${fake}/git-town_test.tar.gz" git-town
archive_sha="$(python3 - "${fake}/git-town_test.tar.gz" <<'PY'
import hashlib,sys
print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())
PY
)"

cat > "${TMP}/manifest.json" <<JSON
{
  "schema":"runtime-env/git-town-toolchain-manifest/v1",
  "tool":"git-town",
  "version":"24.0.0",
  "release":{
    "repository":"git-town/git-town",
    "tag":"v24.0.0",
    "immutable":true,
    "published_at":"2026-07-23T13:48:21Z",
    "checksums_asset":"checksums.txt",
    "checksums_sha256":"7532377166cb59dc01c74f86e3a71c54ba9567a461313a5d203a1ea99c571b24"
  },
  "assets":{
    "linux-amd64":{"name":"git-town_linux_intel_64.tar.gz","sha256":"${archive_sha}"}
  }
}
JSON

tool_root="${TMP}/home/.local/lib/runtime-env/git-town"
launcher="${TMP}/home/.local/bin/git-town"
receipt="${TMP}/receipts/install.json"

RUNTIME_ENV_ALLOW_TEST_ROOT=1 python3 "${ROOT}/scripts/git-town-toolchain.py" apply \
  --manifest "${TMP}/manifest.json" \
  --platform linux-amd64 \
  --tool-root "${tool_root}" \
  --launcher "${launcher}" \
  --archive "${fake}/git-town_test.tar.gz" \
  --receipt "${receipt}" > "${TMP}/apply.json"

test -L "${launcher}"
test -x "$(readlink -f "${launcher}")"
test "$(stat -c '%a' "${receipt}")" = 600
"${launcher}" --version | grep -F '24.0.0' >/dev/null

RUNTIME_ENV_ALLOW_TEST_ROOT=1 python3 "${ROOT}/scripts/git-town-toolchain.py" check \
  --manifest "${TMP}/manifest.json" \
  --platform linux-amd64 \
  --tool-root "${tool_root}" \
  --launcher "${launcher}" > "${TMP}/check.json"

python3 - "${TMP}/apply.json" "${TMP}/check.json" <<'PY'
import json,sys
installed=json.load(open(sys.argv[1])); checked=json.load(open(sys.argv[2]))
assert installed['state']=='PASS', installed
assert checked['state']=='PASS', checked
assert installed['version']=='24.0.0'
assert installed['live_stack']=='NOT_EXERCISED'
assert installed['live_dual_forge']=='NOT_EXERCISED'
assert checked['live_stack']=='NOT_EXERCISED'
assert checked['live_dual_forge']=='NOT_EXERCISED'
assert installed['asset']['platform']=='linux-amd64'
PY

# Idempotent apply to the same managed target remains valid.
RUNTIME_ENV_ALLOW_TEST_ROOT=1 python3 "${ROOT}/scripts/git-town-toolchain.py" apply \
  --manifest "${TMP}/manifest.json" --platform linux-amd64 \
  --tool-root "${tool_root}" --launcher "${launcher}" \
  --archive "${fake}/git-town_test.tar.gz" >/dev/null

# Wrong checksum must fail before activation.
python3 - "${TMP}/manifest.json" "${TMP}/bad-digest.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); p['assets']['linux-amd64']['sha256']='0'*64
json.dump(p,open(sys.argv[2],'w'))
PY
if RUNTIME_ENV_ALLOW_TEST_ROOT=1 python3 "${ROOT}/scripts/git-town-toolchain.py" apply \
  --manifest "${TMP}/bad-digest.json" --platform linux-amd64 \
  --tool-root "${TMP}/bad-root" --launcher "${TMP}/home/.local/bin/bad-git-town" \
  --archive "${fake}/git-town_test.tar.gz" >/dev/null 2>&1; then
  echo 'FAIL: wrong archive checksum was accepted' >&2
  exit 1
fi

# Mutable release identity is forbidden.
python3 - "${TMP}/manifest.json" "${TMP}/latest.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); p['version']='latest'; p['release']['tag']='latest'
json.dump(p,open(sys.argv[2],'w'))
PY
if python3 "${ROOT}/scripts/git-town-toolchain.py" plan --manifest "${TMP}/latest.json" --platform linux-amd64 --tool-root "${TMP}/x" --launcher "${TMP}/y" >/dev/null 2>&1; then
  echo 'FAIL: mutable latest identity was accepted' >&2
  exit 1
fi

# Platform mismatch must fail before archive use.
if python3 "${ROOT}/scripts/git-town-toolchain.py" plan --manifest "${TMP}/manifest.json" --platform darwin-arm64 --tool-root "${TMP}/x" --launcher "${TMP}/y" >/dev/null 2>&1; then
  echo 'FAIL: unmanifested platform was accepted' >&2
  exit 1
fi

# Never replace an unmanaged launcher.
unmanaged="${TMP}/home/.local/bin/unmanaged-git-town"
printf '#!/bin/sh\nexit 0\n' > "${unmanaged}"
chmod +x "${unmanaged}"
if RUNTIME_ENV_ALLOW_TEST_ROOT=1 python3 "${ROOT}/scripts/git-town-toolchain.py" apply \
  --manifest "${TMP}/manifest.json" --platform linux-amd64 \
  --tool-root "${TMP}/other-root" --launcher "${unmanaged}" \
  --archive "${fake}/git-town_test.tar.gz" >/dev/null 2>&1; then
  echo 'FAIL: unmanaged launcher was replaced' >&2
  exit 1
fi

# Repository-local installation is not a supported consumer pattern.
if python3 "${ROOT}/scripts/git-town-toolchain.py" plan --manifest "${TMP}/manifest.json" --platform linux-amd64 --tool-root "${ROOT}/.git-town-runtime" --launcher "${TMP}/y" >/dev/null 2>&1; then
  echo 'FAIL: repository-local tool root was admitted' >&2
  exit 1
fi

# Doctor is structural: executable state can vary, live delivery cannot self-promote.
python3 "${ROOT}/scripts/repository-control-plane-doctor.py" --mode contract > "${TMP}/doctor.json"
python3 - "${TMP}/doctor.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]))
assert p['contract']=='PASS', p
assert p['live_stack_operation']=='NOT_EXERCISED', p
assert p['live_dual_forge_operation']=='NOT_EXERCISED', p
assert p['forgejo_credential_canary']=='NOT_EXERCISED', p
PY

# The checked-in upstream manifest must remain exact and immutable.
python3 - "${ROOT}/catalog/git-town-toolchain.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]))
assert p['version']=='24.0.0'
assert p['release']['tag']=='v24.0.0'
assert p['release']['immutable'] is True
assert p['release']['checksums_sha256']=='7532377166cb59dc01c74f86e3a71c54ba9567a461313a5d203a1ea99c571b24'
assert p['assets']['darwin-arm64']['sha256']=='0de42d52bad34316413c9d0ba0052d09d4ba8746930aa2cc6eaa5931562a91b2'
assert p['assets']['darwin-amd64']['sha256']=='ef0ba7ef0526a4ad414d9a3e8507b2eaa6e08edb6dd67ffff0ee244222c84cd4'
assert p['assets']['linux-arm64']['sha256']=='967d8014a43a7ad6cf9760b7cb70f79dc423c2b550ec934ad71b0513fbad9427'
assert p['assets']['linux-amd64']['sha256']=='0ed4936f010b42db2ef573e4b2abd951289f4980d95b8236a619429e2501cbc7'
PY

echo 'PASS: pinned user-scoped Git Town toolchain and doctor controls'
