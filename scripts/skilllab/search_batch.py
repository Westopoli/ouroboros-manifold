"""The ping search batch (Stage A): settings x seeker policies x placements, one csv row per run, a run file and a page.
Spec: docs/northstar/plans/2026-10-05-ping-search-spec.md, "The batch".
Rows are written as results arrive, in job order whatever the worker count; the parent keeps only the aggregates."""
import argparse
import csv
import dataclasses
import datetime
import html
import itertools
import math
import multiprocessing
import statistics
from pathlib import Path

from scripts.skilllab import search as S
from scripts.skilllab.search_policies import HIDER_SCRIPTS

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "docs/northstar/research/layer_dynamics/runs"

REACH_TIMES_SIGHT = (1.5, 2.0, 3.0)         # provisional (lab draft, 2026-10-05)
RADII = (250.0, 500.0, 1000.0)              # provisional (lab draft, 2026-10-05)
COOLDOWNS = (100, 200, 400, 800)            # provisional (lab draft, 2026-10-05)
REVEAL_TICKS = 100                          # provisional (lab draft, 2026-10-05)
FORCE = 16                                  # provisional (lab draft, 2026-10-05)
N_PLACEMENTS = 60                           # provisional (lab draft, 2026-10-05)
SEED = 1                                    # provisional (lab draft, 2026-10-05)
POLICY_ORDER = ("ahead", "sweep", "reactive", "none")
SMOKE_SETTINGS = ((2.0, 500.0, 100), (2.0, 500.0, 800))
SMOKE_PLACEMENTS = 6
COLOURS = {"ahead": ("#2f5fb3", "#7fa8f0"), "sweep": ("#b36a1f", "#e8a35c"),
           "reactive": ("#2a7f62", "#58c9a1"), "none": ("#8a8578", "#9c978c")}
NOT_EXPRESSED = (
    ("The \"likely places\" policy", "it needs terrain to say where a hider would sit, and the scene is open ground."),
    ("The hider's decoy", "the hider only moves and changes layer; it has no way to put out a false picture."),
    ("Stage B (what knowing is worth)", "nobody fires here, so what the picture is worth in a fight is not measured."),
    ("Both sides pinging at once (the detection ratio)", "the hider side is on policy none; the ratio needs both casting."),
)
HEADER = ("Every number here is a provisional lab draft. The alert is off, every unit casts, and the reveal follows "
          "units for reveal_ticks.")

_engine = None


def grid(sight):
    return [S.SearchSetting(radius=r, reach=x * sight, reveal_ticks=REVEAL_TICKS, cooldown_ticks=c, force=FORCE)
            for x in REACH_TIMES_SIGHT for r in RADII for c in COOLDOWNS]


def _vanguard_sight():
    from scripts.skilllab.engine import Engine
    e = Engine()
    w = e.new_world(0)
    try:
        return e.type_stats(w, S.VANGUARD)["sensor_radius"]
    finally:
        e.free_world(w)


def _init_worker(path):
    global _engine
    from scripts.skilllab.engine import Engine
    _engine = Engine(path)


def _job(job):
    global _engine
    if _engine is None:
        from scripts.skilllab.engine import Engine
        _engine = Engine()
    setting, policy, placement, seed = job
    return S.run_search(setting, policy, "none", placement, seed, engine=_engine)


def _fields(cls, prefix=""):
    return [prefix + f.name for f in dataclasses.fields(cls)]


def _header():
    return (_fields(S.SearchSetting) + ["coverage_rate", "policy", "placement"] + _fields(S.Placement)
            + ["ended", "contact_tick"] + _fields(S.SideResult, "seeker_") + _fields(S.SideResult, "hider_"))


def _row(setting, policy, i, placement, res):
    side = [dataclasses.astuple(r) for r in res.side]
    return ([repr(v) if isinstance(v, float) else v for v in dataclasses.astuple(setting)]
            + [repr(S.coverage_rate(setting)), policy, i]
            + [repr(v) if isinstance(v, float) else v for v in dataclasses.astuple(placement)]
            + [res.ended, "" if res.contact_tick is None else res.contact_tick]
            + [("" if v is None else v) for t in side for v in t])


def _stats(runs):
    """runs: list of (SideResult of the seeker, Placement, ended)."""
    n = len(runs)
    found = [r for r, *_ in runs if r.found_before_contact]
    warn = [r.warning_ticks for r in found]
    ages = [r.picture_age_ticks for r in found if r.picture_age_ticks is not None]
    cast, hit = sum(r.pings_cast for r, *_ in runs), sum(r.pings_found for r, *_ in runs)
    return {"n": n, "found": len(found) / n, "warn": statistics.median(warn) if warn else None,
            "share": sum(r.share_revealed for r, *_ in runs) / n,
            "age": sum(ages) / len(ages) if ages else None, "per_find": cast / hit if hit else None}


def run_search_batch(settings, policies, n_placements, seed, workers, out_dir=None, name="search"):
    if workers < 1:
        raise ValueError("workers must be at least 1")
    settings = list(settings)
    policies = list(policies)
    sight = _vanguard_sight()
    places = S.placements(seed, n_placements, sight, max(s.reach for s in settings))
    jobs = [(st, p, pl, seed + i) for st in settings for p in policies for i, pl in enumerate(places)]
    index = [i for _ in settings for _ in policies for i in range(len(places))]
    out = Path(out_dir) if out_dir is not None else RUNS / (datetime.date.today().isoformat() + "_" + name)
    out.mkdir(parents=True, exist_ok=True)
    paths = {"csv": out / (name + ".csv"), "run": out / (name + "_run.md"),
             "page": out / (name + "_page.html"), "summary": out / "summary.txt"}
    groups = {}
    pool = None
    if workers == 1:
        results = map(_job, jobs)
    else:
        from scripts.skilllab import engine as engine_module
        pool = multiprocessing.get_context("spawn").Pool(
            workers, initializer=_init_worker, initargs=(engine_module._cached_library(),))
        results = pool.imap(_job, jobs, chunksize=4)
    try:
        with open(paths["csv"], "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(_header())
            for (st, p, pl, _), i, res in zip(jobs, index, results):
                w.writerow(_row(st, p, i, pl, res))
                groups.setdefault((st, p), []).append((res.side[0], pl, res.ended))
    finally:
        if pool is not None:
            pool.close()
            pool.join()
    _write_outputs(paths, settings, policies, groups, name, n_placements, sight)
    return paths


def _write_outputs(paths, settings, policies, groups, name, n_placements, sight):
    data = _aggregate(settings, policies, groups)
    paths["run"].write_text(_run_file(data, name, n_placements, sight), encoding="utf-8")
    paths["page"].write_text(_page(data, name, n_placements, sight), encoding="utf-8")
    paths["summary"].write_text(_summary(data), encoding="utf-8")


def _typed(cls, row, prefix=""):
    kw = {}
    for f in dataclasses.fields(cls):
        v = row[prefix + f.name]
        t = str(f.type)
        if v == "":
            kw[f.name] = None
        elif "float" in t:
            kw[f.name] = float(v)
        elif "int" in t:
            kw[f.name] = int(v)
        elif "bool" in t:
            kw[f.name] = v == "True"
        else:
            kw[f.name] = v
    return cls(**kw)


def _read_csv(path):
    """The inverse of the csv writer: (settings, policies, placements per cell, groups), in file order."""
    settings, policies, groups = [], [], {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            st = _typed(S.SearchSetting, row)
            p = row["policy"]
            if st not in settings:
                settings.append(st)
            if p not in policies:
                policies.append(p)
            groups.setdefault((st, p), []).append(
                (_typed(S.SideResult, row, "seeker_"), _typed(S.Placement, row), row["ended"]))
    return settings, policies, max(len(g) for g in groups.values()), groups


def rebuild_from_csv(csv_path, out_dir, name):
    csv_path = Path(csv_path)
    settings, policies, n_placements, groups = _read_csv(csv_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {"csv": csv_path, "run": out / (name + "_run.md"), "page": out / (name + "_page.html"),
             "summary": out / "summary.txt"}
    _write_outputs(paths, settings, policies, groups, name, n_placements, _vanguard_sight())
    return paths


def _aggregate(settings, policies, groups):
    cells, spread, by_script, by_layer, why = {}, {}, {}, {}, {}
    for st in settings:
        for p in policies:
            cells[(st, p)] = _stats(groups[(st, p)])
        if "ahead" in policies:
            best = max(cells[(st, p)]["found"] for p in policies)
            spread[st] = best - cells[(st, "ahead")]["found"]
    for p in policies:
        pooled = list(itertools.chain.from_iterable(groups[(st, p)] for st in settings))
        for key in HIDER_SCRIPTS:
            sub = [x for x in pooled if x[1].script == key]
            if sub:
                by_script[(p, key)] = _stats(sub)["found"]
        for key, test in (("same layer", lambda pl: pl.layer == S.SEEKER_LAYER),
                          ("other layer", lambda pl: pl.layer != S.SEEKER_LAYER)):
            sub = [x for x in pooled if test(x[1])]
            if sub:
                by_layer[(p, key)] = _stats(sub)["found"]
    for p in policies:
        for st in settings:
            for side, pl, ended in groups[(st, p)]:
                k = (p, "same layer" if pl.layer == S.SEEKER_LAYER else "other layer",
                     "within reach" if math.hypot(pl.dx, pl.dy) <= st.reach else "beyond reach")
                c = why.setdefault(k, {"runs": 0, "missed": 0, "cap": 0, "contact": 0})
                c["runs"] += 1
                if not side.found_before_contact:
                    c["missed"] += 1
                    c[ended] += 1
    return {"settings": settings, "policies": policies, "cells": cells, "spread": spread,
            "by_script": by_script, "by_layer": by_layer, "why": why}


def _f(v, nd=2):
    return "-" if v is None else ("%.*f" % (nd, v))


def _label(st):
    return "reach %g, radius %g, cooldown %d" % (st.reach, st.radius, st.cooldown_ticks)


def _cell_rows(data):
    rows = []
    for st in data["settings"]:
        for p in data["policies"]:
            c = data["cells"][(st, p)]
            w = c["warn"]
            rows.append([_label(st), p, _f(S.coverage_rate(st), 3), _f(c["found"]), _f(w, 0),
                         _f(None if w is None else w / S.TICKS_PER_SECOND, 1), _f(c["share"]), _f(c["age"], 0),
                         _f(c["per_find"], 1)])
    return rows


CELL_HEAD = ["setting", "policy", "coverage rate", "found before contact", "median warning (ticks)",
             "median warning (s)", "mean share revealed", "mean picture age (ticks)", "pings per find"]


def _tables(data):
    """(title, head, rows) in page order, shared by the run file and the page."""
    pol = data["policies"]
    t = [("Per setting and policy", CELL_HEAD, _cell_rows(data))]
    if data["spread"]:
        t.append(("Policy spread (best policy's found rate minus ahead's)", ["setting", "spread"],
                  [[_label(st), _f(v)] for st, v in data["spread"].items()]))
    t.append(("Found rate by hider script", ["policy"] + list(HIDER_SCRIPTS),
              [[p] + [_f(data["by_script"].get((p, k))) for k in HIDER_SCRIPTS] for p in pol]))
    t.append(("Found rate by hider layer", ["policy", "same layer", "other layer"],
              [[p, _f(data["by_layer"].get((p, "same layer"))), _f(data["by_layer"].get((p, "other layer")))]
               for p in pol]))
    why = data["why"]
    t.append(("Why not found (runs where the seeker never found the hider before contact; start distance is the hider's at the start, against ping reach)",
              ["policy", "hider layer", "start distance", "runs", "not found", "ended at the cap, no contact, no find",
               "ended in contact, no earlier find"],
              [[p, lay, dist, why[(p, lay, dist)]["runs"], why[(p, lay, dist)]["missed"], why[(p, lay, dist)]["cap"],
                why[(p, lay, dist)]["contact"]]
               for p in pol for lay in ("same layer", "other layer") for dist in ("within reach", "beyond reach")
               if (p, lay, dist) in why]))
    if "reactive" in pol and "sweep" in pol:
        t.append(("Reactive against sweep (found rates are equal by construction)",
                  ["setting", "sweep: mean picture age (ticks)", "reactive: mean picture age (ticks)",
                   "sweep: pings per find", "reactive: pings per find"],
                  [[_label(st), _f(data["cells"][(st, "sweep")]["age"], 0), _f(data["cells"][(st, "reactive")]["age"], 0),
                    _f(data["cells"][(st, "sweep")]["per_find"], 1), _f(data["cells"][(st, "reactive")]["per_find"], 1)]
                   for st in data["settings"]]))
    return t


def _run_file(data, name, n, sight):
    out = ["# Ping search batch: %s" % name, "", HEADER, "",
           "Vanguard sight %g wu; %d placements per setting and policy; %d settings; policies %s." % (
               sight, n, len(data["settings"]), ", ".join(data["policies"])), ""]
    for title, head, rows in _tables(data):
        out += ["## " + title, "", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
        out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows] + [""]
    out += ["## What the instrument could not express", ""] + ["- %s: %s" % x for x in NOT_EXPRESSED] + [""]
    return "\n".join(out)


def _summary(data):
    return "\n".join("%s | %s | found %s" % (_label(st), p, _f(c["found"], 3))
                     for (st, p), c in data["cells"].items()) + "\n"


def _table_html(head, rows):
    esc = html.escape
    return ("<table>\n<tr>" + "".join("<th>%s</th>" % esc(h) for h in head) + "</tr>\n"
            + "".join("<tr>" + "".join("<td>%s</td>" % esc(str(c)) for c in r) + "</tr>\n" for r in rows) + "</table>\n")


def _chart(data):
    W, H, L, R, T, B = 640, 340, 56, 110, 20, 44
    xs = [S.coverage_rate(st) for st in data["settings"]]
    lo, hi = math.log10(min(xs)), math.log10(max(xs))
    if hi - lo < 1e-9:
        lo, hi = lo - 0.5, hi + 0.5
    px = lambda v: L + (math.log10(v) - lo) / (hi - lo) * (W - L - R)
    py = lambda v: T + (1 - v) * (H - T - B)
    o = ['<svg viewBox="0 0 %d %d" role="img" aria-label="Found before contact against coverage rate">' % (W, H)]
    for k in range(5):
        y = py(k / 4)
        o.append('<line class="grid" x1="%d" x2="%d" y1="%.1f" y2="%.1f"/>' % (L, W - R, y, y))
        o.append('<text x="%d" y="%.1f" text-anchor="end" class="muted">%.2f</text>' % (L - 6, y + 4, k / 4))
    for e in range(math.ceil(lo), math.floor(hi) + 1):
        x = px(10 ** e)
        o.append('<line class="grid" x1="%.1f" x2="%.1f" y1="%d" y2="%d"/>' % (x, x, T, H - B))
        o.append('<text x="%.1f" y="%d" text-anchor="middle" class="muted">%g</text>' % (x, H - B + 14, 10 ** e))
    o.append('<text x="%d" y="%d" text-anchor="middle" class="muted">Coverage rate (log scale)</text>' % (
        (L + W - R) // 2, H - 6))
    o.append('<text x="12" y="14" class="muted">Found before contact</text>')
    ordered = [p for p in POLICY_ORDER if p in data["policies"]] + [p for p in data["policies"] if p not in POLICY_ORDER]
    ends = []
    for p in ordered:
        pts = sorted(((S.coverage_rate(st), data["cells"][(st, p)]["found"], st) for st in data["settings"]),
                     key=lambda t: (t[0], t[1], dataclasses.astuple(t[2])))
        cls = "s-" + p
        o.append('<polyline class="line %s" points="%s"/>' % (cls, " ".join("%.1f,%.1f" % (px(x), py(y)) for x, y, _ in pts)))
        for x, y, st in pts:
            o.append('<circle class="dot %s" cx="%.1f" cy="%.1f" r="3.5"><title>%s: %s, coverage %.3f, found %.2f</title></circle>'
                     % (cls, px(x), py(y), html.escape(p), html.escape(_label(st)), x, y))
        ends.append((p, px(pts[-1][0]), py(pts[-1][1])))
    placed = []
    for p, x, y in sorted(ends, key=lambda e: e[2]):
        y = max(y, placed[-1] + 12) if placed else y
        placed.append(y)
        o.append('<text x="%.1f" y="%.1f">%s</text>' % (x + 8, y + 4, html.escape(p)))
    o.append("</svg>")
    return "\n".join(o)


def _page(data, name, n, sight):
    ordered = [p for p in POLICY_ORDER if p in data["policies"]] + [p for p in data["policies"] if p not in POLICY_ORDER]
    css_l = "".join("--c-%s:%s;" % (p, COLOURS.get(p, ("#555", "#bbb"))[0]) for p in ordered)
    css_d = "".join("--c-%s:%s;" % (p, COLOURS.get(p, ("#555", "#bbb"))[1]) for p in ordered)
    css_s = "".join(".s-%s{stroke:var(--c-%s);fill:none}circle.s-%s{fill:var(--c-%s);stroke:none}" % (p, p, p, p)
                    for p in ordered)
    legend = "".join('<span><i style="background:var(--c-%s)"></i>%s</span>' % (p, html.escape(p)) for p in ordered)
    tables = _tables(data)
    chart_rows = [[_label(st), p, _f(S.coverage_rate(st), 3), _f(data["cells"][(st, p)]["found"])]
                  for p in ordered for st in data["settings"]]
    body = ["<h1>Ping search batch: %s</h1>" % html.escape(name), "<p>%s</p>" % html.escape(HEADER),
            "<p>Open ground, nobody fires. Vanguard sight %g wu; %d placements per setting and policy.</p>" % (sight, n),
            "<h2>Found before contact against coverage rate</h2>", '<div class="legend">%s</div>' % legend, _chart(data),
            _table_html(["setting", "policy", "coverage rate", "found before contact"], chart_rows)]
    for title, head, rows in tables:
        body += ["<h2>%s</h2>" % html.escape(title), _table_html(head, rows)]
    body += ["<h2>What the instrument could not express</h2>", "<ul>"]
    body += ["<li><b>%s</b>: %s</li>" % (html.escape(a), html.escape(b)) for a, b in NOT_EXPRESSED] + ["</ul>"]
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ping search batch %s</title>
<style>
:root{--bg:#fbfaf7;--fg:#1c1b19;--muted:#6b675f;--grid:#dedad0;--rule:#cfcabd;%s}
@media (prefers-color-scheme: dark){:root{--bg:#161614;--fg:#ecebe6;--muted:#9c978c;--grid:#35332e;--rule:#4a4740;%s}}
body{background:var(--bg);color:var(--fg);font-family:system-ui,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem}
h1{font-size:1.6rem}h2{font-size:1.15rem;margin:1.4rem 0 .4rem}
svg{width:100%%;height:auto}svg text{fill:var(--fg);font-size:11px}svg .muted{fill:var(--muted)}
.grid{stroke:var(--grid);stroke-width:1}.line{stroke-width:2}%s
.legend span{margin-right:1rem;font-size:.85rem}.legend i{display:inline-block;width:.9rem;height:.25rem;margin-right:.3rem;vertical-align:middle}
table{border-collapse:collapse;width:100%%;font-size:.85rem;margin:.4rem 0 1.2rem}
th,td{border-bottom:1px solid var(--rule);padding:.2rem .5rem;text-align:left}
</style>
</head>
<body>
%s
</body>
</html>
""" % (html.escape(name), css_l, css_d, css_s, "\n".join(body))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="search_batch")
    ap.add_argument("--name", default=None)
    ap.add_argument("--from-csv", default=None)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.from_csv:
        src = Path(a.from_csv)
        paths = rebuild_from_csv(src, a.out or src.parent, a.name or src.stem)
        for p in paths.values():
            print(p)
        return 0
    if not a.name:
        ap.error("--name is required unless --from-csv is given")
    out = Path(a.out) if a.out else RUNS / ("%s_%s" % (a.date, a.name))
    if a.smoke:
        sight = _vanguard_sight()
        settings = [S.SearchSetting(radius=r, reach=x * sight, reveal_ticks=REVEAL_TICKS, cooldown_ticks=c, force=FORCE)
                    for x, r, c in SMOKE_SETTINGS]
        paths = run_search_batch(settings, list(POLICY_ORDER), SMOKE_PLACEMENTS, SEED, a.workers, out, a.name)
    else:
        paths = run_search_batch(grid(_vanguard_sight()), list(POLICY_ORDER), N_PLACEMENTS, SEED, a.workers, out, a.name)
    for p in paths.values():
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
