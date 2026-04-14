"""
diag_perf_subsystems.py — Per-subsystem timing at 100v100, 50 ticks.
Identifies which subsystem dominates tick time.
"""
import math, random, time
import config
from unit import UnitStore
from damage import resolve_damage, update_targeting
from movement import update_movement
from ability import update_abilities, resolve_barrage
from fog_of_war import update_fog_timers
from command import Command, CommandQueue, process_commands
from test_maps import open_field_large

DT = config.TACTICAL_TICK_DURATION
TICKS = 50
FACTION_A, FACTION_B = 0, 1
CENTER_X, CENTER_Y = 6000.0, 6000.0

MIXED_RATIO = {"Vanguard": 0.30, "Warden": 0.15, "Raider": 0.20,
               "Interceptor": 0.10, "Bombard": 0.15, "Bastion": 0.10}

def _spawn(store, faction, cx, cy, count, rng):
    roster = []
    for ut, frac in MIXED_RATIO.items():
        roster.extend([ut] * max(1, round(count * frac)))
    while len(roster) > count: roster.pop(rng.randrange(len(roster)))
    while len(roster) < count: roster.append(rng.choice(list(MIXED_RATIO)))
    rng.shuffle(roster)
    cols = max(5, int(math.sqrt(count)) + 1)
    uids = []
    for i, ut in enumerate(roster):
        x = cx + (i % cols) * 55.0 + rng.uniform(-8, 8)
        y = cy + (i // cols) * 55.0 + rng.uniform(-8, 8)
        uids.append(store.spawn(ut, faction, x, y))
    return uids

rng = random.Random(1)
tmap = open_field_large()
store = UnitStore()
uids_a = _spawn(store, FACTION_A, CENTER_X - 500, CENTER_Y - 2500, 100, rng)
uids_b = _spawn(store, FACTION_B, CENTER_X - 500, CENTER_Y + 2500, 100, rng)

queue = CommandQueue()
queue.add(Command(tick=0, type="attack_move", unit_ids=uids_a,
                  params={"target_x": CENTER_X, "target_y": CENTER_Y + 2500}))
queue.add(Command(tick=0, type="attack_move", unit_ids=uids_b,
                  params={"target_x": CENTER_X, "target_y": CENTER_Y - 2500}))

sim_rng = random.Random(1)
t_cmd, t_tgt, t_mov, t_dmg, t_abl, t_fog, t_tot = [], [], [], [], [], [], []

print(f"Running {TICKS} ticks at 100v100...")
for tick in range(TICKS):
    t0 = time.perf_counter()
    ts = time.perf_counter(); process_commands(queue, store, tick);           t_cmd.append((time.perf_counter()-ts)*1000)
    ts = time.perf_counter(); update_targeting(store, tmap, sim_rng);        t_tgt.append((time.perf_counter()-ts)*1000)
    ts = time.perf_counter(); update_movement(store, tmap, DT);              t_mov.append((time.perf_counter()-ts)*1000)
    ts = time.perf_counter(); deaths, ks = resolve_damage(store, tmap, DT); t_dmg.append((time.perf_counter()-ts)*1000)
    ts = time.perf_counter()
    be = update_abilities(store, DT)
    if be: resolve_barrage(store, be)
    t_abl.append((time.perf_counter()-ts)*1000)
    ts = time.perf_counter(); update_fog_timers(store); t_fog.append((time.perf_counter()-ts)*1000)
    t_tot.append((time.perf_counter()-t0)*1000)
    print(f"  tick {tick+1:>3}/{TICKS}  total={t_tot[-1]:.1f}ms  mov={t_mov[-1]:.1f}ms  tgt={t_tgt[-1]:.1f}ms")

def stats(t):
    s = sorted(t); n = len(s)
    return sum(s)/n, s[int(n*0.95)], s[-1]

print(f"\n{'Subsystem':<16} {'mean':>8} {'p95':>8} {'max':>8}")
print(f"{'─'*16} {'─'*8} {'─'*8} {'─'*8}")
for label, t in [("commands", t_cmd), ("targeting", t_tgt), ("movement", t_mov),
                  ("damage", t_dmg), ("abilities", t_abl), ("fog", t_fog), ("TOTAL", t_tot)]:
    mn, p95, mx = stats(t)
    pct = mn / stats(t_tot)[0] * 100 if label != "TOTAL" else 100.0
    print(f"  {label:<14} {mn:>7.2f}ms {p95:>7.2f}ms {mx:>7.2f}ms  ({pct:.0f}% of tick)")
