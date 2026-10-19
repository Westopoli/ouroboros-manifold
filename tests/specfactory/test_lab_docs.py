# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces row L7 (LAB-REV2-L7)
"""Doc tests for the skill lab rev 2 record: README output rule (ruling 12), the retired gap-table
rows (E3 fog and cross-layer fire land in the engine), register rows Q-008-03 / Q-008-07 (ruling 5)
and the Q-LAB-03 note, the ROADMAP section 1 row, and the LAB-REV2 owner rows.

Refresh 2026-10-19 (L7-tests-refresh): the Architect decisions 22 to 37
(docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md) add the checks below the 'decisions 22-37'
banner: DRAFT numbers stay marked DRAFT, superseded README / harness-spec / ROADMAP sentences are gone,
the instrument section names the built commands and refusals. A check pins presence or absence of named
words in one README bullet, paragraph or table row (see _blocks); no number is invented here, every
number comes from the spec's rulings or the decisions file."""
import re
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
README = REPO / "docs" / "northstar" / "research" / "layer_dynamics" / "README.md"
REGISTER = REPO / "docs" / "northstar" / "ambiguity_register.md"
ROADMAP = REPO / "docs" / "northstar" / "ROADMAP.md"
PIECES = REPO / "docs" / "northstar" / "plans" / "push" / "pieces.toml"
HARNESS = REPO / "docs" / "northstar" / "plans" / "skilllab-harness-spec.md"


def _section(text: str, number: int) -> str:
    """Body of '## <number>. ...' up to the next '## ' heading."""
    m = re.search(rf"^## {number}\. .*?$(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m, f"README has no '## {number}.' section"
    return m.group(1)


def _register_row(qid: str) -> list[str]:
    for line in REGISTER.read_text().splitlines():
        if line.startswith(f"| {qid} |"):
            return [c.strip() for c in line.strip().strip("|").split("|")]
    raise AssertionError(f"register has no row {qid}")


# Register columns: id, epic/story, question, candidates, status, answer
STATUS, ANSWER = 4, 5


def _blocks(text: str) -> list[str]:
    """Units a claim lives in: a paragraph (text between blank lines), or one bullet / numbered item /
    table row (a line starting '- ', '* ', '| ' or 'N. ' opens its own block). Heading lines are not blocks."""
    out, cur = [], []
    for ln in text.splitlines():
        if not ln.strip() or ln.startswith("#"):
            if cur:
                out.append(" ".join(cur))
            cur = []
        elif re.match(r"(- |\* |\| |\d+\. )", ln):
            if cur:
                out.append(" ".join(cur))
            cur = [ln.strip()]
        else:
            cur.append(ln.strip())
    if cur:
        out.append(" ".join(cur))
    return out


def _has_block(text: str, *tokens) -> bool:
    """True when ONE block holds every token, case-insensitive. A token is a string or a tuple of alternatives."""
    for b in _blocks(text):
        low = b.lower()
        if all(any(a.lower() in low for a in (t if isinstance(t, tuple) else (t,))) for t in tokens):
            return True
    return False


def _clause(n: int) -> str:
    """Harness-spec acceptance clause n: the line starting 'n. ' under 'Acceptance criteria'."""
    m = re.search(rf"^{n}\. .*$", HARNESS.read_text(), re.M)
    assert m, f"harness spec has no clause {n}"
    return m.group(0)


def _lab_rev2_rows():
    pieces = tomllib.loads(PIECES.read_text())["piece"]
    return [p for p in pieces if p["id"].startswith("LAB-REV2")]


# --- positive controls (green today) ---

def test_control_readme_and_section5_exist():
    assert README.exists()
    assert "Small batches" in _section(README.read_text(), 5)


def test_control_register_rows_exist_with_status_column():
    for qid in ("Q-008-03", "Q-008-07", "Q-LAB-03"):
        assert _register_row(qid)[STATUS] in ("open", "closed"), qid
    assert _register_row("Q-008-04")[STATUS] == "closed"  # control: a row known closed parses as closed


# --- ruling 12: output rule in README section 5 ---

def test_ruling12_readme_section5_has_output_rule():
    body = _section(README.read_text(), 5)
    phrases = [
        "csv", "json",                     # the lab's output is data (CSV, JSON, run metadata)
        "run metadata",
        "claude analyses",
        "top-down",
        "arrows",
        "where the lines cross",
        "a number without its diagram is not evidence",
    ]
    assert _has_block(body, *phrases), \
        f"README section 5 has no single paragraph carrying the ruling 12 output rule phrases: {phrases}"


# --- gap table rows retired (spec L7 row) ---

def test_readme_gap_table_rows_deleted():
    text = README.read_text().lower()
    hits = {s: [i + 1 for i, ln in enumerate(text.splitlines()) if s in ln]
            for s in ("same-layer fire only", "targeting ignores fog")}
    hits = {s: h for s, h in hits.items() if h}
    assert not hits, f"README still carries retired gap rows (phrase: lines): {hits}"


# --- register: Q-008-03 and Q-008-07 closed to (a) by ruling 5; Q-LAB-03 note ---

def test_q_008_03_stays_open_with_rev2_note():
    # decision 39 item 1: Q-008-03 (the cross-layer parameter families) closes only when the ALG rows exist, after
    # batch one's analysis and Westley's numbers; the rev 2 note cites rulings 10 and 11. (Was: closed to (a), ruling 5.)
    row = _register_row("Q-008-03")
    assert row[STATUS] == "open", f"Q-008-03 status is {row[STATUS]!r}"
    text = " | ".join(row).lower()
    assert re.search(r"rulings? 10\b", text), "Q-008-03 row does not cite ruling 10"
    assert re.search(r"(ruling 11|\band 11\b|, 11\b)", text), "Q-008-03 row does not cite ruling 11"
    assert "alg rows" in text, "Q-008-03 row does not say it closes when the ALG rows exist"
    assert "rev 2" in text or "rev2" in text, "Q-008-03 row has no rev 2 note"


def test_ruling5_q_008_07_closed_to_a():
    row = _register_row("Q-008-07")
    assert row[STATUS] == "closed", f"Q-008-07 status is {row[STATUS]!r}"
    assert row[ANSWER].startswith("(a)"), f"Q-008-07 answer {row[ANSWER][:40]!r}"
    assert "ruling 5" in row[ANSWER].lower()


def test_q_lab_03_has_rev2_note():
    row = " | ".join(_register_row("Q-LAB-03")).lower()
    assert "skill-lab-rev2-spec" in row or "lab-rev2" in row, "Q-LAB-03 has no note naming the rev 2 spec"


# --- ROADMAP section 1 row ---

def test_roadmap_section1_has_lab_rev2_row():
    text = ROADMAP.read_text()
    m = re.search(r"^## 1\. .*?$(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m, "ROADMAP has no section 1"
    rows = [ln for ln in m.group(1).splitlines()
            if ln.startswith("|") and ("LAB-REV2" in ln or "skill-lab-rev2-spec" in ln)]
    assert rows, "ROADMAP section 1 has no LAB-REV2 row"
    assert any("2026-10-14-skill-lab-rev2-spec.md" in r for r in rows), "row does not point at the spec"


# --- pieces.toml invariants ---

def test_lab_rev2_rows_all_have_status_table():
    rows = _lab_rev2_rows()
    assert len(rows) >= 14, f"expected umbrella + L1..L7 + S + E0..E4, found {len(rows)}"
    for p in rows:
        st = p.get("status")
        assert isinstance(st, dict) and st.get("state"), f"{p['id']} has no status table"


def test_l7_depends_on_every_other_lab_rev2_row_except_e2_and_e4():
    # decision 39 item 7 (ruler row TD-LAB-REV2-L7-2): E2 and E4 land after the lab landing, so L7 does not wait for them.
    rows = _lab_rev2_rows()
    l7 = next(p for p in rows if p["id"] == "LAB-REV2-L7")
    others = {p["id"] for p in rows if p["id"] not in ("LAB-REV2", "LAB-REV2-L7", "LAB-REV2-E2", "LAB-REV2-E4")}
    missing = sorted(others - set(l7["depends_on"]))
    assert not missing, f"LAB-REV2-L7 depends_on lacks {missing}"


def test_l7_depends_on_drops_e2_and_e4():
    l7 = next(p for p in _lab_rev2_rows() if p["id"] == "LAB-REV2-L7")
    kept = sorted({"LAB-REV2-E2", "LAB-REV2-E4"} & set(l7["depends_on"]))
    assert not kept, f"LAB-REV2-L7 depends_on still lists {kept} (decision 39 item 7)"


# =====================================================================================================
# Decisions 22 to 37 (Architect, 2026-10-19), added by the L7-tests-refresh. Presence / absence of named
# words per bullet, paragraph or table row; the builder writes the sentences, the rulings give the words.
# =====================================================================================================

import pytest  # noqa: E402  (kept beside the block it serves)

# --- controls for the helpers (green today) ---

def test_control_blocks_helper_splits_bullets_rows_and_paragraphs():
    sample = "# H\n\npara one\nsecond line\n\n- bullet a\n- bullet b with CSV\n| C1 | row |\n1. numbered\n"
    assert _blocks(sample) == ["para one second line", "- bullet a", "- bullet b with CSV", "| C1 | row |", "1. numbered"]
    assert _has_block(sample, "bullet b", ("csv", "json"))
    assert not _has_block(sample, "bullet a", "csv")      # two blocks never satisfy one claim together


def test_control_present_readme_and_harness_blocks_parse():
    text = README.read_text()
    assert _has_block(text, "five layers, always")              # a section 6 bullet that stays
    assert _has_block(_section(text, 4), "| C1", "firing advantage")   # the C1 table row stays a table row
    assert _clause(5).startswith("5. ") and _clause(15).startswith("15. ")   # clause lookup does not confuse 5 and 15


# --- README claims: one bullet, paragraph or table row (see _blocks) must carry all the words.
# id -> (README section or None for the whole file, tokens). Sources: the rulings in the spec, decisions 22 to 37.

_README_CLAIMS = {
    # DRAFT numbers stay marked DRAFT (decision 29 item 4, decision 31 F, the spec's open list)
    "draft-opening-window": (None, ("opening window", "40", "draft")),
    "draft-guard-radius": (None, (("guard radius", "guard_radius"), "200", "draft", "E4")),
    "draft-firing-arc": (None, ("firing arc", "120", "draft", "flanked")),
    "draft-cone": (None, ("cone", "300", "45", "1.0", "draft")),
    "draft-mixes": (None, ("M3b", "M4", "draft")),
    "draft-reengage-silence": (None, ("REENGAGE_SILENCE_TICKS", "40", "draft")),
    "draft-scale-marks": (None, ("scale marks", "1.5", "90", "4 h", "draft", "Westley")),
    # section 4, the measure (ruling 1, 5, 6; decisions 28, 29, 31)
    "target-of-record": (4, ("target of record", "can_engage")),
    "two-predictions": (4, ("count-only", "type-weighted", "agreement")),
    "cell-won-by-elimination": (4, ("cell", "won", "every fight")),
    "c1-row": (4, ("| C1", "naive attacker", "naive defender", "mirror")),
    "c2-row": (4, ("| C2", "opening window", "whole fight")),
    "assault-contact": (None, ("assault", ("centre of mass", "center of mass", "centroid"), "guard")),
    "r-087-06-original-point": (None, ("R-087-06", "original point")),
    "reengage-onto-centroid": (None, (("re-engage", "reengage"), "REENGAGE_SILENCE_TICKS", "centroid")),
    # baselines (decisions 25, 26, 29, 32)
    "naive-baselines": (None, ("naive_attacker", "naive_defender", "blob per unit type")),
    "naive-defender-layer-variants": (None, ("naive_defender_play_layer", "naive_defender_attacker_layer", "draft")),
    "baseline-no-fit": (None, ("baseline_no_fit", "ceiling", "finding")),
    "baseline-ceiling-label": (None, ("baseline_ceiling",)),
    # section 5, the artifact (decisions 29, 31, 34)
    "artifact-thresholds": (5, ("artifact", "--thresholds", "thresholds not supplied")),
    "artifact-both-wrong": (5, ("both_wrong", "finding")),
    "artifact-diagram-per-crossing": (5, ("ceiling hit", "crossing", "diagram")),
    "artifact-bracketing-arrows": (5, ("bracketing", "arrows", "break-even")),
    "artifact-legend-draft": (5, ("draft", "legend")),
    "point-column": (None, ("`point`", "half=", "vision=")),
    "ground-scene-inert-knobs": (None, ("s1_slope_top", "12000", "inert")),   # decision 18
    # section 7, the instrument
    "commands": (7, ("`smoke`", "`sweep`", "`artifact`")),
    "preflight-refusals": (7, ("`no_fit`", "`unroutable`", "`no_reach`")),
    "count-is-can-engage": (7, ("can_engage", "parity")),
    # section 12, open
    "speed-marks-finding": (12, ("FINDING-speed-marks-unmet", "Westley")),
    # decision 39
    "orders-per-unit-default": (None, ("`orders_per_unit`", "True", "E1b", "smoke", "zero")),
    "arc-cone-batch-two": (None, ("arc", "cone", "built", "E2", "batch two")),
}


@pytest.mark.parametrize("claim", sorted(_README_CLAIMS))
def test_readme_claim(claim):
    section, tokens = _README_CLAIMS[claim]
    text = README.read_text()
    if section is not None:
        text = _section(text, section)
    assert _has_block(text, *tokens), \
        f"README{'' if section is None else f' section {section}'} has no single bullet, paragraph or row carrying {tokens}"


# --- README: superseded sentences are gone ---

def test_readme_band_is_a_ruling_not_a_draft():
    # decision 31 F: the 0.25x to 4x band is a ruling, not a draft number, and is not marked.
    hits = re.findall(r"draft\W{0,3}0\.25x", README.read_text(), re.I)
    assert not hits, "README still marks the 0.25x to 4x band as a draft"


@pytest.mark.parametrize("stale", [
    "able-to-fire-eligible",                          # ruling 5 replaced the 'option (a)' target rule
    "draft definition to be approved",                # ruling 5 settled it
    "ending ahead by a margin",                       # ruling 1: a cell is won by elimination, no margin
    "waits for the sim to have ground",               # spec L6: the ground scene s1_slope_top is built
    "close when the lab's numbers fold",              # Q-008-03 closed to (a) by ruling 5
])
def test_readme_stale_sentence_is_gone(stale):
    assert stale not in README.read_text().lower(), f"README still says: {stale!r}"


def test_readme_names_the_ground_scene_and_does_not_present_highground_as_live():
    text = README.read_text()
    live = [ln for ln in text.splitlines()
            if "highground.py" in ln and "deleted" not in ln.lower() and "retired" not in ln.lower()]
    assert not live, f"README presents ground/highground.py (deleted by L6) as existing: {live[0][:100]}"
    assert "s1_slope_top" in text, "README never names the ground scene s1_slope_top"


@pytest.mark.parametrize("fid", ["FINDING-damage-up-layer-above", "FINDING-group-orders-cap", "FINDING-attackmove-idle-cap"])
def test_readme_open_list_names_the_findings(fid):
    # decision 39 item 5: ids only; status is the ledger's at L7 time
    assert fid in _section(README.read_text(), 12), f"README section 12 does not name {fid}"


def test_readme_section8_points_at_rev2_spec_and_first_batch():
    sec = _section(README.read_text(), 8)
    assert "2026-10-14-skill-lab-rev2-spec.md" in sec, "section 8 does not point at the rev 2 spec"
    assert "coarse knob batch" in sec.lower(), "section 8 does not name the first coarse knob batch"


# --- register: the Q-LAB-03 note names the new lab drafts (decisions 4, 28) ---

def test_q_lab_03_note_names_the_new_lab_drafts():
    row = " | ".join(_register_row("Q-LAB-03"))
    for name in ("DRAFT-opening-window-ticks", "REENGAGE_SILENCE_TICKS"):
        assert name in row, f"Q-LAB-03 row does not name {name}"


def test_q_lab_01_marked_superseded_by_q_lab_03():
    assert "superseded by q-lab-03" in " | ".join(_register_row("Q-LAB-01")).lower(), \
        "Q-LAB-01 row does not say it is superseded by Q-LAB-03 (decision 39 item 6)"


# --- ROADMAP rows that the elimination ruling and L6 make stale ---

def test_roadmap_t14_row_follows_q_lab_03():
    rows = [ln for ln in ROADMAP.read_text().splitlines() if ln.startswith("| T14 |")]
    assert rows, "ROADMAP has no T14 row"
    assert "not yet recorded" not in rows[0], "T14 still says outcome classes are not yet recorded"
    assert "Q-LAB-03" in rows[0], "T14 does not cite Q-LAB-03 (elimination only, cap as defect)"
    assert "Q-LAB-01" not in rows[0], "T14 still cites Q-LAB-01 (superseded by Q-LAB-03; decision 39 item 6)"


def test_roadmap_highground_instrument_is_not_listed_as_live():
    stale = [ln for ln in ROADMAP.read_text().splitlines()
             if "highground.py" in ln and "deleted" not in ln.lower() and "retired" not in ln.lower()]
    assert not stale, f"ROADMAP still lists highground.py (deleted by L6) as existing: {stale[0][:120]}"


# --- harness spec: the clauses decision 15 names (5, 11, 12, 13) are rewritten; each loses 'stalemate' / the win margin ---

_CLAUSE_WORDS = {   # clause -> words it must carry (rev 2 contract: elimination only, cap a defect, FightResult and Setup fields)
    5: ("elimination", "`cap`", "`orders_per_unit`", "`Setup.point`"),
    11: ("`draw`", "`cap`", "firing_window", "weighted_unit_seconds", "weighted_window",
         "predicted_count", "predicted_type", "agreement", "states"),
    # decision 39 item 2: reach_play retired by ruling 2, damage_play the labelled positive control, point for goal None,
    # per-unit orders until the decision 23 flip, the contact placement sentence stands
    12: ("`Setup.point`", "meeting", "per-unit", "`orders_per_unit`", "`reach_play`", "retired", "ruling 2",
         "labelled positive control", "Contact placement"),
    13: ("every fight", "side0", "defect"),
    14: ("bisection", "`ceiling_hit`", "`multi_flip`", "`full_scan`"),
    17: ("firing_window_0", "weighted_unit_seconds_0", "weighted_window_0", "predicted_count", "predicted_type", "agreement",
         "`knob`", "`knob_value`", "`baseline`", "`ceiling_hit`", "`prefight`", "reengage_0", "`point`", "baseline_no_fit"),
    18: ("`artifact`", "SVG"),
    19: ("ceiling hit", "scan cut by baseline_no_fit"),
    20: ("`full_scan`",),
    26: ("TD-LAB-REV2-golden",),
    28: ("FINDING-speed-marks-unmet", "known red", "Westley"),
}
_CLAUSE_ABSENT = {   # clause -> stale words it must not keep
    12: ("a study knob", "`goal` None"),
    14: ("(all won, all lost, or flat)",),
}


@pytest.mark.parametrize("n,word", [(n, w) for n in sorted(_CLAUSE_ABSENT) for w in _CLAUSE_ABSENT[n]])
def test_harness_clause_drops_stale_words(n, word):
    assert word not in _clause(n), f"clause {n} still says {word}"


@pytest.mark.parametrize("n", [5, 11, 12])
def test_harness_clause_has_no_stalemate(n):
    assert "stalemate" not in _clause(n).lower(), f"clause {n} still mentions a stalemate (retired by Q-LAB-03)"


def test_harness_clause13_has_no_win_margin():
    c = _clause(13)
    assert "win margin" not in c.lower() and "0.05" not in c, "clause 13 still defines a won cell by a win margin"


@pytest.mark.parametrize("n,word", [(n, w) for n in sorted(_CLAUSE_WORDS) for w in _CLAUSE_WORDS[n]])
def test_harness_clause_carries_rev2_word(n, word):
    assert word.lower() in _clause(n).lower(), f"clause {n} lacks {word}"


# --- pieces.toml: L7 must own every file its tests make it edit ---

def test_l7_owns_the_harness_spec():
    l7 = next(p for p in _lab_rev2_rows() if p["id"] == "LAB-REV2-L7")
    owned = set(l7["owns"])
    assert "docs/northstar/plans/skilllab-harness-spec.md" in owned, \
        "LAB-REV2-L7 does not own the harness spec it must rewrite (clauses 5, 11, 12, 13; decision 15)"


def test_l1_no_longer_owns_the_harness_spec():
    # decision 39 item 7: two in-flight rows never own one file; L1 is built and has no further edit to it.
    l1 = next(p for p in _lab_rev2_rows() if p["id"] == "LAB-REV2-L1")
    assert "docs/northstar/plans/skilllab-harness-spec.md" not in l1["owns"], "LAB-REV2-L1 still owns the harness spec"
