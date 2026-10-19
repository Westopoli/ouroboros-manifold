# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decisions 25, 26, 32 and 36 (baseline variants, pre-flight coverage, baseline_no_fit, blob bounds); spec L4 (sweep.py)
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
Decision 32 (Architect 2026-10-19, the BASE readings), pinned below:
  - item 1: a baseline refused no_reach / unroutable drops only that baseline (the play and the others run; listed with its role).
  - item 2: a baseline that cannot be placed at headcount 8 (K < 8) lists the layout as `baseline_no_fit` with last_headcount None, no scan
    rows for the play on that layout (control rows are not pinned), no defect and no ceiling hit; the refused entry still names the role.
  - item 3: a scan cut at K by baseline_no_fit that the play wins throughout 8 to K is not a ceiling hit (ceiling_hit 0 on every row)
    and not a finding; refinement runs only inside 8 to K (no fight above K, refined points included).
  - item 4: the order is deterministic: rows identical at 1 and 12 workers for a cut run.
  - item 5: a blob of one unit follows the same rule (the anchor is radius zero; if blocked the nearest free cell).
Decision 36: the continuation stays inside the canvas and the anchor's connected region (the walls and pockets are in test_naive_blob_skip.py;
here the sweep's `_naive_side` builds are checked with a canvas-edge anchor and a wall across the canvas).
Decision 25's earlier-role case: when the EARLIER-listed role binds, K is still the minimum and BOTH roles are listed (exact set).
Seams the tests rely on (the builder must keep them): `sweep.run_family(..., builds=)` / `sweep.run_smoke(..., builds=)` take builds(play, role,
layout); `sweep._layouts` is the cache of placed scenes, emptied by the `fake_scene` fixture (monkeypatch); `scenes.placed_scene` is replaced
there by a lambda with the signature (layout, play, start_distance, features, counter=False) returning a prepared build; `sweep.default_builds`
reads the scene only through that call. The hand-built bases hold ONE group per side-and-type (the sweep's `_naive_side` blobs one group per
type).

Existing sweep tests keep their meaning: nothing here changes an entry key they read.
"""
import csv
import dataclasses
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_baselines import aligned, expected_skipping, fake_base, in_block, inside_canvas, keyed, positions, rounded, route_region, vg  # noqa: E402
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

def limited_builds(limits=None, refuse=None, refuse_at=None):
    """builds(play, role, layout) as the sweep's seam. `limits` {(play, role, layout id): K}: label 'no_fit' at heads > K, else 'ok'.
    `refuse` {(play, role): word}: that word at every headcount. `refuse_at` {(play, role): {heads: word}}: that word at those
    headcounts only. The Setup carries the cell's identity in unit_types."""
    limits, refuse, refuse_at = limits or {}, refuse or {}, refuse_at or {}

    def builds(play, role, layout):
        def build(enemy_heads, swap):
            word = refuse_at.get((play, role), {}).get(enemy_heads, refuse.get((play, role), "ok"))
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


@pytest.mark.parametrize("heads", [8, 48])
@pytest.mark.parametrize("word", ["no_reach", "unroutable"])
@pytest.mark.parametrize("play,role", [(S3, r) for r in S3_ROLES] + [(PLAY, r) for r in S2_ROLES])
def test_c_a_baseline_refused_at_the_smallest_or_the_largest_headcount_only_is_not_fought_and_is_listed(tmp_path, play, role, word, heads):
    """Decision 25 reads the pre-flight at the smallest (8) and the largest (48) headcount: a refusal at either one alone drops the
    baseline (never fought, listed once per layout with its word), and the play and the other roles still run to 48. Green before and
    after (sweep._usable_baselines)."""
    entry, fights, rows = run(tmp_path, limited_builds(refuse_at={(play, role): {heads: word}}), plays=(play,))
    assert not [c for c in fights.calls if c["role"] == role]
    got = [r for r in entry["refused"] if r["play"] == play]
    assert [(r["layout"], r["role"], r["reason"]) for r in got] == [(l, role, word) for l in LAYOUTS]
    for other in [r for r in sweep.baseline_roles(play) if r != role] + ["play"]:
        assert heads_of(fights, play, 1, other)[-1] == 48, other
    assert entry.get("baseline_no_fit", []) == [] and not [r for r in rows if r["outcome"] == "cap"]


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
    """naive_attacker places up to 32, naive_defender up to 24: K is 24, and both are listed with their roles (exactly those two)."""
    entry, fights, _ = run(tmp_path, limited_builds({(PLAY, "naive_attacker", 1): 32, (PLAY, "naive_defender", 1): 24}))
    assert max(heads_of(fights, PLAY, 1)) == 24 and max(heads_of(fights, PLAY, 2)) == 48
    assert entry["baseline_no_fit"] == [{"family": "damage_up", "play": PLAY, "layout": "A", "last_headcount": 24}]
    listed = {r["role"] for r in entry["refused"] if r["layout"] == "A"}
    assert listed == {"naive_attacker", "naive_defender"}


def test_d_the_earlier_role_binds_when_it_runs_out_first(tmp_path):
    """naive_attacker (the first role in baseline_roles) places up to 24, naive_defender up to 32: K is 24, the minimum, whichever role
    comes first; both are listed (exactly those two) and each baseline and the play are fought to 24 and no further."""
    entry, fights, _ = run(tmp_path, limited_builds({(PLAY, "naive_attacker", 1): 24, (PLAY, "naive_defender", 1): 32}))
    for role in ("play",) + S2_ROLES:
        assert max(heads_of(fights, PLAY, 1, role)) == 24 and max(heads_of(fights, PLAY, 2, role)) == 48, role
    assert entry["baseline_no_fit"] == [{"family": "damage_up", "play": PLAY, "layout": "A", "last_headcount": 24}]
    assert {r["role"] for r in entry["refused"] if r["layout"] == "A"} == {"naive_attacker", "naive_defender"}
    assert [r["reason"] for r in entry["refused"] if r["layout"] == "A"] == ["no_fit", "no_fit"]


def test_d_a_layer_play_whose_attacker_layer_variant_runs_out_first_is_cut_at_the_minimum(tmp_path):
    """s3_layer_above: naive_attacker places everywhere, the attacker-layer variant up to 16 and the play-layer variant up to 24: K is 16
    and exactly those two variants are listed."""
    entry, fights, _ = run(tmp_path, limited_builds({(S3, "naive_defender_attacker_layer", 1): 16, (S3, "naive_defender_play_layer", 1): 24}),
                           plays=(S3,))
    for role in ("play",) + S3_ROLES:
        assert max(heads_of(fights, S3, 1, role)) == 16 and max(heads_of(fights, S3, 2, role)) == 48, role
    assert entry["baseline_no_fit"] == [{"family": "damage_up", "play": S3, "layout": "A", "last_headcount": 16}]
    assert {r["role"] for r in entry["refused"] if r["layout"] == "A"} == {"naive_defender_attacker_layer", "naive_defender_play_layer"}


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
    assert entry["refined"] == []                      # an always-won cut scan is not a finding: nothing to refine


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


# ---- decision 32: K < 8, cut cells, refinement inside 8..K, workers --------------------------------------------------------------

def test_d_a_baseline_unplaceable_at_8_lists_the_layout_with_last_headcount_none_and_scans_nothing(tmp_path):
    """Decision 32 item 2 (K < 8): naive_attacker places up to 7 on layout A only. The layout is listed `baseline_no_fit` with
    last_headcount None; the play and the other baseline have NO scan rows on A (control rows are not pinned) and no baseline is fought
    there; no defect, no ceiling hit; the refusal is listed with its role. Layout B is scanned to 48 (positive control)."""
    entry, fights, rows = run(tmp_path, limited_builds({(PLAY, "naive_attacker", 1): 7}), Fights(be=lambda ut: 99))
    assert entry["baseline_no_fit"] == [{"family": "damage_up", "play": PLAY, "layout": "A", "last_headcount": None}]
    assert cell_rows(rows, PLAY, "A") == []
    assert not [c for c in fights.calls if c["layout"] == 1 and c["role"] in S2_ROLES]
    assert [(r["role"], r["reason"]) for r in entry["refused"] if r["layout"] == "A"] == [("naive_attacker", "no_fit")]
    assert entry["defects"] == {"cap_rows": 0, "draw_rows": 0, "cells": 0} and not [r for r in rows if r["outcome"] == "cap"]
    b = cell_rows(rows, PLAY, "B")
    assert b and max(int(r["enemy_heads"]) for r in b) == 48 and {r["ceiling_hit"] for r in b if r["baseline"] == "none"} == {"1"}
    assert {r["baseline_no_fit"] for r in b} == {"0"}


def pocket_base(ring):
    """A hand-built world: 16 holders on guard at (1000, 1000), 8 attackers at (3000, 1000), a 4000 x 4000 canvas; `ring` closes a
    200 x 100 wu pocket (100 wu walls on 50 wu bounds) round the holders' anchor, which cannot hold a blob of 16 (about 51,000 wu^2)."""
    ring_blocks = (aligned(800, 850, 900, 1150), aligned(1100, 850, 1200, 1150), aligned(900, 850, 1100, 950), aligned(900, 1050, 1100, 1150)) if ring else ()
    return fake_base([vg(0, "Vanguard", 16, 1000.0, 1000.0, order="guard"), vg(1, "Vanguard", 8, 3000.0, 1000.0, facing=180.0)], blocks=ring_blocks)


@pytest.mark.parametrize("ring", [True, False])
def test_d_a_closed_pocket_smaller_than_the_count_is_the_baseline_no_fit_path_on_hand_built_terrain(tmp_path, fake_scene, library, ring):
    """The real sweep.default_builds over a hand-built terrain (scenes.placed_scene stands in for the play's own scene only): the
    naive defender's 16 holders cannot be placed in the closed pocket (decision 36: the region has no free cell left), so the REAL
    pre-flight of its own Setup reads 'no_fit' at every headcount, K < 8, and the layout is listed baseline_no_fit with last_headcount
    None, no scan rows for the play, no defect, no ceiling hit. Without the ring (positive control) the same run places everything:
    nothing listed, every role scanned to 48. Red before: the build keeps its open-ground cells in the walls but nothing cuts the scan
    (and the label is the base's 'ok')."""
    fake_scene(pocket_base(ring))
    heads = []

    def fight_fn(setup, seed, swap):
        enemy = sum(g.count for g in setup.groups if g.side == 1)
        heads.append(enemy)
        return _fr("side0" if enemy <= 20 else "side1", enemy)

    entry = sweep.run_family("damage_up", tmp_path, layouts={"P": FEATS}, plays=(PLAY,), fight_fn=fight_fn, caps=CAPS)
    with open(tmp_path / "sweep_damage_up.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))
    mine = [r for r in rows if r["play"] == PLAY and not r["kind"].startswith("control_")]
    build = sweep.default_builds(PLAY, "naive_defender", FEATS)
    labels = {build(h, False) and build.labels["prefight"] for h in range(8, 49)}
    if ring:
        assert labels == {"no_fit"} and scenes.preflight(build(8, False), library) == "no_fit"
        assert entry["baseline_no_fit"] == [{"family": "damage_up", "play": PLAY, "layout": "P", "last_headcount": None}]
        assert [(r["role"], r["reason"]) for r in entry["refused"]] == [("naive_defender", "no_fit")]
        assert mine == []
        assert entry["defects"] == {"cap_rows": 0, "draw_rows": 0, "cells": 0}
    else:
        assert labels == {"ok"}
        assert entry["baseline_no_fit"] == [] and entry["refused"] == []
        assert {r["baseline"] for r in mine} == {"none", *S2_ROLES} and max(int(r["enemy_heads"]) for r in mine) == 48


@pytest.mark.parametrize("full_scan", [False, True])
def test_d_a_cut_cell_fights_each_headcount_like_an_uncut_one(tmp_path, full_scan):
    """Every (role, headcount) cell of a cut scan holds exactly 2 * replicates fights, swap False and True over seeds 0 .. replicates-1,
    the same set an uncut run fights there (full scan: the same cells too, so the cut is only the missing headcounts above K)."""
    cut_entry, cut_fights, _ = run(tmp_path / "cut", limited_builds({(PLAY, "naive_attacker", 1): 24}), full_scan=full_scan)
    _, full_fights, _ = run(tmp_path / "full", limited_builds(), full_scan=full_scan)
    per_cell = {}
    for c in cut_fights.calls:
        per_cell.setdefault((c["play"], c["role"], c["layout"], c["enemy"]), []).append((c["swap"], c["seed"]))
    want = sorted((swap, seed) for swap in (False, True) for seed in range(sweep.REPLICATES))
    assert per_cell
    for key, got in per_cell.items():
        assert sorted(set(got)) == want and len(got) % len(want) == 0, key          # each knob point fights the 2 * replicates set once
    if full_scan:
        key = lambda calls: sorted((c["play"], c["role"], c["layout"], c["enemy"], c["swap"], c["seed"]) for c in calls
                                   if not (c["layout"] == 1 and c["enemy"] > 24))
        assert key(cut_fights.calls) == key(full_fights.calls)
        assert not [c for c in cut_fights.calls if c["layout"] == 1 and c["enemy"] > 24 and c["play"] == PLAY]


class KnobFights(Fights):
    """side 0 wins while enemy_heads <= be(role, settings): the break-even follows the damage-up knob of the cell."""

    def __call__(self, setup, seed, swap):
        ut = setup.unit_types
        self.calls.append(dict(play=ut["_play"], role=ut["_role"], layout=ut["_layout"], enemy=ut["enemy"], swap=swap, seed=seed))
        return _fr("side0" if ut["enemy"] <= self.be(ut["_role"], setup.settings) else "side1", ut["enemy"])


def test_d_refinement_runs_only_inside_8_to_k_and_finds_what_the_uncut_run_finds(tmp_path):
    """The play's break-even is 20 from damage-up 0.75 up and 12 below, the baselines' 16: the gain changes sign between 0.75 and 0.5
    and refinement adds the values between them. Layout A is cut at K = 24 (above both break-evens): its refined points are fought
    only at 8 to 24 and the refined values equal an uncut run's. Layout B (positive control) is scanned to 48 including its refined
    points."""
    be = lambda role, settings: (20 if settings.get("OM_TP_DAMAGE_UP_1", 1.0) >= 0.75 else 12) if role == "play" else 16
    entry, fights, rows = run(tmp_path / "cut", limited_builds({(PLAY, "naive_attacker", 1): 24}), KnobFights(be=be))
    base, _, _ = run(tmp_path / "base", limited_builds(), KnobFights(be=be))
    assert entry["refined"] and entry["refined"] == base["refined"]
    refined_a = [r for r in cell_rows(rows, PLAY, "A") if r["kind"] == "refined"]
    assert refined_a and max(int(r["enemy_heads"]) for r in cell_rows(rows, PLAY, "A")) == 24
    assert not [c for c in fights.calls if c["layout"] == 1 and c["play"] == PLAY and c["enemy"] > 24]
    refined_b = [r for r in cell_rows(rows, PLAY, "B") if r["kind"] == "refined"]
    assert refined_b and max(int(r["enemy_heads"]) for r in refined_b) == 48
    assert {r["baseline_no_fit"] for r in refined_a} == {"1"} and {r["ceiling_hit"] for r in refined_a} == {"0"}


def test_d_a_cut_run_gives_the_same_rows_at_one_and_twelve_workers(tmp_path, monkeypatch):
    """Decision 32 item 4: the order is deterministic. The same cut run through the pool path (workers = 12, map_fn from a pool whose jobs
    run in REVERSE order) and in-process (workers = 1) writes the same csv bytes and the same summary."""
    from scripts.skilllab import pool
    from fakes_scans import FakePool
    be = lambda role, settings: (20 if settings.get("OM_TP_DAMAGE_UP_1", 1.0) >= 0.75 else 12) if role == "play" else 16
    builds = limited_builds({(PLAY, "naive_attacker", 1): 24, (S3, "naive_defender_play_layer", 2): 16})

    class ReversePool(FakePool):
        def map(self, jobs):
            jobs = list(jobs)
            out = [None] * len(jobs)
            for i in reversed(range(len(jobs))):
                out[i] = self.fight_fn(*jobs[i])
            return out

    FakePool.instances.clear()
    FakePool.fight_fn = KnobFights(be=be)
    monkeypatch.setattr(pool, "FightPool", ReversePool)
    kw = dict(builds=builds, layouts=LAYOUTS, plays=(PLAY, S3), caps=CAPS)
    sweep.run(["damage_up"], tmp_path / "w12", workers=12, **kw)
    assert FakePool.instances and FakePool.instances[0].workers == 12
    sweep.run(["damage_up"], tmp_path / "w1", workers=1, fight_fn=KnobFights(be=be), **kw)
    for name in ("sweep_damage_up.csv", "sweep_summary.json"):
        assert (tmp_path / "w12" / name).read_bytes() == (tmp_path / "w1" / name).read_bytes(), name
    assert json.loads((tmp_path / "w1" / "sweep_summary.json").read_text())["families"]["damage_up"]["baseline_no_fit"]


def test_d_the_cut_cells_are_listed_in_layout_then_play_order(tmp_path):
    """Entry order: layouts in the order given, plays in the order given inside a layout (A: the first play, the second play; B: ...)."""
    cuts = {(PLAY, "naive_attacker", 1): 24, ("s2_screen", "naive_attacker", 1): 16, (PLAY, "naive_attacker", 2): 32, ("s2_screen", "naive_attacker", 2): None}
    entry, _, _ = run(tmp_path, limited_builds({k: v for k, v in cuts.items() if v}), plays=("s2_screen", PLAY))
    assert [(e["layout"], e["play"], e["last_headcount"]) for e in entry["baseline_no_fit"]] == \
        [("A", "s2_screen", 16), ("A", PLAY, 24), ("B", PLAY, 32)]


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
    assert all("family" not in r for r in summary["refused"] + summary["baseline_no_fit"])        # the smoke entries have no family key
    assert {r["baseline"] for r in cut} == {"none", "naive_attacker"} | {"naive_defender_attacker_layer", "naive_defender_play_layer"}


def test_d_smoke_without_a_cut_lists_no_cell_and_its_refusals_have_no_family(tmp_path):
    """An uncut smoke run (one baseline refused no_reach on the way): summary['baseline_no_fit'] is [], every row reads 0 and reaches
    48, the refused entries keep {play, layout, role, reason} with no 'family'."""
    builds = limited_builds(refuse={(S3, "naive_attacker"): "no_reach"})
    summary = sweep.run_smoke(tmp_path, workers=1, builds=lambda play, role, features: builds(play, role, {"id": None}), fight_fn=Fights(),
                              control_builds=smoke_controls())
    with open(tmp_path / "smoke.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert summary["baseline_no_fit"] == [] and {r["baseline_no_fit"] for r in rows} == {"0"}
    assert summary["refused"] and all(set(r) == {"play", "layout", "role", "reason"} for r in summary["refused"])
    assert [r["role"] for r in summary["refused"]] == ["naive_attacker"] * len(sweep.SMOKE_LAYOUTS)
    assert max(int(r["enemy_heads"]) for r in rows if r["play"] == S3) == 48


def test_d_smoke_a_baseline_unplaceable_at_8_lists_none_and_has_no_rows(tmp_path):
    """Smoke counterpart of the K < 8 case: the cell is listed with last_headcount None and the play has no rows on that layout."""
    builds = limited_builds({(S3, "naive_attacker", None): 7})
    summary = sweep.run_smoke(tmp_path, workers=1, builds=lambda play, role, features: builds(play, role, {"id": None}), fight_fn=Fights(),
                              control_builds=smoke_controls())
    with open(tmp_path / "smoke.csv", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert summary["baseline_no_fit"] == [{"play": S3, "layout": l, "last_headcount": None} for l in sweep.SMOKE_LAYOUTS]
    assert not [r for r in rows if r["play"] == S3] and [r for r in rows if r["play"] == "s3_types_by_reach"]
    assert summary["defects"] == {"cap_rows": 0, "draw_rows": 0, "cells": 0}


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


# ---- (d) a baseline built by sweep._naive_side skips blocked cells (decisions 26, 32, 36) ------------------------------------------

def mixed_side0():
    """Side 0 holds with two types, Vanguards on layer 0 and Raiders on layer 1 (a layer play's shape); side 1 attacks from layer 0."""
    return [vg(0, "Vanguard", 8, 1100.0, 1000.0, layer=0, order="guard", facing=0.0), vg(0, "Raider", 8, 900.0, 1000.0, layer=1, order="guard", facing=0.0),
            vg(1, "Vanguard", 8, 3000.0, 1000.0, layer=0, order="attack_move", facing=180.0)]


# Walls on 50 wu bounds (test_naive_blob_skip.py header: the region reading). The mean anchor of side 0 is (1000, 1000).
WALLS = {"one cell": lambda top, lo, hi: aligned(top[0], top[1], top[0] + 1e-6, top[1] + 1e-6, lo, hi),
         "upper half": lambda top, lo, hi: Block(600.0, 1050.0, 1400.0, 1400.0, lo, hi)}


def own_points(setup):
    return [p for g in setup.groups if g.side == 0 for p in positions(g)]


def mean(pts):
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


@pytest.mark.parametrize("role", ["naive_defender_attacker_layer", "naive_defender_play_layer"])
@pytest.mark.parametrize("wall", sorted(WALLS))
def test_d_a_defender_blob_skips_the_blocked_cells_on_its_layer(fake_scene, library, role, wall):
    """The mean anchor of side 0 is (1000, 1000). Open ground gives each type one blob there. A wall on layer 0 catches cells of the
    layer-0 blob(s): they skip (unit k takes the k-th free cell of the continued fill order, compared UNSORTED), the label is 'ok' and
    the pre-flight of the Setup, nothing else of a group changes, and Setup.point is the mean of the skipped positions of the guard
    groups (ruling 6; both roles guard). In the play-layer variant the Raiders stand on layer 1 and keep their open-ground cells (control
    for layer awareness). Red before: units stand in the wall and the label is the base's."""
    open_setup = fake_scene(fake_base(mixed_side0()))(role)(8, False)
    top = max((p for g in open_setup.groups if g.side == 0 and g.layer == 0 for p in positions(g)), key=lambda p: p[1])
    wall_block = WALLS[wall](top, 0, 0)
    build = fake_scene(fake_base(mixed_side0(), blocks=(wall_block,)))(role)
    setup = build(8, False)
    blocks = setup.terrain.blocks
    assert [p for g in open_setup.groups if g.side == 0 for p in positions(g) if in_block(blocks, g.layer, p)], "fixture: the wall catches a cell"
    for g in (g for g in setup.groups if g.side == 0):
        assert len(positions(g)) == g.count == 8
        assert not [p for p in positions(g) if in_block(blocks, g.layer, p)], (g.unit, g.layer)
        expected = expected_skipping(g, setup.terrain)
        assert expected is not None and rounded(positions(g)) == rounded(expected), (g.unit, g.layer)
        g0 = next(o for o in open_setup.groups if o.side == 0 and (o.unit, o.layer) == (g.unit, g.layer))
        assert (g.x, g.y) == (g0.x, g0.y)
        assert dataclasses.replace(g0, formation=g.formation, params=g.params) == g, (g.unit, g.layer)
    if role == "naive_defender_play_layer":
        old = {(g.unit, g.layer): positions(g) for g in open_setup.groups if g.side == 0}
        raider = next(g for g in setup.groups if g.side == 0 and g.unit == "Raider")
        assert raider.layer == 1 and positions(raider) == old[("Raider", 1)]
    assert setup.point == pytest.approx(mean(own_points(setup)), abs=1e-6) and setup.point != open_setup.point
    assert build.labels["prefight"] == scenes.preflight(setup, library) == "ok"


@pytest.mark.parametrize("wall", sorted(WALLS))
def test_d_a_wall_on_layer_1_only_skips_the_layer_1_blob_and_leaves_the_layer_0_blob(fake_scene, library, wall):
    """Positive case for a wall that reaches layer 1 only (layer_lo = layer_hi = 1): in the play-layer variant the Raiders (layer 1) skip
    (the first free cells of their fill order) and the Vanguards (layer 0) keep every open-ground cell, with the wall through both
    blobs' cells in the plane. In the attacker-layer variant both types stand on layer 0, so nothing is skipped (control). Kills a
    builder that tests layer 0 only, or every layer."""
    base = lambda blocks=(): fake_base(mixed_side0(), blocks=blocks)
    open_setup = fake_scene(base())("naive_defender_play_layer")(8, False)
    top = max((p for g in open_setup.groups if g.side == 0 and g.layer == 1 for p in positions(g)), key=lambda p: p[1])
    wall_block = WALLS[wall](top, 1, 1)
    build = fake_scene(base((wall_block,)))("naive_defender_play_layer")
    setup = build(8, False)
    blocks = setup.terrain.blocks
    raider, vanguard = (next(g for g in setup.groups if g.side == 0 and g.unit == u) for u in ("Raider", "Vanguard"))
    r0, v0 = (next(g for g in open_setup.groups if g.side == 0 and g.unit == u) for u in ("Raider", "Vanguard"))
    assert [p for p in positions(r0) if in_block(blocks, 1, p)], "fixture: the wall catches a Raider cell"
    assert [p for p in positions(v0) if p[1] >= 1050.0 and 600.0 <= p[0] <= 1400.0] or wall == "one cell"
    assert not [p for p in positions(raider) if in_block(blocks, 1, p)]
    assert rounded(positions(raider)) == rounded(expected_skipping(raider, setup.terrain)) and positions(raider) != positions(r0)
    assert positions(vanguard) == positions(v0) and vanguard == v0
    assert build.labels["prefight"] == scenes.preflight(setup, library) == "ok"
    same = fake_scene(base((wall_block,)))("naive_defender_attacker_layer")(8, False)
    plain = fake_scene(base())("naive_defender_attacker_layer")(8, False)
    assert same.groups == plain.groups


@pytest.mark.parametrize("edge", ["lower edge", "upper edge"])
def test_d_a_cell_exactly_on_a_block_edge_is_blocked(fake_scene, library, edge):
    """Bounds are inclusive (the header's reading, the pre-flight's no_fit): a block whose edge is exactly an open-ground unit's
    coordinate catches that unit. The base is hand-built, so the coordinates are not moved by a scene offset."""
    open_setup = fake_scene(fake_base(mixed_side0()))("naive_defender_attacker_layer")(8, False)
    vanguards = next(g for g in open_setup.groups if g.side == 0 and g.unit == "Vanguard")
    pts = positions(vanguards)
    if edge == "lower edge":
        py = max(p[1] for p in pts)
        wall = Block(500.0, py, 1500.0, py + 300.0, 0, 0)
    else:
        py = min(p[1] for p in pts)
        wall = Block(500.0, py - 300.0, 1500.0, py, 0, 0)
    edge_cell = next(p for p in pts if p[1] == py)
    setup = fake_scene(fake_base(mixed_side0(), blocks=(wall,)))("naive_defender_attacker_layer")(8, False)
    new = [p for g in setup.groups if g.side == 0 and g.unit == "Vanguard" for p in positions(g)]
    assert edge_cell not in new and len(new) == 8 and not [p for p in new if in_block(setup.terrain.blocks, 0, p)]


@pytest.mark.parametrize("count", [1, 7, 9])
@pytest.mark.parametrize("role", ["naive_defender_attacker_layer", "naive_defender"])
def test_d_an_odd_or_single_blob_on_a_blocked_anchor_skips_like_any_other(fake_scene, library, role, count):
    """Decision 32 item 5 and the odd-count blob: a 10 x 10 wu block on the anchor (1000, 1000) takes the anchor cell. The odd blobs
    (7, 9) have a unit there on open ground and lose it to the next free cell of the fill order (unsorted); the blob of ONE unit
    (radius zero) takes the nearest free cell by increasing radius (properties: free, in the canvas, in the region, outside the
    wall, near, and never nearer for a wider wall). Setup.point is the mean of the skipped positions."""
    def groups():
        return [vg(0, "Vanguard", count, 1000.0, 1000.0, order="guard"), vg(1, "Vanguard", 8, 3000.0, 1000.0, facing=180.0)]
    open_setup = fake_scene(fake_base(groups()))(role)(8, False)
    assert positions(next(g for g in open_setup.groups if g.side == 0))[0] == (1000.0, 1000.0)       # an odd count puts a unit on the anchor, first
    distances = []
    for half in (5.0, 15.0):
        wall = Block(1000.0 - half, 1000.0 - half, 1000.0 + half, 1000.0 + half, 0, 4)
        build = fake_scene(fake_base(groups(), blocks=(wall,)))(role)
        setup = build(8, False)
        g = next(g for g in setup.groups if g.side == 0)
        pts = positions(g)
        assert len(pts) == count and not [p for p in pts if in_block(setup.terrain.blocks, g.layer, p)]
        assert (1000.0, 1000.0) not in pts
        if count == 1:
            seen, cell_of = route_region(setup.terrain, g.layer, (g.x, g.y))
            d = math.hypot(pts[0][0] - 1000.0, pts[0][1] - 1000.0)
            assert cell_of(pts[0]) in seen and inside_canvas(setup.terrain, pts[0]) and half < d < 150.0
            distances.append(d)
        else:
            assert rounded(pts) == rounded(expected_skipping(g, setup.terrain))
        assert setup.point == pytest.approx(mean(own_points(setup)), abs=1e-6)
        assert build.labels["prefight"] == scenes.preflight(setup, library) == "ok"
    if count == 1:
        assert distances[0] <= distances[1]


@pytest.mark.parametrize("bound", ["canvas edge", "closed wall", "wall with a gap"])
def test_d_the_continuation_stays_in_the_canvas_and_the_anchors_region(fake_scene, library, bound):
    """Decision 36 on the sweep's own builder: a 16-unit blob (anchor (1000, 1000), canvas 2000 x 2000) with
      - 'canvas edge': the anchor moved to 60 wu from the left edge: no unit is taken outside the canvas;
      - 'closed wall': a one-cell wall from the bottom to the top of the canvas just east of the anchor: no unit is taken beyond it;
      - 'wall with a gap': the same wall with a 200 wu gap on the anchor's row: units ARE taken beyond it (connected through the gap).
    Each equals the fill order over the free cells of the region (unsorted). Fixture guards show the case separates the rules."""
    canvas, ax = (2000.0, 2000.0), 1000.0
    blocks = ()
    if bound == "canvas edge":
        ax = 60.0
    else:
        blocks = (Block(1050.0, 0.0, 1100.0, 2000.0, 0, 4),) if bound == "closed wall" else \
            (Block(1050.0, 0.0, 1100.0, 900.0, 0, 4), Block(1050.0, 1100.0, 1100.0, 2000.0, 0, 4))
    groups = [vg(0, "Vanguard", 16, ax, 1000.0, order="guard"), vg(1, "Vanguard", 8, 1800.0, 1000.0, facing=180.0)]
    build = fake_scene(fake_base(groups, blocks=blocks, canvas=canvas, point=(ax, 1000.0)))("naive_defender_attacker_layer")
    setup = build(8, False)
    g = next(g for g in setup.groups if g.side == 0)
    pts = positions(g)
    expected = expected_skipping(g, setup.terrain)
    assert expected is not None and rounded(pts) == rounded(expected) and len(pts) == 16
    assert not [p for p in pts if in_block(setup.terrain.blocks, g.layer, p)]
    if bound == "canvas edge":
        assert len([p for p in expected_skipping(g, setup.terrain, canvas=False) if not inside_canvas(setup.terrain, p)]) >= 2, "fixture"
        assert all(inside_canvas(setup.terrain, p) for p in pts)
    elif bound == "closed wall":
        assert len([p for p in expected_skipping(g, setup.terrain, connected=False) if p[0] > 1100.0]) >= 2, "fixture"
        assert not [p for p in pts if p[0] > 1100.0]
    else:
        assert [p for p in pts if p[0] > 1100.0]
    assert build.labels["prefight"] == scenes.preflight(setup, library)


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
