"""Closeup: the arena runner's fight with a frame every K ticks, to watch it like a video (spec: docs/stories/H-088.md; Westley's request 2026-11-07).

CLI: python3 -m scripts.skilllab.arena.closeup --layout <toml> --seed <int> --sight off|on|control --every-ticks K --out <dir> [--from-tick A --to-tick B]
It runs the fight `run.py` runs (`run.fight`, `run._document`; `--sight control` is `run.py --sight on --control sight`'s control file: stage 4 with targeting by sight off)
and keeps a frame at tick 0, K, 2K ... and the last tick, with no thinning to snapshot.MAX_FRAMES. With `--from-tick A` and/or `--to-tick B` only frames with
A <= tick <= B are written (tick 0 is then not forced). One file, `<id>[-control]-s<seed>-every<K>.fight.json`, `snapshot_every` K, `result` the normal runner's.
The file has more frames than `snapshot.validate` accepts: it is for the replay (scenes/proto/fight_replay, OM_FPS), not for `snapshot.read` or the page (SNAPSHOT.md).
Exit 0 with a FIGHT line, 2 for REJECT lines or a bad K, 1 when the window holds no frame (nothing is written)."""
import argparse
import json
import sys
import tomllib
from pathlib import Path

from scripts.skilllab.arena import groups, snap, snapshot
from scripts.skilllab.arena.run import fight, _document, layer_mismatch, unreachable, REACH_RULE
from scripts.skilllab.catalogue.produce import check_layout, presets, rules


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m scripts.skilllab.arena.closeup")
    ap.add_argument("--layout", required=True, type=Path)
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--sight", choices=("off", "on", "control"), default="off")
    ap.add_argument("--every-ticks", required=True, type=int, help="a frame every K ticks (20 ticks a second), K >= 1")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--from-tick", type=int, help="keep frames from this tick on (tick 0 is not forced)")
    ap.add_argument("--to-tick", type=int, help="keep frames up to this tick")
    args = ap.parse_args(argv)
    if args.every_ticks < 1:
        ap.error("--every-ticks must be at least 1")
    if args.from_tick is not None and args.to_tick is not None and args.from_tick > args.to_tick:
        ap.error("--from-tick %d is after --to-tick %d" % (args.from_tick, args.to_tick))
    with open(args.layout, "rb") as f:
        layout = tomllib.load(f)
    broken = check_layout(layout, presets(), rules())
    if broken:
        for rule in broken:
            print("REJECT %s %s" % (layout.get("id", args.layout.stem), rule))
        return 2
    if layout.get("orders") == "groups":
        bad = groups.check(layout)
        if bad:
            print("REJECT %s G2 groups: %s" % (layout["id"], bad))
            return 2
    ground = "off" if args.sight == "off" else "on"   # the checks run.py makes for `--sight on` also guard the control
    wrong = layer_mismatch(layout) if ground == "on" else None
    if wrong:
        print("REJECT %s G1 layer: %s" % (layout["id"], wrong))
        return 2
    miss = unreachable(layout, ground)
    if miss:
        print("REJECT %s %s unreachable: %s" % (layout["id"], REACH_RULE, miss))
        return 2
    if ground == "on":
        for line in snap.report(layout):
            print(line)
    frames, last, end, orders = fight(layout, args.seed, args.sight, snapshot.CAP_SECONDS, args.every_ticks)
    doc = _document(layout, args.layout, args.seed, args.sight, frames, last, end, orders, args.every_ticks)
    doc["frames"] = [f for f in doc["frames"]
                     if (args.from_tick is None or f["tick"] >= args.from_tick) and (args.to_tick is None or f["tick"] <= args.to_tick)]
    if not doc["frames"]:
        print("no frame between tick %s and tick %s (the fight ends at tick %d); nothing written" % (args.from_tick, args.to_tick, last), file=sys.stderr)
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    name = "%s%s-s%d-every%d.fight.json" % (layout["id"], "-control" if args.sight == "control" else "", args.seed, args.every_ticks)
    (args.out / name).write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")   # not snapshot.write: it refuses more than MAX_FRAMES frames
    print("FIGHT %s seed %d winner %s ticks %d frames %d every %d -> %s" % (layout["id"], args.seed, doc["result"]["winner"], last, len(doc["frames"]), args.every_ticks, name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
