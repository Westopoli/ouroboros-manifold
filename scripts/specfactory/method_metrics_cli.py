#!/usr/bin/env python3
# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md "Design", G13, G14, G15, A7 (HARNESS-mm-1c)
"""Method metrics entry point: the git/ledger metrics (method_metrics.py), the runs/transcripts metrics
(method_metrics_runs.py) and M16, M17, M18 here; --write, --last, --weeks (the back-test table), --verbose.

method_metrics.py hands its __main__ to main() here (spec A7).
# See also: scripts/specfactory/method_metrics.py and method_metrics_runs.py, whose metrics this module runs
# next to its own.
"""
import datetime as dt
import json
import re
import functools
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import method_metrics as m1a  # noqa: E402
import method_metrics_runs as m1b  # noqa: E402

METRICS_REL = "docs/northstar/plans/method_rev3_2026-10-26/metrics"
VERDICTS_DIR = "docs/northstar/story_reviews/westley"
DECISIONS_REL = VERDICTS_DIR + "/decisions.md"


def _picture_rows(ctx):
    """[(author epoch, line)] of the rows of the README's Picture table (header starting `| Picture |`); a row leaves
    the table on a verdict, so every row is a picture awaiting Westley."""
    rows, inside = [], False
    for at, ln in ctx.blame_rows(m1a.README_REL):
        if ln.lstrip().startswith("| Picture |"):
            inside = True
        elif inside and not ln.lstrip().startswith("|"):
            inside = False
        elif inside and not set(ln.replace("|", "").strip()) <= set("-: "):
            rows.append((at, ln))
    return rows


def _state_of(p):
    s = p.get("status")
    return s.get("state") if isinstance(s, dict) else (str(s).split() or [""])[0]


def _verdict_text(ctx):
    """Lines of the verdict files and decisions.md on origin/main."""
    names = ctx.git("ls-tree", "--name-only", "origin/main", VERDICTS_DIR + "/").splitlines()
    rels = [n for n in names if re.fullmatch(r"verdicts_.*\.md", Path(n).name)] + [DECISIONS_REL]
    return [ln for rel in rels for ln in (ctx.show(rel) or "").splitlines()]


def _landed_recently(ctx):
    done = set()
    for r in ctx.gate_rows(28):
        if r["rc"] == "0":
            done |= {x.strip() for x in r["label"].split(",")}
    return done


def m16(ctx):  # G13 lanes with >= 2 look pieces (attached, or landed in 28 days) and no verdict by piece id
    t = ctx.thr("M16") or {}
    need = t.get("value", 2)
    text = _verdict_text(ctx)
    recent = _landed_recently(ctx)
    bad = []
    for lane in ctx.th.get("lanes", []):
        look = [p["id"] for p in ctx.pieces() if p["id"].startswith(lane) and any(o.startswith("scenes/") for o in p.get("owns", []))
                and (_state_of(p) == "attached" or p["id"] in recent)]
        open_ = [i for i in look if not any(re.search(r"(?<![\w-])" + re.escape(i) + r"(?![\w-])", ln) for ln in text)]
        if len(open_) >= need:
            bad.append(f"{lane}: {len(open_)} look pieces with no verdict ({' '.join(open_)})")
    status = "FAIL" if bad else ("PASS" if t.get("approved") else "DRAFT")
    if bad:
        ctx.decisive["M16"] = bad
    return status, len(bad), ("<=", 0), f"{len(bad)} lanes with >= {need} look pieces and no verdict"


def m17(ctx):  # G14 report only
    sunday = dt.datetime.fromtimestamp(ctx.t1 - 86400, dt.timezone.utc).date()
    rows = _picture_rows(ctx)
    age = max(((sunday - dt.datetime.fromtimestamp(at, dt.timezone.utc).date()).days for at, _ in rows), default=0)
    return "NA", f"{len(rows)} rows, oldest {age} d", ("<=", "-"), "pictures awaiting Westley in the README"


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


@functools.lru_cache(maxsize=None)
def _du_mb(root):
    return int(subprocess.run(["du", "-sm", root], capture_output=True, text=True).stdout.split()[0])


def m18(ctx):  # G15 worktree sprawl
    dirs = _wt_dirs(ctx)
    active = [d for d in dirs if _state(d) == "active"]
    done = [d for d in dirs if (d / ".wt-done").is_file()]
    mb = _du_mb(str(ctx.wt)) if dirs else 0
    old = _stale_branches(ctx)
    res = [
        m1a.judge(ctx, "M18a", len(active), f"{len(active)} active of {len(dirs)} trees", [d.name for d in active]),
        m1a.judge(ctx, "M18b", len(done), f"{len(done)} finished and not reaped", [d.name for d in done]),
        m1a.judge(ctx, "M18c", mb / 1024, f"{mb} MB under wt/", [f"{mb} MB"]),
        m1a.judge(ctx, "M18d", len(old), f"{len(old)} unmerged push branches older than 14 d", [n for _, n in old]),
    ]
    return dict(zip(("M18a", "M18b", "M18c", "M18d"), res))


def collect(a):
    """(ctx, [(id, res)]) over all three modules, sorted by metric number."""
    ctx = m1a.Context(a)
    res = {mid: fn(ctx) for mid, fn in {**m1a.METRICS, **m1b.METRICS}.items()}
    res.update({"M16": m16(ctx), "M17": m17(ctx), **m18(ctx)})
    return ctx, sorted(res.items(), key=lambda kv: (int(kv[0][1:3]), kv[0]))


def emit(ctx, recs):
    """Print each metric's line, then, on a FAIL, its decisive rows (three, or all with --verbose) and, with
    --verbose, the full detail list when the line's was cut."""
    for mid, res in recs:
        line = m1a.render(ctx, mid, res)
        print(line)
        if ctx.verbose and len(str(res[3])) > m1a.DETAIL_CAP:
            print(f"  full: {res[3]}")
        rows = ctx.decisive.get(mid, []) if res[0] == "FAIL" else []
        for r in rows if ctx.verbose else rows[:3]:
            print(f"  {r}"[:None if ctx.verbose else m1a.DETAIL_CAP])


def write(ctx, recs):
    d = Path(ctx.repo) / METRICS_REL
    d.mkdir(parents=True, exist_ok=True)
    ms = []
    for mid, res in recs:
        value, thr = m1a.fields(ctx, mid, res)
        ms.append({"id": mid, "status": res[0], "value": value, "threshold": thr, "line": m1a.render(ctx, mid, res)})
    (d / f"{ctx.week}.json").write_text(json.dumps({"week": ctx.week, "phase": ctx.phase, "metrics": ms}, indent=1) + "\n")
    readme = d / "README.md"
    if not readme.is_file():
        readme.write_text("# Stored metric weeks\n\n| Week | FAIL | DRAFT | NA |\n|---|---|---|---|\n")
    row = "| %s | %s | %d | %d |\n" % (ctx.week, " ".join(m for m, r in recs if r[0] == "FAIL") or "-",
                                       sum(r[0] == "DRAFT" for _, r in recs), sum(r[0] == "NA" for _, r in recs))
    with open(readme, "a") as f:
        f.write(row)


def backtest(a):
    """Markdown table, one row per metric and one column per week; values only, nothing judged."""
    weeks = m1a.week_range(a.weeks)
    cols = {}
    for w in weeks:
        a.week = w
        ctx, recs = collect(a)
        cols[w] = {mid: m1a.fields(ctx, mid, res)[0] or "-" for mid, res in recs}
    ids = sorted({m for c in cols.values() for m in c}, key=lambda m: (int(m[1:3]), m))
    print("| Metric | " + " | ".join(weeks) + " |")
    print("|-|" + "-|" * len(weeks))
    for mid in ids:
        print(f"| {mid} | " + " | ".join(cols[w].get(mid, "-") for w in weeks) + " |")


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
    a = p.parse_args(argv)
    if a.last:
        return last(a)
    if a.weeks:
        backtest(a)
        return 0
    if not a.week:
        today = dt.date.today() - dt.timedelta(days=7)
        a.week = "%d-W%02d" % today.isocalendar()[:2]
    ctx, recs = collect(a)
    emit(ctx, recs)
    if a.write:
        write(ctx, recs)
    return 1 if any(r[0] == "FAIL" for _, r in recs) else 0


if __name__ == "__main__":
    sys.exit(main())
