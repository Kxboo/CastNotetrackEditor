# CastNotetrackEditor
Notetrack Viewer and Editor for Blender

> **Disclaimer:** Tested on Blender 3.6 only.

---

## Installation

### (Option 1) Quick Update
Only `cast_notetrack_editor.py` and `__init__.py` need to be replaced.

### (Option 2)Clean Install
1. Download this repo as a zip
2. Open Blender
3. Go to **Edit → Preferences → Add-ons → Install**
4. Select the downloaded zip file

> If updating, it is recommended to uninstall the previous version first.

---

## (Option 3)Manual Install
Copy `cast_notetrack_editor.py` into your cast addon folder next to `__init__.py`, `cast.py`, `import_cast.py` and `export_cast.py`.

Then in `__init__.py` add the following if you didn't replace the file:

At the top:
```python
from . import cast_notetrack_editor
```

Inside `register()`:
```python
cast_notetrack_editor.register()
```

Inside `unregister()`:
```python
cast_notetrack_editor.unregister()
```

Full register and unregister example:
```python
def register():
    bpy.utils.register_class(ImportCast)
    bpy.utils.register_class(ExportCast)
    bpy.utils.register_class(CastProperties)
    bpy.utils.register_class(CastImportScenePanel)
    cast_notetrack_editor.register()
    bpy.types.TOPBAR_MT_file_import.append(menu_func_cast_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_cast_export)
    bpy.types.Scene.cast_properties = PointerProperty(type=CastProperties)
    if utilityIsVersionAtLeast(4, 1):
        bpy.utils.register_class(DragAndDropCast)

def unregister():
    bpy.utils.unregister_class(ImportCast)
    bpy.utils.unregister_class(ExportCast)
    bpy.utils.unregister_class(CastImportScenePanel)
    bpy.utils.unregister_class(CastProperties)
    cast_notetrack_editor.unregister()
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_cast_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_cast_export)
    del bpy.types.Scene.cast_properties
    if utilityIsVersionAtLeast(4, 1):
        bpy.utils.unregister_class(DragAndDropCast)
```

---

## How Notetracks Work in Cast
In the binary `.cast` format, notetracks live inside the Animation node as children of type NotificationTrack (identifier `0x6669746E`).

Each NotificationTrack has a name such as `end`, `loop_end`, `snd_...` or `xstring_...` and a list of frame numbers it fires on. One name can fire on multiple frames. Blender stores these as separate pose markers with the same name on the action. The Cast importer already handles this correctly on import.

---

## What the Editor Does
- Reads pose markers from the active action and displays them in a list showing frame number and name
- Add, remove, rename and change the frame of any notetrack
- Jump button on each row sets the scene to that frame
- Apply Changes writes edits back to the action's pose markers
- Write to .cast file exports updated notetracks into an existing `.cast` file replacing old NotificationTrack nodes

---

## Viewing Notetracks in Blender
Pose markers appear in the Action Editor as small triangles along the top labeled with the notetrack name. To make them visible:

1. Once you import an animation open the Cast Panel on the right of Blender.
2. Click Refresh on the Cast Panel to update the current list.
3. To view them on the Timline open a Dopesheet editor
4. Switch the mode dropdown to **Action Editor**
5. Open the **Marker** menu and enable **Show Pose Markers**

> Pose markers do not appear in the regular Timeline by default in Blender 3.6.

---

## Based On
[DTZxPorter's Cast](https://github.com/dtzxporter/cast/releases)
