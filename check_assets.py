#!/usr/bin/env python3
"""檢查 manifest.json 與 content/ 是否對得上。

用法：
    python check_assets.py                 # 列出缺素材的頁、孤兒條目
    python check_assets.py --local assets  # 另外檢查本機資料夾裡檔案是否存在

manifest.json 格式：
{
  "6023": [
    {"type": "image", "file": "hs2/06023.gif", "alt": "說明文字"},
    {"type": "video", "file": "video/06023.mp4"}
  ]
}
實際網址 = site.json 的 asset_base + file。之後搬家只要改 asset_base。
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def page_numbers():
    nums = set()
    for p in (ROOT / "content").glob("*.md"):
        m = re.search(r"^page:\s*(\d+)", p.read_text(encoding="utf-8"), re.M)
        if m:
            nums.add(int(m.group(1)))
    return nums


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", help="本機素材資料夾（對應 asset_base）")
    args = ap.parse_args()

    mf_path = ROOT / "manifest.json"
    manifest = json.loads(mf_path.read_text(encoding="utf-8")) if mf_path.exists() else {}
    pages = page_numbers()
    keys = {int(k) for k in manifest}

    missing = sorted(pages - keys)
    orphans = sorted(keys - pages)
    print(f"頁面 {len(pages)} 頁；manifest 涵蓋 {len(keys & pages)} 頁")
    if missing:
        print(f"沒有素材紀錄的頁面（{len(missing)}）：{missing[:30]}{' …' if len(missing) > 30 else ''}")
    if orphans:
        print(f"manifest 有、但 content 沒有的頁碼（{len(orphans)}）：{orphans[:30]}")

    bad = 0
    if args.local:
        base = Path(args.local)
        for k, items in manifest.items():
            for it in items:
                if "file" not in it:  # 例如 youtube 類型沒有本機檔案
                    continue
                if not (base / it["file"]).exists():
                    bad += 1
                    print(f"檔案不存在：{k} → {it['file']}")
        print(f"本機缺檔 {bad} 個")


if __name__ == "__main__":
    main()
