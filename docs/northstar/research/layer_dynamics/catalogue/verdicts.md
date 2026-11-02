# Catalogue verdicts (Westley)

One row per layout: `| id | verdict | feedback |`. Verdicts: the words `review.py` accepts. Applied with `python3 scripts/skilllab/catalogue/review.py apply --dir docs/northstar/research/layer_dynamics/catalogue --verdicts <this file>`.

## Batch one, 2026-10-31 (12-layout sample; the whole batch is denied on the same defect)

Westley, on L-0001: "There is no chokepoint here, just units arranged in a surround. Chokepoint is a layout/landscape formation, not a unit formation. The formation in this screenshot is considered a surround, and if units were closer together (within shooting range if they aren't already, it appears that they're not) and the formation was not broken by movement forward (which it probably would be, units are too far apart for this test to effectively be considered testing a surround) based on only the formation red would be expected to win 10 out of 10 times. Qs for this one: The unit symbols aren't really visible from this far away, they all look roughly the same. I'd also like unit ranges visualized for me." On L-0028: "I don't think you looked at these screenshots before passing them to me. This is so far zoomed out that nothing is really discernable. I see far off units barely in the distance, but nothing that appears to be a city. Why are you showing 5 layers if we're starting with the ground era first which only ever has 1 layer that units can travel at any given point on the map? Where is the city referenced? I see no buildings or anything." Then: "Check all the screenshots after these ones."

The Architect checked all twelve on 2026-10-31: every picture is a flat green plane with two unit clusters and no landscape feature, because the layout format carries none (`situation` is a label and `landscape` a preset with bounds and a layer count; nothing in the file says where the choke, the city, the cover, the slope or the vantage is), so the shot scene had nothing to draw. The defect is the Architect's spec (H-025 round one), not the builder's. Denied as a set; round two is in `docs/stories/H-025.md`.

| id | verdict | feedback |
|---|---|---|
| L-0001 | deny | Westley: no chokepoint, a surround of units too far apart to hold; chokepoint is landscape, not formation; unit symbols unreadable at this distance; show unit ranges. |
| L-0004 | deny | No vantage drawn: three stacked planes on a flat field; a ground era has one walkable layer at any point (R-001-07), high ground is terrain, not a plane. |
| L-0007 | deny | No cover obstacles drawn; units unreadable at this distance. |
| L-0010 | deny | No objective drawn (no capture ring, no marker); two clusters on an empty field. |
| L-0013 | deny | No staging area drawn; two clusters on an empty field. |
| L-0016 | deny | No transit route or destination drawn. |
| L-0019 | deny | No flank route and no terrain; five stacked planes wash out a ground-era field; units barely visible. |
| L-0022 | deny | No hazard drawn; the ring of units stands around nothing. |
| L-0025 | deny | No slope or height bands drawn; three planes on a flat field. |
| L-0028 | deny | Westley: too far zoomed out, nothing discernable, no city, no buildings; five layers shown for a ground era that has one walkable layer at any point. |
| L-0031 | deny | No trap geometry drawn (nothing to spring it); clusters on an empty field. |
| L-0034 | deny | Open field is the one situation the flat plane fits, but the units are unreadable at this distance and no ranges are shown; redo with round two's camera and glyphs. |

The other 24 batch-one layouts (denied as a set, same defect):

| id | verdict | feedback |
|---|---|---|
| L-0002 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0003 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0005 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0006 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0008 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0009 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0011 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0012 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0014 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0015 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0017 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0018 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0020 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0021 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0023 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0024 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0026 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0027 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0029 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0030 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0032 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0033 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0035 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0036 | deny | Batch one denied as a set (DEC-catalogue-batch1-denied-2026-10-31): no landscape geometry in the layout format. |
| L-0037 | A | Westley 2026-11-01: "chokepoint: approved" |
| L-0038 | deny | Westley 2026-11-01: "vantage: is that a single layer? 2x the height on a single layer if that's the case. Show me an updated one." |
| L-0039 | hold | Westley 2026-11-01: "cover: the placeholders don't really break LOS, do the units see each other through the cracks? Cover can also change size, so what size is this showing?" |
| L-0040 | hold | Westley 2026-11-01: "objective: what exactly am I approving/disapproving for this one?" |
| L-0041 | hold | Westley 2026-11-01: "staging: same Q for this one, what exactly am I approving/disapproving? Next time you ask for screenshots, pair the screenshots with a doc that describes what approve/disapproval means for each individual screenshot." |
| L-0042 | hold | Westley 2026-11-01: "transit: same Q with this one." |
| L-0043 | deny | Westley 2026-11-01: "flank: a flank comes from behind usually, not from the side, and splitting the forces would lead to a wider available area of attack." |
| L-0044 | hold | Westley 2026-11-01: "hazard_anchor: same Q for this one." |
| L-0045 | hold | Westley 2026-11-01: "slope: Same Q as vantage, is that a single layer change?" |
| L-0046 | deny | Westley 2026-11-01: "city: the city is too uniform, unless what I'm approving/disapproving is very specific. Can units travel between the buildings?" |
| L-0047 | deny | Westley 2026-11-01: "trap: blue would not put themselves in this situation, a trap is more like 'leading' an enemy force into a much more complicated situation, one where the trapping side has multiple attack points blocking a retreat, and has high ground or better vision on the enemy. What exactly was the point of this screenshot? What am I approving/disapproving?" |
| L-0048 | hold | Westley 2026-11-01: "Same Q for open_field." |
| L-0037 | redraw | Westley 2026-11-01 (amends A): "chokepoint: blue needs to be lined up flush as a 'sphere', in an arc, that maximize the number of units concurrently firing. They also need to have their range be close enough to the chokepoint such that enemy units coming *through* the chokepoint do not come *out* of it, and enemy units get stuck in the back when first row enemy units coming to the end of the chokepoint stop to shoot if not manually commanded to. Blue is expected to win 98% of the time." |
| L-0038 | redraw | Westley 2026-11-01: "vantage: same in terms of an arc for this one, blue should be spread out in an arc to maximize firing units, and be closer to the edge of the 'hill'. Blue is expected to win 98% of the time." |
| L-0039 | deny | Westley 2026-11-01: "cover: rejected, this position is technically worse for blue because they have less space to spread out units to get firing angles on red. Without being changed red is expected to win 75% of the time depending on where units stop (how much range both units have, I can't tell unless I see a fight)" |
| L-0040 | redraw | Westley 2026-11-01: "objective: both sides need to spread units out in arcs, I'd like red to have 2 groups of units come at two different angles, surrounding blue. Red would be expected to win 80% of the time." |
| L-0041 | out | Westley 2026-11-01: "staging: red has a much larger force, expected to win 98% of the time." and "This and staging seem like pointless layouts. Throw them out." |
| L-0042 | out | Westley 2026-11-01: "transit: what is this testing? This and staging seem like pointless layouts. Throw them out." |
| L-0043 | redraw | Westley 2026-11-01: "Flank route: do 2 different variants of this, 2 and 3 pronged surround, same size force for both sides, blue is expected to win 95% of the time." |
| L-0044 | hold | Westley 2026-11-01: "hazard anchor: what is a hazard anchor?" (answered: a map-generator seed point for interference density, R-114-03 and ALG-71, not a tactical situation; recommended out) |
| L-0045 | redraw | Westley 2026-11-01: "slope: spread out blue in an arc, blue expected to win 60% of the time." |
| L-0046 | redraw | Westley 2026-11-01: "city: Place blue inside the city, and many more buildings. Blue should have an arc on red when its forces enter the city, blue expected to win 75% of the time." |
| L-0044 | out | Westley 2026-11-01: "hazard anchor out for now" |
