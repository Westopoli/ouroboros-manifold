# spec: docs/stories/H-040.md ("Orders and fight end"); docs/northstar/plans/engine-rules-2026-11-08/round6.md (L5); DEC-formation-kept-2026-11-19, DEC-stuck-behind-is-expected-2026-11-19
"""Round 6, L5 (part two): the runner names a quiet end in which every order is finished `apart` (DEC-formation-kept-2026-11-19).

round6.md L5: "A fight that goes quiet with both sides alive is a defect to trace, except one kind of end, which is expected without a player's micro: no living unit holds a destination or a
target, and no two living enemies stand within the notice distance of either (weapon range plus a tenth, on layers the unit can reach). The runner writes that end as `end: "apart"` in place of
`"silence"`, with `stall` false, and the fight document says how far the nearest enemies stand. ... a quiet end of any other kind (a unit still holds a destination or a target, or two enemies
stand within notice and do not fire) stays `silence` with `stall` true". docs/stories/H-040.md "Orders and fight end": a quiet fight with both sides alive is flagged and brought to him.

WHAT THIS FILE PINS (the lab builder builds to it; the names are the test writer's, in the style of `result.end` / `result.stall`):
  result.end                 "apart" in place of "silence" for the end above. `snapshot._ENDS` gains it.
  result.stall               false on an apart end (a stall is a `silence` end with both alive, as today).
  result.winner              not "stall" on an apart end (the document says "draw" today for an end that is neither a wipe nor a stall; the test does not pin which word, only not "stall").
  result.nearest_enemy_wu    NEW, a number in wu, written only on an apart end: the distance between the nearest two living enemies at the last tick (same layer, flat, as the last frame's x and y
                             give it, rounded to two places like the frames). A document with any other end carries no such key, so a fight that ends by elimination is byte-identical to today's.
  The notice distance of a unit is its role's attack range times 1.1 (`csrc/notice_internal.h` OM_NOTICE_MARGIN 0.1; the roster ranges are `produce._roster_ranges()`: Raider 200, Interceptor 250,
  Vanguard 300, Warden 350, Bastion 800, Bombard 1200). A pair counts only if one of the two could fight the other: the same layer, or within the unit's reach up or down (`csrc/unit.c`
  om_tac_in_reach). The engine's reach, which the planted fixtures state: with `--sight off` every type's reach is (0 up, 0 down) (`Engine.profile_reach`, read in the test), so two units on
  different layers can never fight; with `--sight on` it is (0 up, 1 down) (`run.REACH_UP`, `run.REACH_DOWN`), so a unit may fight an enemy one layer below it and no other layer.

THE FIXTURES, as cheap as the neighbours' (tests/skilllab/arena/test_run.py): one to three units a side, built as layouts and run through `run.fight` and `run._document` (no catalogue rule is applied to a
layout given to `run.fight`; the R4 headcount minimum is for the CLI, which the one CLI test here meets with the neighbours' 8:8 stall fixture). Three kinds:
  * REAL: `hold:A`, A at x 1100 and x 2900 (y 2000), B one unit at (2000, 2000), the empty centre of A. No unit holds an order after tick 0 and the enemies stand 900 wu apart: a real apart end at tick 200
    (measured 2026-11-19, before the build: end silence, survivors 2:1; the 8:8 stall fixture of test_run.py is the same shape and is also apart: see the report's list of the existing tests that said silence).
  * PLANTED STATE: a unit that still holds a destination or a target is made by wrapping `Engine.unit_destination` / `Engine.unit_target` to answer for one unit id (the same way
    test_invariants_wiring.py plants a fault by wrapping `Engine.step`): there is no cheap real fight in which a unit keeps an order and stands still for ten seconds. The runner is held to reading the
    state through those two engine calls, which it already does (`blocked_now`, `_frame`).
  * FROZEN WORLD: `Engine.step` and `Engine.order_attack_move` do nothing, so nobody moves, fires or holds an order and the fight goes quiet at tick 200 with the units where the layout put them. This is the
    only cheap way to have two idle enemies within notice that do not fire (the real engine closes in and fires).

The stage 1 fight (L-0054, sight off, seed 1) is a real fight of about a minute; it is not behind the slow tier because its neighbours of that length (test_engine_rules_r*.py pinned fights) are not.
Every test names H-040 and DEC-formation-kept-2026-11-19 above."""
import contextlib
import hashlib
import io
import math
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import h063_fixtures as fx  # noqa: E402
import h088_fixtures as f8  # noqa: E402
from scripts.skilllab.arena import run, snapshot  # noqa: E402
from scripts.skilllab.catalogue.produce import _roster_ranges  # noqa: E402
from scripts.skilllab.engine import Engine  # noqa: E402
from test_closeup import PINS, _layout as closeup_layout  # noqa: E402
from test_run import make_stall_layout, write_layout_orders  # noqa: E402

CATALOGUE = ROOT / "docs" / "northstar" / "research" / "layer_dynamics" / "catalogue"
NOTICE = 1.1                  # 1 + OM_NOTICE_MARGIN (csrc/notice_internal.h)
FIELD = "nearest_enemy_wu"    # the name this file pins for the distance, in `result`


def tiny(a, b, orders="both_same_point", lid="X-apart"):
    """A layout of single rows (role, x, y, layer) a side, small_flat; `orders` as the runner reads it."""
    def rows(units):
        return [{"role": r, "x": x, "y": y, "layer": layer} for r, x, y, layer in units]
    return {"id": lid, "landscape": "small_flat", "orders": orders, "predict": "A", "side_a": {"units": rows(a)}, "side_b": {"units": rows(b)}}


# A real apart end: A is two Vanguards 1800 wu apart, B one Vanguard at A's centre of mass, which B's attack-move reaches at once (hold:A: only B is ordered).
REAL = tiny([("Vanguard", 1100.0, 2000.0, 0), ("Vanguard", 2900.0, 2000.0, 0)], [("Vanguard", 2000.0, 2000.0, 0)], "hold:A")
A_UNIT, B_UNIT = 1, 3         # unit ids in REAL: spawn order is side A then side B, ids from 1


def document(layout, sight="off", seconds=60):
    frames, last, end, orders = run.fight(layout, 1, sight, seconds)
    return run._document(layout, "x.toml", 1, sight, frames, last, end, orders)


def nearest(doc):
    """The distance between the nearest two living enemies in the last frame (all fixtures stand on layer 0 or are asked about only by `end`)."""
    units = [u for u in doc["frames"][-1]["units"] if u["alive"]]
    return min(math.hypot(a["x"] - b["x"], a["y"] - b["y"]) for a in units if a["side"] == "A" for b in units if b["side"] == "B")


def notice(doc, side):
    ranges = doc["ranges"]
    return max(ranges[u["role"]] * NOTICE for u in doc["frames"][-1]["units"] if u["alive"] and u["side"] == side)


def freeze(monkeypatch):
    """The frozen world of the module docstring: no step, no order."""
    monkeypatch.setattr(Engine, "step", lambda self, w: None)
    monkeypatch.setattr(Engine, "order_attack_move", lambda self, w, ids, x, y: None)


def is_apart(doc):
    r = doc["result"]
    return (r["end"], r["stall"]) == ("apart", False) and r["winner"] != "stall" and isinstance(r.get(FIELD), (int, float))


def is_stall(doc):
    r = doc["result"]
    return (r["end"], r["stall"], r["winner"]) == ("silence", True, "stall") and FIELD not in r


# ---------------------------------------------------------------- the stage 1 fight

def test_L5_the_stage_1_fight_ends_apart_with_the_nearest_enemies_beyond_every_survivors_notice_distance():
    """H-040 / DEC-formation-kept-2026-11-19: L-0054 (sight off, seed 1; about a minute) ends with both sides alive, each survivor having finished its order, the nearest enemies beyond notice
    (round6.md E5; measured on this branch 2026-11-19: 14 against 22 at tick 10,860, end silence). Under L5 that end is `apart`: `end` apart, `stall` false, both sides alive, not capped, no survivor holds a target in the last frame, the document validates, and `nearest_enemy_wu`
    is the distance between the nearest two survivors (as the last frame gives it, within 0.05 wu) and is greater than the notice distance of every survivor. Red today: the end is `silence`, `stall` true."""
    with open(CATALOGUE / "L-0054.toml", "rb") as f:
        layout = tomllib.load(f)
    doc = document(layout, "off", snapshot.CAP_SECONDS)
    res = doc["result"]
    assert res["end"] == "apart" and res["stall"] is False and res["capped"] is False, res
    assert min(res["survivors"]) > 0 and res["winner"] != "stall", res
    assert snapshot.validate(doc) == []
    last = doc["frames"][-1]["units"]
    assert all(u["target"] is None for u in last if u["alive"]), "a survivor still holds a target in the last frame"
    assert abs(res[FIELD] - nearest(doc)) <= 0.05, (res[FIELD], nearest(doc))
    assert res[FIELD] > max(notice(doc, "A"), notice(doc, "B")), "the nearest enemies are within a survivor's notice distance: %s" % res


# ---------------------------------------------------------------- planted fights

def test_L5_real_fight_with_every_order_finished_and_the_enemies_far_apart_ends_apart():
    """H-040 / DEC-formation-kept-2026-11-19: REAL (module docstring): no unit holds a destination or a target at the quiet end and the nearest enemies are 900 wu apart on one layer, past the Vanguard's
    330 wu notice distance. `end` apart, `stall` false, about 10 s in (ticks 200 to 240), `nearest_enemy_wu` 900 (within 1 wu), the document validates. Red today: the end is `silence`."""
    doc = document(REAL)
    res = doc["result"]
    assert is_apart(doc) and res["capped"] is False and res["survivors"] == [2, 1], res
    assert 200 <= res["ticks"] <= 240 and abs(res[FIELD] - 900.0) <= 1.0, res
    assert snapshot.validate(doc) == []


def test_L5_the_cli_writes_an_apart_end_as_no_stall_and_exits_0(tmp_path):
    """H-040 "Orders and fight end" (the runner prints STALL and exits 0 for a stall): the neighbours' 8:8 stall fixture (`hold:A`, A in two clusters, B at A's empty centre) through `run.main`:
    exit 0, no STALL line, the file reads back (`snapshot.read`) with end apart, stall false, survivors 8:8, and a `nearest_enemy_wu` over 800 wu (the clusters stand about 820 wu from B). The
    printed line's wording is the builder's. Red today: the end is `silence` and the line says STALL."""
    path = write_layout_orders(make_stall_layout("L-9101"), tmp_path / "layouts", "hold:A")
    out, err, buf = tmp_path / "out", io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
        code = run.main(["--layout", str(path), "--seed", "1", "--out", str(out), "--allow-invalid"])
    assert code == 0, err.getvalue()[-800:] + buf.getvalue()[-400:]
    assert not any("STALL" in line for line in buf.getvalue().splitlines()), buf.getvalue()
    doc = snapshot.read(out / "L-9101-s1.fight.json")
    res = doc["result"]
    assert (res["end"], res["stall"], res["survivors"]) == ("apart", False, [8, 8]), res
    assert res[FIELD] > 800.0, res


@pytest.mark.parametrize("who,kind", [(A_UNIT, "destination"), (B_UNIT, "destination"), (A_UNIT, "target"), (B_UNIT, "target")])
def test_L5_a_quiet_end_where_one_living_unit_still_holds_a_destination_or_a_target_stays_silence(monkeypatch, who, kind):
    """H-040 / DEC-formation-kept-2026-11-19: REAL, with one unit (of side A or of side B) made to answer the engine's `unit_destination` (a point) or `unit_target` (an enemy's id) as if it held one: the
    fight is quiet at tick 200 with the enemies 900 wu apart, yet a unit is still under its order, so the end is `silence`, `stall` true, winner `stall`, no distance in the document, and the
    document validates. Green today (it is the end the runner writes today) and must stay green: it pins that `apart` needs every unit free of an order."""
    if kind == "destination":
        real = Engine.unit_destination
        monkeypatch.setattr(Engine, "unit_destination", lambda self, w, u: (2000.0, 2600.0) if u == who else real(self, w, u))
    else:
        real = Engine.unit_target
        monkeypatch.setattr(Engine, "unit_target", lambda self, w, u: (B_UNIT if who == A_UNIT else A_UNIT) if u == who else real(self, w, u))
    doc = document(REAL)
    assert is_stall(doc) and 200 <= doc["result"]["ticks"] <= 240, doc["result"]
    assert snapshot.validate(doc) == []


# (role A, role B, distance in wu, the end). Each fixture is a frozen world: two idle units that fire at nobody. The notice distance of a Vanguard is 330, a Warden 385, a Raider 220.
NOTICE_CASES = [
    ("Vanguard", "Vanguard", 320.0, "silence"),   # inside the notice distance of both (and outside the 300 wu range: they would walk, and do not here)
    ("Vanguard", "Vanguard", 200.0, "silence"),   # inside the weapon range itself
    ("Vanguard", "Vanguard", 340.0, "apart"),     # just outside the notice distance of both
    ("Warden", "Vanguard", 360.0, "silence"),     # inside the Warden's notice distance (385) only: within notice "of either" is enough
    ("Raider", "Vanguard", 400.0, "apart"),       # outside the Raider's (220) and the Vanguard's (330)
]


@pytest.mark.parametrize("role_a,role_b,dist,end", NOTICE_CASES)
def test_L5_two_idle_enemies_that_do_not_fire_are_apart_only_beyond_the_notice_distance_of_both(monkeypatch, role_a, role_b, dist, end):
    """H-040 / DEC-formation-kept-2026-11-19: FROZEN WORLD, one unit a side on layer 0, `dist` wu apart, nobody holds an order: two idle enemies inside the notice distance of either one (weapon range
    times 1.1) that do not fire end `silence` with `stall` true; beyond both notice distances the end is `apart` and `nearest_enemy_wu` is `dist`. Red today for the `apart` rows (the end is `silence`);
    green today for the `silence` rows."""
    freeze(monkeypatch)
    doc = document(tiny([(role_a, 1000.0, 1000.0, 0)], [(role_b, 1000.0 + dist, 1000.0, 0)]))
    if end == "silence":
        assert is_stall(doc), doc["result"]
    else:
        assert is_apart(doc) and abs(doc["result"][FIELD] - dist) <= 0.05, doc["result"]
        assert dist > max(notice(doc, "A"), notice(doc, "B"))
    assert snapshot.validate(doc) == []


def reach_of_vanguard():
    """(up, down) the engine gives a Vanguard in a fight run `--sight off`: read from a world set up as `run.fight` does for sight off."""
    e = Engine()
    w = e.new_world(1)
    try:
        types = run._register_types(e, w, run._setup_for(tiny([("Vanguard", 0.0, 0.0, 0)], [("Vanguard", 1.0, 0.0, 0)])))
        return e.profile_reach(w, types["Vanguard"][0])
    finally:
        e.free_world(w)


# (sight, layer of A, layer of B, the end): 100 wu apart in the plane, well inside the 300 wu range on one layer.
LAYER_CASES = [
    ("off", 0, 0, "silence"),    # control: the same layer, within notice
    ("off", 0, 1, "apart"),      # sight off: reach (0, 0): neither can fight the other
    ("on", 0, 1, "silence"),     # sight on: reach (0 up, 1 down): the unit on layer 1 fights down at layer 0, so it is within its notice
    ("on", 1, 0, "silence"),     # the same pair, sides swapped
    ("on", 0, 2, "apart"),       # two layers apart: down 1 only, up 0: neither reaches the other
]


@pytest.mark.parametrize("sight,la,lb,end", LAYER_CASES)
def test_L5_a_pair_on_layers_the_units_cannot_fight_across_is_apart_only_if_the_reach_says_neither_can(monkeypatch, sight, la, lb, end):
    """H-040 / DEC-formation-kept-2026-11-19 ("counting only a pair the unit could shoot across layers, as the engine's reach says"): FROZEN WORLD, one Vanguard a side, 100 wu apart in the plane, on
    layers `la` and `lb`. The engine's reach, stated here and read from the engine: sight off gives a Vanguard (0 up, 0 down), sight on (0 up, 1 down) (`run.REACH_UP`, `run.REACH_DOWN`); the pair
    counts as within notice, and the end stays `silence`, only when one of the two can reach the other by those numbers; otherwise it is `apart`. The document carries the nearest distance as a
    number in the apart cases (its value is the builder's: this file pins only that it is there). Red today for the `apart` rows; green for the `silence` rows."""
    assert reach_of_vanguard() == (0, 0) and (run.REACH_UP, run.REACH_DOWN) == (0, 1)
    freeze(monkeypatch)
    doc = document(tiny([("Vanguard", 1000.0, 1000.0, la)], [("Vanguard", 1100.0, 1000.0, lb)]), sight)
    assert (is_apart(doc) if end == "apart" else is_stall(doc)), doc["result"]
    assert snapshot.validate(doc) == []


# ---------------------------------------------------------------- the document

def apart_doc(**result):
    """A valid-looking om-fight-2 document with an apart end, built from `snapshot.example`: both sides alive in the last frame, winner draw."""
    doc = snapshot.example(frames=3, units_per_side=2, schema=snapshot.SCHEMA_V2)
    last = doc["frames"][-1]
    for row in last["units"]:
        row["hp"], row["alive"] = 100.0, True
    last["alive"] = [2, 2]
    doc["result"].update({"winner": "draw", "survivors": [2, 2], "agree": False, "end": "apart", "stall": False, FIELD: 378.0})
    doc["result"].update(result)
    return doc


def test_L5_snapshot_validate_accepts_an_apart_end_with_its_field_and_rejects_the_rest():
    """H-040 / DEC-formation-kept-2026-11-19: `snapshot.validate` accepts `end` apart with `result.nearest_enemy_wu` (a number) and `stall` false; rejects it without the field; rejects it with `stall`
    true (a stall is a silence end); rejects a non-number field. Red today: `apart` is not an end the file knows, so the first assertion fails."""
    assert snapshot.validate(apart_doc()) == []
    missing = apart_doc()
    del missing["result"][FIELD]
    assert any(FIELD in m for m in snapshot.validate(missing)), snapshot.validate(missing)
    stalled = apart_doc(stall=True, winner="stall")
    assert any("stall" in m for m in snapshot.validate(stalled)), snapshot.validate(stalled)
    assert snapshot.validate(apart_doc(**{FIELD: "far"})), "a non-number distance validated"


@pytest.mark.parametrize("end,stall", [("wipe", False), ("cap", False), ("silence", True)])
def test_L5_the_distance_field_belongs_to_the_apart_end_alone(end, stall):
    """DEC-formation-kept-2026-11-19 / byte identity: a document with any other end that carries `result.nearest_enemy_wu` is rejected, so every other file stays as it is today. Green today (an unknown key
    is rejected) and must stay green."""
    doc = apart_doc(end=end, stall=stall, winner="stall" if stall else "draw")
    assert any(FIELD in m for m in snapshot.validate(doc)), snapshot.validate(doc)


# ---------------------------------------------------------------- elimination is unchanged

@pytest.mark.parametrize("case,sight", [("open", "off"), ("open", "on")])
def test_L5_a_fight_that_ends_by_elimination_writes_the_same_bytes_as_before(tmp_path, case, sight):
    """H-040 / DEC-formation-kept-2026-11-19: "A fight that ends by elimination writes the same bytes as today". The two pinned open-field fights of test_closeup.py (`PINS`, wipe at tick 576 sight off and
    558 sight on; layout path replaced as `h088_fixtures._pinned_sha` does) through `run.main`: the fight file and `results.md` hash to the recorded sha256. Green today, must stay green; it
    stays green only if the apart branch adds nothing to a wipe."""
    layout = closeup_layout(case)
    proc = fx.run(fx.write(layout, tmp_path / "layouts"), tmp_path / "out", 1, "--sight", sight)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    fight_file = tmp_path / "out" / ("%s-s1.fight.json" % layout["id"])
    got = (f8._pinned_sha(fight_file), hashlib.sha256((tmp_path / "out" / "results.md").read_bytes()).hexdigest())
    assert got == PINS[(case, sight)]
    assert FIELD not in snapshot.read(fight_file)["result"]
