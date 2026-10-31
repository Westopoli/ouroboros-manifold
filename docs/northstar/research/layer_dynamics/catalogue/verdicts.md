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
