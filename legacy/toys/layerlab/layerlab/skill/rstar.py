"""R*: the enemy-to-skilled headcount ratio at which the skilled side's margin crosses the win margin (SPEC.md
sections 14.1 and 14.5)."""
from dataclasses import dataclass

from ..run import run
from .cost import force_cost
from .fight import run_fights
from .margin import effective_margin

RATIOS = (0.5, 0.7, 0.85, 1.0, 1.2, 1.4, 1.7, 2.0, 2.4, 2.9, 3.5, 4.2, 5.0, 6.0, 8.0)
_RERUN_SHIFT = 1000
_TARGET_SCAN = 3.0


@dataclass
class RStar:
    value: float
    above_scan: bool
    below_scan: bool
    points: list
    first_loss: float
    last_win: float
    violation: float
    monotonic: bool
    rerun: bool
    valid: bool
    skipped_ratios: list
    scan_max: float
    short_scan: bool
    label_gap: float
    fights: int
    win_margin: float
    value_cost: float
    firing_adv_at_rstar: float
    firing_adv_equal: float
    last_win_heads: int = None
    first_loss_heads: int = None


def isotonic_nonincreasing(xs, ys):
    """Least-squares non-increasing fit by pool-adjacent-violators; xs only order the points."""
    blocks = []                                   # [sum, count]
    for y in ys:
        blocks.append([float(y), 1])
        while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] < blocks[-1][0] / blocks[-1][1]:
            s, n = blocks.pop()
            blocks[-1][0] += s
            blocks[-1][1] += n
    return [s / n for s, n in blocks for _ in range(n)]


def zero_crossing(xs, fitted):
    """The first x at which `fitted` (non-increasing) goes from above 0 to at or below 0."""
    if not fitted or fitted[0] <= 0 or fitted[-1] > 0:
        return None
    for i in range(1, len(fitted)):
        if fitted[i] <= 0:
            y0, y1 = fitted[i - 1], fitted[i]
            return xs[i - 1] + y0 / (y0 - y1) * (xs[i] - xs[i - 1])
    return None


def _mean(v):
    return sum(v) / len(v)


def _interp(xs, ys, x):
    """Linear interpolation of ys over xs at x; None when x is outside xs or a neighbouring y is None."""
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            y0, y1 = ys[i], ys[i + 1]
            if x == xs[i]:
                return y0
            if x == xs[i + 1]:
                return y1
            if y0 is None or y1 is None:
                return None
            return y0 + (y1 - y0) * (x - xs[i]) / (xs[i + 1] - xs[i])
    return None


def _measure(build, ratios, seeds, processes, lib, size=None):
    """Run both labels and every seed at each ratio; a ratio `build` rejects is skipped. With `size`, each point
    also carries `heads`, the enemy head count (ratio * size)."""
    jobs, slots, skipped, cost_ratio = [], [], [], {}
    for r in ratios:
        try:
            scns = (build(r, False), build(r, True))
        except ValueError:
            skipped.append(r)
            continue
        cost_ratio[r] = _mean([force_cost(scn, 1 - sk) / force_cost(scn, sk)
                               for sk, scn in zip((0, 1), scns)])
        for swap, scn in zip((False, True), scns):
            for seed in seeds:
                jobs.append((scn, seed))
                slots.append((r, swap))
    results = run_fights(jobs, processes=processes, lib=lib) if jobs else []
    by_ratio = {}
    for (r, swap), fr in zip(slots, results):
        if fr.outcome == "error":
            raise ValueError("fight at ratio %g failed: %s" % (r, fr.error))
        by_ratio.setdefault(r, []).append((swap, fr))
    points = []
    for r, rows in by_ratio.items():
        a = [fr.margin for swap, fr in rows if not swap]
        b = [fr.margin for swap, fr in rows if swap]
        sk_fire = _mean([fr.firing_per_head(int(swap)) for swap, fr in rows])
        nv_fire = _mean([fr.firing_per_head(1 - int(swap)) for swap, fr in rows])
        points.append({
            "ratio": r, "value": (_mean(a) - _mean(b)) / 2.0,
            **({} if size is None else {"heads": int(r * size + 0.5)}),
            "margin_A_label": _mean(a), "margin_B_label": _mean(b),
            "n_stalemate": sum(fr.outcome == "stalemate" for _, fr in rows),
            "n_no_contact": sum(not fr.contact for _, fr in rows),
            "cost_ratio": cost_ratio[r],
            "skilled_firing_per_head": sk_fire, "naive_firing_per_head": nv_fire,
            "skilled_alive_ticks": _mean([fr.alive_ticks[int(swap)] for swap, fr in rows]),
            "naive_alive_ticks": _mean([fr.alive_ticks[1 - int(swap)] for swap, fr in rows]),
            "firing_adv": sk_fire / nv_fire if nv_fire else None,
        })
    return points, skipped, len(jobs)


def _solve(build, ratios, seeds, refine, processes, lib, viol_tol, win_margin, size=None):
    if size is not None:
        ratios = [n / size for n in sorted({max(1, int(r * size + 0.5)) for r in ratios})]
    scan, skipped, fights = _measure(build, ratios, seeds, processes, lib, size)
    scan.sort(key=lambda p: p["ratio"])
    points = list(scan)
    pos = [i for i, p in enumerate(scan) if p["value"] > win_margin]
    if pos and pos[-1] + 1 < len(scan):
        lo, hi = scan[pos[-1]]["ratio"], scan[pos[-1] + 1]["ratio"]
        if size is not None:
            lo, hi = scan[pos[-1]]["heads"], scan[pos[-1] + 1]["heads"]
        for _ in range(refine):
            if size is not None and hi - lo < 2:
                break
            mid = (lo + hi) // 2 if size is not None else (lo + hi) / 2.0
            new, skip, n = _measure(build, ((mid / size) if size is not None else mid,), seeds, processes, lib,
                                    size)
            fights += n
            skipped += skip
            if new and new[0]["value"] > win_margin:
                lo = mid
            else:
                hi = mid
            points += new
    points.sort(key=lambda p: p["ratio"])
    xs = [p["ratio"] for p in points]
    vals = [p["value"] for p in points]
    fitted = isotonic_nonincreasing(xs, vals)
    value = zero_crossing(xs, [f - win_margin for f in fitted])
    above = bool(fitted) and value is None and fitted[-1] > win_margin
    below = bool(fitted) and value is None and not above
    violation = max([b - a for a, b in zip(vals, vals[1:]) if b > a], default=0.0)
    scan_max = max((p["ratio"] for p in scan), default=None)
    edge = scan if size is None else points                 # with a size the refined points set the bracket
    losses = [p["ratio"] for p in edge if p["value"] <= win_margin]
    wins = [p["ratio"] for p in edge if p["value"] > win_margin]
    return RStar(
        value=value, above_scan=above, below_scan=below, points=points,
        first_loss=min(losses, default=None), last_win=max(wins, default=None),
        last_win_heads=None if size is None or not wins else int(max(wins) * size + 0.5),
        first_loss_heads=None if size is None or not losses else int(min(losses) * size + 0.5),
        violation=violation, monotonic=violation <= viol_tol, rerun=False, valid=violation <= viol_tol,
        skipped_ratios=skipped, scan_max=scan_max,
        short_scan=above and scan_max is not None and scan_max <= _TARGET_SCAN,
        label_gap=max((abs(p["margin_A_label"] + p["margin_B_label"]) for p in points), default=0.0),
        fights=fights, win_margin=win_margin,
        value_cost=None if value is None else _interp(xs, [p["cost_ratio"] for p in points], value),
        firing_adv_at_rstar=None if value is None else _interp(xs, [p["firing_adv"] for p in points], value),
        firing_adv_equal=next((p["firing_adv"] for p in points if p["ratio"] == 1.0), None),
    )


def rstar(build, ratios=RATIOS, seeds=(0, 1), refine=4, processes=None, lib="O2", viol_tol=0.15,
          win_margin=0.02, size=None):
    """With `size` (the skilled head count) the scan runs over distinct whole enemy head counts and refinement
    bisects integer head counts (SPEC.md 14.5 item 9); without it the ratios are scanned and bisected as given."""
    res = _solve(build, ratios, seeds, refine, processes, lib, viol_tol, win_margin, size)
    if res.monotonic:
        return res
    again = _solve(build, ratios, tuple(s + _RERUN_SHIFT for s in seeds), refine, processes, lib, viol_tol,
                   win_margin, size)
    again.rerun = True
    again.fights += res.fights
    return again


def rstar_windows(build, rs, seeds=(0,), window_ticks=100, lib="O2"):
    """Per-window means of units able to fire and units alive, for the fights either side of the break-even."""
    out = []
    for ratio in (rs.last_win, rs.first_loss):
        if ratio is None:
            continue
        for swap in (False, True):
            scn = build(ratio, swap)
            sk = int(swap)
            for seed in seeds:
                res = run(scn, seed=seed, trace=True, lib=lib)
                tr = res.trace
                side = tr["side"][0]
                fire = (tr["flags"] & 16) != 0
                alive = tr["alive"] != 0
                windows = []
                for start in range(0, len(tr), window_ticks):
                    sl = slice(start, start + window_ticks)
                    windows.append({
                        "skilled_firing": float(fire[sl][:, side == sk].sum(axis=1).mean()),
                        "naive_firing": float(fire[sl][:, side != sk].sum(axis=1).mean()),
                        "skilled_alive": float(alive[sl][:, side == sk].sum(axis=1).mean()),
                        "naive_alive": float(alive[sl][:, side != sk].sum(axis=1).mean()),
                    })
                m = effective_margin(res, scn)[0]
                out.append({"ratio": ratio, "swap": swap, "seed": seed, "margin": -m if swap else m,
                            "windows": windows})
    return out
