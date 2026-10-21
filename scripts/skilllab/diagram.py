"""One SVG per notable layout of a sweep: units by side and layer, walls, covers, the point, a legend, and arrows that mark the CSV
value each assertion comes from (README section 5 output rule: a number without its diagram is not evidence).

Spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::L5; decisions 29, 31, 34. Notables are read from the rows of the
family and smoke CSVs; the layout of each comes from the caller's setup_for(notable).
"""
from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Optional

from scripts.skilllab import contract, formations

CROSSING, CEILING_HIT, BOTH_WRONG = "crossing", "ceiling_hit", "both_wrong"
SCAN_KINDS = ("grid", "refined")
_INT = ("enemy_heads", "ceiling_hit", "ticks", "first_contact_tick", "survivors_0", "survivors_1", "heads_0", "heads_1", "reengage_0", "reengage_1")
_FLOAT = ("margin", "strength_left_0", "strength_left_1", "firing_unit_seconds_0", "firing_unit_seconds_1", "firing_window_0",
          "firing_window_1", "weighted_unit_seconds_0", "weighted_unit_seconds_1", "weighted_window_0", "weighted_window_1", "knob_value", "paper_score_0", "paper_score_1")
OPENING = "DRAFT-opening-window-ticks"
ARC = "DRAFT-firing-arc-deg"
CONE = ("DRAFT-aoe-cone-range", "DRAFT-aoe-cone-deg", "DRAFT-aoe-cone-share")
WINDOW_COLUMNS = ("firing_window_0", "firing_window_1", "weighted_window_0", "weighted_window_1")


def read_rows(path) -> list:
    out = []
    with open(path, newline="", encoding="utf-8") as fh:
        for raw in csv.DictReader(fh):
            row = {}
            for k, v in raw.items():
                if v == "":
                    row[k] = None
                elif k in _INT:
                    row[k] = int(v)
                elif k in _FLOAT:
                    row[k] = float(v)
                else:
                    row[k] = v
            out.append(row)
    return out


def csv_text(v) -> str:
    """The text rows.write_rows puts in the cell."""
    if v is None:
        return ""
    return repr(v) if isinstance(v, float) else str(v)


@dataclass(frozen=True)
class Notable:
    kind: str
    family: str
    play: str
    layout: str
    point: str
    role: str
    knob_lo: float
    knob_hi: float
    heads: int
    row: Optional[int]
    reach: Optional[str] = None   # the rows' `reach` configuration (LAB-REV3-C, R3); None when the rows have no such column

    @property
    def id(self) -> str:
        fields = (self.kind, self.family, self.play, self.layout, self.point, self.role, repr(self.knob_lo), repr(self.knob_hi),
                  str(self.heads), str(self.row)) + (() if self.reach is None else (self.reach,))
        slug = re.sub(r"[^A-Za-z0-9_]+", "_", "-".join(fields[:6]) + "-" + fields[6] + "-" + fields[7])
        return slug + "-" + hashlib.sha1("\x1f".join(fields).encode("utf-8")).hexdigest()[:10]


# ---- scans read from rows ---------------------------------------------------------------------------------------------------------

def _series_key(r):
    return (r["family"], r["play"], r["layout"], r.get("point") or "-", r.get("reach"))


def _index(rows):
    """{series (family, play, layout, point, reach): {baseline: {knob value: {enemy_heads: [row index, ...]}}}} over the grid and refined rows."""
    out = {}
    for i, r in enumerate(rows):
        if r.get("kind") not in SCAN_KINDS or r.get("knob_value") is None:
            continue
        out.setdefault(_series_key(r), {}).setdefault(r["baseline"], {}).setdefault(r["knob_value"], {}).setdefault(r["enemy_heads"], []).append(i)
    return out


def scan_result(rows, cells):
    """(break-even, first lost headcount after it or None, headcounts ascending) of one scan; cells maps enemy_heads to row indices.
    A cell is won when every row of it is side0. Break-even: the top headcount when every cell is won, else the headcount before the
    first won-to-lost step, else 0 (scan._crossing; a later flip back to won is not read). The first lost headcount is the cell after it."""
    heads = sorted(cells)
    won = [all(rows[i]["outcome"] == "side0" for i in cells[h]) for h in heads]
    if all(won):
        return heads[-1], None, heads
    for j in range(len(heads) - 1):
        if won[j] and not won[j + 1]:
            return heads[j], heads[j + 1], heads
    return 0, heads[0], heads


def break_even(rows, cells) -> int:
    return scan_result(rows, cells)[0]


def _crossings(rows, index):
    out = []
    for (family, play, layout, point, reach), by_role in index.items():
        ours = by_role.get("none")
        if not ours:
            continue
        for role, theirs in by_role.items():
            if role == "none":
                continue
            knobs = sorted(set(ours) & set(theirs))
            ahead = {k: break_even(rows, ours[k]) - break_even(rows, theirs[k]) > 0 for k in knobs}
            for lo, hi in zip(knobs, knobs[1:]):
                if ahead[lo] != ahead[hi]:
                    where = lo if ahead[lo] else hi
                    out.append(Notable(CROSSING, family, play, layout, point, role, lo, hi, break_even(rows, ours[where]), None, reach))
    return out


def _ceiling_rows(rows, baseline_is_none):
    """{(series key, role, knob value): [row indices]} of the grid and refined rows that carry ceiling_hit 1."""
    out = {}
    for i, r in enumerate(rows):
        if r.get("kind") in SCAN_KINDS and r.get("ceiling_hit") == 1 and r.get("knob_value") is not None \
                and (r["baseline"] == "none") == baseline_is_none:
            out.setdefault((_series_key(r), r["baseline"], r["knob_value"]), []).append(i)
    return out


def notables(rows) -> list:
    rows = list(rows)
    crossings = sorted(_crossings(rows, _index(rows)), key=lambda n: (n.family, n.play, n.layout, n.point, n.reach or "", n.role, n.knob_lo))
    ceilings = []
    for ((family, play, layout, point, reach), role, knob), idx in _ceiling_rows(rows, True).items():
        ceilings.append(Notable(CEILING_HIT, family, play, layout, point, role, knob, knob, max(rows[i]["enemy_heads"] for i in idx), None, reach))
    ceilings.sort(key=lambda n: (n.family, n.play, n.layout, n.point, n.reach or "", n.knob_lo))
    wrong = [Notable(BOTH_WRONG, r["family"], r["play"], r["layout"], r.get("point") or "-", r["baseline"], r["knob_value"],
                     r["knob_value"], r["enemy_heads"], i, r.get("reach")) for i, r in enumerate(rows) if r.get("agreement") == "both_wrong"]
    return crossings + ceilings + wrong


def baseline_ceilings(rows) -> list:
    rows = list(rows)
    out = [dict(family=key[0], play=key[1], layout=key[2], point=key[3], role=role, knob_value=knob)
           for key, role, knob in _ceiling_rows(rows, False)]
    return sorted(out, key=lambda d: (d["family"], d["play"], d["layout"], d["point"], d["role"], d["knob_value"]))


def _scan_for(rows, index, n, scan, knob):
    role = "none" if scan == "play" else n.role
    return index[(n.family, n.play, n.layout, n.point, n.reach)][role][knob]


def scan_counts(rows, n) -> list:
    """Per knob value and scan of a crossing: dicts scan ("play" or the role), knob (float), beats, loses_to (None when the scan won
    everywhere), in the order lo play, lo baseline, hi play, hi baseline."""
    rows = list(rows)
    index = _index(rows)
    out = []
    for knob in (n.knob_lo, n.knob_hi):
        for scan in ("play", n.role):
            beats, loses_to, _ = scan_result(rows, _scan_for(rows, index, n, "play" if scan == "play" else "role", knob))
            out.append(dict(scan=scan, knob=knob, beats=beats, loses_to=loses_to))
    return out


# ---- the picture ------------------------------------------------------------------------------------------------------------------

W = 900
MARGIN = 20
MAP_W, MAP_H_MAX = W - 2 * MARGIN, 460
LINE = 15
STYLE = (".diagram{font-family:sans-serif}.diagram text{fill:#1c1b19;font-size:11px;stroke:none}.diagram .bg{fill:#fbfaf7;stroke:none}"
         ".diagram .unit{stroke:#1c1b19;stroke-width:.5}.diagram .unit.side0{fill:#2f5fb3}.diagram .unit.side1{fill:#b36a1f}"
         ".diagram .layer-0{fill-opacity:.3}.diagram .layer-1{fill-opacity:.5}.diagram .layer-2{fill-opacity:.7}"
         ".diagram .layer-3{fill-opacity:.85}.diagram .layer-4,.diagram .layer-5{fill-opacity:1}"
         ".diagram .wall{fill:#6b675f;stroke:#1c1b19;stroke-width:1}.diagram .cover{fill:#9c978c;fill-opacity:.5;stroke:#6b675f}"
         ".diagram .point line{stroke:#1c1b19;stroke-width:2}.diagram .arrow line{stroke:#c0452f;stroke-width:1.2;marker-end:url(#head)}"
         ".diagram .arrow text{fill:#c0452f}.diagram .arrow-play text,.diagram .arrow-baseline text{fill:#2a7f62}"
         ".diagram .arrow-play line,.diagram .arrow-baseline line{stroke:#2a7f62}.diagram .draft{fill:#c0452f;font-style:italic}"
         ".diagram .head{fill:#1c1b19}")


def _f(v) -> str:
    return "%.3f" % v


def _q(v) -> str:
    return escape(str(v), quote=True)


def _positions(setup):
    out = {0: [], 1: []}
    for g in setup.groups:
        out[g.side] += formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)
    return out


def _centroid(pts, fallback):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)) if pts else fallback


def _side(word):
    return 1 if word == "side1" else 0


def _arrows(n, rows, index):
    """[(kind, column, row index, side, label suffix data)] the evidence arrows of one notable, in drawing order."""
    out = []
    if n.kind == CROSSING:
        for knob in (n.knob_lo, n.knob_hi):
            for scan in ("play", "baseline"):
                cells = _scan_for(rows, index, n, scan, knob)
                beats, loses_to, _ = scan_result(rows, cells)
                for h in [beats] * (beats > 0) + [loses_to] * (loses_to is not None):
                    out.append((scan, "enemy_heads", min(cells[h]), "0", "(%s, %s)" % (h, rows[min(cells[h])]["outcome"])))
    elif n.kind == CEILING_HIT:
        idx = _ceiling_rows(rows, True)[((n.family, n.play, n.layout, n.point, n.reach), "none", n.knob_lo)]
        top = max(rows[i]["enemy_heads"] for i in idx)
        out.append(("ceiling", "ceiling_hit", idx[0], "0", None))
        out.append(("ceiling", "enemy_heads", next(i for i in idx if rows[i]["enemy_heads"] == top), "1", None))
    else:
        r = rows[n.row]
        for col in WINDOW_COLUMNS:
            out.append(("window", col, n.row, col[-1], None))
        out.append(("prediction", "predicted_count", n.row, str(_side(r["predicted_count"])), None))
        out.append(("prediction", "predicted_type", n.row, str(_side(r["predicted_type"])), None))
        if r.get("predicted_paper") not in (None, "tie", "no_reach"):
            out.append(("prediction", "predicted_paper", n.row, str(_side(r["predicted_paper"])), None))
        out.append(("outcome", "outcome", n.row, str(_side(r["outcome"])), None))
    return out


def _drafts(n, arrows):
    names = []
    if any(a[0] == "window" for a in arrows):
        names.append((OPENING, "%s = %d ticks" % (OPENING, contract.OPENING_WINDOW_TICKS)))
    if n.family == "arc":
        names.append((ARC, ARC + " (the swept values will retune)"))
    if n.family == "cone":
        names += [(c, c + " (the swept values will retune)") for c in CONE]
    return names


def _title(n):
    words = "%s %s %s" % (n.family, n.play, n.layout)
    if n.point != "-":
        words += " " + n.point
    if n.kind == BOTH_WRONG:
        words += " both_wrong"
    return words


def render(notable, rows, setup) -> str:
    return _render(notable, list(rows), setup, _index(list(rows)))


def _render(n, rows, setup, index) -> str:
    placed = _positions(setup)
    terrain = setup.terrain
    xs, ys = [p[0] for pts in placed.values() for p in pts], [p[1] for pts in placed.values() for p in pts]
    if setup.point is not None:
        xs.append(setup.point[0])
        ys.append(setup.point[1])
    if terrain is not None:
        xs += [0.0, terrain.canvas[0]] + [v for b in terrain.blocks for v in (b.x0, b.x1)]
        ys += [0.0, terrain.canvas[1]] + [v for b in terrain.blocks for v in (b.y0, b.y1)]
        for c in terrain.covers:
            xs += [c.x - c.radius, c.x + c.radius]
            ys += [c.y - c.radius, c.y + c.radius]
    lo_x, hi_x, lo_y, hi_y = min(xs, default=0.0), max(xs, default=1.0), min(ys, default=0.0), max(ys, default=1.0)
    span_x, span_y = max(hi_x - lo_x, 1.0), max(hi_y - lo_y, 1.0)
    scale = min(MAP_W / span_x, MAP_H_MAX / span_y)
    map_w, map_h = span_x * scale, span_y * scale
    left = MARGIN + (MAP_W - map_w) / 2
    arrows = _arrows(n, rows, index)
    drafts = _drafts(n, arrows)
    top = 10 + LINE * len(arrows) + 8
    px = lambda x: left + (x - lo_x) * scale
    py = lambda y: top + (y - lo_y) * scale
    centre = ((lo_x + hi_x) / 2, (lo_y + hi_y) / 2)
    target = {"0": _centroid(placed[0], centre), "1": _centroid(placed[1], centre)}
    legend_top = top + map_h + 24
    legend = ["side 0 (blue)", "side 1 (orange)", "layer: a darker unit is on a higher layer", "wall: a blocked rectangle",
              "point: the shared attack-move point (a cross)", "arrow: marks the CSV value its label gives"]
    height = legend_top + LINE * (len(legend) + len(drafts)) + 10
    out = ['<svg xmlns="http://www.w3.org/2000/svg" class="diagram" role="img" viewBox="0 0 %d %s" id="%s" data-kind="%s" data-family="%s" '
           'data-play="%s" data-layout="%s" data-point="%s" data-role="%s">' % (W, _f(height), _q(n.id), n.kind, _q(n.family), _q(n.play),
                                                                                  _q(n.layout), _q(n.point), _q(n.role)),
           "<title>%s</title>" % escape(_title(n) + ("" if n.kind != BOTH_WRONG or n.role == "none" else " " + n.role)
                                        + (" " + rows[n.row]["kind"] if n.kind == BOTH_WRONG and rows[n.row]["kind"].startswith("control_") else "")),
           "<style>%s</style>" % STYLE,
           '<defs><marker id="head" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path class="head" d="M0,0 L8,4 L0,8 z"/></marker></defs>',
           '<rect class="bg" x="0" y="0" width="%d" height="%s"/>' % (W, _f(height))]
    if terrain is not None:
        for c in terrain.covers:
            out.append('<circle class="cover" data-x="%r" data-y="%r" data-radius="%r" data-height="%d" cx="%s" cy="%s" r="%s"/>'
                       % (c.x, c.y, c.radius, c.height, _f(px(c.x)), _f(py(c.y)), _f(c.radius * scale)))
        for b in terrain.blocks:
            out.append('<rect class="wall" data-x0="%r" data-y0="%r" data-x1="%r" data-y1="%r" data-layer-lo="%d" data-layer-hi="%d" '
                       'x="%s" y="%s" width="%s" height="%s"/>' % (b.x0, b.y0, b.x1, b.y1, b.layer_lo, b.layer_hi, _f(px(b.x0)), _f(py(b.y0)),
                                                                   _f((b.x1 - b.x0) * scale), _f((b.y1 - b.y0) * scale)))
        for gx, gy, gap in _gaps(terrain.blocks):
            out.append('<text class="choke" x="%s" y="%s" text-anchor="middle">gap %d wu</text>' % (_f(px(gx)), _f(py(gy)), round(gap)))
    for g in setup.groups:
        for x, y in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params):
            out.append('<circle class="unit side%d layer-%d" data-side="%d" data-layer="%d" data-unit="%s" data-x="%r" data-y="%r" '
                       'cx="%s" cy="%s" r="4"/>' % (g.side, g.layer, g.side, g.layer, _q(g.unit), x, y, _f(px(x)), _f(py(y))))
    if setup.point is not None:
        x, y = _f(px(setup.point[0])), _f(py(setup.point[1]))
        out.append('<g class="point" data-x="%r" data-y="%r"><line x1="%s" y1="%s" x2="%s" y2="%s"/><line x1="%s" y1="%s" x2="%s" y2="%s"/></g>'
                   % (setup.point[0], setup.point[1], _f(px(setup.point[0]) - 6), y, _f(px(setup.point[0]) + 6), y, x, _f(py(setup.point[1]) - 6),
                      x, _f(py(setup.point[1]) + 6)))
    for i, (kind, column, row, side, label) in enumerate(arrows):
        text = label if label is not None else "%s %s" % (column, csv_text(rows[row][column]))
        draft = OPENING if kind == "window" else None
        if draft:
            text += " DRAFT"
        ty = 10 + LINE * (i + 1) - 4
        tx, tyw = target[side]
        extra = ""
        if n.kind == CROSSING:
            extra = ' data-outcome="%s" data-knob="%s" data-role="%s"' % (_q(rows[row]["outcome"]), csv_text(rows[row]["knob_value"]),
                                                                           _q(rows[row]["baseline"]))
        out.append('<g class="arrow arrow-%s" data-kind="%s" data-column="%s" data-value="%s" data-row="%d" data-target-side="%s" '
                   'data-target-x="%r" data-target-y="%r"%s%s><line x1="%s" y1="%s" x2="%s" y2="%s"/><text x="%d" y="%d">%s</text></g>'
                   % (kind, kind, column, _q(csv_text(rows[row][column])), row, side, tx, tyw, extra,
                      ' data-draft="%s"' % draft if draft else "", _f(MARGIN + 7 * len(text) + 8), _f(ty - 4), _f(px(tx)), _f(py(tyw)),
                      MARGIN, ty, escape(text)))
    out.append('<g class="legend">')
    for i, words in enumerate(legend):
        out.append('<text x="%d" y="%s">%s</text>' % (MARGIN, _f(legend_top + LINE * i), escape(words)))
    for j, (name, words) in enumerate(drafts):
        out.append('<text class="draft" data-draft="%s" x="%d" y="%s">%s</text>' % (name, MARGIN, _f(legend_top + LINE * (len(legend) + j)),
                                                                                    escape(words)))
    out.append("</g></svg>")
    return "\n".join(out)


def _gaps(blocks):
    """(x, y, width) of the gap between two walls that face each other with no third wall between them (the choke)."""
    found = []
    for i, a in enumerate(blocks):
        for b in blocks[i + 1:]:
            for lo, hi in ((a, b), (b, a)):
                if lo.y1 < hi.y0 and min(lo.x1, hi.x1) > max(lo.x0, hi.x0):
                    x0, x1, y0, y1 = max(lo.x0, hi.x0), min(lo.x1, hi.x1), lo.y1, hi.y0
                    gap = y1 - y0
                    pos = ((x0 + x1) / 2, (y0 + y1) / 2)
                elif lo.x1 < hi.x0 and min(lo.y1, hi.y1) > max(lo.y0, hi.y0):
                    x0, x1, y0, y1 = lo.x1, hi.x0, max(lo.y0, hi.y0), min(lo.y1, hi.y1)
                    gap = x1 - x0
                    pos = ((x0 + x1) / 2, (y0 + y1) / 2)
                else:
                    continue
                if not any(c.x0 < x1 and c.x1 > x0 and c.y0 < y1 and c.y1 > y0 for c in blocks):
                    found.append((pos[0], pos[1], gap))
    return found


def render_all(rows, setup_for) -> dict:
    rows = list(rows)
    index = _index(rows)
    return {n.id: _render(n, rows, setup_for(n), index) for n in notables(rows)}


def write_all(rows, setup_for, out_dir) -> list:
    svgs = render_all(rows, setup_for)
    if not svgs:
        return []
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, svg in svgs.items():
        path = out / (name + ".svg")
        path.write_text(svg, encoding="utf-8")
        paths.append(path)
    return paths
