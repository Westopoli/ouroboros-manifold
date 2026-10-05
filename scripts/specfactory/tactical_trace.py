#!/usr/bin/env python3
"""Tactical determinism trace for the merge gate (lockstep spec, "trace" lane).
Sibling of checksum_trace.py: loads a libouroboros*.so with ctypes, starts a
real mission for a fixed seed (the pipe's set_seed + mission_start +
mission_begin composition, done through the library), submits a fixed command
stream with om_cmd_submit, steps tactical ticks and prints
"tick combined s0 s1 ... sN" (om_world_checksum_full) every tenth tick.
The gate runs it on build/O0 and build/O2 and diffs with --compare.

See also: scripts/specfactory/checksum_trace.py (strategic-sim trace),
csrc/pipe/om_pipe.c handle_set_seed / handle_mission_start (composition ported).
"""
from __future__ import annotations

import argparse
import ctypes as C
import sys
from pathlib import Path

N_REGIONS = 80
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
VERB_ATTACK_MOVE = 1
FIRST_CMD_TICK = 5
REISSUE_EVERY = 400
PHASE_MISSION = 2  # OM_PIPE_CHAPTER_PHASE_MISSION


class NetCommand(C.Structure):  # mirrors om_net_command
    _fields_ = [("tick", C.c_uint64), ("seq", C.c_uint32), ("arg", C.c_uint32),
                ("x", C.c_double), ("y", C.c_double), ("peer", C.c_uint8),
                ("verb", C.c_uint8), ("layer", C.c_uint8), ("n_units", C.c_uint8)]


class Vec2(C.Structure):
    _fields_ = [("x", C.c_double), ("y", C.c_double)]


def bind(h):
    P, u32, i32, u64, dbl = C.c_void_p, C.c_uint32, C.c_int32, C.c_uint64, C.c_double
    sigs = {
        "om_world_new": (P, [u32, u64]), "om_world_free": (None, [P]),
        "om_world_set_feature": (None, [P, C.c_int, C.c_int]),
        "om_world_generate": (None, [P]), "om_events_load_launch": (None, [P]),
        "om_world_generated": (C.c_int, [P]), "om_mission_load_launch_library": (None, [P]),
        "om_campaign_start": (None, [P, u32]), "om_region_count": (u32, [P]),
        "om_region_owner": (i32, [P, u32]), "om_player_faction": (i32, [P]),
        "om_mission_start": (u32, [P, i32]), "om_mission_refresh_context": (None, [P, i32]),
        "om_mission_generator_chosen_archetype": (i32, [P]),
        "om_mission_generator_chosen_region": (u32, [P]),
        "om_mission_fallback_region": (u32, [P]), "om_mission_fallback_enemy": (i32, [P, u32]),
        "om_mission_setup_fallback": (None, [P, u32, i32]),
        "om_mission_setup": (None, [P, u32, u32, C.c_int]),
        "om_mission_archetype_count": (u32, [P]),
        "om_mission_set_candidate_viable": (None, [P, u32, C.c_int]),
        "om_mission_select_candidate": (u32, [P]),
        "om_mission_get_deployed_force_count": (u32, [P]),
        "om_mission_get_enemy_power": (dbl, [P]),
        "om_mission_build_objectives": (None, [P, u32]),
        "om_chapter_set_phase": (None, [P, C.c_int]), "om_mission_begin": (None, [P]),
        "om_cmd_reset": (None, [P]),
        "om_cmd_submit": (C.c_int, [P, C.POINTER(NetCommand), C.POINTER(u32)]),
        "om_tactical_step": (u64, [P]),
        "om_objective_get_center": (C.c_int, [P, u32, C.POINTER(Vec2)]),
        "om_unit_count": (u32, [P]), "om_unit_alive": (C.c_int, [P, u32]),
        "om_unit_get_faction": (i32, [P, u32]),
        "om_world_checksum_full": (u64, [P, C.POINTER(u64), u32]),
        "om_checksum_section_count": (u32, []),
    }
    for name, (res, args) in sigs.items():
        fn = getattr(h, name)
        fn.restype, fn.argtypes = res, args
    return h


def load(lib_path: str):
    h = C.CDLL(str(Path(lib_path).resolve()))
    if not hasattr(h, "om_world_checksum_full"):
        print(f"tactical_trace: {lib_path} lacks om_world_checksum_full", file=sys.stderr)
        sys.exit(3)
    return bind(h)


def start_mission(h, seed: int):
    w = h.om_world_new(N_REGIONS, seed)
    assert w, "om_world_new returned NULL"
    for f in FEATURES:
        h.om_world_set_feature(w, f, 1)
    h.om_world_generate(w)
    h.om_events_load_launch(w)
    assert h.om_world_generated(w), "generation failed"
    h.om_mission_load_launch_library(w)
    h.om_campaign_start(w, 1)
    player = h.om_player_faction(w)
    n = h.om_region_count(w)
    h.om_mission_start(w, 0)
    for ri in range(n):
        h.om_mission_refresh_context(w, ri)
    drawn = h.om_mission_generator_chosen_archetype(w)
    region = arch = None
    if drawn >= 0:
        region, arch = h.om_mission_generator_chosen_region(w), drawn
        h.om_mission_setup(w, region, arch, 0)
    else:
        # The pipe retries by time-jumping here; this tool goes straight to
        # its fallback, which is deterministic and enough for a trace.
        region = h.om_mission_fallback_region(w)
        enemy = h.om_mission_fallback_enemy(w, region)
        if enemy >= 0:
            arch = 0
            h.om_mission_setup_fallback(w, region, enemy)
    ok = arch is not None and h.om_mission_get_deployed_force_count(w) > 0 \
        and h.om_mission_get_enemy_power(w) > 0.0
    if not ok:
        for a in range(h.om_mission_archetype_count(w)):
            h.om_mission_set_candidate_viable(w, a, 1)
        for a in range(h.om_mission_archetype_count(w)):
            for ri in range(n):
                if h.om_region_owner(w, ri) != player:
                    continue
                h.om_mission_setup(w, ri, a, 0)
                if h.om_mission_get_deployed_force_count(w) > 0 and h.om_mission_get_enemy_power(w) > 0.0:
                    region, arch, ok = ri, a, True
                    break
            if ok:
                break
    assert ok, "no viable mission for this seed"
    h.om_mission_build_objectives(w, arch)
    h.om_chapter_set_phase(w, PHASE_MISSION)
    h.om_mission_begin(w)
    h.om_cmd_reset(w)
    return w, player


def player_units(h, w, player):
    return [u for u in range(1, h.om_unit_count(w) + 1)
            if h.om_unit_get_faction(w, u) == player and h.om_unit_alive(w, u)][:70]


def run(lib_path: str, seed: int, ticks: int) -> list[str]:
    h = load(lib_path)
    w, player = start_mission(h, seed)
    try:
        obj = Vec2()
        assert h.om_objective_get_center(w, 0, C.byref(obj)) is not None
        nsec = h.om_checksum_section_count()
        secs = (C.c_uint64 * nsec)()
        out = [f"# lib={lib_path} seed={seed} ticks={ticks} sections={nsec}"]
        seq = 0
        for t in range(1, ticks + 1):
            if t >= FIRST_CMD_TICK and (t - FIRST_CMD_TICK) % REISSUE_EVERY == 0:
                ids = player_units(h, w, player)
                if ids:
                    seq += 1
                    cmd = NetCommand(tick=t, seq=seq, arg=0, x=obj.x, y=obj.y, peer=0,
                                     verb=VERB_ATTACK_MOVE, layer=0, n_units=len(ids))
                    arr = (C.c_uint32 * len(ids))(*ids)
                    rc = h.om_cmd_submit(w, C.byref(cmd), arr)
                    assert rc == 0, f"om_cmd_submit refused at tick {t}: {rc}"
            h.om_tactical_step(w)
            if t % 10 == 0:
                comb = h.om_world_checksum_full(w, secs, nsec)
                out.append(f"tick {t} {comb} " + " ".join(str(secs[i]) for i in range(nsec)))
        return out
    finally:
        h.om_world_free(w)


def compare(a_text: str, b_text: str) -> tuple[bool, str]:
    def rows(text):
        return [ln.split() for ln in text.splitlines() if ln.startswith("tick ")]
    ra, rb = rows(a_text), rows(b_text)
    for x, y in zip(ra, rb):
        if x == y:
            continue
        if x[1] != y[1]:
            return False, f"first difference at tick {x[1]}: tick label {x[1]} vs {y[1]}"
        for i, (p, q) in enumerate(zip(x[3:], y[3:])):
            if p != q:
                return False, f"first difference at tick {x[1]} section s{i}: {p} vs {q}"
        return False, f"first difference at tick {x[1]} section combined: {x[2]} vs {y[2]}"
    if len(ra) != len(rb):
        return False, f"different number of rows: {len(ra)} vs {len(rb)}"
    if not ra:
        return False, "no trace rows found"
    return True, f"IDENTICAL ({len(ra)} rows)"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--lib")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--ticks", type=int, default=1500)
    ap.add_argument("--compare", nargs=2, metavar=("FILE_A", "FILE_B"))
    args = ap.parse_args(argv)
    if args.compare:
        ok, detail = compare(Path(args.compare[0]).read_text(), Path(args.compare[1]).read_text())
        print(("MATCH " if ok else "DIVERGE ") + detail)
        return 0 if ok else 1
    if not args.lib:
        ap.print_usage(sys.stderr)
        return 2
    print("\n".join(run(args.lib, args.seed, args.ticks)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
