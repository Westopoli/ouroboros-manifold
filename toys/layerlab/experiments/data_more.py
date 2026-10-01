"""More systematic datasets for the crossing search (README 6). D2: high ground (A one layer above B), lever
configurations swept as raw tables. D3: concave (P2/P4). One row per fight via layerlab.batch."""
import sys, time, itertools
sys.path.insert(0, ".")
from layerlab import scenario
from layerlab.scenario import set_path
from layerlab.batch import run_rows, write_rows
from experiments.p2_concave import build as p2

def d2():
    base = scenario.load("scenarios/x4_high_ground_both_answer.toml")
    base = set_path(base, "rules.vis_factor", [0.0, 0.0, 0.2, 0.5, 1.0, 0.5, 0.2, 0.0, 0.0])
    J = []
    for ru, d, nb, na in itertools.product((0.4, 0.55, 0.7, 0.8, 0.9, 1.0, 1.1), (0.5, 0.7, 0.85, 1.0, 1.15), (8, 10, 12, 14), (10,)):
        scn = set_path(set_path(set_path(set_path(base, "rules.range_mult[5]", ru), "rules.dmg_mult[5]", d), "groups[1].count", nb), "groups[0].count", na)
        st = {"rules.range_mult[5]": ru, "rules.dmg_mult[5]": d, "groups[1].count": nb, "groups[0].count": na}
        for s in range(20): J.append({"scenario": scn, "seed": s, "settings": st})
    return J

def d3():
    J = []
    for arc, na, R in itertools.product((40, 60, 80, 100, 120, 140, 160, 200, 240), (8, 9, 10, 11, 12), (400.0, 500.0, 700.0, 900.0)):
        try: scn = p2(n_a=na, arc=arc, R=R)
        except Exception: continue
        st = {"arc": arc, "groups[0].count": na, "R": R}
        for s in range(20): J.append({"scenario": scn, "seed": s, "settings": st})
    return J

if __name__ == "__main__":
    for name, J in (("d2_high_ground", d2()), ("d3_concave", d3())):
        t = time.time(); rows = run_rows(J, processes=8); write_rows(rows, f"results/data/{name}.csv")
        print(f"{name}: {len(rows)} rows in {time.time()-t:.0f}s; errors {sum(1 for r in rows if r['error'])}")
