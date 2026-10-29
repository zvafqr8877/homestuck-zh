#!/usr/bin/env python3
"""由 UHC 素材包的 mspa.json 產生官方新網址的素材對照表（manifest.json 格式）。

用法：
    python gen_manifest.py <mspa.json> [輸出檔，預設 manifest_gap.json] [起始官方頁碼] [結束官方頁碼]

只讀取每頁的 media（素材路徑）欄位，不會輸出或保存任何劇情文字。

規則與驗證（2026-10-29 用官方站 storage.homestuck.com 逐檔 HEAD 檢查，全部 200）：
  - 檔名沿用 UHC 的名稱；.swf 放 flashes/，圖片放 images/panels/
  - 資料夾：檔案編號 < 6240 用 act-6-int-5，>= 6240 用 act-6-act-6
    （官方頁 8143 起換成 act-6-act-6）
  - 「重製頁」8004–8007 引用的舊素材，資料夾用實測值（RETCON 表）
  - 官方把 08082heal.png 這類檔名改成純編號（08082.png）
  - 8801（GAMEOVER）的 Flash 官方用 06898-modified.swf
  - 9987、10027、10030 官方是 YouTube 內嵌，UHC 裡是 mp4
範圍外或其他頁碼沒有驗證過，用之前請再抽查。
"""
import json, re, sys

SRC = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "manifest_gap.json"
FIRST = int(sys.argv[3]) if len(sys.argv) > 3 else 7959
LAST = int(sys.argv[4]) if len(sys.argv) > 4 else 10030

story = json.load(open(SRC, encoding="utf-8"))["story"]
meta = {int(k): {"media": e.get("media", [])} for k, e in story.items() if k.isdigit()}

# 8004–8007（重製頁）引用的舊素材，所在資料夾是實測值
RETCON = {}
for folder, names in {
  "act-1": "00204 00234",
  "act-2": "00331 00508 00638 00740_1",
  "act-3": "00825 00922 00994_1 01069 01087 01134_1",
  "int-1": "01198 01271 01308",
  "act-4": "01361_1 01455 01585_1 01778 01882_5 01931",
  "act-5-act-1": "02048_2 02176 02281 02434 02601",
  "act-5-act-2": "02728 03021 03124 03294 03476 03686 03781 03881_1 03973_2 04007 04067 04090",
  "act-6-act-1": "04151 04255",
  "act-6-int-1": "04409",
  "act-6-act-2": "04600",
  "act-6-int-2": "04723",
  "act-6-act-3": "04828 04955 05084_2 05219",
  "act-6-int-3": "05351",
  "act-6-int-4": "05451",
  "act-6-act-5": "05612",
  "act-6-int-5": "05947",
}.items():
    for n in names.split():
        RETCON[n + "retcon.gif"] = folder

RETCON.update({
  "00248retcon.gif": "act-2", "01395retcon.gif": "act-4", "02267retcon.gif": "act-5-act-1",
  "05247retcon.gif": "act-6-act-3", "04054retcon.gif": "act-5-act-2", "04863retcon.gif": "act-6-act-3",
  "05277retconheir.gif": "act-6-int-3",
})
YT = {9987: "Y5wYN6rB_Rg", 10027: "FevMNMwvdPw", 10030: "rMZU89jY2j8"}   # 官方實測
SPECIAL_FILE = {8801: "06898-modified.swf"}                              # 官方實測

def folder_for(base, path=""):
    if base in RETCON: return RETCON[base]
    m = re.match(r"\d+", base) or re.search(r"/(\d{5})/[^/]+$", path)   # A6A6I1.swf 這類檔名用上層資料夾的編號
    n = int(m.group(1) if m.lastindex else m.group())
    return "act-6-int-5" if n < 6240 else "act-6-act-6"

manifest, verify, notes = {}, [], []
for p in range(FIRST, LAST + 1):
    if p not in meta: continue
    if p in YT:
        manifest[str(p)] = [{"type": "youtube", "id": YT[p]}]; continue
    items = []
    for path in meta[p]["media"]:
        base = path.rsplit("/", 1)[-1]
        ext = base.rsplit(".", 1)[-1].lower()
        if p in SPECIAL_FILE and ext == "swf": base = SPECIAL_FILE[p]
        if ext == "png" and re.fullmatch(r"\d{5}[a-z]+\.png", base): base = base[:5] + ".png"   # 官方實測：08093mspaint.png → 08093.png
        fol = folder_for(base, path)
        if ext in ("gif", "png", "jpg"):
            f = f"images/panels/{fol}/{base}"; t = "image"
        elif ext == "swf":
            f = f"flashes/{fol}/{base}"; t = "flash"
        else:
            notes.append((p, path)); continue
        items.append({"type": t, "file": f})
        verify.append([p, f])
    manifest[str(p)] = items
json.dump(manifest, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"寫入 {len(manifest)} 頁、{len(verify)} 個素材 → {OUT}；未處理：{notes}")
