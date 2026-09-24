"""E-03 S-021 (a fresh galaxy from a seed), ALG-26 (docs/bible/algorithms.md)
-- a generated faction's tech multipliers must equal the ALG-26 formula from
creation, and its budget must accrue over ticks, exactly like a hand-set
faction does.

B4-2: csrc/worldgen.c writes w->faction_archetype/faction_tech directly in
om_world_generate's faction-setup and per-faction placement loops -- it never
goes through om_faction_set (that setter's confidence roll would insert an
RNG draw the E-03 draw order does not have, R-022-04). Only om_faction_set
calls om_faction_tech_multipliers_recalc (commit d61bd52), which caches
w->faction_tech_attack/defense/economy; the public om_faction_tech_attack/
defense/economy accessors (csrc/diplomacy.c) do not read that cache -- they
recompute the ALG-26 formula live from w->faction_archetype/faction_tech every
call, so test_R_ALG_26_generated_faction_multipliers_match_formula below
passes on main whether or not the cache was ever recalculated (it is a
correctness check on the read path, not a detector for this bug). The cache
is read directly, by field, only inside csrc/faction.c's
om_faction_step_budget (`delta *= w->faction_tech_economy[f]`) and in
resolve.c/collision.c's combat math -- so a generated faction's stale
calloc-zero cache is invisible to every accessor and only shows up as budget
that never grows. test_R_ALG_26_generated_faction_budget_grows_over_50_ticks
is the regression detector: red on main, `assert budget > 0.0` fails with
`0.0 > 0.0` (faction 0, seed 7, 8 factions, 60-90 regions, quoted below).

Positive control (test_R_ALG_26_hand_built_faction_matches_formula) exercises
the same multiplier-formula assertion through om_faction_set instead of
generation -- green on both sides of the fix, proving the assertion itself is
right.
"""
import pytest

from conftest import (
    OMArchetype,
    gen_set_faction_count,
    gen_set_region_range,
    generate,
    set_faction,
)

# ALG-26 table (docs/bible/algorithms.md), (attack, defense, economy) per
# archetype -- values from csrc/om_constants.h's OM_ARCHETYPE_TECH_MULTIPLIERS_*.
ARCHETYPE_TECH_MULTIPLIERS = {
    OMArchetype.PLAYER: (0.06, 0.07, 0.07),
    OMArchetype.CONQUEROR: (0.16, 0.02, 0.02),
    OMArchetype.FORTIFIER: (0.03, 0.09, 0.08),
    OMArchetype.OPPORTUNIST: (0.10, 0.05, 0.05),
    OMArchetype.WARLORD: (0.14, 0.04, 0.02),
    OMArchetype.SCHISM: (0.12, 0.04, 0.04),
    OMArchetype.BREAKAWAY: (0.06, 0.08, 0.06),
}

# csrc/om_internal.h OM_TIE_EPSILON; the formula is identical double
# arithmetic on both sides so an exact match is expected, but this keeps
# the assertion from being flaky on a compiler reassociation.
OM_TIE_EPSILON = 1e-9


def _expected_multipliers(archetype, tech):
    attack_w, defense_w, economy_w = ARCHETYPE_TECH_MULTIPLIERS[archetype]
    return (
        1.0 + (tech / 100.0) * attack_w,
        1.0 + (tech / 100.0) * defense_w,
        1.0 + (tech / 100.0) * economy_w,
    )


def _assert_faction_multipliers_match_formula(lib, w, faction_id):
    archetype = lib.om_faction_archetype(w, faction_id)
    tech = lib.om_faction_tech(w, faction_id)
    exp_attack, exp_defense, exp_economy = _expected_multipliers(archetype, tech)
    assert lib.om_faction_tech_attack(w, faction_id) == pytest.approx(exp_attack, abs=OM_TIE_EPSILON), (
        f"faction {faction_id} (archetype {archetype}, tech {tech}): attack multiplier wrong"
    )
    assert lib.om_faction_tech_defense(w, faction_id) == pytest.approx(exp_defense, abs=OM_TIE_EPSILON), (
        f"faction {faction_id} (archetype {archetype}, tech {tech}): defense multiplier wrong"
    )
    assert lib.om_faction_tech_economy(w, faction_id) == pytest.approx(exp_economy, abs=OM_TIE_EPSILON), (
        f"faction {faction_id} (archetype {archetype}, tech {tech}): economy multiplier wrong"
    )


def test_R_ALG_26_generated_faction_multipliers_match_formula(lib, world_factory):
    """Given a generated world, When each faction's tech multipliers are read
    right after generation, Then every one equals ALG-26's
    1 + tech/100 * ARCHETYPE_TECH_MULTIPLIERS[archetype][axis]. Passes on
    main regardless of the B4-2 bug (module docstring): the accessor
    recomputes live from faction_archetype/faction_tech, never from the
    stale cache; kept as a correctness check on those reads."""
    w = world_factory(n_regions=0, seed=7)
    gen_set_faction_count(lib, w, 8)
    gen_set_region_range(lib, w, 60, 90)
    assert generate(lib, w) == 1, "world generation must succeed for this seed/config"

    n_factions = lib.om_faction_count(w)
    assert n_factions == 8
    for faction_id in range(n_factions):
        _assert_faction_multipliers_match_formula(lib, w, faction_id)


def test_R_ALG_26_generated_faction_budget_grows_over_50_ticks(lib, world_factory):
    """Given a generated world with the faction/economy features on (the
    world_factory default set: EVENTS, FACTIONS, FRICTION, ADMIN_REVOLTS,
    DRIFT), When 50 ticks run, Then every faction's budget has grown above
    its starting 0.0 -- om_faction_step_budget's delta is scaled by
    faction_tech_economy (csrc/faction.c), which is 0.0 (all growth zeroed)
    unless the generation path recalculates it."""
    w = world_factory(n_regions=0, seed=7)
    gen_set_faction_count(lib, w, 8)
    gen_set_region_range(lib, w, 60, 90)
    assert generate(lib, w) == 1, "world generation must succeed for this seed/config"

    n_factions = lib.om_faction_count(w)
    for faction_id in range(n_factions):
        assert lib.om_faction_budget(w, faction_id) == pytest.approx(0.0, abs=OM_TIE_EPSILON), (
            "a freshly generated faction must start at budget 0.0"
        )

    for _ in range(50):
        lib.om_world_step(w)

    for faction_id in range(n_factions):
        budget = lib.om_faction_budget(w, faction_id)
        assert budget > 0.0, (
            f"faction {faction_id} budget must grow over 50 ticks (every generated "
            f"home/frontier region's economy is well above the 8.0 floor ALG-27's "
            f"delta uses), got {budget}"
        )


def test_R_ALG_26_hand_built_faction_matches_formula(lib, world_factory):
    """Positive control: the same assertion the two tests above make on a
    generated faction, made instead on a hand-built one (om_faction_set),
    which already calls om_faction_tech_multipliers_recalc (commit d61bd52).
    Green on main -- proves the assertion is right and only the generation
    path (csrc/worldgen.c) is broken."""
    w = world_factory(n_regions=1, seed=1)
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=0.0, tech=40.0)
    _assert_faction_multipliers_match_formula(lib, w, 0)
