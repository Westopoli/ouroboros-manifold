"""Story plays S-005, S-091, S-092 (E-01/E-12, R-089-03/04): sight discs from unit sight; an elevated unit sees farther;
the outside is dimmed; nothing is remembered. Moments: the opening frame; after 100 ticks of movement.
Red on main: no fog_layer inventory."""
from play_support import count, has_key, moment


def test_s_005_sight_discs_exist(tactical_game):
    state = moment(tactical_game.client, "S-005", "opening_sight")
    assert has_key(state, "fog_layer"), "S-005: no fog_layer in the inventory"
    assert count(state, "fog_layer") > 0, "S-005: fog_layer shows no sight disc for the player's units"


def test_s_091_sight_discs_follow_the_units(tactical_game):
    client = tactical_game.client
    client.call("input", "drag", 0, 0, 1900, 140)
    client.call("input", "click", 960, 540, 2)
    client.call("step", 20)
    state = moment(client, "S-091", "sight_after_20_ticks")
    assert count(state, "fog_layer") > 0, "S-091: no sight disc 20 ticks into a move; an elevated unit must see farther (discs from unit.sight)"


def test_s_092_only_what_is_in_sight_is_drawn(tactical_game):
    client = tactical_game.client
    client.call("step", 100)
    state = moment(client, "S-092", "after_100_ticks")
    assert has_key(state, "fog_layer") and count(state, "fog_layer") > 0, "S-092: no sight discs after 100 ticks"
    assert len(state["units_px"]) < int(state["unit_count"]), "S-092: R-089-04 every unit is drawn; enemies outside sight must not be"
