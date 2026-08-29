import json
import os
import pty
import runpy
import signal
import socket
import subprocess
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
BQ = REPOSITORY / "scripts" / "bq"


class BqCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.home = self.root / "home"
        config_path = self.home / ".config" / "bq" / "config.json"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            json.dumps(
                {"definitionId": "definition-default", "concurrencyDefinitions": {}}
            ),
            encoding="utf-8",
        )
        self.capture_path = self.root / "captured-trigger.json"
        self.definition_log = self.root / "definition-documents.jsonl"
        self.fake_omqueue = self.root / "omqueue"
        self.fake_omqueue.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import json
                import os
                import sys

                arguments = sys.argv[1:]
                if arguments[0] == "trigger":
                    document = json.loads(open(arguments[2], encoding="utf-8").read())
                    open(os.environ["FAKE_CAPTURE"], "w", encoding="utf-8").write(
                        json.dumps(document, ensure_ascii=False)
                    )
                    print(json.dumps({"job": {"jobId": "job-123", "state": "queued"}}))
                    raise SystemExit(0)
                raise SystemExit(f"unsupported fake omqueue arguments: {arguments!r}")
                """
            ),
            encoding="utf-8",
        )
        self.fake_omqueue.chmod(0o755)

    def environment(self) -> dict[str, str]:
        return {
            **os.environ,
            "HOME": str(self.home),
            "BQ_OMQUEUE": str(self.fake_omqueue),
            "FAKE_CAPTURE": str(self.capture_path),
            "FAKE_DEFINITION_LOG": str(self.definition_log),
        }

    def install_definition_fake(self) -> None:
        self.fake_omqueue.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import json
                import os
                import sys
                import uuid

                arguments = sys.argv[1:]
                if arguments[:2] == ["definition", "inspect"]:
                    print(json.dumps({"definition": {"currentRevision": 7}}))
                elif arguments[:2] == ["definition", "apply"]:
                    with open(arguments[2], encoding="utf-8") as handle:
                        document = json.load(handle)
                    with open(os.environ["FAKE_DEFINITION_LOG"], "a", encoding="utf-8") as handle:
                        handle.write(json.dumps(document) + "\\n")
                    definition_id = document.get("definitionId", f"created-{uuid.uuid4()}")
                    print(json.dumps({"result": {"definitionId": definition_id}}))
                elif arguments[:2] == ["definition", "enable"]:
                    print("{}")
                elif arguments[0] == "trigger":
                    print(json.dumps({"job": {"jobId": "job-123", "state": "queued"}}))
                else:
                    raise SystemExit(f"unsupported fake omqueue arguments: {arguments!r}")
                """
            ),
            encoding="utf-8",
        )
        self.fake_omqueue.chmod(0o755)

    def test_submission_does_not_consume_stdin_without_opt_in(self) -> None:
        with tempfile.TemporaryFile() as submission_stdin:
            submission_stdin.write(b"leave this unread")
            submission_stdin.seek(0)
            result = subprocess.run(
                [str(BQ), "--", "/usr/bin/true"],
                stdin=submission_stdin,
                text=True,
                capture_output=True,
                env=self.environment(),
                check=False,
            )
            offset = submission_stdin.tell()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(offset, 0)
        trigger_input = json.loads(self.capture_path.read_text(encoding="utf-8"))
        self.assertNotIn("stdin", trigger_input)

    def test_submission_persists_utf8_text_exactly_with_stdin(self) -> None:
        values = [
            "Olá, 世界\nsecond line with 'single' and \"double\" quotes\n",
            "",
        ]
        for value in values:
            with self.subTest(value=value):
                result = subprocess.run(
                    [str(BQ), "--stdin", "--", "/usr/bin/true"],
                    input=value.encode("utf-8"),
                    capture_output=True,
                    env=self.environment(),
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr.decode())
                trigger_input = json.loads(
                    self.capture_path.read_text(encoding="utf-8")
                )
                self.assertEqual(trigger_input["stdin"], value)

    def test_internal_run_restores_stdin_and_executes_arguments_literally(self) -> None:
        result_path = self.root / "command-result.json"
        shell_marker = self.root / "shell-was-run"
        recorder = self.root / "recorder"
        recorder.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import json
                import sys

                with open(sys.argv[1], "w", encoding="utf-8") as handle:
                    json.dump(
                        {"arguments": sys.argv[2:], "stdin": sys.stdin.read()},
                        handle,
                        ensure_ascii=False,
                    )
                """
            ),
            encoding="utf-8",
        )
        recorder.chmod(0o755)
        stdin_text = f"line one\n$(touch {shell_marker}) 'quoted' 世界\n"
        literal_arguments = [
            f"$(touch {shell_marker})",
            "; echo not-a-command",
            "quote'\"value",
        ]
        trigger_input = {
            "executable": str(recorder),
            "arguments": [str(result_path), *literal_arguments],
            "workingDirectory": str(self.root),
            "stdin": stdin_text,
        }

        result = subprocess.run(
            [str(BQ), "--internal-run"],
            input=json.dumps(trigger_input, ensure_ascii=False).encode("utf-8"),
            capture_output=True,
            env=self.environment(),
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode())
        command_result = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertEqual(command_result["stdin"], stdin_text)
        self.assertEqual(command_result["arguments"], literal_arguments)
        self.assertFalse(shell_marker.exists())

    def test_linux_session_environment_uses_only_a_private_owned_runtime(self) -> None:
        runtime_path = self.root / "run" / str(os.getuid())
        runtime_path.mkdir(parents=True, mode=0o700)
        runtime_path.chmod(0o700)
        bus_path = runtime_path / "bus"

        with socket.socket(socket.AF_UNIX) as bus:
            bus.bind(str(bus_path))
            module = runpy.run_path(str(BQ))
            environment = module["linux_session_environment"](
                runtime_path, os.getuid()
            )

        self.assertEqual(
            environment,
            {
                "XDG_RUNTIME_DIR": str(runtime_path),
                "DBUS_SESSION_BUS_ADDRESS": f"unix:path={bus_path}",
            },
        )

        runtime_path.chmod(0o755)
        self.assertEqual(
            module["linux_session_environment"](runtime_path, os.getuid()), {}
        )

    def test_stdin_rejects_an_interactive_terminal(self) -> None:
        master, slave = pty.openpty()
        self.addCleanup(os.close, master)
        result = subprocess.run(
            [str(BQ), "--stdin", "--", "/usr/bin/true"],
            stdin=slave,
            capture_output=True,
            env=self.environment(),
            check=False,
        )
        os.close(slave)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"requires piped or redirected UTF-8 input", result.stderr)

    def test_legacy_trigger_without_stdin_still_executes(self) -> None:
        result_path = self.root / "legacy-stdin.txt"
        recorder = self.root / "legacy-recorder"
        recorder.write_text(
            "#!/usr/bin/env python3\n"
            "import pathlib, sys\n"
            "pathlib.Path(sys.argv[1]).write_text(sys.stdin.read(), encoding='utf-8')\n",
            encoding="utf-8",
        )
        recorder.chmod(0o755)
        trigger_input = {
            "executable": str(recorder),
            "arguments": [str(result_path)],
            "workingDirectory": str(self.root),
        }

        result = subprocess.run(
            [str(BQ), "--internal-run"],
            input=json.dumps(trigger_input).encode(),
            capture_output=True,
            env=self.environment(),
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(result_path.read_text(encoding="utf-8"), "")

    def test_json_immediate_submission_prints_only_accepted_job(self) -> None:
        result = subprocess.run(
            [str(BQ), "--json", "--", "/usr/bin/true"],
            input=b"",
            capture_output=True,
            env=self.environment(),
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(
            json.loads(result.stdout),
            {"jobId": "job-123", "state": "queued"},
        )
        self.assertEqual(result.stdout.count(b"\n"), 1)

    def test_setup_reconciles_optional_stdin_for_serial_definitions(self) -> None:
        config_path = self.home / ".config" / "bq" / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "definitionId": "definition-default",
                    "concurrencyDefinitions": {"serial-key": "definition-serial"},
                }
            ),
            encoding="utf-8",
        )
        self.install_definition_fake()

        result = subprocess.run(
            [str(BQ), "--setup"],
            capture_output=True,
            env=self.environment(),
            check=False,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        documents = [
            json.loads(line)
            for line in self.definition_log.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(len(documents), 2)
        for document in documents:
            schema = document["triggerInputSchema"]
            self.assertEqual(schema["properties"]["stdin"], {"type": "string"})
            self.assertNotIn("stdin", schema["required"])
        serial_document = next(
            document
            for document in documents
            if document.get("definitionId") == "definition-serial"
        )
        self.assertEqual(serial_document["concurrencyKey"], "serial-key")
        saved_config = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(
            saved_config["concurrencyDefinitions"],
            {"serial-key": "definition-serial"},
        )

    def test_lazy_concurrency_setup_does_not_contaminate_json_stdout(self) -> None:
        self.install_definition_fake()

        result = subprocess.run(
            [
                str(BQ),
                "--json",
                "--concurrency-key",
                "new-serial-key",
                "--",
                "/usr/bin/true",
            ],
            input=b"",
            capture_output=True,
            env=self.environment(),
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(
            json.loads(result.stdout),
            {"jobId": "job-123", "state": "queued"},
        )
        self.assertNotIn(b"ready concurrency key", result.stdout)
        self.assertIn(b"ready concurrency key", result.stderr)

    def test_json_rejects_scheduling_and_setup(self) -> None:
        scheduled = subprocess.run(
            [str(BQ), "--json", "--in", "1m", "--", "/usr/bin/true"],
            capture_output=True,
            env=self.environment(),
            check=False,
        )
        setup = subprocess.run(
            [str(BQ), "--setup", "--json"],
            capture_output=True,
            env=self.environment(),
            check=False,
        )

        self.assertNotEqual(scheduled.returncode, 0)
        self.assertIn(b"only for immediate submissions", scheduled.stderr)
        self.assertNotEqual(setup.returncode, 0)
        self.assertIn(b"cannot be combined", setup.stderr)

    def test_cancellation_terminates_owned_process_group_with_durable_stdin(
        self,
    ) -> None:
        leader_marker = self.root / "leader-terminated"
        child_marker = self.root / "child-terminated"
        ready_marker = self.root / "processes-ready"
        runner = self.root / "process-group-runner"
        runner.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import pathlib
                import signal
                import subprocess
                import sys
                import time

                leader_marker, child_marker, ready_marker = map(pathlib.Path, sys.argv[1:])
                child_code = '''
                import pathlib, signal, sys, time
                marker = pathlib.Path(sys.argv[1])
                ready = pathlib.Path(sys.argv[2])
                def stop(signum, frame):
                    marker.write_text("terminated", encoding="utf-8")
                    raise SystemExit(0)
                signal.signal(signal.SIGTERM, stop)
                ready.write_text("ready", encoding="utf-8")
                while True: time.sleep(1)
                '''
                child_ready = ready_marker.with_suffix(".child")
                subprocess.Popen([sys.executable, "-c", child_code, str(child_marker), str(child_ready)])
                while not child_ready.exists():
                    time.sleep(0.01)
                def stop(signum, frame):
                    leader_marker.write_text("terminated", encoding="utf-8")
                    raise SystemExit(0)
                signal.signal(signal.SIGTERM, stop)
                ready_marker.write_text("ready", encoding="utf-8")
                while True: time.sleep(1)
                """
            ),
            encoding="utf-8",
        )
        runner.chmod(0o755)
        trigger_input = {
            "executable": str(runner),
            "arguments": [
                str(leader_marker),
                str(child_marker),
                str(ready_marker),
            ],
            "workingDirectory": str(self.root),
            "stdin": "durable input",
        }
        process = subprocess.Popen(
            [str(BQ), "--internal-run"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=self.environment(),
            start_new_session=True,
        )

        def terminate_process_group() -> None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass

        self.addCleanup(terminate_process_group)
        assert process.stdin is not None
        process.stdin.write(json.dumps(trigger_input).encode("utf-8"))
        process.stdin.close()
        deadline = time.monotonic() + 5
        while not ready_marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(ready_marker.exists(), "process group did not become ready")

        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
        deadline = time.monotonic() + 5
        while not child_marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)

        self.assertTrue(leader_marker.exists())
        self.assertTrue(child_marker.exists())

    def test_invalid_utf8_stdin_fails_without_submitting(self) -> None:
        result = subprocess.run(
            [str(BQ), "--stdin", "--", "/usr/bin/true"],
            input=b"\xff",
            capture_output=True,
            env=self.environment(),
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"not valid UTF-8", result.stderr)
        self.assertFalse(self.capture_path.exists())

    def test_queue_resource_limit_rejection_is_returned(self) -> None:
        self.fake_omqueue.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "print('trigger input exceeds resource limit', file=sys.stderr)\n"
            "raise SystemExit(23)\n",
            encoding="utf-8",
        )
        self.fake_omqueue.chmod(0o755)

        result = subprocess.run(
            [str(BQ), "--stdin", "--", "/usr/bin/true"],
            input=("á" * 100).encode("utf-8"),
            capture_output=True,
            env=self.environment(),
            check=False,
        )

        self.assertEqual(result.returncode, 23)
        self.assertIn(b"exceeds resource limit", result.stderr)

    def test_help_warns_that_stdin_is_durable_and_not_for_secrets(self) -> None:
        result = subprocess.run(
            [str(BQ), "--help"],
            capture_output=True,
            env=self.environment(),
            check=False,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--stdin", result.stdout)
        self.assertIn("durable Queue data", result.stdout)
        self.assertIn("Do not use it for", result.stdout)
        self.assertIn("secrets", result.stdout)

    def test_default_immediate_submission_keeps_human_acceptance_line(self) -> None:
        result = subprocess.run(
            [str(BQ), "--", "/usr/bin/true"],
            input=b"",
            capture_output=True,
            env=self.environment(),
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(result.stdout, b"bq: accepted Job job-123 (queued)\n")


if __name__ == "__main__":
    unittest.main()
