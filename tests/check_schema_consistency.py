#!/usr/bin/env python3
"""Keep published JSON Schema fields aligned with dependency-free validators."""

from __future__ import annotations

import json
from pathlib import Path
import sys


def main(root: Path) -> int:
    sys.path.insert(0, str(root / "src"))
    from runtime_env.cli import ALLOWED_FIELDS, REQUIRED_FIELDS
    from runtime_env.isolation_policy import (
        ALLOWED_FIELDS as ISOLATION_ALLOWED_FIELDS,
        REQUIRED_FIELDS as ISOLATION_REQUIRED_FIELDS,
    )

    documents = {
        "variables": json.loads((root / "contracts" / "variables.schema.json").read_text()),
        "module": json.loads((root / "contracts" / "module.schema.json").read_text()),
        "profile": json.loads((root / "contracts" / "profile.schema.json").read_text()),
        "workload": json.loads((root / "contracts" / "workload.schema.json").read_text()),
        "policy": json.loads((root / "contracts" / "carrier-policy.schema.json").read_text()),
    }
    checks = {
        "variables": documents["variables"],
        "variable": documents["variables"]["properties"]["variables"]["items"],
        "module": documents["module"],
        "profile": documents["profile"],
        "workload": documents["workload"],
        "policy": documents["policy"],
    }
    for kind, schema in checks.items():
        if schema.get("additionalProperties") is not False:
            raise SystemExit(f"ERROR: {kind} schema must reject additional properties")
        if set(schema["properties"]) != ALLOWED_FIELDS[kind]:
            raise SystemExit(f"ERROR: {kind} allowed fields drifted from validator")
        if set(schema["required"]) != REQUIRED_FIELDS[kind]:
            raise SystemExit(f"ERROR: {kind} required fields drifted from validator")

    isolation = json.loads((root / "contracts" / "workload-isolation-policy.schema.json").read_text())
    if isolation.get("additionalProperties") is not False:
        raise SystemExit("ERROR: isolation policy schema must reject additional properties")
    if set(isolation["properties"]) != ISOLATION_ALLOWED_FIELDS:
        raise SystemExit("ERROR: isolation policy allowed fields drifted from validator")
    if set(isolation["required"]) != ISOLATION_REQUIRED_FIELDS:
        raise SystemExit("ERROR: isolation policy required fields drifted from validator")
    for nested in (
        isolation["properties"]["non_equivalence"]["items"],
        isolation["properties"]["absence_semantics"],
        isolation["$defs"]["repositoryReference"],
    ):
        if nested.get("additionalProperties") is not False:
            raise SystemExit("ERROR: isolation policy nested schemas must reject additional properties")

    print("PASS: published schemas match validator field contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]).resolve()))
