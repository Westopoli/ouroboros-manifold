"""
diag_perf_combat.py — Deep timing through full combat phase (march → peak fight → cleanup).

Breaks abilities into sub-components by timing them individually:
  - ability main loop (cooldown/state ticks)
  - _check_intercept (inline replicated)
  - _apply_warden_aura_healing (inline replicated)
  - resolve_barrage

Breaks movement into sub-components:
  - per-unit steering loop
  - _update_move_groups
  - _resolve_collisions (via HARD_COLLISION_ENABLED toggle timing)

Shows per-tick data for ticks 400–700 (peak spike window) and summary stats.
"""
import math, random, time
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_MAX_HP, FIELD_LAYER, CATEGORY_STRIKE
from damage import resolve_damage, update_targeting
from movement import update_movement, _ensure_navmesh, _resolve_collisions
from ability import update_abilities, resolve_barrage, ABILITY_INACTIVE, ABILITY_MAP
from fog_of_war import update_fog_timers
from command import Command, CommandQueue, process_commands
from test_maps import open_field_large

DT   = config.TACTICAL_TICK_DURATION
TICKS = 1500
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

# Sub-timing storage
t_tgt, t_mov, t_dmg, t_abl_main, t_abl_intercept, t_abl_warden, t_abl_barrage, t_tot = \
    [], [], [], [], [], [], [], []
t_mov_steer, t_mov_groups, t_mov_collide = [], [], []

navmesh = _ensure_navmesh(tmap)

SPIKE_WINDOW = (400, 700)  # ticks to print per-tick output

print(f"Running {TICKS} ticks at 100v100 (per-tick output for t={SPIKE_WINDOW[0]}–{SPIKE_WINDOW[1]})...\n")
print(f"  {'t':>5}  {'units':>5}  {'tot':>7}  {'tgt':>7}  {'mov':>7}  "
      f"{'steer':>7}  {'coll':>7}  {'abl':>7}  {'intcp':>7}  {'warden':>7}  {'barrage':>7}  {'dmg':>7}")
print(f"  {'─'*5}  {'─'*5}  {'─'*7}  {'─'*7}  {'─'*7}  "
      f"{'─'*7}  {'─'*7}  {'─'*7}  {'─'*7}  {'─'*7}  {'─'*7}  {'─'*7}")

for tick in range(TICKS):
    t0 = time.perf_counter()

    process_commands(queue, store, tick)

    ts = time.perf_counter(); update_targeting(store, tmap, sim_rng, tick=tick); t_tgt.append((time.perf_counter()-ts)*1000)

    # Movement sub-timing: steer loop isolated by temporarily disabling collision,
    # then running collision separately.
    ts_mov = time.perf_counter()

    # Steer phase (no collision): time the per-unit loop + group updates only.
    orig_collision = config.HARD_COLLISION_ENABLED
    config.HARD_COLLISION_ENABLED = False
    ts = time.perf_counter(); update_movement(store, tmap, DT); t_mov_steer.append((time.perf_counter()-ts)*1000)
    config.HARD_COLLISION_ENABLED = orig_collision

    # Collision phase: run _resolve_collisions separately.
    if orig_collision:
        active = store.active_ids()
        positions_now = {uid: (store.data[uid, FIELD_X], store.data[uid, FIELD_Y]) for uid in active}
        # moved set: all units (since steer already ran, positions may have changed
        # relative to start of tick; use full active as conservative moved set)
        ts = time.perf_counter()
        _resolve_collisions(store, active, set(active), tmap, navmesh)
        t_mov_collide.append((time.perf_counter()-ts)*1000)
    else:
        t_mov_collide.append(0.0)

    t_mov_groups.append(0.0)  # groups already included in steer timing above
    t_mov.append((time.perf_counter()-ts_mov)*1000)

    ts = time.perf_counter(); deaths, ks = resolve_damage(store, tmap, DT); t_dmg.append((time.perf_counter()-ts)*1000)

    # Abilities sub-timing
    active = store.active_ids()

    # Main loop (cooldown ticks + state transitions, minus intercept/warden)
    ts = time.perf_counter()
    barrage_events = []
    for uid in active:
        if store.data[uid, 8] > 0:   # FIELD_ABILITY_COOLDOWN = 8
            store.data[uid, 8] -= 1
        state = store.data[uid, 9]   # FIELD_ABILITY_ACTIVE = 9
        if state == ABILITY_INACTIVE:
            continue
        ut = store.unit_type[uid]
        ability = ABILITY_MAP.get(ut)
        if ability == "surge":
            store.data[uid, 10] -= 1  # FIELD_ABILITY_DURATION = 10
            if store.data[uid, 10] <= 0:
                store.data[uid, 9] = ABILITY_INACTIVE
        elif ability == "brace":
            if state == 2.0:  # ABILITY_WINDUP
                store.data[uid, 10] -= 1
                if store.data[uid, 10] <= 0:
                    store.data[uid, 9] = 1.0 if store.data[uid, 8] > 0 else ABILITY_INACTIVE
        elif ability == "barrage":
            if state == 3.0:  # ABILITY_TELEGRAPH
                store.data[uid, 10] -= 1
                if store.data[uid, 10] <= 0:
                    barrage_events.append(uid)
                    store.data[uid, 9] = ABILITY_INACTIVE
        elif ability in ("fortify", "intercept"):
            store.data[uid, 10] -= 1
            if store.data[uid, 10] <= 0:
                store.data[uid, 9] = ABILITY_INACTIVE
    t_abl_main.append((time.perf_counter()-ts)*1000)

    # _check_intercept cost
    ts = time.perf_counter()
    for uid in active:
        if store.unit_type[uid] != "Interceptor":
            continue
        if store.data[uid, 9] != ABILITY_INACTIVE:
            continue
        if store.data[uid, 8] > 0:
            continue
        mx, my_ = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
        my_faction = store.faction[uid]
        my_layer = store.data[uid, FIELD_LAYER]
        detect_r_sq = config.INTERCEPT_DETECTION_RADIUS ** 2
        for other in active:
            if store.faction[other] == my_faction:
                continue
            if store.data[other, FIELD_LAYER] != my_layer:
                continue
            if store.category[other] != CATEGORY_STRIKE:
                continue
            dx = store.data[other, FIELD_X] - mx
            dy = store.data[other, FIELD_Y] - my_
            if dx * dx + dy * dy <= detect_r_sq:
                store.data[uid, 9] = 1.0
                store.data[uid, 10] = 1
                store.data[uid, 8] = config.INTERCEPT_COOLDOWN_TICKS
                store.auto_engage_target[uid] = other
                break
    t_abl_intercept.append((time.perf_counter()-ts)*1000)

    # _apply_warden_aura_healing cost
    ts = time.perf_counter()
    wardens = [uid for uid in active if store.unit_type[uid] == "Warden"]
    if wardens:
        aura_r_sq = config.WARDEN_AURA_RADIUS ** 2
        for uid in active:
            for warden in wardens:
                if store.faction[warden] != store.faction[uid]:
                    continue
                dx = store.data[uid, FIELD_X] - store.data[warden, FIELD_X]
                dy = store.data[uid, FIELD_Y] - store.data[warden, FIELD_Y]
                if dx * dx + dy * dy <= aura_r_sq:
                    store.data[uid, FIELD_HP] = min(
                        store.data[uid, FIELD_HP] + config.WARDEN_AURA_REPAIR_RATE,
                        store.data[uid, FIELD_MAX_HP],
                    )
                    break
    t_abl_warden.append((time.perf_counter()-ts)*1000)

    # resolve_barrage cost
    ts = time.perf_counter()
    if barrage_events:
        resolve_barrage(store, barrage_events)
    t_abl_barrage.append((time.perf_counter()-ts)*1000)

    update_fog_timers(store)

    t_tot.append((time.perf_counter()-t0)*1000)

    n_alive = len(store.active_ids())
    if SPIKE_WINDOW[0] <= tick < SPIKE_WINDOW[1]:
        tot = t_tot[-1]; tgt = t_tgt[-1]; mov = t_mov[-1]
        steer = t_mov_steer[-1]; coll = t_mov_collide[-1]
        abl = t_abl_main[-1]+t_abl_intercept[-1]+t_abl_warden[-1]+t_abl_barrage[-1]
        intcp = t_abl_intercept[-1]; wrd = t_abl_warden[-1]; bar = t_abl_barrage[-1]
        dmg = t_dmg[-1]
        print(f"  {tick:>5}  {n_alive:>5}  {tot:>7.1f}  {tgt:>7.1f}  {mov:>7.1f}  "
              f"{steer:>7.1f}  {coll:>7.1f}  {abl:>7.1f}  {intcp:>7.1f}  {wrd:>7.1f}  {bar:>7.1f}  {dmg:>7.1f}")

def stats(t):
    s = sorted(t); n = len(s)
    mean = sum(s)/n
    p95 = s[int(n*0.95)]
    mx = s[-1]
    # find tick of max
    tick_of_max = t.index(mx)
    return mean, p95, mx, tick_of_max

print(f"\nSummary over {TICKS} ticks:\n")
print(f"  {'Subsystem':<22} {'mean':>8} {'p95':>8} {'max':>8}  {'at tick':>8}")
print(f"  {'─'*22} {'─'*8} {'─'*8} {'─'*8}  {'─'*8}")

rows = [
    ("targeting",       t_tgt),
    ("movement total",  t_mov),
    ("  └ steer",       t_mov_steer),
    ("  └ collision",   t_mov_collide),
    ("abl: main loop",  t_abl_main),
    ("abl: intercept",  t_abl_intercept),
    ("abl: warden",     t_abl_warden),
    ("abl: barrage",    t_abl_barrage),
    ("damage",          t_dmg),
    ("TOTAL",           t_tot),
]
for label, t in rows:
    mn, p95, mx, tk = stats(t)
    print(f"  {label:<22} {mn:>7.2f}ms {p95:>7.2f}ms {mx:>7.2f}ms  t={tk:<6}")
