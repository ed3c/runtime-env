#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

profiles="$(${ROOT}/runtime-env list --kind profiles)"
[[ "${profiles}" == *"skill-bettor-local"* ]] || {
  echo "FAIL: profile listing omitted skill-bettor-local" >&2
  exit 1
}
[[ "${profiles}" == *"mac-device-runner"* ]] || {
  echo "FAIL: profile listing omitted mac-device-runner" >&2
  exit 1
}
[[ "${profiles}" == *"codex-cloud-portable"* ]] || {
  echo "FAIL: profile listing omitted codex-cloud-portable" >&2
  exit 1
}

e2b="$(${ROOT}/runtime-env list --profile skill-bettor-e2b)"
[[ "${e2b}" == *$'required\tsecret\tE2B_API_KEY'* ]] || {
  echo "FAIL: profile details lost E2B requirement metadata" >&2
  exit 1
}

local="$(${ROOT}/runtime-env list --profile skill-bettor-local)"
[[ "${local}" == *$'optional\tnon-secret\tOLLAMA_BASE_URL\thttp://127.0.0.1:11434/v1'* ]] || {
  echo "FAIL: profile details lost local defaults" >&2
  exit 1
}

forgejo="$(${ROOT}/runtime-env list --profile forgejo-delivery-local-password)"
for expected in \
  $'optional\tnon-secret\tFORGEJO_URL\thttp://localhost:3000' \
  $'required\tnon-secret\tFORGEJO_USERNAME' \
  $'required\tsecret\tFORGEJO_PASSWORD'; do
  [[ "${forgejo}" == *"${expected}"* ]] || {
    echo "FAIL: Forgejo password profile omitted ${expected}" >&2
    exit 1
  }
done

forgejo_token="$(${ROOT}/runtime-env list --profile forgejo-delivery-local-api)"
[[ "${forgejo_token}" == *$'required\tsecret\tFORGEJO_TOKEN'* ]] || {
  echo "FAIL: Forgejo token profile omitted FORGEJO_TOKEN" >&2
  exit 1
}

echo "PASS: catalog discovery seam"
