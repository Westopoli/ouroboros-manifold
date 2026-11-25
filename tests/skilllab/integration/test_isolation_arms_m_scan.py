# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 3 arm M ("Headcount scan: 8 to 48 against 16, and 16 against 16 mirror (C0: the larger force wins, break-even near equal). Reported as the cell map with the flips marked, not as a verdict on where equal sits"),
# section 1 preconditions 2, 3, 6, 7 and 8, section 4 (measures per run, `defect`), section 5 (rows keyed by version); layer_dynamics README section 4 (C0; "A cell is won by elimination"; "Break-even, in whole units")
"""LI3 arm M, whole runs of the real lab: `scan_m` on flat Vanguard walkers, three headcounts (8, 16, 24) against 16, one seed (10), both spawn orders, on `now` and on `then`: 6 fights a version (about 90 s).
The full scan is `scan_m(..., heads=range(8, 49))`, the default; a test never runs it. The scan's contract and the curve structure are what is pinned, not the break-even's place.

S1 the summary has the contract keys; points come back in increasing enemy headcount, one per headcount asked, each both spawn orders over the seeds.   S2 each point's fields are the aggregates of its fight rows (no second reading of any file).
S3 beats, loses_to, ceiling_hit, multi_flip are the lab's own `scan.read_cells` over the points, and the flips are the places `won` changes.   S4 C0 direction: the larger force wins in both spawn orders (8 v 16 won, 24 v 16 lost).
S5 the 16 v 16 mirror control: one layout in both orders, one fight twice, the force never decides it; `summary["mirror"]` is that point and the cell is not won.   S6 every fight row is the runner's row plus the arm's keys; own-side margin; keyed once.
S7 the row's measures are LI2's `measure_fight` of the fight file, not a copy of it.   S8 the rows file is the summary's rows, flushed per run.   S9 no key is a pass mark; flags and `blocks` agree with the stopping check; `blocks` is the one finding that blocks.
S10 the layouts are walkers on flat ground written into the scratch tree and the lab's fight files say so."""
import json
import re
import statistics
from pathlib import Path
from types import SimpleNamespace

import pytest

import isolation_arms_fixtures as af
import isolation_fixtures as fx

HEADS = (8, 16, 24)
SUMMARY = {"arm", "version", "lab_sha", "own", "heads", "seeds", "movement", "spread_ticks", "points", "beats", "loses_to", "ceiling_hit", "multi_flip", "flips", "part_word", "blocks", "mirror", "rows"}
POINT = {"own_heads", "enemy_heads", "won", "defect", "outcomes", "mean_margin", "fights", "layouts", "orders_ended_short", "idle_behind", "idle_front", "max_overlap_pairs", "first_contact_ticks"}


@pytest.fixture(params=["now", "then"], scope="module")
def scan(request, iso_scratch):
    return af.m_scan(request.param, iso_scratch)


def _point(scan, heads):
    (p,) = [p for p in scan["points"] if p["enemy_heads"] == heads]
    return p


def _rows(scan, heads):
    return [r for r in scan["rows"] if r["enemy"] == heads]


def test_s1_the_summary_and_its_points_have_the_contract_shape(scan):
    a = af.arms()
    assert set(scan) == SUMMARY
    assert scan["arm"] == "M" and scan["own"] == 16 == a.OWN_HEADS and scan["heads"] == list(HEADS) and scan["seeds"] == [10] and scan["movement"] == "walk"
    ir = fx.runner()
    assert scan["lab_sha"] == ir.resolve_version(scan["version"], repo=fx.ROOT).sha and len(scan["lab_sha"]) == 40
    assert [p["enemy_heads"] for p in scan["points"]] == list(HEADS)
    for p in scan["points"]:
        assert set(p) == POINT and p["own_heads"] == 16
        assert p["fights"] == 2 == len(p["outcomes"]) == len(p["layouts"]) == len(p["first_contact_ticks"]), "both spawn orders over one seed"
        assert all(o in ("side0", "side1", "draw", "cap") for o in p["outcomes"]) and isinstance(p["won"], bool) and isinstance(p["defect"], bool)
        assert p["won"] == all(o == "side0" for o in p["outcomes"]) and p["defect"] == any(o in ("draw", "cap") for o in p["outcomes"])
    assert af.roundtrip(scan) == scan, "everything in a summary is JSON: it goes to a rows file and back"


def test_s2_each_point_is_the_aggregate_of_its_rows(scan):
    for p in scan["points"]:
        rows = _rows(scan, p["enemy_heads"])
        assert [r["swap"] for r in rows] == [False, True] and [r["layout"] for r in rows] == p["layouts"]
        assert [r["outcome"] for r in rows] == p["outcomes"]
        assert p["mean_margin"] == pytest.approx(statistics.mean(r["own_margin"] for r in rows))
        assert p["orders_ended_short"] == sum(r["stopping"]["orders_ended_short"] for r in rows)
        assert p["idle_behind"] == sum(r["measures"]["idle_units"]["behind"] for r in rows)
        assert p["idle_front"] == sum(r["measures"]["idle_units"]["front"] for r in rows)
        assert p["max_overlap_pairs"] == max(r["measures"]["overlap"]["max_per_frame"] for r in rows)
        assert p["first_contact_ticks"] == [r["measures"]["first_contact_tick"] for r in rows]


def test_s3_the_break_even_is_the_labs_own_reading_of_the_points(scan):
    from scripts.skilllab import scan as lab_scan
    cells = [SimpleNamespace(enemy_heads=p["enemy_heads"], won=p["won"]) for p in scan["points"]]
    assert (scan["beats"], scan["loses_to"], scan["ceiling_hit"], scan["multi_flip"]) == lab_scan.read_cells(cells)
    flips = [{"before": x.enemy_heads, "after": y.enemy_heads, "direction": "win_to_loss" if x.won else "loss_to_win"} for x, y in zip(cells, cells[1:]) if x.won != y.won]
    assert scan["flips"] == flips and len(flips) >= 1
    assert scan["multi_flip"] is (len(flips) > 1)
    assert not scan["ceiling_hit"], "the scan stopped winning: 16 does not beat 24"


def test_s4_c0_the_larger_force_wins_in_both_spawn_orders(scan):
    small, large = _point(scan, 8), _point(scan, 24)
    assert small["outcomes"] == ["side0", "side0"] and small["won"] and not small["defect"] and small["mean_margin"] > 0
    assert large["outcomes"] == ["side1", "side1"] and not large["won"] and not large["defect"] and large["mean_margin"] < 0
    assert scan["part_word"] == "pass", "C0 read at the cells where the numbers differ; the mirror cell is not read"


def test_s5_the_mirror_control_is_one_fight_twice_and_the_force_never_decides_it(scan):
    im = af.measures()
    mirror = scan["mirror"]
    assert mirror == _point(scan, 16) and mirror["own_heads"] == mirror["enemy_heads"] == 16
    assert mirror["won"] is False and mirror["defect"] is False, "a draw or a cap at equal numbers is a lab bug, traced, never accepted (memory 2026-11-18)"
    assert sorted(mirror["outcomes"]) == ["side0", "side1"], "own wins exactly the order in which the engine's side advantage is its"
    one, two = _rows(scan, 16)
    d1, d2 = im.load_fight(one["fight_path"]), im.load_fight(two["fight_path"])
    f1, f2 = next(iter(d1["frames"])), next(iter(d2["frames"]))
    assert f1["units"] == f2["units"], "the same layout in both orders: the same units at the same places"
    assert (d1["result"]["winner"], d1["result"]["survivors"], d1["result"]["ticks"]) == (d2["result"]["winner"], d2["result"]["survivors"], d2["result"]["ticks"])
    assert one["layout"] != two["layout"] and one["fight_path"] != two["fight_path"]
    assert one["own_side"] == "A" and two["own_side"] == "B"


def test_s6_every_fight_row_is_the_runners_row_plus_the_arms_keys(scan):
    ir = fx.runner()
    assert len(scan["rows"]) == len(HEADS) * 2
    keys = set()
    for r in scan["rows"]:
        assert set(r) == af.ROW_KEYS | af.M_EXTRA, set(r) ^ (af.ROW_KEYS | af.M_EXTRA)
        assert r["error"] is None and r["arm"] == "M" and r["version"] == scan["version"] and r["lab_sha"] == scan["lab_sha"] and r["seed"] == 10
        assert re.fullmatch(r"L-\d{4}", r["layout"]) and Path(r["fight_path"]).is_file() and r["fight_sha256"] == fx.sha256(r["fight_path"])
        assert (r["own"], r["swap"], r["movement"]) == (16, r["swap"], "walk") and r["own_side"] == ("B" if r["swap"] else "A")
        own, enemy = (r["result"]["survivors"][1], r["result"]["survivors"][0]) if r["swap"] else tuple(r["result"]["survivors"])
        assert r["own_margin"] == own - enemy
        if r["result"]["winner"] in ("A", "B"):
            assert r["outcome"] == ("side0" if r["result"]["winner"] == r["own_side"] else "side1")
        else:
            assert r["outcome"] in ("draw", "cap"), "both sides alive at the end is a defect, never a result (Q-LAB-03)"
        keys.add(ir.row_key(r))
    assert len(keys) == len(scan["rows"]) and len({r["fight_path"] for r in scan["rows"]}) == len(scan["rows"]), "no fight file overwritten by another cell"
    assert af.roundtrip(scan["rows"]) == scan["rows"]


def test_s7_the_measures_are_li2s_over_the_fight_file(scan):
    im, a = af.measures(), af.arms()
    for r in scan["rows"][:2] + scan["rows"][-1:]:
        doc = im.load_fight(r["fight_path"])
        assert r["measures"] == af.roundtrip(im.measure_fight(doc, spread_ticks=list(a.DRAFT_SPREAD_TICKS)))
        assert r["stopping"] == af.roundtrip(a.stopping_check(doc)) and r["flags"] == a.flags_of(doc) and r["blocks"] is a.blocks_of(doc, "M")
        assert set(r["measures"]["spread"]) == {str(t) for t in a.DRAFT_SPREAD_TICKS}, "spread at the ticks asked; JSON keys are strings"


def test_s8_the_rows_file_is_the_summarys_rows(scan, iso_scratch):
    ir = fx.runner()
    path = Path(iso_scratch) / ("m-%s-%s.jsonl" % (scan["version"], "-".join(map(str, HEADS))))
    lines = path.read_text().splitlines()
    assert len(lines) == len(scan["rows"]) and path.read_text().endswith("\n")
    assert ir.read_rows(path) == scan["rows"]
    assert all(line == json.dumps(json.loads(line), sort_keys=True) for line in lines)


def test_s9_flags_are_signals_and_only_the_stopping_check_blocks(scan):
    a = af.arms()
    assert not (set(scan) | set(scan["points"][0]) | set(scan["rows"][0])) & af.PASS_MARK_KEYS
    for r in scan["rows"]:
        ended = r["stopping"]["orders_ended_short"]
        assert isinstance(ended, int) and r["blocks"] is (ended > 0), "blocks is the stopping check and nothing else"
        assert ("orders_ended_short" in r["flags"]) is (ended > 0)
        assert ("defect" in r["flags"]) is (r["outcome"] in ("draw", "cap"))
        assert r["flags"] == sorted(set(r["flags"]))
    assert scan["blocks"] is any(r["blocks"] for r in scan["rows"])
    assert scan["part_word"] in ("pass", "fail", "no stated direction") and a.part_word_m(scan["points"]) == scan["part_word"]


def test_s10_the_layouts_are_flat_walkers_written_into_the_scratch_tree_only(scan, iso_scratch):
    import tomllib
    im, ir = af.measures(), fx.runner()
    tree = (Path(iso_scratch) / ("tree-" + scan["lab_sha"])).resolve()
    for r in scan["rows"]:
        doc = im.load_fight(r["fight_path"])
        assert doc["layout_id"] == r["layout"] and doc["sight"] == "off" and doc["orders"]["mode"] == "both_same_point" and doc["movement_kind"] == 1
        assert doc["landscape"] == "small_flat" and set(doc["ranges"]) == {"Vanguard"} and "sights" not in doc and "built_features" not in doc
        first = next(iter(doc["frames"]))
        assert {u["role"] for u in first["units"]} == {"Vanguard"} and sorted(first["alive"]) == sorted([16, r["enemy"]])
        written = tree / af.LD / "catalogue" / (r["layout"] + ".toml")
        assert written.is_file()
        lay = tomllib.loads(written.read_text())
        assert lay["orders"] == "both_same_point" and lay["situation"] == "open_field" and not lay.get("features") and lay["movement"] == "walk"
        assert not (fx.ROOT / af.LD / "catalogue" / (r["layout"] + ".toml")).exists(), "the repository's catalogue is not written"
