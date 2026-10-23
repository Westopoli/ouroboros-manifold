# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decisions 25 and 41 items 2 and 3 (layer holder, mean anchor, roles from the play's Setup);
# audit of 013370a4 (Architect's coordinator, 2026-10-19) items C, E and G
"""LAB-REV2-FIX: more pins on baseline_roles and the naive defender (the interface is test_drift_fix_holder.py's).

  C  LAYER HOLDER, the test writer's reading of 'as today' (Q-FIX-1): a holder (some side-0 group on guard) with a side-0 GUARD group on a layer
     no side-1 group stands on gets ("naive_attacker", "naive_defender_attacker_layer", "naive_defender_play_layer"); otherwise
     ("naive_attacker", "naive_defender"). Layers are compared as sets, whatever their values (the enemy need not stand on layer 0), and a
     play's NAME plays no part (a layer holder not named s3_ gets the layer roles).
  E  MEAN ANCHOR of a type split over groups with UNEQUAL counts: the PLAIN mean of the groups' anchors (what the old code did; the Architect
     has not been asked whether it should be count-weighted: DRAFT reading, question Q-FIX2-3). The play-layer variant is one blob per unit TYPE
     when a type's groups all stand on one layer, and one blob per (type, layer) when a type's layers differ (decision 44 item 8).
  G  CALLS: run_family and run_smoke read baseline_roles from builds(play, "play", layout)(ENEMY_FROM, False), the first headcount, unswapped."""
import csv
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_baselines import vg  # noqa: E402
from fakes_scans import ScriptedFight, fake_groups  # noqa: E402
from scripts.skilllab import sweep  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402
from test_drift_fix_holder import ATT, ENEMY, FEATS, HOLD, LAYER_ROLES, fake_scene, own  # noqa: E402,F401


def guard(layer, side=0, count=8):
    return Group(side=side, unit="Vanguard", count=count, formation="blob", x=-700.0 if side == 0 else 700.0, y=0.0, facing_deg=0.0, layer=layer,
                 order="guard" if side == 0 else "attack_move", params={"radius": 114.0})


def setup_of(side0_layers, side1_layers):
    return Setup(groups=tuple(guard(l) for l in side0_layers) + tuple(guard(l, side=1) for l in side1_layers), unit_types={})


# ---- C: the layer reading, enemy off layer 0 ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("side0,side1,roles", [
    ((2,), (2,), (ATT, HOLD)),                  # same raised layer: plain
    ((1,), (2,), LAYER_ROLES),                  # holder on a layer the enemy is not on
    ((0,), (1, 2), LAYER_ROLES),                # the enemy stands on two layers, neither is the holder's
    ((2,), (1, 2), (ATT, HOLD)),                # one of the enemy's layers is the holder's
    ((2, 3), (2,), LAYER_ROLES),                # two holder groups, one of them on a layer the enemy is not on
    ((2, 2), (2,), (ATT, HOLD)),
    ((0,), (0,), (ATT, HOLD)),                  # control: the old layer-0 case
    ((1,), (1, 2), (ATT, HOLD)),                # audit of 32039a0f item 4: one of the enemy's layers is the holder's (the lower one): plain
])
def test_baseline_roles_compares_the_holders_layers_with_the_enemys_whatever_their_values(side0, side1, roles):
    assert sweep.baseline_roles(setup_of(side0, side1)) == roles


def test_a_side_0_group_that_is_not_on_guard_does_not_count_toward_the_layer_rule():
    """Audit of 32039a0f item 4. The holder (guard, layer 2) stands where the enemy does; a side-0 group that attack-moves from layer 3 is not a
    holder and its layer plays no part: the roles are the plain ones. Controls: the same group on guard is a layer holder; the same group on
    the enemy's layer changes nothing."""
    holder, enemy = guard(2), guard(2, side=1)
    raised = dataclasses.replace(guard(3), order="attack_move")
    assert sweep.baseline_roles(Setup(groups=(holder, raised, enemy), unit_types={})) == (ATT, HOLD)
    assert sweep.baseline_roles(Setup(groups=(holder, guard(3), enemy), unit_types={})) == LAYER_ROLES
    assert sweep.baseline_roles(Setup(groups=(holder, dataclasses.replace(guard(2), order="attack_move"), enemy), unit_types={})) == (ATT, HOLD)


def layer_builds(layer_of_holder):
    """builds(play, role, layout): a holder on `layer_of_holder` against an enemy on layer 0 for ANY play name (none starts with s3_)."""
    def builds(play, role, layout):
        def build(enemy_heads, swap):
            build.labels["prefight"] = "ok"
            g0, g1 = fake_groups(play)
            return Setup(groups=(dataclasses.replace(g0, layer=layer_of_holder), g1),
                         unit_types={"enemy": enemy_heads, "swap": swap, "_play": play, "_role": role})
        build.labels = {"placement_shift": 0.0, "prefight": None}
        return build
    return builds


def baselines_of_run(tmp_path, builds, play="p_layer"):
    fights = ScriptedFight(be_of=lambda s: 20)
    sweep.run_family("range_up", tmp_path, builds=builds, layouts={"A": {"id": 1}}, plays=(play,), fight_fn=fights,
                     caps=sweep.Capabilities(arc=True, cone=True))
    with open(tmp_path / "sweep_range_up.csv", newline="") as fh:
        return {r["baseline"] for r in csv.DictReader(fh) if r["kind"] == "grid"}


def test_a_layer_holder_not_named_s3_gets_the_two_layer_variants_in_the_sweep(tmp_path):
    assert baselines_of_run(tmp_path, layer_builds(1)) == {"none", *LAYER_ROLES}


def test_control_the_same_name_holding_on_the_enemys_layer_gets_the_plain_defender(tmp_path):
    assert baselines_of_run(tmp_path, layer_builds(0)) == {"none", ATT, HOLD}


# ---- E: the mean anchor and the play-layer variant ---------------------------------------------------------------------------------------

def test_unequal_counts_of_one_type_use_the_plain_mean_of_the_groups_anchors(fake_scene):
    """DRAFT reading (Q-FIX2-3): Vanguards 2 at (600, 900) and 6 at (1000, 1100): the plain mean (800, 1000), not the count-weighted (900, 1050)."""
    from fakes_baselines import fake_base
    base = fake_base([vg(0, "Vanguard", 2, 600.0, 900.0, order="guard"), vg(0, "Vanguard", 6, 1000.0, 1100.0, order="guard"), ENEMY])
    blobs = own(fake_scene(base)("naive_defender_attacker_layer")(8, False))
    assert [(g.unit, g.count, g.x, g.y) for g in blobs] == [("Vanguard", 8, 800.0, 1000.0)]


def test_the_play_layer_variant_is_one_blob_per_type_and_layer_when_a_type_stands_on_two_layers(fake_scene):
    """Decision 44 item 8 (supersedes the audit-E reading 'one blob per type'): one blob per (type, layer) ONLY when a type's layers differ.
    Vanguards 4 on layer 0 and 4 on layer 1 are two blobs of 4, one per layer; the Raiders stand on one layer: one blob."""
    from fakes_baselines import fake_base
    base = fake_base([vg(0, "Vanguard", 4, 600.0, 900.0, layer=0, order="guard"), vg(0, "Vanguard", 4, 1000.0, 1100.0, layer=1, order="guard"),
                      vg(0, "Raider", 8, 1500.0, 1000.0, layer=1, order="guard"), ENEMY])
    blobs = own(fake_scene(base)("naive_defender_play_layer")(8, False))
    assert sorted((g.unit, g.count) for g in blobs) == [("Raider", 8), ("Vanguard", 4), ("Vanguard", 4)]
    assert sorted(g.layer for g in blobs if g.unit == "Vanguard") == [0, 1]
    assert [g.layer for g in blobs if g.unit == "Raider"] == [1]


def test_control_a_type_whose_groups_all_stand_on_one_layer_is_one_blob_per_type_in_the_play_layer_variant(fake_scene):
    """Control for decision 44 item 8: two Vanguard groups both on layer 1 are ONE blob of 8 on layer 1 (per type, not per group)."""
    from fakes_baselines import fake_base
    base = fake_base([vg(0, "Vanguard", 4, 600.0, 900.0, layer=1, order="guard"), vg(0, "Vanguard", 4, 1000.0, 1100.0, layer=1, order="guard"),
                      vg(0, "Raider", 8, 1500.0, 1000.0, layer=1, order="guard"), ENEMY])
    blobs = own(fake_scene(base)("naive_defender_play_layer")(8, False))
    assert sorted((g.unit, g.count, g.layer) for g in blobs) == [("Raider", 8, 1), ("Vanguard", 8, 1)]


def test_the_attacker_layer_variant_puts_every_blob_on_the_enemys_layer_when_it_is_not_zero(fake_scene):
    """Control for the layer reading of E: the enemy on layer 2, the naive_defender_attacker_layer blobs all stand on layer 2."""
    from fakes_baselines import fake_base
    enemy = vg(1, "Vanguard", 8, 3000.0, 1000.0, layer=2, order="attack_move", facing=180.0)
    base = fake_base([vg(0, "Vanguard", 8, 800.0, 900.0, layer=0, order="guard"), vg(0, "Raider", 8, 1200.0, 1100.0, layer=1, order="guard"), enemy])
    blobs = own(fake_scene(base)("naive_defender_attacker_layer")(8, False))
    assert len(blobs) == 2 and {g.layer for g in blobs} == {2}


# ---- G: where the sweep reads the roles from ---------------------------------------------------------------------------------------------

def picky_builds(log):
    """The play's build is a LAYER holder (side 0 on layer 1, enemy on 0) ONLY at (ENEMY_FROM, False); at any other (heads, swap) it is a
    meeting. The name p_x starts with no s3_, so the old name-keyed function reads a plain holder here and fails the layer roles below.
    Records every call of a role "play" build."""
    def builds(play, role, layout):
        def build(enemy_heads, swap):
            build.labels["prefight"] = "ok"
            if role == "play":
                log.append((play, enemy_heads, swap))
            holder = (enemy_heads, swap) == (sweep.ENEMY_FROM, False)
            g0, g1 = fake_groups(play, meeting=not holder)
            if holder:
                g0 = dataclasses.replace(g0, layer=1)
            return Setup(groups=(g0, g1), unit_types={"enemy": enemy_heads, "swap": swap, "_play": play, "_role": role})
        build.labels = {"placement_shift": 0.0, "prefight": None}
        return build
    return builds


def test_run_family_reads_the_roles_from_the_play_build_at_the_first_headcount_unswapped(tmp_path):
    log = []
    baselines = baselines_of_run(tmp_path, picky_builds(log), play="p_x")
    assert (("p_x", sweep.ENEMY_FROM, False)) in log
    assert baselines == {"none", *LAYER_ROLES}         # a read at (ENEMY_TO, True) or (ENEMY_FROM, True) sees a meeting: no defender


def test_run_smoke_reads_the_roles_from_the_play_build_at_the_first_headcount_unswapped(tmp_path):
    log = []
    controls = {n: (lambda h, swap, n=n: Setup(groups=(), unit_types={"enemy": h, "swap": swap, "_play": n, "_role": "play"}))
                for n in ("mirror", "numbers", "planted")}
    sweep.run_smoke(tmp_path, workers=1, builds=picky_builds(log), layouts={"A": {"id": 1}}, fight_fn=ScriptedFight(be_of=lambda s: 20),
                    control_builds=controls)
    with open(tmp_path / "smoke.csv", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r["family"] == "vision"]
    assert any(h == sweep.ENEMY_FROM and not s for _p, h, s in log)
    assert {r["baseline"] for r in rows} == {"none", *LAYER_ROLES}
