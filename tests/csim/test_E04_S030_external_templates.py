"""S-030 -- module-owned named templates outside the launch library (F2h).

ALG-27b (docs/bible/algorithms.md) needs a "Knowledge Lost" fired-event record,
but the launch library is pinned at exactly 26 templates (R-030-01,
test_E04_S030_the_launch_event_library.py::test_R_030_01). om_event_register_external
lets a module (E-06's Knowledge Lost, R-045-07) register its own named template
outside that table, at an id the rest of the event machinery treats like any
other trigger-less template.

R-030-02 (a template with no trigger never starts a chain -- it fires only as
a spawn) applies to a registered template exactly as it does to a launch
template: registration gives it no trigger, so this is the same rule, not a
new one.

Undefined until B1-4 lands the symbol in csrc/events.c. This is meant to fail
red right now: no pytest.skip, no xfail -- an AttributeError (or, once the
symbol exists but misbehaves, an AssertionError) is the expected failure
mode, never a quiet pass.
"""
from conftest import (
    OMSource,
    OMTier,
    get_template,
    isolate_events,
    load_launch_events,
    queue_external,
    read_events,
    register_external_template,
    set_region,
    template_id,
    template_name,
    zero_all_noise,
)


def test_R_030_02_registering_assigns_an_id_past_the_launch_library(lib, world_factory):
    """Given the 26-template launch library loaded, When a module registers a
    named template, Then the returned id is >= the launch library size and
    om_event_template_count -- the accessor R-030-01's contract test reads --
    still reports exactly 26: the registration is not counted."""
    w = world_factory(n_regions=1)
    isolate_events(lib, w)
    load_launch_events(lib, w)

    launch_count = lib.om_event_template_count(w)
    assert launch_count == 26

    new_id = register_external_template(lib, w, "Knowledge Lost", significance_tier=3)

    assert new_id >= 26
    assert new_id >= launch_count
    assert lib.om_event_template_count(w) == 26


def test_R_030_02_registering_the_same_name_twice_returns_the_same_id(lib, world_factory):
    """Given a template already registered by name, When registered again with
    the same name, Then the same id comes back (idempotent by name) and the
    launch-library count is still unaffected."""
    w = world_factory(n_regions=1)
    isolate_events(lib, w)
    load_launch_events(lib, w)

    first_id = register_external_template(lib, w, "Knowledge Lost", significance_tier=3)
    second_id = register_external_template(lib, w, "Knowledge Lost", significance_tier=3)

    assert second_id == first_id
    assert lib.om_event_template_count(w) == 26


def test_R_030_02_registered_template_has_no_trigger_and_the_name_resolves(lib, world_factory):
    """Given a freshly registered template, Then get_template reports it with
    no trigger (R-030-02's shape: it can only ever fire as a spawn) and
    om_event_template_name resolves the id back to the registered name."""
    w = world_factory(n_regions=1)
    isolate_events(lib, w)
    load_launch_events(lib, w)

    new_id = register_external_template(lib, w, "Knowledge Lost", significance_tier=3)

    t = get_template(lib, w, new_id)
    assert t.id == new_id
    assert t.trigger_kind == 0  # OM_TRIG_NONE: fires only as a spawn, R-030-02
    assert t.n_spawns == 0

    assert template_name(lib, w, new_id) == "Knowledge Lost"


def test_R_045_07_a_queued_registered_template_fires_only_as_a_spawn(lib, world_factory):
    """Given a registered template queued externally (R-045-07's own firing
    path for Knowledge Lost), When the queue resolves, Then it fires exactly
    once with the registered template id, sourced as a spawn/external firing
    never a trigger -- the same R-030-02 shape the launch-library
    no-trigger templates already prove in test_R_030_02_b_it_fires_only_as_a_spawn."""
    w = world_factory(n_regions=1)
    isolate_events(lib, w)
    load_launch_events(lib, w)
    zero_all_noise(lib, w)

    new_id = register_external_template(lib, w, "Knowledge Lost", significance_tier=3)

    set_region(lib, w, 0, tier=OMTier.HOME, military=40.0, economy=45.0, tension=0.0, population=45.0)

    # Grace period, same shape as the launch-library spawn test (R-026-05).
    for _ in range(3):
        lib.om_world_step(w)
    lib.om_world_step(w)  # tick 4: triggers evaluated, registered template has none

    assigned_tag = queue_external(lib, w, region_idx=0, tid=new_id, due_tick=5, probability=1.0)
    assert assigned_tag >= 0

    lib.om_world_step(w)  # tick 5: queue resolution
    events_t5 = read_events(lib, w)

    firings = [e for e in events_t5 if e.template_id == new_id]
    assert len(firings) == 1
    fired = firings[0]
    assert fired.source in (OMSource.SPAWN, OMSource.EXTERNAL)
    assert fired.chain_tag == assigned_tag

    assert template_name(lib, w, fired.template_id) == "Knowledge Lost"


def test_R_030_02_registration_does_not_collide_with_launch_library_names(lib, world_factory):
    """Given the launch library's own template ids, When a new name is
    registered, Then it never aliases an existing launch-library id --
    template_id (om_event_template_by_name) still resolves every launch name
    to its original id, unaffected by the registration."""
    w = world_factory(n_regions=1)
    isolate_events(lib, w)
    load_launch_events(lib, w)

    border_incursion_id = template_id(lib, w, "Border Incursion")

    new_id = register_external_template(lib, w, "Knowledge Lost", significance_tier=3)

    assert new_id != border_incursion_id
    assert template_id(lib, w, "Border Incursion") == border_incursion_id
