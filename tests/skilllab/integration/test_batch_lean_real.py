# spec: skill lab memory - a batch's parent keeps no per-tick series except each cell's charted example
"""Real library, spawned workers. Digests were recorded by running the same small batch on origin/main (5c2e1d04)."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROBE = Path(__file__).with_name("lean_batch_probe.py")
PY = sys.executable

# recorded on origin/main before the change: 3 replicates, workers 2; re-recorded once 2026-10-06
# (TD-SL-goldens-rerecord-1006: group speed-cap fix dcb83d5f, re-order rule efdc5548, which added summary.json)
BEFORE = {"csv": "e7b9dca1a1b85858a038e79f74af60e4c63f358072559767bcd42fde220b8fdd",
          "page": "e4d1bc887c6f2f16afcbd7cf1d742cc29a708eb0b5618f8e620ce2ac1a652bd6",
          "run": "574b22110687eb1060ef0c43766bf47de4c3c97a5e9619d1344e38688538dbe8",
          "summary": "e23287200d62021ebb408efca856b8d24e71d72530906e82162e1773efc1ec21"}
# measured on origin/main: about 206 KB per finished fight (weighted on); after: about 3.4 KB. Bound sits between.
KB_PER_FIGHT_BOUND = 40.0


def _probe(out_dir, replicates, workers):
    out = subprocess.run([PY, str(PROBE), str(out_dir), str(replicates), str(workers)], capture_output=True,
                         text=True, cwd=ROOT, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_small_batch_output_is_byte_identical_to_before(tmp_path):
    got = _probe(tmp_path, 3, 2)
    assert got["digests"] == BEFORE
    assert "units able to fire through one fight" in (tmp_path / "enemy_position_page.html").read_text()


def test_parent_memory_per_finished_fight_stays_small(tmp_path):
    got = _probe(tmp_path, 300, 2)
    assert got["fights"] == 1800
    assert got["kb_per_fight"] < KB_PER_FIGHT_BOUND, got
