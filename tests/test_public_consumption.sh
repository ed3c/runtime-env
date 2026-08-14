#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOC="${ROOT}/docs/public-consumption.md"

[[ -f "${DOC}" ]] || {
  echo "FAIL: public consumption contract is absent" >&2
  exit 1
}

grep -Fq 'public-consumption.md' "${ROOT}/docs/INDEX.md" || {
  echo "FAIL: docs/INDEX.md does not route to the public consumption contract" >&2
  exit 1
}

for required in \
  'No credential is required' \
  'Pin by commit SHA' \
  'a Git tag is a mutable ref' \
  'runtime-env verify-consumer --target-root' \
  'Never hand-edit a resolved'; do
  grep -Fq "${required}" "${DOC}" || {
    echo "FAIL: public consumption contract omitted ${required}" >&2
    exit 1
  }
done

# The document states three pin constraints as facts about the published schema.
# Assert them against the schema itself, so loosening the contract reddens here
# instead of silently turning the document into a false claim.
python3 - "${ROOT}" <<'PY'
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
schema = json.loads(
    (root / "contracts" / "consumer-binding.schema.json").read_text(encoding="utf-8")
)
source = schema["properties"]["source"]

expected_required = {"repository", "commit", "tree"}
actual_required = set(source["required"])
if not expected_required <= actual_required:
    print(
        "FAIL: consumer binding no longer requires the documented pin fields: "
        f"missing {sorted(expected_required - actual_required)}",
        file=sys.stderr,
    )
    raise SystemExit(1)

expected_patterns = {
    "repository": "^https://",
    "commit": "^[0-9a-f]{40}$",
    "tree": "^[0-9a-f]{40}$",
}
for field, pattern in expected_patterns.items():
    actual = source["properties"][field].get("pattern")
    if actual != pattern:
        print(
            f"FAIL: documented pin constraint for source.{field} is {pattern!r} "
            f"but the schema enforces {actual!r}",
            file=sys.stderr,
        )
        raise SystemExit(1)

print("PASS: documented pin constraints match the published binding schema")
PY

echo "PASS: public consumption contract"
