# spec: Architect ruling A187 item 2 (more fights near a break-even) - scripts/skilllab/batches.py run()
"""batches.run asks every scan for refine_factor=3 and says so in the run file. Fake scan; no engine."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches  # noqa: E402
from tests.skilllab.fakes_batches import FakeScan, faked, stub_summary_write  # noqa: E402,F401

SENTENCE = "Cells within 2 enemy units of a break-even run 3 times the fights."


def _go(tmp_path, name):
    fake = FakeScan()
    paths = batches.run(faked(batches.get(name)), tmp_path / name, scan_fn=fake)
    return fake, Path(paths["run"]).read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ["enemy_position", "landscape", "focus_fire"])
def test_every_scan_gets_refine_factor_3(tmp_path, name):
    fake, _ = _go(tmp_path, name)
    assert fake.calls and all(c["kw"].get("refine_factor") == 3 for c in fake.calls)


def test_reference_scans_are_refined_too(tmp_path):
    fake, _ = _go(tmp_path, "landscape")
    refs = [c for c in fake.calls if c["label"].endswith("#ref")]
    assert refs and all(c["kw"].get("refine_factor") == 3 for c in refs)


def test_sentence_appears_once_under_the_cells_table(tmp_path):
    _, text = _go(tmp_path, "enemy_position")
    assert text.count(SENTENCE) == 1
    cells = text.split("## Cells", 1)[1].split("\n## ", 1)[0]
    assert SENTENCE in cells
    assert cells.index("| status |") < cells.index(SENTENCE)


def test_fights_per_cell_column_stays_first_pass(tmp_path):
    _, text = _go(tmp_path, "enemy_position")
    assert re.search(r"^\| blob \| 16 \| 8 to 24 \| 10 \| 20 \| naive \|$", text, re.M)
