#!/usr/bin/env python3
"""Report repository control-plane runtime lanes without promoting live delivery."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLCHAIN = ROOT / "scripts" / "git-town-toolchain.py"


def git_town_lane() -> dict:
    binary = shutil.which("git-town")
    if binary is None:
        return {"state": "ABSENT", "executable": None, "version": None}
    proc = subprocess.run([binary, "--version"], text=True, capture_output=True, check=False, timeout=15)
    output = (proc.stdout + proc.stderr).strip()
    return {
        "state": "PASS" if proc.returncode == 0 else "FAIL",
        "executable": binary,
        "version": output if proc.returncode == 0 else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["contract", "git-town"], default="contract")
    args = parser.parse_args(argv)
    if args.mode == "git-town":
        lane = git_town_lane()
        print(json.dumps(lane, sort_keys=True))
        return 0 if lane["state"] == "PASS" else 3
    manifest = ROOT / "catalog" / "git-town-toolchain.json"
    proc = subprocess.run([sys.executable, str(TOOLCHAIN), "plan", "--manifest", str(manifest)], text=True, capture_output=True, check=False)
    contract_state = "PASS" if proc.returncode == 0 else "FAIL"
    receipt = {
        "schema": "runtime-env/repository-control-plane-doctor/v1",
        "contract": contract_state,
        "skills_binding": "EXTERNAL",
        "git_town_executable": git_town_lane()["state"],
        "forgejo_credential_canary": "NOT_EXERCISED",
        "consumer_repository_config": "NOT_EXERCISED",
        "live_stack_operation": "NOT_EXERCISED",
        "live_dual_forge_operation": "NOT_EXERCISED",
    }
    print(json.dumps(receipt, sort_keys=True))
    return 0 if contract_state == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
