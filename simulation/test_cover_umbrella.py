"""Wave 2.5 Cover-LOS Rework umbrella test.

Encodes the top-level acceptance criteria from `docs/legacy/test_specs/cover_los_rework_spec.md`.
Initially RED. Goes GREEN only after all 7 leaves (L1-L7) merge.

DO NOT EDIT leaf-by-leaf. This is the parent-owned end-to-end gate.
"""

import os
import re

import pytest

import tactical_map
from tactical_map import TacticalMap


# ---------------------------------------------------------------------------
# A. Cover polygon data structure (L2)
# ---------------------------------------------------------------------------


def test_umbrella_a_cover_polygon_class_exists():
    assert hasattr(tactical_map, "CoverPolygon"), (
        "L2 not landed: tactical_map.CoverPolygon class must exist"
    )


def test_umbrella_a_tactical_map_exposes_cover_polygons():
    tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
    assert hasattr(tm, "cover_polygons"), "L2 not landed: TacticalMap.cover_polygons"
    assert isinstance(tm.cover_polygons, list)


def test_umbrella_a_is_in_cover_api():
    tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
    assert hasattr(tm, "is_in_cover"), "L2 not landed: TacticalMap.is_in_cover"
    # Empty map: no point is in cover.
    assert tm.is_in_cover(500, 500) is False


def test_umbrella_a_cover_polygon_containing_api():
    tm = TacticalMap(width=1000, height=1000, gradient_sources=[], spine_nodes=[])
    assert hasattr(tm, "cover_polygon_containing"), (
        "L2 not landed: TacticalMap.cover_polygon_containing"
    )
    assert tm.cover_polygon_containing(500, 500) is None


# ---------------------------------------------------------------------------
# B. gradient_placer cover-source -> polygon conversion (L3)
# ---------------------------------------------------------------------------


def test_umbrella_b_gradient_placer_emits_polygons():
    """After L3, a map generated from a layout with cover at chokepoints
    contains >= 1 cover polygon on the TacticalMap rather than only gradient
    field samples."""
    from gradient_placer import place_cover_polygons
    from layout_instantiator import InstantiatedLayout
    from tactical_map import SpineNode

    inst = InstantiatedLayout(
        layout_id="umbrella_b_test",
        canvas_size="medium",
        canvas_w=1000,
        canvas_h=1000,
        seed=0,
        spine_nodes=[SpineNode(position=(500.0, 500.0), node_type="chokepoint")],
        node_id_map={},
        edges=[],
    )
    polys = place_cover_polygons(inst)
    assert len(polys) >= 1, (
        "L3 not landed: chokepoint layout should emit >= 1 CoverPolygon"
    )
    assert polys[0].vertices, "L3 not landed: CoverPolygon must have vertices"


# ---------------------------------------------------------------------------
# C. fog_of_war symmetric-blind (L4)
# ---------------------------------------------------------------------------


def _umbrella_c_make_map():
    from tactical_map import CoverPolygon
    poly1 = CoverPolygon(1, [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)])
    poly2 = CoverPolygon(2, [(200.0, 200.0), (300.0, 200.0), (300.0, 300.0), (200.0, 300.0)])
    return TacticalMap(
        width=1000,
        height=1000,
        gradient_sources=[],
        spine_nodes=[],
        cover_polygons=[poly1, poly2],
    )


def _umbrella_c_spawn(store, faction_id, x, y, sensor_radius=2000.0):
    from unit import FIELD_X, FIELD_Y, FIELD_LAYER, FIELD_SENSOR_RADIUS
    uid = store.count
    store.count += 1
    store.data[uid, FIELD_X] = x
    store.data[uid, FIELD_Y] = y
    store.data[uid, FIELD_LAYER] = 0
    store.data[uid, FIELD_SENSOR_RADIUS] = sensor_radius
    store.faction[uid] = faction_id
    store.alive[uid] = True
    return uid


def test_umbrella_c_symmetric_blind_target_in_cover_observer_outside():
    """Target inside cover polygon, observer outside that polygon, otherwise
    in sensor range -> target NOT in observer's visible set."""
    from unit import UnitStore
    from fog_of_war import compute_visibility
    tm = _umbrella_c_make_map()
    store = UnitStore()
    observer = _umbrella_c_spawn(store, faction_id=0, x=500.0, y=500.0)
    target = _umbrella_c_spawn(store, faction_id=1, x=50.0, y=50.0)
    vis = compute_visibility(store, tm)
    assert target not in vis[observer], (
        "L4 not landed: observer outside cover should be blind to target in cover poly"
    )


def test_umbrella_c_same_polygon_units_see_each_other():
    """Target and observer in the SAME cover polygon -> visible to each other."""
    from unit import UnitStore
    from fog_of_war import compute_visibility
    tm = _umbrella_c_make_map()
    store = UnitStore()
    a = _umbrella_c_spawn(store, faction_id=0, x=10.0, y=10.0)
    b = _umbrella_c_spawn(store, faction_id=1, x=50.0, y=50.0)
    vis = compute_visibility(store, tm)
    assert b in vis[a], "L4 not landed: same-polygon units must see each other (a→b)"
    assert a in vis[b], "L4 not landed: same-polygon units must see each other (b→a)"


def test_umbrella_c_different_polygons_blind():
    """Target in cover poly 1, observer in cover poly 2 -> not visible."""
    from unit import UnitStore
    from fog_of_war import compute_visibility
    tm = _umbrella_c_make_map()
    store = UnitStore()
    a = _umbrella_c_spawn(store, faction_id=0, x=10.0, y=10.0)
    b = _umbrella_c_spawn(store, faction_id=1, x=250.0, y=250.0)
    vis = compute_visibility(store, tm)
    assert b not in vis[a], "L4 not landed: different-polygon units must be blind (a→b)"
    assert a not in vis[b], "L4 not landed: different-polygon units must be blind (b→a)"


# ---------------------------------------------------------------------------
# D. damage.py visibility-gate + no (1.0 - cover) multiplier (L5)
# ---------------------------------------------------------------------------


def test_umbrella_d_damage_module_has_no_cover_multiplier():
    """Regression guard: damage.py source must not contain a (1.0 - cover) term."""
    here = os.path.dirname(__file__)
    damage_path = os.path.join(here, "damage.py")
    with open(damage_path, "r", encoding="utf-8") as f:
        src = f.read()
    # Tolerate the *string* "(1.0 - cover" inside a comment that explicitly
    # marks the removal, but disallow any executable expression form.
    pattern = re.compile(r"\(\s*1\.0\s*-\s*cover[^)]*\)")
    matches = pattern.findall(src)
    # Strip any matches that appear on a commented line (start of trimmed line == '#').
    real_matches = []
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if pattern.search(line):
            real_matches.append(line)
    assert not real_matches, (
        f"L5 not landed: damage.py still contains (1.0 - cover) multiplier:\n"
        + "\n".join(real_matches)
    )


def test_umbrella_d_attack_at_hidden_target_zero_damage():
    """Attacker fires at target that is not in attacker's visible set ->
    no damage applied. Visibility gate enforced in damage.py."""
    from tactical_map import CoverPolygon
    from unit import (
        UnitStore,
        FIELD_X, FIELD_Y, FIELD_LAYER, FIELD_HP, FIELD_MAX_HP,
        FIELD_BASE_DAMAGE, FIELD_ATTACK_INTERVAL, FIELD_ATTACK_RANGE,
        FIELD_SENSOR_RADIUS, FIELD_AOE_RADIUS, FIELD_ATTACK_TIMER,
        CATEGORY_STRIKE,
    )
    from damage import resolve_damage

    poly = CoverPolygon(1, [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)])
    tm = TacticalMap(
        width=1000, height=1000,
        gradient_sources=[], spine_nodes=[],
        cover_polygons=[poly],
    )
    store = UnitStore()

    def _spawn(faction_id, x, y):
        uid = store.count
        store.count += 1
        store.data[uid, FIELD_X] = x
        store.data[uid, FIELD_Y] = y
        store.data[uid, FIELD_LAYER] = 0
        store.data[uid, FIELD_HP] = 1000.0
        store.data[uid, FIELD_MAX_HP] = 1000.0
        store.data[uid, FIELD_BASE_DAMAGE] = 50.0
        store.data[uid, FIELD_ATTACK_INTERVAL] = 1.0
        store.data[uid, FIELD_ATTACK_RANGE] = 2000.0
        store.data[uid, FIELD_SENSOR_RADIUS] = 2000.0
        store.data[uid, FIELD_AOE_RADIUS] = 0.0
        store.data[uid, FIELD_ATTACK_TIMER] = 0.0
        store.faction[uid] = faction_id
        store.category[uid] = CATEGORY_STRIKE
        store.alive[uid] = True
        return uid

    attacker = _spawn(0, 500.0, 500.0)
    target = _spawn(1, 50.0, 50.0)
    store.auto_engage_target[attacker] = target

    hp_before = store.data[target, FIELD_HP]
    resolve_damage(store, tm, dt=1.0)
    hp_after = store.data[target, FIELD_HP]

    assert hp_after == hp_before, (
        f"L5 not landed: hidden target took damage: before={hp_before} after={hp_after}"
    )


# ---------------------------------------------------------------------------
# E. Bible spec aligned with new design (L1)
# ---------------------------------------------------------------------------


def test_umbrella_e_bible_combat_no_damage_mult_in_formula():
    """docs/bible_history/bible_2_00_combat.md must not contain the (1.0 - cover_density) damage
    formula after L1 lands."""
    here = os.path.dirname(__file__)
    bible_path = os.path.join(here, "..", "docs", "bible", "docs/bible_history/bible_2_00_combat.md")
    with open(bible_path, "r", encoding="utf-8") as f:
        text = f.read()
    assert "(1.0 - cover_density" not in text, (
        "L1 not landed: docs/bible_history/bible_2_00_combat.md still contains "
        "'(1.0 - cover_density)' damage formula language"
    )


def test_umbrella_e_bible_world_cover_describes_los_block():
    """docs/bible_history/bible_2_00_world.md cover_density definition must include LOS-block language
    after L1 lands (the paragraph defining cover_density mentions LOS / blocks
    sight). The current spec defines cover as damage-reduction, not LOS."""
    here = os.path.dirname(__file__)
    bible_path = os.path.join(here, "..", "docs", "bible", "docs/bible_history/bible_2_00_world.md")
    with open(bible_path, "r", encoding="utf-8") as f:
        text = f.read()
    # Find the cover_density definition paragraph.
    # Pattern: starts at backticked `cover_density`, take next ~600 chars.
    m = re.search(r"`cover_density`[\s\S]{0,600}", text)
    assert m is not None, "docs/bible_history/bible_2_00_world.md cover_density paragraph not found"
    cover_paragraph = m.group(0).lower()
    assert (
        "line of sight" in cover_paragraph
        or "line-of-sight" in cover_paragraph
        or "los" in cover_paragraph
        or "blocks sight" in cover_paragraph
        or "blocks vision" in cover_paragraph
    ), (
        "L1 not landed: docs/bible_history/bible_2_00_world.md cover_density paragraph must describe "
        "LOS / vision blocking, not damage reduction"
    )
    assert "reduces incoming damage" not in cover_paragraph, (
        "L1 not landed: docs/bible_history/bible_2_00_world.md cover_density paragraph still says "
        "'reduces incoming damage' (damage-multiplier language must be removed)"
    )


# ---------------------------------------------------------------------------
# F. Integration scenario (L7)
# ---------------------------------------------------------------------------


def test_umbrella_f_integration_cover_blocks_fire():
    """Apex scenario: 2 attackers + 1 defender behind cover poly. Attackers
    cannot see defender (symmetric blind). Defender takes 0 damage. Defender
    walks out of cover -> attackers see + damage applied."""
    from cover_integration_fixture import build_cover_apex_scenario
    from fog_of_war import compute_visibility
    from damage import resolve_damage
    from unit import FIELD_X, FIELD_Y, FIELD_HP

    tm, store, attackers, defenders = build_cover_apex_scenario()
    defender = defenders[0]

    # Symmetric blind: attackers cannot see defender in cover.
    vis = compute_visibility(store, tm)
    for atk in attackers:
        assert defender not in vis[atk], (
            "L7 not landed: attacker outside cover should be blind to defender in cover"
        )
        store.auto_engage_target[atk] = defender

    # Attackers fire at hidden defender -> 0 damage.
    hp_before = store.data[defender, FIELD_HP]
    resolve_damage(store, tm, dt=1.0)
    assert store.data[defender, FIELD_HP] == hp_before, (
        "L7 not landed: hidden defender took damage from blind attackers"
    )

    # Defender walks out of cover -> attackers see + damage applies.
    store.data[defender, FIELD_X] = 900.0
    store.data[defender, FIELD_Y] = 500.0
    vis2 = compute_visibility(store, tm)
    assert any(defender in vis2[atk] for atk in attackers), (
        "L7 not landed: defender out of cover should be visible to attackers"
    )
    hp_mid = store.data[defender, FIELD_HP]
    resolve_damage(store, tm, dt=1.0)
    assert store.data[defender, FIELD_HP] < hp_mid, (
        "L7 not landed: visible defender should take damage"
    )
