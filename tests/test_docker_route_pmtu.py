"""Control-flow tests only: no real firewall, files in /run, or subprocesses."""
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import mock_open, patch

spec = importlib.util.spec_from_file_location(
    "candidate", Path(__file__).resolve().parents[1] / "scripts" / "docker-route-pmtu.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Fake:
    def __init__(self, fail_insert=None, timeout_insert=None, timeout_delete=None):
        self.state = set()
        self.inserts = 0
        self.deletes = 0
        self.fail_insert = fail_insert
        self.timeout_insert = timeout_insert
        self.timeout_delete = timeout_delete

    def run(self, args, check=True):
        action = args[5]
        rule = tuple(args[8:] if action == "-I" else args[7:])
        key = (args[0], rule)
        rc = 0
        if action == "-C":
            rc = 0 if key in self.state else 1
        elif action == "-I":
            self.inserts += 1
            if self.inserts == self.fail_insert:
                raise subprocess.CalledProcessError(2, args)
            self.state.add(key)
            if self.inserts == self.timeout_insert:
                raise subprocess.TimeoutExpired(args, 20)
        elif action == "-D":
            self.deletes += 1
            if self.deletes == self.timeout_delete:
                raise subprocess.TimeoutExpired(args, 20)
            self.state.remove(key)
        else:
            raise AssertionError(args)
        return subprocess.CompletedProcess(args, rc, stdout="", stderr="")


class CandidateTests(unittest.TestCase):
    def execute(self, fake, mode):
        with patch.object(m, "run", fake.run), patch.object(m, "preflight"), \
             patch("builtins.open", mock_open()), patch.object(m.fcntl, "flock"):
            m.change(mode)

    def test_scope_and_dynamic_flags(self):
        rules = list(m.rules())
        self.assertEqual(len(rules), 8)
        for tool, rule in rules:
            self.assertIn(tool, m.TOOLS)
            self.assertIn(rule[0], ("-i", "-o"))
            self.assertIn(rule[1], ("docker0", "br-+"))
            self.assertIn("--clamp-mss-to-pmtu", rule)
            self.assertNotIn("--set-mss", rule)
            self.assertEqual(rule[rule.index("--tcp-flags") + 1:][:2], ["SYN,RST", "SYN"])
            self.assertNotIn("wg0", rule)
            self.assertNotIn("wld0", rule)

    def test_idempotence_and_exact_removal(self):
        fake = Fake()
        unrelated = ("other", ("unrelated-rule",))
        fake.state.add(unrelated)
        self.execute(fake, "apply")
        self.execute(fake, "apply")
        self.assertEqual(fake.inserts, 8)
        self.assertEqual(len(fake.state), 9)
        self.execute(fake, "remove")
        self.execute(fake, "remove")
        self.assertEqual(fake.state, {unrelated})

    def test_partial_failure_preserves_preexisting(self):
        fake = Fake(fail_insert=3)
        tool, rule = next(m.rules())
        preexisting = {(tool, tuple(rule)), ("other", ("unrelated-rule",))}
        fake.state.update(preexisting)
        with self.assertRaises(subprocess.CalledProcessError):
            self.execute(fake, "apply")
        self.assertEqual(fake.state, preexisting)

    def test_committed_insertion_timeout_is_reconciled(self):
        fake = Fake(timeout_insert=3)
        tool, rule = next(m.rules())
        preexisting = {(tool, tuple(rule)), ("other", ("unrelated",))}
        fake.state.update(preexisting)
        with self.assertRaises(subprocess.TimeoutExpired):
            self.execute(fake, "apply")
        self.assertEqual(fake.state, preexisting)

    def test_rollback_exception_does_not_skip_remaining_or_mask_original(self):
        fake = Fake(fail_insert=4, timeout_delete=1)
        with patch("builtins.print") as output:
            with self.assertRaises(subprocess.CalledProcessError):
                self.execute(fake, "apply")
        self.assertEqual(fake.deletes, 3)
        self.assertEqual(len(fake.state), 1)
        self.assertTrue(any("ROLLBACK" in str(call) for call in output.call_args_list))

    def test_remove_does_not_require_docker_or_firewalld_state(self):
        fake = Fake()
        with patch.object(m, "run", fake.run), \
             patch.object(m, "preflight", side_effect=AssertionError("called preflight")), \
             patch("builtins.open", mock_open()), patch.object(m.fcntl, "flock"):
            m.change("remove")

    def test_plan_has_no_runtime_calls(self):
        for mode in ("plan-apply", "plan-remove"):
            with patch.object(m.sys, "argv", ["candidate", mode]), \
                 patch.object(m, "run", side_effect=AssertionError("runtime call")), \
                 patch("builtins.print") as output:
                m.main()
                self.assertEqual(output.call_count, 8)


if __name__ == "__main__":
    unittest.main()
