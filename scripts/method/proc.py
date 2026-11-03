#!/usr/bin/env python3
"""proc.py: the process register and reaper (H-081, DEC-proc-reaper-2026-11-03). Stdlib only, no model call.

  start --owner O [--session S] [--story ID] --purpose TEXT [--ttl SECONDS] [--detach] -- CMD...
  list
  reap [--dry-run] [--pid N]

Records live in $OM_PUSH_DIR/procs/<pid>.json (default ~/Projects/om-push/procs). `reap` kills only a recorded process
whose /proc start time equals the record's and for which one of these holds: the owner has ended, the story has a
`Land <story>` commit on HEAD after the record's start, or the TTL has passed. An unrecorded pid is never killed.
`reap` finds the repo for the Land check as the cwd of the call. Chat-owner sockets are read from $OM_SOCK_DIR
(default /run/user/1000/cc-socks). `--owner none` means TTL only. A process that holds for several reasons gets
one KEEP line per reason; a recorded pid that no longer exists prints `PROC GONE` and its record is archived.
# See also: docs/stories/H-081.md, .claude/hooks/kill-guard.sh (denies raw kill; reap is the way)
"""
import argparse
import glob
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TTL_DEFAULT = 14400  # DRAFT-proc-ttl


def push_dir():
    return Path(os.environ.get("OM_PUSH_DIR") or Path.home() / "Projects" / "om-push")


def procs_dir():
    return push_dir() / "procs"


def sock_dir():
    return Path(os.environ.get("OM_SOCK_DIR") or "/run/user/1000/cc-socks")


def now():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def parse_iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def stat_fields(pid):
    """(state, start ticks) from /proc/<pid>/stat, or None when the pid is gone."""
    try:
        with open(f"/proc/{pid}/stat") as f:
            rest = f.read().rsplit(")", 1)[1].split()
    except OSError:
        return None
    return rest[0], rest[19]


def alive(pid):
    s = stat_fields(pid)
    return s is not None and s[0] != "Z"


def cmd_start(a):
    cmd = a.command[1:] if a.command and a.command[0] == "--" else a.command
    if not cmd:
        print("PROC ERROR no command", file=sys.stderr)
        return 2
    kw = dict(start_new_session=True)
    if a.detach:
        kw.update(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p = subprocess.Popen(cmd, **kw)
    s = stat_fields(p.pid)
    rec = {"pid": p.pid, "pgid": os.getpgid(p.pid) if s else p.pid, "start": s[1] if s else "",
           "ts": iso(now()), "owner": a.owner, "session": a.session, "story": a.story,
           "purpose": a.purpose, "cmd": cmd, "ttl_s": a.ttl}
    procs_dir().mkdir(parents=True, exist_ok=True)
    (procs_dir() / f"{p.pid}.json").write_text(json.dumps(rec) + "\n")
    print(f"PROC OK {p.pid} {a.purpose}", flush=True)
    return 0 if a.detach else p.wait()


def records():
    out = []
    for f in sorted(glob.glob(str(procs_dir() / "*.json"))):
        try:
            out.append(json.loads(Path(f).read_text()))
        except (OSError, ValueError):
            continue
    return out


def cmd_list(_a):
    for r in records():
        age = int((now() - parse_iso(r["ts"])).total_seconds())
        print(f"PROC {r['pid']} {'alive' if alive(r['pid']) else 'gone'} {r['owner']} {r['story']} {age}s {r['purpose']}")
    return 0


def agent_ended(owner, since):
    """True/False from a sub-agent transcript, None when this owner has no transcript."""
    pat = str(Path.home() / ".claude" / "projects" / "*" / "**" / "subagents" / f"{owner}.jsonl")
    files = glob.glob(pat, recursive=True)
    if not files:
        return None
    for f in files:
        last_end = None
        user_after = False
        for line in Path(f).read_text().splitlines():
            try:
                d = json.loads(line)
                ts = parse_iso(d["timestamp"])
            except (ValueError, KeyError):
                continue
            msg = d.get("message") or {}
            if d.get("type") == "assistant" and msg.get("stop_reason") == "end_turn" and ts > since:
                last_end, user_after = ts, False
            elif d.get("type") == "user" and last_end is not None and ts > last_end:
                user_after = True
        if last_end is not None and not user_after:
            return True
    return False


def chat_alive(session):
    """A chat is alive while a socket in the socket dir belongs to a live pid whose command line names the session."""
    for s in glob.glob(str(sock_dir() / "*.sock")):
        pid = Path(s).stem
        if not pid.isdigit() or not alive(int(pid)):
            continue
        try:
            cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace")
        except OSError:
            continue
        if session in cmdline:
            return True
    return False


def owner_ended(r, since):
    if r["owner"] == "none":
        return "owner none"
    ended = agent_ended(r["owner"], since)
    if ended is True:
        return "owner ended"
    if ended is None and r.get("session"):
        return None if chat_alive(r["session"]) else "owner ended (chat socket gone)"
    return None


def landed(story, since):
    if not story or story == "-":
        return None
    r = subprocess.run(["git", "log", "-E", f"--grep=^Land {story}( |$)", "--format=%H %ct", "HEAD"],
                       capture_output=True, text=True)
    for line in r.stdout.splitlines():
        sha, ct = line.split()
        if datetime.fromtimestamp(int(ct), timezone.utc) > since:
            return sha[:8]
    return None


def kill_group(pgid, pid):
    try:
        os.killpg(pgid, signal.SIGTERM)
    except OSError:
        return
    end = time.time() + 10
    while alive(pid) and time.time() < end:
        time.sleep(0.1)
    if alive(pid):
        try:
            os.killpg(pgid, signal.SIGKILL)
        except OSError:
            pass


def archive(r, evidence, dry):
    if dry:
        return
    d = procs_dir() / "reaped"
    d.mkdir(parents=True, exist_ok=True)
    os.replace(procs_dir() / f"{r['pid']}.json", d / f"{r['pid']}.json")
    with open(procs_dir() / "reaped.log", "a") as f:
        f.write(f"{iso(now())} {r['pid']} {r['owner']} {r['story']} {evidence} {Path(r['cmd'][0]).name}\n")


def cmd_reap(a):
    recs = records()
    if a.pid is not None:
        if not any(r["pid"] == a.pid for r in recs):
            print(f"PROC KEEP {a.pid} no record")
            return 0
        recs = [r for r in recs if r["pid"] == a.pid]
    for r in recs:
        pid = r["pid"]
        s = stat_fields(pid)
        if s is None or s[0] == "Z":
            print(f"PROC GONE {pid}")
            archive(r, "gone", a.dry_run)
            continue
        if s[1] != str(r["start"]):
            print(f"PROC KEEP {pid} start mismatch")
            continue
        since = parse_iso(r["ts"])
        left = r["ttl_s"] - (now() - since).total_seconds()
        evidence = owner_ended(r, since)
        if evidence is None:
            sha = landed(r["story"], since)
            evidence = f"story landed {sha}" if sha else None
        if evidence is None and left <= 0:
            evidence = "ttl passed"
        if evidence is None:
            print(f"PROC KEEP {pid} alive owner")
            print(f"PROC KEEP {pid} ttl {int(left)}s left")
            continue
        print(f"PROC KILL {pid} {evidence}")
        if not a.dry_run:
            kill_group(r["pgid"], pid)
        archive(r, evidence, a.dry_run)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="verb", required=True)
    st = sub.add_parser("start")
    st.add_argument("--owner", required=True)
    st.add_argument("--session", default="")
    st.add_argument("--story", default="-")
    st.add_argument("--purpose", required=True)
    st.add_argument("--ttl", type=int, default=TTL_DEFAULT)
    st.add_argument("--detach", action="store_true")
    st.add_argument("command", nargs=argparse.REMAINDER)
    st.set_defaults(fn=cmd_start)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    rp = sub.add_parser("reap")
    rp.add_argument("--dry-run", action="store_true")
    rp.add_argument("--pid", type=int)
    rp.set_defaults(fn=cmd_reap)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
