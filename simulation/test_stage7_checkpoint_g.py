import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from map_gen_contracts import RegionState
from sim_flavoring import compute_flavoring, apply_flavoring, FlavoringDeltas
from layout_library import load_all_layouts
from layout_instantiator import instantiate_layout
from gradient_placer import place_gradients
import config

PROPS = ["obstacle_density", "cover_density", "elevation", "sensor_interference"]

REPRESENTATIVE_STATES = [
    ("high_stability", RegionState(
        stability=0.90, capacity=0.80,
        economy=70.0, tension=20.0, military=40.0, population=65.0,
    )),
    ("low_stability", RegionState(
        stability=0.15, capacity=0.30,
        economy=22.0, tension=78.0, military=55.0, population=40.0,
    )),
    ("high_tension", RegionState(
        stability=0.50, capacity=0.40,
        economy=30.0, tension=90.0, military=80.0, population=60.0,
    )),
]


def delta_val(deltas: FlavoringDeltas, prop: str) -> float:
    return getattr(deltas, prop)


def main():
    print("=== Stage 7 Checkpoint G: Simulation Flavoring ===\n")

    # ── Per-property modifier values for the 3 representative states ──────────
    print("── Deltas per representative state ─────────────────────────────────")
    header = f"{'state':<20}" + "".join(f"  {p[:3+3]:>10}" for p in PROPS)
    print(header)
    for label, rs in REPRESENTATIVE_STATES:
        d = compute_flavoring(rs)
        row = f"{label:<20}" + "".join(f"  {delta_val(d, p):+.4f}    " for p in PROPS)
        print(row)
    print()

    # ── Direction assertions ──────────────────────────────────────────────────
    failures = []

    def assert_direction(label, rs, prop, direction, reason):
        d = compute_flavoring(rs)
        val = delta_val(d, prop)
        ok = (val > 0) if direction == "positive" else (val < 0)
        if not ok:
            msg = f"{label}: {prop} expected {direction} but got {val:+.4f}  ({reason})"
            failures.append(msg)
            print(f"  FAIL: {msg}")

    label_hs, rs_hs = REPRESENTATIVE_STATES[0]   # high_stability
    label_ls, rs_ls = REPRESENTATIVE_STATES[1]   # low_stability
    label_ht, rs_ht = REPRESENTATIVE_STATES[2]   # high_tension

    # Low stability → +SI and +cover
    assert_direction(label_ls, rs_ls, "sensor_interference", "positive",
                     "instability drives SI up")
    assert_direction(label_ls, rs_ls, "cover_density", "positive",
                     "instability drives cover up")

    # High stability + high capacity + high economy → -obstacle
    assert_direction(label_hs, rs_hs, "obstacle_density", "negative",
                     "capacity+economy should reduce obstacles")

    # High tension → +cover
    assert_direction(label_ht, rs_ht, "cover_density", "positive",
                     "high tension drives cover up")

    # High military (high_tension state has mil=80) → +obstacle
    assert_direction(label_ht, rs_ht, "obstacle_density", "positive",
                     "high military drives obstacle up")

    # Elevation always zero
    for label, rs in REPRESENTATIVE_STATES:
        d = compute_flavoring(rs)
        if d.elevation != 0.0:
            msg = f"{label}: elevation delta should be 0.0 but got {d.elevation}"
            failures.append(msg)
            print(f"  FAIL: {msg}")

    # Deltas must stay within configured cap
    for label, rs in REPRESENTATIVE_STATES:
        d = compute_flavoring(rs)
        for prop in PROPS:
            val = delta_val(d, prop)
            if abs(val) > config.FLAVOR_MAX_DELTA + 1e-9:
                msg = f"{label}: {prop} delta {val:+.4f} exceeds cap ±{config.FLAVOR_MAX_DELTA}"
                failures.append(msg)
                print(f"  FAIL: {msg}")

    if failures:
        print(f"\nFAILURES ({len(failures)}):")
        for f in failures:
            print(f"  {f}")
    else:
        print("All direction and bounds assertions passed.")

    # ── apply_flavoring: verify intensities shift correctly on a real layout ──
    print("\n── apply_flavoring smoke test (layout_01, medium) ──────────────────")
    library = load_all_layouts()
    layout = library["layout_01_fortress_ridge"]
    inst = instantiate_layout(layout, "medium", 0x1a2b3c)
    base_sources = place_gradients(inst)

    for label, rs in REPRESENTATIVE_STATES:
        deltas = compute_flavoring(rs)
        flavored = apply_flavoring(base_sources, deltas)
        assert len(flavored) == len(base_sources), "source count must be preserved"
        # Spot-check: obstacle_density sources shifted in expected direction
        obs_base  = [s.intensity for s in base_sources  if s.property_type == "obstacle_density"]
        obs_flav  = [s.intensity for s in flavored       if s.property_type == "obstacle_density"]
        delta_obs = deltas.obstacle_density
        for b, f in zip(obs_base, obs_flav):
            expected = max(0.0, min(1.0, b + delta_obs))
            if abs(f - expected) > 1e-9:
                failures.append(f"{label}: apply_flavoring intensity mismatch {f} vs {expected}")
        obs_mean_base  = sum(obs_base)  / len(obs_base)  if obs_base  else 0
        obs_mean_flav  = sum(obs_flav) / len(obs_flav) if obs_flav else 0
        print(f"  {label:<20}  obs_base_mean={obs_mean_base:.3f}  "
              f"obs_flavored_mean={obs_mean_flav:.3f}  "
              f"delta={delta_obs:+.4f}")

    print()
    if not failures:
        print("Checkpoint G complete — no failures.")
    else:
        print(f"TOTAL FAILURES: {len(failures)}")


if __name__ == "__main__":
    main()
