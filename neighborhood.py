import scipy.spatial
import numpy as np


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


def test_tree_query_pairs(ps):
    s = 0
    for i, a in enumerate(ps):
        for j, b in enumerate(ps):
            if j<=i:
                continue
            if np.linalg.norm(a-b) < r:
                s += 1
    tree = scipy.spatial.cKDTree(ps)
    neis = tree.query_pairs(r)
    assert s == len(neis)


def find_hoods(edges, n):
    hoods = {}
    for a in range(n):
        hoods[a] = []
    for a, b in edges:
        hoods[a].append(b)
        hoods[b].append(a)
    return hoods


def optimize_radius(kdtree):
    # let's find the smallest radius that leads to a neighborhood graph with average degree > 6.
    # too lazy to calculate it analytically for the Fibonacci sphere,
    # too lazy to set radius on a per-point level for complex surfaces.
    n = kdtree.n
    r = np.sqrt(1.0/n)
    for i in range(100):
        edges = kdtree.query_pairs(r)
        hoods = find_hoods(edges, n)
        sizes = np.array(list(map(len, hoods.values())))
        avgdeg = sizes.mean()
        mindeg = sizes.min()
        maxdeg = sizes.max()
        print("radius", r, "average degree", avgdeg, "min", mindeg, "max", maxdeg)
        if avgdeg >= 6:
            print("final radius", r)
            return r
        r *= 1.2
    assert False, "could not find proper radius"


def sparse_laplacian(n, hoods):
    data = []
    row = []
    col = []
    for a, hood in hoods.items():
        m = len(hood)
        if m > 0:
            data += [1.0 / m] * m
            row += [a] * m
            col += hood
    s = scipy.sparse.csr_matrix((data, (row, col)), shape=(n, n))
    # dealing with isolated vertices so that all-1 is still an eigenvector.
    s.setdiag([-1 if len(hoods[a])>0 else 0 for a in range(n)])
    return s


def build_graph(points):
    n = len(points)
    tree = scipy.spatial.cKDTree(points)
    r = optimize_radius(tree)
    edges = tree.query_pairs(r)
    hoods = find_hoods(edges, n)
    laplacian = sparse_laplacian(n, hoods)
    assert np.allclose(laplacian.dot(np.ones(n)), np.zeros(n))
    return laplacian
