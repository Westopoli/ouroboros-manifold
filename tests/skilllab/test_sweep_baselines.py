# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decisions 25 and 26 (baseline variants, pre-flight coverage, baseline_no_fit); spec L4 (sweep.py)
"""LAB-REV2-BASE, part 2 of 3: the sweep's baselines (scripts/skilllab/sweep.py, scan.py). Fakes for the fights; the real scenes only where
a test says so (they need the library for the pre-flight's reach read: the `library` fixture).

THIS FILE FREEZES THE INTERFACE ADDITIONS FOR THE BUILDER.

Decision 25: every baseline variant (naive_attacker, naive_defender, naive_defender_attacker_layer, naive_defender_play_layer) is
pre-flighted ON ITS OWN SETUP. Today sweep._naive_side copies the PLAY's `prefight` word onto the baseline build, so a baseline that
does not fit or cannot be routed or cannot reach is fought anyway (the 35 caps of the first L4 try). Now:
  - default_builds(play, role, features)(heads, swap).labels["prefight"] == scenes.preflight(<the Setup that call returned>, engine), for
    every role, the same contract as scenes.placed_scene's label (decision 7). "no_reach" included: a defender variant none of whose types
    reach the attackers' layer, or the reverse, reads "no_reach".
  - A baseline refused no_reach / unroutable at the smallest or largest headcount is NOT fought, is LISTED with its role in the entry's
    `refused` ({"family", "play", "layout", "role", "reason"}, the shape of today's entries), and the play and the other baselines still run
    (the behaviour of sweep._usable_baselines; green controls below). No cap row comes from it.

Decision 26, the sweep half. A baseline whose placement fails ("no_fit") at some headcount of 8..48 (ENEMY_FROM..ENEMY_TO) while it placed
at 8 stops the play's scan on that layout:
  - K = the last headcount of 8..48 below the first headcount at which ANY baseline of the play is refused "no_fit" (the test worlds
    refuse monotonically: every headcount above a limit; behaviour on a non-monotone refusal is the builder's and is not pinned).
    sweep finds K by calling each baseline build at every headcount 8..48 (a build is cheap and runs no tick) and reading
    labels["prefight"].
  - The play and every baseline that placed are then scanned over 8..K only (bisection or full_scan, K as the top of the range), with the
    same replicates; no fight at a headcount above K is run for that play on that layout, no other play or layout is touched.
  - Every NON-CONTROL row of that (play, layout) in the csv carries the new label column `baseline_no_fit` = 1 (an int, written "1"), and
    its `ceiling_hit` is 0 even when the play won every scanned headcount: the cell is neither a ceiling hit nor a finding. Every other
    row, control rows and smoke control rows included, carries `baseline_no_fit` = 0. It is a LABEL column of the row (passed to
    rows.fight_row as a keyword like family or play, so rows.py and test_rows.py's fixed-key list are untouched), present in every sweep
    and smoke csv.
  - The entry (sweep) and the summary (smoke) carry `baseline_no_fit`: a list, in layout then play order, of
    {"family", "play", "layout", "last_headcount"} for a sweep entry and {"play", "layout", "last_headcount"} for the smoke summary (smoke
    refused entries have no "family"), empty when no cell was cut. `last_headcount` is K.
  - `refused` carries one entry per baseline role that failed to place at some headcount of 8..48, reason "no_fit", the cut play's other
    roles that placed everywhere absent; the play itself is not refused.
  - `defects` (cap_rows, draw_rows, cells) and the refinement are not fed by the cut: the cut scan is not a defect.
Not pinned (questions in the report): a play whose baseline is already refused no_fit at the smallest headcount (K < 8); how refinement
reads a cut, always-won scan.

Existing sweep tests keep their meaning: nothing here changes an entry key they read.
"""
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_baselines import expected_skipping, fake_base, in_block, keyed, positions, vg  # noqa: E402
from fakes_scans import _fr  # noqa: E402
from scripts.skilllab import scenes, sweep  # noqa: E402
from scripts.skilllab.contract import Block, Setup  # noqa: E402

CAPS = sweep.Capabilities(arc=True, cone=True)
PLAY = "s2_concave"
S3 = "s3_layer_above"
S3_ROLES = ("naive_attacker", "naive_defender_attacker_layer", "naive_defender_play_layer")
S2_ROLES = ("naive_attacker", "naive_defender")


@pytest.fixture(scope="module")
def library():
    from scripts.skilllab import engine
    return engine.Engine()


# ---- the fakes ---------------------------------------------------------------------------------------------------------------------

def limited_builds(limits=None, refuse=None):
    """builds(play, role, layout) as the sweep's seam. `limits` {(play, role, layout id): K}: label 'no_fit' at heads > K, else 'ok'.
    `refuse` {(play, role): word}: that word at every headcount. The Setup carries the cell's identity in unit_types."""
    limits, refuse = limits or {}, refuse or {}

    def builds(play, role, layout):
        def build(enemy_heads, swap):
            word = refuse.get((play, role), "ok")
            k = limits.get((play, role, layout.get("id")))
            if word == "ok" and k is not None and enemy_heads > k:
                word = "no_fit"
            build.labels["prefight"] = word
            return Setup(groups=(), unit_types={"enemy": enemy_heads, "swap": swap, "_play": play, "_role": role, "_layout": layout.get("id")})
        build.labels = {"placement_shift": 0.0, "prefight": None}
        return build
    return builds


class Fights:
    """fight_fn: side 0 wins while enemy_heads <= be(unit_types); records every call."""

    def __init__(self, be=lambda ut: 20):
        self.be, self.calls = be, []

    def __call__(self, setup, seed, swap):
        ut = setup.unit_types
        self.calls.append(dict(play=ut["_play"], role=ut["_role"], layout=ut["_layout"], enemy=ut["enemy"], swap=swap, seed=seed))
        return _fr("side0" if ut["enemy"] <= self.be(ut) else "side1", ut["enemy"])


LAYOUTS = {"A": {"id": 1}, "B": {"id": 2}}


def run(tmp_path, builds, fights=None, family="damage_up", plays=(PLAY,), layouts=None, **kw):
    fights = fights or Fights()
    entry = sweep.run_family(family, tmp_path, builds=builds, layouts=layouts or LAYOUTS, plays=plays, fight_fn=fights, caps=CAPS, **kw)
    with open(tmp_path / ("sweep_%s.csv" % family), newline="") as fh:
        rows = list(csv.DictReader(fh))
    return entry, fights, rows


def heads_of(fights, play, layout_id, role=None):
    return sorted({c["enemy"] for c in fights.calls if c["play"] == play and c["layout"] == layout_id and (role is None or c["role"] == role)})


def cell_rows(rows, play, layout):
    return [r for r in rows if r["play"] == play and r["layout"] == layout and not r["kind"].startswith("control_")]


# ---- (c) a refused baseline variant is not fought and is listed with its role (green controls: the behaviour exists) -------------

@pytest.mark.parametrize("word", ["no_reach", "unroutable"])
@pytest.mark.parametrize("play,role", [(S3, r) for r in S3_ROLES] + [(PLAY, r) for r in S2_ROLES])
def test_c_a_baseline_variant_refused_by_the_preflight_is_not_fought_and_is_listed_with_its_role(tmp_path, play, role, word):
    """Decision 25: refused 'like any scene'. The role is never fought (so it cannot cap), is listed with its role and the word, the
    play and the other roles still run to 48, and nothing is cut (baseline_no_fit 0). Green before and after (sweep._usable_baselines)."""
    entry, fights, rows = run(tmp_path, limited_builds(refuse={(play, role): word}), plays=(play,))
    assert not [c for c in fights.calls if c["role"] == role]
    got = [r for r in entry["refused"] if r["play"] == play]
    assert [(r["family"], r["layout"], r["role"], r["reason"]) for r in got] == [("damage_up", l, role, word) for l in LAYOUTS]
    others = [r for r in sweep.baseline_roles(play) if r != role] + ["play"]
    for other in others:
        assert heads_of(fights, play, 1, other)[-1] == 48, other
    assert not [r for r in rows if r["outcome"] == "cap"] and entry["defects"]["cap_rows"] == 0


def test_c_control_the_same_run_without_a_refusal_fights_every_role(tmp_path):
    """Positive control for the test above: the role it leaves out is fought when it is not refused."""
    entry, fights, _ = run(tmp_path, limited_builds(), plays=(S3,))
    assert {c["role"] for c in fights.calls if c["play"] == S3} >= {"play", *S3_ROLES} and entry["refused"] == []


# ---- (d) a layout that cannot hold the count at all: the scan stops at the last headcount where every baseline placed -----------

@pytest.mark.parametrize("full_scan", [False, True])
@pytest.mark.parametrize("k", [24, 47])
def test_d_the_scan_of_the_play_stops_at_the_last_headcount_where_both_baselines_placed(tmp_path, k, full_scan):
    """naive_attacker places up to k on layout A only. The play and both baselines are fought over 8..k on A and over 8..48 on B."""
    entry, fights, rows = run(tmp_path, limited_builds({(PLAY, "naive_attacker", 1): k}), full_scan=full_scan)
    for role in ("play",) + S2_ROLES:
        a, b = heads_of(fights, PLAY, 1, role), heads_of(fights, PLAY, 2, role)
        assert a[0] == 8 and a[-1] == k and b[-1] == 48, (role, a, b)
        if full_scan:
            assert a == list(range(8, k + 1)) and b == list(range(8, 49))
    assert not [c for c in fights.calls if c["layout"] == 1 and c["enemy"] > k and c["play"] == PLAY]


def test_d_the_binding_baseline_sets_k_when_two_baselines_run_out(tmp_path):
    """naive_attacker places up to 32, naive_defender up to 24: K is 24, and both are listed with their roles."""
    entry, fights, _ = run(tmp_path, limited_builds({(PLAY, "naive_attacker", 1): 32, (PLAY, "naive_defender", 1): 24}))
    assert max(heads_of(fights, PLAY, 1)) == 24 and max(heads_of(fights, PLAY, 2)) == 48
    assert entry["baseline_no_fit"] == [{"family": "damage_up", "play": PLAY, "layout": "A", "last_headcount": 24}]
    listed = {r["role"] for r in entry["refused"] if r["layout"] == "A"}
    assert "naive_defender" in listed and listed <= set(S2_ROLES)


def test_d_a_layer_play_with_three_baselines_stops_at_the_weakest_of_them(tmp_path):
    entry, fights, _ = run(tmp_path, limited_builds({(S3, "naive_defender_play_layer", 1): 16}), plays=(S3,))
    assert max(heads_of(fights, S3, 1)) == 16 and max(heads_of(fights, S3, 2)) == 48
    assert [r["role"] for r in entry["refused"] if r["layout"] == "A"] == ["naive_defender_play_layer"]


def test_d_the_cell_is_marked_baseline_no_fit_and_is_neither_a_ceiling_hit_nor_a_defect(tmp_path):
    """The play wins everywhere (be 99), so a scan cut at 24 reads as 'won at every scanned headcount'. It is marked baseline_no_fit
    and ceiling_hit 0; the same play on layout B (not cut) is the positive control: ceiling_hit 1, baseline_no_fit 0."""
    entry, fights, rows = run(tmp_path, limited_builds({(PLAY, "naive_attacker", 1): 24}), Fights(be=lambda ut: 99))
    a, b = cell_rows(rows, PLAY, "A"), cell_rows(rows, PLAY, "B")
    assert a and {r["baseline_no_fit"] for r in a} == {"1"} and {r["ceiling_hit"] for r in a} == {"0"}
    assert b and {r["baseline_no_fit"] for r in b} == {"0"} and {r["ceiling_hit"] for r in b if r["baseline"] == "none"} == {"1"}
    assert entry["defects"] == {"cap_rows": 0, "draw_rows": 0, "cells": 0}
    assert entry["baseline_no_fit"] == [{"family": "damage_up", "play": PLAY, "layout": "A", "last_headcount": 24}]


def test_d_the_refusal_is_listed_with_its_role_and_the_play_is_not_refused(tmp_path):
    entry, fights, rows = run(tmp_path, limited_builds({(PLAY, "naive_attacker", 1): 24}))
    a = [r for r in entry["refused"] if r["layout"] == "A"]
    assert [(r["family"], r["play"], r["role"], r["reason"]) for r in a] == [("damage_up", PLAY, "naive_attacker", "no_fit")]
    assert not [r for r in entry["refused"] if r["layout"] == "B"]
    assert {r["baseline"] for r in cell_rows(rows, PLAY, "A")} == {"none", *S2_ROLES}      # the play and both baselines have rows


def test_d_the_column_is_in_every_row_and_controls_read_zero(tmp_path):
    entry, _, rows = run(tmp_path, limited_builds({(PLAY, "naive_attacker", 1): 24}), plays=(PLAY,))
    assert rows and all(r["baseline_no_fit"] in ("0", "1") for r in rows)
    controls = [r for r in rows if r["kind"].startswith("control_")]
    assert controls and {r["baseline_no_fit"] for r in controls} == {"0"}


def test_d_nothing_is_cut_without_a_no_fit_refusal_and_the_column_reads_zero(tmp_path):
    """Positive control for the column: an ordinary run has baseline_no_fit 0 on every row and an empty list."""
    entry, fights, rows = run(tmp_path, limited_builds())
    assert {r["baseline_no_fit"] for r in rows} == {"0"} and entry["baseline_no_fit"] == [] and max(heads_of(fights, PLAY, 1)) == 48


def test_d_the_cut_is_per_play_and_per_layout(tmp_path):
    """Two plays on two layouts, one cell cut: the other three cells are scanned to 48 and read 0."""
    entry, fights, rows = run(tmp_path, limited_builds({(PLAY, "naive_attacker", 1): 24}), plays=(PLAY, "s2_screen"))
    assert max(heads_of(fights, PLAY, 1)) == 24
    for play, layout_id in ((PLAY, 2), ("s2_screen", 1), ("s2_screen", 2)):
        assert max(heads_of(fights, play, layout_id)) == 48
    assert [(e["play"], e["layout"]) for e in entry["baseline_no_fit"]] == [(PLAY, "A")]


def test_d_the_summary_json_carries_the_list(tmp_path):
    sweep.run(["damage_up"], tmp_path, builds=limited_builds({(PLAY, "naive_attacker", 1): 24}), layouts=LAYOUTS, plays=(PLAY,),
              fight_fn=Fights(), caps=CAPS)
    on_disk = json.loads((tmp_path / "sweep_summary.json").read_text())["families"]["damage_up"]
    assert on_disk["baseline_no_fit"] == [{"family": "damage_up", "play": PLAY, "layout": "A", "last_headcount": 24}]


# ---- (d) the smoke command --------------------------------------------------------------------------------------------------------

def smoke_controls():
    return {name: (lambda enemy_heads, swap, name=name: Setup(groups=(), unit_types={
        "enemy": enemy_heads, "swap": swap, "_play": name, "_role": "play", "_layout": None})) for name in ("mirror", "numbers", "planted")}


def test_d_smoke_cuts_the_scan_marks_the_rows_and_lists_the_cells(tmp_path):
    """Smoke layouts 81, 78, 192 (features are only keys for the fake): s3_layer_above's naive attacker places up to 24 everywhere."""
    inner = limited_builds({(S3, "naive_attacker", None): 24})
    fights = Fights()
    summary = sweep.run_smoke(tmp_path, workers=1, builds=lambda play, role, features: inner(play, role, {"id": None}), fight_fn=fights,
                              control_builds=smoke_controls())
    with open(tmp_path / "smoke.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert summary["baseline_no_fit"] == [{"play": S3, "layout": l, "last_headcount": 24} for l in sweep.SMOKE_LAYOUTS]
    assert [(r["play"], r["layout"], r["role"], r["reason"]) for r in summary["refused"]] == \
        [(S3, l, "naive_attacker", "no_fit") for l in sweep.SMOKE_LAYOUTS]
    cut = [r for r in rows if r["play"] == S3]
    assert cut and {r["baseline_no_fit"] for r in cut} == {"1"} and max(int(r["enemy_heads"]) for r in cut) == 24
    other = [r for r in rows if r["play"] == "s3_types_by_reach"]
    assert other and {r["baseline_no_fit"] for r in other} == {"0"} and max(int(r["enemy_heads"]) for r in other) == 48
    assert {r["baseline_no_fit"] for r in rows if r["family"] == "controls"} == {"0"}
    assert summary["defects"] == {"cap_rows": 0, "draw_rows": 0, "cells": 0}
    assert json.loads((tmp_path / "smoke_summary.json").read_text())["baseline_no_fit"] == summary["baseline_no_fit"]


# ---- (c) default_builds: the label is the pre-flight of the baseline's OWN Setup -----------------------------------------------

FEATS = {"blocked_layer_top": 0, "choke_width_bodies": 0, "cover_density_corridor": 0, "detour_ratio": 0, "lane_count": 0,
         "start_distance": 1400}


@pytest.fixture
def fake_scene(monkeypatch):
    """default_builds with scenes.placed_scene replaced by a stand-in returning `base` (and the sweep's layout cache emptied)."""
    def install(base):
        monkeypatch.setattr(sweep, "_layouts", {})
        monkeypatch.setattr(scenes, "placed_scene", lambda layout, play, start_distance, features, counter=False: base)
        return lambda role: sweep.default_builds("fake_play", role, FEATS)
    return install


def holder_on_layer_1():
    """Side 0 holds on layer 1, side 1 attacks from layer 0; both are Vanguards (reach none up, none down): the play's own scene is
    'no_reach'. The attacker-layer variant moves the holders to layer 0 (same-layer fight, 'ok'); the play-layer variant keeps layer 1
    ('no_reach')."""
    return (vg(0, "Vanguard", 8, 1000.0, 1000.0, layer=1, order="guard", facing=0.0),
            vg(1, "Vanguard", 8, 3000.0, 1000.0, layer=0, order="attack_move", facing=180.0))


@pytest.mark.parametrize("base_label", ["ok", "no_fit", "unroutable"])
@pytest.mark.parametrize("role,expected", [("naive_defender_play_layer", "no_reach"), ("naive_defender_attacker_layer", "ok"),
                                           ("naive_defender", "ok")])
def test_c_a_baseline_variant_is_preflighted_on_its_own_setup_not_on_the_plays_label(fake_scene, library, role, expected, base_label):
    """Decision 25. The stand-in base lies about itself (its label is base_label whatever its groups are). Red before: the baseline
    copies that label."""
    for_role = fake_scene(fake_base(holder_on_layer_1(), label=base_label, point=(1000.0, 1000.0)))
    build = for_role(role)
    setup = build(8, False)
    assert scenes.preflight(setup, library) == expected
    assert build.labels["prefight"] == expected


# ---- (d) a baseline built by sweep._naive_side skips blocked cells (decision 26) ------------------------------------------------

def mixed_side0():
    """Side 0 holds with two types, Vanguards on layer 0 and Raiders on layer 1 (a layer play's shape); side 1 attacks from layer 0."""
    return [vg(0, "Vanguard", 8, 1100.0, 1000.0, layer=0, order="guard", facing=0.0), vg(0, "Raider", 8, 900.0, 1000.0, layer=1, order="guard", facing=0.0),
            vg(1, "Vanguard", 8, 3000.0, 1000.0, layer=0, order="attack_move", facing=180.0)]


WALLS = {"one cell": lambda top: Block(top[0] - 5, top[1] - 5, top[0] + 5, top[1] + 5, 0, 0),
         "upper half": lambda top: Block(600.0, 1060.0, 1400.0, 1400.0, 0, 0)}      # layer 0 only: the Raiders (layer 1) are not blocked


@pytest.mark.parametrize("role", ["naive_defender_attacker_layer", "naive_defender_play_layer"])
@pytest.mark.parametrize("wall", sorted(WALLS))
def test_d_a_defender_blob_skips_the_blocked_cells_on_its_layer(fake_scene, library, role, wall):
    """The mean anchor of side 0 is (1000, 1000). Open ground gives each type one blob there. A wall on layer 0 catches cells of the
    layer-0 blob(s): they skip (the first `count` free cells of the continued fill order), the label is 'ok' and the pre-flight of the
    Setup. In the play-layer variant the Raiders stand on layer 1 and keep their open-ground cells (control for layer awareness).
    Red before: units stand in the wall and the label is the base's."""
    open_setup = fake_scene(fake_base(mixed_side0()))(role)(8, False)
    top = max((p for g in open_setup.groups if g.side == 0 and g.layer == 0 for p in positions(g)), key=lambda p: p[1])
    wall_block = WALLS[wall](top)
    build = fake_scene(fake_base(mixed_side0(), blocks=(wall_block,)))(role)
    setup = build(8, False)
    blocks = setup.terrain.blocks
    assert [p for g in open_setup.groups if g.side == 0 for p in positions(g) if in_block(blocks, g.layer, p)], "fixture: the wall catches a cell"
    for g in (g for g in setup.groups if g.side == 0):
        assert len(positions(g)) == g.count == 8
        assert not [p for p in positions(g) if in_block(blocks, g.layer, p)], (g.unit, g.layer)
        assert keyed(positions(g)) == keyed(expected_skipping(g, blocks)), (g.unit, g.layer)
    if role == "naive_defender_play_layer":
        old = {(g.unit, g.layer): positions(g) for g in open_setup.groups if g.side == 0}
        raider = next(g for g in setup.groups if g.side == 0 and g.unit == "Raider")
        assert raider.layer == 1 and positions(raider) == old[("Raider", 1)]
    assert build.labels["prefight"] == scenes.preflight(setup, library) == "ok"


# ---- (b) open ground: the baselines are byte-identical to the built tree ----------------------------------------------------------

# sha256 over repr((play, role, heads, side, unit, layer, order, positions)) of default_builds for s2_concave and s3_layer_above on an open
# layout (features FEATS), heads 8, 17, 48, every baseline role but naive_attacker. Recorded on the built tree 2741d544.
OPEN_BASELINE_HASH = "dfc06c36b51bc7663c5a1de087c4d3508a389b6d507c82a9bac3a2fefd0613a5"


def test_b_open_ground_baseline_blobs_are_byte_identical_to_the_built_tree(library):
    import hashlib
    h = hashlib.sha256()
    for play in (PLAY, S3):
        for role in sweep.baseline_roles(play)[1:]:
            build = sweep.default_builds(play, role, FEATS)
            for n in (8, 17, 48):
                for g in build(n, False).groups:
                    h.update(repr((play, role, n, g.side, g.unit, g.layer, g.order, positions(g))).encode())
                assert build.labels["prefight"] == "ok", (play, role, n)
    assert h.hexdigest() == OPEN_BASELINE_HASH


# ---- (f) ruling 25's construction, as built (green controls) ------------------------------------------------------------------------

def test_f_the_play_layer_variant_keeps_each_type_on_its_layer_and_the_attacker_layer_variant_puts_all_on_the_attackers(fake_scene):
    """Ruling 25: _play_layer keeps each type on the layer the play gave it; _attacker_layer puts every type on the attacker's layer;
    neither is 'the whole blob on one raised layer'. One blob per (type, layer), same units and counts, the timeline dropped. Green
    before and after."""
    base = fake_base(mixed_side0())
    play_layer = fake_scene(base)("naive_defender_play_layer")(8, False)
    attacker_layer = fake_scene(base)("naive_defender_attacker_layer")(8, False)
    own = [g for g in play_layer.groups if g.side == 0]
    assert {(g.unit, g.layer, g.count) for g in own} == {("Vanguard", 0, 8), ("Raider", 1, 8)}
    assert {g.layer for g in own} == {0, 1}                               # not one raised layer
    mine = [g for g in attacker_layer.groups if g.side == 0]
    assert {(g.unit, g.count) for g in mine} == {("Vanguard", 8), ("Raider", 8)} and {g.layer for g in mine} == {0}
    assert play_layer.timeline == () == attacker_layer.timeline
