# Rule pins: R-004-07@c7c723, R-005-09@dd0832
# spec: LAB-REV2-L6 (docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, rulings 6, 10, 11, the L6 row); R-005-09, S-164, R-004-07
"""s1_slope_top through the production library: pre-flight ok on seed 11, contact, elimination, the walkers and the reach table,
and what each knob does (or is declared inert for). The engine-level controls (no scene) are green before the build.

Reading of the spec the builder must honour (measured 2026-10-14 on the lab branch, not a tolerance):
- The scene lives on a canvas where seed 11 has slopes (12000: six; 4000: none, where any climbing scene is `unroutable`).
- Walkers spawned on ground they cannot walk get unit id 0 and are counted dead without a word; the scene places every unit
  on walkable ground (test_every_unit_spawns).
- A Setup has no way today to say a unit type walks (om_roster_set_movement_kind), so all units fly in a ground era and
  OM_TP_SLOPE_UP_DIV moves nothing; test_attackers_and_holders_walk reads the movement kind from the library.
- A knob that changes nothing here must be listed in scenes_ground.INERT_KNOBS with its reason; a knob not listed must move
  the fight for at least one of the seeds tried. Both directions are tested, so the list cannot rot.
Test numbers are test drafts (2026-10-14), Westley may tighten: SEEDS."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight, formations, scenes  # noqa: E402
from scripts.skilllab.ground import scenes_ground as sg  # noqa: E402

SEEDS = (1, 2)                          # test draft (2026-10-14)
REACH = {"Vanguard": (0, 0), "Raider": (1, 1)}      # the reach table (batches.REACH_TABLE): up, down in layers
WALKING = 1
KNOBS = ("OM_TP_SIGHT_EYE_HEIGHT", "OM_TP_GROUND_FLYER_SEEN_MULT", "OM_TP_SLOPE_UP_DIV")     # the L6 row
NULL_VISION = (0.0, 0.5, 1.0)           # OM_TP_VISION_UP_1: a space-era factor; ground vision ignores it (R-005-09)


class Spy(engine.Engine):
    """Records every spawn (type, side, layer, id) and, just before the world is freed, each spawned type's reach and movement kind."""

    def __init__(self):
        super().__init__()
        self.spawned, self.read = [], {}

    def spawn(self, w, type_id, side, x, y, layer):
        u = super().spawn(w, type_id, side, x, y, layer)
        self.spawned.append((type_id, side, layer, u))
        return u

    def free_world(self, w):
        for tid in {s[0] for s in self.spawned}:
            self.read[tid] = (self.profile_reach(w, tid), self.movement_kind(w, tid))
        super().free_world(w)


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def _setup(size=16, heads=16, **settings):
    s = sg.slope_top(size)(heads, False)
    return dataclasses.replace(s, settings={**s.settings, **settings})


def _fight(lib, seed, **settings):
    return fight.fight(_setup(**settings), seed, False, engine=lib)


# ---------------------------------------------------------------- the scene runs

def test_preflight_is_ok_on_seed_11(library):
    s = _setup()
    assert s.terrain.field_seed == 11
    assert scenes.preflight(s, library) == "ok"


@pytest.mark.parametrize("seed", SEEDS)
def test_the_attacker_reaches_contact_and_the_fight_eliminates(library, seed):
    r = _fight(library, seed)
    assert r.outcome in ("side0", "side1"), "outcome %r (a cap or a draw is a lab defect to trace)" % (r.outcome,)
    assert 0 < r.first_contact_tick < r.ticks
    assert min(r.survivors) == 0 and max(r.survivors) > 0


def test_the_attackers_walk_towards_the_holders_point_before_contact(library):
    s = dataclasses.replace(_setup(), trace=True)
    spy = Spy()
    r = fight.fight(s, 1, False, engine=spy)
    side0 = {u for (_t, side, _l, u) in spy.spawned if side == 0}
    px, py = s.point

    def mean_dist(tick):
        rows = [(x, y) for (t, u, x, y, _tg, _f, alive, _layer, _utype) in r.trace if t == tick and u in side0 and alive]
        assert rows, "no living attacker at tick %d" % tick
        return sum(((x - px) ** 2 + (y - py) ** 2) ** 0.5 for x, y in rows) / len(rows)

    sampled = sorted({t for (t, *_rest) in r.trace})
    contact = min(t for t in sampled if t >= r.first_contact_tick)
    assert mean_dist(contact) < mean_dist(0)


def test_two_runs_of_one_seed_are_equal(library):
    assert _fight(library, 1) == _fight(library, 1)


# ---------------------------------------------------------------- spawns, walkers, the reach table

@pytest.mark.parametrize("heads", [8, 16, 48])
@pytest.mark.parametrize("seed", range(5))
def test_every_unit_spawns(seed, heads):
    """The replicate jitter (contract.SHIFT_MAX) moves each unit a little; none may land on ground a walker cannot stand on.
    The holder runs at 8, 16 and 48 units (ruling 4): the audit found a 48-head blob can reach unwalkable ground."""
    spy = Spy()
    fight.fight(dataclasses.replace(_setup(heads=heads), max_ticks=1), seed, False, engine=spy)
    assert len(spy.spawned) == 16 + heads and all(u != 0 for (*_x, u) in spy.spawned), [s for s in spy.spawned if s[3] == 0]


def test_attackers_and_holders_walk_and_the_reach_table_applies():
    s = _setup()
    spy = Spy()
    fight.fight(dataclasses.replace(s, max_ticks=1), 1, False, engine=spy)
    order = [g.unit for side in (0, 1) for g in s.groups if g.side == side for _ in range(g.count)]    # fight() spawns side 0 first
    assert len(order) == len(spy.spawned)
    type_of = {}
    for name, (tid, _side, _layer, _u) in zip(order, spy.spawned):
        assert type_of.setdefault(name, tid) == tid, "%s is registered as more than one type" % name
    for name, tid in type_of.items():
        reach, kind = spy.read[tid]
        assert reach == REACH[name], "%s reach %r, table says %r" % (name, reach, REACH[name])
        assert kind == WALKING, "%s moves with kind %r, not walking" % (name, kind)


# ---------------------------------------------------------------- knobs

def _results(lib, name, values):
    return {seed: [_fight(lib, seed, **{name: v}) for v in values] for seed in SEEDS}


def _moves(results):
    """True when, for some seed, two grid values give different fights."""
    return any(any(r != rs[0] for r in rs[1:]) for rs in results.values())


@pytest.mark.parametrize("name", KNOBS)
def test_each_knob_changes_the_fight_or_is_declared_inert(library, name):
    moved = _moves(_results(library, name, sg.SLOPE_TOP_KNOBS[name]))
    inert = name in sg.INERT_KNOBS
    assert moved != inert, ("%s moves the fight but INERT_KNOBS lists it" if moved else "%s changes nothing here and INERT_KNOBS does not say so") % name


def test_positive_control_the_slope_divisor_changes_the_fight(library):
    """Walkers climb slower with a larger divisor, so 1.0 and 2.0 give different fights. Reads the same comparison the null
    control uses, so a null result below means something."""
    assert _moves(_results(library, "OM_TP_SLOPE_UP_DIV", (1.0, 2.0)))


def test_null_control_the_space_vision_factor_does_not_change_a_ground_fight(library):
    """OM_TP_VISION_UP_1 is the space-era cross-layer factor; a ground era sees by R-005-09 (high ground sees down, low never
    sees up), so the fight is byte-identical across the factor."""
    assert not _moves(_results(library, "OM_TP_VISION_UP_1", NULL_VISION))


# ---------------------------------------------------------------- engine-level controls (no scene; green before the build)

def _hold(lib, w, n, x, y, layer, side, walking=True):
    van = lib.type_id("Vanguard")
    if walking:
        lib.set_movement_kind(w, van, WALKING)
    return [lib.spawn(w, van, side, x + 3.0 * i, y, layer) for i in range(n)]


def _ground_world(lib, **params):
    w = lib.new_world(0)
    lib.disable_abilities(w)
    lib.set_canvas(w, 12000.0, 12000.0)
    assert lib.terrain_generate(w, 11, 12000.0) == 0
    lib.set_era_kind(w, 1)
    for k, v in params.items():
        lib.set_param(w, lib.param_id(k), float(v))
    return w


def test_control_ground_high_sees_low_and_low_never_sees_up_whatever_the_space_factor(library):
    """Seed 11, four walkers on band 3 and four on band 2, 400 wu apart (the ground-scene smoke positions): the same at every factor."""
    for up in NULL_VISION:
        w = _ground_world(library, OM_TP_VISION_UP_1=up, OM_TP_VISION_DOWN_1=up)
        try:
            high = _hold(library, w, 4, 8150.0, 6050.0, 2, 0)
            low = _hold(library, w, 4, 8550.0, 6050.0, 1, 1)
            for _ in range(20):
                library.step(w)
            assert len(library.seen_by_sight(w, 0, low)) == 4 and library.seen_by_sight(w, 1, high) == set(), up
        finally:
            library.free_world(w)


def test_control_space_cross_layer_sight_does_follow_the_factor(library):
    """Positive control for the null control: with no terrain (a space era) the same factor decides whether the layer above is seen."""
    seen = {}
    for up in NULL_VISION:
        w = library.new_world(0)
        library.disable_abilities(w)
        library.set_param(w, library.param_id("OM_TP_VISION_UP_1"), up)
        library.set_param(w, library.param_id("OM_TP_VISION_DOWN_1"), up)
        try:
            low = _hold(library, w, 4, 500.0, 500.0, 0, 0, walking=False)
            high = _hold(library, w, 4, 900.0, 500.0, 1, 1, walking=False)
            for _ in range(20):
                library.step(w)
            seen[up] = len(library.seen_by_sight(w, 0, high))
        finally:
            library.free_world(w)
    assert (seen[0.0], seen[1.0]) == (0, 4), seen      # 0.5 sits on the range edge at 400 wu: not asserted


def test_control_eye_height_decides_what_the_high_ground_sees():
    """One walker on band 3 looking at one on band 2, 400 wu away: not seen at eye height 25 and 50, seen at 100 and 200."""
    lib = engine.Engine()
    seen = {}
    for eye in (25, 50, 100, 200):
        w = _ground_world(lib, OM_TP_SIGHT_EYE_HEIGHT=eye)
        try:
            hi = _hold(lib, w, 1, 8150.0, 6050.0, 2, 0)[0]
            lo = _hold(lib, w, 1, 8550.0, 6050.0, 1, 1)[0]
            for _ in range(20):
                lib.step(w)
            seen[eye] = lib.can_see(w, hi, lo)
        finally:
            lib.free_world(w)
    assert seen == {25: False, 50: False, 100: True, 200: True}, seen


def test_control_flyer_seen_mult_decides_how_far_a_flyer_is_seen_from():
    """A walker (sensor 700) and a flying Raider (sensor 800) 1100 wu apart on band 1: the Raider is seen at 1.5 and not at 1.25."""
    lib = engine.Engine()
    seen = {}
    for mult in (1.25, 1.5):
        w = _ground_world(lib, OM_TP_GROUND_FLYER_SEEN_MULT=mult)
        try:
            walker = _hold(lib, w, 1, 1000.0, 1000.0, 0, 0)[0]
            flyer = lib.spawn(w, lib.type_id("Raider"), 1, 2100.0, 1000.0, 1)
            for _ in range(20):
                lib.step(w)
            seen[mult] = lib.can_see(w, walker, flyer)
        finally:
            lib.free_world(w)
    assert seen == {1.25: False, 1.5: True}, seen
