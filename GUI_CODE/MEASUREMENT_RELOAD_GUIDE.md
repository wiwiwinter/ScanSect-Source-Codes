# Measurement Reload Feature - Quick Guide

## 🎯 Overview
The measurement reload feature allows you to save measurements with their exact 3D positions and reload them later at the same location on your model.

## 📝 How to Save a Measurement

1. **Load your 3D model**
   - Use File > Open Model or load from Recent Models

2. **Create a measurement**
   - Click the "Measure" button in the toolbar
   - Click and drag the endpoints on your model to measure

3. **Save the measurement**
   - Click "Save Data" button in the toolbar
   - Enter a description (e.g., "Wing span", "Antenna length")
   - Click OK

4. **What gets saved:**
   - 3D coordinates of both measurement points
   - Distance value
   - Model file path (for automatic reloading)
   - Timestamp and description
   - Text file with detailed data
   - Entry in Archive with metadata

## 🔄 How to Reload a Measurement

### Method 1: From Archive Tab

1. **Open Archive tab** (right panel)
2. **Select a measurement** from the list
   - Measurements show type "Measurement" and distance
3. **Click "Load Measurement"** button
4. **If model isn't loaded:**
   - You'll be prompted to load the associated model
   - Click Yes to auto-load it
5. **Measurement appears** at exact same position!

### Method 2: Double-Click (opens text file)

- Double-click a measurement to open the saved text file
- View the detailed measurement data
- See coordinates and distance information

## ✨ Features

### Exact Position Restoration
- Saves 3D coordinates: `[x, y, z]` for both points
- Restores line widget to exact position
- No approximation - pixel-perfect accuracy

### Smart Model Loading
- Automatically detects associated model
- Prompts to load model if not currently open
- Handles missing model files gracefully

### Editable After Loading
- Loaded measurements are fully interactive
- Adjust endpoints as needed
- Save again with new description

### Backward Compatibility
- Old measurements (without coordinates) are preserved
- "Load Measurement" button only enables for new measurements
- Clear messaging if coordinates are missing

## 📊 Data Structure

### Archive Metadata (JSON)
```json
{
  "timestamp": "2025-12-17 14:30:45",
  "type": "Measurement",
  "description": "Wing span measurement",
  "file_path": "path/to/measurement_20251217_143045.txt",
  "model_name": "butterfly.obj",
  "model_path": "D:/Models/butterfly.obj",
  "distance": "12.34 mm",
  "point1": [10.5, 20.3, 5.7],
  "point2": [22.8, 20.1, 5.9]
}
```

### Text File Format
```
ScanSect Measurement Data
========================

Timestamp: 2025-12-17 14:30:45
Model: butterfly.obj
Description: Wing span measurement

Measurement:
  Point 1: (10.5000, 20.3000, 5.7000)
  Point 2: (22.8000, 20.1000, 5.9000)
  Distance: 12.3400 mm
```

## 🔧 Troubleshooting

### "Incomplete Data" Error
- **Cause**: Measurement saved with older version
- **Solution**: Create and save a new measurement

### Model Not Found
- **Cause**: Model file moved or deleted
- **Solution**: Manually load the correct model, then load measurement

### Measurement Not Visible
- **Cause**: Camera angle or zoom level
- **Solution**: Use reset camera or adjust view to see the measurement

### Wrong Model Loaded
- **Cause**: Different model than measurement was taken from
- **Solution**: The measurement will still load but may be positioned incorrectly

## 💡 Best Practices

1. **Use descriptive names**
   - "Left wing tip to tip" is better than "measurement 1"

2. **Keep models organized**
   - Don't move model files after taking measurements
   - Use consistent folder structure

3. **Save multiple measurements**
   - Create different measurements for different features
   - Each saves independently with its own coordinates

4. **Document your work**
   - Use descriptions to note what you're measuring
   - Include context in the description

5. **Regular backups**
   - Archive folder contains all your work
   - Back up the `ScanSect_Archive` folder regularly

## 📂 File Locations

- **Archive Folder**: `ScanSect_Archive/` (in same directory as GUI_CODE.py)
- **Metadata**: `ScanSect_Archive/archive_metadata.json`
- **Measurements**: `ScanSect_Archive/measurement_YYYYMMDD_HHMMSS.txt`
- **Screenshots**: `ScanSect_Archive/screenshot_YYYYMMDD_HHMMSS.png`

## 🎬 Example Workflow

1. Load model: `butterfly.obj`
2. Measure wing span → Save as "Wing span full"
3. Measure antenna → Save as "Left antenna length"
4. Close application
5. **Next day...**
6. Open application
7. Go to Archive tab
8. Select "Wing span full"
9. Click "Load Measurement"
10. Model loads, measurement appears!
11. Adjust if needed and save again

---

**Enjoy accurate, reproducible measurements!** 📏✨
