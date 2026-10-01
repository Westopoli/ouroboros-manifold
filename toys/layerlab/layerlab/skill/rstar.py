"""R*: the enemy-to-skilled force ratio at which the skilled side's margin crosses zero (SPEC.md section 14.1)."""
from dataclasses import dataclass

from .fight import run_fights

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
    if not fitted or fitted[0] <= 0 or fitted[-1] > 0:
        return None
    for i in range(1, len(fitted)):
        if fitted[i] <= 0:
            y0, y1 = fitted[i - 1], fitted[i]
            return xs[i - 1] + y0 / (y0 - y1) * (xs[i] - xs[i - 1])
    return None


def _mean(v):
    return sum(v) / len(v)


def _measure(build, ratios, seeds, processes, lib):
    """Run both labels and every seed at each ratio; a ratio `build` rejects is skipped."""
    jobs, slots, skipped = [], [], []
    for r in ratios:
        try:
            scns = (build(r, False), build(r, True))
        except ValueError:
            skipped.append(r)
            continue
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
        points.append({
            "ratio": r, "value": (_mean(a) - _mean(b)) / 2.0,
            "margin_A_label": _mean(a), "margin_B_label": _mean(b),
            "n_stalemate": sum(fr.outcome == "stalemate" for _, fr in rows),
            "n_no_contact": sum(not fr.contact for _, fr in rows),
        })
    return points, skipped, len(jobs)


def _solve(build, ratios, seeds, refine, processes, lib, viol_tol):
    scan, skipped, fights = _measure(build, ratios, seeds, processes, lib)
    scan.sort(key=lambda p: p["ratio"])
    points = list(scan)
    pos = [i for i, p in enumerate(scan) if p["value"] > 0]
    if pos and pos[-1] + 1 < len(scan):
        lo, hi = scan[pos[-1]]["ratio"], scan[pos[-1] + 1]["ratio"]
        for _ in range(refine):
            mid = (lo + hi) / 2.0
            new, skip, n = _measure(build, (mid,), seeds, processes, lib)
            fights += n
            skipped += skip
            if new and new[0]["value"] > 0:
                lo = mid
            else:
                hi = mid
            points += new
    points.sort(key=lambda p: p["ratio"])
    xs = [p["ratio"] for p in points]
    vals = [p["value"] for p in points]
    fitted = isotonic_nonincreasing(xs, vals)
    value = zero_crossing(xs, fitted)
    above = bool(fitted) and value is None and fitted[-1] > 0
    below = bool(fitted) and value is None and not above
    violation = max([b - a for a, b in zip(vals, vals[1:]) if b > a], default=0.0)
    scan_max = max((p["ratio"] for p in scan), default=None)
    losses = [p["ratio"] for p in scan if p["value"] < 0]
    wins = [p["ratio"] for p in scan if p["value"] > 0]
    return RStar(
        value=value, above_scan=above, below_scan=below, points=points,
        first_loss=min(losses, default=None), last_win=max(wins, default=None),
        violation=violation, monotonic=violation <= viol_tol, rerun=False, valid=violation <= viol_tol,
        skipped_ratios=skipped, scan_max=scan_max,
        short_scan=above and scan_max is not None and scan_max <= _TARGET_SCAN,
        label_gap=max((abs(p["margin_A_label"] + p["margin_B_label"]) for p in points), default=0.0),
        fights=fights,
    )


def rstar(build, ratios=RATIOS, seeds=(0, 1), refine=4, processes=None, lib="O2", viol_tol=0.15):
    res = _solve(build, ratios, seeds, refine, processes, lib, viol_tol)
    if res.monotonic:
        return res
    again = _solve(build, ratios, tuple(s + _RERUN_SHIFT for s in seeds), refine, processes, lib, viol_tol)
    again.rerun = True
    again.fights += res.fights
    return again
