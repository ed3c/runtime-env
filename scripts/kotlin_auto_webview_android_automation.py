#!/usr/bin/env python3
import json
import os
import shutil
import sys

BASELINE = {
    "runtime_env_commit": "c0790b9a8c81d7eb45ed45ac3d761c7fad5baa9b",
    "consumer_repository": "ed3c/kotlin-auto-webview",
    "consumer_commit": "8d0ac180971d8aa5a93643165d1a59cf26ed6e71",
    "consumer_tree": "91a288004630abe543fd1402a507173a973aa285",
}
ALLOWED_DEVICE_CLASSES = {"emulator", "physical", "privileged"}


def present_env(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def preflight() -> int:
    device_class = os.environ.get("KAW_ANDROID_DEVICE_CLASS", "emulator").strip()
    if device_class not in ALLOWED_DEVICE_CLASSES:
        print(json.dumps({"schema": "runtime-env/kaw-android-preflight/v1", "state": "FAIL", "reason": "UNDECLARED_DEVICE_CLASS"}, sort_keys=True))
        return 2

    java_present = shutil.which("java") is not None or present_env("JAVA_HOME")
    sdk_present = present_env("ANDROID_SDK_ROOT") or present_env("ANDROID_HOME")
    adb_present = shutil.which("adb") is not None
    emulator_present = shutil.which("emulator") is not None

    requirements = {
        "java": java_present,
        "android_sdk": sdk_present,
        "adb": adb_present,
        "emulator": emulator_present if device_class == "emulator" else None,
    }
    required = [java_present, sdk_present, adb_present]
    if device_class == "emulator":
        required.append(emulator_present)
    state = "PASS" if all(required) else "ABSENT"
    payload = {
        "schema": "runtime-env/kaw-android-preflight/v1",
        "state": state,
        "environment_class": device_class,
        "requirements": requirements,
        "subjects": BASELINE,
        "device_identity": "REDACTED_BY_CONTRACT",
        "secrets": "NOT_READ",
        "execution_claim": "PREFLIGHT_ONLY",
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if state == "PASS" else 3


def render_handoff() -> int:
    payload = {
        "schema": "runtime-env/kaw-local-handoff-readiness/v1",
        "state": "ABSENT",
        "reason": "CONCRETE_PRODUCT_COMMANDS_NOT_YET_BOUND",
        "subjects": BASELINE,
        "missing": [
            "kotlin-auto-webview final Gradle variant/task names",
            "selected adapter implementation heads",
            "receipt schema and cleanup commands",
        ],
        "rule": "This is readiness metadata, not an execution queue and not evidence that local execution occurred.",
    }
    print(json.dumps(payload, sort_keys=True))
    return 3


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in {"preflight", "render-handoff"}:
        print("usage: kotlin_auto_webview_android_automation.py {preflight|render-handoff}", file=sys.stderr)
        return 2
    return preflight() if argv[1] == "preflight" else render_handoff()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
