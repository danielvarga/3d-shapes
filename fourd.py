# four D as in 4D -> 3D

import numpy as np
import skvideo.io  
import skimage.measure
import visvis as vv
import matplotlib.pyplot as plt


filename = "horse.mp4"
filename = "horse-slow.mp4" # 10x temporal upscale by runwayml.com
filename = "horse-slow-cut.mp4" # first 340 frames of horse-slow.mp4
# filename = "horse-hq-cut.mp4" # https://www.youtube.com/watch?v=QcNe8Akm1ts
# filename = "lapdance.mp4"
video = skvideo.io.vread(filename)  
print("video.shape", video.shape, video.size / 1e6, "megabytes")

video = (video > 50).astype(np.uint8).max(axis=3)
video = 1 - video

# this is specific to horse.mp4 that has those cinematic stripes at the top and bottom.
if filename == "horse.mp4":
    video = video[:, 144:444, :]
    video = video[:34] # first walk animation loop
    video = np.array([video] * 5)
    video = np.transpose(video, (1, 0, 2, 3))
    sh = video.shape
    video = video.reshape((sh[0]*sh[1], sh[2], sh[3]))
elif filename.startswith("horse-slow"):
    video = video[:, 144:444, :]
    video = video[:340] # first walk animation loop

    video = video.astype(np.float32)
    print("before spatial upsampling", video.shape, video.dtype, video.max())

    frames = []
    new_shape = (video.shape[1] * 4, video.shape[2] * 4)
    for frame in video:
        upscaled_frame = skimage.transform.resize(frame, new_shape, anti_aliasing=True)
        frames.append(upscaled_frame)
    video = np.array(frames)
    print("after spatial upsampling", video.shape, video.dtype, video.max())

# we destroy first and last frame, this is the laziest way to add front and back to polytope
video[0] = 0
video[-1] = 0

print("video.shape", video.shape, video.sum() / video.size)


'''
for t in range(50):
    plt.imshow(video[t])
    plt.show()
'''

video = np.transpose(video, (1, 0, 2))
video = video[::-1, :, :]

iso_val = 0.5
verts, faces, normals, values = skimage.measure.marching_cubes(video, level=iso_val, allow_degenerate=False)

print(f"{len(verts)} vertices, {len(faces)} faces")

print("vv visualization")
values = np.linalg.norm(normals[:, :2], axis=1)
vv.mesh(np.fliplr(verts), faces, normals, values)
vv.use().Run()
exit()
