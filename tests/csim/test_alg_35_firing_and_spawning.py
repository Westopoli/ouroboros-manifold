"""ALG-35 Firing and spawning (docs/bible/algorithms.md; E-04 S-027 R-027-01/06, S-028, R-019-04).

Rules under test:
  * effects apply per field as max(floor, min(100, field + delta)), floors economy 8.0,
    tension 12.0, military/population 0 ("each nonzero summed delta applies once", ALG-36:
    a field whose summed delta is zero is not touched);
  * each chain spawn draws one uniform u and queues due = tick + d,
    d = clamp(round(triangular(a, b, (a + b)/2)), a, b), carrying probability and the parent's
    chain tag, one draw per spawn in template order;
  * every chain start takes the next value of one global counter (fresh trigger or external);
    spawns inherit the parent's tag.

Custom templates are loaded with om_events_load so the fixture is exact. Expected values are
computed here from the rule (the triangular inverse CDF, the clamp), never read from the C
output. Positive control: the debug build with OM_BUG_CHAIN_COUNTER_UNSAVED makes the counter
check fail, and wrong expectations fail the rest.
"""
import math

import pytest

from conftest import (
    OMArchetype,
    OMEdge,
    OMStance,
    OMBugE04,
    OMCond,
    OMField,
    OMSource,
    OMTier,
    OMTrigger,
    OmEventTemplate,
    force_draws,
    isolate_agents,
    isolate_events,
    load_launch_events,
    read_attacks,
    set_edge,
    set_faction,
    set_stance,
    set_tech_multipliers,
    isolate_events,
    queue_external,
    read_event_queue,
    read_events,
    set_noise,
    set_owner,
    set_region,
)

import ctypes

ECONOMY_FLOOR = 8.0
TENSION_FLOOR = 12.0
FLOORS = {OMField.MILITARY: 0.0, OMField.ECONOMY: ECONOMY_FLOOR,
          OMField.TENSION: TENSION_FLOOR, OMField.POPULATION: 0.0}


def apply_rule(field, start, delta):
    return max(FLOORS[field], min(100.0, start + delta))


def triangular_round(a, b, u):
    """round(triangular(a, b, mode (a+b)/2)) by the textbook inverse CDF, clamped to [a, b]."""
    c = (a + b) / 2.0
    if b == a:
        x = float(a)
    elif u <= 0.5:   # F(mode) = (c - a)/(b - a) = 0.5
        x = a + math.sqrt(u * (b - a) * (c - a))
    else:
        x = b - math.sqrt((1.0 - u) * (b - a) * (b - c))
    return x, int(max(a, min(b, math.floor(x + 0.5))))


def tmpl(name, effect=(0.0, 0.0, 0.0, 0.0), spawns=(), trigger=OMTrigger.NONE, field=0, threshold=0.0):
    t = OmEventTemplate()
    t.name = name.encode()
    t.trigger_kind = trigger
    t.trigger_field = field
    t.threshold = threshold
    for i, v in enumerate(effect):
        t.effect[i] = v
    t.n_spawns = len(spawns)
    for j, (tid, dmin, dmax, prob) in enumerate(spawns):
        t.spawns[j].template_id = tid
        t.spawns[j].delay_min = dmin
        t.spawns[j].delay_max = dmax
        t.spawns[j].probability = prob
        t.spawns[j].cond_kind = OMCond.NONE
    return t


def load(handle, w, templates):
    arr = (OmEventTemplate * len(templates))(*templates)
    assert handle.om_events_load(w, arr, len(templates)) == 0


def region(handle, w, idx, m=50.0, e=50.0, t=50.0, p=50.0):
    set_region(handle, w, idx, tier=OMTier.HOME, military=m, economy=e, tension=t, population=p)
    set_owner(handle, w, idx, 0, held_since=-1)


FLOOR_CASES = [
    (OMField.MILITARY, 3.0, -5.0), (OMField.MILITARY, 97.0, 5.0), (OMField.MILITARY, 50.0, -5.0),
    (OMField.ECONOMY, 9.0, -5.0), (OMField.ECONOMY, 8.0, -3.0), (OMField.ECONOMY, 96.0, 10.0),
    (OMField.ECONOMY, 50.0, -5.0),
    (OMField.TENSION, 13.0, -5.0), (OMField.TENSION, 50.0, -5.0), (OMField.TENSION, 98.0, 5.0),
    (OMField.TENSION, 5.0, 1.0),
    (OMField.POPULATION, 2.0, -5.0), (OMField.POPULATION, 99.0, 5.0),
]


@pytest.mark.parametrize("field,start,delta", FLOOR_CASES)
def test_ALG_35_effects_apply_as_max_floor_min_100(lib, world_factory, field, start, delta):
    w = world_factory(n_regions=1)
    isolate_events(lib, w)
    effect = [0.0] * 4
    effect[field] = delta
    load(lib, w, [tmpl("FX", effect=effect)])
    region(lib, w, 0)
    base = {OMField.MILITARY: 50.0, OMField.ECONOMY: 50.0, OMField.TENSION: 50.0, OMField.POPULATION: 50.0}
    base[field] = start
    region(lib, w, 0, base[OMField.MILITARY], base[OMField.ECONOMY], base[OMField.TENSION], base[OMField.POPULATION])
    assert queue_external(lib, w, 0, 0, due_tick=2, probability=1.0) > 0
    lib.om_world_step(w)           # tick 1: not due
    force_draws(lib, w, [0.0])
    lib.om_world_step(w)           # tick 2: fires
    assert len(read_events(lib, w)) == 1
    assert lib.om_region_field(w, 0, field) == pytest.approx(apply_rule(field, start, delta), abs=1e-9)


def test_ALG_35_a_field_with_zero_delta_is_not_touched(lib, world_factory):
    """ALG-36 'each nonzero summed delta applies once': a military-only event leaves a tension below its 12.0 floor and an economy below its 8.0 floor as they were (conquest and drift may leave them there; R-019-02, R-019-04)."""
    w = world_factory(n_regions=1)
    isolate_events(lib, w)
    load(lib, w, [tmpl("MIL", effect=(5.0, 0.0, 0.0, 0.0))])
    region(lib, w, 0, m=50.0, e=3.0, t=5.0, p=50.0)
    queue_external(lib, w, 0, 0, due_tick=2, probability=1.0)
    lib.om_world_step(w)
    force_draws(lib, w, [0.0])
    lib.om_world_step(w)
    assert len(read_events(lib, w)) == 1
    assert lib.om_region_field(w, 0, OMField.MILITARY) == pytest.approx(55.0, abs=1e-9)
    assert lib.om_region_field(w, 0, OMField.TENSION) == pytest.approx(5.0, abs=1e-9)
    assert lib.om_region_field(w, 0, OMField.ECONOMY) == pytest.approx(3.0, abs=1e-9)


DELAY_CASES = [(3, 6), (2, 5), (1, 2), (4, 4), (1, 10), (5, 9)]
DRAWS = [0.0, 0.03, 0.18, 0.37, 0.51, 0.77, 0.99, 1.0]


def _delay_world(handle, factory, a, b, p, draws):
    w = factory(n_regions=1)
    isolate_events(handle, w)
    load(handle, w, [tmpl("PARENT", spawns=[(1, a, b, p)]), tmpl("CHILD")])
    region(handle, w, 0)
    queue_external(handle, w, 0, 0, due_tick=1, probability=1.0)
    force_draws(handle, w, [0.0] + list(draws))   # probability roll, then the spawn delay draw(s)
    handle.om_world_step(w)
    return w


@pytest.mark.parametrize("a,b", DELAY_CASES)
@pytest.mark.parametrize("u", DRAWS)
def test_ALG_35_spawn_delay_is_clamped_rounded_triangular_from_one_draw(lib, world_factory, a, b, u):
    x, d = triangular_round(a, b, u)
    if abs((x - math.floor(x)) - 0.5) < 1e-6:
        pytest.skip("exact .5 midpoint: the rounding convention is not what this test is about")
    w = _delay_world(lib, world_factory, a, b, 0.6, [u])
    assert lib.om_rng_forced_remaining(w) == 0, "exactly one draw per spawn"
    q = [e for e in read_event_queue(lib, w) if e.template_id == 1]
    assert len(q) == 1
    assert q[0].due_tick == 1 + d
    assert q[0].probability == pytest.approx(0.6, abs=1e-12)
    parent = read_events(lib, w)[0]
    assert q[0].chain_tag == parent.chain_tag


def test_ALG_35_one_draw_per_spawn_in_template_order(lib, world_factory):
    w = world_factory(n_regions=1)
    isolate_events(lib, w)
    load(lib, w, [tmpl("PARENT", spawns=[(1, 3, 6, 1.0), (2, 2, 5, 0.5)]), tmpl("CHILD_A"), tmpl("CHILD_B")])
    region(lib, w, 0)
    queue_external(lib, w, 0, 0, due_tick=1, probability=1.0)
    u1, u2 = 0.0, 1.0
    force_draws(lib, w, [0.0, u1, u2])
    lib.om_world_step(w)
    assert lib.om_rng_forced_remaining(w) == 0
    q = {e.template_id: e for e in read_event_queue(lib, w)}
    assert q[1].due_tick == 1 + triangular_round(3, 6, u1)[1]
    assert q[2].due_tick == 1 + triangular_round(2, 5, u2)[1]
    tag = read_events(lib, w)[0].chain_tag
    assert q[1].chain_tag == tag and q[2].chain_tag == tag


def _counter_scenario(handle, factory, inject=None):
    """Two external chain starts, then two fresh threshold crossings on tick 4; return the observed tags."""
    w = factory(n_regions=2)
    isolate_events(handle, w)
    load(handle, w, [tmpl("EXT"), tmpl("CROSS", trigger=OMTrigger.ABOVE, field=OMField.TENSION, threshold=50.0)])
    for r in range(2):
        for tid in range(2):
            set_noise(handle, w, r, tid, 0.0)
        region(handle, w, r, t=40.0)
    ext_tags = [queue_external(handle, w, 0, 0, due_tick=20), queue_external(handle, w, 1, 0, due_tick=20)]
    if inject is not None:
        handle.om_debug_inject(w, inject)
    for _ in range(3):
        handle.om_world_step(w)
    for r in range(2):
        region(handle, w, r, t=60.0)
    handle.om_world_step(w)
    fresh = [e for e in read_events(handle, w) if e.source == OMSource.TRIGGER]
    return ext_tags, [e.chain_tag for e in fresh], handle.om_chain_counter(w)


def _assert_counter(ext_tags, fresh_tags, counter):
    # one global counter: externals take 1, 2; the two fresh starts take the next two values, in region order
    assert ext_tags == [1, 2]
    assert fresh_tags == [3, 4]
    assert counter == 4


def test_ALG_35_every_chain_start_takes_the_next_value_of_one_global_counter(lib, world_factory):
    _assert_counter(*_counter_scenario(lib, world_factory))


def test_control_ALG_35_counter_not_advanced_is_detected(dbg, dbg_world_factory):
    """Positive control: OM_BUG_CHAIN_COUNTER_UNSAVED rolls the counter back after each fresh start, so the counter assertion must fail."""
    got = _counter_scenario(dbg, dbg_world_factory, inject=OMBugE04.CHAIN_COUNTER_UNSAVED)
    with pytest.raises(AssertionError):
        _assert_counter(*got)


def test_control_ALG_35_wrong_expectations_fail(lib, world_factory):
    """Positive control: a tension floor of 8.0 (the economy floor) or a draw-ignoring delay is rejected by the same helpers."""
    with pytest.raises(AssertionError):
        assert apply_rule(OMField.TENSION, 13.0, -5.0) == 8.0
    _, d_lo = triangular_round(1, 10, 0.0)
    _, d_hi = triangular_round(1, 10, 1.0)
    assert d_lo != d_hi
    w = _delay_world(lib, world_factory, 1, 10, 1.0, [1.0])
    q = [e for e in read_event_queue(lib, w) if e.template_id == 1][0]
    assert q.due_tick == 1 + d_hi
    with pytest.raises(AssertionError):
        assert q.due_tick == 1 + d_lo


# ---- chain starts outside the event pipeline: admin revolt roll (ALG-29) and conquest (ALG-22) ----

def test_ALG_35_an_admin_revolt_chain_start_takes_the_next_counter_value(lib, world_factory):
    """ALG-35: 'every chain start, whether a fresh trigger, a conquest spawn, or an admin-revolt spawn, takes the next value of one global counter'. First chain start of the world: tag 1, counter 1."""
    w = world_factory(n_regions=1)
    isolate_agents(lib, w, admin=True)
    load_launch_events(lib, w)
    set_faction(lib, w, 0, OMArchetype.DEFAULT, budget=0.0, tech=10.0, confidence=5.0)
    region(lib, w, 0)
    lib.om_region_set_owner(w, 0, 0, -1)
    force_draws(lib, w, [0.0, 0.0])          # roll 0.0 < chance 0.001, then the chain-length draw
    lib.om_world_step(w)
    q = read_event_queue(lib, w)
    assert len(q) == 1, "fixture check: the admin revolt roll queued one chain start"
    assert q[0].chain_tag == 1
    assert lib.om_chain_counter(w) == 1


def _conquest(handle, factory, u_delay):
    w = factory(n_regions=2)
    isolate_agents(handle, w)
    set_faction(handle, w, 0, OMArchetype.CONQUEROR, budget=100.0, confidence=2.0)
    set_faction(handle, w, 1, OMArchetype.FORTIFIER, budget=0.0)
    set_stance(handle, w, 0, 1, OMStance.HOSTILE)
    for f in (0, 1):
        set_tech_multipliers(handle, w, f, 1.0, 1.0, 1.0)
    set_region(handle, w, 0, tier=OMTier.HOME, military=50.0, economy=8.0, tension=0.0, population=50.0, faction_id=0)
    set_owner(handle, w, 0, 0, held_since=-1)
    set_region(handle, w, 1, tier=OMTier.HOME, military=10.0, economy=50.0, tension=10.0, population=50.0, faction_id=1)
    set_owner(handle, w, 1, 1, held_since=-1)
    set_edge(handle, w, 0, 1, OMEdge.BOTH)
    load_launch_events(handle, w)
    # mode draw (surprise), stochastic 1.0 -> net 24 -> conquest, unrest probability 0.30 <= 0.60, delay draw
    force_draws(handle, w, [0.95, 1.0, 0.30, u_delay])
    handle.om_world_step(w)
    assert read_attacks(handle, w)[0].conquest == 1, "fixture check: the attack conquered the region"
    q = read_event_queue(handle, w)
    assert len(q) == 1
    return w, q[0]


def test_ALG_35_a_conquest_chain_start_takes_the_next_counter_value(lib, world_factory):
    w, q = _conquest(lib, world_factory, 0.5)
    assert q.chain_tag == 1
    assert lib.om_chain_counter(w) == 1


@pytest.mark.parametrize("u", [0.0, 0.1, 0.25, 0.4, 0.6, 0.75, 0.9, 1.0])
def test_ALG_22_35_conquest_unrest_delay_is_round_triangular_4_8_mode_6(lib, world_factory, u):
    """ALG-22: 'a CONQUEST_UNREST chain is queued after a delay of round(triangular(4, 8, mode 6)) ticks (second draw)'; the same triangular as ALG-35 (inverse CDF, both halves)."""
    x, d = triangular_round(4, 8, u)
    if abs((x - math.floor(x)) - 0.5) < 1e-6:
        pytest.skip("exact .5 midpoint")
    _, q = _conquest(lib, world_factory, u)
    assert q.due_tick == 1 + d
