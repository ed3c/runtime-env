#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ALLOWED_CLOSURE = {"PARTIAL", "CONTRACT_CLOSED", "LIVE_CLOSED"}
REQ_ID = re.compile(r"^REQ-[A-Z0-9-]+$")


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--graph", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    graph_path = (args.graph or (root / "prd" / "requirements.json")).resolve()
    data = json.loads(graph_path.read_text(encoding="utf-8"))

    if data.get("schema") != "prd-requirements/v1":
        fail("unsupported requirement graph schema")
    requirements = data.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        fail("requirements must be a non-empty list")

    seen: set[str] = set()
    for requirement in requirements:
        req_id = requirement.get("id")
        if not isinstance(req_id, str) or not REQ_ID.fullmatch(req_id):
            fail(f"invalid requirement id: {req_id!r}")
        if req_id in seen:
            fail(f"duplicate requirement id: {req_id}")
        seen.add(req_id)

        owner = requirement.get("owner") or {}
        if not owner.get("directory") or not owner.get("state_machine"):
            fail(f"{req_id} is missing directory/state-machine ownership")

        implementation_paths = requirement.get("implementation_paths") or []
        positive_controls = requirement.get("positive_controls") or []
        negative_controls = requirement.get("negative_controls") or []
        if not implementation_paths:
            fail(f"{req_id} has no implementation subjects")
        if not positive_controls:
            fail(f"{req_id} has no positive control")
        if not negative_controls:
            fail(f"{req_id} has no disagreement/negative control")

        for field, paths in (
            ("implementation", implementation_paths),
            ("positive control", positive_controls),
            ("negative control", negative_controls),
        ):
            for raw_path in paths:
                path = Path(raw_path)
                if path.is_absolute() or ".." in path.parts:
                    fail(f"{req_id} {field} path is not repository-relative: {raw_path}")
                if not (root / path).exists():
                    fail(f"{req_id} {field} path does not exist: {raw_path}")

        issues = requirement.get("issues") or []
        if not issues or any(not isinstance(item, int) or item < 1 for item in issues):
            fail(f"{req_id} must bind at least one valid issue number")

        closure = requirement.get("closure")
        if closure not in ALLOWED_CLOSURE:
            fail(f"{req_id} has invalid closure state: {closure!r}")
        live_required = requirement.get("live_required")
        live_evidence = requirement.get("live_evidence") or []
        if not isinstance(live_required, bool):
            fail(f"{req_id} live_required must be boolean")
        if closure == "LIVE_CLOSED" and not live_evidence:
            fail(f"{req_id} claims LIVE_CLOSED without exact live evidence")
        if live_required and closure == "CONTRACT_CLOSED" and live_evidence:
            fail(f"{req_id} has live evidence but remains CONTRACT_CLOSED; classify it explicitly")
        if closure in {"CONTRACT_CLOSED", "LIVE_CLOSED"} and not requirement.get("prs"):
            fail(f"{req_id} closed requirement has no PR lineage")

    print(f"PASS: {len(requirements)} PRD requirements are mechanically traceable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
