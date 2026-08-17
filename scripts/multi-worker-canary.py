#!/usr/bin/env python3
"""Fixed local-only subprocess/worktree canary for the bounded multi-Worker scheduler.

This runner intentionally has no arbitrary command field. It exercises runtime mechanics on
an exact Git repository subject and reports a synthetic harness receipt. It does not promote
an admitted consumer or delivery lane.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import time
import uuid

class CanaryError(ValueError):
    pass


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CanaryError(f"invalid JSON {path}: {exc}") from exc


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=False)
    if check and p.returncode:
        raise CanaryError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p


def exact_head(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def safe_owned_path(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise CanaryError("owned_path must be non-empty")
    p = PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts or not p.parts or p.parts[0] == ".git":
        raise CanaryError(f"unsafe owned_path: {value}")
    return p


def validate_plan(plan: dict) -> list[dict]:
    if not isinstance(plan, dict) or plan.get("schema") != "runtime-env/multi-worker-canary-plan/v1":
        raise CanaryError("invalid canary plan schema")
    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or len(tasks) < 2:
        raise CanaryError("canary requires at least two tasks")
    ids = set(); paths = set()
    for task in tasks:
        if not isinstance(task, dict) or set(task) != {"task_id", "owned_path", "delay_ms", "interrupt_once"}:
            raise CanaryError("task must contain only task_id/owned_path/delay_ms/interrupt_once")
        tid = task["task_id"]
        owned = str(safe_owned_path(task["owned_path"]))
        if not isinstance(tid, str) or not tid or tid in ids:
            raise CanaryError("task_id must be unique non-empty string")
        if owned in paths:
            raise CanaryError("owned paths must be disjoint")
        if not isinstance(task["delay_ms"], int) or not 0 <= task["delay_ms"] <= 5000:
            raise CanaryError("delay_ms outside bounded range")
        if not isinstance(task["interrupt_once"], bool):
            raise CanaryError("interrupt_once must be boolean")
        ids.add(tid); paths.add(owned)
    return tasks


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def worker(args) -> int:
    worktree = args.worktree.resolve()
    owned = safe_owned_path(args.owned_path)
    target = worktree.joinpath(*owned.parts)
    checkpoint = args.checkpoint.resolve()
    checkpoint.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if args.delay_ms:
        time.sleep(args.delay_ms / 1000.0)
    if args.interrupt_once and not args.resume and not checkpoint.exists():
        atomic_json(checkpoint, {"task_id": args.task_id, "state": "CHECKPOINTED", "worktree": str(worktree)})
        return 75
    if args.resume and not checkpoint.exists():
        raise CanaryError("resume requested without checkpoint")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"task={args.task_id}\nresumed={str(args.resume).lower()}\n", encoding="utf-8")
    atomic_json(checkpoint, {"task_id": args.task_id, "state": "RESULT_READY", "worktree": str(worktree), "output_sha256": sha(target)})
    return 0


def run(args) -> int:
    repo = args.repository.resolve()
    if not (repo / ".git").exists() and not git(repo, "rev-parse", "--git-dir", check=False).returncode == 0:
        raise CanaryError("repository is not a Git worktree")
    observed = exact_head(repo)
    if observed != args.expected_head:
        raise CanaryError("consumer exact HEAD mismatch")
    if git(repo, "status", "--porcelain").stdout.strip():
        raise CanaryError("consumer repository must be clean")
    tasks = validate_plan(load(args.plan))
    state_root = args.state_root.resolve()
    worktree_root = state_root / "worktrees"
    checkpoint_root = state_root / "checkpoints"
    receipt_path = state_root / "receipt.json"
    if state_root == repo or repo in state_root.parents:
        raise CanaryError("state root must not be inside consumer repository")
    if state_root.exists() and any(state_root.iterdir()):
        raise CanaryError("state root must be empty for exact canary")
    state_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    worktree_root.mkdir(mode=0o700)
    checkpoint_root.mkdir(mode=0o700)
    run_id = uuid.uuid4().hex
    created: list[tuple[Path, str]] = []
    processes = []
    observations = []
    try:
        for index, task in enumerate(tasks):
            wt = worktree_root / task["task_id"]
            branch = f"runtime-canary/{run_id}/{index}-{task['task_id']}"
            git(repo, "worktree", "add", "-q", "-b", branch, str(wt), args.expected_head)
            created.append((wt, branch))
            if exact_head(wt) != args.expected_head:
                raise CanaryError("linked worktree head mismatch")
            cp = checkpoint_root / f"{task['task_id']}.json"
            cmd = [sys.executable, str(Path(__file__).resolve()), "worker", "--worktree", str(wt), "--task-id", task["task_id"], "--owned-path", task["owned_path"], "--checkpoint", str(cp), "--delay-ms", str(task["delay_ms"])]
            if task["interrupt_once"]:
                cmd.append("--interrupt-once")
            started = time.time_ns()
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            processes.append((task, wt, branch, cp, proc, started))

        # All first attempts are launched before waiting; this is the concurrency boundary.
        for task, wt, branch, cp, proc, started in processes:
            out, err = proc.communicate(timeout=10)
            first_exit = proc.returncode
            first_end = time.time_ns()
            resume_pid = None; resume_exit = None; resume_start = None; resume_end = None
            if first_exit == 75 and task["interrupt_once"]:
                resume_cmd = [sys.executable, str(Path(__file__).resolve()), "worker", "--worktree", str(wt), "--task-id", task["task_id"], "--owned-path", task["owned_path"], "--checkpoint", str(cp), "--delay-ms", "0", "--resume"]
                resume_start = time.time_ns()
                resumed = subprocess.Popen(resume_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                resume_pid = resumed.pid
                rout, rerr = resumed.communicate(timeout=10)
                resume_exit = resumed.returncode; resume_end = time.time_ns(); out += rout; err += rerr
            final_exit = resume_exit if resume_exit is not None else first_exit
            if final_exit != 0:
                raise CanaryError(f"worker {task['task_id']} failed: {err.strip()}")
            output = wt.joinpath(*safe_owned_path(task["owned_path"]).parts)
            if not output.is_file() or not cp.is_file():
                raise CanaryError("worker result/checkpoint missing")
            observations.append({
                "task_id":task["task_id"], "branch":branch, "worktree":str(wt), "first_pid":proc.pid,
                "first_started_ns":started, "first_ended_ns":first_end, "first_exit":first_exit,
                "resume_pid":resume_pid, "resume_started_ns":resume_start, "resume_ended_ns":resume_end, "resume_exit":resume_exit,
                "checkpoint_sha256":sha(cp), "output_sha256":sha(output), "owned_path":task["owned_path"]
            })
        # Prove at least two first attempts overlapped in wall-clock intervals.
        overlaps = False
        for i, left in enumerate(observations):
            for right in observations[i+1:]:
                if max(left["first_started_ns"], right["first_started_ns"]) < min(left["first_ended_ns"], right["first_ended_ns"]):
                    overlaps = True
        if not overlaps:
            raise CanaryError("first Worker processes did not overlap")
        receipt = {
            "schema":"runtime-env/multi-worker-process-canary-receipt/v1", "run_id":run_id,
            "repository":str(repo), "repository_head":observed, "task_count":len(tasks), "overlap_observed":True,
            "tasks":observations, "synthetic_runtime":"PASS", "admitted_consumer":"NOT_EXERCISED",
            "git_town":"NOT_EXERCISED", "forgejo":"NOT_EXERCISED", "merge_authority":False,
            "residue":"PENDING_CLEANUP"
        }
        atomic_json(receipt_path, receipt)
    finally:
        for wt, branch in reversed(created):
            git(repo, "worktree", "remove", "--force", str(wt), check=False)
            git(repo, "branch", "-D", branch, check=False)
        git(repo, "worktree", "prune", check=False)
    receipt = load(receipt_path)
    receipt["residue"] = "CLEAN"
    atomic_json(receipt_path, receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(); sub=p.add_subparsers(dest="command", required=True)
    r=sub.add_parser("run"); r.add_argument("--repository",type=Path,required=True); r.add_argument("--expected-head",required=True); r.add_argument("--plan",type=Path,required=True); r.add_argument("--state-root",type=Path,required=True)
    w=sub.add_parser("worker"); w.add_argument("--worktree",type=Path,required=True); w.add_argument("--task-id",required=True); w.add_argument("--owned-path",required=True); w.add_argument("--checkpoint",type=Path,required=True); w.add_argument("--delay-ms",type=int,default=0); w.add_argument("--interrupt-once",action="store_true"); w.add_argument("--resume",action="store_true")
    a=p.parse_args(argv)
    try:
        return run(a) if a.command=="run" else worker(a)
    except (CanaryError,OSError,subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr); return 2

if __name__ == "__main__": raise SystemExit(main())
