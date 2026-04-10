import math
import config
import damage as dmg_module
from unit import UnitStore, FIELD_X, FIELD_Y, FIELD_HP, FIELD_ATTACK_TIMER, CATEGORY_NAMES
from tactical_engine import TacticalEngine
from command import Command, CommandQueue
from test_maps import open_field

FACTION_RAIDER = 0
FACTION_VANGUARD = 1
DT = config.TACTICAL_TICK_DURATION
SAMPLE = 20


def _print_stats():
    r = config.UNIT_STATS["Raider"]
    v = config.UNIT_STATS["Vanguard"]
    mx = config.CATEGORY_MULTIPLIER
    print("=" * 60)
    print("UNIT STATS")
    print(f"  Raider:   hp={r['hp']}  dmg={r['base_damage']}  interval={r['attack_interval']}s  range={r['attack_range']}")
    print(f"  Vanguard: hp={v['hp']}  dmg={v['base_damage']}  interval={v['attack_interval']}s  range={v['attack_range']}")
    print("CATEGORY MULTIPLIERS")
    for cat, row in mx.items():
        print(f"  {cat}: {row}")
    r_mult = mx["Strike"]["Line"]
    v_mult = mx["Line"]["Strike"]
    r_dps  = r["base_damage"] * r_mult / r["attack_interval"]
    v_dps  = v["base_damage"] * v_mult / v["attack_interval"]
    print(f"THEORETICAL TTK (1v1, no abilities, no cover)")
    print(f"  Raider  -> Vanguard: dmg/shot={r['base_damage']*r_mult:.2f}  DPS={r_dps:.2f}  TTK={v['hp']/r_dps:.1f}s")
    print(f"  Vanguard-> Raider:   dmg/shot={v['base_damage']*v_mult:.2f}  DPS={v_dps:.2f}  TTK={r['hp']/v_dps:.1f}s")
    print("=" * 60)


def _run_scenario(mode, seed=1):
    """mode: 'attack_move' or 'plain_move'"""
    store = UnitStore()
    tmap = open_field()

    raider   = store.spawn("Raider",   FACTION_RAIDER,   500.0, 2000.0)
    vanguard = store.spawn("Vanguard", FACTION_VANGUARD, 2000.0, 2000.0)

    queue = CommandQueue()
    if mode == "attack_move":
        queue.add(Command(tick=0, type="attack_move", unit_ids=[raider],
                          params={"target_x": 3500.0, "target_y": 2000.0}))
    else:
        queue.add(Command(tick=0, type="move", unit_ids=[raider],
                          params={"target_x": 3500.0, "target_y": 2000.0}))

    # Intercept _accumulate_single to log the first 20 Raider shots
    shot_log = []
    _orig = dmg_module._accumulate_single

    def _log_accumulate(s, attacker, target, base_dmg, attacker_cat, tactical_map, pending):
        if attacker == raider and len(shot_log) < 20:
            target_cat = CATEGORY_NAMES[s.category[target]]
            mult = config.CATEGORY_MULTIPLIER[attacker_cat][target_cat]
            final = base_dmg * mult  # cover=0 on open_field, no ability active at start
            shot_log.append((engine.tick, target, base_dmg, mult, final))
        return _orig(s, attacker, target, base_dmg, attacker_cat, tactical_map, pending)

    dmg_module._accumulate_single = _log_accumulate
    engine = TacticalEngine(tmap, store, seed=seed)
    engine.command_queue = queue

    print(f"\n{'─'*60}")
    print(f"MODE: {mode.upper()}")
    print(f"{'tick':>5} {'R_x':>7} {'R_hp':>7} {'V_hp':>7} {'R_tgt':>6} {'V_alive':>7}")

    for _ in range(6000):
        engine.step()
        if engine.tick % SAMPLE == 0:
            rx   = store.data[raider,   FIELD_X]
            r_hp = store.data[raider,   FIELD_HP] if store.alive[raider]   else 0
            v_hp = store.data[vanguard, FIELD_HP] if store.alive[vanguard] else 0
            tgt  = store.auto_engage_target[raider] if store.alive[raider] else -99
            print(f"{engine.tick:>5} {rx:>7.0f} {r_hp:>7.0f} {v_hp:>7.0f} {tgt:>6} {str(store.alive[vanguard]):>7}")
        if engine.is_terminal():
            break

    dmg_module._accumulate_single = _orig  # restore

    print(f"\nTerminal at tick {engine.tick} ({engine.tick * DT:.1f}s)")
    print(f"Raider alive: {store.alive[raider]}  |  Vanguard alive: {store.alive[vanguard]}")

    print(f"\nFirst {len(shot_log)} Raider shots (tick / tgt / raw_dmg / rps_mult / final_dmg):")
    print(f"  {'tick':>5}  {'tgt':>4}  {'raw':>7}  {'mult':>6}  {'final':>7}")
    for tick, tgt, raw, mult, final in shot_log:
        print(f"  {tick:>5}  {tgt:>4}  {raw:>7.2f}  {mult:>6.3f}  {final:>7.2f}")

    return engine.tick


def run():
    _print_stats()
    t_am    = _run_scenario("attack_move")
    t_plain = _run_scenario("plain_move")

    print(f"\n{'='*60}")
    print(f"COMPARISON")
    print(f"  attack_move terminal tick: {t_am}  ({t_am * DT:.1f}s)")
    print(f"  plain_move  terminal tick: {t_plain}  ({t_plain * DT:.1f}s)")
    print(f"  Difference: {abs(t_am - t_plain)} ticks ({abs(t_am - t_plain) * DT:.1f}s)")
    print("  (If close, attack_move is not distorting damage)")


if __name__ == "__main__":
    run()
