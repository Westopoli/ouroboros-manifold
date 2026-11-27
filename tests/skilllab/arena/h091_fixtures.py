# Rule pins: none (lab harness story H-091, lab stage 5)
"""Shared fixtures for the H-091 (lab stage 5) lab tests (not a test file), built on h063_fixtures.

FLANK scenes (`flank_layout`): the holder is side A, eight Vanguards in two ranks of four (40 wu apart) at (2000, 2000) facing east, orders hold:A, sight off, small_flat; side B is eight
Vanguards in two ranks of four, 40 wu apart, the front rank DISTANCE (200 wu) from the holder's centre in the direction `approach` ("east" is the holder's front, "north" and "south" its sides,
"west" its rear), facing the holder; B attack-moves onto the holder's centre (the engine's order rule R2). A Vanguard's attack range is 300 wu, so every unit has an enemy in range on tick 0
and the first shots fall on ticks 1 to 4 (dumped, facing off): the holders have no time to turn before the first hits, so the first hit on a holder is from the side the attackers came from.
A larger `distance` (700) makes the attackers walk in, and the holders turn toward them before the first shot (dumped: first shots on ticks 83 to 106, the holders already turned 45 degrees).

SLOPE scene (`slope_layout`): small_tiered, the stage 3 slope feature (x 2000, y 2000, length 600, width 200: foot x 1700, top x 2300), hold:A; holder A eight Vanguards on layer 1 at x 2700
to 2740 (400 wu past the top, so the ramp is crossed whole before the first shot), attacker B eight Vanguards on layer 0 at x 1000 to 1040 walking up the ribbon (sight off: walkers because the layout carries a feature, run.fight).

PINS (R-091-07): the sha256 of the fight files the tree writes with facing OFF, seed 1, `--allow-invalid` (the runner exits 2 on the checker's INVALID lines, which these three fights
carry today; the file is the same), recorded 2026-11-26 on the base of this lane (s/lab5-engine e008c38bb, the firing arc built and off at the default 360) BEFORE any lab stage 5 line was
written. The one `"layout_path": "<value>"` string is replaced by the constant `"layout_path_pinned"` before hashing (the control twin's path is a temporary directory), as
h088_fixtures does. Commands, from the repository root, with D a scratch directory:
    python -m scripts.skilllab.arena.run --layout docs/northstar/research/layer_dynamics/catalogue/L-0054.toml --seed 1 --out D/o54 --allow-invalid
    python -m scripts.skilllab.arena.run --layout docs/northstar/research/layer_dynamics/catalogue/L-0055.toml --seed 1 --out D/o55 --control-dir D/c55 --allow-invalid
    python -m scripts.skilllab.arena.run --layout docs/northstar/research/layer_dynamics/catalogue/L-0080.toml --seed 1 --out D/o80 --sight on --allow-invalid
and the sha256 of D/o54/L-0054-s1.fight.json, D/o55/L-0055-s1.fight.json, D/c55/L-0055-control-s1.fight.json and D/o80/L-0080-s1.fight.json.
"""
import contextlib
import hashlib
import io
import json
import math
import re
from pathlib import Path
from types import SimpleNamespace

import h063_fixtures as fx
from scripts.skilllab.arena import closeup, snapshot
from scripts.skilllab.catalogue import produce

CATALOGUE = fx.ROOT / "docs" / "northstar" / "research" / "layer_dynamics" / "catalogue"
PINS = {   # layout key -> (run.py arguments after --layout/--seed/--out/--allow-invalid, {file written, relative to the scratch directory: sha256})
    "L-0054": ((), {"out/L-0054-s1.fight.json": "c73540dc5526d1a3196d21f25e60707eb3eb703178881f28b189965484db466d"}),
    "L-0055": (("--control-dir", "control"), {"out/L-0055-s1.fight.json": "e69768138b6c1ee4994aa9455d3c1ace46c1b3ff110f54c7bf5487b6ea2b66b3",
                                             "control/L-0055-control-s1.fight.json": "eee998660cddf7ce75e89e705a5e8daeb4283661a536bd0cc788dc8bdad2e2bd"}),
    "L-0080": (("--sight", "on"), {"out/L-0080-s1.fight.json": "14f447e9fe638bc16710d3cd3b25810930b9b4779e1ce2611039ec04facf0b11"}),
}
HOLDER_CENTRE = (2000.0, 2000.0)
APPROACH = {"east": (1.0, 0.0), "north": (0.0, -1.0), "south": (0.0, 1.0), "west": (-1.0, 0.0)}
DISTANCE = 200.0
SLOPE_FEATURE = {"kind": "slope", "x": 2000.0, "y": 2000.0, "length": 600.0, "width": 200.0, "heading": 0.0, "from_band": 0, "to_band": 1}
SLOPE_FOOT, SLOPE_TOP, SLOPE_Y, SLOPE_HALF_WIDTH = 1700.0, 2300.0, 2000.0, 100.0
FRONT_DEG, REAR_DEG = 45.0, 135.0   # DRAFT-stage5-front-deg, DRAFT-stage5-rear-deg
ROUND_DEG = 0.25   # the fight file rounds facing to 3 decimals (0.03 deg) and positions to 2: an angle read back from it is good to well under this


def pinned_sha(path):
    """sha256 of the file with its one layout_path string replaced by the constant. See also: h088_fixtures._pinned_sha."""
    raw = Path(path).read_text()
    shown = json.dumps(json.loads(raw)["layout_path"])
    assert raw.count(shown) == 1
    return hashlib.sha256(raw.replace(shown, '"layout_path_pinned"').encode()).hexdigest()


def run_pin(key, directory, *extra):
    """Run the pinned fixture `key` into `directory` as the pin's commands say, plus `extra` flags, through the CLI in-process (as fx.run); returns (process, {file: sha256} of the files
    the pin names that were written)."""
    args, files = PINS[key]
    d = Path(directory)
    args = [str(d / a) if a == "control" else a for a in args]
    proc = fx.run(CATALOGUE / (key + ".toml"), d / "out", 1, *args, *extra)
    return proc, {name: pinned_sha(d / name) for name in files if (d / name).exists()}


def holder_block():
    """The holder's eight Vanguards, two ranks of four 40 wu apart, facing east, centred on HOLDER_CENTRE."""
    return [{"role": "Vanguard", "x": HOLDER_CENTRE[0] + dx, "y": HOLDER_CENTRE[1] + dy, "facing": 0.0, "layer": 0} for dx in (-20.0, 20.0) for dy in (-60.0, -20.0, 20.0, 60.0)]


def attacker_block(approach, distance=DISTANCE):
    """The attacker's eight Vanguards, two ranks of four across the line of approach from `approach` ('east', 'north', 'south', 'west' or a unit vector), the front rank at `distance`, facing the holder."""
    u = APPROACH.get(approach, approach)
    px, py = -u[1], u[0]
    face = round(math.atan2(-u[1], -u[0]), 4)
    return [{"role": "Vanguard", "x": round(HOLDER_CENTRE[0] + (distance + 40.0 * r) * u[0] + (k - 1.5) * 40.0 * px, 2), "y": round(HOLDER_CENTRE[1] + (distance + 40.0 * r) * u[1] + (k - 1.5) * 40.0 * py, 2),
             "facing": face, "layer": 0} for r in range(2) for k in range(4)]


def flank_layout(lid, approach="east", distance=DISTANCE):
    """The FLANK scene (module docstring): hold:A, side B attack-moves onto the holder's centre from `approach`."""
    return {"id": lid, "situation": "open_field", "landscape": "small_flat", "seed": 1, "predict": "B", "predict_why": "Test fixture.", "verdict": "", "feedback": "",
            "defender": "", "orders": "hold:A", "side_a": {"headcount": 8, "units": holder_block()}, "side_b": {"headcount": 8, "units": attacker_block(approach, distance)}}


def slope_layout(lid):
    """The SLOPE scene (module docstring)."""
    lay = fx.layout(lid, "slope", "small_tiered", dict(SLOPE_FEATURE), orders="hold:A")
    lay["side_a"] = {"headcount": 8, "units": [{"role": "Vanguard", "x": 2700.0 + (i // 4) * 40.0, "y": 1940.0 + (i % 4) * 40.0, "facing": round(math.pi, 4), "layer": 1} for i in range(8)]}
    lay["side_b"] = {"headcount": 8, "units": [{"role": "Vanguard", "x": 1000.0 + (i // 4) * 40.0, "y": 1940.0 + (i % 4) * 40.0, "facing": 0.0, "layer": 0} for i in range(8)]}
    return lay


def write_without_facing(lay, directory):
    """Write `lay` as a TOML with the `facing` key of every unit row removed (a layout that gives no facing)."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (lay["id"] + ".toml")
    path.write_text(re.sub(r"(?m)^facing = .*\n", "", produce.dump_toml(lay)))
    return path


def run_without_facing(lay, directory, *extra, seed=1):
    """The arena CLI on `lay` written with no `facing` key on any unit row (write_without_facing); returns (process, the fight document or None)."""
    path = write_without_facing(lay, Path(directory) / "layouts")
    proc = fx.run(path, Path(directory) / "out", seed, *extra)
    f = Path(directory) / "out" / ("%s-s%d.fight.json" % (lay["id"], seed))
    return proc, (snapshot.read(f) if f.exists() else None)


def closeup_doc(lay, directory, every, *extra, seed=1):
    """The closeup CLI (a frame every `every` ticks, no thinning) on `lay`, in-process; returns (process, the fight document or None). The file has more frames than snapshot.validate takes,
    so it is read as plain JSON, as the replay reads it."""
    path = fx.write(lay, Path(directory) / "layouts")
    out = Path(directory) / "closeup"
    buf, err = io.StringIO(), io.StringIO()
    argv = ["--layout", str(path), "--seed", str(seed), "--sight", "off", "--every-ticks", str(every), "--out", str(out), *[str(e) for e in extra]]
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
        try:
            code = closeup.main(argv)
        except SystemExit as e:
            code = e.code
    proc = SimpleNamespace(returncode=int(code or 0), stdout=buf.getvalue(), stderr=err.getvalue())
    f = out / ("%s-s%d-every%d.fight.json" % (lay["id"], seed, every))
    return proc, (json.loads(f.read_text()) if f.exists() else None)


def rows(doc):
    """{tick: {unit id: row}} for every frame of the document."""
    return {f["tick"]: {u["id"]: u for u in f["units"]} for f in doc["frames"]}


def off_deg(facing, bearing):
    """The angle between a facing and a bearing, radians in, degrees out, 0 to 180."""
    d = (bearing - facing + math.pi) % (2.0 * math.pi) - math.pi
    return abs(math.degrees(d))


def bearing(frm, to):
    return math.atan2(to["y"] - frm["y"], to["x"] - frm["x"])


def cls_of(angle):
    """front up to 45, rear from 135, side between (DRAFT-stage5-front-deg, DRAFT-stage5-rear-deg)."""
    return "front" if angle <= FRONT_DEG else "rear" if angle >= REAR_DEG else "side"


def hit_list(doc):
    """Every entry of every frame's `hits`, in file order."""
    return [h for f in doc["frames"] for h in f.get("hits", [])]


def shot_angle(doc, hit, at):
    """The angle (degrees) between the attacker's facing at tick `at` and the direction from the attacker to the victim at tick `at`, read from an every-tick document's rows
    (`at` is hit['tick'] - 1 for the facing the engine's rule reads: the facing at the START of the tick, csrc/unit.c om_tac_in_arc; positions are those after the tick)."""
    r_at, r_pos = rows(doc)[at], rows(doc)[hit["tick"]]
    return off_deg(r_at[hit["a"]]["facing"], bearing(r_pos[hit["a"]], r_pos[hit["v"]]))


def planted_doc(sides, last_tick, hits=(), pos=None, facing=None, climbing=None, every=1, arc_deg=90):
    """A hand-made stage 5 fight document with a known answer (nothing is run). `sides` {unit id: "A"|"B"}; frames at ticks 0, every, 2 every ... last_tick; `hits` [(tick, attacker, victim,
    off_deg, cls)] each placed in the first frame at or after its tick; a unit's row says `fired` in the frame that holds one of its shots and its `target` is its latest victim. `pos(id, t)`
    gives (x, y) (default (10 id, 0)), `facing(id, t)` radians (default 0.0), `climbing(id, t)` (default 0.0). Only the keys the stage 5 measures and checks read are filled
    in, plus the usual row keys; the document is not meant for snapshot.validate (an every-tick file has more frames than it takes)."""
    ticks = list(range(0, last_tick + 1, every))
    frames, prev, target = [], -1, {}
    for t in ticks:
        mine = [h for h in hits if prev < h[0] <= t]
        for _, a, v, _, _ in mine:
            target[a] = v
        units = []
        for uid in sorted(sides):
            x, y = (pos(uid, t) if pos else (10.0 * uid, 0.0))
            units.append({"id": uid, "side": sides[uid], "role": "Vanguard", "x": x, "y": y, "layer": 0, "facing": facing(uid, t) if facing else 0.0, "hp": 100.0, "alive": True,
                          "target": target.get(uid), "fired": any(h[1] == uid for h in mine), "climbing": climbing(uid, t) if climbing else 0.0})
        frames.append({"tick": t, "alive": [sum(1 for s in sides.values() if s == "A"), sum(1 for s in sides.values() if s == "B")], "units": units,
                       "hits": [{"a": a, "v": v, "tick": ht, "off_deg": d, "cls": c} for ht, a, v, d, c in mine]})
        prev = t
    return {"schema": "om-fight-2", "layout_id": "L-9999", "layout_path": "planted", "seed": 1, "tick_rate": 20, "snapshot_every": every, "sight": "off",
            "stage5": {"arc_deg": arc_deg, "slope_up_div": 1.1, "front_deg": 45, "rear_deg": 135}, "frames": frames,
            "result": {"winner": "A", "survivors": [sum(1 for s in sides.values() if s == "A"), sum(1 for s in sides.values() if s == "B")], "ticks": last_tick, "capped": False, "predict": "A",
                       "agree": True, "end": "wipe", "stall": False}}
