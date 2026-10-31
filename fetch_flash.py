#!/usr/bin/env python3
"""把 manifest.json 裡所有 Flash（89 個 SWF）從官方儲存空間下載到 assets/，路徑和 manifest 的 file 一致。

在你自己的電腦、專案資料夾裡執行（只用標準函式庫）：
    python fetch_flash.py            # 下載全部，已存在的略過，可中斷續跑
    python fetch_flash.py 8105 8282  # 只下載指定頁碼

下載完後 python build.py，有檔案的頁面自動改成本站用 Ruffle 播放；沒檔案的頁面維持嵌入官方頁面。
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UA = "Mozilla/5.0 (homestuck-zh-fan-project; non-commercial)"


def main():
    site = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
    base = site["asset_base"]
    if not base.endswith("/"):
        base += "/"
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    only = {int(a) for a in sys.argv[1:] if a.isdigit()}
    todo = [(int(p), it["file"]) for p, items in manifest.items() for it in items
            if it.get("type") == "flash" and (not only or int(p) in only)]
    ok = skip = 0
    failed = []
    for page, f in sorted(todo):
        dest = ROOT / "assets" / f
        if dest.exists() and dest.stat().st_size > 0:
            skip += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            req = urllib.request.Request(base + f, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            if not data.startswith((b"CWS", b"FWS", b"ZWS")):
                raise ValueError("不是 SWF 檔")
            dest.write_bytes(data)
            ok += 1
            print(f"{page}: {f} ({len(data) // 1024} KB)")
        except Exception as e:
            failed.append(page)
            print(f"{page}: 失敗 {e}")
        time.sleep(0.5)
    print(f"完成：新下載 {ok}，略過 {skip}，失敗 {len(failed)} {failed if failed else ''}")


if __name__ == "__main__":
    main()
