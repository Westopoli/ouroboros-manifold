"""Test-local oracle for R-087-01 (engine rule fixes 2026-11-11, Round 2, F9): a unit with no target that is hit by an enemy its side does not see.

Holds no tests. The lab checker (scripts/skilllab/invariants.py) has no check for this rule, so the measurement is written here, on the Recorder of
engine_rules_oracle.py (per tick: the unit rows before and after the step, the fire events, who sees whom).

Rule word for word (docs/bible/epics/E-11-units-and-combat.md, R-087-01): "Given an idle or attack-moving unit with no target that takes damage from an
attacker it cannot see or cannot reach, When the loop runs, Then it leaves the line of fire instead of standing or walking on blindly: it moves 200 wu
directly away from the damage direction and stops, and an attack-mover then resumes its attack-move toward its original point (R-096-02); once the attacker
is visible and in range it stands and fights."

The measure (`standing_in_unseen_fire`): an UNSEEN HIT is a fire event (attacker a, victim v) on a tick on which v is alive, hostile to a, holds no target at the
start of the tick, and a is seen by v's side neither before nor after the tick (om_player_can_see). A run of unseen hits on one victim starts at the first one,
where the victim stands (its position after the tick is the anchor); the run goes on while the next unseen hit comes within HIT_GAP ticks of the last and the
victim has stayed within WITHIN wu of the anchor on every tick; it is a VIOLATION at every unseen hit that lands more than STAY ticks after the first. A unit
that moved off (more than WITHIN wu from the anchor) ends the run; the next unseen hit starts a new one.

Detector bounds (not rules; Westley's to change):
  STAY      DRAFT-inv-unseen-fire-ticks 60   the brief: 'more than 60 ticks in a row while the hits continue'
  WITHIN    50 wu                            the brief: 'within 50 wu of where it was first hit'
  HIT_GAP   DRAFT-f9-hit-gap 60 ticks        how far apart two hits may be and still be 'the hits continue' (the slowest shot of the roster is 30 ticks apart
                                             in the L-0080 trace; 60 is two of them)
"""
import math

STAY = 60
WITHIN = 50.0
HIT_GAP = 60


def unseen_hits(rec):
    """[(tick, victim, attacker, victim layer, attacker layer)] of every unseen hit (definition above)."""
    out = []
    for tk in rec.ticks:
        pre = tk["pre"]
        for a, v in tk["fires"]:
            if v not in pre or a not in pre or not pre[v]["alive"] or rec.side[v] == rec.side[a] or pre[v]["tgt"]:
                continue
            s = rec.side[v]
            if tk["vis_pre"].get((s, a), False) or tk["vis_post"].get((s, a), False):
                continue
            out.append((tk["n"], v, a, pre[v]["layer"], pre[a]["layer"]))
    return out


def standing_in_unseen_fire(rec, stay=STAY, within=WITHIN, gap=HIT_GAP):
    """[(tick, victim, ticks since the first hit of the run, distance from the anchor)] of every unseen hit that lands more than `stay` ticks into a run on a
    victim that has stayed within `within` wu of where the run began."""
    by_tick = {}
    for h in unseen_hits(rec):
        by_tick.setdefault(h[0], []).append(h)
    anchor = {}                     # victim -> [first tick, x, y, last unseen hit]
    out = []
    for tk in rec.ticks:
        n, post = tk["n"], tk["post"]
        for v in list(anchor):
            p = post[v]
            if not p["alive"] or math.hypot(p["x"] - anchor[v][1], p["y"] - anchor[v][2]) > within:
                del anchor[v]
        for _, v, a, _, _ in by_tick.get(n, ()):
            p = post[v]
            run = anchor.get(v)
            if run is None or n - run[3] > gap:
                anchor[v] = [n, p["x"], p["y"], n]
                continue
            run[3] = n
            if n - run[0] > stay:
                out.append((n, v, n - run[0], round(math.hypot(p["x"] - run[1], p["y"] - run[2]), 1)))
    return out


def summary(rec):
    """The premise line: unseen hits, the violating hits, the victims, the first violation, and how many unseen hits came from a higher layer."""
    hits, bad = unseen_hits(rec), standing_in_unseen_fire(rec)
    return {"ticks": len(rec.ticks), "unseen_hits": len(hits), "from_higher_layer": sum(1 for h in hits if h[4] > h[3]),
            "violations": len(bad), "victims": len({b[1] for b in bad}), "first": bad[0] if bad else None}
