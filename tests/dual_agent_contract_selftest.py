#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/'contracts'/'dual-agent'; E=ROOT/'examples'/'dual-agent'; M=ROOT/'tests'/'fixtures'/'dual-agent'/'mutation-registry.json'
METHOD_COMMIT='7e33890e9e3763e0cd6188fdc68fce96e1caaba3'; METHOD_TREE='7e2293b52b48394e4aa905d61fb5782f55110a67'
METHOD_ID='https://skills-shared.invalid/agentic-tech-lead-orchestration/dual-agent-offload/method-contract.v1.schema.json'; METHOD_SHA='83e1393a87c7caee5bc7cb8772b3706d3114b568b11a916609dccf723b251daf'
LOGICAL={'runtime-env/dual-agent/offload-job/v1':'offload-job.v1.schema.json','runtime-env/dual-agent/capability-grant/v1':'capability-grant.v1.schema.json','runtime-env/dual-agent/effect-intent/v1':'effect-intent.v1.schema.json','runtime-env/dual-agent/artifact-manifest/v1':'artifact-manifest.v1.schema.json','runtime-env/dual-agent/execution-receipt/v1':'execution-receipt.v1.schema.json'}
FAIL={'R01':'METHOD_SUBJECT_MISMATCH','R02':'DUPLICATE_OR_UNKNOWN_SCHEMA_ID','R03':'UNKNOWN_PROPERTY_OR_EXECUTION_WIDENING','R04':'MUTABLE_SUBJECT','R05':'JOB_RECEIPT_SOURCE_MISMATCH','R06':'LANE_SUBSTITUTION','R07':'LOCAL_ONLY_REMOTE_EGRESS','R08':'SECRET_SESSION_OR_HOST_PATH','R09':'WRITE_WITHOUT_EFFECT_IDENTITY','R10':'IDEMPOTENCY_COLLISION','R11':'SUCCESS_WITH_CLEANUP_FAILURE','R12':'TERMINAL_STATE_COLLAPSE','R13':'ARTIFACT_WITHOUT_DIGEST_OR_READBACK','R14':'BROWSER_AS_API_EVIDENCE','R15':'STATIC_FIXTURE_AS_LIVE_PASS','R16':'MANIFEST_SCHEMA_DIGEST_DRIFT','R17':'UNKNOWN_EXTERNAL_EFFECT_AS_SUCCESS','R18':'WORKER_OR_PROVIDER_SELF_PROMOTION'}
H40=re.compile(r'^[0-9a-f]{40}$'); H64=re.compile(r'^[0-9a-f]{64}$')
class Refusal(Exception): pass
def refuse(c,d=''): raise Refusal(c+(': '+d if d else ''))
def load(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def exact(s):
    if not isinstance(s,dict) or not H40.fullmatch(str(s.get('commit',''))) or not H40.fullmatch(str(s.get('tree',''))) or '/' not in str(s.get('repository','')): refuse('MUTABLE_SUBJECT')
def no_extra(d, keys):
    if set(d)-set(keys): refuse('UNKNOWN_PROPERTY_OR_EXECUTION_WIDENING')
def manifest(m):
    ms=m.get('method_subject',{})
    if (ms.get('repository'),ms.get('commit'),ms.get('tree'),ms.get('id'),ms.get('sha256'))!=('ed3c/skills-shared',METHOD_COMMIT,METHOD_TREE,METHOD_ID,METHOD_SHA): refuse('METHOD_SUBJECT_MISMATCH')
    entries=m.get('schemas',[]); ids=[x.get('logical_id') for x in entries]
    if len(ids)!=len(set(ids)) or set(ids)!=set(LOGICAL): refuse('DUPLICATE_OR_UNKNOWN_SCHEMA_ID')
    for x in entries:
        p=ROOT/x['path']
        if p.name!=LOGICAL[x['logical_id']] or not p.is_file() or sha(p)!=x.get('sha256') or load(p).get('$id')!=x.get('id'): refuse('MANIFEST_SCHEMA_DIGEST_DRIFT')
    basis={'method_sha256':METHOD_SHA,'schemas':[(x['logical_id'],x['path'],x['id'],x['sha256']) for x in entries]}
    if canonical(basis)!=m.get('contract_set_digest'): refuse('MANIFEST_SCHEMA_DIGEST_DRIFT')
    return m['contract_set_digest']
def grant(g):
    no_extra(g,{'schema','grant_id','subject_identity_ref','tenant_scope','audience','capabilities','policy_digest','issued_at','expires_at','revocation_state','secret_handle_ids','contract_set_ref'})
    if g.get('schema')!='runtime-env/dual-agent/capability-grant/v1' or not g.get('capabilities') or any('*' in x for x in g['capabilities']) or g.get('audience') in ('','*','ANY'): refuse('UNKNOWN_PROPERTY_OR_EXECUTION_WIDENING')
    if any(not str(x).startswith('secret://') for x in g.get('secret_handle_ids',[])): refuse('SECRET_SESSION_OR_HOST_PATH')
def job(j):
    no_extra(j,{'schema','job_id','idempotency_key','tenant_scope','requester_identity_ref','source_subject','goal','non_goals','deadline','budget','retry_policy','data_classification','side_effect_class','execution_lane','capability_grant_ref','bindings','allowlists','secret_handles','approval_requirement','artifact_requirements','trace_id','method_contract','contract_set_ref'})
    if j.get('schema')!='runtime-env/dual-agent/offload-job/v1': refuse('DUPLICATE_OR_UNKNOWN_SCHEMA_ID')
    exact(j.get('source_subject'))
    if j.get('method_contract')!={'id':METHOD_ID,'sha256':METHOD_SHA}: refuse('METHOD_SUBJECT_MISMATCH')
    a=j.get('allowlists',{})
    if j.get('data_classification')=='LOCAL_ONLY' and (j.get('execution_lane')!='LOCAL' or a.get('network_origins')): refuse('LOCAL_ONLY_REMOTE_EGRESS')
    for p in a.get('filesystem_paths',[]):
        if p.startswith('/') or '..' in p.split('/'): refuse('SECRET_SESSION_OR_HOST_PATH')
    if any(not str(x).startswith('secret://') for x in j.get('secret_handles',[])): refuse('SECRET_SESSION_OR_HOST_PATH')
def effect(e,j):
    if e.get('schema')!='runtime-env/dual-agent/effect-intent/v1' or e.get('job_id')!=j.get('job_id') or e.get('idempotency_key')!=j.get('idempotency_key'): refuse('WRITE_WITHOUT_EFFECT_IDENTITY')
    if j.get('side_effect_class')=='READ_ONLY': refuse('WRITE_WITHOUT_EFFECT_IDENTITY')
    if e.get('side_effect_class')!=j.get('side_effect_class') or j.get('approval_requirement')=='NONE': refuse('WRITE_WITHOUT_EFFECT_IDENTITY')
def artifact(a,job_id=None,attempt_id=None):
    if a.get('schema')!='runtime-env/dual-agent/artifact-manifest/v1': refuse('DUPLICATE_OR_UNKNOWN_SCHEMA_ID')
    if job_id and a.get('job_id')!=job_id: refuse('JOB_RECEIPT_SOURCE_MISMATCH')
    if attempt_id and a.get('attempt_id')!=attempt_id: refuse('JOB_RECEIPT_SOURCE_MISMATCH')
    for x in a.get('artifacts',[]):
        if not H64.fullmatch(str(x.get('digest',''))) or not isinstance(x.get('source_readback'),dict) or not H64.fullmatch(str(x['source_readback'].get('digest',''))): refuse('ARTIFACT_WITHOUT_DIGEST_OR_READBACK')
def receipt(r,j,a=None):
    no_extra(r,{'schema','receipt_id','job_id','attempt_id','parent_attempt_id','execution_lane','execution_subject','source_subject','bindings','started_at','ended_at','terminal_state','transport_state','workflow_state','task_state','effect_state','artifact_state','cleanup_state','budget_observation','artifact_manifest_ref','policy_decisions','residue_observation','capability_class','evidence_class','evidence_ceiling','claims_not_proven','external_states','contract_set_ref'})
    if r.get('job_id')!=j.get('job_id') or r.get('source_subject')!=j.get('source_subject'): refuse('JOB_RECEIPT_SOURCE_MISMATCH')
    if r.get('execution_lane')!=j.get('execution_lane'): refuse('LANE_SUBSTITUTION')
    if r.get('capability_class')=='BROWSER_FALLBACK' and r.get('evidence_class')=='API_OBSERVATION': refuse('BROWSER_AS_API_EVIDENCE')
    if r.get('evidence_ceiling')=='LIVE_CLOSED': refuse('STATIC_FIXTURE_AS_LIVE_PASS')
    if any(v not in ('NOT_EXERCISED','EXTERNALLY_REFERENCED','HUMAN_ADMIT_REQUIRED') for v in r.get('external_states',{}).values()): refuse('WORKER_OR_PROVIDER_SELF_PROMOTION')
    t,e,c,ar=r.get('terminal_state'),r.get('effect_state'),r.get('cleanup_state'),r.get('artifact_state')
    if t=='SUCCEEDED' and c in ('FAIL','UNKNOWN'): refuse('SUCCESS_WITH_CLEANUP_FAILURE')
    if t=='SUCCEEDED' and e=='UNKNOWN_EXTERNAL_EFFECT': refuse('UNKNOWN_EXTERNAL_EFFECT_AS_SUCCESS')
    if t=='SUCCEEDED' and ar in ('PARTIAL','MISSING'): refuse('TERMINAL_STATE_COLLAPSE')
    if e=='UNKNOWN_EXTERNAL_EFFECT' and t!='UNKNOWN_EXTERNAL_EFFECT': refuse('UNKNOWN_EXTERNAL_EFFECT_AS_SUCCESS')
    if c=='FAIL' and t!='CLEANUP_FAILED': refuse('TERMINAL_STATE_COLLAPSE')
    if r.get('transport_state')=='TIMED_OUT' and t not in ('TIMED_OUT','NOT_EXERCISED'): refuse('TERMINAL_STATE_COLLAPSE')
    if a is not None: artifact(a,j.get('job_id'),r.get('attempt_id'))
def fixture(f):
    j=f['job']; job(j); grant(f['grant'])
    if f['grant']['grant_id']!=j['capability_grant_ref']: refuse('CAPABILITY_GRANT_MISMATCH')
    e=f.get('effect_intent')
    if j['side_effect_class']!='READ_ONLY':
        if not e: refuse('WRITE_WITHOUT_EFFECT_IDENTITY')
        effect(e,j)
    elif e: refuse('WRITE_WITHOUT_EFFECT_IDENTITY')
    rs=f.get('receipts') or [f['receipt']]
    for r in rs: receipt(r,j,f.get('artifact_manifest'))

def meta():
    for p in sorted(C.glob('*.schema.json')):
        x=load(p)
        if x.get('$schema')!='https://json-schema.org/draft/2020-12/schema' or x.get('type')!='object' or x.get('additionalProperties') is not False: refuse('SCHEMA_SHAPE_INVALID',p.name)
    try:
        from jsonschema import Draft202012Validator
    except Exception: print('DRAFT202012_META_VALIDATION: OPTIONAL_DEPENDENCY_ABSENT')
    else:
        for p in sorted(C.glob('*.schema.json')): Draft202012Validator.check_schema(load(p))
        print('DRAFT202012_META_VALIDATION: PASS')
def positives():
    d=manifest(load(C/'contract-set-manifest.json'))
    for p in sorted(E.glob('p[1-5]-*.example.json')):
        f=load(p); fixture(f); print(f"{f['fixture_id']}: PASS")
    print('P6: PASS',d)
def mutations():
    base={load(p)['fixture_id']:load(p) for p in E.glob('p[1-5]-*.example.json')}; man=load(C/'contract-set-manifest.json')
    cases={}
    m=copy.deepcopy(man); m['method_subject']['commit']='0'*40; cases['R01']=lambda m=m:manifest(m)
    m=copy.deepcopy(man); m['schemas'].append(copy.deepcopy(m['schemas'][0])); cases['R02']=lambda m=m:manifest(m)
    m=copy.deepcopy(base['P1']); m['job']['command']='rm -rf /'; cases['R03']=lambda m=m:fixture(m)
    m=copy.deepcopy(base['P1']); m['job']['source_subject']['commit']='main'; cases['R04']=lambda m=m:fixture(m)
    m=copy.deepcopy(base['P1']); m['receipt']['source_subject']['tree']='0'*40; cases['R05']=lambda m=m:fixture(m)
    m=copy.deepcopy(base['P1']); m['receipt']['execution_lane']='LOCAL'; cases['R06']=lambda m=m:fixture(m)
    m=copy.deepcopy(base['P2']); m['job']['execution_lane']='CLOUD'; m['job']['allowlists']['network_origins']=['https://api.example.test']; cases['R07']=lambda m=m:fixture(m)
    m=copy.deepcopy(base['P1']); m['job']['allowlists']['filesystem_paths'].append('/Users/x/.ssh/id_rsa'); cases['R08']=lambda m=m:fixture(m)
    m=copy.deepcopy(base['P3']); del m['effect_intent']; cases['R09']=lambda m=m:fixture(m)
    m=copy.deepcopy(base['P4']); original=base['P4']['effect_intent']; m['effect_intent']['normalized_request_digest']='b'*64
    def r10(m=m,o=original):
        fixture(m)
        if m['effect_intent']['idempotency_key']==o['idempotency_key'] and m['effect_intent']['normalized_request_digest']!=o['normalized_request_digest']: refuse('IDEMPOTENCY_COLLISION')
    cases['R10']=r10
    m=copy.deepcopy(base['P1']); m['receipt']['terminal_state']='SUCCEEDED'; m['receipt']['cleanup_state']='FAIL'; cases['R11']=lambda m=m:fixture(m)
    m=copy.deepcopy(base['P1']); m['receipt']['terminal_state']='FAILED'; m['receipt']['transport_state']='TIMED_OUT'; cases['R12']=lambda m=m:fixture(m)
    a={'schema':'runtime-env/dual-agent/artifact-manifest/v1','manifest_id':'m','job_id':'job-x','attempt_id':'attempt-1','artifacts':[{'logical_name':'x','media_type':'application/json','digest':'a'*64,'size_bytes':1}],'completeness_state':'COMPLETE','contract_set_ref':{}}; cases['R13']=lambda a=a:artifact(a)
    m=copy.deepcopy(base['P1']); m['receipt']['capability_class']='BROWSER_FALLBACK'; m['receipt']['evidence_class']='API_OBSERVATION'; cases['R14']=lambda m=m:fixture(m)
    m=copy.deepcopy(base['P1']); m['receipt']['evidence_ceiling']='LIVE_CLOSED'; cases['R15']=lambda m=m:fixture(m)
    m=copy.deepcopy(man); m['schemas'][0]['sha256']='0'*64; cases['R16']=lambda m=m:manifest(m)
    m=copy.deepcopy(base['P5']); m['receipt']['terminal_state']='SUCCEEDED'; m['receipt']['cleanup_state']='PASS'; cases['R17']=lambda m=m:fixture(m)
    m=copy.deepcopy(base['P1']); m['receipt']['external_states']['release']='PASS'; cases['R18']=lambda m=m:fixture(m)
    reg={x['id']:x['expected_failure'] for x in load(M)['controls']}
    if reg!=FAIL: raise AssertionError(('mutation registry drift',reg,FAIL))
    for k,fn in cases.items():
        try: fn()
        except Refusal as e:
            got=str(e).split(':',1)[0]
            if got!=FAIL[k]: raise AssertionError(f'{k}: expected {FAIL[k]}, got {e}') from e
            print(f'{k}: RED/{got}')
        else: raise AssertionError(f'{k}: mutation survived; expected {FAIL[k]}')
if __name__=='__main__':
    meta(); positives(); mutations(); print('PASS: Dual-Agent runtime contract P1-P6 + R01-R18')
