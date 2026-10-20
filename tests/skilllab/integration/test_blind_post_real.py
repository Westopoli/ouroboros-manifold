# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 43 item 6 and decision 44 (Architect, 2026-10-19): blind naive-defender posts, shift then refuse
"""LAB-REV2-FIX round 3, real layouts. Interface in tests/skilllab/test_drift_fix_blind_post.py's header.

  - Positive control (library, no fight): scenes.sight_clear agrees with the engine's own om_unit_can_see on seeded pairs of units on the real blocks of layouts 192 and
    81, 100 to 560 wu apart (inside the sensor radius, so range is not what decides), read where the engine left the units after one step (it moves a unit out of a
    blocked cell). This is what makes the lab-side probe trustworthy as 'sight under R-098-02'.
  - Gated (OM_LAB_SLOW=1): the real shift. Layout 81 (the doorway at x 1505 to 1595 is 60 wu wide: both 100 wu cells of it are blocked, so a post in the doorway sees
    nothing), s3_types_by_reach, naive_defender_attacker_layer, 8 enemy units: the type posts that are blind to the attackers' start are moved, the ones with a clear line
    stay, each moved post is sighted per the probe and within 200 wu, the label carries the largest distance, the pre-flight reads ok. The fight outcome is not pinned. The
    same test checks the refusal on layout 78 (s4_bait, naive_defender: post (350, 2000) has no sighted cell within 200 wu): label blind_post, nothing moved.

NOT PINNED, SURPRISE (question Q-FIX3-3): on layout 192 the post (805, 2000) of s3_types_by_reach / naive_defender_attacker_layer, named in the brief as shifted, is NOT blind
under this probe: the doorway there is 240 wu wide (gap rows 1880 to 2120, sight rows 19 and 20 open) and the engine agrees (a unit at (805, 2000) sees a unit 600 wu along the
gap). No naive-defender anchor on 192 is blind to the attackers' start, so decision 44's shift does nothing there; the blind caps seen on 192 come from where the survivors
stand, not from the post."""
import math
import os
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
for _p in (ROOT, ROOT / "tests" / "skilllab"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import fakes_blind as fb  # noqa: E402
from scripts.skilllab import engine as engine_mod, fight, scenes, sweep  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="the real placed scenes; set OM_LAB_SLOW=1")
VANGUARD = "Vanguard"


@pytest.fixture(scope="module")
def library():
    return engine_mod.Engine()


def play_setup(layout, play="s2_concave"):
    return sweep.default_builds(play, "play", sweep.smoke_layouts()[layout])(8, False)


@pytest.mark.parametrize("layout", ["192", "81"])
def test_the_probe_agrees_with_the_engine_on_seeded_pairs(library, layout):
    setup = play_setup(layout)
    t = setup.terrain
    rnd = random.Random(44)
    agree = {True: 0, False: 0}
    for _ in range(80):
        b = rnd.choice(t.blocks)
        px, py = rnd.uniform(b.x0 - 300, b.x1 + 300), rnd.uniform(b.y0 - 300, b.y1 + 300)
        ang, r = rnd.uniform(0, 2 * math.pi), rnd.uniform(100, 560)
        qx, qy = px + r * math.cos(ang), py + r * math.sin(ang)
        if not (0 < px < t.canvas[0] and 0 < qx < t.canvas[0] and 0 < py < t.canvas[1] and 0 < qy < t.canvas[1]):
            continue
        w = library.new_world(0)
        try:
            library.set_canvas(w, *t.canvas)
            for blk in t.blocks:
                library.block_rect(w, blk.x0, blk.y0, blk.x1, blk.y1, blk.layer_lo, blk.layer_hi)
            tid = fight._register_types(library, w, setup)[VANGUARD][0]
            a, c = library.spawn(w, tid, 0, px, py, 0), library.spawn(w, tid, 1, qx, qy, 0)
            library.step(w)
            pa, pc = library.unit_pos(w, a), library.unit_pos(w, c)
            engine_sees = c in library.seen_by_sight(w, 0, [c])
        finally:
            library.free_world(w)
        mine = scenes.sight_clear(t, pa, 0, pc, 0)
        assert mine is engine_sees, (layout, pa, pc, engine_sees)
        agree[mine] += 1
    assert agree[True] >= 10 and agree[False] >= 10, agree


@SLOW
def test_the_real_shift_and_the_real_refusal(library):
    # shift: layout 81
    feats = sweep.smoke_layouts()["81"]
    play = sweep.default_builds("s3_types_by_reach", "play", feats)(8, False)
    build = sweep.default_builds("s3_types_by_reach", "naive_defender_attacker_layer", feats)
    setup = build(8, False)
    starts = fb.starts_of(setup)
    t = setup.terrain
    pre = {}
    for g in play.groups:
        if g.side == 0:
            pre.setdefault(g.unit, []).append((g.x, g.y))
    pre = {u: (sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps)) for u, ps in pre.items()}
    blind_before = {u for u, p in pre.items() if scenes.blind_post(t, 0, p, starts)}
    assert blind_before, "fixture: layout 81 has a blind type post"
    moved = []
    for g in (g for g in setup.groups if g.side == 0):
        assert not scenes.blind_post(t, 0, (g.x, g.y), starts), (g.unit, g.x, g.y)                    # every post is sighted now
        d = math.hypot(g.x - pre[g.unit][0], g.y - pre[g.unit][1])
        assert (d > 0) == (g.unit in blind_before)                                                    # blind ones moved, clear ones stayed
        assert d <= scenes.GUARD_RADIUS + 1e-9
        moved.append(d)
    assert build.labels["prefight"] == "ok" == scenes.preflight(setup, library, naive_defender=True)
    assert 0 < build.labels["placement_shift"] <= scenes.GUARD_RADIUS and build.labels["placement_shift"] == pytest.approx(max(moved))
    # refusal: layout 78
    feats78 = sweep.smoke_layouts()["78"]
    refused = sweep.default_builds("s4_bait", "naive_defender", feats78)
    got = refused(8, False)
    assert refused.labels["prefight"] == "blind_post" and refused.labels["placement_shift"] == 0.0
    assert scenes.preflight(got, library, naive_defender=True) == "blind_post"
    assert any(scenes.blind_post(got.terrain, g.layer, (g.x, g.y), fb.starts_of(got)) for g in got.groups if g.side == 0)
