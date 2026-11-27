"""The arc check (story docs/stories/H-091.md R-091-15; engine rule E-13 R-100-04): no shot leaves a unit whose target is outside its firing arc.

A lab check on a finished fight file, not a rule of the checker's list (scripts/skilllab/invariants.py RULES does not gain it). `check_arc(doc)` takes an every-tick `--facing on` fight
document and returns the violations, empty when every shot is inside. For each entry of a frame's `hits` (attacker `a`, victim `v`, tick T) it takes the angle between the attacker's facing
at the START of tick T (its row in frame T-1: csrc/unit.c om_tac_in_arc reads the facing the unit had when the tick began) and the direction from the attacker to the victim on the positions of
frame T. A shot whose angle is more than half the arc (`doc["stage5"]["arc_deg"]`) is a violation; exactly half is inside (R-091-06). The file rounds facing to 3 decimals and positions to 2, so
an angle within ROUND_DEG of the edge counts as on it. A file that cannot be judged (no `stage5`, or no frame T-1 or T for a shot: not an every-tick file) raises ValueError rather than pass.
See also: scripts/skilllab/arena/stage5.py (writes `hits`), tests/csim/test_E13_R100_04_firing_arc.py (the engine's own check)."""
import math

RULE = "R-100-04"
ROUND_DEG = 0.05   # a facing rounded to 3 decimals is off by up to 0.029 degree; positions rounded to 2 decimals add under 0.02 at 20 wu


def check_arc(doc):
    """[{"rule": "R-100-04", "tick", "unit", "target", "angle_deg", "detail"}] for every shot outside the arc, in (tick, unit) order."""
    if "stage5" not in doc:
        raise ValueError("no stage5 table: the arc check judges a --facing on fight file")
    half = doc["stage5"]["arc_deg"] / 2.0
    rows = {f["tick"]: {u["id"]: u for u in f["units"]} for f in doc["frames"]}
    out = []
    for h in sorted((h for f in doc["frames"] for h in f.get("hits", [])), key=lambda h: (h["tick"], h["a"], h["v"])):
        t, a, v = h["tick"], h["a"], h["v"]
        if t - 1 not in rows or t not in rows:
            raise ValueError("the arc check needs an every-tick file: no frame for tick %d or %d" % (t - 1, t))
        start, end = rows[t - 1][a], rows[t]
        turn = (math.atan2(end[v]["y"] - end[a]["y"], end[v]["x"] - end[a]["x"]) - start["facing"] + math.pi) % (2.0 * math.pi) - math.pi
        angle = abs(math.degrees(turn))
        if angle > half + ROUND_DEG:
            out.append({"rule": RULE, "tick": t, "unit": a, "target": v, "angle_deg": round(angle, 2),
                        "detail": "unit %d fired at unit %d on tick %d with the target %.2f degrees from its facing, outside the half arc of %.1f degrees" % (a, v, t, angle, half)})
    return out
