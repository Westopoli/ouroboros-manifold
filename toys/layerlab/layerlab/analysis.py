"""Firing-share analysis (README 6.1, SPEC.md section 8): predict a winner from how often each side
could fire, and check that prediction against actual runs."""
from dataclasses import dataclass

import numpy as np

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


_EVEN_BAND = 0.02


def _start_hp(scn):
    types, defaults = scn.get("types", {}), scn.get("type_defaults", {})
    hp = []
    for g in scn["groups"]:
        hp += [float({**defaults, **types[g["type"]]}["hp"])] * int(g["count"])
    return np.array(hp, dtype=np.float64)


def _share(a, b):
    return a / (a + b) if a + b > 0 else None


def _window_state(f_a, d_a):
    if f_a is None or d_a is None:
        return "idle"
    if abs(f_a - 0.5) <= _EVEN_BAND and abs(d_a - 0.5) <= _EVEN_BAND:
        return "even"
    return "agree" if (f_a > 0.5 and d_a > 0.5) or (f_a < 0.5 and d_a < 0.5) else "disagree"


def _check_window(window):
    if isinstance(window, bool) or not isinstance(window, int) or window < 1:
        raise ValueError("window must be a positive int, got %r" % (window,))


def _ratio(num, den):
    return num / den if den > 0 else None


def _fmt(v, spec):
    return "%*s" % (int(spec), "-") if v is None else "%*.3f" % (int(spec), v)


@dataclass
class ExchangeTable:
    windows: list
    window: int
    n_agree: int
    n_disagree: int
    n_even: int
    n_idle: int
    firing_ratio: float
    damage_ratio: float
    lead_A_windows: int
    lead_B_windows: int
    survivors: tuple

    @property
    def text(self):
        fr = "-" if self.firing_ratio is None else "%.3f" % self.firing_ratio
        dr = "-" if self.damage_ratio is None else "%.3f" % self.damage_ratio
        lines = ["exchange: window %d  windows %d  agree %d  disagree %d  even %d  idle %d"
                 % (self.window, len(self.windows), self.n_agree, self.n_disagree, self.n_even, self.n_idle),
                 "firing ratio %s  damage ratio %s  lead A %d  B %d  survivors A %d  B %d"
                 % (fr, dr, self.lead_A_windows, self.lead_B_windows, *self.survivors)]
        for w in self.windows:
            lines.append("%6d %6d  fire A %6.2f B %6.2f  dealt A %8.1f B %8.1f  lost A %3d B %3d"
                         "  f_A %s d_A %s l_A %s  %-8s"
                         % (w["start"], w["end"], w["firing_A"], w["firing_B"], w["dealt_A"], w["dealt_B"],
                            w["lost_A"], w["lost_B"], _fmt(w["f_A"], 5), _fmt(w["d_A"], 5), _fmt(w["l_A"], 5),
                            w["state"]))
        return "\n".join(lines)


def exchange(result, scn, window=20):
    _check_window(window)
    if result.trace is None:
        raise ValueError("exchange needs a trace: run with trace=True")
    tr = result.trace
    first = result.first_shot_tick
    windows = []
    if first >= 0:
        side = tr["side"][0]
        hp = tr["hp"].astype(np.float64)
        alive = tr["alive"] != 0
        firing = (tr["flags"] & _FIRING_BIT) != 0
        start_hp = _start_hp(scn) if first == 0 else None
        for start in range(first, len(tr), window):
            end = min(start + window, len(tr))
            ref_hp = hp[start - 1] if start > 0 else start_hp
            ref_alive = alive[start - 1] if start > 0 else np.ones(tr.shape[1], dtype=bool)
            removed = np.maximum(0.0, ref_hp - hp[end - 1])
            died = ref_alive & ~alive[end - 1]
            fire = firing[start:end].sum(axis=0) / (end - start)
            w = {"start": start, "end": end}
            for k, name in ((0, "A"), (1, "B")):
                mine, other = side == k, side != k
                w["firing_" + name] = float(fire[mine].sum())
                w["dealt_" + name] = float(removed[other].sum())
                w["lost_" + name] = int(died[mine].sum())
            w["f_A"] = _share(w["firing_A"], w["firing_B"])
            w["d_A"] = _share(w["dealt_A"], w["dealt_B"])
            w["l_A"] = _share(w["lost_A"], w["lost_B"])
            w["state"] = _window_state(w["f_A"], w["d_A"])
            windows.append(w)
    states = [w["state"] for w in windows]
    return ExchangeTable(
        windows=windows, window=window, n_agree=states.count("agree"), n_disagree=states.count("disagree"),
        n_even=states.count("even"), n_idle=states.count("idle"),
        firing_ratio=_ratio(sum(w["firing_A"] for w in windows), sum(w["firing_B"] for w in windows)),
        damage_ratio=_ratio(sum(w["dealt_A"] for w in windows), sum(w["dealt_B"] for w in windows)),
        lead_A_windows=sum(1 for w in windows if w["f_A"] is not None and w["f_A"] - 0.5 > _EVEN_BAND),
        lead_B_windows=sum(1 for w in windows if w["f_A"] is not None and 0.5 - w["f_A"] > _EVEN_BAND),
        survivors=tuple(result.survivors))


def _mean(xs):
    return sum(xs) / len(xs) if xs else None


def check_exchange(scn, seeds, window=20, lib="O2"):
    _check_window(window)
    seeds = range(seeds) if isinstance(seeds, int) else seeds
    agree, fr, dr = [], [], []
    counted = won = 0
    for seed in seeds:
        res = run(scn, seed=seed, lib=lib, trace=True)
        t = exchange(res, scn, window=window)
        if t.n_agree + t.n_disagree:
            agree.append(t.n_agree / (t.n_agree + t.n_disagree))
        if t.firing_ratio is not None:
            fr.append(t.firing_ratio)
        if t.damage_ratio is not None:
            dr.append(t.damage_ratio)
        if t.firing_ratio not in (None, 1.0) and res.winner in (WIN_A, WIN_B):
            counted += 1
            won += (res.winner == WIN_A) == (t.firing_ratio > 1.0)
    return {"agree_fraction": _mean(agree), "firing_ratio": _mean(fr), "damage_ratio": _mean(dr),
            "higher_firing_won": won / counted if counted else None}
