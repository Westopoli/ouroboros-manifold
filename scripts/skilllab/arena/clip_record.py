"""The recorder half of the clip pipeline (scripts/skilllab/arena/clip.py runs it as `python -P <this file>` with cwd and PYTHONPATH at the engine tree, so an older tree
records its own engine; the file itself uses only names every tree has).

Writes the fight closeup writes for the same layout, seed and `--every` (sight off, or `--sight on`; H-091 `--facing on`, `--arc-deg N`, `--slope-up-div V`, as closeup takes them), with json.dump rather than one string. `--situation SIT-NNNN` converts the
situation as scripts/skilllab/arena/regression._layout does (needs `--work`). Prints `REJECT <id> <rule>` lines and exits 2 for a layout the lab rejects (as closeup),
else `WROTE <file name>` and exits 0."""
import argparse
import json
import sys
import tomllib
from pathlib import Path

from scripts.skilllab.arena import groups, situations, snapshot
from scripts.skilllab.arena.run import fight, _document, unreachable, REACH_RULE
from scripts.skilllab.catalogue.produce import check_layout, presets, rules

SITUATIONS = Path("docs/northstar/research/layer_dynamics/situations")


def _situation_layout(situation: str, work: Path) -> Path:
    src = work / ("src-" + situation)
    src.mkdir(parents=True)
    text = next(SITUATIONS.glob(situation + "-*.md"))
    (src / text.name).write_text(text.read_text())
    number = int(situation.split("-")[1])
    lines, rejected = situations.convert(src, work / ("out-" + situation), "L-%04d" % number)
    if rejected:
        print("REJECT %s %s" % (situation, lines[0].split(" ", 2)[2]))
        raise SystemExit(2)
    return work / ("out-" + situation) / ("L-%04d.toml" % number)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", type=Path)
    ap.add_argument("--situation")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--every", type=int, required=True)
    ap.add_argument("--sight", choices=("off", "on"), default="off")
    ap.add_argument("--facing", choices=("off", "on"), default="off")
    ap.add_argument("--arc-deg", type=int)
    ap.add_argument("--slope-up-div", type=float)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--work", type=Path)
    a = ap.parse_args(argv)
    if a.facing != "on" and (a.arc_deg is not None or a.slope_up_div is not None):
        ap.error("--arc-deg and --slope-up-div need --facing on")
    arc = None
    if a.facing == "on":
        from scripts.skilllab.arena.run import ARC_DEG_DEFAULT, ARC_DEG_MAX, ARC_DEG_MIN   # not at the top: an older tree has none, and records with the flags off
        arc = ARC_DEG_DEFAULT if a.arc_deg is None else a.arc_deg
        if not ARC_DEG_MIN <= arc <= ARC_DEG_MAX:
            ap.error("--arc-deg must be %d to %d" % (ARC_DEG_MIN, ARC_DEG_MAX))
    path = _situation_layout(a.situation, a.work) if a.situation else a.layout
    with open(path, "rb") as f:
        layout = tomllib.load(f)
    broken = check_layout(layout, presets(), rules())
    if broken:
        for rule in broken:
            print("REJECT %s %s" % (layout.get("id", path.stem), rule))
        return 2
    if layout.get("orders") == "groups":
        bad = groups.check(layout)
        if bad:
            print("REJECT %s G2 groups: %s" % (layout["id"], bad))
            return 2
    if a.sight == "on":
        from scripts.skilllab.arena.run import layer_mismatch   # not at the top: a stage 1 to 3 tree has none, and records with sight off
        wrong = layer_mismatch(layout)
        if wrong:
            print("REJECT %s G1 layer: %s" % (layout["id"], wrong))
            return 2
    miss = unreachable(layout, a.sight)
    if miss:
        print("REJECT %s %s unreachable: %s" % (layout["id"], REACH_RULE, miss))
        return 2
    stage5 = {"arc_deg": arc, "slope_up_div": a.slope_up_div} if arc is not None else {}   # passed only when facing is on: an older tree's fight() takes neither
    frames, last, end, orders = fight(layout, a.seed, a.sight, snapshot.CAP_SECONDS, a.every, **stage5)
    doc = _document(layout, path, a.seed, a.sight, frames, last, end, orders, a.every)
    a.out.mkdir(parents=True, exist_ok=True)
    name = "%s-s%d-every%d.fight.json" % (layout["id"], a.seed, a.every)
    with open(a.out / name, "w", encoding="utf-8") as f:
        json.dump(doc, f, sort_keys=True, indent=2)
        f.write("\n")
    print("WROTE %s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
