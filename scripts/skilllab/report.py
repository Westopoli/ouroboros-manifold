"""report(batch, out_dir): one self-contained HTML page (inline SVG, standard library only).

Spec: docs/northstar/plans/skilllab-harness-spec.md AC 18-19.
"""
from __future__ import annotations

import os
from html import escape
from pathlib import Path

from scripts.skilllab.contract import Batch, ScanResult

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
    if scan.beats is not None:
        pos = {c.enemy_heads: xof(c.enemy_heads) for c in cells}
        if scan.beats in pos and scan.beats + 1 in pos:
            mx = (pos[scan.beats] + pos[scan.beats + 1]) / 2
            parts.append(f'<line class="marker" x1="{_n(mx)}" x2="{_n(mx)}" y1="{PY0}" y2="{PY1}"/>')
            parts.append(_text(mx, PY0 - 6, f"beats {scan.beats}, loses to {scan.beats + 1}", "", "middle"))
    for c in cells:
        cls = "cell won" if c.won else "cell lost"
        parts.append(f'<circle class="{cls}" cx="{_n(xof(c.enemy_heads))}" cy="{_n(yof(c.mean_margin))}" r="5"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def _scan_table(scan: ScanResult) -> str:
    rows = ["<tr><th>Enemy units</th><th>Mean margin</th><th>Result</th><th>In words</th></tr>"]
    for c in sorted(scan.cells, key=lambda c: c.enemy_heads):
        words = f"{scan.size} units {'beat' if c.won else 'lose to'} {c.enemy_heads}"
        rows.append(f"<tr><td>{c.enemy_heads}</td><td>{c.mean_margin:.3f}</td>"
                    f"<td>{'won' if c.won else 'lost'}</td><td>{escape(words)}</td></tr>")
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
    if reach is not None and ident is not None and reach.beats is not None and ident.beats is not None:
        out.append(f"With longer reach, {reach.size} units beat {reach.beats}. Identical sides beat {ident.beats}.")
        plain = [(k, v) for k, v in plain if k not in ("reach", "identical")]
    for label, sc in plain:
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
