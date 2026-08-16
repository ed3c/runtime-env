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
{"schema":"runtime-env/github-monitor-registry/v1","repositories":{"example/repo":{"visibility_class":"public","required_phases":{"2":["STACK_DELIVERY"]}}}}
JSON
cat > "${TMP}/issues.json" <<'JSON'
[
 {"number":1,"state":"closed","title":"closed blocker","body":"MUST NOT LEAK"},
 {"number":2,"state":"open","title":"work","body":"PRIVATE BODY MUST NOT LEAK","labels":[{"name":"x"}]},
 {"number":3,"state":"open","title":"pr","pull_request":{"url":"ignored"}}
]
JSON
cat > "${TMP}/deps.json" <<'JSON'
{"example/repo#2":[{"number":1,"state":"closed","title":"closed blocker","body":"MUST NOT LEAK","repository_url":"https://api.github.com/repos/example/repo"}]}
JSON

run_monitor() {
  python3 "${ROOT}/scripts/github-control-plane-monitor.py" fixture \
    --registry "${TMP}/registry.json" --repository example/repo \
    --skills-root "${skills}" --skills-commit "${skills_sha}" \
    --state-root "${TMP}/state" --issues-fixture "${TMP}/issues.json" \
    --dependencies-fixture "${TMP}/deps.json"
}
run_monitor > "${TMP}/receipt.out"
python3 - "${TMP}/state/snapshot.json" "${TMP}/state/plan.json" "${TMP}/state/receipt.json" "${TMP}/state/handoff.json" <<'PY'
import json,sys
s,p,r,h=[json.load(open(x)) for x in sys.argv[1:]]
assert s['packet']==[
 {'repository':'example/repo','number':1,'state':'closed','depends_on':[],'required_phases':[]},
 {'repository':'example/repo','number':2,'state':'open','depends_on':['example/repo#1'],'required_phases':['STACK_DELIVERY']}
],s
encoded=json.dumps(s)
assert 'PRIVATE BODY' not in encoded and 'MUST NOT LEAK' not in encoded
assert p['automatic_merge'] is False and p['automatic_conflict_resolution'] is False
assert all(x['execution_state']=='NOT_EXERCISED' for x in p['issue_plans'].values())
assert r['provider_permission']=='issues:read' and r['provider_writes'] is False
assert r['worker_execution']=='NOT_EXERCISED' and r['terminal_state']=='READY'
assert r['deduplication']=='NEW' and len(r['run_identity_sha256'])==64
assert h['admission']=='READY_FOR_SCHEDULER_REVIEW'
assert h['launch_worker'] is False and h['worker_execution']=='NOT_EXERCISED'
PY

# Same exact subject is suppressed, without rewriting the admitted receipt.
receipt_before="$(sha256sum "${TMP}/state/receipt.json" | awk '{print $1}')"
run_monitor > "${TMP}/duplicate.out"
receipt_after="$(sha256sum "${TMP}/state/receipt.json" | awk '{print $1}')"
test "${receipt_before}" = "${receipt_after}"
grep -q 'SUPPRESSED_DUPLICATE' "${TMP}/duplicate.out"

# Overlap lock refuses a second publisher and preserves prior state.
touch "${TMP}/state/monitor.lock"
if run_monitor >/dev/null 2>&1; then echo 'FAIL: overlapping run was accepted' >&2; exit 1; fi
rm "${TMP}/state/monitor.lock"
test "$(sha256sum "${TMP}/state/receipt.json" | awk '{print $1}')" = "${receipt_before}"

# A failed candidate does not replace the previously admitted state.
printf '{}\n' > "${TMP}/missing-deps.json"
if python3 "${ROOT}/scripts/github-control-plane-monitor.py" fixture --registry "${TMP}/registry.json" --repository example/repo --skills-root "${skills}" --skills-commit "${skills_sha}" --state-root "${TMP}/state" --issues-fixture "${TMP}/issues.json" --dependencies-fixture "${TMP}/missing-deps.json" >/dev/null 2>&1; then
  echo 'FAIL: missing dependency response was accepted' >&2; exit 1
fi
test "$(sha256sum "${TMP}/state/receipt.json" | awk '{print $1}')" = "${receipt_before}"

cat > "${TMP}/cross-deps.json" <<'JSON'
{"example/repo#2":[{"number":9,"state":"open","repository_url":"https://api.github.com/repos/other/repo"}]}
JSON
if python3 "${ROOT}/scripts/github-control-plane-monitor.py" fixture --registry "${TMP}/registry.json" --repository example/repo --skills-root "${skills}" --skills-commit "${skills_sha}" --state-root "${TMP}/bad2" --issues-fixture "${TMP}/issues.json" --dependencies-fixture "${TMP}/cross-deps.json" >/dev/null 2>&1; then
  echo 'FAIL: cross-repository incomplete closure was accepted' >&2; exit 1
fi
if python3 "${ROOT}/scripts/github-control-plane-monitor.py" fixture --registry "${TMP}/registry.json" --repository example/repo --skills-root "${skills}" --skills-commit "0000000000000000000000000000000000000000" --state-root "${TMP}/bad3" --issues-fixture "${TMP}/issues.json" --dependencies-fixture "${TMP}/deps.json" >/dev/null 2>&1; then
  echo 'FAIL: stale skills-shared subject was accepted' >&2; exit 1
fi
if python3 "${ROOT}/scripts/github-control-plane-monitor.py" fixture --registry "${TMP}/registry.json" --repository evil/repo --skills-root "${skills}" --skills-commit "${skills_sha}" --state-root "${TMP}/bad4" --issues-fixture "${TMP}/issues.json" --dependencies-fixture "${TMP}/deps.json" >/dev/null 2>&1; then
  echo 'FAIL: non-allowlisted repository was accepted' >&2; exit 1
fi
python3 -m json.tool "${ROOT}/contracts/github-monitor-registry.schema.json" >/dev/null

echo 'PASS: read-only GitHub monitor dedup, locking, failure preservation, and scheduler handoff'
