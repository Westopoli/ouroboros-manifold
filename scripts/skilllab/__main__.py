import argparse
import sys
from pathlib import Path

from scripts.skilllab import batches, plays, report, rows, scan, sweep
from scripts.skilllab.contract import Batch

SIZE = 16
ENEMY_FROM, ENEMY_TO = 8, 24
REPLICATES = 10


def _scan_plays(out_dir, plays_by_label, csv_name, title):
    out_dir.mkdir(parents=True, exist_ok=True)
    scans, firing_example, fight_rows = {}, {}, []
    for label, build in plays_by_label.items():
        result = scan.scan(build, SIZE, ENEMY_FROM, ENEMY_TO, replicates=REPLICATES, full_scan=True)   # a dot per fight at every headcount
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


def _batch(name, out_dir, workers=1, layouts=200):
    if name == "layout_search":
        for path in batches.layout_search(layouts, 0, workers, out_dir).values():
            print(path)
        return 0
    try:
        defn = batches.get(name) if name else None
    except ValueError:
        defn = None
    if defn is None:
        print("batch needs one of: " + ", ".join(batches.NAMES))
        return 2
    for path in batches.run(defn, out_dir, workers=workers).values():
        print(path)
    return 0


def _sweep(name, out_dir, workers, full_scan):
    if name in (None, "all"):
        families = list(sweep.FAMILY_ORDER)
    elif name in sweep.FAMILY_ORDER:
        families = [name]
    else:
        print("sweep needs one of: all, " + ", ".join(sweep.FAMILY_ORDER))
        return 2
    summary = sweep.run(families, out_dir, workers=workers, full_scan=full_scan)
    for entry in summary["families"].values():
        if entry.get("csv"):
            print(out_dir / entry["csv"])
    print(out_dir / "sweep_summary.json")
    return 0


def _smoke(out_dir, workers, full_scan):
    summary = sweep.run_smoke(out_dir, workers=workers, full_scan=full_scan)
    print(out_dir / "smoke.csv")
    print(out_dir / "smoke_summary.json")
    print("rows sha256 " + summary["rows_sha256"])
    return 0


def _workers(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a positive whole number, got %r" % (text,)) from None
    if value < 1:
        raise argparse.ArgumentTypeError("must be a positive whole number, got %r" % (text,))
    return value


def _positive(text):
    value = float(text)
    if not value > 0 or value == float("inf"):
        raise argparse.ArgumentTypeError("must be a positive number, got %r" % (text,))
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="skilllab")
    parser.add_argument("command")
    parser.add_argument("name", nargs="?")
    parser.add_argument("--out", default="./skilllab_out")
    parser.add_argument("--factor", type=_positive, default=1.2)
    parser.add_argument("--workers", type=_workers, default=None,
                        help="batch, sweep and smoke: fight in this many worker processes (default 1; smoke 12)")
    parser.add_argument("--full-scan", action="store_true",
                        help="sweep and smoke: fight every headcount 8 to 48 instead of bisecting (controls and reach always do)")
    parser.add_argument("--layouts", type=_workers, default=200, help="batch layout_search only: how many layouts to draw (default 200)")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if args.command == "controls":
        return _controls(Path(args.out))
    if args.command == "reach":
        return _reach(Path(args.out), args.factor)
    if args.command == "batch":
        return _batch(args.name, Path(args.out), args.workers or 1, args.layouts)
    if args.command == "sweep":
        return _sweep(args.name, Path(args.out), args.workers or 1, args.full_scan)
    if args.command == "smoke":
        return _smoke(Path(args.out), args.workers or 12, args.full_scan)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
