"""Helper for test_batch_lean_real: a small real batch, its output digests, and a parent-memory probe (run as a script)."""
import hashlib
import json
import resource
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches, engine, plays, summary  # noqa: E402


def small_batch(replicates, enemy=(7, 9)):
    """One real cell, blob against blob at 8 units; the weighted columns are always recorded (LAB-REV2: no Setup.weighted)."""
    cell = batches._cell("blob@8", 8, plays.blob_play(8), "naive", enemy=enemy)
    cell = batches.CellDef(**{**cell.__dict__, "replicates": replicates})
    return batches.BatchDef(name="enemy_position", title="Lean probe", scene="one cell", cells=(cell,),
                            variants=(("default", {}),), unexpressed=("none",))


def digests(paths):
    return {k: hashlib.sha256(Path(p).read_bytes()).hexdigest() for k, p in sorted(paths.items())}


def main(out_dir, replicates, workers):
    """Print {fights, kb_per_fight} for the parent's peak RSS growth over the run."""
    engine.Engine()
    # summary.py is L5's file and still reads FightResult.mopup_orders (retired by L2); this probe is about the parent's memory and
    # the csv, page and run file, so it replaces summary.write with an empty-object writer. See also: fakes_batches.stub_summary_write.
    summary.write = lambda defn, scans, path, rule, *a, **k: Path(path).write_text("{}", encoding="utf-8")
    base = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    paths = batches.run(small_batch(replicates), out_dir, workers=workers)
    grown = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - base
    fights = 3 * 2 * replicates
    print(json.dumps({"fights": fights, "kb_per_fight": grown / fights, "digests": digests(paths)}))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
