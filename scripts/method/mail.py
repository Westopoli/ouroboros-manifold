#!/usr/bin/env python3
"""mail.py: mailboxes for the named chats of docs/method/agents.toml (docs/method/communication.md, docs/stories/H-077.md).

  register <name>                  make mail/<name>/ from the registry table
  send --me <from> --to <agent>|rules --class block|ask|info|westley [--re <id>] [--attach <path>]... "<text>"
  read --me <agent>                print the unread digest, move the lines to delivered.jsonl; never blocks
  wait --me <agent> [--max <s>]    block until mail/<agent>/flag exists, remove it, then read (the only wait a chat arms)
  list                             the registry with unread counts
Exit 0 ok, 1 refused (`MAIL REFUSED <why>`), 2 usage. Mail root $OM_PUSH_DIR/mail (default ~/Projects/om-push/mail);
registry $OM_AGENTS_TOML (default docs/method/agents.toml). Stdlib only; no model is called. See also: station.py.
"""
import argparse
import datetime
import fcntl
import json
import os
import re
import secrets
import sys
import time
import tomllib

MAX = 1500  # DRAFT-mail-max
BLACKBOARD = [r"\b(landed|pushed|merged) (at|on|to)?\s*[0-9a-f]{7,}", r"\bslots? (freed|free|held)\b",
              r"\bin flight\b", r"\bsweep (pass|green|red)\b", r"\bstatus:"]
CLASSES = ("block", "ask", "info", "westley")
CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def registry_path():
    return os.environ.get("OM_AGENTS_TOML") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), "docs", "method", "agents.toml")


def registry():
    with open(registry_path(), "rb") as f:
        return tomllib.load(f)


def mail_root():
    push = os.environ.get("OM_PUSH_DIR") or os.path.expanduser("~/Projects/om-push")
    return os.path.join(push, "mail")


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ulid():
    n = (int(time.time() * 1000) << 80) | secrets.randbits(80)
    return "".join(CROCKFORD[(n >> (5 * i)) & 31] for i in reversed(range(26)))


def read_lines(path):
    out = []
    try:
        with open(path) as f:
            for ln in f:
                try:
                    out.append(json.loads(ln))
                except ValueError:
                    pass
    except OSError:
        pass
    return out


def locked(agent):
    d = os.path.join(mail_root(), agent)
    os.makedirs(d, exist_ok=True)
    f = open(os.path.join(d, ".lock"), "a")
    fcntl.flock(f, fcntl.LOCK_EX)
    return f, d


def refuse(why):
    print(f"MAIL REFUSED {why}")
    return 1


def cmd_register(a):
    if a.name not in registry():
        return refuse(f"unknown agent {a.name}")
    os.makedirs(os.path.join(mail_root(), a.name), exist_ok=True)
    open(os.path.join(mail_root(), a.name, "inbox.jsonl"), "a").close()
    print(f"MAIL OK registered {a.name}")
    return 0


def cmd_send(a):
    reg = registry()
    targets = [n for n, t in reg.items() if t.get("rules")] if a.to == "rules" else [a.to]
    if a.to != "rules" and a.to not in reg:
        return refuse(f"unknown agent {a.to}")
    if not targets:
        return refuse("unknown agent rules")
    for n in targets:
        senders = reg[n].get("senders", ["*"])
        if "*" not in senders and a.me not in senders:
            return refuse(f"sender {a.me} not allowed by {n}.senders")
        if a.cls == "ask" and not reg[n].get("rules"):
            return refuse("class ask needs rules = true")
    for p in BLACKBOARD:
        if re.search(p, a.text):
            return refuse(f"blackboard: {p}")
    if len(a.text) > MAX:
        return refuse(f"text over {MAX} chars, put it in a file and --attach it")
    for n in targets:
        m = {"id": ulid(), "ts": now(), "from": a.me, "to": n, "class": a.cls, "re": a.re, "text": a.text,
             "attach": a.attach, "read": None}
        f, d = locked(n)
        with f, open(os.path.join(d, "inbox.jsonl"), "a") as inbox:
            inbox.write(json.dumps(m) + "\n")
        print(f"MAIL OK {m['id']} -> {n} {a.cls}")
    return 0


def cmd_read(a):
    f, d = locked(a.me)
    with f:
        inbox = os.path.join(d, "inbox.jsonl")
        got = read_lines(inbox)
        if got:
            ts = now()
            with open(os.path.join(d, "delivered.jsonl"), "a") as out:
                for m in got:
                    out.write(json.dumps({**m, "read": ts}) + "\n")
            open(inbox, "w").close()
    if not got:
        print("MAIL none")
    for m in got:
        att = f" [attach: {' '.join(m['attach'])}]" if m.get("attach") else ""
        print(f"MAIL {m['class']} {m['from']} {m['re']} {m['ts']}: {m['text'][:200]}{att}")
    return 0


def cmd_wait(a):
    flag = os.path.join(mail_root(), a.me, "flag")
    start = time.monotonic()
    while not os.path.exists(flag):
        if a.max is not None and time.monotonic() - start >= a.max:
            print(f"MAIL idle {a.max}s")
            return 0
        time.sleep(0.25)  # a poll; inotify is not in the stdlib
    try:
        os.remove(flag)
    except OSError:
        pass
    return cmd_read(a)


def cmd_list(a):
    for n, t in registry().items():
        wake = ",".join(t.get("wake", ["block", "ask", "westley"]))
        unread = len(read_lines(os.path.join(mail_root(), n, "inbox.jsonl")))
        print(f"{n} {t.get('role', '-')} {str(bool(t.get('rules'))).lower()} {wake} {unread}")
    return 0


def main():
    ap = argparse.ArgumentParser(prog="mail.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("register")
    p.add_argument("name")
    p = sub.add_parser("send")
    p.add_argument("--me", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--class", dest="cls", required=True, choices=CLASSES)
    p.add_argument("--re", default="-")
    p.add_argument("--attach", action="append", default=[])
    p.add_argument("text")
    p = sub.add_parser("read")
    p.add_argument("--me", required=True)
    p = sub.add_parser("wait")
    p.add_argument("--me", required=True)
    p.add_argument("--max", type=int)
    sub.add_parser("list")
    a = ap.parse_args()
    sys.exit({"register": cmd_register, "send": cmd_send, "read": cmd_read, "wait": cmd_wait, "list": cmd_list}[a.cmd](a))


if __name__ == "__main__":
    main()
