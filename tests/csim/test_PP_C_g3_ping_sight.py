"""Phase C, step G3: a ping is a source of side sight (E-12 R-093-02 "what its pings reveal (E-01 S-162)";
E-01 R-008-04 "revealed by a ping may be fired at", R-162-05 "Given a ping that has ended, When no passive
detection applies, Then the units it revealed are hidden again"; plan decision "a spotter or a ping lets
long-range units fire").

Only what the ping DOES TO FIRING is tested here: that it opens fire to the caster's side and that the end
of the reveal closes it again. The ping's own contract (reach, cooldown, layer, alert sector, exact reveal
length) is step G7's tests, not repeated.

RED TODAY, and why: with no sight test in csrc/unit.c a Bombard fires at an unseen target with or without a
ping, so the 'before the ping, nothing fires' phase fails; om_command_ping is a generated stub (returns 0,
reveals nothing) so the 'the ping opens fire' phases would fail on it as well once the gate exists. The
fix has two parts: the gate (G3) and the ping (G7).

Settings used (pp_contract.md section 4): OM_TP_PING_REVEAL_TICKS = 200 (valid 0 to 1200; default 40). A
longer reveal than the default is used only so that the window holds several Bombard hits (they land every
60 ticks); it is a test setting, not a proposed game value. Default reach 2000, radius 500 are used as is.
"""
from test_PP_C_g3_support import BIG_HP, cohort_cycle, hp, run_and_watch, set_param, siege_scene, step

REVEAL = 200
BEFORE = 100  # quiet ticks before the ping; longer than the Bombard's first hit (tick 31)


def _ping(lib, w, caster, x, y, layer=0):
    return lib.om_command_ping(w, caster, layer, float(x), float(y))


def test_R_093_02_a_ping_lets_siege_fire_and_its_end_stops_it(lib, world_factory):
    """R-093-02, R-008-04, R-162-05: a Bombard with nobody seeing the target 1,000 wu away does nothing for
    100 ticks; it pings the target's position (1,000 wu: inside the default 2,000 reach); while the reveal
    lasts it targets and damages the target; once the reveal has ended (plus one cohort cycle to drop the
    target) no more damage lands for 200 ticks, because nothing sees it any more."""
    w = world_factory(n_regions=1)
    assert set_param(lib, w, "PING_REVEAL_TICKS", REVEAL) == 0
    bombard, supply, _ = siege_scene(lib, w, 0, spotter=False)

    hps, held = run_and_watch(lib, w, BEFORE, supply, bombard, supply)
    assert not held and min(hps) == BIG_HP, "before the ping nobody on the side sees the target: no fire"

    assert _ping(lib, w, bombard, 1000.0, 0.0) == 0, "the ping must be accepted"
    hps, held = run_and_watch(lib, w, REVEAL, supply, bombard, supply)
    assert held and min(hps) < BIG_HP, "while the ping reveals the target the side may fire at it"

    step(lib, w, cohort_cycle(lib, w))
    frozen = hp(lib, w, supply)
    hps, held = run_and_watch(lib, w, 200, supply, bombard, supply)
    assert min(hps) == frozen, "damage landed after the reveal ended"
    assert not held, "the Bombard still holds a target nobody sees after the reveal ended"


def test_R_093_02_a_ping_that_misses_reveals_nothing(lib, world_factory):
    """R-093-02: the reveal is the enemy units inside the pinged disc (radius 500). The ping lands at
    (1600, 0), 600 wu from the target and 1,600 from the caster (inside reach 2,000): the target is outside
    the disc, nobody sees it, the Bombard does not fire. Red today for the same reason as the first test."""
    w = world_factory(n_regions=1)
    assert set_param(lib, w, "PING_REVEAL_TICKS", REVEAL) == 0
    bombard, supply, _ = siege_scene(lib, w, 0, spotter=False)

    assert _ping(lib, w, bombard, 1600.0, 0.0) == 0, "the ping must be accepted (a miss is still a ping)"
    hps, held = run_and_watch(lib, w, REVEAL, supply, bombard, supply)

    assert not held and min(hps) == BIG_HP, "a target outside the pinged disc was fired at"
