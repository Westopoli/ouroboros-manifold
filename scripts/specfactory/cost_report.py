#!/usr/bin/env python3
"""Token and dollar totals from Claude Code session logs. Reads only timestamp, type, sessionId, message.model,
message.usage, requestId and the file path; never message content."""
import argparse
import json
import os
import sys

DEFAULT_ROOT = "~/.claude/projects/-home-westopoli-Projects-ouroboros-manifold"
USAGE_KEYS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
COLUMNS = ["key", "turns", "input", "output", "cache_write", "cache_read", "est_usd"]

# DRAFT-cost-rates: USD per million tokens, order (input, output, cache_write, cache_read).
DRAFT_COST_RATES = {
    "opus/fable": (15.0, 75.0, 18.75, 1.5),
    "sonnet": (3.0, 15.0, 3.75, 0.30),
    "haiku": (0.8, 4.0, 1.0, 0.08),
}


def rate_for(model):
    m = model.lower()
    if "opus" in m or "fable" in m:
        return DRAFT_COST_RATES["opus/fable"]
    if "sonnet" in m:
        return DRAFT_COST_RATES["sonnet"]
    if "haiku" in m:
        return DRAFT_COST_RATES["haiku"]
    return None


def role_of(rel):
    parts = rel.split(os.sep)
    if len(parts) > 2 and parts[1] == "subagents":
        return "workflow-agent" if len(parts) > 3 and parts[2] == "workflows" else "subagent"
    return "main"


def read_lines(root):
    """Yield (rel_path, parsed counting line) in file order, files sorted as plain strings of the relative path."""
    rels = []
    for d, _, names in os.walk(root):
        for n in names:
            if n.endswith(".jsonl"):
                rels.append(os.path.relpath(os.path.join(d, n), root))
    for rel in sorted(rels):
        with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as f:
            for raw in f:
                try:
                    o = json.loads(raw)
                except ValueError:
                    continue
                if not isinstance(o, dict) or o.get("type") != "assistant" or not isinstance(o.get("timestamp"), str):
                    continue
                msg = o.get("message")
                usage = msg.get("usage") if isinstance(msg, dict) else None
                if not isinstance(usage, dict):
                    continue
                tokens = tuple(usage[k] if isinstance(usage.get(k), (int, float)) else 0 for k in USAGE_KEYS)
                model = msg.get("model")
                yield rel, {"day": o["timestamp"][:10], "sid": str(o.get("sessionId", "<missing>")),
                            "model": model if isinstance(model, str) else "<missing>",
                            "req": o.get("requestId"), "tokens": tokens}


def dedup(root):
    """DEDUP. PRIMARY: group by requestId across all files and keep the LAST line of each group (streaming updates
    make the last line the final usage). FALLBACK, lines without requestId: key is the usage tuple, keep the FIRST
    per file. Returns kept lines, the first line of each requestId group, and the two drop counts."""
    last, first, order, tuples = {}, {}, [], {}
    n_req = n_tuple = 0
    for rel, ln in read_lines(root):
        ln["role"] = role_of(rel)
        if ln["req"]:
            if ln["req"] in last:
                n_req += 1
            else:
                first[ln["req"]] = ln
                order.append(ln["req"])
            last[ln["req"]] = ln
        elif (rel, ln["tokens"]) in tuples:
            n_tuple += 1
        else:
            tuples[(rel, ln["tokens"])] = ln
    kept = [last[r] for r in order] + list(tuples.values())
    firsts = [first[r] for r in order] + list(tuples.values())
    return kept, firsts, n_req, n_tuple


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--by", choices=("session", "day", "role"), default="day")
    ap.add_argument("--csv", action="store_true")
    a = ap.parse_args()
    root = os.path.expanduser(a.root)
    if not os.path.isdir(root):
        print(f"cost_report: --root is not a directory: {root}", file=sys.stderr)
        return 2

    kept, firsts, n_req, n_tuple = dedup(root)

    def inside(ln):
        return (not a.since or ln["day"] >= a.since) and (not a.until or ln["day"] <= a.until)

    kept = [l for l in kept if inside(l)]
    keep_first_out = sum(l["tokens"][1] for l in firsts if inside(l))
    key_of = {"session": lambda l: l["sid"], "day": lambda l: l["day"], "role": lambda l: l["role"]}[a.by]

    groups, unpriced = {}, set()
    for l in kept:
        rate = rate_for(l["model"])
        if rate is None:
            unpriced.add(l["model"])
        usd = sum(t * r for t, r in zip(l["tokens"], rate)) / 1e6 if rate else 0.0
        for k in (key_of(l), "TOTAL"):
            g = groups.setdefault(k, [0, 0, 0, 0, 0, 0.0])
            g[0] += 1
            for i, t in enumerate(l["tokens"]):
                g[1 + i] += t
            g[5] += usd
    groups.setdefault("TOTAL", [0, 0, 0, 0, 0, 0.0])
    keys = sorted(k for k in groups if k != "TOTAL") + ["TOTAL"]
    rows = [[k, *groups[k][:5], f"{groups[k][5]:.6f}"] for k in keys]

    out = sys.stderr if a.csv else sys.stdout
    if a.csv:
        print(",".join(COLUMNS))
        for r in rows:
            print(",".join(str(x) for x in r))
    else:
        for r in [COLUMNS] + rows:
            print(" ".join(str(x).rjust(12) if i else str(x).ljust(12) for i, x in enumerate(r)))
    for m in sorted(unpriced):
        print(f"no rate: {m}", file=out)
    print(f"dedup: {n_req} by requestId, {n_tuple} by tuple", file=out)
    print(f"note: keep-first would give {keep_first_out} output tokens, keep-last {groups['TOTAL'][2]}", file=out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
