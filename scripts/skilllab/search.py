from dataclasses import dataclass


@dataclass(frozen=True)
class SearchSetting:
    radius: float          # ping radius, wu
    reach: float           # ping reach, wu
    reveal_ticks: int
    cooldown_ticks: int
    force: int             # seeker headcount; every unit casts


@dataclass(frozen=True)
class Placement:
    dx: float
    dy: float              # hider centre, relative to the seeker's start
    layer: int             # 0..4
    heading_deg: float
    script: str            # a key of search_policies.HIDER_SCRIPTS
