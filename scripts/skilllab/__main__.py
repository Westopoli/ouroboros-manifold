import argparse
import sys
from pathlib import Path

from scripts.skilllab import plays, report, rows, scan
from scripts.skilllab.contract import Batch

SIZE = 16
ENEMY_FROM, ENEMY_TO = 8, 24
REPLICATES = 10


def _scan_plays(out_dir, plays_by_label, csv_name, title):
    out_dir.mkdir(parents=True, exist_ok=True)
    scans, firing_example, fight_rows = {}, {}, []
    for label, build in plays_by_label.items():
        result = scan.scan(build, SIZE, ENEMY_FROM, ENEMY_TO, replicates=REPLICATES)
        scans[label] = result
        for cell in result.cells:
            if cell.enemy_heads == SIZE:
                firing_example[label] = cell.fights[0]
            for fight in cell.fights:
                fight_rows.append(rows.fight_row(fight, play=label, enemy_heads=cell.enemy_heads))
    csv_path = out_dir / csv_name
    rows.write_rows(fight_rows, csv_path)
    batch = Batch(title=title, scans=scans, firing_example=firing_example, rows=fight_rows)
    page = report.report(batch, out_dir)
    print(csv_path)
    print(page)
    return 0


def _controls(out_dir):
    plays_by_label = {"identical": plays.blob_play(SIZE), "damage": plays.damage_play(SIZE)}
    return _scan_plays(out_dir, plays_by_label, "controls.csv", "Skill lab controls")


def _reach(out_dir, factor):
    return _scan_plays(out_dir, {"reach": plays.reach_play(SIZE, factor=factor)}, "reach.csv",
                       "Skill lab reach control")


def _positive(text):
    value = float(text)
    if not value > 0 or value == float("inf"):
        raise argparse.ArgumentTypeError("must be a positive number, got %r" % (text,))
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="skilllab")
    parser.add_argument("command")
    parser.add_argument("--out", default="./skilllab_out")
    parser.add_argument("--factor", type=_positive, default=1.2)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if args.command == "controls":
        return _controls(Path(args.out))
    if args.command == "reach":
        return _reach(Path(args.out), args.factor)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
