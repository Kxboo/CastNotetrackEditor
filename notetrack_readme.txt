CAST NOTETRACK EDITOR
=====================
DISCLAIMER TESTED ON BLENDER 3.6 ONLY
INSTALLATION
-------------
  1. Copy cast_notetrack_editor.py into your cast addon folder,
     next to __init__.py, cast.py, import_cast.py, export_cast.py.

  2. Add this import at the top of __init__.py:

       from . import cast_notetrack_editor

  3. Add this line inside register() in __init__.py:

       cast_notetrack_editor.register()

  4. Add this line inside unregister() in __init__.py:

       cast_notetrack_editor.unregister()

  Full example of register() and unregister():

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

HOW NOTETRACKS WORK IN CAST
-----------------------------
In the binary .cast format, notetracks live inside the Animation node as
children of type NotificationTrack (identifier 0x6669746E).

Each NotificationTrack has two properties:

  "n"  (string)    The notetrack name, e.g. "end", "loop_end",
                   "snd_..." sound hashes, "xstring_..." string hashes.

  "kb" (int array) The list of frame numbers this note fires on.
                   The integer width (b/h/i) is chosen automatically
                   based on the highest frame number.

One notetrack name can fire on MULTIPLE frames. For example a footstep
notetrack might fire on frames 18 and 108. Blender stores these as
separate pose_markers with the same name on the action. The Cast importer
(importNotificationTrackNode in import_cast.py) already handles this
correctly on import.

Notetracks are typically found near the end of the .cast file since they
are children of the Animation node which is written last. In the raw
binary they appear as readable ASCII strings surrounded by binary data,
which is why they look like noise until you know what to search for.


WHAT THE EDITOR DOES
---------------------
- Reads pose_markers from the active action and displays them in a list
  showing frame number and notetrack name.
- Lets you add, remove, rename, and change the frame of any notetrack.
- The jump button (triangle) on each row sets the scene to that frame.
- Apply Changes writes edits back to the action's pose_markers.
- Write to .cast file exports the updated notetracks into an existing
  .cast animation file, replacing its old NotificationTrack nodes.
- A Notetracks button in the Action Editor header opens a popup with
  the full editor without needing to use the N-panel.


VIEWING NOTETRACKS IN BLENDER
-------------------------------
Pose markers show up in the Action Editor (Dopesheet -> Action Editor mode)
as small triangles along the top of the editor, labeled with the notetrack
name. To make them visible:

  1. Open a Dopesheet editor.
  2. Switch the mode dropdown (top left) to "Action Editor".
  3. In the header, open the Marker menu and enable "Show Pose Markers".

They do NOT appear in the regular Timeline by default in Blender 3.6.



