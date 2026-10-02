"""Fixed set of fights whose unit-state hashes are recorded NOW on the unchanged
engine (plan docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md,
verification item 4: "With the two movement switches at 0 the recorded hashes are
unchanged (the baseline)"; skill-lab cascade section 3 invariant, "record, before
touching csrc/, a file of hashes over the unit states of a fixed set of fights").

Shared by test_baseline_hashes.py (compare) and the recorder:

    make libouroboros.so build/O0/libouroboros.so build/O2/libouroboros.so
    python3 tests/csim/parity/baseline/baseline_fights.py --generate

which writes baseline_hashes.json beside this file from the O2 build. Regenerate it
ONLY from a build whose behaviour is the reference one (the commit this file was
recorded on, or, after a deliberate change, once per wave with a ledger row).

Hash of one fight: sha256 rolled over every tick of the fight, each tick one record
per spawned unit (id, alive, x, y, hp, layer, and the target where the fixture is a
csim one) packed as exact little-endian doubles. Stored per fight: tick count, the
final digest, and the rolling digest at every CHECKPOINT_EVERY ticks (so a drift can
be placed). No wall clock, no unseeded random: positions come from the skill lab's
seeded shifts (random.Random(seed)) and fixed grids.

Three groups of fights:
  skilllab_*   the three skill-lab controls (mirror 16v16, numbers 16v8, planted
               damage 16v16) through scripts.skilllab (plays, fight setup helpers),
               two (seed, spawn order) cells each.
  a99_*        two tests/csim A99 scenarios (full mission map, real generator),
               built and hashed with tests/csim/a99_tactical_runs.py's own helpers.
  fixture_*    three hand-built tactical fixtures of this file: a wall with a gap
               (density cells and obstacle discs, group move and attack-move), a
               mixed-speed march (slowest-member cap, abilities on), a cover standoff.
"""
import ctypes
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
DATA = HERE / "baseline_hashes.json"
CHECKPOINT_EVERY = 100
OM_TP_PURSUE_BY_STEERING = 0   # enum om_tac_param, csrc/ouroboros_sim.h
OM_TP_ROUTE_AROUND_TERRAIN = 1
SKILLLAB_MAX_TICKS = 2500
SKILLLAB_TAIL_TICKS = 20

LIB = {
    "O0": REPO / "build" / "O0" / "libouroboros.so",
    "O2": REPO / "build" / "O2" / "libouroboros.so",
}


def build_libs():
    """Make both fixed-optimisation libraries (Makefile targets build/O0 and build/O2)."""
    subprocess.run(["make", "-s", "build/O0/libouroboros.so", "build/O2/libouroboros.so"],
                   cwd=REPO, check=True, capture_output=True, text=True)


def _csim_conftest():
    """tests/csim/conftest.py under a private module name (never `conftest`: a sibling
    conftest in another directory would otherwise shadow it in sys.modules)."""
    name = "_baseline_csim_conftest"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "tests" / "csim" / "conftest.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _a99():
    sys.path.insert(0, str(REPO / "tests" / "csim"))
    try:
        import a99_tactical_runs
    finally:
        sys.path.remove(str(REPO / "tests" / "csim"))
    return a99_tactical_runs


def csim_handle(lib_path):
    """A ctypes handle on lib_path bound the way tests/csim binds the library."""
    csim = _csim_conftest()
    h = ctypes.CDLL(str(lib_path))
    csim._configure_common(h)
    csim._bind_generated(h)
    return h


def apply_baseline_settings(lib, w):
    """The one place the two movement switches are set to 0 (OM_TP_PURSUE_BY_STEERING and
    OM_TP_ROUTE_AROUND_TERRAIN, plan Phase A/C), through om_tactical_set_param, so the recorded
    hashes are checked in baseline mode. Every runner below calls this right after the world is
    built. The ungated fixes G04, G15 and P9 still change a few fights (see baseline_hashes.json)."""
    lib.om_tactical_set_param.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_double]
    lib.om_tactical_set_param.restype = ctypes.c_int
    for p in (OM_TP_PURSUE_BY_STEERING, OM_TP_ROUTE_AROUND_TERRAIN):
        lib.om_tactical_set_param(w, p, 0.0)


class _Roller:
    """Rolling sha256 over per-tick unit records."""

    def __init__(self):
        self.h = hashlib.sha256()
        self.ticks = 0
        self.checkpoints = []

    def tick(self, records):
        buf = bytearray()
        for rec in records:
            buf += struct.pack("<IIdddiI", *rec)
        self.h.update(bytes(buf))
        self.ticks += 1
        if self.ticks % CHECKPOINT_EVERY == 0:
            self.checkpoints.append(self.h.copy().hexdigest()[:16])

    def result(self):
        return {"ticks": self.ticks, "final": self.h.hexdigest(), "checkpoints": self.checkpoints}


# --------------------------------------------------------------------- skill lab

def _skilllab_setups():
    """{name: (build_fn, enemy_heads, seed, swap)} for the three controls, two cells each."""
    from scripts.skilllab import plays
    size = 16
    controls = {
        "mirror": (plays.blob_play(size), 16),
        "numbers": (plays.blob_play(size), 8),
        "planted": (plays.damage_play(size), 16),
    }
    out = {}
    for label, (build, enemy) in controls.items():
        out[f"skilllab_{label}_s0"] = (build, enemy, 0, False)
        out[f"skilllab_{label}_s1_swap"] = (build, enemy, 1, True)
    return out


def run_skilllab(lib_path, name):
    from scripts.skilllab import fight as F
    from scripts.skilllab.engine import Engine
    build, enemy, seed, swap = _skilllab_setups()[name]
    setup = build(enemy, swap)
    eng = Engine(lib_path)
    w = eng.new_world(seed)
    try:
        apply_baseline_settings(eng._lib, w)
        if not setup.abilities:
            eng.disable_abilities(w)
        types = F._register_types(eng, w, setup)
        import random
        rng, ids_by_group, ranges = random.Random(seed), {}, {}
        for side in ((1, 0) if swap else (0, 1)):
            F._spawn_side(eng, w, setup, side, types, rng, ids_by_group, ranges)
        F._issue_orders(eng, w, setup, ids_by_group)
        side_ids = tuple([u for gi, g in enumerate(setup.groups) if g.side == s for u in ids_by_group[gi]]
                         for s in (0, 1))
        everyone = [u for ids in side_ids for u in ids]
        roll = _Roller()
        tail = None
        for t in range(SKILLLAB_MAX_TICKS):
            eng.step(w)
            roll.tick([(u, int(eng.unit_alive(w, u)), *eng.unit_pos(w, u), eng.unit_hp(w, u),
                        eng.unit_layer(w, u), 0) for u in everyone])
            alive = [sum(1 for u in ids if eng.unit_alive(w, u)) for ids in side_ids]
            if tail is None and 0 in alive:
                tail = SKILLLAB_TAIL_TICKS
            if tail is not None:
                tail -= 1
                if tail <= 0:
                    break
        return roll.result()
    finally:
        eng.free_world(w)


# ------------------------------------------------------------------- a99 fixtures

A99_RUNS = ("fight_502_gap100", "fight_990_gap300")


def run_a99(lib_path, name):
    a = _a99()
    lib = csim_handle(lib_path)
    _, units, gap, steps, _tier = next(r for r in a.RUNS if r[0] == name)
    w = a.build(lib, units)
    apply_baseline_settings(lib, w)
    ids = a._slots(lib, w)
    if gap is not None:
        a.stage_fight(lib, w, ids, gap)
    roll = _Roller()
    for _ in range(steps):
        lib.om_tactical_step(w)
        roll.tick(_records(lib, w, a._slots(lib, w)))
    lib.om_world_free(w)
    return roll.result()


# ----------------------------------------------------------- hand-built fixtures

def _records(lib, w, ids):
    out = []
    for u in ids:
        x, y = lib.om_unit_get_pos(w, u)
        out.append((u, int(lib.om_unit_alive(w, u)), x, y, lib.om_unit_get_hp(w, u),
                    lib.om_unit_get_layer(w, u), lib.om_unit_get_target(w, u)))
    return out


def _world(lib, seed):
    csim = _csim_conftest()
    w = lib.om_world_new(1, seed)
    for feat in range(9):
        lib.om_world_set_feature(w, feat, 0)
    assert csim.OMFeature.TACTICAL == 8
    apply_baseline_settings(lib, w)
    return w


def _block(lib, w, utype, faction, n, cols, x0, y0, spacing=30.0):
    ids = []
    for i in range(n):
        ids.append(lib.om_unit_spawn(w, utype, faction, x0 + (i % cols) * spacing,
                                     y0 + (i // cols) * spacing, 0))
    return ids


def _order(lib, fn, w, ids, x, y):
    arr = (ctypes.c_uint32 * len(ids))(*ids)
    return fn(w, arr, len(ids), x, y)


RAIDER, INTERCEPTOR, VANGUARD, WARDEN, BOMBARD, BASTION = 0, 1, 2, 3, 4, 5


def _fixture_wall_gap(lib):
    """A wall of blocked density cells at x 5000..5100 with a 500 wu gap, plus obstacle
    discs and one cover disc; 24 Vanguards attack-move through it at 24 Raiders."""
    w = _world(lib, 20261002)
    cell = 100
    for cy in range(0, 60):
        if 26 <= cy <= 30:
            continue
        lib.om_map_set_obstacle_density(w, 50, cy, 0, 1.0)
    lib.om_map_add_obstacle(w, 3600.0, 2400.0, 90.0)
    lib.om_map_add_obstacle(w, 6400.0, 3400.0, 90.0)
    lib.om_map_add_cover(w, 6800.0, 2900.0, 80.0, 1.0)
    a = _block(lib, w, VANGUARD, 0, 24, 6, 3000.0, 2800.0)
    b = _block(lib, w, RAIDER, 1, 24, 6, 7000.0, 2800.0)
    _order(lib, lib.om_command_attack_move, w, a, 7100.0, 2900.0)
    _order(lib, lib.om_command_group_move, w, b, 5050.0, 2850.0)
    return w, cell, 900


def _fixture_mixed_march(lib):
    """Mixed speeds (Raider, Vanguard, Bombard) in one group each side, abilities on."""
    w = _world(lib, 20261003)
    a = (_block(lib, w, RAIDER, 0, 20, 5, 1000.0, 1000.0) + _block(lib, w, VANGUARD, 0, 20, 5, 1000.0, 1200.0)
         + _block(lib, w, BOMBARD, 0, 10, 5, 1000.0, 1400.0))
    b = (_block(lib, w, VANGUARD, 1, 25, 5, 4200.0, 1000.0) + _block(lib, w, WARDEN, 1, 5, 5, 4200.0, 1200.0)
         + _block(lib, w, BASTION, 1, 5, 5, 4200.0, 1300.0))
    _order(lib, lib.om_command_attack_move, w, a, 4300.0, 1100.0)
    _order(lib, lib.om_command_attack_move, w, b, 1100.0, 1100.0)
    return w, 100, 1000


def _fixture_cover_standoff(lib):
    """Two lines with three cover discs between them, one side on hold (idle), one marching."""
    w = _world(lib, 20261004)
    lib.om_tactical_disable_abilities(w)
    for cx, cy in ((2000.0, 1000.0), (2000.0, 1100.0), (2000.0, 1200.0)):
        lib.om_map_add_cover(w, cx, cy, 60.0, 1.0)
    a = _block(lib, w, BOMBARD, 0, 12, 12, 1000.0, 1100.0, spacing=25.0)
    b = _block(lib, w, VANGUARD, 1, 18, 9, 3000.0, 1050.0)
    _order(lib, lib.om_command_attack_move, w, b, 1000.0, 1100.0)
    return w, 100, 700


FIXTURES = {
    "fixture_wall_gap": _fixture_wall_gap,
    "fixture_mixed_march": _fixture_mixed_march,
    "fixture_cover_standoff": _fixture_cover_standoff,
}


def run_fixture(lib_path, name):
    lib = csim_handle(lib_path)
    w, _cell, steps = FIXTURES[name](lib)
    roll = _Roller()
    ids = sorted(u for u in range(1, lib.om_unit_count(w) + 1))
    for _ in range(steps):
        lib.om_tactical_step(w)
        roll.tick(_records(lib, w, ids))
    lib.om_world_free(w)
    return roll.result()


# ------------------------------------------------------------------------ driver

def all_names():
    return list(_skilllab_setups()) + [f"a99_{n}" for n in A99_RUNS] + list(FIXTURES)


def run_one(lib_path, name):
    if name.startswith("skilllab_"):
        return run_skilllab(lib_path, name)
    if name.startswith("a99_"):
        return run_a99(lib_path, name[len("a99_"):])
    return run_fixture(lib_path, name)


def run_all(lib_path):
    return {name: run_one(lib_path, name) for name in all_names()}


def load_recorded():
    return json.loads(DATA.read_text())


if __name__ == "__main__":
    sys.path.insert(0, str(REPO))
    if "--generate" not in sys.argv:
        sys.exit("pass --generate to record baseline_hashes.json from the O2 build")
    build_libs()
    got = run_all(LIB["O2"])
    DATA.write_text(json.dumps(got, indent=1, sort_keys=True) + "\n")
    for n, r in got.items():
        print(n, r["ticks"], r["final"][:16])
