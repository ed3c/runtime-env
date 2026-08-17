#!/usr/bin/env python3
"""Bounded multi-Worker scheduler state reducer bound to skills-shared lifecycle law."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA_REL = Path("skills/agentic-tech-lead-orchestration/references/scheduler-lifecycle.schema.json")
VALIDATOR_REL = Path("skills/agentic-tech-lead-orchestration/scripts/assert_scheduler_lifecycle.py")
TERMINAL = {"STALE_ATTEMPT", "LEASE_EXPIRED", "TIMED_OUT", "STRAGGLER_DETACHED", "FAILED_RETRYABLE", "CANCELLED", "SUPERSEDED", "INTEGRATED"}

class SchedulerError(ValueError):
    pass


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SchedulerError(f"invalid JSON {path}: {exc}") from exc


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_json(value) -> str:
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def git_head(root: Path) -> str:
    proc = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], text=True, capture_output=True, check=False)
    if proc.returncode:
        raise SchedulerError("cannot resolve skills-shared exact HEAD")
    return proc.stdout.strip()


def bind_shared(skills_root: Path, expected_commit: str):
    root = skills_root.resolve()
    if git_head(root) != expected_commit:
        raise SchedulerError("skills-shared exact subject mismatch")
    schema = root / SCHEMA_REL
    validator = root / VALIDATOR_REL
    if not schema.is_file() or not validator.is_file():
        raise SchedulerError("canonical scheduler schema/validator missing")
    return root, schema, validator, digest_bytes(schema.read_bytes()), digest_bytes(validator.read_bytes())


def attempts_by_id(state):
    return {item["attempt_id"]: item for item in state["attempts"]}


def find_attempt(state, attempt_id):
    item = attempts_by_id(state).get(attempt_id)
    if not item:
        raise SchedulerError(f"unknown attempt: {attempt_id}")
    return item


def ensure_transition(item, allowed, target):
    if item["state"] not in allowed:
        raise SchedulerError(f"invalid transition {item['attempt_id']}: {item['state']} -> {target}")
    item["state"] = target


def active_lease(state, resource):
    return next((x for x in state["leases"] if x["resource"] == resource and x["active"]), None)


def event_apply(state, event):
    if not isinstance(event, dict) or not isinstance(event.get("type"), str):
        raise SchedulerError("event must contain type")
    typ = event["type"]
    now = event.get("at")
    if not isinstance(now, int) or now < 0:
        raise SchedulerError("event.at must be non-negative integer")

    if typ == "CREATE_ATTEMPT":
        aid, tid = event.get("attempt_id"), event.get("task_id")
        if not isinstance(aid, str) or not aid or not isinstance(tid, str) or not tid:
            raise SchedulerError("CREATE_ATTEMPT requires task_id/attempt_id")
        if aid in attempts_by_id(state):
            raise SchedulerError("duplicate attempt")
        parent = event.get("parent_attempt_id")
        if parent is not None:
            p = find_attempt(state, parent)
            if p["task_id"] != tid or p["state"] not in TERMINAL:
                raise SchedulerError("retry parent must be terminal attempt for same task")
        budget = event.get("budget")
        head = event.get("head")
        worktree = event.get("worktree")
        if not isinstance(budget, int) or budget < 0 or not isinstance(head, str) or len(head) != 40 or not isinstance(worktree, str) or not worktree:
            raise SchedulerError("invalid CREATE_ATTEMPT budget/head/worktree")
        state["attempts"].append({"task_id":tid,"attempt_id":aid,"parent_attempt_id":parent,"state":"PLANNED","budget":budget,"consumed":0,"worktree":worktree,"head":head})
    elif typ == "ADVANCE":
        item = find_attempt(state, event.get("attempt_id"))
        target = event.get("state")
        chain = {"PLANNED":"ADMITTED","ADMITTED":"ASSIGNED","ASSIGNED":"LEASED","LEASED":"RUNNING","RUNNING":"CHECKPOINTED","CHECKPOINTED":"RUNNING","RESULT_READY":"RESULT_VERIFIED","RESULT_VERIFIED":"INTEGRATED"}
        if chain.get(item["state"]) != target:
            raise SchedulerError(f"non-canonical ADVANCE: {item['state']} -> {target}")
        item["state"] = target
    elif typ == "LEASE":
        item = find_attempt(state, event.get("attempt_id")); resource = event.get("resource"); expires = event.get("expires_at")
        if item["state"] not in {"ASSIGNED", "LEASED"} or not isinstance(resource, str) or not resource or not isinstance(expires, int) or expires <= now:
            raise SchedulerError("invalid LEASE")
        owner = active_lease(state, resource)
        if owner and owner["attempt_id"] != item["attempt_id"]:
            raise SchedulerError("resource already has active writer")
        if not owner:
            state["leases"].append({"attempt_id":item["attempt_id"],"resource":resource,"active":True,"expires_at":expires})
        else:
            owner["expires_at"] = expires
        item["state"] = "LEASED"
    elif typ == "HEARTBEAT":
        item = find_attempt(state, event.get("attempt_id")); expires = event.get("expires_at")
        if item["state"] not in {"LEASED","RUNNING","CHECKPOINTED"} or not isinstance(expires, int) or expires <= now:
            raise SchedulerError("invalid HEARTBEAT")
        owned = [x for x in state["leases"] if x["attempt_id"] == item["attempt_id"] and x["active"]]
        if not owned:
            raise SchedulerError("heartbeat without active lease")
        for lease in owned: lease["expires_at"] = expires
    elif typ == "TICK":
        for lease in state["leases"]:
            if lease["active"] and lease["expires_at"] <= now:
                lease["active"] = False
                item = find_attempt(state, lease["attempt_id"])
                if item["state"] not in TERMINAL:
                    item["state"] = "LEASE_EXPIRED"
    elif typ == "CONSUME":
        item = find_attempt(state, event.get("attempt_id")); amount = event.get("amount")
        if item["state"] in TERMINAL or not isinstance(amount, int) or amount < 0:
            raise SchedulerError("invalid CONSUME")
        if item["consumed"] + amount > item["budget"]:
            raise SchedulerError("attempt budget exceeded")
        item["consumed"] += amount
    elif typ == "CHECKPOINT":
        item = find_attempt(state, event.get("attempt_id")); cid = event.get("checkpoint_id"); artifact = event.get("artifact_digest")
        if item["state"] not in {"RUNNING","CHECKPOINTED"} or not isinstance(cid,str) or not cid or any(x["checkpoint_id"]==cid for x in state["checkpoints"]) or not isinstance(artifact,str) or len(artifact)!=64:
            raise SchedulerError("invalid CHECKPOINT")
        state["checkpoints"].append({"attempt_id":item["attempt_id"],"checkpoint_id":cid,"artifact_digest":artifact}); item["state"]="CHECKPOINTED"
    elif typ == "RESULT":
        item = find_attempt(state, event.get("attempt_id")); result = event.get("result_digest"); oracle = event.get("oracle")
        if item["state"] not in {"RUNNING","CHECKPOINTED"} or any(x["attempt_id"]==item["attempt_id"] for x in state["results"]) or not isinstance(result,str) or len(result)!=64 or oracle not in {"PASS","FAIL"}:
            raise SchedulerError("invalid RESULT")
        item["state"]="RESULT_READY"
        state["results"].append({"attempt_id":item["attempt_id"],"result_digest":result,"oracle":oracle,"accepted":False})
    elif typ == "VERIFY_RESULT":
        item = find_attempt(state, event.get("attempt_id")); result = next((x for x in state["results"] if x["attempt_id"]==item["attempt_id"]),None)
        if item["state"] != "RESULT_READY" or not result or result["oracle"] != "PASS":
            raise SchedulerError("result not admissible for verification")
        item["state"]="RESULT_VERIFIED"; result["accepted"] = True
        for lease in state["leases"]:
            if lease["attempt_id"] == item["attempt_id"]: lease["active"] = False
    elif typ == "TERMINATE":
        item = find_attempt(state, event.get("attempt_id")); target = event.get("state")
        if target not in TERMINAL - {"INTEGRATED"} or item["state"] in TERMINAL:
            raise SchedulerError("invalid TERMINATE")
        item["state"] = target
        for lease in state["leases"]:
            if lease["attempt_id"] == item["attempt_id"]: lease["active"] = False
        for result in state["results"]:
            if result["attempt_id"] == item["attempt_id"]: result["accepted"] = False
    else:
        raise SchedulerError(f"unsupported event type: {typ}")


def validate_shared(state, validator: Path):
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "lifecycle.json"
        path.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
        proc = subprocess.run([sys.executable, str(validator), "--lifecycle", str(path)], text=True, capture_output=True, check=False)
    if proc.returncode:
        raise SchedulerError("skills-shared lifecycle validator rejected state: " + proc.stderr.strip())


def atomic_json(path: Path, value):
    path = path.expanduser().absolute(); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600); os.replace(tmp, path)


def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("command",choices=["contract","reduce"]); p.add_argument("--skills-root",type=Path,required=True); p.add_argument("--skills-commit",required=True); p.add_argument("--initial",type=Path); p.add_argument("--events",type=Path); p.add_argument("--state-root",type=Path)
    a=p.parse_args(argv)
    try:
        root,schema,validator,schema_sha,validator_sha=bind_shared(a.skills_root,a.skills_commit)
        if a.command=="contract":
            print(json.dumps({"schema":"runtime-env/multi-worker-scheduler-contract/v1","skills_shared_commit":a.skills_commit,"lifecycle_schema_sha256":schema_sha,"lifecycle_validator_sha256":validator_sha,"worker_execution":"NOT_EXERCISED","merge_authority":False},sort_keys=True)); return 0
        if not a.initial or not a.events or not a.state_root: raise SchedulerError("reduce requires --initial --events --state-root")
        state=load(a.initial); events=load(a.events)
        if not isinstance(events,list): raise SchedulerError("events must be array")
        validate_shared(state,validator)
        for event in events:
            event_apply(state,event); validate_shared(state,validator)
        state["evidence_state"]="NOT_EXERCISED"; validate_shared(state,validator)
        receipt={"schema":"runtime-env/multi-worker-scheduler-receipt/v1","skills_shared_commit":a.skills_commit,"lifecycle_schema_sha256":schema_sha,"event_stream_sha256":digest_json(events),"lifecycle_sha256":digest_json(state),"worker_execution":"NOT_EXERCISED","process_execution":"NOT_EXERCISED","worktree_execution":"NOT_EXERCISED","merge_authority":False,"terminal_state":"READY"}
        root_path=a.state_root.expanduser().absolute(); atomic_json(root_path/"lifecycle.json",state); atomic_json(root_path/"receipt.json",receipt); print(json.dumps(receipt,sort_keys=True)); return 0
    except (SchedulerError,OSError,subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
