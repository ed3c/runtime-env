#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT
repo="${scratch}/repo"
mkdir -p "${repo}/.agents/skills/upper/scripts" \
  "${repo}/.agents/skills/lower/tests" "${repo}/kb-ingest" "${repo}/indexing"
printf '%s\n' '# Upper' 'Run `kb-ingest/verify.sh` with `${DEMO_TOKEN:-}`.' > "${repo}/.agents/skills/upper/SKILL.md"
printf '%s\n' '#!/bin/sh' 'exit 0' > "${repo}/.agents/skills/upper/scripts/run.sh"
printf '%s\n' '# Lower' 'Use `indexing/ingest.py`.' > "${repo}/.agents/skills/lower/skill.md"
printf '%s\n' '#!/bin/sh' 'exit 0' > "${repo}/.agents/skills/lower/tests/selftest.sh"
printf '%s\n' '#!/bin/sh' 'exit 0' > "${repo}/kb-ingest/verify.sh"
printf '%s\n' 'pass' > "${repo}/indexing/ingest.py"

inventory="$(${ROOT}/runtime-env inventory skills --repo-root "${repo}")"
python3 -c '
import json, sys
value = json.load(sys.stdin)
assert value["skill_count"] == 2
by_id = {item["id"]: item for item in value["skills"]}
assert by_id["upper"]["runtime_modules"] == [".agents/skills/upper/scripts/run.sh"]
assert by_id["lower"]["assertion_modules"] == [".agents/skills/lower/tests/selftest.sh"]
assert by_id["upper"]["repo_modules"] == ["kb-ingest/verify.sh"]
assert by_id["lower"]["repo_modules"] == ["indexing/ingest.py"]
assert by_id["upper"]["environment_names"] == ["DEMO_TOKEN"]
' <<< "${inventory}"

echo 'PASS: skill inventory includes lowercase manifests and physical modules'
