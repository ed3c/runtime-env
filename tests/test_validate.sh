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

echo "PASS: catalog validation seam"
