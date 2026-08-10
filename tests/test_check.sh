#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

set +e
missing_output="$(env -u E2B_API_KEY "${ROOT}/runtime-env" check --profile skill-bettor-e2b 2>&1)"
missing_status=$?
set -e
[[ ${missing_status} -eq 3 ]] || {
  echo "FAIL: missing required configuration should exit 3, got ${missing_status}" >&2
  exit 1
}
[[ "${missing_output}" == *"MISSING required: E2B_API_KEY"* ]] || {
  echo "FAIL: missing configuration did not name E2B_API_KEY" >&2
  exit 1
}

present_output="$(env E2B_API_KEY=present-for-test "${ROOT}/runtime-env" check --profile skill-bettor-e2b)"
[[ "${present_output}" == *"PRESENT required: E2B_API_KEY"* ]] || {
  echo "FAIL: present configuration was not recognized" >&2
  exit 1
}
[[ "${present_output}" != *"present-for-test"* ]] || {
  echo "FAIL: check output leaked the configured value" >&2
  exit 1
}

file_output="$(env -u E2B_API_KEY "${ROOT}/runtime-env" check --profile skill-bettor-e2b --env-file "${ROOT}/tests/fixtures/e2b.present")"
[[ "${file_output}" == *"OK profile skill-bettor-e2b"* ]] || {
  echo "FAIL: dotenv input did not satisfy the profile" >&2
  exit 1
}

local_output="$(env -u OPENAI_API_KEY -u GEMINI_API_KEY -u E2B_API_KEY "${ROOT}/runtime-env" check --profile skill-bettor-local)"
[[ "${local_output}" == *"OK profile skill-bettor-local"* ]] || {
  echo "FAIL: local-zero-key profile should pass without cloud credentials" >&2
  exit 1
}

echo "PASS: environment presence check seam"
