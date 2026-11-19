"""The approved fights, run as the lab's standing set (round6.md L2, DEC-regression-set-2026-11-18).

  python3 -m scripts.skilllab.arena.regression [--manifest PATH] [--catalogue DIR] [--situations DIR]

Runs every row of `docs/northstar/research/layer_dynamics/arena/approved.toml` at seed 1, one after another in this process, with the orders its layout names and nothing more (one attack-move a side
at tick 0; a trap's groups get theirs when it springs: `run.fight`, DEC-one-click-2026-11-18). A row of stage 3 or 4 names a control (`ground`: the twin with the features emptied; `sight`: targeting by
sight off) that runs as a second fight of the row on its own line. One line per fight, in manifest order:

  <id> sight=<on|off> end=<wipe|apart|silence|cap> winner=<A|B|stall|none> survivors=<a>:<b> ticks=<n> agree=<yes|no|-> checker=<none|rule[,rule...]>   [DRAW|APART]

`agree` compares the winner with his expected one (`-` when he expects a draw; a control is never compared); a disagreement alone is no failure. `checker` names every rule the checker reported in the fight (not only the first
`invariants.KEEP` reports the fight document keeps). DRAW marks a fight that ended with both sides alive; APART marks the one kind of that end the lab expects (round6.md L5: `run._apart`), with winner `none`, and is no failure.
Exit 0 only when every fight ended by elimination or apart and the checker reported nothing; a row the
catalogue's rejection rules refuse is a failure too, and so is a ground control that cannot fight (L6: its sides stand on layers the units cannot fire across by the layout's design; printed `cannot fight`, not run). The fights' winners and survivors are what `run._document` records.
"""
import argparse
import sys
import tempfile
import tomllib
from pathlib import Path

from scripts.skilllab.arena import run, situations, snapshot
from scripts.skilllab.catalogue.produce import check_layout, presets, rules

ROOT = Path(__file__).resolve().parents[3]
LD = ROOT / "docs" / "northstar" / "research" / "layer_dynamics"
SEED = 1


def _layout(row, catalogue, sit_dir, work):
    """(layout dict, path of its file) for a manifest row: a `layout` row is `<catalogue>/<id>.toml`; a `situation` row is converted alone into `work` as `L-<its number>`."""
    if "layout" in row:
        path = Path(catalogue) / (row["layout"] + ".toml")
    else:
        number = int(row["situation"].split("-")[1])
        src = Path(work) / ("src-" + row["situation"])
        src.mkdir()
        text = next(Path(sit_dir).glob(row["situation"] + "-*.md"))
        (src / text.name).write_text(text.read_text())
        lines, rejected = situations.convert(src, Path(work) / ("out-" + row["situation"]), "L-%04d" % number)
        if rejected:
            raise ValueError(lines[0].split(" ", 2)[2])
        path = Path(work) / ("out-" + row["situation"]) / ("L-%04d.toml" % number)
    with open(path, "rb") as f:
        return tomllib.load(f), path


def _refused(layout, sight):
    """The catalogue's rejection rules as run.main applies them to a fight, or None."""
    broken = check_layout(layout, presets(), rules())
    if broken:
        return " ".join(broken)
    wrong = run.layer_mismatch(layout) if sight == "on" else None
    if wrong:
        return "G1 layer: %s" % wrong
    miss = run.unreachable(layout, sight)
    return "%s unreachable: %s" % (run.REACH_RULE, miss) if miss else None


def _play(label, layout, path, sight, expected, control=False):
    """Run one fight; returns (its printed line, whether it passes). `sight` is "off", "on" or "control" (run.fight's names). A control is not held to the catalogue's rules, as `run.main` does
    not hold one: the ground control's twin has no features, which R6 (a layout carries its feature) refuses."""
    refused = None if control else _refused(layout, "off" if sight == "control" else sight)
    if refused:
        return "%s sight=%s REJECT %s" % (label, "on" if sight == "on" else "off", refused), False
    frames, last, end, orders = run.fight(layout, SEED, sight, snapshot.CAP_SECONDS)
    doc = run._document(layout, path, SEED, sight, frames, last, end, orders)
    res = doc["result"]
    rules_seen = orders["reported_rules"]   # every rule the checker reported; the document keeps only the first invariants.KEEP reports. See also: run.fight
    winner = "none" if res["end"] == "apart" else "stall" if res["winner"] == "draw" else res["winner"]
    agree = "-" if expected in (None, "draw") else "yes" if winner == expected else "no"
    line = "%s sight=%s end=%s winner=%s survivors=%d:%d ticks=%d agree=%s checker=%s" % (
        label, "on" if sight == "on" else "off", res["end"], winner, res["survivors"][0], res["survivors"][1], res["ticks"], agree, ",".join(rules_seen) or "none")
    if res["end"] == "apart":
        line += " APART"   # round6.md L5: expected without a player's micro; not a failure
    elif res["end"] != "wipe":
        line += " DRAW"
    return line, res["end"] in ("wipe", "apart") and not rules_seen


def _cannot_fight(twin, sight):
    """True when no unit of one side could fire at a unit of the other across the layers the twin gives them: the same layer, or (sight on) one layer down (`run.REACH_UP`, `run.REACH_DOWN`; sight
    off is reach (0, 0)). A control in which no shot can be fired measures nothing (round6.md L6). See also: run.control_twin."""
    up, down = (run.REACH_UP, run.REACH_DOWN) if sight == "on" else (0, 0)
    a = {u["layer"] for u in twin["side_a"]["units"]}
    b = {u["layer"] for u in twin["side_b"]["units"]}
    return not any(la == lb or (lb > la and lb - la <= up) or (lb < la and la - lb <= down) for la in a for lb in b)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m scripts.skilllab.arena.regression", description=__doc__.splitlines()[0])
    ap.add_argument("--manifest", type=Path, default=LD / "arena" / "approved.toml")
    ap.add_argument("--catalogue", type=Path, default=LD / "catalogue")
    ap.add_argument("--situations", type=Path, default=LD / "situations")
    args = ap.parse_args(argv)
    with open(args.manifest, "rb") as f:
        fights = tomllib.load(f)["fight"]
    failed = 0
    with tempfile.TemporaryDirectory(prefix="om-regression-") as work:
        for row in fights:
            label = row.get("layout") or row["situation"]
            try:
                layout, path = _layout(row, args.catalogue, args.situations, work)
            except ValueError as why:
                print("%s sight=%s REJECT %s" % (label, row["sight"], why), flush=True)
                failed += 1
                continue
            line, ok = _play(label, layout, path, row["sight"], row["expected_winner"])
            print(line, flush=True)
            failed += not ok
            if row["control"] == "none":
                continue
            if row["control"] == "sight":
                twin, twin_path, sight = layout, path, "control"
            else:
                twin, twin_path = run.control_twin(layout, path, Path(work) / "control")
                sight = row["sight"]
                if twin is None:
                    print("%s-control sight=%s REJECT no control twin: the engine is given nothing by this layout's features" % (label, sight), flush=True)
                    failed += 1
                    continue
            if sight != "control" and _cannot_fight(twin, sight):
                print("%s-control sight=%s cannot fight: the sides stand on layers the units cannot fire across, by the layout's design; not run" % (label, sight), flush=True)
                failed += 1
                continue
            line, ok = _play(label + "-control", twin, twin_path, sight, None, control=True)
            print(line, flush=True)
            failed += not ok
    print("regression: %d fights, %d failed" % (len(fights), failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
