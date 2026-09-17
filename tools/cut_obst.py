# -*- coding: utf-8 -*-
"""Geminiの「ステージ用の障害物4つ（白背景に横一列）」を切り抜く。
   使い方: python cut_obst.py 画像 ステージ名 [しきい値]
   → assets/stage_obj/ステージ名_spike1.png / _spike3.png / _hang.png / _bat.png
   外周からつながった「明るい色」を背景にする（うすい光のもやも一緒に消える）。"""
import sys, os
from collections import deque
import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "stage_obj")
os.makedirs(OUT, exist_ok=True)
src, name = sys.argv[1], sys.argv[2]
TH = int(sys.argv[3]) if len(sys.argv) > 3 else 190
rgb = np.array(Image.open(src).convert("RGB")).astype(int)
h, w, _ = rgb.shape
light = rgb.min(axis=2) > TH
bg = np.zeros((h, w), bool); q = deque()
for x in range(w):
    for y in (0, h - 1):
        if light[y, x] and not bg[y, x]: bg[y, x] = True; q.append((y, x))
for y in range(h):
    for x in (0, w - 1):
        if light[y, x] and not bg[y, x]: bg[y, x] = True; q.append((y, x))
while q:
    y, x = q.popleft()
    for ny, nx in ((y+1, x), (y-1, x), (y, x+1), (y, x-1)):
        if 0 <= ny < h and 0 <= nx < w and not bg[ny, nx] and light[ny, nx]:
            bg[ny, nx] = True; q.append((ny, nx))
fg = ~bg
cols = fg.sum(axis=0)
parts, start = [], None
for x, c in enumerate(list(cols) + [0]):
    if c > 2 and start is None: start = x
    if c <= 2 and start is not None:
        if x - start > 25: parts.append((start, x))
        start = None
print("parts", parts)
assert len(parts) == 4, "4つに分かれなかった"
alpha = np.where(fg, 255, 0).astype(np.uint8)
img = np.dstack([rgb.astype(np.uint8), alpha])
for (x0, x1), key in zip(parts, ["spike1", "spike3", "hang", "bat"]):
    sub = Image.fromarray(img[:, x0:x1], "RGBA")
    sub = sub.crop(sub.getbbox())
    sub.save(os.path.join(OUT, f"{name}_{key}.png"))
    print(key, sub.size)
