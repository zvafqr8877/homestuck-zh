# -*- coding: utf-8 -*-
"""把 swf_zh/<頁碼>.json 裡的譯文寫進 Flash，輸出到 assets/zh/。

用法（在專案根目錄）：
    python tools/swf_zh.py            # 處理 swf_zh/ 底下所有 json
    python tools/swf_zh.py 9001 8300  # 只處理指定頁

原始 SWF 要先用 fetch_flash.py 下載到 assets/（assets/<manifest 路徑> 或 assets/flashes/<檔名>）。
字型：嵌入文泉驛正黑（WenQuanYi Zen Hei，GPLv2＋字型嵌入例外），只含用到的字；字形放在 swf_zh/glyph_cache.json。
如果譯文新增了快取裡沒有的字，工具會列出缺的字；請把缺字回報，或用 --font 指定
一個 .ttc/.ttf 字型檔（例如文泉驛正黑）讓它自己補。
"""
import argparse, json, struct, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from swflib import read_swf, write_swf, parse_edit, build_edit, parse_static
from cjkfont import GlyphSource, define_font3

ROOT = Path(__file__).resolve().parent.parent
FONT_ID = 60001
NO_CONVERT = False   # 只給測試用（--no-convert：不做簡轉繁，直接用 json 裡的文字）
NO_BREAK_BEFORE = set("，。、；：！？）」』”’…—,.;:!?)]}%")
NO_BREAK_AFTER = set("（「『“‘([{")


def make_tc():
    """簡中 -> 繁中：和 convert.py 完全同一套（OpenCC s2twp + glossary.csv）"""
    import convert
    cc = convert.make_converter()
    gl = convert.load_glossary(ROOT / "glossary.csv")
    def tc(t):
        t = cc.convert(t)
        for a, b in gl: t = t.replace(a, b)
        return t
    return tc


def rect_bytes(xmin, xmax, ymin, ymax):
    vals = [xmin, xmax, ymin, ymax]
    n = 1
    while any(not (-(1 << (n - 1)) <= v < (1 << (n - 1))) for v in vals): n += 1
    bits = f"{n:05b}" + "".join(format(v & ((1 << n) - 1), f"0{n}b") for v in vals)
    bits += "0" * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def find_src(rel):
    for p in (ROOT / "assets" / rel, ROOT / "assets" / "flashes" / Path(rel).name):
        if p.exists(): return p
    return None


def bounds_width(rect):
    n = rect[0] >> 3
    bits = "".join(f"{b:08b}" for b in rect)[5:5 + n * 4]
    def sv(s):
        v = int(s, 2); return v - (1 << n) if s[0] == "1" else v
    xmin, xmax = sv(bits[0:n]), sv(bits[n:2 * n])
    ymin, ymax = sv(bits[2 * n:3 * n]), sv(bits[3 * n:4 * n])
    return xmax - xmin, ymax - ymin


def wrap(text, advs, fh, width_tw):
    """自己先斷行（插入 \\r），避免 Ruffle 對中文斷行不穩。寬度留 6% 餘裕。"""
    limit = width_tw * 0.94
    def w(ch): return advs.get(ch, 20480 * 0.55) * fh / 20480.0
    out_lines = []
    for para in text.split("\r"):
        cur, cw = "", 0.0
        for ch in para:
            cwid = w(ch)
            if cw + cwid > limit and cur:
                if ch in NO_BREAK_BEFORE:
                    cur += ch; cw += cwid; continue
                if cur[-1] in NO_BREAK_AFTER and len(cur) > 1:
                    out_lines.append(cur[:-1]); cur, cw = cur[-1] + ch, w(cur[-1]) + cwid; continue
                out_lines.append(cur); cur, cw = ch, cwid
            else:
                cur += ch; cw += cwid
        out_lines.append(cur)
    return "\r".join(out_lines)


def patch(page, glyphs):
    cfg = json.load(open(ROOT / "swf_zh" / f"{page}.json", encoding="utf-8"))
    src = find_src(cfg["swf"])
    if not src:
        print(f"[{page}] 找不到原始 SWF（{cfg['swf']}），請先執行 fetch_flash.py"); return False
    ver, header, tags = read_swf(src)
    tc = make_tc() if not NO_CONVERT else (lambda t: t)
    texts = {int(k): tc(v) for k, v in cfg["sc"].items()}
    chars = set(chr(c) for c in range(32, 127)) | set("".join(texts.values()).replace("\r", ""))
    missing = sorted(c for c in chars if glyphs.get(c) is None)
    if missing:
        print(f"[{page}] ！！字型缺這些字，已先用 □ 代替：{''.join(missing)}  （請回報給 Claude，或加 --font 補字）")
        for k in texts:
            for c in missing: texts[k] = texts[k].replace(c, "□")
        chars = (chars - set(missing)) | {"□"}
    fbody, advs = define_font3(FONT_ID, "WenQuanYiZenHei", chars, glyphs)
    done = set(); first_edit = None
    for i, (code, data) in enumerate(tags):
        if code in (11, 33):
            sid = struct.unpack_from("<H", data, 0)[0]
            if sid not in texts: continue
            st = parse_static(data, code)
            fh = st["h"]
            line = texts[sid].replace("\r", " ")
            wtw = int(sum(advs.get(c, 20480 * 0.55) for c in line) * fh / 20480) + 120
            ymin = st["ty"] + st["yo"] - int(fh * glyphs.asc) - 40
            cx = (st["bd"][0] + st["bd"][1]) // 2          # 官方是整行置中：以原本英文文字的中心為中心
            r = dict(id=sid, bounds=rect_bytes(cx - wtw // 2, cx + wtw // 2, ymin, ymin + int(fh * 1.3) + 80),
                     f1=0x8D, f2=0x11, font=FONT_ID, fclass=None, fh=fh, color=st["color"] + b"\xff",
                     maxlen=None, layout=None, var="", text=line)
            tags[i] = [37, build_edit(r)]
            if first_edit is None: first_edit = i
            done.add(sid)
            continue
        if code != 37: continue
        if first_edit is None: first_edit = i
        r = parse_edit(data)
        if r["id"] not in texts: continue
        fh = r["fh"] or 280
        wtw, htw = bounds_width(r["bounds"])
        margins = 0
        if r["layout"]:
            lm, rm = struct.unpack_from("<HH", r["layout"], 1); margins = lm + rm
        txt = wrap(texts[r["id"]], advs, fh, wtw - margins - 80)
        lines = txt.count("\r") + 1
        if lines * fh * 1.25 > htw:
            print(f"  [{page}] 文字框 {r['id']} 可能放不下：{lines} 行 × {fh/20:.0f}px，框高 {htw/20:.0f}px")
        r.update(text=txt, font=FONT_ID, f1=r["f1"] | 0x81, f2=r["f2"] | 0x01)
        if r["f2"] & 0x80: r["f2"] &= ~0x80; r["fclass"] = None
        tags[i][1] = build_edit(r)
        done.add(r["id"])
    miss = set(texts) - done
    if miss: print(f"[{page}] 這些文字框 id 在動畫裡找不到：{sorted(miss)}")
    tags.insert(first_edit, [75, fbody])
    out = ROOT / "assets" / "zh" / cfg["swf"]
    out.parent.mkdir(parents=True, exist_ok=True)
    write_swf(out, ver, header, tags)
    print(f"[{page}] 完成：{len(done)} 個文字框 → {out.relative_to(ROOT)}（{out.stat().st_size//1024} KB）")
    return not miss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="*")
    ap.add_argument("--font", help="補字用的字型檔（.ttc/.ttf），沒有缺字就不需要")
    ap.add_argument("--ttc-index", type=int, default=0, help="TTC 裡的第幾個字型（文泉驛正黑是 0）")
    ap.add_argument("--no-convert", action="store_true", help="測試用：不做簡轉繁")
    a = ap.parse_args()
    global NO_CONVERT
    NO_CONVERT = a.no_convert
    g = GlyphSource(str(ROOT / "swf_zh" / "glyph_cache.json"), a.font, a.ttc_index)
    pages = a.pages or sorted(p.stem for p in (ROOT / "swf_zh").glob("*.json") if p.stem.isdigit())
    ok = all([patch(p, g) for p in pages])
    if a.font: g.save()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
