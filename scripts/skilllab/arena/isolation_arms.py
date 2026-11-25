"""LI3, arms M and V of the lab isolation (docs/northstar/plans/lab-isolation-2026-11-24/spec.md sections 3, 4, 7; interface: docs/reports/2026-11-24-li3-interface.md).

Arm M: one role (Vanguard) both sides on flat featureless ground, sight off, the lab's one attack-move order a side; 16 against 8 to 48 and the 16 v 16 mirror, walkers.
Arm V: the same ground with sight on, one holder and one attack-mover (flat), and the four stage 4 layouts as authored; each with the lab's own sight-off twin (`--control sight`).
Every run goes through LI1's runner (`isolation_runner`) into a scratch tree and is read by LI2's measures (`isolation_measures`); this module issues no order and imports no engine.
A flag is a name from FLAGS, never a pass mark; only the stopping check of arm M (`blocks`) blocks a landing. Tests: tests/skilllab/integration/test_isolation_arms_*.py."""
import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace

from scripts.skilllab import scan as lab_scan
from scripts.skilllab.arena import isolation_measures as im
from scripts.skilllab.arena import isolation_runner as ir
from scripts.skilllab.catalogue.produce import dump_toml
from scripts.skilllab.invariants import NOTICE_MARGIN

OWN_HEADS = 16                              # README 4 (Westley's): the scan is "over 8 to 48 against 16"
SCAN_FROM, SCAN_TO = 8, 48                  # README 4 (Westley's)
SCAN_HEADS = tuple(range(SCAN_FROM, SCAN_TO + 1))   # README 4: every headcount
MIRROR_HEADS = 16                           # README 4 (Westley's): 16 against 16
V_HEADS = 16                                # DRAFT-v-heads: a side of the flat vision layouts
DRAFT_SCAN_SEEDS_10 = tuple(range(1, 11))   # DRAFT-scan-seeds-10: the default seeds of a cell (the flat fights do not change with the seed)
DRAFT_SPREAD_TICKS = (0, 500, 1000, 2000)   # DRAFT-spread-ticks: where LI2 reads each side's spread
DRAFT_HOLDER_STEP_WU = 15                   # DRAFT-holder-step: a holder further than this from its tick-0 place has stepped
DRAFT_FORMATION_PITCH_WU = 40.0             # DRAFT-formation-pitch-wu: the lab's own block pitch (catalogue/produce.py)
STAGE4_LAYOUTS = ("L-0061", "L-0080", "L-0083", "L-0039")
FLAGS = ("defect", "invalid", "orders_ended_short")
LD = ir.LD
FLAT = dict(situation="open_field", landscape="small_flat", predict="draw", predict_why="isolation arm", verdict="", feedback="")
NOT_MEASURED = "not measured at %s"


# ---------------------------------------------------------------- layouts

def _block(n, x0, direction):
    """`n` Vanguards in blocks of four columns at the lab's pitch, level at y 2000, facing the other side; the shape of the test layouts' flat ground."""
    return [{"role": "Vanguard", "x": x0 + direction * row * DRAFT_FORMATION_PITCH_WU, "y": 2000.0 + (col - 1.5) * DRAFT_FORMATION_PITCH_WU,
             "facing": 0.0 if direction < 0 else 3.14159, "layer": 0, "range": 300.0} for row, col in (divmod(i, 4) for i in range(n))]


def _layout(layout_id, heads_a, heads_b, orders, movement):
    return {"id": layout_id, "seed": 1, **FLAT, "orders": orders, "movement": movement,
            "side_a": {"headcount": heads_a, "units": _block(heads_a, 800.0, -1)},      # A west, spawned first
            "side_b": {"headcount": heads_b, "units": _block(heads_b, 3200.0, 1)}}      # B east


def layout_id_m(own, enemy, swap, movement="walk"):
    """`L-5000` and up for walkers, `L-6000` up for flyers: one id per (own, enemy, swap), both in SCAN_FROM..SCAN_TO, never a catalogue id of any version."""
    if not (SCAN_FROM <= own <= SCAN_TO and SCAN_FROM <= enemy <= SCAN_TO):
        raise ValueError("headcounts are %d to %d, not %d against %d" % (SCAN_FROM, SCAN_TO, own, enemy))
    span = SCAN_TO - SCAN_FROM + 1
    return "L-%04d" % (5000 + (1000 if movement == "fly" else 0) + 2 * ((own - SCAN_FROM) * span + enemy - SCAN_FROM) + int(bool(swap)))


def layout_id_v(heads, holder):
    return "L-%04d" % (9000 + heads + (100 if holder == "B" else 0))


def m_layout(own, enemy, swap=False, movement="walk"):
    """Side A has `own` units unless `swap` (exchanging the arguments); orders both_same_point; no features."""
    heads_a, heads_b = (enemy, own) if swap else (own, enemy)
    return _layout(layout_id_m(own, enemy, swap, movement), heads_a, heads_b, "both_same_point", movement)


def v_layout(heads, holder="A"):
    """The same ground and places whichever side holds; the other attacks."""
    return _layout(layout_id_v(heads, holder), heads, heads, "hold:" + holder, "walk")


def layout_toml(layout):
    """`dump_toml` plus the `movement` line it drops, before the first table (a top-level key)."""
    text = dump_toml(layout)
    cut = text.index("\n[side_a]")
    return text[:cut] + '\nmovement = "%s"' % layout["movement"] + text[cut:]


def _write_layout(tree, layout):
    path = Path(tree) / LD / "catalogue" / (layout["id"] + ".toml")
    path.write_text(layout_toml(layout))
    return path


# ---------------------------------------------------------------- pure readings of one fight document

def stopping_check(doc):
    """LI2's orders-ended-short over the fight file: the count of units alive at the end that stopped short of the point (listed), those that died short (listed apart, never counted); `blocks` None when the file carries no destination."""
    short = im.orders_ended_short(doc)
    if isinstance(short, str):
        return {"orders_ended_short": short, "units": [], "died_short": [], "blocks": None}
    count = len(short["alive_at_end"])
    return {"orders_ended_short": count, "units": short["alive_at_end"], "died_short": short["died"], "blocks": count > 0}


def blocks_of(doc, arm):
    """The one finding that blocks a landing: an order ended short in arm M (Westley, 2026-11-24)."""
    return arm == "M" and stopping_check(doc)["blocks"] is True


def flags_of(doc):
    flags = set()
    if im.result_of(doc)["defect"]:
        flags.add("defect")
    if doc.get("invalid"):
        flags.add("invalid")
    if stopping_check(doc)["blocks"]:
        flags.add("orders_ended_short")
    return sorted(flags)


def _holder(doc):
    orders = doc["orders"]
    if orders.get("mode") != "hold_and_attack":
        return "not measured: the orders are %s, no side holds" % orders.get("mode")
    side = "B" if orders["attacker"] == "A" else "A"
    home, away, stepped, fired, returned = {}, set(), False, False, False
    for frame in doc["frames"]:
        for u in frame["units"]:
            if u["side"] != side:
                continue
            home.setdefault(u["id"], (u["x"], u["y"]))
            if not u["alive"]:
                continue
            fired = fired or bool(u.get("fired"))
            if ((u["x"] - home[u["id"]][0]) ** 2 + (u["y"] - home[u["id"]][1]) ** 2) ** 0.5 > DRAFT_HOLDER_STEP_WU:
                stepped = True
                away.add(u["id"])
            elif u["id"] in away:
                returned = True
    return {"side": side, "stepped": stepped, "fired": fired, "returned": returned}


def vision_report(doc, version_name):
    """Sensor distance (the file's `sights`), notice distance (weapon range plus NOTICE_MARGIN of it, R-087-04), first seen, the holder, stand-off count, time to first shot; `not measured at <version>` where the file has none."""
    sights = doc.get("sights")
    seen = doc["result"].get("first_seen")
    short = stopping_check(doc)["orders_ended_short"]
    return {"sensor": dict(sights) if sights else NOT_MEASURED % version_name,
            "notice": {role: doc["ranges"][role] * (1 + NOTICE_MARGIN) for role in sights} if sights else NOT_MEASURED % version_name,
            "first_seen": seen if seen is not None else NOT_MEASURED % version_name,
            "holder": _holder(doc),
            "standoff_count": short if isinstance(short, int) and min(doc["result"]["survivors"]) > 0 else 0,
            "first_shot_tick": im.first_contact_tick(doc)}


def part_word_m(points):
    """C0 (README 4): the larger force wins both spawn orders, read in every cell where the numbers differ and no fight is a draw or cap."""
    read = []
    for p in points:
        if p["enemy_heads"] == p["own_heads"] or any(o in ("draw", "cap") for o in p["outcomes"]):
            continue
        read.append(all(o == ("side0" if p["own_heads"] > p["enemy_heads"] else "side1") for o in p["outcomes"]))
    if not read:
        return "no stated direction"
    return "pass" if all(read) else "fail"


def part_word_v(winner, expected):
    """The approved row's winner against the fight's; a layout with no ruling has no stated direction."""
    if expected not in ("A", "B"):
        return "no stated direction"
    return "pass" if winner == expected else "fail"


# ---------------------------------------------------------------- runs

def _json(x):
    """What a rows file does to a value (spread keys become strings)."""
    return json.loads(json.dumps(x, sort_keys=True))


def _measure(doc):
    return _json(im.measure_fight(doc, spread_ticks=DRAFT_SPREAD_TICKS))


def _prepare(name, layout, scratch_root, ref, repo):
    """Build the version and write the arm's layout into its scratch tree. A failure is left for the run itself to report as its error row."""
    try:
        tree = ir.build_version(ir.resolve_version(name, ref, repo), scratch_root, repo)
        _write_layout(tree, layout)
    except (ir.BuildError, OSError, ValueError):
        pass


def run_m(name, enemy, scratch_root, *, own=OWN_HEADS, swap=False, seed=10, movement="walk", ref=None, repo=None, out_dir=None):
    layout = m_layout(own, enemy, swap, movement)
    _prepare(name, layout, scratch_root, ref, repo)
    row = ir.run_one(name, layout["id"], seed, scratch_root, arm="M", ref=ref, repo=repo, out_dir=out_dir)
    row.update(own=own, enemy=enemy, swap=swap, own_side="B" if swap else "A", outcome=None, own_margin=None, movement=movement, measures=None, stopping=None, flags=[], blocks=False)
    if row["error"]:
        return row
    doc = im.load_fight(row["fight_path"])
    winner = im.result_of(doc)["winner"]
    row["outcome"] = winner if winner in ("draw", "cap") else "side0" if winner == row["own_side"] else "side1"
    row["own_margin"] = -row["margin"] if swap else row["margin"]
    row.update(measures=_measure(doc), stopping=_json(stopping_check(doc)), flags=flags_of(doc), blocks=blocks_of(doc, "M"))
    return row


def _point(own, enemy, rows):
    outcomes = [r["outcome"] for r in rows]
    return {"own_heads": own, "enemy_heads": enemy, "won": all(o == "side0" for o in outcomes), "defect": any(o in ("draw", "cap") for o in outcomes), "outcomes": outcomes,
            "mean_margin": statistics.mean(r["own_margin"] for r in rows), "fights": len(rows), "layouts": [r["layout"] for r in rows],
            "orders_ended_short": sum(r["stopping"]["orders_ended_short"] for r in rows), "idle_behind": sum(r["measures"]["idle_units"]["behind"] for r in rows),
            "idle_front": sum(r["measures"]["idle_units"]["front"] for r in rows), "max_overlap_pairs": max(r["measures"]["overlap"]["max_per_frame"] for r in rows),
            "first_contact_ticks": [r["measures"]["first_contact_tick"] for r in rows]}


def scan_m(name, scratch_root, *, heads=SCAN_HEADS, own=OWN_HEADS, seeds=DRAFT_SCAN_SEEDS_10, movement="walk", ref=None, repo=None, out_dir=None, rows_path=None):
    """Each headcount of `heads` against `own`: a cell is both spawn orders (swap False then True) over `seeds`, in that order. `rows_path` gets one JSONL line, flushed, per fight.
    A cell with an error row has no point (its error row is in `rows`, and the CLI exits 1)."""
    rows, points = [], []
    sink = open(rows_path, "w") if rows_path else None
    try:
        for enemy in heads:
            cell = []
            for swap in (False, True):
                for seed in seeds:
                    cell.append(run_m(name, enemy, scratch_root, own=own, swap=swap, seed=seed, movement=movement, ref=ref, repo=repo, out_dir=out_dir))
                    if sink:
                        sink.write(json.dumps(cell[-1], sort_keys=True) + "\n")
                        sink.flush()
            rows += cell
            if not any(r["error"] for r in cell):
                points.append(_point(own, enemy, cell))
    finally:
        if sink:
            sink.close()
    cells = [SimpleNamespace(enemy_heads=p["enemy_heads"], won=p["won"]) for p in points]
    beats, loses_to, ceiling_hit, multi_flip = lab_scan.read_cells(cells) if cells else (None, None, False, False)
    return {"arm": "M", "version": name, "lab_sha": rows[0]["lab_sha"] if rows else None, "own": own, "heads": list(heads), "seeds": list(seeds), "movement": movement,
            "spread_ticks": list(DRAFT_SPREAD_TICKS), "points": points, "beats": beats, "loses_to": loses_to, "ceiling_hit": ceiling_hit, "multi_flip": multi_flip,
            "flips": [{"before": a.enemy_heads, "after": b.enemy_heads, "direction": "win_to_loss" if a.won else "loss_to_win"} for a, b in zip(cells, cells[1:]) if a.won != b.won],
            "part_word": part_word_m(points), "blocks": any(r["blocks"] for r in rows), "mirror": next((p for p in points if p["enemy_heads"] == own), None), "rows": rows}


def _result_cell(doc):
    res = doc["result"]
    return {"winner": res["winner"], "survivors": res["survivors"], "last_tick": res["ticks"], "end": res["end"]}


def _lab_with_twin(tree, layout_id, seed, out):
    """The version's own lab once, sight on with its sight-off twin: (fight file or None, twin file or None, the process). Exit 2 with the fight file written is a fight the rule checker marked invalid."""
    path = out / ("%s-s%d.fight.json" % (layout_id, seed))
    path.unlink(missing_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    done = subprocess.run([sys.executable, "-m", "scripts.skilllab.arena.run", "--layout", str(tree / LD / "catalogue" / (layout_id + ".toml")), "--seed", str(seed), "--out", str(out),
                           "--sight", "on", "--control-dir", str(out / "ctl"), "--control", "sight"], cwd=str(tree), capture_output=True, text=True)
    twin = out / "ctl" / ("%s-control-s%d.fight.json" % (layout_id, seed))
    return (path if path.is_file() else None), (twin if twin.is_file() else None), done


def _run_v(name, layout_id, layout, seed, scratch_root, *, kind, heads, holder, expected, ref, repo, out_dir):
    scratch_root = Path(scratch_root)
    row = {"version": name, "lab_sha": None, "arm": "V", "layout": layout_id, "seed": seed, "result": None, "margin": None, "units_firing": None, "fight_path": None, "fight_sha256": None,
           "error": None, "kind": kind, "heads": heads, "holder": holder, "sight": None, "expected_winner": expected, "part_word": None, "measures": None, "vision": None, "twin": None,
           "flags": [], "blocks": False}
    try:
        version = ir.resolve_version(name, ref, repo)
        row["lab_sha"] = version.sha
        tree = ir.build_version(version, scratch_root, repo)
        if layout:
            _write_layout(tree, layout)
        elif not (tree / LD / "catalogue" / (layout_id + ".toml")).is_file():
            raise ir.BuildError("layout", "unknown layout %s" % layout_id)
        out = Path(out_dir or scratch_root / "fights").resolve() / ("%s-%s-V-%s" % (name, version.sha[:12], layout_id))
        path, twin_path, done = _lab_with_twin(tree, layout_id, seed, out)
        if path is None:
            raise ir.BuildError("layout" if done.returncode == 2 else "fight", (done.stderr + done.stdout)[-ir.TAIL:].strip() or "the lab wrote no fight file (exit %d)" % done.returncode)
        doc = im.load_fight(path)
        twin = NOT_MEASURED % name
        if twin_path:
            twin_doc = im.load_fight(twin_path)
            twin = {"sight": twin_doc["sight"], "result": _result_cell(twin_doc), "fight_path": str(twin_path), "fight_sha256": hashlib.sha256(twin_path.read_bytes()).hexdigest(),
                    "invalid": bool(twin_doc.get("invalid"))}
        row.update(result=_result_cell(doc), margin=doc["result"]["survivors"][0] - doc["result"]["survivors"][1], units_firing=ir.units_firing(doc, name), fight_path=str(path),
                   fight_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), sight=doc["sight"], part_word=part_word_v(doc["result"]["winner"], expected), measures=_measure(doc),
                   vision=_json(vision_report(doc, name)), twin=twin, flags=flags_of(doc))
    except ir.BuildError as err:
        row["error"] = {"stage": err.stage, "message": err.args[0]}
    except (OSError, ValueError, KeyError, IndexError) as err:      # a fight file the lab wrote but this arm cannot read: said, not skipped
        row["error"] = {"stage": "fight", "message": "%s: %s" % (type(err).__name__, err)}
    return row


def run_v_flat(name, scratch_root, *, heads=V_HEADS, holder="A", seed=10, ref=None, repo=None, out_dir=None):
    layout = v_layout(heads, holder)
    return _run_v(name, layout["id"], layout, seed, scratch_root, kind="flat", heads=heads, holder=holder, expected=None, ref=ref, repo=repo, out_dir=out_dir)


def run_v_stage4(name, layout, scratch_root, *, seed=10, ref=None, repo=None, out_dir=None):
    """A stage 4 layout as authored (the version's own catalogue file, never rewritten); the expected winner is the approved row's."""
    if layout not in STAGE4_LAYOUTS:
        raise ValueError("%s is not a stage 4 layout of the lab isolation: %s" % (layout, ", ".join(STAGE4_LAYOUTS)))
    with open((repo or ir.REPO) / LD / "arena" / "approved.toml", "rb") as f:
        expected = {r["layout"]: r for r in tomllib.load(f)["fight"] if r["stage"] == 4}[layout]["expected_winner"]
    return _run_v(name, layout, None, seed, scratch_root, kind="stage4", heads=None, holder=None, expected=expected, ref=ref, repo=repo, out_dir=out_dir)


def main(argv=None):
    """Arm M: the scan's fight rows to --rows. Arm V: the flat pair (holder A, holder B at V_HEADS) and the four stage 4 layouts. Exit 1 when any row is an error row."""
    ap = argparse.ArgumentParser(prog="python3 -m scripts.skilllab.arena.isolation_arms")
    ap.add_argument("--arm", required=True, choices=("M", "V"))
    ap.add_argument("--version", required=True, choices=("then", "now", "fix"))
    ap.add_argument("--ref")
    ap.add_argument("--heads", help="comma list, default every headcount 8 to 48 (arm M)")
    ap.add_argument("--seeds", help="comma list of seeds, default DRAFT_SCAN_SEEDS_10 (arm M)")
    ap.add_argument("--scratch", required=True, type=Path)
    ap.add_argument("--rows", required=True, type=Path)
    ap.add_argument("--repo", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    if args.version == "fix" and not args.ref:
        ap.error("--version fix needs --ref")
    if args.arm == "M":
        heads = [int(x) for x in args.heads.split(",")] if args.heads else SCAN_HEADS
        seeds = [int(x) for x in args.seeds.split(",")] if args.seeds else DRAFT_SCAN_SEEDS_10
        rows = scan_m(args.version, args.scratch, heads=heads, seeds=seeds, ref=args.ref, repo=args.repo, out_dir=args.out, rows_path=args.rows)["rows"]
    else:
        kw = dict(ref=args.ref, repo=args.repo, out_dir=args.out)
        rows = [run_v_flat(args.version, args.scratch, holder=h, **kw) for h in "AB"] + [run_v_stage4(args.version, lay, args.scratch, **kw) for lay in STAGE4_LAYOUTS]
        ir.write_rows(rows, args.rows)
    for row in rows:
        err = row["error"]
        print("%s %s %s seed %d %s" % (row["version"], row["lab_sha"], row["layout"], row["seed"], "ERROR %s: %s" % (err["stage"], err["message"]) if err else "ok"))
    return 1 if any(r["error"] for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
