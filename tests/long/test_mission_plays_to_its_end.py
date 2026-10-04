"""Long-mission suite: a mission played through the pipe to its own end.

Never sends mission_end. The player force is given attack-move orders (half
toward the objective node, half toward the enemy centroid, refreshed every
REORDER_TICKS), then tactical_step runs in batches until the frame reports
mission_over or deadline_ticks * 1.10 is passed.

Rules asserted (docs/bible/epics/E-10-missions.md): R-075-07 (a mission ends
on the first of objectives done, time limit, player force eliminated) and
R-076-01 (the time limit is the mission's deadline_ticks). Debrief band and
progress ranges: R-077-02 (five bands, -1 is the unknown sentinel before an end).
Recorded, never asserted: ticks, how it ended, alive per side, retention, wall time.

Known gap, not a bug of this suite: destroy_targets and escort objectives are
not evaluated yet (assault, siege_breaking, interception, evacuation can only end
by clock or wipe); their rows carry gap=True.
"""
import json
import os
import time

import pytest

from harness import ARCHETYPES, FEATURES, N_REGIONS, PIPE, Pipe

SEEDS = [int(s) for s in os.environ.get("OM_LONG_SEEDS", "3,5,6,7,1,4,264").split(",")]
BATCH = 250
REORDER_TICKS = 1000
TACTICAL_TICK_RATE = 20  # csrc/om_constants.h OM_TACTICAL_TICK_RATE: game seconds = ticks / 20
RESULTS = os.environ.get("OM_LONG_RESULTS", "/tmp/om_long_results.jsonl")
GAP = {"assault", "siege_breaking", "interception", "evacuation"}  # destroy_targets / escort

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")


def _mid(units):
    return (sum(u["x"] for u in units) / len(units), sum(u["y"] for u in units) / len(units))


def _order(pp, ids, x, y):
    if not ids:
        return
    r = pp.send("command", verb="attack_move", units=ids, x=x, y=y)
    assert r["type"] == "ack", r


def _play(seed):
    t0 = time.time()
    pp = Pipe()
    out = {"seed": seed}
    try:
        pp.cmd("set_seed", seed=seed, n_regions=N_REGIONS, features=FEATURES)
        pp.cmd("snapshot")
        snap = pp.read_more()
        pf = snap.get("player_faction", 0)
        m = pp.send("mission_start", faction=pf)
        assert m["type"] == "mission", m
        deadline = m["deadline_ticks"]
        out.update(archetype=ARCHETYPES[m["archetype"]], deadline=deadline)
        out["gap"] = out["archetype"] in GAP
        t = pp.send("mission_begin")
        assert t["type"] == "tactical", t
        units = t["units"]
        mine = [u for u in units if u["faction"] == pf]
        foe = [u for u in units if u["faction"] != pf]
        out["start_alive"] = [len(mine), len(foe)]
        hp0 = {u["id"]: u["hp"] for u in units}
        side = {u["id"]: u["faction"] == pf for u in units}
        nodes = {n["i"]: n for n in t["map"]["nodes"]}
        obj_node = next((o["node"] for o in m["objectives"] if o["primary"]), -1)
        damaged = set()

        def orders(frame_units):
            me = [u for u in frame_units if u["faction"] == pf]
            en = [u for u in frame_units if u["faction"] != pf]
            ids = sorted(u["id"] for u in me)
            half = len(ids) // 2
            a, b = ids[:half], ids[half:]
            if obj_node in nodes:
                _order(pp, a, nodes[obj_node]["x"], nodes[obj_node]["y"])
            else:
                b = ids
            if en:
                _order(pp, b, *_mid(en))
            elif obj_node in nodes:
                _order(pp, b, nodes[obj_node]["x"], nodes[obj_node]["y"])

        orders(units)
        cap = int(deadline * 1.10)
        ticks, last, next_order = 0, t, REORDER_TICKS
        while not last["mission_over"] and ticks < cap:
            n = BATCH if ticks + BATCH < deadline - BATCH else 1  # single steps near the limit
            if n == 1 and ticks >= deadline + 50:
                n = BATCH
            last = pp.send("tactical_step", n=n, full=True)
            assert last["type"] == "tactical", last
            ticks += n
            for u in last["units"]:
                if u["id"] in hp0 and u["hp"] < hp0[u["id"]]:
                    damaged.add(u["id"])
            alive_ids = {u["id"] for u in last["units"]}
            for uid in hp0:
                if uid not in alive_ids:
                    damaged.add(uid)
            if ticks >= next_order and not last["mission_over"]:
                orders(last["units"])
                next_order += REORDER_TICKS
        out["ticks"] = ticks
        out["over"] = bool(last["mission_over"])
        out["band_tactical"] = last["band"]
        out["progress"] = [o["progress"] for o in last["objectives"]]
        out["alive"] = [sum(1 for u in last["units"] if u["faction"] == pf),
                        sum(1 for u in last["units"] if u["faction"] != pf)]
        out["fought"] = [any(side[i] for i in damaged if i in side),
                         any(not side[i] for i in damaged if i in side)]
        if out["over"]:
            out["end"] = ("force wiped" if out["alive"][0] == 0 else
                          "clock" if ticks >= deadline - 2 else "objective complete")
        out["wall_s"] = round(time.time() - t0, 1)
        out["tps"] = round(ticks / max(out["wall_s"], 0.01), 1)
        out["game_s"] = ticks / TACTICAL_TICK_RATE
        # post-mission: jump then chronicle, chapter advance (no mission_end sent)
        chap0 = snap.get("chapter")
        j = pp.send("jump", ticks=50)
        out["jump_first"] = j["type"]
        if j["type"] == "chronicle":
            s1 = pp.read_more()
            out["chapter"] = [chap0, s1.get("chapter")]
        else:
            out["jump_err"] = j
    finally:
        pp.close()
    return out


_cache = {}


@pytest.fixture(params=SEEDS, ids=lambda s: "seed%d" % s)
def run(request):
    seed = request.param
    if seed not in _cache:
        _cache[seed] = _play(seed)
        with open(RESULTS, "a") as f:
            f.write(json.dumps(_cache[seed]) + "\n")
    return _cache[seed]


def test_mission_ends_by_itself_at_or_before_its_time_limit(run):
    """R-075-07 + R-076-01."""
    assert run["over"], "no mission_over in %d ticks (cap 110%% of deadline %d)" % (run["ticks"], run["deadline"])
    assert run["ticks"] <= run["deadline"] + 2, "ended at tick %d past deadline %d" % (run["ticks"], run["deadline"])


def test_end_state_has_band_and_progress_in_range(run):
    assert run["band_tactical"] in (0, 1, 2, 3, 4), "band %r not one of the five bands" % run["band_tactical"]
    for p in run["progress"]:
        assert 0.0 <= p <= 1.0, run["progress"]


def test_both_sides_took_part(run):
    if not any(run["fought"]):
        pytest.fail("no fighting happened: no unit on either side lost hp or died")
    assert run["fought"][0] and run["fought"][1], "only one side was hit: fought=%r" % run["fought"]


def test_post_mission_jump_and_chapter_advance(run):
    assert run.get("jump_first") == "chronicle", run.get("jump_err")
    assert run["chapter"][1] == run["chapter"][0] + 1, run["chapter"]
