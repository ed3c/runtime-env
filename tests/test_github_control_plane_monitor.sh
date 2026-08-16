#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

skills="${TMP}/skills-shared"
mkdir -p "${skills}/skills/shared-skills-infra/scripts" "${skills}/skills/shared-skills-infra/references"
git -C "${skills}" init -q
git -C "${skills}" config user.name test
git -C "${skills}" config user.email test@example.invalid
cat > "${skills}/skills/shared-skills-infra/scripts/repository_control_plane.py" <<'PY'
#!/usr/bin/env python3
import argparse,json
p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True); m=sub.add_parser('monitor-plan'); m.add_argument('--issues',required=True); a=p.parse_args()
items=json.load(open(a.issues)); ids=[f"{x['repository']}#{x['number']}" for x in items if x.get('state','open')=='open']
plans={i:{'phase_dispositions':[], 'required_receipts':[], 'execution_state':'NOT_EXERCISED'} for i in ids}
print(json.dumps({'schema':'repository-control-plane-monitor-plan/v1','issues':ids,'waves':[ids] if ids else [],'issue_plans':plans,'automatic_merge':False,'automatic_conflict_resolution':False}))
PY
chmod +x "${skills}/skills/shared-skills-infra/scripts/repository_control_plane.py"
printf '{"schema":"fixture"}\n' > "${skills}/skills/shared-skills-infra/references/repository-control-plane-monitor-plan.v1.schema.json"
git -C "${skills}" add . && git -C "${skills}" commit -qm fixture
skills_sha="$(git -C "${skills}" rev-parse HEAD)"

cat > "${TMP}/registry.json" <<'JSON'
{
  "schema":"runtime-env/github-monitor-registry/v1",
  "repositories":{
    "example/repo":{"visibility_class":"public","required_phases":{"2":["STACK_DELIVERY"]}}
  }
}
JSON
cat > "${TMP}/issues.json" <<'JSON'
[
  {"number":1,"state":"closed","title":"closed blocker","body":"MUST NOT LEAK"},
  {"number":2,"state":"open","title":"work","body":"PRIVATE BODY MUST NOT LEAK","labels":[{"name":"x"}]},
  {"number":3,"state":"open","title":"pr","pull_request":{"url":"ignored"}}
]
JSON
cat > "${TMP}/deps.json" <<'JSON'
{
  "example/repo#2":[
    {"number":1,"state":"closed","title":"closed blocker","body":"MUST NOT LEAK","repository_url":"https://api.github.com/repos/example/repo"}
  ]
}
JSON

python3 "${ROOT}/scripts/github-control-plane-monitor.py" fixture \
  --registry "${TMP}/registry.json" --repository example/repo \
  --skills-root "${skills}" --skills-commit "${skills_sha}" \
  --state-root "${TMP}/state" --issues-fixture "${TMP}/issues.json" \
  --dependencies-fixture "${TMP}/deps.json" > "${TMP}/receipt.out"

python3 - "${TMP}/state/snapshot.json" "${TMP}/state/plan.json" "${TMP}/state/receipt.json" <<'PY'
import json,sys
s,p,r=[json.load(open(x)) for x in sys.argv[1:]]
assert s['packet']==[
 {'repository':'example/repo','number':1,'state':'closed','depends_on':[],'required_phases':[]},
 {'repository':'example/repo','number':2,'state':'open','depends_on':['example/repo#1'],'required_phases':['STACK_DELIVERY']}
],s
encoded=json.dumps(s)
assert 'PRIVATE BODY' not in encoded and 'MUST NOT LEAK' not in encoded
assert p['automatic_merge'] is False and p['automatic_conflict_resolution'] is False
assert all(x['execution_state']=='NOT_EXERCISED' for x in p['issue_plans'].values())
assert r['provider_permission']=='issues:read'
assert r['provider_writes'] is False
assert r['worker_execution']=='NOT_EXERCISED'
assert r['terminal_state']=='READY'
PY

# Missing dependency response for an open issue cannot be converted into an empty graph.
printf '{}\n' > "${TMP}/missing-deps.json"
if python3 "${ROOT}/scripts/github-control-plane-monitor.py" fixture --registry "${TMP}/registry.json" --repository example/repo --skills-root "${skills}" --skills-commit "${skills_sha}" --state-root "${TMP}/bad" --issues-fixture "${TMP}/issues.json" --dependencies-fixture "${TMP}/missing-deps.json" >/dev/null 2>&1; then
  echo 'FAIL: missing dependency response was accepted' >&2; exit 1
fi

# Cross-repository blockers require a separate exact monitor subject; never infer incomplete closure.
cat > "${TMP}/cross-deps.json" <<'JSON'
{"example/repo#2":[{"number":9,"state":"open","repository_url":"https://api.github.com/repos/other/repo"}]}
JSON
if python3 "${ROOT}/scripts/github-control-plane-monitor.py" fixture --registry "${TMP}/registry.json" --repository example/repo --skills-root "${skills}" --skills-commit "${skills_sha}" --state-root "${TMP}/bad2" --issues-fixture "${TMP}/issues.json" --dependencies-fixture "${TMP}/cross-deps.json" >/dev/null 2>&1; then
  echo 'FAIL: cross-repository incomplete closure was accepted' >&2; exit 1
fi

# Stale compiler subject fails closed.
if python3 "${ROOT}/scripts/github-control-plane-monitor.py" fixture --registry "${TMP}/registry.json" --repository example/repo --skills-root "${skills}" --skills-commit "0000000000000000000000000000000000000000" --state-root "${TMP}/bad3" --issues-fixture "${TMP}/issues.json" --dependencies-fixture "${TMP}/deps.json" >/dev/null 2>&1; then
  echo 'FAIL: stale skills-shared subject was accepted' >&2; exit 1
fi

# Repository must be allowlisted; model-supplied arbitrary repo is refused.
if python3 "${ROOT}/scripts/github-control-plane-monitor.py" fixture --registry "${TMP}/registry.json" --repository evil/repo --skills-root "${skills}" --skills-commit "${skills_sha}" --state-root "${TMP}/bad4" --issues-fixture "${TMP}/issues.json" --dependencies-fixture "${TMP}/deps.json" >/dev/null 2>&1; then
  echo 'FAIL: non-allowlisted repository was accepted' >&2; exit 1
fi

python3 -m json.tool "${ROOT}/contracts/github-monitor-registry.schema.json" >/dev/null

echo 'PASS: read-only GitHub metadata adapter and exact monitor handoff'
