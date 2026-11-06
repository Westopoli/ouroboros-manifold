## Assumptions made during leaf-03

- **Picture y direction**: y runs downward (JSON y = picture y / 20) — source: no source, spec fixes neither; tests accept both
- **District grid orientation**: `district[row][col]`, row = y band, col = x band, 8 by 8 equal cells of the canvas — source: spec JSON line "district [[int x8] x8]", fixture; test needs only corner cell (0,0)
- **Sidebar width / map-and-sidebar layout**: 260 px sidebar, 13 px lines, image grows taller than the map when the sidebar needs it — source: no source, tests say width is the renderer's
- **Label words**: base_home "keep", base_forward "forward camp", objective "objective", resource "prize", expansion "expansion", choke "choke", vantage "height" — source: spec criterion 8 word list; which of base_home/objective is "keep" is a guess
- **Sheet tile scale**: tile map at DRAFT_PX_WU x 2 (40 wu a pixel; 600 px for 24,000 wu) with a caption strip of canvas-px/8 (min 24 px) under it — source: no source, spec gives only "a map without the sidebar"
- **Sheet sides mode**: taken from the file names present (mode with most files; ties mirror, rotate, separate; none found: separate) — source: spec criterion 9 "layout_assault_s<N>_<sides>.json found in the directory"
- **Sheet frame/background**: sheet background equals the map ground colour; every tile carries a constant grey frame; pass or fail shows in the caption colour (green 6/6, red n/6) — source: test locates tiles by non-background content and compares gutter pixels between sheets
- **Unreadable (invalid JSON) seed file on a sheet**: treated like a missing one (labelled "missing" tile, exit 1); `map` on an unreadable file exits 1 — source: no source
- **Choke axis**: axis_k is a count of 15-degree steps, walls lie along the axis either side of a gap of `width`, `wall_span` long and `length` thick — source: spec JSON/Design ("axis in 15-degree steps"), choke fields
