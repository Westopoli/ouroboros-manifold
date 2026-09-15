#!/usr/bin/env python3
"""Fill generated test skeletons with agy, one file per call, from the prompt
template in docs/northstar/spec_factory/prompts/fill_tests.md. Filled files
land in --out (a scratch dir), never in tests/csim/; the reviewer runs
red_check.py on them and copies them in.

Usage:
    scripts/specfactory/fill_tests.py E-05 --skeletons DIR --alg "ALG-11 through ALG-25 and ALG-29" --out DIR
    scripts/specfactory/fill_tests.py E-05 --controls --skeletons CTRL_DIR --filled-dir DIR --alg "..." --out CTRL_OUT
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
from budget_gate import require_budget  # noqa: E402

PROMPT_TESTS = REPO / "docs/northstar/spec_factory/prompts/fill_tests.md"
PROMPT_CONTROLS = REPO / "docs/northstar/spec_factory/prompts/fill_controls.md"
SCHEMA = REPO / "docs/northstar/spec_factory/schemas/tests.json"
WRAPPER = REPO / "scripts/agy_task.sh"


def epic_file(epic_id: str) -> Path:
    for p in sorted(EPICS_DIR.iterdir()):
        m = EPIC_FILE_RE.match(p.name)
        if m and m.group(1) == epic_id:
            return p
    sys.exit(f"no epic file for {epic_id}")


def fill_one(epic_id: str, ef: Path, alg: str, skeleton: Path, out: Path,
             prompt_file: Path, filled_dir: Path | None) -> tuple[int, int]:
    prompt = (prompt_file.read_text(encoding="utf-8")
              .replace("{{EPIC_ID}}", epic_id)
              .replace("{{EPIC_FILE}}", str(ef.relative_to(REPO)))
              .replace("{{ALG_RANGE}}", alg)
              .replace("{{SKELETON_FILE}}", str(skeleton))
              .replace("{{FILLED_DIR}}", str(filled_dir) if filled_dir else ""))
    prompt_path = out / (skeleton.stem + ".prompt.md")
    prompt_path.write_text(prompt, encoding="utf-8")
    payload = None
    for attempt in (1, 2):
        res = subprocess.run([str(WRAPPER), str(prompt_path), str(SCHEMA)],
                             cwd=REPO, capture_output=True, text=True)
        (out / (skeleton.stem + f".raw{attempt}.json")).write_text(res.stdout, encoding="utf-8")
        if res.returncode != 0 or not res.stdout.strip():
            sys.stderr.write(f"{skeleton.name}: attempt {attempt} agy exit {res.returncode}, "
                             f"{len(res.stdout)} bytes stdout\n{res.stderr[-1500:]}\n")
            continue
        payload = payload_from_envelope(res.stdout, ("path", "content", "questions", "assumptions"))
        if payload is not None:
            break
        sys.stderr.write(f"{skeleton.name}: attempt {attempt} unusable output; head: {res.stdout[:200]!r}\n")
    if payload is None:
        print(f"FAILED {skeleton.name}: no usable output after 2 attempts", flush=True)
        return 0, 0
    (out / skeleton.name).write_text(payload["content"], encoding="utf-8")
    notes = out / (skeleton.stem + ".notes.md")
    notes.write_text("Questions\n" + "\n".join(f"- {q}" for q in payload["questions"])
                     + "\n\nAssumptions\n" + "\n".join(f"- {a}" for a in payload["assumptions"]) + "\n",
                     encoding="utf-8")
    print(f"filled {skeleton.name}: {len(payload['questions'])} questions, {len(payload['assumptions'])} assumptions", flush=True)
    return len(payload["questions"]), len(payload["assumptions"])


def main() -> int:
    require_budget()
    ap = argparse.ArgumentParser()
    ap.add_argument("epic")
    ap.add_argument("--skeletons", type=Path, required=True)
    ap.add_argument("--alg", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--only", nargs="*", default=None, help="skeleton file names to fill")
    ap.add_argument("--controls", action="store_true", help="use the positive-control prompt")
    ap.add_argument("--filled-dir", type=Path, default=None, help="filled story tests the controls reuse")
    args = ap.parse_args()

    ef = epic_file(args.epic)
    args.out.mkdir(parents=True, exist_ok=True)
    files = sorted(args.skeletons.glob("test_*.py"))
    if args.only:
        files = [f for f in files if f.name in set(args.only)]
    total_q = 0
    for f in files:
        q, _ = fill_one(args.epic, ef, args.alg, f, args.out,
                        PROMPT_CONTROLS if args.controls else PROMPT_TESTS, args.filled_dir)
        total_q += q
    print(f"done: {len(files)} files, {total_q} questions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
