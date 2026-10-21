# ScanSect - 3D Insect Model & Morphometrics Viewer

Desktop application for inspecting 3D insect scans (`.obj`, `.ply`, `.stl`, `.vtk`, `.vtp`, `.vtu`), capturing specimen screenshots, and recording vertex-snapped morphometric measurements (`Distance`, `Angle`, and `Polyline`).

## Project Structure

- `GUI_CODE.py`: Main window (`ScanSectGUI`), unified instrument toolbar, 3D viewport interaction, and entry point (`python GUI_CODE.py`).
- `managers.py`: Background 3D model/texture loading (`ModelLoaderWorker`), mesh state (`MeshManager`), and separated screenshot/measurement archive persistence (`ArchiveManager`).
- `widgets.py`: Reusable viewport overlays, dialogs, SVG icons, and VTK trackball interactor style (`MeasurementDisplayWidget`, `MeasurementDetailWidget`, `ScreenshotPreviewDialog`, `LoadingOverlay`, `ScanSectUnifiedInteractorStyle`).
- `measurement_utils.py`: Pure geometry math (distance, polyline length, 3-point angle, unit conversion) and atomic JSON persistence with `.bak` recovery.
- `tests/test_measurement_utils.py`: Unit test suite for geometry calculations, unit scaling, atomic JSON backup recovery, and managers.

## Running ScanSect

```bash
pip install -r requirements.txt
python GUI_CODE.py
```

## Running Tests

```bash
python -B -m unittest discover -s tests -v
```

## Keyboard Shortcuts

- `Ctrl+O` / `Ctrl+Shift+O`: Open 3D model or texture
- `M`: Toggle measurement mode (`Shift + Left-Click` on the mesh to pick vertices while keeping camera navigation active)
- `Ctrl+Enter`: Finish active polyline measurement
- `Ctrl+Shift+C`: Capture screenshot
- `Ctrl+Shift+S`: Save current measurement to archive
