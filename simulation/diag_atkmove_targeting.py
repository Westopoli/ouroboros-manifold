"""
Diagnostic: why does an attack_move unit fail to engage enemies in sensor range?

Runs scenario C (formation ON, attack_move Strike into Line) and prints per-tick
detail for any Strike unit that:
  - is alive
  - is NOT plain_moving
  - has auto_engage_target == -1
  - has at least one enemy within sensor_radius

Prints the unit's flags, closest enemy distance, attack_range, and sensor_radius
so we can see exactly which condition is preventing engagement.
"""

import math
import random
import config
config.FORMATION_MOVE_ENABLED = True

from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_SENSOR_RADIUS, FIELD_ATTACK_RANGE, FIELD_LAYER
from damage import resolve_damage, update_targeting
from movement import update_movement
from ability import update_abilities, resolve_barrage
from fog_of_war import update_fog_timers
from command import Command, CommandQueue, process_commands
from test_maps import chokepoint

DT = config.TACTICAL_TICK_DURATION
FACTION_STRIKE = 4
FACTION_LINE   = 5
PRINT_WINDOW   = (230, 310)   # only print during this tick range to avoid noise


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


def closest_enemy_dist(store, uid, enemy_uids):
    ux, uy = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
    best = float("inf")
    best_uid = -1
    for e in enemy_uids:
        if not store.alive[e]:
            continue
        ex, ey = store.data[e, FIELD_X], store.data[e, FIELD_Y]
        d = math.sqrt((ux - ex)**2 + (uy - ey)**2)
        if d < best:
            best, best_uid = d, e
    return best, best_uid


def run():
    tmap = chokepoint()
    store = UnitStore()
    rng = random.Random(1)

    strike_uids = _spawn_strike(store, rng)
    line_uids   = _spawn_line(store, rng)

    queue = CommandQueue()
    queue.add(Command(tick=0, type="attack_move", unit_ids=strike_uids,
                      params={"target_x": 2000.0, "target_y": 1100.0}))

    sim_rng = random.Random(1)
    printed_header = False

    for t in range(400):
        process_commands(queue, store, t)
        update_targeting(store, tmap, sim_rng)
        update_movement(store, tmap, DT)
        resolve_damage(store, tmap, DT)
        be = update_abilities(store, DT)
        if be:
            resolve_barrage(store, be)
        update_fog_timers(store)

        tick = t + 1

        if tick < PRINT_WINDOW[0] or tick > PRINT_WINDOW[1]:
            continue

        # Find Strike units that are NOT engaging but have enemies nearby
        for uid in strike_uids:
            if not store.alive[uid]:
                continue
            if store.plain_moving[uid]:
                continue
            if store.auto_engage_target[uid] >= 0:
                continue

            ux, uy = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
            sensor_r  = store.data[uid, FIELD_SENSOR_RADIUS]
            attack_r  = store.data[uid, FIELD_ATTACK_RANGE]

            closest_d, closest_e = closest_enemy_dist(store, uid, line_uids)

            # Only print if an enemy is within sensor range
            if closest_d > sensor_r:
                continue

            if not printed_header:
                print(f"{'tick':>5}  {'uid':>4}  {'type':<14}  "
                      f"{'pos':>18}  {'atk_mvg':>7}  {'has_tgt':>7}  "
                      f"{'plain':>5}  {'sensor_r':>8}  {'attack_r':>8}  "
                      f"{'closest_e':>9}  {'closest_d':>9}")
                print("-" * 110)
                printed_header = True

            print(f"{tick:>5}  {uid:>4}  {store.unit_type[uid]:<14}  "
                  f"({ux:>7.1f},{uy:>7.1f})  "
                  f"{str(store.attack_moving[uid]):>7}  "
                  f"{str(store.has_move_target[uid]):>7}  "
                  f"{str(store.plain_moving[uid]):>5}  "
                  f"{sensor_r:>8.0f}  {attack_r:>8.0f}  "
                  f"{closest_e:>9}  {closest_d:>9.1f}")

    if not printed_header:
        print(f"No unengaged Strike units with enemies in sensor range found "
              f"during ticks {PRINT_WINDOW[0]}–{PRINT_WINDOW[1]}.")
        print("Try widening PRINT_WINDOW.")


if __name__ == "__main__":
    run()
