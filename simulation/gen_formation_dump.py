"""
Generate a sim_viewer dump for formation movement (Steps 3–5).

Three scenarios run back-to-back in the same dump:
  - ticks   1–300:  FORMATION OFF  plain_move  (faction 0=Strike blue,  1=Line grey)
  - ticks 301–600:  FORMATION ON   plain_move  (faction 2=Strike green, 3=Line grey)
  - ticks 601–950:  FORMATION ON   attack_move (faction 4=Strike orange, 5=Line red)
                    Strike marches into Line — engagement fires on contact

Usage:
    python3 gen_formation_dump.py          (writes /tmp/formation_test.jsonl)
    python3 sim_viewer.py /tmp/formation_test.jsonl
"""

import random
import time
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP, FIELD_LAYER, FIELD_ABILITY_ACTIVE
from damage import resolve_damage, update_targeting
from movement import update_movement, apply_group_move
from ability import update_abilities, resolve_barrage
from fog_of_war import update_fog_timers
from command import Command, CommandQueue, process_commands
from sim_logger import SimLogger, config_snapshot
from test_maps import chokepoint

OUT = "/tmp/formation_test.jsonl"
TARGET_X = 2000.0
TARGET_Y = 1610.0
TICKS = 300
ATTACK_TICKS = 350
DT = config.TACTICAL_TICK_DURATION


def _spawn_strike(store, faction, rng):
    uids = []
    spacing = 55.0
    center_x, center_y = 2000.0, 2900.0
    start_x = center_x - 9 * spacing / 2.0
    for i in range(10):
        ut = "Raider" if i % 2 == 0 else "Interceptor"
        x = start_x + i * spacing + rng.uniform(-10, 10)
        y = center_y + rng.uniform(-15, 15)
        uids.append(store.spawn(ut, faction, x, y))
    return uids


def _spawn_line(store, faction, rng):
    uids = []
    for i in range(10):
        ut = "Vanguard" if i % 3 != 2 else "Warden"
        x = 2000.0 + (i % 5) * 40.0 + rng.uniform(-15, 15)
        y = 1100.0 + (i // 5) * 40.0 + rng.uniform(-15, 15)
        uids.append(store.spawn(ut, faction, x, y))
    return uids


def run_scenario(store, strike_uids, line_uids, use_formation, tmap, tick_offset, logger):
    rng = random.Random(1)

    if use_formation:
        config.FORMATION_MOVE_ENABLED = True
        apply_group_move(store, strike_uids, TARGET_X, TARGET_Y, tmap)
    else:
        config.FORMATION_MOVE_ENABLED = False
        for uid in strike_uids:
            store.set_move_target(uid, TARGET_X, TARGET_Y)

    for uid in strike_uids:
        if store.alive[uid]:
            store.plain_moving[uid] = True

    for t in range(TICKS):
        t0 = time.perf_counter()
        update_targeting(store, tmap, rng)
        dt_tgt = time.perf_counter() - t0

        t0 = time.perf_counter()
        update_movement(store, tmap, DT)
        dt_mov = time.perf_counter() - t0

        resolve_damage(store, tmap, DT)
        be = update_abilities(store, DT)
        if be:
            resolve_barrage(store, be)
        update_fog_timers(store)

        tick = tick_offset + t + 1
        logger.log_tick(tick, store, [], {
            "targeting": dt_tgt, "movement": dt_mov,
            "abilities": 0.0, "damage": 0.0, "fog": 0.0, "commands": 0.0,
        })

    config.FORMATION_MOVE_ENABLED = False


def run_attack_move_scenario(tmap, tick_offset, logger):
    """Scenario C: formation ON, attack_move — Strike marches into Line."""
    config.FORMATION_MOVE_ENABLED = True
    store = UnitStore()
    rng = random.Random(1)

    strike_uids = _spawn_strike(store, 4, rng)   # orange
    line_uids   = _spawn_line(store, 5, rng)     # red

    queue = CommandQueue()
    queue.add(Command(tick=0, type="attack_move", unit_ids=strike_uids,
                      params={"target_x": 2000.0, "target_y": 1100.0}))

    sim_rng = random.Random(1)
    deaths_all = []

    for t in range(ATTACK_TICKS):
        process_commands(queue, store, t)

        t0 = time.perf_counter()
        update_targeting(store, tmap, sim_rng)
        dt_tgt = time.perf_counter() - t0

        t0 = time.perf_counter()
        update_movement(store, tmap, DT)
        dt_mov = time.perf_counter() - t0

        deaths, _ = resolve_damage(store, tmap, DT)
        be = update_abilities(store, DT)
        if be:
            resolve_barrage(store, be)
        update_fog_timers(store)
        deaths_all.extend(deaths)

        tick = tick_offset + t + 1
        logger.log_tick(tick, store, deaths, {
            "targeting": dt_tgt, "movement": dt_mov,
            "abilities": 0.0, "damage": 0.0, "fog": 0.0, "commands": 0.0,
        })

        alive_factions = {store.faction[u] for u in range(store.count) if store.alive[u]}
        if len(alive_factions) <= 1:
            # Pad remaining ticks with final state so scrubber length is consistent
            for remaining in range(t + 1, ATTACK_TICKS):
                logger.log_tick(tick_offset + remaining + 1, store, [], {
                    "targeting": 0.0, "movement": 0.0,
                    "abilities": 0.0, "damage": 0.0, "fog": 0.0, "commands": 0.0,
                })
            break

    config.FORMATION_MOVE_ENABLED = False


def main():
    tmap = chokepoint()

    factions = {
        0: ("Strike (OFF)",       "#4f7be8"),
        1: ("Line (OFF)",         "#555555"),
        2: ("Strike (ON)",        "#22c55e"),
        3: ("Line (ON)",          "#555555"),
        4: ("Strike (atk_move)",  "#f97316"),
        5: ("Line (defending)",   "#ef4444"),
    }
    logger = SimLogger(OUT, "formation_baseline", tmap, factions, config_snapshot())

    # --- Scenario A: formation OFF, plain_move (factions 0, 1) ---
    store_a = UnitStore()
    rng_a = random.Random(1)
    strike_a = _spawn_strike(store_a, 0, rng_a)
    line_a = _spawn_line(store_a, 1, rng_a)
    print("Running scenario A: formation OFF, plain_move …")
    run_scenario(store_a, strike_a, line_a, False, tmap, tick_offset=0, logger=logger)

    # --- Scenario B: formation ON, plain_move (factions 2, 3) ---
    store_b = UnitStore()
    rng_b = random.Random(1)
    strike_b = _spawn_strike(store_b, 2, rng_b)
    line_b = _spawn_line(store_b, 3, rng_b)
    print("Running scenario B: formation ON,  plain_move …")
    run_scenario(store_b, strike_b, line_b, True, tmap, tick_offset=TICKS, logger=logger)

    # --- Scenario C: formation ON, attack_move (factions 4, 5) ---
    print("Running scenario C: formation ON,  attack_move into Line …")
    run_attack_move_scenario(tmap, tick_offset=TICKS * 2, logger=logger)

    total = TICKS * 2 + ATTACK_TICKS
    logger.close()
    print(f"\nWrote {OUT}  ({total} ticks total)")
    print()
    print("Launch viewer:")
    print(f"  python3 sim_viewer.py {OUT}")
    print()
    print("Tips:")
    print("  • Ticks   1–300 = formation OFF, plain_move  (blue Strike)")
    print("  • Ticks 301–600 = formation ON,  plain_move  (green Strike)")
    print("  • Ticks 601–950 = formation ON,  attack_move (orange Strike vs red Line)")
    print("  • In segment C: watch Strike march in formation then halt and engage on contact")
    print("  • Press T to see combat target lines in segment C")


if __name__ == "__main__":
    main()
