"""S-020 -- Same seed, same galaxy: the world RNG is actually seeded.

R-020-01. Change-protocol reason: CLAUDE.md "Determinism is a contract" and
the header's own world RNG contract (csrc/ouroboros_sim.h, "the world RNG
contract"), which states the seeding formula and the draw. M1 found (push
2026-09-22, .swarm/M1-CRITICAL-rng-never-seeded.md) that om_world_new stored
the seed and never derived rng_state/rng_inc from it, so every unforced draw
returned 0.0 for every seed, and that csrc/resolve.c's inline draw used a
different formula from csrc/agent.c and csrc/faction.c. These tests pin the
contract itself: seeding from om_world_new / om_world_set_seed, the PCG32
reference outputs, forced-draw precedence, and a positive control.

The stream is observed through om_faction_set with attack_confidence < 0
(R-032-01: "roll it once from the archetype's range with the world RNG").
That is a fixture call, not a tick step, so it needs no feature switch and
the E-02 world_factory (DRIFT only) reaches it. A Conqueror rolls
confidence = 2.0 + (6.0 - 2.0) * u, which the PCG32 reference below
reproduces exactly (one multiply and one add in IEEE double, same as the C).
No debug-only accessor was needed.
"""
import pytest

from conftest import OMArchetype, OMBug, force_draws, set_faction

MASK64 = (1 << 64) - 1
MASK32 = (1 << 32) - 1
PCG_MULT = 6364136223846793005
INC_XOR = 0xDA3E39CB94B95BDB
CONF_LO, CONF_HI = 2.0, 6.0


class Pcg32Reference:
    """The header's stated stream: O'Neill PCG-XSH-RR 64/32 (pcg32_random_r),
    seeded inc = (seed ^ 0xDA3E39CB94B95BDB) << 1 | 1; state = 0; step;
    state += seed; step. u = (next32() >> 5 * 2^26 + next32() >> 6) / 2^53."""

    def __init__(self, seed):
        seed &= MASK64
        self.inc = (((seed ^ INC_XOR) << 1) | 1) & MASK64
        self.state = 0
        self._step()
        self.state = (self.state + seed) & MASK64
        self._step()

    def _step(self):
        self.state = (self.state * PCG_MULT + self.inc) & MASK64

    def next32(self):
        old = self.state
        self._step()
        xorshifted = (((old >> 18) ^ old) >> 27) & MASK32
        rot = old >> 59
        return ((xorshifted >> rot) | (xorshifted << ((32 - rot) & 31))) & MASK32

    def uniform(self):
        a = self.next32() >> 5
        b = self.next32() >> 6
        return (a * 67108864.0 + b) * (1.0 / 9007199254740992.0)


def _draw_confidences(lib, w, n, first_id=0):
    out = []
    for i in range(n):
        set_faction(lib, w, first_id + i, OMArchetype.CONQUEROR, budget=100.0, tech=1.0, confidence=-1.0)
        out.append(lib.om_faction_confidence(w, first_id + i))
    return out


def _expected_confidences(seed, n):
    ref = Pcg32Reference(seed)
    return [CONF_LO + (CONF_HI - CONF_LO) * ref.uniform() for _ in range(n)]


def test_reference_first_draw_is_not_zero():
    """Fixture check for the tests below: the reference stream for seed 1
    must not itself start at 0.0, or the seed-1 pins would also pass against
    the never-seeded library."""
    for seed in (1, 2):
        u = Pcg32Reference(seed).uniform()
        assert 0.0 < u < 1.0, f"reference seed {seed} first draw {u!r}"
    assert Pcg32Reference(1).uniform() != Pcg32Reference(2).uniform()


def test_R_020_01_seed_1_and_seed_2_give_different_first_unforced_draws(lib, world_factory):
    w1 = world_factory(n_regions=1, seed=1)
    w2 = world_factory(n_regions=1, seed=2)
    c1 = _draw_confidences(lib, w1, 1)[0]
    c2 = _draw_confidences(lib, w2, 1)[0]
    assert c1 != c2, (
        f"seed 1 and seed 2 both rolled confidence {c1!r}: the world RNG is not "
        "derived from the seed (om_world_new never seeds rng_state/rng_inc)"
    )


def test_R_020_01_first_three_draws_for_seed_1_match_the_pcg32_reference(lib, world_factory):
    w = world_factory(n_regions=1, seed=1)
    got = _draw_confidences(lib, w, 3)
    expected = _expected_confidences(1, 3)
    for i, (g, e) in enumerate(zip(got, expected)):
        assert g.hex() == e.hex(), (
            f"draw {i} for seed 1: library gave {g!r} ({g.hex()}), header's PCG32 "
            f"contract gives {e!r} ({e.hex()})"
        )


def test_R_020_01_seed_2_matches_the_pcg32_reference_too(lib, world_factory):
    w = world_factory(n_regions=1, seed=2)
    got = _draw_confidences(lib, w, 3)
    expected = _expected_confidences(2, 3)
    assert [g.hex() for g in got] == [e.hex() for e in expected]


def test_R_020_01_same_seed_twice_gives_identical_draws(lib, world_factory):
    w1 = world_factory(n_regions=1, seed=7)
    w2 = world_factory(n_regions=1, seed=7)
    a = _draw_confidences(lib, w1, 5)
    b = _draw_confidences(lib, w2, 5)
    assert [x.hex() for x in a] == [x.hex() for x in b]
    assert len(set(x.hex() for x in a)) > 1, (
        f"five successive draws for seed 7 are all {a[0]!r}: the stream is not stepping"
    )


def test_R_020_01_om_world_set_seed_reseeds_to_the_same_stream_as_om_world_new(lib, world_factory):
    w = world_factory(n_regions=1, seed=99)
    _draw_confidences(lib, w, 2)
    lib.om_world_set_seed(w, 1)
    got = _draw_confidences(lib, w, 3, first_id=10)
    expected = _expected_confidences(1, 3)
    assert [g.hex() for g in got] == [e.hex() for e in expected], (
        "om_world_set_seed(1) after two draws does not restart the stream at "
        "the same place om_world_new(seed=1) starts it"
    )


def test_R_020_01_forced_draws_take_precedence_then_the_unforced_stream_resumes(lib, world_factory):
    w = world_factory(n_regions=1, seed=1)
    force_draws(lib, w, [0.5, 0.25])
    got = _draw_confidences(lib, w, 4)
    expected = _expected_confidences(1, 2)
    assert got[0] == CONF_LO + (CONF_HI - CONF_LO) * 0.5
    assert got[1] == CONF_LO + (CONF_HI - CONF_LO) * 0.25
    assert lib.om_rng_forced_remaining(w) == 0
    assert [g.hex() for g in got[2:]] == [e.hex() for e in expected], (
        "after the forced queue empties, the unforced stream must resume at its "
        "first value (forced draws do not consume the PCG32 stream)"
    )


def test_control_rng_unseeded_makes_seed_1_and_seed_2_draw_alike(dbg, dbg_world_factory):
    """OM_BUG_RNG_UNSEEDED (8): the stream is never derived from the seed, so
    every seed draws the same values -- the exact defect M1 found. Proves the
    seed-1-vs-seed-2 detector above can fail."""
    w1 = dbg_world_factory(n_regions=1, seed=1)
    w2 = dbg_world_factory(n_regions=1, seed=2)
    dbg.om_debug_inject(w1, OMBug.RNG_UNSEEDED)
    dbg.om_debug_inject(w2, OMBug.RNG_UNSEEDED)
    c1 = _draw_confidences(dbg, w1, 1)[0]
    c2 = _draw_confidences(dbg, w2, 1)[0]
    assert c1 == c2, (
        f"with OM_BUG_RNG_UNSEEDED injected, seed 1 rolled {c1!r} and seed 2 "
        f"rolled {c2!r}: the control did not disable seeding"
    )
    ref = CONF_LO + (CONF_HI - CONF_LO) * Pcg32Reference(1).uniform()
    assert c1.hex() != ref.hex(), (
        "with OM_BUG_RNG_UNSEEDED injected, seed 1 still matched the seeded reference"
    )
