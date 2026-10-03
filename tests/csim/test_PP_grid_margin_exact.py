"""R-097-10 / ALG-68 (docs/bible/algorithms.md): the movement grid is a speed
device only; "a grid setting must only change speed, never results". This test
builds the sim twice from a temporary copy of csrc/ -- once as committed, once
with OM_MOVE_GRID_MARGIN (csrc/tactical_move.c) replaced -- runs the same
battle and demands byte-identical unit positions and hp every tick.

Cause it guards (found 2026-10-03, profile of test_scale_E13_dense_moving):
om_move_grid_set refiles the grid mid-tick (om_move_grid_rebuild, from_units=0)
when the spill list fills; the rebuild files units by their CURRENT position
and resets grid_disp to 0, but om_move_probe_gather_start looks them up by
START-of-tick position, so the steering probe misses neighbours (ALG-68: "each
read at its start-of-tick position"). A smaller margin fills the spill list
sooner. The scene is one engagement, 100 v 100, margin 0.1 x radius: the
smallest scene found that shows it (1,250 units at 0.5 x radius).

Red while the defect stands. The committed margin itself is not the subject;
any margin must give the same results.
"""
import ctypes
import hashlib
import math
import pathlib
import re
import shutil
import struct
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
MARGIN_RE = re.compile(r"^#define OM_MOVE_GRID_MARGIN .*$", re.M)
ALT_MARGIN = "(0.1 * OM_UNIT_COLLISION_RADIUS)"
# Same flags as the Makefile's release build (CFLAGS_COMMON + CFLAGS_DET_BASE, -O2).
FLAGS = ["-std=c11", "-fPIC", "-O2", "-fno-fast-math", "-ffp-contract=off",
         "-fexcess-precision=standard", "-msse2", "-mfpmath=sse", "-fno-math-errno"]
SEED = 2026091413
SPACING = 30.0
GAP = 600.0
N_PER_SIDE = 100
TICKS = 100


class Vec2(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


def _build(tmp, name, margin):
    src = tmp / name
    shutil.copytree(REPO / "csrc", src, ignore=shutil.ignore_patterns("pipe"))
    if margin is not None:
        f = src / "tactical_move.c"
        text, n = MARGIN_RE.subn("#define OM_MOVE_GRID_MARGIN " + margin, f.read_text())
        assert n == 1, "OM_MOVE_GRID_MARGIN define not found exactly once in tactical_move.c"
        f.write_text(text)
    out = tmp / f"lib_{name}.so"
    res = subprocess.run(["cc", *FLAGS, "-I", str(src), "-shared", "-o", str(out),
                          *sorted(str(p) for p in src.glob("*.c")), "-lm"],
                         capture_output=True, text=True)
    assert res.returncode == 0, res.stderr[-3000:]
    return out


def _load(path):
    h = ctypes.CDLL(str(path))
    h.om_world_new.argtypes = [ctypes.c_uint32, ctypes.c_uint64]
    h.om_world_new.restype = ctypes.c_void_p
    h.om_world_free.argtypes = [ctypes.c_void_p]
    h.om_world_set_feature.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    h.om_unit_spawn.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int32,
                                ctypes.c_double, ctypes.c_double, ctypes.c_uint32]
    h.om_unit_spawn.restype = ctypes.c_uint32
    h.om_command_group_move.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32),
                                        ctypes.c_uint32, ctypes.c_double, ctypes.c_double]
    h.om_tactical_step.argtypes = [ctypes.c_void_p]
    h.om_tactical_step.restype = ctypes.c_uint64
    h.om_unit_get_position.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(Vec2)]
    h.om_unit_get_hp.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    h.om_unit_get_hp.restype = ctypes.c_double
    return h


def _run(h, n):
    """One engagement, n v n, 30 wu spacing, 600 wu gap, each side group-moved to
    the other's centre (the E-13 five-engagements scene, shrunk to one).
    Returns one digest per tick over every unit's (x, y, hp) and the raw
    last-tick vector."""
    w = h.om_world_new(1, SEED)
    for f in range(9):
        h.om_world_set_feature(w, f, 0)
    cols = math.ceil(math.sqrt(n))
    rows = -(-n // cols)
    gw, gh = cols * SPACING, rows * SPACING
    cx, cy = 4500.0, 4000.0
    ox = [cx - gw - GAP / 2, cx + GAP / 2]
    oy = cy - gh / 2
    ids = [[], []]
    for side in range(2):
        for i in range(n):
            ids[side].append(h.om_unit_spawn(
                w, 0, side, ox[side] + SPACING * 0.5 + (i % cols) * SPACING,
                oy + SPACING * 0.5 + (i // cols) * SPACING, 0))
    for side in range(2):
        sel = (ctypes.c_uint32 * n)(*ids[side])
        h.om_command_group_move(w, sel, n, ox[1 - side] + gw / 2, cy)
    flat = ids[0] + ids[1]
    digests, last = [], None
    for _ in range(TICKS):
        h.om_tactical_step(w)
        vec = []
        for u in flat:
            p = Vec2()
            h.om_unit_get_position(w, u, ctypes.byref(p))
            vec += [p.x, p.y, h.om_unit_get_hp(w, u)]
        digests.append(hashlib.sha256(struct.pack(f"{len(vec)}d", *vec)).hexdigest())
        last = vec
    h.om_world_free(w)
    return digests, last


@pytest.fixture(scope="module")
def traces(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("margin")
    base = _load(_build(tmp, "base", None))
    alt = _load(_build(tmp, "alt", ALT_MARGIN))
    return _run(base, N_PER_SIDE), _run(alt, N_PER_SIDE)


def test_grid_margin_does_not_change_results(traces):
    """R-097-10 / ALG-68: same battle, different grid margin, same positions."""
    (base, _), (alt, _) = traces
    first = next((t + 1 for t, (a, b) in enumerate(zip(base, alt)) if a != b), None)
    assert first is None, (
        f"grid margin changed results: first differing tick {first} of {TICKS} "
        f"(100 v 100 engagement, margin {ALT_MARGIN} vs committed)")


def test_detector_positive_control(traces):
    """The comparison detects a single unit moved 1e-9 in the final vector."""
    (_, vec), _ = traces
    bent = list(vec)
    bent[0] += 1e-9
    pack = lambda v: hashlib.sha256(struct.pack(f"{len(v)}d", *v)).hexdigest()
    assert pack(vec) != pack(bent)
    assert pack(vec) == pack(list(vec))
