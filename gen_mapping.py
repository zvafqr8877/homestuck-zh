#!/usr/bin/env python3
"""依已驗證的規則產生頁碼對照表 sources.csv。

已用官方站實測的規則：
  官方頁碼 = 簡中頁碼 + 1900（簡中站收錄 6023–8130）
  官方沒有的頁碼（跳號）：MISSING，簡中站同樣跳過
  網址用別名的頁面：ALIASES（簡中站仍佔一個頁碼）
  素材檔編號 = 官方頁碼 - 1900 - (小於該頁的跳號數)
    例：7959→06056、8801→06898、9305→07402、9930→08024

這份腳本只算頁碼和網址，不含任何作品內容。素材的資料夾（act-6-int-5 等）、
副檔名（gif/swf）、多圖頁、-modified 這類例外檔名，目前沒有規則可推，
要靠實測資料另外補進 manifest.json。

用法：
    python gen_mapping.py                      # 預設 7959–10030（繁中沒翻的部分）
    python gen_mapping.py 7959 10030 sources.csv
"""
import csv
import sys

SC_OFFSET = 1900
SC_RANGE = (6023, 8130)          # 簡中站實際收錄的頁碼（8130 對應官方最後一頁 10030）
TC_LAST = 7958                   # 繁中站最後翻譯到的官方頁碼
MISSING = [4299, 4938, 4988, 9802, 9803, 9804]
HIDDEN = [8270]  # 官方隱藏頁：網址存在，但 8269 的下一頁直接跳 8271；簡中站沒有（6370），沒有譯文
ALIASES = {8801: "GAMEOVER", 9305: "shes8ack"}
SC_URL = "https://linzhiyi622.github.io/homestuckjz.GitHub.io/{n}.html"  # 只驗證過 6065、6066
TC_URL = "https://zhhomestuck.github.io/p/{n:06d}"


def file_number(n):
    return n - SC_OFFSET - sum(1 for m in MISSING if m < n)


def rows(first, last):
    for n in range(first, last + 1):
        if n in MISSING:
            continue
        sc = n - SC_OFFSET
        in_sc = SC_RANGE[0] <= sc <= SC_RANGE[1] and n not in HIDDEN
        yield {
            "official": n,
            "official_url": f"https://www.homestuck.com/{ALIASES.get(n, f'{n:06d}')}",
            "sc": sc if in_sc else "",
            "sc_url": SC_URL.format(n=sc) if in_sc else "",
            "tc_url": TC_URL.format(n=n) if n <= TC_LAST else "",
            "file_no": f"{file_number(n):05d}",
        }


def main():
    first = int(sys.argv[1]) if len(sys.argv) > 1 else 7959
    last = int(sys.argv[2]) if len(sys.argv) > 2 else 10030
    out = sys.argv[3] if len(sys.argv) > 3 else "sources.csv"
    fields = ["official", "official_url", "sc", "sc_url", "tc_url", "file_no"]
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        count = 0
        for r in rows(first, last):
            w.writerow(r)
            count += 1
    print(f"寫入 {count} 頁 → {out}")


if __name__ == "__main__":
    main()
