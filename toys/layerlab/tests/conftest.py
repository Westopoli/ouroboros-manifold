"""Pytest session setup for the layer lab: put toys/layerlab on sys.path and build the library once.

Run from toys/layerlab/ (SPEC.md section 10). A failed make aborts the whole session loudly.
"""
import subprocess
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent.parent

if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))


def pytest_sessionstart(session):
    proc = subprocess.run(["make"], cwd=LAB, capture_output=True, text=True)
    if proc.returncode != 0:
        raise pytest.UsageError(
            "make failed in %s (rc=%d)\n--- stdout ---\n%s\n--- stderr ---\n%s"
            % (LAB, proc.returncode, proc.stdout, proc.stderr)
        )


@pytest.fixture(scope="session")
def lab_dir():
    return LAB


@pytest.fixture(scope="session")
def scenarios_dir():
    return LAB / "scenarios"


# ---------------------------------------------------------------------------
# R1 helpers (appended). Scenario builders and trace decoders for the layer tests.
# layerlab is imported lazily so that conftest import never needs the built library.
# ---------------------------------------------------------------------------
import copy  # noqa: E402
from types import SimpleNamespace  # noqa: E402

import numpy as np  # noqa: E402


def make_scenario(groups=(), *, terrain=None, rules=None, run=None):
    """Load scenarios/base.toml and append `groups` (list of group dicts, see grp()).

    `terrain`, `rules` and `run` are dicts merged over the base tables (top-level keys only,
    so a list such as rules["range_mult"] is replaced whole). Returns a plain nested dict.
    """
    from layerlab import scenario

    scn = scenario.load(str(LAB / "scenarios" / "base.toml"))
    scn["groups"] = [copy.deepcopy(dict(g)) for g in groups]
    for table, over in (("terrain", terrain), ("rules", rules), ("run", run)):
        if over:
            scn.setdefault(table, {}).update(copy.deepcopy(over))
    return scn


def add_type(scn, name, base, **over):
    """Add a unit type `name` copied from type `base` with field overrides. Returns scn."""
    scn["types"][name] = {**scn["types"][base], **over}
    return scn


def grp(side, type_, x, y, layer, count=1, **kw):
    """One scenario group dict. Defaults: hold order, line formation, facing 0. Extra keys
    (order, goal, pre_revealed, transfer_layer, transfer_tick, pulse_tick, ...) pass through."""
    g = {"side": side, "type": type_, "count": count, "x": float(x), "y": float(y),
         "layer": layer, "order": "hold", "formation": "line", "facing": 0.0}
    g.update(kw)
    return g


def table9(**by_offset):
    """A 9-entry signed-offset table, all zero except the given offsets. Keys are offsets as
    strings 'm4'..'m1', 'z', 'p1'..'p4' (target layer minus source layer), e.g. table9(z=1, p1=1)."""
    names = {"m4": 0, "m3": 1, "m2": 2, "m1": 3, "z": 4, "p1": 5, "p2": 6, "p3": 7, "p4": 8}
    t = [0.0] * 9
    for k, v in by_offset.items():
        t[names[k]] = float(v)
    return t


def decode_flags(flags):
    """Decode ll_trace_rec.flags (scalar or array): bit0 changing layer, bit1 fired this tick,
    bit2 on a slope, bit3 visible to the other side."""
    f = np.asarray(flags).astype(np.uint8)
    return SimpleNamespace(changing=(f & 1) != 0, fired=(f & 2) != 0,
                           on_slope=(f & 4) != 0, visible=(f & 8) != 0)


def unit_trace(res, i):
    """Per-tick arrays for unit i from a run(..., trace=True) result: x y hp progress layer
    side alive plus the decoded flag arrays changing / fired / on_slope / visible."""
    assert res.trace is not None, "run(..., trace=True) is required"
    col = res.trace[:, i]
    out = decode_flags(col["flags"])
    out.x, out.y, out.hp, out.progress = (col[k].astype(np.float64) for k in ("x", "y", "hp", "progress"))
    out.layer, out.side, out.alive = col["layer"].astype(int), col["side"].astype(int), col["alive"].astype(int)
    return out


def fire_ticks(res, i):
    """Tick indices on which unit i fired (trace flag bit1)."""
    return np.flatnonzero(unit_trace(res, i).fired)


def any_in(ticks, lo, hi):
    """True if any tick in the integer array `ticks` lies in [lo, hi] inclusive."""
    t = np.asarray(ticks)
    return bool(((t >= lo) & (t <= hi)).any())
