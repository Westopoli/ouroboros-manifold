"""
Checkpoint J — Reinforcement Structure Mechanics (capture + HP)

Scenarios:
  1. Uncontested capture (neutral → player)
  2. Contested (player + enemy both in radius → stall)
  3. Abandoned (units removed mid-capture → reset)
  4. Flip (enemy-owned → player)
  5. HP destruction (hp → 0 → removal)

Production timer is not tested here — see Checkpoint K.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import types
import config
from unit import UnitStore, FIELD_X, FIELD_Y
from tactical_map import TacticalMap
from reinforcement import ReinforcementStructure, step_reinforcement
from PIL import Image, ImageDraw

PLAYER  = 0
ENEMY   = 1
NEUTRAL = -1

DT             = config.TACTICAL_TICK_DURATION           # 0.05 s
CAPTURE_DUR    = config.REINFORCEMENT_CAPTURE_DURATION_SEC  # 10.0 s
CAPTURE_TICKS  = int(CAPTURE_DUR / DT)                  # 200 ticks
CAPTURE_R      = config.REINFORCEMENT_CAPTURE_RADIUS     # 300.0
STRUCT_POS     = (2000.0, 2000.0)
STRUCT_HP      = float(config.REINFORCEMENT_STRUCTURE_HP)

OUT_DIR = os.path.join(os.path.dirname(__file__), "tuning_output", "stage7", "checkpoint_j")


def _make_engine(tmap, store):
    e = types.SimpleNamespace(map=tmap, store=store, reinforcement_structures=[])
    return e


def _rebuild_hash(engine):
    engine.map.spatial_hash.clear()
    for uid in range(engine.store.count):
        if engine.store.alive[uid]:
            x = engine.store.data[uid, FIELD_X]
            y = engine.store.data[uid, FIELD_Y]
            engine.map.spatial_hash.insert(uid, x, y)


def _make_structure(owner=NEUTRAL, progress=0.0, hp=None):
    return ReinforcementStructure(
        structure_uid=1,
        position=STRUCT_POS,
        layer=0,
        hp=STRUCT_HP if hp is None else hp,
        max_hp=STRUCT_HP,
        owner_faction=owner,
        capture_progress=progress,
        production_timer_sec=0.0,
        production_target_unit_type="Vanguard",
        capture_radius=CAPTURE_R,
    )


# ── PNG helpers ──────────────────────────────────────────────────────────────

FRAME_W, FRAME_H = 200, 160
MAP_SIZE = 4000.0
MARGIN   = 12

OWNER_COLOR  = {NEUTRAL: (160, 160, 160), PLAYER: (80, 200, 120), ENEMY: (220, 80, 80)}
FACTION_DOT  = {PLAYER: (80, 200, 120), ENEMY: (220, 80, 80)}
BG           = (28, 30, 38)
GRID_COLOR   = (45, 48, 58)
TEXT_COLOR   = (210, 210, 210)
BAR_BG       = (55, 58, 70)
CAPTURE_BAR  = (100, 180, 255)
HP_BAR       = (220, 80, 80)


def _to_img(mx, my, frame_w=FRAME_W, frame_h=FRAME_H):
    draw_w = frame_w - 2 * MARGIN
    draw_h = int((frame_h - 2 * MARGIN) * 0.70)
    ix = int(MARGIN + (mx / MAP_SIZE) * draw_w)
    iy = int(MARGIN + (my / MAP_SIZE) * draw_h)
    return ix, iy


def _draw_frame(structure, units_by_faction, tick, label):
    """units_by_faction: dict of faction → list of (x, y)"""
    img = Image.new("RGB", (FRAME_W, FRAME_H), BG)
    draw = ImageDraw.Draw(img)

    draw_h_top = int((FRAME_H - 2 * MARGIN) * 0.70)

    # Capture radius
    sx, sy = STRUCT_POS
    ix, iy = _to_img(sx, sy)
    r_px = int((CAPTURE_R / MAP_SIZE) * (FRAME_W - 2 * MARGIN))
    draw.ellipse([ix - r_px, iy - r_px, ix + r_px, iy + r_px],
                 outline=(70, 80, 110), width=1)

    # Units
    for faction, pts in units_by_faction.items():
        col = FACTION_DOT.get(faction, (200, 200, 200))
        for (ux, uy) in pts:
            uix, uiy = _to_img(ux, uy)
            draw.ellipse([uix - 3, uiy - 3, uix + 3, uiy + 3], fill=col)

    # Structure
    col = OWNER_COLOR.get(structure.owner_faction, (200, 80, 200))
    draw.ellipse([ix - 5, iy - 5, ix + 5, iy + 5], fill=col, outline=(255, 255, 255))

    # Bars
    bar_y0 = MARGIN + draw_h_top + 6
    bar_w  = FRAME_W - 2 * MARGIN

    # Capture progress bar
    draw.rectangle([MARGIN, bar_y0, MARGIN + bar_w, bar_y0 + 8], fill=BAR_BG)
    plen = int(bar_w * min(1.0, max(0.0, structure.capture_progress)))
    if plen > 0:
        draw.rectangle([MARGIN, bar_y0, MARGIN + plen, bar_y0 + 8], fill=CAPTURE_BAR)

    # HP bar
    hp_y0 = bar_y0 + 12
    draw.rectangle([MARGIN, hp_y0, MARGIN + bar_w, hp_y0 + 8], fill=BAR_BG)
    hplen = int(bar_w * min(1.0, max(0.0, structure.hp / structure.max_hp)))
    if hplen > 0:
        draw.rectangle([MARGIN, hp_y0, MARGIN + hplen, hp_y0 + 8], fill=HP_BAR)

    # Tick indicator dots along bottom
    dot_y = hp_y0 + 14
    tick_frac = min(1.0, tick / (CAPTURE_TICKS + 1))
    dot_x = int(MARGIN + tick_frac * bar_w)
    draw.ellipse([dot_x - 3, dot_y, dot_x + 3, dot_y + 6], fill=(200, 200, 100))

    return img


def _contact_sheet(scenario_frames):
    """scenario_frames: list of (scenario_name, [PIL.Image])"""
    label_w  = 140
    max_cols = max(len(frames) for _, frames in scenario_frames)
    sheet_w  = label_w + max_cols * FRAME_W + (max_cols - 1) * 4
    row_h    = FRAME_H + 4
    sheet_h  = len(scenario_frames) * row_h + 30

    sheet = Image.new("RGB", (sheet_w, sheet_h), (20, 22, 28))
    draw  = ImageDraw.Draw(sheet)
    draw.text((8, 8), "Checkpoint J — Reinforcement Mechanics", fill=(200, 200, 200))

    for row_idx, (name, frames) in enumerate(scenario_frames):
        y0 = 30 + row_idx * row_h
        draw.text((4, y0 + FRAME_H // 2 - 5), name, fill=(160, 160, 180))
        for col_idx, frame in enumerate(frames):
            x0 = label_w + col_idx * (FRAME_W + 4)
            sheet.paste(frame, (x0, y0))

    return sheet


# ── Scenario runners ─────────────────────────────────────────────────────────

def run_uncontested():
    print("\n── Scenario 1: Uncontested capture (neutral → player) ──────────────────")
    tmap  = TacticalMap(width=4000, height=4000, layers=5)
    store = UnitStore()
    store.spawn("Vanguard", PLAYER, 2050.0, 2000.0)
    store.spawn("Vanguard", PLAYER, 1950.0, 2000.0)
    store.spawn("Vanguard", PLAYER, 2000.0, 2050.0)
    engine    = _make_engine(tmap, store)
    structure = _make_structure(owner=NEUTRAL)
    engine.reinforcement_structures = [structure]
    _rebuild_hash(engine)

    SAMPLE = [0, 40, 80, 120, 160, CAPTURE_TICKS]
    capture_tick = None
    frames = []
    owner_name = {NEUTRAL: "neutral", PLAYER: "player", ENEMY: "enemy"}

    for t in range(CAPTURE_TICKS + 5):
        if t in SAMPLE:
            print(f"  tick {t:>3}: progress={structure.capture_progress:.3f}  "
                  f"owner={owner_name.get(structure.owner_faction, str(structure.owner_faction))}")
            frames.append(_draw_frame(structure,
                                      {PLAYER: [(2050, 2000), (1950, 2000), (2000, 2050)]},
                                      t, f"t={t}"))

        step_reinforcement(engine, DT)

        if capture_tick is None and structure.owner_faction == PLAYER:
            capture_tick = t + 1  # flip happened inside this step

    assert structure.owner_faction == PLAYER, \
        f"FAIL: owner should be player, got {structure.owner_faction}"
    assert capture_tick is not None, "FAIL: capture never completed"
    assert abs(capture_tick - CAPTURE_TICKS) <= 1, \
        f"FAIL: capture took {capture_tick} ticks, expected {CAPTURE_TICKS} ± 1"

    print(f"  Capture completed at tick {capture_tick} (expected {CAPTURE_TICKS} ± 1)  ✓")
    return frames


def run_contested():
    print("\n── Scenario 2: Contested (player + enemy in radius → stall) ────────────")
    tmap  = TacticalMap(width=4000, height=4000, layers=5)
    store = UnitStore()
    store.spawn("Vanguard", PLAYER, 2050.0, 2000.0)
    store.spawn("Vanguard", ENEMY,  1950.0, 2000.0)
    engine    = _make_engine(tmap, store)
    structure = _make_structure(owner=NEUTRAL)
    engine.reinforcement_structures = [structure]
    _rebuild_hash(engine)

    frames = []
    for t in range(100):
        if t in (0, 25, 50, 75, 99):
            print(f"  tick {t:>3}: progress={structure.capture_progress:.3f}  (stalled)")
            frames.append(_draw_frame(structure,
                                      {PLAYER: [(2050, 2000)], ENEMY: [(1950, 2000)]},
                                      t, f"t={t}"))
        step_reinforcement(engine, DT)

    assert structure.capture_progress == 0.0, \
        f"FAIL: progress should be 0.0, got {structure.capture_progress}"
    assert structure.owner_faction == NEUTRAL, \
        f"FAIL: owner should stay neutral, got {structure.owner_faction}"
    print(f"  No ownership change after 100 ticks  ✓")
    return frames


def run_abandoned():
    print("\n── Scenario 3: Abandoned (units removed mid-capture → reset) ────────────")
    tmap  = TacticalMap(width=4000, height=4000, layers=5)
    store = UnitStore()
    uid = store.spawn("Vanguard", PLAYER, 2050.0, 2000.0)
    engine    = _make_engine(tmap, store)
    structure = _make_structure(owner=NEUTRAL)
    engine.reinforcement_structures = [structure]
    _rebuild_hash(engine)

    RUN_TICKS = 50
    frames = []
    for t in range(RUN_TICKS):
        if t in (0, 25, RUN_TICKS - 1):
            frames.append(_draw_frame(structure, {PLAYER: [(2050, 2000)]}, t, f"t={t}"))
        step_reinforcement(engine, DT)

    expected = RUN_TICKS * (DT / CAPTURE_DUR)
    print(f"  tick {RUN_TICKS}: progress={structure.capture_progress:.3f}  "
          f"(expected ≈{expected:.3f})")

    # Kill the capturing unit
    store.kill(uid)
    # spatial_hash still has the dead uid, but step_reinforcement filters by alive
    step_reinforcement(engine, DT)

    frames.append(_draw_frame(structure, {}, RUN_TICKS + 1, f"t={RUN_TICKS+1}"))
    print(f"  tick {RUN_TICKS + 1}: progress={structure.capture_progress:.3f}  (reset)  ✓")

    assert structure.capture_progress == 0.0, \
        f"FAIL: progress should reset to 0.0, got {structure.capture_progress}"
    assert structure.owner_faction == NEUTRAL, \
        f"FAIL: owner should remain neutral, got {structure.owner_faction}"
    print(f"  Ownership unchanged after abandonment  ✓")
    return frames


def run_flip():
    print("\n── Scenario 4: Flip (enemy-owned → player) ─────────────────────────────")
    tmap  = TacticalMap(width=4000, height=4000, layers=5)
    store = UnitStore()
    store.spawn("Vanguard", PLAYER, 2050.0, 2000.0)
    engine    = _make_engine(tmap, store)
    structure = _make_structure(owner=ENEMY)
    engine.reinforcement_structures = [structure]
    _rebuild_hash(engine)

    SAMPLE = [0, 40, 80, 120, 160, CAPTURE_TICKS]
    capture_tick = None
    frames = []
    owner_name = {NEUTRAL: "neutral", PLAYER: "player", ENEMY: "enemy"}

    for t in range(CAPTURE_TICKS + 5):
        if t in SAMPLE:
            print(f"  tick {t:>3}: progress={structure.capture_progress:.3f}  "
                  f"owner={owner_name.get(structure.owner_faction, str(structure.owner_faction))}")
            frames.append(_draw_frame(structure, {PLAYER: [(2050, 2000)]}, t, f"t={t}"))

        step_reinforcement(engine, DT)

        if capture_tick is None and structure.owner_faction == PLAYER:
            capture_tick = t + 1

    assert structure.owner_faction == PLAYER, \
        f"FAIL: owner should flip to player, got {structure.owner_faction}"
    assert capture_tick is not None, "FAIL: capture never completed"
    print(f"  Flip completed at tick {capture_tick} (expected {CAPTURE_TICKS} ± 1)  ✓")
    return frames


def run_hp_destruction():
    print("\n── Scenario 5: HP destruction ───────────────────────────────────────────")
    tmap  = TacticalMap(width=4000, height=4000, layers=5)
    store = UnitStore()
    engine    = _make_engine(tmap, store)
    structure = _make_structure()
    engine.reinforcement_structures = [structure]

    before_hp   = structure.hp
    before_count = len(engine.reinforcement_structures)
    print(f"  hp={before_hp:.0f}  structures=[{structure.structure_uid}]")

    structure.hp = 0.0
    step_reinforcement(engine, DT)

    after_count = len(engine.reinforcement_structures)
    print(f"  hp set to 0  →  structures=[]  ✓")

    assert structure not in engine.reinforcement_structures, \
        "FAIL: destroyed structure should be removed from list"
    assert after_count == 0, \
        f"FAIL: expected 0 structures, got {after_count}"

    frames_before = _draw_frame(
        ReinforcementStructure(1, STRUCT_POS, 0, before_hp, before_hp,
                               NEUTRAL, 0.0, 0.0, "Vanguard", CAPTURE_R),
        {}, 0, "full HP")
    frames_after = _draw_frame(
        ReinforcementStructure(1, STRUCT_POS, 0, 0.0, before_hp,
                               NEUTRAL, 0.0, 0.0, "Vanguard", CAPTURE_R),
        {}, 1, "destroyed")
    return [frames_before, frames_after]


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    failures = []

    print("Checkpoint J — Reinforcement Structure Mechanics")
    print("=" * 60)

    scenario_frames = []

    try:
        frames = run_uncontested()
        scenario_frames.append(("1 uncontested", frames))
    except AssertionError as e:
        print(f"  {e}")
        failures.append(str(e))

    try:
        frames = run_contested()
        scenario_frames.append(("2 contested", frames))
    except AssertionError as e:
        print(f"  {e}")
        failures.append(str(e))

    try:
        frames = run_abandoned()
        scenario_frames.append(("3 abandoned", frames))
    except AssertionError as e:
        print(f"  {e}")
        failures.append(str(e))

    try:
        frames = run_flip()
        scenario_frames.append(("4 flip", frames))
    except AssertionError as e:
        print(f"  {e}")
        failures.append(str(e))

    try:
        frames = run_hp_destruction()
        scenario_frames.append(("5 hp destruct", frames))
    except AssertionError as e:
        print(f"  {e}")
        failures.append(str(e))

    # Contact sheet
    if scenario_frames:
        sheet = _contact_sheet(scenario_frames)
        sheet_path = os.path.join(OUT_DIR, "contact_sheet.png")
        sheet.save(sheet_path)
        print(f"\nPNGs → {OUT_DIR}")

    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)
    else:
        print("\nCheckpoint J complete — no failures.")


if __name__ == "__main__":
    main()
