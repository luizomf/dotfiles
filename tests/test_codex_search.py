import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "codex_search"


class CodexSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.capture = self.root / "capture.json"
        fake = self.root / "codex"
        fake.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "Path(os.environ['FAKE_CAPTURE']).write_text(json.dumps({"
            "'args': sys.argv[1:], 'stdin': sys.stdin.read()}))\n"
        )
        fake.chmod(0o755)
        self.env = {
            key: value for key, value in os.environ.items()
            if not key.startswith("CODEX_SEARCH_")
        }
        self.env.update(
            PATH=f"{self.root}{os.pathsep}{os.environ['PATH']}",
            FAKE_CAPTURE=str(self.capture),
        )

    def invoke(self, *args: str) -> dict:
        result = subprocess.run(
            [str(SCRIPT), *args, "-"], input="A literal prompt; $(not a shell)",
            text=True, capture_output=True, env=self.env, check=True,
        )
        self.assertIn("user_config=ignored", result.stderr)
        return json.loads(self.capture.read_text())

    def test_default_profiles_use_astra_and_preserve_reasoning(self) -> None:
        for profile, effort in (("quick", "low"), ("research", "medium")):
            with self.subTest(profile=profile):
                captured = self.invoke("--profile", profile)
                self.assertEqual(captured["args"], [
                    "--search", "--model", "gpt-6-astra",
                    "-c", f"model_reasoning_effort={effort}", "exec",
                    "--ephemeral", "--ignore-user-config",
                    "--sandbox", "read-only", "-",
                ])
                self.assertEqual(captured["stdin"], "A literal prompt; $(not a shell)")

    def test_profile_override_and_yolo_remain_explicit(self) -> None:
        self.env["CODEX_SEARCH_RESEARCH_MODEL"] = "profile-model"
        self.env["CODEX_SEARCH_RESEARCH_REASONING"] = "high"
        captured = self.invoke("--profile=research", "--yolo")
        self.assertEqual(captured["args"][2:5], [
            "profile-model", "-c", "model_reasoning_effort=high",
        ])
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", captured["args"])
        self.assertNotIn("--sandbox", captured["args"])

    def test_invocation_overrides_take_precedence(self) -> None:
        self.env.update(
            CODEX_SEARCH_QUICK_MODEL="profile-model",
            CODEX_SEARCH_MODEL="invocation-model", CODEX_SEARCH_REASONING="high",
        )
        captured = self.invoke("--write", "--cd", "a path with spaces")
        self.assertEqual(captured["args"][2:5], [
            "invocation-model", "-c", "model_reasoning_effort=high",
        ])
        self.assertEqual(captured["args"][-5:], [
            "--sandbox", "workspace-write", "--cd", "a path with spaces", "-",
        ])


if __name__ == "__main__":
    unittest.main()
