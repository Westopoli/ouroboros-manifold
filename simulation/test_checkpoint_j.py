#!/usr/bin/env python3
import json
import os
import sys
import random

sys.path.insert(0, os.path.dirname(__file__))

from naming_system import NamingSystem


def load_naming_system():
    ns = NamingSystem()
    names_path = os.path.join("library", "naming", "names.json")
    with open(names_path) as f:
        all_names = json.load(f)
    for fid, cats in all_names.items():
        for cat, names in cats.items():
            ns.load_pool(fid, cat, names)
    return ns


def load_variable_subsets(ns):
    path = os.path.join("prompts", "variable_subsets.json")
    with open(path) as f:
        subsets = json.load(f)
    for fid, subset in subsets.items():
        ns.set_variable_subset(fid, subset)
    return subsets


def diff_subsets(parent, child):
    diffs = []
    for cat in parent:
        p_vals = set(parent[cat])
        c_vals = set(child.get(cat, []))
        removed = p_vals - c_vals
        added = c_vals - p_vals
        if removed or added:
            diffs.append((cat, removed, added))
    return diffs


def main():
    print("=" * 60)
    print("CHECKPOINT J: Schism Cultural Drift")
    print("=" * 60)

    rng = random.Random(42)
    ns = load_naming_system()
    subsets = load_variable_subsets(ns)

    parent_fid = "conqueror"
    parent_subset = subsets[parent_fid]

    print(f"\nParent faction: {parent_fid}")
    print(f"  Subset:")
    for cat, vals in parent_subset.items():
        print(f"    {cat}: {vals}")

    # Create 3 breakaway factions
    breakaway_ids = []
    for i in range(1, 4):
        child_fid = f"breakaway_{i}"
        ns.derive_schism_subset(parent_fid, child_fid, rng)
        ns.ensure_pool(child_fid, "people", parent_fid)
        breakaway_ids.append(child_fid)

    # Print subset comparisons
    print(f"\n{'='*60}")
    print("SUBSET COMPARISON")
    print(f"{'='*60}")

    all_pass = True
    for child_fid in breakaway_ids:
        child_subset = ns.get_variable_subset(child_fid)
        if child_subset is None:
            print(f"\n  {child_fid}: NO SUBSET (FAIL)")
            all_pass = False
            continue

        diffs = diff_subsets(parent_subset, child_subset)
        n_diffs = sum(len(r) + len(a) for _, r, a in diffs)

        print(f"\n  {child_fid}:")
        for cat, vals in child_subset.items():
            parent_vals = set(parent_subset.get(cat, []))
            child_vals = set(vals)
            markers = []
            for v in vals:
                if v not in parent_vals:
                    markers.append(f"  + {v}")
            for v in parent_vals - child_vals:
                markers.append(f"  - {v}")
            print(f"    {cat}: {vals}")
            for m in markers:
                print(f"      {m}")

        if len(diffs) == 1 and n_diffs == 2:
            cat, removed, added = diffs[0]
            print(f"    PASS: exactly 1 swap in '{cat}' ({removed.pop()} → {added.pop()})")
        else:
            print(f"    FAIL: expected 1 swap, found {len(diffs)} changed categories, {n_diffs} total diffs")
            all_pass = False

    # Draw 5 names from parent and each breakaway
    print(f"\n{'='*60}")
    print("NAME COMPARISON")
    print(f"{'='*60}")

    print(f"\n  {parent_fid} (parent):")
    for i in range(5):
        name = ns.get_name(parent_fid, "people", current_tick=0, rng=rng)
        print(f"    {name}")

    for child_fid in breakaway_ids:
        print(f"\n  {child_fid}:")
        for i in range(5):
            name = ns.get_name(child_fid, "people", current_tick=0, rng=rng)
            print(f"    {name}")

    print(f"\n{'='*60}")
    print(f"CHECKPOINT J: {'PASS' if all_pass else 'FAIL'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
