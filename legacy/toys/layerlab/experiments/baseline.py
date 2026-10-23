"""K2 baseline (README 4.2, 7): the skill profile of today's rules under four rule tables (base, LA, LB, LC).
One task = one (situation, size, config); each task runs all 32 combinations serially inside one process, so the
pool is over tasks (no pool per solve). Results go to results/data/baseline.json (not committed)."""
import sys, json, time, statistics
sys.path.insert(0, ".")
from concurrent.futures import ProcessPoolExecutor, as_completed
from layerlab.skill.situation import sample_situations
from layerlab.skill.plays import profile, all_combinations

def _task(args):
    sit, size, cfg, seeds = args
    prof = profile([sit], sizes=(size,), config=cfg, processes=1, seeds=seeds)
    out = []
    for c in prof.cells:
        out.append({"sit": c["situation"], "family": sit.family, "size": c["size"], "config": cfg or "base",
                    "combo": "".join(sorted(s[1] for s in c["combo"])) or "0",
                    "value": c["value"], "r0": c["r0"], "premium": c["premium"], "valid": c["valid"],
                    "map_set": c["map_set"], "refusable": c["refusable"], "value_cost": c["value_cost"],
                    "firing_adv_at_rstar": c["firing_adv_at_rstar"], "firing_adv_equal": c["firing_adv_equal"],
                    "win_margin": c["win_margin"], "windows": c["windows"],
                    "flags": list(c["flags"]) if not isinstance(c["flags"], dict) else c["flags"]})
    return out

def _key(sit, size, cfg):
    return "%d|%d|%s" % (sit.id, size, cfg or "base")

def run(n_sits=14, sizes=(8, 16), configs=(None, "LA", "LB", "LC"), seeds=(0, 1, 2), procs=9,
        out="results/data/baseline.json", seed=1, part="results/data/baseline.parts.jsonl"):
    """Each finished task is appended to `part` (one JSON line); a rerun skips the tasks already there, so a
    stopped run resumes. The final `out` is written from all parts. Delete `part` to start over."""
    sits = sample_situations(n_sits, seed)
    tasks = [(s, z, c, tuple(seeds)) for c in configs for s in sits for z in sizes]
    done = {}
    try:
        for line in open(part):
            row = json.loads(line)
            done[row["key"]] = row["cells"]
    except FileNotFoundError:
        pass
    todo = [t for t in tasks if _key(t[0], t[1], t[2]) not in done]
    t0 = time.time()
    print(f"{len(done)} tasks on disk, {len(todo)} to run, {procs} processes", flush=True)
    with ProcessPoolExecutor(max_workers=procs) as ex, open(part, "a") as f:
        futs = {ex.submit(_task, t): t for t in todo}
        for i, fut in enumerate(as_completed(futs)):
            t = futs[fut]
            cells = fut.result()
            done[_key(t[0], t[1], t[2])] = cells
            f.write(json.dumps({"key": _key(t[0], t[1], t[2]), "cells": cells}) + "\n")
            f.flush()
            if (i + 1) % 8 == 0:
                print(f"  {i+1}/{len(todo)} tasks, {time.time()-t0:.0f}s", flush=True)
    cells = [c for t in tasks for c in done[_key(t[0], t[1], t[2])]]
    json.dump(cells, open(out, "w"))
    print(f"{len(cells)} cells in {time.time()-t0:.0f}s -> {out}")
    return cells

if __name__ == "__main__":
    run()
