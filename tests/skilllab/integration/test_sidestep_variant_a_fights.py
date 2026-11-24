# Rule pins: DEC-movement-sidestep-2026-11-24, R-099-04, R-096-02, R-097-03
"""Movement-sidestep LS1, whole runs: the lab fights L-0054 and SIT-0106 (seed 1) reproduce variant A's frames, and an attack-move is carried through on every tick.

Rule words: DEC-movement-sidestep-2026-11-24 (docs/northstar/story_reviews/westley/decisions.md): "The movement rule is variant A of the 2026-11-24 comparison artifact ... 'the old
side-step' ... (1) an attack-moving unit never ends its order short because it is blocked ... (2) the steering probe is not blocked by a group mate or by an idle friend ... (3) a detour
keeps the side it was first taken on until the straight line to the aim is clear"; "The artifact shows SIT-0106 red wins 13:0 at tick 2301 and L-0054 red wins 17:0 at tick 6408 under A."
Spec: docs/northstar/plans/movement-sidestep-2026-11-24/spec.md Acceptance 1 to 3 ("Byte-identical fights ... Compare the frames (positions, hp, targets, orders)"; "Determinism: two runs,
identical bytes"; "The lab's carried-through check: no alive unit ends a fight with an active order, no progress for 200 ticks and a free path"). Engine-rules spec "Test architecture": whole
run, per tick, never a final-state check in place of a per-tick one.

How the A hashes were made (helper and recipe: tests/skilllab/sidestep_blocks.py): variant A's fight files (the `every 2` documents of the 2026-11-24 comparison,
~/Projects/om-wt/engine-rules-baseline/r6-compare/runs/A-l54/L-0054-s1-every2.fight.json, sha256 269a80b869259d6a15419109f0e7edf048bef623f9eb322886d3842df13dce0d per its .meta.json, and A-sit/L-0106-s1-every2.fight.json, sha256
a20a6c52b5ccce750cc3b35ce210a5df2d4b9d724df23e247d0c96b5ccbe7654) were
streamed frame by frame; per 100-tick block (tick // 100) the sha256 of each frame's line [tick, [[id, x, y, hp, target], ...]] was taken (`block_hashes`). The literals below are those digests: 65 blocks
for L-0054 (ticks 0 to 6408), 24 for SIT-0106 (0 to 2301). `hp` is the frame's hp and `target` the id the unit holds (null or an id); orders show as positions, as the document carries no order field.
The fights are run as the lab runs them (scripts/skilllab/arena/run.fight, sight off, 600 s cap, a frame every 2 ticks, the layout's own single attack-move per side at tick 0); SIT-0106 is converted to
L-0106 by scripts/skilllab/arena/situations.convert from docs/northstar/research/layer_dynamics/situations/SIT-0106-open_field.md (the conversion reproduces A's L-0106.toml byte for byte).

Units are the lab's flyers on a plain canvas (neither layout has ground features or movement = walk): the steering probe is the movement the fights exercise. Nothing is switched off.

Red today: the first block whose positions differ is reported (main's fights differ from A; on main L-0054 ends in an apart end at tick 10860, SIT-0106 ends differently too). Controls green today: the helper's hash
sees one changed number in exactly one block; the planted traces of the two carried-through checks fire and stay quiet as they should; the SIT-0106 fight is deterministic. The no-order-ends-short check is also green today on SIT-0106 (no give-up fires there) and red on L-0054 (57 orders); the no-stall check is green today on both.
"""
import copy
import sys
import tomllib
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for extra in (ROOT, HERE.parent):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

import sidestep_blocks as sb  # noqa: E402
from scripts.skilllab import invariants  # noqa: E402
from scripts.skilllab.arena import run, situations, snapshot  # noqa: E402

CATALOGUE = ROOT / "docs/northstar/research/layer_dynamics/catalogue"
SITUATIONS = ROOT / "docs/northstar/research/layer_dynamics/situations"
EVERY = 2
SEED = 1

L0054_A_BLOCKS = (
    "fc1eeb92b1b23582e38bab7ea471de17020c5966bc843f8c153afa273dbb0956",
    "16a898e465435d73f593ebdf628d0f24054fdf238103012465e934c4aed98dab",
    "35eece06a1970773f446ac2fe7860f835546a05821958cf9c99e3a0510fc1a21",
    "1d604e9f98cd92a68b7be5166ff09f5c1b63a8ce37a7488758aab8542cb29f48",
    "447dc1e5a8b1b5e053449e1789dee6f491149dfb77ec99848abb0059ba062f86",
    "4fa7187312d5e0c20e74851af9ed996aed24e542526e2dd5d9f030474e1bbe31",
    "b613e08cd3ef7234539a1a700c9e539a2bc5180b227b803d73e81f58012713e0",
    "91e8ceb6daa80c97e4996fc160977c1afc9fcef3aefde12518f878313deea489",
    "b0833cb22552010317e6aabc8050cedf17d77801fe3f1f1d04e2efdae4f92b30",
    "108a92a185ac6c708ed426189e509e5d9d5a543fca2f817209fe4237df94ac3d",
    "9daf11d440969991be038af8d3dece46e0fc7100445ad8fda08f880250e2ff75",
    "d8c2afd1d0f50dc9f051c827a9cf4ad015be3d3128ee98c258e01ff316c98ae4",
    "6f8afc8371d9c170cc626de881217f21ad2c8435d1b234f78c391e809450dfcb",
    "5a8594181c58a6de6034a8e10cc2e4e06e725117e4e7adc678dc915bbfc0bd1f",
    "c03818eb5ec68282c7896a1ce36a065fdf1143f77f5a520ad21882ae1c5ab10a",
    "e02970b4188fa4f7ba1ad3dd4620337ae65f9008730b8dbf60da0b5551f03128",
    "5bda159f45a80770553945f7f924f6c68d95b5bb24964c30ef10216f23ab584d",
    "e997070ea1a01fc12a8e447d4a18329910bde0f3cba57356f1a85c350257b739",
    "6bdefe75887954d8b07bdc80ddf5252facdae4221020da26389d45e6b8462525",
    "fa75a1075cf67afc21dcc73ba379644a6c946be43c19bf62335074fad668f7b7",
    "100d7527512d5bb373165f376c4f1c895a4626ea734b4e0da036b91fb8cfc92a",
    "b08b0b45434d57f3ab4c0db53e77eadce6d95bb2be5dfe195143ca63df12ce54",
    "566dd314a700784d506160ab19701533470421d85b29c58c7ca91b2572ee72bb",
    "62e8c056eb6e615615f6e412f0b6df97637b8f78da99c37c38b842b76a386949",
    "7a4b365b5f5e8be29ca5b61bf864f3b0b9a4f01fe228a896521b25cb9a65582c",
    "db48b81667eaed7516cbdadb63f214380a92489cdf1280cc473b752e871dc132",
    "820a2b4ac0eb1733faba9a08ed614cd137286c3f4f610975f1da0178a91ec813",
    "6d234e20980f7e5d3a7e130608e9bda22bc8526003f8a9f63812d687732fba64",
    "2ddfd3c440d5cb4917d8e491157526c51c51ddbeedb6c41f10d5b231fd4d8b44",
    "97aefb940d26883074a23ed86c1f3d1560bbbe5b99dc8a5906115b43b170cca1",
    "c147e8b082da3e4260a34c59f06aa319b8e309bd162fdc2b0e8d639a3b6980de",
    "ba4279252b9449bf23fe047acae1886ec505b3306e77a493a129736b803281d8",
    "27fac0ab28aeae908e1b24502f153533855d7e46e1c2836e3009606776b45da4",
    "47500cc5d9490ed113b09ffed3058a6272dd957a4158339840fb36745d31033a",
    "7fb1db45e65d3b5c54e448a0db99d0ea13673f552dd3aaee4f0af24b5a8106c7",
    "c1089230385cb21db6a4e758671069e0a50d8f79cf753eb918680c9b60b641f2",
    "08f873c4c1ca7d842b0745e26408d1259a7afca9ca364b0cca477a4d1ad16a00",
    "231ec50f875ec3b2cd96f31e9608590937431fc04c15811260502aec0f71ef50",
    "9411faec890535c5f05647e386a2d05e1aadf37079cc75aebd2e5096a2887ea2",
    "ff889a4064bbff07b7d47112ae3916242ddc581764dc0e47a2c8a878ace38ef7",
    "36587c94acf704724afbaea9d24b5300b7f3367637980a27c6ce64d0d0ab8898",
    "3f56765ce6ce7b093fec0299d51d1a338c2e6386ceb206bc116a41018c908f69",
    "204eb72c08c9adb9660ce01c75c090ed6f2000e3c19781fe2937466711e6b90b",
    "4dc7da3c14f6dc475087ada9020e2a949cd9c910ee319bfda8041557e74f35e9",
    "d9b3d18e51a85ba457732e237256474f033ed8dcaf2e057a42d96b51d86c362c",
    "853df46da13912fd3df1d2972296279589cf83ac2b6fa9ad0a393367ea83aaa7",
    "a3aba52860cc68728c192b0596ca0642039196bb6e7c8af1984ef3c2616cb45d",
    "b45473afba9afef62258df1cff75a3307a87a50550d4b82ba35c3e1da8cdddfa",
    "e31fb437949dc273d6076d9c9a91c5f9289dfaad73fc32dfa4fe437240b01ed9",
    "9f6a4d57d2c13d0ea25e92bc37cffcce1e835a928889ce06e98b74c9e75d1311",
    "cf2296c302b2bff19c21c23016af259a3845a086cf355e4b194066611a781650",
    "644d83b20ce4f10f29257774c8b4851c5afe12e93165e6e81ac572225c119b85",
    "a90b927d70c821a1d61ca3e605c5d6995d45e00bd4ee5e158b91493e92901143",
    "189513e89ea679e74ba8e1e1c4b0eff9c7bd5017da50c2b2b9022893f54b8dfe",
    "4caeee67da5c0aa94a2fa731edd77f957de15a4460958cc145192e60807decfd",
    "f6d5ddd8868ed81c935399e3466e38ca264623d412ee1c8ce9da41f674ccc379",
    "06783beb55843563125c1a28a23adc5b6ea2d3dc44a197d74fb2a80bd61a43a0",
    "3216c283a199fa8719f02eb1fa19989553e622e8880101f298f2588ba6e9e8a5",
    "2450888b6cb8dfae9ee82bed1a85d4693299dfe22d44b39b98b34d5a72938041",
    "f3b86dd902b0ed1811a20e9385a5ea440ff4dc01aec6f1c0b4f527ab46d03098",
    "d6d358802afcf644f8391d643d02b3845fdc3a168a94361ee506ea3dabf0b683",
    "57272700a29424995e6f137e2eb8dec2025ff567dde23a7c0c016827b7b4c5bb",
    "141932fb2d70f08d1eb0858c817f5df0dfd33043d106d7bc64f878ae9d4e7904",
    "72ead92876df9813e88755a7e1512250ef02e380bb05c3c8c5cb63c62c331471",
    "42856fae017fddc3d70526f93232fde024e51216b129a4b75021f869bfc1a3d4",
)

SIT0106_A_BLOCKS = (
    "6e0596104b25d6a08e82f19fefbecb13141f03b0e369d7a5de2de53f365d49d5",
    "7e831feb00dad97dcca3d4d154163fb4ce3526c316a5bc2a70f96bfa745504b1",
    "20252cd9607c1b0e743f213907a3cb067b58b9f8ea2ac07d4597814dade13691",
    "82a4573405a62598730dee88f44a3f039c703c5ad13dff68bd9324cbd71b77d7",
    "dd61ffaadb1536d0e86303abfd49633ffcf6efc359cfa74cebb01487572aae9e",
    "a0f509fe22775395ce56d27f59c72046962f4dcb91efac54810e918749e366a4",
    "b76698581a19716ecafd100e6020fe5f481d2586931f8f29ca5619e5cfa0c646",
    "ea9e4cf90f562ad2c2b4a643e61ecda0432054111ffa8253ab3613cf792c7b7a",
    "1ec3737f7a211eee11bba58b0548f1fb8f1c0323d04696e312724fc8ee223b93",
    "df32f69e072ca1ee36ebe24d30effe362b3e822a467334bcb7270fff51fc02d6",
    "f1ec1a7a1bf4d258530067a246fda899daeda91d13489004159455be04a95acc",
    "a0fd7a5880d606c6bbe45eb6dc6f4960c1a051358963c5a6681b7860bc4d8c07",
    "e91bec593e4710deb22487af1f5155921e54e8df511320fb1df471824a4fbccc",
    "d7c922e2717df1e9600c616ce6d48d2ab488fed6e4ea80e528aa7ef18d125990",
    "df25d5f590f43e1c89297897084380109f3495ae6fd048144edcefc0a194c126",
    "e5348cdfeb382b411265de61b3ee465035b629e3d6e0e67e6ac8fa8043d1e9fc",
    "b2ac92eae1c64be2dfd30983b2222057c727fa132dd8d32881875089530cf274",
    "3392c41c871233039e68e1e121ab6a89f77701b8858ab8af72b30b6e22608e69",
    "21c01819ef2b899edd355e17b68230e657fd52f515adf3068d64ad310257560b",
    "d90ed663d1835f6c3c148c9cbe3c7aa475d1c4cb273da344e3e70f4cc1270a89",
    "28c7b216fc6c80defc0d091e699a6bb01eb5a05ea1dbfc0be21749f2833208c5",
    "017856fe7c68b1af5597af23aa15fdbd3821e1bfa4eec84daeb252a3bfc8747a",
    "c0a17460af372f5bc1dab6452c361578c8194625e926207df8254c9a0ff11cf1",
    "870f55fa79124b1fe4d0473a24e3d0f209a33a61331b589e6b8d63561ce15bde",
)

A_FACTS = {   # r6-compare/out/*-A.facts.json
    "L-0054": {"ticks": 6408, "winner": "B", "survivors": [0, 17], "end": "wipe", "blocks": L0054_A_BLOCKS},
    "L-0106": {"ticks": 2301, "winner": "B", "survivors": [0, 13], "end": "wipe", "blocks": SIT0106_A_BLOCKS},
}

_CACHE = {}


def _layout(name, tmp_dir):
    if name == "L-0054":
        with open(CATALOGUE / "L-0054.toml", "rb") as f:
            return tomllib.load(f)
    src = Path(tmp_dir) / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "SIT-0106-open_field.md").write_text((SITUATIONS / "SIT-0106-open_field.md").read_text())
    lines, rejected = situations.convert(src, Path(tmp_dir) / "out", "L-0106")
    assert not rejected and lines == ["CONVERTED SIT-0106-open_field L-0106"], lines
    with open(Path(tmp_dir) / "out" / "L-0106.toml", "rb") as f:
        return tomllib.load(f)


def _units(engine, w, ids):
    out = []
    for u in ids:
        x, y = engine.unit_pos(w, u)
        out.append({"id": u, "alive": engine.unit_alive(w, u), "x": x, "y": y, "dest": engine.unit_destination(w, u), "target": engine.unit_target(w, u) or 0})
    return out


def fought(name, tmp_path_factory, again=False):
    """(frames by tick, last tick, end, CarriedThrough) of `name` fought as the lab fights it; the checks see every tick (a Monitor subclass, as test_engine_rules_f5_giveup does); cached per session."""
    key = (name, again)
    if key not in _CACHE:
        carried = sb.CarriedThrough()
        original = invariants.Monitor

        class Watch(original):
            def after_step(self):
                super().after_step()
                carried.feed(self.tick, _units(self.engine, self.w, self._ids))

        layout = _layout(name, tmp_path_factory.mktemp("sidestep_" + name))
        invariants.Monitor = Watch
        try:
            frames, last, end, _ = run.fight(layout, SEED, "off", snapshot.CAP_SECONDS, EVERY)
        finally:
            invariants.Monitor = original
        _CACHE[key] = (frames, last, end, carried)
    return _CACHE[key]


def _frames_list(frames):
    return [frames[t] for t in sorted(frames)]


# ---------------------------------------------------------------- the carried-through checks: positive controls on planted traces (green today)

def _u(i, x, y, dest=None, target=0, alive=True):
    return {"id": i, "alive": alive, "x": x, "y": y, "dest": dest, "target": target}


def test_DEC_movement_sidestep_control_the_stall_check_fires_on_a_unit_that_stands_with_a_free_path_and_not_on_one_that_walks_or_is_blocked():
    """Positive control of the 200-tick no-progress check, planted traces. Unit 1 stands 500 wu from its destination for 260 ticks with nothing near its path: flagged. Unit 2 walks in 2 wu a tick:
    not flagged. Unit 3 stands, but a living unit of the fight stands on the point 40 wu ahead of it: its path is not free, not flagged. Unit 4 stands with a target held: not flagged."""
    c = sb.CarriedThrough()
    for t in range(1, 261):
        c.feed(t, [_u(1, 1000.0, 1000.0, (1500.0, 1000.0)), _u(2, 100.0 + 2.0 * t, 3000.0, (3900.0, 3000.0)), _u(3, 1000.0, 2000.0, (1500.0, 2000.0)), _u(5, 1040.0, 2000.0),
                    _u(4, 1000.0, 500.0, (1500.0, 500.0), target=9)])
    assert [s[1] for s in c.stalled] == [1], c.stalled
    assert c.stalled[0][0] == 210 and c.stalled[0][2] == 500.0   # first sampled tick (every 10th) at which 200 ticks have passed since tick 1


def test_DEC_movement_sidestep_control_the_ended_short_check_fires_on_an_order_cleared_far_from_its_point_and_not_on_an_arrival_or_a_death():
    """Positive control of the order-ends-only-by-arrival check, planted traces: unit 1's destination vanishes 60 wu from it (the old give-up): flagged. Unit 2's vanishes 20 wu away (an arrival):
    not flagged. Unit 3 dies with its destination set: not flagged. Unit 4's vanishes while it holds a target (a pursuit hands its order over): not flagged."""
    c = sb.CarriedThrough()
    c.feed(1, [_u(1, 0.0, 0.0, (60.0, 0.0)), _u(2, 0.0, 100.0, (20.0, 100.0)), _u(3, 0.0, 200.0, (500.0, 200.0)), _u(4, 0.0, 300.0, (500.0, 300.0))])
    c.feed(2, [_u(1, 0.0, 0.0), _u(2, 0.0, 100.0), _u(3, 0.0, 200.0, alive=False), _u(4, 0.0, 300.0, target=7)])
    assert [e[1] for e in c.ended_short] == [1] and c.ended_short[0][2] == 60.0, c.ended_short


def test_DEC_movement_sidestep_control_the_block_hash_sees_one_changed_number_in_exactly_one_block():
    """Positive control of the byte comparison: the same frames hashed twice agree; one unit's x changed by 0.01 in one frame changes that block's hash and no other."""
    frames = [{"tick": t, "alive": [1, 1], "units": [{"id": 1, "x": 1.0 * t, "y": 2.0, "hp": 500.0, "target": None}, {"id": 2, "x": 3.0, "y": 4.0, "hp": 500.0, "target": 1}]} for t in range(0, 400, 2)]
    base = sb.block_hashes(frames)
    assert len(base) == 4 and base == sb.block_hashes(copy.deepcopy(frames))
    bent = copy.deepcopy(frames)
    bent[75]["units"][1]["x"] += 0.01      # tick 150: block 1
    other = sb.block_hashes(bent)
    assert [a != b for a, b in zip(base, other)] == [False, True, False, False]


# ---------------------------------------------------------------- the whole runs

@pytest.mark.parametrize("name", ["L-0054", "L-0106"])
def test_DEC_movement_sidestep_the_fight_reproduces_variant_a_frame_for_frame_in_every_100_tick_block(name, tmp_path_factory):
    """DEC-movement-sidestep-2026-11-24 / spec Acceptance 1: seed 1, one attack-move per side at tick 0, a frame every 2 ticks: the sha256 of every 100-tick block of (id, x, y, hp, target) equals variant
    A's. The first differing block is reported with its tick range. Red today: main's movement (give-up, 60 wu hold, group mates and idle friends blocking) leaves A's path at the first fight in which
    one of them acts."""
    frames, last, end, _ = fought(name, tmp_path_factory)
    want = A_FACTS[name]["blocks"]
    got = sb.block_hashes(_frames_list(frames))
    first = next((i for i in range(max(len(got), len(want))) if i >= len(got) or i >= len(want) or got[i] != want[i]), None)
    assert first is None, "%s: first block that differs from variant A is %d (ticks %d to %d); %d blocks recorded, %d wanted" % (name, first, first * 100, first * 100 + 99, len(got), len(want))


@pytest.mark.parametrize("name", ["L-0054", "L-0106"])
def test_DEC_movement_sidestep_the_fight_ends_where_variant_a_ends(name, tmp_path_factory):
    """Spec Acceptance 1 facts: L-0054 tick count 6408, winner B, 17 survivors; SIT-0106 (L-0106) tick count 2301, winner B, 13 survivors, both a wipe. (A's r6-compare/out/*-A.facts.json.)
    Red today: main ends L-0054 at tick 10860 apart with 14 and 22 alive."""
    frames, last, end, _ = fought(name, tmp_path_factory)
    a, b = frames[last]["alive"]
    want = A_FACTS[name]
    assert (last, end, [a, b]) == (want["ticks"], want["end"], want["survivors"]), "%s ended at tick %d (%s) with %d:%d alive; variant A: tick %d, %s, %s" % (name, last, end, a, b, want["ticks"], want["end"], want["survivors"])


@pytest.mark.parametrize("name", ["L-0054", "L-0106"])
def test_DEC_movement_sidestep_no_order_ends_short_on_any_tick_of_the_fight(name, tmp_path_factory):
    """DEC-movement-sidestep-2026-11-24 (1), per tick, R-099-04 / R-096-02 'an attack-move is not finished until the unit reaches its point': on every tick of the whole fight no living unit that held a
    destination the tick before and holds no target loses it farther than 22.5 wu (+5 slack, DRAFT-sidestep-arrive-slack) from that destination. Red today: the give-up clears orders 30 to 75 wu out."""
    _, last, _, carried = fought(name, tmp_path_factory)
    assert last > 1000, "premise: the fight ran %d ticks" % last
    assert not carried.ended_short, "%d orders ended short, the first %s (tick, unit, wu from its point, the point)" % (len(carried.ended_short), carried.ended_short[:5])


@pytest.mark.parametrize("name", ["L-0054", "L-0106"])
def test_DEC_movement_sidestep_no_unit_stands_200_ticks_with_an_order_a_free_path_and_no_progress(name, tmp_path_factory):
    """Spec Acceptance 3 (the lab's carried-through check) as a per-tick invariant: on no sampled tick (every 10th) does a living unit hold a destination and no target, have its distance to it not fall by
    more than 1 wu for 200 ticks, and have a free path (nothing within 30 wu of the point 40 wu toward its destination) throughout. The definition's numbers are DRAFT- in sidestep_blocks.py.
    Green today in its own right (the give-up clears the order, so a stalled unit has no order to carry) and the guard against an implementation that drops the give-up and leaves units standing."""
    _, last, _, carried = fought(name, tmp_path_factory)
    assert last > 1000
    assert not carried.stalled, "%d stalled units, the first %s (tick, unit, wu from its point)" % (len(carried.stalled), carried.stalled[:5])


def test_DEC_movement_sidestep_two_runs_of_sit_0106_give_identical_frames(tmp_path_factory):
    """Spec Acceptance 2: determinism, two runs of the fight, identical frames (every id, x, y, hp, target, alive, fired, facing of every frame: whole-document equality, not only the hashed fields).
    Green today: a control that the run is reproducible; it stays green after the change."""
    one = fought("L-0106", tmp_path_factory)
    two = fought("L-0106", tmp_path_factory, again=True)
    assert one[1] == two[1] and one[2] == two[2]
    assert _frames_list(one[0]) == _frames_list(two[0])
