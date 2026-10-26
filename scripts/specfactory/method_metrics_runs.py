#!/usr/bin/env python3
# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md "The gaps" G01 G02 G04 G05 G10 G11 G12 G19 G20 G21
"""Method metrics read from runs and transcripts: M01b M03 M06 M06b M07 M07b M08 M08b M13 M13b M14 M14b M15
M21a M21b M22. One function per metric returns (status, value, threshold, numbers); `lines(ctx)` prints them.
Imported by method_metrics.py (mm-1a); `main()` here is a minimal stand-alone entry for the same arguments.
See also: method_metrics.py (git and ledger metrics), method_metrics_cli.py (the CLI)."""
import argparse
import csv
import datetime as dt
import json
import os
import re
import statistics
import subprocess
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import method_check as mc  # noqa: E402
import pieces as pc  # noqa: E402

REPO = HERE.parents[1]
LEDGER_REL = "docs/northstar/plans/push_ledger_2026-09-22.md"
CTX_LIMIT = 400000  # spec G05: assistant calls whose context exceeds 400,000 tokens
ROLES = ("spec", "tests", "build", "land", "audit", "verify", "records", "draft", "review")
GAPS = {"M01b": "G01", "M03": "G02", "M06": "G04", "M06b": "G04", "M07": "G19", "M07b": "G19", "M08": "G05",
        "M08b": "G05", "M13": "G10", "M13b": "G10", "M14": "G11", "M14b": "G11", "M15": "G12", "M21a": "G20",
        "M21b": "G20", "M22": "G21"}
# DRAFT values from the spec, used only when method_thresholds.toml is absent (mm-1a writes it)
FALLBACK = {"M01b": ("<=", 0, "runs"), "M03": ("<=", 2, "rows"), "M06": ("<=", 25, "%"), "M06b": ("<=", 0, "runs"),
            "M07": ("<=", 5, "%"), "M07b": ("<=", 0, "runs"), "M08": ("<=", 0, "calls"), "M08b": ("<=", 0, "turns"),
            "M13": ("<=", 2, "runs"), "M13b": ("<=", 1.0, "ratio"), "M14": ("<=", 4, "runs"),
            "M14b": ("<=", 0, "roles"), "M15": ("<=", 20, "%"), "M21a": ("<=", 1, "rows"),
            "M21b": ("<=", 2, "lines"), "M22": ("<=", 2, "sessions")}
OPS = {"<=": lambda a, b: a <= b, ">=": lambda a, b: a >= b, "<": lambda a, b: a < b, ">": lambda a, b: a > b}


# ---------------------------------------------------------------- context
def week_bounds(week):
    y, w = re.fullmatch(r"(\d{4})-W(\d{2})", week).groups()
    mon = dt.date.fromisocalendar(int(y), int(w), 1)
    return mon, mon + dt.timedelta(days=6)


def week_of_epoch(t):
    y, w, _ = dt.datetime.fromtimestamp(int(t), dt.timezone.utc).isocalendar()
    return "%d-W%02d" % (y, w)


def make_ctx(week, repo=REPO, ledger=None, pieces=None, sdk_runs=None, transcripts=None, thresholds=None, **_):
    repo = Path(repo)
    thr_path = Path(thresholds) if thresholds else HERE / "method_thresholds.toml"
    thr = tomllib.loads(thr_path.read_text()) if thr_path.exists() else None
    if thr is None:
        print("method_metrics_runs: %s absent, using the spec's DRAFT values" % thr_path, file=sys.stderr)
    first, last = week_bounds(week)
    return {"week": week, "first": first, "last": last, "repo": repo,
            "ledger": Path(ledger) if ledger else repo / LEDGER_REL,
            "pieces": {p["id"]: p for p in pc.load_pieces(Path(pieces) if pieces else pc.DEFAULT_PIECES)},
            "sdk": Path(sdk_runs) if sdk_runs else Path("~/Projects/om-push/runs/sdk_runs.csv").expanduser(),
            "gate": None, "transcripts": Path(transcripts) if transcripts else Path("~/.claude/projects").expanduser(),
            "thr": thr}


def in_week(ctx, stamp):
    try:
        return ctx["first"] <= dt.date.fromisoformat(str(stamp)[:10]) <= ctx["last"]
    except ValueError:
        return False


def fmt(v):
    return str(int(v)) if float(v) == int(v) else ("%.2f" % v).rstrip("0").rstrip(".")


def judge(ctx, mid, value, numbers, na=False):
    op, limit, unit = FALLBACK[mid]
    approved = "(draft)"
    row = (ctx["thr"] or {}).get(mid)
    if row:
        op, limit, unit, approved = row["direction"], row["value"], row.get("unit", unit), row.get("approved", "")
    if na or value is None:
        status = "NA"
    elif not approved or approved == "(draft)":
        status = "DRAFT"
    else:
        status = "PASS" if OPS[op](value, limit) else "FAIL"
    if ctx["thr"] is None and status == "PASS":
        status = "DRAFT"
    suffix = "%" if unit == "%" else ""
    return status, (fmt(value) + suffix if value is not None else "-"), "%s%s%s" % (op, fmt(limit), suffix), numbers


# ---------------------------------------------------------------- runs
def top_files(ctx):
    root = ctx["transcripts"]
    start = dt.datetime.combine(ctx["first"], dt.time()).replace(tzinfo=dt.timezone.utc).timestamp()
    for p in sorted(root.rglob("*.jsonl")):
        if p.stat().st_mtime >= start:
            yield p, "subagents" in p.relative_to(root).parts


def raw_entries(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if isinstance(e, dict) and e.get("type") == "assistant":
                yield e


def model_of(e):
    m = (e.get("message") or {}).get("model") or ""
    return "" if m.startswith("<") else m


def meta_runs(ctx):
    out = []
    root = ctx["transcripts"]
    for mp in sorted(root.rglob("agent-*.meta.json")):
        try:
            desc = str(json.loads(mp.read_text()).get("description") or "").split()
        except ValueError:
            continue
        if len(desc) < 2 or desc[1] not in ROLES:
            continue
        jp = mp.with_name(mp.name[:-len(".meta.json")] + ".jsonl")
        model, stamp, result = "", "", "unknown"
        if jp.exists():
            for e in raw_entries(jp):
                model = model or model_of(e)
                stamp = stamp or str(e.get("timestamp") or "")
                for b in (e.get("message") or {}).get("content") or []:
                    m = isinstance(b, dict) and re.search(r"RESULT (success|stop:[\w-]+|error)", b.get("text") or "")
                    if m:
                        result = m.group(1)
        out.append({"label": "%s %s" % (desc[0], desc[1]), "piece": desc[0], "role": desc[1], "model": model,
                    "cost": 0.0, "outcome": result, "date": stamp[:10] or dt.date.fromtimestamp(mp.stat().st_mtime).isoformat()})
    return out


def runs(ctx):
    if "runs" not in ctx:
        rows = []
        if ctx["sdk"].exists():
            with open(ctx["sdk"], newline="") as f:
                for r in csv.DictReader(f):
                    rows.append({"label": r["label"], "piece": r["piece"], "role": r["role"], "model": r["model"],
                                 "cost": float(r["cost"] or 0), "outcome": r["outcome"], "date": r["date"]})
        ctx["runs"] = [r for r in rows + meta_runs(ctx) if in_week(ctx, r["date"])]
    return ctx["runs"]


def landed(ctx):
    """Labels of rc-0 gate rows in the week, comma lists split."""
    if ctx["gate"] is None or not Path(ctx["gate"]).exists():
        return []
    out = []
    with open(ctx["gate"], newline="") as f:
        for r in csv.DictReader(f):
            if str(r["rc"]) == "0" and in_week(ctx, r["date"]):
                out += [x.strip() for x in r["label"].split(",") if x.strip()]
    return list(dict.fromkeys(out))


def contract(ctx, piece):
    return bool((ctx["pieces"].get(piece) or {}).get("contract"))


def names(rs):
    return ", ".join("%s(%s $%s)" % (r["label"], r["model"], fmt(r["cost"])) for r in rs) or "none"


# ---------------------------------------------------------------- metrics
def m01b(ctx):
    bad = [r for r in runs(ctx) if r["role"] == "tests" and (own := ctx["pieces"].get(r["piece"], {}).get("owns"))
           and all(o.startswith(("autoload/", "scenes/")) for o in own)]
    return judge(ctx, "M01b", len(bad), "tests runs on client-only pieces: " + names(bad))


def blame_rows(ctx):
    """(event cell, time cell) of each ledger row whose git blame week on origin/main is this week."""
    rel = os.path.relpath(ctx["ledger"], ctx["repo"])
    out = subprocess.run(["git", "-C", str(ctx["repo"]), "blame", "--line-porcelain", "origin/main", "--", rel],
                         capture_output=True, text=True, check=True).stdout
    rows, when = [], None
    for ln in out.splitlines():
        if ln.startswith("author-time "):
            when = week_of_epoch(ln.split()[1])
        elif ln.startswith("\t"):
            cells = [c.strip() for c in ln[1:].split("|")]
            if when == ctx["week"] and ln[1:].startswith("|") and len(cells) > 2:
                rows.append(cells[2])
    return rows


def m03(ctx):
    td = [e for e in blame_rows(ctx) if e.startswith("TD-")]
    fable = [e for e in td if "ruler=fable" in e]
    return judge(ctx, "M03", len(fable), "TD rows %d, ruler=fable %d: %s" % (
        len(td), len(fable), ", ".join(e.split()[0] for e in fable) or "none"))


def spend(rs):
    return sum(r["cost"] for r in rs)


def m06(ctx):
    rs = runs(ctx)
    total, fable = spend(rs), spend([r for r in rs if "fable" in r["model"].lower()])
    return judge(ctx, "M06", fable / total * 100 if total else None, "fable $%s of $%s" % (fmt(fable), fmt(total)),
                 na=not total)


def m06b(ctx):
    bad = [r for r in runs(ctx) if "fable" in r["model"].lower() and r["role"] in ("draft", "review")
           and not contract(ctx, r["piece"])]
    return judge(ctx, "M06b", len(bad), "Fable draft/review runs on non-contract pieces: " + names(bad))


def m07(ctx):
    rs = runs(ctx)
    total, av = spend(rs), spend([r for r in rs if r["role"] in ("audit", "verify")])
    return judge(ctx, "M07", av / total * 100 if total else None, "audit+verify $%s of $%s" % (fmt(av), fmt(total)),
                 na=not total)


def m07b(ctx):
    bad = [r for r in runs(ctx) if r["role"] == "verify" or (
        r["role"] == "audit" and not contract(ctx, r["piece"]) and "beta" not in r["piece"])]
    return judge(ctx, "M07b", len(bad), "audit (non-contract) and verify runs: " + names(bad))


def m08(ctx):
    n, worst = 0, (0, "", "")
    for p, _ in top_files(ctx):
        for e in raw_entries(p):
            size = mc.ctx_size(e)
            if size > CTX_LIMIT and in_week(ctx, e.get("timestamp") or ""):
                n += 1
                worst = max(worst, (size, p.stem, str(e.get("timestamp"))))
    return judge(ctx, "M08", n, "calls over %d: %d, worst %d tokens, session %s at %s" % (
        CTX_LIMIT, n, worst[0], worst[1], worst[2]))


def session_hits(ctx, drift_rules):
    """{session: {rule: [(timestamp, call)]}} over top-level sessions, hits dated in the week."""
    live = os.path.realpath(os.path.expanduser("~/Projects/ouroboros-manifold"))
    out = {}
    for p, sub in top_files(ctx):
        if sub:
            continue
        es = [e for e in mc.load(p) if e["type"] == "assistant"]
        models = [model_of(e) for e in es if model_of(e)]
        role = mc.role_of([models[-1]] if models else [])
        for cid, roles, kind, _ in mc.CHECKS:
            if kind != "DRIFT" or cid not in drift_rules or (roles != "both" and role != "unknown" and roles != role):
                continue
            hit = None if cid == "context" else mc.matcher(cid, role, live)
            for e in es:
                if not in_week(ctx, e.get("timestamp") or ""):
                    continue
                if cid == "context":
                    if mc.ctx_size(e) > CTX_LIMIT:
                        out.setdefault(p.stem, {}).setdefault(cid, []).append(e["timestamp"])
                elif any(hit(c, e.get("cwd") or "") for c in mc.calls(e)):
                    out.setdefault(p.stem, {}).setdefault(cid, []).append(e["timestamp"])
    return out


def m08b(ctx):
    hits = [(s, t) for s, d in session_hits(ctx, ("polling",)).items() for t in d.get("polling", [])]
    return judge(ctx, "M08b", len(hits), "polling turns %d: %s" % (len(hits), ", ".join("%s %s" % h for h in hits[:3]) or "none"))


def by_piece(ctx):
    rs = runs(ctx)
    return {p: [r for r in rs if r["piece"] == p] for p in landed(ctx)}


def m13(ctx):
    bp = by_piece(ctx)
    lands = {p: [r for r in rs if r["role"] == "land"] for p, rs in bp.items()}
    worst = max(lands.values(), key=len, default=[])
    return judge(ctx, "M13", len(worst) if bp else None, "landing runs per piece: " + (", ".join(
        "%s=%d" % (p, len(v)) for p, v in lands.items()) or "none") + "; " + names(worst), na=not bp)


def m13b(ctx):
    bp = by_piece(ctx)
    land = spend([r for rs in bp.values() for r in rs if r["role"] == "land"])
    build = spend([r for rs in bp.values() for r in rs if r["role"] == "build"])
    return judge(ctx, "M13b", land / build if build else None, "landing $%s vs build $%s over %d landed pieces" % (
        fmt(land), fmt(build), len(bp)), na=not build)


def m14(ctx):
    bp = by_piece(ctx)
    med = statistics.median(len(v) for v in bp.values()) if bp else None
    return judge(ctx, "M14", med, "runs per landed piece: " + (", ".join("%s=%d" % (p, len(v)) for p, v in bp.items()) or "none"),
                 na=not bp)


def m14b(ctx):
    bp = by_piece(ctx)
    extra = {}
    for p, rs in bp.items():
        ok = {"spec", "tests", "build", "land"} | ({"audit"} if contract(ctx, p) else set())
        for r in rs:
            if r["role"] not in ok:
                extra.setdefault(p, set()).add(r["role"])
    return judge(ctx, "M14b", sum(len(v) for v in extra.values()) if bp else None,
                 "extra roles: " + ("; ".join("%s: %s" % (p, ",".join(sorted(v))) for p, v in extra.items()) or "none"),
                 na=not bp)


def m15(ctx):
    rs = runs(ctx)
    stops = [r for r in rs if r["outcome"] in ("stop:spec", "stop:records")]
    return judge(ctx, "M15", len(stops) / len(rs) * 100 if rs else None, "%d stops of %d runs: %s" % (
        len(stops), len(rs), ", ".join("%s %s" % (r["label"], r["outcome"]) for r in stops) or "none"), na=not rs)


def m21a(ctx):
    exc = [e.split()[0] for e in blame_rows(ctx) if e.startswith("EXC-")]
    return judge(ctx, "M21a", len(exc), "EXC rows: " + (", ".join(exc) or "none"))


def m21b(ctx):
    rules = [c[0] for c in mc.CHECKS if c[2] == "DRIFT"]
    lines = [(s, r, len(t)) for s, d in session_hits(ctx, rules).items() for r, t in d.items()]
    return judge(ctx, "M21b", len(lines), "DRIFT lines %d: %s" % (len(lines), ", ".join(
        "%s %s x%d" % l for l in lines) or "none"))


def m22(ctx):
    hours = {}
    for p, sub in top_files(ctx):
        if sub:
            continue
        for e in raw_entries(p):
            stamp = str(e.get("timestamp") or "")
            if in_week(ctx, stamp) and mc.role_of([model_of(e)]) != "unknown":
                hours.setdefault(stamp[:13], set()).add(p.stem)
    hour, ss = max(hours.items(), key=lambda kv: len(kv[1]), default=("-", set()))
    return judge(ctx, "M22", len(ss), "coordinator sessions in hour %s: %s" % (hour, ", ".join(sorted(ss)) or "none"))


METRICS = [m01b, m03, m06, m06b, m07, m07b, m08, m08b, m13, m13b, m14, m14b, m15, m21a, m21b, m22]


def lines(ctx):
    out = []
    for fn in METRICS:
        mid = "M" + fn.__name__[1:]
        status, value, thr, numbers = fn(ctx)
        out.append("METRIC %s %s %s vs %s %s (%s) %s" % (mid, status, value, thr, GAPS[mid], numbers, ctx["week"]))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", required=True)
    ap.add_argument("--phase", default="lab")
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--ledger")
    ap.add_argument("--pieces")
    ap.add_argument("--gate-runs", default="~/Projects/om-push/gate_runs.csv")
    ap.add_argument("--sdk-runs")
    ap.add_argument("--transcripts")
    ap.add_argument("--wt")
    ap.add_argument("--thresholds")
    a, _ = ap.parse_known_args(argv)
    ctx = make_ctx(a.week, a.repo, a.ledger, a.pieces, a.sdk_runs, a.transcripts, a.thresholds)
    ctx["gate"] = Path(a.gate_runs).expanduser()
    out = lines(ctx)
    print("\n".join(out))
    return 1 if any(" FAIL " in l for l in out) else 0


if __name__ == "__main__":
    sys.exit(main())
