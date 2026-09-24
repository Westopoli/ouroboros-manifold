"""Shared helpers for the scale suite (docs/bible/epics/E-*.md "Scale
requirements" sections). Deliberately NOT named conftest.py and imported by
the story test files as `from ._scale_helpers import ...` (a relative
import: this directory is a package, __init__.py present, specifically so
its own conftest.py does not collide with tests/csim/conftest.py's module
identity -- see conftest.py's docstring for what broke and why). The
directory's actual conftest.py carries only the OM_SCALE gate and the
`scale` marker.

Library build: tests/csim/conftest.py's `lib`/`dbg` fixtures load
libouroboros.so / libouroboros_dbg.so from the repo root, built by `make -s
libouroboros.so libouroboros_dbg.so`. Per the Makefile, OPT defaults to -O2
and the top-level libouroboros*.so targets use the same CFLAGS
(CFLAGS_COMMON + $(OPT) + CFLAGS_DET_BASE) as the fixed build/O2/*.so
targets -- sha256 verified byte-identical on 2026-09-24. There is nothing
for this file to override: `lib`/`dbg` already load the -O2 deterministic
build with no env var needed. `make build/O2/libouroboros.so
build/O2/libouroboros_dbg.so` is still built alongside (see the leaf report)
as the named artifact the task asked for; it is the same bytes.

Helpers (OMTier, OMField, OMFeature, OMArchetype, set_region, generate, ...)
are borrowed from tests/csim/conftest.py by executing that file under a
private module name (never "conftest"). tests/csim/conftest.py itself is
never imported normally, edited, or written to -- only read via this
file-local exec, which is the only way to reach its plain helper functions
from a nested pytest rootpath without touching it.
"""
import importlib.util
import math
import os
import pathlib
import time

_PARENT_CONFTEST_PATH = pathlib.Path(__file__).resolve().parents[1] / "conftest.py"
_spec = importlib.util.spec_from_file_location("_om_scale_borrowed_conftest", _PARENT_CONFTEST_PATH)
_parent = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_parent)

REPO_ROOT = _parent.REPO_ROOT
LIB_PATH = _parent.LIB_PATH
DBG_LIB_PATH = _parent.DBG_LIB_PATH

OMField = _parent.OMField
OMComposite = _parent.OMComposite
OMTier = _parent.OMTier
OMFeature = _parent.OMFeature
OMArchetype = _parent.OMArchetype
OMStance = _parent.OMStance
OMEdge = _parent.OMEdge
OMAction = _parent.OMAction
OMMode = _parent.OMMode
OMTemplate = _parent.OMTemplate

set_region = _parent.set_region
generate = _parent.generate
gen_set_region_range = _parent.gen_set_region_range
gen_set_faction_count = _parent.gen_set_faction_count
gen_set_extra_edges_enabled = _parent.gen_set_extra_edges_enabled
isolate_agents = _parent.isolate_agents
set_faction = _parent.set_faction
set_stance = _parent.set_stance
set_owner = _parent.set_owner
set_edge = _parent.set_edge
force_draws = _parent.force_draws
isolate_events = _parent.isolate_events
load_launch_events = _parent.load_launch_events


def all_features_off(lib, w):
    """Every om_feature switched off -- the scale suite turns on only the
    feature(s) its own epic's tick step needs, so a tick's measured cost is
    that epic's step alone (mirrors isolate_agents / isolate_events for the
    epics that have no such helper yet in the parent conftest)."""
    for feat in (OMFeature.EVENTS, OMFeature.FACTIONS, OMFeature.FRICTION,
                 OMFeature.ADMIN_REVOLTS, OMFeature.DIPLOMACY, OMFeature.TECHNOLOGY,
                 OMFeature.DRIFT, OMFeature.LIFECYCLE, OMFeature.TACTICAL):
        lib.om_world_set_feature(w, feat, 0)


def raw_world(lib, n_regions, seed, features=()):
    """A world with exactly `features` on and everything else off -- the
    scale suite's own fixture builder, independent of world_factory's
    filename-sniffed epic (these files are named test_scale_E##, which
    world_factory's `test_e##_` regex does not match)."""
    w = lib.om_world_new(n_regions, seed)
    assert w, "om_world_new returned NULL"
    all_features_off(lib, w)
    for feat in features:
        lib.om_world_set_feature(w, feat, 1)
    return w


def median_ns(op, n=100, warmup=5):
    """Warm up `warmup` calls, then return the MEDIAN wall time of `n` further
    calls to `op()`, in nanoseconds (time.perf_counter_ns, per the brief)."""
    for _ in range(warmup):
        op()
    samples = []
    for _ in range(n):
        t0 = time.perf_counter_ns()
        op()
        t1 = time.perf_counter_ns()
        samples.append(t1 - t0)
    samples.sort()
    mid = len(samples) // 2
    if len(samples) % 2:
        return float(samples[mid])
    return (samples[mid - 1] + samples[mid]) / 2.0


def median_ns_with_setup(setup, op, n=100, warmup=5):
    """Like median_ns, but `setup()` runs (untimed) immediately before each
    timed call to `op()` -- for an op whose state is consumed/cleared by one
    call (e.g. chronicle distillation) and must be refilled every iteration."""
    for _ in range(warmup):
        setup()
        op()
    samples = []
    for _ in range(n):
        setup()
        t0 = time.perf_counter_ns()
        op()
        t1 = time.perf_counter_ns()
        samples.append(t1 - t0)
    samples.sort()
    mid = len(samples) // 2
    if len(samples) % 2:
        return float(samples[mid])
    return (samples[mid - 1] + samples[mid]) / 2.0


CANVAS = 24000.0


def spawn_grid(lib, w, n, faction_id, unit_type, layer=0):
    """n units in a grid spanning the 24000 wu canvas (the brief's build
    recipe for the tactical scale epics), evenly split faction/layer as
    passed by the caller."""
    cols = max(1, math.ceil(math.sqrt(n)))
    spacing = CANVAS / cols
    ids = []
    for i in range(n):
        gx, gy = i % cols, i // cols
        x = spacing * 0.5 + gx * spacing
        y = spacing * 0.5 + gy * spacing
        ids.append(lib.om_unit_spawn(w, unit_type, faction_id, x, y, layer))
    return ids


OM_SCALE_CPU_FACTOR = float(os.environ.get("OM_SCALE_CPU_FACTOR", "1.35"))
# The bible's Scale requirements budgets are set for the min-spec machine
# (Ryzen 5 1600 / i5-7600 class); this suite runs on the forge (Ryzen 7
# 3700X), which is faster single-thread by roughly this factor. A raw median
# is compared against budget/OM_SCALE_CPU_FACTOR, not the bare budget, so a
# forge pass means the min-spec machine is expected to clear the real budget.
# A run on the actual min-spec machine sets OM_SCALE_CPU_FACTOR=1.0. See
# tests/csim/scale/README.md.


def scaled_budget_ns(budget_ns):
    return budget_ns / OM_SCALE_CPU_FACTOR


def assert_budget(measured_ns, budget_ns, label):
    """The real per-file assertion: measured (forge, raw) against the
    min-spec budget scaled down by OM_SCALE_CPU_FACTOR for this machine."""
    scaled = scaled_budget_ns(budget_ns)
    print(
        f"[scale] {label}: raw_median={measured_ns / 1000.0:.3f}us "
        f"budget={budget_ns / 1000.0:.3f}us scaled_budget={scaled / 1000.0:.3f}us "
        f"factor={OM_SCALE_CPU_FACTOR} verdict={'PASS' if measured_ns <= scaled else 'FAIL'}"
    )
    assert measured_ns <= scaled, (
        f"{label}: raw median {measured_ns / 1000.0:.3f}us exceeds the min-spec budget "
        f"{budget_ns / 1000.0:.3f}us scaled to {scaled / 1000.0:.3f}us on this machine "
        f"(OM_SCALE_CPU_FACTOR={OM_SCALE_CPU_FACTOR})"
    )


def assert_control_violates_budget(measured_ns, budget_ns, label, divisor=100):
    """Positive control: the SAME scaled budget this file's real assertion
    uses, tightened by `divisor`, must be violated by `measured_ns` -- proof
    the clock and the assertion are live, not that the op is fast."""
    control_budget = scaled_budget_ns(budget_ns) / divisor
    print(
        f"[scale-control] {label}: raw_median={measured_ns / 1000.0:.3f}us "
        f"control_budget={control_budget / 1000.0:.3f}us (budget/{divisor}, scaled) "
        f"verdict={'DETECTED (exceeds control budget, as expected)' if measured_ns >= control_budget else 'CONTROL DID NOT TRIP'}"
    )
    assert measured_ns >= control_budget, (
        f"{label}: control expected to exceed {control_budget / 1000.0:.3f}us "
        f"(budget/{divisor}) but measured only {measured_ns / 1000.0:.3f}us -- "
        "the clock or the assertion is not live"
    )
