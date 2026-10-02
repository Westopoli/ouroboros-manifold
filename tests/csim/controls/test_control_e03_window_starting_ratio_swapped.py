"""F5 window control (two-day-push brief, docs/northstar/plans/briefs/2026-09-22-two-day-push.md)
for csrc/worldgen.c (E-03, wave 1 card B4). Not one of the 92 gen_controls.py
placeholders; a fresh scenario authored against the module's own rule so the
leaf has a live detector to plant OM_BUG_STARTING_RATIO_SWAPPED (id 312,
csrc/ouroboros_sim.h om_bug_e03) against.

Rule (docs/bible/algorithms.md ALG-30 "general formula"): every frontier
region, and a player faction's home (the player has no archetype range), is
seeded as `economy = population * STARTING_ECO_RATIO(1.1) + jitter_e`,
`military = population * STARTING_MIL_RATIO(0.7) + jitter_m`, each jitter an
independent uniform draw in [-STARTING_FIELD_JITTER(5.0), +5.0]. Draw order
per region: population, economy slot, military slot, tension jitter, econ
phase, tension phase (ALG-30's own "draw order" paragraph).

PLANT: under OM_BUG_STARTING_RATIO_SWAPPED, om_world_generate computes
`economy = population * STARTING_MIL_RATIO(0.7) + jitter_e` and
`military = population * STARTING_ECO_RATIO(1.1) + jitter_m` -- the two
ratio constants swapped, jitters and draw order untouched.

Fixture (TD-A122-e03-fixture: the old single-faction, n_regions=4 fixture was
infeasible, om_world_generate returns at worldgen.c:181 with fewer than 2
factions): two factions, n_regions=8. The player (faction 0) home follows the
general formula; the AI faction's archetype home (region 3) uses its range
path and is skipped. Extra edges disabled (the isolation switch
ALG-31/header documents for exactly this kind of placement test, so no extra
draws land between regions). The RNG is forced through the whole draw
sequence with the SAME economy-jitter (u=0.70 -> jitter +2.0) and
military-jitter (u=0.20 -> jitter -3.0) draw repeated for every region, so
the test does not need to know which region index the generator assigns to
the home versus each frontier (an implementation detail the epic text does
not pin down) -- every inhabited region must show the same wrong economy/
military relationship to its own (independently read back) population.
"""
import pytest

from conftest import (
    OMBugE03,
    OMField,
    OMTier,
    force_draws,
    gen_set_extra_edges_enabled,
    gen_set_faction_count,
    generate,
)

STARTING_ECO_RATIO = 1.1
STARTING_MIL_RATIO = 0.7
AI_HOME_REGION = 3


def test_control_starting_ratio_swapped_trips_the_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=8, seed=3120001)
    gen_set_faction_count(dbg, w, 2)
    gen_set_extra_edges_enabled(dbg, w, 0)
    dbg.om_debug_inject(w, OMBugE03.STARTING_RATIO_SWAPPED)

    # template roll (Isolated bucket [0, 1/3)), then 6 repeats of the
    # per-region 6-slot draw group (population, eco jitter, mil jitter,
    # tension jitter, econ phase, tension phase) -- more repeats than the 3
    # inhabited regions actually need, so any corridor/shuffle draws this
    # test does not account for cannot shift a real region's jitter slot.
    per_region = [0.40, 0.70, 0.20, 0.50, 0.50, 0.50]
    force_draws(dbg, w, [0.10, 0.10] + per_region * 12)

    assert generate(dbg, w) == 1, "fixture setup: n_regions=8 must be feasible for two factions"

    jitter_e = -5.0 + 10.0 * 0.70   # +2.0
    jitter_m = -5.0 + 10.0 * 0.20   # -3.0

    checked = 0
    for idx in range(8):
        if dbg.om_region_tier(w, idx) == OMTier.EMPTY:
            continue
        if idx == AI_HOME_REGION:
            continue  # archetype range path, not the general formula
        checked += 1
        p = dbg.om_region_field(w, idx, OMField.POPULATION)
        e = dbg.om_region_field(w, idx, OMField.ECONOMY)
        m = dbg.om_region_field(w, idx, OMField.MILITARY)
        buggy_e = p * STARTING_MIL_RATIO + jitter_e
        buggy_m = p * STARTING_ECO_RATIO + jitter_m
        correct_e = p * STARTING_ECO_RATIO + jitter_e
        correct_m = p * STARTING_MIL_RATIO + jitter_m
        assert e == pytest.approx(buggy_e, abs=1e-6), (
            f"region {idx}: OM_BUG_STARTING_RATIO_SWAPPED injected but economy "
            f"still reads population*1.1+jitter ({correct_e}) instead of the "
            f"swapped population*0.7+jitter ({buggy_e}) -- the detector did not trip"
        )
        assert m == pytest.approx(buggy_m, abs=1e-6), (
            f"region {idx}: OM_BUG_STARTING_RATIO_SWAPPED injected but military "
            f"still reads population*0.7+jitter ({correct_m}) instead of the "
            f"swapped population*1.1+jitter ({buggy_m}) -- the detector did not trip"
        )
    assert checked == 5, "fixture setup: expected 5 general-formula regions (probe: 0,1,2,4,5)"
