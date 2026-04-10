import math
import random
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP, FIELD_ATTACK_RANGE, FIELD_LAYER
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from test_maps import open_field

FACTION_STRIKE = 0
FACTION_LINE = 1
DT = config.TACTICAL_TICK_DURATION
MAX_TICKS = 6000
SAMPLE_INTERVAL = 30


def _spawn_strike(store, faction, cx, cy, count, rng):
    uids = []
    for i in range(count):
        ut = "Raider" if i % 2 == 0 else "Interceptor"
        x = cx + (i % 5) * 40.0 + rng.uniform(-15, 15)
        y = cy + (i // 5) * 40.0 + rng.uniform(-15, 15)
        uids.append(store.spawn(ut, faction, x, y))
    return uids


def _spawn_line_column(store, faction, lead_x, lead_y, count, spacing, rng):
    uids = []
    for i in range(count):
        ut = "Vanguard" if i % 3 != 2 else "Warden"
        x = lead_x + rng.uniform(-10, 10)
        y = lead_y + i * spacing + rng.uniform(-10, 10)
        uids.append(store.spawn(ut, faction, x, y))
    return uids


def _count_firing(store, uids):
    count = 0
    for uid in uids:
        if not store.alive[uid]:
            continue
        tgt = store.auto_engage_target[uid]
        if tgt < 0 or not store.alive[tgt]:
            continue
        ax, ay = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
        tx, ty = store.data[tgt, FIELD_X], store.data[tgt, FIELD_Y]
        dist = math.sqrt((tx - ax) ** 2 + (ty - ay) ** 2)
        if dist <= store.data[uid, FIELD_ATTACK_RANGE]:
            count += 1
    return count


def run():
    seed = 1
    rng = random.Random(seed)
    tmap = open_field()
    store = UnitStore()

    line_uids = _spawn_line_column(store, FACTION_LINE, 2000.0, 1325.0, 10, 150.0, rng)
    strike_uids = _spawn_strike(store, FACTION_STRIKE, 3200.0, 2000.0, 10, rng)

    queue = CommandQueue()
    queue.add(Command(tick=0, type="group_move", unit_ids=strike_uids,
                      params={"target_x": 2000.0, "target_y": 2000.0}))

    engine = TacticalEngine(tmap, store, seed=seed)
    engine.command_queue = queue

    log_lines = []
    header = (f"{'tick':>5} {'s_alive':>7} {'l_alive':>7} {'s_hp':>8} {'l_hp':>8} "
              f"{'s_fire':>6} {'l_fire':>6} {'s_cx':>7} {'s_cy':>7} {'l_cx':>7} {'l_cy':>7} {'min_d':>7}")
    log_lines.append(header)
    print(header)

    for t in range(MAX_TICKS):
        engine.step()

        if engine.tick % SAMPLE_INTERVAL == 0:
            s_alive = [u for u in strike_uids if store.alive[u]]
            l_alive = [u for u in line_uids if store.alive[u]]

            s_hp = sum(store.data[u, FIELD_HP] for u in s_alive) if s_alive else 0
            l_hp = sum(store.data[u, FIELD_HP] for u in l_alive) if l_alive else 0

            s_fire = _count_firing(store, strike_uids)
            l_fire = _count_firing(store, line_uids)

            if s_alive:
                s_cx = sum(store.data[u, FIELD_X] for u in s_alive) / len(s_alive)
                s_cy = sum(store.data[u, FIELD_Y] for u in s_alive) / len(s_alive)
            else:
                s_cx, s_cy = 0, 0

            if l_alive:
                l_cx = sum(store.data[u, FIELD_X] for u in l_alive) / len(l_alive)
                l_cy = sum(store.data[u, FIELD_Y] for u in l_alive) / len(l_alive)
            else:
                l_cx, l_cy = 0, 0

            min_d = float('inf')
            if s_alive and l_alive:
                for su in s_alive:
                    sx, sy = store.data[su, FIELD_X], store.data[su, FIELD_Y]
                    for lu in l_alive:
                        lx, ly = store.data[lu, FIELD_X], store.data[lu, FIELD_Y]
                        d = math.sqrt((sx - lx) ** 2 + (sy - ly) ** 2)
                        if d < min_d:
                            min_d = d
            if min_d == float('inf'):
                min_d = -1

            line = (f"{engine.tick:>5} {len(s_alive):>7} {len(l_alive):>7} "
                    f"{s_hp:>8.0f} {l_hp:>8.0f} "
                    f"{s_fire:>6} {l_fire:>6} "
                    f"{s_cx:>7.0f} {s_cy:>7.0f} {l_cx:>7.0f} {l_cy:>7.0f} {min_d:>7.0f}")
            log_lines.append(line)
            print(line)

        if engine.is_terminal():
            break

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    surv_s = len(engine.get_survivors(FACTION_STRIKE))
    surv_l = len(engine.get_survivors(FACTION_LINE))

    print(f"  Final tick: {engine.tick} (max={MAX_TICKS})")
    print(f"  Strike survivors: {surv_s}")
    print(f"  Line survivors: {surv_l}")
    print(f"  Terminal: {engine.is_terminal()}")

    # Total damage
    dmg_to_line = 0
    for uid in line_uids:
        if store.alive[uid]:
            dmg_to_line += store.data[uid, FIELD_MAX_HP] - store.data[uid, FIELD_HP]
        else:
            dmg_to_line += store.data[uid, FIELD_MAX_HP]

    dmg_to_strike = 0
    for uid in strike_uids:
        if store.alive[uid]:
            dmg_to_strike += store.data[uid, FIELD_MAX_HP] - store.data[uid, FIELD_HP]
        else:
            dmg_to_strike += store.data[uid, FIELD_MAX_HP]

    print(f"  Total damage dealt to Line: {dmg_to_line:.0f}")
    print(f"  Total damage dealt to Strike: {dmg_to_strike:.0f}")
    print(f"  Damage ratio (to_line/to_strike): {dmg_to_line/dmg_to_strike:.2f}" if dmg_to_strike > 0 else "  Damage ratio: inf")

    # Scoring branch
    strike_wins = surv_s > 0 and surv_l == 0
    print(f"\n  Scoring condition: strike_wins = (surv_strike > 0 and surv_line == 0)")
    print(f"    surv_strike={surv_s} > 0 = {surv_s > 0}")
    print(f"    surv_line={surv_l} == 0 = {surv_l == 0}")
    print(f"    strike_wins = {strike_wins}")

    if not strike_wins:
        if surv_s == 0:
            print(f"  -> Strike lost because all Strike units died")
        elif surv_l > 0:
            print(f"  -> Strike lost because {surv_l} Line units survived (timeout / incomplete wipe)")

    # Save log
    with open("test_6j_t3a_diagnostic.log", "w") as f:
        f.write("\n".join(log_lines))
    print(f"\n  Log saved to test_6j_t3a_diagnostic.log")


if __name__ == "__main__":
    run()
