#!/usr/bin/env python3
"""Write one Agora build card: YAML frontmatter from the arguments (same shape
as gen_card.py, but with several stories, several test files, and extra
allowed files) plus a prose brief drafted by agy from the rules file only.
The card lands in --out (a scratch dir) for review; the reviewer copies it
into ~/Projects/agora/queue/.

Usage:
    scripts/specfactory/draft_card.py E-05 --num 202 --slug e05-faction-state \\
        --title "faction state, fixtures, budget accumulation" \\
        --target csrc/faction.c --allowed csrc/faction.c,csrc/om_internal.h,csrc/sim.c \\
        --symbols om_world_set_feature,om_faction_set,... \\
        --stories S-032,S-033 \\
        --tests tests/csim/test_E05_S032_every_faction_is_a_person.py,tests/csim/test_E05_S033_territory_pays_or_costs.py \\
        --earlier "201 (sim.c tick loop)" --index 1 --count 5 --wall 90 --out DIR
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
AGORA = Path.home() / "Projects" / "agora"
PROMPT = REPO / "docs/northstar/spec_factory/prompts/card_brief.md"
SCHEMA = REPO / "docs/northstar/spec_factory/schemas/brief.json"
WRAPPER = REPO / "scripts/agy_task.sh"
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))
from agy_json import payload_from_envelope  # noqa: E402
PYTEST = f"{AGORA}/.venv/bin/python -m pytest -q -p no:cacheprovider"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("epic")
    ap.add_argument("--num", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--allowed", required=True, help="comma-separated allowed files")
    ap.add_argument("--symbols", required=True, help="comma-separated symbols")
    ap.add_argument("--stories", required=True, help="comma-separated story ids")
    ap.add_argument("--tests", required=True, help="comma-separated test files this card must turn green")
    ap.add_argument("--also-green",
                    default=("tests/csim/test_E02_S012_composites.py tests/csim/test_E02_S013_military.py "
                             "tests/csim/test_E02_S014_economy.py tests/csim/test_E02_S015_adjacency.py "
                             "tests/csim/test_E02_S016_tension.py tests/csim/test_E02_S017_population.py "
                             "tests/csim/test_E02_S018_oscillation.py tests/csim/test_E02_S019_floor.py "
                             "tests/csim/test_E02_S020_determinism.py tests/csim/test_E02_gate_drift_trajectory.py "
                             "tests/csim/controls/test_control_composite_pre_clamp.py tests/csim/controls/test_control_empty_drifts.py "
                             "tests/csim/controls/test_control_ge_not_gt.py tests/csim/controls/test_control_osc_as_level.py "
                             "tests/csim/controls/test_control_raw_not_trend.py tests/csim/controls/test_control_slow.py"),
                    help="earlier suites that must stay green, listed explicitly so later epics' files are never swept in")
    ap.add_argument("--earlier", default="none")
    ap.add_argument("--index", type=int, required=True)
    ap.add_argument("--count", type=int, required=True)
    ap.add_argument("--wall", type=int, default=90)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--no-agy", action="store_true", help="write the YAML with a TODO brief")
    args = ap.parse_args()

    tests = [t.strip() for t in args.tests.split(",") if t.strip()]
    rules_file = f"projects/ouroboros/rules/{args.epic}.md"
    args.out.mkdir(parents=True, exist_ok=True)

    brief, expected_lines, notes = "TODO: brief not drafted", 0, ""
    if not args.no_agy:
        prompt = (PROMPT.read_text(encoding="utf-8")
                  .replace("{{CARD_TITLE}}", args.title)
                  .replace("{{TARGET_FILE}}", args.target)
                  .replace("{{SYMBOLS}}", args.symbols)
                  .replace("{{STORIES}}", args.stories)
                  .replace("{{CARD_INDEX}}", str(args.index))
                  .replace("{{CARD_COUNT}}", str(args.count))
                  .replace("{{EPIC_ID}}", args.epic)
                  .replace("{{EARLIER_CARDS}}", args.earlier)
                  .replace("{{RULES_FILE}}", str(AGORA / rules_file)))
        prompt_path = args.out / f"{args.num}-{args.slug}.prompt.md"
        prompt_path.write_text(prompt, encoding="utf-8")
        res = subprocess.run([str(WRAPPER), str(prompt_path), str(SCHEMA)],
                             cwd=REPO, capture_output=True, text=True)
        (args.out / f"{args.num}-{args.slug}.raw.json").write_text(res.stdout, encoding="utf-8")
        try:
            payload = payload_from_envelope(res.stdout, ("brief", "expected_lines", "questions", "assumptions"))
            if payload is None:
                raise ValueError("unusable agy output")
            brief = payload["brief"]
            expected_lines = int(payload["expected_lines"])
            notes = ("Questions\n" + "\n".join(f"- {q}" for q in payload["questions"])
                     + "\n\nAssumptions\n" + "\n".join(f"- {a}" for a in payload["assumptions"]) + "\n")
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            sys.stderr.write(f"agy brief unusable ({exc}); writing TODO brief\n{res.stderr[-800:]}\n")

    acceptance = [f'  - "{PYTEST} {t}"' for t in tests]
    acceptance.append(f'  - "{PYTEST} {args.also_green}"')
    fm = "\n".join([
        "---",
        f"project: {REPO}",
        f'goal: "{args.target} implements {args.epic} {args.stories} ({args.title}) so {", ".join(tests)} pass and earlier suites stay green"',
        "acceptance:",
        *acceptance,
        f'allowed_files: "{args.allowed}"',
        f"snippet_file: {args.target}",
        f'snippet_symbol: "{args.symbols.replace(",", ", ")}"',
        "header_file: csrc/ouroboros_sim.h",
        f"rules_file: {rules_file}",
        f"test_file: {tests[0]}",
        f"expected_lines: {expected_lines or 'TODO'}",
        f"max_wall_minutes: {args.wall}",
        "---",
    ])
    card = args.out / f"{args.num}-{args.slug}.md"
    card.write_text(fm + "\n\n## Brief for DeepSeek\n\n" + brief.strip() + "\n", encoding="utf-8")
    if notes:
        (args.out / f"{args.num}-{args.slug}.notes.md").write_text(notes, encoding="utf-8")
    print(f"card: {card} (expected_lines={expected_lines})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
