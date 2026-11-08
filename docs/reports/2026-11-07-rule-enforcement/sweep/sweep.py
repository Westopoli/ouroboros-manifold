"""One-command sweep:  .venv/bin/python <this file>   (cwd = repo root). Writes sweep_results.jsonl next to this file; 25 min wall-clock cap."""
import json, multiprocessing as mp, sys, time, glob, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, ".")
CAT = "docs/northstar/research/layer_dynamics/catalogue/L-%04d.toml"
LEGACY = [1, 2, 3, 4, 5, 6, 7, 10, 13, 16, 19, 20, 22, 25, 28, 31]   # denied old open-field layouts (R6 bypassed), incl. tiered/large landscapes
OPEN = [34, 35, 36, 48, 49, 50, 51, 52, 53] + LEGACY
FEAT = [37, 38, 39, 40, 41, 42, 43, 44, 45, 47, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84]
HEAVY = [46, 54]
def tasks():
    t = []
    # NOTE seed 2 was run once (v2 sweep, 130 layout/sight pairs): byte-identical fights to seed 1 (the tactical sim draws no random numbers), so the second pass is
    # the stage-4 "control" rule set (targeting by sight off, reach/era as stage 4) instead
    for seed, sights in ((1, ("on", "off")), (2, ("control",))):
        for L in OPEN + FEAT:
            for sight in sights:
                t.append((CAT % L, 1, sight, "main"))
        if seed == 1:
            for L in HEAVY:
                for sight in ("on", "off"):
                    t.append((CAT % L, 1, sight, "heavy"))
            # determinism: second independent run (different process) of 12 fights
            for L in (1, 4, 39, 43, 45, 55, 61, 73, 80, 83, 84, 19, 49, 79):
                for sight in ("on", "off"):
                    t.append((CAT % L, 1, sight, "dup"))
    return t

def work(a):
    import inv_check
    inv_check.ALLOW_R6 = True
    path, seed, sight, tag = a
    t0 = time.time()
    try:
        r = inv_check.run_one(path, seed, sight)
    except Exception as e:
        import traceback
        r = {"layout": os.path.basename(path)[:-5], "seed": seed, "sight": sight, "error": traceback.format_exc()[-1500:]}
    r["tag"] = tag; r["wall"] = round(time.time() - t0, 1)
    return r
if __name__ == "__main__":
    out = os.path.join(HERE, "sweep_results.jsonl")
    deadline = time.time() + 25 * 60
    ts = tasks()
    done = 0
    with mp.Pool(4) as pool, open(out, "w") as f:
        it = pool.imap_unordered(work, ts, chunksize=1)
        while done < len(ts):
            left = deadline - time.time()
            if left <= 0:
                print("DEADLINE reached, aborting", flush=True); pool.terminate(); break
            try:
                r = it.next(timeout=left)
            except mp.TimeoutError:
                print("DEADLINE reached, aborting", flush=True); pool.terminate(); break
            done += 1
            f.write(json.dumps(r, default=str) + "\n"); f.flush()
            print(done, len(ts), r.get("layout"), r.get("sight"), r.get("seed"), r.get("tag"), r.get("wall"), r.get("reject") or r.get("error", "")[:80], flush=True)
    print("done", done, "of", len(ts))
