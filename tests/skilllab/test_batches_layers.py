# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md row L4: tables LA, LB, LC and the body-size table deleted from batches.py
"""The 'layers' batch is retired (LAB-REV2-L4). It was tables LA, LB, LC by three scenes plus the sixteen body-size cells, all at
draft sweep points that ran on same-layer scenes (the 2026-10-13 audit: identical fights). The `sweep` command replaces it
(test_sweep.py). This file keeps the guards that nothing of it comes back; the old cell-by-cell tests are retired with it."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches  # noqa: E402

SRC = (ROOT / "scripts" / "skilllab" / "batches.py").read_text()


def test_layers_is_not_a_batch_name_and_get_refuses_it():
    assert "layers" not in batches.NAMES
    with pytest.raises(ValueError):
        batches.get("layers")


@pytest.mark.parametrize("name", ["_layers", "_layer_settings", "_with_reach", "LAYER_SCENES", "LAYER_REACH", "REACH_NOTE", "REACH_TABLE"])
def test_the_layers_builders_and_constants_are_gone(name):
    assert not hasattr(batches, name)


def test_no_table_label_or_body_size_cell_is_built_by_any_batch():
    for n in batches.NAMES:
        if n == "layout_search":
            continue
        labels = [c.label for c in batches.get(n).cells]
        assert not [lb for lb in labels if re.match(r"L[ABC]:", lb) or lb.startswith("body")], n


def test_batches_does_not_set_layer_vision_or_reach_factors():
    """Vision, range and damage multipliers are swept knobs now (sweep.py); a batch never sets them."""
    assert not re.search(r"OM_TP_(VISION|RANGE|DAMAGE)_(UP|DOWN)", SRC)
