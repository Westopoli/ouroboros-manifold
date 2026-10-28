#!/usr/bin/env python3
# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md "The gaps" G01 G02 G04 G05 G10 G11 G12 G19 G20 G21; audit_findings.md
"""Method metrics read from runs and transcripts: M01b M03 M06 M06b M07 M07b M08 M08b M13 M13b M14 M14b M15
M21a M21b M22. One function per metric returns (status, value, threshold, numbers) through the one `judge` in
method_metrics.py; METRICS maps id to function. Run through method_metrics_cli.py.
See also: method_metrics.py (git and ledger metrics, Context, judge), method_metrics_cli.py (the CLI)."""
import csv
import json
import os
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import method_check as mc  # noqa: E402
from method_metrics import date_epoch, fmt, judge, na  # noqa: E402

CTX_LIMIT = 400000  # spec G05: assistant calls whose context exceeds 400,000 tokens
ROLES = ("spec", "tests", "build", "land", "audit")
BREACH_RULES = ("polling", "gate_runs", "live_tree", "main_push", "wakeups", "spawn_model", "fable_spawns", "messages")
TOKEN_KEYS = (("input_tokens", "input"), ("cache_read_input_tokens", "cache_read"),
              ("cache_creation_input_tokens", "cache_write"), ("output_tokens", "output"))


# ---------------------------------------------------------------- transcripts
def in_window(ctx, stamp, days=7):
    try:
        return ctx.t1 - days * 86400 <= date_epoch(str(stamp)[:10]) < ctx.t1
    except ValueError:
        return False


def project_root(ctx):
    return Path(ctx.transcripts) / ctx.project


def top_files(ctx):
    root = project_root(ctx)
    if root.is_dir():
        for p in sorted(root.rglob("*.jsonl")):
            if p.stat().st_mtime >= ctx.t0:
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


def price_of(ctx, model):
    return next((v for k, v in ctx.prices.items() if model.startswith(k)), None)


def entry_cost(ctx, e):
    """Dollars for one assistant entry: usage tokens times the model's list price per million tokens."""
    price = price_of(ctx, model_of(e))
    usage = (e.get("message") or {}).get("usage") or {}
    if not price:
        return 0.0
    return sum(int(usage.get(k) or 0) * price[p] for k, p in TOKEN_KEYS) / 1e6


def transcript_cost(ctx, path):
    """Cost of a transcript; entries that repeat one message id (one line per content block) count once."""
    by_id, anon = {}, []
    for e in raw_entries(path):
        mid = (e.get("message") or {}).get("id")
        if mid:
            by_id[mid] = e
        else:
            anon.append(e)
    return sum(entry_cost(ctx, e) for e in [*by_id.values(), *anon])


# ---------------------------------------------------------------- runs
def pieces_by_id(ctx):
    return ctx.cached("pieces_by_id", lambda: {p["id"]: p for p in ctx.pieces()})


def meta_runs(ctx):
    """Sub-agent spawns. `<pieces.toml id> <role>` is a labelled run; any other description is an `unlabelled` run."""
    out, pieces = [], pieces_by_id(ctx)
    root = project_root(ctx)
    for mp in sorted(root.rglob("agent-*.meta.json")) if root.is_dir() else []:
        try:
            desc = str(json.loads(mp.read_text()).get("description") or "")
        except ValueError:
            continue
        words = desc.split()
        labelled = len(words) >= 2 and words[0] in pieces and words[1] in ROLES
        jp = mp.with_name(mp.name[:-len(".meta.json")] + ".jsonl")
        model, stamp, result, cost = "", "", "unknown", 0.0
        if jp.exists():
            for e in raw_entries(jp):
                model = model or model_of(e)
                stamp = stamp or str(e.get("timestamp") or "")
                for b in (e.get("message") or {}).get("content") or []:
                    m = isinstance(b, dict) and re.search(r"RESULT (success|stop:[\w-]+|error)", b.get("text") or "")
                    if m:
                        result = m.group(1)
            cost = transcript_cost(ctx, jp)
        out.append({"label": desc, "piece": words[0] if labelled else "", "role": words[1] if labelled else "unlabelled",
                    "model": model, "cost": cost, "outcome": result, "date": stamp[:10]})
    return out


def runs(ctx, days=7):
    def load():
        rows = []
        if ctx.sdk_runs and Path(ctx.sdk_runs).exists():
            with open(ctx.sdk_runs, newline="") as f:
                for r in csv.DictReader(f):
                    rows.append({"label": r["label"], "piece": r["piece"], "role": r["role"], "model": r["model"],
                                 "cost": float(r["cost"] or 0), "outcome": r["outcome"], "date": r["date"]})
        return [r for r in rows + meta_runs(ctx) if in_window(ctx, r["date"], days)]
    return ctx.cached(("runs", days), load)


def landed(ctx):
    """Piece ids of rc-0 gate rows in the week, comma lists split."""
    out = [x.strip() for r in ctx.gate_rows() if r["rc"] == "0" for x in r["label"].split(",") if x.strip()]
    return list(dict.fromkeys(out))


def contract(ctx, piece):
    return bool(pieces_by_id(ctx).get(piece, {}).get("contract"))


def names(rs):
    return ", ".join("%s(%s $%s)" % (r["label"], r["model"], fmt(r["cost"])) for r in rs) or "none"


def spend(rs):
    return sum(r["cost"] for r in rs)


def by_piece(ctx, days=7):
    rs = runs(ctx, days)
    return {p: [r for r in rs if r["piece"] == p] for p in landed(ctx)}


def not_landed(ctx):
    """Runs in the week on labelled pieces that did not land: shown, not judged."""
    done = set(landed(ctx))
    rs = [r for r in runs(ctx) if r["piece"] and r["piece"] not in done]
    return "; not landed this week: %d runs on %d pieces" % (len(rs), len({r["piece"] for r in rs}))


# ---------------------------------------------------------------- metrics
def m01b(ctx):
    pieces, bad = pieces_by_id(ctx), []
    for r in runs(ctx):
        own = [o for o in pieces.get(r["piece"], {}).get("owns", []) if not o.startswith("tests/")]
        if r["role"] == "tests" and own and all(o.startswith(("autoload/", "scenes/")) for o in own):
            bad.append(r)
    return judge(ctx, "M01b", len(bad), "tests runs on client-only pieces: " + names(bad), [r["label"] for r in bad])


def m03(ctx):
    if not ctx.has_ledger():
        return na(ctx, "M03", "no ledger on origin/main")
    td = [e for _, e, _ in ctx.ledger_rows() if e.startswith("TD-")]
    fable = [e for e in td if "ruler=fable" in e]
    return judge(ctx, "M03", len(fable), "TD rows %d, ruler=fable %d: %s" % (
        len(td), len(fable), ", ".join(e.split()[0] for e in fable) or "none"), [e.split()[0] for e in fable])


def m06(ctx):
    rs = runs(ctx)
    total, fable = spend(rs), spend([r for r in rs if "fable" in r["model"].lower()])
    n = "fable $%s of $%s" % (fmt(fable), fmt(total))
    return judge(ctx, "M06", fable / total * 100, n) if total else na(ctx, "M06", n)


def m06b(ctx):
    bad = [r for r in runs(ctx) if "fable" in r["model"].lower() and r["role"] in ("draft", "review")
           and not contract(ctx, r["piece"])]
    return judge(ctx, "M06b", len(bad), "Fable draft/review runs on non-contract pieces: " + names(bad), [r["label"] for r in bad])


def m07(ctx):
    rs = runs(ctx)
    total, av = spend(rs), spend([r for r in rs if r["role"] in ("audit", "verify")])
    n = "audit+verify $%s of $%s" % (fmt(av), fmt(total))
    return judge(ctx, "M07", av / total * 100, n) if total else na(ctx, "M07", n)


def m07b(ctx):
    bad = [r for r in runs(ctx) if r["role"] == "verify" or (
        r["role"] == "audit" and not contract(ctx, r["piece"]) and "beta" not in r["piece"])]
    return judge(ctx, "M07b", len(bad), "audit (non-contract) and verify runs: " + names(bad), [r["label"] for r in bad])


def m08(ctx):
    n, worst = 0, (0, "", "")
    for p, _ in top_files(ctx):
        for e in raw_entries(p):
            size = mc.ctx_size(e)
            if size > CTX_LIMIT and in_window(ctx, e.get("timestamp") or ""):
                n += 1
                worst = max(worst, (size, p.stem, str(e.get("timestamp"))))
    return judge(ctx, "M08", n, "calls over %d: %d, worst %d tokens, session %s at %s" % (
        CTX_LIMIT, n, worst[0], worst[1], worst[2]), [f"{worst[1]} {worst[2]}"])


def session_hits(ctx, drift_rules):
    """{session: {rule: [timestamp]}} over top-level sessions, hits dated in the week."""
    live = os.path.realpath(os.path.expanduser("~/Projects/ouroboros-manifold"))
    out = {}
    for p, sub in top_files(ctx):
        if sub:
            continue
        es = [e for e in mc.load(p) if e["type"] == "assistant"]
        models = [model_of(e) for e in es if model_of(e)]
        role = mc.role_of([models[-1]] if models else [])
        for cid, roles, _, _ in mc.CHECKS:
            if cid not in drift_rules or (roles != "both" and role != "unknown" and roles != role):
                continue
            hit = None if cid == "context" else mc.matcher(cid, role, live)
            for e in es:
                if not in_window(ctx, e.get("timestamp") or ""):
                    continue
                if cid == "context":
                    if mc.ctx_size(e) > CTX_LIMIT:
                        out.setdefault(p.stem, {}).setdefault(cid, []).append(e["timestamp"])
                elif any(hit(c, e.get("cwd") or "") for c in mc.calls(e)):
                    out.setdefault(p.stem, {}).setdefault(cid, []).append(e["timestamp"])
    return out


def m08b(ctx):
    hits = [(s, t) for s, d in session_hits(ctx, ("polling",)).items() for t in d.get("polling", [])]
    return judge(ctx, "M08b", len(hits), "polling turns %d: %s" % (len(hits), ", ".join("%s %s" % h for h in hits[:3]) or "none"),
                 ["%s %s" % h for h in hits])


def m13(ctx):
    bp = by_piece(ctx)
    lands = {p: [r for r in rs if r["role"] == "land"] for p, rs in bp.items()}
    worst = max(lands.values(), key=len, default=[])
    n = "landing runs per piece: " + (", ".join("%s=%d" % (p, len(v)) for p, v in lands.items()) or "none") + \
        "; " + names(worst) + not_landed(ctx)
    return judge(ctx, "M13", len(worst), n, [r["label"] for r in worst]) if bp else na(ctx, "M13", n)


def m13b(ctx):
    bp = by_piece(ctx, 28)
    land = spend([r for rs in bp.values() for r in rs if r["role"] == "land"])
    build = spend([r for rs in bp.values() for r in rs if r["role"] == "build"])
    n = "landing $%s vs build $%s over %d landed pieces, runs of the trailing 28 days" % (fmt(land), fmt(build), len(bp))
    return judge(ctx, "M13b", land / build, n) if build else na(ctx, "M13b", n)


def m14(ctx):
    bp = by_piece(ctx)
    n = "runs per landed piece: " + (", ".join("%s=%d" % (p, len(v)) for p, v in bp.items()) or "none") + not_landed(ctx)
    return judge(ctx, "M14", statistics.median(len(v) for v in bp.values()), n,
                 [f"{p}={len(v)}" for p, v in bp.items()]) if bp else na(ctx, "M14", n)


def m14b(ctx):
    bp, extra = by_piece(ctx), {}
    for p, rs in bp.items():
        ok = set(ROLES[:4]) | ({"audit"} if contract(ctx, p) else set())
        for r in rs:
            if r["role"] not in ok:
                extra.setdefault(p, set()).add(r["role"])
    unl = [r for r in runs(ctx) if r["role"] == "unlabelled"]
    n = "extra roles: " + ("; ".join("%s: %s" % (p, ",".join(sorted(v))) for p, v in extra.items()) or "none") + \
        "; unlabelled runs: %d (%s)" % (len(unl), ", ".join(r["label"] for r in unl) or "none")
    if not bp and not unl:
        return na(ctx, "M14b", n)
    return judge(ctx, "M14b", sum(len(v) for v in extra.values()) + len(unl), n,
                 [f"{p}: {','.join(sorted(v))}" for p, v in extra.items()] + [r["label"] for r in unl])


def m15(ctx):
    rs = runs(ctx)
    stops = [r for r in rs if r["outcome"] in ("stop:spec", "stop:records")]
    unknown = [r for r in rs if r["outcome"] == "unknown"]
    n = "%d stops of %d runs: %s; %d unknown (no RESULT line): %s" % (
        len(stops), len(rs), ", ".join("%s %s" % (r["label"], r["outcome"]) for r in stops) or "none",
        len(unknown), ", ".join(r["label"] for r in unknown) or "none")
    if not rs:
        return na(ctx, "M15", n)
    res = judge(ctx, "M15", len(stops) / len(rs) * 100, n, [f"{r['label']} {r['outcome']}" for r in stops])
    limit = (ctx.thr("M15") or {}).get("max_unknown")
    if res[0] != "FAIL" and limit is not None and len(unknown) / len(rs) * 100 > limit:
        ctx.decisive["M15"] = [r["label"] for r in unknown]
        return "FAIL", *res[1:]
    return res


def m21a(ctx):
    if not ctx.has_ledger():
        return na(ctx, "M21a", "no ledger on origin/main")
    exc = [e.split()[0] for _, e, _ in ctx.ledger_rows() if e.startswith("EXC-")]
    return judge(ctx, "M21a", len(exc), "EXC rows: " + (", ".join(exc) or "none"), exc)


def m21b(ctx):  # the week's DRIFT lines that are breaches; `context` is M08's, `code_edits` is not a worker rule
    lines = [(s, r, len(t)) for s, d in session_hits(ctx, BREACH_RULES).items() for r, t in d.items()]
    return judge(ctx, "M21b", len(lines), "DRIFT lines %d: %s" % (len(lines), ", ".join("%s %s x%d" % l for l in lines) or "none"),
                 ["%s %s x%d" % l for l in lines])


def is_coordinator(ctx, path):
    """A top-level session that spawns (an Agent or SendMessage call in the week) or runs on Fable."""
    for e in raw_entries(path):
        if in_window(ctx, e.get("timestamp") or "") and (
                "fable" in model_of(e).lower() or any(c["name"] in (*mc.AGENT_TOOLS, "SendMessage") for c in mc.calls(e))):
            return True
    return False


def m22(ctx):
    hours = {}
    for p, sub in top_files(ctx):
        if sub or not is_coordinator(ctx, p):
            continue
        for e in raw_entries(p):
            stamp = str(e.get("timestamp") or "")
            if in_window(ctx, stamp) and model_of(e):
                hours.setdefault(stamp[:13], set()).add(p.stem)
    hour, ss = max(hours.items(), key=lambda kv: len(kv[1]), default=("-", set()))
    return judge(ctx, "M22", len(ss), "coordinator sessions in hour %s: %s" % (hour, ", ".join(sorted(ss)) or "none"), sorted(ss))


METRICS = {"M01b": m01b, "M03": m03, "M06": m06, "M06b": m06b, "M07": m07, "M07b": m07b, "M08": m08, "M08b": m08b,
           "M13": m13, "M13b": m13b, "M14": m14, "M14b": m14b, "M15": m15, "M21a": m21a, "M21b": m21b, "M22": m22}
