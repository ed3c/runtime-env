#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

tracked_sensitive="$(git -C "${ROOT}" ls-files | grep -E '(^|/)\.env($|\.)|\.(p8|pem|key)$' | grep -vE '\.env\..*example$|\.env\.example$' || true)"
[[ -z "${tracked_sensitive}" ]] || {
  echo "FAIL: tracked value-bearing file type detected:" >&2
  echo "${tracked_sensitive}" >&2
  exit 1
}

python3 - "${ROOT}" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
for path in sorted(root.glob("**/*.json")):
    if ".git" in path.parts:
        continue
    json.loads(path.read_text(encoding="utf-8"))
print("PASS: every JSON document parses")
PY

echo "PASS: repository safety boundary"
