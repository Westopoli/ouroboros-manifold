"""Helper for the movement-sidestep whole-run tests (piece LS1, story movement-sidestep).

A block is 100 ticks (frames whose tick // 100 is the same). A block's hash is the sha256 of, for each frame of the block in file order,
the line  json.dumps([tick, [[id, x, y, hp, target], ...]], separators=(",", ":"))  followed by a newline, units in the file's order
(ascending id), every unit of the frame (dead ones too). x and y are the frame's rounded values; nothing else of the frame is read.

How the literals in test_sidestep_variant_a_fights.py were computed (reproduce with the command in `main`):
variant A's fight files (the `every 2` documents of the 2026-11-24 comparison, ~/Projects/om-wt/engine-rules-baseline/r6-compare/runs/A-l54/
and A-sit/, seed 1, sha256 recorded in their .meta.json) are streamed frame by frame with `stream_frames` (they are pretty-printed with
2-space indent; a frame is the text between a line "    {" and the line "    }" or "    },"), then folded by `block_hashes`.
The test folds the frames of a fresh lab fight (scripts/skilllab/arena/run.fight, sight off, every 2 ticks) the same way.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

BLOCK_TICKS = 100


def _line(frame):
    rows = [[u["id"], u["x"], u["y"], u["hp"], u["target"]] for u in frame["units"]]
    return json.dumps([frame["tick"], rows], separators=(",", ":")) + "\n"


def block_hashes(frames):
    """{block index: sha256 hex} for an iterable of frames in tick order."""
    out, cur, h = {}, None, None
    for fr in frames:
        b = fr["tick"] // BLOCK_TICKS
        if b != cur:
            if cur is not None:
                out[cur] = h.hexdigest()
            cur, h = b, hashlib.sha256()
        h.update(_line(fr).encode())
    if cur is not None:
        out[cur] = h.hexdigest()
    return [out[b] for b in sorted(out)]


def stream_frames(path):
    """The frames of a pretty-printed fight document, one at a time (a 226 MB file never sits in memory)."""
    buf = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if buf is None:
                if line == "    {\n":
                    buf = ["{\n"]
            else:
                buf.append(line)
                if line in ("    }\n", "    },\n"):
                    text = "".join(buf).rstrip().rstrip(",")
                    frame = json.loads(text)
                    buf = None
                    if "units" in frame:   # the document's `violations` list has the same indent; it is not a frame
                        yield frame


# ---------------------------------------------------------------------------------------------- the carried-through checks (per tick)

ARRIVE_WU = 22.5          # R-099-04: 1.5 x collision radius 15, a formation slot and a flying unit alone
DRAFT_ARRIVE_SLACK = 5.0  # DRAFT-sidestep-arrive-slack (Westley's): wu a push may carry a unit away from the arrival radius between the check and the position the lab reads
DRAFT_STALL_TICKS = 200   # the spec's "no progress for 200 ticks" (spec.md Acceptance 3)
DRAFT_PROGRESS_WU = 1.0   # DRAFT-sidestep-progress-wu (Westley's): nearer its destination by more than this resets a unit's no-progress clock
DRAFT_SAMPLE_EVERY = 10   # DRAFT-sidestep-sample-ticks: the no-progress check is evaluated every 10th tick
PROBE_DIST, BLOCK_DIAMETER = 40.0, 30.0   # OM_STEERING_PROBE_DIST, 2 x collision radius: a path is "free" when the point 40 wu toward the destination has no other living unit within 30 wu


class CarriedThrough:
    """Two per-tick checks of "an attack-move is carried through" (DEC-movement-sidestep-2026-11-24; spec.md Acceptance 3), fed one tick at a time with every unit of the fight:
    `feed(tick, units)`, units = [{"id", "alive", "x", "y", "dest": (x, y) or None, "target": int}, ...].
      ended_short: a living unit that had a destination on the previous tick and has none now, holds no target, and stood farther than ARRIVE_WU + DRAFT_ARRIVE_SLACK from that destination
                   (an order ends by arrival, a new order, death or the pursuit and guard rules; not by being blocked). Entries (tick, id, distance, destination).
      stalled:     a living unit with a destination and no target, whose distance to the destination has not fallen by more than DRAFT_PROGRESS_WU for DRAFT_STALL_TICKS ticks while the
                   point 40 wu ahead toward the destination had no other living unit within 30 wu at every sampled tick of that time (a free path). Entries (tick, id, distance).
    Both lists empty is the rule held on every tick of the fight."""

    def __init__(self):
        self.prev, self.ref, self.ended_short, self.stalled = {}, {}, [], []

    def _free(self, u, units):
        d = math.hypot(u["dest"][0] - u["x"], u["dest"][1] - u["y"])
        if d <= 0.0:
            return True
        tx, ty = u["x"] + PROBE_DIST * (u["dest"][0] - u["x"]) / d, u["y"] + PROBE_DIST * (u["dest"][1] - u["y"]) / d
        return not any(o["alive"] and o["id"] != u["id"] and (o["x"] - tx) ** 2 + (o["y"] - ty) ** 2 < BLOCK_DIAMETER ** 2 for o in units)

    def feed(self, tick, units):
        cur = {}
        for u in units:
            if not u["alive"]:
                self.prev.pop(u["id"], None)
                self.ref.pop(u["id"], None)
                continue
            cur[u["id"]] = u
            before = self.prev.get(u["id"])
            if before is not None and before["dest"] is not None and u["dest"] is None and not u["target"]:
                d = math.hypot(before["dest"][0] - u["x"], before["dest"][1] - u["y"])
                if d > ARRIVE_WU + DRAFT_ARRIVE_SLACK:
                    self.ended_short.append((tick, u["id"], round(d, 2), before["dest"]))
            if u["dest"] is None or u["target"]:
                self.ref.pop(u["id"], None)
                continue
            d = math.hypot(u["dest"][0] - u["x"], u["dest"][1] - u["y"])
            ref = self.ref.get(u["id"])
            if ref is None or ref[2] != u["dest"] or d < ref[1] - DRAFT_PROGRESS_WU:
                self.ref[u["id"]] = (tick, d, u["dest"])
            elif tick % DRAFT_SAMPLE_EVERY == 0:
                if not self._free(u, units):
                    self.ref[u["id"]] = (tick, d, u["dest"])      # blocked: the clock restarts; a free path must hold for the whole window
                elif tick - ref[0] >= DRAFT_STALL_TICKS:
                    self.stalled.append((tick, u["id"], round(d, 2)))
                    self.ref[u["id"]] = (tick, d, u["dest"])
        self.prev = cur


def main(argv):
    for p in argv:
        print(p)
        for i, d in enumerate(block_hashes(stream_frames(p))):
            print('    "%s",  # block %d' % (d, i))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
