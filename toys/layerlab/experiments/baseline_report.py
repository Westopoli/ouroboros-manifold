"""Reads results/data/baseline.json and prints the baseline skill profile, C1 and C2 (README 4.2 to 4.4, SPEC 14.5)."""
import sys, json, math, os, statistics, itertools
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
    for map_set in ("space", "land"):
        print(f"\n######## {map_set} maps" + ("" if map_set == "space" else " (not counted toward a rule set's pass)"))
        _report_set([c for c in cells if c["map_set"] == map_set])

def _report_set(cells):
    configs = ["base", "LA", "LB", "LC"]
    for size in (8, 16, None):
        print(f"\n=== size {size if size else 'both'} (median premium over valid cells; n valid / n cells) ===")
        print("combo      " + "".join(f"{c:>16s}" for c in configs))
        tabs = {c: table(cells, c, size) for c in configs}
        keys = ["1", "2", "3", "4", "5", "12", "13", "14", "15", "23", "24", "25", "34", "35", "45", "123", "124", "125", "134", "135", "145", "234", "235", "245", "345", "1234", "1235", "1245", "1345", "2345", "12345"]
        for k in keys:
            print(f"S{k:<9s} " + "".join(f"{fmt(tabs[c][k]['median'])} ({tabs[c][k]['n_valid']:>3d}/{tabs[c][k]['n']:>3d})  " for c in configs))
    print("\n=== median premium read-out (both sizes): singles, full set, C3 ===")
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
    print(f"\ncells {tot}, valid with a premium {valid} ({100*valid/tot:.0f} percent)" if tot else "\nno cells")

def fit_loglog(points):
    """Least squares of ln y on ln x over (x, y, ...) points: slope, intercept, r2, n."""
    lx, ly = [math.log(p[0]) for p in points], [math.log(p[1]) for p in points]
    n = len(points)
    mx, my = sum(lx) / n, sum(ly) / n
    slope = sum((x - mx) * (y - my) for x, y in zip(lx, ly)) / sum((x - mx) ** 2 for x in lx)
    intercept = my - slope * mx
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(lx, ly))
    ss_tot = sum((y - my) ** 2 for y in ly)
    return {"slope": slope, "intercept": intercept, "r2": 1.0 - ss_res / ss_tot if ss_tot else float("nan"), "n": n}

def off_line(points, fit, thresh=0.25):
    """The points whose ln residual from the fitted line is more than thresh."""
    return [p for p in points if abs(math.log(p[1]) - (fit["slope"] * math.log(p[0]) + fit["intercept"])) > thresh]

def c1_share(cells, combo_key):
    """Share of the valid space cells of this combo whose firing_adv_equal is above 1.0; None when there are none."""
    ok = [c["firing_adv_equal"] for c in cells if c["combo"] == combo_key and c["valid"] and c["map_set"] == "space"
          and c["firing_adv_equal"] is not None]
    return sum(1 for x in ok if x > 1.0) / len(ok) if ok else None

def plot_rule_set(cells, config, out_path, map_set="space"):
    """Plot R* against firing_adv_at_rstar (log-log) for the valid cells of this rule set and map set, with the
    fitted line. Returns the text to print: slope, r squared, and the off-line points."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = [c for c in cells if c["config"] == config and c["map_set"] == map_set and c["valid"]
            and c["value"] is not None and c["firing_adv_at_rstar"] is not None]
    pts = [(c["firing_adv_at_rstar"], c["value"], c) for c in rows]
    head = f"{config} {map_set}"
    if len(pts) < 2:
        return f"{head}: {len(pts)} points, no fit"
    fit = fit_loglog(pts)
    off = off_line(pts, fit)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=12)
    ax.scatter([p[0] for p in off], [p[1] for p in off], s=40, facecolors="none", edgecolors="r")
    xs = [min(p[0] for p in pts), max(p[0] for p in pts)]
    ax.plot(xs, [math.exp(fit["slope"] * math.log(x) + fit["intercept"]) for x in xs], "k-", lw=1)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("firing_adv_at_rstar"); ax.set_ylabel("R*")
    ax.set_title(f"{head}: slope {fit['slope']:.2f}, r2 {fit['r2']:.2f}, n {fit['n']}")
    fig.savefig(out_path, dpi=100)
    plt.close(fig)
    lines = [f"{head}: n {fit['n']}, slope {fit['slope']:.2f}, r2 {fit['r2']:.2f} -> {out_path}"]
    if off:
        lines.append(f"  off the line by more than 0.25 ln (some other number decided the fight): {len(off)}")
        lines += [f"    sit {c['sit']} size {c['size']} combo {c['combo']}: R* {y:.2f}, firing_adv_at_rstar {x:.2f}"
                  for x, y, c in off]
    return "\n".join(lines)

def main(path="results/data/baseline.json", plots="results/plots"):
    cells = load(path)
    report(cells)
    os.makedirs(plots, exist_ok=True)
    for config in ["base", "LA", "LB", "LC"]:
        rows = [c for c in cells if c["config"] == config]
        print(f"\n=== {config}: C1, share of valid space cells where the skill alone has more firing units than the naive side at equal numbers (firing_adv_equal above 1.0) ===")
        for k in SK:
            share = c1_share(rows, k)
            print(f"  S{k}: " + ("no cells" if share is None else f"{share:.2f}"))
        print(f"=== {config}: C2, log-log fit of R* on firing_adv_at_rstar, and the off-line list ===")
        for map_set in ("space", "land"):
            print(plot_rule_set(cells, config, f"{plots}/{config}_{map_set}.png", map_set))

if __name__ == "__main__":
    main()
