"""Q2 (wave-2, docs/northstar/plans/briefs/2026-09-22-two-day-push.md): fenced
failing tests for the T1 tactical RTS-bug detectors. The implementation is
scripts/qa/rts_detectors.py, owned by manager M2 -- it does not exist yet, so
every test in this file is expected to fail at collection (ImportError) until
M2 lands it. That collection failure is the story's "red now" state, not a
defect in this file.

Trace contract (copied from
~/Projects/agora/runs/101-probe-a-toy-drift-20260910-1521/worktree/probe_c/detectors/rts.py,
the semantics this suite mirrors, not its code -- unchanged so the future
`om_tactical_trace_*` C reader can produce it directly):

    trace = list of ticks, each
      {"tick": int, "dt": float,
       "units": {uid: {"x", "y", "vx", "vy", "facing", "target_active", "tx", "ty"}},
       "commands": [{"uid", "tx", "ty", "ack"}]}

`uid` keys and `commands[].uid` are the same id space (int once loaded off
disk; JSON forces the `units` mapping's keys through strings on round-trip,
so `_load_trace` below casts them back). `x`/`y` are world units; `vx`/`vy`
are the unit's current velocity in wu/s; `facing` is radians; `target_active`
is true while the unit has a live move/attack-move order; `tx`/`ty` is that
order's current destination. `ack` on a command is the C sim's acceptance
code (0 = accepted, matching R-096-06's "rejected with a reason" for
anything else -- a rejected command produces no state change by design and
is not a drop).

Detector functions (`from scripts.qa.rts_detectors import rubberband, stuck,
backwards, dropped_order, run_all, fingerprint`) mirror probe C's shape
exactly: a `Finding(kind, uid, tick, detail)` dataclass, `fingerprint()`
strips digits from "kind:sorted(detail keys)" for stable cross-run dedup
(tests/qa/t1/detectors.py's own `fingerprint()` does the same thing for the
strategic-trace detectors), and `run_all(trace, speed)` returns
{detector_name: [Finding, ...]}.
"""
from __future__ import annotations

import ctypes
import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

from scripts.qa.rts_detectors import (  # noqa: E402  (expected red: module does not exist yet)
    BACKWARDS_MIN_TICKS,
    DROPPED_GRACE,
    RUBBERBAND_FACTOR,
    STUCK_MIN_DISP,
    STUCK_MIN_DIST,
    STUCK_WINDOW,
    backwards,
    dropped_order,
    fingerprint,
    run_all,
    rubberband,
    stuck,
)

# R-099-02: "a Raider covers 150 wu/s at 20 ticks per second, 7.5 wu per
# tick." Used as the `speed` argument every fixture's velocities are built
# against, so RUBBERBAND_FACTOR's expected value traces to a real rule.
RAIDER_SPEED_WU_S = 150.0


def _load_trace(name: str) -> list[dict]:
    with (FIXTURES_DIR / f"{name}.json").open() as f:
        raw = json.load(f)
    for t in raw:
        t["units"] = {int(uid): u for uid, u in t["units"].items()}
    return raw


PLANTED_FIXTURES = {
    "rubberband": "rubberband_planted",
    "stuck": "stuck_planted",
    "backwards": "backwards_planted",
    "dropped_order": "dropped_order_planted",
}


# ============================================================== thresholds ==
# Every constant's expected value is derived from a bible rule or the bug
# catalog signature it exists to detect, cited in the docstring, per
# CLAUDE.md's "Invariant modification rules": these are the values M2 is
# building to, not values discovered after the fact.

def test_rubberband_factor_traces_to_r099_02_nominal_speed():
    """R-099-02: a Raider moves 150 wu/s = 7.5 wu/tick at 20 ticks/s. The
    detector's limit is RUBBERBAND_FACTOR * speed * dt; 1.5x gives an 11.25 wu
    per-tick backward-displacement ceiling for a Raider, comfortably above
    the few wu of legitimate jitter R-097-05's collision-separation pass
    (pushed apart over up to 3 iterations per tick) can add against a unit's
    own heading, so the detector trips only on an actual snap-back, not
    steering noise. Bug catalog #1 (rubber-banding)."""
    assert RUBBERBAND_FACTOR == 1.5


def test_stuck_window_traces_to_r099_02_tick_rate():
    """R-099-02: 20 ticks per second. STUCK_WINDOW=40 ticks is a 2-second
    span: long enough that a single-tick steering wait (R-097-03, "if none
    [angle] is clear, it waits") never looks like a stall, short enough to
    catch a genuinely stuck unit inside one QA pass. Bug catalog #2."""
    assert STUCK_WINDOW == 40


def test_stuck_min_disp_is_the_near_zero_progress_floor():
    """Bug catalog #2's signature is "zero displacement over N ticks";
    0.05 wu over a 2-second window is far below any unit's slowest
    legitimate crawl (even at R-097-06's worst pre-block slowdown, d=0.7-
    epsilon, speed is still multiplied by (1 - 0.5*0.7) = 0.65, not zeroed),
    so it isolates a true zero-velocity stall from real but slow movement."""
    assert STUCK_MIN_DISP == 0.05


def test_stuck_min_dist_exceeds_r095_05_arrival_tolerance():
    """R-095-05: a move group terminates once every unit is within 1.5 x
    collision radius of its slot; R-097-05 fixes collision radius at 15 wu
    (30 wu = 2 x radius between two units), so the arrival tolerance is
    1.5 x 15 = 22.5 wu. A unit resting inside that tolerance has correctly
    arrived, not stalled. STUCK_MIN_DIST=25.0 sits just above 22.5 so an
    arrived unit is never misclassified as stuck."""
    assert STUCK_MIN_DIST == 25.0


def test_backwards_min_ticks_traces_to_r100_02_turn_rate():
    """R-100-02: turn rate is capped (6.0 rad/s Strike, 4.0 Line, 2.5
    Siege). A single-tick steering deflection (R-097-03) can point a unit's
    velocity briefly away from a facing that has not yet caught up;
    BACKWARDS_MIN_TICKS=5 (0.25 s at 20 ticks/s) requires the reversal to
    outlast one such deflection before it counts as bug catalog #3
    (backwards walking), not a normal mid-turn slew."""
    assert BACKWARDS_MIN_TICKS == 5


def test_dropped_grace_traces_to_r096_07_command_apply_order():
    """R-096-07: commands for tick t are all applied before any state
    advances, in arrival order, and recorded for replay. DROPPED_GRACE=3
    gives an accepted command three ticks to show up as the unit's new
    target before bug catalog #4 ("command acknowledged... no state change
    within N ticks") calls it dropped."""
    assert DROPPED_GRACE == 3


# ===================================================== four-way cross-check ==
# Each planted fixture plants exactly one of the four bugs; every detector
# is run against all four planted fixtures plus its own clean twin, the way
# PX-04's test_control_empty_drifts_does_not_falsely_trip_oscillator_control
# (tests/qa/t1/test_detectors.py) cross-checks its own two detectors,
# generalized here to four.

def test_rubberband_fires_only_on_its_own_planted_trace():
    """R-099-02 / bug catalog #1: a unit teleported 40 wu backward against
    its own velocity in one tick, well past RUBBERBAND_FACTOR * speed * dt
    (11.25 wu). Fires exactly once, at the right uid and tick; silent on its
    clean twin (the same unit covering its normal 7.5 wu/tick) and on the
    other three detectors' planted traces."""
    planted = _load_trace("rubberband_planted")
    clean = _load_trace("rubberband_clean")
    hits = rubberband(planted, RAIDER_SPEED_WU_S)
    assert len(hits) == 1
    assert hits[0].uid == 1
    assert hits[0].tick == 2
    assert rubberband(clean, RAIDER_SPEED_WU_S) == []
    for kind, fixture in PLANTED_FIXTURES.items():
        if kind == "rubberband":
            continue
        assert rubberband(_load_trace(fixture), RAIDER_SPEED_WU_S) == [], fixture


def test_stuck_fires_only_on_its_own_planted_trace():
    """R-095-05 / R-097-03 / bug catalog #2: a unit with target_active true
    for the whole STUCK_WINDOW (40-tick) window, displacement under
    STUCK_MIN_DISP (0.05 wu) while STUCK_MIN_DIST (25.0 wu) short of a
    target 5000 wu away. Fires exactly once, at the right uid and tick
    (the window's last tick); silent on its clean twin (the same unit
    covering 300 wu over the window at nominal Raider speed) and on the
    other three detectors' planted traces."""
    planted = _load_trace("stuck_planted")
    clean = _load_trace("stuck_clean")
    hits = stuck(planted)
    assert len(hits) == 1
    assert hits[0].uid == 2
    assert hits[0].tick == 40
    assert stuck(clean) == []
    for kind, fixture in PLANTED_FIXTURES.items():
        if kind == "stuck":
            continue
        assert stuck(_load_trace(fixture)) == [], fixture


def test_backwards_fires_only_on_its_own_planted_trace():
    """R-100-01 / R-100-02 / bug catalog #3: a unit moving at Raider speed
    with its facing fixed 180 degrees off its velocity for BACKWARDS_MIN_TICKS
    (5) consecutive ticks. Fires exactly once, at the right uid and tick
    (the 5th consecutive tick); silent on its clean twin (same motion,
    facing correctly aligned with heading per R-100-01) and on the other
    three detectors' planted traces."""
    planted = _load_trace("backwards_planted")
    clean = _load_trace("backwards_clean")
    hits = backwards(planted)
    assert len(hits) == 1
    assert hits[0].uid == 3
    assert hits[0].tick == 5
    assert backwards(clean) == []
    for kind, fixture in PLANTED_FIXTURES.items():
        if kind == "backwards":
            continue
        assert backwards(_load_trace(fixture)) == [], fixture


def test_dropped_order_fires_only_on_its_own_planted_trace():
    """R-096-06 / R-096-07 / bug catalog #4: a command accepted (ack=0) at
    tick 1, but the unit's tx/ty never adopts the commanded destination
    within DROPPED_GRACE (3) ticks. Fires exactly once, at the issuing tick;
    silent on its clean twin (the unit's target updates to match by tick 2,
    well inside the grace window) and on the other three detectors' planted
    traces."""
    planted = _load_trace("dropped_order_planted")
    clean = _load_trace("dropped_order_clean")
    hits = dropped_order(planted)
    assert len(hits) == 1
    assert hits[0].uid == 4
    assert hits[0].tick == 1
    assert dropped_order(clean) == []
    for kind, fixture in PLANTED_FIXTURES.items():
        if kind == "dropped_order":
            continue
        assert dropped_order(_load_trace(fixture)) == [], fixture


# ================================================================== run_all ==

def test_run_all_returns_the_four_detector_keys():
    """run_all's shape (mirrors tests/qa/t1/detectors.py's own run_all):
    a dict keyed by all four detector names, each an empty list on a clean
    trace. Uses the dropped_order clean twin, which is clean for all four
    detectors (verified by test_dropped_order_fires_only_on_its_own_planted_trace's
    cross-check family)."""
    findings = run_all(_load_trace("dropped_order_clean"), RAIDER_SPEED_WU_S)
    assert set(findings.keys()) == {"rubberband", "stuck", "backwards", "dropped_order"}
    assert findings["rubberband"] == []
    assert findings["stuck"] == []
    assert findings["backwards"] == []
    assert findings["dropped_order"] == []


def test_run_all_dedups_same_shaped_rubberband_findings_to_one_fingerprint():
    """Bug catalog #1: two units (uid 1 and uid 5) independently teleport
    backward against their own velocity in the same trace. Both findings
    share kind "rubberband" and the same detail keys
    (displacement/limit/dot), so fingerprint() -- which strips digits from
    "kind:sorted(detail keys)" -- collapses them to one dedup key even
    though uid and tick differ. Same finding shape twice, one fingerprint."""
    findings = run_all(_load_trace("run_all_dedup"), RAIDER_SPEED_WU_S)
    hits = findings["rubberband"]
    assert len(hits) == 2
    assert {hits[0].uid, hits[1].uid} == {1, 5}
    assert fingerprint(hits[0]) == fingerprint(hits[1])
    assert findings["stuck"] == []
    assert findings["backwards"] == []
    assert findings["dropped_order"] == []


def test_fingerprint_distinguishes_different_kinds():
    """fingerprint() must not collapse genuinely different bugs together:
    rubberband's and stuck's planted findings have different kinds and
    different detail-key sets, so their fingerprints differ."""
    rb = rubberband(_load_trace("rubberband_planted"), RAIDER_SPEED_WU_S)[0]
    st = stuck(_load_trace("stuck_planted"))[0]
    assert fingerprint(rb) != fingerprint(st)


# ============================================================ integration ==
# F5 moves this into conftest. Local until then: the real C tactical trace
# reader does not exist yet (om_tactical_step, csrc/ouroboros_sim.h:805, is
# still a stub with no trace/command API), so this bug id is not in
# csrc/ouroboros_sim.h's om_bug enum and has no OMBug mirror in
# tests/csim/conftest.py yet either.
OM_BUG_MOVE_RUBBERBAND = 1100  # local enum; F5 moves it into conftest

_INTEGRATION_TICKS = 300

_QA_T1_RTS_CSIM_CONFTEST = REPO_ROOT / "tests" / "csim" / "conftest.py"
_spec = importlib.util.spec_from_file_location("_qa_t1_rts_csim_conftest", _QA_T1_RTS_CSIM_CONFTEST)
_csim = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _csim
_spec.loader.exec_module(_csim)


def _has_tactical_trace_read() -> bool:
    if not _csim.DBG_LIB_PATH.exists():
        return False
    try:
        handle = ctypes.CDLL(str(_csim.DBG_LIB_PATH))
    except OSError:
        return False
    return hasattr(handle, "om_tactical_trace_read")


@pytest.mark.skipif(not _has_tactical_trace_read(),
                     reason="om_tactical_trace_read not yet in the C library "
                            "(om_tactical_step is still a stub, csrc/ouroboros_sim.h:805)")
def test_integration_scripted_move_is_silent_then_om_bug_move_rubberband_fires(dbg):
    """R-096-07 (a scripted move command is applied before state advances)
    and R-099-02 (nominal speed) over a real 300-tick run of the C sim's own
    tactical trace: a clean scripted move produces silence on all four
    detectors, and injecting OM_BUG_MOVE_RUBBERBAND (id 1100) makes
    `rubberband` fire. Speculative future API surface (om_tactical_*
    functions do not exist yet); the skipif above keeps this test inert
    until they do, and its call shapes are expected to need adjustment once
    B10/T1's real tactical wiring lands."""
    world = dbg.om_world_new(ctypes.c_uint32(1), ctypes.c_uint64(2026092200))
    assert world, "om_world_new returned NULL"
    unit_id = dbg.om_tactical_unit_spawn(world, ctypes.c_int(0), ctypes.c_int(0),
                                          ctypes.c_double(0.0), ctypes.c_double(0.0))
    dbg.om_tactical_command_move(world, ctypes.c_int(unit_id),
                                  ctypes.c_double(3000.0), ctypes.c_double(0.0))
    dbg.om_tactical_trace_enable(world, 1)
    ran = dbg.om_world_run(world, ctypes.c_uint64(_INTEGRATION_TICKS))
    assert ran == _INTEGRATION_TICKS
    trace = dbg.om_tactical_trace_read(world)
    findings = run_all(trace, RAIDER_SPEED_WU_S)
    assert findings["rubberband"] == []
    assert findings["stuck"] == []
    assert findings["backwards"] == []
    assert findings["dropped_order"] == []
    dbg.om_world_free(world)

    world2 = dbg.om_world_new(ctypes.c_uint32(1), ctypes.c_uint64(2026092200))
    dbg.om_debug_inject(world2, ctypes.c_int(OM_BUG_MOVE_RUBBERBAND))
    unit_id2 = dbg.om_tactical_unit_spawn(world2, ctypes.c_int(0), ctypes.c_int(0),
                                           ctypes.c_double(0.0), ctypes.c_double(0.0))
    dbg.om_tactical_command_move(world2, ctypes.c_int(unit_id2),
                                  ctypes.c_double(3000.0), ctypes.c_double(0.0))
    dbg.om_tactical_trace_enable(world2, 1)
    dbg.om_world_run(world2, ctypes.c_uint64(_INTEGRATION_TICKS))
    bug_trace = dbg.om_tactical_trace_read(world2)
    bug_findings = run_all(bug_trace, RAIDER_SPEED_WU_S)
    assert bug_findings["rubberband"], "OM_BUG_MOVE_RUBBERBAND injected but rubberband found nothing"
    dbg.om_world_free(world2)
