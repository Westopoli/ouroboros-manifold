#!/usr/bin/env python3
"""Derive Agora per-epic rules files from docs/bible/epics/E-##-*.md.

Agora decision D17: DeepSeek reads distilled rules files, never the target's bible.
This script is the only path from the bible to those files, so the bible stays
fenced and the rules never drift from it by hand.

An epic is derived only when it has zero open flags in
docs/northstar/ambiguity_register.md. Epics with open flags are skipped and
reported. Output files carry a do-not-edit header naming their source.

Usage:
    scripts/derive_agora_rules.py [--out DIR] [--dry-run] [--epic E-01 ...]

Default output directory: ~/Projects/agora/projects/ouroboros/rules/
Exit code 0 when every requested epic was derived or skipped cleanly; 1 on a
malformed epic file.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EPICS_DIR = REPO / "docs" / "bible" / "epics"
REGISTER = REPO / "docs" / "northstar" / "ambiguity_register.md"
DEFAULT_OUT = Path.home() / "Projects" / "agora" / "projects" / "ouroboros" / "rules"

EPIC_FILE_RE = re.compile(r"^(E-\d{2})-.+\.md$")
STORY_HEAD_RE = re.compile(r"^### (S-\d{3}) — (.+)$")
RULE_RE = re.compile(r"^- (R-\d{3}-\d{2})\s+(.+)$")
SECTION_RE = re.compile(r"^## (.+)$")
FLAG_ROW_RE = re.compile(r"^\| (Q-[A-Za-z0-9]+-\d{2}) \| ([^|]+) \|.*\| (open|closed) \|")
# A flag is resolved-in-place when Westley answered or deferred it, even if the
# status column still reads "open" (the register is inconsistent about flipping it,
# and deferral notes land in different columns). These phrases are the reliable
# signal; a bare "needs Westley"/"Pending" note is NOT a resolution and still blocks.
_RESOLVED_RE = re.compile(r"answered by westley|deferred by westley|stays deferred", re.IGNORECASE)


def open_flags_by_epic(register_text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for line in register_text.splitlines():
        m = FLAG_ROW_RE.match(line)
        if not m:
            continue
        flag, scope, status = m.group(1), m.group(2).strip(), m.group(3)
        # Blocks only when open AND not resolved-in-place (answered or deferred).
        if status != "open" or _RESOLVED_RE.search(line):
            continue
        epic = scope.split("/")[0].strip()
        if not re.match(r"^E-\d{2}$", epic):
            legacy = re.match(r"^Q-E(\d{2})-", flag)
            epic = f"E-{legacy.group(1)}" if legacy else epic
        result.setdefault(epic, []).append(flag)
    return result


def parse_epic(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else path.stem
    sections: dict[str, list[str]] = {}
    current = None
    for line in lines[1:]:
        m = SECTION_RE.match(line)
        if m:
            current = m.group(1).strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    stories = []
    story = None
    for line in sections.get("Stories", []):
        m = STORY_HEAD_RE.match(line)
        if m:
            story = {"id": m.group(1), "title": m.group(2).strip(), "words": "", "rules": []}
            stories.append(story)
            continue
        if story is None:
            continue
        if line.startswith("As a ") and not story["words"]:
            story["words"] = line.strip()
            continue
        r = RULE_RE.match(line)
        if r:
            story["rules"].append((r.group(1), r.group(2).strip()))
    if not stories:
        raise ValueError(f"{path.name}: no stories found under '## Stories'")
    for s in stories:
        if not s["rules"]:
            raise ValueError(f"{path.name}: story {s['id']} has no rules")
    return {
        "title": title,
        "purpose": "\n".join(sections.get("Purpose", [])).strip(),
        "obvious": "\n".join(sections.get("Obviously working in 60 seconds", [])).strip(),
        "stories": stories,
        "invariants": "\n".join(sections.get("Invariants", [])).strip(),
        "wrong": "\n".join(sections.get("Ways this could be wrong", [])).strip(),
    }


def render(epic_id: str, rel_path: str, epic: dict) -> str:
    out = [
        f"# {epic['title']}",
        "",
        f"<!-- DO NOT EDIT. Derived from {rel_path} by scripts/derive_agora_rules.py. -->",
        f"<!-- Edit the epic file and rerun the script. Epic {epic_id} had zero open flags at derivation. -->",
        "",
        "## What this is",
        "",
        epic["purpose"],
        "",
        "## Obviously working in 60 seconds",
        "",
        epic["obvious"],
        "",
        "## Rules",
        "",
    ]
    for s in epic["stories"]:
        out.append(f"### {s['id']} — {s['title']}")
        if s["words"]:
            out.append(s["words"])
        out.append("")
        for rid, rule in s["rules"]:
            out.append(f"- {rid}  {rule}")
        out.append("")
    if epic["invariants"]:
        out += ["## Invariants", "", epic["invariants"], ""]
    if epic["wrong"]:
        out += ["## Ways this could be wrong — worth trying", "", epic["wrong"], ""]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--epic", nargs="*", default=None, help="Only these epic ids (E-01 ...)")
    args = ap.parse_args(argv)

    flags = open_flags_by_epic(REGISTER.read_text(encoding="utf-8"))
    derived, skipped, failed = [], [], []
    for path in sorted(EPICS_DIR.glob("E-*.md")):
        m = EPIC_FILE_RE.match(path.name)
        if not m:
            continue
        epic_id = m.group(1)
        if args.epic and epic_id not in args.epic:
            continue
        open_for_epic = flags.get(epic_id, [])
        if open_for_epic:
            skipped.append((epic_id, open_for_epic))
            continue
        try:
            epic = parse_epic(path)
        except ValueError as e:
            failed.append((epic_id, str(e)))
            continue
        rel = path.relative_to(REPO).as_posix()
        text = render(epic_id, rel, epic)
        target = args.out / f"{epic_id}.md"
        if args.dry_run:
            print(f"[dry-run] would write {target} ({len(text)} chars)")
        else:
            args.out.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            print(f"wrote {target}")
        derived.append(epic_id)

    print(f"derived: {len(derived)} {' '.join(derived)}".rstrip())
    for epic_id, fl in skipped:
        print(f"skipped {epic_id}: {len(fl)} open flag(s): {' '.join(fl)}")
    for epic_id, msg in failed:
        print(f"FAILED {epic_id}: {msg}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
