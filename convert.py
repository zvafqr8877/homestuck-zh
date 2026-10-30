#!/usr/bin/env python3
"""簡體文字 → 繁體（台灣正體用語）→ 套用術語表 → 寫成 content/NNNNNN.md。

用法：
    pip install opencc-python-reimplemented
    python convert.py src_sc content

src_sc/ 裡放簡體純文字檔，檔名是「簡中站頁碼」，例如 6059.txt（可用 fetch_sc.py 抓）。
輸出的 content/ 檔名一律是官方頁碼（簡中 + 1900），例如 6059.txt → 007959.md。
第一行如果以「# 」開頭，會當作標題。其餘每行是一行內文。

安全設計：
- 已經是「校對中」或「已校對」的頁面不會被覆蓋。
- 術語表（glossary.csv）是在 OpenCC 轉完後做純文字取代，長詞優先。
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SC_OFFSET = 1900  # 官方頁碼 = 簡中頁碼 + 1900


def make_converter():
    try:
        from opencc import OpenCC
    except ImportError:
        raise SystemExit("找不到 opencc，請先執行：pip install opencc-python-reimplemented")
    for cfg in ("s2twp", "s2twp.json"):
        try:
            return OpenCC(cfg)
        except Exception:
            continue
    raise SystemExit("OpenCC 無法載入 s2twp 設定")


def load_glossary(path):
    pairs = []
    if not path.exists():
        return pairs
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            src, dst = (row.get("from") or "").strip(), (row.get("to") or "").strip()
            if src and dst and not src.startswith("#"):
                pairs.append((src, dst))
    return sorted(pairs, key=lambda p: len(p[0]), reverse=True)


def existing_status(path):
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines()[:10]:
        if line.startswith("status:"):
            return line.split(":", 1)[1].strip()
    return None


def main():
    if len(sys.argv) != 3:
        raise SystemExit("用法：python convert.py <簡體來源資料夾> <輸出資料夾 content>")
    src_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(exist_ok=True)
    cc = make_converter()
    glossary = load_glossary(ROOT / "glossary.csv")

    done = skipped = 0
    for src in sorted(src_dir.glob("*.txt")):
        try:
            page = int(src.stem)
        except ValueError:
            print(f"略過（檔名不是頁碼）：{src.name}")
            continue
        page += SC_OFFSET  # 簡中頁碼 → 官方頁碼（本站一律用官方頁碼）
        out = out_dir / f"{page:06d}.md"
        status = existing_status(out)
        if status in ("proofreading", "done"):
            skipped += 1
            continue

        lines = src.read_text(encoding="utf-8").splitlines()
        title = f"第 {page} 頁"
        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip()
            lines = lines[1:]
        text = cc.convert("\n".join([title] + lines))
        for a, b in glossary:
            text = text.replace(a, b)
        new_title, *body = text.split("\n")

        out.write_text(
            f"---\npage: {page}\ntitle: {new_title}\nstatus: converted\n---\n"
            + "\n".join(body).strip("\n")
            + "\n",
            encoding="utf-8",
        )
        done += 1
    print(f"轉換 {done} 頁，略過已校對 {skipped} 頁")


if __name__ == "__main__":
    main()
