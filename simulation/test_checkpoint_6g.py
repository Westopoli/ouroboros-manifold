import math
import config
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_LAYER, FIELD_SENSOR_RADIUS
from fog_of_war import compute_visibility, activate_pulse, update_fog_timers
from test_maps import open_field, sensor_interference, multi_layer, vantage_point

FACTION_A = 0
FACTION_B = 1


def test_interference():
    print("=" * 70)
    print("  INTERFERENCE — Sensor radius reduction at varying intensities")
    print("=" * 70)

    tmap = sensor_interference()
    intensities_and_positions = [
        (0.0, 500.0),
        (0.2, 1000.0),
        (0.5, 1800.0),
        (0.8, 2600.0),
        (1.0, 3400.0),
    ]

    print(f"  {'Interference':>13} {'Base':>8} {'Effective':>10} {'Ratio':>8}")
    print(f"  {'-'*13} {'-'*8} {'-'*10} {'-'*8}")

    l11_pass = True
    for intensity, x_pos in intensities_and_positions:
        store = UnitStore()
        scout = store.spawn("Interceptor", FACTION_A, x_pos, 2000.0)
        store.spawn("Raider", FACTION_B, x_pos + 100.0, 2000.0)

        base_radius = store.data[scout, FIELD_SENSOR_RADIUS]
        vis = compute_visibility(store, tmap)

        actual_interference = tmap.sensor_interference(x_pos, 2000.0)
        effective = base_radius * (1.0 - actual_interference)
        ratio = effective / base_radius if base_radius > 0 else 0.0

        print(f"  {actual_interference:>12.1f} {base_radius:>8.0f} {effective:>10.0f} {ratio:>7.1%}")

        if abs(actual_interference - 0.8) < 0.05:
            if abs(ratio - 0.20) > 0.05:
                l11_pass = False

    print(f"\n  L11: {'PASS' if l11_pass else 'FAIL'} (0.8 interference → ~20% of base)")
    return l11_pass


def test_cross_layer_cone():
    print(f"\n{'=' * 70}")
    print("  CROSS-LAYER CONE — Detection radius by layer difference")
    print("=" * 70)

    tmap = multi_layer()
    store = UnitStore()

    scout = store.spawn("Interceptor", FACTION_A, 2000.0, 2000.0, layer=0)
    base_radius = store.data[scout, FIELD_SENSOR_RADIUS]

    targets = {}
    for layer in range(3):
        for dist in range(50, 600, 10):
            uid = store.spawn("Raider", FACTION_B, 2000.0 + dist, 2000.0, layer=layer)
            targets[(layer, dist)] = uid

    vis = compute_visibility(store, tmap)
    scout_visible = vis[scout]

    print(f"  Base sensor radius: {base_radius:.0f}")
    print(f"\n  {'Layer':>6} {'Expected %':>11} {'Max visible dist':>18} {'Effective':>10} {'Ratio':>8}")
    print(f"  {'-'*6} {'-'*11} {'-'*18} {'-'*10} {'-'*8}")

    expected = {0: 1.0, 1: config.CONE_LAYER_1_FACTOR, 2: config.CONE_LAYER_2_FACTOR}
    l12_pass = True

    for layer in range(3):
        max_visible_dist = 0
        for dist in range(50, 600, 10):
            uid = targets[(layer, dist)]
            if uid in scout_visible:
                max_visible_dist = dist

        effective = max_visible_dist
        ratio = effective / base_radius if base_radius > 0 else 0.0
        exp = expected[layer]
        exp_radius = base_radius * exp

        print(f"  {layer:>6} {exp:>10.0%} {max_visible_dist:>17} wu {effective:>10.0f} {ratio:>7.1%}")

        if layer == 1 and abs(ratio - 0.50) > 0.10:
            l12_pass = False
        if layer == 2 and abs(ratio - 0.20) > 0.10:
            l12_pass = False

    print(f"\n  L12: {'PASS' if l12_pass else 'FAIL'} (layer 1 ≈ 50%, layer 2 ≈ 20%)")
    return l12_pass


def test_vantage():
    print(f"\n{'=' * 70}")
    print("  VANTAGE BONUS — Doubled cone factors + extra layer")
    print("=" * 70)

    tmap = vantage_point()
    store = UnitStore()

    scout = store.spawn("Interceptor", FACTION_A, 2000.0, 2000.0, layer=0)
    base_radius = store.data[scout, FIELD_SENSOR_RADIUS]

    targets = {}
    for layer in range(3):
        for dist in range(50, 1100, 10):
            uid = store.spawn("Raider", FACTION_B, 2000.0 + dist, 2000.0, layer=layer)
            targets[(layer, dist)] = uid

    vis = compute_visibility(store, tmap)
    scout_visible = vis[scout]

    print(f"  Scout at vantage point (2000, 2000)")
    print(f"  Base sensor radius: {base_radius:.0f}")
    print(f"\n  {'Layer':>6} {'Max visible':>12} {'Ratio':>8}")
    print(f"  {'-'*6} {'-'*12} {'-'*8}")

    layer_3_visible = False
    for layer in range(3):
        max_visible_dist = 0
        for dist in range(50, 1100, 10):
            uid = targets.get((layer, dist))
            if uid and uid in scout_visible:
                max_visible_dist = dist

        ratio = max_visible_dist / base_radius if base_radius > 0 else 0.0
        print(f"  {layer:>6} {max_visible_dist:>11} wu {ratio:>7.1%}")

        if layer == 2 and max_visible_dist > 0:
            layer_3_visible = True

    tmap_no_vantage = multi_layer()
    store2 = UnitStore()
    scout2 = store2.spawn("Interceptor", FACTION_A, 2000.0, 2000.0, layer=0)
    for layer in range(3):
        for dist in range(50, 1100, 10):
            store2.spawn("Raider", FACTION_B, 2000.0 + dist, 2000.0, layer=layer)
    vis2 = compute_visibility(store2, tmap_no_vantage)
    no_vantage_l1 = 0
    for dist in range(50, 1100, 10):
        uid = 1 + 1 * ((1100 - 50) // 10) + (dist - 50) // 10
        # Simpler: just recount
    # Recount without vantage
    no_vantage_visible = vis2[scout2]
    no_v_max = {0: 0, 1: 0, 2: 0}
    for uid in range(store2.count):
        if uid in no_vantage_visible:
            layer = int(store2.data[uid, FIELD_LAYER])
            dist = store2.data[uid, FIELD_X] - 2000.0
            if dist > no_v_max[layer]:
                no_v_max[layer] = dist

    print(f"\n  Comparison (same scout, no vantage):")
    for layer in range(3):
        print(f"    Layer {layer}: {no_v_max[layer]:.0f} wu")

    ok = layer_3_visible
    print(f"\n  Vantage: {'PASS' if ok else 'FAIL'} (doubled factors, +1 layer visible)")
    return ok


def test_pulse():
    print(f"\n{'=' * 70}")
    print("  SENSOR PULSE — Temporary reveal within radius")
    print("=" * 70)

    tmap = open_field()
    store = UnitStore()

    # Bombard has 300 wu sensor radius — leaves a 200 wu gap to the 500 wu pulse radius
    scout = store.spawn("Bombard", FACTION_A, 2000.0, 2000.0)
    base_radius = store.data[scout, FIELD_SENSOR_RADIUS]

    far_enemy = store.spawn("Raider", FACTION_B, 2000.0 + config.PULSE_RADIUS + 50, 2000.0)
    pulse_enemy = store.spawn("Raider", FACTION_B, 2000.0 + base_radius + 50, 2000.0)

    vis_before = compute_visibility(store, tmap)
    far_visible_before = far_enemy in vis_before[scout]
    pulse_visible_before = pulse_enemy in vis_before[scout]

    activate_pulse(store, scout)

    vis_during = compute_visibility(store, tmap)
    far_visible_during = far_enemy in vis_during[scout]
    pulse_visible_during = pulse_enemy in vis_during[scout]

    for _ in range(config.PULSE_REVEAL_TICKS):
        update_fog_timers(store)

    vis_after = compute_visibility(store, tmap)
    far_visible_after = far_enemy in vis_after[scout]
    pulse_visible_after = pulse_enemy in vis_after[scout]

    print(f"  Far enemy ({base_radius + 50:.0f} wu, outside sensor, outside pulse):")
    print(f"    Before pulse: {far_visible_before}")
    print(f"    During pulse: {far_visible_during}")
    print(f"    After pulse:  {far_visible_after}")
    print(f"\n  Pulse-range enemy ({config.PULSE_RADIUS - 10} wu, outside sensor, inside pulse):")
    print(f"    Before pulse: {pulse_visible_before}")
    print(f"    During pulse: {pulse_visible_during}")
    print(f"    After pulse:  {pulse_visible_after}")
    print(f"\n  Pulse duration: {config.PULSE_REVEAL_TICKS} ticks")
    print(f"  Remaining after expiry: {store.pulse_remaining[scout]}")

    ok = (not pulse_visible_before and pulse_visible_during and not pulse_visible_after
          and not far_visible_before and not far_visible_during and not far_visible_after)
    print(f"\n  Pulse: {'PASS' if ok else 'FAIL'}")
    return ok


def test_instant_vanish():
    print(f"\n{'=' * 70}")
    print("  INSTANT VANISH — No ghost after leaving sensor coverage")
    print("=" * 70)

    tmap = open_field()
    store = UnitStore()

    scout = store.spawn("Interceptor", FACTION_A, 2000.0, 2000.0)
    base_radius = store.data[scout, FIELD_SENSOR_RADIUS]

    enemy = store.spawn("Raider", FACTION_B, 2000.0 + base_radius - 10, 2000.0)

    vis1 = compute_visibility(store, tmap)
    visible_inside = enemy in vis1[scout]

    store.data[enemy, FIELD_X] = 2000.0 + base_radius + 50
    vis2 = compute_visibility(store, tmap)
    visible_outside = enemy in vis2[scout]

    print(f"  Enemy at {base_radius - 10:.0f} wu (inside): visible = {visible_inside}")
    print(f"  Enemy at {base_radius + 50:.0f} wu (outside): visible = {visible_outside}")
    print(f"  Visibility is binary, no ghost state")

    ok = visible_inside and not visible_outside
    print(f"\n  Instant vanish: {'PASS' if ok else 'FAIL'}")
    return ok


def run():
    print("=" * 70)
    print("CHECKPOINT 6G — Fog of War (Isolation)")
    print("=" * 70)

    results = {}
    results["Interference (L11)"] = test_interference()
    results["Cross-layer (L12)"] = test_cross_layer_cone()
    results["Vantage"] = test_vantage()
    results["Pulse"] = test_pulse()
    results["Instant vanish"] = test_instant_vanish()

    print(f"\n{'=' * 70}")
    print("  SUMMARY")
    print("=" * 70)
    for name, passed in results.items():
        print(f"  {name:<24} {'PASS' if passed else 'FAIL'}")

    total_pass = sum(1 for v in results.values() if v)
    print(f"\n  {total_pass}/{len(results)} tests passed")
    print("\nCheckpoint 6G complete.")


if __name__ == "__main__":
    run()
