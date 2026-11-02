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


# ================================================================ H-052: fight.json contract v2 (orders and fight end)
# spec: docs/stories/H-052.md. Quoted: "`schema` becomes `om-fight-2`; `om-fight-1` files still validate (the checker accepts both ...)."
# "New top-level `orders`: `{"mode": "both_same_point" | "hold_and_attack", "point": [x, y], "attacker": "A" | "B" | null}`." "No other mode
# exists." "New `result.end`: `"wipe"` ..., `"silence"` (no shot by either side for DRAFT-silence-seconds 10 of sim time), `"cap"` (DRAFT-fight-cap)."
# "New `result.stall`: true when `end` is `silence` and both sides have survivors. `winner` is then `"stall"`, not `"draw"`; `agree` is false."
# "The checker rejects an `om-fight-2` file missing `orders` or `result.end`, and a `stall` without `end == "silence"`."
# The builder adds the v2 example builder; until it exists the v2 documents are built inline from `snapshot.example()` (DRAFT-v2-example-name).
# Every v2 test first asserts the baseline v2 document validates, so while v2 is missing it fails for that reason and not by accident.

def _v2(snap, end="wipe", stall=False, mode="both_same_point", attacker=None):
    """`snapshot.example()` as an om-fight-2 document: schema, `orders`, `result.end`, `result.stall`; a stall puts both sides alive in the last frame."""
    doc = snap.example()
    doc["schema"] = "om-fight-2"
    doc["orders"] = {"mode": mode, "point": [120.0, 52.0], "attacker": attacker}
    doc["result"]["end"] = end
    doc["result"]["stall"] = stall
    if stall:
        last = doc["frames"][-1]
        for row in last["units"]:
            row["hp"], row["alive"] = 100.0, True
        last["alive"] = [2, 2]
        doc["result"].update({"winner": "stall", "survivors": [2, 2], "agree": False, "predict": "A"})
    return doc


def test_control_v1_example_still_validates(snap):
    """H-052 Tests: "v1 example still validates." Control, green today and after: the unchanged `snapshot.example()` carries the v1 schema and no
    `orders`, `result.end` or `result.stall`, and validates clean."""
    doc = snap.example()
    assert doc["schema"] == "om-fight-1"
    assert "orders" not in doc and "end" not in doc["result"] and "stall" not in doc["result"]
    assert snap.validate(doc) == []


def test_v2_example_validates(snap):
    """H-052 Tests: "v2 example validates." and "`schema` becomes `om-fight-2`": a wipe fight under both_same_point validates clean."""
    assert snap.validate(_v2(snap)) == []


@pytest.mark.parametrize("mode,attacker", [("both_same_point", None), ("hold_and_attack", "B"), ("hold_and_attack", "A")])
def test_v2_orders_modes_validate(snap, mode, attacker):
    """H-052: "`{"mode": "both_same_point" | "hold_and_attack", "point": [x, y], "attacker": "A" | "B" | null}`": each mode, with attacker null
    or A or B, is a valid `orders`."""
    assert snap.validate(_v2(snap, mode=mode, attacker=attacker)) == []


def test_v2_missing_orders_fails_naming_orders(snap):
    """H-052: "The checker rejects an `om-fight-2` file missing `orders`" and Tests: "v2 missing `orders` fails naming it"."""
    assert snap.validate(_v2(snap)) == []
    doc = _v2(snap)
    del doc["orders"]
    msgs = snap.validate(doc)
    assert any("missing orders" in m for m in msgs), msgs


def test_v2_missing_result_end_fails_naming_it(snap):
    """H-052: "The checker rejects an `om-fight-2` file missing `orders` or `result.end`"."""
    assert snap.validate(_v2(snap)) == []
    doc = _v2(snap)
    del doc["result"]["end"]
    msgs = snap.validate(doc)
    assert any("missing result.end" in m for m in msgs), msgs


def test_v2_stall_with_end_wipe_fails(snap):
    """H-052: "The checker rejects ... a `stall` without `end == "silence"`" and Tests: "`stall` with `end == "wipe"` fails". The stall document
    validates with end silence; the same document with end wipe fails with a message naming stall."""
    assert snap.validate(_v2(snap, end="silence", stall=True)) == []
    doc = _v2(snap, end="silence", stall=True)
    doc["result"]["end"] = "wipe"
    msgs = snap.validate(doc)
    assert any("stall" in m for m in msgs), msgs


def test_v2_stall_with_end_cap_fails(snap):
    """H-052: "a `stall` without `end == "silence"`": a stall that ended at the cap fails too."""
    assert snap.validate(_v2(snap, end="silence", stall=True)) == []
    doc = _v2(snap, end="silence", stall=True)
    doc["result"]["end"] = "cap"
    msgs = snap.validate(doc)
    assert any("stall" in m for m in msgs), msgs


def test_v2_winner_stall_allowed_only_with_stall_true(snap):
    """H-052: "`stall` ... `winner` is then `"stall"`": winner `stall` validates with stall true; a wipe document (stall false) whose winner is
    `stall` fails (DRAFT-winner-stall: the story does not say which message; the test needs one naming winner or stall)."""
    assert snap.validate(_v2(snap, end="silence", stall=True)) == []
    doc = _v2(snap)
    doc["result"]["winner"] = "stall"
    doc["result"]["agree"] = False
    msgs = snap.validate(doc)
    assert any("stall" in m or "winner" in m for m in msgs), msgs


def test_v2_stall_true_needs_winner_stall(snap):
    """H-052: "`stall`: true when `end` is `silence` and both sides have survivors. `winner` is then `"stall"`, not `"draw"`": a stall whose winner
    is `draw` fails."""
    assert snap.validate(_v2(snap, end="silence", stall=True)) == []
    doc = _v2(snap, end="silence", stall=True)
    doc["result"]["winner"] = "draw"
    msgs = snap.validate(doc)
    assert any("stall" in m or "winner" in m for m in msgs), msgs


def test_v2_stall_agree_must_be_false(snap):
    """H-052: "`agree` is false and the row is flagged": a stall with `agree` true fails (the existing agree rule already forces false while predict
    is A or B and winner is `stall`; the control is the stall document, which validates)."""
    assert snap.validate(_v2(snap, end="silence", stall=True)) == []
    doc = _v2(snap, end="silence", stall=True)
    doc["result"]["agree"] = True
    assert snap.validate(doc) != []


def test_v2_unknown_mode_is_rejected(snap):
    """H-052: "No other mode exists": a mode other than both_same_point and hold_and_attack fails, naming mode."""
    assert snap.validate(_v2(snap)) == []
    doc = _v2(snap)
    doc["orders"]["mode"] = "guard"
    msgs = snap.validate(doc)
    assert any("mode" in m for m in msgs), msgs


def test_v2_unknown_end_is_rejected(snap):
    """H-052: `result.end` is `"wipe"`, `"silence"` or `"cap"`: any other value fails, naming end."""
    assert snap.validate(_v2(snap)) == []
    doc = _v2(snap)
    doc["result"]["end"] = "timeout"
    msgs = snap.validate(doc)
    assert any("end" in m for m in msgs), msgs


def test_v2_stall_key_missing_is_rejected(snap):
    """H-052: "New `result.stall`": a v2 result without `stall` fails naming it (DRAFT-stall-required: the story lists `orders` and `result.end` as the
    required ones and says `stall` is a new key; the test takes it as required so a stall cannot hide by omission)."""
    assert snap.validate(_v2(snap)) == []
    doc = _v2(snap)
    del doc["result"]["stall"]
    msgs = snap.validate(doc)
    assert any("stall" in m for m in msgs), msgs


def test_v2_point_must_be_a_pair_of_numbers(snap):
    """H-052: `"point": [x, y]`: a one-element point fails, naming point."""
    assert snap.validate(_v2(snap)) == []
    doc = _v2(snap)
    doc["orders"]["point"] = [120.0]
    msgs = snap.validate(doc)
    assert any("point" in m for m in msgs), msgs


def test_v2_write_read_round_trips(snap, tmp_path):
    """H-052: "`om-fight-1` files still validate (the checker accepts both and the page shows the version)": a v2 file writes and reads back
    byte-identically on a second write, like a v1 file."""
    doc = _v2(snap, end="silence", stall=True, mode="hold_and_attack", attacker="B")
    first, second = tmp_path / "a.fight.json", tmp_path / "b.fight.json"
    snap.write(doc, first)
    back = snap.read(first)
    assert back == doc
    snap.write(back, second)
    assert first.read_bytes() == second.read_bytes()


def test_v1_file_round_trips_unchanged_beside_v2(snap, tmp_path):
    """H-052: "`om-fight-1` files still validate": a v1 document written and read keeps schema om-fight-1 and gains no `orders`."""
    doc = snap.example()
    path = tmp_path / "v1.fight.json"
    snap.write(doc, path)
    back = snap.read(path)
    assert back["schema"] == "om-fight-1" and "orders" not in back and back == doc


def test_frame_ticks_unchanged_by_v2(snap):
    """H-052 Tests: "`frame_ticks` unchanged": the same two values the H-039 tests pin."""
    assert snap.frame_ticks(300, 20) == [0, 100, 200, 300]
    ticks = snap.frame_ticks(12000, 20)
    assert ticks[0] == 0 and ticks[-1] == 12000 and len(ticks) <= snap.MAX_FRAMES


# ================================================================ H-053 defect: range rings need ranges in the fight file
# Brief to the test writer, 2026-11-02 (the Architect amends H-053's Tests line and SNAPSHOT.md): the replay builds its rows with range 0.0 because an om-fight-2 file carries no
# range, so no range ring is drawn and the legend says "no range". Intended: a top-level optional `ranges` map {role: range in wu}, still schema om-fight-2; run.py writes it,
# snapshot.py accepts and documents it, `example(schema=om-fight-2)` carries one. The file without `ranges` stays valid (v1 files and older v2 files).

def _with_ranges(snap, ranges=None):
    doc = _v2(snap)
    doc["ranges"] = {"Raider": 200.0} if ranges is None else ranges
    return doc


def test_control_v2_without_ranges_and_v1_example_stay_valid(snap):
    """Control, green today: an om-fight-2 document with no `ranges` validates and the v1 example carries no `ranges`, so `ranges` is optional and the reds below are the missing key."""
    assert snap.validate(_v2(snap)) == []
    assert "ranges" not in snap.example() and snap.validate(snap.example()) == []


def test_v2_accepts_a_ranges_map_and_round_trips_it(snap, tmp_path):
    """Brief 2026-11-02: "snapshot validate accepts a `ranges` map" ({role: range}, numbers, zero or more): a v2 document with {"Raider": 200.0, "Bombard": 1200} validates, writes and reads
    back equal, and a second write is byte-identical."""
    doc = _with_ranges(snap, {"Raider": 200.0, "Bombard": 1200})
    assert snap.validate(doc) == [], snap.validate(doc)
    first, second = tmp_path / "a.fight.json", tmp_path / "b.fight.json"
    snap.write(doc, first)
    back = snap.read(first)
    assert back["ranges"] == doc["ranges"]
    snap.write(back, second)
    assert first.read_bytes() == second.read_bytes()


@pytest.mark.parametrize("bad", [{"Raider": "far"}, {"Raider": -1.0}, {"Raider": None}, {"Raider": True}, ["Raider", 200.0], 200.0],
                         ids=["non-numeric", "negative", "null", "bool", "list", "number"])
def test_v2_rejects_a_malformed_ranges_map_naming_ranges(snap, bad):
    """Brief 2026-11-02: "rejects a malformed one (non-numeric, negative)". The well-formed sibling validates first (so this is red until `ranges` is a known key), then each malformed
    value (a non-numeric or null or bool range, a negative range, a list, a bare number) is rejected with a message that names `ranges`."""
    assert snap.validate(_with_ranges(snap)) == [], snap.validate(_with_ranges(snap))
    msgs = snap.validate(_with_ranges(snap, bad))
    assert msgs and any("ranges" in m for m in msgs), msgs


def test_v2_example_carries_a_ranges_map_for_its_roles(snap):
    """Brief 2026-11-02: "the example() carries one". `example(schema=om-fight-2)` has a `ranges` map that validates, whose keys include every role in its frames and whose values
    are numbers at or above zero; the v1 example is unchanged (no `ranges`)."""
    doc = snap.example(schema=snap.SCHEMA_V2)
    assert snap.validate(doc) == [], snap.validate(doc)
    roles = {u["role"] for f in doc["frames"] for u in f["units"]}
    assert "ranges" in doc and roles <= set(doc["ranges"]), (roles, doc.get("ranges"))
    assert all(isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0 for v in doc["ranges"].values())
    assert "ranges" not in snap.example()
