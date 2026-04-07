#!/usr/bin/env python3
import json
import os
import re
from collections import Counter

BATCH_DIR = "batch_output"

FACTION_IDS = [
    "player", "conqueror", "fortifier", "opportunist",
    "faction_05", "faction_06", "faction_07",
    "faction_08", "faction_09", "faction_10",
]

NAME_TARGETS = {"people": 500, "places": 200, "units": 200, "factions": 100}


def strip_markdown_fences(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def parse_file(filepath):
    with open(filepath) as f:
        raw = f.read()
    if not raw.strip():
        return None
    cleaned = strip_markdown_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def is_eponym(name):
    parts = name.strip().split()
    if len(parts) == 2 and parts[0] == parts[1]:
        return True
    return False


def is_alphabetically_enumerated(names):
    if len(names) < 10:
        return False
    first_chars = [n[0].upper() for n in names if n]
    runs = 0
    for i in range(1, len(first_chars)):
        if ord(first_chars[i]) == ord(first_chars[i-1]) + 1:
            runs += 1
    return runs > len(names) * 0.4


def find_overused_components(names, max_reuse=5):
    firsts = Counter()
    lasts = Counter()
    for n in names:
        parts = n.strip().split()
        if len(parts) >= 1:
            firsts[parts[0]] += 1
        if len(parts) >= 2:
            lasts[parts[-1]] += 1
    overused_first = {k for k, v in firsts.items() if v > max_reuse}
    overused_last = {k for k, v in lasts.items() if v > max_reuse}
    return overused_first, overused_last


def filter_names(names):
    seen = set()
    kept = []
    rejected_reasons = Counter()

    overused_first, overused_last = find_overused_components(names)

    first_usage = Counter()
    last_usage = Counter()

    for name in names:
        name = name.strip()
        if not name:
            rejected_reasons["empty"] += 1
            continue

        lower = name.lower()
        if lower in seen:
            rejected_reasons["duplicate"] += 1
            continue
        seen.add(lower)

        if is_eponym(name):
            rejected_reasons["eponym (first=last)"] += 1
            continue

        parts = name.split()
        first = parts[0] if parts else ""
        last = parts[-1] if len(parts) >= 2 else ""

        if first in overused_first and first_usage[first] >= 3:
            rejected_reasons["overused first component"] += 1
            continue
        if last and last in overused_last and last_usage[last] >= 3:
            rejected_reasons["overused last component"] += 1
            continue

        first_usage[first] += 1
        if last:
            last_usage[last] += 1
        kept.append(name)

    return kept, rejected_reasons


def analyze_naming_files():
    print("=" * 60)
    print("PHASE 2: NAMING SALVAGE ANALYSIS")
    print("=" * 60)

    files = sorted(f for f in os.listdir(BATCH_DIR) if f.endswith(".txt"))

    faction_pools = {}

    for f in files:
        is_naming = any(f"{fid}_" in f for fid in FACTION_IDS)
        if not is_naming:
            continue
        if "_b" in f:
            continue

        filepath = os.path.join(BATCH_DIR, f)
        if os.path.getsize(filepath) == 0:
            continue

        data = parse_file(filepath)
        if data is None:
            continue

        names = data.get("names", [])
        if not names:
            continue

        stem = f.replace(".txt", "")
        tokens = stem.split("_")
        tokens = tokens[1:]
        category = tokens[-1]
        faction_id = "_".join(tokens[:-1])

        kept, reasons = filter_names(names)
        key = (faction_id, category)
        faction_pools[key] = {
            "original": len(names),
            "kept": kept,
            "reasons": reasons,
        }

    print("\n--- Per-Faction/Category Breakdown ---\n")
    print(f"  {'Faction':<14} {'Category':<10} {'Original':>8} {'Kept':>6} {'Rejected':>8} {'Target':>7} {'Gap':>6}")
    print("  " + "-" * 65)

    total_kept = 0
    total_original = 0
    gaps = {}

    for (fid, cat) in sorted(faction_pools.keys()):
        pool = faction_pools[(fid, cat)]
        target = NAME_TARGETS.get(cat, 0)
        kept_count = len(pool["kept"])
        gap = max(0, target - kept_count)
        total_kept += kept_count
        total_original += pool["original"]
        gaps[(fid, cat)] = gap

        print(f"  {fid:<14} {cat:<10} {pool['original']:>8} {kept_count:>6} "
              f"{pool['original'] - kept_count:>8} {target:>7} {gap:>6}")

    print(f"\n  {'TOTAL':<14} {'':<10} {total_original:>8} {total_kept:>6}")

    print("\n--- Rejection Reasons (all factions) ---\n")
    all_reasons = Counter()
    for pool in faction_pools.values():
        all_reasons.update(pool["reasons"])
    for reason, count in all_reasons.most_common():
        print(f"  {reason}: {count}")

    print("\n--- Sample Kept Names (5 per faction) ---\n")
    shown_factions = set()
    for (fid, cat) in sorted(faction_pools.keys()):
        if fid in shown_factions:
            continue
        if cat != "people":
            continue
        shown_factions.add(fid)
        kept = faction_pools[(fid, cat)]["kept"]
        sample = kept[:5]
        print(f"  {fid} people: {', '.join(sample)}")

    print("\n--- Gaps to Fill (new prompts needed) ---\n")
    archetype_factions = {"player", "conqueror", "fortifier", "opportunist"}
    for (fid, cat) in sorted(gaps.keys()):
        if fid not in archetype_factions:
            continue
        gap = gaps[(fid, cat)]
        if gap > 0:
            batches = -(-gap // 75)  # ceiling division
            print(f"  {fid}/{cat}: need {gap} more names ({batches} batch{'es' if batches > 1 else ''})")
        else:
            print(f"  {fid}/{cat}: COMPLETE ({len(faction_pools[(fid, cat)]['kept'])} >= {NAME_TARGETS[cat]})")

    return faction_pools


def analyze_chronicle_files():
    print("\n" + "=" * 60)
    print("PHASE 2: CHRONICLE QUALITY CHECK")
    print("=" * 60)

    from library_validator import validate_structural, validate_dedup, VALID_SLOTS, WORD_LIMITS

    all_fragments = []
    category_slots = {}

    from library_builder import CATEGORIES
    for cat in CATEGORIES:
        category_slots[cat["name"]] = set(cat["required_slots"])

    for i in range(1, 21):
        pattern = f"{i:02d}_"
        matches = [f for f in os.listdir(BATCH_DIR)
                   if f.startswith(pattern) and not any(f"{fid}_" in f for fid in FACTION_IDS)]
        if not matches:
            print(f"  MISSING: chronicle file {i:02d}")
            continue

        filepath = os.path.join(BATCH_DIR, matches[0])
        if os.path.getsize(filepath) == 0:
            continue

        data = parse_file(filepath)
        if data is None:
            print(f"  ERROR parsing {matches[0]}")
            continue

        category = matches[0].replace(f"{i:02d}_", "").replace(".txt", "")
        for ftype in ("openings", "details", "closings"):
            for frag in data.get(ftype, []):
                frag["type"] = ftype.rstrip("s")
                if ftype == "closings":
                    frag["type"] = "closing"
                frag["category"] = category
                all_fragments.append(frag)

    print(f"\n  Total fragments parsed: {len(all_fragments)}")

    by_category = {}
    for frag in all_fragments:
        by_category.setdefault(frag["category"], {"opening": 0, "detail": 0, "closing": 0})
        by_category[frag["category"]][frag["type"]] += 1

    print(f"\n--- Fragment Counts by Category ---\n")
    print(f"  {'Category':<30} {'Open':>5} {'Detail':>7} {'Close':>6} {'Total':>6} {'OK?':>4}")
    print("  " + "-" * 60)
    for cat in sorted(by_category):
        counts = by_category[cat]
        total = sum(counts.values())
        ok = "YES" if counts["opening"] == 6 and counts["detail"] == 8 and counts["closing"] == 5 else "NO"
        print(f"  {cat:<30} {counts['opening']:>5} {counts['detail']:>7} {counts['closing']:>6} {total:>6} {ok:>4}")

    structural = validate_structural(all_fragments, category_required_slots=category_slots)
    print(f"\n--- Structural Issues ({len(structural)}) ---\n")
    if structural:
        for issue in structural[:20]:
            print(f"  [{issue['id']}] {issue['issue']}: {issue['detail']}")
        if len(structural) > 20:
            print(f"  ... and {len(structural) - 20} more")
    else:
        print("  None found!")

    dedup = validate_dedup(all_fragments)
    print(f"\n--- Dedup Matches ({len(dedup['matches'])}) ---\n")
    if dedup["matches"]:
        for m in dedup["matches"][:10]:
            print(f"  {m['id_a']} <-> {m['id_b']} (pool={m['pool']}, dist={m['distance']})")
        if len(dedup["matches"]) > 10:
            print(f"  ... and {len(dedup['matches']) - 10} more")
    else:
        print("  None found!")

    if dedup["thin_pools"]:
        print(f"\n--- Thin Pools ---")
        for tp in dedup["thin_pools"]:
            print(f"  {tp['pool']}: {tp['dupes']}/{tp['total']} ({tp['loss_pct']}% loss)")

    print("\n--- Sample Fragments (3 categories) ---\n")
    shown = 0
    for cat in sorted(by_category):
        if shown >= 3:
            break
        frags = [f for f in all_fragments if f["category"] == cat]
        opening = next((f for f in frags if f["type"] == "opening"), None)
        if opening:
            print(f"  [{cat}] {opening['id']}: \"{opening['text'][:120]}...\"" if len(opening['text']) > 120 else f"  [{cat}] {opening['id']}: \"{opening['text']}\"")
            shown += 1

    return all_fragments


if __name__ == "__main__":
    pools = analyze_naming_files()
    frags = analyze_chronicle_files()
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
