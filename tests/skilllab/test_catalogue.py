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


def test_rules_toml_is_the_closed_list_r1_to_r5():
    """H-025 "Rules live in rules.toml (closed list, machine-checkable): R1 ... R5"."""
    text = (CAT / "rules.toml").read_text()
    assert all(re.search(r"\b%s\b" % r, text) for r in RULE_IDS)
    assert not re.search(r"\bR(?!1\b|2\b|3\b|4\b|5\b)\d+\b", text), "rules.toml names a rule beyond R1 to R5"


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
        assert set(d) == TOP_KEYS, "%s keys: %s" % (p.name, sorted(d))
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
