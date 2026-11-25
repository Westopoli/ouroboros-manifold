# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 5 (Comparison output), section 6 (Delivery), section 7 ("Tests are whole-run on real lab fights"), piece LI5 part 1
"""The generator on real rows of a short real run: arm W of L-0039 (cover) at `then` (4fa618ce7, its own lab) and `now` (origin/main, its own lab), seed 10, layout and twin: 4 real fights
(isolation_fw.run_arms; premises isolation_fw_real.FACTS: then layout cap 8:8 t12000, then twin A 3:0 t2606, now layout A 2:0 t3081, now twin B 0:5 t2352; the then fights carry no `fired` and no
rule checker). The page module is imported before any fight, so a missing module fails in seconds. About 2 to 4 minutes once built. Interface: docs/reports/2026-11-24-li5-interface.md.
No arm M or V fight is run here: their module (LI3, branch s/lab-isolation-li3) is not in this branch's tree; their page code is covered on the shapes of its interface (test_isolation_page_arms.py)."""
import json
import re
from pathlib import Path

import pytest

import isolation_page_fixtures as pf

LAYOUT = "L-0039"


@pytest.fixture(scope="module")
def real(tmp_path_factory):
    mod = pf.page()                                                    # red fast when the module is missing
    scratch = tmp_path_factory.mktemp("page-real")
    rows = pf.fw().run_arms(["then", "now"], scratch, scratch / "rows" / "rows.jsonl", arms=("W",), layouts=(LAYOUT,), seeds=(10,), repo=pf.ROOT, out_dir=scratch / "fights")
    assert [r["error"] for r in rows] == [None] * 4, rows
    inputs = mod.read_inputs(rows=[scratch / "rows" / "rows.jsonl"], repo=pf.ROOT)
    res = mod.build_page(scratch / "out", banner=pf.BANNER, banner_kind="ask", inputs=inputs, clips=None, drafts=None, ledger=pf.LEDGER)
    res2 = mod.build_page(scratch / "out2", banner=pf.BANNER, banner_kind="ask", inputs=inputs, clips=None, drafts=None, ledger=pf.LEDGER)
    return {"rows": rows, "out": scratch / "out", "out2": scratch / "out2", "root": pf.page_root(scratch / "out"), "res": res, "res2": res2}


def test_the_comparison_row_of_real_fights_traces_to_the_fights(real):
    c = pf.table_cells(real["root"], "comparison")[(LAYOUT, None, None)]
    assert "cap 8:8 t12000" in c["then"] and "A 2:0 t3081" in c["now"]
    assert c["change"].startswith("changed") and "1" in c["change"] and "DRAFT-same-or-changed-rule" in c["change"]
    assert pf.WORDS[LAYOUT] in c["ruling"] and "2026-11-01" in c["ruling"] and "0.25" in c["ruling"]
    assert c["first_arm"] == "none, the whole differs only at W"           # only arm W was run
    twin = pf.table_cells(real["root"], "comparison")[(LAYOUT, "control", None)]
    assert "A 3:0 t2606" in twin["then"] and "B 0:5 t2352" in twin["now"]


def test_real_then_cells_say_not_measured_at_then_and_now_has_the_curve(real):
    w = pf.table_cells(real["root"], "arm-W")
    then, now = w[(LAYOUT, "layout", "then")], w[(LAYOUT, "layout", "now")]
    assert "not measured at then" in then["units_firing"] and "not measured at then" in then["invalid"] and "not measured at then" in then["agreement"]
    assert "signal: defect" in then["flags"] and then["winner"] == "cap" and then["end"] == "cap"
    frames = next(r for r in real["rows"] if (r["version"], r["variant"]) == ("now", "layout"))["measures"]["units_firing"]["by_frame"]
    svg = [tr for tr in real["root"].one("table", data_table="arm-W").find("tr") if (tr.attrs.get("data-version"), tr.attrs.get("data-variant")) == ("now", "layout")][0].one("svg")
    assert len(frames) > 10 and all(len(p.attrs["points"].split()) == len(frames) for p in svg.find("polyline")) and now["winner"] == "A"


def test_real_shas_are_the_rows_lab_shas(real):
    sec = real["root"].one("section", data_section="shas")
    for r in real["rows"]:
        assert r["lab_sha"] in sec.text()
    assert len({r["lab_sha"] for r in real["rows"]}) == 2 and pf.SHA["then"] in sec.text()


def test_real_page_passes_every_form_check(real):
    html = (real["out"] / "index.html").read_text()
    assert pf.all_problems(html, real["out"]) == []


def test_real_page_is_byte_identical_when_built_twice_and_the_fragment_has_ten_columns(real):
    for name in ("index.html", "artifacts-row.md"):
        assert (real["out"] / name).read_bytes() == (real["out2"] / name).read_bytes()
    line = (real["out"] / "artifacts-row.md").read_text()
    assert len(re.split(r"(?<!\\)\|", line.strip()[1:-1])) == 10 and all(r["lab_sha"] in line for r in real["rows"])
