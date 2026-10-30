#!/usr/bin/env python3
"""從簡中站抓取文字，存成 src_sc/NNNN.txt（NNNN 是簡中頁碼）。

簡中站的頁面結構（2026-10-30 實測）：
- 標題：#content_container 裡第一個 <h2>
- 對話記錄：<p class="o_chat-log">，每行用 <br> 分隔（網頁上預設收起，要按「Show Dialoglog」）
- 少數頁面（例如 Credits）有 <p class="o-story_text"> 的內文
- 圖片裡的英文沒有翻譯，簡中站也沒有處理，所以抓得到的文字就只有這些

更好的做法（不用打擾對方伺服器）：
    git clone https://github.com/linzhiyi622/homestuckjz.GitHub.io
    python fetch_sc.py --from-dir homestuckjz.GitHub.io      # 直接解析 repo 裡的 NNNN.html

或從網站抓（在你自己的電腦上，需要 Python 3，不用安裝其他套件）：
    python fetch_sc.py                 # 抓 6059–8130，已抓過的會略過，可隨時中斷再續跑
    python fetch_sc.py 6059 6100       # 只抓指定範圍
    python fetch_sc.py --refresh       # 已存在的也重抓

對對方站點的禮貌：每次請求之間等待 1 秒，失敗會退讓重試，不會同時發多個請求。
全部約 2070 頁，大約 40 分鐘。
"""
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://linzhiyi622.github.io/homestuckjz.GitHub.io/{n}.html"
FIRST, LAST = 6059, 8130
DELAY = 1.0
OUT = Path(__file__).resolve().parent / "src_sc"
UA = "Mozilla/5.0 (homestuck-zh-fan-project; non-commercial; contact via GitHub)"


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self._in_h2 = False
        self._h2_buf = []
        self._cap = None  # 目前正在收集的區塊："chat" 或 "text"
        self._cap_depth = 0
        self._buf = []
        self.blocks = []  # [(kind, [lines])]
        self._skip = 0  # script/style

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").split()
        if tag in ("script", "style"):
            self._skip += 1
        if tag == "h2" and self.title is None:
            self._in_h2 = True
            self._h2_buf = []
        if self._cap:
            if tag == "br":
                self._buf.append("\n")
            elif tag == "p":
                self._cap_depth += 1
            return
        if tag == "p" and "o_chat-log" in cls:
            self._cap, self._cap_depth, self._buf = "chat", 1, []
        elif tag == "p" and "o-story_text" in cls:
            self._cap, self._cap_depth, self._buf = "text", 1, []

    def handle_startendtag(self, tag, attrs):
        if tag == "br" and self._cap:
            self._buf.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        if tag == "h2" and self._in_h2:
            self._in_h2 = False
            self.title = "".join(self._h2_buf).strip()
        if self._cap and tag == "p":
            self._cap_depth -= 1
            if self._cap_depth == 0:
                lines = [x.strip() for x in "".join(self._buf).split("\n")]
                lines = [x for x in lines if x]
                if lines:
                    self.blocks.append((self._cap, lines))
                self._cap = None

    def handle_data(self, data):
        if self._skip:
            return
        if self._in_h2:
            self._h2_buf.append(data)
        if self._cap:
            self._buf.append(data)


def parse(html):
    p = PageParser()
    p.feed(html)
    return p.title or "", p.blocks


def render(title, blocks):
    out = [f"# {title}"] if title else []
    for _, lines in blocks:
        out.extend(lines)
    return "\n".join(out) + "\n"


def fetch(n, tries=4):
    url = BASE.format(n=n)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            wait = 5 * (i + 1)
        except Exception:
            wait = 5 * (i + 1)
        print(f"  {n}：失敗，{wait} 秒後重試")
        time.sleep(wait)
    raise SystemExit(f"{n} 連續失敗，先停下來。稍後重跑會從這頁繼續。")


def from_dir(repo, first, last):
    """直接讀簡中站 repo（git clone 下來的 NNNN.html），不用打擾對方的伺服器。"""
    OUT.mkdir(exist_ok=True)
    missing, empty, got = [], 0, 0
    for n in range(first, last + 1):
        src = Path(repo) / f"{n}.html"
        if not src.exists():
            missing.append(n)
            continue
        title, blocks = parse(src.read_text(encoding="utf-8", errors="replace"))
        empty += not blocks
        (OUT / f"{n}.txt").write_text(render(title, blocks), encoding="utf-8")
        got += 1
    print(f"完成：{got} 頁（沒有任何中文區塊的 {empty} 頁），repo 裡沒有的 {len(missing)} 頁：{missing}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--from-dir" in sys.argv:
        i = sys.argv.index("--from-dir")
        repo = sys.argv[i + 1]
        args = [a for a in args if a != repo]
        first, last = (int(args[0]), int(args[1])) if len(args) == 2 else (FIRST, LAST)
        return from_dir(repo, first, last)
    refresh = "--refresh" in sys.argv
    first, last = (int(args[0]), int(args[1])) if len(args) == 2 else (FIRST, LAST)
    OUT.mkdir(exist_ok=True)
    missing, empty, got = [], 0, 0
    for n in range(first, last + 1):
        dest = OUT / f"{n}.txt"
        if dest.exists() and not refresh:
            continue
        html = fetch(n)
        time.sleep(DELAY)
        if html is None:
            missing.append(n)
            print(f"{n}：404（簡中站沒有這頁）")
            continue
        title, blocks = parse(html)
        if not blocks:
            empty += 1
        dest.write_text(render(title, blocks), encoding="utf-8")
        got += 1
        if got % 50 == 0:
            print(f"已抓 {got} 頁，目前到 {n}")
    print(f"完成：新抓 {got} 頁（其中沒有任何中文區塊的 {empty} 頁），404 共 {len(missing)} 頁：{missing}")


if __name__ == "__main__":
    main()
