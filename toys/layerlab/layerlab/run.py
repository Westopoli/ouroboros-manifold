"""Run one engagement through the C library (SPEC.md section 8)."""
import ctypes as C
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from . import ffi
from .scenario import to_c

_TRACE_DTYPE = np.dtype([
    ("x", "<f4"), ("y", "<f4"), ("hp", "<f4"), ("progress", "<f4"),
    ("layer", "u1"), ("side", "u1"), ("alive", "u1"), ("flags", "u1"),
])
assert _TRACE_DTYPE.itemsize == C.sizeof(ffi.ll_trace_rec)


@dataclass
class Result:
    winner: int
    ticks: int
    survivors: tuple
    hp_ratio: tuple
    cost_lost: tuple
    damage_dealt: tuple
    shots: tuple
    transitions: int
    first_shot_side: int
    first_shot_tick: int
    first_contact_tick: int
    unanswered_ticks: tuple
    alive_ticks: tuple
    firing_ticks: tuple
    firing_weight: tuple
    alerted_tick: tuple
    alerts: tuple
    alert_dir_x: tuple
    alert_dir_y: tuple
    unit: list
    trace: Any = field(default=None, repr=False)
    raw: bytes = field(default=b"", repr=False)


def run(scn, seed=0, trace=False, lib="O2"):
    dll = ffi.load_lib(lib)
    sc = to_c(scn)
    out = ffi.ll_result()
    n = sc.n_spawns
    tr = buf = None
    if trace:
        cap = sc.rules.max_ticks
        buf = (ffi.ll_trace_rec * max(1, cap * n))()
        tr = ffi.ll_trace(buf=C.cast(buf, C.POINTER(ffi.ll_trace_rec)), capacity_ticks=cap, ticks_written=0)
    rc = dll.ll_run(C.byref(sc), seed, C.byref(out), C.byref(tr) if tr is not None else None)
    if rc != 0:
        msg = dll.ll_last_error()
        raise RuntimeError("ll_run failed (%d): %s" % (rc, msg.decode() if msg else ""))
    trace_arr = None
    if trace:
        t = tr.ticks_written
        trace_arr = np.frombuffer(buf, dtype=_TRACE_DTYPE, count=t * n).reshape(t, n).copy()
    units = [
        {"x": u.x, "y": u.y, "hp": u.hp, "layer": u.layer, "alive": u.alive, "transitions": u.transitions}
        for u in out.unit[:n]
    ]
    return Result(
        winner=out.winner, ticks=out.ticks,
        survivors=tuple(out.survivors), hp_ratio=tuple(out.hp_ratio),
        cost_lost=tuple(out.cost_lost), damage_dealt=tuple(out.damage_dealt),
        shots=tuple(out.shots), transitions=out.transitions,
        first_shot_side=out.first_shot_side, first_shot_tick=out.first_shot_tick,
        first_contact_tick=out.first_contact_tick,
        unanswered_ticks=tuple(out.unanswered_ticks), alive_ticks=tuple(out.alive_ticks),
        firing_ticks=tuple(out.firing_ticks), firing_weight=tuple(out.firing_weight),
        alerted_tick=tuple(out.alerted_tick), alerts=tuple(out.alerts),
        alert_dir_x=tuple(out.alert_dir_x), alert_dir_y=tuple(out.alert_dir_y), unit=units,
        trace=trace_arr, raw=C.string_at(C.addressof(out), C.sizeof(out)),
    )


def probe_can_see(scn, observer, target, seed=0, lib="O2"):
    dll = ffi.load_lib(lib)
    sc = to_c(scn)
    rc = dll.ll_probe_can_see(C.byref(sc), seed, observer, target)
    if rc < 0:
        msg = dll.ll_last_error()
        raise RuntimeError("ll_probe_can_see failed (%d): %s" % (rc, msg.decode() if msg else ""))
    return bool(rc)
