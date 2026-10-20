"""report(batch, out_dir): one self-contained HTML page (inline SVG, standard library only).

Spec: docs/northstar/plans/skilllab-harness-spec.md AC 18-19.
"""
from __future__ import annotations

import os
from html import escape
from pathlib import Path

from scripts.skilllab import conditions, diagram, evidence
from scripts.skilllab.contract import OPENING_WINDOW_TICKS, Batch, ScanResult

W, H = 640, 320                       # svg size
L, R, T, B = 56, 80, 24, 40           # plot margins (right margin holds the series labels)
PX0, PX1, PY0, PY1 = L, W - R, T, H - B

FONT = "https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap"

CSS = """
:root{--bg:#fbfaf7;--fg:#1c1b19;--muted:#6b675f;--grid:#dedad0;--won:#2a7f62;--lost:#c0452f;
--side0:#2f5fb3;--side1:#b36a1f;--gap:rgba(120,120,120,.22);--rule:#cfcabd}
@media (prefers-color-scheme: dark){:root{--bg:#161614;--fg:#ecebe6;--muted:#9c978c;--grid:#35332e;
--won:#58c9a1;--lost:#f0806a;--side0:#7fa8f0;--side1:#e8a35c;--gap:rgba(190,190,190,.2);--rule:#4a4740}}
body{background:var(--bg);color:var(--fg);font-family:Inter,system-ui,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem}
h1{font-size:1.6rem}h2{font-size:1.15rem;margin:.6rem 0}h3{font-size:1rem;color:var(--muted);margin:1.6rem 0 .3rem}
svg{width:100%;height:auto}svg text{fill:var(--fg);font-size:11px}svg .muted{fill:var(--muted)}
.grid{stroke:var(--grid);stroke-width:1}.marker{stroke:var(--fg);stroke-width:1;stroke-dasharray:4 3}
.cell.won{fill:var(--won)}.cell.lost{fill:var(--lost)}
.side0{stroke:var(--side0);fill:none;stroke-width:2}.side1{stroke:var(--side1);fill:none;stroke-width:2}
text.side0{fill:var(--side0);stroke:none}text.side1{fill:var(--side1);stroke:none}
.gap{fill:var(--gap);stroke:none}
.cell.defect{fill:var(--muted)}
.ceiling{fill:var(--won)}
td.finding{background:var(--lost);color:var(--bg)}
table{border-collapse:collapse;width:100%;font-size:.85rem;margin:.4rem 0 1.2rem}
th,td{border-bottom:1px solid var(--rule);padding:.2rem .5rem;text-align:left}
"""


def _n(v: float) -> str:
    return f"{v:.3f}"


def _scale(v, lo, hi, p_lo, p_hi):
    """Linear map of v in [lo, hi] to [p_lo, p_hi]; a flat range sits in the middle."""
    if hi == lo:
        return (p_lo + p_hi) / 2
    return p_lo + (v - lo) / (hi - lo) * (p_hi - p_lo)


def _text(x, y, s, cls="", anchor="start"):
    c = f' class="{cls}"' if cls else ""
    return f'<text x="{_n(x)}" y="{_n(y)}" text-anchor="{anchor}"{c}>{escape(str(s))}</text>'


def _hgrid(values, lo, hi, fmt):
    out = []
    for v in values:
        y = _scale(v, hi, lo, PY0, PY1)       # larger value, smaller y
        out.append(f'<line class="grid" x1="{PX0}" x2="{PX1}" y1="{_n(y)}" y2="{_n(y)}"/>')
        out.append(_text(PX0 - 6, min(y + 4, PY1), fmt(v), "muted", "end"))
    return out


def _scan_svg(scan: ScanResult) -> str:
    cells = sorted(scan.cells, key=lambda c: c.enemy_heads)
    if not cells:
        return f'<svg viewBox="0 0 {W} {H}" role="img"></svg>'
    heads = [c.enemy_heads for c in cells]
    ms = [c.mean_margin for c in cells]
    lo, hi = min(ms + [0.0]), max(ms + [0.0])
    xof = lambda n: _scale(n, heads[0], heads[-1], PX0 + 20, PX1 - 20)
    yof = lambda m: _scale(m, hi, lo, PY0, PY1)
    ticks = sorted({lo, 0.0, hi})
    parts = [f'<svg viewBox="0 0 {W} {H}" role="img">']
    parts += _hgrid(ticks, lo, hi, lambda v: f"{v:.2f}")
    parts.append(_text((PX0 + PX1) / 2, H - 6, "Enemy units", "muted", "middle"))
    parts.append(_text(12, PY0 - 8, "Mean margin", "muted"))
    for c in cells:
        parts.append(_text(xof(c.enemy_heads), PY1 + 16, c.enemy_heads, "muted", "middle"))
    if scan.ceiling_hit:
        parts.append(_text((PX0 + PX1) / 2, PY0 - 6, f"ceiling hit: beats up to {scan.beats}", "ceiling", "middle"))
    elif scan.beats is not None:
        pos = {c.enemy_heads: xof(c.enemy_heads) for c in cells}
        if scan.beats in pos and scan.beats + 1 in pos:
            mx = (pos[scan.beats] + pos[scan.beats + 1]) / 2
            parts.append(f'<line class="marker" x1="{_n(mx)}" x2="{_n(mx)}" y1="{PY0}" y2="{PY1}"/>')
            parts.append(_text(mx, PY0 - 6, f"beats {scan.beats}, loses to {scan.beats + 1}", "", "middle"))
    for c in cells:
        cls = "cell defect" if c.defect else "cell won" if c.won else "cell lost"
        parts.append(f'<circle class="{cls}" cx="{_n(xof(c.enemy_heads))}" cy="{_n(yof(c.mean_margin))}" r="5"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def _scan_table(scan: ScanResult) -> str:
    rows = ["<tr><th>Enemy units</th><th>Mean margin</th><th>Result</th><th>In words</th></tr>"]
    for c in sorted(scan.cells, key=lambda c: c.enemy_heads):
        words = f"{scan.size} units {'beat' if c.won else 'lose to'} {c.enemy_heads}"
        result = "won" if c.won else "lost"
        if c.defect:
            result, words = "defect", f"defect: a draw or a cap sits in the cell at {c.enemy_heads} (a lab defect, not a result)"
        rows.append(f"<tr><td>{c.enemy_heads}</td><td>{c.mean_margin:.3f}</td>"
                    f"<td>{result}</td><td>{escape(words)}</td></tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def _firing_svg(firing: list) -> str:
    ticks = [f[0] for f in firing]
    a0 = [f[1] for f in firing]
    a1 = [f[2] for f in firing]
    top = max(a0 + a1 + [0]) or 1
    xs = [_scale(t, ticks[0], ticks[-1], PX0, PX1) for t in ticks]
    y0 = [_scale(c, top, 0, PY0, PY1) for c in a0]       # one y scale for both lines
    y1 = [_scale(c, top, 0, PY0, PY1) for c in a1]
    pts = lambda ys: " ".join(f"{_n(x)},{_n(y)}" for x, y in zip(xs, ys))
    parts = [f'<svg viewBox="0 0 {W} {H}" role="img">']
    parts += _hgrid(sorted({0, top}), 0, top, lambda v: str(v))
    parts.append(_text((PX0 + PX1) / 2, H - 6, "Tick", "muted", "middle"))
    parts.append(_text(12, PY0 - 8, "Units able to fire", "muted"))
    n = len(ticks)
    shown = range(n) if n <= 8 else sorted({round(i * (n - 1) / 7) for i in range(8)})
    for i in shown:
        parts.append(_text(xs[i], PY1 + 16, ticks[i], "muted", "middle"))
    if xs:
        gap = " ".join(f"{_n(x)},{_n(y)}" for x, y in list(zip(xs, y0)) + list(zip(xs, y1))[::-1])
        parts.append(f'<polygon class="gap" points="{gap}"/>')
    parts.append(f'<polyline class="side0" fill="none" points="{pts(y0)}"/>')
    parts.append(f'<polyline class="side1" fill="none" points="{pts(y1)}"/>')
    if xs:
        nudge = 5 if y0[-1] == y1[-1] else 0           # equal ends: keep each label nearer its own line
        parts.append(_text(xs[-1] + 8, y0[-1] - nudge + 4, "Side 0", "side0"))
        parts.append(_text(xs[-1] + 8, y1[-1] + nudge + 4, "Side 1", "side1"))
    parts.append("</svg>")
    return "\n".join(parts)


def _firing_table(firing: list) -> str:
    rows = ["<tr><th>Tick</th><th>Side 0</th><th>Side 1</th></tr>"]
    rows += [f"<tr><td>{t}</td><td>{a}</td><td>{b}</td></tr>" for t, a, b in firing]
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def _no_break_even(scan: ScanResult) -> str:
    heads = [c.enemy_heads for c in scan.cells]
    return f"No break-even found between {min(heads, default=0)} and {max(heads, default=0)} enemy units."


def _sentences(scans: dict) -> list:
    """Finding sentences, in batch order; the combined one leads when reach and identical both have a break-even."""
    out, plain = [], list(scans.items())
    reach, ident = scans.get("reach"), scans.get("identical")
    if reach is not None and ident is not None and reach.beats is not None and ident.beats is not None \
            and not (reach.ceiling_hit or ident.ceiling_hit):
        out.append(f"With longer reach, {reach.size} units beat {reach.beats}. Identical sides beat {ident.beats}.")
        plain = [(k, v) for k, v in plain if k not in ("reach", "identical")]
    for label, sc in plain:
        if sc.ceiling_hit:
            out.append(f"{label}: ceiling hit, {sc.size} units beat every enemy size up to {sc.beats}.")
        else:
            out.append(_no_break_even(sc) if sc.beats is None else f"{label}: {sc.size} units beat {sc.beats}.")
    return out


def _html(title: str, body: list) -> str:
    return ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            f"<title>{escape(title)}</title>\n<link rel=\"stylesheet\" href=\"{FONT}\">\n"
            f"<style>{CSS}</style>\n</head>\n<body>\n" + "\n".join(body) + "\n</body>\n</html>\n")


def report(batch: Batch, out_dir) -> str:
    out = Path(os.fspath(out_dir))
    out.mkdir(parents=True, exist_ok=True)
    body = [f"<h1>{escape(batch.title)}</h1>"]
    body += [f"<h2>{escape(s)}</h2>" for s in _sentences(batch.scans)]
    for label, sc in batch.scans.items():
        body += [f"<h3>{escape(label)}: line of fights by enemy size</h3>", _scan_svg(sc), _scan_table(sc)]
    for label, fr in batch.firing_example.items():
        body += [f"<h3>{escape(label)}: units able to fire through one fight</h3>",
                 _firing_svg(fr.firing), _firing_table(fr.firing)]
    html = _html(batch.title, body)
    path = out / "report.html"
    path.write_text(html, encoding="utf-8")
    return str(path)


# ---- the artifact: the page of README section 5 -----------------------------------------------------------------------------------

ARTIFACT_SECTIONS = ("drafts", "findings", "baseline-ceiling", "agreement", "both-wrong", "refinement", "cone-grid", "conditions")
NO_VERDICTS = "no condition verdicts: thresholds not supplied"
MIRROR_C1 = "mirror C1: not computed here, it lives in the engine-run evaluate_all"
NO_C1 = "no C1: no equal-numbers cell"
C2_FIELDS = ("c2_rank_agreement", "c2_off_trend_margin", "c2_off_trend_share")
DRAFT_TEXT = {
    "DRAFT-guard-radius": "the radius a guarding holder steps out to engage",
    "DRAFT-mixes": "the roster mixes M0 to M9 (and M3b) of the plays",
    "DRAFT-reengage-silence-ticks": "the silence after which an idle side is attack-moved onto the enemy centroid",
    "DRAFT-scale-marks": "the speed marks of the scale guards",
    "DRAFT-reengage-moved-wu": "the displacement from the window start (the tick the silence counter was last zeroed) above which an idle-eligible unit counts as moved and zeroes its side's counter; units holding a destination are not tested (1 wu)",
    "DRAFT-coarse-step": "the headcount step of the first coarse pass of a scan (scan.COARSE_STEP)",
    "DRAFT-control-max-ticks": "the tick cap of a control fight (sweep.CONTROL_MAX_TICKS)",
    "DRAFT-probe-count-bound": "the bound on the probes of a bisected scan (at most 9 at COARSE_STEP 8, derived)",
    "DRAFT-ground-geometry": "the coordinates and radii of the ground scenes",
    "DRAFT-behind-cover": "how far short-reach types stand in front of the long-reach ones (scenes.BEHIND_COVER 150)",
    "DRAFT-ambush-behind": "how far the ambush group stands behind the bait group (scenes.AMBUSH_BEHIND 200)",
    "DRAFT-mix-M1": "the composition of roster mix M1, a row of the MIXES table in plays_space.py",
    "DRAFT-mix-M2": "the composition of roster mix M2, a row of the MIXES table in plays_space.py",
    "DRAFT-mix-M3": "the composition of roster mix M3, a row of the MIXES table in plays_space.py",
    "DRAFT-mix-M4": "the composition of roster mix M4, a row of the MIXES table in plays_space.py",
    "DRAFT-mix-M3b": "the composition of roster mix M3b, a row of the MIXES table in plays_space.py",
    "DRAFT-mix-M5": "the composition of roster mix M5, a row of the MIXES table in plays_space.py",
    "DRAFT-mix-M6": "the composition of roster mix M6, a row of the MIXES table in plays_space.py",
    "DRAFT-mix-M7": "the composition of roster mix M7, a row of the MIXES table in plays_space.py",
    "DRAFT-mix-M8": "the composition of roster mix M8, a row of the MIXES table in plays_space.py",
    "DRAFT-mix-M9": "the composition of roster mix M9, a row of the MIXES table in plays_space.py",
    "DRAFT-layer-stack-s3_raider_bombard": "the layers the play s3_raider_bombard places each side-0 unit type on (derived from its placement in plays_space.py)",
    "DRAFT-layer-stack-s3_interceptor_bombard": "the layers the play s3_interceptor_bombard places each side-0 unit type on (derived from its placement in plays_space.py)",
    "DRAFT-layer-stack-s3_interceptor_raider": "the layers the play s3_interceptor_raider places each side-0 unit type on (derived from its placement in plays_space.py)",
    "DRAFT-layer-stack-s3_bombard_bastion": "the layers the play s3_bombard_bastion places each side-0 unit type on (derived from its placement in plays_space.py)",
    "DRAFT-layer-stack-s3_bombard_bastion_level": "the layers the play s3_bombard_bastion_level places each side-0 unit type on (derived from its placement in plays_space.py)",
}
STANDIN = "re-engage is a lab stand-in for the engine's pending sight-engagement rule"
NO_DEFENDER = "C1 for plays without a naive defender baseline rests on naive_attacker only"


_csv = diagram.csv_text


def _attrs(**kv) -> str:
    return "".join(' data-%s="%s"' % (k.replace("_", "-"), escape(str(v), quote=True)) for k, v in kv.items())


def _where(family, play, layout, point) -> str:
    return "%s %s on layout %s%s" % (family, play, layout, "" if point == "-" else " (" + point + ")")


def _sentence(n, rows) -> str:
    where = _where(n.family, n.play, n.layout, n.point)
    if n.kind == "crossing":
        reach = "" if n.reach is None or len({r.get("reach") for r in rows}) < 2 else " with reach %s" % n.reach
        return "%s: against %s the gain crosses between %r and %r%s" % (where, n.role, n.knob_lo, n.knob_hi, reach)
    if n.kind == "ceiling_hit":
        return "%s: ceiling hit at %r, the play beat every enemy size up to %d" % (where, n.knob_lo, n.heads)
    r = rows[n.row]
    extra = "" if n.role == "none" else ", baseline %s" % n.role
    extra += ", %s" % r["kind"] if r["kind"].startswith("control_") else ""
    return "%s%s: both predictions were wrong (outcome %s)" % (where, extra, r["outcome"])


def _called(rows) -> str:
    """Per reading (window, paper, whole), how many of the fights that ended side0 or side1 it named the winner of (LAB-REV3-C, R4). A tie,
    a paper word of no_reach, a cap, a draw and a no_reach_stall name or ask no winner, so they are no call."""
    fights = [r for r in rows if r["outcome"] in ("side0", "side1")]
    whole = lambda r: "side0" if r["firing_unit_seconds_0"] > r["firing_unit_seconds_1"] else "side1" if r["firing_unit_seconds_1"] > r["firing_unit_seconds_0"] else "tie"
    readings = (("window", lambda r: r["predicted_count"]), ("paper", lambda r: r.get("predicted_paper")), ("whole", whole))
    return "".join('<p class="called"%s>%s: right in %d of %d fights</p>'
                   % (_attrs(reading=name, right=sum(read(r) == r["outcome"] for r in fights), fights=len(fights)), name,
                      sum(read(r) == r["outcome"] for r in fights), len(fights)) for name, read in readings)


def _counts(n, rows) -> str:
    spans = []
    for c in diagram.scan_counts(rows, n):
        lost = "no lost headcount" if c["loses_to"] is None else "loses to %d" % c["loses_to"]
        spans.append('<span class="count"%s>%s at %s: beats %d, %s</span>'
                     % (_attrs(scan=c["scan"], knob=_csv(c["knob"]), beats=c["beats"], loses_to="" if c["loses_to"] is None else c["loses_to"]),
                        escape(c["scan"]), _csv(c["knob"]), c["beats"], lost))
    return '<p class="counts"%s>%s</p>' % (_attrs(notable=n.id), "; ".join(spans))


def _always_won(rows, cut) -> bool:
    mine = [r for r in rows if (r["family"], r["play"], r["layout"], r["baseline"]) == (cut["family"], cut["play"], cut["layout"], "none")
            and r["kind"] in diagram.SCAN_KINDS]
    return all(r["outcome"] == "side0" for r in mine)


def _cut_list(summary, rows) -> str:
    items = []
    for family in summary.get("order", ()):
        for cut in summary.get("families", {}).get(family, {}).get("baseline_no_fit") or ():
            k = cut["last_headcount"]
            if k is None:
                words = "no scan: baseline_no_fit at the smallest headcount"
            elif _always_won(rows, cut):
                words = "won through %d, scan cut by baseline_no_fit" % k
            else:
                words = "scan cut by baseline_no_fit at %d" % k
            items.append('<li data-cut-scan=""%s>%s: %s</li>' % (
                _attrs(family=cut["family"], play=cut["play"], layout=cut["layout"], last_headcount="" if k is None else k),
                escape(_where(cut["family"], cut["play"], cut["layout"], "-")), escape(words)))
    return '<ul class="cut-scans">\n' + "\n".join(items) + "\n</ul>" if items else ""


def _refused(summary) -> list:
    families = summary.get("families", {})
    out = []
    for family in summary.get("order", ()):
        mine = [e for e in families.get(family, {}).get("refused") or () if e["role"].startswith("naive_")]
        out += sorted(mine, key=lambda e: (e["play"], e["layout"], e["role"]))
    return out


def _refused_ul(entries, cls, **attrs) -> str:
    items = ['<li data-refused-baseline=""%s>no naive %s: %s</li>' % (
        _attrs(family=e["family"], play=e["play"], layout=e["layout"], role=e["role"], reason=e["reason"]),
        escape(e["role"][len("naive_"):].replace("_", " ")), escape(e["reason"].replace("_", " "))) for e in entries]
    return '<ul class="%s"%s>\n' % (cls, _attrs(**attrs)) + "\n".join(items) + "\n</ul>"


def _refused_blocks(refused) -> dict:
    by_play = {}
    for e in refused:
        by_play.setdefault((e["family"], e["play"]), []).append(e)
    return {k: _refused_ul(sorted(v, key=lambda e: (e["layout"], e["role"])), "refused-play", family=k[0], play=k[1]) for k, v in by_play.items()}


def _shifted(summary) -> list:
    families = summary.get("families", {})
    out = []
    for family in summary.get("order", ()):
        mine = [e for e in families.get(family, {}).get("shifted_posts") or () if e["role"].startswith("naive_")]
        out += sorted(mine, key=lambda e: (e["play"], e["layout"], e["role"]))
    return out


def _shifted_ul(entries, cls, **attrs) -> str:
    items = []
    for e in entries:
        wu = "%.1f" % e["shift_wu"]
        items.append('<li data-shifted-post=""%s>naive %s: post shifted %s wu</li>' % (
            _attrs(family=e["family"], play=e["play"], layout=e["layout"], role=e["role"], shift_wu=wu),
            escape(e["role"][len("naive_"):].replace("_", " ")), wu))
    return '<ul class="%s"%s>\n' % (cls, _attrs(**attrs)) + "\n".join(items) + "\n</ul>"


def _shifted_blocks(shifted) -> dict:
    by_play = {}
    for e in shifted:
        by_play.setdefault((e["family"], e["play"]), []).append(e)
    return {k: _shifted_ul(sorted(v, key=lambda e: (e["layout"], e["role"])), "shifted-play", family=k[0], play=k[1]) for k, v in by_play.items()}


def _findings(summary, rows, ns, svgs) -> list:
    out = []
    refused, shifted = _refused(summary), _shifted(summary)
    blocks, sblocks = _refused_blocks(refused), _shifted_blocks(shifted)
    for n in ns:
        for b in (blocks, sblocks):
            if (n.family, n.play) in b:
                out.append(b.pop((n.family, n.play)))
        out.append("<h2%s>%s</h2>" % (_attrs(notable=n.id), escape(_sentence(n, rows))))
        out.append(svgs[n.id])
        if n.kind == "crossing":
            out.append(_counts(n, rows))
    if not ns:
        out += ["<p>no crossing</p>", "<p>no ceiling hit</p>", "<p>no both_wrong fight</p>"]
    cuts = _cut_list(summary, rows)
    out += [cuts] if cuts else []
    order = {f: i for i, f in enumerate(summary.get("order", ()))}
    for k in sorted(set(blocks) | set(sblocks), key=lambda k: (order[k[0]], k[1])):
        out += [b[k] for b in (blocks, sblocks) if k in b]
    out += [_refused_ul(refused, "refused-baselines")] if refused else []
    out += [_shifted_ul(shifted, "shifted-posts")] if shifted else []
    return out + ['<p class="probed"%s>%s</p>' % (_attrs(family=r["family"], play=r["play"], layout=r["layout"]), escape(r["line"]))
                  for r in summary.get("probed") or ()]


def _vision_layouts(summary, rows) -> str:
    refused = [e for e in summary.get("families", {}).get("vision", {}).get("refused") or ()
               if e["role"] == "play" and e["reason"] == "no_fit"] if "vision" in summary.get("order", ()) else []
    ran = sorted({str(r["layout"]) for r in rows if r["family"] == "vision"})
    gone = list(dict.fromkeys(str(e["layout"]) for e in refused if str(e["layout"]) not in ran))
    if not gone or not ran:
        return ""
    lead = "layout %s only" % ran[0] if len(ran) == 1 else "layouts %s only" % ", ".join(ran)
    who = ("%s refuses" % gone[0] if len(gone) == 1 else "%s and %s refuse" % (", ".join(gone[:-1]), gone[-1]))
    return '<p class="vision-layouts"%s>vision cells: %s; %s the play: no_fit</p>' % (
        _attrs(layouts_run=",".join(ran), layouts_refused=",".join(gone)), lead, who)


def _reengage_standin(rows) -> str:
    if any((r.get("reengage_0") or 0) > 0 or (r.get("reengage_1") or 0) > 0 for r in rows):
        return '<p class="reengage-standin">%s</p>' % escape(STANDIN)
    return ""


def _drafts(summary, rows) -> list:
    families = summary.get("families", {})
    live = lambda f: f in families and not families[f].get("skipped")
    items = []
    if rows:
        items.append(("DRAFT-opening-window-ticks", "%d ticks after first contact: the primary prediction window" % OPENING_WINDOW_TICKS))
    if live("arc"):
        items.append(("DRAFT-firing-arc-deg", "the swept firing arcs, grid from Westley's ruling 30 deg (magnitudes, they will retune)"))
    if live("cone"):
        items += [("DRAFT-aoe-cone-range", "the swept cone ranges"), ("DRAFT-aoe-cone-deg", "the swept cone half-angles"),
                  ("DRAFT-aoe-cone-share", "the cone damage share")]
    items += list(DRAFT_TEXT.items())
    out = ['<ul class="drafts">'] + ['<li data-draft="%s">%s: %s</li>' % (name, name, escape(words)) for name, words in items] + ["</ul>"]
    out += [p for p in (_vision_layouts(summary, rows), _reengage_standin(rows)) if p]
    plays = sorted({e["play"] for e in _refused(summary) if e["role"].startswith("naive_defender")})
    if plays:
        out.append('<p class="no-defender-baseline" data-plays-without-defender="%s">%s: %s</p>' % (
            escape(",".join(plays), quote=True), NO_DEFENDER, escape(", ".join(plays))))
    return out


def _threshold_spans(t, names) -> str:
    return " ".join('<span class="threshold"%s>%s = %s</span>' % (_attrs(name=n, value=repr(getattr(t, n))), n, repr(getattr(t, n)))
                    for n in names)


def _holds(flag) -> str:
    return "true" if flag else "false"


def _conditions(rows, t) -> list:
    out = [] if t is not None else ["<p>%s</p>" % NO_VERDICTS]
    out.append("<p>%s</p>" % MIRROR_C1)
    verdicts = {}
    for basis in ("window", "whole"):
        counts = evidence.agreement_counts(evidence.row_agreement(r, basis) for r in rows)
        table = ['<table class="words"%s>' % _attrs(basis=basis)]
        for word, n in counts.items():
            table.append('<tr class="c2-count"%s><td>%s</td><td>%d</td></tr>' % (_attrs(basis=basis, word=word, count=n), word, n))
        if t is not None:
            for r in conditions.c2_table([conditions.row_scan(rows)], t):
                if r["basis"] != basis:
                    continue
                heads = "" if r["enemy_heads"] is None else r["enemy_heads"]
                verdicts[("C2", basis, r["scope"], heads)] = r["holds"]
                table.append('<tr class="c2-verdict"%s><td>C2 %s%s: %d fights, rho %.3f, off-trend share %.3f %s</td></tr>' % (
                    _attrs(code="C2", basis=basis, scope=r["scope"], enemy_heads=heads, fights=r["fights"], holds=_holds(r["holds"])),
                    r["scope"], "" if heads == "" else " " + str(heads), r["fights"], r["rho"], r["off_trend_share"],
                    _threshold_spans(t, C2_FIELDS)))
        lines = conditions.row_c1(rows, basis)[0]
        for c in lines:
            key = (c["family"], c["play"], c["layout"], c["point"], c["knob"], c["role"])
            attrs = dict(code="C1@" + c["role"], basis=basis, family=c["family"], play=c["play"], layout=c["layout"], point=c["point"],
                         knob=_csv(c["knob"]), baseline=c["role"], advantage=repr(c["advantage"]), baseline_max=repr(c["baseline_max"]))
            tail = ""
            if t is not None:
                holds = c["advantage"] > c["baseline_max"] + t.c1_min_firing_advantage
                verdicts[("C1",) + (basis,) + key] = holds
                attrs["holds"] = _holds(holds)
                tail = " " + _threshold_spans(t, ("c1_min_firing_advantage",))
            table.append('<tr class="c1"%s><td>C1@%s %s knob %s: advantage %s, baseline maximum %s%s</td></tr>' % (
                _attrs(**attrs), c["role"], escape(_where(c["family"], c["play"], c["layout"], c["point"])), _csv(c["knob"]),
                repr(c["advantage"]), repr(c["baseline_max"]), tail))
        table.append("</table>")
        out.append("\n".join(table))
    for m in conditions.row_c1(rows)[1]:
        out.append('<p class="c1-none"%s>%s</p>' % (_attrs(family=m["family"], play=m["play"], layout=m["layout"], point=m["point"],
                                                          knob=_csv(m["knob"]), baseline=m["role"]), NO_C1))
    if t is not None:
        differ = []
        for key, window in verdicts.items():
            if key[0] == "C2" and key[1] == "window":
                other = verdicts.get(("C2", "whole") + key[2:])
                extra = _attrs(scope=key[2], enemy_heads=key[3])
                code = "C2"
            elif key[0] == "C1" and key[1] == "window":
                other = verdicts.get(("C1", "whole") + key[2:])
                extra = _attrs(family=key[2], play=key[3], layout=key[4], point=key[5], knob=_csv(key[6]))
                code = "C1@" + key[7]
            else:
                continue
            if other is not None and other != window:
                differ.append('<li%s%s>%s</li>' % (_attrs(code=code, window=_holds(window), whole=_holds(other)), extra, escape(code)))
        out.append('<ul class="basis-differences">\n' + "\n".join(differ) + "\n</ul>" if differ
                   else "<p>no verdict differs between the bases</p>")
    return out


def _mix_caps(verdict) -> str:
    """The "caps (known)" cell: N of F fights capped; a known cap (sweep.KNOWN_CAP) adds its reason, fight index and seed (seed = index // 2).
    The verdict may have been through JSON: roster keys are strings."""
    text = "%d of %d" % (verdict["caps"], verdict["fights"])
    if verdict["reason"] and verdict["reason"].startswith("known_cap:"):
        text += ", " + verdict["reason"] + "".join(", fight %d seed %d" % (int(i), int(i) // 2) for i in verdict["rosters"])
    return text


def _mixes(mixes) -> list:
    """The mixes section: one row per mirror_precheck verdict (R1), the caps column naming M9's known cap."""
    out = ["<table>", "<tr><th>mix</th><th>units</th><th>result</th><th>caps (known)</th></tr>"]
    for name, v in mixes.items():
        units = ", ".join("%s %s" % (t, n) for t, n in (v.get("mix") or {}).items())
        result = ("ok" if v["ok"] else "rejected") + (", " + v["reason"] if v["reason"] else "")
        out.append("<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            _attrs(mix=name), escape(name), escape(units), escape(result), escape(_mix_caps(v))))
    return out + ["</table>"]


def artifact(summary, rows, setup_for, out_dir, title="Skill lab artifact", thresholds=None) -> str:
    """artifact.html and diagrams/<id>.svg in out_dir; the page is README section 5: drafts, findings with a diagram each, baseline
    ceilings, agreement, both_wrong fights, refinement, the cone grid and the conditions the CSV rows alone support; with summary["mixes"]
    (sweep.vet_mixes verdicts) a last section, the mixes table with the caps of each mirror pre-check."""
    from scripts.skilllab import charts   # charts imports this module
    rows = list(rows)
    out = Path(os.fspath(out_dir))
    ns = diagram.notables(rows)
    svgs = diagram.render_all(rows, setup_for)
    ceilings = diagram.baseline_ceilings(rows)
    groups = {}
    for r in rows:
        groups.setdefault("%s/%s" % (r["family"], r["play"]), []).append(r["agreement"])
    wrong = [n for n in ns if n.kind == "both_wrong"]
    sections = {
        "drafts": _drafts(summary, rows),
        "findings": _findings(summary, rows, ns, svgs),
        "baseline-ceiling": ['<ul>'] + ['<li%s>baseline_ceiling: %s, the baseline beat every enemy size at %s</li>' % (
            _attrs(role=c["role"], family=c["family"], play=c["play"], layout=c["layout"], point=c["point"], knob=_csv(c["knob_value"])),
            escape(c["role"]), _csv(c["knob_value"])) for c in ceilings] + ["</ul>"] if ceilings else ["<p>no baseline_ceiling</p>"],
        "agreement": [charts.agreement_html(groups), _called(rows)],
        "both-wrong": ['<ul>'] + ['<li%s>%s | outcome %s | predicted_count %s | predicted_type %s | firing_window_0 %s | firing_window_1 %s</li>'
                                  % (_attrs(row=n.row), escape(_sentence(n, rows).split(":")[0]), *(escape(_csv(rows[n.row][c])) for c in (
                                      "outcome", "predicted_count", "predicted_type", "firing_window_0", "firing_window_1")))
                                  for n in wrong] + ["</ul>"] if wrong else ["<p>no both_wrong fight</p>"],
        "refinement": [charts.refinement_html(summary.get("families", {}))],
        "cone-grid": [charts.cone_grid_html(rows) or "<p>no cone family</p>"],
        "conditions": _conditions(rows, thresholds),
    }
    if "mixes" in summary:
        sections["mixes"] = _mixes(summary["mixes"])
    body = ["<h1>%s</h1>" % escape(title)]
    for name in ARTIFACT_SECTIONS + (("mixes",) if "mixes" in summary else ()):
        body += ['<section id="%s">' % name, "<h3>%s</h3>" % name.replace("-", " ")] + sections[name] + ["</section>"]
    out.mkdir(parents=True, exist_ok=True)
    diagram.write_all(rows, setup_for, out / "diagrams")
    path = out / "artifact.html"
    path.write_text(_html(title, body), encoding="utf-8")
    return str(path)
