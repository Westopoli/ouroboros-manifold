# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 3 (arms F and W: "each fight runs beside its feature-free control twin"), section 4 ("a fight the rule checker marks invalid is listed"), section 2 (V-then and V-now each use their own lab)
"""LI4-FW controls: the lab commands `isolation_fw.py` must wrap, exercised as they are today. Green before the module exists and they must stay green; if one goes red, the premise moved
(not the module). Each names the module behaviour that stands on it. All are real lab runs from a tree LI1's `build_version` made (about 15 s a fight).

K0 `now` is still the main the facts were dumped from (893a5af7f). Red here means: re-dump the facts of isolation_fw_real.py, nothing else is wrong.
K1 the lab's `--control-dir` writes `<id>-control-s<seed>.fight.json` and the twin's layout file, at `now`; the twin's `layout_path` is tree-relative when the control dir is inside the tree
   (so two scratch roots can write equal files), and the twin is the layout without its features.   (the control twin beside the layout)
K2 at `now` an INVALID fight (L-0055, R-097-05) exits 2, prints the INVALID line, still writes the fight file, and the file says `invalid: true` with its `violations`.
   (an invalid fight is a row with its rule listed, never an error row; today LI1 `run_one` makes it an error row of stage layout)
K3 at `then` the lab runs the same twin (`--control-dir`), has no rule checker (`scripts/skilllab/invariants.py` is not in the tree) and writes neither `invalid` nor `violations`; at `now` the checker is in the tree and a valid fight
   still writes neither key, so the file cannot say which version had a checker: the tree does.   (`invalid` is `not measured at then`, `[]` for a valid fight at now)"""
import json
import subprocess

import pytest

import isolation_fixtures as fx
import isolation_fw_real as real

L = "docs/northstar/research/layer_dynamics/catalogue/%s.toml"


@pytest.fixture(scope="module")
def trees(tmp_path_factory):
    ir = fx.runner()
    scratch = tmp_path_factory.mktemp("fw-controls")
    return {n: ir.build_version(ir.resolve_version(n, repo=fx.ROOT), scratch, repo=fx.ROOT) for n in ("then", "now")}


def _lab(tree, layout, out, control_dir):
    done = real.lab_job([fx.PY, "-m", "scripts.skilllab.arena.run", "--layout", str(tree / (L % layout)), "--seed", "10", "--out", str(out), "--control-dir", str(control_dir)], tree)
    return done


def test_k0_now_is_the_main_the_facts_were_dumped_from():
    now = fx.runner().resolve_version("now", repo=fx.ROOT)
    assert now.sha == real.NOW_SHA, "origin/main moved: re-dump FACTS in isolation_fw_real.py before judging any red"


def test_k1_control_dir_writes_the_twin_beside_the_layout_at_now(trees):
    tree = trees["now"]
    out, ctl = tree / "fw-out", tree / "fw-ctl"
    done = _lab(tree, "L-0039", out, ctl)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "FIGHT L-0039 seed 10 winner A ticks 3081" in done.stdout
    doc = json.loads((out / "L-0039-s10.fight.json").read_text())
    twin = json.loads((ctl / "L-0039-control-s10.fight.json").read_text())
    assert (twin["result"]["winner"], twin["result"]["survivors"], twin["result"]["ticks"]) == ("B", [0, 5], 2352)
    assert (ctl / "L-0039-control.toml").is_file() and (ctl / "L-0039-control.json").is_file()
    assert twin["layout_path"] == "fw-ctl/L-0039-control.toml", "inside the tree the path is tree-relative: no scratch path reaches the file"
    assert [(u["id"], u["role"], u["x"], u["y"]) for u in doc["frames"][0]["units"]] == [(u["id"], u["role"], u["x"], u["y"]) for u in twin["frames"][0]["units"]], "same units, same places"
    assert "features" in (ctl / "L-0039-control.json").read_text() and json.loads((ctl / "L-0039-control.json").read_text())["features"] == []


def test_k2_an_invalid_fight_exits_2_and_still_writes_its_file_at_now(trees):
    tree = trees["now"]
    out, ctl = tree / "fw-out2", tree / "fw-ctl2"
    done = _lab(tree, "L-0055", out, ctl)
    assert done.returncode == 2, done.stdout + done.stderr
    assert "INVALID L-0055 R-097-05" in done.stdout and "FIGHT L-0055 seed 10 winner A ticks 1963" in done.stdout
    doc = json.loads((out / "L-0055-s10.fight.json").read_text())
    assert doc["invalid"] is True and {v["rule"] for v in doc["violations"]} == {"R-097-05"}
    assert doc["result"]["survivors"] == [19, 0] and doc["result"]["ticks"] == 1963
    twin = json.loads((ctl / "L-0055-control-s10.fight.json").read_text())
    assert (twin["result"]["winner"], twin["result"]["survivors"], twin["result"]["ticks"]) == ("A", [19, 0], 2188) and not twin.get("invalid")


def test_k3_the_lab_at_then_runs_the_twin_and_writes_no_checker_fields(trees):
    tree = trees["then"]
    out, ctl = tree / "fw-out3", tree / "fw-ctl3"
    done = _lab(tree, "L-0055", out, ctl)
    assert done.returncode == 0, done.stdout + done.stderr
    doc = json.loads((out / "L-0055-s10.fight.json").read_text())
    twin = json.loads((ctl / "L-0055-control-s10.fight.json").read_text())
    for d in (doc, twin):
        assert "invalid" not in d and "violations" not in d
    assert not (tree / "scripts/skilllab/invariants.py").exists() and (trees["now"] / "scripts/skilllab/invariants.py").is_file()
    assert (doc["result"]["winner"], doc["result"]["survivors"], doc["result"]["ticks"]) == ("A", [21, 0], 3394)
    assert (twin["result"]["winner"], twin["result"]["survivors"], twin["result"]["ticks"]) == ("A", [23, 0], 2196)
