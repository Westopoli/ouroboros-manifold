"""Fight margin by cost-weighted surviving hp (SPEC.md section 14.1)."""
from .. import ffi
from .cost import side_units


def margin(result, scn):
    rows = side_units(scn)
    alive, total = [0.0, 0.0], [0.0, 0.0]
    for r, u in zip(rows, result.unit):
        total[r["side"]] += r["cost"]
        if u["alive"]:
            alive[r["side"]] += r["cost"] * u["hp"] / r["hp0"]
    share = [alive[s] / total[s] if total[s] > 0 else 0.0 for s in (0, 1)]
    return share[0] - share[1]


_OUTCOME = {ffi.WIN_A: "win_A", ffi.WIN_B: "win_B", ffi.WIN_MUTUAL: "mutual",
            ffi.WIN_STALEMATE: "stalemate", ffi.WIN_CAP: "cap"}


def effective_margin(result, scn):
    outcome = _OUTCOME[result.winner]
    if outcome in ("stalemate", "cap"):
        return 0.0, outcome
    return margin(result, scn), outcome
