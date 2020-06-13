bl_info = {
    "name": "Mustard Tools",
    "description": "A set of tools for riggers and animators",
    "author": "Mustard",
    "version": (0, 0, 1),
    "blender": (2, 83, 0),
    #"location": "Render Settings > Performance",
    "warning": "",
    #"wiki_url": "https://docs.blender.org/manual/en/dev/addons/"
    #            "render/auto_tile_size.html",
    "category": "3D View",
}

import bpy
import addon_utils
import sys
import os
import re
import time
from bpy.props import *
from mathutils import Vector, Color
import webbrowser

# ------------------------------------------------------------------------
#    Mustard Tools Properties
# ------------------------------------------------------------------------

# Poll functions for properties
def poll_mesh(self, object):
    
    return object.type == 'MESH'

class MustardTools_Settings(bpy.types.PropertyGroup):
    
    # Main Settings definitions
    # UI definitions
    ms_advanced: bpy.props.BoolProperty(name="Advanced Options",
                                        description="Unlock advanced options",
                                        default=False)
    ms_debug: bpy.props.BoolProperty(name="Debug mode",
                                        description="Unlock debug mode.\nThis will generate more messaged in the console.\nEnable it only if you encounter problems, as it might degrade general Blender performance",
                                        default=False)
    
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
                                                                poll=poll_mesh)
    ik_chain_pole_bone_custom_shape: bpy.props.PointerProperty(type=bpy.types.Object,
                                                                name="",
                                                                description="Object that will be used as custom shape for the IK pole",
                                                                poll=poll_mesh)
    
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
    ik_spline_resolution: bpy.props.IntProperty(default=2,min=1,max=64,
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
                                                                description="Object that will be used as custom shape for the IK spline controllers",
                                                                poll=poll_mesh)

bpy.utils.register_class(MustardTools_Settings)

bpy.types.Scene.mustardtools_settings = bpy.props.PointerProperty(type=MustardTools_Settings)
#bpy.context.scene.mustardtools_settings.ik_chain_pole_status = False

# ------------------------------------------------------------------------
#    IK Chain Tool
# ------------------------------------------------------------------------

class MUSTARDTOOLS_OT_IKChain(bpy.types.Operator):
    """This tool will create an IK rig on the selected chain.\nSelect the bones, the last one being the tip of the chain where the controller will be placed"""
    bl_idname = "ops.ik_chain"
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
        
        settings = bpy.context.scene.mustardtools_settings
        
        # Naming convention
        IKChain_Controller_Bone_Name = "MustardTools.IK.Controller"
        IKChain_Constraint_Name = "MustardTools IKChain"
    
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
        
        else:
            
            chain_last_bone_edit = arm.data.edit_bones[chain_last_bone.name]
            IK_main_bone_edit = arm.data.edit_bones.new(IKChain_Controller_Bone_Name)
            IK_main_bone_edit.use_deform = False
            IK_main_bone_edit.head = chain_last_bone_edit.tail
            IK_main_bone_edit.tail = 2. * chain_last_bone_edit.tail - chain_last_bone_edit.head

        bpy.ops.object.mode_set(mode='POSE')
        
        IK_main_bone = arm.pose.bones[IK_main_bone_edit.name]
        IK_main_bone.custom_shape = settings.ik_chain_last_bone_custom_shape
        IK_main_bone.custom_shape_scale = 0.2
        IK_main_bone.use_custom_shape_bone_size = True

        IKConstr = chain_last_bone.constraints.new('IK')
        IKConstr.name = IKChain_Constraint_Name
        IKConstr.use_rotation = True
        IKConstr.target = arm
        IKConstr.subtarget = IK_main_bone_edit.name
        IKConstr.chain_count = chain_length

        self.report({'INFO'}, 'MustardTools - IK successfully added.')
        
        return {'FINISHED'}

class MUSTARDTOOLS_OT_IKChain_Pole(bpy.types.Operator):
    """This tool will guide you in the creation of a pole for an already available IK rig"""
    bl_idname = "ops.ik_chainpole"
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
        
        settings = bpy.context.scene.mustardtools_settings
        
        # Naming convention
        IKChain_Pole_Bone_Name = "MustardTools.IK.Pole"
    
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
            IK_pole_bone.custom_shape_scale = 0.2
            IK_pole_bone.use_custom_shape_bone_size = True
            
            for constraint in arm.pose.bones[settings.ik_chain_last_bone].constraints:
                if constraint.type == 'IK':
                    IKConstr = constraint

            IKConstr.use_rotation = True
            IKConstr.pole_target = arm
            IKConstr.pole_subtarget = settings.ik_chain_pole_bone
            IKConstr.pole_angle = 3.141593/2.
            
            settings.ik_chain_pole_status = False

            self.report({'INFO'}, 'MustardTools - IK pole successfully added.')
        
        return {'FINISHED'}

class MUSTARDTOOLS_OT_IKChain_Clean(bpy.types.Operator):
    """This tool will clean the available IK constraints in the selected bones.\nSelect a bone with an IK constraint to enable the tool.\nA confirmation box will appear"""
    bl_idname = "ops.ik_chainclean"
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
    """This tool will create an IK spline on the selected chain.\nSelect the bones, the last one being the tip of the chain"""
    bl_idname = "ops.ik_spline"
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
            if len(chain_bones) < 2:
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
        
        settings = bpy.context.scene.mustardtools_settings
        
        num = settings.ik_spline_number
        
        # Naming convention
        IKSpline_Curve_Name = "MustardTools.IKSpline.Curve"
        IKSpline_Bone_Name = "MustardTools.IKSpline.Bone"
        IKSpline_Hook_Modifier_Name = "MustardTools.IKSpline.Hook"
        IKSpline_Empty_Name = "MustardTools.IKSpline.Empty"
        IKSpline_Constraint_Name = "MustardTools.IKSpline"
    
        # Definitions
        arm = bpy.context.object
        chain_bones = bpy.context.selected_pose_bones
        chain_length = len(chain_bones)
        chain_last_bone = chain_bones[chain_length-1]
        
        if arm.location.x != 0. or arm.location.y != 0. or arm.location.z != 0.:
            self.report({'WARNING'}, 'MustardTools - The Armature selected seems not to have location applied. This might generate odd results!')
            print("MustardTools IK Spline - Apply the location on the armature with Ctrl+A in Object mode!")

        if settings.ms_debug:
            print("MustardTools IK Spline - Armature selected: " + bpy.context.object.name)
            print("MustardTools IK Spline - Chain length: " + str(chain_length))
        
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        
        curveData = bpy.data.curves.new(IKSpline_Curve_Name, type='CURVE')
        curveData.dimensions = '3D'
        curveData.resolution_u = settings.ik_spline_resolution
        curveData.use_path = True
        
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        
        polyline = curveData.splines.new('BEZIER')
        polyline.bezier_points.add(num-1)
        
        b = []
        
        for i in range(0,num-1):
            x = chain_bones[int(chain_length/(num-1)*i)].head.x
            y = chain_bones[int(chain_length/(num-1)*i)].head.y
            z = chain_bones[int(chain_length/(num-1)*i)].head.z
            polyline.bezier_points[i].co = (x, y, z)
            polyline.bezier_points[i].handle_right_type = 'VECTOR'
            polyline.bezier_points[i].handle_left_type = 'VECTOR'
            
            b.append( arm.data.edit_bones.new(IKSpline_Bone_Name) )
            b[i].use_deform = False
            b[i].head = 2. * arm.data.edit_bones[int(chain_length/(num-1)*i)].head - arm.data.edit_bones[int(chain_length/(num-1)*i)].tail
            b[i].tail = arm.data.edit_bones[int(chain_length/(num-1)*i)].head
        
        i += 1
        x = chain_bones[chain_length-1].head.x
        y = chain_bones[chain_length-1].head.y
        z = chain_bones[chain_length-1].head.z
        polyline.bezier_points[i].co = (x, y, z)
        polyline.bezier_points[i].handle_right_type = 'VECTOR'
        polyline.bezier_points[i].handle_left_type = 'VECTOR'
        b.append( arm.data.edit_bones.new(IKSpline_Bone_Name) )
        b[i].use_deform = False
        b[i].head = arm.data.edit_bones[chain_length-1].head
        b[i].tail = arm.data.edit_bones[chain_length-1].tail
        
        if settings.ik_spline_bendy:
            for bone in chain_bones:
                arm.data.edit_bones[bone.name].bbone_segments = settings.ik_spline_bendy_segments
            
            arm.data.display_type = "BBONE"
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Create empties
        e = []
        for i in range(0,num):
            e.append( bpy.data.objects.new(IKSpline_Empty_Name, None) )
            e[i].location=polyline.bezier_points[i].co
            e[i].parent = arm
            e[i].parent_type = "BONE"
            e[i].parent_bone = b[i].name
            e[i].empty_display_type="SPHERE"
            bpy.context.collection.objects.link(e[i])
            #e[i].location = (arm.location.x,arm.location.y,arm.location.z)#polyline.bezier_points[0].co
        
        # Create curve object
        curveOB = bpy.data.objects.new(IKSpline_Curve_Name, curveData)
        
        # Create hook modifiers
        m = []
        for i in range(0,num):
            m.append( curveOB.modifiers.new(IKSpline_Hook_Modifier_Name, 'HOOK') )
            m[i].object = e[i]
        
        bpy.context.collection.objects.link(curveOB)
        context.view_layer.objects.active = curveOB
        
        bpy.ops.object.editmode_toggle()
        
        for i in range(0,num):
            
            select_index = i
            for j, point in enumerate(curveData.splines[0].bezier_points) :
                point.select_left_handle = j == select_index
                point.select_right_handle = j == select_index
                point.select_control_point = j == select_index
            
            bpy.ops.object.hook_assign(modifier=m[i].name)
            bpy.ops.object.hook_reset(modifier=m[i].name)
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Create Spline IK modifier
        IKSplineConstr = chain_last_bone.constraints.new('SPLINE_IK')
        IKSplineConstr.name = IKSpline_Constraint_Name
        IKSplineConstr.target = curveOB
        IKSplineConstr.chain_count = chain_length
        IKSplineConstr.y_scale_mode = "BONE_ORIGINAL"
        IKSplineConstr.xz_scale_mode = "BONE_ORIGINAL"
        
        # Apply custom shape
        for bone in b:
            pose_bone = arm.pose.bones[bone.name]
            pose_bone.custom_shape = settings.ik_spline_bone_custom_shape
            pose_bone.custom_shape_scale = 0.2
            pose_bone.use_custom_shape_bone_size = True
        
        # Final cleanup
        for i in range(0,num):
            e[i].hide_render = True
            e[i].hide_viewport = True
        
        context.view_layer.objects.active = arm
        
        bpy.ops.object.mode_set(mode='POSE')
        
        return {'FINISHED'}
    
class MUSTARDTOOLS_OT_IKSpline_Clean(bpy.types.Operator):
    """This tool will remove the IK spline"""
    bl_idname = "ops.ik_splineclean"
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
                    if self.delete_bones:
                        
                        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                        
                        if constraint.target != None:
                            IKCurve = constraint.target
                            for hook_mod in IKCurve.modifiers:
                                if hook_mod.object != None:
                                    
                                    IKEmpty = hook_mod.object
                                    e.append(IKEmpty)
                                    
                                    if IKEmpty.parent_type == "BONE" and IKEmpty.parent != None and IKEmpty.parent_bone != None and IKEmpty.parent_bone != "":
                                        IKArm = IKEmpty.parent
                                        IKBone = IKArm.data.edit_bones[IKEmpty.parent_bone]
                                        IKBone_name = IKBone.name
                                        IKArm.data.edit_bones.remove(IKBone)
                                        if settings.ms_debug:
                                            print("MustardTools IK Spline - Bone " + IKBone_name + " removed from Armature " + IKArm.name)
                                        removed_bones = removed_bones + 1
                                    
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.object.select_all(action='DESELECT')
                    for empty in e:
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
    bl_options = {"DEFAULT_CLOSED"}

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
        layout.operator('ops.ik_chain', icon="ADD")
        box=layout.box()
        box.label(text="Pole settings", icon="SHADING_WIRE")
        row=box.row()
        row.label(text="Shape")
        row.scale_x = 3.
        row.prop(settings,"ik_chain_pole_bone_custom_shape")
        if not settings.ik_chain_pole_status:
            layout.operator('ops.ik_chainpole', icon="ADD").status = True
        else:
            row=box.row(align=True)
            row.operator('ops.ik_chainpole', text="Confirm", icon = "CHECKMARK", depress = True).status = False
            row.scale_x=1.
            row.operator('ops.ik_chainpole', text="", icon = "X").cancel = True
        layout.separator()
        layout.operator('ops.ik_chainclean', icon="CANCEL")

class MUSTARDTOOLS_PT_IKSpline(MainPanel, bpy.types.Panel):
    bl_idname = "MUSTARDTOOLS_PT_IKSpline"
    bl_label = "IK Spline"
    bl_options = {"DEFAULT_CLOSED"}

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
        row=box.row()
        row.label(text="Shape")
        row.scale_x = 3.
        row.prop(settings,"ik_spline_bone_custom_shape")
        
        layout.operator('ops.ik_spline', icon="ADD")
        
        layout.separator()
        layout.operator('ops.ik_splineclean', icon="CANCEL")

class MUSTARDTOOLS_PT_Settings(MainPanel, bpy.types.Panel):
    bl_idname = "MUSTARDTOOLS_PT_Settings"
    bl_label = "Settings"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        
        layout = self.layout
        settings = bpy.context.scene.mustardtools_settings
        
        box=layout.box()
        box.label(text="Settings", icon="SETTINGS")
        box.prop(settings,"ms_advanced")
        box.prop(settings,"ms_debug")

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
    MUSTARDTOOLS_PT_Settings
)

def register():
    
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()
