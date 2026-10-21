# Rule pins: R-126-04@6335da, R-218-06@c47aed
"""Story play S-126 (E-15), VG-CONTRACT-E7: "Most of my force is out there." Moment: tick 0 of the first mission, ground era
(`--era greek_placeholder`, seed 1): the battle screen shows the smaller starting force, the structures yet to produce the rest.
Rules: R-218-06 as the spec rewrites it ("until S-211 the player starts with at least half of F, sliding down to a fifth only when
the player holds almost none of the contested strongpoints at the start and up to four fifths when they hold them all, and the
structures can produce the rest"; Westley 2026-10-11, Architect reading 2026-10-19, register row Q-218-07), R-126-04 ("a player who
holds every structure the whole mission fields at least F").

The deterministic element inventory (spec section 2) is read from `qa_state()` for ONE number only: the player's own unit count, the
number of entries of qa_state `units` whose `faction` equals qa_state `local_faction` (there is no single key for it; keys dumped on
the built tree 2026-10-19: camera, canvas, commands_sent_last_order, error_panel, focus_layer, ground3d, ground_layer, inventory,
last_command, local_faction, objects_px, plants, scale, scene, selected, settlement_lots, space3d, tick, unit_count, units,
units_in_last_command, units_px). `unit_count` counts every visible unit (the enemy is fogged at tick 0), so it is not the own count.

Premise (Architect rulings 2026-10-19, (a); TD-VG-E-33): the share is NOT read from qa_state. qa_state `inventory.structures` counts the
structures the player can see, not the contested table the rule reads (the earlier derivation of share 1.0 from it was wrong). The
premise constants below come from the C table, independently re-dumped on the tests-branch tree (push/vg-e7r-rulings, ABI 7, no E7)
for seed 1, greek_placeholder, after New Game, step 10, Mission, Deploy (set_seed 80 regions, mission_start era_kind 1): the mission is
archetype 3 in region 76; the tactical frame lists 4 structures with owners [0, -1, 3, 3]; om_structure_assign_owners(3, 4, ...)
called through ctypes on libouroboros.so (the same total om_mission_place_structures hands it) gives p 1, e 2, n 1; the player's
units at tick 0 before E7 are 330 (= F). N does not enter share = p / (p + e) = 1/3, so the earlier "n 0" only differed in an
unused number. share 1/3 is above START_KNEE 0.25 (named draft DRAFT-e7-floor-knee, Westley to confirm), so
frac = 0.5 + 0.4 * (1/3 - 0.25) = 0.5333..., and the expectation is floor(F * frac + 0.5) = floor(330 * 0.5333... + 0.5) = 176.
Red today: the player has 330 units. The csim twin is tests/csim/test_VG_E_e7.py (same formula, the fixtures there). The queue row
reads '176 of 330 at share 1/3'. Screenshot and qa_state go to docs/northstar/story_reviews/shots/<run id>/ (moment
'tick0_smaller_force'); the battle screen with the smaller force is queued for Westley with the count and F in the row."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "K"))
from _k_common import GodotGame, moment, pick_free_port, to_tactical  # noqa: E402

STORY = "S-126"
# Premise constants, provenance in the header (C table dump, om_structure_assign_owners(3, 4, ...)).
P_SEED1 = 1         # player structures in the contested table
E_SEED1 = 2         # enemy structures
N_SEED1 = 1       # neutral structures; not used by the share
F_SEED1 = 330       # own units at tick 0 before E7 (= F)
START_KNEE = 0.25   # DRAFT-e7-floor-knee
SHARE_SEED1 = P_SEED1 / (P_SEED1 + E_SEED1)


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
    expected = math.floor(F_SEED1 * frac(SHARE_SEED1) + 0.5)
    assert expected == 176, "CONTROL: the premise arithmetic moved (share %s, expected %d, header says 176)" % (SHARE_SEED1, expected)
    qa = to_tactical(game.client)
    for key in ("units", "local_faction", "tick"):
        assert key in qa, "S-126: qa_state has no `%s` (keys: %s)" % (key, sorted(qa))
    assert qa["tick"] <= 1, "premise: the play must look at tick 0, qa_state tick is %s" % qa["tick"]
    shot = moment(game.client, STORY, "tick0_smaller_force")
    count = own_units(shot)
    assert count == expected, "S-126: the player has %d units at tick 0, E7 wants floor(F * frac(share) + 0.5) = %d (F %d, p %d e %d n %d, share %s)" % (
        count, expected, F_SEED1, P_SEED1, E_SEED1, N_SEED1, SHARE_SEED1)
