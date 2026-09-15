#!/usr/bin/env python3
"""Report and (optionally) apply the mechanical half of folding closed register
answers into an epic file: dropping flag references once every flag a story or
the epic itself lists is closed.

This script never rewrites rule bodies. A closed answer that only confirms
existing rule text (or says "keep as-is") is safe to auto-strip; a closed
answer that implies new or changed rule content is a design decision and
stays Claude's to fold by hand (agy may draft a candidate rewrite for Claude
to review, per CLAUDE.md's sub-agent rules, but never edits the epic file
itself). This script's job is to find every closed-but-unfolded flag and
hand back exactly what a human or agy draft pass needs: the flag id, the
letter picked, the candidate text for that letter, and the full answer.

Usage:
    scripts/specfactory/fold_answers.py E-03 [--apply]

--apply strips closed flag ids from "Open flags:" lines (story-level and the
epic-level "## Open ambiguity flags" section), collapsing an empty list to
"none". It never touches rule bodies, the completeness-gate table, or the
gate verdict — those are judgment calls for Claude to re-run by hand.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
EPICS_DIR = REPO / "docs" / "bible" / "epics"
REGISTER = REPO / "docs" / "northstar" / "ambiguity_register.md"

FLAG_ROW_RE = re.compile(
    r"^\| (Q-[A-Za-z0-9]+-\d{2}) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| (open|closed) \| (.+) \|$"
)
LETTER_RE = re.compile(r"^\(([a-z])\)")
CANDIDATE_SPLIT_RE = re.compile(r"(?=\([a-z]\)\s)")
OPEN_FLAGS_LINE_RE = re.compile(r"^(Open flags:\s*)(.*)$")


def load_register_rows(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        m = FLAG_ROW_RE.match(line)
        if not m:
            continue
        flag, scope, question, candidates, status, answer = (g.strip() for g in m.groups())
        rows.append(
            {
                "flag": flag,
                "scope": scope,
                "question": question,
                "candidates": candidates,
                "status": status,
                "answer": answer,
            }
        )
    return rows


def candidate_for_letter(candidates: str, letter: str) -> str | None:
    parts = [p.strip().rstrip(";").strip() for p in CANDIDATE_SPLIT_RE.split(candidates) if p.strip()]
    for p in parts:
        if p.startswith(f"({letter})"):
            return p[len(f"({letter})"):].strip()
    return None


def flags_mentioned(epic_text: str) -> set[str]:
    return set(re.findall(r"Q-[A-Za-z0-9]+-\d{2}", epic_text))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("epic", help="Epic id, e.g. E-03")
    ap.add_argument("--apply", action="store_true", help="Strip closed flags from Open flags lines")
    args = ap.parse_args(argv)

    epic_paths = list(EPICS_DIR.glob(f"{args.epic}-*.md"))
    if not epic_paths:
        print(f"no epic file matches {args.epic}", file=sys.stderr)
        return 1
    epic_path = epic_paths[0]
    epic_text = epic_path.read_text(encoding="utf-8")

    rows = load_register_rows(REGISTER.read_text(encoding="utf-8"))
    mentioned = flags_mentioned(epic_text)
    relevant = [r for r in rows if r["flag"] in mentioned]

    closed_unfolded = [r for r in relevant if r["status"] == "closed"]
    still_open = [r for r in relevant if r["status"] == "open"]

    if still_open:
        print(f"{args.epic}: {len(still_open)} flag(s) still open, fold blocked on these:")
        for r in still_open:
            print(f"  {r['flag']}  {r['question'][:100]}")
        if not closed_unfolded:
            return 0

    print(f"{args.epic}: {len(closed_unfolded)} closed flag(s) referenced in the epic file")
    for r in closed_unfolded:
        m = LETTER_RE.match(r["answer"])
        letter = m.group(1) if m else None
        candidate_text = candidate_for_letter(r["candidates"], letter) if letter else None
        print(f"\n  {r['flag']}  (letter: {letter or 'n/a'})")
        print(f"    question:  {r['question']}")
        if candidate_text:
            print(f"    candidate: {candidate_text}")
        print(f"    answer:    {r['answer']}")
        print(f"    ACTION NEEDED: fold this into the epic's rule text by hand (or via an agy draft, Claude reviewing) —")
        print(f"    this script only removes the flag reference below, it does not write rule content.")

    if args.apply:
        closed_ids = {r["flag"] for r in closed_unfolded}
        new_lines = []
        changed = False
        for line in epic_text.splitlines():
            m = OPEN_FLAGS_LINE_RE.match(line)
            if not m:
                new_lines.append(line)
                continue
            prefix, rest = m.groups()
            if rest.strip().lower() == "none":
                new_lines.append(line)
                continue
            remaining_ids = [fid for fid in re.findall(r"Q-[A-Za-z0-9]+-\d{2}", rest) if fid not in closed_ids]
            if not remaining_ids:
                new_lines.append(f"{prefix}none")
                changed = True
            elif len(remaining_ids) < len(re.findall(r"Q-[A-Za-z0-9]+-\d{2}", rest)):
                kept = [seg.strip() for seg in rest.split(",") if any(fid in seg for fid in remaining_ids)]
                new_lines.append(prefix + ", ".join(kept))
                changed = True
            else:
                new_lines.append(line)
        if changed:
            epic_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            print(f"\napplied: stripped closed flag references in {epic_path.relative_to(REPO)}")
            print("NOTE: the completeness-gate table and gate verdict were not touched — re-run the gate by hand.")
        else:
            print("\napplied: nothing to strip (no Open flags line referenced a closed flag)")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
