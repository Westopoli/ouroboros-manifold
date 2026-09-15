#!/usr/bin/env python3
"""Draft an epic's Stage 3 e2e file with agy, from the prompt template in
docs/northstar/spec_factory/prompts/draft_e2e.md. Writes the draft to
--out (default: the scratch dir given), never to docs/northstar/e2e/; the
reviewer moves it there after reading it.

Usage:
    scripts/specfactory/draft_e2e.py E-05 --alg "ALG-11 through ALG-25 and ALG-29" --out /tmp/e05
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from derive_agora_rules import EPICS_DIR, EPIC_FILE_RE  # noqa: E402
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))
from agy_json import payload_from_envelope  # noqa: E402

PROMPT = REPO / "docs/northstar/spec_factory/prompts/draft_e2e.md"
SCHEMA = REPO / "docs/northstar/spec_factory/schemas/e2e.json"
WRAPPER = REPO / "scripts/agy_task.sh"


def epic_file(epic_id: str) -> Path:
    for p in sorted(EPICS_DIR.iterdir()):
        m = EPIC_FILE_RE.match(p.name)
        if m and m.group(1) == epic_id:
            return p
    sys.exit(f"no epic file for {epic_id}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("epic")
    ap.add_argument("--alg", required=True, help="human-readable ALG id range for the prompt")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    ef = epic_file(args.epic)
    prompt = PROMPT.read_text(encoding="utf-8")
    prompt = (prompt.replace("{{EPIC_ID}}", args.epic)
                    .replace("{{EPIC_FILE}}", str(ef.relative_to(REPO)))
                    .replace("{{ALG_RANGE}}", args.alg))
    args.out.mkdir(parents=True, exist_ok=True)
    prompt_path = args.out / f"{args.epic}_draft_e2e.prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    res = subprocess.run([str(WRAPPER), str(prompt_path), str(SCHEMA)],
                         cwd=REPO, capture_output=True, text=True)
    raw_path = args.out / f"{args.epic}_draft_e2e.raw.json"
    raw_path.write_text(res.stdout, encoding="utf-8")
    if res.returncode != 0:
        sys.stderr.write(res.stderr[-2000:])
        return res.returncode

    payload = payload_from_envelope(res.stdout, ("e2e_markdown", "questions", "assumptions"))
    if payload is None:
        sys.stderr.write(f"unusable agy output; raw saved at {raw_path}\n")
        return 1
    (args.out / f"{args.epic}.md").write_text(payload["e2e_markdown"], encoding="utf-8")
    (args.out / f"{args.epic}_questions.md").write_text(
        "\n".join(f"- {q}" for q in payload["questions"]) + "\n\nAssumptions\n"
        + "\n".join(f"- {a}" for a in payload["assumptions"]) + "\n", encoding="utf-8")
    print(f"draft: {args.out / (args.epic + '.md')}")
    print(f"questions: {len(payload['questions'])}, assumptions: {len(payload['assumptions'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
