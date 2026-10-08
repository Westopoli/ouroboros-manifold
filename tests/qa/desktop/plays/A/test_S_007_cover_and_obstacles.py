"""Story play S-007 (E-01, R-007): "A tall obstacle hides units on more layers than a short one; cover hides but never
protects or blocks." Moment: the opening frame draws cover by class and the obstacles. Red on main: no cover_cells key."""
from play_support import count, has_key, moment


def test_s_007_cover_and_obstacles_are_drawn(tactical_game):
    state = moment(tactical_game.client, "S-007", "cover_on_field")
    assert has_key(state, "cover_cells") and has_key(state, "obstacles"), "S-007: no cover_cells / obstacles in the inventory"
    assert count(state, "cover_cells") > 0, "S-007: the field shows no cover"
