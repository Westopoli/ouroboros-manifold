import argparse
import dataclasses
import json
import sys
from pathlib import Path

from scripts.skilllab import batches, diagram, plays, report, rows, scan, sweep
from scripts.skilllab.contract import Batch
from scripts.skilllab.evidence import Thresholds

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


def _thresholds(path):
    """Westley's pass marks from a JSON object holding every field of evidence.Thresholds; raises ValueError naming what is wrong."""
    fields = [f.name for f in dataclasses.fields(Thresholds)]
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError("cannot read thresholds file %s: %s" % (path, e)) from None
    if not isinstance(data, dict):
        raise ValueError("thresholds file %s must hold a JSON object" % path)
    missing, unknown = [k for k in fields if k not in data], [k for k in data if k not in fields]
    if missing or unknown:
        raise ValueError("thresholds file %s: missing %s; unknown %s" % (path, ", ".join(missing) or "none", ", ".join(unknown) or "none"))
    return Thresholds(**{k: tuple(v) if isinstance(v, list) else v for k, v in data.items()})


def _artifact(directory, thresholds_path):
    if directory is None:
        print("artifact needs a directory: artifact <dir> [--thresholds <file.json>]")
        return 2
    d = Path(directory)
    if not (d / "sweep_summary.json").is_file():
        print("artifact: %s holds no sweep_summary.json" % d)
        return 2
    try:
        thresholds = None if thresholds_path is None else _thresholds(thresholds_path)
    except ValueError as e:
        print("artifact: %s" % e)
        return 2
    summary = json.loads((d / "sweep_summary.json").read_text(encoding="utf-8"))
    files = [d / summary["families"][f]["csv"] for f in summary["order"] if summary["families"][f].get("csv")]
    files += [d / "smoke.csv"] * (d / "smoke.csv").is_file()
    csv_rows = [r for path in files for r in diagram.read_rows(path)]
    layouts = []

    def setup_for(notable):
        if not layouts:
            layouts.append(sweep.smoke_layouts())
        if notable.layout not in layouts[0]:
            raise ValueError("layout %s is not a smoke layout, so its diagram cannot be built" % notable.layout)
        return sweep.default_builds(notable.play, "play", layouts[0][notable.layout])(notable.heads, False)

    try:
        page = report.artifact(summary, csv_rows, setup_for, d, thresholds=thresholds)
    except ValueError as e:
        print("artifact: %s" % e)
        return 2
    print(page)
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
    parser.add_argument("--thresholds", default=None, help="artifact only: a JSON file of Westley's pass marks (every Thresholds field)")
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
    if args.command == "artifact":
        return _artifact(args.name, args.thresholds)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
