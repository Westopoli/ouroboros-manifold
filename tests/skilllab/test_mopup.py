# spec: docs/northstar/plans/briefs/2026-10-06-sonnet-parallel-briefs.md::B1 (mop-up "in attack range" means able to shoot)
"""mopup_goal: a same-layer enemy within range counts as "in attack range" only when the unit can shoot it.
A wall between a pair (can_shoot false) must not veto the re-order forever; a clear line still does."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.mopup import mopup_goal  # noqa: E402

RANGE = 100.0


class Stub:
    """Two units on one layer 50 wu apart (inside range); unit 1 is mine, unit 2 theirs. Nobody has a destination."""

    def __init__(self, shootable, sees=True, layer2=0):
        self.shootable, self.sees, self.layer2 = shootable, sees, layer2
        self.pos = {1: (0.0, 0.0), 2: (50.0, 0.0)}

    def unit_pos(self, w, u):
        return self.pos[u]

    def unit_layer(self, w, u):
        return 0 if u == 1 else self.layer2

    def unit_destination(self, w, u):
        return None

    def can_see(self, w, a, b):
        return self.sees

    def can_shoot(self, w, a, b):
        return self.shootable


def goal(engine):
    return mopup_goal(engine, "w", [1], [2], {1: RANGE, 2: RANGE}, {1, 2})


def test_enemy_in_range_behind_a_block_does_not_veto_the_reorder():
    assert goal(Stub(shootable=False)) == (50.0, 0.0)


def test_enemy_in_range_with_a_clear_line_still_vetoes_the_reorder():
    assert goal(Stub(shootable=True)) is None


def test_enemy_on_another_layer_in_range_does_not_veto_even_when_shootable():
    assert goal(Stub(shootable=True, layer2=3)) == (50.0, 0.0)


def test_positive_control_blocked_enemy_not_seen_gives_no_goal():
    assert goal(Stub(shootable=False, sees=False)) is None


# spec: Architect ruling 2026-10-06 (residual stalemate), ruling 1 (changed 2026-10-07): with no enemy seen, go to the enemy's starting anchor (mopup_goal enemy_anchor kwarg)
class Hunt(Stub):
    """Unit 1 mine at the origin; living enemies 2 (far) and 3 (nearer), both out of range; `sees` decides sight."""

    def __init__(self, sees):
        super().__init__(shootable=True, sees=sees)
        self.pos = {1: (0.0, 0.0), 2: (900.0, 0.0), 3: (0.0, 600.0), 4: (10.0, 0.0)}


def hunt_goal(engine, alive=(1, 2, 3), **kw):
    return mopup_goal(engine, "w", [1], [2, 3, 4], {1: RANGE}, set(alive), **kw)


ANCHOR = (1500.0, -300.0)   # the enemy's first-group spawn position at setup


def test_unseen_enemies_re_order_at_the_enemy_anchor():
    assert hunt_goal(Hunt(sees=False), enemy_anchor=ANCHOR) == ANCHOR


def test_unseen_goal_is_the_anchor_not_the_nearest_unit():
    """Living enemy 3 is 600 wu away, far nearer than the anchor; the goal is still the anchor."""
    assert hunt_goal(Hunt(sees=False), alive=(1, 2, 3), enemy_anchor=ANCHOR) == ANCHOR
    assert hunt_goal(Hunt(sees=False), alive=(1, 3), enemy_anchor=ANCHOR) == ANCHOR


def test_seen_enemy_goal_is_unchanged_from_today():
    assert hunt_goal(Hunt(sees=True)) == (0.0, 600.0)


def test_positive_control_no_living_enemy_gives_no_goal():
    assert hunt_goal(Hunt(sees=False), alive=(1,)) is None
