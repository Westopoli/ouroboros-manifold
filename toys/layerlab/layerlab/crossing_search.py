"""Does a variable's 0.5 crossing move, or gain a second crossing, when another variable changes?
(SPEC.md section 8: crossing_search.py; README 6.) Reads only `winner_name` and the `set:` columns
(an error row has no winner_name and is skipped)."""
import math
from dataclasses import dataclass

from .sweep import find_crossings

_SET = "set:"


def _usable(row):
    return row.get("winner_name") is not None


def win_curve(rows, var, expect="A", where=None):
    col = _SET + var
    filters = [(_SET + k, v) for k, v in (where or {}).items()]
    tally = {}
    for row in rows:
        if not _usable(row) or row.get(col) is None:
            continue
        if any(row.get(k) != v for k, v in filters):
            continue
        n_won = tally.setdefault(row[col], [0, 0])
        n_won[0] += 1
        n_won[1] += row["winner_name"] == expect
    return [(x, tally[x][1] / tally[x][0], tally[x][0]) for x in sorted(tally)]


def _se(p, n):
    return math.sqrt(max(p * (1.0 - p), 0.0) / n)


def curve_diagnostics(curve):
    xs = [c[0] for c in curve]
    ps = [c[1] for c in curve]
    steps = []
    for (xl, pl, nl), (xr, pr, nr) in zip(curve, curve[1:]):
        delta = pr - pl
        if abs(delta) > 2.0 * max(_se(pl, nl), _se(pr, nr)):
            steps.append((xl, xr, delta))
    up = sum(d for _, _, d in steps if d > 0)
    down = -sum(d for _, _, d in steps if d < 0)
    if up > down:
        reversals = [s for s in steps if s[2] < 0]
    elif down > up:
        reversals = [s for s in steps if s[2] > 0]
    else:
        reversals = steps
    return {"crossings": find_crossings(xs, ps, 0.5), "non_monotonic": bool(reversals), "reversals": reversals}


@dataclass
class CrossingReport:
    curves: dict
    crossings: dict
    moves: bool
    gains_second: bool
    non_monotonic_by: list
    text: str


def _label(v):
    return "%g" % v if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v)


def _order(v):
    return (0, v, "") if isinstance(v, (int, float)) and not isinstance(v, bool) else (1, 0, str(v))


def crossing_shift(rows, var, by, expect="A", tol=None, min_n=10):
    by_col = _SET + by
    values = sorted({r[by_col] for r in rows if _usable(r) and r.get(by_col) is not None}, key=_order)
    curves, crossings, non_monotonic_by = {}, {}, []
    for v in values:
        curve = [c for c in win_curve(rows, var, expect, where={by: v}) if c[2] >= min_n]
        if not curve:
            continue
        diag = curve_diagnostics(curve)
        curves[v], crossings[v] = curve, diag["crossings"]
        if diag["non_monotonic"]:
            non_monotonic_by.append(v)
    xs = [c[0] for curve in curves.values() for c in curve]
    if tol is None:
        tol = (max(xs) - min(xs)) / 10.0 if xs else 0.0
    firsts = [c[0] for c in crossings.values() if c]
    moves = len(firsts) > 1 and max(firsts) - min(firsts) > tol
    counts = [len(c) for c in crossings.values()]
    gains_second = bool(counts) and max(counts) > min(counts)

    w_by = max([len("by")] + [len(_label(v)) for v in curves])
    cells = {v: " ".join("%.4g" % x for x in crossings[v]) or "-" for v in curves}
    w_x = max([len("crossings")] + [len(c) for c in cells.values()])
    fmt = "%%-%ds  %%-%ds  %%5s  %%-13s" % (w_by, w_x)
    lines = ["crossing shift of %s by %s (expect %s, tol %.4g, min_n %d)" % (var, by, expect, tol, min_n),
             "moves %s  gains_second %s  non_monotonic_by %s"
             % (moves, gains_second, [_label(v) for v in non_monotonic_by] or "none"),
             fmt % ("by", "crossings", "points", "non_monotonic")]
    for v in curves:
        lines.append(fmt % (_label(v), cells[v], len(curves[v]), "yes" if v in non_monotonic_by else "no"))
    return CrossingReport(curves=curves, crossings=crossings, moves=moves, gains_second=gains_second,
                          non_monotonic_by=non_monotonic_by, text="\n".join(lines))
