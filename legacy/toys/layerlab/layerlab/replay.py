"""Top-down matplotlib replay of a traced run (SPEC.md section 8)."""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgb
from matplotlib.patches import Polygon

from .run import run
from .scenario import to_c

SIDE_COLOURS = ("tab:blue", "tab:red")
MARKERS = {"strike": "^", "line": "s", "siege": "D"}
_DIM = 0.2
_BAR_HALF, _BAR_RISE = 30.0, 38.0


def _categories(scn):
    defaults = scn.get("type_defaults", {})
    out = []
    for g in scn.get("groups", []):
        cat = {**defaults, **scn["types"][g["type"]]}["category"]
        out += [cat] * int(g["count"])
    return out


def _slope_artists(ax, scn):
    try:
        terr = to_c(scn).terrain
    except NotImplementedError:
        return
    for i in range(terr.n_slope):
        s = terr.slope[i]
        d = np.array([s.dx, s.dy]) / np.hypot(s.dx, s.dy)
        nrm = np.array([-d[1], d[0]]) * s.width / 2
        p0 = np.array([s.x0, s.y0])
        p1 = p0 + d * s.length
        ax.add_patch(Polygon([p0 + nrm, p1 + nrm, p1 - nrm, p0 - nrm], closed=True, facecolor="tab:olive",
                             alpha=0.25, edgecolor="tab:olive", zorder=0))
        n = s.top_layer - s.bottom_layer
        for k in range(1, n + 1):
            c = p0 + d * s.length * (k - 0.5) / n
            ax.plot(*zip(c + nrm, c - nrm), color="tab:olive", linestyle="--", linewidth=1, zorder=0)


def replay(scn, trace=None, seed=0, lib="O2"):
    if trace is None:
        trace = run(scn, seed=seed, trace=True, lib=lib).trace
    ticks, n = trace.shape
    cats = _categories(scn)
    if len(cats) != n:
        raise ValueError("trace has %d units, scenario spawns %d" % (n, len(cats)))
    max_hp = np.maximum(trace["hp"].max(axis=0), 1e-9)
    terr = scn.get("terrain", {})
    width = float(terr.get("w_cells", 80)) * float(terr.get("cell", 50.0))
    height = float(terr.get("h_cells", 40)) * float(terr.get("cell", 50.0))

    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=70)
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    _slope_artists(ax, scn)

    groups = {}
    for cat in dict.fromkeys(cats):
        idx = np.array([i for i, c in enumerate(cats) if c == cat])
        groups[cat] = (idx, ax.scatter([], [], marker=MARKERS[cat], s=40, linewidths=1.5, zorder=3))
    bars_back = LineCollection([], colors="0.25", linewidths=2, zorder=2)
    bars_fill = LineCollection([], colors="tab:green", linewidths=2, zorder=2)
    ax.add_collection(bars_back)
    ax.add_collection(bars_fill)
    label = ax.text(0.01, 0.98, "", transform=ax.transAxes, va="top", fontsize=8)
    state = {"layer": None, "frame": 0}

    def update(f):
        state["frame"] = f
        fr = trace[f]
        alive = fr["alive"] != 0
        hollow = (fr["flags"] & 1) != 0
        dim = np.zeros(n, bool) if state["layer"] is None else fr["layer"] != state["layer"]
        alpha = np.where(alive, np.where(dim, _DIM, 1.0), 0.0)
        colours = np.array([to_rgb(SIDE_COLOURS[s % 2]) for s in fr["side"]])
        for idx, sc in groups.values():
            rgba = np.column_stack([colours[idx], alpha[idx]])
            sc.set_offsets(np.column_stack([fr["x"][idx], fr["y"][idx]]))
            sc.set_edgecolors(rgba)
            sc.set_facecolors(np.where(hollow[idx][:, None], 0.0, rgba))
        up = alive & ~dim
        x, y = fr["x"][up].astype(float), fr["y"][up].astype(float) + _BAR_RISE
        frac = np.clip(fr["hp"][up] / max_hp[up], 0.0, 1.0)
        bars_back.set_segments([[(a - _BAR_HALF, b), (a + _BAR_HALF, b)] for a, b in zip(x, y)])
        bars_fill.set_segments([[(a - _BAR_HALF, b), (a - _BAR_HALF + 2 * _BAR_HALF * k, b)]
                                for a, b, k in zip(x, y, frac)])
        layer = "all layers" if state["layer"] is None else "layer %d" % state["layer"]
        label.set_text("tick %d/%d   %s (keys 1-5, 0 clears)" % (f + 1, ticks, layer))

    def on_key(event):
        if event.key in ("1", "2", "3", "4", "5"):
            pick = int(event.key)
            state["layer"] = None if state["layer"] == pick else pick
        elif event.key == "0":
            state["layer"] = None
        else:
            return
        update(state["frame"])
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("key_press_event", on_key)
    return FuncAnimation(fig, update, frames=ticks, interval=50, blit=False, repeat=False,
                         cache_frame_data=False)


def save_gif(anim, path):
    anim.save(str(path), writer=PillowWriter(fps=20))
