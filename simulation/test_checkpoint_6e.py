import math
import random
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP, FIELD_ATTACK_TIMER, FIELD_ATTACK_RANGE, FIELD_SPEED, FIELD_ABILITY_COOLDOWN, FIELD_ABILITY_ACTIVE, FIELD_ABILITY_DURATION
from damage import update_targeting, resolve_damage
from movement import update_movement
from ability import activate_ability, update_abilities, resolve_barrage, ABILITY_ACTIVE, ABILITY_MAP
from test_maps import open_field

FACTION_A = 0
FACTION_B = 1
DT = config.TACTICAL_TICK_DURATION


def run_until_dead(store, tmap, target_uid, max_ticks=10000):
    rng = random.Random(42)
    for tick in range(max_ticks):
        update_movement(store, tmap, DT)
        update_targeting(store, tmap, rng)
        deaths, _ = resolve_damage(store, tmap, DT)
        update_abilities(store, DT)
        if not store.alive[target_uid]:
            return tick
    return max_ticks


def test_brace():
    print("=" * 70)
    print("  BRACE — Vanguard damage taken braced vs unbraced (200-tick window)")
    print("=" * 70)

    attackers = ["Raider", "Interceptor", "Vanguard", "Warden", "Bombard", "Bastion"]
    print(f"  {'Attacker':<14} {'Unbraced':>10} {'Braced':>10} {'Ratio':>8} {'Status':>8}")
    print(f"  {'-'*14} {'-'*10} {'-'*10} {'-'*8} {'-'*8}")

    all_pass = True
    for attacker_type in attackers:
        dmg_unbraced = _brace_trial(attacker_type, braced=False)
        dmg_braced = _brace_trial(attacker_type, braced=True)
        ratio = dmg_unbraced / dmg_braced if dmg_braced > 0 else float("inf")
        ok = ratio >= 1.5
        if not ok:
            all_pass = False
        print(f"  {attacker_type:<14} {dmg_unbraced:>9.0f} {dmg_braced:>9.0f} {ratio:>7.2f}x {'OK' if ok else 'FAIL':>8}")

    print(f"\n  L8: {'PASS' if all_pass else 'FAIL'} (all ≥ 1.5× damage reduction)")
    return all_pass


def _brace_trial(attacker_type, braced):
    tmap = open_field()
    store = UnitStore()

    vanguard = store.spawn("Vanguard", FACTION_A, 2000.0, 2000.0)
    store.spawn(attacker_type, FACTION_B, 2000.0 + 150.0, 2000.0)

    if braced:
        activate_ability(store, vanguard)
        for _ in range(config.BRACE_WINDUP_TICKS + 1):
            update_abilities(store, DT)

    initial_hp = store.data[vanguard, FIELD_HP]
    rng = random.Random(42)
    for _ in range(200):
        update_movement(store, tmap, DT)
        update_targeting(store, tmap, rng)
        resolve_damage(store, tmap, DT)
        update_abilities(store, DT)

    return max(0.0, initial_hp - store.data[vanguard, FIELD_HP])


def test_rally():
    print(f"\n{'=' * 70}")
    print("  RALLY — Warden heals 10 Vanguards at 50% HP")
    print("=" * 70)

    tmap = open_field()
    store = UnitStore()

    warden = store.spawn("Warden", FACTION_A, 2000.0, 2000.0)
    vanguards = []
    for i in range(10):
        uid = store.spawn("Vanguard", FACTION_A, 2000.0 + (i % 5) * 40.0, 2000.0 + (i // 5) * 40.0)
        store.data[uid, FIELD_HP] = store.data[uid, FIELD_MAX_HP] * 0.5
        vanguards.append(uid)

    hp_before = [store.data[uid, FIELD_HP] for uid in vanguards]
    max_hp = [store.data[uid, FIELD_MAX_HP] for uid in vanguards]

    activate_ability(store, warden)

    hp_after = [store.data[uid, FIELD_HP] for uid in vanguards]

    print(f"  {'Unit':<10} {'HP Before':>10} {'HP After':>10} {'Healed':>10} {'% Max HP':>10}")
    print(f"  {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")

    all_pass = True
    for i, uid in enumerate(vanguards):
        healed = hp_after[i] - hp_before[i]
        pct = healed / max_hp[i] * 100
        ok = pct >= 15.0
        if not ok:
            all_pass = False
        print(f"  Van #{uid:<5} {hp_before[i]:>10.0f} {hp_after[i]:>10.0f} {healed:>10.0f} {pct:>9.1f}%")

    print(f"\n  L9: {'PASS' if all_pass else 'FAIL'} (all ≥ 15% of max HP restored)")
    return all_pass


def test_surge():
    print(f"\n{'=' * 70}")
    print("  SURGE — 3 Raiders vs Bombard, with and without Surge")
    print("=" * 70)

    ticks_no_surge = _surge_trial(use_surge=False)
    ticks_surge = _surge_trial(use_surge=True)

    improvement = 1.0 - (ticks_surge / ticks_no_surge) if ticks_no_surge > 0 else 0.0
    ok = improvement >= 0.30

    print(f"  Without Surge: {ticks_no_surge} ticks ({ticks_no_surge * DT:.1f}s)")
    print(f"  With Surge:    {ticks_surge} ticks ({ticks_surge * DT:.1f}s)")
    print(f"  Improvement:   {improvement * 100:.1f}%")
    print(f"\n  L10: {'PASS' if ok else 'FAIL'} (≥ 30% faster with Surge)")
    return ok


def _surge_trial(use_surge):
    tmap = open_field()
    store = UnitStore()

    raiders = []
    for i in range(3):
        uid = store.spawn("Raider", FACTION_A, 1900.0 + i * 30.0, 2000.0)
        raiders.append(uid)
    bombard = store.spawn("Bombard", FACTION_B, 2100.0, 2000.0)

    rng = random.Random(42)
    for tick in range(10000):
        update_movement(store, tmap, DT)
        update_targeting(store, tmap, rng)

        if use_surge and tick == 0:
            for uid in raiders:
                activate_ability(store, uid)

        deaths, _ = resolve_damage(store, tmap, DT)
        update_abilities(store, DT)

        if not store.alive[bombard]:
            return tick

    return 10000


def test_fortify():
    print(f"\n{'=' * 70}")
    print("  FORTIFY — Bastion zone reduces damage to nearby friendlies")
    print("=" * 70)

    dmg_no_fortify = _fortify_trial(use_fortify=False)
    dmg_fortify = _fortify_trial(use_fortify=True)

    reduction = 1.0 - (dmg_fortify / dmg_no_fortify) if dmg_no_fortify > 0 else 0.0
    ok = reduction >= config.FORTIFY_DAMAGE_REDUCTION * 0.8

    print(f"  Damage taken without Fortify: {dmg_no_fortify:.1f}")
    print(f"  Damage taken with Fortify:    {dmg_fortify:.1f}")
    print(f"  Effective reduction:           {reduction * 100:.1f}%")
    print(f"  Expected:                      ~{config.FORTIFY_DAMAGE_REDUCTION * 100:.0f}%")
    print(f"\n  Fortify: {'PASS' if ok else 'FAIL'}")
    return ok


def _fortify_trial(use_fortify):
    tmap = open_field()
    store = UnitStore()

    bastion = store.spawn("Bastion", FACTION_A, 2000.0, 2000.0)
    vanguard = store.spawn("Vanguard", FACTION_A, 2020.0, 2000.0)
    attacker = store.spawn("Raider", FACTION_B, 2000.0 + 150.0, 2000.0)

    if use_fortify:
        activate_ability(store, bastion)

    initial_hp = store.data[vanguard, FIELD_HP]
    rng = random.Random(42)
    for tick in range(200):
        update_movement(store, tmap, DT)
        update_targeting(store, tmap, rng)
        resolve_damage(store, tmap, DT)
        update_abilities(store, DT)

    return initial_hp - store.data[vanguard, FIELD_HP]


def test_intercept():
    print(f"\n{'=' * 70}")
    print("  INTERCEPT — Interceptor triggers on nearby enemy Strike")
    print("=" * 70)

    tmap = open_field()
    store = UnitStore()

    interceptor = store.spawn("Interceptor", FACTION_A, 2000.0, 2000.0)
    raider = store.spawn("Raider", FACTION_B, 2000.0 + config.INTERCEPT_DETECTION_RADIUS - 10.0, 2000.0)

    triggered = False
    rng = random.Random(42)
    for tick in range(100):
        update_movement(store, tmap, DT)
        update_targeting(store, tmap, rng)
        resolve_damage(store, tmap, DT)
        update_abilities(store, DT)
        if store.data[interceptor, FIELD_ABILITY_COOLDOWN] > 0:
            triggered = True
            break

    cooldown_set = store.data[interceptor, FIELD_ABILITY_COOLDOWN] > 0
    print(f"  Trigger detected: {triggered}")
    print(f"  Cooldown set:     {cooldown_set}")
    print(f"  Target locked:    {store.auto_engage_target[interceptor] == raider}")
    print(f"\n  Intercept: {'PASS' if triggered else 'FAIL'}")
    return triggered


def test_barrage():
    print(f"\n{'=' * 70}")
    print("  BARRAGE — Bombard fires concentrated volley at clustered targets")
    print("=" * 70)

    tmap = open_field()
    store = UnitStore()

    bombard = store.spawn("Bombard", FACTION_A, 2000.0, 2000.0)
    targets = []
    for i in range(5):
        uid = store.spawn("Vanguard", FACTION_B, 2400.0 + (i % 3) * 20.0, 2000.0 + (i // 3) * 20.0)
        targets.append(uid)

    store.auto_engage_target[bombard] = targets[0]
    activate_ability(store, bombard)

    telegraph_ticks = 0
    barrage_fired = False
    rng = random.Random(42)

    hp_before = {uid: store.data[uid, FIELD_HP] for uid in targets}

    for tick in range(100):
        update_movement(store, tmap, DT)
        update_targeting(store, tmap, rng)
        resolve_damage(store, tmap, DT)
        barrage_events = update_abilities(store, DT)
        if barrage_events:
            resolve_barrage(store, barrage_events)
            barrage_fired = True
            telegraph_ticks = tick + 1  # tick is 0-indexed; elapsed ticks = tick + 1
            break

    hp_after = {uid: store.data[uid, FIELD_HP] for uid in targets}
    units_hit = sum(1 for uid in targets if hp_after[uid] < hp_before[uid])
    total_dmg = sum(hp_before[uid] - hp_after[uid] for uid in targets)

    print(f"  Telegraph delay: {telegraph_ticks} ticks ({telegraph_ticks * DT:.1f}s)")
    print(f"  Expected delay:  {config.BARRAGE_TELEGRAPH_TICKS} ticks ({config.BARRAGE_TELEGRAPH_TICKS * DT:.1f}s)")
    print(f"  Barrage fired:   {barrage_fired}")
    print(f"  Units hit:       {units_hit}/{len(targets)}")
    print(f"  Total damage:    {total_dmg:.1f}")

    ok = barrage_fired and units_hit > 0
    print(f"\n  Barrage: {'PASS' if ok else 'FAIL'}")
    return ok


def test_warden_aura():
    print(f"\n{'=' * 70}")
    print("  WARDEN AURA — Damage reduction + repair for nearby friendlies")
    print("=" * 70)

    dmg_no_aura = _aura_damage_trial(with_warden=False)
    dmg_with_aura = _aura_damage_trial(with_warden=True)

    reduction = 1.0 - (dmg_with_aura / dmg_no_aura) if dmg_no_aura > 0 else 0.0

    print(f"  Damage reduction test (Warden out of combat range, within aura range):")
    print(f"  Damage taken without Warden: {dmg_no_aura:.1f}")
    print(f"  Damage taken with Warden:    {dmg_with_aura:.1f}")
    print(f"  Effective reduction:          {reduction * 100:.1f}%")
    print(f"  Expected:                     ~{config.WARDEN_AURA_DAMAGE_REDUCTION * 100:.0f}%")

    tmap = open_field()
    store = UnitStore()
    warden = store.spawn("Warden", FACTION_A, 2000.0, 2000.0)
    vanguard = store.spawn("Vanguard", FACTION_A, 2020.0, 2000.0)
    store.data[vanguard, FIELD_HP] = store.data[vanguard, FIELD_MAX_HP] * 0.5
    initial_hp = store.data[vanguard, FIELD_HP]

    for _ in range(100):
        update_abilities(store, DT)

    repaired = store.data[vanguard, FIELD_HP] - initial_hp
    print(f"\n  Repair test (100 ticks, no combat):")
    print(f"  HP repaired: {repaired:.1f}")
    print(f"  Expected:    ~{config.WARDEN_AURA_REPAIR_RATE * 100:.1f}")

    reduction_ok = reduction >= config.WARDEN_AURA_DAMAGE_REDUCTION * 0.5
    repair_ok = repaired > 0
    ok = reduction_ok and repair_ok
    if not reduction_ok:
        print(f"\n  WARNING: reduction {reduction*100:.1f}% is below 50% of expected {config.WARDEN_AURA_DAMAGE_REDUCTION*100:.0f}%")
    print(f"\n  Warden Aura: {'PASS' if ok else 'FAIL'}")
    return ok


def _aura_damage_trial(with_warden):
    tmap = open_field()
    store = UnitStore()

    # Vanguard at center, Raider 150 wu to the right (within Raider's 200 attack range)
    vanguard = store.spawn("Vanguard", FACTION_A, 2000.0, 2000.0)
    store.spawn("Raider", FACTION_B, 2150.0, 2000.0)

    if with_warden:
        # Warden 280 wu left of Vanguard: within 300 aura range of Vanguard,
        # but 430 wu from Raider — outside Warden's 350 attack range.
        # Raider is also 430 wu from Warden — outside Raider's 200 attack range.
        # So Warden can't fight the Raider and Raider can't fight the Warden.
        store.spawn("Warden", FACTION_A, 1720.0, 2000.0)

    initial_hp = store.data[vanguard, FIELD_HP]
    rng = random.Random(42)
    for _ in range(200):
        update_movement(store, tmap, DT)
        update_targeting(store, tmap, rng)
        resolve_damage(store, tmap, DT)
        update_abilities(store, DT)

    # Subtract aura repair to isolate the damage reduction effect
    repair = 0.0
    if with_warden:
        repair = config.WARDEN_AURA_REPAIR_RATE * 200
    raw_damage = initial_hp - store.data[vanguard, FIELD_HP] + repair
    return raw_damage


def run():
    print("=" * 70)
    print("CHECKPOINT 6E — Abilities (Isolation Tests)")
    print("=" * 70)

    results = {}
    results["Brace (L8)"] = test_brace()
    results["Rally (L9)"] = test_rally()
    results["Surge (L10)"] = test_surge()
    results["Fortify"] = test_fortify()
    results["Intercept"] = test_intercept()
    results["Barrage"] = test_barrage()
    results["Warden Aura"] = test_warden_aura()

    print(f"\n{'=' * 70}")
    print("  SUMMARY")
    print("=" * 70)
    for name, passed in results.items():
        print(f"  {name:<20} {'PASS' if passed else 'FAIL'}")

    total_pass = sum(1 for v in results.values() if v)
    print(f"\n  {total_pass}/{len(results)} tests passed")
    print("\nCheckpoint 6E complete.")


if __name__ == "__main__":
    run()
