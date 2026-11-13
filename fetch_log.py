#!/usr/bin/env python3
"""從官方站取得「冒險紀錄」(viewlog) 的完整資料：每頁的日期與連結文字（英文原文，含引號）。

官方把整份紀錄寫死在一個 JS 檔（assets/HomestuckLog-xxxx.js）裡，這個腳本把它抓下來整理成 log_official.json。
在你自己的電腦、專案資料夾執行（只用標準函式庫）：
    python fetch_log.py
輸出：log_official.json  [[id, "MM/DD/YY", "\\"文字\\"", "/001901"], ...]（由舊到新）
build.py 看到這個檔就會用它產生紀錄頁（文字與官方完全一致）。
"""
import json
import re
import urllib.request
from pathlib import Path

BASE = "https://www.homestuck.com"
UA = "Mozilla/5.0 (homestuck-zh-fan-project; non-commercial)"
ROOT = Path(__file__).resolve().parent

ENTRY = re.compile(
    r"\{id:([^,]+),date:\"([^\"]+)\",value:(?:'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"|`((?:[^`\\]|\\.)*)`),linkTo:\"([^\"]+)\"\}"
)
ESC = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}


def unescape(s):
    def rep(m):
        g = m.group(1)
        if g[0] == "u":
            return chr(int(g[1:], 16))
        if g[0] == "x":
            return chr(int(g[1:], 16))
        return ESC.get(g, g)
    return re.sub(r"\\(u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|.)", rep, s)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="ignore")


def parse(text):
    out = []
    for m in ENTRY.finditer(text):
        v = m.group(3) if m.group(3) is not None else (m.group(4) if m.group(4) is not None else m.group(5))
        out.append([int(float(m.group(1))), m.group(2), unescape(v), m.group(6)])
    out.sort(key=lambda x: x[0])
    return out


def main():
    home = get(BASE + "/")
    index = re.search(r"assets/index-[\w-]+\.js", home).group(0)
    ij = get(f"{BASE}/{index}")
    name = re.search(r"HomestuckLog-[\w-]+\.js", ij).group(0)
    data = parse(get(f"{BASE}/assets/{name}"))
    (ROOT / "log_official.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"{name}：{len(data)} 筆（預期約 8124）→ log_official.json")


if __name__ == "__main__":
    main()
