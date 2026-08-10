#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "${ROOT}/scripts/verify-jdk-runtime.py" --selftest

local_render="$(${ROOT}/runtime-env render --profile java-build-local --format dotenv)"
[[ "${local_render}" == *'JAVA_HOME='* ]]
[[ "${local_render}" == *'JAVA_VERSION=21'* ]]

cloud_render="$(${ROOT}/runtime-env render --profile java-build-cloud --format github-actions)"
[[ "${cloud_render}" == *'JAVA_VERSION: "21"'* ]]
[[ "${cloud_render}" == *'CLOUD_JDK_DISTRIBUTION: "temurin"'* ]]

workload="$(${ROOT}/runtime-env workload show --id local-jdk-verify)"
[[ "${workload}" == *'verify'* ]]

echo 'PASS: JDK 21 has separate local and cloud runtime contracts'
