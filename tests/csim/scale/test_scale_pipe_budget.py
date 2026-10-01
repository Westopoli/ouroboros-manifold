"""E-13 pipe budget (docs/architecture.md delta frame note; ruling A22, Westley
2026-10-01): one `tactical_step` round trip through the real pipe binary, request
written to frame parsed, p95 under 100 ms (the 10 ticks per second of R-099-03) at
5,000 units in the clash scene. Reuses scripts/bench_tactical_pipe.py's LD_PRELOAD
shim, which adds the units at mission_begin.

Gated by OM_SCALE=1 like the rest of this directory. Needs `make pipe/ouroboros_pipe`.
The budget is the bare 100 ms: OM_SCALE_CPU_FACTOR is not applied, because A22 pins
the budget against the forge's measured p95, not a min-spec derating.

Positive control: the same run with a 150 ms sleep planted in the shim's
om_tactical_step must violate the budget.
"""
import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location("_bench_tactical_pipe", ROOT / "scripts/bench_tactical_pipe.py")
bench = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bench)

N_UNITS = 5000
STEPS = 60
WARMUP = 3
BUDGET_MS = 100.0
PLANTED_DELAY_US = 150_000


def _p95_roundtrip_ms(shim_src):
    tmp = pathlib.Path(tempfile.mkdtemp())
    (tmp / "shim.c").write_text(shim_src)
    subprocess.check_call(["cc", "-O2", "-shared", "-fPIC", "-o", str(tmp / "shim.so"), str(tmp / "shim.c"), "-ldl"])
    env = dict(os.environ, LD_PRELOAD=str(tmp / "shim.so"), BENCH_N=str(N_UNITS), BENCH_LAYOUT="clash")
    p = subprocess.Popen([str(ROOT / "pipe/ouroboros_pipe")], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, env=env, cwd=ROOT)
    try:
        def send(c):
            p.stdin.write(bench.frame(c)); p.stdin.flush()
        send({"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": bench.FEATURES, "new_campaign": False})
        send({"type": "cmd", "name": "step", "n": 10})
        send({"type": "cmd", "name": "snapshot"})
        bench.read_frame(p.stdout)
        while bench.read_frame(p.stdout)[1]["type"] != "snapshot":
            pass
        send({"type": "cmd", "name": "mission_start", "faction": 0})
        while bench.read_frame(p.stdout)[1]["type"] != "mission":
            pass
        send({"type": "cmd", "name": "mission_begin"})
        _, fr = bench.read_frame(p.stdout)
        assert fr["type"] == "tactical"
        times = []
        for i in range(WARMUP + STEPS):
            t = time.perf_counter()
            send({"type": "cmd", "name": "tactical_step", "n": 1})
            bench.read_frame(p.stdout)
            if i >= WARMUP:
                times.append((time.perf_counter() - t) * 1e3)
        send({"type": "cmd", "name": "quit"})
        p.wait(timeout=30)
    finally:
        if p.poll() is None:
            p.kill()
    p95 = bench.pct(times, .95)
    print("pipe tactical_step roundtrip at %d units: p95 %.2f ms" % (N_UNITS, p95), file=sys.stderr)
    return p95


def test_pipe_round_trip_p95_under_100ms_at_5000_units():
    assert _p95_roundtrip_ms(bench.SHIM) < BUDGET_MS


def test_pipe_budget_positive_control_planted_delay_violates():
    planted = bench.SHIM.replace(
        "double t=now(); real(w);",
        "usleep(%d); double t=now(); real(w);" % PLANTED_DELAY_US,
    ).replace("#include <time.h>", "#include <time.h>\n#include <unistd.h>")
    assert planted != bench.SHIM
    assert _p95_roundtrip_ms(planted) >= BUDGET_MS
