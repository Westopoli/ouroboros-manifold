# Blender — Separate Wheels from Artillery Mesh

> After importing your Sloyd GLB. Goal: wheels become child objects you can rotate in Godot.

## 1. Select the artillery mesh
- Left-click the artillery model in the viewport

## 2. Enter Edit Mode
- Press **Tab** (or top-left dropdown: Object Mode → Edit Mode)

## 3. Switch to Face Select
- Press **3** on keyboard (not numpad), or click the third icon in the top-left header bar (looks like a small square face)

## 4. Select the wheel faces
- Click one face on a wheel
- **Ctrl+L** to select all connected faces (selects the whole wheel if it's a separate island of geometry — it usually is from Sloyd)
- If the wheel is fused to the frame: hold **Shift** and click faces manually to add to selection, or use **L** while hovering over connected wheel geometry
- To add the second wheel: hold **Shift**, hover over a face on the other wheel, press **L**

## 5. Separate the selection into its own object
- Press **P** → choose **Selection** from the popup menu
- The selected faces are now a new object. You'll see a new entry in the Outliner (top-right panel)

## 6. Exit Edit Mode
- Press **Tab**

## 7. Rename the objects
- In the Outliner (top-right panel), double-click each object name to rename:
  - Frame → `ballista_frame_t2` (or whatever tier)
  - Wheels → `ballista_wheels_t2`
- If you separated each wheel individually, name them `wheel_left` / `wheel_right`

## 8. Parent wheels to frame
- Left-click a wheel object to select it
- Then **Shift+left-click** the frame object (frame must be selected last — it becomes the parent, highlighted in a lighter orange)
- Press **Ctrl+P** → choose **Object (Keep Transform)**
- Repeat for the other wheel if separated individually

## 9. Set wheel origin to wheel center
- Select a wheel object
- Right-click → **Set Origin** → **Origin to Center of Mass (Volume)**
- If the wheel's center is off, you can instead: right-click → **Set Origin** → **Origin to 3D Cursor** after placing the cursor at the wheel's axle with **Shift+right-click**

## 10. Verify
- Select a wheel, press **R** then **Y** (or whatever the wheel's roll axis is) and move mouse to test rotation
- It should spin around its center. If it orbits weirdly, the origin is wrong — redo step 9
- **Ctrl+Z** to undo the test rotation

## 11. Export as usual
- File → Export → glTF 2.0 (.glb)
- In Godot, the frame imports as a MeshInstance3D with wheel MeshInstance3Ds as children
- Rotate wheel nodes in script or AnimationPlayer when the unit moves
