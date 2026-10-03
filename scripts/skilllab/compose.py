"""compose(skills): the five-slot rule (history section 7, rung K2). A skill fills its slot, every other slot is naive."""
from dataclasses import dataclass

from scripts.skilllab import skills as registry
from scripts.skilllab.asym import Side, asym_play

SLOTS = ("where", "shape", "layer", "info", "matchup")
SKILL_SLOT = {"S1": "where", "S2": "shape", "S3": "layer", "S4": "info", "S5": "matchup"}


@dataclass(frozen=True)
class Composition:
    skills: tuple
    slots: dict
    missing: tuple
    expressible: bool
    note: str

    def build(self, size):
        if not self.expressible:
            raise NotImplementedError(self.note)
        side = Side("skilled", skill=self.skills[0]) if self.skills else Side("blob")
        return asym_play(size, side, Side("blob"))


def _has_play(skill):
    try:
        registry.get(skill, "skilled")
    except ValueError:
        return False
    return True


def compose(skills):
    names = list(skills)
    for s in names:
        if s not in SKILL_SLOT:
            raise ValueError("unknown skill %r" % (s,))
    if len(set(names)) != len(names):
        raise ValueError("two skills never fill one slot: repeated skill in %r" % (names,))
    chosen = tuple(sorted(names))
    slots = {slot: None for slot in SLOTS}
    for s in chosen:
        slots[SKILL_SLOT[s]] = s
    missing = tuple(s for s in chosen if not _has_play(s))
    expressible = not missing and len(chosen) <= 1
    if expressible:
        note = ""
    elif missing:
        note = "no skilled play for " + ", ".join(missing)
    else:
        note = "slot plays do not exist yet to fill %s together" % ", ".join(SKILL_SLOT[s] for s in chosen)
    return Composition(chosen, slots, missing, expressible, note)
