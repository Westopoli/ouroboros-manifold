import sys, collections
sys.path.insert(0, "/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/b1e8769e-404e-4263-be23-8535a58b0e59/scratchpad/mix_B")
from mixlib import *
from scripts.skilllab import sweep
lay = sweep.smoke_layouts()
layout, feats = next(iter(lay.items()))
for play in ("s3_layer_above", "s3_types_by_reach"):
    for role in ("play",) + tuple(sweep.baseline_roles(play)):
        b = sweep.default_builds(play, role, feats)
        s = b(16, False)
        c0 = collections.Counter(); c1 = collections.Counter()
        for g in s.groups:
            (c0 if g.side == 0 else c1)["%s@L%d" % (g.unit, g.layer)] += g.count
        print(play, "layout", layout, role, "side0", dict(c0), "side1", dict(c1), flush=True)
