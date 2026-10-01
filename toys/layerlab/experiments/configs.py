"""The three lever configurations of README 6.3 (Westley, 2026-10-01), applied to any scenario dict.
Index convention for the 9-entry tables: offset = target layer minus own layer + 4, so index 3 is
firing down one layer and index 5 is firing up one layer.
  LA vision only: vision symmetric (0.50 / 0.20 as in base.toml); range and damage as on the unit's
                  own layer in every direction.
  LB vision and reach: LA, and a unit firing UP has its range multiplied by `ru` per layer (< 1);
                  firing down is full range.
  LC vision, reach and a damage penalty: LB, and a unit firing UP has its damage multiplied by `d`
                  per layer (< 1)."""
from layerlab.scenario import set_path

def table(up, down=1.0):
    t = [0.0] * 9
    t[4] = 1.0
    for k in range(1, 5):
        t[4 + k] = up ** k          # target k layers above the shooter
        t[4 - k] = down ** k        # target k layers below the shooter
    return t

def apply(scn, cfg, ru=0.8, d=0.8):
    if cfg == "LA":
        rng, dmg = table(1.0), table(1.0)
    elif cfg == "LB":
        rng, dmg = table(ru), table(1.0)
    elif cfg == "LC":
        rng, dmg = table(ru), table(d)
    else:
        raise ValueError(cfg)
    s = set_path(scn, "rules.range_mult", rng)
    s = set_path(s, "rules.dmg_mult", dmg)
    s = set_path(s, "rules.aoe_layer_mult", dmg)
    return s
