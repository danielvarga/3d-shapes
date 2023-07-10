import sys
from mayavi import mlab

filename, = sys.argv[1:]
mesh = mlab.pipeline.open(filename)
mlab.pipeline.surface(mesh)
mlab.show()
