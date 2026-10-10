"""Story play S-193 (settlement density), lane E1 piece E1b. Fenced. The density field is sim-side; its view arrives with
E1k/E1p, so this play asserts only the qa_state key the settlement layer will publish. Red until then (key absent).
Draft key name: settlement_density_cells (count of cells with density > 0)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "K"))
from _k_common import moment, start_game, step_ticks, to_tactical  # noqa: E402


def test_s193_density_grows_in_play():
    g = start_game(seed=1)
    try:
        to_tactical(g)
        first = moment(g, "S193", "start")
        step_ticks(g, 600)
        later = moment(g, "S193", "after_30s")
        assert "settlement_density_cells" in later, "settlement layer does not publish settlement_density_cells yet"
        assert later["settlement_density_cells"] > first.get("settlement_density_cells", 0)
    finally:
        g.stop()
