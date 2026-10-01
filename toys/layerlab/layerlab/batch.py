"""Bulk runs: one data row per fight, optionally in a process pool (SPEC.md section 8: batch.py).

Processes, never threads: ll_sim.c keeps a static error buffer. Rows are dicts of scalars; traces are
dropped as soon as the row is built."""
import csv
from concurrent.futures import ProcessPoolExecutor
from functools import partial

from .analysis import exchange, predict_early
from .ffi import WIN_A, WIN_B, WIN_CAP, WIN_MUTUAL, WIN_STALEMATE
from .run import run

FIELDS = [
    "job", "seed", "error", "winner", "winner_name", "survivors_A", "survivors_B", "hp_ratio_A",
    "hp_ratio_B", "ticks", "first_shot_tick", "first_contact_tick", "shots_A", "shots_B", "damage_A",
    "damage_B", "cost_lost_A", "cost_lost_B", "unanswered_A", "unanswered_B", "transitions",
    "firing_ticks_A", "firing_ticks_B", "alive_ticks_A", "alive_ticks_B", "firing_share_A", "early_f_A",
    "early_f_B", "early_pred", "early_agree", "ex_agree_fraction", "ex_firing_ratio", "ex_damage_ratio",
]
_NAMES = {WIN_A: "A", WIN_B: "B", WIN_STALEMATE: "stalemate", WIN_CAP: "cap", WIN_MUTUAL: "mutual"}
_SET = "set:"


def _row(index, job, error=None, res=None, window=40, ex_window=20):
    row = dict.fromkeys(FIELDS)
    row["job"], row["seed"], row["error"] = index, job["seed"], error
    if res is not None:
        scn = job["scenario"]
        p = predict_early(res, scn, window=window)
        t = exchange(res, scn, window=ex_window)
        fa, fb = res.firing_ticks
        actual = {WIN_A: "A", WIN_B: "B"}.get(res.winner)
        decided = t.n_agree + t.n_disagree
        row.update(
            winner=res.winner, winner_name=_NAMES.get(res.winner, str(res.winner)),
            survivors_A=res.survivors[0], survivors_B=res.survivors[1],
            hp_ratio_A=res.hp_ratio[0], hp_ratio_B=res.hp_ratio[1], ticks=res.ticks,
            first_shot_tick=res.first_shot_tick, first_contact_tick=res.first_contact_tick,
            shots_A=res.shots[0], shots_B=res.shots[1],
            damage_A=res.damage_dealt[0], damage_B=res.damage_dealt[1],
            cost_lost_A=res.cost_lost[0], cost_lost_B=res.cost_lost[1],
            unanswered_A=res.unanswered_ticks[0], unanswered_B=res.unanswered_ticks[1],
            transitions=res.transitions, firing_ticks_A=fa, firing_ticks_B=fb,
            alive_ticks_A=res.alive_ticks[0], alive_ticks_B=res.alive_ticks[1],
            firing_share_A=fa / (fa + fb) if fa + fb > 0 else None,
            early_f_A=p["f_A"], early_f_B=p["f_B"], early_pred=p["predicted"],
            early_agree=None if p["predicted"] in ("tie", "none") or actual is None
            else int(p["predicted"] == actual),
            ex_agree_fraction=t.n_agree / decided if decided else None,
            ex_firing_ratio=t.firing_ratio, ex_damage_ratio=t.damage_ratio)
    for path in sorted(job.get("settings") or {}):
        row[_SET + path] = job["settings"][path]
    return row


def _work(item, lib, window, ex_window):
    index, job = item
    try:
        res = run(job["scenario"], seed=job["seed"], trace=True, lib=lib)
    except (ValueError, RuntimeError) as e:
        return _row(index, job, error=str(e))
    return _row(index, job, res=res, window=window, ex_window=ex_window)


def run_rows(jobs, processes=None, lib="O2", window=40, ex_window=20):
    jobs = list(jobs)
    work = partial(_work, lib=lib, window=window, ex_window=ex_window)
    items = list(enumerate(jobs))
    if not processes or processes <= 1 or len(jobs) <= 1:
        return [work(it) for it in items]
    procs = min(processes, len(jobs))
    with ProcessPoolExecutor(max_workers=procs) as pool:
        return list(pool.map(work, items, chunksize=max(1, len(jobs) // (procs * 4))))


def _columns(rows):
    return FIELDS + sorted({k for r in rows for k in r if k.startswith(_SET)})


def _cell(v):
    if v is None:
        return ""
    return repr(v) if isinstance(v, float) else str(v)


def write_rows(rows, path):
    cols = _columns(rows)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(cols)
        for r in rows:
            w.writerow([_cell(r.get(c)) for c in cols])


def _parse(text):
    if text == "":
        return None
    for conv in (int, float):
        try:
            return conv(text)
        except ValueError:
            pass
    return text


def read_rows(path):
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if header is None:
            return []
        return [{c: _parse(v) for c, v in zip(header, rec)} for rec in reader]
