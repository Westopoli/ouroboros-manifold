"""Story plays S-100, S-101 (E-13; the S-100 turn rule is the sim's, its visible half is this interpolation): "Units face what they shoot and where they go, and turn rather than snap"; "I see units
turn, slow behind blockers, and settle." Moment: a unit under way is sampled SAMPLES times in quick succession (about 1 s). A qa_state call now costs one display
frame (0.67 ticks per call, 1.33 before; TD-VG-A-8), so the sampler polls until the tick has advanced and keeps that sample:
every sample lands on a new tick. The tick count cannot be held fixed (TD-VG-A-2, assumption-changed). The interpolation shows instead as (a) the drawn position of the moving unit
changing across the samples, (b) the drawn position sitting between sim positions rather than on the sim position in at
least one sample, and (c) no snap: no drawn jump exceeds the sim jump between the same two samples plus one frame step.
Red on main: the view draws sim positions only, so drawn equals the sim position in every sample."""
import math
import time

from play_support import moment, qa, select_own_by_drag

SAMPLES = 8


def _sim_px(q, uid):
    u, cam, sc = q["units"][uid], q["camera"], q["scale"]
    return ((u["x"] - cam["x"]) * sc + 960, (u["y"] - cam["y"]) * sc + 540)


def test_s_101_drawn_positions_between_ticks(tactical_game):
    client = tactical_game.client
    select_own_by_drag(client)
    client.call("input", "click", 960, 540, 2)
    time.sleep(0.3)
    moment(client, "S-101", "under_way")
    t0 = time.monotonic()
    rows = []  # (tick, {uid: (drawn, sim)})
    for i in range(SAMPLES):
        q = qa(client)
        for _ in range(50):
            if i == 0 or int(q["tick"]) > rows[-1][0]:
                break
            q = qa(client)
        rows.append((int(q["tick"]), {uid: (tuple(p), _sim_px(q, uid)) for uid, p in q["units_px"].items() if uid in q["units"]}))
    span = time.monotonic() - t0
    assert span < 3.0, "S-101: %d samples took %.1f s; the sampler is too slow to show the in-between positions" % (SAMPLES, span)
    uids = set.intersection(*[set(r[1]) for r in rows])
    travel = {u: math.dist(rows[0][1][u][1], rows[-1][1][u][1]) for u in uids}
    uid = max(travel, key=travel.get)
    assert travel[uid] > 0.0, "S-101: no unit moved across the samples"
    drawn = [r[1][uid][0] for r in rows]
    sim = [r[1][uid][1] for r in rows]
    ticks = [r[0] for r in rows]
    assert len(set(drawn)) >= SAMPLES - 1, "S-101: unit %s drawn at %d distinct positions in %d samples" % (uid, len(set(drawn)), SAMPLES)
    off_sim = [i for i in range(SAMPLES) if math.dist(drawn[i], sim[i]) > 1e-6]
    assert off_sim, "S-101: unit %s was drawn exactly on its sim position in all %d samples; no interpolation (ticks %s)" % (uid, SAMPLES, ticks)
    step = max(math.dist(sim[i], sim[i + 1]) / max(ticks[i + 1] - ticks[i], 1) for i in range(SAMPLES - 1))
    for i in range(SAMPLES - 1):
        jump = math.dist(drawn[i], drawn[i + 1])
        bound = math.dist(sim[i], sim[i + 1]) + step + 1e-6
        # TD-VG-A-3: one display pixel of tolerance; the old tie at the larger scale was float noise
        assert jump <= bound + 1.0, "S-101: unit %s snapped %.3f px between samples %d and %d (ticks %d,%d); sim jump plus one frame step is %.3f (tolerance 1.0 px)" % (uid, jump, i, i + 1, ticks[i], ticks[i + 1], bound)
