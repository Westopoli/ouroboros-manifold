"""Layout search, run 1 (spec docs/northstar/plans/2026-10-06-layout-search-spec.md, P4): which layouts induce depth.

A seeded Latin-hypercube draw over six feature values; per layout 7 skilled plays, 3 counters and two naive baselines (blob, spread line)
are scanned for a break-even; depth gain, counter works and the layout's score follow the spec section 2 rule.
"""
import json
import random
import re
from html import escape
from pathlib import Path

from scripts.skilllab import maps, plays_space, pool, report, rows, scan, scenes, skills
from scripts.skilllab.contract import Batch

G = 2                       # draft gain threshold in units (Q-LS-01, Westley's)
UNITS, ENEMY_FROM, ENEMY_TO = 16, 8, 24
SKILL_NAMES = ("S1", "S2", "S3", "S4", "S5")
VALUES = {"choke_width_bodies": (0, 2, 4, 8), "detour_ratio": (0, 1.5, 3), "lane_count": (0, 1, 2),
          "blocked_layer_top": (0, 2, 4), "cover_density_corridor": (0, 0.1, 0.3), "start_distance": (1400, 2800)}
SKILLED = ("s1_hold_choke", "s2_concave", "s2_spread_line", "s2_screen", "s3_types_by_reach", "s4_bait",
           "s5_vulnerable_away")
COUNTERS = ("s2_mass_one_end", "s4_do_not_chase", "s1_outrange")
README = Path(__file__).resolve().parents[2] / "docs/northstar/research/map_design/README.md"
LINE_COLORS = ("--side0", "--side1", "--won", "--lost", "--muted")


def lhs_draw(n, seed):
    """n feature dicts; each feature's values are dealt evenly (within one) and shuffled on Random(seed)."""
    rng = random.Random(seed)
    columns = {}
    for key, values in VALUES.items():
        column = [values[i % len(values)] for i in range(n)]
        rng.shuffle(column)
        columns[key] = column
    return [{key: columns[key][i] for key in VALUES} for i in range(n)]


def skill_break_evens(by_play):
    """Per skill, the largest break-even among its plays (None when every play has none)."""
    out = {}
    for name, be in by_play.items():
        skill = plays_space.PLAYS[name].skill
        best = out.get(skill)
        out[skill] = be if best is None else best if be is None else max(best, be)
    return out


def score_layout(skilled, naive, counters, g=G):
    """skilled and counters: skill -> break-even; naive: the shared blob's break-even."""
    gains = {s: None if b is None or naive is None else b - naive for s, b in skilled.items()}
    works = {}
    for s, b in skilled.items():
        if not skills.has_counter(s):
            works[s] = None
        elif s not in counters or b is None:
            works[s] = False
        else:
            c = counters[s]
            works[s] = c is None or c < b
    score = sum(1 for s, gain in gains.items() if gain is not None and gain >= g and works[s] is not False)
    return {"gains": gains, "counter_works": works, "no_gain": [s for s, gain in gains.items() if gain is None],
            "score": score}


def _features(v):
    w, n, k = v["choke_width_bodies"], v["lane_count"], v["blocked_layer_top"]
    return maps.Features(
        choke_count=1 if w else 0, choke_width_wu=w * maps.LAYOUT_BODY_WU, choke_width_bodies=float(w), lane_count=n,
        blocked_layer_ranges=((0, k),) if (w or n) else (), fight_layer_blocked=bool(w or n),
        cover_density_corridor=v["cover_density_corridor"], start_distance=v["start_distance"],
        detour_ratio=v["detour_ratio"], blocked_layer_top=k)


def run_layout(values, seed, replicates, scan_fn):
    """scan_fn(label, build, replicates) -> ScanResult; the map is built once and passed to every placed scene (Rev 4).
    12 scans: 7 skilled, 3 counters, the naive blob and the naive spread line; gains are scored against each baseline."""
    features = _features(values)
    d = values["start_distance"]
    frame = maps.Frame((-d / 2, 0.0), (d / 2, 0.0), 0)
    layout = maps.layout_map(features, seed, frame=frame)
    builds = {name: scenes.placed_scene(layout, name, d, features) for name in SKILLED}
    builds.update({name: scenes.placed_scene(layout, name, d, features, counter=True) for name in COUNTERS})
    builds.update({name: scenes.placed_scene(layout, name, d, features) for name in scenes.NAIVE_PLAYS})
    results = {label: scan_fn(label, build, replicates) for label, build in builds.items()}
    be = {label: r.beats for label, r in results.items()}
    skilled, counters = skill_break_evens({n: be[n] for n in SKILLED}), skill_break_evens({n: be[n] for n in COUNTERS})
    scored = score_layout(skilled, be["naive"], counters)
    scored_line = score_layout(skilled, be["naive_line"], counters)
    out = []
    for label, r in results.items():
        skill = None if label in scenes.NAIVE_PLAYS else plays_space.PLAYS[label].skill
        variant = "naive" if label in scenes.NAIVE_PLAYS else "skilled" if label in SKILLED else "counter"
        for c in r.cells:
            for f in c.fights:
                out.append(rows.fight_row(f, features, play=label, variant=variant, enemy_heads=c.enemy_heads,
                                          break_even=r.beats, no_gain=skill in scored["no_gain"], winner=f.winner,
                                          placement_shift=builds[label].labels["placement_shift"]))
    return {"features": dict(values), "rows": out, **scored,
            "gains_naive_line": scored_line["gains"], "score_naive_line": scored_line["score"]}


def _mean(xs):
    return sum(xs) / len(xs)


def _summary(layouts):
    means = {}
    for key, values in VALUES.items():
        means[key] = {str(v): _mean([x["score"] for x in layouts if x["features"][key] == v])
                      for v in values if any(x["features"][key] == v for x in layouts)}
    return {"G": G, "layouts": layouts, "feature_means": means}


def _panel_svg(i, key, means):
    pw, ph = 200, 120
    x0, y0 = 20 + (i % 3) * (pw + 20), 24 + (i // 3) * (ph + 50)
    vals = sorted(means[key].items(), key=lambda kv: float(kv[0]))
    parts = [f'<g class="panel" transform="translate({x0},{y0})">', report._text(0, -8, key, "muted")]
    parts.append(f'<line class="grid" x1="0" x2="{pw}" y1="{ph}" y2="{ph}"/>')
    for j, (v, m) in enumerate(vals):
        x = report._scale(j, 0, max(len(vals) - 1, 1), 20, pw - 20)
        y = report._scale(m, 5, 0, 0, ph)
        parts.append(f'<circle class="cell won" cx="{report._n(x)}" cy="{report._n(y)}" r="4"/>')
        parts.append(report._text(x, ph + 14, v, "muted", "middle"))
    parts.append(report._text(-4, 8, "5", "muted", "end"))
    parts.append("</g>")
    return "\n".join(parts)


def chart_score_by_feature(summary):
    parts = ['<svg viewBox="0 0 700 360" role="img">']
    parts += [_panel_svg(i, key, summary["feature_means"]) for i, key in enumerate(VALUES)]
    parts.append("</svg>")
    return "\n".join(parts)


def chart_gain_by_choke(summary):
    widths = VALUES["choke_width_bodies"]
    mean_gain = {s: [] for s in SKILL_NAMES}
    for w in widths:
        for s in SKILL_NAMES:
            g = [x["gains"][s] for x in summary["layouts"] if x["features"]["choke_width_bodies"] == w and x["gains"][s] is not None]
            mean_gain[s].append(_mean(g) if g else None)
    flat = [g for gs in mean_gain.values() for g in gs if g is not None]
    lo, hi = min(flat + [0]), max(flat + [0])
    xof = lambda w: report._scale(widths.index(w), 0, len(widths) - 1, report.PX0 + 20, report.PX1 - 20)
    parts = [f'<svg viewBox="0 0 {report.W} {report.H}" role="img">']
    parts += report._hgrid(sorted({lo, 0, hi}), lo, hi, lambda v: f"{v:.1f}")
    parts.append(report._text((report.PX0 + report.PX1) / 2, report.H - 6, "Choke width (bodies)", "muted", "middle"))
    for w in widths:
        parts.append(report._text(xof(w), report.PY1 + 16, w if w else "none", "muted", "middle"))
    for s, color in zip(SKILL_NAMES, LINE_COLORS):
        pts = [(xof(w), report._scale(g, hi, lo, report.PY0, report.PY1)) for w, g in zip(widths, mean_gain[s]) if g is not None]
        style = f"stroke:var({color});fill:none;stroke-width:2"
        parts.append(f'<polyline class="line" style="{style}" points="{" ".join(f"{report._n(x)},{report._n(y)}" for x, y in pts)}"/>')
        if pts:
            parts.append(f'<text x="{report._n(pts[-1][0] + 8)}" y="{report._n(pts[-1][1] + 4)}" style="fill:var({color})">{s}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def _means_text(summary, *keys):
    return "; ".join(f"{k}: " + ", ".join(f"{v} -> {m:.2f}" for v, m in summary["feature_means"][k].items()) for k in keys)


def _counter_text(summary):
    flags = [w for x in summary["layouts"] for w in x.get("counter_works", {}).values() if w is not None]
    return "counter works in %d of %d (layout, skill) pairs" % (sum(flags), len(flags)) if flags else "no counter data"


def pillars_table(summary):
    pillars = re.findall(r"^### (P\d+)\. (.+)$", README.read_text(encoding="utf-8"), flags=re.M)
    recorded = {
        "P2": _means_text(summary, "start_distance"),
        "P3": _means_text(summary, "choke_width_bodies"),
        "P4": _means_text(summary, "lane_count", "detour_ratio"),
        "P5": _means_text(summary, "blocked_layer_top"),
        "P6": _means_text(summary, "cover_density_corridor"),
        "P8": _counter_text(summary),
    }
    rows_html = []
    for pid, title in pillars:
        number = recorded.get(pid)
        cells = (pid, title, number or "not measured in run 1",
                 "recorded; pass marks are Westley's" if number else "not judged")
        rows_html.append("<tr>" + "".join(f"<td>{escape(c)}</td>" for c in cells) + "</tr>")
    return ("<table>\n<thead><tr><th>Pillar</th><th>Title</th><th>Number recorded (mean depth score by value)</th>"
            "<th>Verdict</th></tr></thead>\n<tbody>\n" + "\n".join(rows_html) + "\n</tbody>\n</table>")


def _page(summary):
    missing = [s for s in SKILL_NAMES if not skills.has_counter(s)]
    best = [x for x in summary["layouts"] if x["score"] >= 3]
    body = ["<h1>Layout search: which layouts induce depth</h1>",
            f"<h2>{len(summary['layouts'])} layouts, depth score 0 to 5 (gain of at least {G} units, counter works)</h2>",
            "<p>%s: no counter registered, scored on gain alone.</p>" % escape(", ".join(missing)) if missing else "",
            "<h3>Depth score against each feature</h3>", chart_score_by_feature(summary),
            "<h3>Gain per skill against choke width</h3>", chart_gain_by_choke(summary),
            "<h3>Pillars</h3>", pillars_table(summary),
            "<h3>Layouts scoring 3 or more (%d)</h3>" % len(best),
            "<p>%s</p>" % escape("; ".join("#%d %s" % (x["index"], json.dumps(x["features"], sort_keys=True)) for x in best) or "none")]
    return report._html("Layout search", body)


def _real_scan(map_fn):
    return lambda label, build, replicates: scan.scan(build, UNITS, ENEMY_FROM, ENEMY_TO, replicates=replicates,
                                                      map_fn=map_fn)


def _run(n_layouts, seed, out, replicates, scan_fn):
    out.mkdir(parents=True, exist_ok=True)
    layouts, fight_rows = [], []
    for i, values in enumerate(lhs_draw(n_layouts, seed)):
        r = run_layout(values, seed + i, replicates, scan_fn)
        fight_rows += [{"layout": i, **row} for row in r.pop("rows")]
        layouts.append({"index": i, **r})
    summary = _summary(layouts)
    paths = {"csv": out / "depth.csv", "summary": out / "depth_summary.json", "page": out / "depth_page.html"}
    rows.write_rows(fight_rows, paths["csv"])
    paths["summary"].write_text(json.dumps(summary, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    paths["page"].write_text(_page(summary), encoding="utf-8")
    return paths


def run(n_layouts, seed, workers, out_dir, replicates=3, scan_fn=None):
    if workers < 1:
        raise ValueError("workers must be at least 1")
    out = Path(out_dir)
    if scan_fn is not None:
        return _run(n_layouts, seed, out, replicates, scan_fn)
    with pool.FightPool(workers, lean=True) as p:
        return _run(n_layouts, seed, out, replicates, _real_scan(p.map))
