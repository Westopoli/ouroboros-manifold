# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase S, situation sampler (a map with no effect is reported)
"""A landscape cell on a non-open map whose result equals the open map's is listed under 'What the instrument could not express'.

Proposed function (does not exist yet): batches.terrain_had_no_effect(cell_result, open_result) -> bool, True when the two
ScanResults agree on every fight's outcome, margin, survivors and ticks. The page builder uses it per non-open cell, against the
open cell with the same role. Fakes only."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches  # noqa: E402
from tests.skilllab.fakes_batches import FakeScan, faked, make_scan  # noqa: E402


def test_equal_scans_had_no_effect_and_different_ones_did():
    same = make_scan(16, 8, 10, 9)
    assert batches.terrain_had_no_effect(same, make_scan(16, 8, 10, 9)) is True
    assert batches.terrain_had_no_effect(make_scan(16, 8, 10, 9, ticks=101), same) is False
    assert batches.terrain_had_no_effect(make_scan(16, 8, 10, 7), same) is False


def test_the_page_lists_non_open_cells_that_equal_open_and_only_those(tmp_path):
    fake = FakeScan(results={("block:blob_v_defenders", None): 9, ("wall:line_v_defenders", None): 4})
    defn = faked(batches.get("landscape"))
    out = tmp_path / "out"
    batches.run(defn, out, scan_fn=fake)
    text = next(p for p in sorted(out.glob("*.md"))).read_text(encoding="utf-8")
    m = re.search(r"^## What the instrument could not express\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m, "no could-not-express section"
    section = m.group(1)
    for label in ("block:line_v_defenders", "wall:blob_v_defenders", "lane:blob_v_defenders", "lane:line_v_defenders",
                  "cover_field:blob_v_defenders", "cover_field:line_v_defenders"):
        assert label in section, label
    for label in ("block:blob_v_defenders", "wall:line_v_defenders", "open:blob_v_defenders", "open:line_v_defenders"):
        assert label not in section, label
