#!/usr/bin/env python3
import json
from library_validator import validate_all
from library_builder import CATEGORIES

LIBRARY_DIR = "library"
NAME_TARGETS = {"people": 500, "places": 200, "units": 200, "factions": 100}
ARCHETYPE_FACTIONS = ["player", "conqueror", "fortifier", "opportunist"]

print("=" * 60)
print("CHECKPOINT G: Production Library Validation")
print("=" * 60)

# ── Chronicle ──
with open(f"{LIBRARY_DIR}/chronicle/fragments.json") as f:
    fragments = json.load(f)

category_slots = {}
for cat in CATEGORIES:
    category_slots[cat["name"]] = set(cat["required_slots"])

report = validate_all(fragments, category_required_slots=category_slots)

print(f"\n--- Chronicle: {len(fragments)} fragments ---\n")

by_cat = {}
for frag in fragments:
    c = frag["category"]
    t = frag["type"]
    by_cat.setdefault(c, {"opening": 0, "detail": 0, "closing": 0})
    by_cat[c][t] += 1

print(f"  {'Category':<30} {'O':>3} {'D':>3} {'C':>3} {'Tot':>4} {'OK':>3}")
print("  " + "-" * 48)
all_ok = True
for cat in sorted(by_cat):
    counts = by_cat[cat]
    total = sum(counts.values())
    ok = counts["opening"] == 6 and counts["detail"] == 8 and counts["closing"] == 5
    if not ok:
        all_ok = False
    print(f"  {cat:<30} {counts['opening']:>3} {counts['detail']:>3} {counts['closing']:>3} {total:>4} {'YES' if ok else 'NO':>3}")
print(f"\n  All categories 6/8/5: {'YES' if all_ok else 'NO'}")

print(f"\n  Structural issues: {report['summary']['structural_failures']}")
for issue in report["structural"][:10]:
    print(f"    [{issue['id']}] {issue['issue']}: {issue['detail']}")
if report["summary"]["structural_failures"] > 10:
    print(f"    ... and {report['summary']['structural_failures'] - 10} more")

print(f"  Dedup matches: {report['summary']['dedup_matches']}")
for m in report["dedup"]["matches"][:5]:
    print(f"    {m['id_a']} <-> {m['id_b']} (dist={m['distance']})")

print(f"  Tone flags: {report['summary']['tone_flags']}")

# Sample fragments
print(f"\n--- Sample Fragments (3 categories) ---\n")
shown = set()
for frag in fragments:
    if frag["category"] in shown:
        continue
    if frag["type"] == "opening":
        print(f"  [{frag['category']}] {frag['id']}:")
        print(f"    \"{frag['text']}\"\n")
        shown.add(frag["category"])
    if len(shown) >= 3:
        break

# ── Naming ──
with open(f"{LIBRARY_DIR}/naming/names.json") as f:
    all_names = json.load(f)

print("\n--- Naming Pools ---\n")
print(f"  {'Faction':<14} {'people':>7} {'places':>7} {'units':>7} {'factions':>9}")
print("  " + "-" * 48)

naming_ok = True
for fid in ARCHETYPE_FACTIONS:
    if fid not in all_names:
        print(f"  {fid:<14} MISSING")
        naming_ok = False
        continue
    pools = all_names[fid]
    cols = []
    for cat in ["people", "places", "units", "factions"]:
        count = len(pools.get(cat, []))
        target = NAME_TARGETS[cat]
        marker = "" if count >= target else " *"
        if count < target:
            naming_ok = False
        cols.append(f"{count}{marker}")
    print(f"  {fid:<14} {cols[0]:>7} {cols[1]:>7} {cols[2]:>7} {cols[3]:>9}")

print(f"\n  All targets met: {'YES' if naming_ok else 'NO — pools marked * are below target'}")

# Sample names
print(f"\n--- Sample Names (5 per faction) ---\n")
for fid in ARCHETYPE_FACTIONS:
    if fid not in all_names:
        continue
    people = all_names[fid].get("people", [])
    # Pick evenly spaced samples
    if len(people) >= 5:
        step = len(people) // 5
        samples = [people[i * step] for i in range(5)]
    else:
        samples = people[:5]
    print(f"  {fid}: {', '.join(samples)}")

print(f"\n{'=' * 60}")
print("CHECKPOINT G COMPLETE")
print("=" * 60)
