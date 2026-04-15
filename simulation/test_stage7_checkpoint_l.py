"""
Checkpoint L — Drifting Spine Nodes

Layout:
  obj_alpha     — objective, ping_pong, period=400, 3 waypoints
  obj_beta      — objective, ping_pong, period=200, 2 waypoints
  capture_gamma — reinforcement_structure, loop, period=300, 4 waypoints

1000 ticks, sampled every 10.
Waypoint-boundary checks verify ping_pong reversal and loop cycling.
Navmesh generation count asserted == 1 (I8).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import math
import types
from PIL import Image, ImageDraw

from tactical_map import TacticalMap, SpineNode
from spine_drift import DriftingNode, update_drifting_nodes

OUT_DIR = os.path.join(os.path.dirname(__file__), "tuning_output", "stage7", "checkpoint_l")
MAP_W, MAP_H = 4000, 4000
TICKS = 1000


# ── Node definitions ─────────────────────────────────────────────────────────

WP_ALPHA  = [(1000.0, 2000.0), (3000.0, 2000.0), (2000.0, 3500.0)]
WP_BETA   = [(500.0,  500.0),  (3500.0, 3500.0)]
WP_GAMMA  = [(2000.0, 1000.0), (3000.0, 2000.0), (2000.0, 3000.0), (1000.0, 2000.0)]

PERIOD_ALPHA = 400
PERIOD_BETA  = 200
PERIOD_GAMMA = 300

# Expected positions at waypoint-transition ticks (exact multiples of seg_len)
# obj_alpha: 4 segments of 100 ticks each
ALPHA_EXACT = {
    0:   WP_ALPHA[0],
    100: WP_ALPHA[1],
    200: WP_ALPHA[2],
    300: WP_ALPHA[1],  # reversal midpoint
    400: WP_ALPHA[0],  # full period
}
# obj_beta: 2 segments of 100 ticks each
BETA_EXACT = {
    0:   WP_BETA[0],
    100: WP_BETA[1],
    200: WP_BETA[0],   # full period
}
# capture_gamma: 4 segments of 75 ticks each
GAMMA_EXACT = {
    0:   WP_GAMMA[0],
    75:  WP_GAMMA[1],
    150: WP_GAMMA[2],
    225: WP_GAMMA[3],
    300: WP_GAMMA[0],  # full period
}


def _close(a, b, tol=0.5):
    return math.dist(a, b) < tol


def build_map():
    sn_alpha = SpineNode(position=WP_ALPHA[0], node_type="objective")
    sn_beta  = SpineNode(position=WP_BETA[0],  node_type="objective")
    sn_gamma = SpineNode(position=WP_GAMMA[0], node_type="reinforcement_structure")

    dn_alpha = DriftingNode("obj_alpha",     "objective",              sn_alpha, WP_ALPHA, PERIOD_ALPHA, "ping_pong")
    dn_beta  = DriftingNode("obj_beta",      "objective",              sn_beta,  WP_BETA,  PERIOD_BETA,  "ping_pong")
    dn_gamma = DriftingNode("capture_gamma", "reinforcement_structure", sn_gamma, WP_GAMMA, PERIOD_GAMMA, "loop")

    tmap = TacticalMap(
        width=MAP_W, height=MAP_H, layers=5,
        spine_nodes=[sn_alpha, sn_beta, sn_gamma],
        drifting_nodes=[dn_alpha, dn_beta, dn_gamma],
    )
    return tmap, dn_alpha, dn_beta, dn_gamma


# ── PNG helpers ───────────────────────────────────────────────────────────────

FW, FH   = 220, 220
MARGIN   = 14
BG       = (28, 30, 38)
PATH_COL = {
    "obj_alpha":     (100, 160, 255),
    "obj_beta":      (80,  220, 120),
    "capture_gamma": (200, 80,  200),
}
DOT_R = 5


def _to_px(x, y):
    dw = FW - 2 * MARGIN
    dh = FH - 2 * MARGIN
    return (int(MARGIN + (x / MAP_W) * dw),
            int(MARGIN + (y / MAP_H) * dh))


def _draw_frame(dnodes, tick):
    img  = Image.new("RGB", (FW, FH), BG)
    draw = ImageDraw.Draw(img)

    # Draw path outlines
    for dn in dnodes:
        col = PATH_COL[dn.node_id]
        pts = [_to_px(*wp) for wp in dn.waypoints]
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=(col[0]//3, col[1]//3, col[2]//3), width=1)
        if dn.mode == "loop":
            draw.line([pts[-1], pts[0]], fill=(col[0]//3, col[1]//3, col[2]//3), width=1)

    # Draw waypoints as small squares
    for dn in dnodes:
        col = PATH_COL[dn.node_id]
        for wp in dn.waypoints:
            px, py = _to_px(*wp)
            draw.rectangle([px - 2, py - 2, px + 2, py + 2], outline=col)

    # Draw current positions
    for dn in dnodes:
        col = PATH_COL[dn.node_id]
        px, py = _to_px(*dn.position_at(tick))
        draw.ellipse([px - DOT_R, py - DOT_R, px + DOT_R, py + DOT_R], fill=col)

    # Tick label (dots along bottom)
    draw.text((MARGIN, FH - 10), f"t={tick}", fill=(160, 160, 160))

    return img


def build_contact_sheet(frames_with_ticks, dnodes):
    cols = 10
    rows = math.ceil(len(frames_with_ticks) / cols)
    sheet_w = cols * FW + (cols - 1) * 3
    sheet_h = rows * FH + (rows - 1) * 3 + 24

    sheet = Image.new("RGB", (sheet_w, sheet_h), (18, 20, 26))
    draw  = ImageDraw.Draw(sheet)
    draw.text((6, 4), "Checkpoint L — Drifting Spine Nodes", fill=(200, 200, 200))

    for idx, (tick, frame) in enumerate(frames_with_ticks):
        row, col = divmod(idx, cols)
        x = col * (FW + 3)
        y = 24 + row * (FH + 3)
        sheet.paste(frame, (x, y))

    return sheet


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    failures = []

    print("Checkpoint L — Drifting Spine Nodes")
    print("=" * 60)

    tmap, dn_alpha, dn_beta, dn_gamma = build_map()
    engine = types.SimpleNamespace(map=tmap)
    dnodes = [dn_alpha, dn_beta, dn_gamma]

    # ── Node summary ──────────────────────────────────────────────────────────
    for dn in dnodes:
        wps = "  ".join(f"({wx:.0f},{wy:.0f})" for wx, wy in dn.waypoints)
        print(f"\n  {dn.node_id}  [{dn.mode}  period={dn.period_ticks}]")
        print(f"    waypoints: {wps}")

    # ── Sampled positions (first 200 ticks, every 10) ─────────────────────────
    print("\n  Sampled positions (first 200 ticks, every 10):")
    print(f"  {'tick':>5}  {'obj_alpha':>20}  {'obj_beta':>20}  {'capture_gamma':>22}")
    for t in range(0, 200, 10):
        pa = dn_alpha.position_at(t)
        pb = dn_beta.position_at(t)
        pg = dn_gamma.position_at(t)
        print(f"  {t:>5}  ({pa[0]:>7.1f},{pa[1]:>7.1f})  "
              f"({pb[0]:>7.1f},{pb[1]:>7.1f})  "
              f"({pg[0]:>7.1f},{pg[1]:>7.1f})")

    # ── Waypoint-boundary checks ──────────────────────────────────────────────
    print("\n  Waypoint-boundary checks:")

    def check(node_id, dn, exact_table):
        for tick, expected in exact_table.items():
            got = dn.position_at(tick)
            ok = _close(got, expected)
            status = "✓" if ok else f"✗  got ({got[0]:.2f},{got[1]:.2f}) expected ({expected[0]:.2f},{expected[1]:.2f})"
            print(f"    {node_id}  t={tick:>4}: {status}")
            if not ok:
                failures.append(f"{node_id} t={tick}: got ({got[0]:.2f},{got[1]:.2f}), "
                                 f"expected ({expected[0]:.2f},{expected[1]:.2f})")

    check("obj_alpha",     dn_alpha, ALPHA_EXACT)
    check("obj_beta",      dn_beta,  BETA_EXACT)
    check("capture_gamma", dn_gamma, GAMMA_EXACT)

    # ── Ping_pong reversal: midpoint of return trip ───────────────────────────
    # obj_beta: at tick 150 (halfway through return), should be midpoint of B→A
    mid = ((WP_BETA[1][0] + WP_BETA[0][0]) / 2,
           (WP_BETA[1][1] + WP_BETA[0][1]) / 2)
    got = dn_beta.position_at(150)
    ok = _close(got, mid)
    print(f"\n  ping_pong midpoint reversal (obj_beta t=150): "
          f"{'✓' if ok else f'✗ got ({got[0]:.1f},{got[1]:.1f}) expected ({mid[0]:.1f},{mid[1]:.1f})'}")
    if not ok:
        failures.append(f"obj_beta ping_pong midpoint at t=150: ({got[0]:.2f},{got[1]:.2f}) != ({mid[0]:.2f},{mid[1]:.2f})")

    # ── Loop cycling: tick 600 = 2 full periods of gamma, same as tick 0 ─────
    got600 = dn_gamma.position_at(600)
    ok = _close(got600, WP_GAMMA[0])
    print(f"  loop cycle (capture_gamma t=600 == t=0): "
          f"{'✓' if ok else f'✗ got ({got600[0]:.1f},{got600[1]:.1f})'}")
    if not ok:
        failures.append(f"capture_gamma loop: t=600 ({got600[0]:.2f},{got600[1]:.2f}) != waypoints[0]")

    # ── update_drifting_nodes mutates SpineNode.position ─────────────────────
    update_drifting_nodes(engine, 100)
    for dn in dnodes:
        expected = dn.position_at(100)
        got = dn.spine_node.position
        ok = _close(got, expected)
        print(f"  SpineNode mutated at t=100 ({dn.node_id}): {'✓' if ok else f'✗ {got} != {expected}'}")
        if not ok:
            failures.append(f"SpineNode not mutated for {dn.node_id} at t=100")

    # ── current_spine_node_positions ─────────────────────────────────────────
    pos_dict = tmap.current_spine_node_positions(200)
    assert set(pos_dict.keys()) == {"obj_alpha", "obj_beta", "capture_gamma"}, \
        f"FAIL: unexpected keys in current_spine_node_positions: {pos_dict.keys()}"
    for node_id, pos in pos_dict.items():
        dn = next(d for d in dnodes if d.node_id == node_id)
        expected = dn.position_at(200)
        ok = _close(pos, expected)
        print(f"  current_spine_node_positions t=200 ({node_id}): {'✓' if ok else f'✗ {pos} != {expected}'}")
        if not ok:
            failures.append(f"current_spine_node_positions mismatch for {node_id} at t=200")

    # ── Navmesh generation count ──────────────────────────────────────────────
    from movement import _ensure_navmesh
    _ensure_navmesh(tmap)  # first build
    _ensure_navmesh(tmap)  # should not rebuild
    gen_count = getattr(tmap, "_navmesh_generation_count", 0)
    ok = gen_count == 1
    print(f"\n  Navmesh generation count: {gen_count} (expected 1)  {'✓' if ok else '✗'}")
    if not ok:
        failures.append(f"Navmesh generation_count == {gen_count}, expected 1")

    # ── PNG sequence ─────────────────────────────────────────────────────────
    sample_ticks = list(range(0, 401, 20))  # 21 frames covering the longest period
    frames_with_ticks = [(t, _draw_frame(dnodes, t)) for t in sample_ticks]
    sheet = build_contact_sheet(frames_with_ticks, dnodes)
    sheet_path = os.path.join(OUT_DIR, "contact_sheet.png")
    sheet.save(sheet_path)

    for t, frame in frames_with_ticks:
        frame.save(os.path.join(OUT_DIR, f"frame_{t:04d}.png"))

    print(f"\nPNGs → {OUT_DIR}")

    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)
    else:
        print("\nCheckpoint L complete — no failures.")


if __name__ == "__main__":
    main()
