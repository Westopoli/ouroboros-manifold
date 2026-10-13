"""Story play S-088 (E-13, via E-13/E-13.png): the player sees a unit as a small group of models moving as one (R-132-03).
Moment: the opening frame. Red on main: no squads inventory."""
from play_support import has_key, moment


def test_s_088_squads_are_in_the_inventory(tactical_game):
    state = moment(tactical_game.client, "S-088", "squads_opening")
    assert has_key(state, "squads"), "S-088: no squads in the inventory (R-132-03: 3 to 5 models per strike unit)"
