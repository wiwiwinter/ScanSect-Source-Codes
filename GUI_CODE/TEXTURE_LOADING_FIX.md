# Texture Loading Fix - Documentation

## 🔧 Problem Identified

Your MTL files contain **absolute paths** to texture files that don't match the current file location:

**MTL File Says:**
```
map_Kd D:/THESIS/THESIS-MODELING/REALITY CAPTURE/MODELS/SCARABIDAE_SP1 - THESIS/FINAL_SCARABIDAE_-_THESIS_FINAL_MODEL_u1_v1_diffuse.png
```

**Current Location:**
```
D:/THESIS/THESIS-MODELING/REALITY CAPTURE/MODELS/TO BE TESTED/
```

This is a **very common issue** when:
- Files are moved to different folders
- Models are shared between computers
- Projects are reorganized
- MTL files contain hardcoded absolute paths

## ✅ Solution Implemented

I've added **intelligent texture path resolution** that automatically searches for textures in multiple locations:

### 🔍 Search Strategy

The application now searches for textures in this order:

1. **MTL File Path (Exact)**
   - Tries the exact path specified in the MTL file

2. **MTL File Name in Model Directory**
   - Takes just the filename from MTL and looks in the OBJ's folder
   - Example: If MTL says `D:/old/path/texture.png`, tries `./texture.png`

3. **Common Naming Patterns**
   - Searches for files matching: `<modelname>_diffuse.png`
   - Also tries: `<modelname>_u1_v1_diffuse.png`
   - And: `<modelname>_texture.png`, `<modelname>_color.png`, etc.
   - Checks multiple extensions: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`

4. **Texture Subfolders**
   - Searches in `textures/`, `Textures/`, `maps/`, `Maps/`, `images/`, `Images/`
   - With all naming patterns

5. **Parent Directory**
   - Searches one level up from the model folder
   - Useful for organized project structures

### 📊 For Your Specific Case

**Your Files:**
- Model: `THESIS_SCARABIDAE.obj`
- Texture: `FINAL_SCARABIDAE_-_THESIS_FINAL_MODEL_u1_v1_diffuse.png`
- MTL: `THESIS_SCARABIDAE.mtl`

**What the app will try (in order):**

1. ✗ `D:/THESIS/.../SCARABIDAE_SP1 - THESIS/FINAL_SCARABIDAE_-_THESIS_FINAL_MODEL_u1_v1_diffuse.png` (MTL absolute path)
2. ✓ `TO BE TESTED/FINAL_SCARABIDAE_-_THESIS_FINAL_MODEL_u1_v1_diffuse.png` ← **FOUND!**
3. (Doesn't need to check further)

## 🎯 Features Added

### 1. MTL File Parsing
```python
def parse_mtl_file(obj_file_path):
    # Reads the .mtl file
    # Extracts the map_Kd texture path
    # Returns the path specified in MTL
```

### 2. Intelligent Search
```python
def find_texture_file(obj_file_path, mtl_texture_path):
    # Searches in 40+ possible locations
    # Checks multiple naming patterns
    # Returns first valid texture found
```

### 3. Enhanced Feedback
- ✅ Console output shows search progress
- ✅ Success messages when texture is found
- ✅ Informative dialog if no texture found
- ✅ Error details if texture found but can't load

## 📝 Console Output Example

When you load a model, you'll see:

```
============================================================
Attempting to read model: D:/THESIS/.../THESIS_SCARABIDAE.obj
============================================================

--- Searching for Texture ---
MTL specifies texture: D:/THESIS/.../FINAL_SCARABIDAE_-_THESIS_FINAL_MODEL_u1_v1_diffuse.png
✓ Found texture: D:/THESIS/.../TO BE TESTED/FINAL_SCARABIDAE_-_THESIS_FINAL_MODEL_u1_v1_diffuse.png
Loading texture: ...
✓ Texture loaded successfully!

--- Post-Load Mesh Inspection ---
  mesh.textures exists. Type: <class 'dict'>
  mesh.textures is a dict. Keys: ['diffuse']
```

## 🚨 User Notifications

### If Texture Found ✓
- Silently loads and applies
- Status bar shows success
- Model displays with texture

### If Texture Not Found ✗
Shows informative dialog:
```
Could not find a texture file for this model.

Searched in:
• Same folder as model
• Parent folder
• Common texture subfolders
• Path from MTL file

You can load a texture manually using:
'Load Texture' button or File > Open Model/Texture
```

## 🔧 Troubleshooting

### Texture Still Not Loading?

**Check These:**

1. **File exists in model folder?**
   - Ensure PNG file is in same folder as OBJ/MTL

2. **Correct filename?**
   - Should match what's in the MTL file (at least the actual filename)

3. **Console output**
   - Open the application from terminal
   - Check which paths are being searched
   - See if texture is found but fails to load

4. **File permissions**
   - Ensure you can read the texture file

5. **File format**
   - PyVista supports: PNG, JPG, JPEG, BMP, TIFF
   - Check if it's a valid image file

### Common Issues Fixed:

✅ **Absolute paths in MTL files**
- Now extracts filename and searches locally

✅ **Models moved to different folders**
- Searches in current location, not MTL path

✅ **Different naming conventions**
- Checks 40+ possible filenames

✅ **Textures in subfolders**
- Automatically searches common texture folders

✅ **Missing MTL files**
- Gracefully handles missing MTL, still searches

## 📂 Recommended File Organization

### Option 1: Flat Structure (Simplest)
```
MyProject/
  ├── model.obj
  ├── model.mtl
  └── model_diffuse.png
```

### Option 2: Organized Structure
```
MyProject/
  ├── models/
  │   ├── model.obj
  │   └── model.mtl
  └── textures/
      └── model_diffuse.png
```

### Option 3: Per-Model Folders
```
MyProject/
  ├── ModelA/
  │   ├── model_a.obj
  │   ├── model_a.mtl
  │   └── model_a_diffuse.png
  └── ModelB/
      ├── model_b.obj
      ├── model_b.mtl
      └── model_b_diffuse.png
```

All three structures will work with the new texture loading!

## 🎓 Best Practices

1. **Keep textures with models**
   - Put texture files in same folder as OBJ/MTL

2. **Use relative paths in MTL**
   - Edit MTL to use: `map_Kd texture.png`
   - Instead of: `map_Kd D:/full/absolute/path/texture.png`

3. **Consistent naming**
   - Name texture: `modelname_diffuse.png`
   - Makes automatic finding easier

4. **Check console output**
   - Run from terminal to see search progress
   - Helpful for debugging

## 🔄 Migration Guide

If you have **many models with wrong MTL paths**:

### Quick Fix Script (PowerShell):
```powershell
# Run this in your model folder
Get-ChildItem *.mtl | ForEach-Object {
    $content = Get-Content $_.FullName
    $newContent = $content -replace 'map_Kd.*\\', 'map_Kd '
    $newContent | Set-Content $_.FullName
}
```

This removes absolute paths, making MTL files use relative paths.

## ✨ Summary

**Before:** ❌ Texture loading failed if MTL had wrong path
**After:** ✅ Intelligently searches 40+ locations automatically

**Your models should now load with textures automatically!** 🎉

---

**Test it now:**
1. Load `THESIS_SCARABIDAE.obj`
2. Texture should apply automatically
3. Check console for search details
4. Enjoy textured models! 🦗
