"""Exercise keepwarm argv with fake runners and a disposable process group only."""
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import unittest

REPOSITORY = Path(__file__).resolve().parents[1]


class KeepwarmModelTests(unittest.TestCase):
    def first_pings(self, platform, model=None):
        with tempfile.TemporaryDirectory(prefix="keepwarm-model-") as temporary:
            root = Path(temporary)
            home = root / "home"
            (home / "dotfiles/scripts").mkdir(parents=True)
            tools = root / "bin"
            tools.mkdir()

            def fake(name, source):
                target = tools / name
                target.write_text(f"#!{sys.executable}\n" + source, encoding="utf-8")
                target.chmod(0o755)

            fake("uname", f"print({platform!r})\n")
            fake("pkill", """import json, os, sys
from pathlib import Path
Path(os.environ['PKILL_CAPTURE']).write_text(json.dumps(sys.argv[1:]))
# Do not invoke pkill or signal any process.
""")
            fake("sannux", """import json, os, sys
with open(os.environ['ARGV_CAPTURE'], 'a') as capture:
    capture.write(json.dumps(sys.argv[1:]) + '\\n')
assert sys.stdin.read() == 'Testing. Answer with true\\n'
print('true')
""")
            fake("sleep", """import signal, sys
if sys.argv[1:] == ['10s']:
    raise SystemExit(0)
assert sys.argv[1:] == ['30']
# First Codex/Pi pair is finished. Block until the fixture kills its own group;
# never allow a second pair or call the real sleep command.
print('fixture-first-pings-complete', flush=True)
signal.pause()
""")
            env = {
                "HOME": str(home), "PATH": f"{tools}:/usr/bin:/bin",
                "TMPDIR": str(root), "ARGV_CAPTURE": str(root / "argv.jsonl"),
                "PKILL_CAPTURE": str(root / "pkill.json"),
            }
            if model is not None:
                env["KEEPWARM_CODEX_MODEL"] = model
            process = subprocess.Popen(
                ["/bin/bash", str(REPOSITORY / "scripts/keepwarm")],
                cwd=root, env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            try:
                ready, _, _ = select.select([process.stdout], [], [], 5)
                self.assertTrue(ready, "Fixture did not reach its first ping pair")
                self.assertEqual(process.stdout.readline(), b"fixture-first-pings-complete\n")
                self.assertEqual(process.wait(timeout=5), 0)
                args = [json.loads(line) for line in (root / "argv.jsonl").read_text().splitlines()]
                self.assertEqual(len(args), 2, "Exactly one Codex/Pi pair expected")
                expected_kill = ['-A', '-9', '-f', '[k]eepwarm'] if platform == 'Linux' else ['-9', '-f', '[k]eepwarm']
                self.assertEqual(json.loads((root / "pkill.json").read_text()), expected_kill)
                self.assertEqual(args[1], ['run', 'pi', '-p', '--no-session', '--model',
                                           'openai-codex/gpt-5.6-sol:high'])
                return args[0]
            finally:
                # disown does not leave this fresh session/process group. Signal
                # only the group created above, including the paused fake sleep.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=5)
                process.stdout.close()

    def test_default_uses_codex_configuration_without_model_flag(self):
        for platform in ('Darwin', 'Linux'):
            for model in (None, ''):
                with self.subTest(platform=platform, model=model):
                    self.assertEqual(self.first_pings(platform, model), [
                        'run', 'codex', 'exec', '--yolo', '-', '--ephemeral',
                        '-c', 'model_reasoning_effort=low', '--color', 'never',
                    ])

    def test_explicit_model_is_one_literal_argument(self):
        model = 'fixture-model with spaces;$HOME'
        for platform in ('Darwin', 'Linux'):
            with self.subTest(platform=platform):
                self.assertEqual(self.first_pings(platform, model), [
                    'run', 'codex', 'exec', '--yolo', '-', '--ephemeral',
                    '--model', model, '-c', 'model_reasoning_effort=low', '--color', 'never',
                ])


if __name__ == '__main__':
    unittest.main()
