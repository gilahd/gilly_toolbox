bl_info = {
    "name": "Gilly Toolbox",
    "blender": (3, 0, 0),
    "author": "Gilahd Yefet",
    "version": (1,0),
    "description": "Set of tools that will help speed up repetative tasks",
}

import bpy

# Function to check if an object is a linked duplicate
def is_linked_duplicate(obj):
    return obj.data and obj.data.users > 1

# Define the operator for selecting linked duplicates
class OBJECT_OT_SelectedLinkedDuplicatesOperator(bpy.types.Operator):
    bl_idname = "object.selected_linked_duplicates"
    bl_label = "Selected Linked Duplicates"
    bl_description = "Selects linked duplicates of mesh objects in the scene"
    
    def execute(self, context):
        # Deselect all objects first
        bpy.ops.object.select_all(action='DESELECT')

        # Get all mesh objects in the scene
        mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

        # Loop through the mesh objects and select those that are linked duplicates
        for obj in mesh_objects:
            if is_linked_duplicate(obj):
                obj.select_set(True)

        # Set the active object (optional)
        if len(mesh_objects) > 0:
            bpy.context.view_layer.objects.active = mesh_objects[0]
        
        return {'FINISHED'}
    
# Function to move selected objects to the chosen collection
def move_selected_objects_to_chosen_collection(chosen_collection_name):
    # Get the chosen collection by name
    chosen_collection = bpy.data.collections[chosen_collection_name]

    # Get selected objects
    selected_objects = bpy.context.selected_objects

    # Move selected objects to the chosen collection
    for obj in selected_objects:
        if obj.users_collection:
            obj.users_collection[0].objects.unlink(obj)
        chosen_collection.objects.link(obj)

# Operator to trigger moving selected objects to the chosen collection
class OBJECT_OT_MoveToChosenCollection(bpy.types.Operator):
    bl_idname = "object.move_to_chosen_collection"
    bl_label = "Move to Chosen Collection"
    bl_description = "Move selected objects to the chosen collection in the Outliner"

    collection_name: bpy.props.StringProperty()

    def execute(self, context):
        move_selected_objects_to_chosen_collection(self.collection_name)
        return {'FINISHED'}

# Define the operator for removing custom properties
class OBJECT_OT_RemoveCustomPropertyOperator(bpy.types.Operator):
    bl_idname = "object.remove_custom_property"
    bl_label = "Remove Custom Property"
    bl_description = "Removes custom properties from selected mesh objects"
    
    def execute(self, context):
        settings = context.scene.remove_custom_property_settings
        property_name = settings.property_name
        
        # Get the selected objects
        selected_objects = bpy.context.selected_objects
        
        # Loop through the selected objects and remove custom properties
        for obj in selected_objects:
            if obj.type == 'MESH':
                if not property_name:
                    # Remove all custom properties if property name is blank
                    properties_to_remove = list(obj.keys())
                else:
                    properties_to_remove = [property_name] if property_name in obj.keys() else []
                
                # Remove properties after collecting all names to avoid changing size during iteration
                for prop_name in properties_to_remove:
                    del obj[prop_name]
        
        return {'FINISHED'}

# Define the operator for adding custom properties
class OBJECT_OT_AddCustomPropertyOperator(bpy.types.Operator):
    bl_idname = "object.add_custom_property"
    bl_label = "Add Custom Property"
    bl_description = "Adds custom property to selected mesh objects"
    
    def execute(self, context):
        settings = context.scene.add_custom_property_settings
        property_name = settings.property_name
        property_value = settings.property_value
        
        # Get the selected objects
        selected_objects = bpy.context.selected_objects
        
        # Loop through the selected objects and add custom properties
        for obj in selected_objects:
            if obj.type == 'MESH':
                if property_name and property_value:
                    obj[property_name] = property_value
        
        return {'FINISHED'}

# Property group to store the property name and value for Remove Custom Property
class RemoveCustomPropertySettings(bpy.types.PropertyGroup):
    property_name: bpy.props.StringProperty(
        name="Property Name",
        default="",
        description="Name of the custom property to remove (leave blank to remove all custom properties from selected mesh objects)",
    )

# Property group to store the property name and value for Add Custom Property
class AddCustomPropertySettings(bpy.types.PropertyGroup):
    property_name: bpy.props.StringProperty(
        name="Property Name",
        default="",
        description="Name of the custom property to add",
    )
    
    property_value: bpy.props.StringProperty(
        name="Value",
        default="",
        description="Value of the custom property",
    )
    
# Property group for UV renaming settings
class RenameUVSettings(bpy.types.PropertyGroup):
    uv_name: bpy.props.StringProperty(
        name="New UV Name",
        default="",
        description="Set the name for the new UV",
    )

# Define the operator for renaming UVs
class OBJECT_OT_RenameUVOperator(bpy.types.Operator):
    bl_idname = "object.rename_uv"
    bl_label = "Rename UV"
    bl_description = "Renames active UV of selected meshes"
    
    uv_name: bpy.props.StringProperty(
        name="New UV Name",
        default="",
        description="Set the name for the new UV",
    )
    
    def execute(self, context):
        uv_name = context.scene.rename_uv_settings.uv_name
        if uv_name:
            selected_objects = bpy.context.selected_objects
            for obj in selected_objects:
                if obj.type == 'MESH':
                    mesh = obj.data
                    if mesh.uv_layers.active is not None and mesh.uv_layers.active.name != uv_name:
                        try:
                            mesh.uv_layers[uv_name]
                        except KeyError:
                            mesh.uv_layers.active.name = uv_name
        return {'FINISHED'}

# Define the operator for removing inactive UV maps
class OBJECT_OT_RemoveInactiveUVOperator(bpy.types.Operator):
    bl_idname = "object.remove_inactive_uv"
    bl_label = "Remove Inactive Maps"
    bl_description = "Removes UV maps that are inactive for rendering from selected mesh objects"
    
    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        for obj in selected_objects:
            if obj.type == 'MESH':
                mesh = obj.data
                active_uv_map_name = None
                
                # Find the UV map that is active for rendering
                for uv_map in mesh.uv_layers:
                    if uv_map.active_render:
                        active_uv_map_name = uv_map.name
                        break
                
                if active_uv_map_name:
                    # Collect UV map names that are inactive for rendering
                    uv_map_names_to_remove = [
                        uv_map.name for uv_map in mesh.uv_layers 
                        if uv_map.name != active_uv_map_name and not uv_map.active_render
                    ]
                    
                    # Remove the inactive UV maps by name
                    for uv_map_name in uv_map_names_to_remove:
                        mesh.uv_layers.remove(mesh.uv_layers[uv_map_name])
                        print(f"Removed inactive UV map '{uv_map_name}' from {obj.name}")
                    
        return {'FINISHED'}
    
# Define the operator for removing unused material slots from selected meshes
class OBJECT_OT_RemoveUnusedMaterialsOperator(bpy.types.Operator):
    bl_idname = "object.remove_unused_materials"
    bl_label = "Remove Unused Materials"
    bl_description = "Removes unused and empty material slots from selected meshes"

    def execute(self, context):
        bpy.ops.object.material_slot_remove_unused()
        return {'FINISHED'}

# Define the operator for changing curve fill modes
class OBJECT_OT_ChangeCurveFillModeOperator(bpy.types.Operator):
    bl_idname = "object.change_curve_fill_mode"
    bl_label = "Change Curve Fill Mode"
    bl_description = "Change fill mode of selected curves"

    fill_mode: bpy.props.StringProperty(default="BOTH")  # Property to store fill mode

    def execute(self, context):
        selected_objects = bpy.context.selected_objects

        for obj in selected_objects:
            if obj.type == 'CURVE':
                obj.data.fill_mode = self.fill_mode

        return {'FINISHED'}
    
# Define the operator for extruding curves by a given value
class OBJECT_OT_ExtrudeCurvesOperator(bpy.types.Operator):
    bl_idname = "object.extrude_curves"
    bl_label = "Extrude Curves"
    bl_description = "Extrude selected curves by the given value"

    def execute(self, context):
        extrude_value = context.scene.extrude_settings.extrude_value
        
        selected_objects = bpy.context.selected_objects

        for obj in selected_objects:
            if obj.type == 'CURVE':
                obj.data.extrude = extrude_value

        return {'FINISHED'}

# Property group for extrude value
class ExtrudeSettings(bpy.types.PropertyGroup):
    extrude_value: bpy.props.FloatProperty(
        name="Value",
        description="Set the amount you would like to extrude the curves by",
        default=0.0,
        unit='LENGTH'  # Set the unit of measurement
    )

#Property group for curve resolution value
class SetCurveResolutionSettings(bpy.types.PropertyGroup):
    resolution_u: bpy.props.IntProperty(
        name="Resolution U",
        description="Set the resolution value for selected curves",
        default=12,  # Adjust the default value as needed
        min=1,       # Minimum resolution value
        step=1        # Increment value (whole numbers)
    )

# Define the operator for setting curve resolution U
class OBJECT_OT_SetCurveResolutionOperator(bpy.types.Operator):
    bl_idname = "object.set_curve_resolution"
    bl_label = "Set Curve Resolution"
    bl_description = "Sets Resolution Preview U for selected curves"

    def execute(self, context):
        settings = context.scene.set_curve_resolution_settings
        resolution_u = settings.resolution_u

        selected_objects = bpy.context.selected_objects

        for obj in selected_objects:
            if obj.type == 'CURVE':
                curve = obj.data
                if curve.resolution_u != resolution_u:
                    curve.resolution_u = resolution_u

        return {'FINISHED'}

#Define the operator for baking particle simulations
class OBJECT_OT_BakeParticleSimulationOperator(bpy.types.Operator):
    bl_idname = "object.bake_particle_simulation"
    bl_label = "Bake Particle Simulation"
    bl_description = "Run the particle simulation baking code"

    def execute(self, context):
        
        # Set these to False if you don't want to key that property.
        KEYFRAME_LOCATION = True
        KEYFRAME_ROTATION = True
        KEYFRAME_SCALE = True
        KEYFRAME_VISIBILITY = False  # Viewport and render visibility.
        KEYFRAME_VISIBILITY_SCALE = True


        def create_objects_for_particles(ps, obj):
            # Duplicate the given object for every particle and return the duplicates.
            # Use instances instead of full copies.
            obj_list = []
            mesh = obj.data
            particles_coll = bpy.data.collections.new(name="particles")
            bpy.context.scene.collection.children.link(particles_coll)

            for i, _ in enumerate(ps.particles):
                dupli = bpy.data.objects.new(
                            name="particle.{:03d}".format(i),
                            object_data=mesh)
                particles_coll.objects.link(dupli)
                obj_list.append(dupli)
            return obj_list

        def match_and_keyframe_objects(ps, obj_list, start_frame, end_frame):
            # Match and keyframe the objects to the particles for every frame in the
            # given range.
            for frame in range(start_frame, end_frame + 1):
                print("frame {} processed".format(frame))
                bpy.context.scene.frame_set(frame)
                for p, obj in zip(ps.particles, obj_list):
                    match_object_to_particle(p, obj)
                    keyframe_obj(obj)

        def match_object_to_particle(p, obj):
            # Match the location, rotation, scale and visibility of the object to
            # the particle.
            loc = p.location
            rot = p.rotation
            size = p.size
            if p.alive_state == 'ALIVE':
                vis = True
            else:
                vis = False
            obj.location = loc
            # Set rotation mode to quaternion to match particle rotation.
            obj.rotation_mode = 'QUATERNION'
            obj.rotation_quaternion = rot
            if KEYFRAME_VISIBILITY_SCALE:
                if vis:
                    obj.scale = (size, size, size)
                if not vis:
                    obj.scale = (0.001, 0.001, 0.001)
            obj.hide_viewport = not(vis) # <<<-- this was called "hide" in <= 2.79
            obj.hide_render = not(vis)

        def keyframe_obj(obj):
            # Keyframe location, rotation, scale and visibility if specified.
            if KEYFRAME_LOCATION:
                obj.keyframe_insert("location")
            if KEYFRAME_ROTATION:
                obj.keyframe_insert("rotation_quaternion")
            if KEYFRAME_SCALE:
                obj.keyframe_insert("scale")
            if KEYFRAME_VISIBILITY:
                obj.keyframe_insert("hide_viewport") # <<<-- this was called "hide" in <= 2.79
                obj.keyframe_insert("hide_render")


        def main():
            #in 2.8 you need to evaluate the Dependency graph in order to get data from animation, modifiers, etc
            depsgraph = bpy.context.evaluated_depsgraph_get()

            # Assume only 2 objects are selected.
            # The active object should be the one with the particle system.
            ps_obj = bpy.context.object
            ps_obj_evaluated = depsgraph.objects[ ps_obj.name ]
            obj = [obj for obj in bpy.context.selected_objects if obj != ps_obj][0]
            
            for psy in ps_obj_evaluated.particle_systems:         
                ps = psy  # Assume only 1 particle system is present.
                start_frame = bpy.context.scene.frame_start
                end_frame = bpy.context.scene.frame_end
                obj_list = create_objects_for_particles(ps, obj)
                match_and_keyframe_objects(ps, obj_list, start_frame, end_frame)
                
        main()

        return {'FINISHED'}
        
#---------------
# USER INTERFACE
#---------------
# Define the panel for the UI in the N-panel
class OBJECT_PT_GillyToolsPanel(bpy.types.Panel):
    bl_label = "Gilly Tools"
    bl_idname = "OBJECT_PT_GillyToolsPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Gilly Tools'  # Custom tab name
    
    def draw(self, context):
        layout = self.layout
        add_settings = context.scene.add_custom_property_settings
        set_curve_resolution_settings = context.scene.set_curve_resolution_settings
        remove_settings = context.scene.remove_custom_property_settings
        
        #Instances Box
        row = layout.row()
        row.label(text="Objects & Instances", icon='OUTLINER')
        box = layout.box()
        col = box.column()
        col.operator("object.selected_linked_duplicates")
        
        # Function to update the collection items in the dropdown
        box = layout.box()
        col = box.column()
        col.label(text="Move Selected to Collection")
        def update_collection_items(self, context):
            collections = bpy.context.scene.collection.children
            col.prop(context.scene, "chosen_collection", text="", icon='GROUP')

        # Dropdown menu to select the collection
        collections = bpy.context.scene.collection.children
        collection_items = [(col.name, col.name, '') for col in collections]
        col.prop(context.scene, "chosen_collection", text="", icon='GROUP')

        # Button to move selected objects to the chosen collection
        col.operator("object.move_to_chosen_collection", text="Move to Collection").collection_name = context.scene.chosen_collection
        
        #Custom Properties Box
        row = layout.row()
        row.label(text="Custom Properties", icon='CONSOLE')
        box = layout.box()
        col = box.column()
        
        col.label(text="Add Custom Property")
        
        col.prop(add_settings, "property_name", text="Name")
        col.prop(add_settings, "property_value", text="Value")
        add_op = col.operator("object.add_custom_property")
        
        col.separator()
        
        col.label(text="Remove Custom Property")
        
        col.prop(remove_settings, "property_name", text="Name")
        remove_op = col.operator("object.remove_custom_property")
        
        # UV Rename Box
        row = layout.row()
        row.label(text="UV Tools", icon='UV')
        box = layout.box()
        col = box.column()
        
        col.label(text="Rename UV")        
        col.prop(context.scene.rename_uv_settings, "uv_name", text="New Name")
        col.operator("object.rename_uv")
        col.separator()
        col.operator("object.remove_inactive_uv", text="Remove Inactive Maps")
        
        # Materials Box
        row = layout.row()
        row.label(text="Materials", icon='MATERIAL')
        box = layout.box()
        col = box.column()
        col.operator("object.remove_unused_materials", text="Remove Unused Materials")
        
        # Curves Box
        row = layout.row()
        row.label(text="Curves", icon='CURVE_BEZCURVE')
        box = layout.box()
        col = box.column()
        
        # Curves Box - Extrude Section
        col.label(text="Extrude Curves")
        
        scene = context.scene
        extrude_settings = scene.extrude_settings
    
        col.prop(extrude_settings, "extrude_value")
        col.operator("object.extrude_curves", text="Extrude")
        
        # Curves Box - Fill Mode
        row = box.row(align=True)
        row.label(text="Fill Mode")  
        row.operator("object.change_curve_fill_mode", text="Both").fill_mode = 'BOTH'
        row.operator("object.change_curve_fill_mode", text="Back").fill_mode = 'BACK'
        row.operator("object.change_curve_fill_mode", text="Front").fill_mode = 'FRONT'
        
        col.separator()
        
        # Curves Box - Resolution Preview U Section
        col = box.column()
        col.label(text="Curve Resolution") 
        
 
        col.prop(set_curve_resolution_settings, "resolution_u", text="Resolution U")
        col.operator("object.set_curve_resolution", text="Set Resolution")
        
        # Particle Bake Section
        row = layout.row()
        row.label(text="Particle Simulation", icon='PARTICLES')
        
        box = layout.box()

        row = box.row(align=True)
        row.operator("object.bake_particle_simulation", text="Bake Particle Simulation")


def get_collection_items(self, context):
    collections = bpy.context.scene.collection.children
    return [(col.name, col.name, '') for col in collections]

# Property to store the chosen collection name
bpy.types.Scene.chosen_collection = bpy.props.EnumProperty(
    items=get_collection_items,
    name="Chosen Collection"
)

# Registration and unregistering of operators and panels
def register():
    bpy.utils.register_class(OBJECT_OT_SelectedLinkedDuplicatesOperator)
    bpy.utils.register_class(OBJECT_OT_RemoveCustomPropertyOperator)
    bpy.utils.register_class(OBJECT_OT_AddCustomPropertyOperator)
    bpy.utils.register_class(OBJECT_PT_GillyToolsPanel)  # Your existing panels
    bpy.utils.register_class(RemoveCustomPropertySettings)
    bpy.utils.register_class(AddCustomPropertySettings)
    bpy.utils.register_class(OBJECT_OT_RenameUVOperator)
    bpy.utils.register_class(RenameUVSettings)
    bpy.utils.register_class(OBJECT_OT_RemoveInactiveUVOperator)
    bpy.utils.register_class(OBJECT_OT_RemoveUnusedMaterialsOperator)
    bpy.utils.register_class(OBJECT_OT_ChangeCurveFillModeOperator)
    bpy.utils.register_class(OBJECT_OT_ExtrudeCurvesOperator)
    bpy.utils.register_class(ExtrudeSettings)
    bpy.types.Scene.extrude_settings = bpy.props.PointerProperty(type=ExtrudeSettings)
    bpy.utils.register_class(OBJECT_OT_BakeParticleSimulationOperator)
    bpy.types.Scene.remove_custom_property_settings = bpy.props.PointerProperty(type=RemoveCustomPropertySettings)
    bpy.types.Scene.add_custom_property_settings = bpy.props.PointerProperty(type=AddCustomPropertySettings)
    bpy.types.Scene.rename_uv_settings = bpy.props.PointerProperty(type=RenameUVSettings)
    bpy.utils.register_class(SetCurveResolutionSettings)
    bpy.utils.register_class(OBJECT_OT_SetCurveResolutionOperator)
    bpy.types.Scene.set_curve_resolution_settings = bpy.props.PointerProperty(type=SetCurveResolutionSettings)
    bpy.utils.register_class(OBJECT_OT_MoveToChosenCollection)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_SelectedLinkedDuplicatesOperator)
    bpy.utils.unregister_class(OBJECT_OT_RemoveCustomPropertyOperator)
    bpy.utils.unregister_class(OBJECT_OT_AddCustomPropertyOperator)
    bpy.utils.unregister_class(OBJECT_PT_GillyToolsPanel)
    bpy.utils.unregister_class(RemoveCustomPropertySettings)
    bpy.utils.unregister_class(AddCustomPropertySettings)
    bpy.utils.unregister_class(OBJECT_OT_RenameUVOperator)
    bpy.utils.unregister_class(RenameUVSettings)
    bpy.utils.unregister_class(OBJECT_OT_RemoveInactiveUVOperator)
    bpy.utils.unregister_class(OBJECT_OT_RemoveUnusedMaterialsOperator)
    bpy.utils.unregister_class(OBJECT_OT_ChangeCurveFillModeOperator)
    bpy.utils.unregister_class(OBJECT_OT_ExtrudeCurvesOperator)
    bpy.utils.unregister_class(ExtrudeSettings)
    del bpy.types.Scene.extrude_settings
    bpy.utils.unregister_class(OBJECT_OT_BakeParticleSimulationOperator)
    del bpy.types.Scene.remove_custom_property_settings
    del bpy.types.Scene.add_custom_property_settings
    del bpy.types.Scene.rename_uv_settings
    bpy.utils.unregister_class(SetCurveResolutionSettings)
    bpy.utils.unregister_class(OBJECT_OT_SetCurveResolutionOperator)
    del bpy.types.Scene.set_curve_resolution_settings
    bpy.utils.unregister_class(OBJECT_OT_MoveToChosenCollection)
    del bpy.types.Scene.chosen_collection
    
# Handler to update the collection items in the dropdown when collections change
def update_dropdown_collections(self, context):
    collections = bpy.context.scene.collection.children
    bpy.types.Scene.chosen_collection = bpy.props.EnumProperty(
        items=[(col.name, col.name, '') for col in collections],
        name="Chosen Collection"
    )

# Add the handler to listen for changes in collections
bpy.app.handlers.depsgraph_update_post.append(update_dropdown_collections)

# Checking if the script is being run directly from Blender
if __name__ == "__main__":
    register()
