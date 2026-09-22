"""PX-4: T1 trace detectors over the C sim's own trace API (Factory,
"Oracles" -- T1 trace detectors and invariants over the trace API are an
oracle class for the sim from rung P0, with OM_BUG_* builds as positive
controls).

Mirrors the SHAPE of the archived probe-C RTS detector suite
(~/Projects/agora/runs/101-probe-a-toy-drift-20260910-1521/worktree/probe_c/detectors/rts.py:
`Finding` dataclass, `fingerprint()` strips digits from "kind:sorted(detail
keys)" for stable cross-run dedup, `run_all()` returns
{detector_name: [Finding, ...]}) -- not its movement rules, which do not
exist yet in the C sim (no units). The C sim has no equivalent of the toy's
rubberband/stuck/backwards/dropped_order detectors; these two are the ones
the trace API (csrc/ouroboros_sim.h:81-95 `om_trace_row`) actually supports
today.

Pure functions over sequences of `om_trace_row`-shaped objects (duck-typed:
any object with `.region_idx`, `.tick`, `.tier`, the four fields, and
`.drift.<osc>_osc_delta` works -- a plain namedtuple in a unit test, or
tests/csim/conftest.py's ctypes `OmTraceRow` from a real trace read). No
csrc/ or tests/csim/ edits; `run_trace.py` in this directory is the runner
that builds real worlds and feeds these detectors rows, the way
tests/qa/t1/desync.py feeds its own comparison.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Finding:
    kind: str
    region_idx: int
    tick: int
    detail: dict = field(default_factory=dict)


def fingerprint(finding: Finding) -> str:
    keys = ",".join(sorted(finding.detail.keys()))
    return re.sub(r"\d", "", f"{finding.kind}:{keys}")


def _rows_by_region(rows) -> dict[int, list]:
    by_region: dict[int, list] = {}
    for r in rows:
        by_region.setdefault(r.region_idx, []).append(r)
    for region_rows in by_region.values():
        region_rows.sort(key=lambda r: r.tick)
    return by_region


def frozen_field(region_rows: list, field_name: str, window: int) -> bool:
    """True iff `field_name` (military/economy/tension/population) is
    constant across the last `window` rows of `region_rows` (or the whole
    sequence if shorter). Purely mechanical -- carries no judgement about
    whether frozen is the correct state; the caller supplies that (see
    `empty_region_drifted` below, where R-012-07 says frozen IS the correct
    clean-build state for an EMPTY-tier region, and OM_BUG_EMPTY_DRIFTS's
    positive control is a region that stops being frozen)."""
    tail = region_rows[-window:] if window else region_rows
    values = [getattr(r, field_name) for r in tail]
    return len(values) > 0 and all(v == values[0] for v in values)


def oscillation_as_level(region_rows: list, osc_field: str = "economy_osc_delta",
                          period: int = 15, tol: float = 1e-6) -> bool:
    """True iff some `period`-tick window of `drift.<osc_field>` sums to
    more than `tol` away from zero -- the oscillator behaving as a level
    shift instead of a zero-mean delta (OM_BUG_OSC_AS_LEVEL). Mirrors
    tests/csim/controls/test_control_osc_as_level.py's own inline check,
    generalized into a reusable function.

    `period` MUST match the field's own oscillator period (ALG-01,
    docs/bible/algorithms.md:35): economy 15 ticks, tension 18. Found
    empirically while building this detector: reusing economy's hardcoded
    15-tick window against `tension_osc_delta` fires on every region of a
    genuinely clean, un-injected build, because a 15-tick sum over an
    18-tick sine period does not cancel to zero regardless of correctness --
    a detector defect this probe caught before shipping it, not a sim
    defect (see the PX-4 write-up's "Found and fixed" section). Every caller
    in this module passes the field's real period explicitly; the default
    of 15 is economy's, kept only so a bare call for economy needs no extra
    argument.

    k=0 is skipped: R-018-02 fixes ALG-01's previous-tick value at 0 rather
    than the true osc(tick 0), so that one window is off by exactly
    A*sin(phase) under every implementation, correct or buggy (see that
    test's own comment) -- not a detector defect, just the one window this
    check cannot use."""
    deltas = [getattr(r.drift, osc_field) for r in region_rows]
    if len(deltas) < period + 1:
        return False
    return any(abs(sum(deltas[k:k + period])) >= tol for k in range(1, len(deltas) - period + 1))


def empty_region_drifted(rows, empty_region_indices, window: int = 0) -> list[Finding]:
    """Finding per region in `empty_region_indices` (the caller's own
    fixture ground truth -- which regions it built EMPTY) whose trace rows
    show it drifted -- R-012-07's clean-build guarantee, and
    OM_BUG_EMPTY_DRIFTS's positive control.

    `empty_region_indices` MUST come from the fixture, not from reading
    `row.tier` back out of the trace. Found empirically while building this
    detector: `OM_BUG_EMPTY_DRIFTS` doesn't just move an empty region's
    fields, it promotes the region's own live tier from EMPTY to FRONTIER
    within the FIRST tick it drifts (confirmed directly: `om_region_tier`
    reads EMPTY before `om_world_step`, FRONTIER after one step) -- a
    detector gating on `row.tier == EMPTY` disqualifies the very region the
    bug changed after its first tick, and (found the same way) a clean
    build never emits a trace row for an EMPTY region at all, so a
    tier-gated scan silently sees nothing to check on either build and
    reports false-silent on the PLANTED build too, not just the clean one --
    the exact "check that cannot fail is a defect" the project's own rule
    warns about. Gating on the fixture's own indices instead makes both
    signals usable: on a clean build, `empty_region_indices` produce zero
    trace rows at all (never traced -- itself the correct, expected state,
    not something this function needs to assert further); on the planted
    build, rows appear and move. `window=0` (default) checks the whole row
    sequence for whatever rows a region does have."""
    out = []
    by_region = _rows_by_region(rows)
    for region_idx in empty_region_indices:
        region_rows = by_region.get(region_idx, [])
        if not region_rows:
            continue  # clean-build state: never traced, nothing to report
        for f in ("military", "economy", "tension", "population"):
            if not frozen_field(region_rows, f, window):
                values = [getattr(r, f) for r in region_rows]
                out.append(Finding("empty_region_drifted", region_idx, region_rows[-1].tick,
                                    {"field": f, "first": values[0], "last": values[-1]}))
    return out


# ALG-01 (docs/bible/algorithms.md:35): economy P=15, tension P=18.
_OSC_FIELDS = {"economy_osc_delta": 15, "tension_osc_delta": 18}


def oscillator_as_level(rows) -> list[Finding]:
    """Finding per region/oscillator-field pair where `oscillation_as_level`
    trips -- OM_BUG_OSC_AS_LEVEL's positive control, ordinary shape (silent
    on clean, fires on planted)."""
    out = []
    for region_idx, region_rows in _rows_by_region(rows).items():
        for osc_field, period in _OSC_FIELDS.items():
            if oscillation_as_level(region_rows, osc_field, period):
                out.append(Finding("oscillator_as_level", region_idx, region_rows[-1].tick,
                                    {"osc_field": osc_field}))
    return out


def run_all(rows, empty_region_indices=()) -> dict[str, list[Finding]]:
    return {
        "empty_region_drifted": empty_region_drifted(rows, empty_region_indices),
        "oscillator_as_level": oscillator_as_level(rows),
    }
