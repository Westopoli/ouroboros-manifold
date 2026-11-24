"""Run a card's checks over a fight file; one row per check. Missing, unreadable or empty input gives FAIL rows, never PASS."""
import json
from pathlib import Path

from scripts.look import report, state_checks as sc

# check name -> (fight, params) -> result; params keys are the card's DRAFT- names
STATE = {
    "no_stack": lambda f, p: sc.check_overlap(f, p.get("DRAFT-radius", sc.DRAFT_LOOK_RADIUS), p.get("DRAFT-max-ticks", sc.DRAFT_LOOK_MAX_TICKS)),
    "unit_in_wall": lambda f, p: sc.check_unit_in_wall(f),
    "not_frozen": lambda f, p: sc.check_frozen(f, p.get("DRAFT-frozen-window", sc.DRAFT_LOOK_FROZEN_WINDOW)),
    "blue_wins": lambda f, p: sc.check_winner(f, p.get("DRAFT-expected-winner", "A")),
}


def _row(req, ch, verdict, numbers, tick=0):
    return {"req": req, "check": ch["name"], "kind": ch["kind"], "verdict": verdict, "numbers": numbers, "crop": None, "frame": None, "tick": tick}


def run_card(card, fight_path):
    req = ", ".join(card["requirements"])
    try:
        fight = json.loads(Path(fight_path).read_text())
        if not isinstance(fight, dict) or not fight.get("frames"):
            raise ValueError("no frames")
        err = None
    except (OSError, ValueError) as e:
        fight, err = None, str(e)
    rows = []
    for ch in card["checks"]:
        if err is not None:
            rows.append(_row(req, ch, "FAIL", {"reason": err}))
        elif ch["kind"] != "state" or ch["name"] not in STATE:
            rows.append(_row(req, ch, "FAIL", {"reason": f"core cannot run {ch['kind']} check {ch['name']!r}"}))
        else:
            try:
                r = STATE[ch["name"]](fight, ch.get("params", {}))
            except (KeyError, TypeError, ValueError) as e:
                r = {"verdict": "FAIL", "numbers": {"reason": f"bad fight data: {e!r}"}, "tick": 0}
            rows.append(_row(req, ch, r["verdict"], r["numbers"], r["tick"]))
    return rows


def run(cards, fight_path, out_dir):
    rows = [r for c in cards for r in run_card(c, fight_path)]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "rows.json").write_text(json.dumps(rows, indent=1, sort_keys=True))
    (out / "report.html").write_text(report.render(rows))
    return rows
