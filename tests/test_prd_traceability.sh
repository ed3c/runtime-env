#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECK="${ROOT}/tests/check_prd_traceability.py"
GRAPH="${ROOT}/prd/requirements.json"

python3 "${CHECK}" --root "${ROOT}" --graph "${GRAPH}"

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

expect_fail() {
  local name="$1"
  local graph="$2"
  if python3 "${CHECK}" --root "${ROOT}" --graph "${graph}" >/dev/null 2>&1; then
    echo "FAIL: planted ${name} traceability defect was accepted" >&2
    exit 1
  fi
}

python3 - "${GRAPH}" "${TMP}/duplicate.json" <<'PY'
import copy, json, sys
source = json.load(open(sys.argv[1]))
source["requirements"].append(copy.deepcopy(source["requirements"][0]))
json.dump(source, open(sys.argv[2], "w"))
PY
expect_fail duplicate-id "${TMP}/duplicate.json"

python3 - "${GRAPH}" "${TMP}/missing-path.json" <<'PY'
import json, sys
source = json.load(open(sys.argv[1]))
source["requirements"][0]["implementation_paths"] = ["does/not/exist"]
json.dump(source, open(sys.argv[2], "w"))
PY
expect_fail missing-path "${TMP}/missing-path.json"

python3 - "${GRAPH}" "${TMP}/fake-live.json" <<'PY'
import json, sys
source = json.load(open(sys.argv[1]))
source["requirements"][0]["closure"] = "LIVE_CLOSED"
source["requirements"][0]["live_evidence"] = []
json.dump(source, open(sys.argv[2], "w"))
PY
expect_fail fake-live-closure "${TMP}/fake-live.json"

echo "PASS: PRD traceability planted controls"
