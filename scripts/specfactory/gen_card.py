#!/usr/bin/env python3
"""Emit an Agora card's YAML frontmatter for one story, matching the format
already in use (~/Projects/agora/queue/200-e02-region-state.md): project,
goal, acceptance, allowed_files, snippet_file/symbol, header_file, rules_file,
test_file, expected_lines, max_wall_minutes.

The prose brief body is not generated here -- per the spec factory pipeline,
agy drafts it from the rules file only (never from the tests, the E-02
finding: a brief written from tests leaks implementation instead of intent),
and Claude reviews before it ships. This script emits a placeholder body
naming exactly that.

Usage:
    scripts/specfactory/gen_card.py E-03 S-021 --target-file csrc/region.c \\
        --symbols om_world_generate,om_world_new --out-num 201

--out-num picks the queue file's leading number; the caller is responsible
for not colliding with an existing card.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from derive_agora_rules import EPICS_DIR, parse_epic  # noqa: E402

AGORA_ROOT = Path.home() / "Projects" / "agora"
RULES_REL = "projects/ouroboros/rules"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("epic", help="Epic id, e.g. E-03")
    ap.add_argument("story", help="Story id, e.g. S-021")
    ap.add_argument("--target-file", required=True, help="C file this card is allowed to write, e.g. csrc/region.c")
    ap.add_argument("--symbols", default="", help="Comma-separated symbols this card must define")
    ap.add_argument("--out-num", required=True, help="Leading queue number, e.g. 201")
    ap.add_argument("--out-dir", type=Path, default=AGORA_ROOT / "queue")
    ap.add_argument("--max-wall-minutes", type=int, default=60)
    args = ap.parse_args(argv)

    epic_paths = list(EPICS_DIR.glob(f"{args.epic}-*.md"))
    if not epic_paths:
        print(f"no epic file matches {args.epic}", file=sys.stderr)
        return 1
    epic = parse_epic(epic_paths[0])
    story = next((s for s in epic["stories"] if s["id"] == args.story), None)
    if story is None:
        print(f"{args.story} not found in {args.epic}", file=sys.stderr)
        return 1

    test_glob = list((REPO / "tests" / "csim").glob(f"test_{args.epic.replace('-', '')}_{args.story.replace('-', '')}_*.py"))
    test_file = str(test_glob[0].relative_to(REPO)) if test_glob else f"tests/csim/test_{args.epic.replace('-', '')}_{args.story.replace('-', '')}_TODO.py"

    slug = args.story.lower().replace("-", "")
    filename = f"{args.out_num}-{args.epic.lower()}-{slug}.md"
    out_path = args.out_dir / filename

    rules_file = f"{RULES_REL}/{args.epic}.md"

    frontmatter = "\n".join(
        [
            "---",
            f"project: {REPO}",
            f'goal: "{args.target_file} implements {args.epic} {args.story} ({story["title"]}) so {test_file} passes"',
            "acceptance:",
            f'  - "{AGORA_ROOT}/.venv/bin/python -m pytest -q -p no:cacheprovider {test_file}"',
            f'allowed_files: "{args.target_file}"',
            f"snippet_file: {args.target_file}",
            f'snippet_symbol: "{args.symbols}"',
            "header_file: csrc/ouroboros_sim.h",
            f"rules_file: {rules_file}",
            f"test_file: {test_file}",
            "expected_lines: TODO",
            f"max_wall_minutes: {args.max_wall_minutes}",
            "---",
        ]
    )

    body = (
        f"\n\n## Brief for DeepSeek\n\n"
        f"TODO: agy drafts this from {rules_file} only (never from {test_file} -- "
        f"a brief written from the tests leaks implementation instead of intent, "
        f"the E-02 finding). Claude reviews the draft before this card ships.\n"
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        print(f"refusing to overwrite existing card: {out_path}", file=sys.stderr)
        return 1
    out_path.write_text(frontmatter + body, encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
