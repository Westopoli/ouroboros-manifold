import math
import random
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP, FIELD_ATTACK_RANGE
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from movement import _ensure_navmesh
from test_maps import chokepoint

FACTION_STRIKE = 0
FACTION_LINE = 1
DT = config.TACTICAL_TICK_DURATION
MAX_TICKS = 6000


def _spawn_strike_arc_x(store, faction, center_x, center_y, count, rng):
    uids = []
    spacing = 55.0
    start_x = center_x - (count - 1) * spacing / 2.0
    for i in range(count):
        ut = "Raider" if i % 2 == 0 else "Interceptor"
        jx = rng.uniform(-10, 10)
        jy = rng.uniform(-15, 15)
        x = start_x + i * spacing + jx
        y = center_y + jy
        uids.append(store.spawn(ut, faction, x, y))
    return uids


def _spawn_line_formed(store, faction, center_x, center_y, count, rng):
    uids = []
    for i in range(count):
        ut = "Vanguard" if i % 3 != 2 else "Warden"
        jx = rng.uniform(-15, 15)
        jy = rng.uniform(-15, 15)
        x = center_x + (i % 5) * 40.0 + jx
        y = center_y + (i // 5) * 40.0 + jy
        uids.append(store.spawn(ut, faction, x, y))
    return uids


def run():
    rng = random.Random(1)
    tmap = chokepoint()
    store = UnitStore()

    strike_uids = _spawn_strike_arc_x(store, FACTION_STRIKE, 2000.0, 2900.0, 10, rng)
    line_uids = _spawn_line_formed(store, FACTION_LINE, 2000.0, 1100.0, 10, rng)

    queue = CommandQueue()
    queue.add(Command(tick=0, type="group_move", unit_ids=line_uids,
                      params={"target_x": 2000.0, "target_y": 2900.0}))

    # Sanity check: verify all spawn positions are on walkable cells
    navmesh = _ensure_navmesh(tmap)
    print("SANITY CHECK — spawn walkability (seed 1)")
    print("=" * 70)
    all_ok = True
    for label, uids in [("Line", line_uids), ("Strike", strike_uids)]:
        for uid in uids:
            x, y = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
            c = int(x / navmesh.cell_size)
            r = int(y / navmesh.cell_size)
            walkable = navmesh.grid[r][c] if 0 <= r < navmesh.rows and 0 <= c < navmesh.cols else False
            typ = store.unit_type[uid]
            if not walkable:
                print(f"  FAIL: {label} uid={uid} ({typ}) at ({x:.0f},{y:.0f}) -> cell ({r},{c}) UNWALKABLE")
                all_ok = False
    if all_ok:
        print("  ALL UNITS ON WALKABLE CELLS")
    print()

    if not all_ok:
        print("Aborting — fix spawn positions first.")
        return

    # Run with diagnostics at specific ticks
    engine = TacticalEngine(tmap, store, seed=1)
    engine.command_queue = queue

    diag_ticks = {0, 100, 300, 500, 1000, 2000, 4000}
    prev_pos = {}

    for t in range(MAX_TICKS):
        engine.step()

        if engine.tick in diag_ticks:
            print(f"Tick {engine.tick} ({engine.tick * DT:.1f}s):")

            line_alive = [u for u in line_uids if store.alive[u]]
            strike_alive = [u for u in strike_uids if store.alive[u]]

            if line_alive:
                lx = [store.data[u, FIELD_X] for u in line_alive]
                ly = [store.data[u, FIELD_Y] for u in line_alive]

                stuck = 0
                for u in line_alive:
                    if u in prev_pos:
                        px, py = prev_pos[u]
                        cx, cy = store.data[u, FIELD_X], store.data[u, FIELD_Y]
                        spd = math.sqrt((cx-px)**2 + (cy-py)**2) / DT
                        if spd < 5.0:
                            stuck += 1

                print(f"  Line: mean=({sum(lx)/len(lx):.0f},{sum(ly)/len(ly):.0f})  "
                      f"x=[{min(lx):.0f},{max(lx):.0f}]  "
                      f"y=[{min(ly):.0f},{max(ly):.0f}]  "
                      f"alive={len(line_alive)}  stuck(v<5)={stuck}")

                # At tick 300, print per-unit positions for corridor flow analysis
                if engine.tick == 300:
                    print(f"  Line per-unit positions (tick 300):")
                    for u in line_alive:
                        ux, uy = store.data[u, FIELD_X], store.data[u, FIELD_Y]
                        typ = store.unit_type[u]
                        tgt = store.auto_engage_target[u]
                        print(f"    uid={u} ({typ}) at ({ux:.0f},{uy:.0f}) target={tgt}")

            if strike_alive:
                sx = [store.data[u, FIELD_X] for u in strike_alive]
                sy = [store.data[u, FIELD_Y] for u in strike_alive]
                has_tgt = sum(1 for u in strike_alive if store.auto_engage_target[u] >= 0)
                print(f"  Strike: mean=({sum(sx)/len(sx):.0f},{sum(sy)/len(sy):.0f})  "
                      f"alive={len(strike_alive)}  has_target={has_tgt}")

            if line_alive and strike_alive:
                min_d = min(
                    math.sqrt((store.data[lu, FIELD_X] - store.data[su, FIELD_X])**2 +
                              (store.data[lu, FIELD_Y] - store.data[su, FIELD_Y])**2)
                    for lu in line_alive for su in strike_alive
                )
                print(f"  Closest Line<->Strike: {min_d:.0f} wu")

            # Update prev positions
            for u in line_alive:
                prev_pos[u] = (store.data[u, FIELD_X], store.data[u, FIELD_Y])

            print()

        if engine.is_terminal():
            print(f"TERMINAL at tick {engine.tick} ({engine.tick * DT:.1f}s)")
            break

    if engine.tick >= MAX_TICKS - 1:
        print(f"TIMEOUT at tick {engine.tick}")

    surv_s = len(engine.get_survivors(FACTION_STRIKE))
    surv_l = len(engine.get_survivors(FACTION_LINE))
    print(f"Result: Strike surv={surv_s}, Line surv={surv_l}, "
          f"winner={'Strike' if surv_s > surv_l else 'Line' if surv_l > surv_s else 'Draw'}")


if __name__ == "__main__":
    run()
