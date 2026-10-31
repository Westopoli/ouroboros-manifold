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
RULE_IDS = ["R1", "R2", "R3", "R4", "R5", "R6"]  # R6 is round two
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
    assert all(re.search(r"\b%s\b" % r, text) for r in RULE_IDS), "rules.toml lacks one of %s" % RULE_IDS
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
        assert set(d) - {"features"} == TOP_KEYS, "%s keys: %s" % (p.name, sorted(d))  # round two adds the optional `features`
        for s in ("side_a", "side_b"):
            assert set(d[s]) == SIDE_KEYS, "%s %s keys: %s" % (p.name, s, sorted(d[s]))
            for u in d[s]["units"]:
                assert set(u) == UNIT_KEYS, "%s %s unit keys: %s" % (p.name, s, sorted(u))


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
    def r6(d):  # ROUND TWO: the layout is a chokepoint (the first of the batch) and loses its feature
        d.pop("features", None)
    return {"R1": r1, "R2": r2, "R3": r3, "R4": r4, "R5": r5, "R6": r6}


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
# Quoted from the story's "Round two" section, word for word where a number or a key is pinned:
#   "Layout format gains `[[features]]`, each `kind`, `x`, `y`, plus the kind's geometry, from the H-023 stage's values (DRAFT until H-023 locks them):
#    `chokepoint` (two walls with `gap` 200 wu, `radius` 600), `vantage` (a raised disc `radius` 700, `height_band` 1), `cover` (two to four obstacle boxes
#    `w` 120 `h` 60), `objective` (capture ring `radius` 300), `staging` (a marked square), `transit` (a route polyline and a destination marker),
#    `flank_route` (a polyline), `hazard_anchor` (a disc `radius` 500, drawn as a hazard), `slope` (a band 600 wu long joining two height bands, R-001-06),
#    `city` (footprint disc `radius` 400 with a 3 by 3 building grid), `trap` (a pocket of walls with one mouth), `open_field` (no feature)."
#   "writes `predict_why` naming the feature, and rule R6 (new, `rules.toml`) requires every layout except `open_field` to carry its situation's feature
#    and every unit to stand off its walls by the collision radius."
#   "Batch two is 12 pictures again, one per situation kind, on `small_flat` and `small_tiered` only, with headcounts spread 8 to 64 a side."
# The story gives no key for a feature's other geometry (wall list, polyline points, destination, building grid, box list), so those are searched for
# anywhere inside the feature entry (nested dicts and lists), never by an invented key name.

GLYPH_MIN_PX = 14  # DRAFT-glyph-min-px 14 (story, Round two)
R2_PAIRS = [(8, 8), (64, 64), (8, 64), (64, 8)]  # fixture choice inside the story's "headcounts spread 8 to 64 a side"; the story gives no batch-two pair list
R2_PAIRS_ARG = "8:8,64:64,8:64,64:8"
R2_PRESETS = {"small_flat", "small_tiered"}
# kind -> {key: number} the story pins (backticked keys only)
KIND_NUMBERS = {"chokepoint": {"gap": 200, "radius": 600}, "vantage": {"radius": 700, "height_band": 1}, "objective": {"radius": 300},
                "hazard_anchor": {"radius": 500}, "city": {"radius": 400}}
COLLISION_RADIUS = 15  # OM_UNIT_COLLISION_RADIUS, csrc/om_constants.h:581 (the standoff R6 names)


def _walk(node):
    """Every dict and list reachable inside node, node first."""
    yield node
    if isinstance(node, dict):
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def _values_of(feature: dict, key: str):
    return [d[key] for d in _walk(feature) if isinstance(d, dict) and key in d]


def _feats(layout: dict, kind: str):
    return [f for f in layout.get("features", []) if f.get("kind") == kind]


def _glyph_below_min(px) -> bool:
    return not (isinstance(px, (int, float)) and px >= GLYPH_MIN_PX)


@pytest.fixture(scope="module")
def batch_two(tmp_path_factory):
    out = tmp_path_factory.mktemp("batch_two")
    r = _cli(out, "all", R2_PAIRS_ARG)
    return out, r


def _r2_layouts(out: Path):
    """The layouts the producer wrote for the fixture pairs (a pair it rejected is missing here and is reported by the feasibility test below)."""
    files = _layouts(out)
    assert files, "the producer wrote no round-two layout"
    return [_load_toml(p) for p in files]


# ---------------------------------------------------------------- ROUND TWO positive controls (green today)

def test_control_round_two_r1_to_r5_still_pass_a_layout_that_carries_features(tmp_path):
    """H-025 Round two "positive control the batch-one rules R1 to R5 still pass on a round-two layout". CONTROL: a toy open_field layout carrying an
    empty `features` list is accepted by check_layout with no R1 to R5 violation, and a unit outside the bounds is still R1; green on the round-one tree,
    so a red R6 test below is the missing rule, not a broken fixture."""
    from scripts.skilllab.catalogue.produce import check_layout
    presets, rules = _load_toml(CAT / "presets.toml"), _load_toml(CAT / "rules.toml")
    units = lambda x0, face: [{"role": "Raider", "x": x0 + 40.0 * i, "y": 2000.0, "facing": face, "layer": 0} for i in range(8)]
    d = {"id": "L-0001", "situation": "open_field", "landscape": "small_flat", "seed": 1, "predict": "draw", "predict_why": "even", "verdict": "", "feedback": "",
         "features": [], "side_a": {"headcount": 8, "units": units(500.0, 0.0)}, "side_b": {"headcount": 8, "units": units(3000.0, 3.1416)}}
    assert check_layout(d, presets, rules) == []
    d["side_a"]["units"][0]["x"] = 1.0e9
    assert "R1" in check_layout(d, presets, rules)


def test_control_round_two_glyph_detector_and_walker():
    """H-025 Round two "DRAFT-glyph-min-px 14". CONTROL: the detector used below rejects 13 and None and accepts 14; the nested-key walker finds a key
    inside a nested feature."""
    assert _glyph_below_min(13) and _glyph_below_min(None) and not _glyph_below_min(14) and not _glyph_below_min(14.5)
    assert _values_of({"kind": "cover", "boxes": [{"w": 120, "h": 60}, {"w": 120, "h": 60}]}, "w") == [120, 120]


# ---------------------------------------------------------------- ROUND TWO: rule R6

def test_rules_toml_carries_r6_with_the_collision_radius_standoff():
    """H-025 Round two "rule R6 (new, `rules.toml`) requires every layout except `open_field` to carry its situation's feature and every unit to stand off
    its walls by the collision radius". rules.toml has an [R6] table with a text; the stand-off number is the collision radius 15 (control above: header is 15)."""
    rules = _load_toml(CAT / "rules.toml")
    assert "R6" in rules, "rules.toml has no [R6]; tables: %s" % sorted(rules)
    assert isinstance(rules["R6"].get("text"), str) and rules["R6"]["text"].strip()
    assert "feature" in rules["R6"]["text"] and "wall" in rules["R6"]["text"], "R6 text does not name the feature and the walls: %r" % rules["R6"]["text"]


def test_check_layout_r6_names_a_missing_feature_and_a_wrong_feature(batch_two):
    """H-025 Round two "rule R6 ... requires every layout except `open_field` to carry its situation's feature". A valid chokepoint layout that loses its
    `features` returns R6; one whose feature is another kind returns R6; an open_field layout with no feature returns no R6 (CONTROL)."""
    out, _ = batch_two
    from scripts.skilllab.catalogue.produce import check_layout
    presets, rules = _load_toml(CAT / "presets.toml"), _load_toml(CAT / "rules.toml")
    layouts = _r2_layouts(out)
    choke = next(d for d in layouts if d["situation"] == "chokepoint")
    assert check_layout(choke, presets, rules) == []
    gone = dict(choke)
    gone.pop("features", None)
    assert "R6" in check_layout(gone, presets, rules), "a chokepoint without its feature is not R6"
    wrong = dict(choke, features=[dict(f, kind="vantage") for f in choke.get("features", [])] or [{"kind": "vantage", "x": 2000.0, "y": 2000.0}])
    assert "R6" in check_layout(wrong, presets, rules), "a chokepoint carrying only a vantage feature is not R6"
    openf = next(d for d in layouts if d["situation"] == "open_field")
    bare = dict(openf)
    bare.pop("features", None)
    assert "R6" not in check_layout(bare, presets, rules), "open_field must not need a feature"


def test_check_layout_r6_names_a_unit_standing_on_a_cover_box(batch_two):
    """H-025 Round two "every unit to stand off its walls by the collision radius". A cover layout (valid) with one unit moved onto an obstacle box's
    (x, y) returns R6; works whether the story's box x, y is its centre or its corner (a unit there is inside or on the box either way)."""
    out, _ = batch_two
    from scripts.skilllab.catalogue.produce import check_layout
    presets, rules = _load_toml(CAT / "presets.toml"), _load_toml(CAT / "rules.toml")
    cover = next(d for d in _r2_layouts(out) if d["situation"] == "cover")
    assert check_layout(cover, presets, rules) == []
    feats = _feats(cover, "cover")
    boxes = [(b.get("x", f["x"]), b.get("y", f["y"])) for f in feats for b in _walk(f) if isinstance(b, dict) and "w" in b and "h" in b]
    assert boxes, "the cover layout carries no obstacle box (an entry with w and h): %s" % feats
    bad = json.loads(json.dumps(cover))
    bad["side_a"]["units"][0]["x"], bad["side_a"]["units"][0]["y"] = float(boxes[0][0]), float(boxes[0][1])
    assert "R6" in check_layout(bad, presets, rules), "a unit on an obstacle box is not R6"


@pytest.mark.parametrize("rule", ["R6"])
def test_plant_r6_is_rejected_with_reject_line_and_no_file(tmp_path, rule):
    """H-025 "`--plant <rule id>` makes the producer emit one extra layout that breaks that rule on purpose (the positive control): the test asserts the
    REJECT line names it and no file for it exists", applied to the new rule R6 (Round two: "every detector ships a positive control")."""
    r = _cli(tmp_path, "chokepoint", "16:16", plant=rule)
    assert r.returncode == 2, "--plant %s: rc=%s stderr tail: %s" % (rule, r.returncode, r.stderr[-400:])
    hits = REJECT_RE.findall(r.stderr)
    assert any(rid == rule for _, rid in hits), "--plant %s: no REJECT line naming it; stderr: %s" % (rule, r.stderr[-400:])
    for lid, _ in hits:
        assert not (tmp_path / (lid + ".toml")).exists() and not (tmp_path / (lid + ".json")).exists(), "rejected %s was written" % lid
    assert len(_layouts(tmp_path)) == 1


# ---------------------------------------------------------------- ROUND TWO: the layout carries landscape geometry

def test_every_round_two_layout_exits_zero_and_passes_check_layout(batch_two):
    """H-025 Round two "headcounts spread 8 to 64 a side"; "positive control the batch-one rules R1 to R5 still pass on a round-two layout". The producer
    writes every situation at pairs 8:8, 64:64, 8:64 and 64:8 with exit 0, no REJECT, and check_layout (R1 to R6) returns [] for each."""
    out, r = batch_two
    from scripts.skilllab.catalogue.produce import check_layout
    assert r.returncode == 0, "producer CLI rc=%s stderr tail: %s" % (r.returncode, r.stderr[-600:])
    assert "REJECT" not in r.stderr, r.stderr[-600:]
    assert len(_layouts(out)) == len(SITUATIONS) * len(R2_PAIRS), "wrote %d TOML files, want %d" % (len(_layouts(out)), len(SITUATIONS) * len(R2_PAIRS))
    presets, rules = _load_toml(CAT / "presets.toml"), _load_toml(CAT / "rules.toml")
    bad = {d["id"]: check_layout(d, presets, rules) for d in _r2_layouts(out)}
    assert not {k: v for k, v in bad.items() if v}, "violations: %s" % {k: v for k, v in bad.items() if v}


def test_headcounts_stay_inside_eight_to_sixty_four(batch_two):
    """H-025 Round two "headcounts spread 8 to 64 a side"; every layout of the fixture pairs has the pair's headcounts and as many unit rows."""
    out, _ = batch_two
    seen = {}
    for d in _r2_layouts(out):
        assert 8 <= d["side_a"]["headcount"] <= 64 and 8 <= d["side_b"]["headcount"] <= 64
        assert d["side_a"]["headcount"] == len(d["side_a"]["units"]) and d["side_b"]["headcount"] == len(d["side_b"]["units"])
        seen.setdefault(d["situation"], []).append((d["side_a"]["headcount"], d["side_b"]["headcount"]))
    assert set(seen) <= set(SITUATIONS)
    assert all(set(v) <= set(R2_PAIRS) for v in seen.values()), seen


def test_batch_two_lands_on_small_flat_and_small_tiered_only(batch_two):
    """H-025 Round two "Batch two is 12 pictures again, one per situation kind, on `small_flat` and `small_tiered` only"; "presets.toml (no change to
    bounds)": the four presets still exist unchanged, and no layout uses a large preset."""
    out, _ = batch_two
    presets = _load_toml(CAT / "presets.toml")
    assert presets["small_flat"]["width"] == presets["small_tiered"]["width"] == 4000 and presets["large_flat"]["width"] == 12000
    used = {(d["situation"], d["landscape"]) for d in _r2_layouts(out)}
    assert {l for _, l in used} <= R2_PRESETS, "layouts on presets outside small_flat/small_tiered: %s" % sorted(u for u in used if u[1] not in R2_PRESETS)


def test_every_situation_except_open_field_carries_its_feature(batch_two):
    """H-025 Round two "Layout format gains `[[features]]`, each `kind`, `x`, `y`, plus the kind's geometry"; "(`open_field` (no feature))". Every layout of
    a situation other than open_field has a `features` list holding an entry whose kind is the situation, each entry with kind (str), x and y (numbers) inside
    the preset's bounds; open_field has none."""
    out, _ = batch_two
    presets = _load_toml(CAT / "presets.toml")
    for d in _r2_layouts(out):
        feats = d.get("features")
        if d["situation"] == "open_field":
            assert not feats, "%s: open_field carries a feature: %s" % (d["id"], feats)
            continue
        assert isinstance(feats, list) and feats, "%s (%s) has no `features` list; keys %s" % (d["id"], d["situation"], sorted(d))
        assert all({"kind", "x", "y"} <= set(f) for f in feats), "%s: a feature lacks kind, x or y: %s" % (d["id"], feats[:2])
        assert d["situation"] in {f["kind"] for f in feats}, "%s: no %s feature among %s" % (d["id"], d["situation"], [f["kind"] for f in feats])
        p = presets[d["landscape"]]
        for f in feats:
            assert isinstance(f["x"], (int, float)) and isinstance(f["y"], (int, float)) and f["kind"] in SITUATIONS
            assert 0 <= f["x"] <= p["width"] and 0 <= f["y"] <= p["height"], "%s: feature %s outside the preset" % (d["id"], f)


def test_features_in_toml_and_json_are_the_same(batch_two):
    """H-025 "a sibling <id>.json with the same content (Godot reads JSON)", with the Round two `[[features]]` table in both files."""
    out, _ = batch_two
    for p in _layouts(out):
        assert json.loads(p.with_suffix(".json").read_text()) == _load_toml(p), "%s: TOML and JSON differ" % p.name
    assert any(_load_toml(p).get("features") for p in _layouts(out)), "no layout carries a features table"


def test_feature_geometry_numbers_the_story_pins(batch_two):
    """H-025 Round two geometry, the backticked keys and numbers: chokepoint `gap` 200 `radius` 600; vantage `radius` 700 `height_band` 1; cover boxes `w` 120
    `h` 60, two to four of them; objective `radius` 300; hazard_anchor `radius` 500; city `radius` 400. DRAFT until H-023 locks them."""
    out, _ = batch_two
    for d in _r2_layouts(out):
        k = d["situation"]
        feats = _feats(d, k)
        if k in KIND_NUMBERS:
            assert feats, "%s: no %s feature" % (d["id"], k)
            for key, want in KIND_NUMBERS[k].items():
                got = [v for f in feats for v in _values_of(f, key)]
                assert got and all(v == want for v in got), "%s (%s): `%s` is %s, the story says %s" % (d["id"], k, key, got, want)
        if k == "cover":
            boxes = [b for f in feats for b in _walk(f) if isinstance(b, dict) and "w" in b and "h" in b]
            assert 2 <= len(boxes) <= 4, "%s: %d obstacle boxes, the story says two to four" % (d["id"], len(boxes))
            assert all(b["w"] == 120 and b["h"] == 60 for b in boxes), "%s: box sizes %s, the story says w 120 h 60" % (d["id"], [(b["w"], b["h"]) for b in boxes])


def test_polyline_features_carry_a_route_of_points(batch_two):
    """H-025 Round two "`transit` (a route polyline and a destination marker)", "`flank_route` (a polyline)": the feature holds a list of at least two points
    (each a [x, y] pair or a dict with x and y). Key names are the builder's; the story gives none."""
    out, _ = batch_two
    point = lambda p: (isinstance(p, dict) and {"x", "y"} <= set(p)) or (isinstance(p, list) and len(p) == 2 and all(isinstance(v, (int, float)) for v in p))
    for d in _r2_layouts(out):
        if d["situation"] in ("transit", "flank_route"):
            feats = _feats(d, d["situation"])
            assert feats, "%s: no %s feature" % (d["id"], d["situation"])
            lines = [n for f in feats for n in _walk(f) if isinstance(n, list) and len(n) >= 2 and all(point(p) for p in n)]
            assert lines, "%s (%s): no polyline of two or more points in %s" % (d["id"], d["situation"], feats)


def test_city_carries_a_three_by_three_building_grid(batch_two):
    """H-025 Round two "`city` (footprint disc `radius` 400 with a 3 by 3 building grid)": the city feature holds nine buildings (a list of nine entries) or a
    grid size of 3 (`grid` as 3 or [3, 3]); key names are the builder's."""
    out, _ = batch_two
    for d in _r2_layouts(out):
        if d["situation"] == "city":
            feats = _feats(d, "city")
            assert feats, "%s: no city feature" % d["id"]
            nine = any(isinstance(n, list) and len(n) == 9 for f in feats for n in _walk(f))
            grid = any(k.lower().startswith("grid") and v in (3, [3, 3]) for f in feats for n in _walk(f) if isinstance(n, dict) for k, v in n.items())
            assert nine or grid, "%s: city feature has no nine buildings and no 3 by 3 grid: %s" % (d["id"], feats)


def test_predict_why_names_the_feature(batch_two):
    """H-025 Round two "writes `predict_why` naming the feature": for every layout with a feature, predict_why contains the feature kind, as written or with
    its underscore as a space, or the kind's first word (flank, hazard)."""
    out, _ = batch_two
    for d in _r2_layouts(out):
        if d["situation"] == "open_field":
            continue
        kind = d["situation"]
        names = {kind, kind.replace("_", " "), kind.split("_")[0]}
        why = d["predict_why"].lower()
        assert any(n in why for n in names), "%s: predict_why %r does not name the %s feature" % (d["id"], d["predict_why"], kind)


# ---------------------------------------------------------------- ROUND TWO: terrain tiers, not stacked planes

def test_raised_features_sit_on_a_tiered_preset_and_the_vantage_units_stand_on_its_band(batch_two):
    """H-025 Round two "a landscape's `layers` is the number of height bands on the land, drawn as terrain tiers joined by slopes (R-001-06, R-001-07: a walker
    has exactly one layer with ground under it at any point)". A vantage (`height_band` 1) and a slope (joins two height bands) need a preset with more than
    one band; every vantage unit standing inside the disc is on layer `height_band`, every unit outside it on layer 0; a flat preset has one band, so its
    units are all on layer 0."""
    out, _ = batch_two
    presets = _load_toml(CAT / "presets.toml")
    for d in _r2_layouts(out):
        layers = presets[d["landscape"]]["layers"]
        units = _all_units(d)
        if d["situation"] in ("vantage", "slope"):
            assert layers >= 2, "%s: a %s on %s, which has %d height band" % (d["id"], d["situation"], d["landscape"], layers)
        if layers == 1:
            assert all(u["layer"] == 0 for u in units), "%s: layer above 0 on a one-band preset" % d["id"]
        if d["situation"] == "vantage":
            assert _feats(d, "vantage"), "%s: no vantage feature" % d["id"]
            f = _feats(d, "vantage")[0]
            for u in units:
                inside = math.hypot(u["x"] - f["x"], u["y"] - f["y"]) < f["radius"]
                want = f["height_band"] if inside else 0
                assert u["layer"] == want, "%s: unit at (%s, %s) is %s the vantage disc but on layer %s, want %s" % (
                    d["id"], u["x"], u["y"], "inside" if inside else "outside", u["layer"], want)
