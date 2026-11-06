# Rule pins: R-096-08, R-096-02
# spec: docs/reports/2026-11-06-stage4-fix-plan.md::F3 (per-group orders with a release trigger); Story H-088 follow-up; Flag client
"""Stage 4 fix F3, the runner part: per-group orders with an optional release trigger (scripts/skilllab/arena/groups.py, run.py).

Layout schema (additive, DEC-stage4-group-orders-2026-11-06): `orders = "groups"`; unit rows carry `group = "<name>"`; `[[order_groups]]` rows carry
`side` ("A"/"B"), `group`, `order` ("hold" or "attack_move"), `to` ([x, y] or "enemy_centroid"), and for a hold an optional `release = {point = [x, y], radius = R}`:
on the first tick on which any living enemy unit is within R wu of the point, the group is given an attack-move to `to`. A hold is a guard (R-096-08) under the
stage 4 rule set. The fight file's `orders` gains `groups`: per group the unit ids, order, `to`, `release` and `released_at` (the tick, or null).

Fixture: `small_flat`, no features. Side A: eight Vanguards at x 1000 holding, released when side B is within 300 wu of (2500, 2000); side B: eight Vanguards at
x 3000 attack-moving to (1800, 2000). Unit ids: side A 1 to 8, side B 9 to 16 (spawn order). The release tick is recomputed here from the engine's own positions after
every step (Engine.step wrapped), the first tick on which the trigger holds."""
import hashlib
import json
import math
from pathlib import Path

import pytest

import h063_fixtures as fx
from scripts.skilllab.engine import Engine

ROOT = Path(__file__).resolve().parents[3]
POINT, RADIUS = (2500.0, 2000.0), 300.0


def groups_layout(lid, release=True):
    lay = fx.layout(lid, "open_field", "small_flat", None, orders="groups")
    lay["defender"] = ""
    for u in lay["side_a"]["units"]:
        u["group"] = "post"
    for u in lay["side_b"]["units"]:
        u["group"] = "walkers"
    hold = {"side": "A", "group": "post", "order": "hold", "to": "enemy_centroid"}
    if release:
        hold["release"] = {"point": list(POINT), "radius": RADIUS}
    lay["order_groups"] = [hold, {"side": "B", "group": "walkers", "order": "attack_move", "to": [1800.0, 2000.0]}]
    return lay


@pytest.fixture()
def per_tick(monkeypatch):
    """Wrap Engine.step: after every step, the first tick on which a side B unit is within RADIUS of POINT is recorded in the returned dict."""
    seen = {"tick": 0, "first": None}
    real = Engine.step

    def step(self, w):
        real(self, w)
        seen["tick"] += 1
        if seen["first"] is None and any(self.unit_alive(w, u) and math.dist(self.unit_pos(w, u), POINT) <= RADIUS for u in range(9, 17)):
            seen["first"] = seen["tick"]
    monkeypatch.setattr(Engine, "step", step)
    return seen


def _run(lay, tmp, *extra):
    proc, doc = fx.fight(lay, tmp, 1, "--sight", "on", "--cap-seconds", "40", *extra)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return doc


def test_the_hold_releases_on_the_first_tick_the_trigger_holds(tmp_path, per_tick):
    """F3: evaluated from engine state each tick. `released_at` equals the first tick at which a side B unit is within 300 wu of the point; the group did not move before."""
    doc = _run(groups_layout("L-9830"), tmp_path)
    groups = {g["group"]: g for g in doc["orders"]["groups"]}
    assert per_tick["first"] is not None and groups["post"]["released_at"] == per_tick["first"], (groups["post"], per_tick)
    assert groups["walkers"]["released_at"] is None and groups["walkers"]["units"] == list(range(9, 17)) and groups["post"]["units"] == list(range(1, 9))
    assert groups["post"]["release"] == {"point": list(POINT), "radius": RADIUS} and groups["post"]["order"] == "hold"
    first = doc["frames"][0]["units"]
    after = next(f for f in doc["frames"] if f["tick"] > groups["post"]["released_at"])
    assert all(a["x"] > first[i]["x"] + 20 for i, a in enumerate(after["units"]) if a["side"] == "A"), "the released group walks on"


def test_without_a_release_the_hold_stays_put_and_records_null(tmp_path):
    """A hold with no `release` never moves on its own: released_at is null and the group's units are where they began at every frame (they may still step to fire; the fixture is out of range)."""
    lay = groups_layout("L-9831", release=False)
    doc = _run(lay, tmp_path)
    post = next(g for g in doc["orders"]["groups"] if g["group"] == "post")
    assert post["released_at"] is None and post["release"] is None
    start = {u["id"]: (u["x"], u["y"]) for u in doc["frames"][0]["units"]}
    assert all(abs(u["x"] - start[u["id"]][0]) < 5 for f in doc["frames"][:3] for u in f["units"] if u["side"] == "A")


def test_a_second_run_is_byte_identical(tmp_path):
    a = _run(groups_layout("L-9832"), tmp_path / "a")
    b = _run(groups_layout("L-9832"), tmp_path / "b")
    a.pop("layout_path")   # the layout was written under two temporary directories; every other byte is the fight's
    b.pop("layout_path")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True) and a["orders"]["groups"][0]["released_at"] is not None


def test_a_layout_without_group_keys_writes_no_groups_and_the_old_stage3_fight_reproduces_byte_for_byte(tmp_path):
    """The new keys are additive: a both_same_point fight has no `orders.groups`, and the committed stage 3 cover fight (L-0039 seed 1, `--sight off`) is reproduced
    byte for byte by today's runner (the stage 3 determinism line; the conversion for `--sight off` is untouched)."""
    lay = fx.layout("L-9833", "open_field", "small_flat", None)
    lay["defender"] = ""
    proc, doc = fx.fight(lay, tmp_path / "plain", 1, "--sight", "on", "--cap-seconds", "5")
    assert proc.returncode == 0 and "groups" not in doc["orders"]
    committed = ROOT / "docs/northstar/research/layer_dynamics/arena/stage3/L-0039-s1.fight.json"
    out = tmp_path / "s3"
    proc = fx.run(ROOT / "docs/northstar/research/layer_dynamics/catalogue/L-0039.toml", out, 1, "--sight", "off", "--control-dir", tmp_path / "s3c")
    assert proc.returncode == 0, proc.stdout
    assert (out / "L-0039-s1.fight.json").read_bytes() == committed.read_bytes()


def test_a_unit_without_a_group_or_a_group_without_a_unit_is_rejected(tmp_path):
    """`REJECT <id> G2 groups: ...` (exit 2), runner-local like the layer check: every unit of a groups layout names a group that has an `order_groups` row."""
    lay = groups_layout("L-9834")
    del lay["side_a"]["units"][3]["group"]
    proc = fx.run(fx.write(lay, tmp_path), tmp_path / "out", 1, "--sight", "on", "--cap-seconds", "2")
    assert proc.returncode == 2 and "REJECT L-9834 G2 groups: side_a unit 3" in proc.stdout, proc.stdout
    lay = groups_layout("L-9835")
    lay["side_b"]["units"][0]["group"] = "ghost"
    proc = fx.run(fx.write(lay, tmp_path / "b"), tmp_path / "out_b", 1, "--sight", "on", "--cap-seconds", "2")
    assert proc.returncode == 2 and "REJECT L-9835 G2 groups: side_b unit 0" in proc.stdout, proc.stdout


def test_the_layout_dump_round_trips_the_group_keys():
    """produce.dump_toml writes the unit `group` and the `[[order_groups]]` rows, so a producer can generate them and tomllib reads them back unchanged."""
    import tomllib
    from scripts.skilllab.catalogue import produce
    lay = groups_layout("L-9836")
    back = tomllib.loads(produce.dump_toml(dict(lay, predict_why="x")))
    assert back["order_groups"] == lay["order_groups"] and back["side_a"]["units"][0]["group"] == "post" and back["orders"] == "groups"
