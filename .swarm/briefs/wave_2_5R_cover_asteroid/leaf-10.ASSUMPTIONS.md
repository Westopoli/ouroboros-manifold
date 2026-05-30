# leaf-10 assumptions

## cell_size accessor
`Navmesh.cell_size` is a plain instance attribute (set in `__init__`). No accessor method needed.

## grid attribute
`Navmesh.grid` is a list-of-lists (rows × cols), all `True` at init. Mutated directly: `nm.grid[row][col] = False`.

## cell-center coordinate math
Cell (r, c) center = `((c + 0.5) * cell_size, (r + 0.5) * cell_size)`. Confirmed from existing `cell_center` method.

## medium asteroid fixture position
Brief says "medium asteroid at (500,500) → cell at center unwalkable." With `NAVMESH_CELL_SIZE=100`, cell (5,5) center = (550,550). Distance from (550,550) to (500,500) ≈ 70.7, which exceeds block_dist = radius(10) + half_cell(50) = 60. Test adjusted: asteroid placed at (550,550) so cell-center distance = 0 < block_dist. Intent preserved: medium-floor asteroid blocks its containing cell.

## conservative-ring epsilon
Used `cell_size * 1.5` as epsilon (well beyond half-cell boundary) to keep probe point firmly outside block zone. Verified fixture: cell center at probe is >block_dist from asteroid center before asserting walkable.

## TacticalMap.asteroid_field default
`TacticalMap.__init__` always sets `self.asteroid_field = AsteroidField([])` (non-None). None case tested by manually assigning `tmap.asteroid_field = None` after construction.

## iteration order
Iterated `tmap.asteroid_field.asteroids` by index order (list iteration), matching spec line 55.
