#!/usr/bin/env python3
"""Definition of Ready check for one epic file.

Checks, per `docs/northstar/agile.md`'s Definition of Ready:
  1. Every required section is present and non-empty.
  2. Zero open ambiguity-register flags scoped to this epic.
  3. Every visible-surface story (one with a references note) has a
     non-empty references directory under docs/bible/references/E-##/.
  4. The Scale requirements section is dated ("Confirmed by Westley <date>"),
     not merely "Proposed for Westley to confirm".

Usage:
    scripts/specfactory/dor_check.py E-03

Exit code 0 if Ready, 1 if blocked (with the exact blocking items printed).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
EPICS_DIR = REPO / "docs" / "bible" / "epics"
REGISTER = REPO / "docs" / "northstar" / "ambiguity_register.md"
REFERENCES_DIR = REPO / "docs" / "bible" / "references"

REQUIRED_SECTIONS = [
    "Purpose",
    "Obviously working in 60 seconds",
    "Stories",
    "Inputs",
    "Outputs",
    "Invariants",
    "Scale requirements",
    "Look and behavior references",
    "Ways this could be wrong",
    "Open ambiguity flags",
    "Depends on",
]

SECTION_RE = re.compile(r"^## (.+)$")
FLAG_ROW_RE = re.compile(
    r"^\| (Q-[A-Za-z0-9]+-\d{2}) \| ([^|]+) \|.*\| (open|closed) \|"
)
CONFIRMED_RE = re.compile(r"Confirmed by Westley\b.*\d{4}-\d{2}-\d{2}")


def split_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        m = SECTION_RE.match(line)
        if m:
            current = m.group(1).strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def open_flags_for_epic(register_text: str, epic_id: str) -> list[str]:
    result = []
    for line in register_text.splitlines():
        m = FLAG_ROW_RE.match(line)
        if not m:
            continue
        flag, scope, status = m.group(1), m.group(2).strip(), m.group(3)
        if status != "open":
            continue
        if scope.split("/")[0].strip() == epic_id:
            result.append(flag)
    return result


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("epic", help="Epic id, e.g. E-03")
    args = ap.parse_args(argv)

    epic_paths = list(EPICS_DIR.glob(f"{args.epic}-*.md"))
    if not epic_paths:
        print(f"no epic file matches {args.epic}", file=sys.stderr)
        return 1
    epic_path = epic_paths[0]
    text = epic_path.read_text(encoding="utf-8")
    sections = split_sections(text)

    blocking: list[str] = []

    for name in REQUIRED_SECTIONS:
        if name not in sections:
            blocking.append(f"missing section: ## {name}")
        elif not sections[name]:
            blocking.append(f"empty section: ## {name}")

    open_flags = open_flags_for_epic(REGISTER.read_text(encoding="utf-8"), args.epic)
    if open_flags:
        blocking.append(f"{len(open_flags)} open register flag(s): {', '.join(open_flags)}")

    scale = sections.get("Scale requirements", "")
    if scale and not CONFIRMED_RE.search(scale):
        blocking.append(
            "Scale requirements not dated (needs 'Confirmed by Westley <date>...'): "
            + scale.splitlines()[0][:100]
        )

    stories_text = sections.get("Stories", "")
    story_ids = re.findall(r"^### (S-\d{3})", stories_text, re.MULTILINE)
    epic_ref_dir = REFERENCES_DIR / args.epic
    look_section = sections.get("Look and behavior references", "")
    if story_ids and "none required" not in look_section.lower():
        if not epic_ref_dir.is_dir() or not any(epic_ref_dir.iterdir()):
            blocking.append(
                f"visible-surface stories present ({', '.join(story_ids)}) but "
                f"{epic_ref_dir.relative_to(REPO)} is missing or empty, and "
                "'Look and behavior references' doesn't say none required"
            )

    if blocking:
        print(f"{args.epic}: NOT READY, {len(blocking)} blocking item(s)")
        for b in blocking:
            print(f"  - {b}")
        return 1

    print(f"{args.epic}: READY")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
