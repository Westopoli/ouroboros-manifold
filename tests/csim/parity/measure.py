"""Measure the Python reference against the C, scene by scene.

    python tests/csim/parity/measure.py                  # Python vs C: per-scene max position deviation,
                                                         # where each channel first leaves tolerance
    python tests/csim/parity/measure.py --series 20      # plus the per-tick max deviation every 20 ticks
    python tests/csim/parity/measure.py --diagnose       # same, C ids shifted by 3 so its id % 4 targeting
                                                         # cohort equals the Python's uid % 4 (attribution only)
    python tests/csim/parity/measure.py --tolerance      # Python vs Python: trig sweep vs fixed direction vectors
                                                         # (the measurement PARITY_TOLERANCE was proposed from)
    python tests/csim/parity/measure.py --sensitivity    # Python vs Python: collision pair order reversed
    python tests/csim/parity/measure.py --scene NAME     # one scene

Run with the agora venv python (numpy needed by the Python reference). No pass/fail here: this
prints numbers; the red/green is tests/csim/parity/test_parity_scenes.py.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import parity_c
import parity_python
from parity_compare import compare
from parity_scenes import SCENES
from parity_tolerance import PARITY_FACING_TOLERANCE, PARITY_TOLERANCE

FIXED_DIGITS = (None, 12, 10, 8, 6, 4)   # None = full double; n = the six sweep constants rounded to n decimals


def _fmt(first, what):
    return "%s@%d" % (what, first[0]) if first else "-"


def python_vs_c(names, series, id_offset):
    print("Python reference vs C library (position tol %g wu, facing tol %g rad, id_offset %d)"
          % (PARITY_TOLERANCE, PARITY_FACING_TOLERANCE, id_offset))
    print("%-28s %5s %12s %10s  %s" % ("scene", "ticks", "max pos wu", "max face", "first tick out of tolerance by channel"))
    for name in names:
        scene = SCENES[name]
        ref = parity_python.run_scene(scene)
        got = parity_c.run_scene(scene, id_offset=id_offset)
        rep = compare(ref, got, PARITY_TOLERANCE, PARITY_FACING_TOLERANCE)
        chans = "  ".join(_fmt(c, n) for n, c in (("pos", rep.first_pos), ("target", rep.first_target),
                                                   ("facing", rep.first_facing), ("alive", rep.first_alive)))
        print("%-28s %5d %12.4g %10.4g  %s%s" % (name, rep.ticks, rep.max_pos, rep.max_facing, chans,
                                                 "  SHAPE: " + rep.shape_error if rep.shape_error else ""))
        if series:
            print("    per-tick max position deviation every %d ticks: %s" % (
                series, " ".join("%d:%.4g" % (t, rep.pos_dev[t - 1]) for t in range(series, rep.ticks + 1, series))))


def python_vs_python(names, variants, title):
    print(title)
    worst = {}
    print("%-28s %s" % ("scene", "  ".join("%-22s" % ("%s%s" % (v, "" if d is None else "(%d dec)" % d)) for v, d in variants)))
    for name in names:
        scene = SCENES[name]
        ref = parity_python.run_scene(scene)
        cells = []
        for v, d in variants:
            rep = compare(ref, parity_python.run_scene(scene, v, d), 0.0, 0.0)
            w = worst.setdefault((v, d), [0.0, 0.0])
            w[0], w[1] = max(w[0], rep.max_pos), max(w[1], rep.max_facing)
            cells.append("%-22s" % ("%.3g wu %.3g rad" % (rep.max_pos, rep.max_facing)))
        print("%-28s %s" % (name, "  ".join(cells)))
    print("%-28s %s" % ("MAX over scenes", "  ".join("%-22s" % ("%.3g wu %.3g rad" % tuple(worst[k])) for k in variants)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scene", action="append", help="scene name (repeatable); default all")
    ap.add_argument("--series", type=int, default=0, help="print the per-tick max deviation every N ticks")
    ap.add_argument("--diagnose", action="store_true", help="shift C ids by 3 so the targeting cohort lines up")
    ap.add_argument("--tolerance", action="store_true", help="Python trig sweep vs fixed direction vectors")
    ap.add_argument("--sensitivity", action="store_true", help="Python collision pair order reversed")
    args = ap.parse_args()
    names = args.scene or list(SCENES)
    if args.tolerance:
        python_vs_python(names, [("fixed", d) for d in FIXED_DIGITS],
                         "Python (trig sweep) vs Python (fixed direction vectors, constants to n decimals)")
    elif args.sensitivity:
        python_vs_python(names, [("order_rev", None)], "Python vs Python with the collision pass in descending uid order")
    else:
        parity_c.build()
        python_vs_c(names, args.series, 3 if args.diagnose else 0)


if __name__ == "__main__":
    main()
