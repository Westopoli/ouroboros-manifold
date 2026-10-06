# spec: docs/northstar/plans/2026-10-05-ping-search-spec.md::Policies (side-blind) and hider scripts; R-162-01, R-162-02
"""search_policies.POLICIES and HIDER_SCRIPTS on hand-built PolicyView objects. No engine, no compiler.
Every test fails with a message naming the missing module while scripts/skilllab/search.py or search_policies.py
does not exist. The numbers are the spec's lab drafts (2026-10-05), provisional.

Readings of the spec the builder must confirm (see the report): a hider script is called
HIDER_SCRIPTS[key](tick, centre, heading_deg, layer, speed) and returns a list of orders, each ("move", x, y) or
("layer", new_layer); a policy's returned list keeps ready-unit order."""
import copy
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from scripts.skilllab import search as S
except Exception as e:  # noqa: BLE001
    S, S_ERR = None, e
try:
    from scripts.skilllab import search_policies as P
except Exception as e:  # noqa: BLE001
    P, P_ERR = None, e

DECIDE = 10
BEARINGS, RINGS, LAYERS = (-60, -30, 0, 30, 60), (0.5, 1.0), range(5)


def _mods():
    assert S is not None, "scripts/skilllab/search.py is missing or fails to import (SearchSetting): %r" % (S_ERR,)
    assert P is not None, "scripts/skilllab/search_policies.py is missing or fails to import: %r" % (P_ERR,)
    return S, P


def _view(**kw):
    s, p = _mods()
    ids = kw.pop("ready", [1, 2, 3, 4])
    d = dict(tick=0, setting=s.SearchSetting(radius=500.0, reach=2000.0, reveal_ticks=100, cooldown_ticks=200,
                                             force=len(ids)),
             centre=(0.0, 0.0), heading_deg=0.0, layer=2, ready=list(ids),
             unit_pos={u: (0.0, 0.0) for u in ids}, revealed={}, memory={})
    d.update(kw)
    return p.PolicyView(**d)


def _expected_targets(centre, heading, reach):
    out = set()
    for b in BEARINGS:
        for r in RINGS:
            a = math.radians(heading + b)
            for layer in LAYERS:
                out.add((layer, round(centre[0] + r * reach * math.cos(a), 3), round(centre[1] + r * reach * math.sin(a), 3)))
    return out


def _key(ping):
    return (ping[1], round(ping[2], 3), round(ping[3], 3))


def _near_set(ping, targets, tol=0.05):
    return any(ping[1] == l and abs(ping[2] - x) < tol and abs(ping[3] - y) < tol for l, x, y in targets)


def test_policy_keys_exist():
    _, p = _mods()
    for k in ("none", "ahead", "sweep", "reactive"):
        assert k in p.POLICIES, "search_policies.POLICIES has no %r" % k


def test_none_returns_nothing():
    _, p = _mods()
    assert p.POLICIES["none"](_view()) == []


def test_ahead_one_ping_per_ready_unit_at_reach_along_heading_on_own_layer():
    _, p = _mods()
    pos = {1: (0.0, 0.0), 2: (100.0, -50.0), 3: (-30.0, 200.0)}
    for heading in (0.0, 90.0, 33.0):
        v = _view(ready=[1, 2, 3], unit_pos=pos, heading_deg=heading, layer=3)
        out = p.POLICIES["ahead"](v)
        assert sorted(o[0] for o in out) == [1, 2, 3], out
        h = math.radians(heading)
        for caster, layer, x, y in out:
            assert layer == 3
            assert abs(x - (pos[caster][0] + 2000 * math.cos(h))) < 1e-6
            assert abs(y - (pos[caster][1] + 2000 * math.sin(h))) < 1e-6


def test_ahead_skips_units_not_ready():
    _, p = _mods()
    v = _view(ready=[2], unit_pos={1: (0.0, 0.0), 2: (5.0, 5.0), 3: (9.0, 9.0)})
    assert [o[0] for o in p.POLICIES["ahead"](v)] == [2]


def test_sweep_walks_all_50_targets_in_order_across_calls_then_repeats():
    _, p = _mods()
    mem, seen, firsts = {}, [], None
    for call in range(25):                                   # 2 ready units each: 25 x 2 = 50 targets
        v = _view(tick=call * DECIDE, ready=[1, 2], memory=mem)
        out = p.POLICIES["sweep"](v)
        assert len(out) == 2 and sorted(o[0] for o in out) == [1, 2], out
        assert len({_key(o) for o in out}) == 2, "one target per ready unit, two units took the same target"
        seen += [_key(o) for o in out]
        firsts = firsts or [_key(o) for o in out]
    assert len(set(seen)) == 50, "50 calls' worth of targets must all differ: got %d distinct" % len(set(seen))
    assert set(seen) == _expected_targets((0.0, 0.0), 0.0, 2000.0), "targets are 5 bearings x 2 rings x 5 layers"
    again = [_key(o) for o in p.POLICIES["sweep"](_view(tick=250, ready=[1, 2], memory=mem))]
    assert again == firsts, "after all 50 the list starts again from its first targets"


def test_sweep_uses_heading_and_force_centre():
    _, p = _mods()
    mem, seen = {}, set()
    for call in range(50):
        out = p.POLICIES["sweep"](_view(tick=call * DECIDE, ready=[1], memory=mem, heading_deg=40.0,
                                        centre=(100.0, -200.0), unit_pos={1: (100.0, -200.0)}))
        seen |= {_key(o) for o in out}
    assert seen == _expected_targets((100.0, -200.0), 40.0, 2000.0)


def test_sweep_memory_keeps_the_position_between_calls():
    _, p = _mods()
    mem = {}
    a = p.POLICIES["sweep"](_view(ready=[1], memory=mem))
    b = p.POLICIES["sweep"](_view(tick=10, ready=[1], memory=mem))
    assert _key(a[0]) != _key(b[0]) and mem, "second call must take the next target; memory must record the position"


def test_sweep_skips_a_target_its_caster_cannot_reach():
    _, p = _mods()
    mem = {}
    seen = []
    for call in range(60):
        v = _view(tick=call * DECIDE, ready=[1], memory=mem, unit_pos={1: (-1000.0, 0.0)})   # force centre at origin
        for o in p.POLICIES["sweep"](v):
            seen.append(o)
            assert math.hypot(o[2] + 1000.0, o[3]) <= 2000.0 + 1e-6, "ping beyond the caster's reach: %r" % (o,)
    assert seen, "a caster that can reach some targets must still ping"
    assert len({_key(o) for o in seen}) < 50, "a caster 1000 wu behind the centre cannot reach every target"


def _reactive_step(mem, tick, revealed, ready=(1, 2)):
    _, p = _mods()
    return p.POLICIES["reactive"](_view(tick=tick, ready=list(ready), revealed=revealed, memory=mem))


def test_reactive_equals_sweep_when_nothing_was_revealed():
    _, p = _mods()
    ma, mb = {}, {}
    for call in range(12):
        a = p.POLICIES["reactive"](_view(tick=call * DECIDE, ready=[1, 2, 3], memory=ma))
        b = p.POLICIES["sweep"](_view(tick=call * DECIDE, ready=[1, 2, 3], memory=mb))
        assert a == b, "call %d: reactive %r != sweep %r" % (call, a, b)


def test_reactive_first_ping_goes_to_revealed_centre_advanced_along_velocity_on_enemy_layer():
    mem = {}
    for k, t in enumerate((100, 110, 120)):
        out = _reactive_step(mem, t, {7: (1200.0 + 40 * k, 300.0, 3), 8: (1200.0 + 40 * k, 340.0, 3)})
    caster, layer, x, y = out[0]
    assert layer == 3, "ping must go to the enemy's layer"
    assert abs(y - 320.0) < 1.0, "enemy moves along +x, so the target stays on y = 320: %r" % (out[0],)
    assert x >= 1280.0 - 1.0 and x <= 1280.0 + 2000.0, "target is the revealed centre moved forward along its velocity"


def test_reactive_static_enemy_is_pinged_at_its_centre():
    mem = {}
    for t in (100, 110, 120):
        out = _reactive_step(mem, t, {7: (1200.0, 300.0, 3), 8: (1200.0, 340.0, 3)})
    assert out[0][1] == 3 and abs(out[0][2] - 1200.0) < 1.0 and abs(out[0][3] - 320.0) < 1.0, out[0]


def test_reactive_keeps_pinging_the_last_known_picture_for_reveal_memory_then_stops():
    _, p = _mods()
    mem = {}
    for k, t in enumerate((100, 110, 120)):
        _reactive_step(mem, t, {7: (1200.0 + 40 * k, 300.0, 3), 8: (1200.0 + 40 * k, 340.0, 3)})
    targets = _expected_targets((0.0, 0.0), 0.0, 2000.0)
    for t in (130, 120 + p.REVEAL_MEMORY - DECIDE):
        out = _reactive_step(mem, t, {})
        assert out and out[0][1] == 3 and abs(out[0][3] - 320.0) < 1.0 and out[0][2] >= 1279.0, \
            "tick %d: still within REVEAL_MEMORY of the last reveal, first ping must chase it: %r" % (t, out)
    for t in (120 + p.REVEAL_MEMORY + DECIDE, 120 + p.REVEAL_MEMORY + 3 * DECIDE):
        out = _reactive_step(mem, t, {})
        assert out and all(_near_set(o, targets) for o in out), \
            "tick %d: past REVEAL_MEMORY the policy is plain sweep, got %r" % (t, out)


def test_every_policy_is_deterministic_and_casts_only_ready_units():
    _, p = _mods()
    revealed = {7: (1200.0, 300.0, 3)}
    for key, fn in p.POLICIES.items():
        for ready in ([], [2], [1, 3, 4]):
            v = _view(tick=100, ready=ready, revealed=revealed,
                      unit_pos={1: (0.0, 0.0), 2: (10.0, 0.0), 3: (0.0, 10.0), 4: (-5.0, 5.0)})
            a, b = fn(copy.deepcopy(v)), fn(copy.deepcopy(v))
            assert a == b, "%s is not deterministic: %r vs %r" % (key, a, b)
            assert all(o[0] in ready for o in a), "%s cast with a unit not in ready: %r (ready %r)" % (key, a, ready)
            assert len({o[0] for o in a}) == len(a), "%s cast twice with one unit in one call" % key


# ---- hider scripts. Reading: script(tick, centre, heading_deg, layer, speed) -> [("move", x, y) | ("layer", n)]

def _orders(key, tick, centre=(0.0, 0.0), heading=0.0, layer=2, speed=4.0):
    _, p = _mods()
    assert key in p.HIDER_SCRIPTS, "search_policies.HIDER_SCRIPTS has no %r" % key
    return list(p.HIDER_SCRIPTS[key](tick, centre, heading, layer, speed))


def test_hider_script_keys():
    _, p = _mods()
    assert {"still", "drift", "shift"} <= set(p.HIDER_SCRIPTS)


def test_hider_still_gives_no_orders():
    for tick in (0, 10, 400, 2399):
        assert _orders("still", tick) == []


def test_hider_drift_moves_along_the_heading():
    for heading in (0.0, 90.0, 217.0):
        moves = [o for o in _orders("drift", 0, centre=(100.0, 50.0), heading=heading) if o[0] == "move"]
        assert moves, "drift must give a move order at tick 0"
        dx, dy = moves[0][1] - 100.0, moves[0][2] - 50.0
        h = math.radians(heading)
        assert dx * math.cos(h) + dy * math.sin(h) > 0 and abs(-dx * math.sin(h) + dy * math.cos(h)) < 1e-3 * math.hypot(dx, dy)
    assert not [o for o in _orders("drift", 400) if o[0] == "layer"], "drift never changes layer"


def test_hider_shift_changes_layer_every_400_ticks_inside_0_to_4():
    layer, changes, ups, downs = 2, [], 0, 0
    for tick in range(0, 4001, DECIDE):
        for o in _orders("shift", tick, layer=layer):
            if o[0] == "layer":
                assert abs(o[1] - layer) == 1 and 0 <= o[1] <= 4, "tick %d: bad shift %d -> %d" % (tick, layer, o[1])
                changes.append(tick)
                ups, downs = ups + (o[1] > layer), downs + (o[1] < layer)
                layer = o[1]
    assert all(t % 400 == 0 for t in changes), changes
    assert all(t in changes for t in range(400, 4001, 400)), "a shift is due at every multiple of 400: %r" % changes
    assert ups >= 1 and downs >= 1, "layer goes up then down (ups %d, downs %d)" % (ups, downs)


def test_hider_shift_stays_in_range_from_either_edge():
    for start in (0, 4):
        layer = start
        for tick in range(0, 4001, DECIDE):
            for o in _orders("shift", tick, layer=layer):
                if o[0] == "layer":
                    assert 0 <= o[1] <= 4 and abs(o[1] - layer) == 1
                    layer = o[1]


def test_hider_shift_also_drifts():
    assert [o for o in _orders("shift", 0, heading=45.0) if o[0] == "move"], "shift is drift plus layer changes"
