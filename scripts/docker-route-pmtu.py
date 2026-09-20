#!/usr/bin/python3
# Copyright (c) 2026 Luiz Otávio Miranda
"""Review candidate: eight owned route-PMTU rules; never run apply without approval."""

import fcntl
import json
import os
import shlex
import subprocess
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path

TAG = "docker-route-pmtu:20260910:v1"
TOOLS = ("/usr/sbin/iptables", "/usr/sbin/ip6tables")
ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C"}
EXPECTED_ARGC = 2


def rules() -> Iterator[tuple[str, list[str]]]:
  for tool in TOOLS:
    for interface in ("docker0", "br-+"):
      for direction in ("-i", "-o"):
        yield (
          tool,
          [
            direction,
            interface,
            "-p",
            "tcp",
            "--tcp-flags",
            "SYN,RST",
            "SYN",
            "-m",
            "comment",
            "--comment",
            TAG,
            "-j",
            "TCPMSS",
            "--clamp-mss-to-pmtu",
          ],
        )


def command(tool: str, action: str, rule: Sequence[str]) -> list[str]:
  return [tool, "-w", "5", "-t", "mangle", action, "FORWARD", *rule]


def run(
  args: Sequence[str],
  check: bool = True,  # noqa: FBT001, FBT002 - preserved callable contract
) -> subprocess.CompletedProcess[str]:
  # Callers use fixed absolute executables and internally constructed arguments.
  return subprocess.run(  # noqa: S603
    args, check=check, text=True, capture_output=True, env=ENV, timeout=20
  )


def preflight() -> None:
  state = run(["/usr/bin/systemctl", "is-active", "firewalld"], check=False)
  if state.stdout.strip() != "inactive":
    message = "Require reviewed inactive firewalld; do not change its state"
    raise RuntimeError(message)
  for tool in TOOLS:
    if "(nf_tables)" not in run([tool, "--version"]).stdout:
      message = "Unexpected iptables backend"
      raise RuntimeError(message)


def check_scope() -> None:
  # Run explicitly before first application; boot application precedes Docker.
  docker = ["/usr/bin/docker", "--host", "unix:///var/run/docker.sock"]
  ids = run(
    [*docker, "network", "ls", "--filter", "driver=bridge", "-q"]
  ).stdout.split()
  if not ids:
    message = "No local Docker bridge inventory; refuse application"
    raise RuntimeError(message)
  networks = json.loads(run([*docker, "network", "inspect", *ids]).stdout)
  owned = {
    n["Options"].get("com.docker.network.bridge.name") or "br-" + n["Id"][:12]
    for n in networks
  }

  def covered(name: str) -> bool:
    return name == "docker0" or name.startswith("br-")

  interfaces = {p.name for p in Path("/sys/class/net").iterdir()}
  if any(not covered(name) for name in owned) or any(
    covered(name) and name not in owned for name in interfaces
  ):
    message = "Bridge naming scope changed/collides; require fresh review"
    raise RuntimeError(message)


def rule_exists(tool: str, rule: Sequence[str]) -> bool:
  result = run(command(tool, "-C", rule), check=False)
  if result.returncode == 0:
    return True
  if result.returncode == 1:
    return False
  message = "Rule check failed: " + result.stderr.strip()
  raise RuntimeError(message)


def rollback(added: list[tuple[str, list[str]]]) -> None:
  # Reconcile attempted additions, including a commit followed by timeout.
  # These exact rules were absent before our attempt; prior rules stay.
  for tool, rule in reversed(added):
    try:
      if rule_exists(tool, rule):
        run(command(tool, "-D", rule))
    # Rollback is deliberately best-effort: report every failure while preserving
    # the original application error and continuing with the remaining rules.
    except Exception as cleanup_error:  # noqa: BLE001, PERF203
      removal = shlex.join(command(tool, "-D", rule))
      error_name = type(cleanup_error).__name__
      print(f"ROLLBACK UNRESOLVED: {removal} ({error_name})", file=sys.stderr)


def change(mode: str) -> None:
  # Serialize this helper only; every individual command also takes xtables' lock.
  # Keep builtins.open as the established non-/run test seam.
  with open(  # noqa: PTH123
    "/run/docker-route-pmtu.lock", "a", encoding="utf-8"
  ) as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if mode == "apply":
      preflight()
    added: list[tuple[str, list[str]]] = []
    try:
      for tool, rule in rules():
        exists = rule_exists(tool, rule)
        if mode == "apply" and not exists:
          # Record the absent-before rule before an uncertain subprocess.
          added.append((tool, rule))
          run(command(tool, "-I", ["1", *rule]))
        elif mode == "remove" and exists:
          run(command(tool, "-D", rule))
    except Exception:
      rollback(added)
      # Keep the original failure even if any individual cleanup failed.
      raise


def main() -> None:
  mode = sys.argv[1] if len(sys.argv) == EXPECTED_ARGC else ""
  if mode in ("plan-apply", "plan-remove"):
    for tool, rule in rules():
      print(
        shlex.join(
          command(tool, "-I", ["1", *rule])
          if mode == "plan-apply"
          else command(tool, "-D", rule)
        )
      )
    return
  if mode == "check-scope":
    check_scope()
    print("PASS: current Docker bridge names match the reserved selectors")
    return
  if mode not in ("apply", "remove"):
    message = (
      "usage: docker-route-pmtu.py plan-apply|plan-remove|check-scope|apply|remove"
    )
    raise SystemExit(message)
  if os.geteuid() != 0:
    message = "apply/remove require root and separate operator authorization"
    raise SystemExit(message)
  change(mode)


if __name__ == "__main__":
  main()
