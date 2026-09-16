# -*- coding: utf-8 -*-
"""Geminiの「左右2コマ」の挿絵を2枚に分けて、縦長のJPGにする。
   使い方: python split_scene.py 元画像 出力名   → assets/story/出力名_a.jpg, 出力名_b.jpg"""
import sys, os
from PIL import Image

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "story")
src, name = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
w, h = im.size
px = im.load()

def dark_col(x):  # 列の暗さ（真っ黒な区切りを探す）
    return sum(sum(px[x, y]) for y in range(0, h, 4))

# 真ん中あたりで一番暗い列が区切り。そこから左右に黒い帯を広げる
mid = min(range(int(w * .35), int(w * .65)), key=dark_col)
limit = dark_col(mid) * 1.6 + h * 6
l = mid
while l > 0 and dark_col(l - 1) < limit: l -= 1
r = mid
while r < w - 1 and dark_col(r + 1) < limit: r += 1

def trim(box):
    # まわりの黒い余白を落とす
    x0, y0, x1, y1 = box
    part = im.crop(box)
    g = part.convert("L").point(lambda v: 255 if v > 28 else 0)
    bb = g.getbbox() or (0, 0, part.width, part.height)
    return part.crop(bb)

for tag, box in (("a", (0, 0, l, h)), ("b", (r + 1, 0, w, h))):
    p = trim(box)
    # 縦長にそろえて、大きすぎれば縮める
    if p.height > 1100:
        p = p.resize((int(p.width * 1100 / p.height), 1100), Image.LANCZOS)
    out = os.path.join(A, f"{name}_{tag}.jpg")
    p.save(out, quality=86)
    print(out, p.size)
