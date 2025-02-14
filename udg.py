import numpy as np
import trimesh
import trimesh.transformations as tf

# Parameters: adjust these as needed
ball_radius = 0.03        # Radius for the sphere at each point
cylinder_radius = 0.03   # Radius for the cylinders (edges)
unit_length = 1.0        # Expected unit distance between connected points
threshold = 0.05         # Allowable deviation from unit distance

# Your set of 3D points
def nechustan():
    return np.array([
        [-1/2, -1/2, 0],
        [-1/2, 1/2, 0],
        [1/2, -1/2, 0],
        [1/2, 1/2, 0],
        [-5/6, 0, -np.sqrt(23)/6],
        [5/6, 0, -np.sqrt(23)/6],
        [0, 1/16 * (2 - np.sqrt(46)), np.roots([16384, 0, -14080, 0, 1369])[2]],
        [0, 1/16 * (-2 + np.sqrt(46)), np.roots([16384, 0, -14080, 0, 1369])[2]],
        [0, 1/16 * (-2 - np.sqrt(46)), np.roots([16384, 0, -14080, 0, 1369])[0]],
        [0, 1/16 * (2 + np.sqrt(46)), np.roots([16384, 0, -14080, 0, 1369])[0]]
    ])

def haugstrup():
    return np.array([
        [ 1.1785113,   0.,          0.        ],
        [ 0.,          1.1785113,   0.        ],
        [ 0.,          0.,          1.1785113 ],
        [ 0.31426968,  0.31426968, -0.3928371 ],
        [ 0.31426968, -0.3928371,   0.31426968],
        [-0.3928371,   0.31426968,  0.31426968],
        [ 0.94280904,  0.94280904,  0.23570226],
        [ 0.94280904,  0.23570226,  0.94280904],
        [ 0.23570226,  0.94280904,  0.94280904],
        [ 0.23570226,  0.23570226,  0.23570226],
        [ 0.54997194,  0.54997194,  0.54997194],
        [-0.45026651,  0.37171126, -0.38253597],
        [ 0.48538513,  0.68586851, -0.22172165],
        [ 0.30658109, -0.28163251, -0.40052569],
        [ 0.75554503,  0.46284175,  0.71490671],
        [ 0.57674099, -0.50465927,  0.53610267],
        [-0.18880331,  0.72469895,  0.51581624],
        [-0.38509282, -0.33741521,  0.31952673],
        [ 0.16133597, -0.15873793,  0.20446152],
        [ 0.26822346,  0.41962571,  0.31134901],
        [-0.38379233,  0.90602325,  1.00011477],
        [ 0.28299999,  1.56647086,  0.65486567],
        [ 0.59304208,  0.75730501,  1.15398943],
        [ 0.7018372,   1.21141872, -0.18090546],
        [ 1.01187929,  0.40225287,  0.31821831],
        [-0.26070818,  1.02370404,  0.01472068],
        [ 0.07965331,  0.13540886,  0.56265438],
        [ 0.45477549,  0.58598804,  0.55922763],
        [ 0.26943504,  1.06970031,  0.26085581],
        [ 0.90602325,  1.00011477, -0.38379233],
        [ 1.56647086,  0.65486567,  0.28299999],
        [ 0.75730501,  1.15398943,  0.59304208],
        [ 1.21141872, -0.18090546,  0.7018372 ],
        [ 0.40225287,  0.31821831,  1.01187929],
        [ 1.02370404,  0.01472068, -0.26070818],
        [ 0.13540886,  0.56265438,  0.07965331],
        [ 0.58598804,  0.55922763,  0.45477549],
        [ 1.06970031,  0.26085581,  0.26943504],
        [ 1.00011477, -0.38379233,  0.90602325],
        [ 0.65486567,  0.28299999,  1.56647086],
        [ 1.15398943,  0.59304208,  0.75730501],
        [-0.18090546,  0.7018372,   1.21141872],
        [ 0.31821831,  1.01187929,  0.40225287],
        [ 0.01472068, -0.26070818,  1.02370404],
        [ 0.56265438,  0.07965331,  0.13540886],
        [ 0.55922763,  0.45477549,  0.58598804],
        [ 0.26085581,  0.26943504,  1.06970031]])


# points = nechustan()
points = haugstrup()


def create_cylinder_between_points(p1, p2, radius, sections=32):
    """
    Create a cylinder mesh connecting point p1 to point p2.
    The cylinder is built along the Z-axis then transformed.
    """
    p1 = np.array(p1)
    p2 = np.array(p2)
    vector = p2 - p1
    length = np.linalg.norm(vector)
    if length == 0:
        return None

    # Create a cylinder along the Z-axis.
    # trimesh.creation.cylinder creates a mesh centered at the origin,
    # spanning from -height/2 to +height/2.
    cyl = trimesh.creation.cylinder(radius=radius, height=length, sections=sections)
    
    # Shift it so that its base is at z=0 (instead of -length/2).
    shift = tf.translation_matrix([0, 0, length / 2])
    cyl.apply_transform(shift)

    # Compute the rotation matrix to align the Z-axis with the vector (p2-p1).
    direction = vector / length
    T_align = trimesh.geometry.align_vectors([0, 0, 1], direction, return_angle=False)
    cyl.apply_transform(T_align)
    
    # Finally, translate the cylinder so that it starts at p1.
    translation = tf.translation_matrix(p1)
    cyl.apply_transform(translation)
    
    return cyl

meshes = []

# Create spheres at each point
for p in points:
    sphere_mesh = trimesh.creation.icosphere(radius=ball_radius, subdivisions=3)
    sphere_mesh.apply_translation(p)
    meshes.append(sphere_mesh)

# Create cylinders for each pair of points that satisfy the unit distance condition
n = len(points)
for i in range(n):
    for j in range(i + 1, n):
        p1 = np.array(points[i])
        p2 = np.array(points[j])
        dist = np.linalg.norm(p2 - p1)
        if abs(dist - unit_length) <= threshold:
            cyl = create_cylinder_between_points(p1, p2, cylinder_radius)
            if cyl is not None:
                meshes.append(cyl)

# Combine all meshes into one. (Note: This is a simple concatenation,
# so overlapping parts are not "boolean-unioned".)
combined = trimesh.util.concatenate(meshes)

# Export the combined mesh to an STL file.
stl_filename = 'graph_model.stl'
combined.export(stl_filename)
print(f"STL file '{stl_filename}' has been saved.")
