# Archive Rename Feature - Documentation

## 🎯 Overview

You can now rename archive items (screenshots, measurements) directly within the UI without losing any data or needing to re-save them.

## ✨ Features

### 📝 What You Can Rename
- **Screenshots** - Change the description to better describe what's shown
- **Measurements** - Update labels to be more descriptive
- **Any archive item** - All archive entries can be renamed

### 🔒 What Stays The Same
- ✅ File paths (screenshots/measurements files unchanged)
- ✅ Timestamps (original save time preserved)
- ✅ Measurement coordinates (exact positions unchanged)
- ✅ Model associations (linked model stays the same)
- ✅ File type (screenshot remains screenshot, etc.)

**Only the description changes!**

## 🎮 How to Use

### Method 1: Simple Rename

1. **Open Archive tab** (right panel)
2. **Select an item** from the list
3. **Click "Rename" button**
4. **Edit the description** in the dialog
5. **Click OK**
6. **Done!** Item is renamed and re-selected

### Method 2: Quick Edit

1. Select item in Archive
2. Click Rename
3. Description is pre-filled and selected
4. Just type new name (no need to clear first)
5. Press Enter or click OK

## 📋 Rename Dialog

```
┌─────────────────────────────────────────┐
│ Rename Screenshot                       │
├─────────────────────────────────────────┤
│ Rename Screenshot from 2025-12-17 14:30 │
│                                         │
│ Current: Top view of wing               │
│                                         │
│ New description:                        │
│ ┌─────────────────────────────────────┐ │
│ │ Top view of wing                    │ │ ← Pre-filled, selected
│ └─────────────────────────────────────┘ │
│                                         │
│              [OK]  [Cancel]             │
└─────────────────────────────────────────┘
```

## ✅ Features

### Smart Input
- **Pre-filled** - Current description is already there
- **Auto-selected** - Just start typing to replace
- **Empty check** - Can't save empty description
- **No-change detection** - Doesn't save if nothing changed

### Visual Feedback
- ✅ Status bar shows: `Renamed: 'old name' → 'new name'`
- ✅ List refreshes automatically
- ✅ Renamed item stays selected
- ✅ Clear success indication

### Error Handling
- ⚠️ Warns if description is empty
- ⚠️ Shows error if save fails
- 🔄 Doesn't break archive if error occurs

## 🎯 Use Cases

### 1. Better Organization
**Before:** `Screenshot - 2025-12-17 14:30:45`
**After:** `Wing span - dorsal view - specimen A`

### 2. Fix Typos
**Before:** `Wing mesurement` (typo)
**After:** `Wing measurement` (fixed)

### 3. Add Context
**Before:** `Measurement`
**After:** `Antenna length - left side - specimen B`

### 4. Standardize Names
Rename multiple items to follow a consistent naming scheme:
- `Specimen A - Wing - Dorsal`
- `Specimen A - Wing - Ventral`
- `Specimen A - Antenna - Left`

### 5. Update After Analysis
**Initial:** `Quick test measurement`
**Later:** `Final wing span - published data`

## 🔧 Technical Details

### What Gets Updated
```json
{
  "timestamp": "2025-12-17 14:30:45",  // ← Unchanged
  "type": "Screenshot",                 // ← Unchanged
  "description": "NEW NAME HERE",       // ← CHANGED
  "file_path": "path/to/file.png",     // ← Unchanged
  "model_name": "model.obj",            // ← Unchanged
  // ... all other fields unchanged
}
```

### Archive Metadata
- Updates `archive_metadata.json`
- Preserves all other fields
- Maintains data integrity
- No file copying or moving

### Files Affected
- ✅ `archive_metadata.json` - Description updated
- ❌ Screenshot files - Not renamed or moved
- ❌ Measurement text files - Content unchanged
- ❌ Model files - Not affected

## 💡 Best Practices

### 1. Use Descriptive Names
**Good:**
- `Wing span - male specimen - trial 3`
- `Antenna measurement - right side`
- `Dorsal view - high resolution`

**Not as useful:**
- `Test 1`
- `Screenshot`
- `Measurement`

### 2. Include Context
Add information that will help you later:
- Specimen identifier
- Body part measured
- View angle
- Trial number
- Date (if not using timestamp)

### 3. Consistent Format
Choose a format and stick to it:
- `[Specimen] - [Part] - [Detail]`
- `[Date] - [Type] - [Notes]`
- `[Project] - [Item] - [Status]`

### 4. Rename Soon After Creation
Don't wait - rename while you remember the context!

## 🔄 Workflow Example

### Research Workflow

```
1. Load model → Take screenshot → Save as "Screenshot"
2. Immediately rename: "Specimen_001 - Dorsal - Overview"

3. Create measurement → Save as "Measurement"  
4. Immediately rename: "Specimen_001 - Wing Span"

5. Later analysis...
6. Rename: "Specimen_001 - Wing Span - Published Figure 3"
```

### Batch Organization

```
Load old archive with generic names:
  - Screenshot - 2025-12-15 10:30
  - Screenshot - 2025-12-15 10:35
  - Screenshot - 2025-12-15 10:40

Rename all systematically:
  - Species A - Dorsal view
  - Species A - Ventral view  
  - Species A - Lateral view
```

## ⚡ Keyboard Tips

1. **Select item** with ↑↓ arrow keys
2. **Click Rename** or press Alt+R (if shortcut set)
3. **Type new name** (old text is selected)
4. **Press Enter** to confirm
5. **Repeat** for next item

## 🚨 Important Notes

### ✅ Safe Operations
- Renaming is **non-destructive**
- Original files are **not modified**
- Can rename multiple times
- Can undo by renaming back
- Archive data remains valid

### ⚠️ Limitations
- Cannot rename the actual files (screenshots/measurements)
- Only changes the description in archive list
- File names remain as originally saved
- Doesn't affect file contents

### 💡 Why Only Description?
- **File integrity** - Don't break references
- **Simplicity** - Just metadata change
- **Safety** - No risk of file corruption
- **Speed** - Instant rename

## 🎬 Complete Example

### Scenario: Documenting Multiple Specimens

```
Day 1: Field Collection
  Save: "Screenshot - 2025-12-15 09:00"
  Rename: "Field_Specimen_A - Initial capture"

Day 2: Lab Analysis  
  Save: "Measurement - 2025-12-16 14:30"
  Rename: "Specimen_A - Wing length - preliminary"

Day 3: Detailed Study
  Load old measurement
  Rename: "Specimen_A - Wing length - verified data"

Week Later: Publication
  Rename: "Figure_2A - Wing morphology - final"
```

## 📊 Archive Organization Tips

### Before Rename:
```
[2025-12-15 09:00] Screenshot: Screenshot - 2025-12-15 09:00
[2025-12-15 09:15] Measurement: Measurement - 2025-12-15 09:15
[2025-12-15 10:30] Screenshot: Screenshot - 2025-12-15 10:30
```

### After Rename:
```
[2025-12-15 09:00] Screenshot: Beetle A - Dorsal overview
[2025-12-15 09:15] Measurement: Beetle A - Body length
[2025-12-15 10:30] Screenshot: Beetle A - Wing detail closeup
```

Much easier to find what you need! 🎯

## ✨ Summary

- 🎯 **Quick**: Select → Rename → Done
- 🔒 **Safe**: Only description changes
- 💾 **Persistent**: Saves to archive metadata
- 🔄 **Reversible**: Rename again anytime
- 📝 **Intuitive**: Simple dialog interface
- ✅ **Smart**: Pre-filled, validated input

**Perfect for keeping your archive organized!** 📁✨
