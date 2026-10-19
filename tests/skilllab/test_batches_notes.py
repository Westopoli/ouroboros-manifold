# spec: Architect ruling A187 item 3 (plays that are not one group say so) - scripts/skilllab/batches.py enemy_position
"""bait and fall_back say they are not a single group order; ambush and the blob control do not. Fake scan; no engine."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches  # noqa: E402
from tests.skilllab.fakes_batches import FakeScan, faked, stub_summary_write  # noqa: E402,F401

PHRASE = "not a single group order"
NOTES = {"bait": "the bait is a second group, so the play is not a single group order",
         "fall_back": "the retreat is a later move, so the play is not a single group order"}


def _cells():
    return {c.label: c for c in batches.get("enemy_position").cells}


def test_bait_and_fall_back_notes_carry_the_exact_text():
    cells = _cells()
    for label, note in NOTES.items():
        assert note in cells[label].note, label


def test_ambush_and_blob_do_not_carry_the_phrase():
    cells = _cells()
    for label in ("ambush", "blob"):
        assert PHRASE not in cells[label].note, label


def test_run_file_states_it_for_bait_and_fall_back_only(tmp_path):
    paths = batches.run(faked(batches.get("enemy_position")), tmp_path, scan_fn=FakeScan())
    text = Path(paths["run"]).read_text(encoding="utf-8")
    hits = [l for l in text.splitlines() if PHRASE in l]
    assert any("bait" in l and "fall_back" not in l for l in hits)
    assert any("fall_back" in l for l in hits)
    for l in hits:
        assert "ambush" not in l and not l.startswith("| blob")
