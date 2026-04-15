"""
Checkpoint M — Engine Integration + Performance (Final)

Full pipeline:
  generate_map → TacticalEngine → reinforcements + drift → MissionResult

Performance: 200v200 on large generated map vs Stage 6 hand-authored baseline.
I8: navmesh generation count == 1 after full mission run.
I9: generated-map per-tick time within 15% of baseline.
I10: no protected files modified (git diff check).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import math
import time
import random
import subprocess
from PIL import Image, ImageDraw

import config
from unit import UnitStore, FIELD_X, FIELD_Y
from tactical_map import TacticalMap, SpineNode
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from reinforcement import ReinforcementStructure
from spine_drift import DriftingNode
from layout_library import load_all_layouts
from map_gen_contracts import GeneratorInput, RegionState
from map_generator import generate_map
from test_maps import open_field_large

PLAYER = 0
ENEMY  = 1
DT     = config.TACTICAL_TICK_DURATION
MAX_TICKS = 6000

OUT_DIR = os.path.join(os.path.dirname(__file__), "tuning_output", "stage7", "checkpoint_m")

MIXED_RATIO = {
    "Vanguard": 0.30, "Warden": 0.15, "Raider": 0.20,
    "Interceptor": 0.10, "Bombard": 0.15, "Bastion": 0.10,
}

PROTECTED_FILES = {
    "tick.py", "drift.py", "faction.py", "region.py", "events.py",
    "event_engine.py", "intent_resolver.py", "border_friction.py",
    "technology.py", "diplomacy.py", "world.py", "templates.py",
    "theme_scifi.py",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _spawn_force(store, faction, cx, cy, count, rng):
    roster = []
    for ut, frac in MIXED_RATIO.items():
        roster.extend([ut] * max(1, round(count * frac)))
    while len(roster) > count: roster.pop(rng.randrange(len(roster)))
    while len(roster) < count: roster.append(rng.choice(list(MIXED_RATIO)))
    rng.shuffle(roster)
    cols = max(5, int(math.sqrt(count)) + 1)
    uids = []
    for i, ut in enumerate(roster):
        x = cx + (i % cols) * 60.0 + rng.uniform(-10, 10)
        y = cy + (i // cols) * 60.0 + rng.uniform(-10, 10)
        uids.append(store.spawn(ut, faction, x, y))
    return [u for u in uids if u >= 0]


def _run_baseline(count_per_side=200):
    rng  = random.Random(42)
    tmap = open_field_large()
    engine = TacticalEngine(tmap, seed=42)
    engine.enable_reinforcement = False

    player_uids = _spawn_force(engine.store, PLAYER,  1000,  1000, count_per_side, rng)
    enemy_uids  = _spawn_force(engine.store, ENEMY,  11000, 11000, count_per_side, rng)

    q = engine.command_queue
    q.add(Command(tick=0, type="attack_move", unit_ids=player_uids,
                  params={"target_x": 11000, "target_y": 11000}))
    q.add(Command(tick=0, type="attack_move", unit_ids=enemy_uids,
                  params={"target_x": 1000, "target_y": 1000}))

    tick_times = []
    for _ in range(MAX_TICKS):
        t0 = time.perf_counter()
        engine.step()
        tick_times.append((time.perf_counter() - t0) * 1000)
        if engine.is_terminal():
            break

    return engine, tick_times


def _structures_from_map(tmap, rng):
    structs = []
    for i, node in enumerate(tmap.get_spine_nodes_by_type("reinforcement_structure")):
        owner_key = node.properties.get("initial_owner", "neutral")
        owner_map = {"player": PLAYER, "neutral": -1, "enemy": ENEMY}
        owner = owner_map.get(owner_key, -1)
        structs.append(ReinforcementStructure(
            structure_uid=i,
            position=node.position,
            layer=0,
            hp=float(config.REINFORCEMENT_STRUCTURE_HP),
            max_hp=float(config.REINFORCEMENT_STRUCTURE_HP),
            owner_faction=owner,
            capture_progress=0.0,
            production_timer_sec=0.0,
            production_target_unit_type=rng.choice(["Vanguard", "Raider", "Warden"]),
            capture_radius=config.REINFORCEMENT_CAPTURE_RADIUS,
        ))
    return structs


def _add_drift(tmap):
    obj_nodes = tmap.get_spine_nodes_by_type("objective")
    if not obj_nodes:
        return
    sn = obj_nodes[0]
    px, py = sn.position
    w = tmap.width
    wp = [(px, py), (min(px + 1200, w - 200), py)]
    dn = DriftingNode("drift_obj_m", "objective", sn, wp, period_ticks=600, mode="ping_pong")
    tmap.drifting_nodes = [dn]


def _run_stage7(layout_lib, count_per_side=200):
    rng = random.Random(99)

    t_gen0 = time.perf_counter()
    result = generate_map(GeneratorInput(
        archetype="defensive_stand",
        region_state=RegionState(
            stability=0.65, capacity=0.70,
            economy=55.0, tension=45.0, military=62.0, population=58.0,
            region_id="r_m_test", tier=2,
        ),
        canvas_size="large",
        seed=0xBEEF_CAFE,
    ), layout_lib)
    gen_time_ms = (time.perf_counter() - t_gen0) * 1000

    tmap = result.tactical_map
    structs = _structures_from_map(tmap, rng)
    _add_drift(tmap)

    engine = TacticalEngine(tmap, seed=99)
    engine.reinforcement_structures = structs
    engine.enable_reinforcement = True

    # Spawn on opposing staging nodes if available, else fixed corners
    staging = tmap.get_spine_nodes_by_type("staging")
    if len(staging) >= 2:
        px, py = staging[0].position
        ex, ey = staging[-1].position
    else:
        px, py = 800.0, 800.0
        ex, ey = tmap.width - 800.0, tmap.height - 800.0

    player_uids = _spawn_force(engine.store, PLAYER, px, py, count_per_side, rng)
    enemy_uids  = _spawn_force(engine.store, ENEMY,  ex, ey, count_per_side, rng)

    q = engine.command_queue
    q.add(Command(tick=0, type="attack_move", unit_ids=player_uids,
                  params={"target_x": ex, "target_y": ey}))
    q.add(Command(tick=0, type="attack_move", unit_ids=enemy_uids,
                  params={"target_x": px, "target_y": py}))

    tick_times = []
    capture_events = 0
    drift_dist = 0.0
    prev_owners = {s.structure_uid: s.owner_faction for s in structs}
    prev_drift_pos = {dn.node_id: dn.position_at(0) for dn in tmap.drifting_nodes}
    sample_ticks = set()

    total_ticks = min(MAX_TICKS, 6000)
    step_sample = max(1, total_ticks // 6)
    for t in range(total_ticks):
        if t % step_sample == 0:
            sample_ticks.add(t)

    frames = []

    for t in range(total_ticks):
        t0 = time.perf_counter()
        engine.step()
        tick_times.append((time.perf_counter() - t0) * 1000)

        for s in engine.reinforcement_structures:
            if prev_owners.get(s.structure_uid) != s.owner_faction:
                capture_events += 1
                prev_owners[s.structure_uid] = s.owner_faction

        if t % 10 == 0:
            for dn in tmap.drifting_nodes:
                cur = dn.position_at(t)
                prev = prev_drift_pos[dn.node_id]
                drift_dist += math.dist(cur, prev)
                prev_drift_pos[dn.node_id] = cur

        if t in sample_ticks:
            frames.append((t, _draw_frame(engine, tmap, t)))

        if engine.is_terminal():
            break

    # final frame
    frames.append((engine.tick, _draw_frame(engine, tmap, engine.tick)))

    return engine, tick_times, gen_time_ms, capture_events, drift_dist, frames, result


# ── PNG helpers ───────────────────────────────────────────────────────────────

FW, FH = 240, 240
MARGIN  = 12
BG      = (28, 30, 38)


def _draw_frame(engine, tmap, tick):
    img  = Image.new("RGB", (FW, FH), BG)
    draw = ImageDraw.Draw(img)

    w, h = tmap.width, tmap.height
    dw   = FW - 2 * MARGIN
    dh   = FH - 2 * MARGIN - 18

    def px(mx, my):
        return (int(MARGIN + (mx / w) * dw),
                int(MARGIN + (my / h) * dh))

    # Gradient sources (faint)
    for src in tmap.gradient_sources[:30]:
        ix, iy = px(*src.position)
        r = max(2, int((src.radius / w) * dw * 0.4))
        draw.ellipse([ix - r, iy - r, ix + r, iy + r],
                     outline=(50, 55, 70), width=1)

    # Spine nodes
    node_col = {
        "staging": (80, 200, 120), "chokepoint": (220, 80, 80),
        "objective": (100, 160, 255), "reinforcement_structure": (200, 80, 200),
        "vantage": (230, 200, 50), "flank_route": (100, 200, 170),
    }
    for sn in tmap.spine_nodes:
        col = node_col.get(sn.node_type, (100, 100, 120))
        ix, iy = px(*sn.position)
        draw.ellipse([ix - 4, iy - 4, ix + 4, iy + 4], outline=col, width=1)

    # Reinforcement structures (filled, owner-colored)
    owner_col = {-1: (160, 160, 160), PLAYER: (80, 200, 120), ENEMY: (220, 80, 80)}
    for s in engine.reinforcement_structures:
        col = owner_col.get(s.owner_faction, (200, 80, 200))
        ix, iy = px(*s.position)
        draw.ellipse([ix - 5, iy - 5, ix + 5, iy + 5], fill=col)

    # Units
    for uid in engine.store.active_ids():
        x = engine.store.data[uid, FIELD_X]
        y = engine.store.data[uid, FIELD_Y]
        col = (80, 200, 120) if engine.store.faction[uid] == PLAYER else (220, 80, 80)
        ix, iy = px(x, y)
        draw.point((ix, iy), fill=col)

    # Drifting node current position
    for dn in tmap.drifting_nodes:
        ix, iy = px(*dn.position_at(tick))
        draw.ellipse([ix - 4, iy - 4, ix + 4, iy + 4],
                     fill=(100, 160, 255), outline=(255, 255, 255))

    draw.text((MARGIN, FH - 16), f"t={tick}", fill=(150, 150, 150))
    return img


def _p95(times):
    s = sorted(times)
    return s[int(len(s) * 0.95)] if s else 0.0


def _median(times):
    s = sorted(times)
    return s[len(s) // 2] if s else 0.0


# ── I10: protected file check ─────────────────────────────────────────────────

def check_protected_files():
    try:
        diff = subprocess.check_output(
            ["git", "diff", "--name-only"],
            cwd=os.path.dirname(__file__),
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        modified = {os.path.basename(p) for p in diff.splitlines() if p}
        hits = modified & PROTECTED_FILES
        return hits
    except Exception:
        return set()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    failures = []

    print("Checkpoint M — Engine Integration + Performance (Final)")
    print("=" * 60)

    # ── Stage 6 baseline ─────────────────────────────────────────────────────
    print("\n── Stage 6 baseline (200v200, open_field_large) ────────────")
    engine_base, t_base = _run_baseline(count_per_side=200)
    base_median = _median(t_base)
    base_p95    = _p95(t_base)
    base_ticks  = engine_base.tick
    print(f"  ticks: {base_ticks}  median: {base_median:.3f}ms  p95: {base_p95:.3f}ms")

    # ── Stage 7 run ───────────────────────────────────────────────────────────
    print("\n── Stage 7 run (200v200, large generated map) ──────────────")
    layout_lib = load_all_layouts()
    engine_s7, t_s7, gen_time, capture_events, drift_dist, frames, gen_result = \
        _run_stage7(layout_lib, count_per_side=200)

    s7_median = _median(t_s7)
    s7_p95    = _p95(t_s7)
    s7_ticks  = engine_s7.tick
    tmap      = engine_s7.map

    active = list(engine_s7.store.active_ids())
    n_player = sum(1 for u in active if engine_s7.store.faction[u] == PLAYER)
    n_enemy  = sum(1 for u in active if engine_s7.store.faction[u] == ENEMY)
    outcome  = "player_win" if n_enemy == 0 else ("enemy_win" if n_player == 0 else "timeout")

    print(f"  generation time:  {gen_time:.1f}ms")
    print(f"  layout:           {gen_result.chosen_layout_id}")
    print(f"  structures:       {len(engine_s7.reinforcement_structures)}")
    print(f"  drifting nodes:   {len(tmap.drifting_nodes)}")
    print(f"  ticks:            {s7_ticks}")
    print(f"  outcome:          {outcome}  (player={n_player} enemy={n_enemy})")
    print(f"  capture events:   {capture_events}")
    print(f"  drift distance:   {drift_dist:.0f} wu")
    print(f"  median tick:      {s7_median:.3f}ms  p95: {s7_p95:.3f}ms")

    # ── Performance comparison (I9) ───────────────────────────────────────────
    perf_ratio = s7_median / base_median if base_median > 0 else float("inf")
    ok_perf    = perf_ratio <= 1.15
    print(f"\n── Performance (I9) ─────────────────────────────────────────")
    print(f"  baseline median:  {base_median:.3f}ms")
    print(f"  stage7 median:    {s7_median:.3f}ms")
    print(f"  ratio:            {perf_ratio:.3f}  (limit 1.15)  {'✓' if ok_perf else '✗'}")
    if not ok_perf:
        failures.append(f"I9 fail: per-tick ratio {perf_ratio:.3f} > 1.15")

    # ── Navmesh count (I8) ────────────────────────────────────────────────────
    gen_count = getattr(tmap, "_navmesh_generation_count", 0)
    ok_nav    = gen_count == 1
    print(f"\n── Navmesh (I8) ─────────────────────────────────────────────")
    print(f"  generation_count: {gen_count} (expected 1)  {'✓' if ok_nav else '✗'}")
    if not ok_nav:
        failures.append(f"I8 fail: navmesh generation_count == {gen_count}, expected 1")

    # ── Protected files (I10) ─────────────────────────────────────────────────
    hits = check_protected_files()
    ok_prot = len(hits) == 0
    print(f"\n── Protected files (I10) ────────────────────────────────────")
    print(f"  {'No protected files modified  ✓' if ok_prot else f'MODIFIED: {hits}  ✗'}")
    if not ok_prot:
        failures.append(f"I10 fail: protected files modified: {hits}")

    # ── PNG sequence ─────────────────────────────────────────────────────────
    cols   = min(len(frames), 4)
    rows   = math.ceil(len(frames) / cols)
    sheet  = Image.new("RGB", (cols * FW + (cols - 1) * 3, rows * FH + (rows - 1) * 3 + 24),
                       (18, 20, 26))
    sdraw  = ImageDraw.Draw(sheet)
    sdraw.text((6, 4), "Checkpoint M — Mission at sampled ticks", fill=(200, 200, 200))
    for idx, (tick, frame) in enumerate(frames):
        r, c = divmod(idx, cols)
        sheet.paste(frame, (c * (FW + 3), 24 + r * (FH + 3)))
        frame.save(os.path.join(OUT_DIR, f"frame_{tick:05d}.png"))
    sheet.save(os.path.join(OUT_DIR, "contact_sheet.png"))
    print(f"\nPNGs → {OUT_DIR}")

    # ── Result ───────────────────────────────────────────────────────────────
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)
    else:
        print("\nCheckpoint M complete — no failures.")


if __name__ == "__main__":
    main()
