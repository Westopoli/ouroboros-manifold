import math
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP, FIELD_ATTACK_RANGE
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from test_maps import open_field

FACTION_LINE = 1
FACTION_STRIKE = 0
DT = config.TACTICAL_TICK_DURATION
MAX_TICKS = 6000
SAMPLE_INTERVAL = 30


def _spawn_defender_line(store):
    uids = []
    for i in range(20):
        x = 1525.0 + i * 50.0
        y = 2000.0
        uids.append(store.spawn("Vanguard", FACTION_LINE, x, y))
    return uids


def _spawn_attacker_blob(store):
    uids = []
    for row in range(4):
        for col in range(5):
            x = 2000.0 - 2 * 40.0 + col * 40.0
            y = 1200.0 - 1.5 * 40.0 + row * 40.0
            uids.append(store.spawn("Vanguard", FACTION_STRIKE, x, y))
    return uids


def _count_in_range(store, attacker_uids, defender_uids):
    d_alive = [u for u in defender_uids if store.alive[u]]
    if not d_alive:
        return 0
    count = 0
    for uid in attacker_uids:
        if not store.alive[uid]:
            continue
        ax = store.data[uid, FIELD_X]
        ay = store.data[uid, FIELD_Y]
        rng = store.data[uid, FIELD_ATTACK_RANGE]
        for du in d_alive:
            dx = store.data[du, FIELD_X] - ax
            dy = store.data[du, FIELD_Y] - ay
            if dx * dx + dy * dy <= rng * rng:
                count += 1
                break
    return count


def _count_firing(store, uids):
    count = 0
    for uid in uids:
        if not store.alive[uid]:
            continue
        tgt = store.auto_engage_target[uid]
        if tgt < 0 or not store.alive[tgt]:
            continue
        count += 1
    return count


def run():
    store = UnitStore()
    tmap = open_field()

    a_uids = _spawn_defender_line(store)
    b_uids = _spawn_attacker_blob(store)

    queue = CommandQueue()
    queue.add(Command(tick=0, type="group_move", unit_ids=b_uids,
                      params={"target_x": 2000.0, "target_y": 2000.0}))

    engine = TacticalEngine(tmap, store, seed=1)
    engine.command_queue = queue

    header = (f"{'tick':>5}  {'a_alive':>7}  {'b_alive':>7}  {'b_in_rng':>8}  "
              f"{'b_fire':>6}  {'a_fire':>6}  {'b_ymin':>6}  {'b_ymax':>6}  "
              f"{'a_hp':>8}  {'b_hp':>8}")
    print(header)

    peak_b_fire = 0
    peak_b_fire_tick = 0

    window_b_fire = []
    window_a_fire = []
    WINDOW_START = 200
    WINDOW_END = 600

    for t in range(MAX_TICKS):
        engine.step()
        tick = engine.tick

        a_alive = [u for u in a_uids if store.alive[u]]
        b_alive = [u for u in b_uids if store.alive[u]]

        b_fire = _count_firing(store, b_uids)
        a_fire = _count_firing(store, a_uids)

        if b_fire > peak_b_fire:
            peak_b_fire = b_fire
            peak_b_fire_tick = tick

        if WINDOW_START <= tick <= WINDOW_END and a_alive and b_alive:
            window_b_fire.append(b_fire)
            window_a_fire.append(a_fire)

        if tick % SAMPLE_INTERVAL == 0:
            b_in_rng = _count_in_range(store, b_uids, a_uids)
            b_ymin = min(store.data[u, FIELD_Y] for u in b_alive) if b_alive else 0.0
            b_ymax = max(store.data[u, FIELD_Y] for u in b_alive) if b_alive else 0.0
            a_hp = sum(store.data[u, FIELD_HP] for u in a_alive)
            b_hp = sum(store.data[u, FIELD_HP] for u in b_alive)
            print(f"{tick:>5}  {len(a_alive):>7}  {len(b_alive):>7}  {b_in_rng:>8}  "
                  f"{b_fire:>6}  {a_fire:>6}  {b_ymin:>6.0f}  {b_ymax:>6.0f}  "
                  f"{a_hp:>8.0f}  {b_hp:>8.0f}")

        if engine.is_terminal():
            break

    a_surv = len(engine.get_survivors(FACTION_LINE))
    b_surv = len(engine.get_survivors(FACTION_STRIKE))
    if a_surv > 0 and b_surv == 0:
        winner = "defender (Line A)"
    elif b_surv > 0 and a_surv == 0:
        winner = "attacker (Blob B)"
    else:
        winner = f"draw / timeout (a={a_surv}, b={b_surv})"

    avg_b = sum(window_b_fire) / len(window_b_fire) if window_b_fire else 0.0
    avg_a = sum(window_a_fire) / len(window_a_fire) if window_a_fire else 0.0
    ratio = avg_a / avg_b if avg_b > 0 else float("inf")

    print()
    print("=" * 70)
    print(f"  Winner:              {winner}")
    print(f"  Final tick:          {engine.tick}  ({engine.tick * DT:.1f}s)")
    print(f"  Peak b_firing:       {peak_b_fire} at tick {peak_b_fire_tick}")
    print(f"  Window ticks {WINDOW_START}-{WINDOW_END}:")
    print(f"    Avg b_firing:      {avg_b:.2f}")
    print(f"    Avg a_firing:      {avg_a:.2f}")
    print(f"    a/b fire ratio:    {ratio:.2f}  (>1.0 = defender fires more = queueing present)")
    print("=" * 70)


if __name__ == "__main__":
    run()
