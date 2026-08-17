#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

skills="${TMP}/skills-shared"
mkdir -p "${skills}/skills/agentic-tech-lead-orchestration/references" "${skills}/skills/agentic-tech-lead-orchestration/scripts"
git -C "${skills}" init -q
git -C "${skills}" config user.name test
git -C "${skills}" config user.email test@example.invalid
printf '{"schema":"fixture-canonical-scheduler"}\n' > "${skills}/skills/agentic-tech-lead-orchestration/references/scheduler-lifecycle.schema.json"
cat > "${skills}/skills/agentic-tech-lead-orchestration/scripts/assert_scheduler_lifecycle.py" <<'PY'
#!/usr/bin/env python3
import argparse,json,sys
p=argparse.ArgumentParser(); p.add_argument('--lifecycle',required=True); a=p.parse_args(); d=json.load(open(a.lifecycle))
if d.get('schema')!='agentic-tech-lead/scheduler-lifecycle/v1' or d.get('evidence_state')=='PASS': sys.exit(2)
ids=set(); active={}
for x in d.get('attempts',[]):
    if x['attempt_id'] in ids or x['consumed']>x['budget']: sys.exit(2)
    ids.add(x['attempt_id'])
for x in d.get('leases',[]):
    if x['active']:
        if x['resource'] in active and active[x['resource']]!=x['attempt_id']: sys.exit(2)
        active[x['resource']]=x['attempt_id']
for r in d.get('results',[]):
    item=next((x for x in d['attempts'] if x['attempt_id']==r['attempt_id']),None)
    if not item: sys.exit(2)
    if r['accepted'] and (r['oracle']!='PASS' or item['state'] not in {'RESULT_READY','RESULT_VERIFIED','INTEGRATED'}): sys.exit(2)
print('{"verdict":"PASS"}')
PY
chmod +x "${skills}/skills/agentic-tech-lead-orchestration/scripts/assert_scheduler_lifecycle.py"
git -C "${skills}" add . && git -C "${skills}" commit -qm fixture
skills_sha="$(git -C "${skills}" rev-parse HEAD)"

cat > "${TMP}/initial.json" <<JSON
{
  "schema":"agentic-tech-lead/scheduler-lifecycle/v1",
  "repository":{"id":"example/repo","commit":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","tree":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
  "task_graph_digest":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "attempts":[],"leases":[],"checkpoints":[],"results":[],"evidence_state":"NOT_EXERCISED"
}
JSON
cat > "${TMP}/events.json" <<'JSON'
[
  {"type":"CREATE_ATTEMPT","at":1,"task_id":"a","attempt_id":"a1","parent_attempt_id":null,"budget":10,"worktree":"/tmp/wt-a1","head":"1111111111111111111111111111111111111111"},
  {"type":"ADVANCE","at":2,"attempt_id":"a1","state":"ADMITTED"},
  {"type":"ADVANCE","at":3,"attempt_id":"a1","state":"ASSIGNED"},
  {"type":"LEASE","at":4,"attempt_id":"a1","resource":"src/a","expires_at":10},
  {"type":"ADVANCE","at":5,"attempt_id":"a1","state":"RUNNING"},
  {"type":"CONSUME","at":6,"attempt_id":"a1","amount":3},
  {"type":"CHECKPOINT","at":7,"attempt_id":"a1","checkpoint_id":"cp-a1","artifact_digest":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"},
  {"type":"HEARTBEAT","at":8,"attempt_id":"a1","expires_at":20},
  {"type":"ADVANCE","at":9,"attempt_id":"a1","state":"RUNNING"},
  {"type":"RESULT","at":10,"attempt_id":"a1","result_digest":"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee","oracle":"PASS"},
  {"type":"VERIFY_RESULT","at":11,"attempt_id":"a1"},
  {"type":"ADVANCE","at":12,"attempt_id":"a1","state":"INTEGRATED"},

  {"type":"CREATE_ATTEMPT","at":1,"task_id":"b","attempt_id":"b1","parent_attempt_id":null,"budget":8,"worktree":"/tmp/wt-b1","head":"2222222222222222222222222222222222222222"},
  {"type":"ADVANCE","at":2,"attempt_id":"b1","state":"ADMITTED"},
  {"type":"ADVANCE","at":3,"attempt_id":"b1","state":"ASSIGNED"},
  {"type":"LEASE","at":4,"attempt_id":"b1","resource":"src/b","expires_at":6},
  {"type":"ADVANCE","at":5,"attempt_id":"b1","state":"RUNNING"},
  {"type":"TICK","at":7},
  {"type":"CREATE_ATTEMPT","at":8,"task_id":"b","attempt_id":"b2","parent_attempt_id":"b1","budget":8,"worktree":"/tmp/wt-b2","head":"3333333333333333333333333333333333333333"},
  {"type":"ADVANCE","at":9,"attempt_id":"b2","state":"ADMITTED"},
  {"type":"ADVANCE","at":10,"attempt_id":"b2","state":"ASSIGNED"},
  {"type":"LEASE","at":11,"attempt_id":"b2","resource":"src/b","expires_at":30},
  {"type":"ADVANCE","at":12,"attempt_id":"b2","state":"RUNNING"},
  {"type":"TERMINATE","at":13,"attempt_id":"b2","state":"STRAGGLER_DETACHED"},
  {"type":"CREATE_ATTEMPT","at":14,"task_id":"b","attempt_id":"b3","parent_attempt_id":"b2","budget":8,"worktree":"/tmp/wt-b3","head":"4444444444444444444444444444444444444444"}
]
JSON

python3 "${ROOT}/scripts/multi-worker-scheduler.py" contract --skills-root "${skills}" --skills-commit "${skills_sha}" > "${TMP}/contract.json"
python3 "${ROOT}/scripts/multi-worker-scheduler.py" reduce --skills-root "${skills}" --skills-commit "${skills_sha}" --initial "${TMP}/initial.json" --events "${TMP}/events.json" --state-root "${TMP}/state" > "${TMP}/receipt.out"
python3 - "${TMP}/state/lifecycle.json" "${TMP}/state/receipt.json" <<'PY'
import json,os,sys
s,r=[json.load(open(x)) for x in sys.argv[1:]]
by={x['attempt_id']:x for x in s['attempts']}
assert by['a1']['state']=='INTEGRATED'
assert by['b1']['state']=='LEASE_EXPIRED'
assert by['b2']['state']=='STRAGGLER_DETACHED'
assert by['b3']['parent_attempt_id']=='b2'
assert next(x for x in s['results'] if x['attempt_id']=='a1')['accepted'] is True
assert all(not x['active'] for x in s['leases'] if x['attempt_id'] in {'a1','b1','b2'})
assert r['worker_execution']=='NOT_EXERCISED' and r['process_execution']=='NOT_EXERCISED' and r['worktree_execution']=='NOT_EXERCISED'
assert r['merge_authority'] is False and r['terminal_state']=='READY'
assert oct(os.stat(sys.argv[2]).st_mode & 0o777)=='0o600'
PY

# Stale exact skills-shared subject must fail closed.
if python3 "${ROOT}/scripts/multi-worker-scheduler.py" contract --skills-root "${skills}" --skills-commit 0000000000000000000000000000000000000000 >/dev/null 2>&1; then
  echo 'FAIL: stale skills-shared subject accepted' >&2; exit 1
fi

# Same resource cannot have two active writers.
cat > "${TMP}/double.json" <<'JSON'
[
 {"type":"CREATE_ATTEMPT","at":1,"task_id":"x","attempt_id":"x1","parent_attempt_id":null,"budget":1,"worktree":"/tmp/x1","head":"5555555555555555555555555555555555555555"},
 {"type":"ADVANCE","at":2,"attempt_id":"x1","state":"ADMITTED"}, {"type":"ADVANCE","at":3,"attempt_id":"x1","state":"ASSIGNED"},
 {"type":"LEASE","at":4,"attempt_id":"x1","resource":"same","expires_at":20},
 {"type":"CREATE_ATTEMPT","at":1,"task_id":"y","attempt_id":"y1","parent_attempt_id":null,"budget":1,"worktree":"/tmp/y1","head":"6666666666666666666666666666666666666666"},
 {"type":"ADVANCE","at":2,"attempt_id":"y1","state":"ADMITTED"}, {"type":"ADVANCE","at":3,"attempt_id":"y1","state":"ASSIGNED"},
 {"type":"LEASE","at":4,"attempt_id":"y1","resource":"same","expires_at":20}
]
JSON
if python3 "${ROOT}/scripts/multi-worker-scheduler.py" reduce --skills-root "${skills}" --skills-commit "${skills_sha}" --initial "${TMP}/initial.json" --events "${TMP}/double.json" --state-root "${TMP}/bad1" >/dev/null 2>&1; then
  echo 'FAIL: double writer lease accepted' >&2; exit 1
fi

# Budget overrun fails before publication.
cat > "${TMP}/budget.json" <<'JSON'
[
 {"type":"CREATE_ATTEMPT","at":1,"task_id":"x","attempt_id":"x1","parent_attempt_id":null,"budget":1,"worktree":"/tmp/x1","head":"7777777777777777777777777777777777777777"},
 {"type":"CONSUME","at":2,"attempt_id":"x1","amount":2}
]
JSON
if python3 "${ROOT}/scripts/multi-worker-scheduler.py" reduce --skills-root "${skills}" --skills-commit "${skills_sha}" --initial "${TMP}/initial.json" --events "${TMP}/budget.json" --state-root "${TMP}/bad2" >/dev/null 2>&1; then
  echo 'FAIL: budget overrun accepted' >&2; exit 1
fi

# Retry lineage must stay in the same task and start only after terminal parent.
cat > "${TMP}/retry.json" <<'JSON'
[
 {"type":"CREATE_ATTEMPT","at":1,"task_id":"x","attempt_id":"x1","parent_attempt_id":null,"budget":1,"worktree":"/tmp/x1","head":"8888888888888888888888888888888888888888"},
 {"type":"CREATE_ATTEMPT","at":2,"task_id":"x","attempt_id":"x2","parent_attempt_id":"x1","budget":1,"worktree":"/tmp/x2","head":"9999999999999999999999999999999999999999"}
]
JSON
if python3 "${ROOT}/scripts/multi-worker-scheduler.py" reduce --skills-root "${skills}" --skills-commit "${skills_sha}" --initial "${TMP}/initial.json" --events "${TMP}/retry.json" --state-root "${TMP}/bad3" >/dev/null 2>&1; then
  echo 'FAIL: retry from non-terminal parent accepted' >&2; exit 1
fi

# Workload/catalog JSON remains valid and fixture receipts never claim live execution.
python3 -m json.tool "${ROOT}/modules/multi-worker-scheduler.json" >/dev/null
python3 -m json.tool "${ROOT}/profiles/repository-control-plane-scheduler-local.json" >/dev/null
python3 -m json.tool "${ROOT}/workloads/repository-control-plane-scheduler.json" >/dev/null

echo 'PASS: bounded multi-Worker scheduler lifecycle reducer and negative controls'
