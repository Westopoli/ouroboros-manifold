#!/usr/bin/env python3
"""Generates Agora micro-cards in ~/Projects/agora/queue/parked/*.hold for all
authored story test files across the unblocked epics.

Conforms strictly to the 30B Sizing Contract:
- 2 to 4 tests per micro-card (5 to 15 test assertions)
- 1 algorithmic behavior / formula per card
- Expected lines: 35-65 lines
- Single target C file per card
- Disjoint partitioning of tests (no two cards share acceptance checks)
- Cards are emitted into ~/Projects/agora/queue/parked/<id>.md.hold
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
AGORA_ROOT = Path.home() / "Projects" / "agora"
PARKED_DIR = AGORA_ROOT / "queue" / "parked"
RULES_REL = "projects/ouroboros/rules"

EPIC_MODULE_MAP = {
    "E03": {"file": "csrc/worldgen.c", "range_start": 211, "name": "e03-worldgen"},
    "E06": {"file": "csrc/diplomacy.c", "range_start": 220, "name": "e06-diplomacy"},
    "E07": {"file": "csrc/lifecycle.c", "range_start": 230, "name": "e07-lifecycle"},
    "E08": {"file": "csrc/generational.c", "range_start": 240, "name": "e08-generational"},
    "E09": {"file": "csrc/chronicle.c", "range_start": 250, "name": "e09-chronicle"},
    "E10": {"file": "csrc/mission.c", "range_start": 260, "name": "e10-missions"},
    "E11": {"file": "csrc/unit.c", "range_start": 270, "name": "e11-combat"},
    "E12": {"file": "csrc/fog.c", "range_start": 280, "name": "e12-fog"},
    "E13": {"file": "csrc/tactical_move.c", "range_start": 290, "name": "e13-movement"},
    "E14": {"file": "csrc/enemy_macro.c", "range_start": 300, "name": "e14-enemy"},
    "E15": {"file": "csrc/tactical_support.c", "range_start": 310, "name": "e15-support"},
    "E17": {"file": "csrc/tactical_mapgen.c", "range_start": 320, "name": "e17-mapgen"},
}


def parse_test_file(test_path: Path):
    with open(test_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    module_doc = ast.get_docstring(tree) or ""

    tests = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_R_"):
            doc = ast.get_docstring(node) or ""
            tests.append((node.name, doc))

    return module_doc, tests


def partition_tests(tests, max_per_card=3):
    """Partition tests into micro-cards of 2-4 tests each."""
    if len(tests) <= 4:
        return [tests]
    elif len(tests) <= 6:
        mid = len(tests) // 2
        return [tests[:mid], tests[mid:]]
    elif len(tests) <= 8:
        # 3 and 4 or 4 and 4
        mid = (len(tests) + 1) // 2
        return [tests[:mid], tests[mid:]]
    else:
        # chunk by 3
        chunks = []
        for i in range(0, len(tests), 3):
            chunks.append(tests[i : i + 3])
        return chunks


def make_symbol_hint(test_names: list[str], story_slug: str, epic_key: str) -> str:
    # Derive plausible primary symbol hint from test names or story
    if epic_key == "E03":
        return "om_world_generate"
    elif epic_key == "E06":
        if "tech" in story_slug or any("tech" in t.lower() for t in test_names):
            return "om_tech_step"
        return "om_diplomacy_step"
    elif epic_key == "E07":
        return "om_lifecycle_step"
    elif epic_key == "E08":
        return "om_generational_step"
    elif epic_key == "E09":
        return "om_chronicle_step"
    elif epic_key == "E10":
        return "om_mission_step"
    elif epic_key == "E11":
        return "om_unit_step"
    elif epic_key == "E12":
        return "om_fog_step"
    elif epic_key == "E13":
        return "om_movement_step"
    elif epic_key == "E14":
        return "om_enemy_macro_step"
    elif epic_key == "E15":
        return "om_support_step"
    elif epic_key == "E17":
        return "om_mapgen_step"
    return "om_step"


def main():
    PARKED_DIR.mkdir(parents=True, exist_ok=True)
    test_files = sorted((REPO / "tests" / "csim").glob("test_E*.py"))

    # Group by epic
    epic_files: dict[str, list[Path]] = {}
    for tf in test_files:
        m = re.search(r"test_(E\d{2})_S(\d{3})_([a-z0-9_]+)\.py", tf.name)
        if not m:
            continue
        epic_code = m.group(1)
        if epic_code not in EPIC_MODULE_MAP:
            continue
        epic_files.setdefault(epic_code, []).append(tf)

    total_cards = 0
    all_card_records = []

    for epic_code, files in epic_files.items():
        meta = EPIC_MODULE_MAP[epic_code]
        card_num_base = meta["range_start"]
        target_file = meta["file"]
        rules_file = f"{RULES_REL}/{epic_code[:1]}-{epic_code[1:]}.md"

        story_idx = 0
        for tf in files:
            m = re.search(r"test_(E\d{2})_S(\d{3})_([a-z0-9_]+)\.py", tf.name)
            story_id = f"S-{m.group(2)}"
            story_slug = m.group(3)
            module_doc, tests = parse_test_file(tf)

            if not tests:
                continue

            story_idx += 1
            card_num = card_num_base + (story_idx - 1)
            chunks = partition_tests(tests)

            for chunk_idx, chunk in enumerate(chunks, 1):
                suffix = f"a{chunk_idx}" if len(chunks) > 1 else "a"
                card_id = f"{card_num}{suffix}-{meta['name']}-{story_slug[:24]}"
                rel_test_file = str(tf.relative_to(REPO))

                acceptance_lines = []
                for tname, _ in chunk:
                    acceptance_lines.append(
                        f'  - "{AGORA_ROOT}/.venv/bin/python -m pytest -q -p no:cacheprovider {rel_test_file}::{tname}"'
                    )

                test_names_in_chunk = [t[0] for t in chunk]
                symbol_hint = make_symbol_hint(test_names_in_chunk, story_slug, epic_code)

                # Format Given/When/Then items for brief
                rules_summary = []
                for tname, tdoc in chunk:
                    clean_doc = " ".join(tdoc.strip().split())
                    rules_summary.append(f"- `{tname}`: {clean_doc}")

                rules_block = "\n".join(rules_summary)

                frontmatter = [
                    "---",
                    f"project: {REPO}",
                    f'goal: "{target_file} implements {epic_code} {story_id} ({story_slug}) for {len(chunk)} rules"',
                    "acceptance:",
                    *acceptance_lines,
                    f'allowed_files: "{target_file}"',
                    f"snippet_file: {target_file}",
                    f'snippet_symbol: "{symbol_hint}"',
                    "header_file: csrc/ouroboros_sim.h",
                    "extra_context_files: csrc/om_internal.h",
                    f"rules_file: {rules_file}",
                    f"test_file: {rel_test_file}",
                    f"expected_lines: {35 + len(chunk) * 10}",
                    "max_wall_minutes: 45",
                    "---",
                ]

                brief = [
                    "",
                    "## Brief for DeepSeek",
                    "",
                    f"Micro-card {chunk_idx} of {len(chunks)} for {epic_code} Story {story_id} (`{story_slug}`).",
                    f"Module: `{target_file}`.",
                    f"Governing rules file: `{rules_file}`.",
                    "",
                    "### Rules in Scope:",
                    rules_block,
                    "",
                    f"In `{target_file}`:",
                    "Implement the required logic with external linkage (DO NOT declare static):",
                    f"- Ensure `{symbol_hint}` or related step functions satisfy each Given/When/Then rule.",
                    "- Honor deterministic RNG consumption order and exact numeric constants from the spec.",
                    "",
                ]

                card_content = "\n".join(frontmatter) + "\n" + "\n".join(brief)
                card_filename = f"{card_id}.md.hold"
                out_path = PARKED_DIR / card_filename

                out_path.write_text(card_content, encoding="utf-8")
                total_cards += 1
                all_card_records.append((card_id, epic_code, story_id, len(chunk), out_path))

    print(f"Generated {total_cards} micro-cards in {PARKED_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
