"""E6, guns that bear (README 6.2). A line of n units (A) crosses the head of a column of n units (B) marching
at it. Firing arcs are on (rules.facing_gates_fire): a unit fires only at a target inside its arc, so the
firing-count ratio should follow how many units' arcs bear, and decay as the column turns. Control: arc 360
(everyone bears). Both sides attack-move, nearest-target, same layer, flat, hard bodies on."""
import copy
from layerlab import scenario
from layerlab.scenario import set_path

def build(arc=60.0, n=10, gate=1, line_x=2600.0, y=1000.0, col_x=900.0, base="scenarios/x0_mirror.toml", turn=6.0, broadside=False, offset=180.0):
    scn = scenario.load(base)
    t = copy.deepcopy(scn["types"]["raider"]); t["arc_deg"] = float(arc); t["turn_rate"] = float(turn)
    scn["types"]["raider_arc"] = t
    if broadside:
        # the line lies ALONG the column's path, `offset` to its side, facing across it (south); the column marches
        # east past it, facing east, so its guns do not bear until it turns. Hold orders on the line.
        mid = 2000.0
        scn["groups"] = [
            dict(side="A", type="raider_arc", count=n, formation="column", x=mid, y=y + offset, facing=-90.0, layer=3, order="hold", goal=[mid, y + offset]),
            dict(side="B", type="raider_arc", count=n, formation="column", x=mid - 500.0, y=y, facing=0.0, layer=3, order="attack_move", goal=[mid + 800.0, y]),
        ]
        # a "column" is laid out along its facing; the broadside line needs to run east-west, so lay it out as a line facing north-south
        scn["groups"][0]["formation"] = "line"
    else:
        scn["groups"] = [
            dict(side="A", type="raider_arc", count=n, formation="line", x=line_x, y=y, facing=180.0, layer=3, order="hold", goal=[line_x, y]),
            dict(side="B", type="raider_arc", count=n, formation="column", x=col_x, y=y, facing=0.0, layer=3, order="attack_move", goal=[line_x, y]),
        ]
    scn = set_path(scn, "rules.facing_gates_fire", gate)
    scn = set_path(scn, "rules.chase_when_idle", 1)
    return scn
