# ScanSect GUI - Measurement Workflow Update

This README documents the recent measurement feature changes implemented in `GUI_CODE.py`.

## What Changed

### 1. Vertex-Snapped Measurement (Replaces Floating Ruler)
- Measurement now snaps to mesh vertices instead of using a free-drag floating line widget.
- Two picked vertices define a locked distance measurement.
- Visual feedback now shows:
  - marker sphere for point 1
  - marker sphere for point 2
  - a connecting measurement line
- Measurement values still update in:
  - status bar
  - viewport measurement overlay card
  - saved measurement metadata

### 2. Rotate/Pan/Zoom While Measuring
- Navigation remains available while Measure mode is active.
- Vertex picking is now intentionally triggered with:
  - **Shift + Left Click**
- This avoids locking orientation during measurement and supports normal camera interaction.

### 3. Save Behavior
- `Save Data` stays disabled until two valid snapped vertices are selected.
- After two points are selected, measurement can be archived normally.
- Loading archived measurements now restores the snapped points and measurement line visuals.

### 4. Model Reload Safety
- If a new model is loaded while Measure mode is active:
  - previous picked points are cleared
  - old measurement visuals are removed
  - measurement state is reset safely

## Backup Created Before Changes
- `BACKUP/GUI_CODE-V13.txt`

## Primary File Updated
- `GUI_CODE.py`

## How To Use
1. Open a model.
2. Click `Measure`.
3. Rotate/pan/zoom as needed (normal mouse controls).
4. Hold **Shift** and left-click first vertex.
5. Hold **Shift** and left-click second vertex.
6. Save measurement with `Save Data`.

## Suggested Commit Message
`feat(measurement): add vertex-snap measurement with Shift+click while keeping camera navigation`

## Suggested Commit Description
- Replace floating line widget measurement with vertex snapping
- Add locked marker/line visualization for picked vertices
- Keep navigation active during measurement mode
- Require Shift+LeftClick for vertex selection
- Reset measurement state safely on model reload
- Preserve archive save/load compatibility
