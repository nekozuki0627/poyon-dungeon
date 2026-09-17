# -*- coding: utf-8 -*-
"""Geminiの「右向きに走る4コマ」（白背景。1列でも2×2でもよい）を1コマずつ切り抜く。
   使い方: python cut_run.py 画像 出力名   → assets/run/出力名_0.png 〜 _3.png
   並び順は 上の段の左から → 下の段の左から。足元の高さと体の中心をそろえ、同じ大きさの透過PNGにする。"""
import sys, os
from collections import deque
import numpy as np
from PIL import Image

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "run")
os.makedirs(A, exist_ok=True)
src, name = sys.argv[1], sys.argv[2]
OUT_H = int(sys.argv[3]) if len(sys.argv) > 3 else 220
im = np.array(Image.open(src).convert("RGB")).astype(int)
h, w, _ = im.shape
white = im.min(axis=2) > 232

# 外周からつながった白だけを背景にする（白い服やハイライトは残す）
bg = np.zeros((h, w), bool)
q = deque()
for x in range(w):
    for y in (0, h - 1):
        if white[y, x] and not bg[y, x]: bg[y, x] = True; q.append((y, x))
for y in range(h):
    for x in (0, w - 1):
        if white[y, x] and not bg[y, x]: bg[y, x] = True; q.append((y, x))
while q:
    y, x = q.popleft()
    for ny, nx in ((y+1, x), (y-1, x), (y, x+1), (y, x-1)):
        if 0 <= ny < h and 0 <= nx < w and not bg[ny, nx] and white[ny, nx]:
            bg[ny, nx] = True; q.append((ny, nx))
fg = ~bg

def bands(counts, minsize):
    """0が続く所で区切って、中身のある区間を返す"""
    res, start = [], None
    for i, c in enumerate(counts):
        if c > 0 and start is None: start = i
        if c == 0 and start is not None:
            if i - start >= minsize: res.append((start, i))
            start = None
    if start is not None and len(counts) - start >= minsize: res.append((start, len(counts)))
    return res

cells = []
rows = bands(fg.sum(axis=1) > 2, h // 12)
for r0, r1 in rows:
    cols = bands(fg[r0:r1].sum(axis=0) > 2, w // 16)
    for c0, c1 in cols:
        sub = fg[r0:r1, c0:c1]
        ys, xs = np.nonzero(sub)
        cells.append((r0 + ys.min(), r0 + ys.max() + 1, c0 + xs.min(), c0 + xs.max() + 1))
if len(cells) != 4:
    print("コマ数が4ではありません:", len(cells), cells)
cells = cells[:4]

rgba = np.dstack([im.astype(np.uint8), np.where(fg, 255, 0).astype(np.uint8)])
# 背景に接するふちを少しやわらげる
edge = fg & (np.roll(bg, 1, 0) | np.roll(bg, -1, 0) | np.roll(bg, 1, 1) | np.roll(bg, -1, 1))
m = 255 - im.min(axis=2)
rgba[..., 3] = np.where(edge, np.clip((m - 12) * 4, 0, 255), rgba[..., 3]).astype(np.uint8)

bw = max(c[3] - c[2] for c in cells); bh = max(c[1] - c[0] for c in cells)
pad = 6
for i, (y0, y1, x0, x1) in enumerate(cells):
    canvas = Image.new("RGBA", (bw + pad * 2, bh + pad * 2), (0, 0, 0, 0))
    piece = Image.fromarray(rgba[y0:y1, x0:x1])
    cx = pad + (bw - (x1 - x0)) // 2
    cy = pad + bh - (y1 - y0)          # 足元（下端）をそろえる
    canvas.alpha_composite(piece, (cx, cy))
    k = OUT_H / canvas.height
    canvas = canvas.resize((max(1, round(canvas.width * k)), OUT_H), Image.LANCZOS)
    canvas.save(os.path.join(A, f"{name}_{i}.png"))
print("ok", name, len(cells), (bw, bh))
