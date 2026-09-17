# -*- coding: utf-8 -*-
"""Geminiの「左右2コマ」の挿絵を2枚に分けて、縦長のJPGにする。
   使い方: python split_home.py 元画像 系統_段階   → assets/home/系統_段階_clear.jpg（左）, _fail.jpg（右）
   区切りは黒とは限らない（白や生成りの枠で来ることがある）ので、
   「縦にまっすぐ同じ色が続く列」を区切りとみなす。"""
import sys, os
from PIL import Image, ImageStat

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "home")
src, name = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
w, h = im.size
px = im.load()
y0, y1 = int(h * .08), int(h * .92)

def col_var(x):
    # 列の色のばらつき。区切りの列はほぼ一色
    vals = [sum(px[x, y]) for y in range(y0, y1, 3)]
    m = sum(vals) / len(vals)
    return sum((v - m) ** 2 for v in vals) / len(vals)

mid = min(range(int(w * .35), int(w * .65)), key=col_var)
base = col_var(mid)
lim = max(base * 4, 400)
l = mid
while l > 0 and col_var(l - 1) < lim: l -= 1
r = mid
while r < w - 1 and col_var(r + 1) < lim: r += 1
print("区切り", l, r)

def trim(part):
    # 外側の枠（一色の帯）を落とす：各辺から、一色の行・列が続くあいだ削る
    pp = part.load(); pw, ph = part.size
    def flat_row(y):
        v = [sum(pp[x, y]) for x in range(0, pw, 3)]; m = sum(v)/len(v); return sum((a-m)**2 for a in v)/len(v) < 400
    def flat_col(x):
        v = [sum(pp[x, y]) for y in range(0, ph, 3)]; m = sum(v)/len(v); return sum((a-m)**2 for a in v)/len(v) < 400
    t = 0
    while t < ph // 4 and flat_row(t): t += 1
    b = ph - 1
    while b > ph * 3 // 4 and flat_row(b): b -= 1
    le = 0
    while le < pw // 4 and flat_col(le): le += 1
    ri = pw - 1
    while ri > pw * 3 // 4 and flat_col(ri): ri -= 1
    # 枠の内側の細い線も落とすため、少しだけ余分に削る
    return part.crop((le + 3, t + 3, ri - 2, b - 2))

for tag, box in (("a", (0, 0, l, h)), ("b", (r + 1, 0, w, h))):
    p = trim(im.crop(box))
    if p.height > 1100:
        p = p.resize((int(p.width * 1100 / p.height), 1100), Image.LANCZOS)
    out = os.path.join(A, f"{name}_{ {"a":"clear","b":"fail"}[tag] }.jpg")
    p.save(out, quality=86)
    print(out, p.size)
