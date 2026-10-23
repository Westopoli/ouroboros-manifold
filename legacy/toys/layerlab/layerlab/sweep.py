"""Parameter sweeps over scenario paths (SPEC.md section 8)."""
import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np

from . import log as _log
from .ffi import LAB, WIN_A, WIN_B, WIN_CAP, WIN_STALEMATE
from .run import run
from .scenario import load, scenario_diff, set_path

_METRICS = {
    "win_rate": None,
    "hp_ratio_A": lambda r: r.hp_ratio[0],
    "hp_ratio_B": lambda r: r.hp_ratio[1],
    "ticks": lambda r: float(r.ticks),
    "unanswered_A": lambda r: float(r.unanswered_ticks[0]),
    "unanswered_B": lambda r: float(r.unanswered_ticks[1]),
    "cost_lost_A": lambda r: r.cost_lost[0],
    "cost_lost_B": lambda r: r.cost_lost[1],
}
# Crossings of level 0.5 mean something only for metrics bounded by [0, 1].
_UNIT_METRICS = {"win_rate", "hp_ratio_A", "hp_ratio_B"}
_WINNER = {"A": WIN_A, "B": WIN_B}


@dataclass
class SweepTable:
    var: str
    values: list
    var2: Any
    values2: Any
    metric: str
    expect: str
    seeds: list
    mean: list
    per_seed: np.ndarray
    stalemates: list
    caps: list
    crossings: list
    png: str
    text: str


def find_crossings(xs, ys, level=0.5):
    out = []
    at_level = False
    for i in range(len(ys)):
        s = ys[i] - level
        if s == 0:
            if not at_level:
                out.append(float(xs[i]))
            at_level = True
            continue
        at_level = False
        if i and (ys[i - 1] - level) * s < 0:
            x0, x1, y0, y1 = xs[i - 1], xs[i], ys[i - 1], ys[i]
            out.append(float(x0 + (level - y0) * (x1 - x0) / (y1 - y0)))
    return out


def _headless():
    if matplotlib.rcParams._get_backend_or_none() is None:
        matplotlib.use("Agg")


def _fmt(x):
    return "%g" % x


def _cell_stats(results, expect):
    win = _WINNER[expect]
    return (
        [float(r.winner == win) for r in results],
        sum(r.winner == WIN_STALEMATE for r in results),
        sum(r.winner == WIN_CAP for r in results),
    )


def _table_text(var, values, var2, values2, metric, expect, seeds, mean, stalemates, caps, crossings):
    head = "sweep %s%s  metric=%s  expect=%s  seeds=%d..%d (%d)" % (
        var, " x " + var2 if var2 else "", metric, expect, min(seeds), max(seeds), len(seeds))
    lines = [head]
    if var2 is None:
        w = max([len(var), 5] + [len(_fmt(v)) for v in values])
        lines.append("%-*s %12s %11s %5s" % (w, "value", metric, "stalemates", "caps"))
        for v, m, s, c in zip(values, mean, stalemates, caps):
            lines.append("%-*s %12.3f %11d %5d" % (w, _fmt(v), m, s, c))
        if crossings:
            lines.append("crossings of 0.5: " + ", ".join("%.3f" % x for x in crossings))
    else:
        lines.append("rows: %s   columns: %s   cells: mean %s" % (var, var2, metric))
        w = max([5] + [len(_fmt(v)) for v in values])
        cw = max([9] + [len(_fmt(v)) for v in values2])
        lines.append("%-*s" % (w, "") + "".join(" %*s" % (cw, _fmt(v)) for v in values2))
        for i, v in enumerate(values):
            lines.append("%-*s" % (w, _fmt(v)) + "".join(" %*.3f" % (cw, m) for m in mean[i]))
        lines.append("stalemates %d  caps %d (all cells)" % (sum(map(sum, stalemates)), sum(map(sum, caps))))
        for v2, cx in zip(values2, crossings):
            if cx:
                lines.append("crossings of 0.5 at %s=%s: %s" % (var2, _fmt(v2), ", ".join("%.3f" % x for x in cx)))
    return "\n".join(lines) + "\n"


def _plot(path, var, values, var2, values2, metric, expect, seeds, mean, per_seed, crossings, title):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=100)
    if var2 is None:
        xs = np.asarray(values, dtype=float)
        ax.scatter(np.repeat(xs, len(seeds)), per_seed.reshape(-1), s=10, alpha=0.35, color="tab:gray",
                   label="per seed")
        ax.plot(xs, mean, "-o", color="tab:blue", label="mean")
        for x in crossings:
            ax.axvline(x, color="tab:red", linestyle=":", linewidth=1)
        ax.set_xlabel(var)
        ax.set_ylabel(metric)
        ax.legend(loc="best")
    else:
        m = np.asarray(mean, dtype=float).T
        im = ax.imshow(m, origin="lower", aspect="auto", cmap="viridis")
        ax.set_xticks(range(len(values)), [_fmt(v) for v in values])
        ax.set_yticks(range(len(values2)), [_fmt(v) for v in values2])
        ax.set_xlabel(var)
        ax.set_ylabel(var2)
        fig.colorbar(im, ax=ax, label=metric)
        if m.size <= 100:
            for (j, i), v in np.ndenumerate(m):
                ax.text(i, j, "%.2f" % v, ha="center", va="center", color="white", fontsize=7)
    ax.set_title(title, fontsize=9)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _png_path(out_dir, var, var2, metric):
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = "".join(c if c.isalnum() else "_" for c in var + ("_x_" + var2 if var2 else "")).strip("_")
    stem = "sweep_%s_%s_%s" % (datetime.datetime.now().strftime("%Y%m%d-%H%M%S"), slug, metric)
    path, n = out_dir / (stem + ".png"), 1
    while path.exists():
        n += 1
        path = out_dir / ("%s-%d.png" % (stem, n))
    return path


def sweep(scn, var, values, seeds=range(5), var2=None, values2=None, metric="win_rate", expect="A",
          out_dir=None, log=True, transfer_class=None, title=None, lib="O2"):
    if metric not in _METRICS:
        raise ValueError("unknown metric %r (known: %s)" % (metric, sorted(_METRICS)))
    if expect not in _WINNER:
        raise ValueError("expect must be 'A' or 'B', got %r" % (expect,))
    if log is not False:
        _log.check_class(transfer_class)
    if (var2 is None) != (values2 is None):
        raise ValueError("var2 and values2 go together")
    values, seeds = list(values), list(seeds)
    values2 = list(values2) if var2 is not None else None
    if not values or not seeds or values2 == []:
        raise ValueError("sweep needs at least one value and one seed")
    set_path(scn, var, values[0])
    if var2 is not None:
        set_path(scn, var2, values2[0])
    out_dir = Path(out_dir) if out_dir is not None else LAB / "results"
    extract = _METRICS[metric]

    def cell(s):
        results = [run(s, seed=k, lib=lib) for k in seeds]
        vals, st, cp = _cell_stats(results, expect)
        if extract is not None:
            vals = [extract(r) for r in results]
        return vals, st, cp

    if var2 is None:
        cells = [cell(set_path(scn, var, v)) for v in values]
        per_seed = np.array([c[0] for c in cells], dtype=float)
        stalemates, caps = [c[1] for c in cells], [c[2] for c in cells]
        mean = [float(m) for m in per_seed.mean(axis=-1)]
        crossings = find_crossings(values, mean) if metric in _UNIT_METRICS else []
    else:
        cells = [[cell(set_path(set_path(scn, var, v), var2, v2)) for v2 in values2] for v in values]
        per_seed = np.array([[c[0] for c in row] for row in cells], dtype=float)
        stalemates = [[c[1] for c in row] for row in cells]
        caps = [[c[2] for c in row] for row in cells]
        mean = [[float(m) for m in row] for row in per_seed.mean(axis=-1)]
        crossings = [find_crossings(values, [mean[i][j] for i in range(len(values))])
                     if metric in _UNIT_METRICS else [] for j in range(len(values2))]

    text = _table_text(var, values, var2, values2, metric, expect, seeds, mean, stalemates, caps, crossings)
    print(text, end="")
    _headless()
    png = _png_path(out_dir, var, var2, metric)
    ptitle = title or "%s%s: %s" % (var, " x " + var2 if var2 else "", metric)
    if transfer_class:
        ptitle += "  [%s]" % transfer_class
    _plot(png, var, values, var2, values2, metric, expect, seeds, mean, per_seed,
          crossings if var2 is None else None, ptitle)

    if log is not False:
        command = "sweep var=%s values=%s%s metric=%s expect=%s seeds=%d..%d" % (
            var, values, " var2=%s values2=%s" % (var2, values2) if var2 else "", metric, expect,
            min(seeds), max(seeds))
        _log.append({
            "date": datetime.date.today().isoformat(), "command": command,
            "diff": scenario_diff(load(LAB / "scenarios" / "base.toml"), scn),
            "table": text, "png": str(png), "transfer_class": transfer_class, "title": title,
        }, None if log is True else log)

    return SweepTable(var, values, var2, values2, metric, expect, seeds, mean, per_seed,
                      stalemates, caps, crossings, str(png), text)
