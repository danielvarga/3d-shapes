# four D as in 4D -> 3D

import numpy as np
import skvideo.io  
import skimage.measure
import visvis as vv
import matplotlib.pyplot as plt


filename = "horse.mp4"
filename = "horse-slow.mp4" # 10x temporal upscale by runwayml.com
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
elif filename.startswith("horse-slow"):
    video = video[:, 144:444, :]
    video = video[1400:1660] # first walk animation loop

    print(video.shape)
    video = video[::-1, :, :]
    speed = 2.0
    t, h, w = video.shape
    w2 = w + int(speed * t) + 1
    video2 = np.zeros((t, h, w2))
    for timestep in range(t):
        w_delta = int(np.around(speed * timestep))
        video2[timestep, :, w_delta:(w_delta+w)] = video[timestep, :, :]

    video = video2
    video = video.astype(np.float32)
    print("before spatial upsampling", video.shape, video.dtype, video.max())

    '''
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
verts, faces, normals, values = skimage.measure.marching_cubes(video, level=iso_val, allow_degenerate=False)

print(f"{len(verts)} vertices, {len(faces)} faces")

print("vv visualization")
values = np.linalg.norm(normals[:, :2], axis=1)
vv.mesh(np.fliplr(verts), faces, normals, values)
vv.use().Run()
exit()
