#!/usr/bin/env python3
"""apply_proofs.py <repo> [--dry-run] [--csv <all.csv>]: put a Proof line under every rule line and Invariant bullet
of the 22 epic files <repo>/docs/bible/epics/E-*.md, from all.csv (written by assemble.py, beside this script).

  proven row          ->  `  Proof: <file>::<name> | <kind> | verified PENDING`
  MISSING / MISSING?  ->  `  Proof: MISSING`
  unbuilt             ->  `  Proof: unbuilt`

Idempotent: Proof lines already directly under the bullet are replaced by the computed one, never duplicated, so a
second run changes nothing. Rule lines and bullets themselves are never edited (the rule pin hashes the rule line only).
A rule line is `^- R-ddd-dd`; an Invariant bullet is a top-level `- ` bullet under `## Invariants` (Nth = Invariant N).
Ids with no row in all.csv get no line (reported). Standard library only; reads and writes text only.
"""
import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULE_RE = re.compile(r"^- (R-\d{3}-\d{2})(?!\d)")
PROOF_RE = re.compile(r"^\s+Proof:")


def proof_line(row):
    p = row["proof"]
    if p in ("MISSING", "MISSING?"):
        return "  Proof: MISSING\n"
    if p == "unbuilt":
        return "  Proof: unbuilt\n"
    return f"  Proof: {p} | {row['kind']} | verified PENDING\n"


def rewrite(epic, text, rows):
    """returns (new text, inserted, replaced, unchanged, ids without a row)"""
    out, ins, rep, same, nofit = [], 0, 0, 0, []
    lines = text.splitlines(keepends=True)
    in_inv, n_inv, i = False, 0, 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        i += 1
        if line.startswith("## "):
            in_inv = line.strip() == "## Invariants"
            continue
        if (m := RULE_RE.match(line)):
            rid = m.group(1)
        elif in_inv and re.match(r"^[-*+] ", line):
            n_inv += 1
            rid = f"{epic} Invariant {n_inv}"
        else:
            continue
        if rid not in rows:
            nofit.append(rid)
            continue
        old = []
        while i < len(lines) and PROOF_RE.match(lines[i]):
            old.append(lines[i])
            i += 1
        new = proof_line(rows[rid])
        out.append(new)
        if not old:
            ins += 1
        elif old == [new]:
            same += 1
        else:
            rep += 1
    return "".join(out), ins, rep, same, nofit


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    dry = "--dry-run" in argv
    csv_path = Path(argv[argv.index("--csv") + 1]) if "--csv" in argv else HERE / "all.csv"
    if "--csv" in argv:
        args.remove(argv[argv.index("--csv") + 1])
    if len(args) != 1:
        print(__doc__.split("\n")[0], file=sys.stderr)
        return 2
    repo = Path(args[0])
    by_epic = {}
    for r in csv.DictReader(open(csv_path, newline="", encoding="utf-8")):
        by_epic.setdefault(r["epic"], {})[r["id"]] = r
    total = [0, 0, 0]
    for f in sorted((repo / "docs/bible/epics").glob("E-*.md")):
        epic = "E-" + re.match(r"E-(\d+)", f.name).group(1)
        text = f.read_bytes().decode("utf-8")
        new, ins, rep, same, nofit = rewrite(epic, text, by_epic.get(epic, {}))
        total = [total[0] + ins, total[1] + rep, total[2] + same]
        print(f"{epic}: {'would insert' if dry else 'inserted'} {ins}, replaced {rep}, already current {same}"
              + (f", no row for {len(nofit)}: {', '.join(nofit)}" if nofit else ""))
        if new != text and not dry:
            f.write_bytes(new.encode("utf-8"))
    print(f"all: {'would insert' if dry else 'inserted'} {total[0]}, replaced {total[1]}, already current {total[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
