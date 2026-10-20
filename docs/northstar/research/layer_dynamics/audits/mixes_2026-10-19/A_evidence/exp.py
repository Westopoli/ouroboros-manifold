import sys, json, time, collections
sys.path.insert(0, ".")
from mixlab import *
from scripts.skilllab import scan as scan_mod
from scripts.skilllab.pool import FightPool

OUT = "/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/b1e8769e-404e-4263-be23-8535a58b0e59/scratchpad/mix_A/"
SEEDS = range(4)

def jobs16(fn, heads=16):
    b = scan_build(fn)
    return [(b(heads, sw), s, sw) for sw in (False, True) for s in SEEDS]

def summarize(results):
    c = collections.Counter(r.outcome for r in results)
    a = collections.Counter(r.agreement for r in results)
    return dict(outcomes=dict(c), agreement=dict(a), mean_margin=round(sum(r.margin for r in results) / len(results), 3),
                mean_ticks=round(sum(r.ticks for r in results) / len(results)), rows=[row(r) for r in results])

MIXES = {
    "M0": (("Vanguard", 16),), "M1": (("Vanguard", 8), ("Raider", 8)), "M2": (("Vanguard", 8), ("Interceptor", 8)),
    "M3": (("Vanguard", 8), ("Bombard", 8)), "M3b": (("Vanguard", 7), ("Raider", 1), ("Bombard", 8)),
    "M4": (("Vanguard", 8), ("Bastion", 8)),
    "N1_RBo": (("Raider", 8), ("Bombard", 8)), "N2_VW": (("Vanguard", 12), ("Warden", 4)),
    "N3_VRBo": (("Vanguard", 6), ("Raider", 5), ("Bombard", 5)), "N4_IBo": (("Interceptor", 8), ("Bombard", 8)),
    "N5_RBa": (("Raider", 8), ("Bastion", 8)),
    "N6_all": (("Vanguard", 3), ("Warden", 2), ("Raider", 3), ("Interceptor", 3), ("Bombard", 3), ("Bastion", 2)),
}

# --- plays (side 0 arranged, side 1 the same mix in a naive blob) ---
def p_rps():   # N3: each type on the type it beats: Vanguards front, Bombards behind, Raiders swing wide to the enemy rear
    x = -GAP / 2
    g = [line(0, "Vanguard", 6, x + 60), line(0, "Bombard", 5, x - 200),
         ps._g(0, "Raider", 5, "blob", x, 350.0, radius=80 + 12 * math.sqrt(5), goal=(GAP / 2 + 150, 0.0))]
    return make_setup(g + enemy(MIXES["N3_VRBo"]), types(["Vanguard", "Raider", "Bombard"]))

def p_art_above(mix_name, spotter):
    def fn():
        x = -GAP / 2
        g = [blob(0, "Bombard", 8, x - 100, layer=2), blob(0, spotter, 8, x)]
        return make_setup(g + enemy(MIXES[mix_name]), types([spotter, "Bombard"]))
    return fn

def p_warden_back():   # N2: Vanguards in a line, Wardens 150 behind spaced 110 so every Vanguard sits inside one aura
    x = -GAP / 2
    g = [line(0, "Vanguard", 12, x), line(0, "Warden", 4, x - 150, spacing=110.0)]
    return make_setup(g + enemy(MIXES["N2_VW"]), types(["Vanguard", "Warden"]))

def p_screen(mix_name, front, back):
    def fn():
        x = -GAP / 2
        m = dict(MIXES[mix_name])
        g = [line(0, front, m[front], x + 60), line(0, back, m[back], x - 60)]
        return make_setup(g + enemy(MIXES[mix_name]), types([front, back]))
    return fn

def clone_warden():  # A1: side 0 builtin Wardens, side 1 cloned Wardens ("base": "Warden"); labelled asymmetric engine check
    x = -GAP / 2
    g = [blob(0, "Vanguard", 8, x), blob(0, "Warden", 8, x), blob(1, "Vanguard", 8, -x), blob(1, "WardenC", 8, -x)]
    return make_setup(g, {"WardenC": {"base": "Warden"}})

def clone_bastion(clone):  # A2: 8 Raiders (side 0) against 4 Bastions builtin or cloned (side 1)
    def fn():
        x = -GAP / 2
        b = "BastionC" if clone else "Bastion"
        g = [blob(0, "Raider", 8, x), blob(1, b, 4, -x)]
        return make_setup(g, {"BastionC": {"base": "Bastion"}} if clone else {})
    return fn

def run_fixed(pool, fn, heads=16):
    return summarize(pool.map(jobs16(fn, heads)))

def run_scan(pool, fn, reps=2):
    t = time.time()
    r = scan_mod.scan(scan_build(fn), 16, 8, 48, replicates=reps, map_fn=pool.map)
    cells = [dict(h=c.enemy_heads, won=c.won, defect=c.defect, m=round(c.mean_margin, 3),
                  out=dict(collections.Counter(f.outcome for f in c.fights)),
                  agree=dict(collections.Counter(f.agreement for f in c.fights))) for c in r.cells]
    n = sum(len(c.fights) for c in r.cells)
    return dict(beats=r.beats, loses_to=r.loses_to, ceiling=r.ceiling_hit, multi_flip=r.multi_flip, fights=n,
                wall_s=round(time.time() - t, 1), cells=cells)

if __name__ == "__main__":
    which = sys.argv[1]
    res = {}
    t0 = time.time()
    with FightPool(14) as pool:
        if which == "engine":
            res["A1_warden_builtin_vs_clone"] = run_fixed(pool, clone_warden)
            res["A2_raiders_vs_bastion_builtin"] = run_fixed(pool, clone_bastion(False), heads=4)
            res["A2_raiders_vs_bastion_clone"] = run_fixed(pool, clone_bastion(True), heads=4)
        elif which == "mirror":
            for k, m in MIXES.items():
                res[k] = {"fixed16": run_fixed(pool, naive(m)), "scan": run_scan(pool, naive(m))}
                print(k, res[k]["fixed16"]["outcomes"], res[k]["fixed16"]["agreement"], res[k]["scan"]["beats"], res[k]["scan"]["loses_to"], res[k]["scan"]["fights"], flush=True)
        elif which == "plays":
            P = {"rps_N3": p_rps, "art_above_IBo": p_art_above("N4_IBo", "Interceptor"),
                 "art_above_VBo": p_art_above("M3", "Vanguard"), "warden_back_N2": p_warden_back,
                 "screen_RBo_Rfront": p_screen("N1_RBo", "Raider", "Bombard"),
                 "screen_VBo_M3": p_screen("M3", "Vanguard", "Bombard")}
            for k, fn in P.items():
                res[k] = {"fixed16": run_fixed(pool, fn), "scan": run_scan(pool, fn)}
                print(k, res[k]["fixed16"]["outcomes"], res[k]["fixed16"]["agreement"], res[k]["scan"]["beats"], res[k]["scan"]["loses_to"], res[k]["scan"]["ceiling"], res[k]["scan"]["fights"], flush=True)
    res["_wall_s"] = round(time.time() - t0, 1)
    json.dump(res, open(OUT + "exp_%s.json" % which, "w"), indent=1, default=str)
    print("wall", res["_wall_s"])
