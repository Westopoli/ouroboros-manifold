# spec: skill lab bindings for ping, set_layer, set_emission and the visibility readers - real library (R-162-01 to R-162-05, R-163-01, R-002-01)
"""Each test fails with 'engine wrapper has no <name>' until scripts/skilllab/engine.py binds it.

Wrapper names (world handle first, like the rest of Engine; the wrapper cannot list units, so the readers take the
candidate enemy ids): ping(w, caster, layer, x, y) -> int, set_layer(w, ids, layer), set_emission(w, ids, on),
visible_enemies(w, side, enemy_ids) -> set (om_player_can_see: sight or ping), seen_by_sight(w, side, enemy_ids) -> set
(union over the side's own units of om_unit_can_see: sight only, never the ping reveal; own_ids are found by the
wrapper), set_ping_params(w, radius=None, reach=None, reveal_ticks=None, cooldown_ticks=None), unit_layer(w, u) (exists).
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine  # noqa: E402

RAIDER, INTERCEPTOR, SUPPLY = 0, 1, 6   # unit type ids of the csim tests; Supply never fires
HIGH = 4          # engine layer 4: four layers above a layer-0 caster, so no passive sight
RADIUS, REACH, REVEAL, COOLDOWN = 500.0, 2000.0, 40, 400


@pytest.fixture(scope="module")
def lib():
    return engine.Engine()


@pytest.fixture
def world(lib):
    w = lib.new_world(0)
    yield w
    lib.free_world(w)


def _need(lib, *names):
    for n in names:
        assert hasattr(lib, n), "engine wrapper has no %s" % n


def _steps(lib, w, n):
    for _ in range(n):
        lib.step(w)


def _scene(lib, w, enemy_x=1600.0):
    """Side 0: Raider caster at the origin, layer 0. Side 1: Supply on layer 4 at (enemy_x, 0)."""
    caster = lib.spawn(w, RAIDER, 0, 0.0, 0.0, 0)
    enemy = lib.spawn(w, SUPPLY, 1, enemy_x, 0.0, HIGH)
    return caster, enemy


def test_1_far_apart_nothing_seen_then_ping_reveals_but_not_by_sight(lib, world):
    _need(lib, "ping", "visible_enemies", "seen_by_sight")
    w = world
    caster, enemy = _scene(lib, w)
    mine = lib.spawn(w, SUPPLY, 0, 9000.0, 9000.0, 0)
    assert lib.visible_enemies(w, 0, [enemy]) == set() and lib.visible_enemies(w, 1, [mine]) == set()
    assert lib.seen_by_sight(w, 0, [enemy]) == set()
    assert lib.ping(w, caster, HIGH, 1500.0, 0.0) == 0
    _steps(lib, w, 1)
    assert lib.visible_enemies(w, 0, [enemy]) == {enemy}
    assert lib.seen_by_sight(w, 0, [enemy]) == set(), "a ping reveal is not sight"


def test_2_wrong_layer_reveals_nothing(lib, world):
    _need(lib, "ping", "visible_enemies")
    w = world
    caster, enemy = _scene(lib, w)
    # the control must be on the named layer inside the radius AT THE CAST (a ping reveals only those)
    other = lib.spawn(w, SUPPLY, 1, 1500.0, 100.0, HIGH - 1)
    assert lib.ping(w, caster, HIGH - 1, 1500.0, 0.0) == 0, "control: the call itself is accepted"
    _steps(lib, w, 1)
    assert lib.visible_enemies(w, 0, [enemy]) == set()
    assert lib.visible_enemies(w, 0, [other]) == {other}, "control: the named layer is revealed"


def test_3_reach_and_cooldown_refusals(lib, world):
    _need(lib, "ping", "visible_enemies")
    w = world
    caster, far = _scene(lib, w, enemy_x=REACH + 600.0)
    assert lib.ping(w, caster, HIGH, REACH + 600.0, 0.0) != 0, "beyond the reach"
    _steps(lib, w, 1)
    assert lib.visible_enemies(w, 0, [far]) == set()
    near = lib.spawn(w, SUPPLY, 1, 1500.0, 0.0, HIGH)
    second = lib.spawn(w, RAIDER, 0, 0.0, 300.0, 0)
    assert lib.ping(w, caster, HIGH, 1500.0, 0.0) == 0, "control: inside reach is accepted"
    assert lib.ping(w, caster, HIGH, 1500.0, 0.0) != 0, "same caster inside the cooldown"
    assert lib.ping(w, second, HIGH, 1500.0, 0.0) == 0, "another caster pings at once"


def test_4_reveal_ends_after_the_reveal_time(lib, world):
    _need(lib, "ping", "visible_enemies")
    w = world
    caster, enemy = _scene(lib, w)
    assert lib.ping(w, caster, HIGH, 1500.0, 0.0) == 0
    _steps(lib, w, 1)
    assert lib.visible_enemies(w, 0, [enemy]) == {enemy}, "control: revealed while the ping is live"
    reveal = int(lib.get_param(w, lib.param_id("OM_TP_PING_REVEAL_TICKS")))
    _steps(lib, w, reveal + 2)
    assert lib.visible_enemies(w, 0, [enemy]) == set()


def test_5_a_larger_radius_reveals_a_unit_the_default_misses(lib, world):
    _need(lib, "ping", "visible_enemies", "set_ping_params")
    w = world
    caster, enemy = _scene(lib, w, enemy_x=1500.0 + RADIUS + 200.0)
    assert lib.ping(w, caster, HIGH, 1500.0, 0.0) == 0
    _steps(lib, w, 1)
    assert lib.visible_enemies(w, 0, [enemy]) == set(), "control: default radius misses it"
    w2 = lib.new_world(0)
    try:
        caster2, enemy2 = _scene(lib, w2, enemy_x=1500.0 + RADIUS + 200.0)
        lib.set_ping_params(w2, radius=RADIUS + 400.0)
        assert lib.ping(w2, caster2, HIGH, 1500.0, 0.0) == 0
        _steps(lib, w2, 1)
        assert lib.visible_enemies(w2, 0, [enemy2]) == {enemy2}
    finally:
        lib.free_world(w2)


def test_6_set_layer_moves_the_group(lib, world):
    _need(lib, "set_layer", "unit_layer")
    w = world
    a = lib.spawn(w, RAIDER, 0, 300.0, 400.0, 2)
    b = lib.spawn(w, RAIDER, 0, 300.0, 460.0, 2)
    ctl = lib.spawn(w, RAIDER, 0, 1500.0, 1500.0, 2)
    lib.set_layer(w, [a, b], 3)
    _steps(lib, w, 80)    # a Raider takes 20 ticks to cross; the margin is generous
    assert [lib.unit_layer(w, u) for u in (a, b)] == [3, 3]
    assert lib.unit_layer(w, ctl) == 2, "control: an unordered unit stays"


def test_7_an_emitting_force_is_seen_from_further_across_layers(lib, world):
    _need(lib, "set_emission", "visible_enemies")
    w = world
    obs = lib.spawn(w, INTERCEPTOR, 1, 0.0, 0.0, 2)          # sensor 1000
    target = lib.spawn(w, SUPPLY, 0, 600.0, 0.0, 3)          # one layer up, 600 away
    lib.set_param(w, lib.param_id("OM_TP_EMIT_SEEN_MULT"), 2.0)
    _steps(lib, w, 1)
    assert lib.visible_enemies(w, 1, [target]) == set(), "control: silent, not seen at 600"
    lib.set_emission(w, [target], True)
    _steps(lib, w, 1)
    assert lib.visible_enemies(w, 1, [target]) == {target}
    lib.set_emission(w, [target], False)
    _steps(lib, w, 1)
    assert lib.visible_enemies(w, 1, [target]) == set(), "and silent again hides it"


def test_8_walking_into_true_vision_is_sight_and_a_subset_of_visible(lib, world):
    _need(lib, "visible_enemies", "seen_by_sight")
    w = world
    walker = lib.spawn(w, RAIDER, 0, 0.0, 0.0, 0)
    enemy = lib.spawn(w, SUPPLY, 1, 2500.0, 0.0, 0)
    assert lib.seen_by_sight(w, 0, [enemy]) == set(), "control: out of sight at the start"
    lib.order_move(w, [walker], 2500.0, 0.0)
    for _ in range(600):
        lib.step(w)
        if lib.seen_by_sight(w, 0, [enemy]):
            break
    sight = lib.seen_by_sight(w, 0, [enemy])
    assert sight == {enemy}
    assert sight <= lib.visible_enemies(w, 0, [enemy])
