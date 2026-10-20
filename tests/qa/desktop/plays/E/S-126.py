"""Story play S-126 (E-15), VG-CONTRACT-E7: "Most of my force is out there." Moment: tick 0 of the first mission, ground era
(`--era greek_placeholder`, seed 1): the battle screen shows the smaller starting force, the structures yet to produce the rest.
Rules: R-218-06 as the spec rewrites it ("until S-211 the player starts with at least half of F, sliding down to a fifth only when
the player holds almost none of the contested strongpoints at the start and up to four fifths when they hold them all, and the
structures can produce the rest"; Westley 2026-10-11, Architect reading 2026-10-19, register row Q-218-07), R-126-04 ("a player who
holds every structure the whole mission fields at least F").

The deterministic element inventory (spec section 2) is read from `qa_state()`: the own-faction unit count is NOT a single key; it is
the number of entries of qa_state `units` whose `faction` equals qa_state `local_faction` (keys dumped on the built tree 2026-10-19:
camera, canvas, commands_sent_last_order, error_panel, focus_layer, ground3d, ground_layer, inventory, last_command, local_faction,
objects_px, plants, scale, scene, selected, settlement_lots, space3d, tick, unit_count, units, units_in_last_command, units_px).
`unit_count` counts every visible unit (the enemy is fogged at tick 0, so it equals the own count here, but it is not the own count).

Premise, dumped on the built tree (origin/main de9958f0, ABI 7, no E7): seed 1, greek_placeholder, after New Game, Mission, Deploy:
tick 1, local_faction 0, 330 own units (all of F: nothing is cut yet), inventory.structures 1, inventory.hud.reinforcements 1 (the one
structure is the player's), so p 1, e 0, n 0, share 1.0. The play asserts those inputs first, so a changed premise stops it as a
premise failure and not as an E7 failure; the expectation is then floor(F * frac(share) + 0.5) with F = LIVE_F (the unit count before
E7), share 1.0, frac(1.0) = 0.8 (START_KNEE 0.25 is the named draft DRAFT-e7-floor-knee, Westley to confirm): 330 * 0.8 = 264.
Red today: the player has 330 units. The csim twin is tests/csim/test_VG_E_e7.py (same formula, the fixtures there). Screenshot and
qa_state go to docs/northstar/story_reviews/shots/<run id>/ (moment 'tick0_smaller_force'); the battle screen with the smaller force
is queued for Westley with the count and F in the row."""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "K"))
from _k_common import GodotGame, moment, pick_free_port, to_tactical  # noqa: E402

STORY = "S-126"
LIVE_F = 330        # own units at tick 0 of the seed-1 greek_placeholder mission before E7 (premise, dumped; see the header)
START_KNEE = 0.25   # DRAFT-e7-floor-knee


def frac(share):
    share = min(max(share, 0.0), 1.0)
    return 0.2 + 1.2 * share if share <= START_KNEE else 0.5 + 0.4 * (share - START_KNEE)


def own_units(qa):
    """The own-faction unit count: entries of qa_state `units` whose faction is qa_state `local_faction`."""
    return sum(1 for u in qa["units"].values() if int(u["faction"]) == int(qa["local_faction"]))


@pytest.fixture(scope="module")
def game():
    g = GodotGame(qa_port=pick_free_port(), seed=1, resolution="1920x1080", extra_args=["--era", "greek_placeholder"], renderer="vulkan")
    g.start()
    g.wait_for_port(timeout=60.0)
    yield g
    g.stop()


def test_s_126_the_starting_force_is_a_fraction_of_f(game):
    assert own_units({"units": {"1": {"faction": 0}, "2": {"faction": 1}}, "local_faction": 0}) == 1, "CONTROL: the own-count reader missed the faction filter"
    qa = to_tactical(game.client)
    for key in ("units", "local_faction", "inventory", "tick"):
        assert key in qa, "S-126: qa_state has no `%s` (keys: %s)" % (key, sorted(qa))
    inv = qa["inventory"]
    total, own_structures = int(inv["structures"]), int(inv["hud"]["reinforcements"])
    assert qa["tick"] <= 1, "premise: the play must look at tick 0, qa_state tick is %s" % qa["tick"]
    assert (total, own_structures) == (1, 1), "premise: seed 1 greek_placeholder fields one structure, the player's (got %s total, %s own)" % (total, own_structures)
    share = own_structures / total  # n = 0 and e = 0 here: share = p / (p + e) = 1.0
    expected = math.floor(LIVE_F * frac(share) + 0.5)
    shot = moment(game.client, STORY, "tick0_smaller_force")
    count = own_units(shot)
    assert count == expected, "S-126: the player has %d units at tick 0, E7 wants floor(F * frac(share) + 0.5) = %d (F %d, share %s)" % (count, expected, LIVE_F, share)
