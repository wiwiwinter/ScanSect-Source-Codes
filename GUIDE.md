# ScanSect Build Guide

Step-by-step guide to recreate ScanSect: a low-cost turntable rig that photographs an insect specimen from 72 angles, plus a desktop app to view the resulting 3D model and measure it.

```
Arduino turntable ──serial──> capture script ──gphoto2──> camera
                                                             │ photos
                                                             ▼
                                   photogrammetry software (3D model)
                                                             │ .obj / .ply / .stl
                                                             ▼
                                         ScanSect GUI (view, screenshot, measure)
```

## 1. Parts

| Part | Notes |
|------|-------|
| Arduino (Uno/Mega class, 5 V) | Runs `TURN_TABLE_CODE.ino` |
| Stepper motor, 1.8° (200 steps/rev) + step/dir driver (A4988/DRV8825 type) | Driver uses STEP, DIR and ENABLE pins |
| 16x2 LCD (HD44780, parallel) | Shows angle and status |
| 3 push buttons | Reset, Pause, Resume |
| Turntable platform with a gear/pulley ratio of 4:1 | See the note in section 3 |
| Camera supported by gphoto2 (the scripts look for `.ARW`/`.JPG`, so a Sony camera was used) | USB cable to the PC |
| Tripod, even diffuse lighting, plain background | Needed for good photogrammetry |
| PC (Windows or Linux/WSL) | Python 3.10+ |

## 2. Wiring (from the sketch)

| Function | Arduino pin |
|----------|-------------|
| Stepper DIR / STEP / ENABLE | 9 / 10 / 11 |
| Reset button | 4 (to GND, uses internal pull-up) |
| Pause button | 3 (to GND) |
| Resume button | 2 (to GND) |
| LCD RS / EN | 13 / 12 |
| LCD D4 / D5 / D6 / D7 | 8 / 7 / 6 / 5 |

Power the stepper driver from its own supply and share ground with the Arduino.

## 3. Flash the turntable

1. Install the Arduino IDE and the **AccelStepper** library (Library Manager). `EEPROM` and `LiquidCrystal` ship with the IDE.
2. Open `TURN_TABLE_CODE.ino/TURN_TABLE_CODE.ino`. If the IDE complains about the folder name, rename the folder to `TURN_TABLE_CODE`.
3. Select your board and port, then upload.

How it behaves:
- It turns **5° per step**, 72 steps = 360°. The step count is `200 / 1.8 × (5 / 20)`, which assumes a 4:1 reduction (`20` in the formula). Change that ratio in the sketch if your mechanics differ.
- After each move it prints `READY` over serial (115200 baud) and **waits for `DONE`** before continuing.
- At 360° it returns to home and prints `RESET_COMPLETE`.
- Position is saved to EEPROM every 5 s so it can return home after a power cycle.
- Buttons: Pause stops, Resume continues (or restarts after a full rotation), Reset homes the table.

## 4. Set up the capture PC

```bash
pip install pyserial
```

Install **gphoto2** (Linux: `sudo apt install gphoto2`; on Windows use WSL and attach the camera and Arduino with `usbipd`). Check the camera is seen:

```bash
gphoto2 --auto-detect
gphoto2 --capture-image
```

## 5. Take the photos

Scripts are in `SCRIPT-CAMERA-SHUTTER-CLICK/`.

> [!IMPORTANT]
> The scripts do not match each other yet. The sketch speaks `READY` / `DONE`.
> `CAPTURE_DEBUG.py` follows that protocol, so **use it as your starting point**.
> `CAPTURE.py` is an older version: it waits for the text `CAPTURE`, never sends `DONE`, and stops after 61 photos (the sketch does 72). Update it before relying on it.

1. Open the script and set the serial port (`/dev/ttyUSB0`, `/dev/ttyACM0` or `COM3`) and the download folder.
2. Place the specimen at the center of the turntable, lock camera focus, exposure and white balance.
3. Run the script, then press Resume on the rig. For each of the 72 positions: Arduino sends `READY` → script captures with `gphoto2` → script sends `DONE` → table turns.

`CAPTURE_DEBUG.py` stops after 3 captures on purpose (`while captures_done < 3`). Raise that to 72 for a real scan.

Optional: `SCRIPT-BATCH-COPY-AND-PASTE/SCRIPT.py` moves images from the camera dump folder into a watch folder (for example Lightroom auto-import). Edit the two paths at the top.

## 6. Build the 3D model

Edit the photos if needed (same settings for all), then use any photogrammetry program that exports `.obj`, `.ply`, `.stl`, `.vtk`, `.vtp` or `.vtu`, with an optional texture image. Import the 72 photos, align, build the mesh and texture, and export.

> The exact photogrammetry software and settings used in the thesis are not recorded in this repository. See the thesis document for them and add them here.

## 7. Run the GUI

```bash
cd GUI_CODE
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python GUI_CODE.py
```

Requirements: PySide6, pyvista, pyvistaqt, vtk, numpy.

### Using it

1. `Ctrl+O` opens a model; `Ctrl+Shift+O` loads a texture.
2. Rotate, pan and zoom with the toolbar tools or the mouse.
3. Press `M` for measurement mode. **Shift + Left-click** on the mesh to pick vertices.
   - Tools: Distance, Angle, Polyline (`Ctrl+Enter` finishes a polyline).
4. Set the scale so measurements are real. The app starts in mm with a scale of 1.0, so the model must be scaled against a known reference (a ruler or scale bar photographed with the specimen).
5. `Ctrl+Shift+C` takes a screenshot; `Ctrl+Shift+S` saves the current measurement. Both go to `GUI_CODE/ScanSect_Archive/`, grouped by model name.

## 8. Check it works

```bash
cd GUI_CODE
python -B -m unittest discover -s tests -v
```

Expected: 6 tests, all OK.

## Troubleshooting

| Problem | Try |
|---------|-----|
| `gphoto2` says camera is busy | Close other camera software; unplug and replug; on Linux stop `gvfs-gphoto2-volume-monitor` |
| Serial port not found | Check Device Manager / `ls /dev/tty*`; only one program may hold the port |
| Table turns the wrong amount | Fix the gear ratio in `stepsPerMoveX` |
| Table never moves after the first stop | The script is not sending `DONE` (see section 5) |
| GUI won't start | Reinstall with `pip install -r requirements.txt`; use a supported Python version for PySide6/vtk |
| Measurements look too big/small | Scale the model to a real reference (step 4) |
