#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT
fake_bin="${scratch}/bin"
fake_home="${scratch}/home"
state_root="${scratch}/state"
env_file="${scratch}/runtime.env"
sentinel='fixture-password-must-never-appear'
username='fixture-user-must-never-appear'

mkdir -p "${fake_bin}" "${fake_home}" "${state_root}"
ln -s "${ROOT}/tests/fixtures/fake-git.py" "${fake_bin}/git"
printf 'protocol=http\nhost=localhost:3000\nusername=legacy\npassword=legacy\n\n' \
  > "${fake_home}/.git-credentials"
chmod 0600 "${fake_home}/.git-credentials"
printf 'FORGEJO_URL=http://localhost:3000\nFORGEJO_USERNAME=%s\nFORGEJO_PASSWORD=%s\n' \
  "${username}" "${sentinel}" > "${env_file}"
chmod 0600 "${env_file}"

output="$(HOME="${fake_home}" PATH="${fake_bin}:/usr/bin:/bin" \
  FAKE_GIT_STATE_ROOT="${state_root}" \
  "${ROOT}/runtime-env" local-env migrate-forgejo-keychain \
  --env-file "${env_file}" 2>&1)"

[[ "${output}" == *'MIGRATED Forgejo localhost credential to macOS Keychain'* ]]
[[ "${output}" != *"${sentinel}"* ]]
[[ "${output}" != *"${username}"* ]]
grep -Fq "username=${username}" "${state_root}/keychain"
grep -Fq "password=${sentinel}" "${state_root}/keychain"
grep -Fq 'FORGEJO_USERNAME=fixture-user-must-never-appear' "${env_file}"
grep -Fxq 'FORGEJO_PASSWORD=' "${env_file}"
[[ ! -e "${fake_home}/.git-credentials" ]]
grep -Fq -- $'--replace-all\tcredential.http://localhost:3000.helper\t' \
  "${state_root}/config.log"
grep -Fq -- $'--add\tcredential.http://localhost:3000.helper\tosxkeychain' \
  "${state_root}/config.log"

unsafe_env="${scratch}/unsafe.env"
printf 'FORGEJO_URL=http://forgejo.example:3000\nFORGEJO_USERNAME=x\nFORGEJO_PASSWORD=%s\n' \
  "${sentinel}" > "${unsafe_env}"
chmod 0600 "${unsafe_env}"
rm -f "${state_root}/keychain"
set +e
unsafe_output="$(HOME="${fake_home}" PATH="${fake_bin}:/usr/bin:/bin" \
  FAKE_GIT_STATE_ROOT="${state_root}" \
  "${ROOT}/runtime-env" local-env migrate-forgejo-keychain \
  --env-file "${unsafe_env}" 2>&1)"
unsafe_status=$?
set -e
[[ ${unsafe_status} -eq 2 ]]
[[ "${unsafe_output}" == *'only http://localhost:3000 or http://127.0.0.1:3000'* ]]
[[ "${unsafe_output}" != *"${sentinel}"* ]]
[[ ! -e "${state_root}/keychain" ]]
grep -Fq "FORGEJO_PASSWORD=${sentinel}" "${unsafe_env}"

mismatch_env="${scratch}/mismatch.env"
printf 'FORGEJO_URL=http://localhost:3000\nFORGEJO_USERNAME=x\nFORGEJO_PASSWORD=%s\n' \
  "${sentinel}" > "${mismatch_env}"
chmod 0600 "${mismatch_env}"
set +e
mismatch_output="$(HOME="${fake_home}" PATH="${fake_bin}:/usr/bin:/bin" \
  FAKE_GIT_STATE_ROOT="${state_root}" FAKE_GIT_MODE=keychain-mismatch \
  "${ROOT}/runtime-env" local-env migrate-forgejo-keychain \
  --env-file "${mismatch_env}" 2>&1)"
mismatch_status=$?
set -e
[[ ${mismatch_status} -eq 2 ]]
[[ "${mismatch_output}" == *'Keychain verification returned different credentials'* ]]
[[ "${mismatch_output}" != *"${sentinel}"* ]]
grep -Fq "FORGEJO_PASSWORD=${sentinel}" "${mismatch_env}"

echo 'PASS: Forgejo credential migration is localhost-only and output-redacted'
