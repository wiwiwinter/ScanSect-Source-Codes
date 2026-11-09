# ScanSect

Thesis project: scan insect specimens with a turntable and camera, then inspect the 3D models and take measurements in a desktop GUI.

## Layout

| Folder | What it is |
|--------|-----------|
| `GUI_CODE/` | PySide6 + PyVista viewer for 3D models, screenshots and measurements. See [GUI_CODE/README.md](GUI_CODE/README.md). |
| `TURN_TABLE_CODE.ino/` | Arduino sketch that drives the turntable and sends `CAPTURE` over serial after each step. |
| `SCRIPT-CAMERA-SHUTTER-CLICK/` | `CAPTURE.py` listens for `CAPTURE` on serial and fires the camera with `gphoto2`. `CAPTURE_DEBUG.py` is the verbose version. |
| `SCRIPT-BATCH-COPY-AND-PASTE/` | `SCRIPT.py` moves images from the camera dump folder to the Lightroom watch folder (edit the two paths at the top). |

## Workflow

1. Flash `TURN_TABLE_CODE.ino` to the Arduino.
2. Run `CAPTURE.py` (needs `pyserial` and `gphoto2`; set the serial port in the file).
3. Move the photos with `SCRIPT.py`, then build the 3D model in your photogrammetry tool.
4. Open the model in the GUI:

```bash
cd GUI_CODE
pip install -r requirements.txt
python GUI_CODE.py
```

## Tests

```bash
cd GUI_CODE
python -B -m unittest discover -s tests -v
```

Runtime data (`recent_models.json`, `ScanSect_Archive/`) is created per user and is not tracked by git.
