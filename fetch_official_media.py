#!/usr/bin/env python3
"""第二步：從官方站取得 1901–7958 各頁用到的圖片／Flash／影片路徑，寫成 manifest_old.json。

官方每頁的內容在一個小 JS 檔裡（assets/NNNNNNHS-xxxx.js），裡面有素材相對路徑（例如 panels/act-1/00001.gif）。
在你自己的電腦、專案資料夾執行（只用標準函式庫）：
    python fetch_official_media.py              # 全部（約 5500 個小檔，已抓過的存在 official_cache/，可續跑）
    python fetch_official_media.py 1901 2000    # 只抓頁碼範圍

輸出：manifest_old.json  { "1901": ["panels/act-1/00001.gif"], ... }
速度：每檔間隔 0.15 秒。
"""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://www.homestuck.com"
UA = "Mozilla/5.0 (homestuck-zh-fan-project; non-commercial)"
ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "official_cache"
MEDIA = re.compile(r'"([^"\s]+\.(?:gif|jpg|jpeg|png|swf|mp4|webm|mp3|ogg|m4a))"', re.I)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="ignore")


def main():
    lo, hi = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) >= 3 else (1901, 7958)
    CACHE.mkdir(exist_ok=True)
    home = get(BASE + "/")
    index = re.search(r"assets/index-[\w-]+\.js", home).group(0)
    ij = get(f"{BASE}/{index}")
    sv = re.search(r"StandardPageView-[\w-]+\.js", ij).group(0)
    svt = get(f"{BASE}/assets/{sv}")
    chunks = {}
    for m in re.finditer(r"assets/(\d{6})(\w*)-([\w-]+)\.js", svt):
        p = int(m.group(1))
        if lo <= p <= hi:
            chunks.setdefault(p, [])
            if m.group(0) not in chunks[p]:
                chunks[p].append(m.group(0))
    print(f"官方頁面檔 {len(chunks)} 頁")
    out_path = ROOT / "manifest_old.json"
    out = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    n = 0
    for p in sorted(chunks):
        if str(p) in out:
            continue
        items = []
        for f in chunks[p]:
            c = CACHE / f.split("/")[-1]
            try:
                if c.exists():
                    t = c.read_text(encoding="utf-8")
                else:
                    t = get(f"{BASE}/{f}")
                    c.write_text(t, encoding="utf-8")
                    time.sleep(0.15)
            except Exception as e:
                print(f"{p}: 失敗 {e}")
                continue
            for m in MEDIA.finditer(t):
                if m.group(1) not in items:
                    items.append(m.group(1))
        out[str(p)] = items
        n += 1
        if n % 200 == 0:
            out_path.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
            print(f"已處理 {n} 頁（目前 {p}）")
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"完成：manifest_old.json 共 {len(out)} 頁")


if __name__ == "__main__":
    main()
