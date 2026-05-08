## Minimal InputRouter stub for the B2 isolated test scene.
## unit_renderer.gd reads two fields off its `../InputRouter` sibling:
## `active_layer` (int) and `selected_uids` (Array[int]). The real
## input_router.gd handles selection, control groups, and command dispatch
## — none of which we need in this isolated visual harness.
## See also: scenes/debug/test_squad_impact_origins.gd
extends Node2D

var active_layer: int = 0
var selected_uids: Array[int] = []
