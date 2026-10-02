"""Drive the Python reference sim (simulation/, TacticalEngine) over a parity scene.

Loads simulation/ modules into a private namespace (a fresh import per variant, kept out of
sys.modules between runs so nothing else in the pytest session sees `config`, `unit`, `movement`...),
resets the module-level state the Python keeps between engines, and records a Trace.

Variants (the Python is never edited; a variant is the stock source with one line swapped at load
time, and the swap asserts its anchor text exists):
  "stock"          the Python as it is: trig steering sweep.
  "fixed"          the sweep done with fixed direction vectors (cos/sin of +-30, +-60, +-90 as
                   constants, rotated onto the seek vector), as plan P8 specifies for the C.
                   fixed_digits=None keeps full double precision; an int rounds the constants.
  "order_rev"      stock, but the collision pass starts its pairs in descending uid order: a probe
                   for how much the result depends on pair order (Python: grid cells, C: id order).

Random: the Python draws random numbers in exactly one place, reinforcement.py:69-70 (module-level
random.random(), unseeded), reachable only with reinforcement structures, which no scene has. The
TacticalEngine's own seeded Random is never drawn from in these scenes (update_targeting takes
`rng` and ignores it). To prove it, every module-level `random` draw function is replaced by one
that raises while a scene runs.
"""
import contextlib
import importlib
import io
import math
import os
import random
import sys
import types
from pathlib import Path

from .parity_compare import Trace, TWO_PI
from .parity_scenes import CUSTOM_TYPES

REPO = Path(__file__).resolve().parents[3]
SIM_DIR = REPO / "simulation"

_FIXED_ANCHOR = """            heading_angle = math.atan2(seek_y, seek_x)
            for deg in [30, -30, 60, -60, 90, -90]:
                a = heading_angle + math.radians(deg)
                ax, ay = math.cos(a), math.sin(a)
"""
_FIXED_REPLACEMENT = """            for _c, _s in _FIXED_SWEEP:
                ax = seek_x * _c - seek_y * _s
                ay = seek_x * _s + seek_y * _c
"""
_ORDER_ANCHOR = "        for uid_a in moved:\n"
_ORDER_REPLACEMENT = "        for uid_a in sorted(moved, reverse=True):\n"

_loaded = {}


def _fixed_sweep(digits):
    c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))
    c60, s60 = math.cos(math.radians(60)), math.sin(math.radians(60))
    rows = [(c30, s30), (c30, -s30), (c60, s60), (c60, -s60), (0.0, 1.0), (0.0, -1.0)]
    if digits is not None:
        rows = [(round(c, digits), round(s, digits)) for c, s in rows]
    return rows


def _movement_variant(variant, digits):
    src = (SIM_DIR / "movement.py").read_text()
    if variant == "fixed":
        assert _FIXED_ANCHOR in src, "simulation/movement.py sweep block moved; update parity_python._FIXED_ANCHOR"
        src = src.replace(_FIXED_ANCHOR, _FIXED_REPLACEMENT)
        src += "\n_FIXED_SWEEP = %r\n" % (_fixed_sweep(digits),)
    elif variant == "order_rev":
        assert _ORDER_ANCHOR in src, "simulation/movement.py collision loop moved; update parity_python._ORDER_ANCHOR"
        src = src.replace(_ORDER_ANCHOR, _ORDER_REPLACEMENT)
    mod = types.ModuleType("movement")
    mod.__file__ = str(SIM_DIR / "movement.py")
    sys.modules["movement"] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def _sim_module_names():
    return [p.stem for p in SIM_DIR.glob("*.py")]


@contextlib.contextmanager
def _sim_on_path(ns=None):
    """Put simulation/ on sys.path, and (when ns is given) its modules in sys.modules, for the
    duration; restore everything after, so the pytest session is not polluted."""
    names = _sim_module_names()
    saved = {n: sys.modules.pop(n) for n in names if n in sys.modules}
    saved_path = list(sys.path)
    sys.path.insert(0, str(SIM_DIR))
    if ns is not None:
        sys.modules.update(ns.modules)
    try:
        yield
    finally:
        for n in names:
            sys.modules.pop(n, None)
        sys.modules.update(saved)
        sys.path[:] = saved_path


def load(variant="stock", digits=None):
    """Return a namespace of freshly imported simulation modules for a variant (cached)."""
    key = (variant, digits)
    if key in _loaded:
        return _loaded[key]
    with _sim_on_path():
        if variant != "stock":
            _movement_variant(variant, digits)
        names = ("config", "unit", "movement", "damage", "facing", "command", "tactical_engine",
                 "tactical_map", "test_maps", "test_obstacle_navigation")
        mods = {n: importlib.import_module(n) for n in names}
        keep = {n: sys.modules[n] for n in sys.modules if n in set(_sim_module_names())}
    ns = types.SimpleNamespace(variant=variant, digits=digits, modules=keep, **mods)
    _loaded[key] = ns
    return ns


# Module-level state the Python keeps between engines. Anything else found by audit_state() that is
# not listed here makes tests/csim/parity/test_parity_harness.py fail, so a new global cannot slip by.
RESET_COVERS = {"damage": {"_targeting_tick"},
                "facing": {"_prev_x", "_prev_y", "_prev_initialized", "_facing_log_counter"}}


def reset_globals(ns):
    """Reset every module-level counter and cache the Python carries from one engine to the next:
    damage._targeting_tick (the targeting cohort clock), facing._prev_x/_prev_y/_prev_initialized
    (previous positions for velocity facing), facing._facing_log_counter. Per-map caches
    (_navmesh, _path_cache) and per-engine state (UnitStore, move groups) live on instances that
    each scene builds fresh."""
    ns.damage._targeting_tick = 0
    ns.facing._prev_x[:] = 0.0
    ns.facing._prev_y[:] = 0.0
    ns.facing._prev_initialized = False
    ns.facing._facing_log_counter = 0


def audit_state():
    """Names of module-level mutable/rebound state in the simulation modules the tick runs through,
    found by reading the source (AST): names declared `global` in a function, plus lower-case or
    underscore module-level names bound to a container or call. Returns {module: set(names)}."""
    import ast
    found = {}
    for mod in ("damage", "facing", "movement", "command", "unit", "ability", "fog_of_war",
                "tactical_map", "tactical_engine", "spine_drift", "reinforcement", "objectives"):
        tree = ast.parse((SIM_DIR / (mod + ".py")).read_text())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                names.update(node.names)
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, (ast.List, ast.Dict, ast.Set, ast.Call)):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and not tgt.id.isupper():
                        names.add(tgt.id)
        if names:
            found[mod] = names
    return found


class _NoRandom:
    def __init__(self, where):
        self.where = where

    def __call__(self, *a, **k):
        raise AssertionError("unseeded random drawn by the Python during a parity scene (%s)" % self.where)


@contextlib.contextmanager
def _forbid_global_random():
    names = ("random", "uniform", "randint", "randrange", "choice", "shuffle", "gauss", "sample")
    saved = {n: getattr(random, n) for n in names}
    for n in names:
        setattr(random, n, _NoRandom("random." + n))
    try:
        yield
    finally:
        for n, f in saved.items():
            setattr(random, n, f)


def _build_map(ns, name):
    if name == "open":
        return ns.test_maps.open_field()
    if name == "wall":
        return ns.test_obstacle_navigation._build_wall_map()
    raise ValueError("unknown map %r" % name)


def _stats(ns, type_name):
    if type_name in CUSTOM_TYPES:
        s = dict(CUSTOM_TYPES[type_name])
        s["category"] = ("Strike", "Line", "Siege")[s["category"]]
        return s
    return None


def _frame(ns, store, n):
    rows = []
    for uid in range(n):
        alive = bool(store.alive[uid])
        tgt = int(store.auto_engage_target[uid])
        if not alive or tgt < 0 or not store.alive[tgt]:
            tgt = -1
        rows.append((alive, float(store.data[uid, ns.unit.FIELD_X]), float(store.data[uid, ns.unit.FIELD_Y]),
                     tgt, float(store.data[uid, ns.unit.FIELD_FACING_RAD]) % TWO_PI))
    return rows


def run_scene(scene, variant="stock", digits=None, reset=True):
    """Run a scene through TacticalEngine; return a Trace. reset=False leaves the module globals
    as the previous run left them (used only by the positive control that shows the reset matters)."""
    ns = load(variant, digits)
    with _sim_on_path(ns), _forbid_global_random():
        if reset:
            reset_globals(ns)
        tmap = _build_map(ns, scene.map)
        store = ns.unit.UnitStore()
        for type_name, faction, x, y in scene.units:
            uid = store.spawn(type_name, faction, x, y, stats=_stats(ns, type_name))
            assert uid >= 0
        engine = ns.tactical_engine.TacticalEngine(tmap, store, seed=1)
        engine.enable_reinforcement = False
        for tick, verb, uids, x, y in scene.orders:
            engine.command_queue.add(ns.command.Command(
                tick=tick, type=verb, unit_ids=list(uids), params={"target_x": x, "target_y": y}))
        n = len(scene.units)
        trace = Trace(scene.name, "python:" + variant + ("" if digits is None else str(digits)))
        trace.frames.append(_frame(ns, store, n))
        sink = io.StringIO()     # facing.py prints a debug line every 60 ticks
        with contextlib.redirect_stdout(sink):
            for _ in range(scene.ticks):
                engine.step()
                trace.frames.append(_frame(ns, store, n))
    return trace


def python_stats(type_name):
    """Stats of a unit type as the Python has them (name -> dict), for the stats-match check."""
    ns = load("stock")
    if type_name in CUSTOM_TYPES:
        return dict(CUSTOM_TYPES[type_name])
    return dict(ns.config.UNIT_STATS[type_name])
