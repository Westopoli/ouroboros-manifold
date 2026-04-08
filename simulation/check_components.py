#!/usr/bin/env python3
import json, re
from collections import Counter

for fname, label in [("22_player_places.txt", "player/places"), ("23_player_units.txt", "player/units")]:
    with open(f"batch_output/{fname}") as f:
        raw = f.read().strip()
    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
    raw = re.sub(r"\n?```\s*$", "", raw)
    data = json.loads(raw)
    names = data["names"]
    firsts = Counter()
    lasts = Counter()
    for n in names:
        p = n.split()
        if p:
            firsts[p[0]] += 1
        if len(p) >= 2:
            lasts[p[-1]] += 1
    print(f"\n{label} ({len(names)} names):")
    print("  Top first components:", firsts.most_common(5))
    print("  Top last components:", lasts.most_common(5))
    over10 = sum(1 for n in names if firsts[n.split()[0]] > 10 or (len(n.split()) >= 2 and lasts[n.split()[-1]] > 10))
    print(f"  Names with component used >10 times: {over10}")
