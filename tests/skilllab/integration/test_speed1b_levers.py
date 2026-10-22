# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::S (speed); Architect ruling 2026-10-22 for LAB-REV2-SPEED-1B (Westley may veto)
"""LAB-REV2-SPEED-1B (stage 1B): what the firing.py / engine.py levers must do, each with identical results. The builder owns
scripts/skilllab/firing.py and engine.py; this file only pins it. The CPU ratio acceptance is test_speed1b_ratio.py; stage one's epoch
tests stay in test_speed_equal.py.

  (L-a) alive read at most once per living unit per sample (or taken from the per-tick hp), plus one confirmation read per death and one at
        spawn: counted in a real 16v16 fight.
  (L-b) a unit's type read once per unit and world.
  The layer is NOT a lever of 1B (Architect ruling 2026-10-22): a unit's layer can change inside step with no set_layer (route across layers,
        walker slopes), so it is always read live. Four scenes pin that it is never stale (set_layer, route across layers, walker slope).
  (L-c) lazy nearest-first selection, the same total order (squared distance, then lower id): equality on tie scenes, a mutant fails.
  (L-d) hoisted code evaluation, gate order 1 to 5 kept (the code of the first failing gate): equality on one scene per code, a mutant fails.

Read counts are taken at the ctypes boundary: a proxy around Engine._lib counts every call of a C function by name, and Engine._bind runs
again through it, so a read the builder takes by any route through the library is counted. New public Engine methods are not allowed.

RED today (stage one built): the two read-count bounds (L-a alive, L-b type). Everything that compares the live code with the frozen
reference (the staleness and prune scenes are correctness pins that stage one already passes), the cold-read guard and every positive
control is green.
"""
import ctypes
import math
import sys
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

W = ctypes.c_void_p(7)
FIRING_FUNCTIONS = ("count_able", "count_weighted", "states")


@pytest.fixture(scope="module")
def library():
    return engine_mod.Engine()


def load_variant(name, transform=None):
    """A module built from the reference source, optionally rewritten by `transform` (a mutant)."""
    src = Path(ref.__file__).read_text()
    if transform is not None:
        new = transform(src)
        assert new != src, "the mutation did not change the source (the control would be vacuous)"
        src = new
    mod = types.ModuleType(name)
    exec(compile(src, name, "exec"), mod.__dict__)
    return mod


# ---- a counting proxy at the ctypes boundary ----------------------------------------------------------------------------------------------

class _CountedFn:
    def __init__(self, fn, name, counts):
        object.__setattr__(self, "_fn", fn)
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_counts", counts)

    def __call__(self, *args):
        self._counts[self._name] += 1
        return self._fn(*args)

    def __setattr__(self, key, value):      # argtypes / restype set by Engine._bind land on the real function
        setattr(self._fn, key, value)


class CountingLib:
    """Wraps the CDLL: every function fetched through it counts its calls by C name. `real` is the uncounted library."""

    def __init__(self, real):
        self.real, self.counts, self._wrapped = real, Counter(), {}

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        if name not in self._wrapped:
            self._wrapped[name] = _CountedFn(getattr(self.real, name), name, self.counts)
        return self._wrapped[name]


class counted:
    """Context manager: the engine's library goes through a CountingLib, and Engine._bind runs again through it (so any function pointer
    the builder caches at bind time is a counted one). The original library is restored on exit."""

    def __init__(self, engine):
        self.engine = engine

    def __enter__(self):
        self.original = self.engine._lib
        self.lib = CountingLib(self.original)
        self.engine._lib = self.lib
        self.engine._bind()
        return self.lib

    def __exit__(self, *exc):
        self.engine._lib = self.original
        self.engine._bind()


def fight_counts(engine, enemies=16, module=None, view=None):
    """Run one 16v16 fight (fixed seed) with the live firing (or `module`'s three functions, through `view` of the engine). Returns (counts, samples, living_sum, units_spawned): samples = calls of
    fight's count_able (one per sample tick); living_sum = sum over samples of the units alive at that sample (read on the uncounted lib)."""
    samples, living = [0], [0]
    saved = {n: getattr(fight, n) for n in FIRING_FUNCTIONS}
    real_count_able = getattr((module or firing), "count_able")

    def watching(eng, w, u0, u1, arc):
        out = real_count_able(eng, w, u0, u1, arc)
        samples[0] += 1
        living[0] += sum(1 for u in list(u0) + list(u1) if lib.real.om_unit_alive(w, u))
        return out

    with counted(engine) as lib:
        try:
            for n in FIRING_FUNCTIONS:
                setattr(fight, n, getattr(module or firing, n))
            fight.count_able = watching
            fight.fight(plays.blob_play(16)(enemies, False), 0, False, view or engine)
        finally:
            for n, f in saved.items():
                setattr(fight, n, f)
    return lib.counts, samples[0], living[0], lib.counts["om_unit_spawn"]


# ---- (L-a, L-b) read counts in a real fight ---------------------------------------------------------------------------------------------

def test_the_counting_proxy_counts_a_real_fight(library):
    """Guard (green today): the proxy sees the spawns, the samples and the reads the bounds below are made of, so a bound cannot hold by a
    blind counter. 16 + 16 units spawned; hundreds of samples. COLD-READ PROBE: in a fresh world under the proxy, one unit is spawned and
    engine.unit_alive, unit_type and unit_layer are called once each; every C counter must be exactly 1. A value cache passes (its first read
    is cold); a builder who binds the C functions as attributes in Engine.__init__ (bypassing the proxy) reads 0 and fails, so the bounds
    below cannot pass by a blind counter."""
    counts, samples, living_sum, spawned = fight_counts(library)
    assert spawned == 32 and samples > 100 and 0 < living_sum <= 32 * samples
    assert counts["om_unit_get_pos"] >= living_sum and counts["om_command_set_layer"] == 0
    with counted(library) as lib:
        w = library.new_world(0)
        try:
            u = library.spawn(w, library.type_id("Vanguard"), 0, 1000.0, 1000.0, 0)
            assert library.unit_alive(w, u) is True
            assert isinstance(library.unit_type(w, u), int)
            assert library.unit_layer(w, u) == 0
        finally:
            library.free_world(w)
    for name in ("om_unit_alive", "om_unit_get_unit_type", "om_unit_get_layer"):
        assert lib.counts[name] == 1, "cold read of %s counted %d times (a read that bypasses the counting proxy reads 0)" % (name, lib.counts[name])


class ReadOnceView:
    """Control: an engine view that reads a unit's type once and asks alive only of units not yet seen dead. Run with the firing (one sample
    per epoch) it shows that the two bounds below are reachable by caching alone (no change of results)."""

    def __init__(self, engine):
        self._e, self._type, self._dead = engine, {}, set()

    def __getattr__(self, name):
        return getattr(self._e, name)

    def unit_type(self, w, u):
        if (w.value, u) not in self._type:
            self._type[(w.value, u)] = self._e.unit_type(w, u)
        return self._type[(w.value, u)]

    def unit_alive(self, w, u):
        if (w.value, u) in self._dead:
            return False
        alive = self._e.unit_alive(w, u)
        if not alive:
            self._dead.add((w.value, u))
        return alive


def test_control_the_read_count_bounds_are_reachable_and_the_results_unchanged(library):
    """Positive control (green on stage one and on a correct sped tree alike): the firing through a view that reads a unit's type once and
    alive only until a unit is seen dead meets both bounds, and its FightResult equals the frozen reference's. So the bounds ask for
    something that exists, reached by caching alone. (It does not assert that the plain engine breaks the bounds: a correct sped engine
    does not.)"""
    counts, samples, living_sum, spawned = fight_counts(library, view=ReadOnceView(library))
    assert counts["om_unit_get_unit_type"] <= spawned
    assert counts["om_unit_alive"] <= living_sum + 2 * spawned
    setup = plays.blob_play(16)(16, False)
    saved = {n: getattr(fight, n) for n in FIRING_FUNCTIONS}
    try:
        for n in FIRING_FUNCTIONS:
            setattr(fight, n, getattr(ref, n))
        frozen = fight.fight(setup, 0, False, library)
    finally:
        for n, f in saved.items():
            setattr(fight, n, f)
    assert fight.fight(setup, 0, False, ReadOnceView(library)) == frozen


def test_stage_1b_la_alive_is_read_at_most_once_per_living_unit_per_sample_plus_once_per_unit(library):
    """(L-a) RED today. Derivation (Architect audit fix 2026-10-22): lever (L-a) is 'fewer ctypes reads of unit_alive per sample', alive
    taken from the per-tick hp or read only where needed. A unit that is already known dead is not read again. Each sample reads each living
    unit at most once (living_sum reads in all: the units alive at each sample, summed), each death costs one confirmation read (the read that
    finds the unit dead, once per unit: at most `spawned`), and each unit may be read once at spawn (at most `spawned`). So over a fight
    om_unit_alive reads <= living_sum + 2 * spawned (13318 + 64 = 13382 on the standard 16v16 fight). Reading alive for every spawned unit on
    every sample, as stage one does (28896 reads), exceeds it as soon as units die. A builder taking alive from hp reads it 0 times and passes
    (the cold-read probe in the counter guard keeps the counter honest)."""
    counts, samples, living_sum, spawned = fight_counts(library)
    bound = living_sum + 2 * spawned
    assert counts["om_unit_alive"] <= bound, "om_unit_alive read %d times over %d samples (bound %d = %d living-unit-samples + 2 * %d spawned)" % (
        counts["om_unit_alive"], samples, bound, living_sum, spawned)


def test_stage_1b_lb_unit_type_is_read_once_per_unit(library):
    """(L-b) RED today. Derivation: a unit's type never changes after the spawn, so it is cached once per unit and world: om_unit_get_unit_type
    reads over a whole fight <= units spawned (32 here). Stage one reads it for every living unit on every sample."""
    counts, samples, _, spawned = fight_counts(library)
    assert counts["om_unit_get_unit_type"] <= spawned, "om_unit_get_unit_type read %d times over %d samples for %d units" % (
        counts["om_unit_get_unit_type"], samples, spawned)


# ---- the layer is read live and never stale (not a 1B lever; correctness pins that stage one passes) -------------------------------------------------------------------------------------------------------

SPACING = 30.0


def _grid(lib, w, faction, x, y, layer=0, n=16, unit="Vanguard"):
    t = lib.type_id(unit)
    return [lib.spawn(w, t, faction, x + SPACING * (i % 4), y + SPACING * (i // 4), layer) for i in range(n)]


class StaleLayerEngine:
    """The mutant: an engine view whose unit_layer is cached forever (a layer cache never invalidated by set_layer). Everything else passes through."""

    def __init__(self, engine):
        self._e, self._layers = engine, {}

    def __getattr__(self, name):
        return getattr(self._e, name)

    def unit_layer(self, w, u):
        if (w.value, u) not in self._layers:
            self._layers[(w.value, u)] = self._e.unit_layer(w, u)
        return self._layers[(w.value, u)]


def _layer_scene(library, trace):
    """s1 starts on layer 0 beside s0, then set_layer moves it to layer 1 (lands after the transition time, about 25 ticks). Returns the
    list of `trace(w, s0, s1)` per tick."""
    w = library.new_world(0)
    try:
        library.disable_abilities(w)
        s0 = _grid(library, w, 0, 1000.0, 1000.0)
        s1 = _grid(library, w, 1, 1150.0, 1000.0)
        rows = [trace(w, s0, s1)]
        for _ in range(3):
            library.step(w)
            rows.append(trace(w, s0, s1))
        library.set_layer(w, s1, 1)
        rows.append(trace(w, s0, s1))
        for _ in range(45):
            library.step(w)
            rows.append(trace(w, s0, s1))
        return rows
    finally:
        library.free_world(w)


def _answers(module, engine, w, s0, s1):
    return tuple(getattr(module, n)(engine, w, s0, s1, 360.0) for n in FIRING_FUNCTIONS)


def test_stage_1b_lb_layer_follows_set_layer_and_its_transition_exactly_as_the_reference(library):
    """(L-b) staleness, green today and must stay green: after set_layer mid-run, and at every step through the transition, the live answers
    (asked twice, so a hot cache is used) equal the uncached reference's, and the layer change really moves an answer."""
    live = _layer_scene(library, lambda w, s0, s1: (_answers(firing, library, w, s0, s1), _answers(firing, library, w, s0, s1)))
    frozen = _layer_scene(library, lambda w, s0, s1: (_answers(ref, library, w, s0, s1), _answers(ref, library, w, s0, s1)))
    assert live == frozen
    assert frozen[3][0] != frozen[-1][0], "the layer change must change an answer, or the check proves nothing"


def test_control_a_layer_cache_never_invalidated_fails_the_staleness_check(library):
    """Positive control: the reference run on an engine whose layer is cached forever (the mutant) differs from the true reference once
    set_layer has landed, so the staleness check above can fail."""
    stale_view = StaleLayerEngine(library)
    mutant = _layer_scene(library, lambda w, s0, s1: _answers(ref, stale_view, w, s0, s1))
    frozen = _layer_scene(library, lambda w, s0, s1: _answers(ref, library, w, s0, s1))
    assert mutant != frozen


# ---- the layer changes inside step with no set_layer call: route across layers, and a walker on a slope --------------------------------------

def _route_across_world(lib, w):
    """OM_TP_ROUTE_ACROSS_LAYERS = 1 and a wall on layer 0 only between the mover and its goal: order_move sends the mover over the wall by
    layer 1 (the layer goes 0, then 1 at about tick 25, then back to 0 at about tick 199, with no set_layer). The enemy sits on layer 0,
    and a Vanguard's reach is 0 up 0 down, so the code against it is 2 (not seen) on layer 0 before the climb, 1 (out of reach) on layer 1, then 0."""
    lib.set_canvas(w, 4000.0, 4000.0)
    lib.set_param(w, lib.param_id("OM_TP_ROUTE_ACROSS_LAYERS"), 1.0)
    lib.block_rect(w, 1500.0, 0.0, 1700.0, 4000.0, 0, 0)
    t = lib.type_id("Vanguard")
    me = lib.spawn(w, t, 0, 1000.0, 2000.0, 0)
    enemy = lib.spawn(w, t, 1, 1900.0, 2100.0, 0)
    lib.order_move(w, [me], 2400.0, 2000.0)
    return me, enemy, 240


def _slope_world(lib, w):
    """A walker (Vanguard) at the foot of slope 2 of the generated field of seed 11 (canvas 12000, bands 2 and 3 = layers 1 and 2), ordered
    to the top: its layer goes 1, then 2 at about tick 25 as it climbs, and back to 1 at about tick 229, with no set_layer. The enemy waits on
    layer 2 (code 1 out of reach while the walker is on layer 1, then 3, 0, 3 as it climbs on layer 2). Costs about 13 s (terrain generation)."""
    lib.set_canvas(w, 12000.0, 12000.0)
    lib.terrain_generate(w, 11, 12000.0)
    t = lib.type_id("Vanguard")
    me = lib.spawn(w, t, 0, 9350.0, 3150.0, 1)
    enemy = lib.spawn(w, t, 1, 8800.0, 3150.0, 2)
    lib.order_move(w, [me], 8850.0, 3150.0)
    return me, enemy, 260


def _moving_trace(library, build):
    """One world, one row per tick. Each row holds: the true layer (an uncounted read of the C library), the engine's unit_layer asked twice, the
    live firing's three answers asked twice (so a hot cache is used), the frozen reference's answers, and the reference's answers on an engine
    whose layer is cached forever (the mutant). No set_layer is ever called."""
    w = library.new_world(0)
    try:
        library.disable_abilities(w)
        me, enemy, ticks = build(library, w)
        stale = StaleLayerEngine(library)
        rows = []
        for tick in range(ticks + 1):
            if tick:
                library.step(w)
            rows.append(dict(
                tick=tick, truth=library._lib.om_unit_get_layer(w, me), asked=(library.unit_layer(w, me), library.unit_layer(w, me)),
                live=(_answers(firing, library, w, [me], [enemy]), _answers(firing, library, w, [me], [enemy])),
                ref=_answers(ref, library, w, [me], [enemy]), mutant=_answers(ref, stale, w, [me], [enemy])))
        return rows
    finally:
        library.free_world(w)


@pytest.fixture(scope="module", params=["route_across_layers", "walker_slope"])
def moving_rows(request, library):
    return _moving_trace(library, {"route_across_layers": _route_across_world, "walker_slope": _slope_world}[request.param])


def test_stage_1b_the_layer_that_changes_inside_step_is_never_stale_exactly_as_the_reference(moving_rows):
    """Correctness pin (green on stage one; a layer cache that is not refreshed when the engine moves a unit between layers fails it). At
    every tick the live engine's layer (asked twice) is the true layer, and the live firing's answers (asked twice) equal the frozen
    reference's. The scene must prove the layer really changes without set_layer: the true layer takes at least two values, and the
    reference answers on one layer are not any answer seen on another (so a stale layer would change an answer)."""
    for r in moving_rows:
        assert r["asked"] == (r["truth"], r["truth"]), "tick %d: unit_layer asked twice gave %s, the layer is %d" % (r["tick"], r["asked"], r["truth"])
        assert r["live"] == (r["ref"], r["ref"]), "tick %d (layer %d): live answers differ from the reference" % (r["tick"], r["truth"])
    layers = {r["truth"] for r in moving_rows}
    assert len(layers) >= 2, "the layer never changed in this scene (%s)" % sorted(layers)
    answers = {layer: {repr(r["ref"]) for r in moving_rows if r["truth"] == layer} for layer in layers}
    for a in layers:
        for b in layers:
            assert a == b or not (answers[a] & answers[b]), "a reference answer is shared by layers %d and %d: a stale layer could hide" % (a, b)


def test_control_a_layer_cache_never_invalidated_fails_the_moving_layer_scenes(moving_rows):
    """Positive control: the reference on an engine whose layer is cached forever differs from the true reference at some tick once the
    layer has changed inside step, so the check above can fail (a layer that changes with no set_layer defeats a cache refreshed by set_layer alone)."""
    differing = [r["tick"] for r in moving_rows if r["mutant"] != r["ref"]]
    assert differing and min(differing) > 0, "the never-invalidated layer cache is not caught by this scene"


# ---- a fake engine for the logic scenes --------------------------------------------------------------------------------------------------------

class FakeSim:
    """The surface firing reads. units: id -> {pos, layer, type, alive, facing, target}. `hidden` ids are not visible to the other side;
    `blocked` pairs fail can_shoot; `params` sets named parameters (default 1.0); `codes` (when given) makes can_engage answer from the table (the E0 path), else -1 (not available)."""

    def __init__(self, units, hidden=(), blocked=(), codes=None, params=None):
        self.units, self.hidden, self.blocked, self.codes = units, set(hidden), set(blocked), codes
        self.params = params or {}      # parameter name -> value (param_id answers the name itself); default 1.0
        self.calls = Counter()

    def unit_alive(self, w, u):
        return self.units[u]["alive"]

    def unit_pos(self, w, u):
        return self.units[u]["pos"]

    def unit_layer(self, w, u):
        return self.units[u]["layer"]

    def unit_type(self, w, u):
        return self.units[u]["type"]

    def unit_target(self, w, u):
        return self.units[u].get("target", 0)

    def unit_facing(self, w, u):
        return self.units[u].get("facing", 0.0)

    def type_stats(self, w, t):
        return {"attack_range": 300.0, "category": t % 3}

    def profile_reach(self, w, t):
        return (1, 1)

    def visible_enemies(self, w, side, ids):
        return {i for i in ids if i not in self.hidden}

    def get_param(self, w, p):
        return self.params.get(p, 1.0)

    def param_id(self, name):
        return name

    def can_engage(self, w, a, b):
        return -1 if self.codes is None else self.codes.get((a, b), 0)

    def can_shoot(self, w, a, b):
        return (a, b) not in self.blocked

    def category_multiplier(self, w, a, b):
        return 1.0 + 0.1 * a + 0.01 * b


def _answers_fake(module, sim, s0, s1, arc=360.0):
    return (module.count_able(sim, W, s0, s1, arc), module.count_weighted(sim, W, s0, s1, arc), module.states(sim, W, s0, s1, arc))


def _u(x, y, t=0, layer=0, **kw):
    return dict({"pos": (float(x), float(y)), "layer": layer, "type": t, "alive": True}, **kw)


def _ring_scene():
    """Side 0: unit 1 at the origin and unit 2 far to the left. Side 1: ids 5, 9, 12, 20 at EXACTLY equal squared distance 10000 from unit 1
    (axis points), with different types (so different categories) and different gate outcomes by id: 5 hidden (code 2), 9 blocked (code 5),
    12 and 20 fire (code 0, categories 0 and 2, so the chosen target's id shows in the weight)."""
    units = {1: _u(0, 0, 0), 2: _u(-1000, 0, 1),
             5: _u(100, 0, 1), 9: _u(-100, 0, 2), 12: _u(0, 100, 0), 20: _u(0, -100, 2)}
    return units, [1, 2], [5, 9, 12, 20]


# ---- (L-c) nearest-first, same total order ------------------------------------------------------------------------------------------------------

def test_stage_1b_lc_ties_in_distance_are_broken_by_the_lower_id_exactly_as_the_reference():
    """(L-c) equality on a tie scene (equal squared distances, ids decide): the live count/weight/state answers equal the reference's on
    the whole scene, and for unit 1 alone the reference really chose the lower id 12 among the code-0 ties 12 and 20 (their categories differ,
    so the weight shows the choice)."""
    units, s0, s1 = _ring_scene()
    kw = dict(hidden={5}, blocked={(1, 9)})
    expected = _answers_fake(ref, FakeSim(units, **kw), s0, s1)
    assert _answers_fake(firing, FakeSim(units, **kw), s0, s1) == expected
    sim = FakeSim(units, **kw)
    cat_12, cat_20 = sim.category_multiplier(W, 0, 0), sim.category_multiplier(W, 0, 2)    # unit 1 is type 0; 12 is type 0, 20 is type 2
    assert cat_12 != cat_20
    one_unit = _answers_fake(ref, FakeSim(units, **kw), [1], s1)
    assert one_unit[1][0] == cat_12, "the reference must choose the lower id 12 among the code-0 ties"
    assert _answers_fake(firing, FakeSim(units, **kw), [1], s1) == one_unit


def test_stage_1b_lc_the_first_failing_code_is_that_of_the_lowest_id_among_ties():
    """(L-c) when nothing fires, the state is the code of the first enemy in (distance, id) order. The four enemies tie; 5 and 9 are blocked
    (code 5) and 12 and 20 are hidden (code 2): the lowest id 5 gives code 5, whereas a higher id first would give code 2."""
    units, s0, s1 = _ring_scene()
    kw = dict(hidden={12, 20}, blocked={(1, 5), (1, 9)})
    expected = _answers_fake(ref, FakeSim(units, **kw), [1], s1)
    assert dict(expected[2])[1] == 5
    assert _answers_fake(firing, FakeSim(units, **kw), [1], s1) == expected


def test_stage_1b_lc_no_target_scene_gives_the_same_answers():
    """(L-c) a side with no living enemy: the record is (-1, 0), nothing fires, no weight; the live answers equal the reference's, and the
    reference really holds the -1 states."""
    units, s0, s1 = _ring_scene()
    for u in s1:
        units[u]["alive"] = False
    expected = _answers_fake(ref, FakeSim(units), s0, s1)
    assert dict(expected[2])[1] == -1 and expected[0] == (0, 0)
    assert _answers_fake(firing, FakeSim(units), s0, s1) == expected
    both = _answers_fake(ref, FakeSim(units), [], [])
    assert _answers_fake(firing, FakeSim(units), [], []) == both


def test_control_a_record_variant_ordering_ties_by_the_higher_id_fails_the_tie_scenes():
    """Positive control: a copy of the reference with ties broken by the HIGHER id (key ... , -v) gives a different answer on the tie scenes
    (both the code-0 choice and the first-failing code), so the two tests above can fail."""
    mutant = load_variant("mutant_high_id", lambda s: s.replace("(enemies[v][1] - y) ** 2, v))", "(enemies[v][1] - y) ** 2, -v))"))
    units, s0, s1 = _ring_scene()
    kw = dict(hidden={5}, blocked={(1, 9)})
    assert _answers_fake(mutant, FakeSim(units, **kw), [1], s1) != _answers_fake(ref, FakeSim(units, **kw), [1], s1)
    kw2 = dict(hidden={12, 20}, blocked={(1, 5), (1, 9)})
    assert _answers_fake(mutant, FakeSim(units, **kw2), [1], s1) != _answers_fake(ref, FakeSim(units, **kw2), [1], s1)


# ---- (L-c) the prune is sound: a valid target that is not the nearest, and a farther enemy in range through a layer-range multiplier ------------

def _target_scene():
    """Unit 1 (type 0, category 0) with two enemies in range: 5 at 100 (type 1, category 1) and 9 at 200 (type 2, category 2). The weight shows which
    one the record names: category_multiplier is 1.0 + 0.1 * a + 0.01 * b."""
    return {1: _u(0, 0, 0), 5: _u(100, 0, 1), 9: _u(200, 0, 2)}, [1], [5, 9]


def test_stage_1b_lc_a_valid_non_nearest_target_of_record_is_kept_exactly_as_the_reference():
    """(L-c) correctness pin: unit 1's `target` is the farther enemy 9 and it can still engage it (code 0), so the record names 9, not the
    nearest 5 (the weight shows it: category 2, not 1). Blocking that shot (code 5) drops the record to the nearest-first scan, which finds 5."""
    units, s0, s1 = _target_scene()
    units[1]["target"] = 9
    sim = FakeSim(units)
    to_9, to_5 = sim.category_multiplier(W, 0, 2), sim.category_multiplier(W, 0, 1)
    assert to_9 != to_5
    expected = _answers_fake(ref, FakeSim(units), s0, s1)
    assert expected[1][0] == to_9, "the reference must keep the valid non-nearest target 9"
    assert _answers_fake(firing, FakeSim(units), s0, s1) == expected
    blocked = _answers_fake(ref, FakeSim(units, blocked={(1, 9)}), s0, s1)
    assert blocked[1][0] == to_5, "with the target's shot blocked the reference falls back to the nearest, 5"
    assert _answers_fake(firing, FakeSim(units, blocked={(1, 9)}), s0, s1) == blocked


def _range_up_scene():
    """Unit 1 (range 300, reach 1 up 1 down) with OM_TP_RANGE_UP_1 = 1.5: the nearest enemy 5 (layer 0, 350 away) is out of range (code 3);
    the farther enemy 9 (layer +1, 400 away, range there 300 * 1.5 = 450) is in range and fires. No other gate fails."""
    units = {1: _u(0, 0, 0), 5: _u(350, 0, 1), 9: _u(0, 400, 2, layer=1)}
    return units, [1], [5, 9], {"OM_TP_RANGE_UP_1": 1.5}


def test_stage_1b_lc_a_farther_enemy_in_range_through_a_range_multiplier_above_one_is_found_exactly_as_the_reference():
    """(L-c) correctness pin against an unsound prune: the nearest enemy is out of range but a farther one at +1 layer is in range (the
    multiplier 1.5 above 1 lifts its reach to 450). The reference must choose that farther enemy 9 (asserted: one able unit, the weight of
    category 2 against category 0), and the live code must equal it; a prune whose cap ignores multipliers above 1 stops at 300 and misses 9."""
    units, s0, s1, params = _range_up_scene()
    sim = FakeSim(units, params=params)
    expected = _answers_fake(ref, FakeSim(units, params=params), s0, s1)
    assert expected[0] == (1, 0) and dict(expected[2])[1] == 0
    assert expected[1][0] == sim.category_multiplier(W, 0, 2) != sim.category_multiplier(W, 0, 1), "the reference must choose the farther enemy 9"
    assert _answers_fake(firing, FakeSim(units, params=params), s0, s1) == expected


def _prune_with_cap_equal_to_range(src):
    """The mutant: stop the nearest-first scan once an enemy is farther than the unit's plain range (a cap that ignores multipliers above 1)."""
    scan = "        for v in sorted(enemies, key=lambda v: ((enemies[v][0] - x) ** 2 + (enemies[v][1] - y) ** 2, v)):\n"
    assert scan in src
    return src.replace(scan, "        rng0 = self.type_info(self.sides[side][u][3])[0]\n" + scan +
                       "            if first is not None and (enemies[v][0] - x) ** 2 + (enemies[v][1] - y) ** 2 > rng0 * rng0:\n"
                       "                return first\n")


def test_control_a_prune_with_the_cap_at_the_plain_range_fails_the_range_multiplier_scene():
    """Positive control: the reference with that unsound prune answers (0, 0) (no unit able, code 3 against the nearest) where the reference
    answers (1, 0), so the scene above can fail; and with the multiplier at its default 1.0 the prune is harmless, so it is the multiplier that
    the scene exercises."""
    mutant = load_variant("mutant_prune_cap_range", _prune_with_cap_equal_to_range)
    units, s0, s1, params = _range_up_scene()
    assert _answers_fake(mutant, FakeSim(units, params=params), s0, s1)[0] == (0, 0)
    assert _answers_fake(ref, FakeSim(units, params=params), s0, s1)[0] == (1, 0)
    assert _answers_fake(mutant, FakeSim(units), s0, s1) == _answers_fake(ref, FakeSim(units), s0, s1)


# ---- (L-d) gate order 1 to 5 ----------------------------------------------------------------------------------------------------------------

def _gate_scene(code):
    """One unit (id 1) against one enemy (id 2) that fails every gate from `code` to 5 (and passes the earlier ones), so only the gate order
    decides the code. 1: layer offset 3 (the reach is 1); 2: enemy hidden; 3: 600 away (range 300); 4: unit faces away (arc 30); 5: shot
    blocked; 0: nothing fails."""
    me, enemy = _u(0, 0), _u(250, 0)
    hidden, blocked = set(), set()
    if code == 1:
        enemy["layer"] = 3
    if 1 <= code <= 2:
        hidden.add(2)
    if 1 <= code <= 3:
        enemy["pos"] = (600.0, 0.0)
    if 1 <= code <= 4:
        me["facing"] = math.pi
    if code != 0:
        blocked.add((1, 2))
    return {1: me, 2: enemy}, hidden, blocked


@pytest.mark.parametrize("code", [0, 1, 2, 3, 4, 5])
def test_stage_1b_ld_each_gate_code_is_the_first_failing_gate_exactly_as_the_reference(code):
    """(L-d) one scene per gate code, built so that the pair fails every gate from `code` to 5: the reference returns `code` for unit 1
    (checked), and the live code returns the same code and the same counts. Gate order 1 to 5 is pinned for every neighbouring pair."""
    units, hidden, blocked = _gate_scene(code)
    expected = _answers_fake(ref, FakeSim(units, hidden=hidden, blocked=blocked), [1], [2], 30.0)
    assert dict(expected[2])[1] == code, "scene for code %d gives %s in the reference" % (code, expected[2])
    assert _answers_fake(firing, FakeSim(units, hidden=hidden, blocked=blocked), [1], [2], 30.0) == expected


def _swap_gates_2_and_3(src):
    vis = "        if v not in self.visible(side):\n            return 2\n"
    rng = ("        reach = rng * self.offset_mult(off)\n        dx, dy = ex - x, ey - y\n"
           "        if dx * dx + dy * dy > reach * reach:\n            return 3\n")
    assert vis + rng in src
    return src.replace(vis + rng, rng + vis)


def test_control_a_mutant_that_swaps_gates_2_and_3_fails_the_gate_order_scene():
    """Positive control: the reference with visibility and range checked in the other order answers 3 where the reference answers 2 (the
    scene for code 2 fails both gates), so the per-code test above can fail."""
    mutant = load_variant("mutant_swap_23", _swap_gates_2_and_3)
    units, hidden, blocked = _gate_scene(2)
    assert dict(_answers_fake(mutant, FakeSim(units, hidden=hidden, blocked=blocked), [1], [2], 30.0)[2])[1] == 3
    assert dict(_answers_fake(ref, FakeSim(units, hidden=hidden, blocked=blocked), [1], [2], 30.0)[2])[1] == 2


def test_stage_1b_ld_the_engine_answer_path_is_unchanged():
    """(L-d) when the engine answers can_engage itself (E0 present: any answer but -1), the code is the engine's answer, not the composed
    one: a fake with a code table gives the same counts and states as the reference, and the table's non-zero codes reach the states."""
    units, s0, s1 = _ring_scene()
    table = {(1, 5): 3, (1, 9): 4, (1, 12): 0, (1, 20): 0, (2, 5): 2, (2, 9): 2, (2, 12): 5, (2, 20): 1}
    expected = _answers_fake(ref, FakeSim(units, codes=table), s0, s1)
    assert {c for _, c in expected[2]} >= {0, 2}
    assert _answers_fake(firing, FakeSim(units, codes=table), s0, s1) == expected
