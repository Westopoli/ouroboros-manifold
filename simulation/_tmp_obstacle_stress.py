"""
Obstacle stress test — 200v200 on an 8000x8000 map with dense obstacle walls
forcing A* pathfinding around chokepoints. Measures navmesh build time, path
computation, and per-tick movement cost.
"""
import math, random, time, resource, config
from unit import UnitStore, FIELD_X, FIELD_Y
from damage import resolve_damage, update_targeting
from movement import update_movement, Navmesh, find_path
from ability import update_abilities, resolve_barrage
from fog_of_war import update_fog_timers
from command import Command, CommandQueue, process_commands
from tactical_map import TacticalMap, GradientSource

DT = config.TACTICAL_TICK_DURATION
TICKS = 1500
FACTION_A, FACTION_B = 0, 1
MAP_W = MAP_H = 24000
COUNT = 200

MIXED_RATIO = {
    "Vanguard": 0.30, "Warden": 0.15, "Raider": 0.20,
    "Interceptor": 0.10, "Bombard": 0.15, "Bastion": 0.10,
}


def build_obstacle_map():
    sources = []
    # 3 horizontal walls with gaps, forcing pathfinding detours
    for wall_y in [7800, 12000, 16200]:
        # Wall spans x=0..10200 and x=13800..24000 (gap at x=10200-13800)
        for row_off in [-100, 0, 100]:
            for x in range(200, 10200, 300):
                sources.append(GradientSource(
                    position=(x, wall_y + row_off),
                    property_type="obstacle_density",
                    radius=200, intensity=1.0, falloff="constant",
                ))
            for x in range(13800, 24000, 300):
                sources.append(GradientSource(
                    position=(x, wall_y + row_off),
                    property_type="obstacle_density",
                    radius=200, intensity=1.0, falloff="constant",
                ))
    # Scattered cover patches that create additional obstacle density
    rng = random.Random(42)
    for _ in range(40):
        px = rng.uniform(500, 23500)
        py = rng.uniform(500, 23500)
        sources.append(GradientSource(
            position=(px, py), property_type="obstacle_density",
            radius=250, intensity=0.9, falloff="linear",
        ))
    return TacticalMap(width=MAP_W, height=MAP_H, gradient_sources=sources, layers=1)


def spawn(store, faction, cx, cy, count, rng):
    roster = []
    for ut, frac in MIXED_RATIO.items():
        roster.extend([ut] * max(1, round(count * frac)))
    while len(roster) > count:
        roster.pop(rng.randrange(len(roster)))
    while len(roster) < count:
        roster.append(rng.choice(list(MIXED_RATIO)))
    rng.shuffle(roster)
    cols = max(5, int(math.sqrt(count)) + 1)
    uids = []
    for i, ut in enumerate(roster):
        x = cx + (i % cols) * 55.0 + rng.uniform(-8, 8)
        y = cy + (i // cols) * 55.0 + rng.uniform(-8, 8)
        uids.append(store.spawn(ut, faction, x, y))
    return uids


print(f"Building obstacle map ({MAP_W}x{MAP_H})...")
t0 = time.perf_counter()
tmap = build_obstacle_map()
build_ms = (time.perf_counter() - t0) * 1000
print(f"  Map built: {len(tmap.gradient_sources)} gradient sources  ({build_ms:.1f}ms)")

t0 = time.perf_counter()
nm = Navmesh.from_tactical_map(tmap)
nm_ms = (time.perf_counter() - t0) * 1000
blocked = sum(1 for r in range(nm.rows) for c in range(nm.cols) if not nm.is_walkable(r, c))
total_cells = nm.rows * nm.cols
print(f"  Navmesh: {nm.cols}x{nm.rows} = {total_cells} cells, {blocked} blocked ({blocked/total_cells:.1%})  ({nm_ms:.1f}ms)")

# Test a long path through all 3 walls
t0 = time.perf_counter()
path, nodes = find_path(nm, 12000.0, 1500.0, 12000.0, 22500.0)
path_ms = (time.perf_counter() - t0) * 1000
if path:
    print(f"  Test path: {len(path)} waypoints, {nodes} nodes explored  ({path_ms:.1f}ms)")
else:
    print(f"  Test path: NO PATH FOUND  ({path_ms:.1f}ms)")

rng = random.Random(1)
store = UnitStore()
# Faction A spawns top, faction B spawns bottom
uids_a = spawn(store, FACTION_A, 10500, 1500, COUNT, rng)
uids_b = spawn(store, FACTION_B, 10500, 21000, COUNT, rng)
print(f"  Spawned: A={len(uids_a)}  B={len(uids_b)}")

queue = CommandQueue()
queue.add(Command(tick=0, type="attack_move", unit_ids=uids_a,
                  params={"target_x": 12000.0, "target_y": 22500.0}))
queue.add(Command(tick=0, type="attack_move", unit_ids=uids_b,
                  params={"target_x": 12000.0, "target_y": 1500.0}))

sim_rng = random.Random(1)
t_targeting, t_movement, t_damage, t_abilities, t_total = [], [], [], [], []

print(f"\nRunning {TICKS} ticks...")
for tick in range(TICKS):
    t0 = time.perf_counter()
    process_commands(queue, store, tick)

    ts = time.perf_counter(); update_targeting(store, tmap, sim_rng);  t_targeting.append((time.perf_counter()-ts)*1000)
    ts = time.perf_counter(); update_movement(store, tmap, DT);        t_movement.append((time.perf_counter()-ts)*1000)
    ts = time.perf_counter(); resolve_damage(store, tmap, DT);         t_damage.append((time.perf_counter()-ts)*1000)
    ts = time.perf_counter()
    be = update_abilities(store, DT)
    if be:
        resolve_barrage(store, be)
    t_abilities.append((time.perf_counter()-ts)*1000)
    update_fog_timers(store)
    t_total.append((time.perf_counter()-t0)*1000)

    if tick % 300 == 299:
        active = store.active_ids()
        a = sum(1 for u in active if store.faction[u] == FACTION_A)
        b = sum(1 for u in active if store.faction[u] == FACTION_B)
        print(f"  t={tick+1:>5}  A={a:>3}  B={b:>3}  tick_avg={sum(t_total[-300:])/300:.2f}ms")

    alive_factions = {store.faction[u] for u in store.active_ids()}
    if len(alive_factions) <= 1:
        print(f"  Combat resolved at tick {tick+1}.")
        break

peak_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

def stats(ts):
    s = sorted(ts)
    n = len(s)
    return {"mean": sum(s)/n, "p95": s[int(n*0.95)], "p99": s[int(n*0.99)], "max": s[-1]}

print()
print(f"  {'Subsystem':<16} {'mean':>8} {'p95':>8} {'p99':>8} {'max':>8}")
print(f"  {'─'*16} {'─'*8} {'─'*8} {'─'*8} {'─'*8}")
for label, ts in [
    ("targeting",  t_targeting),
    ("movement",   t_movement),
    ("damage",     t_damage),
    ("abilities",  t_abilities),
    ("TOTAL",      t_total),
]:
    s = stats(ts)
    print(f"  {label:<16} {s['mean']:>7.2f}ms {s['p95']:>7.2f}ms {s['p99']:>7.2f}ms {s['max']:>7.2f}ms")

tot = stats(t_total)
n = len(t_total)
comp = sum(1 for t in t_total if t < 50.0)
print(f"\n  Ticks measured:    {n}")
print(f"  Budget compliance: {comp}/{n} ticks < 50ms  ({comp/n:.1%})")
print(f"  Peak memory:       {peak_mem/1024/1024:.1f} MB")
print(f"\n  400-unit obstacle p95: {tot['p95']:.2f}ms  (budget=50ms)  {'PASS' if tot['p95'] < 50 else 'FAIL'}")
