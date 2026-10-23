"""Small batch (design chat, 2026-10-01): a control first, then ONE skill on ONE map family at ONE size, read in soldiers.
Usage: python3 experiments/small_batch.py"""
import sys
sys.path.insert(0, ".")
from layerlab.skill import controls, plays
from layerlab.skill.rstar import rstar, rstar_windows
from layerlab.skill.situation import sample_situations


def summary_line(rs, size):
    """The break-even in whole heads, read from the bracket edges (never from value * size)."""
    if rs.last_win_heads is None or rs.first_loss_heads is None:
        return f"no break-even: above_scan={rs.above_scan} below_scan={rs.below_scan} short_scan={rs.short_scan} valid={rs.valid}"
    return f"{size} skilled heads beat {rs.last_win_heads} and lose to {rs.first_loss_heads}"


def show(title, rs, size):
    print(f"\n{title}")
    print("  enemy heads | skilled margin | skilled firing/head | naive firing/head | firing advantage")
    for p in rs.points:
        print(f"  {p['heads']:>11d} | {p['value']:>+14.3f} | {p['skilled_firing_per_head']:>19.1f} | "
              f"{p['naive_firing_per_head']:>17.1f} | {p['firing_adv'] if p['firing_adv'] is None else round(p['firing_adv'], 2)}")
    line = summary_line(rs, size)
    if rs.value is not None and rs.last_win_heads is not None and rs.first_loss_heads is not None:
        print(f"  break-even: {line} (R* {rs.value:.3f}, cost ratio {rs.value_cost:.3f}); firing advantage at break-even"
              f" {rs.firing_adv_at_rstar}, at equal heads {rs.firing_adv_equal}; valid={rs.valid} label_gap={rs.label_gap:.3f}")
    else:
        print(f"  {line}")


if __name__ == "__main__":
    size = 8
    m = controls.mirror_control(size, processes=4)
    show(f"CONTROL mirror, {size} v {size} identical raiders, flat: expect break-even 1.0", m, size)
    sit = [s for s in sample_situations(14, 1) if s.family == "flat"][0]
    print(f"\nsituation: family={sit.family} mix={sit.mix} approach={sit.approach_distance:.0f} refusable={sit.refusable}")
    for combo, name in ((frozenset(), "naive vs naive (R0)"), (frozenset({"S2"}), "S2 formation (concave) vs naive")):
        build = plays.build_scenario(sit, combo, size)
        rs = rstar(build, seeds=(0, 1, 2), processes=4, size=size)
        show(f"{name}", rs, size)
