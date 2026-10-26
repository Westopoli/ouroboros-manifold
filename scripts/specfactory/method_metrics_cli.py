#!/usr/bin/env python3
# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md "Design", G13, G14, G15, A7 (HARNESS-mm-1c)
"""Method metrics entry point: mm-1a (git/ledger) + mm-1b (runs/transcripts) + M16, M17, M18, --write, --last.

method_metrics.py hands its __main__ to main() here (spec A7).
# See also: scripts/specfactory/method_metrics.py (mm-1a) and method_metrics_runs.py (mm-1b), whose metrics
# this module runs next to its own.
"""
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import method_metrics as m1a  # noqa: E402
import method_metrics_runs as m1b  # noqa: E402

METRICS_REL = "docs/northstar/plans/method_rev3_2026-10-26/metrics"
DECISIONS_REL = "docs/northstar/story_reviews/westley/decisions.md"
LINE = re.compile(r"^METRIC (\S+) (PASS|FAIL|DRAFT|NA) (.*) vs (\S+) (\S*) \((.*)\) (\S+)$")


def _readme_rows(ctx):
    """[(author epoch, verdict cell, line)] of the Westley README's table rows."""
    out = []
    for at, ln in ctx.blame_rows(m1a.README_REL):
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if ln.lstrip().startswith("|") and len(cells) >= 2 and not set(cells[0]) <= set("-: ") and cells[0] != "File":
            out.append((at, cells[1], ln))
    return out


def _state_of(p):
    s = p.get("status")
    return s.get("state") if isinstance(s, dict) else (str(s).split() or [""])[0]


def m16(ctx):  # G13 lanes with >= 2 attached look pieces and no verdict row
    t = ctx.thr("M16") or {}
    need = t.get("value", 2)
    verdicts = [ln for _, v, ln in _readme_rows(ctx) if v and "awaiting" not in v.lower()]
    verdicts += (ctx.show(DECISIONS_REL) or "").splitlines()
    bad = []
    for lane in ctx.th.get("lanes", []):
        look = [p["id"] for p in ctx.pieces() if p["id"].startswith(lane) and _state_of(p) == "attached"
                and any(o.startswith("scenes/") for o in p.get("owns", []))]
        if len(look) >= need and not any(lane in v for v in verdicts):
            bad.append(f"{lane}: {len(look)} attached look pieces, 0 verdicts ({' '.join(look)})")
    status = "FAIL" if bad else ("PASS" if t.get("approved") else "DRAFT")
    if bad:
        ctx.decisive["M16"] = bad
    return status, len(bad), ("<=", 0), f"{len(bad)} lanes with >= {need} look pieces and no verdict"


def m17(ctx):  # G14 report only
    sunday = dt.datetime.fromtimestamp(ctx.t1 - 86400, dt.timezone.utc).date()
    rows = [(at, ln) for at, v, ln in _readme_rows(ctx) if not v or "awaiting" in v.lower()]
    age = max(((sunday - dt.datetime.fromtimestamp(at, dt.timezone.utc).date()).days for at, _ in rows), default=0)
    return "NA", f"{len(rows)} rows, oldest {age} d", ("<=", "-"), "Westley README rows awaiting a verdict"


def _wt_dirs(ctx):
    root = Path(ctx.wt)
    return sorted(d for d in root.iterdir() if d.is_dir()) if root.is_dir() else []


def _state(d):
    f = d / ".wt-state"
    return (f.read_text().split() or [""])[0] if f.is_file() else ""


def _stale_branches(ctx):
    merged = {x.strip() for x in ctx.git("branch", "-r", "--merged", "origin/main").splitlines()}
    out = ctx.git("for-each-ref", "--format=%(refname:short) %(committerdate:unix)", "refs/remotes/origin/push/")
    old = [(int(at), n) for n, at in (x.split() for x in out.splitlines())
           if n not in merged and int(at) < ctx.t1 - 14 * 86400]
    return sorted(old)


def m18(ctx):  # G15 worktree sprawl
    dirs = _wt_dirs(ctx)
    active = [d for d in dirs if _state(d) == "active"]
    done = [d for d in dirs if (d / ".wt-done").is_file()]
    mb = int(subprocess.run(["du", "-sm", str(ctx.wt)], capture_output=True, text=True).stdout.split()[0]) if dirs else 0
    old = _stale_branches(ctx)
    res = [
        m1a.judge(ctx, "M18a", len(active), f"{len(active)} active of {len(dirs)} trees", [d.name for d in active]),
        m1a.judge(ctx, "M18b", len(done), f"{len(done)} finished and not reaped", [d.name for d in done]),
        m1a.judge(ctx, "M18c", mb / 1024, f"{mb} MB under wt/", [f"{mb} MB"]),
        m1a.judge(ctx, "M18d", len(old), f"{len(old)} unmerged push branches older than 14 d", [n for _, n in old]),
    ]
    return dict(zip(("M18a", "M18b", "M18c", "M18d"), res))


def collect(a):
    """[(id, status, value, line, decisive rows)] over all three modules."""
    ctx = m1a.Context(a)
    out = []
    for mid, fn in m1a.METRICS.items():
        res = fn(ctx)
        out.append((mid, res, ctx.decisive.get(mid, [])))
    extra = {"M16": m16(ctx), "M17": m17(ctx), **m18(ctx)}
    out += [(mid, res, ctx.decisive.get(mid, [])) for mid, res in extra.items()]
    recs = [(mid, res[0], m1a.render(ctx, mid, res), rows) for mid, res, rows in out]
    c2 = m1b.make_ctx(a.week, a.repo, a.ledger, a.pieces, a.sdk_runs, a.transcripts, a.thresholds)
    c2["gate"] = Path(a.gate_runs).expanduser()
    for ln in m1b.lines(c2):
        m = LINE.match(ln)
        recs.append((m.group(1), m.group(2), ln, []))
    for mid in filter(None, a.baseline.split(",")):
        base = (ctx.thr(mid) or {}).get("baseline", "")
        if base == "":
            continue
        res = m1a.judge(ctx, mid, base, "baseline W43 from the spec, no records for the week")
        recs = [r for r in recs if r[0] != mid] + [(mid, res[0], m1a.render(ctx, mid, res), ctx.decisive.get(mid, []))]
    recs.sort(key=lambda r: (int(r[0][1:3]), r[0]))
    return recs


def write(a, recs):
    d = Path(a.repo) / METRICS_REL
    d.mkdir(parents=True, exist_ok=True)
    ms = []
    for mid, status, ln, _ in recs:
        m = LINE.match(ln)
        ms.append({"id": mid, "status": status, "value": m.group(3), "threshold": m.group(4), "line": ln})
    (d / f"{a.week}.json").write_text(json.dumps({"week": a.week, "metrics": ms}, indent=1) + "\n")
    readme = d / "README.md"
    if not readme.is_file():
        readme.write_text("# Stored metric weeks\n\n| Week | FAIL | DRAFT | NA |\n|---|---|---|---|\n")
    row = "| %s | %s | %d | %d |\n" % (a.week, " ".join(r[0] for r in recs if r[1] == "FAIL") or "-",
                                       sum(r[1] == "DRAFT" for r in recs), sum(r[1] == "NA" for r in recs))
    with open(readme, "a") as f:
        f.write(row)


def last(a):
    files = sorted((Path(a.repo) / METRICS_REL).glob("*-W[0-9][0-9].json"))
    if not files:
        print("no stored metrics week")
        return 0
    for m in json.loads(files[-1].read_text())["metrics"]:
        if m["status"] == "FAIL":
            print(m["line"])
    return 0


def main(argv=None):
    p = m1a.parser()
    p.add_argument("--write", action="store_true")
    p.add_argument("--last", action="store_true")
    p.add_argument("--baseline", default="", help="comma list of ids to take from the toml baseline (W43 snapshot only)")
    a, _ = p.parse_known_args(argv)
    if a.last:
        return last(a)
    if not a.week:
        today = dt.date.today() - dt.timedelta(days=7)
        a.week = "%d-W%02d" % today.isocalendar()[:2]
    recs = collect(a)
    for _, _, ln, rows in recs:
        print(ln)
        for r in rows[:3]:
            print(f"  {r}")
    if a.write:
        write(a, recs)
    return 1 if any(r[1] == "FAIL" for r in recs) else 0


if __name__ == "__main__":
    sys.exit(main())
