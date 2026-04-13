"""
test_j_plain_move_diag.py — Tick-by-tick diagnostic for plain move behavior.

Manually calls each engine subsystem and prints state between steps.
Only runs 10 ticks. No engine file modifications.

Isolates: did Strike receive the move command? did they move?
"""
import sys
import math
sys.path.insert(0, ".")

import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_SPEED, FIELD_ATTACK_RANGE
from command import Command, CommandQueue, process_commands
from damage import update_targeting
from movement import update_movement
from ability import update_abilities
from test_maps import open_field

tmap  = open_field()
store = UnitStore()
DT    = config.TACTICAL_TICK_DURATION

# 3 Raiders (Strike, faction 0) on the left
# 3 Vanguards (Line, faction 1) in the center — no commands, just stand there
strike_uids = []
for i in range(3):
    uid = store.spawn("Raider", 0, 400.0 + i * 50.0, 2000.0)
    strike_uids.append(uid)

line_uids = []
for i in range(3):
    uid = store.spawn("Vanguard", 1, 2000.0 + i * 50.0, 2000.0)
    line_uids.append(uid)

# Issue plain move for Strike to reach x=3600
queue = CommandQueue()
queue.add(Command(tick=0, type="move", unit_ids=strike_uids,
                  params={"target_x": 3600.0, "target_y": 2000.0}))

import random
rng = random.Random(1)

print(f"\n{'═'*70}")
print(f"  PLAIN MOVE DIAGNOSTIC  —  3 Raiders vs 3 stationary Vanguards")
print(f"  Strike command: plain move → (3600, 2000)")
print(f"  Raider attack_range={config.UNIT_STATS['Raider']['attack_range']} wu  "
      f"Vanguard attack_range={config.UNIT_STATS['Vanguard']['attack_range']} wu")
print(f"{'═'*70}")

print(f"\n  Initial positions:")
for uid in strike_uids:
    print(f"    Strike uid={uid}  x={store.data[uid, FIELD_X]:.1f}  "
          f"has_move_target={store.has_move_target[uid]}  "
          f"plain_moving={store.plain_moving[uid]}  "
          f"auto_engage={store.auto_engage_target[uid]}")
for uid in line_uids:
    print(f"    Line   uid={uid}  x={store.data[uid, FIELD_X]:.1f}  "
          f"has_move_target={store.has_move_target[uid]}  "
          f"auto_engage={store.auto_engage_target[uid]}")

for tick in range(10):
    print(f"\n{'─'*70}")
    print(f"  TICK {tick}")
    print(f"{'─'*70}")

    # ── 1. Commands ───────────────────────────────────────────────────────────
    cmds = queue.get(tick)
    if cmds:
        print(f"\n  [COMMANDS] Processing {len(cmds)} command(s) at tick {tick}:")
        for cmd in cmds:
            print(f"    type={cmd.type}  units={cmd.unit_ids}  params={cmd.params}")
    else:
        print(f"\n  [COMMANDS] No commands at tick {tick}")

    process_commands(queue, store, tick)

    print(f"\n  [AFTER COMMANDS] Strike state:")
    for uid in strike_uids:
        tx = store.target_x[uid] if store.has_move_target[uid] else None
        ty = store.target_y[uid] if store.has_move_target[uid] else None
        print(f"    uid={uid}  x={store.data[uid, FIELD_X]:.1f}  "
              f"has_move_target={store.has_move_target[uid]}  "
              f"plain_moving={store.plain_moving[uid]}  "
              f"attack_moving={store.attack_moving[uid]}  "
              f"target=({tx},{ty})")

    # ── 2. Targeting ──────────────────────────────────────────────────────────
    print(f"\n  [TARGETING] Running update_targeting...")

    # Manually replicate update_targeting logic to show what happens per unit
    # First rebuild the spatial hash (update_targeting does this)
    tmap.spatial_hash.clear()
    active = store.active_ids()
    for uid in active:
        tmap.spatial_hash.insert(uid, store.data[uid, FIELD_X], store.data[uid, FIELD_Y])

    for uid in active:
        if store.plain_moving[uid]:
            print(f"    uid={uid} ({store.unit_type[uid]})  SKIPPED — plain_moving=True")
            continue
        # Check what target they'd pick
        my_faction = store.faction[uid]
        mx, my_ = store.data[uid, FIELD_X], store.data[uid, FIELD_Y]
        engage_range = store.data[uid, FIELD_ATTACK_RANGE]
        candidates = []
        for other in sorted(tmap.spatial_hash.query(mx, my_, engage_range)):
            if store.faction[other] == my_faction:
                continue
            dx = store.data[other, FIELD_X] - mx
            dy = store.data[other, FIELD_Y] - my_
            d = math.sqrt(dx * dx + dy * dy)
            if d <= engage_range:
                candidates.append((other, d))
        if candidates:
            nearest = min(candidates, key=lambda c: c[1])
            print(f"    uid={uid} ({store.unit_type[uid]})  "
                  f"candidates={[(c[0], f'{c[1]:.0f}wu') for c in candidates]}  "
                  f"→ will target uid={nearest[0]} at {nearest[1]:.0f}wu")
        else:
            print(f"    uid={uid} ({store.unit_type[uid]})  "
                  f"no enemies in attack_range ({engage_range:.0f}wu)")

    # Actually run it
    update_targeting(store, tmap, rng)

    print(f"\n  [AFTER TARGETING] auto_engage_target values:")
    for uid in active:
        tgt = store.auto_engage_target[uid]
        print(f"    uid={uid} ({store.unit_type[uid]})  auto_engage_target={tgt}  "
              f"plain_moving={store.plain_moving[uid]}")

    # ── 3. Movement ───────────────────────────────────────────────────────────
    print(f"\n  [MOVEMENT] Before update_movement:")
    for uid in strike_uids:
        if store.alive[uid]:
            print(f"    uid={uid}  x={store.data[uid, FIELD_X]:.2f}  "
                  f"has_move_target={store.has_move_target[uid]}  "
                  f"plain_moving={store.plain_moving[uid]}  "
                  f"auto_engage={store.auto_engage_target[uid]}  "
                  f"attack_moving={store.attack_moving[uid]}")

    prev_x = {uid: store.data[uid, FIELD_X] for uid in strike_uids if store.alive[uid]}

    update_movement(store, tmap, DT)

    print(f"\n  [AFTER MOVEMENT] Strike positions:")
    for uid in strike_uids:
        if store.alive[uid]:
            dx = store.data[uid, FIELD_X] - prev_x[uid]
            moved = abs(dx) > 0.001
            print(f"    uid={uid}  x={store.data[uid, FIELD_X]:.2f}  "
                  f"Δx={dx:+.2f}  {'MOVED ✓' if moved else 'DID NOT MOVE ✗'}")

print(f"\n{'═'*70}")
print(f"  DIAGNOSIS:")

all_moved = all(store.data[uid, FIELD_X] > 400.0 for uid in strike_uids if store.alive[uid])
if all_moved:
    print(f"  All Strike units moved → command was received and followed")
else:
    print(f"  Some Strike units did NOT move — check output above for cause")
    for uid in strike_uids:
        if store.alive[uid] and store.data[uid, FIELD_X] <= 400.0:
            print(f"    uid={uid} stuck at x={store.data[uid, FIELD_X]:.2f}")
            print(f"      has_move_target={store.has_move_target[uid]}")
            print(f"      plain_moving={store.plain_moving[uid]}")
            print(f"      auto_engage={store.auto_engage_target[uid]}")
print(f"{'═'*70}\n")
