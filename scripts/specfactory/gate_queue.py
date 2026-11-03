#!/usr/bin/env python3
"""gate_queue.py: the gate's queue owner (H-080, DEC-gate-queue-2026-11-03). Stdlib only; no model is called.

  submit --channel c --id I --branch B --sha S --worktree W --requester R [--tier T]   write a ticket
  wait   --channel c --id I [--max s]    block on <id>.result; exit 0 OK, 1 REJECT, 3 on --max
  status                                 one line per channel
  [--once] [--channel c]                 the worker: drains the queue in ts order (--once exits when empty)

Files live under $OM_PUSH_DIR (default ~/Projects/om-push): queue/<channel>/<id>.json (ticket), <id>.result, PAUSED
(`red-sweep <sha>`), RUNNING (the id being gated). A worker holds gate-<channel>.lock while it runs. Siblings
(pre_gate.sh, merge_gate.sh, wt.py) are found beside this script's own path, mail.py in ../method.
While ticket j gates, the next ticket k is prepared on a q-<channel>-<n> tree holding j's sha; if j rejects, k is
re-prepared without it. A REJECT last row of sweeps.md pauses the queue (poll, stdlib has no inotify) unless the
ticket's story carries `Fixes-sweep: <that sha>`. See also: merge_gate.sh (sweep read at the same row), mail.py,
docs/stories/H-080.md.
"""
import argparse
import datetime
import fcntl
import json
import os
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MAIL = os.path.join(HERE, "..", "method", "mail.py")
CHANNELS = ("lab", "beta")
PAUSE_POLL_S = 5
IDLE_POLL_S = 2
GIT = ["git", "-c", "user.name=gate-queue", "-c", "user.email=gate-queue@localhost"]


def push_dir():
    return os.environ.get("OM_PUSH_DIR") or os.path.expanduser("~/Projects/om-push")


def qdir(ch):
    return os.path.join(push_dir(), "queue", ch)


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def parse_ts(s):
    try:
        return datetime.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc)
    except (ValueError, TypeError):
        return now()


def write_atomic(path, text):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-")
    with os.fdopen(fd, "w") as f:
        f.write(text)
    os.rename(tmp, path)


def tickets(ch):
    """Unresolved tickets (a .json with no .result), by ts then id."""
    d, out = qdir(ch), []
    if not os.path.isdir(d):
        return out
    for n in os.listdir(d):
        if n.endswith(".json") and not n.startswith(".") and not os.path.exists(os.path.join(d, n[:-5] + ".result")):
            try:
                with open(os.path.join(d, n)) as f:
                    t = json.load(f)
            except (OSError, ValueError):
                continue
            t.setdefault("id", n[:-5])
            out.append(t)
    return sorted(out, key=lambda t: (t.get("ts", ""), t["id"]))


def read_one(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ""


def cmd_submit(a):
    os.makedirs(qdir(a.channel), exist_ok=True)
    t = {"id": a.id, "branch": a.branch, "sha": a.sha, "worktree": a.worktree, "requester": a.requester,
         "tier": a.tier, "ts": now().strftime("%Y-%m-%dT%H:%M:%SZ")}
    write_atomic(os.path.join(qdir(a.channel), a.id + ".json"), json.dumps(t))
    pos = [x["id"] for x in tickets(a.channel)].index(a.id) + 1
    print(f"QUEUE {a.channel} {a.id} position {pos}")
    return 0


def cmd_wait(a):
    path = os.path.join(qdir(a.channel), a.id + ".result")
    end = time.time() + a.max if a.max is not None else None
    while not os.path.exists(path):
        if end is not None and time.time() >= end:
            return 3
        time.sleep(0.5)
    text = read_one(path)
    print(text)
    return 0 if f"QUEUE verdict OK {a.id} " in text + " " else 1


def cmd_status(a):
    for ch in CHANNELS:
        running = read_one(os.path.join(qdir(ch), "RUNNING")) or "idle"
        waiting = len([t for t in tickets(ch) if t["id"] != running])
        paused = read_one(os.path.join(qdir(ch), "PAUSED"))
        print(f"QUEUE {ch} {running} waiting {waiting}" + (f" PAUSED {paused}" if paused else ""))
    return 0


def sweep_row():
    try:
        with open(os.path.join(ROOT, "docs", "northstar", "plans", "push", "sweeps.md")) as f:
            rows = [ln for ln in f if ln.startswith("|")]
    except OSError:
        return "", ""
    cells = [c.strip() for c in rows[-1].split("|")] if rows else []
    return (cells[3], cells[2]) if len(cells) > 3 else ("", "")


def story_fixes(t):
    p = os.path.join(t.get("worktree", ""), "docs", "stories", t["id"].split(",")[0] + ".md")
    fixes = ""
    for ln in read_one(p).splitlines():
        if ln.startswith("Fixes-sweep:"):
            fixes = ln.split(":", 1)[1].strip()
    return fixes


def wait_unpaused(ch, t):
    """Blocks while the last sweeps row is REJECT and the ticket's story does not fix it."""
    pf = os.path.join(qdir(ch), "PAUSED")
    while True:
        verdict, sha = sweep_row()
        if verdict != "REJECT" or story_fixes(t) == sha:
            if os.path.exists(pf):
                os.unlink(pf)
            return
        write_atomic(pf, f"red-sweep {sha}")
        time.sleep(PAUSE_POLL_S)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


class Prep:
    """A lookahead tree: wt.py new q-<ch>-<n>, main plus the ticket's sha plus the earlier candidate's sha."""

    def __init__(self, ch, t, n, earlier=None):
        self.path, self.ok, self.name = "", False, f"q-{ch}-{n}"
        self.thread = threading.Thread(target=self.build, args=(ch, t, earlier))
        self.thread.start()

    def build(self, ch, t, earlier):
        r = run([sys.executable, os.path.join(HERE, "wt.py"), "new", self.name, "--channel", ch, "--owner", "gate-queue",
                 "--purpose", f"lookahead {t['id']}", "--base", t["sha"]])
        words = r.stdout.split()
        if r.returncode or len(words) < 3 or words[0] != "WT" or words[1] != "OK":
            return
        self.path = words[2]
        steps = [["fetch", "-q", "origin"], ["merge", "--no-edit", "-q", t["sha"]]]
        if earlier:
            steps.append(["merge", "--no-edit", "-q", earlier["sha"]])
        steps.append(["merge", "--no-edit", "-q", "origin/main"])
        self.ok = all(run(GIT + ["-C", self.path] + s).returncode == 0 for s in steps)

    def finish(self):
        self.thread.join()
        if self.path:
            sha = run(["git", "-C", self.path, "rev-parse", "HEAD"]).stdout.strip()
            run([sys.executable, os.path.join(HERE, "wt.py"), "done", self.path, sha])


def gate(ch, t, tree, wait_s):
    """Merge main into the tree, pre_gate, merge_gate. Returns (lines, ok)."""
    lines = []
    run(["git", "-C", tree, "fetch", "-q", "origin"])
    m = run(GIT + ["-C", tree, "merge", "--no-edit", "-q", "origin/main"])
    if m.returncode:
        run(["git", "-C", tree, "merge", "--abort"])
        return ["GATE merge REJECT conflict"], False
    env = {**os.environ, "MERGE_GATE_QUEUE_S": str(wait_s)}
    id_ = t["id"]
    p = run([os.path.join(HERE, "pre_gate.sh"), tree, "origin/main", id_], env=env)
    lines += p.stdout.splitlines()
    if p.returncode:
        return lines, False
    tier = ["--tier", t["tier"]] if t.get("tier") else []
    g = run([os.path.join(HERE, "merge_gate.sh"), *tier, tree, "origin/main", id_], env=env)
    lines += g.stdout.splitlines()
    err = os.path.join(qdir(ch), id_ + ".err")
    if g.stderr:
        write_atomic(err, g.stderr)
    return lines, g.returncode == 0


def send_mail(t, ok, wait_s, stage_s, result):
    verdict = "OK" if ok else "REJECT"
    r = run([sys.executable, MAIL, "send", "--me", "gate-queue", "--to", t.get("requester", ""), "--class", "info",
             "--re", t["id"], f"gate {t['id']} {verdict} {wait_s}s/{stage_s}s, result {result}"])
    if r.returncode:
        print(f"gate_queue: mail to {t.get('requester')} failed: {r.stdout}{r.stderr}", file=sys.stderr)


def free_n(ch, used):
    n = 1
    while n in used or os.path.exists(os.path.join(push_dir(), "wt", f"q-{ch}-{n}")):
        n += 1
    return n


def drain(ch):
    """Gates every pending ticket in order; returns when none is left."""
    d, used, prep = qdir(ch), set(), None  # prep: (ticket id, Prep) for the next ticket

    def start_prep(k, earlier):
        n = free_n(ch, used)
        used.add(n)
        return (k["id"], Prep(ch, k, n, earlier))

    while True:
        pending = tickets(ch)
        if not pending:
            return
        t, rest = pending[0], pending[1:]
        wait_unpaused(ch, t)
        began = time.time()
        wait_s = max(0, int((now() - parse_ts(t.get("ts"))).total_seconds()))
        mine = None
        if prep and prep[0] == t["id"] and prep[1].ok:
            mine = prep[1]
        elif prep:
            prep[1].finish()
        prep = None
        nxt = start_prep(rest[0], t) if rest else None
        write_atomic(os.path.join(d, "RUNNING"), t["id"])
        try:
            lines, ok = gate(ch, t, mine.path if mine else t.get("worktree", ""), wait_s)
        finally:
            os.unlink(os.path.join(d, "RUNNING"))
        if mine:
            mine.finish()
        stage_s = int(time.time() - began)
        res = os.path.join(d, t["id"] + ".result")
        write_atomic(res, "\n".join(lines) + f"\nQUEUE verdict {'OK' if ok else 'REJECT'} {t['id']} queue {wait_s}s stage {stage_s}s\n")
        send_mail(t, ok, wait_s, stage_s, res)
        if nxt:
            nxt[1].thread.join()
            if ok and nxt[1].ok:
                prep = nxt
            else:  # j rejected: k is re-prepared without j before its gate
                nxt[1].finish()
                prep = start_prep(rest[0], None) if not ok else None
                if prep:
                    prep[1].thread.join()


def worker(ch, once):
    os.makedirs(qdir(ch), exist_ok=True)
    with open(os.path.join(push_dir(), f"gate-{ch}.lock"), "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        rp = os.path.join(qdir(ch), "RUNNING")
        if os.path.exists(rp):
            os.unlink(rp)
        while True:
            drain(ch)
            if once:
                return
            time.sleep(IDLE_POLL_S)


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--once", action="store_true")
    p.add_argument("--channel", choices=CHANNELS)
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("submit")
    s.add_argument("--channel", required=True, choices=CHANNELS)
    for k in ("id", "branch", "sha", "worktree", "requester"):
        s.add_argument("--" + k, required=True)
    s.add_argument("--tier", default="")
    w = sub.add_parser("wait")
    w.add_argument("--channel", required=True, choices=CHANNELS)
    w.add_argument("--id", required=True)
    w.add_argument("--max", type=float)
    sub.add_parser("status")
    a = p.parse_args()
    if a.cmd:
        return {"submit": cmd_submit, "wait": cmd_wait, "status": cmd_status}[a.cmd](a)
    os.makedirs(push_dir(), exist_ok=True)
    ths = [threading.Thread(target=worker, args=(c, a.once)) for c in ([a.channel] if a.channel else CHANNELS)]
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    return 0


if __name__ == "__main__":
    sys.exit(main())
