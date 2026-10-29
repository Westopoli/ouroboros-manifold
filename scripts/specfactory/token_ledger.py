#!/usr/bin/env python3
# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md Amendment A10, A14 (HARNESS-mm-12)
"""Token ledger: per day and per piece, planned tokens (a plan CSV: date,piece,role,estimate_m) against actual
transcript usage, and the week's running total against the allotment (method_thresholds.toml M26).

Tokens of an entry = input + cache read + cache write + output, cache reads at face value, in millions. A run is a
sub-agent transcript whose `.meta.json` description is `<piece> <role>`; a top-level session counts as coordinator.
  token_ledger.py --day 2026-11-02 --plan plan.csv
  token_ledger.py --week 2026-W45
# See also: scripts/specfactory/method_metrics_runs.py (the loader and the metrics M25 to M29 that read the same tokens).
"""
import argparse
import csv
import datetime as dt
import json
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import method_metrics_runs as mr  # noqa: E402
from method_metrics import SLUG, fmt  # noqa: E402

DEFAULT_THRESHOLDS = Path(__file__).with_name("method_thresholds.toml")


def days_of(a):
    if a.day:
        return [a.day]
    y, w = a.week.split("-W")
    mon = dt.date.fromisocalendar(int(y), int(w), 1)
    return [(mon + dt.timedelta(days=i)).isoformat() for i in range(7)]


def usage(a, days):
    """(runs {(day, piece, role): M}, top {(day, 'dispatcher'|'other'): M}) over the days."""
    ctx = SimpleNamespace(transcripts=a.transcripts, project=a.project, t0=0)
    runs, top = {}, {}
    for p, sub in mr.top_files(ctx):
        if sub:
            words = ""
            mp = p.with_name(p.stem + ".meta.json")
            if mp.is_file():
                words = str(json.loads(mp.read_text()).get("description") or "")
            piece, _, role = words.partition(" ")
        for e in mr.dedup_entries(p):
            day = str(e.get("timestamp") or "")[:10]
            if day not in days:
                continue
            m = mr.entry_tokens(e)
            if sub:
                k = (day, piece, role.split()[0] if role else "")
                runs[k] = runs.get(k, 0.0) + m
            else:
                k = (day, "dispatcher" if "sonnet" in mr.model_of(e).lower() else "other")
                top[k] = top.get(k, 0.0) + m
    return runs, top


def plan_rows(a, days):
    if not a.plan:
        return []
    with open(a.plan, newline="") as f:
        return [(r["date"], r["piece"], r["role"], float(r["estimate_m"])) for r in csv.DictReader(f) if r["date"] in days]


def report(a):
    days = days_of(a)
    runs, top = usage(a, days)
    plan = plan_rows(a, days)
    planned = {(d, p, r) for d, p, r, _ in plan}
    for d, p, r, est in plan:
        got = runs.get((d, p, r), 0.0)
        print("%s %s %s plan %s M actual %s M %s" % (d, p, r, fmt(est), fmt(got), "over" if got > est else "under"))
    rest = sum(v for k, v in runs.items() if k not in planned)
    if a.day or plan:
        print("unplanned runs %s M" % fmt(rest))
    coordinator = sum(top.values())
    if a.day:
        print("coordinator sessions %s M" % fmt(coordinator))
    pieces = sum(runs.values())
    print("total %s M of %s M" % (fmt(pieces + coordinator), allotment(a, days)))
    if a.week:
        th = tomllib.loads(Path(a.thresholds).read_text()).get("M26", {})
        n = len(days)
        for word, key, got in (("dispatcher", "dispatcher_m", sum(v for k, v in top.items() if k[1] == "dispatcher")),
                               ("pieces", "pieces_m", pieces),
                               ("reserve", "reserve_m", sum(v for k, v in top.items() if k[1] == "other"))):
            per = th.get(key, "-")
            print("%s: allotment %s M a day, %s M a week; actual %s M" % (word, per, per * 5 if per != "-" else "-", fmt(got)))
        for d in days:
            day = sum(v for k, v in runs.items() if k[0] == d) + sum(v for k, v in top.items() if k[0] == d)
            if day:
                print("day %s %s M" % (d, fmt(day)))


def allotment(a, days):
    if not a.week:
        return "-"
    return fmt(tomllib.loads(Path(a.thresholds).read_text()).get("M26", {}).get("value", "-"))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--day")
    g.add_argument("--week")
    p.add_argument("--plan")
    p.add_argument("--transcripts", default=str(Path.home() / ".claude" / "projects"))
    p.add_argument("--project", default=SLUG)
    p.add_argument("--thresholds", default=str(DEFAULT_THRESHOLDS))
    argv = list(sys.argv[1:] if argv is None else argv)
    for i, x in enumerate(argv[:-1]):  # a slug begins with `-`, which argparse reads as a flag
        if x == "--project":
            argv[i:i + 2] = ["--project=" + argv[i + 1]]
            break
    report(p.parse_args(argv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
