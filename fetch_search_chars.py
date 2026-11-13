#!/usr/bin/env python3
"""從官方站取得搜尋用的「角色資料」：每一頁有哪些角色說話，以及角色別名（egbert／eb → john、gt → john+jake…）。

官方搜尋索引 hs_index.json（約 8 MB，每一行台詞都標了說話者）在你自己的電腦、專案資料夾執行（只用標準函式庫）：
    python fetch_search_chars.py
輸出：search_chars.json  {"aliases": {...}, "names": ["john", ...], "pages": {"1917": [0, 3], ...}}
build.py 看到這個檔，搜尋頁進階欄的 chars:john,gt 就會用官方資料（以「這一頁有沒有該角色說話」判斷）。
"""
import json
import urllib.request
from pathlib import Path

BASE = "https://www.homestuck.com"
UA = "Mozilla/5.0 (homestuck-zh-fan-project; non-commercial)"
ROOT = Path(__file__).resolve().parent
SKIP = {"title", "narration", "unknown", "autoresponder", "space"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8", errors="ignore")


def main():
    aliases = json.loads(get(f"{BASE}/assets/hs_char_aliases.json"))
    out = {"aliases": aliases}
    (ROOT / "search_chars.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"別名 {len(aliases)} 筆 → search_chars.json")


if __name__ == "__main__":
    main()
