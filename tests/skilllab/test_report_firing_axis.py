# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-19 (firing chart x axis)
"""The firing chart labels at most 8 ticks on its x axis, first and last always among them.

Labels are the numeric `muted` svg texts below the plot area (y > PY1); the "Tick" axis title is not numeric
and is ignored.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.report import PY1, _firing_svg  # noqa: E402

TEXT = re.compile(r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*class="muted"[^>]*>([^<]*)</text>')


def axis_labels(svg):
    """Numeric muted texts under the plot area, as ints, in document order."""
    out = []
    for _x, y, body in TEXT.findall(svg):
        if float(y) > PY1 and re.fullmatch(r"-?\d+", body.strip()):
            out.append(int(body))
    return out


def series(n, step=5):
    return [(i * step, i % 4, (i + 1) % 3) for i in range(n)]


def test_helper_counts_one_label_per_tick_on_a_hand_built_svg():
    """Positive control: a one-label-per-tick svg (the old style) is counted as 200 labels, so the cap check bites."""
    svg = "\n".join(f'<text x="{i}.000" y="{PY1 + 16}.000" text-anchor="middle" class="muted">{i * 5}</text>'
                    for i in range(200))
    assert len(axis_labels(svg)) == 200


def test_200_samples_give_at_most_eight_labels_with_first_and_last():
    s = series(200)
    labels = axis_labels(_firing_svg(s))
    ticks = [f[0] for f in s]
    assert 2 <= len(labels) <= 8
    assert labels[0] == ticks[0] and labels[-1] == ticks[-1]
    assert set(labels) <= set(ticks)
    assert labels == sorted(set(labels))


def test_a_few_samples_keep_every_label():
    s = series(3)
    assert axis_labels(_firing_svg(s)) == [0, 5, 10]


def test_eight_samples_keep_every_label_and_nine_are_capped():
    assert len(axis_labels(_firing_svg(series(8)))) == 8
    assert len(axis_labels(_firing_svg(series(9)))) <= 8


def test_one_sample_does_not_crash():
    svg = _firing_svg([(0, 1, 1)])
    assert svg.startswith("<svg")
    assert axis_labels(svg) in ([0], [])
