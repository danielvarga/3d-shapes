import bpy
import bmesh
import math
from mathutils import Vector, Quaternion


# Deselect all objects first
bpy.ops.object.select_all(action='DESELECT')
# Select all objects in the scene
for obj in bpy.context.scene.objects:
    obj.select_set(True)
# Delete all selected objects
bpy.ops.object.delete() 


# Parameters for the ring
outer_radius = 1.4
inner_radius = 1.3
height = 0.25
resolution = 256  # Number of vertices around the circumference

# Create the outer cylinder (larger)
bpy.ops.mesh.primitive_cylinder_add(radius=outer_radius, depth=height, vertices=resolution)
outer_cylinder = bpy.context.object
outer_cylinder.name = 'Outer Cylinder'

# Create the inner cylinder (smaller)
bpy.ops.mesh.primitive_cylinder_add(radius=inner_radius, depth=height + 0.1, vertices=resolution)  # Slightly taller for clean subtraction
inner_cylinder = bpy.context.object
inner_cylinder.name = 'Inner Cylinder'

# Apply Boolean modifier to the outer cylinder to subtract the inner cylinder
bool_mod = outer_cylinder.modifiers.new(type="BOOLEAN", name="bool")
bool_mod.object = inner_cylinder
bool_mod.operation = 'DIFFERENCE'

# Apply the modifier
bpy.context.view_layer.objects.active = outer_cylinder
bpy.ops.object.modifier_apply(modifier=bool_mod.name)

# Delete the inner cylinder as it's no longer needed
bpy.data.objects.remove(inner_cylinder, do_unlink=True)




# Ensure the world exists
if bpy.context.scene.world:
    # Enable use of nodes for the world
    bpy.context.scene.world.use_nodes = True
    nodes = bpy.context.scene.world.node_tree.nodes

    # Get the background node
    bg_node = nodes.get('Background')
    if not bg_node:
        # If the Background node doesn't exist, create one
        bg_node = nodes.new(type='ShaderNodeBackground')

    # Set the color to blue
    # RGB values range from 0 to 1, where (0, 0, 1) corresponds to blue
    # bg_node.inputs['Color'].default_value = (135/255, 180/255, 255/255, 1.0)  # The fourth value is alpha
    bg_node.inputs['Color'].default_value = (10/255, 10/255, 10/255, 1.0)  # The fourth value is alpha
    # bg_node.inputs['Color'].default_value = (205/4000, 127/4000, 50/4000, 1.0)  # The fourth value is alpha

    # Ensure the background node is connected to the world output
    world_output = nodes.get('World Output')
    if not world_output:
        world_output = nodes.new(type='ShaderNodeOutputWorld')
    links = bpy.context.scene.world.node_tree.links
    # if not links.get((bg_node.outputs['Background'], world_output.inputs['Surface'])):
    #     links.new(bg_node.outputs['Background'], world_output.inputs['Surface'])


bpy.ops.mesh.primitive_cylinder_add(radius=1.29, depth=0.2, vertices=100, location=(0, 0, 0))
coin = bpy.context.object
coin.select_set(True)
bpy.ops.object.shade_smooth()


# Create a sphere
n = 256
bpy.ops.mesh.primitive_uv_sphere_add(segments=n, ring_count=n, radius=1)
sphere = bpy.context.object

# Create a large flat box
bpy.ops.mesh.primitive_cube_add(size=1)
cube = bpy.context.object

cube.scale[0] = 0.2
cube.scale[1] = 4
cube.scale[2] = 4



def rotate_to_normal(cylinder, target_normal):
    # Ensure the normal vector is a normalized mathutils Vector
    target_normal = Vector(target_normal).normalized()
    
    # Initial cylinder axis (assuming Z-axis)
    cylinder_axis = Vector((0, 0, 1))
    
    # Calculate the rotation needed to align the cylinder axis with the target normal
    # Using the rotation_difference method
    rotation_quaternion = cylinder_axis.rotation_difference(target_normal)
    
    # Rotate the cylinder
    cylinder.rotation_mode = 'QUATERNION'  # Change rotation mode to quaternion
    cylinder.rotation_quaternion = rotation_quaternion


def create_plane(normal):
    bpy.ops.mesh.primitive_cylinder_add(radius=3, depth=0.1, vertices=10, location=(0, 0, 0))
    plane = bpy.context.object
    rotate_to_normal(plane, normal)
    return plane


def cutout(plane):
    # Use boolean modifier to subtract the cube from the sphere
    boolean_modifier = sphere.modifiers.new(name="SphereCutter", type='BOOLEAN')
    boolean_modifier.object = plane
    boolean_modifier.operation = 'DIFFERENCE'
    bpy.context.view_layer.update()

    # Apply the boolean modifier
    bpy.context.view_layer.objects.active = sphere
    bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)


normals = [
 (-0.32545395,  0.15232232,  0.93320825),
 (-0.27622077,  0.52217858, -0.80686531),
 ( 0.13710178, -0.94826809, -0.28634025),
 ( 0.4701685 ,  0.48804455,  0.73535984),
 ( 0.98654012, -0.15679634, -0.04640579),
 (-0.59515362, -0.6797727 ,  0.42860385)
]
normals = [Vector(v) for v in normals]

for normal in normals:
    plane = create_plane(normal)

    # applying a fixed rotation to the whole icosidocecahedron,
    # tuned to make the slices nice but not too regular:
    quaternion = Quaternion((1, 2, 2), 65/180*math.pi)
    plane.rotation_mode = 'QUATERNION'
    plane.rotation_quaternion = quaternion @ plane.rotation_quaternion

    cutout(plane)
    bpy.data.objects.remove(plane)


# Delete the cube
bpy.data.objects.remove(cube)


sphere.select_set(True)
# bpy.ops.object.shade_smooth()


sphere.scale[2] /= 6


EXTRUDE_LENGTH = 0.15

# Ensure an object is selected and it's a mesh
if bpy.context.selected_objects and bpy.context.active_object.type == 'MESH':
    obj = bpy.context.active_object
    
    # Switch to Edit Mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Deselect all faces
    bpy.ops.mesh.select_all(action='DESELECT')
    
    # Make sure we're using face select mode
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    
    # Access the BMesh representation
    bm = bmesh.from_edit_mesh(obj.data)
    
    # Update the mesh to ensure the selection gets updated correctly
    bm.faces.ensure_lookup_table()
    
    # Select faces whose normal's Z coordinate is positive (facing upwards)
    for face in bm.faces:
        if face.normal.z > 0:
            face.select = True
    
    # Update the mesh to reflect the selection change
    bmesh.update_edit_mesh(obj.data)
    
    # Extrude the selected faces
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0, 0, EXTRUDE_LENGTH)})  # Adjust the value as needed
    
    # Switch back to Object Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.location[2] -= EXTRUDE_LENGTH / 2

else:
    print("No mesh object selected.")






'''
# Apply a simple material
material = bpy.data.materials.new(name="SimpleMaterial")
material.diffuse_color = (0.6, 0.6, 0.6, 1)  # Grey color
sphere.data.materials.append(material)
'''



# Create a new material with metallic and shiny properties
material = bpy.data.materials.new(name="MetallicMaterial")
material.use_nodes = True
nodes = material.node_tree.nodes

# Get the Principled BSDF node to adjust its properties
if "Principled BSDF" in nodes:
    principled_node = nodes.get("Principled BSDF")
    principled_node.inputs['Base Color'].default_value = (175/255, 127/255, 80/255, 1)
    principled_node.inputs['Metallic'].default_value = 1.0  # Max metallic effect
    principled_node.inputs['Specular'].default_value = 0.5  # Adjust specular reflection
    principled_node.inputs['Roughness'].default_value = 0.15  # Lower value for smoother surface

sphere.data.materials.append(material)
coin.data.materials.append(material)
outer_cylinder.data.materials.append(material)



# Create a light source
light_data = bpy.data.lights.new(name="MyLight", type='POINT')
light_data.energy = 10000
light_object = bpy.data.objects.new(name="MyLight", object_data=light_data)
bpy.context.collection.objects.link(light_object)
light_object.location = (1, 1, 3)

# Create a camera
camera_data = bpy.data.cameras.new(name="MyCamera")
camera = bpy.data.objects.new("MyCamera", camera_data)
bpy.context.collection.objects.link(camera)
bpy.context.scene.camera = camera
camera.location = (0, -5, 5)

# Point the camera to the sphere
look_at = sphere.location
direction = look_at - camera.location
rot_quat = direction.to_track_quat('-Z', 'Y')
camera.rotation_euler = rot_quat.to_euler()

camera.rotation_mode = 'QUATERNION'

frames = 240
radius = 5
for frame in range(frames):
    # Calculate the angle for this frame
    angle = (math.pi * 2) * (frame / frames)
    
    # Calculate the camera's position using trigonometry
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    z = 5  # Keep the camera's initial height
    
    # Set camera's location
    camera.location = (x, y, z)
    
    # Make the camera look at the center point
    direction = - camera.location
    # Point the camera's '-Z' and use its 'Y' as up
    camera.rotation_quaternion = direction.to_track_quat('-Z', 'Y')
    
    # Insert keyframes for location and rotation
    camera.keyframe_insert(data_path="location", frame=frame)
    camera.keyframe_insert(data_path="rotation_quaternion", frame=frame)

bpy.context.scene.frame_start = 0
bpy.context.scene.frame_end = frames - 1



print(">>>", "starting rendering")

OUTPUT_DIRECTORY = "./" # "/Users/daniel/Documents/blender/"
do_animation = True
if do_animation:
    bpy.context.scene.render.engine = 'BLENDER_EEVEE' # 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    bpy.context.scene.render.ffmpeg.format = 'MPEG4'
    bpy.context.scene.render.ffmpeg.codec = 'H264'
    bpy.context.scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    bpy.context.scene.render.filepath = OUTPUT_DIRECTORY + "video.mp4"
    bpy.ops.render.render(animation=True)
else:
    bpy.context.scene.render.image_settings.file_format = 'PNG' # or any other format you prefer
    bpy.context.scene.render.filepath = OUTPUT_DIRECTORY + "image.png"
    bpy.ops.render.render(write_still=True)


# Render viewport
# bpy.ops.object.select_all(action='DESELECT')
# bpy.ops.render.opengl(write_still=True)  # Set write_still to True to save the render
