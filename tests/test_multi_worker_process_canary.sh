#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT
repo="${TMP}/consumer"
mkdir -p "${repo}"
git -C "${repo}" init -q
git -C "${repo}" config user.name test
git -C "${repo}" config user.email test@example.invalid
printf 'base\n' > "${repo}/README.md"
git -C "${repo}" add README.md && git -C "${repo}" commit -qm base
head="$(git -C "${repo}" rev-parse HEAD)"

cat > "${TMP}/plan.json" <<'JSON'
{
  "schema":"runtime-env/multi-worker-canary-plan/v1",
  "tasks":[
    {"task_id":"alpha","owned_path":"out/alpha.txt","delay_ms":250,"interrupt_once":true},
    {"task_id":"beta","owned_path":"out/beta.txt","delay_ms":250,"interrupt_once":false}
  ]
}
JSON
python3 "${ROOT}/scripts/multi-worker-canary.py" run --repository "${repo}" --expected-head "${head}" --plan "${TMP}/plan.json" --state-root "${TMP}/state" > "${TMP}/out.json"
python3 - "${TMP}/state/receipt.json" "${repo}" "${head}" <<'PY'
import json,os,subprocess,sys
p=json.load(open(sys.argv[1])); repo=sys.argv[2]; head=sys.argv[3]
assert p['schema']=='runtime-env/multi-worker-process-canary-receipt/v1'
assert p['repository_head']==head and p['task_count']==2 and p['overlap_observed'] is True
assert p['synthetic_runtime']=='PASS' and p['admitted_consumer']=='NOT_EXERCISED'
assert p['git_town']=='NOT_EXERCISED' and p['forgejo']=='NOT_EXERCISED' and p['merge_authority'] is False
assert p['residue']=='CLEAN'
by={x['task_id']:x for x in p['tasks']}
assert by['alpha']['first_exit']==75 and by['alpha']['resume_exit']==0 and by['alpha']['resume_pid']
assert by['beta']['first_exit']==0 and by['beta']['resume_pid'] is None
assert all(len(x['checkpoint_sha256'])==64 and len(x['output_sha256'])==64 for x in p['tasks'])
assert oct(os.stat(sys.argv[1]).st_mode & 0o777)=='0o600'
assert subprocess.check_output(['git','-C',repo,'rev-parse','HEAD'],text=True).strip()==head
assert subprocess.check_output(['git','-C',repo,'status','--porcelain'],text=True).strip()==''
assert subprocess.check_output(['git','-C',repo,'worktree','list','--porcelain'],text=True).count('worktree ')==1
PY

# Exact repository subject mismatch refuses mutation.
if python3 "${ROOT}/scripts/multi-worker-canary.py" run --repository "${repo}" --expected-head 0000000000000000000000000000000000000000 --plan "${TMP}/plan.json" --state-root "${TMP}/bad1" >/dev/null 2>&1; then
  echo 'FAIL: wrong consumer head accepted' >&2; exit 1
fi

# Owned paths must be unique and cannot escape the worktree.
cat > "${TMP}/bad-plan.json" <<'JSON'
{"schema":"runtime-env/multi-worker-canary-plan/v1","tasks":[
 {"task_id":"a","owned_path":"../escape","delay_ms":1,"interrupt_once":false},
 {"task_id":"b","owned_path":"ok.txt","delay_ms":1,"interrupt_once":false}
]}
JSON
if python3 "${ROOT}/scripts/multi-worker-canary.py" run --repository "${repo}" --expected-head "${head}" --plan "${TMP}/bad-plan.json" --state-root "${TMP}/bad2" >/dev/null 2>&1; then
  echo 'FAIL: escaping owned path accepted' >&2; exit 1
fi

# No arbitrary command field is admitted.
cat > "${TMP}/command-plan.json" <<'JSON'
{"schema":"runtime-env/multi-worker-canary-plan/v1","tasks":[
 {"task_id":"a","owned_path":"a.txt","delay_ms":1,"interrupt_once":false,"command":"rm -rf /"},
 {"task_id":"b","owned_path":"b.txt","delay_ms":1,"interrupt_once":false}
]}
JSON
if python3 "${ROOT}/scripts/multi-worker-canary.py" run --repository "${repo}" --expected-head "${head}" --plan "${TMP}/command-plan.json" --state-root "${TMP}/bad3" >/dev/null 2>&1; then
  echo 'FAIL: arbitrary command field accepted' >&2; exit 1
fi

echo 'PASS: real subprocess overlap, linked worktrees, interruption/resume, and cleanup selftest'
