import sys
import numpy as np
from numpy import sin, cos, pi
from skimage import measure
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from stl import mesh
import visvis as vv


def dot(p1, p2):
    return p1.real * p2.real + p1.imag * p2.imag


def sd_reuleaux_triangle(p, radius):
    triangle = np.exp(np.pi * 2j / 3 * np.arange(3)) / 3 ** 0.5
    x = np.sqrt(radius ** 2 - 1 / 4) + triangle[1].real
    dual_triangle = x * np.exp(np.pi * 2j / 3 * np.array([1, 3, 5]))
    dists =  np.abs(dual_triangle[:, None] - p[None, :]).max(axis=0) - radius
    return dists


def test_sd():
    n = 1000
    grid = np.mgrid[-1:1:n * 1j, -1:1: n * 1j]
    grid = np.transpose(grid, (1, 2, 0))
    x = grid[..., 0]
    y = grid[..., 1]
    xy_grid = x + 1j * y
    p = xy_grid.flatten()
    radius = 1.0
    values = sd_reuleaux_triangle(p, radius)
    values[values <= 0] = -1
    values = values.reshape(xy_grid.shape)
    print(values.shape)
    plt.imshow(values) # [400:600, 400:600]

    # keep this in sync with sd_reuleaux_triangle(), otherwise it's not testing it
    triangle = np.exp(np.pi * 2j / 3 * np.arange(3)) / 3 ** 0.5
    plt.scatter((triangle.imag + 1) / 2 * n, (triangle.real + 1) / 2 * n, marker='x')
    x = np.sqrt(radius ** 2 - 1 / 4) + triangle[1].real
    dual_triangle = x * np.exp(np.pi * 2j / 3 * np.array([1, 3, 5]))
    plt.scatter((dual_triangle.imag + 1) / 2 * n, (dual_triangle.real + 1) / 2 * n)

    plt.show()


# test_sd() ; exit()


def fun(ps, center_radius, triangle_side, reuleaux_radius, twist_ratio):
    assert ps.shape[-1] == 3
    shape = ps.shape[:-1]
    ps = ps.reshape((-1, 3))
    x, y, z = ps[:, 0], ps[:, 1], ps[:, 2]
    xy = x + 1j * y
    rot = xy / np.abs(xy)
    plane_angle = np.arctan2(rot.imag, rot.real)
    twist_angle = plane_angle * twist_ratio
    twist = np.exp(1j * twist_angle)
    pp = np.abs(xy) - center_radius + 1j * z
    rotpp = pp * twist
    values = sd_reuleaux_triangle(rotpp / triangle_side, radius=reuleaux_radius)
    return values.reshape(shape)


grid_size, center_radius, triangle_side, reuleaux_radius, twist_ratio  = map(float, sys.argv[1: ])

cube_size = center_radius + triangle_side


n = int(grid_size)

grid = np.mgrid[
    -cube_size: cube_size: n * 1j,
    -cube_size: cube_size: n * 1j,
    -cube_size: cube_size: n * 1j]
grid = np.transpose(grid, (1, 2, 3, 0))
x, y, z = grid[..., 0], grid[..., 1], grid[..., 2]

vol = fun(grid, center_radius=center_radius, triangle_side=triangle_side,
    reuleaux_radius=reuleaux_radius, twist_ratio=twist_ratio)


def visualize_2d_slices(vol):
    print("cube side (not size)", 2 * cube_size)
    plt.imshow(vol[vol.shape[0] // 2, :, :] > 0)
    plt.show()
    plt.imshow(vol[:, vol.shape[0] // 2, :] > 0)
    plt.show()
    plt.imshow(vol[:, :, vol.shape[2] // 2] > 0)
    plt.show()


visualize_2d_slices(vol)


def find_changes(vec):
    switches = vec[1:] - vec[:-1]
    assert np.count_nonzero(switches == +1) == 2
    assert np.count_nonzero(switches == -1) == 2
    ups = np.where(switches == +1)[0]
    downs = np.where(switches == -1)[0]
    return np.array([ups[0], downs[0], ups[1], downs[1]])


def stats(switches):
    print("inner diag", switches[2] - switches[1])
    print("outer diag", switches[3] - switches[0])
    print("center diag", switches[2:].mean() - switches[:2].mean())
    print("thickness", (switches[1]- switches[0] + switches[3]- switches[2]) / 2)


def verify_parameters(vol):
    ring_slice = (vol[:, :, vol.shape[2] // 2] < 0).astype(int)
    ring_slice_x = ring_slice[ring_slice.shape[0] // 2, :]
    ring_slice_y = ring_slice[:, ring_slice.shape[1] // 2]

    spacing = 2 * cube_size / n
    switches_x = find_changes(ring_slice_x) * spacing
    print("----\nhorizontal piercing")
    stats(switches_x)
    switches_y = find_changes(ring_slice_y) * spacing
    print("----\nvertical piercing")
    stats(switches_y)


verify_parameters(vol)


# vol[n//2:, :, :] = 1e-3
# vol = vol[::-1, :, :]
iso_val = 0.0
verts, faces, normals, values = measure.marching_cubes(vol, level=iso_val,
    # the [blah] * 3 means [blah, blah, blah], not [3 * blah]!
    spacing=[2 * cube_size / n] * 3, allow_degenerate=False)

print(f"{len(verts)} vertices, {len(faces)} faces")

print("creating stl mesh")
your_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
for i, face in enumerate(faces):
    for j in range(3):
        your_mesh.vectors[i][j] = verts[face[j]]

filename = f"reuleaux-mesh-n{n}-center_radius{center_radius}-triangle_side{triangle_side}-reuleaux_radius{reuleaux_radius}-twist_ratio{twist_ratio}.stl"
your_mesh.save(filename)


print("vv visualization")
values = np.linalg.norm(normals[:, :2], axis=1)
vv.mesh(np.fliplr(verts), faces, normals, values)
vv.use().Run()
exit()


print("matplotlib visualization")
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot_trisurf(verts[:, 0], verts[:,1], faces, verts[:, 2],
                cmap='Spectral', lw=1)
ax.set_xlim(0, 2 * cube_size)
ax.set_ylim(0, 2 * cube_size)
ax.set_zlim(0, 2 * cube_size)
plt.show()
