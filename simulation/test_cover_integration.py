from cover_integration_fixture import build_cover_apex_scenario
from unit import FIELD_X, FIELD_Y, FIELD_HP
from fog_of_war import compute_visibility
from damage import resolve_damage


def test_integration_cover_apex_full_scenario():
    tm, store, attackers, defenders = build_cover_apex_scenario()

    assert len(attackers) == 2
    assert len(defenders) == 1
    defender = defenders[0]
    atk1, atk2 = attackers[0], attackers[1]

    assert tm.is_in_cover(500, 500) is True
    assert tm.is_in_cover(200, 500) is False
    assert tm.is_in_cover(800, 500) is False

    vis = compute_visibility(store, tm)

    assert defender not in vis[atk1], (
        "Attacker 1 should not see defender hiding in cover"
    )
    assert defender not in vis[atk2], (
        "Attacker 2 should not see defender hiding in cover"
    )

    assert atk1 in vis[defender] or atk2 in vis[defender], (
        "Defender (in cover) should see at least one attacker outside cover"
    )

    store.auto_engage_target[atk1] = defender
    hp_before = store.data[defender, FIELD_HP]
    resolve_damage(store, tm, dt=1.0)
    hp_after = store.data[defender, FIELD_HP]
    assert hp_after == hp_before, (
        f"Hidden defender took damage from attacker 1: before={hp_before} after={hp_after}"
    )

    store.auto_engage_target[atk1] = -1
    store.auto_engage_target[defender] = atk1
    hp_before_atk = store.data[atk1, FIELD_HP]
    resolve_damage(store, tm, dt=1.0)
    hp_after_atk = store.data[atk1, FIELD_HP]
    assert hp_after_atk < hp_before_atk, (
        f"Defender's return fire dealt no damage: before={hp_before_atk} after={hp_after_atk}"
    )

    store.data[defender, FIELD_X] = 700.0
    store.data[defender, FIELD_Y] = 500.0
    assert tm.is_in_cover(700, 500) is False

    vis2 = compute_visibility(store, tm)
    assert defender in vis2[atk1] or defender in vis2[atk2], (
        "Defender out of cover should be visible to at least one attacker"
    )

    store.auto_engage_target[atk1] = defender
    store.auto_engage_target[atk2] = defender
    store.data[atk1, 12] = 0.0  # FIELD_ATTACK_TIMER reset
    store.data[atk2, 12] = 0.0
    hp_before_def = store.data[defender, FIELD_HP]
    resolve_damage(store, tm, dt=1.0)
    hp_after_def = store.data[defender, FIELD_HP]
    assert hp_after_def < hp_before_def, (
        f"Exposed defender took no damage: before={hp_before_def} after={hp_after_def}"
    )
