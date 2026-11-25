# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 8 ruling 3 ("Arm V also covers the stage 4 sight-on layouts (L-0061, L-0080, L-0083, L-0039 sight twin), not only stage 3"), section 3 arm V ("Sight on is the stage 4 rule set;
# V uses only the rules the stage 4 rows already approved and adds none"), approved.toml stage 4 rows (`sight = "on"`, `control = "sight"`), run.py docstring H-088 (`--sight on`, `--control sight`), section 3 readings
"""LI3 arm V on the four stage 4 layouts, whole runs of the real lab on `now` (L-0061, L-0080, L-0083, L-0039: about 20 s each with its twin) and L-0061 on `then`.

G1 the lab runs with `--sight on` and `--control sight` for each, on the layout as authored (its catalogue file, never rewritten), with one `--seed 10` and no other order flag; the call comes from the scratch tree.
G2 the row: arm V, kind stage4, expected winner and the part word from the approved row; `sight` on in the file; the twin is the sight-off run of the same layout; a twin the rule checker marks invalid (L-0080, L-0083 at `now`: R-097-05, the lab exits 2) still comes back as a row.
G3 holder: a dict where the file says hold_and_attack, `not measured: ...` where the orders are groups or both_same_point.   G4 `then` L-0061 is a STALL at tick 460 (both sides alive): a `defect` flag, never a block, sensor and twin `not measured at then`.
G5 no source change: the catalogue layouts the lab read are byte-identical to the committed ones."""
import subprocess
import tomllib
from pathlib import Path

import pytest

import isolation_arms_fixtures as af
import isolation_fixtures as fx

NM = "not measured"


def _approved():
    with open(fx.ROOT / af.LD / "arena" / "approved.toml", "rb") as f:
        return {r["layout"]: r for r in tomllib.load(f)["fight"] if r["stage"] == 4}


@pytest.fixture(scope="module")
def stage4(iso_scratch):
    """{layout: row} on `now` and the lab calls (argv, cwd) the arm made, recorded by wrapping subprocess.run (the real run still happens)."""
    calls, real = [], subprocess.run

    def spy(argv, *args, **kw):
        calls.append((list(map(str, argv)), str(kw.get("cwd"))))
        return real(argv, *args, **kw)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(subprocess, "run", spy)
        rows = {layout: af.v_stage4("now", layout, iso_scratch) for layout in af.STAGE4}
    return rows, calls


def test_control_the_stage_4_rows_are_in_the_approved_set():
    assert set(_approved()) == set(af.STAGE4)
    assert all(r["sight"] == "on" and r["control"] == "sight" for r in _approved().values())


def test_g1_each_layout_runs_with_sight_on_and_its_sight_twin_and_one_order_each(stage4, iso_scratch):
    rows, calls = stage4
    labs = af.fight_lab_calls([c[0] for c in calls])
    cwds = [c[1] for c in calls if "scripts.skilllab.arena.run" in " ".join(c[0])]
    assert len(labs) >= len(af.STAGE4)
    for layout in af.STAGE4:
        mine = [(argv, cwd) for argv, cwd in zip(labs, cwds) if Path(af.flag_value(argv, "--layout")).stem == layout]
        assert len(mine) == 1, "one lab call per layout: the twin comes from `--control sight`, not a second run"
        (argv, cwd), = mine
        assert af.flag_value(argv, "--sight") == "on" and af.flag_value(argv, "--control") == "sight" and af.flag_value(argv, "--control-dir")
        assert af.flag_value(argv, "--seed") == "10" and argv.count("--seed") == 1 and argv.count("--layout") == 1
        assert Path(cwd).resolve().is_relative_to(Path(iso_scratch).resolve()), "the lab ran from a scratch tree, never the repository"
        assert Path(af.flag_value(argv, "--layout")).resolve().is_relative_to(Path(iso_scratch).resolve())


def test_g2_the_rows(stage4, iso_scratch):
    im, a, ir = af.measures(), af.arms(), fx.runner()
    rows, _ = stage4
    approved = _approved()
    keys = set()
    for layout, r in rows.items():
        assert set(r) == af.ROW_KEYS | af.V_EXTRA and r["error"] is None, (layout, r["error"])
        assert r["arm"] == "V" and r["kind"] == "stage4" and r["layout"] == layout and r["seed"] == 10 and r["version"] == "now" and r["heads"] is None and r["holder"] is None
        assert r["expected_winner"] == approved[layout]["expected_winner"] and r["sight"] == "on"
        doc = im.load_fight(r["fight_path"])
        assert doc["sight"] == "on" and doc["layout_id"] == layout and doc["sights"] and set(doc["result"]["first_seen"]) == {"A", "B"}
        assert r["part_word"] == a.part_word_v(doc["result"]["winner"], r["expected_winner"])
        assert r["blocks"] is False and r["flags"] == a.flags_of(doc)
        twin = r["twin"]
        assert twin["sight"] == "off" and set(twin["result"]) == fx.RESULT_KEYS and isinstance(twin["invalid"], bool) and Path(twin["fight_path"]).is_file()
        tdoc = im.load_fight(twin["fight_path"])
        assert tdoc["sight"] == "off" and tdoc["layout_id"] == layout and tdoc.get("invalid", False) is twin["invalid"]
        keys.add(ir.row_key(r))
    assert len(keys) == 4 and af.roundtrip(rows) == rows


def test_g3_a_holder_is_reported_only_where_the_orders_name_one(stage4):
    im = af.measures()
    rows, _ = stage4
    for layout, r in rows.items():
        mode = im.load_fight(r["fight_path"])["orders"]["mode"]
        holder = r["vision"]["holder"]
        if mode == "hold_and_attack":
            assert isinstance(holder, dict) and holder["side"] in ("A", "B")
        else:
            assert isinstance(holder, str) and holder.startswith(NM), (layout, mode)
    assert im.load_fight(rows["L-0061"]["fight_path"])["orders"]["mode"] == "hold_and_attack"
    assert im.load_fight(rows["L-0080"]["fight_path"])["orders"]["mode"] == "groups"
    assert im.load_fight(rows["L-0039"]["fight_path"])["orders"]["mode"] == "both_same_point"


def test_g4_then_on_a_stage_4_layout_is_a_stall_flagged_not_blocking(iso_scratch):
    r = af.v_stage4("then", "L-0061", iso_scratch)
    assert r["error"] is None and r["version"] == "then" and r["lab_sha"] == fx.THEN_SHA
    assert r["result"]["winner"] == "stall" and r["result"]["end"] == "silence" and r["result"]["survivors"] == [24, 24], "both sides alive at the end: a lab defect, found not smoothed over"
    assert "defect" in r["flags"] and r["blocks"] is False
    assert r["vision"]["sensor"] == r["vision"]["first_seen"] == "not measured at then" and r["twin"] == "not measured at then"
    assert r["part_word"] in ("pass", "fail", "no stated direction")


def test_g5_the_layouts_the_lab_read_are_the_committed_ones(iso_scratch, stage4):
    ir = fx.runner()
    tree = Path(iso_scratch) / ("tree-" + ir.resolve_version("now", repo=fx.ROOT).sha)
    for layout in af.STAGE4:
        committed = fx.git(fx.ROOT, "show", "origin/main:%s/catalogue/%s.toml" % (af.LD, layout))
        assert (tree / af.LD / "catalogue" / (layout + ".toml")).read_text().strip() == committed.strip()
