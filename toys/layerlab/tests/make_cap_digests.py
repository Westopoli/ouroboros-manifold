"""Pin digests of six small traced fights (SPEC.md section 16: no behaviour change at 128 units or fewer).

Run from toys/layerlab/ BEFORE the unit cap change, against the ABI 3 build:

    make && python3 tests/make_cap_digests.py

It writes tests/data/cap_digests.json (committed). tests/test_cap.py recomputes the same digests with
the changed library (O0 and O2) and compares: the old library cannot be run any more, so the stored
file is the ABI 3 reference. The digest hashes only things that exist in ABI 3: the result scalar
fields, the first n_spawns unit rows, and the trace bytes. It never hashes ll_abi_version or the size
of the result's unit array, so the cap change does not move it.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
DATA = Path(__file__).resolve().parent / "data" / "cap_digests.json"
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

import numpy as np  # noqa: E402

from layerlab import scenario  # noqa: E402
from layerlab.run import run  # noqa: E402

SEEDS = (0, 1)
_SKIP = ("unit", "trace", "raw")   # everything else on Result is an ABI 3 scalar field


def _base():
    return scenario.load(str(LAB / "scenarios" / "base.toml"))


def _g(side, type_, x, y, layer, count, facing, goal=None, order="attack_move", **kw):
    g = {"side": side, "type": type_, "count": count, "formation": "line", "x": float(x), "y": float(y),
         "facing": float(facing), "layer": layer, "order": order}
    if goal is not None:
        g["goal"] = [float(goal[0]), float(goal[1])]
    g.update(kw)
    return g


def _slope():
    """Ramp (x1 40, sl 600, sw 200, g 1, h 1): ten walkers climb the slope to meet five raiders on the plateau."""
    scn = _base()
    scn["terrain"].update({"preset": "ramp", "x1": 40, "sl": 600.0, "sw": 200.0, "g": 1, "h": 1})
    scn["types"]["walker"] = {**scn["types"]["raider"], "movement_kind": "walk", "speed": 80.0}
    scn["groups"] = [
        _g("A", "walker", 900, 1000, 1, 10, 0, goal=(2800, 1000), formation="box", cols=5, spacing=31.0),
        _g("B", "raider", 2800, 1000, 2, 5, 180, goal=(900, 1000), order="hold"),
    ]
    scn["run"].update({"max_ticks": 2000, "stalemate_ticks": 3000})   # the climb takes ~480 ticks
    return scn


def _burst():
    """Two casters and six raiders (A, layer 3) against a clustered box of twelve raiders walking in."""
    scn = _base()
    scn["groups"] = [
        _g("A", "caster", 1000, 1000, 3, 2, 0, order="hold", spacing=60.0),
        _g("A", "raider", 1000, 1300, 3, 6, 0, goal=(3000, 1000)),
        _g("B", "raider", 1700, 1000, 3, 12, 180, goal=(1000, 1000), formation="box", cols=4, spacing=40.0),
    ]
    return scn


def _mirror5():
    scn = scenario.load(str(LAB / "scenarios" / "x0_mirror.toml"))
    for g in scn["groups"]:
        g["count"] = 5
    return scn


def _mix64():
    """64 against 64, mixed types, boxes in four rows per side."""
    scn = _base()
    a = [("raider", 20), ("vanguard", 20), ("warden", 12), ("bombard", 12)]
    b = [("interceptor", 24), ("bastion", 8), ("vanguard", 16), ("raider", 16)]
    groups = []
    for (ta, na), (tb, nb), y in zip(a, b, (300, 700, 1100, 1500)):
        groups.append(_g("A", ta, 800, y, 3, na, 0, goal=(3200, y), formation="box", cols=5))
        groups.append(_g("B", tb, 3200, y, 3, nb, 180, goal=(800, y), formation="box", cols=5))
    scn["groups"] = groups
    return scn


def build_scenarios():
    """name -> scenario dict. Six fixed fights, all at most 128 units."""
    s = {
        "r0_raiders_10v5": scenario.load(str(LAB / "scenarios" / "r0_raiders_10v5.toml")),
        "mirror_5v5": _mirror5(),
        "slope_walkers": _slope(),
        "layered_crossfire": scenario.load(str(LAB / "scenarios" / "x4_high_ground_both_answer.toml")),
        "burst_casters": _burst(),
        "mix_64v64": _mix64(),
    }
    return copy.deepcopy(s)


def digest(scn, seed, lib="O2"):
    """sha256 over the traced result: scalar fields, the first n_spawns unit rows, the trace bytes."""
    res = run(scn, seed=seed, trace=True, lib=lib)
    h = hashlib.sha256()
    for name in res.__dataclass_fields__:
        if name in _SKIP:
            continue
        h.update(("%s=%r;" % (name, getattr(res, name))).encode())
    for u in res.unit:
        h.update(("%r,%r,%r,%r,%r,%r;" % (u["x"], u["y"], u["hp"], u["layer"], u["alive"], u["transitions"])).encode())
    h.update(np.ascontiguousarray(res.trace).tobytes())
    return h.hexdigest()


def key(name, seed):
    return "%s|seed%d" % (name, seed)


def compute(lib="O2"):
    return {key(n, sd): digest(s, sd, lib) for n, s in build_scenarios().items() for sd in SEEDS}


def main():
    out = compute("O2")
    DATA.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("wrote %s (%d digests)" % (DATA, len(out)))


if __name__ == "__main__":
    main()
