import math
import random
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP, FIELD_ATTACK_TIMER, FIELD_ATTACK_RANGE
from damage import update_targeting, resolve_damage
from movement import update_movement, apply_group_move
from test_maps import open_field

FACTION_A = 0
FACTION_B = 1
DT = config.TACTICAL_TICK_DURATION


def spawn_mixed_formation(store, faction, count, center_x, center_y, facing_x, rng):
    ratio = {"Vanguard": 0.25, "Warden": 0.15, "Raider": 0.15,
             "Interceptor": 0.15, "Bombard": 0.15, "Bastion": 0.15}

    role_counts = {}
    placed = 0
    for ut, frac in ratio.items():
        n = max(1, round(count * frac))
        if placed + n > count:
            n = count - placed
        role_counts[ut] = n
        placed += n
        if placed >= count:
            break

    sign = 1.0 if facing_x > center_x else -1.0

    row_spacing = 50.0
    col_spacing = 50.0

    rows = {
        "Vanguard":    0,
        "Warden":      1,
        "Raider":      2,
        "Interceptor": 2,
        "Bombard":     3,
        "Bastion":     4,
    }

    uids = []
    for ut, n in role_counts.items():
        row = rows[ut]
        row_x = center_x + sign * row * row_spacing
        start_y = center_y - (n - 1) * col_spacing / 2.0
        for i in range(n):
            jx = rng.uniform(-10.0, 10.0)
            jy = rng.uniform(-10.0, 10.0)
            x = row_x + jx
            y = start_y + i * col_spacing + jy
            uid = store.spawn(ut, faction, x, y)
            uids.append(uid)

    return uids


def run():
    print("=" * 70)
    print("6D DEBUG — 50v50 Mirror, Seed 1, Per-Tick Diagnostics")
    print("=" * 70)

    seed = 1
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()
    engine_rng = random.Random(seed)

    uids_a = spawn_mixed_formation(store, FACTION_A, 50, 1600.0, 2000.0, 2200.0, rng)
    uids_b = spawn_mixed_formation(store, FACTION_B, 50, 2200.0, 2000.0, 1600.0, rng)

    apply_group_move(store, uids_a, 2000.0, 2000.0)
    apply_group_move(store, uids_b, 2000.0, 2000.0)

    print(f"\n  {'Tick':>5} {'Time':>6} {'A alive':>7} {'B alive':>7} "
          f"{'A HP':>8} {'B HP':>8}")
    print(f"  {'-'*5} {'-'*6} {'-'*7} {'-'*7} {'-'*8} {'-'*8}")

    for tick in range(3000):
        update_movement(store, tmap, DT)
        update_targeting(store, tmap, engine_rng)
        deaths, kill_sources = resolve_damage(store, tmap, DT)

        alive_a = len(store.active_ids_for_faction(FACTION_A))
        alive_b = len(store.active_ids_for_faction(FACTION_B))

        if tick % 100 == 0:
            hp_a = sum(store.data[uid, FIELD_HP] for uid in store.active_ids_for_faction(FACTION_A))
            hp_b = sum(store.data[uid, FIELD_HP] for uid in store.active_ids_for_faction(FACTION_B))
            print(f"  {tick:>5} {tick*DT:>5.1f}s {alive_a:>7} {alive_b:>7} "
                  f"{hp_a:>8.0f} {hp_b:>8.0f}")

        if deaths:
            for dead_uid in deaths:
                dead_faction = "A" if store.faction[dead_uid] == FACTION_A else "B"
                dead_type = store.unit_type[dead_uid]
                killer_uid = kill_sources.get(dead_uid, -1)
                if killer_uid >= 0:
                    killer_faction = "A" if store.faction[killer_uid] == FACTION_A else "B"
                    killer = f"{killer_faction}:{store.unit_type[killer_uid]}(#{killer_uid})"
                else:
                    killer = "unknown"
                print(f"         KILL tick {tick} ({tick*DT:.1f}s): "
                      f"faction {dead_faction} {dead_type}(#{dead_uid}) killed by {killer}")

        if alive_a == 0 or alive_b == 0:
            winner = "A" if alive_a > 0 else "B"
            print(f"\n  ENGAGEMENT OVER at tick {tick} ({tick*DT:.1f}s)")
            print(f"  Winner: {winner} | A survivors: {alive_a} | B survivors: {alive_b}")
            break

    unknown_count = sum(1 for d in deaths if kill_sources.get(d, -1) < 0) if deaths else 0
    print(f"\n  Unknown kills in final tick: {unknown_count}")


if __name__ == "__main__":
    run()
