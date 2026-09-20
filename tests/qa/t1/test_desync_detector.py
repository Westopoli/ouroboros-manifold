"""T1 desync detector -- positive and negative controls for the S-139 claim
(docs/bible/epics/E-19-multiplayer.md R-139-03/04) and the factory Track
claim in docs/northstar/PLAN.md "Factory" section / A7 memo (section 4):
two `om_world` instances, same seed and command stream, must checksum
identically every `om_checksum_cadence()` ticks; a corrupted peer must be
caught within the cadence window and named by tick, region, and field.

Scenario: 7 regions, 3 factions (CONQUEROR/FORTIFIER/OPPORTUNIST) in a ring
with one unowned frontier, FACTIONS on (om_world_new's own DRIFT default
stays on too) -- the same fixture pattern tests/csim/test_E05_*.py already
use (set_faction/set_region/set_owner/set_edge), so this suite runs against
exactly the ABI the fenced E-02/E-05 tests already exercise, nothing new.

Honest finding from building this (see the module docstring in desync.py and
the report handed back with this card): om_intent_inject is currently a
no-op once FACTIONS runs -- csrc/agent.c's om_step_decisions() unconditionally
resets and recomputes every faction's decision from scratch each tick with no
check for an already-injected one, so an injected intent is overwritten
before resolution. This is a gap in the in-progress E-05 build (most of
tests/csim/test_E05_S039/S040/S041 already fail against today's csrc/ for the
same reason), not a defect in this detector. The clean-pair test below still
calls om_intent_inject once, as the card asked, and asserts it does not
perturb the checksum -- true today because it is a no-op, and still true once
card 204 lands, because both peers receive the identical call. The order
sensitivity the "out of order" control needs is exercised through
om_rng_force instead (see that test for why, and for the swap that does
divide the two peers), exactly as the card's own fallback instructions
anticipate.
"""
from conftest import (
    OMAction,
    OMArchetype,
    OMEdge,
    OMFeature,
    OMMode,
    OMStance,
    OMTier,
    OmTraceRow,
    isolate_agents,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)

from desync import run_pair

N_REGIONS = 7
SEED = 12345


def _build_scenario(lib, w):
    isolate_agents(lib, w, friction=False, admin=False)
    lib.om_world_set_feature(w, OMFeature.DRIFT, 1)  # trace rows are appended
    # from the drift step (csrc/sim.c); FACTIONS-only leaves the trace empty
    # and this detector needs trace rows to name a diverging field.
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=200.0, confidence=1.5)
    set_faction(lib, w, 1, OMArchetype.FORTIFIER, budget=200.0, confidence=1.2)
    set_faction(lib, w, 2, OMArchetype.OPPORTUNIST, budget=200.0, confidence=1.3)
    for a, b in ((0, 1), (0, 2), (1, 2)):
        set_stance(lib, w, a, b, OMStance.HOSTILE)
    for f in (0, 1, 2):
        set_tech_multipliers(lib, w, f, 1.0, 1.0, 1.0)

    # idx, tier, faction_id, military, economy, tension, population, econ_phase, tension_phase
    regions = [
        (0, OMTier.HOME, 0, 60.0, 55.0, 20.0, 55.0, 0.4, 1.7),
        (1, OMTier.FRONTIER, 0, 35.0, 40.0, 25.0, 40.0, 1.1, 2.3),
        (2, OMTier.HOME, 1, 45.0, 60.0, 15.0, 50.0, 2.0, 0.6),
        (3, OMTier.FRONTIER, 1, 30.0, 45.0, 30.0, 35.0, 3.4, 4.9),
        (4, OMTier.HOME, 2, 50.0, 50.0, 22.0, 45.0, 5.1, 1.3),
        (5, OMTier.FRONTIER, 2, 28.0, 38.0, 28.0, 30.0, 0.9, 3.2),
    ]
    for idx, tier, faction_id, mil, eco, ten, pop, ephase, tphase in regions:
        set_region(lib, w, idx, tier=tier, military=mil, economy=eco, tension=ten,
                   population=pop, econ_phase=ephase, tension_phase=tphase, faction_id=faction_id)
        set_owner(lib, w, idx, faction_id, held_since=-1)
    set_region(lib, w, 6, tier=OMTier.EMPTY, military=0.0, economy=20.0, tension=10.0,
               population=0.0, econ_phase=0.0, tension_phase=0.0, faction_id=-1)

    ring = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (1, 6)]
    for a, b in ring:
        set_edge(lib, w, a, b, OMEdge.BOTH)


# Three factions all decide ATTACK on tick 1 in this scenario (faction-ascending
# decision order), each consuming one forced draw for its telegraph/surprise
# roll -- this is the "scripted command stream" both peers receive identically.
COMMANDS = [
    {"tick": 1, "op": "rng_force", "draws": [0.42, 0.15, 0.77]},
    {"tick": 5, "op": "intent", "faction_id": 0, "action": OMAction.REINFORCE,
     "target_idx": 0, "source_idx": 0, "commit": 1.0, "mode": OMMode.SURPRISE},
    {"tick": 33, "op": "rng_force", "draws": [0.6, 0.25]},
]


def test_clean_pair_never_diverges(lib):
    report = run_pair(lib, seed=SEED, commands=COMMANDS, ticks=5000, n_regions=N_REGIONS,
                       trace_row_type=OmTraceRow, setup=_build_scenario)

    assert not report.diverged, (
        f"clean pair diverged at tick {report.first_divergent_tick}, "
        f"region {report.region}, field {report.field!r} "
        f"(checksums {report.checksum_a} vs {report.checksum_b})"
    )
    assert report.checkpoint_checksums, "expected at least one cadence checkpoint over 5,000 ticks"
    for tick, ca, cb in report.checkpoint_checksums:
        assert ca == cb, f"checkpoint mismatch at tick {tick}"

    # R-020-01-style memcmp: the two peers' full traces, not just their
    # checksums, must be byte-identical. Row count is not N_REGIONS * 5000:
    # the drift step (which appends trace rows) skips the empty-tier region
    # until it is colonized, exactly like the S-020/gate tests' own traces.
    assert report.trace_bytes_equal is True
    assert report.n_trace_rows_a == report.n_trace_rows_b > 0


def test_bit_flip_trips_within_cadence(lib):
    cadence = lib.om_checksum_cadence()
    corrupt_b = [(100, {
        "region": 3, "field": "military", "bit": 0,
        "econ_phase": 3.4, "tension_phase": 4.9,
    })]

    report = run_pair(lib, seed=SEED, commands=COMMANDS, ticks=100 + cadence + 5,
                       n_regions=N_REGIONS, trace_row_type=OmTraceRow,
                       setup=_build_scenario, corrupt_b=corrupt_b)

    assert report.diverged, "corrupting one bit of region 3's military did not trip the detector"
    assert report.first_divergent_tick == 100, (
        f"expected the corruption to surface at tick 100, got {report.first_divergent_tick}"
    )
    assert report.first_checkpoint_reported <= 110, (
        f"checkpoint reported at tick {report.first_checkpoint_reported}, "
        f"expected <= 110 (R-139-04: within {cadence} ticks of tick 100)"
    )
    assert report.region == 3
    assert report.field == "military"


def test_detector_names_first_field(lib):
    """Same corruption as the bit-flip control, a different field and region,
    to prove the name that comes back tracks what was actually corrupted
    rather than always reporting the same hardcoded answer."""
    cadence = lib.om_checksum_cadence()
    corrupt_b = [(50, {
        "region": 4, "field": "economy", "bit": 3,
        "econ_phase": 5.1, "tension_phase": 1.3,
    })]

    report = run_pair(lib, seed=SEED, commands=COMMANDS, ticks=50 + cadence + 5,
                       n_regions=N_REGIONS, trace_row_type=OmTraceRow,
                       setup=_build_scenario, corrupt_b=corrupt_b)

    assert report.diverged
    assert report.first_divergent_tick == 50
    assert report.region == 4
    assert report.field == "economy"


def _build_symmetric_attackers(lib, w):
    """A minimal scenario, independent of _build_scenario, built only to make
    tick 1's decision order deterministic and easy to reason about: three
    factions, three homes, all mutually hostile, each with exactly one
    telegraph/surprise roll due on tick 1."""
    isolate_agents(lib, w, friction=False, admin=False)
    lib.om_world_set_feature(w, OMFeature.DRIFT, 1)  # trace rows are appended
    # from the drift step (csrc/sim.c); FACTIONS-only leaves the trace empty
    # and this detector needs trace rows to name a diverging field.
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=200.0, confidence=1.5)
    set_faction(lib, w, 1, OMArchetype.FORTIFIER, budget=200.0, confidence=1.2)
    set_faction(lib, w, 2, OMArchetype.OPPORTUNIST, budget=200.0, confidence=1.3)
    for a, b in ((0, 1), (0, 2), (1, 2)):
        set_stance(lib, w, a, b, OMStance.HOSTILE)
    for f in (0, 1, 2):
        set_tech_multipliers(lib, w, f, 1.0, 1.0, 1.0)
    regions = [
        (0, OMTier.HOME, 0, 60.0, 55.0, 20.0, 55.0, 0.4, 1.7),
        (1, OMTier.FRONTIER, 0, 35.0, 40.0, 25.0, 40.0, 1.1, 2.3),
        (2, OMTier.HOME, 1, 45.0, 60.0, 15.0, 50.0, 2.0, 0.6),
        (3, OMTier.FRONTIER, 1, 30.0, 45.0, 30.0, 35.0, 3.4, 4.9),
        (4, OMTier.HOME, 2, 50.0, 50.0, 22.0, 45.0, 5.1, 1.3),
        (5, OMTier.FRONTIER, 2, 28.0, 38.0, 28.0, 30.0, 0.9, 3.2),
    ]
    for idx, tier, faction_id, mil, eco, ten, pop, ephase, tphase in regions:
        set_region(lib, w, idx, tier=tier, military=mil, economy=eco, tension=ten,
                   population=pop, econ_phase=ephase, tension_phase=tphase, faction_id=faction_id)
        set_owner(lib, w, idx, faction_id, held_since=-1)
    set_region(lib, w, 6, tier=OMTier.EMPTY, military=0.0, economy=20.0, tension=10.0,
               population=0.0, econ_phase=0.0, tension_phase=0.0, faction_id=-1)
    for a, b in [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (1, 6)]:
        set_edge(lib, w, a, b, OMEdge.BOTH)


def test_out_of_order_commands_trip(lib):
    """R-140-02-style peer-order hazard: two peers receive the same set of
    forced draws for tick 1 but queued in a different order.

    Investigated first with om_intent_inject: injecting the same two ATTACK
    intents in reversed call order on tick 1 made no difference to the
    outcome, honestly, because om_step_decisions recomputes every faction's
    decision from candidates each tick and never reads back an injected one
    (the same gap noted in the module docstring) -- so intent order is not
    an observable hazard for this step today, exactly the outcome the card
    told us to expect and report if it happened. Falling back to the card's
    suggested alternative: at tick 1 in this scenario all three factions
    naturally decide ATTACK and each consumes one forced draw, in
    faction-ascending order, for its telegraph-vs-surprise roll (ALG-15).
    Queuing the same three draws in a different order hands faction 0 a
    different draw against its own 0.7 threshold, flips its mode, and the
    two peers visibly diverge on tick 1."""
    draws_a = [0.75, 0.1, 0.5]
    draws_b = [0.5, 0.1, 0.75]
    commands_a = [{"tick": 1, "op": "rng_force", "draws": draws_a}]
    commands_b = [{"tick": 1, "op": "rng_force", "draws": draws_b}]

    report = run_pair(lib, seed=SEED, commands=commands_a, commands_b=commands_b,
                       ticks=10, n_regions=N_REGIONS, trace_row_type=OmTraceRow,
                       setup=_build_symmetric_attackers)

    assert report.diverged, (
        "reordering the same three forced draws across the two peers did not "
        "trip the detector -- decision order turned out not to be a hazard "
        "here after all"
    )
    assert report.first_divergent_tick == 1
    assert report.field is not None
