import bpy
from bpy.props import StringProperty, IntProperty, CollectionProperty
from bpy.types import PropertyGroup, Operator, Panel, UIList


class CastNotetracksEntry(PropertyGroup):
    name: StringProperty(name="Name", default="")
    frame: IntProperty(name="Frame", default=0, min=0)


class CastNotetracksGroup(PropertyGroup):
    entries: CollectionProperty(type=CastNotetracksEntry)
    active_index: IntProperty(name="Active", default=0)


def get_active_action():
    obj = bpy.context.object
    if obj and obj.animation_data and obj.animation_data.action:
        return obj.animation_data.action
    return None


def rebuild_list_from_markers(scene):
    action = get_active_action()
    nt = bpy.context.scene.cast_notetracks
    nt.entries.clear()
    if action is None:
        return
    for marker in sorted(action.pose_markers, key=lambda m: m.frame):
        entry = nt.entries.add()
        entry.name = marker.name
        entry.frame = marker.frame


def push_list_to_markers(action):
    while action.pose_markers:
        action.pose_markers.remove(action.pose_markers[0])
    nt = bpy.context.scene.cast_notetracks
    for entry in nt.entries:
        m = action.pose_markers.new(entry.name)
        m.frame = entry.frame


class CAST_OT_notetrack_refresh(Operator):
    bl_idname = "cast.notetrack_refresh"
    bl_label = "Refresh"
    bl_description = "Re-read notetracks from the active action's pose markers"

    def execute(self, context):
        rebuild_list_from_markers(context.scene)
        return {'FINISHED'}


class CAST_OT_notetrack_add(Operator):
    bl_idname = "cast.notetrack_add"
    bl_label = "Add Notetrack"
    bl_description = "Add a new notetrack at the current frame"

    name: StringProperty(name="Name", default="new_note")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "name")

    def execute(self, context):
        action = get_active_action()
        if action is None:
            self.report({'WARNING'}, "No active action found")
            return {'CANCELLED'}
        frame = context.scene.frame_current
        m = action.pose_markers.new(self.name)
        m.frame = frame
        rebuild_list_from_markers(context.scene)
        self.report({'INFO'}, f"Added '{self.name}' at frame {frame}")
        return {'FINISHED'}


class CAST_OT_notetrack_remove(Operator):
    bl_idname = "cast.notetrack_remove"
    bl_label = "Remove Notetrack"
    bl_description = "Remove the selected notetrack entry"

    def execute(self, context):
        action = get_active_action()
        if action is None:
            return {'CANCELLED'}
        nt = context.scene.cast_notetracks
        idx = nt.active_index
        if idx < 0 or idx >= len(nt.entries):
            return {'CANCELLED'}
        entry = nt.entries[idx]
        for m in action.pose_markers:
            if m.name == entry.name and m.frame == entry.frame:
                action.pose_markers.remove(m)
                break
        rebuild_list_from_markers(context.scene)
        nt.active_index = min(idx, len(nt.entries) - 1)
        return {'FINISHED'}


class CAST_OT_notetrack_apply(Operator):
    bl_idname = "cast.notetrack_apply"
    bl_label = "Apply Changes"
    bl_description = "Write the current notetrack list back to pose markers"

    def execute(self, context):
        action = get_active_action()
        if action is None:
            self.report({'WARNING'}, "No active action found")
            return {'CANCELLED'}
        push_list_to_markers(action)
        rebuild_list_from_markers(context.scene)
        self.report({'INFO'}, "Notetracks applied to action")
        return {'FINISHED'}


class CAST_OT_notetrack_jump(Operator):
    bl_idname = "cast.notetrack_jump"
    bl_label = "Jump to Frame"
    bl_description = "Set the scene frame to this notetrack's frame"

    index: IntProperty()

    def execute(self, context):
        nt = context.scene.cast_notetracks
        if self.index < len(nt.entries):
            context.scene.frame_current = nt.entries[self.index].frame
        return {'FINISHED'}


class CAST_OT_notetrack_export_cast(Operator):
    bl_idname = "cast.notetrack_export_cast"
    bl_label = "Export Notetracks to Cast"
    bl_description = "Write the current notetracks back into an existing .cast file"

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.cast", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        import sys, os

        addon_dir = os.path.dirname(os.path.realpath(__file__))
        if addon_dir not in sys.path:
            sys.path.insert(0, addon_dir)

        try:
            import cast as castlib
        except ImportError:
            self.report({'ERROR'}, "cast.py not found next to this file")
            return {'CANCELLED'}

        action = get_active_action()
        if action is None:
            self.report({'WARNING'}, "No active action - nothing to export")
            return {'CANCELLED'}

        path = self.filepath
        if not os.path.isfile(path):
            self.report({'ERROR'}, f"File not found: {path}")
            return {'CANCELLED'}

        try:
            c = castlib.Cast.load(path)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load cast: {e}")
            return {'CANCELLED'}

        notes = {}
        for m in action.pose_markers:
            notes.setdefault(m.name, []).append(m.frame)

        for root in c.Roots():
            for anim in root.ChildrenOfType(castlib.Animation):
                anim.childNodes = [
                    ch for ch in anim.childNodes
                    if not isinstance(ch, castlib.NotificationTrack)
                ]
                for note_name, frames in notes.items():
                    nt_node = anim.CreateNotification()
                    nt_node.SetName(note_name)
                    nt_node.SetKeyFrameBuffer(sorted(frames))

        try:
            c.save(path)
            self.report({'INFO'}, f"Notetracks written to {os.path.basename(path)}")
        except Exception as e:
            self.report({'ERROR'}, f"Save failed: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}


class CAST_OT_notetrack_popup(Operator):
    bl_idname = "cast.notetrack_popup"
    bl_label = "Notetracks"
    bl_description = "View and edit notetracks for the active action"

    def invoke(self, context, event):
        rebuild_list_from_markers(context.scene)
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        nt = context.scene.cast_notetracks
        action = get_active_action()

        box = layout.box()
        row = box.row()
        if action:
            row.label(text=action.name, icon="ACTION")
            row.label(text=f"{len(action.pose_markers)} marker(s)")
        else:
            row.label(text="No active action", icon="ERROR")

        row = layout.row(align=True)
        row.operator("cast.notetrack_refresh", icon="FILE_REFRESH", text="Refresh")
        row.operator("cast.notetrack_add", icon="ADD", text="Add")
        row.operator("cast.notetrack_remove", icon="REMOVE", text="Remove")

        layout.template_list(
            "CAST_UL_notetracks", "",
            nt, "entries",
            nt, "active_index",
            rows=8
        )

        idx = nt.active_index
        if 0 <= idx < len(nt.entries):
            entry = nt.entries[idx]
            box = layout.box()
            box.label(text="Edit Selected", icon="GREASEPENCIL")
            col = box.column(align=True)
            col.prop(entry, "name", text="Name")
            col.prop(entry, "frame", text="Frame")
            box.operator("cast.notetrack_apply", icon="CHECKMARK")

        layout.separator()
        layout.operator("cast.notetrack_export_cast", text="Write to .cast file", icon="FILE_TICK")

    def execute(self, context):
        return {'FINISHED'}


class CAST_UL_notetracks(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        sub = row.row(align=True)
        sub.scale_x = 0.38
        sub.prop(item, "frame", text="")
        row.prop(item, "name", text="", emboss=False)
        op = row.operator("cast.notetrack_jump", text="", icon="PLAY")
        op.index = index

    def filter_items(self, context, data, propname):
        entries = getattr(data, propname)
        flt_flags = []
        flt_neworder = []
        if self.filter_name:
            flt_flags = [
                self.bitflag_filter_item if self.filter_name.lower() in e.name.lower()
                else 0
                for e in entries
            ]
        return flt_flags, flt_neworder


class CAST_PT_notetracks(Panel):
    bl_idname = "CAST_PT_notetracks"
    bl_label = "Notetrack Editor"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Cast"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        nt = context.scene.cast_notetracks
        action = get_active_action()

        box = layout.box()
        row = box.row()
        if action:
            row.label(text=action.name, icon="ACTION")
            row.label(text=f"{len(action.pose_markers)} marker(s)")
        else:
            row.label(text="No active action", icon="ERROR")

        row = layout.row(align=True)
        row.operator("cast.notetrack_refresh", icon="FILE_REFRESH", text="Refresh")
        row.operator("cast.notetrack_add", icon="ADD", text="Add")
        row.operator("cast.notetrack_remove", icon="REMOVE", text="Remove")

        layout.template_list(
            "CAST_UL_notetracks", "",
            nt, "entries",
            nt, "active_index",
            rows=6
        )

        idx = nt.active_index
        if 0 <= idx < len(nt.entries):
            entry = nt.entries[idx]
            box = layout.box()
            box.label(text="Edit Selected", icon="GREASEPENCIL")
            col = box.column(align=True)
            col.prop(entry, "name", text="Name")
            col.prop(entry, "frame", text="Frame")
            box.operator("cast.notetrack_apply", icon="CHECKMARK")

        layout.separator()
        layout.label(text="Export", icon="EXPORT")
        layout.operator("cast.notetrack_export_cast", text="Write to .cast file", icon="FILE_TICK")


def draw_action_editor_button(self, context):
    if context.space_data.mode == 'ACTION':
        self.layout.operator("cast.notetrack_popup", text="Notetracks", icon="MARKER_HLT")


classes = (
    CastNotetracksEntry,
    CastNotetracksGroup,
    CAST_UL_notetracks,
    CAST_OT_notetrack_refresh,
    CAST_OT_notetrack_add,
    CAST_OT_notetrack_remove,
    CAST_OT_notetrack_apply,
    CAST_OT_notetrack_jump,
    CAST_OT_notetrack_export_cast,
    CAST_OT_notetrack_popup,
    CAST_PT_notetracks,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.cast_notetracks = bpy.props.PointerProperty(type=CastNotetracksGroup)
    bpy.types.DOPESHEET_HT_header.append(draw_action_editor_button)


def unregister():
    bpy.types.DOPESHEET_HT_header.remove(draw_action_editor_button)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.cast_notetracks