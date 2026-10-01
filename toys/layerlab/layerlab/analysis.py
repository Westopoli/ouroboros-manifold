"""Firing-share analysis (README 6.1, SPEC.md section 8): predict a winner from how often each side
could fire, and check that prediction against actual runs."""
from dataclasses import dataclass

from .ffi import WIN_A, WIN_B
from .run import run

_TIE_EPS = 1e-9
_FIRING_BIT = 16


def firing_fraction(result, side, weighted=False):
    alive = result.alive_ticks[side]
    if alive <= 0:
        return 0.0
    num = result.firing_weight[side] if weighted else result.firing_ticks[side]
    return num / alive


def start_counts(scn):
    n = [0, 0]
    for g in scn["groups"]:
        n[0 if g["side"] == "A" else 1] += g["count"]
    return n[0], n[1]


def predict(result, scn, weighted=False):
    n_a, n_b = start_counts(scn)
    f_a = firing_fraction(result, 0, weighted)
    f_b = firing_fraction(result, 1, weighted)
    s_a = f_a * n_a ** 2
    s_b = f_b * n_b ** 2
    if abs(s_a - s_b) <= _TIE_EPS:
        who = "tie"
    else:
        who = "A" if s_a > s_b else "B"
    return {"f_A": f_a, "f_B": f_b, "strength_A": s_a, "strength_B": s_b, "predicted": who}


def predict_early(result, scn, window=40):
    if result.trace is None:
        raise ValueError("predict_early needs a trace: run with trace=True")
    n_a, n_b = start_counts(scn)
    first = result.first_shot_tick
    if first < 0:
        return {"f_A": 0.0, "f_B": 0.0, "strength_A": 0.0, "strength_B": 0.0, "predicted": "none",
                "start": first, "end": first}
    tr = result.trace
    end = min(first + window, len(tr))
    seg = tr[first:end]
    firing = (seg["flags"] & _FIRING_BIT) != 0
    live = (seg["alive"] != 0) | firing
    f = []
    for side in (0, 1):
        on_side = seg["side"] == side
        denom = int((live & on_side).sum())
        f.append(int((firing & on_side).sum()) / denom if denom else 0.0)
    s_a = f[0] * n_a ** 2
    s_b = f[1] * n_b ** 2
    if abs(s_a - s_b) <= _TIE_EPS:
        who = "tie"
    else:
        who = "A" if s_a > s_b else "B"
    return {"f_A": f[0], "f_B": f[1], "strength_A": s_a, "strength_B": s_b, "predicted": who,
            "start": first, "end": end}


@dataclass
class CheckTable:
    wins_A: int
    wins_B: int
    other: int
    agree_count: int
    agree_weighted: int
    tied_count: int
    tied_weighted: int
    mean_f_A: float
    mean_f_B: float
    seeds: tuple
    agree_early: int = 0
    tied_early: int = 0
    none_early: int = 0
    window: int = None

    @property
    def text(self):
        decided = self.wins_A + self.wins_B
        span = "%d..%d" % (self.seeds[0], self.seeds[-1]) if self.seeds else "none"
        rows = [("count-only", self.agree_count, self.tied_count),
                ("type-weighted", self.agree_weighted, self.tied_weighted)]
        if self.window:
            rows.append(("opening-window", self.agree_early, self.tied_early, decided - self.none_early))
        lines = ["firing-share check: seeds %s (%d runs)  wins A %d  B %d  other %d  mean f A %.3f  B %.3f"
                 % (span, len(self.seeds), self.wins_A, self.wins_B, self.other, self.mean_f_A, self.mean_f_B),
                 "%-14s %6s %8s %6s" % ("predictor", "agree", "of", "tied")]
        lines += ["%-14s %6d %8d %6d" % (r[0], r[1], r[3] if len(r) > 3 else decided, r[2]) for r in rows]
        return "\n".join(lines)


def check(scn, seeds, lib="O2", window=40):
    if window is not None and (isinstance(window, bool) or not isinstance(window, int) or window < 0):
        raise ValueError("window must be a non-negative int or None, got %r" % (window,))
    early = bool(window)
    seeds = tuple(range(seeds)) if isinstance(seeds, int) else tuple(seeds)
    wins_a = wins_b = other = 0
    agree = [0, 0]
    tied = [0, 0]
    early_counts = [0, 0, 0]
    sum_a = sum_b = 0.0
    for seed in seeds:
        res = run(scn, seed=seed, lib=lib, trace=early)
        sum_a += firing_fraction(res, 0)
        sum_b += firing_fraction(res, 1)
        actual = {WIN_A: "A", WIN_B: "B"}.get(res.winner)
        if actual == "A":
            wins_a += 1
        elif actual == "B":
            wins_b += 1
        else:
            other += 1
        if actual is None:
            continue
        for k, weighted in enumerate((False, True)):
            who = predict(res, scn, weighted)["predicted"]
            if who == "tie":
                tied[k] += 1
            elif who == actual:
                agree[k] += 1
        if early:
            who = predict_early(res, scn, window)["predicted"]
            if who == "none":
                early_counts[2] += 1
            elif who == "tie":
                early_counts[1] += 1
            elif who == actual:
                early_counts[0] += 1
    n = len(seeds)
    return CheckTable(wins_A=wins_a, wins_B=wins_b, other=other, agree_count=agree[0],
                      agree_weighted=agree[1], tied_count=tied[0], tied_weighted=tied[1],
                      mean_f_A=sum_a / n if n else 0.0, mean_f_B=sum_b / n if n else 0.0, seeds=seeds,
                      agree_early=early_counts[0], tied_early=early_counts[1], none_early=early_counts[2],
                      window=window)
