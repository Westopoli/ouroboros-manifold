"""Each map's naive-against-naive break-even, reported beside every result on that map (plan Phase S, item 5c)."""
from dataclasses import dataclass

from scripts.skilllab.asym import Side, asym_play
from scripts.skilllab.breakeven import BreakEven, find_break_even
from scripts.skilllab.contract import Terrain
from scripts.skilllab.terrain import with_terrain


@dataclass
class MapReport:
    kind: str
    seed: int
    terrain: Terrain
    naive: BreakEven


def naive_break_even(kind, seed, terrain, size, enemy_from, enemy_to, replicates=10, near_replicates=30,
                     max_rounds=2, fight_fn=None, map_fn=None):
    build = with_terrain(asym_play(size, Side("blob"), Side("blob")), terrain)
    naive = find_break_even(build, size, enemy_from, enemy_to, replicates=replicates,
                            near_replicates=near_replicates, max_rounds=max_rounds,
                            fight_fn=fight_fn, map_fn=map_fn)
    return MapReport(kind, seed, terrain, naive)


def map_labels(report):
    return {"map_kind": report.kind, "map_seed": report.seed, "naive_beats": report.naive.beats,
            "naive_loses_to": report.naive.loses_to, "naive_multi_flip": report.naive.multi_flip, "baseline_ceiling": report.naive.ceiling_hit}
