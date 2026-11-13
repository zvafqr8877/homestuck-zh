#!/usr/bin/env python3
"""下載繁中站 11 個「Flash 文字版」特殊頁（002153TC、003258TC…），整理成 tc_special.json。

這些頁是繁中站替互動頁／Flash 遊戲做的文字版（指令與回應、點選說明、對話）。
build.py 看到 tc_special.json，會把內容放在對應頁面最下方（下一頁連結上方），
預設收合，標題「繁中站的文字版」，點開才看得到。

在你自己的電腦、專案資料夾執行（只用標準函式庫）：
    python fetch_tc_special.py
"""
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = "https://zhhomestuck.github.io/p/{:06d}tc.html"
PAGES = [2153, 3258, 4692, 4979, 5221, 5338, 5595, 5660, 6720, 6725, 7327]
UA = "Mozilla/5.0 (homestuck-zh-fan-project; non-commercial)"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="ignore")


def pagebody(h):
    """取出 <div class="pagebody"> 的內容（用 div 深度配對找結尾）"""
    m = re.search(r'<div class="pagebody"[^>]*>', h)
    if not m:
        return ""
    depth, pos = 1, m.end()
    for t in re.finditer(r"<(/?)div\b[^>]*>", h[pos:], re.I):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return h[pos:pos + t.start()]
    return h[pos:]


# 2153 那種「標題＋顯示／縮回按鈕」的區塊，改成 <details>
TOGGLE = re.compile(
    r'<b><span[^>]*underline[^>]*>(.*?)</span></b>\s*<div[^>]*>\s*<div[^>]*>\s*<button.*?</button>\s*</div>\s*'
    r'<div class="spoiler"[^>]*>\s*<div[^>]*>\s*<button.*?</button>\s*</div>\s*<div[^>]*>(.*?)</div></div></div>',
    re.S | re.I,
)


def sanitize(b):
    b = re.sub(r"<script\b.*?</script>", "", b, flags=re.S | re.I)
    b = TOGGLE.sub(lambda m: f"<details class=\"tcs-d\"><summary>{re.sub(r'<[^>]+>', '', m.group(1)).strip()}</summary><div class=\"tcs-b\">{m.group(2).strip()}</div></details>", b)
    b = re.sub(r"<button\b.*?</button>", "", b, flags=re.S | re.I)
    b = re.sub(r"\son\w+=\"[^\"]*\"", "", b, flags=re.I)
    b = re.sub(r"\son\w+='[^']*'", "", b, flags=re.I)
    b = re.sub(r"javascript:", "", b, flags=re.I)
    b = re.sub(r"<(iframe|object|embed|form|input)\b.*?(</\1>|/>|>)", "", b, flags=re.S | re.I)
    b = re.sub(r"\n{3,}", "\n\n", b)
    return b.strip()


def main():
    out = {}
    for n in PAGES:
        try:
            b = pagebody(get(BASE.format(n)))
        except Exception as e:  # noqa: BLE001
            print(f"{n}: 失敗 {e}")
            continue
        credit = ""
        c = re.search(r"文本由.*?翻譯", re.sub(r"<[^>]+>", "", b), re.S)
        if c:
            credit = c.group(0).strip()
            b = re.sub(r"文本由.*?翻譯", "", b, count=1, flags=re.S)
        html = sanitize(b)
        print(f"{n}: {len(html)} 字元，區塊 {html.count('<details')}")
        if html:
            out[str(n)] = {"credit": credit, "html": html}
    (ROOT / "tc_special.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"完成 → tc_special.json（{len(out)} 頁）")


if __name__ == "__main__":
    main()
