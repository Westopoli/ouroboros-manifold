"""Shared fixture helpers for the H-077 mail and station tests (a temp OM_PUSH_DIR and a fixture registry; never the
live ~/Projects/om-push). UNSTATED INTERFACE (reported): the fixture registry is handed to mail.py and station.py by the
env var OM_AGENTS_TOML (default docs/method/agents.toml); the mail root is $OM_PUSH_DIR/mail."""
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
MAIL = REPO / "scripts" / "method" / "mail.py"
STATION = REPO / "scripts" / "method" / "station.py"
HOOK = REPO / ".claude" / "hooks" / "mail-guard.sh"

REGISTRY = '''
[architect]
role = "architect.md"
rules = true
wake = ["block", "ask", "westley"]
senders = ["*"]

[architect2]
role = "architect.md"
rules = true

[planner]
role = "planner.md"
rules = false

[runner-lab]
role = "runner.md"
rules = false
linger_min = 3
batch = 2

[runner-beta]
role = "runner.md"
rules = false
wake = ["info"]

[westley]
role = "westley.md"
rules = false
senders = []

[closed]
role = "runner.md"
rules = false
senders = ["architect"]
'''


def make_env(tmp_path, registry=REGISTRY):
    home = tmp_path / "home"
    push = tmp_path / "om-push"
    home.mkdir(parents=True, exist_ok=True)
    push.mkdir(parents=True, exist_ok=True)
    reg = tmp_path / "agents.toml"
    reg.write_text(registry)
    env = {**os.environ, "HOME": str(home), "OM_PUSH_DIR": str(push), "OM_AGENTS_TOML": str(reg)}
    return env, push / "mail"


def mail(env, *args, timeout=30):
    return subprocess.run([sys.executable, str(MAIL), *args], env=env, capture_output=True, text=True, timeout=timeout)


def station_once(env):
    return subprocess.run([sys.executable, str(STATION), "--once"], env=env, capture_output=True, text=True, timeout=30)


def iso(minutes_ago=0):
    t = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=minutes_ago)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def put_mail(mailroot, agent, cls="info", minutes_ago=0, frm="architect", text="x", n=1):
    """Write n unread lines straight into the inbox (so the station and status tests need no send)."""
    d = mailroot / agent
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "inbox.jsonl", "a") as f:
        for i in range(n):
            f.write(json.dumps({"id": f"01TEST{agent}{cls}{i:04d}", "ts": iso(minutes_ago), "from": frm, "to": agent,
                                "class": cls, "re": "-", "text": text, "attach": [], "read": None}) + "\n")


def lines(path):
    p = Path(path)
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []
