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

    def test_undeclared_device_class_fails_closed(self):
        result = self.run_script("preflight", {"KAW_ANDROID_DEVICE_CLASS": "arbitrary-shell"})
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["state"], "FAIL")
        self.assertEqual(payload["reason"], "UNDECLARED_DEVICE_CLASS")

    def test_render_handoff_never_claims_execution(self):
        result = self.run_script("render-handoff")
        self.assertEqual(result.returncode, 3)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["state"], "ABSENT")
        self.assertIn("not evidence", payload["rule"])

    def test_unknown_command_is_rejected(self):
        result = self.run_script("adb shell")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
