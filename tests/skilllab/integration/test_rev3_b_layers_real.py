# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R2, test T6; defect D1); ledger FINDING-lab-d1; piece LAB-REV3-B
"""LAB-REV3-B, T6 (R2, D1) on the placed scenes (OM_LAB_SLOW=1; seconds): a swept play that no layout can place never runs, and a play that
never runs covers nothing (plan T1). Every play of the layer families (vision, range_up, damage_up, sign_flip, emitting; not arc and cone) is placed on the three run-1 layouts of
`sweep.SMOKE_LAYOUTS` at the smallest and the largest headcount of a scan (8 and 48); at least one layout must pre-flight "ok" at both.
Which layouts batch one fields is Westley's (the layout fit probe is his page); this asks only that the new plays are not refused
everywhere. Green on the lab tip for the plays that are swept today; it guards the plays B adds. Left out on purpose: the arc and cone
family plays (s2_concave is `no_fit` at 8 and 48 on all three run-1 layouts today, measured by this file's author on the lab tip: the
layout fit is Westley's and the plan gives B no job there)."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import sweep  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="the placed scenes of the real layouts; set OM_LAB_SLOW=1")
LAYER_FAMILIES = ("vision", "range_up", "damage_up", "sign_flip", "emitting")
SWEPT = sorted({p for f in LAYER_FAMILIES for p in sweep.PLAYS_BY_FAMILY[f]})


@SLOW
@pytest.mark.parametrize("play", SWEPT)
def test_t6_every_swept_play_places_ok_on_at_least_one_run_1_layout(play):
    words = {}
    for layout, features in sweep.smoke_layouts().items():
        build = sweep.default_builds(play, "play", features)
        got = []
        for heads in (sweep.ENEMY_FROM, sweep.ENEMY_TO):
            build(heads, False)
            got.append(build.labels.get("prefight"))
        words[layout] = got
    assert any(set(g) == {"ok"} for g in words.values()), "%s is refused on every run-1 layout: %s" % (play, words)


@SLOW
@pytest.mark.parametrize("play", SWEPT)
def test_t6_every_baseline_of_a_swept_play_places_ok_on_at_least_one_run_1_layout(play):
    """R2: "plays AND BASELINES place sides on every layer pair the reach table allows". The baselines a play is read against (roles from
    sweep.baseline_roles of its own Setup) are built the way run_family builds them, on a layout where the play itself places; each role
    pre-flights "ok" at 8 and 48 on at least one such layout (a baseline refused everywhere leaves C1 unread on that play; run_family
    keeps the refusal in the artifact, this asks that the plays B adds are not refused on every layout). Green on the lab tip."""
    seen = {}
    for layout, features in sweep.smoke_layouts().items():
        play_build, roles = sweep._play_roles(sweep.default_builds, play, features)
        for h in (sweep.ENEMY_FROM, sweep.ENEMY_TO):
            play_build(h, False)
        if play_build.labels.get("prefight") != "ok":
            continue
        for role in roles:
            build = sweep.default_builds(play, role, features)
            words = []
            for h in (sweep.ENEMY_FROM, sweep.ENEMY_TO):
                build(h, False)
                words.append(build.labels.get("prefight"))
            seen.setdefault(role, []).append((layout, words))
    assert seen, "%s places on no run-1 layout" % play
    for role, got in seen.items():
        assert any(set(w) == {"ok"} for _l, w in got), "%s baseline %s is refused on every layout where the play places: %s" % (play, role, got)
