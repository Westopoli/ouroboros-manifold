#!/usr/bin/env python3
# spec: docs/stories/H-005.md
"""Method check at compaction: count, per rule, the turns of a chat transcript that broke it."""
import argparse
import json
import os
import re
import sys

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
    ("wakeups", "both", "DRIFT", "No scheduled wakeups: the wait is the Workflow or Agent notification (docs/method/runner.md)."),
    ("polling", "both", "DRIFT", "No chat sits in a wait loop or polls a gate; clerks inside scripts do (docs/method/runner.md)."),
    ("gate_runs", "both", "DRIFT", "Gates run inside landing clerks, never in a chat (docs/method/clerk.md)."),
    ("live_tree", "both", "DRIFT", "Never touch `~/Projects/ouroboros-manifold` as a working tree; work in a worktree made by `wt.py` (docs/method/builder.md)."),
    ("code_edits", "architect", "DRIFT", "The Fable chat writes no code; builders do. It writes stories, briefs and docs (docs/method/architect.md)."),
    ("context", "both", "DRIFT", "Restart from memory past 400k context; the compaction is not the restart (docs/method/architect.md)."),
]
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
        if cid == "polling":
            return n == "Monitor" or (s is not None and any(
                w in ("sleep", "flock") or ("gate.lock" in g and w not in READERS) for g, w in segments(s)))
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


def report(entries, live, threshold, session):
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
    role = role_of([last] if last is not None else [])
    others = [m for m in seen if m != last]
    model = "none" if last is None else last + (" (session also %s)" % ", ".join(others) if others else "")
    since = next((e["timestamp"] for e in span if e.get("timestamp")), "none")
    out = ["METHOD role %s model %s session %s span %d of %d turns %d since %s"
           % (role, model, session[:8], k + 1, len(spans), len(asst_span), since)]
    span_ids = {id(e) for e in span}
    drift = False
    for cid, roles, kind, rule in CHECKS:
        if roles != "both" and role != "unknown" and roles != role:
            continue
        if cid == "context":
            hits = [(e, {"name": "context", "input": {"command": str(ctx_size(e))}}) for e in asst_all if ctx_size(e) > threshold]
            hits.sort(key=lambda h: -ctx_size(h[0]))
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
    print("\n".join(report(load(path), live, a.threshold, session)))


if __name__ == "__main__":
    try:
        main()
    except BaseException as ex:
        if isinstance(ex, SystemExit) and ex.code in (0, None):
            pass
        else:
            print("METHOD error %s: %s" % (type(ex).__name__, " ".join(str(ex).split())[:200]))
    sys.exit(0)
