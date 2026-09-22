#!/usr/bin/env python3
# Copyright (c) 2026 Luiz Otávio Miranda
"""Save tmux structure and activate restored windows on demand (no daemon)."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import pwd
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, Union

if TYPE_CHECKING:
  from collections.abc import Generator

  from typing_extensions import TypeGuard

REPO = Path(__file__).resolve().parents[2]


class HomeCwd(TypedDict):
  home: str


class AbsoluteCwd(TypedDict):
  absolute: str


Cwd = Union[HomeCwd, AbsoluteCwd]


class PaneRecord(TypedDict):
  cwd: Cwd
  title: str
  active: bool


class WindowRecord(TypedDict):
  uid: str
  index: int
  name: str
  active: bool
  zoom: bool
  layout: str
  panes: list[PaneRecord]


class SessionRecord(TypedDict):
  uid: str
  name: str
  windows: list[WindowRecord]


class FocusRecord(TypedDict):
  session: object
  window: object


SnapshotVersion = Union[bool, int, float]


class Snapshot(TypedDict):
  version: SnapshotVersion
  sessions: list[SessionRecord]
  focus: FocusRecord


def is_object_mapping(value: object) -> TypeGuard[dict[object, object]]:
  return isinstance(value, dict)


def is_object_list(value: object) -> TypeGuard[list[object]]:
  return isinstance(value, list)


def default_socket() -> Path:
  # tmux uses /tmp, not Python's platform-dependent temporary directory.
  base = os.environ.get("TMUX_TMPDIR", "/tmp")  # noqa: S108
  return (Path(base) / f"tmux-{os.getuid()}" / "default").resolve()


def socket_path(explicit: Path | None = None) -> Path:
  inherited = os.environ.get("TMUX", "").rsplit(",", 2)[0]
  return Path(explicit or inherited or default_socket()).resolve()


def state_directory(socket: Path) -> Path:
  if os.environ.get("TMUX_LAZY_STATE_DIR"):
    return Path(os.environ["TMUX_LAZY_STATE_DIR"]).expanduser()
  # A configured server owns its state path. Query the option rather than
  # exporting it into pane environments (which would leak into custom servers).
  binary = shutil.which("tmux")
  if binary and socket.exists():
    # Resolved tmux executable; socket and option are separate, shell-free arguments.
    owner = subprocess.run(  # noqa: S603
      [binary, "-S", str(socket), "show-option", "-gqv", "@lazy_state_dir"],
      text=True,
      capture_output=True,
      timeout=10,
      check=False,
    )
    value = owner.stdout.removesuffix("\n")
    if owner.returncode == 0 and value:
      return Path(value)
  base = (
    Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
    / "tmux/lazy"
  )
  # Agent/test/custom servers must not overwrite the default server's snapshot.
  if socket != default_socket():
    base /= "servers/" + hashlib.sha256(os.fsencode(socket)).hexdigest()[:16]
  return base


def literal_format(value: object) -> str:
  """Prevent literal paths from being interpreted as tmux format expressions."""
  return str(value).replace("#", "##")


def atomic_json(path: Path, value: object) -> None:
  temporary = path.with_suffix(".tmp")
  try:
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)
  finally:
    temporary.unlink(missing_ok=True)


def read_json_object(path: Path) -> dict[object, object]:
  value: object = json.loads(path.read_text())
  if not is_object_mapping(value):
    message = "Expected a JSON object"
    raise TypeError(message)
  return value


def validate_version(value: object) -> SnapshotVersion:
  if value != 1 or not isinstance(value, (bool, int, float)):
    message = "Unsupported or empty lazy snapshot"
    raise ValueError(message)
  return value


def validate_cwd(value: object) -> Cwd:
  if not is_object_mapping(value):
    message = "cwd must be explicitly home-relative or absolute"
    raise ValueError(message)
  cwd_values = value
  if set(cwd_values) not in ({"home"}, {"absolute"}):
    message = "cwd must be explicitly home-relative or absolute"
    raise ValueError(message)
  path = next(iter(cwd_values.values()))
  if not isinstance(path, str) or any(c in path for c in "\t\r\n\0"):
    message = "cwd containing control characters is not supported"
    raise ValueError(message)
  if "home" in cwd_values:
    if Path(path).is_absolute() or ".." in Path(path).parts:
      message = "Home-relative cwd must remain inside home"
      raise ValueError(message)
    return {"home": path}
  if not Path(path).is_absolute():
    message = "Absolute cwd must be absolute"
    raise ValueError(message)
  return {"absolute": path}


def validate_focus(value: object) -> FocusRecord:
  if not is_object_mapping(value):
    message = "Invalid saved focus"
    raise ValueError(message)
  fields = value
  if set(fields) != {"session", "window"}:
    message = "Invalid saved focus"
    raise ValueError(message)
  return {"session": fields["session"], "window": fields["window"]}


def validate_identity(
  values: dict[object, object], identities: set[str]
) -> tuple[str, str]:
  uid = values["uid"]
  name = values["name"]
  if not isinstance(uid, str) or not uid or uid in identities:
    message = "Snapshot identities must be nonempty and unique"
    raise ValueError(message)
  identities.add(uid)
  if not isinstance(name, str) or any(c in name for c in "\t\r\n\0"):
    message = "Names containing tabs/newlines are not supported"
    raise ValueError(message)
  return uid, name


def validate_pane(value: object) -> PaneRecord:
  if not is_object_mapping(value):
    message = "Invalid pane record"
    raise ValueError(message)
  active = value.get("active")
  if set(value) != {"cwd", "title", "active"} or not isinstance(active, bool):
    message = "Invalid pane record"
    raise ValueError(message)
  cwd = validate_cwd(value["cwd"])
  title = value["title"]
  if not isinstance(title, str) or any(c in title for c in "\t\r\n"):
    message = "Invalid pane title"
    raise ValueError(message)
  return {"cwd": cwd, "title": title, "active": active}


def validate_window(
  value: object, identities: set[str], indices: set[int]
) -> WindowRecord:
  if not is_object_mapping(value):
    message = "Invalid window record"
    raise ValueError(message)
  if set(value) != {"uid", "index", "name", "active", "zoom", "layout", "panes"}:
    message = "Invalid window record"
    raise ValueError(message)
  uid, name = validate_identity(value, identities)
  active = value["active"]
  zoom = value["zoom"]
  if not isinstance(active, bool) or not isinstance(zoom, bool):
    message = "Invalid window active/zoom flags"
    # Invalid serialized records consistently raise ValueError, including types.
    raise ValueError(message)  # noqa: TRY004
  index = value["index"]
  raw_panes = value["panes"]
  if not is_object_list(raw_panes) or (
    not isinstance(index, int) or index < 0 or index in indices or not raw_panes
  ):
    message = "Invalid window index or empty window"
    raise ValueError(message)
  indices.add(index)
  layout = value["layout"]
  if not isinstance(layout, str) or (
    layout and not re.fullmatch(r"[0-9a-f]+,[0-9x,{}\[\]]+", layout)
  ):
    message = "Invalid saved layout"
    raise ValueError(message)
  return {
    "uid": uid,
    "index": index,
    "name": name,
    "active": active,
    "zoom": zoom,
    "layout": layout,
    "panes": [validate_pane(pane) for pane in raw_panes],
  }


def validate_session(value: object, identities: set[str]) -> SessionRecord:
  if not is_object_mapping(value):
    message = "Invalid session record"
    raise ValueError(message)
  raw_windows = value.get("windows")
  if set(value) != {"uid", "name", "windows"} or not is_object_list(raw_windows):
    message = "Invalid session record"
    raise ValueError(message)
  uid, name = validate_identity(value, identities)
  if not raw_windows or not name or ":" in name or "." in name:
    message = "Invalid session name or empty session"
    raise ValueError(message)
  # Window indices are session-local; identities are snapshot-wide.
  indices: set[int] = set()
  return {
    "uid": uid,
    "name": name,
    "windows": [validate_window(window, identities, indices) for window in raw_windows],
  }


def validate_state(state: object) -> Snapshot:
  if not is_object_mapping(state):
    message = "Unsupported or empty lazy snapshot"
    raise ValueError(message)
  version = validate_version(state.get("version"))
  raw_sessions = state.get("sessions")
  if not raw_sessions:
    message = "Unsupported or empty lazy snapshot"
    raise ValueError(message)
  if set(state) != {"version", "sessions", "focus"} or not is_object_list(raw_sessions):
    message = "Unexpected snapshot fields"
    raise ValueError(message)
  focus = validate_focus(state["focus"])
  identities: set[str] = set()
  return {
    "version": version,
    "sessions": [validate_session(session, identities) for session in raw_sessions],
    "focus": focus,
  }


def parse_resurrect_records(
  text: str,
) -> tuple[
  dict[str, SessionRecord], dict[tuple[str, int], list[list[str]]], str | None
]:
  """Collect structure records without interpreting saved process commands."""
  pane_field_count = 11
  window_required_fields = 7
  sessions: dict[str, SessionRecord] = {}
  panes: dict[tuple[str, int], list[list[str]]] = {}
  selected: str | None = None
  for line in text.splitlines():
    fields = line.split("\t")
    if fields[0] == "grouped_session":
      message = "Grouped sessions are not supported"
      raise ValueError(message)
    if fields[0] == "pane":
      if len(fields) != pane_field_count:
        message = "Unsupported Resurrect pane record"
        raise ValueError(message)
      panes.setdefault((fields[1], int(fields[2])), []).append(fields)
    elif fields[0] == "window":
      if len(fields) < window_required_fields:
        message = "Unsupported Resurrect window record"
        raise ValueError(message)
      session = sessions.setdefault(
        fields[1], {"uid": str(uuid.uuid4()), "name": fields[1], "windows": []}
      )
      session["windows"].append(
        {
          "uid": str(uuid.uuid4()),
          "index": int(fields[2]),
          "name": fields[3].removeprefix(":"),
          "active": fields[4] == "1",
          "zoom": "Z" in fields[5],
          "layout": fields[6],
          "panes": [],
        }
      )
    elif fields[0] == "state" and len(fields) > 1:
      selected = fields[1]
  return sessions, panes, selected


class LazyTmux:
  def __init__(
    self,
    directory: str | Path,
    socket: str | Path,
    home: str | Path,
    shell: str,
    *,
    quiet: bool = False,
  ) -> None:
    self.root = Path(directory).expanduser().resolve()
    self.socket = Path(socket).resolve()
    self.home = Path(home).resolve()
    self.shell = shell
    self.quiet = quiet
    self.state_file = self.root / "state.json"
    self.env = dict(os.environ)
    for name in ("TMUX", "TMUX_PANE", "ENV", "BASH_ENV"):
      self.env.pop(name, None)
    self.env["HOME"] = str(self.home)
    binary = shutil.which("tmux")
    if not binary:
      message = "tmux is required in PATH (prefer Homebrew)"
      raise RuntimeError(message)
    self.binary = binary
    if not Path(shell).is_absolute() or not os.access(shell, os.X_OK):
      message = "Select an executable absolute shell path with --shell"
      raise ValueError(message)

  @contextmanager
  def locked(self) -> Generator[None, None, None]:
    self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (self.root / "state.lock").open("a") as handle:
      fcntl.flock(handle, fcntl.LOCK_EX)
      yield

  def tmux(self, *args: str, configuration: str | Path | None = None) -> str:
    command = [self.binary, "-S", str(self.socket)]
    if configuration is None:
      # A failed connection must not silently create a replacement server.
      command += ["-N", "-f", "/dev/null"]
    else:
      command += ["-f", str(configuration)]
    # Shell-free argv; callers quote the deliberate tmux run-shell/login commands.
    result = subprocess.run(  # noqa: S603
      [*command, *args],
      env=self.env,
      text=True,
      capture_output=True,
      timeout=30,
      check=False,
    )
    if result.returncode:
      message = f"tmux {args[0]}: {result.stderr.strip()}"
      raise RuntimeError(message)
    return result.stdout.removesuffix("\n")

  def alive(self) -> bool:
    if not self.socket.exists():
      return False
    try:
      owner = self.tmux("show-option", "-gqv", "@lazy_state_dir")
    except RuntimeError as exc:
      if "no server running" in str(exc) or "Connection refused" in str(exc):
        return False
      raise
    if owner and Path(owner).resolve() != self.root:
      message = "This server uses another lazy state directory; refusing to redirect it"
      raise RuntimeError(message)
    return True

  def notify(self, message: str, *, in_tmux: bool = False) -> None:
    if not self.quiet:
      if in_tmux:
        self.tmux("display-message", message)
      else:
        print(message)

  def encode_cwd(self, cwd: str) -> Cwd:
    path = Path(cwd)
    try:
      return {"home": str(path.relative_to(self.home))}
    except ValueError:
      return {"absolute": str(path)}

  def decode_cwd(self, cwd: Cwd) -> str:
    path = self.home / cwd["home"] if "home" in cwd else Path(cwd["absolute"])
    if not path.is_dir():
      message = f"Missing cwd; activation refused: {path}"
      raise RuntimeError(message)
    return str(path)

  def panes(self, window: str | None = None) -> list[list[str]]:
    target = ["-t", window] if window else ["-a"]
    fields = (
      "#{pane_id}",
      "#{pane_pid}",
      "#{pane_current_path}",
      "#{@lazy_cwd}",
      "#{pane_active}",
    )
    rows = [
      line.split("\t")
      for line in self.tmux("list-panes", *target, "-F", "\t".join(fields)).splitlines()
    ]
    if any(len(row) != len(fields) for row in rows):
      message = "Pane data contains unsupported tabs/newlines"
      raise ValueError(message)
    return rows

  def load(self) -> Snapshot:
    value: object = json.loads(self.state_file.read_text())
    return validate_state(value)

  def import_snapshot(self, snapshot: Path) -> None:
    if self.state_file.exists():
      message = "A lazy snapshot already exists; refusing to overwrite it"
      raise RuntimeError(message)
    sessions, panes, selected = parse_resurrect_records(Path(snapshot).read_text())
    for session in sessions.values():
      session["windows"].sort(key=lambda w: w["index"])
      for window in session["windows"]:
        for p in sorted(
          panes.get((session["name"], window["index"]), []),
          key=lambda p: int(p[5]),
        ):
          raw = p[7].removeprefix(":")
          cwd: Cwd
          if raw == "#{HOME}" or raw.startswith("#{HOME}/"):
            cwd = {"home": raw[len("#{HOME}") :].lstrip("/") or "."}
          elif raw == "~" or raw.startswith("~/"):
            cwd = {"home": raw[2:] or "."}
          else:
            cwd = self.encode_cwd(raw)
          window["panes"].append({"cwd": cwd, "title": p[6], "active": p[8] == "1"})
    if not sessions:
      message = "No sessions in the supplied snapshot"
      raise ValueError(message)
    chosen = (
      sessions[selected] if selected in sessions else next(iter(sessions.values()))
    )
    window = next((w for w in chosen["windows"] if w["active"]), chosen["windows"][0])
    state: Snapshot = {
      "version": 1,
      "sessions": list(sessions.values()),
      "focus": {"session": chosen["uid"], "window": window["uid"]},
    }
    atomic_json(self.state_file, validate_state(state))
    self.notify(
      "Imported Resurrect structure; no saved process commands will be executed."
    )

  def command(self, action: str) -> str:
    # Quiet is per invocation: a quiet configure must not silence prefix C-s.
    return literal_format(
      shlex.join(
        [
          sys.executable,
          str(Path(__file__).resolve()),
          "--state-dir",
          str(self.root),
          "--socket",
          str(self.socket),
          "--home",
          str(self.home),
          "--shell",
          self.shell,
          action,
        ]
      )
    )

  def configure(self) -> None:
    if not self.alive():
      message = "No running tmux server to configure"
      raise RuntimeError(message)
    self.tmux("set-option", "-g", "@lazy_state_dir", str(self.root))
    self.tmux("set-option", "-g", "default-shell", self.shell)
    generation = self.tmux("show-option", "-gqv", "@lazy_generation") or str(
      uuid.uuid4()
    )
    self.tmux("set-option", "-g", "@lazy_generation", generation)
    self.tmux("bind-key", "C-s", "run-shell", "-b", self.command("save"))
    self.tmux(
      "bind-key",
      "C-r",
      "display-message",
      "Lazy restore: save, stop the server when safe, then run tmux-lazy start",
    )
    for hook in (
      "session-window-changed",
      "client-session-changed",
      "client-attached",
    ):
      # Session IDs contain '$', so shell-single-quote the expanded IDs.
      command = (
        self.command("visit")
        + " '#{window_id}' '#{session_id}' "
        + shlex.quote(generation)
      )
      self.tmux(
        "set-hook", "-g", hook + "[200]", "run-shell -b " + shlex.quote(command)
      )

  def boot(self) -> None:
    if self.alive():
      # Reconfiguration/adoption never kills or restores into an existing server.
      self.configure()
      return
    version = re.search(r"(\d+)\.(\d+)", self.tmux("-V"))
    if not version or tuple(map(int, version.groups())) < (3, 5):
      message = "tmux >= 3.5 is required; prefer Homebrew tmux in PATH"
      raise RuntimeError(message)
    if not self.state_file.exists():
      resurrect = self.home / ".local/share/tmux/resurrect/last"
      if self.socket == default_socket() and resurrect.is_file():
        self.import_snapshot(resurrect)
    self.socket.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    state = self.load() if self.state_file.exists() else None
    started = False
    try:
      # tmux reads -f only for a newly created server. A native creator may
      # win between alive() and start-server; only our startup-only token
      # proves that the bootstrap settings were applied to a server we made.
      token = str(uuid.uuid4())
      with tempfile.NamedTemporaryFile(
        "w", prefix="startup-", suffix=".conf", dir=self.root
      ) as config:
        config.write(
          "set-option -s exit-empty off\n"
          f"set-option -g @lazy_boot_owner {token}\n"
          f"set-option -g @lazy_state_dir {shlex.quote(str(self.root))}\n"
          "set-option -g default-shell /bin/sh\n"
          "set-option -g remain-on-exit on\n"
          "set-option -g base-index 1\n"
          "set-option -g pane-base-index 1\n"
        )
        config.flush()
        self.tmux("start-server", configuration=config.name)
      if self.tmux("show-option", "-gqv", "@lazy_boot_owner") != token:
        message = (
          "Another tmux server started concurrently; "
          "left it unchanged. Attach or retry."
        )
        # The outer handler reports partial startup only after ownership is proven.
        raise RuntimeError(message)  # noqa: TRY301
      started = True
      self.tmux(
        "new-session",
        "-d",
        "-s",
        "__lazy_bootstrap",
        "-x",
        "120",
        "-y",
        "40",
        "",
      )
      self.tmux("set-option", "-s", "exit-empty", "on")
      if state:
        sid, wid = self.restore_structure(state)
      else:
        sid = self.tmux(
          "new-session",
          "-d",
          "-s",
          "HOME",
          "-c",
          literal_format(self.home),
          "-P",
          "-F",
          "#{session_id}",
          "exec " + shlex.quote(self.shell) + " -l",
        )
        wid = self.tmux("list-windows", "-t", sid, "-F", "#{window_id}")
      self.tmux("kill-session", "-t", "=__lazy_bootstrap")
      self.tmux("set-option", "-g", "remain-on-exit", "off")
      self.tmux("set-option", "-g", "default-shell", self.shell)
      self.tmux("source-file", str(REPO / "tmux/.tmux.conf"))
      self.configure()
      self.tmux("set-option", "-g", "@lazy_attach", sid)
      atomic_json(
        self.root / "focus.json",
        {"session": self.uid(sid), "window": self.uid(wid, window=True)},
      )
      # Config errors precede real user shell startup. Missing cwd leaves a
      # visible pending window for correction/retry, never a silent fallback.
      try:
        self.activate(wid)
      except RuntimeError as exc:
        print(f"tmux-lazy: {exc}", file=sys.stderr)
    except BaseException:
      if started:
        print(
          "tmux-lazy: restore incomplete; inspect the partial server "
          "before stopping it. "
          "The saved snapshot was not replaced.",
          file=sys.stderr,
        )
      raise

  def restore_structure(self, state: Snapshot) -> tuple[str, str]:
    targets: dict[tuple[object, object], tuple[str, str]] = {}
    focus_path = self.root / "focus.json"
    focus_values = (
      read_json_object(focus_path) if focus_path.exists() else state["focus"]
    )
    focus: FocusRecord = {
      "session": focus_values.get("session"),
      "window": focus_values.get("window"),
    }
    for session in state["sessions"]:
      if session["name"] == "__lazy_bootstrap":
        message = "Reserved bootstrap session name in snapshot"
        raise ValueError(message)
      dimensions = re.match(r"^[0-9a-f]+,(\d+)x(\d+),", session["windows"][0]["layout"])
      width, height = map(int, dimensions.groups()) if dimensions else (120, 40)
      sid = self.tmux(
        "new-session",
        "-d",
        "-s",
        session["name"],
        "-x",
        str(width),
        "-y",
        str(height),
        "-P",
        "-F",
        "#{session_id}",
        "",
      )
      self.tmux("set-option", "-t", sid, "@lazy_uid", session["uid"])
      for number, window in enumerate(session["windows"]):
        if number == 0:
          wid = self.tmux("list-windows", "-t", sid, "-F", "#{window_id}")
          if window["index"] != 1:
            self.tmux("move-window", "-s", wid, "-t", f"{sid}:{window['index']}")
        else:
          wid = self.tmux(
            "new-window",
            "-d",
            "-t",
            f"{sid}:{window['index']}",
            "-P",
            "-F",
            "#{window_id}",
            "",
          )
        match = re.match(r"^[0-9a-f]+,(\d+)x(\d+),", window["layout"])
        width, height = map(int, match.groups()) if match else (120, 40)
        self.tmux(
          "resize-window",
          "-t",
          wid,
          "-x",
          str(max(width, len(window["panes"]) * 4, 20)),
          "-y",
          str(max(height, 10)),
        )
        bootstrap = self.panes(wid)[0][0]
        # Only split-window '' is genuinely process-free. Replace the
        # short-lived /bin/sh bootstrap we created, never a user pane.
        self.tmux("split-window", "-d", "-h", "-t", wid, "")
        self.tmux("kill-pane", "-t", bootstrap)
        for _ in window["panes"][1:]:
          self.tmux("split-window", "-d", "-h", "-t", wid, "")
          self.tmux("select-layout", "-t", wid, "even-horizontal")
        self.tmux("select-layout", "-t", wid, window["layout"] or "even-horizontal")
        self.tmux("rename-window", "-t", wid, window["name"])
        self.tmux("set-option", "-w", "-t", wid, "@lazy_uid", window["uid"])
        self.tmux("set-option", "-w", "-t", wid, "@lazy_pending", "1")
        rows = self.panes(wid)
        for row, pane in zip(rows, window["panes"]):
          self.tmux(
            "set-option",
            "-p",
            "-t",
            row[0],
            "@lazy_cwd",
            json.dumps(pane["cwd"]),
          )
          self.tmux("select-pane", "-t", row[0], "-T", pane["title"])
        active = next(
          (r[0] for r, p in zip(rows, window["panes"]) if p["active"]),
          rows[0][0],
        )
        self.tmux("select-pane", "-t", active)
        if window["zoom"]:
          self.tmux("resize-pane", "-Z", "-t", active)
        self.tmux("set-option", "-w", "-u", "-t", wid, "window-size")
        targets[(session["uid"], window["uid"])] = (sid, wid)
      active_window = next(
        (w for w in session["windows"] if w["active"]), session["windows"][0]
      )
      self.tmux(
        "select-window",
        "-t",
        targets[(session["uid"], active_window["uid"])][1],
      )
    saved_focus = state["focus"]
    fallback = targets.get(
      (saved_focus["session"], saved_focus["window"]),
      next(iter(targets.values())),
    )
    sid, wid = targets.get((focus.get("session"), focus.get("window")), fallback)
    self.tmux("select-window", "-t", wid)
    return sid, wid

  def activate(self, window: str) -> None:
    rows = [p for p in self.panes(window) if p[3]]
    directories = [self.decode_cwd(validate_cwd(json.loads(p[3]))) for p in rows]
    for row, cwd in zip(rows, directories):
      if row[1] not in ("", "0"):
        message = "Marked pane already has a process; refusing to replace it"
        raise RuntimeError(message)
      # Process-free panes start with tmux's MODE_CRLF, which respawn preserves.
      # Reset the empty screen before starting a TUI-capable shell: LF must not
      # unexpectedly return to column zero. Never reset an already-running pane.
      self.tmux("send-keys", "-R", "-t", row[0])
      self.tmux(
        "respawn-pane",
        "-t",
        row[0],
        "-c",
        literal_format(cwd),
        "exec " + shlex.quote(self.shell) + " -l",
      )
      self.tmux("set-option", "-p", "-u", "-t", row[0], "@lazy_cwd")
    self.tmux("set-option", "-w", "-u", "-t", window, "@lazy_pending")
    # No success message here: display-message can freeze pane redraw.

  def uid(self, target: str, *, window: bool = False) -> str:
    args = ["-w"] if window else []
    uid = self.tmux("show-option", *args, "-qv", "-t", target, "@lazy_uid")
    if not uid:
      uid = str(uuid.uuid4())
      self.tmux("set-option", *args, "-t", target, "@lazy_uid", uid)
    return uid

  def visit(self, window: str, session: str, generation: str) -> None:
    if (
      not self.alive()
      or self.tmux("show-option", "-gqv", "@lazy_generation") != generation
    ):
      return
    try:
      if (
        window not in self.tmux("list-windows", "-a", "-F", "#{window_id}").splitlines()
      ):
        return
      if session not in self.tmux("list-sessions", "-F", "#{session_id}").splitlines():
        return
      if self.tmux("display-message", "-p", "-t", session, "#{window_id}") != window:
        return
      self.activate(window)
      atomic_json(
        self.root / "focus.json",
        {"session": self.uid(session), "window": self.uid(window, window=True)},
      )
      self.tmux("set-option", "-g", "@lazy_attach", session)
    finally:
      if self.alive():
        self.tmux("wait-for", "-S", "lazy-visit-complete")

  def save(self, *, if_running: bool = False) -> None:
    if not self.alive():
      if if_running:
        return
      message = "No running tmux server to save"
      raise RuntimeError(message)
    sessions: list[SessionRecord] = []
    for line in self.tmux(
      "list-sessions", "-F", "#{session_id}\t#{session_name}\t#{session_grouped}"
    ).splitlines():
      sid, name, grouped = line.split("\t")
      if grouped == "1":
        message = "Grouped sessions are unsupported; previous snapshot left intact"
        raise ValueError(message)
      session: SessionRecord = {
        "uid": self.uid(sid),
        "name": name,
        "windows": [],
      }
      fields = (
        "#{window_id}\t#{window_index}\t#{window_name}\t#{window_layout}"
        "\t#{window_active}\t#{window_zoomed_flag}\t#{window_linked}"
      )
      for window_line in self.tmux(
        "list-windows", "-t", sid, "-F", fields
      ).splitlines():
        wid, index, name, layout, active, zoom, linked = window_line.split("\t")
        if linked == "1":
          message = "Linked windows are unsupported; previous snapshot left intact"
          raise ValueError(message)
        panes: list[PaneRecord] = []
        for pane_row in self.panes(wid):
          cwd_value: object = json.loads(pane_row[3]) if pane_row[3] else None
          cwd = validate_cwd(cwd_value) if pane_row[3] else self.encode_cwd(pane_row[2])
          panes.append(
            {
              "cwd": cwd,
              "title": self.tmux(
                "display-message",
                "-p",
                "-t",
                pane_row[0],
                "#{pane_title}",
              ),
              "active": pane_row[4] == "1",
            }
          )
        session["windows"].append(
          {
            "uid": self.uid(wid, window=True),
            "index": int(index),
            "name": name,
            "layout": layout,
            "active": active == "1",
            "zoom": zoom == "1",
            "panes": panes,
          }
        )
      sessions.append(session)
    fallback: FocusRecord = {
      "session": sessions[0]["uid"],
      "window": sessions[0]["windows"][0]["uid"],
    }
    focus_path = self.root / "focus.json"
    focus = (
      validate_focus(read_json_object(focus_path)) if focus_path.exists() else fallback
    )
    atomic_json(
      self.state_file,
      validate_state({"version": 1, "sessions": sessions, "focus": focus}),
    )
    self.notify("Tmux structure saved", in_tmux=True)

  def export(self, destination: Path) -> None:
    state = self.load()
    # Only state.json crosses machines. Locks, focus and socket-specific data
    # stay local; home-relative cwd is already portable without substitutions.
    destination = Path(destination)
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    atomic_json(destination / "state.json", state)
    self.notify("Portable tmux snapshot exported")

  def status(self) -> dict[str, object]:
    if not self.alive():
      return {"running": False}
    panes = self.panes()
    return {
      "running": True,
      "sessions": len(self.tmux("list-sessions", "-F", "#{session_id}").splitlines()),
      "windows": len(
        self.tmux("list-windows", "-a", "-F", "#{window_id}").splitlines()
      ),
      "panes": len(panes),
      "pending_panes": sum(bool(p[3]) for p in panes),
      "process_free_panes": sum(p[1] in ("", "0") for p in panes),
    }


def argument_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
    "--socket",
    type=Path,
    help="Explicit socket; otherwise TMUX or the default socket",
  )
  parser.add_argument(
    "--state-dir",
    type=Path,
    help="Local JSON/lock directory (or TMUX_LAZY_STATE_DIR)",
  )
  parser.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
  parser.add_argument(
    "--shell", help="Login shell for new panes (otherwise the server/login shell)"
  )
  quiet_help = "Suppress confirmations; preserve errors, warnings and status JSON"
  parser.add_argument("--quiet", action="store_true", help=quiet_help)
  quiet_options = argparse.ArgumentParser(add_help=False)
  quiet_options.add_argument(
    "--quiet", action="store_true", default=argparse.SUPPRESS, help=quiet_help
  )
  sub = parser.add_subparsers(dest="action", required=True)
  sub.add_parser("import", parents=[quiet_options]).add_argument(
    "--snapshot", type=Path, required=True
  )
  for action in ("boot", "start", "configure", "status"):
    sub.add_parser(action, parents=[quiet_options])
  sub.add_parser("save", parents=[quiet_options]).add_argument(
    "--if-running", action="store_true"
  )
  sub.add_parser("export", parents=[quiet_options]).add_argument(
    "destination", type=Path
  )
  visit = sub.add_parser("visit", parents=[quiet_options])
  visit.add_argument("window")
  visit.add_argument("session")
  visit.add_argument("generation")
  sub.add_parser("stop", parents=[quiet_options]).add_argument(
    "--yes", action="store_true", required=True
  )
  return parser


def attach(app: LazyTmux) -> None:
  """Replace the launcher with an interactive client after releasing the state lock."""
  target = app.tmux("show-option", "-gqv", "@lazy_attach")
  command = [app.binary, "-S", str(app.socket)]
  if os.environ.get("TERM_PROGRAM") == "OMXTerm":
    command += ["-T", "sync"]
  command += ["attach-session"]
  sessions = app.tmux("list-sessions", "-F", "#{session_id}").splitlines()
  if target in sessions:
    command += ["-t", target]
  # Replace the launcher with the resolved tmux binary and explicit argv, no shell.
  os.execvpe(app.binary, command, app.env)  # noqa: S606


# Keep command dispatch explicit under one lock; attach must happen outside it.
def main() -> None:  # noqa: C901
  args = argument_parser().parse_args()
  os.umask(0o077)
  socket = socket_path(args.socket)
  shell = args.shell or os.environ.get("SHELL") or pwd.getpwuid(os.getuid()).pw_shell
  app = LazyTmux(
    args.state_dir or state_directory(socket),
    socket,
    args.home,
    shell,
    quiet=args.quiet,
  )
  if args.action == "start" and (os.environ.get("TMUX") or not os.isatty(0)):
    message = "Run start from a normal terminal outside tmux"
    raise RuntimeError(message)
  with app.locked():
    # Another launcher may be constructing the server with /bin/sh. Resolve
    # implicit shell selection only after its startup lock has been released.
    if not args.shell and app.alive():
      app.shell = app.tmux("show-option", "-gqv", "default-shell") or shell
    if args.action == "import":
      app.import_snapshot(args.snapshot)
    elif args.action in ("boot", "start"):
      app.boot()
    elif args.action == "configure":
      app.configure()
    elif args.action == "visit":
      app.visit(args.window, args.session, args.generation)
    elif args.action == "save":
      app.save(if_running=args.if_running)
    elif args.action == "export":
      app.export(args.destination)
    elif args.action == "status":
      print(json.dumps(app.status()))
    elif args.action == "stop" and app.alive():
      app.tmux("kill-server")
      app.notify("Tmux server stopped; only explicitly saved structure will return")
  if args.action == "start":
    attach(app)


if __name__ == "__main__":
  try:
    main()
  except (
    RuntimeError,
    OSError,
    ValueError,
    KeyError,
    TypeError,
    subprocess.TimeoutExpired,
  ) as exc:
    print(f"tmux-lazy: {exc}", file=sys.stderr)
    binary = shutil.which("tmux")
    if os.environ.get("TMUX") and binary:
      # -l makes the error literal; no shell interprets it.
      subprocess.run(  # noqa: S603
        [binary, "display-message", "-l", f"tmux-lazy: {exc}"],
        check=False,
      )
    sys.exit(1)
