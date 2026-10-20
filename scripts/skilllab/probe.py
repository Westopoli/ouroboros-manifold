"""Inert-knob probe (rev 3 plan R6, test T2; defect D10; ledger FINDING-lab-d10): two fights of one play, the base and the knob at the
band's extreme; the knob is inert on the play when the fight row does not change."""
import dataclasses

from scripts.skilllab import fight as fight_mod, rows


def inert(build, settings, enemy_heads=16, seed=0, swap=False, fight_fn=None, base_settings=None):
    """True when the row of the fight with `settings` merged equals the row of the fight with `base_settings` merged (None: as built)."""
    fight_fn = fight_fn or fight_mod.fight
    setup = build(enemy_heads, swap)
    base = fight_fn(dataclasses.replace(setup, settings={**setup.settings, **(base_settings or {})}), seed, swap)
    moved = fight_fn(dataclasses.replace(setup, settings={**setup.settings, **settings}), seed, swap)
    return rows.fight_row(base) == rows.fight_row(moved)
