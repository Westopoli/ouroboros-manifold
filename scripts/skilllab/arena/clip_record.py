"""The recorder half of the clip pipeline (scripts/skilllab/arena/clip.py runs it as `python -P <this file>` with cwd and PYTHONPATH at the engine tree, so an older tree
records its own engine; the file itself uses only names every tree has).

Writes the fight closeup writes for the same layout, seed and `--every` (sight off), with json.dump rather than one string. `--situation SIT-NNNN` converts the
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
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--work", type=Path)
    a = ap.parse_args(argv)
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
    miss = unreachable(layout, "off")
    if miss:
        print("REJECT %s %s unreachable: %s" % (layout["id"], REACH_RULE, miss))
        return 2
    frames, last, end, orders = fight(layout, a.seed, "off", snapshot.CAP_SECONDS, a.every)
    doc = _document(layout, path, a.seed, "off", frames, last, end, orders, a.every)
    a.out.mkdir(parents=True, exist_ok=True)
    name = "%s-s%d-every%d.fight.json" % (layout["id"], a.seed, a.every)
    with open(a.out / name, "w", encoding="utf-8") as f:
        json.dump(doc, f, sort_keys=True, indent=2)
        f.write("\n")
    print("WROTE %s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
