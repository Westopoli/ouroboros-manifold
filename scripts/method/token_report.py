#!/usr/bin/env python3
"""H-003 nightly token report. Story: docs/stories/H-003.md. Stdlib only.

Counts assistant lines of the project's transcripts once per requestId, weighted
input + output + cache_creation + cache_read/10, classed builder/tests/clerk/fable/runner/other.
Usage: token_report.py [--week 2026-W44 | --day 2026-10-29] [--verbose]
"""
import argparse
import collections
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

PROJ = ".claude/projects/-home-westopoli-Projects-ouroboros-manifold"
REPO = Path(__file__).resolve().parents[2]
HEADER = ("window,calls,weighted_tokens,builder_share,tests_share,build_plus_tests_share,"
          "fable_share,landings,seen,tokens_per_landed_line")
# First matching rule wins; substrings of the sidechain's first user line (story table).
RULES = (("builder", ("builder.md", "subagent_type: doer")), ("tests", ("test_writer.md",)),
         ("clerk", ("clerk.md", "landing", "records")))


def first_prompt(path):
    with open(path, errors="replace") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") == "user":
                c = d.get("message", {}).get("content", "")
                if isinstance(c, list):
                    c = " ".join(b.get("text", "") for b in c if isinstance(b, dict))
                return c
    return ""


def sidechain_class(prompt):
    low = prompt.lower()
    for name, keys in RULES:
        if any(k.lower() in low for k in keys):
            return name
    return "other"


def window_of(args):
    """Return (label, predicate on a UTC date)."""
    if args.day:
        d = dt.date.fromisoformat(args.day)
        return args.day, lambda x: x == d
    if args.week:
        y, w = args.week.split("-W")
    else:
        y, w, _ = dt.datetime.now(dt.timezone.utc).isocalendar()
    y, w = int(y), int(w)
    return "%d-W%02d" % (y, w), lambda x: tuple(x.isocalendar()[:2]) == (y, w)


def tally(root, inwin, verbose):
    seen, tok, calls, others = set(), collections.Counter(), 0, collections.Counter()
    for path in sorted(root.glob("**/*.jsonl")):
        side = "subagents" in path.parts
        cls = sidechain_class(first_prompt(path)) if side else None
        with open(path, errors="replace") as f:
            for line in f:
                if '"assistant"' not in line:
                    continue
                try:
                    d = json.loads(line)
                    if d.get("type") != "assistant":
                        continue
                    day = dt.datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")).astimezone(
                        dt.timezone.utc).date()
                    m = d["message"]
                    u = m["usage"]
                except (ValueError, KeyError, TypeError):
                    continue
                if not inwin(day):
                    continue
                key = d.get("requestId") or d.get("uuid")
                if key in seen:
                    continue
                seen.add(key)
                w = (u.get("input_tokens", 0) + u.get("output_tokens", 0)
                     + u.get("cache_creation_input_tokens", 0)
                     + u.get("cache_read_input_tokens", 0) / 10)
                c = cls
                if not side:
                    model = m.get("model", "")
                    c = "fable" if "fable" in model else "runner" if "sonnet" in model else "other"
                if c == "other" and verbose:
                    others[first_prompt(path)[:80].replace("\n", " ") if side else m.get("model", "")] += 1
                tok[c] += w
                calls += 1
    return calls, tok, others


def git_counts(inwin):
    log = subprocess.run(["git", "-C", str(REPO), "log", "--first-parent", "origin/main",
                          "--format=%H %cs %s"], capture_output=True, text=True).stdout
    land = seen = lines = 0
    for l in log.splitlines():
        h, day, subj = l.split(" ", 2)
        if not inwin(dt.date.fromisoformat(day)):
            continue
        if subj.startswith("Seen "):
            seen += 1
        elif subj.startswith("Land "):
            land += 1
            st = subprocess.run(["git", "-C", str(REPO), "diff", "--shortstat", h + "^1", h, "--",
                                 ".", ":(exclude)docs", ":(exclude)tests"],
                                capture_output=True, text=True).stdout
            for part in st.split(","):
                if "insertion" in part:
                    lines += int(part.split()[0])
    return land, seen, lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week")
    ap.add_argument("--day")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    label, inwin = window_of(args)
    calls, tok, others = tally(Path.home() / PROJ, inwin, args.verbose)
    total = sum(tok.values())
    pct = lambda n: 100.0 * n / total if total else 0.0
    b, t = pct(tok["builder"]), pct(tok["tests"])
    fa = pct(tok["fable"])
    land, seen, lines = git_counts(inwin)
    tpl = "%.0f" % (total / lines) if lines else ""
    row = "%s,%d,%d,%.1f,%.1f,%.1f,%.1f,%d,%d,%s" % (label, calls, round(total), b, t, b + t, fa,
                                                    land, seen, tpl)
    out = Path.home() / "Projects/om-push/metrics" / (label + ".csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(HEADER + "\n" + row + "\n")
    print(row)
    print("build+tests %.1f%% %s (50%%)   fable %.1f%% %s (25%%)" % (
        b + t, "OK" if b + t >= 50 else "UNDER", fa, "OK" if fa >= 25 else "UNDER"))
    for k, n in others.most_common(20):
        print("other: %5d  %s" % (n, k))


if __name__ == "__main__":
    sys.exit(main())
