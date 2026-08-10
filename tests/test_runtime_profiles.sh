#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

testflight="$(${ROOT}/runtime-env list --profile ios-testflight-ship-local)"
for name in APPLE_TEAM_ID ASC_KEY_ID ASC_ISSUER_ID ASC_KEY_PATH JAVA_HOME; do
  [[ "${testflight}" == *"${name}"* ]]
done

wiki="$(${ROOT}/runtime-env list --profile repo-wiki-converge-local)"
for name in AGY_TIMEOUT ANTIGRAVITY_REPO_ROOT; do
  [[ "${wiki}" == *"${name}"* ]]
done

proof="$(${ROOT}/runtime-env list --profile bettor-arena-proof-local)"
for name in ANTIGRAVITY_PEER SKILL_BETTOR_PEER; do
  [[ "${proof}" == *"${name}"* ]]
done

agy="$(${ROOT}/runtime-env list --profile agy-gemini36-flash-high-local)"
[[ "${agy}" == *$'AGY_MODEL\tgemini-3.6-flash-high'* ]]
[[ "${agy}" == *$'AGY_EFFORT\thigh'* ]]

browser="$(${ROOT}/runtime-env list --profile gemini-conversation-research-local)"
[[ "${browser}" == *$'DR_CDP_URL\thttp://127.0.0.1:9333'* ]]

echo 'PASS: physical runtime profiles expose required names'
