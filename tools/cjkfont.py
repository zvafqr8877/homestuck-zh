# -*- coding: utf-8 -*-
"""把字型輪廓轉成 SWF 的 DefineFont3 tag。glyph 資料可快取（glyph_cache.json），
這樣在沒有字型檔的電腦上也能重新產生（只要字都在快取裡）。"""
import base64, json, os, struct
try:                       # 只有「補字」才需要 fontTools；用快取產生字型時不需要安裝
    from fontTools.pens.basePen import BasePen
    from fontTools.cu2qu.cu2qu import curve_to_quadratic
except ImportError:
    BasePen = object
    curve_to_quadratic = None

EM = 20480  # DefineFont3 的座標系


class _BW:
    def __init__(self): self.bits = []
    def u(self, v, n):
        for i in range(n - 1, -1, -1): self.bits.append((v >> i) & 1)
    def s(self, v, n):
        self.u(v & ((1 << n) - 1), n)
    def bytes(self):
        b = self.bits + [0] * (-len(self.bits) % 8)
        return bytes(int("".join(map(str, b[i:i + 8])), 2) for i in range(0, len(b), 8))


def _nb(*vals):
    m = max(abs(v) for v in vals)
    n = 1
    while (1 << (n - 1)) <= m: n += 1   # signed
    return max(n, 2)


class _P(BasePen):
    def __init__(self, gs):
        super().__init__(gs); self.cont = []; self.cur = None
    def _moveTo(self, p): self.cur = [("M", p)]
    def _lineTo(self, p): self.cur.append(("L", p))
    def _curveToOne(self, a, b, c):
        p0 = self._getCurrentPoint()
        pts = curve_to_quadratic([p0, a, b, c], 1.0)
        # pts: p0, q1, p1, q2, p2 ...
        for i in range(1, len(pts) - 1, 2):
            self.cur.append(("Q", pts[i], pts[i + 1]))
    def _qCurveToOne(self, a, b): self.cur.append(("Q", a, b))
    def _closePath(self):
        self.cont.append(self.cur); self.cur = None
    def _endPath(self): self._closePath()


def glyph_shape(font, ch):
    S = EM / font['head'].unitsPerEm
    """回傳 (shape bytes, advance) ；字型沒有這個字回傳 None"""
    cmap = font.getBestCmap()
    if ord(ch) not in cmap: return None
    gn = cmap[ord(ch)]
    gs = font.getGlyphSet()
    pen = _P(gs); gs[gn].draw(pen)
    adv = int(round(gs[gn].width * S))
    w = _BW(); w.u(1, 4); w.u(0, 4)
    cx = cy = 0
    for c in pen.cont:
        if not c or c[0][0] != "M": continue
        sx, sy = c[0][1]; sx = round(sx * S); sy = -round(sy * S)
        w.u(0, 1); w.u(0b00101, 5)           # StyleChange: FillStyle1 + MoveTo
        n = _nb(sx, sy); w.u(n, 5); w.s(sx, n); w.s(sy, n); w.u(1, 1)
        cx, cy = sx, sy
        for seg in c[1:]:
            if seg[0] == "L":
                x, y = round(seg[1][0] * S), -round(seg[1][1] * S)
                dx, dy = x - cx, y - cy
                if dx == 0 and dy == 0: continue
                n = _nb(dx, dy)
                w.u(1, 1); w.u(1, 1); w.u(n - 2, 4); w.u(1, 1); w.s(dx, n); w.s(dy, n)
                cx, cy = x, y
            else:
                ax, ay = round(seg[1][0] * S), -round(seg[1][1] * S)
                bx, by = round(seg[2][0] * S), -round(seg[2][1] * S)
                d = (ax - cx, ay - cy, bx - ax, by - ay)
                n = _nb(*d)
                w.u(1, 1); w.u(0, 1); w.u(n - 2, 4)
                for v in d: w.s(v, n)
                cx, cy = bx, by
        if (cx, cy) != (sx, sy):
            dx, dy = sx - cx, sy - cy; n = _nb(dx, dy)
            w.u(1, 1); w.u(1, 1); w.u(n - 2, 4); w.u(1, 1); w.s(dx, n); w.s(dy, n)
            cx, cy = sx, sy
    w.u(0, 1); w.u(0, 5)  # end
    return w.bytes(), adv


class GlyphSource:
    def __init__(self, cache_path, font_path=None, ttc_index=3):
        self.cache_path = cache_path
        self.cache = json.load(open(cache_path, encoding="utf-8")) if os.path.exists(cache_path) else {}
        self.font = None
        meta = self.cache.pop("_meta", None)
        if font_path:
            from fontTools.ttLib import TTFont, TTCollection
            self.font = TTCollection(font_path).fonts[ttc_index] if font_path.lower().endswith(".ttc") else TTFont(font_path)
        self.asc = 0.88; self.desc = 0.12  # 佔字高比例（有字型檔時會用字型自己的值）
        if self.font is not None:
            hh = self.font['hhea']; u = self.font['head'].unitsPerEm
            self.asc, self.desc = hh.ascent / u, -hh.descent / u
        elif meta:
            self.asc, self.desc = meta

    def get(self, ch):
        if ch in self.cache:
            e = self.cache[ch]; return base64.b64decode(e[0]), e[1]
        if self.font is None: return None
        r = glyph_shape(self.font, ch)
        if r: self.cache[ch] = [base64.b64encode(r[0]).decode(), r[1]]
        return r

    def save(self):
        self.cache["_meta"] = [self.asc, self.desc]
        json.dump(self.cache, open(self.cache_path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        self.cache.pop("_meta", None)


def define_font3(font_id, name, chars, src):
    """chars: 要放進字型的字元（str）。缺字會丟 KeyError 並列出。"""
    chars = sorted(set(chars))
    shapes, advs, missing = [], [], []
    for ch in chars:
        r = src.get(ch)
        if r is None: missing.append(ch); continue
        shapes.append((ch, r[0])); advs.append(r[1])
    if missing:
        raise KeyError("字型缺這些字（快取裡沒有、也沒給字型檔）：" + "".join(missing))
    n = len(shapes)
    body = struct.pack("<H", font_id)
    # flags: HasLayout | WideOffsets | WideCodes
    body += bytes([0x80 | 0x08 | 0x04, 0x03])      # language 3 = 繁中
    nm = name.encode(); body += bytes([len(nm)]) + nm
    body += struct.pack("<H", n)
    offs_size = 4 * n + 4
    pos = offs_size; offs = []
    for _, sh in shapes:
        offs.append(pos); pos += len(sh)
    body += b"".join(struct.pack("<I", o) for o in offs) + struct.pack("<I", pos)
    body += b"".join(sh for _, sh in shapes)
    body += b"".join(struct.pack("<H", ord(ch)) for ch, _ in shapes)
    asc, desc = int(src.asc * EM), int(src.desc * EM)
    body += struct.pack("<hhh", asc, desc, 0)
    body += b"".join(struct.pack("<h", min(a, 32767)) for a in advs)
    body += b"".join(bytes([0x00]) + b"\0" * 0 + b"" for _ in range(0))   # placeholder (no-op)
    for _ in range(n):                    # 每個字的邊界框：Nbits=0 的最小 RECT
        body += bytes([0x00])
    body += struct.pack("<H", 0)          # kerning 數量
    return body, dict(zip([c for c, _ in shapes], advs))
