#!/usr/bin/env python3
"""Build ledger — parse Agora build runs into a performance/quality table.

Reads every ~/Projects/agora/runs/<card>-<ts>/report.md (the build.py report) plus
runs/costs.jsonl, and emits one row per run: outcome, candidates tried, models,
total worker wall seconds, interventions, and DeepSeek cost in that run's window.
The generated table is written between the AUTO markers in
docs/northstar/proving_ground/BUILD_LEDGER.md; notes above/below the markers are
preserved so a human can annotate findings.

Usage: scripts/build_ledger.py [--runs DIR] [--out FILE]
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

AGORA_RUNS = Path.home() / "Projects" / "agora" / "runs"
COSTS = AGORA_RUNS / "costs.jsonl"
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "docs" / "northstar" / "proving_ground" / "BUILD_LEDGER.md"

TITLE_RE = re.compile(r"^#\s+(\S+)\s+—\s+(\w[\w-]*)", re.M)
ROW_RE = re.compile(r"^\|\s*\d+\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|"
                    r"\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([^|]*?)\s*\|\s*[0-9a-f]*\s*\|\s*([\d.]+)\s*\|", re.M)
RUN_DIR_RE = re.compile(r"^(.*)-(\d{8})-(\d{4})(?:-\d+)?$")


def cost_in_window(start: datetime, end: datetime) -> tuple[int, float]:
    if not COSTS.exists():
        return 0, 0.0
    calls, usd = 0, 0.0
    for line in COSTS.read_text().splitlines():
        try:
            row = json.loads(line)
            ts = datetime.fromisoformat(row["ts"]).replace(tzinfo=None)
        except Exception:
            continue
        if start <= ts <= end:
            calls += 1
            usd += float(row.get("usd", 0.0))
    return calls, usd


def parse_run(run_dir: Path) -> dict | None:
    report = run_dir / "report.md"
    if not report.exists():
        return None
    text = report.read_text()
    m = TITLE_RE.search(text)
    if not m:
        return None
    card, outcome = m.group(1), m.group(2)
    rows = ROW_RE.findall(text)
    models = sorted({r[1] for r in rows})
    total_wall = sum(float(r[6]) for r in rows)
    best_pass = max((int(r[3]) for r in rows), default=0)
    total_tests = max((int(r[3]) + int(r[4]) for r in rows), default=0)
    interventions = text.count("\n- reset:") + text.count("\n- hint:") + text.count("\n- abort:")

    dm = RUN_DIR_RE.match(run_dir.name)
    when = ""
    calls, usd = 0, 0.0
    if dm:
        try:
            start = datetime.strptime(dm.group(2) + dm.group(3), "%Y%m%d%H%M")
            end = start.replace(minute=59, hour=(start.hour + 1) % 24)
            when = start.strftime("%Y-%m-%d %H:%M")
            calls, usd = cost_in_window(start, end)
        except ValueError:
            pass

    return {
        "run": run_dir.name, "card": card, "when": when, "outcome": outcome,
        "candidates": len(rows), "models": ", ".join(models) or "-",
        "wall_s": round(total_wall, 1), "best": f"{best_pass}/{total_tests}" if total_tests else "-",
        "interventions": interventions, "ds_calls": calls, "usd": round(usd, 4),
    }


def render(runs: list[dict]) -> str:
    head = ("| Run | When | Outcome | Cands | Best | Models | Wall s | Intervs | DS calls | USD |\n"
            "|---|---|---|---|---|---|---|---|---|---|\n")
    body = "".join(
        f"| {r['run']} | {r['when']} | **{r['outcome']}** | {r['candidates']} | {r['best']} | "
        f"{r['models']} | {r['wall_s']} | {r['interventions']} | {r['ds_calls']} | {r['usd']} |\n"
        for r in runs)
    return head + body


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(AGORA_RUNS))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    runs_dir = Path(args.runs)
    runs = []
    for d in sorted(runs_dir.glob("[0-9]*-*")):
        if d.is_dir():
            row = parse_run(d)
            if row:
                runs.append(row)
    runs.sort(key=lambda r: r["run"])

    table = render(runs)
    out = Path(args.out)
    marker_a, marker_b = "<!-- AUTO:BEGIN -->", "<!-- AUTO:END -->"
    if out.exists():
        text = out.read_text()
        if marker_a in text and marker_b in text:
            pre = text.split(marker_a)[0]
            post = text.split(marker_b)[1]
            out.write_text(f"{pre}{marker_a}\n{table}{marker_b}{post}")
        else:
            out.write_text(text.rstrip() + f"\n\n{marker_a}\n{table}{marker_b}\n")
    else:
        out.write_text(f"# Build ledger (auto-generated table below)\n\n{marker_a}\n{table}{marker_b}\n")
    print(f"wrote {len(runs)} run rows to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
