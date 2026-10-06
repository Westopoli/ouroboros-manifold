#!/usr/bin/env python3
"""Cross-platform determinism probe. Run on each OS; diff the output files.
Usage (repo root, after building the pipe):  python3 scripts/net_xplat_checksum.py [seed] [ticks] > out_<os>.txt
Prints one line per checkpoint tick: tick, full checksum, nine section words.
Windows: build the pipe so it is pipe/ouroboros_pipe.exe and set OM_PIPE to its path (harness reads PIPE below)."""
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests/long")); sys.path.insert(0, str(ROOT / "tests/net"))
import harness
if os.environ.get("OM_PIPE"):
    harness.PIPE = Path(os.environ["OM_PIPE"])
from harness import Pipe
from driver import start_mission, make_script, CHECK_EVERY, REISSUE, SECTIONS

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 3
ticks = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
MARKS = {100, 500, 1000, 2000}
p = Pipe()
try:
    info = start_mission(p, seed)
    script = make_script(info["mine"], info["target"])
    seq = 0
    for s in range(0, ticks, CHECK_EVERY):
        for c in script(0, 1, s):
            r = p.send("net_submit", tick=s + 1, peer=0, seq=seq, verb=c["verb"], arg=0, layer=0,
                       x=c["x"], y=c["y"], units=c["units"])
            assert r.get("code", 0) == 0, r
            seq += 1
        for _ in range(CHECK_EVERY):
            r = p.send("net_step", n=1)
        t = r["tick"]
        if t in MARKS or t == ticks:
            c = p.send("net_checksum")
            print("tick=%d full=%d %s" % (t, c["checksum"],
                  " ".join("%s=%d" % (SECTIONS[i] if i < len(SECTIONS) else i, v) for i, v in enumerate(c["sections"]))))
finally:
    p.close()
