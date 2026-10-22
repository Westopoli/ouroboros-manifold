# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::S (speed); Architect ruling 2026-10-22 for LAB-REV2-SPEED-1B (Westley may veto)
"""LAB-REV2-SPEED-1B (stage 1B): what the four firing.py levers must do, each with identical results. The builder owns scripts/skilllab/firing.py
and engine.py; this file only pins it. The CPU ratio acceptance is test_speed1b_ratio.py; stage one's epoch tests stay in test_speed_equal.py.

  (L-a) alive read at most once per living unit per sample (or taken from the per-tick hp): counted in a real 16v16 fight.
  (L-b) a unit's type read once per unit and world; its layer cached, and invalidated by set_layer (never stale).
  (L-c) lazy nearest-first selection, the same total order (squared distance, then lower id): equality on tie scenes, a mutant fails.
  (L-d) hoisted code evaluation, gate order 1 to 5 kept (the code of the first failing gate): equality on one scene per code, a mutant fails.

Read counts are taken at the ctypes boundary: a proxy around Engine._lib counts every call of a C function by name, and Engine._bind runs
again through it, so a read the builder takes by any route through the library is counted. New public Engine methods are not allowed.

RED today (stage one built): the three read-count bounds (L-a, L-b type, L-b layer). Everything that compares the live code with the frozen
reference, every staleness check and every positive control is green.
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
    blind counter. 16 + 16 units spawned; hundreds of samples; the stage-one code reads a unit's type and layer on every sample."""
    counts, samples, living_sum, spawned = fight_counts(library)
    assert spawned == 32 and samples > 100 and 0 < living_sum <= 32 * samples
    assert counts["om_unit_get_pos"] >= living_sum and counts["om_command_set_layer"] == 0


class ReadOnceView:
    """Control: an engine view that reads a unit's type and layer once and asks alive only of units not yet seen dead. Run with the stage-one
    firing (one sample per epoch) it shows that the three bounds below are reachable by the levers alone (no change of results)."""

    def __init__(self, engine):
        self._e, self._type, self._layer, self._dead = engine, {}, {}, set()

    def __getattr__(self, name):
        return getattr(self._e, name)

    def unit_type(self, w, u):
        if (w.value, u) not in self._type:
            self._type[(w.value, u)] = self._e.unit_type(w, u)
        return self._type[(w.value, u)]

    def unit_layer(self, w, u):
        if (w.value, u) not in self._layer:
            self._layer[(w.value, u)] = self._e.unit_layer(w, u)
        return self._layer[(w.value, u)]

    def unit_alive(self, w, u):
        if (w.value, u) in self._dead:
            return False
        alive = self._e.unit_alive(w, u)
        if not alive:
            self._dead.add((w.value, u))
        return alive


def test_control_the_read_count_bounds_are_reachable_and_the_results_unchanged(library):
    """Positive control (green today): the stage-one firing (one sample per epoch) through a view that reads type/layer once per unit and
    alive only until a unit is seen dead meets all three bounds, and its FightResult equals the frozen reference's. So the bounds ask for
    something that exists, reached by caching alone."""
    counts, samples, living_sum, spawned = fight_counts(library, view=ReadOnceView(library))
    assert counts["om_unit_get_unit_type"] <= spawned and counts["om_unit_get_layer"] <= spawned
    assert counts["om_unit_alive"] <= living_sum + spawned
    plain, _, _, _ = fight_counts(library)
    assert plain["om_unit_alive"] > living_sum + spawned and plain["om_unit_get_unit_type"] > spawned, "the plain stage-one code must break the bounds"
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
    """(L-a) RED today. Derivation: lever (L-a) is 'fewer ctypes reads of unit_alive per sample', alive taken from the per-tick hp or read
    only where needed. A unit that is already known dead need not be read again, and a unit's death must be learned once, so over a fight
    om_unit_alive reads <= sum over samples of the units alive at that sample + units spawned. (Judgement call: the Architect's wording is 'per
    sample <= living units'; the added 'units spawned' term pays for learning each death once and is the loosest form that still fails stage
    one.) Reading alive for every spawned unit on every sample, as stage one does, exceeds it as soon as units die. A builder taking alive from
    hp reads it 0 times and passes."""
    counts, samples, living_sum, spawned = fight_counts(library)
    bound = living_sum + spawned
    assert counts["om_unit_alive"] <= bound, "om_unit_alive read %d times over %d samples (bound %d = %d living-unit-samples + %d spawned)" % (
        counts["om_unit_alive"], samples, bound, living_sum, spawned)


def test_stage_1b_lb_unit_type_is_read_once_per_unit(library):
    """(L-b) RED today. Derivation: a unit's type never changes after the spawn, so it is cached once per unit and world: om_unit_get_unit_type
    reads over a whole fight <= units spawned (32 here). Stage one reads it for every living unit on every sample."""
    counts, samples, _, spawned = fight_counts(library)
    assert counts["om_unit_get_unit_type"] <= spawned, "om_unit_get_unit_type read %d times over %d samples for %d units" % (
        counts["om_unit_get_unit_type"], samples, spawned)


def test_stage_1b_lb_unit_layer_is_read_once_per_unit_when_no_set_layer_is_called(library):
    """(L-b) RED today. Derivation: the layer is cached and invalidated by set_layer only; the fight never calls set_layer (the counter shows
    0 calls of om_command_set_layer), so om_unit_get_layer reads <= units spawned + 0. Stage one reads it for every living unit on every sample."""
    counts, samples, _, spawned = fight_counts(library)
    assert counts["om_command_set_layer"] == 0
    assert counts["om_unit_get_layer"] <= spawned + counts["om_command_set_layer"], (
        "om_unit_get_layer read %d times over %d samples for %d units" % (counts["om_unit_get_layer"], samples, spawned))


# ---- (L-b) the layer never goes stale -------------------------------------------------------------------------------------------------------

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


# ---- a fake engine for the logic scenes --------------------------------------------------------------------------------------------------------

class FakeSim:
    """The surface firing reads. units: id -> {pos, layer, type, alive, facing, target}. `hidden` ids are not visible to the other side;
    `blocked` pairs fail can_shoot; `codes` (when given) makes can_engage answer from the table (the E0 path), else -1 (not available)."""

    def __init__(self, units, hidden=(), blocked=(), codes=None):
        self.units, self.hidden, self.blocked, self.codes = units, set(hidden), set(blocked), codes
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
        return 1.0

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
