# -*- coding: utf-8 -*-
"""Geminiの進化シート（2×2・黒背景）を4体に切り分けて透過PNGにする。
   使い方: python cut_evo.py evo_slime_sheet.png slime
   出力: evo_slime_2.png 〜 evo_slime_5.png（左上＝第2段階、右上＝3、左下＝4、右下＝5）"""
import sys, os
from collections import deque
from PIL import Image

A = os.path.join("C:\\", "Users", "nekoz", "OneDrive", "デスクトップ", "AI", "ぽよんダンジョン", "assets")
src, line = sys.argv[1], sys.argv[2]
# 3つ目の引数: "2x2"（既定）か "1x2"。4つ目: 出力する段階の番号（カンマ区切り）
layout = sys.argv[3] if len(sys.argv) > 3 else "2x2"
stages = [int(v) for v in sys.argv[4].split(",")] if len(sys.argv) > 4 else [2, 3, 4, 5]
im = Image.open(os.path.join(A, src)).convert("RGBA")
w, h = im.size
px = im.load()
TH = 34   # これより暗いものは背景の黒とみなす（外周からつながっている所だけ）
# 背景が白で来ることもある。四隅の色で判断する
WHITE = sum(sum(px[x, y][:3]) for x, y in ((2,2),(w-3,2),(2,h-3),(w-3,h-3))) / 12 > 200

def dark(x, y):
    r, g, b, _ = px[x, y]
    if WHITE: return min(r, g, b) > 236
    return max(r, g, b) < TH

# 外周からつながった黒だけを抜く（こげ茶の輪郭や黒目は残る）
bg = [[False] * w for _ in range(h)]
q = deque()
for x in range(w):
    for y in (0, h - 1):
        if dark(x, y) and not bg[y][x]: bg[y][x] = True; q.append((x, y))
for y in range(h):
    for x in (0, w - 1):
        if dark(x, y) and not bg[y][x]: bg[y][x] = True; q.append((x, y))
while q:
    x, y = q.popleft()
    for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
        if 0 <= nx < w and 0 <= ny < h and not bg[ny][nx] and dark(nx, ny):
            bg[ny][nx] = True; q.append((nx, ny))

# 境目のにじみ：背景に接する暗めの画素は半透明にして、黒いふちを残さない
out = Image.new("RGBA", (w, h))
op = out.load()
for y in range(h):
    for x in range(w):
        if bg[y][x]:
            op[x, y] = (0, 0, 0, 0); continue
        r, g, b, _ = px[x, y]
        edge = any(0 <= x+dx < w and 0 <= y+dy < h and bg[y+dy][x+dx] for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)))
        a = 255
        if edge and WHITE:
            m = 255 - min(r, g, b)
            a = max(0, min(255, int((m - 19) / 60 * 255))) if m < 79 else 255
        elif edge:
            m = max(r, g, b)
            a = max(0, min(255, int((m - TH) / 50 * 255))) if m < TH + 50 else 255
        op[x, y] = (r, g, b, a)

# 縦・横の切れ目を、中央付近でいちばん何もない線にする
def col_fill(x): return sum(1 for y in range(h) if not bg[y][x])
def row_fill(y): return sum(1 for x in range(w) if not bg[y][x])
cx = min(range(int(w*.40), int(w*.60)), key=col_fill)
if layout == "1x1":
    boxes = [(0, 0, w, h)]
elif layout == "1x2":
    boxes = [(0, 0, cx, h), (cx, 0, w, h)]
    print("切れ目", cx, "残り", col_fill(cx))
else:
    cy = min(range(int(h*.40), int(h*.60)), key=row_fill)
    print("切れ目", cx, cy, "残り", col_fill(cx), row_fill(cy))
    boxes = [(0, 0, cx, cy), (cx, 0, w, cy), (0, cy, cx, h), (cx, cy, w, h)]
for i, (x0, y0, x1, y1) in enumerate(boxes):
    if i >= len(stages) or stages[i] <= 0: continue
    part = out.crop((x0, y0, x1, y1))
    # 足元の影など、本体から離れた小さいかたまりは消す（いちばん大きい かたまりの 3% 未満）
    pp = part.load(); pw, ph = part.size
    seen = [[False]*pw for _ in range(ph)]; comps = []
    for yy in range(ph):
        for xx in range(pw):
            if seen[yy][xx] or pp[xx, yy][3] == 0: continue
            st = [(xx, yy)]; seen[yy][xx] = True; pts = []
            while st:
                a, b2 = st.pop(); pts.append((a, b2))
                for na, nb in ((a+1,b2),(a-1,b2),(a,b2+1),(a,b2-1)):
                    if 0 <= na < pw and 0 <= nb < ph and not seen[nb][na] and pp[na, nb][3] > 0:
                        seen[nb][na] = True; st.append((na, nb))
            comps.append(pts)
    if comps:
        big = max(len(c) for c in comps)
        for c in comps:
            if len(c) < big * 0.03:
                for a, b2 in c: pp[a, b2] = (0, 0, 0, 0)
    bb = part.getbbox()
    part = part.crop(bb)
    pad = 6
    canvas = Image.new("RGBA", (part.width + pad*2, part.height + pad*2))
    canvas.paste(part, (pad, pad))
    name = f"evo_{line}_{stages[i]}.png"
    canvas.save(os.path.join(A, name))
    print(name, canvas.size)
