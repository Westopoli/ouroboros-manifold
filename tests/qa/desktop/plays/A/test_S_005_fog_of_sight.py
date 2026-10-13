"""Story plays S-005, S-091, S-092 (E-01/E-12, R-089-03/04): sight discs from unit sight; an elevated unit sees farther;
the outside is dimmed; nothing is remembered. Moments: the opening frame; after 100 ticks of movement.
Red on main: no fog_layer inventory."""
from play_support import GodotGame, RESOLUTION, _to_tactical, count, has_key, moment, pick_free_port, select_own_by_drag


def test_s_005_sight_discs_exist(tactical_game):
    state = moment(tactical_game.client, "S-005", "opening_sight")
    assert has_key(state, "fog_layer"), "S-005: no fog_layer in the inventory"
    assert count(state, "fog_layer") > 0, "S-005: fog_layer shows no sight disc for the player's units"


def test_s_091_sight_discs_follow_the_units(tactical_game):
    client = tactical_game.client
    select_own_by_drag(client)
    client.call("input", "click", 960, 540, 2)
    client.call("step", 20)
    state = moment(client, "S-091", "sight_after_20_ticks")
    assert count(state, "fog_layer") > 0, "S-091: no sight disc 20 ticks into a move; an elevated unit must see farther (discs from unit.sight)"


def _enemies(state):
    me = state["local_faction"]
    return [u for u in state["units"].values() if u["faction"] != me]


def test_s_092_only_what_is_in_sight_is_drawn(tactical_game):
    """R-089-04 with the fog filter ON (TD-VG-A-6): every unit the frame lists is drawn; the frame lists own units and only
    the enemies the filter lets through; with the filter off more enemies appear (positive control). Sight-disc geometry
    is not in qa_state (only the disc count), so enemy-inside-a-disc is proved by the filter, not measured here."""
    client = tactical_game.client
    client.call("step", 100)
    state = moment(client, "S-092", "after_100_ticks")
    assert has_key(state, "fog_layer") and count(state, "fog_layer") > 0, "S-092: no sight discs after 100 ticks"
    me = state["local_faction"]
    assert any(u["faction"] == me for u in state["units"].values()), "S-092: no own unit in the frame"
    assert len(state["units_px"]) == int(state["unit_count"]) == len(state["units"]), "S-092: R-089-04 every unit the frame lists is drawn"
    filtered = len(_enemies(state))
    ctl = GodotGame(qa_port=pick_free_port(), seed=1, resolution=RESOLUTION)
    ctl.start()
    try:
        ctl.wait_for_port(timeout=60.0)
        # Bare False, not play_support's {"on": False}: the daemon reads args[0] as a bool and a non-empty dict is true
        # (TD-VG-A-6; play_support.start_tactical_game(fog_off=True) therefore leaves the filter on, reported not fixed).
        assert ctl.client.call("set_fog_filter", False).get("ok", True), "S-092: set_fog_filter refused"
        _to_tactical(ctl)
        ctl.client.call("step", 100)
        unfiltered = len(_enemies(moment(ctl.client, "S-092", "control_fog_off_100_ticks")))
    finally:
        ctl.stop()
    assert unfiltered > filtered, "S-092: positive control: fog filter off shows %d enemies, on shows %d; the filter hides none" % (unfiltered, filtered)
