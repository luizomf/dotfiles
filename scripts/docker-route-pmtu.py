#!/usr/bin/python3
"""Review candidate: eight owned route-PMTU rules; never run apply without approval."""
import fcntl
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

TAG = "docker-route-pmtu:20260910:v1"
TOOLS = ("/usr/sbin/iptables", "/usr/sbin/ip6tables")
ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C"}


def rules():
    for tool in TOOLS:
        for interface in ("docker0", "br-+"):
            for direction in ("-i", "-o"):
                yield tool, [direction, interface, "-p", "tcp", "--tcp-flags",
                             "SYN,RST", "SYN", "-m", "comment", "--comment", TAG,
                             "-j", "TCPMSS", "--clamp-mss-to-pmtu"]


def command(tool, action, rule):
    return [tool, "-w", "5", "-t", "mangle", action, "FORWARD", *rule]


def run(args, check=True):
    return subprocess.run(args, check=check, text=True, capture_output=True,
                          env=ENV, timeout=20)


def preflight():
    state = run(["/usr/bin/systemctl", "is-active", "firewalld"], check=False)
    if state.stdout.strip() != "inactive":
        raise RuntimeError("Require reviewed inactive firewalld; do not change its state")
    for tool in TOOLS:
        if "(nf_tables)" not in run([tool, "--version"]).stdout:
            raise RuntimeError("Unexpected iptables backend")


def check_scope():
    # Run explicitly before first application; boot application precedes Docker.
    docker = ["/usr/bin/docker", "--host", "unix:///var/run/docker.sock"]
    ids = run(docker + ["network", "ls", "--filter", "driver=bridge", "-q"]).stdout.split()
    if not ids:
        raise RuntimeError("No local Docker bridge inventory; refuse application")
    networks = json.loads(run(docker + ["network", "inspect", *ids]).stdout)
    owned = {n["Options"].get("com.docker.network.bridge.name") or "br-" + n["Id"][:12]
             for n in networks}
    covered = lambda name: name == "docker0" or name.startswith("br-")
    interfaces = {p.name for p in Path("/sys/class/net").iterdir()}
    if any(not covered(name) for name in owned) or any(
            covered(name) and name not in owned for name in interfaces):
        raise RuntimeError("Bridge naming scope changed/collides; require fresh review")


def change(mode):
    # Serialize this helper only; every individual command also takes xtables' lock.
    with open("/run/docker-route-pmtu.lock", "a", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if mode == "apply":
            preflight()
        added = []
        try:
            for tool, rule in rules():
                result = run(command(tool, "-C", rule), check=False)
                if result.returncode not in (0, 1):
                    raise RuntimeError("Rule check failed: " + result.stderr.strip())
                if mode == "apply" and result.returncode == 1:
                    # Record the absent-before rule before an uncertain subprocess.
                    added.append((tool, rule))
                    run(command(tool, "-I", ["1", *rule]))
                elif mode == "remove" and result.returncode == 0:
                    run(command(tool, "-D", rule))
        except Exception:
            # Reconcile attempted additions, including a commit followed by timeout.
            # These exact rules were absent before our attempt; prior rules stay.
            for tool, rule in reversed(added):
                try:
                    result = run(command(tool, "-C", rule), check=False)
                    if result.returncode == 0:
                        run(command(tool, "-D", rule))
                    elif result.returncode != 1:
                        raise RuntimeError("Cannot reconcile exact rule")
                except Exception as cleanup_error:
                    print("ROLLBACK UNRESOLVED: " + shlex.join(command(tool, "-D", rule))
                          + " (" + type(cleanup_error).__name__ + ")", file=sys.stderr)
            # Keep the original failure even if any individual cleanup failed.
            raise


def main():
    mode = sys.argv[1] if len(sys.argv) == 2 else ""
    if mode in ("plan-apply", "plan-remove"):
        for tool, rule in rules():
            print(shlex.join(command(tool, "-I", ["1", *rule]) if mode == "plan-apply"
                             else command(tool, "-D", rule)))
        return
    if mode == "check-scope":
        check_scope()
        print("PASS: current Docker bridge names match the reserved selectors")
        return
    if mode not in ("apply", "remove"):
        raise SystemExit("usage: docker-route-pmtu.py plan-apply|plan-remove|check-scope|apply|remove")
    if os.geteuid() != 0:
        raise SystemExit("apply/remove require root and separate operator authorization")
    change(mode)


if __name__ == "__main__":
    main()
