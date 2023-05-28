import bpy

from bpy.utils import (register_class, unregister_class)
from bpy.props import (StringProperty, BoolProperty,
                       PointerProperty, FloatVectorProperty, IntProperty)
from bpy.types import (Object, Operator, Panel, Scene)
from mathutils import Matrix

bl_info = {
    "name": "Bone Ext Tool",
    "description": "Animation extension",
    "author": "Heyter",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "category": "Bone",
    "location": "Properties -> Bone Properties",
    "support": "COMMUNITY"
}

PROPS = [
    ('skeleton', PointerProperty(
        name='Skeleton', type=Object)),
    ('parent_bone_name', StringProperty(
        name='Parent bone')),
    ('offset_vector', FloatVectorProperty(
        name='Custom Position', default=(0.0, 0.0, 0.0), subtype="XYZ")),
    ('offset_angle', FloatVectorProperty(
        name='Custom Rotation', default=(0.0, 0.0, 0.0), subtype="EULER")),
    ('bool_angle', BoolProperty(
        name='Keep rotation of parent', default=False)),
    ('bool_current_frame', BoolProperty(
        name='Keep current scene frame', default=False)),
    ('bool_swap_bones', BoolProperty(
        name='Swap bone with parent', default=False)),
    ('start_frame', IntProperty(
        name='Start frame', default=0)),
    ('end_frame', IntProperty(
        name='End frame', default=0))
]


class SetParentBoneOperator(Operator):
    bl_idname = 'bat.set_parent_bone'
    bl_label = 'Set Parent Bone'

    def execute(self, context):
        if bpy.context.active_object.mode != "POSE":
            return {'CANCELLED'}

        bones = bpy.context.selected_pose_bones

        if len(bones) == 1:
            context.scene.skeleton = bpy.context.object
            context.scene.parent_bone_name = bones[0].name

        return {'FINISHED'}


class AnimationBoneOperator(Operator):
    bl_idname = 'bat.anim_insert'
    bl_label = 'Insert keyframe'

    def execute(self, context):
        scene = context.scene

        if context.active_object.mode != "POSE" or not scene.skeleton or scene.skeleton is None or scene.skeleton.type != "ARMATURE":
            return {'CANCELLED'}

        parent = scene.skeleton.pose.bones[scene.parent_bone_name]

        if parent is None:
            return {'CANCELLED'}

        bones = context.selected_pose_bones

        if len(bones) > 0:
            start_frame = end_frame = 0

            bool_angle = scene.bool_angle
            swap_bones = scene.bool_swap_bones
            offset_angle = scene.offset_angle
            matrix = Matrix.Translation(scene.offset_vector)

            if scene.bool_current_frame:
                start_frame = scene.frame_current
                end_frame = scene.frame_current + 1
            else:
                start_frame = scene.start_frame
                end_frame = scene.end_frame + 1

            for obj in bones:
                if swap_bones is not True and obj == parent:
                    continue

                for frame in range(start_frame, end_frame):
                    bpy.context.scene.frame_set(frame)

                    parent_matrix = parent.matrix.copy() if swap_bones else parent.matrix
                    euler = parent.rotation_euler.copy()

                    if bool_angle is False:
                        euler.x += offset_angle.x
                        euler.y += offset_angle.y
                        euler.z += offset_angle.z

                    if swap_bones:
                        parent.rotation_euler = obj.rotation_euler.copy()
                        parent.matrix = obj.matrix.copy()

                    obj.matrix = parent_matrix @ matrix
                    obj.rotation_euler = euler

                    obj.keyframe_insert(data_path="location", frame=frame)
                    obj.keyframe_insert(
                        data_path="rotation_euler", frame=frame)

                    if swap_bones:
                        parent.keyframe_insert(
                            data_path="location", frame=frame)
                        parent.keyframe_insert(
                            data_path="rotation_euler", frame=frame)

        return {'FINISHED'}


class AnimationBonePanel(Panel):
    bl_label = 'Animation Bone Tool'
    bl_idname = "BAT_PT_anim_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'bone'
    bl_default_closed = True

    def draw(self, context):
        scene = context.scene
        col = self.layout.column()

        for (prop_name, _) in PROPS:
            row = col.row()
            row.prop(scene, prop_name)

            if prop_name == "parent_bone_name":
                col.operator('bat.set_parent_bone', text='Set parent bone')
                col.separator()

        col.separator()
        col.operator('bat.anim_insert', text='Insert keyframe')


CLASSES = [
    AnimationBoneOperator,
    AnimationBonePanel,
    SetParentBoneOperator
]


def register():
    for c in CLASSES:
        register_class(c)

    for (prop_name, prop_value) in PROPS:
        setattr(Scene, prop_name, prop_value)


def unregister():
    for (prop_name, _) in PROPS:
        delattr(Scene, prop_name)

    for c in CLASSES:
        unregister_class(c)


if __name__ == "__main__":
    register()
