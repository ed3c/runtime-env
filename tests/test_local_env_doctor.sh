#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT
fixture="${scratch}/runtime.env"
initialized="${scratch}/initialized.env"
symlinked="${scratch}/symlinked.env"
sentinel='fixture-secret-must-never-appear'

file_mode() {
  if stat -f '%Lp' "$1" >/dev/null 2>&1; then
    stat -f '%Lp' "$1"
  else
    stat -c '%a' "$1"
  fi
}

init_output="$(${ROOT}/runtime-env local-env init --env-file "${initialized}")"
[[ "${init_output}" == *'CREATED local env template'* ]]
[[ "$(file_mode "${initialized}")" == '600' ]]
grep -Fq 'E2B_API_KEY=' "${initialized}"
grep -Fq 'GEMINI_API_KEY=' "${initialized}"
if grep -Eq '^[A-Z][A-Z0-9_]*=.+$' "${initialized}"; then
  echo 'FAIL: initialized local env contains a value' >&2
  exit 1
fi

set +e
reinit_output="$(${ROOT}/runtime-env local-env init --env-file "${initialized}" 2>&1)"
reinit_status=$?
set -e
[[ ${reinit_status} -eq 2 ]]
[[ "${reinit_output}" == *'already exists'* ]]

ln -s "${initialized}" "${symlinked}"
set +e
symlink_output="$(${ROOT}/runtime-env local-env doctor --env-file "${symlinked}" 2>&1)"
symlink_status=$?
set -e
[[ ${symlink_status} -eq 2 ]]
[[ "${symlink_output}" == *'not a symlink'* ]]

printf 'E2B_API_KEY=%s\nGEMINI_API_KEY=\n' "${sentinel}" > "${fixture}"
chmod 0644 "${fixture}"

set +e
unsafe_output="$(${ROOT}/runtime-env local-env doctor --env-file "${fixture}" 2>&1)"
unsafe_status=$?
set -e
[[ ${unsafe_status} -eq 2 ]]
[[ "${unsafe_output}" == *'mode 0600'* ]]
[[ "${unsafe_output}" != *"${sentinel}"* ]]

chmod 0600 "${fixture}"
safe_output="$(${ROOT}/runtime-env local-env doctor --env-file "${fixture}")"
[[ "${safe_output}" == *'PRESENT E2B_API_KEY'* ]]
[[ "${safe_output}" == *'EMPTY GEMINI_API_KEY'* ]]
[[ "${safe_output}" == *'OK local env metadata'* ]]
[[ "${safe_output}" != *"${sentinel}"* ]]

reconcile_output="$(${ROOT}/runtime-env local-env reconcile --env-file "${fixture}")"
[[ "${reconcile_output}" == *'RECONCILED local env'* ]]
[[ "${reconcile_output}" != *"${sentinel}"* ]]
[[ "$(file_mode "${fixture}")" == '600' ]]
grep -Fq "E2B_API_KEY=${sentinel}" "${fixture}"
grep -Fq 'EQUIVALENCE_REQUEST_PATH=' "${fixture}"

config_root="${scratch}/codex-home"
mkdir -p "${config_root}"
set_path_output="$(${ROOT}/runtime-env local-env set-path --env-file "${fixture}" \
  --name CODEX_HOME --path "${config_root}")"
[[ "${set_path_output}" == 'UPDATED local env path: CODEX_HOME' ]]
[[ "${set_path_output}" != *"${config_root}"* ]]
grep -Fq "CODEX_HOME=${config_root}" "${fixture}"

set +e
secret_path_output="$(${ROOT}/runtime-env local-env set-path --env-file "${fixture}" \
  --name E2B_API_KEY --path "${config_root}" 2>&1)"
secret_path_status=$?
set -e
[[ ${secret_path_status} -eq 2 && "${secret_path_output}" == *'non-secret path variables'* ]]
[[ "${secret_path_output}" != *"${sentinel}"* ]]

echo 'PASS: local env doctor reports metadata without values'
