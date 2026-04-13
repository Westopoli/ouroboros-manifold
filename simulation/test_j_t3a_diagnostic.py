"""
test_j_t3a_diagnostic.py — Tick-by-tick diagnostic for the T3a gradient scenario.

Runs a single T3a engagement (seed 1) and prints state at key moments:
  - Every 50 ticks during plain_move phase (are units moving toward flanking pos?)
  - Ticks 190–215 one-by-one (did the attack_move command land? did flags change?)
  - Every 20 ticks after attack_move until first contact

Isolates: do units reach the flanking position? do they receive the attack_move?
where do they stall or get stuck?

Run:  python3 test_j_t3a_diagnostic.py
"""
import sys
import math
import random
sys.path.insert(0, ".")

import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP
from command import Command, CommandQueue
from tactical_engine import TacticalEngine
from test_maps import open_field

FACTION_S = 0
FACTION_L = 1
N  = 12
DT = config.TACTICAL_TICK_DURATION

rng   = random.Random(1)
tmap  = open_field()
store = UnitStore()


def _spawn_strike(store, cx, cy, rng):
    uids  = []
    types = ["Raider"] * 6 + ["Interceptor"] * 6
    rng.shuffle(types)
    for i, ut in enumerate(types):
        x = cx + (i % 4) * 45.0 + rng.uniform(-6, 6)
        y = cy + (i // 4) * 45.0 + rng.uniform(-6, 6)
        uids.append(store.spawn(ut, FACTION_S, x, y))
    return uids


def _spawn_line(store, cx, cy, rng):
    uids  = []
    types = ["Vanguard"] * 8 + ["Warden"] * 4
    rng.shuffle(types)
    for i, ut in enumerate(types):
        x = cx + (i % 2) * 40.0 + rng.uniform(-4, 4)
        y = cy + (i // 2) * 70.0 + rng.uniform(-4, 4)
        uids.append(store.spawn(ut, FACTION_L, x, y))
    return uids


su = _spawn_strike(store, 200.0, 1600.0, rng)
lu = _spawn_line(store, 1980.0, 1400.0, rng)

line_mid_y = 1400.0 + (N // 4) * 70.0  # same formula as test_j_gradient.py

queue = CommandQueue()
queue.add(Command(tick=0,   type="move",        unit_ids=su,
                  params={"target_x": 700.0,   "target_y": line_mid_y}))
queue.add(Command(tick=200, type="attack_move", unit_ids=su,
                  params={"target_x": 2000.0,  "target_y": line_mid_y}))

engine = TacticalEngine(tmap, store, seed=1)
engine.command_queue = queue

print(f"\n{'═'*70}")
print(f"  T3a DIAGNOSTIC  —  {N} Strike vs {N} Line (column)")
print(f"  Phase 1: plain move  → (700, {line_mid_y:.0f})")
print(f"  Phase 2 at tick 200: attack_move → (2000, {line_mid_y:.0f})")
print(f"  Line column y-range: 1400 – {1400 + (N//2 - 1)*70:.0f}")
print(f"{'═'*70}")

print(f"\n  Initial Strike positions:")
for uid in su:
    print(f"    uid={uid} ({store.unit_type[uid]:12s})  "
          f"x={store.data[uid, FIELD_X]:.1f}  y={store.data[uid, FIELD_Y]:.1f}")
print(f"\n  Initial Line positions:")
for uid in lu:
    print(f"    uid={uid} ({store.unit_type[uid]:10s})  "
          f"x={store.data[uid, FIELD_X]:.1f}  y={store.data[uid, FIELD_Y]:.1f}")


def snapshot_strike(tick, su, store, label=""):
    alive = [uid for uid in su if store.alive[uid]]
    if not alive:
        print(f"  tick={tick:4d}  Strike: ALL DEAD")
        return
    xs      = [store.data[uid, FIELD_X] for uid in alive]
    ys      = [store.data[uid, FIELD_Y] for uid in alive]
    plain   = sum(1 for uid in alive if store.plain_moving[uid])
    atk_mv  = sum(1 for uid in alive if store.attack_moving[uid])
    has_tgt = sum(1 for uid in alive if store.has_move_target[uid])
    engaged = sum(1 for uid in alive if store.auto_engage_target[uid] >= 0)
    print(f"  tick={tick:4d}  {label}")
    print(f"    alive={len(alive)}  "
          f"x=[{min(xs):.0f}–{max(xs):.0f}]  y=[{min(ys):.0f}–{max(ys):.0f}]  "
          f"has_move_tgt={has_tgt}  plain_moving={plain}  "
          f"attack_moving={atk_mv}  engaged={engaged}")


first_contact = None
MAX_TICKS = 700

for _ in range(MAX_TICKS):
    engine.step()
    tick = engine.tick

    # Phase 1: summary every 50 ticks
    if tick % 50 == 0 and tick < 190:
        snapshot_strike(tick, su, store, "[plain move phase]")

    # Command boundary: every single tick 190–215
    if 190 <= tick <= 215:
        alive = [uid for uid in su if store.alive[uid]]
        uid0  = alive[0] if alive else None
        if uid0 is not None:
            tx = store.target_x[uid0] if store.has_move_target[uid0] else None
            ty = store.target_y[uid0] if store.has_move_target[uid0] else None
            print(f"  tick={tick:4d}  uid={uid0}  "
                  f"x={store.data[uid0, FIELD_X]:.1f}  y={store.data[uid0, FIELD_Y]:.1f}  "
                  f"plain={store.plain_moving[uid0]}  "
                  f"atk_mv={store.attack_moving[uid0]}  "
                  f"has_tgt={store.has_move_target[uid0]}  "
                  f"target=({tx},{ty})  "
                  f"engage={store.auto_engage_target[uid0]}")

    # After attack_move: every 20 ticks until first contact
    if tick > 215 and first_contact is None and tick % 20 == 0:
        snapshot_strike(tick, su, store, "[approaching]")

    # First contact detection
    if first_contact is None:
        for uid in su:
            if store.alive[uid] and store.auto_engage_target[uid] >= 0:
                first_contact = tick
                print(f"\n  *** FIRST CONTACT at tick={tick} ({tick*DT:.1f}s) ***")
                snapshot_strike(tick, su, store, "[contact]")

                alive_l   = [uid for uid in lu if store.alive[uid]]
                engaged_l = [uid for uid in alive_l if store.auto_engage_target[uid] >= 0]
                lxs = [store.data[uid, FIELD_X] for uid in alive_l]
                lys = [store.data[uid, FIELD_Y] for uid in alive_l]
                print(f"    Line alive={len(alive_l)}  engaged={len(engaged_l)}")
                if lxs:
                    print(f"    Line x=[{min(lxs):.0f}–{max(lxs):.0f}]  "
                          f"y=[{min(lys):.0f}–{max(lys):.0f}]")
                break

    if engine.is_terminal():
        print(f"\n  Terminal at tick={tick} ({tick*DT:.1f}s)")
        break

    if first_contact is not None and tick >= first_contact + 50:
        print(f"\n  Stopping 50 ticks after first contact.")
        break

print(f"\n{'─'*70}")
alive_s = [uid for uid in su if store.alive[uid]]
alive_l = [uid for uid in lu if store.alive[uid]]
print(f"  Strike alive: {len(alive_s)}/{N}")
print(f"  Line alive:   {len(alive_l)}/{N}")
if first_contact:
    print(f"  First contact: tick={first_contact} ({first_contact*DT:.1f}s)")
else:
    print(f"  No contact detected in {MAX_TICKS} ticks")
print(f"{'═'*70}\n")
