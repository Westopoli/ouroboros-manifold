"""B3 rivals half (mission-plays plan): om_mission_end tags rivals
(R-058-05: when a mission ends, every named enemy-faction character in the
mission region gains a rival tag pointing at the player's commander).

Isolation of om_mission_tag_rivals itself is
test_E08_S058_who_i_come_back_as.py::test_R_058_05_every_named_enemy_faction_character;
this file proves it is reached from om_mission_end, with a positive control.

Setup note: om_mission_end is called with no commander argument and the
mission state holds no commander id today. The only commander marker is
om_character_selector_confirm_commander (main-character flag), so the
commander is confirmed that way. How the Doer sources the id is a flagged
ambiguity (see the report); these tests pin only the observable tags.

See also: csrc/generational.c om_mission_tag_rivals.
"""
from conftest import OMArchetype, set_faction, set_owner

PLAYER_FAC = 0
ENEMY_FAC = 1
MISSION_REGION = 0
DEFENSIVE_STAND = 0
COMMANDER = 10
ENEMY_NAMED = 20
FRIENDLY_NAMED = 30
ENEMY_ELSEWHERE = 40


def _world(lib, world_factory):
    w = world_factory(n_regions=2)
    lib.om_world_set_feature(w, 8, 1)  # OMFeature.TACTICAL
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY_FAC, held_since=-1)
    set_owner(lib, w, 1, PLAYER_FAC, held_since=-1)

    lib.om_character_create(w, character_id=COMMANDER, lineage_id=1, region_idx=MISSION_REGION, rank=3, birth_tick=0, lifespan=100)
    lib.om_character_set_faction(w, COMMANDER, faction_id=PLAYER_FAC)
    lib.om_character_selector_confirm_commander(w, character_id=COMMANDER)
    lib.om_character_create(w, character_id=ENEMY_NAMED, lineage_id=2, region_idx=MISSION_REGION, rank=1, birth_tick=10, lifespan=100)
    lib.om_character_set_faction(w, ENEMY_NAMED, faction_id=ENEMY_FAC)
    lib.om_character_create(w, character_id=FRIENDLY_NAMED, lineage_id=1, region_idx=MISSION_REGION, rank=1, birth_tick=15, lifespan=100)
    lib.om_character_set_faction(w, FRIENDLY_NAMED, faction_id=PLAYER_FAC)
    lib.om_character_create(w, character_id=ENEMY_ELSEWHERE, lineage_id=3, region_idx=1, rank=1, birth_tick=12, lifespan=100)
    lib.om_character_set_faction(w, ENEMY_ELSEWHERE, faction_id=ENEMY_FAC)

    lib.om_mission_setup(w, MISSION_REGION, DEFENSIVE_STAND, 0)
    lib.om_mission_build_objectives(w, DEFENSIVE_STAND)
    return w


def _tagged(lib, w, cid):
    return lib.om_character_has_rival_tag(w, character_id=cid, target_commander_id=COMMANDER)


def test_R_058_05_no_rival_tags_before_the_mission_ends(lib, world_factory):
    w = _world(lib, world_factory)
    assert _tagged(lib, w, ENEMY_NAMED) == 0


def test_R_058_05_positive_control_direct_tag_rivals_tags_the_enemy(lib, world_factory):
    """Control: the detector (has_rival_tag) fires when tag_rivals runs, so the
    wired test below cannot pass or fail for a reason in the detector."""
    w = _world(lib, world_factory)
    lib.om_mission_tag_rivals(w, mission_region=MISSION_REGION, commander_id=COMMANDER)
    assert _tagged(lib, w, ENEMY_NAMED) == 1
    assert _tagged(lib, w, FRIENDLY_NAMED) == 0


def test_R_058_05_mission_end_tags_the_named_enemy_in_the_mission_region(lib, world_factory):
    w = _world(lib, world_factory)
    lib.om_mission_end(w)
    assert _tagged(lib, w, ENEMY_NAMED) == 1, (
        "R-058-05: om_mission_end must tag the named enemy-faction character in the mission region")


def test_R_058_05_mission_end_does_not_tag_friendlies_or_other_regions(lib, world_factory):
    w = _world(lib, world_factory)
    lib.om_mission_end(w)
    assert _tagged(lib, w, ENEMY_NAMED) == 1, "precondition: the end path tagged the enemy at all"
    assert _tagged(lib, w, FRIENDLY_NAMED) == 0
    assert _tagged(lib, w, ENEMY_ELSEWHERE) == 0
    assert _tagged(lib, w, COMMANDER) == 0
