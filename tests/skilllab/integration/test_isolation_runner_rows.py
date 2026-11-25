# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 7, piece LI1; section 2 (versions, "not measured at V-then"), section 4 (measures per run)
"""LI1 rows: whole runs of the real lab, `then` (4fa618ce7) and `now` (origin/main) on one layout and seed, through `isolation_runner.run_matrix`.

R1 version names resolve: then is the full 4fa618ce sha, now is `origin/main` of the repo, fix is a given ref made a full sha.   R2 a rows file is JSONL, one row per run, in the order asked, every row with exactly the ROW_KEYS.
R3 the key (version, lab_sha, arm, layout, seed) is filled and unique.   R4 `then` and `now` ran the same layout and seed with different lab shas, each its own lab (the fight files differ in what that lab writes).
R5 result and margin copy the lab's own fight file; fight_path exists and fight_sha256 is its sha256.   R6 units_firing: a dict from the per-frame `fired` flags where the lab offers it, else the string
`not measured at <version>`, never 0.   R7 a layout may be a situation id (converted by that version's own converter).   R8 the CLI writes the same row."""
import json
import subprocess
from pathlib import Path

import pytest

import isolation_fixtures as fx


def test_r1_versions_resolve_to_full_shas():
    ir = fx.runner()
    assert ir.THEN_SHA == fx.THEN_SHA
    then = ir.resolve_version("then", repo=fx.ROOT)
    assert (then.name, then.sha) == ("then", fx.THEN_SHA)
    now = ir.resolve_version("now", repo=fx.ROOT)
    assert now.name == "now" and now.sha == fx.git(fx.ROOT, "rev-parse", "origin/main")
    fix = ir.resolve_version("fix", ref=fx.THEN_SHA[:9], repo=fx.ROOT)
    assert fix.name == "fix" and fix.sha == fx.THEN_SHA
    with pytest.raises(ValueError):
        ir.resolve_version("fix", repo=fx.ROOT)       # fix needs a branch or sha
    with pytest.raises(ValueError):
        ir.resolve_version("later", repo=fx.ROOT)     # only then, now, fix


def test_r2_rows_file_is_jsonl_one_row_per_run_in_order(iso_scratch):
    m = fx.matrix(iso_scratch)
    lines = m.file1.read_text().splitlines()
    assert len(lines) == 2 and m.file1.read_text().endswith("\n")
    parsed = [json.loads(line) for line in lines]
    assert [r["version"] for r in parsed] == ["then", "now"]          # versions in the order asked, then layouts, then seeds
    assert [set(r) for r in parsed] == [fx.ROW_KEYS] * 2
    assert fx.runner().read_rows(m.file1) == parsed == m.first
    assert all(line == json.dumps(json.loads(line), sort_keys=True) for line in lines), "one canonical line per row: sorted keys, compact JSON per json.dumps defaults"


def test_r3_key_is_filled_and_unique(iso_scratch):
    ir = fx.runner()
    rows = fx.matrix(iso_scratch).first
    keys = [ir.row_key(r) for r in rows]
    assert len(set(keys)) == 2
    for r in rows:
        assert r["error"] is None
        assert r["arm"] == "W" and r["layout"] == fx.LAYOUT and r["seed"] == fx.SEED
        assert isinstance(r["lab_sha"], str) and len(r["lab_sha"]) == 40
    assert ir.row_key(rows[0]) == ("then", fx.THEN_SHA, "W", fx.LAYOUT, fx.SEED)


def test_r4_then_and_now_are_different_labs_on_one_layout_and_seed(iso_scratch):
    rows = fx.matrix(iso_scratch).first
    then, now = fx.by_version(rows, "then"), fx.by_version(rows, "now")
    assert then["lab_sha"] == fx.THEN_SHA
    assert now["lab_sha"] == fx.git(fx.ROOT, "rev-parse", "origin/main")
    assert then["lab_sha"] != now["lab_sha"]
    assert (then["layout"], then["seed"]) == (now["layout"], now["seed"])
    assert then["fight_sha256"] != now["fight_sha256"]
    docs = {n: json.loads(Path(r["fight_path"]).read_text()) for n, r in (("then", then), ("now", now))}
    assert all(d["layout_id"] == fx.LAYOUT and d["seed"] == fx.SEED for d in docs.values())
    assert not any("fired" in u for u in docs["then"]["frames"][1]["units"]), "the fight file of `then` was written by the then lab"
    assert any("fired" in u for u in docs["now"]["frames"][1]["units"]), "the fight file of `now` was written by the now lab"


def test_r5_result_margin_and_file_copy_the_lab(iso_scratch):
    for r in fx.matrix(iso_scratch).first:
        doc = json.loads(Path(r["fight_path"]).read_text())
        assert Path(r["fight_path"]).is_file() and Path(r["fight_path"]).is_absolute()
        assert r["fight_sha256"] == fx.sha256(r["fight_path"])
        res = r["result"]
        assert set(res) == fx.RESULT_KEYS
        assert res == {"winner": doc["result"]["winner"], "survivors": doc["result"]["survivors"], "last_tick": doc["result"]["ticks"], "end": doc["result"]["end"]}
        assert res["end"] in fx.ENDS and res["last_tick"] > 0 and len(res["survivors"]) == 2
        assert r["margin"] == res["survivors"][0] - res["survivors"][1]       # side A survivors minus side B survivors; positive means A ended ahead


def test_r6_units_firing_is_a_summary_or_the_not_measured_string(iso_scratch):
    ir = fx.runner()
    rows = fx.matrix(iso_scratch).first
    then, now = fx.by_version(rows, "then"), fx.by_version(rows, "now")
    assert then["units_firing"] == "not measured at then"         # a string, never 0, never null, never a blank
    doc = json.loads(Path(now["fight_path"]).read_text())
    expect = [[f["tick"]] + [sum(1 for u in f["units"] if u["side"] == s and u["fired"]) for s in "AB"] for f in doc["frames"]]
    got = now["units_firing"]
    assert isinstance(got, dict) and set(got) == {"by_frame", "peak"}
    assert got["by_frame"] == expect                              # [tick, side A units that fired since the last frame, side B units that did]
    assert got["peak"] == [max(e[1] for e in expect), max(e[2] for e in expect)] and max(got["peak"]) > 0
    assert ir.units_firing(doc, "now") == got
    assert ir.units_firing(json.loads(Path(then["fight_path"]).read_text()), "fix") == "not measured at fix"   # the name in the string is the version asked about


def test_r7_a_situation_id_is_a_layout(iso_scratch):
    ir = fx.runner()
    row = ir.run_one("now", fx.SITUATION, fx.SEED, iso_scratch, repo=fx.ROOT, out_dir=Path(iso_scratch) / "fights-sit")
    assert row["error"] is None and row["layout"] == fx.SITUATION and set(row) == fx.ROW_KEYS
    doc = json.loads(Path(row["fight_path"]).read_text())
    assert doc["layout_id"] == "L-0106" and row["result"]["last_tick"] == doc["result"]["ticks"]
    assert row["fight_sha256"] == fx.sha256(row["fight_path"])


def test_r8_cli_writes_the_same_row(iso_scratch, tmp_path):
    ir = fx.runner()
    rows_file = tmp_path / "cli.jsonl"
    done = subprocess.run([fx.PY, "-m", "scripts.skilllab.arena.isolation_runner", "--version", "then", "--layout", fx.LAYOUT, "--seed", str(fx.SEED), "--arm", "W",
                           "--scratch", str(iso_scratch), "--rows", str(rows_file), "--repo", str(fx.ROOT), "--out", str(tmp_path / "fights")],
                          cwd=str(fx.ROOT), capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr
    (cli,) = ir.read_rows(rows_file)
    api = fx.by_version(fx.matrix(iso_scratch).first, "then")
    assert fx.sans_path(cli) == fx.sans_path(api)
