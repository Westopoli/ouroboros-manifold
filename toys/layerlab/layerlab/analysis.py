"""Firing-share analysis (README 6.1, SPEC.md section 8): predict a winner from how often each side
could fire, and check that prediction against actual runs."""
from dataclasses import dataclass

from .ffi import WIN_A, WIN_B
from .run import run

_TIE_EPS = 1e-9


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

    @property
    def text(self):
        decided = self.wins_A + self.wins_B
        span = "%d..%d" % (self.seeds[0], self.seeds[-1]) if self.seeds else "none"
        rows = [("count-only", self.agree_count, self.tied_count),
                ("type-weighted", self.agree_weighted, self.tied_weighted)]
        lines = ["firing-share check: seeds %s (%d runs)  wins A %d  B %d  other %d  mean f A %.3f  B %.3f"
                 % (span, len(self.seeds), self.wins_A, self.wins_B, self.other, self.mean_f_A, self.mean_f_B),
                 "%-14s %6s %8s %6s" % ("predictor", "agree", "of", "tied")]
        lines += ["%-14s %6d %8d %6d" % (name, agree, decided, tied) for name, agree, tied in rows]
        return "\n".join(lines)


def check(scn, seeds, lib="O2"):
    seeds = tuple(range(seeds)) if isinstance(seeds, int) else tuple(seeds)
    wins_a = wins_b = other = 0
    agree = [0, 0]
    tied = [0, 0]
    sum_a = sum_b = 0.0
    for seed in seeds:
        res = run(scn, seed=seed, lib=lib)
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
    n = len(seeds)
    return CheckTable(wins_A=wins_a, wins_B=wins_b, other=other, agree_count=agree[0],
                      agree_weighted=agree[1], tied_count=tied[0], tied_weighted=tied[1],
                      mean_f_A=sum_a / n if n else 0.0, mean_f_B=sum_b / n if n else 0.0, seeds=seeds)
