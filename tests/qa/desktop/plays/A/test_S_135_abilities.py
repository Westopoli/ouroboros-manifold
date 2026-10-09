"""Story plays S-135, S-086 (E-18/E-11): "Every ability reads at a glance as an ability in progress"; "each unit has exactly one
ability". Moment: the selection panel shows one ability slot per type, and an ability effect appears once an ability event
arrives (abilities_fx). The ability trigger is the activate_ability verb wrapper (K-a, not built): this play only reads the
inventory. Red on main: no abilities_fx inventory."""
import time

from play_support import count, has_key, moment, qa, select_own_by_drag


def test_s_135_ability_slots_and_fx_inventory(tactical_game):
    client = tactical_game.client
    select_own_by_drag(client)
    time.sleep(0.5)
    state = moment(client, "S-135", "ability_slot")
    assert has_key(state, "abilities_fx"), "S-135: no abilities_fx in the inventory"
    assert has_key(state, "hud.selection") and count(state, "hud.selection") > 0, "S-086: the selection panel shows no ability slot"
