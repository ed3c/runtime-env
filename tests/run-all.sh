#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for test_script in "${ROOT}"/tests/test_*.sh; do
  bash "${test_script}"
done

python3 -m compileall -q "${ROOT}/src"
"${ROOT}/runtime-env" validate
git -C "${ROOT}" diff --check

echo "PASS: full runtime-env suite"
