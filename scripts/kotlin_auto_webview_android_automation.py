#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys

CONSUMER = {
    "repository": "ed3c/kotlin-auto-webview",
    "commit": "4e0eb9bf01ebb90b553da1ef4e69c90eb13fd48a",
    "tree": "74711834806434cee8899930daf9845c0c93d106",
    "issue": 74,
    "pr": 157,
}
ALLOWED_PREFLIGHTS = {
    "preflight-emulator": "emulator",
    "preflight-physical": "physical",
    "preflight-privileged": "privileged",
}
EMULATOR_APIS = [24, 28, 33, 36]


def present_env(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def runtime_subject() -> dict[str, str]:
    def git_value(*args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return "ABSENT"
        return result.stdout.strip()

    return {
        "repository": "ed3c/runtime-env",
        "commit": git_value("rev-parse", "HEAD"),
        "tree": git_value("rev-parse", "HEAD^{tree}"),
    }


def preflight(device_class: str) -> int:
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
        "schema": "runtime-env/kaw-android-preflight/v2",
        "state": state,
        "environment_class": device_class,
        "requirements": requirements,
        "subjects": {
            "runtime_env": runtime_subject(),
            "consumer": CONSUMER,
        },
        "device_identity": "REDACTED_BY_CONTRACT",
        "secrets": "NOT_READ",
        "execution_claim": "PREFLIGHT_ONLY",
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if state == "PASS" else 3


def render_contract() -> int:
    payload = {
        "schema": "runtime-env/kaw-android-runtime-contract/v1",
        "state": "RUNTIME_CONTRACT_COMPLETE",
        "subjects": {
            "runtime_env": runtime_subject(),
            "consumer": CONSUMER,
        },
        "profile": "kotlin-auto-webview-android-automation",
        "workload": "kotlin-auto-webview-android-automation-evidence",
        "emulator_api_allowlist": EMULATOR_APIS,
        "fixed_product_commands": [
            {
                "id": "evidence-contract-self-test",
                "argv": ["python3", "scripts/evidence/android/evidence_contract.py"],
                "cwd": ".",
                "timeout_seconds": 30,
            },
            {
                "id": "selected-source-check",
                "argv": ["python3", "scripts/evidence/android/verify_selected_sources.py"],
                "cwd": ".",
                "timeout_seconds": 120,
            },
            {
                "id": "managed-emulator-evidence",
                "argv": ["bash", "scripts/evidence/android/run-managed-emulator.sh"],
                "cwd": ".",
                "timeout_seconds": 1800,
            },
        ],
        "receipt_contract": "kotlin-auto-webview/android-device-evidence-receipt/v1",
        "evidence_lanes": {
            "L0_STATIC_CONTRACT": "CONSUMER_CI_PROVEN",
            "L1_LOCAL_DETERMINISTIC": "CONSUMER_CI_PROVEN",
            "L2_EMULATOR": "CONSUMER_CI_PROVEN_API_24_28_33_36",
            "L3_PHYSICAL_DEVICE": "NOT_EXERCISED",
            "L4_PRIVILEGED_DEVICE": "NOT_IMPLEMENTED",
            "L5_STORE_POLICY": "HUMAN_ADMIT_REQUIRED",
            "L6_HUMAN_ADMIT": "HUMAN_ADMIT_REQUIRED",
        },
        "accessibility_user_enablement": "HUMAN_LOCAL_AUTHORITY",
        "shizuku_operation": "NOT_IMPLEMENTED",
        "generic_shell": "DENIED",
        "secret_delivery": "NONE",
        "device_identity": "REDACTED_BY_CONTRACT",
        "local_handoff_execution": "NOT_EXERCISED",
        "execution_claim": "CONTRACT_ONLY",
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


def render_handoff() -> int:
    payload = {
        "schema": "runtime-env/kaw-local-handoff-readiness/v2",
        "state": "READY_FOR_QUEUE_COMPILATION",
        "subjects": {
            "runtime_env": runtime_subject(),
            "consumer": CONSUMER,
        },
        "fixed_entrypoints": [
            "preflight-emulator",
            "preflight-physical",
            "preflight-privileged",
            "render-contract",
        ],
        "human_local_gates": [
            "physical device attachment and USB trust",
            "device unlock",
            "AccessibilityService or restricted-settings enablement",
            "any future Shizuku permission",
        ],
        "execution_claim": "QUEUE_COMPILATION_READY_NOT_EXECUTED",
        "rule": "The final Local Handoff Execution Queue is owned by kotlin-auto-webview issue #75. This readiness record is not evidence that any local command or device action executed.",
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: kotlin_auto_webview_android_automation.py {preflight-emulator|preflight-physical|preflight-privileged|render-contract|render-handoff}", file=sys.stderr)
        return 2
    command = argv[1]
    if command in ALLOWED_PREFLIGHTS:
        return preflight(ALLOWED_PREFLIGHTS[command])
    if command == "render-contract":
        return render_contract()
    if command == "render-handoff":
        return render_handoff()
    print("usage: kotlin_auto_webview_android_automation.py {preflight-emulator|preflight-physical|preflight-privileged|render-contract|render-handoff}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
