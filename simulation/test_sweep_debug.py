import random
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP
from tactical_engine import TacticalEngine
from movement import apply_group_move
from test_maps import open_field

FACTION_A = 0
FACTION_B = 1
DT = config.TACTICAL_TICK_DURATION

SIEGE_HP_LEVELS = [
    ("S1", 900, 1800),
    ("S2", 750, 1500),
]

CATEGORY_UNITS = {
    "Strike": ["Raider", "Interceptor"],
    "Siege":  ["Bombard", "Bastion"],
}


def build_force(store, category, faction_id, start_x, start_y, rng, count=10):
    types = CATEGORY_UNITS[category]
    half = count // 2
    roster = [types[0]] * half + [types[1]] * (count - half)
    rng.shuffle(roster)
    uids = []
    for i, ut in enumerate(roster):
        x = start_x + (i % 5) * 60.0
        y = start_y + (i // 5) * 60.0
        uid = store.spawn(ut, faction_id, x, y)
        uids.append(uid)
    return uids


def run_strike_vs_siege(seed):
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()
    uids_a = build_force(store, "Strike", FACTION_A, 1700.0, 1850.0, rng)
    uids_b = build_force(store, "Siege", FACTION_B, 2100.0, 1850.0, rng)
    apply_group_move(store, uids_a, 2000.0, 2000.0)
    apply_group_move(store, uids_b, 2000.0, 2000.0)

    engine = TacticalEngine(tmap, store, seed=seed)
    engine.run(10000)

    dur = engine.tick * DT
    winner = engine.get_winner()
    surv_a = len(engine.get_survivors(FACTION_A))
    surv_b = len(engine.get_survivors(FACTION_B))
    winner_label = "Strike" if winner == FACTION_A else ("Siege" if winner == FACTION_B else "Draw")
    return dur, winner_label, surv_a, surv_b


if __name__ == "__main__":
    print("Sweep debug: Strike vs Siege with varying Siege HP")
    print("=" * 70)

    for level, bomb_hp, bast_hp in SIEGE_HP_LEVELS:
        config.UNIT_STATS["Bombard"]["hp"] = bomb_hp
        config.UNIT_STATS["Bastion"]["hp"] = bast_hp

        print(f"\n  {level}: Bombard HP={bomb_hp}, Bastion HP={bast_hp}")
        print(f"  DEBUG: config reads Bombard={config.UNIT_STATS['Bombard']['hp']}, "
              f"Bastion={config.UNIT_STATS['Bastion']['hp']}")

        for seed in [1, 2, 3]:
            dur, winner, sa, sb = run_strike_vs_siege(seed)
            print(f"    seed {seed}: {dur:.1f}s, winner={winner}, "
                  f"Strike surv={sa}, Siege surv={sb}")
