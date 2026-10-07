# -*- coding: utf-8 -*-
"""Geminiの「左右2コマ」を2枚に分けて assets/still に保存する。
   使い方: python tools/split_still.py 元画像 左の名前 右の名前
           python tools/split_still.py 元画像 名前            （1枚絵のとき）
   外側の白い余白は落とし、まんなかの仕切りも落とす。"""
import sys, os
import numpy as np
from PIL import Image

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "still")
os.makedirs(A, exist_ok=True)
src = sys.argv[1]; names = sys.argv[2:]
im = Image.open(src).convert("RGB")
a = np.array(im).astype(int)
h, w, _ = a.shape

# 外側の明るい余白を落とす
bright = a.min(axis=2) > 214
cols = bright.mean(axis=0); rows = bright.mean(axis=1)
def trim(v):
    i, j = 0, len(v) - 1
    while i < j and v[i] > .92: i += 1
    while j > i and v[j] > .92: j -= 1
    return i, j
x0, x1 = trim(cols); y0, y1 = trim(rows)
im = im.crop((x0, y0, x1 + 1, y1 + 1))

if len(names) == 1:
    im.save(os.path.join(A, names[0] + ".jpg"), quality=88)
    print(names[0], im.size)
else:
    w2, h2 = im.size
    # まんなか付近の、いちばん明るい（＝仕切りの）列を探す
    b = np.array(im.convert("L")).astype(int).mean(axis=0)
    mid = w2 // 2
    band = range(max(0, mid - int(w2 * .06)), min(w2, mid + int(w2 * .06)))
    cut = max(band, key=lambda x: b[x])
    gap = int(w2 * .022)
    for nm, box in zip(names, [(0, 0, max(1, cut - gap), h2), (min(w2 - 1, cut + gap), 0, w2, h2)]):
        p = im.crop(box)
        p.save(os.path.join(A, nm + ".jpg"), quality=88)
        print(nm, p.size)
