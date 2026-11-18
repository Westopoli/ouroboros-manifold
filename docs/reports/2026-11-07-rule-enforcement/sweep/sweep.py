"""One-command sweep:  .venv/bin/python <this file>   (cwd = repo root). Writes sweep_results.jsonl next to this file; 25 min wall-clock cap."""
import json, multiprocessing as mp, shutil, sys, time, glob, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
CAT = ROOT + "/docs/northstar/research/layer_dynamics/catalogue/%s.toml"
MANIFEST = ROOT + "/docs/northstar/research/layer_dynamics/arena/approved.toml"   # round6.md L2: the sweep runs his approved fights and no other layout
SITUATIONS = ROOT + "/docs/northstar/research/layer_dynamics/situations"
def tasks():
    """One task per fight of the manifest (seed 1, the row's sight), and one more per control (ground: the twin with the features emptied; sight: targeting by sight off).
    Situation rows are converted alone into a scratch directory first, as scripts/skilllab/arena/regression.py does."""
    import tempfile, tomllib
    from scripts.skilllab.arena import run, situations
    work = tempfile.mkdtemp(prefix="om-sweep-")
    t = []
    for row in tomllib.load(open(MANIFEST, "rb"))["fight"]:
        if "layout" in row:
            path = CAT % row["layout"]
        else:
            n = int(row["situation"].split("-")[1])
            src = os.path.join(work, row["situation"]); os.makedirs(src)
            shutil.copy(glob.glob(os.path.join(SITUATIONS, row["situation"] + "-*.md"))[0], src)
            situations.convert(src, os.path.join(work, "out"), "L-%04d" % n)
            path = os.path.join(work, "out", "L-%04d.toml" % n)
        t.append((path, 1, row["sight"], "main"))
        if row["control"] == "sight":
            t.append((path, 1, "control", "main"))
        elif row["control"] == "ground":
            twin, twin_path = run.control_twin(tomllib.load(open(path, "rb")), path, os.path.join(work, "control"))
            if twin is not None:
                t.append((str(twin_path), 1, row["sight"], "main"))
    return t

def work(a):
    import inv_check
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
