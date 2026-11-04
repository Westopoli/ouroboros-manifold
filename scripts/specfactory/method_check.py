#!/usr/bin/env python3
# spec: docs/stories/H-005.md
"""Method check at compaction: count, per rule, the turns of a chat transcript that broke it."""
import argparse
import json
import os
import re
import sys
import tomllib

CODE_EXT = r"(?:c|h|gd|py|sh|tscn)"
EDIT_TOOLS = ("Edit", "Write", "NotebookEdit")
AGENT_TOOLS = ("Agent", "Task")  # See also: method_metrics_runs.py:344 (reads mc.AGENT_TOOLS)
GIT_MUTATE = re.compile(r"\bgit\s+(?:add|commit|push|checkout|switch|merge|stash|reset|rm|mv)\b")
REDIRECT = re.compile(r"(?:>>?|\btee\b(?:\s+-\w+)*)\s*[\"']?[^\s\"'|;&<>]*\.%s(?![\w.])" % CODE_EXT)
HEREDOC = re.compile(r"(?<!<)<<-?\s*([\"']?)(\w+)\1")
SEGMENT_SPLIT = re.compile(r"&&|\|\||;|\||\n")
READERS = ("cat", "sed", "head", "tail", "grep", "ls", "wc", "echo", "git", "stat", "du", "find", "awk", "diff", "python3")

# id, roles, kind, rule line
CHECKS = [
    ("wakeups", "both", "DRIFT", "No scheduled wakeups: the wait is the Workflow or Agent notification or `mail.py wait` (docs/method/runner.md)."),
    ("polling", "both", "DRIFT", "No chat sits in a wait loop or polls a gate; clerks inside scripts do (docs/method/runner.md)."),
    ("gate_runs", "both", "DRIFT", "Gates run inside landing clerks, never in a chat (docs/method/clerk.md)."),
    ("live_tree", "both", "DRIFT", "Never touch `~/Projects/ouroboros-manifold` as a working tree; work in a worktree made by `wt.py` (docs/method/builder.md)."),
    ("code_edits", "architect", "DRIFT", "The Fable chat writes no code; builders do. It writes stories, briefs and docs (docs/method/architect.md)."),
    ("context", "both", "DRIFT", "Compaction at 400k is the only context rule; a turn past 400k without a compaction is drift (docs/method/architect.md)."),
    ("plan_reread", "both", "DRIFT", "After a compaction read every file of the reading list before any mutating call (docs/method/reading_list.toml)."),
    ("comm_send", "both", "DRIFT", "Never `SendMessage` another chat: `mail.py send` (docs/method/communication.md)."),
    ("comm_state_checks", "both", "DRIFT", "No more than three state-check commands in one wakeup: git log, status.sh, lock listings (docs/method/communication.md)."),
    ("comm_mail_first", "both", "DRIFT", "Every wakeup begins with `mail.py read --me <name>` (docs/method/communication.md)."),
]
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
READING_LIST = "docs/method/reading_list.toml"
ROADMAP = "docs/northstar/ROADMAP.md"
PLANS_DIR = "docs/northstar/plans/"
MUTATING_TOOLS = EDIT_TOOLS + AGENT_TOOLS + ("SendMessage",)
PLAN_REREAD = ("PLAN RE-READ %s: this plan needs to be re-read, fully, because you are the architect and the plan execution "
               "depends on your ability to guide the dispatchers in their work and collaborate between them and help them "
               "when they get stuck. If you don't have full context of the plan, guesses will be made, and the output will "
               "not be what the plan file required, verifications will fail, and we'll waste time and effort on issues "
               "that could have been avoided.")
NEXT = ("METHOD next: quote every DRIFT line to Westley in your first message after this compaction, before any other "
        "work, and stop the behaviour. A DRIFT line is never argued away: a rule change is Westley's to make.")


def in_scratch(p):
    return "om-push/scratch/" in str(p).replace("$HOME", "~").replace(os.path.expanduser("~"), "~")


def under(path, base):
    return path == base or path.startswith(base + os.sep)


def segments(s):
    kept, end = [], None
    for line in s.split("\n"):
        if end is not None:
            if line.strip() == end:
                end = None
            continue
        kept.append(line)
        m = HEREDOC.search(line)
        if m:
            end = m.group(2)
    return [(seg, (seg.split() or [""])[0]) for seg in SEGMENT_SPLIT.split("\n".join(kept))]


def resolve(path, cwd):
    p = os.path.expanduser(str(path))
    if not os.path.isabs(p):
        p = os.path.join(cwd or "", p)
    return os.path.realpath(p)


def load(path):
    entries = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if isinstance(e, dict) and e.get("type") in ("assistant", "user") and e.get("isSidechain") is not True:
                entries.append(e)
    return entries


def session_name(path):
    """The /rename name: the last custom-title or agent-name entry of the transcript."""
    name = ""
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if isinstance(e, dict):
                n = e.get("customTitle") if e.get("type") == "custom-title" else e.get("agentName") if e.get("type") == "agent-name" else None
                if n:
                    name = str(n)
    return name


def reading_list(role, name, root):
    """(files, match-list owner) for the chat, or None when reading_list.toml is missing."""
    p = os.path.join(root, READING_LIST)
    if not os.path.exists(p):
        return None
    with open(p, "rb") as f:
        d = tomllib.load(f)
    if role == "architect":
        return d["architect"]["files"]
    beta = d["runner_beta"]
    return beta["files"] if any(m in name for m in beta.get("match", [])) else d["runner_lab"]["files"]


def plans_executed(files, root):
    """Files of the list under docs/northstar/plans/ that ROADMAP section 1 names (full path or plans/<name>)."""
    with open(os.path.join(root, ROADMAP), encoding="utf-8") as f:
        m = re.search(r"^## 1\.[^\n]*\n(.*?)(?=^## |\Z)", f.read(), re.S | re.M)
    sec = m.group(1) if m else ""
    return [x for x in files if x.startswith(PLANS_DIR) and ("plans/" + x[len(PLANS_DIR):]) in sec]


def is_read(c, cwd, rel, root):
    path = os.path.join(root, rel)
    i = c["input"]
    if c["name"] == "Read":
        return bool(i.get("file_path")) and resolve(i["file_path"], cwd) == os.path.realpath(path)
    s = str(i.get("command") or "") if c["name"] == "Bash" else ""
    return bool(s) and all(w in READERS or w == "cd" for g, w in segments(s)) and (rel in s or path in s)


def is_mutating(c):
    if c["name"] == "Bash":
        return any((w not in READERS and w != "cd" and w) or GIT_MUTATE.search(g) for g, w in segments(str(c["input"].get("command") or "")))
    return c["name"] in MUTATING_TOOLS


def ctx_size(e):
    u = (e.get("message") or {}).get("usage") or {}
    return sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))


def calls(e):
    c = (e.get("message") or {}).get("content")
    if not isinstance(c, list):
        return []
    return [b for b in c if isinstance(b, dict) and b.get("type") == "tool_use" and isinstance(b.get("input"), dict)]


def role_of(models):
    kinds = set()
    for m in models:
        m = m.lower()
        kinds.add("runner" if "sonnet" in m else "architect" if ("fable" in m or "opus" in m) else "unknown")
    return kinds.pop() if len(kinds) == 1 else "unknown"


def excerpt(c):
    i = c["input"]
    text = i.get("command") or i.get("file_path") or json.dumps(i, sort_keys=True)
    return " ".join(str(text).split())[:100]


# H-077: a `Bash` segment that is a state check, and a `SendMessage` target a chat may use (main or a sub-agent id).
STATE_CHECK = re.compile(r"^\s*(?:git\s+(?:-C\s+\S+\s+)?(?:log|status|rev-parse|branch)\b|(?:\S*/)?status\.sh\b|"
                         r"(?:python3\s+)?(?:\S*/)?status_check\.py\b|flock\b|ls\b.*\.lock\b)")
MAIL_WAIT = "python3 scripts/method/mail.py wait"
MAIL_READ = re.compile(r"mail\.py\s+read\b")


def is_user_turn(e):
    c = (e.get("message") or {}).get("content")
    return e["type"] == "user" and e.get("isCompactSummary") is not True and not (isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c))


def wakeups(entries):
    """The spans from one user turn to the next, each (user entry, [assistant entries]); the entries before the first user turn are no wakeup."""
    spans = []
    for e in entries:
        if is_user_turn(e):
            spans.append((e, []))
        elif spans and e["type"] == "assistant":
            spans[-1][1].append(e)
    return spans


def westley_typed(e):
    c = (e.get("message") or {}).get("content")
    return isinstance(c, str) and not c.startswith("<task-notification>")


def comm_hits(cid, entries):
    hits = []
    for user, asst in wakeups(entries):
        seq = [(e, c) for e in asst for c in calls(e)]
        if cid == "comm_mail_first" and seq and not westley_typed(user) and not (
                seq[0][1]["name"] == "Bash" and MAIL_READ.search(str(seq[0][1]["input"].get("command") or ""))):
            hits.append(seq[0])
        if cid == "comm_state_checks":
            found = [(e, c) for e, c in seq if c["name"] == "Bash"
                     for g, w in segments(str(c["input"].get("command") or "")) if STATE_CHECK.match(g)]
            if len(found) > 3:
                hits.append(found[3])
    return hits


# H-059: the retired single lock and the two channel locks all mean "a chat waits on a gate".
GATE_LOCKS = ("gate-lab.lock", "gate-beta.lock")


def matcher(cid, role, live):
    def under_live(p, cwd):
        return under(resolve(p, cwd), live)

    def cmd(c):
        return str(c["input"].get("command") or "") if c["name"] == "Bash" else None

    def hit(c, cwd):
        n, i, s = c["name"], c["input"], cmd(c)
        fp = i.get("file_path") or i.get("notebook_path")
        if cid == "wakeups":
            return n == "ScheduleWakeup"
        if cid == "comm_send":
            to = str(i.get("to") or "")
            return n == "SendMessage" and not (to == "main" or re.match(r"a[0-9a-f]{8,}", to))
        if cid == "polling":
            return n == "Monitor" or (s is not None and not s.startswith(MAIL_WAIT) and any(
                w in ("sleep", "flock") or (any(n in g for n in GATE_LOCKS) and w not in READERS) for g, w in segments(s)))
        if cid == "gate_runs":
            return s is not None and any(
                ("merge_gate.sh" in g or "pre_gate.sh" in g) and w not in READERS for g, w in segments(s))
        if cid == "live_tree":
            if n in EDIT_TOOLS:
                return bool(fp) and under_live(fp, cwd)
            return bool(s) and any(GIT_MUTATE.search(g) for g, w in segments(s)) and "om-push" not in s and under_live(cwd or "", "")
        if cid == "code_edits":
            # G20: runner scripts under om-push/scratch/ are briefs, not code (spec method_rev3 G20)
            if n in EDIT_TOOLS:
                return bool(fp) and re.search(r"\.%s$" % CODE_EXT, str(fp)) is not None and not in_scratch(fp)
            return bool(s) and any(not in_scratch(m.group(0)) for g, w in segments(s) for m in REDIRECT.finditer(g))
        return False
    return hit


def report(entries, live, threshold, session, name="", root=REPO_ROOT):
    spans = [[]]
    for e in entries:
        if e["type"] == "user" and e.get("isCompactSummary") is True:
            spans.append([])
        spans[-1].append(e)
    with_asst = [k for k, s in enumerate(spans) if any(e["type"] == "assistant" for e in s)]
    k = with_asst[-1] if with_asst else len(spans) - 1
    span = spans[k]
    asst_all = [e for e in entries if e["type"] == "assistant"]
    asst_span = [e for e in span if e["type"] == "assistant"]
    seen = []
    for e in asst_all:
        m = (e.get("message") or {}).get("model") or ""
        if not m.startswith("<") and m not in seen:
            seen.append(m)
    last = next((m for m in ((e.get("message") or {}).get("model") or "" for e in reversed(asst_span)) if not m.startswith("<")), None)
    first = next((m for m in ((e.get("message") or {}).get("model") or "" for e in asst_all) if not m.startswith("<")), None)
    role = role_of([first] if first is not None else [])
    others = [m for m in seen if m != last]
    model = "none" if last is None else last + (" (session also %s)" % ", ".join(others) if others else "")
    since = next((e["timestamp"] for e in span if e.get("timestamp")), "none")
    files = reading_list(role, name, root)
    out = ["METHOD read first: " + (" ".join(files) if files is not None else "NONE (%s missing)" % READING_LIST)]
    if role == "architect" and files is not None:
        out += [PLAN_REREAD % p for p in plans_executed(files, root)]
    out.append("METHOD role %s model %s session %s span %d of %d turns %d since %s"
           % (role, model, session[:8], k + 1, len(spans), len(asst_span), since))
    span_ids = {id(e) for e in span}
    drift = False
    for cid, roles, kind, rule in CHECKS:
        if roles != "both" and role != "unknown" and roles != role:
            continue
        if cid == "plan_reread" and k == 0:
            continue
        if cid == "plan_reread":
            hits, unread, first_unread = [], list(files or []), []
            for e in (span if k > 0 and files is not None else []):
                if e["type"] != "assistant":
                    continue
                for c in calls(e):
                    if unread and is_mutating(c):
                        first_unread = first_unread or list(unread)
                        hits.append((e, c))
                        break
                    unread = [x for x in unread if not is_read(c, e.get("cwd") or "", x, root)]
        elif cid == "context":
            hits, run = [], []  # a lone turn past the threshold that a compaction follows is the allowed one turn (H-062)
            for e in entries + [{"type": "end"}]:
                if e["type"] == "assistant" and ctx_size(e) > threshold:
                    run.append(e)
                    continue
                if e["type"] == "assistant" or e["type"] == "end" or e.get("isCompactSummary") is True:
                    lone = len(run) == 1 and e.get("isCompactSummary") is True
                    hits += [] if lone else [(r, {"name": "context", "input": {"command": str(ctx_size(r))}}) for r in run]
                    run = []
            hits.sort(key=lambda h: -ctx_size(h[0]))
        elif cid in ("comm_state_checks", "comm_mail_first"):
            hits = comm_hits(cid, entries)
        else:
            hit = matcher(cid, role, live)
            hits = []
            for e in asst_all:
                cwd = e.get("cwd") or ""
                for c in calls(e):
                    if hit(c, cwd):
                        hits.append((e, c))
                        break
        in_span = [h for h in hits if id(h[0]) in span_ids]
        ns, nt = len(in_span), len(hits)
        status = "DRIFT" if ns else "OK"
        drift = drift or status == "DRIFT"
        out.append("METHOD %s %s span %d session %d  %s" % (cid, status, ns, nt, rule))
        pool = in_span if ns else hits
        if cid == "context" and not pool and asst_span:
            big = max(asst_span, key=ctx_size)
            pool = [(big, {"name": "context", "input": {"command": str(ctx_size(big))}})]
        if cid == "plan_reread" and ns:
            out.append("  unread at the first mutating call: " + " ".join(first_unread))
        for e, c in pool[:3]:
            if cid == "context":
                out.append("  %s context %d" % (e.get("timestamp", ""), ctx_size(e)))
            else:
                out.append("  %s %s %s" % (e.get("timestamp", ""), c["name"], excerpt(c)))
    out.append("METHOD verdict %s" % ("DRIFT" if drift else "OK"))
    out.append(NEXT)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript")
    ap.add_argument("--live-checkout", default="~/Projects/ouroboros-manifold")
    ap.add_argument("--threshold", type=int, default=400000)
    a = ap.parse_args()
    live = os.path.realpath(os.path.expanduser(a.live_checkout))
    path, session = a.transcript, ""
    if path:
        session = os.path.splitext(os.path.basename(path))[0]
    elif not sys.stdin.isatty():
        data = json.loads(sys.stdin.read())
        path, session = data["transcript_path"], str(data.get("session_id") or "")
    if not path:
        raise ValueError("no transcript given")
    print("\n".join(report(load(path), live, a.threshold, session, session_name(path))))


if __name__ == "__main__":
    try:
        main()
    except BaseException as ex:
        if isinstance(ex, SystemExit) and ex.code in (0, None):
            pass
        else:
            print("METHOD error %s: %s" % (type(ex).__name__, " ".join(str(ex).split())[:200]))
    sys.exit(0)
