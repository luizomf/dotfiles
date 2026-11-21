# Copyright (c) 2026 Otávio Miranda

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

REPOSITORY = Path(__file__).resolve().parents[1]

# The fixture records how it was called, then replays FIXTURE_OUTPUT as the
# Antigravity stream and exits with FIXTURE_STATUS.
FAKE_EPHEMERAL = f"""#!{sys.executable}
import json, os, sys
with open(os.environ["FIXTURE_LOG"], "w") as log:
    json.dump({{"args": sys.argv[1:], "stdin": sys.stdin.read()}}, log)
sys.stdout.write(os.environ.get("FIXTURE_OUTPUT", ""))
sys.exit(int(os.environ.get("FIXTURE_STATUS", "0")))
"""


def stream(*events: dict[str, Any]) -> str:
  return "".join(json.dumps(event) + "\n" for event in events)


def result(**fields: object) -> dict[str, Any]:
  return {"event": "result", "result": {"status": "SUCCESS", **fields}}


class SannuxAgyStdinTests(unittest.TestCase):
  def setUp(self) -> None:
    temporary = tempfile.TemporaryDirectory()
    self.addCleanup(temporary.cleanup)
    self.root = Path(temporary.name)
    scripts = self.root / "scripts"
    scripts.mkdir()
    self.wrapper = scripts / "sannux_agy_stdin"
    shutil.copyfile(REPOSITORY / "scripts/sannux_agy_stdin", self.wrapper)
    fake = scripts / "sannux_ephemeral"
    fake.write_text(FAKE_EPHEMERAL, encoding="utf-8")
    fake.chmod(0o755)
    self.log = self.root / "call.json"

  def run_wrapper(
    self, prompt: str, output: str, status: int = 0, *args: str
  ) -> subprocess.CompletedProcess[str]:
    # Safe: the wrapper only reaches the fixture sannux_ephemeral beside it.
    return subprocess.run(  # noqa: S603
      ["/bin/bash", str(self.wrapper), *args],
      input=prompt,
      capture_output=True,
      text=True,
      cwd=self.root,
      env={
        **os.environ,
        "FIXTURE_LOG": str(self.log),
        "FIXTURE_OUTPUT": output,
        "FIXTURE_STATUS": str(status),
      },
      check=False,
      timeout=30,
    )

  def call(self) -> dict[str, Any]:
    return json.loads(self.log.read_text(encoding="utf-8"))

  def test_sends_prompt_as_one_stream_message_and_prints_only_the_answer(self):
    prompt = 'Line one\n"quoted" {json} $(not expanded)\n'
    output = stream(
      {"event": "init"},
      {"event": "step_update", "step_update": {"text_delta": "progress"}},
      result(response='{"curated": []}\n'),
    )
    completed = self.run_wrapper(prompt, output, 0, "--model", "gemini-4-hydrogen")
    self.assertEqual(completed.returncode, 0, completed.stderr)
    self.assertEqual(completed.stdout, '{"curated": []}\n')
    call = self.call()
    self.assertEqual(
      json.loads(call["stdin"]),
      {"event": "user", "message": {"role": "user", "content": prompt}},
    )
    self.assertEqual(call["stdin"].count("\n"), 1)
    args = call["args"]
    self.assertEqual(args[:3], ["agy", "--model", "gemini-4-hydrogen"])
    self.assertEqual(args[args.index("--print-timeout") + 1], "900s")
    self.assertEqual(args[args.index("--input-format") + 1], "stream-json")
    self.assertEqual(args[args.index("--output-format") + 1], "stream-json")
    self.assertNotIn(prompt, args)

  def test_keeps_a_caller_print_timeout(self):
    output = stream(result(response="ok"))
    completed = self.run_wrapper("hi", output, 0, "--print-timeout", "60s")
    self.assertEqual(completed.returncode, 0, completed.stderr)
    self.assertEqual(self.call()["args"].count("--print-timeout"), 1)

  def test_failures_exit_nonzero_without_printing_a_partial_answer(self):
    cases = {
      "error status": (stream(result(status="ERROR", error="quota")), 0, "quota"),
      "print timeout": (
        stream(result(response="partial", finished_reason="print_timeout")),
        0,
        "print_timeout",
      ),
      "no result": (stream({"event": "init"}), 0, "no result"),
      "runner failed": (stream(result(response="partial")), 3, "exited with 3"),
    }
    for name, (output, status, message) in cases.items():
      with self.subTest(name):
        completed = self.run_wrapper("hi", output, status)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")
        self.assertIn(message, completed.stderr)

  def test_rejects_an_empty_prompt_before_starting_agy(self):
    completed = self.run_wrapper("", stream(result(response="ok")))
    self.assertEqual(completed.returncode, 2)
    self.assertIn("stdin prompt is empty", completed.stderr)
    self.assertFalse(self.log.exists())


if __name__ == "__main__":
  unittest.main()
