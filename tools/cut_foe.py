# -*- coding: utf-8 -*-
"""Geminiが白背景に横一列で描いたキャラを、1体ずつ透過PNGに切り分ける。
   使い方: python tools/cut_foe.py 画像 出し先フォルダ 名前1 名前2 ...
   左から順に 名前1, 名前2 ... で保存する。"""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage

src, outdir = sys.argv[1], sys.argv[2]
names = sys.argv[3:]
os.makedirs(outdir, exist_ok=True)

im = Image.open(src).convert("RGB")
a = np.array(im).astype(int)
h, w, _ = a.shape
white = a.min(axis=2) > 228

# 外周からつながった白だけ背景にする（体の中の白は残す）
lab, n = ndimage.label(white)
edge = set(lab[0].tolist()) | set(lab[-1].tolist()) | set(lab[:, 0].tolist()) | set(lab[:, -1].tolist())
edge.discard(0)
bg = np.isin(lab, list(edge))

fg = ~bg
fg = ndimage.binary_closing(fg, np.ones((5, 5)))
lab2, n2 = ndimage.label(fg)
sizes = ndimage.sum(fg, lab2, range(1, n2 + 1))
order = np.argsort(sizes)[::-1][:len(names)] + 1
boxes = []
for i in order:
    ys, xs = np.where(lab2 == i)
    boxes.append((xs.min(), ys.min(), xs.max(), ys.max(), i))
boxes.sort(key=lambda b: b[0])

rgba = np.dstack([a.astype(np.uint8), (~bg * 255).astype(np.uint8)])
for (x0, y0, x1, y1, i), name in zip(boxes, names):
    m = (lab2 == i)
    part = rgba[y0:y1 + 1, x0:x1 + 1].copy()
    part[..., 3] = (m[y0:y1 + 1, x0:x1 + 1] * 255).astype(np.uint8)
    p = os.path.join(outdir, name + ".png")
    Image.fromarray(part, "RGBA").save(p)
    print(name, part.shape[1], "x", part.shape[0], "->", p)
