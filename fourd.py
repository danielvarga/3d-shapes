# four D as in 4D -> 3D

import numpy as np
import skvideo.io  
import skimage.measure
from stl import mesh
import visvis as vv
import matplotlib.pyplot as plt


filename = "horse.mp4"
filename = "horse-slow.mp4" # 10x temporal upscale by runwayml.com
filename = "horse-tensorpix-s4-t2.mp4" # done by app.tensorpix.ai from "horse.mp4", 4x spatial upscale, 2x temporal upscale


filename = "horse-tensorpix-s4-t4.mp4" # created from "horse-tensorpix-s4-t2.mp4" by 2x temporal upscale again.
# ...too big to load, hence this cut:
# ffmpeg -i horse-tensorpix-s4-t4.mp4 -ss 00:00:11.50 -t 00:00:03.00 horse-tensorpix-s4-t4-run-cut.mp4
# ffmpeg -i horse-tensorpix-s4-t8.mp4 -ss 00:00:22.00 -t 00:00:09.05 horse-tensorpix-s4-t8-run-cut.mp4
filename = "horse-tensorpix-s4-t8-run-cut.mp4"

'''
filename = "horse-slow-cut.mp4" # first 340 frames of horse-slow.mp4
filename = "horse-hq.mp4" # https://www.youtube.com/watch?v=QcNe8Akm1ts

# first ffmpeg -i horse-hq.mp4 -ss 00:00:02.50 -t 00:00:01.16 horse-hq-cut.mp4
# and then 10x temporal upscale by runwayml.com:
# filename = "horse-hq-cut-slow.mp4"
# filename = "lapdance.mp4"
'''

video = skvideo.io.vread(filename)  
print("video.shape", video.shape, video.size / 1e6, "megabytes")

# video = (video > 50).astype(np.uint8).max(axis=3)
video = (video[:, :, :, 1].astype(int) - video[:, :, :, 0].astype(int) > 128).astype(np.uint8)
video = 1 - video

# this is specific to horse.mp4 that has those cinematic stripes at the top and bottom.
if filename == "horse.mp4":
    video = video[:, 144:444, :]
    video = video[140:180] # first walk animation loop
    video = np.array([video] * 15)
    video = np.transpose(video, (1, 0, 2, 3))
    sh = video.shape
    video = video.reshape((sh[0]*sh[1], sh[2], sh[3]))
elif filename == "horse-tensorpix.mp4":
    video = video[:, 4*144:4*444, :] # same part as "horse-slow", but 4x spatial upscale
    video = video[280:320] # same part as "horse-slow", but 2x rather than 10x temporal upscale

    video = np.array([video] * 2 * 5) # 2 because the horse-slow had that, and 5 because this is 5 times faster.
    video = np.transpose(video, (1, 0, 2, 3))
    sh = video.shape
    video = video.reshape((sh[0]*sh[1], sh[2], sh[3]))
elif filename == "horse-tensorpix-s4-t8-run-cut.mp4":
    video = video[:, 4*144:4*444, :] # same part as "horse-slow", but 4x spatial upscale
    # it's already a cut, but the first and last few frames are ugly interpolated ones:
    video = video[:-66]

    do_conveyor_belt_removal = False
    # speed not yet tuned to be correct
    if do_conveyor_belt_removal:
        print("counteracting conveyor belt effect")
        video = video[::-1, :, :]
        speed = 2.2
        t, h, w = video.shape
        w2 = w + int(speed * t) + 1
        video2 = np.zeros((t, h, w2))
        for timestep in range(t):
            w_delta = int(np.around(speed * timestep))
            video2[timestep, :, w_delta:(w_delta+w)] = video[timestep, :, :]

        video2 = np.array([video2] * 2)
        video2 = np.transpose(video2, (1, 0, 2, 3))
        sh = video2.shape
        video2 = video2.reshape((sh[0]*sh[1], sh[2], sh[3]))

        video = video2
elif filename.startswith("horse-slow"):
    video = video[:, 144:444, :]
    video = video[1400:1600]

    do_conveyor_belt_removal = True
    if do_conveyor_belt_removal:
        print("counteracting conveyor belt effect")
        video = video[::-1, :, :]
        speed = 2.2
        t, h, w = video.shape
        w2 = w + int(speed * t) + 1
        video2 = np.zeros((t, h, w2))
        for timestep in range(t):
            w_delta = int(np.around(speed * timestep))
            video2[timestep, :, w_delta:(w_delta+w)] = video[timestep, :, :]

        video2 = np.array([video2] * 2)
        video2 = np.transpose(video2, (1, 0, 2, 3))
        sh = video2.shape
        video2 = video2.reshape((sh[0]*sh[1], sh[2], sh[3]))

        video = video2

    print("before spatial upsampling", video.shape, video.dtype, video.max())

    '''
    video = video.astype(np.float32)
    frames = []
    new_shape = (video.shape[1] * 4, video.shape[2] * 4)
    for frame in video:
        upscaled_frame = skimage.transform.resize(frame, new_shape, anti_aliasing=True)
        frames.append(upscaled_frame)
    video = np.array(frames)
    print("after spatial upsampling", video.shape, video.dtype, video.max())
    '''
elif filename.startswith("horse-hq"):
    video = video[:, 18:318, :]

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
temporal_scaling = 3 # one frame has the same width as temporal_scaling pixels.
verts, faces, normals, values = skimage.measure.marching_cubes(video, level=iso_val, allow_degenerate=False, spacing=(1, temporal_scaling, 1))

print(f"{len(verts)} vertices, {len(faces)} faces")


print("creating stl mesh")
your_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
for i, face in enumerate(faces):
    for j in range(3):
        your_mesh.vectors[i][j] = verts[face[j]]

print("vv visualization")
values = np.linalg.norm(normals[:, :2], axis=1)
vv.mesh(np.fliplr(verts), faces, normals, values)
vv.use().Run()


filename = f"horse.stl"
your_mesh.save(filename)
print(f"saved {filename}")


exit()
