"""Position plays through the timeline: bait, ambush and fall back, each an unconfirmed draft (batch3_spec.md).
Draft numbers (turn or spring tick 100, bait share 0.25) are arguments, none confirmed."""
import dataclasses
import statistics

from scripts.skilllab import skills, timeline
from scripts.skilllab.asym import Side, asym_play
from scripts.skilllab.contract import Step
from scripts.skilllab.formations import place

TICK = 100
SHARE = 0.25


def _check(size, tick):
    if size < 1:
        raise ValueError("size must be >= 1")
    if tick < 1:
        raise ValueError("tick must be >= 1")


def _play(name, size, rewrite):
    base = asym_play(size, Side("blob"), Side("blob"))

    def build(enemy_heads, swap):
        setup = rewrite(base(enemy_heads, swap))
        timeline.validate(setup)
        return setup
    build.labels = {**base.labels, "play_side0": name, "status_side0": skills.DRAFT}
    return build


def bait_play(size, tick=TICK, share=SHARE):
    _check(size, tick)
    if size < 2:
        raise ValueError("bait needs at least 2 units")
    if not 0 < share < 1:
        raise ValueError("share must be inside (0, 1)")
    k = max(1, round(size * share))

    def rewrite(setup):
        g = setup.groups[0]
        pts = sorted(place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params), key=lambda p: (-p[0], p[1]))
        bait, main = pts[:k], pts[k:]
        make = lambda pts, order: dataclasses.replace(g, count=len(pts), formation="points", x=0.0, y=0.0,
                                                      order=order, params={"points": pts})
        centre = (statistics.fmean(p[0] for p in main), statistics.fmean(p[1] for p in main))
        return dataclasses.replace(
            setup, groups=(make(bait, "attack_move"), make(main, "idle")) + setup.groups[1:],
            timeline=(Step(0, ("tick", tick), "move", goal=centre), Step(1, ("tick", tick), "attack_move")))
    return _play("bait", size, rewrite)


def ambush_play(size, tick=TICK):
    _check(size, tick)

    def rewrite(setup):
        groups = (dataclasses.replace(setup.groups[0], order="idle"),) + setup.groups[1:]
        return dataclasses.replace(setup, groups=groups, timeline=(Step(0, ("tick", tick), "attack_move"),))
    return _play("ambush", size, rewrite)


def fall_back_play(size, tick=TICK):
    _check(size, tick)

    def rewrite(setup):
        g = setup.groups[0]
        return dataclasses.replace(setup, timeline=(Step(0, ("tick", tick), "move", goal=(g.x, g.y)),
                                                    Step(0, ("tick", 2 * tick), "attack_move")))
    return _play("fall_back", size, rewrite)
