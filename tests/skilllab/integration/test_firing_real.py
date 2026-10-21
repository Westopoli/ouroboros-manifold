# Rule pins: R-005-05@96a3b1, R-164-01@511d57
# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::L1; harness-spec AC-24 (hand-built count)
"""The rev 2 count of LAB-REV2-L1 against the real engine, hand-built geometry, no fight loop.

This file imports neither `fight` nor `plays`: it needs only L1 (firing.py and the engine bindings), so it can be green
before L2 exists. The fight-level cases (the old AC-24 series through fight.fight, the 16 v 16 control read on the
fight's own series, the parity run over fight.fight) live in test_fight_firing_real.py, owned by L2.

Expected numbers come from the geometry and the engine's own tables, never from firing.py. Each case also reads what
the engine DID (hit points after 60 to 100 ticks), so a count that disagrees with the fight is caught here.
"""
import ctypes
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, firing  # noqa: E402

UNIT = "Vanguard"
BASE_X, BASE_Y = 400.0, 400.0   # keeps every point positive


@pytest.fixture(scope="module")
def real_engine():
    return engine.Engine()


@pytest.fixture(scope="module")
def reach(real_engine):
    w = real_engine.new_world(0)
    try:
        stats = real_engine.type_stats(w, real_engine.type_id(UNIT))
    finally:
        real_engine.free_world(w)
    return float(stats["attack_range"])


ARC_OFF = 360.0
CATMULT_NAMES = ["OM_TP_CATMULT_%s_%s" % (a, d) for a in ("LINE", "SIEGE", "STRIKE") for d in ("LINE", "SIEGE", "STRIKE")]
VISION_PARAMS = ("OM_TP_VISION_UP_1", "OM_TP_VISION_DOWN_1")
SPACING = 30.0
FIGHT_TICKS = 60


@contextmanager
def world(lib, catmult=False):
    w = lib.new_world(0)
    lib.disable_abilities(w)
    try:
        if catmult:                      # nine distinct multipliers: a wrong attacker/target pair can never match
            for i, name in enumerate(CATMULT_NAMES):
                lib.set_param(w, lib.param_id(name), 0.5 + 0.1 * i)
        yield w
    finally:
        lib.free_world(w)


def cat_mult(lib, w, attacker_cat, target_cat):
    """The engine's own table, called directly so the oracle does not depend on the wrapper under test."""
    fn = lib._lib.om_tactical_category_multiplier
    fn.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    fn.restype = ctypes.c_double
    return fn(w, attacker_cat, target_cat)


def category(lib, w, name):
    return lib.type_stats(w, lib.type_id(name))["category"]


def grid(lib, w, name, faction, x, y, layer, n=16):
    """n units of one type in a 4-wide grid of 30 wu spacing from (x, y); returns the ids."""
    t = lib.type_id(name)
    return [lib.spawn(w, t, faction, x + SPACING * (i % 4), y + SPACING * (i // 4), layer) for i in range(n)]


def hp_total(lib, w, ids):
    return sum(lib.unit_hp(w, u) for u in ids)


def damage_done(lib, w, ids, ticks=FIGHT_TICKS):
    before = hp_total(lib, w, ids)
    for _ in range(ticks):
        lib.step(w)
    return before - hp_total(lib, w, ids)


# ---------------------------------------------------------------- AC 24 hand-built case, read through count_able
# Side 0: three units in a row A, B, C along +x; side 1: one enemy E behind A on the -x side. Distances from E, as
# fractions of the Vanguard attack range R: A 0.3, B 0.7, C 1.2 (R is read from the engine: no magic position).

def _ac24_units(lib, w, reach):
    t = lib.type_id(UNIT)
    a = [lib.spawn(w, t, 0, BASE_X + f * reach, BASE_Y, 0) for f in (0.0, 0.4, 0.9)]
    e = lib.spawn(w, t, 1, BASE_X - 0.3 * reach, BASE_Y, 0)
    return a, e


# ---------------------------------------------------------------- the type weight (ruling 5)



# ---------------------------------------------------------------- states (the code is the first failing gate)

def _layered(lib, w, reach, vision):
    """16 v 16 Vanguards, side 0 on layer 1 and side 1 on layer 0, 150 wu apart in x (the cross-layer case above)."""
    lib.set_reach(w, lib.type_id(UNIT), *reach)
    for name in VISION_PARAMS:
        lib.set_param(w, lib.param_id(name), vision)
    return grid(lib, w, UNIT, 0, 1000.0, 1000.0, 1), grid(lib, w, UNIT, 1, 1150.0, 1000.0, 0)


# ---------------------------------------------------------------- parity (goes live when E0 is on main)

SAMPLE_EVERY = 5      # Setup.sample_every: the lab checks parity on every sampled tick
MAX_PARITY_TICKS = 300


def _e0_on_main(lib):
    """E0 adds OM_TP_FIRING_ARC_DEG to the header (parameter enum) and om_combat_can_engage to the library."""
    return "OM_TP_FIRING_ARC_DEG" in engine._load_param_ids() and hasattr(lib._lib, "om_combat_can_engage")


class _ParitySpy(engine.Engine):
    """Real Engine whose step() checks firing.parity on every sampled tick (every SAMPLE_EVERY steps, tick 0 included)
    over the units this wrapper spawned, and keeps every unit the check names. Needs no fight loop: see the scenes."""

    def __init__(self):
        super().__init__()
        self.parity_differences = []
        self.parity_checks = 0
        self._n = 0

    def step(self, w):
        if self._n % SAMPLE_EVERY == 0:
            sides = [[u for u in self._own.get((w.value, f), []) if self.unit_alive(w, u)] for f in (0, 1)]
            if sides[0] and sides[1]:
                self.parity_checks += 1
                self.parity_differences += [(self._n, u) for u in firing.parity(self, w, sides[0], sides[1], ARC_OFF)]
        self._n += 1
        super().step(w)


def _parity_scene(spy, w, scene):
    """The three controls, inline (no plays.py): mirror 16 v 16, numbers 16 v 8, and a cross-layer fog case (side 0 one
    layer up, reach one each way, vision 0.5) so the reach, sight and range gates all run. Every unit attack-moves at the
    enemy's start centroid; OM_TP_TARGET_BY_SIGHT is 1, the only setting tested (overseer default)."""
    spy.disable_abilities(w)
    spy.set_param(w, spy.param_id("OM_TP_TARGET_BY_SIGHT"), 1.0)
    n1 = 8 if scene == "numbers" else 16
    layer0 = 1 if scene == "fog_layers" else 0
    if scene == "fog_layers":
        spy.set_reach(w, spy.type_id(UNIT), 1, 1)
    s0 = grid(spy, w, UNIT, 0, 1000.0, 1000.0, layer0)
    s1 = grid(spy, w, UNIT, 1, 1500.0, 1000.0, 0, n=n1)
    for u in s0:
        spy.order_attack_move(w, [u], 1545.0, 1045.0)
    for u in s1:
        spy.order_attack_move(w, [u], 1045.0, 1045.0)
    return s0, s1


@pytest.mark.parametrize("scene", ["mirror", "numbers", "fog_layers"])
def test_parity_is_empty_on_every_sampled_tick_of_the_controls(scene):
    """Spec L1 row (after E0): the composed set equals the can_engage set on every sampled tick (every 5th) of the
    controls, fog on; a non-empty list is a defect. The third control is the cross-layer fog case, not the planted
    damage scene (that one differs only in a damage multiplier, which no gate reads). Skipped until E0 is on main; with
    the E0 stub (can_engage = -1) it passes trivially and E2 makes it bite."""
    spy = _ParitySpy()
    if not _e0_on_main(spy):
        pytest.skip("E0 not on main")
    w = spy.new_world(0)
    try:
        s0, s1 = _parity_scene(spy, w, scene)
        for _ in range(MAX_PARITY_TICKS):
            if not any(spy.unit_alive(w, u) for u in s0) or not any(spy.unit_alive(w, u) for u in s1):
                break
            spy.step(w)
    finally:
        spy.free_world(w)
    assert spy.parity_checks >= 10
    assert spy.parity_differences == []
