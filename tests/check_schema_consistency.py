#!/usr/bin/env python3
"""Keep published JSON Schema fields aligned with the dependency-free validator."""

from __future__ import annotations

import json
from pathlib import Path
import sys


def main(root: Path) -> int:
    sys.path.insert(0, str(root / "src"))
    from runtime_env.cli import ALLOWED_FIELDS, REQUIRED_FIELDS

    documents = {
        "variables": json.loads((root / "contracts" / "variables.schema.json").read_text()),
        "module": json.loads((root / "contracts" / "module.schema.json").read_text()),
        "profile": json.loads((root / "contracts" / "profile.schema.json").read_text()),
    }
    checks = {
        "variables": documents["variables"],
        "variable": documents["variables"]["properties"]["variables"]["items"],
        "module": documents["module"],
        "profile": documents["profile"],
    }
    for kind, schema in checks.items():
        if schema.get("additionalProperties") is not False:
            raise SystemExit(f"ERROR: {kind} schema must reject additional properties")
        if set(schema["properties"]) != ALLOWED_FIELDS[kind]:
            raise SystemExit(f"ERROR: {kind} allowed fields drifted from validator")
        if set(schema["required"]) != REQUIRED_FIELDS[kind]:
            raise SystemExit(f"ERROR: {kind} required fields drifted from validator")
    print("PASS: published schemas match validator field contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]).resolve()))
