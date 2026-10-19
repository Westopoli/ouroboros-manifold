"""summary.json beside a batch csv: per cell and enemy size the outcome counts and means, for the Architect's chart.
Cell sentences say what the cell varies; the status and break-even are the lab's own printed values."""
import json

MIRROR = "naive against naive: both sides play the same, so the cell is a mirror control"


def varies(batch, c):
    """One plain sentence on what this cell varies."""
    n, lab = batch, c.label
    if c.build is None:
        return "not expressed: " + (c.note or "no play built")
    if n == "landscape":
        if lab.startswith("tall_cover"):
            return ("16 attackers in a blob against guarding defenders behind a wall of nine height-3 cover discs, "
                    + ("the attackers on layer 3 reaching 3 layers down" if lab.endswith("counter") else "all on layer 0"))
        kind, rest = lab.split(":", 1)
        return ("map '%s' (see the scene text for where its blocked ground and cover lie); 16 attackers playing %s "
                "against guarding defenders in a blob; all on layer 0" % (kind, rest.split("_v_")[0]))
    if n == "enemy_position":
        return {"blob": MIRROR + " (control)", "bait": "a quarter of the units run in as bait, the rest wait, then the whole side attacks at tick 100",
                "ambush": "the whole side stands still until tick 100, then attack-moves",
                "fall_back": "the side advances, falls back to its start at tick 100, then attack-moves at tick 200"}.get(lab, lab)
    if n == "combinations":
        if lab == "counter:S2":
            return "a 3-wide column (draft counter) against a line"
        subset = lab.split(":", 1)[1]
        return "no skill: a blob against a blob (control)" if subset == "none" else "skill %s played by side 0 against a blob" % subset
    return lab


def _cell_summary(result):
    sizes = {}
    for cell in result.cells:
        fights = cell.fights
        k = len(fights)
        count = lambda o: sum(f.outcome == o for f in fights)
        mean = lambda xs: round(sum(xs) / len(xs), 4) if xs else None
        sizes[str(cell.enemy_heads)] = {
            "fights": k, "won": count("side0"), "lost": count("side1"),
            "cap": count("cap"), "draw": count("draw"), "mean_margin": mean([f.margin for f in fights]),
            "firing_unit_seconds_side0": mean([f.firing_unit_seconds[0] for f in fights]),
            "firing_unit_seconds_side1": mean([f.firing_unit_seconds[1] for f in fights])}
    return {"break_even": ("no break-even in range" if result.beats is None
                           else "%d units beat %d, lose to %d" % (result.size, result.beats, result.loses_to)),
            "beats": result.beats, "loses_to": result.loses_to, "by_enemy_size": sizes}


def write(defn, scans, path, rule, reference_key="reference"):
    cells = []
    for c in defn.cells:
        entry = {"label": c.label, "status": c.status, "size": c.size, "enemy_from": c.enemy_from,
                 "enemy_to": c.enemy_to, "varies": varies(defn.name, c)}
        if c.build is None:
            entry["not_expressed"] = c.note
        else:
            entry["variants"] = {v: _cell_summary(scans[(c.label, v)]) for v, _ in defn.variants}
            if c.reference is not None:
                entry["reference_naive_v_naive"] = _cell_summary(scans[(c.label, reference_key)])
        cells.append(entry)
    path.write_text(json.dumps({"batch": defn.name, "rule": rule, "cells": cells}, separators=(",", ":")), encoding="utf-8")
