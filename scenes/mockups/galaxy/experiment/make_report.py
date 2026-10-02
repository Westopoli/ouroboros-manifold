#!/usr/bin/env python3
"""Builds the numeric tables for REPORT.md from results/*.json (prints Markdown)."""
import json, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
P = ["d120", "d25", "d7.5_f0", "inside"]
PN = {"d120": "dist 120", "d25": "dist 25", "d7.5_f0": "dist 7.5 on f0", "inside": "inside bubble"}
L = lambda n: json.load(open(f"{D}/{n}.json"))
f2 = lambda x: f"{x:.2f}"

def baseline():
    b = L("baseline"); R = {r["name"]: r for r in b["runs"]}
    out = ["| galaxy | position | old shell viewport GPU ms (median / p95) | main viewport ms, shell on | main viewport ms, shell off | shell cost = vp + (on-off) |", "|---|---|---|---|---|---|"]
    for g, label in (("default", "default (219 sys / 4 fac)"), ("big", "400 sys / 15 fac")):
        on, off = R[f"base_{g}_on"], R[f"base_{g}_off"]
        # shell-off main time is only trustworthy when the GPU clock was high (>=1850 MHz)
        hot = [off["positions"][p]["gpu_main_ms"]["median"] for p in P if off["positions"][p]["gpu_sm_clock_mhz"] >= 1850]
        ref = min(hot)
        for p in P:
            a, o = on["positions"][p], off["positions"][p]
            vp = a["gpu_old_shell_vp_ms"]
            clk = o["gpu_sm_clock_mhz"]
            offs = f2(o["gpu_main_ms"]["median"]) + ("" if clk >= 1850 else f" (clock {clk} MHz, unreliable)")
            cost = vp["median"] + (a["gpu_main_ms"]["median"] - ref)
            out.append(f"| {label} | {PN[p]} | {vp['median']:.1f} / {vp['p95']:.1f} | {f2(a['gpu_main_ms']['median'])} | {offs} | **{cost:.1f}** |")
    return "\n".join(out)

def variant_row(r, bold=False):
    v = {k: (int(x) if isinstance(x, float) and k != "skip" else x) for k, x in r["variant"].items()}
    r = dict(r, grid=int(r["grid"]))
    vals = [r["positions"][p]["gpu_field_vp_ms"]["median"] for p in P]
    p95 = [r["positions"][p]["gpu_field_vp_ms"]["p95"] for p in P]
    mx = max(vals)
    name = f"grid {r['grid']}, {v['steps']} steps, div {v['divisor']}, skip {'on' if v['skip'] else 'off'}, {v['cross']} crossings" + (f", refine {v['refine']}" if v['refine'] != 2 else "")
    cells = " | ".join(f2(x) for x in vals)
    row = f"| {r['name']} | {r['galaxy']} | {name} | {cells} | {f2(max(p95))} | {f2(mx)} | {'yes' if mx <= 2.0 else '**NO**'} |"
    return ("| **" + row[2:].replace(" | ", "** | **", 0) + "") if False else row

def table(runs):
    h = ["| run | galaxy | variant | " + " | ".join(PN[p] for p in P) + " | worst p95 | max median | <= 2.0 ms at all 4? |", "|---|---|---|---|---|---|---|---|---|---|"]
    return "\n".join(h + [variant_row(r) for r in runs])

def bake():
    b = L("bake"); out = ["| galaxy | grid | GPU bake pass (derived) ms | full fill wall ms (draw + readback + 3D texture) | refill after 1 owner change wall ms | of which readback / slice+upload ms | skip-grid build ms (CPU) | texture memory as built (RGBAH) | packed alternative (RG16F + R8) |", "|---|---|---|---|---|---|---|---|---|"]
    for r in b["runs"]:
        if r["mode"] != "bake": continue
        for g, v in r["grids"].items():
            pt = v["parts_last"]
            out.append(f"| {r['galaxy']} | {g}^3 | {v['bake_pass_gpu_ms_derived']:.2f} | {v['full_wall_ms']['median']:.1f} | {v['refill_wall_ms']['median']:.1f} | {pt['readback_ms']:.1f} / {pt['slice_upload_ms']:.1f} | {v['skip_build_ms']:.0f} | {v['mem_bytes_rgbah']/1048576:.2f} MiB | {v['mem_bytes_packed_rgh_r8']/1048576:.2f} MiB |")
    return "\n".join(out)

def accuracy():
    out = ["| galaxy | grid | rays | median err | p95 err | worst err (same surface, <=1 u) | rays where grid and exact disagree on first surface by >1 u (worst such gap) | grid missed a surface the exact field has | GPU fill vs numpy max abs diff |", "|---|---|---|---|---|---|---|---|---|"]
    for k in ("default", "big"):
        d = L(f"accuracy_{k}")
        for g in ("64", "96", "128"):
            v = d[g]; r = v["random_rays"]
            out.append(f"| {k} | {g}^3 | {r['rays']} | {r['median_err']:.3f} | {r['p95_err']:.3f} | {r['worst_err_same_surface']:.2f} | {r['first_surface_differs_gt_1u']} ({r['worst_err_any']:.0f} u) | {r['missed_by_grid']} | {v['gpu_fill_vs_numpy_max_abs_diff']:.4f} |")
    out2 = ["", "Smallest isolated bubbles (one owned system alone in the grid, 24 random sub-cell positions, 40 rays through the centre each; error = distance along the ray between exact and grid surface):", "", "| grid | system significance (normalised) | exact iso radius | rays | grid missed | median err | p95 err | worst err |", "|---|---|---|---|---|---|---|---|"]
    iso = L("accuracy_default")["isolated_smallest_bubbles"]
    for k, v in iso.items():
        g, sn = k.split("_sn")
        out2.append(f"| {g}^3 | {sn} | {v['iso_radius']:.2f} | {v['rays']} | {v['missed_by_grid']} | {v['median_err']:.3f} | {v['p95_err']:.3f} | {v['worst_err']:.3f} |")
    return "\n".join(out + out2)

if __name__ == "__main__":
    m = L("matrix")["runs"]; best = L("best")["runs"]
    print("## BASELINE\n" + baseline() + "\n\n## MATRIX\n" + table(m) + "\n\n## BEST\n" + table(best) + "\n\n## BAKE\n" + bake() + "\n\n## ACCURACY\n" + accuracy())
