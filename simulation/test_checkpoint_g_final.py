#!/usr/bin/env python3
import json
from collections import Counter

LIBRARY_DIR = "library"
TARGETS = {"people": 500, "places": 200, "units": 200, "factions": 100}
ARCHETYPE_FACTIONS = ["player", "conqueror", "fortifier", "opportunist"]

with open(f"{LIBRARY_DIR}/naming/names.json") as f:
    data = json.load(f)

print("=" * 60)
print("CHECKPOINT G FINAL: Eponym + Component + Target Verification")
print("=" * 60)

# Eponym check
print("\n=== Eponym Check ===")
eponyms = 0
for fid in data:
    for cat in data[fid]:
        for name in data[fid][cat]:
            parts = name.split()
            if len(parts) == 2 and parts[0] == parts[1]:
                eponyms += 1
                print(f"  FOUND: {fid}/{cat}: {name}")
print(f"  Eponyms remaining: {eponyms}")

# Component frequency spot-check
print("\n=== Component Frequency: player/places ===")
names = data["player"]["places"]
firsts = Counter(n.split()[0] for n in names if n.split())
print(f"  Pool size: {len(names)}")
print(f"  Top 5 first components: {firsts.most_common(5)}")
print(f"  Max first-component reuse: {firsts.most_common(1)[0][1] if firsts else 0}")

print("\n=== Component Frequency: player/units ===")
names = data["player"]["units"]
firsts = Counter(n.split()[0] for n in names if n.split())
lasts = Counter(n.split()[-1] for n in names if len(n.split()) >= 2)
print(f"  Pool size: {len(names)}")
print(f"  Top 5 first components: {firsts.most_common(5)}")
print(f"  Top 5 last components: {lasts.most_common(5)}")
print(f"  Max last-component reuse: {lasts.most_common(1)[0][1] if lasts else 0}")

# Target check
print("\n=== Target Check ===")
below = []
for fid in ARCHETYPE_FACTIONS:
    for cat in ["people", "places", "units", "factions"]:
        count = len(data[fid].get(cat, []))
        t = TARGETS[cat]
        status = "OK" if count >= t else f"BELOW (need {t - count} more)"
        if count < t:
            below.append((fid, cat, t - count))
        print(f"  {fid}/{cat}: {count} — {status}")

if below:
    print("\n=== Gaps Remaining ===")
    for fid, cat, gap in below:
        batches = -(-gap // 75)
        print(f"  {fid}/{cat}: {gap} names short ({batches} batch{'es' if batches > 1 else ''})")
else:
    print("\n  All targets met: YES")

print(f"\n{'=' * 60}")
