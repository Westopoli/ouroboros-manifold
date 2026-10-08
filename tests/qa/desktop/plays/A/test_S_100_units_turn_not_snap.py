"""Story plays S-100, S-101 (E-13; the S-100 turn rule is the sim's, its visible half is this interpolation): "Units face what they shoot and where they go, and turn rather than snap"; "I see units
turn, slow behind blockers, and settle." Moment: a unit under way is sampled over real time; the drawn position changes by
more distinct values than the sim ticks seen (interpolation, A2), and the drawn facing follows the sim facing.
Red on main: the view draws sim positions only, so drawn positions change once per tick."""
import time

from play_support import moment, qa


def test_s_101_drawn_positions_between_ticks(tactical_game):
    client = tactical_game.client
    client.call("input", "drag", 0, 0, 1900, 140)
    client.call("input", "click", 960, 540, 2)
    time.sleep(0.3)
    moment(client, "S-101", "under_way")
    ticks, drawn = set(), set()
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        q = qa(client)
        ticks.add(int(q["tick"]))
        for uid, p in q["units_px"].items():
            drawn.add((uid, round(p[0], 2), round(p[1], 2)))
        time.sleep(0.03)
    per_unit = max((len([d for d in drawn if d[0] == u]) for u in {d[0] for d in drawn}), default=0)
    assert per_unit > len(ticks), "S-101: one unit was drawn at %d positions across %d sim ticks; interpolation must add in-between positions" % (per_unit, len(ticks))
