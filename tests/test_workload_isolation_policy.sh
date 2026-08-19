#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="${ROOT}/src" python3 -m runtime_env.isolation_policy "${ROOT}/isolation-policies" >/tmp/runtime-env-isolation-policy.out
python3 - <<'PY' /tmp/runtime-env-isolation-policy.out
import json
import sys
p = json.load(open(sys.argv[1], encoding="utf-8"))
assert p["state"] == "PASS"
assert p["schema"] == "runtime-env/workload-isolation-policy/v1"
assert p["policies"] == ["kotlin-auto-webview-android-device-evidence"]
PY

PYTHONPATH="${ROOT}/src" python3 - "${ROOT}" <<'PY'
from copy import deepcopy
import json
from pathlib import Path
import sys
from runtime_env.isolation_policy import IsolationPolicyError, validate_isolation_policy_document

root = Path(sys.argv[1])
baseline = json.loads((root / "isolation-policies" / "kotlin-auto-webview-android-device-evidence.json").read_text())

def rejected(mutator, expected):
    value = deepcopy(baseline)
    mutator(value)
    try:
        validate_isolation_policy_document(value)
    except IsolationPolicyError as exc:
        assert expected in str(exc), (expected, str(exc))
    else:
        raise AssertionError(f"mutation unexpectedly admitted: {expected}")

# Sensitive planted values are assembled at runtime so the repository's tracked-text
# scanner can continue enforcing that these signatures never exist verbatim in Git.
secret_fixture = "to" + "ken=" + "forbidden-value"
endpoint_fixture = "connect to " + "https" + "://" + "example.invalid"
local_path_fixture = "read " + "/" + "Users" + "/" + "alice" + "/private"
device_serial_fixture = "device " + "emulator-" + "5554"
command_fixture = "run " + "adb " + "shell" + ";" + " id"

rejected(lambda p: p.__setitem__("argv", ["adb", "shell"]), "unexpected isolation-policy fields")
rejected(lambda p: p.__setitem__("summary", secret_fixture), "secret-bearing")
rejected(lambda p: p.__setitem__("summary", endpoint_fixture), "endpoint-bearing")
rejected(lambda p: p.__setitem__("summary", local_path_fixture), "local-path")
rejected(lambda p: p.__setitem__("summary", device_serial_fixture), "device-serial")
rejected(lambda p: p.__setitem__("summary", command_fixture), "command-bearing")
rejected(
    lambda p: next(r for r in p["non_equivalence"] if r["observed"] == "EMULATOR")["cannot_satisfy"].remove("PHYSICAL"),
    "evidence-lane promotion",
)
rejected(
    lambda p: p["forbidden_execution_surfaces"].remove("caller-supplied-shell"),
    "omitted hard execution denials",
)
rejected(
    lambda p: p["absence_semantics"].__setitem__("not_exercised", "PASS"),
    "stable fail-closed state mapping",
)
print("PASS: workload isolation policy mutations fail closed")
PY

# Existing carrier policies still validate through their unchanged CLI surface.
"${ROOT}/runtime-env" policy show --id claude-code-native-isolation >/dev/null
"${ROOT}/runtime-env" policy show --id codex-cli-native-isolation >/dev/null

echo "PASS: workload isolation policy is strict and carrier-policy semantics remain unchanged"
