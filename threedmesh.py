import sys
import numpy as np
from scipy.spatial import ConvexHull, Delaunay
from mayavi import mlab
from stl import mesh

from neighborhood import *


def gray_scott(n, laplacian):
    # *4 because the original formula summed rather than averaged.
    Du, Dv, F, k = 0.16*4, 0.08*4, 0.060, 0.062 # Coral

    def gray_scott_iteration(u, v, laplacian):
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
        gray_scott_iteration(u, v, laplacian)
        if i % 1000 == 0:
            print(i, np.std(v))
            sys.stdout.flush()

    print("v.min", v.min(), "v.max", v.max(), "before normalization")
    # we normalize values to [0, 1]
    v -= v.min()
    v /= v.max()

    return v


def save_stl(points, simplices, filename):
    # Create the numpy-stl mesh object
    stl_mesh = mesh.Mesh(np.zeros(simplices.shape[0], dtype=mesh.Mesh.dtype))
    for i, triangle in enumerate(simplices):
        for j in range(3):
            stl_mesh.vectors[i][j] = points[triangle[j]]

    stl_mesh.save(filename)


def main():
    n = 50000

    points = fibonacci_sphere(n, randomize=False)

    hull = ConvexHull(points)
    simplices = hull.simplices

    laplacian = build_graph(points)

    v = gray_scott(n, laplacian)

    # we do some gamma
    v = 1 - v
    v = v * v
    v = 1 - v

    # this is where the magic happens:
    points *= (v + 3.0)[:, None]

    save_stl(points, simplices, 'gray-scott.stl')

    mlab_mesh = mlab.triangular_mesh(points[:, 0], points[:, 1], points[:, 2], simplices,
        colormap='Blues', representation='mesh')

    mlab.show()


if __name__ == "__main__":
    main()
