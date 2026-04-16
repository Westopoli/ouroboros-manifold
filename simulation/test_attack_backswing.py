from tactical_engine import TacticalEngine
from command import Command
from test_maps import open_field


def count_disengage_events(n_ticks=300):
    """Count how many times a fast Raider loses its engage lock on a fleeing Bastion.

    High count = oscillation/jitter. Low count = smooth chase-and-fire stride.

    Raider (speed=150, range=200) chases Bastion (speed=40) that is plain-moving
    away. Bastion does NOT attack_move — it just flees — so it never stops to fight.
    The Raider attack_moves and uses sensor pursuit to chase.

    The leash (_ATTACK_MOVE_LEASH_SQ=200) is the same radius as Raider's attack
    range, so the leash breaks almost immediately once the Raider stops and the
    Bastion keeps moving. Without backswing this produces rapid oscillation (many
    disengage events per 300 ticks). With backswing the cycle is stretched.
    """
    tmap = open_field()
    engine = TacticalEngine(tmap, seed=7)
    raider  = engine.store.spawn("Raider",  0, 2000.0, 2000.0)
    bastion = engine.store.spawn("Bastion", 1, 2000.0, 2250.0)

    # Raider pursues north; Bastion plain-moves north (flees without turning to fight)
    engine.command_queue.add(Command(tick=0, type="attack_move", unit_ids=[raider],
                                     params={"target_x": 2000.0, "target_y": 5000.0}))
    engine.command_queue.add(Command(tick=0, type="move", unit_ids=[bastion],
                                     params={"target_x": 2000.0, "target_y": 5000.0}))

    disengages = 0
    prev_engaged = False
    for _ in range(n_ticks):
        engine.step()
        if not engine.store.alive[raider] or not engine.store.alive[bastion]:
            break
        tgt = engine.store.auto_engage_target[raider]
        engaged = tgt >= 0 and engine.store.alive[tgt]
        if prev_engaged and not engaged:
            disengages += 1
        prev_engaged = engaged

    print(f"Disengage events in {n_ticks} ticks: {disengages}")
    return disengages


if __name__ == "__main__":
    count_disengage_events()
