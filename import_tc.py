#!/usr/bin/env python3
"""把繁中站（zhhomestuck.github.io）的 Blogger 備份 feed.atom 轉成本站的 content/NNNNNN.md。

用法：
    python import_tc.py feed.atom [輸出資料夾，預設 content] [--min 1901] [--max 7964]

- 只處理已發佈的數字頁（001901 … 007964）；檔名帶 tc 的特殊頁、獨立頁面另外列在 tc_special_report.txt，不轉。
- 內文轉成純文字（<br> 換行，其餘標籤去掉），對話的顏色由 build.py 依 speaker_colors.json 套用。
- status 寫 done（真人翻譯，不需要再校對），所以 convert.py 不會覆蓋。
- 已存在、而且 status 是 proofreading/done 的檔案預設不覆蓋；加 --force 才覆蓋（7959–7964 要用繁中站的版本時用）。
"""
import html
import re
import sys
from pathlib import Path


def text_of(c):
    c = html.unescape(c)
    c = re.sub(r"<!--.*?-->", "", c, flags=re.S)
    c = re.sub(r"<(script|style)\b.*?</\1>", "", c, flags=re.S | re.I)
    c = re.sub(r"<img\b[^>]*>", "", c, flags=re.I)
    c = re.sub(r"<br\s*/?>", "\n", c, flags=re.I)
    c = re.sub(r"</(div|p|tr|li)>", "\n", c, flags=re.I)
    c = re.sub(r"<[^>]+>", "", c)
    c = html.unescape(c).replace("\xa0", " ").replace("\r", "")
    lines = [l.strip() for l in c.split("\n")]
    out, blank = [], False
    for l in lines:
        if not l:
            blank = True
            continue
        out.append(l)
    return "\n".join(out)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    lo, hi = 1901, 7964
    argv = sys.argv
    if "--min" in argv:
        lo = int(argv[argv.index("--min") + 1])
        args = [a for a in args if a != str(lo)]
    if "--max" in argv:
        hi = int(argv[argv.index("--max") + 1])
        args = [a for a in args if a != str(hi)]
    if not args:
        raise SystemExit(__doc__)
    feed = Path(args[0])
    out = Path(args[1]) if len(args) > 1 else Path(__file__).resolve().parent / "content"
    out.mkdir(parents=True, exist_ok=True)
    t = feed.read_text(encoding="utf-8")
    written = skipped = 0
    special = []
    for e in re.findall(r"<entry>.*?</entry>", t, re.S):
        ty = re.search(r"<blogger:type>(\w+)", e).group(1)
        st = re.search(r"<blogger:status>(\w+)", e).group(1)
        fm = re.search(r"<blogger:filename>([^<]*)</blogger:filename>", e)
        fn = fm.group(1) if fm else ""
        m = re.search(r"/(\d{6})(\w*)\.html$", fn)
        tm = re.search(r"<title>(.*?)</title>", e, re.S)
        title = html.unescape(tm.group(1)).strip() if tm else ""
        if ty != "POST" or st != "LIVE" or not m or m.group(2):
            special.append(f"{ty}/{st} {fn or '(無檔名)'} {title}")
            continue
        n = int(m.group(1))
        if not (lo <= n <= hi):
            continue
        if n in (4299, 4938, 4988):  # 官方沒有的頁碼（跳號），繁中站放了空白佔位頁，不轉
            continue
        cm = re.search(r"<content type='html'>(.*?)</content>", e, re.S)
        raw = cm.group(1) if cm else ""
        body = text_of(raw)
        dest = out / f"{n:06d}.md"
        if dest.exists() and not force:
            old = dest.read_text(encoding="utf-8")
            sm = re.search(r"^status:\s*(\w+)", old, re.M)
            if sm and sm.group(1) in ("proofreading", "done"):
                skipped += 1
                continue
        title = title.replace("\n", " ").replace("---", "—")
        dest.write_text(f"---\npage: {n}\ntitle: {title}\nstatus: done\nsource: tc\n---\n{body}\n", encoding="utf-8")
        written += 1
    (out.parent / "tc_special_report.txt").write_text("\n".join(special), encoding="utf-8")
    print(f"寫出 {written} 頁，略過 {skipped} 頁；特殊／獨立頁 {len(special)} 筆見 tc_special_report.txt")


if __name__ == "__main__":
    main()
