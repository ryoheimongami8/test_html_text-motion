# Cut the 5 BEANS characters out of the white-background character sheet.
# bg = near-white connected to the border; per character keep the largest fg blob in its crop window.
# Outputs go to assets/ (sheet_alpha.png, char_1..5.png) so index.html's config.json can reference them.
import os
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

SRC = sys.argv[1]
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else 'assets'
os.makedirs(OUTDIR, exist_ok=True)
im = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float32) / 255
H, W, _ = im.shape
lum = im @ np.array([.299, .587, .114], np.float32)
sat = im.max(-1) - im.min(-1)

cand = (lum > .86) & (sat < .10)
lab, nl = ndi.label(cand)
border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
bg = np.isin(lab, border[border > 0])
fg = ~bg
fg = ndi.binary_opening(fg, iterations=1)

def soften(m):
    a = ndi.gaussian_filter(m.astype(np.float32), 1.0)
    return np.clip((a - .15) / .7, 0, 1)

# whole lineup
a = soften(fg)
Image.fromarray((np.dstack([im, a]) * 255 + .5).astype(np.uint8)).save(f'{OUTDIR}/sheet_alpha.png')

CROPS = [(0, 800, 700, 1035), (617, 408, 958, 1259), (1458, 683, 709, 1117), (1825, 392, 842, 1341), (2450, 925, 842, 892)]
# hand-placed separation lines where neighbours touch on the sheet (sheet px)
YY, XX = np.mgrid[0:H, 0:W]
KEEP = {
    1: (XX < 742) & ~((XX > 600) & (YY >= 1100)),                     # glasses | big's cuff
    2: ~((XX < 742) & (YY > 1000) & (YY < 1100)),                    # big | glasses' raised hand
    3: (XX < 2025) | ((XX < 2167) & (YY > 783) & (YY < 892)),        # grumpy (+ ear tip) | tall
    4: ((XX >= 2000) | (YY < 650)) & ~((XX < 2167) & (YY > 800) & (YY < 880)),      # tall | grumpy's ear
    5: np.ones((H, W), bool),
}
PAD = 60
for i, (x, y, w, h) in enumerate(CROPS, 1):
    x0, y0 = max(0, x - PAD), max(0, y - PAD)
    x1, y1 = min(W, x + w + PAD), min(H, y + h + PAD)
    sub = (fg & KEEP[i])[y0:y1, x0:x1]
    l, n = ndi.label(sub)
    # the character is the biggest blob whose centroid sits inside the nominal crop
    best, best_a = 0, 0
    for j, sl in enumerate(ndi.find_objects(l), 1):
        m = l[sl] == j
        ar = m.sum()
        cy, cx = ndi.center_of_mass(m)
        cy += sl[0].start + y0; cx += sl[1].start + x0
        if x <= cx <= x + w and y <= cy <= y + h and ar > best_a:
            best, best_a = j, ar
    m = l == best
    ys, xs = np.nonzero(m)
    bb = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    m = m[bb[1]:bb[3], bb[0]:bb[2]]
    rgb = im[y0:y1, x0:x1][bb[1]:bb[3], bb[0]:bb[2]]
    Image.fromarray((np.dstack([rgb, soften(m)]) * 255 + .5).astype(np.uint8)).save(f'{OUTDIR}/char_{i}.png')
    print(i, 'bbox', bb[2] - bb[0], bb[3] - bb[1])
