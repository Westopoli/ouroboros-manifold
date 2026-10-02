"""S5 matchup grid: break-even army sizes per pair of unit types."""
from __future__ import annotations

from html import escape

from scripts.skilllab.report import CSS

_EXTRA = """
.grid td.above{background:var(--won);color:var(--bg)}.grid td.below{background:var(--lost);color:var(--bg)}
.grid td.level,.grid td.none{color:var(--muted)}
"""


def _cls(v, size):
    if v is None:
        return "none"
    return "above" if v > size else "below" if v < size else "level"


def matchup_grid_html(row_names, col_names, cells, size, title=None) -> str:
    if len(set(row_names)) != len(row_names) or len(set(col_names)) != len(col_names):
        raise ValueError("names must be unique")
    for r in row_names:
        for c in col_names:
            if (r, c) not in cells:
                raise ValueError(f"missing pair {(r, c)!r}")
    best = None
    for r in row_names:
        for c in col_names:
            v = cells[(r, c)]
            if v is not None and (best is None or v > best[0]):
                best = (v, r, c)
    if best is None:
        head = "No pair has a break-even in range."
    else:
        head = f"Most lopsided pair: {best[1]} ({size} units) beats up to {best[0]} {best[2]}."
    e = escape
    parts = [f"<style>{CSS}{_EXTRA}</style>"]
    if title:
        parts.append(f"<h1>{e(title)}</h1>")
    parts.append(f"<h2>{e(head)}</h2>")
    parts.append('<table class="grid"><tr><th></th>' + "".join(f"<th>{e(c)}</th>" for c in col_names) + "</tr>")
    for r in row_names:
        tds = "".join(
            f'<td class="{_cls(cells[(r, c)], size)}">{"none" if cells[(r, c)] is None else cells[(r, c)]}</td>'
            for c in col_names)
        parts.append(f"<tr><th>{e(r)}</th>{tds}</tr>")
    parts.append("</table>")
    parts.append('<table class="words">')
    for r in row_names:
        above = [c for c in col_names if _cls(cells[(r, c)], size) == "above"]
        tail = ": " + ", ".join(above) if above else " nothing in range"
        s = f"{r} beats more than its own size against" + tail
        parts.append(f"<tr><td>{e(s)}</td></tr>")
    parts.append("</table>")
    return "\n".join(parts) + "\n"
