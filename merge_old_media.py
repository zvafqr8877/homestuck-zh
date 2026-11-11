#!/usr/bin/env python3
"""把 manifest_old.json（fetch_official_media.py 產生，官方 1901–7958 的素材路徑）併進 manifest.json。

用法：python merge_old_media.py
規則：
  - panels/…（gif/png/jpg）→ {"type":"image","file":"images/panels/…"}
  - act-…/NNNNN.swf        → {"type":"flash","file":"flashes/act-…/NNNNN.swf"}
  - 檔名帶 retcon 的，同頁有一般版本時只留一般版本
  - 內文用的小圖（emojis/、inline-text/、scraps/、外部連結）不進 manifest，列在 old_inline_report.txt
  - manifest.json 裡已經有的頁（7959 以後）不動
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
old = json.loads((ROOT / "manifest_old.json").read_text(encoding="utf-8"))
man = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
added = 0
skipped = []
for k in sorted(old, key=int):
    if k in man:
        continue
    items, seen = [], []
    for x in old[k]:
        if x.startswith("panels/") and re.search(r"\.(gif|png|jpg|jpeg)$", x, re.I):
            seen.append(("image", "images/" + x))
        elif x.lower().endswith(".swf") and x.startswith("act-"):
            seen.append(("flash", "flashes/" + x))
        else:
            skipped.append(f"{k}\t{x}")
    has_normal = {t for t, f in seen if "retcon" not in f.lower()}
    for t, f in seen:
        if "retcon" in f.lower() and t in has_normal:
            continue
        items.append({"type": t, "file": f})
    if items:
        man[k] = items
        added += 1
(ROOT / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
(ROOT / "old_inline_report.txt").write_text("\n".join(skipped), encoding="utf-8")
print(f"新增 {added} 頁素材；未收進 manifest 的內文小圖／其他 {len(skipped)} 筆，見 old_inline_report.txt")
