# Mustard Tools script
# https://github.com/Mustard2/MustardTools

bl_info = {
    "name": "Mustard Tools",
    "description": "A set of tools for riggers and animators",
    "author": "Mustard",
    "version": (0, 2, 0),
    "blender": (2, 90, 1),
    "warning": "",
    "category": "3D View",
}

import bpy
import addon_utils
import sys
import os
import re
import time
import math
from bpy.props import *
from mathutils import Vector, Color
import webbrowser

# ------------------------------------------------------------------------
#    Mustard Tools Properties
# ------------------------------------------------------------------------

# Poll functions for properties
def mustardtools_poll_mesh(self, object):
    
    return object.type == 'MESH'

def mustardtools_poll_armature(self, object):
    
    return object.type == 'ARMATURE'

# Function for advanced settings (reset advanced settings if toggled off)
def mustardtools_ms_advanced_update(self, context):
    
    if not self.ms_advanced:
        
        settings = bpy.context.scene.mustardtools_settings
        
        settings.ik_spline_bone_custom_shape = None
        settings.ik_spline_first_bone_custom_shape = None
        settings.ik_spline_resolution = 32
    
    return
        
# Class with all the settings variables
class MustardTools_Settings(bpy.types.PropertyGroup):
    
    # Main Settings definitions
    # UI definitions
    ms_advanced: bpy.props.BoolProperty(name="Advanced Options",
                                        description="Unlock advanced options",
                                        default=False,
                                        update=mustardtools_ms_advanced_update)
    ms_debug: bpy.props.BoolProperty(name="Debug mode",
                                        description="Unlock debug mode.\nThis will generate more messaged in the console.\nEnable it only if you encounter problems, as it might degrade general Blender performance",
                                        default=False)
    ms_naming_prefix: bpy.props.StringProperty(name="",
                                                default="MustardTools",
                                                description="Name prefix for the objects created by the addon")
    
    # IK Chain Tool definitions
    # UI definitions
    ik_chain_last_bone_use: bpy.props.BoolProperty(name="Last Bone Controller",
                                                    description="Use last bone as the controller instead of creating a new bone at the end of the chain",
                                                    default=False)
    ik_chain_bendy: bpy.props.BoolProperty(name="Bendy Bones",
                                                    description="Convert the bones of the chain to bendy bones",
                                                    default=False)
    ik_chain_bendy_segments: bpy.props.IntProperty(name="Segments",
                                                    default=2,min=2,max=32,
                                                    description="Number of segments for every bendy bone")
    ik_chain_last_bone_custom_shape: bpy.props.PointerProperty(type=bpy.types.Object,
                                                                name="",
                                                                description="Object that will be used as custom shape for the IK controller",
                                                                poll=mustardtools_poll_mesh)
    ik_chain_pole_angle: bpy.props.IntProperty(name="Pole Angle",
                                                    default=90,min=-180,max=180,
                                                    description="Pole rotation offset.\nChange this value if the rotation of the bones in the result are wrong (usually this is 90 or -90 degrees)")
    ik_chain_pole_bone_custom_shape: bpy.props.PointerProperty(type=bpy.types.Object,
                                                                name="",
                                                                description="Object that will be used as custom shape for the IK pole",
                                                                poll=mustardtools_poll_mesh)
    
    # Internal definitions (not for UI)
    ik_chain_pole_status: bpy.props.BoolProperty(default=False,
                                                options={'HIDDEN'})
    ik_chain_last_bone: bpy.props.StringProperty(default="",
                                                options={'HIDDEN'})
    ik_chain_pole_bone: bpy.props.StringProperty(default="",
                                                options={'HIDDEN'})
    
    # IK Spline Tool definitions
    # UI definitions
    ik_spline_number: bpy.props.IntProperty(default=3,min=3,max=20,
                                            name="Controllers",
                                            description="Number of IK spline controllers")
    ik_spline_resolution: bpy.props.IntProperty(default=32,min=1,max=64,
                                            name="Resolution",
                                            description="Resolution of the spline.\nSubdivision performed on each segment of the curve")
    ik_spline_bendy: bpy.props.BoolProperty(name="Bendy Bones",
                                                    description="Convert the bones of the chain to bendy bones",
                                                    default=False)
    ik_spline_bendy_segments: bpy.props.IntProperty(name="Segments",
                                                    default=2,min=2,max=32,
                                                    description="Number of segments for every bendy bone")
    ik_spline_bone_custom_shape: bpy.props.PointerProperty(type=bpy.types.Object,
                                                    name="",
                                                    description="Object that will be used as custom shape for the spline IK bones",
                                                    poll=mustardtools_poll_mesh)
    ik_spline_first_bone_custom_shape: bpy.props.PointerProperty(type=bpy.types.Object,
                                                    name="",
                                                    description="Object that will be used as custom shape for the spline IK first bone",
                                                    poll=mustardtools_poll_mesh)
    
    # Mouth Controller Tool definitions
    # UI definitions
    mouth_controller_mirror: bpy.props.BoolProperty(name="Mirror",
                                                    description="Use this option if the bones are named with the .r and .l naming convention for right and left")
    mouth_controller_number_bones: bpy.props.IntProperty(default=2, min=1, max=2, name="Number of central bones")
    mouth_controller_edge_bone_correction_x: bpy.props.FloatProperty(default=1.0,
                                                            name="Edge bones correction (x axis)",
                                                            description="The default value can not be changed")
    mouth_controller_edge_bone_correction_z: bpy.props.FloatProperty(default=0.1,
                                                            name="Edge bones correction (z axis)",
                                                            description="This value is the ratio between the movement of the edge bones and the center bones on the z axis (back and forth movement of the controller bone)")
    mouth_controller_middle1_bone_correction_x: bpy.props.FloatProperty(default=0.2,
                                                            name="Middle bones 1 correction (x axis)",
                                                            description="This value is the ratio between the movement of the middle bones and the edge bones on the x axis (left and right movement of the controller bone)")
    mouth_controller_middle1_bone_correction_z: bpy.props.FloatProperty(default=1.,
                                                            name="Middle bones 1 correction (z axis)",
                                                            description="This value is the ratio between the movement of the middle bones and the center bones on the x axis (back and forth movement of the controller bone)")
    mouth_controller_middle2_bone_correction_x: bpy.props.FloatProperty(default=0.5,
                                                            name="Middle bones 2 correction (x axis)",
                                                            description="This value is the ratio between the movement of the middle bones and the edge bones on the x axis (left and right movement of the controller bone)")
    mouth_controller_middle2_bone_correction_z: bpy.props.FloatProperty(default=1.,
                                                            name="Middle bones 2 correction (z axis)",
                                                            description="This value is the ratio between the movement of the middle bones and the center bones on the x axis (back and forth movement of the controller bone)")
    mouth_controller_center_bone_correction_x: bpy.props.FloatProperty(default=1.,
                                                            name="Center bones correction (x axis)",
                                                            description="The default value can not be changed")
    mouth_controller_center_bone_correction_z: bpy.props.FloatProperty(default=1.,
                                                            name="Middle bones 2 correction (z axis)",
                                                            description="This value is the ratio between the movement of the middle bones and the center bones on the x axis (back and forth movement of the controller bone)")
    mouth_controller_floor_offset: bpy.props.FloatProperty(default=0.006,
                                                            name="Upper bone floor distance",
                                                            description="The minimum distance between the upper and the bottom mouth bones")
    mouth_controller_transform_ratio: bpy.props.FloatProperty(default=0.1,
                                                            name="Bones transformation value",
                                                            description="The value with which the bones are affected by the movement of the controller")
    
    mouth_controller_armature_controller: bpy.props.PointerProperty(type=bpy.types.Object,
                                                    name="Armature controller",
                                                    description="Armature",
                                                    poll=mustardtools_poll_armature)
    mouth_controller_bone: bpy.props.StringProperty(name="Controller Bone")
    mouth_controller_bone_custom_shape: bpy.props.PointerProperty(type=bpy.types.Object,
                                                                name="",
                                                                description="Object that will be used as custom shape for the mouth controller",
                                                                poll=mustardtools_poll_mesh)
    
    mouth_controller_armature: bpy.props.PointerProperty(type=bpy.types.Object,
                                                    name="Armature",
                                                    description="Armature",
                                                    poll=mustardtools_poll_armature)
    mouth_controller_edge_bone_L: bpy.props.StringProperty(name="Edge L")
    mouth_controller_edge_bone_R: bpy.props.StringProperty(name="Edge R")
    mouth_controller_center_bone_top: bpy.props.StringProperty(name="Center Top")
    mouth_controller_center_bone_bot: bpy.props.StringProperty(name="Center Bottom")
    mouth_controller_middle1_bone_L_top: bpy.props.StringProperty(name="Middle 1 Top L",description="In the case of more than one middle bone, the Middle 1 should be the one near the center bone")
    mouth_controller_middle1_bone_R_top: bpy.props.StringProperty(name="Middle 1 Top R",description="In the case of more than one middle bone, the Middle 1 should be the one near the center bone")
    mouth_controller_middle2_bone_L_top: bpy.props.StringProperty(name="Middle 2 Top L",description="In the case of more than one middle bone, the Middle 2 should be the one far from the center bone")
    mouth_controller_middle2_bone_R_top: bpy.props.StringProperty(name="Middle 2 Top R",description="In the case of more than one middle bone, the Middle 2 should be the one far from the center bone")
    mouth_controller_middle1_bone_L_bot: bpy.props.StringProperty(name="Middle 1 Bottom L",description="In the case of more than one middle bone, the Middle 1 should be the one near the center bone")
    mouth_controller_middle1_bone_R_bot: bpy.props.StringProperty(name="Middle 1 Bottom R",description="In the case of more than one middle bone, the Middle 1 should be the one near the center bone")
    mouth_controller_middle2_bone_L_bot: bpy.props.StringProperty(name="Middle 2 Bottom L",description="In the case of more than one middle bone, the Middle 2 should be the one far from the center bone")
    mouth_controller_middle2_bone_R_bot: bpy.props.StringProperty(name="Middle 2 Bottom R",description="In the case of more than one middle bone, the Middle 2 should be the one far from the center bone")
    mouth_controller_jaw_bone: bpy.props.StringProperty(name="Jaw")
    
    # Slide Keyframes Tool definitions
    # UI definitions
    slide_keyframes_application: bpy.props.EnumProperty(name = "",
                                                        description = "Which object's keyframes are considered by the Slide Keyframes tool",
                                                            items = [('0','Active','Consider the active object only'), 
                                                                    ('1','Selected','Consider all the selected objects'),
                                                                    ('2','All','Consider all objects in the scene')],
                                                            default = '0')

bpy.utils.register_class(MustardTools_Settings)

bpy.types.Scene.mustardtools_settings = bpy.props.PointerProperty(type=MustardTools_Settings)

# ------------------------------------------------------------------------
#    IK Chain Tool
# ------------------------------------------------------------------------

class MUSTARDTOOLS_OT_IKChain(bpy.types.Operator):
    """This tool will create an IK rig on the selected chain.\nSelect the bones, the last one being the tip of the chain where the controller will be placed.\n\nCondition: select at least 3 bones"""
    bl_idname = "mustardui.ik_chain"
    bl_label = "Create"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):
        if context.mode != "POSE" or bpy.context.selected_pose_bones == None:
            return False
        else:
            
            chain_bones = bpy.context.selected_pose_bones
            
            if len(chain_bones) < 2:
                return False
            else:
                abort_aa = False
                for bone in chain_bones:
                    for constraint in bone.constraints:
                        if constraint.type == 'IK':
                            abort_aa = True
                            break
                
                if abort_aa:
                    return False
                else:
                    return True

    def execute(self, context):
        
        # Import settings
        settings = bpy.context.scene.mustardtools_settings
        name_prefix = settings.ms_naming_prefix
        
        IKChainControllerBoneName = name_prefix + ".IK.Controller"
        IKChainConstraintName = name_prefix + " IKChain"
    
        # Definitions
        arm = bpy.context.object
        chain_bones = bpy.context.selected_pose_bones
        chain_length = len(chain_bones)
        chain_last_bone = chain_bones[chain_length-1]
        chain_pole_bone = chain_bones[int((chain_length-1)/2)]

        if settings.ms_debug:
            print("MustardTools IK Chain - Armature selected: " + bpy.context.object.name)
            print("MustardTools IK Chain - Chain length: " + str(chain_length))
            print("MustardTools IK Chain - Last bone: " + chain_last_bone.name)
            
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        
        if settings.ik_chain_bendy:
            for bone in chain_bones:
                arm.data.edit_bones[bone.name].bbone_segments = settings.ik_chain_bendy_segments
            if settings.ik_chain_last_bone_use:
                arm.data.edit_bones[chain_last_bone.name].bbone_segments = 1
            
            arm.data.display_type = "BBONE"
        
        if settings.ik_chain_last_bone_use:
            
            IK_main_bone_edit = arm.data.edit_bones[chain_last_bone.name]
            IK_main_bone_edit.parent = None
            IK_main_bone_edit.use_deform = False
            chain_last_bone = chain_bones[chain_length-2]
            chain_length = chain_length - 1
            IK_main_bone_name = IK_main_bone_edit.name
        
        else:
            
            chain_last_bone_edit = arm.data.edit_bones[chain_last_bone.name]
            IK_main_bone_edit = arm.data.edit_bones.new(IKChainControllerBoneName)
            IK_main_bone_edit.use_deform = False
            IK_main_bone_edit.head = chain_last_bone_edit.tail
            IK_main_bone_edit.tail = 2. * chain_last_bone_edit.tail - chain_last_bone_edit.head
            IK_main_bone_name = IK_main_bone_edit.name

        bpy.ops.object.mode_set(mode='POSE')
        
        IK_main_bone = arm.pose.bones[IK_main_bone_name]
        IK_main_bone.custom_shape = settings.ik_chain_last_bone_custom_shape
        IK_main_bone.use_custom_shape_bone_size = True

        IKConstr = chain_last_bone.constraints.new('IK')
        IKConstr.name = IKChainConstraintName
        IKConstr.use_rotation = True
        IKConstr.target = arm
        IKConstr.subtarget = IK_main_bone_name
        IKConstr.chain_count = chain_length

        self.report({'INFO'}, 'MustardTools - IK successfully added.')
        
        return {'FINISHED'}

class MUSTARDTOOLS_OT_IKChain_Pole(bpy.types.Operator):
    """This tool will guide you in the creation of a pole for an already available IK rig.\nFor a better automatic generation, select the same chain you used to generate the IK Chain rig"""
    bl_idname = "mustardui.ik_chainpole"
    bl_label = "Add Pole"
    bl_options = {'REGISTER','UNDO'}
    
    status: BoolProperty(name='',
        description="",
        default=True,
        options={'HIDDEN'}
    )
    cancel: BoolProperty(name='',
        description="",
        default=False,
        options={'HIDDEN'}
    )
    
    @classmethod
    def poll(cls, context):
        
        settings = bpy.context.scene.mustardtools_settings
        
        if not settings.ik_chain_pole_status:
            
            if context.mode != "POSE" or bpy.context.selected_pose_bones == None:
                return False
            else:
                
                chain_bones = bpy.context.selected_pose_bones
                chain_length = len(chain_bones)
                
                if len(chain_bones) < 2:
                    return False
                else:
                    
                    chain_last_bone = chain_bones[chain_length-1]
                    
                    abort_aa = True
                    for constraint in chain_last_bone.constraints:
                        if constraint.type == 'IK':
                            abort_aa = False
                            if constraint.pole_target != None and constraint.pole_subtarget != None and constraint.pole_subtarget != "":
                                abort_aa = True
                    
                    if abort_aa:
                        return False
                    else:
                        return True
                    
        else:
            
            return True

    def execute(self, context):
        
        # Import settings
        settings = bpy.context.scene.mustardtools_settings
        name_prefix = settings.ms_naming_prefix
        
        # Naming convention
        IKChain_Pole_Bone_Name = name_prefix + ".IK.Pole"
    
        # Definitions
        arm = bpy.context.object
        
        if self.cancel and self.status:
                
            IK_pole_bone_edit = arm.data.edit_bones[settings.ik_chain_pole_bone]
            arm.data.edit_bones.remove(IK_pole_bone_edit)
                
            bpy.ops.object.mode_set(mode='POSE')
                
            self.cancel = False
            self.status = False
            settings.ik_chain_pole_status = False
        
        elif self.status and not self.cancel:
            
            # Definitions
            chain_bones = bpy.context.selected_pose_bones
            chain_length = len(chain_bones)
            chain_last_bone = chain_bones[chain_length-1]
            chain_pole_bone = chain_bones[int((chain_length-1)/2)]
            
            settings.ik_chain_pole_status = True
            
            if settings.ms_debug:
                print("MustardTools IK Chain - Armature selected: " + bpy.context.object.name)
                print("MustardTools IK Chain - Chain length: " + str(chain_length))
                print("MustardTools IK Chain - Last bone: " + chain_last_bone.name)
                print("MustardTools IK Chain - Pole bone reference: " + chain_pole_bone.name)
            
            settings.ik_chain_last_bone = chain_last_bone.name
        
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    
            chain_pole_bone_edit = arm.data.edit_bones[chain_pole_bone.name]
            IK_pole_bone_edit = arm.data.edit_bones.new(IKChain_Pole_Bone_Name)
            IK_pole_bone_edit.use_deform = False
            IK_pole_bone_edit.head = chain_pole_bone_edit.head
            IK_pole_bone_edit.tail = chain_pole_bone_edit.tail
            
            settings.ik_chain_pole_bone = IK_pole_bone_edit.name
            
            bpy.ops.armature.select_all(action='DESELECT')
            IK_pole_bone_edit.select = True
            IK_pole_bone_edit.select_head = True
            IK_pole_bone_edit.select_tail = True
            arm.data.edit_bones.active = IK_pole_bone_edit
                        
            print(bpy.context.selected_editable_bones)
            
        else:
            
            bpy.ops.object.mode_set(mode='POSE')
            
            IK_pole_bone = arm.pose.bones[settings.ik_chain_pole_bone]
            IK_pole_bone.custom_shape = settings.ik_chain_pole_bone_custom_shape
            IK_pole_bone.use_custom_shape_bone_size = True
            
            for constraint in arm.pose.bones[settings.ik_chain_last_bone].constraints:
                if constraint.type == 'IK':
                    IKConstr = constraint

            IKConstr.use_rotation = True
            IKConstr.pole_target = arm
            IKConstr.pole_subtarget = settings.ik_chain_pole_bone
            IKConstr.pole_angle = settings.ik_chain_pole_angle * 3.141593/ 180.
            
            settings.ik_chain_pole_status = False

            self.report({'INFO'}, 'MustardTools - IK pole successfully added.')
        
        return {'FINISHED'}

class MUSTARDTOOLS_OT_IKChain_Clean(bpy.types.Operator):
    """This tool will clean the available IK constraints in the selected bones.\nSelect a bone with an IK constraint to enable the tool.\nA confirmation box will appear"""
    bl_idname = "mustardui.ik_chainclean"
    bl_label = "Remove IK"
    bl_options = {'REGISTER','UNDO'}
    
    delete_bones: BoolProperty(name='Delete bones',
        description="Delete controller and pole bones",
        default=True
    )
    reset_bendy: BoolProperty(name='Reset Bendy Bones',
        description="Reset bendy bones to standard bones",
        default=True
    )
    
    @classmethod
    def poll(cls, context):
        if context.mode != "POSE" or bpy.context.selected_pose_bones == None:
            return False
        else:
            
            chain_bones = bpy.context.selected_pose_bones
            
            if len(chain_bones) < 1:
                return False
            else:
                abort_aa = True
                for bone in chain_bones:
                    for constraint in bone.constraints:
                        if constraint.type == 'IK':
                            abort_aa = False
                            break
                
                if abort_aa:
                    return False
                else:
                    return True

    def execute(self, context):
        
        # Import settings
        settings = bpy.context.scene.mustardtools_settings
            
        # Definitions
        arm = bpy.context.object
        chain_bones = bpy.context.selected_pose_bones
        chain_length = len(chain_bones)
        chain_last_bone = chain_bones[chain_length-1]
        chain_pole_bone = chain_bones[int((chain_length-1)/2)]
            
        removed_constr = 0
        removed_bones = 0
        
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        
        if self.reset_bendy:
            for bone in chain_bones:
                arm.data.edit_bones[bone.name].bbone_segments = 1
            arm.data.display_type = "OCTAHEDRAL"
            if settings.ms_debug:
                print("MustardTools IK Chain - Bendy bones resetted")
        
        bpy.ops.object.mode_set(mode='POSE', toggle=False)

        for bone in chain_bones:
            for constraint in bone.constraints:
                if constraint.type == 'IK':
                    if self.delete_bones:
                        
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                        
                        if constraint.target != None and constraint.subtarget != None and constraint.subtarget != "":
                            IKArm = constraint.target
                            IKBone = IKArm.data.edit_bones[constraint.subtarget]
                            IKBone_name = IKBone.name
                            IKArm.data.edit_bones.remove(IKBone)
                            if settings.ms_debug:
                                print("MustardTools IK Chain - Bone " + IKBone_name + " removed from Armature " + IKArm.name)
                            removed_bones = removed_bones + 1
                        if constraint.pole_target != None and constraint.pole_subtarget != None and constraint.pole_subtarget != "":
                            IKArm2 = constraint.pole_target
                            IKBone2 = IKArm2.data.edit_bones[constraint.pole_subtarget]
                            IKBone2_name = IKBone2.name
                            IKArm2.data.edit_bones.remove(IKBone2)
                            if settings.ms_debug:
                                print("MustardTools IK Chain - Bone " + IKBone2_name + " removed from Armature " + IKArm2.name)
                            removed_bones = removed_bones + 1
                        
                        bpy.ops.object.mode_set(mode='POSE')
                    
                    bone.constraints.remove(constraint)
                    removed_constr = removed_constr + 1
        if self.delete_bones:
            self.report({'INFO'}, 'MustardTools - '+ str(removed_constr) +' IK constraints and '+ str(removed_bones) +' Bones successfully removed.')
        else:
            self.report({'INFO'}, 'MustardTools - '+ str(removed_constr) +' IK constraints successfully removed.')
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        
        return context.window_manager.invoke_props_dialog(self)
            
    def draw(self, context):
        
        layout = self.layout
        
        chain_bones = bpy.context.selected_pose_bones
        
        IK_num = 0
        IK_num_nMUI = 0
        for bone in chain_bones:
            for constraint in bone.constraints:
                if constraint.type == 'IK':
                    IK_num = IK_num + 1
                    if "MustardTools" not in constraint.name:
                        IK_num_nMUI = IK_num_nMUI + 1
        
        box = layout.box()
        box.prop(self, "delete_bones")
        box.prop(self, "reset_bendy")
        box = layout.box()
        box.label(text="Will be removed:", icon="ERROR")
        box.label(text="        - " + str(IK_num) + " IK constraints.")
        box.label(text="        - " + str(IK_num_nMUI) + " of which are not Mustard Tools generated.")


# ------------------------------------------------------------------------
#    IK Spline Tool
# ------------------------------------------------------------------------

class MUSTARDTOOLS_OT_IKSpline(bpy.types.Operator):
    """This tool will create an IK spline on the selected chain.\nSelect the bones, the last one being the tip of the chain.\n\nConditions:\n    - select at least 4 bones\n    - the number of controllers should be lower than the number of bones - 1"""
    bl_idname = "mustardui.ik_spline"
    bl_label = "Create"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):
        
        settings = bpy.context.scene.mustardtools_settings
        
        if context.mode != "POSE" or bpy.context.selected_pose_bones == None:
            return False
        else:
            
            chain_bones = bpy.context.selected_pose_bones
            
            if settings.ik_spline_number > len(chain_bones)-1:
                return False
            if len(chain_bones) < 3:
                return False
            else:
                abort_aa = False
                for bone in chain_bones:
                    for constraint in bone.constraints:
                        if constraint.type == 'SPLINE_IK':
                            abort_aa = True
                            break
                
                if abort_aa:
                    return False
                else:
                    return True

    def execute(self, context):
        
        # Import settings
        settings = bpy.context.scene.mustardtools_settings
        name_prefix = settings.ms_naming_prefix
        num = settings.ik_spline_number
        
        # Naming convention
        IKSpline_Curve_Name = name_prefix + ".IKSpline.Curve"
        IKSpline_Bone_Name = name_prefix + ".IKSpline.Bone"
        IKSpline_Hook_Modifier_Name = name_prefix + ".IKSpline.Hook"
        IKSpline_Empty_Name = name_prefix + ".IKSpline.Empty"
        IKSpline_Constraint_Name = name_prefix + ".IKSpline"
    
        # Definitions
        arm = bpy.context.object
        chain_bones = bpy.context.selected_pose_bones
        chain_length = len(chain_bones)
        chain_last_bone = chain_bones[chain_length-1]
        
        # Output a warning if the location has not been applied to the armature
        warning = 0
        if arm.location.x != 0. or arm.location.y != 0. or arm.location.z != 0.:
            self.report({'WARNING'}, 'MustardTools - The Armature selected seems not to have location applied. This might generate odd results!')
            print("MustardTools IK Spline - Apply the location on the armature with Ctrl+A in Object mode!")
            warning += 1
        
        if settings.ms_debug:
            print("MustardTools IK Spline - Armature selected: " + bpy.context.object.name)
            print("MustardTools IK Spline - Chain length: " + str(chain_length))
        
        # Create the curve in Object mode
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        
        curveData = bpy.data.curves.new(IKSpline_Curve_Name, type='CURVE')
        curveData.dimensions = '3D'
        curveData.use_path = True
        
        # Create the path for the curve in Edit mode
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        
        polyline = curveData.splines.new('BEZIER')
        polyline.bezier_points.add(num-1)
        
        # Fill the curve with the points, and also create controller bones
        b = []
        b_name = []
        
        for i in range(0,num-1):
            # Create the point to insert in the curve, at the head of the bone
            (x,y,z) = (chain_bones[int(chain_length/(num-1)*i)].head.x,
                        chain_bones[int(chain_length/(num-1)*i)].head.y,
                        chain_bones[int(chain_length/(num-1)*i)].head.z)
            polyline.bezier_points[i].co = (x, y, z)
            # Use AUTO to generate handles (should be changed later to ALIGNED to enable rotations)
            polyline.bezier_points[i].handle_right_type = 'AUTO'
            polyline.bezier_points[i].handle_left_type = 'AUTO'
            
            # Create the controller bone
            b = arm.data.edit_bones.new(IKSpline_Bone_Name)
            b.use_deform = False
            b.head = chain_bones[int(chain_length/(num-1)*i)].head
            b.tail = chain_bones[int(chain_length/(num-1)*i)].tail
            
            # Save the name, as changing context will erase the bone data
            b_name.append(b.name)
            
            if settings.ms_debug:
                print("MustardTools IK Spline - Bone created with head: " + str(b[i].head.x) + " , " + str(b[i].head.y) + " , " + str(b[i].head.z))
                print("                                       and tail: " + str(b[i].tail.x) + " , " + str(b[i].tail.y) + " , " + str(b[i].tail.z))
        
        # The same as above, but for the last bone
        i += 1
        (x,y,z) = (chain_bones[chain_length-1].head.x,chain_bones[chain_length-1].head.y,chain_bones[chain_length-1].head.z)
        (x2,y2,z2) = (chain_bones[chain_length-2].head.x,chain_bones[chain_length-2].head.y,chain_bones[chain_length-2].head.z)
        polyline.bezier_points[i].co = (x, y, z)
        polyline.bezier_points[i].handle_right = ( x+(x-x2)/2 , y+(y-y2)/2, z+(z-z2)/2)
        polyline.bezier_points[i].handle_left = (x2+(x-x2)/2, y2+(y-y2)/2, z2+(z-z2)/2)
        polyline.bezier_points[i].handle_right_type = 'ALIGNED'
        polyline.bezier_points[i].handle_left_type = 'ALIGNED'
        
        b = arm.data.edit_bones.new(IKSpline_Bone_Name)
        b.use_deform = False
        b.head = chain_bones[chain_length-1].head
        b.tail = chain_bones[chain_length-1].tail
        b_name.append(b.name)
        
        if settings.ms_debug:
            print("MustardTools IK Spline - Bone created with head: " + str(b[i].head.x) + " , " + str(b[i].head.y) + " , " + str(b[i].head.z))
            print("                                       and tail: " + str(b[i].tail.x) + " , " + str(b[i].tail.y) + " , " + str(b[i].tail.z))
        
        # Enable bendy bones if the option has been selected
        if settings.ik_spline_bendy:
            for bone in chain_bones:
                arm.data.edit_bones[bone.name].bbone_segments = settings.ik_spline_bendy_segments
            
            # Switch to B-Bone view for the Armature bones
            arm.data.display_type = "BBONE"
        
        # GO back to Object mode
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        
        # Create empties
        e = []
        for i in range(0,num):
            e.append( bpy.data.objects.new(IKSpline_Empty_Name, None) )
            e[i].location=curveData.splines[0].bezier_points[i].co
            constraint=e[i].constraints.new('COPY_TRANSFORMS')
            constraint.target = arm
            constraint.subtarget = b_name[i]
            if i == 0:
                e[i].empty_display_type="SPHERE"
            else:
                e[i].empty_display_type="CIRCLE"
            bpy.context.collection.objects.link(e[i])
            e[i].hide_render = True
            e[i].hide_viewport = True
            if settings.ms_debug:
                print("MustardTools IK Spline - Empty created at: " + str(e[i].location.x) + " , " + str(e[i].location.y) + " , " + str(e[i].location.z))
            
        # Set bones custom shape if selected in the options, else use the Empty default shapes
        if settings.ik_spline_first_bone_custom_shape != None:
            bone = arm.pose.bones[b_name[0]]
            bone.custom_shape = settings.ik_spline_first_bone_custom_shape
            bone.use_custom_shape_bone_size = True
        else:
            bone = arm.pose.bones[b_name[0]]
            bone.custom_shape = e[0]
            bone.use_custom_shape_bone_size = True
        
        if settings.ik_spline_bone_custom_shape != None:
            for i in range(1,num):
                bone = arm.pose.bones[b_name[i]]
                bone.custom_shape = settings.ik_spline_bone_custom_shape
                bone.use_custom_shape_bone_size = True
        else:
            for i in range(1,num):
                bone = arm.pose.bones[b_name[i]]
                bone.custom_shape = e[i]
                bone.use_custom_shape_bone_size = True
        
        # Create curve object
        curveOB = bpy.data.objects.new(IKSpline_Curve_Name, curveData)
        
        # Create hook modifiers
        m = []
        for i in range(0,num):
            m.append( curveOB.modifiers.new(IKSpline_Hook_Modifier_Name, 'HOOK') )
            m[i].object = e[i]
        
        # Link the curve in the scene and use as active object
        bpy.context.collection.objects.link(curveOB)
        context.view_layer.objects.active = curveOB
        
        # Go in Edit mode
        bpy.ops.object.editmode_toggle()
        
        # Hook the curve points to the empties
        for i in range(0,num):
            
            select_index = i
            for j, point in enumerate(curveData.splines[0].bezier_points) :
                point.select_left_handle = j == select_index
                point.select_right_handle = j == select_index
                point.select_control_point = j == select_index
            
            bpy.ops.object.hook_assign(modifier=m[i].name)
            bpy.ops.object.hook_reset(modifier=m[i].name)
            
            # Change the handle type to ALIGNED to enable rotations
            curveData.splines[0].bezier_points[i].handle_right_type = 'ALIGNED'
            curveData.splines[0].bezier_points[i].handle_left_type = 'ALIGNED'
        
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        
        # Create Spline IK modifier
        IKSplineConstr = chain_last_bone.constraints.new('SPLINE_IK')
        IKSplineConstr.name = IKSpline_Constraint_Name
        IKSplineConstr.target = curveOB
        IKSplineConstr.chain_count = chain_length
        IKSplineConstr.y_scale_mode = "BONE_ORIGINAL"
        IKSplineConstr.xz_scale_mode = "BONE_ORIGINAL"
        
        # Final settings cleanup
        curveData.resolution_u = settings.ik_spline_resolution
        
        # Go back to pose mode
        context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='POSE')
        
        # Final messag, if no warning were raised during the execution
        if warning == 0:
            self.report({'INFO'}, 'MustardTools - IK spline rig successfully created.')
        
        return {'FINISHED'}
    
class MUSTARDTOOLS_OT_IKSpline_Clean(bpy.types.Operator):
    """This tool will remove the IK spline.\nSelect a bone with an IK constraint to enable the tool.\nA confirmation box will appear"""
    bl_idname = "mustardui.ik_splineclean"
    bl_label = "Clean"
    bl_options = {'REGISTER','UNDO'}
    
    delete_bones: BoolProperty(name='Delete bones',
        description="Delete controller and pole bones",
        default=True
    )
    reset_bendy: BoolProperty(name='Reset Bendy Bones',
        description="Reset bendy bones to standard bones",
        default=True
    )
    
    @classmethod
    def poll(cls, context):
        if context.mode != "POSE" or bpy.context.selected_pose_bones == None:
            return False
        else:
            
            chain_bones = bpy.context.selected_pose_bones
            
            if len(chain_bones) < 1:
                return False
            else:
                abort_aa = True
                for bone in chain_bones:
                    for constraint in bone.constraints:
                        if constraint.type == 'SPLINE_IK':
                            abort_aa = False
                            break
                
                if abort_aa:
                    return False
                else:
                    return True

    def execute(self, context):
        
        settings = bpy.context.scene.mustardtools_settings
        
        arm = bpy.context.object
        chain_bones = bpy.context.selected_pose_bones
        
        e = []
        
        removed_constr = 0
        removed_bones = 0
        
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        
        if self.reset_bendy:
            for bone in chain_bones:
                arm.data.edit_bones[bone.name].bbone_segments = 1
            arm.data.display_type = "OCTAHEDRAL"
            if settings.ms_debug:
                print("MustardTools IK Spline - Bendy bones resetted")
        
        bpy.ops.object.mode_set(mode='POSE', toggle=False)

        for bone in chain_bones:
            for constraint in bone.constraints:
                if constraint.type == 'SPLINE_IK':
                    
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                        
                        if constraint.target != None:
                            IKCurve = constraint.target
                            for hook_mod in IKCurve.modifiers:
                                if hook_mod.object != None:
                                    
                                    IKEmpty = hook_mod.object
                                    e.append(IKEmpty.name)
                                    
                                    if self.delete_bones:
                                        for e_constraint in IKEmpty.constraints:
                                            if e_constraint.type=="COPY_TRANSFORMS":
                                                if e_constraint.target != None and e_constraint.subtarget != None and e_constraint.subtarget != "":
                                                    IKArm = e_constraint.target
                                                    IKBone = IKArm.data.edit_bones[e_constraint.subtarget]
                                                    IKBone_name = IKBone.name
                                                    IKArm.data.edit_bones.remove(IKBone)
                                                    if settings.ms_debug:
                                                        print("MustardTools IK Spline - Bone " + IKBone_name + " removed from Armature " + IKArm.name)
                                                    removed_bones = removed_bones + 1
                                    
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.object.select_all(action='DESELECT')
                        for empty_name in e:
                            empty = bpy.data.objects[empty_name]
                            bpy.context.collection.objects.unlink(empty)
                            bpy.data.objects.remove(empty)
                    
                        bpy.ops.object.select_all(action='DESELECT')
                        IKCurve = constraint.target
                        IKCurve_name = IKCurve.name
                        bpy.context.collection.objects.unlink(IKCurve)
                        bpy.data.objects.remove(IKCurve)
                        if settings.ms_debug:
                            print("MustardTools IK Spline - Curve " + IKCurve_name + " removed.")
                        
                        bpy.ops.object.mode_set(mode='POSE')
                    
                        IKConstr_name = constraint.name
                        bone.constraints.remove(constraint)
                        removed_constr = removed_constr + 1
                        if settings.ms_debug:
                            print("MustardTools IK Spline - Constraint " + IKConstr_name + " removed from " + bone.name + ".")
        
        if self.delete_bones:
            self.report({'INFO'}, 'MustardTools - '+ str(removed_constr) +' IK constraints and '+ str(removed_bones) +' Bones successfully removed.')
        else:
            self.report({'INFO'}, 'MustardTools - '+ str(removed_constr) +' IK constraints successfully removed.')
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        
        return context.window_manager.invoke_props_dialog(self)
            
    def draw(self, context):
        
        layout = self.layout
        
        chain_bones = bpy.context.selected_pose_bones
        
        IK_num = 0
        IK_num_nMUI = 0
        for bone in chain_bones:
            for constraint in bone.constraints:
                if constraint.type == 'SPLINE_IK':
                    IK_num = IK_num + 1
                    if "MustardTools" not in constraint.name:
                        IK_num_nMUI = IK_num_nMUI + 1
        
        box = layout.box()
        box.prop(self, "delete_bones")
        box.prop(self, "reset_bendy")
        box = layout.box()
        box.label(text="Will be removed:", icon="ERROR")
        box.label(text="        - " + str(IK_num) + " Spline IK constraints.")
        box.label(text="        - " + str(IK_num_nMUI) + " of which are not Mustard Tools generated.")

# ------------------------------------------------------------------------
#    Mouth Controller
# ------------------------------------------------------------------------

class MUSTARDTOOLS_OT_MouthController(bpy.types.Operator):
    """This tool will create a mouth controller.\nThe control will be assigned to a bone that you should create in advance, and selected in the Controller Settings.\nRun the tool in Pose mode"""
    bl_idname = "mustardui.mouth_controller"
    bl_label = "Apply"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):
        
        settings = bpy.context.scene.mustardtools_settings
        armature = settings.mouth_controller_armature
        armature_controller = settings.mouth_controller_armature_controller
        bone_controller = settings.mouth_controller_bone
        
        if context.mode != "POSE" or armature == None or armature_controller == None or bone_controller == "":
            return False
        if settings.mouth_controller_mirror and (settings.mouth_controller_jaw_bone == "" or settings.mouth_controller_center_bone_top == "" or settings.mouth_controller_center_bone_bot == "" or settings.mouth_controller_edge_bone_L == "" or settings.mouth_controller_middle1_bone_L_top == "" or settings.mouth_controller_middle1_bone_L_bot == "" or  (settings.mouth_controller_number_bones > 1 and (settings.mouth_controller_middle2_bone_L_top == "" or settings.mouth_controller_middle2_bone_L_bot == ""))):
            return False
        elif not settings.mouth_controller_mirror and (settings.mouth_controller_jaw_bone == "" or settings.mouth_controller_center_bone_top == "" or settings.mouth_controller_center_bone_bot == "" or settings.mouth_controller_edge_bone_L == "" or settings.mouth_controller_edge_bone_R == "" or settings.mouth_controller_middle1_bone_L_top == "" or settings.mouth_controller_middle1_bone_R_top == "" or settings.mouth_controller_middle1_bone_L_bot == "" or settings.mouth_controller_middle1_bone_R_bot == "" or  (settings.mouth_controller_number_bones > 1 and (settings.mouth_controller_middle2_bone_L_top == "" or settings.mouth_controller_middle2_bone_R_top == "" or settings.mouth_controller_middle2_bone_L_bot == "" or settings.mouth_controller_middle2_bone_R_bot == ""))):
            return False
        else:
            return True

    def execute(self, context):
        
        settings = bpy.context.scene.mustardtools_settings
        mouth_controller_name = settings.ms_naming_prefix + "_MouthControllerConstraint"
        mouth_controller_rot_name = settings.ms_naming_prefix + "_MouthControllerConstraintRot"
        mouth_controller_floor_name = settings.ms_naming_prefix + "_MouthControllerFloor"
        mirror = settings.mouth_controller_mirror
        
        floor_offset = settings.mouth_controller_floor_offset
        transform_min = 0.1
        transform_ratio = settings.mouth_controller_transform_ratio
        middle1_correction_x = settings.mouth_controller_middle1_bone_correction_x
        middle2_correction_x = settings.mouth_controller_middle2_bone_correction_x
        middle1_correction_z = settings.mouth_controller_middle1_bone_correction_z
        middle2_correction_z = settings.mouth_controller_middle2_bone_correction_z
        edge_correction_z = settings.mouth_controller_edge_bone_correction_z
        center_correction_z = settings.mouth_controller_center_bone_correction_z
                
        armature = settings.mouth_controller_armature
        armature_controller = settings.mouth_controller_armature_controller
        controller_bone = settings.mouth_controller_bone
        
        # Jaw bone
        bone = settings.mouth_controller_jaw_bone
        if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_name])<1:
            constr = armature.pose.bones[bone].constraints.new('TRANSFORM')
            constr.name = mouth_controller_name
        else:
            constr = armature.pose.bones[bone].constraints[mouth_controller_name]
        constr.target = armature_controller
        constr.subtarget = controller_bone
        constr.use_motion_extrapolate = True
        constr.target_space = "LOCAL"
        constr.owner_space = "LOCAL"
        constr.from_min_y = transform_min
        constr.map_to_z_from = "Y"
        constr.to_min_z = -transform_min
        
        # Edge bones
        bone = settings.mouth_controller_edge_bone_L
        if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_name])<1:
            constr = armature.pose.bones[bone].constraints.new('TRANSFORM')
            constr.name = mouth_controller_name
        else:
            constr = armature.pose.bones[bone].constraints[mouth_controller_name]
        constr.target = armature_controller
        constr.subtarget = controller_bone
        constr.use_motion_extrapolate = True
        constr.target_space = "LOCAL"
        constr.owner_space = "LOCAL"
        
        constr.from_min_x = transform_min
        constr.map_to_z_from = "X"
        constr.to_min_z = -transform_min
        
        constr.from_min_z = transform_min
        constr.map_to_x_from = "Z"
        constr.to_min_x = transform_min * edge_correction_z
        
        if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_rot_name])<1:
            constr = armature.pose.bones[bone].constraints.new('TRANSFORM')
            constr.name = mouth_controller_rot_name
        else:
            constr = armature.pose.bones[bone].constraints[mouth_controller_rot_name]
        constr.target = armature_controller
        constr.subtarget = controller_bone
        constr.use_motion_extrapolate = True
        constr.target_space = "LOCAL"
        constr.owner_space = "LOCAL"
        
        constr.map_from = "ROTATION"
        
        constr.from_min_z_rot = 90/180*3.14
        constr.map_to_y_from = "Z"
        constr.to_min_y = transform_min
        
        
        if mirror:
            string_check = settings.mouth_controller_edge_bone_L[len(settings.mouth_controller_edge_bone_L)-1]
            if string_check=="l":
                bone = settings.mouth_controller_edge_bone_L[:-1]+"r"
            elif string_check=="r":
                bone = settings.mouth_controller_edge_bone_L[:-1]+"l"
            else:
                self.report({'ERROR'}, 'MustardTools - Bones are not correctly named for Mirror option.')
                return {'FINISHED'}
        else:
            bone = settings.mouth_controller_edge_bone_R
        if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_name])<1:
            constr = armature.pose.bones[bone].constraints.new('TRANSFORM')
            constr.name = mouth_controller_name
        else:
            constr = armature.pose.bones[bone].constraints[mouth_controller_name]
        constr.target = armature_controller
        constr.subtarget = controller_bone
        constr.use_motion_extrapolate = True
        constr.target_space = "LOCAL"
        constr.owner_space = "LOCAL"
        
        constr.from_min_x = -transform_min
        constr.map_to_z_from = "X"
        constr.to_min_z = transform_min
        
        constr.from_min_z = transform_min
        constr.map_to_x_from = "Z"
        constr.to_min_x = -transform_min * edge_correction_z
        
        if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_rot_name])<1:
            constr = armature.pose.bones[bone].constraints.new('TRANSFORM')
            constr.name = mouth_controller_rot_name
        else:
            constr = armature.pose.bones[bone].constraints[mouth_controller_rot_name]
        constr.target = armature_controller
        constr.subtarget = controller_bone
        constr.use_motion_extrapolate = True
        constr.target_space = "LOCAL"
        constr.owner_space = "LOCAL"
        
        constr.map_from = "ROTATION"
        
        constr.from_min_z_rot = 90/180*3.14
        constr.map_to_y_from = "Z"
        constr.to_min_y = transform_min
        
        
        # Center bones
        bone = settings.mouth_controller_center_bone_top
        if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_name])<1:
            constr = armature.pose.bones[bone].constraints.new('TRANSFORM')
            constr.name = mouth_controller_name
        else:
            constr = armature.pose.bones[bone].constraints[mouth_controller_name]
        constr.target = armature_controller
        constr.subtarget = controller_bone
        constr.use_motion_extrapolate = True
        constr.target_space = "LOCAL"
        constr.owner_space = "LOCAL"
        
        constr.from_min_z = transform_min
        constr.map_to_x_from = "Z"
        constr.to_min_x = transform_min * center_correction_z
        
        if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_floor_name])<1:
            constr = armature.pose.bones[bone].constraints.new('FLOOR')
            constr.name = mouth_controller_floor_name
        else:
            constr = armature.pose.bones[bone].constraints[mouth_controller_floor_name]
        constr.target = armature
        constr.subtarget = settings.mouth_controller_center_bone_bot
        constr.offset = floor_offset
        
        
        bone = settings.mouth_controller_center_bone_bot
        if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_name])<1:
            constr = armature.pose.bones[bone].constraints.new('TRANSFORM')
            constr.name = mouth_controller_name
        else:
            constr = armature.pose.bones[bone].constraints[mouth_controller_name]
        constr.target = armature_controller
        constr.subtarget = controller_bone
        constr.use_motion_extrapolate = True
        constr.target_space = "LOCAL"
        constr.owner_space = "LOCAL"
        
        constr.from_min_z = transform_min
        constr.map_to_x_from = "Z"
        constr.to_min_x = transform_min * center_correction_z
        
        
        # Middle bones 1 top
        bone = settings.mouth_controller_middle1_bone_L_top
        if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_name])<1:
            constr = armature.pose.bones[bone].constraints.new('TRANSFORM')
            constr.name = mouth_controller_name
        else:
            constr = armature.pose.bones[bone].constraints[mouth_controller_name]
        constr.target = armature_controller
        constr.subtarget = controller_bone
        constr.use_motion_extrapolate = True
        constr.target_space = "LOCAL"
        constr.owner_space = "LOCAL"
        
        constr.from_min_x = transform_min
        constr.map_to_z_from = "X"
        constr.to_min_z = -transform_min * middle1_correction_x
        
        constr.from_min_z = transform_min
        constr.map_to_x_from = "Z"
        constr.to_min_x = transform_min * middle1_correction_z
        
        if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_floor_name])<1:
            constr = armature.pose.bones[bone].constraints.new('FLOOR')
            constr.name = mouth_controller_floor_name
        else:
            constr = armature.pose.bones[bone].constraints[mouth_controller_floor_name]
        constr.target = armature
        constr.subtarget = settings.mouth_controller_middle1_bone_L_bot
        constr.offset = floor_offset
        
        if mirror:
            string_check = settings.mouth_controller_middle1_bone_L_top[len(settings.mouth_controller_middle1_bone_L_top)-1]
            if string_check=="l":
                bone = settings.mouth_controller_middle1_bone_L_top[:-1]+"r"
            elif string_check=="r":
                bone = settings.mouth_controller_middle1_bone_L_top[:-1]+"l"
            else:
                self.report({'ERROR'}, 'MustardTools - Bones are not correctly named for Mirror option.')
                return {'FINISHED'}
        else:
            bone = mouth_controller_middle1_bone_R_top
        if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_name])<1:
            constr = armature.pose.bones[bone].constraints.new('TRANSFORM')
            constr.name = mouth_controller_name
        else:
            constr = armature.pose.bones[bone].constraints[mouth_controller_name]
        constr.target = armature_controller
        constr.subtarget = controller_bone
        constr.use_motion_extrapolate = True
        constr.target_space = "LOCAL"
        constr.owner_space = "LOCAL"
        
        constr.from_min_x = -transform_min
        constr.map_to_z_from = "X"
        constr.to_min_z = transform_min * middle1_correction_x
        
        constr.from_min_z = transform_min
        constr.map_to_x_from = "Z"
        constr.to_min_x = -transform_min * middle1_correction_z
        
        if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_floor_name])<1:
            constr = armature.pose.bones[bone].constraints.new('FLOOR')
            constr.name = mouth_controller_floor_name
        else:
            constr = armature.pose.bones[bone].constraints[mouth_controller_floor_name]
        constr.target = armature
        if mirror:
            string_check = settings.mouth_controller_middle1_bone_L_bot[len(settings.mouth_controller_middle1_bone_L_bot)-1]
            if string_check=="l":
                constr.subtarget = settings.mouth_controller_middle1_bone_L_bot[:-1]+"r"
            elif string_check=="r":
                constr.subtarget = settings.mouth_controller_middle1_bone_L_bot[:-1]+"l"
            else:
                self.report({'ERROR'}, 'MustardTools - Bones are not correctly named for Mirror option.')
                return {'FINISHED'}
        else:
            constr.subtarget = mouth_controller_middle1_bone_R_bot
        constr.offset = floor_offset
        
        # Middle bones 1 bottom
        bone = settings.mouth_controller_middle1_bone_L_bot
        if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_name])<1:
            constr = armature.pose.bones[bone].constraints.new('TRANSFORM')
            constr.name = mouth_controller_name
        else:
            constr = armature.pose.bones[bone].constraints[mouth_controller_name]
        constr.target = armature_controller
        constr.subtarget = controller_bone
        constr.use_motion_extrapolate = True
        constr.target_space = "LOCAL"
        constr.owner_space = "LOCAL"
        
        constr.from_min_x = transform_min
        constr.map_to_z_from = "X"
        constr.to_min_z = -transform_min * middle1_correction_x
        
        constr.from_min_z = transform_min
        constr.map_to_x_from = "Z"
        constr.to_min_x = transform_min * middle1_correction_z
        
        if mirror:
            string_check = settings.mouth_controller_middle1_bone_L_bot[len(settings.mouth_controller_middle1_bone_L_bot)-1]
            if string_check=="l":
                bone = settings.mouth_controller_middle1_bone_L_bot[:-1]+"r"
            elif string_check=="r":
                bone = settings.mouth_controller_middle1_bone_L_bot[:-1]+"l"
            else:
                self.report({'ERROR'}, 'MustardTools - Bones are not correctly named for Mirror option.')
                return {'FINISHED'}
        else:
            bone = mouth_controller_middle1_bone_R_bot
        if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_name])<1:
            constr = armature.pose.bones[bone].constraints.new('TRANSFORM')
            constr.name = mouth_controller_name
        else:
            constr = armature.pose.bones[bone].constraints[mouth_controller_name]
        constr.target = armature_controller
        constr.subtarget = controller_bone
        constr.use_motion_extrapolate = True
        constr.target_space = "LOCAL"
        constr.owner_space = "LOCAL"
        
        constr.from_min_x = -transform_min
        constr.map_to_z_from = "X"
        constr.to_min_z = transform_min * middle1_correction_x
        
        constr.from_min_z = transform_min
        constr.map_to_x_from = "Z"
        constr.to_min_x = -transform_min * middle1_correction_z
        
        
        if settings.mouth_controller_number_bones == 2:
            # Middle bones 2 top
            bone = settings.mouth_controller_middle2_bone_L_top
            if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_name])<1:
                constr = armature.pose.bones[bone].constraints.new('TRANSFORM')
                constr.name = mouth_controller_name
            else:
                constr = armature.pose.bones[bone].constraints[mouth_controller_name]
            constr.target = armature_controller
            constr.subtarget = controller_bone
            constr.use_motion_extrapolate = True
            constr.target_space = "LOCAL"
            constr.owner_space = "LOCAL"
            
            constr.from_min_x = transform_min
            constr.map_to_z_from = "X"
            constr.to_min_z = -transform_min * middle2_correction_x
            
            constr.from_min_z = transform_min
            constr.map_to_x_from = "Z"
            constr.to_min_x = transform_min * middle2_correction_z
            
            if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_floor_name])<1:
                constr = armature.pose.bones[bone].constraints.new('FLOOR')
                constr.name = mouth_controller_floor_name
            else:
                constr = armature.pose.bones[bone].constraints[mouth_controller_floor_name]
            constr.target = armature
            constr.subtarget = settings.mouth_controller_middle2_bone_L_bot
            constr.offset = floor_offset
            
            if mirror:
                string_check = settings.mouth_controller_middle2_bone_L_top[len(settings.mouth_controller_middle2_bone_L_top)-1]
                if string_check=="l":
                    bone = settings.mouth_controller_middle2_bone_L_top[:-1]+"r"
                elif string_check=="r":
                    bone = settings.mouth_controller_middle2_bone_L_top[:-1]+"l"
                else:
                    self.report({'ERROR'}, 'MustardTools - Bones are not correctly named for Mirror option.')
                    return {'FINISHED'}
            else:
                bone = mouth_controller_middle2_bone_R_top
            if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_name])<1:
                constr = armature.pose.bones[bone].constraints.new('TRANSFORM')
                constr.name = mouth_controller_name
            else:
                constr = armature.pose.bones[bone].constraints[mouth_controller_name]
            constr.target = armature_controller
            constr.subtarget = controller_bone
            constr.use_motion_extrapolate = True
            constr.target_space = "LOCAL"
            constr.owner_space = "LOCAL"
            
            constr.from_min_x = -transform_min
            constr.map_to_z_from = "X"
            constr.to_min_z = transform_min * middle2_correction_x
            
            constr.from_min_z = transform_min
            constr.map_to_x_from = "Z"
            constr.to_min_x = -transform_min * middle2_correction_z
            
            if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_floor_name])<1:
                constr = armature.pose.bones[bone].constraints.new('FLOOR')
                constr.name = mouth_controller_floor_name
            else:
                constr = armature.pose.bones[bone].constraints[mouth_controller_floor_name]
            constr.target = armature
            if mirror:
                string_check = settings.mouth_controller_middle2_bone_L_bot[len(settings.mouth_controller_middle2_bone_L_bot)-1]
                if string_check=="l":
                    constr.subtarget = settings.mouth_controller_middle2_bone_L_bot[:-1]+"r"
                elif string_check=="r":
                    constr.subtarget = settings.mouth_controller_middle2_bone_L_bot[:-1]+"l"
                else:
                    self.report({'ERROR'}, 'MustardTools - Bones are not correctly named for Mirror option.')
                    return {'FINISHED'}
            else:
                constr.subtarget = mouth_controller_middle2_bone_R_bot
            constr.offset = floor_offset
            
            
            # Middle bones 2 bottom
            bone = settings.mouth_controller_middle2_bone_L_bot
            if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_name])<1:
                constr = armature.pose.bones[bone].constraints.new('TRANSFORM')
                constr.name = mouth_controller_name
            else:
                constr = armature.pose.bones[bone].constraints[mouth_controller_name]
            constr.target = armature_controller
            constr.subtarget = controller_bone
            constr.use_motion_extrapolate = True
            constr.target_space = "LOCAL"
            constr.owner_space = "LOCAL"
            
            constr.from_min_x = transform_min
            constr.map_to_z_from = "X"
            constr.to_min_z = -transform_min * middle2_correction_x
            
            constr.from_min_z = transform_min
            constr.map_to_x_from = "Z"
            constr.to_min_x = transform_min * middle2_correction_z
            
            if mirror:
                string_check = settings.mouth_controller_middle2_bone_L_bot[len(settings.mouth_controller_middle2_bone_L_bot)-1]
                if string_check=="l":
                    bone = settings.mouth_controller_middle2_bone_L_bot[:-1]+"r"
                elif string_check=="r":
                    bone = settings.mouth_controller_middle2_bone_L_bot[:-1]+"l"
                else:
                    self.report({'ERROR'}, 'MustardTools - Bones are not correctly named for Mirror option.')
                    return {'FINISHED'}
            else:
                bone = mouth_controller_middle2_bone_R_bot
            if len([m for m in armature.pose.bones[bone].constraints if m.name == mouth_controller_name])<1:
                constr = armature.pose.bones[bone].constraints.new('TRANSFORM')
                constr.name = mouth_controller_name
            else:
                constr = armature.pose.bones[bone].constraints[mouth_controller_name]
            constr.target = armature_controller
            constr.subtarget = controller_bone
            constr.use_motion_extrapolate = True
            constr.target_space = "LOCAL"
            constr.owner_space = "LOCAL"
            
            constr.from_min_x = -transform_min
            constr.map_to_z_from = "X"
            constr.to_min_z = transform_min * middle2_correction_x
            
            constr.from_min_z = transform_min
            constr.map_to_x_from = "Z"
            constr.to_min_x = -transform_min * middle2_correction_z
        
        # Controller bone limits
        bone = controller_bone
        if len([m for m in armature_controller.pose.bones[bone].constraints if m.name == mouth_controller_name])<1:
            constr = armature_controller.pose.bones[bone].constraints.new('LIMIT_LOCATION')
            constr.name = mouth_controller_name
        else:
            constr = armature_controller.pose.bones[bone].constraints[mouth_controller_name]
        constr.owner_space = "LOCAL"
        
        constr.use_max_x = True
        constr.max_x = transform_min/10
        constr.use_min_x = True
        constr.min_x = -transform_min/15
        
        constr.use_max_y = True
        constr.max_y = transform_min/20
        constr.use_min_y = True
        constr.min_y = -transform_min/5
        
        constr.use_max_z = True
        constr.max_z = transform_min/15
        constr.use_min_z = True
        constr.min_z = -transform_min/15
        
        
        if len([m for m in armature_controller.pose.bones[bone].constraints if m.name == mouth_controller_rot_name])<1:
            constr = armature_controller.pose.bones[bone].constraints.new('LIMIT_ROTATION')
            constr.name = mouth_controller_rot_name
        else:
            constr = armature_controller.pose.bones[bone].constraints[mouth_controller_rot_name]
        constr.owner_space = "LOCAL"
        
        constr.use_limit_x = True
        constr.max_x = 0.
        constr.min_x = 0.
        
        constr.use_limit_y = True
        constr.max_y = 0.
        constr.min_y = 0.
        
        constr.use_limit_z = True
        constr.max_z = 20/180*3.14
        constr.min_z = -20/180*3.14
        
        # Apply custom shape
        controller_bone = armature_controller.pose.bones[bone]
        controller_bone.custom_shape = settings.mouth_controller_bone_custom_shape
        
        
        self.report({'INFO'}, 'MustardTools - Mouth Controller successfully created.')
        
        return {'FINISHED'}


class MUSTARDTOOLS_OT_MouthControllerClean(bpy.types.Operator):
    """This tool will clean all setting related to a mouth controller generated by this addon.\nThe armatures which are cleaned are the ones set in the settings.\nRun the tool in Pose mode"""
    bl_idname = "mustardui.mouth_controller_clean"
    bl_label = "Apply"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):
        
        settings = bpy.context.scene.mustardtools_settings
        armature = settings.mouth_controller_armature
        armature_controller = settings.mouth_controller_armature_controller
        bone_controller = settings.mouth_controller_bone
        
        if context.mode != "POSE" or armature == None or armature_controller == None or bone_controller == "":
            return False
        if settings.mouth_controller_mirror and (settings.mouth_controller_jaw_bone == "" and settings.mouth_controller_center_bone_top == "" or settings.mouth_controller_center_bone_bot == "" or settings.mouth_controller_edge_bone_L == "" or settings.mouth_controller_middle1_bone_L_top == "" or settings.mouth_controller_middle1_bone_L_bot == "" or  (settings.mouth_controller_number_bones > 1 and (settings.mouth_controller_middle2_bone_L_top == "" or settings.mouth_controller_middle2_bone_L_bot == ""))):
            return False
        else:
            return True

    def execute(self, context):
        
        settings = bpy.context.scene.mustardtools_settings
        mouth_controller_name = settings.ms_naming_prefix + "_MouthControllerConstraint"
        mouth_controller_rot_name = settings.ms_naming_prefix + "_MouthControllerConstraintRot"
        mouth_controller_floor_name = settings.ms_naming_prefix + "_MouthControllerFloor"
        
        armature = settings.mouth_controller_armature
        armature_controller = settings.mouth_controller_armature_controller
        controller_bone = settings.mouth_controller_bone
        
        removed_constr = 0
        for bone in armature.pose.bones:
            for constr in bone.constraints:
                if constr.name == mouth_controller_name or constr.name == mouth_controller_rot_name or constr.name == mouth_controller_floor_name:
                    if settings.ms_debug:
                        print("MustardTools Mouth Controller - Constraint "+constr.name+" removed from "+bone.name)
                    bone.constraints.remove(constr)
                    removed_constr = removed_constr + 1
        
        controller_bone = armature_controller.pose.bones[controller_bone]
        controller_bone.custom_shape = None
        
        self.report({'INFO'}, 'MustardTools - '+ str(removed_constr) +' constraints successfully removed.')
        
        return {'FINISHED'}

class MUSTARDTOOLS_OT_MouthControllerSmartSearch(bpy.types.Operator):
    """This tool will search for standard names of the lips bones.\nRun the tool in Pose mode"""
    bl_idname = "mustardui.mouth_controller_search"
    bl_label = "Search"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls, context):
        
        settings = bpy.context.scene.mustardtools_settings
        armature = settings.mouth_controller_armature
        
        if context.mode != "POSE" or armature == None:
            return False
        else:
            return True

    def execute(self, context):
        
        settings = bpy.context.scene.mustardtools_settings
        armature = settings.mouth_controller_armature
        
        convention = 0
        for bone in armature.pose.bones:
            if bone.name == "c_jawbone.x":
                convention = 1 # auto-rig
                break
        
        if convention==1:
            settings.mouth_controller_mirror = True
            settings.mouth_controller_jaw_bone = "c_jawbone.x"
            settings.mouth_controller_center_bone_top = "c_lips_top.x"
            settings.mouth_controller_center_bone_bot = "c_lips_bot.x"
            settings.mouth_controller_edge_bone_L = "c_lips_smile.r"
            settings.mouth_controller_middle1_bone_L_top = "c_lips_top.l"
            settings.mouth_controller_middle1_bone_L_bot = "c_lips_bot.l"
            settings.mouth_controller_middle2_bone_L_top = "c_lips_top_01.r"
            settings.mouth_controller_middle2_bone_L_bot = "c_lips_bot_01.l"
            self.report({'INFO'}, 'MustardTools - Auto-rig convention used to fill properties.')
        else:
            self.report({'INFO'}, 'MustardTools - No convention found. Insert bones manually.')
        
        
        return {'FINISHED'}

# ------------------------------------------------------------------------
#    Slide Keyframes
# ------------------------------------------------------------------------
#
# Slide Keyframes tool (thanks to @KDE for the idea)
#
# Consider the following keyframes configuration
# A ----- B ------ C ------ D ----- E
# Suppose I want to scale B ------ C,
# but I want to keep the relationship from C to D as 6 frames.
# Scaling B -> C in Blender would result in:
# A ------ B ------------ D --- C --- E
# This tool will scale from B to C and preserve the relations between the remaining keyframes: 
# A ------ B --------------- C ------ D ------ E

class MUSTARDTOOLS_OT_SlideKeyframes(bpy.types.Operator):
    
    """Tool to scale keyframes, sliding the others accordingly"""
    bl_idname = "mustardui.anim_slidekeyframes"
    bl_label = "Slide Keyframes"
    bl_options = {'REGISTER','UNDO','GRAB_CURSOR','BLOCKING'}
    
    @classmethod
    def poll(cls, context):
        
        settings = bpy.context.scene.mustardtools_settings
        
        if settings.slide_keyframes_application == '0':
        
            obj = bpy.context.active_object
        
            if context.active_object == None:
                if settings.ms_debug:
                    print("MustardTools Slide Keyframes - No object selected")
                return False
        
            try:
                action = obj.animation_data.action
                
                check = False
                check_value = 0
                    
                for fcurve in action.fcurves:
                    for p in fcurve.keyframe_points:
                        if p.select_control_point:
                            if check_value == 0:
                                check_value = p.co[0]
                                continue
                            else:
                                if p.co[0] != check_value:
                                    check = True
                                    break
                
                if not check and settings.ms_debug:
                    print("MustardTools Slide Keyframes - The keyframe should belong to the object selected")
                    
                return check
                
            except:
                if settings.ms_debug:
                    print("MustardTools Slide Keyframes - No keyframes found on the object")
                return False
        
        elif settings.slide_keyframes_application == '1':
            
            objs = bpy.context.selected_objects
            
            if objs == []:
                if settings.ms_debug:
                    print("MustardTools Slide Keyframes - No object selected")
                return False
            
            check = False
            check_value = 0
            
            for obj in objs:
                
                try:
                    action = obj.animation_data.action
                    
                    for fcurve in action.fcurves:
                        for p in fcurve.keyframe_points:
                            if p.select_control_point:
                                if check_value == 0:
                                    check_value = p.co[0]
                                    continue
                                else:
                                    if p.co[0] != check_value:
                                        check = True
                                        break
                    
                except:
                    if settings.ms_debug:
                        print("MustardTools Slide Keyframes - Object "+obj.name+" neglected. No keyframes found")
            
            return check
        
        elif settings.slide_keyframes_application == '2':
            
            objs = bpy.data.objects
            
            if objs == []:
                if settings.ms_debug:
                    print("MustardTools Slide Keyframes - No object in the scene")
                return False
            
            for obj in objs:
                
                try:
                    action = obj.animation_data.action
                    
                    check = False
                    
                    for fcurve in action.fcurves:
                        for p in fcurve.keyframe_points:
                            if p.select_control_point:
                                check = True
                                break
                    
                    return check
                    
                except:
                    if settings.ms_debug:
                        print("MustardTools Slide Keyframes - Object "+obj.name+" neglected. No keyframes found")
        
        return True
    
    def execute(self, context):
        
        settings = bpy.context.scene.mustardtools_settings
        
        if settings.slide_keyframes_application == '0':

            obj = bpy.context.active_object
            action = obj.animation_data.action
        
            self.action_end_scaled = self.value / 10.

            for fcurve in action.fcurves:
                for p in fcurve.keyframe_points:
                    if p.co[0]>self.action_end:
                        p.co[0] = p.co[0] + (self.action_end_scaled - self.action_end)
            
            if self.action_end - self.action_start > 0:
                scale_factor = (self.action_end_scaled - self.action_end) / (self.action_end - self.action_start)
                
                for fcurve in action.fcurves:
                    for p in fcurve.keyframe_points:
                        if p.co[0]>=self.action_start and p.co[0]<=self.action_end:
                            p.co[0] = p.co[0] + (p.co[0] - self.action_start) * scale_factor
            else:
                self.error = True
            
            self.action_end = self.action_end_scaled
        
        else:
        
            if settings.slide_keyframes_application == '1':
                objs = bpy.context.selected_objects
            else:
                objs = bpy.data.objects
            
            self.action_end_scaled = self.value / 10.
            
            for obj in objs:
                
                try:
                    action = obj.animation_data.action

                    for fcurve in action.fcurves:
                        for p in fcurve.keyframe_points:
                            if p.co[0]>self.action_end:
                                p.co[0] = p.co[0] + (self.action_end_scaled - self.action_end)
            
                    if self.action_end - self.action_start > 0:
                        scale_factor = (self.action_end_scaled - self.action_end) / (self.action_end - self.action_start)
                
                        for fcurve in action.fcurves:
                            for p in fcurve.keyframe_points:
                                if p.co[0]>=self.action_start and p.co[0]<=self.action_end:
                                    p.co[0] = p.co[0] + (p.co[0] - self.action_start) * scale_factor
                    else:
                        self.error = True
                        break
                
                except:
                    continue
            
            self.action_end = self.action_end_scaled
        
        return {'FINISHED'}
    
    def modal(self, context, event):
        
        settings = bpy.context.scene.mustardtools_settings
        
        if self.error:
            self.report({'ERROR'}, 'MustardTools - Cannot slide those keyframes. Undo and retry.')
            return {'CANCELLED'}
        
        if event.type == 'MOUSEMOVE':  # Apply
            if (event.mouse_prev_x != event.mouse_x):
                self.value = event.mouse_region_x
                self.execute(context)
        
        elif event.type == 'LEFTMOUSE':  # Confirm
            self.report({'INFO'}, 'MustardTools - Slide complete.')
            if settings.ms_debug:
                scale_factor = 1. + (self.action_end_scaled - self.init_action_end) / (self.init_action_end - self.action_start)
                print("MustardTools Slide Keyframes - Scaling with factor " + str(scale_factor))
            return {'FINISHED'}
        
        elif event.type in {'RIGHTMOUSE', 'ESC'}:  # Cancel
            self.report({'INFO'}, 'MustardTools - Undo to cancel.')   
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        
        settings = bpy.context.scene.mustardtools_settings
        
        self.error = False
        
        self.action_start = 1048574
        self.action_end = - 1048574
        
        if settings.slide_keyframes_application == '0':
        
            obj = bpy.context.active_object
            action = obj.animation_data.action
            
            for fcurve in action.fcurves:
                for p in fcurve.keyframe_points:
                    if p.select_control_point and self.action_start > p.co[0]:
                        self.action_start = p.co[0]
                    if p.select_control_point and self.action_end < p.co[0]:
                        self.action_end = p.co[0]
            if settings.ms_debug:
                print("MustardTools Slide Keyframes - Starting point found at " + str(self.action_start))
                print("MustardTools Slide Keyframes - Ending point found at " + str(self.action_start))
            
            self.init_action_end = self.action_end
            
            self.action_end_scaled = self.action_end
        
        else:
        
            if settings.slide_keyframes_application == '1':
                objs = bpy.context.selected_objects
            else:
                objs = bpy.data.objects
            
            for obj in objs:
                
                try:
                    action = obj.animation_data.action
                    
                    for fcurve in action.fcurves:
                        for p in fcurve.keyframe_points:
                            if p.select_control_point and self.action_start > p.co[0]:
                                self.action_start = p.co[0]
                            if p.select_control_point and self.action_end < p.co[0]:
                                self.action_end = p.co[0]
                    if settings.ms_debug:
                        print("MustardTools Slide Keyframes - Starting point found at " + str(self.action_start))
                        print("MustardTools Slide Keyframes - Ending point found at " + str(self.action_start))
                    
                    self.init_action_end = self.action_end
                    
                    self.action_end_scaled = self.action_end
                
                except:
                    if settings.ms_debug:
                        print("MustardTools Slide Keyframes - Object "+obj.name+" neglected. No keyframes found")
        
        self.value = event.mouse_region_x
        self.execute(context)

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def draw(self, context):
        self.layout.operator("message.messagebox", text = "message").message = 'Sample Text'

# ------------------------------------------------------------------------
#    OptiX compatibility
# ------------------------------------------------------------------------

class MUSTARDTOOLS_OT_OptiXCompatibility(bpy.types.Operator):
    
    """Tool to optimize the materials for OptiX renderings. The tool is non-destructive, you can revert the changes with the button in the UI"""
    bl_idname = "mustardui.optix_compatibility"
    bl_label = "OptiX Compatibility"
    bl_options = {'REGISTER','UNDO'}
    
    revert: BoolProperty(name='Revert',
        description="Revert restoring previous options",
        default=False
    )
    
    def execute(self, context):
        
        settings = bpy.context.scene.mustardtools_settings
        
        counter = 0
        
        for mat in bpy.data.materials:
            if mat.use_nodes:
                nodes = mat.node_tree.nodes
                for node in nodes:
                    if isinstance(node, bpy.types.ShaderNodeAmbientOcclusion):
                        if settings.ms_debug:
                            print("MustardTools - Node " + node.name + " found in material " + mat.name)
                        node.mute = not self.revert
                        counter = counter + 1
                    elif isinstance(node, bpy.types.ShaderNodeBevel):
                        if settings.ms_debug:
                            print("MustardTools - Node " + node.name + " found in from material " + mat.name)
                        node.mute = not self.revert
                        counter = counter + 1
        
        if not self.revert and counter > 0:
            self.report({'INFO'}, 'MustardTools - ' + str(counter) + ' nodes muted.')
        elif self.revert and counter > 0:
            self.report({'INFO'}, 'MustardTools - ' + str(counter) + ' nodes un-muted.')
        else:
            self.report({'INFO'}, 'MustardTools - No node to optimize found.')
            
        return {'FINISHED'}
    
    def draw(self, context):
        
        layout = self.layout
        
        box = layout.box()
        if self.revert:
            box.label(text="This tool is:", icon="ERROR")
            box.label(text="        - Enabling AO nodes from all materials.")
            box.label(text="        - Enabling Bevel nodes from all materials.")
        else:
            box.label(text="This tool is:", icon="ERROR")
            box.label(text="        - Muting AO nodes from all materials.")
            box.label(text="        - Muting Bevel nodes from all materials.")

# ------------------------------------------------------------------------
#    UI
# ------------------------------------------------------------------------

class MainPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Mustard Tools"
    #bl_options = {"DEFAULT_CLOSED"}


class MUSTARDTOOLS_PT_IKChain(MainPanel, bpy.types.Panel):
    bl_idname = "MUSTARDTOOLS_PT_IKChain"
    bl_label = "IK Chain"

    def draw(self, context):
        
        layout = self.layout
        settings = bpy.context.scene.mustardtools_settings
        
        box=layout.box()
        box.label(text="Main settings", icon="CON_KINEMATIC")
        box.prop(settings,"ik_chain_last_bone_use")
        box.prop(settings,"ik_chain_bendy")
        col=box.column()
        if not settings.ik_chain_bendy:
            col.enabled=False
        col.prop(settings,"ik_chain_bendy_segments")
        row=box.row()
        row.label(text="Shape")
        row.scale_x = 3.
        row.prop(settings,"ik_chain_last_bone_custom_shape")
        layout.operator('mustardui.ik_chain', icon="ADD")
        box=layout.box()
        box.label(text="Pole settings", icon="SHADING_WIRE")
        box.prop(settings,"ik_chain_pole_angle")
        row=box.row()
        row.label(text="Shape")
        row.scale_x = 3.
        row.prop(settings,"ik_chain_pole_bone_custom_shape")
        if not settings.ik_chain_pole_status:
            layout.operator('mustardui.ik_chainpole', icon="ADD").status = True
        else:
            row=box.row(align=True)
            row.operator('mustardui.ik_chainpole', text="Confirm", icon = "CHECKMARK", depress = True).status = False
            row.scale_x=1.
            row.operator('mustardui.ik_chainpole', text="", icon = "X").cancel = True
        layout.separator()
        layout.operator('mustardui.ik_chainclean', icon="CANCEL")

class MUSTARDTOOLS_PT_IKSpline(MainPanel, bpy.types.Panel):
    bl_idname = "MUSTARDTOOLS_PT_IKSpline"
    bl_label = "IK Spline"

    def draw(self, context):
        
        layout = self.layout
        settings = bpy.context.scene.mustardtools_settings
        
        box=layout.box()
        box.label(text="Main settings", icon="CON_SPLINEIK")
        box.prop(settings,"ik_spline_number")
        if settings.ms_advanced:
            box.prop(settings,"ik_spline_resolution")
        box.prop(settings,"ik_spline_bendy")
        col=box.column()
        if not settings.ik_spline_bendy:
            col.enabled=False
        col.prop(settings,"ik_spline_bendy_segments")
        if settings.ms_advanced:
            box.label(text="Bone Custom Shapes", icon="SHADING_WIRE")
            row=box.row()
            row.label(text="First")
            row.scale_x = 3.
            row.prop(settings,"ik_spline_first_bone_custom_shape")
            row=box.row()
            row.label(text="Others")
            row.scale_x = 3.
            row.prop(settings,"ik_spline_bone_custom_shape")
        
        layout.operator('mustardui.ik_spline', icon="ADD")
        
        layout.separator()
        layout.operator('mustardui.ik_splineclean', icon="CANCEL")

class MUSTARDTOOLS_PT_MouthController(MainPanel, bpy.types.Panel):
    bl_idname = "MUSTARDTOOLS_PT_MouthController"
    bl_label = "Mouth Controller"

    def draw(self, context):
        
        layout = self.layout
        settings = bpy.context.scene.mustardtools_settings
        
        row_scale = 1.8
        
        box=layout.box()
        box.label(text="Main settings", icon="MESH_MONKEY")
        
        box.prop(settings,"mouth_controller_mirror")
        box.prop(settings,"mouth_controller_number_bones")
        if settings.ms_advanced:
            box.prop(settings,"mouth_controller_transform_ratio")
            box.prop(settings,"mouth_controller_floor_offset")
            
            box=layout.box()
            box.label(text="Corrections", icon="SETTINGS")
            row = box.row()
            row.label(text="")
            row.label(text="X")
            row.label(text="Z")
            row = box.row()
            row.label(text="Center")
            col = row.column()
            col.enabled = False
            col.prop(settings,"mouth_controller_center_bone_correction_x", text="")
            row.prop(settings,"mouth_controller_center_bone_correction_z", text="")
            row = box.row()
            row.label(text="Edge")
            col = row.column()
            col.enabled = False
            col.prop(settings,"mouth_controller_edge_bone_correction_x", text="")
            row.prop(settings,"mouth_controller_edge_bone_correction_z", text="")
            row = box.row()
            row.label(text="Middle 1")
            row.prop(settings,"mouth_controller_middle1_bone_correction_x", text="")
            row.prop(settings,"mouth_controller_middle1_bone_correction_z", text="")
            if settings.mouth_controller_number_bones>=2:
                row = box.row()
                row.label(text="Middle 2")
                row.prop(settings,"mouth_controller_middle2_bone_correction_x", text="")
                row.prop(settings,"mouth_controller_middle2_bone_correction_z", text="")
        
        box=layout.box()
        box.label(text="Controller settings", icon="SHADING_WIRE")
        row=box.row()
        row.label(text="Armature")
        row.scale_x = row_scale
        row.prop(settings,"mouth_controller_armature_controller", text="")
        if settings.mouth_controller_armature_controller != None:
            row=box.row()
            row.label(text="Bone")
            row.scale_x = row_scale-0.1
            row.prop_search(settings,"mouth_controller_bone",settings.mouth_controller_armature_controller.pose,"bones", text="")
        box.separator()
        row=box.row()
        row.label(text="Custom shape")
        row.scale_x = row_scale
        row.prop(settings,"mouth_controller_bone_custom_shape", text="")    
        
        box=layout.box()
        row=box.row()
        row.label(text="Mouth settings", icon="BONE_DATA")
        row.operator('mustardui.mouth_controller_search', icon="VIEWZOOM", text="")
        row=box.row()
        row.label(text="Armature")
        row.scale_x = row_scale
        row.prop(settings,"mouth_controller_armature", text="")
        
        if settings.mouth_controller_armature != None:
            
            row=box.row()
            row.label(text="Jaw")
            row.scale_x = row_scale-0.1
            row.prop_search(settings,"mouth_controller_jaw_bone",settings.mouth_controller_armature.pose,"bones", text="")
            row=box.row()
            row.label(text="Center Top")
            row.scale_x = row_scale-0.1
            row.prop_search(settings,"mouth_controller_center_bone_top",settings.mouth_controller_armature.pose,"bones", text="")
            row=box.row()
            row.label(text="Center Bottom")
            row.scale_x = row_scale-0.1
            row.prop_search(settings,"mouth_controller_center_bone_bot",settings.mouth_controller_armature.pose,"bones", text="")
            
            if settings.mouth_controller_mirror:
                row=box.row()
                row.label(text="Edge")
                row.scale_x = row_scale-0.1
                row.prop_search(settings,"mouth_controller_edge_bone_L",settings.mouth_controller_armature.pose,"bones", text="")
                row=box.row()
                row.label(text="Middle Top")
                row.scale_x = row_scale-0.1
                row.prop_search(settings,"mouth_controller_middle1_bone_L_top",settings.mouth_controller_armature.pose,"bones", text="")
                row=box.row()
                row.label(text="Middle Bottom")
                row.scale_x = row_scale-0.1
                row.prop_search(settings,"mouth_controller_middle1_bone_L_bot",settings.mouth_controller_armature.pose,"bones", text="")
                if settings.mouth_controller_number_bones>=2:
                    row=box.row()
                    row.label(text="Middle 2 Top")
                    row.scale_x = row_scale-0.1
                    row.prop_search(settings,"mouth_controller_middle2_bone_L_top",settings.mouth_controller_armature.pose,"bones", text="")
                    row=box.row()
                    row.label(text="Middle 2 Bottom")
                    row.scale_x = row_scale-0.1
                    row.prop_search(settings,"mouth_controller_middle2_bone_L_bot",settings.mouth_controller_armature.pose,"bones", text="")
            
            else:
                row=box.row()
                row.label(text="Edge Left")
                row.scale_x = row_scale-0.1
                row.prop_search(settings,"mouth_controller_edge_bone_L",settings.mouth_controller_armature.pose,"bones", text="")
                row=box.row()
                row.label(text="Edge Right")
                row.scale_x = row_scale-0.1
                row.prop_search(settings,"mouth_controller_edge_bone_R",settings.mouth_controller_armature.pose,"bones", text="")
                row=box.row()
                row.label(text="Middle Top Left")
                row.scale_x = row_scale-0.1
                row.prop_search(settings,"mouth_controller_middle1_bone_L_top",settings.mouth_controller_armature.pose,"bones", text="")
                row=box.row()
                row.label(text="Middle Bottom Left")
                row.scale_x = row_scale-0.1
                row.prop_search(settings,"mouth_controller_middle1_bone_L_bot",settings.mouth_controller_armature.pose,"bones", text="")
                row=box.row()
                row.label(text="Middle Top Right")
                row.scale_x = row_scale-0.1
                row.prop_search(settings,"mouth_controller_middle1_bone_R_bot",settings.mouth_controller_armature.pose,"bones", text="")
                row=box.row()
                row.label(text="Middle Bottom Right")
                row.scale_x = row_scale-0.1
                row.prop_search(settings,"mouth_controller_middle1_bone_R_top",settings.mouth_controller_armature.pose,"bones", text="")
                if settings.mouth_controller_number_bones>=2:
                    row=box.row()
                    row.label(text="Middle 2 Top Left")
                    row.scale_x = row_scale-0.1
                    row.prop_search(settings,"mouth_controller_middle2_bone_L_top",settings.mouth_controller_armature.pose,"bones", text="")
                    row=box.row()
                    row.label(text="Middle 2 Top Right")
                    row.scale_x = row_scale-0.1
                    row.prop_search(settings,"mouth_controller_middle2_bone_R_top",settings.mouth_controller_armature.pose,"bones", text="")
                    row=box.row()
                    row.label(text="Middle 2 Bottom Left")
                    row.scale_x = row_scale-0.1
                    row.prop_search(settings,"mouth_controller_middle2_bone_L_bot",settings.mouth_controller_armature.pose,"bones", text="")
                    row=box.row()
                    row.label(text="Middle 2 Bottom Right")
                    row.scale_x = row_scale-0.1
                    row.prop_search(settings,"mouth_controller_middle2_bone_R_bot",settings.mouth_controller_armature.pose,"bones", text="")
        
        layout.operator('mustardui.mouth_controller', icon="ADD")
        layout.separator()
        layout.operator('mustardui.mouth_controller_clean', icon="CANCEL", text="Clean")

class MUSTARDTOOLS_PT_VariousTools(MainPanel, bpy.types.Panel):
    bl_idname = "MUSTARDTOOLS_PT_VariousTools"
    bl_label = "Additional Tools"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        
        layout = self.layout
        settings = bpy.context.scene.mustardtools_settings
        
        box=layout.box()
        row=box.row(align = True)
        row.operator('mustardui.optix_compatibility', icon="MATERIAL").revert = False
        row.operator('mustardui.optix_compatibility', icon="DECORATE_OVERRIDE", text="").revert = True

class MUSTARDTOOLS_PT_Settings(MainPanel, bpy.types.Panel):
    bl_idname = "MUSTARDTOOLS_PT_Settings"
    bl_label = "Settings"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        
        layout = self.layout
        settings = bpy.context.scene.mustardtools_settings
        
        box=layout.box()
        box.label(text="Main Settings", icon="SETTINGS")
        box.prop(settings,"ms_advanced")
        box.prop(settings,"ms_debug")
        
        box=layout.box()
        box.label(text="Slide Keyframes Settings", icon="SETTINGS")
        row=box.row()
        row.label(text="Application")
        row.scale_x = 2.
        row.prop(settings,"slide_keyframes_application")
        
        box=layout.box()
        box.label(text="Objects Naming Convention",icon="OUTLINER_OB_FONT")
        row=box.row()
        row.label(text="Prefix")
        row.scale_x = 2.
        row.prop(settings,"ms_naming_prefix")

# ------------------------------------------------------------------------
#    Register
# ------------------------------------------------------------------------

classes = (
    MUSTARDTOOLS_OT_IKChain,
    MUSTARDTOOLS_OT_IKChain_Pole,
    MUSTARDTOOLS_OT_IKChain_Clean,
    MUSTARDTOOLS_PT_IKChain,
    MUSTARDTOOLS_OT_IKSpline,
    MUSTARDTOOLS_OT_IKSpline_Clean,
    MUSTARDTOOLS_PT_IKSpline,
    MUSTARDTOOLS_OT_MouthController,
    MUSTARDTOOLS_OT_MouthControllerSmartSearch,
    MUSTARDTOOLS_OT_MouthControllerClean,
    MUSTARDTOOLS_PT_MouthController,
    MUSTARDTOOLS_OT_SlideKeyframes,
    MUSTARDTOOLS_OT_OptiXCompatibility,
    MUSTARDTOOLS_PT_VariousTools,
    MUSTARDTOOLS_PT_Settings
)

addon_keymaps = []

def register():
    
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
        
    wm = bpy.context.window_manager ### register the keymap
    km = wm.keyconfigs.addon.keymaps.new(name='Dopesheet', space_type='DOPESHEET_EDITOR')
    kmi = km.keymap_items.new(MUSTARDTOOLS_OT_SlideKeyframes.bl_idname, 'S', 'PRESS', shift=True, ctrl=False, alt=True)
    addon_keymaps.append((km, kmi))

def unregister():
    
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()
