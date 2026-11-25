# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 3 (arms M and V "reuse, do not rebuild": run.py, breakeven.py, scan.py) and section 7 (LI3)
"""LI3 positive controls, GREEN on the branch as it is: the wrapped lab commands work, so a red in the other test_isolation_arms_*.py files means the arms are missing, not that the harness is broken.

K1 a flat featureless Vanguard layout (test-local, 8 a side) written into a scratch tree runs through LI1's `run_one` on `now`: sight off, both_same_point, one role, a wipe; LI2's `measure_fight` reads it (orders ended short is a dict).
K2 the same lab with `--sight on --control sight` on a hold:A flat layout (the V arm's lab call): `sights`, `result.first_seen`, `orders.guard`, and the sight-off twin file.
K3 `scan.scan` / `breakeven.find_break_even` / `scan.read_cells`, the functions the M scan reuses, find a flip on a scripted fight function (no engine).
K4 the layout the arms write must pass the lab's own `check_layout` (R1 to R7): the control layout does."""
from types import SimpleNamespace

import isolation_arms_fixtures as af
import isolation_fixtures as fx


def test_k1_a_flat_layout_runs_through_the_runner_and_is_measured(iso_scratch):
    ir, im = fx.runner(), af.measures()
    tree = af.tree_of("now", iso_scratch)
    af.put_layout(tree, af.flat_layout("L-9101", 8, 8))
    row = ir.run_one("now", "L-9101", 10, iso_scratch, arm="M", repo=fx.ROOT)
    assert row["error"] is None and row["arm"] == "M" and row["layout"] == "L-9101"
    d = im.load_fight(row["fight_path"])
    assert d["sight"] == "off" and d["orders"]["mode"] == "both_same_point" and d["ranges"] == {"Vanguard": 300.0} and "sights" not in d
    first = next(iter(d["frames"]))
    assert {u["role"] for u in first["units"]} == {"Vanguard"} and first["alive"] == [8, 8]
    assert row["result"]["end"] in ("wipe", "apart") and row["result"]["winner"] in ("A", "B")
    short = im.orders_ended_short(d)
    assert isinstance(short, dict) and isinstance(short["alive_at_end"], list)


def test_k2_the_lab_with_sight_on_writes_sights_first_seen_guard_and_the_twin(iso_scratch):
    im = af.measures()
    tree = af.tree_of("now", iso_scratch)
    path = af.put_layout(tree, af.flat_layout("L-9102", 8, 8, orders="hold:A"))
    out = iso_scratch / "k2"
    done, fight = af.lab(tree, path, 10, out, "--sight", "on", "--control-dir", str(out / "ctl"), "--control", "sight")
    assert done.returncode == 0, done.stderr[-500:]
    d = im.load_fight(fight)
    assert d["sight"] == "on" and d["sights"] == {"Vanguard": 700.0} and set(d["result"]["first_seen"]) == {"A", "B"}
    assert d["orders"]["mode"] == "hold_and_attack" and d["orders"]["attacker"] == "B" and d["orders"]["guard"] is True
    twin = im.load_fight(out / "ctl" / "L-9102-control-s10.fight.json")
    assert twin["sight"] == "off" and "sights" not in twin


def test_k3_the_scan_functions_find_a_flip_on_a_scripted_fight():
    from scripts.skilllab import breakeven, scan
    seen = []

    def fight_fn(setup, seed, swap):
        own, enemy = setup
        seen.append((enemy, seed, swap))
        return SimpleNamespace(outcome="side0" if own > enemy else "side1", margin=float(own - enemy))

    build = lambda enemy, swap: (16, enemy)
    result = scan.scan(build, 16, 8, 24, replicates=1, fight_fn=fight_fn, full_scan=True)
    assert [c.enemy_heads for c in result.cells] == list(range(8, 25))
    assert (result.beats, result.loses_to, result.ceiling_hit, result.multi_flip) == (15, 16, False, False)
    assert all(c.fights and len(c.fights) == 2 for c in result.cells), "a cell is both spawn orders per replicate"
    be = breakeven.find_break_even(build, 16, 8, 24, replicates=1, near_replicates=1, fight_fn=fight_fn)
    assert (be.beats, be.loses_to) == (15, 16) and [(f.before, f.after) for f in be.flips] == [(15, 16)]
    cells = [SimpleNamespace(enemy_heads=h, won=h < 16) for h in (8, 16, 24)]
    assert scan.read_cells(cells) == (8, 16, False, False)


def test_k4_the_control_layout_is_valid_for_the_labs_own_rules():
    from scripts.skilllab.arena.run import is_mirror
    from scripts.skilllab.catalogue.produce import check_layout, presets, rules
    for n in (8, 16, 48):
        assert check_layout(af.flat_layout("L-9103", n, 16), presets(), rules()) == []
    assert is_mirror(af.flat_layout("L-9104", 16, 16)) and not is_mirror(af.flat_layout("L-9104", 8, 16))
