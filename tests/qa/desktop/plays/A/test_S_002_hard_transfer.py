"""Story play S-002 (E-01): "Changing layers takes time." (stories.md:8 "I order selected units to a layer and they go there as soon as they can.")
Proves [B R-002-01]: "Given a selected unit on layer 3 at a position where layer 5 is open, When the player issues a hard transfer to
layer 5, Then the unit begins its transition on the same tick and finishes on layer 5 after its transition duration (S-004)."
Also R-001-07 (a walker takes no layer order; the space era is all flyers) and the A16 order control (visible-game spec rev 12c, A16;
Architect 2026-10-12 GAP 1: every mission unit spawns on engine layer 0, so the play presses Q, one layer up, and asserts the layer above).
Moment: after a real box drag and the Q key, within 25 ticks a selected unit is in a layer transit (state & 4, docs/architecture.md
section 2) with tl equal to the layer above the lowest selected unit's layer (GAP 2: engine numbers on the wire; GAP 4: qa_state units carry tl).
Control (green today): the drag selected units and their layer values are in qa_state units.
Red on main: no layer key is bound (Q is unhandled), so no unit enters a transit inside 25 ticks."""
import time

from play_support import moment, qa, select_own_by_drag, step_until

MAX_TICKS = 25  # the spec's number: "assert within 25 ticks" (A16)


def _layers(q: dict) -> dict:
    return {uid: q["units"][uid]["layer"] for uid in q["selected"] if uid in q["units"]}


def test_s_002_hard_transfer_begins_a_transit_within_25_ticks(tactical_game):
    client = tactical_game.client
    select_own_by_drag(client)
    time.sleep(0.5)
    q = qa(client)
    selected = [str(s) for s in q["selected"]]
    assert len(selected) > 0, "S-002 CONTROL: the drag selected nothing (no unit to order to a layer)"
    q["selected"] = selected
    layers = _layers(q)
    assert len(layers) == len(selected) and all(isinstance(v, int) for v in layers.values()), \
        "S-002 CONTROL: the selected units' layer values are not all in qa_state units: %r" % layers
    types = {uid: q["units"][uid]["type"] for uid in layers}
    print("S-002 premises: tick=%s selected=%d layers=%r types=%r" % (q["tick"], len(selected), sorted(set(layers.values())), sorted(set(types.values()))))
    low = min(layers.values())
    asked = low + 1  # Q = one layer up from the lowest selected unit (Q-A16-01 (a)); engine numbers (GAP 2)
    client.call("input", "key", "Q")

    def in_transit(state: dict) -> bool:
        for uid in selected:
            u = state["units"].get(uid)
            if u and int(u.get("state", 0)) & 4 and u.get("tl") == asked:
                return True
        return False

    ok = step_until(client, in_transit, MAX_TICKS)
    state = moment(client, "S-002", "hard_transfer")
    last = state.get("last_command", {})
    seen = {uid: (state["units"][uid].get("state"), state["units"][uid].get("tl"), state["units"][uid].get("layer"))
            for uid in selected[:5] if uid in state["units"]}
    assert ok, ("S-002: R-002-01 no selected unit began a layer transit (state & 4, tl == %d) within %d ticks of Q; "
                "last_command=%r first units (state, tl, layer)=%r" % (asked, MAX_TICKS, last, seen))
