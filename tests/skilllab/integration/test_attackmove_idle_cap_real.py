# Rule pins: R-087-06@2b0850
# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md::28 (point 1); docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::E1
"""LAB-REV2-E1b -- the layout-192 lone-attacker scene that capped (FINDING-attackmove-idle-cap) ends by elimination.

The scene is the one non-control cap of the L4 smoke under per-unit orders (decision 28; the overseer's cap trace, scratch scripts
under docs/northstar/research/layer_dynamics/audits/attackmove_idle_cap_2026-10-19/, committed by a records clerk; the repro knobs
are in its cap-trace report): play s3_layer_above, layout 192 of the seed-0 draw (map seed = the layout's index in the draw), 19 enemy
heads, replicate seed 2, swapped, vision 0.5, one attack-move per unit (Setup.orders_per_unit True), built exactly as the smoke builds
it (`sweep.default_builds` then `sweep.Applied`). Measured on the unfixed tree: outcome cap, 5 v 1 alive at tick 12000, first contact
at tick 315. The lone survivor of the attacking side (unit id 13, a Vanguard) is idle with no destination 128 wu short of its point,
where a defender's hit sent it after an attacker and the engine overwrote its ordered point (R-087-06 before 2026-10-19).

THIS FILE IS A CAP REGRESSION GUARD, NOT A SPEC PROOF: it shows that the one scene that capped no longer caps. The spec of the redirect
(the point of record, the three pursuit endings, the group slot, the immediate resume) is carried by
tests/csim/test_E11_S087_redirect_resumes_original_point.py. The minimal fix 'keep the issued point, let om_tac_release resume' turns
this file green and leaves five of those csim tests red (the auditor's measurement); a green here alone does not mean E1b is done.

What is here (all gated OM_LAB_SLOW=1, about a second each, like the smoke they come from):
  - the scene ends side0, side1 or draw, not cap -- RED on the unfixed tree: `cap (5, 1) at 12000`, and the message carries the idle
    line (a living attacker with no destination and no target);
  - the control: the same scene with that attacker (id 13) killed before the first step ends by elimination -- GREEN on the unfixed
    tree and after (it shows the cap is that one unit and that the scene can be finished; a cap detector that cannot pass is no detector);
  - the precondition that the scene is the traced one (head counts, id 13 on the attacking side), so a changed lab does not turn the
    control into a different scene silently. The cap tick (12000) is the lab's Setup.max_ticks and stays Westley's; it is not asserted.
Satisfiability: a throwaway build of the E1b change (the ordered point kept, the pursuit one engagement of it; not committed) turns
the first test green: the same scene ends side0 with 8 left.
"""
import ctypes
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight, sweep  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights over the real plays; set OM_LAB_SLOW=1")

PLAY, LAYOUT, HEADS, SEED, SWAP = "s3_layer_above", "192", 19, 2, True
ATTACKER = 13       # the lone survivor of the unfixed run: a side 1 Vanguard, the 13th unit spawned (the swapped fight spawns side 1 first)


class _Probe(engine.Engine):
    """The lab engine, recording each unit's faction at spawn and, when the world is freed, the living units' destination and target
    (the idle line); optionally killing one unit before the first step (the control)."""

    def __init__(self, kill=None):
        super().__init__()
        self.kill, self.faction, self.left, self._killed = kill, {}, [], False

    def spawn(self, w, type_id, faction, x, y, layer):
        u = super().spawn(w, type_id, faction, x, y, layer)
        self.faction[u] = faction
        return u

    def step(self, w):
        if self.kill is not None and not self._killed:
            fn = self._lib.om_unit_set_hp
            fn.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_double]
            fn(w, self.kill, 0.0)
            self._killed = True
        super().step(w)

    def free_world(self, w):
        self.left = [(u, self.faction[u], self.unit_pos(w, u), self.unit_destination(w, u), self.unit_target(w, u))
                     for u in sorted(self.faction) if self.unit_hp(w, u) > 0.0]
        super().free_world(w)


def _setup():
    features = sweep.smoke_layouts()[LAYOUT]
    build = sweep.default_builds(PLAY, "play", features)
    point = next(p for p in sweep.grid("vision") if p.value == 0.5)
    return sweep.Applied(build, point)(HEADS, SWAP)


def _idle_line(probe):
    idle = [(u, tuple(round(c, 1) for c in pos)) for u, side, pos, dest, target in probe.left
            if side == 1 and dest is None and target == 0]
    return f"living attackers (side 1) with no destination and no target (id, position): {idle}"


@SLOW
def test_the_traced_scene_is_the_one_that_capped():
    """Precondition: head counts (16 defenders, 19 attackers), per-unit orders, and unit 13 on the attacking side."""
    setup = _setup()
    probe = _Probe(kill=ATTACKER)
    r = fight.fight(setup, SEED, SWAP, engine=probe)
    assert r.heads == (16, HEADS) and setup.orders_per_unit is True and setup.max_ticks == 12000
    assert probe.faction[ATTACKER] == 1, f"unit {ATTACKER} is not on the attacking side: the scene is not the traced one"


@SLOW
def test_E1b_layout_192_lone_attacker_scene_ends_by_elimination_not_by_the_cap():
    """Decision 28 point 1: the attacker hit by a defender pursues it as one engagement of its attack-move and then resumes toward its
    point, so it never idles short of the point holding an attack-move that fires only at what is already in range. Red on the
    unfixed tree: the run ends `cap` with 5 v 1 alive at tick 12000 and the lone attacker idle (the idle line is in the message)."""
    probe = _Probe()
    r = fight.fight(_setup(), SEED, SWAP, engine=probe)
    assert r.outcome in ("side0", "side1", "draw"), (
        f"the fight ended {r.outcome} with {r.survivors} alive at tick {r.ticks} (first contact {r.first_contact_tick}); "
        f"{_idle_line(probe)}")


@SLOW
def test_control_the_same_scene_with_the_attacker_killed_before_it_fires_ends_by_elimination():
    """Positive control (green on the unfixed tree and after): unit 13, the attacker that idles in the capped run, is killed before
    the first step; the other 18 attackers against the 16 defenders end the fight by elimination. Shows the cap is that one unit's idling
    and that the scene can be finished."""
    probe = _Probe(kill=ATTACKER)
    r = fight.fight(_setup(), SEED, SWAP, engine=probe)
    assert r.outcome in ("side0", "side1", "draw"), (
        f"even without unit {ATTACKER} the fight ended {r.outcome} with {r.survivors} alive; {_idle_line(probe)}")
    assert r.survivors[1] <= HEADS - 1, "the control did not remove the attacker"
