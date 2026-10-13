"""ALG-43 Latent loyalty (docs/bible/algorithms.md; E-07 S-050, R-050-*).

Rule: after the split in ALG-41, if the region has a previous owner different from its current
owner, tick - held_since <= LATENT_LOYALTY_TICKS = 20, one draw < LATENT_LOYALTY_REVERT_CHANCE =
0.5, and the previous owner still exists: the region reverts to the previous owner with
held-since = tick, previous owner cleared, and the same tension cap (40.0) and floors as ALG-41
(military x0.40, economy x0.60 floored 20.0, population floored 25.0). Otherwise a breakaway forms.

A tension revolt ("Revolt Entrenched", custom creates_faction template) is queued on region 0 at
tick 101 (world tick set to 100). Draw order: event roll, rate, check, loyalty draw (only when the
first three conditions hold), then the new faction's confidence draw. Positive control: a wrong
expectation (revert at age 21, revert at draw 0.5) fails against the same worlds.
"""
import pytest

from conftest import (
    OMArchetype,
    OMField,
    OMFeature,
    OMTier,
    OmEventTemplate,
    OmReversionRecord,
    force_draws,
    isolate_events,
    queue_external,
    set_faction,
    set_owner,
    set_region,
    template_id,
)

TICK = 101
START = (40.0, 50.0, 70.0, 60.0)
SPLIT = (40.0 - 40.0 * 0.60, max(20.0, 50.0 - 50.0 * 0.40), min(70.0, 40.0), max(60.0, 25.0))


def _world(handle, factory, *, prev, held_since, prev_exists=True):
    w = factory(n_regions=2)
    isolate_events(handle, w)
    handle.om_world_set_feature(w, OMFeature.LIFECYCLE, 1)
    t = OmEventTemplate()
    t.name = b"Revolt Entrenched"
    t.creates_faction = 1
    arr = (OmEventTemplate * 1)(t)
    assert handle.om_events_load(w, arr, 1) == 0
    set_faction(handle, w, 0, OMArchetype.DEFAULT, budget=5.0, tech=10.0, confidence=5.0)
    if prev_exists:
        set_faction(handle, w, 1, OMArchetype.CONQUEROR, budget=5.0, tech=10.0, confidence=5.0)
    set_region(handle, w, 0, tier=OMTier.HOME, military=START[0], economy=START[1], tension=START[2],
               population=START[3], faction_id=0)
    set_owner(handle, w, 0, 0, held_since=held_since)
    set_region(handle, w, 1, tier=OMTier.HOME, military=50.0, economy=50.0, tension=0.0, population=50.0,
               faction_id=1 if prev_exists else 0)
    set_owner(handle, w, 1, 1 if prev_exists else 0, held_since=-1)
    handle.om_region_set_previous_owner(w, 0, prev)
    handle.om_world_set_tick(w, TICK - 1)
    assert queue_external(handle, w, 0, template_id(handle, w, "Revolt Entrenched"), due_tick=TICK, probability=1.0) > 0
    return w


def _fields(handle, w):
    return tuple(handle.om_region_field(w, 0, f) for f in
                 (OMField.MILITARY, OMField.ECONOMY, OMField.TENSION, OMField.POPULATION))


def _run(handle, w, draws):
    force_draws(handle, w, draws)
    handle.om_world_step(w)


REVOLT = [0.0, 0.0, 0.5]    # event roll, rate (0.50), check (0.5 <= 0.5)


@pytest.mark.parametrize("age", [0, 10, 20])
def test_ALG_43_within_20_ticks_and_draw_below_half_reverts_to_the_previous_owner(lib, world_factory, age):
    w = _world(lib, world_factory, prev=1, held_since=TICK - age)
    _run(lib, w, REVOLT + [0.4999])
    assert lib.om_rng_forced_remaining(w) == 0
    assert lib.om_region_owner(w, 0) == 1
    assert lib.om_region_held_since(w, 0) == TICK
    assert lib.om_region_previous_owner(w, 0) == -1
    assert lib.om_faction_count(w) == 2, "no breakaway faction was created"
    for got, exp in zip(_fields(lib, w), SPLIT):
        assert got == pytest.approx(exp, abs=1e-9)
    buf = (OmReversionRecord * 4)()
    assert lib.om_tick_reversions(w, buf, 4) == 1
    assert buf[0].original_faction == 0 and buf[0].restored_faction == 1


@pytest.mark.parametrize("scenario,draws", [
    ("age 21", REVOLT + [0.5]),                  # no loyalty draw: the last 0.5 is the confidence draw
    ("draw exactly 0.5", REVOLT + [0.5, 0.5]),   # loyalty draw 0.5 is not < 0.5; then confidence
    ("draw above 0.5", REVOLT + [0.9, 0.5]),
])
def test_ALG_43_outside_the_window_or_draw_at_least_half_a_breakaway_forms(lib, world_factory, scenario, draws):
    age = 21 if scenario == "age 21" else 20
    w = _world(lib, world_factory, prev=1, held_since=TICK - age)
    _run(lib, w, draws)
    assert lib.om_rng_forced_remaining(w) == 0, scenario
    new = lib.om_region_owner(w, 0)
    assert new not in (-1, 0, 1)
    assert lib.om_faction_archetype(w, new) == OMArchetype.BREAKAWAY
    assert lib.om_region_previous_owner(w, 0) == 0
    for got, exp in zip(_fields(lib, w), SPLIT):
        assert got == pytest.approx(exp, abs=1e-9)


def test_ALG_43_a_previous_owner_that_no_longer_exists_cannot_take_the_region_back(lib, world_factory):
    """Draw is spent (conditions 1-3 hold) but the previous owner (faction 7) does not exist: a breakaway forms."""
    w = _world(lib, world_factory, prev=7, held_since=TICK - 5, prev_exists=False)
    _run(lib, w, REVOLT + [0.1, 0.5])
    assert lib.om_rng_forced_remaining(w) == 0
    new = lib.om_region_owner(w, 0)
    assert new not in (-1, 0, 7)
    assert lib.om_faction_is_active(w, new) == 1
    assert lib.om_faction_archetype(w, new) == OMArchetype.BREAKAWAY
    assert lib.om_region_previous_owner(w, 0) == 0


@pytest.mark.parametrize("prev", [0, -1])
def test_ALG_43_no_previous_owner_or_the_same_owner_makes_no_draw(lib, world_factory, prev):
    w = _world(lib, world_factory, prev=prev, held_since=TICK - 5)
    _run(lib, w, REVOLT + [0.5])                  # the 0.5 is the confidence draw: no loyalty draw is taken
    assert lib.om_rng_forced_remaining(w) == 0
    new = lib.om_region_owner(w, 0)
    assert new not in (-1, 0, 1)


def test_control_ALG_43_wrong_expectations_fail(lib, world_factory):
    w = _world(lib, world_factory, prev=1, held_since=TICK - 21)
    _run(lib, w, REVOLT + [0.5])
    with pytest.raises(AssertionError):
        assert lib.om_region_owner(w, 0) == 1        # 'revert at age 21' is the wrong expectation
    w2 = _world(lib, world_factory, prev=1, held_since=TICK - 20)
    _run(lib, w2, REVOLT + [0.5, 0.5])
    with pytest.raises(AssertionError):
        assert lib.om_region_owner(w2, 0) == 1       # 'revert at draw 0.5' is the wrong expectation
    w3 = _world(lib, world_factory, prev=1, held_since=TICK - 20)
    _run(lib, w3, REVOLT + [0.4999])
    assert lib.om_region_owner(w3, 0) == 1           # and the right draw does revert, so the detector discriminates
