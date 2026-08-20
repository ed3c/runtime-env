import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "kotlin_auto_webview_android_automation.py"
EXPECTED_CONSUMER_COMMIT = "4e0eb9bf01ebb90b553da1ef4e69c90eb13fd48a"
EXPECTED_CONSUMER_TREE = "74711834806434cee8899930daf9845c0c93d106"


class KotlinAutoWebViewAndroidAutomationTest(unittest.TestCase):
    def run_script(self, command: str, env: dict[str, str] | None = None):
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        return subprocess.run(
            [sys.executable, str(SCRIPT), command],
            env=run_env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_each_preflight_binds_exact_environment_class(self):
        for command, expected in (
            ("preflight-emulator", "emulator"),
            ("preflight-physical", "physical"),
            ("preflight-privileged", "privileged"),
        ):
            with self.subTest(command=command):
                result = self.run_script(command)
                self.assertIn(result.returncode, {0, 3})
                payload = json.loads(result.stdout)
                self.assertEqual(payload["environment_class"], expected)
                self.assertEqual(payload["execution_claim"], "PREFLIGHT_ONLY")
                self.assertEqual(payload["device_identity"], "REDACTED_BY_CONTRACT")
                self.assertEqual(payload["secrets"], "NOT_READ")
                self.assertEqual(payload["subjects"]["consumer"]["commit"], EXPECTED_CONSUMER_COMMIT)
                self.assertEqual(payload["subjects"]["consumer"]["tree"], EXPECTED_CONSUMER_TREE)

    def test_render_contract_binds_exact_consumer_and_runtime_subject(self):
        result = self.run_script("render-contract")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["state"], "RUNTIME_CONTRACT_COMPLETE")
        self.assertEqual(payload["execution_claim"], "CONTRACT_ONLY")
        self.assertEqual(payload["subjects"]["consumer"]["repository"], "ed3c/kotlin-auto-webview")
        self.assertEqual(payload["subjects"]["consumer"]["commit"], EXPECTED_CONSUMER_COMMIT)
        self.assertEqual(payload["subjects"]["consumer"]["tree"], EXPECTED_CONSUMER_TREE)
        self.assertEqual(payload["subjects"]["consumer"]["issue"], 74)
        self.assertEqual(payload["subjects"]["consumer"]["pr"], 157)
        runtime = payload["subjects"]["runtime_env"]
        self.assertEqual(runtime["repository"], "ed3c/runtime-env")
        self.assertRegex(runtime["commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(runtime["tree"], r"^[0-9a-f]{40}$")
        self.assertEqual(payload["emulator_api_allowlist"], [24, 28, 33, 36])
        self.assertEqual(payload["evidence_lanes"]["L2_EMULATOR"], "CONSUMER_CI_PROVEN_API_24_28_33_36")
        self.assertEqual(payload["evidence_lanes"]["L3_PHYSICAL_DEVICE"], "NOT_EXERCISED")
        self.assertEqual(payload["evidence_lanes"]["L4_PRIVILEGED_DEVICE"], "NOT_IMPLEMENTED")
        self.assertEqual(payload["local_handoff_execution"], "NOT_EXERCISED")
        self.assertEqual(payload["generic_shell"], "DENIED")
        command_ids = [item["id"] for item in payload["fixed_product_commands"]]
        self.assertEqual(
            command_ids,
            ["evidence-contract-self-test", "selected-source-check", "managed-emulator-evidence"],
        )
        for command in payload["fixed_product_commands"]:
            argv = command["argv"]
            joined = " ".join(argv)
            self.assertNotIn("adb shell", joined)
            self.assertNotIn("sh -c", joined)
            self.assertEqual(command["cwd"], ".")
            self.assertGreater(command["timeout_seconds"], 0)

    def test_render_handoff_is_ready_for_compilation_but_never_execution(self):
        result = self.run_script("render-handoff")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["state"], "READY_FOR_QUEUE_COMPILATION")
        self.assertEqual(payload["execution_claim"], "QUEUE_COMPILATION_READY_NOT_EXECUTED")
        self.assertIn("#75", payload["rule"])
        self.assertIn("not evidence", payload["rule"])
        self.assertIn("AccessibilityService or restricted-settings enablement", payload["human_local_gates"])

    def test_unknown_command_is_rejected(self):
        for command in ("adb shell", "preflight-arbitrary", "sh -c", "render-contract && sh"):
            with self.subTest(command=command):
                result = self.run_script(command)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")

    def test_no_device_selector_is_reflected_to_public_receipt(self):
        result = self.run_script("preflight-physical", {"ANDROID_SERIAL": "private-device-123"})
        self.assertIn(result.returncode, {0, 3})
        self.assertNotIn("private-device-123", result.stdout)

    def test_render_contract_does_not_reflect_secret_or_private_environment_values(self):
        result = self.run_script(
            "render-contract",
            {
                "ANDROID_SERIAL": "private-device-123",
                "TOKEN": "private-token-value",
                "PRIVATE_ENDPOINT": "https://private.invalid/secret",
            },
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("private-device-123", result.stdout)
        self.assertNotIn("private-token-value", result.stdout)
        self.assertNotIn("private.invalid", result.stdout)


if __name__ == "__main__":
    unittest.main()
