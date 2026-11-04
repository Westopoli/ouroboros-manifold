#!/usr/bin/env python3
"""station.py: raises the flag of every agent whose unread mail needs a wake (docs/method/communication.md rule 4).

Every 2 s it re-reads the registry (docs/method/agents.toml, or $OM_AGENTS_TOML) and, for each agent with unread mail
and no flag yet, touches mail/<agent>/flag when an unread has a class in the agent's `wake` (default block, ask,
westley), or the oldest unread is older than `linger_min` (DRAFT-mail-linger 20), or the unread count is at least
`batch` (DRAFT-mail-batch 5). Each raise is one line of mail/station.log. It never reads text and never moves mail.
Once a minute it also runs `proc.py reap` (H-081; not under `--once`). `--once` runs one loop and exits. No model is called. See also: mail.py, docs/stories/H-077.md.
"""
import argparse
import datetime
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import mail  # noqa: E402

LINGER, BATCH = 20, 5  # DRAFT-mail-linger (min), DRAFT-mail-batch
WAKE = ["block", "ask", "westley"]


def age_min(ts):
    t = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    return (datetime.datetime.now(datetime.timezone.utc) - t).total_seconds() / 60


def reason(table, unread):
    wake = table.get("wake", WAKE)
    for m in unread:
        if m.get("class") in wake:
            return f"class={m['class']}"
    linger = table.get("linger_min", LINGER)
    oldest = max((age_min(m["ts"]) for m in unread if m.get("ts")), default=0)
    if oldest > linger:
        return f"linger={int(oldest)}"
    if len(unread) >= table.get("batch", BATCH):
        return f"batch={len(unread)}"
    return None


def loop():
    root = mail.mail_root()
    for name, table in mail.registry().items():
        d = os.path.join(root, name)
        unread = mail.read_lines(os.path.join(d, "inbox.jsonl"))
        if not unread or os.path.exists(os.path.join(d, "flag")):
            continue
        why = reason(table, unread)
        if why:
            open(os.path.join(d, "flag"), "w").close()
            with open(os.path.join(root, "station.log"), "a") as log:
                log.write(f"{mail.now()} flag {name} {why} unread={len(unread)}\n")


def reap():
    """Once a minute: proc.py reap (H-081). A failure goes to station.log and never stops the loop."""
    try:
        r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.realpath(__file__)), "proc.py"), "reap"],
                           capture_output=True, text=True, timeout=120)
        bad = r.returncode != 0
        why = f"exit {r.returncode} {r.stderr.strip()[:200]}"
    except Exception as ex:
        bad, why = True, f"{type(ex).__name__}: {ex}"
    if bad:
        with open(os.path.join(mail.mail_root(), "station.log"), "a") as log:
            log.write(f"{mail.now()} reap FAIL {why}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    last = time.monotonic() - 60
    while True:
        if not a.once and time.monotonic() - last >= 60:
            last = time.monotonic()
            reap()
        try:
            loop()
        except Exception as ex:  # a bad registry edit must not stop the daemon
            print(f"station: {type(ex).__name__}: {ex}", file=sys.stderr)
            if a.once:
                sys.exit(1)
        if a.once:
            return
        time.sleep(2)


if __name__ == "__main__":
    main()
