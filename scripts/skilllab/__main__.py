import argparse
import sys
from pathlib import Path

from scripts.skilllab import plays, report, rows, scan
from scripts.skilllab.contract import Batch

SIZE = 16
ENEMY_FROM, ENEMY_TO = 8, 24
REPLICATES = 10


def _controls(out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    plays_by_label = {"identical": plays.blob_play(SIZE), "reach": plays.reach_play(SIZE)}
    scans, firing_example, fight_rows = {}, {}, []
    for label, build in plays_by_label.items():
        result = scan.scan(build, SIZE, ENEMY_FROM, ENEMY_TO, replicates=REPLICATES)
        scans[label] = result
        for cell in result.cells:
            if cell.enemy_heads == SIZE:
                firing_example[label] = cell.fights[0]
            for fight in cell.fights:
                fight_rows.append(rows.fight_row(fight, play=label, enemy_heads=cell.enemy_heads))
    csv_path = out_dir / "controls.csv"
    rows.write_rows(fight_rows, csv_path)
    batch = Batch(title="Skill lab controls", scans=scans, firing_example=firing_example, rows=fight_rows)
    page = report.report(batch, out_dir)
    print(csv_path)
    print(page)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="skilllab")
    parser.add_argument("command")
    parser.add_argument("--out", default="./skilllab_out")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if args.command == "controls":
        return _controls(Path(args.out))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
