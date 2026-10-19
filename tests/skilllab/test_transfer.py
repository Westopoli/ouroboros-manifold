# spec: docs/northstar/plans/skilllab-plan.md::Phase S::every result row carries how far it transfers
"""transfer_class, row_labels and label_build. The class definition is unconfirmed (Architect to rule)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402
from scripts.skilllab import rows, transfer  # noqa: E402
from scripts.skilllab.contract import FightResult, Group, Setup  # noqa: E402
from scripts.skilllab.transfer import MAGNITUDES, RULE_GEOMETRY, label_build, row_labels, transfer_class  # noqa: E402


def G(side, count=1):
    return Group(side=side, unit="Vanguard", count=count, formation="line", x=0.0, y=0.0, facing_deg=0.0,
                 layer=0, order="idle")


def setup(heads=1, **kw):
    return Setup(groups=(G(0), G(1, heads)), unit_types=kw.pop("unit_types", {}), **kw)


def test_constants_are_the_stated_strings():
    """The two class strings are fixed text."""
    assert RULE_GEOMETRY == "rule geometry: holds as is"
    assert MAGNITUDES == "magnitudes: will retune"


def test_four_hand_made_setups():
    """Plain is geometry; settings, unit_types, or both is magnitudes."""
    assert transfer_class(setup()) == RULE_GEOMETRY
    assert transfer_class(setup(settings={"OM_TP_TARGET_POLICY": 1})) == MAGNITUDES
    assert transfer_class(setup(unit_types={"X": {"base": "Vanguard", "scale": {"max_hp": 2}}})) == MAGNITUDES
    assert transfer_class(setup(settings={"OM_TP_TARGET_POLICY": 1},
                                unit_types={"X": {"base": "Vanguard"}})) == MAGNITUDES


def test_headcount_timeline_and_formation_never_change_the_class():
    """Headcounts, tick limits and terrain-free geometry are geometry."""
    assert transfer_class(setup(heads=9, max_ticks=10, sample_every=1)) == RULE_GEOMETRY


def test_row_labels_is_one_key_and_not_a_fixed_row_name():
    """row_labels carries only 'transfer', and that name does not collide with rows._FIXED."""
    assert row_labels(setup()) == {"transfer": RULE_GEOMETRY}
    assert "transfer" not in rows._FIXED


def _build(labels=None, **kw):
    def build(enemy_heads, swap):
        return setup(heads=enemy_heads, **kw)
    if labels is not None:
        build.labels = labels
    return build


def test_label_build_returns_equal_setups_and_keeps_signature():
    """The wrapper builds the very same Setup as the original, for any headcount and swap."""
    orig = _build(settings={"OM_TP_TARGET_POLICY": 1})
    wrapped = label_build(orig)
    for heads, swap in ((1, False), (9, True)):
        assert wrapped(heads, swap) == orig(heads, swap)


def test_label_build_adds_transfer_to_existing_labels_and_does_not_mutate_them():
    """The wrapper's labels are the original's plus 'transfer'; with none, just 'transfer'."""
    base = {"play_side0": "a"}
    wrapped = label_build(_build(labels=base))
    assert wrapped.labels == {"play_side0": "a", "transfer": RULE_GEOMETRY}
    assert base == {"play_side0": "a"}
    assert label_build(_build(settings={"OM_TP_TARGET_POLICY": 1})).labels == {"transfer": MAGNITUDES}
    assert not set(wrapped.labels) & set(rows._FIXED)


def test_class_is_the_same_for_one_and_nine_enemy_heads():
    """The class does not depend on headcount."""
    for kw in ({}, {"settings": {"OM_TP_TARGET_POLICY": 1}}):
        b = _build(**kw)
        assert transfer_class(b(1, False)) == transfer_class(b(9, False))


def test_labels_reach_fight_row_and_are_deterministic():
    """The labels pass through fight_row's **labels as a 'transfer' cell; two wrappers give the same labels."""
    r = FightResult(outcome="side0", margin=0.5, strength_left=(1.0, 0.0), survivors=(1, 0), heads=(1, 1), ticks=1,
                    first_contact_tick=0, firing=[(0, 1, 1)], firing_unit_seconds=(0.25, 0.25))
    wrapped = label_build(_build())
    row = rows.fight_row(r, **wrapped.labels)
    assert row["transfer"] == RULE_GEOMETRY and list(row)[0] == "transfer"
    assert label_build(_build()).labels == wrapped.labels


# ---------- LAB-REV2-L5 (spec: 2026-10-14-skill-lab-rev2-spec.md::Pieces::L5 owns transfer.py; contract Setup gains firing_arc_deg and cone) ----------
# QUESTION (Architect): the module docstring's own definition is "a tunable number changed or not". The two new Setup fields are tunable numbers
# (DRAFT-firing-arc-deg, DRAFT-aoe-cone-range/-deg/-share): a Setup with firing_arc_deg below 360 or a non-empty cone is MAGNITUDES. Drop these
# three tests if the Architect rules the arc and the cone are geometry.

def test_l5_a_narrowed_firing_arc_is_a_magnitude():
    assert transfer_class(setup(firing_arc_deg=120.0)) == MAGNITUDES
    assert transfer_class(setup(firing_arc_deg=360.0)) == RULE_GEOMETRY          # the default arc changes nothing (negative control)


def test_l5_a_cone_is_a_magnitude_and_an_empty_cone_is_not():
    assert transfer_class(setup(cone={"Vanguard": (300.0, 45.0, 1.0)})) == MAGNITUDES
    assert transfer_class(setup(cone={})) == RULE_GEOMETRY


def test_l5_the_shared_point_and_the_order_style_stay_geometry():
    """Where the units meet and how the orders are issued are layout, not a tunable number."""
    assert transfer_class(setup(point=(100.0, 200.0), orders_per_unit=False)) == RULE_GEOMETRY
