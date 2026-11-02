# Rule pins: R-087-06@45fc58
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

def test_q_008_03_closed_with_fu_row():
    # Architect 2026-10-22 (implementation; Westley may veto) closed Q-008-03 and owes the ALG rows as FU-lab-alg-rows in the push ledger
    # (ledger row TD-LAB-REV2-q008-closed). (Was test_q_008_03_stays_open_with_rev2_note: asserted status open and the rev 2 note.)
    row = _register_row("Q-008-03")
    assert row[STATUS] == "closed", f"Q-008-03 status is {row[STATUS]!r}"
    ledger = (REPO / "docs" / "northstar" / "plans" / "push_ledger_2026-09-22.md").read_text()
    assert any(ln.startswith("|") and "FU-lab-alg-rows" in ln.split("|")[2] for ln in ledger.splitlines()), \
        "the push ledger has no FU-lab-alg-rows row"


def test_ruling5_q_008_07_closed_to_a():
    row = _register_row("Q-008-07")
    assert row[STATUS] == "closed", f"Q-008-07 status is {row[STATUS]!r}"
    assert row[ANSWER].startswith("(a)"), f"Q-008-07 answer {row[ANSWER][:40]!r}"
    assert "ruling 5" in row[ANSWER].lower()


def test_q_lab_03_has_rev2_note():
    row = " | ".join(_register_row("Q-LAB-03")).lower()
    assert "skill-lab-rev2-spec" in row or "lab-rev2" in row, "Q-LAB-03 has no note naming the rev 2 spec"


# --- ROADMAP section 1 row ---

def _roadmap_section1_problems(text: str) -> list[str]:
    m = re.search(r"^## 1\. .*?$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return ["ROADMAP has no section 1"]
    body = m.group(1)
    out = []
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")]
            for ln in body.splitlines() if ln.startswith("|")]
    if not any(len(r) >= 3 and r[0] == "lab" and "H-0" in r[2] for r in rows):
        out.append("ROADMAP section 1 has no row with first cell 'lab' and an H-0 story id")
    if "2026-10-31-lab-staircase.md" not in body:
        out.append("ROADMAP section 1 intro does not name 2026-10-31-lab-staircase.md")
    return out


# Test-defect: ROADMAP section 1 rewritten as the two staircases by Westley's order of 2026-11-02;
# the lab rev 2 row it pinned is history (DEC-beta-staircase-2026-11-02)
def test_roadmap_section1_has_lab_row():
    problems = _roadmap_section1_problems(ROADMAP.read_text())
    assert not problems, problems


def test_control_roadmap_section1_without_lab_row_fails():
    planted = ("## 1. Now building\n\nplans/2026-10-31-lab-staircase.md\n\n"
               "| Staircase | Stage | Story |\n|---|---|---|\n| beta | B0 | H-028 |\n\n## 2. Next\n")
    assert _roadmap_section1_problems(planted), "planted text without a lab row must fail"
    good = planted.replace("| beta | B0 | H-028 |", "| lab | 1 | H-040 |")
    assert not _roadmap_section1_problems(good)


# --- pieces.toml invariants ---

def test_lab_rev2_rows_all_have_status_table():
    rows = _lab_rev2_rows()
    assert len(rows) >= 14, f"expected umbrella + L1..L7 + S + E0..E4, found {len(rows)}"
    for p in rows:
        st = p.get("status")
        assert isinstance(st, dict) and st.get("state"), f"{p['id']} has no status table"


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
    "firing-arc-ruled": (None, ("firing arc", "30", "Westley", "flanked")),   # decision 46: 30 degrees is Westley's, no longer the 120 draft (TD-LAB-REV2-FIX5-arc30)
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
    # the orders_per_unit default is no longer a mandatory-text claim: decision 43 item 1 makes the flip conditional on a smoke rerun, so
    # test_readme_states_the_orders_per_unit_default_the_code_has (below) reads the default and checks the README against it (TD-LAB-REV2-L7-3)
    # decision 41 item 6: ruling 4's 8..48 is the scan of the plays; the golden-hash controls keep their own range (TD-LAB-REV2-FIX-docs)
    "scan-range-plays-not-golden-controls": (None, (("8 to 48", "8..48"), "plays", "golden", ("8 to 24", "8..24"),
                                                    ("10 replicates", "ten replicates"))),
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


CONTRACT = REPO / "scripts" / "skilllab" / "contract.py"

_STALE_TRUE = r"stays true|true by default|defaults? to true|until both hold|holds? [^.]*at true|per-unit by default"
_STALE_FALSE = r"flipped|false by default|defaults? to false|default is false|default flipped"
_STATE_TOKENS = {   # what ONE README block must carry for each state of the default
    True: ("orders_per_unit", "True", ("per-unit", "per unit"), "flip"),
    False: ("orders_per_unit", "False", "group attack-move", "flipped", "lab landing"),
}


def _orders_default() -> bool:
    """Setup.orders_per_unit's default as contract.py writes it, read at test time (no import: the doc test runs without the package path)."""
    m = re.search(r"^\s+orders_per_unit:\s*bool\s*=\s*(True|False)\b", CONTRACT.read_text(), re.M)
    assert m, "contract.py has no 'orders_per_unit: bool = ...' field line"
    return m.group(1) == "True"


def orders_default_problems(text: str, default: bool) -> list[str]:
    """README-style `text` against the code's `default`: [] when one block states exactly that default and no orders_per_unit block states
    the other. Decision 43 item 1 (TD-LAB-REV2-L7-3): the flip is conditional, so the doc follows the code, whichever it is."""
    problems = []
    if not _has_block(text, *_STATE_TOKENS[default]):
        problems.append(f"no single block carries {_STATE_TOKENS[default]} (the default is {default})")
    stale = _STALE_FALSE if default else _STALE_TRUE
    bad = [b for b in _blocks(text) if "orders_per_unit" in b.lower() and re.search(stale, b, re.I)]
    if bad:
        problems.append("a block states the other default: " + bad[0][:140])
    return problems


def test_readme_states_the_orders_per_unit_default_the_code_has():
    default = _orders_default()
    assert orders_default_problems(README.read_text(), default) == []


TRUE_TEXT = "- Orders: `Setup.orders_per_unit` is True by default, so the opening is per-unit; the default flips to group attack-move once the smoke caps zero fights."
FALSE_TEXT = "- Orders: `Setup.orders_per_unit` is False; the default was flipped to group attack-move in the lab landing, per-unit stays the opt-in."


def test_control_the_consistency_check_passes_each_state_against_its_own_text():
    assert orders_default_problems(TRUE_TEXT, True) == [] and orders_default_problems(FALSE_TEXT, False) == []


def test_mutant_a_readme_that_says_flipped_while_the_code_default_is_true_fails():
    assert orders_default_problems(FALSE_TEXT, True)


def test_mutant_a_readme_that_says_true_while_the_code_default_is_false_fails():
    assert orders_default_problems(TRUE_TEXT, False)


@pytest.mark.parametrize("wording,default", [
    ("- Orders: `Setup.orders_per_unit` defaults to True; the opening is per-unit.", False),
    ("- Orders: `Setup.orders_per_unit` default to True.", False),
    ("- Orders: `Setup.orders_per_unit` defaults to False; the opening is group attack-move.", True),
    ("- Orders: `Setup.orders_per_unit` default to False.", True),
])
def test_mutant_the_defaults_to_wordings_state_a_default(wording, default):
    """Audit of 32039a0f, item 4: 'defaults to True' / 'defaults to False' state the default as 'true by default' does; a block saying the other one than
    the code has is a problem (a README block that also carries the full tokens of the code's own state would still hold)."""
    assert any("states the other default" in p for p in orders_default_problems(wording, default))


def test_mutant_a_readme_that_says_nothing_about_the_default_fails_both_ways():
    silent = "- Orders: the opening attack-move goes out as the setup says."
    assert orders_default_problems(silent, True) and orders_default_problems(silent, False)


GROUND = REPO / "scripts" / "skilllab" / "ground"


def test_ground_files_no_longer_say_a_flyer_is_routed_by_a_straight_line():
    """Decisions 20 and 27: a flyer is routed on the 50 wu grid like a walker, only the mask differs; the straight-line walk is retired.
    ground/README.md and the scenes_ground.py comment said otherwise (decision 41 item 6; TD-LAB-REV2-FIX-docs)."""
    files = [p for p in sorted(GROUND.iterdir()) if p.is_file() and p.suffix in (".py", ".md")]
    assert any(p.name == "README.md" for p in files) and any(p.name == "scenes_ground.py" for p in files)
    hits = [(p.name, ln.strip()[:120]) for p in files for ln in p.read_text().splitlines()
            if re.search(r"straight[- ]line", ln, re.I) or re.search(r"routes? a flyer .*straight", ln, re.I)]
    assert not hits, hits


def test_ground_readme_still_describes_the_flyer_variant():
    """Positive control for the grep above: the variant is still described, only the retired routing sentence goes."""
    text = (GROUND / "README.md").read_text()
    assert "s1_slope_top_flyer" in text and "scenes.preflight" in text


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

# test_roadmap_t14_row_follows_q_lab_03 retired with ROADMAP section 3b (Westley 2026-11-02);
# parity: test_q_lab_03_has_rev2_note.
# Test-defect: retired with ROADMAP section 3b (Westley 2026-11-02); parity test_q_lab_03_has_rev2_note


def test_roadmap_highground_instrument_is_not_listed_as_live():
    stale = [ln for ln in ROADMAP.read_text().splitlines()
             if "highground.py" in ln and "deleted" not in ln.lower() and "retired" not in ln.lower()]
    assert not stale, f"ROADMAP still lists highground.py (deleted by L6) as existing: {stale[0][:120]}"


# --- harness spec: the clauses decision 15 names (5, 11, 12, 13) are rewritten; each loses 'stalemate' / the win margin ---

_CLAUSE_WORDS = {   # clause -> words it must carry (rev 2 contract: elimination only, cap a defect, FightResult and Setup fields)
    5: ("elimination", "`cap`", "`orders_per_unit`", "`Setup.point`",
        # decision 45 item 6 (TD-LAB-REV2-FIX5-docs): the no-op re-arm and the moved-displacement draft, in the re-engage sentence
        "no-op", "re-arm", "another `REENGAGE_SILENCE_TICKS`", "DRAFT-reengage-moved-wu"),
    11: ("`draw`", "`cap`", "firing_window", "weighted_unit_seconds", "weighted_window",
         "predicted_count", "predicted_type", "agreement", "states",
         "`blind_cap`", "`[]`"),       # decision 45 item 6: the field list names blind_cap; states is [] when off, not None
    # decision 39 item 2: reach_play retired by ruling 2, damage_play the labelled positive control, point for goal None,
    # per-unit orders until the decision 23 flip, the contact placement sentence stands
    12: ("`Setup.point`", "meeting", "per-unit", "`orders_per_unit`", "`reach_play`", "retired", "ruling 2",
         "labelled positive control", "Contact placement"),
    13: ("every fight", "side0", "defect"),
    14: ("bisection", "`ceiling_hit`", "`multi_flip`", "`full_scan`"),
    17: ("firing_window_0", "weighted_unit_seconds_0", "weighted_window_0", "predicted_count", "predicted_type", "agreement",
         "`knob`", "`knob_value`", "`baseline`", "`ceiling_hit`", "`prefight`", "reengage_0", "`point`", "baseline_no_fit",
         "`blind_post`"),             # decision 45 item 6: the blind_post column, and blind_post among the prefight words
    18: ("`artifact`", "SVG"),
    19: ("ceiling hit", "scan cut by baseline_no_fit"),
    20: ("`full_scan`",),
    26: ("TD-LAB-REV2-golden",),
    28: ("FINDING-speed-marks-unmet", "known red", "Westley"),
}
_CLAUSE_ABSENT = {   # clause -> stale words it must not keep
    11: ("None when it is not",),          # decision 45 item 6: states is [] when off
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


# --- LAB-REV2-FIX audit item B: the smoke's `parity` key is documented (decision 41 ruling 1; TD-LAB-REV2-FIX-parity-doc) ---

_PARITY_TOKENS = ("smoke_summary.json", "`parity`", "skipped: E0 absent")


def test_the_smoke_summary_parity_key_is_documented_in_the_readme_or_the_harness_spec():
    """One README block or one harness-spec block names smoke_summary.json, the `parity` key and its E0-absent string. The text is the
    builder's; the tokens are the interface (tests/skilllab/test_drift_fix_parity.py header)."""
    assert _has_block(README.read_text(), *_PARITY_TOKENS) or _has_block(HARNESS.read_text(), *_PARITY_TOKENS)


def test_control_the_parity_doc_check_accepts_a_block_that_has_the_tokens_and_refuses_one_that_lacks_them():
    good = "- Smoke: `smoke_summary.json` carries `parity`: the units where the composed and the engine's answers differ, or skipped: E0 absent."
    assert _has_block(good, *_PARITY_TOKENS)
    assert not _has_block(good.replace("skipped: E0 absent", "n/a"), *_PARITY_TOKENS)


# =====================================================================================================
# LAB-REV2-FIX round 5 (Architect decision 45 items 2, 3, 4, 6 and the follow-ups of 2026-10-19; decision 46). Ledger TD-LAB-REV2-FIX5-docs.
# Same method as above: presence / absence of named words in one bullet, paragraph or row; the builder writes the sentences.
# =====================================================================================================

GROUND_README = REPO / "scripts" / "skilllab" / "ground" / "README.md"


def _sentences(text: str) -> list[str]:
    flat = " ".join(text.split())
    return [x for x in re.split(r"(?<=[.;:!?])\s+", flat) if x]


def _flat(text: str) -> str:
    return " ".join(text.split())


_FIX5_README_CLAIMS = {
    # (6) README names the plays batch one actually runs. Evidence for s5_vulnerable_away among the five: the second drift audit's pre-flight probe of all 14
    # plays on layouts 81, 78 and 192 refused s5_vulnerable_away blind_post alongside s1_outrange, s2_spread_line, s4_bait and s4_do_not_chase (TD-LAB-REV2-FIX5-docs)
    # README names the plays batch one actually runs and says the five blind_post-refused plays are not in its sweep
    "batch-one-plays": (None, ("s3_layer_above", "s3_types_by_reach", "s3_dark_striker", "s1_outrange", "s2_spread_line", "s4_bait", "s4_do_not_chase",
                               "s5_vulnerable_away", "blind_post", ("not in batch one's sweep", "not in batch one’s sweep"))),
    # (6) the pre-flight list names all five words
    "preflight-five-words": (7, ("scenes.preflight", "`ok`", "`no_fit`", "`unroutable`", "`no_reach`", "`blind_post`")),
    # (6) the CSV rows bullet lists the blind_post column
    "rows-blind-post-column": (7, ("`prefight`", "`baseline_no_fit`", "`reengage_0`", "`blind_post`")),
    # (6) the orders flip is conditional on decision 43 item 1, with its status (green on the integration tree: kept as a guard)
    "orders-flip-conditional": (7, ("orders_per_unit", "conditional", "decision 43 item 1", "FINDING-group-orders-cap")),
    # (2) decision 45 item 2: the ground scene, its slope-divisor header line, the detection and its positive test are batch two's
    "ground-scene-is-batch-two": (None, ("ground scene", ("slope-divisor", "slope divisor"), "header", "detection", ("positive test", "positive control"),
                                         "batch two")),
}


@pytest.mark.parametrize("claim", sorted(_FIX5_README_CLAIMS))
def test_fix5_readme_claim(claim):
    section, tokens = _FIX5_README_CLAIMS[claim]
    text = README.read_text()
    if section is not None:
        text = _section(text, section)
    assert _has_block(text, *tokens), \
        f"README{'' if section is None else f' section {section}'} has no single bullet, paragraph or row carrying {tokens}"


def test_fix5_readme_x1_sentence_is_there_exactly():
    assert "vision cells: layout 192 only; 81 and 78 refuse the play: no_fit" in _flat(README.read_text())


def test_fix5_readme_says_reengage_is_a_stand_in_exactly():
    assert "re-engage is a lab stand-in for the engine's pending sight-engagement rule" in _flat(README.read_text())


def test_fix5_readme_firing_arc_is_thirty_not_the_old_draft():
    """Decision 46 (Westley): the firing arc is 30 degrees. No README block about the firing arc and the flanked unit still says 120."""
    blocks = [b for b in _blocks(README.read_text()) if "firing arc" in b.lower() and "flanked" in b.lower()]
    assert blocks and not [b for b in blocks if re.search(r"\b120\b", b)], "a firing-arc block still says 120"


@pytest.mark.parametrize("path", [README, GROUND_README], ids=["research-readme", "ground-readme"])
def test_fix5_no_sentence_says_the_first_batch_reports_the_inert_knobs(path):
    """Decision 45 item 3. The ground README said 'the first batch reports them inert'; the research README said 'the batch summary reports them inert'."""
    bad = [x for x in _sentences(path.read_text()) if "inert" in x.lower() and "report" in x.lower() and re.search(r"first batch|batch one", x, re.I)]
    assert not bad, bad[0][:160]


@pytest.mark.parametrize("path", [README, GROUND_README], ids=["research-readme", "ground-readme"])
def test_fix5_the_inert_knobs_are_batch_twos(path):
    assert _has_block(path.read_text(), "inert", "batch two", ("report", "reports")), f"{path.name} does not say batch two reports the inert knobs"


def test_fix5_control_the_inert_check_catches_the_old_wording():
    old = "The knobs are inert here (`INERT_KNOBS`; the first batch reports them inert): every sight line is clear."
    assert [x for x in _sentences(old) if "inert" in x.lower() and "report" in x.lower() and re.search(r"first batch|batch one", x, re.I)]
    assert _has_block("- Batch two reports the inert knobs.", "inert", "batch two", ("report", "reports"))


def test_fix5_no_test_pins_ground_scene_detection_or_a_slope_header_for_batch_one():
    """Decision 45 item 2 withdraws decision 34 item 3 for batch one: no test under tests/skilllab asserts a slope-divisor header line or a ground-scene
    detection. (The existing header test pins the opposite: no name containing 'slope'.)"""
    hits = []
    for p in sorted((REPO / "tests" / "skilllab").rglob("test_*.py")):
        for i, ln in enumerate(p.read_text().splitlines(), 1):
            if re.search(r"DRAFT-slope|DRAFT-ground-scene|detect_ground|ground_scene_ran|slope-divisor header", ln):
                hits.append(f"{p.name}:{i}")
    assert not hits, hits


# --- the harness spec ----------------------------------------------------------------------------------------------

def test_fix5_harness_clause17_lists_blind_post_as_a_column_and_as_a_prefight_word():
    c = _clause(17)
    m = re.search(r"`prefight` \(([^)]*)\)", c)
    assert m and "`blind_post`" in m.group(1), "clause 17's prefight words lack `blind_post`"
    assert c.replace(m.group(0), "").count("`blind_post`") >= 1 or "blind_post" in c.replace(m.group(0), ""), "clause 17 lists no blind_post column"


def test_fix5_harness_parity_runs_at_tick_zero_only():
    text = HARNESS.read_text()
    assert _has_block(text, "parity", "tick 0"), "the harness spec does not say parity runs at tick 0"
    assert not _has_block(text, "parity", "every sampled tick"), "the harness spec still says parity runs at every sampled tick"


def test_fix5_harness_does_not_say_fight_imports_the_retired_count_able_weighted():
    stale = [b for t in (HARNESS.read_text(), README.read_text()) for b in _blocks(t) if "fight.py" in b and "count_able_weighted" in b]
    assert not stale, stale[0][:140]


def test_fix5_control_the_harness_helpers_catch_the_old_sentences():
    old = "- L1 and L2 land together: `fight.py` still imports the retired `count_able_weighted` until L2 rewires it.\n- Parity runs at every sampled tick (`Setup.sample_every`)."
    assert _has_block(old, "fight.py", "count_able_weighted") and _has_block(old, "parity", "every sampled tick") and not _has_block(old, "parity", "tick 0")


# --- the register ---------------------------------------------------------------------------------------------------

def test_fix5_q_lab_01_is_no_longer_open():
    """Architect decision 39 item 6: Q-LAB-01 is marked superseded by Q-LAB-03 (so the register no longer lists it as open)."""
    status = _register_row("Q-LAB-01")[STATUS].strip().lower()
    assert status != "open" and status.split()[0] in ("closed", "superseded"), f"Q-LAB-01 status is {status!r}"


def test_fix5_q_lab_03_answer_lists_the_new_lab_drafts():
    row = _register_row("Q-LAB-03")
    text = " | ".join(row)
    for name in ("GUARD_RADIUS", "REENGAGE_MOVED_WU", "COARSE_STEP", "CONTROL_MAX_TICKS"):
        assert name in text, f"Q-LAB-03 row does not name {name} among the DRAFTs"
    assert "draft" in text.lower()


def test_fix5_control_register_status_helper_reads_a_superseded_row():
    assert _register_row("Q-008-04")[STATUS] == "closed"
