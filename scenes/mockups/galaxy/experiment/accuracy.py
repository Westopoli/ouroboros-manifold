#!/usr/bin/env python3
"""Throwaway: first-surface accuracy of the baked grid (trilinear, CPU) vs the exact formulas.
Usage: accuracy.py <dump_dir> <galaxy_key> -> prints/writes JSON to results/accuracy_<key>.json
Also validates the GPU-filled grid against a numpy re-bake (max abs diff)."""
import json, sys, os, numpy as np

R = 14.0; GAP = 0.5; ISO = 0.6

def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def exact_net(P, S, nfac):
    """P: (M,3); S: (n,5) pos,sn,fid. returns net, rival, fid of best faction."""
    M = P.shape[0]
    d2 = ((P[:, None, :] - S[None, :, :3]) ** 2).sum(-1)
    r = R * (0.6 + 0.4 * S[:, 3])
    k = np.clip(1 - d2 / (r * r)[None, :], 0, None) ** 3
    own = np.zeros((M, nfac)); mk = np.zeros((M, nfac))
    for f in range(nfac):
        m = S[:, 4] == f
        if m.any():
            own[:, f] = k[:, m].sum(1); mk[:, f] = k[:, m].max(1)
    order = np.argsort(-mk, axis=1)
    m1 = np.take_along_axis(mk, order[:, :1], 1)[:, 0]; m1f = order[:, 0]
    m2 = np.take_along_axis(mk, order[:, 1:2], 1)[:, 0] if nfac > 1 else np.zeros(M)
    fidx = np.arange(nfac)[None, :]
    rival = np.where(fidx == m1f[:, None], m2[:, None], m1[:, None])
    ratio = rival / np.maximum(own, 0.001)
    net = own * (1 - GAP * smoothstep(0.3, 1.0, ratio))
    net = np.where(own > 0, net, 0.0)
    best = net.argmax(1)
    return net[np.arange(M), best], rival[np.arange(M), best], best

def bake_grid(S, nfac, n, gmin, gsize):
    h = gsize / n
    c = gmin + (np.arange(n) + 0.5) * h
    out = np.zeros((n, n, n), np.float32)  # [z,y,x]
    zz, yy = np.meshgrid(c, c, indexing='ij')
    for z in range(n):
        P = np.stack([np.tile(c, n), np.repeat(c, n), np.full(n * n, c[z])], 1)  # x fastest, then y
        # restrict to systems that can matter
        near = np.linalg.norm(S[:, :3] - np.array([0, 0, c[z]]), axis=1)  # cheap prune by |z diff|
        sel = np.abs(S[:, 2] - c[z]) < R
        if not sel.any():
            continue
        net, _, _ = exact_net(P, S[sel], nfac)
        out[z] = net.reshape(n, n)
    return out

def trilinear(G, gmin, gsize, P):
    n = G.shape[0]
    u = (P - gmin) / gsize * n - 0.5
    i0 = np.floor(u).astype(int); f = u - i0
    res = np.zeros(P.shape[0])
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                ix = np.clip(i0[:, 0] + dx, 0, n - 1); iy = np.clip(i0[:, 1] + dy, 0, n - 1); iz = np.clip(i0[:, 2] + dz, 0, n - 1)
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                res += w * G[iz, iy, ix]
    return res

def make_rays(rng, m, rad_o=95.0, rad_t=45.0):
    o = rng.normal(size=(m, 3)); o = o / np.linalg.norm(o, axis=1)[:, None] * rad_o
    tg = rng.normal(size=(m, 3)); tg = tg / np.linalg.norm(tg, axis=1)[:, None] * rad_t * rng.random((m, 1)) ** (1 / 3)
    d = tg - o; d /= np.linalg.norm(d, axis=1)[:, None]
    return o, d

def first_cross(fn, o, d, t_lo, t_hi, dt, bis=22):
    """first t where fn goes below->above ISO along each ray; NaN if none. fn(P)->values"""
    m = o.shape[0]
    ts = np.arange(t_lo, t_hi, dt)
    found = np.full(m, np.nan)
    prev = np.zeros(m); alive = np.ones(m, bool)
    prev_t = np.full(m, t_lo)
    for t in ts:
        idx = np.nonzero(alive)[0]
        if idx.size == 0: break
        v = fn(o[idx] + d[idx] * t)
        hit = v >= ISO
        h_idx = idx[hit]
        if h_idx.size:
            lo = prev_t[h_idx].copy(); hi = np.full(h_idx.size, t)
            for _ in range(bis):
                mid = 0.5 * (lo + hi)
                vm = fn(o[h_idx] + d[h_idx] * mid[:, None])
                ins = vm >= ISO
                hi = np.where(ins, mid, hi); lo = np.where(ins, lo, mid)
            found[h_idx] = 0.5 * (lo + hi)
            alive[h_idx] = False
        prev_t[idx] = t
    return found

def report(err, miss, fp, total):
    e_all = err[~np.isnan(err)]
    e = e_all[e_all <= 1.0]          # same surface seen by both (within 1 world unit)
    return {"rays": total, "both_hit": int(e_all.size), "missed_by_grid": int(miss), "false_hit_by_grid": int(fp),
            "median_err": float(np.median(e)) if e.size else None, "p95_err": float(np.percentile(e, 95)) if e.size else None,
            "worst_err_same_surface": float(e.max()) if e.size else None,
            "worst_err_any": float(e_all.max()) if e_all.size else None}

def eval_grid_vs_exact(G, gmin, gsize, S, nfac, o, d, t_lo, t_hi, dt=0.25):
    exact_fn = lambda P: exact_net(P, S, nfac)[0]
    grid_fn = lambda P: trilinear(G, gmin, gsize, P)
    te = first_cross(exact_fn, o, d, t_lo, t_hi, dt)
    tg = first_cross(grid_fn, o, d, t_lo, t_hi, dt)
    both = ~np.isnan(te) & ~np.isnan(tg)
    err = np.where(both, np.abs(te - tg), np.nan)
    miss = int((~np.isnan(te) & np.isnan(tg)).sum()); fp = int((np.isnan(te) & ~np.isnan(tg)).sum())
    # "wrong first surface": both hit but > 1 unit apart (grid saw a different surface)
    wrong = int((err > 1.0).sum())
    r = report(err, miss, fp, o.shape[0]); r["first_surface_differs_gt_1u"] = wrong
    return r, te

def isolated(rng):
    """Smallest isolated bubbles: one owned system alone, sn = 0.35 (smallest real: sig 0.3 / capital 0.85)
    and sn = 0 (extreme), random sub-cell positions; rays through the centre."""
    res = {}
    half = 64.0; gmin = -half; gsize = 2 * half
    for n in (64, 96, 128):
        for sn in (0.35, 0.0):
            errs = []; miss = 0; total = 0; r_iso_true = None
            for trial in range(24):
                c = rng.uniform(-10, 10, 3)
                S = np.array([[c[0], c[1], c[2], sn, 0]])
                G = bake_grid(S, 1, n, gmin, gsize).astype(np.float16).astype(np.float32)
                o, d = make_rays(rng, 40, rad_o=30.0, rad_t=0.3)
                o = o + c; 
                dirs = (c + rng.normal(size=(40, 3)) * 0.3) - o; d = dirs / np.linalg.norm(dirs, axis=1)[:, None]
                exact_fn = lambda P: exact_net(P, S, 1)[0]
                grid_fn = lambda P: trilinear(G, gmin, gsize, P)
                te = first_cross(exact_fn, o, d, 5.0, 60.0, 0.1)
                tg = first_cross(grid_fn, o, d, 5.0, 60.0, 0.1)
                both = ~np.isnan(te) & ~np.isnan(tg)
                errs.extend(np.abs(te - tg)[both].tolist()); miss += int((~np.isnan(te) & np.isnan(tg)).sum()); total += 40
            r = R * (0.6 + 0.4 * sn)
            e = np.array(errs)
            res[f"{n}_sn{sn}"] = {"iso_radius": float(r * np.sqrt(1 - 0.6 ** (1 / 3))), "rays": total, "missed_by_grid": miss,
                                  "median_err": float(np.median(e)), "p95_err": float(np.percentile(e, 95)), "worst_err": float(e.max())}
            print("isolated", n, sn, json.dumps(res[f"{n}_sn{sn}"]), flush=True)
    return res

def main():
    dump, key = sys.argv[1], sys.argv[2]
    out = {}
    rng = np.random.default_rng(1234)
    for grid in (64, 96, 128):
        meta = json.load(open(f"{dump}/{key}_g{grid}.json"))
        n = meta["n"]; gmin = np.array(meta["gmin"]); gsize = meta["gsize"]; nfac = meta["nfac"]
        S = np.array(meta["systems"], float)
        raw = np.fromfile(f"{dump}/{key}_g{grid}.bin", dtype=np.float16).reshape(n, n, n, 4).astype(np.float32)
        Ggpu = raw[..., 0]
        entry = {}
        # 1. GPU fill vs numpy re-bake of the same formulas
        Gref = bake_grid(S, nfac, n, gmin[0], gsize)
        diff = np.abs(Ggpu - Gref)
        entry["gpu_fill_vs_numpy_max_abs_diff"] = float(diff.max())
        entry["gpu_fill_vs_numpy_mean_abs_diff"] = float(diff.mean())
        # id agreement where net > ISO
        ids_ref = np.zeros((n, n, n), int)
        # (id check on a sample of inside cells)
        zs, ys, xs = np.nonzero(Gref > ISO)
        sel = rng.choice(zs.size, size=min(3000, zs.size), replace=False)
        c = lambda i: gmin[0] + (i + 0.5) * gsize / n
        P = np.stack([c(xs[sel]), c(ys[sel]), c(zs[sel])], 1)
        _, _, fid = exact_net(P, S, nfac)
        entry["id_agreement_inside_cells"] = float((raw[zs[sel], ys[sel], xs[sel], 2].round().astype(int) == fid).mean())
        # 2. random rays through the real galaxy
        o, d = make_rays(rng, 2000)
        t_hi = 190.0
        r, te = eval_grid_vs_exact(Ggpu, gmin[0], gsize, S, nfac, o, d, 40.0, t_hi)
        entry["random_rays"] = r
        out[str(grid)] = entry
        print(grid, json.dumps(entry), flush=True)
    if key == "default":
        out["isolated_smallest_bubbles"] = isolated(rng)
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"results/accuracy_{key}.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
