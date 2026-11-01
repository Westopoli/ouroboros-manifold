# spec: docs/stories/H-039.md (arena-snapshot-contract; Tests section); Flag harness, Scene none (file format)
"""H-039 arena snapshot contract: the `om-fight-1` fight file and its checker, `scripts/skilllab/arena/snapshot.py`.

Every number is an Architect draft dated 2026-10-31 that Westley rules: DRAFT-snapshot-count (MAX_FRAMES 20, MIN_FRAMES 10),
DRAFT-snapshot-seconds (5 s between frames), DRAFT-fight-cap (CAP_SECONDS 600), DRAFT-winner. The tests use the story's names
and the story's examples; none adds a number of its own.

The module is imported through the `snap` fixture, not at file top, so that while it is missing the contract tests fail one by
one for the missing-module reason and the harness control (test_control_*) still runs green."""
import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import contract  # noqa: E402


@pytest.fixture
def snap():
    return importlib.import_module("scripts.skilllab.arena.snapshot")


def _flip(doc, path, value):
    """Set doc[path...] = value on a deep copy; return the copy."""
    out = json.loads(json.dumps(doc))
    node = out
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return out


# ---------------------------------------------------------------- positive control (green today)

def test_control_harness_and_tick_rate():
    """Positive control, green before the feature exists. Story: "`tick_rate`: int ticks per second of sim time (20 today,
    `scripts/skilllab/contract.py:161`)." The lab constant the snapshot copies is 20, and this file runs under pytest, so a
    red elsewhere in the file means the snapshot module is missing, not that the harness is broken."""
    assert contract.TICKS_PER_SECOND == 20


# ---------------------------------------------------------------- the module's constants

def test_module_constants(snap):
    """Story: "`SCHEMA = "om-fight-1"`; `MAX_FRAMES = 20`; `MIN_FRAMES = 10` (advisory, not enforced); `CAP_SECONDS = 600`."
    (DRAFT-snapshot-count, DRAFT-fight-cap.)"""
    assert snap.SCHEMA == "om-fight-1"
    assert snap.MAX_FRAMES == 20
    assert snap.MIN_FRAMES == 10
    assert snap.CAP_SECONDS == 600


# ---------------------------------------------------------------- example(), validate()

def test_example_validates_clean(snap):
    """Story: "`example()` validates clean" and "A fixture builder for tests `example(frames: int = 3, units_per_side: int = 2)
    -> dict` returns a valid document." The fixture follows the file spec: schema string, lab tick rate, sight off for stage 1,
    one unit row per unit with the nine stage-1 keys."""
    doc = snap.example()
    assert snap.validate(doc) == []
    assert doc["schema"] == "om-fight-1"
    assert doc["tick_rate"] == contract.TICKS_PER_SECOND
    assert doc["sight"] == "off"
    assert len(doc["frames"]) == 3
    assert len(doc["frames"][0]["units"]) == 4
    assert sorted(doc["frames"][0]["units"][0]) == sorted(
        ["id", "side", "role", "x", "y", "layer", "facing", "hp", "alive", "target"])


def test_example_sizes_validate_clean(snap):
    """Story: "`example(frames: int = 3, units_per_side: int = 2)`" and the SNAPSHOT.md worked example "a two-frame,
    one-unit-per-side fight": other sizes are valid documents too, with the frame and unit counts asked for."""
    doc = snap.example(frames=2, units_per_side=1)
    assert snap.validate(doc) == []
    assert len(doc["frames"]) == 2
    assert len(doc["frames"][0]["units"]) == 2


# ---------------------------------------------------------------- write / read

def test_write_read_round_trips_and_second_write_is_byte_identical(snap, tmp_path):
    """Story: "`write` then `read` round-trips byte-identically on a second write." and "JSON, UTF-8, keys sorted, two-space
    indent (so two runs of the same fight diff to nothing)" and "`write(...)` ... writes sorted keys, indent 2, trailing
    newline.\""""
    doc = snap.example()
    first = tmp_path / "a.fight.json"
    second = tmp_path / "b.fight.json"
    snap.write(doc, first)
    back = snap.read(first)
    assert back == doc
    snap.write(back, second)
    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes() == (json.dumps(doc, sort_keys=True, indent=2) + "\n").encode("utf-8")


# ---------------------------------------------------------------- positive controls of the detector

def test_validate_missing_hp_is_exactly_one_message_naming_hp(snap):
    """Story: "a frame with `hp` removed from one unit gives exactly one message naming `hp`" and "(`missing
    frames[3].units[7].hp`...)": the message names the frame, the unit row and the key."""
    doc = snap.example()
    del doc["frames"][1]["units"][3]["hp"]
    msgs = snap.validate(doc)
    assert len(msgs) == 1, msgs
    assert "hp" in msgs[0]
    assert "missing frames[1].units[3].hp" in msgs[0]


def test_validate_extra_key_seen_is_unknown_key(snap):
    """Story: "an extra key `seen` gives `unknown key`" and "the checker rejects keys it does not know (so a stage cannot
    grow the file silently)" (`unknown key frames[0].units[0].seen`)."""
    doc = snap.example()
    doc["frames"][0]["units"][0]["seen"] = [1]
    msgs = snap.validate(doc)
    assert len(msgs) == 1, msgs
    assert "unknown key" in msgs[0]
    assert "seen" in msgs[0]


@pytest.mark.parametrize("path", [("extra",), ("result", "extra"), ("frames", 0, "extra")])
def test_validate_rejects_unknown_key_at_every_level(snap, path):
    """Story: "the checker rejects keys it does not know" at the top level, in `result` and in a frame, not only in a unit
    row."""
    doc = _flip(snap.example(), path, 1)
    msgs = snap.validate(doc)
    assert len(msgs) == 1, msgs
    assert "unknown key" in msgs[0]


def test_validate_frames_out_of_order(snap):
    """Story: "`frames`: list, in tick order." and "frames out of order" (`frames not in tick order`)."""
    doc = snap.example()
    doc["frames"][1], doc["frames"][2] = doc["frames"][2], doc["frames"][1]
    msgs = snap.validate(doc)
    assert any("frames not in tick order" in m for m in msgs), msgs


def test_validate_first_frame_tick_not_zero(snap):
    """Story: "`frames` ... Always includes tick 0" and "first frame tick not 0" (`frames[0].tick is not 0`)."""
    doc = _flip(snap.example(), ("frames", 0, "tick"), 5)
    msgs = snap.validate(doc)
    assert "frames[0].tick is not 0" in msgs, msgs


def test_validate_agree_wrong(snap):
    """Story: "`agree`: bool, `winner == predict`." (`result.agree disagrees with winner and predict`)."""
    doc = snap.example()
    doc["result"]["agree"] = not doc["result"]["agree"]
    msgs = snap.validate(doc)
    assert msgs == ["result.agree disagrees with winner and predict"], msgs


def test_validate_units_not_sorted_by_id(snap):
    """Story: "`units`: list, one row per unit spawned ..., sorted by `id`" (`units sorted by id`)."""
    doc = snap.example()
    doc["frames"][0]["units"].reverse()
    msgs = snap.validate(doc)
    assert any("sorted by id" in m for m in msgs), msgs


# ---------------------------------------------------------------- frame_ticks

def test_frame_ticks_capped_fight_obeys_the_doubling_rule(snap):
    """Story: "a runner that would write more than 20 frames doubles `snapshot_every` until it does not" and "`frame_ticks
    (12000, 20)` has at most 20 entries, first 0, last 12000, spacing a power-of-two multiple of 100." (DRAFT-snapshot-count,
    DRAFT-snapshot-seconds 5 s at 20 ticks per second is 100 ticks.)"""
    ticks = snap.frame_ticks(12000, 20)
    assert len(ticks) <= snap.MAX_FRAMES
    assert ticks[0] == 0
    assert ticks[-1] == 12000
    assert ticks == sorted(set(ticks))
    gaps = [b - a for a, b in zip(ticks, ticks[1:])]
    step = gaps[0]
    assert step % 100 == 0
    ratio = step // 100
    assert ratio & (ratio - 1) == 0, f"spacing {step} is not a power-of-two multiple of 100"
    assert all(g == step for g in gaps[:-1])
    assert 0 < gaps[-1] <= step


def test_frame_ticks_short_fight_is_every_hundred(snap):
    """Story: "`frame_ticks(300, 20)` is `[0, 100, 200, 300]`" (fewer than MIN_FRAMES is allowed when the fight is short)."""
    assert snap.frame_ticks(300, 20) == [0, 100, 200, 300]


# ---------------------------------------------------------------- write refuses

def test_write_refuses_invalid_document_and_writes_nothing(snap, tmp_path):
    """Story: "`write(doc, path)`: validates (raises `ValueError` with the messages joined) then writes" and "`write` refuses
    an invalid document and writes nothing." No file, and no stray temporary beside it."""
    doc = snap.example()
    del doc["frames"][1]["units"][3]["hp"]
    target = tmp_path / "bad.fight.json"
    with pytest.raises(ValueError, match="hp"):
        snap.write(doc, target)
    assert not target.exists()
    assert list(tmp_path.iterdir()) == []
