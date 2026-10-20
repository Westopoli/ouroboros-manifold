#!/usr/bin/env python3
# spec: docs/northstar/plans/2026-10-19-harness-enforcement-spec.md section 1 HARNESS-C1a, sections 3 and 4
# See also: scripts/specfactory/spec_provenance.py (reason 8 reads the same pins; B_TAG, PIN_RE, rule_pin live there)
"""rule_pins.py pin|unwrap|rewrite|check|spec-of ...: rule pins of [B R-id@xxxxxx] tags. Standard library only."""
import re
import sys
import tomllib
from pathlib import Path

import spec_provenance as sp

ONE_TAG = re.compile(r"`(\[(?:B |W |P |DRAFT-|ASSERT |OPEN )[^`\n]*\])`")
PLACEHOLDER = re.compile(r"<|>|…|\.\.\.|\b(?:R-id|Q-id|name|xxxxxx|path)\b")

def edit(f, fn):
    """Apply fn(line number, line) to every line outside a fenced block; return the new text."""
    out, fenced = [], False
    for no, raw in enumerate(Path(f).read_text().splitlines(keepends=True), 1):
        edge = raw.lstrip().startswith("```")
        fenced ^= edge
        out.append(raw if fenced or edge else fn(no, raw))
    return "".join(out)

def repin(f):
    """(new text, [(line, id, old pin or None, right pin)] for every known id, [lines with a tag in backticks])."""
    rules, found, skips = sp.load_context(sp.find_root(Path(f)))["rule_lines"], [], []

    def line(no, raw):
        def one(p):
            rid = p.group(1)
            if rid not in rules:
                return p.group(0)
            found.append((no, rid, p.group(2), sp.rule_pin(rules[rid])))
            return f"{rid}@{found[-1][3]}"

        def tag(m):
            if raw.count("`", 0, m.start()) % 2:
                skips.append(no)
                return m.group(0)
            return "[B " + sp.PIN_RE.sub(one, m.group(1)) + m.group(2) + "]"
        return sp.B_TAG.sub(tag, raw)
    return edit(f, line), found, skips

def cmd_pin(args):
    rules = sp.load_context(sp.find_root(Path.cwd() / "-"))["rule_lines"]
    for rid in args:
        print(f"{rid}@{sp.rule_pin(rules[rid])}" if rid in rules else f"{rid}@?")
    return 2 if any(rid not in rules for rid in args) else 0

def cmd_unwrap(args):
    for f in args:
        n = 0
        def line(no, raw):
            def span(m):
                nonlocal n
                if PLACEHOLDER.search(re.sub(r'"[^"]*"', "", m.group(1))):
                    print(f"SKIP {f}:{no} placeholder")
                    return m.group(0)
                n += 1
                return m.group(1)
            return ONE_TAG.sub(span, raw)
        Path(f).write_text(edit(f, line))
        print(f"UNWRAP {f} {n} tags")
    return 0

def cmd_rewrite(args):
    for f in args:
        new, found, skips = repin(f)
        Path(f).write_text(new)
        print("".join(f"SKIP {f}:{no} tag in backticks\n" for no in skips), end="")
        added = sum(1 for h in found if h[2] is None)
        print(f"REPIN {f} {added} added {sum(1 for h in found if h[2] not in (None, h[3]))} refreshed")
    return 0

def cmd_check(args):
    only = {str(Path(a).resolve()) for a in args[args.index("--only") + 1:]} if "--only" in args else None
    files = args[:args.index("--only")] if only is not None else args
    found = {f: repin(f)[1] for f in files}
    bad = [(f, h) for f in files for h in found[f] if h[2] != h[3]]
    rejects = [(f, h) for f, h in bad if only is None or str(Path(f).resolve()) in only]
    for f, (no, rid, old, new) in rejects:
        print(f"PINS REJECT {f}:{no} {rid} {'stale' if old else 'missing'} {old or '-'} {new}")
    if len(bad) > len(rejects):
        print(f"PINS WARN {len(bad) - len(rejects)} stale outside the diff")
    elif not bad:
        print(f"PINS OK {len(files)} files {sum(map(len, found.values()))} ids")
    return 1 if rejects else 0

def cmd_spec_of(args):
    rows = {p["id"]: p for p in tomllib.loads(Path(args[0]).read_text()).get("piece", [])}
    print(*[rows.get(pid, {}).get("spec", "-") for pid in ",".join(args[1:]).split(",")], sep="\n")
    return 0

COMMANDS = {"pin": cmd_pin, "unwrap": cmd_unwrap, "rewrite": cmd_rewrite, "check": cmd_check, "spec-of": cmd_spec_of}

if __name__ == "__main__":
    cmd = COMMANDS.get(sys.argv[1] if len(sys.argv) > 2 else "")
    sys.exit(cmd(sys.argv[2:]) if cmd else print("usage: rule_pins.py pin|unwrap|rewrite|check|spec-of <args>", file=sys.stderr) or 2)
