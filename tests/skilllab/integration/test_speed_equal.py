# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::S (speed); Architect ruling 2026-10-21 for LAB-REV2-SPEED (Westley may veto)
"""LAB-REV2-SPEED stage one: the rev 2 lab gets faster without changing a byte of what it says.

The builder owns scripts/skilllab/firing.py and engine.py; this file only pins what they must keep and what they must reach.

  (a) EQUALITY. The whole FightResult of a fight run with the live firing.py equals the same fight run with
      tests/skilllab/ref_firing_rev2.py (firing.py frozen at 30f827b3), over ten setups (the three controls, arc 120, arc 30, terrain
      block, mixed types, layer offset, states with trace, re-engage). fight.py is not touched: the reference is swapped in by patching
      the three names fight.py imports from firing (count_able, count_weighted, states).
  (b) The three goldens (tests/skilllab/golden_hashes.json, tests/csim/data/baseline_hashes_pre_g3.json,
      tests/csim/parity/baseline/baseline_hashes.json) are not edited here; test_cross_machine.py and test_trace_real.py keep proving them.
  (c) CPU TIME. ratio = time.process_time spent by the live code / by the frozen reference, the two interleaved fight by fight in one
      process; wall time is printed beside it. DRAFT_LAB_SPEED_RATIO_1 is a DRAFT; the mark is Westley's.
  (d) THE EPOCH CONTRACT the builder satisfies (names are pinned here):
        Engine.epoch                    an int attribute. It rises on EVERY state-changing Engine method (MUTATORS below) and does not
                                        move on a read-only one (READ_ONLY below). A public Engine method in neither set fails the
                                        enumeration test, so a new or missed mutator cannot slip through.
        Engine.__new__ + _bind objects  (tests/skilllab/test_firing.py make_engine) need no new state set in __init__: epoch must be
                                        readable and bumpable on an object that only ran _bind (class attribute or getattr default).
        firing.count_able / count_weighted / states
                                        share ONE sample build per (engine, world, epoch, units, arc). The cache applies only when
                                        engine.epoch is an int; an engine without it (every fake) is never cached. The key holds the
                                        epoch, never call arguments alone.

RED today (before the builder): the ratio test, the epoch tests, and the one-build test. Everything that compares the live code against
the reference, and every positive control, is green because the code is still identical to the reference.

POSITIVE CONTROLS: a planted CPU slowdown must fail the ratio check (and a sleep must not move it: the measure is CPU); the reference run
against itself passes the equality check; mutants of a copy of the reference (a tie-break in record, the nearest-first order, the
current-target shortcut) must fail it; an argument-keyed cache wrapper (the stale design the ruling forbids) must fail the staleness check.
"""
import contextlib
import ctypes
import dataclasses
import inspect
import math
import sys
import time
import types
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
HERE = str(Path(__file__).resolve().parents[1])
for _p in (str(ROOT), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ref_firing_rev2 as ref  # noqa: E402
from scripts.skilllab import engine as engine_mod, fight, firing, plays  # noqa: E402
from scripts.skilllab.contract import Block, Cover, Group, Setup, Terrain  # noqa: E402

# DRAFT, Westley's number. Stage one (firing.py and engine.py) only; measured floor: with firing stubbed a 16v16 fight costs
# 0.17 s CPU against 0.45 s today, so the ratio floor is about 0.38 and a prototype of the epoch cache reached about 0.71.
# The 0.5 ratio (DRAFT-lab-speed-ratio) and the 30 s mark belong to the combined stages; SPEED-2 tests against the same frozen reference.
DRAFT_LAB_SPEED_RATIO_1 = 0.75  # DRAFT: process_time(live firing) / process_time(frozen reference) must not exceed it. The mark is Westley's.
RATIO_ENEMIES = range(12, 25)   # blob_play(16) against 12 to 24 enemies, both orders: 26 fights
RATIO_SWAPS = (False, True)
FIRING_FUNCTIONS = ("count_able", "count_weighted", "states")


@pytest.fixture(scope="module")
def library():
    return engine_mod.Engine()


# ---- helpers -------------------------------------------------------------------------------------------------------------------------

@contextlib.contextmanager
def firing_of(module):
    """fight.py calls the three names it imported from firing; point them at `module` for the duration (fight.py itself is untouched)."""
    saved = {n: getattr(fight, n) for n in FIRING_FUNCTIONS}
    try:
        for n in FIRING_FUNCTIONS:
            setattr(fight, n, getattr(module, n))
        yield module
    finally:
        for n, f in saved.items():
            setattr(fight, n, f)


def fight_with(module, setup, seed, swap, eng):
    with firing_of(module):
        return fight.fight(setup, seed, swap, eng)


def assert_results_equal(a, b, what="fight"):
    """The whole FightResult, field by field first so a failure names the field, then as a dataclass."""
    for f in dataclasses.fields(a):
        assert getattr(a, f.name) == getattr(b, f.name), "%s: FightResult.%s differs" % (what, f.name)
    assert a == b, what


def load_variant(name, transform=None):
    """A module built from the reference source, optionally with the source rewritten by `transform` (a mutant)."""
    src = Path(ref.__file__).read_text()
    if transform is not None:
        new = transform(src)
        assert new != src, "the mutation did not change the source (the control would be vacuous)"
        src = new
    mod = types.ModuleType(name)
    exec(compile(src, name, "exec"), mod.__dict__)
    return mod


def blob(side, unit, n, x, y, facing, layer=0, order="attack_move"):
    return Group(side=side, unit=unit, count=n, formation="blob", x=x, y=y, facing_deg=facing, layer=layer, order=order,
                 params={"radius": 80 + 12 * math.sqrt(n)})


def burn(seconds):
    """Spend CPU (not sleep) for `seconds` of process time."""
    end = time.process_time() + seconds
    while time.process_time() < end:
        pass


# ---- the setups: (name, setup, seed, swap, evidence that the mechanism under test ran) -------------------------------------------------

def _shifted(setup, dx, dy, **over):
    groups = tuple(dataclasses.replace(g, x=g.x + dx, y=g.y + dy) for g in setup.groups)
    return dataclasses.replace(setup, groups=groups, point=(setup.point[0] + dx, setup.point[1] + dy), **over)


VANGUARD_REACH_1 = {"VanguardR": {"base": "Vanguard", "scale": {}, "set": {}, "reach": (1, 1)}}


def _codes(res):
    return {c for _, _, c in res.states}


def _setup_cases():
    mirror = plays.blob_play(16)(16, False)
    cases = [
        ("mirror 16v16", mirror, 0, False, lambda r: 0 in _codes(r)),
        ("numbers 16v8", plays.blob_play(16)(8, False), 1, False, lambda r: r.outcome == "side0"),
        ("planted damage 16v16", plays.damage_play(16)(16, True), 3, True, lambda r: r.outcome in ("side0", "side1")),
        ("arc 120", dataclasses.replace(mirror, firing_arc_deg=120.0, max_ticks=1500), 0, False, lambda r: len(r.firing) > 100),
        ("arc 30 (gate 4 fires)", dataclasses.replace(mirror, firing_arc_deg=30.0, max_ticks=1500), 0, False, lambda r: 4 in _codes(r)),
        ("terrain block and cover (gate 5)",
         _shifted(mirror, 1000.0, 1000.0, terrain=Terrain(canvas=(2000.0, 2000.0), blocks=(Block(985.0, 1060.0, 1015.0, 1140.0, 0, 4),),
                                                           covers=(Cover(1000.0, 1000.0, 60.0, 3),))),
         0, False, lambda r: 5 in _codes(r)),
        ("mixed types and categories",
         Setup(groups=(blob(0, "Vanguard", 8, -400, 0, 0), blob(0, "Bombard", 4, -550, 0, 0), blob(0, "Raider", 4, -300, 100, 0),
                       blob(1, "Warden", 6, 400, 0, 180), blob(1, "Interceptor", 6, 500, 0, 180), blob(1, "Vanguard", 4, 300, -100, 180)),
               unit_types={}, point=(0.0, 0.0), max_ticks=3000),
         0, False, lambda r: tuple(r.weighted_unit_seconds) != tuple(r.firing_unit_seconds)),
        ("layer offset (gates 1 and 3)",
         Setup(groups=(blob(0, "VanguardR", 16, -400, 0, 0), blob(1, "Vanguard", 16, 400, 0, 180, layer=1)),
               unit_types=VANGUARD_REACH_1, point=(0.0, 0.0), max_ticks=1500),
         0, False, lambda r: {1, 3} <= _codes(r)),
        ("states with trace", dataclasses.replace(plays.blob_play(16)(10, False), trace=True), 2, False,
         lambda r: bool(r.trace) and bool(r.states)),
        ("attack-move group, re-engage trigger", dataclasses.replace(plays.blob_play(16)(16, True), orders_per_unit=False), 0, True,
         lambda r: sum(r.reengage) >= 1),
    ]
    return [(n, dataclasses.replace(s, states=True), seed, swap, ev) for n, s, seed, swap, ev in cases]


SETUP_CASES = _setup_cases()
SETUP_IDS = [c[0] for c in SETUP_CASES]


# ---- (a) equality against the frozen reference ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("name,setup,seed,swap,evidence", SETUP_CASES, ids=SETUP_IDS)
def test_live_firing_gives_the_same_whole_fightresult_as_the_frozen_reference(library, name, setup, seed, swap, evidence):
    """Acceptance (a): every FightResult field (firing, weighted, states, trace, reengage, blind_cap, ...) equals the reference run, and
    the setup really exercised its mechanism (the evidence lambda), so the equality is not between two empty results."""
    expected = fight_with(ref, setup, seed, swap, library)
    got = fight.fight(setup, seed, swap, library)
    assert evidence(expected), "%s: the setup does not exercise its mechanism (outcome %s, codes %s)" % (name, expected.outcome, sorted(_codes(expected)))
    assert expected.firing and expected.states
    assert_results_equal(got, expected, name)


def test_the_seam_swap_really_reaches_fight():
    """Guard on the helper: inside firing_of the names fight calls are the reference's, outside they are the live ones."""
    with firing_of(ref):
        assert fight.count_able is ref.count_able and fight.states is ref.states
    assert fight.count_able is firing.count_able and fight.count_weighted is firing.count_weighted and fight.states is firing.states


def test_control_reference_against_itself_passes_the_equality_check(library):
    """Positive control (iii): the same fight twice on the unchanged reference is equal; the check is not always failing."""
    name, setup, seed, swap, _ = SETUP_CASES[0]
    assert_results_equal(fight_with(ref, setup, seed, swap, library), fight_with(ref, setup, seed, swap, library), name)


def _reverse_order(src):
    return src.replace("(enemies[v][1] - y) ** 2, v)):", "(enemies[v][1] - y) ** 2, v), reverse=True):")


def _no_current_target_shortcut(src):
    return src.replace("if t in enemies and self.code(side, u, t) == 0:", "if False:")


@pytest.mark.parametrize("label,transform", [("nearest-first order reversed", _reverse_order),
                                              ("current-target shortcut removed", _no_current_target_shortcut)])
def test_control_a_mutant_of_record_fails_the_equality_check(library, label, transform):
    """Positive control (ii), whole-fight form: a copy of the reference with record's order or shortcut changed must make a mixed-type
    fight differ from the reference in some FightResult field."""
    name, setup, seed, swap, _ = next(c for c in SETUP_CASES if c[0].startswith("mixed"))
    mutant = load_variant("mutant_" + label.split()[0], transform)
    with pytest.raises(AssertionError):
        assert_results_equal(fight_with(mutant, setup, seed, swap, library), fight_with(ref, setup, seed, swap, library), label)


# ---- a fake engine for the logic tests (no C library) -------------------------------------------------------------------------------

W = ctypes.c_void_p(7)


class FakeSim:
    """The surface firing._Sample reads. units: id -> {pos, layer, type, alive, facing, target}. `calls` counts every query by name."""

    def __init__(self, units, blocked=(), by_world=None):
        self.units = units
        self.by_world = by_world or {}    # world handle value -> units dict: answers for that handle; any other handle reads `units`
        self.blocked = set(blocked)
        self.calls = Counter()

    def _u(self, w):
        return self.by_world.get(w.value, self.units)

    def unit_alive(self, w, u):
        self.calls["unit_alive"] += 1
        return self._u(w)[u]["alive"]

    def unit_pos(self, w, u):
        self.calls["unit_pos"] += 1
        return self._u(w)[u]["pos"]

    def unit_layer(self, w, u):
        self.calls["unit_layer"] += 1
        return self._u(w)[u]["layer"]

    def unit_type(self, w, u):
        self.calls["unit_type"] += 1
        return self._u(w)[u]["type"]

    def unit_target(self, w, u):
        self.calls["unit_target"] += 1
        return self._u(w)[u].get("target", 0)

    def unit_facing(self, w, u):
        self.calls["unit_facing"] += 1
        return self._u(w)[u].get("facing", 0.0)

    def type_stats(self, w, t):
        self.calls["type_stats"] += 1
        return {"attack_range": 300.0, "category": t % 3}

    def profile_reach(self, w, t):
        return (1, 1)

    def visible_enemies(self, w, side, ids):
        self.calls["visible_enemies"] += 1
        return set(ids)

    def get_param(self, w, p):
        return 1.0

    def param_id(self, name):
        return name

    def can_engage(self, w, a, b):
        return -1

    def can_shoot(self, w, a, b):
        self.calls["can_shoot"] += 1
        return (a, b) not in self.blocked

    def category_multiplier(self, w, a, b):
        return 1.0 + 0.1 * a + 0.01 * b


class EpochSim(FakeSim):
    """A fake that exposes the epoch; `touch()` is what a mutator does."""
    epoch = 0

    def touch(self):
        self.epoch += 1


def _units():
    out = {}
    for i in range(3):
        out[1 + i] = {"pos": (0.0 + 20 * i, 0.0), "layer": 0, "type": i, "alive": True}
        out[100 + i] = {"pos": (150.0 + 20 * i, 10.0), "layer": 0, "type": i + 1, "alive": True}
    return out


SIDE0, SIDE1 = [1, 2, 3], [100, 101, 102]


def _all_answers(module, eng, arc=360.0, s0=SIDE0, s1=SIDE1, w=W):
    return (module.count_able(eng, w, s0, s1, arc), module.count_weighted(eng, w, s0, s1, arc), module.states(eng, w, s0, s1, arc))


def _tie_units():
    """Unit 1 against two enemies at the same distance: id 5 (category 1) and id 9 (category 2)."""
    return {1: {"pos": (0.0, 0.0), "layer": 0, "type": 0, "alive": True},
            5: {"pos": (100.0, 0.0), "layer": 0, "type": 1, "alive": True},
            9: {"pos": (-100.0, 0.0), "layer": 0, "type": 2, "alive": True}}


def test_tie_break_by_id_is_pinned_on_the_live_code_and_the_reference():
    """Total order of record: equal squared distances break by the lower id. Two enemies at the same distance with different categories:
    the weight must come from the lower id's category (1), not the higher's (2)."""
    expected = FakeSim(_tie_units()).category_multiplier(W, 0, 1)
    assert expected != FakeSim(_tie_units()).category_multiplier(W, 0, 2)
    for module in (ref, firing):
        assert module.count_weighted(FakeSim(_tie_units()), W, [1], [5, 9], 360.0)[0] == expected, module.__name__


def test_control_a_tie_break_mutant_fails_the_tie_pin():
    """Positive control (ii), unit form: with the id tie-break negated, the pin above sees the higher id's category and fails."""
    mutant = load_variant("mutant_tie", lambda s: s.replace("(enemies[v][1] - y) ** 2, v))", "(enemies[v][1] - y) ** 2, -v))"))
    wrong = mutant.count_weighted(FakeSim(_tie_units()), W, [1], [5, 9], 360.0)[0]
    assert wrong != FakeSim(_tie_units()).category_multiplier(W, 0, 1)


# ---- the cache: one sample build per epoch, never stale ------------------------------------------------------------------------------

def test_an_engine_without_epoch_is_never_cached():
    """An engine that does not expose epoch is queried afresh by every call, and a change of its state shows at once."""
    eng = FakeSim(_units())
    assert not hasattr(eng, "epoch")
    first = _all_answers(firing, eng)
    one_round = eng.calls["unit_pos"]
    _all_answers(firing, eng)
    assert eng.calls["unit_pos"] == 2 * one_round, "a second round of calls must query the engine again"
    eng.units[100]["alive"] = False
    after = _all_answers(firing, eng)
    assert after == _all_answers(ref, eng) and after != first


def test_same_epoch_the_counts_and_states_build_one_sample():
    """RED until the builder: count_able, count_weighted and states at one epoch query each unit once (one sample build), asking the
    engine no more than one count does, and answer exactly as the uncached reference does."""
    eng, twin = EpochSim(_units()), FakeSim(_units())
    got = _all_answers(firing, eng)
    assert got == _all_answers(ref, twin)
    n_units = len(SIDE0) + len(SIDE1)
    assert eng.calls["unit_pos"] <= n_units, "unit_pos asked %d times for %d units: the sample was built more than once" % (
        eng.calls["unit_pos"], n_units)
    single = EpochSim(_units())
    firing.count_able(single, W, SIDE0, SIDE1, 360.0)
    assert eng.calls["can_shoot"] <= single.calls["can_shoot"], "three calls asked can_shoot %d times, one count asks %d" % (
        eng.calls["can_shoot"], single.calls["can_shoot"])


def _stale_check(module):
    """The staleness check: after a state change and an epoch bump, the module's answers equal the uncached reference's on the new state."""
    eng, twin = EpochSim(_units()), FakeSim(_units())
    assert _all_answers(module, eng) == _all_answers(ref, twin)
    for sim in (eng, twin):
        sim.units[1]["alive"] = False
        sim.units[101]["pos"] = (900.0, 0.0)
        sim.blocked.add((2, 100))
    eng.touch()
    assert _all_answers(module, eng) == _all_answers(ref, twin), "answers after a mutation + epoch bump are stale"


def test_a_state_change_with_an_epoch_bump_is_seen():
    """Guard: the cache is keyed on the epoch, so a bump shows the new state (green today, must stay green)."""
    _stale_check(firing)


def test_control_an_argument_keyed_cache_fails_the_staleness_check():
    """Positive control: a memo keyed on call arguments only (the design the ruling forbids) answers stale after the state changes."""
    memo = {}

    def keyed(fn):
        def wrapped(engine, w, u0, u1, arc):
            key = (fn.__name__, id(engine), w.value, tuple(u0), tuple(u1), arc)
            if key not in memo:
                memo[key] = fn(engine, w, u0, u1, arc)
            return memo[key]
        wrapped.__name__ = fn.__name__
        return wrapped

    stale = types.SimpleNamespace(**{n: keyed(getattr(ref, n)) for n in FIRING_FUNCTIONS})
    with pytest.raises(AssertionError):
        _stale_check(stale)


def test_the_cache_key_holds_the_arguments_the_world_and_the_engine():
    """Same epoch (0) everywhere, yet different arcs, unit lists, worlds and engines each get their own answer."""
    units = _units()
    units[2]["facing"] = math.pi          # faces away from the enemy: outside a narrow arc
    eng = EpochSim(units)
    wide = _all_answers(firing, eng, 360.0)
    sub = _all_answers(firing, eng, 360.0, s0=[1, 2], s1=SIDE1)       # right after `wide`: same arc, only the unit lists differ
    narrow = _all_answers(firing, eng, 30.0)
    assert sub == _all_answers(ref, FakeSim(units), 360.0, s0=[1, 2], s1=SIDE1) and sub != wide, "the unit lists must reach the answer"
    assert narrow == _all_answers(ref, FakeSim(units), 30.0) and wide == _all_answers(ref, FakeSim(units), 360.0)
    assert narrow != wide, "the arc must reach the answer"
    gone = _units()
    for u in SIDE1:
        gone[u]["alive"] = False
    both = EpochSim(units, by_world={8: gone})          # the answers depend on the world handle: handle 8 sees the enemies dead
    w8 = ctypes.c_void_p(8)
    first7 = _all_answers(firing, both)                 # handle 7, then handle 8 at the same epoch, same ids, same arc
    assert first7 == wide
    got8 = _all_answers(firing, both, w=w8)
    assert got8 == _all_answers(ref, FakeSim(units, by_world={8: gone}), w=w8) and got8 != first7, "the world handle must reach the answer"
    dead = _units()
    for u in SIDE1:
        dead[u]["alive"] = False
    other = EpochSim(dead)                # a second engine, also at epoch 0, same world handle
    got = _all_answers(firing, other)
    assert got == _all_answers(ref, FakeSim(dead)) and got != wide


def test_an_engine_whose_epoch_is_not_an_int_is_never_cached():
    """Reading 'exposes an integer attribute epoch' strictly: a proxy or mock whose .epoch is some object must not be cached (it would
    never move). Green today."""
    class Odd(FakeSim):
        epoch = object()

    eng = Odd(_units())
    _all_answers(firing, eng)
    first = eng.calls["unit_pos"]
    eng.units[100]["alive"] = False
    assert _all_answers(firing, eng) == _all_answers(ref, FakeSim(eng.units))
    assert eng.calls["unit_pos"] > first


# ---- the epoch contract on Engine ------------------------------------------------------------------------------------------------------

READ_ONLY = {"type_id", "type_stats", "profile_reach", "visible_enemies", "seen_by_sight", "can_see", "unit_hp", "unit_pos",
             "unit_destination", "unit_layer", "unit_alive", "unit_target", "unit_facing", "unit_type", "transition_progress",
             "category_multiplier", "can_engage", "param_id", "get_param", "can_shoot", "terrain_band_at", "terrain_walkable_at",
             "terrain_dump_bands", "terrain_walk_mask", "terrain_slope_at", "movement_kind"}
# new_world and free_world are mutators: a freed world's address can be handed to the next world, so a cache keyed on (engine, world
# address, epoch) would otherwise answer for the dead world.
MUTATORS = {"new_world", "free_world", "register_unit_type", "set_reach", "set_cone", "disable_abilities", "spawn", "ping", "set_layer",
            "set_emission", "set_ping_params", "order_attack_move", "order_move", "order_group_move", "order_guard", "clear_orders",
            "step", "set_param", "add_blocker", "set_canvas", "block_rect", "add_cover", "terrain_generate", "set_era_kind",
            "set_movement_kind"}
STATS = {"category": 1, "role": "x", "max_hp": 10.0, "base_damage": 1.0, "attack_interval": 1.0, "attack_range": 100.0, "speed": 1.0,
         "sensor_radius": 1.0, "layer_transition_time": 1.0, "aoe_radius": 0.0, "ability_id": 0}
CALLS = {   # one valid call per public method: name -> f(engine)
    "type_id": lambda e: e.type_id("Vanguard"), "type_stats": lambda e: e.type_stats(W, 0), "profile_reach": lambda e: e.profile_reach(W, 0),
    "visible_enemies": lambda e: e.visible_enemies(W, 0, [1, 2]), "seen_by_sight": lambda e: e.seen_by_sight(W, 0, [1]),
    "can_see": lambda e: e.can_see(W, 1, 2), "unit_hp": lambda e: e.unit_hp(W, 1), "unit_pos": lambda e: e.unit_pos(W, 1),
    "unit_destination": lambda e: e.unit_destination(W, 1), "unit_layer": lambda e: e.unit_layer(W, 1),
    "unit_alive": lambda e: e.unit_alive(W, 1), "unit_target": lambda e: e.unit_target(W, 1),
    "unit_facing": lambda e: e.unit_facing(W, 1), "unit_type": lambda e: e.unit_type(W, 1),
    "transition_progress": lambda e: e.transition_progress(W, 1), "category_multiplier": lambda e: e.category_multiplier(W, 0, 1),
    "can_engage": lambda e: e.can_engage(W, 1, 2), "param_id": lambda e: e.param_id("OM_TP_PING_RADIUS"),
    "get_param": lambda e: e.get_param(W, 0), "can_shoot": lambda e: e.can_shoot(W, 1, 2),
    "terrain_band_at": lambda e: e.terrain_band_at(W, 1.0, 1.0), "terrain_walkable_at": lambda e: e.terrain_walkable_at(W, 1.0, 1.0),
    "terrain_dump_bands": lambda e: e.terrain_dump_bands(W), "terrain_walk_mask": lambda e: e.terrain_walk_mask(W, 0),
    "terrain_slope_at": lambda e: e.terrain_slope_at(W, 1.0, 1.0), "movement_kind": lambda e: e.movement_kind(W, 0),
    "new_world": lambda e: e.new_world(0), "free_world": lambda e: e.free_world(W),
    "register_unit_type": lambda e: e.register_unit_type(W, 100, STATS), "set_reach": lambda e: e.set_reach(W, 100, 1, 1),
    "set_cone": lambda e: e.set_cone(W, 100, 100.0, 30.0, 0.5), "disable_abilities": lambda e: e.disable_abilities(W),
    "spawn": lambda e: e.spawn(W, 0, 0, 1.0, 1.0, 0), "ping": lambda e: e.ping(W, 1, 0, 1.0, 1.0),
    "set_layer": lambda e: e.set_layer(W, [1], 1), "set_emission": lambda e: e.set_emission(W, [1], True),
    "set_ping_params": lambda e: e.set_ping_params(W, radius=5.0), "order_attack_move": lambda e: e.order_attack_move(W, [1], 1.0, 1.0),
    "order_move": lambda e: e.order_move(W, [1], 1.0, 1.0), "order_group_move": lambda e: e.order_group_move(W, [1], 1.0, 1.0),
    "order_guard": lambda e: e.order_guard(W, [1]), "clear_orders": lambda e: e.clear_orders(W, [1, 2]), "step": lambda e: e.step(W),
    "set_param": lambda e: e.set_param(W, 0, 1.0), "add_blocker": lambda e: e.add_blocker(W, 1.0, 1.0, 5.0),
    "set_canvas": lambda e: e.set_canvas(W, 10.0, 10.0), "block_rect": lambda e: e.block_rect(W, 0.0, 0.0, 1.0, 1.0, 0, 1),
    "add_cover": lambda e: e.add_cover(W, 1.0, 1.0, 5.0, 1), "terrain_generate": lambda e: e.terrain_generate(W, 1, 100.0),
    "set_era_kind": lambda e: e.set_era_kind(W, 1), "set_movement_kind": lambda e: e.set_movement_kind(W, 0, 1),
}


class _Fn:
    def __init__(self, ret):
        self.ret = ret

    def __call__(self, *args):
        return self.ret


class _FakeLib:
    """Stands in for ctypes.CDLL (as tests/skilllab/test_firing.py does): every symbol exists and returns 0 unless `returns` says so."""

    def __init__(self, returns=None):
        self._returns = dict(returns or {})

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        fn = _Fn(self._returns.get(name, 0))
        object.__setattr__(self, name, fn)
        return fn


def bare_engine():
    """Engine.__new__ + _bind only: the make_engine idiom of tests/skilllab/test_firing.py. Nothing __init__ sets exists on it."""
    eng = engine_mod.Engine.__new__(engine_mod.Engine)
    eng._lib = _FakeLib({"om_world_new": 5, "om_map_add_cover": 1, "om_unit_spawn": 3})
    eng._bind()
    return eng


def engine_with_init_state():
    """The same, plus the attributes Engine.__init__ sets TODAY (the wrapper's scratch buffers and spawn log), which the calls in CALLS
    need. `epoch` is deliberately not among them: see test_epoch_needs_no_init_state."""
    eng = bare_engine()
    eng._px, eng._py = ctypes.c_double(), ctypes.c_double()
    eng._pbx, eng._pby = ctypes.byref(eng._px), ctypes.byref(eng._py)
    eng._own = {}
    return eng


def public_engine_methods():
    return {n for n, m in inspect.getmembers(engine_mod.Engine, predicate=callable) if not n.startswith("_")}


def test_every_public_engine_method_is_classified_read_only_or_mutator():
    """Mutation-style guard against a missed mutator: a public Engine method in neither set fails; so does a stale name in a set,
    a name in both, and a method with no sample call in CALLS."""
    methods = public_engine_methods()
    assert not (READ_ONLY & MUTATORS), sorted(READ_ONLY & MUTATORS)
    unclassified = methods - READ_ONLY - MUTATORS
    assert not unclassified, "classify these Engine methods as READ_ONLY or MUTATORS (and add a CALLS entry): %s" % sorted(unclassified)
    stale = (READ_ONLY | MUTATORS) - methods
    assert not stale, "classified but no longer an Engine method: %s" % sorted(stale)
    assert set(CALLS) == READ_ONLY | MUTATORS


def test_the_classification_covers_test_engines_method_list():
    """tests/skilllab/test_engine.py pins the methods every Engine has (its METHODS list); each is classified here."""
    import test_engine
    assert set(test_engine.METHODS) <= READ_ONLY | MUTATORS


def test_control_the_enumeration_catches_an_unclassified_method(monkeypatch):
    """Positive control: add a public method to Engine and the enumeration check sees it."""
    monkeypatch.setattr(engine_mod.Engine, "brand_new_mutator", lambda self, w: None, raising=False)
    assert "brand_new_mutator" in public_engine_methods() - READ_ONLY - MUTATORS


@pytest.mark.parametrize("name", sorted(MUTATORS))
def test_every_mutator_raises_the_epoch(name):
    """RED until the builder: Engine.epoch is an int and strictly rises on each state-changing method."""
    eng = engine_with_init_state()
    before = eng.epoch
    assert type(before) is int
    CALLS[name](eng)
    assert eng.epoch > before, "%s did not bump Engine.epoch (%r -> %r)" % (name, before, eng.epoch)


@pytest.mark.parametrize("name", sorted(READ_ONLY))
def test_no_read_only_method_moves_the_epoch(name):
    """RED until the builder (the attribute is missing today): a read-only call leaves Engine.epoch exactly where it was."""
    eng = engine_with_init_state()
    before = eng.epoch
    assert type(before) is int
    CALLS[name](eng)
    assert eng.epoch == before, "%s moved Engine.epoch (%r -> %r)" % (name, before, eng.epoch)


def test_epoch_needs_no_init_state():
    """The make_engine idiom (Engine.__new__ + _bind, no __init__): epoch is readable as an int and a mutator bumps it, with no
    attribute set by __init__ (a class attribute or a getattr default will do). A fake bound this way must keep working."""
    eng = bare_engine()
    first = eng.epoch
    assert type(first) is int
    eng.step(W)
    eng.step(W)
    assert eng.epoch >= first + 2
    after = eng.epoch
    eng.type_stats(W, 0)
    eng.can_shoot(W, 1, 2)
    assert eng.epoch == after


def test_two_engines_keep_their_own_epoch():
    """The counter belongs to the object: bumping one Engine leaves another alone."""
    a, b = engine_with_init_state(), engine_with_init_state()
    base_b = b.epoch
    a.step(W)
    assert a.epoch > base_b and b.epoch == base_b


# ---- the live world: the cache never goes stale across real mutations ----------------------------------------------------------------

SPACING = 30.0


def _grid(lib, w, faction, x, y, layer=0, n=16, unit="Vanguard"):
    t = lib.type_id(unit)
    return [lib.spawn(w, t, faction, x + SPACING * (i % 4), y + SPACING * (i // 4), layer) for i in range(n)]


def test_epoch_follows_a_real_world(library):
    """On the real library: spawn, step, and each world-changing order raise the epoch; reading the world does not."""
    w = library.new_world(0)
    try:
        library.disable_abilities(w)
        e0 = library.epoch
        ids = _grid(library, w, 0, 1000.0, 1000.0, n=4)
        e1 = library.epoch
        assert e1 > e0
        for u in ids:
            library.unit_pos(w, u)
            library.unit_alive(w, u)
        library.can_shoot(w, ids[0], ids[1])
        assert library.epoch == e1
        library.step(w)
        e2 = library.epoch
        assert e2 > e1
        library.add_blocker(w, 1100.0, 1000.0, 20.0)
        assert library.epoch > e2
    finally:
        library.free_world(w)


def test_live_answers_equal_the_reference_through_every_kind_of_world_change(library):
    """The staleness guard on the real library (cf. test_firing_real.py blocker cases and the live parity of test_firing.py): after each
    step AND after each out-of-band change (blocker, layer change, emission, a move order, a parameter) the live firing answers equal the uncached
    reference's, asked twice in a row so a hot cache is exercised. The mid-run changes must really move the answers."""
    w = library.new_world(0)
    try:
        library.disable_abilities(w)
        s0 = _grid(library, w, 0, 1000.0, 1000.0)
        s1 = _grid(library, w, 1, 1150.0, 1000.0)

        def answers(module):
            return tuple(getattr(module, n)(library, w, s0, s1, 360.0) for n in FIRING_FUNCTIONS)

        def check(what):
            live1, live2, frozen = answers(firing), answers(firing), answers(ref)
            assert live1 == frozen, "%s: first call differs from the reference" % what
            assert live2 == frozen, "%s: repeated call (cache hot) differs from the reference" % what
            return frozen

        check("tick 0")
        for t in range(1, 41):
            library.step(w)
            check("tick %d" % t)
        before = check("before the changes")
        library.add_blocker(w, 1120.0, 1060.0, 120.0)
        after_block = check("blocker, no step")
        assert after_block != before, "the blocker must change an answer, or the control proves nothing"
        library.set_layer(w, s1, 1)       # a layer change lands only after the transition time (about 25 ticks): check every step
        check("layer change, no step")
        for t in range(40):
            library.step(w)
            after_layer = check("layer change, step %d" % t)
        assert after_layer != after_block, "the layer change must change an answer, or the control proves nothing"
        library.set_layer(w, s1, 0)
        check("layer back, no step")
        library.set_emission(w, s1, False)
        check("emission off, no step")
        library.order_move(w, s0, 400.0, 400.0)
        for t in range(10):
            library.step(w)
            check("moving, step %d" % t)
        library.set_param(w, library.param_id("OM_TP_PING_RADIUS"), 123.0)
        check("param change, no step")
    finally:
        library.free_world(w)


# ---- (c) CPU time ratio -----------------------------------------------------------------------------------------------------------------

def measure_ratio(new_fn, ref_fn, items):
    """Run new_fn(item) and ref_fn(item) for every item, alternating which goes first. Returns (ratio, cpu_new, cpu_ref, wall_new, wall_ref):
    the ratio is time.process_time of the live side over the reference side (wall time is for the report only)."""
    cpu = {"new": 0.0, "ref": 0.0}
    wall = {"new": 0.0, "ref": 0.0}
    for i, item in enumerate(items):
        order = (("new", new_fn), ("ref", ref_fn)) if i % 2 == 0 else (("ref", ref_fn), ("new", new_fn))
        for label, fn in order:
            c0, w0 = time.process_time(), time.perf_counter()
            fn(item)
            cpu[label] += time.process_time() - c0
            wall[label] += time.perf_counter() - w0
    return cpu["new"] / cpu["ref"], cpu["new"], cpu["ref"], wall["new"], wall["ref"]


def within_ratio(measured, limit=None):
    """THE detector: the CPU ratio must not exceed the (DRAFT) limit."""
    limit = DRAFT_LAB_SPEED_RATIO_1 if limit is None else limit
    ratio, cpu_new, cpu_ref, wall_new, wall_ref = measured
    assert ratio <= limit, ("CPU ratio %.3f (live %.2f s / reference %.2f s) is over the DRAFT limit %.2f; wall %.2f s / %.2f s = %.3f"
                            % (ratio, cpu_new, cpu_ref, limit, wall_new, wall_ref, wall_new / wall_ref))


def test_the_speed_ratio_of_the_live_firing_against_the_frozen_reference(library):
    """Acceptance (c): 26 fights, blob_play(16) against 12 to 24, both orders, live and reference interleaved in this process. RED until
    the builder: today the two are the same code and the ratio is about 1.0. Results are compared too, so a faster-but-different
    firing cannot pass."""
    items = [(enemies, swap) for enemies in RATIO_ENEMIES for swap in RATIO_SWAPS]
    seen = {}

    def run(label, module):
        def go(item):
            enemies, swap = item
            seen[(label, item)] = fight_with(module, plays.blob_play(16)(enemies, swap), 0, swap, library)
        return go

    measured = measure_ratio(run("new", firing), run("ref", ref), items)
    print("\nLAB-REV2-SPEED ratio %.3f  cpu live %.2f s ref %.2f s  wall live %.2f s ref %.2f s (limit DRAFT %.2f, %d fights each)"
          % (measured[0], measured[1], measured[2], measured[3], measured[4], DRAFT_LAB_SPEED_RATIO_1, len(items)))
    for item in items:
        assert_results_equal(seen[("new", item)], seen[("ref", item)], "enemies %d swap %s" % item)
    within_ratio(measured)


def _spin_items(n=8):
    return list(range(n))


def test_control_a_planted_cpu_slowdown_fails_the_ratio_check():
    """Positive control (i): a candidate that burns as much CPU as the reference (ratio 1.0), and one that burns more, fail the check."""
    for planted in (0.012, 0.02):
        measured = measure_ratio(lambda _: burn(planted), lambda _: burn(0.012), _spin_items())
        with pytest.raises(AssertionError):
            within_ratio(measured)


def test_control_a_wrapper_planted_around_a_fast_candidate_fails_the_ratio_check():
    """Positive control (i), wrapper form: the fast candidate passes; wrapped to burn extra CPU per call, it fails."""
    def fast(_):
        burn(0.003)

    within_ratio(measure_ratio(fast, lambda _: burn(0.012), _spin_items()))

    def slowed(item):
        fast(item)
        burn(0.010)

    with pytest.raises(AssertionError):
        within_ratio(measure_ratio(slowed, lambda _: burn(0.012), _spin_items()))


def test_control_the_ratio_is_cpu_time_not_wall_time():
    """A candidate that only sleeps spends no CPU: the ratio ignores it (the wall time is printed beside, never judged)."""
    measured = measure_ratio(lambda _: time.sleep(0.02), lambda _: burn(0.012), _spin_items(4))
    assert measured[0] < 0.1 and measured[3] > 0.07
    within_ratio(measured)


def test_the_ratio_constant_is_the_ruled_draft():
    """Pins the ruled DRAFT; it changes only with Westley's word."""
    assert DRAFT_LAB_SPEED_RATIO_1 == 0.75
