#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

positive_output="$(${ROOT}/runtime-env validate)"
[[ "${positive_output}" == OK* ]] || {
  echo "FAIL: validate did not emit an OK receipt" >&2
  exit 1
}

set +e
negative_output="$(${ROOT}/runtime-env --catalog-root "${ROOT}/tests/fixtures/invalid-unknown-variable" validate 2>&1)"
negative_status=$?
set -e
[[ ${negative_status} -eq 2 ]] || {
  echo "FAIL: invalid catalog should exit 2, got ${negative_status}" >&2
  exit 1
}
[[ "${negative_output}" == *"unknown variable MISSING_TOKEN"* ]] || {
  echo "FAIL: invalid catalog did not identify the unknown variable" >&2
  exit 1
}

set +e
unsafe_output="$(${ROOT}/runtime-env --catalog-root "${ROOT}/tests/fixtures/invalid-value-field" validate 2>&1)"
unsafe_status=$?
set -e
[[ ${unsafe_status} -eq 2 ]] || {
  echo "FAIL: catalog containing a value field should exit 2, got ${unsafe_status}" >&2
  exit 1
}
[[ "${unsafe_output}" == *"unexpected fields on E2B_API_KEY: value"* ]] || {
  echo "FAIL: unsafe catalog field was not identified" >&2
  exit 1
}

echo "PASS: catalog validation seam"
