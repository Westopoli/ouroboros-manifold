"""Chart forms: regions, the two-settings region map and small multiples (inline SVG fragments).

Spec: docs/northstar/research/layer_dynamics/README.md section 5. Counts not ratios, one common scale,
no log scale, no dual axes, small multiples not animation.
"""
from __future__ import annotations

from html import escape

from scripts.skilllab import diagram
from scripts.skilllab.contract import ScanResult
from scripts.skilllab.evidence import AGREEMENTS, agreement_counts
from scripts.skilllab.report import CSS, _n, _scale, _text

EXTRA = """
.legend{font-size:.85rem;color:var(--muted);margin:.3rem 0}
.legend .key{display:inline-block;width:.9em;height:.9em;margin:0 .3em 0 .8em;vertical-align:middle}
.key.holds,.cell.holds{fill:var(--won);background:var(--won)}
.key.fails,.cell.fails{fill:var(--lost);background:var(--lost)}
.cell.fails{opacity:.55}
.multiples{display:grid;grid-template-columns:repeat(2,1fr);gap:.6rem}
"""
MW, MH = 640, 360
MX0, MX1, MY0, MY1 = 70, 620, 20, 300
PW, PH = 320, 90
PX0, PX1, PCY = 16, PW - 16, 52


def _num(v) -> str:
    return str(int(v)) if float(v) == int(v) else format(v, "g")


def _grid(cells):
    xs = sorted({c["x"] for c in cells})
    ys = sorted({c["y"] for c in cells})
    seen = {(c["x"], c["y"]) for c in cells}
    if len(seen) != len(cells) or len(seen) != len(xs) * len(ys):
        raise ValueError("cells must cover every (x, y) pair of the grid exactly once")
    return xs, ys


def regions(cells) -> list:
    xs, ys = _grid(cells)
    xi, yi = {v: i for i, v in enumerate(xs)}, {v: i for i, v in enumerate(ys)}
    holds = {(xi[c["x"]], yi[c["y"]]) for c in cells if c["holds"]}
    seen, out = set(), []
    for start in sorted(holds, key=lambda p: (xs[p[0]], ys[p[1]])):
        if start in seen:
            continue
        seen.add(start)
        stack, comp = [start], []
        while stack:
            i, j = stack.pop()
            comp.append((xs[i], ys[j]))
            for n in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
                if n in holds and n not in seen:
                    seen.add(n)
                    stack.append(n)
        out.append(sorted(comp))
    return out


def _page(title, body) -> str:
    head = f"<h1>{escape(title)}</h1>\n" if title else ""
    return f"<style>{CSS}{EXTRA}</style>\n{head}{body}\n"


def _axis(values, p0, p1):
    """Return (centre of a value, cell extent) on a linear scale padded by half a cell."""
    gap = min(b - a for a, b in zip(values, values[1:]))
    k = (p1 - p0) / (values[-1] - values[0] + gap)
    return (lambda v: p0 + gap * k / 2 + (v - values[0]) * k), gap * k


def region_map_html(cells, x_name, y_name, title=None) -> str:
    xs, ys = _grid(cells)
    if len(xs) < 2 or len(ys) < 2:
        raise ValueError("each axis needs at least 2 distinct values")
    marks = {"failing" in c for c in cells}
    if len(marks) > 1:
        raise ValueError("failing must be on every cell or on none")
    counted = marks == {True}
    cx, w = _axis(xs, MX0, MX1)
    cy_, h = _axis(ys, MY0, MY1)
    cy = lambda v: MY1 + MY0 - cy_(v)          # larger value, smaller y
    regs = regions(cells)
    parts = [f'<svg viewBox="0 0 {MW} {MH}" role="img">']
    for c in sorted(cells, key=lambda c: (c["x"], c["y"])):
        cls = "cell holds" if c["holds"] else "cell fails"
        parts.append(f'<rect class="{cls}" x="{_n(cx(c["x"]) - w / 2)}" y="{_n(cy(c["y"]) - h / 2)}" '
                     f'width="{_n(w)}" height="{_n(h)}"/>')
    for v in xs:
        parts.append(_text(cx(v), MY1 + 16, _num(v), "muted", "middle"))
    for v in ys:
        parts.append(_text(MX0 - 6, cy(v) + 4, _num(v), "muted", "end"))
    parts.append(_text((MX0 + MX1) / 2, MH - 10, x_name, "muted", "middle"))
    parts.append(_text(12, MY0 - 6, y_name, "muted"))
    if counted:
        for c in cells:
            if not c["holds"]:
                parts.append(f'<text x="{_n(cx(c["x"]))}" y="{_n(cy(c["y"]))}" text-anchor="middle" '
                             f'dominant-baseline="central">{c["failing"]}</text>')
    for n, reg in enumerate(regs, 1):
        parts.append(_text(cx(reg[0][0]), cy(reg[0][1]) + 4, n, "", "middle"))
    parts.append("</svg>")
    held = sum(c["holds"] for c in cells)
    r = len(regs)
    head = (f"<h2>{held} of {len(cells)} settings pairs hold every condition, "
            f"in {r} region{'' if r == 1 else 's'}</h2>")
    legend = ('<p class="legend"><span class="key holds"></span>holds every condition'
              '<span class="key fails"></span>fails at least one'
              + ("; number = conditions failing" if counted else "") + "</p>")
    rows = ["<tr><th>Region</th><th>Settings pairs</th><th>In words</th></tr>"]
    for n, reg in enumerate(regs, 1):
        rx, ry = [p[0] for p in reg], [p[1] for p in reg]
        words = f"x from {_num(min(rx))} to {_num(max(rx))}, y from {_num(min(ry))} to {_num(max(ry))}"
        rows.append(f"<tr><td>{n}</td><td>{len(reg)}</td><td>{escape(words)}</td></tr>")
    table = '<table class="words">\n' + "\n".join(rows) + "\n</table>"
    return _page(title, "\n".join([head] + parts + [legend, table]))


def small_multiples_html(panels, title=None) -> str:
    if not 2 <= len(panels) <= 12:
        raise ValueError("small multiples need 2 to 12 panels")
    if any(not sc.cells for _, sc in panels):
        raise ValueError("every panel needs at least one cell")
    heads = [c.enemy_heads for _, sc in panels for c in sc.cells]
    lo, hi = min(heads), max(heads)
    xof = lambda n: _scale(n, lo, hi, PX0, PX1)
    svgs, rows = [], ["<tr><th>Panel</th><th>Beats</th><th>Loses to</th></tr>"]
    for label, sc in panels:
        cells = sorted(sc.cells, key=lambda c: c.enemy_heads)
        s = [f'<svg viewBox="0 0 {PW} {PH}" role="img">', _text(PX0, 14, label)]
        if sc.ceiling_hit:
            s.append(_text(PX1, 14, "ceiling hit", "ceiling", "end"))
        elif sc.beats is not None and sc.loses_to is not None:
            mx = (xof(sc.beats) + xof(sc.loses_to)) / 2
            s.append(f'<line class="marker" x1="{_n(mx)}" x2="{_n(mx)}" y1="22" y2="68"/>')
        else:
            s.append(_text(PX1, 14, "no break-even in range", "muted", "end"))
        for c in cells:
            s.append(f'<circle class="{"cell defect" if c.defect else "cell won" if c.won else "cell lost"}" '
                     f'cx="{_n(xof(c.enemy_heads))}" cy="{PCY}" r="4"/>')
            s.append(_text(xof(c.enemy_heads), PH - 6, c.enemy_heads, "muted", "middle"))
        s.append("</svg>")
        svgs.append("\n".join(s))
        won = [c.enemy_heads for c in cells if c.won]
        beats = sc.beats if sc.beats is not None else (max(won) if won else None)
        rows.append(f"<tr><td>{escape(str(label))}</td><td>{'none' if beats is None else beats}</td>"
                    f"<td>{'ceiling hit' if sc.ceiling_hit else 'none' if sc.loses_to is None else sc.loses_to}</td></tr>")
    head = f"<h2>{len(panels)} panels, same enemy headcounts on every panel</h2>"
    table = '<table class="words">\n' + "\n".join(rows) + "\n</table>"
    return _page(title, "\n".join([head, '<div class="multiples">'] + svgs + ["</div>", table]))


def _table(rows, cls="words", attrs=""):
    return f'<table class="{cls}"{attrs}>\n' + "\n".join(rows) + "\n</table>"


def refinement_html(entries, title=None) -> str:
    rows = ["<tr><th>Family</th><th>Refined between the coarse points</th></tr>"]
    for family, e in entries.items():
        if e.get("skipped"):
            words = "skipped: " + e["skipped"]
        else:
            clauses = [f"{role}: " + (", ".join(format(v, "g") for v in sorted(values)) if values else "no crossing")
                       for role, values in e.get("refined_vs", {}).items()]
            words = "; ".join(clauses) if clauses else "no crossing"
        rows.append(f"<tr><td>{escape(str(family))}</td><td>{escape(words)}</td></tr>")
    return _page(title, _table(rows))


def agreement_html(groups, title=None) -> str:
    rows = ["<tr><th>Group</th>" + "".join(f"<th>{w}</th>" for w in AGREEMENTS) + "<th>Fights</th></tr>"]
    for label, words in groups.items():
        counts = agreement_counts(words)
        cells = "".join(f'<td class="finding">{n}</td>' if w == "both_wrong" and n else f"<td>{n}</td>" for w, n in counts.items())
        rows.append(f"<tr><td>{escape(str(label))}</td>{cells}<td>{sum(counts.values())}</td></tr>")
    return _page(title, _table(rows))


def _signed(v) -> str:
    return f"{v:+d}" if v else "0"


def cone_grid_html(rows, title=None) -> str:
    rows = [r for r in rows if r.get("family") == "cone" and r.get("kind") in diagram.SCAN_KINDS]
    index = diagram._index(rows)
    tables = {}
    for (family, play, layout, point), by_role in index.items():
        for role in by_role:
            if role != "none" and "none" in by_role:
                tables.setdefault((play, layout, role), {})[point] = (by_role["none"], by_role[role])
    out = []
    for (play, layout, role), series in sorted(tables.items()):
        points = sorted(series, key=lambda p: (float(p.split("=")[-1]) if "=" in p else 0.0, p))
        ranges = sorted({k for p in points for scans in series[p] for k in scans})
        head = "<tr><th>Range</th>" + "".join(f"<th>{escape(p)}</th>" for p in points) + "</tr>"
        body = []
        for rng in ranges:
            cells = []
            for p in points:
                ours, theirs = series[p]
                if rng in ours and rng in theirs:
                    gain = diagram.break_even(rows, ours[rng]) - diagram.break_even(rows, theirs[rng])
                    cells.append(f'<td data-range="{format(rng, "g")}" data-point="{escape(p)}" data-gain="{gain}">{_signed(gain)}</td>')
                else:
                    cells.append(f'<td data-range="{format(rng, "g")}" data-point="{escape(p)}" data-gain="">-</td>')
            body.append(f'<tr><th>{format(rng, "g")}</th>{"".join(cells)}</tr>')
        out.append(_table([head] + body, "words cone-grid",
                          f' data-play="{escape(play)}" data-layout="{escape(layout)}" data-role="{escape(role)}"'))
    return _page(title, "\n".join(out)) if out else ""
