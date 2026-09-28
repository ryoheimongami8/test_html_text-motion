# Key out the plain light background of the Wan clip while keeping eye whites
# (bg = low-diff region connected to the frame border) and a soft contact shadow.
import subprocess, sys
import numpy as np
from scipy import ndimage as ndi

SRC, OUT, PREV = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, S = 1920, 1080, 2  # analyze at half res
w, h = W // S, H // S

raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                     capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
n = len(fr)
print('frames', n)

small = fr[:, ::S, ::S].astype(np.float32) / 255
lum = small @ np.array([.299, .587, .114], np.float32)
plate = ndi.uniform_filter(np.percentile(lum, 92, axis=0), 25)  # clean background luminance

sat = small.max(-1) - small.min(-1)
out_frames = []
for i in range(n):
    d = plate - lum[i]
    cand = (lum[i] > .70) & (sat[i] < .08)
    lab, nl = ndi.label(cand)
    idx = np.arange(1, nl + 1)
    area = ndi.sum(cand, lab, idx)
    blu = ndi.mean(small[i][..., 2] - small[i][..., 0], lab, idx)
    md = ndi.mean(d, lab, idx)
    sd = ndi.standard_deviation(lum[i], lab, idx)
    border = np.zeros(nl + 1, bool)
    border[np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))] = True
    keep = (blu >= .02) | ((md > .1) & (sd < .04))           # glasses lenses, metal buckles
    crowd = i > n * .5                                       # enclosed gaps only exist once the squad bunches up
    isbg = border[1:] | (~keep & (area > (450 if crowd else 4000)))
    fg = ~np.concatenate([[False], isbg])[lab]
    fg = ndi.binary_opening(fg, iterations=1)
    # upsample mask, soften edge a touch
    a = np.repeat(np.repeat(fg.astype(np.float32), S, 0), S, 1)
    a = ndi.gaussian_filter(a, 1.0)
    a = np.clip((a - .15) / .7, 0, 1)
    # shadow on bg: darkness vs plate
    dl = np.repeat(np.repeat(np.clip(d, 0, None), S, 0), S, 1)
    sh = np.clip((dl - .025) * 5.0, 0, .55) * (1 - a)
    rgb = fr[i].astype(np.float32) / 255
    alpha = a + sh
    col = rgb * a[..., None] / np.maximum(alpha, 1e-4)[..., None]  # shadow is black
    rgba = np.concatenate([col, alpha[..., None]], -1)
    out_frames.append((np.clip(rgba, 0, 1) * 255 + .5).astype(np.uint8))
    if i % 30 == 0: print(i)

buf = np.stack(out_frames).tobytes()
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '12M', '-auto-alt-ref', '0', OUT], input=buf, check=True)
# preview: composite on magenta at 3 times
idx = [int(n * x) for x in (.03, .1, .6, .97)]
prev = []
for j in idx:
    f = out_frames[j].astype(np.float32) / 255
    c = f[..., :3] * f[..., 3:] + np.array([1, 0, 1]) * (1 - f[..., 3:])
    prev.append(c[::3, ::3])
from PIL import Image
Image.fromarray((np.concatenate(prev, 1) * 255).astype(np.uint8)).save(PREV)
print('done')
