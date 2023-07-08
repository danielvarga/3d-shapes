import sys
import numpy as np
from scipy.spatial import ConvexHull, Delaunay
from mayavi import mlab
from stl import mesh

from neighborhood import *


# https://stackoverflow.com/questions/9600801/evenly-distributing-n-points-on-a-sphere/26127012#26127012
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


n = 50000

# Sample input points
points = fibonacci_sphere(n, randomize=False)


tree = scipy.spatial.cKDTree(points)
r = optimize_radius(tree)


edges = tree.query_pairs(r)
hoods = find_hoods(edges, n)
laplacian = sparse_laplacian(n, hoods)
assert np.allclose(laplacian.dot(np.ones(n)), np.zeros(n))


# *4 because the original formula summed rather than averaged.
Du, Dv, F, k = 0.16*4, 0.08*4, 0.060, 0.062 # Coral

def gray_scott_update(u, v, laplacian):
    uvv = u*v*v
    Lu = laplacian.dot(u)
    Lv = laplacian.dot(v)
    u += (Du*Lu - uvv +  F   *(1-u))
    v += (Dv*Lv + uvv - (F+k)*v    )

u = 0.2 * np.random.random(n) + 1
v = 0.2 * np.random.random(n)

n_iter = 10000
print("starting", n_iter, "Gray-Scott iterations")
for i in range(1, n_iter+1):
    gray_scott_update(u, v, laplacian)
    if i % 1000 == 0:
        print(i, np.std(v))
        sys.stdout.flush()


# Compute the convex hull
hull = ConvexHull(points)
simplices = hull.simplices



print(v.min(), v.max())
# we normalize values to [0, 1]
v -= v.min()
v /= v.max()

# we do some gamma
v = 1 - v
v = v * v
v = 1 - v

# this is where the magic is supposed to happen
points *= (v + 3.0)[:, None]


'''
x, y, z = points.T
freq = 10
altitudes = np.random.uniform(size=(len(points), ), low=0.5, high=1.0)
altitudes = (np.sin(x*freq) + np.sin(y*freq) + np.sin(z*freq) / 3) + 10
points *= altitudes[:, None]
'''

# Create the numpy-stl mesh object
stl_mesh = mesh.Mesh(np.zeros(simplices.shape[0], dtype=mesh.Mesh.dtype))
for i, triangle in enumerate(simplices):
    for j in range(3):
        stl_mesh.vectors[i][j] = points[triangle[j]]

# Save the mesh to an STL file
stl_mesh.save('convex_hull.stl')



# Create a triangular surface mesh using Mayavi
# mlab.triangular_mesh(vertices[:, 0], vertices[:, 1], vertices[:, 2], simplices)
mlab_mesh = mlab.triangular_mesh(points[:, 0], points[:, 1], points[:, 2], simplices,
    colormap='Blues', representation='mesh', opacity=1.0)

'''
mlab_surface = mlab.pipeline.surface(mlab_mesh)

mlab_surface.actor.property.color = (0.8, 0.8, 0.8)
# mlab_surface.module_manager.scalar_lut_manager.lut.table = np.ones((256, 4), dtype=float)
# mlab_surface.module_manager.scalar_lut_manager.lut.table[:, :3] = np.linspace(0, 1, 256)[:, np.newaxis]

mlab_surface.actor.property.opacity = 1.0  # Set opacity to 1 (non-transparent)
mlab_surface.actor.property.edge_visibility = True  # Show edges
# Display the visualization
'''

mlab.draw()

mlab.show()
