#!/usr/bin/env python3
"""新增／更新密碼頁的答案（只存 SHA-256，不存明文）。

用法：python add_password.py 9058 密碼
  - 密碼會先轉大寫、去掉所有空白再算雜湊，網頁上輸入時也是同樣處理。
  - 結果寫進 passwords.json。沒有寫進去的密碼頁，會改成「到官方頁面輸入」。
"""
import hashlib
import json
import re
import sys
from pathlib import Path

PATH = Path(__file__).resolve().parent / "passwords.json"
if len(sys.argv) != 3:
    raise SystemExit("用法：python add_password.py <頁碼> <密碼>")
page, pw = sys.argv[1], re.sub(r"\s+", "", sys.argv[2].upper())
data = json.loads(PATH.read_text(encoding="utf-8")) if PATH.exists() else {}
data[str(int(page))] = hashlib.sha256(pw.encode("utf-8")).hexdigest()
PATH.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")
print(f"已更新第 {page} 頁；目前共 {len(data)} 頁有設密碼")
