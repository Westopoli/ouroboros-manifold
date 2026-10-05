# spec: skill lab memory - a batch's parent keeps no per-tick series except each cell's charted example
"""Real library, spawned workers. Digests were recorded by running the same small batch on origin/main (5c2e1d04)."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROBE = Path(__file__).with_name("lean_batch_probe.py")
PY = sys.executable

# recorded on origin/main before the change: 3 replicates, workers 2
BEFORE = {"csv": "b01d649c3a65ae95946429890e331ae998f521006054cbc48f2ddc075962feb9",
          "page": "7bb1c195a9db78c701fe6c1093e2cbb428f757cb97e003a23cbf6c50bfdc5633",
          "run": "94af00f2fe0532c3e8cbf73500a5fdfb3d06fba3ce023e52dec860a6a05b512a"}
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
