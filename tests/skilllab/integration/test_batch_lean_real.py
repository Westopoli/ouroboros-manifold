# spec: skill lab memory - a batch's parent keeps no per-tick series except each cell's charted example
"""Real library, spawned workers. Digests were recorded by running the same small batch on origin/main (5c2e1d04)."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROBE = Path(__file__).with_name("lean_batch_probe.py")
PY = sys.executable

# measured on origin/main: about 206 KB per finished fight (weighted on); after: about 3.4 KB. Bound sits between.
KB_PER_FIGHT_BOUND = 40.0
# LAB-REV2-L4: the digests recorded on main (5c2e1d04, re-recorded 2026-10-06) cannot hold: the CSV gained columns (firing_window_*,
# weighted_*, predicted_*, agreement, knob, baseline, ceiling_hit, prefight) and the run file lost the stalled count. The test below
# compares one worker with two instead; a new golden is recorded with TD-LAB-REV2-golden once the lab lands.


def _probe(out_dir, replicates, workers):
    out = subprocess.run([PY, str(PROBE), str(out_dir), str(replicates), str(workers)], capture_output=True,
                         text=True, cwd=ROOT, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_small_batch_output_is_byte_identical_at_one_and_two_workers(tmp_path):
    one = _probe(tmp_path / "one", 3, 1)
    two = _probe(tmp_path / "two", 3, 2)
    assert one["digests"].keys() == two["digests"].keys() >= {"csv", "page", "run"}
    for k in ("csv", "page", "run"):
        assert one["digests"][k] == two["digests"][k], k
    assert "units able to fire through one fight" in (tmp_path / "two" / "enemy_position_page.html").read_text()


def test_parent_memory_per_finished_fight_stays_small(tmp_path):
    got = _probe(tmp_path, 300, 2)
    assert got["fights"] == 1800
    assert got["kb_per_fight"] < KB_PER_FIGHT_BOUND, got
