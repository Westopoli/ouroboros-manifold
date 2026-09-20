"""T1 desync detector -- docs/bible/epics/E-19-multiplayer.md S-139
(R-139-03/04) and docs/northstar/research/factory/A7-multiplayer-determinism-qa.md
section 4: two `om_world` instances built from the same seed and fed the same
command stream must checksum identically every `om_checksum_cadence()` ticks;
a corrupted peer must be caught within the cadence window and named by tick,
region, and field.

Pure Python over ctypes. Callers supply an already-loaded `lib` handle (the
`lib` fixture in tests/csim/conftest.py) plus a `setup(lib, world)` callback
that builds identical fixture state on both instances, and a `commands` list
applied to instance A each tick (an identical `commands_b` list, defaulting to
`commands`, is applied to instance B -- pass a different one to make the two
peers' inputs diverge, as the out-of-order control does). An optional
`corrupt_b` list of (tick, how) pairs mutates instance B only, through the
`corrupt()` fixture-setter hook below, to fabricate the positive control.

This module does not touch csrc/ or tests/csim/; it only calls the public ABI
those already expose.
"""
from __future__ import annotations

import ctypes
import struct
from dataclasses import dataclass, field as dataclass_field

# Canonical field order the checksum is defined over (header comment on
# om_world_checksum: "every inhabited region's six numbers"), used to name
# the first differing field once a checksum mismatch is found.
_TRACE_FIELDS = ("military", "economy", "tension", "population", "stability", "capacity")

_REGION_FIELD_INDEX = {"military": 0, "economy": 1, "tension": 2, "population": 3}


@dataclass
class DesyncReport:
    diverged: bool
    ticks_run: int
    cadence: int
    first_divergent_tick: int | None = None
    first_checkpoint_reported: int | None = None
    region: int | None = None
    field: str | None = None
    checksum_a: int | None = None
    checksum_b: int | None = None
    checkpoint_checksums: list[tuple[int, int, int]] = dataclass_field(default_factory=list)
    trace_bytes_equal: bool | None = None
    n_trace_rows_a: int | None = None
    n_trace_rows_b: int | None = None


def _apply_commands(lib, world, commands, tick):
    for cmd in commands:
        if cmd["tick"] != tick:
            continue
        op = cmd["op"]
        if op == "intent":
            rc = lib.om_intent_inject(
                world, cmd["faction_id"], cmd["action"], cmd["target_idx"],
                cmd["source_idx"], cmd["commit"], cmd.get("mode", 0),
            )
            assert rc == 0, f"om_intent_inject failed at tick {tick}: {cmd}"
        elif op == "rng_force":
            draws = cmd["draws"]
            arr = (ctypes.c_double * len(draws))(*draws)
            lib.om_rng_force(world, arr, len(draws))
        else:
            raise ValueError(f"unknown command op {op!r}")


def corrupt(lib, world, how):
    """Flip one bit of one region's field on `world`, through the fixture
    setter (om_region_set) -- the header exposes no direct struct write, and
    only the release build (not just `dbg`) is needed since this path is a
    documented fixture, not a debug-only fault injector.

    `how` = {"region": idx, "field": one of military/economy/tension/population,
    "bit": 0..63, "econ_phase": ..., "tension_phase": ...}. Tier and owner are
    read live (om_region_tier / om_region_owner) so a region that changed
    hands since fixture time is not silently reset; the oscillator phases have
    no getter, so the caller supplies the values it originally fixed the
    region with.
    """
    idx = how["region"]
    field_name = how["field"]
    bit = how.get("bit", 0)
    values = {
        name: lib.om_region_field(world, idx, i)
        for name, i in _REGION_FIELD_INDEX.items()
    }
    raw = struct.unpack("<Q", struct.pack("<d", values[field_name]))[0]
    raw ^= (1 << bit)
    values[field_name] = struct.unpack("<d", struct.pack("<Q", raw))[0]

    tier = lib.om_region_tier(world, idx)
    faction_id = lib.om_region_owner(world, idx)
    rc = lib.om_region_set(
        world, idx, tier,
        values["military"], values["economy"], values["tension"], values["population"],
        how["econ_phase"], how["tension_phase"], faction_id,
    )
    assert rc == 0, f"corrupt(): om_region_set failed for region {idx}"


def _read_all_trace(lib, world, trace_row_type):
    n = lib.om_trace_len(world)
    if n == 0:
        return []
    buf = (trace_row_type * n)()
    got = lib.om_trace_read(world, 0, n, buf)
    assert got == n
    return list(buf)


def _first_diff_at_tick(lib, world_a, world_b, tick, trace_row_type):
    """After a checksum mismatch is confirmed at `tick`, replay both traces
    and return (region_idx, field_name) of the first mismatching value in
    region-index order, then _TRACE_FIELDS order. None, None if the trace
    rows at that tick agree (should not happen when checksums differ, but a
    disagreement here is itself evidence worth reporting rather than hiding)."""
    rows_a = {r.region_idx: r for r in _read_all_trace(lib, world_a, trace_row_type) if r.tick == tick}
    rows_b = {r.region_idx: r for r in _read_all_trace(lib, world_b, trace_row_type) if r.tick == tick}
    for idx in sorted(set(rows_a) | set(rows_b)):
        ra = rows_a.get(idx)
        rb = rows_b.get(idx)
        if ra is None or rb is None:
            return idx, "presence"
        for name in _TRACE_FIELDS:
            if getattr(ra, name) != getattr(rb, name):
                return idx, name
    return None, None


def run_pair(lib, seed, commands, ticks, *, n_regions, trace_row_type, setup=None,
             commands_b=None, corrupt_b=None, compare_trace_bytes=None):
    """Run two `om_world` instances from the same seed through `ticks` ticks,
    checking om_world_checksum() every tick (so the report can name the exact
    first divergent tick) and recording the value at every
    om_checksum_cadence() checkpoint (what two real peers would exchange).

    `commands_b` defaults to `commands` (the clean-pair case); pass a
    different list to feed peer B a different command order. `corrupt_b` is a
    list of (tick, how) pairs applied only to instance B, right before that
    tick's step, via `corrupt()` above.

    `trace_row_type` must be the exact `om_trace_row` ctypes.Structure class
    already bound to `lib.om_trace_read.argtypes` by the caller's fixture
    (ctypes rejects a structurally-identical-but-distinct class) -- this
    module defines no ABI struct mirrors of its own, to stay a single source
    of truth with whatever mirrors the caller's conftest already declared.

    Frees both worlds before returning. `compare_trace_bytes` defaults to
    True when the run never diverges (cheap, and it is the memcmp check
    S-020's own determinism test performs) and False once a divergence is
    already known, since the trace rows are then expected to disagree and the
    field-level diagnosis already covers why.
    """
    if commands_b is None:
        commands_b = commands
    corrupt_b = corrupt_b or []
    corrupt_by_tick: dict[int, list[dict]] = {}
    for tick, how in corrupt_b:
        corrupt_by_tick.setdefault(tick, []).append(how)

    cadence = lib.om_checksum_cadence()

    world_a = lib.om_world_new(n_regions, seed)
    world_b = lib.om_world_new(n_regions, seed)
    assert world_a and world_b, "om_world_new returned NULL"

    try:
        if setup is not None:
            setup(lib, world_a)
            setup(lib, world_b)

        lib.om_trace_enable(world_a, 1)
        lib.om_trace_enable(world_b, 1)

        first_divergent_tick = None
        checksum_a_at_div = None
        checksum_b_at_div = None
        checkpoints: list[tuple[int, int, int]] = []

        for tick in range(1, ticks + 1):
            _apply_commands(lib, world_a, commands, tick)
            _apply_commands(lib, world_b, commands_b, tick)
            for how in corrupt_by_tick.get(tick, []):
                corrupt(lib, world_b, how)

            lib.om_world_step(world_a)
            lib.om_world_step(world_b)

            ca = lib.om_world_checksum(world_a)
            cb = lib.om_world_checksum(world_b)

            if ca != cb and first_divergent_tick is None:
                first_divergent_tick = tick
                checksum_a_at_div = ca
                checksum_b_at_div = cb

            if tick % cadence == 0:
                checkpoints.append((tick, ca, cb))

        diverged = first_divergent_tick is not None
        region = fld = None
        first_checkpoint_reported = None
        if diverged:
            region, fld = _first_diff_at_tick(lib, world_a, world_b, first_divergent_tick, trace_row_type)
            first_checkpoint_reported = (
                (first_divergent_tick + cadence - 1) // cadence
            ) * cadence

        if compare_trace_bytes is None:
            compare_trace_bytes = not diverged

        trace_bytes_equal = None
        n_rows_a = n_rows_b = None
        if compare_trace_bytes:
            n_rows_a = lib.om_trace_len(world_a)
            n_rows_b = lib.om_trace_len(world_b)
            if n_rows_a == n_rows_b:
                buf_a = (trace_row_type * n_rows_a)()
                buf_b = (trace_row_type * n_rows_b)()
                lib.om_trace_read(world_a, 0, n_rows_a, buf_a)
                lib.om_trace_read(world_b, 0, n_rows_b, buf_b)
                bytes_a = ctypes.string_at(ctypes.addressof(buf_a), ctypes.sizeof(buf_a))
                bytes_b = ctypes.string_at(ctypes.addressof(buf_b), ctypes.sizeof(buf_b))
                trace_bytes_equal = bytes_a == bytes_b
            else:
                trace_bytes_equal = False

        return DesyncReport(
            diverged=diverged,
            ticks_run=ticks,
            cadence=cadence,
            first_divergent_tick=first_divergent_tick,
            first_checkpoint_reported=first_checkpoint_reported,
            region=region,
            field=fld,
            checksum_a=checksum_a_at_div,
            checksum_b=checksum_b_at_div,
            checkpoint_checksums=checkpoints,
            trace_bytes_equal=trace_bytes_equal,
            n_trace_rows_a=n_rows_a,
            n_trace_rows_b=n_rows_b,
        )
    finally:
        lib.om_world_free(world_a)
        lib.om_world_free(world_b)
