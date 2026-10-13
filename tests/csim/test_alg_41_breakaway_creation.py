"""ALG-41 Breakaway creation (docs/bible/algorithms.md; E-07 S-049, R-049-*).

Rule, on a faction-creating event in an owned region:
  * tension revolt: rate = U(0.50, 0.95) (one draw), then a second draw must be <= rate, and the
    region's population must be >= REVOLT_BREAKAWAY_POP_FLOOR = 25.0; else no faction forms;
  * admin revolt: success rate 1.0 (no draws), pruned if the region's owner differs from the
    chain's source faction or the region changed hands after the chain started;
  * then military -= military * 0.60, economy -= economy * 0.40; new faction breakaway_<tick>_<region>,
    region previous owner = old owner, tension = min(tension, 40.0), population = max(population, 25.0),
    economy = max(economy, 20.0); archetype breakaway for tension revolts, one draw from
    [conqueror, fortifier, warlord, opportunist, schism] for admin revolts; budget 0; hostile both ways
    with every faction; tech = the parent's current tech.

Custom templates named "Revolt Entrenched" and "Admin Breakaway" (creates_faction) are loaded so the
fixture is exact; expected values are computed here. Positive control: a wrong expectation (the
unfloored economy, the uncapped tension) fails against the same world.
"""
import ctypes

import pytest

from conftest import (
    OMArchetype,
    OMField,
    OMFeature,
    OMStance,
    OMTier,
    OmEventTemplate,
    OmRevoltRecord,
    force_draws,
    isolate_events,
    queue_external,
    read_pruned,
    set_faction,
    set_owner,
    set_region,
    template_id,
    load_launch_events,
)

MIL_STEAL = 0.60
ECO_STEAL = 0.40
TENSION_CAP = 40.0
POP_FLOOR = 25.0
ECO_FLOOR = 20.0
RATE_LO, RATE_HI = 0.50, 0.95
ADMIN_ARCHETYPES = [OMArchetype.CONQUEROR, OMArchetype.FORTIFIER, OMArchetype.WARLORD,
                    OMArchetype.OPPORTUNIST, OMArchetype.SCHISM]


def expected_split(m, e, t, p):
    return (m - m * MIL_STEAL, max(ECO_FLOOR, e - e * ECO_STEAL), min(t, TENSION_CAP), max(p, POP_FLOOR))


def revolts(handle, w):
    buf = (OmRevoltRecord * 16)()
    n = handle.om_tick_revolts(w, buf, 16)
    return [buf[i] for i in range(n)]


def _templates():
    out = []
    for name in ("Revolt Entrenched", "Admin Breakaway"):
        t = OmEventTemplate()
        t.name = name.encode()
        t.creates_faction = 1
        out.append(t)
    return out


def _world(handle, factory, *, m=40.0, e=50.0, t=70.0, p=60.0, parent_tech=37.0, admin=False, source=0):
    w = factory(n_regions=2)
    isolate_events(handle, w)
    handle.om_world_set_feature(w, OMFeature.LIFECYCLE, 1)
    tpl = _templates()
    arr = (OmEventTemplate * 2)(*tpl)
    assert handle.om_events_load(w, arr, 2) == 0
    set_faction(handle, w, 0, OMArchetype.DEFAULT, budget=5.0, tech=parent_tech, confidence=5.0)
    set_faction(handle, w, 1, OMArchetype.CONQUEROR, budget=5.0, tech=10.0, confidence=5.0)
    set_region(handle, w, 0, tier=OMTier.HOME, military=m, economy=e, tension=t, population=p, faction_id=0)
    set_owner(handle, w, 0, 0, held_since=-1)
    set_region(handle, w, 1, tier=OMTier.HOME, military=50.0, economy=50.0, tension=0.0, population=50.0, faction_id=1)
    set_owner(handle, w, 1, 1, held_since=-1)
    tid = template_id(handle, w, "Admin Breakaway" if admin else "Revolt Entrenched")
    assert queue_external(handle, w, 0, tid, due_tick=1, probability=1.0, source_faction=source) > 0
    return w


def _fields(handle, w, idx=0):
    return tuple(handle.om_region_field(w, idx, f) for f in
                 (OMField.MILITARY, OMField.ECONOMY, OMField.TENSION, OMField.POPULATION))


def _assert_split(handle, w, start):
    got = _fields(handle, w)
    exp = expected_split(*start)
    for g, x in zip(got, exp):
        assert g == pytest.approx(x, abs=1e-9)


def test_ALG_41_tension_revolt_success_split_and_new_faction(lib, world_factory):
    start = (40.0, 50.0, 70.0, 60.0)
    w = _world(lib, world_factory, m=start[0], e=start[1], t=start[2], p=start[3], parent_tech=37.0)
    u_rate = 0.5
    rate = RATE_LO + (RATE_HI - RATE_LO) * u_rate
    force_draws(lib, w, [0.0, u_rate, rate, 0.5])        # event roll, rate draw, check == rate (<= passes), new faction's confidence
    lib.om_world_step(w)
    assert lib.om_rng_forced_remaining(w) == 0
    new = lib.om_region_owner(w, 0)
    assert new not in (-1, 0, 1)
    assert lib.om_faction_archetype(w, new) == OMArchetype.BREAKAWAY
    assert lib.om_faction_budget(w, new) == 0.0
    assert lib.om_faction_tech(w, new) == pytest.approx(37.0, abs=1e-9)
    assert lib.om_region_previous_owner(w, 0) == 0
    assert lib.om_region_held_since(w, 0) == 1
    _assert_split(lib, w, start)
    for f in (0, 1):
        assert lib.om_faction_stance(w, new, f) == OMStance.HOSTILE
        assert lib.om_faction_stance(w, f, new) == OMStance.HOSTILE
    rec = revolts(lib, w)
    assert len(rec) == 1 and rec[0].faction_created == 1 and rec[0].new_faction_id == new
    assert rec[0].success_rate == pytest.approx(rate, abs=1e-9)
    assert rec[0].military_stolen == pytest.approx(start[0] * MIL_STEAL, abs=1e-9)
    assert rec[0].economy_stolen == pytest.approx(start[1] * ECO_STEAL, abs=1e-9)


def test_ALG_41_economy_floor_and_population_floor_on_the_new_region(lib, world_factory):
    """economy 30 -> 18 is floored to 20.0; population 25 stays; tension 30 stays under the 40 cap."""
    start = (40.0, 30.0, 30.0, 25.0)
    w = _world(lib, world_factory, m=start[0], e=start[1], t=start[2], p=start[3])
    force_draws(lib, w, [0.0, 0.0, 0.5, 0.5])             # rate 0.50, check 0.5 <= 0.5
    lib.om_world_step(w)
    assert lib.om_region_owner(w, 0) not in (-1, 0, 1)
    _assert_split(lib, w, start)
    assert lib.om_region_field(w, 0, OMField.ECONOMY) == pytest.approx(20.0, abs=1e-9)


@pytest.mark.parametrize("check_over,pop,expect_created", [
    (False, 60.0, True),
    (True, 60.0, False),        # second draw just above the rate
    (False, 24.9, False),       # population below the 25.0 floor
])
def test_ALG_41_tension_revolt_needs_check_le_rate_and_population_ge_25(lib, world_factory, check_over, pop, expect_created):
    w = _world(lib, world_factory, p=pop)
    rate = RATE_LO + (RATE_HI - RATE_LO) * 0.0
    check = rate + (1e-6 if check_over else 0.0)
    force_draws(lib, w, [0.0, 0.0, check, 0.5])
    lib.om_world_step(w)
    created = lib.om_region_owner(w, 0) != 0
    assert created == expect_created
    if not expect_created:
        assert _fields(lib, w) == (40.0, 50.0, 70.0, pop)


@pytest.mark.parametrize("pick,arch_idx", [(0.0, 0), (0.19, 0), (0.2, 1), (0.45, 2), (0.6, 3), (0.8, 4), (0.999, 4)])
def test_ALG_41_admin_revolt_rate_is_1_and_archetype_is_one_draw_over_the_five(lib, world_factory, pick, arch_idx):
    start = (40.0, 50.0, 70.0, 10.0)   # population 10: the population floor does not gate an admin revolt
    w = _world(lib, world_factory, m=start[0], e=start[1], t=start[2], p=start[3], admin=True, source=0)
    force_draws(lib, w, [0.0, pick, 0.5])                 # event roll, archetype draw, confidence (no rate / check draws)
    lib.om_world_step(w)
    assert lib.om_rng_forced_remaining(w) == 0
    new = lib.om_region_owner(w, 0)
    assert new not in (-1, 0, 1)
    assert lib.om_faction_archetype(w, new) == ADMIN_ARCHETYPES[arch_idx]
    _assert_split(lib, w, start)
    assert revolts(lib, w)[0].success_rate == 1.0


def test_ALG_41_admin_revolt_is_pruned_when_the_owner_is_not_the_chain_source(lib, world_factory):
    w = _world(lib, world_factory, admin=True, source=1)   # chain started by faction 1; region 0 is faction 0's
    force_draws(lib, w, [0.0, 0.5, 0.5])
    lib.om_world_step(w)
    assert lib.om_region_owner(w, 0) == 0
    assert lib.om_faction_count(w) == 2
    assert len(read_pruned(lib, w)) == 1


def _admin_chain(handle, factory, takeover):
    """Launch library, short admin chain (L = 3: Separatist, Military Defection, Breakaway on ticks 1, 2, 3)
    started by faction 0; with `takeover`, faction 1 takes region 0 between tick 2 and tick 3."""
    w = factory(n_regions=2)
    isolate_events(handle, w)
    handle.om_world_set_feature(w, OMFeature.LIFECYCLE, 1)
    load_launch_events(handle, w)
    set_faction(handle, w, 0, OMArchetype.DEFAULT, budget=5.0, tech=10.0, confidence=5.0)
    set_faction(handle, w, 1, OMArchetype.CONQUEROR, budget=5.0, tech=10.0, confidence=5.0)
    set_region(handle, w, 0, tier=OMTier.HOME, military=40.0, economy=50.0, tension=30.0, population=60.0, faction_id=0)
    set_owner(handle, w, 0, 0, held_since=-1)
    set_region(handle, w, 1, tier=OMTier.HOME, military=50.0, economy=50.0, tension=0.0, population=50.0, faction_id=1)
    set_owner(handle, w, 1, 1, held_since=-1)
    for r in range(2):
        for tid in range(handle.om_event_template_count(w)):
            handle.om_event_set_noise(w, r, tid, 0.0)
    assert queue_external(handle, w, 0, template_id(handle, w, "Admin Separatist"), due_tick=1,
                          probability=1.0, source_faction=0, chain_length=3) > 0
    for tick in (1, 2, 3):
        if tick == 3 and takeover:
            handle.om_region_set_owner(w, 0, 1, 2)
        handle.om_world_step(w)
    return w


def test_control_ALG_41_the_admin_chain_reaches_its_breakaway_on_tick_3(lib, world_factory):
    """Positive control for the test below: with no takeover the chain does split region 0 on tick 3."""
    w = _admin_chain(lib, world_factory, takeover=False)
    assert lib.om_region_owner(w, 0) not in (-1, 0, 1)
    assert lib.om_faction_count(w) == 3


def test_ALG_41_admin_chain_is_pruned_when_the_region_changes_hands_mid_chain(lib, world_factory):
    """Faction 1 takes the region on tick 2; the chain's Admin Breakaway on tick 3 must be pruned: 'pruned if the region's owner differs from the chain's source faction or the region changed hands after the chain started'."""
    w = _admin_chain(lib, world_factory, takeover=True)
    assert lib.om_region_owner(w, 0) == 1, "the chain's Breakaway must not split a region that changed hands"
    assert lib.om_faction_count(w) == 2


def test_control_ALG_41_wrong_expectations_fail(lib, world_factory):
    start = (40.0, 30.0, 70.0, 60.0)
    w2 = _world(lib, world_factory, m=start[0], e=start[1], t=start[2], p=60.0)
    force_draws(lib, w2, [0.0, 0.0, 0.5, 0.5])
    lib.om_world_step(w2)
    _assert_split(lib, w2, (start[0], start[1], start[2], 60.0))
    with pytest.raises(AssertionError):
        assert lib.om_region_field(w2, 0, OMField.ECONOMY) == pytest.approx(start[1] - start[1] * ECO_STEAL, abs=1e-9)  # unfloored 18.0
    with pytest.raises(AssertionError):
        assert lib.om_region_field(w2, 0, OMField.TENSION) == pytest.approx(70.0, abs=1e-9)                      # uncapped 70.0
