# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R1 known cap; defect D9); ledger FINDING-lab-d9; piece LAB-REV3-B
"""LAB-REV3-B, the artifact prints the mixes' caps (Architect ruling 2026-10-20): "the artifact prints M9's caps under that finding until
the engine piece lands". Implemented in scripts/skilllab/report.py (the B builder owns that edit); fast half, rendered through
report.artifact exactly as tests/skilllab/test_report.py renders it (its `_page` helper and parsed-tree helpers are reused; this file does
not edit test_report.py).

PLUMBING CONTRACT (DRAFT, the minimal key; the Architect left the shape to the writer):
  summary["mixes"] = {mix name: the verdict dict of sweep.mirror_precheck for that mix}
    each verdict has the keys the mirror tests pin: ok, reason (None, "capped", "warden_cap" or "known_cap:FINDING-lab-d9"), fights,
    caps, rosters ({capped fight index: living}); a "mix" key (the units) may be present and is not read.
  The sweep side that fills summary["mixes"] (after vet_mixes) is the builder's; the report side reads only this key.
  With no summary["mixes"] there is no mixes section (so the section list pinned in test_report.py is unchanged for every older summary).
THE TABLE: a section <section id="mixes"> holding one <table>. A header row of <th>; one <tr data-mix="NAME"> per mix of the dict, in the
  dict's order, its cells <td> in the same order as the <th>. One header is exactly "caps (known)" (the column the ruling names); the other
  columns (the mix name first, the units, ok/reason) are the builder's. The caps cell, DRAFT wording (to be ratified with the header):
    a mix with no caps                       "0 of 30"
    a mix whose only cap is the known one    "1 of 30, known_cap:FINDING-lab-d9, fight 12 seed 6"
  where N of F reads caps of fights, and "fight i seed s" reads the capped fight's index i and its seed s = i // 2 (the mirror's DRAFT scheme:
  fight i is seed i // 2). Not pinned (listed in the report): the cell of a rejected mix (caps off the pattern), of a mix with more than one
  known cap, and of a Warden-cap refusal (fights 0).
THE HEADER: the artifact's DRAFT list gains DRAFT-mix-M5 .. DRAFT-mix-M9, once each, always listed (with or without summary["mixes"]), like
  DRAFT-mix-M1 .. M4 and M3b. test_report.py::test_l5_artifact_header_lists_every_draft_number_in_force_once and ...lists_the_scene_and_mix_
  draft_names_once (the pinned name tuples SCENE_MIX_DRAFTS, lines 1247-1290) go red on the builder's tree and move under the ruler's TD row
  (assumption changed: five more mixes); this file is not that row.
Red today: report.py has no mixes section and none of the five names."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (ROOT, HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from test_report import _artifact_inputs, _page, _sec, _tree  # noqa: E402

KNOWN = "known_cap:FINDING-lab-d9"
WARDENS = ({"Warden": 3}, {"Warden": 2})
NAMES = ("DRAFT-mix-M5", "DRAFT-mix-M6", "DRAFT-mix-M7", "DRAFT-mix-M8", "DRAFT-mix-M9")
COLUMN = "caps (known)"


def verdict(caps=(), reason=None, ok=True):
    return {"ok": ok, "reason": reason, "fights": 30, "caps": len(caps), "rosters": {i: WARDENS for i in caps}}


def mixes_summary(**mixes):
    _, _, summary = _artifact_inputs()
    return {**summary, "mixes": mixes}


def cell(root, mix, column=COLUMN):
    """The text of `column` in the row of `mix` of the mixes table; fails loudly when the table, the column or the row is missing."""
    section = _sec(root, "mixes")
    tables = section.find("table")
    assert len(tables) == 1, "the mixes section holds %d tables" % len(tables)
    heads = [th.text() for th in tables[0].find("th")]
    assert column in heads, "no column %r in %s" % (column, heads)
    rows = [tr for tr in tables[0].find("tr") if tr.attrs.get("data-mix") == mix]
    assert len(rows) == 1, "%d rows for mix %r" % (len(rows), mix)
    tds = rows[0].find("td")
    assert len(tds) == len(heads), "row %r has %d cells, the header %d" % (mix, len(tds), len(heads))
    return tds[heads.index(column)].text()


# ---- the cell lookup's own positive control (green on the base) --------------------------------------------------------------------

def test_control_the_cell_lookup_reads_a_column_by_its_header_and_a_row_by_data_mix():
    html = ('<section id="mixes"><table><tr><th>mix</th><th>caps (known)</th></tr>'
            '<tr data-mix="A"><td>A</td><td>1 of 30</td></tr><tr data-mix="B"><td>B</td><td>0 of 30</td></tr></table></section>')
    root = _tree(html)
    assert cell(root, "A") == "1 of 30" and cell(root, "B") == "0 of 30"
    with pytest.raises(AssertionError):
        cell(root, "C")
    with pytest.raises(AssertionError):
        cell(root, "A", column="other")


# ---- the mixes table ----------------------------------------------------------------------------------------------------------------

def test_t1_the_artifact_has_a_mixes_table_with_the_caps_known_column(tmp_path):
    """R1 exception: summary["mixes"] makes a mixes section with a column headed exactly "caps (known)". Red today: no such section."""
    root = _tree(_page(tmp_path, summary=mixes_summary(M5=verdict(), M9=verdict((12,), KNOWN)))[2])
    heads = [th.text() for th in _sec(root, "mixes").find("table")[0].find("th")]
    assert COLUMN in heads, heads
    assert [tr.attrs["data-mix"] for tr in _sec(root, "mixes").find("tr") if "data-mix" in tr.attrs] == ["M5", "M9"]


def test_t1_m9_reads_one_of_30_with_the_known_cap_finding_and_its_fight_and_seed(tmp_path):
    """The ruled reading (DRAFT wording): "1 of 30, known_cap:FINDING-lab-d9, fight 12 seed 6". Red today: no mixes section."""
    root = _tree(_page(tmp_path, summary=mixes_summary(M9=verdict((12,), KNOWN)))[2])
    assert cell(root, "M9") == "1 of 30, %s, fight 12 seed 6" % KNOWN


def test_t1_the_seed_in_the_cell_follows_the_fight_index_not_a_constant(tmp_path):
    """Control against a hard-coded cell: a known cap at fight 7 reads seed 3 (seed = i // 2)."""
    root = _tree(_page(tmp_path, summary=mixes_summary(M9=verdict((7,), KNOWN)))[2])
    assert cell(root, "M9") == "1 of 30, %s, fight 7 seed 3" % KNOWN


def test_t1_a_clean_mix_reads_0_of_30(tmp_path):
    root = _tree(_page(tmp_path, summary=mixes_summary(M5=verdict(), M9=verdict((12,), KNOWN)))[2])
    assert cell(root, "M5") == "0 of 30"


def test_t1_the_cell_is_per_mix_in_one_page(tmp_path):
    root = _tree(_page(tmp_path, summary=mixes_summary(M5=verdict(), M6=verdict(), M9=verdict((12,), KNOWN)))[2])
    assert [cell(root, m) for m in ("M5", "M6", "M9")] == ["0 of 30", "0 of 30", "1 of 30, %s, fight 12 seed 6" % KNOWN]


def test_t1_the_cell_survives_a_json_round_trip_of_the_summary(tmp_path):
    """summary.json is read back by the artifact command: the rosters' integer keys come back as strings and the living tuples as lists.
    The same cells are printed."""
    summary = json.loads(json.dumps(mixes_summary(M5=verdict(), M9=verdict((12,), KNOWN))))
    assert list(summary["mixes"]["M9"]["rosters"]) == ["12"]
    root = _tree(_page(tmp_path, summary=summary)[2])
    assert cell(root, "M9") == "1 of 30, %s, fight 12 seed 6" % KNOWN and cell(root, "M5") == "0 of 30"


def test_t1_without_summary_mixes_there_is_no_mixes_section(tmp_path):
    """Keeps the section list pinned in test_report.py (SECTIONS) true for every older summary. Green today."""
    root = _tree(_page(tmp_path)[2])
    assert not root.find("section", id="mixes")


# ---- the header DRAFT list ---------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("with_mixes", [False, True], ids=["no-mixes-key", "with-mixes"])
def test_t1_the_header_lists_draft_mix_m5_to_m9_once_each(tmp_path, with_mixes):
    """DRAFT-mix-M5 .. M9 join the header DRAFT list, always listed, once each, whether or not the batch carries mirror verdicts.
    Red today: the list ends at DRAFT-mix-M3b."""
    summary = mixes_summary(M9=verdict((12,), KNOWN)) if with_mixes else None
    root = _tree(_page(tmp_path, summary=summary)[2])
    names = [li.attrs["data-draft"] for li in _sec(root, "drafts").find("li") if "data-draft" in li.attrs]
    for name in NAMES:
        assert names.count(name) == 1, (name, names.count(name))


def test_t1_no_diagram_legend_carries_the_new_mix_drafts(tmp_path):
    """As for M1 to M4: a diagram's legend lists the draft numbers its arrows touch; these touch none."""
    root = _tree(_page(tmp_path)[2])
    svgs = root.find("svg")
    assert svgs, "positive control: the page with rows has diagrams to look in"
    assert not [n for svg in svgs for n in svg.iter() if n.attrs.get("data-draft") in NAMES]
