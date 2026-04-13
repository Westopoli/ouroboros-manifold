"""
Generates a sim_viewer dump of the formation performance checkpoint scenario.

10v10 Strike attack_move into stationary Line, FORMATION_MOVE_ENABLED=True.

Usage:
    python3 gen_formation_perf_dump.py
    python3 sim_viewer.py /tmp/formation_perf.jsonl
"""

import random
import config

config.FORMATION_MOVE_ENABLED = True

from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP, FIELD_LAYER, FIELD_ABILITY_ACTIVE
from damage import resolve_damage, update_targeting
from movement import update_movement
from ability import update_abilities, resolve_barrage
from fog_of_war import update_fog_timers
from command import Command, CommandQueue, process_commands
from sim_logger import SimLogger, config_snapshot
from test_maps import chokepoint

OUT    = "/tmp/formation_perf.jsonl"
TICKS  = 300
DT     = config.TACTICAL_TICK_DURATION

FACTION_STRIKE = 0
FACTION_LINE   = 1


def _spawn_strike(store, rng):
    uids = []
    spacing = 55.0
    start_x = 2000.0 - 9 * spacing / 2.0
    for i in range(10):
        ut = "Raider" if i % 2 == 0 else "Interceptor"
        x = start_x + i * spacing + rng.uniform(-10, 10)
        y = 2900.0 + rng.uniform(-15, 15)
        uids.append(store.spawn(ut, FACTION_STRIKE, x, y))
    return uids


def _spawn_line(store, rng):
    uids = []
    for i in range(10):
        ut = "Vanguard" if i % 3 != 2 else "Warden"
        x = 2000.0 + (i % 5) * 40.0 + rng.uniform(-15, 15)
        y = 1100.0 + (i // 5) * 40.0 + rng.uniform(-15, 15)
        uids.append(store.spawn(ut, FACTION_LINE, x, y))
    return uids


def main():
    tmap  = chokepoint()
    store = UnitStore()
    rng   = random.Random(1)

    factions = {
        0: ("Strike (attack_move)", "#f97316"),
        1: ("Line (defending)",     "#ef4444"),
    }
    logger = SimLogger(OUT, "formation_perf", tmap, factions, config_snapshot())

    strike_uids = _spawn_strike(store, rng)
    line_uids   = _spawn_line(store, rng)

    queue = CommandQueue()
    queue.add(Command(tick=0, type="attack_move", unit_ids=strike_uids,
                      params={"target_x": 2000.0, "target_y": 1100.0}))

    sim_rng = random.Random(1)

    for t in range(TICKS):
        process_commands(queue, store, t)
        update_targeting(store, tmap, sim_rng)
        update_movement(store, tmap, DT)
        deaths, _ = resolve_damage(store, tmap, DT)
        be = update_abilities(store, DT)
        if be:
            resolve_barrage(store, be)
        update_fog_timers(store)

        logger.log_tick(t + 1, store, deaths, {
            "targeting": 0.0, "movement": 0.0,
            "abilities": 0.0, "damage": 0.0, "fog": 0.0, "commands": 0.0,
        })

        alive_factions = {store.faction[u] for u in range(store.count) if store.alive[u]}
        if len(alive_factions) <= 1:
            for remaining in range(t + 1, TICKS):
                logger.log_tick(remaining + 1, store, [], {
                    "targeting": 0.0, "movement": 0.0,
                    "abilities": 0.0, "damage": 0.0, "fog": 0.0, "commands": 0.0,
                })
            break

    logger.close()
    print(f"Wrote {OUT}")
    print(f"  python3 sim_viewer.py {OUT}")


if __name__ == "__main__":
    main()
