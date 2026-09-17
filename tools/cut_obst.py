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
DIL = int(sys.argv[4]) if len(sys.argv) > 4 else 2
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
# 絵の内側に閉じこめられた白いすき間（つるの間など）も、ある程度の大きさなら背景として抜く
white = rgb.min(axis=2) > 238
seen = bg.copy()
for y0 in range(0, h, 2):
    for x0 in range(0, w, 2):
        if white[y0, x0] and not seen[y0, x0]:
            q = deque([(y0, x0)]); seen[y0, x0] = True; pts = []
            while q:
                y, x = q.popleft(); pts.append((y, x))
                for ny, nx in ((y+1, x), (y-1, x), (y, x+1), (y, x-1)):
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and white[ny, nx]:
                        seen[ny, nx] = True; q.append((ny, nx))
            if len(pts) > 120:
                for y, x in pts: bg[y, x] = True
fg = ~bg
# かたまりごとに分ける（縦に2つ重なっていても分けられるように）。
# 小さく縮めた図で、近いかけら同士をつなげてからラベルを付ける
S = 4
sh, sw = h // S, w // S
small = fg[:sh * S, :sw * S].reshape(sh, S, sw, S).any(axis=(1, 3))
grow = small.copy()
for _ in range(DIL):   # 少し太らせて、近いかけらをつなぐ
    g2 = grow.copy()
    g2[1:, :] |= grow[:-1, :]; g2[:-1, :] |= grow[1:, :]; g2[:, 1:] |= grow[:, :-1]; g2[:, :-1] |= grow[:, 1:]
    grow = g2
lab = np.zeros((sh, sw), int); n = 0; boxes = []
for y in range(sh):
    for x in range(sw):
        if grow[y, x] and not lab[y, x]:
            n += 1; q = deque([(y, x)]); lab[y, x] = n; ys = []; xs = []; cnt = 0
            while q:
                cy, cx = q.popleft(); ys.append(cy); xs.append(cx); cnt += small[cy, cx]
                for ny, nx in ((cy+1, cx), (cy-1, cx), (cy, cx+1), (cy, cx-1)):
                    if 0 <= ny < sh and 0 <= nx < sw and grow[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = n; q.append((ny, nx))
            boxes.append((cnt, n, min(ys) * S, max(ys) * S + S, min(xs) * S, max(xs) * S + S))
boxes.sort(reverse=True)
big = boxes[:4]
print("parts", [(b[2], b[3], b[4], b[5], b[0]) for b in big], "others", [b[0] for b in boxes[4:8]])
assert len(big) == 4, "4つに分かれなかった"
big.sort(key=lambda b: (b[4] + b[5]) / 2)
# 並びがちがうときは、左から数えた番号で並べかえを指定する（例 "0,2,1,3"）
if len(sys.argv) > 5: big = [big[int(i)] for i in sys.argv[5].split(",")]
# 並びは左から ①1個 ②3個 ③吊るすもの ④飛ぶもの。③④が縦に重なったときは、上にあるほうを③にする
if abs((big[2][4] + big[2][5]) - (big[3][4] + big[3][5])) < 0.25 * (big[3][5] - big[3][4]) * 2 and big[2][2] > big[3][2]:
    big[2], big[3] = big[3], big[2]
labfull = np.kron(lab, np.ones((S, S), int))
alpha_all = np.where(fg, 255, 0).astype(np.uint8)
for b, key in zip(big, ["spike1", "spike3", "hang", "bat"]):
    m = np.zeros((h, w), bool); m[:sh * S, :sw * S] = labfull == b[1]
    a = np.where(m & fg, 255, 0).astype(np.uint8)
    sub = Image.fromarray(np.dstack([rgb.astype(np.uint8), a]), "RGBA")
    sub = sub.crop(sub.getbbox())
    sub.save(os.path.join(OUT, f"{name}_{key}.png"))
    print(key, sub.size)
