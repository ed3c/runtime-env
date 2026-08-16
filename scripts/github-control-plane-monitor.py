#!/usr/bin/env python3
"""Read-only GitHub issue adapter for the provider-neutral repository control plane."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from urllib.parse import urlparse

API = "https://api.github.com"
API_VERSION = "2026-03-10"
PHASES = {"BOOTSTRAP","SHADOW_ADMISSION","TECH_LEAD_PLAN","SPATIAL_INVARIANTS","STACK_DELIVERY","FORGE_RECONCILIATION"}

class MonitorError(ValueError): pass

def load(path: Path):
    try: v=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e: raise MonitorError(f"invalid JSON {path}: {e}") from e
    return v

def canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def digest(v): return hashlib.sha256(canon(v)).hexdigest()

def registry(path: Path):
    v=load(path)
    if not isinstance(v,dict) or v.get("schema")!="runtime-env/github-monitor-registry/v1" or set(v)!={"schema","repositories"}: raise MonitorError("invalid monitor registry")
    repos=v["repositories"]
    if not isinstance(repos,dict) or not repos: raise MonitorError("monitor registry is empty")
    for name, row in repos.items():
        if name.count("/")!=1 or not isinstance(row,dict) or set(row)!={"visibility_class","required_phases"}: raise MonitorError(f"invalid registry row {name}")
        if row["visibility_class"] not in {"public","private"} or not isinstance(row["required_phases"],dict): raise MonitorError(f"invalid registry policy {name}")
        for n, phases in row["required_phases"].items():
            if not n.isdigit() or not isinstance(phases,list) or any(p not in PHASES for p in phases): raise MonitorError(f"invalid required phases {name}#{n}")
    return v

def headers(token: str|None):
    h={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":API_VERSION,"User-Agent":"runtime-env-control-plane-monitor"}
    if token: h["Authorization"]="Bearer "+token
    return h

def get_json(url: str, token: str|None):
    if not url.startswith(API+"/"): raise MonitorError("provider URL escaped api.github.com")
    req=urllib.request.Request(url,headers=headers(token),method="GET")
    try:
        with urllib.request.urlopen(req,timeout=30) as r: # noqa: S310 fixed origin checked above
            data=json.loads(r.read().decode()); meta={"rate_limit":r.headers.get("X-RateLimit-Limit"),"rate_remaining":r.headers.get("X-RateLimit-Remaining"),"link":r.headers.get("Link")}
    except (urllib.error.URLError,json.JSONDecodeError) as e: raise MonitorError(f"GitHub read failed: {e}") from e
    return data,meta

def pages(url: str, token: str|None):
    page=1; values=[]; metadata=[]
    while True:
        sep="&" if "?" in url else "?"
        data,meta=get_json(f"{url}{sep}per_page=100&page={page}",token)
        if not isinstance(data,list): raise MonitorError("GitHub list response is not an array")
        values.extend(data); metadata.append({"page":page,**meta,"count":len(data)})
        if len(data)<100: break
        page+=1
        if page>100: raise MonitorError("pagination budget exceeded")
    return values,metadata

def repo_from_url(value: str):
    prefix=API+"/repos/"
    if not isinstance(value,str) or not value.startswith(prefix): raise MonitorError("dependency repository_url is invalid")
    tail=value[len(prefix):].strip("/")
    if tail.count("/")!=1: raise MonitorError("dependency repository identity is invalid")
    return tail

def normalize_issue(repo: str, issue: dict, required: list[str]):
    number=issue.get("number"); state=issue.get("state")
    if not isinstance(number,int) or number<=0 or state not in {"open","closed"}: raise MonitorError("invalid GitHub issue identity/state")
    return {"repository":repo,"number":number,"state":state,"depends_on":[],"required_phases":required}

def build_packet_from_fixture(reg: dict, repo: str, issues: list[dict], deps: dict[str,list[dict]]):
    if repo not in reg["repositories"]: raise MonitorError(f"repository not allowlisted: {repo}")
    by_id={}
    def add(r,i):
        if "pull_request" in i: return None
        phases=reg["repositories"].get(r,{}).get("required_phases",{}).get(str(i.get("number")),[])
        item=normalize_issue(r,i,phases); ident=f"{r}#{item['number']}"
        old=by_id.get(ident)
        if old and old["state"]!=item["state"]: raise MonitorError(f"conflicting issue state: {ident}")
        by_id[ident]=old or item; return ident
    for issue in issues: add(repo,issue)
    for ident in list(by_id):
        if by_id[ident]["state"]!="open": continue
        edges=[]
        for dep in deps.get(ident,[]):
            dep_repo=repo_from_url(dep.get("repository_url"))
            if dep_repo not in reg["repositories"]: raise MonitorError(f"dependency repository not allowlisted: {dep_repo}")
            dep_id=add(dep_repo,dep)
            if dep_id: edges.append(dep_id)
        by_id[ident]["depends_on"]=sorted(set(edges))
    return [by_id[k] for k in sorted(by_id)]

def fetch_packet(reg: dict, repo: str, token: str|None):
    if repo not in reg["repositories"]: raise MonitorError(f"repository not allowlisted: {repo}")
    owner,name=repo.split("/",1)
    issues,page_meta=pages(f"{API}/repos/{owner}/{name}/issues?state=all",token)
    issues=[i for i in issues if "pull_request" not in i]
    deps={}; dep_meta=[]
    for issue in issues:
        if issue.get("state")!="open": continue
        n=issue.get("number"); ident=f"{repo}#{n}"
        rows,meta=pages(f"{API}/repos/{owner}/{name}/issues/{n}/dependencies/blocked_by",token)
        deps[ident]=rows; dep_meta.extend({"issue":ident,**m} for m in meta)
    return build_packet_from_fixture(reg,repo,issues,deps), {"issue_pages":page_meta,"dependency_pages":dep_meta}

def git_head(root: Path):
    p=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],text=True,capture_output=True,check=False)
    if p.returncode: raise MonitorError("cannot resolve skills-shared exact head")
    return p.stdout.strip()

def compile_plan(packet, skills_root: Path, expected_commit: str):
    root=skills_root.resolve()
    if git_head(root)!=expected_commit: raise MonitorError("skills-shared exact subject mismatch")
    compiler=root/"skills/shared-skills-infra/scripts/repository_control_plane.py"
    schema=root/"skills/shared-skills-infra/references/repository-control-plane-monitor-plan.v1.schema.json"
    if not compiler.is_file() or not schema.is_file(): raise MonitorError("skills-shared control-plane compiler/schema missing")
    with tempfile.TemporaryDirectory() as td:
        inp=Path(td)/"packet.json"; inp.write_text(json.dumps(packet,sort_keys=True)+"\n")
        p=subprocess.run([sys.executable,str(compiler),"monitor-plan","--issues",str(inp)],text=True,capture_output=True,check=False)
    if p.returncode: raise MonitorError("skills-shared monitor compiler rejected packet: "+p.stderr.strip())
    try: plan=json.loads(p.stdout)
    except json.JSONDecodeError as e: raise MonitorError("monitor compiler emitted invalid JSON") from e
    if plan.get("schema")!="repository-control-plane-monitor-plan/v1" or plan.get("automatic_merge") is not False or plan.get("automatic_conflict_resolution") is not False: raise MonitorError("monitor plan authority/schema mismatch")
    if any(v.get("execution_state")!="NOT_EXERCISED" for v in plan.get("issue_plans",{}).values()): raise MonitorError("monitor plan promoted runtime evidence")
    return plan, hashlib.sha256(schema.read_bytes()).hexdigest()

def atomic_json(path: Path, value):
    path=path.expanduser().absolute(); path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8"); os.replace(tmp,path)

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("command",choices=["fixture","fetch"]); p.add_argument("--registry",type=Path,required=True); p.add_argument("--repository",required=True); p.add_argument("--skills-root",type=Path,required=True); p.add_argument("--skills-commit",required=True); p.add_argument("--state-root",type=Path,required=True); p.add_argument("--issues-fixture",type=Path); p.add_argument("--dependencies-fixture",type=Path); args=p.parse_args(argv)
    try:
        reg=registry(args.registry); token=os.environ.get("GITHUB_TOKEN")
        if args.command=="fixture":
            if not args.issues_fixture or not args.dependencies_fixture: raise MonitorError("fixture mode requires issue/dependency fixtures")
            packet=build_packet_from_fixture(reg,args.repository,load(args.issues_fixture),load(args.dependencies_fixture)); provider={"mode":"fixture","api_version":API_VERSION}
        else:
            if reg["repositories"][args.repository]["visibility_class"]=="private" and not token: raise MonitorError("GITHUB_TOKEN is required for private repository read")
            packet,provider=fetch_packet(reg,args.repository,token); provider={"mode":"github-read-only","api_version":API_VERSION,**provider}
        plan,schema_sha=compile_plan(packet,args.skills_root,args.skills_commit)
        snapshot={"schema":"runtime-env/github-control-plane-snapshot/v1","repository":args.repository,"provider":provider,"packet":packet,"packet_sha256":digest(packet)}
        receipt={"schema":"runtime-env/github-control-plane-monitor-receipt/v1","repository":args.repository,"skills_shared_commit":args.skills_commit,"snapshot_sha256":digest(snapshot),"packet_sha256":snapshot["packet_sha256"],"plan_sha256":digest(plan),"plan_schema_sha256":schema_sha,"provider_permission":"issues:read","provider_writes":False,"worker_execution":"NOT_EXERCISED","terminal_state":"READY"}
        root=args.state_root.expanduser().absolute(); atomic_json(root/"snapshot.json",snapshot); atomic_json(root/"plan.json",plan); atomic_json(root/"receipt.json",receipt)
        print(json.dumps(receipt,sort_keys=True)); return 0
    except (MonitorError,OSError) as e:
        print(f"ERROR: {e}",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
