#!/usr/bin/env python3
"""Measure tactical_step cost at N units: through the real pipe binary and sim-only (ctypes).

Usage: bench_tactical_pipe.py N [steps] [spread|clash]
Run from the repo root after `make pipe/ouroboros_pipe`. Measurement only; no repo file changes.

The pipe has no verb that spawns many units, so a throwaway LD_PRELOAD shim (built into a temp
dir) wraps om_mission_begin to spawn N extra units and wraps om_tactical_step to time it. The
pipe binary itself is unmodified. Pipe time = request written to full frame read; serialise time
= pipe time minus the shim-measured om_tactical_step time (includes the pipe write and read).
"""
import ctypes, json, os, statistics, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURES = [1, 2, 3, 4, 5, 6, 7]
SHIM = r"""
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
typedef void om_world;
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec*1e3+t.tv_nsec/1e6;}
static uint64_t s=88172645463325252ULL;
static double rnd(void){s^=s<<13;s^=s>>7;s^=s<<17;return (double)(s>>11)/9007199254740992.0;}
void om_mission_begin(om_world *w){
  void (*real)(om_world*)=dlsym(RTLD_NEXT,"om_mission_begin");
  uint32_t (*spawn)(om_world*,int,int32_t,double,double,uint32_t)=dlsym(RTLD_NEXT,"om_unit_spawn");
  real(w);
  int n=atoi(getenv("BENCH_N")); int clash=getenv("BENCH_LAYOUT")&&getenv("BENCH_LAYOUT")[0]=='c';
  for(int i=0;i<n;i++){
    int f=i&1; double x,y;
    if(clash){x=(f?9000:6000)+rnd()*2500;y=7000+rnd()*3000;}
    else{x=rnd()*16000;y=rnd()*16000;}
    spawn(w,i%6,f,x,y,0);
  }
}
static double acc_see=0; static long n_see=0;
int om_player_can_see_unit(om_world *w,int32_t f,uint32_t id){
  static int (*real)(om_world*,int32_t,uint32_t); if(!real) real=dlsym(RTLD_NEXT,"om_player_can_see_unit");
  double t=now(); int r=real(w,f,id); acc_see+=now()-t; n_see++; return r;
}
void om_tactical_step(om_world *w){
  void (*real)(om_world*)=dlsym(RTLD_NEXT,"om_tactical_step");
  fprintf(stderr,"SEE %.4f %ld\n",acc_see,n_see); acc_see=0; n_see=0;
  double t=now(); real(w);
  fprintf(stderr,"STEP %.4f\n",now()-t);
}
"""

def frame(o):
    b = json.dumps(o).encode()
    return len(b).to_bytes(4, "big") + b

def read_frame(f):
    h = f.read(4)
    n = int.from_bytes(h, "big")
    b = f.read(n)
    return n, json.loads(b)

def pct(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(round(p * (len(v) - 1))))]

def summarize(name, v):
    return "%s: median %.2f  p95 %.2f  max %.2f  min %.2f ms (n=%d)" % (
        name, statistics.median(v), pct(v, .95), max(v), min(v), len(v))

def pipe_run(n, steps, layout):
    tmp = Path(tempfile.mkdtemp())
    (tmp / "shim.c").write_text(SHIM)
    subprocess.check_call(["cc", "-O2", "-shared", "-fPIC", "-o", str(tmp / "shim.so"), str(tmp / "shim.c"), "-ldl"])
    env = dict(os.environ, LD_PRELOAD=str(tmp / "shim.so"), BENCH_N=str(n), BENCH_LAYOUT=layout)
    errf = open(tmp / "err.txt", "w")
    p = subprocess.Popen([str(ROOT / "pipe/ouroboros_pipe")], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=errf, env=env, cwd=ROOT)
    def send(c): p.stdin.write(frame(c)); p.stdin.flush()
    send({"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": FEATURES, "new_campaign": False})
    send({"type": "cmd", "name": "step", "n": 10})
    send({"type": "cmd", "name": "snapshot"})
    read_frame(p.stdout)  # hello
    while read_frame(p.stdout)[1]["type"] != "snapshot": pass
    send({"type": "cmd", "name": "mission_start", "faction": 0})
    while read_frame(p.stdout)[1]["type"] != "mission": pass
    send({"type": "cmd", "name": "mission_begin"})
    size, fr = read_frame(p.stdout)
    assert fr["type"] == "tactical"
    n_units = len(fr["units"])
    times, sizes = [], []
    for _ in range(steps):
        t = time.perf_counter()
        send({"type": "cmd", "name": "tactical_step", "n": 1})
        size, fr = read_frame(p.stdout)
        times.append((time.perf_counter() - t) * 1e3)
        sizes.append(size)
    if os.environ.get("BENCH_DUMP"):
        Path(os.environ["BENCH_DUMP"]).write_text(json.dumps(fr))
    send({"type": "cmd", "name": "quit"})
    p.wait(timeout=30)
    errf.close()
    sim = [float(l.split()[1]) for l in (tmp / "err.txt").read_text().splitlines() if l.startswith("STEP")]
    sim = sim[-steps:]
    ser = [a - b for a, b in zip(times, sim)]
    print("PIPE n_spawned=%d units_in_frame=%d layout=%s frame_bytes=%d" % (n, n_units, layout, sizes[-1]))
    print(" ", summarize("roundtrip", times))
    print(" ", summarize("sim step (shim)", sim))
    print(" ", summarize("serialise+io (roundtrip-sim)", ser))
    see = [float(l.split()[1]) for l in (tmp / "err.txt").read_text().splitlines() if l.startswith("SEE")][-steps:]
    print(" ", summarize("  of which om_player_can_see_unit (visible[], per frame)", see))
    print("  serialise share of roundtrip (medians): %.0f%%" % (100 * statistics.median(ser) / statistics.median(times)))

def ctypes_run(n, steps, layout):
    sys.path.insert(0, str(ROOT / "tests/csim"))
    import conftest as csim
    lib = csim.load_lib(); csim._bind_e03(lib)
    lib.om_unit_spawn.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int32, ctypes.c_double, ctypes.c_double, ctypes.c_uint32]
    lib.om_unit_spawn.restype = ctypes.c_uint32
    w = lib.om_world_new(80, 1)
    for f in FEATURES: lib.om_world_set_feature(w, f, 1)
    lib.om_world_generate(w)
    for _ in range(10): lib.om_world_step(w)
    lib.om_mission_start(w, 0)
    lib.om_mission_build_candidate_pool(w)
    idx = lib.om_mission_select(w)
    pool = (csim.OMMissionCandidate * 256)()
    c = lib.om_mission_candidates(w, pool, 256)
    region, arch = (pool[idx].region_idx, pool[idx].archetype) if idx < c else (0, 0)
    lib.om_mission_setup(w, region, arch, 0)
    lib.om_mission_build_objectives(w, arch)
    lib.om_chapter_set_phase(w, 2)
    lib.om_mission_begin(w)
    s = 88172645463325252
    def rnd():
        nonlocal s
        s ^= (s << 13) & (2**64 - 1); s ^= s >> 7; s ^= (s << 17) & (2**64 - 1)
        return (s >> 11) / 9007199254740992.0
    for i in range(n):
        f = i & 1
        x, y = ((9000 if f else 6000) + rnd() * 2500, 7000 + rnd() * 3000) if layout == "clash" else (rnd() * 16000, rnd() * 16000)
        lib.om_unit_spawn(w, i % 6, f, x, y, 0)
    ts = []
    for _ in range(steps):
        t = time.perf_counter(); lib.om_tactical_step(w); ts.append((time.perf_counter() - t) * 1e3)
    print("CTYPES units=%d layout=%s" % (lib.om_unit_count(w), layout))
    print(" ", summarize("sim step", ts))

if __name__ == "__main__":
    n = int(sys.argv[1]); steps = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    layout = sys.argv[3] if len(sys.argv) > 3 else "spread"
    pipe_run(n, steps, layout)
    ctypes_run(n, steps, layout)
