"""Story play S-126 (E-15): "most of my force is out there". Moment: the battle screen at tick 0 of the first mission with the
smaller starting force. VG-CONTRACT-E7, spec docs/northstar/plans/2026-10-07-visible-game-spec.md rev 12c "Lane E1 part e", paragraph
"E7, the starting force".

Rules proved (quoted): R-218-06 "until S-211 the starting force is between a fifth and four fifths of F by the player's share of
contested strongpoints at the start, and the structures can produce the rest" (Westley 2026-10-11: "players start with at least
half-force when a match begins, if not as far down as 20% (specific number depends on the range of possible values for what the
simulation currently is at for the specific mission being played, scaled)"); R-126-04 "a player who holds every structure the whole
mission fields at least F"; R-218-03 "production is paid by the holder's economy, not free" (payment stays E2, FU-E7-production-paid).

Element inventory (deterministic, from qa_state): the own-faction unit count. The qa_state key is `unit_count` (tactical_view.gd:519,
the size of the frame's visible units; under the fog filter at tick 0 that is the player's own units only); the same number is the
count of `units` rows whose `faction` equals `local_faction`. Both are asserted and must agree.

Premises (dumped 2026-10-14 on the built tree, origin/push/vg-e7-base, by replaying the game's own pipe sequence set_seed {seed 1,
n_regions 80, features 0..7} / step 10 / mission_start {era_kind 1} / mission_begin / tactical_step 1, and by this play's own boot):
  mission frame: archetype 3, region 76, force types [26, 41, 23, 194, 33, 13] (sum F = 330); the play's qa_state at tick 1 has
  unit_count 330 (tick 1 in the boot probe, tick 6 in the play run), local_faction 0, every `units` row faction 0 (enemies hidden by fog).
  full tactical frame strongpoints/structures owners: [0, -1, 3, 3] (player 0, neutral -1, enemy faction 3) -> p 1, e 2, n 1,
  share p / (p + e) = 1/3.
Expected: start = F * clamp(START_MIN + START_SPAN * share, START_MIN, START_MIN + START_SPAN), START_MIN 0.2 and START_SPAN 0.6
(DRAFT-start-fraction, register row Q-218-07) = 330 * 0.4 = 132; start_units = floor(start + 0.5) = 132. The F, p and e above are the
seed-1 greek-placeholder mission as generated today; a change to generation changes them, and the failure line prints the count read
so a human re-dumps the premise (this is not a threshold: nobody tunes it here).

Red today: no E7, the player fields the whole force, unit_count is 330 (F), not 132. Screenshot and qa_state go to
docs/northstar/story_reviews/shots/<run id>/ (moment); the battle screen at tick 0 is queued for Westley with the count and F in the row.
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "K"))
from _k_common import GodotGame, moment, pick_free_port, to_tactical  # noqa: E402

STORY = "S-126"

# DRAFT-start-fraction (register row Q-218-07): start = F * clamp(START_MIN + START_SPAN * share, START_MIN, START_MIN + START_SPAN).
START_MIN = 0.2
START_SPAN = 0.6
# Dumped premise (see the module docstring): seed 1, greek placeholder, ground era, the first mission.
PREMISE_F = 330
PREMISE_P, PREMISE_E, PREMISE_N = 1, 2, 1


def start_units(f_units, p, e):
    share = 0.5 if p + e == 0 else p / (p + e)
    frac = min(max(START_MIN + START_SPAN * share, START_MIN), START_MIN + START_SPAN)
    return int(math.floor(f_units * frac + 0.5))


@pytest.fixture(scope="module")
def game():
    g = GodotGame(qa_port=pick_free_port(), seed=1, resolution="1920x1080", extra_args=["--era", "greek_placeholder"], renderer="vulkan")
    g.start()
    g.wait_for_port(timeout=60.0)
    yield g
    g.stop()


def test_control_the_expectation_is_a_real_cut():
    """Positive control (green today): the expected count is strictly between a fifth and four fifths of the premise F, so a
    full-force screen (330) cannot satisfy it and the assertion below can fire."""
    want = start_units(PREMISE_F, PREMISE_P, PREMISE_E)
    assert want == 132
    assert PREMISE_F * START_MIN <= want <= PREMISE_F * (START_MIN + START_SPAN) and want < PREMISE_F


def test_s_126_the_battle_opens_with_the_smaller_force(game):
    c = game.client
    to_tactical(c)
    shot = moment(c, STORY, "start_force")
    assert "unit_count" in shot and "units" in shot and "local_faction" in shot, "S-126: qa_state lacks unit_count / units / local_faction (keys: %s)" % sorted(shot)
    local = shot["local_faction"]
    own = sum(1 for u in shot["units"].values() if u.get("faction") == local)
    want = start_units(PREMISE_F, PREMISE_P, PREMISE_E)
    assert int(shot["unit_count"]) == own, "S-126: unit_count %s differs from the own-faction rows in units (%d)" % (shot["unit_count"], own)
    assert own == want, "S-126: the player fields %d units at tick %s, expected start_units %d of F %d (share %d/%d)" % (
        own, shot.get("tick"), want, PREMISE_F, PREMISE_P, PREMISE_P + PREMISE_E)
