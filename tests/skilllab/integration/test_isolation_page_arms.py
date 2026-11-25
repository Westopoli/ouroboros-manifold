# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 6 ("per-arm tables and curves (break-even maps with flips, units-firing lines labelled, never one number); the DRAFT list; the lab SHAs"),
# section 8 ruling 2 ("the movement-stopping check ... blocks a landing. Role and layout flags stay labels"), section 1 precondition 3 ("Flags are signals, never verdicts"), piece LI5 part 1
"""Per-arm tables and curves, the stopping-check badge, the flags, the DRAFT list and the shas. Interface: docs/reports/2026-11-24-li5-interface.md.
Red today: `scripts/skilllab/arena/isolation_page.py` does not exist."""
import re

import pytest

import isolation_page_fixtures as pf

HEX40 = re.compile(r"\b[0-9a-f]{40}\b")


def render(tmp_path, rows=None, **kw):
    out, res = pf.build(tmp_path, rows if rows is not None else pf.synthetic_rows() + pf.synthetic_f_rows(), **kw)
    return pf.page_root(out), out


# ------------------------------------------------------------------ arm M

def test_m_map_lists_every_point_with_its_flips_marked_never_one_number(tmp_path):
    """spec 6: "break-even maps with flips ... never one number". Points 14 won, 15 won, 16 lost, 17 won, 18 lost: three flips, every point has a row, each flip is marked."""
    pts = ((14, True, 0), (15, True, 0), (16, False, 0), (17, True, 0), (18, False, 0))
    root, _ = render(tmp_path, m=[pf.m_summary(points=pts)])
    t = root.one("section", data_section="arm-M").one("table", data_table="arm-M")
    rows = {tr.attrs["data-enemy"]: tr for tr in t.find("tr") if "data-enemy" in tr.attrs}
    assert list(rows) == ["14", "15", "16", "17", "18"]
    flipped = [e for e, tr in rows.items() if tr.attrs.get("data-flip") == "true"]
    assert flipped == ["16", "17", "18"]              # a flip is marked on the point after it (`after` of the summary's flips)
    assert "win_to_loss" in {td.attrs["data-col"]: td.text() for td in rows["16"].find("td") if "data-col" in td.attrs}["flip"]
    assert {td.attrs["data-col"]: td.text() for td in rows["16"].find("td") if "data-col" in td.attrs}["won"] == "lost"
    assert root.one("section", data_section="arm-M").find(data_multi_flip="true")


def test_m_map_cells_come_from_the_points(tmp_path):
    base, _ = render(tmp_path / "a", m=[pf.m_summary(points=((16, True, 0), (17, False, 0)))])
    planted, _ = render(tmp_path / "b", m=[pf.m_summary(points=((16, True, 0), (17, True, 0)))])
    cell = lambda r, e: {td.attrs["data-col"]: td.text() for td in [tr for tr in r.find("tr") if tr.attrs.get("data-enemy") == e][0].find("td") if "data-col" in td.attrs}
    assert cell(base, "16") == cell(planted, "16") and cell(base, "17")["won"] == "lost" and cell(planted, "17")["won"] == "won"


def test_m_defect_point_is_a_defect_not_a_loss(tmp_path):
    s = pf.m_summary(points=((16, True, 0), (17, False, 0)))
    s["points"][1].update(defect=True, won=False)
    root, _ = render(tmp_path, m=[s])
    tr = [tr for tr in root.find("tr") if tr.attrs.get("data-enemy") == "17"][0]
    assert {td.attrs["data-col"]: td.text() for td in tr.find("td") if "data-col" in td.attrs}["won"] == "defect"


def test_stopping_check_is_the_only_blocks_badge(tmp_path):
    """spec 8 ruling 2: "the movement-stopping check (an order ended short, M arm) blocks a landing. Role and layout flags stay labels". An offender: unit ids with tick and place are listed."""
    hit = pf.m_summary(version="now", blocks=True, units=[(17, 510, 1234.5, 987.25), (23, 640, 1500.0, 1400.0)])
    root, _ = render(tmp_path, m=[hit, pf.m_summary(version="then")], v=[pf.v_row(flags=("defect",))])
    badges = [n for n in root.walk() if "blocks" in n.cls()]
    assert len(badges) == 1 and badges[0].text().strip().lower() == "blocks"
    holder = badges[0].parent
    while holder is not None and "data-version" not in holder.attrs:
        holder = holder.parent
    assert holder is not None and holder.attrs["data-version"] == "now"       # the badge sits in the hit summary's block, not the clean `then` one
    sec = root.one("section", data_section="arm-M")
    for uid, tick, x, y in ((17, 510, "1234.5", "987.25"), (23, 640, "1500", "1400")):
        li = sec.one("li", data_unit_id=str(uid))
        assert all(token in li.text() for token in (str(uid), str(tick), x, y))
    assert len(re.findall(r"\bblocks\b", root.text(), re.I)) == 1


def test_no_hit_means_no_blocks_anywhere_in_the_page(tmp_path):
    """The stopping-check result is shown (count 0, the word `orders ended short`), the word `blocks` is not."""
    root, out = render(tmp_path, m=[pf.m_summary()], v=[pf.v_row(flags=("defect", "orders_ended_short"))])
    assert not re.search(r"\bblocks?\b", root.text(), re.I) and not [n for n in root.walk() if "blocks" in n.cls() or "data-blocks" in n.attrs]
    sec = root.one("section", data_section="arm-M")
    assert re.search(r"orders ended short:?\s*0", sec.text())


def test_m_stopping_result_not_measured_is_not_a_zero(tmp_path):
    s = pf.m_summary()
    s["rows"][0]["stopping"] = {"orders_ended_short": "not measured: the file has no destination", "units": [], "died_short": [], "blocks": None}
    root, _ = render(tmp_path, m=[s])
    sec = root.one("section", data_section="arm-M")
    assert "not measured: the file has no destination" in sec.text() and not [n for n in root.walk() if "blocks" in n.cls()]


# ------------------------------------------------------------------ arm V

def test_v_table_one_row_per_run_with_its_vision_values(tmp_path):
    rows = [pf.v_row("now", standoff=3, first_shot=141), pf.v_row("now", kind="stage4", layout="L-0080", standoff=0, first_shot=77, expected="A", part_word="pass")]
    root, _ = render(tmp_path, v=rows)
    cells = pf.table_cells(root, "arm-V")
    flat, st4 = cells[("L-9002", "flat", "now")], cells[("L-0080", "stage4", "now")]
    assert flat["standoff_count"] == "3" and flat["first_shot_tick"] == "141" and st4["standoff_count"] == "0" and st4["first_shot_tick"] == "77"
    assert st4["part_word"] == "pass" and flat["part_word"] == "no stated direction" and "700" in flat["sensor"] and "330" in flat["notice"]


def test_v_not_measured_at_then_is_that_text_never_zero(tmp_path):
    """spec 2: the cell says "not measured at V-then", never a blank or a zero (sensor, notice, first seen, the sight twin)."""
    root, _ = render(tmp_path, v=[pf.v_row("then", layout="L-0061", kind="stage4")])
    c = pf.table_cells(root, "arm-V")[("L-0061", "stage4", "then")]
    for col in ("sensor", "notice", "first_seen", "twin"):
        assert c[col] == "not measured at then", col


# ------------------------------------------------------------------ arms W and F

def test_w_and_f_tables_one_row_per_cell(tmp_path):
    root, _ = render(tmp_path)
    w, f = pf.table_cells(root, "arm-W"), pf.table_cells(root, "arm-F")
    assert sorted(w) == sorted((l, v, ver) for l in ("L-0055", "L-0084") for v in ("layout", "control") for ver in ("then", "now"))
    assert sorted(f) == sorted(("L-0084", v, ver) for v in ("layout", "control") for ver in ("then", "now"))
    c = w[("L-0084", "layout", "now")]
    assert c["winner"] == "A" and c["survivors"] == "18:0" and c["last_tick"] == "2097" and c["end"] == "wipe"
    assert f[("L-0084", "control", "then")]["survivors"] == "0:9"


def test_planted_arm_row_changes_exactly_its_arm_cell(tmp_path):
    base, _ = render(tmp_path / "a")
    planted, _ = render(tmp_path / "b", pf.synthetic_rows() + pf.synthetic_f_rows({("now", "L-0084", "layout"): {"surv": (0, 7)}}))
    a, b = pf.table_cells(base, "arm-F"), pf.table_cells(planted, "arm-F")
    assert [k for k in a if a[k] != b[k]] == [("L-0084", "layout", "now")] and b[("L-0084", "layout", "now")]["survivors"] == "0:7"
    assert pf.table_cells(base, "arm-W") == pf.table_cells(planted, "arm-W")


def test_a_differing_f_reading_is_the_first_differing_arm(tmp_path):
    """spec 5: "the first arm in the order M, V, R, F, P, W whose reading differs between versions"."""
    root, _ = render(tmp_path, pf.synthetic_rows() + pf.synthetic_f_rows({("now", "L-0084", "layout"): {"winner": "A", "surv": (4, 0)}}))
    assert pf.table_cells(root, "comparison")[("L-0084", None, None)]["first_arm"] == "F"


def test_units_firing_lines_are_labelled_curves_with_every_frame(tmp_path):
    """spec 6: "units-firing lines labelled, never one number": one polyline per side, a point per frame, labelled."""
    root, _ = render(tmp_path)
    td = [tr for tr in root.one("table", data_table="arm-W").find("tr") if (tr.attrs.get("data-layout"), tr.attrs.get("data-variant"), tr.attrs.get("data-version")) == ("L-0084", "layout", "now")][0]
    (svg,) = td.find("svg")
    lines = {p.attrs["data-side"]: p for p in svg.find("polyline")}
    assert sorted(lines) == ["A", "B"]
    for side, line in lines.items():
        assert len(line.attrs["points"].split()) == 3 and "units firing" in line.attrs["aria-label"].lower() and side in line.attrs["aria-label"]
    assert "units firing" in svg.text().lower() or svg.find("title")


def test_units_firing_not_measured_at_then_is_text_not_a_curve(tmp_path):
    root, _ = render(tmp_path)
    tr = [tr for tr in root.one("table", data_table="arm-W").find("tr") if (tr.attrs.get("data-layout"), tr.attrs.get("data-variant"), tr.attrs.get("data-version")) == ("L-0084", "layout", "then")][0]
    c = {td.attrs["data-col"]: td for td in tr.find("td") if "data-col" in td.attrs}
    assert not c["units_firing"].find("svg") and "not measured at then" in c["units_firing"].text()
    assert c["invalid"].text().startswith("not measured at then") and "agreement" in c and "not measured at then" in c["agreement"].text()
    assert not re.fullmatch(r"0|0:0", c["units_firing"].text().strip())


def test_invalid_rules_are_listed_by_id_and_a_defect_is_a_signal(tmp_path):
    rows = pf.synthetic_rows({("now", "L-0055", "layout"): {"invalid": ["R-097-05"]}})
    root, _ = render(tmp_path, rows)
    w = pf.table_cells(root, "arm-W")
    assert "R-097-05" in w[("L-0055", "layout", "now")]["invalid"] and "R-097-05" not in w[("L-0055", "control", "now")]["invalid"]
    flags = w[("L-0084", "control", "then")]["flags"]
    assert "signal: defect" in flags and "signal" not in w[("L-0055", "layout", "now")]["flags"].replace("signal: invalid", "")


def test_flags_are_worded_as_signals_never_verdicts(tmp_path):
    """precondition 3: "Flags are signals, never verdicts": "only a signal, not a conclusion" (L-0104). A flag element carries the class `flag` and nothing else, and says `signal:`."""
    rows = pf.synthetic_rows({("now", "L-0055", "layout"): {"invalid": ["R-097-05"]}})
    root, _ = render(tmp_path, rows, v=[pf.v_row(flags=("defect", "invalid", "orders_ended_short"))], m=[pf.m_summary()])
    flags = [n for n in root.walk() if "data-flag" in n.attrs]
    assert {n.attrs["data-flag"] for n in flags} >= {"defect", "invalid", "orders_ended_short"}
    for n in flags:
        assert n.cls() == ["flag"] and n.text().startswith("signal: ")
    assert not [n for n in root.walk() if set(n.cls()) & {"bad", "fail", "error", "pass", "ok", "danger"}]
    assert not re.search(r"regressed|improved", root.text(), re.I)


# ------------------------------------------------------------------ the DRAFT list and the shas

def test_draft_list_shows_each_name_and_value_passed_in(tmp_path):
    root, _ = render(tmp_path, drafts={"DRAFT_OPENING_WINDOW_40": 40, "DRAFT_SEEDS": (10, 1), "DRAFT_SAME_OR_CHANGED_RULE": "identical winner over the seeds"})
    items = {li.attrs["data-draft"]: li.text() for li in root.one("section", data_section="drafts").find("li")}
    assert sorted(items) == ["DRAFT-opening-window-40", "DRAFT-same-or-changed-rule", "DRAFT-seeds"]
    assert "40" in items["DRAFT-opening-window-40"] and "10" in items["DRAFT-seeds"] and "identical winner over the seeds" in items["DRAFT-same-or-changed-rule"]
    assert "Westley" in root.one("section", data_section="drafts").text()      # the list says whose numbers these are


def test_draft_label_form():
    mod = pf.page()
    assert mod.draft_label("DRAFT_OPENING_WINDOW_40") == "DRAFT-opening-window-40" and mod.draft_label("DRAFT_IDLE_FRONT_BEHIND") == "DRAFT-idle-front-behind"
    with pytest.raises(ValueError):
        mod.draft_label("OPENING_WINDOW")


def test_collected_drafts_are_the_modules_constants_with_their_values():
    mod, fw, im = pf.page(), pf.fw(), pf.importlib.import_module("scripts.skilllab.arena.isolation_measures")
    got = mod.collect_drafts()
    assert got["DRAFT_OPENING_WINDOW_40"] == im.DRAFT_OPENING_WINDOW_40 == 40 and got["DRAFT_SEEDS"] == fw.DRAFT_SEEDS
    assert got["DRAFT_SAME_OR_CHANGED_RULE"] == fw.DRAFT_SAME_OR_CHANGED_RULE and all(k.startswith("DRAFT_") for k in got)
    assert {k for k in dir(im) if k.startswith("DRAFT_")} <= set(got)


def test_default_page_lists_the_collected_drafts(tmp_path):
    root, _ = render(tmp_path)
    shown = {li.attrs["data-draft"] for li in root.one("section", data_section="drafts").find("li")}
    assert {pf.page().draft_label(k) for k in pf.page().collect_drafts()} == shown


def test_lab_and_engine_shas_per_version_from_the_rows_and_the_clips(tmp_path):
    """spec 6: "the lab SHAs"; each version's full sha, and the engine sha of each clip."""
    manifest = pf.clip_dir(tmp_path / "src", [("l0084-changed", "L-0084", "changed", ["then", "now"])])
    root, _ = render(tmp_path, clips=manifest)
    sec = root.one("section", data_section="shas")
    shown = {li.attrs["data-version"]: li.text() for li in sec.find("li") if "data-version" in li.attrs}
    assert pf.SHA["then"] in shown["then"] and pf.SHA["now"] in shown["now"]
    assert set(HEX40.findall(sec.text())) == set(pf.SHA.values())
    assert sec.text().count(pf.SHA["now"]) >= 1


def test_a_planted_lab_sha_reaches_the_page(tmp_path):
    rows = pf.synthetic_rows()
    for r in rows:
        if r["version"] == "now":
            r["lab_sha"] = "e" * 40
    root, _ = render(tmp_path, rows)
    assert "e" * 40 in root.one("section", data_section="shas").text()
