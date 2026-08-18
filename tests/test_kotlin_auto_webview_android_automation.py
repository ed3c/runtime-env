import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "kotlin_auto_webview_android_automation.py"


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

    def test_render_handoff_never_claims_execution(self):
        result = self.run_script("render-handoff")
        self.assertEqual(result.returncode, 3)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["state"], "ABSENT")
        self.assertIn("not evidence", payload["rule"])

    def test_unknown_command_is_rejected(self):
        for command in ("adb shell", "preflight-arbitrary", "sh -c"):
            with self.subTest(command=command):
                result = self.run_script(command)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")

    def test_no_device_selector_is_reflected_to_public_receipt(self):
        result = self.run_script("preflight-physical", {"ANDROID_SERIAL": "private-device-123"})
        self.assertIn(result.returncode, {0, 3})
        self.assertNotIn("private-device-123", result.stdout)


if __name__ == "__main__":
    unittest.main()
