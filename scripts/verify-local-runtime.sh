#!/usr/bin/env bash
set -euo pipefail
# Credentials are acquired below. Disable inherited/explicit `bash -x` before
# any secret can enter a shell variable; xtrace would otherwise serialize the
# value to stderr during command substitution.
set +x

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${HOME}/.config/runtime-env/secrets/forgejo-local.env"
canonical_path=""
credential_helper_only=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      [[ $# -ge 2 && -n "$2" ]] || {
        echo "--env-file requires a path" >&2
        exit 2
      }
      env_file="$2"
      shift 2
      ;;
    --canonical-path)
      [[ $# -ge 2 && -n "$2" ]] || {
        echo "--canonical-path requires a path" >&2
        exit 2
      }
      canonical_path="$2"
      shift 2
      ;;
    --credential-helper-only)
      credential_helper_only=true
      shift
      ;;
    *)
      echo "usage: verify-local-runtime.sh [--env-file PATH] [--canonical-path PATH] [--credential-helper-only]" >&2
      exit 2
      ;;
  esac
done

if [[ -n "${canonical_path}" ]]; then
  [[ -d "${canonical_path}" ]] || {
    echo "ABSENT canonical runtime checkout: ${canonical_path}" >&2
    exit 3
  }
  root_real="$(cd "${ROOT}" && pwd -P)"
  canonical_real="$(cd "${canonical_path}" && pwd -P)"
  [[ "${root_real}" == "${canonical_real}" ]] || {
    echo "DRIFT verifier root ${root_real} != canonical ${canonical_real}" >&2
    exit 2
  }
  echo "PRESENT canonical runtime checkout ${canonical_path}"
fi

"${ROOT}/runtime-env" validate

version_json="$(curl -q --noproxy '*' -fsS --connect-timeout 2 --max-time 5 http://localhost:3000/api/v1/version)" || {
  echo "UNREACHABLE Forgejo at http://localhost:3000" >&2
  exit 4
}
FORGEJO_VERSION_JSON="${version_json}" python3 - <<'PY'
import json
import os

value = json.loads(os.environ["FORGEJO_VERSION_JSON"])
version = value.get("version")
if not isinstance(version, str) or not version:
    raise SystemExit("INVALID Forgejo version response")
print(f"PRESENT Forgejo loopback version={version}")
PY
unset version_json

credential_payload=""
set +e
credential_payload="$(
  printf 'protocol=http\nhost=localhost:3000\n\n' |
    GIT_TERMINAL_PROMPT=0 git credential fill 2>/dev/null
)"
credential_status=$?
set -e

credential_user=""
credential_secret=""
credential_secret_present=false
if [[ ${credential_status} -eq 0 ]]; then
  while IFS='=' read -r key value; do
    case "${key}" in
      username) credential_user="${value}" ;;
      password)
        credential_secret="${value}"
        [[ -n "${value}" ]] && credential_secret_present=true
        ;;
    esac
  done <<< "${credential_payload}"
fi
credential_payload=""
unset credential_payload

if [[ -n "${credential_user}" && "${credential_secret_present}" == true ]]; then
  credential_source="git credential helper"
elif [[ "${credential_helper_only}" == true ]]; then
  echo "MISSING Forgejo credential: helper empty in helper-only mode" >&2
  exit 3
elif [[ -f "${env_file}" ]]; then
  set +e
  python3 - "${env_file}" <<'PY'
import os
from pathlib import Path
import stat
import sys

path = Path(sys.argv[1])
mode = stat.S_IMODE(path.stat().st_mode)
if path.stat().st_uid != os.getuid():
    raise SystemExit(f"UNSAFE fallback owner for {path}")
if mode != 0o600:
    raise SystemExit(f"UNSAFE fallback mode {mode:04o} for {path}; expected 0600")
PY
  fallback_mode_status=$?
  set -e
  [[ ${fallback_mode_status} -eq 0 ]] || exit 2
  "${ROOT}/runtime-env" check \
    --profile forgejo-delivery-local-password \
    --env-file "${env_file}"
  credential_user="$(PYTHONPATH="${ROOT}/src" python3 -c \
    'from pathlib import Path; import sys; from runtime_env.cli import load_dotenv; print(load_dotenv(Path(sys.argv[1]))["FORGEJO_USERNAME"])' \
    "${env_file}")"
  credential_secret="$(PYTHONPATH="${ROOT}/src" python3 -c \
    'from pathlib import Path; import sys; from runtime_env.cli import load_dotenv; print(load_dotenv(Path(sys.argv[1]))["FORGEJO_PASSWORD"])' \
    "${env_file}")"
  forgejo_url="$(PYTHONPATH="${ROOT}/src" python3 -c \
    'from pathlib import Path; import sys; from runtime_env.cli import load_dotenv; print(load_dotenv(Path(sys.argv[1])).get("FORGEJO_URL") or "http://localhost:3000")' \
    "${env_file}")"
  credential_source="explicit dotenv fallback"
else
  echo "MISSING Forgejo credential: helper empty and fallback absent at ${env_file}" >&2
  exit 3
fi

forgejo_url="${forgejo_url:-http://localhost:3000}"
case "${forgejo_url}" in
  http://localhost:3000|http://localhost:3000/|http://127.0.0.1:3000|http://127.0.0.1:3000/) ;;
  *)
    echo "REFUSED non-loopback Forgejo URL: ${forgejo_url}" >&2
    exit 2
    ;;
esac

curl_config_escape() {
  local value="$1"
  [[ "${value}" != *$'\n'* && "${value}" != *$'\r'* ]] || return 2
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  printf '%s' "${value}"
}

escaped_user="$(curl_config_escape "${credential_user}")" || {
  echo "REFUSED credential username contains a newline" >&2
  exit 2
}
escaped_secret="$(curl_config_escape "${credential_secret}")" || {
  echo "REFUSED credential secret contains a newline" >&2
  exit 2
}
auth_url="${forgejo_url%/}/api/v1/user"

set +e
auth_body="$(
  {
    printf 'url = "%s"\n' "${auth_url}"
    printf 'user = "%s:%s"\n' "${escaped_user}" "${escaped_secret}"
    printf '%s\n' 'fail' 'silent' 'show-error' 'connect-timeout = 2' 'max-time = 5'
  } | curl -q --noproxy '*' --config -
)"
auth_status=$?
set -e
credential_user=""
credential_secret=""
escaped_user=""
escaped_secret=""
unset credential_user credential_secret escaped_user escaped_secret

if [[ ${auth_status} -ne 0 ]]; then
  auth_body=""
  unset auth_body
  echo "REFUSED Forgejo credential from ${credential_source}" >&2
  exit 1
fi

printf '%s' "${auth_body}" | python3 -c \
  'import json,sys; value=json.load(sys.stdin); assert isinstance(value.get("login"), str) and value["login"]'
auth_body=""
unset auth_body

echo "AUTHENTICATED Forgejo credential via ${credential_source} (value redacted)"

echo "LOCAL-RUNTIME GREEN ${ROOT}"
