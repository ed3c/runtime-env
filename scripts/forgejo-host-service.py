#!/usr/bin/env python3
"""Forgejo host lifecycle with exact artifact binding and fail-closed recovery."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, socket, stat, subprocess, sys, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"catalog/forgejo-host-service.json"
MARKER=".runtime-env-forgejo-managed"
class HostError(ValueError): pass

def load(path):
    try: return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e: raise HostError(f"invalid JSON {path}: {e}") from e

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def expand(value): return Path(value).expanduser().absolute()

def contract(manifest,binding):
    if manifest.get("schema")!="runtime-env/forgejo-host-service-manifest/v1" or manifest.get("service")!="forgejo": raise HostError("invalid service manifest")
    if binding.get("schema")!="runtime-env/forgejo-host-binding/v1": raise HostError("invalid host binding")
    if binding.get("version")!=manifest.get("version"): raise HostError("binding version differs from admitted service version")
    if not isinstance(binding.get("artifact_sha256"),str) or len(binding["artifact_sha256"])!=64: raise HostError("artifact sha256 required")
    if binding.get("port")!=manifest["network"]["default_port"]: raise HostError("non-admitted Forgejo port")
    install=expand(binding["install_root"]); state=expand(binding["state_root"])
    for p in (install,state):
        if ROOT.resolve()==p or ROOT.resolve() in p.parents: raise HostError("repository-local Forgejo host state is forbidden")
    return install,state

def paths(manifest,binding):
    install,state=contract(manifest,binding); version=manifest["version"]
    target=install/version; binary=target/"forgejo"; config=state/"config"/"app.ini"; data=state/"data"; backups=state/"backups"; launcher=install/"current"; staging=install/("."+version+".staging"); return install,state,target,binary,config,data,backups,launcher,staging

def probe(binary,version):
    p=subprocess.run([str(binary),"--version"],text=True,capture_output=True,check=False,timeout=15); out=(p.stdout+p.stderr).strip()
    if p.returncode or version not in out: raise HostError("Forgejo binary version probe failed")
    return out

def config_text(binding,data):
    port=binding["port"]
    return f"""[server]\nPROTOCOL = http\nHTTP_ADDR = 127.0.0.1\nHTTP_PORT = {port}\nROOT_URL = http://127.0.0.1:{port}/\n\n[database]\nDB_TYPE = sqlite3\nPATH = {data / 'forgejo.db'}\n\n[repository]\nROOT = {data / 'repositories'}\n\n[security]\nINSTALL_LOCK = true\n"""

def port_available(port):
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); s.bind(("127.0.0.1",port)); return True
    except OSError: return False
    finally: s.close()

def plan(manifest,binding):
    install,state,target,binary,config,data,backups,launcher,staging=paths(manifest,binding)
    return {"schema":"runtime-env/forgejo-host-plan/v1","version":manifest["version"],"platform":binding["platform"],"install_root":str(install),"state_root":str(state),"binary":str(binary),"config":str(config),"port":binding["port"],"artifact_sha256":binding["artifact_sha256"],"service":"NOT_EXERCISED","health":"NOT_EXERCISED","backup":"NOT_EXERCISED","restore":"NOT_EXERCISED","upgrade":"HUMAN_ADMIT_REQUIRED","rollback":"NOT_EXERCISED"}

def receipt(path,value):
    if not path: return
    p=Path(path).expanduser().absolute(); p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    if p.exists() or p.is_symlink(): raise HostError("receipt already exists")
    fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,"w") as f: json.dump(value,f,indent=2,sort_keys=True); f.write("\n")

def preflight(manifest,binding,allow_occupied=False):
    install,state,target,binary,config,data,backups,launcher,staging=paths(manifest,binding)
    if staging.exists(): raise HostError("interrupted Forgejo staging directory present")
    if target.exists() and not (target/MARKER).is_file(): raise HostError("existing unmanaged Forgejo target")
    available=port_available(binding["port"])
    if not available and not allow_occupied: raise HostError("Forgejo loopback port is occupied")
    return {"schema":"runtime-env/forgejo-host-preflight/v1","state":"PASS","port_available":available,"managed_target":target.exists(),"service":"NOT_EXERCISED","health":"NOT_EXERCISED"}

def install(manifest,binding,artifact,receipt_path):
    if os.geteuid()==0 and os.environ.get("RUNTIME_ENV_ALLOW_TEST_ROOT")!="1": raise HostError("refusing root/sudo host install")
    install_root,state,target,binary,config,data,backups,launcher,staging=paths(manifest,binding); artifact=Path(artifact).absolute()
    preflight(manifest,binding)
    if sha(artifact)!=binding["artifact_sha256"]: raise HostError("Forgejo artifact checksum mismatch")
    probe(artifact,manifest["version"])
    install_root.mkdir(mode=0o700,parents=True,exist_ok=True); data.mkdir(mode=0o700,parents=True,exist_ok=True); config.parent.mkdir(mode=0o700,parents=True,exist_ok=True); backups.mkdir(mode=0o700,parents=True,exist_ok=True)
    if not target.exists():
        staging.mkdir(mode=0o700)
        staged_binary=staging/"forgejo"; shutil.copy2(artifact,staged_binary); staged_binary.chmod(staged_binary.stat().st_mode|stat.S_IXUSR)
        if sha(staged_binary)!=binding["artifact_sha256"]: raise HostError("staged Forgejo binary digest mismatch")
        (staging/MARKER).write_text(json.dumps({"version":manifest["version"],"sha256":binding["artifact_sha256"]})+"\n")
        os.replace(staging,target)
    if sha(binary)!=binding["artifact_sha256"]: raise HostError("installed Forgejo binary digest mismatch")
    probe(binary,manifest["version"])
    config.write_text(config_text(binding,data),encoding="utf-8"); config.chmod(0o600)
    tmp=install_root/".current.tmp"; tmp.unlink(missing_ok=True); tmp.symlink_to(target); os.replace(tmp,launcher)
    r={"schema":"runtime-env/forgejo-host-install-receipt/v1","state":"PASS","version":manifest["version"],"artifact_sha256":binding["artifact_sha256"],"binary_sha256":sha(binary),"config_sha256":sha(config),"activation_target":str(target),"service":"NOT_EXERCISED","health":"NOT_EXERCISED","credentials":"NOT_EXERCISED","migration":"NOT_EXERCISED"}; receipt(receipt_path,r); print(json.dumps(r,sort_keys=True)); return 0

def check(manifest,binding):
    install,state,target,binary,config,data,backups,launcher,staging=paths(manifest,binding)
    if staging.exists(): raise HostError("interrupted Forgejo staging directory present")
    if not binary.is_file() or not config.is_file() or not (target/MARKER).is_file(): status="ABSENT"
    else:
        if sha(binary)!=binding["artifact_sha256"]: raise HostError("installed binary digest drift")
        probe(binary,manifest["version"]); status="PASS"
    r={"schema":"runtime-env/forgejo-host-check/v1","state":status,"service":"NOT_EXERCISED","health":"NOT_EXERCISED","backup":"NOT_EXERCISED","restore":"NOT_EXERCISED","rollback":"NOT_EXERCISED"}; print(json.dumps(r,sort_keys=True)); return 0 if status=="PASS" else 3

def backup(manifest,binding,output,service_stopped,receipt_path):
    if not service_stopped: raise HostError("consistent backup requires explicit stopped-service evidence")
    install,state,target,binary,config,data,backups,launcher,staging=paths(manifest,binding)
    if not binary.is_file() or not config.is_file(): raise HostError("Forgejo host is not installed")
    out=Path(output).expanduser().absolute(); out.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    p=subprocess.run([str(binary),"dump","--config",str(config),"--work-path",str(data),"--file",str(out),"--type","zip"],text=True,capture_output=True,check=False,timeout=300)
    if p.returncode or not out.is_file(): raise HostError("Forgejo dump failed")
    r={"schema":"runtime-env/forgejo-host-backup-receipt/v1","state":"PASS","version":manifest["version"],"backup_path":str(out),"backup_sha256":sha(out),"binary_sha256":sha(binary),"config_sha256":sha(config),"service_stopped":True}; receipt(receipt_path,r); print(json.dumps(r,sort_keys=True)); return 0

def restore_check(manifest,binding,backup_receipt,backup_file,emit=True):
    check_receipt=load(backup_receipt)
    if check_receipt.get("schema")!="runtime-env/forgejo-host-backup-receipt/v1" or check_receipt.get("state")!="PASS": raise HostError("invalid backup receipt")
    if check_receipt.get("version")!=manifest["version"]: raise HostError("backup version mismatch")
    candidate=Path(backup_file).expanduser().absolute()
    if not candidate.is_file() or sha(candidate)!=check_receipt.get("backup_sha256"): raise HostError("backup artifact identity mismatch")
    install,state,target,binary,config,data,backups,launcher,staging=paths(manifest,binding)
    if not binary.is_file() or sha(binary)!=check_receipt.get("binary_sha256"): raise HostError("restore binary identity mismatch")
    if not config.is_file() or sha(config)!=check_receipt.get("config_sha256"): raise HostError("restore config identity mismatch")
    r={"schema":"runtime-env/forgejo-host-restore-check/v1","state":"PASS","backup_sha256":check_receipt["backup_sha256"],"version":manifest["version"],"restore_execution":"NOT_EXERCISED","destructive_mutation":False}
    if emit: print(json.dumps(r,sort_keys=True))
    return r

def rollback_plan(manifest,binding,backup_receipt,backup_file):
    restore_check(manifest,binding,backup_receipt,backup_file,emit=False)
    r=plan(manifest,binding); r["rollback"]="HUMAN_ADMIT_REQUIRED"; r["restore_preflight"]="PASS"; r["destructive_mutation"]=False; print(json.dumps(r,sort_keys=True)); return 4

def health(binding):
    url=f"http://127.0.0.1:{binding['port']}/api/v1/settings/api"
    try:
        with urllib.request.urlopen(url,timeout=5) as r: ok=200<=r.status<300
    except Exception: ok=False
    print(json.dumps({"schema":"runtime-env/forgejo-host-health/v1","url":url,"state":"PASS" if ok else "FAIL"},sort_keys=True)); return 0 if ok else 3

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("command",choices=["plan","preflight","install","check","health","backup","restore-check","rollback-plan","upgrade-plan"]); p.add_argument("--manifest",type=Path,default=MANIFEST); p.add_argument("--binding",type=Path,required=True); p.add_argument("--artifact",type=Path); p.add_argument("--output",type=Path); p.add_argument("--receipt",type=Path); p.add_argument("--backup-receipt",type=Path); p.add_argument("--backup-file",type=Path); p.add_argument("--service-stopped",action="store_true"); a=p.parse_args(argv)
    try:
        m=load(a.manifest); b=load(a.binding)
        if a.command=="plan": print(json.dumps(plan(m,b),sort_keys=True)); return 0
        if a.command=="preflight": print(json.dumps(preflight(m,b),sort_keys=True)); return 0
        if a.command=="install":
            if not a.artifact: raise HostError("install requires exact --artifact")
            return install(m,b,a.artifact,a.receipt)
        if a.command=="check": return check(m,b)
        if a.command=="health": contract(m,b); return health(b)
        if a.command=="backup":
            if not a.output: raise HostError("backup requires --output")
            return backup(m,b,a.output,a.service_stopped,a.receipt)
        if a.command in {"restore-check","rollback-plan"}:
            if not a.backup_receipt or not a.backup_file: raise HostError(f"{a.command} requires --backup-receipt and --backup-file")
            if a.command=="restore-check": restore_check(m,b,a.backup_receipt,a.backup_file); return 0
            return rollback_plan(m,b,a.backup_receipt,a.backup_file)
        r=plan(m,b); r["upgrade"]="HUMAN_ADMIT_REQUIRED"; r["backup_required"]=True; r["rollback_subject_required"]=True; print(json.dumps(r,sort_keys=True)); return 4
    except (HostError,OSError,subprocess.SubprocessError) as e: print(f"ERROR: {e}",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
