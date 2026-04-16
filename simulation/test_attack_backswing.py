from tactical_engine import TacticalEngine
from command import Command
from test_maps import open_field


def count_disengage_events(n_ticks=300):
    """Count how many times a fast Raider loses its engage lock on a fleeing Bastion.

    High count = oscillation/jitter. Low count = smooth chase-and-fire stride.
    Raider (speed=150, range=200) starts just outside range of Bastion (speed=40).
    Bastion flees. We count how often the Raider gains then loses its target lock.
    """
    tmap = open_field()
    engine = TacticalEngine(tmap, seed=7)
    raider  = engine.store.spawn("Raider",  0, 2000.0, 2200.0)
    bastion = engine.store.spawn("Bastion", 1, 2000.0, 2500.0)
    engine.command_queue.add(Command(tick=0, type="attack_move", unit_ids=[raider],
                                     params={"target_x": 2000.0, "target_y": 4000.0}))
    engine.command_queue.add(Command(tick=0, type="attack_move", unit_ids=[bastion],
                                     params={"target_x": 2000.0, "target_y": 500.0}))

    disengages = 0
    prev_engaged = False
    for _ in range(n_ticks):
        engine.step()
        if not engine.store.alive[raider]:
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
