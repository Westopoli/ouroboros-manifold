# Rule pins: R-001-06@9f9051, R-001-07@8f31c3
# spec: docs/stories/H-025.md (layout-catalogue-producer), DEC-lab-catalogue-mass-produced-2026-10-30
"""H-025 layout catalogue producer and review queue.

Story H-025: "Layouts are mass-produced from the recorded rules, each with a 3D shot and a predicted verdict,
and Westley approves or denies each one with feedback; only approved layouts reach the lab."

Story tests proved here:
  - `produce` writes 36 valid files for batch one and every file passes `check_layout`; every situation kind appears.
  - `--plant R2` gives a REJECT line naming R2 and no file for it (positive control).
  - `review build` writes the page listing every id.
  - `review apply` writes a verdict back into the TOML and JSON and `denied` lists it.

Positive controls (green today): the roster at scripts/skilllab/engine.py:16, the collision radius
OM_UNIT_COLLISION_RADIUS 15 at csrc/om_constants.h:581 (R2's 30 world units is two radii), and the REJECT-line pattern
the plant tests parse.

Red on the built tree: scripts/skilllab/catalogue/ (produce.py, review.py, rules.toml, presets.toml) does not exist.
Closed lists, key lists and rule texts below are copied from the story; the seed is a fixture choice, not a story number.

ROUND TWO (2026-10-31, "Round two" section of the story, after Westley denied batch one; the section is quoted in the docstrings of the tests
marked ROUND TWO below). Red on the round-one tree because: the layout has no `features`, rules.toml has no R6, `--plant R6` is refused, and
the recipes put flank_route, city and open_field on 12000 wu presets. Positive controls green today: test_control_round_two_*.
The scene half of round two (qa_state `features`, `ranges_visible`, `glyph_px`) is in tests/qa/test_layout_shot.py.
"""
import hashlib
import json
import math
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CAT = ROOT / "scripts" / "skilllab" / "catalogue"
PRODUCE = "scripts.skilllab.catalogue.produce"
REVIEW = CAT / "review.py"

# DRAFT-situation-kinds, the closed list (H-025 "Layout file").
SITUATIONS = ["chokepoint", "vantage", "cover", "objective", "staging", "transit", "flank_route", "hazard_anchor",
              "slope", "city", "trap", "open_field"]
# DRAFT-batch-one: every situation kind at pairs 16:16, 16:32 and 32:16, 36 layouts.
PAIRS = [(16, 16), (16, 32), (32, 16)]
PAIRS_ARG = "16:16,16:32,32:16"
SEED = 1  # fixture choice; the story gives no batch seed
ROLES = ["Raider", "Interceptor", "Vanguard", "Warden", "Bombard", "Bastion"]  # scripts/skilllab/engine.py:16
RULE_IDS = ["R1", "R2", "R3", "R4", "R5"]
ALL_RULE_IDS = RULE_IDS + ["R6"]  # R6 is round two
TOP_KEYS = {"id", "situation", "landscape", "seed", "predict", "predict_why", "verdict", "feedback", "side_a", "side_b"}
SIDE_KEYS = {"headcount", "units"}
UNIT_KEYS = {"role", "x", "y", "facing", "layer"}
MIN_SPACING = 30   # R2: two radii of OM_UNIT_COLLISION_RADIUS 15 (ALG-68)
HEADCOUNT_MIN, HEADCOUNT_MAX = 8, 256  # R4
REJECT_RE = re.compile(r"^REJECT (\S+) (R\d+)\b", re.M)


def _cli(out: Path, situations: str, pairs: str, seed: int = SEED, plant: str | None = None):
    cmd = [sys.executable, "-m", PRODUCE, "--out", str(out), "--situations", situations, "--pairs", pairs, "--seed", str(seed)]
    if plant:
        cmd += ["--plant", plant]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300)


def _review(*args):
    return subprocess.run([sys.executable, str(REVIEW), *map(str, args)], cwd=ROOT, capture_output=True, text=True, timeout=300)


def _layouts(d: Path):
    return sorted(d.glob("L-*.toml"))


def _load_toml(p: Path) -> dict:
    with open(p, "rb") as f:
        return tomllib.load(f)


def _all_units(layout: dict):
    return layout["side_a"]["units"] + layout["side_b"]["units"]


@pytest.fixture(scope="module")
def batch(tmp_path_factory):
    out = tmp_path_factory.mktemp("batch_one")
    r = _cli(out, "all", PAIRS_ARG)
    return out, r


def _need36(out: Path):
    files = _layouts(out)
    assert len(files) == 36, "batch one wrote %d TOML files, the story says 36" % len(files)
    return files


# ---------------------------------------------------------------- positive controls (green today)

def test_control_roster_is_the_story_roster():
    """H-025 "role (one of Raider, Interceptor, Vanguard, Warden, Bombard, Bastion, the roster at scripts/skilllab/engine.py:16)".
    CONTROL: the live roster equals the list this file tests R5 against, so a red role test is the producer's, not the list's."""
    from scripts.skilllab import engine
    assert sorted(engine._BUILTIN) == sorted(ROLES)


def test_control_collision_radius_is_fifteen():
    """H-025 R2 "no two units closer than 30 world units (two radii of OM_UNIT_COLLISION_RADIUS 15, ALG-68, csrc/om_constants.h:581)".
    CONTROL: the header still says 15, so 2 x 15 = MIN_SPACING."""
    m = re.search(r"#define\s+OM_UNIT_COLLISION_RADIUS\s+(\d+)", (ROOT / "csrc" / "om_constants.h").read_text())
    assert m and 2 * int(m.group(1)) == MIN_SPACING


def test_control_reject_line_pattern_parses_the_story_format():
    """H-025 "the producer prints `REJECT <id> <rule id> <detail>` on stderr per violation".
    CONTROL: the pattern the plant tests use matches that format and not a plain log line."""
    assert REJECT_RE.findall("REJECT L-0007 R2 units 3 and 4 are 12.0 apart\n") == [("L-0007", "R2")]
    assert not REJECT_RE.findall("wrote L-0007\n")


# ---------------------------------------------------------------- batch one

def test_producer_files_exist():
    """H-025 "Producer: Module scripts/skilllab/catalogue/produce.py ... Rules live in scripts/skilllab/catalogue/rules.toml"."""
    missing = [p for p in ("produce.py", "rules.toml", "presets.toml", "review.py") if not (CAT / p).is_file()]
    assert not missing, "missing under scripts/skilllab/catalogue/: %s" % missing


def test_rules_toml_is_the_closed_list_r1_to_r6():
    """H-025 "Rules live in rules.toml (closed list, machine-checkable): R1 ... R5"; ROUND TWO "rule R6 (new, `rules.toml`)": the list is R1 to R6.
    Re-pinned from R1 to R5 by the round-two writer (the story added R6)."""
    text = (CAT / "rules.toml").read_text()
    assert all(re.search(r"\b%s\b" % r, text) for r in ALL_RULE_IDS), "rules.toml lacks one of %s" % ALL_RULE_IDS
    assert not re.search(r"\bR(?!1\b|2\b|3\b|4\b|5\b|6\b)\d+\b", text), "rules.toml names a rule beyond R1 to R6"


def test_cli_batch_one_exits_zero_and_writes_36_layouts(batch):
    """H-025 "`produce` writes 36 valid files for batch one"; "Batch one ... every situation kind at pairs 16:16, 16:32 and 32:16, 36 layouts";
    "exits 2 if any layout was rejected, 0 otherwise"."""
    out, r = batch
    assert r.returncode == 0, "producer CLI rc=%s stderr tail: %s" % (r.returncode, r.stderr[-400:])
    assert "REJECT" not in r.stderr
    assert len(_layouts(out)) == 36, "TOML files: %d" % len(_layouts(out))
    assert len(list(out.glob("L-*.json"))) == 36


def test_every_toml_has_a_json_sibling_with_the_same_content(batch):
    """H-025 "a sibling <id>.json with the same content (Godot reads JSON)"."""
    out, _ = batch
    for p in _need36(out):
        j = p.with_suffix(".json")
        assert j.is_file(), "no JSON sibling for %s" % p.name
        assert json.loads(j.read_text()) == _load_toml(p), "%s: TOML and JSON differ" % p.name


def test_ids_are_L_numbers_upward_from_0001(batch):
    """H-025 "Path .../catalogue/<id>.toml, id L-0001 upward"; "`id` (string)"."""
    out, _ = batch
    ids = [p.stem for p in _need36(out)]
    assert all(re.fullmatch(r"L-\d{4}", i) for i in ids), ids[:5]
    assert len(set(ids)) == len(ids)
    assert "L-0001" in ids
    assert all(_load_toml(p)["id"] == p.stem for p in _need36(out))


def test_layout_key_lists(batch):
    """H-025 "Layout file ... Keys: id, situation, landscape, seed, predict, predict_why, verdict, feedback, [side_a] and [side_b] each with headcount and rows [[side_a.units]]
    with role, x, y, facing, layer"."""
    out, _ = batch
    for p in _need36(out):
        d = _load_toml(p)
        assert set(d) - {"features", "defender"} == TOP_KEYS, "%s keys: %s" % (p.name, sorted(d))  # round two adds `features` and `defender`
        for s in ("side_a", "side_b"):
            assert set(d[s]) == SIDE_KEYS, "%s %s keys: %s" % (p.name, s, sorted(d[s]))
            for u in d[s]["units"]:
                assert set(u) - {"range"} == UNIT_KEYS, "%s %s unit keys: %s" % (p.name, s, sorted(u))  # round two adds `range`


def test_layout_value_types_and_closed_values(batch):
    """H-025 "`seed` (int). `predict`: "A", "B" or "draw"; `predict_why`: one sentence. `verdict`: "" until Westley ... `feedback` (string)";
    "x, y (float, world units), facing (float, radians), layer (int, 0-based)"."""
    out, _ = batch
    presets_text = (CAT / "presets.toml").read_text()
    for p in _need36(out):
        d = _load_toml(p)
        assert isinstance(d["seed"], int) and not isinstance(d["seed"], bool)
        assert d["predict"] in ("A", "B", "draw"), p.name
        assert isinstance(d["predict_why"], str) and d["predict_why"].strip(), p.name
        assert d["verdict"] == "" and isinstance(d["feedback"], str), p.name
        assert d["landscape"] and d["landscape"] in presets_text, "%s landscape %r not in presets.toml" % (p.name, d["landscape"])
        for u in _all_units(d):
            assert isinstance(u["x"], float) and isinstance(u["y"], float) and isinstance(u["facing"], float), (p.name, u)
            assert isinstance(u["layer"], int) and not isinstance(u["layer"], bool) and u["layer"] >= 0, (p.name, u)


def test_every_situation_kind_appears_three_times_and_only_the_closed_list(batch):
    """H-025 "every situation kind appears"; "`situation`: one of the closed list DRAFT-situation-kinds: chokepoint, vantage, ... open_field"."""
    out, _ = batch
    kinds = [_load_toml(p)["situation"] for p in _need36(out)]
    assert set(kinds) == set(SITUATIONS), "situations seen: %s" % sorted(set(kinds))
    assert all(kinds.count(k) == 3 for k in SITUATIONS), {k: kinds.count(k) for k in set(kinds)}


def test_headcount_pairs_per_situation(batch):
    """H-025 "one layout per situation per pair"; "every situation kind at pairs 16:16, 16:32 and 32:16"."""
    out, _ = batch
    seen = {}
    for p in _need36(out):
        d = _load_toml(p)
        seen.setdefault(d["situation"], []).append((d["side_a"]["headcount"], d["side_b"]["headcount"]))
    for k in SITUATIONS:
        assert sorted(seen.get(k, [])) == sorted(PAIRS), "%s pairs: %s" % (k, seen.get(k))


def test_independent_rule_check_r2_r4_r5(batch):
    """H-025 R2 "no two units closer than 30 world units"; R4 "each side's headcount within 8 to 256 and equal to its unit row count";
    R5 "roles from the roster". Checked here without check_layout, so the producer is not its own oracle."""
    out, _ = batch
    for p in _need36(out):
        d = _load_toml(p)
        for s in ("side_a", "side_b"):
            side = d[s]
            assert HEADCOUNT_MIN <= side["headcount"] <= HEADCOUNT_MAX, (p.name, s)
            assert side["headcount"] == len(side["units"]), (p.name, s)
            assert all(u["role"] in ROLES for u in side["units"]), (p.name, s)
        us = _all_units(d)
        for i, a in enumerate(us):
            for b in us[i + 1:]:
                assert math.hypot(a["x"] - b["x"], a["y"] - b["y"]) >= MIN_SPACING, "%s: two units closer than %d" % (p.name, MIN_SPACING)


def test_check_layout_passes_every_produced_layout(batch):
    """H-025 "`produce` ... every file passes `check_layout`"; "`check_layout(layout, presets, rules) -> list[str]`: the rule ids violated, empty when valid"."""
    out, _ = batch
    from scripts.skilllab.catalogue.produce import check_layout
    presets = _load_toml(CAT / "presets.toml")
    rules = _load_toml(CAT / "rules.toml")
    bad = {p.name: check_layout(_load_toml(p), presets, rules) for p in _need36(out)}
    assert not {k: v for k, v in bad.items() if v}, "violations: %s" % {k: v for k, v in bad.items() if v}


def test_produce_function_returns_one_path_per_situation_per_pair_and_is_deterministic(tmp_path):
    """H-025 "`produce(situations, pairs, seed, out) -> list[Path]`: one layout per situation per pair, deterministic from the seed"."""
    from scripts.skilllab.catalogue.produce import produce
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    pa = produce(["chokepoint", "city"], [(16, 16), (32, 16)], SEED, a)
    pb = produce(["chokepoint", "city"], [(16, 16), (32, 16)], SEED, b)
    assert len(pa) == 4 and len(pb) == 4
    assert all(Path(p).exists() for p in pa)
    digest = lambda d: [hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.glob("L-*.json"))]
    assert digest(a) and digest(a) == digest(b), "same seed, different bytes"


# ---------------------------------------------------------------- rejection: check_layout on mutated layouts

def _mutations():
    def r1(d):
        d["side_a"]["units"][0]["x"] = 1.0e9
    def r2(d):
        u = d["side_a"]["units"]
        u[1]["x"], u[1]["y"] = u[0]["x"], u[0]["y"]
    def r3(d):
        d["side_a"]["units"][0]["layer"] = 10**6
    def r4(d):
        d["side_a"]["headcount"] = len(d["side_a"]["units"]) + 1
    def r5(d):
        d["side_a"]["units"][0]["role"] = "Wizard"
    return {"R1": r1, "R2": r2, "R3": r3, "R4": r4, "R5": r5}


@pytest.mark.parametrize("rule", RULE_IDS)
def test_check_layout_names_the_broken_rule(batch, rule):
    """H-025 R1 "every unit inside the preset's bounds"; R2 "no two units closer than 30 world units"; R3 "every layer below the preset's layer count";
    R4 "headcount within 8 to 256 and equal to its unit row count"; R5 "roles from the roster". A valid layout broken on one rule returns that rule id."""
    out, _ = batch
    from scripts.skilllab.catalogue.produce import check_layout
    presets = _load_toml(CAT / "presets.toml")
    rules = _load_toml(CAT / "rules.toml")
    d = _load_toml(_need36(out)[0])
    assert check_layout(d, presets, rules) == []
    _mutations()[rule](d)
    assert rule in check_layout(d, presets, rules), "%s not reported" % rule


# ---------------------------------------------------------------- --plant positive controls

@pytest.mark.parametrize("rule", RULE_IDS)
def test_plant_rule_is_rejected_with_reject_line_and_no_file(tmp_path, rule):
    """H-025 "`--plant R2` gives a REJECT line naming R2 and no file for it (positive control)"; "A layout with violations is not written; the producer
    prints `REJECT <id> <rule id> <detail>` on stderr per violation and exits 2 if any layout was rejected". Run for each of R1 to R5."""
    r = _cli(tmp_path, "chokepoint", "16:16", plant=rule)
    assert r.returncode == 2, "--plant %s: rc=%s stderr tail: %s" % (rule, r.returncode, r.stderr[-400:])
    hits = REJECT_RE.findall(r.stderr)
    assert any(rid == rule for _, rid in hits), "--plant %s: no REJECT line naming it; stderr: %s" % (rule, r.stderr[-400:])
    for lid, _ in hits:
        assert not (tmp_path / (lid + ".toml")).exists() and not (tmp_path / (lid + ".json")).exists(), "rejected %s was written" % lid
    assert len(_layouts(tmp_path)) == 1, "the one valid layout (chokepoint 16:16) should be the only file"


# ---------------------------------------------------------------- review queue

@pytest.fixture()
def small(tmp_path):
    r = _cli(tmp_path, "chokepoint,city", "16:16,32:16")
    assert r.returncode == 0, r.stderr[-400:]
    return tmp_path


def test_denied_is_empty_before_any_verdict(small):
    """H-025 "A denied layout is listed by `review.py denied --dir <catalogue>`". CONTROL for the denied test: with no verdict yet it lists no id."""
    r = _review("denied", "--dir", small)
    assert r.returncode == 0, r.stderr[-400:]
    assert not re.search(r"L-\d{4}", r.stdout)


def test_review_build_writes_a_page_listing_every_id(small):
    """H-025 "`review.py build --dir <catalogue> --out <catalogue>/review.html` writes one static page: per layout its PNG, situation, pair, predict and predict_why,
    and a verdict cell"."""
    out = small / "review.html"
    r = _review("build", "--dir", small, "--out", out)
    assert r.returncode == 0, r.stderr[-400:]
    page = out.read_text()
    for p in _layouts(small):
        d = _load_toml(p)
        assert d["id"] in page, "page lacks %s" % d["id"]
        assert d["id"] + ".png" in page, "page lacks the PNG reference %s.png" % d["id"]
        assert d["situation"] in page
        assert d["predict"] in page


def test_review_apply_writes_toml_and_json_and_denied_lists_it(small):
    """H-025 "`review.py apply --dir <catalogue> --verdicts <file>` writes `verdict` and `feedback` into each layout's TOML and JSON and prints `APPLIED <id> <verdict>`
    per row. A denied layout is listed by `review.py denied --dir <catalogue>`"; verdicts.md is a table `| id | verdict | feedback |`."""
    ids = [p.stem for p in _layouts(small)]
    assert len(ids) == 4
    rows = [(ids[0], "A", "good chokepoint"), (ids[1], "draw", "even"), (ids[2], "deny", "too cramped"), (ids[3], "B", "")]
    verdicts = small / "verdicts.md"
    verdicts.write_text("| id | verdict | feedback |\n|---|---|---|\n" + "".join("| %s | %s | %s |\n" % row for row in rows))
    r = _review("apply", "--dir", small, "--verdicts", verdicts)
    assert r.returncode == 0, r.stderr[-400:]
    for lid, v, _ in rows:
        assert re.search(r"^APPLIED %s %s\s*$" % (re.escape(lid), re.escape(v)), r.stdout, re.M), "no APPLIED line for %s %s; stdout: %s" % (lid, v, r.stdout[-400:])
    for lid, v, fb in rows:
        t, j = _load_toml(small / (lid + ".toml")), json.loads((small / (lid + ".json")).read_text())
        assert t["verdict"] == v and j["verdict"] == v, lid
        assert t["feedback"] == fb and j["feedback"] == fb, lid
    d = _review("denied", "--dir", small)
    assert d.returncode == 0, d.stderr[-400:]
    assert ids[2] in d.stdout, "denied does not list %s" % ids[2]
    assert not any(i in d.stdout for i in (ids[0], ids[1], ids[3])), "denied lists a layout that was not denied"



# ================================================================ ROUND TWO (2026-10-31)
# Pinned from the story's "Round two" and "Round two format" sections (rulings 1 to 7), word for word where a key or number is given:
#   "Layout format gains `[[features]]`, each `kind`, `x`, `y`, plus the kind's geometry"; R6 "requires every layout except `open_field` to carry its situation's
#    feature and every unit to stand off its walls by the collision radius"; "`--plant R6` ... writes a layout whose situation is not `open_field` with the
#    `features` list removed (and, as a second mutation, with the feature's `kind` swapped for another)"; "Rectangles everywhere are `{x, y, w, h}` axis-aligned
#    about their centre"; "R6's standoff: a unit's centre lies outside every rectangle of `walls`, `boxes` and `buildings` expanded by the collision radius 15
#    (ALG-68); discs and routes impose no standoff"; batch two "twelve layouts, one per situation kind, in the order of DRAFT-situation-kinds; headcount pairs
#    (A:B) ... 16:32, 24:24, 8:8, 32:32, 8:64, 64:8, 48:12, 12:48, 40:56, 64:64, 16:16, 32:16"; "`vantage`, `slope`, `flank_route` on `small_tiered`; the rest on
#    `small_flat`"; "`produce.py --batch two` ... a grid with pitch 40 wu"; "Layout file: `defender` (`"A"` or `"B"` ...; `open_field` has `defender = ""`), and
#    per unit row `range` (float, world units, from the sim roster through `scripts/skilllab/engine.py` `om_unit_profile_attack_range`)";
#    "Vantage: a unit whose centre is inside the vantage disc stands on layer `height_band`; outside, layer 0".
# Every number is a story DRAFT (Architect, 5% rule); no test here widens one. Floats are compared to 0.02 because layouts round coordinates to 0.01.

GLYPH_MIN_PX = 14  # DRAFT-glyph-min-px 14
B2_PAIRS = [(16, 32), (24, 24), (8, 8), (32, 32), (8, 64), (64, 8), (48, 12), (12, 48), (40, 56), (64, 64), (16, 16), (32, 16)]  # DRAFT-batch2-headcounts
B2_TIERED = {"vantage", "slope", "flank_route"}
COLLISION_RADIUS = 15  # OM_UNIT_COLLISION_RADIUS (control test_control_collision_radius_is_fifteen)
GRID_PITCH = 40.0  # ruling 5
TOL = 0.02


def _cli_two(out: Path, plant: str | None = None, seed: int = SEED):
    cmd = [sys.executable, "-m", PRODUCE, "--batch", "two", "--out", str(out), "--seed", str(seed)]
    if plant:
        cmd += ["--plant", plant]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=600)


@pytest.fixture(scope="module")
def batch_two(tmp_path_factory):
    out = tmp_path_factory.mktemp("batch_two")
    return out, _cli_two(out)


def _b2(batch_two_fixture):
    out, r = batch_two_fixture
    files = _layouts(out)
    assert files, "`produce.py --batch two` wrote no layout (rc=%s): %s" % (r.returncode, r.stderr[-300:].strip().replace("\n", " | "))
    return [_load_toml(p) for p in files]


def _feat(d: dict, kind: str | None = None):
    fs = [f for f in d.get("features", []) if f.get("kind") == (kind or d["situation"])]
    assert len(fs) == 1, "%s (%s): %d %s features in %s" % (d["id"], d["situation"], len(fs), kind or d["situation"], d.get("features"))
    return fs[0]


def _rects(d: dict):
    """Every wall, box and building rectangle {x, y, w, h} of the layout's features (the R6 stand-off set)."""
    return [r for f in d.get("features", []) for key in ("walls", "boxes", "buildings") for r in f.get(key, [])]


def _inside_expanded(ux, uy, r, pad) -> bool:
    return abs(ux - r["x"]) < r["w"] / 2 + pad and abs(uy - r["y"]) < r["h"] / 2 + pad


def _near(a, b) -> bool:
    return abs(a - b) <= TOL


# ---------------------------------------------------------------- ROUND TWO positive controls (green today)

def test_control_round_two_r1_to_r5_still_pass_a_layout_that_carries_the_new_keys():
    """H-025 Round two "positive control the batch-one rules R1 to R5 still pass on a round-two layout". CONTROL: a toy open_field layout with the round-two
    keys (`defender` "", per-unit `range`, no `features` key) is accepted by check_layout with no R1 to R5 violation, and a unit outside the bounds is still R1;
    green on the round-one tree, so a red R6 test below is the missing rule, not a broken fixture."""
    from scripts.skilllab.catalogue.produce import check_layout
    presets, rules = _load_toml(CAT / "presets.toml"), _load_toml(CAT / "rules.toml")
    units = lambda x0, face: [{"role": "Raider", "x": x0 + 40.0 * i, "y": 2000.0, "facing": face, "layer": 0, "range": 200.0} for i in range(8)]
    d = {"id": "L-0001", "situation": "open_field", "landscape": "small_flat", "seed": 1, "predict": "draw", "predict_why": "even", "verdict": "", "feedback": "",
         "defender": "", "side_a": {"headcount": 8, "units": units(500.0, 0.0)}, "side_b": {"headcount": 8, "units": units(3000.0, 3.1416)}}
    assert check_layout(d, presets, rules) == []
    d["side_a"]["units"][0]["x"] = 1.0e9
    assert "R1" in check_layout(d, presets, rules)


def test_control_round_two_stand_off_helper_and_roster_ranges():
    """H-025 Round two "stand off its walls by the collision radius 15". CONTROL: the rectangle test used below calls a unit 14 from a 100 by 50 rectangle's
    edge inside and 16 outside; the sim roster (engine.py, read through om_unit_profile_attack_range as ruling 6 says) gives every roster role a range above 0."""
    r = {"x": 0.0, "y": 0.0, "w": 100.0, "h": 50.0}
    assert _inside_expanded(64.0, 0.0, r, COLLISION_RADIUS) and not _inside_expanded(66.0, 0.0, r, COLLISION_RADIUS)
    assert _inside_expanded(0.0, 39.0, r, COLLISION_RADIUS) and not _inside_expanded(0.0, 41.0, r, COLLISION_RADIUS)
    from scripts.skilllab.engine import Engine
    e = Engine()
    w = e.new_world(1)
    assert all(e.type_stats(w, e.type_id(role))["attack_range"] > 0 for role in ROLES)


# ---------------------------------------------------------------- ROUND TWO: rule R6 and its plant

def test_rules_toml_carries_r6():
    """H-025 Round two "rule R6 (new, `rules.toml`) requires every layout except `open_field` to carry its situation's feature and every unit to stand off its
    walls by the collision radius": an [R6] table with a text naming the feature and the walls."""
    rules = _load_toml(CAT / "rules.toml")
    assert "R6" in rules, "rules.toml has no [R6]; tables: %s" % sorted(rules)
    text = rules["R6"].get("text", "")
    assert isinstance(text, str) and "feature" in text and "wall" in text, "R6 text does not name the feature and the walls: %r" % text


def test_check_layout_r6_names_a_missing_feature_a_swapped_kind_and_spares_open_field(batch_two):
    """H-025 Round two ruling 3 "`features` list removed (and, as a second mutation, with the feature's `kind` swapped for another)" and R6 "every layout except
    `open_field`". A valid chokepoint layout loses its `features`: R6; its feature kind is swapped for vantage: R6; the batch's open_field layout (no `features`
    key) returns no R6 (CONTROL)."""
    from scripts.skilllab.catalogue.produce import check_layout
    presets, rules = _load_toml(CAT / "presets.toml"), _load_toml(CAT / "rules.toml")
    layouts = _b2(batch_two)
    choke = next(d for d in layouts if d["situation"] == "chokepoint")
    assert check_layout(choke, presets, rules) == []
    gone = json.loads(json.dumps(choke))
    gone.pop("features", None)
    assert "R6" in check_layout(gone, presets, rules), "a chokepoint without its feature is not R6"
    swapped = json.loads(json.dumps(choke))
    for f in swapped["features"]:
        f["kind"] = "vantage"
    assert "R6" in check_layout(swapped, presets, rules), "a chokepoint carrying only a vantage-kind feature is not R6"
    openf = next(d for d in layouts if d["situation"] == "open_field")
    assert "features" not in openf and "R6" not in check_layout(openf, presets, rules)


@pytest.mark.parametrize("kind,group", [("chokepoint", "walls"), ("cover", "boxes"), ("city", "buildings"), ("trap", "walls")])
def test_check_layout_r6_stand_off_from_walls_boxes_and_buildings(batch_two, kind, group):
    """H-025 Round two ruling 4 "R6's standoff: a unit's centre lies outside every rectangle of `walls`, `boxes` and `buildings` expanded by the collision
    radius 15". In a valid layout one unit is moved to 14 wu outside the first rectangle's edge (inside the expanded rectangle): R6; to 16 wu outside: no R6
    (CONTROL, the same layout one step further out)."""
    from scripts.skilllab.catalogue.produce import check_layout
    presets, rules = _load_toml(CAT / "presets.toml"), _load_toml(CAT / "rules.toml")
    d = next(d for d in _b2(batch_two) if d["situation"] == kind)
    assert check_layout(d, presets, rules) == []
    r = _feat(d)[group][0]
    for gap, want in ((14.0, True), (16.0, False)):
        bad = json.loads(json.dumps(d))
        u = bad["side_a"]["units"][0]
        u["x"], u["y"] = r["x"] + r["w"] / 2 + gap, r["y"]
        assert ("R6" in check_layout(bad, presets, rules)) is want, "%s: unit %s wu off a %s rectangle, R6 expected %s" % (kind, gap, group, want)


def test_plant_r6_writes_no_file_and_names_r6_on_stderr(tmp_path):
    """H-025 "`--plant <rule id>` makes the producer emit one extra layout that breaks that rule on purpose (the positive control): the test asserts the REJECT
    line names it and no file for it exists", for R6 (ruling 3): exit 2, a REJECT line naming R6, no file for a rejected id, the twelve valid layouts written."""
    r = _cli_two(tmp_path, plant="R6")
    assert r.returncode == 2, "--batch two --plant R6: rc=%s stderr tail: %s" % (r.returncode, r.stderr[-400:])
    hits = REJECT_RE.findall(r.stderr)
    assert any(rid == "R6" for _, rid in hits), "no REJECT line naming R6; stderr: %s" % r.stderr[-400:]
    for lid, _ in hits:
        assert not (tmp_path / (lid + ".toml")).exists() and not (tmp_path / (lid + ".json")).exists(), "rejected %s was written" % lid
    assert len(_layouts(tmp_path)) == 12


# ---------------------------------------------------------------- ROUND TWO: batch two

def test_batch_two_writes_twelve_valid_layouts_in_situation_order(batch_two):
    """H-025 Round two ruling 5 "twelve layouts, one per situation kind, in the order of DRAFT-situation-kinds" by `produce.py --batch two`: exit 0, no REJECT,
    ids L-0001 to L-0012 in an empty directory with the situation list in DRAFT-situation-kinds order, and check_layout (R1 to R6) returns [] for each."""
    out, r = batch_two
    from scripts.skilllab.catalogue.produce import check_layout
    assert r.returncode == 0, "`--batch two` rc=%s stderr tail: %s" % (r.returncode, r.stderr[-600:])
    assert "REJECT" not in r.stderr, r.stderr[-600:]
    files = _layouts(out)
    assert [p.stem for p in files] == ["L-%04d" % i for i in range(1, 13)], [p.stem for p in files]
    layouts = [_load_toml(p) for p in files]
    assert [d["situation"] for d in layouts] == SITUATIONS
    presets, rules = _load_toml(CAT / "presets.toml"), _load_toml(CAT / "rules.toml")
    bad = {d["id"]: check_layout(d, presets, rules) for d in layouts}
    assert not {k: v for k, v in bad.items() if v}, "violations: %s" % {k: v for k, v in bad.items() if v}


def test_batch_two_headcount_pairs_and_presets(batch_two):
    """H-025 Round two ruling 5 "headcount pairs (A:B) in the same order DRAFT-batch2-headcounts: 16:32, 24:24, 8:8, 32:32, 8:64, 64:8, 48:12, 12:48, 40:56, 64:64,
    16:16, 32:16"; "`vantage`, `slope`, `flank_route` on `small_tiered`; the rest on `small_flat`" (so no large preset)."""
    layouts = _b2(batch_two)
    assert [(d["side_a"]["headcount"], d["side_b"]["headcount"]) for d in layouts] == B2_PAIRS
    assert all(d["side_a"]["headcount"] == len(d["side_a"]["units"]) and d["side_b"]["headcount"] == len(d["side_b"]["units"]) for d in layouts)
    assert {d["situation"]: d["landscape"] for d in layouts} == {k: ("small_tiered" if k in B2_TIERED else "small_flat") for k in SITUATIONS}


def test_batch_two_layout_keys(batch_two):
    """H-025 Round two ruling 6 "Layout file: `defender` ..., and per unit row `range`", ruling 4 "`open_field`: no `features` key". Every batch-two layout has the
    round-one keys plus `defender`, plus `features` unless it is open_field; every unit row has the round-one keys plus `range` (a float)."""
    for d in _b2(batch_two):
        want = TOP_KEYS | {"defender"} | (set() if d["situation"] == "open_field" else {"features"})
        assert set(d) == want, "%s (%s) keys %s, want %s" % (d["id"], d["situation"], sorted(d), sorted(want))
        for u in _all_units(d):
            assert set(u) == UNIT_KEYS | {"range"} and isinstance(u["range"], float), (d["id"], u)


def test_defender_is_a_side_letter_and_open_field_has_none(batch_two):
    """H-025 Round two ruling 6 "`defender` (`"A"` or `"B"`, the side placed on or behind the feature; `open_field` has `defender = ""`)"; ruling 5 "chokepoint gets
    16:32: the holder is the smaller side": the batch's chokepoint (16:32) has defender "A"."""
    for d in _b2(batch_two):
        if d["situation"] == "open_field":
            assert d["defender"] == "", d["id"]
        else:
            assert d["defender"] in ("A", "B"), "%s (%s) defender %r" % (d["id"], d["situation"], d.get("defender"))
        if d["situation"] == "chokepoint":
            assert d["defender"] == "A", "the chokepoint holder is the smaller side (A, 16 against 32); defender %r" % d["defender"]


def test_unit_range_is_the_sim_rosters_attack_range(batch_two):
    """H-025 Round two ruling 6 "per unit row `range` (float, world units, from the sim roster through `scripts/skilllab/engine.py`
    `om_unit_profile_attack_range`, read at produce time ...)": every unit's range equals the roster's attack_range for its role."""
    from scripts.skilllab.engine import Engine
    e = Engine()
    w = e.new_world(1)
    want = {role: e.type_stats(w, e.type_id(role))["attack_range"] for role in ROLES}
    for d in _b2(batch_two):
        for u in _all_units(d):
            assert abs(u["range"] - want[u["role"]]) < 1e-6, "%s: %s range %r, roster says %r" % (d["id"], u["role"], u["range"], want[u["role"]])


def test_batch_two_sides_are_grids_of_pitch_forty(batch_two):
    """H-025 Round two ruling 5 "a side's block is a grid with pitch 40 wu": within a side no two units are closer than 40 and every unit has a same-side
    neighbour at exactly 40 (to rounding)."""
    for d in _b2(batch_two):
        for s in ("side_a", "side_b"):
            us = d[s]["units"]
            for i, a in enumerate(us):
                near = min(math.hypot(a["x"] - b["x"], a["y"] - b["y"]) for j, b in enumerate(us) if j != i)
                assert abs(near - GRID_PITCH) <= 0.05, "%s %s unit %d: nearest same-side unit is %.2f wu away, the grid pitch is 40" % (d["id"], s, i, near)


def test_features_in_toml_and_json_are_the_same(batch_two):
    """H-025 "a sibling <id>.json with the same content (Godot reads JSON)", with the Round two `[[features]]` tables and nested rectangle and point lists in both."""
    out, _ = batch_two
    files = _layouts(out)
    assert files
    for p in files:
        assert json.loads(p.with_suffix(".json").read_text()) == _load_toml(p), "%s: TOML and JSON differ" % p.name
    assert any(_load_toml(p).get("features") for p in files), "no layout carries a features table"


def test_every_feature_has_kind_x_y_and_the_situations_feature_is_present(batch_two):
    """H-025 Round two ruling 4 "Every entry has `kind`, `x`, `y` (centre, floats, world units)"; R6 "carry its situation's feature". Each non-open_field layout has
    exactly one feature of its situation's kind; centre inside the preset's bounds."""
    presets = _load_toml(CAT / "presets.toml")
    for d in _b2(batch_two):
        if d["situation"] == "open_field":
            continue
        assert isinstance(d.get("features"), list) and d["features"], "%s (%s) has no `features` list" % (d["id"], d["situation"])
        for f in d["features"]:
            assert {"kind", "x", "y"} <= set(f) and isinstance(f["x"], float) and isinstance(f["y"], float), (d["id"], f)
            p = presets[d["landscape"]]
            assert 0 <= f["x"] <= p["width"] and 0 <= f["y"] <= p["height"], (d["id"], f)
        _feat(d)


def _geometry_chokepoint(f):
    assert f["gap"] == 200 and f["radius"] == 600
    assert len(f["walls"]) == 2 and all(w["w"] == 200 and w["h"] == 500 for w in f["walls"]), f["walls"]
    centres = sorted((w["x"], w["y"]) for w in f["walls"])
    want = sorted([(f["x"], f["y"] - 350.0), (f["x"], f["y"] + 350.0)])  # y +- (gap/2 + h/2)
    assert all(_near(a[0], b[0]) and _near(a[1], b[1]) for a, b in zip(centres, want)), "wall centres %s, want %s" % (centres, want)


def _geometry_vantage(f):
    assert f["radius"] == 700 and f["height_band"] == 1


def _geometry_cover(f):
    assert 2 <= len(f["boxes"]) <= 4, "%d boxes" % len(f["boxes"])
    assert all(b["w"] == 120 and b["h"] == 60 for b in f["boxes"]), f["boxes"]
    assert all(math.hypot(b["x"] - f["x"], b["y"] - f["y"]) <= 300 + TOL for b in f["boxes"]), "a box centre is beyond DRAFT-cover-spread 300"


def _geometry_objective(f):
    assert f["radius"] == 300


def _geometry_staging(f):
    assert f["size"] == 600


def _geometry_transit(f):
    pts = f["points"]
    assert 2 <= len(pts) <= 4 and all(isinstance(p, list) and len(p) == 2 for p in pts), pts
    assert _near(pts[0][0], f["x"]) and _near(pts[0][1], f["y"]), "the route must start at the feature centre"
    assert set(f["dest"]) == {"x", "y"} and _near(f["dest"]["x"], pts[-1][0]) and _near(f["dest"]["y"], pts[-1][1]), "dest %s is not the last point %s" % (f["dest"], pts[-1])


def _geometry_flank_route(f):
    pts = f["points"]
    assert 3 <= len(pts) <= 5 and all(isinstance(p, list) and len(p) == 2 for p in pts), pts


def _geometry_hazard_anchor(f):
    assert f["radius"] == 500


def _geometry_slope(f):
    assert f["length"] == 600 and f["width"] == 200 and f["from_band"] == 0 and f["to_band"] == 1
    assert isinstance(f["heading"], float)


def _geometry_city(f):
    assert f["radius"] == 400 and len(f["buildings"]) == 9
    assert all(b["w"] == 100 and b["h"] == 100 for b in f["buildings"]), f["buildings"]
    want = sorted((f["x"] + i * 250.0, f["y"] + j * 250.0) for i in (-1, 0, 1) for j in (-1, 0, 1))  # DRAFT-city-pitch 250
    got = sorted((b["x"], b["y"]) for b in f["buildings"])
    assert all(_near(a[0], b[0]) and _near(a[1], b[1]) for a, b in zip(got, want)), "building centres %s, want %s" % (got, want)


def _geometry_trap(f):
    walls, m = f["walls"], f["mouth"]
    assert len(walls) == 3 and isinstance(m, float)
    q = m / (math.pi / 2)
    assert abs(q - round(q)) < 1e-3, "mouth %r is not a multiple of pi/2, so the rectangles cannot stay axis-aligned" % m
    dims = sorted(tuple(sorted((w["w"], w["h"]))) for w in walls)
    assert dims == [(200, 800), (200, 800), (200, 1000)], "wall sizes %s: want two sides 200 by 800 and a back wall 1000 by 200" % dims
    back = next(w for w in walls if tuple(sorted((w["w"], w["h"]))) == (200, 1000))
    assert _near(back["x"], f["x"] - 500 * math.cos(m)) and _near(back["y"], f["y"] - 500 * math.sin(m)), "back wall %s is not 500 wu behind the mouth heading %s" % (back, m)
    sides = sorted((w["x"], w["y"]) for w in walls if w is not back)
    want = sorted([(f["x"] + 400 * math.sin(m), f["y"] - 400 * math.cos(m)), (f["x"] - 400 * math.sin(m), f["y"] + 400 * math.cos(m))])
    assert all(_near(a[0], b[0]) and _near(a[1], b[1]) for a, b in zip(sides, want)), "side walls %s, want %s" % (sides, want)


GEOMETRY = {k: v for k, v in list(globals().items()) if k.startswith("_geometry_")}


@pytest.mark.parametrize("kind", [k for k in SITUATIONS if k != "open_field"])
def test_feature_geometry_per_kind(batch_two, kind):
    """H-025 Round two ruling 4, the per-kind schema and numbers: chokepoint `gap` 200 `radius` 600 `walls` two 200 by 500 at (x, y +- 350); vantage `radius` 700
    `height_band` 1; cover `boxes` two to four 120 by 60 within 300 of the centre; objective `radius` 300; staging `size` 600; transit `points` two to four from the
    centre and `dest` = the last point; flank_route `points` three to five; hazard_anchor `radius` 500; slope `length` 600 `width` 200 `heading` `from_band` 0
    `to_band` 1; city `radius` 400 and nine 100 by 100 `buildings` at pitch 250; trap `walls` three (two 200 by 800 sides at 400, a 1000 by 200 back wall 500 behind)
    and `mouth`."""
    d = next(d for d in _b2(batch_two) if d["situation"] == kind)
    GEOMETRY["_geometry_" + kind](_feat(d))


def test_units_stand_off_every_wall_box_and_building(batch_two):
    """H-025 Round two ruling 4 R6 stand-off, checked here without check_layout so the producer is not its own oracle: no unit's centre inside any wall, box or
    building rectangle expanded by 15; at least one rectangle exists in the batch (so the check can fail)."""
    layouts = _b2(batch_two)
    assert sum(len(_rects(d)) for d in layouts) > 0, "no layout carries a wall, box or building rectangle"
    for d in layouts:
        for u in _all_units(d):
            for r in _rects(d):
                assert not _inside_expanded(u["x"], u["y"], r, COLLISION_RADIUS), "%s (%s): unit at (%s, %s) is inside rectangle %s plus 15" % (d["id"], d["situation"], u["x"], u["y"], r)


def test_predict_why_names_the_feature(batch_two):
    """H-025 Round two "writes `predict_why` naming the feature": for every layout with a feature, predict_why contains the feature kind, as written or with its
    underscore as a space, or the kind's first word (flank, hazard)."""
    for d in _b2(batch_two):
        if d["situation"] == "open_field":
            continue
        kind = d["situation"]
        names = {kind, kind.replace("_", " "), kind.split("_")[0]}
        assert any(n in d["predict_why"].lower() for n in names), "%s: predict_why %r does not name the %s feature" % (d["id"], d["predict_why"], kind)


def test_terrain_tiers_and_the_vantage_layer_rule(batch_two):
    """H-025 Round two "a landscape's `layers` is the number of height bands ... a walker has exactly one layer with ground under it at any point" and ruling 2
    "a unit whose centre is inside the vantage disc stands on layer `height_band`; outside, layer 0". Vantage and slope sit on a preset with more than one band; a
    one-band preset has every unit on layer 0; in the vantage layout inside the disc means layer `height_band`, outside means layer 0."""
    presets = _load_toml(CAT / "presets.toml")
    for d in _b2(batch_two):
        layers = presets[d["landscape"]]["layers"]
        units = _all_units(d)
        if d["situation"] in ("vantage", "slope"):
            assert layers >= 2, "%s: a %s on %s, which has %d height band" % (d["id"], d["situation"], d["landscape"], layers)
        if layers == 1:
            assert all(u["layer"] == 0 for u in units), "%s: a unit above layer 0 on a one-band preset" % d["id"]
        if d["situation"] == "vantage":
            f = _feat(d)
            for u in units:
                inside = math.hypot(u["x"] - f["x"], u["y"] - f["y"]) < f["radius"]
                want = f["height_band"] if inside else 0
                assert u["layer"] == want, "%s: unit at (%s, %s) is %s the vantage disc but on layer %s, want %s" % (
                    d["id"], u["x"], u["y"], "inside" if inside else "outside", u["layer"], want)


def test_control_round_two_geometry_checks_accept_a_feature_built_from_the_ruling():
    """H-025 Round two ruling 4. CONTROL (green today): features written by hand straight from the ruling's schema pass the per-kind checks used above, the trap
    both as written (mouth pi/2) and rotated a quarter turn (mouth 0, sizes swapped), and a wrong number fails them; so a red per-kind test is the producer's."""
    x, y = 2000.0, 2000.0
    rect = lambda cx, cy, w, h: {"x": cx, "y": cy, "w": w, "h": h}
    good = {
        "chokepoint": {"gap": 200, "radius": 600, "walls": [rect(x, y - 350, 200, 500), rect(x, y + 350, 200, 500)]},
        "vantage": {"radius": 700, "height_band": 1},
        "cover": {"boxes": [rect(x + 100, y, 120, 60), rect(x - 100, y, 120, 60)]},
        "objective": {"radius": 300}, "staging": {"size": 600},
        "transit": {"points": [[x, y], [x + 300.0, y + 100.0]], "dest": {"x": x + 300.0, "y": y + 100.0}},
        "flank_route": {"points": [[x, y], [x + 1.0, y + 2.0], [x + 3.0, y + 4.0]]},
        "hazard_anchor": {"radius": 500},
        "slope": {"length": 600, "width": 200, "heading": 0.5, "from_band": 0, "to_band": 1},
        "city": {"radius": 400, "buildings": [rect(x + i * 250.0, y + j * 250.0, 100, 100) for i in (-1, 0, 1) for j in (-1, 0, 1)]},
        "trap": {"mouth": math.pi / 2, "walls": [rect(x - 400, y, 200, 800), rect(x + 400, y, 200, 800), rect(x, y - 500, 1000, 200)]},
    }
    for kind, g in good.items():
        GEOMETRY["_geometry_" + kind](dict(g, kind=kind, x=x, y=y))
    GEOMETRY["_geometry_trap"](dict(kind="trap", x=x, y=y, mouth=0.0, walls=[rect(x, y - 400, 800, 200), rect(x, y + 400, 800, 200), rect(x - 500, y, 200, 1000)]))
    with pytest.raises(AssertionError):
        GEOMETRY["_geometry_objective"](dict(good["objective"], radius=301))
