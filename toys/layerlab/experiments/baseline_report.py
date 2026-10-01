"""Reads results/data/baseline.json and prints the baseline skill profile (README 4.2, 4.3)."""
import sys, json, statistics, itertools
SK = "12345"
def med(xs): return statistics.median(xs) if xs else None
def fmt(x): return "  -  " if x is None else f"{x:5.2f}"

def load(path="results/data/baseline.json"):
    return json.load(open(path))

def table(cells, config, size=None):
    rows = [c for c in cells if c["config"] == config and (size is None or c["size"] == size)]
    out = {}
    for combo in ["".join(p) for k in range(0, 6) for p in itertools.combinations(SK, k)]:
        key = combo or "0"
        cs = [c for c in rows if c["combo"] == key]
        ok = [c["premium"] for c in cs if c["valid"] and c["premium"] is not None]
        out[key] = {"median": med(ok), "n_valid": len(ok), "n": len(cs), "n_above": sum(1 for c in cs if c["value"] is None and not c["valid"] is False)}
    return out

def report(cells):
    configs = ["base", "LA", "LB", "LC"]
    for size in (8, 16, None):
        print(f"\n=== size {size if size else 'both'} (median premium over valid cells; n valid / n cells) ===")
        print("combo      " + "".join(f"{c:>16s}" for c in configs))
        tabs = {c: table(cells, c, size) for c in configs}
        keys = ["1", "2", "3", "4", "5", "12", "13", "14", "15", "23", "24", "25", "34", "35", "45", "123", "124", "125", "134", "135", "145", "234", "235", "245", "345", "1234", "1235", "1245", "1345", "2345", "12345"]
        for k in keys:
            print(f"S{k:<9s} " + "".join(f"{fmt(tabs[c][k]['median'])} ({tabs[c][k]['n_valid']:>3d}/{tabs[c][k]['n']:>3d})  " for c in configs))
    print("\n=== condition read-out (both sizes), median premium; draft targets: C1 each skill alone ~1.3 (band 1.2-1.4); C2 all five >= 3 ===")
    for c in configs:
        t = table(cells, c, None)
        singles = {s: t[s]["median"] for s in SK}
        full = t["12345"]["median"]
        stack_viol = []
        for k in itertools.chain.from_iterable(itertools.combinations(SK, r) for r in (2, 3, 4, 5)):
            kk = "".join(k)
            parts = [t["".join(p)]["median"] for r in range(1, len(k)) for p in itertools.combinations(k, r)]
            parts = [p for p in parts if p is not None]
            if t[kk]["median"] is not None and parts and t[kk]["median"] < max(parts) - 1e-9: stack_viol.append(kk)
        print(f"{c:5s}: singles " + " ".join(f"S{s}={fmt(v).strip()}" for s, v in singles.items()) + f" | full set {fmt(full).strip()} | combos that do NOT beat their best part (C3): {len(stack_viol)}")
    print("\n=== by family, single skills, median premium (both sizes, all four tables pooled is NOT done: per table) ===")
    fams = sorted({c["family"] for c in cells})
    for cfg in configs:
        print(f"--- {cfg}")
        print("family          " + "".join(f"{'S'+s:>8s}" for s in SK) + "     S12345")
        for f in fams:
            row = []
            for k in list(SK) + ["12345"]:
                ok = [c["premium"] for c in cells if c["config"] == cfg and c["family"] == f and c["combo"] == k and c["valid"] and c["premium"] is not None]
                row.append(fmt(med(ok)))
            print(f"{f:15s} " + "".join(f"{r:>8s}" for r in row[:5]) + "  " + row[5])
    tot = len(cells); valid = sum(1 for c in cells if c["valid"] and c["premium"] is not None)
    print(f"\ncells {tot}, valid with a premium {valid} ({100*valid/tot:.0f} percent)")

if __name__ == "__main__":
    report(load())
