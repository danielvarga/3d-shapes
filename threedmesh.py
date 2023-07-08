import numpy as np
from scipy.spatial import ConvexHull, Delaunay
from mayavi import mlab
from stl import mesh



# https://stackoverflow.com/questions/9600801/evenly-distributing-n-points-on-a-sphere/26127012#26127012
# TODO trivial to vectorize
def fibonacci_sphere(n, randomize=True):
    rnd = 1.
    if randomize:
        rnd = random.random() * n

    points = []
    offset = 2./n
    increment = np.pi * (3. - np.sqrt(5.));

    for i in range(n):
        y = ((i * offset) - 1) + (offset / 2);
        r = np.sqrt(1 - pow(y,2))

        phi = ((i + rnd) % n) * increment

        x = np.cos(phi) * r
        z = np.sin(phi) * r

        points.append([x,y,z])

    return np.array(points)




# Sample input points
points = np.random.normal(size=(50, 3))
points = fibonacci_sphere(200, randomize=False)

# Compute the convex hull
hull = ConvexHull(points)
simplices = hull.simplices

# Create the numpy-stl mesh object
stl_mesh = mesh.Mesh(np.zeros(simplices.shape[0], dtype=mesh.Mesh.dtype))
for i, triangle in enumerate(simplices):
    for j in range(3):
        stl_mesh.vectors[i][j] = points[triangle[j]]

# Save the mesh to an STL file
stl_mesh.save('convex_hull.stl')



# Create a triangular surface mesh using Mayavi
# mlab.triangular_mesh(vertices[:, 0], vertices[:, 1], vertices[:, 2], simplices)
mlab.triangular_mesh(points[:, 0], points[:, 1], points[:, 2], simplices)

# Display the visualization
mlab.show()
