# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md, piece LI3 (arms M and V); interface: docs/reports/2026-11-24-li3-interface.md
"""Helpers shared by test_isolation_arms_*.py. The module under test is imported lazily so a missing module fails each test (red), not the collection.

Premises dumped 2026-11-24 on this branch (li3, main 893a5af7f), one flat layout of 16 Vanguards a side (positions: blocks of four columns at pitch 40, A west at x 800, B east at x 3200, y about 2000,
canvas small_flat 4000 x 4000, situation open_field, orders both_same_point), run by the runner on `now` and `then` (about 14 s a fight, the build 13 s):
- the fight file is `om-fight-2`, `sight` "off", `orders` {mode both_same_point, point [2000, 2000], attacker null}, `ranges` {Vanguard: 300}; no `sights`; `then` writes no per-unit `fired`;
- 16 v 16 is mirror-exact: swapping which side is which gives the same fight, the winner follows the side (A at `now`, B at `then`), never the force; `swap` therefore only changes who is "own";
- the lab's `--sight on` gives `sights` {Vanguard: 700}, `result.first_seen` {A, B}, `orders.guard` (hold:A), and `--control sight` writes a sight-off twin `ctl/<id>-control-s<seed>.fight.json` at `now`; at `then` the same flags
  give a fight file with none of those and no twin; `then` on L-0061 with `--sight on` is a STALL (both sides alive at tick 460, end silence).
Versions: `now` = origin/main of this worktree's repository (the runner resolves it)."""
import importlib
import json
import re
import subprocess
from pathlib import Path

import isolation_fixtures as fx

ROOT, PY, THEN_SHA = fx.ROOT, fx.PY, fx.THEN_SHA
LD = "docs/northstar/research/layer_dynamics"
ROW_KEYS = fx.ROW_KEYS
STAGE4 = ("L-0061", "L-0080", "L-0083", "L-0039")
PASS_MARK_KEYS = {"pass", "passed", "fail", "failed", "ok", "verdict", "score", "threshold", "tolerance", "pass_mark"}
ID_RE = re.compile(r"L-\d{4}")


def arms():
    return importlib.import_module("scripts.skilllab.arena.isolation_arms")


def measures():
    return importlib.import_module("scripts.skilllab.arena.isolation_measures")


def roundtrip(x):
    """What a rows file does to a value: the JSON text of it and back."""
    return json.loads(json.dumps(x, sort_keys=True))


def flat_layout(layout_id, a, b, orders="both_same_point"):
    """A TEST-LOCAL flat featureless layout of `a` Vanguards (A, west) against `b` (B, east), for the controls only; the arm builds its own (`arms.m_layout`)."""
    def block(n, x0, direction):
        return [{"role": "Vanguard", "x": x0 + direction * r * 40.0, "y": 2000.0 + (k - 1.5) * 40.0, "facing": 0.0 if direction < 0 else 3.14159, "layer": 0, "range": 300.0}
                for r, k in (divmod(i, 4) for i in range(n))]
    ua, ub = block(a, 800.0, -1), block(b, 3200.0, 1)
    return {"id": layout_id, "situation": "open_field", "landscape": "small_flat", "seed": 1, "predict": "draw", "predict_why": "control", "verdict": "", "feedback": "", "orders": orders,
            "side_a": {"headcount": a, "units": ua}, "side_b": {"headcount": b, "units": ub}}


def put_layout(tree, layout):
    """Write a layout into a scratch TREE's catalogue (never the repository's); the path."""
    from scripts.skilllab.catalogue.produce import dump_toml
    path = Path(tree) / LD / "catalogue" / (layout["id"] + ".toml")
    path.write_text(dump_toml(layout))
    return path


def tree_of(name, scratch):
    ir = fx.runner()
    return ir.build_version(ir.resolve_version(name, repo=ROOT), scratch, repo=ROOT)


def lab(tree, layout_path, seed, out, *flags):
    """The version's own lab, as a tool would call it: (completed process, fight file path)."""
    done = subprocess.run([PY, "-m", "scripts.skilllab.arena.run", "--layout", str(layout_path), "--seed", str(seed), "--out", str(out), *flags], cwd=str(tree), capture_output=True, text=True)
    return done, Path(out) / ("%s-s%d.fight.json" % (Path(layout_path).stem, seed))


def catalogue_ids(sha):
    """The L-#### ids of a version's committed catalogue."""
    names = fx.git(ROOT, "ls-tree", "--name-only", sha, LD + "/catalogue/").splitlines()
    return {Path(n).stem for n in names if n.endswith(".toml")}


def fight_lab_calls(calls):
    """The argv lists of the calls that ran the arena lab."""
    return [c for c in calls if "scripts.skilllab.arena.run" in " ".join(map(str, c))]


def flag_value(argv, flag):
    argv = list(map(str, argv))
    return argv[argv.index(flag) + 1] if flag in argv else None


# ---------------------------------------------------------------- synthetic fight documents (om-fight-2) with a known answer

TICKS = list(range(0, 1601, 100))
POINT = [2000.0, 2000.0]


def doc(roster, pos, *, alive=None, target=None, fired=None, orders=None, result=None, ranges=None, sights=None, first_seen=None, ticks=TICKS, sight="off", extra=None, with_fired=True):
    """roster [(id, side, role)]; pos(id, tick) -> (x, y); alive(id, tick) -> bool (default True); target(id, tick); fired(id, tick). Valid shape: dead units stay in every frame with hp 0."""
    frames = []
    for t in ticks:
        rows = []
        for uid, side, role in sorted(roster):
            up = alive(uid, t) if alive else True
            x, y = pos(uid, t)
            row = {"id": uid, "side": side, "role": role, "x": round(x, 2), "y": round(y, 2), "layer": 0, "facing": 0.0, "hp": 500.0 if up else 0.0, "alive": bool(up),
                   "target": target(uid, t) if (target and up) else None}
            if with_fired:
                row["fired"] = bool(fired(uid, t)) if (fired and up) else False
            rows.append(row)
        frames.append({"tick": t, "alive": [sum(1 for r in rows if r["alive"] and r["side"] == s) for s in "AB"], "units": rows})
    surv = frames[-1]["alive"]
    winner = "A" if surv[0] and not surv[1] else "B" if surv[1] and not surv[0] else "none"
    d = {"schema": "om-fight-2", "layout_id": "L-9999", "layout_path": "synthetic.toml", "seed": 1, "tick_rate": 20, "snapshot_every": 100, "sight": sight, "landscape": "small_flat",
         "orders": orders or {"attacker": None, "mode": "both_same_point", "point": list(POINT)}, "ranges": ranges or {"Vanguard": 300.0}, "frames": frames,
         "result": result or {"winner": winner, "survivors": surv, "ticks": ticks[-1], "capped": False, "end": "wipe" if winner != "none" else "silence", "stall": winner == "none", "predict": "A", "agree": winner == "A"}}
    if sights:
        d["sights"] = sights
    if first_seen:
        d["result"]["first_seen"] = first_seen
    d.update(extra or {})
    return d


def clean_doc():
    """A wipe: A1 and A2 end at the point, B1 died at tick 800. Nothing is still short of the point. Orders: both_same_point."""
    roster = [(1, "A", "Vanguard"), (2, "A", "Vanguard"), (11, "B", "Vanguard")]
    paths = {1: lambda t: (min(1000.0 + 1.0 * t, 2000.0), 2000.0), 2: lambda t: (min(1000.0 + 1.0 * t, 2010.0), 2040.0), 11: lambda t: (3000.0 - 0.5 * min(t, 800), 2000.0)}
    return doc(roster, lambda u, t: paths[u](t), alive=lambda u, t: not (u == 11 and t > 800), fired=lambda u, t: u in (1, 2) and 400 <= t <= 800)


def short_doc(also_dead=False):
    """Unit A1 stops at tick 600 at (400, 400), 1,600 wu from the point, no target, no enemy near, and stays so to tick 1600 (1,000 ticks, far above DRAFT_STUCK_TICKS): an order ended short, alive at the end.
    A2 walks to the point and stays (arrived). B1 dies at tick 500. With also_dead, A3 does the same as A1 but dies at tick 1400 (listed apart from the alive ones)."""
    roster = [(1, "A", "Vanguard"), (2, "A", "Vanguard"), (11, "B", "Vanguard")] + ([(3, "A", "Vanguard")] if also_dead else [])
    paths = {1: lambda t: (100.0 + 0.5 * min(t, 600), 400.0), 2: lambda t: (min(1000.0 + 1.0 * t, 2000.0), 2000.0), 11: lambda t: (3000.0 - 0.5 * min(t, 500), 3000.0), 3: lambda t: (100.0 + 0.5 * min(t, 600), 900.0)}
    return doc(roster, lambda u, t: paths[u](t), alive=lambda u, t: not (u == 11 and t > 500) and not (u == 3 and t > 1400), fired=lambda u, t: u == 2 and 300 <= t <= 500)


def draw_doc():
    """Both sides alive at the end (a stall): winner stall, end silence; both stand within 75 wu of the point (arrived), so no order ended short."""
    roster = [(1, "A", "Vanguard"), (11, "B", "Vanguard")]
    return doc(roster, lambda u, t: (1980.0, 2000.0) if u == 1 else (2020.0, 2000.0), fired=lambda u, t: t == 300,
               result={"winner": "stall", "survivors": [1, 1], "ticks": 1600, "capped": False, "end": "silence", "stall": True, "predict": "A", "agree": False})


def vision_doc(holder_steps=True, holder_fires=True, both_alive=False):
    """A sight-on hold:A fight (om-fight-2 with `sights`, `result.first_seen`, `orders.guard`): holder A (id 1, 2), attacker B (id 11, 12), Vanguard, range 300, sensor 700.
    A1 anchors at (800, 2000); with holder_steps it walks out 40 wu at tick 500, stays to 700, is back at its anchor at tick 800 (stepped and returned); A1 fires at tick 600 when holder_fires. A2 never moves.
    Attackers walk from x 3200 to 900 by tick 1200. B dies at tick 1000 unless both_alive (then B1 stays alive at (1700, 2000) and A1 alive: a stand-off)."""
    roster = [(1, "A", "Vanguard"), (2, "A", "Vanguard"), (11, "B", "Vanguard"), (12, "B", "Vanguard")]

    def pos(u, t):
        if u == 1:
            out = 40.0 if (holder_steps and 500 <= t <= 700) else 0.0
            return 800.0 + out, 2000.0
        if u == 2:
            return 800.0, 2040.0
        x = 3200.0 - 2300.0 * min(t, 1200) / 1200.0 + (0 if u == 11 else 40)
        return (1700.0 if both_alive and u == 11 and t >= 900 else x), 2000.0 + (0 if u == 11 else 40)

    d = doc(roster, pos, alive=lambda u, t: not (u in (11, 12) and t > 1000 and not (both_alive and u == 11)), fired=lambda u, t: (u == 1 and holder_fires and t == 600) or (u in (11, 12) and t == 1000),
            orders={"attacker": "B", "mode": "hold_and_attack", "point": [800.0, 2020.0], "guard": True}, sights={"Vanguard": 700.0}, first_seen={"A": 440, "B": 460}, sight="on")
    if both_alive:
        d["result"].update(winner="stall", survivors=[2, 1], end="silence", stall=True)
    return d



# ---------------------------------------------------------------- whole runs, memoised per process (a fight is about 14 s)

M_EXTRA = {"own", "enemy", "swap", "own_side", "outcome", "own_margin", "movement", "measures", "stopping", "flags", "blocks"}
V_EXTRA = {"kind", "heads", "holder", "sight", "expected_winner", "part_word", "measures", "vision", "twin", "flags", "blocks"}
_memo = {}


def m_scan(name, scratch, heads=(8, 16, 24)):
    key = ("M", name, str(scratch), tuple(heads))
    if key not in _memo:
        scratch = Path(scratch)
        _memo[key] = arms().scan_m(name, scratch, heads=list(heads), seeds=(10,), repo=ROOT, out_dir=scratch / ("m-%s-%s" % (name, "-".join(map(str, heads)))),
                                   rows_path=scratch / ("m-%s-%s.jsonl" % (name, "-".join(map(str, heads)))))
    return _memo[key]


def v_flat(name, scratch, holder="A", heads=8):
    key = ("V", name, str(scratch), holder, heads)
    if key not in _memo:
        scratch = Path(scratch)
        _memo[key] = arms().run_v_flat(name, scratch, heads=heads, holder=holder, seed=10, repo=ROOT, out_dir=scratch / ("v-%s-%s-%d" % (name, holder, heads)))
    return _memo[key]


def v_stage4(name, layout, scratch):
    key = ("V4", name, layout, str(scratch))
    if key not in _memo:
        scratch = Path(scratch)
        _memo[key] = arms().run_v_stage4(name, layout, scratch, seed=10, repo=ROOT, out_dir=scratch / ("v4-%s" % name))
    return _memo[key]
